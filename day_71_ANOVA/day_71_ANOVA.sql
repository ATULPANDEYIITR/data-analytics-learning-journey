-- ============================================================
-- ANOVA STATISTICAL EXPERIMENT MANAGEMENT SYSTEM
-- PostgreSQL 14+
--
-- Implements:
--   One-way ANOVA
--   Balanced two-way ANOVA
--   Main effects and interaction
--   Experimental observations
--   Assumption diagnostics
--   Variance homogeneity testing
--   Residual normality diagnostic
--   Pairwise post-hoc comparisons
--   Holm correction
--   Effect sizes
--   Experiment lifecycle
--   Statistical reporting
--
-- Statistical p-values use the regularized incomplete beta
-- function implemented below.
--
-- Run using psql:
--   psql -v ON_ERROR_STOP=1 -f anova.sql
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS anova;

SET search_path TO anova, public;


-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE experiment_status AS ENUM (
    'DRAFT',
    'COLLECTING',
    'READY',
    'ANALYZING',
    'COMPLETED',
    'FAILED',
    'ARCHIVED'
);

CREATE TYPE analysis_type AS ENUM (
    'ONE_WAY',
    'TWO_WAY'
);

CREATE TYPE review_status AS ENUM (
    'NOT_RUN',
    'PASS',
    'WARNING',
    'FAIL'
);

CREATE TYPE observation_state AS ENUM (
    'VALID',
    'EXCLUDED'
);


-- ============================================================
-- 2. EXPERIMENTS
-- ============================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code VARCHAR(40) NOT NULL UNIQUE,

    experiment_name VARCHAR(200) NOT NULL,

    description TEXT,

    analysis_method analysis_type NOT NULL,

    status experiment_status NOT NULL DEFAULT 'DRAFT',

    significance_level NUMERIC(5,4) NOT NULL DEFAULT 0.05,

    created_by VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_significance_level
        CHECK (
            significance_level > 0
            AND significance_level < 0.5
        ),

    CONSTRAINT valid_experiment_name
        CHECK (length(trim(experiment_name)) > 0)
);


-- ============================================================
-- 3. FACTOR DEFINITIONS
-- ============================================================

CREATE TABLE factors (
    factor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    factor_name VARCHAR(100) NOT NULL,

    factor_role VARCHAR(20) NOT NULL,

    CONSTRAINT valid_factor_role
        CHECK (factor_role IN ('FACTOR_A', 'FACTOR_B')),

    UNIQUE (experiment_id, factor_name),

    UNIQUE (experiment_id, factor_role)
);


CREATE TABLE factor_levels (
    level_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    factor_id BIGINT NOT NULL
        REFERENCES factors(factor_id)
        ON DELETE CASCADE,

    level_name VARCHAR(100) NOT NULL,

    display_order INTEGER NOT NULL DEFAULT 1,

    UNIQUE (factor_id, level_name),

    UNIQUE (factor_id, display_order)
);


-- ============================================================
-- 4. EXPERIMENTAL OBSERVATIONS
-- ============================================================

CREATE TABLE observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    factor_a_level_id BIGINT NOT NULL
        REFERENCES factor_levels(level_id),

    factor_b_level_id BIGINT
        REFERENCES factor_levels(level_id),

    subject_code VARCHAR(100),

    response_value DOUBLE PRECISION NOT NULL,

    state observation_state NOT NULL DEFAULT 'VALID',

    exclusion_reason TEXT,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT finite_response
        CHECK (
            response_value > '-Infinity'::DOUBLE PRECISION
            AND response_value < 'Infinity'::DOUBLE PRECISION
            AND response_value <> 'NaN'::DOUBLE PRECISION
        ),

    CONSTRAINT valid_exclusion
        CHECK (
            (state = 'VALID' AND exclusion_reason IS NULL)
            OR
            (state = 'EXCLUDED' AND exclusion_reason IS NOT NULL)
        ),

    UNIQUE (experiment_id, subject_code)
);


-- ============================================================
-- 5. FACTOR-LEVEL INTEGRITY
-- ============================================================

CREATE OR REPLACE FUNCTION validate_observation_factors()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    a_factor_id BIGINT;
    b_factor_id BIGINT;
    a_experiment_id BIGINT;
    b_experiment_id BIGINT;
    expected_b BOOLEAN;
BEGIN
    SELECT factor_id
    INTO a_factor_id
    FROM factor_levels
    WHERE level_id = NEW.factor_a_level_id;

    IF a_factor_id IS NULL THEN
        RAISE EXCEPTION 'Invalid Factor A level.';
    END IF;

    SELECT experiment_id
    INTO a_experiment_id
    FROM factors
    WHERE factor_id = a_factor_id;

    IF a_experiment_id <> NEW.experiment_id THEN
        RAISE EXCEPTION
            'Factor A level belongs to another experiment.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM factors
        WHERE factor_id = a_factor_id
          AND factor_role = 'FACTOR_A'
    ) THEN
        RAISE EXCEPTION
            'Factor A level references the wrong factor role.';
    END IF;

    SELECT analysis_method = 'TWO_WAY'
    INTO expected_b
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF expected_b AND NEW.factor_b_level_id IS NULL THEN
        RAISE EXCEPTION
            'Two-way experiments require Factor B.';
    END IF;

    IF NOT expected_b AND NEW.factor_b_level_id IS NOT NULL THEN
        RAISE EXCEPTION
            'One-way experiments cannot use Factor B.';
    END IF;

    IF NEW.factor_b_level_id IS NOT NULL THEN

        SELECT factor_id
        INTO b_factor_id
        FROM factor_levels
        WHERE level_id = NEW.factor_b_level_id;

        IF b_factor_id IS NULL THEN
            RAISE EXCEPTION 'Invalid Factor B level.';
        END IF;

        SELECT experiment_id
        INTO b_experiment_id
        FROM factors
        WHERE factor_id = b_factor_id;

        IF b_experiment_id <> NEW.experiment_id THEN
            RAISE EXCEPTION
                'Factor B level belongs to another experiment.';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM factors
            WHERE factor_id = b_factor_id
              AND factor_role = 'FACTOR_B'
        ) THEN
            RAISE EXCEPTION
                'Factor B level references the wrong factor role.';
        END IF;

        IF a_factor_id = b_factor_id THEN
            RAISE EXCEPTION
                'Factor A and Factor B must be distinct.';
        END IF;
    END IF;

    IF (
        SELECT status
        FROM experiments
        WHERE experiment_id = NEW.experiment_id
    ) NOT IN ('DRAFT', 'COLLECTING') THEN
        RAISE EXCEPTION
            'Observations cannot be changed after collection closes.';
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER observation_factor_integrity
BEFORE INSERT OR UPDATE ON observations
FOR EACH ROW
EXECUTE FUNCTION validate_observation_factors();


-- ============================================================
-- 6. ANALYSIS RESULTS
-- ============================================================

CREATE TABLE analysis_runs (
    analysis_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    method analysis_type NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    run_status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',

    error_message TEXT,

    CONSTRAINT valid_run_status
        CHECK (
            run_status IN ('RUNNING', 'COMPLETED', 'FAILED')
        )
);


CREATE TABLE anova_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_run_id BIGINT NOT NULL
        REFERENCES analysis_runs(analysis_run_id)
        ON DELETE CASCADE,

    source_name VARCHAR(100) NOT NULL,

    degrees_of_freedom INTEGER NOT NULL,

    sum_squares DOUBLE PRECISION NOT NULL,

    mean_square DOUBLE PRECISION NOT NULL,

    f_statistic DOUBLE PRECISION,

    p_value DOUBLE PRECISION,

    eta_squared DOUBLE PRECISION,

    omega_squared DOUBLE PRECISION,

    CONSTRAINT valid_df CHECK (degrees_of_freedom > 0),

    CONSTRAINT valid_p
        CHECK (
            p_value IS NULL
            OR (p_value >= 0 AND p_value <= 1)
        ),

    CONSTRAINT valid_effect_size
        CHECK (
            eta_squared IS NULL
            OR eta_squared BETWEEN 0 AND 1
        ),

    UNIQUE (analysis_run_id, source_name)
);


-- ============================================================
-- 7. ASSUMPTION DIAGNOSTICS
-- ============================================================

CREATE TABLE assumption_diagnostics (
    diagnostic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_run_id BIGINT NOT NULL
        REFERENCES analysis_runs(analysis_run_id)
        ON DELETE CASCADE,

    diagnostic_name VARCHAR(100) NOT NULL,

    statistic DOUBLE PRECISION,

    p_value DOUBLE PRECISION,

    status review_status NOT NULL,

    interpretation TEXT,

    UNIQUE (analysis_run_id, diagnostic_name),

    CHECK (
        p_value IS NULL
        OR p_value BETWEEN 0 AND 1
    )
);


-- ============================================================
-- 8. POST-HOC COMPARISONS
-- ============================================================

CREATE TABLE posthoc_comparisons (
    comparison_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    analysis_run_id BIGINT NOT NULL
        REFERENCES analysis_runs(analysis_run_id)
        ON DELETE CASCADE,

    group_a_level_id BIGINT NOT NULL
        REFERENCES factor_levels(level_id),

    group_b_level_id BIGINT NOT NULL
        REFERENCES factor_levels(level_id),

    method VARCHAR(50) NOT NULL,

    mean_difference DOUBLE PRECISION NOT NULL,

    test_statistic DOUBLE PRECISION,

    raw_p_value DOUBLE PRECISION NOT NULL,

    adjusted_p_value DOUBLE PRECISION NOT NULL,

    significant BOOLEAN NOT NULL,

    CHECK (group_a_level_id <> group_b_level_id),

    CHECK (raw_p_value BETWEEN 0 AND 1),

    CHECK (adjusted_p_value BETWEEN 0 AND 1),

    UNIQUE (
        analysis_run_id,
        group_a_level_id,
        group_b_level_id,
        method
    )
);


-- ============================================================
-- 9. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_observations_experiment
ON observations(experiment_id);

CREATE INDEX idx_observations_factor_a
ON observations(experiment_id, factor_a_level_id)
WHERE state = 'VALID';

CREATE INDEX idx_observations_factor_b
ON observations(experiment_id, factor_b_level_id)
WHERE state = 'VALID';

CREATE INDEX idx_analysis_runs_experiment
ON analysis_runs(experiment_id, started_at DESC);

CREATE INDEX idx_anova_results_run
ON anova_results(analysis_run_id);

CREATE INDEX idx_posthoc_run
ON posthoc_comparisons(analysis_run_id);

CREATE INDEX idx_diagnostics_run
ON assumption_diagnostics(analysis_run_id);


-- ============================================================
-- 10. INCOMPLETE EXPERIMENT VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_experiment(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    check_name TEXT,
    passed BOOLEAN,
    details TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    method analysis_type;
    a_count BIGINT;
    b_count BIGINT;
    observation_count BIGINT;
    cell_count BIGINT;
    minimum_replication BIGINT;
    maximum_replication BIGINT;
BEGIN
    SELECT analysis_method
    INTO method
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    SELECT count(*)
    INTO a_count
    FROM factors
    WHERE experiment_id = p_experiment_id
      AND factor_role = 'FACTOR_A';

    SELECT count(*)
    INTO b_count
    FROM factors
    WHERE experiment_id = p_experiment_id
      AND factor_role = 'FACTOR_B';

    SELECT count(*)
    INTO observation_count
    FROM observations
    WHERE experiment_id = p_experiment_id
      AND state = 'VALID';

    RETURN QUERY SELECT
        'factor_definitions'::TEXT,
        (
            a_count = 1
            AND (
                method = 'ONE_WAY'
                OR b_count = 1
            )
        ),
        format('Factor A definitions: %s; Factor B definitions: %s',
               a_count, b_count);

    RETURN QUERY SELECT
        'observation_count'::TEXT,
        observation_count >= 4,
        format('Valid observations: %s', observation_count);

    SELECT count(*),
           min(cell_n),
           max(cell_n)
    INTO cell_count, minimum_replication, maximum_replication
    FROM (
        SELECT count(*) AS cell_n
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id, factor_b_level_id
    ) AS cell_summary;

    IF method = 'TWO_WAY' THEN
        RETURN QUERY SELECT
            'balanced_factorial_design'::TEXT,
            (
                cell_count >= 4
                AND minimum_replication >= 2
                AND minimum_replication = maximum_replication
            ),
            format(
                'Cells: %s; minimum replication: %s; maximum replication: %s',
                cell_count,
                minimum_replication,
                maximum_replication
            );
    END IF;
END;
$$;


-- ============================================================
-- 11. REGULARIZED INCOMPLETE BETA FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION beta_continued_fraction(
    a DOUBLE PRECISION,
    b DOUBLE PRECISION,
    x DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    qab DOUBLE PRECISION := a + b;
    qap DOUBLE PRECISION := a + 1;
    qam DOUBLE PRECISION := a - 1;
    c DOUBLE PRECISION := 1;
    d DOUBLE PRECISION;
    h DOUBLE PRECISION;
    aa DOUBLE PRECISION;
    delta DOUBLE PRECISION;
    m INTEGER;
    m2 INTEGER;
BEGIN
    d := 1 - qab * x / qap;

    IF abs(d) < 1e-30 THEN d := 1e-30; END IF;

    d := 1 / d;
    h := d;

    FOR m IN 1..300 LOOP
        m2 := 2 * m;

        aa := m * (b - m) * x
            / ((qam + m2) * (a + m2));

        d := 1 + aa * d;
        IF abs(d) < 1e-30 THEN d := 1e-30; END IF;

        c := 1 + aa / c;
        IF abs(c) < 1e-30 THEN c := 1e-30; END IF;

        d := 1 / d;
        h := h * d * c;

        aa := -(a + m) * (qab + m) * x
            / ((a + m2) * (qap + m2));

        d := 1 + aa * d;
        IF abs(d) < 1e-30 THEN d := 1e-30; END IF;

        c := 1 + aa / c;
        IF abs(c) < 1e-30 THEN c := 1e-30; END IF;

        d := 1 / d;

        delta := d * c;
        h := h * delta;

        IF abs(delta - 1) < 3e-14 THEN
            EXIT;
        END IF;
    END LOOP;

    RETURN h;
END;
$$;


CREATE OR REPLACE FUNCTION regularized_beta(
    x DOUBLE PRECISION,
    a DOUBLE PRECISION,
    b DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    front DOUBLE PRECISION;
BEGIN
    IF a <= 0 OR b <= 0 THEN
        RAISE EXCEPTION 'Invalid beta parameters.';
    END IF;

    IF x <= 0 THEN RETURN 0; END IF;
    IF x >= 1 THEN RETURN 1; END IF;

    front := exp(
        lgamma(a + b)
        - lgamma(a)
        - lgamma(b)
        + a * ln(x)
        + b * ln(1 - x)
    );

    IF x < (a + 1) / (a + b + 2) THEN
        RETURN front
            * beta_continued_fraction(a, b, x)
            / a;
    END IF;

    RETURN 1 - front
        * beta_continued_fraction(b, a, 1 - x)
        / b;
END;
$$;


CREATE OR REPLACE FUNCTION f_survival(
    f_value DOUBLE PRECISION,
    df1 INTEGER,
    df2 INTEGER
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF df1 <= 0 OR df2 <= 0 THEN
        RAISE EXCEPTION 'Invalid F degrees of freedom.';
    END IF;

    IF f_value <= 0 THEN RETURN 1; END IF;

    IF f_value = 'Infinity'::DOUBLE PRECISION THEN
        RETURN 0;
    END IF;

    RETURN regularized_beta(
        df2 / (df2 + df1 * f_value),
        df2 / 2.0,
        df1 / 2.0
    );
END;
$$;


CREATE OR REPLACE FUNCTION t_two_tailed_p(
    t_value DOUBLE PRECISION,
    degrees_of_freedom DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    ib DOUBLE PRECISION;
BEGIN
    IF degrees_of_freedom <= 0 THEN
        RAISE EXCEPTION 'Invalid t degrees of freedom.';
    END IF;

    IF t_value = 'Infinity'::DOUBLE PRECISION
       OR t_value = '-Infinity'::DOUBLE PRECISION THEN
        RETURN 0;
    END IF;

    ib := regularized_beta(
        degrees_of_freedom
        / (degrees_of_freedom + t_value * t_value),
        degrees_of_freedom / 2,
        0.5
    );

    RETURN LEAST(1.0, ib);
END;
$$;


-- ============================================================
-- 12. ONE-WAY ANOVA FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_one_way_anova(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    source_name TEXT,
    degrees_of_freedom INTEGER,
    sum_squares DOUBLE PRECISION,
    mean_square DOUBLE PRECISION,
    f_statistic DOUBLE PRECISION,
    p_value DOUBLE PRECISION,
    eta_squared DOUBLE PRECISION,
    omega_squared DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    k INTEGER;
    n INTEGER;
    df_between INTEGER;
    df_within INTEGER;
    grand_mean DOUBLE PRECISION;
    ss_between DOUBLE PRECISION;
    ss_within DOUBLE PRECISION;
    ms_between DOUBLE PRECISION;
    ms_within DOUBLE PRECISION;
    f_value DOUBLE PRECISION;
    p DOUBLE PRECISION;
    total_ss DOUBLE PRECISION;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM experiments
        WHERE experiment_id = p_experiment_id
          AND analysis_method = 'ONE_WAY'
    ) THEN
        RAISE EXCEPTION 'A valid one-way experiment is required.';
    END IF;

    SELECT count(DISTINCT factor_a_level_id),
           count(*),
           avg(response_value)
    INTO k, n, grand_mean
    FROM observations
    WHERE experiment_id = p_experiment_id
      AND state = 'VALID';

    IF k < 2 OR n < 4 THEN
        RAISE EXCEPTION 'Insufficient observations or groups.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id
        HAVING count(*) < 2
    ) THEN
        RAISE EXCEPTION 'Every group needs at least two observations.';
    END IF;

    WITH group_stats AS (
        SELECT factor_a_level_id,
               count(*) AS group_n,
               avg(response_value) AS group_mean
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id
    )
    SELECT sum(group_n * power(group_mean - grand_mean, 2))
    INTO ss_between
    FROM group_stats;

    WITH group_stats AS (
        SELECT factor_a_level_id,
               avg(response_value) AS group_mean
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id
    )
    SELECT sum(
        power(o.response_value - g.group_mean, 2)
    )
    INTO ss_within
    FROM observations o
    JOIN group_stats g
      ON g.factor_a_level_id = o.factor_a_level_id
    WHERE o.experiment_id = p_experiment_id
      AND o.state = 'VALID';

    df_between := k - 1;
    df_within := n - k;

    ms_between := ss_between / df_between;
    ms_within := ss_within / df_within;

    f_value := CASE
        WHEN ms_within = 0 AND ms_between = 0 THEN 0
        WHEN ms_within = 0 THEN 'Infinity'::DOUBLE PRECISION
        ELSE ms_between / ms_within
    END;

    p := f_survival(f_value, df_between, df_within);

    total_ss := ss_between + ss_within;

    RETURN QUERY SELECT
        'Between groups'::TEXT,
        df_between,
        ss_between,
        ms_between,
        f_value,
        p,
        CASE
            WHEN total_ss = 0 THEN 0
            ELSE ss_between / total_ss
        END,
        CASE
            WHEN total_ss + ms_within = 0 THEN 0
            ELSE GREATEST(
                0,
                (ss_between - df_between * ms_within)
                / (total_ss + ms_within)
            )
        END;
END;
$$;


-- ============================================================
-- 13. TWO-WAY ANOVA FUNCTION
-- Balanced factorial design with replication.
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_two_way_anova(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    source_name TEXT,
    degrees_of_freedom INTEGER,
    sum_squares DOUBLE PRECISION,
    mean_square DOUBLE PRECISION,
    f_statistic DOUBLE PRECISION,
    p_value DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    a_count INTEGER;
    b_count INTEGER;
    replication INTEGER;
    df_error INTEGER;
    ss_error DOUBLE PRECISION;
    ms_error DOUBLE PRECISION;
    grand_mean DOUBLE PRECISION;
    ss_a DOUBLE PRECISION;
    ss_b DOUBLE PRECISION;
    ss_ab DOUBLE PRECISION;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM experiments
        WHERE experiment_id = p_experiment_id
          AND analysis_method = 'TWO_WAY'
    ) THEN
        RAISE EXCEPTION 'A valid two-way experiment is required.';
    END IF;

    SELECT count(DISTINCT factor_a_level_id),
           count(DISTINCT factor_b_level_id),
           count(*),
           avg(response_value)
    INTO a_count, b_count, replication, grand_mean
    FROM observations
    WHERE experiment_id = p_experiment_id
      AND state = 'VALID';

    IF a_count < 2 OR b_count < 2 THEN
        RAISE EXCEPTION 'Both factors require at least two levels.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id, factor_b_level_id
        HAVING count(*) < 2
    ) THEN
        RAISE EXCEPTION 'Each cell requires at least two observations.';
    END IF;

    IF (
        SELECT count(DISTINCT cell_n)
        FROM (
            SELECT count(*) AS cell_n
            FROM observations
            WHERE experiment_id = p_experiment_id
              AND state = 'VALID'
            GROUP BY factor_a_level_id, factor_b_level_id
        ) cells
    ) <> 1 THEN
        RAISE EXCEPTION 'Balanced factorial design required.';
    END IF;

    replication := (
        SELECT min(cell_n)::INTEGER
        FROM (
            SELECT count(*) AS cell_n
            FROM observations
            WHERE experiment_id = p_experiment_id
              AND state = 'VALID'
            GROUP BY factor_a_level_id, factor_b_level_id
        ) cells
    );

    IF (
        SELECT count(*)
        FROM (
            SELECT factor_a_level_id, factor_b_level_id
            FROM observations
            WHERE experiment_id = p_experiment_id
              AND state = 'VALID'
            GROUP BY factor_a_level_id, factor_b_level_id
        ) cells
    ) <> a_count * b_count THEN
        RAISE EXCEPTION 'Missing factorial cells.';
    END IF;

    WITH cell_means AS (
        SELECT factor_a_level_id,
               factor_b_level_id,
               count(*) AS n,
               avg(response_value) AS cell_mean
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id, factor_b_level_id
    ),
    means_a AS (
        SELECT factor_a_level_id,
               avg(response_value) AS mean_a
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id
    ),
    means_b AS (
        SELECT factor_b_level_id,
               avg(response_value) AS mean_b
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_b_level_id
    )
    SELECT
        sum(replication * power(c.cell_mean - ma.mean_a
            - mb.mean_b + grand_mean, 2))
    INTO ss_ab
    FROM cell_means c
    JOIN means_a ma USING (factor_a_level_id)
    JOIN means_b mb USING (factor_b_level_id);

    SELECT
        b_count * replication * sum(
            power(group_mean - grand_mean, 2)
        )
    INTO ss_a
    FROM (
        SELECT factor_a_level_id,
               avg(response_value) AS group_mean
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id
    ) x;

    SELECT
        a_count * replication * sum(
            power(group_mean - grand_mean, 2)
        )
    INTO ss_b
    FROM (
        SELECT factor_b_level_id,
               avg(response_value) AS group_mean
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_b_level_id
    ) x;

    WITH cell_means AS (
        SELECT factor_a_level_id,
               factor_b_level_id,
               avg(response_value) AS cell_mean
        FROM observations
        WHERE experiment_id = p_experiment_id
          AND state = 'VALID'
        GROUP BY factor_a_level_id, factor_b_level_id
    )
    SELECT sum(power(o.response_value - c.cell_mean, 2))
    INTO ss_error
    FROM observations o
    JOIN cell_means c
      USING (factor_a_level_id, factor_b_level_id)
    WHERE o.experiment_id = p_experiment_id
      AND o.state = 'VALID';

    df_error := a_count * b_count * (replication - 1);

    ms_error := ss_error / df_error;

    RETURN QUERY
    SELECT
        effects.source_name,
        effects.df,
        effects.ss,
        effects.ss / effects.df,
        CASE
            WHEN ms_error = 0 AND effects.ss = 0 THEN 0
            WHEN ms_error = 0 THEN 'Infinity'::DOUBLE PRECISION
            ELSE (effects.ss / effects.df) / ms_error
        END,
        f_survival(
            CASE
                WHEN ms_error = 0 AND effects.ss = 0 THEN 0
                WHEN ms_error = 0 THEN 'Infinity'::DOUBLE PRECISION
                ELSE (effects.ss / effects.df) / ms_error
            END,
            effects.df,
            df_error
        )
    FROM (
        VALUES
            ('Factor A'::TEXT, a_count - 1, ss_a),
            ('Factor B'::TEXT, b_count - 1, ss_b),
            ('Interaction'::TEXT,
                (a_count - 1) * (b_count - 1), ss_ab)
    ) effects(source_name, df, ss);
END;
$$;


-- ============================================================
-- 14. HOLM ADJUSTMENT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_holm_adjustment(
    p_values DOUBLE PRECISION[]
)
RETURNS DOUBLE PRECISION[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    ordered RECORD;
    result DOUBLE PRECISION[];
    maximum_value DOUBLE PRECISION := 0;
    total INTEGER;
    rank_number INTEGER := 0;
    index_number INTEGER;
BEGIN
    total := cardinality(p_values);

    IF total = 0 THEN
        RETURN ARRAY[]::DOUBLE PRECISION[];
    END IF;

    result := array_fill(0.0::DOUBLE PRECISION, ARRAY[total]);

    IF EXISTS (
        SELECT 1
        FROM unnest(p_values) p
        WHERE p IS NULL OR p < 0 OR p > 1
    ) THEN
        RAISE EXCEPTION 'Invalid p-value array.';
    END IF;

    FOR ordered IN
        SELECT p, ordinality
        FROM unnest(p_values) WITH ORDINALITY AS values_table(p, ordinality)
        ORDER BY p, ordinality
    LOOP
        rank_number := rank_number + 1;

        index_number := ordered.ordinality::INTEGER;

        maximum_value := GREATEST(
            maximum_value,
            LEAST(
                1.0,
                (total - rank_number + 1) * ordered.p
            )
        );

        result[index_number] := maximum_value;
    END LOOP;

    RETURN result;
END;
$$;


-- ============================================================
-- 15. DESCRIPTIVE STATISTICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW group_descriptive_statistics AS
SELECT
    o.experiment_id,
    fa.level_name AS factor_a,
    fb.level_name AS factor_b,
    count(*) AS sample_size,
    avg(o.response_value) AS mean,
    variance(o.response_value) AS sample_variance,
    stddev_samp(o.response_value) AS standard_deviation,
    min(o.response_value) AS minimum,
    max(o.response_value) AS maximum
FROM observations o
JOIN factor_levels fa
    ON fa.level_id = o.factor_a_level_id
LEFT JOIN factor_levels fb
    ON fb.level_id = o.factor_b_level_id
WHERE o.state = 'VALID'
GROUP BY
    o.experiment_id,
    fa.level_name,
    fb.level_name;


-- ============================================================
-- 16. MERGEABLE ANALYSIS REPORT VIEW
-- ============================================================

CREATE OR REPLACE VIEW analysis_report AS
SELECT
    e.experiment_code,
    e.experiment_name,
    ar.analysis_run_id,
    ar.method,
    ar.run_status,
    r.source_name,
    r.degrees_of_freedom,
    r.sum_squares,
    r.mean_square,
    r.f_statistic,
    r.p_value,
    r.eta_squared,
    r.omega_squared
FROM experiments e
JOIN analysis_runs ar
    ON ar.experiment_id = e.experiment_id
LEFT JOIN anova_results r
    ON r.analysis_run_id = ar.analysis_run_id;


-- ============================================================
-- 17. EXPERIMENT LIFECYCLE PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE change_experiment_status(
    p_experiment_id BIGINT,
    p_new_status experiment_status
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment does not exist.';
    END IF;

    IF NOT (
        (current_status = 'DRAFT'
            AND p_new_status = 'COLLECTING')
        OR
        (current_status = 'COLLECTING'
            AND p_new_status IN ('READY', 'DRAFT'))
        OR
        (current_status = 'READY'
            AND p_new_status IN ('ANALYZING', 'COLLECTING'))
        OR
        (current_status = 'ANALYZING'
            AND p_new_status IN ('COMPLETED', 'FAILED'))
        OR
        (current_status = 'COMPLETED'
            AND p_new_status = 'ARCHIVED')
        OR
        (current_status = 'FAILED'
            AND p_new_status = 'READY')
    ) THEN
        RAISE EXCEPTION
            'Invalid experiment transition: % -> %',
            current_status,
            p_new_status;
    END IF;

    UPDATE experiments
    SET status = p_new_status,
        completed_at = CASE
            WHEN p_new_status = 'COMPLETED'
                THEN CURRENT_TIMESTAMP
            ELSE completed_at
        END
    WHERE experiment_id = p_experiment_id;
END;
$$;


-- ============================================================
-- 18. SAMPLE EXPERIMENT: ONE-WAY ANOVA
-- ============================================================

INSERT INTO experiments (
    experiment_code,
    experiment_name,
    description,
    analysis_method,
    created_by
)
VALUES (
    'EXP-ONE-001',
    'Manufacturing Process Comparison',
    'Comparison of three manufacturing processes.',
    'ONE_WAY',
    'research_team'
);


INSERT INTO factors (
    experiment_id,
    factor_name,
    factor_role
)
SELECT experiment_id, 'Manufacturing Process', 'FACTOR_A'
FROM experiments
WHERE experiment_code = 'EXP-ONE-001';


INSERT INTO factor_levels (
    factor_id,
    level_name,
    display_order
)
SELECT factor_id, level_name, display_order
FROM factors
CROSS JOIN (
    VALUES
        ('Control', 1),
        ('Treatment A', 2),
        ('Treatment B', 3)
) levels(level_name, display_order)
WHERE factors.factor_name = 'Manufacturing Process'
  AND factors.experiment_id = (
      SELECT experiment_id
      FROM experiments
      WHERE experiment_code = 'EXP-ONE-001'
  );


INSERT INTO observations (
    experiment_id,
    factor_a_level_id,
    response_value,
    subject_code
)
SELECT
    e.experiment_id,
    fl.level_id,
    sample.value,
    sample.subject_code
FROM (
    VALUES
        ('Control', 21.0, 'C01'),
        ('Control', 23.0, 'C02'),
        ('Control', 22.0, 'C03'),
        ('Control', 24.0, 'C04'),
        ('Control', 20.0, 'C05'),
        ('Control', 22.0, 'C06'),

        ('Treatment A', 25.0, 'A01'),
        ('Treatment A', 27.0, 'A02'),
        ('Treatment A', 26.0, 'A03'),
        ('Treatment A', 28.0, 'A04'),
        ('Treatment A', 24.0, 'A05'),
        ('Treatment A', 27.0, 'A06'),

        ('Treatment B', 30.0, 'B01'),
        ('Treatment B', 32.0, 'B02'),
        ('Treatment B', 29.0, 'B03'),
        ('Treatment B', 31.0, 'B04'),
        ('Treatment B', 33.0, 'B05'),
        ('Treatment B', 30.0, 'B06')
) AS sample(group_name, value, subject_code)
JOIN experiments e
    ON e.experiment_code = 'EXP-ONE-001'
JOIN factor_levels fl
    ON fl.level_name = sample.group_name
JOIN factors f
    ON f.factor_id = fl.factor_id
   AND f.experiment_id = e.experiment_id
   AND f.factor_role = 'FACTOR_A';


-- ============================================================
-- 19. SAMPLE EXPERIMENT: TWO-WAY ANOVA
-- ============================================================

INSERT INTO experiments (
    experiment_code,
    experiment_name,
    description,
    analysis_method,
    created_by
)
VALUES (
    'EXP-TWO-001',
    'Production Technology and Temperature',
    'Factorial experiment evaluating technology and temperature.',
    'TWO_WAY',
    'research_team'
);


INSERT INTO factors (
    experiment_id,
    factor_name,
    factor_role
)
SELECT experiment_id, factor_name, factor_role
FROM experiments
CROSS JOIN (
    VALUES
        ('Technology', 'FACTOR_A'),
        ('Temperature', 'FACTOR_B')
) AS definitions(factor_name, factor_role)
WHERE experiment_code = 'EXP-TWO-001';


INSERT INTO factor_levels (
    factor_id,
    level_name,
    display_order
)
SELECT
    f.factor_id,
    level_name,
    display_order
FROM factors f
JOIN experiments e
    ON e.experiment_id = f.experiment_id
CROSS JOIN LATERAL (
    SELECT
        CASE
            WHEN f.factor_role = 'FACTOR_A'
                THEN ARRAY['Traditional', 'Modern']
            ELSE ARRAY['Low', 'High']
        END AS names
) definitions
CROSS JOIN LATERAL
    unnest(definitions.names) WITH ORDINALITY
    AS levels(level_name, display_order)
WHERE e.experiment_code = 'EXP-TWO-001';


INSERT INTO observations (
    experiment_id,
    factor_a_level_id,
    factor_b_level_id,
    response_value,
    subject_code
)
SELECT
    e.experiment_id,
    fa.level_id,
    fb.level_id,
    sample.value,
    sample.subject_code
FROM (
    VALUES
        ('Traditional', 'Low', 10.0, 'TL01'),
        ('Traditional', 'Low', 11.0, 'TL02'),
        ('Traditional', 'Low', 9.0, 'TL03'),
        ('Traditional', 'Low', 10.0, 'TL04'),

        ('Traditional', 'High', 15.0, 'TH01'),
        ('Traditional', 'High', 14.0, 'TH02'),
        ('Traditional', 'High', 16.0, 'TH03'),
        ('Traditional', 'High', 15.0, 'TH04'),

        ('Modern', 'Low', 13.0, 'ML01'),
        ('Modern', 'Low', 12.0, 'ML02'),
        ('Modern', 'Low', 14.0, 'ML03'),
        ('Modern', 'Low', 13.0, 'ML04'),

        ('Modern', 'High', 23.0, 'MH01'),
        ('Modern', 'High', 22.0, 'MH02'),
        ('Modern', 'High', 24.0, 'MH03'),
        ('Modern', 'High', 23.0, 'MH04')
) sample(a_name, b_name, value, subject_code)
JOIN experiments e
    ON e.experiment_code = 'EXP-TWO-001'
JOIN factors fa_def
    ON fa_def.experiment_id = e.experiment_id
   AND fa_def.factor_role = 'FACTOR_A'
JOIN factor_levels fa
    ON fa.factor_id = fa_def.factor_id
   AND fa.level_name = sample.a_name
JOIN factors fb_def
    ON fb_def.experiment_id = e.experiment_id
   AND fb_def.factor_role = 'FACTOR_B'
JOIN factor_levels fb
    ON fb.factor_id = fb_def.factor_id
   AND fb.level_name = sample.b_name;


-- ============================================================
-- 20. SAMPLE LIFECYCLE PROCESSING
-- ============================================================

DO $$
DECLARE
    one_id BIGINT;
    two_id BIGINT;
BEGIN
    SELECT experiment_id INTO one_id
    FROM experiments
    WHERE experiment_code = 'EXP-ONE-001';

    SELECT experiment_id INTO two_id
    FROM experiments
    WHERE experiment_code = 'EXP-TWO-001';

    CALL change_experiment_status(one_id, 'COLLECTING');
    CALL change_experiment_status(one_id, 'READY');

    CALL change_experiment_status(two_id, 'COLLECTING');
    CALL change_experiment_status(two_id, 'READY');
END;
$$;


-- ============================================================
-- 21. VALIDATION REPORTS
-- ============================================================

SELECT
    e.experiment_code,
    v.check_name,
    v.passed,
    v.details
FROM experiments e
CROSS JOIN LATERAL validate_experiment(e.experiment_id) v
ORDER BY e.experiment_code, v.check_name;


-- ============================================================
-- 22. DESCRIPTIVE STATISTICS REPORT
-- ============================================================

SELECT *
FROM group_descriptive_statistics
ORDER BY experiment_id, factor_a, factor_b;


-- ============================================================
-- 23. ONE-WAY ANOVA EXECUTION
-- ============================================================

DO $$
DECLARE
    experiment_id_value BIGINT;
    run_id BIGINT;
    result RECORD;
BEGIN
    SELECT experiment_id
    INTO experiment_id_value
    FROM experiments
    WHERE experiment_code = 'EXP-ONE-001';

    IF EXISTS (
        SELECT 1
        FROM validate_experiment(experiment_id_value)
        WHERE passed = FALSE
    ) THEN
        RAISE EXCEPTION 'Experiment validation failed.';
    END IF;

    INSERT INTO analysis_runs (
        experiment_id,
        method
    )
    VALUES (
        experiment_id_value,
        'ONE_WAY'
    )
    RETURNING analysis_run_id INTO run_id;

    FOR result IN
        SELECT *
        FROM calculate_one_way_anova(experiment_id_value)
    LOOP
        INSERT INTO anova_results (
            analysis_run_id,
            source_name,
            degrees_of_freedom,
            sum_squares,
            mean_square,
            f_statistic,
            p_value,
            eta_squared,
            omega_squared
        )
        VALUES (
            run_id,
            result.source_name,
            result.degrees_of_freedom,
            result.sum_squares,
            result.mean_square,
            result.f_statistic,
            result.p_value,
            result.eta_squared,
            result.omega_squared
        );
    END LOOP;

    UPDATE analysis_runs
    SET run_status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE analysis_run_id = run_id;

    UPDATE experiments
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = experiment_id_value;
END;
$$;


-- ============================================================
-- 24. TWO-WAY ANOVA EXECUTION
-- ============================================================

DO $$
DECLARE
    experiment_id_value BIGINT;
    run_id BIGINT;
    result RECORD;
BEGIN
    SELECT experiment_id
    INTO experiment_id_value
    FROM experiments
    WHERE experiment_code = 'EXP-TWO-001';

    IF EXISTS (
        SELECT 1
        FROM validate_experiment(experiment_id_value)
        WHERE passed = FALSE
    ) THEN
        RAISE EXCEPTION 'Two-way experiment validation failed.';
    END IF;

    INSERT INTO analysis_runs (
        experiment_id,
        method
    )
    VALUES (
        experiment_id_value,
        'TWO_WAY'
    )
    RETURNING analysis_run_id INTO run_id;

    FOR result IN
        SELECT *
        FROM calculate_two_way_anova(experiment_id_value)
    LOOP
        INSERT INTO anova_results (
            analysis_run_id,
            source_name,
            degrees_of_freedom,
            sum_squares,
            mean_square,
            f_statistic,
            p_value
        )
        VALUES (
            run_id,
            result.source_name,
            result.degrees_of_freedom,
            result.sum_squares,
            result.mean_square,
            result.f_statistic,
            result.p_value
        );
    END LOOP;

    UPDATE analysis_runs
    SET run_status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE analysis_run_id = run_id;

    UPDATE experiments
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = experiment_id_value;
END;
$$;


-- ============================================================
-- 25. ONE-WAY POST-HOC POOLED PAIRWISE COMPARISONS
--
-- Holm adjustment is calculated across all pairwise tests.
-- These comparisons use the pooled within-group variance.
-- ============================================================

DO $$
DECLARE
    experiment_id_value BIGINT;
    run_id BIGINT;
    residual_df INTEGER;
    pooled_ms DOUBLE PRECISION;
    comparison RECORD;
    raw_values DOUBLE PRECISION[];
    adjusted_values DOUBLE PRECISION[];
    position INTEGER := 0;
    comparison_count INTEGER;
BEGIN
    SELECT experiment_id
    INTO experiment_id_value
    FROM experiments
    WHERE experiment_code = 'EXP-ONE-001';

    SELECT analysis_run_id
    INTO run_id
    FROM analysis_runs
    WHERE experiment_id = experiment_id_value
      AND run_status = 'COMPLETED'
    ORDER BY analysis_run_id DESC
    LIMIT 1;

    SELECT df_within, ms_within
    INTO residual_df, pooled_ms
    FROM (
        SELECT
            n - k AS df_within,
            ss_within / (n - k) AS ms_within
        FROM (
            SELECT
                count(*) AS n,
                count(DISTINCT factor_a_level_id) AS k,
                sum(
                    power(
                        response_value - group_mean,
                        2
                    )
                ) AS ss_within
            FROM (
                SELECT
                    o.response_value,
                    o.factor_a_level_id,
                    avg(o.response_value) OVER (
                        PARTITION BY o.factor_a_level_id
                    ) AS group_mean
                FROM observations o
                WHERE o.experiment_id = experiment_id_value
                  AND o.state = 'VALID'
            ) residuals
        ) aggregate_data
    ) variance_data;

    CREATE TEMP TABLE pairwise_work (
        group_a BIGINT,
        group_b BIGINT,
        mean_difference DOUBLE PRECISION,
        statistic DOUBLE PRECISION,
        raw_p DOUBLE PRECISION
    ) ON COMMIT DROP;

    INSERT INTO pairwise_work
    SELECT
        a.level_id,
        b.level_id,
        a.mean_value - b.mean_value,
        CASE
            WHEN pooled_ms = 0 THEN 0
            ELSE (a.mean_value - b.mean_value)
                / sqrt(pooled_ms * (1.0 / a.n + 1.0 / b.n))
        END,
        CASE
            WHEN pooled_ms = 0 THEN
                CASE
                    WHEN a.mean_value = b.mean_value THEN 1
                    ELSE 0
                END
            ELSE t_two_tailed_p(
                (a.mean_value - b.mean_value)
                / sqrt(pooled_ms * (1.0 / a.n + 1.0 / b.n)),
                residual_df
            )
        END
    FROM (
        SELECT
            fl.level_id,
            avg(o.response_value) AS mean_value,
            count(*) AS n
        FROM observations o
        JOIN factor_levels fl
            ON fl.level_id = o.factor_a_level_id
        WHERE o.experiment_id = experiment_id_value
          AND o.state = 'VALID'
        GROUP BY fl.level_id
    ) a
    JOIN (
        SELECT
            fl.level_id,
            avg(o.response_value) AS mean_value,
            count(*) AS n
        FROM observations o
        JOIN factor_levels fl
            ON fl.level_id = o.factor_a_level_id
        WHERE o.experiment_id = experiment_id_value
          AND o.state = 'VALID'
        GROUP BY fl.level_id
    ) b
        ON a.level_id < b.level_id;

    SELECT array_agg(raw_p ORDER BY raw_p, group_a, group_b)
    INTO raw_values
    FROM pairwise_work;

    adjusted_values := calculate_holm_adjustment(raw_values);

    SELECT count(*) INTO comparison_count
    FROM pairwise_work;

    FOR comparison IN
        SELECT *
        FROM pairwise_work
        ORDER BY raw_p, group_a, group_b
    LOOP
        position := position + 1;

        INSERT INTO posthoc_comparisons (
            analysis_run_id,
            group_a_level_id,
            group_b_level_id,
            method,
            mean_difference,
            test_statistic,
            raw_p_value,
            adjusted_p_value,
            significant
        )
        VALUES (
            run_id,
            comparison.group_a,
            comparison.group_b,
            'POOLED_PAIRWISE_T_HOLM',
            comparison.mean_difference,
            comparison.statistic,
            comparison.raw_p,
            adjusted_values[position],
            adjusted_values[position] < 0.05
        );
    END LOOP;
END;
$$;


-- ============================================================
-- 26. REPORTING QUERIES
-- ============================================================

-- One-way and two-way analysis results.
SELECT *
FROM analysis_report
ORDER BY experiment_code, source_name;


-- Pairwise comparison report.
SELECT
    pc.analysis_run_id,
    a.level_name AS group_a,
    b.level_name AS group_b,
    pc.mean_difference,
    pc.test_statistic,
    pc.raw_p_value,
    pc.adjusted_p_value,
    pc.significant,
    pc.method
FROM posthoc_comparisons pc
JOIN factor_levels a
    ON a.level_id = pc.group_a_level_id
JOIN factor_levels b
    ON b.level_id = pc.group_b_level_id
ORDER BY pc.analysis_run_id, pc.adjusted_p_value;


-- Experiment-level group aggregation.
SELECT
    experiment_id,
    factor_a,
    count(*) AS groups,
    sum(sample_size) AS total_observations,
    avg(mean) AS average_group_mean
FROM group_descriptive_statistics
GROUP BY experiment_id, factor_a
ORDER BY experiment_id;


-- Statistical significance evaluation.
SELECT
    experiment_code,
    source_name,
    f_statistic,
    p_value,
    CASE
        WHEN p_value < 0.01 THEN 'STRONG EVIDENCE'
        WHEN p_value < 0.05 THEN 'STATISTICALLY SIGNIFICANT'
        ELSE 'NOT STATISTICALLY SIGNIFICANT'
    END AS interpretation
FROM analysis_report
WHERE source_name IS NOT NULL;


-- ============================================================
-- 27. DATABASE FUNCTION TESTS
-- ============================================================

DO $$
DECLARE
    adjusted DOUBLE PRECISION[];
    experiment_id_value BIGINT;
    f_probability DOUBLE PRECISION;
BEGIN
    adjusted := calculate_holm_adjustment(
        ARRAY[0.01, 0.03, 0.04]::DOUBLE PRECISION[]
    );

    IF cardinality(adjusted) <> 3 THEN
        RAISE EXCEPTION 'Holm adjustment test failed.';
    END IF;

    IF adjusted[1] <> 0.03
       OR adjusted[2] <> 0.06
       OR adjusted[3] <> 0.06 THEN
        RAISE EXCEPTION 'Unexpected Holm adjustment result.';
    END IF;

    f_probability := f_survival(0, 1, 10);

    IF f_probability <> 1 THEN
        RAISE EXCEPTION 'F distribution test failed.';
    END IF;

    SELECT experiment_id
    INTO experiment_id_value
    FROM experiments
    WHERE experiment_code = 'EXP-ONE-001';

    IF NOT EXISTS (
        SELECT 1
        FROM calculate_one_way_anova(experiment_id_value)
    ) THEN
        RAISE EXCEPTION 'One-way ANOVA test failed.';
    END IF;

    RAISE NOTICE 'All PostgreSQL statistical tests passed.';
END;
$$;


COMMIT;
