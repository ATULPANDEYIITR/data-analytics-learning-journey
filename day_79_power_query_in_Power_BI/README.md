# Power Query in Power BI

## Technical Scope

Power Query is the data preparation and transformation engine used in Power BI. It connects to data sources, extracts information, cleans inconsistent records, changes data structures, combines datasets, and prepares data for reporting and analysis.

Power Query uses the **M language**, a functional language designed for data transformation.

Its primary purpose is to convert raw source data into a structured, consistent dataset without requiring every transformation to be performed manually.

The implementations in this repository demonstrate the underlying data-processing concepts through Python, JavaScript, C++17, Java 17, and PostgreSQL.

## 1. Power Query Architecture

A typical Power Query workflow follows this sequence:

Source Systems
    |
    v
Data Connection
    |
    v
Data Extraction
    |
    v
Data Cleaning
    |
    v
Data Transformation
    |
    v
Data Type Conversion
    |
    v
Merge / Append
    |
    v
Query Dependencies
    |
    v
Load Transformed Data
    |
    v
Power BI Data Model
    |
    v
Reports and Dashboards

Each stage has a separate responsibility.

| Stage | Purpose |
|---|---|
| Data connection | Establish access to source information |
| Extraction | Retrieve source records |
| Cleaning | Correct inconsistent or incomplete data |
| Transformation | Change the structure and content |
| Type conversion | Assign appropriate data types |
| Merge | Combine columns from related tables |
| Append | Combine records from multiple tables |
| Dependencies | Establish relationships between queries |
| Loading | Make prepared data available to the model |

Power Query transformations are represented as ordered steps. A later transformation generally uses the output of earlier transformations.

## 2. Data Cleaning

Data cleaning identifies and corrects problems that can affect reporting accuracy.

Common problems include:

- Leading and trailing spaces.
- Inconsistent capitalization.
- Empty strings.
- Null values.
- Duplicate records.
- Incorrect column names.
- Inconsistent category values.
- Invalid numerical values.
- Incorrect date formats.
- Unexpected source records.

### Text cleaning

Consider the following customer information:

| Customer ID | Original Name | Region |
|---|---|---|
| 1 | ` Alice ` | North |
| 2 | `Bob` | South |
| 3 | `Carol` | North |

The name ` Alice ` contains unnecessary spaces.

Text cleaning produces:

| Customer ID | Cleaned Name | Region |
|---|---|---|
| 1 | Alice | North |
| 2 | Bob | South |
| 3 | Carol | North |

The Python and JavaScript implementations use whitespace normalization.

The C++ and Java implementations use their own string-processing mechanisms.

The PostgreSQL implementation uses `btrim` and `regexp_replace`.

### Removing duplicates

Duplicate removal prevents repeated records from being counted unnecessarily.

A duplicate can be identified using:

- All columns.
- A unique identifier.
- A selected combination of columns.

For example, `customer_id` can identify duplicate customer records.

A suitable duplicate-removal operation should preserve a defined record-selection rule. Simply deleting arbitrary records can result in the loss of important information.

### Handling null values

A null value represents missing or unknown information.

It is different from:

- Zero.
- An empty string.
- The text `NULL`.
- A Boolean false value.

Possible treatments include:

- Keeping null values.
- Removing rows with missing mandatory fields.
- Replacing values using an approved business rule.
- Flagging incomplete records for investigation.

Replacing missing information with zero without understanding its meaning can produce misleading results.

### Filtering rows

Filtering selects records that satisfy a condition.

For example:

`amount >= 500`

This retains orders with an amount of at least 500.

Filtering can be applied using:

- Numerical conditions.
- Text conditions.
- Date ranges.
- Multiple conditions.
- Null-value conditions.

Filtering should be performed at an appropriate stage because early filtering can reduce the amount of data processed by later operations.

## 3. Data Transformation

Data transformation changes the structure or values of information.

Common operations include:

| Transformation | Purpose |
|---|---|
| Rename Columns | Change column names |
| Remove Columns | Eliminate unnecessary fields |
| Reorder Columns | Change column arrangement |
| Add Custom Column | Calculate new values |
| Replace Values | Substitute existing values |
| Split Column | Divide one column into multiple columns |
| Merge Columns | Combine multiple columns |
| Filter Rows | Retain selected records |
| Group By | Aggregate records |
| Pivot Column | Convert distinct values into columns |
| Unpivot Columns | Convert columns into attribute-value records |
| Transpose | Exchange rows and columns |

### Custom columns

A custom column calculates a value using existing columns.

For example:

| Order ID | Amount | Category |
|---|---:|---|
| 101 | 1250.50 | High Value |
| 102 | 800.00 | Standard |
| 103 | 450.25 | Standard |

The business rule is:

- Amount greater than or equal to 1000: High Value.
- Amount below 1000: Standard.

The Python, JavaScript, and Java implementations demonstrate this through functions or expressions.

### Group By

Group By combines records with matching values and calculates aggregate results.

Example:

| Region | Order Amount |
|---|---:|
| North | 1250.50 |
| South | 800.00 |
| North | 450.25 |

Grouped result:

| Region | Total Sales |
|---|---:|
| North | 1700.75 |
| South | 800.00 |

Common aggregation operations include:

- Sum.
- Count.
- Average.
- Minimum.
- Maximum.
- Distinct count.

Grouping changes the level of detail in the dataset. The original individual transactions may no longer be available in the aggregated result.

## 4. Data Types

Data types determine how values are interpreted and processed.

Incorrect data types can cause calculation errors, incorrect sorting, failed relationships, and inaccurate reports.

| Data Type | Example | Purpose |
|---|---|---|
| Text | `Atul` | Names and descriptions |
| Whole Number | `100` | Counts and identifiers |
| Decimal Number | `1250.50` | Measurements and amounts |
| Fixed Decimal Number | `1250.50` | Financial values with controlled decimal precision |
| Date | `2026-01-10` | Calendar dates |
| Date/Time | `2026-01-10 10:30` | Date and time values |
| Time | `10:30:00` | Time values |
| True/False | `TRUE` | Logical conditions |
| Percentage | `0.15` | Percentage measurements |
| Currency | `1250.50` | Financial reporting |

### Why data types matter

Consider the following values:

`100`, `200`, `50`

If stored as numbers, sorting produces:

`50, 100, 200`

If stored as text, sorting can produce a different order because text is compared character by character.

Similarly, adding two numerical values requires numerical data types.

The implementations use explicit conversion functions and validation.

The PostgreSQL implementation uses safe conversion functions:

- `try_integer`
- `try_numeric`
- `try_date`

Invalid source values return null from these conversion functions rather than terminating the entire extraction process.

The PostgreSQL staging tables preserve the original text values so invalid records can be investigated.

### Strict and non-strict conversion

Two approaches are demonstrated.

**Strict conversion**

The transformation stops when an invalid value is encountered.

This is useful when every record must satisfy a defined data contract.

**Non-strict conversion**

Invalid values are converted to null and logged or handled separately.

This is useful when a dataset contains non-critical errors that should not prevent processing of all valid records.

A production implementation should distinguish between mandatory fields and optional fields.

## 5. Merge Queries

Merge combines two tables horizontally using related columns.

It is conceptually similar to a relational database join.

Consider two tables.

**Customers**

| Customer ID | Customer Name | Region |
|---|---|---|
| 1 | Alice | North |
| 2 | Bob | South |
| 3 | Carol | North |

**Orders**

| Order ID | Customer ID | Amount |
|---|---|---:|
| 101 | 1 | 1250.50 |
| 102 | 2 | 800.00 |
| 103 | 1 | 450.25 |
| 104 | 99 | 300.00 |

The common column is `Customer ID`.

After a left outer merge:

| Order ID | Customer ID | Amount | Customer Name | Region |
|---|---|---:|---|---|
| 101 | 1 | 1250.50 | Alice | North |
| 102 | 2 | 800.00 | Bob | South |
| 103 | 1 | 450.25 | Alice | North |
| 104 | 99 | 300.00 | NULL | NULL |

The unmatched order remains in the output because the operation is a left outer join.

### Merge types

| Merge Type | Behaviour |
|---|---|
| Left Outer | All rows from the first table and matching rows from the second |
| Right Outer | All rows from the second table and matching rows from the first |
| Full Outer | All rows from both tables |
| Inner | Only matching rows |
| Left Anti | Rows from the first table without a match |
| Right Anti | Rows from the second table without a match |

### Important merge considerations

- The joining columns should have compatible data types.
- Matching values should follow consistent formatting rules.
- Duplicate keys can produce multiple output rows.
- Null values require explicit consideration.
- Column-name collisions must be handled.
- Unexpected unmatched records should be investigated.

A merge is not necessarily a one-to-one operation.

For example, one customer can have several orders. Therefore, a customer-to-orders merge can produce several rows for the same customer.

### Implementation details

The Python, JavaScript, C++17, and Java implementations use hash-based indexing to find matching records.

For a left table containing `n` records and a right table containing `m` records, building the right-side index generally requires O(m) time.

Lookup and output processing generally require O(n + m + k), where `k` is the number of resulting rows, assuming efficient hashing.

The PostgreSQL implementation uses a `LEFT JOIN` between the `orders` and `customers` tables.

## 6. Append Queries

Append combines multiple tables vertically.

It adds records from one table below records from another table.

Unlike Merge, Append does not combine columns using matching identifiers.

Example:

**Current Orders**

| Order ID | Customer ID | Amount |
|---|---|---:|
| 101 | 1 | 1250.50 |
| 102 | 2 | 800.00 |

**Archived Orders**

| Order ID | Customer ID | Amount |
|---|---|---:|
| 90 | 2 | 500.00 |
| 91 | 3 | 700.00 |

After Append:

| Order ID | Customer ID | Amount |
|---|---|---:|
| 101 | 1 | 1250.50 |
| 102 | 2 | 800.00 |
| 90 | 2 | 500.00 |
| 91 | 3 | 700.00 |

### Append behaviour

Append can work with:

- Two tables.
- Three or more tables.
- Tables with identical structures.
- Tables with different column structures.

When a column exists in one table but not another, the missing values must be represented as null.

### Append versus Merge

| Property | Merge | Append |
|---|---|---|
| Direction | Horizontal | Vertical |
| Main purpose | Combine related columns | Combine records |
| Matching keys | Usually required | Not required |
| Typical result | Wider table | Taller table |
| Common use | Customer and order information | Monthly transaction files |

The PostgreSQL implementation uses `UNION ALL` to represent Append.

`UNION ALL` retains duplicate records, while `UNION` removes duplicate result rows.

This distinction is important when preserving transactional records.

## 7. Query Dependencies

Query dependencies describe relationships between queries.

A query can use the result of another query as its input.

Example:

Customers_Source
    |
    v
Clean_Customers

Orders_Source
    |
    v
Typed_Orders
    |
    +------------------+
    |                  |
    v                  v
Customer_Order_Merge  Combined_Orders
    |                  ^
    |                  |
    |             Archived_Orders_Source
    v
Regional_Summary

The diagram represents logical dependencies, not necessarily a fixed execution sequence for every Power BI refresh.

### Why dependencies matter

Suppose a report depends on a customer query.

If the customer query changes, dependent queries may need to be recalculated.

Dependencies help determine:

- Which queries use a particular source.
- Which transformations depend on another query.
- Which queries must be evaluated first.
- Which changes can affect downstream outputs.
- Where circular references exist.

### Dependency management

The four programming implementations use graph traversal to determine an execution order.

They detect:

- Missing dependencies.
- Circular dependencies.
- Duplicate query definitions.
- Failed transformations.
- Invalid outputs.

The Python, C++, and Java implementations use depth-first traversal.

The JavaScript implementation adds asynchronous query evaluation and execution events.

The PostgreSQL implementation uses a recursive common table expression to inspect dependencies and a trigger to prevent circular relationships.

### Query dependency versus query loading

A query can be used as an intermediate transformation without necessarily being loaded into the Power BI data model.

This distinction is important.

A staging query may supply data to several downstream queries while remaining an intermediate preparation step.

In Power BI, the Enable Load setting determines whether a query's output is loaded into the model.

The option to include a query in the report refresh process is separate from whether its intermediate result is loaded as a model table.

## 8. Applied Workflow

The implementations use a retail sales scenario.

The source information consists of customer records, current orders, and archived orders.

### Source datasets

| Dataset | Purpose |
|---|---|
| Customers | Customer identification and region |
| Current Orders | Recent transactions |
| Archived Orders | Historical transactions |

### Transformation workflow

| Stage | Operation | Result |
|---|---|---|
| 1 | Extract customer records | Raw customer dataset |
| 2 | Clean customer names | Standardized text |
| 3 | Remove duplicate customers | Unique customer records |
| 4 | Convert customer identifiers | Numerical identifiers |
| 5 | Convert order amounts | Decimal values |
| 6 | Convert order dates | Date values |
| 7 | Filter invalid records | Valid transaction dataset |
| 8 | Merge customers and orders | Enriched transaction dataset |
| 9 | Append archived transactions | Combined transaction dataset |
| 10 | Add calculated category | Categorized transactions |
| 11 | Group by region | Regional sales summary |
| 12 | Validate output | Quality-controlled dataset |

### Expected business outcomes

The transformed information supports:

- Total sales reporting.
- Regional sales comparison.
- Customer transaction analysis.
- Historical and current sales comparison.
- High-value transaction identification.
- Data quality monitoring.

## 9. Understanding M Language

Power Query transformations are expressed using the M language.

M uses expressions and named steps.

A typical query contains:

- A `let` expression.
- One or more named transformation steps.
- An `in` expression identifying the final result.

A conceptual sequence is:

Source
    |
    v
Promoted Headers
    |
    v
Changed Type
    |
    v
Filtered Rows
    |
    v
Removed Duplicates
    |
    v
Final Result

The steps are evaluated according to their dependencies.

### Common M functions

| M Function | Purpose |
|---|---|
| `Table.SelectRows` | Filter records |
| `Table.SelectColumns` | Select columns |
| `Table.RemoveColumns` | Remove columns |
| `Table.RenameColumns` | Rename columns |
| `Table.TransformColumnTypes` | Change data types |
| `Table.Distinct` | Remove duplicate records |
| `Table.NestedJoin` | Merge related tables |
| `Table.Combine` | Append tables |
| `Table.Group` | Group and aggregate |
| `Table.AddColumn` | Create calculated columns |
| `Table.Sort` | Sort records |
| `Table.PromoteHeaders` | Use the first row as column headers |
| `Table.FillDown` | Fill missing values using preceding values |
| `Table.Unpivot` | Convert columns into attribute-value rows |
| `Table.Pivot` | Convert attribute values into columns |

The programming files in this repository simulate the relevant processing mechanisms. They are not implementations of the complete M language interpreter.

## 10. Query Folding

Query folding is the process of translating supported Power Query transformations into operations that can execute at the source system.

For example, a filter performed in Power Query may be translated into a SQL `WHERE` condition.

Instead of transferring an entire database table into Power BI and filtering locally, the source database can perform the filtering.

Conceptually:

Power Query Transformation
    |
    v
Query Folding
    |
    v
Source Database Query
    |
    v
Filtered Source Results
    |
    v
Power BI

### Benefits

- Reduced data transfer.
- Reduced memory consumption.
- Faster refresh operations.
- Better use of source database processing.
- Improved scalability for large datasets.

### Factors affecting folding

- Source connector capabilities.
- Supported transformation operations.
- The order of transformations.
- Custom functions.
- Native queries.
- Data source compatibility.
- Privacy and security restrictions.

Not every transformation can be folded.

When folding is unavailable, some transformations are executed by the Power Query engine.

The actual folding behaviour must be checked for the selected connector and transformation sequence.

## 11. Refresh and Data Loading

Power Query prepares data before it becomes available to the Power BI data model.

A typical refresh involves:

1. Connecting to the source.
2. Reading source data.
3. Evaluating the required query dependencies.
4. Applying transformation steps.
5. Validating the resulting data.
6. Loading enabled query results into the model.

### Import mode

In Import mode, transformed data is loaded into the Power BI semantic model.

Reports use the imported data until the next refresh.

### DirectQuery

In DirectQuery mode, Power BI queries the underlying source when report interactions require data.

The available transformations and their execution depend on connector capabilities and supported folding behaviour.

### Incremental refresh

Incremental refresh processes selected periods or partitions rather than repeatedly refreshing the complete historical dataset.

It can reduce refresh time and source-system workload when the data source and model are configured appropriately.

## 12. Python Implementation

File: `power_query.py`

The Python implementation provides a self-contained ETL simulation.

| Component | Responsibility |
|---|---|
| `Table` | Stores structured tabular data |
| `DataType` | Defines supported types |
| `clean_text` | Normalizes text |
| `remove_duplicates` | Removes repeated records |
| `remove_null_rows` | Removes incomplete records |
| `rename_columns` | Renames fields |
| `change_data_types` | Converts column values |
| `filter_rows` | Applies row conditions |
| `add_column` | Calculates additional values |
| `merge_tables` | Performs a left outer merge |
| `append_tables` | Combines tables vertically |
| `group_sales` | Aggregates regional sales |
| `QueryEngine` | Manages dependencies and execution |

The implementation uses dictionaries for rows and lists for tables.

Decimal is used for financial values to avoid the common floating-point precision problems associated with binary floating-point arithmetic.

The dependency engine detects circular references and evaluates queries in dependency order.

The JSON export demonstrates how transformed results can be persisted.

### Run

`python power_query.py`

The script generates `power_query_output.json`.

## 13. JavaScript Implementation

File: `power_query.js`

The JavaScript implementation focuses on event-driven and asynchronous query processing.

| Component | Responsibility |
|---|---|
| `createTable` | Constructs validated tables |
| `cleanTable` | Standardizes source values |
| `changeTypes` | Performs type conversion |
| `removeDuplicates` | Removes duplicate records |
| `mergeTables` | Combines related tables |
| `appendTables` | Combines transaction datasets |
| `groupBy` | Aggregates information |
| `QueryEngine` | Manages asynchronous query execution |

The implementation uses:

- `Map` for dependency and lookup management.
- `Set` for duplicate detection.
- `Promise` and `async/await` for asynchronous execution.
- `EventEmitter` for query lifecycle events.
- Node.js file handling for report export.

The events `queryStarted`, `queryCompleted`, and `queryFailed` expose execution state.

This design is useful for understanding how transformation pipelines can communicate progress and failures.

### Run

`node power_query.js`

The program generates `power_query_report.json`.

## 14. C++17 Implementation

File: `power_query.cpp`

The C++ implementation focuses on data structures, explicit domain modelling, and transformation efficiency.

| Component | Responsibility |
|---|---|
| `Table` | Represents tabular information |
| `Value` | Represents nullable field values |
| `DataType` | Defines conversion categories |
| `JoinType` | Defines join behaviour |
| `PowerQueryEngine` | Implements transformation operations |
| `merge` | Implements INNER, LEFT, and FULL joins |
| `append` | Combines records |
| `filter` | Selects matching rows |
| `registerQuery` | Registers dependent transformations |
| `execute` | Evaluates query dependencies |

The merge operation uses an `unordered_map` index.

This avoids repeatedly scanning the entire right-side table for each left-side record.

The implementation also distinguishes unmatched records from matched records when performing full outer joins.

The standard library is sufficient for the complete implementation.

### Compile and run

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic power_query.cpp -o power_query`

`./power_query`

## 15. Java 17 Implementation

File: `PowerQueryEnterprise.java`

The Java implementation models an enterprise-oriented transformation system.

| Component | Responsibility |
|---|---|
| `DataTable` | Immutable tabular representation |
| `DataType` | Defines supported data types |
| `QueryStatus` | Represents query lifecycle states |
| `JoinType` | Defines supported join types |
| `QueryPolicy` | Defines validation and cleaning rules |
| `TransformationService` | Implements data operations |
| `Query` | Represents an individual transformation |
| `QueryEngine` | Manages execution dependencies |

Java records represent structured domain information such as customers, orders, and query policies.

Immutable collection copies reduce accidental modification of source data.

BigDecimal supports financial calculations with controlled decimal precision.

Custom exceptions distinguish transformation failures from ordinary execution errors.

The query engine uses dependency traversal and explicit execution states.

### Compile and run

`javac --release 17 PowerQueryEnterprise.java`

`java PowerQueryEnterprise`

## 16. PostgreSQL Implementation

File: `power_query.sql`

The PostgreSQL implementation represents a relational ETL workflow.

It provides persistent staging tables, validated output tables, query metadata, transformation definitions, dependency tracking, execution auditing, and reporting views.

### Database objects

| Database Object | Purpose |
|---|---|
| `data_sources` | Registers source systems |
| `queries` | Stores query definitions and states |
| `query_dependencies` | Records query relationships |
| `staging_customers` | Stores raw customer records |
| `staging_orders` | Stores raw transaction records |
| `staging_archived_orders` | Stores historical transactions |
| `customers` | Stores cleaned customer records |
| `orders` | Stores validated current transactions |
| `archived_orders` | Stores validated historical transactions |
| `transformations` | Records transformation steps |
| `data_quality_issues` | Tracks detected errors |
| `query_execution_log` | Records execution results |

### Database functions

The SQL script includes safe conversion functions:

- `try_integer`
- `try_numeric`
- `try_date`

These functions allow invalid source values to be identified without terminating the entire loading operation.

The query dependency trigger prevents circular dependencies.

The recursive dependency report exposes relationships between queries.

### Database views

| View | Purpose |
|---|---|
| `customer_order_merge` | Combines customer and order information |
| `combined_orders` | Appends current and archived transactions |
| `regional_sales_summary` | Aggregates sales by region |
| `query_dependency_report` | Displays query dependencies |
| `query_quality_report` | Displays data quality and reporting eligibility |

The execution audit procedure records query outcomes and affected-row counts.

The transaction section demonstrates consistent recording of execution information.

### Execute

Run `power_query.sql` in a PostgreSQL database using a PostgreSQL client.

The script creates and populates its own `power_query` schema.

## 17. Implementation Comparison

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Data cleaning | Yes | Yes | Yes | Yes | Yes |
| Type conversion | Yes | Yes | Yes | Yes | Yes |
| Duplicate removal | Yes | Yes | Yes | Yes | Yes |
| Filtering | Yes | Yes | Yes | Yes | Yes |
| Merge | Yes | Yes | Yes | Yes | Yes |
| Append | Yes | Yes | Yes | Yes | Yes |
| Aggregation | Yes | Yes | Not implemented | Yes | Yes |
| Dependency tracking | Yes | Yes | Yes | Yes | Yes |
| Circular dependency detection | Yes | Yes | Yes | Yes | Yes |
| Asynchronous events | No | Yes | No | No | No |
| Relational constraints | Simulated | Simulated | Simulated | Simulated | Native |
| Persistent execution audit | JSON export | JSON export | No | No | Yes |

The five implementations are independent learning models. They do not share a runtime or require communication with one another.

## 18. Performance and Reliability

### Memory management

Import-style processing requires memory for the extracted and transformed data.

For large datasets, processing every row in memory may be impractical.

Potential approaches include:

- Filtering at the source.
- Query folding.
- Incremental refresh.
- Processing data in batches.
- Selecting only required columns.
- Reducing unnecessary intermediate tables.

### Merge performance

Hash-based merges generally provide efficient lookup when join keys are properly prepared.

Database joins can use indexes, statistics, and query-planning optimizations.

The best join strategy depends on data size, key distribution, memory availability, and source-system capabilities.

### Append performance

Append is generally a row-concatenation operation.

Schema differences require alignment before combination.

A consistent schema simplifies downstream reporting and reduces unexpected null values.

### Data quality

Data validation should include:

- Mandatory-field checks.
- Type checks.
- Duplicate detection.
- Referential integrity.
- Valid numerical ranges.
- Date validation.
- Record-count reconciliation.
- Source-to-output control totals.

A successful refresh does not automatically mean that the resulting dataset is correct.

### Security

Production data preparation should consider:

- Credentials stored through approved connection mechanisms.
- Least-privilege source access.
- Sensitive-column handling.
- Data privacy requirements.
- Approved data-sharing boundaries.
- Secure storage of exported files.
- Controlled access to database staging tables.

Connection credentials should never be embedded in transformation scripts.

## 19. Important Distinctions

| Concept | Meaning |
|---|---|
| Data Cleaning | Correcting inconsistent or problematic source information |
| Data Transformation | Changing data structure or values |
| Data Type Conversion | Assigning the correct representation to a field |
| Merge | Combining related tables horizontally |
| Append | Combining records vertically |
| Query Dependency | Defining which queries require other query results |
| Query Folding | Translating transformations into source-system operations |
| Refresh | Re-evaluating queries and updating data |
| Data Loading | Making query output available to the model |
| Semantic Model | Organizing data, relationships, measures, and reporting logic |

These mechanisms solve different problems and should not be treated as interchangeable.

## 20. Limitations

The implementations demonstrate fundamental and advanced ETL mechanisms but are not replacements for the complete Power Query engine.

Specifically:

- They do not implement the complete M language.
- They do not connect to Power BI Desktop.
- They do not implement Power BI's visual query editor.
- They do not reproduce every Power Query connector.
- They do not reproduce Power BI privacy-level enforcement.
- They do not implement the complete query-folding engine.
- They do not implement Power BI semantic-model loading.
- They do not reproduce incremental refresh partitions.
- They use simplified dependency and refresh models.

The PostgreSQL implementation represents relational ETL processing, not Power BI's internal query execution architecture.

The sample financial data uses decimal values for accurate calculations. Real production systems should define currency precision, rounding, and conversion rules explicitly.

## 21. Practical Learning Outcomes

The implementations establish the following technical understanding:

- How raw information enters a transformation pipeline.
- Why data cleaning is necessary.
- How transformations change tabular structures.
- Why explicit data types improve reliability.
- How related datasets are combined using Merge.
- How multiple datasets are combined using Append.
- How query dependencies determine evaluation order.
- How invalid records can be isolated.
- How database constraints protect data integrity.
- How aggregation produces reporting-ready information.
- How execution failures can be detected and recorded.
- How performance improves through indexing, filtering, and source-side processing.

The central processing model is:

**Extract → Clean → Transform → Validate → Merge or Append → Aggregate → Load → Report**
