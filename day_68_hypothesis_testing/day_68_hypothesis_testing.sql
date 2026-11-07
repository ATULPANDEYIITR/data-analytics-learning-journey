-- ============================================================
-- HYPOTHESIS TESTING AND EXPERIMENT GOVERNANCE
-- PostgreSQL 14+
--
-- Implements:
--   Hypotheses and alternatives
--   Experiment observations
--   Sample statistics
--   One-sample Z-tests
--   P-value evaluation
--   Significance policies
--   Type I and Type II error records
--   Statistical power estimates
--   Multiple-testing records
--   Audit history
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS statistics_lab;

SET search_path TO statistics_lab, public;

-- ------------------------------------------------------------
-- ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE hypothesis_alternative AS ENUM (
    'two-sided',
    'greater',
    'less'
);

CREATE TYPE experiment_status AS ENUM (
    'created',
    'collecting',
    'ready',
    'evaluated',
    'failed'
);

CREATE TYPE test_decision AS ENUM (
    'reject_h0',
    'fail_to_reject_h0'
);

CREATE TYPE error_type AS ENUM (
    'type_i',
    'type_ii'
);

-- ------------------------------------------------------------
-- EXPERIMENT REGISTRY
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_name VARCHAR(200) NOT NULL UNIQUE,

    description TEXT NOT NULL DEFAULT '',

    owner_name VARCHAR(120) NOT NULL,

    status experiment_status NOT NULL DEFAULT 'created',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_experiment_name
        CHECK (length(trim(experiment_name)) > 0),

    CONSTRAINT valid_owner
        CHECK (length(trim(owner_name)) > 0),

    CONSTRAINT valid_completion_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= created_at
        )
);

-- ------------------------------------------------------------
-- HYPOTHESIS DEFINITIONS
-- ------------------------------------------------------------

CREATE TABLE hypotheses (
    hypothesis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE RESTRICT,

    hypothesis_name VARCHAR(200) NOT NULL,

    null_value DOUBLE PRECISION NOT NULL,

    alternative hypothesis_alternative NOT NULL,

    significance_level DOUBLE PRECISION NOT NULL DEFAULT 0.05,

    hypothesis_description TEXT NOT NULL DEFAULT '',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_null_value
        CHECK (
            null_value > '-Infinity'::DOUBLE PRECISION
            AND null_value < 'Infinity'::DOUBLE PRECISION
        ),

    CONSTRAINT valid_significance_level
        CHECK (
            significance_level > 0
            AND significance_level < 1
        ),

    CONSTRAINT unique_hypothesis_name
        UNIQUE (experiment_id, hypothesis_name)
);

-- ------------------------------------------------------------
-- OBSERVATIONS
-- ------------------------------------------------------------

CREATE TABLE observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE RESTRICT,

    group_name VARCHAR(80) NOT NULL,

    observation_value DOUBLE PRECISION NOT NULL,

    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_observation_group
        CHECK (length(trim(group_name)) > 0),

    CONSTRAINT valid_observation_value
        CHECK (
            observation_value > '-Infinity'::DOUBLE PRECISION
            AND observation_value < 'Infinity'::DOUBLE PRECISION
        )
);

-- ------------------------------------------------------------
-- STATISTICAL EVALUATION RESULTS
-- ------------------------------------------------------------

CREATE TABLE test_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hypothesis_id BIGINT NOT NULL
        REFERENCES hypotheses(hypothesis_id)
        ON DELETE RESTRICT,

    test_name VARCHAR(150) NOT NULL,

    sample_size INTEGER NOT NULL,

    sample_mean DOUBLE PRECISION NOT NULL,

    sample_stddev DOUBLE PRECISION NOT NULL,

    standard_error DOUBLE PRECISION NOT NULL,

    test_statistic DOUBLE PRECISION NOT NULL,

    p_value DOUBLE PRECISION NOT NULL,

    confidence_lower DOUBLE PRECISION,

    confidence_upper DOUBLE PRECISION,

    decision test_decision NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT minimum_sample_size
        CHECK (sample_size >= 2),

    CONSTRAINT nonnegative_stddev
        CHECK (sample_stddev >= 0),

    CONSTRAINT nonnegative_standard_error
        CHECK (standard_error >= 0),

    CONSTRAINT valid_p_value
        CHECK (p_value BETWEEN 0 AND 1),

    CONSTRAINT valid_confidence_interval
        CHECK (
            confidence_lower IS NULL
            OR confidence_upper IS NULL
            OR confidence_lower <= confidence_upper
        ),

    CONSTRAINT valid_result_numbers
        CHECK (
            sample_mean > '-Infinity'::DOUBLE PRECISION
            AND sample_mean < 'Infinity'::DOUBLE PRECISION
            AND sample_stddev < 'Infinity'::DOUBLE PRECISION
            AND standard_error < 'Infinity'::DOUBLE PRECISION
            AND test_statistic > '-Infinity'::DOUBLE PRECISION
            AND test_statistic < 'Infinity'::DOUBLE PRECISION
        )
);

-- ------------------------------------------------------------
-- ERROR MODELING
-- ------------------------------------------------------------

CREATE TABLE error_analysis (
    error_analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hypothesis_id BIGINT NOT NULL
        REFERENCES hypotheses(hypothesis_id)
        ON DELETE RESTRICT,

    error_category error_type NOT NULL,

    probability DOUBLE PRECISION NOT NULL,

    description TEXT NOT NULL DEFAULT '',

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_error_probability
        CHECK (probability BETWEEN 0 AND 1),

    CONSTRAINT unique_error_category
        UNIQUE (hypothesis_id, error_category)
);

-- ------------------------------------------------------------
-- STATISTICAL POWER
-- ------------------------------------------------------------

CREATE TABLE power_analysis (
    power_analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hypothesis_id BIGINT NOT NULL
        REFERENCES hypotheses(hypothesis_id)
        ON DELETE RESTRICT,

    assumed_true_mean DOUBLE PRECISION NOT NULL,

    population_stddev DOUBLE PRECISION NOT NULL,

    planned_sample_size INTEGER NOT NULL,

    estimated_beta DOUBLE PRECISION NOT NULL,

    estimated_power DOUBLE PRECISION NOT NULL,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_power_sample_size
        CHECK (planned_sample_size >= 2),

    CONSTRAINT positive_population_stddev
        CHECK (population_stddev > 0),

    CONSTRAINT valid_beta
        CHECK (estimated_beta BETWEEN 0 AND 1),

    CONSTRAINT valid_power
        CHECK (estimated_power BETWEEN 0 AND 1),

    CONSTRAINT valid_power_mean
        CHECK (
            assumed_true_mean > '-Infinity'::DOUBLE PRECISION
            AND assumed_true_mean < 'Infinity'::DOUBLE PRECISION
        )
);

-- ------------------------------------------------------------
-- MULTIPLE TESTING
-- ------------------------------------------------------------

CREATE TABLE multiple_testing_batches (
    batch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    batch_name VARCHAR(150) NOT NULL UNIQUE,

    adjustment_method VARCHAR(50) NOT NULL,

    alpha DOUBLE PRECISION NOT NULL DEFAULT 0.05,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (alpha > 0 AND alpha < 1),

    CHECK (
        adjustment_method IN (
            'bonferroni',
            'benjamini_hochberg'
        )
    )
);

CREATE TABLE multiple_testing_items (
    batch_id BIGINT NOT NULL
        REFERENCES multiple_testing_batches(batch_id)
        ON DELETE CASCADE,

    hypothesis_id BIGINT NOT NULL
        REFERENCES hypotheses(hypothesis_id)
        ON DELETE RESTRICT,

    p_value DOUBLE PRECISION NOT NULL,

    adjusted_p_value DOUBLE PRECISION,

    significant BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (batch_id, hypothesis_id),

    CHECK (p_value BETWEEN 0 AND 1),

    CHECK (
        adjusted_p_value IS NULL
        OR adjusted_p_value BETWEEN 0 AND 1
    )
);

-- ------------------------------------------------------------
-- AUDIT TRAIL
-- ------------------------------------------------------------

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE RESTRICT,

    event_name VARCHAR(100) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- PERFORMANCE INDEXES
-- ------------------------------------------------------------

CREATE INDEX idx_observations_experiment_group
    ON observations(experiment_id, group_name);

CREATE INDEX idx_observations_timestamp
    ON observations(observed_at);

CREATE INDEX idx_hypotheses_experiment
    ON hypotheses(experiment_id);

CREATE INDEX idx_results_hypothesis
    ON test_results(hypothesis_id, evaluated_at DESC);

CREATE INDEX idx_results_significance
    ON test_results(decision, p_value);

CREATE INDEX idx_experiments_status
    ON experiments(status);

-- ------------------------------------------------------------
-- NORMAL CDF APPROXIMATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION normal_cdf(x DOUBLE PRECISION)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
AS $$
    SELECT CASE
        WHEN x >= 0 THEN
            1.0 - normal_tail(ABS(x))
        ELSE
            normal_tail(ABS(x))
    END;
$$;

CREATE OR REPLACE FUNCTION normal_tail(x DOUBLE PRECISION)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
AS $$
    SELECT
        (
            0.3989422804014327
            * EXP(-0.5 * x * x)
            * (
                0.319381530 / (1.0 + 0.2316419 * x)
                + (-0.356563782)
                  / POWER(1.0 + 0.2316419 * x, 2)
                + 1.781477937
                  / POWER(1.0 + 0.2316419 * x, 3)
                + (-1.821255978)
                  / POWER(1.0 + 0.2316419 * x, 4)
                + 1.330274429
                  / POWER(1.0 + 0.2316419 * x, 5)
            )
        );
$$;

-- ------------------------------------------------------------
-- P-VALUE CALCULATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_p_value(
    p_statistic DOUBLE PRECISION,
    p_alternative hypothesis_alternative
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
AS $$
    SELECT CASE p_alternative
        WHEN 'two-sided' THEN
            LEAST(
                1.0,
                2.0 * normal_tail(ABS(p_statistic))
            )
        WHEN 'greater' THEN
            normal_cdf(-p_statistic)
        WHEN 'less' THEN
            normal_cdf(p_statistic)
    END;
$$;

-- ------------------------------------------------------------
-- SAMPLE STATISTICS
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW group_statistics AS
SELECT
    experiment_id,
    group_name,
    COUNT(*) AS sample_size,
    AVG(observation_value) AS sample_mean,
    STDDEV_SAMP(observation_value) AS sample_stddev,
    VAR_SAMP(observation_value) AS sample_variance,
    MIN(observation_value) AS minimum_value,
    MAX(observation_value) AS maximum_value
FROM observations
GROUP BY experiment_id, group_name;

-- ------------------------------------------------------------
-- HYPOTHESIS TEST EVALUATION FUNCTION
--
-- Uses a one-sample Z-test.
-- Population standard deviation must be known.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_one_sample_z(
    p_hypothesis_id BIGINT,
    p_population_stddev DOUBLE PRECISION
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_hypothesis hypotheses%ROWTYPE;
    v_experiment_id BIGINT;

    v_n INTEGER;
    v_mean DOUBLE PRECISION;
    v_standard_error DOUBLE PRECISION;
    v_statistic DOUBLE PRECISION;
    v_p_value DOUBLE PRECISION;

    v_lower DOUBLE PRECISION;
    v_upper DOUBLE PRECISION;

    v_decision test_decision;
    v_critical DOUBLE PRECISION;

    v_result_id BIGINT;
BEGIN
    IF p_population_stddev IS NULL
       OR p_population_stddev <= 0
       OR p_population_stddev = 'Infinity'::DOUBLE PRECISION
       OR p_population_stddev = 'NaN'::DOUBLE PRECISION
    THEN
        RAISE EXCEPTION
            'Population standard deviation must be finite and positive.';
    END IF;

    SELECT *
    INTO STRICT v_hypothesis
    FROM hypotheses
    WHERE hypothesis_id = p_hypothesis_id
    FOR SHARE;

    v_experiment_id := v_hypothesis.experiment_id;

    SELECT
        COUNT(*)::INTEGER,
        AVG(observation_value)
    INTO
        v_n,
        v_mean
    FROM observations
    WHERE experiment_id = v_experiment_id
      AND group_name = 'sample';

    IF v_n < 2 THEN
        RAISE EXCEPTION
            'At least two sample observations are required.';
    END IF;

    v_standard_error :=
        p_population_stddev / SQRT(v_n::DOUBLE PRECISION);

    v_statistic :=
        (v_mean - v_hypothesis.null_value)
        / v_standard_error;

    v_p_value := calculate_p_value(
        v_statistic,
        v_hypothesis.alternative
    );

    -- Normal critical value approximation.
    -- 1.96 and 1.645 are used for common alpha levels.
    IF v_hypothesis.significance_level = 0.05 THEN
        v_critical := 1.959963984540054;
    ELSIF v_hypothesis.significance_level = 0.01 THEN
        v_critical := 2.5758293035489004;
    ELSIF v_hypothesis.significance_level = 0.10 THEN
        v_critical := 1.6448536269514722;
    ELSE
        -- Binary search for other two-sided critical values.
        v_critical := 0;

        WHILE v_critical < 10 LOOP
            IF 2 * normal_tail(v_critical)
               <= v_hypothesis.significance_level THEN
                EXIT;
            END IF;

            v_critical := v_critical + 0.00001;
        END LOOP;
    END IF;

    IF v_hypothesis.alternative = 'two-sided' THEN
        v_lower := v_mean - v_critical * v_standard_error;
        v_upper := v_mean + v_critical * v_standard_error;

    ELSIF v_hypothesis.alternative = 'greater' THEN
        v_lower := v_mean - v_critical * v_standard_error;
        v_upper := NULL;

    ELSE
        v_lower := NULL;
        v_upper := v_mean + v_critical * v_standard_error;
    END IF;

    v_decision := CASE
        WHEN v_p_value < v_hypothesis.significance_level
            THEN 'reject_h0'::test_decision
        ELSE 'fail_to_reject_h0'::test_decision
    END;

    INSERT INTO test_results (
        hypothesis_id,
        test_name,
        sample_size,
        sample_mean,
        sample_stddev,
        standard_error,
        test_statistic,
        p_value,
        confidence_lower,
        confidence_upper,
        decision
    )
    SELECT
        p_hypothesis_id,
        'One-sample Z-test',
        v_n,
        v_mean,
        p_population_stddev,
        v_standard_error,
        v_statistic,
        v_p_value,
        v_lower,
        v_upper,
        v_decision
    RETURNING result_id INTO v_result_id;

    UPDATE experiments
    SET status = 'evaluated',
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = v_experiment_id;

    INSERT INTO experiment_audit (
        experiment_id,
        event_name,
        event_details
    )
    VALUES (
        v_experiment_id,
        'hypothesis_evaluated',
        jsonb_build_object(
            'hypothesis_id', p_hypothesis_id,
            'result_id', v_result_id,
            'p_value', v_p_value,
            'alpha', v_hypothesis.significance_level,
            'decision', v_decision
        )
    );

    RETURN v_result_id;
END;
$$;

-- ------------------------------------------------------------
-- EXPERIMENT STATUS TRANSITION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'evaluated'
       AND NEW.status NOT IN ('evaluated', 'collecting') THEN
        RAISE EXCEPTION
            'Invalid transition from evaluated to %',
            NEW.status;
    END IF;

    IF OLD.status = 'failed'
       AND NEW.status <> 'failed' THEN
        RAISE EXCEPTION
            'Failed experiments cannot be reopened automatically.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_status
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_transition();

-- ------------------------------------------------------------
-- SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO experiments (
    experiment_name,
    description,
    owner_name,
    status
)
VALUES
(
    'Production Quality Study',
    'Evaluation of average production measurements.',
    'Statistics Team',
    'collecting'
),
(
    'Website Conversion Study',
    'Evaluation of website conversion performance.',
    'Product Analytics',
    'collecting'
);

INSERT INTO hypotheses (
    experiment_id,
    hypothesis_name,
    null_value,
    alternative,
    significance_level,
    hypothesis_description
)
VALUES
(
    1,
    'Production Mean Test',
    50.0,
    'two-sided',
    0.05,
    'Test whether the population mean differs from 50.'
),
(
    2,
    'Conversion Mean Test',
    50.0,
    'greater',
    0.01,
    'Test whether the treatment mean exceeds 50.'
);

INSERT INTO observations (
    experiment_id,
    group_name,
    observation_value
)
VALUES
(1, 'sample', 52.1),
(1, 'sample', 50.8),
(1, 'sample', 53.2),
(1, 'sample', 51.7),
(1, 'sample', 54.0),
(1, 'sample', 52.9),
(1, 'sample', 51.4),
(1, 'sample', 53.5),
(1, 'sample', 52.4),
(1, 'sample', 54.1),
(1, 'sample', 51.9),
(1, 'sample', 53.0);

INSERT INTO observations (
    experiment_id,
    group_name,
    observation_value
)
VALUES
(2, 'sample', 52.1),
(2, 'sample', 53.0),
(2, 'sample', 51.8),
(2, 'sample', 54.2),
(2, 'sample', 52.9),
(2, 'sample', 53.5),
(2, 'sample', 51.7),
(2, 'sample', 54.0);

-- ------------------------------------------------------------
-- TRANSACTIONAL TEST EXECUTION
-- ------------------------------------------------------------

SAVEPOINT before_first_test;

SELECT evaluate_one_sample_z(1, 3.0);

RELEASE SAVEPOINT before_first_test;

-- The second experiment can be evaluated separately.
SELECT evaluate_one_sample_z(2, 3.0);

-- ------------------------------------------------------------
-- ERROR ANALYSIS SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO error_analysis (
    hypothesis_id,
    error_category,
    probability,
    description
)
VALUES
(
    1,
    'type_i',
    0.05,
    'Maximum planned Type I error probability.'
),
(
    1,
    'type_ii',
    0.20,
    'Illustrative Type II error probability.'
);

INSERT INTO power_analysis (
    hypothesis_id,
    assumed_true_mean,
    population_stddev,
    planned_sample_size,
    estimated_beta,
    estimated_power
)
VALUES
(
    1,
    52.0,
    3.0,
    30,
    0.20,
    0.80
);

-- ------------------------------------------------------------
-- MULTIPLE TESTING SAMPLE
-- ------------------------------------------------------------

INSERT INTO multiple_testing_batches (
    batch_name,
    adjustment_method,
    alpha
)
VALUES
(
    'Production Quality Batch',
    'benjamini_hochberg',
    0.05
);

INSERT INTO multiple_testing_items (
    batch_id,
    hypothesis_id,
    p_value
)
VALUES
(1, 1, 0.001),
(1, 2, 0.015);

-- ------------------------------------------------------------
-- MULTIPLE TESTING EVALUATION
-- Benjamini-Hochberg step-up procedure.
-- ------------------------------------------------------------

WITH ranked AS (
    SELECT
        batch_id,
        hypothesis_id,
        p_value,
        ROW_NUMBER() OVER (
            PARTITION BY batch_id
            ORDER BY p_value
        ) AS ranking,
        COUNT(*) OVER (
            PARTITION BY batch_id
        ) AS total_tests,
        alpha
    FROM multiple_testing_items
    JOIN multiple_testing_batches USING (batch_id)
),
significant_rank AS (
    SELECT
        batch_id,
        MAX(ranking) FILTER (
            WHERE p_value <= alpha * ranking / total_tests
        ) AS maximum_significant_rank
    FROM ranked
    GROUP BY batch_id
),
adjusted AS (
    SELECT
        r.batch_id,
        r.hypothesis_id,
        LEAST(
            1.0,
            MIN(
                r.p_value * r.total_tests / r.ranking
            ) OVER (
                PARTITION BY r.batch_id
                ORDER BY r.ranking DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )
        ) AS adjusted_p
    FROM ranked r
)
UPDATE multiple_testing_items item
SET
    adjusted_p_value = adjusted.adjusted_p,
    significant = (
        item.p_value <= batch.alpha
        AND ranked_item.ranking <= COALESCE(
            significant_rank.maximum_significant_rank,
            0
        )
    )
FROM adjusted
JOIN multiple_testing_batches batch
    ON batch.batch_id = adjusted.batch_id
JOIN ranked ranked_item
    ON ranked_item.batch_id = adjusted.batch_id
    AND ranked_item.hypothesis_id = adjusted.hypothesis_id
JOIN significant_rank
    ON significant_rank.batch_id = adjusted.batch_id
WHERE item.batch_id = adjusted.batch_id
  AND item.hypothesis_id = adjusted.hypothesis_id;

-- ------------------------------------------------------------
-- RETRIEVAL AND REPORTING QUERIES
-- ------------------------------------------------------------

-- Experiment registry.
SELECT *
FROM experiments
ORDER BY created_at DESC;

-- Defined hypotheses.
SELECT
    e.experiment_name,
    h.hypothesis_name,
    h.null_value,
    h.alternative,
    h.significance_level
FROM hypotheses h
JOIN experiments e USING (experiment_id)
ORDER BY e.experiment_name;

-- Descriptive statistics.
SELECT *
FROM group_statistics
ORDER BY experiment_id, group_name;

-- Test results and decisions.
SELECT
    e.experiment_name,
    h.hypothesis_name,
    r.test_name,
    r.sample_size,
    ROUND(r.sample_mean::NUMERIC, 4) AS sample_mean,
    ROUND(r.test_statistic::NUMERIC, 4) AS statistic,
    ROUND(r.p_value::NUMERIC, 8) AS p_value,
    h.significance_level AS alpha,
    r.decision
FROM test_results r
JOIN hypotheses h USING (hypothesis_id)
JOIN experiments e USING (experiment_id)
ORDER BY r.evaluated_at DESC;

-- Explicit decision validation.
SELECT
    result_id,
    p_value,
    h.significance_level,
    decision,
    (
        p_value < h.significance_level
    ) AS reject_condition_satisfied
FROM test_results r
JOIN hypotheses h USING (hypothesis_id);

-- Type I and Type II error report.
SELECT
    h.hypothesis_name,
    ea.error_category,
    ea.probability
FROM error_analysis ea
JOIN hypotheses h USING (hypothesis_id)
ORDER BY h.hypothesis_name, ea.error_category;

-- Power analysis report.
SELECT
    h.hypothesis_name,
    pa.planned_sample_size,
    pa.assumed_true_mean,
    pa.estimated_beta,
    pa.estimated_power
FROM power_analysis pa
JOIN hypotheses h USING (hypothesis_id);

-- Multiple-testing report.
SELECT
    batch.batch_name,
    item.hypothesis_id,
    item.p_value,
    item.adjusted_p_value,
    item.significant
FROM multiple_testing_items item
JOIN multiple_testing_batches batch USING (batch_id)
ORDER BY item.batch_id, item.p_value;

-- Audit trail.
SELECT
    experiment_id,
    event_name,
    event_details,
    recorded_at
FROM experiment_audit
ORDER BY recorded_at DESC;

COMMIT;
