# Power Query fundamentals

## Introduction

Power Query is a data preparation and transformation technology used to extract data from sources, transform it into a consistent analytical structure, and load the resulting data into a destination such as Excel, Power BI, or another supported environment.

Its central workflow is commonly described as **ETL**:

- **Extract** data from one or more sources.
- **Transform** the data through repeatable preparation steps.
- **Load** the resulting dataset into a destination.

Power Query is particularly useful when source data is inconsistent, distributed across multiple files or systems, contains incorrect data types, requires filtering or cleaning, or must be refreshed repeatedly.

This implementation set models those concepts in Python, JavaScript, and C++. The Python program provides a broad educational implementation of ETL operations. The JavaScript program emphasizes functional transformations, object-based records, arrays, JSON, and asynchronous extraction. The C++ program presents a more strongly typed industry-style sales-processing case study.

## ETL fundamentals

### Extract

Extraction is the process of obtaining source data.

Typical sources include:

- CSV files
- Excel workbooks
- relational databases
- JSON documents
- web APIs
- cloud services
- text files
- folders containing multiple files
- enterprise applications

The extracted data is not necessarily ready for analysis. A CSV file, for example, commonly represents every field as text until appropriate data types are assigned.

The Python implementation uses `csv.DictReader` to extract CSV data. The JavaScript implementation begins with JavaScript objects representing records. The C++ implementation models external source records with the `RawSale` structure.

### Transform

Transformation converts source data into a reliable structure.

Typical transformations include:

- changing data types
- removing unnecessary columns
- renaming columns
- filtering rows
- sorting
- trimming text
- replacing values
- creating calculated columns
- handling null values
- removing duplicates
- merging queries
- appending queries
- grouping and aggregation
- deriving date attributes
- validating relationships
- applying conditional business rules

Transformation is the main part of most data-preparation workflows.

### Load

Loading places the prepared data into a destination.

Possible destinations include:

- Excel worksheets
- Power BI semantic models
- databases
- data warehouses
- files
- applications
- analytical systems

The Python implementation demonstrates JSON-ready output. JavaScript demonstrates JSON serialization. The C++ implementation produces a formatted analytical report as its load destination.

## Important terminology

### Query

A Power Query query is a defined sequence of operations applied to a source.

A query can be refreshed when the source changes. The transformation logic does not need to be manually repeated for every refresh.

The Python `DataQuery` class, JavaScript `DataQuery` class, and C++ `ETLQuery` class model this idea.

### Row

A row represents one record.

For example, a sales table may contain one row per order.

### Column

A column represents an attribute of each row.

Examples include `OrderID`, `OrderDate`, `Quantity`, and `UnitPrice`.

### Table

A table is a structured collection of rows and columns.

The Python programs use lists of dictionaries as an educational table representation. JavaScript uses arrays of objects. C++ uses vectors of structures.

### Schema

A schema describes the expected structure of a dataset.

It includes concepts such as:

- column names
- data types
- required fields
- relationships
- constraints

External sources can change their schema unexpectedly, so validating required columns is an important production practice.

## Data types

Correct data types are fundamental to reliable transformations.

Common analytical data types include:

| Type | Example |
|---|---|
| Text | `"North"` |
| Whole number | `25` |
| Decimal number | `1250.50` |
| Date | `2026-01-05` |
| Date/time | `2026-01-05 14:30` |
| Logical | `true` / `false` |
| Null | missing value |

A CSV field containing `"25"` is text until it is converted to a number.

This distinction matters because mathematical operations, comparisons, sorting, joins, and aggregations behave differently for text and numeric values.

The Python implementation explicitly converts order IDs and quantities to integers, prices to `Decimal`, and dates to `datetime`.

The JavaScript implementation converts numeric source values using `Number.parseInt` and `Number.parseFloat`.

The C++ implementation converts external strings into strongly typed `int` and `double` values.

## Changing data types

Changing data types should be deliberate.

For example:

`"1250.50"` should become a numeric value before calculating revenue.

`"2026-01-05"` should become a date before extracting year, month, or quarter.

Type conversion should also account for invalid values.

An invalid value such as `"not-a-number"` should not silently become a valid business value.

The Python program uses functions such as `to_integer`, `to_decimal`, and `to_date`.

The JavaScript program uses `parseInteger`, `parseMoney`, and `parseDate`.

The C++ program uses `parseInteger` and `parseDecimal`.

## Text transformation

Source systems frequently contain inconsistent text.

Examples include:

- `" North "`
- `"north"`
- `"NORTH"`
- `" North  Region "`

Common text transformations include:

- trimming leading and trailing spaces
- removing unnecessary whitespace
- changing case
- replacing characters
- splitting text
- combining text
- extracting substrings

The implementations normalize region names and identifiers before using them in filtering and joins.

Text cleaning is important because apparently identical values can fail to match if hidden spaces or inconsistent formatting are present.

## Filtering

Filtering removes rows that do not satisfy a condition.

Examples:

- only North-region orders
- orders with quantity greater than four
- orders above a specified revenue threshold
- records from a particular date range
- customers belonging to a particular segment

The Python implementation uses `filter_rows`.

The JavaScript implementation uses `Array.prototype.filter`.

The C++ implementation uses a generic predicate-based `filterSales` function.

A filter should be based on a clearly defined business rule.

For example, filtering `Quantity >= 4` is different from filtering `SalesAmount >= 2000`. The two conditions answer different questions.

## Selecting columns

A dataset may contain more columns than the analytical task requires.

Selecting only necessary columns can:

- simplify downstream transformations
- reduce memory consumption
- improve readability
- reduce unnecessary data movement
- reduce exposure of sensitive fields

The Python implementation uses `select_columns`.

The JavaScript implementation uses `selectColumns`.

The C++ case study models a structured dataset rather than dynamically selecting columns, because C++ structures explicitly represent the expected schema.

## Renaming columns

Column names should communicate their meaning.

For example:

`SalesAmount` can be renamed to `Revenue` when the business definition makes that terminology appropriate.

Renaming should be performed carefully because downstream transformations may depend on the original name.

The Python and JavaScript implementations demonstrate explicit column mappings.

## Calculated columns

A calculated column derives a new value from existing fields.

The sales case study calculates:

`SalesAmount = Quantity × UnitPrice`

This is conceptually equivalent to creating a Custom Column in Power Query.

Calculated columns are useful for:

- revenue
- profit
- margin
- tax
- discounts
- classification
- date attributes
- business indicators

The transformation should use clearly defined business rules.

## Conditional logic

Conditional logic creates values according to business rules.

The implementations classify orders into:

- Low
- Medium
- High
- Very High

based on sales amount.

Conditional logic is useful for categorization and reporting, but thresholds should be treated as business definitions rather than arbitrary technical values.

## Missing values

Missing data is commonly represented as `null` or an equivalent missing-value representation.

Missing values must not automatically be treated as zero.

For example:

- missing price does not necessarily mean price is zero
- missing customer ID does not necessarily mean customer ID is unknown
- missing date does not necessarily mean today's date

The Python implementation uses `None`.

JavaScript uses `null`.

C++ uses `std::optional` for fields where the merged reference value may not exist.

## Error handling

ETL pipelines encounter invalid records.

Examples include:

- malformed numbers
- invalid dates
- missing required values
- unexpected columns
- invalid keys
- negative quantities
- negative prices
- duplicate identifiers

There are two important error-handling strategies.

### Fail the pipeline

Use this when invalid data makes the resulting dataset unsafe to load.

For example, if every sales record requires a valid order ID, an invalid order ID may be a fatal error.

### Isolate the bad record

Use this when the rest of the dataset can still be processed.

A production pipeline may place invalid rows into an error table containing:

- source record
- error reason
- source system
- timestamp
- pipeline run identifier

The examples demonstrate both validation and explicit exceptions.

## Data validation

Validation verifies that data satisfies expected rules.

The sales case study validates:

- required identifiers
- positive quantities
- non-negative prices
- source schema
- reference-data relationships

Validation should occur at appropriate points rather than only after all transformations have completed.

Early validation can prevent corrupted intermediate datasets.

## Duplicate records

Duplicate handling requires a clearly defined business key.

For sales data, `OrderID` might identify a unique order.

Removing duplicates based on every column is not always equivalent to removing duplicate business records.

A row can differ in an unimportant field while still representing the same business entity.

The Python implementation demonstrates `distinct_rows`.

The JavaScript implementation uses `distinctByKey`.

## Merge Queries

A merge combines two datasets using related columns.

For example:

Sales:

| CustomerID | OrderID | Revenue |
|---|---|---:|
| C001 | 1001 | 2501 |

Customers:

| CustomerID | CustomerName |
|---|---|
| C001 | Atul Pandey |

A merge on `CustomerID` can produce:

| CustomerID | OrderID | Revenue | CustomerName |
|---|---|---:|---|
| C001 | 1001 | 2501 | Atul Pandey |

This is a horizontal combination because columns from the related table are added to the existing rows.

The implementations use customer and product reference data to enrich sales transactions.

## Join types

Important join concepts include:

### Left outer join

Keep every row from the left table and matching rows from the right table.

This is useful when every sales record must remain in the output even when reference data is missing.

### Inner join

Keep only records for which a matching key exists in both datasets.

This can unintentionally remove records if reference data is incomplete.

### Right outer join

Keep every row from the right dataset and matching rows from the left dataset.

### Full outer join

Keep records appearing on either side.

### Anti join

Return records for which no matching key exists in the other dataset.

Anti joins are particularly useful for data-quality checks.

## Merge keys

A merge depends on a relationship between columns.

For example:

`Sales.CustomerID -> Customers.CustomerID`

The key should be:

- correctly typed
- consistently formatted
- appropriately unique on the dimension side
- free from accidental whitespace
- validated for missing values

A merge can produce unexpected results if the supposedly unique dimension key appears multiple times.

## Indexed joins

The C++ and JavaScript implementations create hash-based indexes for reference tables.

Conceptually:

1. Build an index from customer ID to customer record.
2. Read each sales record.
3. Look up its customer ID.
4. Attach the matching customer information.

For a dimension table of size `m` and a fact table of size `n`, building an index is approximately `O(m)` and average hash lookups are approximately `O(1)`, producing approximately `O(n + m)` behavior.

A naive nested-loop join can approach `O(n × m)`.

This difference becomes significant as datasets grow.

## Append Queries

Append combines compatible tables vertically.

For example:

January:

| OrderID | Revenue |
|---|---:|
| 1 | 100 |
| 2 | 200 |

February:

| OrderID | Revenue |
|---|---:|
| 3 | 150 |
| 4 | 300 |

Appending them produces four rows.

The important distinction is:

**Merge combines related columns using keys.**

**Append stacks rows from compatible datasets.**

Typical append use cases include:

- January transactions + February transactions
- sales from multiple regions
- files with the same structure
- historical partitions

## Append schema considerations

Append works best when the source tables have compatible columns.

If one table contains `Revenue` and another contains `SalesAmount`, they should not automatically be assumed to represent the same business field.

Differences in:

- names
- data types
- meanings
- units
- currencies

must be understood before appending.

## Group By and aggregation

Grouping organizes rows by a key and calculates aggregate values.

Examples include:

- total revenue by region
- order count by customer
- average price by product
- maximum transaction value by segment

The Python and JavaScript implementations calculate regional revenue.

The C++ implementation uses a `map` to aggregate revenue by region.

## Date transformations

Dates are often decomposed into analytical attributes.

For example:

`2026-01-05`

can produce:

- Year = 2026
- Month = 1
- Quarter = 1

Date attributes are useful for:

- monthly reporting
- quarterly reporting
- year-over-year analysis
- seasonal analysis
- calendar-based filtering

Date handling must consider locale, time zones, and source-system conventions.

## Query steps

A major Power Query concept is that transformations are represented as a sequence of applied steps.

A conceptual pipeline might be:

1. Source
2. Promote or identify headers
3. Change types
4. Clean text
5. Filter rows
6. Add calculated columns
7. Merge customer data
8. Merge product data
9. Group data
10. Load the result

The Python `DataQuery`, JavaScript `DataQuery`, and C++ `ETLQuery` classes model this approach.

This design makes a transformation pipeline easier to inspect and repeat.

## Python implementation

The Python program provides the broadest educational treatment.

It demonstrates:

- CSV extraction
- schema inspection
- explicit type conversion
- `Decimal` for monetary arithmetic
- text normalization
- calculated columns
- filtering
- selecting columns
- renaming columns
- sorting
- missing values
- validation
- deduplication
- indexed left joins
- inner joins
- appending
- grouping
- date attributes
- conditional classification
- query steps
- referential-integrity checks
- query-folding concepts
- idempotence
- performance considerations
- JSON loading
- transformation tests

Python is well suited to demonstrating ETL because its standard library provides convenient data structures and file-processing capabilities while keeping the implementation readable.

## JavaScript implementation

The JavaScript program emphasizes application-oriented data processing.

It demonstrates:

- object-based records
- arrays of objects
- `map`
- `filter`
- `Set`
- `Map`
- type conversion
- validation
- merging
- appending
- aggregation
- JSON serialization
- asynchronous extraction
- query pipelines
- performance considerations

JavaScript is particularly relevant when ETL processing is part of:

- web applications
- browser applications
- Node.js services
- API integrations
- JSON-based workflows

The use of `Map` for lookup indexes provides a useful demonstration of efficient key-based joins.

## C++ case study

### Problem

The C++ program models a retail analytics pipeline.

The system receives:

- transaction records
- customer reference data
- product reference data

The transaction source initially represents fields as strings, similar to a CSV import.

The system must create an analytical sales dataset containing:

- typed transaction fields
- calculated revenue
- customer information
- product information
- date attributes
- order classifications

### Architecture

The C++ pipeline follows:

`Extract -> Validate -> Transform -> Filter -> Merge -> Enrich -> Aggregate -> Load`

### Extract

The program uses dedicated extraction functions:

- `extractSales`
- `extractCustomers`
- `extractProducts`

These functions represent external sources while remaining self-contained.

### Transform

`transformSales` converts source strings into typed fields.

It also:

- trims identifiers
- normalizes region names
- validates quantity
- validates price
- calculates sales amount

### Merge

Customer and product tables are indexed using `unordered_map`.

This allows sales records to retrieve reference information through key lookups.

### Enrichment

The system derives:

- year
- month
- quarter
- order value classification

### Data quality

The `DataQualityReport` checks:

- total rows
- invalid quantities
- negative prices
- missing customer relationships
- missing product relationships

### Load

`loadReport` produces a formatted analytical report.

In a production implementation, this stage could instead write to a database, data warehouse, file, or reporting model.

## Conceptual relationship with Power Query

The following mapping connects the implementations to Power Query concepts:

| Power Query concept | Python | JavaScript | C++ |
|---|---|---|---|
| Source | CSV reader | Object array | Extraction functions |
| Table | List of dictionaries | Array of objects | Vector of structures |
| Column | Dictionary key | Object property | Struct member |
| Changed Type | Type conversion functions | Parsing functions | Strongly typed conversion |
| Text cleaning | String functions | String functions | Utility functions |
| Filter Rows | `filter_rows` | `filter` | `filterSales` |
| Custom Column | `add_sales_amount` | `addSalesAmount` | Calculated `salesAmount` |
| Select Columns | `select_columns` | `selectColumns` | Explicit structures |
| Rename Columns | `rename_columns` | `renameColumns` | Explicit fields |
| Merge | `left_merge` | `leftMerge` | Indexed reference join |
| Append | `append_tables` | `appendTables` | `appendSales` |
| Group By | `group_sum` | `groupSum` | `revenueByRegion` |
| Null | `None` | `null` | `std::optional` |
| Applied Steps | `DataQuery` | `DataQuery` | `ETLQuery` |
| Load | JSON | JSON | Report output |

## Query folding

Query folding is an important Power Query performance concept.

When Power Query connects to a source that supports folding, compatible transformations can be translated into operations executed by the source system.

Consider a database containing ten million sales records where only North-region records are needed.

Without source-side filtering, the conceptual flow may be:

`Database -> 10,000,000 records -> Power Query -> filter`

With folding, the source can execute the filter:

`Database -> WHERE Region = 'North' -> smaller result -> Power Query`

This can reduce:

- network transfer
- client memory consumption
- client CPU usage
- refresh time

Not every transformation can fold. Whether folding occurs depends on the connector, source system, transformation, query structure, and other constraints.

The Python implementation discusses this concept because Python is not attempting to reproduce Power Query's connector-specific folding engine.

## Performance considerations

Performance depends on:

- source size
- number of columns
- number of rows
- transformation complexity
- join strategy
- memory availability
- source capabilities
- network transfer
- query folding
- number of repeated scans

### Filter early

If a filter can safely be applied before expensive transformations, processing fewer rows may reduce computational work.

### Select necessary columns

Unused columns increase data movement and memory consumption.

### Use indexed joins

For equality joins, hash-based indexes can reduce repeated searches.

### Avoid unnecessary copies

Python and JavaScript transformations often create new arrays or objects. This improves functional clarity but can increase memory consumption on very large datasets.

### Source-side processing

For large database-backed datasets, pushing compatible operations to the database can be substantially more efficient than transferring all records to the client.

## Monetary precision

The Python implementation uses `Decimal` for monetary calculations.

Binary floating-point values such as Python `float`, JavaScript `Number`, and C++ `double` can introduce representation differences because many decimal fractions cannot be represented exactly in binary floating-point.

For financial systems, possible approaches include:

- decimal arithmetic
- integer minor units such as cents or paise
- database decimal types
- dedicated high-precision libraries

The appropriate choice depends on the required financial accuracy and system architecture.

## Idempotence

An idempotent transformation produces the same result when applied repeatedly.

For example, normalizing:

`"  north "`

to:

`"North"`

should produce `"North"` again if the normalization is repeated.

Idempotent transformations are valuable in refreshable ETL pipelines because rerunning a transformation should not progressively alter the data.

## Common mistakes

### Treating text as numeric data

A value such as `"100"` may look numeric but remains text until conversion.

### Ignoring locale

A decimal value can be represented differently depending on source conventions.

For example, a source may use different decimal and thousands separators from the environment processing it.

### Joining on unclean keys

`"C001"` and `" C001 "` may represent the same identifier but fail to match without normalization.

### Using the wrong join type

An inner join can remove records that have no reference-data match.

### Confusing merge and append

Merge is relationship-based horizontal enrichment.

Append is vertical row combination.

### Removing duplicates without defining a key

A duplicate business record must be defined using business meaning rather than only visual similarity.

### Silently converting errors to null

Replacing every conversion error with null can hide source-quality problems.

Error handling should preserve enough information to investigate the original problem.

### Performing unnecessary transformations

Each additional operation can increase processing time and complexity.

### Assuming the source schema is permanent

External files, APIs, and database queries can change.

Production pipelines should detect important schema changes.

### Ignoring relationships

A successful technical join does not guarantee a correct business relationship.

A customer table containing duplicate `CustomerID` values can produce ambiguous results.

## Edge cases

Important ETL edge cases include:

- empty source tables
- missing required columns
- missing values
- invalid numeric values
- invalid dates
- negative quantities
- negative prices
- zero quantities
- zero prices
- duplicate keys
- duplicate records
- unmatched reference records
- null join keys
- inconsistent capitalization
- leading or trailing whitespace
- changed source schemas
- different column orders
- different data types
- different currencies
- locale-dependent number formats
- time-zone differences
- malformed files
- unexpected encodings
- very large datasets

These cases should be considered explicitly rather than assumed to be impossible.

## Merge and append comparison

| Property | Merge | Append |
|---|---|---|
| Direction | Horizontal | Vertical |
| Main purpose | Enrichment | Combining compatible datasets |
| Relationship key | Usually required | Not normally required |
| Main effect | Adds columns | Adds rows |
| Example | Sales + Customers | January + February sales |
| Main risk | Incorrect relationship | Incompatible schemas |

## Python, JavaScript, and C++ comparison

| Characteristic | Python | JavaScript | C++ |
|---|---|---|---|
| Main demonstration | Broad ETL concepts | Application/data processing | Strongly typed case study |
| Primary records | Dictionaries | Objects | Structs |
| Collections | Lists | Arrays | Vectors |
| Lookup index | Dictionary | Map | unordered_map |
| Missing value | `None` | `null` | `optional` |
| Type discipline | Dynamic | Dynamic | Static |
| JSON use | Standard library | Native ecosystem | Manual modeling |
| Async example | Not central | Promise/async | Not central |
| Memory control | Higher-level | Higher-level | Explicitly controllable |
| Typical strength | Rapid data processing | Web/API integration | Performance and systems control |

## Security considerations

ETL systems frequently process sensitive information.

Important practices include:

- do not hard-code database passwords
- do not expose API credentials in source files
- use secure authentication mechanisms
- limit access to sensitive datasets
- minimize unnecessary personal information
- protect exported files
- use encrypted connections where supported
- validate external input
- log failures without exposing secrets
- apply appropriate retention policies
- control who can refresh or modify production queries

Data transformation does not remove the need for data security.

## Production considerations

A production ETL pipeline should consider:

### Data lineage

Record where data originated and which transformations were applied.

### Observability

Track:

- row counts
- processing duration
- rejected records
- validation failures
- source availability
- destination status

### Reproducibility

The same source data and transformation definitions should produce the same result unless nondeterministic behavior is explicitly required.

### Idempotent loading

Repeated execution should not unintentionally duplicate records.

### Schema evolution

Source systems can add, remove, rename, or change columns.

### Error isolation

Record-level errors should be separated from pipeline-level failures where possible.

### Data quality

Validation rules should reflect actual business requirements.

### Performance

Large datasets require attention to:

- memory
- network transfer
- source-side processing
- query folding
- indexing
- unnecessary transformations
- repeated scans

## Practical applications

Power Query-style ETL techniques are applicable to:

- financial reporting
- sales analytics
- inventory analysis
- customer analytics
- operational dashboards
- HR reporting
- procurement analysis
- marketing data preparation
- data warehouse preparation
- management reporting
- recurring Excel reporting
- Power BI data models
- multi-file consolidation
- API data preparation

The fundamental pattern remains the same:

`Extract -> Validate -> Transform -> Combine -> Aggregate -> Load`

## Implementation considerations

A robust transformation pipeline should make the meaning of each step clear.

For the sales case study, the resulting analytical record contains:

- order identifier
- order date
- customer identifier
- product identifier
- quantity
- unit price
- region
- calculated sales amount
- customer name
- customer segment
- product name
- product category
- year
- month
- quarter
- order value classification

The three implementations reach this conceptual result using different programming models.

Python emphasizes readable data manipulation and reusable transformation functions.

JavaScript emphasizes arrays, objects, functional transformations, lookup maps, JSON, and asynchronous extraction.

C++ emphasizes explicit data models, validation, efficient hash-based joins, modular functions, and a strongly typed architecture.

## Real-world relevance

Power Query fundamentals are not limited to simple spreadsheet cleaning.

The same concepts appear in larger data engineering systems:

- source ingestion
- schema validation
- data type enforcement
- data cleansing
- dimensional enrichment
- joins
- union operations
- aggregation
- data quality monitoring
- transformation lineage
- performance optimization
- repeatable refreshes
- analytical data modeling

Understanding the difference between extraction, transformation, merging, appending, filtering, typing, and loading provides the foundation for designing reliable data-preparation workflows.
