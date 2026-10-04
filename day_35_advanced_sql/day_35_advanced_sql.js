"use strict";

/*
 * Advanced SQL CTEs in JavaScript.
 *
 * This Node.js program models a SQL CTE execution workflow without requiring
 * an npm package. JavaScript owns the application-side orchestration while
 * PostgreSQL-compatible SQL strings demonstrate the actual CTE patterns that
 * a production application can submit through a database driver.
 *
 * The domain distinguishes:
 * - Pull Requests: proposed changes and lifecycle state.
 * - Code Review: reviewer evaluation and discussion.
 * - Approvals: explicit approval decisions.
 * - Branch Protection: repository policy that controls merge eligibility.
 *
 * The SQL examples focus on CTEs rather than treating those domain concepts
 * as interchangeable.
 */

const DEMO_DATABASE = "PostgreSQL-compatible SQL";
const targetBranch = "main";

const pullRequests = [
  {
    id: 101,
    title: "Increase payment timeout safely",
    state: "open",
    targetBranch: "main",
    author: "atul",
  },
  {
    id: 102,
    title: "Add fraud risk rules",
    state: "open",
    targetBranch: "main",
    author: "maya",
  },
  {
    id: 103,
    title: "Emergency authentication fix",
    state: "open",
    targetBranch: "release/2026.10",
    author: "liam",
  },
];

const reviews = [
  {
    id: 2001,
    pullRequestId: 101,
    reviewer: "maya",
    state: "approved",
    submittedAt: "2026-10-03T10:00:00Z",
  },
  {
    id: 2002,
    pullRequestId: 101,
    reviewer: "liam",
    state: "commented",
    submittedAt: "2026-10-03T11:00:00Z",
  },
  {
    id: 2003,
    pullRequestId: 102,
    reviewer: "liam",
    state: "changes_requested",
    submittedAt: "2026-10-04T09:00:00Z",
  },
  {
    id: 2004,
    pullRequestId: 102,
    reviewer: "sofia",
    state: "approved",
    submittedAt: "2026-10-04T10:00:00Z",
  },
];

const statusChecks = [
  { pullRequestId: 101, name: "unit-tests", status: "passed" },
  { pullRequestId: 101, name: "integration-tests", status: "passed" },
  { pullRequestId: 101, name: "security-scan", status: "passed" },
  { pullRequestId: 102, name: "unit-tests", status: "passed" },
  { pullRequestId: 102, name: "integration-tests", status: "failed" },
  { pullRequestId: 102, name: "security-scan", status: "passed" },
];

const branchProtection = new Map([
  [
    "main",
    {
      requiredApprovals: 2,
      requiredStatusChecks: true,
      requireConversationResolution: true,
    },
  ],
  [
    "release/2026.10",
    {
      requiredApprovals: 1,
      requiredStatusChecks: true,
      requireConversationResolution: true,
    },
  ],
]);

function printHeading(title) {
  console.log(`\n=== ${title} ===`);
}

function showRows(rows) {
  for (const row of rows) {
    console.log(JSON.stringify(row));
  }
}

/*
 * A basic CTE isolates filtering from the final projection.
 *
 * In a Node application this string would normally be sent through a
 * PostgreSQL client. Keeping SQL in a named function makes the query reusable
 * without pretending that a CTE itself persists after the statement ends.
 */
function buildBasicCteQuery() {
  return `
    WITH open_pull_requests AS (
      SELECT
        pr.id,
        pr.title,
        pr.author,
        pr.target_branch
      FROM pull_requests AS pr
      WHERE pr.state = 'open'
    )
    SELECT id, title, author
    FROM open_pull_requests
    WHERE target_branch = $1
    ORDER BY id;
  `;
}

/*
 * Multiple CTEs form a pipeline. Each CTE has a narrower responsibility:
 * candidate Pull Requests, review aggregation, and check aggregation.
 */
function buildCtePipelineQuery() {
  return `
    WITH
    open_prs AS (
      SELECT id, target_branch
      FROM pull_requests
      WHERE state = 'open'
    ),
    review_summary AS (
      SELECT
        pull_request_id,
        COUNT(*) AS review_count,
        COUNT(*) FILTER (
          WHERE review_state = 'approved'
        ) AS approval_count
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
        ) AS failed_checks
      FROM status_checks
      GROUP BY pull_request_id
    )
    SELECT
      p.id,
      p.target_branch,
      COALESCE(r.review_count, 0) AS review_count,
      COALESCE(r.approval_count, 0) AS approval_count,
      COALESCE(c.passed_checks, 0) AS passed_checks,
      COALESCE(c.failed_checks, 0) AS failed_checks
    FROM open_prs AS p
    LEFT JOIN review_summary AS r
      ON r.pull_request_id = p.id
    LEFT JOIN check_summary AS c
      ON c.pull_request_id = p.id
    ORDER BY p.id;
  `;
}

/*
 * A recursive CTE has an anchor term and a recursive term. This query walks a
 * branch hierarchy while maintaining a path. PostgreSQL arrays make cycle
 * detection explicit and avoid relying on an arbitrary recursion depth alone.
 */
function buildRecursiveBranchQuery() {
  return `
    WITH RECURSIVE branch_tree AS (
      SELECT
        b.id,
        b.branch_name,
        0 AS depth,
        ARRAY[b.id] AS path
      FROM branches AS b
      WHERE b.branch_name = $1

      UNION ALL

      SELECT
        child.id,
        child.branch_name,
        tree.depth + 1,
        tree.path || child.id
      FROM branch_tree AS tree
      JOIN branch_relationships AS relation
        ON relation.parent_branch_id = tree.id
      JOIN branches AS child
        ON child.id = relation.child_branch_id
      WHERE NOT child.id = ANY(tree.path)
    )
    SELECT
      branch_name,
      depth,
      path
    FROM branch_tree
    ORDER BY depth, branch_name;
  `;
}

/*
 * Nested CTEs can represent a query's semantic stages. The first CTE chooses
 * the latest review per reviewer. The second CTE turns that row set into
 * approval facts. The application only consumes the final result.
 */
function buildLatestDecisionQuery() {
  return `
    WITH ranked_reviews AS (
      SELECT
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
    latest_decisions AS (
      SELECT
        pull_request_id,
        reviewer_id,
        review_state
      FROM ranked_reviews
      WHERE reviewer_rank = 1
    ),
    active_approvals AS (
      SELECT
        pull_request_id,
        COUNT(*) AS approval_count
      FROM latest_decisions
      WHERE review_state = 'approved'
      GROUP BY pull_request_id
    )
    SELECT *
    FROM active_approvals
    ORDER BY pull_request_id;
  `;
}

/*
 * This CTE demonstrates a domain-specific merge eligibility pipeline. The
 * application does not infer policy from a single review row. It combines
 * independent CTEs only at the final policy evaluation stage.
 */
function buildMergeEligibilityQuery() {
  return `
    WITH
    protected_targets AS (
      SELECT
        branch_id,
        required_approvals,
        require_status_checks,
        require_conversation_resolution
      FROM branch_protection
      WHERE enabled = TRUE
    ),
    latest_reviewer_decisions AS (
      SELECT
        pull_request_id,
        reviewer_id,
        review_state,
        ROW_NUMBER() OVER (
          PARTITION BY pull_request_id, reviewer_id
          ORDER BY submitted_at DESC, review_id DESC
        ) AS reviewer_rank
      FROM reviews
    ),
    active_approvals AS (
      SELECT
        pull_request_id,
        COUNT(*) AS approvals
      FROM latest_reviewer_decisions
      WHERE reviewer_rank = 1
        AND review_state = 'approved'
      GROUP BY pull_request_id
    ),
    check_summary AS (
      SELECT
        pull_request_id,
        COUNT(*) FILTER (WHERE status = 'passed') AS passed_checks,
        COUNT(*) FILTER (
          WHERE status IN ('failed', 'cancelled', 'pending')
        ) AS non_green_checks
      FROM status_checks
      GROUP BY pull_request_id
    ),
    unresolved_conversations AS (
      SELECT
        pull_request_id,
        COUNT(*) AS unresolved_count
      FROM review_comments
      WHERE resolved = FALSE
      GROUP BY pull_request_id
    )
    SELECT
      pr.id,
      pr.title,
      CASE
        WHEN pr.state <> 'open'
          THEN 'Pull Request is not open'
        WHEN COALESCE(a.approvals, 0) < p.required_approvals
          THEN 'approval requirement not met'
        WHEN p.require_status_checks
             AND COALESCE(c.non_green_checks, 0) > 0
          THEN 'required checks are not green'
        WHEN p.require_conversation_resolution
             AND COALESCE(u.unresolved_count, 0) > 0
          THEN 'review conversations remain unresolved'
        ELSE 'eligible'
      END AS merge_condition
    FROM pull_requests AS pr
    JOIN protected_targets AS p
      ON p.branch_id = pr.target_branch_id
    LEFT JOIN active_approvals AS a
      ON a.pull_request_id = pr.id
    LEFT JOIN check_summary AS c
      ON c.pull_request_id = pr.id
    LEFT JOIN unresolved_conversations AS u
      ON u.pull_request_id = pr.id
    WHERE pr.id = ANY($1)
    ORDER BY pr.id;
  `;
}

/*
 * JavaScript's Map is useful for local query-result transformation after the
 * database has already performed relational work. This complements CTEs:
 * SQL handles set-based grouping, while JavaScript can present the result.
 */
function calculateLocalReviewMetrics(prId) {
  const prReviews = reviews.filter(
    (review) => review.pullRequestId === prId,
  );

  const latestByReviewer = new Map();

  for (const review of prReviews) {
    const previous = latestByReviewer.get(review.reviewer);

    if (
      previous === undefined ||
      new Date(review.submittedAt) > new Date(previous.submittedAt)
    ) {
      latestByReviewer.set(review.reviewer, review);
    }
  }

  const activeApprovals = [...latestByReviewer.values()].filter(
    (review) => review.state === "approved",
  ).length;

  return {
    pullRequestId: prId,
    reviewCount: prReviews.length,
    uniqueReviewers: latestByReviewer.size,
    activeApprovals,
  };
}

/*
 * This event-driven model represents a JavaScript-specific complement to SQL.
 * Each state transition emits an event, while the SQL CTEs can later analyze
 * the persisted events in set-based form.
 */
class PullRequestWorkflow {
  #listeners = new Map();

  constructor(pullRequest) {
    this.pullRequest = structuredClone(pullRequest);
  }

  on(eventName, listener) {
    if (!this.#listeners.has(eventName)) {
      this.#listeners.set(eventName, []);
    }

    this.#listeners.get(eventName).push(listener);
    return this;
  }

  #emit(eventName, payload) {
    for (const listener of this.#listeners.get(eventName) ?? []) {
      listener(payload);
    }
  }

  changeState(nextState) {
    const allowedTransitions = {
      draft: new Set(["open", "closed"]),
      open: new Set(["closed", "merged"]),
      closed: new Set(["open"]),
      merged: new Set(),
    };

    const currentState = this.pullRequest.state;
    const allowed = allowedTransitions[currentState];

    if (!allowed || !allowed.has(nextState)) {
      throw new Error(
        `Invalid Pull Request transition: ${currentState} -> ${nextState}`,
      );
    }

    const previousState = this.pullRequest.state;
    this.pullRequest.state = nextState;

    this.#emit("stateChanged", {
      pullRequestId: this.pullRequest.id,
      previousState,
      nextState,
    });
  }

  get state() {
    return this.pullRequest.state;
  }
}

function demonstrateEventDrivenWorkflow() {
  printHeading("Event-driven Pull Request lifecycle");

  const workflow = new PullRequestWorkflow({
    id: 105,
    title: "Build recursive reporting query",
    state: "draft",
  });

  workflow.on("stateChanged", (event) => {
    console.log(
      `PR ${event.pullRequestId}: ` +
      `${event.previousState} -> ${event.nextState}`,
    );
  });

  workflow.changeState("open");
  workflow.changeState("closed");

  try {
    workflow.changeState("merged");
  } catch (error) {
    console.log(`Rejected invalid transition: ${error.message}`);
  }
}

function validateQueryParameters(branch) {
  /*
   * SQL parameter binding remains the primary defense against injection.
   * This validation adds domain constraints before the query is sent.
   */
  if (typeof branch !== "string" || branch.length === 0) {
    throw new TypeError("Target branch must be a non-empty string.");
  }

  if (branch.length > 255) {
    throw new RangeError("Target branch is too long.");
  }

  return branch;
}

async function simulateDatabaseExecution(query, parameters) {
  /*
   * No database dependency is required for this educational executable.
   * A production implementation would call a PostgreSQL driver's parameterized
   * query method here. The function is async to demonstrate the natural
   * Node.js boundary between application logic and database I/O.
   */
  await Promise.resolve();

  return {
    database: DEMO_DATABASE,
    query: query.trim(),
    parameters,
  };
}

async function run() {
  printHeading("Advanced SQL CTEs with Node.js");
  console.log(`Target branch: ${validateQueryParameters(targetBranch)}`);

  printHeading("Basic CTE");
  console.log(
    await simulateDatabaseExecution(
      buildBasicCteQuery(),
      [targetBranch],
    ),
  );

  printHeading("Multiple CTE pipeline");
  console.log(await simulateDatabaseExecution(buildCtePipelineQuery(), []));

  printHeading("Recursive CTE");
  console.log(
    await simulateDatabaseExecution(
      buildRecursiveBranchQuery(),
      ["main"],
    ),
  );

  printHeading("Nested CTE and latest reviewer decisions");
  console.log(
    await simulateDatabaseExecution(
      buildLatestDecisionQuery(),
      [],
    ),
  );

  printHeading("Merge eligibility CTE pipeline");
  console.log(
    await simulateDatabaseExecution(
      buildMergeEligibilityQuery(),
      [[101, 102, 103]],
    ),
  );

  printHeading("Local JavaScript review metrics");
  showRows(
    pullRequests.map((pullRequest) =>
      calculateLocalReviewMetrics(pullRequest.id),
    ),
  );

  demonstrateEventDrivenWorkflow();

  printHeading("Security validation");
  console.log(
    await simulateDatabaseExecution(
      buildBasicCteQuery(),
      [validateQueryParameters("main")],
    ),
  );

  printHeading("Query-design distinctions");
  console.log(
    "A CTE is statement-scoped reusable query logic; a recursive CTE " +
    "extends that idea to hierarchical or linked data; JavaScript " +
    "orchestration decides when the database query runs.",
  );
}

run().catch((error) => {
  console.error("Application failure:", error.message);
  process.exitCode = 1;
});
