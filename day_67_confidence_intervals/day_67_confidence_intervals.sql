-- ============================================================
-- CONFIDENCE INTERVAL ANALYSIS
-- PostgreSQL 14+
--
-- Implements:
-- Point estimates, mean intervals, Wilson proportion intervals,
-- bootstrap percentile intervals, margin of error, sample sizing,
-- reproducible analysis runs, and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS statistics_lab;

SET search_path TO statistics_lab, public;

-- ------------------------------------------------------------
-- 1. Domain types
-- ------------------------------------------------------------

CREATE TYPE interval_method AS ENUM (
    'NORMAL',
    'STUDENT_T',
    'WILSON',
    'BOOTSTRAP'
);

CREATE TYPE analysis_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

-- ------------------------------------------------------------
-- 2. Data model
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS study (
    study_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    study_code VARCHAR(40) NOT NULL UNIQUE,
    study_name VARCHAR(200) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(study_code)) > 0),
    CHECK (length(trim(study_name)) > 0)
);

CREATE TABLE IF NOT EXISTS observation_group (
    group_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    study_id BIGINT NOT NULL REFERENCES study(study_id)
        ON DELETE CASCADE,
    group_code VARCHAR(50) NOT NULL,
    group_name VARCHAR(150) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_unit VARCHAR(40) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (study_id, group_code)
);

CREATE TABLE IF NOT EXISTS observation (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_id BIGINT NOT NULL REFERENCES observation_group(group_id)
        ON DELETE CASCADE,
    observation_value DOUBLE PRECISION NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_reference VARCHAR(100),
    CHECK (
        observation_value > '-Infinity'::DOUBLE PRECISION
        AND observation_value < 'Infinity'::DOUBLE PRECISION
    )
);

CREATE TABLE IF NOT EXISTS proportion_observation (
    proportion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_id BIGINT NOT NULL REFERENCES observation_group(group_id)
        ON DELETE CASCADE,
    successes BIGINT NOT NULL,
    trials BIGINT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (trials > 0),
    CHECK (successes >= 0),
    CHECK (successes <= trials)
);

CREATE TABLE IF NOT EXISTS analysis_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_id BIGINT NOT NULL REFERENCES observation_group(group_id),
    method interval_method NOT NULL,
    confidence_level DOUBLE PRECISION NOT NULL DEFAULT 0.95,
    bootstrap_repetitions INTEGER NOT NULL DEFAULT 10000,
    random_seed BIGINT NOT NULL DEFAULT 42,
    status analysis_status NOT NULL DEFAULT 'CREATED',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    CHECK (
        confidence_level > 0
        AND confidence_level < 1
    ),
    CHECK (bootstrap_repetitions >= 100),
    CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS interval_result (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL UNIQUE REFERENCES analysis_run(run_id)
        ON DELETE CASCADE,
    point_estimate DOUBLE PRECISION NOT NULL,
    lower_bound DOUBLE PRECISION NOT NULL,
    upper_bound DOUBLE PRECISION NOT NULL,
    standard_error DOUBLE PRECISION NOT NULL,
    margin_of_error DOUBLE PRECISION NOT NULL,
    sample_size BIGINT NOT NULL,
    degrees_of_freedom BIGINT,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (lower_bound <= upper_bound),
    CHECK (standard_error >= 0),
    CHECK (margin_of_error >= 0),
    CHECK (sample_size > 0),
    CHECK (
        point_estimate > '-Infinity'::DOUBLE PRECISION
        AND point_estimate < 'Infinity'::DOUBLE PRECISION
        AND lower_bound > '-Infinity'::DOUBLE PRECISION
        AND lower_bound < 'Infinity'::DOUBLE PRECISION
        AND upper_bound > '-Infinity'::DOUBLE PRECISION
        AND upper_bound < 'Infinity'::DOUBLE PRECISION
    )
);

-- ------------------------------------------------------------
-- 3. Performance indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_observation_group_time
    ON observation(group_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_observation_value
    ON observation(group_id, observation_value);

CREATE INDEX IF NOT EXISTS idx_proportion_group_time
    ON proportion_observation(group_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_analysis_status
    ON analysis_run(status, started_at);

CREATE INDEX IF NOT EXISTS idx_result_run
    ON interval_result(run_id);

-- ------------------------------------------------------------
-- 4. Sample studies and observations
-- ------------------------------------------------------------

INSERT INTO study (
    study_code,
    study_name,
    owner_name
)
VALUES
    ('WEB-RESPONSE-001', 'Website Response Time Study', 'Research Team'),
    ('CONVERSION-001', 'Marketing Conversion Study', 'Analytics Team')
ON CONFLICT (study_code) DO NOTHING;

INSERT INTO observation_group (
    study_id,
    group_code,
    group_name,
    metric_name,
    metric_unit
)
SELECT
    study_id,
    'RESPONSE-A',
    'API Response Times',
    'Response time',
    'milliseconds'
FROM study
WHERE study_code = 'WEB-RESPONSE-001'
ON CONFLICT (study_id, group_code) DO NOTHING;

INSERT INTO observation_group (
    study_id,
    group_code,
    group_name,
    metric_name,
    metric_unit
)
SELECT
    study_id,
    'CAMPAIGN-A',
    'Campaign Conversion',
    'Conversion rate',
    'proportion'
FROM study
WHERE study_code = 'CONVERSION-001'
ON CONFLICT (study_id, group_code) DO NOTHING;

INSERT INTO observation (
    group_id,
    observation_value,
    source_reference
)
SELECT
    group_id,
    value,
    'API-TEST-2026'
FROM observation_group
CROSS JOIN (
    VALUES
        (12.4::DOUBLE PRECISION),
        (13.1),
        (11.8),
        (14.2),
        (12.9),
        (13.7),
        (12.1),
        (14.0),
        (13.3),
        (12.7),
        (11.9),
        (13.5),
        (14.1),
        (12.6),
        (13.0)
) AS sample(value)
WHERE group_code = 'RESPONSE-A'
AND NOT EXISTS (
    SELECT 1
    FROM observation existing
    WHERE existing.group_id = observation_group.group_id
);

INSERT INTO proportion_observation (
    group_id,
    successes,
    trials
)
SELECT group_id, 735, 1000
FROM observation_group
WHERE group_code = 'CAMPAIGN-A'
AND NOT EXISTS (
    SELECT 1
    FROM proportion_observation p
    WHERE p.group_id = observation_group.group_id
);

-- ------------------------------------------------------------
-- 5. Statistical utility functions
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_confidence(
    p_confidence DOUBLE PRECISION
)
RETURNS VOID
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_confidence IS NULL
       OR p_confidence <= 0
       OR p_confidence >= 1
       OR p_confidence = 'NaN'::DOUBLE PRECISION
       OR p_confidence = 'Infinity'::DOUBLE PRECISION
       OR p_confidence = '-Infinity'::DOUBLE PRECISION THEN
        RAISE EXCEPTION
            'Confidence must be strictly between zero and one.';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION normal_critical_value(
    p_confidence DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_alpha DOUBLE PRECISION;
    v_p DOUBLE PRECISION;
BEGIN
    PERFORM validate_confidence(p_confidence);

    v_alpha := 1 - p_confidence;
    v_p := 1 - v_alpha / 2;

    -- Inverse standard normal distribution.
    RETURN statistics_lab.inverse_normal_cdf(v_p);
END;
$$;

-- PostgreSQL does not provide inverse_normal_cdf by default.
-- This implementation uses the Acklam approximation.
CREATE OR REPLACE FUNCTION inverse_normal_cdf(
    p DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    a DOUBLE PRECISION[] := ARRAY[
        -39.69683028665376,
        220.9460984245205,
        -275.9285104469687,
        138.3577518672690,
        -30.66479806614716,
        2.506628277459239
    ];

    b DOUBLE PRECISION[] := ARRAY[
        -54.47609879822406,
        161.5858368580409,
        -155.6989798598866,
        66.80131188771972,
        -13.28068155288572
    ];

    c DOUBLE PRECISION[] := ARRAY[
        -0.007784894002430293,
        -0.3223964580411365,
        -2.400758277161838,
        -2.549732539343734,
        4.374664141464968,
        2.938163982698783
    ];

    d DOUBLE PRECISION[] := ARRAY[
        0.007784695709041462,
        0.3224671290700398,
        2.445134137142996,
        3.754408661907416
    ];

    v_low CONSTANT DOUBLE PRECISION := 0.02425;
    v_high CONSTANT DOUBLE PRECISION := 0.97575;
    q DOUBLE PRECISION;
    r DOUBLE PRECISION;
BEGIN
    IF p <= 0 OR p >= 1 OR p IS NULL THEN
        RAISE EXCEPTION 'Probability must be between zero and one.';
    END IF;

    IF p < v_low THEN
        q := sqrt(-2 * ln(p));

        RETURN -(
            (((((c[1] * q + c[2]) * q + c[3]) * q + c[4]) * q
                + c[5]) * q + c[6]) /
            ((((d[1] * q + d[2]) * q + d[3]) * q + d[4]) * q + 1)
        );
    END IF;

    IF p > v_high THEN
        q := sqrt(-2 * ln(1 - p));

        RETURN (
            (((((c[1] * q + c[2]) * q + c[3]) * q + c[4]) * q
                + c[5]) * q + c[6]) /
            ((((d[1] * q + d[2]) * q + d[3]) * q + d[4]) * q + 1)
        );
    END IF;

    q := p - 0.5;
    r := q * q;

    RETURN (
        (((((a[1] * r + a[2]) * r + a[3]) * r + a[4]) * r
            + a[5]) * r + a[6]) * q /
        (((((b[1] * r + b[2]) * r + b[3]) * r
            + b[4]) * r + b[5]) * r + 1)
    );
END;
$$;

-- ------------------------------------------------------------
-- 6. Point estimation
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION point_mean(
    p_group_id BIGINT
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_mean DOUBLE PRECISION;
BEGIN
    SELECT AVG(observation_value)
    INTO v_mean
    FROM observation
    WHERE group_id = p_group_id;

    IF v_mean IS NULL THEN
        RAISE EXCEPTION 'No observations found for group %', p_group_id;
    END IF;

    RETURN v_mean;
END;
$$;

CREATE OR REPLACE FUNCTION point_sample_variance(
    p_group_id BIGINT
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_variance DOUBLE PRECISION;
BEGIN
    SELECT VAR_SAMP(observation_value)
    INTO v_variance
    FROM observation
    WHERE group_id = p_group_id;

    IF v_variance IS NULL THEN
        RAISE EXCEPTION
            'At least two observations are required.';
    END IF;

    RETURN v_variance;
END;
$$;

-- ------------------------------------------------------------
-- 7. Student t critical values
-- Exact 95% values for df 1..30, normal approximation thereafter.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION student_t_critical_95(
    p_df BIGINT
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    values_table DOUBLE PRECISION[] := ARRAY[
        12.706, 4.303, 3.182, 2.776, 2.571,
        2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131,
        2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060,
        2.056, 2.052, 2.048, 2.045, 2.042
    ];
BEGIN
    IF p_df < 1 THEN
        RAISE EXCEPTION 'Degrees of freedom must be positive.';
    END IF;

    IF p_df <= 30 THEN
        RETURN values_table[p_df::INTEGER];
    END IF;

    RETURN 1.959963984540054;
END;
$$;

-- ------------------------------------------------------------
-- 8. Mean confidence interval
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_mean_interval(
    p_group_id BIGINT,
    p_confidence DOUBLE PRECISION DEFAULT 0.95,
    p_method interval_method DEFAULT 'STUDENT_T'
)
RETURNS TABLE (
    point_estimate DOUBLE PRECISION,
    lower_bound DOUBLE PRECISION,
    upper_bound DOUBLE PRECISION,
    standard_error DOUBLE PRECISION,
    margin_of_error DOUBLE PRECISION,
    sample_size BIGINT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_n BIGINT;
    v_mean DOUBLE PRECISION;
    v_sd DOUBLE PRECISION;
    v_se DOUBLE PRECISION;
    v_critical DOUBLE PRECISION;
    v_margin DOUBLE PRECISION;
BEGIN
    PERFORM validate_confidence(p_confidence);

    IF p_method NOT IN ('NORMAL', 'STUDENT_T') THEN
        RAISE EXCEPTION 'Unsupported mean interval method.';
    END IF;

    SELECT
        COUNT(*),
        AVG(observation_value),
        STDDEV_SAMP(observation_value)
    INTO v_n, v_mean, v_sd
    FROM observation
    WHERE group_id = p_group_id;

    IF v_n < 2 THEN
        RAISE EXCEPTION 'At least two observations are required.';
    END IF;

    v_se := v_sd / sqrt(v_n::DOUBLE PRECISION);

    IF p_method = 'STUDENT_T' THEN
        IF p_confidence <> 0.95 THEN
            RAISE EXCEPTION
                'Student t table supports 95%% confidence only.';
        END IF;

        v_critical := student_t_critical_95(v_n - 1);
    ELSE
        v_critical := normal_critical_value(p_confidence);
    END IF;

    v_margin := v_critical * v_se;

    RETURN QUERY SELECT
        v_mean,
        v_mean - v_margin,
        v_mean + v_margin,
        v_se,
        v_margin,
        v_n;
END;
$$;

-- ------------------------------------------------------------
-- 9. Wilson proportion interval
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_wilson_interval(
    p_successes BIGINT,
    p_trials BIGINT,
    p_confidence DOUBLE PRECISION DEFAULT 0.95
)
RETURNS TABLE (
    point_estimate DOUBLE PRECISION,
    lower_bound DOUBLE PRECISION,
    upper_bound DOUBLE PRECISION,
    margin_of_error DOUBLE PRECISION
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_p DOUBLE PRECISION;
    v_z DOUBLE PRECISION;
    v_z2 DOUBLE PRECISION;
    v_denominator DOUBLE PRECISION;
    v_center DOUBLE PRECISION;
    v_adjustment DOUBLE PRECISION;
BEGIN
    PERFORM validate_confidence(p_confidence);

    IF p_trials <= 0
       OR p_successes < 0
       OR p_successes > p_trials THEN
        RAISE EXCEPTION 'Invalid success and trial counts.';
    END IF;

    v_p := p_successes::DOUBLE PRECISION / p_trials;
    v_z := normal_critical_value(p_confidence);
    v_z2 := v_z * v_z;

    v_denominator := 1 + v_z2 / p_trials;

    v_center := (
        v_p + v_z2 / (2 * p_trials)
    ) / v_denominator;

    v_adjustment := v_z * sqrt(
        v_p * (1 - v_p) / p_trials
        + v_z2 / (4 * p_trials * p_trials)
    ) / v_denominator;

    RETURN QUERY SELECT
        v_p,
        GREATEST(0.0, v_center - v_adjustment),
        LEAST(1.0, v_center + v_adjustment),
        v_adjustment;
END;
$$;

-- ------------------------------------------------------------
-- 10. Margin of error and sample size
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_margin_of_error(
    p_sd DOUBLE PRECISION,
    p_sample_size BIGINT,
    p_confidence DOUBLE PRECISION DEFAULT 0.95
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    PERFORM validate_confidence(p_confidence);

    IF p_sd IS NULL
       OR p_sd < 0
       OR p_sample_size <= 0 THEN
        RAISE EXCEPTION 'Invalid margin-of-error inputs.';
    END IF;

    RETURN normal_critical_value(p_confidence)
        * p_sd / sqrt(p_sample_size::DOUBLE PRECISION);
END;
$$;

CREATE OR REPLACE FUNCTION calculate_required_sample_size(
    p_sd DOUBLE PRECISION,
    p_desired_margin DOUBLE PRECISION,
    p_confidence DOUBLE PRECISION DEFAULT 0.95
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_required NUMERIC;
BEGIN
    PERFORM validate_confidence(p_confidence);

    IF p_sd IS NULL
       OR p_sd < 0
       OR p_desired_margin IS NULL
       OR p_desired_margin <= 0 THEN
        RAISE EXCEPTION 'Invalid sample-size inputs.';
    END IF;

    v_required := CEIL(
        POWER(
            normal_critical_value(p_confidence)::NUMERIC
            * p_sd::NUMERIC
            / p_desired_margin::NUMERIC,
            2
        )
    );

    IF v_required > 9223372036854775807 THEN
        RAISE EXCEPTION 'Required sample size exceeds BIGINT capacity.';
    END IF;

    RETURN v_required::BIGINT;
END;
$$;

-- ------------------------------------------------------------
-- 11. Bootstrap percentile interval
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_bootstrap_interval(
    p_group_id BIGINT,
    p_confidence DOUBLE PRECISION DEFAULT 0.95,
    p_repetitions INTEGER DEFAULT 10000,
    p_seed BIGINT DEFAULT 42
)
RETURNS TABLE (
    point_estimate DOUBLE PRECISION,
    lower_bound DOUBLE PRECISION,
    upper_bound DOUBLE PRECISION,
    margin_of_error DOUBLE PRECISION,
    sample_size BIGINT
)
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
    v_values DOUBLE PRECISION[];
    v_n INTEGER;
    v_estimates DOUBLE PRECISION[];
    v_sample DOUBLE PRECISION[];
    v_estimate DOUBLE PRECISION;
    v_lower DOUBLE PRECISION;
    v_upper DOUBLE PRECISION;
    v_alpha DOUBLE PRECISION;
    v_index INTEGER;
    v_i INTEGER;
    v_j INTEGER;
    v_rng_state DOUBLE PRECISION;
    v_rng_seed DOUBLE PRECISION;
BEGIN
    PERFORM validate_confidence(p_confidence);

    IF p_repetitions < 100 THEN
        RAISE EXCEPTION 'At least 100 repetitions are required.';
    END IF;

    SELECT ARRAY_AGG(observation_value ORDER BY observation_id)
    INTO v_values
    FROM observation
    WHERE group_id = p_group_id;

    v_n := COALESCE(array_length(v_values, 1), 0);

    IF v_n < 2 THEN
        RAISE EXCEPTION 'At least two observations are required.';
    END IF;

    v_estimate := (
        SELECT AVG(value)
        FROM unnest(v_values) AS source(value)
    );

    v_estimates := ARRAY[]::DOUBLE PRECISION[];
    v_rng_state := abs(mod(p_seed::NUMERIC, 2147483647))::DOUBLE PRECISION;

    -- A private deterministic generator avoids changing global random state.
    IF v_rng_state = 0 THEN
        v_rng_state := 1;
    END IF;

    FOR v_i IN 1..p_repetitions LOOP
        v_sample := ARRAY[]::DOUBLE PRECISION[];

        FOR v_j IN 1..v_n LOOP
            v_rng_state := mod(
                16807 * v_rng_state,
                2147483647
            );

            v_index := floor(
                v_rng_state / 2147483647.0 * v_n
            )::INTEGER + 1;

            v_sample := array_append(
                v_sample,
                v_values[v_index]
            );
        END LOOP;

        v_estimates := array_append(
            v_estimates,
            (
                SELECT AVG(value)
                FROM unnest(v_sample) AS source(value)
            )
        );
    END LOOP;

    SELECT ARRAY_AGG(value ORDER BY value)
    INTO v_estimates
    FROM unnest(v_estimates) AS source(value);

    v_alpha := (1 - p_confidence) / 2;

    -- Linear interpolation between adjacent empirical percentiles.
    v_index := floor(v_alpha * (p_repetitions - 1))::INTEGER + 1;

    v_lower := v_estimates[v_index]
        + (
            v_estimates[LEAST(v_index + 1, p_repetitions)]
            - v_estimates[v_index]
        ) * (
            v_alpha * (p_repetitions - 1)
            - floor(v_alpha * (p_repetitions - 1))
        );

    v_index := floor(
        (1 - v_alpha) * (p_repetitions - 1)
    )::INTEGER + 1;

    v_upper := v_estimates[v_index]
        + (
            v_estimates[LEAST(v_index + 1, p_repetitions)]
            - v_estimates[v_index]
        ) * (
            (1 - v_alpha) * (p_repetitions - 1)
            - floor((1 - v_alpha) * (p_repetitions - 1))
        );

    RETURN QUERY SELECT
        v_estimate,
        v_lower,
        v_upper,
        (v_upper - v_lower) / 2,
        v_n::BIGINT;
END;
$$;

-- ------------------------------------------------------------
-- 12. Workflow state enforcement
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_analysis_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status IN ('COMPLETED', 'FAILED')
           AND NEW.status <> OLD.status THEN
            RAISE EXCEPTION
                'Terminal analysis states cannot be reopened.';
        END IF;

        IF NEW.status = 'RUNNING'
           AND OLD.status <> 'RUNNING' THEN
            NEW.started_at := CURRENT_TIMESTAMP;
        END IF;

        IF NEW.status IN ('COMPLETED', 'FAILED')
           AND NEW.completed_at IS NULL THEN
            NEW.completed_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_analysis_state ON analysis_run;

CREATE TRIGGER trg_analysis_state
BEFORE UPDATE ON analysis_run
FOR EACH ROW
EXECUTE FUNCTION enforce_analysis_state();

-- ------------------------------------------------------------
-- 13. Analysis execution procedure
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE execute_analysis(
    p_run_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run analysis_run%ROWTYPE;
    v_result RECORD;
BEGIN
    SELECT *
    INTO v_run
    FROM analysis_run
    WHERE run_id = p_run_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Analysis run % does not exist.', p_run_id;
    END IF;

    IF v_run.status <> 'CREATED' THEN
        RAISE EXCEPTION
            'Only CREATED analyses can be executed.';
    END IF;

    UPDATE analysis_run
    SET status = 'RUNNING'
    WHERE run_id = p_run_id;

    IF v_run.method = 'NORMAL'
       OR v_run.method = 'STUDENT_T' THEN

        SELECT *
        INTO v_result
        FROM calculate_mean_interval(
            v_run.group_id,
            v_run.confidence_level,
            v_run.method
        );

        INSERT INTO interval_result (
            run_id,
            point_estimate,
            lower_bound,
            upper_bound,
            standard_error,
            margin_of_error,
            sample_size,
            degrees_of_freedom
        )
        VALUES (
            p_run_id,
            v_result.point_estimate,
            v_result.lower_bound,
            v_result.upper_bound,
            v_result.standard_error,
            v_result.margin_of_error,
            v_result.sample_size,
            CASE
                WHEN v_run.method = 'STUDENT_T'
                THEN v_result.sample_size - 1
                ELSE NULL
            END
        );

    ELSIF v_run.method = 'BOOTSTRAP' THEN

        SELECT *
        INTO v_result
        FROM calculate_bootstrap_interval(
            v_run.group_id,
            v_run.confidence_level,
            v_run.bootstrap_repetitions,
            v_run.random_seed
        );

        INSERT INTO interval_result (
            run_id,
            point_estimate,
            lower_bound,
            upper_bound,
            standard_error,
            margin_of_error,
            sample_size
        )
        VALUES (
            p_run_id,
            v_result.point_estimate,
            v_result.lower_bound,
            v_result.upper_bound,
            NULL,
            v_result.margin_of_error,
            v_result.sample_size
        );

    ELSIF v_run.method = 'WILSON' THEN

        SELECT
            SUM(successes),
            SUM(trials)
        INTO v_result.successes, v_result.trials
        FROM proportion_observation
        WHERE group_id = v_run.group_id;

        IF v_result.trials IS NULL THEN
            RAISE EXCEPTION
                'No proportion observations for group %',
                v_run.group_id;
        END IF;

        SELECT *
        INTO v_result
        FROM calculate_wilson_interval(
            v_result.successes,
            v_result.trials,
            v_run.confidence_level
        );

        INSERT INTO interval_result (
            run_id,
            point_estimate,
            lower_bound,
            upper_bound,
            standard_error,
            margin_of_error,
            sample_size
        )
        VALUES (
            p_run_id,
            v_result.point_estimate,
            v_result.lower_bound,
            v_result.upper_bound,
            0,
            v_result.margin_of_error,
            v_result.sample_size
        );
    END IF;

    UPDATE analysis_run
    SET status = 'COMPLETED'
    WHERE run_id = p_run_id;

EXCEPTION
    WHEN OTHERS THEN
        UPDATE analysis_run
        SET status = 'FAILED',
            error_message = SQLERRM
        WHERE run_id = p_run_id
          AND status IN ('CREATED', 'RUNNING');

        RAISE;
END;
$$;

-- ------------------------------------------------------------
-- 14. Create reproducible analysis runs
-- ------------------------------------------------------------

INSERT INTO analysis_run (
    group_id,
    method,
    confidence_level,
    bootstrap_repetitions,
    random_seed
)
SELECT group_id, 'STUDENT_T', 0.95, 1000, 42
FROM observation_group
WHERE group_code = 'RESPONSE-A'
AND NOT EXISTS (
    SELECT 1
    FROM analysis_run r
    WHERE r.group_id = observation_group.group_id
      AND r.method = 'STUDENT_T'
);

INSERT INTO analysis_run (
    group_id,
    method,
    confidence_level,
    bootstrap_repetitions,
    random_seed
)
SELECT group_id, 'NORMAL', 0.95, 1000, 42
FROM observation_group
WHERE group_code = 'RESPONSE-A'
AND NOT EXISTS (
    SELECT 1
    FROM analysis_run r
    WHERE r.group_id = observation_group.group_id
      AND r.method = 'NORMAL'
);

INSERT INTO analysis_run (
    group_id,
    method,
    confidence_level,
    bootstrap_repetitions,
    random_seed
)
SELECT group_id, 'BOOTSTRAP', 0.95, 1000, 42
FROM observation_group
WHERE group_code = 'RESPONSE-A'
AND NOT EXISTS (
    SELECT 1
    FROM analysis_run r
    WHERE r.group_id = observation_group.group_id
      AND r.method = 'BOOTSTRAP'
);

INSERT INTO analysis_run (
    group_id,
    method,
    confidence_level,
    bootstrap_repetitions,
    random_seed
)
SELECT group_id, 'WILSON', 0.95, 1000, 42
FROM observation_group
WHERE group_code = 'CAMPAIGN-A'
AND NOT EXISTS (
    SELECT 1
    FROM analysis_run r
    WHERE r.group_id = observation_group.group_id
      AND r.method = 'WILSON'
);

-- ------------------------------------------------------------
-- 15. Execute analysis workflow
-- ------------------------------------------------------------

DO $$
DECLARE
    v_run RECORD;
BEGIN
    FOR v_run IN
        SELECT run_id
        FROM analysis_run
        WHERE status = 'CREATED'
        ORDER BY run_id
    LOOP
        CALL execute_analysis(v_run.run_id);
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- 16. Reporting views
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW confidence_interval_report AS
SELECT
    s.study_code,
    s.study_name,
    g.group_code,
    g.group_name,
    g.metric_name,
    g.metric_unit,
    r.run_id,
    r.method,
    r.confidence_level,
    r.status,
    result.point_estimate,
    result.lower_bound,
    result.upper_bound,
    result.margin_of_error,
    result.upper_bound - result.lower_bound AS interval_width,
    result.sample_size,
    result.degrees_of_freedom,
    result.computed_at
FROM analysis_run r
JOIN observation_group g ON g.group_id = r.group_id
JOIN study s ON s.study_id = g.study_id
LEFT JOIN interval_result result ON result.run_id = r.run_id;

-- ------------------------------------------------------------
-- 17. Retrieval
-- ------------------------------------------------------------

SELECT *
FROM confidence_interval_report
ORDER BY study_code, method;

-- ------------------------------------------------------------
-- 18. Point estimate and descriptive statistics
-- ------------------------------------------------------------

SELECT
    g.group_code,
    COUNT(o.observation_id) AS sample_size,
    AVG(o.observation_value) AS point_estimate,
    STDDEV_SAMP(o.observation_value) AS sample_standard_deviation,
    VAR_SAMP(o.observation_value) AS sample_variance,
    MIN(o.observation_value) AS minimum_value,
    MAX(o.observation_value) AS maximum_value
FROM observation_group g
JOIN observation o ON o.group_id = g.group_id
GROUP BY g.group_code;

-- ------------------------------------------------------------
-- 19. Validation query
-- ------------------------------------------------------------

SELECT
    run_id,
    status,
    CASE
        WHEN status <> 'COMPLETED' THEN 'NOT COMPLETED'
        WHEN lower_bound > point_estimate
          OR upper_bound < point_estimate THEN 'INVALID INTERVAL'
        WHEN lower_bound > upper_bound THEN 'INVALID BOUNDS'
        ELSE 'VALID'
    END AS validation_status
FROM confidence_interval_report
WHERE run_id IS NOT NULL;

-- ------------------------------------------------------------
-- 20. Aggregation and interval comparison
-- ------------------------------------------------------------

SELECT
    method,
    COUNT(*) AS analyses,
    AVG(upper_bound - lower_bound) AS average_interval_width,
    AVG(margin_of_error) AS average_margin_of_error,
    AVG(sample_size) AS average_sample_size
FROM confidence_interval_report
WHERE status = 'COMPLETED'
GROUP BY method
ORDER BY method;

-- ------------------------------------------------------------
-- 21. Eligibility determination
-- ------------------------------------------------------------

-- A report is eligible when it is completed, has a valid interval,
-- and meets the configured precision threshold.
SELECT
    run_id,
    method,
    sample_size,
    margin_of_error,
    CASE
        WHEN status <> 'COMPLETED' THEN 'INELIGIBLE'
        WHEN lower_bound > point_estimate THEN 'INELIGIBLE'
        WHEN upper_bound < point_estimate THEN 'INELIGIBLE'
        WHEN margin_of_error > 2.0 THEN 'PRECISION REVIEW REQUIRED'
        ELSE 'ELIGIBLE'
    END AS publication_eligibility
FROM confidence_interval_report
WHERE run_id IS NOT NULL;

-- ------------------------------------------------------------
-- 22. Sample-size planning
-- ------------------------------------------------------------

SELECT calculate_required_sample_size(
    10.0,
    2.0,
    0.95
) AS required_observations;

SELECT calculate_margin_of_error(
    10.0,
    100,
    0.95
) AS expected_margin_of_error;

-- ------------------------------------------------------------
-- 23. Proportion interval edge cases
-- ------------------------------------------------------------

SELECT
    'Zero successes' AS scenario,
    *
FROM calculate_wilson_interval(0, 100, 0.95);

SELECT
    'All successes' AS scenario,
    *
FROM calculate_wilson_interval(100, 100, 0.95);

SELECT
    'Small sample' AS scenario,
    *
FROM calculate_wilson_interval(2, 5, 0.95);

-- ------------------------------------------------------------
-- 24. Failure-case validation
-- These blocks intentionally catch invalid input.
-- ------------------------------------------------------------

DO $$
BEGIN
    BEGIN
        PERFORM calculate_wilson_interval(110, 100, 0.95);
        RAISE EXCEPTION 'Invalid count was accepted.';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'Invalid count was accepted.' THEN
                RAISE;
            END IF;
            RAISE NOTICE 'Invalid proportion correctly rejected.';
    END;

    BEGIN
        PERFORM calculate_required_sample_size(10, 0, 0.95);
        RAISE EXCEPTION 'Invalid precision was accepted.';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'Invalid precision was accepted.' THEN
                RAISE;
            END IF;
            RAISE NOTICE 'Invalid precision correctly rejected.';
    END;
END;
$$;

COMMIT;
