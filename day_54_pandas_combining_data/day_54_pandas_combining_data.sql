DROP SCHEMA IF EXISTS pandas_combining CASCADE;
CREATE SCHEMA pandas_combining;

SET search_path TO pandas_combining;

-- The relational model mirrors the major combining operations:
-- customers provide the parent relation, orders provide a one-to-many
-- child relation, contacts provide a one-to-one relation, and monthly
-- order tables demonstrate row-wise concatenation.

CREATE TABLE customers (
    customer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name TEXT NOT NULL CHECK (btrim(customer_name) <> ''),
    region TEXT NOT NULL CHECK (btrim(region) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_contacts (
    customer_id INTEGER PRIMARY KEY
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE
        CHECK (position('@' IN email) > 1)
);

CREATE TABLE orders (
    order_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    status TEXT NOT NULL
        CHECK (status IN ('pending', 'paid', 'cancelled')),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT
);

CREATE TABLE monthly_order_import (
    import_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INTEGER NOT NULL,
    import_month DATE NOT NULL,
    customer_id INTEGER NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    status TEXT NOT NULL
        CHECK (status IN ('pending', 'paid', 'cancelled')),
    UNIQUE (order_id, import_month)
);

CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX idx_orders_customer_status
    ON orders(customer_id, status);

CREATE INDEX idx_monthly_order_import_customer
    ON monthly_order_import(customer_id);

INSERT INTO customers (customer_name, region)
VALUES
    ('Atul', 'North'),
    ('Priya', 'South'),
    ('Rahul', 'North'),
    ('Neha', 'West');

INSERT INTO customer_contacts (customer_id, email)
VALUES
    (1, 'atul@example.com'),
    (2, 'priya@example.com'),
    (3, 'rahul@example.com'),
    (4, 'neha@example.com');

INSERT INTO orders (
    customer_id,
    order_date,
    amount,
    status
)
VALUES
    (1, DATE '2026-01-10', 1200.00, 'paid'),
    (2, DATE '2026-01-12', 850.00, 'paid'),
    (2, DATE '2026-02-04', 450.00, 'pending'),
    (3, DATE '2026-02-15', 1500.00, 'paid');

INSERT INTO monthly_order_import (
    order_id,
    import_month,
    customer_id,
    amount,
    status
)
VALUES
    (101, DATE '2026-01-01', 1, 1200.00, 'paid'),
    (102, DATE '2026-01-01', 2, 850.00, 'paid'),
    (103, DATE '2026-02-01', 2, 450.00, 'pending'),
    (104, DATE '2026-02-01', 5, 700.00, 'paid'),
    (105, DATE '2026-02-01', 3, 1500.00, 'paid');

-- A LEFT JOIN corresponds to preserving all rows from the left
-- DataFrame while attaching matching right-side rows.
SELECT
    c.customer_id,
    c.customer_name,
    c.region,
    o.order_id,
    o.amount,
    o.status
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_id;

-- An INNER JOIN retains only relationally matched records.
SELECT
    c.customer_id,
    c.customer_name,
    o.order_id,
    o.amount
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_id;

-- A FULL OUTER JOIN exposes both matched and unmatched records.
-- The imported order with customer_id 5 intentionally represents
-- an orphaned right-side record.
SELECT
    c.customer_id AS known_customer_id,
    o.customer_id AS order_customer_id,
    c.customer_name,
    o.order_id,
    o.amount,
    CASE
        WHEN c.customer_id IS NULL THEN 'RIGHT_ONLY'
        WHEN o.order_id IS NULL THEN 'LEFT_ONLY'
        ELSE 'MATCHED'
    END AS relationship_state
FROM customers AS c
FULL OUTER JOIN monthly_order_import AS o
    ON o.customer_id = c.customer_id
ORDER BY COALESCE(c.customer_id, o.customer_id), o.order_id;

-- Index-based join is represented relationally by joining two
-- one-to-one relations through the customer primary key.
SELECT
    c.customer_id,
    c.customer_name,
    c.region,
    cc.email
FROM customers AS c
LEFT JOIN customer_contacts AS cc
    ON cc.customer_id = c.customer_id
ORDER BY c.customer_id;

-- Row-wise concatenation is represented by UNION ALL.
-- UNION ALL preserves rows and does not perform duplicate elimination.
SELECT
    order_id,
    import_month,
    customer_id,
    amount,
    status
FROM monthly_order_import
WHERE import_month = DATE '2026-01-01'

UNION ALL

SELECT
    order_id,
    import_month,
    customer_id,
    amount,
    status
FROM monthly_order_import
WHERE import_month = DATE '2026-02-01'
ORDER BY import_month, order_id;

-- DataFrame.append() is not required as a separate relational operation.
-- INSERT or UNION ALL expresses the corresponding row-addition semantics.

-- Anti-join: customers that have no order.
SELECT
    c.customer_id,
    c.customer_name
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
)
ORDER BY c.customer_id;

-- Anti-join: imported records whose customer is unknown.
SELECT
    moi.order_id,
    moi.customer_id,
    moi.amount
FROM monthly_order_import AS moi
WHERE NOT EXISTS (
    SELECT 1
    FROM customers AS c
    WHERE c.customer_id = moi.customer_id
)
ORDER BY moi.order_id;

-- Aggregation after combination.
WITH matched_orders AS (
    SELECT
        c.customer_id,
        c.customer_name,
        o.amount
    FROM customers AS c
    INNER JOIN orders AS o
        ON o.customer_id = c.customer_id
)
SELECT
    customer_id,
    customer_name,
    SUM(amount) AS total_order_amount,
    CASE
        WHEN SUM(amount) >= 1500 THEN 'high'
        ELSE 'standard'
    END AS customer_segment
FROM matched_orders
GROUP BY customer_id, customer_name
ORDER BY customer_id;

-- A reusable relational view for a frequently consumed combined dataset.
CREATE OR REPLACE VIEW customer_order_summary AS
SELECT
    c.customer_id,
    c.customer_name,
    c.region,
    COUNT(o.order_id) AS order_count,
    COALESCE(SUM(o.amount), 0.00) AS total_amount,
    COUNT(*) FILTER (
        WHERE o.status = 'pending'
    ) AS pending_order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    c.region;

SELECT *
FROM customer_order_summary
ORDER BY customer_id;

-- A materialized integrity report can identify orphan records in
-- staging data without changing the normalized customer/order model.
CREATE OR REPLACE FUNCTION find_orphan_imports()
RETURNS TABLE (
    order_id INTEGER,
    customer_id INTEGER,
    amount NUMERIC(12, 2)
)
LANGUAGE sql
AS $$
    SELECT
        moi.order_id,
        moi.customer_id,
        moi.amount
    FROM monthly_order_import AS moi
    WHERE NOT EXISTS (
        SELECT 1
        FROM customers AS c
        WHERE c.customer_id = moi.customer_id
    )
    ORDER BY moi.order_id;
$$;

SELECT *
FROM find_orphan_imports();

-- Transactional workflow: insert a valid order and verify the
-- resulting relational state atomically.
BEGIN;

INSERT INTO orders (
    customer_id,
    order_date,
    amount,
    status
)
VALUES (
    4,
    DATE '2026-02-20',
    700.00,
    'pending'
);

SAVEPOINT after_valid_insert;

SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
FROM orders
WHERE customer_id = 4
GROUP BY customer_id;

COMMIT;

-- Invalid records are rejected by database constraints.
-- The following transaction demonstrates controlled failure.
BEGIN;

SAVEPOINT before_invalid_insert;

DO $$
BEGIN
    BEGIN
        INSERT INTO orders (
            customer_id,
            order_date,
            amount,
            status
        )
        VALUES (
            9999,
            CURRENT_DATE,
            500.00,
            'paid'
        );
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'Expected failure: unknown customer was rejected.';
    END;
END
$$;

ROLLBACK;

-- EXPLAIN demonstrates the role of the customer-key index in a
-- realistic retrieval pattern.
EXPLAIN
SELECT
    o.order_id,
    o.customer_id,
    o.amount,
    o.status
FROM orders AS o
WHERE o.customer_id = 2
  AND o.status = 'paid';

-- The unique primary key on customer_contacts enforces the
-- one-to-one relationship needed for a safe join.
SELECT
    c.customer_id,
    c.customer_name,
    cc.email
FROM customers AS c
JOIN customer_contacts AS cc
    ON cc.customer_id = c.customer_id
ORDER BY c.customer_id;
