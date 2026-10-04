# Advanced SQL: CTEs, Recursive CTEs, Nested CTEs, and Reusable Query Logic

## Scope

This repository is a practical study of Common Table Expressions in advanced SQL. The implementations use a repository-governance domain because it creates realistic relational workloads involving Pull Requests, Code Review, Approvals, status checks, branches, and branch-protection policies.

The domain is deliberately separated into four concerns:

| Concern | Role in the model |
| --- | --- |
| Pull Request | Represents a proposed change, its source branch, target branch, author, and lifecycle state. |
| Code Review | Represents reviewer evaluation, review states, and line-level discussion. |
| Approval | Represents an explicit approval decision that may contribute to a merge requirement. |
| Branch Protection | Represents repository-level policy such as required approvals, required checks, conversation resolution, and protected-branch restrictions. |

The SQL is the primary implementation of the topic. Python, JavaScript, C++, and Java provide different ways to reason about the same relational transformations rather than simply translating one program into four other languages.

## Why CTEs Matter

A Common Table Expression gives a SQL statement a named intermediate result.

The basic shape is:

`WITH named_relation AS (SELECT ...) SELECT ... FROM named_relation;`

The CTE does not normally create a permanent database object. Its scope is the statement containing the `WITH` clause.

This makes CTEs useful when a query has a sequence of meaningful relational transformations. Instead of repeating a complicated expression, the query can name the intermediate relation and allow later stages to consume it.

For example, the SQL implementation first identifies open Pull Requests, then calculates review statistics, then calculates status-check statistics, and finally joins those results. Each stage has a clear relational responsibility.

The distinction is important:

- A CTE is temporary query structure.
- A view is a persistent named query definition.
- A materialized view stores query results and has refresh semantics.
- A SQL function can expose reusable parameterized database logic.
- A temporary table stores intermediate data as a database object for the transaction or session.

A CTE should not automatically be treated as a performance optimization. Its primary benefit is query structure and composability. PostgreSQL may inline a CTE or materialize it depending on the query and optimizer decisions, and `MATERIALIZED` or `NOT MATERIALIZED` can influence that behavior.

## Basic CTEs

The Python program starts with a basic CTE that selects open Pull Requests.

The important mechanism is that the `open_pull_requests` relation is created once and then consumed by the outer query. The CTE separates filtering from final presentation.

The JavaScript implementation represents the same database-side idea as a PostgreSQL query builder function. JavaScript does not attempt to implement SQL semantics itself. It constructs parameterized SQL that a PostgreSQL driver could execute.

The C++ and Java implementations take a different perspective. They model intermediate relations as native collections and records. This makes the distinction between database-side set processing and application-side processing visible.

A CTE is particularly valuable when an intermediate relation has a meaningful business interpretation. A name such as `open_pull_requests` communicates considerably more than embedding the same filtering predicate repeatedly in unrelated parts of a large query.

## Chained and Nested CTEs

Complex SQL commonly needs more than one intermediate relation.

A chained query can look conceptually like:

`WITH open_prs AS (...), review_summary AS (...), check_summary AS (...) SELECT ...`

Later CTEs can reference earlier CTEs, which allows a query to form a pipeline.

The SQL implementation uses this approach for repository governance:

- `open_prs` establishes the candidate Pull Request set.
- `review_summary` aggregates Code Review activity.
- `check_summary` aggregates CI/status-check outcomes.
- The final relation combines those independent facts.

This prevents unrelated aggregations from becoming one large expression.

Nested CTE logic goes one step further. An intermediate CTE can itself be consumed by another CTE that derives a classification. The SQL implementation creates `review_summary` and then creates `review_condition` from that result.

This is useful when a query has a semantic transformation such as:

`raw rows -> aggregate facts -> classification -> final result`

The intermediate names become part of the query's reasoning structure.

## Reusable Query Logic

CTEs are reusable within one statement, not across arbitrary statements.

The repository examples use reusable SQL patterns in two ways.

First, a CTE can be written as a stable intermediate stage that is referenced multiple times later in the same statement.

Second, application code can keep a parameterized SQL statement as a reusable template. The JavaScript example accepts a target branch as a parameter instead of constructing SQL through string concatenation.

This distinction matters for security. A CTE does not prevent SQL injection. Parameters must still be bound through the database driver's parameter mechanism.

The Python implementation demonstrates parameter binding through `sqlite3` placeholders. The JavaScript implementation represents PostgreSQL positional parameters such as `$1`. The SQL itself remains separate from caller-controlled values.

Reusable logic should also be evaluated for lifecycle requirements. If the same query is needed by many applications, a view or SQL function may be a better abstraction than copying a CTE into every application query.

## Recursive CTEs

A recursive CTE extends the ordinary CTE model to data whose rows point back to other rows.

Its conceptual structure is:

`WITH RECURSIVE relation AS (anchor UNION ALL recursive_member) SELECT ...`

The anchor establishes the starting row set.

The recursive member takes rows already discovered and finds additional rows.

The SQL implementation uses this structure to traverse branch relationships and commit ancestry.

### Branch traversal

The branch relationship table represents edges:

`parent_branch_id -> child_branch_id`

The recursive query starts at `main`, discovers its children, then discovers children of those children.

The result contains a depth value and a path.

The depth answers how far a branch is from the root.

The path is important because branch relationships can become graph data rather than a clean tree. A cycle such as:

`main -> release/2026.10 -> hotfix/auth -> main`

would otherwise allow recursion to continue indefinitely.

The SQL implementation prevents revisiting a branch already present in the path. PostgreSQL also provides `SEARCH` and `CYCLE` facilities for recursive query processing.

### Commit ancestry

Commit history provides a different recursive structure.

A commit has a `parent_sha`. Starting from the latest commit and repeatedly following `parent_sha` creates a linked-chain traversal.

This is different from branch hierarchy traversal because the data structure is closer to a linked list than a tree.

The recursive SQL therefore demonstrates that recursive CTEs are not restricted to organizational hierarchies. They can represent graph walks, ancestry, dependency chains, category trees, organizational structures, and other transitive relationships.

## Recursive CTE Termination

Recursive queries require a termination strategy.

A well-designed recursive query should consider:

- A finite data set that naturally reaches an endpoint.
- A cycle-detection mechanism when relationships can contain loops.
- A depth limit as an operational safety boundary.
- Appropriate indexing on the recursive join columns.
- The possibility of duplicate edges.
- The size of the reachable graph.

Path tracking is a semantic solution because it identifies exactly which nodes have already occurred on the current path.

A depth ceiling is a defensive operational limit. It should not replace correct cycle handling when cycles are meaningful possibilities in the data.

The C++ implementation uses an `unordered_set` to prevent revisiting nodes. The Java implementation uses a `HashSet`. Both make the algorithmic purpose of recursive termination explicit.

## CTEs and Window Functions

Window functions and CTEs solve different problems and work well together.

A window function preserves individual rows while calculating information over a related set of rows.

The repository uses:

`ROW_NUMBER() OVER (PARTITION BY pull_request_id, reviewer_id ORDER BY submitted_at DESC, review_id DESC)`

This ranks review records for each Pull Request and reviewer.

The CTE then filters the ranked result to obtain the latest decision.

This matters for approval analysis. A reviewer might have approved a Pull Request earlier and subsequently submitted a different review state. Counting every historical approval would incorrectly treat the old approval as active.

The CTE provides the intermediate ranked relation. The window function provides the ordering and partition semantics. The final query consumes only the latest row for each reviewer.

This is substantially different from a simple `GROUP BY`, because grouping collapses rows while window functions retain the underlying rows.

## Pull Request Workflow and CTE Analysis

The Pull Request table represents the proposed change and its lifecycle.

The SQL model supports states such as:

- `draft`
- `open`
- `closed`
- `merged`

The CTE examples use Pull Request state to establish candidate sets, but they do not confuse Pull Request lifecycle with review policy.

For example, an open Pull Request is a candidate for further merge evaluation. That does not mean it is mergeable.

The merge-eligibility pipeline combines independent facts only at the final evaluation stage.

This creates a useful relational flow:

`Pull Request state -> review facts -> approval facts -> status-check facts -> conversation facts -> branch policy -> eligibility`

The intermediate CTEs keep these relationships visible.

## Code Review as a Separate Domain

Code Review concerns how reviewers evaluate the proposed changes.

The model stores:

- reviewer identity
- review state
- submission time
- review body
- line-level comments
- comment resolution state

Review states include:

`commented`, `approved`, `changes_requested`, and `dismissed`.

The CTE logic does not treat every review as an approval. Instead, it derives the latest reviewer decision and then identifies approvals from that relation.

This is important because historical review rows represent events or decisions at different points in the Pull Request lifecycle.

Review comments are also separate from the review decision itself. A Pull Request can contain resolved or unresolved discussion even when an approval exists.

The merge-eligibility query therefore calculates unresolved conversations separately.

## Approvals as a Distinct Decision

An approval is not merely another review row.

The SQL implementation treats an active approval as a current reviewer decision after considering the latest review submitted by that reviewer.

This avoids a common analytical error:

A reviewer approves a Pull Request, later submits a different review state, and the query still counts the old approval.

The `ROW_NUMBER()` CTE solves this by selecting the latest decision per reviewer.

Approval requirements are then evaluated against the branch-protection policy.

For example, a policy requiring two approvals can be evaluated using:

`active_approvals >= required_approvals`

The query does not hard-code the number two into the final policy calculation. The requirement comes from the `branch_protection` relation.

This is an important form of reusable query logic because the same eligibility pipeline can operate against branches with different approval thresholds.

## Branch Protection as Repository Policy

Branch Protection represents repository governance rather than reviewer behavior.

The model includes:

- required approvals
- required status checks
- direct-push restrictions
- force-push restrictions
- branch deletion restrictions
- required conversation resolution
- linear-history requirements

The SQL implementation stores these rules as data.

That allows the merge-eligibility query to consume policy rows instead of embedding repository-specific values throughout the query.

The relationship is therefore:

`Pull Request` proposes the change.

`Code Review` evaluates the change.

`Approval` records a review decision that may satisfy part of the policy.

`Branch Protection` defines which conditions must be satisfied before the protected branch accepts the merge.

This separation prevents the four concepts from becoming one generic "approval" field.

## Merge Eligibility CTE Pipeline

The central governance query demonstrates a multi-stage CTE design.

`protected_targets` selects active policies for protected target branches.

`ranked_reviews` assigns a deterministic rank to each reviewer decision.

`latest_reviewer_decisions` keeps only the current decision for each reviewer.

`active_approval_counts` calculates the number of current approvals.

`status_summary` aggregates CI outcomes.

`conversation_summary` identifies unresolved review comments.

`merge_eligibility` combines these independent facts and evaluates the final condition.

The final decision can therefore identify distinct failure causes:

- the Pull Request is not open
- the required approval count is not satisfied
- required checks are failed or pending
- review conversations remain unresolved

This structure is preferable to a large expression that mixes all of these concerns in one query block.

## Python Implementation

The Python program uses only the standard-library `sqlite3` module and creates an in-memory database.

This makes the demonstration executable without an external Python dependency.

The schema intentionally contains enough relationships to demonstrate:

- ordinary CTE filtering
- multiple CTE stages
- nested classification
- recursive branch traversal
- recursive commit traversal
- window functions
- merge-eligibility evaluation
- latest reviewer decisions
- cycle protection
- CTE-backed updates
- transaction handling
- parameterized SQL
- query-plan inspection

The Python program also demonstrates a practical limitation: SQL dialects differ. PostgreSQL provides more advanced data-modifying CTE behavior than SQLite, so the Python example uses SQLite-compatible statements rather than presenting PostgreSQL-only syntax as if it were portable.

This distinction is important when moving CTE-heavy applications between database engines.

## JavaScript Implementation

The JavaScript implementation uses Node.js and does not require an npm dependency.

Its main purpose is to show the application boundary around advanced SQL.

Named functions return PostgreSQL-compatible SQL statements, including:

- a basic CTE
- a chained CTE pipeline
- a recursive branch query
- latest reviewer decision logic
- merge-eligibility analysis

The application layer uses parameter placeholders instead of concatenating user-controlled values into SQL.

The program also includes an event-driven Pull Request lifecycle model. This is intentionally separate from SQL query logic. JavaScript event handling is appropriate for reacting to application events, while SQL CTEs are appropriate for set-based analysis of persisted relational data.

This difference demonstrates why a JavaScript implementation should complement rather than merely translate the SQL.

## C++ Case Study

The C++ program models a repository-governance engine.

Its domain structures represent Pull Requests, reviews, comments, status checks, and branch policies.

`RepositoryGovernanceEngine` performs set-oriented aggregations using C++ collections.

The `latestReviews()` method corresponds conceptually to a SQL CTE containing `ROW_NUMBER()`. It keeps the latest review per Pull Request and reviewer.

`activeApprovalCount()` then consumes that intermediate relation.

`evaluatePullRequest()` combines approval, status-check, and conversation facts against branch policy.

The recursive branch traversal uses an adjacency list and an `unordered_set` for cycle protection. Its traversal complexity is approximately `O(V + E)` for reachable vertices and edges.

The C++ implementation also validates invalid relationships and duplicate Pull Request identifiers through exceptions.

This case study is useful for understanding the boundary between SQL recursion and application algorithms. A recursive CTE can execute graph traversal close to the data, while an application implementation may make the same algorithm explicit in memory.

## Java Enterprise Model

The Java implementation uses records, enums, collections, streams, explicit service classes, and immutable record state.

The `ReviewSummary` and `CheckSummary` records act as typed intermediate relations.

`QueryLogicService` performs the transformations that correspond to chained CTE stages.

The latest-review logic uses timestamp ordering to identify the current decision for each reviewer. This mirrors the semantics of the SQL window function without copying SQL syntax into Java.

`BranchHierarchyService` models recursive traversal and uses a visited set to prevent cycles.

`PullRequestLifecycleService` models state transitions separately from merge-policy evaluation. This makes an important enterprise design distinction explicit: a workflow state transition is not the same thing as a policy decision.

The Java implementation is therefore closer to a service-domain architecture than the SQL script. The SQL database remains responsible for relational filtering, joining, aggregation, and integrity enforcement when the application is connected to PostgreSQL.

## Relational Integrity

The SQL schema uses database constraints to enforce rules that should not depend entirely on application code.

Examples include:

- primary keys for entity identity
- foreign keys for relationships
- unique constraints for repository and branch identity
- check constraints for valid Pull Request states
- check constraints for valid review states
- check constraints for valid status-check states
- positive line numbers for review comments
- non-negative approval requirements
- prevention of a Pull Request targeting its own source branch

These constraints complement CTEs.

A CTE analyzes relations. A constraint protects the validity of stored data.

They should not be treated as interchangeable mechanisms.

## Indexing and Performance

CTEs do not inherently make a query faster.

The important performance questions concern the relations consumed by the CTE pipeline and the joins performed between intermediate results.

The SQL schema indexes:

`pull_requests(target_branch_id, state)`

This supports filtering Pull Requests by protected target branch and lifecycle state.

`reviews(pull_request_id, reviewer_id, submitted_at DESC)` supports review aggregation and latest-decision analysis.

`review_comments(review_id, resolved)` supports resolution checks.

`status_checks(pull_request_id, status)` supports status aggregation.

`commits(pull_request_id, committed_at DESC)` supports latest-commit analysis.

`branch_relationships(parent_branch_id)` supports recursive child discovery.

A CTE may still produce a large intermediate relation. `EXPLAIN` and `EXPLAIN ANALYZE` should be used to understand actual execution behavior.

The SQL script includes both ordinary execution-plan inspection and examples using `MATERIALIZED` and `NOT MATERIALIZED`.

## MATERIALIZED and NOT MATERIALIZED

PostgreSQL can choose whether to inline a suitable CTE or materialize it depending on the query.

`MATERIALIZED` explicitly requests materialization.

This can be useful when a costly intermediate result is referenced multiple times and computing it once is preferable.

It can also hurt performance when predicate pushdown would have reduced the amount of data processed.

`NOT MATERIALIZED` permits the optimizer to inline the CTE when appropriate.

Therefore, CTE materialization should be treated as an execution-plan decision rather than a stylistic rule.

The correct choice depends on data volume, number of references, predicates, indexes, and the PostgreSQL planner's chosen strategy.

## Transactions and CTEs

A CTE defines query structure.

A transaction defines atomicity.

These are separate concepts.

The SQL script demonstrates a transaction containing a CTE-backed update. The CTE determines which Pull Requests have failed checks, while `BEGIN` and `COMMIT` determine whether the update becomes durable as a unit.

A data-modifying CTE can also participate in PostgreSQL's statement-level execution model.

The important design principle is not to assume that adding a CTE automatically provides transactional behavior. Transaction boundaries must still be managed explicitly.

## Common Failure Modes

### Reusing a CTE outside its statement

A CTE is normally visible only to the statement containing its `WITH` clause.

Trying to query a CTE name from a later independent statement fails because the relation was never created as a persistent database object.

When persistent reuse is required, a view, materialized view, SQL function, or table may be more appropriate.

### Counting historical approvals as current approvals

A simple count of rows where `review_state = 'approved'` can be wrong if reviewers can submit subsequent decisions.

The latest-review CTE prevents historical approvals from being counted as current approvals.

### Ignoring recursive cycles

A recursive CTE over graph data can repeatedly revisit the same rows.

Path tracking, `CYCLE`, or another explicit termination strategy should be used when the relationship is not guaranteed to be acyclic.

### Treating a recursive query as automatically cheap

Recursive execution can become expensive for large graphs or deep hierarchies.

The recursive join should be indexed appropriately, and the reachable data set should be bounded where business rules permit.

### Using a CTE to hide a bad query plan

A query can become easier to read while remaining slow.

The solution is not automatically to remove the CTE. The execution plan should be inspected to identify large scans, repeated work, poor join strategies, or ineffective predicates.

### Mixing domain responsibilities

A review is not an approval.

An approval is not branch protection.

Branch protection is not Pull Request lifecycle state.

A query that collapses all four into one generic status loses important semantics and makes policy debugging harder.

## Security Considerations

Application code should use parameterized queries.

The Python example binds values through SQLite parameters.

The JavaScript example uses PostgreSQL-style placeholders.

The SQL text should not be built by concatenating arbitrary branch names, repository names, reviewer names, or other external values into SQL syntax.

CTEs do not provide SQL-injection protection.

Database permissions also matter. A reporting query should not automatically receive permissions to modify repository data. Read-only database roles are appropriate for reporting workloads when updates are unnecessary.

Recursive queries require resource awareness. A malicious or accidentally cyclic graph can consume substantial database resources without appropriate termination conditions.

## Debugging CTE Queries

A practical debugging method is to execute the query one logical CTE stage at a time.

For example, inspect:

`open_prs`

before inspecting:

`review_summary`

then inspect:

`active_approval_counts`

then inspect:

`status_summary`

and finally inspect:

`merge_eligibility`.

This makes it easier to determine whether an incorrect final result originates from filtering, aggregation, latest-review selection, policy joining, or final classification.

A CTE's intermediate result can also be temporarily changed into a final `SELECT` during development.

For recursive queries, inspect:

- the anchor result
- depth
- path
- number of rows produced at each depth
- termination conditions

The PostgreSQL `EXPLAIN (ANALYZE, BUFFERS, VERBOSE)` example in the SQL implementation provides the execution-level perspective.

## Design Relationships

The implementations demonstrate a progression from simple query composition to policy-oriented recursive analysis:

`base relational rows`

become

`named CTE`

then

`chained CTEs`

then

`window-function CTEs`

then

`recursive CTEs`

and finally

`multi-stage policy evaluation`.

The same progression appears in the application implementations, but with language-specific data structures and control flow.

Python emphasizes executable SQL against an in-memory database.

JavaScript emphasizes parameterized SQL construction and event-driven application orchestration.

C++ emphasizes explicit algorithms, hash-based intermediate relations, validation, and graph traversal.

Java emphasizes typed domain objects, service boundaries, state modeling, and immutable intermediate results.

PostgreSQL provides the actual relational mechanisms, constraints, indexes, recursive queries, data-modifying CTEs, and execution-plan inspection.

## Practical Interpretation

CTEs are most valuable when a complex SQL statement has meaningful intermediate relations.

A useful CTE usually has a reason to exist beyond shortening the query. Its name should communicate what the relation means, and its columns should represent a coherent intermediate result.

Recursive CTEs are appropriate when the desired result depends on repeatedly following relationships in the data.

Nested CTEs are useful when a query naturally has several semantic transformations.

Window functions inside CTEs are useful when row-level information must be retained while deriving ranks, latest decisions, running values, or partition-level metrics.

Reusable CTE logic is especially effective when several policy conditions depend on the same intermediate relation.

The key design principle is to use CTEs to make relational reasoning explicit without assuming that naming an intermediate result automatically improves execution performance.
