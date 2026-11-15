/*
    STATISTICAL ANALYSIS PROJECT
    PostgreSQL 14+

    Domain:
    Study hours and examination performance.

    Statistical operations:
    - Descriptive statistics
    - Pearson correlation
    - Simple linear regression
    - Hypothesis testing
    - Fisher-transformation confidence interval
    - Dataset validation
    - Reproducible analysis runs
    - Historical result storage
*/

DROP SCHEMA IF EXISTS statistical_lab CASCADE;

CREATE SCHEMA statistical_lab;

SET search_path TO statistical_lab, public;

-- ============================================================
-- 1. DOMAIN TABLES
-- ============================================================

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT NOT NULL,

    source_name VARCHAR(150) NOT NULL,

    sample_size INTEGER NOT NULL DEFAULT 0
        CHECK (sample_size >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE participants (
    participant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_reference VARCHAR(80) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,

    participant_id BIGINT NOT NULL
        REFERENCES participants(participant_id),

    study_hours NUMERIC(8, 3) NOT NULL
        CHECK (
            study_hours >= 0
            AND study_hours <= 1000
        ),

    exam_score NUMERIC(6, 3) NOT NULL
        CHECK (
            exam_score >= 0
            AND exam_score <= 100
        ),

    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (dataset_id, participant_id)
);

CREATE TABLE analysis_runs (
    analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id),

    analysis_name VARCHAR(150) NOT NULL,

    null_hypothesis TEXT NOT NULL,

    alternative_hypothesis TEXT NOT NULL,

    significance_level NUMERIC(5, 4) NOT NULL
        CHECK (
            significance_level > 0
            AND significance_level < 1
        ),

    permutation_count INTEGER NOT NULL
        CHECK (permutation_count >= 1000),

    bootstrap_count INTEGER NOT NULL
        CHECK (bootstrap_count >= 1000),

    random_seed BIGINT NOT NULL,

    execution_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (
            execution_status IN (
                'PENDING',
                'RUNNING',
                'COMPLETED',
                'FAILED'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ
);

CREATE TABLE statistical_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_id BIGINT NOT NULL UNIQUE
        REFERENCES analysis_runs(analysis_id)
        ON DELETE CASCADE,

    sample_size INTEGER NOT NULL
        CHECK (sample_size >= 4),

    mean_study_hours DOUBLE PRECISION NOT NULL,

    sd_study_hours DOUBLE PRECISION NOT NULL
        CHECK (sd_study_hours >= 0),

    mean_exam_score DOUBLE PRECISION NOT NULL,

    sd_exam_score DOUBLE PRECISION NOT NULL
        CHECK (sd_exam_score >= 0),

    correlation DOUBLE PRECISION NOT NULL
        CHECK (correlation BETWEEN -1 AND 1),

    correlation_ci_lower DOUBLE PRECISION NOT NULL,

    correlation_ci_upper DOUBLE PRECISION NOT NULL,

    regression_slope DOUBLE PRECISION NOT NULL,

    regression_intercept DOUBLE PRECISION NOT NULL,

    r_squared DOUBLE PRECISION NOT NULL
        CHECK (r_squared BETWEEN 0 AND 1),

    rmse DOUBLE PRECISION NOT NULL
        CHECK (rmse >= 0),

    permutation_p_value DOUBLE PRECISION NOT NULL
        CHECK (permutation_p_value BETWEEN 0 AND 1),

    decision VARCHAR(30) NOT NULL
        CHECK (
            decision IN (
                'REJECT_NULL',
                'FAIL_TO_REJECT_NULL'
            )
        ),

    CHECK (correlation_ci_lower <= correlation_ci_upper)
);

-- ============================================================
-- 2. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_observations_dataset
    ON observations(dataset_id);

CREATE INDEX idx_observations_participant
    ON observations(participant_id);

CREATE INDEX idx_observations_study_hours
    ON observations(dataset_id, study_hours);

CREATE INDEX idx_analysis_runs_dataset_date
    ON analysis_runs(dataset_id, created_at DESC);

CREATE INDEX idx_analysis_runs_status
    ON analysis_runs(execution_status);

-- ============================================================
-- 3. AUDIT AND INTEGRITY TRIGGER
-- ============================================================

CREATE TABLE observation_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    observation_id BIGINT NOT NULL,

    operation_type VARCHAR(10) NOT NULL,

    old_values JSONB,

    new_values JSONB,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION audit_observation_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO observation_audit (
            observation_id,
            operation_type,
            new_values
        )
        VALUES (
            NEW.observation_id,
            'INSERT',
            to_jsonb(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO observation_audit (
            observation_id,
            operation_type,
            old_values,
            new_values
        )
        VALUES (
            NEW.observation_id,
            'UPDATE',
            to_jsonb(OLD),
            to_jsonb(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO observation_audit (
            observation_id,
            operation_type,
            old_values
        )
        VALUES (
            OLD.observation_id,
            'DELETE',
            to_jsonb(OLD)
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_observation_audit
AFTER INSERT OR UPDATE OR DELETE
ON observations
FOR EACH ROW
EXECUTE FUNCTION audit_observation_changes();

-- ============================================================
-- 4. DATASET SAMPLE RECORDS
-- ============================================================

INSERT INTO datasets (
    dataset_name,
    description,
    source_name
)
VALUES (
    'Student Performance Study',
    'Relationship between weekly study hours and examination scores.',
    'Synthetic educational research dataset'
);

INSERT INTO participants (external_reference)
SELECT 'STUDENT-' || LPAD(value::TEXT, 3, '0')
FROM generate_series(1, 12) AS value;

INSERT INTO observations (
    dataset_id,
    participant_id,
    study_hours,
    exam_score
)
SELECT
    1,
    p.participant_id,
    sample.study_hours,
    sample.exam_score
FROM (
    VALUES
        (1, 1.0, 48.0),
        (2, 1.5, 52.0),
        (3, 2.0, 55.0),
        (4, 2.5, 58.0),
        (5, 3.0, 62.0),
        (6, 3.5, 65.0),
        (7, 4.0, 68.0),
        (8, 4.5, 70.0),
        (9, 5.0, 74.0),
        (10, 5.5, 77.0),
        (11, 6.0, 80.0),
        (12, 7.0, 86.0)
) AS sample(reference_number, study_hours, exam_score)
JOIN participants p
    ON p.external_reference =
       'STUDENT-' || LPAD(sample.reference_number::TEXT, 3, '0');

UPDATE datasets
SET sample_size = (
    SELECT COUNT(*)
    FROM observations
    WHERE dataset_id = 1
)
WHERE dataset_id = 1;

-- ============================================================
-- 5. DESCRIPTIVE STATISTICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_descriptive_statistics AS
SELECT
    dataset_id,

    COUNT(*) AS sample_size,

    ROUND(AVG(study_hours), 3) AS mean_study_hours,

    ROUND(STDDEV_SAMP(study_hours), 3)
        AS sd_study_hours,

    ROUND(MIN(study_hours), 3)
        AS minimum_study_hours,

    ROUND(MAX(study_hours), 3)
        AS maximum_study_hours,

    ROUND(AVG(exam_score), 3)
        AS mean_exam_score,

    ROUND(STDDEV_SAMP(exam_score), 3)
        AS sd_exam_score,

    ROUND(MIN(exam_score), 3)
        AS minimum_exam_score,

    ROUND(MAX(exam_score), 3)
        AS maximum_exam_score,

    ROUND(CORR(study_hours, exam_score)::NUMERIC, 6)
        AS pearson_correlation,

    ROUND(REGR_SLOPE(exam_score, study_hours)::NUMERIC, 6)
        AS regression_slope,

    ROUND(REGR_INTERCEPT(exam_score, study_hours)::NUMERIC, 6)
        AS regression_intercept,

    ROUND(REGR_R2(exam_score, study_hours)::NUMERIC, 6)
        AS r_squared

FROM observations
GROUP BY dataset_id;

-- ============================================================
-- 6. ANALYSIS REGISTRATION
-- ============================================================

INSERT INTO analysis_runs (
    dataset_id,
    analysis_name,
    null_hypothesis,
    alternative_hypothesis,
    significance_level,
    permutation_count,
    bootstrap_count,
    random_seed
)
VALUES (
    1,
    'Study Hours and Examination Performance',
    'Population Pearson correlation equals zero.',
    'Population Pearson correlation differs from zero.',
    0.05,
    10000,
    5000,
    42
);

-- ============================================================
-- 7. FISHER TRANSFORMATION CONFIDENCE INTERVAL
-- ============================================================

CREATE OR REPLACE FUNCTION correlation_confidence_interval(
    p_correlation DOUBLE PRECISION,
    p_sample_size INTEGER,
    p_confidence DOUBLE PRECISION DEFAULT 0.95
)
RETURNS TABLE (
    lower_bound DOUBLE PRECISION,
    upper_bound DOUBLE PRECISION
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    z_critical DOUBLE PRECISION;
    fisher_z DOUBLE PRECISION;
    standard_error DOUBLE PRECISION;
    tail_probability DOUBLE PRECISION;
BEGIN
    IF p_sample_size < 4 THEN
        RAISE EXCEPTION
            'At least four observations are required.';
    END IF;

    IF p_correlation <= -1 OR p_correlation >= 1 THEN
        RAISE EXCEPTION
            'Correlation must be strictly between -1 and 1.';
    END IF;

    IF p_confidence <= 0 OR p_confidence >= 1 THEN
        RAISE EXCEPTION
            'Confidence must be between zero and one.';
    END IF;

    -- Approximate two-sided normal critical value.
    -- The Fisher transformation provides the correlation interval.
    tail_probability := (1 - p_confidence) / 2;

    z_critical := CASE
        WHEN ABS(p_confidence - 0.95) < 0.000001 THEN 1.959964
        WHEN ABS(p_confidence - 0.90) < 0.000001 THEN 1.644854
        WHEN ABS(p_confidence - 0.99) < 0.000001 THEN 2.575829
        ELSE NULL
    END;

    IF z_critical IS NULL THEN
        RAISE EXCEPTION
            'Supported confidence levels are 0.90, 0.95 and 0.99.';
    END IF;

    fisher_z := 0.5 * LN(
        (1 + p_correlation) / (1 - p_correlation)
    );

    standard_error := 1 / SQRT(p_sample_size - 3);

    lower_bound := TANH(
        fisher_z - z_critical * standard_error
    );

    upper_bound := TANH(
        fisher_z + z_critical * standard_error
    );

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 8. ANALYSIS REPORTING FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION generate_statistical_report(
    p_dataset_id BIGINT
)
RETURNS TABLE (
    dataset_name VARCHAR,
    sample_size BIGINT,
    correlation DOUBLE PRECISION,
    ci_lower DOUBLE PRECISION,
    ci_upper DOUBLE PRECISION,
    regression_slope DOUBLE PRECISION,
    r_squared DOUBLE PRECISION,
    interpretation TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_correlation DOUBLE PRECISION;
    v_size BIGINT;
    v_lower DOUBLE PRECISION;
    v_upper DOUBLE PRECISION;
    v_name VARCHAR;
BEGIN
    SELECT
        d.dataset_name,
        COUNT(o.observation_id),
        CORR(o.study_hours, o.exam_score)
    INTO
        v_name,
        v_size,
        v_correlation
    FROM datasets d
    JOIN observations o
        ON o.dataset_id = d.dataset_id
    WHERE d.dataset_id = p_dataset_id
    GROUP BY d.dataset_name;

    IF v_size IS NULL OR v_size < 4 THEN
        RAISE EXCEPTION
            'Dataset does not contain enough valid observations.';
    END IF;

    SELECT
        ci.lower_bound,
        ci.upper_bound
    INTO
        v_lower,
        v_upper
    FROM correlation_confidence_interval(
        v_correlation,
        v_size::INTEGER,
        0.95
    ) AS ci;

    RETURN QUERY
    SELECT
        v_name,
        v_size,
        v_correlation,
        v_lower,
        v_upper,
        REGR_SLOPE(o.exam_score, o.study_hours),
        REGR_R2(o.exam_score, o.study_hours),
        CASE
            WHEN v_correlation >= 0.7
                THEN 'Strong positive association'
            WHEN v_correlation >= 0.4
                THEN 'Moderate positive association'
            WHEN v_correlation > 0
                THEN 'Weak positive association'
            WHEN v_correlation <= -0.7
                THEN 'Strong negative association'
            WHEN v_correlation <= -0.4
                THEN 'Moderate negative association'
            ELSE 'Weak or negative association'
        END
    FROM observations o
    WHERE o.dataset_id = p_dataset_id
    GROUP BY o.dataset_id;
END;
$$;

-- ============================================================
-- 9. WORKFLOW PROCESSING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE complete_analysis(
    p_analysis_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_dataset_id BIGINT;
    v_size INTEGER;
    v_correlation DOUBLE PRECISION;
    v_slope DOUBLE PRECISION;
    v_intercept DOUBLE PRECISION;
    v_r_squared DOUBLE PRECISION;
    v_rmse DOUBLE PRECISION;
    v_mean_x DOUBLE PRECISION;
    v_sd_x DOUBLE PRECISION;
    v_mean_y DOUBLE PRECISION;
    v_sd_y DOUBLE PRECISION;
    v_ci_lower DOUBLE PRECISION;
    v_ci_upper DOUBLE PRECISION;
    v_p_value DOUBLE PRECISION;
    v_alpha NUMERIC;
BEGIN
    SELECT
        dataset_id,
        significance_level
    INTO
        v_dataset_id,
        v_alpha
    FROM analysis_runs
    WHERE analysis_id = p_analysis_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Analysis run does not exist.';
    END IF;

    UPDATE analysis_runs
    SET execution_status = 'RUNNING'
    WHERE analysis_id = p_analysis_id;

    SELECT
        COUNT(*)::INTEGER,
        CORR(study_hours, exam_score),
        REGR_SLOPE(exam_score, study_hours),
        REGR_INTERCEPT(exam_score, study_hours),
        REGR_R2(exam_score, study_hours),
        SQRT(
            AVG(
                POWER(
                    exam_score -
                    (
                        REGR_INTERCEPT(exam_score, study_hours)
                        + REGR_SLOPE(exam_score, study_hours)
                        * study_hours
                    ),
                    2
                )
            )
        ),
        AVG(study_hours),
        STDDEV_SAMP(study_hours),
        AVG(exam_score),
        STDDEV_SAMP(exam_score)
    INTO
        v_size,
        v_correlation,
        v_slope,
        v_intercept,
        v_r_squared,
        v_rmse,
        v_mean_x,
        v_sd_x,
        v_mean_y,
        v_sd_y
    FROM observations
    WHERE dataset_id = v_dataset_id;

    IF v_size < 4 OR v_correlation IS NULL THEN
        RAISE EXCEPTION 'Insufficient valid observations.';
    END IF;

    SELECT
        lower_bound,
        upper_bound
    INTO
        v_ci_lower,
        v_ci_upper
    FROM correlation_confidence_interval(
        v_correlation,
        v_size,
        0.95
    );

    /*
       PostgreSQL provides descriptive and regression statistics.
       A genuine permutation p-value requires randomized resampling.
       This procedure does not fabricate one. The value below is
       NULL until an external or database-native permutation engine
       supplies the calculated result.

       A separate completed result must contain a valid p-value.
    */

    RAISE EXCEPTION
        'Permutation inference is required before finalization. Use a computed permutation p-value and record the result through the validation workflow.';

EXCEPTION
    WHEN OTHERS THEN
        UPDATE analysis_runs
        SET
            execution_status = 'FAILED',
            completed_at = CURRENT_TIMESTAMP
        WHERE analysis_id = p_analysis_id;

        RAISE;
END;
$$;

-- ============================================================
-- 10. DESCRIPTIVE AND REGRESSION RETRIEVAL
-- ============================================================

SELECT *
FROM v_descriptive_statistics
ORDER BY dataset_id;

SELECT *
FROM generate_statistical_report(1);

-- ============================================================
-- 11. GROUPED ANALYSIS
-- ============================================================

WITH grouped_observations AS (
    SELECT
        CASE
            WHEN study_hours < 3 THEN 'LOW STUDY TIME'
            WHEN study_hours < 5 THEN 'MEDIUM STUDY TIME'
            ELSE 'HIGH STUDY TIME'
        END AS study_category,

        study_hours,
        exam_score

    FROM observations
    WHERE dataset_id = 1
)
SELECT
    study_category,
    COUNT(*) AS participants,
    ROUND(AVG(study_hours), 2) AS average_study_hours,
    ROUND(AVG(exam_score), 2) AS average_exam_score,
    ROUND(STDDEV_SAMP(exam_score), 2) AS score_standard_deviation
FROM grouped_observations
GROUP BY study_category
ORDER BY average_study_hours;

-- ============================================================
-- 12. DATA VALIDATION QUERIES
-- ============================================================

SELECT
    observation_id,
    participant_id,
    study_hours,
    exam_score,
    CASE
        WHEN study_hours < 0 THEN 'INVALID STUDY HOURS'
        WHEN exam_score NOT BETWEEN 0 AND 100 THEN 'INVALID SCORE'
        ELSE 'VALID'
    END AS validation_status
FROM observations
WHERE dataset_id = 1;

SELECT
    dataset_id,
    COUNT(*) AS actual_sample_size,
    COUNT(DISTINCT participant_id) AS unique_participants
FROM observations
GROUP BY dataset_id;

-- ============================================================
-- 13. ELIGIBILITY AND HYPOTHESIS REPORTING
-- ============================================================

SELECT
    r.analysis_id,
    r.analysis_name,
    r.significance_level,
    r.execution_status,
    d.dataset_name,
    d.sample_size,
    CASE
        WHEN d.sample_size < 4 THEN 'INSUFFICIENT DATA'
        WHEN r.execution_status = 'COMPLETED' THEN 'RESULT AVAILABLE'
        WHEN r.execution_status = 'FAILED' THEN 'INVESTIGATION REQUIRED'
        ELSE 'PENDING INFERENCE'
    END AS analysis_eligibility
FROM analysis_runs r
JOIN datasets d
    ON d.dataset_id = r.dataset_id;

-- ============================================================
-- 14. AUDIT RETRIEVAL
-- ============================================================

SELECT
    audit_id,
    observation_id,
    operation_type,
    changed_at,
    old_values,
    new_values
FROM observation_audit
ORDER BY changed_at DESC;

-- ============================================================
-- 15. TRANSACTION EXAMPLE
-- ============================================================

BEGIN;

SAVEPOINT before_observation_update;

UPDATE observations
SET exam_score = exam_score + 1
WHERE dataset_id = 1
  AND participant_id = (
      SELECT participant_id
      FROM participants
      WHERE external_reference = 'STUDENT-001'
  );

-- Demonstrate rollback of the illustrative update.
ROLLBACK TO SAVEPOINT before_observation_update;

COMMIT;

-- ============================================================
-- 16. FINAL DATASET REPORT
-- ============================================================

SELECT
    d.dataset_name,
    d.source_name,
    d.sample_size,
    s.mean_study_hours,
    s.mean_exam_score,
    s.pearson_correlation,
    s.regression_slope,
    s.r_squared
FROM datasets d
JOIN v_descriptive_statistics s
    ON s.dataset_id = d.dataset_id
ORDER BY d.dataset_id;
