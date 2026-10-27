-- Data Visualization with Matplotlib
-- PostgreSQL data-preparation and reporting model.
--
-- The database stores visualization-ready observations rather than image
-- rendering instructions. SQL performs validation, aggregation, comparison,
-- and selection of metrics; Matplotlib consumes the resulting data.

DROP SCHEMA IF EXISTS visualization_lab CASCADE;
CREATE SCHEMA visualization_lab;

SET search_path TO visualization_lab;

CREATE TYPE metric_kind AS ENUM (
    'deployments',
    'incidents',
    'lead_time_hours',
    'coverage_percent'
);

CREATE TABLE teams (
    team_id BIGSERIAL PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(team_name)) > 0)
);

CREATE TABLE reporting_periods (
    period_id BIGSERIAL PRIMARY KEY,
    period_name TEXT NOT NULL UNIQUE,
    period_start DATE NOT NULL UNIQUE,
    CHECK (length(trim(period_name)) > 0)
);

CREATE TABLE team_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(team_id)
        ON DELETE CASCADE,
    period_id BIGINT NOT NULL REFERENCES reporting_periods(period_id)
        ON DELETE RESTRICT,
    deployments INTEGER NOT NULL DEFAULT 0,
    incidents INTEGER NOT NULL DEFAULT 0,
    lead_time_hours NUMERIC(10, 2) NOT NULL,
    coverage_percent NUMERIC(5, 2) NOT NULL,

    CONSTRAINT uq_team_period UNIQUE (team_id, period_id),
    CONSTRAINT ck_deployments_nonnegative CHECK (deployments >= 0),
    CONSTRAINT ck_incidents_nonnegative CHECK (incidents >= 0),
    CONSTRAINT ck_lead_time_positive CHECK (lead_time_hours > 0),
    CONSTRAINT ck_coverage_range CHECK (
        coverage_percent BETWEEN 0 AND 100
    )
);

CREATE TABLE chart_definitions (
    chart_id BIGSERIAL PRIMARY KEY,
    chart_name TEXT NOT NULL UNIQUE,
    metric metric_kind NOT NULL,
    scale_type TEXT NOT NULL DEFAULT 'linear',
    y_axis_min NUMERIC,
    y_axis_max NUMERIC,
    show_legend BOOLEAN NOT NULL DEFAULT TRUE,
    show_annotations BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT ck_scale_type CHECK (
        scale_type IN ('linear', 'logarithmic')
    ),
    CONSTRAINT ck_axis_range CHECK (
        y_axis_min IS NULL
        OR y_axis_max IS NULL
        OR y_axis_min <= y_axis_max
    )
);

CREATE INDEX idx_team_metrics_period
    ON team_metrics(period_id);

CREATE INDEX idx_team_metrics_team_period
    ON team_metrics(team_id, period_id);

INSERT INTO teams (team_name)
VALUES
    ('Platform'),
    ('Payments'),
    ('Analytics');

INSERT INTO reporting_periods (period_name, period_start)
VALUES
    ('Jan', DATE '2026-01-01'),
    ('Feb', DATE '2026-02-01'),
    ('Mar', DATE '2026-03-01'),
    ('Apr', DATE '2026-04-01'),
    ('May', DATE '2026-05-01'),
    ('Jun', DATE '2026-06-01');

INSERT INTO team_metrics (
    team_id,
    period_id,
    deployments,
    incidents,
    lead_time_hours,
    coverage_percent
)
SELECT
    t.team_id,
    p.period_id,
    v.deployments,
    v.incidents,
    v.lead_time_hours,
    v.coverage_percent
FROM (
    VALUES
        ('Platform', 'Jan', 42, 8, 18.0, 76.0),
        ('Platform', 'Feb', 48, 7, 16.0, 79.0),
        ('Platform', 'Mar', 53, 6, 14.0, 82.0),
        ('Platform', 'Apr', 61, 5, 12.0, 85.0),
        ('Platform', 'May', 67, 4, 10.5, 88.0),
        ('Platform', 'Jun', 74, 4, 9.2, 91.0),

        ('Payments', 'Jan', 31, 10, 24.0, 71.0),
        ('Payments', 'Feb', 35, 9, 22.0, 74.0),
        ('Payments', 'Mar', 39, 8, 19.0, 77.0),
        ('Payments', 'Apr', 44, 7, 17.0, 80.0),
        ('Payments', 'May', 49, 6, 15.0, 83.0),
        ('Payments', 'Jun', 55, 5, 13.5, 86.0),

        ('Analytics', 'Jan', 25, 5, 20.0, 81.0),
        ('Analytics', 'Feb', 28, 5, 18.0, 83.0),
        ('Analytics', 'Mar', 34, 4, 15.5, 86.0),
        ('Analytics', 'Apr', 38, 3, 13.0, 89.0),
        ('Analytics', 'May', 43, 3, 11.5, 92.0),
        ('Analytics', 'Jun', 47, 2, 10.0, 94.0)
) AS v(
    team_name,
    period_name,
    deployments,
    incidents,
    lead_time_hours,
    coverage_percent
)
JOIN teams t
    ON t.team_name = v.team_name
JOIN reporting_periods p
    ON p.period_name = v.period_name;

INSERT INTO chart_definitions (
    chart_name,
    metric,
    scale_type,
    show_legend,
    show_annotations
)
VALUES
    (
        'Deployment Trend',
        'deployments',
        'linear',
        TRUE,
        TRUE
    ),
    (
        'Incident Comparison',
        'incidents',
        'linear',
        TRUE,
        FALSE
    ),
    (
        'Lead Time',
        'lead_time_hours',
        'logarithmic',
        TRUE,
        TRUE
    ),
    (
        'Coverage Trend',
        'coverage_percent',
        'linear',
        TRUE,
        FALSE
    );

-- Visualization-ready long-form dataset.
CREATE VIEW visualization_dataset AS
SELECT
    t.team_name,
    p.period_name,
    p.period_start,
    m.deployments,
    m.incidents,
    m.lead_time_hours,
    m.coverage_percent
FROM team_metrics m
JOIN teams t
    ON t.team_id = m.team_id
JOIN reporting_periods p
    ON p.period_id = m.period_id
WHERE t.active
ORDER BY p.period_start, t.team_name;

-- Query 1: retrieve a line-chart series.
SELECT
    team_name,
    period_name,
    deployments
FROM visualization_dataset
ORDER BY team_name, period_start;

-- Query 2: validate logarithmic-scale data.
-- Every value must be strictly positive.
SELECT
    team_name,
    period_name,
    lead_time_hours,
    CASE
        WHEN lead_time_hours > 0 THEN 'valid'
        ELSE 'invalid for logarithmic scale'
    END AS scale_status
FROM visualization_dataset
ORDER BY team_name, period_start;

-- Query 3: aggregate values for dashboard KPI cards.
SELECT
    team_name,
    SUM(deployments) AS total_deployments,
    SUM(incidents) AS total_incidents,
    ROUND(AVG(lead_time_hours), 2) AS average_lead_time_hours,
    ROUND(AVG(coverage_percent), 2) AS average_coverage_percent
FROM visualization_dataset
GROUP BY team_name
ORDER BY total_deployments DESC;

-- Query 4: calculate first-to-last changes with window functions.
WITH ordered AS (
    SELECT
        team_name,
        period_start,
        deployments,
        lead_time_hours,
        FIRST_VALUE(deployments) OVER (
            PARTITION BY team_name
            ORDER BY period_start
        ) AS first_deployments,
        LAST_VALUE(deployments) OVER (
            PARTITION BY team_name
            ORDER BY period_start
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND UNBOUNDED FOLLOWING
        ) AS last_deployments,
        FIRST_VALUE(lead_time_hours) OVER (
            PARTITION BY team_name
            ORDER BY period_start
        ) AS first_lead_time,
        LAST_VALUE(lead_time_hours) OVER (
            PARTITION BY team_name
            ORDER BY period_start
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND UNBOUNDED FOLLOWING
        ) AS last_lead_time
    FROM visualization_dataset
)
SELECT DISTINCT
    team_name,
    ROUND(
        ((last_deployments - first_deployments)
        / NULLIF(first_deployments, 0)) * 100,
        2
    ) AS deployment_change_percent,
    ROUND(
        ((last_lead_time - first_lead_time)
        / NULLIF(first_lead_time, 0)) * 100,
        2
    ) AS lead_time_change_percent
FROM ordered
ORDER BY team_name;

-- Query 5: find the highest observed value for annotation.
WITH ranked AS (
    SELECT
        team_name,
        period_name,
        deployments,
        ROW_NUMBER() OVER (
            PARTITION BY team_name
            ORDER BY deployments DESC, period_start
        ) AS ranking
    FROM visualization_dataset
)
SELECT
    team_name,
    period_name,
    deployments
FROM ranked
WHERE ranking = 1
ORDER BY deployments DESC;

-- Query 6: detect values that would make a logarithmic chart invalid.
SELECT
    COUNT(*) AS invalid_log_values
FROM visualization_dataset
WHERE lead_time_hours <= 0;

-- Query 7: produce a compact chart configuration report.
SELECT
    chart_name,
    metric,
    scale_type,
    show_legend,
    show_annotations,
    y_axis_min,
    y_axis_max
FROM chart_definitions
ORDER BY chart_id;

-- Transactional example: add a validated metric atomically.
BEGIN;

WITH target AS (
    SELECT
        t.team_id,
        p.period_id
    FROM teams t
    CROSS JOIN reporting_periods p
    WHERE t.team_name = 'Analytics'
      AND p.period_name = 'Jun'
)
INSERT INTO team_metrics (
    team_id,
    period_id,
    deployments,
    incidents,
    lead_time_hours,
    coverage_percent
)
SELECT
    team_id,
    period_id,
    47,
    2,
    10.0,
    94.0
FROM target
ON CONFLICT (team_id, period_id)
DO UPDATE SET
    deployments = EXCLUDED.deployments,
    incidents = EXCLUDED.incidents,
    lead_time_hours = EXCLUDED.lead_time_hours,
    coverage_percent = EXCLUDED.coverage_percent;

COMMIT;

-- Constraint test query.
-- The following statement is intentionally not executed because it would
-- violate the database rule that lead_time_hours must be positive.
SELECT
    'Invalid examples are rejected by ck_lead_time_positive'
    AS validation_note;

-- A report specifically suitable for a four-panel dashboard.
WITH dashboard AS (
    SELECT
        team_name,
        period_name,
        period_start,
        deployments,
        incidents,
        lead_time_hours,
        coverage_percent
    FROM visualization_dataset
)
SELECT
    period_name,
    team_name,
    deployments,
    incidents,
    lead_time_hours,
    coverage_percent
FROM dashboard
ORDER BY period_start, team_name;
