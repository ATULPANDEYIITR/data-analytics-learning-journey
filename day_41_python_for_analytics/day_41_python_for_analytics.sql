-- Python for Analytics: PostgreSQL relational model for operational sales.
-- The schema demonstrates typed values, arithmetic expressions, data
-- validation, missing-data representation, aggregation, and analytical output.

BEGIN;

DROP VIEW IF EXISTS regional_sales_summary;
DROP TABLE IF EXISTS sales_transaction;
DROP TABLE IF EXISTS sales_region;

CREATE TABLE sales_region (
    region_code VARCHAR(12) PRIMARY KEY,
    region_name VARCHAR(80) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE sales_transaction (
    transaction_id VARCHAR(30) PRIMARY KEY,
    region_code VARCHAR(12) NOT NULL
        REFERENCES sales_region(region_code),
    transaction_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14, 2) NOT NULL CHECK (unit_price >= 0),
    -- A generated column prevents application code from storing a
    -- sales amount inconsistent with quantity and unit price.
    sales_amount NUMERIC(18, 2)
        GENERATED ALWAYS AS (quantity * unit_price) STORED,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_transaction_region_date
    ON sales_transaction(region_code, transaction_date);

CREATE INDEX idx_sales_transaction_date
    ON sales_transaction(transaction_date);

INSERT INTO sales_region (region_code, region_name) VALUES
    ('NORTH', 'North'),
    ('SOUTH', 'South'),
    ('EAST', 'East'),
    ('WEST', 'West');

INSERT INTO sales_transaction (
    transaction_id,
    region_code,
    transaction_date,
    quantity,
    unit_price,
    notes
) VALUES
    ('TX-1001', 'NORTH', DATE '2026-09-01', 12, 1499.50, 'Retail order'),
    ('TX-1002', 'SOUTH', DATE '2026-09-02', 8, 2200.00, 'Enterprise order'),
    ('TX-1003', 'NORTH', DATE '2026-09-03', 5, 999.00, NULL),
    ('TX-1004', 'EAST', DATE '2026-09-04', 3, 750.00, 'Online order'),
    ('TX-1005', 'WEST', DATE '2026-09-05', 4, 100.00, 'Outlet order');

-- Inspect the stored values and generated arithmetic expression.
SELECT
    transaction_id,
    region_code,
    quantity,
    unit_price,
    sales_amount,
    quantity * unit_price AS independently_calculated_amount
FROM sales_transaction
ORDER BY transaction_id;

-- A NULL note means unknown or unrecorded descriptive information.
-- It does not mean an empty string or a zero monetary amount.
SELECT
    transaction_id,
    notes,
    notes IS NULL AS note_is_missing
FROM sales_transaction
ORDER BY transaction_id;

-- Aggregate at the regional level. COALESCE provides a numeric result
-- for regions that have no matching transactions.
CREATE VIEW regional_sales_summary AS
SELECT
    r.region_code,
    r.region_name,
    COUNT(t.transaction_id) AS transaction_count,
    COALESCE(SUM(t.quantity), 0) AS units_sold,
    COALESCE(SUM(t.sales_amount), 0.00)::NUMERIC(18, 2) AS total_sales,
    ROUND(AVG(t.sales_amount), 2) AS average_transaction_value
FROM sales_region AS r
LEFT JOIN sales_transaction AS t
    ON t.region_code = r.region_code
GROUP BY r.region_code, r.region_name;

SELECT *
FROM regional_sales_summary
ORDER BY total_sales DESC, region_name;

-- CTEs expose the calculation steps for revenue share and regional ranking.
WITH regional_totals AS (
    SELECT
        region_code,
        region_name,
        total_sales
    FROM regional_sales_summary
),
grand_total AS (
    SELECT COALESCE(SUM(total_sales), 0.00) AS total_sales
    FROM regional_totals
)
SELECT
    rt.region_name,
    rt.total_sales,
    CASE
        WHEN gt.total_sales = 0 THEN NULL
        ELSE ROUND(rt.total_sales / gt.total_sales * 100, 2)
    END AS revenue_share_percent,
    DENSE_RANK() OVER (ORDER BY rt.total_sales DESC) AS sales_rank
FROM regional_totals AS rt
CROSS JOIN grand_total AS gt
ORDER BY sales_rank, rt.region_name;

-- Calculate monthly performance. The baseline is explicitly represented
-- by a CTE, and NULLIF protects the percentage calculation from zero.
WITH current_period AS (
    SELECT COALESCE(SUM(sales_amount), 0.00) AS revenue
    FROM sales_transaction
    WHERE transaction_date >= DATE '2026-09-01'
      AND transaction_date < DATE '2026-10-01'
),
previous_period AS (
    SELECT 0.00::NUMERIC AS revenue
)
SELECT
    current_period.revenue AS current_revenue,
    previous_period.revenue AS previous_revenue,
    CASE
        WHEN previous_period.revenue = 0 THEN NULL
        ELSE ROUND(
            (current_period.revenue - previous_period.revenue)
            / NULLIF(previous_period.revenue, 0) * 100,
            2
        )
    END AS growth_percent
FROM current_period
CROSS JOIN previous_period;

-- Data-quality checks reveal potential issues before a report is published.
SELECT
    COUNT(*) AS transaction_count,
    COUNT(*) FILTER (WHERE transaction_id IS NULL) AS missing_ids,
    COUNT(*) FILTER (WHERE quantity <= 0) AS invalid_quantities,
    COUNT(*) FILTER (WHERE unit_price < 0) AS invalid_prices,
    COUNT(*) FILTER (WHERE notes IS NULL) AS missing_notes
FROM sales_transaction;

-- The constraints above reject invalid quantities, negative prices,
-- unknown regions, and duplicate transaction IDs. The following
-- savepoint demonstrates rejection without aborting the full transaction.
SAVEPOINT invalid_record_test;

DO $$
BEGIN
    BEGIN
        INSERT INTO sales_transaction (
            transaction_id,
            region_code,
            transaction_date,
            quantity,
            unit_price
        ) VALUES (
            'TX-INVALID',
            'NORTH',
            DATE '2026-09-10',
            0,
            100.00
        );
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid quantity rejected by database constraint';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_record_test;
RELEASE SAVEPOINT invalid_record_test;

-- Demonstrate a transactional insert. The transaction either commits all
-- its changes or can be rolled back as a unit.
SAVEPOINT valid_insert_test;

INSERT INTO sales_transaction (
    transaction_id,
    region_code,
    transaction_date,
    quantity,
    unit_price,
    notes
) VALUES (
    'TX-1006',
    'SOUTH',
    DATE '2026-09-06',
    2,
    1250.00,
    'Validated sample transaction'
);

SELECT transaction_id, sales_amount
FROM sales_transaction
WHERE transaction_id = 'TX-1006';

ROLLBACK TO SAVEPOINT valid_insert_test;
RELEASE SAVEPOINT valid_insert_test;

-- Final integrity and aggregation checks use the committed sample dataset.
SELECT
    COUNT(*) AS committed_transactions,
    SUM(quantity) AS committed_units,
    SUM(sales_amount) AS committed_sales
FROM sales_transaction;

COMMIT;
