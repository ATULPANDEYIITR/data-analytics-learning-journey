#!/usr/bin/env python3
"""
SQL String Functions: CONCAT, SUBSTRING, POSITION, REPLACE, LOWER, UPPER,
TRIM, and regular expressions.

This self-contained program uses Python's standard-library sqlite3 module to
execute real SQL string expressions and complements SQLite's built-in string
functions with a small compatibility layer for regular-expression operations.

The examples use realistic customer and support-ticket data so that each
string
function is demonstrated against a concrete data-cleaning or querying task.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class QueryExample:
    name: str
    description: str
    sql: str


def create_database() -> sqlite3.Connection:
    """Create an in-memory database containing realistic text data."""
    connection = sqlite3.connect(":memory:")

    connection.executescript(
        """
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            city TEXT,
            status TEXT NOT NULL
        );

        CREATE TABLE support_tickets (
            ticket_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        INSERT INTO customers
            (customer_id, first_name, last_name, email, phone, city, status)
        VALUES
            (1, '  Atul  ', 'Pandey', 'ATUL.PANDEY@EXAMPLE.COM',
             '+91-98765-43210', 'Lucknow', 'ACTIVE'),
            (2, 'Priya', 'Sharma', ' priya.sharma@example.com ',
             '+91-91234-56789', 'Delhi', 'ACTIVE'),
            (3, 'Rohan', 'Mehta', 'ROHAN.MEHTA@EXAMPLE.COM',
             '+91-99887-77665', 'Mumbai', 'INACTIVE'),
            (4, 'Neha', 'Verma', 'neha.verma@example.com',
             '+91-90000-11122', 'Bengaluru', 'ACTIVE');

        INSERT INTO support_tickets
            (ticket_id, customer_id, subject, message)
        VALUES
            (1001, 1, 'Password Reset',
             'Customer requested a password reset for the account.'),
            (1002, 2, 'Payment Failed',
             'Payment failed while processing order ORD-2026-1042.'),
            (1003, 3, 'Address Change',
             'Customer wants to change the registered delivery address.'),
            (1004, 4, 'Email Verification',
             'Verification link was sent but customer reports an error.');
        """
    )

    return connection


def register_regex_functions(connection: sqlite3.Connection) -> None:
    """
    Add REGEXP and REGEXP_REPLACE behavior to SQLite.

    SQLite supports registering application-defined SQL functions. This is
    useful because SQLite does not provide a full regular-expression function
    set by default.
    """

    def regexp(pattern: str | None, value: str | None) -> int:
        if pattern is None or value is None:
            return 0

        try:
            return int(re.search(pattern, value) is not None)
        except re.error as exc:
            raise ValueError(f"Invalid regular expression: {pattern}") from exc

    def regexp_replace(
        value: str | None,
        pattern: str | None,
        replacement: str | None,
    ) -> str | None:
        if value is None:
            return None
        if pattern is None or replacement is None:
            return value

        try:
            return re.sub(pattern, replacement, value)
        except re.error as exc:
            raise ValueError(f"Invalid regular expression: {pattern}") from exc

    connection.create_function("REGEXP", 2, regexp)
    connection.create_function("REGEXP_REPLACE", 3, regexp_replace)


def print_rows(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple = (),
) -> None:
    """Execute a SELECT statement and display its columns and rows."""
    cursor = connection.execute(sql, parameters)
    rows = cursor.fetchall()

    print("\nSQL:")
    print(sql.strip())

    print("Result:")
    if not rows:
        print("(no rows)")
        return

    column_names = [description[0] for description in cursor.description]
    print(" | ".join(column_names))
    print("-" * (len(" | ".join(column_names)) + 10))

    for row in rows:
        print(" | ".join("(NULL)" if value is None else str(value) for value in row))


def demonstrate_concatenation(connection: sqlite3.Connection) -> None:
    """
    CONCAT combines strings.

    SQLite's || operator is used here because SQLite does not expose CONCAT()
    as a built-in function. The example also demonstrates why separators
    should be added explicitly when building a display name.
    """
    print("\n=== CONCAT: Building a customer display name ===")

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            TRIM(first_name) || ' ' || TRIM(last_name) AS display_name
        FROM customers
        ORDER BY customer_id;
        """,
    )

    print("\nA NULL-safe CONCAT example:")
    print_rows(
        connection,
        """
        SELECT
            customer_id,
            TRIM(first_name) || ' ' ||
            TRIM(last_name) || ' <' ||
            LOWER(TRIM(email)) || '>' AS contact_label
        FROM customers
        ORDER BY customer_id;
        """,
    )


def demonstrate_substring(connection: sqlite3.Connection) -> None:
    """
    SUBSTRING extracts part of a string.

    SQLite uses substr(value, start, length). Positions are one-based in the
    SQL interface, matching common SQL substring conventions.
    """
    print("\n=== SUBSTRING: Extracting ticket identifiers ===")

    print_rows(
        connection,
        """
        SELECT
            ticket_id,
            subject,
            SUBSTR(message, 1, 24) AS message_preview
        FROM support_tickets
        ORDER BY ticket_id;
        """,
    )

    print("\nExtracting a known order-code fragment:")
    print_rows(
        connection,
        """
        SELECT
            ticket_id,
            SUBSTR(message, 44, 13) AS possible_order_code
        FROM support_tickets
        WHERE ticket_id = 1002;
        """,
    )


def demonstrate_position(connection: sqlite3.Connection) -> None:
    """
    POSITION finds where a substring occurs.

    SQLite uses instr(haystack, needle). A return value of zero means that the
    requested substring was not found.
    """
    print("\n=== POSITION: Locating characters and substrings ===")

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            email,
            INSTR(email, '@') AS at_position
        FROM customers
        ORDER BY customer_id;
        """,
    )

    print("\nFinding the first occurrence of a word in support messages:")
    print_rows(
        connection,
        """
        SELECT
            ticket_id,
            INSTR(LOWER(message), 'customer') AS customer_position
        FROM support_tickets
        ORDER BY ticket_id;
        """,
    )


def demonstrate_replace(connection: sqlite3.Connection) -> None:
    """
    REPLACE substitutes every occurrence of a literal substring.

    Literal replacement is useful when the transformation does not require
    pattern matching, such as normalizing phone-number separators.
    """
    print("\n=== REPLACE: Normalizing phone numbers ===")

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            phone,
            REPLACE(REPLACE(phone, '-', ''), ' ', '') AS normalized_phone
        FROM customers
        ORDER BY customer_id;
        """,
    )

    print("\nRedacting a known domain:")
    print_rows(
        connection,
        """
        SELECT
            customer_id,
            REPLACE(LOWER(TRIM(email)), '@example.com', '@company.test')
                AS redacted_domain
        FROM customers
        ORDER BY customer_id;
        """,
    )


def demonstrate_case_conversion(connection: sqlite3.Connection) -> None:
    """
    LOWER and UPPER are useful for case normalization.

    Case conversion is often applied before comparisons, grouping, or
    presentation. It should not be assumed to provide full Unicode
    case-folding semantics in every database engine.
    """
    print("\n=== LOWER and UPPER: Normalizing email and status ===")

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            LOWER(TRIM(email)) AS canonical_email,
            UPPER(status) AS canonical_status
        FROM customers
        ORDER BY customer_id;
        """,
    )

    print("\nCase-normalized filtering:")
    print_rows(
        connection,
        """
        SELECT customer_id, email
        FROM customers
        WHERE LOWER(TRIM(email)) = 'atul.pandey@example.com';
        """,
    )


def demonstrate_trim(connection: sqlite3.Connection) -> None:
    """
    TRIM removes leading and trailing whitespace.

    It does not automatically remove whitespace embedded between words, which
    is an important distinction when cleaning names and addresses.
    """
    print("\n=== TRIM: Cleaning imported customer fields ===")

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            '[' || first_name || ']' AS raw_name,
            '[' || TRIM(first_name) || ']' AS trimmed_name,
            '[' || email || ']' AS raw_email,
            '[' || TRIM(email) || ']' AS trimmed_email
        FROM customers
        ORDER BY customer_id;
        """,
    )

    print("\nRemoving a specific surrounding character:")
    print_rows(
        connection,
        """
        SELECT TRIM('---temporary-ticket---', '-') AS cleaned_ticket;
        """,
    )


def demonstrate_regular_expressions(connection: sqlite3.Connection) -> None:
    """
    Regular expressions handle pattern-oriented validation and transformation.

    The examples use a registered REGEXP predicate and REGEXP_REPLACE
    function. Exact regex syntax can vary between database engines.
    """
    print("\n=== Regular expressions: Validating and transforming text ===")

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            email,
            REGEXP(?, TRIM(email)) AS looks_like_email
        FROM customers
        ORDER BY customer_id;
        """,
        (email_pattern,),
    )

    print("\nRemoving non-digit characters from phone numbers:")
    print_rows(
        connection,
        """
        SELECT
            customer_id,
            phone,
            REGEXP_REPLACE(phone, '[^0-9]', '') AS digits_only
        FROM customers
        ORDER BY customer_id;
        """,
    )

    print("\nExtracting a ticket order-code pattern:")
    order_pattern = r"ORD-[0-9]{4}-[0-9]{4}"

    print_rows(
        connection,
        """
        SELECT
            ticket_id,
            message,
            REGEXP(?, message) AS contains_order_code
        FROM support_tickets
        ORDER BY ticket_id;
        """,
        (order_pattern,),
    )


def demonstrate_function_composition(connection: sqlite3.Connection) -> None:
    """
    SQL string functions become more useful when composed.

    This query creates a canonical customer record from messy input while
    keeping the transformation visible and deterministic.
    """
    print("\n=== Function composition: Creating canonical customer data ===")

    print_rows(
        connection,
        """
        SELECT
            customer_id,
            UPPER(
                SUBSTR(
                    TRIM(first_name),
                    1,
                    1
                )
            ) || LOWER(
                SUBSTR(
                    TRIM(first_name),
                    2
                )
            ) || ' ' ||
            UPPER(
                SUBSTR(
                    TRIM(last_name),
                    1,
                    1
                )
            ) || LOWER(
                SUBSTR(
                    TRIM(last_name),
                    2
                )
            ) AS normalized_name,
            LOWER(TRIM(email)) AS normalized_email,
            REPLACE(phone, '-', '') AS compact_phone
        FROM customers
        ORDER BY customer_id;
        """,
    )


def demonstrate_parameterized_pattern_search(
    connection: sqlite3.Connection,
) -> None:
    """
    Demonstrate safe dynamic filtering.

    Values are passed as SQL parameters instead of being interpolated into
    SQL text. This matters whenever patterns originate outside trusted code.
    """
    print("\n=== Parameterized pattern search ===")

    search_pattern = r"password|verification"

    print_rows(
        connection,
        """
        SELECT ticket_id, subject
        FROM support_tickets
        WHERE REGEXP(?, LOWER(subject || ' ' || message))
        ORDER BY ticket_id;
        """,
        (search_pattern,),
    )


def demonstrate_edge_cases(connection: sqlite3.Connection) -> None:
    """Show NULL behavior, missing substrings, and empty strings."""
    print("\n=== Edge cases and failure conditions ===")

    print_rows(
        connection,
        """
        SELECT
            INSTR('database', 'base') AS found_position,
            INSTR('database', 'xyz') AS missing_position,
            SUBSTR('database', 20, 5) AS beyond_end,
            TRIM('   ') AS trimmed_spaces,
            REPLACE('aaaa', 'aa', 'b') AS overlapping_behavior;
        """,
    )

    print("\nNULL propagation differs by function and database engine:")
    print_rows(
        connection,
        """
        SELECT
            TRIM(NULL) AS trimmed_null,
            LOWER(NULL) AS lower_null,
            REPLACE(NULL, 'a', 'b') AS replaced_null,
            SUBSTR(NULL, 1, 2) AS substring_null;
        """,
    )


def demonstrate_indexes_and_performance(connection: sqlite3.Connection) -> None:
    """
    Show an important production consideration.

    Applying a function to a column inside a WHERE predicate can prevent a
    normal index from being used, depending on the database engine and index
    definition. Canonicalized values are often better stored separately when
    they are queried frequently.
    """
    print("\n=== Performance consideration ===")

    connection.execute(
        "CREATE INDEX idx_customers_email ON customers(email)"
    )

    print_rows(
        connection,
        """
        EXPLAIN QUERY PLAN
        SELECT customer_id
        FROM customers
        WHERE email = 'ATUL.PANDEY@EXAMPLE.COM';
        """,
    )

    print_rows(
        connection,
        """
        EXPLAIN QUERY PLAN
        SELECT customer_id
        FROM customers
        WHERE LOWER(TRIM(email)) = 'atul.pandey@example.com';
        """,
    )

    print(
        "\nFor large production tables, consider a normalized column or a "
        "database-specific expression/function index when supported."
    )


def demonstrate_safe_regex_validation() -> None:
    """
    Demonstrate regex compilation before accepting a pattern.

    Regular expressions are powerful but user-controlled patterns can be
    expensive. Production systems should constrain pattern complexity and
    input size when patterns are externally supplied.
    """
    print("\n=== Regex validation outside SQL ===")

    candidates = [
        ("customer-1042", r"^customer-[0-9]{4}$"),
        ("customer-ABCD", r"^customer-[0-9]{4}$"),
    ]

    for value, pattern in candidates:
        try:
            compiled = re.compile(pattern)
            matched = compiled.fullmatch(value) is not None
            print(f"{value!r} -> {matched}")
        except re.error as exc:
            print(f"Rejected regex {pattern!r}: {exc}")


def run_sql_examples(connection: sqlite3.Connection) -> None:
    examples: Iterable[QueryExample] = [
        QueryExample(
            "CONCAT",
            "Build a readable customer name from separate columns.",
            "TRIM(first_name) || ' ' || TRIM(last_name)",
        ),
        QueryExample(
            "SUBSTRING",
            "Extract a bounded portion of a message.",
            "SUBSTR(message, 1, 24)",
        ),
        QueryExample(
            "POSITION",
            "Find the location of a substring.",
            "INSTR(email, '@')",
        ),
        QueryExample(
            "REPLACE",
            "Replace literal characters in a phone number.",
            "REPLACE(phone, '-', '')",
        ),
        QueryExample(
            "LOWER / UPPER",
            "Normalize case for comparison and presentation.",
            "LOWER(TRIM(email))",
        ),
        QueryExample(
            "TRIM",
            "Remove surrounding whitespace.",
            "TRIM(email)",
        ),
        QueryExample(
            "REGEXP",
            "Validate or locate text patterns.",
            "REGEXP(pattern, value)",
        ),
    ]

    print("SQL STRING FUNCTION REFERENCE")
    for example in examples:
        print(f"{example.name}: {example.description}")
        print(f"  SQLite expression: {example.sql}")


def main() -> None:
    connection = create_database()
    register_regex_functions(connection)

    try:
        run_sql_examples(connection)
        demonstrate_concatenation(connection)
        demonstrate_substring(connection)
        demonstrate_position(connection)
        demonstrate_replace(connection)
        demonstrate_case_conversion(connection)
        demonstrate_trim(connection)
        demonstrate_regular_expressions(connection)
        demonstrate_function_composition(connection)
        demonstrate_parameterized_pattern_search(connection)
        demonstrate_edge_cases(connection)
        demonstrate_indexes_and_performance(connection)
        demonstrate_safe_regex_validation()

        print("\n=== Production-oriented validation example ===")
        email_pattern = re.compile(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )

        raw_email = "  analyst@example.com  "
        canonical_email = raw_email.strip().lower()

        if email_pattern.fullmatch(canonical_email):
            print(f"Accepted canonical email: {canonical_email}")
        else:
            print("Rejected invalid email address.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
