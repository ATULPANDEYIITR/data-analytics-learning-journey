-- PostgreSQL 15+
-- Repository inventory and deployment analytics using relational data,
-- arrays, JSONB, constraints, views, indexing, and transactional operations.

BEGIN;

CREATE SCHEMA IF NOT EXISTS data_structures_lab;
SET search_path TO data_structures_lab, public;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL CHECK (btrim(language) <> ''),
    stars INTEGER NOT NULL DEFAULT 0 CHECK (stars >= 0),
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    topics TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    maintainers TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        archived OR cardinality(maintainers) > 0
    ),
    CHECK (
        NOT EXISTS (
            SELECT 1
            FROM unnest(topics) AS topic
            WHERE topic IS NULL OR btrim(topic) = ''
        )
    ),
    CHECK (
        NOT EXISTS (
            SELECT 1
            FROM unnest(maintainers) AS maintainer
            WHERE maintainer IS NULL OR btrim(maintainer) = ''
        )
    ),
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE deployment_regions (
    region_code TEXT PRIMARY KEY,
    display_name TEXT NOT NULL CHECK (btrim(display_name) <> '')
);

CREATE TABLE deployments (
    deployment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    deployment_key TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    status TEXT NOT NULL
        CHECK (status IN ('pending', 'passed', 'failed', 'blocked')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE deployment_region_assignments (
    deployment_id BIGINT NOT NULL
        REFERENCES deployments(deployment_id) ON DELETE CASCADE,
    region_code TEXT NOT NULL
        REFERENCES deployment_regions(region_code),
    PRIMARY KEY (deployment_id, region_code)
);

CREATE TABLE deployment_checks (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    deployment_id BIGINT NOT NULL
        REFERENCES deployments(deployment_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL CHECK (btrim(check_name) <> ''),
    status TEXT NOT NULL
        CHECK (status IN ('pending', 'passed', 'failed')),
    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    UNIQUE (deployment_id, check_name),
    CHECK (jsonb_typeof(details) = 'object')
);

CREATE TABLE release_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    max_check_duration_ms INTEGER NOT NULL
        CHECK (max_check_duration_ms >= 0)
);

CREATE TABLE policy_required_checks (
    policy_id BIGINT NOT NULL
        REFERENCES release_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL CHECK (btrim(check_name) <> ''),
    PRIMARY KEY (policy_id, check_name)
);

CREATE INDEX repositories_language_active_idx
    ON repositories (language)
    WHERE archived = FALSE;

CREATE INDEX repositories_topics_gin_idx
    ON repositories USING GIN (topics);

CREATE INDEX repositories_metadata_gin_idx
    ON repositories USING GIN (metadata);

CREATE INDEX deployments_repository_started_idx
    ON deployments (repository_id, started_at DESC);

CREATE INDEX deployment_checks_status_idx
    ON deployment_checks (status, deployment_id);

CREATE INDEX deployment_checks_details_gin_idx
    ON deployment_checks USING GIN (details);

INSERT INTO repositories
    (name, language, stars, archived, topics, maintainers, metadata)
VALUES
    (
        'market-prism', 'Python', 320, FALSE,
        ARRAY['finance', 'analytics', 'api'],
        ARRAY['Anika', 'Rahul'],
        '{"tier":"production","tests_passing":true}'::JSONB
    ),
    (
        'portfolio-ui', 'JavaScript', 210, FALSE,
        ARRAY['dashboard', 'analytics'],
        ARRAY['Meera'],
        '{"tier":"production","tests_passing":true}'::JSONB
    ),
    (
        'security-audit', 'Python', 145, FALSE,
        ARRAY['security', 'automation'],
        ARRAY['Rahul', 'Dev'],
        '{"tier":"internal","tests_passing":false}'::JSONB
    ),
    (
        'data-warehouse', 'SQL', 88, FALSE,
        ARRAY['analytics', 'data'],
        ARRAY['Anika'],
        '{"tier":"internal","tests_passing":true}'::JSONB
    ),
    (
        'legacy-reports', 'Java', 34, TRUE,
        ARRAY['reporting', 'legacy'],
        ARRAY['Dev'],
        '{"tier":"archived","tests_passing":true}'::JSONB
    );

INSERT INTO deployment_regions (region_code, display_name)
VALUES
    ('ap-south-1', 'Mumbai'),
    ('eu-west-1', 'Ireland'),
    ('us-east-1', 'Northern Virginia');

INSERT INTO release_policies
    (policy_name, environment, enabled, max_check_duration_ms)
VALUES
    ('production-standard', 'production', TRUE, 2000),
    ('staging-standard', 'staging', TRUE, 3000),
    ('development-standard', 'development', TRUE, 5000);

INSERT INTO policy_required_checks (policy_id, check_name)
SELECT policy_id, check_name
FROM release_policies
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan'), ('integration-tests')
) AS required(check_name);

INSERT INTO deployments
    (repository_id, deployment_key, environment, status, finished_at)
SELECT repository_id, 'DEP-901', 'production', 'passed',
       CURRENT_TIMESTAMP
FROM repositories
WHERE name = 'market-prism';

INSERT INTO deployments
    (repository_id, deployment_key, environment, status, finished_at)
SELECT repository_id, 'DEP-902', 'production', 'failed',
       CURRENT_TIMESTAMP
FROM repositories
WHERE name = 'security-audit';

INSERT INTO deployments
    (repository_id, deployment_key, environment, status, finished_at)
SELECT repository_id, 'DEP-903', 'staging', 'pending', NULL
FROM repositories
WHERE name = 'portfolio-ui';

INSERT INTO deployment_region_assignments
    (deployment_id, region_code)
SELECT deployment_id, 'ap-south-1'
FROM deployments
WHERE deployment_key IN ('DEP-901', 'DEP-902', 'DEP-903');

INSERT INTO deployment_region_assignments
    (deployment_id, region_code)
SELECT deployment_id, 'eu-west-1'
FROM deployments
WHERE deployment_key = 'DEP-901';

INSERT INTO deployment_checks
    (deployment_id, check_name, status, duration_ms, details)
SELECT deployment_id, sample.check_name, sample.status,
       sample.duration_ms, sample.details::JSONB
FROM deployments
CROSS JOIN (
    VALUES
        ('DEP-901', 'unit-tests', 'passed', 420,
         '{"suite":"unit","cases":184}'),
        ('DEP-901', 'security-scan', 'passed', 730,
         '{"findings":0,"scanner":"dependency-audit"}'),
        ('DEP-901', 'integration-tests', 'passed', 1200,
         '{"suite":"integration","cases":42}'),
        ('DEP-902', 'unit-tests', 'passed', 350,
         '{"suite":"unit","cases":91}'),
        ('DEP-902', 'security-scan', 'failed', 900,
         '{"findings":3,"severity":"high"}'),
        ('DEP-903', 'unit-tests', 'passed', 280,
         '{"suite":"unit","cases":60}'),
        ('DEP-903', 'security-scan', 'pending', 0,
         '{"scanner":"dependency-audit"}')
) AS sample(
    deployment_key, check_name, status, duration_ms, details
)
WHERE deployments.deployment_key = sample.deployment_key;

-- Arrays represent compact collections, but a normalized child table is
-- preferable when each item needs independent constraints or relationships.
SELECT
    repository_id,
    name,
    language,
    stars,
    topics,
    maintainers
FROM repositories
WHERE archived = FALSE
ORDER BY stars DESC;

-- Unnest converts an array into rows for aggregation.
SELECT
    topic,
    COUNT(*) AS repository_count
FROM repositories
CROSS JOIN LATERAL unnest(topics) AS topic
WHERE archived = FALSE
GROUP BY topic
ORDER BY repository_count DESC, topic;

-- Group repositories by language and exclude archived projects.
SELECT
    language,
    COUNT(*) AS repository_count,
    SUM(stars) AS total_stars,
    AVG(stars)::NUMERIC(10, 2) AS average_stars
FROM repositories
WHERE archived = FALSE
GROUP BY language
ORDER BY total_stars DESC;

-- JSONB extraction and containment support flexible metadata queries.
SELECT name, metadata ->> 'tier' AS tier
FROM repositories
WHERE metadata @> '{"tests_passing":false}'::JSONB;

-- Index check names and statuses for deployment readiness reports.
CREATE OR REPLACE VIEW deployment_check_summary AS
SELECT
    d.deployment_id,
    d.deployment_key,
    r.name AS repository_name,
    d.environment,
    d.status AS deployment_status,
    COUNT(c.check_id) AS total_checks,
    COUNT(*) FILTER (WHERE c.status = 'passed') AS passed_checks,
    COUNT(*) FILTER (WHERE c.status = 'failed') AS failed_checks,
    COUNT(*) FILTER (WHERE c.status = 'pending') AS pending_checks,
    COALESCE(SUM(c.duration_ms), 0) AS total_duration_ms
FROM deployments d
JOIN repositories r
    ON r.repository_id = d.repository_id
LEFT JOIN deployment_checks c
    ON c.deployment_id = d.deployment_id
GROUP BY
    d.deployment_id, d.deployment_key, r.name,
    d.environment, d.status;

SELECT *
FROM deployment_check_summary
ORDER BY deployment_key;

-- A policy evaluation returns one row per deployment, with blockers that
-- distinguish missing checks, unsuccessful checks, excessive durations,
-- disallowed environments, archived repositories, and missing regions.
CREATE OR REPLACE VIEW deployment_policy_evaluation AS
WITH check_results AS (
    SELECT
        d.deployment_id,
        d.deployment_key,
        d.environment,
        d.status AS deployment_status,
        r.name AS repository_name,
        r.archived,
        p.policy_id,
        p.policy_name,
        p.max_check_duration_ms,
        COUNT(c.check_id) AS actual_check_count,
        COALESCE(
            BOOL_AND(c.status = 'passed'),
            FALSE
        ) AS all_present_checks_passed,
        COUNT(c.check_id) FILTER (
            WHERE c.status = 'failed'
        ) AS failed_check_count,
        COUNT(c.check_id) FILTER (
            WHERE c.status = 'pending'
        ) AS pending_check_count,
        COUNT(c.check_id) FILTER (
            WHERE c.duration_ms > p.max_check_duration_ms
        ) AS excessive_duration_count,
        COALESCE(SUM(c.duration_ms), 0) AS total_duration_ms,
        COUNT(DISTINCT dra.region_code) AS assigned_region_count
    FROM deployments d
    JOIN repositories r
        ON r.repository_id = d.repository_id
    LEFT JOIN release_policies p
        ON p.environment = d.environment AND p.enabled = TRUE
    LEFT JOIN deployment_checks c
        ON c.deployment_id = d.deployment_id
    LEFT JOIN deployment_region_assignments dra
        ON dra.deployment_id = d.deployment_id
    GROUP BY
        d.deployment_id, d.deployment_key, d.environment,
        d.status, r.name, r.archived,
        p.policy_id, p.policy_name, p.max_check_duration_ms
),
missing_checks AS (
    SELECT
        cr.deployment_id,
        COUNT(prc.check_name) FILTER (
            WHERE dc.check_id IS NULL
        ) AS missing_check_count
    FROM check_results cr
    LEFT JOIN policy_required_checks prc
        ON prc.policy_id = cr.policy_id
    LEFT JOIN deployment_checks dc
        ON dc.deployment_id = cr.deployment_id
       AND dc.check_name = prc.check_name
    GROUP BY cr.deployment_id
)
SELECT
    cr.deployment_key,
    cr.repository_name,
    cr.environment,
    cr.policy_name,
    cr.total_duration_ms,
    COALESCE(mc.missing_check_count, 0) AS missing_check_count,
    cr.failed_check_count,
    cr.pending_check_count,
    cr.excessive_duration_count,
    cr.assigned_region_count,
    CASE
        WHEN cr.archived THEN 'BLOCKED: archived repository'
        WHEN cr.policy_id IS NULL THEN 'BLOCKED: no active policy'
        WHEN COALESCE(mc.missing_check_count, 0) > 0
            THEN 'BLOCKED: missing required checks'
        WHEN cr.failed_check_count > 0
            THEN 'BLOCKED: failed checks'
        WHEN cr.pending_check_count > 0
            THEN 'BLOCKED: pending checks'
        WHEN cr.excessive_duration_count > 0
            THEN 'BLOCKED: duration limit exceeded'
        WHEN cr.assigned_region_count = 0
            THEN 'BLOCKED: no deployment region'
        WHEN cr.deployment_status <> 'passed'
            THEN 'BLOCKED: deployment not passed'
        ELSE 'ELIGIBLE'
    END AS policy_decision
FROM check_results cr
LEFT JOIN missing_checks mc
    ON mc.deployment_id = cr.deployment_id;

SELECT *
FROM deployment_policy_evaluation
ORDER BY deployment_key;

-- A transaction ensures that deployment state and its checks are changed
-- together. This sample only marks a deployment passed when all mandatory
-- checks exist and have passed under the applicable active policy.
BEGIN;

WITH eligible_deployments AS (
    SELECT evaluation.deployment_key
    FROM deployment_policy_evaluation evaluation
    WHERE evaluation.deployment_key = 'DEP-901'
      AND evaluation.policy_decision = 'ELIGIBLE'
)
UPDATE deployments d
SET status = 'passed',
    finished_at = CURRENT_TIMESTAMP
FROM eligible_deployments e
WHERE d.deployment_key = e.deployment_key;

COMMIT;

-- Constraints expose common invalid data states directly.
DO $$
BEGIN
    BEGIN
        INSERT INTO repositories
            (name, language, stars, archived, maintainers)
        VALUES
            ('invalid-stars-example', 'Python', -1, FALSE, ARRAY['Anika']);
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Negative stars rejected by CHECK constraint.';
    END;

    BEGIN
        INSERT INTO deployment_checks
            (deployment_id, check_name, status, duration_ms)
        SELECT deployment_id, 'unit-tests', 'passed', 100
        FROM deployments
        WHERE deployment_key = 'DEP-901';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'Duplicate check rejected by UNIQUE constraint.';
    END;

    BEGIN
        INSERT INTO deployment_region_assignments
            (deployment_id, region_code)
        SELECT deployment_id, 'unknown-region'
        FROM deployments
        WHERE deployment_key = 'DEP-901';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'Unknown region rejected by FOREIGN KEY constraint.';
    END;
END;
$$;

ROLLBACK;
