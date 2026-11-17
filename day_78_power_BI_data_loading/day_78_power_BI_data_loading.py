#!/usr/bin/env python3
"""
POWER BI DATA LOADING
Excel, CSV, databases, web sources, data connections, and import modes.

A self-contained data-loading simulation using Python's standard library.
Supports CSV, XLSX, SQLite, JSON, and HTTP-based JSON sources.
Demonstrates Import, DirectQuery-style, and Live Connection behavior.
"""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
import statistics
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("powerbi_loader")


# ---------------------------------------------------------
# Domain types
# ---------------------------------------------------------

class SourceType(Enum):
    CSV = "csv"
    EXCEL = "excel"
    SQLITE = "sqlite"
    JSON = "json"
    WEB = "web"


class StorageMode(Enum):
    IMPORT = "import"
    DIRECT_QUERY = "directquery"
    LIVE_CONNECTION = "live_connection"


class LoadStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class DataLoadError(Exception):
    pass


class ValidationError(DataLoadError):
    pass


class ConnectionError(DataLoadError):
    pass


@dataclass
class DataConnection:
    connection_id: str
    source_type: SourceType
    location: str
    enabled: bool = True
    timeout_seconds: int = 15
    options: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.connection_id.strip():
            raise ValidationError("Connection ID cannot be empty.")

        if not self.location.strip():
            raise ValidationError("Source location cannot be empty.")

        if self.timeout_seconds <= 0:
            raise ValidationError("Timeout must be positive.")


@dataclass
class LoadResult:
    connection_id: str
    status: LoadStatus
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    error: Optional[str] = None
    loaded_at: Optional[str] = None


@dataclass
class RefreshRecord:
    connection_id: str
    storage_mode: StorageMode
    row_count: int
    status: LoadStatus
    timestamp: str


# ---------------------------------------------------------
# Data validation
# ---------------------------------------------------------

class DataValidator:

    REQUIRED_COLUMNS = {"product", "quantity", "revenue"}

    @staticmethod
    def normalize_column(name: str) -> str:
        return name.strip().lower().replace(" ", "_")

    @classmethod
    def normalize_rows(
        cls,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        normalized = []

        for row in rows:
            normalized_row = {
                cls.normalize_column(str(key)): value
                for key, value in row.items()
            }

            normalized.append(normalized_row)

        return normalized

    @classmethod
    def validate_sales(
        cls,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        normalized = cls.normalize_rows(rows)

        if not normalized:
            raise ValidationError("Source contains no records.")

        available = set(normalized[0].keys())
        missing = cls.REQUIRED_COLUMNS - available

        if missing:
            raise ValidationError(
                f"Missing required columns: {sorted(missing)}"
            )

        valid_rows = []

        for index, row in enumerate(normalized, start=1):

            try:
                product = str(row["product"]).strip()

                if not product:
                    raise ValueError("Product cannot be empty.")

                quantity = int(row["quantity"])
                revenue = float(row["revenue"])

                if quantity < 0:
                    raise ValueError("Quantity cannot be negative.")

                if revenue < 0:
                    raise ValueError("Revenue cannot be negative.")

                if not all(
                    map(
                        lambda value: value == value
                        and abs(value) != float("inf"),
                        [revenue],
                    )
                ):
                    raise ValueError("Revenue must be finite.")

                cleaned = dict(row)
                cleaned["product"] = product
                cleaned["quantity"] = quantity
                cleaned["revenue"] = round(revenue, 2)

                valid_rows.append(cleaned)

            except (ValueError, TypeError, KeyError) as exc:
                logger.warning(
                    "Rejected source row %d: %s",
                    index,
                    exc,
                )

        if not valid_rows:
            raise ValidationError("No valid records remain.")

        return valid_rows


# ---------------------------------------------------------
# Excel XLSX reader using ZIP and XML
# ---------------------------------------------------------

class ExcelReader:

    MAIN_NS = (
        "http://schemas.openxmlformats.org/"
        "spreadsheetml/2006/main"
    )

    REL_NS = (
        "http://schemas.openxmlformats.org/"
        "officeDocument/2006/relationships"
    )

    PKG_NS = (
        "http://schemas.openxmlformats.org/"
        "package/2006/relationships"
    )

    @classmethod
    def read(cls, file_path: Path) -> list[dict[str, Any]]:

        try:
            with zipfile.ZipFile(file_path) as archive:

                workbook = ET.fromstring(
                    archive.read("xl/workbook.xml")
                )

                relationships = ET.fromstring(
                    archive.read("xl/_rels/workbook.xml.rels")
                )

                relation_map = {
                    rel.attrib["Id"]: rel.attrib["Target"]
                    for rel in relationships
                }

                sheets = workbook.find(
                    f"{{{cls.MAIN_NS}}}sheets"
                )

                if sheets is None or not list(sheets):
                    raise DataLoadError("Workbook contains no sheets.")

                sheet = list(sheets)[0]

                relationship_id = sheet.attrib[
                    f"{{{cls.REL_NS}}}id"
                ]

                target = relation_map[relationship_id]

                if target.startswith("/"):
                    sheet_path = target.lstrip("/")
                elif target.startswith("xl/"):
                    sheet_path = target
                else:
                    sheet_path = "xl/" + target

                sheet_xml = ET.fromstring(
                    archive.read(sheet_path)
                )

                shared_strings = []

                if "xl/sharedStrings.xml" in archive.namelist():

                    shared_xml = ET.fromstring(
                        archive.read("xl/sharedStrings.xml")
                    )

                    for item in shared_xml.findall(
                        f"{{{cls.MAIN_NS}}}si"
                    ):
                        shared_strings.append(
                            "".join(
                                node.text or ""
                                for node in item.iter(
                                    f"{{{cls.MAIN_NS}}}t"
                                )
                            )
                        )

                raw_rows = []

                sheet_data = sheet_xml.find(
                    f"{{{cls.MAIN_NS}}}sheetData"
                )

                if sheet_data is None:
                    raise DataLoadError("Worksheet has no data.")

                for row in sheet_data:

                    values = {}

                    for cell in row:

                        reference = cell.attrib.get("r", "")
                        column = "".join(
                            char for char in reference
                            if char.isalpha()
                        )

                        if not column:
                            continue

                        value_element = cell.find(
                            f"{{{cls.MAIN_NS}}}v"
                        )

                        if value_element is None:
                            value = ""

                        else:
                            value = value_element.text or ""
                            cell_type = cell.attrib.get("t")

                            if cell_type == "s":
                                value = shared_strings[int(value)]

                            elif cell_type == "inlineStr":
                                inline = cell.find(
                                    f"{{{cls.MAIN_NS}}}is"
                                )
                                value = "".join(
                                    node.text or ""
                                    for node in inline.iter(
                                        f"{{{cls.MAIN_NS}}}t"
                                    )
                                ) if inline is not None else ""

                        values[column] = value

                    raw_rows.append(values)

                if len(raw_rows) < 2:
                    raise DataLoadError(
                        "Worksheet needs a header and at least one record."
                    )

                headers = [
                    raw_rows[0].get(column, "")
                    for column in sorted(
                        raw_rows[0],
                        key=lambda value: (
                            sum(
                                (ord(char) - 64)
                                * (26 ** index)
                                for index, char in enumerate(
                                    reversed(value)
                                )
                            )
                        ),
                    )
                ]

                result = []

                for row in raw_rows[1:]:
                    ordered_values = [
                        row.get(column, "")
                        for column in sorted(
                            raw_rows[0],
                            key=lambda value: (
                                sum(
                                    (ord(char) - 64)
                                    * (26 ** index)
                                    for index, char in enumerate(
                                        reversed(value)
                                    )
                                )
                            ),
                        )
                    ]

                    result.append(
                        dict(zip(headers, ordered_values))
                    )

                return result

        except (KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
            raise DataLoadError(
                f"Excel reading failed: {exc}"
            ) from exc


# ---------------------------------------------------------
# Source connectors
# ---------------------------------------------------------

class SourceConnector:

    def load(
        self,
        connection: DataConnection,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class CSVConnector(SourceConnector):

    def load(self, connection):

        path = Path(connection.location)

        if not path.is_file():
            raise ConnectionError(f"CSV file not found: {path}")

        encoding = connection.options.get("encoding", "utf-8-sig")
        delimiter = connection.options.get("delimiter", ",")

        with path.open(
            "r",
            encoding=encoding,
            newline="",
        ) as file:

            return list(
                csv.DictReader(file, delimiter=delimiter)
            )


class ExcelConnector(SourceConnector):

    def load(self, connection):

        path = Path(connection.location)

        if not path.is_file():
            raise ConnectionError("Excel workbook not found.")

        return ExcelReader.read(path)


class SQLiteConnector(SourceConnector):

    def load(self, connection):

        path = Path(connection.location)

        if not path.is_file():
            raise ConnectionError("SQLite database not found.")

        query = connection.options.get(
            "query",
            "SELECT product, quantity, revenue FROM sales",
        )

        # Restrict the example to read-only SELECT queries.
        if not query.strip().lower().startswith("select"):
            raise ValidationError(
                "Only SELECT statements are permitted."
            )

        uri = path.resolve().as_uri() + "?mode=ro"

        with sqlite3.connect(uri, uri=True) as database:

            database.row_factory = sqlite3.Row

            cursor = database.execute(query)

            return [
                dict(row)
                for row in cursor.fetchall()
            ]


class JSONConnector(SourceConnector):

    def load(self, connection):

        path = Path(connection.location)

        if not path.is_file():
            raise ConnectionError("JSON file not found.")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            data = data.get("data", [])

        if not isinstance(data, list):
            raise ValidationError(
                "JSON must contain an array of records."
            )

        if not all(isinstance(row, dict) for row in data):
            raise ValidationError(
                "Every JSON record must be an object."
            )

        return data


class WebConnector(SourceConnector):

    def load(self, connection):

        from urllib.parse import urlparse

        parsed = urlparse(connection.location)

        if parsed.scheme != "https":
            raise ValidationError(
                "Web connections must use HTTPS."
            )

        if not parsed.hostname:
            raise ValidationError("Invalid web URL.")

        request = urllib.request.Request(
            connection.location,
            headers={
                "Accept": "application/json",
                "User-Agent": "PowerBI-DataLoader/1.0",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=connection.timeout_seconds,
            ) as response:

                if response.status != 200:
                    raise ConnectionError(
                        f"HTTP status: {response.status}"
                    )

                if len(response.headers.get("Content-Length", "0")) > 10:
                    raise ConnectionError(
                        "Response size metadata is invalid."
                    )

                content_type = response.headers.get(
                    "Content-Type", ""
                )

                if "json" not in content_type.lower():
                    raise ValidationError(
                        "Web source must return JSON."
                    )

                raw = response.read(
                    connection.options.get(
                        "max_response_bytes",
                        2_000_000,
                    ) + 1
                )

                if len(raw) > connection.options.get(
                    "max_response_bytes",
                    2_000_000,
                ):
                    raise ConnectionError(
                        "Web response exceeds configured size."
                    )

                data = json.loads(raw.decode("utf-8"))

                if isinstance(data, dict):
                    data = data.get("data", [])

                if not isinstance(data, list):
                    raise ValidationError(
                        "Web response must contain an array."
                    )

                return data

        except (
            urllib.error.URLError,
            TimeoutError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ConnectionError(
                f"Web request failed: {exc}"
            ) from exc


# ---------------------------------------------------------
# Connection manager
# ---------------------------------------------------------

class ConnectionManager:

    def __init__(self):

        self.connectors = {
            SourceType.CSV: CSVConnector(),
            SourceType.EXCEL: ExcelConnector(),
            SourceType.SQLITE: SQLiteConnector(),
            SourceType.JSON: JSONConnector(),
            SourceType.WEB: WebConnector(),
        }

        self.connections: dict[str, DataConnection] = {}

    def register(self, connection: DataConnection):

        connection.validate()

        if connection.connection_id in self.connections:
            raise ValidationError(
                "Connection ID already exists."
            )

        self.connections[connection.connection_id] = connection

    def load(self, connection_id: str) -> LoadResult:

        connection = self.connections.get(connection_id)

        if connection is None:
            raise ConnectionError("Unknown connection.")

        if not connection.enabled:
            raise ConnectionError("Connection is disabled.")

        try:
            rows = self.connectors[
                connection.source_type
            ].load(connection)

            valid_rows = DataValidator.validate_sales(rows)

            return LoadResult(
                connection_id=connection_id,
                status=LoadStatus.SUCCESS,
                rows=valid_rows,
                row_count=len(valid_rows),
                loaded_at=datetime.now(
                    timezone.utc
                ).isoformat(),
            )

        except DataLoadError as exc:

            return LoadResult(
                connection_id=connection_id,
                status=LoadStatus.FAILED,
                error=str(exc),
            )

        except Exception as exc:

            logger.exception("Unexpected loading failure.")

            return LoadResult(
                connection_id=connection_id,
                status=LoadStatus.FAILED,
                error=str(exc),
            )


# ---------------------------------------------------------
# Storage modes
# ---------------------------------------------------------

class SemanticModel:

    def __init__(self):

        self.imported_tables = {}
        self.refresh_history = []

    def import_data(
        self,
        table_name: str,
        result: LoadResult,
    ) -> None:

        if result.status != LoadStatus.SUCCESS:
            raise DataLoadError("Cannot import failed data.")

        if not table_name.isidentifier():
            raise ValidationError("Invalid table name.")

        # Replace the table only after a successful load.
        self.imported_tables[table_name] = [
            dict(row) for row in result.rows
        ]

        self.refresh_history.append(
            RefreshRecord(
                connection_id=result.connection_id,
                storage_mode=StorageMode.IMPORT,
                row_count=result.row_count,
                status=LoadStatus.SUCCESS,
                timestamp=result.loaded_at or "",
            )
        )

    def direct_query(
        self,
        connection: DataConnection,
        manager: ConnectionManager,
    ) -> list[dict[str, Any]]:

        if connection.source_type == SourceType.WEB:
            raise ValidationError(
                "This demonstration does not support "
                "DirectQuery against web sources."
            )

        # The source is queried again instead of using cached
        # imported rows. This is a DirectQuery-style simulation.
        result = manager.load(connection.connection_id)

        if result.status != LoadStatus.SUCCESS:
            raise DataLoadError(result.error or "Query failed.")

        return result.rows

    def live_connection(self, external_model):
        if external_model is None:
            raise ConnectionError(
                "External semantic model is unavailable."
            )

        return external_model


# ---------------------------------------------------------
# Reporting layer
# ---------------------------------------------------------

class SalesAnalytics:

    @staticmethod
    def summarize(
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not rows:
            raise ValidationError("No records to summarize.")

        total_revenue = sum(
            row["revenue"] for row in rows
        )

        total_quantity = sum(
            row["quantity"] for row in rows
        )

        product_revenue = Counter()

        for row in rows:
            product_revenue[row["product"]] += row["revenue"]

        revenues = [
            row["revenue"] for row in rows
        ]

        return {
            "record_count": len(rows),
            "total_quantity": total_quantity,
            "total_revenue": round(total_revenue, 2),
            "average_revenue": round(
                statistics.mean(revenues), 2
            ),
            "highest_revenue": round(max(revenues), 2),
            "product_revenue": dict(product_revenue),
        }


# ---------------------------------------------------------
# Demonstration data
# ---------------------------------------------------------

def create_demo_files(directory: Path):

    directory.mkdir(parents=True, exist_ok=True)

    csv_path = directory / "sales.csv"

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "product",
                "quantity",
                "revenue",
            ],
        )

        writer.writeheader()

        writer.writerows([
            {
                "product": "Laptop",
                "quantity": 5,
                "revenue": 250000,
            },
            {
                "product": "Monitor",
                "quantity": 8,
                "revenue": 120000,
            },
            {
                "product": "Keyboard",
                "quantity": 20,
                "revenue": 40000,
            },
            {
                "product": "Mouse",
                "quantity": -2,
                "revenue": 10000,
            },
        ])

    json_path = directory / "sales.json"

    json_path.write_text(
        json.dumps({
            "data": [
                {
                    "product": "Tablet",
                    "quantity": 4,
                    "revenue": 80000,
                },
                {
                    "product": "Phone",
                    "quantity": 10,
                    "revenue": 200000,
                },
            ]
        }, indent=2),
        encoding="utf-8",
    )

    database_path = directory / "sales.db"

    with sqlite3.connect(database_path) as database:

        database.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                product TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                revenue REAL NOT NULL
            )
        """)

        database.execute("DELETE FROM sales")

        database.executemany(
            "INSERT INTO sales VALUES (?, ?, ?)",
            [
                ("Desktop", 3, 180000),
                ("Printer", 2, 30000),
            ],
        )

    return csv_path, json_path, database_path


# ---------------------------------------------------------
# Application
# ---------------------------------------------------------

def main():

    directory = Path("powerbi_data_loading_demo")

    csv_path, json_path, database_path = (
        create_demo_files(directory)
    )

    manager = ConnectionManager()

    connections = [
        DataConnection(
            "sales_csv",
            SourceType.CSV,
            str(csv_path),
        ),
        DataConnection(
            "sales_json",
            SourceType.JSON,
            str(json_path),
        ),
        DataConnection(
            "sales_database",
            SourceType.SQLITE,
            str(database_path),
        ),
    ]

    for connection in connections:
        manager.register(connection)

    semantic_model = SemanticModel()

    combined_rows = []

    print("\nPOWER BI DATA LOADING DEMONSTRATION")
    print("=" * 55)

    for connection in connections:

        result = manager.load(connection.connection_id)

        print(
            f"\nSource: {connection.connection_id}"
            f"\nStatus: {result.status.value}"
            f"\nRecords: {result.row_count}"
        )

        if result.error:
            print("Error:", result.error)
            continue

        semantic_model.import_data(
            connection.connection_id,
            result,
        )

        combined_rows.extend(result.rows)

    print("\nIMPORT MODE")
    print("Imported tables:", list(
        semantic_model.imported_tables
    ))

    print("\nDIRECTQUERY-STYLE MODE")

    direct_rows = semantic_model.direct_query(
        connections[0],
        manager,
    )

    print("Fresh source records:", len(direct_rows))

    print("\nLIVE CONNECTION MODE")

    external_model = {
        "model_name": "EnterpriseSalesModel",
        "owner": "Central Analytics",
    }

    print(
        semantic_model.live_connection(
            external_model
        )
    )

    print("\nCOMBINED DATA REPORT")
    print("=" * 55)

    report = SalesAnalytics.summarize(combined_rows)

    print(json.dumps(report, indent=4))

    print("\nREFRESH HISTORY")

    for record in semantic_model.refresh_history:
        print(
            record.connection_id,
            record.storage_mode.value,
            record.row_count,
            record.status.value,
        )

    # Edge-case validation.
    try:
        DataValidator.validate_sales([])
    except ValidationError as exc:
        print("\nExpected validation failure:", exc)

    print("\nExecution completed.")


if __name__ == "__main__":
    main()
