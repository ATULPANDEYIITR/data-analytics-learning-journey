/*
===============================================================================
REGRESSION FUNDAMENTALS
Simple Linear Regression, Coefficients, Residuals, R-squared and Assumptions
PostgreSQL 15+

Database workflow:
    Dataset
       |
    Observations
       |
    Regression Model
       |
    OLS Coefficients
       |
    Predictions
       |
    Residuals
       |
    Evaluation Metrics
       |
    Assumption Diagnostics
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS regression_lab;

SET search_path TO regression_lab, public;

-- ============================================================================
-- 1. DOMAIN TYPES
-- ============================================================================

CREATE TYPE model_status AS ENUM (
    'created',
    'fitted',
    'failed'
);

CREATE TYPE diagnostic_category AS ENUM (
    'linearity',
    'independence',
    'homoscedasticity',
    'normality'
);

-- ============================================================================
-- 2. DATASETS
-- ============================================================================

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT NOT NULL,

    predictor_name VARCHAR(100) NOT NULL,

    response_name VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(dataset_name)) > 0),

    CHECK (length(trim(predictor_name)) > 0),

    CHECK (length(trim(response_name)) > 0),

    CHECK (predictor_name <> response_name)
);

CREATE TABLE observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,

    observation_number INTEGER NOT NULL,

    predictor_x DOUBLE PRECISION NOT NULL,

    response_y DOUBLE PRECISION NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dataset_id, observation_number),

    CHECK (observation_number > 0),

    CHECK (
        predictor_x NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    ),

    CHECK (
        response_y NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE INDEX idx_observations_dataset
    ON observations(dataset_id, observation_number);

CREATE INDEX idx_observations_predictor
    ON observations(dataset_id, predictor_x);

-- ============================================================================
-- 3. MODEL REGISTRY
-- ============================================================================

CREATE TABLE regression_models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE RESTRICT,

    model_name VARCHAR(150) NOT NULL,

    algorithm VARCHAR(50) NOT NULL DEFAULT 'ordinary_least_squares',

    status model_status NOT NULL DEFAULT 'created',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fitted_at TIMESTAMPTZ,

    UNIQUE(dataset_id, model_name),

    CHECK (length(trim(model_name)) > 0),

    CHECK (algorithm = 'ordinary_least_squares'),

    CHECK (
        (status = 'fitted' AND fitted_at IS NOT NULL)
        OR
        (status <> 'fitted')
    )
);

CREATE INDEX idx_models_status
    ON regression_models(status, created_at DESC);

-- ============================================================================
-- 4. COEFFICIENTS
-- ============================================================================

CREATE TABLE model_coefficients (
    model_id BIGINT PRIMARY KEY
        REFERENCES regression_models(model_id)
        ON DELETE CASCADE,

    intercept DOUBLE PRECISION NOT NULL,

    slope DOUBLE PRECISION NOT NULL,

    x_mean DOUBLE PRECISION NOT NULL,

    y_mean DOUBLE PRECISION NOT NULL,

    sxx DOUBLE PRECISION NOT NULL,

    sse DOUBLE PRECISION NOT NULL,

    syy DOUBLE PRECISION NOT NULL,

    observations_count INTEGER NOT NULL,

    fitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (sxx > 0),

    CHECK (sse >= 0),

    CHECK (syy >= 0),

    CHECK (observations_count >= 3),

    CHECK (
        intercept NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    ),

    CHECK (
        slope NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

-- ============================================================================
-- 5. PREDICTIONS AND RESIDUALS
-- ============================================================================

CREATE TABLE model_predictions (
    prediction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES regression_models(model_id)
        ON DELETE CASCADE,

    observation_id BIGINT NOT NULL
        REFERENCES observations(observation_id)
        ON DELETE CASCADE,

    actual_value DOUBLE PRECISION NOT NULL,

    predicted_value DOUBLE PRECISION NOT NULL,

    residual DOUBLE PRECISION NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model_id, observation_id),

    CHECK (
        abs(
            residual - (actual_value - predicted_value)
        ) < 1e-8
    )
);

CREATE INDEX idx_predictions_model
    ON model_predictions(model_id);

CREATE INDEX idx_predictions_residual
    ON model_predictions(model_id, residual);

-- ============================================================================
-- 6. EVALUATION METRICS
-- ============================================================================

CREATE TABLE model_metrics (
    model_id BIGINT PRIMARY KEY
        REFERENCES regression_models(model_id)
        ON DELETE CASCADE,

    mae DOUBLE PRECISION NOT NULL,

    mse DOUBLE PRECISION NOT NULL,

    rmse DOUBLE PRECISION NOT NULL,

    r_squared DOUBLE PRECISION NOT NULL,

    adjusted_r_squared DOUBLE PRECISION NOT NULL,

    residual_standard_error DOUBLE PRECISION NOT NULL,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (mae >= 0),

    CHECK (mse >= 0),

    CHECK (rmse >= 0),

    CHECK (residual_standard_error >= 0),

    CHECK (
        r_squared NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    ),

    CHECK (
        adjusted_r_squared NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

-- ============================================================================
-- 7. ASSUMPTION DIAGNOSTICS
-- ============================================================================

CREATE TABLE assumption_diagnostics (
    diagnostic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES regression_models(model_id)
        ON DELETE CASCADE,

    category diagnostic_category NOT NULL,

    statistic DOUBLE PRECISION NOT NULL,

    threshold DOUBLE PRECISION,

    indicator_passed BOOLEAN NOT NULL,

    interpretation TEXT NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        statistic NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    ),

    UNIQUE(model_id, category)
);

CREATE INDEX idx_diagnostics_model
    ON assumption_diagnostics(model_id, category);

-- ============================================================================
-- 8. DATASET INTEGRITY TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_observation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.observation_number <= 0 THEN
        RAISE EXCEPTION
            'Observation number must be positive.';
    END IF;

    IF NOT isfinite(NEW.predictor_x)
       OR NOT isfinite(NEW.response_y) THEN
        RAISE EXCEPTION
            'Observation values must be finite.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_observation
BEFORE INSERT OR UPDATE ON observations
FOR EACH ROW
EXECUTE FUNCTION validate_observation();

-- ============================================================================
-- 9. DATASET VALIDATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_dataset(
    p_dataset_id BIGINT
)
RETURNS TABLE (
    observation_count BIGINT,
    distinct_predictors BIGINT,
    predictor_variance DOUBLE PRECISION,
    response_variance DOUBLE PRECISION,
    eligible BOOLEAN,
    validation_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_count BIGINT;
    v_distinct BIGINT;
    v_sxx DOUBLE PRECISION;
    v_syy DOUBLE PRECISION;
BEGIN
    SELECT
        COUNT(*),
        COUNT(DISTINCT predictor_x),
        COALESCE(
            SUM(
                POWER(
                    predictor_x -
                    (SELECT AVG(o2.predictor_x)
                     FROM observations o2
                     WHERE o2.dataset_id = p_dataset_id),
                    2
                )
            ),
            0
        ),
        COALESCE(
            SUM(
                POWER(
                    response_y -
                    (SELECT AVG(o3.response_y)
                     FROM observations o3
                     WHERE o3.dataset_id = p_dataset_id),
                    2
                )
            ),
            0
        )
    INTO v_count, v_distinct, v_sxx, v_syy
    FROM observations
    WHERE dataset_id = p_dataset_id;

    observation_count := v_count;
    distinct_predictors := v_distinct;

    predictor_variance :=
        CASE WHEN v_count > 1
        THEN v_sxx / (v_count - 1)
        ELSE 0 END;

    response_variance :=
        CASE WHEN v_count > 1
        THEN v_syy / (v_count - 1)
        ELSE 0 END;

    eligible := v_count >= 3 AND v_sxx > 1e-12;

    validation_message :=
        CASE
            WHEN v_count < 3
                THEN 'At least three observations are required.'
            WHEN v_sxx <= 1e-12
                THEN 'Predictor variance is insufficient.'
            ELSE 'Dataset is eligible for simple linear regression.'
        END;

    RETURN NEXT;
END;
$$;

-- ============================================================================
-- 10. ORDINARY LEAST SQUARES FITTING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE fit_regression(
    p_model_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_dataset_id BIGINT;

    v_n INTEGER;

    v_x_mean DOUBLE PRECISION;
    v_y_mean DOUBLE PRECISION;

    v_sxx DOUBLE PRECISION;
    v_sxy DOUBLE PRECISION;
    v_syy DOUBLE PRECISION;

    v_slope DOUBLE PRECISION;
    v_intercept DOUBLE PRECISION;

    v_sse DOUBLE PRECISION;
    v_mae DOUBLE PRECISION;
    v_mse DOUBLE PRECISION;
    v_rmse DOUBLE PRECISION;

    v_r2 DOUBLE PRECISION;
    v_adjusted_r2 DOUBLE PRECISION;

    v_residual_se DOUBLE PRECISION;
BEGIN
    SELECT dataset_id
    INTO v_dataset_id
    FROM regression_models
    WHERE model_id = p_model_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Regression model % does not exist.',
            p_model_id;
    END IF;

    SELECT
        COUNT(*)::INTEGER,
        AVG(predictor_x),
        AVG(response_y),
        SUM(POWER(predictor_x - avg_x, 2)),
        SUM((predictor_x - avg_x) * (response_y - avg_y)),
        SUM(POWER(response_y - avg_y, 2))
    INTO
        v_n,
        v_x_mean,
        v_y_mean,
        v_sxx,
        v_sxy,
        v_syy
    FROM (
        SELECT
            predictor_x,
            response_y,
            AVG(predictor_x) OVER () AS avg_x,
            AVG(response_y) OVER () AS avg_y
        FROM observations
        WHERE dataset_id = v_dataset_id
    ) AS centered;

    IF v_n < 3 THEN
        RAISE EXCEPTION
            'At least three observations are required.';
    END IF;

    IF v_sxx <= 1e-12 THEN
        RAISE EXCEPTION
            'Predictor variance is insufficient.';
    END IF;

    -- OLS coefficient formulas.
    v_slope := v_sxy / v_sxx;

    v_intercept := v_y_mean - v_slope * v_x_mean;

    -- Replace old predictions within the same transaction.
    DELETE FROM model_predictions
    WHERE model_id = p_model_id;

    INSERT INTO model_predictions (
        model_id,
        observation_id,
        actual_value,
        predicted_value,
        residual
    )
    SELECT
        p_model_id,
        observation_id,
        response_y,
        v_intercept + v_slope * predictor_x,
        response_y - (v_intercept + v_slope * predictor_x)
    FROM observations
    WHERE dataset_id = v_dataset_id;

    SELECT
        SUM(POWER(residual, 2)),
        AVG(ABS(residual))
    INTO v_sse, v_mae
    FROM model_predictions
    WHERE model_id = p_model_id;

    v_mse := v_sse / v_n;

    v_rmse := SQRT(v_mse);

    v_r2 :=
        CASE
            WHEN v_syy > 1e-12
                THEN 1 - v_sse / v_syy
            WHEN v_sse <= 1e-12
                THEN 1
            ELSE 0
        END;

    v_adjusted_r2 :=
        1 - (1 - v_r2) * (v_n - 1.0) / (v_n - 2.0);

    v_residual_se := SQRT(v_sse / (v_n - 2.0));

    INSERT INTO model_coefficients (
        model_id,
        intercept,
        slope,
        x_mean,
        y_mean,
        sxx,
        sse,
        syy,
        observations_count
    )
    VALUES (
        p_model_id,
        v_intercept,
        v_slope,
        v_x_mean,
        v_y_mean,
        v_sxx,
        v_sse,
        v_syy,
        v_n
    )
    ON CONFLICT (model_id)
    DO UPDATE SET
        intercept = EXCLUDED.intercept,
        slope = EXCLUDED.slope,
        x_mean = EXCLUDED.x_mean,
        y_mean = EXCLUDED.y_mean,
        sxx = EXCLUDED.sxx,
        sse = EXCLUDED.sse,
        syy = EXCLUDED.syy,
        observations_count = EXCLUDED.observations_count,
        fitted_at = CURRENT_TIMESTAMP;

    INSERT INTO model_metrics (
        model_id,
        mae,
        mse,
        rmse,
        r_squared,
        adjusted_r_squared,
        residual_standard_error
    )
    VALUES (
        p_model_id,
        v_mae,
        v_mse,
        v_rmse,
        v_r2,
        v_adjusted_r2,
        v_residual_se
    )
    ON CONFLICT (model_id)
    DO UPDATE SET
        mae = EXCLUDED.mae,
        mse = EXCLUDED.mse,
        rmse = EXCLUDED.rmse,
        r_squared = EXCLUDED.r_squared,
        adjusted_r_squared = EXCLUDED.adjusted_r_squared,
        residual_standard_error = EXCLUDED.residual_standard_error,
        calculated_at = CURRENT_TIMESTAMP;

    UPDATE regression_models
    SET
        status = 'fitted',
        fitted_at = CURRENT_TIMESTAMP
    WHERE model_id = p_model_id;

    -- These are descriptive indicators, not formal assumption tests.
    DELETE FROM assumption_diagnostics
    WHERE model_id = p_model_id;

    INSERT INTO assumption_diagnostics (
        model_id,
        category,
        statistic,
        threshold,
        indicator_passed,
        interpretation
    )
    SELECT
        p_model_id,
        'linearity',
        ABS(AVG(residual)),
        1e-8,
        ABS(AVG(residual)) < 1e-8,
        'OLS with an intercept produces approximately zero mean residuals.'
    FROM model_predictions
    WHERE model_id = p_model_id

    UNION ALL

    SELECT
        p_model_id,
        'independence',
        COALESCE(
            ABS(
                SUM(
                    current_row.residual * previous_row.residual
                ) /
                NULLIF(
                    SUM(current_row.residual * current_row.residual),
                    0
                )
            ),
            0
        ),
        0.3,
        COALESCE(
            ABS(
                SUM(
                    current_row.residual * previous_row.residual
                ) /
                NULLIF(
                    SUM(current_row.residual * current_row.residual),
                    0
                )
            ),
            0
        ) < 0.3,
        'Lag-one residual correlation is a descriptive indicator.'
    FROM model_predictions current_row
    LEFT JOIN model_predictions previous_row
        ON previous_row.model_id = current_row.model_id
        AND previous_row.observation_id =
            current_row.observation_id - 1
    WHERE current_row.model_id = p_model_id

    UNION ALL

    SELECT
        p_model_id,
        'normality',
        COALESCE(
            ABS(
                SUM(
                    POWER(
                        residual - residual_mean,
                        3
                    )
                ) /
                NULLIF(
                    COUNT(*) * POWER(residual_sd, 3),
                    0
                )
            ),
            0
        ),
        1.0,
        COALESCE(
            ABS(
                SUM(
                    POWER(
                        residual - residual_mean,
                        3
                    )
                ) /
                NULLIF(
                    COUNT(*) * POWER(residual_sd, 3),
                    0
                )
            ),
            0
        ) < 1.0,
        'Absolute residual skewness is a descriptive normality indicator.'
    FROM (
        SELECT
            residual,
            AVG(residual) OVER () AS residual_mean,
            STDDEV_SAMP(residual) OVER () AS residual_sd
        FROM model_predictions
        WHERE model_id = p_model_id
    ) residual_data

    ON CONFLICT (model_id, category)
    DO UPDATE SET
        statistic = EXCLUDED.statistic,
        threshold = EXCLUDED.threshold,
        indicator_passed = EXCLUDED.indicator_passed,
        interpretation = EXCLUDED.interpretation,
        evaluated_at = CURRENT_TIMESTAMP;

    -- Heteroscedasticity indicator based on fitted-value halves.
    WITH ranked AS (
        SELECT
            residual,
            NTILE(2) OVER (ORDER BY predicted_value) AS group_number
        FROM model_predictions
        WHERE model_id = p_model_id
    ),
    group_variances AS (
        SELECT
            group_number,
            VAR_SAMP(residual) AS residual_variance
        FROM ranked
        GROUP BY group_number
    ),
    ratio AS (
        SELECT
            COALESCE(
                MAX(residual_variance) /
                NULLIF(MIN(residual_variance), 0),
                0
            ) AS variance_ratio
        FROM group_variances
    )
    INSERT INTO assumption_diagnostics (
        model_id,
        category,
        statistic,
        threshold,
        indicator_passed,
        interpretation
    )
    SELECT
        p_model_id,
        'homoscedasticity',
        variance_ratio,
        4.0,
        variance_ratio < 4.0,
        'Compares residual variance across fitted-value groups.'
    FROM ratio
    ON CONFLICT (model_id, category)
    DO UPDATE SET
        statistic = EXCLUDED.statistic,
        threshold = EXCLUDED.threshold,
        indicator_passed = EXCLUDED.indicator_passed,
        interpretation = EXCLUDED.interpretation,
        evaluated_at = CURRENT_TIMESTAMP;

END;
$$;

-- ============================================================================
-- 11. PREDICTION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION predict_value(
    p_model_id BIGINT,
    p_x DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_intercept DOUBLE PRECISION;
    v_slope DOUBLE PRECISION;
BEGIN
    IF NOT isfinite(p_x) THEN
        RAISE EXCEPTION
            'Prediction input must be finite.';
    END IF;

    SELECT intercept, slope
    INTO v_intercept, v_slope
    FROM model_coefficients
    WHERE model_id = p_model_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Model coefficients are unavailable.';
    END IF;

    RETURN v_intercept + v_slope * p_x;
END;
$$;

-- ============================================================================
-- 12. REPORTING VIEW
-- ============================================================================

CREATE OR REPLACE VIEW regression_model_report AS
SELECT
    m.model_id,
    m.model_name,
    m.status,
    d.dataset_name,
    d.predictor_name,
    d.response_name,

    c.intercept,
    c.slope,
    c.observations_count,

    metrics.mae,
    metrics.mse,
    metrics.rmse,
    metrics.r_squared,
    metrics.adjusted_r_squared,
    metrics.residual_standard_error,

    c.fitted_at

FROM regression_models m

JOIN datasets d
    ON d.dataset_id = m.dataset_id

LEFT JOIN model_coefficients c
    ON c.model_id = m.model_id

LEFT JOIN model_metrics metrics
    ON metrics.model_id = m.model_id;

-- ============================================================================
-- 13. RESIDUAL REPORT VIEW
-- ============================================================================

CREATE OR REPLACE VIEW residual_report AS
SELECT
    m.model_name,
    o.observation_number,
    o.predictor_x,
    p.actual_value,
    p.predicted_value,
    p.residual,
    ABS(p.residual) AS absolute_residual,
    POWER(p.residual, 2) AS squared_residual

FROM model_predictions p

JOIN regression_models m
    ON m.model_id = p.model_id

JOIN observations o
    ON o.observation_id = p.observation_id;

-- ============================================================================
-- 14. SAMPLE DATA
-- ============================================================================

INSERT INTO datasets (
    dataset_name,
    description,
    predictor_name,
    response_name
)
VALUES
(
    'Student Examination Performance',
    'Relationship between study hours and examination marks.',
    'study_hours',
    'exam_score'
),
(
    'Constant Predictor Failure',
    'Dataset demonstrating insufficient predictor variance.',
    'constant_input',
    'observed_output'
),
(
    'Business Advertising Performance',
    'Advertising expenditure and sales revenue.',
    'advertising_spend',
    'sales_revenue'
);

INSERT INTO observations (
    dataset_id,
    observation_number,
    predictor_x,
    response_y
)
SELECT
    d.dataset_id,
    sample.observation_number,
    sample.x,
    sample.y
FROM datasets d
CROSS JOIN (
    VALUES
        (1, 1.0, 42.0),
        (2, 2.0, 46.0),
        (3, 3.0, 53.0),
        (4, 4.0, 57.0),
        (5, 5.0, 61.0),
        (6, 6.0, 68.0),
        (7, 7.0, 72.0),
        (8, 8.0, 79.0)
) AS sample(observation_number, x, y)
WHERE d.dataset_name = 'Student Examination Performance';

INSERT INTO observations (
    dataset_id,
    observation_number,
    predictor_x,
    response_y
)
SELECT
    d.dataset_id,
    sample.observation_number,
    sample.x,
    sample.y
FROM datasets d
CROSS JOIN (
    VALUES
        (1, 5.0, 10.0),
        (2, 5.0, 12.0),
        (3, 5.0, 15.0)
) AS sample(observation_number, x, y)
WHERE d.dataset_name = 'Constant Predictor Failure';

INSERT INTO observations (
    dataset_id,
    observation_number,
    predictor_x,
    response_y
)
SELECT
    d.dataset_id,
    sample.observation_number,
    sample.x,
    sample.y
FROM datasets d
CROSS JOIN (
    VALUES
        (1, 100.0, 200.0),
        (2, 200.0, 390.0),
        (3, 300.0, 610.0),
        (4, 400.0, 790.0),
        (5, 500.0, 1030.0),
        (6, 600.0, 1190.0)
) AS sample(observation_number, x, y)
WHERE d.dataset_name = 'Business Advertising Performance';

INSERT INTO regression_models (
    dataset_id,
    model_name
)
SELECT
    dataset_id,
    'OLS examination model'
FROM datasets
WHERE dataset_name = 'Student Examination Performance';

INSERT INTO regression_models (
    dataset_id,
    model_name
)
SELECT
    dataset_id,
    'OLS constant predictor failure'
FROM datasets
WHERE dataset_name = 'Constant Predictor Failure';

INSERT INTO regression_models (
    dataset_id,
    model_name
)
SELECT
    dataset_id,
    'OLS advertising model'
FROM datasets
WHERE dataset_name = 'Business Advertising Performance';

-- ============================================================================
-- 15. EXECUTE VALID MODELS
-- ============================================================================

CALL fit_regression(
    (
        SELECT model_id
        FROM regression_models
        WHERE model_name = 'OLS examination model'
    )
);

CALL fit_regression(
    (
        SELECT model_id
        FROM regression_models
        WHERE model_name = 'OLS advertising model'
    )
);

-- ============================================================================
-- 16. RETRIEVAL QUERIES
-- ============================================================================

SELECT *
FROM regression_model_report
ORDER BY model_id;

SELECT *
FROM residual_report
ORDER BY model_name, observation_number;

-- ============================================================================
-- 17. VALIDATION QUERY
-- ============================================================================

SELECT
    d.dataset_name,
    validation.observation_count,
    validation.distinct_predictors,
    validation.predictor_variance,
    validation.response_variance,
    validation.eligible,
    validation.validation_message

FROM datasets d

CROSS JOIN LATERAL validate_dataset(d.dataset_id) validation

ORDER BY d.dataset_id;

-- ============================================================================
-- 18. EVALUATION AND AGGREGATION
-- ============================================================================

SELECT
    model_name,
    observations_count,
    ROUND(intercept::NUMERIC, 4) AS intercept,
    ROUND(slope::NUMERIC, 4) AS slope,
    ROUND(r_squared::NUMERIC, 4) AS r_squared,
    ROUND(adjusted_r_squared::NUMERIC, 4) AS adjusted_r_squared,
    ROUND(rmse::NUMERIC, 4) AS rmse

FROM regression_model_report

WHERE status = 'fitted';

-- Mean absolute residual and maximum prediction error.
SELECT
    model_name,
    COUNT(*) AS prediction_count,
    AVG(absolute_residual) AS mean_absolute_residual,
    MAX(absolute_residual) AS maximum_absolute_residual,
    AVG(squared_residual) AS mean_squared_residual

FROM residual_report

GROUP BY model_name
ORDER BY model_name;

-- ============================================================================
-- 19. ASSUMPTION REPORT
-- ============================================================================

SELECT
    m.model_name,
    d.category,
    d.statistic,
    d.threshold,
    d.indicator_passed,
    d.interpretation

FROM assumption_diagnostics d

JOIN regression_models m
    ON m.model_id = d.model_id

ORDER BY m.model_name, d.category;

-- ============================================================================
-- 20. ELIGIBILITY DETERMINATION
-- ============================================================================

SELECT
    m.model_name,

    CASE
        WHEN m.status <> 'fitted'
            THEN 'NOT FITTED'

        WHEN c.observations_count < 3
            THEN 'INSUFFICIENT DATA'

        WHEN c.sxx <= 1e-12
            THEN 'INVALID PREDICTOR'

        ELSE 'MODEL FIT COMPLETED'
    END AS fitting_eligibility,

    metrics.r_squared,
    metrics.rmse

FROM regression_models m

LEFT JOIN model_coefficients c
    ON c.model_id = m.model_id

LEFT JOIN model_metrics metrics
    ON metrics.model_id = m.model_id

ORDER BY m.model_id;

-- ============================================================================
-- 21. PREDICTION EXAMPLE
-- ============================================================================

SELECT
    9.0 AS study_hours,
    predict_value(
        (
            SELECT model_id
            FROM regression_models
            WHERE model_name = 'OLS examination model'
        ),
        9.0
    ) AS predicted_exam_score;

-- ============================================================================
-- 22. FAILURE HANDLING
-- ============================================================================

-- This query deliberately identifies a dataset that cannot be fitted.
SELECT
    d.dataset_name,
    validation.eligible,
    validation.validation_message

FROM datasets d

CROSS JOIN LATERAL validate_dataset(d.dataset_id) validation

WHERE d.dataset_name = 'Constant Predictor Failure';

-- A fitting attempt on the constant predictor would raise an exception.
-- Execute the following independently if a failure demonstration is needed:
--
-- CALL fit_regression(
--     (
--         SELECT model_id
--         FROM regression_models
--         WHERE model_name = 'OLS constant predictor failure'
--     )
-- );
--
-- PostgreSQL rolls back the failed procedure statement automatically.

COMMIT;

===============================================================================
TRANSACTION AND PERFORMANCE NOTES

1. Model fitting is executed inside a transaction.
2. Predictions and metrics are replaced atomically.
3. Foreign keys maintain dataset and model relationships.
4. Unique constraints prevent duplicate observations and predictions.
5. Composite indexes support dataset and model retrieval.
6. The regression procedure uses centered sums for OLS calculations.
7. The model report separates coefficients from evaluation metrics.
8. Diagnostic indicators are not substitutes for formal statistical tests.
9. Model predictions are in-sample predictions, not independent test results.
10. Production systems should version datasets and preserve model snapshots.
===============================================================================
*/
