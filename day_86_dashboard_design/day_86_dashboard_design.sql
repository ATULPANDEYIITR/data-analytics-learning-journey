/*
 * ENTERPRISE DASHBOARD DESIGN AND KPI ANALYTICS DATABASE
 *
 * PostgreSQL 14+
 *
 * Implements:
 * - Dashboard ownership and permissions
 * - Dashboard visual configuration
 * - KPI definitions and calculations
 * - KPI threshold policies
 * - Business metric records
 * - Dashboard filters and saved views
 * - Chart configuration and layout
 * - Interactive dashboard events
 * - KPI evaluation history
 * - Accessibility validation
 * - Aggregation and reporting
 * - Transactional dashboard configuration
 *
 * Execute using psql.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS dashboard;

SET search_path TO dashboard, public;

-- ==========================================================
-- 1. ENUMERATIONS
-- ==========================================================

CREATE TYPE user_role AS ENUM (
    'viewer',
    'analyst',
    'manager',
    'administrator'
);

CREATE TYPE kpi_status AS ENUM (
    'good',
    'warning',
    'critical',
    'neutral'
);

CREATE TYPE metric_format AS ENUM (
    'number',
    'currency',
    'percentage',
    'duration'
);

CREATE TYPE aggregation_type AS ENUM (
    'sum',
    'average',
    'count',
    'minimum',
    'maximum'
);

CREATE TYPE chart_type AS ENUM (
    'line',
    'bar',
    'donut',
    'area',
    'table'
);

CREATE TYPE dashboard_event_type AS ENUM (
    'filter_changed',
    'sort_changed',
    'drill_down',
    'reset'
);

CREATE TYPE comparison_direction AS ENUM (
    'higher_is_better',
    'lower_is_better'
);

-- ==========================================================
-- 2. USERS AND ACCESS CONTROL
-- ==========================================================

CREATE TABLE dashboard_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role user_role NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- 3. DESIGN SYSTEM
-- ==========================================================

CREATE TABLE design_tokens (
    token_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    token_name VARCHAR(80) NOT NULL UNIQUE,
    token_category VARCHAR(40) NOT NULL,
    token_value VARCHAR(100) NOT NULL,
    semantic_meaning TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_token_category CHECK (
        token_category IN (
            'color',
            'typography',
            'spacing',
            'radius',
            'shadow'
        )
    )
);

CREATE TABLE typography_styles (
    typography_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    style_name VARCHAR(80) NOT NULL UNIQUE,
    font_size INTEGER NOT NULL,
    font_weight INTEGER NOT NULL,
    line_height NUMERIC(5,2) NOT NULL,

    CONSTRAINT valid_font_size CHECK (
        font_size BETWEEN 8 AND 96
    ),

    CONSTRAINT valid_font_weight CHECK (
        font_weight IN (100, 200, 300, 400, 500, 600, 700, 800, 900)
    ),

    CONSTRAINT valid_line_height CHECK (
        line_height BETWEEN 0.8 AND 3.0
    )
);

-- ==========================================================
-- 4. DASHBOARD DEFINITIONS
-- ==========================================================

CREATE TABLE dashboards (
    dashboard_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id BIGINT NOT NULL REFERENCES dashboard_users(user_id),
    dashboard_name VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(80) NOT NULL,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    default_time_range VARCHAR(30) NOT NULL DEFAULT '30_days',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_dashboard_time_range CHECK (
        default_time_range IN (
            '7_days',
            '30_days',
            '90_days',
            '12_months',
            'custom'
        )
    ),

    CONSTRAINT unique_dashboard_name_per_owner UNIQUE (
        owner_id,
        dashboard_name
    )
);

CREATE INDEX idx_dashboards_owner
ON dashboards(owner_id, is_archived);

CREATE INDEX idx_dashboards_published
ON dashboards(is_published, category)
WHERE is_published = TRUE AND is_archived = FALSE;

-- ==========================================================
-- 5. DASHBOARD ACCESS POLICIES
-- ==========================================================

CREATE TABLE dashboard_permissions (
    permission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(dashboard_id)
        ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES dashboard_users(user_id)
        ON DELETE CASCADE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_share BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dashboard_id, user_id),

    CONSTRAINT edit_requires_view CHECK (
        NOT can_edit OR can_view
    ),

    CONSTRAINT share_requires_view CHECK (
        NOT can_share OR can_view
    )
);

CREATE INDEX idx_dashboard_permissions_user
ON dashboard_permissions(user_id, dashboard_id);

-- ==========================================================
-- 6. BUSINESS METRIC DATA
-- ==========================================================

CREATE TABLE business_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recorded_on DATE NOT NULL,
    department VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    revenue NUMERIC(16,2) NOT NULL,
    expenses NUMERIC(16,2) NOT NULL,
    orders INTEGER NOT NULL,
    satisfaction NUMERIC(5,2) NOT NULL,
    conversion_rate NUMERIC(5,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nonnegative_revenue CHECK (revenue >= 0),
    CONSTRAINT nonnegative_expenses CHECK (expenses >= 0),
    CONSTRAINT nonnegative_orders CHECK (orders >= 0),

    CONSTRAINT valid_satisfaction CHECK (
        satisfaction BETWEEN 0 AND 100
    ),

    CONSTRAINT valid_conversion_rate CHECK (
        conversion_rate BETWEEN 0 AND 100
    ),

    CONSTRAINT unique_business_metric_dimension UNIQUE (
        recorded_on,
        department,
        region
    )
);

CREATE INDEX idx_business_metrics_date
ON business_metrics(recorded_on DESC);

CREATE INDEX idx_business_metrics_region_date
ON business_metrics(region, recorded_on DESC);

CREATE INDEX idx_business_metrics_department
ON business_metrics(department, recorded_on DESC);

CREATE INDEX idx_business_metrics_revenue
ON business_metrics(revenue DESC);

-- ==========================================================
-- 7. KPI DEFINITIONS
-- ==========================================================

CREATE TABLE kpi_definitions (
    kpi_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(dashboard_id)
        ON DELETE CASCADE,
    kpi_code VARCHAR(80) NOT NULL,
    kpi_name VARCHAR(150) NOT NULL,
    description TEXT,
    source_metric VARCHAR(80) NOT NULL,
    aggregation aggregation_type NOT NULL,
    display_format metric_format NOT NULL,
    direction comparison_direction NOT NULL DEFAULT 'higher_is_better',
    target_value NUMERIC(18,4),
    warning_threshold NUMERIC(18,4),
    critical_threshold NUMERIC(18,4),
    display_order INTEGER NOT NULL DEFAULT 1,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dashboard_id, kpi_code),

    CONSTRAINT valid_kpi_order CHECK (display_order > 0),

    CONSTRAINT valid_kpi_thresholds CHECK (
        warning_threshold IS NULL
        OR critical_threshold IS NULL
        OR (
            (
                direction = 'higher_is_better'
                AND warning_threshold >= critical_threshold
            )
            OR
            (
                direction = 'lower_is_better'
                AND warning_threshold <= critical_threshold
            )
        )
    )
);

CREATE INDEX idx_kpi_dashboard_visibility
ON kpi_definitions(dashboard_id, is_visible, display_order);

-- ==========================================================
-- 8. KPI VALUES AND EVALUATION HISTORY
-- ==========================================================

CREATE TABLE kpi_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kpi_id BIGINT NOT NULL REFERENCES kpi_definitions(kpi_id)
        ON DELETE CASCADE,
    evaluation_period DATE NOT NULL,
    actual_value NUMERIC(18,4) NOT NULL,
    previous_value NUMERIC(18,4),
    calculated_change NUMERIC(12,4),
    target_achievement NUMERIC(12,4),
    status kpi_status NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(kpi_id, evaluation_period)
);

CREATE INDEX idx_kpi_evaluations_period
ON kpi_evaluations(evaluation_period DESC, status);

CREATE INDEX idx_kpi_evaluations_status
ON kpi_evaluations(status, evaluated_at DESC);

-- ==========================================================
-- 9. VISUAL COMPONENTS
-- ==========================================================

CREATE TABLE dashboard_components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(dashboard_id)
        ON DELETE CASCADE,
    component_key VARCHAR(100) NOT NULL,
    component_title VARCHAR(150) NOT NULL,
    component_type chart_type NOT NULL,
    row_position INTEGER NOT NULL,
    column_position INTEGER NOT NULL,
    row_span INTEGER NOT NULL DEFAULT 1,
    column_span INTEGER NOT NULL DEFAULT 3,
    priority INTEGER NOT NULL DEFAULT 1,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dashboard_id, component_key),

    CONSTRAINT valid_component_positions CHECK (
        row_position > 0 AND column_position > 0
    ),

    CONSTRAINT valid_component_spans CHECK (
        row_span > 0 AND column_span BETWEEN 1 AND 12
    ),

    CONSTRAINT valid_component_priority CHECK (priority > 0),

    CONSTRAINT valid_component_column CHECK (
        column_position + column_span - 1 <= 12
    ),

    CONSTRAINT valid_component_configuration CHECK (
        jsonb_typeof(configuration) = 'object'
    )
);

CREATE INDEX idx_dashboard_components_order
ON dashboard_components(
    dashboard_id,
    row_position,
    priority DESC,
    column_position
);

CREATE INDEX idx_dashboard_components_configuration
ON dashboard_components USING GIN(configuration);

-- ==========================================================
-- 10. SAVED FILTERS AND VIEWS
-- ==========================================================

CREATE TABLE dashboard_saved_views (
    saved_view_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(dashboard_id)
        ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES dashboard_users(user_id)
        ON DELETE CASCADE,
    view_name VARCHAR(120) NOT NULL,
    filter_configuration JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dashboard_id, user_id, view_name),

    CONSTRAINT valid_filter_configuration CHECK (
        jsonb_typeof(filter_configuration) = 'object'
    )
);

CREATE INDEX idx_saved_views_owner
ON dashboard_saved_views(user_id, dashboard_id);

-- ==========================================================
-- 11. INTERACTION EVENT LOG
-- ==========================================================

CREATE TABLE dashboard_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(dashboard_id)
        ON DELETE CASCADE,
    user_id BIGINT REFERENCES dashboard_users(user_id)
        ON DELETE SET NULL,
    event_type dashboard_event_type NOT NULL,
    component_id BIGINT REFERENCES dashboard_components(component_id)
        ON DELETE SET NULL,
    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_event_payload CHECK (
        jsonb_typeof(event_payload) = 'object'
    )
);

CREATE INDEX idx_dashboard_events_recent
ON dashboard_events(dashboard_id, occurred_at DESC);

CREATE INDEX idx_dashboard_events_type
ON dashboard_events(event_type, occurred_at DESC);

-- ==========================================================
-- 12. ACCESSIBILITY AUDIT
-- ==========================================================

CREATE TABLE accessibility_audits (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(dashboard_id)
        ON DELETE CASCADE,
    component_id BIGINT REFERENCES dashboard_components(component_id)
        ON DELETE CASCADE,
    foreground_color VARCHAR(7) NOT NULL,
    background_color VARCHAR(7) NOT NULL,
    contrast_ratio NUMERIC(8,4) NOT NULL,
    minimum_required NUMERIC(4,2) NOT NULL DEFAULT 4.5,
    passes_normal_text BOOLEAN GENERATED ALWAYS AS (
        contrast_ratio >= minimum_required
    ) STORED,
    audited_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_contrast CHECK (
        contrast_ratio BETWEEN 1 AND 21
    ),

    CONSTRAINT valid_minimum_contrast CHECK (
        minimum_required BETWEEN 1 AND 21
    ),

    CONSTRAINT valid_foreground_color CHECK (
        foreground_color ~ '^#[0-9A-Fa-f]{6}$'
    ),

    CONSTRAINT valid_background_color CHECK (
        background_color ~ '^#[0-9A-Fa-f]{6}$'
    )
);

-- ==========================================================
-- 13. UPDATED_AT TRIGGER
-- ==========================================================

CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_dashboard_updated_at
BEFORE UPDATE ON dashboards
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- ==========================================================
-- 14. COMPONENT OVERLAP VALIDATION
-- ==========================================================

CREATE OR REPLACE FUNCTION prevent_component_overlap()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM dashboard_components existing
        WHERE existing.dashboard_id = NEW.dashboard_id
          AND existing.component_id <> COALESCE(NEW.component_id, -1)

          AND existing.row_position <
              NEW.row_position + NEW.row_span

          AND NEW.row_position <
              existing.row_position + existing.row_span

          AND existing.column_position <
              NEW.column_position + NEW.column_span

          AND NEW.column_position <
              existing.column_position + existing.column_span
    ) THEN
        RAISE EXCEPTION
            'Dashboard layout collision for component %',
            NEW.component_key;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_component_overlap
BEFORE INSERT OR UPDATE ON dashboard_components
FOR EACH ROW
EXECUTE FUNCTION prevent_component_overlap();

-- ==========================================================
-- 15. KPI EVALUATION FUNCTION
-- ==========================================================

CREATE OR REPLACE FUNCTION evaluate_kpi(
    p_kpi_id BIGINT,
    p_actual NUMERIC,
    p_previous NUMERIC DEFAULT NULL
)
RETURNS TABLE (
    calculated_change NUMERIC,
    target_achievement NUMERIC,
    calculated_status kpi_status
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_kpi kpi_definitions%ROWTYPE;
    v_change NUMERIC;
    v_achievement NUMERIC;
    v_status kpi_status := 'good';
    v_critical BOOLEAN := FALSE;
    v_warning BOOLEAN := FALSE;
BEGIN
    SELECT *
    INTO v_kpi
    FROM kpi_definitions
    WHERE kpi_id = p_kpi_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown KPI identifier: %', p_kpi_id;
    END IF;

    IF p_actual IS NULL THEN
        RAISE EXCEPTION 'Actual KPI value cannot be NULL';
    END IF;

    IF p_previous IS NOT NULL AND p_previous <> 0 THEN
        v_change := (
            (p_actual - p_previous) /
            ABS(p_previous)
        ) * 100;
    END IF;

    IF v_kpi.target_value IS NOT NULL
       AND v_kpi.target_value <> 0 THEN

        IF v_kpi.direction = 'higher_is_better' THEN
            v_achievement :=
                p_actual / v_kpi.target_value * 100;

        ELSIF p_actual <> 0 THEN
            v_achievement :=
                v_kpi.target_value / p_actual * 100;
        END IF;
    END IF;

    IF v_kpi.critical_threshold IS NOT NULL THEN
        v_critical :=
            CASE
                WHEN v_kpi.direction = 'higher_is_better'
                THEN p_actual < v_kpi.critical_threshold
                ELSE p_actual > v_kpi.critical_threshold
            END;
    END IF;

    IF v_kpi.warning_threshold IS NOT NULL THEN
        v_warning :=
            CASE
                WHEN v_kpi.direction = 'higher_is_better'
                THEN p_actual < v_kpi.warning_threshold
                ELSE p_actual > v_kpi.warning_threshold
            END;
    END IF;

    IF v_critical THEN
        v_status := 'critical';
    ELSIF v_warning THEN
        v_status := 'warning';
    END IF;

    RETURN QUERY
    SELECT v_change, v_achievement, v_status;
END;
$$;

-- ==========================================================
-- 16. KPI EVALUATION STORAGE FUNCTION
-- ==========================================================

CREATE OR REPLACE FUNCTION store_kpi_evaluation(
    p_kpi_id BIGINT,
    p_period DATE,
    p_actual NUMERIC,
    p_previous NUMERIC DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
    v_evaluation_id BIGINT;
BEGIN
    SELECT *
    INTO v_result
    FROM evaluate_kpi(
        p_kpi_id,
        p_actual,
        p_previous
    );

    INSERT INTO kpi_evaluations (
        kpi_id,
        evaluation_period,
        actual_value,
        previous_value,
        calculated_change,
        target_achievement,
        status
    )
    VALUES (
        p_kpi_id,
        p_period,
        p_actual,
        p_previous,
        v_result.calculated_change,
        v_result.target_achievement,
        v_result.calculated_status
    )
    ON CONFLICT (kpi_id, evaluation_period)
    DO UPDATE SET
        actual_value = EXCLUDED.actual_value,
        previous_value = EXCLUDED.previous_value,
        calculated_change = EXCLUDED.calculated_change,
        target_achievement = EXCLUDED.target_achievement,
        status = EXCLUDED.status,
        evaluated_at = CURRENT_TIMESTAMP
    RETURNING evaluation_id INTO v_evaluation_id;

    RETURN v_evaluation_id;
END;
$$;

-- ==========================================================
-- 17. BUSINESS PERFORMANCE VIEW
-- ==========================================================

CREATE OR REPLACE VIEW regional_performance AS
SELECT
    region,
    COUNT(*) AS record_count,
    SUM(revenue) AS total_revenue,
    SUM(expenses) AS total_expenses,
    SUM(revenue - expenses) AS total_profit,
    SUM(orders) AS total_orders,
    ROUND(AVG(satisfaction), 2) AS average_satisfaction,
    ROUND(AVG(conversion_rate), 2) AS average_conversion
FROM business_metrics
GROUP BY region;

CREATE OR REPLACE VIEW department_performance AS
SELECT
    department,
    COUNT(*) AS record_count,
    SUM(revenue) AS revenue,
    SUM(expenses) AS expenses,
    SUM(revenue - expenses) AS profit,
    ROUND(AVG(satisfaction), 2) AS satisfaction,
    ROUND(AVG(conversion_rate), 2) AS conversion_rate
FROM business_metrics
GROUP BY department;

-- ==========================================================
-- 18. DASHBOARD SUMMARY FUNCTION
-- ==========================================================

CREATE OR REPLACE FUNCTION get_dashboard_summary(
    p_dashboard_id BIGINT,
    p_from DATE,
    p_to DATE
)
RETURNS TABLE (
    total_revenue NUMERIC,
    total_expenses NUMERIC,
    total_profit NUMERIC,
    total_orders BIGINT,
    average_satisfaction NUMERIC,
    average_conversion NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_from IS NULL OR p_to IS NULL OR p_from > p_to THEN
        RAISE EXCEPTION 'Invalid dashboard date range';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM dashboards
        WHERE dashboard_id = p_dashboard_id
    ) THEN
        RAISE EXCEPTION 'Dashboard does not exist';
    END IF;

    RETURN QUERY
    SELECT
        COALESCE(SUM(b.revenue), 0),
        COALESCE(SUM(b.expenses), 0),
        COALESCE(SUM(b.revenue - b.expenses), 0),
        COALESCE(SUM(b.orders), 0)::BIGINT,
        COALESCE(AVG(b.satisfaction), 0),
        COALESCE(AVG(b.conversion_rate), 0)
    FROM business_metrics b
    WHERE b.recorded_on BETWEEN p_from AND p_to;
END;
$$;

-- ==========================================================
-- 19. DASHBOARD PUBLICATION POLICY
-- ==========================================================

CREATE OR REPLACE FUNCTION publish_dashboard(
    p_dashboard_id BIGINT,
    p_user_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_owner BIGINT;
    v_role user_role;
BEGIN
    SELECT d.owner_id, u.role
    INTO v_owner, v_role
    FROM dashboards d
    JOIN dashboard_users u
      ON u.user_id = p_user_id
    WHERE d.dashboard_id = p_dashboard_id
      AND u.is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dashboard or active user not found';
    END IF;

    IF v_owner <> p_user_id AND v_role <> 'administrator' THEN
        RAISE EXCEPTION 'Insufficient dashboard publication permission';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM dashboard_components
        WHERE dashboard_id = p_dashboard_id
          AND is_visible = TRUE
    ) THEN
        RAISE EXCEPTION 'Dashboard requires visible components';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM accessibility_audits
        WHERE dashboard_id = p_dashboard_id
          AND passes_normal_text = FALSE
    ) THEN
        RAISE EXCEPTION 'Dashboard has failing accessibility audits';
    END IF;

    UPDATE dashboards
    SET is_published = TRUE
    WHERE dashboard_id = p_dashboard_id;

    RETURN TRUE;
END;
$$;

-- ==========================================================
-- 20. SAMPLE USERS
-- ==========================================================

INSERT INTO dashboard_users (
    username,
    email,
    role
)
VALUES
    ('atul_analyst', 'atul.analyst@example.com', 'analyst'),
    ('finance_manager', 'finance@example.com', 'manager'),
    ('executive_viewer', 'viewer@example.com', 'viewer'),
    ('platform_admin', 'admin@example.com', 'administrator');

-- ==========================================================
-- 21. DESIGN TOKENS
-- ==========================================================

INSERT INTO design_tokens (
    token_name,
    token_category,
    token_value,
    semantic_meaning
)
VALUES
    ('primary', 'color', '#2563EB', 'Primary actions'),
    ('background', 'color', '#F8FAFC', 'Page background'),
    ('surface', 'color', '#FFFFFF', 'Cards and panels'),
    ('text', 'color', '#172033', 'Primary text'),
    ('muted', 'color', '#64748B', 'Secondary information'),
    ('success', 'color', '#15803D', 'Positive performance'),
    ('warning', 'color', '#B45309', 'Warning performance'),
    ('danger', 'color', '#B91C1C', 'Critical performance');

INSERT INTO typography_styles (
    style_name,
    font_size,
    font_weight,
    line_height
)
VALUES
    ('page_title', 28, 700, 1.20),
    ('section_title', 20, 600, 1.30),
    ('card_title', 14, 600, 1.40),
    ('kpi_value', 30, 700, 1.10),
    ('body', 14, 400, 1.50),
    ('caption', 12, 400, 1.40);

-- ==========================================================
-- 22. BUSINESS METRIC SAMPLE DATA
-- ==========================================================

INSERT INTO business_metrics (
    recorded_on,
    department,
    region,
    revenue,
    expenses,
    orders,
    satisfaction,
    conversion_rate
)
VALUES
    ('2026-11-20', 'Sales', 'North', 18000, 11000, 120, 91, 5.2),
    ('2026-11-21', 'Technology', 'North', 14000, 9000, 90, 87, 4.5),
    ('2026-11-22', 'Sales', 'South', 16000, 10000, 110, 83, 3.8),
    ('2026-11-23', 'Technology', 'South', 12000, 8500, 75, 88, 4.2),
    ('2026-11-24', 'Operations', 'East', 9000, 7000, 65, 79, 2.8),
    ('2026-11-25', 'Sales', 'East', 21000, 13000, 140, 94, 5.8),
    ('2026-11-26', 'Operations', 'West', 11000, 7500, 80, 85, 3.6),
    ('2026-11-27', 'Technology', 'West', 15000, 9500, 95, 90, 4.9);

-- ==========================================================
-- 23. DASHBOARD SAMPLE
-- ==========================================================

INSERT INTO dashboards (
    owner_id,
    dashboard_name,
    description,
    category,
    default_time_range
)
VALUES
    (
        1,
        'Enterprise Performance',
        'Financial, operational and customer performance',
        'business',
        '30_days'
    );

INSERT INTO dashboard_permissions (
    dashboard_id,
    user_id,
    can_view,
    can_edit,
    can_share
)
VALUES
    (1, 2, TRUE, TRUE, FALSE),
    (1, 3, TRUE, FALSE, FALSE),
    (1, 4, TRUE, TRUE, TRUE);

-- ==========================================================
-- 24. KPI DEFINITIONS
-- ==========================================================

INSERT INTO kpi_definitions (
    dashboard_id,
    kpi_code,
    kpi_name,
    description,
    source_metric,
    aggregation,
    display_format,
    direction,
    target_value,
    warning_threshold,
    critical_threshold,
    display_order
)
VALUES
    (
        1,
        'REVENUE',
        'Total Revenue',
        'Total revenue generated',
        'revenue',
        'sum',
        'currency',
        'higher_is_better',
        50000,
        35000,
        25000,
        1
    ),
    (
        1,
        'PROFIT',
        'Operating Profit',
        'Revenue less operating expenses',
        'profit',
        'sum',
        'currency',
        'higher_is_better',
        15000,
        8000,
        4000,
        2
    ),
    (
        1,
        'SATISFACTION',
        'Customer Satisfaction',
        'Average satisfaction score',
        'satisfaction',
        'average',
        'percentage',
        'higher_is_better',
        90,
        75,
        60,
        3
    ),
    (
        1,
        'CONVERSION',
        'Conversion Rate',
        'Average conversion percentage',
        'conversion_rate',
        'average',
        'percentage',
        'higher_is_better',
        5,
        2.5,
        1.5,
        4
    );

-- ==========================================================
-- 25. DASHBOARD COMPONENT LAYOUT
-- ==========================================================

INSERT INTO dashboard_components (
    dashboard_id,
    component_key,
    component_title,
    component_type,
    row_position,
    column_position,
    row_span,
    column_span,
    priority,
    configuration
)
VALUES
    (
        1,
        'revenue',
        'Revenue KPI',
        'table',
        1,
        1,
        1,
        3,
        10,
        '{"format":"currency","emphasis":"high"}'
    ),
    (
        1,
        'profit',
        'Profit KPI',
        'table',
        1,
        4,
        1,
        3,
        9,
        '{"format":"currency","emphasis":"high"}'
    ),
    (
        1,
        'satisfaction',
        'Customer Satisfaction',
        'table',
        1,
        7,
        1,
        3,
        8,
        '{"format":"percentage"}'
    ),
    (
        1,
        'conversion',
        'Conversion Rate',
        'table',
        1,
        10,
        1,
        3,
        7,
        '{"format":"percentage"}'
    ),
    (
        1,
        'revenue_trend',
        'Revenue Trend',
        'line',
        2,
        1,
        2,
        8,
        6,
        '{"time_granularity":"day","show_comparison":true}'
    ),
    (
        1,
        'regional_performance',
        'Regional Performance',
        'bar',
        2,
        9,
        2,
        4,
        5,
        '{"orientation":"vertical","sort":"descending"}'
    );

-- ==========================================================
-- 26. SAVED FILTERS
-- ==========================================================

INSERT INTO dashboard_saved_views (
    dashboard_id,
    user_id,
    view_name,
    filter_configuration,
    is_default
)
VALUES
    (
        1,
        1,
        'North Region',
        '{"region":"North","sortBy":"revenue","descending":true}',
        TRUE
    ),
    (
        1,
        2,
        'Sales Performance',
        '{"department":"Sales","sortBy":"revenue"}',
        FALSE
    );

-- ==========================================================
-- 27. ACCESSIBILITY AUDIT RECORDS
-- ==========================================================

INSERT INTO accessibility_audits (
    dashboard_id,
    foreground_color,
    background_color,
    contrast_ratio,
    minimum_required
)
VALUES
    (1, '#172033', '#FFFFFF', 16.00, 4.50),
    (1, '#64748B', '#FFFFFF', 4.76, 4.50),
    (1, '#FFFFFF', '#2563EB', 5.17, 4.50);

-- ==========================================================
-- 28. KPI EVALUATION EXAMPLES
-- ==========================================================

SELECT store_kpi_evaluation(
    kpi_id,
    DATE '2026-11-27',
    CASE kpi_code
        WHEN 'REVENUE' THEN 116000
        WHEN 'PROFIT' THEN 49000
        WHEN 'SATISFACTION' THEN 87.125
        WHEN 'CONVERSION' THEN 4.35
    END,
    CASE kpi_code
        WHEN 'REVENUE' THEN 110000
        WHEN 'PROFIT' THEN 45000
        WHEN 'SATISFACTION' THEN 85
        WHEN 'CONVERSION' THEN 4.1
    END
)
FROM kpi_definitions
WHERE dashboard_id = 1;

-- ==========================================================
-- 29. EVENT HISTORY
-- ==========================================================

INSERT INTO dashboard_events (
    dashboard_id,
    user_id,
    event_type,
    event_payload
)
VALUES
    (
        1,
        1,
        'filter_changed',
        '{"region":"North"}'
    ),
    (
        1,
        2,
        'drill_down',
        '{"component":"regional_performance","region":"East"}'
    ),
    (
        1,
        1,
        'sort_changed',
        '{"field":"revenue","direction":"descending"}'
    );

-- ==========================================================
-- 30. RETRIEVAL QUERIES
-- ==========================================================

-- Dashboard components in visual priority order.

SELECT
    component_key,
    component_title,
    component_type,
    row_position,
    column_position,
    row_span,
    column_span,
    priority
FROM dashboard_components
WHERE dashboard_id = 1
  AND is_visible = TRUE
ORDER BY
    row_position,
    priority DESC,
    column_position;

-- KPI definitions and latest evaluation.

SELECT
    k.kpi_code,
    k.kpi_name,
    k.display_format,
    k.target_value,
    e.actual_value,
    e.calculated_change,
    e.target_achievement,
    e.status
FROM kpi_definitions k
LEFT JOIN LATERAL (
    SELECT *
    FROM kpi_evaluations evaluation
    WHERE evaluation.kpi_id = k.kpi_id
    ORDER BY evaluation_period DESC
    LIMIT 1
) e ON TRUE
WHERE k.dashboard_id = 1
ORDER BY k.display_order;

-- ==========================================================
-- 31. AGGREGATION AND ANALYTICS
-- ==========================================================

SELECT *
FROM regional_performance
ORDER BY total_revenue DESC;

SELECT *
FROM department_performance
ORDER BY profit DESC;

-- Daily revenue trend.

SELECT
    recorded_on,
    SUM(revenue) AS daily_revenue,
    SUM(expenses) AS daily_expenses,
    SUM(revenue - expenses) AS daily_profit,
    SUM(orders) AS daily_orders
FROM business_metrics
GROUP BY recorded_on
ORDER BY recorded_on;

-- Rolling seven-record revenue average.

WITH daily_revenue AS (
    SELECT
        recorded_on,
        SUM(revenue) AS revenue
    FROM business_metrics
    GROUP BY recorded_on
),
rolling_metrics AS (
    SELECT
        recorded_on,
        revenue,
        AVG(revenue) OVER (
            ORDER BY recorded_on
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_average
    FROM daily_revenue
)
SELECT *
FROM rolling_metrics
ORDER BY recorded_on;

-- ==========================================================
-- 32. KPI STATUS REPORTING
-- ==========================================================

SELECT
    status,
    COUNT(*) AS kpi_count,
    ROUND(AVG(actual_value), 2) AS average_actual_value
FROM kpi_evaluations
GROUP BY status
ORDER BY status;

-- Target achievement report.

SELECT
    k.kpi_name,
    e.actual_value,
    k.target_value,
    e.target_achievement,
    e.status,
    CASE
        WHEN e.target_achievement IS NULL
            THEN 'NOT_COMPARABLE'
        WHEN e.target_achievement >= 100
            THEN 'TARGET_MET'
        ELSE 'TARGET_NOT_MET'
    END AS target_result
FROM kpi_definitions k
JOIN kpi_evaluations e
  ON e.kpi_id = k.kpi_id
WHERE k.dashboard_id = 1
ORDER BY k.display_order;

-- ==========================================================
-- 33. VALIDATION AND FAILURE INVESTIGATION
-- ==========================================================

-- Components exceeding grid boundaries.

SELECT
    component_id,
    component_key,
    column_position,
    column_span
FROM dashboard_components
WHERE column_position + column_span - 1 > 12;

-- Components with insufficient contrast.

SELECT
    audit_id,
    component_id,
    foreground_color,
    background_color,
    contrast_ratio,
    minimum_required
FROM accessibility_audits
WHERE passes_normal_text = FALSE;

-- KPIs currently requiring attention.

SELECT
    k.kpi_name,
    e.actual_value,
    e.status,
    e.evaluated_at
FROM kpi_evaluations e
JOIN kpi_definitions k
  ON k.kpi_id = e.kpi_id
WHERE e.status IN ('warning', 'critical')
ORDER BY e.evaluated_at DESC;

-- Dashboard interaction activity.

SELECT
    event_type,
    COUNT(*) AS total_events,
    MAX(occurred_at) AS latest_event
FROM dashboard_events
WHERE dashboard_id = 1
GROUP BY event_type;

-- ==========================================================
-- 34. ELIGIBILITY DETERMINATION
-- ==========================================================

SELECT
    d.dashboard_id,
    d.dashboard_name,
    d.is_published,

    EXISTS (
        SELECT 1
        FROM dashboard_components c
        WHERE c.dashboard_id = d.dashboard_id
          AND c.is_visible = TRUE
    ) AS has_visible_components,

    NOT EXISTS (
        SELECT 1
        FROM accessibility_audits a
        WHERE a.dashboard_id = d.dashboard_id
          AND a.passes_normal_text = FALSE
    ) AS accessibility_passed,

    (
        EXISTS (
            SELECT 1
            FROM dashboard_components c
            WHERE c.dashboard_id = d.dashboard_id
              AND c.is_visible = TRUE
        )
        AND NOT EXISTS (
            SELECT 1
            FROM accessibility_audits a
            WHERE a.dashboard_id = d.dashboard_id
              AND a.passes_normal_text = FALSE
        )
    ) AS publication_eligible

FROM dashboards d
WHERE d.dashboard_id = 1;

-- ==========================================================
-- 35. TRANSACTIONAL DASHBOARD UPDATE
-- ==========================================================

-- The transaction ensures that a failed layout update does not
-- leave a partially published configuration.

SAVEPOINT before_dashboard_update;

UPDATE dashboard_components
SET priority = priority + 1
WHERE dashboard_id = 1
  AND component_key = 'revenue';

UPDATE dashboards
SET description =
    'Updated enterprise financial and operational dashboard'
WHERE dashboard_id = 1;

-- Confirm the configuration before accepting the update.

SELECT
    dashboard_name,
    description,
    updated_at
FROM dashboards
WHERE dashboard_id = 1;

RELEASE SAVEPOINT before_dashboard_update;

-- ==========================================================
-- 36. PERMISSION VALIDATION
-- ==========================================================

SELECT
    u.username,
    u.role,
    p.can_view,
    p.can_edit,
    p.can_share,
    d.dashboard_name
FROM dashboard_permissions p
JOIN dashboard_users u
  ON u.user_id = p.user_id
JOIN dashboards d
  ON d.dashboard_id = p.dashboard_id
WHERE d.dashboard_id = 1
ORDER BY u.username;

-- ==========================================================
-- 37. PUBLICATION ELIGIBILITY
-- ==========================================================

-- The sample dashboard can be published only when it has
-- visible components and no recorded accessibility failures.
-- This is an application-level policy enforced by the function.

SELECT publish_dashboard(1, 1);

-- ==========================================================
-- 38. FINAL REPORT
-- ==========================================================

SELECT
    d.dashboard_name,
    d.is_published,
    COUNT(DISTINCT c.component_id) AS total_components,
    COUNT(DISTINCT k.kpi_id) AS total_kpis,
    COUNT(DISTINCT e.event_id) AS interaction_events
FROM dashboards d
LEFT JOIN dashboard_components c
  ON c.dashboard_id = d.dashboard_id
LEFT JOIN kpi_definitions k
  ON k.dashboard_id = d.dashboard_id
LEFT JOIN dashboard_events e
  ON e.dashboard_id = d.dashboard_id
WHERE d.dashboard_id = 1
GROUP BY d.dashboard_id, d.dashboard_name, d.is_published;

COMMIT;
