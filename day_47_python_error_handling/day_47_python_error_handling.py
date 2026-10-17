"""Practical error handling for repository governance workflows.

The examples use Python's exception model to validate pull requests,
process code reviews, evaluate approval policies, and protect merge operations.
The script uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
import tempfile
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("repository_governance")

T = TypeVar("T")


# Domain-specific exceptions allow callers to distinguish recoverable
# validation failures from operational and policy failures.
class GovernanceError(Exception):
    """Base exception for repository governance failures."""


class ValidationError(GovernanceError):
    """Raised when submitted repository data violates domain rules."""


class PullRequestStateError(GovernanceError):
    """Raised when a pull request cannot perform the requested transition."""


class ReviewPolicyError(GovernanceError):
    """Raised when a review decision violates review policy."""


class ApprovalError(GovernanceError):
    """Raised when approval requirements are not satisfied."""


class ProtectionError(GovernanceError):
    """Raised when a protected-branch operation is prohibited."""


class PersistenceError(GovernanceError):
    """Raised when governance data cannot be persisted."""


class RetryableOperationError(GovernanceError):
    """Represents a temporary failure that may succeed on retry."""


class PullRequestState(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class ReviewState(str, Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


@dataclass(frozen=True)
class Repository:
    name: str
    default_branch: str = "main"

    def __post_init__(self) -> None:
        if not self.name.strip() or "/" not in self.name:
            raise ValidationError(
                "Repository name must use the owner/repository format."
            )
        if not self.default_branch.strip():
            raise ValidationError("Default branch cannot be empty.")


@dataclass(frozen=True)
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    comments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reviewer.strip():
            raise ValidationError("Reviewer identity is required.")
        if not self.commit_sha.strip():
            raise ValidationError("A review must reference a commit.")
        if any(not comment.strip() for comment in self.comments):
            raise ValidationError("Review comments cannot be blank.")


@dataclass
class PullRequest:
    number: int
    repository: Repository
    title: str
    source_branch: str
    target_branch: str
    author: str
    head_sha: str
    state: PullRequestState = PullRequestState.DRAFT
    reviews: list[Review] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    unresolved_threads: int = 0

    def __post_init__(self) -> None:
        if self.number <= 0:
            raise ValidationError("Pull request number must be positive.")
        if not self.title.strip():
            raise ValidationError("Pull request title cannot be empty.")
        if not self.author.strip():
            raise ValidationError("Pull request author is required.")
        if not self.head_sha.strip():
            raise ValidationError("Head commit SHA is required.")
        if not self.source_branch.strip() or not self.target_branch.strip():
            raise ValidationError("Source and target branches are required.")
        if self.source_branch == self.target_branch:
            raise ValidationError("Source and target branches must differ.")
        if self.unresolved_threads < 0:
            raise ValidationError("Unresolved thread count cannot be negative.")

    def publish(self) -> None:
        if self.state != PullRequestState.DRAFT:
            raise PullRequestStateError(
                "Only a draft pull request can be published."
            )
        self.state = PullRequestState.OPEN
        logger.info("Pull request #%s published.", self.number)

    def add_review(self, review: Review) -> None:
        if self.state != PullRequestState.OPEN:
            raise PullRequestStateError(
                "Reviews can only be submitted to open pull requests."
            )
        if review.reviewer == self.author:
            raise ReviewPolicyError("Authors cannot approve their own changes.")
        self.reviews.append(review)

    def synchronize(self, new_head_sha: str) -> None:
        if self.state != PullRequestState.OPEN:
            raise PullRequestStateError(
                "Only open pull requests can be synchronized."
            )
        if not new_head_sha.strip():
            raise ValidationError("New head SHA cannot be empty.")
        if new_head_sha == self.head_sha:
            raise ValidationError("New head SHA must differ from current SHA.")

        self.head_sha = new_head_sha
        # Existing approvals are retained as history, but approvals tied
        # to an earlier commit no longer count toward merge eligibility.
        self.checks.clear()
        logger.info(
            "Pull request #%s synchronized; status checks must be rerun.",
            self.number,
        )

    def set_check(self, name: str, passed: bool) -> None:
        if self.state != PullRequestState.OPEN:
            raise PullRequestStateError(
                "Checks can only be updated for open pull requests."
            )
        if not name.strip():
            raise ValidationError("Status check name cannot be empty.")
        self.checks[name] = passed


@dataclass(frozen=True)
class BranchProtection:
    required_approvals: int = 2
    required_checks: frozenset[str] = frozenset(
        {"unit-tests", "security-scan"}
    )
    require_resolved_threads: bool = True
    prohibit_direct_pushes: bool = True
    prohibit_force_pushes: bool = True
    prohibit_deletion: bool = True
    require_linear_history: bool = True
    dismiss_stale_approvals: bool = True

    def __post_init__(self) -> None:
        if self.required_approvals < 0:
            raise ValidationError("Required approvals cannot be negative.")
        if any(not check.strip() for check in self.required_checks):
            raise ValidationError("Required check names cannot be blank.")


def current_approvals(pr: PullRequest, policy: BranchProtection) -> set[str]:
    """Count distinct eligible approvals for the current commit."""
    approved: set[str] = set()
    blocked_reviewers: set[str] = set()

    for review in pr.reviews:
        if review.commit_sha != pr.head_sha:
            if policy.dismiss_stale_approvals:
                continue

        if review.state == ReviewState.CHANGES_REQUESTED:
            blocked_reviewers.add(review.reviewer)
            approved.discard(review.reviewer)
        elif review.state == ReviewState.APPROVED:
            if review.reviewer not in blocked_reviewers:
                approved.add(review.reviewer)

    return approved - blocked_reviewers


def evaluate_merge(pr: PullRequest, policy: BranchProtection) -> list[str]:
    """Return all policy violations instead of stopping at the first."""
    failures: list[str] = []

    if pr.state != PullRequestState.OPEN:
        failures.append("Pull request is not open.")

    approvals = current_approvals(pr, policy)
    if len(approvals) < policy.required_approvals:
        failures.append(
            f"Requires {policy.required_approvals} current approvals; "
            f"found {len(approvals)}."
        )

    for check in sorted(policy.required_checks):
        if pr.checks.get(check) is not True:
            failures.append(f"Required check has not passed: {check}.")

    if policy.require_resolved_threads and pr.unresolved_threads:
        failures.append(
            f"{pr.unresolved_threads} review discussion(s) remain unresolved."
        )

    return failures


def merge_pull_request(pr: PullRequest, policy: BranchProtection) -> None:
    failures = evaluate_merge(pr, policy)
    if failures:
        raise ProtectionError("Merge denied: " + " ".join(failures))

    pr.state = PullRequestState.MERGED
    logger.info("Pull request #%s merged.", pr.number)


def direct_push(branch: str, policy: BranchProtection) -> None:
    if not branch.strip():
        raise ValidationError("Branch name cannot be empty.")
    if branch == "main" and policy.prohibit_direct_pushes:
        raise ProtectionError("Direct pushes to main are prohibited.")


def force_push(branch: str, policy: BranchProtection) -> None:
    if not branch.strip():
        raise ValidationError("Branch name cannot be empty.")
    if branch == "main" and policy.prohibit_force_pushes:
        raise ProtectionError("Force pushes to main are prohibited.")


def delete_branch(branch: str, policy: BranchProtection) -> None:
    if not branch.strip():
        raise ValidationError("Branch name cannot be empty.")
    if branch == "main" and policy.prohibit_deletion:
        raise ProtectionError("Protected branch deletion is prohibited.")


def run_with_recovery(
    operation: Callable[[], T],
    default: T,
    expected_errors: tuple[type[Exception], ...] = (GovernanceError,),
) -> T:
    """Handle known domain failures without hiding programming errors."""
    try:
        return operation()
    except expected_errors as exc:
        logger.warning("Operation rejected: %s", exc)
        return default


def load_governance_json(path: Path) -> dict[str, Any]:
    """Read JSON while distinguishing filesystem and data failures."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise PersistenceError(f"Governance file not found: {path}") from exc
    except PermissionError as exc:
        raise PersistenceError("Insufficient permission to read governance file.") from exc
    except json.JSONDecodeError as exc:
        raise PersistenceError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}."
        ) from exc
    except OSError as exc:
        raise PersistenceError("Operating-system failure while reading file.") from exc

    if not isinstance(data, dict):
        raise ValidationError("Governance JSON must contain an object.")
    return data


def save_governance_json(path: Path, data: dict[str, Any]) -> None:
    """Write through a temporary file and replace the destination atomically."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(data, file, indent=2)
            file.write("\n")
            file.flush()

        temporary_path.replace(path)
    except (OSError, TypeError, ValueError) as exc:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.error("Unable to remove temporary file %s", temporary_path)
        raise PersistenceError("Unable to persist governance data.") from exc


def retry_temporary_failure(
    operation: Callable[[], T],
    attempts: int = 3,
) -> T:
    """Retry only explicitly transient failures, not policy violations."""
    if attempts < 1:
        raise ValueError("At least one attempt is required.")

    for attempt in range(attempts):
        try:
            return operation()
        except RetryableOperationError:
            if attempt == attempts - 1:
                raise
            logger.warning("Transient failure; retry %s of %s.", attempt + 1, attempts)

    raise AssertionError("Unreachable retry state.")


def demonstrate_basic_exceptions() -> None:
    print("\n--- Input validation and exception handling ---")

    raw_number = "42"
    try:
        number = int(raw_number)
        print(f"Parsed pull request number: {number}")
    except ValueError as exc:
        print(f"Invalid integer: {exc}")

    try:
        int("PR-42")
    except ValueError:
        print("Rejected malformed pull request number.")

    # finally executes whether the protected operation succeeds or fails.
    resource_open = True
    try:
        raise RuntimeError("Simulated review-service outage")
    except RuntimeError as exc:
        print(f"Handled operational failure: {exc}")
    finally:
        resource_open = False
        print(f"Resource cleanup completed: {not resource_open}")


def build_example_pull_request() -> PullRequest:
    repository = Repository("platform/release-service")
    pr = PullRequest(
        number=84,
        repository=repository,
        title="Validate release manifest before deployment",
        source_branch="feature/manifest-validation",
        target_branch="main",
        author="developer-alex",
        head_sha="a4d9e31",
        unresolved_threads=0,
    )
    pr.publish()
    return pr


def demonstrate_repository_governance() -> None:
    print("\n--- Pull request governance ---")

    policy = BranchProtection()
    pr = build_example_pull_request()

    # A failed merge attempt does not mutate the pull request state.
    try:
        merge_pull_request(pr, policy)
    except ProtectionError as exc:
        print(f"Expected merge rejection: {exc}")

    pr.add_review(
        Review("reviewer-maya", ReviewState.APPROVED, "a4d9e31")
    )
    pr.add_review(
        Review("reviewer-raj", ReviewState.APPROVED, "a4d9e31")
    )
    pr.set_check("unit-tests", True)
    pr.set_check("security-scan", True)

    print("Merge evaluation:", evaluate_merge(pr, policy) or "eligible")
    merge_pull_request(pr, policy)
    print("Final state:", pr.state.value)

    try:
        direct_push("main", policy)
    except ProtectionError as exc:
        print(f"Protected operation rejected: {exc}")

    try:
        force_push("main", policy)
    except ProtectionError as exc:
        print(f"Force push rejected: {exc}")


def demonstrate_stale_approval() -> None:
    print("\n--- Stale approvals after synchronization ---")

    policy = BranchProtection(required_approvals=1)
    pr = build_example_pull_request()
    pr.add_review(Review("reviewer-maya", ReviewState.APPROVED, "a4d9e31"))
    pr.set_check("unit-tests", True)
    pr.set_check("security-scan", True)

    print("Before synchronization:", evaluate_merge(pr, policy) or "eligible")

    pr.synchronize("f10a62b")
    print("After synchronization:", evaluate_merge(pr, policy))

    # A review against the new commit restores approval eligibility.
    pr.add_review(Review("reviewer-maya", ReviewState.APPROVED, "f10a62b"))
    pr.set_check("unit-tests", True)
    pr.set_check("security-scan", True)
    print("After fresh approval:", evaluate_merge(pr, policy) or "eligible")


def demonstrate_review_conflict() -> None:
    print("\n--- Requested changes override approval ---")

    pr = build_example_pull_request()
    pr.add_review(Review("reviewer-maya", ReviewState.APPROVED, "a4d9e31"))
    pr.add_review(
        Review(
            "reviewer-maya",
            ReviewState.CHANGES_REQUESTED,
            "a4d9e31",
            ("Validate the deployment target against the allowlist.",),
        )
    )

    approvals = current_approvals(pr, BranchProtection(required_approvals=1))
    print("Eligible reviewers:", sorted(approvals))
    print("Policy evaluation:", evaluate_merge(pr, BranchProtection(1)))


def demonstrate_defensive_programming() -> None:
    print("\n--- Defensive programming and persistence ---")

    malformed = run_with_recovery(
        lambda: PullRequest(
            number=0,
            repository=Repository("platform/api"),
            title="",
            source_branch="main",
            target_branch="main",
            author="",
            head_sha="",
        ),
        default=None,
    )
    print("Invalid pull request result:", malformed)

    with tempfile.TemporaryDirectory() as directory:
        file_path = Path(directory) / "governance.json"
        save_governance_json(
            file_path,
            {
                "repository": "platform/release-service",
                "protected_branch": "main",
                "required_approvals": 2,
            },
        )
        print("Persisted policy:", load_governance_json(file_path))

        file_path.write_text("{invalid json", encoding="utf-8")
        try:
            load_governance_json(file_path)
        except PersistenceError as exc:
            print(f"Corrupt configuration rejected: {exc}")


def demonstrate_retry_boundary() -> None:
    print("\n--- Bounded retry for transient failures ---")
    calls = 0

    def simulated_remote_operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RetryableOperationError("Temporary service unavailability")
        return "Review service recovered"

    print(retry_temporary_failure(simulated_remote_operation, attempts=3))


def run_self_tests() -> None:
    """Use assertions to check important policy and failure invariants."""
    policy = BranchProtection(required_approvals=1)
    pr = build_example_pull_request()

    assert evaluate_merge(pr, policy)
    pr.add_review(Review("reviewer-maya", ReviewState.APPROVED, pr.head_sha))
    pr.set_check("unit-tests", True)
    pr.set_check("security-scan", True)
    assert evaluate_merge(pr, policy) == []

    merge_pull_request(pr, policy)
    assert pr.state == PullRequestState.MERGED

    try:
        pr.publish()
    except PullRequestStateError:
        pass
    else:
        raise AssertionError("A merged pull request must not be republished.")

    try:
        Repository("invalid-name")
    except ValidationError:
        pass
    else:
        raise AssertionError("Malformed repository names must be rejected.")

    # Repeated approvals by the same person count only once.
    open_pr = build_example_pull_request()
    open_pr.add_review(Review("reviewer-maya", ReviewState.APPROVED, open_pr.head_sha))
    open_pr.add_review(Review("reviewer-maya", ReviewState.APPROVED, open_pr.head_sha))
    assert len(current_approvals(open_pr, BranchProtection(2))) == 1

    print("All self-tests passed.")


def main() -> None:
    demonstrate_basic_exceptions()
    demonstrate_repository_governance()
    demonstrate_stale_approval()
    demonstrate_review_conflict()
    demonstrate_defensive_programming()
    demonstrate_retry_boundary()
    run_self_tests()


if __name__ == "__main__":
    main()
