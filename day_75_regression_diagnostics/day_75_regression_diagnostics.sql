/*
===============================================================================
REGRESSION DIAGNOSTICS DATABASE
PostgreSQL 14+

Scope:
1. Regression model and observation management
2. Predictor coefficients and fitted values
3. Multicollinearity and VIF
4. Heteroscedasticity assessment
5. Residual diagnostics
6. Influence and leverage
7. HC3 robust standard errors
8. Diagnostic policy and reporting
9. Transaction-controlled model execution

The database stores calculated model results. OLS coefficient estimation is
performed by an external numerical implementation. PostgreSQL performs
relational integrity enforcement, residual calculations, aggregation,
diagnostic screening, and reporting.
===============================================================================
*/

DROP SCHEMA IF EXISTS regression_lab CASCADE;

CREATE SCHEMA regression_lab;

SET search_path TO regression_lab, public;

-- ---------------------------------------------------------------------------
-- Domain types
-- ---------------------------------------------------------------------------

CREATE TYPE model_status AS ENUM (
    'CREATED',
    'FITTED',
    'DIAGNOSTICS_COMPLETED',
    'REJECTED',
    'ARCHIVED'
);

CREATE TYPE diagnostic_category AS ENUM (
    'MULTICOLLINEARITY',
    'HETEROSCEDASTICITY',
    'RESIDUAL_NORMALITY',
    'HIGH_LEVERAGE',
    'INFLUENTIAL_OBSERVATION',
    'LARGE_RESIDUAL'
);

CREATE TYPE diagnostic_severity AS ENUM (
    'PASS',
    'WARNING',
    'FAIL'
);

CREATE TYPE observation_status AS ENUM (
    'ACTIVE',
    'EXCLUDED',
    'UNDER_REVIEW'
);

-- ---------------------------------------------------------------------------
-- Reference tables
-- ---------------------------------------------------------------------------

CREATE TABLE analyst (
    analyst_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analyst_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE regression_model (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name VARCHAR(150) NOT NULL,
    analyst_id BIGINT NOT NULL REFERENCES analyst(analyst_id),
    status model_status NOT NULL DEFAULT 'CREATED',
    target_name VARCHAR(100) NOT NULL,
    observation_count INTEGER NOT NULL DEFAULT 0,
    predictor_count INTEGER NOT NULL CHECK (predictor_count > 0),
    parameter_count INTEGER GENERATED ALWAYS AS (
        predictor_count + 1
    ) STORED,
    r_squared NUMERIC(16,12),
    adjusted_r_squared NUMERIC(16,12),
    residual_standard_error NUMERIC(20,10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fitted_at TIMESTAMPTZ,

    CONSTRAINT model_r_squared_valid CHECK (
        r_squared IS NULL OR
        (r_squared >= 0 AND r_squared <= 1)
    ),

    CONSTRAINT model_adjusted_r_squared_valid CHECK (
        adjusted_r_squared IS NULL OR
        adjusted_r_squared <= 1
    ),

    CONSTRAINT model_residual_error_valid CHECK (
        residual_standard_error IS NULL OR
        residual_standard_error >= 0
    )
);

CREATE TABLE model_predictor (
    predictor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_model(model_id)
        ON DELETE CASCADE,
    predictor_name VARCHAR(100) NOT NULL,
    predictor_order INTEGER NOT NULL CHECK (predictor_order > 0),
    coefficient NUMERIC(24,12),
    hc3_standard_error NUMERIC(24,12),

    UNIQUE (model_id, predictor_name),
    UNIQUE (model_id, predictor_order),

    CHECK (
        hc3_standard_error IS NULL OR
        hc3_standard_error >= 0
    )
);

CREATE TABLE observation (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_model(model_id)
        ON DELETE CASCADE,
    external_reference VARCHAR(120) NOT NULL,
    actual_value NUMERIC(24,10) NOT NULL,
    fitted_value NUMERIC(24,10),
    residual NUMERIC(24,10),
    squared_residual NUMERIC(28,10),
    status observation_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (model_id, external_reference),

    CHECK (
        squared_residual IS NULL OR
        squared_residual >= 0
    )
);

CREATE TABLE observation_predictor_value (
    observation_id BIGINT NOT NULL REFERENCES observation(
        observation_id
    ) ON DELETE CASCADE,
    predictor_id BIGINT NOT NULL REFERENCES model_predictor(
        predictor_id
    ) ON DELETE CASCADE,
    predictor_value NUMERIC(24,10) NOT NULL,

    PRIMARY KEY (observation_id, predictor_id)
);

-- ---------------------------------------------------------------------------
-- Diagnostic results
-- ---------------------------------------------------------------------------

CREATE TABLE diagnostic_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(120) NOT NULL UNIQUE,
    vif_warning NUMERIC(12,6) NOT NULL DEFAULT 5,
    vif_critical NUMERIC(12,6) NOT NULL DEFAULT 10,
    significance_level NUMERIC(8,6) NOT NULL DEFAULT 0.05,
    cook_multiplier NUMERIC(12,6) NOT NULL DEFAULT 4,
    leverage_multiplier NUMERIC(12,6) NOT NULL DEFAULT 2,
    studentized_limit NUMERIC(12,6) NOT NULL DEFAULT 3,

    CHECK (vif_warning > 0),
    CHECK (vif_critical > vif_warning),
    CHECK (
        significance_level > 0 AND
        significance_level < 1
    ),
    CHECK (cook_multiplier > 0),
    CHECK (leverage_multiplier > 0),
    CHECK (studentized_limit > 0)
);

CREATE TABLE diagnostic_result (
    diagnostic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_model(model_id)
        ON DELETE CASCADE,
    policy_id BIGINT NOT NULL REFERENCES diagnostic_policy(policy_id),
    category diagnostic_category NOT NULL,
    subject_reference VARCHAR(120),
    statistic NUMERIC(28,12) NOT NULL,
    threshold NUMERIC(28,12),
    p_value NUMERIC(16,12),
    severity diagnostic_severity NOT NULL,
    explanation TEXT NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        p_value IS NULL OR
        (p_value >= 0 AND p_value <= 1)
    )
);

CREATE TABLE influence_measure (
    observation_id BIGINT PRIMARY KEY REFERENCES observation(
        observation_id
    ) ON DELETE CASCADE,
    leverage NUMERIC(20,12) NOT NULL,
    studentized_residual NUMERIC(24,12) NOT NULL,
    cooks_distance NUMERIC(24,12) NOT NULL,
    externally_studentized_residual NUMERIC(24,12),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (leverage >= 0 AND leverage <= 1),
    CHECK (cooks_distance >= 0)
);

CREATE TABLE auxiliary_test (
    auxiliary_test_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_model(model_id)
        ON DELETE CASCADE,
    test_name VARCHAR(100) NOT NULL,
    test_statistic NUMERIC(24,12) NOT NULL,
    degrees_of_freedom INTEGER NOT NULL CHECK (
        degrees_of_freedom > 0
    ),
    p_value NUMERIC(16,12) NOT NULL CHECK (
        p_value >= 0 AND p_value <= 1
    ),
    test_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Indexing
-- ---------------------------------------------------------------------------

CREATE INDEX idx_model_analyst_status
ON regression_model(analyst_id, status);

CREATE INDEX idx_observation_model_status
ON observation(model_id, status);

CREATE INDEX idx_predictor_model_order
ON model_predictor(model_id, predictor_order);

CREATE INDEX idx_diagnostic_model_category
ON diagnostic_result(model_id, category, severity);

CREATE INDEX idx_influence_cooks
ON influence_measure(cooks_distance DESC);

CREATE INDEX idx_auxiliary_model_test
ON auxiliary_test(model_id, test_name);

CREATE INDEX idx_observation_external_reference
ON observation(external_reference);

-- ---------------------------------------------------------------------------
-- Integrity trigger: maintain residual values from fitted predictions
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_observation_residual()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.fitted_value IS NOT NULL THEN
        NEW.residual :=
            NEW.actual_value - NEW.fitted_value;

        NEW.squared_residual :=
            NEW.residual * NEW.residual;
    ELSE
        NEW.residual := NULL;
        NEW.squared_residual := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calculate_residual
BEFORE INSERT OR UPDATE OF actual_value, fitted_value
ON observation
FOR EACH ROW
EXECUTE FUNCTION calculate_observation_residual();

-- ---------------------------------------------------------------------------
-- Predictor relationship validation
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_observation_predictor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    observation_model BIGINT;
    predictor_model BIGINT;
BEGIN
    SELECT model_id
    INTO observation_model
    FROM observation
    WHERE observation_id = NEW.observation_id;

    SELECT model_id
    INTO predictor_model
    FROM model_predictor
    WHERE predictor_id = NEW.predictor_id;

    IF observation_model IS NULL OR predictor_model IS NULL THEN
        RAISE EXCEPTION 'Observation or predictor does not exist';
    END IF;

    IF observation_model <> predictor_model THEN
        RAISE EXCEPTION
            'Observation and predictor must belong to the same model';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_observation_predictor
BEFORE INSERT OR UPDATE
ON observation_predictor_value
FOR EACH ROW
EXECUTE FUNCTION validate_observation_predictor();

-- ---------------------------------------------------------------------------
-- Model lifecycle enforcement
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_model_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'ARCHIVED' AND NEW.status <> 'ARCHIVED' THEN
        RAISE EXCEPTION 'Archived models cannot be reopened';
    END IF;

    IF OLD.status = 'REJECTED'
       AND NEW.status NOT IN ('REJECTED', 'ARCHIVED') THEN
        RAISE EXCEPTION 'Rejected model cannot transition to active state';
    END IF;

    IF NEW.status IN (
        'FITTED',
        'DIAGNOSTICS_COMPLETED'
    ) AND (
        NEW.r_squared IS NULL OR
        NEW.residual_standard_error IS NULL OR
        NEW.observation_count <= NEW.parameter_count
    ) THEN
        RAISE EXCEPTION
            'Fitted model requires valid fit statistics and sufficient observations';
    END IF;

    IF NEW.status = 'DIAGNOSTICS_COMPLETED'
       AND OLD.status NOT IN (
           'FITTED',
           'DIAGNOSTICS_COMPLETED'
       ) THEN
        RAISE EXCEPTION
            'Diagnostics require a fitted model';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_model_transition
BEFORE UPDATE OF status
ON regression_model
FOR EACH ROW
EXECUTE FUNCTION enforce_model_transition();

-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW observation_residual_report AS
SELECT
    o.model_id,
    o.observation_id,
    o.external_reference,
    o.actual_value,
    o.fitted_value,
    o.residual,
    o.squared_residual,
    im.leverage,
    im.studentized_residual,
    im.cooks_distance,
    o.status
FROM observation o
LEFT JOIN influence_measure im
    ON im.observation_id = o.observation_id;

CREATE OR REPLACE VIEW model_quality_report AS
SELECT
    m.model_id,
    m.model_name,
    m.status,
    m.observation_count,
    m.predictor_count,
    m.r_squared,
    m.adjusted_r_squared,
    m.residual_standard_error,
    COUNT(d.diagnostic_id) AS diagnostic_count,
    COUNT(*) FILTER (
        WHERE d.severity = 'WARNING'
    ) AS warning_count,
    COUNT(*) FILTER (
        WHERE d.severity = 'FAIL'
    ) AS failure_count
FROM regression_model m
LEFT JOIN diagnostic_result d
    ON d.model_id = m.model_id
GROUP BY
    m.model_id,
    m.model_name,
    m.status,
    m.observation_count,
    m.predictor_count,
    m.r_squared,
    m.adjusted_r_squared,
    m.residual_standard_error;

-- ---------------------------------------------------------------------------
-- VIF storage and calculation
-- ---------------------------------------------------------------------------

CREATE TABLE predictor_diagnostic (
    model_id BIGINT NOT NULL REFERENCES regression_model(model_id)
        ON DELETE CASCADE,
    predictor_id BIGINT NOT NULL REFERENCES model_predictor(predictor_id)
        ON DELETE CASCADE,
    correlation_with_other_predictors NUMERIC(16,12),
    vif NUMERIC(24,12) NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (model_id, predictor_id),

    CHECK (vif >= 1)
);

CREATE OR REPLACE FUNCTION calculate_vif(
    p_model_id BIGINT,
    p_predictor_id BIGINT
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    result_vif NUMERIC;
BEGIN
    SELECT vif
    INTO result_vif
    FROM predictor_diagnostic
    WHERE model_id = p_model_id
      AND predictor_id = p_predictor_id;

    IF result_vif IS NULL THEN
        RAISE EXCEPTION
            'VIF not available for model %, predictor %',
            p_model_id, p_predictor_id;
    END IF;

    RETURN result_vif;
END;
$$;

-- ---------------------------------------------------------------------------
-- Residual summary function
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION residual_summary(
    p_model_id BIGINT
)
RETURNS TABLE (
    sample_count BIGINT,
    residual_mean NUMERIC,
    residual_variance NUMERIC,
    residual_min NUMERIC,
    residual_max NUMERIC,
    residual_sum_squares NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COUNT(*)::BIGINT,
        AVG(o.residual),
        VAR_POP(o.residual),
        MIN(o.residual),
        MAX(o.residual),
        SUM(o.squared_residual)
    FROM observation o
    WHERE o.model_id = p_model_id
      AND o.status = 'ACTIVE'
      AND o.residual IS NOT NULL;
$$;

-- ---------------------------------------------------------------------------
-- Diagnostic eligibility function
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_model_eligible(
    p_model_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    current_status model_status;
    failures BIGINT;
    active_observations BIGINT;
    required_count BIGINT;
BEGIN
    SELECT status, parameter_count
    INTO current_status, required_count
    FROM regression_model
    WHERE model_id = p_model_id;

    IF current_status IS NULL THEN
        RETURN FALSE;
    END IF;

    SELECT COUNT(*)
    INTO active_observations
    FROM observation
    WHERE model_id = p_model_id
      AND status = 'ACTIVE';

    SELECT COUNT(*)
    INTO failures
    FROM diagnostic_result
    WHERE model_id = p_model_id
      AND severity = 'FAIL';

    RETURN
        current_status = 'DIAGNOSTICS_COMPLETED'
        AND active_observations > required_count
        AND failures = 0;
END;
$$;

-- ---------------------------------------------------------------------------
-- Procedure: refresh fitted values and residuals
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE refresh_model_residuals(
    p_model_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status model_status;
    observation_total BIGINT;
    residual_total BIGINT;
BEGIN
    SELECT status
    INTO current_status
    FROM regression_model
    WHERE model_id = p_model_id
    FOR UPDATE;

    IF current_status IS NULL THEN
        RAISE EXCEPTION 'Unknown model ID %', p_model_id;
    END IF;

    IF current_status NOT IN ('FITTED', 'DIAGNOSTICS_COMPLETED') THEN
        RAISE EXCEPTION
            'Residual refresh requires a fitted model';
    END IF;

    SELECT COUNT(*)
    INTO observation_total
    FROM observation
    WHERE model_id = p_model_id
      AND status = 'ACTIVE';

    SELECT COUNT(*)
    INTO residual_total
    FROM observation
    WHERE model_id = p_model_id
      AND status = 'ACTIVE'
      AND fitted_value IS NOT NULL;

    IF observation_total <> residual_total THEN
        RAISE EXCEPTION
            'Every active observation requires a fitted value';
    END IF;

    UPDATE observation
    SET fitted_value = fitted_value
    WHERE model_id = p_model_id
      AND status = 'ACTIVE';

    UPDATE regression_model
    SET status = 'FITTED'
    WHERE model_id = p_model_id
      AND status = 'DIAGNOSTICS_COMPLETED';
END;
$$;

-- ---------------------------------------------------------------------------
-- Procedure: evaluate and store basic influence findings
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE evaluate_influence(
    p_model_id BIGINT,
    p_policy_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    model_n INTEGER;
    model_p INTEGER;
    cook_limit NUMERIC;
    leverage_limit NUMERIC;
    student_limit NUMERIC;
    observation_record RECORD;
BEGIN
    SELECT observation_count, parameter_count
    INTO model_n, model_p
    FROM regression_model
    WHERE model_id = p_model_id
      AND status IN ('FITTED', 'DIAGNOSTICS_COMPLETED')
    FOR UPDATE;

    IF model_n IS NULL OR model_n <= model_p THEN
        RAISE EXCEPTION 'Model is not eligible for influence evaluation';
    END IF;

    SELECT
        cook_multiplier / model_n,
        leverage_multiplier * model_p / model_n,
        studentized_limit
    INTO cook_limit, leverage_limit, student_limit
    FROM diagnostic_policy
    WHERE policy_id = p_policy_id;

    IF cook_limit IS NULL THEN
        RAISE EXCEPTION 'Unknown diagnostic policy';
    END IF;

    FOR observation_record IN
        SELECT
            o.external_reference,
            im.cooks_distance,
            im.leverage,
            im.studentized_residual
        FROM observation o
        JOIN influence_measure im
            ON im.observation_id = o.observation_id
        WHERE o.model_id = p_model_id
          AND o.status = 'ACTIVE'
    LOOP
        IF observation_record.cooks_distance > cook_limit THEN
            INSERT INTO diagnostic_result (
                model_id,
                policy_id,
                category,
                subject_reference,
                statistic,
                threshold,
                severity,
                explanation
            )
            VALUES (
                p_model_id,
                p_policy_id,
                'INFLUENTIAL_OBSERVATION',
                observation_record.external_reference,
                observation_record.cooks_distance,
                cook_limit,
                'WARNING',
                'Cook distance screening threshold exceeded.'
            );
        END IF;

        IF observation_record.leverage > leverage_limit THEN
            INSERT INTO diagnostic_result (
                model_id,
                policy_id,
                category,
                subject_reference,
                statistic,
                threshold,
                severity,
                explanation
            )
            VALUES (
                p_model_id,
                p_policy_id,
                'HIGH_LEVERAGE',
                observation_record.external_reference,
                observation_record.leverage,
                leverage_limit,
                'WARNING',
                'Leverage screening threshold exceeded.'
            );
        END IF;

        IF ABS(observation_record.studentized_residual)
            > student_limit THEN
            INSERT INTO diagnostic_result (
                model_id,
                policy_id,
                category,
                subject_reference,
                statistic,
                threshold,
                severity,
                explanation
            )
            VALUES (
                p_model_id,
                p_policy_id,
                'LARGE_RESIDUAL',
                observation_record.external_reference,
                ABS(observation_record.studentized_residual),
                student_limit,
                'WARNING',
                'Studentized residual screening threshold exceeded.'
            );
        END IF;
    END LOOP;
END;
$$;

-- ---------------------------------------------------------------------------
-- Sample governance records
-- ---------------------------------------------------------------------------

INSERT INTO analyst (analyst_name, email)
VALUES
    ('Regression Analyst', 'analyst@example.org'),
    ('Model Validation Officer', 'validator@example.org');

INSERT INTO diagnostic_policy (
    policy_name,
    vif_warning,
    vif_critical,
    significance_level,
    cook_multiplier,
    leverage_multiplier,
    studentized_limit
)
VALUES (
    'STANDARD_DIAGNOSTIC_POLICY',
    5,
    10,
    0.05,
    4,
    2,
    3
);

INSERT INTO regression_model (
    model_name,
    analyst_id,
    target_name,
    predictor_count,
    observation_count
)
VALUES (
    'Sales Performance Regression',
    1,
    'Sales',
    2,
    80
);

INSERT INTO model_predictor (
    model_id,
    predictor_name,
    predictor_order,
    coefficient,
    hc3_standard_error
)
VALUES
    (1, 'Advertising_Spend', 1, 2.500000, 0.150000),
    (1, 'Market_Exposure', 2, 1.300000, 0.180000);

-- ---------------------------------------------------------------------------
-- Generate observations and predictor values
-- ---------------------------------------------------------------------------

INSERT INTO observation (
    model_id,
    external_reference,
    actual_value,
    fitted_value
)
SELECT
    1,
    'OBS-' || LPAD(i::TEXT, 3, '0'),
    (
        12 + 2.5 * i
        + 1.3 * (0.92 * i + (i % 7) * 0.8)
        + ((i % 9) - 4) * (0.4 + 0.025 * i)
        + CASE WHEN i = 72 THEN 35 ELSE 0 END
    )::NUMERIC(24,10),
    (
        12 + 2.5 * i
        + 1.3 * (0.92 * i + (i % 7) * 0.8)
    )::NUMERIC(24,10)
FROM generate_series(1, 80) AS i;

INSERT INTO observation_predictor_value (
    observation_id,
    predictor_id,
    predictor_value
)
SELECT
    o.observation_id,
    p.predictor_id,
    CASE
        WHEN p.predictor_name = 'Advertising_Spend'
            THEN substring(o.external_reference FROM 5)::NUMERIC
        WHEN p.predictor_name = 'Market_Exposure'
            THEN (
                0.92 * substring(o.external_reference FROM 5)::NUMERIC
                + (
                    substring(o.external_reference FROM 5)::INTEGER
                    % 7
                ) * 0.8
            )
    END
FROM observation o
JOIN model_predictor p
    ON p.model_id = o.model_id
WHERE o.model_id = 1;

-- ---------------------------------------------------------------------------
-- Store externally calculated VIF results.
--
-- These are illustrative supplied results, not values calculated by this
-- database script. Production values must come from auxiliary regressions.
-- ---------------------------------------------------------------------------

INSERT INTO predictor_diagnostic (
    model_id,
    predictor_id,
    correlation_with_other_predictors,
    vif
)
VALUES
    (1, 1, 0.981000, 18.450000),
    (1, 2, 0.981000, 18.450000);

-- ---------------------------------------------------------------------------
-- Store influence statistics.
--
-- Values represent supplied diagnostic results for the demonstration.
-- ---------------------------------------------------------------------------

INSERT INTO influence_measure (
    observation_id,
    leverage,
    studentized_residual,
    cooks_distance,
    externally_studentized_residual
)
SELECT
    observation_id,
    CASE
        WHEN external_reference = 'OBS-072'
            THEN 0.115
        ELSE 0.025
    END,
    CASE
        WHEN external_reference = 'OBS-072'
            THEN 4.25
        ELSE 0.15
    END,
    CASE
        WHEN external_reference = 'OBS-072'
            THEN 0.42
        ELSE 0.002
    END,
    CASE
        WHEN external_reference = 'OBS-072'
            THEN 4.30
        ELSE 0.15
    END
FROM observation
WHERE model_id = 1;

-- ---------------------------------------------------------------------------
-- Model fit metadata
-- ---------------------------------------------------------------------------

UPDATE regression_model
SET
    status = 'FITTED',
    r_squared = 0.975,
    adjusted_r_squared = 0.974,
    residual_standard_error = 4.250000,
    fitted_at = CURRENT_TIMESTAMP
WHERE model_id = 1;

-- ---------------------------------------------------------------------------
-- Auxiliary tests
-- ---------------------------------------------------------------------------

INSERT INTO auxiliary_test (
    model_id,
    test_name,
    test_statistic,
    degrees_of_freedom,
    p_value,
    test_details
)
VALUES
(
    1,
    'BREUSCH_PAGAN',
    12.750000,
    2,
    0.001700,
    '{"purpose":"Testing constant error variance","method":"LM"}'
),
(
    1,
    'JARQUE_BERA',
    15.420000,
    2,
    0.000450,
    '{"purpose":"Testing residual normality"}'
);

-- ---------------------------------------------------------------------------
-- Diagnostic policy evaluation
-- ---------------------------------------------------------------------------

INSERT INTO diagnostic_result (
    model_id,
    policy_id,
    category,
    subject_reference,
    statistic,
    threshold,
    p_value,
    severity,
    explanation
)
SELECT
    1,
    1,
    'MULTICOLLINEARITY',
    p.predictor_name,
    pd.vif,
    dp.vif_warning,
    NULL,
    CASE
        WHEN pd.vif >= dp.vif_critical THEN 'FAIL'
        WHEN pd.vif >= dp.vif_warning THEN 'WARNING'
        ELSE 'PASS'
    END,
    'Variance inflation factor indicates predictor redundancy.'
FROM predictor_diagnostic pd
JOIN model_predictor p
    ON p.predictor_id = pd.predictor_id
JOIN diagnostic_policy dp
    ON dp.policy_id = 1
WHERE pd.model_id = 1;

INSERT INTO diagnostic_result (
    model_id,
    policy_id,
    category,
    statistic,
    threshold,
    p_value,
    severity,
    explanation
)
SELECT
    1,
    1,
    'HETEROSCEDASTICITY',
    test_statistic,
    0.05,
    p_value,
    CASE
        WHEN p_value < 0.05 THEN 'WARNING'
        ELSE 'PASS'
    END,
    'Breusch-Pagan test evaluates error variance.'
FROM auxiliary_test
WHERE model_id = 1
  AND test_name = 'BREUSCH_PAGAN';

INSERT INTO diagnostic_result (
    model_id,
    policy_id,
    category,
    statistic,
    threshold,
    p_value,
    severity,
    explanation
)
SELECT
    1,
    1,
    'RESIDUAL_NORMALITY',
    test_statistic,
    0.05,
    p_value,
    CASE
        WHEN p_value < 0.05 THEN 'WARNING'
        ELSE 'PASS'
    END,
    'Jarque-Bera test evaluates residual normality.'
FROM auxiliary_test
WHERE model_id = 1
  AND test_name = 'JARQUE_BERA';

-- ---------------------------------------------------------------------------
-- Influence evaluation
-- ---------------------------------------------------------------------------

CALL evaluate_influence(1, 1);

-- ---------------------------------------------------------------------------
-- Workflow completion
-- ---------------------------------------------------------------------------

UPDATE regression_model
SET status = 'DIAGNOSTICS_COMPLETED'
WHERE model_id = 1;

-- ---------------------------------------------------------------------------
-- Retrieval: model metadata
-- ---------------------------------------------------------------------------

SELECT
    model_id,
    model_name,
    status,
    observation_count,
    predictor_count,
    r_squared,
    adjusted_r_squared,
    residual_standard_error
FROM regression_model
ORDER BY model_id;

-- ---------------------------------------------------------------------------
-- Retrieval: coefficient estimates
-- ---------------------------------------------------------------------------

SELECT
    p.predictor_name,
    p.coefficient,
    p.hc3_standard_error,
    p.coefficient / NULLIF(p.hc3_standard_error, 0)
        AS hc3_test_ratio
FROM model_predictor p
WHERE p.model_id = 1
ORDER BY p.predictor_order;

-- ---------------------------------------------------------------------------
-- Multicollinearity: VIF assessment
-- ---------------------------------------------------------------------------

SELECT
    p.predictor_name,
    pd.vif,
    CASE
        WHEN pd.vif >= dp.vif_critical THEN 'CRITICAL'
        WHEN pd.vif >= dp.vif_warning THEN 'ELEVATED'
        ELSE 'ACCEPTABLE'
    END AS interpretation
FROM predictor_diagnostic pd
JOIN model_predictor p
    ON p.predictor_id = pd.predictor_id
JOIN diagnostic_policy dp
    ON dp.policy_id = 1
WHERE pd.model_id = 1
ORDER BY pd.vif DESC;

-- ---------------------------------------------------------------------------
-- Residual analysis
-- ---------------------------------------------------------------------------

SELECT *
FROM residual_summary(1);

SELECT
    external_reference,
    actual_value,
    fitted_value,
    residual,
    squared_residual
FROM observation_residual_report
WHERE model_id = 1
ORDER BY ABS(residual) DESC
LIMIT 15;

-- ---------------------------------------------------------------------------
-- Heteroscedasticity test retrieval
-- ---------------------------------------------------------------------------

SELECT
    test_name,
    test_statistic,
    degrees_of_freedom,
    p_value,
    CASE
        WHEN p_value < 0.05 THEN
            'Evidence against constant variance'
        ELSE
            'No statistically significant evidence'
    END AS interpretation
FROM auxiliary_test
WHERE model_id = 1
ORDER BY evaluated_at;

-- ---------------------------------------------------------------------------
-- Influence analysis
-- ---------------------------------------------------------------------------

SELECT
    o.external_reference,
    im.leverage,
    im.studentized_residual,
    im.cooks_distance,
    CASE
        WHEN im.cooks_distance > 4.0 / 80
            THEN 'INFLUENTIAL'
        WHEN im.leverage > 2.0 * 3.0 / 80
            THEN 'HIGH LEVERAGE'
        WHEN ABS(im.studentized_residual) > 3
            THEN 'LARGE RESIDUAL'
        ELSE 'WITHIN SCREENING LIMITS'
    END AS influence_assessment
FROM observation o
JOIN influence_measure im
    ON im.observation_id = o.observation_id
WHERE o.model_id = 1
ORDER BY im.cooks_distance DESC;

-- ---------------------------------------------------------------------------
-- Aggregation: diagnostic status counts
-- ---------------------------------------------------------------------------

SELECT
    category,
    severity,
    COUNT(*) AS finding_count
FROM diagnostic_result
WHERE model_id = 1
GROUP BY category, severity
ORDER BY category, severity;

-- ---------------------------------------------------------------------------
-- Model-level reporting
-- ---------------------------------------------------------------------------

SELECT *
FROM model_quality_report
WHERE model_id = 1;

-- ---------------------------------------------------------------------------
-- Eligibility determination
-- ---------------------------------------------------------------------------

SELECT
    model_id,
    model_name,
    status,
    is_model_eligible(model_id) AS merge_or_release_eligible
FROM regression_model
WHERE model_id = 1;

-- ---------------------------------------------------------------------------
-- Validation query: missing fitted values
-- ---------------------------------------------------------------------------

SELECT
    external_reference,
    actual_value
FROM observation
WHERE model_id = 1
  AND status = 'ACTIVE'
  AND fitted_value IS NULL;

-- ---------------------------------------------------------------------------
-- Validation query: predictor completeness
-- ---------------------------------------------------------------------------

SELECT
    o.external_reference,
    COUNT(v.predictor_id) AS recorded_predictors,
    m.predictor_count AS required_predictors
FROM observation o
JOIN regression_model m
    ON m.model_id = o.model_id
LEFT JOIN observation_predictor_value v
    ON v.observation_id = o.observation_id
WHERE o.model_id = 1
  AND o.status = 'ACTIVE'
GROUP BY
    o.observation_id,
    o.external_reference,
    m.predictor_count
HAVING COUNT(v.predictor_id) <> m.predictor_count;

-- ---------------------------------------------------------------------------
-- Transaction demonstration: controlled exclusion of an observation
-- ---------------------------------------------------------------------------

BEGIN;

UPDATE observation
SET status = 'UNDER_REVIEW'
WHERE model_id = 1
  AND external_reference = 'OBS-072';

SELECT
    external_reference,
    status
FROM observation
WHERE model_id = 1
  AND external_reference = 'OBS-072';

-- Commit only after an authorized review decision.
-- This demonstration rolls back to preserve the original sample.

ROLLBACK;

-- ---------------------------------------------------------------------------
-- Concurrency and integrity guidance:
--
-- 1. Use SELECT ... FOR UPDATE when changing model lifecycle states.
-- 2. Use SERIALIZABLE isolation for sensitive multi-step recalculations.
-- 3. Store model version identifiers when coefficients are recalculated.
-- 4. Preserve original observations when investigating influential points.
-- 5. Keep supplied test statistics traceable to the numerical engine.
-- 6. Do not treat an illustrative VIF or influence value as an independently
--    calculated database result.
-- 7. Restrict direct modification of diagnostic_result in production.
-- ---------------------------------------------------------------------------

RESET search_path;
