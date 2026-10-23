DROP SCHEMA IF EXISTS pandas_grouping_demo CASCADE;
CREATE SCHEMA pandas_grouping_demo;
SET search_path TO pandas_grouping_demo;

-- The relational model separates raw transaction facts from derived
-- analytical structures. PostgreSQL performs the same conceptual work
-- as groupby, aggregation, transform, pivot_table, and crosstab.

CREATE TYPE sales_region AS ENUM ('North', 'South', 'East', 'West');
CREATE TYPE sales_department AS ENUM ('Cloud', 'Security', 'Data');
CREATE TYPE sales_channel AS ENUM ('Online', 'Partner', 'Direct');
CREATE TYPE customer_segment AS ENUM ('Enterprise', 'SMB');

CREATE TABLE orders (
    order_id          integer PRIMARY KEY,
    order_date        date NOT NULL,
    region            sales_region NOT NULL,
    department        sales_department NOT NULL,
    channel           sales_channel NOT NULL,
    product           text NOT NULL,
    customer_segment  customer_segment NOT NULL,
    units             integer NOT NULL CHECK (units > 0),
    unit_price        numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    discount          numeric(5,4) NOT NULL CHECK (discount BETWEEN 0 AND 1),
    returned          boolean NOT NULL DEFAULT false
);

CREATE INDEX idx_orders_region_department
    ON orders (region, department);

CREATE INDEX idx_orders_channel
    ON orders (channel);

CREATE INDEX idx_orders_order_date
    ON orders (order_date);

CREATE TABLE grouping_audit (
    audit_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    operation_name text NOT NULL,
    executed_at    timestamptz NOT NULL DEFAULT clock_timestamp(),
    row_count      bigint NOT NULL CHECK (row_count >= 0)
);

CREATE OR REPLACE FUNCTION audit_grouping_operation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO grouping_audit (operation_name, row_count)
    VALUES ('order_insert', 1);

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_order_insert_audit
AFTER INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION audit_grouping_operation();

INSERT INTO orders (
    order_id, order_date, region, department, channel,
    product, customer_segment, units, unit_price, discount, returned
)
VALUES
(1001, '2026-01-05', 'North', 'Cloud', 'Online', 'Compute', 'Enterprise', 8, 1200, 0.05, false),
(1002, '2026-01-07', 'North', 'Security', 'Partner', 'Firewall', 'Enterprise', 4, 2100, 0.00, false),
(1003, '2026-01-09', 'South', 'Cloud', 'Online', 'Storage', 'SMB', 15, 400, 0.10, false),
(1004, '2026-01-11', 'West', 'Data', 'Direct', 'Analytics', 'Enterprise', 6, 1800, 0.05, false),
(1005, '2026-01-13', 'East', 'Security', 'Online', 'Identity', 'SMB', 20, 250, 0.00, true),
(1006, '2026-01-15', 'North', 'Data', 'Partner', 'Analytics', 'SMB', 5, 1800, 0.15, false),
(1007, '2026-01-18', 'South', 'Security', 'Direct', 'Firewall', 'Enterprise', 3, 2100, 0.05, false),
(1008, '2026-01-20', 'West', 'Cloud', 'Online', 'Compute', 'SMB', 12, 1200, 0.00, false),
(1009, '2026-01-22', 'East', 'Data', 'Direct', 'Analytics', 'Enterprise', 7, 1800, 0.10, false),
(1010, '2026-01-25', 'North', 'Cloud', 'Partner', 'Storage', 'SMB', 30, 400, 0.05, false),
(1011, '2026-02-02', 'South', 'Cloud', 'Online', 'Compute', 'Enterprise', 5, 1200, 0.00, false),
(1012, '2026-02-04', 'West', 'Security', 'Partner', 'Identity', 'SMB', 18, 250, 0.10, true),
(1013, '2026-02-06', 'East', 'Cloud', 'Direct', 'Storage', 'SMB', 22, 400, 0.05, false),
(1014, '2026-02-08', 'North', 'Data', 'Online', 'Analytics', 'Enterprise', 4, 1800, 0.00, false),
(1015, '2026-02-11', 'South', 'Security', 'Online', 'Firewall', 'SMB', 9, 2100, 0.15, false),
(1016, '2026-02-14', 'West', 'Cloud', 'Direct', 'Compute', 'Enterprise', 10, 1200, 0.05, false),
(1017, '2026-02-17', 'East', 'Security', 'Partner', 'Identity', 'Enterprise', 11, 250, 0.00, false),
(1018, '2026-02-20', 'North', 'Data', 'Direct', 'Analytics', 'SMB', 8, 1800, 0.10, true);

CREATE OR REPLACE VIEW order_metrics AS
SELECT
    o.*,
    o.units * o.unit_price AS gross_revenue,
    o.units * o.unit_price * (1 - o.discount) AS net_revenue,
    CASE
        WHEN o.units * o.unit_price * (1 - o.discount) >= 5000
        THEN true
        ELSE false
    END AS high_value_order
FROM orders AS o;

-- groupby + aggregation: one result row per region.
SELECT
    region,
    count(*) AS orders,
    sum(units) AS units,
    sum(net_revenue) AS net_revenue,
    count(*) FILTER (WHERE returned) AS returned_orders,
    round(
        count(*) FILTER (WHERE returned)::numeric / NULLIF(count(*), 0),
        4
    ) AS return_rate
FROM order_metrics
GROUP BY region
ORDER BY net_revenue DESC;

-- Multiple grouping keys model a hierarchical groupby.
SELECT
    region,
    department,
    count(*) AS orders,
    sum(units) AS units,
    sum(net_revenue) AS net_revenue,
    round(avg(net_revenue), 2) AS average_order_value
FROM order_metrics
GROUP BY region, department
ORDER BY region, net_revenue DESC;

-- Multiple aggregation functions describe the distribution within
-- each department rather than returning individual transactions.
SELECT
    department,
    count(*) AS orders,
    sum(units) AS total_units,
    round(avg(net_revenue), 2) AS mean_revenue,
    round(percentile_cont(0.5) WITHIN GROUP (ORDER BY net_revenue), 2)
        AS median_revenue,
    min(net_revenue) AS minimum_revenue,
    max(net_revenue) AS maximum_revenue
FROM order_metrics
GROUP BY department
ORDER BY mean_revenue DESC;

-- transform semantics: the window SUM preserves every source row while
-- attaching the aggregate for its region.
SELECT
    order_id,
    region,
    net_revenue,
    sum(net_revenue) OVER (PARTITION BY region) AS region_revenue,
    round(
        net_revenue
        / NULLIF(sum(net_revenue) OVER (PARTITION BY region), 0),
        4
    ) AS region_revenue_share
FROM order_metrics
ORDER BY region, order_id;

-- Another transform-style calculation: department average remains
-- available on every transaction row.
SELECT
    order_id,
    department,
    net_revenue,
    round(
        avg(net_revenue) OVER (PARTITION BY department),
        2
    ) AS department_average,
    net_revenue >
        avg(net_revenue) OVER (PARTITION BY department)
        AS above_department_average
FROM order_metrics
ORDER BY department, order_id;

-- pivot_table semantics can be expressed with FILTER aggregates.
SELECT
    region,
    round(sum(net_revenue) FILTER (WHERE channel = 'Online'), 2)
        AS online_revenue,
    round(sum(net_revenue) FILTER (WHERE channel = 'Partner'), 2)
        AS partner_revenue,
    round(sum(net_revenue) FILTER (WHERE channel = 'Direct'), 2)
        AS direct_revenue,
    round(sum(net_revenue), 2) AS region_total
FROM order_metrics
GROUP BY region
ORDER BY region;

-- A more dynamic pivot is represented as grouped rows rather than
-- hard-coded columns, preserving arbitrary channel values.
SELECT
    region,
    channel,
    round(sum(net_revenue), 2) AS net_revenue
FROM order_metrics
GROUP BY region, channel
ORDER BY region, channel;

-- crosstab semantics: count categorical combinations.
SELECT
    department,
    count(*) FILTER (WHERE channel = 'Online') AS online_orders,
    count(*) FILTER (WHERE channel = 'Partner') AS partner_orders,
    count(*) FILTER (WHERE channel = 'Direct') AS direct_orders,
    count(*) AS total_orders
FROM order_metrics
GROUP BY department
ORDER BY department;

-- Conditional grouping: only high-value transactions enter the group.
SELECT
    region,
    count(*) AS high_value_orders,
    round(sum(net_revenue), 2) AS high_value_revenue
FROM order_metrics
WHERE high_value_order
GROUP BY region
ORDER BY high_value_revenue DESC;

-- HAVING filters complete groups after aggregation. This is distinct
-- from WHERE, which filters source rows before grouping.
SELECT
    region,
    count(*) AS orders,
    round(sum(net_revenue), 2) AS net_revenue
FROM order_metrics
GROUP BY region
HAVING sum(net_revenue) >= 9000
ORDER BY net_revenue DESC;

-- CTE workflow: compute regional metrics once, then rank the groups.
WITH regional AS (
    SELECT
        region,
        count(*) AS orders,
        sum(net_revenue) AS revenue
    FROM order_metrics
    GROUP BY region
),
ranked AS (
    SELECT
        regional.*,
        rank() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM regional
)
SELECT
    region,
    orders,
    round(revenue, 2) AS revenue,
    revenue_rank
FROM ranked
ORDER BY revenue_rank, region;

-- Validate that aggregation preserves the total measure.
WITH source_total AS (
    SELECT sum(net_revenue) AS total
    FROM order_metrics
),
grouped_total AS (
    SELECT sum(region_revenue) AS total
    FROM (
        SELECT
            region,
            sum(net_revenue) AS region_revenue
        FROM order_metrics
        GROUP BY region
    ) AS grouped
)
SELECT
    source_total.total AS source_total,
    grouped_total.total AS grouped_total,
    source_total.total = grouped_total.total AS reconciled
FROM source_total
CROSS JOIN grouped_total;

-- Transactional example: an intentionally invalid row is rejected by
-- the CHECK constraint, while the savepoint keeps the transaction usable.
BEGIN;

SAVEPOINT before_invalid_order;

INSERT INTO orders (
    order_id, order_date, region, department, channel,
    product, customer_segment, units, unit_price, discount, returned
)
VALUES (
    9001, CURRENT_DATE, 'North', 'Cloud', 'Online',
    'Validation-Test', 'SMB', 5, 100, 1.50, false
);

ROLLBACK TO SAVEPOINT before_invalid_order;

-- The transaction remains valid after the failed business operation.
INSERT INTO orders (
    order_id, order_date, region, department, channel,
    product, customer_segment, units, unit_price, discount, returned
)
VALUES (
    9002, CURRENT_DATE, 'South', 'Cloud', 'Online',
    'Valid-Test', 'SMB', 2, 100, 0.10, false
);

COMMIT;

-- The committed row participates in subsequent grouping operations.
SELECT
    region,
    count(*) AS orders,
    round(sum(net_revenue), 2) AS net_revenue
FROM order_metrics
WHERE order_id = 9002
GROUP BY region;

-- The trigger records DML activity, which is useful when analytical
-- pipelines need a basic operational audit trail.
SELECT
    operation_name,
    count(*) AS events
FROM grouping_audit
GROUP BY operation_name
ORDER BY operation_name;

-- Explain the planner's access strategy for a realistic grouped filter.
EXPLAIN
SELECT
    region,
    department,
    sum(net_revenue)
FROM order_metrics
WHERE order_date >= DATE '2026-01-01'
GROUP BY region, department;
