-- PostgreSQL-compatible dependency-management data model.
--
-- The schema represents a platform team managing Python applications,
-- environments, packages, dependency constraints, and validation results.
-- Database constraints protect the integrity of dependency metadata while
-- queries evaluate whether an environment satisfies its declared policy.

DROP SCHEMA IF EXISTS python_dependency_governance CASCADE;

CREATE SCHEMA python_dependency_governance;

SET search_path TO python_dependency_governance;

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_name TEXT NOT NULL UNIQUE,
    runtime_name TEXT NOT NULL DEFAULT 'Python',
    minimum_runtime_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT applications_runtime_check
        CHECK (runtime_name = 'Python'),
    CONSTRAINT applications_version_format_check
        CHECK (
            minimum_runtime_version ~ '^[0-9]+\.[0-9]+(\.[0-9]+)?$'
        )
);

CREATE TABLE packages (
    package_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    distribution_name TEXT NOT NULL UNIQUE,
    CONSTRAINT packages_name_check
        CHECK (distribution_name ~ '^[A-Za-z0-9_.-]+$')
);

CREATE TABLE dependency_declarations (
    dependency_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,
    package_id BIGINT NOT NULL
        REFERENCES packages(package_id)
        ON DELETE RESTRICT,
    minimum_version TEXT,
    maximum_exclusive_version TEXT,
    exact_version TEXT,
    declared_by TEXT NOT NULL,
    declared_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT dependency_constraint_presence_check
        CHECK (
            minimum_version IS NOT NULL
            OR maximum_exclusive_version IS NOT NULL
            OR exact_version IS NOT NULL
        ),

    CONSTRAINT dependency_exact_exclusion_check
        CHECK (
            exact_version IS NULL
            OR (
                minimum_version IS NULL
                AND maximum_exclusive_version IS NULL
            )
        ),

    CONSTRAINT dependency_minimum_format_check
        CHECK (
            minimum_version IS NULL
            OR minimum_version ~ '^[0-9]+\.[0-9]+(\.[0-9]+)?$'
        ),

    CONSTRAINT dependency_maximum_format_check
        CHECK (
            maximum_exclusive_version IS NULL
            OR maximum_exclusive_version ~ '^[0-9]+\.[0-9]+(\.[0-9]+)?$'
        ),

    CONSTRAINT dependency_exact_format_check
        CHECK (
            exact_version IS NULL
            OR exact_version ~ '^[0-9]+\.[0-9]+(\.[0-9]+)?$'
        ),

    CONSTRAINT dependency_unique_application_package
        UNIQUE (application_id, package_id)
);

CREATE TABLE environments (
    environment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,
    environment_name TEXT NOT NULL,
    python_version TEXT NOT NULL,
    environment_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT environments_version_format_check
        CHECK (
            python_version ~ '^[0-9]+\.[0-9]+(\.[0-9]+)?$'
        ),

    CONSTRAINT environments_unique_name
        UNIQUE (application_id, environment_name)
);

CREATE TABLE installed_packages (
    environment_id BIGINT NOT NULL
        REFERENCES environments(environment_id)
        ON DELETE CASCADE,
    package_id BIGINT NOT NULL
        REFERENCES packages(package_id)
        ON DELETE RESTRICT,
    installed_version TEXT NOT NULL,
    installed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (environment_id, package_id),

    CONSTRAINT installed_version_format_check
        CHECK (
            installed_version ~ '^[0-9]+\.[0-9]+(\.[0-9]+)?$'
        )
);

CREATE TABLE validation_runs (
    validation_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    environment_id BIGINT NOT NULL
        REFERENCES environments(environment_id)
        ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'RUNNING',

    CONSTRAINT validation_status_check
        CHECK (status IN ('RUNNING', 'PASSED', 'FAILED'))
);

CREATE TABLE validation_findings (
    finding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    validation_run_id BIGINT NOT NULL
        REFERENCES validation_runs(validation_run_id)
        ON DELETE CASCADE,
    package_id BIGINT
        REFERENCES packages(package_id)
        ON DELETE RESTRICT,
    severity TEXT NOT NULL,
    finding_code TEXT NOT NULL,
    message TEXT NOT NULL,

    CONSTRAINT finding_severity_check
        CHECK (severity IN ('INFO', 'WARNING', 'ERROR'))
);

CREATE INDEX idx_dependency_application
    ON dependency_declarations(application_id);

CREATE INDEX idx_installed_package
    ON installed_packages(package_id);

CREATE INDEX idx_validation_environment
    ON validation_runs(environment_id);

CREATE INDEX idx_findings_run_severity
    ON validation_findings(validation_run_id, severity);

INSERT INTO applications (
    application_name,
    minimum_runtime_version
)
VALUES
    ('repository-governance-tool', '3.11.0'),
    ('deployment-auditor', '3.12.0');

INSERT INTO packages (distribution_name)
VALUES
    ('httpx'),
    ('pydantic'),
    ('packaging'),
    ('pytest');

INSERT INTO dependency_declarations (
    application_id,
    package_id,
    minimum_version,
    maximum_exclusive_version,
    declared_by
)
SELECT
    a.application_id,
    p.package_id,
    '0.27.0',
    '1.0.0',
    'platform-engineering'
FROM applications a
JOIN packages p
    ON p.distribution_name = 'httpx'
WHERE a.application_name = 'repository-governance-tool';

INSERT INTO dependency_declarations (
    application_id,
    package_id,
    minimum_version,
    maximum_exclusive_version,
    declared_by
)
SELECT
    a.application_id,
    p.package_id,
    '2.0.0',
    '3.0.0',
    'platform-engineering'
FROM applications a
JOIN packages p
    ON p.distribution_name = 'pydantic'
WHERE a.application_name = 'repository-governance-tool';

INSERT INTO dependency_declarations (
    application_id,
    package_id,
    exact_version,
    declared_by
)
SELECT
    a.application_id,
    p.package_id,
    '8.3.0',
    'release-engineering'
FROM applications a
JOIN packages p
    ON p.distribution_name = 'pytest'
WHERE a.application_name = 'deployment-auditor';

INSERT INTO environments (
    application_id,
    environment_name,
    python_version,
    environment_path
)
SELECT
    application_id,
    'production',
    '3.13.0',
    '/srv/repository-governance/.venv'
FROM applications
WHERE application_name = 'repository-governance-tool';

INSERT INTO environments (
    application_id,
    environment_name,
    python_version,
    environment_path
)
SELECT
    application_id,
    'test-invalid-runtime',
    '3.10.14',
    '/srv/repository-governance/test-env'
FROM applications
WHERE application_name = 'repository-governance-tool';

INSERT INTO environments (
    application_id,
    environment_name,
    python_version,
    environment_path
)
SELECT
    application_id,
    'production',
    '3.12.6',
    '/srv/deployment-auditor/.venv'
FROM applications
WHERE application_name = 'deployment-auditor';

INSERT INTO installed_packages (
    environment_id,
    package_id,
    installed_version
)
SELECT
    e.environment_id,
    p.package_id,
    CASE
        WHEN e.environment_name = 'production'
             AND e.python_version = '3.13.0'
            THEN
                CASE p.distribution_name
                    WHEN 'httpx' THEN '0.28.1'
                    WHEN 'pydantic' THEN '2.9.2'
                END
        ELSE
            CASE p.distribution_name
                WHEN 'httpx' THEN '0.26.0'
                WHEN 'pydantic' THEN '2.9.2'
            END
    END
FROM environments e
JOIN applications a
    ON a.application_id = e.application_id
JOIN packages p
    ON p.distribution_name IN ('httpx', 'pydantic')
WHERE a.application_name = 'repository-governance-tool';

INSERT INTO installed_packages (
    environment_id,
    package_id,
    installed_version
)
SELECT
    e.environment_id,
    p.package_id,
    '8.3.0'
FROM environments e
JOIN applications a
    ON a.application_id = e.application_id
JOIN packages p
    ON p.distribution_name = 'pytest'
WHERE a.application_name = 'deployment-auditor';

-- The following view compares declared dependency ranges with installed
-- package versions. PostgreSQL does not provide semantic-version comparison
-- as a built-in scalar type, so the view converts numeric components into
-- integer arrays before comparison.
CREATE OR REPLACE VIEW dependency_compliance AS
SELECT
    a.application_name,
    e.environment_name,
    e.python_version,
    p.distribution_name,
    ip.installed_version,
    dd.minimum_version,
    dd.maximum_exclusive_version,
    dd.exact_version,
    CASE
        WHEN dd.exact_version IS NOT NULL THEN
            string_to_array(ip.installed_version, '.')::INT[]
                = string_to_array(dd.exact_version, '.')::INT[]
        ELSE
            (
                dd.minimum_version IS NULL
                OR string_to_array(ip.installed_version, '.')::INT[]
                    >= string_to_array(dd.minimum_version, '.')::INT[]
            )
            AND
            (
                dd.maximum_exclusive_version IS NULL
                OR string_to_array(ip.installed_version, '.')::INT[]
                    < string_to_array(
                        dd.maximum_exclusive_version,
                        '.'
                    )::INT[]
            )
    END AS dependency_satisfied
FROM applications a
JOIN environments e
    ON e.application_id = a.application_id
JOIN dependency_declarations dd
    ON dd.application_id = a.application_id
JOIN packages p
    ON p.package_id = dd.package_id
LEFT JOIN installed_packages ip
    ON ip.environment_id = e.environment_id
    AND ip.package_id = p.package_id;

-- Review the state of all application environments.
SELECT
    application_name,
    environment_name,
    python_version,
    distribution_name,
    installed_version,
    dependency_satisfied
FROM dependency_compliance
ORDER BY application_name, environment_name, distribution_name;

-- Find environments containing missing or incompatible dependencies.
SELECT
    application_name,
    environment_name,
    distribution_name,
    installed_version,
    dependency_satisfied
FROM dependency_compliance
WHERE installed_version IS NULL
   OR dependency_satisfied = FALSE
ORDER BY application_name, environment_name;

-- Aggregate compliance at environment level.
SELECT
    application_name,
    environment_name,
    COUNT(*) AS declared_dependencies,
    COUNT(*) FILTER (
        WHERE dependency_satisfied
    ) AS satisfied_dependencies,
    COUNT(*) FILTER (
        WHERE NOT dependency_satisfied
    ) AS failed_dependencies
FROM dependency_compliance
GROUP BY application_name, environment_name
ORDER BY application_name, environment_name;

-- Runtime policy evaluation uses the same numeric-array technique.
SELECT
    a.application_name,
    e.environment_name,
    e.python_version,
    a.minimum_runtime_version,
    string_to_array(e.python_version, '.')::INT[]
        >= string_to_array(a.minimum_runtime_version, '.')::INT[]
        AS runtime_satisfied
FROM applications a
JOIN environments e
    ON e.application_id = a.application_id
ORDER BY a.application_name, e.environment_name;

-- Demonstrate a transaction that records a validation run based on the
-- current dependency state. The run remains atomic: either all findings and
-- its final status are stored, or the transaction is rolled back.
BEGIN;

WITH environment_results AS (
    SELECT
        environment_id,
        BOOL_AND(
            installed_version IS NOT NULL
            AND dependency_satisfied
        ) AS dependencies_pass
    FROM (
        SELECT
            e.environment_id,
            p.distribution_name,
            ip.installed_version,
            CASE
                WHEN dd.exact_version IS NOT NULL THEN
                    string_to_array(ip.installed_version, '.')::INT[]
                        = string_to_array(
                            dd.exact_version,
                            '.'
                        )::INT[]
                ELSE
                    (
                        dd.minimum_version IS NULL
                        OR string_to_array(
                            ip.installed_version,
                            '.'
                        )::INT[]
                        >= string_to_array(
                            dd.minimum_version,
                            '.'
                        )::INT[]
                    )
                    AND
                    (
                        dd.maximum_exclusive_version IS NULL
                        OR string_to_array(
                            ip.installed_version,
                            '.'
                        )::INT[]
                        < string_to_array(
                            dd.maximum_exclusive_version,
                            '.'
                        )::INT[]
                    )
            END AS dependency_satisfied
        FROM environments e
        JOIN applications a
            ON a.application_id = e.application_id
        JOIN dependency_declarations dd
            ON dd.application_id = a.application_id
        JOIN packages p
            ON p.package_id = dd.package_id
        LEFT JOIN installed_packages ip
            ON ip.environment_id = e.environment_id
            AND ip.package_id = p.package_id
    ) checks
    GROUP BY environment_id
)
INSERT INTO validation_runs (
    environment_id,
    completed_at,
    status
)
SELECT
    environment_id,
    CURRENT_TIMESTAMP,
    CASE
        WHEN dependencies_pass THEN 'PASSED'
        ELSE 'FAILED'
    END
FROM environment_results;

COMMIT;

-- Validation results now exist as durable audit records.
SELECT
    vr.validation_run_id,
    a.application_name,
    e.environment_name,
    vr.status,
    vr.started_at,
    vr.completed_at
FROM validation_runs vr
JOIN environments e
    ON e.environment_id = vr.environment_id
JOIN applications a
    ON a.application_id = e.application_id
ORDER BY vr.validation_run_id;
