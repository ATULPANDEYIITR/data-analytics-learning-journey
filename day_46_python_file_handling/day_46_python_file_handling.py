#!/usr/bin/env python3
"""
Practical Python file handling: TXT, CSV, JSON, paths, encodings, and safe writes.

Run:
    python file_handling.py
    python file_handling.py --directory ./file_lab

The program uses only the Python standard library. It creates a demonstration
workspace, processes operational records, validates input, and demonstrates
reliable file operations without modifying files outside that workspace.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def print_heading(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def validate_relative_path(value: str) -> Path:
    """Reject absolute paths and traversal components for workspace operations."""
    candidate = Path(value)

    if candidate.is_absolute() or candidate.drive:
        raise ValueError("An absolute path is not allowed.")

    if any(part == ".." for part in candidate.parts):
        raise ValueError("Parent-directory traversal is not allowed.")

    if not candidate.parts:
        raise ValueError("A relative file path is required.")

    return candidate


def resolve_workspace_path(root: Path, relative_name: str) -> Path:
    """Resolve a path and verify that it remains within the workspace."""
    relative_path = validate_relative_path(relative_name)
    resolved_root = root.resolve()
    resolved_target = (resolved_root / relative_path).resolve()

    if not resolved_target.is_relative_to(resolved_root):
        raise ValueError("The resolved path escapes the workspace.")

    return resolved_target


def ensure_workspace(root: Path) -> Path:
    """Create a workspace directory and reject a non-directory root."""
    root = root.expanduser().resolve()

    if root.exists() and not root.is_dir():
        raise NotADirectoryError(f"Workspace is not a directory: {root}")

    root.mkdir(parents=True, exist_ok=True)
    return root


def read_text_file(path: Path, encoding: str = "utf-8") -> str:
    """Read text explicitly using an encoding and universal newline handling."""
    with path.open("r", encoding=encoding, newline=None) as file:
        return file.read()


def write_text_atomically(
    path: Path,
    content: str,
    encoding: str = "utf-8",
) -> None:
    """
    Write through a temporary file and replace the destination.

    The temporary file is created in the destination directory so replacement
    normally stays on the same filesystem. Atomic replacement does not by
    itself guarantee durability after a power failure.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())

        os.replace(temporary_name, path)
        temporary_name = None

    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def write_json_atomically(path: Path, value: Any) -> None:
    """Serialize structured data before atomically replacing the JSON file."""
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    write_text_atomically(path, serialized + "\n")


def read_json_file(path: Path) -> Any:
    """Load JSON and preserve a useful error location for malformed documents."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}, line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error


def write_csv_file(
    path: Path,
    fieldnames: list[str],
    records: Iterable[dict[str, Any]],
) -> None:
    """
    Write a UTF-8 CSV with a header and stable newline behavior.

    newline="" lets csv.writer manage record boundaries correctly across
    platforms. DictWriter rejects unexpected fields by default.
    """
    if not fieldnames or len(fieldnames) != len(set(fieldnames)):
        raise ValueError("CSV field names must be non-empty and unique.")

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()

        for record in records:
            writer.writerow(record)


def read_csv_file(path: Path) -> list[dict[str, str]]:
    """Read CSV rows as strings so conversion rules remain explicit."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")

        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"CSV contains duplicate column names: {path}")

        if any(name is None or not name.strip() for name in reader.fieldnames):
            raise ValueError(f"CSV contains a blank column name: {path}")

        records: list[dict[str, str]] = []

        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"CSV row {line_number} has more fields than its header."
                )

            if any(value is None for value in row.values()):
                raise ValueError(
                    f"CSV row {line_number} has fewer fields than its header."
                )

            records.append(dict(row))

        return records


def validate_incident(record: dict[str, str]) -> dict[str, Any]:
    """Convert a CSV incident row into a validated application record."""
    required = {"incident_id", "department", "severity", "description"}

    if not required.issubset(record):
        raise ValueError(f"Missing required fields: {required - record.keys()}")

    incident_id = record["incident_id"].strip()
    department = record["department"].strip()
    description = record["description"].strip()
    severity_text = record["severity"].strip()

    if not incident_id or len(incident_id) > 40:
        raise ValueError("incident_id must contain 1 to 40 characters.")

    if not department or len(department) > 80:
        raise ValueError("department must contain 1 to 80 characters.")

    if not description or len(description) > 1000:
        raise ValueError("description must contain 1 to 1000 characters.")

    try:
        severity = int(severity_text)
    except ValueError as error:
        raise ValueError("severity must be an integer from 1 through 5.") from error

    if severity not in range(1, 6):
        raise ValueError("severity must be an integer from 1 through 5.")

    return {
        "incident_id": incident_id,
        "department": department,
        "severity": severity,
        "description": description,
    }


def process_incident_csv(path: Path) -> dict[str, Any]:
    """Validate source rows and calculate a department-level severity report."""
    records = read_csv_file(path)
    incidents: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for row_number, record in enumerate(records, start=2):
        try:
            incident = validate_incident(record)

            if incident["incident_id"] in seen_ids:
                raise ValueError("Duplicate incident_id.")

            seen_ids.add(incident["incident_id"])
            incidents.append(incident)

        except ValueError as error:
            rejected.append({
                "row": str(row_number),
                "reason": str(error),
                "incident_id": record.get("incident_id", ""),
            })

    department_counts = Counter(
        incident["department"] for incident in incidents
    )

    severity_totals: dict[str, int] = {}
    for incident in incidents:
        department = incident["department"]
        severity_totals[department] = (
            severity_totals.get(department, 0) + incident["severity"]
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": path.name,
        "total_rows": len(records),
        "accepted_count": len(incidents),
        "rejected_count": len(rejected),
        "incidents": incidents,
        "rejected_rows": rejected,
        "department_summary": [
            {
                "department": department,
                "incident_count": count,
                "total_severity": severity_totals[department],
                "average_severity": round(
                    severity_totals[department] / count, 2
                ),
            }
            for department, count in sorted(department_counts.items())
        ],
    }


def demonstrate_text_files(root: Path) -> None:
    print_heading("Text files, encodings, and paths")

    notes_path = resolve_workspace_path(root, "input/operations_notes.txt")
    notes = (
        "Operations log\n"
        "Pump inspection completed at 09:30.\n"
        "Technician: José Kumar.\n"
        "Finding: temperature above normal range.\n"
    )

    write_text_atomically(notes_path, notes)
    print(f"Created: {notes_path.relative_to(root)}")
    print(read_text_file(notes_path))

    # UTF-8 preserves accented characters; ASCII cannot encode this text.
    try:
        notes.encode("ascii")
    except UnicodeEncodeError as error:
        print(f"Expected ASCII encoding failure: {error.reason}")

    lines = read_text_file(notes_path).splitlines()
    finding_lines = [line for line in lines if "Finding:" in line]
    print(f"Finding lines: {finding_lines}")

    # Path objects handle separators portably on Windows, Linux, and macOS.
    print(f"Suffix: {notes_path.suffix}")
    print(f"Parent directory: {notes_path.parent.name}")


def demonstrate_csv_files(root: Path) -> Path:
    print_heading("CSV records and validation")

    csv_path = resolve_workspace_path(root, "input/incidents.csv")
    fields = ["incident_id", "department", "severity", "description"]

    sample_rows = [
        {
            "incident_id": "INC-1001",
            "department": "Water Operations",
            "severity": "4",
            "description": "Pump temperature exceeded its operating threshold",
        },
        {
            "incident_id": "INC-1002",
            "department": "Power Operations",
            "severity": "5",
            "description": "Transformer inspection identified overheating",
        },
        {
            "incident_id": "INC-1003",
            "department": "Water Operations",
            "severity": "2",
            "description": "Minor pressure fluctuation recorded",
        },
        {
            "incident_id": "INC-1004",
            "department": "Power Operations",
            "severity": "9",
            "description": "Invalid severity demonstrates row rejection",
        },
        {
            "incident_id": "INC-1001",
            "department": "Water Operations",
            "severity": "3",
            "description": "Duplicate identifier demonstrates uniqueness validation",
        },
    ]

    write_csv_file(csv_path, fields, sample_rows)
    print(f"Created CSV with {len(sample_rows)} source rows.")

    report = process_incident_csv(csv_path)
    print(f"Accepted: {report['accepted_count']}")
    print(f"Rejected: {report['rejected_count']}")

    for department in report["department_summary"]:
        print(
            f"{department['department']}: "
            f"{department['incident_count']} incidents, "
            f"average severity {department['average_severity']}"
        )

    for rejected in report["rejected_rows"]:
        print(
            f"Rejected CSV row {rejected['row']}: "
            f"{rejected['reason']}"
        )

    return csv_path


def demonstrate_json_files(root: Path, csv_path: Path) -> None:
    print_heading("JSON serialization and report persistence")

    report = process_incident_csv(csv_path)
    json_path = resolve_workspace_path(root, "output/incident_report.json")

    write_json_atomically(json_path, report)
    loaded_report = read_json_file(json_path)

    assert loaded_report["accepted_count"] == report["accepted_count"]
    assert loaded_report["rejected_count"] == report["rejected_count"]

    print(f"Saved structured report: {json_path.relative_to(root)}")
    print(
        json.dumps(
            {
                "accepted_count": loaded_report["accepted_count"],
                "rejected_count": loaded_report["rejected_count"],
                "departments": len(loaded_report["department_summary"]),
            },
            indent=2,
        )
    )

    # JSON is a data format, not a Python object serializer. Custom types
    # such as datetime and Path need deliberate conversion before json.dump.
    malformed_path = resolve_workspace_path(root, "input/malformed.json")
    write_text_atomically(malformed_path, '{"status": "open",}')

    try:
        read_json_file(malformed_path)
    except ValueError as error:
        print(f"Malformed JSON handled correctly: {error}")


def demonstrate_append_and_streaming(root: Path) -> None:
    print_heading("Appending logs and streaming large files")

    log_path = resolve_workspace_path(root, "output/audit.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Append mode retains earlier records. Use a controlled record format
    # rather than treating untrusted text as a command or file path.
    with log_path.open("a", encoding="utf-8", newline="\n") as file:
        file.write("event=report_generated actor=operations_service\n")
        file.write("event=validation_completed actor=operations_service\n")

    event_count = 0

    # Iterating over the file avoids loading a potentially large log entirely
    # into memory, giving O(1) auxiliary memory for this count.
    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("event="):
                event_count += 1

    print(f"Audit events found: {event_count}")


def demonstrate_path_security(root: Path) -> None:
    print_heading("Path validation and file-system safety")

    for candidate in ("../outside.txt", "/etc/passwd", "reports/summary.txt"):
        try:
            resolved = resolve_workspace_path(root, candidate)
            print(f"Accepted relative path: {resolved.relative_to(root)}")
        except ValueError as error:
            print(f"Rejected {candidate!r}: {error}")

    link_path = resolve_workspace_path(root, "input/external_link.txt")

    # Resolving symlinks prevents many accidental escapes, but a separate
    # check followed by an open is vulnerable to races if an attacker can
    # concurrently alter directories. Use trusted directories and OS-level
    # permissions for security-sensitive applications.
    if link_path.is_symlink():
        print("External link already exists; refusing to use it.")


def demonstrate_edge_cases(root: Path) -> None:
    print_heading("Missing files, empty files, and binary data")

    missing_path = resolve_workspace_path(root, "input/not_created.txt")

    try:
        read_text_file(missing_path)
    except FileNotFoundError:
        print("Missing file detected without terminating the program.")

    empty_path = resolve_workspace_path(root, "input/empty.txt")
    write_text_atomically(empty_path, "")
    print(f"Empty file length: {len(read_text_file(empty_path))}")

    binary_path = resolve_workspace_path(root, "input/sample.bin")
    with binary_path.open("wb") as file:
        file.write(bytes([0, 1, 127, 128, 255]))

    with binary_path.open("rb") as file:
        binary_content = file.read()

    print(f"Binary byte count: {len(binary_content)}")
    print(f"Binary values: {list(binary_content)}")


def run_self_tests(root: Path) -> None:
    print_heading("Executable assertions")

    assert validate_relative_path("reports/result.json") == Path(
        "reports/result.json"
    )

    for invalid_path in ("../secret.txt", "/tmp/secret.txt"):
        try:
            validate_relative_path(invalid_path)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Unsafe path was accepted: {invalid_path}")

    valid = validate_incident({
        "incident_id": "INC-TEST",
        "department": "Testing",
        "severity": "1",
        "description": "A valid test incident",
    })
    assert valid["severity"] == 1

    try:
        validate_incident({
            "incident_id": "INC-BAD",
            "department": "Testing",
            "severity": "0",
            "description": "Severity outside allowed range",
        })
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid severity was accepted.")

    test_json = resolve_workspace_path(root, "output/test.json")
    write_json_atomically(test_json, {"unicode": "café", "valid": True})
    assert read_json_file(test_json)["unicode"] == "café"

    print("All assertions passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstrate practical Python file handling."
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("file_handling_workspace"),
        help="Workspace directory created or reused by the demonstration.",
    )
    args = parser.parse_args()

    try:
        root = ensure_workspace(args.directory)
        print(f"Workspace: {root}")

        demonstrate_text_files(root)
        csv_path = demonstrate_csv_files(root)
        demonstrate_json_files(root, csv_path)
        demonstrate_append_and_streaming(root)
        demonstrate_path_security(root)
        demonstrate_edge_cases(root)
        run_self_tests(root)

        print_heading("Generated workspace")
        for path in sorted(root.rglob("*")):
            if path.is_file():
                print(f"{path.relative_to(root)} ({path.stat().st_size} bytes)")

    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as error:
        raise SystemExit(f"File handling failed: {error}") from error


if __name__ == "__main__":
    main()
