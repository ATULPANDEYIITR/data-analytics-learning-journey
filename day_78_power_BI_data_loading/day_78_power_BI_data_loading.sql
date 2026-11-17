/*
===============================================================================
POWER BI DATA LOADING
===============================================================================

PostgreSQL implementation of a data integration and refresh management system.

Models:
1. Excel, CSV, database, and web data sources.
2. Connection configuration and ownership.
3. Source tables and imported datasets.
4. Data validation and rejected records.
5. Import, DirectQuery, and Live Connection modes.
6. Refresh execution and audit history.
7. Semantic model metadata.
8. Reporting and aggregation.
9. Refresh eligibility and connection governance.

Requirements:
PostgreSQL 15+

Execution:
Run the complete script in a PostgreSQL database.

===============================================================================
*/


-- ============================================================================
-- 1. SCHEMA
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS powerbi_loading;

SET search_path TO powerbi_loading, public;


-- ============================================================================
-- 2. ENUMERATIONS
-- ============================================================================

CREATE TYPE source_type AS ENUM (
    'EXCEL',
    'CSV',
    'DATABASE',
    'WEB'
);

CREATE TYPE storage_mode AS ENUM (
    'IMPORT',
    'DIRECTQUERY',
    'LIVE_CONNECTION'
);

CREATE TYPE connection_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'FAILED',
    'DISABLED'
);

CREATE TYPE refresh_status AS ENUM (
    'PENDING',
    'RUNNING',
    'SUCCESS',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE validation_status AS ENUM (
    'VALID',
    'INVALID',
    'WARNING'
);


-- ============================================================================
-- 3. USERS AND DATA CONNECTIONS
-- ============================================================================

CREATE TABLE data_owners (
    owner_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    owner_name VARCHAR(150) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(owner_name)) > 0)
);


CREATE TABLE data_connections (
    connection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_name VARCHAR(150) NOT NULL UNIQUE,

    source source_type NOT NULL,

    connection_location TEXT NOT NULL,

    owner_id BIGINT NOT NULL
        REFERENCES data_owners(owner_id),

    status connection_status NOT NULL DEFAULT 'ACTIVE',

    timeout_seconds INTEGER NOT NULL DEFAULT 30,

    ssl_required BOOLEAN NOT NULL DEFAULT TRUE,

    credentials_reference TEXT,

    last_connected_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(connection_name)) > 0),

    CHECK (length(trim(connection_location)) > 0),

    CHECK (timeout_seconds BETWEEN 1 AND 3600),

    CHECK (
        source <> 'WEB'
        OR connection_location ~ '^https://'
    ),

    CHECK (
        source <> 'DATABASE'
        OR ssl_required = TRUE
    )
);


CREATE INDEX idx_connections_owner
ON data_connections(owner_id);

CREATE INDEX idx_connections_source_status
ON data_connections(source, status);


-- ============================================================================
-- 4. SOURCE TABLES
-- ============================================================================

CREATE TABLE source_tables (
    source_table_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES data_connections(connection_id),

    source_object_name VARCHAR(255) NOT NULL,

    source_schema_name VARCHAR(150),

    description TEXT,

    estimated_rows BIGINT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(connection_id, source_schema_name, source_object_name),

    CHECK (length(trim(source_object_name)) > 0),

    CHECK (
        estimated_rows IS NULL
        OR estimated_rows >= 0
    )
);


CREATE INDEX idx_source_tables_connection
ON source_tables(connection_id);


-- ============================================================================
-- 5. SEMANTIC MODELS
-- ============================================================================

CREATE TABLE semantic_models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_name VARCHAR(150) NOT NULL UNIQUE,

    owner_id BIGINT NOT NULL
        REFERENCES data_owners(owner_id),

    description TEXT,

    storage_mode storage_mode NOT NULL,

    external_model_reference TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(model_name)) > 0),

    CHECK (
        storage_mode <> 'LIVE_CONNECTION'
        OR external_model_reference IS NOT NULL
    )
);


CREATE TABLE model_tables (
    model_table_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    source_table_id BIGINT
        REFERENCES source_tables(source_table_id),

    table_name VARCHAR(150) NOT NULL,

    storage_mode storage_mode NOT NULL,

    last_loaded_at TIMESTAMPTZ,

    record_count BIGINT NOT NULL DEFAULT 0,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE(model_id, table_name),

    CHECK (record_count >= 0)
);


CREATE INDEX idx_model_tables_model
ON model_tables(model_id);


-- ============================================================================
-- 6. REFRESH EXECUTIONS
-- ============================================================================

CREATE TABLE refresh_executions (
    refresh_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id),

    connection_id BIGINT
        REFERENCES data_connections(connection_id),

    refresh_status refresh_status NOT NULL DEFAULT 'PENDING',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    rows_read BIGINT NOT NULL DEFAULT 0,

    rows_loaded BIGINT NOT NULL DEFAULT 0,

    rows_rejected BIGINT NOT NULL DEFAULT 0,

    error_message TEXT,

    requested_by BIGINT
        REFERENCES data_owners(owner_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (rows_read >= 0),

    CHECK (rows_loaded >= 0),

    CHECK (rows_rejected >= 0),

    CHECK (rows_loaded + rows_rejected <= rows_read),

    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    ),

    CHECK (
        refresh_status <> 'SUCCESS'
        OR completed_at IS NOT NULL
    )
);


CREATE INDEX idx_refresh_model_date
ON refresh_executions(model_id, created_at DESC);

CREATE INDEX idx_refresh_status
ON refresh_executions(refresh_status);


-- ============================================================================
-- 7. DATA QUALITY RULES
-- ============================================================================

CREATE TABLE validation_rules (
    rule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    rule_name VARCHAR(150) NOT NULL UNIQUE,

    target_column VARCHAR(150) NOT NULL,

    rule_description TEXT NOT NULL,

    severity validation_status NOT NULL,

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (length(trim(rule_name)) > 0)
);


INSERT INTO validation_rules (
    rule_name,
    target_column,
    rule_description,
    severity
)
VALUES
(
    'product_not_empty',
    'product',
    'Product name must not be empty.',
    'INVALID'
),
(
    'quantity_non_negative',
    'quantity',
    'Quantity must be zero or greater.',
    'INVALID'
),
(
    'revenue_non_negative',
    'revenue',
    'Revenue must be zero or greater.',
    'INVALID'
),
(
    'revenue_finite',
    'revenue',
    'Revenue must be a finite numeric value.',
    'INVALID'
);


-- ============================================================================
-- 8. SALES DATASET
-- ============================================================================

CREATE TABLE sales_data (
    sales_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_table_id BIGINT NOT NULL
        REFERENCES model_tables(model_table_id),

    source_record_key VARCHAR(150),

    product VARCHAR(150) NOT NULL,

    quantity INTEGER NOT NULL,

    revenue NUMERIC(18, 2) NOT NULL,

    source_modified_at TIMESTAMPTZ,

    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model_table_id, source_record_key),

    CHECK (length(trim(product)) > 0),

    CHECK (quantity >= 0),

    CHECK (revenue >= 0)
);


CREATE INDEX idx_sales_product
ON sales_data(product);

CREATE INDEX idx_sales_model_table
ON sales_data(model_table_id);

CREATE INDEX idx_sales_loaded_at
ON sales_data(loaded_at);


-- ============================================================================
-- 9. REJECTED RECORDS
-- ============================================================================

CREATE TABLE rejected_records (
    rejected_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    refresh_id BIGINT NOT NULL
        REFERENCES refresh_executions(refresh_id),

    source_record_key VARCHAR(150),

    raw_record JSONB NOT NULL,

    rejection_reason TEXT NOT NULL,

    rejected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_rejected_refresh
ON rejected_records(refresh_id);


-- ============================================================================
-- 10. DATA CONNECTION SECURITY
-- ============================================================================

CREATE TABLE connection_access (
    access_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES data_connections(connection_id)
        ON DELETE CASCADE,

    owner_id BIGINT NOT NULL
        REFERENCES data_owners(owner_id)
        ON DELETE CASCADE,

    can_read BOOLEAN NOT NULL DEFAULT FALSE,

    can_refresh BOOLEAN NOT NULL DEFAULT FALSE,

    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(connection_id, owner_id),

    CHECK (
        can_refresh = FALSE
        OR can_read = TRUE
    )
);


-- ============================================================================
-- 11. REFRESH HISTORY TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_refresh_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF TG_OP = 'INSERT' THEN

        IF NEW.refresh_status NOT IN ('PENDING', 'RUNNING') THEN
            RAISE EXCEPTION
                'New refresh must start as PENDING or RUNNING';
        END IF;

        RETURN NEW;
    END IF;

    IF OLD.refresh_status IN (
        'SUCCESS',
        'FAILED',
        'CANCELLED'
    ) THEN

        RAISE EXCEPTION
            'Completed refresh records are immutable';

    END IF;

    IF NEW.refresh_status = 'RUNNING'
       AND NEW.started_at IS NULL THEN

        NEW.started_at := CURRENT_TIMESTAMP;

    END IF;

    IF NEW.refresh_status IN (
        'SUCCESS',
        'FAILED',
        'CANCELLED'
    ) THEN

        NEW.completed_at := CURRENT_TIMESTAMP;

    END IF;

    IF NEW.refresh_status = 'SUCCESS'
       AND NEW.error_message IS NOT NULL THEN

        RAISE EXCEPTION
            'Successful refresh cannot contain an error';

    END IF;

    IF NEW.refresh_status = 'FAILED'
       AND NEW.error_message IS NULL THEN

        RAISE EXCEPTION
            'Failed refresh must include an error message';

    END IF;

    RETURN NEW;

END;
$$;


CREATE TRIGGER trg_refresh_transition
BEFORE INSERT OR UPDATE ON refresh_executions
FOR EACH ROW
EXECUTE FUNCTION validate_refresh_transition();


-- ============================================================================
-- 12. UPDATE MODEL TABLE METADATA AFTER SUCCESSFUL REFRESH
-- ============================================================================

CREATE OR REPLACE FUNCTION update_model_table_after_refresh()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.refresh_status = 'SUCCESS' THEN

        UPDATE model_tables
        SET
            last_loaded_at = NEW.completed_at,
            record_count = NEW.rows_loaded
        WHERE model_id = NEW.model_id
          AND storage_mode = 'IMPORT';

    END IF;

    RETURN NEW;

END;
$$;


CREATE TRIGGER trg_update_model_metadata
AFTER UPDATE OF refresh_status ON refresh_executions
FOR EACH ROW
EXECUTE FUNCTION update_model_table_after_refresh();


-- ============================================================================
-- 13. CONNECTION VALIDATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_connection(
    p_connection_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    connection_record data_connections%ROWTYPE;
BEGIN

    SELECT *
    INTO connection_record
    FROM data_connections
    WHERE connection_id = p_connection_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Connection does not exist';
    END IF;

    IF connection_record.status <> 'ACTIVE' THEN
        RETURN FALSE;
    END IF;

    IF connection_record.timeout_seconds <= 0 THEN
        RETURN FALSE;
    END IF;

    IF connection_record.source = 'WEB'
       AND connection_record.connection_location !~ '^https://' THEN

        RETURN FALSE;

    END IF;

    RETURN TRUE;

END;
$$;


-- ============================================================================
-- 14. REFRESH ELIGIBILITY FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION can_refresh_model(
    p_model_id BIGINT,
    p_owner_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    model_record semantic_models%ROWTYPE;
BEGIN

    SELECT *
    INTO model_record
    FROM semantic_models
    WHERE model_id = p_model_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF model_record.owner_id = p_owner_id THEN
        RETURN TRUE;
    END IF;

    RETURN EXISTS (
        SELECT 1
        FROM connection_access ca
        JOIN model_tables mt
          ON mt.source_table_id IS NOT NULL
        JOIN source_tables st
          ON st.source_table_id = mt.source_table_id
        WHERE mt.model_id = p_model_id
          AND st.connection_id = ca.connection_id
          AND ca.owner_id = p_owner_id
          AND ca.can_read = TRUE
          AND ca.can_refresh = TRUE
    );

END;
$$;


-- ============================================================================
-- 15. REFRESH PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE start_refresh(
    p_model_id BIGINT,
    p_connection_id BIGINT,
    p_owner_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    new_refresh_id BIGINT;
BEGIN

    IF NOT can_refresh_model(
        p_model_id,
        p_owner_id
    ) THEN

        RAISE EXCEPTION
            'User is not eligible to refresh this model';

    END IF;

    IF NOT validate_connection(
        p_connection_id
    ) THEN

        RAISE EXCEPTION
            'Data connection is not eligible for refresh';

    END IF;

    IF EXISTS (
        SELECT 1
        FROM refresh_executions
        WHERE model_id = p_model_id
          AND refresh_status = 'RUNNING'
    ) THEN

        RAISE EXCEPTION
            'Another refresh is already running';

    END IF;

    INSERT INTO refresh_executions (
        model_id,
        connection_id,
        refresh_status,
        started_at,
        requested_by
    )
    VALUES (
        p_model_id,
        p_connection_id,
        'RUNNING',
        CURRENT_TIMESTAMP,
        p_owner_id
    )
    RETURNING refresh_id INTO new_refresh_id;

    RAISE NOTICE
        'Refresh started with ID %',
        new_refresh_id;

END;
$$;


-- ============================================================================
-- 16. REFRESH COMPLETION PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE complete_refresh(
    p_refresh_id BIGINT,
    p_rows_read BIGINT,
    p_rows_loaded BIGINT,
    p_rows_rejected BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN

    IF p_rows_read < 0
       OR p_rows_loaded < 0
       OR p_rows_rejected < 0 THEN

        RAISE EXCEPTION
            'Row counts cannot be negative';

    END IF;

    IF p_rows_loaded + p_rows_rejected > p_rows_read THEN

        RAISE EXCEPTION
            'Loaded and rejected counts exceed rows read';

    END IF;

    UPDATE refresh_executions
    SET
        refresh_status = 'SUCCESS',
        rows_read = p_rows_read,
        rows_loaded = p_rows_loaded,
        rows_rejected = p_rows_rejected
    WHERE refresh_id = p_refresh_id
      AND refresh_status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No active refresh found';
    END IF;

END;
$$;


-- ============================================================================
-- 17. REPORTING VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW sales_revenue_summary AS
SELECT
    mt.model_id,
    sm.model_name,
    mt.table_name,
    sd.product,
    SUM(sd.quantity) AS total_quantity,
    SUM(sd.revenue) AS total_revenue,
    COUNT(*) AS transaction_count
FROM sales_data sd
JOIN model_tables mt
    ON mt.model_table_id = sd.model_table_id
JOIN semantic_models sm
    ON sm.model_id = mt.model_id
GROUP BY
    mt.model_id,
    sm.model_name,
    mt.table_name,
    sd.product;


CREATE OR REPLACE VIEW refresh_performance AS
SELECT
    re.refresh_id,
    sm.model_name,
    dc.connection_name,
    re.refresh_status,
    re.rows_read,
    re.rows_loaded,
    re.rows_rejected,
    re.started_at,
    re.completed_at,
    CASE
        WHEN re.started_at IS NOT NULL
         AND re.completed_at IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (
                re.completed_at - re.started_at
            )
        )
        ELSE NULL
    END AS duration_seconds
FROM refresh_executions re
JOIN semantic_models sm
    ON sm.model_id = re.model_id
LEFT JOIN data_connections dc
    ON dc.connection_id = re.connection_id;


CREATE OR REPLACE VIEW active_connection_inventory AS
SELECT
    dc.connection_id,
    dc.connection_name,
    dc.source,
    dc.connection_location,
    dc.status,
    d.owner_name,
    dc.last_connected_at
FROM data_connections dc
JOIN data_owners d
    ON d.owner_id = dc.owner_id
WHERE dc.status = 'ACTIVE';


-- ============================================================================
-- 18. SAMPLE DATA
-- ============================================================================

INSERT INTO data_owners (
    owner_name,
    email
)
VALUES
(
    'Enterprise Analytics Team',
    'analytics@example.com'
),
(
    'Business Intelligence Manager',
    'bi.manager@example.com'
),
(
    'Data Engineering Team',
    'engineering@example.com'
);


INSERT INTO data_connections (
    connection_name,
    source,
    connection_location,
    owner_id,
    status,
    timeout_seconds,
    ssl_required
)
VALUES
(
    'Monthly Sales Excel',
    'EXCEL',
    '/data/monthly_sales.xlsx',
    1,
    'ACTIVE',
    30,
    TRUE
),
(
    'Regional CSV Sales',
    'CSV',
    '/data/regional_sales.csv',
    1,
    'ACTIVE',
    30,
    TRUE
),
(
    'Corporate PostgreSQL',
    'DATABASE',
    'postgresql://analytics-db/sales',
    3,
    'ACTIVE',
    60,
    TRUE
),
(
    'External Sales API',
    'WEB',
    'https://api.example.com/sales',
    3,
    'ACTIVE',
    20,
    TRUE
),
(
    'Disabled Legacy CSV',
    'CSV',
    '/data/legacy.csv',
    2,
    'DISABLED',
    30,
    TRUE
);


INSERT INTO source_tables (
    connection_id,
    source_object_name,
    source_schema_name,
    description,
    estimated_rows
)
VALUES
(
    1,
    'SalesWorksheet',
    'ExcelWorkbook',
    'Monthly sales worksheet.',
    5000
),
(
    2,
    'regional_sales',
    'public',
    'Regional sales export.',
    2500
),
(
    3,
    'sales_transactions',
    'public',
    'Central database sales table.',
    500000
),
(
    4,
    'sales_endpoint',
    'api',
    'External sales endpoint.',
    10000
);


INSERT INTO semantic_models (
    model_name,
    owner_id,
    description,
    storage_mode,
    external_model_reference
)
VALUES
(
    'Corporate Sales Import Model',
    1,
    'Imported sales reporting model.',
    'IMPORT',
    NULL
),
(
    'Operational Sales Direct Model',
    3,
    'Operational source-query model.',
    'DIRECTQUERY',
    NULL
),
(
    'Central Enterprise Model',
    2,
    'Shared semantic model.',
    'LIVE_CONNECTION',
    'central-enterprise-model'
);


INSERT INTO model_tables (
    model_id,
    source_table_id,
    table_name,
    storage_mode
)
VALUES
(
    1,
    1,
    'ExcelSales',
    'IMPORT'
),
(
    1,
    2,
    'CSVSales',
    'IMPORT'
),
(
    2,
    3,
    'DatabaseSales',
    'DIRECTQUERY'
);


INSERT INTO connection_access (
    connection_id,
    owner_id,
    can_read,
    can_refresh
)
VALUES
(
    1,
    2,
    TRUE,
    TRUE
),
(
    2,
    2,
    TRUE,
    FALSE
),
(
    3,
    1,
    TRUE,
    TRUE
);


-- ============================================================================
-- 19. IMPORT SAMPLE DATA
-- ============================================================================

INSERT INTO sales_data (
    model_table_id,
    source_record_key,
    product,
    quantity,
    revenue
)
VALUES
(
    1,
    'EXCEL-001',
    'Laptop',
    5,
    250000
),
(
    1,
    'EXCEL-002',
    'Monitor',
    8,
    120000
),
(
    1,
    'EXCEL-003',
    'Keyboard',
    20,
    40000
),
(
    2,
    'CSV-001',
    'Laptop',
    3,
    150000
),
(
    2,
    'CSV-002',
    'Mouse',
    15,
    15000
);


-- ============================================================================
-- 20. SAMPLE REFRESH HISTORY
-- ============================================================================

INSERT INTO refresh_executions (
    model_id,
    connection_id,
    refresh_status,
    started_at,
    rows_read,
    rows_loaded,
    rows_rejected,
    requested_by
)
VALUES
(
    1,
    1,
    'PENDING',
    NULL,
    0,
    0,
    0,
    1
);


UPDATE refresh_executions
SET
    refresh_status = 'RUNNING',
    started_at = CURRENT_TIMESTAMP
WHERE refresh_id = 1;


CALL complete_refresh(
    1,
    100,
    95,
    5
);


-- ============================================================================
-- 21. VALIDATION AND RETRIEVAL QUERIES
-- ============================================================================

-- Active connections.

SELECT *
FROM active_connection_inventory
ORDER BY connection_name;


-- Source inventory.

SELECT
    dc.connection_name,
    dc.source,
    st.source_object_name,
    st.estimated_rows
FROM data_connections dc
JOIN source_tables st
    ON st.connection_id = dc.connection_id
ORDER BY dc.connection_name;


-- Semantic model configuration.

SELECT
    sm.model_name,
    sm.storage_mode,
    mt.table_name,
    mt.record_count
FROM semantic_models sm
LEFT JOIN model_tables mt
    ON mt.model_id = sm.model_id
ORDER BY sm.model_name;


-- Validate database connections.

SELECT
    connection_id,
    connection_name,
    validate_connection(connection_id) AS connection_valid
FROM data_connections;


-- Check user refresh eligibility.

SELECT
    model_id,
    model_name,
    can_refresh_model(model_id, 2) AS manager_can_refresh
FROM semantic_models;


-- ============================================================================
-- 22. AGGREGATION QUERIES
-- ============================================================================

-- Revenue by product.

SELECT
    product,
    SUM(total_quantity) AS quantity_sold,
    SUM(total_revenue) AS revenue
FROM sales_revenue_summary
GROUP BY product
ORDER BY revenue DESC;


-- Revenue by semantic model.

SELECT
    model_name,
    SUM(total_revenue) AS model_revenue,
    SUM(transaction_count) AS transaction_count
FROM sales_revenue_summary
GROUP BY model_name
ORDER BY model_revenue DESC;


-- Overall sales metrics.

SELECT
    COUNT(*) AS transaction_count,
    SUM(quantity) AS total_quantity,
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS average_transaction_revenue
FROM sales_data;


-- ============================================================================
-- 23. DATA QUALITY REPORTING
-- ============================================================================

SELECT
    rule_name,
    target_column,
    severity,
    is_enabled
FROM validation_rules
ORDER BY rule_name;


SELECT
    refresh_id,
    COUNT(*) AS rejected_record_count
FROM rejected_records
GROUP BY refresh_id
ORDER BY refresh_id;


-- Identify potential duplicate business records.

SELECT
    model_table_id,
    product,
    quantity,
    revenue,
    COUNT(*) AS duplicate_count
FROM sales_data
GROUP BY
    model_table_id,
    product,
    quantity,
    revenue
HAVING COUNT(*) > 1;


-- ============================================================================
-- 24. REFRESH PERFORMANCE REPORT
-- ============================================================================

SELECT
    model_name,
    connection_name,
    refresh_status,
    rows_read,
    rows_loaded,
    rows_rejected,
    duration_seconds
FROM refresh_performance
ORDER BY refresh_id DESC;


-- ============================================================================
-- 25. CTE-BASED LOADING QUALITY ANALYSIS
-- ============================================================================

WITH refresh_metrics AS (
    SELECT
        model_id,
        COUNT(*) AS refresh_count,
        SUM(rows_read) AS total_rows_read,
        SUM(rows_loaded) AS total_rows_loaded,
        SUM(rows_rejected) AS total_rows_rejected
    FROM refresh_executions
    GROUP BY model_id
),
quality_analysis AS (
    SELECT
        model_id,
        refresh_count,
        total_rows_read,
        total_rows_loaded,
        total_rows_rejected,
        CASE
            WHEN total_rows_read = 0 THEN 0
            ELSE ROUND(
                100.0 * total_rows_loaded
                / total_rows_read,
                2
            )
        END AS successful_load_percentage
    FROM refresh_metrics
)
SELECT
    sm.model_name,
    qa.*
FROM quality_analysis qa
JOIN semantic_models sm
    ON sm.model_id = qa.model_id
ORDER BY successful_load_percentage DESC;


-- ============================================================================
-- 26. STORAGE MODE COMPARISON
-- ============================================================================

SELECT
    storage_mode,
    COUNT(*) AS configured_tables,
    SUM(record_count) AS imported_record_count
FROM model_tables
GROUP BY storage_mode
ORDER BY storage_mode;


-- ============================================================================
-- 27. TRANSACTION AND FAILURE HANDLING EXAMPLE
-- ============================================================================

-- This transaction demonstrates atomic database-side
-- insertion of records and refresh metadata.

BEGIN;

SAVEPOINT before_import;

INSERT INTO sales_data (
    model_table_id,
    source_record_key,
    product,
    quantity,
    revenue
)
VALUES
(
    1,
    'EXCEL-004',
    'Tablet',
    4,
    80000
);

-- Confirm the new record.

SELECT *
FROM sales_data
WHERE source_record_key = 'EXCEL-004';

-- Preserve the valid operation.

RELEASE SAVEPOINT before_import;

COMMIT;


-- ============================================================================
-- 28. EXPECTED FAILURE EXAMPLES
-- ============================================================================

-- The following statements are intentionally commented out.
-- Execute separately to observe the database constraints.

-- Negative quantity:
-- INSERT INTO sales_data
-- (model_table_id, product, quantity, revenue)
-- VALUES (1, 'Invalid Product', -5, 1000);

-- Negative revenue:
-- INSERT INTO sales_data
-- (model_table_id, product, quantity, revenue)
-- VALUES (1, 'Invalid Product', 5, -1000);

-- Invalid web connection:
-- INSERT INTO data_connections
-- (connection_name, source, connection_location, owner_id)
-- VALUES
-- ('Invalid API', 'WEB', 'http://example.com', 1);

-- Invalid timeout:
-- INSERT INTO data_connections
-- (connection_name, source, connection_location,
--  owner_id, timeout_seconds)
-- VALUES
-- ('Invalid Timeout', 'CSV', '/data/file.csv', 1, 0);


-- ============================================================================
-- 29. OPERATIONAL SUMMARY
-- ============================================================================

SELECT
    (SELECT COUNT(*) FROM data_connections)
        AS total_connections,

    (SELECT COUNT(*)
     FROM data_connections
     WHERE status = 'ACTIVE')
        AS active_connections,

    (SELECT COUNT(*) FROM semantic_models)
        AS semantic_models,

    (SELECT COUNT(*) FROM model_tables)
        AS model_tables,

    (SELECT COUNT(*) FROM sales_data)
        AS loaded_sales_records,

    (SELECT COUNT(*)
     FROM refresh_executions
     WHERE refresh_status = 'SUCCESS')
        AS successful_refreshes,

    (SELECT COUNT(*)
     FROM refresh_executions
     WHERE refresh_status = 'FAILED')
        AS failed_refreshes;


-- ============================================================================
-- END OF POWER BI DATA LOADING SCRIPT
-- ============================================================================
