DROP SCHEMA IF EXISTS eda_governance CASCADE;
CREATE SCHEMA eda_governance;

SET search_path = eda_governance, public;

CREATE TYPE pr_state AS ENUM (
    'draft',
    'open',
    'changes_requested',
    'approved',
    'closed',
    'merged'
);

CREATE TYPE review_state AS ENUM (
    'commented',
    'approved',
    'changes_requested',
    'dismissed'
);

CREATE TYPE check_state AS ENUM (
    'pending',
    'passing',
    'failing'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repository (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    owner_name TEXT NOT NULL,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(repository_name)) > 0),
    CHECK (length(trim(owner_name)) > 0)
);

CREATE TABLE repository_user (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_administrator BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE repository_member (
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES repository_user(user_id)
        ON DELETE CASCADE,
    role_name TEXT NOT NULL CHECK (
        role_name IN ('owner', 'maintainer', 'developer', 'reviewer')
    ),
    PRIMARY KEY (repository_id, user_id)
);

CREATE TABLE branch (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    head_commit_sha TEXT,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0)
);

CREATE UNIQUE INDEX one_default_branch_per_repository
ON branch(repository_id)
WHERE is_default = TRUE;

CREATE TABLE commit_record (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    sha TEXT NOT NULL,
    author_id BIGINT NOT NULL REFERENCES repository_user(user_id),
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, sha),
    CHECK (length(trim(sha)) >= 7),
    CHECK (length(trim(message)) > 0)
);

CREATE TABLE pull_request (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    opened_by BIGINT NOT NULL REFERENCES repository_user(user_id),
    title TEXT NOT NULL,
    state pr_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    conversations_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    branch_synchronized BOOLEAN NOT NULL DEFAULT TRUE,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0),
    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL)
        OR state <> 'merged'
    )
);

CREATE TABLE pull_request_commit (
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commit_record(commit_id)
        ON DELETE RESTRICT,
    sequence_number INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, sequence_number),
    CHECK (sequence_number > 0)
);

CREATE TABLE review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES repository_user(user_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stale BOOLEAN NOT NULL DEFAULT FALSE,
    dismissed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE review_comment (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES review(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(file_path)) > 0),
    CHECK (length(trim(body)) > 0),
    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE TABLE conversation (
    conversation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    opened_by BIGINT NOT NULL REFERENCES repository_user(user_id),
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by BIGINT REFERENCES repository_user(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    CHECK (length(trim(body)) > 0),
    CHECK (
        (resolved = TRUE AND resolved_by IS NOT NULL)
        OR resolved = FALSE
    )
);

CREATE TABLE status_check (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE branch_protection_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branch(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 0,
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_branch_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_approvals >= 0)
);

CREATE TABLE allowed_merge_strategy (
    policy_id BIGINT NOT NULL REFERENCES branch_protection_policy(policy_id)
        ON DELETE CASCADE,
    strategy merge_strategy NOT NULL,
    PRIMARY KEY (policy_id, strategy)
);

CREATE INDEX idx_pr_repository_state
ON pull_request(repository_id, state);

CREATE INDEX idx_review_pr_state
ON review(pull_request_id, state, stale);

CREATE INDEX idx_status_check_pr_state
ON status_check(pull_request_id, state, required);

CREATE INDEX idx_conversation_pr_resolution
ON conversation(pull_request_id, resolved);

CREATE OR REPLACE FUNCTION enforce_review_eligibility()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'approved'
       AND NOT EXISTS (
           SELECT 1
           FROM repository_member rm
           JOIN pull_request pr
             ON pr.repository_id = rm.repository_id
           WHERE pr.pull_request_id = NEW.pull_request_id
             AND rm.user_id = NEW.reviewer_id
             AND rm.role_name IN ('owner', 'maintainer', 'reviewer')
       )
    THEN
        RAISE EXCEPTION
            'Reviewer % is not eligible for Pull Request %',
            NEW.reviewer_id,
            NEW.pull_request_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_review_eligibility
BEFORE INSERT OR UPDATE ON review
FOR EACH ROW
EXECUTE FUNCTION enforce_review_eligibility();

CREATE OR REPLACE FUNCTION prevent_protected_branch_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    protected BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM branch_protection_policy bpp
        WHERE bpp.branch_id = OLD.branch_id
    )
    INTO protected;

    IF protected THEN
        RAISE EXCEPTION
            'Protected branch cannot be deleted through this workflow';
    END IF;

    RETURN OLD;
END;
$$;

CREATE TRIGGER trg_protected_branch_delete
BEFORE DELETE ON branch
FOR EACH ROW
EXECUTE FUNCTION prevent_protected_branch_mutation();

CREATE OR REPLACE FUNCTION count_current_approvals(p_pr BIGINT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT COUNT(DISTINCT reviewer_id)::INTEGER
    FROM review
    WHERE pull_request_id = p_pr
      AND state = 'approved'
      AND stale = FALSE
      AND dismissed = FALSE;
$$;

CREATE OR REPLACE FUNCTION required_checks_pass(p_pr BIGINT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT NOT EXISTS (
        SELECT 1
        FROM status_check
        WHERE pull_request_id = p_pr
          AND required = TRUE
          AND state <> 'passing'
    );
$$;

CREATE OR REPLACE FUNCTION unresolved_conversations(p_pr BIGINT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT COUNT(*)::INTEGER
    FROM conversation
    WHERE pull_request_id = p_pr
      AND resolved = FALSE;
$$;

CREATE OR REPLACE VIEW merge_eligibility AS
SELECT
    pr.pull_request_id,
    r.repository_name,
    target.branch_name AS target_branch,
    pr.state,
    pr.is_draft,
    pr.has_conflicts,
    pr.branch_synchronized,
    count_current_approvals(pr.pull_request_id) AS approval_count,
    bpp.required_approvals,
    required_checks_pass(pr.pull_request_id) AS checks_pass,
    unresolved_conversations(pr.pull_request_id) AS unresolved_conversations,
    (
        pr.state = 'open'
        AND NOT pr.is_draft
        AND NOT pr.has_conflicts
        AND pr.branch_synchronized
        AND count_current_approvals(pr.pull_request_id)
            >= bpp.required_approvals
        AND (
            NOT bpp.require_status_checks
            OR required_checks_pass(pr.pull_request_id)
        )
        AND (
            NOT bpp.require_resolved_conversations
            OR unresolved_conversations(pr.pull_request_id) = 0
        )
    ) AS merge_eligible
FROM pull_request pr
JOIN repository r
  ON r.repository_id = pr.repository_id
JOIN branch target
  ON target.branch_id = pr.target_branch_id
JOIN branch_protection_policy bpp
  ON bpp.branch_id = target.branch_id;

CREATE OR REPLACE FUNCTION merge_pull_request(
    p_pull_request_id BIGINT,
    p_strategy merge_strategy
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    eligible BOOLEAN;
    target_branch_id BIGINT;
BEGIN
    SELECT
        me.merge_eligible,
        pr.target_branch_id
    INTO eligible, target_branch_id
    FROM merge_eligibility me
    JOIN pull_request pr
      ON pr.pull_request_id = me.pull_request_id
    WHERE me.pull_request_id = p_pull_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Pull Request % does not exist',
            p_pull_request_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM allowed_merge_strategy ams
        JOIN branch_protection_policy bpp
          ON bpp.policy_id = ams.policy_id
        WHERE bpp.branch_id = target_branch_id
          AND ams.strategy = p_strategy
    ) THEN
        RAISE EXCEPTION
            'Merge strategy % is not allowed',
            p_strategy;
    END IF;

    IF NOT eligible THEN
        RAISE EXCEPTION
            'Pull Request % is not merge eligible',
            p_pull_request_id;
    END IF;

    UPDATE pull_request
    SET state = 'merged',
        merged_at = CURRENT_TIMESTAMP,
        closed_at = CURRENT_TIMESTAMP
    WHERE pull_request_id = p_pull_request_id;
END;
$$;

INSERT INTO repository(repository_name, owner_name)
VALUES ('customer-analytics', 'platform-team');

INSERT INTO repository_user(username, is_active, is_administrator)
VALUES
    ('alice', TRUE, TRUE),
    ('bob', TRUE, FALSE),
    ('carol', TRUE, FALSE),
    ('dave', TRUE, FALSE),
    ('external-reviewer', TRUE, FALSE);

INSERT INTO repository_member(repository_id, user_id, role_name)
SELECT 1, user_id, role_name
FROM (
    VALUES
        (1, 'owner'),
        (2, 'reviewer'),
        (3, 'reviewer'),
        (4, 'developer')
) AS membership(user_id, role_name);

INSERT INTO branch(
    repository_id,
    branch_name,
    is_default,
    head_commit_sha
)
VALUES
    (1, 'main', TRUE, 'main001'),
    (1, 'feature/customer-eda', FALSE, 'feat001'),
    (1, 'feature/stale-analysis', FALSE, 'feat002');

INSERT INTO commit_record(
    repository_id,
    sha,
    author_id,
    message
)
VALUES
    (1, 'a123456', 1, 'Add exploratory analysis workflow'),
    (1, 'b123456', 2, 'Add anomaly detection'),
    (1, 'c123456', 3, 'Add validation tests');

INSERT INTO pull_request(
    repository_id,
    source_branch_id,
    target_branch_id,
    opened_by,
    title,
    state,
    is_draft,
    has_conflicts,
    conversations_resolved,
    branch_synchronized
)
VALUES
    (
        1, 2, 1, 4,
        'Customer EDA and anomaly analysis',
        'open',
        FALSE,
        FALSE,
        TRUE,
        TRUE
    ),
    (
        1, 3, 1, 4,
        'Stale approval demonstration',
        'open',
        FALSE,
        FALSE,
        TRUE,
        TRUE
    );

INSERT INTO pull_request_commit(
    pull_request_id,
    commit_id,
    sequence_number
)
VALUES
    (1, 1, 1),
    (1, 2, 2),
    (1, 3, 3);

INSERT INTO review(
    pull_request_id,
    reviewer_id,
    state,
    stale,
    dismissed
)
VALUES
    (1, 2, 'approved', FALSE, FALSE),
    (1, 3, 'approved', FALSE, FALSE),
    (2, 2, 'approved', TRUE, FALSE),
    (2, 3, 'approved', FALSE, FALSE);

INSERT INTO review_comment(
    review_id,
    file_path,
    line_number,
    body
)
VALUES
    (1, 'analysis.py', 84, 'Validate the zero-variance case.'),
    (2, 'schema.sql', 112, 'Index the review state lookup.');

INSERT INTO conversation(
    pull_request_id,
    opened_by,
    body,
    resolved,
    resolved_by,
    resolved_at
)
VALUES
    (
        1, 2,
        'Please document the anomaly threshold.',
        TRUE, 4, CURRENT_TIMESTAMP
    ),
    (
        2, 3,
        'Clarify the stale approval behavior.',
        FALSE, NULL, NULL
    );

INSERT INTO status_check(
    pull_request_id,
    check_name,
    state,
    required,
    completed_at
)
VALUES
    (1, 'unit-tests', 'passing', TRUE, CURRENT_TIMESTAMP),
    (1, 'security-scan', 'passing', TRUE, CURRENT_TIMESTAMP),
    (1, 'static-analysis', 'passing', TRUE, CURRENT_TIMESTAMP),
    (2, 'unit-tests', 'passing', TRUE, CURRENT_TIMESTAMP),
    (2, 'security-scan', 'passing', TRUE, CURRENT_TIMESTAMP);

INSERT INTO branch_protection_policy(
    branch_id,
    required_approvals,
    require_status_checks,
    require_resolved_conversations,
    restrict_direct_push,
    restrict_force_push,
    restrict_branch_deletion,
    require_linear_history,
    administrator_bypass
)
VALUES
    (
        1,
        2,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        FALSE
    );

INSERT INTO allowed_merge_strategy(policy_id, strategy)
VALUES
    (1, 'squash'),
    (1, 'rebase');

-- Retrieval: all Pull Requests and their current workflow states.
SELECT
    pull_request_id,
    title,
    state,
    is_draft,
    has_conflicts,
    branch_synchronized
FROM pull_request
ORDER BY pull_request_id;

-- Review analysis: eligible, non-stale approvals only.
SELECT
    pr.pull_request_id,
    COUNT(DISTINCT r.reviewer_id) AS current_eligible_approvals
FROM pull_request pr
LEFT JOIN review r
  ON r.pull_request_id = pr.pull_request_id
 AND r.state = 'approved'
 AND r.stale = FALSE
 AND r.dismissed = FALSE
JOIN repository_member rm
  ON rm.repository_id = pr.repository_id
 AND rm.user_id = r.reviewer_id
 AND rm.role_name IN ('owner', 'maintainer', 'reviewer')
GROUP BY pr.pull_request_id
ORDER BY pr.pull_request_id;

-- Status-check reporting.
SELECT
    pr.pull_request_id,
    sc.check_name,
    sc.state,
    sc.required
FROM status_check sc
JOIN pull_request pr
  ON pr.pull_request_id = sc.pull_request_id
ORDER BY pr.pull_request_id, sc.check_name;

-- Aggregation: review decisions by state.
SELECT
    state,
    COUNT(*) AS review_count
FROM review
GROUP BY state
ORDER BY state;

-- CTE: identify Pull Requests that contain at least one failing or pending
-- required check.
WITH blocked_checks AS (
    SELECT
        pull_request_id,
        COUNT(*) AS blocking_check_count
    FROM status_check
    WHERE required = TRUE
      AND state <> 'passing'
    GROUP BY pull_request_id
)
SELECT
    pr.pull_request_id,
    pr.title,
    COALESCE(bc.blocking_check_count, 0) AS blocking_check_count
FROM pull_request pr
LEFT JOIN blocked_checks bc
  ON bc.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id;

-- Final merge eligibility evaluation.
SELECT *
FROM merge_eligibility
ORDER BY pull_request_id;

-- Transactional merge demonstration.
BEGIN;

SELECT *
FROM merge_eligibility
WHERE pull_request_id = 1
FOR UPDATE;

SELECT merge_pull_request(1, 'squash');

COMMIT;

-- The second Pull Request remains blocked because one of its approvals is
-- stale and one required conversation is unresolved.
SELECT *
FROM merge_eligibility
WHERE pull_request_id = 2;

-- The following query reports repository-level governance settings.
SELECT
    r.repository_name,
    b.branch_name,
    bpp.required_approvals,
    bpp.require_status_checks,
    bpp.require_resolved_conversations,
    bpp.restrict_direct_push,
    bpp.restrict_force_push,
    bpp.restrict_branch_deletion,
    bpp.require_linear_history,
    bpp.administrator_bypass
FROM branch_protection_policy bpp
JOIN branch b
  ON b.branch_id = bpp.branch_id
JOIN repository r
  ON r.repository_id = b.repository_id;
