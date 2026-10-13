"""
Python Data Structures: Lists, Tuples, Sets, Dictionaries, Nested Structures,
Comprehensions, Validation, Data Processing, and Performance.

Run with:
    python data_structures.py

The examples form a repository inventory and deployment analytics system.
Only the Python standard library is required.
"""

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from itertools import chain
from time import perf_counter
from typing import Any, Iterable, Iterator


class DataValidationError(ValueError):
    """Raised when a data structure violates the inventory's data rules."""


@dataclass
class Repository:
    name: str
    language: str
    stars: int = 0
    topics: set[str] = field(default_factory=set)
    maintainers: tuple[str, ...] = ()
    archived: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DataValidationError("Repository name cannot be empty.")
        if not self.language.strip():
            raise DataValidationError("Language cannot be empty.")
        if self.stars < 0:
            raise DataValidationError("Stars cannot be negative.")
        if any(not maintainer.strip() for maintainer in self.maintainers):
            raise DataValidationError("Maintainer names cannot be empty.")

        self.topics = {topic.strip().lower() for topic in self.topics}
        if "" in self.topics:
            raise DataValidationError("Topics cannot be empty.")

    def to_record(self) -> dict[str, Any]:
        """Convert mutable collections into independent output collections."""
        return {
            "name": self.name,
            "language": self.language,
            "stars": self.stars,
            "topics": sorted(self.topics),
            "maintainers": list(self.maintainers),
            "archived": self.archived,
            "metadata": self.metadata.copy(),
        }


def demonstrate_lists() -> None:
    print("\nLISTS: ordered, mutable sequences")

    repositories = ["risk-engine", "api-service", "data-pipeline"]
    repositories.append("security-monitor")
    repositories.insert(1, "deployment-dashboard")

    print("Current order:", repositories)
    print("First repository:", repositories[0])
    print("Last two repositories:", repositories[-2:])

    repositories[0] = "risk-engine-v2"
    removed = repositories.pop()

    print("Updated order:", repositories)
    print("Removed repository:", removed)

    # A shallow copy duplicates the outer list, not nested objects.
    original = [["python", "sql"], ["javascript"]]
    shallow_copy = original.copy()
    shallow_copy[0].append("postgresql")
    print("Shallow-copy shared mutation:", original)

    # A deep copy also duplicates nested mutable objects.
    from copy import deepcopy

    independent_copy = deepcopy(original)
    independent_copy[0].append("redis")
    print("Original after deep-copy mutation:", original)
    print("Independent copy:", independent_copy)

    # Slicing creates a new list, while assignment through a slice mutates
    # the original list.
    numbers = [10, 20, 30, 40, 50]
    selected = numbers[1:4]
    numbers[1:3] = [21, 31, 41]
    print("Slice result:", selected)
    print("Slice assignment:", numbers)

    # Repeating a nested mutable object can create unexpected shared state.
    incorrect_matrix = [[0] * 3] * 2
    incorrect_matrix[0][0] = 99
    print("Aliased matrix:", incorrect_matrix)

    correct_matrix = [[0] * 3 for _ in range(2)]
    correct_matrix[0][0] = 99
    print("Independent rows:", correct_matrix)


def demonstrate_tuples() -> None:
    print("\nTUPLES: fixed-size records and immutable sequences")

    release = ("risk-engine", "2.4.1", "production")
    name, version, environment = release

    print("Unpacked record:", name, version, environment)
    print("Version:", release[1])
    print("Single-element tuple:", ("python",))
    print("Tuple from an iterable:", tuple(["api", "v1"]))

    # Tuples are immutable, but they can contain mutable objects.
    mixed = ("release-42", ["approved", "tested"])
    mixed[1].append("deployed")
    print("Mutable element inside tuple:", mixed)

    # Hashability determines whether a tuple can be a set member or key.
    deployment_key = ("risk-engine", "production")
    deployment_status = {deployment_key: "healthy"}
    print("Tuple dictionary key:", deployment_status[deployment_key])

    try:
        invalid_key = ("risk-engine", ["production"])
        hash(invalid_key)
    except TypeError as error:
        print("Unhashable nested list:", error)


def demonstrate_sets() -> None:
    print("\nSETS: uniqueness and membership")

    required_checks = {"tests", "lint", "security-scan"}
    completed_checks = {"tests", "security-scan", "coverage"}

    print("Completed required checks:", required_checks & completed_checks)
    print("Missing required checks:", required_checks - completed_checks)
    print("Unexpected checks:", completed_checks - required_checks)
    print("All checks:", required_checks | completed_checks)
    print("Exactly one side:", required_checks ^ completed_checks)

    languages = ["python", "sql", "python", "java", "sql"]
    unique_languages = set(languages)
    print("Unique languages:", sorted(unique_languages))

    # Sets do not guarantee display order. Sort when deterministic output
    # matters for logs, tests, or serialized reports.
    deployment_regions = {"ap-south-1", "eu-west-1", "us-east-1"}
    print("Sorted regions:", sorted(deployment_regions))

    approved_reviewers = {"anika", "rahul", "meera"}
    requested_reviewers = {"rahul", "meera"}

    if requested_reviewers <= approved_reviewers:
        print("All requested reviewers are eligible.")

    print("Meera eligible:", "meera" in approved_reviewers)


def demonstrate_dictionaries() -> None:
    print("\nDICTIONARIES: key-value mapping")

    repository = {
        "name": "market-risk",
        "language": "python",
        "stars": 240,
    }

    repository["stars"] += 10
    repository["visibility"] = "private"

    print("Repository:", repository)
    print("Optional owner:", repository.get("owner", "unassigned"))

    language = repository.pop("language")
    print("Removed language:", language)

    # setdefault initializes a value only if the key does not exist.
    repository.setdefault("labels", []).append("risk")
    repository.setdefault("labels", []).append("analytics")
    print("Labels:", repository["labels"])

    # Dictionary unpacking creates a new mapping. Nested values may still
    # be shared unless explicitly copied.
    defaults = {"timeout": 30, "retries": 3}
    overrides = {"timeout": 60, "region": "ap-south-1"}
    configuration = {**defaults, **overrides}
    print("Merged configuration:", configuration)

    # Preserve the distinction between a missing key and a present key
    # whose value is None.
    settings = {"proxy": None}
    print("Proxy present:", "proxy" in settings)
    print("Timeout present:", "timeout" in settings)

    for key, value in repository.items():
        print(f"{key} -> {value}")


def demonstrate_nested_structures() -> None:
    print("\nNESTED STRUCTURES: operational deployment records")

    deployment = {
        "deployment_id": "DEP-2048",
        "service": {
            "name": "portfolio-api",
            "language": "python",
            "version": "3.2.0",
        },
        "checks": [
            {"name": "unit-tests", "passed": True, "duration_ms": 480},
            {"name": "security-scan", "passed": True, "duration_ms": 920},
            {"name": "integration-tests", "passed": False, "duration_ms": 1600},
        ],
        "regions": {"ap-south-1", "eu-west-1"},
    }

    failed_checks = [
        check["name"]
        for check in deployment["checks"]
        if not check["passed"]
    ]

    total_duration = sum(
        check["duration_ms"] for check in deployment["checks"]
    )

    print("Service:", deployment["service"]["name"])
    print("Failed checks:", failed_checks)
    print("Total check duration:", total_duration, "ms")
    print("Regions:", sorted(deployment["regions"]))

    # Validate nested structures before relying on their contents.
    if not isinstance(deployment.get("checks"), list):
        raise DataValidationError("'checks' must be a list.")

    for check in deployment["checks"]:
        if not isinstance(check, dict):
            raise DataValidationError("Every check must be a dictionary.")
        if not isinstance(check.get("passed"), bool):
            raise DataValidationError("'passed' must be a boolean.")
        if not isinstance(check.get("duration_ms"), int):
            raise DataValidationError("'duration_ms' must be an integer.")
        if check["duration_ms"] < 0:
            raise DataValidationError("Duration cannot be negative.")


def demonstrate_comprehensions() -> None:
    print("\nCOMPREHENSIONS: transform and filter collections")

    repositories = [
        {"name": "risk-engine", "language": "python", "stars": 240},
        {"name": "dashboard", "language": "javascript", "stars": 180},
        {"name": "queue-worker", "language": "python", "stars": 95},
        {"name": "database-tools", "language": "sql", "stars": 75},
    ]

    names = [repo["name"] for repo in repositories]
    popular = {
        repo["name"]: repo["stars"]
        for repo in repositories
        if repo["stars"] >= 100
    }
    languages = {repo["language"] for repo in repositories}
    language_counts = {
        language: sum(
            repo["language"] == language for repo in repositories
        )
        for language in languages
    }
    star_bands = [
        "high" if repo["stars"] >= 200 else "standard"
        for repo in repositories
    ]

    print("Names:", names)
    print("Popular repositories:", popular)
    print("Language counts:", language_counts)
    print("Star bands:", star_bands)

    # Nested comprehensions flatten two levels of nested data.
    check_groups = [["tests", "lint"], ["security", "coverage"]]
    flattened = [check for group in check_groups for check in group]
    print("Flattened checks:", flattened)

    # Generator expressions calculate values lazily and avoid creating
    # an intermediate list.
    total_stars = sum(repo["stars"] for repo in repositories)
    print("Total stars:", total_stars)


def demonstrate_iteration_tools() -> None:
    print("\nITERATION TOOLS: counting, grouping, and queues")

    events = [
        ("risk-engine", "success"),
        ("api-service", "failure"),
        ("risk-engine", "success"),
        ("api-service", "success"),
        ("risk-engine", "failure"),
    ]

    status_counts = Counter(status for _, status in events)
    events_by_repository: dict[str, list[str]] = defaultdict(list)

    for name, status in events:
        events_by_repository[name].append(status)

    print("Status counts:", dict(status_counts))
    print("Events by repository:", dict(events_by_repository))

    release_queue = deque(["release-101", "release-102"])
    release_queue.append("release-103")
    first_release = release_queue.popleft()

    print("Next release:", first_release)
    print("Remaining queue:", list(release_queue))

    print("Combined checks:", list(chain(["lint"], ["tests", "security"])))

    for index, (name, status) in enumerate(events, start=1):
        print(f"Event {index}: {name} = {status}")


def build_repository_catalog() -> list[Repository]:
    """Create and validate realistic repository records."""
    return [
        Repository(
            name="market-prism",
            language="python",
            stars=320,
            topics={"finance", "analytics", "api"},
            maintainers=("Anika", "Rahul"),
            metadata={"tier": "production", "tests_passing": True},
        ),
        Repository(
            name="portfolio-ui",
            language="javascript",
            stars=210,
            topics={"dashboard", "analytics"},
            maintainers=("Meera",),
            metadata={"tier": "production", "tests_passing": True},
        ),
        Repository(
            name="security-audit",
            language="python",
            stars=145,
            topics={"security", "automation"},
            maintainers=("Rahul", "Dev"),
            metadata={"tier": "internal", "tests_passing": False},
        ),
        Repository(
            name="data-warehouse",
            language="sql",
            stars=88,
            topics={"analytics", "data"},
            maintainers=("Anika",),
            metadata={"tier": "internal", "tests_passing": True},
        ),
        Repository(
            name="legacy-reports",
            language="java",
            stars=34,
            topics={"reporting", "legacy"},
            maintainers=("Dev",),
            archived=True,
            metadata={"tier": "archived", "tests_passing": True},
        ),
    ]


def analyze_repository_catalog(
    repositories: Iterable[Repository],
) -> dict[str, Any]:
    """Derive aggregate views without changing the source records."""
    records = list(repositories)

    if len({repo.name for repo in records}) != len(records):
        raise DataValidationError("Repository names must be unique.")

    active_repositories = [repo for repo in records if not repo.archived]
    language_counts = Counter(
        repo.language for repo in active_repositories
    )

    topic_index: dict[str, list[str]] = defaultdict(list)
    maintainer_index: dict[str, set[str]] = defaultdict(set)

    for repo in active_repositories:
        for topic in repo.topics:
            topic_index[topic].append(repo.name)

        for maintainer in repo.maintainers:
            maintainer_index[maintainer].add(repo.name)

    failing_repositories = [
        repo.name
        for repo in active_repositories
        if repo.metadata.get("tests_passing") is not True
    ]

    return {
        "total": len(records),
        "active": len(active_repositories),
        "archived": len(records) - len(active_repositories),
        "language_counts": dict(language_counts),
        "topic_index": {
            topic: sorted(names)
            for topic, names in topic_index.items()
        },
        "maintainer_index": {
            maintainer: sorted(names)
            for maintainer, names in maintainer_index.items()
        },
        "failing_repositories": failing_repositories,
        "high_star_repositories": [
            repo.name
            for repo in active_repositories
            if repo.stars >= 200
        ],
    }


def demonstrate_mutable_defaults_and_copying() -> None:
    print("\nMUTABILITY: safe defaults and explicit copies")

    def add_label(
        labels: list[str] | None = None,
        label: str = "reviewed",
    ) -> list[str]:
        # Create a fresh list per call rather than sharing a mutable default.
        if labels is None:
            labels = []
        labels.append(label)
        return labels

    print("First call:", add_label())
    print("Second call:", add_label())

    source = {"pipeline": {"steps": ["lint", "test"]}}
    copied = source.copy()
    copied["pipeline"]["steps"].append("deploy")
    print("Shallow copy shares nested state:", source)

    from copy import deepcopy

    independent = deepcopy(source)
    independent["pipeline"]["steps"].append("monitor")
    print("Source remains unchanged by deep copy:", source)
    print("Independent nested data:", independent)


def benchmark_membership() -> None:
    """Compare list and set membership without asserting machine-specific times."""
    print("\nPERFORMANCE: list versus set membership")

    values = list(range(100_000))
    lookup_set = set(values)
    target = 99_999
    repetitions = 2_000

    start = perf_counter()
    for _ in range(repetitions):
        target in values
    list_seconds = perf_counter() - start

    start = perf_counter()
    for _ in range(repetitions):
        target in lookup_set
    set_seconds = perf_counter() - start

    print(f"List lookup total: {list_seconds:.6f} seconds")
    print(f"Set lookup total:  {set_seconds:.6f} seconds")
    print("List membership is O(n) in the worst case.")
    print("Set membership is O(1) on average, with hashing overhead.")


def demonstrate_error_handling() -> None:
    print("\nVALIDATION: reject invalid records")

    invalid_examples = [
        {"name": "", "language": "python", "stars": 10},
        {"name": "api", "language": "", "stars": 10},
        {"name": "api", "language": "python", "stars": -1},
    ]

    for values in invalid_examples:
        try:
            Repository(**values)
        except DataValidationError as error:
            print("Rejected:", error)

    repository = {"name": "api", "metadata": {"owner": "Anika"}}

    try:
        print(repository["language"])
    except KeyError:
        print("Missing required key: language")

    # Never assume external JSON or API responses have the expected shape.
    external_record: Any = {
        "name": "worker",
        "stars": "unknown",
    }

    if (
        not isinstance(external_record, dict)
        or not isinstance(external_record.get("name"), str)
        or not isinstance(external_record.get("stars"), int)
        or isinstance(external_record.get("stars"), bool)
    ):
        print("External record rejected by schema validation.")


def demonstrate_serialization() -> None:
    print("\nSERIALIZATION: JSON-compatible nested structures")

    import json

    record = {
        "repository": "market-prism",
        "labels": ["finance", "analytics"],
        "maintainers": ("Anika", "Rahul"),
        "metrics": {"stars": 320, "tests_passing": True},
    }

    encoded = json.dumps(record, sort_keys=True)
    decoded = json.loads(encoded)

    print("Encoded JSON:", encoded)
    print("Decoded labels:", decoded["labels"])
    print("Tuple becomes a JSON array and decodes as a list.")

    # Sets are not JSON serializable by default; convert them deliberately.
    tags = {"security", "automation"}
    encoded_tags = json.dumps(sorted(tags))
    print("Serialized set:", encoded_tags)


def main() -> None:
    print("PYTHON DATA STRUCTURES IN A REPOSITORY MANAGEMENT CONTEXT")

    demonstrate_lists()
    demonstrate_tuples()
    demonstrate_sets()
    demonstrate_dictionaries()
    demonstrate_nested_structures()
    demonstrate_comprehensions()
    demonstrate_iteration_tools()
    demonstrate_mutable_defaults_and_copying()
    demonstrate_error_handling()
    demonstrate_serialization()

    catalog = build_repository_catalog()
    report = analyze_repository_catalog(catalog)

    print("\nREPOSITORY CATALOG REPORT")
    print("Total:", report["total"])
    print("Active:", report["active"])
    print("Archived:", report["archived"])
    print("Languages:", report["language_counts"])
    print("Topic index:", report["topic_index"])
    print("Maintainer index:", report["maintainer_index"])
    print("Failing tests:", report["failing_repositories"])
    print("High-star repositories:", report["high_star_repositories"])

    print("\nINDEPENDENT RECORD EXPORT")
    for repository in catalog:
        print(repository.to_record())

    benchmark_membership()

    print("\nAll demonstrations completed.")


if __name__ == "__main__":
    main()
