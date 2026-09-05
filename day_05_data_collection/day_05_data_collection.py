"""
DATA COLLECTION: A COMPLETE BEGINNER-TO-ADVANCED STUDY SCRIPT

This standalone script teaches data collection systematically, from basic
definitions to advanced collection architectures, sampling, bias, APIs,
databases, web data, logs, sensors, validation, quality control, privacy,
security, observability, and production considerations.

The examples use only Python's standard library so that the file can be run
without installing external packages.

Run:
    python data_collection.py
"""

from __future__ import annotations

import csv
import io
import json
import math
import random
import re
import sqlite3
import statistics
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence


# ============================================================================
# 1. FUNDAMENTALS
# ============================================================================

def explain_data_collection() -> None:
    """
    Data collection is the systematic process of obtaining observations,
    measurements, records, responses, or other information for a defined
    purpose.

    Important distinction:
        Data collection is not the same as data analysis.

    Collection answers:
        "How do we obtain the observations?"

    Analysis answers:
        "What do the observations mean?"
    """
    print("\n=== FUNDAMENTALS ===")
    print("Data collection obtains observations for a defined purpose.")
    print("Primary data is collected directly for the current study.")
    print("Secondary data was previously collected for another or broader purpose.")
    print("A dataset is a structured collection of observations and variables.")


# ============================================================================
# 2. TERMINOLOGY
# ============================================================================

@dataclass
class Observation:
    """
    One observation is one recorded unit of information.

    Examples:
        - one customer's survey response
        - one transaction
        - one temperature reading
        - one API response
        - one web event
    """
    observation_id: str
    values: dict[str, Any]


@dataclass
class Dataset:
    """
    A simple representation of a dataset.

    Each row represents an observation.
    Each key in values represents a variable/attribute.
    """
    name: str
    observations: list[Observation] = field(default_factory=list)

    @property
    def columns(self) -> list[str]:
        columns: set[str] = set()
        for observation in self.observations:
            columns.update(observation.values.keys())
        return sorted(columns)

    def row_count(self) -> int:
        return len(self.observations)


def terminology_demo() -> None:
    dataset = Dataset(
        name="customer_orders",
        observations=[
            Observation("O1", {"customer_id": 101, "amount": 500, "city": "Lucknow"}),
            Observation("O2", {"customer_id": 102, "amount": 800, "city": "Delhi"}),
        ],
    )

    print("\n=== TERMINOLOGY ===")
    print("Dataset:", dataset.name)
    print("Observations:", dataset.row_count())
    print("Variables:", dataset.columns)

    terms = {
        "population": "Entire group about which conclusions are intended.",
        "sample": "Subset selected from the population.",
        "variable": "Characteristic recorded for an observation.",
        "record": "Stored representation of an observation.",
        "sampling frame": "Operational list or mechanism from which a sample is drawn.",
        "metadata": "Data describing other data.",
        "measurement": "Recorded value representing a characteristic.",
        "response rate": "Proportion of eligible sampled units that provide usable responses.",
    }

    for term, definition in terms.items():
        print(f"{term}: {definition}")


# ============================================================================
# 3. PRIMARY VS SECONDARY DATA
# ============================================================================

@dataclass
class DataSource:
    name: str
    source_type: str
    collected_directly: bool
    typical_strength: str
    typical_risk: str


def compare_primary_secondary() -> None:
    sources = [
        DataSource(
            "Customer survey",
            "Primary",
            True,
            "Purpose-specific variables can be designed.",
            "Nonresponse and response bias.",
        ),
        DataSource(
            "Government statistics",
            "Secondary",
            False,
            "Broad population coverage may already exist.",
            "Definitions may differ from the current study.",
        ),
        DataSource(
            "Company transaction database",
            "Secondary/internal",
            False,
            "Large volume of operational records.",
            "Records reflect business processes, not necessarily the target population.",
        ),
    ]

    print("\n=== PRIMARY VS SECONDARY DATA ===")
    for source in sources:
        print(
            f"{source.name}: {source.source_type}; "
            f"direct={source.collected_directly}; "
            f"strength={source.typical_strength}; "
            f"risk={source.typical_risk}"
        )

    print(
        "\nPrimary data is appropriate when the required information does not "
        "already exist or existing sources do not match the research question."
    )
    print(
        "Secondary data can reduce collection cost and time, but its definitions, "
        "coverage, quality, timing, and original purpose must be evaluated."
    )


# ============================================================================
# 4. DATA COLLECTION METHODS
# ============================================================================

class CollectionMethod(Enum):
    SURVEY = "survey"
    INTERVIEW = "interview"
    OBSERVATION = "observation"
    DATABASE = "database"
    API = "api"
    WEB = "web"
    LOG = "log"
    SENSOR = "sensor"
    TRANSACTION = "transaction"
    EXPERIMENT = "experiment"


def describe_collection_methods() -> None:
    characteristics = {
        CollectionMethod.SURVEY: (
            "Structured questions answered by sampled respondents."
        ),
        CollectionMethod.INTERVIEW: (
            "Direct questioning, often allowing deeper qualitative information."
        ),
        CollectionMethod.OBSERVATION: (
            "Records behavior or events without necessarily asking participants."
        ),
        CollectionMethod.DATABASE: (
            "Retrieves structured records stored by an operational or analytical system."
        ),
        CollectionMethod.API: (
            "Programmatically retrieves data through a defined application interface."
        ),
        CollectionMethod.WEB: (
            "Collects publicly accessible web content subject to legal, technical, "
            "and ethical constraints."
        ),
        CollectionMethod.LOG: (
            "Collects system-generated event records."
        ),
        CollectionMethod.SENSOR: (
            "Captures physical measurements such as temperature or acceleration."
        ),
        CollectionMethod.TRANSACTION: (
            "Records business events such as purchases, payments, or transfers."
        ),
        CollectionMethod.EXPERIMENT: (
            "Collects observations under controlled or deliberately varied conditions."
        ),
    }

    print("\n=== DATA COLLECTION METHODS ===")
    for method, description in characteristics.items():
        print(f"{method.value.upper():12} -> {description}")


# ============================================================================
# 5. SURVEY DESIGN
# ============================================================================

@dataclass
class SurveyQuestion:
    question_id: str
    text: str
    question_type: str
    required: bool = False
    options: tuple[str, ...] = ()


def validate_survey_question(question: SurveyQuestion) -> list[str]:
    errors: list[str] = []

    if not question.question_id.strip():
        errors.append("Question ID cannot be empty.")

    if not question.text.strip():
        errors.append("Question text cannot be empty.")

    valid_types = {
        "single_choice",
        "multiple_choice",
        "numeric",
        "text",
        "date",
        "likert",
    }

    if question.question_type not in valid_types:
        errors.append("Unsupported question type.")

    if question.question_type in {"single_choice", "multiple_choice", "likert"}:
        if len(question.options) < 2:
            errors.append("Choice questions require at least two options.")

    return errors


def survey_design_demo() -> None:
    questions = [
        SurveyQuestion(
            "Q1",
            "How satisfied are you with the service?",
            "likert",
            required=True,
            options=("Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very satisfied"),
        ),
        SurveyQuestion(
            "Q2",
            "How many purchases did you make last month?",
            "numeric",
        ),
        SurveyQuestion(
            "Q3",
            "What would you improve?",
            "text",
        ),
    ]

    print("\n=== SURVEY DESIGN ===")
    for question in questions:
        errors = validate_survey_question(question)
        print(question.question_id, "valid" if not errors else errors)

    print("\nImportant survey design principles:")
    print("- Avoid leading questions.")
    print("- Avoid double-barreled questions.")
    print("- Make response categories mutually appropriate.")
    print("- Include a valid 'not applicable' state when needed.")
    print("- Keep recall periods explicit.")
    print("- Pilot-test the instrument.")
    print("- Define eligibility before sampling.")


# ============================================================================
# 6. QUESTION BIAS EXAMPLES
# ============================================================================

def survey_bias_demo() -> None:
    examples = {
        "leading": (
            "How excellent was our service?",
            "Presupposes that the service was excellent.",
        ),
        "double_barreled": (
            "How satisfied are you with our price and customer support?",
            "Combines two potentially independent dimensions.",
        ),
        "ambiguous": (
            "Do you regularly use the product?",
            "'Regularly' has no defined frequency.",
        ),
        "loaded": (
            "Why do you support this beneficial policy?",
            "Frames the subject in a favorable way.",
        ),
        "better": (
            "How satisfied are you with the product price?",
            "Measures one clearly defined construct.",
        ),
    }

    print("\n=== SURVEY QUESTION QUALITY ===")
    for category, (question, issue) in examples.items():
        print(f"{category}: {question}")
        print(f"  Assessment: {issue}")


# ============================================================================
# 7. SURVEY RESPONSE VALIDATION
# ============================================================================

def validate_survey_response(
    response: Mapping[str, Any],
    questions: Sequence[SurveyQuestion],
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    question_map = {question.question_id: question for question in questions}

    for question in questions:
        value = response.get(question.question_id)

        if question.required and (value is None or value == ""):
            errors.append(f"{question.question_id} is required.")
            continue

        if value is None:
            continue

        if question.question_type == "numeric":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{question.question_id} must be numeric.")

        elif question.question_type == "single_choice":
            if value not in question.options:
                errors.append(f"{question.question_id} contains an invalid choice.")

        elif question.question_type == "multiple_choice":
            if not isinstance(value, list):
                errors.append(f"{question.question_id} must be a list.")
            elif any(item not in question.options for item in value):
                errors.append(f"{question.question_id} contains an invalid choice.")

        elif question.question_type == "likert":
            if value not in question.options:
                errors.append(f"{question.question_id} contains an invalid Likert value.")

    unknown_fields = set(response) - set(question_map)
    if unknown_fields:
        errors.append(f"Unknown response fields: {sorted(unknown_fields)}")

    return not errors, errors


def survey_validation_demo() -> None:
    questions = [
        SurveyQuestion(
            "Q1",
            "Satisfaction",
            "likert",
            required=True,
            options=("Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very satisfied"),
        ),
        SurveyQuestion("Q2", "Purchases", "numeric", required=True),
    ]

    good_response = {"Q1": "Satisfied", "Q2": 3}
    bad_response = {"Q1": "Amazing", "Q2": "three"}

    print("\n=== SURVEY RESPONSE VALIDATION ===")
    print("Good:", validate_survey_response(good_response, questions))
    print("Bad:", validate_survey_response(bad_response, questions))


# ============================================================================
# 8. SAMPLING BASICS
# ============================================================================

def simple_random_sample(
    population: Sequence[Any],
    sample_size: int,
    seed: int | None = None,
) -> list[Any]:
    """
    Simple random sampling gives each population unit an equal probability
    of selection when sampling is performed correctly without replacement.
    """
    if sample_size < 0:
        raise ValueError("sample_size cannot be negative.")

    if sample_size > len(population):
        raise ValueError("sample_size cannot exceed population size.")

    generator = random.Random(seed)
    return generator.sample(list(population), sample_size)


def systematic_sample(
    population: Sequence[Any],
    sample_size: int,
    seed: int | None = None,
) -> list[Any]:
    """
    Systematic sampling selects observations at a regular interval.

    It requires attention to periodicity. If the ordering of the population
    contains a repeating pattern aligned with the interval, bias can occur.
    """
    if sample_size <= 0:
        return []

    if sample_size > len(population):
        raise ValueError("sample_size cannot exceed population size.")

    interval = len(population) / sample_size
    generator = random.Random(seed)
    start = generator.uniform(0, interval)

    selected = []
    for i in range(sample_size):
        index = int(start + i * interval)
        if index >= len(population):
            index = len(population) - 1
        selected.append(population[index])

    return selected


def stratified_sample(
    population: Sequence[Mapping[str, Any]],
    stratum_key: str,
    sample_size: int,
    seed: int | None = None,
) -> list[Mapping[str, Any]]:
    """
    Stratified sampling divides the population into strata and samples
    separately from each stratum.

    Here the allocation is approximately proportional to stratum size.
    """
    if sample_size <= 0:
        return []

    if sample_size > len(population):
        raise ValueError("sample_size cannot exceed population size.")

    strata: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for row in population:
        if stratum_key not in row:
            raise KeyError(f"Missing stratum field: {stratum_key}")
        strata[row[stratum_key]].append(row)

    generator = random.Random(seed)

    allocations: dict[Any, int] = {}
    total = len(population)

    for key, rows in strata.items():
        allocations[key] = int(sample_size * len(rows) / total)

    remaining = sample_size - sum(allocations.values())

    ranked_strata = sorted(
        strata,
        key=lambda key: (
            sample_size * len(strata[key]) / total
            - allocations[key]
        ),
        reverse=True,
    )

    for key in ranked_strata[:remaining]:
        allocations[key] += 1

    result: list[Mapping[str, Any]] = []
    for key, rows in strata.items():
        count = min(allocations[key], len(rows))
        result.extend(generator.sample(rows, count))

    return result


def cluster_sample(
    population: Sequence[Mapping[str, Any]],
    cluster_key: str,
    number_of_clusters: int,
    seed: int | None = None,
) -> list[Mapping[str, Any]]:
    """
    Cluster sampling randomly selects groups rather than individual units.

    It can reduce operational cost when geographically or organizationally
    clustered collection is easier, but observations within clusters can be
    correlated, increasing sampling error.
    """
    if number_of_clusters <= 0:
        return []

    clusters: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for row in population:
        clusters[row[cluster_key]].append(row)

    if number_of_clusters > len(clusters):
        raise ValueError("More clusters requested than available.")

    generator = random.Random(seed)
    selected_keys = generator.sample(list(clusters), number_of_clusters)

    result = []
    for key in selected_keys:
        result.extend(clusters[key])

    return result


def sampling_demo() -> None:
    population = list(range(1, 101))

    print("\n=== SAMPLING METHODS ===")
    print("Population size:", len(population))
    print("Simple random:", simple_random_sample(population, 10, seed=42))
    print("Systematic:", systematic_sample(population, 10, seed=42))

    customer_population = [
        {"id": i, "segment": "A" if i <= 60 else "B"}
        for i in range(1, 101)
    ]

    stratified = stratified_sample(
        customer_population,
        "segment",
        20,
        seed=42,
    )

    print(
        "Stratified segment counts:",
        Counter(row["segment"] for row in stratified),
    )

    clustered_population = [
        {"id": i, "region": f"R{((i - 1) // 10) + 1}"}
        for i in range(1, 101)
    ]

    cluster_result = cluster_sample(
        clustered_population,
        "region",
        2,
        seed=42,
    )

    print(
        "Cluster sample size:",
        len(cluster_result),
        "clusters:",
        sorted(set(row["region"] for row in cluster_result)),
    )


# ============================================================================
# 9. SAMPLING BIAS
# ============================================================================

def sampling_bias_simulation() -> None:
    """
    Demonstrates coverage bias.

    Suppose the target population has equal numbers of online and offline
    customers, but only online customers can enter the sampling frame.
    """
    population = [
        {"id": i, "channel": "online" if i < 500 else "offline"}
        for i in range(1000)
    ]

    sampling_frame = [
        row for row in population
        if row["channel"] == "online"
    ]

    sample = simple_random_sample(sampling_frame, 100, seed=7)

    observed = Counter(row["channel"] for row in sample)

    print("\n=== SAMPLING BIAS ===")
    print("True population:", Counter(row["channel"] for row in population))
    print("Sampling frame:", Counter(row["channel"] for row in sampling_frame))
    print("Sample:", observed)
    print(
        "The sample is random within the frame, but the frame excludes an entire "
        "part of the target population. Random selection cannot fix missing coverage."
    )


# ============================================================================
# 10. SAMPLE SIZE CONCEPTS
# ============================================================================

def approximate_proportion_sample_size(
    confidence_z: float,
    expected_proportion: float,
    margin_of_error: float,
) -> int:
    """
    Approximate sample size for a population proportion:

        n = z^2 * p * (1-p) / e^2

    This is a planning formula, not a universal answer. Real studies may need
    finite-population correction, design effects, stratification adjustments,
    anticipated nonresponse, and domain-specific assumptions.
    """
    if not 0 < expected_proportion < 1:
        raise ValueError("expected_proportion must be between 0 and 1.")

    if margin_of_error <= 0:
        raise ValueError("margin_of_error must be positive.")

    n = (
        confidence_z ** 2
        * expected_proportion
        * (1 - expected_proportion)
        / margin_of_error ** 2
    )

    return math.ceil(n)


def finite_population_correction(
    initial_sample_size: int,
    population_size: int,
) -> int:
    """
    Approximate finite-population correction:

        n_adj = n / (1 + (n - 1) / N)
    """
    if population_size <= 0:
        raise ValueError("population_size must be positive.")

    if initial_sample_size <= 0:
        return 0

    adjusted = initial_sample_size / (
        1 + (initial_sample_size - 1) / population_size
    )

    return math.ceil(adjusted)


def sample_size_demo() -> None:
    initial = approximate_proportion_sample_size(
        confidence_z=1.96,
        expected_proportion=0.5,
        margin_of_error=0.05,
    )

    adjusted = finite_population_correction(initial, 10000)

    print("\n=== SAMPLE SIZE ===")
    print("Initial approximate sample size:", initial)
    print("Finite-population adjusted size:", adjusted)


# ============================================================================
# 11. DATABASE COLLECTION
# ============================================================================

def database_collection_demo() -> None:
    """
    SQLite demonstrates structured data collection from a database.

    Production systems require:
        - parameterized queries
        - transactions
        - indexes
        - access control
        - backups
        - schema governance
        - connection management
        - auditing
    """
    print("\n=== DATABASE COLLECTION ===")

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                transaction_time TEXT NOT NULL
            )
            """
        )

        records = [
            (1, 101, 500.0, "2026-09-05T09:00:00Z"),
            (2, 102, 1250.0, "2026-09-05T09:05:00Z"),
            (3, 101, 250.0, "2026-09-05T09:10:00Z"),
        ]

        connection.executemany(
            """
            INSERT INTO transactions
            (transaction_id, customer_id, amount, transaction_time)
            VALUES (?, ?, ?, ?)
            """,
            records,
        )
        connection.commit()

        minimum_amount = 300.0

        rows = connection.execute(
            """
            SELECT transaction_id, customer_id, amount
            FROM transactions
            WHERE amount >= ?
            ORDER BY amount DESC
            """,
            (minimum_amount,),
        ).fetchall()

        for row in rows:
            print(row)

        print(
            "Parameterized queries prevent user-controlled values from being "
            "interpreted as SQL syntax."
        )

    finally:
        connection.close()


# ============================================================================
# 12. API DATA COLLECTION
# ============================================================================

def build_api_url(
    base_url: str,
    parameters: Mapping[str, str | int | float],
) -> str:
    """
    Correctly encodes query parameters instead of manually concatenating them.
    """
    query_string = urllib.parse.urlencode(parameters)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query_string}"


def fetch_json_api(
    url: str,
    timeout_seconds: float = 10.0,
) -> Any:
    """
    Generic JSON retrieval example.

    Production API collection should also address:
        - authentication
        - rate limits
        - retries
        - exponential backoff
        - pagination
        - schema changes
        - HTTP status codes
        - idempotency
        - caching
        - observability
        - secret management
    """
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "EducationalDataCollector/1.0",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get("Content-Type", "")
        body = response.read().decode("utf-8")

        if "application/json" not in content_type:
            raise ValueError("Expected a JSON response.")

        return json.loads(body)


def api_pagination_demo() -> list[dict[str, Any]]:
    """
    Demonstrates the logic of paginated API collection without requiring a
    live external API.
    """
    fake_pages = {
        1: {"items": [{"id": 1}, {"id": 2}], "next_page": 2},
        2: {"items": [{"id": 3}, {"id": 4}], "next_page": 3},
        3: {"items": [{"id": 5}], "next_page": None},
    }

    collected: list[dict[str, Any]] = []
    page = 1

    while page is not None:
        payload = fake_pages[page]
        collected.extend(payload["items"])
        page = payload["next_page"]

    return collected


def api_collection_demo() -> None:
    print("\n=== API COLLECTION ===")

    url = build_api_url(
        "https://example.com/api/customers",
        {"page": 2, "limit": 50, "country": "India"},
    )

    print("Constructed URL:", url)
    print("Paginated records:", api_pagination_demo())


# ============================================================================
# 13. API RETRIES AND EXPONENTIAL BACKOFF
# ============================================================================

class TemporaryCollectionError(Exception):
    """Represents a transient collection failure."""


def collect_with_retry(
    operation: Callable[[], Any],
    max_attempts: int = 4,
    base_delay: float = 0.01,
) -> Any:
    """
    Retry only when failures are plausibly transient.

    Blindly retrying authentication failures, invalid requests, or permanent
    schema errors wastes resources and may amplify load.
    """
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive.")

    for attempt in range(max_attempts):
        try:
            return operation()
        except TemporaryCollectionError:
            if attempt == max_attempts - 1:
                raise

            delay = base_delay * (2 ** attempt)
            time.sleep(delay)

    raise RuntimeError("Unreachable code")


def retry_demo() -> None:
    attempts = {"count": 0}

    def unstable_operation() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TemporaryCollectionError("Temporary failure")
        return "collection succeeded"

    print("\n=== RETRIES ===")
    print(collect_with_retry(unstable_operation))


# ============================================================================
# 14. WEB DATA COLLECTION
# ============================================================================

def extract_text_from_html(html: str) -> str:
    """
    Minimal educational HTML text extraction.

    This intentionally does not attempt to be a complete HTML parser.
    For production scraping, use a standards-compliant parser and respect
    site policies, access controls, terms, copyright, and applicable law.
    """
    html_without_scripts = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    html_without_styles = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        html_without_scripts,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(r"<[^>]+>", " ", html_without_styles)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def web_collection_demo() -> None:
    html = """
    <html>
        <head><title>Example</title></head>
        <body>
            <h1>Product Data</h1>
            <p>Price: 999</p>
            <script>secret_internal_code = "do-not-collect";</script>
        </body>
    </html>
    """

    print("\n=== WEB DATA COLLECTION ===")
    print(extract_text_from_html(html))
    print(
        "Web collection requires attention to robots directives, terms of use, "
        "privacy, rate limits, copyright, authentication barriers, and server load."
    )


# ============================================================================
# 15. LOG DATA COLLECTION
# ============================================================================

@dataclass
class LogEvent:
    timestamp: str
    level: str
    service: str
    event: str
    metadata: dict[str, Any]


def create_log_event(
    level: str,
    service: str,
    event: str,
    metadata: Mapping[str, Any],
) -> LogEvent:
    """
    Structured logs are preferable to arbitrary text when downstream systems
    need to query and aggregate events.
    """
    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    if level not in allowed_levels:
        raise ValueError("Invalid log level.")

    return LogEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        level=level,
        service=service,
        event=event,
        metadata=dict(metadata),
    )


def log_collection_demo() -> None:
    events = [
        create_log_event(
            "INFO",
            "payment-service",
            "payment_received",
            {"transaction_id": "T100", "amount": 500},
        ),
        create_log_event(
            "ERROR",
            "payment-service",
            "payment_failed",
            {"transaction_id": "T101", "reason": "timeout"},
        ),
    ]

    print("\n=== LOG DATA COLLECTION ===")
    for event in events:
        print(json.dumps({
            "timestamp": event.timestamp,
            "level": event.level,
            "service": event.service,
            "event": event.event,
            "metadata": event.metadata,
        }))


# ============================================================================
# 16. LOG PRIVACY
# ============================================================================

def redact_sensitive_log_fields(
    record: Mapping[str, Any],
    sensitive_fields: Iterable[str],
) -> dict[str, Any]:
    """
    Redaction prevents unnecessary exposure of sensitive values.

    It is better to avoid collecting sensitive information in logs at all.
    Redaction is a defensive layer, not a substitute for data minimization.
    """
    sensitive = set(sensitive_fields)

    return {
        key: "[REDACTED]" if key in sensitive else value
        for key, value in record.items()
    }


def log_redaction_demo() -> None:
    record = {
        "user_id": "U123",
        "email": "person@example.com",
        "password": "should-never-be-logged",
        "event": "login",
    }

    print("\n=== LOG REDACTION ===")
    print(
        redact_sensitive_log_fields(
            record,
            {"email", "password"},
        )
    )


# ============================================================================
# 17. SENSOR DATA COLLECTION
# ============================================================================

@dataclass
class SensorReading:
    sensor_id: str
    timestamp: float
    value: float
    unit: str


def collect_sensor_readings(
    sensor_id: str,
    values: Sequence[float],
    unit: str,
) -> list[SensorReading]:
    readings = []

    for value in values:
        if not math.isfinite(value):
            raise ValueError("Sensor value must be finite.")

        readings.append(
            SensorReading(
                sensor_id=sensor_id,
                timestamp=time.time(),
                value=float(value),
                unit=unit,
            )
        )

    return readings


def sensor_quality_control(
    readings: Sequence[SensorReading],
    minimum: float,
    maximum: float,
) -> list[SensorReading]:
    """
    Range checks identify physically implausible readings.

    A range failure does not automatically prove that the observation is wrong.
    Sensor calibration, environmental conditions, and device specifications
    determine what constitutes a valid range.
    """
    return [
        reading
        for reading in readings
        if minimum <= reading.value <= maximum
    ]


def sensor_collection_demo() -> None:
    raw_values = [23.4, 23.6, 23.5, 9999.0, 23.7]

    readings = collect_sensor_readings(
        sensor_id="TEMP-001",
        values=raw_values,
        unit="C",
    )

    valid = sensor_quality_control(
        readings,
        minimum=-50,
        maximum=100,
    )

    print("\n=== SENSOR DATA ===")
    print("Raw readings:", len(readings))
    print("Accepted readings:", len(valid))
    print("Accepted values:", [reading.value for reading in valid])


# ============================================================================
# 18. TRANSACTIONAL DATA
# ============================================================================

@dataclass
class Transaction:
    transaction_id: str
    customer_id: str
    amount: float
    currency: str
    status: str
    timestamp: str


def validate_transaction(transaction: Transaction) -> list[str]:
    errors = []

    if not transaction.transaction_id:
        errors.append("Missing transaction ID.")

    if not transaction.customer_id:
        errors.append("Missing customer ID.")

    if transaction.amount < 0:
        errors.append("Amount cannot be negative.")

    if len(transaction.currency) != 3:
        errors.append("Currency should use a three-letter code.")

    allowed_statuses = {"PENDING", "COMPLETED", "FAILED", "REFUNDED"}

    if transaction.status not in allowed_statuses:
        errors.append("Invalid transaction status.")

    return errors


def transaction_collection_demo() -> None:
    transaction = Transaction(
        transaction_id="TX1001",
        customer_id="C100",
        amount=2500,
        currency="INR",
        status="COMPLETED",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    print("\n=== TRANSACTION DATA ===")
    print("Validation errors:", validate_transaction(transaction))


# ============================================================================
# 19. DATA COLLECTION FROM CSV
# ============================================================================

def collect_csv_data(csv_text: str) -> list[dict[str, str]]:
    """
    CSV collection demonstrates schema-aware parsing.

    csv.DictReader handles quoted fields and delimiters more safely than
    manually splitting strings on commas.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    if reader.fieldnames is None:
        raise ValueError("CSV has no header.")

    return rows


def csv_collection_demo() -> None:
    csv_text = """customer_id,name,amount
101,Alice,500
102,"Bob, Jr.",750
103,Carol,1000
"""

    print("\n=== CSV COLLECTION ===")
    rows = collect_csv_data(csv_text)
    for row in rows:
        print(row)


# ============================================================================
# 20. JSON COLLECTION
# ============================================================================

def validate_json_records(payload: str) -> list[dict[str, Any]]:
    data = json.loads(payload)

    if not isinstance(data, list):
        raise ValueError("Expected a JSON array.")

    validated = []

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Record {index} is not an object.")

        if "id" not in item:
            raise ValueError(f"Record {index} has no id.")

        validated.append(item)

    return validated


def json_collection_demo() -> None:
    payload = """
    [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"}
    ]
    """

    print("\n=== JSON COLLECTION ===")
    print(validate_json_records(payload))


# ============================================================================
# 21. DATA QUALITY DIMENSIONS
# ============================================================================

def calculate_completeness(
    records: Sequence[Mapping[str, Any]],
    required_fields: Sequence[str],
) -> float:
    """
    Completeness here means the proportion of required field values that
    are present and non-empty.
    """
    if not records or not required_fields:
        return 1.0

    total = len(records) * len(required_fields)
    present = 0

    for record in records:
        for field_name in required_fields:
            value = record.get(field_name)
            if value is not None and value != "":
                present += 1

    return present / total


def calculate_uniqueness(
    records: Sequence[Mapping[str, Any]],
    key: str,
) -> float:
    """
    Measures the proportion of records with unique key values.

    This is not the same as business-level duplicate detection because
    uniqueness depends on the chosen key.
    """
    if not records:
        return 1.0

    values = [record.get(key) for record in records]
    return len(set(values)) / len(values)


def detect_duplicates(
    records: Sequence[Mapping[str, Any]],
    key: str,
) -> list[Mapping[str, Any]]:
    seen: set[Any] = set()
    duplicates = []

    for record in records:
        value = record.get(key)

        if value in seen:
            duplicates.append(record)
        else:
            seen.add(value)

    return duplicates


def data_quality_demo() -> None:
    records = [
        {"id": 1, "name": "A", "email": "a@example.com"},
        {"id": 2, "name": "B", "email": ""},
        {"id": 2, "name": "B duplicate", "email": "b@example.com"},
    ]

    print("\n=== DATA QUALITY ===")
    print(
        "Completeness:",
        calculate_completeness(records, ["id", "name", "email"]),
    )
    print("Uniqueness:", calculate_uniqueness(records, "id"))
    print("Duplicates:", detect_duplicates(records, "id"))

    dimensions = [
        "accuracy",
        "completeness",
        "consistency",
        "validity",
        "uniqueness",
        "timeliness",
        "integrity",
    ]

    print("Important quality dimensions:", ", ".join(dimensions))


# ============================================================================
# 22. VALIDATION PIPELINE
# ============================================================================

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    normalized_record: dict[str, Any] | None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_customer_record(
    record: Mapping[str, Any],
) -> ValidationResult:
    errors: list[str] = []

    customer_id = record.get("customer_id")
    name = record.get("name")
    email = record.get("email")

    if not isinstance(customer_id, int) or customer_id <= 0:
        errors.append("customer_id must be a positive integer.")

    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string.")

    if not isinstance(email, str) or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email.strip(),
    ):
        errors.append("email has an invalid basic format.")

    if errors:
        return ValidationResult(False, errors, None)

    normalized = {
        "customer_id": customer_id,
        "name": " ".join(name.split()),
        "email": normalize_email(email),
    }

    return ValidationResult(True, [], normalized)


def validation_pipeline_demo() -> None:
    records = [
        {"customer_id": 1, "name": " Alice  ", "email": " ALICE@example.com "},
        {"customer_id": -1, "name": "", "email": "invalid"},
    ]

    print("\n=== VALIDATION PIPELINE ===")

    for record in records:
        result = validate_customer_record(record)
        print(result)


# ============================================================================
# 23. NORMALIZATION AND STANDARDIZATION
# ============================================================================

def normalize_country(value: str) -> str:
    mapping = {
        "india": "IN",
        "ind": "IN",
        "in": "IN",
        "united states": "US",
        "usa": "US",
        "us": "US",
    }

    normalized = value.strip().lower()
    return mapping.get(normalized, normalized.upper())


def standardization_demo() -> None:
    values = ["India", " india ", "IND", "IN", "USA", "United States"]

    print("\n=== STANDARDIZATION ===")
    for value in values:
        print(f"{value!r} -> {normalize_country(value)}")

    print(
        "Standardization improves consistency, but normalization rules must "
        "preserve meaningful distinctions."
    )


# ============================================================================
# 24. MISSING DATA
# ============================================================================

def classify_missing_value(value: Any) -> str:
    """
    Missingness should not automatically be treated as zero.

    Examples:
        None -> missing
        0 -> observed zero
        "" -> empty/missing depending on schema
        "N/A" -> explicit unavailable code
    """
    if value is None:
        return "missing"

    if value == "":
        return "empty"

    if isinstance(value, str) and value.strip().upper() in {
        "N/A",
        "NA",
        "UNKNOWN",
        "NOT AVAILABLE",
    }:
        return "explicit_missing_code"

    return "observed"


def missing_data_demo() -> None:
    values = [None, "", "N/A", 0, 100]

    print("\n=== MISSING DATA ===")
    for value in values:
        print(repr(value), "->", classify_missing_value(value))

    print(
        "Missingness can arise from nonresponse, system failures, inapplicability, "
        "privacy restrictions, measurement failures, or intentional skipping."
    )


# ============================================================================
# 25. MEASUREMENT ERROR
# ============================================================================

def measurement_error_demo() -> None:
    true_values = [10, 20, 30, 40, 50]
    measured_values = [11, 18, 31, 39, 55]

    errors = [
        measured - true
        for measured, true in zip(measured_values, true_values)
    ]

    mean_error = statistics.mean(errors)
    mean_absolute_error = statistics.mean(abs(error) for error in errors)

    print("\n=== MEASUREMENT ERROR ===")
    print("Errors:", errors)
    print("Mean error:", mean_error)
    print("Mean absolute error:", mean_absolute_error)

    print(
        "Random measurement error varies around the true value; systematic "
        "measurement error shifts observations consistently."
    )


# ============================================================================
# 26. NONRESPONSE BIAS
# ============================================================================

def nonresponse_bias_demo() -> None:
    population = [
        {"id": i, "satisfaction": 2 if i < 500 else 5}
        for i in range(1000)
    ]

    # Assume the dissatisfied group is much less likely to respond.
    respondents = [
        row
        for row in population
        if row["satisfaction"] == 5
        or row["id"] % 5 == 0
    ]

    population_mean = statistics.mean(
        row["satisfaction"] for row in population
    )
    respondent_mean = statistics.mean(
        row["satisfaction"] for row in respondents
    )

    print("\n=== NONRESPONSE BIAS ===")
    print("Population mean satisfaction:", population_mean)
    print("Respondent mean satisfaction:", respondent_mean)
    print(
        "A high response count does not guarantee an unbiased estimate. "
        "The response mechanism itself can be related to the measured outcome."
    )


# ============================================================================
# 27. SELECTION BIAS
# ============================================================================

def selection_bias_demo() -> None:
    """
    Selection bias occurs when inclusion probabilities are related to the
    outcome or characteristics relevant to the study.
    """
    population = [
        {
            "id": i,
            "income": 20000 + i * 100,
            "platform_user": i % 3 != 0,
        }
        for i in range(1, 301)
    ]

    selected = [
        row for row in population
        if row["platform_user"]
    ]

    print("\n=== SELECTION BIAS ===")
    print("Population:", len(population))
    print("Selected through platform:", len(selected))
    print(
        "The platform population may differ systematically from the target "
        "population even when all platform users are collected accurately."
    )


# ============================================================================
# 28. INTERVIEW AND OBSERVATIONAL DATA
# ============================================================================

@dataclass
class InterviewRecord:
    participant_id: str
    interviewer_id: str
    question: str
    answer: str
    timestamp: str


def interview_demo() -> None:
    record = InterviewRecord(
        participant_id="P100",
        interviewer_id="I20",
        question="What makes the service difficult to use?",
        answer="The checkout process is unclear.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    print("\n=== INTERVIEW DATA ===")
    print(record)

    print(
        "Interview collection can capture context and explanations that fixed "
        "choice surveys may miss, but interviewer effects, recall, social "
        "desirability, and coding subjectivity require control."
    )


# ============================================================================
# 29. EXPERIMENTAL DATA COLLECTION
# ============================================================================

@dataclass
class ExperimentObservation:
    subject_id: str
    group: str
    outcome: float


def experiment_demo() -> None:
    observations = [
        ExperimentObservation("S1", "control", 70),
        ExperimentObservation("S2", "control", 75),
        ExperimentObservation("S3", "treatment", 82),
        ExperimentObservation("S4", "treatment", 88),
    ]

    grouped: dict[str, list[float]] = defaultdict(list)

    for observation in observations:
        grouped[observation.group].append(observation.outcome)

    print("\n=== EXPERIMENTAL DATA ===")

    for group, outcomes in grouped.items():
        print(group, "mean =", statistics.mean(outcomes))

    print(
        "Random assignment, treatment control, preregistered measurement rules, "
        "consistent procedures, and appropriate sample design strengthen causal inference."
    )


# ============================================================================
# 30. DATA COLLECTION ARCHITECTURE
# ============================================================================

@dataclass
class CollectionPipeline:
    source: str
    ingestion: str
    validation: str
    storage: str
    monitoring: str


def architecture_demo() -> None:
    pipeline = CollectionPipeline(
        source="API / application events / sensors",
        ingestion="batch or streaming ingestion",
        validation="schema + business rules + quality checks",
        storage="operational database / object storage / warehouse",
        monitoring="quality metrics + latency + failure monitoring",
    )

    print("\n=== COLLECTION ARCHITECTURE ===")
    print(pipeline)

    print(
        "\nA production collection pipeline commonly follows:"
        "\nSource -> Ingestion -> Validation -> Transformation -> Storage"
        "\n       -> Quality Monitoring -> Governance -> Consumers"
    )


# ============================================================================
# 31. BATCH VS STREAMING
# ============================================================================

def batch_vs_streaming_demo() -> None:
    print("\n=== BATCH VS STREAMING ===")

    comparison = {
        "batch": {
            "collection": "Periodic groups of records",
            "latency": "Minutes to days",
            "complexity": "Usually lower",
            "examples": "Daily transactions, monthly surveys",
        },
        "streaming": {
            "collection": "Continuous event flow",
            "latency": "Milliseconds to seconds/minutes",
            "complexity": "Usually higher",
            "examples": "IoT telemetry, click events, payment monitoring",
        },
    }

    for architecture, characteristics in comparison.items():
        print(architecture.upper())
        for key, value in characteristics.items():
            print(f"  {key}: {value}")


# ============================================================================
# 32. EVENT SCHEMA DESIGN
# ============================================================================

@dataclass
class Event:
    event_id: str
    event_type: str
    event_time: str
    producer: str
    payload: dict[str, Any]
    schema_version: int


def validate_event(event: Event) -> list[str]:
    errors = []

    if not event.event_id:
        errors.append("event_id is required.")

    if not event.event_type:
        errors.append("event_type is required.")

    if not event.event_time:
        errors.append("event_time is required.")

    if not event.producer:
        errors.append("producer is required.")

    if event.schema_version <= 0:
        errors.append("schema_version must be positive.")

    return errors


def event_schema_demo() -> None:
    event = Event(
        event_id="E100",
        event_type="order_created",
        event_time=datetime.now(timezone.utc).isoformat(),
        producer="checkout-service",
        payload={"order_id": "O100", "amount": 500},
        schema_version=1,
    )

    print("\n=== EVENT SCHEMA ===")
    print(event)
    print("Validation:", validate_event(event))


# ============================================================================
# 33. IDEMPOTENCY AND DUPLICATES
# ============================================================================

class IdempotentCollector:
    """
    A collector can use stable event IDs to avoid processing the same event
    more than once.

    This is especially important in distributed systems where retries can
    produce duplicate delivery.
    """

    def __init__(self) -> None:
        self.processed_ids: set[str] = set()
        self.records: list[Event] = []

    def collect(self, event: Event) -> bool:
        if event.event_id in self.processed_ids:
            return False

        self.processed_ids.add(event.event_id)
        self.records.append(event)
        return True


def idempotency_demo() -> None:
    collector = IdempotentCollector()

    event = Event(
        event_id="E1",
        event_type="payment",
        event_time=datetime.now(timezone.utc).isoformat(),
        producer="payment-service",
        payload={"amount": 100},
        schema_version=1,
    )

    print("\n=== IDEMPOTENCY ===")
    print("First collection:", collector.collect(event))
    print("Duplicate collection:", collector.collect(event))
    print("Stored records:", len(collector.records))


# ============================================================================
# 34. EVENT TIME VS PROCESSING TIME
# ============================================================================

def event_time_demo() -> None:
    event_time = "2026-09-05T10:00:00+00:00"
    processing_time = datetime.now(timezone.utc).isoformat()

    print("\n=== EVENT TIME VS PROCESSING TIME ===")
    print("Event time:", event_time)
    print("Processing time:", processing_time)

    print(
        "Event time describes when the underlying event occurred. "
        "Processing time describes when a system handled the record. "
        "They can differ because of network delay, buffering, retries, or offline devices."
    )


# ============================================================================
# 35. SAMPLING WEIGHTS
# ============================================================================

def weighted_estimate(
    values: Sequence[float],
    weights: Sequence[float],
) -> float:
    if len(values) != len(weights):
        raise ValueError("values and weights must have equal length.")

    if not values:
        raise ValueError("At least one observation is required.")

    if any(weight < 0 for weight in weights):
        raise ValueError("Weights cannot be negative.")

    total_weight = sum(weights)

    if total_weight == 0:
        raise ValueError("Total weight must be positive.")

    return sum(
        value * weight
        for value, weight in zip(values, weights)
    ) / total_weight


def weighting_demo() -> None:
    print("\n=== SAMPLING WEIGHTS ===")

    values = [10, 20, 30]
    weights = [1, 2, 1]

    print("Weighted mean:", weighted_estimate(values, weights))

    print(
        "Weights can compensate for unequal selection probabilities when the "
        "sampling design and weighting methodology justify them. Poorly chosen "
        "weights can increase variance or create instability."
    )


# ============================================================================
# 36. DATA COLLECTION BIAS TAXONOMY
# ============================================================================

def bias_taxonomy_demo() -> None:
    biases = {
        "coverage bias": "Parts of the target population cannot enter the sampling frame.",
        "selection bias": "Inclusion probabilities systematically differ across relevant units.",
        "nonresponse bias": "Responders differ meaningfully from nonresponders.",
        "measurement bias": "The measurement procedure systematically distorts observations.",
        "interviewer bias": "Interviewer behavior influences responses or observations.",
        "recall bias": "Participants remember past events inaccurately or differently.",
        "social desirability bias": "Respondents alter answers to appear socially acceptable.",
        "survivorship bias": "Collection focuses on units that remain while excluding those that disappeared.",
        "confirmation bias": "Collection design preferentially seeks evidence supporting an existing belief.",
        "instrumentation bias": "Changes in measurement devices or procedures alter recorded values.",
    }

    print("\n=== DATA COLLECTION BIAS ===")
    for name, description in biases.items():
        print(f"{name}: {description}")


# ============================================================================
# 37. DATA PROVENANCE
# ============================================================================

@dataclass
class Provenance:
    source_name: str
    collection_method: str
    collected_at: str
    collector_version: str
    schema_version: int
    transformation_history: list[str]


def provenance_demo() -> None:
    provenance = Provenance(
        source_name="customer_api",
        collection_method="REST API",
        collected_at=datetime.now(timezone.utc).isoformat(),
        collector_version="2.4.0",
        schema_version=3,
        transformation_history=[
            "trimmed string fields",
            "normalized country codes",
            "validated customer IDs",
        ],
    )

    print("\n=== DATA PROVENANCE ===")
    print(provenance)

    print(
        "Provenance allows downstream users to determine where a value came from, "
        "when it was collected, which software produced it, and what transformations occurred."
    )


# ============================================================================
# 38. DATA LINEAGE
# ============================================================================

def lineage_demo() -> None:
    lineage = [
        "Source system",
        "Raw ingestion",
        "Validation",
        "Normalization",
        "Deduplication",
        "Warehouse table",
        "Analytical dataset",
        "Report/model",
    ]

    print("\n=== DATA LINEAGE ===")
    print(" -> ".join(lineage))


# ============================================================================
# 39. DATA CONTRACTS
# ============================================================================

@dataclass
class DataContract:
    dataset_name: str
    required_fields: dict[str, type]
    nullable_fields: set[str]
    version: int


def enforce_data_contract(
    record: Mapping[str, Any],
    contract: DataContract,
) -> list[str]:
    errors = []

    for field_name, expected_type in contract.required_fields.items():
        if field_name not in record:
            errors.append(f"Missing required field: {field_name}")
            continue

        value = record[field_name]

        if value is None:
            if field_name not in contract.nullable_fields:
                errors.append(f"Field cannot be null: {field_name}")
            continue

        if not isinstance(value, expected_type):
            errors.append(
                f"{field_name} expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

    return errors


def data_contract_demo() -> None:
    contract = DataContract(
        dataset_name="customers",
        required_fields={
            "customer_id": int,
            "name": str,
            "age": int,
        },
        nullable_fields=set(),
        version=1,
    )

    valid = {"customer_id": 1, "name": "Alice", "age": 33}
    invalid = {"customer_id": "1", "name": "Alice"}

    print("\n=== DATA CONTRACTS ===")
    print("Valid:", enforce_data_contract(valid, contract))
    print("Invalid:", enforce_data_contract(invalid, contract))


# ============================================================================
# 40. SCHEMA EVOLUTION
# ============================================================================

def schema_evolution_demo() -> None:
    version_one = {
        "customer_id": 1,
        "name": "Alice",
    }

    version_two = {
        "customer_id": 1,
        "name": "Alice",
        "country": "IN",
    }

    print("\n=== SCHEMA EVOLUTION ===")
    print("Version 1:", version_one)
    print("Version 2:", version_two)

    print(
        "Adding optional fields is often easier to evolve safely than removing "
        "or changing the meaning/type of existing fields."
    )

    print(
        "Breaking schema changes require coordinated producer and consumer changes "
        "or explicit versioning."
    )


# ============================================================================
# 41. DATA COLLECTION SECURITY
# ============================================================================

def security_principles_demo() -> None:
    principles = [
        "Collect only data required for the defined purpose.",
        "Encrypt sensitive data in transit and at rest.",
        "Use authentication and authorization.",
        "Never hard-code API secrets in source code.",
        "Rotate credentials and restrict their scope.",
        "Validate untrusted input.",
        "Use parameterized database queries.",
        "Protect logs from sensitive data leakage.",
        "Maintain audit trails for sensitive collection.",
        "Apply least privilege.",
        "Use secure secret storage in production.",
        "Define retention and deletion controls.",
    ]

    print("\n=== SECURITY ===")
    for principle in principles:
        print("-", principle)


# ============================================================================
# 42. SECRET HANDLING
# ============================================================================

def get_api_key_from_environment(
    environment: Mapping[str, str],
    variable_name: str = "API_KEY",
) -> str:
    """
    Demonstrates dependency injection for secret retrieval.

    Production applications normally obtain secrets from a controlled secret
    manager or protected runtime environment rather than source code.
    """
    value = environment.get(variable_name)

    if not value:
        raise RuntimeError(f"Missing secret: {variable_name}")

    return value


def secret_handling_demo() -> None:
    print("\n=== SECRET HANDLING ===")

    simulated_environment = {
        "API_KEY": "example-secret-not-for-production",
    }

    print(
        "Secret loaded:",
        bool(get_api_key_from_environment(simulated_environment)),
    )


# ============================================================================
# 43. PRIVACY AND DATA MINIMIZATION
# ============================================================================

def minimize_record(
    record: Mapping[str, Any],
    allowed_fields: Iterable[str],
) -> dict[str, Any]:
    allowed = set(allowed_fields)

    return {
        key: value
        for key, value in record.items()
        if key in allowed
    }


def privacy_demo() -> None:
    record = {
        "customer_id": "C1",
        "name": "Alice",
        "email": "alice@example.com",
        "date_of_birth": "1992-01-01",
        "purchase_amount": 500,
    }

    minimized = minimize_record(
        record,
        {"customer_id", "purchase_amount"},
    )

    print("\n=== DATA MINIMIZATION ===")
    print("Original fields:", list(record))
    print("Required fields:", minimized)

    print(
        "Data minimization reduces privacy exposure, storage burden, attack surface, "
        "and unnecessary processing."
    )


# ============================================================================
# 44. ANONYMIZATION VS PSEUDONYMIZATION
# ============================================================================

import hashlib


def pseudonymize_identifier(identifier: str, secret_salt: str) -> str:
    """
    Hashing with a secret salt can create a stable pseudonymous identifier.

    A pseudonym is not automatically anonymous. If the mapping or auxiliary
    information can be used to identify a person, privacy obligations may remain.
    """
    data = f"{secret_salt}:{identifier}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def privacy_identifier_demo() -> None:
    print("\n=== PSEUDONYMIZATION ===")

    identifier = "customer-123"
    pseudonym = pseudonymize_identifier(
        identifier,
        "example-salt",
    )

    print("Original:", identifier)
    print("Pseudonym:", pseudonym)

    print(
        "Anonymization aims to prevent identification under a defined threat model. "
        "Pseudonymization replaces identifiers but does not necessarily eliminate identifiability."
    )


# ============================================================================
# 45. DATA RETENTION
# ============================================================================

@dataclass
class RetentionPolicy:
    dataset_name: str
    retention_days: int
    deletion_method: str


def retention_demo() -> None:
    policy = RetentionPolicy(
        dataset_name="application_events",
        retention_days=90,
        deletion_method="automated expiration",
    )

    print("\n=== RETENTION ===")
    print(policy)

    print(
        "Retention should be tied to legitimate operational, analytical, legal, "
        "and governance requirements rather than indefinite storage by default."
    )


# ============================================================================
# 46. COLLECTION MONITORING
# ============================================================================

@dataclass
class CollectionMetrics:
    records_received: int
    records_accepted: int
    records_rejected: int
    duplicates: int
    collection_latency_seconds: float


def calculate_acceptance_rate(metrics: CollectionMetrics) -> float:
    if metrics.records_received == 0:
        return 0.0

    return metrics.records_accepted / metrics.records_received


def collection_monitoring_demo() -> None:
    metrics = CollectionMetrics(
        records_received=10000,
        records_accepted=9700,
        records_rejected=300,
        duplicates=120,
        collection_latency_seconds=4.8,
    )

    print("\n=== COLLECTION MONITORING ===")
    print("Acceptance rate:", calculate_acceptance_rate(metrics))
    print("Rejected:", metrics.records_rejected)
    print("Duplicates:", metrics.duplicates)
    print("Latency:", metrics.collection_latency_seconds)

    print(
        "Production monitoring should detect silent failures, sudden volume changes, "
        "schema drift, unusual rejection rates, duplicate spikes, latency increases, "
        "and source outages."
    )


# ============================================================================
# 47. DATA DRIFT AND DISTRIBUTION MONITORING
# ============================================================================

def distribution(values: Sequence[Any]) -> dict[Any, float]:
    counts = Counter(values)
    total = len(values)

    if total == 0:
        return {}

    return {
        key: count / total
        for key, count in counts.items()
    }


def total_variation_distance(
    first: Mapping[Any, float],
    second: Mapping[Any, float],
) -> float:
    """
    Total variation distance:

        TV = 0.5 * sum(|P(x) - Q(x)|)

    It can compare categorical distributions.
    """
    keys = set(first) | set(second)

    return 0.5 * sum(
        abs(first.get(key, 0.0) - second.get(key, 0.0))
        for key in keys
    )


def drift_demo() -> None:
    baseline = ["A"] * 70 + ["B"] * 30
    current = ["A"] * 40 + ["B"] * 60

    baseline_distribution = distribution(baseline)
    current_distribution = distribution(current)

    print("\n=== DISTRIBUTION DRIFT ===")
    print("Baseline:", baseline_distribution)
    print("Current:", current_distribution)
    print(
        "Total variation distance:",
        total_variation_distance(
            baseline_distribution,
            current_distribution,
        ),
    )


# ============================================================================
# 48. QUALITY CONTROL RULE ENGINE
# ============================================================================

@dataclass
class QualityRule:
    name: str
    check: Callable[[Mapping[str, Any]], bool]


class QualityEngine:
    def __init__(self, rules: Sequence[QualityRule]) -> None:
        self.rules = list(rules)

    def evaluate(
        self,
        record: Mapping[str, Any],
    ) -> dict[str, bool]:
        return {
            rule.name: rule.check(record)
            for rule in self.rules
        }

    def is_valid(
        self,
        record: Mapping[str, Any],
    ) -> bool:
        return all(self.evaluate(record).values())


def quality_engine_demo() -> None:
    engine = QualityEngine(
        [
            QualityRule(
                "positive_customer_id",
                lambda row: isinstance(row.get("customer_id"), int)
                and row["customer_id"] > 0,
            ),
            QualityRule(
                "nonnegative_amount",
                lambda row: isinstance(row.get("amount"), (int, float))
                and row["amount"] >= 0,
            ),
            QualityRule(
                "currency_length",
                lambda row: isinstance(row.get("currency"), str)
                and len(row["currency"]) == 3,
            ),
        ]
    )

    records = [
        {"customer_id": 1, "amount": 500, "currency": "INR"},
        {"customer_id": -1, "amount": 500, "currency": "INR"},
        {"customer_id": 2, "amount": -5, "currency": "INR"},
    ]

    print("\n=== QUALITY RULE ENGINE ===")
    for record in records:
        print(record, "->", engine.evaluate(record), "valid=", engine.is_valid(record))


# ============================================================================
# 49. COLLECTION FAILURE MODES
# ============================================================================

def failure_modes_demo() -> None:
    failure_modes = {
        "source unavailable": "Retry where appropriate and alert after bounded failure.",
        "authentication failure": "Stop and repair credentials rather than repeatedly retrying.",
        "rate limiting": "Honor server limits and use controlled backoff.",
        "schema change": "Validate contracts and quarantine incompatible records.",
        "duplicate delivery": "Use stable IDs and idempotent processing.",
        "partial batch": "Track offsets/checkpoints and make recovery deterministic.",
        "corrupt record": "Quarantine or reject with an auditable reason.",
        "clock error": "Validate timestamps and distinguish event time from processing time.",
        "silent source change": "Monitor distributions, volumes, and schema characteristics.",
    }

    print("\n=== FAILURE MODES ===")
    for failure, response in failure_modes.items():
        print(f"{failure}: {response}")


# ============================================================================
# 50. QUARANTINING INVALID DATA
# ============================================================================

@dataclass
class QuarantinedRecord:
    record: dict[str, Any]
    errors: list[str]
    quarantined_at: str


def quarantine_records(
    records: Sequence[Mapping[str, Any]],
    validator: Callable[[Mapping[str, Any]], list[str]],
) -> tuple[list[dict[str, Any]], list[QuarantinedRecord]]:
    accepted: list[dict[str, Any]] = []
    quarantined: list[QuarantinedRecord] = []

    for record in records:
        errors = validator(record)

        if errors:
            quarantined.append(
                QuarantinedRecord(
                    record=dict(record),
                    errors=errors,
                    quarantined_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        else:
            accepted.append(dict(record))

    return accepted, quarantined


def quarantine_demo() -> None:
    def validator(record: Mapping[str, Any]) -> list[str]:
        errors = []

        if not isinstance(record.get("id"), int):
            errors.append("id must be an integer.")

        if not isinstance(record.get("amount"), (int, float)):
            errors.append("amount must be numeric.")
        elif record["amount"] < 0:
            errors.append("amount cannot be negative.")

        return errors

    records = [
        {"id": 1, "amount": 100},
        {"id": "2", "amount": 200},
        {"id": 3, "amount": -50},
    ]

    accepted, quarantined = quarantine_records(records, validator)

    print("\n=== QUARANTINE ===")
    print("Accepted:", accepted)
    print("Quarantined:", quarantined)


# ============================================================================
# 51. DEDUPLICATION STRATEGIES
# ============================================================================

def deduplicate_by_key(
    records: Sequence[Mapping[str, Any]],
    key: str,
) -> list[Mapping[str, Any]]:
    seen: set[Any] = set()
    result = []

    for record in records:
        identifier = record.get(key)

        if identifier in seen:
            continue

        seen.add(identifier)
        result.append(record)

    return result


def deduplication_demo() -> None:
    records = [
        {"id": 1, "value": "first"},
        {"id": 2, "value": "second"},
        {"id": 1, "value": "duplicate"},
    ]

    print("\n=== DEDUPLICATION ===")
    print(deduplicate_by_key(records, "id"))

    print(
        "Deduplication policy must define which record wins when duplicates differ. "
        "First-write, last-write, highest-quality, or version-aware rules may be appropriate."
    )


# ============================================================================
# 52. CHECKPOINTING
# ============================================================================

@dataclass
class Checkpoint:
    source_name: str
    position: int
    updated_at: str


def checkpoint_demo() -> None:
    checkpoint = Checkpoint(
        source_name="transaction-stream",
        position=105000,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    print("\n=== CHECKPOINTING ===")
    print(checkpoint)

    print(
        "Checkpoints let a collector resume from a known position after interruption. "
        "The checkpoint must be persisted safely and must correspond to a clearly defined "
        "processing guarantee."
    )


# ============================================================================
# 53. EXACTLY-ONCE, AT-LEAST-ONCE, AT-MOST-ONCE
# ============================================================================

def delivery_semantics_demo() -> None:
    semantics = {
        "at-most-once": (
            "An event is processed zero or one time; failures can cause loss."
        ),
        "at-least-once": (
            "An event is retried until acknowledged; duplicates can occur."
        ),
        "exactly-once": (
            "The system provides semantics intended to make each logical event's "
            "effect occur once, usually through coordinated transactional mechanisms."
        ),
    }

    print("\n=== DELIVERY SEMANTICS ===")
    for name, description in semantics.items():
        print(name, ":", description)


# ============================================================================
# 54. COLLECTION PERFORMANCE
# ============================================================================

def performance_demo() -> None:
    """
    Common performance considerations:
        - batch requests instead of one request per record where supported
        - connection reuse
        - bounded concurrency
        - streaming large files
        - incremental processing
        - efficient indexing
        - avoiding unnecessary serialization
        - compression where appropriate
        - checkpointing
        - backpressure
    """

    records = list(range(100000))

    start = time.perf_counter()
    total = sum(records)
    elapsed = time.perf_counter() - start

    print("\n=== PERFORMANCE ===")
    print("Processed records:", len(records))
    print("Computed total:", total)
    print("Elapsed seconds:", elapsed)


# ============================================================================
# 55. MEMORY-EFFICIENT STREAMING
# ============================================================================

def generate_records(number_of_records: int) -> Iterator[dict[str, int]]:
    """
    A generator produces one record at a time instead of materializing the
    entire collection in memory.
    """
    for record_id in range(number_of_records):
        yield {
            "id": record_id,
            "value": record_id * 2,
        }


def streaming_demo() -> None:
    print("\n=== STREAMING COLLECTION ===")

    total = 0

    for record in generate_records(1_000_000):
        total += record["value"]

    print("Processed one million generated records.")
    print("Total:", total)


# ============================================================================
# 56. RATE LIMITING
# ============================================================================

class SimpleRateLimiter:
    def __init__(self, minimum_interval_seconds: float) -> None:
        if minimum_interval_seconds < 0:
            raise ValueError("Interval cannot be negative.")

        self.minimum_interval_seconds = minimum_interval_seconds
        self.last_request_time: float | None = None

    def wait_if_needed(self) -> None:
        now = time.monotonic()

        if self.last_request_time is not None:
            elapsed = now - self.last_request_time
            remaining = self.minimum_interval_seconds - elapsed

            if remaining > 0:
                time.sleep(remaining)

        self.last_request_time = time.monotonic()


def rate_limit_demo() -> None:
    limiter = SimpleRateLimiter(0.001)

    print("\n=== RATE LIMITING ===")

    for request_number in range(3):
        limiter.wait_if_needed()
        print("Request", request_number + 1)


# ============================================================================
# 57. BACKPRESSURE
# ============================================================================

def backpressure_demo() -> None:
    print("\n=== BACKPRESSURE ===")

    print(
        "Backpressure occurs when producers generate data faster than consumers "
        "can process it. A robust pipeline can bound queues, slow producers, "
        "buffer safely, reject excess traffic, or scale consumers."
    )


# ============================================================================
# 58. SAMPLING FROM A STREAM
# ============================================================================

def reservoir_sample(
    stream: Iterable[Any],
    sample_size: int,
    seed: int | None = None,
) -> list[Any]:
    """
    Reservoir sampling selects a uniform sample of fixed size from a stream
    whose total length may be unknown.

    Time: O(N)
    Extra space: O(k), where k is sample_size.
    """
    if sample_size < 0:
        raise ValueError("sample_size cannot be negative.")

    generator = random.Random(seed)
    reservoir: list[Any] = []

    for index, item in enumerate(stream):
        if index < sample_size:
            reservoir.append(item)
            continue

        replacement_index = generator.randint(0, index)

        if replacement_index < sample_size:
            reservoir[replacement_index] = item

    return reservoir


def reservoir_sampling_demo() -> None:
    print("\n=== RESERVOIR SAMPLING ===")
    sample = reservoir_sample(range(1, 1_000_001), 10, seed=42)
    print("Sample from one-million-item stream:", sample)


# ============================================================================
# 59. TEMPORAL SAMPLING AND PERIODICITY
# ============================================================================

def temporal_sampling_demo() -> None:
    readings = [
        {"minute": minute, "value": 100 + 10 * math.sin(minute / 5)}
        for minute in range(60)
    ]

    hourly_like_sample = readings[::10]

    print("\n=== TEMPORAL SAMPLING ===")
    print("Sampled readings:", hourly_like_sample)

    print(
        "Temporal sampling can miss short-lived events. Sampling frequency must "
        "match the temporal scale of phenomena that matter."
    )


# ============================================================================
# 60. API RESPONSE SCHEMA VALIDATION
# ============================================================================

def validate_api_customer(payload: Mapping[str, Any]) -> list[str]:
    errors = []

    if not isinstance(payload.get("id"), int):
        errors.append("id must be an integer.")

    if not isinstance(payload.get("name"), str):
        errors.append("name must be a string.")

    if "status" not in payload:
        errors.append("status is required.")
    elif payload["status"] not in {"active", "inactive"}:
        errors.append("status is invalid.")

    return errors


def api_schema_demo() -> None:
    payloads = [
        {"id": 1, "name": "Alice", "status": "active"},
        {"id": "2", "name": "Bob", "status": "unknown"},
    ]

    print("\n=== API SCHEMA VALIDATION ===")
    for payload in payloads:
        print(payload, "->", validate_api_customer(payload))


# ============================================================================
# 61. DATA COLLECTION TESTING
# ============================================================================

def run_collection_tests() -> None:
    print("\n=== TESTS ===")

    assert normalize_country("India") == "IN"
    assert normalize_country("USA") == "US"

    assert calculate_completeness(
        [{"a": 1, "b": 2}],
        ["a", "b"],
    ) == 1.0

    assert calculate_uniqueness(
        [{"id": 1}, {"id": 2}],
        "id",
    ) == 1.0

    assert len(
        detect_duplicates(
            [{"id": 1}, {"id": 1}],
            "id",
        )
    ) == 1

    result = validate_customer_record(
        {
            "customer_id": 1,
            "name": " Alice ",
            "email": "ALICE@example.com",
        }
    )

    assert result.valid
    assert result.normalized_record["email"] == "alice@example.com"

    assert pseudonymize_identifier(
        "same",
        "salt",
    ) == pseudonymize_identifier(
        "same",
        "salt",
    )

    print("All tests passed.")


# ============================================================================
# 62. EDGE CASES
# ============================================================================

def edge_case_demo() -> None:
    print("\n=== EDGE CASES ===")

    cases = {
        "empty dataset": [],
        "single observation": [{"id": 1}],
        "all values missing": [{"value": None}, {"value": None}],
        "duplicate identifiers": [{"id": 1}, {"id": 1}],
        "zero amount": {"amount": 0},
        "negative amount": {"amount": -1},
        "empty string": {"name": ""},
        "unexpected field": {"id": 1, "unexpected": True},
    }

    for name, value in cases.items():
        print(name, ":", value)

    print(
        "Edge cases should be explicitly defined rather than left to accidental "
        "behavior. Empty collections, nulls, duplicates, boundary values, malformed "
        "records, and unexpected schema fields frequently expose collection defects."
    )


# ============================================================================
# 63. COMMON MISTAKES
# ============================================================================

def common_mistakes_demo() -> None:
    mistakes = [
        "Collecting data before defining the research question.",
        "Using a convenient sample and treating it as representative.",
        "Confusing a large sample with a representative sample.",
        "Ignoring nonresponse.",
        "Treating missing values as zero without justification.",
        "Using ambiguous survey questions.",
        "Failing to preserve collection timestamps.",
        "Changing schemas without versioning.",
        "Ignoring duplicates caused by retries.",
        "Hard-coding credentials.",
        "Logging sensitive data.",
        "Collecting more personal data than necessary.",
        "Failing to document source provenance.",
        "Ignoring rate limits.",
        "Assuming scraped data is automatically reliable.",
        "Failing to monitor silent source changes.",
        "Discarding invalid records without recording why.",
    ]

    print("\n=== COMMON MISTAKES ===")
    for mistake in mistakes:
        print("-", mistake)


# ============================================================================
# 64. SOURCE COMPARISON
# ============================================================================

def source_comparison_demo() -> None:
    sources = {
        "survey": {
            "strength": "Purpose-specific respondent information",
            "weakness": "Response and measurement bias",
            "latency": "Usually medium/high",
            "structure": "Designed",
        },
        "database": {
            "strength": "Large operational record volume",
            "weakness": "May not represent the desired population",
            "latency": "Low/medium",
            "structure": "Structured",
        },
        "API": {
            "strength": "Programmatic and repeatable access",
            "weakness": "Rate limits and changing contracts",
            "latency": "Low/medium",
            "structure": "Usually structured",
        },
        "web": {
            "strength": "Broad public information",
            "weakness": "Volatile content and legal/ethical constraints",
            "latency": "Medium",
            "structure": "Often semi-structured",
        },
        "logs": {
            "strength": "Detailed system behavior",
            "weakness": "Instrumentation gaps and high volume",
            "latency": "Low",
            "structure": "Structured or semi-structured",
        },
        "sensors": {
            "strength": "Continuous physical measurements",
            "weakness": "Calibration, noise, drift, hardware failure",
            "latency": "Very low to medium",
            "structure": "Structured",
        },
    }

    print("\n=== SOURCE COMPARISON ===")

    for source, attributes in sources.items():
        print(f"\n{source.upper()}")
        for key, value in attributes.items():
            print(f"  {key}: {value}")


# ============================================================================
# 65. COLLECTION PLAN
# ============================================================================

@dataclass
class CollectionPlan:
    objective: str
    target_population: str
    unit_of_analysis: str
    source: str
    method: str
    sampling_strategy: str
    variables: list[str]
    frequency: str
    validation_rules: list[str]
    storage: str
    retention: str


def collection_plan_demo() -> None:
    plan = CollectionPlan(
        objective="Estimate customer satisfaction.",
        target_population="Customers completing a purchase during the study period.",
        unit_of_analysis="Customer purchase experience.",
        source="Customer survey linked to transactions.",
        method="Structured survey.",
        sampling_strategy="Stratified random sample by customer segment.",
        variables=[
            "customer_segment",
            "satisfaction",
            "purchase_frequency",
            "optional_comment",
        ],
        frequency="Continuous invitation with weekly monitoring.",
        validation_rules=[
            "required satisfaction",
            "valid categorical values",
            "duplicate response prevention",
        ],
        storage="Controlled analytical database.",
        retention="Defined according to purpose and policy.",
    )

    print("\n=== COLLECTION PLAN ===")
    print(plan)


# ============================================================================
# 66. END-TO-END COLLECTION PIPELINE
# ============================================================================

def end_to_end_pipeline(
    raw_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """
    Demonstrates a simplified end-to-end pipeline:

        raw -> validation -> normalization -> deduplication -> metrics

    A production implementation would normally separate ingestion, durable raw
    storage, validation, transformation, and downstream publishing.
    """
    received = len(raw_records)

    accepted, quarantined = quarantine_records(
        raw_records,
        lambda row: validate_customer_record(row).errors,
    )

    normalized = [
        validate_customer_record(row).normalized_record
        for row in accepted
    ]

    normalized = [
        row for row in normalized
        if row is not None
    ]

    unique = deduplicate_by_key(
        normalized,
        "customer_id",
    )

    metrics = CollectionMetrics(
        records_received=received,
        records_accepted=len(unique),
        records_rejected=len(quarantined),
        duplicates=len(normalized) - len(unique),
        collection_latency_seconds=0.001,
    )

    return {
        "accepted": unique,
        "quarantined": quarantined,
        "metrics": metrics,
    }


def end_to_end_demo() -> None:
    records = [
        {
            "customer_id": 1,
            "name": " Alice ",
            "email": "ALICE@example.com",
        },
        {
            "customer_id": 2,
            "name": "Bob",
            "email": "bob@example.com",
        },
        {
            "customer_id": 2,
            "name": "Bob duplicate",
            "email": "bob2@example.com",
        },
        {
            "customer_id": -5,
            "name": "Invalid",
            "email": "invalid",
        },
    ]

    result = end_to_end_pipeline(records)

    print("\n=== END-TO-END PIPELINE ===")
    print("Accepted:", result["accepted"])
    print("Quarantined:", result["quarantined"])
    print("Metrics:", result["metrics"])


# ============================================================================
# 67. REAL-WORLD APPLICATIONS
# ============================================================================

def applications_demo() -> None:
    applications = {
        "business analytics": [
            "sales transactions",
            "customer surveys",
            "CRM records",
            "website events",
        ],
        "finance": [
            "transactions",
            "market feeds",
            "risk events",
            "account activity",
        ],
        "healthcare": [
            "clinical observations",
            "laboratory measurements",
            "patient surveys",
            "device telemetry",
        ],
        "manufacturing": [
            "machine sensors",
            "production records",
            "quality inspections",
            "maintenance logs",
        ],
        "cybersecurity": [
            "authentication events",
            "network logs",
            "endpoint telemetry",
            "security alerts",
        ],
        "retail": [
            "point-of-sale records",
            "inventory events",
            "customer behavior",
            "product surveys",
        ],
        "government": [
            "census collection",
            "administrative records",
            "public surveys",
            "service usage",
        ],
    }

    print("\n=== REAL-WORLD APPLICATIONS ===")

    for domain, sources in applications.items():
        print(domain.upper())
        for source in sources:
            print("  -", source)


# ============================================================================
# 68. FINAL KNOWLEDGE CHECK
# ============================================================================

def knowledge_check() -> None:
    questions = [
        (
            "Can a perfectly random sample still be biased?",
            "Yes. Random selection from a biased or incomplete sampling frame can produce coverage bias.",
        ),
        (
            "Does a large sample automatically become representative?",
            "No. Sample size reduces some forms of random error but does not eliminate systematic bias.",
        ),
        (
            "Is missing data always zero?",
            "No. Missingness, zero, not applicable, and unknown are distinct states.",
        ),
        (
            "Why are stable event IDs useful?",
            "They support deduplication and idempotent processing.",
        ),
        (
            "Why distinguish event time from processing time?",
            "Delayed, buffered, retried, or offline events can be processed long after they occurred.",
        ),
        (
            "Why monitor source distributions?",
            "Silent changes in upstream behavior can alter the collected dataset without obvious system failures.",
        ),
        (
            "Why use data contracts?",
            "They establish explicit expectations between producers and consumers.",
        ),
        (
            "Why is data minimization important?",
            "Unnecessary collection increases privacy exposure, storage cost, and security risk.",
        ),
    ]

    print("\n=== KNOWLEDGE CHECK ===")

    for question, answer in questions:
        print("\nQ:", question)
        print("A:", answer)


# ============================================================================
# 69. MAIN EXECUTION
# ============================================================================

def main() -> None:
    print("=" * 80)
    print("DATA COLLECTION: BEGINNER TO ADVANCED PYTHON STUDY SCRIPT")
    print("=" * 80)

    explain_data_collection()
    terminology_demo()
    compare_primary_secondary()
    describe_collection_methods()
    survey_design_demo()
    survey_bias_demo()
    survey_validation_demo()
    sampling_demo()
    sampling_bias_simulation()
    sample_size_demo()
    database_collection_demo()
    api_collection_demo()
    retry_demo()
    web_collection_demo()
    log_collection_demo()
    log_redaction_demo()
    sensor_collection_demo()
    transaction_collection_demo()
    csv_collection_demo()
    json_collection_demo()
    data_quality_demo()
    validation_pipeline_demo()
    standardization_demo()
    missing_data_demo()
    measurement_error_demo()
    nonresponse_bias_demo()
    selection_bias_demo()
    interview_demo()
    experiment_demo()
    architecture_demo()
    batch_vs_streaming_demo()
    event_schema_demo()
    idempotency_demo()
    event_time_demo()
    weighting_demo()
    bias_taxonomy_demo()
    provenance_demo()
    lineage_demo()
    data_contract_demo()
    schema_evolution_demo()
    security_principles_demo()
    secret_handling_demo()
    privacy_demo()
    privacy_identifier_demo()
    retention_demo()
    collection_monitoring_demo()
    drift_demo()
    quality_engine_demo()
    failure_modes_demo()
    quarantine_demo()
    deduplication_demo()
    checkpoint_demo()
    delivery_semantics_demo()
    performance_demo()
    streaming_demo()
    rate_limit_demo()
    backpressure_demo()
    reservoir_sampling_demo()
    temporal_sampling_demo()
    api_schema_demo()
    run_collection_tests()
    edge_case_demo()
    common_mistakes_demo()
    source_comparison_demo()
    collection_plan_demo()
    end_to_end_demo()
    applications_demo()
    knowledge_check()

    print("\n" + "=" * 80)
    print("STUDY SCRIPT EXECUTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
