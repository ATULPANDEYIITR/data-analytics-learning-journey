/*
================================================================
POWER BI ADVANCED ANALYTICS
PostgreSQL 15+

Subject areas:
1. Decomposition trees
2. Key influencers
3. Time-series forecasting
4. Anomaly detection
5. Analytical measures
6. Reporting and validation

The database represents an analytical sales warehouse.

Execution:
Run this script in a PostgreSQL database using psql.

The script creates a dedicated schema and sample data.
================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS powerbi_analytics;

SET search_path TO powerbi_analytics, public;


-- ============================================================
-- 1. DIMENSION TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_region (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR(60) NOT NULL UNIQUE,
    country_code CHAR(2) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_region_name
        CHECK (length(trim(region_name)) > 0),

    CONSTRAINT valid_country_code
        CHECK (country_code ~ '^[A-Z]{2}$')
);


CREATE TABLE IF NOT EXISTS dim_product (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(80) NOT NULL,
    standard_price NUMERIC(14,2) NOT NULL,

    CONSTRAINT valid_standard_price
        CHECK (standard_price >= 0)
);


CREATE TABLE IF NOT EXISTS dim_customer_segment (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);


CREATE TABLE IF NOT EXISTS dim_channel (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name VARCHAR(60) NOT NULL UNIQUE
);


-- ============================================================
-- 2. DATE DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    calendar_year SMALLINT NOT NULL,
    calendar_month SMALLINT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter_number SMALLINT NOT NULL,

    CONSTRAINT valid_calendar_month
        CHECK (calendar_month BETWEEN 1 AND 12),

    CONSTRAINT valid_quarter
        CHECK (quarter_number BETWEEN 1 AND 4),

    CONSTRAINT valid_calendar_year
        CHECK (calendar_year BETWEEN 2000 AND 2100)
);


-- ============================================================
-- 3. FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_sales (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    transaction_date DATE NOT NULL
        REFERENCES dim_date(date_id),

    region_id BIGINT NOT NULL
        REFERENCES dim_region(region_id),

    product_id BIGINT NOT NULL
        REFERENCES dim_product(product_id),

    segment_id BIGINT NOT NULL
        REFERENCES dim_customer_segment(segment_id),

    channel_id BIGINT NOT NULL
        REFERENCES dim_channel(channel_id),

    revenue NUMERIC(16,2) NOT NULL,
    units INTEGER NOT NULL,
    marketing_spend NUMERIC(16,2) NOT NULL,
    discount_percent NUMERIC(5,2) NOT NULL,
    satisfaction_score NUMERIC(4,2) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_revenue
        CHECK (revenue >= 0),

    CONSTRAINT valid_units
        CHECK (units >= 0),

    CONSTRAINT valid_marketing
        CHECK (marketing_spend >= 0),

    CONSTRAINT valid_discount
        CHECK (discount_percent BETWEEN 0 AND 100),

    CONSTRAINT valid_satisfaction
        CHECK (satisfaction_score BETWEEN 0 AND 10)
);


-- ============================================================
-- 4. ANALYTICAL EXECUTION LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS analysis_run (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    analysis_type VARCHAR(40) NOT NULL,

    execution_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    parameters JSONB NOT NULL DEFAULT '{}'::JSONB,

    result_count INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_analysis_type
        CHECK (
            analysis_type IN (
                'DECOMPOSITION',
                'KEY_INFLUENCERS',
                'FORECAST',
                'ANOMALY'
            )
        ),

    CONSTRAINT valid_execution_status
        CHECK (
            execution_status IN (
                'PENDING',
                'RUNNING',
                'COMPLETED',
                'FAILED'
            )
        ),

    CONSTRAINT valid_result_count
        CHECK (result_count >= 0)
);


-- ============================================================
-- 5. ANOMALY RESULTS
-- ============================================================

CREATE TABLE IF NOT EXISTS anomaly_result (
    anomaly_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id UUID NOT NULL
        REFERENCES analysis_run(run_id),

    transaction_id BIGINT NOT NULL
        REFERENCES fact_sales(transaction_id),

    actual_value NUMERIC(16,2) NOT NULL,

    expected_value NUMERIC(16,2) NOT NULL,

    anomaly_score NUMERIC(12,4) NOT NULL,

    severity VARCHAR(20) NOT NULL,

    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_anomaly_severity
        CHECK (severity IN ('HIGH', 'CRITICAL')),

    CONSTRAINT unique_run_transaction
        UNIQUE (run_id, transaction_id)
);


-- ============================================================
-- 6. FORECAST RESULTS
-- ============================================================

CREATE TABLE IF NOT EXISTS forecast_result (
    forecast_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id UUID NOT NULL
        REFERENCES analysis_run(run_id),

    forecast_period DATE NOT NULL,

    predicted_revenue NUMERIC(16,2) NOT NULL,

    lower_bound NUMERIC(16,2) NOT NULL,

    upper_bound NUMERIC(16,2) NOT NULL,

    CONSTRAINT valid_forecast_bounds
        CHECK (
            lower_bound >= 0
            AND predicted_revenue >= lower_bound
            AND upper_bound >= predicted_revenue
        ),

    CONSTRAINT unique_run_period
        UNIQUE (run_id, forecast_period)
);


-- ============================================================
-- 7. INFLUENCER RESULTS
-- ============================================================

CREATE TABLE IF NOT EXISTS influencer_result (
    influencer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id UUID NOT NULL
        REFERENCES analysis_run(run_id),

    dimension_name VARCHAR(40) NOT NULL,

    dimension_value VARCHAR(100) NOT NULL,

    sample_size INTEGER NOT NULL,

    target_rate NUMERIC(10,6) NOT NULL,

    comparison_rate NUMERIC(10,6) NOT NULL,

    difference NUMERIC(10,6) NOT NULL,

    CONSTRAINT valid_influencer_dimension
        CHECK (
            dimension_name IN (
                'region',
                'product',
                'segment',
                'channel'
            )
        ),

    CONSTRAINT valid_sample_size
        CHECK (sample_size > 0),

    CONSTRAINT valid_target_rate
        CHECK (target_rate BETWEEN 0 AND 1),

    CONSTRAINT valid_comparison_rate
        CHECK (comparison_rate BETWEEN 0 AND 1)
);


-- ============================================================
-- 8. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_date
    ON fact_sales(transaction_date);

CREATE INDEX IF NOT EXISTS idx_sales_region_date
    ON fact_sales(region_id, transaction_date);

CREATE INDEX IF NOT EXISTS idx_sales_product
    ON fact_sales(product_id);

CREATE INDEX IF NOT EXISTS idx_sales_segment
    ON fact_sales(segment_id);

CREATE INDEX IF NOT EXISTS idx_sales_channel
    ON fact_sales(channel_id);

CREATE INDEX IF NOT EXISTS idx_sales_revenue
    ON fact_sales(revenue DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_run_type
    ON analysis_run(analysis_type, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomaly_severity
    ON anomaly_result(severity, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_forecast_period
    ON forecast_result(forecast_period);


-- ============================================================
-- 9. SAMPLE DIMENSION DATA
-- ============================================================

INSERT INTO dim_region(region_name, country_code)
VALUES
    ('North', 'IN'),
    ('South', 'IN'),
    ('East', 'IN'),
    ('West', 'IN')
ON CONFLICT (region_name) DO NOTHING;


INSERT INTO dim_product(
    product_name,
    category,
    standard_price
)
VALUES
    ('Laptop', 'Computing', 850),
    ('Mobile', 'Electronics', 420),
    ('Tablet', 'Electronics', 300),
    ('Monitor', 'Computing', 260)
ON CONFLICT (product_name) DO NOTHING;


INSERT INTO dim_customer_segment(
    segment_name,
    description
)
VALUES
    ('Consumer', 'Individual retail customers'),
    ('Corporate', 'Enterprise customers'),
    ('Small Business', 'Small and medium businesses')
ON CONFLICT (segment_name) DO NOTHING;


INSERT INTO dim_channel(channel_name)
VALUES
    ('Online'),
    ('Retail'),
    ('Partner')
ON CONFLICT (channel_name) DO NOTHING;


-- ============================================================
-- 10. DATE DIMENSION POPULATION
-- ============================================================

INSERT INTO dim_date(
    date_id,
    calendar_year,
    calendar_month,
    month_name,
    quarter_number
)
SELECT
    generated_date::DATE,
    EXTRACT(YEAR FROM generated_date)::SMALLINT,
    EXTRACT(MONTH FROM generated_date)::SMALLINT,
    TO_CHAR(generated_date, 'Month'),
    EXTRACT(QUARTER FROM generated_date)::SMALLINT
FROM generate_series(
    DATE '2025-01-01',
    DATE '2026-12-31',
    INTERVAL '1 day'
) AS generated_date
ON CONFLICT (date_id) DO NOTHING;


-- ============================================================
-- 11. SAMPLE FACT DATA
-- ============================================================

INSERT INTO fact_sales(
    transaction_date,
    region_id,
    product_id,
    segment_id,
    channel_id,
    revenue,
    units,
    marketing_spend,
    discount_percent,
    satisfaction_score
)
SELECT
    DATE '2025-01-01' + (g % 365)::INTEGER,

    1 + ((g * 7 + g / 4) % 4),

    1 + ((g * 3 + g / 5) % 4),

    1 + ((g * 5 + g / 7) % 3),

    1 + ((g * 2 + g / 9) % 3),

    ROUND(
        GREATEST(
            0,
            (
                CASE
                    WHEN ((g * 3 + g / 5) % 4) = 0 THEN 850
                    WHEN ((g * 3 + g / 5) % 4) = 1 THEN 420
                    WHEN ((g * 3 + g / 5) % 4) = 2 THEN 300
                    ELSE 260
                END
                *
                (1 + ((g * 11) % 12))
                *
                (
                    CASE
                        WHEN ((g * 7 + g / 4) % 4) = 0 THEN 1.15
                        WHEN ((g * 7 + g / 4) % 4) = 1 THEN 1.05
                        WHEN ((g * 7 + g / 4) % 4) = 2 THEN 0.90
                        ELSE 1.10
                    END
                )
                *
                (
                    CASE
                        WHEN ((g * 5 + g / 7) % 3) = 1 THEN 1.30
                        WHEN ((g * 5 + g / 7) % 3) = 2 THEN 1.10
                        ELSE 1.00
                    END
                )
                *
                (1 - ((g * 13) % 20) / 100.0)
            )
            *
            CASE
                WHEN g IN (76, 191, 331, 471) THEN 3.5
                ELSE 1.0
            END
        )::NUMERIC,
        2
    ),

    1 + ((g * 11) % 12),

    ROUND((50 + ((g * 37) % 550))::NUMERIC, 2),

    ((g * 13) % 20)::NUMERIC,

    (5 + ((g * 17) % 51) / 10.0)::NUMERIC

FROM generate_series(1, 600) AS g;


-- ============================================================
-- 12. BUSINESS METRICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW vw_business_metrics AS
SELECT
    COUNT(*) AS transaction_count,

    SUM(revenue) AS total_revenue,

    SUM(units) AS total_units,

    ROUND(AVG(revenue), 2) AS average_revenue,

    SUM(marketing_spend) AS total_marketing_spend,

    ROUND(
        (
            SUM(revenue) - SUM(marketing_spend)
        ) / NULLIF(SUM(marketing_spend), 0),
        4
    ) AS marketing_roi,

    ROUND(
        AVG(satisfaction_score),
        2
    ) AS average_satisfaction

FROM fact_sales;


-- ============================================================
-- 13. MONTHLY REVENUE VIEW
-- ============================================================

CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_TRUNC(
        'month',
        transaction_date
    )::DATE AS month,

    SUM(revenue) AS monthly_revenue,

    COUNT(*) AS transaction_count,

    SUM(units) AS units_sold

FROM fact_sales

GROUP BY DATE_TRUNC(
    'month',
    transaction_date
)::DATE;


-- ============================================================
-- 14. DECOMPOSITION TREE FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION fn_decomposition_tree(
    p_dimension VARCHAR,
    p_top_n INTEGER DEFAULT 5
)
RETURNS TABLE (
    dimension_value VARCHAR,
    revenue NUMERIC,
    record_count BIGINT,
    contribution_percent NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_column TEXT;
BEGIN

    IF p_top_n < 1 OR p_top_n > 100 THEN
        RAISE EXCEPTION
            'top_n must be between 1 and 100';
    END IF;

    v_column := CASE p_dimension
        WHEN 'region' THEN 'region_name'
        WHEN 'product' THEN 'product_name'
        WHEN 'segment' THEN 'segment_name'
        WHEN 'channel' THEN 'channel_name'
        ELSE NULL
    END;

    IF v_column IS NULL THEN
        RAISE EXCEPTION
            'Unsupported decomposition dimension: %',
            p_dimension;
    END IF;

    RETURN QUERY EXECUTE format(
        '
        SELECT
            d.%1$I::VARCHAR,
            SUM(f.revenue)::NUMERIC,
            COUNT(*)::BIGINT,
            ROUND(
                100.0 * SUM(f.revenue)
                / NULLIF(
                    (
                        SELECT SUM(revenue)
                        FROM powerbi_analytics.fact_sales
                    ),
                    0
                ),
                2
            )::NUMERIC
        FROM powerbi_analytics.fact_sales f
        JOIN powerbi_analytics.%2$I d
            ON d.%3$I = f.%4$I
        GROUP BY d.%1$I
        ORDER BY SUM(f.revenue) DESC
        LIMIT $1
        ',
        CASE p_dimension
            WHEN 'region' THEN 'region_name'
            WHEN 'product' THEN 'product_name'
            WHEN 'segment' THEN 'segment_name'
            ELSE 'channel_name'
        END,
        CASE p_dimension
            WHEN 'region' THEN 'dim_region'
            WHEN 'product' THEN 'dim_product'
            WHEN 'segment' THEN 'dim_customer_segment'
            ELSE 'dim_channel'
        END,
        CASE p_dimension
            WHEN 'region' THEN 'region_id'
            WHEN 'product' THEN 'product_id'
            WHEN 'segment' THEN 'segment_id'
            ELSE 'channel_id'
        END,
        CASE p_dimension
            WHEN 'region' THEN 'region_id'
            WHEN 'product' THEN 'product_id'
            WHEN 'segment' THEN 'segment_id'
            ELSE 'channel_id'
        END
    )
    USING p_top_n;

END;
$$;


-- ============================================================
-- 15. KEY INFLUENCERS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION fn_key_influencers(
    p_minimum_group_size INTEGER DEFAULT 10
)
RETURNS TABLE (
    dimension_name TEXT,
    dimension_value TEXT,
    sample_size BIGINT,
    target_rate NUMERIC,
    comparison_rate NUMERIC,
    rate_difference NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_threshold NUMERIC;
BEGIN

    IF p_minimum_group_size < 2 THEN
        RAISE EXCEPTION
            'Minimum group size must be at least 2';
    END IF;

    SELECT percentile_cont(0.5)
        WITHIN GROUP (ORDER BY revenue)
    INTO v_threshold
    FROM powerbi_analytics.fact_sales;

    RETURN QUERY

    WITH dimension_groups AS (

        SELECT
            'region'::TEXT AS dimension_name,
            r.region_name::TEXT AS dimension_value,
            COUNT(*) AS sample_size,

            AVG(
                CASE WHEN f.revenue > v_threshold
                    THEN 1.0 ELSE 0.0 END
            ) AS target_rate

        FROM powerbi_analytics.fact_sales f

        JOIN powerbi_analytics.dim_region r
            ON r.region_id = f.region_id

        GROUP BY r.region_name

        UNION ALL

        SELECT
            'product',
            p.product_name,
            COUNT(*),

            AVG(
                CASE WHEN f.revenue > v_threshold
                    THEN 1.0 ELSE 0.0 END
            )

        FROM powerbi_analytics.fact_sales f

        JOIN powerbi_analytics.dim_product p
            ON p.product_id = f.product_id

        GROUP BY p.product_name

        UNION ALL

        SELECT
            'segment',
            s.segment_name,
            COUNT(*),

            AVG(
                CASE WHEN f.revenue > v_threshold
                    THEN 1.0 ELSE 0.0 END
            )

        FROM powerbi_analytics.fact_sales f

        JOIN powerbi_analytics.dim_customer_segment s
            ON s.segment_id = f.segment_id

        GROUP BY s.segment_name

        UNION ALL

        SELECT
            'channel',
            c.channel_name,
            COUNT(*),

            AVG(
                CASE WHEN f.revenue > v_threshold
                    THEN 1.0 ELSE 0.0 END
            )

        FROM powerbi_analytics.fact_sales f

        JOIN powerbi_analytics.dim_channel c
            ON c.channel_id = f.channel_id

        GROUP BY c.channel_name
    ),

    overall AS (
        SELECT
            AVG(
                CASE WHEN revenue > v_threshold
                    THEN 1.0 ELSE 0.0 END
            ) AS overall_rate
        FROM powerbi_analytics.fact_sales
    )

    SELECT
        g.dimension_name,
        g.dimension_value,
        g.sample_size,
        ROUND(g.target_rate::NUMERIC, 6),
        ROUND(
            (
                o.overall_rate * (
                    SELECT
                        COUNT(*)::NUMERIC - g.sample_size
                    FROM powerbi_analytics.fact_sales
                ) / NULLIF(
                    (
                        SELECT COUNT(*)::NUMERIC
                        FROM powerbi_analytics.fact_sales
                    ) - g.sample_size,
                    0
                )
            ),
            6
        ),
        ROUND(
            (
                g.target_rate -
                (
                    o.overall_rate * (
                        SELECT
                            COUNT(*)::NUMERIC - g.sample_size
                        FROM powerbi_analytics.fact_sales
                    ) / NULLIF(
                        (
                            SELECT COUNT(*)::NUMERIC
                            FROM powerbi_analytics.fact_sales
                        ) - g.sample_size,
                        0
                    )
                )
            ),
            6
        )

    FROM dimension_groups g
    CROSS JOIN overall o

    WHERE g.sample_size >= p_minimum_group_size

    ORDER BY 6 DESC;

END;
$$;


-- ============================================================
-- 16. FORECAST FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION fn_revenue_forecast(
    p_horizon INTEGER DEFAULT 3
)
RETURNS TABLE (
    forecast_period DATE,
    predicted_revenue NUMERIC,
    lower_bound NUMERIC,
    upper_bound NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_count BIGINT;
    v_slope DOUBLE PRECISION;
    v_intercept DOUBLE PRECISION;
    v_stddev DOUBLE PRECISION;
    v_last_month DATE;
    v_index INTEGER;
BEGIN

    IF p_horizon < 1 OR p_horizon > 36 THEN
        RAISE EXCEPTION
            'Forecast horizon must be between 1 and 36';
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS forecast_training (
        month_index BIGINT,
        month_date DATE,
        revenue DOUBLE PRECISION
    ) ON COMMIT DROP;

    TRUNCATE TABLE forecast_training;

    INSERT INTO forecast_training(
        month_index,
        month_date,
        revenue
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY month) - 1,
        month,
        monthly_revenue::DOUBLE PRECISION
    FROM powerbi_analytics.vw_monthly_revenue;

    SELECT COUNT(*), MAX(month_date)
    INTO v_count, v_last_month
    FROM forecast_training;

    IF v_count < 6 THEN
        RAISE EXCEPTION
            'At least six monthly observations are required';
    END IF;

    SELECT
        REGR_SLOPE(revenue, month_index),
        REGR_INTERCEPT(revenue, month_index)
    INTO v_slope, v_intercept
    FROM forecast_training;

    SELECT STDDEV_SAMP(
        revenue - (
            v_intercept + v_slope * month_index
        )
    )
    INTO v_stddev
    FROM forecast_training;

    v_stddev := COALESCE(v_stddev, 0);

    FOR v_index IN 1..p_horizon LOOP

        RETURN QUERY
        SELECT
            (
                v_last_month +
                make_interval(months => v_index)
            )::DATE,

            GREATEST(
                0,
                (
                    v_intercept +
                    v_slope * (v_count - 1 + v_index)
                )::NUMERIC
            ),

            GREATEST(
                0,
                (
                    v_intercept +
                    v_slope * (v_count - 1 + v_index)
                    -
                    1.96 * v_stddev *
                    SQRT(
                        1.0 + v_index::DOUBLE PRECISION / v_count
                    )
                )::NUMERIC
            ),

            (
                v_intercept +
                v_slope * (v_count - 1 + v_index)
                +
                1.96 * v_stddev *
                SQRT(
                    1.0 + v_index::DOUBLE PRECISION / v_count
                )
            )::NUMERIC;

    END LOOP;

END;
$$;


-- ============================================================
-- 17. ANOMALY DETECTION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION fn_detect_anomalies(
    p_threshold NUMERIC DEFAULT 3.5
)
RETURNS TABLE (
    transaction_id BIGINT,
    actual_revenue NUMERIC,
    expected_revenue NUMERIC,
    anomaly_score NUMERIC,
    severity TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_median NUMERIC;
    v_mad NUMERIC;
BEGIN

    IF p_threshold <= 0 THEN
        RAISE EXCEPTION
            'Anomaly threshold must be positive';
    END IF;

    SELECT percentile_cont(0.5)
        WITHIN GROUP (ORDER BY revenue)
    INTO v_median
    FROM powerbi_analytics.fact_sales;

    SELECT percentile_cont(0.5)
        WITHIN GROUP (
            ORDER BY ABS(revenue - v_median)
        )
    INTO v_mad
    FROM powerbi_analytics.fact_sales;

    IF COALESCE(v_mad, 0) = 0 THEN
        RAISE EXCEPTION
            'MAD is zero; anomaly scoring is unavailable';
    END IF;

    RETURN QUERY

    WITH scores AS (
        SELECT
            f.transaction_id,
            f.revenue,

            (
                0.6745 *
                (f.revenue - v_median) / v_mad
            ) AS score

        FROM powerbi_analytics.fact_sales f
    )

    SELECT
        s.transaction_id,
        s.revenue,
        v_median,
        ROUND(s.score, 4),

        CASE
            WHEN ABS(s.score) >= 7 THEN 'CRITICAL'
            ELSE 'HIGH'
        END::TEXT

    FROM scores s

    WHERE ABS(s.score) >= p_threshold

    ORDER BY ABS(s.score) DESC;

END;
$$;


-- ============================================================
-- 18. ANALYSIS RUN MANAGEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION fn_start_analysis(
    p_type VARCHAR,
    p_parameters JSONB DEFAULT '{}'::JSONB
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id UUID;
BEGIN

    INSERT INTO powerbi_analytics.analysis_run(
        analysis_type,
        execution_status,
        parameters
    )
    VALUES (
        p_type,
        'RUNNING',
        p_parameters
    )
    RETURNING run_id INTO v_run_id;

    RETURN v_run_id;

END;
$$;


CREATE OR REPLACE PROCEDURE sp_complete_analysis(
    p_run_id UUID,
    p_result_count INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN

    IF p_result_count < 0 THEN
        RAISE EXCEPTION
            'Result count cannot be negative';
    END IF;

    UPDATE powerbi_analytics.analysis_run
    SET
        execution_status = 'COMPLETED',
        result_count = p_result_count,
        completed_at = CURRENT_TIMESTAMP
    WHERE run_id = p_run_id
      AND execution_status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Analysis run not found or not running: %',
            p_run_id;
    END IF;

END;
$$;


-- ============================================================
-- 19. ANALYSIS RUN INTEGRITY TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validate_analysis_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF OLD.execution_status IN ('COMPLETED', 'FAILED')
       AND NEW.execution_status <> OLD.execution_status THEN

        RAISE EXCEPTION
            'Terminal analysis runs cannot be reopened';
    END IF;

    IF NEW.execution_status IN ('COMPLETED', 'FAILED')
       AND NEW.completed_at IS NULL THEN

        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;

END;
$$;


DROP TRIGGER IF EXISTS trg_analysis_transition
ON analysis_run;

CREATE TRIGGER trg_analysis_transition
BEFORE UPDATE ON analysis_run
FOR EACH ROW
EXECUTE FUNCTION fn_validate_analysis_transition();


-- ============================================================
-- 20. DECOMPOSITION TREE REPORTING
-- ============================================================

CREATE OR REPLACE VIEW vw_region_product_revenue AS
SELECT
    r.region_name,
    p.product_name,
    c.channel_name,
    SUM(f.revenue) AS revenue,
    COUNT(*) AS transaction_count,
    ROUND(
        100.0 * SUM(f.revenue) /
        NULLIF(
            SUM(SUM(f.revenue)) OVER (),
            0
        ),
        2
    ) AS contribution_percent

FROM fact_sales f

JOIN dim_region r
    ON r.region_id = f.region_id

JOIN dim_product p
    ON p.product_id = f.product_id

JOIN dim_channel c
    ON c.channel_id = f.channel_id

GROUP BY
    r.region_name,
    p.product_name,
    c.channel_name;


-- ============================================================
-- 21. CUSTOMER AND PRODUCT PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    p.product_name,
    p.category,
    SUM(f.revenue) AS revenue,
    SUM(f.units) AS units_sold,
    AVG(f.discount_percent) AS average_discount,
    AVG(f.satisfaction_score) AS average_satisfaction,
    SUM(f.marketing_spend) AS marketing_spend

FROM fact_sales f

JOIN dim_product p
    ON p.product_id = f.product_id

GROUP BY
    p.product_name,
    p.category;


-- ============================================================
-- 22. QUERY: BUSINESS MEASURES
-- ============================================================

SELECT *
FROM vw_business_metrics;


-- ============================================================
-- 23. QUERY: DECOMPOSITION ANALYSIS
-- ============================================================

SELECT *
FROM fn_decomposition_tree('region', 5);

SELECT *
FROM fn_decomposition_tree('product', 5);

SELECT *
FROM fn_decomposition_tree('channel', 5);


-- ============================================================
-- 24. QUERY: MULTI-DIMENSIONAL ANALYSIS
-- ============================================================

SELECT *
FROM vw_region_product_revenue
ORDER BY revenue DESC
LIMIT 20;


-- ============================================================
-- 25. QUERY: KEY INFLUENCERS
-- ============================================================

SELECT *
FROM fn_key_influencers(10);


-- ============================================================
-- 26. QUERY: FORECAST
-- ============================================================

SELECT *
FROM fn_revenue_forecast(3);


-- ============================================================
-- 27. QUERY: ANOMALY DETECTION
-- ============================================================

SELECT *
FROM fn_detect_anomalies(3.5);


-- ============================================================
-- 28. QUERY: MONTHLY TREND
-- ============================================================

WITH monthly AS (
    SELECT
        month,
        monthly_revenue,

        LAG(monthly_revenue) OVER (
            ORDER BY month
        ) AS previous_month

    FROM vw_monthly_revenue
)
SELECT
    month,
    monthly_revenue,
    previous_month,

    ROUND(
        100.0 * (
            monthly_revenue - previous_month
        ) / NULLIF(previous_month, 0),
        2
    ) AS growth_percent

FROM monthly
ORDER BY month;


-- ============================================================
-- 29. QUERY: RANKED REGIONAL PERFORMANCE
-- ============================================================

WITH regional_performance AS (
    SELECT
        r.region_name,
        SUM(f.revenue) AS revenue,
        SUM(f.units) AS units_sold

    FROM fact_sales f

    JOIN dim_region r
        ON r.region_id = f.region_id

    GROUP BY r.region_name
)
SELECT
    region_name,
    revenue,
    units_sold,

    DENSE_RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank,

    ROUND(
        100.0 * revenue /
        NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS contribution_percent

FROM regional_performance
ORDER BY revenue_rank;


-- ============================================================
-- 30. QUERY: PRODUCT PERFORMANCE
-- ============================================================

SELECT *
FROM vw_product_performance
ORDER BY revenue DESC;


-- ============================================================
-- 31. WORKFLOW: SAVE A FORECAST RUN
-- ============================================================

DO $$
DECLARE
    v_run_id UUID;
    v_count INTEGER;
BEGIN

    v_run_id := powerbi_analytics.fn_start_analysis(
        'FORECAST',
        '{"horizon": 3, "method": "linear_regression"}'::JSONB
    );

    INSERT INTO powerbi_analytics.forecast_result(
        run_id,
        forecast_period,
        predicted_revenue,
        lower_bound,
        upper_bound
    )
    SELECT
        v_run_id,
        forecast_period,
        predicted_revenue,
        lower_bound,
        upper_bound
    FROM powerbi_analytics.fn_revenue_forecast(3);

    GET DIAGNOSTICS v_count = ROW_COUNT;

    CALL powerbi_analytics.sp_complete_analysis(
        v_run_id,
        v_count
    );

    RAISE NOTICE
        'Forecast run completed: %, results: %',
        v_run_id,
        v_count;

END;
$$;


-- ============================================================
-- 32. WORKFLOW: SAVE ANOMALY RESULTS
-- ============================================================

DO $$
DECLARE
    v_run_id UUID;
    v_count INTEGER;
BEGIN

    v_run_id := powerbi_analytics.fn_start_analysis(
        'ANOMALY',
        '{"threshold": 3.5, "method": "MAD"}'::JSONB
    );

    INSERT INTO powerbi_analytics.anomaly_result(
        run_id,
        transaction_id,
        actual_value,
        expected_value,
        anomaly_score,
        severity
    )
    SELECT
        v_run_id,
        transaction_id,
        actual_revenue,
        expected_revenue,
        anomaly_score,
        severity
    FROM powerbi_analytics.fn_detect_anomalies(3.5);

    GET DIAGNOSTICS v_count = ROW_COUNT;

    CALL powerbi_analytics.sp_complete_analysis(
        v_run_id,
        v_count
    );

    RAISE NOTICE
        'Anomaly run completed: %, anomalies: %',
        v_run_id,
        v_count;

END;
$$;


-- ============================================================
-- 33. REPORTING: ANALYSIS EXECUTION HISTORY
-- ============================================================

SELECT
    run_id,
    analysis_type,
    execution_status,
    result_count,
    started_at,
    completed_at,
    parameters
FROM analysis_run
ORDER BY started_at DESC;


-- ============================================================
-- 34. REPORTING: STORED ANOMALIES
-- ============================================================

SELECT
    a.anomaly_id,
    a.transaction_id,
    a.actual_value,
    a.expected_value,
    a.anomaly_score,
    a.severity,
    r.analysis_type,
    r.execution_status

FROM anomaly_result a

JOIN analysis_run r
    ON r.run_id = a.run_id

ORDER BY ABS(a.anomaly_score) DESC;


-- ============================================================
-- 35. REPORTING: STORED FORECASTS
-- ============================================================

SELECT
    forecast_period,
    predicted_revenue,
    lower_bound,
    upper_bound

FROM forecast_result

ORDER BY forecast_period;


-- ============================================================
-- 36. DATA QUALITY VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_records,

    COUNT(*) FILTER (
        WHERE revenue < 0
    ) AS invalid_revenue,

    COUNT(*) FILTER (
        WHERE units < 0
    ) AS invalid_units,

    COUNT(*) FILTER (
        WHERE discount_percent NOT BETWEEN 0 AND 100
    ) AS invalid_discount,

    COUNT(*) FILTER (
        WHERE satisfaction_score NOT BETWEEN 0 AND 10
    ) AS invalid_satisfaction,

    COUNT(*) FILTER (
        WHERE marketing_spend < 0
    ) AS invalid_marketing

FROM fact_sales;


-- ============================================================
-- 37. TRANSACTION HANDLING
-- ============================================================

-- Demonstration of an isolated transaction.
-- A failure rolls back all operations within this block.

SAVEPOINT analytics_validation;

DO $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM powerbi_analytics.fact_sales
    ) THEN
        RAISE EXCEPTION
            'Fact table contains no sales records';
    END IF;

END;
$$;

RELEASE SAVEPOINT analytics_validation;


-- ============================================================
-- 38. FINAL VALIDATION
-- ============================================================

DO $$
DECLARE
    v_records BIGINT;
    v_months BIGINT;
BEGIN

    SELECT COUNT(*)
    INTO v_records
    FROM powerbi_analytics.fact_sales;

    SELECT COUNT(*)
    INTO v_months
    FROM powerbi_analytics.vw_monthly_revenue;

    IF v_records <> 600 THEN
        RAISE EXCEPTION
            'Expected 600 records; found %',
            v_records;
    END IF;

    IF v_months < 6 THEN
        RAISE EXCEPTION
            'Insufficient monthly aggregation results';
    END IF;

    RAISE NOTICE
        'Validation passed. Records: %, months: %',
        v_records,
        v_months;

END;
$$;


COMMIT;
