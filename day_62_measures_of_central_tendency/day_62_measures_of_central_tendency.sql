DROP SCHEMA IF EXISTS central_tendency CASCADE;
CREATE SCHEMA central_tendency;

SET search_path TO central_tendency, public;

CREATE TABLE dataset (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(dataset_name)) > 0)
);

CREATE TABLE observation (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES dataset(dataset_id)
        ON DELETE CASCADE,
    observation_no INTEGER NOT NULL,
    value NUMERIC(30, 12) NOT NULL,
    weight NUMERIC(30, 12),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, observation_no),
    CHECK (weight IS NULL OR weight >= 0)
);

CREATE INDEX idx_observation_dataset_value
    ON observation(dataset_id, value);

CREATE TABLE measure_result (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES dataset(dataset_id)
        ON DELETE CASCADE,
    measure_name TEXT NOT NULL,
    measure_value NUMERIC(30, 12),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, measure_name),
    CHECK (
        measure_name IN (
            'mean',
            'median',
            'mode',
            'weighted_mean',
            'geometric_mean',
            'harmonic_mean'
        )
    )
);

CREATE TABLE calculation_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES dataset(dataset_id)
        ON DELETE CASCADE,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('SUCCESS', 'REJECTED')),
    CHECK (
        operation IN (
            'mean',
            'median',
            'mode',
            'weighted_mean',
            'geometric_mean',
            'harmonic_mean'
        )
    )
);

INSERT INTO dataset (dataset_name, description)
VALUES
    (
        'review_duration_hours',
        'Observed review durations for repository changes'
    ),
    (
        'deployment_growth_multipliers',
        'Positive multipliers used for geometric averaging'
    ),
    (
        'throughput_rates',
        'Positive rates where harmonic averaging is appropriate'
    ),
    (
        'weighted_quality_scores',
        'Scores with explicit assessment weights'
    );

INSERT INTO observation (dataset_id, observation_no, value)
SELECT
    dataset_id,
    ROW_NUMBER() OVER (ORDER BY value, occurrence),
    value
FROM (
    SELECT
        d.dataset_id,
        x.value,
        x.occurrence
    FROM dataset d
    CROSS JOIN LATERAL (
        VALUES
            (2::NUMERIC, 1),
            (3::NUMERIC, 1),
            (3::NUMERIC, 2),
            (4::NUMERIC, 1),
            (5::NUMERIC, 1),
            (8::NUMERIC, 1),
            (40::NUMERIC, 1)
    ) AS x(value, occurrence)
    WHERE d.dataset_name = 'review_duration_hours'
) AS source_data;

INSERT INTO observation (dataset_id, observation_no, value)
SELECT
    d.dataset_id,
    ROW_NUMBER() OVER (ORDER BY x.value),
    x.value
FROM dataset d
CROSS JOIN LATERAL (
    VALUES
        (1.02::NUMERIC),
        (1.04::NUMERIC),
        (1.06::NUMERIC),
        (1.03::NUMERIC)
) AS x(value)
WHERE d.dataset_name = 'deployment_growth_multipliers';

INSERT INTO observation (dataset_id, observation_no, value)
SELECT
    d.dataset_id,
    ROW_NUMBER() OVER (ORDER BY x.value),
    x.value
FROM dataset d
CROSS JOIN LATERAL (
    VALUES
        (30::NUMERIC),
        (40::NUMERIC),
        (50::NUMERIC)
) AS x(value)
WHERE d.dataset_name = 'throughput_rates';

INSERT INTO observation (dataset_id, observation_no, value, weight)
SELECT
    d.dataset_id,
    ROW_NUMBER() OVER (ORDER BY x.value),
    x.value,
    x.weight
FROM dataset d
CROSS JOIN LATERAL (
    VALUES
        (80::NUMERIC, 0.20::NUMERIC),
        (88::NUMERIC, 0.30::NUMERIC),
        (94::NUMERIC, 0.50::NUMERIC)
) AS x(value, weight)
WHERE d.dataset_name = 'weighted_quality_scores';

CREATE OR REPLACE FUNCTION calculate_mean(p_dataset_id BIGINT)
RETURNS NUMERIC
LANGUAGE SQL
STABLE
AS $$
    SELECT AVG(value)
    FROM observation
    WHERE dataset_id = p_dataset_id;
$$;

CREATE OR REPLACE FUNCTION calculate_median(p_dataset_id BIGINT)
RETURNS NUMERIC
LANGUAGE SQL
STABLE
AS $$
    SELECT percentile_cont(0.5)
           WITHIN GROUP (ORDER BY value)
    FROM observation
    WHERE dataset_id = p_dataset_id;
$$;

CREATE OR REPLACE FUNCTION calculate_mode(p_dataset_id BIGINT)
RETURNS TABLE(mode_value NUMERIC, frequency BIGINT)
LANGUAGE SQL
STABLE
AS $$
    WITH frequencies AS (
        SELECT
            value,
            COUNT(*) AS frequency
        FROM observation
        WHERE dataset_id = p_dataset_id
        GROUP BY value
    ),
    maximum AS (
        SELECT MAX(frequency) AS max_frequency
        FROM frequencies
    )
    SELECT f.value, f.frequency
    FROM frequencies f
    CROSS JOIN maximum m
    WHERE f.frequency = m.max_frequency
      AND m.max_frequency > 1
    ORDER BY f.value;
$$;

CREATE OR REPLACE FUNCTION calculate_weighted_mean(p_dataset_id BIGINT)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    total_weight NUMERIC;
    weighted_total NUMERIC;
BEGIN
    SELECT
        COALESCE(SUM(weight), 0),
        COALESCE(SUM(value * weight), 0)
    INTO total_weight, weighted_total
    FROM observation
    WHERE dataset_id = p_dataset_id
      AND weight IS NOT NULL;

    IF total_weight <= 0 THEN
        RAISE EXCEPTION
            'Weighted mean requires a positive total weight';
    END IF;

    RETURN weighted_total / total_weight;
END;
$$;

CREATE OR REPLACE FUNCTION calculate_geometric_mean(p_dataset_id BIGINT)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result NUMERIC;
    invalid_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO invalid_count
    FROM observation
    WHERE dataset_id = p_dataset_id
      AND value <= 0;

    IF invalid_count > 0 THEN
        RAISE EXCEPTION
            'Geometric mean requires strictly positive observations';
    END IF;

    SELECT EXP(AVG(LN(value)))
    INTO result
    FROM observation
    WHERE dataset_id = p_dataset_id;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION calculate_harmonic_mean(p_dataset_id BIGINT)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result NUMERIC;
    invalid_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO invalid_count
    FROM observation
    WHERE dataset_id = p_dataset_id
      AND value <= 0;

    IF invalid_count > 0 THEN
        RAISE EXCEPTION
            'Harmonic mean requires strictly positive observations';
    END IF;

    SELECT COUNT(*) / SUM(1 / value)
    INTO result
    FROM observation
    WHERE dataset_id = p_dataset_id;

    RETURN result;
END;
$$;

CREATE OR REPLACE PROCEDURE refresh_measure_results(p_dataset_id BIGINT)
LANGUAGE plpgsql
AS $$
DECLARE
    mean_value NUMERIC;
    median_value NUMERIC;
    weighted_value NUMERIC;
    geometric_value NUMERIC;
    harmonic_value NUMERIC;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM dataset
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION 'Dataset % does not exist', p_dataset_id;
    END IF;

    mean_value := calculate_mean(p_dataset_id);
    median_value := calculate_median(p_dataset_id);

    INSERT INTO measure_result (
        dataset_id, measure_name, measure_value
    )
    VALUES
        (p_dataset_id, 'mean', mean_value),
        (p_dataset_id, 'median', median_value)
    ON CONFLICT (dataset_id, measure_name)
    DO UPDATE SET
        measure_value = EXCLUDED.measure_value,
        calculated_at = CURRENT_TIMESTAMP;

    SELECT calculate_weighted_mean(p_dataset_id)
    INTO weighted_value;

    INSERT INTO measure_result (
        dataset_id, measure_name, measure_value
    )
    VALUES (
        p_dataset_id,
        'weighted_mean',
        weighted_value
    )
    ON CONFLICT (dataset_id, measure_name)
    DO UPDATE SET
        measure_value = EXCLUDED.measure_value,
        calculated_at = CURRENT_TIMESTAMP;

    SELECT calculate_geometric_mean(p_dataset_id)
    INTO geometric_value;

    INSERT INTO measure_result (
        dataset_id, measure_name, measure_value
    )
    VALUES (
        p_dataset_id,
        'geometric_mean',
        geometric_value
    )
    ON CONFLICT (dataset_id, measure_name)
    DO UPDATE SET
        measure_value = EXCLUDED.measure_value,
        calculated_at = CURRENT_TIMESTAMP;

    SELECT calculate_harmonic_mean(p_dataset_id)
    INTO harmonic_value;

    INSERT INTO measure_result (
        dataset_id, measure_name, measure_value
    )
    VALUES (
        p_dataset_id,
        'harmonic_mean',
        harmonic_value
    )
    ON CONFLICT (dataset_id, measure_name)
    DO UPDATE SET
        measure_value = EXCLUDED.measure_value,
        calculated_at = CURRENT_TIMESTAMP;
END;
$$;

CREATE OR REPLACE VIEW dataset_measure_report AS
SELECT
    d.dataset_id,
    d.dataset_name,
    COUNT(o.observation_id) AS observation_count,
    AVG(o.value) AS mean_value,
    percentile_cont(0.5)
        WITHIN GROUP (ORDER BY o.value) AS median_value,
    MIN(o.value) AS minimum_value,
    MAX(o.value) AS maximum_value,
    SUM(o.value) AS total_value
FROM dataset d
LEFT JOIN observation o
    ON o.dataset_id = d.dataset_id
GROUP BY d.dataset_id, d.dataset_name;

CREATE OR REPLACE VIEW weighted_dataset_report AS
SELECT
    d.dataset_id,
    d.dataset_name,
    SUM(o.weight) AS total_weight,
    SUM(o.value * o.weight) AS weighted_total,
    CASE
        WHEN SUM(o.weight) > 0
        THEN SUM(o.value * o.weight) / SUM(o.weight)
        ELSE NULL
    END AS weighted_mean
FROM dataset d
JOIN observation o
    ON o.dataset_id = d.dataset_id
WHERE o.weight IS NOT NULL
GROUP BY d.dataset_id, d.dataset_name;

CREATE OR REPLACE FUNCTION record_measure_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.measure_value IS NULL THEN
        INSERT INTO calculation_event (
            dataset_id,
            operation,
            status,
            message
        )
        VALUES (
            NEW.dataset_id,
            NEW.measure_name,
            'REJECTED',
            'Measure produced a NULL result'
        );
    ELSE
        INSERT INTO calculation_event (
            dataset_id,
            operation,
            status,
            message
        )
        VALUES (
            NEW.dataset_id,
            NEW.measure_name,
            'SUCCESS',
            'Measure result recorded'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_measure_event
AFTER INSERT OR UPDATE ON measure_result
FOR EACH ROW
EXECUTE FUNCTION record_measure_event();

-- The following transaction demonstrates atomic result refresh.
BEGIN;

CALL refresh_measure_results(
    (
        SELECT dataset_id
        FROM dataset
        WHERE dataset_name = 'review_duration_hours'
    )
);

COMMIT;

BEGIN;

CALL refresh_measure_results(
    (
        SELECT dataset_id
        FROM dataset
        WHERE dataset_name = 'deployment_growth_multipliers'
    )
);

CALL refresh_measure_results(
    (
        SELECT dataset_id
        FROM dataset
        WHERE dataset_name = 'throughput_rates'
    )
);

COMMIT;

SELECT *
FROM dataset_measure_report
ORDER BY dataset_id;

SELECT *
FROM weighted_dataset_report
ORDER BY dataset_id;

SELECT
    d.dataset_name,
    r.measure_name,
    r.measure_value,
    r.calculated_at
FROM measure_result r
JOIN dataset d
    ON d.dataset_id = r.dataset_id
ORDER BY d.dataset_name, r.measure_name;

SELECT
    d.dataset_name,
    m.mode_value,
    m.frequency
FROM dataset d
CROSS JOIN LATERAL calculate_mode(d.dataset_id) m
ORDER BY d.dataset_name, m.mode_value;

WITH ranked_values AS (
    SELECT
        d.dataset_name,
        o.value,
        ROW_NUMBER() OVER (
            PARTITION BY o.dataset_id
            ORDER BY o.value
        ) AS ascending_position,
        COUNT(*) OVER (
            PARTITION BY o.dataset_id
        ) AS observation_count
    FROM dataset d
    JOIN observation o
        ON o.dataset_id = d.dataset_id
)
SELECT
    dataset_name,
    value,
    observation_count
FROM ranked_values
WHERE ascending_position IN (
    (observation_count + 1) / 2,
    (observation_count + 2) / 2
)
ORDER BY dataset_name, ascending_position;

-- Failure cases are evaluated without corrupting stored observations.
DO $$
DECLARE
    review_dataset_id BIGINT;
BEGIN
    SELECT dataset_id
    INTO review_dataset_id
    FROM dataset
    WHERE dataset_name = 'review_duration_hours';

    BEGIN
        PERFORM calculate_geometric_mean(review_dataset_id);
        RAISE NOTICE 'Geometric mean accepted for positive review times.';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Geometric mean rejected: %', SQLERRM;
    END;
END;
$$;

SELECT
    status,
    operation,
    COUNT(*) AS event_count
FROM calculation_event
GROUP BY status, operation
ORDER BY status, operation;
