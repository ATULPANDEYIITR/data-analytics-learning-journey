# Python Error Handling: Exceptions, Defensive Programming, and Reliable Repository Workflows

## Technical scope

Error handling defines how software responds when an operation cannot safely complete. Python supports this through exception propagation, `try` and `except`, `else`, `finally`, custom exception classes, exception chaining, and deliberate validation of application state.

The implementations in this collection use repository governance as a practical domain. A pull request may be rejected because its input is invalid, a reviewer is ineligible, a required check has failed, or the requested operation violates branch policy. These failures are not interchangeable. Reliable code identifies their causes, reports them accurately, and preserves valid state when an operation fails.

The central design principle is to distinguish expected domain failures from unexpected programming or infrastructure failures. A policy violation should be reported as a policy violation, not hidden by a broad exception handler or misrepresented as a successful merge.

## Exception fundamentals

An exception interrupts normal execution and transfers control to a matching handler. If no handler catches it, the exception propagates toward the caller. This allows low-level code to report a failure while higher-level code decides whether to retry, reject an operation, display a message, or terminate.

Python's exception hierarchy supports meaningful categories:

| Exception | Intended meaning in the Python implementation |
|---|---|
| `ValidationError` | Submitted repository or pull request data violates a domain rule. |
| `PullRequestStateError` | A lifecycle operation is invalid for the pull request's current state. |
| `ReviewPolicyError` | A review decision violates reviewer or review policy. |
| `ApprovalError` | Approval requirements cannot be satisfied. |
| `ProtectionError` | A merge or protected-branch operation is prohibited. |
| `PersistenceError` | Governance configuration cannot be read or written safely. |
| `RetryableOperationError` | A temporary operational failure may succeed on another attempt. |

These classes inherit from `GovernanceError`, allowing callers to catch all expected governance failures when that behavior is appropriate. Callers can also catch a narrower type when they need to respond differently to a validation failure and a branch-protection rejection.

### `try`, `except`, `else`, and `finally`

A `try` block contains an operation that may fail. An `except` block handles a matching exception. An `else` block runs only when the `try` block finishes without raising an exception. A `finally` block runs during normal completion and exception propagation, making it useful for cleanup.

A database client, temporary file, or network connection may need cleanup regardless of whether an operation succeeds. The JavaScript implementation uses `finally` to remove a temporary directory, while the Python implementation uses it to demonstrate unconditional cleanup and uses a temporary-file replacement workflow for persistence.

A `finally` block should not return a value or raise an unrelated exception casually. Doing so can suppress or replace the original failure and make debugging harder.

### Exception chaining

When lower-level operations fail, callers often need to add domain context without losing the original cause.

The Python persistence functions use the pattern `raise PersistenceError("...") from exc`. The new exception communicates the application's failure category, while `exc` retains the original filesystem or JSON parsing failure.

This distinction is important for operational diagnostics. A user-facing message can remain concise while logs and tracebacks preserve the underlying cause.

## Python implementation

The Python program models repository governance with dataclasses, enumerations, custom exceptions, and explicit validation.

### Pull request lifecycle

The `PullRequest` class supports publishing a draft, accepting reviews, recording status checks, synchronizing a changed head commit, and merging after policy evaluation.

Its state transitions reject operations that are invalid for the current state. For example, a merged pull request cannot be published again. A synchronized pull request clears its status checks because results from an earlier changeset do not establish that the new changeset passes those checks.

A lifecycle exception is preferable to returning an ambiguous value such as `False`. It gives the caller a precise explanation of why the requested transition failed.

### Approval evaluation

The `current_approvals` function counts distinct reviewers whose approvals apply to the current commit. When stale approvals are dismissed by policy, a review against an earlier commit is ignored.

The implementation also treats a reviewer's latest changes-requested decision as a blocking decision. This illustrates why approval evaluation is not simply a count of every historical review marked `approved`.

The `evaluate_merge` function collects multiple violations rather than raising after the first failure. It evaluates:

- Whether the pull request is open.
- Whether enough current approvals exist.
- Whether required status checks have passed.
- Whether review discussions are resolved when the policy requires it.

The `merge_pull_request` function raises `ProtectionError` when any condition fails. It changes the state to `merged` only after all conditions pass.

### Defensive validation

Validation occurs when domain objects are created and when state-changing operations are invoked. Repository names, commit identifiers, reviewer identities, branch names, and thread counts are checked at their respective boundaries.

This approach reduces invalid intermediate states. It also produces failures close to their origin, where the program has enough context to identify the invalid value.

The `run_with_recovery` function catches explicitly selected expected exceptions. It does not catch every possible exception by default. An unexpected `AttributeError`, for example, should not silently become an ordinary policy rejection.

### Safe persistence

The JSON persistence functions distinguish missing files, permission failures, malformed JSON, and invalid top-level data. The save operation writes to a temporary file in the destination directory before replacing the target.

Writing the temporary file in the same directory makes an atomic replacement more likely on the same filesystem. This protects readers from observing a partially written destination during the replacement operation, but it does not provide a full transactional storage system or guarantee crash durability in every environment.

Production code should also consider file permissions, concurrent writers, configuration versioning, and whether sensitive information is being persisted.

### Bounded retry

The retry demonstration catches only `RetryableOperationError`. It retries a known transient failure and propagates the exception after the configured number of attempts.

Validation failures and policy rejections are not retried because another attempt does not correct their cause. Repeatedly retrying a prohibited merge would waste resources and obscure the actual problem.

Real remote operations may require exponential backoff, jitter, request timeouts, cancellation, and idempotency controls. A retry is safe only when repeating the operation cannot create unintended duplicate effects.

## JavaScript implementation

The JavaScript implementation uses Node.js events and private class fields to model a pull request lifecycle that emits observable state changes.

### Event-driven error reporting

The `PullRequest` class extends `EventEmitter`. It emits events when the state changes, a review is submitted, a check is updated, or the head commit changes.

This separates the domain operation from consumers that need to react to it. An audit logger or user interface can subscribe to events without embedding those responsibilities inside every lifecycle method.

Events are notifications, not automatic transactions. If a listener throws, that failure must be considered explicitly. A production event-driven architecture should define how listener errors, delivery guarantees, and event persistence are handled.

### Private state and snapshots

Private fields such as `#reviews` and `#checks` prevent callers from directly mutating internal collections. The `snapshot` getter returns a detached view of the state.

This reduces accidental changes from outside the class. It does not automatically make every nested object immutable, so the implementation also copies review objects and their comments before returning the snapshot.

### Asynchronous recovery

The `withTemporaryRetry` function uses `async` and `await` to retry temporary service failures without blocking the entire Node.js event loop through synchronous waiting.

The final `demonstrate().catch(...)` handler reports failures that escape the demonstration and sets a nonzero process exit code. This prevents an unhandled top-level failure from being presented as a successful run.

The policy loader separately handles filesystem failures, malformed JSON, and invalid configuration structure. A file that exists and parses successfully can still be invalid for the application.

## C++ case study

The C++ program implements a repository governance engine for a deployment controller. The proposed change validates production deployment manifests before they reach the protected `main` branch.

### Architecture and data structures

The case study uses:

- `PullRequest` to hold the changeset, lifecycle state, reviews, and status-check results.
- `Review` to associate a reviewer decision and inline comments with a specific commit.
- `BranchPolicy` to define approval counts, required checks, and prohibited branch operations.
- `std::map` to maintain named status-check results.
- `std::set` to count distinct eligible reviewers and required check names.
- Custom exception classes to separate input validation, lifecycle errors, and merge rejection.

The implementation keeps merge evaluation separate from the operation that changes the pull request state. This allows eligibility to be inspected without merging the pull request.

### Algorithmic behavior

The approval evaluator tracks the most recent meaningful review decision for each reviewer. It ignores reviews against stale commits when the configured policy requires current approvals.

If \(r\) is the number of review records and \(c\) is the number of required checks, approval evaluation takes \(O(r \log r)\) time in the ordered-map implementation, while checking required checks takes \(O(c \log c)\) map lookups. The total depends on the number of review records and configured checks rather than on the contents of the changeset itself.

The evaluator returns all detected policy violations. This provides a useful diagnostic report rather than forcing the developer to correct one problem, retry, and discover the next.

### Failure handling

Malformed input is rejected by the `PullRequest` constructor. Invalid lifecycle operations raise `TransitionError`, and unsuccessful merge eligibility raises `MergeBlockedError`.

The outer `main` function catches domain failures separately from other standard exceptions. This preserves the distinction between an expected governance rejection and an unexpected runtime failure.

The example is an in-memory policy model, not a complete implementation of a hosted Git service. A production service would need durable storage, concurrency control, authenticated reviewer identities, authoritative status-check records, and protection against changes between policy evaluation and merge execution.

## Java implementation

The Java implementation models enterprise repository governance using explicit domain types and a dedicated merge-eligibility service.

### Domain model

`Repository`, `Commit`, `Review`, `ReviewComment`, and `BranchProtectionPolicy` are records. Their compact constructors validate incoming values and copy collections where appropriate.

The `PullRequest` class manages mutable lifecycle state and maintains its commit history, reviews, and status checks. State changes occur through named methods rather than arbitrary field assignments.

`MergeEligibilityService` evaluates the policy independently of `PullRequest`. This separation makes policy evaluation easier to test and allows the lifecycle object to focus on valid domain transitions.

### Review history and stale approvals

Each review contains the commit SHA against which it was submitted. The service filters stale reviews when policy requires current approvals, then selects the latest eligible review for each reviewer.

This distinction matters when a new commit changes the implementation after review. An approval for an older commit should not automatically be treated as approval of the latest code.

The service uses Java collections and streams to derive eligible reviewer identities. The `Set` representation ensures that one reviewer contributes at most one approval, even if that reviewer submits multiple review records.

### Explicit policy enforcement

`BranchProtectionPolicy` defines required approvals, status checks, resolved conversations, linear-history requirements, and allowed merge strategies.

The `MergeEligibilityService` evaluates these rules and returns immutable violation lists. The `PullRequest.merge` method changes the state only if the list is empty.

The example also distinguishes an invalid state transition from a policy-based merge rejection. This gives callers a reliable way to decide whether the requested operation must be corrected or the policy conditions must first be satisfied.

## PostgreSQL data model

The SQL implementation stores governance information relationally and delegates important integrity rules to PostgreSQL.

### Relationships and constraints

The schema represents repositories, branches, users, pull requests, commits, review policies, required status checks, reviewer eligibility, reviews, review comments, status-check runs, and merge-audit records.

Foreign keys prevent records from referring to nonexistent repositories, branches, users, or pull requests. Unique constraints prevent duplicate repository names, duplicate pull request numbers within a repository, and duplicate commit SHAs within a pull request.

Check constraints enforce valid lifecycle states, review decisions, merge strategies, nonnegative approval counts, valid status-check conclusions, and consistent dismissal metadata.

These database rules protect data even when multiple applications or scripts write to the same tables.

### Trigger-based validation

The `validate_review_submission` trigger checks the pull request's state, rejects self-review, and verifies reviewer eligibility before inserting a review.

This rule belongs near the data because application-level validation alone can be bypassed by another client or by a separate code path.

The trigger does not replace authorization at the application or database-role level. Production systems must still control who can submit reviews and modify governance records.

### Merge evaluation

The `pull_request_merge_evaluation` view uses common table expressions to calculate current approval counts, identify missing or failed required checks, and evaluate branch synchronization and discussion requirements.

`DISTINCT ON` selects the latest eligible review for each reviewer. A lateral query finds the latest check result for each required check on the current head commit.

The `attempt_merge` function locks the pull request row, loads the applicable branch policy, validates the selected merge strategy, and records the result in `merge_audit`.

The function returns a rejection when configured requirements are unmet. PostgreSQL exceptions still propagate for missing records, invalid arguments, and other exceptional conditions. The caller can therefore distinguish an expected policy rejection from an invalid request.

### Transaction and concurrency considerations

The SQL script runs its setup and sample workflow within a transaction. A production merge workflow should use a clearly defined transaction boundary so that policy evaluation, state mutation, and audit recording remain consistent.

Row locking protects the selected pull request row from conflicting updates while the function evaluates it. A complete implementation must also define concurrency behavior for reviews, status checks, policy changes, and target-branch updates.

Application-level exception handling and database transactions solve different problems. Exceptions describe failure to the caller, while transactions determine which database changes commit or roll back.

## Common failure modes and defensive design

### Catching every exception

A broad handler that catches every exception and returns a success-shaped value hides programming errors and makes monitoring unreliable. Catch expected failures at the level where meaningful recovery is possible.

### Treating a failed check as an absent check

A missing status check and a failed status check are distinct operational conditions, but both should block a merge when the check is required. The policy evaluator reports either condition as a violation.

### Counting historical approvals

Historical reviews are valuable for audit purposes, but merge eligibility must follow the configured rules for stale reviews, reviewer eligibility, and changes-requested decisions. Preserve the history while evaluating only the decisions that currently count.

### Retrying non-idempotent operations

Retrying a read operation may be safe, while retrying a partially completed merge or payment-like operation may create duplicate effects. Use idempotency keys, transaction boundaries, or authoritative operation status when retrying actions with side effects.

### Losing the original exception

Replacing a low-level exception without retaining its cause makes diagnosis harder. Python's exception chaining, Java's cause constructors, and JavaScript's `Error` cause option preserve that relationship.

### Performing validation only at the user interface

User interfaces improve feedback but cannot enforce system-wide integrity. Validate inputs in domain methods and enforce persistent invariants with database constraints and appropriate authorization controls.

## Performance, security, and operational considerations

Error handling should provide useful diagnostics without exposing secrets. Exception messages, stack traces, repository credentials, access tokens, and sensitive configuration should not be sent indiscriminately to users or external logs.

Governance evaluation should use indexed queries for common access paths, including pull requests by target branch and state, reviews by pull request and reviewer, and check runs by pull request, check name, and commit SHA. Indexes improve retrieval at the cost of additional storage and write overhead.

A merge decision must be based on authoritative and sufficiently current state. In distributed systems, policy evaluation followed by an unprotected state update creates a time-of-check/time-of-use risk. Locking, transactional updates, immutable audit records, and server-side enforcement help reduce that risk.

Operational monitoring should distinguish rejected operations, transient service failures, invalid configuration, and unexpected exceptions. These categories have different implications for retry behavior, incident response, and system correctness.
