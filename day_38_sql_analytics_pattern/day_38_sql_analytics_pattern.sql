-- PostgreSQL-compatible SQL Analytics Patterns
--
-- The model represents product analytics facts and dimensions needed for:
-- Top-N analysis, cohort preparation, retention, funnel analysis, and
-- behavioral segmentation.
--
-- The design deliberately uses database constraints for data integrity and
-- CTEs for analytical preparation. Window functions are used where ranking
-- depends on an ordered result set.

DROP SCHEMA IF EXISTS sql_analytics_patterns CASCADE;
CREATE SCHEMA sql_analytics_patterns;
SET search_path TO sql_analytics_patterns;

CREATE TABLE users (
    user_id              BIGSERIAL PRIMARY KEY,
    signup_at            TIMESTAMPTZ NOT NULL,
    country              CHAR(2) NOT NULL,
    acquisition_channel  TEXT NOT NULL,
    CHECK (country ~ '^[A-Z]{2}$'),
    CHECK (acquisition_channel IN ('organic', 'paid', 'referral'))
);

CREATE TABLE products (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    CHECK (length(trim(product_name)) > 0)
);

CREATE TABLE events (
    event_id      BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(user_id),
    occurred_at   TIMESTAMPTZ NOT NULL,
    event_name    TEXT NOT NULL,
    amount        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    CHECK (amount >= 0),
    CHECK (
        event_name IN (
            'signup',
            'view_product',
            'add_to_cart',
            'checkout_started',
            'purchase',
            'login'
        )
    ),
    CHECK (
        event_name = 'purchase'
        OR amount = 0
    )
);

CREATE INDEX idx_events_user_time
    ON events (user_id, occurred_at);

CREATE INDEX idx_events_name_time
    ON events (event_name, occurred_at);

CREATE INDEX idx_users_signup
    ON users (signup_at);

INSERT INTO users
    (user_id, signup_at, country, acquisition_channel)
VALUES
    (1, '2026-01-02 09:00:00+00', 'IN', 'organic'),
    (2, '2026-01-03 09:00:00+00', 'IN', 'paid'),
    (3, '2026-01-08 09:00:00+00', 'US', 'organic'),
    (4, '2026-01-15 09:00:00+00', 'IN', 'referral'),
    (5, '2026-02-02 09:00:00+00', 'DE', 'paid'),
    (6, '2026-02-05 09:00:00+00', 'IN', 'organic'),
    (7, '2026-02-09 09:00:00+00', 'US', 'paid'),
    (8, '2026-02-20 09:00:00+00', 'IN', 'referral'),
    (9, '2026-03-01 09:00:00+00', 'IN', 'organic'),
    (10, '2026-03-04 09:00:00+00', 'DE', 'paid'),
    (11, '2026-03-11 09:00:00+00', 'US', 'referral'),
    (12, '2026-03-20 09:00:00+00', 'IN', 'organic');

INSERT INTO products
    (product_id, product_name, category)
VALUES
    ('P100', 'Analytics Platform', 'software'),
    ('P200', 'Operations Suite', 'software'),
    ('P300', 'Data Connector', 'integration'),
    ('P400', 'Audit Module', 'governance'),
    ('P500', 'Forecasting Module', 'analytics');

INSERT INTO events
    (user_id, occurred_at, event_name, amount)
VALUES
    (1, '2026-01-02 09:00+00', 'signup', 0),
    (1, '2026-01-02 09:10+00', 'view_product', 0),
    (1, '2026-01-02 09:20+00', 'add_to_cart', 0),
    (1, '2026-01-02 09:30+00', 'checkout_started', 0),
    (1, '2026-01-02 09:40+00', 'purchase', 300),
    (1, '2026-02-02 10:00+00', 'login', 0),
    (1, '2026-03-02 10:00+00', 'login', 0),

    (2, '2026-01-03 09:00+00', 'signup', 0),
    (2, '2026-01-03 09:10+00', 'view_product', 0),
    (2, '2026-01-03 09:20+00', 'add_to_cart', 0),
    (2, '2026-01-03 09:30+00', 'checkout_started', 0),
    (2, '2026-01-03 09:40+00', 'purchase', 180),

    (3, '2026-01-08 09:00+00', 'signup', 0),
    (3, '2026-01-08 09:10+00', 'view_product', 0),
    (3, '2026-02-08 09:00+00', 'login', 0),

    (4, '2026-01-15 09:00+00', 'signup', 0),
    (4, '2026-01-15 09:10+00', 'view_product', 0),
    (4, '2026-01-15 09:20+00', 'add_to_cart', 0),

    (5, '2026-02-02 09:00+00', 'signup', 0),
    (5, '2026-02-02 09:10+00', 'view_product', 0),
    (5, '2026-02-02 09:20+00', 'add_to_cart', 0),
    (5, '2026-02-02 09:30+00', 'checkout_started', 0),
    (5, '2026-02-02 09:40+00', 'purchase', 230),
    (5, '2026-03-02 09:00+00', 'login', 0),

    (6, '2026-02-05 09:00+00', 'signup', 0),
    (6, '2026-02-05 09:10+00', 'view_product', 0),
    (6, '2026-03-05 09:00+00', 'login', 0),

    (7, '2026-02-09 09:00+00', 'signup', 0),
    (7, '2026-02-09 09:10+00', 'view_product', 0),

    (8, '2026-02-20 09:00+00', 'signup', 0),
    (8, '2026-02-20 09:10+00', 'view_product', 0),
    (8, '2026-02-20 09:20+00', 'add_to_cart', 0),

    (9, '2026-03-01 09:00+00', 'signup', 0),
    (9, '2026-03-01 09:10+00', 'view_product', 0),
    (9, '2026-03-01 09:20+00', 'add_to_cart', 0),
    (9, '2026-03-01 09:30+00', 'checkout_started', 0),
    (9, '2026-03-01 09:40+00', 'purchase', 245),

    (10, '2026-03-04 09:00+00', 'signup', 0),
    (10, '2026-03-04 09:10+00', 'view_product', 0),
    (10, '2026-03-04 09:20+00', 'add_to_cart', 0),
    (10, '2026-03-04 09:30+00', 'checkout_started', 0),
    (10, '2026-03-04 09:40+00', 'purchase', 250),

    (11, '2026-03-11 09:00+00', 'signup', 0),
    (11, '2026-03-11 09:10+00', 'view_product', 0),

    (12, '2026-03-20 09:00+00', 'signup', 0),
    (12, '2026-03-20 09:10+00', 'view_product', 0),
    (12, '2026-03-20 09:20+00', 'add_to_cart', 0);

-- Product revenue is kept in an analytical CTE instead of being stored as a
-- product attribute because revenue is an observed transactional measure.
WITH product_revenue AS (
    SELECT
        e.event_name,
        (e.user_id % 5) + 1 AS product_sequence,
        SUM(e.amount) AS revenue
    FROM events e
    WHERE e.event_name = 'purchase'
    GROUP BY e.event_name, (e.user_id % 5) + 1
),
ranked_products AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        COALESCE(pr.revenue, 0) AS revenue,
        DENSE_RANK() OVER (
            ORDER BY COALESCE(pr.revenue, 0) DESC
        ) AS revenue_rank
    FROM products p
    LEFT JOIN product_revenue pr
        ON pr.product_sequence = regexp_replace(p.product_id, '\D', '', 'g')::integer
)
SELECT
    product_id,
    product_name,
    category,
    revenue,
    revenue_rank
FROM ranked_products
WHERE revenue_rank <= 3
ORDER BY revenue_rank, product_id;

-- Cohort preparation:
-- The signup month is computed once and carried into later analytical CTEs.
WITH cohort_users AS (
    SELECT
        u.user_id,
        u.signup_at::date AS signup_date,
        date_trunc('month', u.signup_at)::date AS cohort_month,
        u.country,
        u.acquisition_channel
    FROM users u
)
SELECT *
FROM cohort_users
ORDER BY cohort_month, user_id;

-- Monthly retention:
-- Activity is deduplicated at user/cohort/period level before aggregation.
-- This prevents a user generating ten login events from being counted ten times.
WITH cohort_users AS (
    SELECT
        user_id,
        date_trunc('month', signup_at)::date AS cohort_month
    FROM users
),
activity AS (
    SELECT DISTINCT
        c.user_id,
        c.cohort_month,
        (
            EXTRACT(YEAR FROM age(date_trunc('month', e.occurred_at),
                                  c.cohort_month)) * 12
            +
            EXTRACT(MONTH FROM age(date_trunc('month', e.occurred_at),
                                   c.cohort_month))
        )::integer AS period_number
    FROM cohort_users c
    JOIN events e
        ON e.user_id = c.user_id
    WHERE e.event_name IN (
        'login',
        'view_product',
        'add_to_cart',
        'purchase'
    )
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM cohort_users
    GROUP BY cohort_month
),
retained AS (
    SELECT
        cohort_month,
        period_number,
        COUNT(DISTINCT user_id) AS retained_users
    FROM activity
    WHERE period_number >= 0
    GROUP BY cohort_month, period_number
)
SELECT
    r.cohort_month,
    r.period_number,
    s.cohort_size,
    r.retained_users,
    ROUND(
        100.0 * r.retained_users / NULLIF(s.cohort_size, 0),
        1
    ) AS retention_pct
FROM retained r
JOIN cohort_sizes s
    ON s.cohort_month = r.cohort_month
ORDER BY r.cohort_month, r.period_number;

-- Funnel analysis:
-- Each stage counts DISTINCT users. Raw event counts would overstate the
-- funnel when a user views a product or retries checkout multiple times.
WITH funnel AS (
    SELECT
        COUNT(DISTINCT user_id)
            FILTER (WHERE event_name = 'signup') AS signup_users,
        COUNT(DISTINCT user_id)
            FILTER (WHERE event_name = 'view_product') AS product_view_users,
        COUNT(DISTINCT user_id)
            FILTER (WHERE event_name = 'add_to_cart') AS cart_users,
        COUNT(DISTINCT user_id)
            FILTER (WHERE event_name = 'checkout_started') AS checkout_users,
        COUNT(DISTINCT user_id)
            FILTER (WHERE event_name = 'purchase') AS purchase_users
    FROM events
)
SELECT
    stage,
    users,
    ROUND(
        100.0 * users
        / NULLIF(LAG(users) OVER (ORDER BY stage_order), 0),
        1
    ) AS conversion_from_previous_pct
FROM (
    SELECT 1 AS stage_order, 'signup' AS stage,
           signup_users AS users FROM funnel
    UNION ALL
    SELECT 2, 'product_view', product_view_users FROM funnel
    UNION ALL
    SELECT 3, 'cart', cart_users FROM funnel
    UNION ALL
    SELECT 4, 'checkout', checkout_users FROM funnel
    UNION ALL
    SELECT 5, 'purchase', purchase_users FROM funnel
) ordered_funnel
ORDER BY stage_order;

-- User segmentation:
-- Segmentation is built from user-level measures first. This keeps business
-- rules auditable and prevents event-level classifications from being mixed
-- with user-level outcomes.
WITH user_metrics AS (
    SELECT
        u.user_id,
        u.country,
        u.acquisition_channel,
        COUNT(*) FILTER (
            WHERE e.event_name IN ('login', 'view_product', 'add_to_cart')
        ) AS activity_events,
        COUNT(*) FILTER (
            WHERE e.event_name = 'purchase'
        ) AS purchases,
        COALESCE(SUM(e.amount) FILTER (
            WHERE e.event_name = 'purchase'
        ), 0) AS revenue
    FROM users u
    LEFT JOIN events e
        ON e.user_id = u.user_id
    GROUP BY
        u.user_id,
        u.country,
        u.acquisition_channel
),
segmented AS (
    SELECT
        *,
        CASE
            WHEN purchases >= 2 OR revenue >= 300
                THEN 'high_value'
            WHEN purchases >= 1
                THEN 'buyer'
            WHEN activity_events >= 3
                THEN 'engaged_non_buyer'
            ELSE 'low_activity'
        END AS segment
    FROM user_metrics
)
SELECT
    segment,
    COUNT(*) AS users,
    COUNT(*) FILTER (WHERE purchases > 0) AS buyers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE purchases > 0)
        / NULLIF(COUNT(*), 0),
        1
    ) AS buyer_rate_pct,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(AVG(revenue), 2) AS average_revenue_per_user
FROM segmented
GROUP BY segment
ORDER BY total_revenue DESC;

-- Segment performance by acquisition channel:
-- This is a second-level segmentation because channel is a user dimension
-- while segment is behavior derived from event facts.
WITH user_metrics AS (
    SELECT
        u.user_id,
        u.acquisition_channel,
        COUNT(*) FILTER (
            WHERE e.event_name IN ('login', 'view_product', 'add_to_cart')
        ) AS activity_events,
        COUNT(*) FILTER (
            WHERE e.event_name = 'purchase'
        ) AS purchases,
        COALESCE(
            SUM(e.amount) FILTER (WHERE e.event_name = 'purchase'),
            0
        ) AS revenue
    FROM users u
    LEFT JOIN events e
        ON e.user_id = u.user_id
    GROUP BY u.user_id, u.acquisition_channel
),
segmented AS (
    SELECT
        *,
        CASE
            WHEN purchases >= 2 OR revenue >= 300 THEN 'high_value'
            WHEN purchases >= 1 THEN 'buyer'
            WHEN activity_events >= 3 THEN 'engaged_non_buyer'
            ELSE 'low_activity'
        END AS segment
    FROM user_metrics
)
SELECT
    acquisition_channel,
    segment,
    COUNT(*) AS users,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(AVG(revenue), 2) AS average_revenue
FROM segmented
GROUP BY acquisition_channel, segment
ORDER BY acquisition_channel, revenue DESC;

-- Window-function comparison:
-- ROW_NUMBER selects exactly one row per rank position, while RANK leaves
-- gaps after ties and DENSE_RANK does not. The distinction matters in Top-N
-- reporting when equal metrics exist.
WITH metrics(product_id, revenue) AS (
    VALUES
        ('P100', 18200.00),
        ('P200', 15700.00),
        ('P300', 15700.00),
        ('P400', 11900.00),
        ('P500', 9400.00)
)
SELECT
    product_id,
    revenue,
    ROW_NUMBER() OVER (ORDER BY revenue DESC, product_id) AS row_number_rank,
    RANK() OVER (ORDER BY revenue DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS dense_rank
FROM metrics
ORDER BY revenue DESC, product_id;

-- Database integrity demonstration:
-- The following statement would fail because a non-purchase event cannot
-- contain a positive amount. It is intentionally kept commented so that the
-- complete script remains executable.
--
-- INSERT INTO events (user_id, occurred_at, event_name, amount)
-- VALUES (1, now(), 'login', 50);

-- The following statement would fail because the referenced user does not exist.
--
-- INSERT INTO events (user_id, occurred_at, event_name)
-- VALUES (999999, now(), 'login');

-- A transaction can combine analytical staging changes while preserving
-- atomicity. Temporary analytical tables are useful when a complex workflow
-- requires several downstream queries.
BEGIN;

CREATE TEMP TABLE monthly_user_activity AS
SELECT
    user_id,
    date_trunc('month', occurred_at)::date AS activity_month,
    COUNT(*) AS event_count,
    COUNT(*) FILTER (WHERE event_name = 'purchase') AS purchase_events,
    COALESCE(SUM(amount) FILTER (WHERE event_name = 'purchase'), 0) AS revenue
FROM events
GROUP BY
    user_id,
    date_trunc('month', occurred_at)::date;

CREATE INDEX idx_monthly_user_activity
    ON monthly_user_activity (activity_month, user_id);

SELECT
    activity_month,
    COUNT(*) AS active_user_rows,
    SUM(purchase_events) AS purchases,
    ROUND(SUM(revenue), 2) AS revenue
FROM monthly_user_activity
GROUP BY activity_month
ORDER BY activity_month;

COMMIT;
