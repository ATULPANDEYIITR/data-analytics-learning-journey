/*
    POWER QUERY IN POWER BI
    Relational ETL and Query Dependency Simulation

    PostgreSQL 14+

    Covers:
    - Data sources and staging
    - Data cleaning
    - Data type validation
    - Query transformations
    - Merge and append
    - Query dependencies
    - Data quality monitoring
    - Transformation execution
    - Aggregation and reporting
*/

DROP SCHEMA IF EXISTS power_query CASCADE;

CREATE SCHEMA power_query;

SET search_path TO power_query, public;

-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE query_status AS ENUM (
    'created',
    'running',
    'completed',
    'failed'
);

CREATE TYPE transformation_type AS ENUM (
    'clean',
    'filter',
    'rename',
    'change_type',
    'merge',
    'append',
    'group',
    'custom'
);

CREATE TYPE data_type AS ENUM (
    'text',
    'integer',
    'decimal',
    'date',
    'boolean'
);

-- ============================================================
-- 2. DATA SOURCE REGISTRY
-- ============================================================

CREATE TABLE data_sources (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(40) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO data_sources (
    source_name,
    source_type,
    description
)
VALUES
(
    'Customer CSV',
    'CSV',
    'Customer master data'
),
(
    'Current Orders',
    'CSV',
    'Current transactional data'
),
(
    'Archived Orders',
    'CSV',
    'Historical transactional data'
);

-- ============================================================
-- 3. QUERY REGISTRY
-- ============================================================

CREATE TABLE queries (
    query_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    query_name VARCHAR(100) NOT NULL UNIQUE,
    source_id BIGINT REFERENCES data_sources(source_id),
    status query_status NOT NULL DEFAULT 'created',
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_executed_at TIMESTAMPTZ,
    execution_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO queries (query_name, source_id)
VALUES
(
    'Customers_Source',
    (SELECT source_id FROM data_sources
     WHERE source_name = 'Customer CSV')
),
(
    'Orders_Source',
    (SELECT source_id FROM data_sources
     WHERE source_name = 'Current Orders')
),
(
    'Archived_Orders_Source',
    (SELECT source_id FROM data_sources
     WHERE source_name = 'Archived Orders')
),
(
    'Clean_Customers',
    NULL
),
(
    'Typed_Orders',
    NULL
),
(
    'Customer_Order_Merge',
    NULL
),
(
    'Combined_Orders',
    NULL
),
(
    'Regional_Summary',
    NULL
);

-- ============================================================
-- 4. QUERY DEPENDENCIES
-- ============================================================

CREATE TABLE query_dependencies (
    query_id BIGINT NOT NULL REFERENCES queries(query_id)
        ON DELETE CASCADE,

    depends_on_query_id BIGINT NOT NULL REFERENCES queries(query_id)
        ON DELETE CASCADE,

    PRIMARY KEY (query_id, depends_on_query_id),

    CHECK (query_id <> depends_on_query_id)
);

INSERT INTO query_dependencies (
    query_id,
    depends_on_query_id
)
SELECT
    child.query_id,
    parent.query_id
FROM (
    VALUES
        ('Clean_Customers', 'Customers_Source'),
        ('Typed_Orders', 'Orders_Source'),
        ('Customer_Order_Merge', 'Typed_Orders'),
        ('Customer_Order_Merge', 'Clean_Customers'),
        ('Combined_Orders', 'Typed_Orders'),
        ('Combined_Orders', 'Archived_Orders_Source'),
        ('Regional_Summary', 'Customer_Order_Merge')
) AS dependency(child_name, parent_name)
JOIN queries child
    ON child.query_name = dependency.child_name
JOIN queries parent
    ON parent.query_name = dependency.parent_name;

-- ============================================================
-- 5. QUERY DEPENDENCY VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION prevent_query_cycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    cycle_found BOOLEAN;
BEGIN
    WITH RECURSIVE dependency_tree(query_id) AS (
        SELECT NEW.depends_on_query_id

        UNION

        SELECT dependency.depends_on_query_id
        FROM query_dependencies dependency
        JOIN dependency_tree tree
          ON dependency.query_id = tree.query_id
    )
    SELECT EXISTS (
        SELECT 1
        FROM dependency_tree
        WHERE query_id = NEW.query_id
    )
    INTO cycle_found;

    IF cycle_found THEN
        RAISE EXCEPTION
            'Circular query dependency is not permitted.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_query_cycle
BEFORE INSERT OR UPDATE ON query_dependencies
FOR EACH ROW
EXECUTE FUNCTION prevent_query_cycle();

-- ============================================================
-- 6. RAW STAGING TABLES
-- ============================================================

CREATE TABLE staging_customers (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id TEXT,
    customer_name TEXT,
    region TEXT,
    source_file TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staging_orders (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT,
    customer_id TEXT,
    amount TEXT,
    order_date TEXT,
    source_file TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staging_archived_orders (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT,
    customer_id TEXT,
    amount TEXT,
    order_date TEXT,
    source_file TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO staging_customers (
    customer_id,
    customer_name,
    region,
    source_file
)
VALUES
('1', ' Alice ', 'North', 'customers.csv'),
('2', 'Bob', 'South', 'customers.csv'),
('3', 'Carol', 'North', 'customers.csv'),
('2', 'Bob', 'South', 'customers.csv'),
('4', NULL, 'West', 'customers.csv');

INSERT INTO staging_orders (
    order_id,
    customer_id,
    amount,
    order_date,
    source_file
)
VALUES
('101', '1', '1250.50', '2026-01-10', 'orders.csv'),
('102', '2', '800.00', '2026-01-12', 'orders.csv'),
('103', '1', '450.25', '2026-02-02', 'orders.csv'),
('104', '99', '300.00', '2026-02-05', 'orders.csv'),
('105', '3', 'INVALID', '2026-02-10', 'orders.csv'),
('106', '2', '500.00', 'INVALID_DATE', 'orders.csv');

INSERT INTO staging_archived_orders (
    order_id,
    customer_id,
    amount,
    order_date,
    source_file
)
VALUES
('90', '2', '500.00', '2025-12-15', 'archive.csv'),
('91', '3', '700.00', '2025-12-20', 'archive.csv');

-- ============================================================
-- 7. DATA QUALITY ISSUE REGISTRY
-- ============================================================

CREATE TABLE data_quality_issues (
    issue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_row_id BIGINT NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    issue_type VARCHAR(60) NOT NULL,
    original_value TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_quality_issues_unresolved
ON data_quality_issues (source_table, detected_at)
WHERE resolved = FALSE;

-- ============================================================
-- 8. SAFE TYPE CONVERSION FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION try_numeric(
    input_value TEXT
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF input_value IS NULL OR btrim(input_value) = '' THEN
        RETURN NULL;
    END IF;

    IF btrim(input_value) !~
       '^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$' THEN
        RETURN NULL;
    END IF;

    RETURN btrim(input_value)::NUMERIC;

EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION try_integer(
    input_value TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF input_value IS NULL OR btrim(input_value) = '' THEN
        RETURN NULL;
    END IF;

    IF btrim(input_value) !~ '^[+-]?[0-9]+$' THEN
        RETURN NULL;
    END IF;

    RETURN btrim(input_value)::BIGINT;

EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION try_date(
    input_value TEXT
)
RETURNS DATE
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF input_value IS NULL OR btrim(input_value) = '' THEN
        RETURN NULL;
    END IF;

    IF btrim(input_value) !~ '^\d{4}-\d{2}-\d{2}$' THEN
        RETURN NULL;
    END IF;

    RETURN btrim(input_value)::DATE;

EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;

-- ============================================================
-- 9. CLEAN CUSTOMER DATA
-- ============================================================

CREATE TABLE customers (
    customer_id BIGINT PRIMARY KEY,
    customer_name VARCHAR(150),
    region VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (customer_id > 0),
    CHECK (length(region) > 0)
);

INSERT INTO customers (
    customer_id,
    customer_name,
    region
)
SELECT DISTINCT ON (try_integer(customer_id))
    try_integer(customer_id),
    NULLIF(
        regexp_replace(
            btrim(customer_name),
            '\s+',
            ' ',
            'g'
        ),
        ''
    ),
    btrim(region)
FROM staging_customers
WHERE try_integer(customer_id) IS NOT NULL
  AND NULLIF(btrim(region), '') IS NOT NULL
ORDER BY try_integer(customer_id), staging_id;

CREATE INDEX idx_customers_region
ON customers(region);

-- ============================================================
-- 10. VALIDATED ORDER TABLE
-- ============================================================

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    order_date DATE NOT NULL,
    order_status VARCHAR(30) NOT NULL DEFAULT 'valid',

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CHECK (order_id > 0),
    CHECK (amount >= 0),
    CHECK (
        order_status IN (
            'valid',
            'review_required',
            'rejected'
        )
    )
);

-- Valid records are loaded first.
-- Unknown customers and invalid types are excluded from
-- this clean relational table and retained in staging.

INSERT INTO orders (
    order_id,
    customer_id,
    amount,
    order_date
)
SELECT
    try_integer(source.order_id),
    try_integer(source.customer_id),
    try_numeric(source.amount),
    try_date(source.order_date)
FROM staging_orders source
JOIN customers customer
    ON customer.customer_id =
       try_integer(source.customer_id)
WHERE try_integer(source.order_id) IS NOT NULL
  AND try_integer(source.customer_id) IS NOT NULL
  AND try_numeric(source.amount) IS NOT NULL
  AND try_date(source.order_date) IS NOT NULL
  AND try_numeric(source.amount) >= 0
ON CONFLICT (order_id) DO NOTHING;

CREATE INDEX idx_orders_customer
ON orders(customer_id);

CREATE INDEX idx_orders_date
ON orders(order_date);

CREATE INDEX idx_orders_amount
ON orders(amount);

-- ============================================================
-- 11. RECORD DATA QUALITY FAILURES
-- ============================================================

INSERT INTO data_quality_issues (
    source_table,
    source_row_id,
    column_name,
    issue_type,
    original_value
)
SELECT
    'staging_orders',
    staging_id,
    column_name,
    issue_type,
    original_value
FROM (
    SELECT
        staging_id,
        'amount' AS column_name,
        'invalid_decimal' AS issue_type,
        amount AS original_value
    FROM staging_orders
    WHERE try_numeric(amount) IS NULL

    UNION ALL

    SELECT
        staging_id,
        'order_date',
        'invalid_date',
        order_date
    FROM staging_orders
    WHERE try_date(order_date) IS NULL

    UNION ALL

    SELECT
        source.staging_id,
        'customer_id',
        'unknown_customer',
        source.customer_id
    FROM staging_orders source
    LEFT JOIN customers customer
      ON customer.customer_id =
         try_integer(source.customer_id)
    WHERE customer.customer_id IS NULL
      AND try_integer(source.customer_id) IS NOT NULL
) failures;

-- ============================================================
-- 12. ARCHIVED ORDER TABLE
-- ============================================================

CREATE TABLE archived_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    order_date DATE NOT NULL,

    CHECK (order_id > 0),
    CHECK (amount >= 0)
);

INSERT INTO archived_orders (
    order_id,
    customer_id,
    amount,
    order_date
)
SELECT
    try_integer(source.order_id),
    try_integer(source.customer_id),
    try_numeric(source.amount),
    try_date(source.order_date)
FROM staging_archived_orders source
WHERE try_integer(source.order_id) IS NOT NULL
  AND try_integer(source.customer_id) IS NOT NULL
  AND try_numeric(source.amount) IS NOT NULL
  AND try_date(source.order_date) IS NOT NULL
  AND try_numeric(source.amount) >= 0;

-- ============================================================
-- 13. MERGE: CUSTOMER AND ORDER DATA
-- ============================================================

CREATE VIEW customer_order_merge AS
SELECT
    orders.order_id,
    orders.customer_id,
    customers.customer_name,
    customers.region,
    orders.amount,
    orders.order_date
FROM orders
LEFT JOIN customers
    ON customers.customer_id = orders.customer_id;

-- ============================================================
-- 14. APPEND: CURRENT AND ARCHIVED ORDERS
-- ============================================================

CREATE VIEW combined_orders AS
SELECT
    order_id,
    customer_id,
    amount,
    order_date,
    'current'::TEXT AS order_period
FROM orders

UNION ALL

SELECT
    order_id,
    customer_id,
    amount,
    order_date,
    'archived'::TEXT AS order_period
FROM archived_orders;

-- UNION ALL preserves duplicate records.
-- UNION would remove duplicate result rows.

CREATE INDEX idx_archived_orders_customer
ON archived_orders(customer_id);

-- ============================================================
-- 15. QUERY TRANSFORMATION REGISTRY
-- ============================================================

CREATE TABLE transformations (
    transformation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    query_id BIGINT NOT NULL REFERENCES queries(query_id),
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    operation transformation_type NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (query_id, step_number)
);

INSERT INTO transformations (
    query_id,
    step_number,
    step_name,
    operation,
    description
)
SELECT
    query_id,
    step_number,
    step_name,
    operation::transformation_type,
    description
FROM (
    VALUES
        ('Clean_Customers', 1, 'Trim Text', 'clean',
         'Remove leading and trailing whitespace'),
        ('Clean_Customers', 2, 'Remove Duplicates', 'clean',
         'Keep one record per customer'),
        ('Typed_Orders', 1, 'Convert Amount', 'change_type',
         'Convert text amount to numeric'),
        ('Typed_Orders', 2, 'Convert Date', 'change_type',
         'Convert ISO text date to date'),
        ('Customer_Order_Merge', 1, 'Customer Merge', 'merge',
         'Left join orders with customers'),
        ('Combined_Orders', 1, 'Append Tables', 'append',
         'Combine current and archived orders'),
        ('Regional_Summary', 1, 'Group by Region', 'group',
         'Aggregate sales by region')
) AS steps(
    query_name,
    step_number,
    step_name,
    operation,
    description
)
JOIN queries
    ON queries.query_name = steps.query_name;

-- ============================================================
-- 16. EXECUTION AUDIT
-- ============================================================

CREATE TABLE query_execution_log (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    query_id BIGINT NOT NULL REFERENCES queries(query_id),
    status query_status NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    affected_rows BIGINT,
    error_message TEXT
);

CREATE OR REPLACE PROCEDURE execute_query_audit(
    p_query_name TEXT,
    p_status query_status,
    p_affected_rows BIGINT,
    p_error TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_id BIGINT;
BEGIN
    SELECT query_id
    INTO v_query_id
    FROM queries
    WHERE query_name = p_query_name
      AND is_enabled = TRUE;

    IF v_query_id IS NULL THEN
        RAISE EXCEPTION 'Unknown or disabled query: %',
            p_query_name;
    END IF;

    INSERT INTO query_execution_log (
        query_id,
        status,
        completed_at,
        affected_rows,
        error_message
    )
    VALUES (
        v_query_id,
        p_status,
        CASE
            WHEN p_status IN ('completed', 'failed')
            THEN CURRENT_TIMESTAMP
            ELSE NULL
        END,
        p_affected_rows,
        p_error
    );

    UPDATE queries
    SET
        status = p_status,
        last_executed_at = CURRENT_TIMESTAMP,
        execution_message = p_error
    WHERE query_id = v_query_id;
END;
$$;

-- ============================================================
-- 17. DEPENDENCY ORDER REPORT
-- ============================================================

CREATE OR REPLACE VIEW query_dependency_report AS
WITH RECURSIVE dependency_tree AS (
    SELECT
        query_id,
        depends_on_query_id,
        1 AS dependency_level
    FROM query_dependencies

    UNION ALL

    SELECT
        dependency.query_id,
        tree.depends_on_query_id,
        tree.dependency_level + 1
    FROM query_dependencies dependency
    JOIN dependency_tree tree
      ON dependency.query_id = tree.depends_on_query_id
)
SELECT
    child.query_name,
    parent.query_name AS depends_on,
    MAX(tree.dependency_level) AS dependency_level
FROM dependency_tree tree
JOIN queries child
    ON child.query_id = tree.query_id
JOIN queries parent
    ON parent.query_id = tree.depends_on_query_id
GROUP BY child.query_name, parent.query_name;

-- ============================================================
-- 18. REGIONAL AGGREGATION
-- ============================================================

CREATE VIEW regional_sales_summary AS
SELECT
    region,
    COUNT(*) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(amount) AS total_sales,
    AVG(amount) AS average_order_value,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS latest_order_date
FROM customer_order_merge
GROUP BY region;

-- ============================================================
-- 19. QUERY ELIGIBILITY AND DATA QUALITY REPORT
-- ============================================================

CREATE VIEW query_quality_report AS
SELECT
    queries.query_name,
    queries.status,
    COUNT(DISTINCT issues.issue_id) AS unresolved_issues,
    CASE
        WHEN queries.is_enabled = FALSE THEN FALSE
        WHEN queries.status = 'failed' THEN FALSE
        WHEN COUNT(DISTINCT issues.issue_id) > 0 THEN FALSE
        ELSE TRUE
    END AS eligible_for_reporting
FROM queries
LEFT JOIN data_quality_issues issues
    ON issues.resolved = FALSE
GROUP BY
    queries.query_id,
    queries.query_name,
    queries.status,
    queries.is_enabled;

-- ============================================================
-- 20. TRANSACTIONAL DATA PROCESSING
-- ============================================================

BEGIN;

CALL execute_query_audit(
    'Customers_Source',
    'completed',
    (SELECT COUNT(*) FROM staging_customers)
);

CALL execute_query_audit(
    'Clean_Customers',
    'completed',
    (SELECT COUNT(*) FROM customers)
);

CALL execute_query_audit(
    'Orders_Source',
    'completed',
    (SELECT COUNT(*) FROM staging_orders)
);

CALL execute_query_audit(
    'Typed_Orders',
    'completed',
    (SELECT COUNT(*) FROM orders)
);

CALL execute_query_audit(
    'Customer_Order_Merge',
    'completed',
    (SELECT COUNT(*) FROM customer_order_merge)
);

CALL execute_query_audit(
    'Combined_Orders',
    'completed',
    (SELECT COUNT(*) FROM combined_orders)
);

CALL execute_query_audit(
    'Regional_Summary',
    'completed',
    (SELECT COUNT(*) FROM regional_sales_summary)
);

COMMIT;

-- ============================================================
-- 21. RETRIEVAL QUERIES
-- ============================================================

SELECT *
FROM customers
ORDER BY customer_id;

SELECT *
FROM orders
ORDER BY order_date;

SELECT *
FROM customer_order_merge
ORDER BY order_id;

SELECT *
FROM combined_orders
ORDER BY order_date;

-- ============================================================
-- 22. VALIDATION QUERIES
-- ============================================================

-- Invalid or incomplete source records.
SELECT
    staging_id,
    order_id,
    customer_id,
    amount,
    order_date
FROM staging_orders
WHERE try_integer(order_id) IS NULL
   OR try_integer(customer_id) IS NULL
   OR try_numeric(amount) IS NULL
   OR try_date(order_date) IS NULL;

-- Unresolved data quality issues.
SELECT *
FROM data_quality_issues
WHERE resolved = FALSE
ORDER BY detected_at;

-- Referential integrity validation.
SELECT source.*
FROM staging_orders source
LEFT JOIN customers customer
    ON customer.customer_id =
       try_integer(source.customer_id)
WHERE customer.customer_id IS NULL;

-- Duplicate customer identification.
SELECT
    try_integer(customer_id) AS customer_id,
    COUNT(*) AS duplicate_count
FROM staging_customers
GROUP BY try_integer(customer_id)
HAVING COUNT(*) > 1;

-- ============================================================
-- 23. AGGREGATION AND REPORTING
-- ============================================================

SELECT *
FROM regional_sales_summary
ORDER BY total_sales DESC;

SELECT
    order_period,
    COUNT(*) AS order_count,
    SUM(amount) AS revenue
FROM combined_orders
GROUP BY order_period
ORDER BY order_period;

SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS lifetime_value
FROM combined_orders
GROUP BY customer_id
ORDER BY lifetime_value DESC;

-- ============================================================
-- 24. QUERY EXECUTION REPORT
-- ============================================================

SELECT
    queries.query_name,
    queries.status,
    queries.last_executed_at,
    log.affected_rows,
    log.error_message
FROM queries
LEFT JOIN LATERAL (
    SELECT
        affected_rows,
        error_message
    FROM query_execution_log
    WHERE query_id = queries.query_id
    ORDER BY execution_id DESC
    LIMIT 1
) log ON TRUE
ORDER BY queries.query_name;

-- ============================================================
-- 25. DEPENDENCY REPORT
-- ============================================================

SELECT *
FROM query_dependency_report
ORDER BY query_name, dependency_level;

-- ============================================================
-- 26. QUALITY AND REPORTING ELIGIBILITY
-- ============================================================

SELECT *
FROM query_quality_report
ORDER BY query_name;

-- ============================================================
-- 27. PERFORMANCE INSPECTION
-- ============================================================

EXPLAIN
SELECT
    customers.region,
    SUM(orders.amount)
FROM orders
JOIN customers
    ON customers.customer_id = orders.customer_id
GROUP BY customers.region;

-- ============================================================
-- 28. DATASET CONTROL TOTALS
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM staging_customers)
        AS raw_customer_rows,

    (SELECT COUNT(*) FROM customers)
        AS clean_customer_rows,

    (SELECT COUNT(*) FROM staging_orders)
        AS raw_order_rows,

    (SELECT COUNT(*) FROM orders)
        AS valid_order_rows,

    (SELECT COUNT(*) FROM archived_orders)
        AS archived_order_rows,

    (SELECT COUNT(*) FROM combined_orders)
        AS combined_order_rows,

    (SELECT COUNT(*) FROM data_quality_issues)
        AS detected_quality_issues;

-- ============================================================
-- END OF POWER QUERY DATABASE IMPLEMENTATION
-- ============================================================
