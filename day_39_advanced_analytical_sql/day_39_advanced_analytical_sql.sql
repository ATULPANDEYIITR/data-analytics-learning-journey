-- Advanced Analytical SQL
-- PostgreSQL 15+
--
-- Demonstrates:
--   ordered-set percentiles and median;
--   conditional aggregation using FILTER and CASE;
--   ROWS-based rolling windows and calendar-based rolling windows;
--   gaps and islands for reporting dates;
--   data-quality checks, constraints, and transaction-safe loading.
--
-- The script runs inside a transaction and rolls back at the end, making
-- it repeatable without leaving sample objects in the current database.
-- Run in a disposable PostgreSQL database if persistent objects are desired.

BEGIN;

CREATE TEMP TABLE analytics_daily (
    record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_date DATE NOT NULL,
    department TEXT NOT NULL CHECK (length(trim(department)) > 0),
    revenue NUMERIC(14, 2) NOT NULL CHECK (revenue >= 0),
    orders INTEGER NOT NULL CHECK (orders >= 0),
    status TEXT NOT NULL
        CHECK (status IN ('completed', 'cancelled', 'pending')),
    UNIQUE (business_date, department)
);

INSERT INTO analytics_daily
    (business_date, department, revenue, orders, status)
VALUES
    ('2026-09-01', 'Operations', 1200.00, 24, 'completed'),
    ('2026-09-02', 'Operations', 1350.00, 27, 'completed'),
    ('2026-09-03', 'Operations', 0.00, 0, 'cancelled'),
    ('2026-09-04', 'Operations', 1820.00, 36, 'completed'),
    ('2026-09-06', 'Operations', 1600.00, 32, 'completed'),
    ('2026-09-07', 'Operations', 1750.00, 35, 'completed'),
    ('2026-09-08', 'Operations', 2100.00, 42, 'completed'),
    ('2026-09-09', 'Operations', 900.00, 18, 'pending'),
    ('2026-09-10', 'Operations', 2400.00, 48, 'completed'),
    ('2026-09-11', 'Operations', 1950.00, 39, 'completed'),
    ('2026-09-12', 'Operations', 2600.00, 52, 'completed'),
    ('2026-09-13', 'Operations', 800.00, 16, 'cancelled'),
    ('2026-09-15', 'Operations', 2850.00, 57, 'completed'),
    ('2026-09-16', 'Operations', 3000.00, 60, 'completed'),
    ('2026-09-17', 'Operations', 2750.00, 55, 'completed'),
    ('2026-09-01', 'Logistics', 950.00, 19, 'completed'),
    ('2026-09-02', 'Logistics', 1100.00, 22, 'completed'),
    ('2026-09-04', 'Logistics', 1550.00, 31, 'completed'),
    ('2026-09-05', 'Logistics', 1750.00, 35, 'completed'),
    ('2026-09-06', 'Logistics', 0.00, 0, 'cancelled'),
    ('2026-09-08', 'Logistics', 1950.00, 39, 'completed');

CREATE INDEX analytics_daily_department_date_idx
    ON analytics_daily (department, business_date);

CREATE INDEX analytics_daily_status_date_idx
    ON analytics_daily (status, business_date);

-- Ordered-set aggregates sort the observations internally.
-- PERCENTILE_CONT interpolates; PERCENTILE_DISC returns an observed value.
SELECT
    department,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_observations,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY revenue)
        FILTER (WHERE status = 'completed') AS median_continuous,
    percentile_disc(0.50) WITHIN GROUP (ORDER BY revenue)
        FILTER (WHERE status = 'completed') AS median_discrete,
    percentile_cont(ARRAY[0.25, 0.50, 0.75, 0.90, 0.95]::double precision[])
        WITHIN GROUP (ORDER BY revenue)
        FILTER (WHERE status = 'completed') AS continuous_percentiles,
    percentile_disc(ARRAY[0.25, 0.50, 0.75, 0.90, 0.95]::double precision[])
        WITHIN GROUP (ORDER BY revenue)
        FILTER (WHERE status = 'completed') AS discrete_percentiles
FROM analytics_daily
GROUP BY department
ORDER BY department;

-- Conditional aggregation calculates several business measures in one scan.
-- FILTER expresses the condition on each aggregate; CASE is useful when
-- the aggregate itself must transform a value for qualifying rows.
SELECT
    department,
    COUNT(*) AS all_daily_records,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_days,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_days,
    COUNT(*) FILTER (WHERE status = 'pending') AS pending_days,
    SUM(revenue) FILTER (WHERE status = 'completed') AS completed_revenue,
    SUM(orders) FILTER (WHERE status = 'completed') AS completed_orders,
    SUM(orders) FILTER (WHERE status = 'cancelled') AS cancelled_orders,
    AVG(revenue) FILTER (WHERE status = 'completed') AS average_completed_day,
    SUM(CASE WHEN status = 'completed' THEN revenue ELSE 0 END)
        AS case_based_completed_revenue,
    COUNT(*) FILTER (WHERE revenue > 2000 AND status = 'completed')
        AS high_revenue_completed_days
FROM analytics_daily
GROUP BY department
ORDER BY department;

-- Percentile-based outlier screening compares each completed day with its
-- department's upper tail. A threshold is not proof of an error: investigate
-- the underlying transaction and business context before excluding records.
WITH department_thresholds AS (
    SELECT
        department,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY revenue) AS p95
    FROM analytics_daily
    WHERE status = 'completed'
    GROUP BY department
)
SELECT
    d.department,
    d.business_date,
    d.revenue,
    t.p95,
    d.revenue > t.p95 AS exceeds_p95
FROM analytics_daily AS d
JOIN department_thresholds AS t USING (department)
WHERE d.status = 'completed'
ORDER BY d.department, d.business_date;

-- A ROWS frame counts records, not calendar days. Missing dates do not create
-- rows, so the window may cover a longer calendar interval than expected.
SELECT
    department,
    business_date,
    revenue,
    SUM(revenue) FILTER (WHERE status = 'completed') OVER (
        PARTITION BY department
        ORDER BY business_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS completed_revenue_last_three_rows,
    AVG(revenue) FILTER (WHERE status = 'completed') OVER (
        PARTITION BY department
        ORDER BY business_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS average_completed_revenue_last_three_rows,
    COUNT(*) OVER (
        PARTITION BY department
        ORDER BY business_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rows_in_frame
FROM analytics_daily
ORDER BY department, business_date;

-- Generate a complete date spine before calculating calendar-day windows.
-- Missing dates are represented as zero revenue here. This is valid only if
-- absence means zero activity rather than unavailable or unreported activity.
WITH bounds AS (
    SELECT
        MIN(business_date) AS first_date,
        MAX(business_date) AS last_date
    FROM analytics_daily
),
departments AS (
    SELECT DISTINCT department FROM analytics_daily
),
date_spine AS (
    SELECT
        d.department,
        gs.business_date::date AS business_date
    FROM departments AS d
    CROSS JOIN bounds AS b
    CROSS JOIN LATERAL generate_series(
        b.first_date,
        b.last_date,
        INTERVAL '1 day'
    ) AS gs(business_date)
),
daily_completed AS (
    SELECT
        department,
        business_date,
        SUM(revenue) FILTER (WHERE status = 'completed') AS completed_revenue,
        COUNT(*) AS observed_records
    FROM analytics_daily
    GROUP BY department, business_date
),
dense_series AS (
    SELECT
        s.department,
        s.business_date,
        COALESCE(d.completed_revenue, 0::numeric) AS completed_revenue,
        COALESCE(d.observed_records, 0) AS observed_records
    FROM date_spine AS s
    LEFT JOIN daily_completed AS d
        ON d.department = s.department
       AND d.business_date = s.business_date
)
SELECT
    department,
    business_date,
    completed_revenue,
    observed_records,
    SUM(completed_revenue) OVER (
        PARTITION BY department
        ORDER BY business_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS completed_revenue_last_seven_calendar_days,
    AVG(completed_revenue) OVER (
        PARTITION BY department
        ORDER BY business_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS average_completed_revenue_last_seven_calendar_days
FROM dense_series
ORDER BY department, business_date;

-- Gaps and islands: subtract the row number from the date to create a stable
-- group key for consecutive dates. Duplicate dates are removed first because
-- this query identifies observed reporting dates, not individual records.
WITH observed_dates AS (
    SELECT DISTINCT department, business_date
    FROM analytics_daily
),
numbered AS (
    SELECT
        department,
        business_date,
        business_date
            - ROW_NUMBER() OVER (
                PARTITION BY department
                ORDER BY business_date
              )::integer AS island_key
    FROM observed_dates
)
SELECT
    department,
    MIN(business_date) AS island_start,
    MAX(business_date) AS island_end,
    COUNT(*) AS consecutive_days
FROM numbered
GROUP BY department, island_key
ORDER BY department, island_start;

-- Detect all missing date intervals within an explicit inclusive reporting
-- range. Unlike islands over observed rows, this also finds leading and
-- trailing gaps inside the selected range.
WITH reporting_bounds AS (
    SELECT DATE '2026-09-01' AS first_date, DATE '2026-09-17' AS last_date
),
departments AS (
    SELECT DISTINCT department FROM analytics_daily
),
calendar AS (
    SELECT
        d.department,
        gs.business_date::date AS business_date
    FROM departments AS d
    CROSS JOIN reporting_bounds AS b
    CROSS JOIN LATERAL generate_series(
        b.first_date,
        b.last_date,
        INTERVAL '1 day'
    ) AS gs(business_date)
),
missing_dates AS (
    SELECT c.department, c.business_date
    FROM calendar AS c
    LEFT JOIN (
        SELECT DISTINCT department, business_date
        FROM analytics_daily
    ) AS o
      ON o.department = c.department
     AND o.business_date = c.business_date
    WHERE o.business_date IS NULL
),
numbered_missing AS (
    SELECT
        department,
        business_date,
        business_date
            - ROW_NUMBER() OVER (
                PARTITION BY department
                ORDER BY business_date
              )::integer AS gap_key
    FROM missing_dates
)
SELECT
    department,
    MIN(business_date) AS gap_start,
    MAX(business_date) AS gap_end,
    COUNT(*) AS missing_calendar_days
FROM numbered_missing
GROUP BY department, gap_key
ORDER BY department, gap_start;

-- Consecutive integer islands use the same difference-key principle:
-- integer_value - ROW_NUMBER() is constant within a consecutive run.
WITH ticket_events(ticket_id) AS (
    VALUES (100), (101), (102), (105), (108), (109), (110)
),
numbered_tickets AS (
    SELECT
        ticket_id,
        ticket_id - ROW_NUMBER() OVER (ORDER BY ticket_id)::integer AS island_key
    FROM ticket_events
)
SELECT
    MIN(ticket_id) AS first_ticket,
    MAX(ticket_id) AS last_ticket,
    COUNT(*) AS consecutive_ticket_count
FROM numbered_tickets
GROUP BY island_key
ORDER BY first_ticket;

-- Data-quality query: a missing date and a recorded zero-revenue date are
-- different conditions. This report distinguishes absent records from rows
-- whose recorded revenue happens to be zero.
WITH date_spine AS (
    SELECT gs.business_date::date AS business_date
    FROM generate_series(
        DATE '2026-09-01',
        DATE '2026-09-17',
        INTERVAL '1 day'
    ) AS gs(business_date)
)
SELECT
    s.business_date,
    d.revenue,
    d.status,
    CASE
        WHEN d.record_id IS NULL THEN 'missing_record'
        WHEN d.revenue = 0 THEN 'recorded_zero_revenue'
        ELSE 'recorded_nonzero_revenue'
    END AS observation_state
FROM date_spine AS s
LEFT JOIN analytics_daily AS d
    ON d.business_date = s.business_date
   AND d.department = 'Operations'
ORDER BY s.business_date;

-- A failed constraint is demonstrated in a nested block. PostgreSQL rolls
-- back the failed statement while allowing the outer transaction to continue.
DO $$
BEGIN
    BEGIN
        INSERT INTO analytics_daily
            (business_date, department, revenue, orders, status)
        VALUES
            ('2026-09-18', 'Operations', -25.00, 1, 'completed');
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Expected rejection: negative revenue violates CHECK.';
    END;

    BEGIN
        INSERT INTO analytics_daily
            (business_date, department, revenue, orders, status)
        VALUES
            ('2026-09-01', 'Operations', 10.00, 1, 'completed');
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'Expected rejection: duplicate department/date.';
    END;
END;
$$;

ROLLBACK;
