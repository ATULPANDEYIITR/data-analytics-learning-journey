/*
    Statistical Tests I
    PostgreSQL 15+

    Relational statistical analysis:
    1. One-sample t-test statistics.
    2. Independent Welch two-sample t-test statistics.
    3. Independent pooled two-sample t-test statistics.
    4. Paired t-test statistics.

    This SQL implementation calculates test statistics,
    sample variances, standard errors, and degrees of freedom.

    Exact Student's t-distribution p-values are calculated
    in the Python, JavaScript, C++, and Java implementations.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS statistical_tests;

SET search_path TO statistical_tests, public;

-- Remove existing demonstration objects for reproducibility.
DROP VIEW IF EXISTS paired_test_statistics CASCADE;
DROP VIEW IF EXISTS independent_test_statistics CASCADE;
DROP VIEW IF EXISTS one_sample_test_statistics CASCADE;
DROP TABLE IF EXISTS observations CASCADE;
DROP TABLE IF EXISTS experiments CASCADE;
DROP TABLE IF EXISTS experiment_groups CASCADE;

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_name VARCHAR(150) NOT NULL,
    test_type VARCHAR(30) NOT NULL CHECK (
        test_type IN (
            'one_sample',
            'independent',
            'paired'
        )
    ),
    hypothesized_mean NUMERIC(15, 6),
    alpha NUMERIC(8, 6) NOT NULL DEFAULT 0.05 CHECK (
        alpha > 0 AND alpha < 1
    ),
    equal_variance_assumption BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,
    CONSTRAINT valid_one_sample_mean CHECK (
        test_type <> 'one_sample'
        OR hypothesized_mean IS NOT NULL
    )
);

CREATE TABLE experiment_groups (
    group_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(
        experiment_id
    ) ON DELETE CASCADE,
    group_name VARCHAR(100) NOT NULL,
    group_role VARCHAR(20) NOT NULL CHECK (
        group_role IN ('single', 'control', 'treatment', 'paired')
    ),
    UNIQUE (experiment_id, group_name),
    UNIQUE (experiment_id, group_id)
);

CREATE TABLE observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    subject_id VARCHAR(100),
    observation_value NUMERIC(15, 6) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT observation_group_fk
        FOREIGN KEY (experiment_id, group_id)
        REFERENCES experiment_groups(experiment_id, group_id),

    CONSTRAINT valid_observation_value CHECK (
        observation_value BETWEEN -1000000000 AND 1000000000
    )
);

-- Useful for group aggregation and experiment retrieval.
CREATE INDEX idx_observations_experiment_group
ON observations(experiment_id, group_id);

CREATE INDEX idx_observations_subject
ON observations(experiment_id, subject_id)
WHERE subject_id IS NOT NULL;

CREATE INDEX idx_experiments_created_at
ON experiments(created_at DESC);


-- ============================================================
-- 1. ONE-SAMPLE TEST
-- ============================================================

CREATE VIEW one_sample_test_statistics AS
WITH sample_summary AS (
    SELECT
        e.experiment_id,
        e.experiment_name,
        e.hypothesized_mean,
        e.alpha,
        COUNT(o.observation_id) AS sample_size,
        AVG(o.observation_value) AS sample_mean,
        VAR_SAMP(o.observation_value) AS sample_variance,
        STDDEV_SAMP(o.observation_value) AS sample_stddev
    FROM experiments e
    JOIN experiment_groups g
        ON g.experiment_id = e.experiment_id
    JOIN observations o
        ON o.experiment_id = e.experiment_id
       AND o.group_id = g.group_id
    WHERE e.test_type = 'one_sample'
      AND g.group_role = 'single'
    GROUP BY
        e.experiment_id,
        e.experiment_name,
        e.hypothesized_mean,
        e.alpha
)
SELECT
    experiment_id,
    experiment_name,
    sample_size,
    sample_mean,
    hypothesized_mean,
    sample_variance,
    sample_stddev,
    sample_mean - hypothesized_mean AS mean_difference,
    sample_size - 1 AS degrees_of_freedom,

    CASE
        WHEN sample_size < 2 THEN NULL
        WHEN sample_variance = 0 THEN NULL
        ELSE (
            sample_mean - hypothesized_mean
        ) / SQRT(sample_variance / sample_size)
    END AS t_statistic,

    CASE
        WHEN sample_size < 2 THEN NULL
        WHEN sample_variance = 0 THEN NULL
        ELSE SQRT(sample_variance / sample_size)
    END AS standard_error,

    alpha
FROM sample_summary;


-- ============================================================
-- 2. INDEPENDENT TWO-SAMPLE TESTS
-- ============================================================

CREATE VIEW independent_test_statistics AS
WITH group_summary AS (
    SELECT
        e.experiment_id,
        e.experiment_name,
        e.alpha,
        e.equal_variance_assumption,
        g.group_role,
        COUNT(o.observation_id) AS sample_size,
        AVG(o.observation_value) AS sample_mean,
        VAR_SAMP(o.observation_value) AS sample_variance
    FROM experiments e
    JOIN experiment_groups g
        ON g.experiment_id = e.experiment_id
    JOIN observations o
        ON o.experiment_id = e.experiment_id
       AND o.group_id = g.group_id
    WHERE e.test_type = 'independent'
      AND g.group_role IN ('control', 'treatment')
    GROUP BY
        e.experiment_id,
        e.experiment_name,
        e.alpha,
        e.equal_variance_assumption,
        g.group_role
),
paired_summary AS (
    SELECT
        experiment_id,
        experiment_name,
        alpha,
        equal_variance_assumption,

        MAX(sample_size) FILTER (
            WHERE group_role = 'control'
        ) AS n1,

        MAX(sample_size) FILTER (
            WHERE group_role = 'treatment'
        ) AS n2,

        MAX(sample_mean) FILTER (
            WHERE group_role = 'control'
        ) AS mean1,

        MAX(sample_mean) FILTER (
            WHERE group_role = 'treatment'
        ) AS mean2,

        MAX(sample_variance) FILTER (
            WHERE group_role = 'control'
        ) AS variance1,

        MAX(sample_variance) FILTER (
            WHERE group_role = 'treatment'
        ) AS variance2

    FROM group_summary
    GROUP BY
        experiment_id,
        experiment_name,
        alpha,
        equal_variance_assumption
)
SELECT
    experiment_id,
    experiment_name,
    n1,
    n2,
    mean1,
    mean2,
    variance1,
    variance2,
    mean1 - mean2 AS mean_difference,

    CASE
        WHEN equal_variance_assumption
        THEN n1 + n2 - 2
        ELSE (
            POWER(
                variance1 / n1 + variance2 / n2,
                2
            )
            /
            (
                POWER(variance1 / n1, 2) / (n1 - 1)
                +
                POWER(variance2 / n2, 2) / (n2 - 1)
            )
        )
    END AS degrees_of_freedom,

    CASE
        WHEN equal_variance_assumption
        THEN SQRT(
            (
                (n1 - 1) * variance1
                +
                (n2 - 1) * variance2
            )
            / (n1 + n2 - 2)
            * (1.0 / n1 + 1.0 / n2)
        )
        ELSE SQRT(
            variance1 / n1 + variance2 / n2
        )
    END AS standard_error,

    CASE
        WHEN equal_variance_assumption
        THEN 'POOLED'
        ELSE 'WELCH'
    END AS statistical_method,

    alpha

FROM paired_summary
WHERE n1 >= 2
  AND n2 >= 2
  AND variance1 IS NOT NULL
  AND variance2 IS NOT NULL;


-- ============================================================
-- 3. PAIRED TEST
-- ============================================================

CREATE VIEW paired_test_statistics AS
WITH paired_observations AS (
    SELECT
        e.experiment_id,
        e.experiment_name,
        e.alpha,
        before_obs.subject_id,
        before_obs.observation_value AS before_value,
        after_obs.observation_value AS after_value,
        after_obs.observation_value
            - before_obs.observation_value AS difference

    FROM experiments e

    JOIN experiment_groups before_group
        ON before_group.experiment_id = e.experiment_id
       AND before_group.group_role = 'control'

    JOIN experiment_groups after_group
        ON after_group.experiment_id = e.experiment_id
       AND after_group.group_role = 'treatment'

    JOIN observations before_obs
        ON before_obs.experiment_id = e.experiment_id
       AND before_obs.group_id = before_group.group_id

    JOIN observations after_obs
        ON after_obs.experiment_id = e.experiment_id
       AND after_obs.group_id = after_group.group_id
       AND after_obs.subject_id = before_obs.subject_id

    WHERE e.test_type = 'paired'
      AND before_obs.subject_id IS NOT NULL
),
difference_summary AS (
    SELECT
        experiment_id,
        experiment_name,
        alpha,
        COUNT(*) AS sample_size,
        AVG(difference) AS mean_difference,
        VAR_SAMP(difference) AS difference_variance,
        STDDEV_SAMP(difference) AS difference_stddev
    FROM paired_observations
    GROUP BY
        experiment_id,
        experiment_name,
        alpha
)
SELECT
    experiment_id,
    experiment_name,
    sample_size,
    mean_difference,
    difference_variance,
    difference_stddev,
    sample_size - 1 AS degrees_of_freedom,

    CASE
        WHEN sample_size < 2 THEN NULL
        WHEN difference_variance = 0 THEN NULL
        ELSE mean_difference /
            SQRT(difference_variance / sample_size)
    END AS t_statistic,

    CASE
        WHEN sample_size < 2 THEN NULL
        WHEN difference_variance = 0 THEN NULL
        ELSE SQRT(difference_variance / sample_size)
    END AS standard_error,

    alpha

FROM difference_summary;


-- ============================================================
-- 4. DATA INTEGRITY VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_experiment_group_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_type VARCHAR(30);
    single_count INTEGER;
    control_count INTEGER;
    treatment_count INTEGER;
BEGIN
    SELECT test_type
    INTO current_type
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF current_type IS NULL THEN
        RAISE EXCEPTION 'Experiment does not exist.';
    END IF;

    SELECT
        COUNT(*) FILTER (WHERE group_role = 'single'),
        COUNT(*) FILTER (WHERE group_role = 'control'),
        COUNT(*) FILTER (WHERE group_role = 'treatment')
    INTO single_count, control_count, treatment_count
    FROM experiment_groups
    WHERE experiment_id = NEW.experiment_id;

    IF current_type = 'one_sample'
       AND single_count > 1 THEN
        RAISE EXCEPTION
            'One-sample experiments support one single group.';
    END IF;

    IF current_type IN ('independent', 'paired')
       AND (single_count > 0 OR control_count > 1
            OR treatment_count > 1) THEN
        RAISE EXCEPTION
            'Two-group experiments require distinct control and treatment groups.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment_group
AFTER INSERT ON experiment_groups
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_group_count();


-- Paired experiments require unique subject observations
-- within each group. This prevents accidental duplicate pairing.

CREATE UNIQUE INDEX uq_paired_subject_observation
ON observations(experiment_id, group_id, subject_id)
WHERE subject_id IS NOT NULL;


-- ============================================================
-- 5. REUSABLE EXPERIMENT CREATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE create_experiment(
    p_name VARCHAR(150),
    p_test_type VARCHAR(30),
    p_alpha NUMERIC(8, 6),
    p_created_by VARCHAR(100),
    p_hypothesized_mean NUMERIC(15, 6),
    OUT p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_name IS NULL OR LENGTH(TRIM(p_name)) = 0 THEN
        RAISE EXCEPTION 'Experiment name is required.';
    END IF;

    IF p_alpha <= 0 OR p_alpha >= 1 THEN
        RAISE EXCEPTION 'Alpha must be between zero and one.';
    END IF;

    IF p_test_type = 'one_sample'
       AND p_hypothesized_mean IS NULL THEN
        RAISE EXCEPTION
            'One-sample test requires a hypothesized mean.';
    END IF;

    INSERT INTO experiments (
        experiment_name,
        test_type,
        alpha,
        created_by,
        hypothesized_mean
    )
    VALUES (
        p_name,
        p_test_type,
        p_alpha,
        p_created_by,
        p_hypothesized_mean
    )
    RETURNING experiment_id INTO p_experiment_id;
END;
$$;


-- ============================================================
-- 6. SAMPLE EXPERIMENTS
-- ============================================================

INSERT INTO experiments (
    experiment_name,
    test_type,
    hypothesized_mean,
    alpha,
    created_by
)
VALUES
(
    'Delivery Time Quality Assessment',
    'one_sample',
    30,
    0.05,
    'quality_team'
),
(
    'Training Method Comparison',
    'independent',
    NULL,
    0.05,
    'research_team'
),
(
    'Employee Training Before and After',
    'paired',
    NULL,
    0.05,
    'hr_analytics'
);


INSERT INTO experiment_groups (
    experiment_id,
    group_name,
    group_role
)
VALUES
(1, 'Delivery Observations', 'single'),
(2, 'Control Method', 'control'),
(2, 'Treatment Method', 'treatment'),
(3, 'Before Training', 'control'),
(3, 'After Training', 'treatment');


-- One-sample observations.
INSERT INTO observations (
    experiment_id,
    group_id,
    subject_id,
    observation_value
)
VALUES
(1, 1, 'D01', 28),
(1, 1, 'D02', 31),
(1, 1, 'D03', 29),
(1, 1, 'D04', 32),
(1, 1, 'D05', 30),
(1, 1, 'D06', 27),
(1, 1, 'D07', 34),
(1, 1, 'D08', 31),
(1, 1, 'D09', 29),
(1, 1, 'D10', 30);


-- Independent groups.
INSERT INTO observations (
    experiment_id,
    group_id,
    subject_id,
    observation_value
)
VALUES
(2, 2, 'C01', 72),
(2, 2, 'C02', 75),
(2, 2, 'C03', 78),
(2, 2, 'C04', 74),
(2, 2, 'C05', 71),
(2, 2, 'C06', 80),
(2, 2, 'C07', 77),
(2, 2, 'C08', 76),

(2, 3, 'T01', 81),
(2, 3, 'T02', 84),
(2, 3, 'T03', 79),
(2, 3, 'T04', 86),
(2, 3, 'T05', 82),
(2, 3, 'T06', 83),
(2, 3, 'T07', 85),
(2, 3, 'T08', 80);


-- Paired observations.
INSERT INTO observations (
    experiment_id,
    group_id,
    subject_id,
    observation_value
)
VALUES
(3, 4, 'E01', 65),
(3, 4, 'E02', 70),
(3, 4, 'E03', 72),
(3, 4, 'E04', 68),
(3, 4, 'E05', 75),
(3, 4, 'E06', 71),
(3, 4, 'E07', 69),
(3, 4, 'E08', 73),

(3, 5, 'E01', 72),
(3, 5, 'E02', 74),
(3, 5, 'E03', 76),
(3, 5, 'E04', 75),
(3, 5, 'E05', 79),
(3, 5, 'E06', 76),
(3, 5, 'E07', 74),
(3, 5, 'E08', 78);


-- ============================================================
-- 7. RETRIEVAL AND REPORTING QUERIES
-- ============================================================

-- Experiment inventory.
SELECT
    experiment_id,
    experiment_name,
    test_type,
    hypothesized_mean,
    alpha,
    created_by,
    created_at
FROM experiments
ORDER BY experiment_id;


-- One-sample statistical evaluation.
SELECT *
FROM one_sample_test_statistics
ORDER BY experiment_id;


-- Independent test evaluation.
SELECT
    experiment_id,
    experiment_name,
    statistical_method,
    n1,
    n2,
    mean1,
    mean2,
    mean_difference,
    standard_error,
    degrees_of_freedom,
    CASE
        WHEN standard_error = 0 THEN NULL
        ELSE mean_difference / standard_error
    END AS t_statistic
FROM independent_test_statistics;


-- Paired test evaluation.
SELECT *
FROM paired_test_statistics
ORDER BY experiment_id;


-- Group-level descriptive statistics.
SELECT
    e.experiment_name,
    g.group_name,
    COUNT(o.observation_id) AS observations,
    ROUND(AVG(o.observation_value), 4) AS average,
    ROUND(STDDEV_SAMP(o.observation_value), 4) AS stddev,
    ROUND(VAR_SAMP(o.observation_value), 4) AS variance,
    MIN(o.observation_value) AS minimum,
    MAX(o.observation_value) AS maximum
FROM experiments e
JOIN experiment_groups g
    ON g.experiment_id = e.experiment_id
LEFT JOIN observations o
    ON o.experiment_id = e.experiment_id
   AND o.group_id = g.group_id
GROUP BY
    e.experiment_name,
    g.group_name
ORDER BY
    e.experiment_name,
    g.group_name;


-- Sample size validation.
SELECT
    e.experiment_name,
    g.group_name,
    COUNT(o.observation_id) AS sample_size,
    CASE
        WHEN COUNT(o.observation_id) >= 2 THEN 'VALID'
        ELSE 'INSUFFICIENT DATA'
    END AS validation_status
FROM experiments e
JOIN experiment_groups g
    ON g.experiment_id = e.experiment_id
LEFT JOIN observations o
    ON o.experiment_id = e.experiment_id
   AND o.group_id = g.group_id
GROUP BY
    e.experiment_name,
    g.group_name;


-- Detect missing subject pairs.
SELECT
    e.experiment_name,
    COALESCE(before_obs.subject_id, after_obs.subject_id)
        AS subject_id
FROM experiments e
JOIN experiment_groups before_group
    ON before_group.experiment_id = e.experiment_id
   AND before_group.group_role = 'control'
JOIN experiment_groups after_group
    ON after_group.experiment_id = e.experiment_id
   AND after_group.group_role = 'treatment'
FULL JOIN observations before_obs
    ON before_obs.experiment_id = e.experiment_id
   AND before_obs.group_id = before_group.group_id
FULL JOIN observations after_obs
    ON after_obs.experiment_id = e.experiment_id
   AND after_obs.group_id = after_group.group_id
   AND after_obs.subject_id = before_obs.subject_id
WHERE e.test_type = 'paired'
  AND (
      before_obs.observation_id IS NULL
      OR after_obs.observation_id IS NULL
  );


-- ============================================================
-- 8. TRANSACTION AND WORKFLOW EXAMPLE
-- ============================================================

SAVEPOINT before_additional_experiment;

INSERT INTO experiments (
    experiment_name,
    test_type,
    hypothesized_mean,
    alpha,
    created_by
)
VALUES (
    'Additional Delivery Validation',
    'one_sample',
    25,
    0.01,
    'quality_team'
);

INSERT INTO experiment_groups (
    experiment_id,
    group_name,
    group_role
)
SELECT
    experiment_id,
    'Single Sample',
    'single'
FROM experiments
WHERE experiment_name = 'Additional Delivery Validation';

INSERT INTO observations (
    experiment_id,
    group_id,
    subject_id,
    observation_value
)
SELECT
    e.experiment_id,
    g.group_id,
    sample.subject_id,
    sample.observation_value
FROM experiments e
JOIN experiment_groups g
    ON g.experiment_id = e.experiment_id
CROSS JOIN (
    VALUES
        ('A01', 24.0),
        ('A02', 25.0),
        ('A03', 27.0),
        ('A04', 26.0)
) AS sample(subject_id, observation_value)
WHERE e.experiment_name = 'Additional Delivery Validation'
  AND g.group_role = 'single';

RELEASE SAVEPOINT before_additional_experiment;

-- The transaction is committed only after all operations succeed.
COMMIT;

-- Final experiment count.
SELECT COUNT(*) AS total_experiments
FROM statistical_tests.experiments;
