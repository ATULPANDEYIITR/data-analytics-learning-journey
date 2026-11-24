-- ============================================================
-- POWER BI VISUALIZATION DATABASE
-- ============================================================
-- PostgreSQL 15+
--
-- Domain:
-- Retail analytical dashboard.
--
-- Implemented analytical concepts:
-- 1. KPI cards
-- 2. Tables
-- 3. Matrices
-- 4. Bar charts
-- 5. Line charts
-- 6. Pie charts
-- 7. Geographic maps
-- 8. Slicers
-- 9. Drill-through
-- 10. Dashboard bookmarks
-- 11. Refresh and aggregation
-- 12. User-specific dashboard state
--
-- The database stores analytical data and visualization
-- configurations. Actual chart rendering is performed by
-- the reporting client.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS powerbi;

SET search_path TO powerbi, public;

-- ============================================================
-- 1. REFERENCE DATA
-- ============================================================

CREATE TABLE IF NOT EXISTS regions (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cities (
    city_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    city_name VARCHAR(100) NOT NULL,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),

    CONSTRAINT uq_city_region UNIQUE (region_id, city_name),

    CONSTRAINT ck_latitude CHECK (
        latitude IS NULL OR latitude BETWEEN -90 AND 90
    ),

    CONSTRAINT ck_longitude CHECK (
        longitude IS NULL OR longitude BETWEEN -180 AND 180
    )
);

CREATE TABLE IF NOT EXISTS product_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id BIGINT NOT NULL
        REFERENCES product_categories(category_id),
    product_name VARCHAR(150) NOT NULL UNIQUE,
    standard_price NUMERIC(14,2) NOT NULL,

    CONSTRAINT ck_product_price CHECK (standard_price >= 0)
);

CREATE TABLE IF NOT EXISTS salespersons (
    salesperson_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salesperson_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- 2. TRANSACTION FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    transaction_date DATE NOT NULL,
    city_id BIGINT NOT NULL REFERENCES cities(city_id),
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    salesperson_id BIGINT NOT NULL
        REFERENCES salespersons(salesperson_id),

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14,2) NOT NULL,
    discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_transaction_quantity CHECK (quantity > 0),
    CONSTRAINT ck_transaction_price CHECK (unit_price >= 0),
    CONSTRAINT ck_transaction_discount CHECK (
        discount_percent BETWEEN 0 AND 100
    )
);

-- Net sales and profit are calculated consistently from source
-- transaction values instead of storing duplicate measures.

CREATE OR REPLACE VIEW sales_analytics AS
SELECT
    st.transaction_id,
    st.transaction_date,
    DATE_TRUNC('month', st.transaction_date)::DATE AS sales_month,
    r.region_name,
    c.city_name,
    pc.category_name,
    p.product_name,
    sp.salesperson_name,
    st.quantity,
    st.unit_price,
    st.discount_percent,

    st.quantity * st.unit_price AS gross_sales,

    ROUND(
        st.quantity * st.unit_price *
        (1 - st.discount_percent / 100),
        2
    ) AS net_sales,

    ROUND(
        st.quantity * st.unit_price *
        (1 - st.discount_percent / 100) * 0.25,
        2
    ) AS estimated_profit

FROM sales_transactions st

JOIN cities c
    ON c.city_id = st.city_id

JOIN regions r
    ON r.region_id = c.region_id

JOIN products p
    ON p.product_id = st.product_id

JOIN product_categories pc
    ON pc.category_id = p.category_id

JOIN salespersons sp
    ON sp.salesperson_id = st.salesperson_id;

-- ============================================================
-- 3. DASHBOARD AND VISUALIZATION CONFIGURATION
-- ============================================================

CREATE TABLE IF NOT EXISTS dashboards (
    dashboard_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_name VARCHAR(150) NOT NULL,
    description TEXT,
    owner_email VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_dashboard_owner_name
        UNIQUE (dashboard_name, owner_email)
);

CREATE TABLE IF NOT EXISTS visualizations (
    visualization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL
        REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,

    visual_name VARCHAR(120) NOT NULL,

    visual_type VARCHAR(30) NOT NULL,

    title VARCHAR(200) NOT NULL,

    dimension_fields TEXT[] NOT NULL DEFAULT '{}',
    measure_fields TEXT[] NOT NULL DEFAULT '{}',

    position_x INTEGER NOT NULL DEFAULT 0,
    position_y INTEGER NOT NULL DEFAULT 0,
    width INTEGER NOT NULL DEFAULT 4,
    height INTEGER NOT NULL DEFAULT 3,

    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT ck_visual_type CHECK (
        visual_type IN (
            'card',
            'table',
            'matrix',
            'bar',
            'line',
            'pie',
            'map'
        )
    ),

    CONSTRAINT ck_visual_dimensions CHECK (
        position_x >= 0 AND position_y >= 0
        AND width > 0 AND height > 0
    ),

    CONSTRAINT uq_dashboard_visual
        UNIQUE (dashboard_id, visual_name)
);

-- ============================================================
-- 4. SLICERS AND FILTER STATE
-- ============================================================

CREATE TABLE IF NOT EXISTS slicers (
    slicer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dashboard_id BIGINT NOT NULL
        REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,

    slicer_name VARCHAR(120) NOT NULL,

    field_name VARCHAR(100) NOT NULL,

    selection_type VARCHAR(30) NOT NULL,

    default_selection JSONB NOT NULL DEFAULT '[]'::JSONB,

    is_visible BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_slicer_type CHECK (
        selection_type IN (
            'single',
            'multi',
            'range',
            'date_range'
        )
    ),

    CONSTRAINT uq_dashboard_slicer
        UNIQUE (dashboard_id, slicer_name)
);

CREATE TABLE IF NOT EXISTS dashboard_filter_states (
    filter_state_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dashboard_id BIGINT NOT NULL
        REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,

    user_email VARCHAR(255) NOT NULL,

    field_name VARCHAR(100) NOT NULL,

    selected_values JSONB NOT NULL,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_dashboard_filter
        UNIQUE (dashboard_id, user_email, field_name),

    CONSTRAINT ck_filter_json
        CHECK (jsonb_typeof(selected_values) IN ('array', 'object', 'string', 'number'))
);

CREATE INDEX IF NOT EXISTS idx_dashboard_filters_user
    ON dashboard_filter_states(user_email, dashboard_id);

-- ============================================================
-- 5. BOOKMARKS
-- ============================================================

CREATE TABLE IF NOT EXISTS dashboard_bookmarks (
    bookmark_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dashboard_id BIGINT NOT NULL
        REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,

    user_email VARCHAR(255) NOT NULL,

    bookmark_name VARCHAR(120) NOT NULL,

    description TEXT,

    filter_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB,

    selected_visual VARCHAR(120),

    visual_visibility JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_bookmark
        UNIQUE (dashboard_id, user_email, bookmark_name)
);

CREATE INDEX IF NOT EXISTS idx_bookmarks_dashboard_user
    ON dashboard_bookmarks(dashboard_id, user_email);

-- ============================================================
-- 6. DRILL-THROUGH CONFIGURATION
-- ============================================================

CREATE TABLE IF NOT EXISTS drillthrough_pages (
    drillthrough_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dashboard_id BIGINT NOT NULL
        REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,

    source_visual_id BIGINT
        REFERENCES visualizations(visualization_id)
        ON DELETE SET NULL,

    target_page VARCHAR(120) NOT NULL,

    dimension_field VARCHAR(100) NOT NULL,

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_drillthrough_route
        UNIQUE (dashboard_id, target_page, dimension_field)
);

-- ============================================================
-- 7. REFRESH TRACKING
-- ============================================================

CREATE TABLE IF NOT EXISTS dataset_refreshes (
    refresh_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dashboard_id BIGINT NOT NULL
        REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,

    refresh_started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    refresh_completed_at TIMESTAMPTZ,

    refresh_status VARCHAR(20) NOT NULL DEFAULT 'running',

    rows_processed BIGINT NOT NULL DEFAULT 0,

    error_message TEXT,

    CONSTRAINT ck_refresh_status CHECK (
        refresh_status IN ('running', 'completed', 'failed')
    ),

    CONSTRAINT ck_refresh_rows CHECK (rows_processed >= 0)
);

CREATE INDEX IF NOT EXISTS idx_refresh_dashboard_time
    ON dataset_refreshes(dashboard_id, refresh_started_at DESC);

-- ============================================================
-- 8. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_transaction_date
    ON sales_transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_sales_city_date
    ON sales_transactions(city_id, transaction_date);

CREATE INDEX IF NOT EXISTS idx_sales_product_date
    ON sales_transactions(product_id, transaction_date);

CREATE INDEX IF NOT EXISTS idx_sales_salesperson_date
    ON sales_transactions(salesperson_id, transaction_date);

CREATE INDEX IF NOT EXISTS idx_product_category
    ON products(category_id);

-- ============================================================
-- 9. KPI CARD AGGREGATION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_kpi(
    p_dashboard_id BIGINT,
    p_measure VARCHAR DEFAULT 'net_sales',
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_result NUMERIC;
BEGIN
    IF p_measure NOT IN (
        'net_sales',
        'gross_sales',
        'estimated_profit',
        'quantity'
    ) THEN
        RAISE EXCEPTION 'Unsupported KPI measure: %', p_measure;
    END IF;

    IF p_start_date IS NOT NULL
       AND p_end_date IS NOT NULL
       AND p_start_date > p_end_date THEN
        RAISE EXCEPTION 'Invalid date range';
    END IF;

    SELECT
        COALESCE(
            CASE p_measure
                WHEN 'net_sales'
                    THEN SUM(net_sales)
                WHEN 'gross_sales'
                    THEN SUM(gross_sales)
                WHEN 'estimated_profit'
                    THEN SUM(estimated_profit)
                WHEN 'quantity'
                    THEN SUM(quantity)
            END,
            0
        )
    INTO v_result
    FROM sales_analytics
    WHERE (p_start_date IS NULL
           OR transaction_date >= p_start_date)
      AND (p_end_date IS NULL
           OR transaction_date <= p_end_date);

    RETURN ROUND(v_result, 2);
END;
$$;

-- ============================================================
-- 10. MATRIX AGGREGATION
-- ============================================================

CREATE OR REPLACE FUNCTION regional_category_matrix(
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    region VARCHAR,
    category VARCHAR,
    total_sales NUMERIC,
    total_profit NUMERIC,
    transaction_count BIGINT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        sa.region_name::VARCHAR,
        sa.category_name::VARCHAR,
        ROUND(SUM(sa.net_sales), 2),
        ROUND(SUM(sa.estimated_profit), 2),
        COUNT(*)
    FROM sales_analytics sa
    WHERE (p_start_date IS NULL
           OR sa.transaction_date >= p_start_date)
      AND (p_end_date IS NULL
           OR sa.transaction_date <= p_end_date)
    GROUP BY sa.region_name, sa.category_name
    ORDER BY sa.region_name, sa.category_name;
$$;

-- ============================================================
-- 11. CHART DATA FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION monthly_sales_chart(
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    sales_month DATE,
    total_sales NUMERIC,
    total_profit NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        sa.sales_month,
        ROUND(SUM(sa.net_sales), 2),
        ROUND(SUM(sa.estimated_profit), 2)
    FROM sales_analytics sa
    WHERE (p_start_date IS NULL
           OR sa.transaction_date >= p_start_date)
      AND (p_end_date IS NULL
           OR sa.transaction_date <= p_end_date)
    GROUP BY sa.sales_month
    ORDER BY sa.sales_month;
$$;

CREATE OR REPLACE FUNCTION category_contribution()
RETURNS TABLE (
    category VARCHAR,
    total_sales NUMERIC,
    contribution_percent NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    WITH category_totals AS (
        SELECT
            category_name,
            SUM(net_sales) AS sales
        FROM sales_analytics
        GROUP BY category_name
    ),
    grand_total AS (
        SELECT SUM(sales) AS total
        FROM category_totals
    )
    SELECT
        ct.category_name::VARCHAR,
        ROUND(ct.sales, 2),
        CASE
            WHEN gt.total = 0 THEN 0
            ELSE ROUND(ct.sales * 100 / gt.total, 2)
        END
    FROM category_totals ct
    CROSS JOIN grand_total gt
    ORDER BY ct.sales DESC;
$$;

-- ============================================================
-- 12. MAP DATA
-- ============================================================

CREATE OR REPLACE VIEW geographic_sales AS
SELECT
    r.region_name,
    c.city_name,
    c.latitude,
    c.longitude,
    ROUND(SUM(sa.net_sales), 2) AS total_sales,
    COUNT(*) AS transaction_count
FROM sales_analytics sa
JOIN cities c
    ON c.city_name = sa.city_name
JOIN regions r
    ON r.region_name = sa.region_name
GROUP BY
    r.region_name,
    c.city_name,
    c.latitude,
    c.longitude;

-- ============================================================
-- 13. DRILL-THROUGH FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION get_drillthrough_details(
    p_dashboard_id BIGINT,
    p_target_page VARCHAR,
    p_dimension_field VARCHAR,
    p_dimension_value VARCHAR
)
RETURNS TABLE (
    transaction_id BIGINT,
    transaction_date DATE,
    region VARCHAR,
    city VARCHAR,
    category VARCHAR,
    product VARCHAR,
    quantity INTEGER,
    net_sales NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_enabled BOOLEAN;
BEGIN
    SELECT is_enabled
    INTO v_enabled
    FROM drillthrough_pages
    WHERE dashboard_id = p_dashboard_id
      AND target_page = p_target_page
      AND dimension_field = p_dimension_field;

    IF NOT FOUND OR NOT v_enabled THEN
        RAISE EXCEPTION 'Drill-through route is not enabled';
    END IF;

    IF p_dimension_field NOT IN (
        'region_name',
        'city_name',
        'category_name',
        'product_name',
        'salesperson_name'
    ) THEN
        RAISE EXCEPTION 'Unsupported drill-through dimension';
    END IF;

    RETURN QUERY
    SELECT
        sa.transaction_id,
        sa.transaction_date,
        sa.region_name::VARCHAR,
        sa.city_name::VARCHAR,
        sa.category_name::VARCHAR,
        sa.product_name::VARCHAR,
        sa.quantity,
        sa.net_sales
    FROM sales_analytics sa
    WHERE CASE p_dimension_field
        WHEN 'region_name' THEN sa.region_name = p_dimension_value
        WHEN 'city_name' THEN sa.city_name = p_dimension_value
        WHEN 'category_name' THEN sa.category_name = p_dimension_value
        WHEN 'product_name' THEN sa.product_name = p_dimension_value
        WHEN 'salesperson_name' THEN sa.salesperson_name = p_dimension_value
        ELSE FALSE
    END;
END;
$$;

-- ============================================================
-- 14. BOOKMARK RESTORATION
-- ============================================================

CREATE OR REPLACE FUNCTION restore_bookmark(
    p_dashboard_id BIGINT,
    p_user_email VARCHAR,
    p_bookmark_name VARCHAR
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_state JSONB;
BEGIN
    SELECT jsonb_build_object(
        'filters', filter_snapshot,
        'selected_visual', selected_visual,
        'visibility', visual_visibility
    )
    INTO v_state
    FROM dashboard_bookmarks
    WHERE dashboard_id = p_dashboard_id
      AND user_email = p_user_email
      AND bookmark_name = p_bookmark_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Bookmark not found: %', p_bookmark_name;
    END IF;

    RETURN v_state;
END;
$$;

-- ============================================================
-- 15. FILTER STATE UPSERT
-- ============================================================

CREATE OR REPLACE PROCEDURE save_filter_state(
    p_dashboard_id BIGINT,
    p_user_email VARCHAR,
    p_field_name VARCHAR,
    p_selected_values JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_dashboard_id IS NULL
       OR p_user_email IS NULL
       OR p_field_name IS NULL THEN
        RAISE EXCEPTION 'Filter identity fields are required';
    END IF;

    IF p_selected_values IS NULL THEN
        RAISE EXCEPTION 'Filter selection cannot be NULL';
    END IF;

    INSERT INTO dashboard_filter_states (
        dashboard_id,
        user_email,
        field_name,
        selected_values,
        updated_at
    )
    VALUES (
        p_dashboard_id,
        p_user_email,
        p_field_name,
        p_selected_values,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (
        dashboard_id,
        user_email,
        field_name
    )
    DO UPDATE SET
        selected_values = EXCLUDED.selected_values,
        updated_at = CURRENT_TIMESTAMP;
END;
$$;

-- ============================================================
-- 16. BOOKMARK DATA VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_bookmark_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF jsonb_typeof(NEW.filter_snapshot) <> 'object' THEN
        RAISE EXCEPTION 'Bookmark filter snapshot must be an object';
    END IF;

    IF jsonb_typeof(NEW.visual_visibility) <> 'object' THEN
        RAISE EXCEPTION 'Visual visibility must be an object';
    END IF;

    IF NEW.bookmark_name IS NULL
       OR LENGTH(TRIM(NEW.bookmark_name)) = 0 THEN
        RAISE EXCEPTION 'Bookmark name cannot be empty';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_bookmark
ON dashboard_bookmarks;

CREATE TRIGGER trg_validate_bookmark
BEFORE INSERT OR UPDATE
ON dashboard_bookmarks
FOR EACH ROW
EXECUTE FUNCTION validate_bookmark_snapshot();

-- ============================================================
-- 17. SAMPLE REFERENCE DATA
-- ============================================================

INSERT INTO regions (region_name)
VALUES
    ('North'),
    ('South'),
    ('East'),
    ('West')
ON CONFLICT (region_name) DO NOTHING;

INSERT INTO cities (
    region_id,
    city_name,
    latitude,
    longitude
)
SELECT
    r.region_id,
    v.city_name,
    v.latitude,
    v.longitude
FROM (
    VALUES
        ('North', 'Delhi', 28.613900, 77.209000),
        ('North', 'Lucknow', 26.846700, 80.946200),
        ('South', 'Bengaluru', 12.971600, 77.594600),
        ('South', 'Chennai', 13.082700, 80.270700),
        ('East', 'Kolkata', 22.572600, 88.363900),
        ('West', 'Mumbai', 19.076000, 72.877700),
        ('West', 'Pune', 18.520400, 73.856700)
) AS v(region_name, city_name, latitude, longitude)
JOIN regions r
    ON r.region_name = v.region_name
ON CONFLICT (region_id, city_name) DO NOTHING;

INSERT INTO product_categories (category_name)
VALUES
    ('Electronics'),
    ('Furniture'),
    ('Clothing')
ON CONFLICT (category_name) DO NOTHING;

INSERT INTO products (
    category_id,
    product_name,
    standard_price
)
SELECT
    pc.category_id,
    v.product_name,
    v.standard_price
FROM (
    VALUES
        ('Electronics', 'Laptop', 65000.00),
        ('Electronics', 'Mobile', 30000.00),
        ('Furniture', 'Chair', 4500.00),
        ('Furniture', 'Table', 12000.00),
        ('Clothing', 'Jacket', 2500.00),
        ('Clothing', 'Shirt', 1200.00)
) AS v(category_name, product_name, standard_price)
JOIN product_categories pc
    ON pc.category_name = v.category_name
ON CONFLICT (product_name) DO NOTHING;

INSERT INTO salespersons (
    salesperson_name,
    email
)
VALUES
    ('Amit', 'amit@example.com'),
    ('Neha', 'neha@example.com'),
    ('Rahul', 'rahul@example.com'),
    ('Priya', 'priya@example.com')
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- 18. SAMPLE TRANSACTIONS
-- ============================================================

INSERT INTO sales_transactions (
    transaction_date,
    city_id,
    product_id,
    salesperson_id,
    quantity,
    unit_price,
    discount_percent
)
SELECT
    v.transaction_date,
    c.city_id,
    p.product_id,
    sp.salesperson_id,
    v.quantity,
    v.unit_price,
    v.discount_percent
FROM (
    VALUES
        ('2026-01-05'::DATE, 'Delhi', 'Laptop',
         'amit@example.com', 2, 65000.00, 5.00),

        ('2026-01-12'::DATE, 'Lucknow', 'Chair',
         'neha@example.com', 5, 4500.00, 10.00),

        ('2026-02-08'::DATE, 'Bengaluru', 'Mobile',
         'rahul@example.com', 4, 30000.00, 8.00),

        ('2026-02-15'::DATE, 'Mumbai', 'Jacket',
         'priya@example.com', 8, 2500.00, 5.00),

        ('2026-03-03'::DATE, 'Kolkata', 'Table',
         'amit@example.com', 3, 12000.00, 12.00),

        ('2026-03-18'::DATE, 'Delhi', 'Shirt',
         'neha@example.com', 10, 1200.00, 2.00),

        ('2026-04-10'::DATE, 'Chennai', 'Laptop',
         'rahul@example.com', 1, 70000.00, 4.00),

        ('2026-04-20'::DATE, 'Pune', 'Chair',
         'priya@example.com', 6, 5000.00, 7.00),

        ('2026-05-05'::DATE, 'Kolkata', 'Mobile',
         'amit@example.com', 3, 28000.00, 6.00),

        ('2026-05-17'::DATE, 'Lucknow', 'Jacket',
         'neha@example.com', 4, 3000.00, 3.00)
) AS v(
    transaction_date,
    city_name,
    product_name,
    salesperson_email,
    quantity,
    unit_price,
    discount_percent
)
JOIN cities c
    ON c.city_name = v.city_name
JOIN products p
    ON p.product_name = v.product_name
JOIN salespersons sp
    ON sp.email = v.salesperson_email;

-- ============================================================
-- 19. DASHBOARD CONFIGURATION
-- ============================================================

INSERT INTO dashboards (
    dashboard_name,
    description,
    owner_email
)
VALUES (
    'Retail Sales Performance',
    'Regional sales, product performance and profitability dashboard',
    'admin@example.com'
)
ON CONFLICT (dashboard_name, owner_email) DO NOTHING;

INSERT INTO visualizations (
    dashboard_id,
    visual_name,
    visual_type,
    title,
    dimension_fields,
    measure_fields,
    position_x,
    position_y,
    width,
    height,
    configuration
)
SELECT
    d.dashboard_id,
    v.visual_name,
    v.visual_type,
    v.title,
    v.dimensions,
    v.measures,
    v.position_x,
    v.position_y,
    v.width,
    v.height,
    v.configuration
FROM dashboards d
CROSS JOIN (
    VALUES
        (
            'total_sales',
            'card',
            'Total Net Sales',
            ARRAY[]::TEXT[],
            ARRAY['net_sales']::TEXT[],
            0, 0, 3, 2,
            '{"aggregation":"SUM","format":"currency"}'::JSONB
        ),
        (
            'profit_card',
            'card',
            'Estimated Profit',
            ARRAY[]::TEXT[],
            ARRAY['estimated_profit']::TEXT[],
            3, 0, 3, 2,
            '{"aggregation":"SUM","format":"currency"}'::JSONB
        ),
        (
            'regional_table',
            'table',
            'Regional Sales Details',
            ARRAY['region_name','city_name']::TEXT[],
            ARRAY['net_sales','estimated_profit']::TEXT[],
            0, 2, 6, 4,
            '{"totals":true,"sorting":"net_sales_desc"}'::JSONB
        ),
        (
            'category_matrix',
            'matrix',
            'Region and Category Matrix',
            ARRAY['region_name','category_name']::TEXT[],
            ARRAY['net_sales']::TEXT[],
            6, 2, 6, 4,
            '{"row_subtotals":true,"grand_total":true}'::JSONB
        ),
        (
            'category_bar',
            'bar',
            'Sales by Category',
            ARRAY['category_name']::TEXT[],
            ARRAY['net_sales']::TEXT[],
            0, 6, 6, 4,
            '{"orientation":"vertical","legend":false}'::JSONB
        ),
        (
            'monthly_line',
            'line',
            'Monthly Sales Trend',
            ARRAY['sales_month']::TEXT[],
            ARRAY['net_sales']::TEXT[],
            6, 6, 6, 4,
            '{"x_axis":"date","time_granularity":"month"}'::JSONB
        ),
        (
            'category_pie',
            'pie',
            'Category Contribution',
            ARRAY['category_name']::TEXT[],
            ARRAY['net_sales']::TEXT[],
            0, 10, 6, 4,
            '{"percentage_labels":true}'::JSONB
        ),
        (
            'regional_map',
            'map',
            'Geographic Sales Distribution',
            ARRAY['latitude','longitude','city_name']::TEXT[],
            ARRAY['net_sales']::TEXT[],
            6, 10, 6, 4,
            '{"location":"city","size":"net_sales"}'::JSONB
        )
) AS v(
    visual_name,
    visual_type,
    title,
    dimensions,
    measures,
    position_x,
    position_y,
    width,
    height,
    configuration
)
WHERE d.dashboard_name = 'Retail Sales Performance'
  AND d.owner_email = 'admin@example.com'
ON CONFLICT (dashboard_id, visual_name) DO NOTHING;

-- ============================================================
-- 20. SLICER CONFIGURATION
-- ============================================================

INSERT INTO slicers (
    dashboard_id,
    slicer_name,
    field_name,
    selection_type,
    default_selection
)
SELECT
    d.dashboard_id,
    v.slicer_name,
    v.field_name,
    v.selection_type,
    v.default_selection
FROM dashboards d
CROSS JOIN (
    VALUES
        (
            'Region Selector',
            'region_name',
            'multi',
            '[]'::JSONB
        ),
        (
            'Category Selector',
            'category_name',
            'multi',
            '[]'::JSONB
        ),
        (
            'Transaction Date Range',
            'transaction_date',
            'date_range',
            '{}'::JSONB
        ),
        (
            'Sales Amount',
            'net_sales',
            'range',
            '{}'::JSONB
        )
) AS v(
    slicer_name,
    field_name,
    selection_type,
    default_selection
)
WHERE d.dashboard_name = 'Retail Sales Performance'
  AND d.owner_email = 'admin@example.com'
ON CONFLICT (dashboard_id, slicer_name) DO NOTHING;

-- ============================================================
-- 21. DRILL-THROUGH ROUTES
-- ============================================================

INSERT INTO drillthrough_pages (
    dashboard_id,
    target_page,
    dimension_field,
    is_enabled
)
SELECT
    dashboard_id,
    v.target_page,
    v.dimension_field,
    TRUE
FROM dashboards d
CROSS JOIN (
    VALUES
        ('Regional Details', 'region_name'),
        ('City Details', 'city_name'),
        ('Category Details', 'category_name'),
        ('Product Details', 'product_name')
) AS v(target_page, dimension_field)
WHERE d.dashboard_name = 'Retail Sales Performance'
  AND d.owner_email = 'admin@example.com'
ON CONFLICT (
    dashboard_id,
    target_page,
    dimension_field
) DO NOTHING;

-- ============================================================
-- 22. SAVED BOOKMARK
-- ============================================================

INSERT INTO dashboard_bookmarks (
    dashboard_id,
    user_email,
    bookmark_name,
    description,
    filter_snapshot,
    selected_visual,
    visual_visibility
)
SELECT
    dashboard_id,
    'admin@example.com',
    'North Region Analysis',
    'Saved northern regional dashboard state',
    '{"region_name":["North"]}'::JSONB,
    'regional_table',
    '{"total_sales":true,"profit_card":true,"regional_map":true}'::JSONB
FROM dashboards
WHERE dashboard_name = 'Retail Sales Performance'
  AND owner_email = 'admin@example.com'
ON CONFLICT (
    dashboard_id,
    user_email,
    bookmark_name
) DO NOTHING;

-- ============================================================
-- 23. REPORTING AND RETRIEVAL QUERIES
-- ============================================================

-- A. KPI CARD

SELECT
    calculate_kpi(
        dashboard_id,
        'net_sales',
        DATE '2026-01-01',
        DATE '2026-12-31'
    ) AS total_net_sales
FROM dashboards
WHERE dashboard_name = 'Retail Sales Performance';

-- B. PROFIT CARD

SELECT
    calculate_kpi(
        dashboard_id,
        'estimated_profit',
        DATE '2026-01-01',
        DATE '2026-12-31'
    ) AS total_estimated_profit
FROM dashboards
WHERE dashboard_name = 'Retail Sales Performance';

-- C. TABLE: REGIONAL AND CATEGORY SALES

SELECT
    region_name,
    city_name,
    category_name,
    SUM(net_sales) AS total_sales,
    SUM(estimated_profit) AS total_profit,
    COUNT(*) AS transaction_count
FROM sales_analytics
GROUP BY region_name, city_name, category_name
ORDER BY total_sales DESC;

-- D. MATRIX

SELECT *
FROM regional_category_matrix(
    DATE '2026-01-01',
    DATE '2026-12-31'
);

-- E. BAR CHART DATA

SELECT
    category_name,
    ROUND(SUM(net_sales), 2) AS total_sales
FROM sales_analytics
GROUP BY category_name
ORDER BY total_sales DESC;

-- F. LINE CHART DATA

SELECT *
FROM monthly_sales_chart(
    DATE '2026-01-01',
    DATE '2026-12-31'
);

-- G. PIE CHART DATA

SELECT *
FROM category_contribution();

-- H. MAP DATA

SELECT *
FROM geographic_sales
ORDER BY total_sales DESC;

-- I. SLICER: MULTIPLE REGIONS AND CATEGORY

SELECT
    region_name,
    category_name,
    ROUND(SUM(net_sales), 2) AS total_sales
FROM sales_analytics
WHERE region_name = ANY(
    ARRAY['North', 'South']::VARCHAR[]
)
AND category_name = 'Electronics'
GROUP BY region_name, category_name;

-- J. DATE RANGE SLICER

SELECT *
FROM sales_analytics
WHERE transaction_date BETWEEN
    DATE '2026-01-01' AND DATE '2026-03-31';

-- K. DRILL-THROUGH

SELECT
    get_drillthrough_details(
        dashboard_id,
        'Regional Details',
        'region_name',
        'North'
    )
FROM dashboards
WHERE dashboard_name = 'Retail Sales Performance';

-- ============================================================
-- 24. VALIDATION AND DATA QUALITY QUERIES
-- ============================================================

-- Transactions with unexpectedly high discounts.

SELECT
    transaction_id,
    discount_percent
FROM sales_transactions
WHERE discount_percent > 50;

-- Transactions with missing geographic coordinates.

SELECT
    c.city_name,
    c.latitude,
    c.longitude
FROM cities c
WHERE c.latitude IS NULL
   OR c.longitude IS NULL;

-- Products without transactions.

SELECT
    p.product_name
FROM products p
LEFT JOIN sales_transactions st
    ON st.product_id = p.product_id
WHERE st.transaction_id IS NULL;

-- Sales aggregation consistency.

SELECT
    SUM(gross_sales) AS gross_sales,
    SUM(net_sales) AS net_sales,
    SUM(estimated_profit) AS estimated_profit
FROM sales_analytics;

-- ============================================================
-- 25. ELIGIBILITY AND REFRESH REPORTING
-- ============================================================

-- Visual configuration completeness.

SELECT
    v.visual_name,
    v.visual_type,
    CARDINALITY(v.dimension_fields) AS dimension_count,
    CARDINALITY(v.measure_fields) AS measure_count,
    CASE
        WHEN v.visual_type IN ('table', 'matrix', 'bar', 'line', 'pie')
             AND CARDINALITY(v.dimension_fields) = 0
            THEN 'INVALID: DIMENSION REQUIRED'
        WHEN CARDINALITY(v.measure_fields) = 0
            THEN 'INVALID: MEASURE REQUIRED'
        ELSE 'CONFIGURATION VALID'
    END AS validation_status
FROM visualizations v
JOIN dashboards d
    ON d.dashboard_id = v.dashboard_id
WHERE d.dashboard_name = 'Retail Sales Performance';

-- Refresh monitoring.

SELECT
    dashboard_id,
    refresh_status,
    COUNT(*) AS refresh_count,
    SUM(rows_processed) AS total_rows_processed
FROM dataset_refreshes
GROUP BY dashboard_id, refresh_status
ORDER BY dashboard_id, refresh_status;

-- ============================================================
-- 26. TRANSACTIONAL FILTER STATE DEMONSTRATION
-- ============================================================

DO $$
DECLARE
    v_dashboard_id BIGINT;
BEGIN
    SELECT dashboard_id
    INTO v_dashboard_id
    FROM dashboards
    WHERE dashboard_name = 'Retail Sales Performance'
      AND owner_email = 'admin@example.com';

    CALL save_filter_state(
        v_dashboard_id,
        'admin@example.com',
        'region_name',
        '["North","South"]'::JSONB
    );

    CALL save_filter_state(
        v_dashboard_id,
        'admin@example.com',
        'category_name',
        '["Electronics"]'::JSONB
    );
END;
$$;

-- ============================================================
-- 27. BOOKMARK RETRIEVAL
-- ============================================================

SELECT
    restore_bookmark(
        dashboard_id,
        'admin@example.com',
        'North Region Analysis'
    ) AS saved_dashboard_state
FROM dashboards
WHERE dashboard_name = 'Retail Sales Performance';

-- ============================================================
-- 28. FINAL DASHBOARD INVENTORY
-- ============================================================

SELECT
    d.dashboard_name,
    COUNT(v.visualization_id) AS visualization_count
FROM dashboards d
LEFT JOIN visualizations v
    ON v.dashboard_id = d.dashboard_id
GROUP BY d.dashboard_id, d.dashboard_name;

COMMIT;

-- ============================================================
-- OPERATIONAL NOTES
-- ============================================================
-- 1. The fact table contains transaction-level data.
-- 2. The analytics view exposes reusable measures.
-- 3. KPI functions provide card-level aggregation.
-- 4. Matrix and chart functions return visualization datasets.
-- 5. Geographic coordinates support map rendering.
-- 6. Filter states are user-specific.
-- 7. Bookmarks store dashboard state, not transaction data.
-- 8. Drill-through routes restrict available detail navigation.
-- 9. JSONB preserves flexible visualization configuration.
-- 10. Database constraints protect data integrity.
-- 11. Application authorization must still enforce user access.
-- 12. Refresh orchestration and visual rendering are external.
-- ============================================================
