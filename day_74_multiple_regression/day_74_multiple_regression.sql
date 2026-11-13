-- ============================================================
-- MULTIPLE REGRESSION
-- PostgreSQL 14+
--
-- Relational regression workflow:
--   Dataset -> Observations -> Model specification
--   -> Feature encoding -> OLS estimation -> Diagnostics
--   -> Predictions -> Reporting
--
-- Implements OLS using PostgreSQL PL/pgSQL and arrays.
-- Supports:
--   Numerical predictors
--   Categorical predictors
--   Reference-category dummy variables
--   Numerical interaction terms
--   Model coefficients and predictions
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS regression_lab;

DROP SCHEMA IF EXISTS regression_lab CASCADE;
CREATE SCHEMA regression_lab;

SET search_path TO regression_lab, public;

-- ------------------------------------------------------------
-- 1. DATA DOMAIN
-- ------------------------------------------------------------

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    salary NUMERIC(14,2) NOT NULL CHECK (salary >= 0),
    experience NUMERIC(8,2) NOT NULL CHECK (experience >= 0),
    performance NUMERIC(8,2) NOT NULL CHECK (performance >= 0),
    education VARCHAR(50) NOT NULL,
    department VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(education)) > 0),
    CHECK (length(trim(department)) > 0)
);

CREATE INDEX idx_employees_dataset
ON employees(dataset_id);

CREATE INDEX idx_employees_department
ON employees(dataset_id, department);

CREATE INDEX idx_employees_education
ON employees(dataset_id, education);

-- ------------------------------------------------------------
-- 2. MODEL CONFIGURATION
-- ------------------------------------------------------------

CREATE TYPE model_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'FITTED',
    'FAILED'
);

CREATE TABLE regression_models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    model_name VARCHAR(150) NOT NULL,
    target_variable VARCHAR(80) NOT NULL DEFAULT 'salary',
    status model_status NOT NULL DEFAULT 'CREATED',
    observation_count INTEGER,
    parameter_count INTEGER,
    r_squared DOUBLE PRECISION,
    adjusted_r_squared DOUBLE PRECISION,
    rmse DOUBLE PRECISION,
    mae DOUBLE PRECISION,
    residual_sum_squares DOUBLE PRECISION,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fitted_at TIMESTAMPTZ,
    UNIQUE(dataset_id, model_name),
    CHECK (
        observation_count IS NULL OR observation_count >= 0
    ),
    CHECK (
        parameter_count IS NULL OR parameter_count > 0
    )
);

CREATE TABLE model_terms (
    term_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_models(model_id)
        ON DELETE CASCADE,
    term_name VARCHAR(200) NOT NULL,
    term_type VARCHAR(30) NOT NULL CHECK (
        term_type IN (
            'INTERCEPT',
            'NUMERICAL',
            'CATEGORICAL',
            'INTERACTION'
        )
    ),
    coefficient DOUBLE PRECISION NOT NULL,
    standard_error DOUBLE PRECISION,
    UNIQUE(model_id, term_name)
);

CREATE TABLE model_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_models(model_id)
        ON DELETE CASCADE,
    variable_name VARCHAR(80) NOT NULL,
    category_value VARCHAR(100) NOT NULL,
    is_reference BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(model_id, variable_name, category_value)
);

CREATE TABLE model_predictions (
    prediction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_models(model_id)
        ON DELETE CASCADE,
    employee_id BIGINT NOT NULL REFERENCES employees(employee_id),
    actual_value DOUBLE PRECISION NOT NULL,
    predicted_value DOUBLE PRECISION NOT NULL,
    residual DOUBLE PRECISION NOT NULL,
    UNIQUE(model_id, employee_id)
);

-- ------------------------------------------------------------
-- 3. INTERACTION SPECIFICATIONS
-- ------------------------------------------------------------

CREATE TABLE model_interactions (
    interaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES regression_models(model_id)
        ON DELETE CASCADE,
    first_variable VARCHAR(80) NOT NULL,
    second_variable VARCHAR(80) NOT NULL,
    UNIQUE(model_id, first_variable, second_variable),
    CHECK (first_variable <> second_variable),
    CHECK (
        first_variable IN ('experience', 'performance')
    ),
    CHECK (
        second_variable IN ('experience', 'performance')
    )
);

-- ------------------------------------------------------------
-- 4. SAMPLE DATASET
-- ------------------------------------------------------------

INSERT INTO datasets(dataset_name, description)
VALUES (
    'employee_compensation',
    'Employee compensation explained by experience, performance, education and department.'
);

INSERT INTO employees (
    dataset_id,
    salary,
    experience,
    performance,
    education,
    department
)
SELECT
    d.dataset_id,
    v.salary,
    v.experience,
    v.performance,
    v.education,
    v.department
FROM datasets d
CROSS JOIN (
    VALUES
    (45000,1,3,'Bachelor','Sales'),
    (49000,2,4,'Bachelor','Sales'),
    (53000,3,3,'Master','Sales'),
    (57000,4,4,'Master','Technology'),
    (65000,5,5,'Master','Technology'),
    (61000,4,5,'Bachelor','Technology'),
    (72000,6,4,'PhD','Technology'),
    (76000,7,5,'PhD','Technology'),
    (50000,2,3,'Bachelor','Operations'),
    (55000,3,4,'Master','Operations'),
    (59000,4,4,'Bachelor','Operations'),
    (68000,6,5,'PhD','Operations'),
    (48000,2,2,'Bachelor','Sales'),
    (62000,5,4,'Master','Sales'),
    (70000,6,5,'PhD','Technology'),
    (54000,3,3,'Bachelor','Operations'),
    (74000,7,5,'Master','Technology'),
    (58000,4,3,'Master','Sales'),
    (64000,5,5,'Bachelor','Operations'),
    (79000,8,5,'PhD','Technology')
) AS v(salary, experience, performance, education, department)
ON d.dataset_name = 'employee_compensation';

-- ------------------------------------------------------------
-- 5. MODEL SPECIFICATION
-- ------------------------------------------------------------

INSERT INTO regression_models (
    dataset_id,
    model_name
)
SELECT dataset_id, 'employee_salary_ols'
FROM datasets
WHERE dataset_name = 'employee_compensation';

INSERT INTO model_interactions (
    model_id,
    first_variable,
    second_variable
)
SELECT model_id, 'experience', 'performance'
FROM regression_models
WHERE model_name = 'employee_salary_ols';

-- ------------------------------------------------------------
-- 6. MATRIX SOLVER
--
-- Gaussian elimination with partial pivoting.
-- Arrays are one-dimensional vectors.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION solve_ols_system(
    matrix_input DOUBLE PRECISION[][],
    vector_input DOUBLE PRECISION[]
)
RETURNS DOUBLE PRECISION[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    n INTEGER := cardinality(vector_input);
    a DOUBLE PRECISION[][];
    result DOUBLE PRECISION[];
    pivot INTEGER;
    factor DOUBLE PRECISION;
    divisor DOUBLE PRECISION;
    temp DOUBLE PRECISION;
    i INTEGER;
    j INTEGER;
    k INTEGER;
BEGIN
    IF n = 0 OR array_length(matrix_input, 1) <> n
       OR array_length(matrix_input, 2) <> n THEN
        RAISE EXCEPTION 'Invalid matrix dimensions';
    END IF;

    a := matrix_input;

    result := vector_input;

    FOR k IN 1..n LOOP
        pivot := k;

        FOR i IN k..n LOOP
            IF abs(a[i][k]) > abs(a[pivot][k]) THEN
                pivot := i;
            END IF;
        END LOOP;

        IF abs(a[pivot][k]) < 1e-12 THEN
            RAISE EXCEPTION
                'Singular matrix: multicollinearity detected';
        END IF;

        -- Swap matrix rows.
        FOR j IN 1..n LOOP
            temp := a[k][j];
            a[k][j] := a[pivot][j];
            a[pivot][j] := temp;
        END LOOP;

        -- Swap response elements.
        temp := result[k];
        result[k] := result[pivot];
        result[pivot] := temp;

        divisor := a[k][k];

        FOR j IN k..n LOOP
            a[k][j] := a[k][j] / divisor;
        END LOOP;

        result[k] := result[k] / divisor;

        FOR i IN 1..n LOOP
            IF i <> k THEN
                factor := a[i][k];

                FOR j IN k..n LOOP
                    a[i][j] :=
                        a[i][j] - factor * a[k][j];
                END LOOP;

                result[i] :=
                    result[i] - factor * result[k];
            END IF;
        END LOOP;
    END LOOP;

    RETURN result;
END;
$$;

-- ------------------------------------------------------------
-- 7. MODEL FITTING FUNCTION
--
-- Constructs:
-- X = [intercept, experience, performance,
--      education dummies, department dummies,
--      experience:performance]
--
-- OLS:
-- beta = inverse(X'X) X'y
--
-- Reference levels are selected alphabetically.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION fit_employee_regression(
    p_model_id BIGINT
)
RETURNS TABLE (
    fitted_model_id BIGINT,
    fitted_status model_status,
    fitted_r_squared DOUBLE PRECISION,
    fitted_adjusted_r_squared DOUBLE PRECISION,
    fitted_rmse DOUBLE PRECISION,
    fitted_mae DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_dataset_id BIGINT;
    v_n INTEGER;
    v_p INTEGER;
    v_levels TEXT[];
    v_departments TEXT[];
    v_education TEXT[];
    v_names TEXT[];
    v_types TEXT[];
    v_x DOUBLE PRECISION[][];
    v_xtx DOUBLE PRECISION[][];
    v_xty DOUBLE PRECISION[];
    v_beta DOUBLE PRECISION[];
    v_predictions DOUBLE PRECISION[];
    v_residuals DOUBLE PRECISION[];
    v_y DOUBLE PRECISION[];
    v_mean DOUBLE PRECISION;
    v_sse DOUBLE PRECISION := 0;
    v_sst DOUBLE PRECISION := 0;
    v_mae DOUBLE PRECISION := 0;
    v_r2 DOUBLE PRECISION;
    v_adjusted DOUBLE PRECISION;
    v_rmse DOUBLE PRECISION;
    v_row RECORD;
    v_i INTEGER;
    v_j INTEGER;
    v_k INTEGER;
    v_col INTEGER;
    v_value DOUBLE PRECISION;
    v_education_reference TEXT;
    v_department_reference TEXT;
    v_error TEXT;
BEGIN
    SELECT dataset_id
    INTO v_dataset_id
    FROM regression_models
    WHERE model_id = p_model_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown model ID: %', p_model_id;
    END IF;

    UPDATE regression_models
    SET status = 'VALIDATED',
        error_message = NULL
    WHERE model_id = p_model_id;

    SELECT COUNT(*)
    INTO v_n
    FROM employees
    WHERE dataset_id = v_dataset_id;

    SELECT ARRAY_AGG(level ORDER BY level)
    INTO v_education
    FROM (
        SELECT DISTINCT education AS level
        FROM employees
        WHERE dataset_id = v_dataset_id
    ) categories;

    SELECT ARRAY_AGG(level ORDER BY level)
    INTO v_departments
    FROM (
        SELECT DISTINCT department AS level
        FROM employees
        WHERE dataset_id = v_dataset_id
    ) categories;

    IF cardinality(v_education) < 2
       OR cardinality(v_departments) < 2 THEN
        RAISE EXCEPTION
            'Categorical predictors need at least two levels';
    END IF;

    v_education_reference := v_education[1];
    v_department_reference := v_departments[1];

    v_p := 3
        + cardinality(v_education) - 1
        + cardinality(v_departments) - 1
        + 1;

    IF v_n <= v_p THEN
        RAISE EXCEPTION
            'Insufficient observations: %, parameters: %',
            v_n, v_p;
    END IF;

    v_names := ARRAY[
        'Intercept',
        'experience',
        'performance'
    ];

    v_types := ARRAY[
        'INTERCEPT',
        'NUMERICAL',
        'NUMERICAL'
    ];

    FOR v_i IN 2..cardinality(v_education) LOOP
        v_names := array_append(
            v_names,
            'education[' || v_education[v_i] || ']'
        );

        v_types := array_append(v_types, 'CATEGORICAL');
    END LOOP;

    FOR v_i IN 2..cardinality(v_departments) LOOP
        v_names := array_append(
            v_names,
            'department[' || v_departments[v_i] || ']'
        );

        v_types := array_append(v_types, 'CATEGORICAL');
    END LOOP;

    v_names := array_append(
        v_names,
        'experience:performance'
    );

    v_types := array_append(v_types, 'INTERACTION');

    -- Record category encoding and reference levels.
    DELETE FROM model_categories
    WHERE model_id = p_model_id;

    INSERT INTO model_categories(
        model_id,
        variable_name,
        category_value,
        is_reference
    )
    SELECT
        p_model_id,
        'education',
        level,
        level = v_education_reference
    FROM unnest(v_education) AS level;

    INSERT INTO model_categories(
        model_id,
        variable_name,
        category_value,
        is_reference
    )
    SELECT
        p_model_id,
        'department',
        level,
        level = v_department_reference
    FROM unnest(v_departments) AS level;

    v_x := array_fill(
        0.0::DOUBLE PRECISION,
        ARRAY[v_n, v_p]
    );

    v_y := array_fill(0.0::DOUBLE PRECISION, ARRAY[v_n]);

    v_i := 0;

    FOR v_row IN
        SELECT *
        FROM employees
        WHERE dataset_id = v_dataset_id
        ORDER BY employee_id
    LOOP
        v_i := v_i + 1;
        v_col := 1;

        v_x[v_i][v_col] := 1.0;
        v_col := v_col + 1;

        v_x[v_i][v_col] := v_row.experience;
        v_col := v_col + 1;

        v_x[v_i][v_col] := v_row.performance;
        v_col := v_col + 1;

        FOR v_j IN 2..cardinality(v_education) LOOP
            v_x[v_i][v_col] :=
                CASE
                    WHEN v_row.education = v_education[v_j]
                    THEN 1.0
                    ELSE 0.0
                END;

            v_col := v_col + 1;
        END LOOP;

        FOR v_j IN 2..cardinality(v_departments) LOOP
            v_x[v_i][v_col] :=
                CASE
                    WHEN v_row.department = v_departments[v_j]
                    THEN 1.0
                    ELSE 0.0
                END;

            v_col := v_col + 1;
        END LOOP;

        v_x[v_i][v_col] :=
            v_row.experience * v_row.performance;

        v_y[v_i] := v_row.salary;
    END LOOP;

    v_xtx := array_fill(
        0.0::DOUBLE PRECISION,
        ARRAY[v_p, v_p]
    );

    v_xty := array_fill(
        0.0::DOUBLE PRECISION,
        ARRAY[v_p]
    );

    -- Construct X'X and X'y.
    FOR v_i IN 1..v_n LOOP
        FOR v_j IN 1..v_p LOOP
            v_xty[v_j] :=
                v_xty[v_j] + v_x[v_i][v_j] * v_y[v_i];

            FOR v_k IN 1..v_p LOOP
                v_xtx[v_j][v_k] :=
                    v_xtx[v_j][v_k] +
                    v_x[v_i][v_j] * v_x[v_i][v_k];
            END LOOP;
        END LOOP;
    END LOOP;

    v_beta := solve_ols_system(v_xtx, v_xty);

    v_mean := (
        SELECT AVG(salary)
        FROM employees
        WHERE dataset_id = v_dataset_id
    );

    v_predictions := array_fill(
        0.0::DOUBLE PRECISION,
        ARRAY[v_n]
    );

    v_residuals := array_fill(
        0.0::DOUBLE PRECISION,
        ARRAY[v_n]
    );

    FOR v_i IN 1..v_n LOOP
        FOR v_j IN 1..v_p LOOP
            v_predictions[v_i] :=
                v_predictions[v_i] +
                v_x[v_i][v_j] * v_beta[v_j];
        END LOOP;

        v_residuals[v_i] :=
            v_y[v_i] - v_predictions[v_i];

        v_sse := v_sse + power(v_residuals[v_i], 2);

        v_sst := v_sst + power(v_y[v_i] - v_mean, 2);

        v_mae := v_mae + abs(v_residuals[v_i]);
    END LOOP;

    IF v_sst <= 1e-12 THEN
        RAISE EXCEPTION 'Target variance is zero';
    END IF;

    v_r2 := 1.0 - v_sse / v_sst;

    v_adjusted :=
        1.0 - (1.0 - v_r2) * (v_n - 1.0) / (v_n - v_p);

    v_rmse := sqrt(v_sse / v_n);
    v_mae := v_mae / v_n;

    DELETE FROM model_terms
    WHERE model_id = p_model_id;

    FOR v_j IN 1..v_p LOOP
        INSERT INTO model_terms (
            model_id,
            term_name,
            term_type,
            coefficient,
            standard_error
        )
        VALUES (
            p_model_id,
            v_names[v_j],
            v_types[v_j],
            v_beta[v_j],
            NULL
        );
    END LOOP;

    DELETE FROM model_predictions
    WHERE model_id = p_model_id;

    v_i := 0;

    FOR v_row IN
        SELECT employee_id, salary
        FROM employees
        WHERE dataset_id = v_dataset_id
        ORDER BY employee_id
    LOOP
        v_i := v_i + 1;

        INSERT INTO model_predictions (
            model_id,
            employee_id,
            actual_value,
            predicted_value,
            residual
        )
        VALUES (
            p_model_id,
            v_row.employee_id,
            v_row.salary,
            v_predictions[v_i],
            v_residuals[v_i]
        );
    END LOOP;

    UPDATE regression_models
    SET status = 'FITTED',
        observation_count = v_n,
        parameter_count = v_p,
        r_squared = v_r2,
        adjusted_r_squared = v_adjusted,
        rmse = v_rmse,
        mae = v_mae,
        residual_sum_squares = v_sse,
        fitted_at = CURRENT_TIMESTAMP
    WHERE model_id = p_model_id;

    RETURN QUERY
    SELECT
        p_model_id,
        'FITTED'::model_status,
        v_r2,
        v_adjusted,
        v_rmse,
        v_mae;

EXCEPTION
    WHEN OTHERS THEN
        v_error := SQLERRM;

        UPDATE regression_models
        SET status = 'FAILED',
            error_message = v_error
        WHERE model_id = p_model_id;

        RAISE;
END;
$$;

-- ------------------------------------------------------------
-- 8. MODEL REPORTING VIEWS
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_model_performance AS
SELECT
    m.model_id,
    m.model_name,
    m.status,
    m.observation_count,
    m.parameter_count,
    m.r_squared,
    m.adjusted_r_squared,
    m.rmse,
    m.mae,
    m.fitted_at
FROM regression_models m;

CREATE OR REPLACE VIEW v_model_coefficients AS
SELECT
    m.model_name,
    t.term_name,
    t.term_type,
    t.coefficient,
    t.standard_error
FROM model_terms t
JOIN regression_models m
    ON m.model_id = t.model_id;

CREATE OR REPLACE VIEW v_prediction_diagnostics AS
SELECT
    m.model_name,
    COUNT(p.prediction_id) AS observations,
    AVG(ABS(p.residual)) AS mean_absolute_error,
    SQRT(AVG(POWER(p.residual, 2))) AS root_mean_squared_error,
    MAX(ABS(p.residual)) AS maximum_absolute_error
FROM regression_models m
JOIN model_predictions p
    ON p.model_id = m.model_id
GROUP BY m.model_name;

-- ------------------------------------------------------------
-- 9. PREDICTION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION predict_employee_salary(
    p_model_id BIGINT,
    p_experience DOUBLE PRECISION,
    p_performance DOUBLE PRECISION,
    p_education TEXT,
    p_department TEXT
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_prediction DOUBLE PRECISION;
    v_coefficient DOUBLE PRECISION;
    v_term TEXT;
BEGIN
    IF p_experience < 0 OR p_performance < 0
       OR p_experience IS NULL OR p_performance IS NULL THEN
        RAISE EXCEPTION 'Invalid numerical prediction inputs';
    END IF;

    IF p_education IS NULL OR p_department IS NULL THEN
        RAISE EXCEPTION 'Categorical prediction inputs are required';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM regression_models
        WHERE model_id = p_model_id
          AND status = 'FITTED'
    ) THEN
        RAISE EXCEPTION 'Model is not fitted';
    END IF;

    v_prediction := 0.0;

    FOR v_term, v_coefficient IN
        SELECT term_name, coefficient
        FROM model_terms
        WHERE model_id = p_model_id
    LOOP
        CASE
            WHEN v_term = 'Intercept' THEN
                v_prediction := v_prediction + v_coefficient;

            WHEN v_term = 'experience' THEN
                v_prediction := v_prediction +
                    v_coefficient * p_experience;

            WHEN v_term = 'performance' THEN
                v_prediction := v_prediction +
                    v_coefficient * p_performance;

            WHEN v_term = 'experience:performance' THEN
                v_prediction := v_prediction +
                    v_coefficient *
                    p_experience * p_performance;

            WHEN v_term LIKE 'education[%]' THEN
                IF v_term = 'education[' || p_education || ']' THEN
                    v_prediction := v_prediction + v_coefficient;
                END IF;

            WHEN v_term LIKE 'department[%]' THEN
                IF v_term = 'department[' || p_department || ']' THEN
                    v_prediction := v_prediction + v_coefficient;
                END IF;
        END CASE;
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM model_categories
        WHERE model_id = p_model_id
          AND variable_name = 'education'
          AND category_value = p_education
    ) THEN
        RAISE EXCEPTION 'Unknown education category: %', p_education;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM model_categories
        WHERE model_id = p_model_id
          AND variable_name = 'department'
          AND category_value = p_department
    ) THEN
        RAISE EXCEPTION 'Unknown department category: %', p_department;
    END IF;

    RETURN v_prediction;
END;
$$;

-- ------------------------------------------------------------
-- 10. ELIGIBILITY AND VALIDATION REPORT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_dataset(
    p_dataset_id BIGINT
)
RETURNS TABLE (
    total_records BIGINT,
    invalid_numeric_records BIGINT,
    distinct_education_levels BIGINT,
    distinct_department_levels BIGINT,
    sufficient_sample BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COUNT(*),
        COUNT(*) FILTER (
            WHERE salary < 0
               OR experience < 0
               OR performance < 0
        ),
        COUNT(DISTINCT education),
        COUNT(DISTINCT department),
        COUNT(*) > 7
    FROM employees
    WHERE dataset_id = p_dataset_id;
$$;

-- ------------------------------------------------------------
-- 11. FIT MODEL TRANSACTION
-- ------------------------------------------------------------

DO $$
DECLARE
    v_model_id BIGINT;
BEGIN
    SELECT model_id
    INTO v_model_id
    FROM regression_models
    WHERE model_name = 'employee_salary_ols';

    PERFORM *
    FROM fit_employee_regression(v_model_id);
END;
$$;

-- ------------------------------------------------------------
-- 12. RETRIEVAL QUERIES
-- ------------------------------------------------------------

-- Model performance.
SELECT *
FROM v_model_performance;

-- Coefficient interpretation table.
SELECT
    term_name,
    term_type,
    ROUND(coefficient::NUMERIC, 4) AS coefficient,
    ROUND(standard_error::NUMERIC, 4) AS standard_error
FROM v_model_coefficients
WHERE model_name = 'employee_salary_ols'
ORDER BY term_id;

-- Reference categories.
SELECT
    variable_name,
    category_value,
    is_reference
FROM model_categories
ORDER BY variable_name, category_value;

-- ------------------------------------------------------------
-- 13. AGGREGATION AND REPORTING
-- ------------------------------------------------------------

SELECT
    department,
    education,
    COUNT(*) AS employees,
    ROUND(AVG(salary), 2) AS average_salary,
    ROUND(AVG(experience), 2) AS average_experience,
    ROUND(AVG(performance), 2) AS average_performance
FROM employees
GROUP BY department, education
ORDER BY department, education;

-- Residual reporting.
SELECT
    employee_id,
    actual_value,
    ROUND(predicted_value::NUMERIC, 2) AS predicted,
    ROUND(residual::NUMERIC, 2) AS residual
FROM model_predictions
ORDER BY ABS(residual) DESC;

-- ------------------------------------------------------------
-- 14. NEW PREDICTION
-- ------------------------------------------------------------

SELECT predict_employee_salary(
    (
        SELECT model_id
        FROM regression_models
        WHERE model_name = 'employee_salary_ols'
    ),
    5.0,
    4.0,
    'Master',
    'Technology'
) AS predicted_salary;

-- ------------------------------------------------------------
-- 15. MODEL QUALITY EVALUATION
-- ------------------------------------------------------------

SELECT
    model_name,
    CASE
        WHEN r_squared >= 0.80 THEN 'HIGH FIT'
        WHEN r_squared >= 0.60 THEN 'MODERATE FIT'
        ELSE 'LOW FIT'
    END AS descriptive_fit_category,
    r_squared,
    adjusted_r_squared,
    rmse,
    mae,
    CASE
        WHEN observation_count > parameter_count
        THEN 'SAMPLE SIZE CONDITION SATISFIED'
        ELSE 'INSUFFICIENT OBSERVATIONS'
    END AS sample_validation
FROM regression_models;

-- ------------------------------------------------------------
-- 16. FAILURE CASE: INVALID CATEGORY
-- Run separately to observe validation failure.
-- ------------------------------------------------------------

-- SELECT predict_employee_salary(
--     1, 5, 4, 'Unknown', 'Technology'
-- );

-- ------------------------------------------------------------
-- 17. DATABASE PERFORMANCE
-- ------------------------------------------------------------

ANALYZE employees;
ANALYZE regression_models;
ANALYZE model_terms;
ANALYZE model_predictions;

COMMIT;
