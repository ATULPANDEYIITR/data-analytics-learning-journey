DROP SCHEMA IF EXISTS pandas_transformation CASCADE;
CREATE SCHEMA pandas_transformation;

SET search_path TO pandas_transformation;

-- The relational model represents the same transformation concepts as a
-- dataframe pipeline while enforcing core data-quality rules at the database level.

CREATE TYPE order_status AS ENUM (
    'completed',
    'pending',
    'cancelled'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'medium',
    'high'
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    CONSTRAINT customers_name_not_blank
        CHECK (length(btrim(customer_name)) > 0)
);

CREATE TABLE regions (
    region_code CHAR(1) PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE,
    CONSTRAINT regions_name_not_blank
        CHECK (length(btrim(region_name)) > 0)
);

INSERT INTO regions (region_code, region_name)
VALUES
    ('N', 'North'),
    ('S', 'South'),
    ('E', 'East'),
    ('W', 'West');

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    region_code CHAR(1) NOT NULL REFERENCES regions(region_code),
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14, 2) NOT NULL,
    status order_status NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT orders_product_not_blank
        CHECK (length(btrim(product)) > 0),
    CONSTRAINT orders_quantity_positive
        CHECK (quantity > 0),
    CONSTRAINT orders_unit_price_nonnegative
        CHECK (unit_price >= 0)
);

CREATE TABLE order_transformations (
    order_id BIGINT PRIMARY KEY REFERENCES orders(order_id) ON DELETE CASCADE,
    gross_amount NUMERIC(16, 2) NOT NULL,
    discount_rate NUMERIC(5, 4) NOT NULL,
    net_amount NUMERIC(16, 2) NOT NULL,
    priority priority_level NOT NULL,
    transformed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT transformation_discount_valid
        CHECK (discount_rate >= 0 AND discount_rate <= 1),
    CONSTRAINT transformation_amounts_valid
        CHECK (
            gross_amount >= 0
            AND net_amount >= 0
        )
);

CREATE INDEX idx_orders_status_region
    ON orders(status, region_code);

CREATE INDEX idx_transformations_net_amount
    ON order_transformations(net_amount DESC);

INSERT INTO customers (customer_name)
VALUES
    ('Asha'),
    ('Ravi'),
    ('Meera'),
    ('Kabir');

INSERT INTO orders (
    order_id,
    customer_id,
    region_code,
    product,
    quantity,
    unit_price,
    status
)
VALUES
    (1001, 1, 'N', 'Laptop', 2, 75000, 'completed'),
    (1002, 2, 'S', 'Monitor', 3, 18000, 'completed'),
    (1003, 3, 'Keyboard', 5, 3500, 'pending'),
    (1004, 4, 'Laptop', 1, 82000, 'cancelled'),
    (1005, 1, 'N', 'Mouse', 4, 1500, 'completed'),
    (1006, 2, 'S', 'Laptop', 2, 78000, 'completed'),
    (1007, 3, 'W', 'Monitor', 2, 19500, 'pending');

-- A PostgreSQL function centralizes the business transformation.
-- It is intentionally separate from the source order table so the original
-- transactional data remains auditable.
CREATE OR REPLACE FUNCTION transform_order(p_order_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_gross NUMERIC(16, 2);
    v_discount NUMERIC(5, 4);
    v_net NUMERIC(16, 2);
    v_priority priority_level;
BEGIN
    SELECT quantity * unit_price
    INTO v_gross
    FROM orders
    WHERE order_id = p_order_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order % does not exist', p_order_id;
    END IF;

    v_discount :=
        CASE
            WHEN v_gross >= 100000 THEN 0.10
            WHEN v_gross >= 50000 THEN 0.05
            ELSE 0
        END;

    v_net := v_gross * (1 - v_discount);

    v_priority :=
        CASE
            WHEN v_net >= 100000 THEN 'high'::priority_level
            WHEN v_net >= 30000 THEN 'medium'::priority_level
            ELSE 'low'::priority_level
        END;

    INSERT INTO order_transformations (
        order_id,
        gross_amount,
        discount_rate,
        net_amount,
        priority
    )
    VALUES (
        p_order_id,
        v_gross,
        v_discount,
        v_net,
        v_priority
    )
    ON CONFLICT (order_id)
    DO UPDATE SET
        gross_amount = EXCLUDED.gross_amount,
        discount_rate = EXCLUDED.discount_rate,
        net_amount = EXCLUDED.net_amount,
        priority = EXCLUDED.priority,
        transformed_at = CURRENT_TIMESTAMP;
END;
$$;

CREATE OR REPLACE FUNCTION transform_all_orders()
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id BIGINT;
BEGIN
    FOR v_order_id IN
        SELECT order_id FROM orders ORDER BY order_id
    LOOP
        PERFORM transform_order(v_order_id);
    END LOOP;
END;
$$;

-- The trigger prevents a transformed result from becoming inconsistent
-- when an order's quantity or price changes.
CREATE OR REPLACE FUNCTION refresh_order_transformation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM transform_order(NEW.order_id);
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_refresh_order_transformation
AFTER INSERT OR UPDATE OF quantity, unit_price
ON orders
FOR EACH ROW
EXECUTE FUNCTION refresh_order_transformation();

BEGIN;

SELECT transform_all_orders();

COMMIT;

CREATE VIEW transformed_order_report AS
SELECT
    o.order_id,
    c.customer_name,
    r.region_name,
    o.product,
    o.quantity,
    o.unit_price,
    o.status,
    t.gross_amount,
    t.discount_rate,
    t.net_amount,
    t.priority,
    t.transformed_at
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id
JOIN regions AS r
    ON r.region_code = o.region_code
JOIN order_transformations AS t
    ON t.order_id = o.order_id;

-- Vectorized-style derived calculation in SQL: expressions operate over
-- result sets without procedural row-by-row client-side processing.
SELECT
    order_id,
    customer_name,
    product,
    gross_amount,
    net_amount,
    priority
FROM transformed_order_report
WHERE status <> 'cancelled'
  AND net_amount >= 30000
ORDER BY
    CASE priority
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
    END,
    net_amount DESC;

-- Equivalent of a map operation for region normalization.
SELECT
    order_id,
    region_name,
    CASE region_name
        WHEN 'North' THEN 'N'
        WHEN 'South' THEN 'S'
        WHEN 'East' THEN 'E'
        WHEN 'West' THEN 'W'
        ELSE 'UNKNOWN'
    END AS normalized_region_code
FROM transformed_order_report
ORDER BY order_id;

-- Aggregation demonstrates how transformed values become an operational report.
SELECT
    region_name,
    COUNT(*) AS completed_orders,
    SUM(quantity) AS total_quantity,
    SUM(net_amount) AS total_revenue
FROM transformed_order_report
WHERE status = 'completed'
GROUP BY region_name
ORDER BY total_revenue DESC;

-- CTE isolates the transformation stage before filtering.
WITH transformed AS (
    SELECT
        order_id,
        customer_name,
        product,
        status,
        gross_amount,
        net_amount,
        priority
    FROM transformed_order_report
)
SELECT
    order_id,
    customer_name,
    product,
    net_amount,
    priority
FROM transformed
WHERE status <> 'cancelled'
  AND priority IN ('high', 'medium')
ORDER BY net_amount DESC;

-- Transactional failure example. PostgreSQL rolls the invalid insert back,
-- preserving database integrity through the CHECK constraint.
DO $$
BEGIN
    BEGIN
        INSERT INTO orders (
            order_id,
            customer_id,
            region_code,
            product,
            quantity,
            unit_price,
            status
        )
        VALUES (
            9001,
            1,
            'N',
            'Invalid Product',
            0,
            50000,
            'pending'
        );
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid quantity correctly rejected';
    END;
END;
$$;
