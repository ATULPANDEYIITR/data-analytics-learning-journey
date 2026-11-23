-- ============================================================
-- ADVANCED DAX: RELATIONAL ANALYTICS FOUNDATION
--
-- Topics:
-- 1. Row context
-- 2. Filter context
-- 3. Context transition
-- 4. CALCULATE
-- 5. Variables
-- 6. SUMX
-- 7. FILTER
-- 8. ADDCOLUMNS
-- 9. Relationship propagation
-- 10. Analytical reporting
--
-- PostgreSQL 15+
-- ============================================================


-- ============================================================
-- 1. SCHEMA
-- ============================================================

CREATE SCHEMA IF NOT EXISTS dax_lab;

SET search_path TO dax_lab, public;


-- ============================================================
-- 2. DIMENSION TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_region (
    region_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR(60) NOT NULL UNIQUE,
    region_group VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category_id INTEGER NOT NULL
        REFERENCES dim_category(category_id),
    unit_cost NUMERIC(14, 2) NOT NULL
        CHECK (unit_cost >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_name)
);


-- ============================================================
-- 3. FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INTEGER NOT NULL
        REFERENCES dim_product(product_id),
    region_id INTEGER NOT NULL
        REFERENCES dim_region(region_id),
    sale_date DATE NOT NULL,
    quantity NUMERIC(14, 2) NOT NULL
        CHECK (quantity >= 0),
    unit_price NUMERIC(14, 2) NOT NULL
        CHECK (unit_price >= 0),
    discount_rate NUMERIC(6, 4) NOT NULL DEFAULT 0
        CHECK (discount_rate >= 0 AND discount_rate <= 1),
    transaction_status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED'
        CHECK (
            transaction_status IN (
                'COMPLETED',
                'PENDING',
                'CANCELLED',
                'REFUNDED'
            )
        ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_date
    ON fact_sales(sale_date);

CREATE INDEX IF NOT EXISTS idx_sales_product
    ON fact_sales(product_id);

CREATE INDEX IF NOT EXISTS idx_sales_region
    ON fact_sales(region_id);

CREATE INDEX IF NOT EXISTS idx_sales_product_region
    ON fact_sales(product_id, region_id);

CREATE INDEX IF NOT EXISTS idx_sales_completed_date
    ON fact_sales(sale_date, product_id)
    WHERE transaction_status = 'COMPLETED';

CREATE INDEX IF NOT EXISTS idx_product_category
    ON dim_product(category_id);


-- ============================================================
-- 5. SAMPLE DIMENSION DATA
-- ============================================================

INSERT INTO dim_region(region_name, region_group)
VALUES
    ('North', 'Northern Zone'),
    ('South', 'Southern Zone'),
    ('West', 'Western Zone')
ON CONFLICT (region_name) DO NOTHING;


INSERT INTO dim_category(category_name)
VALUES
    ('Electronics'),
    ('Furniture'),
    ('Clothing')
ON CONFLICT (category_name) DO NOTHING;


INSERT INTO dim_product(
    product_id,
    product_name,
    category_id,
    unit_cost
)
SELECT
    source.product_id,
    source.product_name,
    category.category_id,
    source.unit_cost
FROM (
    VALUES
        (101, 'Laptop', 'Electronics', 350.00::NUMERIC),
        (102, 'Monitor', 'Electronics', 600.00::NUMERIC),
        (103, 'Desk', 'Furniture', 120.00::NUMERIC),
        (104, 'Chair', 'Furniture', 90.00::NUMERIC),
        (105, 'Shirt', 'Clothing', 40.00::NUMERIC)
) AS source(product_id, product_name, category_name, unit_cost)
JOIN dim_category category
    ON category.category_name = source.category_name
ON CONFLICT (product_id) DO NOTHING;


-- ============================================================
-- 6. SAMPLE TRANSACTIONAL DATA
-- ============================================================

INSERT INTO fact_sales(
    product_id,
    region_id,
    sale_date,
    quantity,
    unit_price,
    discount_rate,
    transaction_status
)
SELECT
    source.product_id,
    region.region_id,
    source.sale_date::DATE,
    source.quantity,
    source.unit_price,
    source.discount_rate,
    source.transaction_status
FROM (
    VALUES
        (101, 'North', '2026-11-01', 2.00, 500.00, 0.00, 'COMPLETED'),
        (102, 'South', '2026-11-02', 1.00, 800.00, 0.00, 'COMPLETED'),
        (103, 'North', '2026-11-03', 3.00, 200.00, 0.00, 'COMPLETED'),
        (101, 'West',  '2026-11-04', 1.00, 500.00, 0.00, 'COMPLETED'),
        (104, 'South', '2026-11-05', 4.00, 150.00, 0.00, 'COMPLETED'),
        (105, 'North', '2026-11-06', 5.00, 80.00, 0.00, 'COMPLETED'),
        (101, 'North', '2026-11-07', 1.00, 500.00, 0.10, 'PENDING'),
        (102, 'West',  '2026-11-08', 1.00, 800.00, 0.00, 'CANCELLED')
) AS source(
    product_id,
    region_name,
    sale_date,
    quantity,
    unit_price,
    discount_rate,
    transaction_status
)
JOIN dim_region region
    ON region.region_name = source.region_name
WHERE NOT EXISTS (
    SELECT 1
    FROM fact_sales existing
    WHERE existing.product_id = source.product_id
      AND existing.sale_date = source.sale_date::DATE
      AND existing.region_id = region.region_id
);


-- ============================================================
-- 7. VALIDATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_sale()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.quantity < 0 THEN
        RAISE EXCEPTION 'Quantity cannot be negative.';
    END IF;

    IF NEW.unit_price < 0 THEN
        RAISE EXCEPTION 'Unit price cannot be negative.';
    END IF;

    IF NEW.discount_rate < 0 OR NEW.discount_rate > 1 THEN
        RAISE EXCEPTION 'Discount must be between zero and one.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM dim_product
        WHERE product_id = NEW.product_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Product is missing or inactive.';
    END IF;

    RETURN NEW;
END;
$$;


DROP TRIGGER IF EXISTS trg_validate_sale ON fact_sales;

CREATE TRIGGER trg_validate_sale
BEFORE INSERT OR UPDATE ON fact_sales
FOR EACH ROW
EXECUTE FUNCTION validate_sale();


-- ============================================================
-- 8. FACT VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_sales_analytics AS
SELECT
    s.sale_id,
    s.sale_date,
    p.product_id,
    p.product_name,
    c.category_name,
    r.region_name,
    s.quantity,
    s.unit_price,
    s.discount_rate,
    s.transaction_status,

    ROUND(
        s.quantity * s.unit_price * (1 - s.discount_rate),
        2
    ) AS revenue,

    ROUND(
        s.quantity * p.unit_cost,
        2
    ) AS total_cost,

    ROUND(
        s.quantity * s.unit_price * (1 - s.discount_rate)
        - s.quantity * p.unit_cost,
        2
    ) AS profit

FROM fact_sales s
JOIN dim_product p
    ON p.product_id = s.product_id
JOIN dim_category c
    ON c.category_id = p.category_id
JOIN dim_region r
    ON r.region_id = s.region_id;


-- ============================================================
-- 9. BASE MEASURES
-- ============================================================

CREATE OR REPLACE VIEW v_base_measures AS
SELECT
    COUNT(*) AS transaction_count,
    COALESCE(SUM(revenue), 0) AS total_revenue,
    COALESCE(SUM(total_cost), 0) AS total_cost,
    COALESCE(SUM(profit), 0) AS total_profit,
    CASE
        WHEN SUM(revenue) IS NULL OR SUM(revenue) = 0
            THEN 0
        ELSE SUM(profit) / SUM(revenue)
    END AS profit_margin
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED';


-- ============================================================
-- 10. FILTER CONTEXT EQUIVALENT
-- ============================================================

-- Equivalent analytical operation:
-- CALCULATE([Total Revenue], Region[RegionName] = "North")

SELECT
    region_name,
    SUM(revenue) AS regional_revenue,
    SUM(profit) AS regional_profit
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED'
  AND region_name = 'North'
GROUP BY region_name;


-- Multiple filter conditions.

SELECT
    category_name,
    region_name,
    SUM(revenue) AS revenue
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED'
  AND category_name = 'Electronics'
  AND region_name = 'North'
GROUP BY category_name, region_name;


-- ============================================================
-- 11. ROW CONTEXT EQUIVALENT
-- ============================================================

-- SQL evaluates expressions against individual source rows.
-- This is conceptually similar to row-wise calculations,
-- but SQL does not implement DAX row context.

SELECT
    sale_id,
    product_name,
    quantity,
    unit_price,
    quantity * unit_price AS gross_row_revenue,
    revenue AS net_row_revenue,
    profit AS row_profit
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED'
ORDER BY sale_id;


-- ============================================================
-- 12. SUMX EQUIVALENT
-- ============================================================

-- DAX:
-- SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])

SELECT
    SUM(quantity * unit_price) AS iterated_gross_revenue
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED';


-- Net revenue with discount.

SELECT
    SUM(
        quantity * unit_price * (1 - discount_rate)
    ) AS iterated_net_revenue
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED';


-- ============================================================
-- 13. FILTER EQUIVALENT
-- ============================================================

-- DAX:
-- FILTER(Sales, Sales[Quantity] * Sales[UnitPrice] >= 500)

WITH filtered_sales AS (
    SELECT *
    FROM v_sales_analytics
    WHERE transaction_status = 'COMPLETED'
      AND quantity * unit_price >= 500
)
SELECT
    sale_id,
    product_name,
    region_name,
    revenue,
    profit
FROM filtered_sales
ORDER BY revenue DESC;


-- ============================================================
-- 14. ADDCOLUMNS EQUIVALENT
-- ============================================================

-- Product-level virtual table.
-- Each product receives an evaluated revenue expression.

SELECT
    p.product_id,
    p.product_name,
    c.category_name,

    COALESCE(
        SUM(
            CASE
                WHEN s.transaction_status = 'COMPLETED'
                THEN s.quantity * s.unit_price
                     * (1 - s.discount_rate)
                ELSE 0
            END
        ),
        0
    ) AS product_revenue,

    COALESCE(
        SUM(
            CASE
                WHEN s.transaction_status = 'COMPLETED'
                THEN s.profit
                ELSE 0
            END
        ),
        0
    ) AS product_profit

FROM dim_product p
JOIN dim_category c
    ON c.category_id = p.category_id
LEFT JOIN v_sales_analytics s
    ON s.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    c.category_name
ORDER BY product_revenue DESC;


-- ============================================================
-- 15. VARIABLES EQUIVALENT
-- ============================================================

-- DAX:
--
-- VAR Revenue = [Total Revenue]
-- VAR Cost = [Total Cost]
-- VAR Profit = Revenue - Cost
-- RETURN DIVIDE(Profit, Revenue, 0)

WITH metrics AS (
    SELECT
        SUM(revenue) AS revenue,
        SUM(total_cost) AS cost
    FROM v_sales_analytics
    WHERE transaction_status = 'COMPLETED'
),
calculated AS (
    SELECT
        revenue,
        cost,
        revenue - cost AS profit
    FROM metrics
)
SELECT
    revenue,
    cost,
    profit,
    CASE
        WHEN revenue = 0 THEN 0
        ELSE profit / revenue
    END AS profit_margin
FROM calculated;


-- ============================================================
-- 16. CONTEXT TRANSITION CONCEPT
-- ============================================================

-- DAX:
-- ADDCOLUMNS(
--     VALUES(Products[ProductID]),
--     "Product Revenue",
--     CALCULATE([Total Revenue])
-- )
--
-- The SQL equivalent explicitly groups by product and
-- joins transactional rows using the product relationship.

SELECT
    p.product_id,
    p.product_name,
    COALESCE(
        SUM(
            s.quantity * s.unit_price
            * (1 - s.discount_rate)
        ),
        0
    ) AS product_revenue
FROM dim_product p
LEFT JOIN fact_sales s
    ON s.product_id = p.product_id
   AND s.transaction_status = 'COMPLETED'
GROUP BY
    p.product_id,
    p.product_name
ORDER BY p.product_id;


-- ============================================================
-- 17. ADVANCED ITERATOR: AVERAGEX EQUIVALENT
-- ============================================================

-- Average revenue per transaction is not the same as
-- average product revenue across products.

WITH product_revenue AS (
    SELECT
        p.product_id,
        COALESCE(
            SUM(
                CASE
                    WHEN s.transaction_status = 'COMPLETED'
                    THEN s.quantity * s.unit_price
                         * (1 - s.discount_rate)
                    ELSE 0
                END
            ),
            0
        ) AS revenue
    FROM dim_product p
    LEFT JOIN fact_sales s
        ON s.product_id = p.product_id
    GROUP BY p.product_id
)
SELECT
    AVG(revenue) AS average_revenue_per_product
FROM product_revenue;


-- ============================================================
-- 18. REMOVEFILTERS / ALL EQUIVALENT
-- ============================================================

-- Compare each region with the total revenue across all regions.

WITH regional AS (
    SELECT
        region_name,
        SUM(revenue) AS regional_revenue
    FROM v_sales_analytics
    WHERE transaction_status = 'COMPLETED'
    GROUP BY region_name
),
overall AS (
    SELECT SUM(revenue) AS total_revenue
    FROM v_sales_analytics
    WHERE transaction_status = 'COMPLETED'
)
SELECT
    regional.region_name,
    regional.regional_revenue,
    overall.total_revenue,
    ROUND(
        100 * regional.regional_revenue
        / NULLIF(overall.total_revenue, 0),
        2
    ) AS contribution_percentage
FROM regional
CROSS JOIN overall
ORDER BY regional.regional_revenue DESC;


-- ============================================================
-- 19. WINDOW FUNCTIONS
-- ============================================================

-- Running revenue by region.
-- SQL window functions are useful for analytical calculations,
-- but they do not reproduce DAX context semantics.

SELECT
    region_name,
    sale_date,
    sale_id,
    revenue,

    SUM(revenue) OVER (
        PARTITION BY region_name
        ORDER BY sale_date, sale_id
        ROWS BETWEEN UNBOUNDED PRECEDING
                 AND CURRENT ROW
    ) AS running_regional_revenue

FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED'
ORDER BY region_name, sale_date, sale_id;


-- ============================================================
-- 20. AGGREGATION AND REPORTING
-- ============================================================

SELECT
    category_name,
    region_name,
    COUNT(*) AS transaction_count,
    SUM(revenue) AS revenue,
    SUM(total_cost) AS cost,
    SUM(profit) AS profit,
    ROUND(
        100 * SUM(profit) / NULLIF(SUM(revenue), 0),
        2
    ) AS margin_percentage
FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED'
GROUP BY GROUPING SETS (
    (category_name, region_name),
    (category_name),
    (region_name),
    ()
)
ORDER BY
    category_name NULLS LAST,
    region_name NULLS LAST;


-- ============================================================
-- 21. VALIDATION REPORT
-- ============================================================

CREATE OR REPLACE VIEW v_data_quality AS
SELECT
    COUNT(*) AS total_records,

    COUNT(*) FILTER (
        WHERE quantity < 0
    ) AS invalid_quantities,

    COUNT(*) FILTER (
        WHERE unit_price < 0
    ) AS invalid_prices,

    COUNT(*) FILTER (
        WHERE discount_rate < 0
           OR discount_rate > 1
    ) AS invalid_discounts,

    COUNT(*) FILTER (
        WHERE transaction_status = 'PENDING'
    ) AS pending_records,

    COUNT(*) FILTER (
        WHERE transaction_status = 'CANCELLED'
    ) AS cancelled_records

FROM fact_sales;


SELECT * FROM v_data_quality;


-- ============================================================
-- 22. ELIGIBILITY AND BUSINESS RULES
-- ============================================================

-- Identify products with positive revenue and profit.

WITH product_metrics AS (
    SELECT
        product_id,
        product_name,
        SUM(revenue) AS revenue,
        SUM(profit) AS profit
    FROM v_sales_analytics
    WHERE transaction_status = 'COMPLETED'
    GROUP BY product_id, product_name
)
SELECT
    *,
    CASE
        WHEN revenue > 0 AND profit > 0
            THEN 'PROFITABLE'
        WHEN revenue > 0 AND profit = 0
            THEN 'BREAK_EVEN'
        WHEN revenue > 0 AND profit < 0
            THEN 'LOSS_MAKING'
        ELSE 'NO_COMPLETED_SALES'
    END AS performance_status
FROM product_metrics
ORDER BY profit DESC;


-- ============================================================
-- 23. REUSABLE ANALYTICAL FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION regional_revenue(
    requested_region VARCHAR
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result NUMERIC;
BEGIN
    IF requested_region IS NULL
       OR BTRIM(requested_region) = '' THEN
        RAISE EXCEPTION 'Region is required.';
    END IF;

    SELECT COALESCE(SUM(revenue), 0)
    INTO result
    FROM v_sales_analytics
    WHERE region_name = requested_region
      AND transaction_status = 'COMPLETED';

    RETURN result;
END;
$$;


SELECT regional_revenue('North') AS north_revenue;


-- ============================================================
-- 24. TRANSACTIONAL WORKFLOW
-- ============================================================

BEGIN;

-- Example of a valid completed transaction.
INSERT INTO fact_sales(
    product_id,
    region_id,
    sale_date,
    quantity,
    unit_price,
    discount_rate,
    transaction_status
)
SELECT
    103,
    region_id,
    DATE '2026-11-09',
    2,
    200,
    0.05,
    'COMPLETED'
FROM dim_region
WHERE region_name = 'West';

-- Validate the transaction inside the same transaction.
SELECT
    sale_id,
    product_name,
    revenue,
    profit
FROM v_sales_analytics
WHERE sale_date = DATE '2026-11-09';

COMMIT;


-- ============================================================
-- 25. FAILURE CASE DEMONSTRATION
-- ============================================================

-- The following statement is intentionally invalid.
-- Run separately to observe the CHECK constraint failure.
--
-- INSERT INTO fact_sales(
--     product_id, region_id, sale_date,
--     quantity, unit_price, discount_rate
-- )
-- VALUES (
--     101, 1, CURRENT_DATE, -5, 500, 0
-- );


-- ============================================================
-- 26. FINAL ANALYTICAL DASHBOARD QUERY
-- ============================================================

SELECT
    region_name,
    category_name,

    COUNT(*) AS completed_transactions,

    ROUND(SUM(revenue), 2) AS revenue,

    ROUND(SUM(total_cost), 2) AS cost,

    ROUND(SUM(profit), 2) AS profit,

    ROUND(
        100 * SUM(profit) / NULLIF(SUM(revenue), 0),
        2
    ) AS profit_margin,

    ROUND(
        AVG(revenue),
        2
    ) AS average_transaction_value

FROM v_sales_analytics
WHERE transaction_status = 'COMPLETED'
GROUP BY region_name, category_name
ORDER BY revenue DESC;


-- ============================================================
-- 27. EXECUTION PLAN
-- ============================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT
    product_id,
    SUM(quantity * unit_price) AS revenue
FROM fact_sales
WHERE transaction_status = 'COMPLETED'
  AND sale_date >= DATE '2026-11-01'
GROUP BY product_id;


-- ============================================================
-- 28. FINAL VALIDATION
-- ============================================================

DO $$
DECLARE
    actual_revenue NUMERIC;
    actual_profit NUMERIC;
BEGIN
    SELECT
        SUM(revenue),
        SUM(profit)
    INTO
        actual_revenue,
        actual_profit
    FROM v_sales_analytics
    WHERE transaction_status = 'COMPLETED';

    IF actual_revenue <> 3350 THEN
        RAISE EXCEPTION
            'Revenue validation failed: %',
            actual_revenue;
    END IF;

    IF actual_profit <> 1160 THEN
        RAISE EXCEPTION
            'Profit validation failed: %',
            actual_profit;
    END IF;

    RAISE NOTICE
        'Analytical validation passed. Revenue: %, Profit: %',
        actual_revenue,
        actual_profit;
END;
$$;
