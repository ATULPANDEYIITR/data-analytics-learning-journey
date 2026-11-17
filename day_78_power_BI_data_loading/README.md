# Power BI Data Loading

## 1. Introduction

Power BI Data Loading is the process of connecting to external data sources, retrieving records, preparing the data, and making it available to a Power BI semantic model for analysis and reporting.

A Power BI report is only as reliable as the data supplied to its semantic model. Data loading therefore involves more than selecting a file or establishing a connection. It requires decisions about source compatibility, authentication, data structure, transformations, refresh frequency, storage modes, data quality, and performance.

The implementations in this project demonstrate a complete data-loading workflow using Python, JavaScript, C++17, Java 17, and PostgreSQL.

The five implementations approach the same subject from different engineering perspectives:

| Implementation | Primary purpose |
|---|---|
| Python | Multi-source ingestion, transformation, validation, and reporting |
| JavaScript | Event-driven connection management and refresh orchestration |
| C++17 | Efficient source processing and data-loading architecture |
| Java 17 | Enterprise-oriented connection governance and refresh management |
| PostgreSQL | Relational storage, data-quality enforcement, refresh tracking, and reporting |

The implementations simulate the data-loading concepts associated with Power BI. They do not invoke the Power BI Desktop application or Power BI Service APIs.

---

## 2. Understanding Data Loading

Data loading moves information from a source system into an analytical environment.

The general workflow is:

Source System
    |
    v
Data Connection
    |
    v
Data Extraction
    |
    v
Data Validation
    |
    v
Data Transformation
    |
    v
Data Loading
    |
    v
Semantic Model
    |
    v
Reports and Dashboards

Each stage has a different responsibility.

| Stage | Purpose |
|---|---|
| Source system | Stores original information |
| Connection | Establishes access to the source |
| Extraction | Retrieves source records |
| Validation | Identifies incorrect or incomplete records |
| Transformation | Changes data into the required structure |
| Loading | Places prepared data into the analytical model |
| Semantic model | Organizes data for analytical queries |
| Reporting | Presents calculated results |

A failure at one stage can affect all subsequent stages.

For example, an Excel workbook may be accessible, but its worksheet may contain duplicate column names. The connection succeeds, while the data-validation stage fails.

This distinction is important when diagnosing data-loading problems.

---

## 3. Data Sources

Power BI supports multiple categories of data sources. Their connection mechanisms and operational requirements differ.

### 3.1 Excel

<text>Excel is commonly used for departmental reporting, financial records, operational tracking, and manually maintained datasets.</text>

<escape></escape>

An Excel workbook can contain:

- Worksheets
- Structured tables
- Formulas
- Named ranges
- PivotTables
- Multiple related datasets
- Date and numeric values
- Text and categorical fields

Power BI can connect to Excel workbooks and retrieve structured information.

A typical workflow is:

1. Select Excel as the source.
2. Locate the workbook.
3. Select the required worksheet or table.
4. Preview the available records.
5. Check column names and data types.
6. Apply required transformations.
7. Load the prepared dataset.

**Important distinction:** An Excel workbook and a CSV file are not equivalent.

Excel supports multiple worksheets, formulas, formatting, and workbook-level structures. CSV represents a single tabular dataset using delimiters and text values.

The Python implementation demonstrates XLSX reading through ZIP and XML processing. The JavaScript, C++17, and Java implementations demonstrate Excel-export ingestion using CSV-compatible files rather than implementing complete XLSX workbook parsing.

### 3.2 CSV

CSV stands for Comma-Separated Values.

It stores tabular data in text format.

Example:

| Product | Quantity | Revenue |
|---|---:|---:|
| Laptop | 5 | 250000 |
| Monitor | 8 | 120000 |
| Keyboard | 20 | 40000 |

CSV characteristics:

- Simple structure
- Small storage overhead
- Broad software compatibility
- Easy exchange between applications
- No built-in relationships
- No native worksheet structure
- No reliable storage of column data types

A CSV file does not guarantee that every record follows the same structure.

Common problems include:

- Missing columns
- Duplicate headers
- Incorrect delimiters
- Unclosed quotation marks
- Empty records
- Invalid numeric values
- Incorrect text encoding

The implementations validate the CSV structure before accepting records.

CSV parsing must account for quoted values. A product description containing a comma should not automatically create another column.

For example, a quoted value such as `"Laptop, Business Edition"` represents one field rather than two.

### 3.3 Databases

Databases provide structured access to information through tables, views, queries, and database-specific connection mechanisms.

Common database systems include:

- PostgreSQL
- Microsoft SQL Server
- MySQL
- Oracle Database
- SQLite

A database connection generally requires:

| Component | Purpose |
|---|---|
| Server | Database host |
| Database | Database name |
| Authentication | Establishes user identity |
| Schema | Organizes database objects |
| Table or view | Identifies the source dataset |
| Query | Retrieves required records |
| Permissions | Controls data access |

A database connection can retrieve selected columns instead of importing an entire table.

For example, a sales dataset may require only:

- Product
- Quantity
- Revenue
- Transaction date

Retrieving unnecessary columns increases network transfer, memory consumption, and processing requirements.

The Python implementation uses SQLite with read-only access.

The JavaScript and Java implementations define database adapter interfaces, allowing a real database driver to be connected without changing the main loading workflow.

The C++ implementation uses a database adapter with in-memory tables to demonstrate source abstraction.

The PostgreSQL implementation provides the relational model for managing connections, source tables, imported records, and refresh history.

### 3.4 Web Sources

Web sources supply information through network-based interfaces.

Typical examples include:

- REST APIs
- JSON endpoints
- Public datasets
- Government data services
- Enterprise applications
- Cloud-hosted services

A web connection generally involves:

1. Identifying the endpoint.
2. Configuring authentication where required.
3. Sending an HTTP request.
4. Receiving the response.
5. Parsing the returned structure.
6. Validating the records.
7. Transforming the data.
8. Loading the prepared information.

JSON is a common response format.

Example structure:

| Product | Quantity | Revenue |
|---|---:|---:|
| Tablet | 4 | 80000 |
| Phone | 10 | 200000 |

Web-source failures can include:

- Authentication failure
- Expired access tokens
- Network interruptions
- HTTP errors
- Invalid JSON
- API rate limits
- Response-size limits
- Changed endpoint structures

The Python and JavaScript implementations demonstrate HTTPS-based JSON retrieval with timeout and response-size controls.

The C++ and Java implementations demonstrate web connection validation and explicitly distinguish URL validation from actual HTTP transport.

---

## 4. Data Connections

A data connection defines how an analytical application accesses an external source.

It contains information about the source and the mechanism used to retrieve data.

A connection configuration can include:

| Property | Description |
|---|---|
| Connection ID | Unique connection identifier |
| Source type | Excel, CSV, database, or web |
| Location | File path, database location, or endpoint |
| Authentication | Credentials or authentication mechanism |
| Timeout | Maximum waiting period |
| Permissions | Authorized operations |
| Status | Active, inactive, failed, or disabled |
| Refresh settings | Conditions for retrieving updated information |

### 4.1 Connection and Dataset Are Different

A connection does not automatically represent a complete analytical dataset.

A single database connection can expose multiple tables.

Similarly, one Excel workbook can contain multiple worksheets.

The relationship can be represented as:

Data Connection
    |
    +---- Source Table A
    |
    +---- Source Table B
    |
    +---- Source Table C

This distinction is represented explicitly in the PostgreSQL implementation through `data_connections` and `source_tables`.

### 4.2 Connection Security

A connection should follow appropriate security controls.

Important controls include:

- Secure authentication
- Encrypted network communication
- Restricted source permissions
- Protected credential storage
- Read-only access where appropriate
- Connection ownership
- Refresh authorization
- Audit logging

Credentials should not be embedded directly in source files or stored as ordinary unprotected text.

The PostgreSQL implementation uses a `credentials_reference` field to represent a reference to a separately managed credential.

It does not store actual passwords.

The Python web connector restricts requests to HTTPS and applies response-size limits.

---

## 5. Power Query and Data Preparation

Power Query is the data preparation and transformation environment associated with Power BI.

It is used to retrieve, clean, combine, and reshape information before it is made available to the analytical model.

Common Power Query operations include:

| Operation | Purpose |
|---|---|
| Remove Columns | Eliminate unnecessary fields |
| Rename Columns | Standardize column names |
| Change Data Type | Assign appropriate data types |
| Filter Rows | Remove unwanted records |
| Remove Duplicates | Eliminate duplicate entries |
| Replace Values | Standardize inconsistent values |
| Split Columns | Separate combined information |
| Merge Queries | Combine related datasets horizontally |
| Append Queries | Combine datasets vertically |
| Group By | Aggregate records |
| Pivot Columns | Convert category values into columns |
| Unpivot Columns | Convert columns into attribute-value records |

### 5.1 Data Type Conversion

Data type conversion ensures that information is interpreted correctly.

Consider the following values:

| Source value | Required type |
|---|---|
| `"250000"` | Decimal number |
| `"5"` | Whole number |
| `"2026-11-17"` | Date |
| `"Laptop"` | Text |

A number stored as text cannot always be used correctly in mathematical calculations.

The implementations convert quantity and revenue into numeric values before generating reports.

### 5.2 Data Validation

Validation checks whether records satisfy predefined requirements.

The sales examples apply these rules:

- Product name cannot be empty.
- Quantity must be a non-negative integer.
- Revenue must be finite.
- Revenue cannot be negative.
- Required columns must exist.

Invalid records are rejected rather than silently included in calculations.

For larger enterprise datasets, validation can also cover:

- Unique transaction identifiers
- Referential integrity
- Date ranges
- Missing-value thresholds
- Currency consistency
- Expected category values
- Business-specific constraints

### 5.3 Data Transformation

Transformation converts source records into a consistent analytical structure.

For example:

Source A:

| Product | Quantity | Revenue |
|---|---:|---:|
| Laptop | 5 | 250000 |

Source B:

| product | quantity | revenue |
|---|---:|---:|
| Monitor | 8 | 120000 |

After standardization:

| product | quantity | revenue |
|---|---:|---:|
| Laptop | 5 | 250000 |
| Monitor | 8 | 120000 |

The objective is to provide a consistent structure regardless of the original source.

---

## 6. Power BI Storage Modes

Power BI uses different storage and connection modes to determine how information is accessed and maintained.

The three important modes are Import, DirectQuery, and Live Connection.

They are related to data access but are not interchangeable.

### 6.1 Import Mode

<badge color="success">Data stored in the semantic model</badge>

Import mode copies selected source data into the Power BI semantic model.

The imported data is stored in the model and can be queried without requesting every individual result from the original source.

Workflow:

External Source
    |
    v
Data Extraction
    |
    v
Power Query Transformations
    |
    v
Semantic Model Storage
    |
    v
Report Queries

Characteristics:

- Data is stored in the semantic model.
- Reports can query imported data without accessing the original source for every interaction.
- Refresh operations retrieve updated source data.
- Model size affects memory and capacity requirements.
- Data may become outdated between refreshes.

Advantages:

- Fast analytical queries for many workloads.
- Reduced dependence on the source during report interaction.
- Efficient analytical compression.
- Suitable for many reporting and dashboard scenarios.

Limitations:

- Requires storage capacity.
- Data must be refreshed to reflect source changes.
- Large datasets can increase refresh time.
- Refresh operations can consume processing resources.

The Python implementation uses `SemanticModel.import_data()` to replace a successfully loaded table.

The JavaScript implementation uses `SemanticModel.importTable()`.

The C++ and Java implementations use maps of table names to validated record collections.

The PostgreSQL implementation represents imported datasets using `sales_data`.

### 6.2 DirectQuery Mode

<badge color="info">Queries executed against the source</badge>

DirectQuery does not normally import the complete source dataset into the semantic model.

Instead, queries are translated and sent to the underlying source when data is requested.

Workflow:

Power BI Report
    |
    v
Semantic Model
    |
    v
Generated Source Query
    |
    v
Database
    |
    v
Query Result
    |
    v
Report Visualization

Characteristics:

- Source data remains in the underlying system.
- Queries are executed against the source.
- Results depend on source availability and performance.
- Query design and source indexing are important.
- Source permissions and connection configuration remain important.

Advantages:

- Avoids importing the complete dataset.
- Useful when data must remain in the source system.
- Supports scenarios requiring access to current source information.
- Can work with datasets larger than the available model memory.

Limitations:

- Source performance directly affects report responsiveness.
- Complex queries can create substantial database workloads.
- Network latency can affect report interactions.
- Some Power Query transformations and model features have limitations depending on the connector.

The implementations demonstrate DirectQuery-style behavior by retrieving source records again whenever the query operation is invoked.

This is a simulation, not an implementation of the complete Power BI DirectQuery protocol.

### 6.3 Live Connection

Live Connection connects a report to an existing external semantic model or supported analytical model.

The report consumes the existing model rather than independently importing its entire underlying dataset.

Workflow:

External Semantic Model
    |
    v
Live Connection
    |
    v
Power BI Report
    |
    v
Visualizations

Characteristics:

- An existing semantic model provides the analytical structure.
- The report uses the external model's existing definitions and measures.
- Model ownership and permissions remain important.
- Data refresh is generally managed by the underlying model.
- Report authors have different modeling capabilities depending on the connection type and supported features.

Advantages:

- Centralized analytical definitions.
- Reuse of existing business measures.
- Reduced duplication of model logic.
- Consistent reporting across departments.

Limitations:

- Dependence on the external model.
- Less independent control over underlying model structures.
- Permissions and availability of the external model affect report access.

The JavaScript, C++, and Java implementations validate the availability of an external model.

The PostgreSQL implementation represents external semantic model references through `external_model_reference`.

### 6.4 Comparison of Storage Modes

| Characteristic | Import | DirectQuery | Live Connection |
|---|---|---|---|
| Data storage | Imported into model | Remains in source | Managed by external model |
| Query execution | Local semantic model | Underlying source | External semantic model |
| Source dependency during interaction | Usually lower | High | Depends on external model |
| Refresh responsibility | Imported model | Source query behavior and supported refresh operations | Underlying model |
| Model flexibility | Broad | Connector-dependent | More restricted |
| Main consideration | Storage and refresh | Source query performance | External model governance |

A useful decision rule is to evaluate dataset size, source performance, freshness requirements, model complexity, and centralized governance requirements before choosing a storage mode.

---

## 7. Data Refresh

A refresh retrieves updated information from the source and updates the relevant analytical data.

A refresh is different from an individual report query.

In Import mode, refresh operations are particularly important because imported data represents a stored snapshot of source information.

A refresh workflow is:

Refresh Request
    |
    v
Connection Validation
    |
    v
Source Access
    |
    v
Data Extraction
    |
    v
Data Validation
    |
    v
Transformation
    |
    v
Load into Model
    |
    v
Refresh Audit
    |
    v
Completion or Failure

### 7.1 Refresh Types

Common refresh concepts include:

- Manual refresh
- Scheduled refresh
- On-demand refresh
- API-triggered refresh
- Incremental refresh

Incremental refresh processes an appropriate subset of data rather than repeatedly processing the entire historical dataset.

For example, a sales model containing several years of transactions may retain older historical partitions while refreshing recent periods.

### 7.2 Refresh Failures

Common failures include:

| Failure | Possible cause |
|---|---|
| Connection failure | Source unavailable |
| Authentication failure | Invalid or expired credentials |
| Timeout | Source response too slow |
| Schema failure | Column removed or renamed |
| Transformation failure | Invalid data values |
| Capacity failure | Insufficient available resources |
| Duplicate records | Incorrect loading or key management |

A production implementation should retain the previous valid dataset when a replacement refresh fails.

The Python, JavaScript, C++, and Java implementations follow the principle of validating incoming data before replacing an imported table.

The PostgreSQL implementation records refresh states and enforces completion rules through triggers.

### 7.3 Incremental Refresh Considerations

Incremental refresh generally depends on:

- A suitable date or time column
- Partition boundaries
- Historical retention requirements
- Recent-data refresh windows
- Source query support
- Appropriate filtering

The implementations focus on full-load simulations rather than implementing Power BI's actual partition management.

---

## 8. Data Loading Architecture

A reliable data-loading system separates source access from data preparation and model management.

The architecture used throughout the project is:

Source Adapter
    |
    v
Connection Manager
    |
    v
Data Extraction
    |
    v
Validation Engine
    |
    v
Transformation Engine
    |
    v
Storage Mode Manager
    |
    v
Semantic Model
    |
    v
Refresh History and Reporting

### 8.1 Source Adapter

An adapter provides a consistent interface for reading different source systems.

For example, CSV and database sources have different connection mechanisms.

A source adapter hides these differences from the main loading service.

This allows additional connectors to be introduced without redesigning the complete workflow.

### 8.2 Connection Manager

The connection manager maintains information about available sources.

It checks:

- Connection identity
- Source type
- Source location
- Connection availability
- Timeout configuration
- Enabled or disabled status

The JavaScript implementation uses a `Map` to maintain connection configurations.

The Python implementation uses dictionaries.

The Java implementation uses a concurrent registry.

The C++ implementation uses an unordered map.

### 8.3 Transformation Engine

The transformation engine prepares source data for analysis.

It performs:

- Column normalization
- Numeric conversion
- Required-field checks
- Invalid-record rejection
- Standardization

Separating transformation from source retrieval prevents connector-specific code from becoming responsible for all business rules.

### 8.4 Semantic Model

A semantic model organizes information for analysis.

It can contain:

- Tables
- Relationships
- Measures
- Calculated columns
- Hierarchies
- Formatting definitions
- Security rules

The project focuses on table storage and source-loading behavior rather than implementing the complete Power BI semantic model.

---

## 9. Python Implementation

### 9.1 Architecture

The Python implementation uses standard-library modules to demonstrate a complete local ingestion workflow.

Its main components are:

| Component | Responsibility |
|---|---|
| `DataConnection` | Stores connection configuration |
| `ConnectionManager` | Registers and retrieves connections |
| `SourceConnector` | Defines the connector interface |
| `CSVConnector` | Reads CSV files |
| `ExcelConnector` | Reads XLSX worksheets |
| `SQLiteConnector` | Retrieves database records |
| `JSONConnector` | Reads JSON datasets |
| `WebConnector` | Retrieves HTTPS JSON responses |
| `DataValidator` | Validates sales records |
| `SemanticModel` | Stores imported tables |
| `SalesAnalytics` | Generates analytical results |

### 9.2 Excel Processing

The XLSX reader uses Python's `zipfile` and `xml.etree.ElementTree`.

An XLSX workbook is a ZIP archive containing XML documents.

The implementation reads:

- Workbook metadata
- Workbook relationships
- Worksheet XML
- Shared strings

It then reconstructs a tabular representation.

This approach avoids external dependencies but does not provide the complete functionality of a dedicated Excel workbook library.

Complex workbook features such as formulas, styles, merged cells, and advanced date interpretation are outside its scope.

### 9.3 Database Processing

The SQLite connector opens the database in read-only mode.

It retrieves records through a SELECT statement.

This demonstrates the separation between database connectivity and data transformation.

### 9.4 Web Processing

The web connector:

- Requires HTTPS.
- Uses a configured timeout.
- Checks the response status.
- Validates the content type.
- Limits the response size.
- Parses JSON records.

### 9.5 Execution

The script creates sample files and a SQLite database.

It then registers the connections, loads the records, rejects invalid data, imports successful datasets, and generates a sales report.

Run the file using Python 3.10 or later.

---

## 10. JavaScript Implementation

The JavaScript implementation emphasizes asynchronous operations and event-driven processing.

Its architecture is suitable for Node.js applications that coordinate multiple data sources.

### 10.1 Main Components

| Component | Responsibility |
|---|---|
| `CSVParser` | Parses CSV data |
| `SalesTransformer` | Validates and transforms records |
| `DatabaseAdapter` | Defines database access |
| `WebSource` | Retrieves HTTPS JSON |
| `ConnectionRegistry` | Maintains connection configurations |
| `DataSourceDispatcher` | Selects the appropriate connector |
| `SemanticModel` | Manages imported datasets |
| `RefreshCoordinator` | Coordinates refresh operations |
| `SalesReport` | Calculates analytical metrics |

### 10.2 Asynchronous Processing

JavaScript uses asynchronous functions and Promises to avoid blocking the application while waiting for external sources.

For example, a web request may take several seconds.

An asynchronous loading operation allows other application activities to continue while the request is being processed.

### 10.3 Event-Driven Refresh

The refresh coordinator extends `EventEmitter`.

It publishes events such as:

- `refreshStarted`
- `refreshCompleted`
- `refreshFailed`
- `tableImported`

These events can be consumed by monitoring systems, logging services, or application interfaces.

### 10.4 Concurrent Refresh Protection

The coordinator maintains an active-refresh set.

This prevents the same connection from being refreshed simultaneously through the same coordinator instance.

The active identifier is removed in a `finally` block, ensuring that a failed operation does not permanently block subsequent refreshes.

### 10.5 Database Integration

The database adapter demonstrates a read-only interface.

The in-memory adapter provides executable sample behavior without requiring an external database driver.

A real PostgreSQL or SQL Server connection would require a corresponding driver and a properly configured authentication mechanism.

### 10.6 Excel Limitation

The JavaScript implementation accepts CSV-exported Excel data.

It does not parse the XLSX ZIP/XML format.

A production XLSX connector would require a dedicated workbook parser.

---

## 11. C++17 Implementation

The C++17 implementation emphasizes structured domain modeling, source abstraction, validation, and predictable resource management.

### 11.1 Main Components

| Component | Responsibility |
|---|---|
| `SalesRecord` | Represents a validated sales record |
| `DataConnection` | Represents source configuration |
| `CSVReader` | Reads CSV data |
| `DataValidator` | Rejects invalid records |
| `SourceAdapter` | Defines source access |
| `FileSourceAdapter` | Reads file-based data |
| `DatabaseSourceAdapter` | Simulates database retrieval |
| `ConnectionRegistry` | Manages connections |
| `DataLoadingService` | Coordinates extraction |
| `SemanticModel` | Maintains imported tables |
| `ReportingEngine` | Aggregates records |

### 11.2 STL Containers

The implementation uses:

- `vector` for ordered records.
- `unordered_map` for connection lookup.
- `map` for ordered product aggregation.
- `string` for source values.
- `optional`-compatible domain design for future optional metadata.

The connection registry uses average constant-time lookup through an unordered map.

### 11.3 Exception Handling

Invalid configuration and source failures are represented using custom exceptions.

The loader catches failures and returns a structured result.

This allows the calling application to distinguish successful extraction from failed extraction.

### 11.4 Performance

The file loader uses sequential reading.

The validation process runs in linear time relative to the number of records.

Product aggregation uses an ordered map, with logarithmic lookup and insertion.

The implementation avoids unnecessary copies in the reporting stage where references can be used safely.

### 11.5 Practical Limitations

The C++ example includes CSV processing and a simulated database adapter.

It does not implement:

- Native XLSX parsing
- HTTP transport
- Power BI connectivity
- Database-driver integration

These capabilities require additional transport or connector implementations.

---

## 12. Java 17 Implementation

The Java implementation focuses on enterprise-oriented connection management and refresh governance.

### 12.1 Domain Modeling

Java records represent immutable configuration and data structures.

Important records include:

- `SalesRecord`
- `ConnectionConfig`
- `LoadResult`
- `RefreshAudit`

The use of records reduces unnecessary mutable state.

### 12.2 Interfaces

The `SourceAdapter` interface separates source-specific retrieval from the central loading service.

The `DatabaseAdapter` interface provides a dedicated database access contract.

This supports modular connector development.

### 12.3 State Management

A connection can move through different states:

CREATED
    |
    v
CONNECTED
    |
    v
LOADING
    |
    v
READY

Failure path:

LOADING
    |
    v
FAILED

Disabled connections remain unavailable.

The connection context tracks these states independently from the actual data records.

### 12.4 Refresh Service

The refresh service coordinates loading and semantic model updates.

It uses an atomic flag to prevent simultaneous refresh operations through the same model service instance.

A refresh audit captures:

- Connection ID
- Model table
- Storage mode
- Status
- Record count
- Timestamp
- Result message

### 12.5 Enterprise Considerations

The implementation demonstrates:

- Immutable configuration
- Concurrent connection registries
- Explicit state transitions
- Custom exceptions
- Adapter-based source access
- Refresh auditing
- Validation before publication

The database adapter uses in-memory data for executable demonstration purposes.

Actual enterprise deployment would require a production database driver, managed credentials, and appropriately scoped permissions.

---

## 13. PostgreSQL Implementation

The PostgreSQL script models the relational infrastructure behind a data-loading management system.

It focuses on the management of connections, source objects, semantic models, imported records, and refresh operations.

### 13.1 Relational Architecture

The main relationship is:

Data Owners
    |
    v
Data Connections
    |
    v
Source Tables
    |
    v
Semantic Models
    |
    v
Model Tables
    |
    v
Sales Data

Refresh Executions
    |
    +---- Models
    |
    +---- Connections
    |
    +---- Owners
    |
    +---- Rejected Records

### 13.2 Main Tables

| Table | Purpose |
|---|---|
| `data_owners` | Stores connection and model owners |
| `data_connections` | Stores source connection metadata |
| `source_tables` | Stores available source objects |
| `semantic_models` | Stores analytical model definitions |
| `model_tables` | Maps source objects to model tables |
| `refresh_executions` | Records refresh operations |
| `validation_rules` | Defines data-quality requirements |
| `sales_data` | Stores imported analytical records |
| `rejected_records` | Stores rejected source records |
| `connection_access` | Stores connection permissions |

### 13.3 Primary Keys and Foreign Keys

Primary keys uniquely identify records.

Foreign keys enforce relationships between database tables.

For example, every source table references an existing connection.

Every model table references an existing semantic model.

This prevents orphaned records.

### 13.4 Constraints

The database uses:

- `NOT NULL`
- `UNIQUE`
- `CHECK`
- `PRIMARY KEY`
- `FOREIGN KEY`

These constraints enforce basic data integrity.

For example, negative quantities and negative revenue values are rejected.

A web connection must use HTTPS.

Database connections must require SSL.

### 13.5 Indexes

Indexes support frequently used queries.

The implementation indexes:

- Connection ownership
- Source type and status
- Source-table relationships
- Semantic model relationships
- Refresh dates
- Refresh status
- Product names
- Imported record timestamps

Indexes improve retrieval efficiency for suitable queries but increase storage requirements and write overhead.

### 13.6 Functions and Procedures

The script includes:

| Database object | Purpose |
|---|---|
| `validate_connection()` | Checks connection eligibility |
| `can_refresh_model()` | Checks refresh authorization |
| `start_refresh()` | Starts an authorized refresh |
| `complete_refresh()` | Completes a running refresh |

These objects move some operational rules into the database.

### 13.7 Triggers

The refresh-state trigger validates changes to refresh records.

It prevents completed refresh records from being modified and checks the presence of required failure information.

The model metadata trigger updates imported table metadata following a successful refresh.

### 13.8 Reporting

The database creates three reporting views:

- `sales_revenue_summary`
- `refresh_performance`
- `active_connection_inventory`

It also includes CTE-based analysis for calculating successful load percentages.

### 13.9 Transaction Handling

The sample transaction demonstrates atomic insertion of an imported record.

A transaction ensures that related database operations are committed together or rolled back when an error occurs.

The SQL transaction does not represent a complete distributed transaction across PostgreSQL, an external source, and Power BI.

A production refresh system would need additional orchestration to coordinate those independent systems.

---

## 14. Important Technical Distinctions

Several concepts in Power BI data loading are closely related but represent different operations.

| Concept | Meaning |
|---|---|
| Data source | Original location of information |
| Data connection | Mechanism for accessing a source |
| Data extraction | Retrieval of source records |
| Data transformation | Modification of retrieved records |
| Data validation | Verification of record correctness |
| Data loading | Placement of prepared records into a target |
| Semantic model | Analytical organization of information |
| Import | Storage of retrieved data in the model |
| DirectQuery | Query execution against the underlying source |
| Live Connection | Connection to an existing external model |
| Refresh | Updating stored or managed data |
| Incremental refresh | Updating selected historical partitions or periods |

These distinctions matter because a successful connection does not guarantee a successful refresh, and a successful refresh does not automatically guarantee accurate analytical results.

---

## 15. Performance Considerations

Data-loading performance depends on several factors.

### 15.1 Source Performance

Database indexes, source query complexity, server capacity, and network response times affect extraction speed.

### 15.2 Data Volume

Large datasets require more memory, processing, and storage.

Removing unnecessary columns and filtering irrelevant records reduces data-transfer requirements.

### 15.3 Transformation Complexity

Repeated transformations and unnecessary type conversions increase processing costs.

Where appropriate, query folding can push supported transformation operations back to the source database.

### 15.4 Import Performance

Import models benefit from appropriate data types, reduced column counts, and efficient model structures.

Large models may benefit from partitioning and incremental refresh.

### 15.5 DirectQuery Performance

DirectQuery depends heavily on the source system.

The following are particularly important:

- Source indexing
- Query optimization
- Appropriate relationships
- Reduced query complexity
- Network latency
- Database capacity

### 15.6 Refresh Performance

Refresh operations should be monitored using:

- Duration
- Records read
- Records loaded
- Records rejected
- Failure frequency
- Source response time
- Model processing time

The JavaScript and PostgreSQL implementations demonstrate refresh-duration and refresh-history tracking.

---

## 16. Security and Reliability

Data loading can expose confidential business information if connection and access controls are inadequate.

Important considerations include:

### Authentication

Verify the identity of users and services connecting to external systems.

### Authorization

Grant only the permissions necessary for the required operation.

### Encryption

Protect data in transit using secure communication protocols.

### Credential Management

Use managed credential references or secure credential storage.

### Data Validation

Reject invalid records and retain sufficient information for investigation.

### Audit Logging

Record who initiated a refresh, which source was used, when processing occurred, and whether the operation succeeded.

### Failure Isolation

A failure in one source should not unnecessarily invalidate unrelated datasets.

### Data Consistency

Do not replace valid imported data with an incomplete or invalid refresh result.

The implementations demonstrate several of these controls through connection validation, HTTPS checks, read-only database access, rejected-record tracking, state management, and refresh auditing.

Production Power BI deployments also require appropriate workspace permissions, gateway configuration where applicable, tenant settings, row-level security, and source-specific authentication.

---

## 17. Practical Scenario

Consider an organization maintaining sales information across three systems.

| Source | Data |
|---|---|
| Excel | Monthly product sales |
| CSV | Regional transactions |
| PostgreSQL | Central transaction records |
| Web API | External sales information |

The organization wants a consolidated sales report.

The workflow is:

1. Establish connections to the sources.
2. Retrieve the relevant datasets.
3. Standardize column names.
4. Convert quantity and revenue into appropriate numeric types.
5. Reject records containing invalid values.
6. Combine compatible datasets.
7. Load the prepared information into the semantic model.
8. Configure the appropriate storage mode.
9. Establish refresh arrangements.
10. Monitor refresh performance and data quality.
11. Build reports using the consolidated model.

For this scenario, Import mode may be suitable for a consolidated historical reporting model.

DirectQuery may be appropriate for a separate operational model requiring source-side query execution.

Live Connection may be suitable when departments need to reuse a centrally managed semantic model.

The correct choice depends on the actual workload, source architecture, freshness requirements, and governance constraints.

---

## 18. Limitations of the Demonstrations

The implementations provide executable examples of data-loading architecture rather than complete replacements for Power BI connectors.

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| CSV | Yes | Yes | Yes | Yes | Metadata and storage |
| XLSX | Basic reader | CSV export | CSV export | CSV export | Metadata |
| JSON | Yes | Yes | Not implemented | Not implemented | JSONB support |
| Database | SQLite | Adapter simulation | Adapter simulation | Adapter simulation | Native relational database |
| Web | HTTPS JSON | HTTPS JSON | URL validation | URL validation | Connection metadata |
| Import simulation | Yes | Yes | Yes | Yes | Yes |
| DirectQuery simulation | Yes | Yes | Yes | Yes | Mode metadata |
| Live Connection simulation | Yes | Yes | Yes | Yes | External model metadata |
| Refresh tracking | Yes | Yes | Basic | Yes | Yes |
| Power BI API integration | No | No | No | No | No |

Additional production capabilities would include:

- Native Power BI connectivity
- Real database-driver integrations
- Complete Excel workbook support
- Enterprise authentication
- Power Query M execution
- Actual DirectQuery query translation
- External semantic model connectivity
- Power BI Service refresh integration
- Incremental partition processing
- Gateway management
- Production-scale monitoring

The examples intentionally separate the underlying data-engineering concepts from Power BI-specific infrastructure.

---

## 19. Execution Requirements

| File | Requirement |
|---|---|
| Python | Python 3.10 or later |
| JavaScript | Node.js 18 or later |
| C++17 | Compiler supporting the C++17 standard |
| Java | JDK 17 |
| PostgreSQL | PostgreSQL 15 or later |

All four application programs use standard language libraries without mandatory third-party dependencies.

The programs create local demonstration datasets during execution.

The PostgreSQL script creates a dedicated schema named `powerbi_loading`.

For repeated SQL execution in an existing database, the custom enum types and existing objects must be managed before rerunning the complete script.

The PostgreSQL implementation is designed as an initial database setup rather than an automatically repeatable migration.

---

## 20. Technical Concepts Covered

The project demonstrates the following connected areas:

| Area | Concepts |
|---|---|
| File ingestion | Excel, CSV, JSON |
| Database integration | Connection adapters, queries, read-only access |
| Web integration | HTTPS, HTTP responses, JSON |
| Data preparation | Standardization, conversion, filtering |
| Data quality | Required fields, invalid values, rejected records |
| Connection management | Configuration, ownership, validation |
| Storage modes | Import, DirectQuery, Live Connection |
| Semantic models | Tables, model metadata, analytical organization |
| Refresh management | Refresh execution, status, auditing |
| Programming architecture | Classes, interfaces, adapters, events |
| Database engineering | Relational tables, constraints, indexes, triggers |
| Security | Authentication design, authorization, encryption |
| Performance | Source queries, indexing, caching, refresh monitoring |

These concepts establish the technical foundation for understanding how Power BI obtains data, prepares it, stores or queries it, and makes it available for business analysis.
