"""
DATA ANALYTICS ECOSYSTEM
========================

Topic:
Data sources, databases, warehouses, data lakes, APIs, spreadsheets,
business applications, transactional vs analytical systems, and
structured/semi-structured/unstructured data.

Purpose:
This script is an executable study module. It explains the data analytics
ecosystem from basic concepts to advanced architecture and includes examples,
comparisons, small simulations, data classification exercises, and practical
case studies.

Requirements:
    Python 3.x

External libraries:
    None

The script can be run directly:

    python data_analytics_ecosystem.py

It prints the learning material to the terminal and creates:

    data_analytics_ecosystem_notes.md

The generated Markdown file contains the same core learning material in a
structured study-note format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from datetime import datetime
import json
import csv
import io
import textwrap


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

WIDTH = 92


def line(char: str = "=", width: int = WIDTH) -> None:
    print(char * width)


def title(text: str) -> None:
    print()
    line("=")
    print(text.center(WIDTH))
    line("=")


def section(number: str, text: str) -> None:
    print()
    line("-")
    print(f"{number}. {text}")
    line("-")


def subsection(text: str) -> None:
    print()
    print(f"\n{text}")
    print("." * len(text))


def explain(text: str) -> None:
    print(textwrap.fill(text, WIDTH))


def bullet(text: str, level: int = 0) -> None:
    prefix = "  " * level + "- "
    print(textwrap.fill(text, WIDTH, initial_indent=prefix,
                        subsequent_indent="  " * level + "  "))


def numbered(number: int, text: str) -> None:
    prefix = f"{number}. "
    print(textwrap.fill(text, WIDTH, initial_indent=prefix,
                        subsequent_indent=" " * len(prefix)))


def code_block(code: str) -> None:
    print()
    print(code.strip())
    print()


def show_table(headers: List[str], rows: List[List[Any]]) -> None:
    """
    Simple dependency-free table renderer.
    """
    rows_as_strings = [[str(x) for x in row] for row in rows]
    widths = []

    for i, header in enumerate(headers):
        values = [header]
        values.extend(row[i] for row in rows_as_strings)
        widths.append(min(max(len(v) for v in values), 32))

    def trim(value: str, width: int) -> str:
        if len(value) <= width:
            return value
        return value[:width - 3] + "..."

    separator = "+".join("-" * (w + 2) for w in widths)

    print(separator)
    print("| " + " | ".join(
        trim(headers[i], widths[i]).ljust(widths[i])
        for i in range(len(headers))
    ) + " |")
    print(separator)

    for row in rows_as_strings:
        print("| " + " | ".join(
            trim(row[i], widths[i]).ljust(widths[i])
            for i in range(len(headers))
        ) + " |")

    print(separator)


# ============================================================================
# MARKDOWN DOCUMENT GENERATION
# ============================================================================

markdown_sections: List[str] = []


def md_heading(level: int, text: str) -> None:
    markdown_sections.append("#" * level + " " + text + "\n")


def md_text(text: str) -> None:
    markdown_sections.append(text.strip() + "\n")


def md_bullet(text: str, level: int = 0) -> None:
    markdown_sections.append("  " * level + "- " + text + "\n")


def md_numbered(number: int, text: str) -> None:
    markdown_sections.append(f"{number}. {text}\n")


def md_code(code: str, language: str = "") -> None:
    markdown_sections.append(
        f"```{language}\n{code.strip()}\n```\n"
    )


def md_table(headers: List[str], rows: List[List[Any]]) -> None:
    markdown_sections.append(
        "| " + " | ".join(headers) + " |\n"
    )
    markdown_sections.append(
        "| " + " | ".join("---" for _ in headers) + " |\n"
    )

    for row in rows:
        markdown_sections.append(
            "| " + " | ".join(str(x) for x in row) + " |\n"
        )

    markdown_sections.append("\n")


# ============================================================================
# DATA MODELS USED IN THE LESSON
# ============================================================================

@dataclass
class DataSource:
    name: str
    category: str
    format: str
    frequency: str
    typical_use: str


@dataclass
class DataSystem:
    name: str
    system_type: str
    workload: str
    storage_model: str
    typical_users: str


@dataclass
class DataLayer:
    name: str
    purpose: str
    examples: List[str] = field(default_factory=list)


# ============================================================================
# 1. INTRODUCTION
# ============================================================================

def lesson_1_introduction() -> None:
    title("DATA ANALYTICS ECOSYSTEM")

    section("1", "What Is a Data Analytics Ecosystem?")

    explain(
        "A data analytics ecosystem is the complete environment through which "
        "data is generated, captured, transported, stored, transformed, "
        "governed, analyzed, visualized, and used for decision-making. It is "
        "not a single database or analytics tool. It is a connected collection "
        "of operational systems, data sources, storage technologies, processing "
        "systems, analytical platforms, applications, people, and governance "
        "mechanisms."
    )

    explain(
        "For example, an online retail company may generate customer data in "
        "its website, order data in an order-management system, payment data "
        "through a payment service, marketing data through an advertising "
        "platform, employee data in an HR system, and financial data in an ERP. "
        "Those sources may feed databases, APIs, files, a data warehouse, or a "
        "data lake. Analysts then use SQL, spreadsheets, dashboards, notebooks, "
        "or business intelligence tools to answer business questions."
    )

    subsection("The basic movement of data")

    code_block("""
Business activity
       |
       v
+----------------------+
| Operational systems  |
| ERP / CRM / Website  |
| POS / HR / Payments  |
+----------------------+
       |
       v
+----------------------+
| Data ingestion       |
| APIs / Files / ETL   |
| ELT / Streaming      |
+----------------------+
       |
       v
+----------------------+       +----------------------+
| Operational database |       | Data lake            |
| OLTP                 |       | Raw / varied data    |
+----------------------+       +----------------------+
       |                               |
       +---------------+---------------+
                       |
                       v
              +----------------+
              | Data warehouse |
              | Curated data   |
              +----------------+
                       |
                       v
              +----------------+
              | Analytics      |
              | SQL / BI / ML  |
              +----------------+
                       |
                       v
                Business decisions
""")

    md_heading(1, "Data Analytics Ecosystem")
    md_heading(2, "What Is a Data Analytics Ecosystem?")
    md_text(
        "A data analytics ecosystem is the complete environment through which "
        "data is generated, captured, transported, stored, transformed, "
        "governed, analyzed, visualized, and used for decision-making. It is "
        "not a single database or analytics tool. It consists of connected "
        "operational systems, data sources, storage technologies, processing "
        "systems, analytical platforms, applications, people, and governance "
        "mechanisms."
    )

    md_heading(2, "Basic Movement of Data")
    md_code("""
Business activity
       |
       v
Operational systems
       |
       v
Data ingestion
       |
       +-------------------+
       |                   |
       v                   v
Operational database    Data lake
       |                   |
       +---------+---------+
                 |
                 v
          Data warehouse
                 |
                 v
             Analytics
                 |
                 v
        Business decisions
""")


# ============================================================================
# 2. DATA SOURCES
# ============================================================================

def lesson_2_data_sources() -> None:
    section("2", "Data Sources")

    explain(
        "A data source is any origin from which data can be obtained. The "
        "source may be an application database, an API, a spreadsheet, a "
        "business system, a log file, a sensor, a third-party platform, or "
        "even manually entered information."
    )

    subsection("Common data source categories")

    sources = [
        DataSource("Website", "Application", "JSON/database/events",
                   "Real time or near real time", "Web behavior"),
        DataSource("Mobile application", "Application", "JSON/events",
                   "Real time", "User activity"),
        DataSource("CRM", "Business application", "Database/API",
                   "Continuous", "Customers and sales"),
        DataSource("ERP", "Business application", "Database/API",
                   "Continuous", "Finance and operations"),
        DataSource("Spreadsheet", "File", "XLSX/CSV",
                   "Manual/periodic", "Small operational analysis"),
        DataSource("Payment gateway", "External service", "API/webhook",
                   "Real time", "Payments"),
        DataSource("Server logs", "Machine-generated", "Text/JSON",
                   "Continuous", "Technical monitoring"),
        DataSource("IoT sensor", "Machine-generated", "Events",
                   "Streaming", "Physical measurements"),
        DataSource("Social platform", "External platform", "API",
                   "Periodic/streaming", "Engagement"),
        DataSource("Document repository", "File", "PDF/DOCX",
                   "Periodic", "Unstructured information"),
    ]

    show_table(
        ["Source", "Category", "Format", "Frequency", "Typical use"],
        [[
            s.name, s.category, s.format, s.frequency, s.typical_use
        ] for s in sources]
    )

    md_heading(1, "Data Sources")
    md_text(
        "A data source is any origin from which data can be obtained. It may "
        "be an application database, API, spreadsheet, business system, log "
        "file, sensor, third-party platform, or manually entered information."
    )

    md_heading(2, "Common Data Sources")
    md_table(
        ["Source", "Category", "Format", "Frequency", "Typical Use"],
        [[s.name, s.category, s.format, s.frequency, s.typical_use]
         for s in sources]
    )

    subsection("Internal and external sources")

    bullet(
        "Internal sources are generated within an organization's own systems. "
        "Examples include ERP, CRM, HR, finance, inventory, and application databases."
    )
    bullet(
        "External sources originate outside the organization. Examples include "
        "government datasets, market data providers, partner APIs, social platforms, "
        "payment providers, and third-party research datasets."
    )

    md_heading(2, "Internal and External Sources")
    md_bullet(
        "Internal sources are generated within an organization's own systems, "
        "such as ERP, CRM, HR, finance, inventory, and application databases."
    )
    md_bullet(
        "External sources originate outside the organization, such as government "
        "datasets, partner APIs, payment providers, social platforms, and third-party datasets."
    )


# ============================================================================
# 3. STRUCTURED, SEMI-STRUCTURED, UNSTRUCTURED
# ============================================================================

def lesson_3_data_types() -> None:
    section("3", "Structured, Semi-Structured, and Unstructured Data")

    explain(
        "The structure of data determines how easily it can be represented, "
        "queried, validated, indexed, transformed, and analyzed. The traditional "
        "classification is structured, semi-structured, and unstructured data."
    )

    subsection("Structured data")

    explain(
        "Structured data follows a predefined schema. It is commonly organized "
        "into tables containing rows and columns. Each column normally has a "
        "defined meaning and data type."
    )

    code_block("""
customer_id | name        | age | city
------------+-------------+-----+---------
101         | Ravi        | 31  | Lucknow
102         | Neha        | 28  | Delhi
103         | Arjun       | 35  | Mumbai
""")

    bullet("Relational database tables are a classic example.")
    bullet("CSV files with consistent columns can be structured.")
    bullet("Financial transaction records are often structured.")
    bullet("Structured data is well suited to SQL.")

    subsection("Semi-structured data")

    explain(
        "Semi-structured data does not necessarily follow one rigid relational "
        "table structure, but it contains tags, keys, metadata, nesting, or "
        "other organizational information. JSON and XML are common examples."
    )

    code_block("""
{
    "customer_id": 101,
    "name": "Ravi",
    "address": {
        "city": "Lucknow",
        "country": "India"
    },
    "orders": [
        {"order_id": 5001, "amount": 1200},
        {"order_id": 5002, "amount": 850}
    ]
}
""")

    subsection("Unstructured data")

    explain(
        "Unstructured data does not naturally conform to a fixed tabular schema. "
        "Examples include text documents, images, audio, video, scanned documents, "
        "and many types of free-form content."
    )

    bullet("PDF documents")
    bullet("Images")
    bullet("Audio recordings")
    bullet("Videos")
    bullet("Emails and free-form text")
    bullet("Scanned documents")

    subsection("Important distinction")

    explain(
        "The classification is about the structure of the data, not its usefulness. "
        "Unstructured data can contain highly valuable information. For example, "
        "a customer support call may contain more useful information about customer "
        "sentiment than a structured satisfaction score."
    )

    rows = [
        ["Structured", "Fixed schema", "SQL tables", "High", "Relational database"],
        ["Semi-structured", "Flexible schema", "JSON/XML", "Medium", "Document store/data lake"],
        ["Unstructured", "No fixed tabular schema", "PDF/image/audio/video", "Low", "Object storage/data lake"],
    ]

    show_table(
        ["Type", "Schema", "Examples", "Tabular fit", "Typical storage"],
        rows
    )

    md_heading(1, "Structured, Semi-Structured, and Unstructured Data")
    md_text(
        "The structure of data affects how easily it can be represented, "
        "queried, validated, indexed, transformed, and analyzed."
    )

    md_heading(2, "Structured Data")
    md_text(
        "Structured data follows a predefined schema and is commonly organized "
        "into rows and columns. Relational database tables are the classic example."
    )
    md_code("""
customer_id | name | age | city
101         | Ravi | 31  | Lucknow
102         | Neha | 28  | Delhi
""")

    md_heading(2, "Semi-Structured Data")
    md_text(
        "Semi-structured data does not necessarily follow one rigid relational "
        "schema, but it contains keys, tags, metadata, nesting, or similar "
        "organizational information. JSON and XML are common examples."
    )

    md_code("""
{
    "customer_id": 101,
    "name": "Ravi",
    "address": {
        "city": "Lucknow"
    }
}
""", "json")

    md_heading(2, "Unstructured Data")
    md_text(
        "Unstructured data does not naturally conform to a fixed tabular schema. "
        "Examples include PDF documents, images, audio, video, scanned documents, "
        "emails, and free-form text."
    )

    md_table(
        ["Type", "Schema", "Examples", "Typical Storage"],
        rows
    )


# ============================================================================
# 4. DATABASES
# ============================================================================

def lesson_4_databases() -> None:
    section("4", "Databases")

    explain(
        "A database is an organized system for storing and retrieving data. "
        "Databases provide mechanisms for querying, inserting, updating, deleting, "
        "indexing, security, concurrency, constraints, and transaction management."
    )

    subsection("Relational databases")

    explain(
        "Relational databases represent data primarily as tables. Relationships "
        "between tables are established using keys. SQL is the standard language "
        "used for querying relational databases."
    )

    code_block("""
CUSTOMERS
---------
customer_id  name
1            A
2            B

ORDERS
------
order_id  customer_id  amount
101       1             500
102       1             700
103       2             300
""")

    explain(
        "The customer_id in ORDERS can reference customer_id in CUSTOMERS. "
        "This is an example of a foreign-key relationship."
    )

    subsection("Primary key")

    explain(
        "A primary key uniquely identifies a row in a table. For example, "
        "customer_id can uniquely identify a customer."
    )

    subsection("Foreign key")

    explain(
        "A foreign key is a column or set of columns that references a key "
        "in another table. It helps represent relationships between entities."
    )

    subsection("Constraints")

    bullet("PRIMARY KEY: uniquely identifies rows.")
    bullet("FOREIGN KEY: represents relationships.")
    bullet("NOT NULL: prevents missing values.")
    bullet("UNIQUE: prevents duplicate values.")
    bullet("CHECK: enforces a condition.")
    bullet("DEFAULT: supplies a value when one is not provided.")

    subsection("Indexes")

    explain(
        "An index is an additional data structure that helps a database locate "
        "rows efficiently. Indexes can make reads much faster but introduce storage "
        "overhead and can make writes more expensive because indexes may need updating."
    )

    subsection("Normalization")

    explain(
        "Normalization is a relational design technique that reduces unnecessary "
        "duplication and improves data integrity. A normalized system often separates "
        "entities into related tables rather than storing everything in one large table."
    )

    bullet(
        "First Normal Form generally requires atomic values and avoids repeating groups."
    )
    bullet(
        "Second Normal Form addresses partial dependency on part of a composite key."
    )
    bullet(
        "Third Normal Form addresses dependencies through non-key attributes."
    )

    subsection("Denormalization")

    explain(
        "Denormalization deliberately introduces some redundancy to improve read "
        "performance or simplify analytical queries. Data warehouses frequently use "
        "denormalized or dimensional structures."
    )

    subsection("NoSQL databases")

    explain(
        "NoSQL is a broad category covering database systems that use models other "
        "than the traditional relational model. Common categories include document, "
        "key-value, column-family, and graph databases."
    )

    show_table(
        ["Type", "Typical model", "Useful for"],
        [
            ["Relational", "Tables and relationships", "Transactions and structured data"],
            ["Document", "JSON-like documents", "Flexible application data"],
            ["Key-value", "Key -> value", "Fast lookup and caching"],
            ["Column-family", "Wide distributed rows", "Large distributed workloads"],
            ["Graph", "Nodes and edges", "Relationships and networks"],
        ]
    )

    md_heading(1, "Databases")
    md_text(
        "A database is an organized system for storing and retrieving data. "
        "Databases support querying, inserting, updating, deleting, indexing, "
        "security, concurrency, constraints, and transaction management."
    )

    md_heading(2, "Relational Databases")
    md_text(
        "Relational databases primarily represent data as tables. Relationships "
        "between tables are represented through keys, and SQL is commonly used "
        "to query the data."
    )

    md_heading(2, "Primary and Foreign Keys")
    md_text(
        "A primary key uniquely identifies a row. A foreign key references a key "
        "in another table and represents a relationship between entities."
    )

    md_heading(2, "Indexes")
    md_text(
        "An index is an additional data structure that helps the database locate "
        "rows efficiently. Indexes can improve read performance but consume storage "
        "and may increase write overhead."
    )

    md_heading(2, "Normalization and Denormalization")
    md_text(
        "Normalization reduces unnecessary duplication and improves data integrity. "
        "Denormalization deliberately introduces some redundancy to improve read "
        "performance or simplify queries."
    )

    md_heading(2, "NoSQL")
    md_text(
        "NoSQL is a broad category containing document, key-value, column-family, "
        "and graph databases. These systems are often selected for particular "
        "scalability, flexibility, or access-pattern requirements."
    )

    md_table(
        ["Type", "Typical Model", "Useful For"],
        [
            ["Relational", "Tables and relationships", "Transactions"],
            ["Document", "JSON-like documents", "Flexible application data"],
            ["Key-value", "Key -> value", "Fast lookups"],
            ["Column-family", "Wide distributed rows", "Distributed workloads"],
            ["Graph", "Nodes and edges", "Relationship-heavy data"],
        ]
    )


# ============================================================================
# 5. TRANSACTIONAL SYSTEMS
# ============================================================================

def lesson_5_oltp() -> None:
    section("5", "Transactional Systems and OLTP")

    explain(
        "OLTP stands for Online Transaction Processing. OLTP systems are designed "
        "to process operational transactions efficiently and reliably. Examples "
        "include placing an order, transferring money, updating inventory, creating "
        "an employee record, or registering a customer."
    )

    subsection("Characteristics of OLTP")

    bullet("Large number of relatively small transactions.")
    bullet("Frequent INSERT, UPDATE, and DELETE operations.")
    bullet("Strong consistency requirements.")
    bullet("Low response-time requirements.")
    bullet("Concurrent users.")
    bullet("Transaction integrity.")
    bullet("Usually normalized relational schemas.")

    subsection("ACID properties")

    explain(
        "ACID is a set of properties associated with reliable database transactions."
    )

    bullet(
        "Atomicity: a transaction is treated as one unit. It either completes "
        "according to the transaction rules or does not."
    )
    bullet(
        "Consistency: transactions preserve defined database constraints and rules."
    )
    bullet(
        "Isolation: concurrent transactions are controlled so that intermediate "
        "states do not incorrectly interfere with one another."
    )
    bullet(
        "Durability: committed changes survive appropriate failures."
    )

    subsection("Example: bank transfer")

    code_block("""
Transaction:

1. Deduct ₹1,000 from Account A.
2. Add ₹1,000 to Account B.
3. Commit.

If the transaction cannot complete correctly,
the database must follow its transaction and
recovery rules rather than leaving an invalid
partial transfer.
""")

    md_heading(1, "Transactional Systems and OLTP")
    md_text(
        "OLTP means Online Transaction Processing. OLTP systems process "
        "operational transactions such as orders, payments, inventory updates, "
        "customer registrations, and account transfers."
    )

    md_heading(2, "Typical OLTP Characteristics")
    for item in [
        "Many relatively small transactions.",
        "Frequent INSERT, UPDATE, and DELETE operations.",
        "Strong consistency requirements.",
        "Low response-time requirements.",
        "Concurrent users.",
        "Transaction integrity.",
        "Often normalized relational schemas.",
    ]:
        md_bullet(item)

    md_heading(2, "ACID")
    md_bullet(
        "Atomicity: a transaction is treated as a unit according to its transaction rules."
    )
    md_bullet(
        "Consistency: database constraints and rules remain valid."
    )
    md_bullet(
        "Isolation: concurrent transactions are controlled so intermediate states "
        "do not incorrectly interfere."
    )
    md_bullet(
        "Durability: committed changes survive appropriate failures."
    )


# ============================================================================
# 6. ANALYTICAL SYSTEMS
# ============================================================================

def lesson_6_olap() -> None:
    section("6", "Analytical Systems and OLAP")

    explain(
        "OLAP stands for Online Analytical Processing. OLAP systems are designed "
        "for complex queries that examine large amounts of historical data. "
        "Analysts may aggregate millions or billions of records to identify "
        "patterns, trends, relationships, and business performance."
    )

    subsection("Typical analytical questions")

    numbered(1, "What were monthly sales by region during the last three years?")
    numbered(2, "Which products have declining margins?")
    numbered(3, "Which customer segments have the highest lifetime value?")
    numbered(4, "How does conversion rate vary by marketing channel?")
    numbered(5, "Which stores consistently underperform their regional average?")

    subsection("OLTP vs OLAP")

    comparison = [
        ["Primary purpose", "Run the business", "Analyze the business"],
        ["Workload", "Transactions", "Complex queries"],
        ["Data", "Current operational", "Historical and integrated"],
        ["Typical operations", "INSERT/UPDATE/DELETE", "SELECT/aggregation"],
        ["Schema", "Often normalized", "Often dimensional/analytical"],
        ["Users", "Applications/operators", "Analysts/BI/data teams"],
        ["Query pattern", "Small and predictable", "Large and exploratory"],
    ]

    show_table(
        ["Dimension", "OLTP", "OLAP"],
        comparison
    )

    md_heading(1, "Analytical Systems and OLAP")
    md_text(
        "OLAP means Online Analytical Processing. OLAP systems are designed "
        "for complex queries over large amounts of historical data."
    )

    md_heading(2, "OLTP vs OLAP")
    md_table(
        ["Dimension", "OLTP", "OLAP"],
        comparison
    )

    subsection("Why not run heavy analytics directly on the production database?")

    explain(
        "An operational database is optimized for application transactions. "
        "A large analytical query can consume CPU, memory, I/O, locks, or other "
        "resources and potentially interfere with operational workloads. Separating "
        "analytical processing from operational processing allows each environment "
        "to be optimized for its own workload."
    )

    md_heading(2, "Why Separate Operational and Analytical Workloads?")
    md_text(
        "Production databases are optimized for operational transactions. Heavy "
        "analytical queries can consume substantial compute, memory, I/O, or other "
        "resources. Separating analytical workloads allows operational and analytical "
        "systems to be optimized independently."
    )


# ============================================================================
# 7. DATA WAREHOUSES
# ============================================================================

def lesson_7_data_warehouse() -> None:
    section("7", "Data Warehouses")

    explain(
        "A data warehouse is a system designed primarily for analytical workloads. "
        "It usually contains integrated, cleaned, transformed, historical data "
        "from multiple operational and external sources."
    )

    subsection("Typical warehouse flow")

    code_block("""
CRM --------\
ERP ---------\
Payments -----+--> Ingestion --> Transformation --> Data Warehouse
Website -----/                                      |
Marketing ---/                                      v
                                              BI / Analytics
""")

    subsection("Characteristics")

    bullet("Designed for analytics.")
    bullet("Integrates multiple sources.")
    bullet("Stores historical information.")
    bullet("Supports SQL and aggregations.")
    bullet("Often applies controlled schemas.")
    bullet("Supports reporting and business intelligence.")

    subsection("Fact tables")

    explain(
        "A fact table usually contains measurable business events. Examples "
        "include sales transactions, shipments, website sessions, or payments."
    )

    code_block("""
sales_fact

date_key
customer_key
product_key
store_key
quantity
sales_amount
discount_amount
cost_amount
""")

    subsection("Dimension tables")

    explain(
        "Dimension tables describe the entities involved in business events. "
        "Examples include customer, product, store, employee, and date dimensions."
    )

    code_block("""
product_dimension

product_key
product_id
product_name
category
brand
supplier
""")

    subsection("Star schema")

    explain(
        "A star schema contains a central fact table surrounded by dimension "
        "tables. It is common in analytical modeling because it provides a "
        "clear structure for business queries."
    )

    code_block("""
                  date_dimension
                        |
                        |
customer_dimension -- sales_fact -- product_dimension
                        |
                        |
                  store_dimension
""")

    subsection("Snowflake schema")

    explain(
        "A snowflake schema normalizes some dimension structures into additional "
        "tables. It can reduce redundancy but may increase query complexity."
    )

    subsection("Data marts")

    explain(
        "A data mart is a focused analytical data store or subset intended for "
        "a particular business function such as finance, sales, marketing, or HR."
    )

    md_heading(1, "Data Warehouses")
    md_text(
        "A data warehouse is primarily designed for analytical workloads. It "
        "usually contains integrated, cleaned, transformed, historical data "
        "from multiple operational and external sources."
    )

    md_heading(2, "Fact Tables")
    md_text(
        "Fact tables usually represent measurable business events such as sales, "
        "shipments, website sessions, or payments."
    )

    md_heading(2, "Dimension Tables")
    md_text(
        "Dimension tables describe entities involved in business events, such as "
        "customers, products, stores, employees, and dates."
    )

    md_heading(2, "Star Schema")
    md_text(
        "A star schema has a central fact table surrounded by dimension tables. "
        "It is widely used for analytical modeling."
    )

    md_code("""
                  date_dimension
                        |
customer_dimension -- sales_fact -- product_dimension
                        |
                  store_dimension
""")

    md_heading(2, "Data Marts")
    md_text(
        "A data mart is a focused analytical data store for a business function "
        "such as finance, sales, marketing, or HR."
    )


# ============================================================================
# 8. DATA LAKES
# ============================================================================

def lesson_8_data_lake() -> None:
    section("8", "Data Lakes")

    explain(
        "A data lake is a storage environment designed to hold large volumes "
        "of data in its original or relatively raw form. It can accommodate "
        "structured, semi-structured, and unstructured data."
    )

    subsection("Typical data lake contents")

    bullet("CSV files")
    bullet("JSON events")
    bullet("Parquet files")
    bullet("Application logs")
    bullet("Images")
    bullet("Audio")
    bullet("Video")
    bullet("Documents")
    bullet("Sensor data")
    bullet("Database extracts")

    subsection("Schema-on-read")

    explain(
        "Data lakes are commonly associated with schema-on-read. Data can be "
        "stored before a rigid analytical schema is imposed. The structure is "
        "applied when the data is read or processed for a particular purpose."
    )

    subsection("Schema-on-write")

    explain(
        "Traditional analytical warehouses often emphasize schema-on-write. "
        "Data is transformed and validated according to a target schema before "
        "being stored in the analytical structure."
    )

    show_table(
        ["Concept", "Schema-on-write", "Schema-on-read"],
        [
            ["When schema is applied", "Before/while storing", "When consuming"],
            ["Typical association", "Warehouse", "Data lake"],
            ["Flexibility", "Lower", "Higher"],
            ["Governance at ingestion", "Usually stronger", "Can be lighter initially"],
        ]
    )

    subsection("Data lake zones")

    bullet("Raw/Bronze: source data with minimal transformation.")
    bullet("Cleansed/Silver: validated and standardized data.")
    bullet("Curated/Gold: business-ready datasets.")

    md_heading(1, "Data Lakes")
    md_text(
        "A data lake is a storage environment designed to hold large volumes "
        "of data in its original or relatively raw form. It can accommodate "
        "structured, semi-structured, and unstructured data."
    )

    md_heading(2, "Schema-on-Read")
    md_text(
        "Schema-on-read means the structure can be applied when data is consumed "
        "or processed for a particular purpose. This is commonly associated with "
        "data lake architectures."
    )

    md_heading(2, "Schema-on-Write")
    md_text(
        "Schema-on-write means data is transformed and validated against a target "
        "schema before being stored in its analytical structure."
    )

    md_table(
        ["Concept", "Schema-on-Write", "Schema-on-Read"],
        [
            ["Schema timing", "Before/while storing", "When consuming"],
            ["Typical association", "Warehouse", "Data lake"],
            ["Flexibility", "Lower", "Higher"],
            ["Initial governance", "Usually stronger", "Can be lighter"],
        ]
    )

    md_heading(2, "Lake Zones")
    md_bullet("Bronze/Raw: source data with minimal transformation.")
    md_bullet("Silver/Cleansed: validated and standardized data.")
    md_bullet("Gold/Curated: business-ready datasets.")


# ============================================================================
# 9. DATA LAKEHOUSE
# ============================================================================

def lesson_9_lakehouse() -> None:
    section("9", "The Data Lakehouse Concept")

    explain(
        "A lakehouse is an architectural approach that attempts to combine the "
        "low-cost and flexible storage characteristics of data lakes with many "
        "of the management and analytical capabilities traditionally associated "
        "with data warehouses."
    )

    subsection("Why lakehouses emerged")

    explain(
        "Organizations often had separate data lakes for raw and varied data and "
        "warehouses for curated analytical data. This could result in duplicated "
        "data, multiple pipelines, inconsistent definitions, and operational "
        "complexity. Lakehouse architectures attempt to reduce this separation "
        "by providing stronger table management and analytical capabilities over "
        "data-lake-style storage."
    )

    bullet("Flexible storage.")
    bullet("Support for multiple data types.")
    bullet("Analytical querying.")
    bullet("Table metadata and schema management.")
    bullet("Versioning or time-travel capabilities in some implementations.")
    bullet("Better support for mixed analytical workloads.")

    md_heading(1, "Data Lakehouse")
    md_text(
        "A lakehouse is an architectural approach that combines flexible data-lake "
        "storage with capabilities traditionally associated with data warehouses."
    )

    md_heading(2, "Why Lakehouses Emerged")
    md_text(
        "Organizations often operated separate lakes and warehouses. This could "
        "create duplicated data, multiple pipelines, inconsistent definitions, "
        "and additional operational complexity. Lakehouse architectures attempt "
        "to provide stronger table and analytical capabilities directly over "
        "lake-style storage."
    )


# ============================================================================
# 10. APIS
# ============================================================================

def lesson_10_apis() -> None:
    section("10", "APIs as Data Sources")

    explain(
        "An API, or Application Programming Interface, provides a defined way for "
        "one software system to communicate with another. APIs are frequently used "
        "to retrieve or submit data between systems."
    )

    subsection("Example REST request")

    code_block("""
GET /customers/101

Response:

{
    "id": 101,
    "name": "Ravi",
    "city": "Lucknow"
}
""")

    subsection("Common HTTP methods")

    show_table(
        ["Method", "Typical meaning"],
        [
            ["GET", "Retrieve data"],
            ["POST", "Create or submit data"],
            ["PUT", "Replace/update a resource"],
            ["PATCH", "Partially update a resource"],
            ["DELETE", "Delete a resource"],
        ]
    )

    subsection("API pagination")

    explain(
        "APIs often limit the number of records returned in a single request. "
        "Pagination allows a client to retrieve data in multiple pages."
    )

    code_block("""
GET /orders?page=1&limit=100
GET /orders?page=2&limit=100
GET /orders?page=3&limit=100
""")

    subsection("Rate limiting")

    explain(
        "Rate limiting restricts how many requests a client can make within "
        "a period. Analytics pipelines must respect API limits or risk failed "
        "requests, throttling, or temporary access restrictions."
    )

    subsection("Authentication")

    bullet("API keys")
    bullet("Bearer tokens")
    bullet("OAuth 2.0")
    bullet("Signed requests")
    bullet("Service credentials")

    subsection("Webhooks")

    explain(
        "A webhook reverses the normal polling pattern. Instead of repeatedly "
        "asking whether something happened, a source sends an HTTP request to "
        "a registered endpoint when an event occurs."
    )

    md_heading(1, "APIs as Data Sources")
    md_text(
        "An API provides a defined interface through which software systems "
        "communicate. APIs are frequently used to retrieve or submit data."
    )

    md_heading(2, "Common HTTP Methods")
    md_table(
        ["Method", "Typical Meaning"],
        [
            ["GET", "Retrieve data"],
            ["POST", "Create or submit data"],
            ["PUT", "Replace/update a resource"],
            ["PATCH", "Partially update a resource"],
            ["DELETE", "Delete a resource"],
        ]
    )

    md_heading(2, "Pagination")
    md_text(
        "APIs commonly limit the number of records returned by one request. "
        "Pagination allows clients to retrieve multiple pages."
    )

    md_heading(2, "Rate Limiting")
    md_text(
        "Rate limiting controls how many requests a client can make during a "
        "period. Data pipelines must respect these limits."
    )

    md_heading(2, "Webhooks")
    md_text(
        "A webhook allows a source to send a request to a registered endpoint "
        "when an event occurs instead of requiring the consumer to repeatedly poll."
    )


# ============================================================================
# 11. SPREADSHEETS
# ============================================================================

def lesson_11_spreadsheets() -> None:
    section("11", "Spreadsheets as Data Sources")

    explain(
        "Spreadsheets are often underestimated in data architecture. In many "
        "organizations, spreadsheets contain operational data, financial models, "
        "manual adjustments, forecasts, mappings, and business rules."
    )

    subsection("Strengths")

    bullet("Easy to create.")
    bullet("Easy to modify.")
    bullet("Familiar to business users.")
    bullet("Useful for small datasets.")
    bullet("Good for ad hoc analysis.")
    bullet("Supports formulas and manual modeling.")

    subsection("Weaknesses")

    bullet("Manual errors.")
    bullet("Duplicate versions.")
    bullet("Unclear ownership.")
    bullet("Weak auditability.")
    bullet("Inconsistent schemas.")
    bullet("Difficult concurrency management.")
    bullet("Poor scalability for large datasets.")
    bullet("Business logic can be hidden inside formulas.")

    subsection("Example problem")

    code_block("""
sales_final.xlsx
sales_final_v2.xlsx
sales_final_latest.xlsx
sales_final_latest_revised.xlsx

Which file is authoritative?
""")

    explain(
        "A spreadsheet can be a legitimate source in an analytics ecosystem, "
        "but it should be treated as a governed data source when it becomes "
        "important to business reporting."
    )

    md_heading(1, "Spreadsheets as Data Sources")
    md_text(
        "Spreadsheets are widely used for operational data, financial models, "
        "manual adjustments, forecasts, mappings, and business rules."
    )

    md_heading(2, "Strengths")
    for item in [
        "Easy to create and modify.",
        "Familiar to business users.",
        "Useful for small datasets.",
        "Good for ad hoc analysis.",
        "Supports formulas and manual modeling.",
    ]:
        md_bullet(item)

    md_heading(2, "Weaknesses")
    for item in [
        "Manual errors.",
        "Duplicate versions.",
        "Unclear ownership.",
        "Weak auditability.",
        "Inconsistent schemas.",
        "Poor scalability.",
        "Business logic may be hidden in formulas.",
    ]:
        md_bullet(item)


# ============================================================================
# 12. BUSINESS APPLICATIONS
# ============================================================================

def lesson_12_business_applications() -> None:
    section("12", "Business Applications as Data Sources")

    explain(
        "Business applications are among the most important sources in enterprise "
        "analytics because they record actual business processes."
    )

    systems = [
        DataSystem("ERP", "Enterprise Resource Planning", "Operational",
                   "Relational/transactional", "Finance, operations"),
        DataSystem("CRM", "Customer Relationship Management", "Operational",
                   "Relational/application", "Sales, service, marketing"),
        DataSystem("HRMS", "Human Resources Management", "Operational",
                   "Relational/application", "HR"),
        DataSystem("POS", "Point of Sale", "Operational",
                   "Transactional", "Retail"),
        DataSystem("SCM", "Supply Chain Management", "Operational",
                   "Relational/application", "Supply chain"),
        DataSystem("Marketing platform", "Marketing automation", "Operational",
                   "Application/API", "Marketing"),
        DataSystem("Ticketing system", "Service management", "Operational",
                   "Application/database", "Support"),
    ]

    show_table(
        ["System", "Purpose", "Workload", "Storage", "Users"],
        [[
            x.name, x.system_type, x.workload, x.storage_model, x.typical_users
        ] for x in systems]
    )

    subsection("ERP")

    explain(
        "ERP systems integrate business processes such as finance, procurement, "
        "inventory, manufacturing, and operations."
    )

    subsection("CRM")

    explain(
        "CRM systems manage information about customers, leads, opportunities, "
        "sales activities, service interactions, and customer relationships."
    )

    subsection("HR systems")

    explain(
        "HR systems contain employee-related operational information such as "
        "employee records, organizational structures, attendance, compensation, "
        "and recruitment information."
    )

    subsection("POS")

    explain(
        "Point-of-sale systems record retail transactions including products, "
        "quantities, prices, discounts, taxes, payments, and timestamps."
    )

    md_heading(1, "Business Applications as Data Sources")
    md_text(
        "Business applications are important enterprise data sources because "
        "they record actual business processes."
    )

    md_table(
        ["System", "Purpose", "Typical Data"],
        [
            ["ERP", "Enterprise operations", "Finance, procurement, inventory"],
            ["CRM", "Customer relationships", "Customers, leads, opportunities"],
            ["HRMS", "Human resources", "Employees, organization, compensation"],
            ["POS", "Retail transactions", "Products, quantities, payments"],
            ["SCM", "Supply chain", "Suppliers, logistics, inventory"],
            ["Marketing platform", "Marketing", "Campaigns, leads, engagement"],
            ["Ticketing", "Service", "Tickets, incidents, resolution"],
        ]
    )


# ============================================================================
# 13. ETL AND ELT
# ============================================================================

def lesson_13_etl_elt() -> None:
    section("13", "ETL and ELT")

    explain(
        "ETL stands for Extract, Transform, Load. ELT stands for Extract, Load, "
        "Transform. Both describe ways of moving data from sources into analytical "
        "systems."
    )

    subsection("ETL")

    code_block("""
Source
  |
  v
Extract
  |
  v
Transform
  |
  v
Load
  |
  v
Warehouse
""")

    explain(
        "In ETL, data is transformed before it is loaded into the target analytical "
        "system. This approach historically became common when target systems had "
        "limited storage or processing capacity."
    )

    subsection("ELT")

    code_block("""
Source
  |
  v
Extract
  |
  v
Load
  |
  v
Analytical storage
  |
  v
Transform
""")

    explain(
        "In ELT, data is loaded into the target environment first and transformed "
        "there. Modern cloud analytical platforms often have substantial compute "
        "capacity, making ELT practical."
    )

    show_table(
        ["Aspect", "ETL", "ELT"],
        [
            ["Transformation", "Before loading", "After loading"],
            ["Raw data retention", "Not always retained", "Often retained"],
            ["Target compute", "Less dependent", "More important"],
            ["Typical modern use", "Still common", "Very common"],
        ]
    )

    md_heading(1, "ETL and ELT")
    md_text(
        "ETL means Extract, Transform, Load. ELT means Extract, Load, Transform. "
        "Both describe methods for moving source data into analytical environments."
    )

    md_heading(2, "ETL")
    md_code("""
Source -> Extract -> Transform -> Load -> Warehouse
""")

    md_heading(2, "ELT")
    md_code("""
Source -> Extract -> Load -> Transform
""")

    md_table(
        ["Aspect", "ETL", "ELT"],
        [
            ["Transformation", "Before loading", "After loading"],
            ["Raw data retention", "Not always retained", "Often retained"],
            ["Target compute", "Less important", "More important"],
        ]
    )


# ============================================================================
# 14. DATA INGESTION
# ============================================================================

def lesson_14_ingestion() -> None:
    section("14", "Data Ingestion")

    explain(
        "Data ingestion is the process of bringing data from source systems into "
        "another storage or processing environment."
    )

    subsection("Batch ingestion")

    explain(
        "Batch ingestion moves data at scheduled intervals. For example, an ERP "
        "extract might be copied to analytical storage every night."
    )

    code_block("""
00:00 ----> Extract yesterday's data
01:00 ----> Validate
02:00 ----> Transform
03:00 ----> Load warehouse
04:00 ----> Refresh dashboards
""")

    subsection("Streaming ingestion")

    explain(
        "Streaming ingestion processes events continuously or in small increments. "
        "Examples include website events, payment events, sensor readings, and "
        "application logs."
    )

    code_block("""
Event 1 --->\
Event 2 -----> Streaming platform ---> Consumers
Event 3 --->/
Event 4 --->/
""")

    subsection("CDC")

    explain(
        "Change Data Capture, or CDC, identifies inserts, updates, and deletes "
        "from a source system so that downstream systems can receive changes "
        "without repeatedly extracting the entire database."
    )

    subsection("Full load vs incremental load")

    bullet(
        "Full load: copy the complete dataset during each load operation."
    )
    bullet(
        "Incremental load: copy only new or changed records."
    )

    md_heading(1, "Data Ingestion")
    md_text(
        "Data ingestion is the process of bringing data from source systems "
        "into another storage or processing environment."
    )

    md_heading(2, "Batch Ingestion")
    md_text(
        "Batch ingestion moves data at scheduled intervals, such as nightly "
        "ERP extracts."
    )

    md_heading(2, "Streaming Ingestion")
    md_text(
        "Streaming ingestion processes events continuously or in small increments. "
        "Common examples include application events, sensor readings, payments, "
        "and logs."
    )

    md_heading(2, "Change Data Capture")
    md_text(
        "CDC identifies inserts, updates, and deletes in a source system so "
        "downstream systems can receive changes without repeatedly copying the "
        "entire source database."
    )

    md_heading(2, "Full vs Incremental Load")
    md_bullet("Full load: copy the complete dataset.")
    md_bullet("Incremental load: copy only new or changed records.")


# ============================================================================
# 15. DATA PIPELINES
# ============================================================================

def lesson_15_pipelines() -> None:
    section("15", "Data Pipelines")

    explain(
        "A data pipeline is a sequence of processes that moves and transforms "
        "data from one stage to another."
    )

    code_block("""
Source
  |
  v
Extract
  |
  v
Validate
  |
  v
Clean
  |
  v
Transform
  |
  v
Store
  |
  v
Serve
  |
  v
Analyze
""")

    subsection("Pipeline concerns")

    bullet("Source connectivity")
    bullet("Scheduling")
    bullet("Data validation")
    bullet("Schema changes")
    bullet("Transformation logic")
    bullet("Error handling")
    bullet("Retries")
    bullet("Monitoring")
    bullet("Logging")
    bullet("Lineage")
    bullet("Security")
    bullet("Access control")

    subsection("Idempotency")

    explain(
        "An operation is idempotent when executing it repeatedly produces the "
        "same intended final state. Idempotency is important in data pipelines "
        "because jobs can fail and need to be retried."
    )

    subsection("Data lineage")

    explain(
        "Data lineage describes where data originated, how it was transformed, "
        "and where it was consumed. It helps with troubleshooting, governance, "
        "impact analysis, and regulatory requirements."
    )

    md_heading(1, "Data Pipelines")
    md_text(
        "A data pipeline is a sequence of processes that moves and transforms "
        "data between stages."
    )

    md_heading(2, "Important Pipeline Concerns")
    for item in [
        "Source connectivity",
        "Scheduling",
        "Validation",
        "Schema changes",
        "Transformation",
        "Error handling",
        "Retries",
        "Monitoring",
        "Logging",
        "Lineage",
        "Security",
        "Access control",
    ]:
        md_bullet(item)

    md_heading(2, "Idempotency")
    md_text(
        "An idempotent operation can be executed repeatedly while producing "
        "the same intended final state. This is valuable when pipeline jobs "
        "need to be retried."
    )

    md_heading(2, "Data Lineage")
    md_text(
        "Data lineage describes where data originated, how it was transformed, "
        "and where it was consumed."
    )


# ============================================================================
# 16. DATA QUALITY
# ============================================================================

def lesson_16_data_quality() -> None:
    section("16", "Data Quality")

    explain(
        "Data quality determines whether data is suitable for its intended use. "
        "Poor quality data can make technically correct analysis produce "
        "incorrect business conclusions."
    )

    dimensions = [
        ["Accuracy", "Does the value represent reality?"],
        ["Completeness", "Are required values present?"],
        ["Consistency", "Do different systems agree?"],
        ["Timeliness", "Is the data available when needed?"],
        ["Validity", "Does the value conform to rules?"],
        ["Uniqueness", "Are duplicate records controlled?"],
    ]

    show_table(["Dimension", "Question"], dimensions)

    subsection("Example")

    code_block("""
customer_id = 101
age = -14
country = "India"
email = "not-an-email"
order_date = "2099-99-45"
""")

    explain(
        "This record may violate validity rules even if every field technically "
        "contains a value. Completeness alone does not imply quality."
    )

    subsection("Data validation")

    bullet("Data type validation")
    bullet("Range validation")
    bullet("Format validation")
    bullet("Referential validation")
    bullet("Uniqueness checks")
    bullet("Null checks")
    bullet("Business-rule validation")

    md_heading(1, "Data Quality")
    md_text(
        "Data quality determines whether data is suitable for its intended use. "
        "Poor quality data can lead to incorrect business conclusions."
    )

    md_table(
        ["Dimension", "Question"],
        dimensions
    )

    md_heading(2, "Validation")
    for item in [
        "Data type validation",
        "Range validation",
        "Format validation",
        "Referential validation",
        "Uniqueness checks",
        "Null checks",
        "Business-rule validation",
    ]:
        md_bullet(item)


# ============================================================================
# 17. DATA GOVERNANCE
# ============================================================================

def lesson_17_governance() -> None:
    section("17", "Data Governance")

    explain(
        "Data governance establishes policies, ownership, standards, controls, "
        "and responsibilities for managing data."
    )

    subsection("Important concepts")

    bullet(
        "Data owner: accountable business stakeholder for a data domain."
    )
    bullet(
        "Data steward: helps maintain data definitions, quality, and governance."
    )
    bullet(
        "Data custodian: responsible for technical management and controls."
    )
    bullet(
        "Data catalog: inventory and description of available datasets."
    )
    bullet(
        "Business glossary: standardized definitions of business terms."
    )
    bullet(
        "Lineage: relationship between sources, transformations, and destinations."
    )
    bullet(
        "Access control: determines who can access which data."
    )

    subsection("Why governance matters")

    explain(
        "Two departments can use the same word but mean different things. For "
        "example, 'customer' could mean anyone registered in a CRM, anyone who "
        "has purchased something, or anyone with an active subscription. Without "
        "defined semantics, dashboards can disagree even when their SQL is correct."
    )

    md_heading(1, "Data Governance")
    md_text(
        "Data governance establishes policies, ownership, standards, controls, "
        "and responsibilities for managing data."
    )

    md_heading(2, "Key Concepts")
    for item in [
        "Data owner: accountable business stakeholder for a data domain.",
        "Data steward: helps maintain definitions, quality, and governance.",
        "Data custodian: responsible for technical management and controls.",
        "Data catalog: inventory and description of datasets.",
        "Business glossary: standardized definitions of business terms.",
        "Data lineage: relationship between sources, transformations, and destinations.",
        "Access control: determines who can access data.",
    ]:
        md_bullet(item)


# ============================================================================
# 18. METADATA
# ============================================================================

def lesson_18_metadata() -> None:
    section("18", "Metadata")

    explain(
        "Metadata is information about data. It makes datasets understandable "
        "and manageable."
    )

    subsection("Types of metadata")

    bullet(
        "Technical metadata: data types, column names, table names, file formats."
    )
    bullet(
        "Business metadata: definitions, owners, business meaning, policies."
    )
    bullet(
        "Operational metadata: load time, pipeline status, record counts, failures."
    )

    code_block("""
Dataset: sales_fact

Technical:
    sales_amount -> DECIMAL
    customer_key -> INTEGER

Business:
    sales_amount = net recognized sales amount

Operational:
    last_loaded = 2026-09-02 03:15
    rows_loaded = 12,450,392
""")

    md_heading(1, "Metadata")
    md_text(
        "Metadata is information about data. It makes datasets understandable, "
        "discoverable, governable, and manageable."
    )

    md_heading(2, "Types of Metadata")
    md_bullet(
        "Technical metadata: column names, data types, table names, file formats."
    )
    md_bullet(
        "Business metadata: definitions, owners, business meaning, policies."
    )
    md_bullet(
        "Operational metadata: load time, pipeline status, record counts, failures."
    )


# ============================================================================
# 19. DATA MODELING
# ============================================================================

def lesson_19_data_modeling() -> None:
    section("19", "Data Modeling in the Analytics Ecosystem")

    explain(
        "Data modeling is the process of designing how data entities, attributes, "
        "relationships, and business events are represented."
    )

    subsection("Entities")

    explain(
        "An entity is something about which the organization stores information. "
        "Examples include Customer, Product, Employee, Supplier, and Order."
    )

    subsection("Attributes")

    explain(
        "Attributes describe entities. A Customer might have customer_id, name, "
        "email, city, and registration_date."
    )

    subsection("Relationships")

    explain(
        "Relationships represent how entities are connected. One customer may "
        "place many orders. One order may contain many products."
    )

    subsection("Grain")

    explain(
        "Grain defines exactly what one row represents. This is one of the most "
        "important ideas in analytical modeling."
    )

    code_block("""
sales_fact grain:

"One row represents one product line
within one customer order."

That means:

Order 1001
  Product A
  Product B

creates two fact rows.
""")

    explain(
        "If the grain is not defined clearly, measures can be duplicated and "
        "aggregations can become incorrect."
    )

    md_heading(1, "Data Modeling")
    md_text(
        "Data modeling defines how entities, attributes, relationships, and "
        "business events are represented."
    )

    md_heading(2, "Grain")
    md_text(
        "Grain specifies exactly what one row represents. It is critical in "
        "analytical modeling because incorrect grain can cause duplicated "
        "measures and incorrect aggregations."
    )

    md_code("""
Example grain:
One row represents one product line within one customer order.
""")


# ============================================================================
# 20. DATA INTEGRATION
# ============================================================================

def lesson_20_integration() -> None:
    section("20", "Data Integration")

    explain(
        "Data integration combines information from different sources so that "
        "it can be analyzed together."
    )

    subsection("The identity problem")

    code_block("""
CRM:
customer_id = 1001
name = "Ravi Kumar"

ERP:
customer_id = C-8841
name = "R. Kumar"

Website:
user_id = 77
email = ravi@example.com
""")

    explain(
        "These may represent the same person even though their identifiers "
        "differ. Integration requires matching, mapping, or a shared master "
        "identifier."
    )

    subsection("Common integration operations")

    bullet("Join")
    bullet("Union")
    bullet("Lookup")
    bullet("Mapping")
    bullet("Deduplication")
    bullet("Standardization")
    bullet("Entity resolution")
    bullet("Master data management")

    subsection("Master data")

    explain(
        "Master data represents relatively stable business entities such as "
        "customers, products, suppliers, employees, or locations. Master data "
        "management attempts to create reliable shared representations of these entities."
    )

    md_heading(1, "Data Integration")
    md_text(
        "Data integration combines information from different sources so it "
        "can be analyzed together."
    )

    md_heading(2, "Common Integration Operations")
    for item in [
        "Join",
        "Union",
        "Lookup",
        "Mapping",
        "Deduplication",
        "Standardization",
        "Entity resolution",
        "Master data management",
    ]:
        md_bullet(item)

    md_heading(2, "Master Data")
    md_text(
        "Master data represents relatively stable business entities such as "
        "customers, products, suppliers, employees, and locations."
    )


# ============================================================================
# 21. DATA STORAGE LAYERS
# ============================================================================

def lesson_21_storage_layers() -> None:
    section("21", "A Layered Analytics Architecture")

    architecture = [
        DataLayer(
            "Source layer",
            "Original systems where business activity occurs.",
            ["ERP", "CRM", "Website", "POS", "Payments"]
        ),
        DataLayer(
            "Ingestion layer",
            "Moves data from sources into analytical environments.",
            ["APIs", "CDC", "Batch", "Streaming"]
        ),
        DataLayer(
            "Raw storage",
            "Retains source-oriented data.",
            ["Object storage", "Raw files"]
        ),
        DataLayer(
            "Processing layer",
            "Cleans, validates, joins, and transforms data.",
            ["SQL", "Spark", "Python"]
        ),
        DataLayer(
            "Analytical storage",
            "Stores curated analytical datasets.",
            ["Warehouse", "Lakehouse"]
        ),
        DataLayer(
            "Serving layer",
            "Makes information available to users.",
            ["BI", "Dashboards", "Semantic models", "APIs"]
        ),
    ]

    show_table(
        ["Layer", "Purpose", "Examples"],
        [[
            x.name, x.purpose, ", ".join(x.examples)
        ] for x in architecture]
    )

    md_heading(1, "Layered Analytics Architecture")
    md_table(
        ["Layer", "Purpose", "Examples"],
        [[x.name, x.purpose, ", ".join(x.examples)] for x in architecture]
    )


# ============================================================================
# 22. DATA FLOW CASE STUDY
# ============================================================================

def lesson_22_case_study() -> None:
    section("22", "End-to-End Example: E-Commerce Company")

    explain(
        "Consider an e-commerce company processing thousands of orders every day."
    )

    subsection("Step 1: Data generation")

    bullet("Customers browse products.")
    bullet("Customers add products to carts.")
    bullet("Customers place orders.")
    bullet("Payments are processed.")
    bullet("Warehouses ship products.")
    bullet("Marketing systems record campaigns.")
    bullet("Customer support records interactions.")

    subsection("Step 2: Operational systems")

    bullet("Website application database stores users and sessions.")
    bullet("Order database stores orders.")
    bullet("Payment provider stores payment events.")
    bullet("CRM stores customer and sales information.")
    bullet("Warehouse system stores fulfillment information.")

    subsection("Step 3: Ingestion")

    bullet("Database changes can be captured using CDC.")
    bullet("Payment events can arrive through webhooks.")
    bullet("CRM data may be retrieved through an API.")
    bullet("Marketing reports may arrive as CSV files.")

    subsection("Step 4: Storage")

    bullet("Raw data can be stored in a data lake.")
    bullet("Curated business data can be loaded into a warehouse.")

    subsection("Step 5: Transformation")

    bullet("Standardize currencies.")
    bullet("Clean customer identifiers.")
    bullet("Remove duplicate records.")
    bullet("Calculate net revenue.")
    bullet("Create product and customer dimensions.")

    subsection("Step 6: Analytics")

    bullet("Daily revenue dashboard.")
    bullet("Customer lifetime value.")
    bullet("Product profitability.")
    bullet("Regional performance.")
    bullet("Marketing attribution.")

    subsection("Architecture")

    code_block("""
                         +----------------+
                         | Website / App   |
                         +--------+-------+
                                  |
                         +--------v-------+
                         | Operational DB |
                         +--------+-------+
                                  |
             +--------------------+--------------------+
             |                    |                    |
             v                    v                    v
           CDC                  API                Webhook
             |                    |                    |
             +--------------------+--------------------+
                                  |
                                  v
                         +----------------+
                         | Data Lake      |
                         | Raw data       |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         | Transform      |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         | Data Warehouse |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         | BI / Analytics |
                         +----------------+
""")

    md_heading(1, "End-to-End Example: E-Commerce")
    md_text(
        "An e-commerce company can generate data from its website, order system, "
        "payment provider, CRM, warehouse, marketing platforms, and customer "
        "support system."
    )

    md_heading(2, "Typical Flow")
    for item in [
        "Customers generate activity.",
        "Operational systems record transactions.",
        "CDC, APIs, webhooks, and files move data.",
        "Raw data is stored.",
        "Data is cleaned and transformed.",
        "Curated data is stored analytically.",
        "BI and analytics tools consume the curated data.",
    ]:
        md_bullet(item)


# ============================================================================
# 23. ARCHITECTURAL TRADE-OFFS
# ============================================================================

def lesson_23_tradeoffs() -> None:
    section("23", "Architectural Trade-offs")

    explain(
        "There is no universally best data storage system. The correct choice "
        "depends on workload, latency, volume, variety, consistency requirements, "
        "cost, governance, security, team capabilities, and analytical needs."
    )

    show_table(
        ["Technology", "Primary strength", "Typical limitation"],
        [
            ["Spreadsheet", "Ease of use", "Scalability/governance"],
            ["OLTP database", "Reliable transactions", "Not ideal for heavy analytics"],
            ["Data warehouse", "Fast structured analytics", "Less natural for raw media"],
            ["Data lake", "Flexible large-scale storage", "Governance can be complex"],
            ["Lakehouse", "Flexible storage + analytical tables", "Architectural complexity"],
            ["API", "System-to-system access", "Rate limits/dependencies"],
        ]
    )

    subsection("Important design dimensions")

    bullet("Latency: How quickly must data become available?")
    bullet("Volume: How much data is generated?")
    bullet("Velocity: How quickly does data arrive?")
    bullet("Variety: How many data formats exist?")
    bullet("Veracity: How reliable is the data?")
    bullet("Cost: What is the storage and processing budget?")
    bullet("Governance: What controls are required?")
    bullet("Security: How sensitive is the information?")
    bullet("Availability: How reliably must the system operate?")

    md_heading(1, "Architectural Trade-offs")
    md_text(
        "There is no universally best data storage system. Technology selection "
        "depends on workload, latency, volume, variety, consistency, cost, "
        "governance, security, and analytical requirements."
    )

    md_table(
        ["Technology", "Primary Strength", "Typical Limitation"],
        [
            ["Spreadsheet", "Ease of use", "Scalability and governance"],
            ["OLTP database", "Reliable transactions", "Heavy analytics"],
            ["Data warehouse", "Structured analytics", "Raw media"],
            ["Data lake", "Flexible storage", "Governance complexity"],
            ["Lakehouse", "Flexible storage + analytics", "Architectural complexity"],
            ["API", "System-to-system access", "Rate limits/dependencies"],
        ]
    )


# ============================================================================
# 24. DATA LATENCY
# ============================================================================

def lesson_24_latency() -> None:
    section("24", "Data Latency and Freshness")

    explain(
        "Data latency is the delay between an event occurring and that data "
        "becoming available to a consumer."
    )

    show_table(
        ["Pattern", "Typical concept", "Example"],
        [
            ["Batch", "Hours/days", "Nightly financial report"],
            ["Micro-batch", "Seconds/minutes", "Near-real-time dashboard"],
            ["Streaming", "Low latency", "Fraud monitoring"],
            ["Real time", "Very low latency", "Operational decision"],
        ]
    )

    explain(
        "Freshness requirements should come from business needs. A monthly board "
        "report may not need second-level freshness, while fraud detection may."
    )

    md_heading(1, "Data Latency and Freshness")
    md_text(
        "Data latency is the delay between an event occurring and the data becoming "
        "available to a consumer."
    )

    md_table(
        ["Pattern", "Typical Concept", "Example"],
        [
            ["Batch", "Hours/days", "Nightly financial report"],
            ["Micro-batch", "Seconds/minutes", "Near-real-time dashboard"],
            ["Streaming", "Low latency", "Fraud monitoring"],
            ["Real time", "Very low latency", "Operational decision"],
        ]
    )


# ============================================================================
# 25. DATA VOLUME, VELOCITY, VARIETY
# ============================================================================

def lesson_25_big_data_characteristics() -> None:
    section("25", "Volume, Velocity, Variety, and Related Characteristics")

    explain(
        "Data architecture is influenced by several characteristics often "
        "associated with the concept of big data."
    )

    bullet(
        "Volume: the amount of data stored or processed."
    )
    bullet(
        "Velocity: the rate at which data is generated or arrives."
    )
    bullet(
        "Variety: the diversity of data formats and structures."
    )
    bullet(
        "Veracity: the reliability and quality of data."
    )
    bullet(
        "Value: the useful business or analytical information that can be extracted."
    )

    md_heading(1, "Data Characteristics")
    for item in [
        "Volume: amount of data.",
        "Velocity: rate at which data arrives.",
        "Variety: diversity of formats and structures.",
        "Veracity: reliability and quality.",
        "Value: useful information derived from the data.",
    ]:
        md_bullet(item)


# ============================================================================
# 26. FILE FORMATS
# ============================================================================

def lesson_26_file_formats() -> None:
    section("26", "Important Data File Formats")

    explain(
        "Different file formats have different storage, interoperability, "
        "compression, schema, and query characteristics."
    )

    formats = [
        ["CSV", "Tabular text", "Simple exchange", "Poor for complex types"],
        ["JSON", "Nested key-value", "APIs/events", "Can be verbose"],
        ["XML", "Tagged hierarchical", "Enterprise integration", "Verbose"],
        ["Parquet", "Columnar", "Analytics", "Less human-readable"],
        ["Avro", "Row-oriented binary", "Data pipelines", "Requires tooling"],
        ["Excel", "Spreadsheet", "Business users", "Scalability/governance"],
    ]

    show_table(
        ["Format", "Structure", "Common use", "Limitation"],
        formats
    )

    subsection("Columnar vs row-oriented storage")

    explain(
        "Row-oriented storage keeps related fields for a record close together. "
        "It is often useful for transactional access. Columnar storage organizes "
        "values by column, which can be highly efficient for analytical queries "
        "that read only selected columns across many rows."
    )

    md_heading(1, "Important Data File Formats")
    md_table(
        ["Format", "Structure", "Common Use", "Limitation"],
        formats
    )

    md_heading(2, "Row vs Columnar Storage")
    md_text(
        "Row-oriented storage keeps fields for a record together and is often "
        "useful for transactional access. Columnar storage groups values by "
        "column and can be efficient for analytical workloads that scan selected "
        "columns across many rows."
    )


# ============================================================================
# 27. SEMANTIC LAYER
# ============================================================================

def lesson_27_semantic_layer() -> None:
    section("27", "Semantic Layer")

    explain(
        "A semantic layer provides a business-friendly representation of data "
        "and metrics. It can define concepts such as Revenue, Customer, Order, "
        "Gross Margin, and Active User so that different reports use consistent "
        "definitions."
    )

    subsection("Example")

    code_block("""
Revenue =
SUM(sales_amount - discount_amount - returns_amount)

Active Customer =
customer with at least one qualifying transaction
within the defined reporting period.
""")

    explain(
        "The purpose is not simply technical convenience. A semantic layer "
        "helps connect technical data structures with business language."
    )

    md_heading(1, "Semantic Layer")
    md_text(
        "A semantic layer provides a business-friendly representation of data "
        "and metrics. It can define shared concepts such as Revenue, Customer, "
        "Order, Gross Margin, and Active User."
    )


# ============================================================================
# 28. SECURITY
# ============================================================================

def lesson_28_security() -> None:
    section("28", "Security in the Data Analytics Ecosystem")

    explain(
        "Data systems must protect information from unauthorized access, alteration, "
        "loss, and misuse."
    )

    bullet("Authentication: who are you?")
    bullet("Authorization: what are you allowed to do?")
    bullet("Encryption at rest: protects stored data.")
    bullet("Encryption in transit: protects data moving between systems.")
    bullet("Role-based access control: permissions based on roles.")
    bullet("Column-level security: controls sensitive columns.")
    bullet("Row-level security: controls access to particular rows.")
    bullet("Audit logging: records access and changes.")
    bullet("Data masking: hides sensitive values.")
    bullet("Retention policies: control how long data is retained.")

    md_heading(1, "Security")
    md_text(
        "Data systems must protect information from unauthorized access, alteration, "
        "loss, and misuse."
    )

    for item in [
        "Authentication: who are you?",
        "Authorization: what are you allowed to do?",
        "Encryption at rest.",
        "Encryption in transit.",
        "Role-based access control.",
        "Column-level security.",
        "Row-level security.",
        "Audit logging.",
        "Data masking.",
        "Retention policies.",
    ]:
        md_bullet(item)


# ============================================================================
# 29. DATA ARCHITECTURE PATTERNS
# ============================================================================

def lesson_29_patterns() -> None:
    section("29", "Common Data Architecture Patterns")

    subsection("Pattern A: Operational database to warehouse")

    code_block("""
OLTP database
      |
      v
   ETL/CDC
      |
      v
Data warehouse
      |
      v
BI dashboards
""")

    subsection("Pattern B: Multi-source lake and warehouse")

    code_block("""
ERP ----\
CRM -----\
API ------> Data Lake ---> Transform ---> Warehouse ---> BI
Files ----/
Logs ----/
""")

    subsection("Pattern C: Streaming analytics")

    code_block("""
Application events
       |
       v
Streaming ingestion
       |
       +----------> Real-time analytics
       |
       +----------> Data lake
                         |
                         v
                    Historical analysis
""")

    subsection("Pattern D: Lakehouse")

    code_block("""
Sources
   |
   v
Object storage
   |
   v
Managed analytical tables
   |
   +--------> BI
   +--------> SQL
   +--------> ML
   +--------> Data science
""")

    md_heading(1, "Common Data Architecture Patterns")

    md_heading(2, "Operational Database to Warehouse")
    md_code("""
OLTP -> ETL/CDC -> Data Warehouse -> BI
""")

    md_heading(2, "Multi-Source Architecture")
    md_code("""
ERP + CRM + APIs + Files + Logs
              |
              v
          Data Lake
              |
              v
         Transformation
              |
              v
        Data Warehouse
              |
              v
              BI
""")

    md_heading(2, "Streaming Architecture")
    md_code("""
Application events
       |
       v
Streaming ingestion
       |
       +--> Real-time analytics
       |
       +--> Data lake
""")

    md_heading(2, "Lakehouse")
    md_code("""
Sources -> Object Storage -> Analytical Tables
                              |
                              +--> BI
                              +--> SQL
                              +--> ML
""")


# ============================================================================
# 30. DATA WAREHOUSE VS DATA LAKE
# ============================================================================

def lesson_30_warehouse_vs_lake() -> None:
    section("30", "Data Warehouse vs Data Lake")

    comparison = [
        ["Primary purpose", "Curated analytics", "Broad data storage"],
        ["Data state", "Usually transformed", "Often raw or lightly processed"],
        ["Data types", "Mostly structured", "Structured + semi + unstructured"],
        ["Schema", "Often schema-on-write", "Often schema-on-read"],
        ["Typical users", "BI/analysts", "Engineers/data scientists/analysts"],
        ["Querying", "Strong SQL analytics", "Varied processing/query engines"],
        ["Historical raw retention", "Not always", "Common"],
    ]

    show_table(
        ["Dimension", "Warehouse", "Lake"],
        comparison
    )

    md_heading(1, "Data Warehouse vs Data Lake")
    md_table(
        ["Dimension", "Warehouse", "Lake"],
        comparison
    )


# ============================================================================
# 31. TRANSACTIONAL VS ANALYTICAL DATA EXAMPLE
# ============================================================================

def lesson_31_transaction_analysis() -> None:
    section("31", "Why the Same Business Data Looks Different in OLTP and OLAP")

    explain(
        "Suppose an online store receives an order containing three products."
    )

    subsection("Operational representation")

    code_block("""
orders
------
order_id
customer_id
order_timestamp
payment_status
shipping_address

order_items
-----------
order_id
product_id
quantity
unit_price
""")

    explain(
        "This structure supports application operations such as creating an "
        "order, updating payment status, and retrieving an order."
    )

    subsection("Analytical representation")

    code_block("""
sales_fact
----------
date_key
customer_key
product_key
channel_key
quantity
gross_sales
discount
net_sales
cost
profit
""")

    explain(
        "The analytical model is designed around business questions. Analysts "
        "can aggregate sales by customer, product, date, channel, region, "
        "or other dimensions."
    )

    md_heading(1, "Transactional vs Analytical Representation")
    md_text(
        "The same business activity may be represented differently in operational "
        "and analytical systems because the systems optimize for different workloads."
    )

    md_heading(2, "Operational Model")
    md_code("""
orders
order_items
customers
products
payments
""")

    md_heading(2, "Analytical Model")
    md_code("""
sales_fact
customer_dimension
product_dimension
date_dimension
channel_dimension
""")


# ============================================================================
# 32. DATA DISCOVERY EXERCISE
# ============================================================================

def lesson_32_classification_exercise() -> None:
    section("32", "Data Classification Exercise")

    examples = [
        ("Customer table in PostgreSQL", "Structured"),
        ("REST API JSON response", "Semi-structured"),
        ("Excel sales workbook", "Structured"),
        ("Server log in JSON", "Semi-structured"),
        ("PDF invoice", "Unstructured"),
        ("MP4 product demonstration", "Unstructured"),
        ("CSV transaction file", "Structured"),
        ("XML business document", "Semi-structured"),
        ("Customer support call recording", "Unstructured"),
        ("Relational order table", "Structured"),
    ]

    for i, (example, answer) in enumerate(examples, start=1):
        numbered(i, f"{example} -> {answer}")

    md_heading(1, "Data Classification Exercise")
    md_table(
        ["Example", "Classification"],
        examples
    )


# ============================================================================
# 33. PRACTICAL PYTHON EXAMPLE: CLASSIFYING DATA
# ============================================================================

def lesson_33_python_classification() -> None:
    section("33", "Practical Python: Basic Data Classification")

    explain(
        "A data analyst often has to inspect incoming data and determine its "
        "likely structure before designing an ingestion or transformation process."
    )

    sample_records = [
        {"name": "Ravi", "age": 31, "city": "Lucknow"},
        {"name": "Neha", "age": 28, "city": "Delhi"},
    ]

    sample_json = json.dumps(sample_records, indent=4)

    code_block(f"""
Structured Python records:
{sample_records}

JSON representation:
{sample_json}
""")

    explain(
        "A Python dictionary can represent semi-structured information because "
        "keys can vary and nested objects can exist. A list of dictionaries is "
        "often a convenient representation for JSON-like data."
    )

    md_heading(1, "Practical Python: Data Classification")
    md_text(
        "A data analyst often inspects incoming data to determine its structure "
        "before designing an ingestion or transformation process."
    )

    md_code("""
records = [
    {"name": "Ravi", "age": 31, "city": "Lucknow"},
    {"name": "Neha", "age": 28, "city": "Delhi"}
]
""", "python")


# ============================================================================
# 34. PRACTICAL PYTHON EXAMPLE: CSV
# ============================================================================

def lesson_34_csv() -> None:
    section("34", "Practical Python: Working with CSV Data")

    csv_data = """customer_id,name,city,amount
101,Ravi,Lucknow,1200
102,Neha,Delhi,1800
103,Arjun,Mumbai,900
"""

    reader = csv.DictReader(io.StringIO(csv_data))
    rows = list(reader)

    print("CSV input:")
    print(csv_data)

    print("Parsed records:")
    for row in rows:
        print(row)

    total = sum(float(row["amount"]) for row in rows)

    print(f"\nTotal amount: {total}")

    md_heading(1, "Practical Python: CSV")
    md_text(
        "CSV is a simple tabular text format commonly used for exchanging "
        "structured data between systems."
    )

    md_code(csv_data, "csv")

    md_text(
        "The Python standard library can parse CSV data using the csv module."
    )


# ============================================================================
# 35. PRACTICAL PYTHON EXAMPLE: JSON
# ============================================================================

def lesson_35_json() -> None:
    section("35", "Practical Python: Working with JSON")

    payload = {
        "customer_id": 101,
        "name": "Ravi",
        "preferences": {
            "language": "English",
            "notifications": True
        },
        "orders": [
            {"id": 5001, "amount": 1200},
            {"id": 5002, "amount": 850}
        ]
    }

    serialized = json.dumps(payload, indent=4)

    print("JSON payload:")
    print(serialized)

    parsed = json.loads(serialized)

    print("\nCustomer:", parsed["name"])
    print("Number of orders:", len(parsed["orders"]))

    md_heading(1, "Practical Python: JSON")
    md_text(
        "JSON is widely used in APIs and event-based systems because it supports "
        "nested structures and flexible fields."
    )
    md_code(serialized, "json")


# ============================================================================
# 36. DATA CONTRACTS
# ============================================================================

def lesson_36_data_contracts() -> None:
    section("36", "Data Contracts")

    explain(
        "A data contract is an explicit agreement between a producer and consumer "
        "about the structure, meaning, quality, and expected behavior of shared data."
    )

    subsection("A contract can define")

    bullet("Field names")
    bullet("Data types")
    bullet("Required fields")
    bullet("Allowed values")
    bullet("Meaning of fields")
    bullet("Nullability")
    bullet("Expected frequency")
    bullet("Quality requirements")
    bullet("Versioning rules")

    code_block("""
OrderEvent

order_id: string
customer_id: string
amount: decimal
currency: string
created_at: timestamp

Required:
    order_id
    customer_id
    amount
    currency
    created_at
""")

    explain(
        "Data contracts reduce accidental breaking changes between independent "
        "teams and systems."
    )

    md_heading(1, "Data Contracts")
    md_text(
        "A data contract is an explicit agreement between a producer and consumer "
        "about the structure, meaning, quality, and expected behavior of shared data."
    )

    md_heading(2, "Common Contract Elements")
    for item in [
        "Field names",
        "Data types",
        "Required fields",
        "Allowed values",
        "Business meaning",
        "Nullability",
        "Expected frequency",
        "Quality requirements",
        "Versioning rules",
    ]:
        md_bullet(item)


# ============================================================================
# 37. SCHEMA EVOLUTION
# ============================================================================

def lesson_37_schema_evolution() -> None:
    section("37", "Schema Evolution")

    explain(
        "Schema evolution occurs when the structure of data changes over time."
    )

    subsection("Example")

    code_block("""
Version 1:
customer_id
name
email

Version 2:
customer_id
name
email
phone

Version 3:
customer_id
full_name
email
phone
""")

    explain(
        "Adding a nullable field is often easier to handle than renaming or "
        "changing the meaning of an existing field. A field rename can break "
        "downstream transformations, dashboards, applications, and data models."
    )

    subsection("Common schema changes")

    bullet("Add a field")
    bullet("Remove a field")
    bullet("Rename a field")
    bullet("Change data type")
    bullet("Change nullability")
    bullet("Change semantic meaning")

    md_heading(1, "Schema Evolution")
    md_text(
        "Schema evolution occurs when the structure of a dataset changes over time."
    )

    md_heading(2, "Common Schema Changes")
    for item in [
        "Add a field",
        "Remove a field",
        "Rename a field",
        "Change a data type",
        "Change nullability",
        "Change semantic meaning",
    ]:
        md_bullet(item)


# ============================================================================
# 38. DIMENSIONAL MODELING
# ============================================================================

def lesson_38_dimensional_modeling() -> None:
    section("38", "Dimensional Modeling")

    explain(
        "Dimensional modeling organizes analytical data around facts and dimensions."
    )

    subsection("Fact")

    explain(
        "A fact usually represents a measurable event or state."
    )

    bullet("Sales amount")
    bullet("Quantity sold")
    bullet("Cost")
    bullet("Units shipped")
    bullet("Number of clicks")

    subsection("Dimension")

    explain(
        "A dimension provides descriptive context for facts."
    )

    bullet("Customer")
    bullet("Product")
    bullet("Date")
    bullet("Location")
    bullet("Channel")

    subsection("Measures")

    explain(
        "Measures are numeric values that can be aggregated, such as SUM(sales), "
        "COUNT(orders), AVG(price), or MAX(delivery_time)."
    )

    md_heading(1, "Dimensional Modeling")
    md_text(
        "Dimensional modeling organizes analytical data around facts and dimensions."
    )

    md_heading(2, "Facts")
    md_text(
        "Facts represent measurable business events or states, such as sales "
        "amount, quantity sold, cost, or units shipped."
    )

    md_heading(2, "Dimensions")
    md_text(
        "Dimensions provide descriptive context such as customer, product, date, "
        "location, and channel."
    )

    md_heading(2, "Measures")
    md_text(
        "Measures are numeric values that can be aggregated, such as SUM(sales), "
        "COUNT(orders), AVG(price), or MAX(delivery_time)."
    )


# ============================================================================
# 39. SCD
# ============================================================================

def lesson_39_scd() -> None:
    section("39", "Slowly Changing Dimensions")

    explain(
        "Slowly Changing Dimensions, commonly called SCDs, describe techniques "
        "for managing changes to dimension attributes over time."
    )

    subsection("Type 1")

    explain(
        "Type 1 overwrites the previous value. Historical values are not preserved."
    )

    subsection("Type 2")

    explain(
        "Type 2 creates a new dimension record for the changed version and "
        "retains historical records."
    )

    code_block("""
customer_key | customer_id | city     | valid_from | valid_to
1            | C100        | Lucknow  | 2025-01-01 | 2026-03-10
2            | C100        | Delhi    | 2026-03-11 | NULL
""")

    subsection("Type 3")

    explain(
        "Type 3 stores limited previous-state information, often through current "
        "and previous columns."
    )

    md_heading(1, "Slowly Changing Dimensions")
    md_text(
        "SCD techniques manage changes to dimension attributes over time."
    )

    md_heading(2, "Type 1")
    md_text(
        "Overwrite the previous value. Historical values are not preserved."
    )

    md_heading(2, "Type 2")
    md_text(
        "Create a new dimension record for a changed version while preserving "
        "historical records."
    )

    md_code("""
customer_key | customer_id | city
1            | C100        | Lucknow
2            | C100        | Delhi
""")

    md_heading(2, "Type 3")
    md_text(
        "Store limited previous-state information, often through current and "
        "previous value columns."
    )


# ============================================================================
# 40. DATA LAKEHOUSE FILE ORGANIZATION
# ============================================================================

def lesson_40_storage_organization() -> None:
    section("40", "Partitioning and Storage Organization")

    explain(
        "Large analytical datasets are often organized into partitions. "
        "Partitioning divides data according to selected attributes such as "
        "date, region, or business unit."
    )

    code_block("""
sales/
    year=2026/
        month=01/
        month=02/
        month=03/
    year=2025/
        month=11/
        month=12/
""")

    explain(
        "If a query only needs March 2026, a well-designed system may avoid "
        "reading unrelated partitions. This can reduce the amount of data scanned."
    )

    subsection("Partitioning vs indexing")

    explain(
        "Partitioning physically or logically divides data into larger sections, "
        "while indexes provide structures that help locate rows or values efficiently. "
        "The exact behavior depends on the database or storage engine."
    )

    md_heading(1, "Partitioning")
    md_text(
        "Partitioning divides large datasets according to attributes such as "
        "date, region, or business unit."
    )

    md_code("""
sales/
    year=2026/
        month=01/
        month=02/
        month=03/
""")

    md_text(
        "When a query filters on the partitioning columns, a system may be able "
        "to avoid scanning unrelated partitions."
    )


# ============================================================================
# 41. QUERY PROCESSING
# ============================================================================

def lesson_41_query_processing() -> None:
    section("41", "Query Processing in Analytical Systems")

    explain(
        "Analytical query engines attempt to read only the data necessary to "
        "answer a query and process it efficiently."
    )

    subsection("Column pruning")

    explain(
        "If a query needs only three columns from a table containing fifty columns, "
        "a columnar engine may avoid reading the other columns."
    )

    subsection("Predicate pushdown")

    explain(
        "Predicate pushdown means applying filters as close as possible to the "
        "storage layer so unnecessary data can be eliminated early."
    )

    subsection("Partition pruning")

    explain(
        "Partition pruning allows the engine to skip partitions that cannot "
        "contain relevant records."
    )

    subsection("Aggregation")

    explain(
        "Analytical systems frequently aggregate large datasets using operations "
        "such as SUM, COUNT, AVG, MIN, and MAX."
    )

    md_heading(1, "Query Processing")
    md_text(
        "Analytical query engines optimize queries by reducing unnecessary data "
        "movement and computation."
    )

    md_heading(2, "Column Pruning")
    md_text(
        "Column pruning avoids reading columns that are not required by a query."
    )

    md_heading(2, "Predicate Pushdown")
    md_text(
        "Predicate pushdown applies filters as close to the storage layer as practical."
    )

    md_heading(2, "Partition Pruning")
    md_text(
        "Partition pruning skips partitions that cannot contain relevant records."
    )


# ============================================================================
# 42. DATA CATALOG
# ============================================================================

def lesson_42_catalog() -> None:
    section("42", "Data Catalog")

    explain(
        "A data catalog is an organized inventory of data assets. It helps users "
        "discover datasets and understand their meaning, ownership, lineage, "
        "quality, and usage."
    )

    subsection("A catalog entry might contain")

    bullet("Dataset name")
    bullet("Description")
    bullet("Owner")
    bullet("Business domain")
    bullet("Columns")
    bullet("Data types")
    bullet("Sensitivity classification")
    bullet("Lineage")
    bullet("Quality information")
    bullet("Usage statistics")

    md_heading(1, "Data Catalog")
    md_text(
        "A data catalog is an inventory of data assets that helps users discover "
        "and understand datasets."
    )

    for item in [
        "Dataset name",
        "Description",
        "Owner",
        "Business domain",
        "Columns",
        "Data types",
        "Sensitivity classification",
        "Lineage",
        "Quality information",
        "Usage statistics",
    ]:
        md_bullet(item)


# ============================================================================
# 43. DATA DOMAIN CONCEPT
# ============================================================================

def lesson_43_domains() -> None:
    section("43", "Data Domains")

    explain(
        "A data domain is a logical business area whose data has related meaning "
        "and ownership. Common domains include Customer, Product, Finance, Sales, "
        "Supply Chain, Employee, and Marketing."
    )

    code_block("""
Organization
|
+-- Customer domain
|
+-- Product domain
|
+-- Finance domain
|
+-- Sales domain
|
+-- Supply Chain domain
|
+-- Employee domain
""")

    explain(
        "Domain-oriented organization can clarify ownership and make governance "
        "responsibilities more explicit."
    )

    md_heading(1, "Data Domains")
    md_text(
        "A data domain is a logical business area containing related data and "
        "typically associated ownership. Examples include Customer, Product, "
        "Finance, Sales, Supply Chain, Employee, and Marketing."
    )


# ============================================================================
# 44. DATA ANALYTICS ECOSYSTEM MAP
# ============================================================================

def lesson_44_ecosystem_map() -> None:
    section("44", "Complete Data Analytics Ecosystem Map")

    code_block("""
                         BUSINESS ACTIVITY
                                |
          +---------------------+---------------------+
          |                     |                     |
          v                     v                     v
        ERP                    CRM                  Website
          |                     |                     |
          +----------+----------+----------+----------+
                     |
                     v
              DATA INGESTION
        +------------+-------------+
        |            |             |
       APIs         CDC          Files
        |            |             |
        +------------+-------------+
                     |
                     v
              DATA STORAGE
        +------------+-------------+
        |            |             |
        v            v             v
   Operational    Data Lake     Warehouse
    Database                     / Lakehouse
        |            |             |
        +------------+-------------+
                     |
                     v
              DATA PROCESSING
                     |
              +------+------+
              |             |
              v             v
         Transformation   Quality
              |             |
              +------+------+
                     |
                     v
               DATA MODELS
                     |
                     v
              SEMANTIC LAYER
                     |
          +----------+----------+
          |          |          |
          v          v          v
         BI         SQL         ML
          |          |          |
          +----------+----------+
                     |
                     v
              BUSINESS DECISIONS

Cross-cutting:
Security | Governance | Metadata | Lineage | Quality | Catalog
""")

    md_heading(1, "Complete Data Analytics Ecosystem Map")
    md_code("""
Business Activity
       |
       v
ERP / CRM / Website / POS / APIs / Files / Logs
       |
       v
Data Ingestion
       |
       +--> Batch
       +--> CDC
       +--> Streaming
       +--> APIs
       +--> Files
       |
       v
Storage
       |
       +--> Operational databases
       +--> Data lake
       +--> Data warehouse
       +--> Lakehouse
       |
       v
Processing
       |
       +--> Validation
       +--> Cleaning
       +--> Transformation
       +--> Integration
       |
       v
Analytical Models
       |
       v
Semantic Layer
       |
       +--> BI
       +--> SQL
       +--> Data Science
       +--> Machine Learning
       |
       v
Business Decisions

Cross-cutting:
Security | Governance | Metadata | Lineage | Quality | Catalog
""")


# ============================================================================
# 45. KNOWLEDGE CHECKS
# ============================================================================

def lesson_45_knowledge_checks() -> None:
    section("45", "Knowledge Checks")

    questions = [
        (
            "Why is an OLTP database generally not the ideal place for large "
            "analytical queries?",
            "Because OLTP systems are optimized for operational transactions, "
            "while large analytical queries can consume resources and interfere "
            "with operational workloads."
        ),
        (
            "What is the main distinction between a data warehouse and a data lake?",
            "A warehouse is primarily a curated analytical environment, while a "
            "lake is designed to store large amounts of varied data, often closer "
            "to its original form."
        ),
        (
            "What does schema-on-read mean?",
            "The structure can be applied when data is consumed or processed rather "
            "than requiring the final rigid schema before storage."
        ),
        (
            "Why are APIs important data sources?",
            "They provide defined interfaces through which systems can exchange data."
        ),
        (
            "What is data lineage?",
            "Information describing where data originated, how it changed, and where "
            "it was consumed."
        ),
        (
            "What is the grain of a fact table?",
            "The exact business meaning of one row in the fact table."
        ),
        (
            "Why are spreadsheets risky as enterprise data sources?",
            "They can introduce manual errors, version confusion, weak governance, "
            "inconsistent structures, and scalability problems."
        ),
        (
            "What is CDC?",
            "Change Data Capture identifies changes such as inserts, updates, and "
            "deletes in source systems for downstream processing."
        ),
        (
            "What is semi-structured data?",
            "Data with organizational information such as keys, tags, or nesting "
            "without requiring one rigid relational schema."
        ),
        (
            "What is a data warehouse primarily optimized for?",
            "Analytical queries, reporting, aggregation, and historical analysis."
        ),
    ]

    for i, (question, answer) in enumerate(questions, start=1):
        print(f"\nQuestion {i}:")
        explain(question)
        print(f"Answer: {answer}")

    md_heading(1, "Knowledge Checks")

    for i, (question, answer) in enumerate(questions, start=1):
        md_heading(3, f"Question {i}")
        md_text(question)
        md_text(f"**Answer:** {answer}")


# ============================================================================
# 46. TERMINOLOGY REFERENCE
# ============================================================================

def lesson_46_terminology() -> None:
    section("46", "Terminology Reference")

    terms = [
        ["API", "Interface used by systems to communicate."],
        ["CDC", "Change Data Capture."],
        ["Database", "System for organized storage and retrieval of data."],
        ["Data Lake", "Flexible large-scale storage for varied data."],
        ["Data Warehouse", "Analytical storage for curated integrated data."],
        ["Data Mart", "Focused analytical data store."],
        ["ETL", "Extract, Transform, Load."],
        ["ELT", "Extract, Load, Transform."],
        ["Fact", "Analytical representation of measurable business events."],
        ["Dimension", "Descriptive context surrounding facts."],
        ["OLTP", "Online Transaction Processing."],
        ["OLAP", "Online Analytical Processing."],
        ["Metadata", "Information about data."],
        ["Lineage", "Origin and transformation path of data."],
        ["Schema", "Defined structure of data."],
        ["Grain", "Meaning represented by one analytical row."],
        ["Batch", "Data processed in groups at intervals."],
        ["Streaming", "Continuous or near-continuous event processing."],
        ["Lakehouse", "Architecture combining lake storage with analytical capabilities."],
        ["Data Catalog", "Inventory and description of data assets."],
    ]

    show_table(["Term", "Meaning"], terms)

    md_heading(1, "Terminology Reference")
    md_table(["Term", "Meaning"], terms)


# ============================================================================
# MARKDOWN FILE WRITER
# ============================================================================

def write_markdown_file(filename: str = "data_analytics_ecosystem_notes.md") -> None:
    content = "\n".join(markdown_sections)

    header = """# Data Analytics Ecosystem

## Scope

These notes cover the data analytics ecosystem from basic concepts through
analytical architecture, including data sources, databases, data warehouses,
data lakes, APIs, spreadsheets, business applications, transactional systems,
analytical systems, data types, ingestion, transformation, modeling,
governance, metadata, security, and related architectural concepts.

"""

    with open(filename, "w", encoding="utf-8") as file:
        file.write(header)
        file.write(content)

    print()
    line("=")
    print(f"Markdown notes written to: {filename}")
    line("=")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main() -> None:
    print()
    line("=")
    print("DATA ANALYTICS ECOSYSTEM".center(WIDTH))
    print("Comprehensive Python Study Module".center(WIDTH))
    line("=")

    lessons = [
        lesson_1_introduction,
        lesson_2_data_sources,
        lesson_3_data_types,
        lesson_4_databases,
        lesson_5_oltp,
        lesson_6_olap,
        lesson_7_data_warehouse,
        lesson_8_data_lake,
        lesson_9_lakehouse,
        lesson_10_apis,
        lesson_11_spreadsheets,
        lesson_12_business_applications,
        lesson_13_etl_elt,
        lesson_14_ingestion,
        lesson_15_pipelines,
        lesson_16_data_quality,
        lesson_17_governance,
        lesson_18_metadata,
        lesson_19_data_modeling,
        lesson_20_integration,
        lesson_21_storage_layers,
        lesson_22_case_study,
        lesson_23_tradeoffs,
        lesson_24_latency,
        lesson_25_big_data_characteristics,
        lesson_26_file_formats,
        lesson_27_semantic_layer,
        lesson_28_security,
        lesson_29_patterns,
        lesson_30_warehouse_vs_lake,
        lesson_31_transaction_analysis,
        lesson_32_classification_exercise,
        lesson_33_python_classification,
        lesson_34_csv,
        lesson_35_json,
        lesson_36_data_contracts,
        lesson_37_schema_evolution,
        lesson_38_dimensional_modeling,
        lesson_39_scd,
        lesson_40_storage_organization,
        lesson_41_query_processing,
        lesson_42_catalog,
        lesson_43_domains,
        lesson_44_ecosystem_map,
        lesson_45_knowledge_checks,
        lesson_46_terminology,
    ]

    for lesson in lessons:
        lesson()

    write_markdown_file()

    print()
    line("=")
    print("END OF DATA ANALYTICS ECOSYSTEM MODULE".center(WIDTH))
    line("=")


if __name__ == "__main__":
    main()
