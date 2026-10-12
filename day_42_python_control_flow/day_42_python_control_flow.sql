-- PostgreSQL 16+ compatible control-flow teaching model.
-- The database models repository workflow records so that SQL control flow
-- can be demonstrated through CASE, conditional filtering, iteration-oriented
-- queries, constraints, transactions, and policy evaluation.

DROP SCHEMA IF EXISTS control_flow_lab CASCADE;
CREATE SCHEMA control_flow_lab;
SET search_path TO control_flow_lab;

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_name TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    state TEXT NOT NULL CHECK (
        state IN ('draft', 'open', 'closed', 'merged')
    ),
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    changed_files INTEGER NOT NULL CHECK (changed_files >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    reviewer_name TEXT NOT NULL UNIQUE
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    review_state TEXT NOT NULL CHECK (
        review_state IN ('commented', 'changes_requested', 'approved')
    ),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, reviewer_id, submitted_at)
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection (
    protection_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL CHECK (required_approvals >= 0),
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_pushes BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_pull_requests_target
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, review_state);

CREATE INDEX idx_status_checks_pr_passed
    ON status_checks(pull_request_id, passed);

INSERT INTO repositories (repository_name)
VALUES ('payment-platform');

INSERT INTO branches (repository_id, branch_name, is_protected)
VALUES
    (1, 'main', TRUE),
    (1, 'feature/auth', FALSE),
    (1, 'feature/billing', FALSE),
    (1, 'feature/docs', FALSE);

INSERT INTO branch_protection (
    branch_id,
    required_approvals,
    require_status_checks,
    restrict_direct_pushes,
    allow_force_push,
    allow_deletion,
    require_linear_history
)
VALUES (1, 2, TRUE, TRUE, FALSE, FALSE, TRUE);

INSERT INTO reviewers (reviewer_name)
VALUES ('alice'), ('bob'), ('carol');

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    state,
    has_conflicts,
    changed_files
)
VALUES
    (1, 2, 1, 'open', FALSE, 7),
    (1, 3, 1, 'open', TRUE, 4),
    (1, 4, 1, 'draft', FALSE, 2);

INSERT INTO reviews (pull_request_id, reviewer_id, review_state)
VALUES
    (1, 1, 'approved'),
    (1, 2, 'approved'),
    (2, 1, 'approved'),
    (2, 2, 'changes_requested'),
    (3, 1, 'commented');

INSERT INTO status_checks (pull_request_id, check_name, passed)
VALUES
    (1, 'unit-tests', TRUE),
    (1, 'lint', TRUE),
    (1, 'security-scan', TRUE),
    (2, 'unit-tests', TRUE),
    (2, 'lint', FALSE),
    (2, 'security-scan', TRUE),
    (3, 'unit-tests', TRUE);

-- CASE expresses if/elif/else-style classification directly in SQL.
SELECT
    pull_request_id,
    state,
    changed_files,
    CASE
        WHEN state = 'draft' THEN 'not ready for merge evaluation'
        WHEN has_conflicts THEN 'blocked by merge conflicts'
        WHEN changed_files = 0 THEN 'blocked because no files changed'
        WHEN changed_files >= 10 THEN 'large change set requires careful review'
        ELSE 'normal change set'
    END AS control_flow_classification
FROM pull_requests
ORDER BY pull_request_id;

-- FILTER performs conditional aggregation. This is preferable to counting
-- every review and then attempting to interpret its state afterward.
SELECT
    pr.pull_request_id,
    COUNT(*) FILTER (
        WHERE r.review_state = 'approved'
    ) AS approvals,
    COUNT(*) FILTER (
        WHERE r.review_state = 'changes_requested'
    ) AS change_requests,
    COUNT(*) FILTER (
        WHERE r.review_state = 'commented'
    ) AS comments
FROM pull_requests AS pr
LEFT JOIN reviews AS r
    ON r.pull_request_id = pr.pull_request_id
GROUP BY pr.pull_request_id
ORDER BY pr.pull_request_id;

-- A CTE calculates status-check failures before the final policy decision.
WITH check_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) AS total_checks,
        COUNT(*) FILTER (WHERE NOT passed) AS failed_checks
    FROM status_checks
    GROUP BY pull_request_id
),
approval_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (
            WHERE review_state = 'approved'
        ) AS approvals
    FROM reviews
    GROUP BY pull_request_id
)
SELECT
    pr.pull_request_id,
    CASE
        WHEN pr.state = 'draft'
            THEN 'BLOCKED: draft pull request'
        WHEN pr.has_conflicts
            THEN 'BLOCKED: conflicts'
        WHEN pr.changed_files = 0
            THEN 'BLOCKED: no changed files'
        WHEN COALESCE(cs.failed_checks, 0) > 0
            THEN 'BLOCKED: failed status check'
        WHEN COALESCE(asum.approvals, 0) < bp.required_approvals
            THEN 'BLOCKED: insufficient approvals'
        ELSE 'MERGE ELIGIBLE'
    END AS merge_decision
FROM pull_requests AS pr
JOIN branches AS target_branch
    ON target_branch.branch_id = pr.target_branch_id
JOIN branch_protection AS bp
    ON bp.branch_id = target_branch.branch_id
LEFT JOIN check_summary AS cs
    ON cs.pull_request_id = pr.pull_request_id
LEFT JOIN approval_summary AS asum
    ON asum.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id;

-- Recursive SQL demonstrates repeated processing over an ordered sequence.
-- It is intentionally used for a finite workflow timeline rather than as a
-- generic replacement for ordinary queries.
WITH RECURSIVE workflow AS (
    SELECT
        1 AS stage,
        'submitted'::TEXT AS state

    UNION ALL

    SELECT
        stage + 1,
        CASE stage
            WHEN 1 THEN 'review'
            WHEN 2 THEN 'checks'
            WHEN 3 THEN 'approval'
            ELSE 'merge'
        END
    FROM workflow
    WHERE stage < 4
)
SELECT stage, state
FROM workflow
ORDER BY stage;

-- Database constraints enforce conditions even when application control flow
-- is incorrect. This transaction demonstrates an atomic policy inspection.
BEGIN;

SELECT
    pr.pull_request_id,
    pr.state,
    bp.required_approvals,
    bp.restrict_direct_pushes,
    bp.allow_force_push,
    bp.allow_deletion,
    bp.require_linear_history
FROM pull_requests AS pr
JOIN branch_protection AS bp
    ON bp.branch_id = pr.target_branch_id
WHERE pr.pull_request_id = 1
FOR UPDATE;

COMMIT;

-- This query exposes branch-governance conditions separately so each rule can
-- be inspected instead of hiding every decision inside one boolean expression.
SELECT
    pr.pull_request_id,
    pr.state = 'open' AS is_open,
    NOT pr.has_conflicts AS no_conflicts,
    pr.changed_files > 0 AS has_changes,
    COALESCE(checks.failed_checks, 0) = 0 AS checks_pass,
    COALESCE(approvals.approval_count, 0) >= bp.required_approvals
        AS approvals_pass
FROM pull_requests AS pr
JOIN branch_protection AS bp
    ON bp.branch_id = pr.target_branch_id
LEFT JOIN (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (WHERE NOT passed) AS failed_checks
    FROM status_checks
    GROUP BY pull_request_id
) AS checks
    ON checks.pull_request_id = pr.pull_request_id
LEFT JOIN (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (WHERE review_state = 'approved')
            AS approval_count
    FROM reviews
    GROUP BY pull_request_id
) AS approvals
    ON approvals.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id;
