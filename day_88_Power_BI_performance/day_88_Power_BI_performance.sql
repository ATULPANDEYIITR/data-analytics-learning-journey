-- ============================================================
-- POWER BI PERFORMANCE ENGINEERING
-- PostgreSQL 14+
--
-- Purpose:
-- 1. Store semantic model metadata.
-- 2. Track table, column and relationship characteristics.
-- 3. Record storage modes and refresh behavior.
-- 4. Maintain DAX measure metadata.
-- 5. Capture query execution metrics.
-- 6. Evaluate performance policies.
-- 7. Maintain aggregation definitions.
-- 8. Identify model optimization opportunities.
-- 9. Produce performance reports.
--
-- Important:
-- This database is a performance governance and telemetry
-- repository. It does not execute DAX or replace VertiPaq,
-- Power Query, Power BI Desktop, or the Power BI service.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS bi_performance;

SET search_path TO bi_performance, public;


-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE storage_mode AS ENUM (
    'IMPORT',
    'DIRECTQUERY',
    'DUAL',
    'DIRECTLAKE'
);

CREATE TYPE table_role AS ENUM (
    'FACT',
    'DIMENSION',
    'BRIDGE'
);

CREATE TYPE severity_level AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);

CREATE TYPE query_status AS ENUM (
    'PENDING',
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE dax_pattern AS ENUM (
    'SIMPLE_AGGREGATION',
    'ROW_ITERATION',
    'FILTER_ALL',
    'VARIABLE_REUSE',
    'PREAGGREGATED'
);


-- ============================================================
-- 2. SEMANTIC MODELS
-- ============================================================

CREATE TABLE semantic_models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_name VARCHAR(150) NOT NULL UNIQUE,

    workspace_name VARCHAR(150) NOT NULL,

    business_domain VARCHAR(100) NOT NULL,

    description TEXT,

    owner_name VARCHAR(150) NOT NULL,

    capacity_name VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_model_name
        CHECK (LENGTH(TRIM(model_name)) > 0),

    CONSTRAINT valid_workspace_name
        CHECK (LENGTH(TRIM(workspace_name)) > 0)
);


-- ============================================================
-- 3. MODEL TABLES
-- ============================================================

CREATE TABLE model_tables (
    table_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    table_name VARCHAR(150) NOT NULL,

    role table_role NOT NULL,

    row_count BIGINT NOT NULL DEFAULT 0,

    storage_mode storage_mode NOT NULL DEFAULT 'IMPORT',

    source_name VARCHAR(200),

    query_folding BOOLEAN NOT NULL DEFAULT TRUE,

    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,

    refresh_duration_ms NUMERIC(14,2),

    estimated_memory_mb NUMERIC(14,2),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_table_per_model
        UNIQUE (model_id, table_name),

    CONSTRAINT valid_row_count
        CHECK (row_count >= 0),

    CONSTRAINT valid_refresh_duration
        CHECK (
            refresh_duration_ms IS NULL
            OR refresh_duration_ms >= 0
        ),

    CONSTRAINT valid_memory
        CHECK (
            estimated_memory_mb IS NULL
            OR estimated_memory_mb >= 0
        )
);


-- ============================================================
-- 4. MODEL COLUMNS
-- ============================================================

CREATE TABLE model_columns (
    column_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    table_id BIGINT NOT NULL
        REFERENCES model_tables(table_id)
        ON DELETE CASCADE,

    column_name VARCHAR(150) NOT NULL,

    data_type VARCHAR(30) NOT NULL,

    cardinality BIGINT NOT NULL DEFAULT 0,

    is_key BOOLEAN NOT NULL DEFAULT FALSE,

    is_used BOOLEAN NOT NULL DEFAULT TRUE,

    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,

    nullable BOOLEAN NOT NULL DEFAULT TRUE,

    estimated_memory_mb NUMERIC(14,4),

    CONSTRAINT unique_column_per_table
        UNIQUE (table_id, column_name),

    CONSTRAINT valid_cardinality
        CHECK (cardinality >= 0),

    CONSTRAINT valid_data_type
        CHECK (
            data_type IN (
                'INTEGER',
                'DECIMAL',
                'STRING',
                'DATE',
                'DATETIME',
                'BOOLEAN'
            )
        ),

    CONSTRAINT valid_column_memory
        CHECK (
            estimated_memory_mb IS NULL
            OR estimated_memory_mb >= 0
        )
);


-- ============================================================
-- 5. MODEL RELATIONSHIPS
-- ============================================================

CREATE TABLE model_relationships (
    relationship_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    from_column_id BIGINT NOT NULL
        REFERENCES model_columns(column_id),

    to_column_id BIGINT NOT NULL
        REFERENCES model_columns(column_id),

    cardinality VARCHAR(20) NOT NULL,

    bidirectional BOOLEAN NOT NULL DEFAULT FALSE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT distinct_relationship_columns
        CHECK (from_column_id <> to_column_id),

    CONSTRAINT valid_relationship_cardinality
        CHECK (
            cardinality IN (
                'ONE_TO_ONE',
                'ONE_TO_MANY',
                'MANY_TO_ONE',
                'MANY_TO_MANY'
            )
        )
);


-- Ensure relationship columns belong to the same model.

CREATE OR REPLACE FUNCTION validate_relationship_model()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_model BIGINT;
    target_model BIGINT;
BEGIN
    SELECT mt.model_id
    INTO source_model
    FROM model_columns mc
    JOIN model_tables mt
        ON mt.table_id = mc.table_id
    WHERE mc.column_id = NEW.from_column_id;

    SELECT mt.model_id
    INTO target_model
    FROM model_columns mc
    JOIN model_tables mt
        ON mt.table_id = mc.table_id
    WHERE mc.column_id = NEW.to_column_id;

    IF source_model IS NULL OR target_model IS NULL THEN
        RAISE EXCEPTION
            'Relationship references missing column';
    END IF;

    IF source_model <> NEW.model_id
       OR target_model <> NEW.model_id THEN
        RAISE EXCEPTION
            'Relationship columns must belong to the specified model';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_relationship_model
BEFORE INSERT OR UPDATE
ON model_relationships
FOR EACH ROW
EXECUTE FUNCTION validate_relationship_model();


-- ============================================================
-- 6. DAX MEASURE REGISTRY
-- ============================================================

CREATE TABLE dax_measures (
    measure_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    measure_name VARCHAR(150) NOT NULL,

    dax_expression TEXT NOT NULL,

    pattern dax_pattern NOT NULL,

    estimated_iterations BIGINT NOT NULL DEFAULT 0,

    repeated_expressions INTEGER NOT NULL DEFAULT 0,

    business_purpose TEXT,

    owner_name VARCHAR(150),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_measure_per_model
        UNIQUE (model_id, measure_name),

    CONSTRAINT valid_iterations
        CHECK (estimated_iterations >= 0),

    CONSTRAINT valid_repetitions
        CHECK (repeated_expressions >= 0),

    CONSTRAINT nonempty_dax
        CHECK (LENGTH(TRIM(dax_expression)) > 0)
);


-- ============================================================
-- 7. QUERY EXECUTION TELEMETRY
-- ============================================================

CREATE TABLE query_executions (
    query_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    measure_id BIGINT
        REFERENCES dax_measures(measure_id)
        ON DELETE SET NULL,

    query_name VARCHAR(200) NOT NULL,

    query_type VARCHAR(40) NOT NULL,

    storage_engine_ms NUMERIC(14,2) NOT NULL DEFAULT 0,

    formula_engine_ms NUMERIC(14,2) NOT NULL DEFAULT 0,

    source_execution_ms NUMERIC(14,2) NOT NULL DEFAULT 0,

    visual_render_ms NUMERIC(14,2) NOT NULL DEFAULT 0,

    rows_scanned BIGINT NOT NULL DEFAULT 0,

    rows_returned BIGINT NOT NULL DEFAULT 0,

    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,

    execution_status query_status NOT NULL DEFAULT 'PENDING',

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    user_name VARCHAR(150),

    CONSTRAINT valid_query_type
        CHECK (
            query_type IN (
                'AGGREGATION',
                'DETAIL',
                'TIME_INTELLIGENCE',
                'CROSS_FILTER'
            )
        ),

    CONSTRAINT valid_query_timings
        CHECK (
            storage_engine_ms >= 0
            AND formula_engine_ms >= 0
            AND source_execution_ms >= 0
            AND visual_render_ms >= 0
        ),

    CONSTRAINT valid_query_rows
        CHECK (
            rows_scanned >= 0
            AND rows_returned >= 0
            AND rows_returned <= rows_scanned
        )
);


-- ============================================================
-- 8. PERFORMANCE POLICY
-- ============================================================

CREATE TABLE performance_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    policy_name VARCHAR(150) NOT NULL,

    max_total_query_ms NUMERIC(14,2) NOT NULL,

    max_formula_share NUMERIC(6,5) NOT NULL,

    max_source_ms NUMERIC(14,2) NOT NULL,

    max_visual_ms NUMERIC(14,2) NOT NULL,

    max_unused_columns INTEGER NOT NULL DEFAULT 0,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_policy_per_model
        UNIQUE (model_id, policy_name),

    CONSTRAINT valid_max_query
        CHECK (max_total_query_ms > 0),

    CONSTRAINT valid_formula_share
        CHECK (
            max_formula_share >= 0
            AND max_formula_share <= 1
        ),

    CONSTRAINT valid_source_limit
        CHECK (max_source_ms >= 0),

    CONSTRAINT valid_visual_limit
        CHECK (max_visual_ms >= 0),

    CONSTRAINT valid_unused_limit
        CHECK (max_unused_columns >= 0)
);


-- ============================================================
-- 9. PERFORMANCE FINDINGS
-- ============================================================

CREATE TABLE optimization_findings (
    finding_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    table_id BIGINT
        REFERENCES model_tables(table_id)
        ON DELETE CASCADE,

    column_id BIGINT
        REFERENCES model_columns(column_id)
        ON DELETE CASCADE,

    category VARCHAR(80) NOT NULL,

    severity severity_level NOT NULL,

    description TEXT NOT NULL,

    recommendation TEXT NOT NULL,

    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,

    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    resolved_at TIMESTAMPTZ,

    CONSTRAINT valid_finding_resolution
        CHECK (
            (is_resolved = FALSE AND resolved_at IS NULL)
            OR
            (is_resolved = TRUE AND resolved_at IS NOT NULL)
        )
);


-- ============================================================
-- 10. AGGREGATION DEFINITIONS
-- ============================================================

CREATE TABLE aggregation_definitions (
    aggregation_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES semantic_models(model_id)
        ON DELETE CASCADE,

    aggregation_name VARCHAR(150) NOT NULL,

    detail_table_id BIGINT NOT NULL
        REFERENCES model_tables(table_id),

    aggregation_table_id BIGINT NOT NULL
        REFERENCES model_tables(table_id),

    aggregation_grain TEXT NOT NULL,

    aggregation_expression TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_aggregation_name
        UNIQUE (model_id, aggregation_name),

    CONSTRAINT distinct_aggregation_tables
        CHECK (
            detail_table_id <> aggregation_table_id
        )
);


-- ============================================================
-- 11. INDEXES
-- ============================================================

CREATE INDEX idx_model_tables_model
    ON model_tables(model_id);

CREATE INDEX idx_model_columns_table
    ON model_columns(table_id);

CREATE INDEX idx_relationship_model
    ON model_relationships(model_id);

CREATE INDEX idx_dax_measures_model
    ON dax_measures(model_id);

CREATE INDEX idx_query_model_date
    ON query_executions(model_id, executed_at DESC);

CREATE INDEX idx_query_slow
    ON query_executions(model_id, executed_at DESC)
    WHERE execution_status = 'COMPLETED';

CREATE INDEX idx_findings_unresolved
    ON optimization_findings(
        model_id,
        severity,
        detected_at DESC
    )
    WHERE is_resolved = FALSE;

CREATE INDEX idx_active_policies
    ON performance_policies(model_id)
    WHERE is_active = TRUE;

CREATE INDEX idx_active_aggregations
    ON aggregation_definitions(model_id)
    WHERE is_active = TRUE;


-- ============================================================
-- 12. QUERY METRICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_query_performance AS
SELECT
    q.query_id,
    q.model_id,
    sm.model_name,
    q.query_name,
    q.query_type,

    q.storage_engine_ms,
    q.formula_engine_ms,
    q.source_execution_ms,
    q.visual_render_ms,

    (
        q.storage_engine_ms
        + q.formula_engine_ms
        + q.source_execution_ms
        + q.visual_render_ms
    ) AS total_execution_ms,

    ROUND(
        (
            q.formula_engine_ms /
            NULLIF(
                q.storage_engine_ms
                + q.formula_engine_ms
                + q.source_execution_ms
                + q.visual_render_ms,
                0
            )
        ) * 100,
        2
    ) AS formula_engine_share_percent,

    q.rows_scanned,
    q.rows_returned,

    ROUND(
        (
            q.rows_returned::NUMERIC /
            NULLIF(q.rows_scanned, 0)
        ) * 100,
        4
    ) AS scan_efficiency_percent,

    q.cache_hit,
    q.execution_status,
    q.executed_at

FROM query_executions q
JOIN semantic_models sm
    ON sm.model_id = q.model_id;


-- ============================================================
-- 13. MODEL INVENTORY VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_model_inventory AS
SELECT
    sm.model_id,
    sm.model_name,
    mt.table_id,
    mt.table_name,
    mt.role,
    mt.row_count,
    mt.storage_mode,
    mt.query_folding,
    COUNT(mc.column_id) AS column_count,

    COUNT(mc.column_id)
        FILTER (
            WHERE mc.is_used = FALSE
              AND mc.is_key = FALSE
        ) AS unused_column_count,

    COALESCE(
        SUM(mc.cardinality),
        0
    ) AS combined_column_cardinality,

    mt.estimated_memory_mb,
    mt.refresh_duration_ms

FROM semantic_models sm

LEFT JOIN model_tables mt
    ON mt.model_id = sm.model_id

LEFT JOIN model_columns mc
    ON mc.table_id = mt.table_id

GROUP BY
    sm.model_id,
    sm.model_name,
    mt.table_id,
    mt.table_name,
    mt.role,
    mt.row_count,
    mt.storage_mode,
    mt.query_folding,
    mt.estimated_memory_mb,
    mt.refresh_duration_ms;


-- ============================================================
-- 14. QUERY POLICY EVALUATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_query(
    p_query_id BIGINT
)
RETURNS TABLE (
    query_name TEXT,
    total_ms NUMERIC,
    formula_share NUMERIC,
    passed BOOLEAN,
    violations TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_query RECORD;
    v_policy RECORD;
    v_total NUMERIC;
    v_formula_share NUMERIC;
    v_violations TEXT[] := ARRAY[]::TEXT[];
BEGIN

    SELECT
        q.*,
        (
            q.storage_engine_ms
            + q.formula_engine_ms
            + q.source_execution_ms
            + q.visual_render_ms
        ) AS total_time

    INTO v_query

    FROM query_executions q

    WHERE q.query_id = p_query_id
      AND q.execution_status = 'COMPLETED';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Completed query % does not exist',
            p_query_id;
    END IF;

    SELECT *
    INTO v_policy
    FROM performance_policies
    WHERE model_id = v_query.model_id
      AND is_active = TRUE
    ORDER BY policy_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No active performance policy for model %',
            v_query.model_id;
    END IF;

    v_total := v_query.total_time;

    v_formula_share :=
        CASE
            WHEN v_total = 0 THEN 0
            ELSE v_query.formula_engine_ms / v_total
        END;

    IF v_total > v_policy.max_total_query_ms THEN
        v_violations := array_append(
            v_violations,
            'Total query duration exceeds policy'
        );
    END IF;

    IF v_formula_share > v_policy.max_formula_share THEN
        v_violations := array_append(
            v_violations,
            'Formula Engine share exceeds policy'
        );
    END IF;

    IF v_query.source_execution_ms >
       v_policy.max_source_ms THEN

        v_violations := array_append(
            v_violations,
            'Source execution exceeds policy'
        );
    END IF;

    IF v_query.visual_render_ms >
       v_policy.max_visual_ms THEN

        v_violations := array_append(
            v_violations,
            'Visual rendering exceeds policy'
        );
    END IF;

    RETURN QUERY
    SELECT
        v_query.query_name::TEXT,
        v_total,
        v_formula_share,
        cardinality(v_violations) = 0,
        v_violations;
END;
$$;


-- ============================================================
-- 15. MODEL OPTIMIZATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE scan_model(
    p_model_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_table RECORD;
    v_column RECORD;
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM semantic_models
        WHERE model_id = p_model_id
    ) THEN
        RAISE EXCEPTION
            'Unknown semantic model %',
            p_model_id;
    END IF;

    -- Prevent duplicate unresolved findings during rescans.
    DELETE FROM optimization_findings
    WHERE model_id = p_model_id
      AND is_resolved = FALSE;

    FOR v_table IN
        SELECT *
        FROM model_tables
        WHERE model_id = p_model_id
    LOOP

        IF v_table.row_count > 1000000
           AND v_table.role = 'FACT'
           AND NOT v_table.query_folding THEN

            INSERT INTO optimization_findings (
                model_id,
                table_id,
                category,
                severity,
                description,
                recommendation
            )
            VALUES (
                p_model_id,
                v_table.table_id,
                'QUERY_FOLDING',
                'HIGH',
                'Large fact table does not fold its source query',
                'Push supported filtering and transformations to the source'
            );
        END IF;

        IF v_table.storage_mode = 'DIRECTQUERY'
           AND v_table.refresh_duration_ms IS NOT NULL THEN

            INSERT INTO optimization_findings (
                model_id,
                table_id,
                category,
                severity,
                description,
                recommendation
            )
            VALUES (
                p_model_id,
                v_table.table_id,
                'STORAGE_MODE_METADATA',
                'LOW',
                'Refresh duration recorded for a DirectQuery table',
                'Verify whether the recorded metric represents source refresh or another operation'
            );
        END IF;

        FOR v_column IN
            SELECT *
            FROM model_columns
            WHERE table_id = v_table.table_id
        LOOP

            IF NOT v_column.is_used
               AND NOT v_column.is_key THEN

                INSERT INTO optimization_findings (
                    model_id,
                    table_id,
                    column_id,
                    category,
                    severity,
                    description,
                    recommendation
                )
                VALUES (
                    p_model_id,
                    v_table.table_id,
                    v_column.column_id,
                    'UNUSED_COLUMN',
                    'HIGH',
                    'Unused column: ' || v_column.column_name,
                    'Remove the column from the semantic model when business requirements permit'
                );
            END IF;

            IF v_column.data_type = 'STRING'
               AND v_column.cardinality > 50000 THEN

                INSERT INTO optimization_findings (
                    model_id,
                    table_id,
                    column_id,
                    category,
                    severity,
                    description,
                    recommendation
                )
                VALUES (
                    p_model_id,
                    v_table.table_id,
                    v_column.column_id,
                    'HIGH_CARDINALITY',
                    'MEDIUM',
                    'High-cardinality text column: ' ||
                    v_column.column_name,
                    'Review necessity, data type, and source representation'
                );
            END IF;

        END LOOP;

    END LOOP;

    INSERT INTO optimization_findings (
        model_id,
        category,
        severity,
        description,
        recommendation
    )
    SELECT
        p_model_id,
        'BIDIRECTIONAL_RELATIONSHIP',
        'MEDIUM',
        'Bidirectional relationship detected',
        'Review whether single-direction filtering is sufficient'
    WHERE EXISTS (
        SELECT 1
        FROM model_relationships
        WHERE model_id = p_model_id
          AND bidirectional = TRUE
    );

    INSERT INTO optimization_findings (
        model_id,
        category,
        severity,
        description,
        recommendation
    )
    SELECT
        p_model_id,
        'MANY_TO_MANY_RELATIONSHIP',
        'HIGH',
        'Many-to-many relationship detected',
        'Evaluate bridge-table modeling and filter propagation'
    WHERE EXISTS (
        SELECT 1
        FROM model_relationships
        WHERE model_id = p_model_id
          AND cardinality = 'MANY_TO_MANY'
    );

END;
$$;


-- ============================================================
-- 16. QUERY AGGREGATION REPORT
-- ============================================================

CREATE OR REPLACE VIEW v_query_aggregation AS
SELECT
    model_id,
    query_type,
    COUNT(*) AS execution_count,

    ROUND(
        AVG(
            storage_engine_ms
            + formula_engine_ms
            + source_execution_ms
            + visual_render_ms
        ),
        2
    ) AS average_duration_ms,

    ROUND(
        MAX(
            storage_engine_ms
            + formula_engine_ms
            + source_execution_ms
            + visual_render_ms
        ),
        2
    ) AS maximum_duration_ms,

    ROUND(
        AVG(formula_engine_ms),
        2
    ) AS average_formula_engine_ms,

    ROUND(
        AVG(source_execution_ms),
        2
    ) AS average_source_ms,

    COUNT(*) FILTER (
        WHERE cache_hit = TRUE
    ) AS cache_hits,

    COUNT(*) FILTER (
        WHERE execution_status = 'FAILED'
    ) AS failed_queries

FROM query_executions

GROUP BY model_id, query_type;


-- ============================================================
-- 17. STORAGE MODE REPORT
-- ============================================================

CREATE OR REPLACE VIEW v_storage_mode_report AS
SELECT
    model_id,
    storage_mode,
    COUNT(*) AS table_count,
    SUM(row_count) AS total_rows,
    SUM(
        COALESCE(estimated_memory_mb, 0)
    ) AS estimated_memory_mb,

    AVG(refresh_duration_ms)
        AS average_refresh_duration_ms

FROM model_tables

GROUP BY model_id, storage_mode;


-- ============================================================
-- 18. SAMPLE ENTERPRISE DATA
-- ============================================================

INSERT INTO semantic_models (
    model_name,
    workspace_name,
    business_domain,
    description,
    owner_name,
    capacity_name
)
VALUES (
    'Enterprise Sales Analytics',
    'Corporate Analytics',
    'Sales and Revenue',
    'Sales performance and customer analytics semantic model',
    'BI Engineering',
    'Premium Analytics'
);


INSERT INTO model_tables (
    model_id,
    table_name,
    role,
    row_count,
    storage_mode,
    source_name,
    query_folding,
    refresh_duration_ms,
    estimated_memory_mb
)
SELECT
    model_id,
    'Sales',
    'FACT',
    2000000,
    'IMPORT',
    'warehouse.fact_sales',
    TRUE,
    42000,
    180.50
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


INSERT INTO model_tables (
    model_id,
    table_name,
    role,
    row_count,
    storage_mode,
    source_name,
    query_folding,
    estimated_memory_mb
)
SELECT
    model_id,
    'Product',
    'DIMENSION',
    5000,
    'IMPORT',
    'warehouse.dim_product',
    TRUE,
    3.20
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


INSERT INTO model_tables (
    model_id,
    table_name,
    role,
    row_count,
    storage_mode,
    source_name,
    query_folding,
    estimated_memory_mb
)
SELECT
    model_id,
    'Customer',
    'DIMENSION',
    180000,
    'DUAL',
    'warehouse.dim_customer',
    TRUE,
    12.50
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


INSERT INTO model_tables (
    model_id,
    table_name,
    role,
    row_count,
    storage_mode,
    source_name,
    query_folding,
    estimated_memory_mb
)
SELECT
    model_id,
    'Date',
    'DIMENSION',
    1825,
    'IMPORT',
    'warehouse.dim_date',
    TRUE,
    1.20
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


-- ============================================================
-- 19. SAMPLE COLUMN METADATA
-- ============================================================

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used,
    estimated_memory_mb
)
SELECT
    table_id,
    'SalesID',
    'INTEGER',
    2000000,
    TRUE,
    TRUE,
    8.00
FROM model_tables
WHERE table_name = 'Sales';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used,
    estimated_memory_mb
)
SELECT
    table_id,
    'ProductKey',
    'INTEGER',
    5000,
    FALSE,
    TRUE,
    1.50
FROM model_tables
WHERE table_name = 'Sales';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used,
    estimated_memory_mb
)
SELECT
    table_id,
    'DateKey',
    'INTEGER',
    1825,
    FALSE,
    TRUE,
    1.20
FROM model_tables
WHERE table_name = 'Sales';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used,
    estimated_memory_mb
)
SELECT
    table_id,
    'SalesAmount',
    'DECIMAL',
    250000,
    FALSE,
    TRUE,
    12.00
FROM model_tables
WHERE table_name = 'Sales';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used,
    estimated_memory_mb
)
SELECT
    table_id,
    'TransactionReference',
    'STRING',
    1900000,
    FALSE,
    TRUE,
    65.00
FROM model_tables
WHERE table_name = 'Sales';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used,
    estimated_memory_mb
)
SELECT
    table_id,
    'UnusedDescription',
    'STRING',
    2000,
    FALSE,
    FALSE,
    0.20
FROM model_tables
WHERE table_name = 'Sales';


INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used
)
SELECT
    table_id,
    'ProductKey',
    'INTEGER',
    5000,
    TRUE,
    TRUE
FROM model_tables
WHERE table_name = 'Product';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used
)
SELECT
    table_id,
    'Category',
    'STRING',
    12,
    FALSE,
    TRUE
FROM model_tables
WHERE table_name = 'Product';


INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used
)
SELECT
    table_id,
    'CustomerKey',
    'INTEGER',
    180000,
    TRUE,
    TRUE
FROM model_tables
WHERE table_name = 'Customer';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used
)
SELECT
    table_id,
    'Region',
    'STRING',
    25,
    FALSE,
    TRUE
FROM model_tables
WHERE table_name = 'Customer';


INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used
)
SELECT
    table_id,
    'DateKey',
    'INTEGER',
    1825,
    TRUE,
    TRUE
FROM model_tables
WHERE table_name = 'Date';

INSERT INTO model_columns (
    table_id,
    column_name,
    data_type,
    cardinality,
    is_key,
    is_used
)
SELECT
    table_id,
    'Year',
    'INTEGER',
    5,
    FALSE,
    TRUE
FROM model_tables
WHERE table_name = 'Date';


-- ============================================================
-- 20. RELATIONSHIP DATA
-- ============================================================

INSERT INTO model_relationships (
    model_id,
    from_column_id,
    to_column_id,
    cardinality,
    bidirectional
)
SELECT
    sm.model_id,
    sales_product.column_id,
    product_key.column_id,
    'MANY_TO_ONE',
    FALSE
FROM semantic_models sm

JOIN model_tables sales
    ON sales.model_id = sm.model_id
   AND sales.table_name = 'Sales'

JOIN model_columns sales_product
    ON sales_product.table_id = sales.table_id
   AND sales_product.column_name = 'ProductKey'

JOIN model_tables product
    ON product.model_id = sm.model_id
   AND product.table_name = 'Product'

JOIN model_columns product_key
    ON product_key.table_id = product.table_id
   AND product_key.column_name = 'ProductKey'

WHERE sm.model_name = 'Enterprise Sales Analytics';


INSERT INTO model_relationships (
    model_id,
    from_column_id,
    to_column_id,
    cardinality,
    bidirectional
)
SELECT
    sm.model_id,
    sales_date.column_id,
    date_key.column_id,
    'MANY_TO_ONE',
    FALSE
FROM semantic_models sm

JOIN model_tables sales
    ON sales.model_id = sm.model_id
   AND sales.table_name = 'Sales'

JOIN model_columns sales_date
    ON sales_date.table_id = sales.table_id
   AND sales_date.column_name = 'DateKey'

JOIN model_tables dates
    ON dates.model_id = sm.model_id
   AND dates.table_name = 'Date'

JOIN model_columns date_key
    ON date_key.table_id = dates.table_id
   AND date_key.column_name = 'DateKey'

WHERE sm.model_name = 'Enterprise Sales Analytics';


-- ============================================================
-- 21. DAX MEASURES
-- ============================================================

INSERT INTO dax_measures (
    model_id,
    measure_name,
    dax_expression,
    pattern,
    estimated_iterations,
    repeated_expressions,
    business_purpose
)
SELECT
    model_id,
    'Total Sales',
    'SUM(Sales[SalesAmount])',
    'SIMPLE_AGGREGATION',
    0,
    0,
    'Total recognized sales'
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


INSERT INTO dax_measures (
    model_id,
    measure_name,
    dax_expression,
    pattern,
    estimated_iterations,
    repeated_expressions,
    business_purpose
)
SELECT
    model_id,
    'Extended Revenue',
    'SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])',
    'ROW_ITERATION',
    2000000,
    0,
    'Revenue computed from quantity and unit price'
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


INSERT INTO dax_measures (
    model_id,
    measure_name,
    dax_expression,
    pattern,
    estimated_iterations,
    repeated_expressions,
    business_purpose
)
SELECT
    model_id,
    'Sales Growth',
    'VAR CurrentSales = [Total Sales] RETURN CurrentSales',
    'VARIABLE_REUSE',
    0,
    2,
    'Reusable sales calculations'
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


-- ============================================================
-- 22. PERFORMANCE POLICY DATA
-- ============================================================

INSERT INTO performance_policies (
    model_id,
    policy_name,
    max_total_query_ms,
    max_formula_share,
    max_source_ms,
    max_visual_ms,
    max_unused_columns
)
SELECT
    model_id,
    'Corporate Interactive Reporting',
    1500,
    0.40,
    500,
    300,
    0
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


-- ============================================================
-- 23. QUERY EXECUTION DATA
-- ============================================================

INSERT INTO query_executions (
    model_id,
    measure_id,
    query_name,
    query_type,
    storage_engine_ms,
    formula_engine_ms,
    source_execution_ms,
    visual_render_ms,
    rows_scanned,
    rows_returned,
    cache_hit,
    execution_status,
    user_name
)
SELECT
    sm.model_id,
    dm.measure_id,
    'Monthly Sales by Region',
    'AGGREGATION',
    120,
    80,
    0,
    100,
    2000000,
    24,
    FALSE,
    'COMPLETED',
    'analyst'
FROM semantic_models sm
JOIN dax_measures dm
    ON dm.model_id = sm.model_id
WHERE sm.model_name = 'Enterprise Sales Analytics'
  AND dm.measure_name = 'Total Sales';


INSERT INTO query_executions (
    model_id,
    query_name,
    query_type,
    storage_engine_ms,
    formula_engine_ms,
    source_execution_ms,
    visual_render_ms,
    rows_scanned,
    rows_returned,
    cache_hit,
    execution_status,
    user_name
)
SELECT
    model_id,
    'Customer Transaction Detail',
    'DETAIL',
    180,
    350,
    700,
    120,
    500000,
    250,
    FALSE,
    'COMPLETED',
    'analyst'
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


INSERT INTO query_executions (
    model_id,
    query_name,
    query_type,
    storage_engine_ms,
    formula_engine_ms,
    source_execution_ms,
    visual_render_ms,
    rows_scanned,
    rows_returned,
    cache_hit,
    execution_status
)
SELECT
    model_id,
    'Product Category Summary',
    'AGGREGATION',
    90,
    25,
    0,
    70,
    200000,
    20,
    TRUE,
    'COMPLETED'
FROM semantic_models
WHERE model_name = 'Enterprise Sales Analytics';


-- ============================================================
-- 24. AGGREGATION DEFINITION
-- ============================================================

INSERT INTO aggregation_definitions (
    model_id,
    aggregation_name,
    detail_table_id,
    aggregation_table_id,
    aggregation_grain,
    aggregation_expression
)
SELECT
    sm.model_id,
    'Monthly Product Sales',
    sales.table_id,
    product.table_id,
    'Month, ProductKey, Category',
    'SUM(SalesAmount) GROUP BY Month, ProductKey, Category'
FROM semantic_models sm
JOIN model_tables sales
    ON sales.model_id = sm.model_id
   AND sales.table_name = 'Sales'
JOIN model_tables product
    ON product.model_id = sm.model_id
   AND product.table_name = 'Product'
WHERE sm.model_name = 'Enterprise Sales Analytics';


-- ============================================================
-- 25. INITIAL OPTIMIZATION SCAN
-- ============================================================

CALL scan_model(
    (
        SELECT model_id
        FROM semantic_models
        WHERE model_name = 'Enterprise Sales Analytics'
    )
);


-- ============================================================
-- 26. RETRIEVAL QUERIES
-- ============================================================

-- Semantic model inventory.
SELECT *
FROM semantic_models
ORDER BY model_name;

-- Table and column statistics.
SELECT *
FROM v_model_inventory
ORDER BY model_name, table_name;

-- Relationship inspection.
SELECT
    r.relationship_id,
    r.cardinality,
    r.bidirectional,
    source_table.table_name AS source_table,
    source_column.column_name AS source_column,
    target_table.table_name AS target_table,
    target_column.column_name AS target_column

FROM model_relationships r

JOIN model_columns source_column
    ON source_column.column_id = r.from_column_id

JOIN model_tables source_table
    ON source_table.table_id = source_column.table_id

JOIN model_columns target_column
    ON target_column.column_id = r.to_column_id

JOIN model_tables target_table
    ON target_table.table_id = target_column.table_id;


-- ============================================================
-- 27. QUERY VALIDATION AND EVALUATION
-- ============================================================

SELECT *
FROM evaluate_query(
    (
        SELECT query_id
        FROM query_executions
        WHERE query_name = 'Monthly Sales by Region'
        ORDER BY query_id DESC
        LIMIT 1
    )
);

-- Inspect all query execution components.
SELECT *
FROM v_query_performance
ORDER BY total_execution_ms DESC;

-- Find slow completed queries.
SELECT
    query_name,
    total_execution_ms,
    formula_engine_share_percent,
    scan_efficiency_percent
FROM v_query_performance
WHERE execution_status = 'COMPLETED'
ORDER BY total_execution_ms DESC;


-- ============================================================
-- 28. AGGREGATION AND REPORTING
-- ============================================================

SELECT *
FROM v_query_aggregation
ORDER BY average_duration_ms DESC;

SELECT *
FROM v_storage_mode_report
ORDER BY model_id, storage_mode;

-- Performance policy violations.
SELECT
    q.query_name,
    q.total_execution_ms,
    p.policy_name,
    p.max_total_query_ms,
    q.formula_engine_share_percent,
    p.max_formula_share * 100 AS allowed_formula_share_percent

FROM v_query_performance q

JOIN performance_policies p
    ON p.model_id = q.model_id

WHERE p.is_active = TRUE
  AND q.execution_status = 'COMPLETED'
  AND (
      q.total_execution_ms > p.max_total_query_ms
      OR q.formula_engine_share_percent >
         p.max_formula_share * 100
  );


-- ============================================================
-- 29. ELIGIBILITY AND OPTIMIZATION REPORT
-- ============================================================

SELECT
    model_name,
    table_name,
    unused_column_count,
    row_count,
    storage_mode,
    query_folding,
    estimated_memory_mb

FROM v_model_inventory

WHERE unused_column_count > 0
   OR (
       role = 'FACT'
       AND row_count > 1000000
       AND query_folding = FALSE
   );


-- Unresolved optimization findings.
SELECT
    finding_id,
    category,
    severity,
    description,
    recommendation,
    detected_at

FROM optimization_findings

WHERE is_resolved = FALSE

ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        ELSE 4
    END,
    detected_at DESC;


-- DAX measures requiring inspection.
SELECT
    measure_name,
    pattern,
    estimated_iterations,
    repeated_expressions,
    dax_expression

FROM dax_measures

WHERE pattern IN (
    'ROW_ITERATION',
    'FILTER_ALL'
)
OR estimated_iterations > 1000000
OR repeated_expressions > 1

ORDER BY estimated_iterations DESC;


-- ============================================================
-- 30. TRANSACTIONAL POLICY CHANGE EXAMPLE
-- ============================================================

-- Example of a controlled performance policy update.
-- The change is committed only after validation.

SAVEPOINT before_policy_update;

UPDATE performance_policies
SET
    max_total_query_ms = 1800,
    max_formula_share = 0.35
WHERE policy_name = 'Corporate Interactive Reporting'
  AND is_active = TRUE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM performance_policies
        WHERE policy_name = 'Corporate Interactive Reporting'
          AND (
              max_total_query_ms <= 0
              OR max_formula_share < 0
              OR max_formula_share > 1
          )
    ) THEN
        RAISE EXCEPTION
            'Updated policy violates validation requirements';
    END IF;
END;
$$;

-- The savepoint allows local rollback if later operations fail.
RELEASE SAVEPOINT before_policy_update;

COMMIT;


-- ============================================================
-- 31. OPERATIONAL QUERIES
-- ============================================================

-- Re-run the model scan after metadata changes.
-- CALL scan_model(1);

-- Record a new completed query through INSERT INTO query_executions.

-- Re-evaluate query behavior with:
-- SELECT * FROM evaluate_query(1);

-- Inspect table-level memory metadata:
-- SELECT table_name, estimated_memory_mb
-- FROM model_tables
-- ORDER BY estimated_memory_mb DESC;

-- Inspect storage-mode distribution:
-- SELECT * FROM v_storage_mode_report;

-- Inspect policy findings:
-- SELECT * FROM optimization_findings
-- WHERE is_resolved = FALSE;
