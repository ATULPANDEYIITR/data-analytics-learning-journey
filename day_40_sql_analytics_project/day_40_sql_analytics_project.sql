-- PostgreSQL Business Analytics Project
-- End-to-end relational model with analytical queries.
--
-- The script is intentionally self-contained. It creates a dedicated schema,
-- loads a realistic retail dataset, enforces business rules through constraints,
-- creates indexes and analytical views, and answers more than 40 business questions.

DROP SCHEMA IF EXISTS business_analytics CASCADE;
CREATE SCHEMA business_analytics;
SET search_path TO business_analytics;

CREATE TABLE regions (
    region_id BIGSERIAL PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id BIGSERIAL PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (
        segment IN ('Consumer', 'Corporate', 'Small Business')
    ),
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    signup_date DATE NOT NULL
);

CREATE TABLE sales_reps (
    sales_rep_id BIGSERIAL PRIMARY KEY,
    rep_name TEXT NOT NULL,
    region_id BIGINT NOT NULL REFERENCES regions(region_id)
);

CREATE TABLE products (
    product_id BIGSERIAL PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category_id BIGINT NOT NULL REFERENCES categories(category_id),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price > 0),
    unit_cost NUMERIC(12,2) NOT NULL
        CHECK (unit_cost >= 0 AND unit_cost <= unit_price)
);

CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    sales_rep_id BIGINT NOT NULL REFERENCES sales_reps(sales_rep_id),
    order_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('Completed', 'Cancelled', 'Returned', 'Pending')
    ),
    discount_rate NUMERIC(5,4) NOT NULL DEFAULT 0
        CHECK (discount_rate BETWEEN 0 AND 1)
);

CREATE TABLE order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price > 0),
    unit_cost NUMERIC(12,2) NOT NULL
        CHECK (unit_cost >= 0 AND unit_cost <= unit_price),
    UNIQUE (order_id, product_id)
);

CREATE INDEX idx_orders_date
    ON orders(order_date);

CREATE INDEX idx_orders_customer
    ON orders(customer_id);

CREATE INDEX idx_orders_status_date
    ON orders(status, order_date);

CREATE INDEX idx_order_items_product
    ON order_items(product_id);

CREATE INDEX idx_customers_segment_region
    ON customers(segment, region_id);

INSERT INTO regions(region_name)
VALUES
    ('North'),
    ('South'),
    ('East'),
    ('West');

INSERT INTO categories(category_name)
VALUES
    ('Electronics'),
    ('Office Equipment'),
    ('Furniture'),
    ('Software');

INSERT INTO sales_reps(rep_name, region_id)
SELECT 'Aarav Mehta', region_id FROM regions WHERE region_name = 'North'
UNION ALL
SELECT 'Priya Sharma', region_id FROM regions WHERE region_name = 'South'
UNION ALL
SELECT 'Rohan Singh', region_id FROM regions WHERE region_name = 'East'
UNION ALL
SELECT 'Neha Verma', region_id FROM regions WHERE region_name = 'West';

INSERT INTO customers
    (customer_name, segment, region_id, signup_date)
VALUES
    ('Atlas Consulting', 'Corporate',
        (SELECT region_id FROM regions WHERE region_name = 'North'), '2025-01-12'),
    ('BluePeak Retail', 'Small Business',
        (SELECT region_id FROM regions WHERE region_name = 'South'), '2025-02-18'),
    ('Cedar Finance', 'Corporate',
        (SELECT region_id FROM regions WHERE region_name = 'East'), '2025-03-07'),
    ('Delta Health', 'Corporate',
        (SELECT region_id FROM regions WHERE region_name = 'West'), '2025-04-21'),
    ('Evergreen Traders', 'Small Business',
        (SELECT region_id FROM regions WHERE region_name = 'North'), '2025-05-15'),
    ('Falcon Services', 'Consumer',
        (SELECT region_id FROM regions WHERE region_name = 'South'), '2025-06-09'),
    ('Granite Labs', 'Corporate',
        (SELECT region_id FROM regions WHERE region_name = 'East'), '2025-07-14'),
    ('Horizon Media', 'Small Business',
        (SELECT region_id FROM regions WHERE region_name = 'West'), '2025-08-20'),
    ('Indigo Works', 'Consumer',
        (SELECT region_id FROM regions WHERE region_name = 'North'), '2025-09-11'),
    ('Jupiter Systems', 'Corporate',
        (SELECT region_id FROM regions WHERE region_name = 'South'), '2025-10-02');

INSERT INTO products
    (product_name, category_id, unit_price, unit_cost)
VALUES
    ('Business Laptop',
        (SELECT category_id FROM categories WHERE category_name = 'Electronics'),
        1200, 820),
    ('Network Router',
        (SELECT category_id FROM categories WHERE category_name = 'Electronics'),
        420, 260),
    ('Laser Printer',
        (SELECT category_id FROM categories WHERE category_name = 'Office Equipment'),
        550, 340),
    ('Conference Desk',
        (SELECT category_id FROM categories WHERE category_name = 'Furniture'),
        780, 470),
    ('Ergonomic Chair',
        (SELECT category_id FROM categories WHERE category_name = 'Furniture'),
        360, 210),
    ('Analytics Suite',
        (SELECT category_id FROM categories WHERE category_name = 'Software'),
        900, 180),
    ('Security Monitor',
        (SELECT category_id FROM categories WHERE category_name = 'Electronics'),
        650, 390),
    ('Document Scanner',
        (SELECT category_id FROM categories WHERE category_name = 'Office Equipment'),
        310, 180);

INSERT INTO orders
    (customer_id, sales_rep_id, order_date, status, discount_rate)
SELECT
    c.customer_id,
    sr.sales_rep_id,
    v.order_date,
    v.status,
    v.discount_rate
FROM (
    VALUES
        ('Atlas Consulting', 'Aarav Mehta', '2026-01-05', 'Completed', 0.05),
        ('BluePeak Retail', 'Priya Sharma', '2026-01-12', 'Completed', 0.10),
        ('Cedar Finance', 'Rohan Singh', '2026-01-19', 'Completed', 0.00),
        ('Delta Health', 'Neha Verma', '2026-01-26', 'Completed', 0.15),
        ('Evergreen Traders', 'Aarav Mehta', '2026-02-04', 'Cancelled', 0.00),
        ('Falcon Services', 'Priya Sharma', '2026-02-11', 'Completed', 0.05),
        ('Granite Labs', 'Rohan Singh', '2026-02-18', 'Completed', 0.10),
        ('Horizon Media', 'Neha Verma', '2026-02-25', 'Pending', 0.05),
        ('Indigo Works', 'Aarav Mehta', '2026-03-04', 'Completed', 0.00),
        ('Jupiter Systems', 'Priya Sharma', '2026-03-11', 'Completed', 0.15),
        ('Atlas Consulting', 'Aarav Mehta', '2026-03-18', 'Completed', 0.05),
        ('BluePeak Retail', 'Priya Sharma', '2026-03-25', 'Returned', 0.10),
        ('Cedar Finance', 'Rohan Singh', '2026-04-01', 'Completed', 0.00),
        ('Delta Health', 'Neha Verma', '2026-04-08', 'Completed', 0.05),
        ('Evergreen Traders', 'Aarav Mehta', '2026-04-15', 'Completed', 0.10),
        ('Falcon Services', 'Priya Sharma', '2026-04-22', 'Completed', 0.15),
        ('Granite Labs', 'Rohan Singh', '2026-05-01', 'Completed', 0.05),
        ('Horizon Media', 'Neha Verma', '2026-05-08', 'Completed', 0.00),
        ('Indigo Works', 'Aarav Mehta', '2026-05-15', 'Completed', 0.10),
        ('Jupiter Systems', 'Priya Sharma', '2026-05-22', 'Completed', 0.05)
) AS v(customer_name, rep_name, order_date, status, discount_rate)
JOIN customers c ON c.customer_name = v.customer_name
JOIN sales_reps sr ON sr.rep_name = v.rep_name;

INSERT INTO order_items
    (order_id, product_id, quantity, unit_price, unit_cost)
SELECT
    o.order_id,
    p.product_id,
    v.quantity,
    p.unit_price,
    p.unit_cost
FROM (
    VALUES
        (1, 'Business Laptop', 2),
        (1, 'Security Monitor', 1),
        (2, 'Laser Printer', 3),
        (3, 'Analytics Suite', 2),
        (4, 'Conference Desk', 2),
        (4, 'Ergonomic Chair', 4),
        (5, 'Network Router', 5),
        (6, 'Document Scanner', 3),
        (6, 'Analytics Suite', 1),
        (7, 'Business Laptop', 4),
        (8, 'Conference Desk', 1),
        (9, 'Security Monitor', 2),
        (10, 'Analytics Suite', 4),
        (11, 'Business Laptop', 1),
        (11, 'Network Router', 3),
        (12, 'Laser Printer', 2),
        (13, 'Analytics Suite', 3),
        (14, 'Conference Desk', 2),
        (15, 'Ergonomic Chair', 6),
        (16, 'Document Scanner', 4),
        (17, 'Business Laptop', 3),
        (18, 'Security Monitor', 4),
        (19, 'Network Router', 5),
        (20, 'Analytics Suite', 2)
) AS v(order_id, product_name, quantity)
JOIN orders o ON o.order_id = v.order_id
JOIN products p ON p.product_name = v.product_name;

CREATE VIEW completed_order_lines AS
SELECT
    o.order_id,
    o.order_date,
    o.customer_id,
    o.sales_rep_id,
    o.discount_rate,
    oi.product_id,
    oi.quantity,
    p.product_name,
    c.category_name,
    r.region_name,
    cu.customer_name,
    cu.segment,
    oi.quantity * oi.unit_price * (1 - o.discount_rate) AS revenue,
    oi.quantity *
        (oi.unit_price * (1 - o.discount_rate) - oi.unit_cost) AS gross_profit
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN categories c ON c.category_id = p.category_id
JOIN customers cu ON cu.customer_id = o.customer_id
JOIN regions r ON r.region_id = cu.region_id
WHERE o.status = 'Completed';

CREATE VIEW customer_lifetime_value AS
SELECT
    cu.customer_id,
    cu.customer_name,
    cu.segment,
    COUNT(DISTINCT col.order_id) AS completed_orders,
    COALESCE(SUM(col.revenue), 0) AS lifetime_revenue,
    COALESCE(SUM(col.gross_profit), 0) AS lifetime_profit
FROM customers cu
LEFT JOIN completed_order_lines col
    ON col.customer_id = cu.customer_id
GROUP BY cu.customer_id, cu.customer_name, cu.segment;

CREATE VIEW product_performance AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    COALESCE(SUM(col.quantity), 0) AS units_sold,
    COALESCE(SUM(col.revenue), 0) AS revenue,
    COALESCE(SUM(col.gross_profit), 0) AS gross_profit
FROM products p
JOIN categories c ON c.category_id = p.category_id
LEFT JOIN completed_order_lines col
    ON col.product_id = p.product_id
GROUP BY p.product_id, p.product_name, c.category_name;

-- Analytical question: total revenue.
SELECT ROUND(SUM(revenue), 2) AS total_revenue
FROM completed_order_lines;

-- Analytical question: total gross profit.
SELECT ROUND(SUM(gross_profit), 2) AS total_gross_profit
FROM completed_order_lines;

-- Analytical question: gross margin.
SELECT ROUND(
    100 * SUM(gross_profit) / NULLIF(SUM(revenue), 0), 2
) AS gross_margin_pct
FROM completed_order_lines;

-- Analytical question: completed order count.
SELECT COUNT(DISTINCT order_id) AS completed_orders
FROM completed_order_lines;

-- Analytical question: average order value.
SELECT ROUND(AVG(order_revenue), 2) AS average_order_value
FROM (
    SELECT order_id, SUM(revenue) AS order_revenue
    FROM completed_order_lines
    GROUP BY order_id
) q;

-- Analytical question: revenue by month.
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY 1
ORDER BY 1;

-- Analytical question: monthly revenue growth.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', order_date)::date AS sales_month,
        SUM(revenue) AS revenue
    FROM completed_order_lines
    GROUP BY 1
),
comparison AS (
    SELECT
        sales_month,
        revenue,
        LAG(revenue) OVER (ORDER BY sales_month) AS previous_revenue
    FROM monthly
)
SELECT
    sales_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(revenue - previous_revenue, 2) AS absolute_change,
    ROUND(
        100 * (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0),
        2
    ) AS growth_pct
FROM comparison
ORDER BY sales_month;

-- Analytical question: running revenue.
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    ROUND(SUM(revenue), 2) AS monthly_revenue,
    ROUND(
        SUM(SUM(revenue)) OVER (
            ORDER BY DATE_TRUNC('month', order_date)
        ),
        2
    ) AS running_revenue
FROM completed_order_lines
GROUP BY 1
ORDER BY 1;

-- Analytical question: three-month moving average.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', order_date)::date AS sales_month,
        SUM(revenue) AS revenue
    FROM completed_order_lines
    GROUP BY 1
)
SELECT
    sales_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(
        AVG(revenue) OVER (
            ORDER BY sales_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS three_month_average
FROM monthly;

-- Analytical question: revenue by region.
SELECT
    region_name,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY region_name
ORDER BY revenue DESC;

-- Analytical question: profit by region.
SELECT
    region_name,
    ROUND(SUM(gross_profit), 2) AS gross_profit
FROM completed_order_lines
GROUP BY region_name
ORDER BY gross_profit DESC;

-- Analytical question: revenue by customer segment.
SELECT
    segment,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY segment
ORDER BY revenue DESC;

-- Analytical question: profit by customer segment.
SELECT
    segment,
    ROUND(SUM(gross_profit), 2) AS gross_profit
FROM completed_order_lines
GROUP BY segment
ORDER BY gross_profit DESC;

-- Analytical question: revenue by category.
SELECT
    category_name,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY category_name
ORDER BY revenue DESC;

-- Analytical question: units by category.
SELECT
    category_name,
    SUM(quantity) AS units
FROM completed_order_lines
GROUP BY category_name
ORDER BY units DESC;

-- Analytical question: product revenue ranking.
SELECT
    product_name,
    category_name,
    ROUND(revenue, 2) AS revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM product_performance
WHERE revenue > 0
ORDER BY revenue_rank;

-- Analytical question: product unit ranking.
SELECT
    product_name,
    units_sold,
    DENSE_RANK() OVER (ORDER BY units_sold DESC) AS unit_rank
FROM product_performance
ORDER BY unit_rank;

-- Analytical question: product gross margin.
SELECT
    product_name,
    ROUND(revenue, 2) AS revenue,
    ROUND(gross_profit, 2) AS gross_profit,
    ROUND(
        100 * gross_profit / NULLIF(revenue, 0),
        2
    ) AS margin_pct
FROM product_performance
WHERE revenue > 0
ORDER BY margin_pct DESC;

-- Analytical question: customer lifetime value.
SELECT
    customer_name,
    segment,
    completed_orders,
    ROUND(lifetime_revenue, 2) AS lifetime_revenue,
    ROUND(lifetime_profit, 2) AS lifetime_profit
FROM customer_lifetime_value
ORDER BY lifetime_revenue DESC;

-- Analytical question: repeat customers.
SELECT customer_name, completed_orders
FROM customer_lifetime_value
WHERE completed_orders >= 2
ORDER BY completed_orders DESC;

-- Analytical question: customers above their segment average.
WITH segment_average AS (
    SELECT
        segment,
        AVG(lifetime_revenue) AS avg_revenue
    FROM customer_lifetime_value
    GROUP BY segment
)
SELECT
    clv.customer_name,
    clv.segment,
    ROUND(clv.lifetime_revenue, 2) AS lifetime_revenue,
    ROUND(sa.avg_revenue, 2) AS segment_average
FROM customer_lifetime_value clv
JOIN segment_average sa ON sa.segment = clv.segment
WHERE clv.lifetime_revenue > sa.avg_revenue
ORDER BY clv.lifetime_revenue DESC;

-- Analytical question: top customers contributing to revenue.
WITH totals AS (
    SELECT SUM(lifetime_revenue) AS total_revenue
    FROM customer_lifetime_value
)
SELECT
    customer_name,
    ROUND(lifetime_revenue, 2) AS lifetime_revenue,
    ROUND(
        100 * lifetime_revenue / NULLIF(total_revenue, 0),
        2
    ) AS revenue_share_pct
FROM customer_lifetime_value, totals
WHERE lifetime_revenue > 0
ORDER BY lifetime_revenue DESC;

-- Analytical question: sales representative revenue.
SELECT
    sr.rep_name,
    ROUND(SUM(col.revenue), 2) AS revenue
FROM sales_reps sr
JOIN completed_order_lines col
    ON col.sales_rep_id = sr.sales_rep_id
GROUP BY sr.sales_rep_id, sr.rep_name
ORDER BY revenue DESC;

-- Analytical question: sales representative profit.
SELECT
    sr.rep_name,
    ROUND(SUM(col.gross_profit), 2) AS gross_profit
FROM sales_reps sr
JOIN completed_order_lines col
    ON col.sales_rep_id = sr.sales_rep_id
GROUP BY sr.sales_rep_id, sr.rep_name
ORDER BY gross_profit DESC;

-- Analytical question: sales representative order count.
SELECT
    sr.rep_name,
    COUNT(DISTINCT col.order_id) AS completed_orders
FROM sales_reps sr
JOIN completed_order_lines col
    ON col.sales_rep_id = sr.sales_rep_id
GROUP BY sr.sales_rep_id, sr.rep_name
ORDER BY completed_orders DESC;

-- Analytical question: order status distribution.
SELECT status, COUNT(*) AS order_count
FROM orders
GROUP BY status
ORDER BY order_count DESC;

-- Analytical question: cancellation rate.
SELECT ROUND(
    100 * COUNT(*) FILTER (WHERE status = 'Cancelled')
    / NULLIF(COUNT(*), 0),
    2
) AS cancellation_rate_pct
FROM orders;

-- Analytical question: return rate.
SELECT ROUND(
    100 * COUNT(*) FILTER (WHERE status = 'Returned')
    / NULLIF(COUNT(*), 0),
    2
) AS return_rate_pct
FROM orders;

-- Analytical question: pending orders requiring operational attention.
SELECT
    o.order_id,
    cu.customer_name,
    o.order_date,
    o.discount_rate
FROM orders o
JOIN customers cu ON cu.customer_id = o.customer_id
WHERE o.status = 'Pending'
ORDER BY o.order_date;

-- Analytical question: cancelled order value.
SELECT ROUND(SUM(
    oi.quantity * oi.unit_price * (1 - o.discount_rate)
), 2) AS cancelled_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Cancelled';

-- Analytical question: returned order value.
SELECT ROUND(SUM(
    oi.quantity * oi.unit_price * (1 - o.discount_rate)
), 2) AS returned_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Returned';

-- Analytical question: average units per completed order.
SELECT ROUND(
    SUM(quantity)::numeric / NULLIF(COUNT(DISTINCT order_id), 0),
    2
) AS average_units_per_order
FROM completed_order_lines;

-- Analytical question: high-value orders.
SELECT
    order_id,
    customer_name,
    ROUND(SUM(revenue), 2) AS order_value
FROM completed_order_lines
GROUP BY order_id, customer_name
HAVING SUM(revenue) >= 2500
ORDER BY order_value DESC;

-- Analytical question: revenue by customer and category.
SELECT
    customer_name,
    category_name,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY customer_name, category_name
ORDER BY revenue DESC;

-- Analytical question: regional category performance.
SELECT
    region_name,
    category_name,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY region_name, category_name
ORDER BY region_name, revenue DESC;

-- Analytical question: best category within each region.
WITH regional_category AS (
    SELECT
        region_name,
        category_name,
        SUM(revenue) AS revenue
    FROM completed_order_lines
    GROUP BY region_name, category_name
),
ranked AS (
    SELECT *,
           RANK() OVER (
               PARTITION BY region_name
               ORDER BY revenue DESC
           ) AS category_rank
    FROM regional_category
)
SELECT
    region_name,
    category_name,
    ROUND(revenue, 2) AS revenue
FROM ranked
WHERE category_rank = 1;

-- Analytical question: average discount by segment.
SELECT
    segment,
    ROUND(AVG(discount_rate) * 100, 2) AS average_discount_pct
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY segment
ORDER BY average_discount_pct DESC;

-- Analytical question: discount-level revenue.
SELECT
    discount_rate,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY discount_rate
ORDER BY discount_rate;

-- Analytical question: order value bands.
WITH order_values AS (
    SELECT order_id, customer_name, SUM(revenue) AS order_value
    FROM completed_order_lines
    GROUP BY order_id, customer_name
)
SELECT
    CASE
        WHEN order_value < 1000 THEN 'Under 1000'
        WHEN order_value < 2500 THEN '1000-2499'
        ELSE '2500+'
    END AS order_band,
    COUNT(*) AS order_count,
    ROUND(SUM(order_value), 2) AS revenue
FROM order_values
GROUP BY 1
ORDER BY revenue DESC;

-- Analytical question: revenue concentration in top customers.
WITH ranked AS (
    SELECT
        customer_name,
        lifetime_revenue,
        SUM(lifetime_revenue) OVER () AS total_revenue,
        SUM(lifetime_revenue) OVER (
            ORDER BY lifetime_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM customer_lifetime_value
)
SELECT
    customer_name,
    ROUND(lifetime_revenue, 2) AS lifetime_revenue,
    ROUND(
        100 * cumulative_revenue / NULLIF(total_revenue, 0),
        2
    ) AS cumulative_share_pct
FROM ranked
ORDER BY lifetime_revenue DESC;

-- Analytical question: products with low margins.
SELECT
    product_name,
    ROUND(revenue, 2) AS revenue,
    ROUND(gross_profit, 2) AS gross_profit,
    ROUND(
        100 * gross_profit / NULLIF(revenue, 0),
        2
    ) AS margin_pct
FROM product_performance
WHERE revenue > 0
  AND gross_profit / NULLIF(revenue, 0) < 0.35
ORDER BY margin_pct;

-- Analytical question: products never sold.
SELECT
    p.product_name
FROM products p
LEFT JOIN completed_order_lines col
    ON col.product_id = p.product_id
WHERE col.product_id IS NULL;

-- Analytical question: customers without completed purchases.
SELECT
    c.customer_name,
    c.segment
FROM customers c
LEFT JOIN customer_lifetime_value clv
    ON clv.customer_id = c.customer_id
WHERE clv.lifetime_revenue = 0;

-- Analytical question: average revenue per customer by region.
SELECT
    r.region_name,
    ROUND(AVG(clv.lifetime_revenue), 2) AS average_customer_revenue
FROM regions r
JOIN customers c ON c.region_id = r.region_id
JOIN customer_lifetime_value clv
    ON clv.customer_id = c.customer_id
GROUP BY r.region_name
ORDER BY average_customer_revenue DESC;

-- Analytical question: segment revenue ranking.
SELECT
    segment,
    ROUND(SUM(lifetime_revenue), 2) AS revenue,
    DENSE_RANK() OVER (
        ORDER BY SUM(lifetime_revenue) DESC
    ) AS segment_rank
FROM customer_lifetime_value
GROUP BY segment;

-- Analytical question: month with highest revenue.
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY 1
ORDER BY revenue DESC
LIMIT 1;

-- Analytical question: highest-profit product.
SELECT
    product_name,
    ROUND(gross_profit, 2) AS gross_profit
FROM product_performance
ORDER BY gross_profit DESC
LIMIT 1;

-- Analytical question: highest-margin product.
SELECT
    product_name,
    ROUND(
        100 * gross_profit / NULLIF(revenue, 0),
        2
    ) AS margin_pct
FROM product_performance
WHERE revenue > 0
ORDER BY margin_pct DESC
LIMIT 1;

-- Analytical question: regional share of total revenue.
WITH regional AS (
    SELECT region_name, SUM(revenue) AS revenue
    FROM completed_order_lines
    GROUP BY region_name
)
SELECT
    region_name,
    ROUND(revenue, 2) AS revenue,
    ROUND(
        100 * revenue / NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS share_pct
FROM regional
ORDER BY revenue DESC;

-- Analytical question: monthly category mix.
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    category_name,
    ROUND(SUM(revenue), 2) AS revenue
FROM completed_order_lines
GROUP BY 1, category_name
ORDER BY 1, revenue DESC;

-- Analytical question: customer acquisition cohort by signup year.
SELECT
    EXTRACT(YEAR FROM c.signup_date) AS signup_year,
    COUNT(*) AS customers,
    ROUND(AVG(clv.lifetime_revenue), 2) AS average_lifetime_revenue
FROM customers c
JOIN customer_lifetime_value clv
    ON clv.customer_id = c.customer_id
GROUP BY 1
ORDER BY 1;

-- Analytical question: completed orders by customer segment and month.
SELECT
    DATE_TRUNC('month', o.order_date)::date AS sales_month,
    c.segment,
    COUNT(DISTINCT o.order_id) AS completed_orders
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY 1, c.segment
ORDER BY 1, c.segment;

-- Analytical question: customers with revenue above a business threshold.
SELECT
    customer_name,
    ROUND(lifetime_revenue, 2) AS lifetime_revenue
FROM customer_lifetime_value
WHERE lifetime_revenue >= 3000
ORDER BY lifetime_revenue DESC;

-- Analytical question: order-level profitability.
SELECT
    order_id,
    customer_name,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(gross_profit), 2) AS gross_profit,
    ROUND(
        100 * SUM(gross_profit) / NULLIF(SUM(revenue), 0),
        2
    ) AS margin_pct
FROM completed_order_lines
GROUP BY order_id, customer_name
ORDER BY gross_profit DESC;

-- Analytical question: data quality check for order economics.
SELECT COUNT(*) AS invalid_order_items
FROM order_items
WHERE unit_price <= 0
   OR unit_cost < 0
   OR unit_cost > unit_price;

-- Analytical question: orphan detection.
SELECT COUNT(*) AS orphan_order_items
FROM order_items oi
LEFT JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_id IS NULL;

-- Transactional demonstration: a database-side correction can be committed
-- atomically. The example creates no invalid business state.
BEGIN;

UPDATE products
SET unit_price = unit_price
WHERE product_id = (
    SELECT product_id
    FROM products
    ORDER BY product_id
    LIMIT 1
);

COMMIT;

-- Query-plan inspection for a frequent date/status filter.
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    order_date,
    COUNT(*) AS completed_orders
FROM orders
WHERE status = 'Completed'
  AND order_date >= DATE '2026-01-01'
GROUP BY order_date
ORDER BY order_date;
