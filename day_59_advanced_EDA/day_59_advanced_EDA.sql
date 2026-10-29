DROP SCHEMA IF EXISTS advanced_eda CASCADE;
CREATE SCHEMA advanced_eda;

SET search_path TO advanced_eda, public;

CREATE TABLE datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE observations (
    observation_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    customer_id INTEGER NOT NULL,
    income NUMERIC(14,2) NOT NULL CHECK (income >= 0),
    spending NUMERIC(14,2) NOT NULL CHECK (spending >= 0),
    visits INTEGER NOT NULL CHECK (visits >= 0),
    tenure_months INTEGER NOT NULL CHECK (tenure_months >= 0),
    complaints INTEGER NOT NULL CHECK (complaints >= 0),
    UNIQUE (dataset_id, customer_id)
);

CREATE TABLE feature_catalog (
    feature_id SMALLSERIAL PRIMARY KEY,
    feature_name TEXT NOT NULL UNIQUE,
    measurement_type TEXT NOT NULL CHECK (
        measurement_type IN ('continuous', 'count')
    )
);

CREATE TABLE analysis_runs (
    analysis_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    analysis_name TEXT NOT NULL,
    transformation TEXT NOT NULL DEFAULT 'none' CHECK (
        transformation IN ('none', 'log1p', 'sqrt', 'zscore', 'robust')
    ),
    executed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE feature_statistics (
    analysis_id BIGINT NOT NULL REFERENCES analysis_runs(analysis_id)
        ON DELETE CASCADE,
    feature_id SMALLINT NOT NULL REFERENCES feature_catalog(feature_id),
    observation_count INTEGER NOT NULL CHECK (observation_count > 0),
    mean_value DOUBLE PRECISION NOT NULL,
    median_value DOUBLE PRECISION NOT NULL,
    variance_value DOUBLE PRECISION NOT NULL CHECK (variance_value >= 0),
    q1 DOUBLE PRECISION NOT NULL,
    q3 DOUBLE PRECISION NOT NULL,
    skewness DOUBLE PRECISION NOT NULL,
    lower_fence DOUBLE PRECISION NOT NULL,
    upper_fence DOUBLE PRECISION NOT NULL,
    outlier_count INTEGER NOT NULL CHECK (outlier_count >= 0),
    PRIMARY KEY (analysis_id, feature_id)
);

CREATE TABLE feature_relationships (
    analysis_id BIGINT NOT NULL REFERENCES analysis_runs(analysis_id)
        ON DELETE CASCADE,
    feature_x SMALLINT NOT NULL REFERENCES feature_catalog(feature_id),
    feature_y SMALLINT NOT NULL REFERENCES feature_catalog(feature_id),
    covariance_value DOUBLE PRECISION,
    pearson_r DOUBLE PRECISION,
    PRIMARY KEY (analysis_id, feature_x, feature_y),
    CHECK (feature_x < feature_y),
    CHECK (
        covariance_value IS NULL OR
        isfinite(covariance_value)
    ),
    CHECK (
        pearson_r IS NULL OR
        (pearson_r >= -1 AND pearson_r <= 1)
    )
);

CREATE INDEX idx_observations_dataset
    ON observations(dataset_id);

CREATE INDEX idx_analysis_dataset_time
    ON analysis_runs(dataset_id, executed_at DESC);

INSERT INTO datasets (dataset_name, description)
VALUES (
    'customer_behavior',
    'Customer income, spending, engagement, tenure, and complaint observations'
);

INSERT INTO feature_catalog (feature_name, measurement_type)
VALUES
    ('income', 'continuous'),
    ('spending', 'continuous'),
    ('visits', 'count'),
    ('tenure_months', 'count'),
    ('complaints', 'count');

INSERT INTO observations (
    dataset_id, customer_id, income, spending,
    visits, tenure_months, complaints
)
SELECT
    1,
    v.customer_id,
    v.income,
    v.spending,
    v.visits,
    v.tenure_months,
    v.complaints
FROM (
    VALUES
        (1, 42000::numeric, 1100::numeric, 3, 8, 2),
        (2, 48000, 1350, 4, 14, 1),
        (3, 51000, 1500, 5, 18, 1),
        (4, 56000, 1720, 6, 25, 0),
        (5, 62000, 1900, 7, 30, 0),
        (6, 68000, 2150, 8, 36, 1),
        (7, 72000, 2450, 9, 42, 0),
        (8, 79000, 2600, 10, 48, 0),
        (9, 85000, 3000, 11, 52, 1),
        (10, 91000, 3200, 12, 60, 0),
        (11, 47000, 1250, 4, 12, 3),
        (12, 53000, 1550, 5, 21, 2),
        (13, 60000, 1820, 7, 28, 1),
        (14, 74000, 2300, 9, 45, 0),
        (15, 1500000, 3500, 3, 10, 5),
        (16, 45000, 1050, 2, 5, 7)
) AS v(
    customer_id, income, spending,
    visits, tenure_months, complaints
);

CREATE OR REPLACE FUNCTION percentile_value(
    values DOUBLE PRECISION[],
    p DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT percentile_cont(p)
    WITHIN GROUP (ORDER BY value)
    FROM unnest(values) AS value;
$$;

CREATE OR REPLACE FUNCTION feature_array(
    p_dataset_id BIGINT,
    p_feature TEXT
)
RETURNS DOUBLE PRECISION[]
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result DOUBLE PRECISION[];
BEGIN
    IF p_feature NOT IN (
        'income',
        'spending',
        'visits',
        'tenure_months',
        'complaints'
    ) THEN
        RAISE EXCEPTION 'Unsupported feature: %', p_feature;
    END IF;

    EXECUTE format(
        'SELECT array_agg(%I::double precision ORDER BY observation_id)
         FROM advanced_eda.observations
         WHERE dataset_id = $1',
        p_feature
    )
    INTO result
    USING p_dataset_id;

    IF result IS NULL OR cardinality(result) = 0 THEN
        RAISE EXCEPTION 'No observations for dataset %', p_dataset_id;
    END IF;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION feature_profile(
    p_dataset_id BIGINT,
    p_feature TEXT
)
RETURNS TABLE (
    feature_name TEXT,
    observation_count BIGINT,
    mean_value DOUBLE PRECISION,
    median_value DOUBLE PRECISION,
    variance_value DOUBLE PRECISION,
    q1 DOUBLE PRECISION,
    q3 DOUBLE PRECISION,
    iqr DOUBLE PRECISION,
    skewness DOUBLE PRECISION,
    lower_fence DOUBLE PRECISION,
    upper_fence DOUBLE PRECISION,
    outlier_count BIGINT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    values DOUBLE PRECISION[];
    n DOUBLE PRECISION;
    m DOUBLE PRECISION;
    s DOUBLE PRECISION;
BEGIN
    values := feature_array(p_dataset_id, p_feature);

    SELECT
        avg(v),
        stddev_samp(v),
        count(*)
    INTO m, s, observation_count
    FROM unnest(values) AS v;

    q1 := percentile_value(values, 0.25);
    q3 := percentile_value(values, 0.75);
    iqr := q3 - q1;
    lower_fence := q1 - 1.5 * iqr;
    upper_fence := q3 + 1.5 * iqr;

    SELECT count(*)
    INTO outlier_count
    FROM unnest(values) AS v
    WHERE v < lower_fence OR v > upper_fence;

    n := cardinality(values);
    mean_value := m;
    median_value := percentile_value(values, 0.5);
    variance_value := COALESCE(s, 0) ^ 2;

    IF n < 3 OR COALESCE(s, 0) = 0 THEN
        skewness := 0;
    ELSE
        SELECT
            n / ((n - 1) * (n - 2)) *
            sum(power((v - m) / s, 3))
        INTO skewness
        FROM unnest(values) AS v;
    END IF;

    feature_name := p_feature;
    RETURN NEXT;
END;
$$;

CREATE OR REPLACE VIEW observation_quality AS
SELECT
    o.observation_id,
    o.customer_id,
    o.income,
    o.spending,
    o.visits,
    o.tenure_months,
    o.complaints,
    CASE
        WHEN o.income > 500000 THEN 'income_outlier_candidate'
        WHEN o.complaints >= 5 THEN 'complaint_outlier_candidate'
        ELSE 'within_basic_screen'
    END AS screening_status
FROM observations AS o;

CREATE OR REPLACE VIEW relationship_report AS
WITH source AS (
    SELECT
        income::double precision AS income,
        spending::double precision AS spending,
        visits::double precision AS visits,
        tenure_months::double precision AS tenure_months,
        complaints::double precision AS complaints
    FROM observations
    WHERE dataset_id = 1
),
pairs AS (
    SELECT
        'income' AS feature_x,
        'spending' AS feature_y,
        covar_samp(income, spending) AS covariance_value,
        corr(income, spending) AS pearson_r
    FROM source

    UNION ALL

    SELECT
        'income',
        'visits',
        covar_samp(income, visits),
        corr(income, visits)
    FROM source

    UNION ALL

    SELECT
        'visits',
        'spending',
        covar_samp(visits, spending),
        corr(visits, spending)
    FROM source

    UNION ALL

    SELECT
        'complaints',
        'spending',
        covar_samp(complaints, spending),
        corr(complaints, spending)
    FROM source
)
SELECT *
FROM pairs;

CREATE OR REPLACE VIEW transformed_income AS
SELECT
    customer_id,
    income,
    ln(1 + income) AS log1p_income,
    sqrt(income) AS sqrt_income
FROM observations
WHERE dataset_id = 1;

CREATE OR REPLACE FUNCTION validate_analysis(
    p_dataset_id BIGINT
)
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    detail TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        'row_count'::TEXT,
        CASE WHEN count(*) >= 10 THEN 'PASS' ELSE 'FAIL' END,
        format('rows=%s', count(*))
    FROM observations
    WHERE dataset_id = p_dataset_id;

    RETURN QUERY
    SELECT
        'negative_values'::TEXT,
        CASE
            WHEN count(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END,
        format('violations=%s', count(*))
    FROM observations
    WHERE dataset_id = p_dataset_id
      AND (
          income < 0 OR
          spending < 0 OR
          visits < 0 OR
          tenure_months < 0 OR
          complaints < 0
      );
END;
$$;

BEGIN;

INSERT INTO analysis_runs (
    dataset_id,
    analysis_name,
    transformation
)
VALUES (
    1,
    'baseline_advanced_eda',
    'none'
);

WITH feature_values AS (
    SELECT
        feature_name,
        feature_id
    FROM feature_catalog
)
INSERT INTO feature_statistics (
    analysis_id,
    feature_id,
    observation_count,
    mean_value,
    median_value,
    variance_value,
    q1,
    q3,
    skewness,
    lower_fence,
    upper_fence,
    outlier_count
)
SELECT
    1,
    f.feature_id,
    p.observation_count::INTEGER,
    p.mean_value,
    p.median_value,
    p.variance_value,
    p.q1,
    p.q3,
    p.skewness,
    p.lower_fence,
    p.upper_fence,
    p.outlier_count::INTEGER
FROM feature_values AS f
CROSS JOIN LATERAL feature_profile(
    1,
    f.feature_name
) AS p;

INSERT INTO feature_relationships (
    analysis_id,
    feature_x,
    feature_y,
    covariance_value,
    pearson_r
)
SELECT
    1,
    LEAST(
        fx.feature_id,
        fy.feature_id
    ),
    GREATEST(
        fx.feature_id,
        fy.feature_id
    ),
    r.covariance_value,
    r.pearson_r
FROM relationship_report AS r
JOIN feature_catalog AS fx
    ON fx.feature_name = r.feature_x
JOIN feature_catalog AS fy
    ON fy.feature_name = r.feature_y;

COMMIT;

SELECT *
FROM feature_profile(1, 'income');

SELECT *
FROM feature_profile(1, 'spending');

SELECT *
FROM feature_profile(1, 'visits');

SELECT *
FROM feature_profile(1, 'tenure_months');

SELECT *
FROM feature_profile(1, 'complaints');

SELECT
    feature_x,
    feature_y,
    covariance_value,
    round(pearson_r::numeric, 4) AS pearson_r
FROM relationship_report
ORDER BY abs(pearson_r) DESC;

SELECT *
FROM observation_quality
WHERE screening_status <> 'within_basic_screen'
ORDER BY customer_id;

SELECT
    feature_name,
    observation_count,
    round(mean_value::numeric, 2) AS mean_value,
    round(median_value::numeric, 2) AS median_value,
    round(skewness::numeric, 3) AS skewness,
    outlier_count
FROM feature_statistics fs
JOIN feature_catalog fc USING (feature_id)
WHERE analysis_id = 1
ORDER BY abs(skewness) DESC;

SELECT
    customer_id,
    income,
    round(log1p_income::numeric, 4) AS log1p_income,
    round(sqrt_income::numeric, 4) AS sqrt_income
FROM transformed_income
ORDER BY income DESC;

SELECT *
FROM validate_analysis(1);

-- Pearson correlation measures linear association.
-- Covariance retains measurement units, while correlation is standardized.
-- IQR fences identify statistical candidates for investigation.
-- Outlier rows remain in the source table because deletion is a domain decision.
-- Database constraints protect basic data quality before statistical analysis.
