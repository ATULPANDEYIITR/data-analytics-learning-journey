DROP SCHEMA IF EXISTS dispersion_analysis CASCADE;
CREATE SCHEMA dispersion_analysis;

SET search_path TO dispersion_analysis, public;

CREATE TYPE measure_kind AS ENUM (
    'RANGE',
    'POPULATION_VARIANCE',
    'SAMPLE_VARIANCE',
    'POPULATION_STANDARD_DEVIATION',
    'SAMPLE_STANDARD_DEVIATION',
    'IQR',
    'MAD',
    'COEFFICIENT_OF_VARIATION'
);

CREATE TYPE variability_level AS ENUM (
    'LOW',
    'MODERATE',
    'HIGH',
    'UNDEFINED'
);

CREATE TABLE datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE observations (
    observation_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    observation_value NUMERIC(18,6) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (isfinite(observation_value::double precision))
);

CREATE INDEX observations_dataset_value_idx
    ON observations(dataset_id, observation_value);

CREATE TABLE dispersion_reports (
    report_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    observation_count INTEGER NOT NULL CHECK (observation_count > 0),
    minimum_value NUMERIC(18,6) NOT NULL,
    maximum_value NUMERIC(18,6) NOT NULL,
    range_value NUMERIC(18,6) NOT NULL,
    mean_value NUMERIC(18,6) NOT NULL,
    population_variance NUMERIC(18,6) NOT NULL,
    sample_variance NUMERIC(18,6),
    population_standard_deviation NUMERIC(18,6) NOT NULL,
    sample_standard_deviation NUMERIC(18,6),
    q1 NUMERIC(18,6) NOT NULL,
    q3 NUMERIC(18,6) NOT NULL,
    iqr NUMERIC(18,6) NOT NULL,
    mad NUMERIC(18,6) NOT NULL,
    coefficient_of_variation_percent NUMERIC(18,6),
    variability variability_level NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (maximum_value >= minimum_value),
    CHECK (range_value >= 0),
    CHECK (iqr >= 0),
    CHECK (mad >= 0),
    CHECK (
        coefficient_of_variation_percent IS NULL
        OR coefficient_of_variation_percent >= 0
    )
);

CREATE UNIQUE INDEX dispersion_reports_dataset_idx
    ON dispersion_reports(dataset_id);

CREATE TABLE measure_catalog (
    measure measure_kind PRIMARY KEY,
    definition TEXT NOT NULL
);

INSERT INTO measure_catalog (measure, definition) VALUES
('RANGE', 'Maximum minus minimum.'),
('POPULATION_VARIANCE', 'Mean squared deviation from the population mean.'),
('SAMPLE_VARIANCE', 'Unbiased sample variance using n - 1.'),
('POPULATION_STANDARD_DEVIATION', 'Square root of population variance.'),
('SAMPLE_STANDARD_DEVIATION', 'Square root of sample variance.'),
('IQR', 'Third quartile minus first quartile.'),
('MAD', 'Median absolute deviation from the median.'),
('COEFFICIENT_OF_VARIATION', 'Population standard deviation divided by absolute mean, expressed as a percentage.');

CREATE OR REPLACE FUNCTION classify_cv(cv NUMERIC)
RETURNS variability_level
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF cv IS NULL OR NOT isfinite(cv::double precision) THEN
        RETURN 'UNDEFINED';
    ELSIF cv < 10 THEN
        RETURN 'LOW';
    ELSIF cv < 20 THEN
        RETURN 'MODERATE';
    ELSE
        RETURN 'HIGH';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION validate_observation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT isfinite(NEW.observation_value::double precision) THEN
        RAISE EXCEPTION 'Observation must be finite';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER observations_validate
BEFORE INSERT OR UPDATE ON observations
FOR EACH ROW
EXECUTE FUNCTION validate_observation();

INSERT INTO datasets (dataset_name, description)
VALUES
(
    'Production Response Times',
    'Representative response-time observations used to evaluate operational variability.'
),
(
    'Stable Workload',
    'A low-dispersion comparison dataset.'
),
(
    'Zero Mean Edge Case',
    'Contains values whose arithmetic mean is zero, making CV undefined.'
);

INSERT INTO observations (dataset_id, observation_value)
SELECT d.dataset_id, x.value
FROM datasets d
JOIN LATERAL (
    VALUES
        (12.0::numeric),
        (15.0::numeric),
        (14.0::numeric),
        (10.0::numeric),
        (18.0::numeric),
        (20.0::numeric),
        (13.0::numeric),
        (16.0::numeric),
        (15.0::numeric),
        (11.0::numeric)
) AS x(value) ON TRUE
WHERE d.dataset_name = 'Production Response Times';

INSERT INTO observations (dataset_id, observation_value)
SELECT d.dataset_id, x.value
FROM datasets d
JOIN LATERAL (
    VALUES
        (99.0::numeric),
        (100.0::numeric),
        (101.0::numeric),
        (100.0::numeric),
        (99.5::numeric),
        (100.5::numeric)
) AS x(value) ON TRUE
WHERE d.dataset_name = 'Stable Workload';

INSERT INTO observations (dataset_id, observation_value)
SELECT d.dataset_id, x.value
FROM datasets d
JOIN LATERAL (
    VALUES
        (-10.0::numeric),
        (10.0::numeric),
        (-5.0::numeric),
        (5.0::numeric)
) AS x(value) ON TRUE
WHERE d.dataset_name = 'Zero Mean Edge Case';

WITH statistics AS (
    SELECT
        d.dataset_id,
        COUNT(*)::INTEGER AS observation_count,
        MIN(o.observation_value) AS minimum_value,
        MAX(o.observation_value) AS maximum_value,
        AVG(o.observation_value) AS mean_value,
        VAR_POP(o.observation_value) AS population_variance,
        VAR_SAMP(o.observation_value) AS sample_variance,
        STDDEV_POP(o.observation_value) AS population_standard_deviation,
        STDDEV_SAMP(o.observation_value) AS sample_standard_deviation,
        PERCENTILE_CONT(0.25)
            WITHIN GROUP (ORDER BY o.observation_value) AS q1,
        PERCENTILE_CONT(0.75)
            WITHIN GROUP (ORDER BY o.observation_value) AS q3,
        PERCENTILE_CONT(0.50)
            WITHIN GROUP (ORDER BY o.observation_value) AS median
    FROM datasets d
    JOIN observations o
        ON o.dataset_id = d.dataset_id
    GROUP BY d.dataset_id
),
mad_values AS (
    SELECT
        s.dataset_id,
        PERCENTILE_CONT(0.50)
            WITHIN GROUP (
                ORDER BY ABS(o.observation_value - s.median)
            ) AS mad
    FROM statistics s
    JOIN observations o
        ON o.dataset_id = s.dataset_id
    GROUP BY s.dataset_id
)
INSERT INTO dispersion_reports (
    dataset_id,
    observation_count,
    minimum_value,
    maximum_value,
    range_value,
    mean_value,
    population_variance,
    sample_variance,
    population_standard_deviation,
    sample_standard_deviation,
    q1,
    q3,
    iqr,
    mad,
    coefficient_of_variation_percent,
    variability
)
SELECT
    s.dataset_id,
    s.observation_count,
    s.minimum_value,
    s.maximum_value,
    s.maximum_value - s.minimum_value,
    s.mean_value,
    s.population_variance,
    s.sample_variance,
    s.population_standard_deviation,
    s.sample_standard_deviation,
    s.q1,
    s.q3,
    s.q3 - s.q1,
    m.mad,
    CASE
        WHEN s.mean_value = 0 THEN NULL
        ELSE
            s.population_standard_deviation
            / ABS(s.mean_value) * 100
    END,
    classify_cv(
        CASE
            WHEN s.mean_value = 0 THEN NULL
            ELSE
                s.population_standard_deviation
                / ABS(s.mean_value) * 100
        END
    )
FROM statistics s
JOIN mad_values m
    ON m.dataset_id = s.dataset_id;

CREATE VIEW dispersion_summary AS
SELECT
    d.dataset_name,
    r.observation_count,
    r.minimum_value,
    r.maximum_value,
    r.range_value,
    r.mean_value,
    r.population_variance,
    r.sample_variance,
    r.population_standard_deviation,
    r.sample_standard_deviation,
    r.q1,
    r.q3,
    r.iqr,
    r.mad,
    r.coefficient_of_variation_percent,
    r.variability,
    r.calculated_at
FROM datasets d
JOIN dispersion_reports r
    ON r.dataset_id = d.dataset_id;

CREATE VIEW observation_quality AS
SELECT
    d.dataset_name,
    COUNT(o.observation_id) AS observation_count,
    MIN(o.observation_value) AS minimum_value,
    MAX(o.observation_value) AS maximum_value,
    AVG(o.observation_value) AS mean_value,
    COUNT(*) FILTER (
        WHERE o.observation_value IS NULL
    ) AS null_observations
FROM datasets d
LEFT JOIN observations o
    ON o.dataset_id = d.dataset_id
GROUP BY d.dataset_id, d.dataset_name;

CREATE OR REPLACE FUNCTION refresh_dispersion_report(
    target_dataset_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    n INTEGER;
    min_value NUMERIC;
    max_value NUMERIC;
    avg_value NUMERIC;
    pop_var NUMERIC;
    samp_var NUMERIC;
    pop_sd NUMERIC;
    samp_sd NUMERIC;
    first_quartile NUMERIC;
    third_quartile NUMERIC;
    median_value NUMERIC;
    median_absolute_deviation NUMERIC;
    cv NUMERIC;
BEGIN
    SELECT
        COUNT(*)::INTEGER,
        MIN(observation_value),
        MAX(observation_value),
        AVG(observation_value),
        VAR_POP(observation_value),
        VAR_SAMP(observation_value),
        STDDEV_POP(observation_value),
        STDDEV_SAMP(observation_value),
        PERCENTILE_CONT(0.25)
            WITHIN GROUP (ORDER BY observation_value),
        PERCENTILE_CONT(0.75)
            WITHIN GROUP (ORDER BY observation_value),
        PERCENTILE_CONT(0.50)
            WITHIN GROUP (ORDER BY observation_value)
    INTO
        n,
        min_value,
        max_value,
        avg_value,
        pop_var,
        samp_var,
        pop_sd,
        samp_sd,
        first_quartile,
        third_quartile,
        median_value
    FROM observations
    WHERE dataset_id = target_dataset_id;

    IF n = 0 THEN
        RAISE EXCEPTION
            'Dataset % contains no observations',
            target_dataset_id;
    END IF;

    SELECT PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY ABS(observation_value - median_value)
        )
    INTO median_absolute_deviation
    FROM observations
    WHERE dataset_id = target_dataset_id;

    IF avg_value = 0 THEN
        cv := NULL;
    ELSE
        cv := pop_sd / ABS(avg_value) * 100;
    END IF;

    INSERT INTO dispersion_reports (
        dataset_id,
        observation_count,
        minimum_value,
        maximum_value,
        range_value,
        mean_value,
        population_variance,
        sample_variance,
        population_standard_deviation,
        sample_standard_deviation,
        q1,
        q3,
        iqr,
        mad,
        coefficient_of_variation_percent,
        variability
    )
    VALUES (
        target_dataset_id,
        n,
        min_value,
        max_value,
        max_value - min_value,
        avg_value,
        pop_var,
        samp_var,
        pop_sd,
        samp_sd,
        first_quartile,
        third_quartile,
        third_quartile - first_quartile,
        median_absolute_deviation,
        cv,
        classify_cv(cv)
    )
    ON CONFLICT (dataset_id)
    DO UPDATE SET
        observation_count = EXCLUDED.observation_count,
        minimum_value = EXCLUDED.minimum_value,
        maximum_value = EXCLUDED.maximum_value,
        range_value = EXCLUDED.range_value,
        mean_value = EXCLUDED.mean_value,
        population_variance = EXCLUDED.population_variance,
        sample_variance = EXCLUDED.sample_variance,
        population_standard_deviation =
            EXCLUDED.population_standard_deviation,
        sample_standard_deviation =
            EXCLUDED.sample_standard_deviation,
        q1 = EXCLUDED.q1,
        q3 = EXCLUDED.q3,
        iqr = EXCLUDED.iqr,
        mad = EXCLUDED.mad,
        coefficient_of_variation_percent =
            EXCLUDED.coefficient_of_variation_percent,
        variability = EXCLUDED.variability,
        calculated_at = CURRENT_TIMESTAMP;
END;
$$;

-- Retrieval.
SELECT *
FROM dispersion_summary
ORDER BY dataset_name;

-- Validation of the relationship between range and extrema.
SELECT
    dataset_name,
    minimum_value,
    maximum_value,
    range_value,
    maximum_value - minimum_value AS recomputed_range,
    range_value =
        maximum_value - minimum_value AS range_valid
FROM dispersion_summary;

-- Comparison of absolute and relative dispersion.
SELECT
    dataset_name,
    range_value,
    iqr,
    population_standard_deviation,
    mad,
    coefficient_of_variation_percent,
    variability
FROM dispersion_summary
ORDER BY coefficient_of_variation_percent NULLS FIRST;

-- Ranking datasets by relative variability.
SELECT
    dataset_name,
    coefficient_of_variation_percent,
    variability,
    RANK() OVER (
        ORDER BY coefficient_of_variation_percent DESC NULLS LAST
    ) AS variability_rank
FROM dispersion_summary;

-- Observation-level aggregation.
SELECT
    d.dataset_name,
    COUNT(*) AS observations,
    ROUND(AVG(o.observation_value), 4) AS mean_value,
    ROUND(MIN(o.observation_value), 4) AS minimum_value,
    ROUND(MAX(o.observation_value), 4) AS maximum_value
FROM datasets d
JOIN observations o
    ON o.dataset_id = d.dataset_id
GROUP BY d.dataset_id, d.dataset_name
ORDER BY d.dataset_name;

-- Transactional refresh demonstrates atomic replacement of a report.
BEGIN;

SELECT refresh_dispersion_report(
    dataset_id
)
FROM datasets
WHERE dataset_name = 'Production Response Times';

COMMIT;

-- The zero-mean dataset demonstrates why CV requires special handling.
SELECT
    dataset_name,
    mean_value,
    population_standard_deviation,
    coefficient_of_variation_percent,
    variability
FROM dispersion_summary
WHERE dataset_name = 'Zero Mean Edge Case';
