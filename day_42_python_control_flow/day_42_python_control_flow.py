"""
Python Control Flow: if/elif/else, for loops, while loops, break, continue, pass

This executable script progresses from basic control-flow decisions to a small
repository-quality validation engine. The examples deliberately show how each
control-flow construct changes execution rather than presenting syntax in
isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def section(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def basic_decisions() -> None:
    section("if / elif / else: selecting exactly one decision path")

    changed_files = 8
    tests_passed = True
    review_approved = True

    if changed_files == 0:
        decision = "reject: pull request contains no changed files"
    elif not tests_passed:
        decision = "block: automated tests are failing"
    elif not review_approved:
        decision = "block: required review is missing"
    else:
        decision = "eligible: basic merge conditions are satisfied"

    print(decision)

    # elif is evaluated only when the preceding conditions were false.
    coverage = 94
    if coverage >= 90:
        quality = "excellent"
    elif coverage >= 80:
        quality = "acceptable"
    elif coverage >= 70:
        quality = "needs improvement"
    else:
        quality = "insufficient"

    print(f"Coverage {coverage}% -> {quality}")


def boolean_conditions() -> None:
    section("Compound conditions")

    branch = "feature/payment-validation"
    target = "main"
    draft = False
    conflicts = False

    if branch != target and not draft and not conflicts:
        print("The change can enter formal review.")
    else:
        print("The change is not ready for formal review.")

    # Membership checks are useful when several allowed states exist.
    review_state = "approved"
    if review_state in {"approved", "commented"}:
        print("A reviewer has submitted a review.")
    else:
        print("No qualifying review has been submitted.")


def for_loop_basics() -> None:
    section("for loops: processing a finite collection")

    files = [
        "src/payment.py",
        "src/refund.py",
        "tests/test_payment.py",
        "README.md",
    ]

    for path in files:
        if path.startswith("tests/"):
            category = "test"
        elif path.endswith(".py"):
            category = "application source"
        else:
            category = "documentation"

        print(f"{path}: {category}")

    print("\nRange-driven iteration:")
    for attempt in range(1, 4):
        print(f"validation attempt {attempt}")


def for_loop_with_continue_and_break() -> None:
    section("for + continue + break")

    commits = [
        {"sha": "a91f", "message": "Add validation", "status": "passed"},
        {"sha": "b72c", "message": "Fix test", "status": "passed"},
        {"sha": "c83d", "message": "Temporary debug change", "status": "failed"},
        {"sha": "d14e", "message": "Documentation", "status": "passed"},
    ]

    for commit in commits:
        # continue skips the current iteration without terminating the loop.
        if commit["message"].lower().startswith("temporary"):
            print(f"Skipping temporary commit {commit['sha']}")
            continue

        if commit["status"] == "failed":
            print(f"Blocking commit found: {commit['sha']}")
            # break stops iteration because a blocking failure makes
            # examination of later commits unnecessary for this check.
            break

        print(f"Accepted for inspection: {commit['sha']}")


def while_loop_basics() -> None:
    section("while loops: repeating until a condition changes")

    attempts = 0
    maximum_attempts = 3
    service_available = False

    while attempts < maximum_attempts:
        attempts += 1
        print(f"Checking service, attempt {attempts}")

        # Simulate recovery on the final allowed attempt.
        if attempts == maximum_attempts:
            service_available = True

        if service_available:
            print("Service became available.")
            break

    if not service_available:
        print("Service remained unavailable after all attempts.")


def continue_in_while_loop() -> None:
    section("continue in a while loop")

    queue = ["", "review-pr-42", "", "run-tests", "merge-pr-42"]
    index = 0

    while index < len(queue):
        item = queue[index]
        index += 1

        # Empty queue entries are invalid input, but they should not
        # terminate processing of valid entries that follow them.
        if not item:
            print("Ignoring empty queue entry.")
            continue

        print(f"Processing: {item}")


def pass_as_intentional_no_operation() -> None:
    section("pass: syntactically valid intentional no-operation")

    events = [
        {"type": "review_comment", "important": True},
        {"type": "documentation_update", "important": False},
        {"type": "status_check", "important": True},
    ]

    for event in events:
        if event["type"] == "documentation_update":
            # pass means this branch intentionally does nothing for now.
            # Unlike continue, pass does not affect loop control.
            pass
        else:
            print(f"Actionable event: {event['type']}")


def nested_control_flow() -> None:
    section("Nested control flow")

    pull_requests = [
        {"id": 101, "draft": False, "checks": [True, True], "approvals": 2},
        {"id": 102, "draft": True, "checks": [True, True], "approvals": 3},
        {"id": 103, "draft": False, "checks": [True, False], "approvals": 3},
    ]

    required_approvals = 2

    for pr in pull_requests:
        if pr["draft"]:
            print(f"PR {pr['id']}: draft, skip merge evaluation")
            continue

        checks_ok = True
        for check in pr["checks"]:
            if not check:
                checks_ok = False
                break

        if not checks_ok:
            print(f"PR {pr['id']}: blocked by failed status check")
        elif pr["approvals"] < required_approvals:
            print(f"PR {pr['id']}: blocked by insufficient approvals")
        else:
            print(f"PR {pr['id']}: eligible for merge")


def validation_engine() -> None:
    section("Integrated control-flow validation engine")

    @dataclass
    class PullRequest:
        number: int
        source_branch: str
        target_branch: str
        draft: bool
        changed_files: list[str]
        checks: dict[str, bool]
        approvals: int
        conflicts: bool

    pull_requests = [
        PullRequest(
            201,
            "feature/auth",
            "main",
            False,
            ["src/auth.py", "tests/test_auth.py"],
            {"unit": True, "lint": True},
            2,
            False,
        ),
        PullRequest(
            202,
            "feature/cache",
            "main",
            True,
            ["src/cache.py"],
            {"unit": True, "lint": True},
            3,
            False,
        ),
        PullRequest(
            203,
            "feature/billing",
            "main",
            False,
            ["src/billing.py"],
            {"unit": True, "lint": False},
            3,
            False,
        ),
        PullRequest(
            204,
            "feature/search",
            "main",
            False,
            ["src/search.py"],
            {"unit": True, "lint": True},
            3,
            True,
        ),
    ]

    required_approvals = 2

    for pr in pull_requests:
        reasons: list[str] = []

        if pr.source_branch == pr.target_branch:
            reasons.append("source and target branches are identical")

        if pr.draft:
            reasons.append("pull request is still a draft")

        if not pr.changed_files:
            reasons.append("there are no changed files")

        for check_name, passed in pr.checks.items():
            if not passed:
                reasons.append(f"status check failed: {check_name}")

        if pr.approvals < required_approvals:
            reasons.append(
                f"requires {required_approvals} approvals, has {pr.approvals}"
            )

        if pr.conflicts:
            reasons.append("merge conflicts exist")

        if reasons:
            print(f"PR #{pr.number}: BLOCKED")
            for reason in reasons:
                print(f"  - {reason}")
        else:
            print(f"PR #{pr.number}: MERGE ELIGIBLE")


def edge_case_search() -> None:
    section("Edge cases: break versus continue")

    values = [4, -1, 7, 0, 9]

    print("continue skips invalid negative values:")
    for value in values:
        if value < 0:
            continue
        print(value)

    print("\nbreak terminates when zero is encountered:")
    for value in values:
        if value == 0:
            break
        print(value)


def performance_example() -> None:
    section("Performance-aware control flow")

    records = [
        {"id": 1, "active": True},
        {"id": 2, "active": False},
        {"id": 3, "active": True},
        {"id": 4, "active": True},
    ]

    # A set provides average O(1) membership testing, while the loop
    # provides O(n) traversal of the records.
    active_ids = {record["id"] for record in records if record["active"]}

    for candidate_id in range(1, 7):
        if candidate_id not in active_ids:
            continue
        print(f"Active record: {candidate_id}")


def interactive_status(value: str) -> str:
    """Return a controlled result for an externally supplied status."""
    normalized = value.strip().lower()

    if not normalized:
        raise ValueError("status cannot be empty")

    allowed = {"open", "closed", "draft", "merged"}
    if normalized not in allowed:
        raise ValueError(f"unsupported status: {normalized}")

    if normalized == "open":
        return "work may continue"
    elif normalized == "draft":
        return "work is not ready for final merge"
    elif normalized == "closed":
        return "workflow is stopped"
    else:
        return "change has already been integrated"


def error_handling() -> None:
    section("Validation and exceptions")

    samples = ["open", "draft", "merged", "unknown", ""]

    for sample in samples:
        try:
            print(f"{sample!r}: {interactive_status(sample)}")
        except ValueError as exc:
            print(f"{sample!r}: rejected -> {exc}")


def main() -> None:
    basic_decisions()
    boolean_conditions()
    for_loop_basics()
    for_loop_with_continue_and_break()
    while_loop_basics()
    continue_in_while_loop()
    pass_as_intentional_no_operation()
    nested_control_flow()
    validation_engine()
    edge_case_search()
    performance_example()
    error_handling()


if __name__ == "__main__":
    main()
