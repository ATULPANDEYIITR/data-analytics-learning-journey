DROP SCHEMA IF EXISTS pandas_fundamentals CASCADE;
CREATE SCHEMA pandas_fundamentals;
SET search_path TO pandas_fundamentals;

-- A relational table represents the same kind of rectangular data
-- that a DataFrame commonly stores: rows, named columns, and types.
CREATE TABLE employees (
    employee_id BIGSERIAL PRIMARY KEY,
    employee_name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary NUMERIC(12, 2) NOT NULL CHECK (salary >= 0),
    performance NUMERIC(3, 2) NOT NULL
        CHECK (performance BETWEEN 0 AND 5),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    hired_at DATE NOT NULL
);

INSERT INTO employees
    (employee_name, department, salary, performance, active, hired_at)
VALUES
    ('Asha', 'Engineering', 95000, 4.50, TRUE, '2023-02-10'),
    ('Ravi', 'Sales', 72000, 3.80, TRUE, '2022-06-15'),
    ('Meera', 'Engineering', 105000, 4.80, TRUE, '2021-09-20'),
    ('John', 'Sales', 68000, 3.20, FALSE, '2020-11-05'),
    ('Fatima', 'Finance', 88000, 4.10, TRUE, '2024-01-18');

-- Indexing department supports repeated filtering and grouping by department.
CREATE INDEX idx_employees_department
    ON employees (department);

-- Indexing active employees supports a common selective predicate.
CREATE INDEX idx_employees_active
    ON employees (active)
    WHERE active = TRUE;

-- Selecting columns corresponds to DataFrame column selection.
SELECT employee_name, salary
FROM employees;

-- Filtering rows corresponds to boolean DataFrame masks.
SELECT employee_name, department, salary, performance
FROM employees
WHERE active = TRUE
  AND performance >= 4.0;

-- Multiple conditions represent a compound row filter.
SELECT employee_name, department, salary
FROM employees
WHERE department IN ('Engineering', 'Finance')
  AND salary >= 90000;

-- A derived column corresponds to vectorized column computation.
SELECT
    employee_name,
    salary,
    performance,
    ROUND(salary * performance / 100, 2) AS bonus,
    ROUND(salary + salary * performance / 100, 2) AS total_compensation
FROM employees;

-- Aggregation corresponds to DataFrame groupby operations.
SELECT
    department,
    COUNT(*) AS employee_count,
    ROUND(AVG(salary), 2) AS average_salary,
    ROUND(AVG(performance), 2) AS average_performance
FROM employees
GROUP BY department
ORDER BY average_salary DESC;

-- A CTE makes a multi-stage tabular transformation explicit.
WITH enriched AS (
    SELECT
        employee_name,
        department,
        salary,
        performance,
        active,
        salary * performance / 100 AS bonus
    FROM employees
),
ranked AS (
    SELECT
        enriched.*,
        RANK() OVER (
            PARTITION BY department
            ORDER BY salary DESC
        ) AS department_salary_rank
    FROM enriched
)
SELECT
    employee_name,
    department,
    ROUND(salary, 2) AS salary,
    ROUND(bonus, 2) AS bonus,
    department_salary_rank
FROM ranked
ORDER BY department, department_salary_rank;

-- A view provides a reusable DataFrame-like analytical projection.
CREATE VIEW active_employee_analysis AS
SELECT
    employee_id,
    employee_name,
    department,
    salary,
    performance,
    ROUND(salary * performance / 100, 2) AS bonus
FROM employees
WHERE active = TRUE;

SELECT *
FROM active_employee_analysis
WHERE performance >= 4.0
ORDER BY salary DESC;

-- PostgreSQL transaction demonstrates validation before persistence.
BEGIN;

INSERT INTO employees
    (employee_name, department, salary, performance, active, hired_at)
VALUES
    ('Grace', 'Engineering', 91000, 4.30, TRUE, CURRENT_DATE);

-- Confirm the row exists before committing.
SELECT employee_name, department, salary
FROM employees
WHERE employee_name = 'Grace';

COMMIT;

-- Demonstrate a failed constraint without leaving invalid data.
BEGIN;

DO $$
BEGIN
    BEGIN
        INSERT INTO employees
            (employee_name, department, salary, performance, active, hired_at)
        VALUES
            ('Invalid Employee', 'Finance', -1000, 4.00, TRUE, CURRENT_DATE);
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid salary rejected by database constraint.';
    END;
END
$$;

ROLLBACK;

-- Conditional aggregation provides a compact quality report.
SELECT
    COUNT(*) AS total_employees,
    COUNT(*) FILTER (
        WHERE active
    ) AS active_employees,
    COUNT(*) FILTER (
        WHERE performance >= 4
    ) AS high_performers,
    ROUND(AVG(salary), 2) AS overall_average_salary
FROM employees;

-- The final query is intentionally equivalent to a typical
-- DataFrame.loc boolean selection: choose specific columns and rows.
SELECT
    employee_name,
    salary,
    performance
FROM employees
WHERE active
  AND salary >= 80000
  AND performance >= 4
ORDER BY salary DESC;
