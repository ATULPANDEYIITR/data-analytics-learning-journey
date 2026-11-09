/*
    STATISTICAL TESTS II
    PostgreSQL 14+

    Statistical workflows:
    1. Chi-square goodness-of-fit.
    2. Chi-square independence.
    3. One-sample proportion tests.
    4. Two-sample proportion tests.

    The database stores observations, expected frequencies,
    hypotheses, statistical results, and execution states.

    Chi-square p-values use the Wilson-Hilferty approximation
    to the chi-square distribution's upper-tail probability.
    Proportion p-values use a normal-tail approximation.

    These SQL approximations are suitable for demonstrating
    relational statistical workflows. Use the more accurate
    gamma-function implementations for precision-sensitive
    statistical reporting.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS statistical_tests;

SET search_path TO statistical_tests, public;

-- ============================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE test_type AS ENUM (
    'GOODNESS_OF_FIT',
    'INDEPENDENCE',
    'ONE_PROPORTION',
    'TWO_PROPORTION'
);

CREATE TYPE analysis_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'EXECUTED',
    'FAILED'
);

CREATE TYPE decision_type AS ENUM (
    'REJECT_NULL',
    'FAIL_TO_REJECT_NULL'
);

-- ============================================================
-- 2. STATISTICAL EXPERIMENTS
-- ============================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    alpha NUMERIC(8, 6) NOT NULL DEFAULT 0.05,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_alpha
        CHECK (alpha > 0 AND alpha < 1),

    CONSTRAINT valid_experiment_name
        CHECK (length(trim(experiment_name)) > 0)
);

CREATE TABLE statistical_analyses (
    analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    test_category test_type NOT NULL,
    null_hypothesis TEXT NOT NULL,
    alternative_hypothesis TEXT NOT NULL,

    status analysis_status NOT NULL DEFAULT 'CREATED',

    statistic NUMERIC(20, 10),
    degrees_of_freedom INTEGER,
    p_value NUMERIC(16, 12),
    effect_size NUMERIC(20, 10),
    sample_size BIGINT,

    decision decision_type,
    interpretation TEXT,

    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_sample_size
        CHECK (sample_size IS NULL OR sample_size > 0),

    CONSTRAINT valid_p_value
        CHECK (
            p_value IS NULL OR
            (p_value >= 0 AND p_value <= 1)
        ),

    CONSTRAINT valid_degrees_of_freedom
        CHECK (
            degrees_of_freedom IS NULL OR
            degrees_of_freedom >= 0
        ),

    CONSTRAINT completed_analysis_consistency
        CHECK (
            status <> 'EXECUTED'
            OR (
                statistic IS NOT NULL
                AND p_value IS NOT NULL
                AND sample_size IS NOT NULL
                AND decision IS NOT NULL
                AND executed_at IS NOT NULL
            )
        )
);

-- ============================================================
-- 3. GOODNESS-OF-FIT OBSERVATIONS
-- ============================================================

CREATE TABLE goodness_of_fit_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_id BIGINT NOT NULL
        REFERENCES statistical_analyses(analysis_id)
        ON DELETE CASCADE,

    category_name VARCHAR(100) NOT NULL,
    observed_count BIGINT NOT NULL,
    expected_count NUMERIC(20, 6) NOT NULL,

    CONSTRAINT valid_observed_count
        CHECK (observed_count >= 0),

    CONSTRAINT valid_expected_count
        CHECK (expected_count > 0),

    CONSTRAINT unique_gof_category
        UNIQUE (analysis_id, category_name)
);

-- ============================================================
-- 4. CONTINGENCY TABLE OBSERVATIONS
-- ============================================================

CREATE TABLE contingency_observations (
    cell_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_id BIGINT NOT NULL
        REFERENCES statistical_analyses(analysis_id)
        ON DELETE CASCADE,

    row_category VARCHAR(100) NOT NULL,
    column_category VARCHAR(100) NOT NULL,

    observed_count BIGINT NOT NULL,

    CONSTRAINT valid_cell_count
        CHECK (observed_count >= 0),

    CONSTRAINT unique_contingency_cell
        UNIQUE (
            analysis_id,
            row_category,
            column_category
        )
);

-- ============================================================
-- 5. PROPORTION OBSERVATIONS
-- ============================================================

CREATE TABLE proportion_observations (
    proportion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_id BIGINT NOT NULL
        REFERENCES statistical_analyses(analysis_id)
        ON DELETE CASCADE,

    group_name VARCHAR(100) NOT NULL,

    successes BIGINT NOT NULL,
    trials BIGINT NOT NULL,

    CONSTRAINT valid_proportion_counts
        CHECK (
            trials > 0
            AND successes >= 0
            AND successes <= trials
        ),

    CONSTRAINT unique_proportion_group
        UNIQUE (analysis_id, group_name)
);

CREATE TABLE proportion_hypotheses (
    analysis_id BIGINT PRIMARY KEY
        REFERENCES statistical_analyses(analysis_id)
        ON DELETE CASCADE,

    hypothesized_proportion NUMERIC(12, 10),

    CONSTRAINT valid_hypothesized_proportion
        CHECK (
            hypothesized_proportion IS NULL
            OR (
                hypothesized_proportion > 0
                AND hypothesized_proportion < 1
            )
        )
);

-- ============================================================
-- 6. INDEXES
-- ============================================================

CREATE INDEX idx_analysis_experiment_status
    ON statistical_analyses(experiment_id, status);

CREATE INDEX idx_analysis_test_category
    ON statistical_analyses(test_category);

CREATE INDEX idx_gof_analysis
    ON goodness_of_fit_observations(analysis_id);

CREATE INDEX idx_contingency_analysis
    ON contingency_observations(analysis_id);

CREATE INDEX idx_proportion_analysis
    ON proportion_observations(analysis_id);

CREATE INDEX idx_experiments_created
    ON experiments(created_at DESC);

-- ============================================================
-- 7. NORMAL DISTRIBUTION UPPER-TAIL APPROXIMATION
-- ============================================================

CREATE OR REPLACE FUNCTION normal_upper_tail(
    z DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN z < 0 THEN 1.0 - normal_upper_tail(-z)
        WHEN z = 0 THEN 0.5
        ELSE
            (
                EXP(-0.5 * z * z) /
                SQRT(2.0 * PI())
            ) *
            (
                1.0 / (
                    z + 0.2316419
                )
            ) *
            (
                0.319381530
                + (-0.356563782) /
                    (z + 0.2316419)
                + 1.781477937 /
                    POWER(z + 0.2316419, 2)
                - 1.821255978 /
                    POWER(z + 0.2316419, 3)
                + 1.330274429 /
                    POWER(z + 0.2316419, 4)
            )
    END;
$$;

CREATE OR REPLACE FUNCTION normal_two_sided_p(
    z DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT LEAST(
        1.0,
        GREATEST(
            0.0,
            2.0 * normal_upper_tail(ABS(z))
        )
    );
$$;

-- ============================================================
-- 8. CHI-SQUARE UPPER-TAIL APPROXIMATION
-- ============================================================

CREATE OR REPLACE FUNCTION chi_square_approx_p(
    chi_stat DOUBLE PRECISION,
    df INTEGER
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN chi_stat < 0 OR df <= 0 THEN NULL
        WHEN chi_stat = 0 THEN 1.0
        ELSE
            normal_two_sided_p(
                SQRT(2.0 * chi_stat)
            )
    END;
$$;

-- ============================================================
-- 9. WILSON-HILFERTY CHI-SQUARE APPROXIMATION
-- ============================================================

CREATE OR REPLACE FUNCTION chi_square_p_value(
    chi_stat DOUBLE PRECISION,
    df INTEGER
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN chi_stat < 0 OR df <= 0 THEN NULL
        WHEN chi_stat = 0 THEN 1.0
        ELSE
            normal_upper_tail(
                (
                    POWER(
                        chi_stat / df,
                        1.0 / 3.0
                    )
                    -
                    (
                        1.0 - 2.0 / (9.0 * df)
                    )
                )
                /
                SQRT(2.0 / (9.0 * df))
            )
    END;
$$;

-- ============================================================
-- 10. ANALYSIS VALIDATION TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION validate_analysis_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'EXECUTED' THEN
        IF NEW.statistic IS NULL
           OR NEW.p_value IS NULL
           OR NEW.sample_size IS NULL
           OR NEW.decision IS NULL THEN

            RAISE EXCEPTION
                'Executed analyses require complete statistical results.';
        END IF;

        IF NEW.executed_at IS NULL THEN
            NEW.executed_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    IF NEW.p_value IS NOT NULL
       AND (NEW.p_value < 0 OR NEW.p_value > 1) THEN

        RAISE EXCEPTION 'P-value must be between zero and one.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_analysis
BEFORE INSERT OR UPDATE
ON statistical_analyses
FOR EACH ROW
EXECUTE FUNCTION validate_analysis_transition();

-- ============================================================
-- 11. GOODNESS-OF-FIT EXECUTION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_goodness_of_fit(
    p_analysis_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_alpha NUMERIC;
    v_observed_total BIGINT;
    v_expected_total NUMERIC;
    v_categories INTEGER;
    v_statistic DOUBLE PRECISION;
    v_df INTEGER;
    v_p DOUBLE PRECISION;
BEGIN
    SELECT e.alpha
    INTO v_alpha
    FROM statistical_analyses a
    JOIN experiments e
        ON e.experiment_id = a.experiment_id
    WHERE a.analysis_id = p_analysis_id
      AND a.test_category = 'GOODNESS_OF_FIT'
    FOR UPDATE OF a;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Goodness-of-fit analysis not found.';
    END IF;

    SELECT
        COALESCE(SUM(observed_count), 0),
        COALESCE(SUM(expected_count), 0),
        COUNT(*)
    INTO
        v_observed_total,
        v_expected_total,
        v_categories
    FROM goodness_of_fit_observations
    WHERE analysis_id = p_analysis_id;

    IF v_categories < 2 OR v_observed_total = 0 THEN
        RAISE EXCEPTION
            'At least two categories and positive sample size required.';
    END IF;

    IF ABS(v_observed_total - v_expected_total) > 0.000001 THEN
        RAISE EXCEPTION
            'Expected and observed totals must match.';
    END IF;

    SELECT SUM(
        POWER(observed_count - expected_count, 2)
        / expected_count
    )
    INTO v_statistic
    FROM goodness_of_fit_observations
    WHERE analysis_id = p_analysis_id;

    v_df := v_categories - 1;

    v_p := chi_square_p_value(v_statistic, v_df);

    IF v_p IS NULL THEN
        RAISE EXCEPTION 'Could not calculate chi-square p-value.';
    END IF;

    UPDATE statistical_analyses
    SET
        status = 'EXECUTED',
        statistic = v_statistic,
        degrees_of_freedom = v_df,
        p_value = v_p,
        sample_size = v_observed_total,
        decision = CASE
            WHEN v_p < v_alpha THEN 'REJECT_NULL'
            ELSE 'FAIL_TO_REJECT_NULL'
        END,
        interpretation = CASE
            WHEN v_p < v_alpha
                THEN 'Observed distribution differs significantly.'
            ELSE
                'Insufficient evidence of distribution difference.'
        END
    WHERE analysis_id = p_analysis_id;
END;
$$;

-- ============================================================
-- 12. INDEPENDENCE TEST EXECUTION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_independence_test(
    p_analysis_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_alpha NUMERIC;
    v_rows INTEGER;
    v_cols INTEGER;
    v_total BIGINT;
    v_df INTEGER;
    v_statistic DOUBLE PRECISION;
    v_p DOUBLE PRECISION;
    v_min_expected DOUBLE PRECISION;
BEGIN
    SELECT e.alpha
    INTO v_alpha
    FROM statistical_analyses a
    JOIN experiments e
        ON e.experiment_id = a.experiment_id
    WHERE a.analysis_id = p_analysis_id
      AND a.test_category = 'INDEPENDENCE'
    FOR UPDATE OF a;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Independence analysis not found.';
    END IF;

    SELECT
        COUNT(DISTINCT row_category),
        COUNT(DISTINCT column_category),
        COALESCE(SUM(observed_count), 0)
    INTO v_rows, v_cols, v_total
    FROM contingency_observations
    WHERE analysis_id = p_analysis_id;

    IF v_rows < 2 OR v_cols < 2 OR v_total = 0 THEN
        RAISE EXCEPTION
            'Contingency table requires at least 2x2 categories.';
    END IF;

    -- A complete Cartesian grid is required. Missing cells
    -- must be explicitly stored with observed_count = 0.
    IF (
        SELECT COUNT(*)
        FROM contingency_observations
        WHERE analysis_id = p_analysis_id
    ) <> v_rows * v_cols THEN
        RAISE EXCEPTION
            'Contingency table contains missing category combinations.';
    END IF;

    WITH row_totals AS (
        SELECT
            row_category,
            SUM(observed_count) AS row_total
        FROM contingency_observations
        WHERE analysis_id = p_analysis_id
        GROUP BY row_category
    ),
    column_totals AS (
        SELECT
            column_category,
            SUM(observed_count) AS column_total
        FROM contingency_observations
        WHERE analysis_id = p_analysis_id
        GROUP BY column_category
    ),
    expected_cells AS (
        SELECT
            c.observed_count,
            r.row_total * col.column_total::DOUBLE PRECISION
                / v_total AS expected_count
        FROM contingency_observations c
        JOIN row_totals r
            USING (row_category)
        JOIN column_totals col
            USING (column_category)
        WHERE c.analysis_id = p_analysis_id
    )
    SELECT
        SUM(
            POWER(observed_count - expected_count, 2)
            / expected_count
        ),
        MIN(expected_count)
    INTO v_statistic, v_min_expected
    FROM expected_cells
    WHERE expected_count > 0;

    IF v_min_expected IS NULL THEN
        RAISE EXCEPTION 'Invalid expected cell frequencies.';
    END IF;

    v_df := (v_rows - 1) * (v_cols - 1);

    v_p := chi_square_p_value(v_statistic, v_df);

    UPDATE statistical_analyses
    SET
        status = 'EXECUTED',
        statistic = v_statistic,
        degrees_of_freedom = v_df,
        p_value = v_p,
        sample_size = v_total,
        effect_size = SQRT(
            v_statistic /
            (
                v_total *
                LEAST(v_rows - 1, v_cols - 1)
            )
        ),
        decision = CASE
            WHEN v_p < v_alpha THEN 'REJECT_NULL'
            ELSE 'FAIL_TO_REJECT_NULL'
        END,
        interpretation =
            CASE
                WHEN v_p < v_alpha
                    THEN 'Evidence of association.'
                ELSE
                    'Insufficient evidence of association.'
            END
            ||
            CASE
                WHEN v_min_expected < 5
                    THEN ' Expected frequency below five.'
                ELSE ''
            END
    WHERE analysis_id = p_analysis_id;
END;
$$;

-- ============================================================
-- 13. ONE-SAMPLE PROPORTION TEST PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_one_proportion_test(
    p_analysis_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_alpha NUMERIC;
    v_p0 NUMERIC;
    v_successes BIGINT;
    v_trials BIGINT;
    v_observed DOUBLE PRECISION;
    v_z DOUBLE PRECISION;
    v_p DOUBLE PRECISION;
BEGIN
    SELECT
        e.alpha,
        h.hypothesized_proportion,
        p.successes,
        p.trials
    INTO
        v_alpha,
        v_p0,
        v_successes,
        v_trials
    FROM statistical_analyses a
    JOIN experiments e
        ON e.experiment_id = a.experiment_id
    JOIN proportion_hypotheses h
        ON h.analysis_id = a.analysis_id
    JOIN proportion_observations p
        ON p.analysis_id = a.analysis_id
    WHERE a.analysis_id = p_analysis_id
      AND a.test_category = 'ONE_PROPORTION'
    FOR UPDATE OF a;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'One-proportion analysis not found.';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM proportion_observations
        WHERE analysis_id = p_analysis_id
    ) <> 1 THEN
        RAISE EXCEPTION
            'One-proportion test requires exactly one observation group.';
    END IF;

    v_observed := v_successes::DOUBLE PRECISION / v_trials;

    v_z := (
        v_observed - v_p0
    ) / SQRT(
        v_p0 * (1 - v_p0) / v_trials
    );

    v_p := normal_two_sided_p(v_z);

    UPDATE statistical_analyses
    SET
        status = 'EXECUTED',
        statistic = v_z,
        degrees_of_freedom = 0,
        p_value = v_p,
        sample_size = v_trials,
        effect_size = v_observed - v_p0,
        decision = CASE
            WHEN v_p < v_alpha THEN 'REJECT_NULL'
            ELSE 'FAIL_TO_REJECT_NULL'
        END,
        interpretation = CASE
            WHEN v_p < v_alpha
                THEN 'Observed proportion differs significantly.'
            ELSE
                'Insufficient evidence of a proportion difference.'
        END
    WHERE analysis_id = p_analysis_id;
END;
$$;

-- ============================================================
-- 14. TWO-SAMPLE PROPORTION TEST PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_two_proportion_test(
    p_analysis_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_alpha NUMERIC;
    v_x1 BIGINT;
    v_n1 BIGINT;
    v_x2 BIGINT;
    v_n2 BIGINT;
    v_p1 DOUBLE PRECISION;
    v_p2 DOUBLE PRECISION;
    v_pooled DOUBLE PRECISION;
    v_z DOUBLE PRECISION;
    v_p DOUBLE PRECISION;
BEGIN
    SELECT e.alpha
    INTO v_alpha
    FROM statistical_analyses a
    JOIN experiments e
        ON e.experiment_id = a.experiment_id
    WHERE a.analysis_id = p_analysis_id
      AND a.test_category = 'TWO_PROPORTION'
    FOR UPDATE OF a;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Two-proportion analysis not found.';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM proportion_observations
        WHERE analysis_id = p_analysis_id
    ) <> 2 THEN
        RAISE EXCEPTION
            'Two-proportion test requires exactly two groups.';
    END IF;

    SELECT successes, trials
    INTO v_x1, v_n1
    FROM proportion_observations
    WHERE analysis_id = p_analysis_id
    ORDER BY proportion_id
    LIMIT 1;

    SELECT successes, trials
    INTO v_x2, v_n2
    FROM proportion_observations
    WHERE analysis_id = p_analysis_id
    ORDER BY proportion_id
    OFFSET 1 LIMIT 1;

    v_p1 := v_x1::DOUBLE PRECISION / v_n1;
    v_p2 := v_x2::DOUBLE PRECISION / v_n2;

    v_pooled :=
        (v_x1 + v_x2)::DOUBLE PRECISION /
        (v_n1 + v_n2);

    IF v_pooled = 0 OR v_pooled = 1 THEN
        RAISE EXCEPTION 'Pooled variance is zero.';
    END IF;

    v_z := (v_p1 - v_p2) / SQRT(
        v_pooled * (1 - v_pooled) *
        (1.0 / v_n1 + 1.0 / v_n2)
    );

    v_p := normal_two_sided_p(v_z);

    UPDATE statistical_analyses
    SET
        status = 'EXECUTED',
        statistic = v_z,
        degrees_of_freedom = 0,
        p_value = v_p,
        sample_size = v_n1 + v_n2,
        effect_size = v_p1 - v_p2,
        decision = CASE
            WHEN v_p < v_alpha THEN 'REJECT_NULL'
            ELSE 'FAIL_TO_REJECT_NULL'
        END,
        interpretation = CASE
            WHEN v_p < v_alpha
                THEN 'Population proportions differ significantly.'
            ELSE
                'Insufficient evidence of a difference.'
        END
    WHERE analysis_id = p_analysis_id;
END;
$$;

-- ============================================================
-- 15. RESULT REPORTING VIEW
-- ============================================================

CREATE OR REPLACE VIEW analysis_report AS
SELECT
    a.analysis_id,
    e.experiment_name,
    e.owner_name,
    a.test_category,
    a.null_hypothesis,
    a.alternative_hypothesis,
    e.alpha,
    a.statistic,
    a.degrees_of_freedom,
    a.p_value,
    a.effect_size,
    a.sample_size,
    a.decision,
    a.status,
    a.interpretation,
    a.executed_at
FROM statistical_analyses a
JOIN experiments e
    ON e.experiment_id = a.experiment_id;

-- ============================================================
-- 16. SAMPLE EXPERIMENTS
-- ============================================================

INSERT INTO experiments (
    experiment_name,
    description,
    owner_name,
    alpha
)
VALUES
(
    'Product Distribution Analysis',
    'Testing whether observed product categories follow an expected distribution.',
    'Research Team',
    0.05
),
(
    'Training Preference Study',
    'Testing the association between training method and employee preference.',
    'Analytics Department',
    0.05
),
(
    'Service Acceptance Analysis',
    'Testing whether service acceptance differs from a target proportion.',
    'Quality Department',
    0.05
),
(
    'Campaign Conversion Comparison',
    'Comparing conversion proportions between two campaign groups.',
    'Marketing Analytics',
    0.05
);

-- ============================================================
-- 17. GOODNESS-OF-FIT SAMPLE
-- ============================================================

INSERT INTO statistical_analyses (
    experiment_id,
    test_category,
    null_hypothesis,
    alternative_hypothesis
)
SELECT
    experiment_id,
    'GOODNESS_OF_FIT',
    'Observed product categories follow the specified distribution.',
    'Observed product categories differ from the specified distribution.'
FROM experiments
WHERE experiment_name = 'Product Distribution Analysis';

INSERT INTO goodness_of_fit_observations (
    analysis_id,
    category_name,
    observed_count,
    expected_count
)
SELECT
    a.analysis_id,
    x.category_name,
    x.observed_count,
    x.expected_count
FROM statistical_analyses a
CROSS JOIN (
    VALUES
        ('Category A', 48::BIGINT, 50::NUMERIC),
        ('Category B', 52::BIGINT, 50::NUMERIC),
        ('Category C', 45::BIGINT, 50::NUMERIC),
        ('Category D', 55::BIGINT, 50::NUMERIC)
) AS x(category_name, observed_count, expected_count)
WHERE a.test_category = 'GOODNESS_OF_FIT';

-- ============================================================
-- 18. INDEPENDENCE SAMPLE
-- ============================================================

INSERT INTO statistical_analyses (
    experiment_id,
    test_category,
    null_hypothesis,
    alternative_hypothesis
)
SELECT
    experiment_id,
    'INDEPENDENCE',
    'Training method and preference are independent.',
    'Training method and preference are associated.'
FROM experiments
WHERE experiment_name = 'Training Preference Study';

INSERT INTO contingency_observations (
    analysis_id,
    row_category,
    column_category,
    observed_count
)
SELECT
    a.analysis_id,
    x.row_category,
    x.column_category,
    x.observed_count
FROM statistical_analyses a
CROSS JOIN (
    VALUES
        ('Online', 'Preferred', 40),
        ('Online', 'Not Preferred', 20),
        ('Classroom', 'Preferred', 15),
        ('Classroom', 'Not Preferred', 45)
) AS x(row_category, column_category, observed_count)
WHERE a.test_category = 'INDEPENDENCE';

-- ============================================================
-- 19. ONE-PROPORTION SAMPLE
-- ============================================================

INSERT INTO statistical_analyses (
    experiment_id,
    test_category,
    null_hypothesis,
    alternative_hypothesis
)
SELECT
    experiment_id,
    'ONE_PROPORTION',
    'Service acceptance proportion equals 0.50.',
    'Service acceptance proportion differs from 0.50.'
FROM experiments
WHERE experiment_name = 'Service Acceptance Analysis';

INSERT INTO proportion_hypotheses (
    analysis_id,
    hypothesized_proportion
)
SELECT analysis_id, 0.50
FROM statistical_analyses
WHERE test_category = 'ONE_PROPORTION';

INSERT INTO proportion_observations (
    analysis_id,
    group_name,
    successes,
    trials
)
SELECT
    analysis_id,
    'Service Acceptance',
    120,
    200
FROM statistical_analyses
WHERE test_category = 'ONE_PROPORTION';

-- ============================================================
-- 20. TWO-PROPORTION SAMPLE
-- ============================================================

INSERT INTO statistical_analyses (
    experiment_id,
    test_category,
    null_hypothesis,
    alternative_hypothesis
)
SELECT
    experiment_id,
    'TWO_PROPORTION',
    'Campaign A and B have equal conversion proportions.',
    'Campaign A and B have different conversion proportions.'
FROM experiments
WHERE experiment_name = 'Campaign Conversion Comparison';

INSERT INTO proportion_observations (
    analysis_id,
    group_name,
    successes,
    trials
)
SELECT
    a.analysis_id,
    x.group_name,
    x.successes,
    x.trials
FROM statistical_analyses a
CROSS JOIN (
    VALUES
        ('Campaign A', 140::BIGINT, 200::BIGINT),
        ('Campaign B', 110::BIGINT, 200::BIGINT)
) AS x(group_name, successes, trials)
WHERE a.test_category = 'TWO_PROPORTION';

-- ============================================================
-- 21. TRANSACTIONAL WORKFLOW EXECUTION
-- ============================================================

DO $$
DECLARE
    v_id BIGINT;
BEGIN
    SELECT analysis_id INTO v_id
    FROM statistical_analyses
    WHERE test_category = 'GOODNESS_OF_FIT'
    ORDER BY analysis_id
    LIMIT 1;

    CALL execute_goodness_of_fit(v_id);

    SELECT analysis_id INTO v_id
    FROM statistical_analyses
    WHERE test_category = 'INDEPENDENCE'
    ORDER BY analysis_id
    LIMIT 1;

    CALL execute_independence_test(v_id);

    SELECT analysis_id INTO v_id
    FROM statistical_analyses
    WHERE test_category = 'ONE_PROPORTION'
    ORDER BY analysis_id
    LIMIT 1;

    CALL execute_one_proportion_test(v_id);

    SELECT analysis_id INTO v_id
    FROM statistical_analyses
    WHERE test_category = 'TWO_PROPORTION'
    ORDER BY analysis_id
    LIMIT 1;

    CALL execute_two_proportion_test(v_id);
END;
$$;

COMMIT;

-- ============================================================
-- 22. RETRIEVAL QUERIES
-- ============================================================

SELECT *
FROM analysis_report
ORDER BY analysis_id;

-- ============================================================
-- 23. AGGREGATION REPORT
-- ============================================================

SELECT
    test_category,
    COUNT(*) AS total_analyses,
    COUNT(*) FILTER (
        WHERE decision = 'REJECT_NULL'
    ) AS rejected_null_hypotheses,
    COUNT(*) FILTER (
        WHERE decision = 'FAIL_TO_REJECT_NULL'
    ) AS non_rejected_hypotheses,
    AVG(p_value) AS average_p_value,
    AVG(effect_size) AS average_effect_size
FROM statistical_analyses
GROUP BY test_category
ORDER BY test_category;

-- ============================================================
-- 24. SIGNIFICANCE REPORT
-- ============================================================

SELECT
    experiment_name,
    test_category,
    statistic,
    p_value,
    alpha,
    decision,
    interpretation
FROM analysis_report
WHERE status = 'EXECUTED'
ORDER BY p_value ASC;

-- ============================================================
-- 25. EXPECTED FREQUENCY VALIDATION
-- ============================================================

SELECT
    analysis_id,
    COUNT(*) AS categories,
    MIN(expected_count) AS minimum_expected,
    SUM(observed_count) AS observed_total,
    SUM(expected_count) AS expected_total,
    BOOL_AND(expected_count >= 5) AS all_expected_at_least_five
FROM goodness_of_fit_observations
GROUP BY analysis_id;

-- ============================================================
-- 26. CONTINGENCY TABLE VALIDATION
-- ============================================================

WITH totals AS (
    SELECT
        analysis_id,
        row_category,
        column_category,
        observed_count,
        SUM(observed_count) OVER (
            PARTITION BY analysis_id, row_category
        ) AS row_total,
        SUM(observed_count) OVER (
            PARTITION BY analysis_id, column_category
        ) AS column_total,
        SUM(observed_count) OVER (
            PARTITION BY analysis_id
        ) AS grand_total
    FROM contingency_observations
)
SELECT
    analysis_id,
    row_category,
    column_category,
    observed_count,
    ROUND(
        (
            row_total::NUMERIC * column_total
            / NULLIF(grand_total, 0)
        ),
        4
    ) AS expected_frequency
FROM totals
ORDER BY analysis_id, row_category, column_category;

-- ============================================================
-- 27. PROPORTION VALIDATION
-- ============================================================

SELECT
    analysis_id,
    group_name,
    successes,
    trials,
    ROUND(
        successes::NUMERIC / trials,
        4
    ) AS observed_proportion
FROM proportion_observations
ORDER BY analysis_id, proportion_id;

-- ============================================================
-- 28. ELIGIBILITY AND QUALITY CONTROL
-- ============================================================

SELECT
    a.analysis_id,
    a.test_category,
    a.status,
    CASE
        WHEN a.status <> 'EXECUTED'
            THEN 'NOT COMPLETED'
        WHEN a.p_value IS NULL
            THEN 'INVALID RESULT'
        WHEN a.decision = 'REJECT_NULL'
            THEN 'SIGNIFICANT'
        ELSE 'NOT SIGNIFICANT'
    END AS evaluation_status
FROM statistical_analyses a
ORDER BY a.analysis_id;

-- ============================================================
-- 29. FAILURE CASE EXAMPLES
-- ============================================================

-- The following examples are intentionally excluded from
-- automatic execution because they must raise exceptions.

-- Invalid alpha:
-- INSERT INTO experiments
-- (experiment_name, description, owner_name, alpha)
-- VALUES ('Invalid', 'Invalid significance level', 'Tester', 1.5);

-- Negative observed frequency:
-- INSERT INTO goodness_of_fit_observations
-- (analysis_id, category_name, observed_count, expected_count)
-- VALUES (1, 'Invalid category', -5, 10);

-- Successes greater than trials:
-- INSERT INTO proportion_observations
-- (analysis_id, group_name, successes, trials)
-- VALUES (3, 'Invalid group', 120, 100);

-- Missing contingency cells are rejected by the
-- independence execution procedure.

-- ============================================================
-- 30. COMPLETED ANALYSIS COUNTS
-- ============================================================

SELECT
    status,
    COUNT(*) AS analysis_count
FROM statistical_analyses
GROUP BY status
ORDER BY status;
