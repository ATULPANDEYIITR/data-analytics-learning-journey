DROP SCHEMA IF EXISTS sql_performance_lab CASCADE;

CREATE SCHEMA sql_performance_lab;

SET search_path TO sql_performance_lab;

-- SQL Performance Laboratory
--
-- PostgreSQL-compatible demonstration of:
--   sequential scans
--   index scans
--   filtering efficiency
--   composite indexes
--   partial indexes
--   covering indexes
--   join optimization
--   query-plan inspection
--   cardinality estimation
--
-- The dataset is intentionally large enough to make access-path choices
-- meaningful while remaining suitable for a laboratory environment.

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region TEXT NOT NULL,
    tier TEXT NOT NULL,
    created_at DATE NOT NULL,
    CONSTRAINT customers_region_ck
        CHECK (region IN ('North', 'South', 'East', 'West')),
    CONSTRAINT customers_tier_ck
        CHECK (tier IN ('standard', 'silver', 'gold', 'enterprise'))
);

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    CONSTRAINT products_category_ck
        CHECK (
            category IN (
                'hardware',
                'software',
                'networking',
                'security',
                'services'
            )
        ),
    CONSTRAINT products_price_ck
        CHECK (price > 0)
);

CREATE TABLE orders (
    order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status TEXT NOT NULL,
    total_amount NUMERIC(14,2) NOT NULL,
    CONSTRAINT orders_status_ck
        CHECK (
            status IN (
                'pending',
                'paid',
                'shipped',
                'cancelled',
                'refunded'
            )
        ),
    CONSTRAINT orders_amount_ck
        CHECK (total_amount > 0)
);

CREATE TABLE order_items (
    order_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL
        REFERENCES orders(order_id)
        ON DELETE CASCADE,
    product_id BIGINT NOT NULL
        REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    CONSTRAINT order_items_quantity_ck
        CHECK (quantity > 0),
    CONSTRAINT order_items_order_product_uq
        UNIQUE (order_id, product_id)
);

-- -------------------------------------------------------------------------
-- Representative data
-- -------------------------------------------------------------------------

INSERT INTO customers (
    region,
    tier,
    created_at
)
SELECT
    (
        ARRAY[
            'North',
            'South',
            'East',
            'West'
        ]
    )[1 + ((g - 1) % 4)],
    (
        ARRAY[
            'standard',
            'silver',
            'gold',
            'enterprise'
        ]
    )[CASE
        WHEN g % 20 = 0 THEN 4
        WHEN g % 5 = 0 THEN 3
        WHEN g % 2 = 0 THEN 2
        ELSE 1
    END],
    DATE '2024-01-01' + ((g * 7) % 900)
FROM generate_series(1, 10000) AS g;

INSERT INTO products (
    category,
    price
)
SELECT
    (
        ARRAY[
            'hardware',
            'software',
            'networking',
            'security',
            'services'
        ]
    )[1 + ((g * 7) % 5)],
    round(
        (
            15 +
            ((g * 137) % 498500) / 100.0
        )::numeric,
        2
    )
FROM generate_series(1, 2000) AS g;

INSERT INTO orders (
    customer_id,
    order_date,
    status,
    total_amount
)
SELECT
    1 + ((g * 7919) % 10000),
    DATE '2026-01-01' + ((g * 17) % 273),
    CASE
        WHEN g % 20 = 0 THEN 'pending'
        WHEN g % 20 IN (1,2,3,4,5,6,7) THEN 'paid'
        WHEN g % 20 IN (8,9,10,11,12,13,14,15,16) THEN 'shipped'
        WHEN g % 20 IN (17,18) THEN 'cancelled'
        ELSE 'refunded'
    END,
    round(
        (
            10 +
            ((g * 7919) % 2499000) / 100.0
        )::numeric,
        2
    )
FROM generate_series(1, 100000) AS g;

INSERT INTO order_items (
    order_id,
    product_id,
    quantity
)
SELECT
    order_id,
    1 + ((order_id * item_number * 31) % 2000),
    1 + ((order_id + item_number) % 4)
FROM orders
CROSS JOIN generate_series(1, 3) AS item_number
WHERE (order_id + item_number) % 7 <> 0;

-- -------------------------------------------------------------------------
-- Baseline: sequential scan
-- -------------------------------------------------------------------------
--
-- The query intentionally has no supporting index on status at this point.
-- PostgreSQL may choose a sequential scan because status has low cardinality.
-- The plan should be inspected rather than assumed.

EXPLAIN
SELECT order_id,
       customer_id,
       order_date,
       total_amount
FROM orders
WHERE status = 'cancelled';

-- -------------------------------------------------------------------------
-- Primary selective index
-- -------------------------------------------------------------------------
--
-- Equality lookup on customer_id is much more selective than a low-cardinality
-- status predicate.

CREATE INDEX idx_orders_customer
    ON orders (customer_id);

ANALYZE orders;

EXPLAIN (ANALYZE, BUFFERS)
SELECT order_id,
       customer_id,
       order_date,
       status,
       total_amount
FROM orders
WHERE customer_id = 731;

-- -------------------------------------------------------------------------
-- Composite index
-- -------------------------------------------------------------------------
--
-- The key order is intentional:
--   customer_id equality
--   order_date range
--
-- This supports queries that first identify a customer and then restrict the
-- customer's orders to a date interval.

CREATE INDEX idx_orders_customer_date
    ON orders (customer_id, order_date);

ANALYZE orders;

EXPLAIN (ANALYZE, BUFFERS)
SELECT order_id,
       customer_id,
       order_date,
       total_amount
FROM orders
WHERE customer_id = 731
  AND order_date >= DATE '2026-09-01'
  AND order_date < DATE '2026-10-01';

-- The reverse key order is not automatically equivalent. This query is useful
-- for discussing how composite B-tree indexes depend on leading columns.

EXPLAIN
SELECT order_id,
       customer_id,
       order_date
FROM orders
WHERE order_date >= DATE '2026-09-01'
  AND order_date < DATE '2026-10-01';

-- -------------------------------------------------------------------------
-- Filtering efficiency
-- -------------------------------------------------------------------------
--
-- The range predicate exposes a direct ordering relationship on order_date.
-- Applying a function to the indexed column can change the access-path
-- possibilities.

EXPLAIN
SELECT count(*)
FROM orders
WHERE order_date >= DATE '2026-09-01'
  AND order_date < DATE '2026-10-01';

EXPLAIN
SELECT count(*)
FROM orders
WHERE date_trunc('month', order_date) = TIMESTAMP '2026-09-01';

-- A function-based expression index can be appropriate when the expression
-- itself is a stable and common access pattern.

CREATE INDEX idx_orders_month_expression
    ON orders ((date_trunc('month', order_date)));

ANALYZE orders;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM orders
WHERE date_trunc('month', order_date) = TIMESTAMP '2026-09-01';

-- -------------------------------------------------------------------------
-- Partial index
-- -------------------------------------------------------------------------
--
-- This index contains only paid orders. It is smaller than an equivalent
-- unrestricted index and is useful for queries whose predicates imply
-- status='paid'.

CREATE INDEX idx_orders_paid_customer
    ON orders (customer_id, order_date)
    WHERE status = 'paid';

ANALYZE orders;

EXPLAIN (ANALYZE, BUFFERS)
SELECT order_id,
       customer_id,
       order_date,
       total_amount
FROM orders
WHERE status = 'paid'
  AND customer_id = 731
  AND order_date >= DATE '2026-09-01';

-- The partial index does not represent cancelled rows.

EXPLAIN
SELECT order_id,
       customer_id,
       order_date
FROM orders
WHERE status = 'cancelled'
  AND customer_id = 731
  AND order_date >= DATE '2026-09-01';

-- -------------------------------------------------------------------------
-- Covering index and index-only scan
-- -------------------------------------------------------------------------
--
-- INCLUDE columns are payload rather than search keys. They can allow
-- PostgreSQL to satisfy projections from the index when visibility-map
-- conditions permit an index-only scan.

CREATE INDEX idx_orders_customer_covering
    ON orders (customer_id)
    INCLUDE (order_date, total_amount);

ANALYZE orders;

EXPLAIN (ANALYZE, BUFFERS)
SELECT customer_id,
       order_date,
       total_amount
FROM orders
WHERE customer_id = 731;

-- -------------------------------------------------------------------------
-- Join optimization
-- -------------------------------------------------------------------------
--
-- Joining orders to customers on a foreign key is a realistic access pattern.
-- The customer table is comparatively small, while orders is larger.

EXPLAIN (ANALYZE, BUFFERS)
SELECT c.customer_id,
       c.region,
       o.order_id,
       o.order_date,
       o.total_amount
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
WHERE c.region = 'West'
  AND o.order_date >= DATE '2026-09-01';

-- Filtering the driving relation can reduce join work.

EXPLAIN (ANALYZE, BUFFERS)
SELECT c.region,
       count(*) AS order_count,
       sum(o.total_amount) AS revenue
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
WHERE c.region = 'West'
  AND o.status = 'shipped'
GROUP BY c.region;

-- -------------------------------------------------------------------------
-- Join cardinality and aggregation
-- -------------------------------------------------------------------------

EXPLAIN (ANALYZE, BUFFERS)
SELECT c.tier,
       o.status,
       count(*) AS orders,
       sum(o.total_amount) AS revenue
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
WHERE o.order_date >= DATE '2026-07-01'
  AND o.order_date < DATE '2026-10-01'
GROUP BY c.tier, o.status
ORDER BY c.tier, o.status;

-- -------------------------------------------------------------------------
-- Explicit join-strategy experiments
-- -------------------------------------------------------------------------
--
-- These settings are diagnostic tools, not recommendations for permanent
-- production configuration. They let an engineer compare candidate plans.

SET LOCAL enable_nestloop = off;

EXPLAIN
SELECT c.customer_id,
       o.order_id
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
WHERE c.region = 'South';

RESET enable_nestloop;

SET LOCAL enable_hashjoin = off;

EXPLAIN
SELECT c.customer_id,
       o.order_id
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
WHERE c.region = 'South';

RESET enable_hashjoin;

-- -------------------------------------------------------------------------
-- CTE and filtering-before-join example
-- -------------------------------------------------------------------------
--
-- The filtered_orders CTE makes the logical intent explicit. Modern
-- PostgreSQL can inline eligible CTEs, so the presence of a CTE does not
-- automatically imply materialization or poor performance.

EXPLAIN (ANALYZE, BUFFERS)
WITH filtered_orders AS (
    SELECT order_id,
           customer_id,
           order_date,
           total_amount
    FROM orders
    WHERE order_date >= DATE '2026-09-01'
      AND order_date < DATE '2026-10-01'
      AND status = 'paid'
)
SELECT c.region,
       count(*) AS paid_orders,
       sum(f.total_amount) AS revenue
FROM filtered_orders AS f
JOIN customers AS c
  ON c.customer_id = f.customer_id
GROUP BY c.region
ORDER BY revenue DESC;

-- -------------------------------------------------------------------------
-- Index usage inspection
-- -------------------------------------------------------------------------
--
-- pg_stat_user_indexes provides cumulative usage information. Counters depend
-- on server activity and reset events, so they should be interpreted as
-- operational telemetry rather than a single-query proof.

SELECT
    indexrelname AS index_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'sql_performance_lab'
ORDER BY idx_scan DESC, indexrelname;

-- -------------------------------------------------------------------------
-- Selectivity analysis
-- -------------------------------------------------------------------------

SELECT
    status,
    count(*) AS row_count,
    round(
        count(*) * 100.0 /
        (SELECT count(*) FROM orders),
        2
    ) AS percentage_of_table
FROM orders
GROUP BY status
ORDER BY row_count DESC;

SELECT
    customer_id,
    count(*) AS order_count
FROM orders
GROUP BY customer_id
ORDER BY order_count DESC
LIMIT 10;

-- These queries expose why a low-cardinality column and a high-cardinality
-- column can produce very different index economics.

-- -------------------------------------------------------------------------
-- Estimated versus actual cardinality
-- -------------------------------------------------------------------------

EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT *
FROM orders
WHERE customer_id = 731
  AND status = 'paid'
  AND order_date >= DATE '2026-09-01';

-- A significant difference between estimated rows and actual rows can point
-- toward stale statistics, skew, correlated predicates, or insufficient
-- statistics detail.

-- -------------------------------------------------------------------------
-- Statistics maintenance
-- -------------------------------------------------------------------------

ANALYZE customers;
ANALYZE products;
ANALYZE orders;
ANALYZE order_items;

-- -------------------------------------------------------------------------
-- Constraint-driven data integrity
-- -------------------------------------------------------------------------
--
-- This transaction demonstrates that database constraints belong to the
-- integrity layer, not just application validation.

BEGIN;

INSERT INTO customers (
    region,
    tier,
    created_at
)
VALUES (
    'North',
    'gold',
    CURRENT_DATE
)
RETURNING customer_id;

ROLLBACK;

-- The following statement is intentionally commented out because executing it
-- would fail the positive-amount CHECK constraint.
--
-- INSERT INTO orders (
--     customer_id,
--     order_date,
--     status,
--     total_amount
-- )
-- VALUES (
--     731,
--     CURRENT_DATE,
--     'paid',
--     -100
-- );

-- -------------------------------------------------------------------------
-- Query patterns that should be validated with execution plans
-- -------------------------------------------------------------------------

EXPLAIN (ANALYZE, BUFFERS)
SELECT o.customer_id,
       sum(o.total_amount) AS revenue
FROM orders AS o
WHERE o.status = 'paid'
  AND o.order_date >= DATE '2026-09-01'
  AND o.order_date < DATE '2026-10-01'
GROUP BY o.customer_id
HAVING sum(o.total_amount) > 10000
ORDER BY revenue DESC;

EXPLAIN (ANALYZE, BUFFERS)
SELECT p.category,
       sum(oi.quantity) AS units,
       sum(oi.quantity * p.price) AS gross_value
FROM order_items AS oi
JOIN products AS p
  ON p.product_id = oi.product_id
JOIN orders AS o
  ON o.order_id = oi.order_id
WHERE o.order_date >= DATE '2026-09-01'
  AND o.order_date < DATE '2026-10-01'
GROUP BY p.category
ORDER BY gross_value DESC;

-- -------------------------------------------------------------------------
-- Performance interpretation notes
-- -------------------------------------------------------------------------
--
-- Sequential scans:
--   Appropriate when a large fraction of the table is needed, the relation
--   is small, or an index cannot reduce enough work.
--
-- Index scans:
--   Useful for selective predicates and ordered access. They can still incur
--   heap access for projected columns not available from the index.
--
-- Filtering efficiency:
--   A good access path minimizes rows read and carried into later operators.
--   Predicate shape, selectivity, and expression use affect this behavior.
--
-- Join optimization:
--   Nested loops, indexed nested loops, hash joins, and merge joins have
--   different cost characteristics. The planner chooses according to its
--   estimates and cost model.
--
-- Index design:
--   Every index has storage and write-maintenance cost. Composite indexes
--   must be designed around real predicate and ordering patterns.
--
-- Production validation:
--   EXPLAIN (ANALYZE, BUFFERS) is the authoritative way to compare the
--   estimated plan with actual execution for a specific PostgreSQL workload.
