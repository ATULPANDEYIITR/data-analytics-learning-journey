DROP SCHEMA IF EXISTS numpy_fundamentals CASCADE;
CREATE SCHEMA numpy_fundamentals;

SET search_path TO numpy_fundamentals;

-- PostgreSQL models the array concepts with explicit dimensions and element
-- rows. This keeps relational integrity visible instead of hiding structure
-- inside an opaque application object.

CREATE TYPE dtype_kind AS ENUM ('INT32', 'FLOAT64', 'BOOLEAN');

CREATE TABLE array_dataset (
    array_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    ndim INTEGER NOT NULL CHECK (ndim >= 0),
    dtype dtype_kind NOT NULL,
    rows INTEGER CHECK (rows IS NULL OR rows > 0),
    columns INTEGER CHECK (columns IS NULL OR columns > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (ndim = 0 AND rows IS NULL AND columns IS NULL)
        OR
        (ndim = 1 AND rows IS NOT NULL AND columns IS NULL)
        OR
        (ndim = 2 AND rows IS NOT NULL AND columns IS NOT NULL)
    )
);

CREATE TABLE array_element (
    array_id BIGINT NOT NULL REFERENCES array_dataset(array_id)
        ON DELETE CASCADE,
    row_index INTEGER NOT NULL CHECK (row_index >= 0),
    column_index INTEGER CHECK (column_index IS NULL OR column_index >= 0),
    numeric_value DOUBLE PRECISION,
    boolean_value BOOLEAN,
    PRIMARY KEY (array_id, row_index, column_index),
    CHECK (
        (numeric_value IS NOT NULL AND boolean_value IS NULL)
        OR
        (numeric_value IS NULL AND boolean_value IS NOT NULL)
    )
);

CREATE TABLE transformation (
    transformation_id BIGSERIAL PRIMARY KEY,
    array_id BIGINT NOT NULL REFERENCES array_dataset(array_id)
        ON DELETE CASCADE,
    operation TEXT NOT NULL CHECK (
        operation IN (
            'RESHAPE',
            'SLICE',
            'VECTORIZE',
            'BROADCAST',
            'FILTER',
            'NORMALIZE',
            'TRANSPOSE'
        )
    ),
    source_shape TEXT NOT NULL,
    target_shape TEXT,
    description TEXT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE validation_rule (
    rule_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    rule_type TEXT NOT NULL CHECK (
        rule_type IN (
            'SHAPE',
            'DTYPE',
            'FINITE',
            'RANGE'
        )
    ),
    minimum_value DOUBLE PRECISION,
    maximum_value DOUBLE PRECISION,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (
        minimum_value IS NULL
        OR maximum_value IS NULL
        OR minimum_value <= maximum_value
    )
);

CREATE TABLE validation_result (
    validation_id BIGSERIAL PRIMARY KEY,
    array_id BIGINT NOT NULL REFERENCES array_dataset(array_id)
        ON DELETE CASCADE,
    rule_id BIGINT NOT NULL REFERENCES validation_rule(rule_id),
    passed BOOLEAN NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT NOT NULL
);

CREATE INDEX idx_array_element_array_row
    ON array_element (array_id, row_index);

CREATE INDEX idx_array_element_numeric_value
    ON array_element (numeric_value)
    WHERE numeric_value IS NOT NULL;

CREATE INDEX idx_transformation_array_time
    ON transformation (array_id, executed_at DESC);

CREATE OR REPLACE FUNCTION validate_element_coordinates()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    metadata array_dataset%ROWTYPE;
BEGIN
    SELECT *
    INTO metadata
    FROM array_dataset
    WHERE array_id = NEW.array_id;

    IF metadata.ndim = 0 THEN
        IF NEW.row_index <> 0 OR NEW.column_index IS NOT NULL THEN
            RAISE EXCEPTION
                'A zero-dimensional array cannot contain row/column coordinates';
        END IF;
    ELSIF metadata.ndim = 1 THEN
        IF NEW.row_index >= metadata.rows
           OR NEW.column_index IS NOT NULL THEN
            RAISE EXCEPTION
                'Invalid one-dimensional coordinates for array %',
                metadata.name;
        END IF;
    ELSE
        IF NEW.row_index >= metadata.rows
           OR NEW.column_index IS NULL
           OR NEW.column_index >= metadata.columns THEN
            RAISE EXCEPTION
                'Invalid two-dimensional coordinates for array %',
                metadata.name;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_element_coordinates
BEFORE INSERT OR UPDATE ON array_element
FOR EACH ROW
EXECUTE FUNCTION validate_element_coordinates();

INSERT INTO array_dataset (name, ndim, dtype, rows, columns)
VALUES
    ('student_scores', 2, 'INT32', 3, 4),
    ('temperatures', 1, 'FLOAT64', 5, NULL),
    ('sales_matrix', 2, 'FLOAT64', 3, 3),
    ('validity_mask', 1, 'BOOLEAN', 5, NULL);

INSERT INTO array_element
    (array_id, row_index, column_index, numeric_value)
SELECT
    a.array_id,
    coordinates.row_index,
    coordinates.column_index,
    coordinates.value
FROM array_dataset AS a
JOIN (
    VALUES
        ('student_scores', 0, 0, 82.0),
        ('student_scores', 0, 1, 91.0),
        ('student_scores', 0, 2, 77.0),
        ('student_scores', 0, 3, 88.0),
        ('student_scores', 1, 0, 95.0),
        ('student_scores', 1, 1, 84.0),
        ('student_scores', 1, 2, 90.0),
        ('student_scores', 1, 3, 73.0),
        ('student_scores', 2, 0, 68.0),
        ('student_scores', 2, 1, 79.0),
        ('student_scores', 2, 2, 85.0),
        ('student_scores', 2, 3, 92.0)
) AS coordinates(name, row_index, column_index, value)
ON a.name = coordinates.name;

INSERT INTO array_element
    (array_id, row_index, column_index, numeric_value)
SELECT
    a.array_id,
    values.row_index,
    NULL,
    values.value
FROM array_dataset AS a
JOIN (
    VALUES
        ('temperatures', 0, 18.5),
        ('temperatures', 1, 21.0),
        ('temperatures', 2, 24.5),
        ('temperatures', 3, 27.0),
        ('temperatures', 4, 30.0)
) AS values(name, row_index, value)
ON a.name = values.name;

INSERT INTO array_element
    (array_id, row_index, column_index, numeric_value)
SELECT
    a.array_id,
    values.row_index,
    values.column_index,
    values.value
FROM array_dataset AS a
JOIN (
    VALUES
        ('sales_matrix', 0, 0, 120.0),
        ('sales_matrix', 0, 1, 150.0),
        ('sales_matrix', 0, 2, 180.0),
        ('sales_matrix', 1, 0, 90.0),
        ('sales_matrix', 1, 1, 110.0),
        ('sales_matrix', 1, 2, 140.0),
        ('sales_matrix', 2, 0, 200.0),
        ('sales_matrix', 2, 1, 220.0),
        ('sales_matrix', 2, 2, 250.0)
) AS values(name, row_index, column_index, value)
ON a.name = values.name;

INSERT INTO array_element
    (array_id, row_index, column_index, boolean_value)
SELECT
    a.array_id,
    values.row_index,
    NULL,
    values.value
FROM array_dataset AS a
JOIN (
    VALUES
        ('validity_mask', 0, TRUE),
        ('validity_mask', 1, TRUE),
        ('validity_mask', 2, FALSE),
        ('validity_mask', 3, TRUE),
        ('validity_mask', 4, FALSE)
) AS values(name, row_index, value)
ON a.name = values.name;

INSERT INTO validation_rule
    (name, rule_type, minimum_value, maximum_value)
VALUES
    ('score_range', 'RANGE', 0, 100),
    ('finite_numeric_values', 'FINITE', NULL, NULL),
    ('positive_sales', 'RANGE', 0, NULL),
    ('temperature_range', 'RANGE', -50, 70);

INSERT INTO transformation
    (array_id, operation, source_shape, target_shape, description)
SELECT
    array_id,
    'SLICE',
    '(3,4)',
    '(2,4)',
    'Selected the first two rows of the student score matrix'
FROM array_dataset
WHERE name = 'student_scores';

INSERT INTO transformation
    (array_id, operation, source_shape, target_shape, description)
SELECT
    array_id,
    'VECTORIZE',
    '(5,)',
    '(5,)',
    'Converted Celsius measurements to Fahrenheit using element-wise arithmetic'
FROM array_dataset
WHERE name = 'temperatures';

INSERT INTO transformation
    (array_id, operation, source_shape, target_shape, description)
SELECT
    array_id,
    'BROADCAST',
    '(3,3)',
    '(3,3)',
    'Applied a three-element target vector across the final dimension'
FROM array_dataset
WHERE name = 'sales_matrix';

INSERT INTO transformation
    (array_id, operation, source_shape, target_shape, description)
SELECT
    array_id,
    'FILTER',
    '(3,4)',
    'variable',
    'Selected student scores greater than or equal to 85'
FROM array_dataset
WHERE name = 'student_scores';

INSERT INTO validation_result
    (array_id, rule_id, passed, details)
SELECT
    a.array_id,
    r.rule_id,
    TRUE,
    'All stored numeric values satisfy the configured score range'
FROM array_dataset AS a
CROSS JOIN validation_rule AS r
WHERE a.name = 'student_scores'
  AND r.name = 'score_range';

INSERT INTO validation_result
    (array_id, rule_id, passed, details)
SELECT
    a.array_id,
    r.rule_id,
    TRUE,
    'All temperature measurements fall within the configured physical range'
FROM array_dataset AS a
CROSS JOIN validation_rule AS r
WHERE a.name = 'temperatures'
  AND r.name = 'temperature_range';

-- Matrix inspection preserves row/column coordinates, making SQL results
-- directly useful for debugging multidimensional data.
SELECT
    a.name,
    e.row_index,
    e.column_index,
    e.numeric_value
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
WHERE a.name = 'student_scores'
ORDER BY e.row_index, e.column_index;

-- Boolean filtering corresponds to NumPy boolean indexing.
SELECT
    e.row_index,
    e.column_index,
    e.numeric_value
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
WHERE a.name = 'student_scores'
  AND e.numeric_value >= 85
ORDER BY e.numeric_value DESC;

-- Axis-like aggregation: GROUP BY row_index produces one aggregate per row.
SELECT
    e.row_index,
    SUM(e.numeric_value) AS row_total,
    AVG(e.numeric_value) AS row_mean,
    MAX(e.numeric_value) AS row_maximum
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
WHERE a.name = 'student_scores'
GROUP BY e.row_index
ORDER BY e.row_index;

-- Column aggregation corresponds to a reduction along the first dimension.
SELECT
    e.column_index,
    SUM(e.numeric_value) AS column_total,
    AVG(e.numeric_value) AS column_mean
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
WHERE a.name = 'student_scores'
GROUP BY e.column_index
ORDER BY e.column_index;

-- Vectorized Celsius-to-Fahrenheit transformation.
SELECT
    e.row_index,
    e.numeric_value AS celsius,
    e.numeric_value * 9.0 / 5.0 + 32.0 AS fahrenheit
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
WHERE a.name = 'temperatures'
ORDER BY e.row_index;

-- Broadcasting-style comparison: every sales column is compared with the
-- corresponding target value. The target CTE represents a one-dimensional
-- vector aligned to the matrix's final dimension.
WITH targets(column_index, target_value) AS (
    VALUES
        (0, 100.0),
        (1, 120.0),
        (2, 160.0)
)
SELECT
    e.row_index,
    e.column_index,
    e.numeric_value AS sales,
    targets.target_value,
    e.numeric_value / targets.target_value AS achievement_ratio
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
JOIN targets
    ON targets.column_index = e.column_index
WHERE a.name = 'sales_matrix'
ORDER BY e.row_index, e.column_index;

-- CTE-based normalization demonstrates a relational equivalent of a
-- row-wise NumPy reduction followed by broadcasting.
WITH row_maxima AS (
    SELECT
        e.row_index,
        MAX(e.numeric_value) AS maximum_value
    FROM array_dataset AS a
    JOIN array_element AS e
        ON e.array_id = a.array_id
    WHERE a.name = 'sales_matrix'
    GROUP BY e.row_index
)
SELECT
    e.row_index,
    e.column_index,
    e.numeric_value,
    e.numeric_value / row_maxima.maximum_value AS normalized_value
FROM array_dataset AS a
JOIN array_element AS e
    ON e.array_id = a.array_id
JOIN row_maxima
    ON row_maxima.row_index = e.row_index
WHERE a.name = 'sales_matrix'
ORDER BY e.row_index, e.column_index;

-- Transactional validation records are written together so a validation
-- result cannot be partially committed.
BEGIN;

INSERT INTO validation_result
    (array_id, rule_id, passed, details)
SELECT
    a.array_id,
    r.rule_id,
    NOT EXISTS (
        SELECT 1
        FROM array_element e
        WHERE e.array_id = a.array_id
          AND e.numeric_value IS NOT NULL
          AND (e.numeric_value < r.minimum_value
               OR e.numeric_value > r.maximum_value)
    ),
    'Database-level validation query evaluated every numeric element'
FROM array_dataset a
CROSS JOIN validation_rule r
WHERE a.name = 'sales_matrix'
  AND r.name = 'positive_sales';

COMMIT;

-- PostgreSQL transaction rollback demonstration. The deliberately invalid
-- coordinate violates the trigger's dimension rule, so the transaction is
-- rolled back rather than leaving an invalid array element.
BEGIN;

SAVEPOINT before_invalid_coordinate;

DO $$
BEGIN
    BEGIN
        INSERT INTO array_element (
            array_id,
            row_index,
            column_index,
            numeric_value
        )
        SELECT
            array_id,
            99,
            0,
            500.0
        FROM array_dataset
        WHERE name = 'sales_matrix';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Invalid coordinate rejected: %', SQLERRM;
            ROLLBACK TO SAVEPOINT before_invalid_coordinate;
    END;
END;
$$;

COMMIT;

-- Governance and quality-control view combining array metadata with the
-- recorded transformations and validations.
CREATE VIEW array_quality_overview AS
SELECT
    a.array_id,
    a.name,
    a.ndim,
    a.dtype,
    a.rows,
    a.columns,
    COUNT(DISTINCT t.transformation_id) AS transformation_count,
    COUNT(DISTINCT v.validation_id) AS validation_count,
    COUNT(DISTINCT v.validation_id)
        FILTER (WHERE v.passed = FALSE) AS failed_validations
FROM array_dataset AS a
LEFT JOIN transformation AS t
    ON t.array_id = a.array_id
LEFT JOIN validation_result AS v
    ON v.array_id = a.array_id
GROUP BY
    a.array_id,
    a.name,
    a.ndim,
    a.dtype,
    a.rows,
    a.columns;

SELECT *
FROM array_quality_overview
ORDER BY array_id;

-- The following statement is intentionally not executed:
-- INSERT INTO array_element (array_id, row_index, column_index, numeric_value)
-- SELECT array_id, 0, 99, 10 FROM array_dataset WHERE name = 'sales_matrix';
-- The trigger rejects column 99 because sales_matrix has only three columns.
