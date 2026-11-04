/*
    PROBABILITY DISTRIBUTIONS
    ========================

    PostgreSQL 14+

    Relational statistical calculation and simulation system.

    Supported distributions:
    1. Bernoulli
    2. Binomial
    3. Geometric
    4. Poisson
    5. Uniform
    6. Normal
    7. Exponential

    Features:
    - Distribution catalog
    - Parameter validation
    - Experiment management
    - Probability mass and density calculations
    - Cumulative distribution calculations
    - Theoretical statistical properties
    - Simulation result storage
    - Aggregate reporting
    - Validation triggers
    - Transactional experiment processing

    Run in a dedicated learning database.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS probability_lab;

SET search_path TO probability_lab, public;

-- ============================================================
-- 1. DISTRIBUTION DOMAIN
-- ============================================================

CREATE TYPE distribution_kind AS ENUM (
    'BERNOULLI',
    'BINOMIAL',
    'GEOMETRIC',
    'POISSON',
    'UNIFORM',
    'NORMAL',
    'EXPONENTIAL'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

-- ============================================================
-- 2. DISTRIBUTION CATALOG
-- ============================================================

CREATE TABLE distribution_catalog (
    distribution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    distribution_type distribution_kind NOT NULL UNIQUE,

    description TEXT NOT NULL,

    is_discrete BOOLEAN NOT NULL,

    parameter_names TEXT[] NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_parameter_names
        CHECK (cardinality(parameter_names) > 0)
);

INSERT INTO distribution_catalog (
    distribution_type,
    description,
    is_discrete,
    parameter_names
)
VALUES
(
    'BERNOULLI',
    'Single binary trial with success probability p.',
    TRUE,
    ARRAY['p']
),
(
    'BINOMIAL',
    'Number of successes in n independent Bernoulli trials.',
    TRUE,
    ARRAY['n', 'p']
),
(
    'GEOMETRIC',
    'Number of independent trials until the first success.',
    TRUE,
    ARRAY['p']
),
(
    'POISSON',
    'Event count in a fixed interval with rate lambda.',
    TRUE,
    ARRAY['lambda']
),
(
    'UNIFORM',
    'Continuous uniform distribution on [a,b].',
    FALSE,
    ARRAY['a', 'b']
),
(
    'NORMAL',
    'Gaussian distribution parameterized by mu and sigma.',
    FALSE,
    ARRAY['mu', 'sigma']
),
(
    'EXPONENTIAL',
    'Continuous waiting-time distribution parameterized by rate lambda.',
    FALSE,
    ARRAY['lambda']
);

-- ============================================================
-- 3. DISTRIBUTION PARAMETER VALIDATION
-- ============================================================

CREATE FUNCTION validate_distribution_parameters(
    p_type distribution_kind,
    p_parameters JSONB
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_n NUMERIC;
    v_p NUMERIC;
    v_lambda NUMERIC;
    v_a NUMERIC;
    v_b NUMERIC;
    v_mu NUMERIC;
    v_sigma NUMERIC;
    v_value JSONB;
    v_key TEXT;
BEGIN
    IF p_parameters IS NULL
       OR jsonb_typeof(p_parameters) <> 'object' THEN
        RAISE EXCEPTION 'Parameters must be a JSON object.';
    END IF;

    -- Reject unknown parameters and non-numeric values.
    FOR v_key, v_value IN
        SELECT key, value
        FROM jsonb_each(p_parameters)
    LOOP
        IF jsonb_typeof(v_value) <> 'number' THEN
            RAISE EXCEPTION
                'Parameter % must be numeric.', v_key;
        END IF;

        IF (v_value #>> '{}')::NUMERIC IN (
            'NaN'::NUMERIC,
            'Infinity'::NUMERIC,
            '-Infinity'::NUMERIC
        ) THEN
            RAISE EXCEPTION
                'Parameter % must be finite.', v_key;
        END IF;
    END LOOP;

    CASE p_type

        WHEN 'BERNOULLI' THEN
            IF p_parameters - ARRAY['p']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'p') THEN
                RAISE EXCEPTION
                    'Bernoulli requires exactly parameter p.';
            END IF;

            v_p := (p_parameters ->> 'p')::NUMERIC;

            IF v_p < 0 OR v_p > 1 THEN
                RAISE EXCEPTION
                    'Bernoulli p must be in [0,1].';
            END IF;

        WHEN 'BINOMIAL' THEN
            IF p_parameters - ARRAY['n','p']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'n')
               OR NOT (p_parameters ? 'p') THEN
                RAISE EXCEPTION
                    'Binomial requires n and p.';
            END IF;

            v_n := (p_parameters ->> 'n')::NUMERIC;
            v_p := (p_parameters ->> 'p')::NUMERIC;

            IF v_n < 0 OR v_n > 100000
               OR v_n <> TRUNC(v_n) THEN
                RAISE EXCEPTION
                    'Binomial n must be an integer in [0,100000].';
            END IF;

            IF v_p < 0 OR v_p > 1 THEN
                RAISE EXCEPTION
                    'Binomial p must be in [0,1].';
            END IF;

        WHEN 'GEOMETRIC' THEN
            IF p_parameters - ARRAY['p']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'p') THEN
                RAISE EXCEPTION
                    'Geometric requires parameter p.';
            END IF;

            v_p := (p_parameters ->> 'p')::NUMERIC;

            IF v_p <= 0 OR v_p > 1 THEN
                RAISE EXCEPTION
                    'Geometric p must be in (0,1].';
            END IF;

        WHEN 'POISSON' THEN
            IF p_parameters - ARRAY['lambda']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'lambda') THEN
                RAISE EXCEPTION
                    'Poisson requires lambda.';
            END IF;

            v_lambda := (p_parameters ->> 'lambda')::NUMERIC;

            IF v_lambda < 0 OR v_lambda > 100000 THEN
                RAISE EXCEPTION
                    'Poisson lambda must be in [0,100000].';
            END IF;

        WHEN 'UNIFORM' THEN
            IF p_parameters - ARRAY['a','b']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'a')
               OR NOT (p_parameters ? 'b') THEN
                RAISE EXCEPTION
                    'Uniform requires a and b.';
            END IF;

            v_a := (p_parameters ->> 'a')::NUMERIC;
            v_b := (p_parameters ->> 'b')::NUMERIC;

            IF v_a >= v_b THEN
                RAISE EXCEPTION
                    'Uniform requires a < b.';
            END IF;

        WHEN 'NORMAL' THEN
            IF p_parameters - ARRAY['mu','sigma']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'mu')
               OR NOT (p_parameters ? 'sigma') THEN
                RAISE EXCEPTION
                    'Normal requires mu and sigma.';
            END IF;

            v_mu := (p_parameters ->> 'mu')::NUMERIC;
            v_sigma := (p_parameters ->> 'sigma')::NUMERIC;

            IF v_sigma <= 0 THEN
                RAISE EXCEPTION
                    'Normal sigma must be positive.';
            END IF;

        WHEN 'EXPONENTIAL' THEN
            IF p_parameters - ARRAY['lambda']::TEXT[] <> '{}'::JSONB
               OR NOT (p_parameters ? 'lambda') THEN
                RAISE EXCEPTION
                    'Exponential requires lambda.';
            END IF;

            v_lambda := (p_parameters ->> 'lambda')::NUMERIC;

            IF v_lambda <= 0 THEN
                RAISE EXCEPTION
                    'Exponential lambda must be positive.';
            END IF;

    END CASE;

    RETURN TRUE;
END;
$$;

-- ============================================================
-- 4. EXPERIMENT MANAGEMENT
-- ============================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_name VARCHAR(150) NOT NULL,

    distribution_id BIGINT NOT NULL
        REFERENCES distribution_catalog(distribution_id),

    parameters JSONB NOT NULL,

    sample_size INTEGER NOT NULL,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    requested_by VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_sample_size
        CHECK (sample_size BETWEEN 1 AND 1000000),

    CONSTRAINT valid_experiment_name
        CHECK (length(trim(experiment_name)) > 0),

    CONSTRAINT valid_requested_by
        CHECK (length(trim(requested_by)) > 0),

    CONSTRAINT valid_completion_times
        CHECK (
            completed_at IS NULL
            OR (
                started_at IS NOT NULL
                AND completed_at >= started_at
            )
        )
);

CREATE INDEX idx_experiments_status_created
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_distribution
    ON experiments(distribution_id, created_at DESC);

CREATE INDEX idx_experiments_parameters
    ON experiments USING GIN(parameters);

-- ============================================================
-- 5. EXPERIMENT PARAMETER TRIGGER
-- ============================================================

CREATE FUNCTION enforce_experiment_parameters()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_type distribution_kind;
BEGIN
    SELECT distribution_type
    INTO STRICT v_type
    FROM distribution_catalog
    WHERE distribution_id = NEW.distribution_id;

    PERFORM validate_distribution_parameters(
        v_type,
        NEW.parameters
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment_parameters
BEFORE INSERT OR UPDATE OF distribution_id, parameters
ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_parameters();

-- ============================================================
-- 6. PROBABILITY MATHEMATICAL FUNCTIONS
-- ============================================================

CREATE FUNCTION log_factorial(p_n INTEGER)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    i INTEGER;
    result DOUBLE PRECISION := 0;
BEGIN
    IF p_n < 0 OR p_n > 100000 THEN
        RAISE EXCEPTION
            'Factorial input must be between 0 and 100000.';
    END IF;

    FOR i IN 2..p_n LOOP
        result := result + LN(i::DOUBLE PRECISION);
    END LOOP;

    RETURN result;
END;
$$;

CREATE FUNCTION log_combination(
    p_n INTEGER,
    p_k INTEGER
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_n < 0 OR p_n > 100000 THEN
        RAISE EXCEPTION 'Invalid n.';
    END IF;

    IF p_k < 0 OR p_k > p_n THEN
        RETURN '-Infinity'::DOUBLE PRECISION;
    END IF;

    RETURN log_factorial(p_n)
        - log_factorial(p_k)
        - log_factorial(p_n - p_k);
END;
$$;

-- ============================================================
-- 7. PROBABILITY MASS FUNCTION
-- ============================================================

CREATE FUNCTION probability_mass(
    p_type distribution_kind,
    p_parameters JSONB,
    p_x INTEGER
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    n INTEGER;
    k INTEGER;
    p DOUBLE PRECISION;
    lambda DOUBLE PRECISION;
BEGIN
    PERFORM validate_distribution_parameters(
        p_type,
        p_parameters
    );

    CASE p_type

        WHEN 'BERNOULLI' THEN
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;

            IF p_x = 0 THEN
                RETURN 1.0 - p;
            ELSIF p_x = 1 THEN
                RETURN p;
            END IF;

            RETURN 0.0;

        WHEN 'BINOMIAL' THEN
            n := (p_parameters ->> 'n')::INTEGER;
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;
            k := p_x;

            IF k < 0 OR k > n THEN
                RETURN 0.0;
            END IF;

            IF p = 0 THEN
                RETURN CASE WHEN k = 0 THEN 1.0 ELSE 0.0 END;
            END IF;

            IF p = 1 THEN
                RETURN CASE WHEN k = n THEN 1.0 ELSE 0.0 END;
            END IF;

            RETURN EXP(
                log_combination(n, k)
                + k * LN(p)
                + (n - k) * LN(1.0 - p)
            );

        WHEN 'GEOMETRIC' THEN
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;

            IF p_x < 1 THEN
                RETURN 0.0;
            END IF;

            IF p = 1 THEN
                RETURN CASE WHEN p_x = 1 THEN 1.0 ELSE 0.0 END;
            END IF;

            RETURN EXP(
                LN(p) + (p_x - 1) * LN(1.0 - p)
            );

        WHEN 'POISSON' THEN
            lambda := (p_parameters ->> 'lambda')::DOUBLE PRECISION;

            IF p_x < 0 THEN
                RETURN 0.0;
            END IF;

            IF lambda = 0 THEN
                RETURN CASE WHEN p_x = 0 THEN 1.0 ELSE 0.0 END;
            END IF;

            RETURN EXP(
                -lambda
                + p_x * LN(lambda)
                - log_factorial(p_x)
            );

        ELSE
            RAISE EXCEPTION
                '% is continuous and does not have a PMF.',
                p_type;
    END CASE;
END;
$$;

-- ============================================================
-- 8. PROBABILITY DENSITY FUNCTION
-- ============================================================

CREATE FUNCTION probability_density(
    p_type distribution_kind,
    p_parameters JSONB,
    p_x DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    a DOUBLE PRECISION;
    b DOUBLE PRECISION;
    mu DOUBLE PRECISION;
    sigma DOUBLE PRECISION;
    lambda DOUBLE PRECISION;
    z DOUBLE PRECISION;
BEGIN
    PERFORM validate_distribution_parameters(
        p_type,
        p_parameters
    );

    IF NOT isfinite(p_x) THEN
        RAISE EXCEPTION 'Input x must be finite.';
    END IF;

    CASE p_type

        WHEN 'UNIFORM' THEN
            a := (p_parameters ->> 'a')::DOUBLE PRECISION;
            b := (p_parameters ->> 'b')::DOUBLE PRECISION;

            IF p_x < a OR p_x > b THEN
                RETURN 0.0;
            END IF;

            RETURN 1.0 / (b - a);

        WHEN 'NORMAL' THEN
            mu := (p_parameters ->> 'mu')::DOUBLE PRECISION;
            sigma := (p_parameters ->> 'sigma')::DOUBLE PRECISION;

            z := (p_x - mu) / sigma;

            RETURN EXP(-0.5 * z * z)
                / (sigma * SQRT(2.0 * PI()));

        WHEN 'EXPONENTIAL' THEN
            lambda := (p_parameters ->> 'lambda')::DOUBLE PRECISION;

            IF p_x < 0 THEN
                RETURN 0.0;
            END IF;

            RETURN lambda * EXP(-lambda * p_x);

        ELSE
            RAISE EXCEPTION
                '% is discrete and does not have a PDF.',
                p_type;
    END CASE;
END;
$$;

-- ============================================================
-- 9. CUMULATIVE DISTRIBUTION FUNCTION
-- ============================================================

CREATE FUNCTION normal_cdf(
    p_x DOUBLE PRECISION,
    p_mu DOUBLE PRECISION,
    p_sigma DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_sigma <= 0
       OR NOT isfinite(p_mu)
       OR NOT isfinite(p_sigma)
       OR NOT isfinite(p_x) THEN
        RAISE EXCEPTION 'Invalid normal distribution input.';
    END IF;

    RETURN 0.5 * (
        1.0 + ERF(
            (p_x - p_mu) / (p_sigma * SQRT(2.0))
        )
    );
END;
$$;

CREATE FUNCTION probability_cdf(
    p_type distribution_kind,
    p_parameters JSONB,
    p_x DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    n INTEGER;
    k INTEGER;
    i INTEGER;
    p DOUBLE PRECISION;
    lambda DOUBLE PRECISION;
    a DOUBLE PRECISION;
    b DOUBLE PRECISION;
    mu DOUBLE PRECISION;
    sigma DOUBLE PRECISION;
    result DOUBLE PRECISION := 0;
BEGIN
    PERFORM validate_distribution_parameters(
        p_type,
        p_parameters
    );

    IF NOT isfinite(p_x) THEN
        RAISE EXCEPTION 'CDF input must be finite.';
    END IF;

    CASE p_type

        WHEN 'BERNOULLI' THEN
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;

            IF p_x < 0 THEN RETURN 0.0; END IF;
            IF p_x < 1 THEN RETURN 1.0 - p; END IF;

            RETURN 1.0;

        WHEN 'BINOMIAL' THEN
            n := (p_parameters ->> 'n')::INTEGER;
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;

            IF p_x < 0 THEN RETURN 0.0; END IF;
            IF p_x >= n THEN RETURN 1.0; END IF;

            k := FLOOR(p_x)::INTEGER;

            FOR i IN 0..k LOOP
                result := result + probability_mass(
                    p_type,
                    p_parameters,
                    i
                );
            END LOOP;

            RETURN LEAST(1.0, result);

        WHEN 'GEOMETRIC' THEN
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;

            IF p_x < 1 THEN RETURN 0.0; END IF;
            IF p = 1 THEN RETURN 1.0; END IF;

            k := FLOOR(p_x)::INTEGER;

            RETURN -EXP(k * LN(1.0 - p)) + 1.0;

        WHEN 'POISSON' THEN
            lambda := (p_parameters ->> 'lambda')::DOUBLE PRECISION;

            IF p_x < 0 THEN RETURN 0.0; END IF;
            IF lambda = 0 THEN RETURN 1.0; END IF;

            IF p_x > lambda + 1000 * SQRT(lambda + 1) + 1000 THEN
                RETURN 1.0;
            END IF;

            k := FLOOR(p_x)::INTEGER;

            FOR i IN 0..k LOOP
                result := result + probability_mass(
                    p_type,
                    p_parameters,
                    i
                );
            END LOOP;

            RETURN LEAST(1.0, result);

        WHEN 'UNIFORM' THEN
            a := (p_parameters ->> 'a')::DOUBLE PRECISION;
            b := (p_parameters ->> 'b')::DOUBLE PRECISION;

            IF p_x <= a THEN RETURN 0.0; END IF;
            IF p_x >= b THEN RETURN 1.0; END IF;

            RETURN (p_x - a) / (b - a);

        WHEN 'NORMAL' THEN
            mu := (p_parameters ->> 'mu')::DOUBLE PRECISION;
            sigma := (p_parameters ->> 'sigma')::DOUBLE PRECISION;

            RETURN normal_cdf(p_x, mu, sigma);

        WHEN 'EXPONENTIAL' THEN
            lambda := (p_parameters ->> 'lambda')::DOUBLE PRECISION;

            IF p_x < 0 THEN RETURN 0.0; END IF;

            RETURN -EXP(-lambda * p_x) + 1.0;

    END CASE;

    RAISE EXCEPTION 'Unsupported distribution type.';
END;
$$;

-- ============================================================
-- 10. THEORETICAL STATISTICAL PROPERTIES
-- ============================================================

CREATE FUNCTION distribution_statistics(
    p_type distribution_kind,
    p_parameters JSONB
)
RETURNS TABLE (
    theoretical_mean DOUBLE PRECISION,
    theoretical_variance DOUBLE PRECISION,
    standard_deviation DOUBLE PRECISION
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    n DOUBLE PRECISION;
    p DOUBLE PRECISION;
    lambda DOUBLE PRECISION;
    a DOUBLE PRECISION;
    b DOUBLE PRECISION;
    mu DOUBLE PRECISION;
    sigma DOUBLE PRECISION;
    v_mean DOUBLE PRECISION;
    v_variance DOUBLE PRECISION;
BEGIN
    PERFORM validate_distribution_parameters(
        p_type,
        p_parameters
    );

    CASE p_type

        WHEN 'BERNOULLI' THEN
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;
            v_mean := p;
            v_variance := p * (1 - p);

        WHEN 'BINOMIAL' THEN
            n := (p_parameters ->> 'n')::DOUBLE PRECISION;
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;
            v_mean := n * p;
            v_variance := n * p * (1 - p);

        WHEN 'GEOMETRIC' THEN
            p := (p_parameters ->> 'p')::DOUBLE PRECISION;
            v_mean := 1.0 / p;
            v_variance := (1.0 - p) / (p * p);

        WHEN 'POISSON' THEN
            lambda := (p_parameters ->> 'lambda')::DOUBLE PRECISION;
            v_mean := lambda;
            v_variance := lambda;

        WHEN 'UNIFORM' THEN
            a := (p_parameters ->> 'a')::DOUBLE PRECISION;
            b := (p_parameters ->> 'b')::DOUBLE PRECISION;
            v_mean := (a + b) / 2.0;
            v_variance := (b - a) ^ 2 / 12.0;

        WHEN 'NORMAL' THEN
            mu := (p_parameters ->> 'mu')::DOUBLE PRECISION;
            sigma := (p_parameters ->> 'sigma')::DOUBLE PRECISION;
            v_mean := mu;
            v_variance := sigma ^ 2;

        WHEN 'EXPONENTIAL' THEN
            lambda := (p_parameters ->> 'lambda')::DOUBLE PRECISION;
            v_mean := 1.0 / lambda;
            v_variance := 1.0 / (lambda * lambda);

    END CASE;

    theoretical_mean := v_mean;
    theoretical_variance := v_variance;
    standard_deviation := SQRT(v_variance);

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 11. SIMULATION OBSERVATIONS
-- ============================================================

CREATE TABLE simulation_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    observation_number INTEGER NOT NULL,

    observed_value DOUBLE PRECISION NOT NULL,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_experiment_observation
        UNIQUE (experiment_id, observation_number),

    CONSTRAINT valid_observation_number
        CHECK (observation_number > 0),

    CONSTRAINT finite_observation
        CHECK (
            observed_value > '-Infinity'::DOUBLE PRECISION
            AND observed_value < 'Infinity'::DOUBLE PRECISION
        )
);

CREATE INDEX idx_observations_experiment
    ON simulation_observations(experiment_id);

CREATE INDEX idx_observations_value
    ON simulation_observations(observed_value);

-- ============================================================
-- 12. OBSERVATION DOMAIN VALIDATION
-- ============================================================

CREATE FUNCTION enforce_observation_domain()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_type distribution_kind;
    v_parameters JSONB;
    v_x DOUBLE PRECISION;
BEGIN
    SELECT c.distribution_type, e.parameters
    INTO STRICT v_type, v_parameters
    FROM experiments e
    JOIN distribution_catalog c
        ON c.distribution_id = e.distribution_id
    WHERE e.experiment_id = NEW.experiment_id;

    v_x := NEW.observed_value;

    IF v_type IN (
        'BERNOULLI',
        'BINOMIAL',
        'GEOMETRIC',
        'POISSON'
    ) THEN
        IF v_x <> TRUNC(v_x) THEN
            RAISE EXCEPTION
                'Discrete distribution requires integer observations.';
        END IF;

        IF v_x < 0 THEN
            RAISE EXCEPTION
                'Discrete observation cannot be negative.';
        END IF;
    END IF;

    IF v_type = 'BERNOULLI' AND v_x NOT IN (0, 1) THEN
        RAISE EXCEPTION 'Bernoulli observations must be 0 or 1.';
    END IF;

    IF v_type = 'BINOMIAL'
       AND v_x > (v_parameters ->> 'n')::DOUBLE PRECISION THEN
        RAISE EXCEPTION 'Binomial observation exceeds n.';
    END IF;

    IF v_type = 'GEOMETRIC' AND v_x < 1 THEN
        RAISE EXCEPTION 'Geometric observations must be at least 1.';
    END IF;

    IF v_type = 'UNIFORM' THEN
        IF v_x < (v_parameters ->> 'a')::DOUBLE PRECISION
           OR v_x > (v_parameters ->> 'b')::DOUBLE PRECISION THEN
            RAISE EXCEPTION 'Uniform observation outside support.';
        END IF;
    END IF;

    IF v_type = 'EXPONENTIAL' AND v_x < 0 THEN
        RAISE EXCEPTION 'Exponential observations cannot be negative.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_observation
BEFORE INSERT OR UPDATE OF experiment_id, observed_value
ON simulation_observations
FOR EACH ROW
EXECUTE FUNCTION enforce_observation_domain();

-- ============================================================
-- 13. EXPERIMENT EXECUTION FUNCTION
-- ============================================================

CREATE FUNCTION start_experiment(
    p_experiment_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_status experiment_status;
BEGIN
    SELECT status
    INTO STRICT v_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF v_status <> 'CREATED' THEN
        RAISE EXCEPTION
            'Only CREATED experiments can be started.';
    END IF;

    UPDATE experiments
    SET
        status = 'RUNNING',
        started_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id;
END;
$$;

CREATE FUNCTION complete_experiment(
    p_experiment_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_status experiment_status;
    v_expected INTEGER;
    v_actual BIGINT;
BEGIN
    SELECT status, sample_size
    INTO STRICT v_status, v_expected
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF v_status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Only RUNNING experiments can be completed.';
    END IF;

    SELECT COUNT(*)
    INTO v_actual
    FROM simulation_observations
    WHERE experiment_id = p_experiment_id;

    IF v_actual <> v_expected THEN
        RAISE EXCEPTION
            'Expected % observations but found %.',
            v_expected,
            v_actual;
    END IF;

    UPDATE experiments
    SET
        status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- ============================================================
-- 14. SIMULATION REPORTING VIEW
-- ============================================================

CREATE VIEW experiment_statistics AS
SELECT
    e.experiment_id,
    e.experiment_name,
    c.distribution_type,
    e.parameters,
    e.sample_size,
    e.status,
    e.requested_by,

    ds.theoretical_mean,
    ds.theoretical_variance,
    ds.standard_deviation AS theoretical_standard_deviation,

    COUNT(o.observation_id) AS recorded_samples,

    AVG(o.observed_value) AS empirical_mean,

    VAR_POP(o.observed_value) AS empirical_variance,

    STDDEV_POP(o.observed_value) AS empirical_standard_deviation,

    MIN(o.observed_value) AS minimum_observation,

    MAX(o.observed_value) AS maximum_observation

FROM experiments e

JOIN distribution_catalog c
    ON c.distribution_id = e.distribution_id

CROSS JOIN LATERAL distribution_statistics(
    c.distribution_type,
    e.parameters
) ds

LEFT JOIN simulation_observations o
    ON o.experiment_id = e.experiment_id

GROUP BY
    e.experiment_id,
    e.experiment_name,
    c.distribution_type,
    e.parameters,
    e.sample_size,
    e.status,
    e.requested_by,
    ds.theoretical_mean,
    ds.theoretical_variance,
    ds.standard_deviation;

-- ============================================================
-- 15. SAMPLE EXPERIMENTS
-- ============================================================

INSERT INTO experiments (
    experiment_name,
    distribution_id,
    parameters,
    sample_size,
    requested_by
)
SELECT
    data.experiment_name,
    catalog.distribution_id,
    data.parameters,
    data.sample_size,
    data.requested_by
FROM (
    VALUES
    (
        'Bernoulli quality inspection',
        'BERNOULLI'::distribution_kind,
        '{"p":0.95}'::JSONB,
        100,
        'quality_team'
    ),
    (
        'Binomial batch defect analysis',
        'BINOMIAL'::distribution_kind,
        '{"n":20,"p":0.05}'::JSONB,
        100,
        'quality_team'
    ),
    (
        'Geometric first success analysis',
        'GEOMETRIC'::distribution_kind,
        '{"p":0.25}'::JSONB,
        100,
        'operations_team'
    ),
    (
        'Poisson incident arrivals',
        'POISSON'::distribution_kind,
        '{"lambda":4.0}'::JSONB,
        100,
        'security_team'
    ),
    (
        'Uniform processing time',
        'UNIFORM'::distribution_kind,
        '{"a":10.0,"b":20.0}'::JSONB,
        100,
        'operations_team'
    ),
    (
        'Normal measurement variation',
        'NORMAL'::distribution_kind,
        '{"mu":100.0,"sigma":15.0}'::JSONB,
        100,
        'analytics_team'
    ),
    (
        'Exponential service waiting time',
        'EXPONENTIAL'::distribution_kind,
        '{"lambda":0.5}'::JSONB,
        100,
        'service_team'
    )
) AS data(
    experiment_name,
    distribution_type,
    parameters,
    sample_size,
    requested_by
)
JOIN distribution_catalog catalog
    ON catalog.distribution_type = data.distribution_type;

-- ============================================================
-- 16. PROBABILITY RETRIEVAL QUERIES
-- ============================================================

-- Bernoulli probability of success.
SELECT probability_mass(
    'BERNOULLI',
    '{"p":0.7}'::JSONB,
    1
) AS probability_of_success;

-- Binomial probability of exactly three successes.
SELECT probability_mass(
    'BINOMIAL',
    '{"n":10,"p":0.3}'::JSONB,
    3
) AS binomial_probability;

-- Binomial cumulative probability.
SELECT probability_cdf(
    'BINOMIAL',
    '{"n":10,"p":0.3}'::JSONB,
    3
) AS probability_of_at_most_three_successes;

-- Geometric probability of first success on trial four.
SELECT probability_mass(
    'GEOMETRIC',
    '{"p":0.25}'::JSONB,
    4
) AS geometric_probability;

-- Poisson probability of exactly two events.
SELECT probability_mass(
    'POISSON',
    '{"lambda":4.0}'::JSONB,
    2
) AS poisson_probability;

-- Uniform density.
SELECT probability_density(
    'UNIFORM',
    '{"a":0,"b":10}'::JSONB,
    5.0
) AS uniform_density;

-- Normal density and cumulative probability.
SELECT
    probability_density(
        'NORMAL',
        '{"mu":100,"sigma":15}'::JSONB,
        115.0
    ) AS normal_density,
    probability_cdf(
        'NORMAL',
        '{"mu":100,"sigma":15}'::JSONB,
        115.0
    ) AS normal_cumulative_probability;

-- Exponential waiting-time density and cumulative probability.
SELECT
    probability_density(
        'EXPONENTIAL',
        '{"lambda":0.5}'::JSONB,
        2.0
    ) AS exponential_density,
    probability_cdf(
        'EXPONENTIAL',
        '{"lambda":0.5}'::JSONB,
        2.0
    ) AS exponential_cumulative_probability;

-- ============================================================
-- 17. THEORETICAL DISTRIBUTION REPORT
-- ============================================================

SELECT
    c.distribution_type,
    s.theoretical_mean,
    s.theoretical_variance,
    s.standard_deviation
FROM distribution_catalog c
CROSS JOIN LATERAL distribution_statistics(
    c.distribution_type,
    CASE c.distribution_type
        WHEN 'BERNOULLI' THEN '{"p":0.4}'::JSONB
        WHEN 'BINOMIAL' THEN '{"n":20,"p":0.4}'::JSONB
        WHEN 'GEOMETRIC' THEN '{"p":0.2}'::JSONB
        WHEN 'POISSON' THEN '{"lambda":5}'::JSONB
        WHEN 'UNIFORM' THEN '{"a":10,"b":20}'::JSONB
        WHEN 'NORMAL' THEN '{"mu":50,"sigma":10}'::JSONB
        WHEN 'EXPONENTIAL' THEN '{"lambda":0.5}'::JSONB
    END
) s
ORDER BY c.distribution_id;

-- ============================================================
-- 18. INVALID PARAMETER TEST
-- ============================================================

-- This block demonstrates a rejected experiment without
-- interrupting the remaining SQL script.

DO $$
BEGIN
    BEGIN
        PERFORM validate_distribution_parameters(
            'GEOMETRIC',
            '{"p":0}'::JSONB
        );

        RAISE EXCEPTION
            'Invalid geometric parameters were not rejected.';

    EXCEPTION
        WHEN raise_exception THEN
            RAISE NOTICE
                'Expected validation failure: %',
                SQLERRM;
    END;
END;
$$;

-- ============================================================
-- 19. EXPERIMENT AGGREGATION AND RETRIEVAL
-- ============================================================

SELECT
    experiment_name,
    distribution_type,
    parameters,
    sample_size,
    status,
    theoretical_mean,
    theoretical_variance,
    recorded_samples
FROM experiment_statistics
ORDER BY experiment_id;

-- ============================================================
-- 20. DISTRIBUTION ELIGIBILITY REPORT
-- ============================================================

-- Identify which distribution can represent a given data type.
SELECT
    distribution_type,
    is_discrete,
    parameter_names,
    CASE
        WHEN is_discrete THEN
            'Suitable for integer-valued event counts'
        ELSE
            'Suitable for continuous measurements'
    END AS modeling_eligibility
FROM distribution_catalog
ORDER BY distribution_type;

COMMIT;

-- ============================================================
-- 21. ADDITIONAL OPERATIONAL QUERIES
-- ============================================================

-- Find the most recently created experiments.
SELECT
    experiment_id,
    experiment_name,
    status,
    created_at
FROM probability_lab.experiments
ORDER BY created_at DESC
LIMIT 10;

-- Count experiments by distribution.
SELECT
    c.distribution_type,
    COUNT(e.experiment_id) AS experiment_count
FROM probability_lab.distribution_catalog c
LEFT JOIN probability_lab.experiments e
    ON e.distribution_id = c.distribution_id
GROUP BY c.distribution_type
ORDER BY c.distribution_type;

-- Identify experiments whose sample collection is incomplete.
SELECT
    e.experiment_id,
    e.experiment_name,
    e.sample_size,
    COUNT(o.observation_id) AS collected_samples,
    e.sample_size - COUNT(o.observation_id) AS missing_samples
FROM probability_lab.experiments e
LEFT JOIN probability_lab.simulation_observations o
    ON o.experiment_id = e.experiment_id
GROUP BY e.experiment_id
HAVING COUNT(o.observation_id) < e.sample_size;

-- Example of an explicit transaction for experiment processing:
--
-- BEGIN;
-- SELECT probability_lab.start_experiment(1);
-- INSERT INTO probability_lab.simulation_observations
--     (experiment_id, observation_number, observed_value)
-- VALUES (1, 1, 1), (1, 2, 0);
-- COMMIT;
--
-- complete_experiment() must only be called after the configured
-- sample size has been recorded. It locks the experiment row
-- and rejects incomplete processing.
