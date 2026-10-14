-- PostgreSQL 15+
-- Python Functions learning case study:
-- Function signatures, arguments, defaults, return values, scope-like
-- parameter visibility, higher-order behavior through function composition,
-- and database functions used to evaluate repository governance.
--
-- Execute with psql against a database where the current role may create schema
-- objects. The dedicated schema keeps the example isolated.

BEGIN;

DROP SCHEMA IF EXISTS function_governance CASCADE;
CREATE SCHEMA function_governance;
SET search_path TO function_governance, public;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(repository_name)) > 0),
    CHECK (length(trim(default_branch)) > 0)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_name TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    head_commit TEXT NOT NULL,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (length(trim(head_commit)) > 0)
);

CREATE TABLE reviewers (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    can_approve BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    state TEXT NOT NULL DEFAULT 'open'
        CHECK (state IN ('open', 'draft', 'closed', 'merged')),
    source_up_to_date BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    changed_files INTEGER NOT NULL DEFAULT 0 CHECK (changed_files >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(author)) > 0),
    CHECK (length(trim(title)) > 0),
    CHECK (source_branch_id <> target_branch_id)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_sha TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, commit_sha),
    CHECK (length(trim(commit_sha)) >= 7),
    CHECK (length(trim(commit_message)) > 0)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    review_state TEXT NOT NULL
        CHECK (
            review_state IN (
                'commented',
                'approved',
                'changes_requested',
                'dismissed'
            )
        ),
    review_summary TEXT NOT NULL DEFAULT '',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    comment_body TEXT NOT NULL,
    is_inline BOOLEAN NOT NULL DEFAULT TRUE,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(file_path)) > 0),
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (length(trim(comment_body)) > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    check_state TEXT NOT NULL
        CHECK (check_state IN ('pending', 'passed', 'failed')),
    run_number INTEGER NOT NULL DEFAULT 1 CHECK (run_number > 0),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name, run_number),
    CHECK (
        (check_state = 'pending' AND completed_at IS NULL)
        OR
        (check_state IN ('passed', 'failed') AND completed_at IS NOT NULL)
    )
);

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id),
    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),
    require_up_to_date BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_discussions BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    restrict_direct_pushes BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_pushes BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    administrators_may_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_merge_strategies TEXT[] NOT NULL
        DEFAULT ARRAY['squash']::TEXT[],
    CHECK (cardinality(allowed_merge_strategies) > 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE pull_request_merge_events (
    merge_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id),
    merge_strategy TEXT NOT NULL
        CHECK (merge_strategy IN ('merge_commit', 'squash', 'rebase')),
    merged_by TEXT NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_reviewer_time
    ON reviews(pull_request_id, reviewer_id, submitted_at DESC, review_id DESC);

CREATE INDEX idx_review_comments_unresolved
    ON review_comments(review_id)
    WHERE is_resolved = FALSE;

CREATE INDEX idx_status_checks_latest
    ON status_checks(pull_request_id, check_name, run_number DESC);

-- Parameterized SQL function: defaults apply when optional arguments are omitted.
CREATE OR REPLACE FUNCTION normalize_branch_name(
    input_name TEXT,
    lowercase_name BOOLEAN DEFAULT TRUE
)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    normalized TEXT;
BEGIN
    normalized := trim(input_name);

    IF normalized = '' THEN
        RAISE EXCEPTION 'Branch name cannot be empty';
    END IF;

    IF lowercase_name THEN
        normalized := lower(normalized);
    END IF;

    RETURN normalized;
END;
$$;

-- Scalar return values can be composed in SQL expressions.
CREATE OR REPLACE FUNCTION estimate_review_capacity(
    open_pull_requests INTEGER,
    available_reviewers INTEGER,
    reviews_per_reviewer INTEGER DEFAULT 3
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF open_pull_requests < 0
       OR available_reviewers < 0
       OR reviews_per_reviewer < 0 THEN
        RAISE EXCEPTION 'Capacity inputs cannot be negative';
    END IF;

    IF available_reviewers = 0 OR reviews_per_reviewer = 0 THEN
        RETURN 0;
    END IF;

    RETURN LEAST(
        open_pull_requests,
        available_reviewers * reviews_per_reviewer
    );
END;
$$;

-- This function models the effective latest review per reviewer. A later
-- dismissal or changes-requested event supersedes an earlier approval.
CREATE OR REPLACE FUNCTION effective_review_state(
    target_pr_id BIGINT,
    target_reviewer_id BIGINT
)
RETURNS TEXT
LANGUAGE sql
STABLE
AS $$
    SELECT r.review_state
    FROM reviews AS r
    WHERE r.pull_request_id = target_pr_id
      AND r.reviewer_id = target_reviewer_id
    ORDER BY r.submitted_at DESC, r.review_id DESC
    LIMIT 1;
$$;

-- Higher-order behavior in SQL is represented by reusable functions and
-- composable predicates rather than first-class function values.
CREATE OR REPLACE FUNCTION count_effective_approvals(target_pr_id BIGINT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT count(*)::INTEGER
    FROM reviewers AS reviewer
    WHERE reviewer.is_active
      AND reviewer.can_approve
      AND effective_review_state(target_pr_id, reviewer.reviewer_id) = 'approved';
$$;

CREATE OR REPLACE FUNCTION has_effective_change_request(target_pr_id BIGINT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM reviewers AS reviewer
        WHERE reviewer.is_active
          AND reviewer.can_approve
          AND effective_review_state(target_pr_id, reviewer.reviewer_id)
              = 'changes_requested'
    );
$$;

CREATE OR REPLACE FUNCTION has_unresolved_discussions(target_pr_id BIGINT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM review_comments AS comment
        JOIN reviews AS review USING (review_id)
        WHERE review.pull_request_id = target_pr_id
          AND comment.is_resolved = FALSE
    );
$$;

-- Return a table of blocking conditions. Returning rows is more useful for
-- debugging a policy decision than returning only a Boolean.
CREATE OR REPLACE FUNCTION evaluate_merge_eligibility(target_pr_id BIGINT)
RETURNS TABLE (
    eligible BOOLEAN,
    blocker TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    pr RECORD;
    policy RECORD;
    observed_check RECORD;
    effective_state TEXT;
BEGIN
    SELECT
        request.pull_request_id,
        request.state,
        request.target_branch_id,
        request.source_up_to_date,
        request.has_conflicts,
        target_branch.is_protected,
        target_branch.is_deleted
    INTO pr
    FROM pull_requests AS request
    JOIN branches AS target_branch
      ON target_branch.branch_id = request.target_branch_id
    WHERE request.pull_request_id = target_pr_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Pull Request does not exist'::TEXT;
        RETURN;
    END IF;

    SELECT *
    INTO policy
    FROM branch_protection_policies AS protection
    WHERE protection.branch_id = pr.target_branch_id;

    IF NOT FOUND OR NOT pr.is_protected THEN
        RETURN QUERY SELECT FALSE, 'Target branch has no active protection policy'::TEXT;
        RETURN;
    END IF;

    IF pr.is_deleted THEN
        RETURN QUERY SELECT FALSE, 'Target branch has been deleted'::TEXT;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY SELECT FALSE, 'Pull Request must be open'::TEXT;
    END IF;

    IF pr.has_conflicts THEN
        RETURN QUERY SELECT FALSE, 'Merge conflicts must be resolved'::TEXT;
    END IF;

    IF policy.require_up_to_date AND NOT pr.source_up_to_date THEN
        RETURN QUERY SELECT FALSE, 'Source branch must be synchronized'::TEXT;
    END IF;

    IF has_effective_change_request(target_pr_id) THEN
        RETURN QUERY SELECT FALSE, 'An eligible reviewer requested changes'::TEXT;
    END IF;

    IF count_effective_approvals(target_pr_id) < policy.required_approvals THEN
        RETURN QUERY
        SELECT FALSE,
            format(
                'Approval threshold not met: %s of %s',
                count_effective_approvals(target_pr_id),
                policy.required_approvals
            );
    END IF;

    IF policy.require_resolved_discussions
       AND has_unresolved_discussions(target_pr_id) THEN
        RETURN QUERY SELECT FALSE, 'Review discussions remain unresolved'::TEXT;
    END IF;

    FOR observed_check IN
        SELECT required.check_name, latest.check_state
        FROM required_status_checks AS required
        LEFT JOIN LATERAL (
            SELECT status.check_state
            FROM status_checks AS status
            WHERE status.pull_request_id = target_pr_id
              AND status.check_name = required.check_name
            ORDER BY status.run_number DESC
            LIMIT 1
        ) AS latest ON TRUE
        WHERE required.policy_id = policy.policy_id
    LOOP
        IF observed_check.check_state IS DISTINCT FROM 'passed' THEN
            RETURN QUERY
            SELECT FALSE,
                format(
                    'Required check %s is missing or not passing',
                    observed_check.check_name
                );
        END IF;
    END LOOP;

    RETURN QUERY SELECT TRUE, 'All configured merge conditions are satisfied'::TEXT;
END;
$$;

-- Seed realistic repository governance data.
INSERT INTO repositories (repository_name, default_branch)
VALUES ('payments-platform', 'main');

INSERT INTO branches (
    repository_id, branch_name, is_protected, head_commit
)
SELECT repository_id, 'main', TRUE, 'a100000'
FROM repositories
WHERE repository_name = 'payments-platform';

INSERT INTO branches (
    repository_id, branch_name, is_protected, head_commit
)
SELECT repository_id, 'feature/settlement-validation', FALSE, 'b200000'
FROM repositories
WHERE repository_name = 'payments-platform';

INSERT INTO branches (
    repository_id, branch_name, is_protected, head_commit
)
SELECT repository_id, 'feature/auth-token-expiry', FALSE, 'c300000'
FROM repositories
WHERE repository_name = 'payments-platform';

INSERT INTO reviewers (username, can_approve, is_active)
VALUES
    ('reviewer_ada', TRUE, TRUE),
    ('reviewer_lin', TRUE, TRUE),
    ('automation_bot', FALSE, TRUE),
    ('reviewer_inactive', TRUE, FALSE);

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_up_to_date,
    require_resolved_discussions,
    require_linear_history,
    restrict_direct_pushes,
    restrict_force_pushes,
    restrict_deletion,
    administrators_may_bypass,
    allowed_merge_strategies
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    ARRAY['squash', 'rebase']::TEXT[]
FROM branches
WHERE branch_name = 'main';

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, required.check_name
FROM branch_protection_policies AS policy
JOIN branches AS branch USING (branch_id)
CROSS JOIN (
    VALUES ('build'), ('unit-tests'), ('security-scan')
) AS required(check_name)
WHERE branch.branch_name = 'main';

INSERT INTO pull_requests (
    repository_id,
    author,
    title,
    source_branch_id,
    target_branch_id,
    state,
    source_up_to_date,
    has_conflicts,
    changed_files
)
SELECT
    repository.repository_id,
    'developer_lee',
    'Validate payment settlement boundaries',
    source.branch_id,
    target.branch_id,
    'open',
    TRUE,
    FALSE,
    8
FROM repositories AS repository
JOIN branches AS source
  ON source.repository_id = repository.repository_id
 AND source.branch_name = 'feature/settlement-validation'
JOIN branches AS target
  ON target.repository_id = repository.repository_id
 AND target.branch_name = 'main'
WHERE repository.repository_name = 'payments-platform';

INSERT INTO pull_requests (
    repository_id,
    author,
    title,
    source_branch_id,
    target_branch_id,
    state,
    source_up_to_date,
    has_conflicts,
    changed_files
)
SELECT
    repository.repository_id,
    'developer_kim',
    'Correct authentication token expiry',
    source.branch_id,
    target.branch_id,
    'open',
    FALSE,
    TRUE,
    17
FROM repositories AS repository
JOIN branches AS source
  ON source.repository_id = repository.repository_id
 AND source.branch_name = 'feature/auth-token-expiry'
JOIN branches AS target
  ON target.repository_id = repository.repository_id
 AND target.branch_name = 'main'
WHERE repository.repository_name = 'payments-platform';

INSERT INTO commits (pull_request_id, commit_sha, commit_message)
SELECT pull_request_id, 'b200001', 'Validate settlement input boundaries'
FROM pull_requests
WHERE title = 'Validate payment settlement boundaries';

INSERT INTO commits (pull_request_id, commit_sha, commit_message)
SELECT pull_request_id, 'b200002', 'Reject invalid settlement amounts'
FROM pull_requests
WHERE title = 'Validate payment settlement boundaries';

-- Reviews are append-only events. The latest event per reviewer determines
-- effective state rather than counting every historical approval.
INSERT INTO reviews (
    pull_request_id, reviewer_id, review_state, review_summary, submitted_at
)
SELECT request.pull_request_id, reviewer.reviewer_id, sample.review_state,
       sample.summary, sample.submitted_at
FROM pull_requests AS request
CROSS JOIN (
    VALUES
        ('reviewer_ada', 'approved', 'Settlement boundary review passed',
         TIMESTAMPTZ '2026-10-14 08:00:00+05:30'),
        ('reviewer_lin', 'approved', 'Failure paths reviewed',
         TIMESTAMPTZ '2026-10-14 08:05:00+05:30'),
        ('automation_bot', 'approved', 'Automated review completed',
         TIMESTAMPTZ '2026-10-14 08:06:00+05:30')
) AS sample(username, review_state, summary, submitted_at)
JOIN reviewers AS reviewer
  ON reviewer.username = sample.username
WHERE request.title = 'Validate payment settlement boundaries';

INSERT INTO reviews (
    pull_request_id, reviewer_id, review_state, review_summary, submitted_at
)
SELECT request.pull_request_id, reviewer.reviewer_id, sample.review_state,
       sample.summary, sample.submitted_at
FROM pull_requests AS request
CROSS JOIN (
    VALUES
        ('reviewer_ada', 'approved', 'Initial inspection',
         TIMESTAMPTZ '2026-10-14 07:30:00+05:30'),
        ('reviewer_lin', 'changes_requested', 'Expiry validation is incomplete',
         TIMESTAMPTZ '2026-10-14 08:07:00+05:30')
) AS sample(username, review_state, summary, submitted_at)
JOIN reviewers AS reviewer
  ON reviewer.username = sample.username
WHERE request.title = 'Correct authentication token expiry';

INSERT INTO review_comments (
    review_id, file_path, line_number, comment_body, is_inline, is_resolved
)
SELECT review.review_id,
       'src/auth/token_validator.py',
       88,
       'Validate expiry before accepting the token.',
       TRUE,
       FALSE
FROM reviews AS review
JOIN pull_requests AS request USING (pull_request_id)
JOIN reviewers AS reviewer USING (reviewer_id)
WHERE request.title = 'Correct authentication token expiry'
  AND reviewer.username = 'reviewer_lin';

INSERT INTO status_checks (
    pull_request_id, check_name, check_state, run_number, completed_at
)
SELECT request.pull_request_id, sample.check_name, sample.check_state,
       sample.run_number, sample.completed_at
FROM pull_requests AS request
CROSS JOIN (
    VALUES
        ('build', 'passed', 1, TIMESTAMPTZ '2026-10-14 08:01:00+05:30'),
        ('unit-tests', 'passed', 1, TIMESTAMPTZ '2026-10-14 08:02:00+05:30'),
        ('security-scan', 'passed', 1, TIMESTAMPTZ '2026-10-14 08:03:00+05:30')
) AS sample(check_name, check_state, run_number, completed_at)
WHERE request.title = 'Validate payment settlement boundaries';

INSERT INTO status_checks (
    pull_request_id, check_name, check_state, run_number, completed_at
)
SELECT request.pull_request_id, sample.check_name, sample.check_state,
       sample.run_number, sample.completed_at
FROM pull_requests AS request
CROSS JOIN (
    VALUES
        ('build', 'passed', 1, TIMESTAMPTZ '2026-10-14 08:01:00+05:30'),
        ('unit-tests', 'pending', 1, NULL::TIMESTAMPTZ)
) AS sample(check_name, check_state, run_number, completed_at)
WHERE request.title = 'Correct authentication token expiry';

-- Demonstrate function calls with required and default parameters.
SELECT normalize_branch_name('  Feature/Payment-Validation  ') AS normalized_lowercase;
SELECT normalize_branch_name('  Feature/Payment-Validation  ', FALSE) AS normalized_original_case;
SELECT estimate_review_capacity(20, 4) AS available_review_capacity;
SELECT estimate_review_capacity(20, 0, 3) AS capacity_without_reviewers;

-- Review metrics distinguish eligible approvals from automated and inactive reviewers.
SELECT
    request.pull_request_id,
    request.title,
    count_effective_approvals(request.pull_request_id) AS eligible_approvals,
    has_effective_change_request(request.pull_request_id) AS changes_requested,
    has_unresolved_discussions(request.pull_request_id) AS unresolved_discussions
FROM pull_requests AS request
ORDER BY request.pull_request_id;

-- Evaluate each Pull Request against the branch's current protection policy.
SELECT
    request.pull_request_id,
    request.title,
    decision.eligible,
    decision.blocker
FROM pull_requests AS request
CROSS JOIN LATERAL evaluate_merge_eligibility(request.pull_request_id) AS decision
ORDER BY request.pull_request_id, decision.eligible DESC;

-- Inspect the newest status-check run for every required check.
SELECT
    request.pull_request_id,
    request.title,
    required.check_name,
    latest.check_state,
    latest.run_number
FROM pull_requests AS request
JOIN branches AS target ON target.branch_id = request.target_branch_id
JOIN branch_protection_policies AS policy ON policy.branch_id = target.branch_id
JOIN required_status_checks AS required ON required.policy_id = policy.policy_id
LEFT JOIN LATERAL (
    SELECT check_run.check_state, check_run.run_number
    FROM status_checks AS check_run
    WHERE check_run.pull_request_id = request.pull_request_id
      AND check_run.check_name = required.check_name
    ORDER BY check_run.run_number DESC
    LIMIT 1
) AS latest ON TRUE
ORDER BY request.pull_request_id, required.check_name;

-- A view exposes current merge eligibility without duplicating the policy logic.
CREATE VIEW pull_request_merge_readiness AS
SELECT
    request.pull_request_id,
    request.title,
    request.state,
    count_effective_approvals(request.pull_request_id) AS approval_count,
    has_effective_change_request(request.pull_request_id) AS changes_requested,
    has_unresolved_discussions(request.pull_request_id) AS unresolved_discussions,
    decision.eligible,
    decision.blocker
FROM pull_requests AS request
CROSS JOIN LATERAL evaluate_merge_eligibility(request.pull_request_id) AS decision;

SELECT * FROM pull_request_merge_readiness
ORDER BY pull_request_id, eligible DESC;

-- Database functions evaluate eligibility; they do not independently guarantee
-- that a concurrent merge remains valid. A production merge service should lock
-- the relevant records, recheck policy, record the merge, and update state in
-- one transaction. This script deliberately does not mark an eligible PR merged.

COMMIT;
