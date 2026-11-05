-- ============================================================
-- SAMPLING DISTRIBUTIONS
-- PostgreSQL 15+
--
-- Demonstrates:
-- 1. Population statistics
-- 2. Sample generation
-- 3. Sampling means
-- 4. Standard error
-- 5. Finite population correction
-- 6. Central Limit Theorem
-- 7. Law of Large Numbers
-- 8. Experiment management
-- 9. Data validation and integrity
-- 10. Statistical reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS sampling_lab;

SET search_path TO sampling_lab, public;

-- ------------------------------------------------------------
-- 1. ENUMERATIONS
-- ------------------------------------------------------------

CREATE TYPE sampling_method AS ENUM (
    'WITH_REPLACEMENT',
    'WITHOUT_REPLACEMENT'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

-- ------------------------------------------------------------
-- 2. POPULATION
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS populations (
    population_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS population_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_id BIGINT NOT NULL
        REFERENCES populations(population_id)
        ON DELETE CASCADE,
    observation_value NUMERIC(18, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        observation_value > -1000000000000
        AND observation_value < 1000000000000
    )
);

CREATE INDEX IF NOT EXISTS idx_population_observations_population
    ON population_observations(population_id);

CREATE INDEX IF NOT EXISTS idx_population_observations_value
    ON population_observations(population_id, observation_value);

-- ------------------------------------------------------------
-- 3. POPULATION STATISTICS VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW population_statistics AS
SELECT
    p.population_id,
    p.population_name,
    COUNT(o.observation_id) AS population_size,
    AVG(o.observation_value) AS population_mean,
    VAR_POP(o.observation_value) AS population_variance,
    STDDEV_POP(o.observation_value) AS population_standard_deviation,
    MIN(o.observation_value) AS minimum_value,
    MAX(o.observation_value) AS maximum_value
FROM populations p
LEFT JOIN population_observations o
    ON p.population_id = o.population_id
GROUP BY
    p.population_id,
    p.population_name;

-- ------------------------------------------------------------
-- 4. EXPERIMENT MANAGEMENT
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sampling_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    population_id BIGINT NOT NULL
        REFERENCES populations(population_id),
    experiment_name VARCHAR(150) NOT NULL,
    sampling_method sampling_method NOT NULL,
    sample_size INTEGER NOT NULL,
    repetitions INTEGER NOT NULL,
    status experiment_status NOT NULL DEFAULT 'CREATED',
    random_seed BIGINT NOT NULL DEFAULT 2026,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    CHECK (sample_size > 0),
    CHECK (repetitions >= 2),
    CHECK (
        (status = 'COMPLETED' AND completed_at IS NOT NULL)
        OR
        (status <> 'COMPLETED' AND completed_at IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_sampling_experiments_status
    ON sampling_experiments(status, created_at DESC);

CREATE TABLE IF NOT EXISTS sampling_draws (
    draw_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES sampling_experiments(experiment_id)
        ON DELETE CASCADE,
    repetition_number INTEGER NOT NULL,
    sample_mean NUMERIC(20, 8) NOT NULL,
    sample_variance NUMERIC(20, 8),
    sample_standard_deviation NUMERIC(20, 8),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, repetition_number),

    CHECK (repetition_number > 0),
    CHECK (
        sample_variance IS NULL OR sample_variance >= 0
    ),
    CHECK (
        sample_standard_deviation IS NULL
        OR sample_standard_deviation >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_sampling_draws_experiment
    ON sampling_draws(experiment_id, repetition_number);

CREATE TABLE IF NOT EXISTS sample_observations (
    sample_observation_id BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES sampling_experiments(experiment_id)
        ON DELETE CASCADE,
    repetition_number INTEGER NOT NULL,
    observation_id BIGINT NOT NULL
        REFERENCES population_observations(observation_id),
    observation_value NUMERIC(18, 4) NOT NULL,

    FOREIGN KEY (experiment_id, repetition_number)
        REFERENCES sampling_draws(experiment_id, repetition_number)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sample_observations_experiment
    ON sample_observations(experiment_id, repetition_number);

-- ------------------------------------------------------------
-- 5. EXPERIMENT RESULTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_id BIGINT PRIMARY KEY
        REFERENCES sampling_experiments(experiment_id)
        ON DELETE CASCADE,
    population_mean NUMERIC(20, 8) NOT NULL,
    sampling_mean NUMERIC(20, 8) NOT NULL,
    theoretical_standard_error NUMERIC(20, 8) NOT NULL,
    empirical_standard_error NUMERIC(20, 8) NOT NULL,
    bias NUMERIC(20, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (theoretical_standard_error >= 0),
    CHECK (empirical_standard_error >= 0)
);

-- ------------------------------------------------------------
-- 6. SAMPLE MEAN FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_sample_mean(
    p_values NUMERIC[]
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF CARDINALITY(p_values) = 0 THEN
        RAISE EXCEPTION 'Sample cannot be empty.';
    END IF;

    RETURN (
        SELECT AVG(value)
        FROM UNNEST(p_values) AS value
    );
END;
$$;

-- ------------------------------------------------------------
-- 7. STANDARD ERROR FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_standard_error(
    p_population_id BIGINT,
    p_sample_size INTEGER,
    p_method sampling_method
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_population_size BIGINT;
    v_population_sd NUMERIC;
    v_standard_error NUMERIC;
BEGIN
    IF p_sample_size <= 0 THEN
        RAISE EXCEPTION 'Sample size must be positive.';
    END IF;

    SELECT
        population_size,
        population_standard_deviation
    INTO
        v_population_size,
        v_population_sd
    FROM population_statistics
    WHERE population_id = p_population_id;

    IF NOT FOUND OR v_population_size = 0 THEN
        RAISE EXCEPTION 'Population does not exist or is empty.';
    END IF;

    IF
        p_method = 'WITHOUT_REPLACEMENT'
        AND p_sample_size > v_population_size
    THEN
        RAISE EXCEPTION
            'Sample size cannot exceed population size.';
    END IF;

    v_standard_error :=
        v_population_sd / SQRT(p_sample_size::NUMERIC);

    IF p_method = 'WITHOUT_REPLACEMENT' THEN
        IF v_population_size = 1 THEN
            RETURN 0;
        END IF;

        v_standard_error :=
            v_standard_error
            * SQRT(
                (v_population_size - p_sample_size)::NUMERIC
                / (v_population_size - 1)
            );
    END IF;

    RETURN v_standard_error;
END;
$$;

-- ------------------------------------------------------------
-- 8. EXPERIMENT VALIDATION TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_sampling_experiment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_population_size BIGINT;
BEGIN
    SELECT population_size
    INTO v_population_size
    FROM population_statistics
    WHERE population_id = NEW.population_id;

    IF NOT FOUND OR v_population_size = 0 THEN
        RAISE EXCEPTION 'Cannot sample an empty population.';
    END IF;

    IF
        NEW.sampling_method = 'WITHOUT_REPLACEMENT'
        AND NEW.sample_size > v_population_size
    THEN
        RAISE EXCEPTION
            'Sample size exceeds population size.';
    END IF;

    IF NEW.status = 'COMPLETED' THEN
        RAISE EXCEPTION
            'Experiments must be completed through the workflow function.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_sampling_experiment
    ON sampling_experiments;

CREATE TRIGGER trg_validate_sampling_experiment
BEFORE INSERT OR UPDATE OF
    population_id,
    sample_size,
    sampling_method,
    status
ON sampling_experiments
FOR EACH ROW
EXECUTE FUNCTION validate_sampling_experiment();

-- ------------------------------------------------------------
-- 9. CREATE EXPERIMENT FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_sampling_experiment(
    p_population_id BIGINT,
    p_experiment_name VARCHAR(150),
    p_sample_size INTEGER,
    p_repetitions INTEGER,
    p_method sampling_method DEFAULT 'WITH_REPLACEMENT',
    p_seed BIGINT DEFAULT 2026
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_experiment_id BIGINT;
BEGIN
    IF p_experiment_name IS NULL OR BTRIM(p_experiment_name) = '' THEN
        RAISE EXCEPTION 'Experiment name is required.';
    END IF;

    INSERT INTO sampling_experiments (
        population_id,
        experiment_name,
        sampling_method,
        sample_size,
        repetitions,
        random_seed
    )
    VALUES (
        p_population_id,
        p_experiment_name,
        p_method,
        p_sample_size,
        p_repetitions,
        p_seed
    )
    RETURNING experiment_id INTO v_experiment_id;

    RETURN v_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- 10. EXECUTE SAMPLING EXPERIMENT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION execute_sampling_experiment(
    p_experiment_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_experiment RECORD;
    v_population_size BIGINT;
    v_population_mean NUMERIC;
    v_population_sd NUMERIC;
    v_repetition INTEGER;
    v_sample_mean NUMERIC;
    v_sample_variance NUMERIC;
    v_sample_sd NUMERIC;
    v_sample_values NUMERIC[];
    v_observation RECORD;
    v_sampling_mean NUMERIC;
    v_empirical_se NUMERIC;
    v_theoretical_se NUMERIC;
BEGIN
    SELECT *
    INTO v_experiment
    FROM sampling_experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF v_experiment.status <> 'CREATED' THEN
        RAISE EXCEPTION
            'Only CREATED experiments can be executed.';
    END IF;

    SELECT
        population_size,
        population_mean,
        population_standard_deviation
    INTO
        v_population_size,
        v_population_mean,
        v_population_sd
    FROM population_statistics
    WHERE population_id = v_experiment.population_id;

    IF v_population_size = 0 THEN
        RAISE EXCEPTION 'Population is empty.';
    END IF;

    IF
        v_experiment.sampling_method = 'WITHOUT_REPLACEMENT'
        AND v_experiment.sample_size > v_population_size
    THEN
        RAISE EXCEPTION 'Invalid sample size.';
    END IF;

    UPDATE sampling_experiments
    SET status = 'RUNNING'
    WHERE experiment_id = p_experiment_id;

    -- Seed the session-local pseudo-random generator.
    PERFORM SETSEED(
        MOD(
            ABS(v_experiment.random_seed::NUMERIC),
            1000000
        )::DOUBLE PRECISION / 1000000.0
    );

    FOR v_repetition IN 1..v_experiment.repetitions LOOP

        IF v_experiment.sampling_method = 'WITH_REPLACEMENT' THEN

            SELECT ARRAY_AGG(
                observation_id ORDER BY position
            )
            INTO v_sample_values
            FROM (
                SELECT
                    observation_id,
                    ROW_NUMBER() OVER () AS position
                FROM (
                    SELECT observation_id
                    FROM population_observations
                    WHERE population_id = v_experiment.population_id
                    ORDER BY RANDOM()
                    LIMIT v_experiment.sample_size
                ) selected
            ) numbered;

            -- WITH replacement permits repeated population records.
            -- A separate draw is made for each observation.
            SELECT ARRAY_AGG(
                selected.observation_id
                ORDER BY selected.position
            )
            INTO v_sample_values
            FROM (
                SELECT
                    draw.position,
                    population.observation_id
                FROM GENERATE_SERIES(
                    1,
                    v_experiment.sample_size
                ) AS draw(position)
                CROSS JOIN LATERAL (
                    SELECT observation_id
                    FROM population_observations
                    WHERE population_id = v_experiment.population_id
                    ORDER BY RANDOM()
                    LIMIT 1
                ) population
            ) selected;

        ELSE

            SELECT ARRAY_AGG(observation_id)
            INTO v_sample_values
            FROM (
                SELECT observation_id
                FROM population_observations
                WHERE population_id = v_experiment.population_id
                ORDER BY RANDOM()
                LIMIT v_experiment.sample_size
            ) selected;

        END IF;

        IF CARDINALITY(v_sample_values) <> v_experiment.sample_size THEN
            RAISE EXCEPTION
                'Sampling produced an incomplete sample.';
        END IF;

        SELECT
            AVG(observation_value),
            VAR_SAMP(observation_value),
            STDDEV_SAMP(observation_value)
        INTO
            v_sample_mean,
            v_sample_variance,
            v_sample_sd
        FROM population_observations
        WHERE observation_id = ANY(v_sample_values);

        IF v_experiment.sample_size = 1 THEN
            v_sample_variance := 0;
            v_sample_sd := 0;
        END IF;

        INSERT INTO sampling_draws (
            experiment_id,
            repetition_number,
            sample_mean,
            sample_variance,
            sample_standard_deviation
        )
        VALUES (
            p_experiment_id,
            v_repetition,
            v_sample_mean,
            v_sample_variance,
            v_sample_sd
        );

        -- Store actual selected observations for auditability.
        FOREACH v_observation IN ARRAY v_sample_values LOOP
            INSERT INTO sample_observations (
                experiment_id,
                repetition_number,
                observation_id,
                observation_value
            )
            SELECT
                p_experiment_id,
                v_repetition,
                observation_id,
                observation_value
            FROM population_observations
            WHERE observation_id = v_observation;
        END LOOP;

    END LOOP;

    SELECT
        AVG(sample_mean),
        STDDEV_SAMP(sample_mean)
    INTO
        v_sampling_mean,
        v_empirical_se
    FROM sampling_draws
    WHERE experiment_id = p_experiment_id;

    v_theoretical_se := calculate_standard_error(
        v_experiment.population_id,
        v_experiment.sample_size,
        v_experiment.sampling_method
    );

    INSERT INTO experiment_results (
        experiment_id,
        population_mean,
        sampling_mean,
        theoretical_standard_error,
        empirical_standard_error,
        bias
    )
    VALUES (
        p_experiment_id,
        v_population_mean,
        v_sampling_mean,
        v_theoretical_se,
        COALESCE(v_empirical_se, 0),
        v_sampling_mean - v_population_mean
    );

    UPDATE sampling_experiments
    SET
        status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id;

EXCEPTION
    WHEN OTHERS THEN
        -- The exception propagates to the caller. PostgreSQL rolls
        -- back the failed transaction, preserving workflow integrity.
        RAISE;
END;
$$;

-- ------------------------------------------------------------
-- 11. CONFIDENCE INTERVAL FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION normal_confidence_interval(
    p_estimate NUMERIC,
    p_standard_error NUMERIC,
    p_confidence_level NUMERIC DEFAULT 0.95
)
RETURNS TABLE (
    estimate NUMERIC,
    lower_bound NUMERIC,
    upper_bound NUMERIC,
    confidence_level NUMERIC
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_critical_value NUMERIC;
    v_margin NUMERIC;
BEGIN
    IF p_estimate IS NULL OR NOT isfinite(p_estimate::DOUBLE PRECISION) THEN
        RAISE EXCEPTION 'Estimate must be finite.';
    END IF;

    IF
        p_standard_error IS NULL
        OR NOT isfinite(p_standard_error::DOUBLE PRECISION)
        OR p_standard_error < 0
    THEN
        RAISE EXCEPTION 'Invalid standard error.';
    END IF;

    CASE p_confidence_level
        WHEN 0.90 THEN v_critical_value := 1.645;
        WHEN 0.95 THEN v_critical_value := 1.96;
        WHEN 0.99 THEN v_critical_value := 2.576;
        ELSE
            RAISE EXCEPTION
                'Supported confidence levels: 0.90, 0.95, 0.99.';
    END CASE;

    v_margin := v_critical_value * p_standard_error;

    RETURN QUERY
    SELECT
        p_estimate,
        p_estimate - v_margin,
        p_estimate + v_margin,
        p_confidence_level;
END;
$$;

-- ------------------------------------------------------------
-- 12. DEMONSTRATION DATA
-- ------------------------------------------------------------

INSERT INTO populations (
    population_name,
    description
)
VALUES (
    'CUSTOMER_TRANSACTIONS',
    'Customer transaction values used for sampling analysis.'
)
ON CONFLICT (population_name) DO NOTHING;

-- Seed data is inserted only when the population is empty.
INSERT INTO population_observations (
    population_id,
    observation_value
)
SELECT
    p.population_id,
    generated.observation_value
FROM populations p
CROSS JOIN LATERAL (
    SELECT 5.0::NUMERIC AS observation_value
    FROM GENERATE_SERIES(1, 500)

    UNION ALL

    SELECT 15.0::NUMERIC
    FROM GENERATE_SERIES(1, 250)

    UNION ALL

    SELECT 30.0::NUMERIC
    FROM GENERATE_SERIES(1, 150)

    UNION ALL

    SELECT 100.0::NUMERIC
    FROM GENERATE_SERIES(1, 100)
) generated
WHERE p.population_name = 'CUSTOMER_TRANSACTIONS'
AND NOT EXISTS (
    SELECT 1
    FROM population_observations existing
    WHERE existing.population_id = p.population_id
);

COMMIT;

-- ------------------------------------------------------------
-- 13. POPULATION RETRIEVAL
-- ------------------------------------------------------------

SELECT *
FROM population_statistics
ORDER BY population_id;

-- ------------------------------------------------------------
-- 14. CREATE AND EXECUTE EXPERIMENTS
-- ------------------------------------------------------------

BEGIN;

SELECT create_sampling_experiment(
    population_id,
    'CLT_SAMPLE_SIZE_10',
    10,
    1000,
    'WITH_REPLACEMENT',
    2026
)
FROM populations
WHERE population_name = 'CUSTOMER_TRANSACTIONS';

SELECT execute_sampling_experiment(
    experiment_id
)
FROM sampling_experiments
WHERE experiment_name = 'CLT_SAMPLE_SIZE_10'
AND status = 'CREATED';

COMMIT;

-- ------------------------------------------------------------
-- 15. CENTRAL LIMIT THEOREM EXPERIMENTS
-- ------------------------------------------------------------

BEGIN;

DO $$
DECLARE
    v_population_id BIGINT;
    v_sample_size INTEGER;
    v_experiment_id BIGINT;
BEGIN
    SELECT population_id
    INTO v_population_id
    FROM populations
    WHERE population_name = 'CUSTOMER_TRANSACTIONS';

    FOREACH v_sample_size IN ARRAY ARRAY[
        2, 5, 10, 30, 50, 100
    ]
    LOOP
        SELECT create_sampling_experiment(
            v_population_id,
            'CLT_SAMPLE_SIZE_' || v_sample_size,
            v_sample_size,
            2000,
            'WITH_REPLACEMENT',
            2026 + v_sample_size
        )
        INTO v_experiment_id;

        PERFORM execute_sampling_experiment(v_experiment_id);
    END LOOP;
END;
$$;

COMMIT;

-- ------------------------------------------------------------
-- 16. SAMPLING DISTRIBUTION REPORT
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    e.sample_size,
    e.repetitions,
    ROUND(r.population_mean, 4) AS population_mean,
    ROUND(r.sampling_mean, 4) AS sampling_mean,
    ROUND(r.bias, 4) AS bias,
    ROUND(r.theoretical_standard_error, 4) AS theoretical_se,
    ROUND(r.empirical_standard_error, 4) AS empirical_se,
    e.status
FROM sampling_experiments e
JOIN experiment_results r
    ON e.experiment_id = r.experiment_id
ORDER BY e.sample_size;

-- ------------------------------------------------------------
-- 17. LAW OF LARGE NUMBERS
-- ------------------------------------------------------------

-- Each row represents one independently generated sample.
WITH sample_sizes AS (
    SELECT UNNEST(
        ARRAY[10, 50, 100, 500, 1000]
    ) AS sample_size
),
random_samples AS (
    SELECT
        s.sample_size,
        AVG(
            (
                SELECT observation_value
                FROM population_observations
                WHERE population_id = p.population_id
                ORDER BY RANDOM()
                LIMIT 1
            )
        ) AS sample_mean
    FROM sample_sizes s
    CROSS JOIN populations p
    WHERE p.population_name = 'CUSTOMER_TRANSACTIONS'
    GROUP BY s.sample_size, p.population_id
)
SELECT
    r.sample_size,
    ROUND(r.sample_mean, 4) AS sample_mean,
    ROUND(p.population_mean, 4) AS population_mean,
    ROUND(
        ABS(r.sample_mean - p.population_mean),
        4
    ) AS absolute_error
FROM random_samples r
CROSS JOIN population_statistics p
WHERE p.population_name = 'CUSTOMER_TRANSACTIONS'
ORDER BY r.sample_size;

-- ------------------------------------------------------------
-- 18. FINITE POPULATION CORRECTION
-- ------------------------------------------------------------

WITH sample_sizes AS (
    SELECT UNNEST(
        ARRAY[10, 50, 100, 250, 500]
    ) AS sample_size
)
SELECT
    s.sample_size,
    ROUND(
        calculate_standard_error(
            p.population_id,
            s.sample_size,
            'WITH_REPLACEMENT'
        ),
        5
    ) AS se_with_replacement,
    ROUND(
        calculate_standard_error(
            p.population_id,
            s.sample_size,
            'WITHOUT_REPLACEMENT'
        ),
        5
    ) AS se_without_replacement
FROM sample_sizes s
CROSS JOIN populations p
WHERE p.population_name = 'CUSTOMER_TRANSACTIONS'
ORDER BY s.sample_size;

-- ------------------------------------------------------------
-- 19. CONFIDENCE INTERVAL REPORT
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    ci.estimate,
    ci.lower_bound,
    ci.upper_bound,
    ci.confidence_level
FROM sampling_experiments e
JOIN experiment_results r
    ON e.experiment_id = r.experiment_id
CROSS JOIN LATERAL normal_confidence_interval(
    r.sampling_mean,
    r.theoretical_standard_error,
    0.95
) ci
WHERE e.status = 'COMPLETED'
ORDER BY e.sample_size;

-- ------------------------------------------------------------
-- 20. SAMPLE OBSERVATION AUDIT
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    so.repetition_number,
    COUNT(*) AS observations_in_sample,
    AVG(so.observation_value) AS actual_sample_mean
FROM sample_observations so
JOIN sampling_experiments e
    ON so.experiment_id = e.experiment_id
GROUP BY
    e.experiment_name,
    so.repetition_number
ORDER BY
    e.experiment_name,
    so.repetition_number
LIMIT 50;

-- ------------------------------------------------------------
-- 21. EXPERIMENT ELIGIBILITY VALIDATION
-- ------------------------------------------------------------

SELECT
    p.population_name,
    e.experiment_name,
    e.sample_size,
    ps.population_size,
    CASE
        WHEN ps.population_size = 0
            THEN 'INELIGIBLE: EMPTY POPULATION'
        WHEN e.sample_size > ps.population_size
            AND e.sampling_method = 'WITHOUT_REPLACEMENT'
            THEN 'INELIGIBLE: SAMPLE TOO LARGE'
        WHEN e.repetitions < 2
            THEN 'INELIGIBLE: INSUFFICIENT REPETITIONS'
        ELSE 'ELIGIBLE'
    END AS eligibility
FROM sampling_experiments e
JOIN populations p
    ON e.population_id = p.population_id
JOIN population_statistics ps
    ON p.population_id = ps.population_id
ORDER BY e.experiment_id;

-- ------------------------------------------------------------
-- 22. FAILED VALIDATION EXAMPLE
-- ------------------------------------------------------------

-- The following statement demonstrates constraint enforcement.
-- It is isolated in a subtransaction so the main script remains valid.

DO $$
BEGIN
    BEGIN
        PERFORM calculate_standard_error(
            (
                SELECT population_id
                FROM populations
                WHERE population_name = 'CUSTOMER_TRANSACTIONS'
            ),
            2000,
            'WITHOUT_REPLACEMENT'
        );

        RAISE EXCEPTION
            'Invalid sampling request was unexpectedly accepted.';

    EXCEPTION
        WHEN raise_exception THEN
            RAISE NOTICE
                'Invalid sampling request correctly rejected: %',
                SQLERRM;
    END;
END;
$$;

-- ------------------------------------------------------------
-- 23. WORKFLOW SUMMARY
-- ------------------------------------------------------------

SELECT
    status,
    COUNT(*) AS experiment_count,
    AVG(sample_size) AS average_sample_size,
    AVG(repetitions) AS average_repetitions
FROM sampling_experiments
GROUP BY status
ORDER BY status;

-- ------------------------------------------------------------
-- 24. COMPLETED EXPERIMENT PERFORMANCE REPORT
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    e.sampling_method,
    e.sample_size,
    e.repetitions,
    ROUND(r.empirical_standard_error, 5) AS empirical_se,
    ROUND(r.theoretical_standard_error, 5) AS theoretical_se,
    ROUND(
        ABS(
            r.empirical_standard_error
            - r.theoretical_standard_error
        ),
        5
    ) AS se_difference
FROM sampling_experiments e
JOIN experiment_results r
    ON e.experiment_id = r.experiment_id
WHERE e.status = 'COMPLETED'
ORDER BY e.sample_size;

-- ============================================================
-- END OF SAMPLING DISTRIBUTIONS SCRIPT
-- ============================================================
