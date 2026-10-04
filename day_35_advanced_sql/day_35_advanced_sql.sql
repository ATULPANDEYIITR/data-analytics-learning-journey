-- Advanced SQL CTEs
-- PostgreSQL 15+ compatible demonstration.
--
-- The schema models a repository-governance domain only because it provides
-- realistic relational structures for demonstrating CTE composition:
-- Pull Requests, Code Review, Approvals, and Branch Protection are separate
-- concepts and are joined only where their facts interact.
--
-- The primary subject is:
--   ordinary CTEs
--   chained/nested CTEs
--   recursive CTEs
--   reusable query logic
--   window functions inside CTEs
--   CTE-based validation
--   data-modifying statements using CTEs
--   transaction boundaries
--   materialization choices
--   execution-plan considerations

DROP SCHEMA IF EXISTS advanced_cte_case_study CASCADE;
CREATE SCHEMA advanced_cte_case_study;
SET search_path TO advanced_cte_case_study;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_name TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    UNIQUE (owner_name, repository_name)
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    team_name TEXT NOT NULL
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    branch_name TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    title TEXT NOT NULL,
    state TEXT NOT NULL
        CHECK (state IN ('draft', 'open', 'closed', 'merged')),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    merged_at TIMESTAMPTZ,
    CHECK (source_branch_id <> target_branch_id)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    commit_sha TEXT NOT NULL UNIQUE,
    parent_sha TEXT,
    author_id BIGINT NOT NULL REFERENCES users(user_id),
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id),
    review_state TEXT NOT NULL
        CHECK (
            review_state IN (
                'commented',
                'approved',
                'changes_requested',
                'dismissed'
            )
        ),
    submitted_at TIMESTAMPTZ NOT NULL,
    dismissed_at TIMESTAMPTZ,
    review_body TEXT
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id),
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    comment_body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE status_checks (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    check_name TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('pending', 'passed', 'failed', 'cancelled')),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    required_approvals INTEGER NOT NULL CHECK (required_approvals >= 0),
    require_status_checks BOOLEAN NOT NULL,
    restrict_direct_push BOOLEAN NOT NULL,
    allow_force_push BOOLEAN NOT NULL,
    allow_deletion BOOLEAN NOT NULL,
    require_conversation_resolution BOOLEAN NOT NULL,
    require_linear_history BOOLEAN NOT NULL
);

CREATE TABLE branch_relationships (
    parent_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    child_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    PRIMARY KEY (parent_branch_id, child_branch_id),
    CHECK (parent_branch_id <> child_branch_id)
);

CREATE INDEX idx_pr_target_state
    ON pull_requests (target_branch_id, state);

CREATE INDEX idx_reviews_pr_reviewer_time
    ON reviews (pull_request_id, reviewer_id, submitted_at DESC);

CREATE INDEX idx_review_comments_review_resolved
    ON review_comments (review_id, resolved);

CREATE INDEX idx_status_checks_pr_status
    ON status_checks (pull_request_id, status);

CREATE INDEX idx_commits_pr_time
    ON commits (pull_request_id, committed_at DESC);

CREATE INDEX idx_branch_relationship_parent
    ON branch_relationships (parent_branch_id);

INSERT INTO repositories (
    owner_name,
    repository_name,
    default_branch
)
VALUES
    ('acme', 'payments-api', 'main'),
    ('acme', 'analytics-platform', 'main');

INSERT INTO users (username, team_name)
VALUES
    ('atul', 'platform'),
    ('maya', 'payments'),
    ('liam', 'security'),
    ('sofia', 'data'),
    ('noah', 'release');

INSERT INTO branches (
    repository_id,
    branch_name,
    is_protected
)
SELECT
    repository_id,
    branch_name,
    is_protected
FROM (
    VALUES
        (1::BIGINT, 'main', TRUE),
        (1::BIGINT, 'feature/payment-timeout', FALSE),
        (1::BIGINT, 'feature/risk-rules', FALSE),
        (1::BIGINT, 'release/2026.10', TRUE),
        (1::BIGINT, 'hotfix/auth', FALSE),
        (2::BIGINT, 'main', TRUE),
        (2::BIGINT, 'feature/cte-report', FALSE)
) AS data(repository_id, branch_name, is_protected);

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    author_id,
    title,
    state,
    created_at,
    updated_at
)
SELECT
    1,
    source.branch_id,
    target.branch_id,
    author.user_id,
    data.title,
    data.state,
    data.created_at,
    data.updated_at
FROM (
    VALUES
        (
            'feature/payment-timeout',
            'main',
            'atul',
            'Increase payment timeout safely',
            'open',
            '2026-10-01 09:00+05:30'::timestamptz,
            '2026-10-05 08:00+05:30'::timestamptz
        ),
        (
            'feature/risk-rules',
            'main',
            'maya',
            'Add fraud risk rules',
            'open',
            '2026-10-02 09:30+05:30'::timestamptz,
            '2026-10-05 08:30+05:30'::timestamptz
        ),
        (
            'hotfix/auth',
            'release/2026.10',
            'liam',
            'Emergency authentication fix',
            'open',
            '2026-10-03 10:00+05:30'::timestamptz,
            '2026-10-05 07:45+05:30'::timestamptz
        )
) AS data(
    source_branch,
    target_branch,
    author,
    title,
    state,
    created_at,
    updated_at
)
JOIN branches AS source
    ON source.branch_name = data.source_branch
JOIN branches AS target
    ON target.branch_name = data.target_branch
JOIN users AS author
    ON author.username = data.author
WHERE source.repository_id = 1
  AND target.repository_id = 1;

INSERT INTO commits (
    pull_request_id,
    commit_sha,
    parent_sha,
    author_id,
    message,
    committed_at
)
SELECT
    pr.pull_request_id,
    data.commit_sha,
    data.parent_sha,
    u.user_id,
    data.message,
    data.committed_at
FROM (
    VALUES
        (
            101::BIGINT,
            'a101',
            NULL::TEXT,
            'atul',
            'Add configurable timeout',
            '2026-10-01 09:10+05:30'::timestamptz
        ),
        (
            101::BIGINT,
            'a102',
            'a101',
            'atul',
            'Add timeout tests',
            '2026-10-02 09:10+05:30'::timestamptz
        ),
        (
            101::BIGINT,
            'a103',
            'a102',
            'atul',
            'Tune integration test',
            '2026-10-05 07:30+05:30'::timestamptz
        ),
        (
            102::BIGINT,
            'b101',
            NULL::TEXT,
            'maya',
            'Add risk rule table',
            '2026-10-02 10:00+05:30'::timestamptz
        ),
        (
            102::BIGINT,
            'b102',
            'b101',
            'maya',
            'Validate risk thresholds',
            '2026-10-03 12:00+05:30'::timestamptz
        ),
        (
            103::BIGINT,
            'c101',
            NULL::TEXT,
            'liam',
            'Patch authentication fallback',
            '2026-10-03 11:00+05:30'::timestamptz
        )
) AS data(
    pull_request_id,
    commit_sha,
    parent_sha,
    username,
    message,
    committed_at
)
JOIN users AS u
    ON u.username = data.username
JOIN pull_requests AS pr
    ON pr.pull_request_id = data.pull_request_id;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    review_state,
    submitted_at,
    review_body
)
SELECT
    data.pull_request_id,
    u.user_id,
    data.review_state,
    data.submitted_at,
    data.review_body
FROM (
    VALUES
        (
            101::BIGINT,
            'maya',
            'approved',
            '2026-10-03 10:00+05:30'::timestamptz,
            'Timeout change is scoped correctly.'
        ),
        (
            101::BIGINT,
            'liam',
            'commented',
            '2026-10-03 11:00+05:30'::timestamptz,
            'Please verify the security-sensitive retry path.'
        ),
        (
            102::BIGINT,
            'liam',
            'changes_requested',
            '2026-10-04 09:00+05:30'::timestamptz,
            'Risk threshold needs a validation guard.'
        ),
        (
            102::BIGINT,
            'sofia',
            'approved',
            '2026-10-04 10:00+05:30'::timestamptz,
            'Data validation looks consistent.'
        ),
        (
            103::BIGINT,
            'atul',
            'approved',
            '2026-10-04 12:00+05:30'::timestamptz,
            'Patch reviewed.'
        )
) AS data(
    pull_request_id,
    username,
    review_state,
    submitted_at,
    review_body
)
JOIN users AS u
    ON u.username = data.username;

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    comment_body,
    resolved,
    created_at
)
VALUES
    (
        2002,
        'retry.py',
        88,
        'The retry path should not amplify failed authentication.',
        TRUE,
        '2026-10-03 11:01+05:30'
    ),
    (
        2003,
        'risk_rules.py',
        42,
        'Reject thresholds outside the configured risk range.',
        FALSE,
        '2026-10-04 09:01+05:30'
    );

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    status,
    completed_at
)
VALUES
    (101, 'unit-tests', 'passed', '2026-10-05 07:00+05:30'),
    (101, 'integration-tests', 'passed', '2026-10-05 07:05+05:30'),
    (101, 'security-scan', 'passed', '2026-10-05 07:10+05:30'),
    (102, 'unit-tests', 'passed', '2026-10-05 07:15+05:30'),
    (102, 'integration-tests', 'failed', '2026-10-05 07:20+05:30'),
    (102, 'security-scan', 'passed', '2026-10-05 07:25+05:30'),
    (103, 'unit-tests', 'passed', '2026-10-05 07:30+05:30'),
    (103, 'security-scan', 'passed', '2026-10-05 07:35+05:30');

INSERT INTO branch_protection (
    branch_id,
    required_approvals,
    require_status_checks,
    restrict_direct_push,
    allow_force_push,
    allow_deletion,
    require_conversation_resolution,
    require_linear_history
)
SELECT
    b.branch_id,
    data.required_approvals,
    data.require_status_checks,
    data.restrict_direct_push,
    data.allow_force_push,
    data.allow_deletion,
    data.require_conversation_resolution,
    data.require_linear_history
FROM (
    VALUES
        ('main', 2, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE),
        ('release/2026.10', 1, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE)
) AS data(
    branch_name,
    required_approvals,
    require_status_checks,
    restrict_direct_push,
    allow_force_push,
    allow_deletion,
    require_conversation_resolution,
    require_linear_history
)
JOIN branches AS b
    ON b.branch_name = data.branch_name
WHERE b.repository_id = 1;

INSERT INTO branch_relationships (
    parent_branch_id,
    child_branch_id
)
SELECT parent.branch_id, child.branch_id
FROM (
    VALUES
        ('main', 'release/2026.10'),
        ('release/2026.10', 'hotfix/auth'),
        ('main', 'feature/payment-timeout'),
        ('main', 'feature/risk-rules')
) AS data(parent_name, child_name)
JOIN branches AS parent
    ON parent.branch_name = data.parent_name
JOIN branches AS child
    ON child.branch_name = data.child_name
WHERE parent.repository_id = 1
  AND child.repository_id = 1;

-- ---------------------------------------------------------------------------
-- Basic CTE
-- ---------------------------------------------------------------------------
-- A CTE is scoped to one statement. It names a result relation so later
-- clauses can consume it without repeating the filtering logic.

WITH open_pull_requests AS (
    SELECT
        pr.pull_request_id,
        pr.title,
        u.username AS author,
        target.branch_name AS target_branch
    FROM pull_requests AS pr
    JOIN users AS u
        ON u.user_id = pr.author_id
    JOIN branches AS target
        ON target.branch_id = pr.target_branch_id
    WHERE pr.state = 'open'
)
SELECT
    pull_request_id,
    title,
    author,
    target_branch
FROM open_pull_requests
WHERE target_branch = 'main'
ORDER BY pull_request_id;

-- ---------------------------------------------------------------------------
-- Chained CTEs
-- ---------------------------------------------------------------------------
-- Each CTE establishes one intermediate relation. This is preferable to
-- duplicating the same aggregate in several places.

WITH
open_prs AS (
    SELECT
        pull_request_id,
        target_branch_id
    FROM pull_requests
    WHERE state = 'open'
),
review_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) AS review_count,
        COUNT(*) FILTER (
            WHERE review_state = 'approved'
        ) AS approval_rows
    FROM reviews
    GROUP BY pull_request_id
),
check_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (
            WHERE status = 'passed'
        ) AS passed_checks,
        COUNT(*) FILTER (
            WHERE status IN ('failed', 'cancelled')
        ) AS failed_checks,
        COUNT(*) FILTER (
            WHERE status = 'pending'
        ) AS pending_checks
    FROM status_checks
    GROUP BY pull_request_id
)
SELECT
    p.pull_request_id,
    COALESCE(r.review_count, 0) AS review_count,
    COALESCE(r.approval_rows, 0) AS approval_rows,
    COALESCE(c.passed_checks, 0) AS passed_checks,
    COALESCE(c.failed_checks, 0) AS failed_checks,
    COALESCE(c.pending_checks, 0) AS pending_checks
FROM open_prs AS p
LEFT JOIN review_summary AS r
    ON r.pull_request_id = p.pull_request_id
LEFT JOIN check_summary AS c
    ON c.pull_request_id = p.pull_request_id
ORDER BY p.pull_request_id;

-- ---------------------------------------------------------------------------
-- Nested CTE logic
-- ---------------------------------------------------------------------------
-- The first stage aggregates review facts. The next stage derives a business
-- classification from that intermediate relation. The final SELECT consumes
-- the classified relation.

WITH review_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) AS review_count,
        COUNT(*) FILTER (
            WHERE review_state = 'approved'
        ) AS approval_count,
        COUNT(*) FILTER (
            WHERE review_state = 'changes_requested'
        ) AS change_request_count
    FROM reviews
    GROUP BY pull_request_id
),
review_condition AS (
    SELECT
        pull_request_id,
        review_count,
        approval_count,
        change_request_count,
        CASE
            WHEN change_request_count > 0
                THEN 'review-action-required'
            WHEN approval_count > 0
                THEN 'approval-present'
            ELSE 'review-pending'
        END AS condition
    FROM review_summary
)
SELECT *
FROM review_condition
ORDER BY pull_request_id;

-- ---------------------------------------------------------------------------
-- CTE with a window function
-- ---------------------------------------------------------------------------
-- GROUP BY collapses rows. ROW_NUMBER preserves the individual rows while
-- assigning a position within each Pull Request/reviewer partition.

WITH ranked_reviews AS (
    SELECT
        r.review_id,
        r.pull_request_id,
        r.reviewer_id,
        r.review_state,
        r.submitted_at,
        ROW_NUMBER() OVER (
            PARTITION BY r.pull_request_id, r.reviewer_id
            ORDER BY r.submitted_at DESC, r.review_id DESC
        ) AS reviewer_rank
    FROM reviews AS r
)
SELECT
    rr.pull_request_id,
    u.username AS reviewer,
    rr.review_state,
    rr.submitted_at
FROM ranked_reviews AS rr
JOIN users AS u
    ON u.user_id = rr.reviewer_id
WHERE rr.reviewer_rank = 1
ORDER BY rr.pull_request_id, reviewer;

-- ---------------------------------------------------------------------------
-- Reusable approval logic
-- ---------------------------------------------------------------------------
-- An approval should represent the latest decision of an eligible reviewer,
-- rather than every historical approved row. The CTE isolates that rule.

WITH ranked_reviews AS (
    SELECT
        r.review_id,
        r.pull_request_id,
        r.reviewer_id,
        r.review_state,
        r.submitted_at,
        ROW_NUMBER() OVER (
            PARTITION BY r.pull_request_id, r.reviewer_id
            ORDER BY r.submitted_at DESC, r.review_id DESC
        ) AS reviewer_rank
    FROM reviews AS r
),
latest_reviewer_decisions AS (
    SELECT
        pull_request_id,
        reviewer_id,
        review_state
    FROM ranked_reviews
    WHERE reviewer_rank = 1
),
active_approval_counts AS (
    SELECT
        pull_request_id,
        COUNT(*) AS active_approvals
    FROM latest_reviewer_decisions
    WHERE review_state = 'approved'
    GROUP BY pull_request_id
)
SELECT
    pr.pull_request_id,
    pr.title,
    COALESCE(a.active_approvals, 0) AS active_approvals
FROM pull_requests AS pr
LEFT JOIN active_approval_counts AS a
    ON a.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id;

-- ---------------------------------------------------------------------------
-- Recursive CTE: branch hierarchy
-- ---------------------------------------------------------------------------
-- Recursive CTE structure:
--   anchor member: choose the root
--   UNION ALL
--   recursive member: find children of rows already discovered
--
-- PostgreSQL arrays provide a convenient path representation. The membership
-- check prevents a cyclic relationship from causing unbounded recursion.

WITH RECURSIVE branch_tree AS (
    SELECT
        b.branch_id,
        b.branch_name,
        0 AS depth,
        ARRAY[b.branch_id] AS path
    FROM branches AS b
    WHERE b.repository_id = 1
      AND b.branch_name = 'main'

    UNION ALL

    SELECT
        child.branch_id,
        child.branch_name,
        tree.depth + 1,
        tree.path || child.branch_id
    FROM branch_tree AS tree
    JOIN branch_relationships AS relation
        ON relation.parent_branch_id = tree.branch_id
    JOIN branches AS child
        ON child.branch_id = relation.child_branch_id
    WHERE NOT child.branch_id = ANY(tree.path)
)
SELECT
    branch_name,
    depth,
    path
FROM branch_tree
ORDER BY depth, branch_name;

-- ---------------------------------------------------------------------------
-- Recursive CTE: commit ancestry
-- ---------------------------------------------------------------------------
-- This recursion walks a linked list instead of a hierarchy. The anchor is
-- the newest commit for the Pull Request. Each recursive step finds its parent.

WITH RECURSIVE commit_chain AS (
    SELECT
        c.commit_id,
        c.pull_request_id,
        c.commit_sha,
        c.parent_sha,
        0 AS distance
    FROM commits AS c
    WHERE c.pull_request_id = 101
      AND NOT EXISTS (
          SELECT 1
          FROM commits AS newer
          WHERE newer.pull_request_id = c.pull_request_id
            AND newer.parent_sha = c.commit_sha
      )

    UNION ALL

    SELECT
        parent.commit_id,
        parent.pull_request_id,
        parent.commit_sha,
        parent.parent_sha,
        chain.distance + 1
    FROM commit_chain AS chain
    JOIN commits AS parent
        ON parent.pull_request_id = chain.pull_request_id
       AND parent.commit_sha = chain.parent_sha
)
SELECT
    commit_sha,
    parent_sha,
    distance
FROM commit_chain
ORDER BY distance;

-- ---------------------------------------------------------------------------
-- Recursive CTE with explicit depth protection
-- ---------------------------------------------------------------------------
-- Path detection is the preferred semantic protection against graph cycles.
-- A depth ceiling is still useful as a defensive operational bound.

WITH RECURSIVE branch_tree AS (
    SELECT
        b.branch_id,
        b.branch_name,
        0 AS depth,
        ARRAY[b.branch_id] AS path
    FROM branches AS b
    WHERE b.repository_id = 1
      AND b.branch_name = 'main'

    UNION ALL

    SELECT
        child.branch_id,
        child.branch_name,
        tree.depth + 1,
        tree.path || child.branch_id
    FROM branch_tree AS tree
    JOIN branch_relationships AS relation
        ON relation.parent_branch_id = tree.branch_id
    JOIN branches AS child
        ON child.branch_id = relation.child_branch_id
    WHERE NOT child.branch_id = ANY(tree.path)
      AND tree.depth < 100
)
SELECT *
FROM branch_tree
ORDER BY depth, branch_name;

-- ---------------------------------------------------------------------------
-- CTE pipeline for complete merge-eligibility analysis
-- ---------------------------------------------------------------------------
-- The domain boundaries remain explicit:
--
-- Pull Request state:
--     pull_requests
--
-- Code Review:
--     reviews and review_comments
--
-- Approvals:
--     latest_reviewer_decisions and active_approval_counts
--
-- Branch Protection:
--     branch_protection
--
-- CI/status checks:
--     status_checks
--
-- The final CTE is where independent facts are combined.

WITH
protected_targets AS (
    SELECT
        bp.branch_id,
        bp.required_approvals,
        bp.require_status_checks,
        bp.require_conversation_resolution,
        bp.require_linear_history
    FROM branch_protection AS bp
    WHERE bp.enabled = TRUE
),
ranked_reviews AS (
    SELECT
        r.review_id,
        r.pull_request_id,
        r.reviewer_id,
        r.review_state,
        r.submitted_at,
        ROW_NUMBER() OVER (
            PARTITION BY r.pull_request_id, r.reviewer_id
            ORDER BY r.submitted_at DESC, r.review_id DESC
        ) AS reviewer_rank
    FROM reviews AS r
),
latest_reviewer_decisions AS (
    SELECT
        review_id,
        pull_request_id,
        reviewer_id,
        review_state
    FROM ranked_reviews
    WHERE reviewer_rank = 1
),
active_approval_counts AS (
    SELECT
        pull_request_id,
        COUNT(DISTINCT reviewer_id) AS active_approvals
    FROM latest_reviewer_decisions
    WHERE review_state = 'approved'
    GROUP BY pull_request_id
),
status_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) AS total_checks,
        COUNT(*) FILTER (
            WHERE status = 'passed'
        ) AS passed_checks,
        COUNT(*) FILTER (
            WHERE status IN ('failed', 'cancelled')
        ) AS failed_or_cancelled_checks,
        COUNT(*) FILTER (
            WHERE status = 'pending'
        ) AS pending_checks
    FROM status_checks
    GROUP BY pull_request_id
),
conversation_summary AS (
    SELECT
        r.pull_request_id,
        COUNT(*) FILTER (
            WHERE rc.resolved = FALSE
        ) AS unresolved_comments
    FROM reviews AS r
    JOIN review_comments AS rc
        ON rc.review_id = r.review_id
    GROUP BY r.pull_request_id
),
merge_eligibility AS (
    SELECT
        pr.pull_request_id,
        pr.title,
        target.branch_name AS target_branch,
        policy.required_approvals,
        COALESCE(approvals.active_approvals, 0) AS active_approvals,
        COALESCE(status.passed_checks, 0) AS passed_checks,
        COALESCE(status.failed_or_cancelled_checks, 0)
            AS failed_or_cancelled_checks,
        COALESCE(status.pending_checks, 0) AS pending_checks,
        COALESCE(conversations.unresolved_comments, 0)
            AS unresolved_comments,
        CASE
            WHEN pr.state <> 'open'
                THEN 'blocked: Pull Request is not open'
            WHEN COALESCE(approvals.active_approvals, 0)
                    < policy.required_approvals
                THEN 'blocked: approval requirement not met'
            WHEN policy.require_status_checks
                AND (
                    COALESCE(status.failed_or_cancelled_checks, 0) > 0
                    OR COALESCE(status.pending_checks, 0) > 0
                )
                THEN 'blocked: required checks are not green'
            WHEN policy.require_conversation_resolution
                AND COALESCE(conversations.unresolved_comments, 0) > 0
                THEN 'blocked: unresolved review conversations'
            ELSE 'eligible'
        END AS merge_condition
    FROM pull_requests AS pr
    JOIN protected_targets AS policy
        ON policy.branch_id = pr.target_branch_id
    JOIN branches AS target
        ON target.branch_id = pr.target_branch_id
    LEFT JOIN active_approval_counts AS approvals
        ON approvals.pull_request_id = pr.pull_request_id
    LEFT JOIN status_summary AS status
        ON status.pull_request_id = pr.pull_request_id
    LEFT JOIN conversation_summary AS conversations
        ON conversations.pull_request_id = pr.pull_request_id
)
SELECT *
FROM merge_eligibility
ORDER BY pull_request_id;

-- ---------------------------------------------------------------------------
-- CTE for invalid-state detection
-- ---------------------------------------------------------------------------
-- CTEs are useful for audits because each intermediate relation describes one
-- detectable consistency rule.

WITH required_review_counts AS (
    SELECT
        pr.pull_request_id,
        bp.required_approvals
    FROM pull_requests AS pr
    JOIN branch_protection AS bp
        ON bp.branch_id = pr.target_branch_id
    WHERE pr.state = 'open'
      AND bp.enabled = TRUE
),
latest_reviewer_decisions AS (
    SELECT
        r.pull_request_id,
        r.reviewer_id,
        r.review_state,
        ROW_NUMBER() OVER (
            PARTITION BY r.pull_request_id, r.reviewer_id
            ORDER BY r.submitted_at DESC, r.review_id DESC
        ) AS reviewer_rank
    FROM reviews AS r
),
active_approvals AS (
    SELECT
        pull_request_id,
        COUNT(*) AS approvals
    FROM latest_reviewer_decisions
    WHERE reviewer_rank = 1
      AND review_state = 'approved'
    GROUP BY pull_request_id
)
SELECT
    required.pull_request_id,
    required.required_approvals,
    COALESCE(actual.approvals, 0) AS actual_approvals
FROM required_review_counts AS required
LEFT JOIN active_approvals AS actual
    ON actual.pull_request_id = required.pull_request_id
WHERE COALESCE(actual.approvals, 0)
    < required.required_approvals
ORDER BY required.pull_request_id;

-- ---------------------------------------------------------------------------
-- Data-modifying CTE: audit and update
-- ---------------------------------------------------------------------------
-- PostgreSQL supports data-modifying statements inside WITH. All sub-statements
-- execute as one statement and share the statement's transactional context.
--
-- This example records the newest commit timestamp as the Pull Request's
-- updated_at value.

WITH latest_commit AS (
    SELECT
        pull_request_id,
        MAX(committed_at) AS latest_commit_at
    FROM commits
    GROUP BY pull_request_id
)
UPDATE pull_requests AS pr
SET updated_at = latest_commit.latest_commit_at
FROM latest_commit
WHERE latest_commit.pull_request_id = pr.pull_request_id;

-- ---------------------------------------------------------------------------
-- CTE with MATERIALIZED
-- ---------------------------------------------------------------------------
-- MATERIALIZED explicitly requests that PostgreSQL materialize this CTE.
-- It can be useful when a costly intermediate result is referenced multiple
-- times, but it can also prevent beneficial optimizer inlining. It is a
-- performance decision, not a readability requirement.

WITH expensive_review_summary AS MATERIALIZED (
    SELECT
        pull_request_id,
        COUNT(*) AS review_count
    FROM reviews
    GROUP BY pull_request_id
)
SELECT
    pr.pull_request_id,
    pr.title,
    COALESCE(summary.review_count, 0) AS review_count
FROM pull_requests AS pr
LEFT JOIN expensive_review_summary AS summary
    ON summary.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id;

-- ---------------------------------------------------------------------------
-- CTE with NOT MATERIALIZED
-- ---------------------------------------------------------------------------
-- PostgreSQL can inline a suitable CTE. NOT MATERIALIZED explicitly permits
-- this behavior and can allow predicates from the outer query to be pushed
-- into the underlying relation.

WITH candidate_prs AS NOT MATERIALIZED (
    SELECT
        pull_request_id,
        title,
        target_branch_id
    FROM pull_requests
    WHERE state = 'open'
)
SELECT
    pull_request_id,
    title
FROM candidate_prs
WHERE target_branch_id = (
    SELECT branch_id
    FROM branches
    WHERE repository_id = 1
      AND branch_name = 'main'
);

-- ---------------------------------------------------------------------------
-- Recursive CTE using SEARCH
-- ---------------------------------------------------------------------------
-- PostgreSQL supports SEARCH syntax for recursive ordering. The generated
-- ordering column separates traversal ordering from the branch data itself.

WITH RECURSIVE branch_tree(branch_id, branch_name) AS (
    SELECT
        b.branch_id,
        b.branch_name
    FROM branches AS b
    WHERE b.repository_id = 1
      AND b.branch_name = 'main'

    UNION ALL

    SELECT
        child.branch_id,
        child.branch_name
    FROM branch_tree AS tree
    JOIN branch_relationships AS relation
        ON relation.parent_branch_id = tree.branch_id
    JOIN branches AS child
        ON child.branch_id = relation.child_branch_id
)
SEARCH DEPTH FIRST BY branch_id SET traversal_order
SELECT
    branch_id,
    branch_name,
    traversal_order
FROM branch_tree
ORDER BY traversal_order;

-- ---------------------------------------------------------------------------
-- Recursive CTE using CYCLE
-- ---------------------------------------------------------------------------
-- PostgreSQL's CYCLE clause can maintain cycle state automatically. This is
-- useful when the recursive relation is genuinely a graph rather than a
-- guaranteed tree.

WITH RECURSIVE branch_tree(branch_id, branch_name) AS (
    SELECT
        b.branch_id,
        b.branch_name
    FROM branches AS b
    WHERE b.repository_id = 1
      AND b.branch_name = 'main'

    UNION ALL

    SELECT
        child.branch_id,
        child.branch_name
    FROM branch_tree AS tree
    JOIN branch_relationships AS relation
        ON relation.parent_branch_id = tree.branch_id
    JOIN branches AS child
        ON child.branch_id = relation.child_branch_id
)
CYCLE branch_id SET is_cycle USING traversal_path
SELECT
    branch_id,
    branch_name,
    is_cycle,
    traversal_path
FROM branch_tree
ORDER BY branch_id;

-- ---------------------------------------------------------------------------
-- Transactional CTE workflow
-- ---------------------------------------------------------------------------
-- CTEs define relational computation. BEGIN/COMMIT define transactional
-- atomicity. They solve different problems and should not be conflated.

BEGIN;

WITH failed_checks AS (
    SELECT
        pull_request_id,
        COUNT(*) AS failure_count
    FROM status_checks
    WHERE status IN ('failed', 'cancelled')
    GROUP BY pull_request_id
)
UPDATE pull_requests AS pr
SET updated_at = CURRENT_TIMESTAMP
FROM failed_checks
WHERE failed_checks.pull_request_id = pr.pull_request_id;

COMMIT;

-- ---------------------------------------------------------------------------
-- Execution-plan inspection
-- ---------------------------------------------------------------------------
-- EXPLAIN ANALYZE is the practical tool for checking whether a CTE-based query
-- uses indexes and whether an intermediate result is expensive.

EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
WITH open_prs AS (
    SELECT
        pull_request_id,
        target_branch_id
    FROM pull_requests
    WHERE state = 'open'
),
failed_checks AS (
    SELECT
        pull_request_id,
        COUNT(*) AS failures
    FROM status_checks
    WHERE status = 'failed'
    GROUP BY pull_request_id
)
SELECT
    pr.pull_request_id,
    COALESCE(fc.failures, 0) AS failures
FROM open_prs AS pr
LEFT JOIN failed_checks AS fc
    ON fc.pull_request_id = pr.pull_request_id;

-- ---------------------------------------------------------------------------
-- Recursive CTE edge-case query
-- ---------------------------------------------------------------------------
-- A recursive query over arbitrary graph data should account for:
--   cycles
--   very deep paths
--   duplicate relationships
--   missing children
--
-- The following query uses both path membership and a depth bound.

WITH RECURSIVE safe_graph AS (
    SELECT
        b.branch_id,
        b.branch_name,
        0 AS depth,
        ARRAY[b.branch_id] AS path
    FROM branches AS b
    WHERE b.repository_id = 1
      AND b.branch_name = 'main'

    UNION ALL

    SELECT
        child.branch_id,
        child.branch_name,
        graph.depth + 1,
        graph.path || child.branch_id
    FROM safe_graph AS graph
    JOIN branch_relationships AS relation
        ON relation.parent_branch_id = graph.branch_id
    JOIN branches AS child
        ON child.branch_id = relation.child_branch_id
    WHERE NOT child.branch_id = ANY(graph.path)
      AND graph.depth < 100
)
SELECT
    branch_name,
    depth,
    path
FROM safe_graph
ORDER BY depth, branch_name;

-- ---------------------------------------------------------------------------
-- CTEs are statement-scoped
-- ---------------------------------------------------------------------------
-- This is intentionally commented out because it would fail:
--
-- SELECT *
-- FROM open_pull_requests;
--
-- open_pull_requests exists only inside the statement containing its WITH
-- clause. If query logic must become a persistent database object, consider a
-- VIEW, materialized view, SQL function, or stored procedure according to the
-- required lifecycle and performance characteristics.
