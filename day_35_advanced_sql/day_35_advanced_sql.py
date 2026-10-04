#!/usr/bin/env python3
"""
Advanced SQL CTEs: CTEs, recursive CTEs, nested CTEs, and reusable query logic.

This self-contained program uses Python's standard-library sqlite3 module to
execute realistic SQL against an in-memory repository-governance dataset.

The examples deliberately keep Pull Requests, Code Review, Approvals, and
Branch Protection distinct:

- Pull Requests model the proposed change and its lifecycle.
- Code Reviews model reviewer evaluation and discussion.
- Approvals model explicit review decisions that can affect merge eligibility.
- Branch Protection models repository-level merge requirements.

The main SQL subject is CTE design. The repository domain gives the queries
enough relational structure to demonstrate ordinary CTEs, multiple CTEs,
nested CTEs, recursive CTEs, correlated logic, reusable query templates,
window functions inside CTEs, cycle-safe recursion, and query debugging.

Run with:
    python advanced_sql_ctes.py
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


DATABASE = ":memory:"


def connect_database() -> sqlite3.Connection:
    """Create a SQLite database with useful foreign-key enforcement."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create a compact but realistic relational model for CTE examples."""
    connection.executescript(
        """
        CREATE TABLE repositories (
            repository_id INTEGER PRIMARY KEY,
            owner TEXT NOT NULL,
            name TEXT NOT NULL,
            default_branch TEXT NOT NULL DEFAULT 'main',
            UNIQUE (owner, name)
        );

        CREATE TABLE branches (
            branch_id INTEGER PRIMARY KEY,
            repository_id INTEGER NOT NULL
                REFERENCES repositories(repository_id),
            branch_name TEXT NOT NULL,
            is_protected INTEGER NOT NULL DEFAULT 0
                CHECK (is_protected IN (0, 1)),
            UNIQUE (repository_id, branch_name)
        );

        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            team TEXT NOT NULL
        );

        CREATE TABLE pull_requests (
            pull_request_id INTEGER PRIMARY KEY,
            repository_id INTEGER NOT NULL
                REFERENCES repositories(repository_id),
            source_branch_id INTEGER NOT NULL
                REFERENCES branches(branch_id),
            target_branch_id INTEGER NOT NULL
                REFERENCES branches(branch_id),
            author_id INTEGER NOT NULL
                REFERENCES users(user_id),
            title TEXT NOT NULL,
            state TEXT NOT NULL
                CHECK (state IN ('draft', 'open', 'closed', 'merged')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            merged_at TEXT,
            CHECK (source_branch_id <> target_branch_id)
        );

        CREATE TABLE commits (
            commit_id INTEGER PRIMARY KEY,
            pull_request_id INTEGER NOT NULL
                REFERENCES pull_requests(pull_request_id),
            sha TEXT NOT NULL UNIQUE,
            parent_sha TEXT,
            author_id INTEGER NOT NULL REFERENCES users(user_id),
            message TEXT NOT NULL,
            committed_at TEXT NOT NULL
        );

        CREATE TABLE reviews (
            review_id INTEGER PRIMARY KEY,
            pull_request_id INTEGER NOT NULL
                REFERENCES pull_requests(pull_request_id),
            reviewer_id INTEGER NOT NULL REFERENCES users(user_id),
            review_state TEXT NOT NULL
                CHECK (
                    review_state IN (
                        'commented',
                        'approved',
                        'changes_requested',
                        'dismissed'
                    )
                ),
            submitted_at TEXT NOT NULL,
            dismissed_at TEXT,
            body TEXT
        );

        CREATE TABLE review_comments (
            comment_id INTEGER PRIMARY KEY,
            review_id INTEGER NOT NULL REFERENCES reviews(review_id),
            file_path TEXT NOT NULL,
            line_number INTEGER NOT NULL CHECK (line_number > 0),
            body TEXT NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0
                CHECK (resolved IN (0, 1)),
            created_at TEXT NOT NULL
        );

        CREATE TABLE status_checks (
            check_id INTEGER PRIMARY KEY,
            pull_request_id INTEGER NOT NULL
                REFERENCES pull_requests(pull_request_id),
            check_name TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK (status IN ('pending', 'passed', 'failed', 'cancelled')),
            completed_at TEXT,
            UNIQUE (pull_request_id, check_name)
        );

        CREATE TABLE branch_protection (
            policy_id INTEGER PRIMARY KEY,
            branch_id INTEGER NOT NULL UNIQUE
                REFERENCES branches(branch_id),
            required_approvals INTEGER NOT NULL
                CHECK (required_approvals >= 0),
            require_status_checks INTEGER NOT NULL
                CHECK (require_status_checks IN (0, 1)),
            restrict_direct_push INTEGER NOT NULL
                CHECK (restrict_direct_push IN (0, 1)),
            allow_force_push INTEGER NOT NULL
                CHECK (allow_force_push IN (0, 1)),
            allow_deletion INTEGER NOT NULL
                CHECK (allow_deletion IN (0, 1)),
            require_conversation_resolution INTEGER NOT NULL
                CHECK (require_conversation_resolution IN (0, 1)),
            require_linear_history INTEGER NOT NULL
                CHECK (require_linear_history IN (0, 1))
        );

        CREATE TABLE branch_relationships (
            parent_branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
            child_branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
            PRIMARY KEY (parent_branch_id, child_branch_id),
            CHECK (parent_branch_id <> child_branch_id)
        );

        CREATE INDEX idx_pr_target_state
            ON pull_requests(target_branch_id, state);

        CREATE INDEX idx_reviews_pr_reviewer
            ON reviews(pull_request_id, reviewer_id, submitted_at);

        CREATE INDEX idx_comments_review_resolution
            ON review_comments(review_id, resolved);

        CREATE INDEX idx_checks_pr_status
            ON status_checks(pull_request_id, status);

        CREATE INDEX idx_commits_pr_time
            ON commits(pull_request_id, committed_at);

        CREATE INDEX idx_branch_relationship_parent
            ON branch_relationships(parent_branch_id);
        """
    )


def seed_data(connection: sqlite3.Connection) -> None:
    """Insert several repositories and PRs in intentionally different states."""
    connection.executescript(
        """
        INSERT INTO repositories VALUES
            (1, 'acme', 'payments-api', 'main'),
            (2, 'acme', 'analytics-platform', 'main');

        INSERT INTO branches VALUES
            (1, 1, 'main', 1),
            (2, 1, 'feature/payment-timeout', 0),
            (3, 1, 'feature/risk-rules', 0),
            (4, 1, 'release/2026.10', 1),
            (5, 1, 'hotfix/auth', 0),
            (6, 2, 'main', 1),
            (7, 2, 'feature/cte-report', 0);

        INSERT INTO users VALUES
            (1, 'atul', 'platform'),
            (2, 'maya', 'payments'),
            (3, 'liam', 'security'),
            (4, 'sofia', 'data'),
            (5, 'noah', 'release');

        INSERT INTO pull_requests VALUES
            (101, 1, 2, 1, 1,
             'Increase payment timeout safely', 'open',
             '2026-10-01T09:00:00', '2026-10-05T08:00:00', NULL),

            (102, 1, 3, 1, 2,
             'Add fraud risk rules', 'open',
             '2026-10-02T09:30:00', '2026-10-05T08:30:00', NULL),

            (103, 1, 5, 4, 3,
             'Emergency authentication fix', 'open',
             '2026-10-03T10:00:00', '2026-10-05T07:45:00', NULL),

            (104, 1, 2, 1, 1,
             'Refactor payment query', 'merged',
             '2026-09-25T10:00:00', '2026-09-28T16:00:00',
             '2026-09-28T16:00:00'),

            (105, 2, 7, 6, 4,
             'Build recursive reporting query', 'draft',
             '2026-10-04T11:00:00', '2026-10-05T06:30:00', NULL);

        INSERT INTO commits VALUES
            (1001, 101, 'a101', NULL, 1,
             'Add configurable timeout', '2026-10-01T09:10:00'),
            (1002, 101, 'a102', 'a101', 1,
             'Add timeout tests', '2026-10-02T09:10:00'),
            (1003, 101, 'a103', 'a102', 1,
             'Tune integration test', '2026-10-05T07:30:00'),

            (1004, 102, 'b101', NULL, 2,
             'Add risk rule table', '2026-10-02T10:00:00'),
            (1005, 102, 'b102', 'b101', 2,
             'Validate risk thresholds', '2026-10-03T12:00:00'),

            (1006, 103, 'c101', NULL, 3,
             'Patch authentication fallback', '2026-10-03T11:00:00'),

            (1007, 104, 'd101', NULL, 1,
             'Refactor payment query', '2026-09-25T10:30:00'),
            (1008, 104, 'd102', 'd101', 1,
             'Add query regression tests', '2026-09-26T10:30:00'),

            (1009, 105, 'e101', NULL, 4,
             'Create recursive CTE report', '2026-10-04T11:30:00');

        INSERT INTO reviews VALUES
            (2001, 101, 2, 'approved', '2026-10-03T10:00:00', NULL,
             'Timeout change is scoped correctly.'),
            (2002, 101, 3, 'commented', '2026-10-03T11:00:00', NULL,
             'Please verify the security-sensitive retry path.'),
            (2003, 102, 3, 'changes_requested', '2026-10-04T09:00:00', NULL,
             'Risk threshold needs a validation guard.'),
            (2004, 102, 4, 'approved', '2026-10-04T10:00:00', NULL,
             'Data validation looks consistent.'),
            (2005, 103, 1, 'approved', '2026-10-04T12:00:00', NULL,
             'Patch reviewed.'),
            (2006, 104, 2, 'approved', '2026-09-27T12:00:00', NULL,
             'Approved before merge.'),
            (2007, 104, 3, 'dismissed', '2026-09-27T13:00:00',
             '2026-09-28T09:00:00',
             'Approval dismissed after the review policy changed.');

        INSERT INTO review_comments VALUES
            (3001, 2002, 'retry.py', 88,
             'The retry path should not amplify failed authentication.',
             1, '2026-10-03T11:01:00'),
            (3002, 2003, 'risk_rules.py', 42,
             'Reject thresholds outside the configured risk range.',
             0, '2026-10-04T09:01:00'),
            (3003, 2004, 'schema.sql', 18,
             'Constraint is appropriate for this domain.',
             1, '2026-10-04T10:01:00');

        INSERT INTO status_checks VALUES
            (4001, 101, 'unit-tests', 'passed', '2026-10-05T07:00:00'),
            (4002, 101, 'integration-tests', 'passed', '2026-10-05T07:05:00'),
            (4003, 101, 'security-scan', 'passed', '2026-10-05T07:10:00'),

            (4004, 102, 'unit-tests', 'passed', '2026-10-05T07:15:00'),
            (4005, 102, 'integration-tests', 'failed', '2026-10-05T07:20:00'),
            (4006, 102, 'security-scan', 'passed', '2026-10-05T07:25:00'),

            (4007, 103, 'unit-tests', 'passed', '2026-10-05T07:30:00'),
            (4008, 103, 'security-scan', 'passed', '2026-10-05T07:35:00'),

            (4009, 104, 'unit-tests', 'passed', '2026-09-28T15:00:00'),
            (4010, 104, 'integration-tests', 'passed', '2026-09-28T15:05:00');

        INSERT INTO branch_protection VALUES
            (5001, 1, 2, 1, 1, 0, 0, 1, 1),
            (5002, 4, 1, 1, 1, 0, 0, 1, 1),
            (5003, 6, 1, 1, 1, 0, 0, 1, 1);

        INSERT INTO branch_relationships VALUES
            (1, 4),
            (4, 5),
            (1, 2),
            (1, 3),
            (6, 7);
        """
    )


def print_rows(title: str, rows: Iterable[sqlite3.Row]) -> None:
    """Print query output without requiring any third-party table library."""
    print(f"\n=== {title} ===")
    rows = list(rows)

    if not rows:
        print("(no rows)")
        return

    columns = rows[0].keys()
    print(" | ".join(columns))
    print("-" * (len(" | ".join(columns)) + 2))

    for row in rows:
        print(" | ".join(str(row[column]) for column in columns))


def execute_query(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...] = (),
) -> list[sqlite3.Row]:
    """Execute a SELECT and return materialized rows."""
    cursor = connection.execute(sql, parameters)
    return cursor.fetchall()


def demonstrate_basic_cte(connection: sqlite3.Connection) -> None:
    """
    A CTE gives a named intermediate result to the statement that follows it.

    The important distinction is scope: the CTE exists for this SQL statement
    rather than becoming a permanent database object.
    """
    sql = """
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
        SELECT *
        FROM open_pull_requests
        WHERE target_branch = 'main'
        ORDER BY pull_request_id;
    """
    print_rows("Basic CTE: reusable filtered relation", execute_query(connection, sql))


def demonstrate_multiple_ctes(connection: sqlite3.Connection) -> None:
    """
    Multiple CTEs form a readable pipeline. Each later CTE can consume earlier
    CTEs, which is useful when one query contains several logical transformations.
    """
    sql = """
        WITH
        open_prs AS (
            SELECT pull_request_id, author_id, target_branch_id
            FROM pull_requests
            WHERE state = 'open'
        ),
        review_activity AS (
            SELECT
                pull_request_id,
                COUNT(*) AS total_reviews
            FROM reviews
            GROUP BY pull_request_id
        ),
        check_activity AS (
            SELECT
                pull_request_id,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) AS passed_checks,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_checks
            FROM status_checks
            GROUP BY pull_request_id
        )
        SELECT
            p.pull_request_id,
            u.username AS author,
            COALESCE(r.total_reviews, 0) AS total_reviews,
            COALESCE(c.passed_checks, 0) AS passed_checks,
            COALESCE(c.failed_checks, 0) AS failed_checks
        FROM open_prs AS p
        JOIN users AS u ON u.user_id = p.author_id
        LEFT JOIN review_activity AS r
          ON r.pull_request_id = p.pull_request_id
        LEFT JOIN check_activity AS c
          ON c.pull_request_id = p.pull_request_id
        ORDER BY p.pull_request_id;
    """
    print_rows("Multiple CTEs: staged query pipeline", execute_query(connection, sql))


def demonstrate_nested_cte_logic(connection: sqlite3.Connection) -> None:
    """
    A nested CTE can consume another CTE and then expose a narrower relation.

    This example separates review aggregation from the final policy-oriented
    classification so each transformation has one responsibility.
    """
    sql = """
        WITH review_summary AS (
            SELECT
                pr.pull_request_id,
                COUNT(r.review_id) AS review_count,
                COUNT(
                    CASE
                        WHEN r.review_state = 'approved'
                        THEN 1
                    END
                ) AS approval_count,
                COUNT(
                    CASE
                        WHEN r.review_state = 'changes_requested'
                        THEN 1
                    END
                ) AS change_request_count
            FROM pull_requests AS pr
            LEFT JOIN reviews AS r
              ON r.pull_request_id = pr.pull_request_id
            GROUP BY pr.pull_request_id
        ),
        policy_view AS (
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
                END AS review_condition
            FROM review_summary
        )
        SELECT *
        FROM policy_view
        WHERE pull_request_id IN (101, 102, 103)
        ORDER BY pull_request_id;
    """
    print_rows(
        "Nested CTE logic: aggregation followed by classification",
        execute_query(connection, sql),
    )


def demonstrate_recursive_cte(connection: sqlite3.Connection) -> None:
    """
    Recursive CTEs contain an anchor query and a recursive member.

    Here the branch relationship graph is traversed from main. depth tracks the
    distance from the starting branch. The path prevents revisiting a branch,
    making the query safer when relationship data contains a cycle.
    """
    sql = """
        WITH RECURSIVE branch_tree AS (
            SELECT
                b.branch_id,
                b.branch_name,
                0 AS depth,
                '>' || CAST(b.branch_id AS TEXT) || '>' AS path
            FROM branches AS b
            WHERE b.branch_name = 'main'

            UNION ALL

            SELECT
                child.branch_id,
                child.branch_name,
                tree.depth + 1,
                tree.path || CAST(child.branch_id AS TEXT) || '>'
            FROM branch_tree AS tree
            JOIN branch_relationships AS relation
              ON relation.parent_branch_id = tree.branch_id
            JOIN branches AS child
              ON child.branch_id = relation.child_branch_id
            WHERE instr(
                tree.path,
                '>' || CAST(child.branch_id AS TEXT) || '>'
            ) = 0
        )
        SELECT branch_name, depth, path
        FROM branch_tree
        ORDER BY depth, branch_name;
    """
    print_rows(
        "Recursive CTE: branch hierarchy traversal",
        execute_query(connection, sql),
    )


def demonstrate_recursive_dependency_walk(connection: sqlite3.Connection) -> None:
    """
    A second recursive example walks a commit chain backward from the latest
    commit. This demonstrates recursion over a linked-list-like structure,
    rather than a tree.
    """
    sql = """
        WITH RECURSIVE commit_chain AS (
            SELECT
                c.commit_id,
                c.pull_request_id,
                c.sha,
                c.parent_sha,
                0 AS distance
            FROM commits AS c
            WHERE c.pull_request_id = 101
              AND c.parent_sha IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM commits AS newer
                  WHERE newer.pull_request_id = c.pull_request_id
                    AND newer.parent_sha = c.sha
              )

            UNION ALL

            SELECT
                parent.commit_id,
                parent.pull_request_id,
                parent.sha,
                parent.parent_sha,
                chain.distance + 1
            FROM commit_chain AS chain
            JOIN commits AS parent
              ON parent.pull_request_id = chain.pull_request_id
             AND parent.sha = chain.parent_sha
        )
        SELECT sha, parent_sha, distance
        FROM commit_chain
        ORDER BY distance;
    """
    print_rows(
        "Recursive CTE: commit ancestry chain",
        execute_query(connection, sql),
    )


def demonstrate_cte_with_window_function(connection: sqlite3.Connection) -> None:
    """
    CTEs can isolate the rows that a window function operates over.

    The window function ranks reviews within each Pull Request without collapsing
    the individual review rows as GROUP BY would.
    """
    sql = """
        WITH ranked_reviews AS (
            SELECT
                r.pull_request_id,
                u.username AS reviewer,
                r.review_state,
                r.submitted_at,
                ROW_NUMBER() OVER (
                    PARTITION BY r.pull_request_id
                    ORDER BY r.submitted_at DESC
                ) AS review_rank
            FROM reviews AS r
            JOIN users AS u
              ON u.user_id = r.reviewer_id
        )
        SELECT
            pull_request_id,
            reviewer,
            review_state,
            submitted_at,
            review_rank
        FROM ranked_reviews
        WHERE review_rank <= 2
        ORDER BY pull_request_id, review_rank;
    """
    print_rows(
        "CTE plus window function: latest reviews",
        execute_query(connection, sql),
    )


def demonstrate_merge_eligibility(connection: sqlite3.Connection) -> None:
    """
    This query intentionally keeps four domain concepts separate.

    Pull Request state comes from pull_requests.
    Code Review behavior comes from reviews and review_comments.
    Approval eligibility comes from active approved reviews.
    Branch Protection supplies the policy requirements.

    The CTE pipeline combines these facts only at the final eligibility step.
    """
    sql = """
        WITH
        protected_targets AS (
            SELECT
                bp.branch_id,
                bp.required_approvals,
                bp.require_status_checks,
                bp.require_conversation_resolution,
                bp.require_linear_history
            FROM branch_protection AS bp
        ),
        active_approvals AS (
            SELECT
                r.pull_request_id,
                r.reviewer_id
            FROM reviews AS r
            WHERE r.review_state = 'approved'
              AND r.dismissed_at IS NULL
        ),
        approval_counts AS (
            SELECT
                pull_request_id,
                COUNT(DISTINCT reviewer_id) AS approvals
            FROM active_approvals
            GROUP BY pull_request_id
        ),
        check_summary AS (
            SELECT
                pull_request_id,
                COUNT(*) AS check_count,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END)
                    AS passed_checks,
                SUM(CASE WHEN status IN ('failed', 'cancelled')
                         THEN 1 ELSE 0 END) AS bad_checks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END)
                    AS pending_checks
            FROM status_checks
            GROUP BY pull_request_id
        ),
        unresolved_conversations AS (
            SELECT
                r.pull_request_id,
                COUNT(*) AS unresolved_count
            FROM reviews AS r
            JOIN review_comments AS rc
              ON rc.review_id = r.review_id
            WHERE rc.resolved = 0
            GROUP BY r.pull_request_id
        ),
        candidate_status AS (
            SELECT
                pr.pull_request_id,
                pr.title,
                target.branch_name AS target_branch,
                policy.required_approvals,
                COALESCE(approval.approvals, 0) AS approvals,
                COALESCE(checks.check_count, 0) AS check_count,
                COALESCE(checks.passed_checks, 0) AS passed_checks,
                COALESCE(checks.bad_checks, 0) AS bad_checks,
                COALESCE(checks.pending_checks, 0) AS pending_checks,
                COALESCE(conversations.unresolved_count, 0)
                    AS unresolved_count,
                CASE
                    WHEN pr.state <> 'open'
                        THEN 'Pull Request is not open'
                    WHEN COALESCE(approval.approvals, 0)
                         < policy.required_approvals
                        THEN 'approval requirement not met'
                    WHEN policy.require_status_checks = 1
                         AND (
                             COALESCE(checks.bad_checks, 0) > 0
                             OR COALESCE(checks.pending_checks, 0) > 0
                         )
                        THEN 'required status checks not green'
                    WHEN policy.require_conversation_resolution = 1
                         AND COALESCE(conversations.unresolved_count, 0) > 0
                        THEN 'unresolved review conversations'
                    ELSE 'eligible'
                END AS merge_condition
            FROM pull_requests AS pr
            JOIN branches AS target
              ON target.branch_id = pr.target_branch_id
            JOIN protected_targets AS policy
              ON policy.branch_id = pr.target_branch_id
            LEFT JOIN approval_counts AS approval
              ON approval.pull_request_id = pr.pull_request_id
            LEFT JOIN check_summary AS checks
              ON checks.pull_request_id = pr.pull_request_id
            LEFT JOIN unresolved_conversations AS conversations
              ON conversations.pull_request_id = pr.pull_request_id
        )
        SELECT *
        FROM candidate_status
        WHERE pull_request_id IN (101, 102, 103)
        ORDER BY pull_request_id;
    """
    print_rows(
        "CTE policy pipeline: merge-eligibility analysis",
        execute_query(connection, sql),
    )


def demonstrate_reusable_query_logic(connection: sqlite3.Connection) -> None:
    """
    A CTE is statement-scoped, so it cannot be called like a stored function.

    Application code can still reuse a parameterized SQL template. The reusable
    template below keeps the CTE logic in one place while allowing different
    target branches to be supplied safely as parameters.
    """
    sql_template = """
        WITH pull_request_metrics AS (
            SELECT
                pr.pull_request_id,
                pr.title,
                pr.target_branch_id,
                COUNT(DISTINCT c.commit_id) AS commit_count,
                COUNT(DISTINCT r.review_id) AS review_count,
                COUNT(DISTINCT CASE
                    WHEN r.review_state = 'approved'
                     AND r.dismissed_at IS NULL
                    THEN r.reviewer_id
                END) AS active_approvers
            FROM pull_requests AS pr
            LEFT JOIN commits AS c
              ON c.pull_request_id = pr.pull_request_id
            LEFT JOIN reviews AS r
              ON r.pull_request_id = pr.pull_request_id
            WHERE pr.target_branch_id = ?
            GROUP BY
                pr.pull_request_id,
                pr.title,
                pr.target_branch_id
        )
        SELECT *
        FROM pull_request_metrics
        ORDER BY pull_request_id;
    """

    for branch_id in (1, 4, 6):
        rows = execute_query(connection, sql_template, (branch_id,))
        print_rows(
            f"Reusable CTE template for target branch {branch_id}",
            rows,
        )


def demonstrate_correlated_cte(connection: sqlite3.Connection) -> None:
    """
    A CTE can identify the latest review from each reviewer. The final query
    then checks whether that latest decision is an approval.

    This avoids incorrectly treating an old approval as active merely because
    the reviewer once approved the Pull Request.
    """
    sql = """
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
                ) AS reviewer_review_rank
            FROM reviews AS r
        ),
        latest_reviewer_decisions AS (
            SELECT
                review_id,
                pull_request_id,
                reviewer_id,
                review_state,
                submitted_at
            FROM ranked_reviews
            WHERE reviewer_review_rank = 1
        )
        SELECT
            d.pull_request_id,
            u.username AS reviewer,
            d.review_state,
            d.submitted_at
        FROM latest_reviewer_decisions AS d
        JOIN users AS u
          ON u.user_id = d.reviewer_id
        WHERE d.pull_request_id IN (101, 102, 104)
        ORDER BY d.pull_request_id, reviewer;
    """
    print_rows(
        "CTE plus ranking: latest reviewer decision",
        execute_query(connection, sql),
    )


def demonstrate_recursive_cycle_safety(connection: sqlite3.Connection) -> None:
    """
    Insert a deliberate graph cycle and show why path tracking matters.

    The recursive query does not revisit an ID already present in its path, so
    the recursion terminates even though the data graph is cyclic.
    """
    connection.execute(
        """
        INSERT INTO branch_relationships(parent_branch_id, child_branch_id)
        VALUES (?, ?)
        """,
        (5, 1),
    )

    sql = """
        WITH RECURSIVE graph_walk AS (
            SELECT
                branch_id,
                branch_name,
                0 AS depth,
                '/' || CAST(branch_id AS TEXT) || '/' AS path
            FROM branches
            WHERE branch_id = 1

            UNION ALL

            SELECT
                child.branch_id,
                child.branch_name,
                walk.depth + 1,
                walk.path || CAST(child.branch_id AS TEXT) || '/'
            FROM graph_walk AS walk
            JOIN branch_relationships AS relation
              ON relation.parent_branch_id = walk.branch_id
            JOIN branches AS child
              ON child.branch_id = relation.child_branch_id
            WHERE instr(
                walk.path,
                '/' || CAST(child.branch_id AS TEXT) || '/'
            ) = 0
              AND walk.depth < 20
        )
        SELECT branch_id, branch_name, depth, path
        FROM graph_walk
        ORDER BY depth, branch_id;
    """

    print_rows(
        "Recursive CTE with cycle protection",
        execute_query(connection, sql),
    )


def demonstrate_cte_update(connection: sqlite3.Connection) -> None:
    """
    SQLite permits CTEs with data-modifying statements only in restricted forms,
    so this example uses a CTE as the source of an UPDATE rather than pretending
    that every PostgreSQL data-modifying CTE feature is portable to SQLite.

    The statement marks a Pull Request's latest update timestamp based on its
    newest commit. The CTE isolates the aggregate used by the update.
    """
    sql = """
        WITH latest_commit AS (
            SELECT
                pull_request_id,
                MAX(committed_at) AS latest_commit_at
            FROM commits
            GROUP BY pull_request_id
        )
        UPDATE pull_requests
        SET updated_at = (
            SELECT latest_commit_at
            FROM latest_commit
            WHERE latest_commit.pull_request_id
                   = pull_requests.pull_request_id
        )
        WHERE pull_request_id IN (
            SELECT pull_request_id
            FROM latest_commit
        );
    """

    connection.execute(sql)

    rows = execute_query(
        connection,
        """
        SELECT pull_request_id, updated_at
        FROM pull_requests
        WHERE pull_request_id IN (101, 102, 103)
        ORDER BY pull_request_id;
        """,
    )
    print_rows("CTE used as UPDATE source", rows)


def demonstrate_explain_query_plan(connection: sqlite3.Connection) -> None:
    """
    EXPLAIN QUERY PLAN is useful when a readable CTE query becomes slow.

    CTE syntax improves organization, but it does not guarantee a particular
    execution strategy. The database optimizer decides how the statement runs.
    """
    sql = """
        EXPLAIN QUERY PLAN
        WITH open_prs AS (
            SELECT pull_request_id, target_branch_id
            FROM pull_requests
            WHERE state = 'open'
        )
        SELECT p.pull_request_id
        FROM open_prs AS p
        JOIN status_checks AS s
          ON s.pull_request_id = p.pull_request_id
        WHERE s.status = 'failed';
    """

    rows = execute_query(connection, sql)
    print_rows("Execution-plan inspection for a CTE query", rows)


def demonstrate_invalid_state_detection(connection: sqlite3.Connection) -> None:
    """
    CTEs are valuable not only for producing reports but also for detecting
    inconsistent application state.

    This query finds open Pull Requests whose protected target branch requires
    approvals but has fewer active approvals than the policy requires.
    """
    sql = """
        WITH required_reviews AS (
            SELECT
                pr.pull_request_id,
                bp.required_approvals
            FROM pull_requests AS pr
            JOIN branch_protection AS bp
              ON bp.branch_id = pr.target_branch_id
            WHERE pr.state = 'open'
        ),
        active_approval_counts AS (
            SELECT
                pull_request_id,
                COUNT(DISTINCT reviewer_id) AS approvals
            FROM reviews
            WHERE review_state = 'approved'
              AND dismissed_at IS NULL
            GROUP BY pull_request_id
        )
        SELECT
            rr.pull_request_id,
            rr.required_approvals,
            COALESCE(ac.approvals, 0) AS actual_approvals
        FROM required_reviews AS rr
        LEFT JOIN active_approval_counts AS ac
          ON ac.pull_request_id = rr.pull_request_id
        WHERE COALESCE(ac.approvals, 0) < rr.required_approvals
        ORDER BY rr.pull_request_id;
    """
    print_rows(
        "CTE validation: Pull Requests below approval policy",
        execute_query(connection, sql),
    )


def demonstrate_transaction(connection: sqlite3.Connection) -> None:
    """
    A transaction keeps related changes atomic. The CTE calculates which status
    checks are currently failing before the application decides whether to
    update another row.

    The demonstration rolls back intentionally, showing that CTE evaluation and
    transactional changes are separate concerns.
    """
    connection.execute("BEGIN")

    try:
        sql = """
            WITH failed_checks AS (
                SELECT pull_request_id, COUNT(*) AS failure_count
                FROM status_checks
                WHERE status IN ('failed', 'cancelled')
                GROUP BY pull_request_id
            )
            UPDATE pull_requests
            SET updated_at = datetime('now')
            WHERE pull_request_id IN (
                SELECT pull_request_id
                FROM failed_checks
            );

        """
        connection.execute(sql)

        changed = connection.total_changes
        print(f"\n=== Transactional CTE demonstration ===")
        print(f"Rows affected by the demonstration update: {changed}")

        connection.rollback()
        print("Transaction rolled back; demonstration data remains unchanged.")
    except sqlite3.Error:
        connection.rollback()
        raise


def demonstrate_parameter_validation(connection: sqlite3.Connection) -> None:
    """
    Parameterized SQL prevents a caller-controlled value from becoming SQL
    syntax. The CTE itself is not a security boundary; safe parameter binding
    is still required when application data enters a query.
    """
    requested_state = "open"

    sql = """
        WITH selected_prs AS (
            SELECT pull_request_id, title, state
            FROM pull_requests
            WHERE state = ?
        )
        SELECT pull_request_id, title
        FROM selected_prs
        ORDER BY pull_request_id;
    """

    rows = execute_query(connection, sql, (requested_state,))
    print_rows(
        "Parameterized CTE query",
        rows,
    )


@dataclass(frozen=True)
class CTEExample:
    """Metadata used to keep the demonstration runner explicit and readable."""

    name: str
    function: Any


def run_all_demos(connection: sqlite3.Connection) -> None:
    """Run demonstrations in increasing technical complexity."""
    examples = [
        CTEExample("basic CTE", demonstrate_basic_cte),
        CTEExample("multiple CTEs", demonstrate_multiple_ctes),
        CTEExample("nested CTE logic", demonstrate_nested_cte_logic),
        CTEExample("recursive CTE", demonstrate_recursive_cte),
        CTEExample(
            "recursive commit traversal",
            demonstrate_recursive_dependency_walk,
        ),
        CTEExample(
            "CTE with window function",
            demonstrate_cte_with_window_function,
        ),
        CTEExample(
            "merge-eligibility CTE pipeline",
            demonstrate_merge_eligibility,
        ),
        CTEExample(
            "reusable parameterized CTE template",
            demonstrate_reusable_query_logic,
        ),
        CTEExample(
            "latest reviewer decision",
            demonstrate_correlated_cte,
        ),
        CTEExample(
            "recursive cycle safety",
            demonstrate_recursive_cycle_safety,
        ),
        CTEExample(
            "CTE as UPDATE source",
            demonstrate_cte_update,
        ),
        CTEExample(
            "query-plan inspection",
            demonstrate_explain_query_plan,
        ),
        CTEExample(
            "invalid-state detection",
            demonstrate_invalid_state_detection,
        ),
        CTEExample(
            "transactional CTE",
            demonstrate_transaction,
        ),
        CTEExample(
            "parameter validation",
            demonstrate_parameter_validation,
        ),
    ]

    for example in examples:
        try:
            example.function(connection)
        except sqlite3.Error as error:
            print(f"\n[{example.name}] SQL error: {error}")
            raise


def main() -> None:
    """Build the database and execute the complete CTE learning case study."""
    connection = connect_database()

    try:
        create_schema(connection)
        seed_data(connection)

        print("Advanced SQL CTE Case Study")
        print("===========================")
        print("SQLite version:", sqlite3.sqlite_version)

        run_all_demos(connection)

        print("\n=== Demonstration complete ===")
        print(
            "The examples covered ordinary CTEs, CTE pipelines, nested "
            "query logic, recursion, cycle protection, window functions, "
            "parameterization, validation, updates, transactions, and "
            "execution-plan inspection."
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
