-- PostgreSQL 15+
-- Repository governance data model demonstrating database-level error handling,
-- integrity constraints, review policy evaluation, and transactional merging.

BEGIN;

CREATE SCHEMA IF NOT EXISTS repository_governance;
SET search_path TO repository_governance, public;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT repository_name_format
        CHECK (full_name ~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'),
    CONSTRAINT repository_default_branch_not_blank
        CHECK (length(trim(default_branch)) > 0)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_name TEXT NOT NULL,
    head_sha TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CONSTRAINT branch_name_not_blank CHECK (length(trim(branch_name)) > 0),
    CONSTRAINT branch_sha_not_blank CHECK (length(trim(head_sha)) > 0)
);

CREATE TABLE repository_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT username_not_blank CHECK (length(trim(username)) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    number INTEGER NOT NULL CHECK (number > 0),
    author_id BIGINT NOT NULL REFERENCES repository_users(user_id),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    title TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'draft'
        CHECK (state IN ('draft', 'open', 'merged', 'closed')),
    head_sha TEXT NOT NULL,
    base_sha TEXT NOT NULL,
    is_draft BOOLEAN NOT NULL DEFAULT TRUE,
    merge_strategy TEXT
        CHECK (merge_strategy IN ('merge_commit', 'squash', 'rebase')),
    unresolved_threads INTEGER NOT NULL DEFAULT 0
        CHECK (unresolved_threads >= 0),
    base_up_to_date BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    linear_history_possible BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CONSTRAINT pull_request_title_not_blank CHECK (length(trim(title)) > 0),
    CONSTRAINT pull_request_head_not_blank CHECK (length(trim(head_sha)) > 0),
    CONSTRAINT pull_request_base_not_blank CHECK (length(trim(base_sha)) > 0),
    CONSTRAINT pull_request_branches_differ
        CHECK (source_branch_id <> target_branch_id),
    CONSTRAINT merged_timestamp_consistent
        CHECK ((state = 'merged') = (merged_at IS NOT NULL)),
    CONSTRAINT merged_strategy_consistent
        CHECK ((state = 'merged') = (merge_strategy IS NOT NULL))
);

CREATE TABLE pull_request_commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    sha TEXT NOT NULL,
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, sha),
    CONSTRAINT commit_sha_not_blank CHECK (length(trim(sha)) > 0),
    CONSTRAINT commit_message_not_blank CHECK (length(trim(message)) > 0)
);

CREATE TABLE review_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_pattern TEXT NOT NULL,
    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    prohibit_direct_pushes BOOLEAN NOT NULL DEFAULT TRUE,
    prohibit_force_pushes BOOLEAN NOT NULL DEFAULT TRUE,
    prohibit_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    allow_merge_commit BOOLEAN NOT NULL DEFAULT FALSE,
    allow_squash BOOLEAN NOT NULL DEFAULT TRUE,
    allow_rebase BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (repository_id, branch_pattern),
    CHECK (length(trim(branch_pattern)) > 0),
    CHECK (allow_merge_commit OR allow_squash OR allow_rebase)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES review_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE reviewer_eligibility (
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    user_id BIGINT NOT NULL REFERENCES repository_users(user_id),
    can_review BOOLEAN NOT NULL DEFAULT TRUE,
    can_bypass_protection BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (repository_id, user_id)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES repository_users(user_id),
    review_state TEXT NOT NULL
        CHECK (review_state IN ('commented', 'approved', 'changes_requested')),
    commit_sha TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMPTZ,
    dismissal_reason TEXT,
    CONSTRAINT dismissal_metadata_consistent
        CHECK (
            (dismissed_at IS NULL AND dismissal_reason IS NULL)
            OR
            (dismissed_at IS NOT NULL AND length(trim(dismissal_reason)) > 0)
        )
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(file_path)) > 0),
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE status_check_runs (
    check_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    conclusion TEXT NOT NULL
        CHECK (conclusion IN ('success', 'failure', 'cancelled', 'pending')),
    completed_at TIMESTAMPTZ,
    CHECK (length(trim(check_name)) > 0),
    CHECK (
        (conclusion = 'pending' AND completed_at IS NULL)
        OR
        (conclusion <> 'pending' AND completed_at IS NOT NULL)
    )
);

CREATE TABLE merge_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id),
    actor_id BIGINT NOT NULL REFERENCES repository_users(user_id),
    strategy TEXT NOT NULL
        CHECK (strategy IN ('merge_commit', 'squash', 'rebase')),
    outcome TEXT NOT NULL CHECK (outcome IN ('merged', 'rejected')),
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX pull_requests_target_state_idx
    ON pull_requests (target_branch_id, state);

CREATE INDEX reviews_current_lookup_idx
    ON reviews (pull_request_id, reviewer_id, submitted_at DESC);

CREATE INDEX status_checks_current_lookup_idx
    ON status_check_runs (pull_request_id, check_name, commit_sha);

CREATE INDEX unresolved_review_comments_idx
    ON review_comments (review_id)
    WHERE is_resolved = FALSE;

CREATE INDEX pull_request_commit_history_idx
    ON pull_request_commits (pull_request_id, committed_at);

-- Prevent an author from submitting a review on their own pull request.
CREATE OR REPLACE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_author_id BIGINT;
    v_state TEXT;
    v_repository_id BIGINT;
    v_can_review BOOLEAN;
BEGIN
    SELECT pr.author_id, pr.state, pr.repository_id
      INTO v_author_id, v_state, v_repository_id
      FROM pull_requests pr
     WHERE pr.pull_request_id = NEW.pull_request_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '23503',
            MESSAGE = 'Pull request does not exist.';
    END IF;

    IF v_state <> 'open' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'Reviews can only be submitted to open pull requests.';
    END IF;

    IF NEW.reviewer_id = v_author_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'Self-review is prohibited.';
    END IF;

    SELECT ru.can_review
      INTO v_can_review
      FROM reviewer_eligibility ru
     WHERE ru.repository_id = v_repository_id
       AND ru.user_id = NEW.reviewer_id;

    IF NOT FOUND OR v_can_review IS NOT TRUE THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'Reviewer is not eligible for this repository.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER reviews_validate_before_insert
BEFORE INSERT ON reviews
FOR EACH ROW EXECUTE FUNCTION validate_review_submission();

-- A policy view reports eligibility failures without prematurely changing PR state.
CREATE OR REPLACE VIEW pull_request_merge_evaluation AS
WITH active_policy AS (
    SELECT
        pr.pull_request_id,
        pr.repository_id,
        pr.target_branch_id,
        pr.state,
        pr.head_sha,
        pr.unresolved_threads,
        pr.base_up_to_date,
        pr.has_conflicts,
        pr.linear_history_possible,
        rp.policy_id,
        rp.required_approvals,
        rp.dismiss_stale_approvals,
        rp.require_resolved_conversations,
        rp.require_linear_history
    FROM pull_requests pr
    JOIN branches target_branch
      ON target_branch.branch_id = pr.target_branch_id
    JOIN review_policies rp
      ON rp.repository_id = pr.repository_id
     AND rp.branch_pattern = target_branch.branch_name
),
reviewer_latest_decisions AS (
    SELECT DISTINCT ON (r.pull_request_id, r.reviewer_id)
        r.pull_request_id,
        r.reviewer_id,
        r.review_state,
        r.commit_sha
    FROM reviews r
    JOIN active_policy ap
      ON ap.pull_request_id = r.pull_request_id
    WHERE r.dismissed_at IS NULL
      AND (
          NOT ap.dismiss_stale_approvals
          OR r.commit_sha = ap.head_sha
      )
    ORDER BY
        r.pull_request_id,
        r.reviewer_id,
        r.submitted_at DESC,
        r.review_id DESC
),
approval_counts AS (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (WHERE review_state = 'approved') AS approval_count,
        COUNT(*) FILTER (WHERE review_state = 'changes_requested') AS changes_requested_count
    FROM reviewer_latest_decisions
    GROUP BY pull_request_id
),
check_failures AS (
    SELECT
        ap.pull_request_id,
        COUNT(rsc.check_name) FILTER (
            WHERE latest_check.conclusion IS DISTINCT FROM 'success'
        ) AS missing_or_failed_checks
    FROM active_policy ap
    LEFT JOIN required_status_checks rsc
      ON rsc.policy_id = ap.policy_id
    LEFT JOIN LATERAL (
        SELECT scr.conclusion
        FROM status_check_runs scr
        WHERE scr.pull_request_id = ap.pull_request_id
          AND scr.check_name = rsc.check_name
          AND scr.commit_sha = ap.head_sha
        ORDER BY scr.check_run_id DESC
        LIMIT 1
    ) latest_check ON TRUE
    GROUP BY ap.pull_request_id
)
SELECT
    ap.pull_request_id,
    ap.state,
    COALESCE(ac.approval_count, 0) AS current_approvals,
    ap.required_approvals,
    COALESCE(cf.missing_or_failed_checks, 0) AS missing_or_failed_checks,
    CASE
        WHEN ap.state <> 'open' THEN 'blocked: pull request is not open'
        WHEN COALESCE(ac.approval_count, 0) < ap.required_approvals
            THEN 'blocked: insufficient current approvals'
        WHEN COALESCE(cf.missing_or_failed_checks, 0) > 0
            THEN 'blocked: required checks missing or failed'
        WHEN ap.require_resolved_conversations AND ap.unresolved_threads > 0
            THEN 'blocked: unresolved review conversations'
        WHEN ap.require_linear_history AND NOT ap.linear_history_possible
            THEN 'blocked: linear history required'
        WHEN NOT ap.base_up_to_date
            THEN 'blocked: base branch synchronization required'
        WHEN ap.has_conflicts
            THEN 'blocked: merge conflicts exist'
        ELSE 'eligible'
    END AS merge_status
FROM active_policy ap
LEFT JOIN approval_counts ac USING (pull_request_id)
LEFT JOIN check_failures cf USING (pull_request_id);

-- Merge through a transaction and record both successful and rejected decisions.
CREATE OR REPLACE FUNCTION attempt_merge(
    p_pull_request_id BIGINT,
    p_actor_id BIGINT,
    p_strategy TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_pr pull_requests%ROWTYPE;
    v_evaluation RECORD;
    v_policy review_policies%ROWTYPE;
    v_branch_name TEXT;
    v_strategy_allowed BOOLEAN;
    v_reason TEXT;
BEGIN
    SELECT *
      INTO v_pr
      FROM pull_requests
     WHERE pull_request_id = p_pull_request_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0002',
            MESSAGE = 'Pull request not found.';
    END IF;

    SELECT branch_name
      INTO v_branch_name
      FROM branches
     WHERE branch_id = v_pr.target_branch_id;

    SELECT *
      INTO v_policy
      FROM review_policies
     WHERE repository_id = v_pr.repository_id
       AND branch_pattern = v_branch_name
     FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'No branch protection policy matches the target branch.';
    END IF;

    CASE p_strategy
        WHEN 'merge_commit' THEN v_strategy_allowed := v_policy.allow_merge_commit;
        WHEN 'squash' THEN v_strategy_allowed := v_policy.allow_squash;
        WHEN 'rebase' THEN v_strategy_allowed := v_policy.allow_rebase;
        ELSE
            RAISE EXCEPTION USING
                ERRCODE = '22023',
                MESSAGE = 'Unknown merge strategy.';
    END CASE;

    IF NOT v_strategy_allowed THEN
        v_reason := 'Selected merge strategy is prohibited.';
    ELSE
        SELECT *
          INTO v_evaluation
          FROM pull_request_merge_evaluation
         WHERE pull_request_id = p_pull_request_id;

        v_reason := v_evaluation.merge_status;
    END IF;

    IF v_reason <> 'eligible' THEN
        INSERT INTO merge_audit (
            pull_request_id, actor_id, strategy, outcome, reason
        )
        VALUES (
            p_pull_request_id, p_actor_id, p_strategy, 'rejected', v_reason
        );

        RETURN 'rejected: ' || v_reason;
    END IF;

    UPDATE pull_requests
       SET state = 'merged',
           is_draft = FALSE,
           merge_strategy = p_strategy,
           merged_at = CURRENT_TIMESTAMP
     WHERE pull_request_id = p_pull_request_id;

    INSERT INTO merge_audit (
        pull_request_id, actor_id, strategy, outcome, reason
    )
    VALUES (
        p_pull_request_id, p_actor_id, p_strategy, 'merged',
        'All configured merge conditions passed.'
    );

    RETURN 'merged';
END;
$$;

-- Branch operations are evaluated separately from PR review decisions.
CREATE OR REPLACE FUNCTION enforce_protected_branch_operation(
    p_repository_id BIGINT,
    p_branch_name TEXT,
    p_operation TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_policy review_policies%ROWTYPE;
    v_prohibited BOOLEAN;
BEGIN
    SELECT *
      INTO v_policy
      FROM review_policies
     WHERE repository_id = p_repository_id
       AND branch_pattern = p_branch_name;

    IF NOT FOUND THEN
        RETURN TRUE;
    END IF;

    CASE p_operation
        WHEN 'direct_push' THEN v_prohibited := v_policy.prohibit_direct_pushes;
        WHEN 'force_push' THEN v_prohibited := v_policy.prohibit_force_pushes;
        WHEN 'delete' THEN v_prohibited := v_policy.prohibit_deletion;
        ELSE
            RAISE EXCEPTION USING
                ERRCODE = '22023',
                MESSAGE = 'Unknown branch operation.';
    END CASE;

    IF v_prohibited THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = format(
                'Operation %s is prohibited on protected branch %s.',
                p_operation, p_branch_name
            );
    END IF;

    RETURN TRUE;
END;
$$;

INSERT INTO repositories (full_name, default_branch)
VALUES ('platform/deployment-service', 'main');

INSERT INTO branches (
    repository_id, branch_name, head_sha, is_protected
)
SELECT repository_id, 'main', 'base-200', TRUE
FROM repositories
WHERE full_name = 'platform/deployment-service';

INSERT INTO branches (
    repository_id, branch_name, head_sha, is_protected
)
SELECT repository_id, 'feature/manifest-guard', 'head-201', FALSE
FROM repositories
WHERE full_name = 'platform/deployment-service';

INSERT INTO repository_users (username)
VALUES
    ('alex'),
    ('maya'),
    ('raj'),
    ('release-bot');

INSERT INTO reviewer_eligibility (repository_id, user_id, can_review)
SELECT r.repository_id, u.user_id, TRUE
FROM repositories r
CROSS JOIN repository_users u
WHERE r.full_name = 'platform/deployment-service'
  AND u.username IN ('maya', 'raj');

INSERT INTO review_policies (
    repository_id,
    branch_pattern,
    required_approvals,
    dismiss_stale_approvals,
    require_resolved_conversations,
    require_linear_history,
    prohibit_direct_pushes,
    prohibit_force_pushes,
    prohibit_deletion,
    allow_merge_commit,
    allow_squash,
    allow_rebase
)
SELECT repository_id, 'main', 2, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
       FALSE, TRUE, TRUE
FROM repositories
WHERE full_name = 'platform/deployment-service';

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, check_name
FROM review_policies
CROSS JOIN (VALUES ('unit-tests'), ('security-scan')) AS checks(check_name)
WHERE branch_pattern = 'main';

INSERT INTO pull_requests (
    repository_id,
    number,
    author_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    head_sha,
    base_sha,
    is_draft,
    unresolved_threads,
    base_up_to_date,
    has_conflicts,
    linear_history_possible
)
SELECT
    r.repository_id,
    512,
    author.user_id,
    source.branch_id,
    target.branch_id,
    'Validate production deployment manifests',
    'open',
    'head-201',
    'base-200',
    FALSE,
    0,
    TRUE,
    FALSE,
    TRUE
FROM repositories r
JOIN repository_users author ON author.username = 'alex'
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/manifest-guard'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.full_name = 'platform/deployment-service';

INSERT INTO pull_request_commits (pull_request_id, sha, message)
SELECT pull_request_id, 'head-201', 'Validate deployment environment allowlist'
FROM pull_requests
WHERE number = 512;

INSERT INTO reviews (
    pull_request_id, reviewer_id, review_state, commit_sha
)
SELECT pr.pull_request_id, reviewer.user_id, 'approved', 'head-201'
FROM pull_requests pr
CROSS JOIN repository_users reviewer
WHERE pr.number = 512
  AND reviewer.username = 'maya';

INSERT INTO review_comments (
    review_id, file_path, line_number, body, is_resolved
)
SELECT
    review_id,
    'src/deployment_validator.py',
    42,
    'The deployment region must be checked against the allowlist.',
    TRUE
FROM reviews
WHERE pull_request_id = (
    SELECT pull_request_id FROM pull_requests WHERE number = 512
)
AND reviewer_id = (SELECT user_id FROM repository_users WHERE username = 'maya');

INSERT INTO status_check_runs (
    pull_request_id, check_name, commit_sha, conclusion, completed_at
)
SELECT pr.pull_request_id, check_name, 'head-201', conclusion,
       CURRENT_TIMESTAMP
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests', 'success'),
        ('security-scan', 'success')
) AS sample(check_name, conclusion)
WHERE pr.number = 512;

-- Read current merge eligibility and the exact reason for any rejection.
SELECT
    pr.number,
    pr.title,
    evaluation.current_approvals,
    evaluation.required_approvals,
    evaluation.missing_or_failed_checks,
    evaluation.merge_status
FROM pull_requests pr
JOIN pull_request_merge_evaluation evaluation
  USING (pull_request_id)
WHERE pr.number = 512;

-- A reviewer can submit a new decision, but the trigger prevents self-review
-- and rejects users who lack repository review eligibility.
INSERT INTO reviews (
    pull_request_id, reviewer_id, review_state, commit_sha
)
SELECT pr.pull_request_id, reviewer.user_id, 'approved', pr.head_sha
FROM pull_requests pr
CROSS JOIN repository_users reviewer
WHERE pr.number = 512
  AND reviewer.username = 'raj';

-- Verify the decision state before attempting a merge.
SELECT
    pr.number,
    evaluation.merge_status
FROM pull_requests pr
JOIN pull_request_merge_evaluation evaluation
  USING (pull_request_id)
WHERE pr.number = 512;

-- The function returns a rejection without merging when requirements are unmet.
SELECT attempt_merge(
    (SELECT pull_request_id FROM pull_requests WHERE number = 512),
    (SELECT user_id FROM repository_users WHERE username = 'release-bot'),
    'squash'
) AS merge_result;

SELECT
    pr.number,
    pr.state,
    pr.merge_strategy,
    audit.outcome,
    audit.reason,
    audit.occurred_at
FROM pull_requests pr
JOIN merge_audit audit USING (pull_request_id)
WHERE pr.number = 512
ORDER BY audit.occurred_at DESC;

-- A prohibited direct push is an explicit database exception.
DO $$
BEGIN
    PERFORM enforce_protected_branch_operation(
        (SELECT repository_id
           FROM repositories
          WHERE full_name = 'platform/deployment-service'),
        'main',
        'force_push'
    );
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Expected protection rejection: %', SQLERRM;
END;
$$;

-- Database constraints reject invalid approval counts at policy creation.
DO $$
BEGIN
    BEGIN
        INSERT INTO review_policies (
            repository_id, branch_pattern, required_approvals
        )
        SELECT repository_id, 'invalid-policy', -1
        FROM repositories
        WHERE full_name = 'platform/deployment-service';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Expected invalid policy rejection: %', SQLERRM;
    END;
END;
$$;

COMMIT;
