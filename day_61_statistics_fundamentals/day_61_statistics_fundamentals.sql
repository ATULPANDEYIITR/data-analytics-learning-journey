DROP SCHEMA IF EXISTS statistics_fundamentals CASCADE;
CREATE SCHEMA statistics_fundamentals;

SET search_path TO statistics_fundamentals;

CREATE TYPE population_status AS ENUM (
    'ACTIVE',
    'CLOSED'
);

CREATE TYPE sample_method AS ENUM (
    'SIMPLE_RANDOM',
    'SYSTEMATIC',
    'STRATIFIED'
);

CREATE TABLE populations (
    population_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    status population_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(population_name)) >= 3)
);

CREATE TABLE population_units (
    unit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_id BIGINT NOT NULL
        REFERENCES populations(population_id)
        ON DELETE CASCADE,
    unit_key TEXT NOT NULL,
    stratum TEXT,
    measurement NUMERIC(14,4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (population_id, unit_key),
    CHECK (measurement IS NOT NULL)
);

CREATE INDEX idx_population_units_population
    ON population_units(population_id);

CREATE INDEX idx_population_units_stratum
    ON population_units(population_id, stratum);

CREATE TABLE samples (
    sample_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_id BIGINT NOT NULL
        REFERENCES populations(population_id)
        ON DELETE RESTRICT,
    method sample_method NOT NULL,
    requested_size INTEGER NOT NULL,
    seed INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (requested_size > 0)
);

CREATE TABLE sample_units (
    sample_id BIGINT NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,
    unit_id BIGINT NOT NULL
        REFERENCES population_units(unit_id)
        ON DELETE RESTRICT,
    selection_order INTEGER NOT NULL,
    PRIMARY KEY (sample_id, unit_id),
    UNIQUE (sample_id, selection_order),
    CHECK (selection_order > 0)
);

CREATE TABLE descriptive_statistics (
    statistic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_id BIGINT NOT NULL
        REFERENCES populations(population_id)
        ON DELETE CASCADE,
    sample_id BIGINT
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,
    observation_count INTEGER NOT NULL,
    minimum_value NUMERIC(14,4) NOT NULL,
    maximum_value NUMERIC(14,4) NOT NULL,
    mean_value NUMERIC(18,8) NOT NULL,
    median_value NUMERIC(18,8) NOT NULL,
    population_variance NUMERIC(20,8),
    population_stddev NUMERIC(20,8),
    sample_variance NUMERIC(20,8),
    sample_stddev NUMERIC(20,8),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (observation_count > 0),
    CHECK (minimum_value <= maximum_value),
    CHECK (sample_id IS NULL OR observation_count >= 2)
);

CREATE TABLE sampling_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sample_id BIGINT NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(action)) > 0)
);

CREATE OR REPLACE FUNCTION validate_sample_size()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    population_count INTEGER;
BEGIN
    SELECT count(*)
    INTO population_count
    FROM population_units
    WHERE population_id = NEW.population_id;

    IF population_count = 0 THEN
        RAISE EXCEPTION
            'Cannot create sample for population % without units',
            NEW.population_id;
    END IF;

    IF NEW.requested_size > population_count THEN
        RAISE EXCEPTION
            'Requested sample size % exceeds population size %',
            NEW.requested_size,
            population_count;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sample_size
BEFORE INSERT OR UPDATE ON samples
FOR EACH ROW
EXECUTE FUNCTION validate_sample_size();

CREATE OR REPLACE FUNCTION record_sample_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO sampling_audit(sample_id, action, details)
    VALUES (
        NEW.sample_id,
        'SAMPLE_CREATED',
        jsonb_build_object(
            'method', NEW.method::text,
            'requested_size', NEW.requested_size
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_sample_audit
AFTER INSERT ON samples
FOR EACH ROW
EXECUTE FUNCTION record_sample_audit();

CREATE OR REPLACE FUNCTION calculate_population_statistics(
    p_population_id BIGINT
)
RETURNS TABLE (
    observation_count BIGINT,
    minimum_value NUMERIC,
    maximum_value NUMERIC,
    mean_value NUMERIC,
    median_value NUMERIC,
    variance_value NUMERIC,
    standard_deviation NUMERIC
)
LANGUAGE sql
AS $$
    WITH ordered AS (
        SELECT
            measurement,
            row_number() OVER (ORDER BY measurement) AS rn,
            count(*) OVER () AS total
        FROM population_units
        WHERE population_id = p_population_id
    ),
    median_value_cte AS (
        SELECT avg(measurement) AS median_value
        FROM ordered
        WHERE rn IN (
            floor((total + 1) / 2.0),
            ceil((total + 1) / 2.0)
        )
    )
    SELECT
        count(*)::BIGINT,
        min(measurement),
        max(measurement),
        avg(measurement),
        (SELECT median_value FROM median_value_cte),
        var_pop(measurement),
        stddev_pop(measurement)
    FROM population_units
    WHERE population_id = p_population_id;
$$;

CREATE OR REPLACE FUNCTION calculate_sample_statistics(
    p_sample_id BIGINT
)
RETURNS TABLE (
    observation_count BIGINT,
    minimum_value NUMERIC,
    maximum_value NUMERIC,
    mean_value NUMERIC,
    median_value NUMERIC,
    variance_value NUMERIC,
    standard_deviation NUMERIC,
    standard_error NUMERIC
)
LANGUAGE sql
AS $$
    WITH sample_data AS (
        SELECT pu.measurement
        FROM sample_units su
        JOIN population_units pu
          ON pu.unit_id = su.unit_id
        WHERE su.sample_id = p_sample_id
    ),
    ordered AS (
        SELECT
            measurement,
            row_number() OVER (ORDER BY measurement) AS rn,
            count(*) OVER () AS total
        FROM sample_data
    ),
    median_value_cte AS (
        SELECT avg(measurement) AS median_value
        FROM ordered
        WHERE rn IN (
            floor((total + 1) / 2.0),
            ceil((total + 1) / 2.0)
        )
    )
    SELECT
        count(*)::BIGINT,
        min(measurement),
        max(measurement),
        avg(measurement),
        (SELECT median_value FROM median_value_cte),
        var_samp(measurement),
        stddev_samp(measurement),
        stddev_samp(measurement) / sqrt(count(*))
    FROM sample_data;
$$;

CREATE OR REPLACE VIEW population_statistics AS
SELECT
    p.population_id,
    p.population_name,
    count(u.unit_id) AS population_size,
    min(u.measurement) AS minimum_value,
    max(u.measurement) AS maximum_value,
    avg(u.measurement) AS mean_value,
    percentile_cont(0.5)
        WITHIN GROUP (ORDER BY u.measurement) AS median_value,
    var_pop(u.measurement) AS population_variance,
    stddev_pop(u.measurement) AS population_stddev
FROM populations p
LEFT JOIN population_units u
    ON u.population_id = p.population_id
GROUP BY p.population_id, p.population_name;

CREATE OR REPLACE VIEW sample_statistics AS
SELECT
    s.sample_id,
    s.population_id,
    s.method,
    s.requested_size,
    count(u.unit_id) AS actual_sample_size,
    min(u.measurement) AS minimum_value,
    max(u.measurement) AS maximum_value,
    avg(u.measurement) AS sample_mean,
    percentile_cont(0.5)
        WITHIN GROUP (ORDER BY u.measurement) AS sample_median,
    var_samp(u.measurement) AS sample_variance,
    stddev_samp(u.measurement) AS sample_stddev,
    stddev_samp(u.measurement) / sqrt(count(u.unit_id))
        AS standard_error
FROM samples s
JOIN sample_units su
    ON su.sample_id = s.sample_id
JOIN population_units u
    ON u.unit_id = su.unit_id
GROUP BY
    s.sample_id,
    s.population_id,
    s.method,
    s.requested_size;

INSERT INTO populations (
    population_name,
    description
)
VALUES (
    'training_scores_2026',
    'Complete set of observed assessment scores.'
);

INSERT INTO population_units (
    population_id,
    unit_key,
    stratum,
    measurement
)
SELECT
    p.population_id,
    'UNIT-' || lpad(row_number() OVER ()::text, 3, '0'),
    CASE
        WHEN n <= 5 THEN 'A'
        WHEN n <= 10 THEN 'B'
        WHEN n <= 15 THEN 'C'
        WHEN n <= 20 THEN 'D'
        ELSE 'E'
    END,
    value
FROM populations p
CROSS JOIN LATERAL (
    VALUES
        (1, 61.0), (2, 64.0), (3, 66.0), (4, 68.0), (5, 69.0),
        (6, 71.0), (7, 72.0), (8, 73.0), (9, 74.0), (10, 75.0),
        (11, 76.0), (12, 77.0), (13, 78.0), (14, 79.0), (15, 80.0),
        (16, 81.0), (17, 82.0), (18, 83.0), (19, 84.0), (20, 85.0),
        (21, 86.0), (22, 87.0), (23, 88.0), (24, 90.0), (25, 92.0)
) AS scores(n, value)
WHERE p.population_name = 'training_scores_2026';

BEGIN;

INSERT INTO samples (
    population_id,
    method,
    requested_size,
    seed
)
SELECT population_id, 'SIMPLE_RANDOM', 8, 42
FROM populations
WHERE population_name = 'training_scores_2026';

WITH selected AS (
    SELECT
        s.sample_id,
        u.unit_id,
        row_number() OVER (
            PARTITION BY s.sample_id
            ORDER BY md5(
                u.unit_id::text || ':' || s.seed::text
            )
        ) AS selection_order
    FROM samples s
    JOIN population_units u
      ON u.population_id = s.population_id
    WHERE s.method = 'SIMPLE_RANDOM'
      AND s.requested_size = 8
)
INSERT INTO sample_units(sample_id, unit_id, selection_order)
SELECT sample_id, unit_id, selection_order
FROM selected
WHERE selection_order <= 8;

INSERT INTO descriptive_statistics (
    population_id,
    sample_id,
    observation_count,
    minimum_value,
    maximum_value,
    mean_value,
    median_value,
    population_variance,
    population_stddev,
    sample_variance,
    sample_stddev
)
SELECT
    s.population_id,
    s.sample_id,
    x.actual_sample_size,
    x.minimum_value,
    x.maximum_value,
    x.sample_mean,
    x.sample_median,
    var_pop(u.measurement),
    stddev_pop(u.measurement),
    x.sample_variance,
    x.sample_stddev
FROM samples s
JOIN sample_statistics x
  ON x.sample_id = s.sample_id
JOIN sample_units su
  ON su.sample_id = s.sample_id
JOIN population_units u
  ON u.unit_id = su.unit_id
GROUP BY
    s.population_id,
    s.sample_id,
    x.actual_sample_size,
    x.minimum_value,
    x.maximum_value,
    x.sample_mean,
    x.sample_median,
    x.sample_variance,
    x.sample_stddev;

COMMIT;

-- Population-level parameter reporting.
SELECT *
FROM population_statistics
ORDER BY population_id;

-- Sample-level statistic and sampling-error reporting.
SELECT *
FROM sample_statistics
ORDER BY sample_id;

-- Direct calculation of the population mean parameter.
SELECT
    population_id,
    avg(measurement) AS population_mean_parameter
FROM population_units
GROUP BY population_id;

-- Compare the sample statistic with the population parameter.
SELECT
    ss.sample_id,
    ss.sample_mean,
    ps.mean_value AS population_mean,
    ss.sample_mean - ps.mean_value AS sampling_difference,
    ss.standard_error
FROM sample_statistics ss
JOIN population_statistics ps
  ON ps.population_id = ss.population_id;

-- Stratum-level descriptive statistics.
SELECT
    population_id,
    stratum,
    count(*) AS stratum_size,
    avg(measurement) AS stratum_mean,
    stddev_pop(measurement) AS stratum_stddev
FROM population_units
GROUP BY population_id, stratum
ORDER BY population_id, stratum;

-- Demonstrate the reusable statistics functions.
SELECT *
FROM calculate_population_statistics(
    (SELECT population_id
     FROM populations
     WHERE population_name = 'training_scores_2026')
);

SELECT *
FROM calculate_sample_statistics(
    (SELECT sample_id
     FROM samples
     ORDER BY sample_id
     LIMIT 1)
);

-- Validation query: sample cannot contain duplicate population units.
SELECT
    sample_id,
    count(*) AS rows,
    count(DISTINCT unit_id) AS distinct_units,
    count(*) = count(DISTINCT unit_id) AS valid
FROM sample_units
GROUP BY sample_id;

-- Failure case demonstration. This statement is intentionally isolated
-- inside a savepoint so the complete script remains executable.
BEGIN;
SAVEPOINT invalid_sample_test;

DO $$
BEGIN
    BEGIN
        INSERT INTO samples (
            population_id,
            method,
            requested_size
        )
        SELECT population_id, 'SIMPLE_RANDOM', 1000
        FROM populations
        WHERE population_name = 'training_scores_2026';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected sample validation failure: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_sample_test;
COMMIT;
