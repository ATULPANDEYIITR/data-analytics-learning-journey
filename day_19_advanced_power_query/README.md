# Advanced Power Query

## Topic

This study focuses on advanced Power Query concepts related to query folding, custom columns, conditional columns, parameters, and reusable transformations.

The implementations use Python, JavaScript, and C++ to model the underlying transformation principles. Power Query itself uses the M language, so the examples are designed to explain how Power Query works rather than to imply that Python, JavaScript, or C++ are replacements for M.

The central idea is to treat a data preparation workflow as a sequence of transformations applied to a source dataset. Some transformations can be translated into operations understood by the source system, while others must be executed by the Power Query engine. Understanding that distinction is essential for building maintainable and performant queries.

## Power Query and the M language

Power Query uses the M language for data acquisition, transformation, type conversion, filtering, joining, grouping, parameterization, and reusable functions.

A Power Query expression commonly follows the pattern:

`Source -> Transformation 1 -> Transformation 2 -> Transformation 3`

A query can therefore be understood as a transformation pipeline.

A simple conceptual M expression for filtering rows is:

`Table.SelectRows(Source, each [Region] = "North")`

A custom column can be represented conceptually as:

`Table.AddColumn(Source, "Tax", each [Amount] * 0.18)`

A conditional column can be represented as:

`Table.AddColumn(Source, "Band", each if [Amount] >= 2000 then "High" else "Standard")`

The M language is functional in nature. Expressions produce values, functions accept values and return values, and a sequence of transformations can be composed into a larger query.

## Fundamental terminology

### Query

A query is a sequence of expressions that retrieves and transforms data.

The query may contain:

- source connection logic
- navigation to a table or object
- type conversions
- filtering
- column selection
- custom calculations
- conditional logic
- joins
- grouping
- sorting
- parameter usage
- reusable functions
- output shaping

### Source

The source is the origin of the data.

Common examples include:

- SQL databases
- Excel workbooks
- CSV files
- SharePoint
- OData services
- APIs
- cloud platforms
- folders
- other Power Query-supported connectors

The capabilities of the source and connector have a major effect on query folding.

### Transformation

A transformation changes the structure, content, type, or meaning of the data.

Examples include:

- filtering rows
- selecting columns
- renaming columns
- changing data types
- replacing values
- adding columns
- merging tables
- appending tables
- grouping rows
- sorting
- pivoting
- unpivoting

### Query folding

Query folding is the process by which Power Query attempts to translate compatible transformations into operations that the underlying data source can execute.

For a relational database, a Power Query pipeline such as:

`Source -> Filter -> Select Columns -> Sort`

may conceptually become:

`SELECT OrderID, Customer, Amount FROM Sales WHERE Region = 'North' ORDER BY Amount DESC`

The actual generated query depends on the connector, source system, transformations, data types, and other contextual factors.

Query folding is important because a database can often process data closer to its storage layer, reducing the amount of information that needs to be transferred and processed locally.

## Why query folding matters

Suppose a database contains 10 million rows, but the report requires only 20,000 rows.

If the source can execute the filter, the database may return only the required rows.

If the filter cannot be pushed to the source, Power Query may need to retrieve substantially more data before applying the filter locally.

The potential consequences of local processing include:

- greater network transfer
- increased memory usage
- higher CPU consumption
- longer refresh times
- greater source and client resource usage

The exact performance impact depends on the connector, source system, network, query design, hardware, indexes, and data volume.

## Foldable and non-foldable transformations

A transformation is often described as foldable when the connector can translate it into an operation supported by the source.

Typical relational operations that may fold include:

- row filtering
- column projection
- sorting
- grouping
- joins
- basic aggregations
- some type conversions
- some arithmetic expressions

This is not a universal list.

Foldability is dependent on context.

A transformation may fold against one source and fail to fold against another.

The same M expression can therefore have different execution behavior depending on the connector and source.

The Python implementation represents this using `QueryPlan` and `Operation` objects. Each operation has a `foldable` property. The model identifies the first non-foldable operation as a folding boundary.

The JavaScript implementation uses `QueryOperation` and `QueryPlan` for the same purpose.

The C++ case study uses an `Operation` structure and a `QueryPlan` class to distinguish source-side and local stages.

These models are educational representations. They do not reproduce the internal query-folding implementation of Power Query.

## Folding boundaries

A folding boundary occurs when the query reaches a transformation that the source cannot execute through the connector.

Conceptually:

`Source -> Filter -> Select Columns -> Custom Logic`

If the first three operations fold but the custom logic does not, the source may execute the first portion and Power Query may execute the remaining portion.

This creates a useful mental model:

`Source-side execution -> Folding boundary -> Local execution`

Operations after the boundary are not automatically pushed back through the boundary.

This is one reason transformation order matters.

## Filtering early

One of the most important design principles is to reduce unnecessary data as early as practical.

Consider:

`Source -> Filter -> Custom Calculation`

versus:

`Source -> Custom Calculation -> Filter`

If the custom calculation is expensive and cannot fold, the second arrangement can require the calculation to run for many more rows.

The Python implementation demonstrates this with a large generated dataset and compares applying an expensive calculation before and after filtering.

The JavaScript implementation performs the same conceptual comparison.

The C++ implementation places region, date, and minimum-amount filtering in a source-oriented stage before custom calculations and joins.

Early filtering is particularly important for large relational sources because a filter that folds can potentially be executed by the database before data reaches the Power Query engine.

## Selecting columns early

Reducing columns can also reduce unnecessary data movement and memory consumption.

A query that needs only:

`OrderID, Customer, Region, Amount`

does not necessarily benefit from carrying dozens of unrelated columns through every subsequent transformation.

The Python script demonstrates column projection with `select_columns`.

The JavaScript implementation provides `selectColumns`.

The C++ query plan explicitly models `SelectColumns` as a foldable operation.

In relational systems, column projection can often be represented by a database `SELECT` list.

## Custom columns

A custom column is a derived column calculated from existing data.

For example:

`Tax = Amount * 0.18`

can be represented in M as:

`Table.AddColumn(Source, "Tax", each [Amount] * 0.18)`

Custom columns are useful for:

- financial calculations
- classifications
- date calculations
- normalization
- derived metrics
- business rules
- flags
- ratios
- text transformations

The Python implementation uses `add_column` with a callable expression.

The JavaScript implementation uses `addColumn` with a callback.

The C++ case study creates `estimatedMargin` and `amountBand` as derived fields.

### Custom column design considerations

A custom expression should be:

- deterministic when possible
- explicit about null behavior
- appropriate for the column's data type
- easy to understand
- tested against boundary conditions
- separated from unrelated business rules

A complex local custom calculation can also affect query folding.

If the source cannot translate the expression, it may create a folding boundary.

## Conditional columns

A conditional column assigns a value according to one or more rules.

A typical structure is:

`if condition1 then result1 else if condition2 then result2 else result3`

For example:

`if [Amount] >= 2000 then "High" else if [Amount] >= 1000 then "Medium" else "Low"`

The order of conditions matters.

For an amount of 2500:

- `Amount >= 2000` is true
- `Amount >= 1000` is also true

The first condition determines the result.

This means conditional rules should normally be ordered from the most specific or restrictive conditions to broader conditions when the rules overlap.

The Python implementation provides `risk_category`.

The JavaScript implementation provides `riskCategory`.

The C++ implementation provides `determineBusinessAction`.

The C++ case study uses several business rules involving credit score and transaction amount.

## Null handling

Null values are a major consideration in data transformation.

A column may contain:

- valid values
- null values
- empty strings
- invalid text
- unexpected types
- missing fields

A custom expression should define how nulls are treated.

The Python script uses `safe_decimal` to convert values while treating invalid values as `None`.

The JavaScript implementation uses `safeNumber`.

The C++ implementation uses explicit validation for numeric values.

A common design error is to assume that every source value is valid simply because most rows appear correct.

Production data pipelines should treat unexpected values as normal operational possibilities rather than exceptional impossibilities.

## Data types

Power Query has explicit data types, including:

- text
- number
- decimal
- percentage
- date
- datetime
- datetimezone
- duration
- logical
- binary
- table
- record
- list

Correct data typing affects:

- comparisons
- arithmetic
- sorting
- joins
- grouping
- filtering
- source translation
- output behavior

For example, the text values `"100"` and `"20"` do not behave like numeric values `100` and `20`.

Explicit type conversion is therefore important before numerical or date-based business logic.

## Parameters

Parameters allow configurable values to be separated from transformation logic.

A query might use parameters such as:

- minimum amount
- region
- start date
- end date
- fiscal year
- environment
- source server
- file location

Conceptually:

`Table.SelectRows(Source, each [Amount] >= MinimumAmount)`

uses `MinimumAmount` as a parameter.

The Python implementation uses the immutable `QueryParameters` data class.

The JavaScript implementation uses an immutable parameter object.

The C++ case study uses the `Parameters` structure.

Parameters make a transformation pipeline more reusable because the transformation logic does not have to be rewritten every time the filtering requirement changes.

## Parameter validation

Parameters should not automatically be treated as trusted values.

The C++ implementation explicitly validates:

- minimum amount
- selected region
- margin rate
- date ordering

The JavaScript implementation validates parameter types and ranges.

The Python implementation uses typed parameters and explicit transformation logic.

Validation can prevent:

- invalid ranges
- accidental empty results
- incorrect calculations
- inconsistent business logic
- runtime errors

A parameter should have a clearly defined meaning, type, valid range, and default behavior where appropriate.

## Date parameters

Date filtering is particularly useful for large transactional datasets.

A common pattern is a half-open interval:

`start <= date < end`

For example:

`2026-09-01 <= OrderDate < 2026-10-01`

This includes every date in September without including October 1.

The half-open interval is useful for partitioning because adjacent ranges do not overlap.

For example:

`[2026-09-01, 2026-10-01)`

followed by:

`[2026-10-01, 2026-11-01)`

does not duplicate the boundary date.

The Python, JavaScript, and C++ implementations all model date-range filtering.

## Reusable transformations

Reusable transformations prevent repeated business logic from appearing in multiple queries.

A conceptual M function may have the form:

`(inputTable as table, threshold as number) as table => Table.SelectRows(inputTable, each [Amount] >= threshold)`

The Python implementation uses `standardize_sales_table`.

The JavaScript implementation uses `standardizeSalesTable`.

The C++ implementation separates the pipeline into functions such as:

- `sourceFilter`
- `createCustomColumns`
- `joinCustomerMetadata`
- `aggregateByRegion`
- `validateParameters`

A reusable transformation should have:

- explicit inputs
- explicit outputs
- predictable behavior
- well-defined error handling
- minimal hidden state
- meaningful naming
- documented assumptions

## Function composition

Power Query's functional nature makes transformation composition an important concept.

A conceptual pipeline can be expressed as:

`Filter -> Filter -> Custom Calculation`

The Python implementation provides `compose`.

The JavaScript implementation also provides `compose`.

The approach makes a transformation pipeline explicit and allows individual operations to be tested independently.

Function composition is particularly useful when several datasets need to undergo the same standardization process.

## Grouping and aggregation

Grouping combines rows according to one or more keys and calculates aggregate values.

Common aggregations include:

- sum
- average
- minimum
- maximum
- count
- distinct count

The Python implementation provides `group_sum`.

The JavaScript implementation provides `groupBySum`.

The C++ case study provides `aggregateByRegion`.

The C++ implementation calculates:

- total amount
- transaction count
- average amount

For large relational datasets, grouping can often benefit from source-side execution because database engines have specialized aggregation algorithms and query optimizers.

## Joins

A merge in Power Query combines information from related tables.

For example:

`Sales.Customer -> Customers.Customer`

can attach customer metadata to transaction records.

The C++ case study uses a hash index to implement an inner join.

For `n` sales rows and `m` customer rows, a hash join has average conceptual complexity of:

`O(n + m)`

The actual performance of a database join depends on factors such as:

- indexes
- join strategy
- cardinality
- statistics
- memory
- partitioning
- source optimizer behavior

Power Query's merge behavior should therefore be understood in the context of the connector and source system rather than only the local transformation expression.

## Transformation ordering

The order of transformations is not merely a matter of readability.

Consider:

`Filter -> Select Columns -> Expensive Custom Calculation`

and:

`Expensive Custom Calculation -> Filter`

If the filter reduces the dataset from one million rows to twenty thousand, executing an expensive non-foldable calculation after filtering can substantially reduce local work.

This is especially important when:

- the source contains millions of rows
- network transfer is significant
- custom logic is expensive
- local memory is constrained
- refresh windows are limited

The Python, JavaScript, and C++ implementations all emphasize early reduction of data.

## Query folding and source systems

Relational databases are particularly relevant to query folding because they naturally support operations such as:

- `WHERE`
- `SELECT`
- `ORDER BY`
- `GROUP BY`
- `JOIN`
- aggregate functions

A conceptual foldable Power Query pipeline might therefore become:

`SELECT OrderID, Customer, Amount FROM Sales WHERE Region = 'North'`

The source database may then use indexes, statistics, parallel execution, caching, and query optimization.

This can be very different from retrieving all rows and performing every operation locally.

## Connector dependency

There is no universal rule that an operation always folds.

Foldability depends on:

- connector implementation
- source system
- M expression
- operation type
- data types
- source capabilities
- transformation order
- native-query boundaries

For this reason, query-folding analysis should be performed against the actual source and connector rather than inferred from a generic list of supposedly foldable operations.

## Native queries

Power Query can work with native source queries in some connector scenarios.

Native queries can provide precise source-side control, but they introduce connector-specific behavior and can influence subsequent folding.

A native query should be treated as an architectural boundary that requires deliberate testing.

Security is also important when constructing native SQL.

Untrusted values should not be concatenated into SQL without appropriate protection.

Parameters and connector-supported mechanisms should be preferred where available.

## Buffering and materialization

Materializing a table can sometimes prevent repeated evaluation of an expression.

The Python and JavaScript implementations contain simplified lazy-table models that demonstrate the distinction between repeated evaluation and cached materialization.

The important point is that buffering is not automatically a performance optimization.

Potential benefits include:

- avoiding repeated evaluation
- stabilizing a snapshot for repeated local use
- controlling certain evaluation behaviors

Potential costs include:

- increased memory usage
- additional materialization time
- loss of beneficial source-side execution
- greater local processing

Buffering should therefore be introduced because of a demonstrated execution requirement, not simply because it sounds like a general optimization.

## Performance considerations

Important performance factors include:

### Reduce rows early

Use restrictive source-side filters when possible.

### Reduce columns early

Carry only fields required by downstream logic.

### Preserve folding when useful

Avoid unnecessary operations that force local execution.

### Minimize expensive custom calculations

Especially before filtering.

### Use appropriate source-side operations

Relational databases can often execute joins, aggregations, and filters efficiently.

### Avoid unnecessary materialization

Materialization can increase memory pressure.

### Measure actual refresh behavior

The fastest-looking M expression is not necessarily the fastest expression for a particular connector and dataset.

### Consider source indexes

For relational sources, appropriate indexes can significantly affect the cost of folded filters and joins.

### Consider cardinality

Joins and grouping behave differently depending on the number and distribution of distinct values.

## Complexity considerations

The Python implementation describes several common algorithmic costs.

Filtering is typically:

`O(n)`

A hash-based join is typically:

`O(n + m)`

Sorting is generally:

`O(n log n)`

Hash-based grouping is typically:

`O(n)` on average.

These are simplified algorithmic models.

Actual performance can differ because real systems use:

- query optimizers
- indexes
- vectorized execution
- parallel processing
- caching
- compression
- partitioning
- statistics
- specialized storage engines

A local transformation and a database transformation may therefore have the same mathematical result but very different execution characteristics.

## Error handling

Data transformation systems should expect errors.

Common data errors include:

- invalid numeric values
- malformed dates
- missing columns
- null values
- incompatible types
- duplicate keys
- unexpected categories
- invalid parameter values

The Python implementation uses safe numeric conversion.

The JavaScript implementation uses `safeNumber` and explicit parameter validation.

The C++ implementation uses exceptions for invalid parameters and failure conditions.

Error handling should preserve enough information to identify the cause without exposing sensitive source data.

## Edge cases

Important edge cases include:

- zero
- negative numbers
- null values
- invalid numeric text
- `NaN`
- extremely large values
- empty strings
- missing records
- missing join keys
- duplicate keys
- date boundaries
- empty result sets

The implementations deliberately include several of these cases.

For example, the Python script distinguishes:

- `None`
- negative values
- `NaN`
- very large values

The JavaScript implementation distinguishes:

- `null`
- `NaN`
- negative values
- zero

The C++ implementation validates finite numeric values and handles missing customer metadata during joins.

## Conditional-rule design

Conditional logic should be written so that rules are:

- mutually understandable
- ordered deliberately
- testable
- documented
- resistant to unexpected nulls

Suppose the rules are:

`Amount >= 5000 -> SeniorApproval`

`Amount >= 2000 -> ManagerApproval`

`Amount >= 1000 -> StandardApproval`

The ordering is significant because a value of 6000 satisfies all three numeric thresholds.

The first matching rule should therefore be the most restrictive.

## Reusability and maintainability

Reusable transformations provide a central location for repeated business logic.

Without reusable functions, multiple queries might independently implement customer normalization, date filtering, or classification rules.

That creates risks such as:

- inconsistent business rules
- duplicated maintenance
- difficult testing
- divergent results
- difficult auditing

A reusable function provides a controlled interface:

`Input -> Transformation -> Output`

Parameters can control behavior without duplicating the transformation itself.

## Python implementation

The Python implementation is primarily an educational transformation engine.

It demonstrates:

- table representation using lists of dictionaries
- row filtering
- column projection
- custom columns
- conditional columns
- null handling
- numeric conversion
- query-plan modeling
- conceptual SQL generation
- folding boundaries
- parameters
- reusable transformations
- function composition
- grouping
- hash joins
- date filtering
- lazy evaluation
- buffering concepts
- validation
- testing
- performance comparisons
- security considerations
- declarative transformation specifications

The `QueryPlan` class is particularly important because it separates the concept of a transformation from its execution location.

The script does not claim to reproduce the actual Power Query engine. Its purpose is to make the underlying architecture executable and observable.

## JavaScript implementation

The JavaScript implementation emphasizes functional and application-level transformation patterns.

It demonstrates:

- array-based row filtering
- object-based column projection
- callback-driven custom columns
- conditional logic
- type validation
- reusable transformation functions
- function composition
- grouping
- hash joins
- parameter objects
- asynchronous source acquisition
- lazy evaluation
- buffering concepts
- validation
- folding-plan modeling
- performance-oriented ordering
- error-resilient calculations
- testing

JavaScript is useful for demonstrating how transformation concepts relate to modern application programming because functions can be passed as values, asynchronous acquisition can be modeled directly, and objects and arrays naturally represent small tabular structures.

The JavaScript implementation intentionally does not depend on npm packages.

## C++ case study

The C++ program models a retail analytics pipeline.

The scenario contains:

`Sales source -> parameterized filtering -> custom columns -> customer join -> conditional business rules -> aggregation`

The source contains:

- order ID
- customer
- region
- amount
- order date

The customer table contains:

- customer
- segment
- credit score

The parameter structure contains:

- minimum amount
- selected region
- start date
- end date
- margin rate

### C++ case-study problem

The organization wants to create a reusable transaction-processing pipeline that reduces source data, enriches transactions, calculates business metrics, applies approval rules, and produces regional aggregates.

The design deliberately separates source-oriented operations from local transformations.

### C++ source filtering

`sourceFilter` applies:

- region filtering
- date filtering
- minimum amount filtering
- numeric validation

This represents the type of operation that may fold into a relational source.

### C++ custom columns

`createCustomColumns` creates:

- normalized customer name
- estimated margin
- amount band

The estimated margin is calculated from:

`Amount * MarginRate`

The amount band is produced through conditional rules.

### C++ join

`joinCustomerMetadata` builds an `unordered_map` keyed by customer name.

This provides average constant-time lookup and results in average:

`O(n + m)`

join behavior.

### C++ conditional rules

`determineBusinessAction` uses:

- credit score
- amount thresholds
- ordered approval rules

This demonstrates how a Power Query conditional-column concept can become a business-rule function in a larger system.

### C++ aggregation

`aggregateByRegion` calculates:

- total amount
- transaction count
- average amount

The results are sorted by total amount.

### C++ diagnostics

The program records:

- source row count
- rows after filtering
- final row count
- number of foldable operations
- number of local operations
- local execution time

These metrics are simplified educational diagnostics rather than replacements for actual Power Query diagnostics.

## Important distinctions

### Custom column versus conditional column

A custom column is a general expression.

A conditional column is primarily rule-based.

For example:

`Tax = Amount * 0.18`

is a custom calculation.

`if Amount >= 2000 then "High" else "Standard"`

is conditional logic.

The two concepts can overlap because a conditional expression is technically also a calculated expression, but the distinction is useful when designing business transformations.

### Parameter versus column

A parameter is external configuration.

A column belongs to the dataset.

For example:

`MinimumAmount`

can be a parameter.

`Amount`

is a column.

The query can compare:

`Amount >= MinimumAmount`

This separates configuration from data.

### Parameter versus hard-coded value

Hard-coded:

`[Amount] >= 1000`

Parameterized:

`[Amount] >= MinimumAmount`

The second form allows the same transformation logic to operate under different configurations.

### Foldable versus local operation

A foldable operation can potentially execute at the source.

A local operation executes within the Power Query environment after the relevant folding boundary.

The actual execution behavior is connector-dependent.

### Source-side processing versus local processing

Source-side processing can take advantage of database capabilities.

Local processing occurs after data has been made available to the Power Query engine.

Neither category is universally superior. The appropriate design depends on source capabilities, data volume, transformation requirements, and operational constraints.

## Common mistakes

### Assuming every transformation folds

Power Query does not guarantee folding for every M expression.

### Filtering after expensive custom logic

This can cause unnecessary local work.

### Carrying unnecessary columns

Unused columns increase data volume and can complicate downstream processing.

### Ignoring types

Text values that represent numbers should not automatically be treated as numeric values.

### Ignoring nulls

A transformation that works for complete data can fail when null values appear.

### Using overlapping conditional rules without deliberate ordering

The first matching branch determines the result.

### Hard-coding configuration

Important business thresholds should often be represented as parameters.

### Duplicating transformation logic

Repeated transformations can drift apart over time.

### Buffering indiscriminately

Materialization can increase memory consumption and interfere with folding.

### Ignoring source behavior

A transformation strategy should consider the actual connector and source system.

### Ignoring privacy boundaries

Combining data sources can have governance implications.

## Security considerations

Power Query solutions can interact with databases, files, APIs, cloud services, and other data sources. Security therefore includes both transformation logic and source governance.

Important principles include:

- do not store credentials in transformation expressions
- use appropriate credential-management mechanisms
- use least-privilege source accounts
- validate parameter inputs
- treat external data as untrusted
- avoid unsafe dynamic SQL
- understand source privacy boundaries
- limit access to sensitive datasets
- avoid unnecessary copies of sensitive data
- review reusable functions for unintended exposure
- audit native queries where applicable

A technically correct transformation can still be operationally unsafe if it exposes credentials or sensitive data.

## Production considerations

A production Power Query solution should consider:

- source reliability
- refresh duration
- data volume
- connector capabilities
- query folding
- data types
- parameter governance
- error handling
- data quality
- credential management
- privacy boundaries
- monitoring
- reproducibility
- maintainability

A transformation should be designed not only to produce the correct output but also to behave predictably as data volume and source complexity increase.

## Reusable transformation architecture

A practical reusable design can be represented as:

`Source`

then:

`Source-side filters`

then:

`Column projection`

then:

`Type normalization`

then:

`Reusable transformation`

then:

`Business calculations`

then:

`Joins`

then:

`Conditional classifications`

then:

`Aggregation`

then:

`Output`

This is not a mandatory sequence for every Power Query solution. The correct sequence depends on which transformations fold and what the source can execute.

The important architectural principle is to make execution boundaries deliberate.

## Practical applications

Advanced Power Query techniques are useful in:

- financial reporting
- sales analytics
- operational reporting
- supply-chain analysis
- customer analytics
- inventory management
- management dashboards
- regulatory reporting
- data-quality workflows
- business intelligence
- recurring Excel transformations
- Power BI semantic-model preparation
- multi-source data integration

A reusable transformation can be applied to recurring monthly or daily data without rebuilding the logic manually.

Parameters can make the same query operate for different:

- regions
- periods
- thresholds
- environments
- source locations

Query folding can reduce the amount of work performed by the local transformation engine when the source and connector support it.

## Implementation correspondence

| Concept | Python implementation | JavaScript implementation | C++ case study |
|---|---|---|---|
| Row filtering | `filter_rows` | `selectRows` | `sourceFilter` |
| Column selection | `select_columns` | `selectColumns` | `SelectColumns` query operation |
| Custom columns | `add_column` | `addColumn` | `createCustomColumns` |
| Conditional columns | `risk_category` | `riskCategory` | `determineBusinessAction` |
| Parameters | `QueryParameters` | parameter object | `Parameters` |
| Reusable transformation | `standardize_sales_table` | `standardizeSalesTable` | modular pipeline functions |
| Function composition | `compose` | `compose` | sequential modular stages |
| Grouping | `group_sum` | `groupBySum` | `aggregateByRegion` |
| Join | `inner_join` | `innerJoin` | `joinCustomerMetadata` |
| Folding model | `QueryPlan` | `QueryPlan` | `QueryPlan` |
| Folding boundary | `folding_stops_at` | `getFoldingBoundary` | `foldingBoundary` |
| Validation | explicit conversion and assertions | validation functions | exceptions |
| Performance | timing comparison | `console.time` | `chrono` |
| Lazy evaluation | `LazyTable` | `LazyTable` | modeled through staged execution |
| Diagnostics | `QueryMetrics` | folding descriptions | `QueryMetrics` |

## Why the three languages are different

Python is well suited to demonstrating data manipulation because lists, dictionaries, functions, and comprehensions provide concise representations of transformation pipelines.

JavaScript is useful for showing functional callbacks, object-based data manipulation, asynchronous acquisition, and application-level transformation patterns.

C++ provides a more explicit systems-oriented implementation. Types, memory-oriented data structures, hash indexes, exceptions, and algorithmic complexity make the implementation details visible.

None of these languages implements the Power Query engine. They model the principles so that the behavior can be studied independently of a particular graphical environment.

## Testing strategy

Reusable transformations should be tested with:

- normal inputs
- empty inputs
- null values
- invalid values
- boundary values
- negative values
- large values
- missing join keys
- invalid parameters
- date boundaries

The Python implementation uses `assert_equal`.

The JavaScript implementation uses a custom `assertEqual`.

The C++ implementation uses explicit runtime checks and exceptions.

Tests should verify both expected outputs and expected failure behavior.

## Data-quality considerations

A transformation pipeline should establish explicit rules for:

- missing values
- invalid values
- duplicates
- type conversion
- inconsistent capitalization
- whitespace
- date formats
- numerical precision
- invalid business states

For example, customer names such as:

`"  alpha   ltd "`

and:

`"ALPHA LTD"`

may need to resolve to the same normalized representation before a join.

Normalization is therefore not merely cosmetic. It can affect join correctness.

## Numerical considerations

Financial and analytical transformations should be careful about numerical representation.

The Python script uses `Decimal` for selected validation examples because decimal arithmetic can be preferable for financial-style calculations.

JavaScript uses IEEE-754 floating-point numbers for its ordinary numeric type.

C++ uses `double` in the case study.

For production financial systems, numerical representation should be selected according to precision requirements, source data types, reporting rules, and rounding policies.

## Date and time considerations

Date transformations should distinguish among:

- date
- datetime
- datetime with timezone
- duration

Date boundaries should be defined explicitly.

The half-open interval:

`start <= value < end`

is particularly useful for partitioning and recurring refresh periods.

Timezone-sensitive data requires additional care because a timestamp can represent different local times depending on its timezone context.

## Performance model

The most important performance distinction is often not the number of characters in an M expression but where the computation occurs.

A simple source-side filter over an indexed database column can be much cheaper than retrieving a large dataset and filtering locally.

A custom local transformation may be computationally inexpensive per row but still expensive when executed against millions of rows.

Performance therefore depends on both:

`Cost per row`

and:

`Number of rows processed`

Query folding can influence both.

## Design principles

A robust advanced Power Query design should generally aim to:

- understand the source
- understand connector capabilities
- filter early where appropriate
- select required columns early
- preserve useful folding
- use parameters for configuration
- encapsulate repeated transformations
- define null behavior
- define data types explicitly
- order conditional rules deliberately
- validate external inputs
- avoid unnecessary buffering
- test boundary conditions
- monitor refresh behavior
- protect credentials and sensitive data

These principles are more useful than treating query folding as a simple checklist of individual functions.

## Conceptual M patterns represented by the implementations

Filtering:

`Table.SelectRows(Source, each [Region] = "North")`

Column selection:

`Table.SelectColumns(Source, {"OrderID", "Customer", "Amount"})`

Custom calculation:

`Table.AddColumn(Source, "Tax", each [Amount] * 0.18)`

Conditional logic:

`Table.AddColumn(Source, "Band", each if [Amount] >= 2000 then "High" else "Standard")`

Parameter-driven filtering:

`Table.SelectRows(Source, each [Amount] >= MinimumAmount)`

Reusable function:

`(inputTable as table, threshold as number) as table => Table.SelectRows(inputTable, each [Amount] >= threshold)`

These expressions illustrate the conceptual relationship between M transformations and the executable transformation models in the three implementations.

## Limitations of the models

The Python, JavaScript, and C++ programs are educational implementations.

They do not reproduce:

- Power Query's internal evaluator
- connector-specific query translators
- the complete M language
- Power BI's refresh engine
- actual query-folding diagnostics
- source-specific query optimizers
- connector privacy enforcement
- Power Query credential infrastructure

The folding models intentionally simplify these mechanisms.

Their purpose is to make the major architectural concepts concrete:

`data source -> transformations -> folding boundary -> local processing -> result`

Understanding this model provides a foundation for reasoning about more complex Power Query pipelines.
