DROP SCHEMA IF EXISTS pandas_cleaning_demo CASCADE;
CREATE SCHEMA pandas_cleaning_demo;
SET search_path TO pandas_cleaning_demo;

-- Raw customer data intentionally contains the quality problems that the
-- cleaning workflow must detect and transform.
CREATE TABLE raw_customers (
    customer_id INTEGER NOT NULL,
    name TEXT,
    age TEXT,
    email TEXT,
    city TEXT,
    segment TEXT,
    signup_date TEXT,
    orders TEXT
);

INSERT INTO raw_customers
(customer_id, name, age, email, city, segment, signup_date, orders)
VALUES
(101, ' Alice  Sharma ', '29', ' ALICE.SHARMA@EXAMPLE.COM ', 'Lucknow', 'Premium', '2026-01-15', '12'),
(102, 'Bob Khan', '', 'bob.khan@example.com', 'Delhi', 'Standard', '2026/02/20', '5'),
(103, 'Charlie  Rao', '34', '', 'Mumbai', 'Premium', '2026-03-10', '8'),
(104, 'Alice  Sharma', '29', 'alice.sharma@example.com', 'Lucknow', 'Premium', '2026-01-15', '12'),
(105, 'David Mehta', 'unknown', 'david.mehta@example.com', 'Delhi', 'standard', '2026-04-05', '3'),
(106, 'Esha Patel', '41', 'esha.patel@example.com', ' ', 'Enterprise', '2026-05-11', '21'),
(107, 'Farhan Ali', '37', 'farhan.ali@example.com', 'Bengaluru', 'Standard', 'invalid', '7'),
(108, '', '26', 'neha@example.com', 'Pune', 'Standard', '2026-06-30', '2'),
(109, 'George Sen', '-5', 'george.sen@example.com', 'Chennai', 'Premium', '2026-07-01', '15'),
(110, 'Hina Roy', '30', 'hina.roy@example.com', 'Kolkata', 'premium', '2026-07-18', '10');

-- NULLIF prevents empty strings from being confused with meaningful values.
CREATE VIEW normalized_customers AS
SELECT
    customer_id,
    NULLIF(
        initcap(
            regexp_replace(trim(name), '\s+', ' ', 'g')
        ),
        ''
    ) AS name,
    NULLIF(trim(age), '') AS age_text,
    NULLIF(lower(trim(email)), '') AS email,
    NULLIF(
        initcap(
            regexp_replace(trim(city), '\s+', ' ', 'g')
        ),
        ''
    ) AS city,
    initcap(lower(NULLIF(trim(segment), ''))) AS segment,
    replace(NULLIF(trim(signup_date), ''), '/', '-') AS signup_date_text,
    NULLIF(trim(orders), '') AS orders_text
FROM raw_customers;

-- PostgreSQL's NULLIF plus regex validation lets conversion happen only
-- when the source string has the expected structure.
CREATE OR REPLACE FUNCTION safe_integer(
    value TEXT,
    minimum_value INTEGER,
    maximum_value INTEGER
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    result INTEGER;
BEGIN
    IF value IS NULL
       OR lower(trim(value)) = 'unknown'
       OR trim(value) = '' THEN
        RETURN NULL;
    END IF;

    IF trim(value) !~ '^-?[0-9]+$' THEN
        RETURN NULL;
    END IF;

    result := trim(value)::INTEGER;

    IF result < minimum_value OR result > maximum_value THEN
        RETURN NULL;
    END IF;

    RETURN result;
EXCEPTION
    WHEN numeric_value_out_of_range THEN
        RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION safe_date(value TEXT)
RETURNS DATE
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF value IS NULL OR trim(value) = '' THEN
        RETURN NULL;
    END IF;

    IF trim(value) !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN
        RETURN NULL;
    END IF;

    RETURN trim(value)::DATE;
EXCEPTION
    WHEN others THEN
        RETURN NULL;
END;
$$;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER CHECK (age BETWEEN 18 AND 100),
    email TEXT,
    city TEXT NOT NULL,
    segment TEXT NOT NULL
        CHECK (segment IN ('Standard', 'Premium', 'Enterprise')),
    signup_date DATE,
    orders INTEGER CHECK (orders >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customers_email_format
        CHECK (
            email IS NULL
            OR email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
        )
);

CREATE UNIQUE INDEX customers_email_unique_idx
ON customers (lower(email))
WHERE email IS NOT NULL;

CREATE INDEX customers_segment_idx
ON customers (segment);

CREATE INDEX customers_signup_date_idx
ON customers (signup_date);

-- Deduplication uses customer_id as the primary identity key. The first
-- source row is retained deterministically by source order.
WITH prepared AS (
    SELECT
        customer_id,
        COALESCE(name, 'Unknown Customer') AS name,
        safe_integer(age_text, 18, 100) AS age,
        email,
        COALESCE(city, 'Unknown') AS city,
        COALESCE(segment, 'Standard') AS segment,
        safe_date(signup_date_text) AS signup_date,
        safe_integer(orders_text, 0, 1000000) AS orders,
        row_number() OVER (
            PARTITION BY customer_id
            ORDER BY customer_id
        ) AS row_number
    FROM normalized_customers
),
deduplicated AS (
    SELECT *
    FROM prepared
    WHERE row_number = 1
),
statistics AS (
    SELECT
        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY age) AS median_age,
        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY orders) AS median_orders
    FROM deduplicated
)
INSERT INTO customers (
    customer_id,
    name,
    age,
    email,
    city,
    segment,
    signup_date,
    orders
)
SELECT
    d.customer_id,
    d.name,
    COALESCE(d.age, round(s.median_age)::INTEGER),
    d.email,
    d.city,
    d.segment,
    d.signup_date,
    COALESCE(d.orders, round(s.median_orders)::INTEGER)
FROM deduplicated d
CROSS JOIN statistics s
ON CONFLICT (customer_id) DO NOTHING;

-- Trigger prevents future writes from introducing invalid email formatting.
CREATE OR REPLACE FUNCTION validate_customer_email()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.email IS NOT NULL
       AND NEW.email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' THEN
        RAISE EXCEPTION 'Invalid email format for customer %', NEW.customer_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER customers_email_validation
BEFORE INSERT OR UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION validate_customer_email();

CREATE VIEW customer_quality_report AS
SELECT
    COUNT(*) AS customer_count,
    COUNT(*) FILTER (WHERE email IS NULL) AS missing_email_count,
    COUNT(*) FILTER (WHERE signup_date IS NULL) AS invalid_or_missing_date_count,
    COUNT(*) FILTER (WHERE age IS NULL) AS missing_age_count,
    COUNT(*) FILTER (WHERE orders IS NULL) AS missing_orders_count,
    ROUND(AVG(age), 2) AS average_age,
    ROUND(AVG(orders), 2) AS average_orders
FROM customers;

CREATE VIEW segment_report AS
SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(age), 2) AS average_age,
    ROUND(AVG(orders), 2) AS average_orders,
    SUM(orders) AS total_orders
FROM customers
GROUP BY segment
ORDER BY segment;

-- Transactional example: the validation trigger and constraints apply as a
-- single atomic operation. The savepoint demonstrates recoverable failure.
BEGIN;

SAVEPOINT before_invalid_update;

-- This statement fails because age violates the CHECK constraint.
DO $$
BEGIN
    BEGIN
        UPDATE customers
        SET age = 150
        WHERE customer_id = 101;
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Rejected invalid age for customer 101';
            ROLLBACK TO SAVEPOINT before_invalid_update;
    END;
END;
$$;

UPDATE customers
SET city = 'Lucknow'
WHERE customer_id = 101;

COMMIT;

-- Missing-value inspection.
SELECT
    customer_id,
    name,
    age,
    email,
    city,
    segment,
    signup_date,
    orders
FROM customers
ORDER BY customer_id;

-- Duplicate detection on the raw data.
SELECT
    customer_id,
    COUNT(*) AS source_occurrences
FROM raw_customers
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY customer_id;

-- Invalid source values are identifiable before they enter the typed table.
SELECT
    customer_id,
    age,
    signup_date,
    CASE
        WHEN safe_integer(age, 18, 100) IS NULL
             AND NULLIF(trim(age), '') IS NOT NULL
        THEN 'Invalid age'
        WHEN safe_date(replace(NULLIF(trim(signup_date), ''), '/', '-')) IS NULL
             AND NULLIF(trim(signup_date), '') IS NOT NULL
        THEN 'Invalid date'
        ELSE 'Valid or missing'
    END AS quality_status
FROM raw_customers
ORDER BY customer_id;

SELECT * FROM customer_quality_report;
SELECT * FROM segment_report;
