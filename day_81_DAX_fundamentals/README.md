# DAX Fundamentals: Measures, Calculated Columns, Calculated Tables, and Evaluation Context

## 1. Introduction

Data Analysis Expressions (DAX) is the formula language used by Power BI, Analysis Services Tabular, and Power Pivot. It supports analytical calculations over relational and tabular data models.

DAX is designed to evaluate expressions within a model containing tables, columns, relationships, and metadata. Its behavior depends on how expressions interact with the current evaluation context.

This project implements an educational sales analytics model across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The central subject areas are:

- DAX syntax and expressions
- Measures
- Calculated columns
- Calculated tables
- Row context
- Filter context
- Context transition
- CALCULATE
- FILTER
- ALL
- VALUES
- DISTINCTCOUNT
- SUMX
- Aggregation and reporting

The five implementations use equivalent analytical scenarios but provide different engineering perspectives. The programming-language implementations simulate selected DAX semantics. They are not complete DAX interpreters.

## 2. Analytical Data Model

The example uses a retail sales model with two principal business tables.

### Product dimension

| Product ID | Product | Category | Unit Price |
|---|---|---|---:|
| 1 | Laptop | Electronics | 1,000 |
| 2 | Phone | Electronics | 500 |
| 3 | Desk | Furniture | 300 |
| 4 | Chair | Furniture | 200 |
| 5 | Notebook | Stationery | 50 |

### Sales fact table

| Sale ID | Product ID | Date | Quantity | Unit Cost |
|---|---:|---|---:|---:|
| 101 | 1 | 2026-01-10 | 2 | 700 |
| 102 | 2 | 2026-01-11 | 4 | 300 |
| 103 | 3 | 2026-01-12 | 3 | 180 |
| 104 | 4 | 2026-01-13 | 5 | 120 |
| 105 | 5 | 2026-01-14 | 10 | 20 |
| 106 | 1 | 2026-02-10 | 1 | 700 |
| 107 | 2 | 2026-02-11 | 2 | 300 |
| 108 | 3 | 2026-02-12 | 4 | 180 |
| 109 | 4 | 2026-02-13 | 3 | 120 |
| 110 | 5 | 2026-02-14 | 5 | 20 |

The model follows a star-schema structure:

- Product dimension: descriptive product attributes.
- Category dimension: product classifications.
- Date dimension: calendar attributes.
- Sales fact: transactional quantities and costs.

The product dimension has a one-to-many relationship with the sales fact table through `ProductID`.

The category dimension filters products, and the product dimension filters sales. This relationship structure allows filters on descriptive dimensions to affect transactional calculations.

### Relationship diagram

    DimCategory
         |
         | 1 : Many
         |
    DimProduct
         |
         | 1 : Many
         |
      FactSales
         |
         | Many : 1
         |
       DimDate

The fact table stores events. Dimension tables describe the entities associated with those events.

## 3. DAX Syntax Fundamentals

DAX expressions use functions, operators, column references, table references, and measure references.

### Basic syntax

A measure definition follows this structure:

`Measure Name = Expression`

Examples:

- `Total Sales = SUMX(Sales, Sales[Quantity] * RELATED(Product[UnitPrice]))`
- `Total Quantity = SUM(Sales[Quantity])`
- `Total Cost = SUMX(Sales, Sales[Quantity] * Sales[UnitCost])`
- `Total Profit = [Total Sales] - [Total Cost]`

DAX table references use single quotation marks when needed, such as `'Product'`.

Column references use square brackets after the table name, such as `'Product'[UnitPrice]`.

Measures are referenced using square brackets, such as `[Total Sales]`.

### Important operators

| Operator | Purpose |
|---|---|
| `=` | Equality or assignment in a definition |
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `&&` | Logical AND |
| `||` | Logical OR |
| `&` | Text concatenation |
| `IN` | Membership testing |

DAX also supports comparison operators, logical expressions, and conditional expressions.

### Important functions

| Function | Purpose |
|---|---|
| `SUM` | Adds values in a column |
| `AVERAGE` | Calculates an arithmetic average |
| `COUNTROWS` | Counts rows in a table |
| `DISTINCTCOUNT` | Counts distinct column values |
| `CALCULATE` | Evaluates an expression under modified filter context |
| `FILTER` | Returns rows satisfying a condition |
| `ALL` | Removes applicable filters |
| `VALUES` | Returns distinct visible values |
| `SUMX` | Evaluates an expression for each row and sums the results |
| `RELATED` | Retrieves a related value from another table |
| `DIVIDE` | Performs division with optional zero-denominator handling |
| `SELECTEDVALUE` | Returns a single visible value when exactly one value is selected |

## 4. Measures

A measure is a calculation evaluated when required by a visual, query, or other expression.

Measures do not normally store a separate result for every fact-table row. Their results are calculated according to the current evaluation context.

### Example measures

Total Sales:

`Total Sales = SUMX(Sales, Sales[Quantity] * RELATED(Product[UnitPrice]))`

Total Cost:

`Total Cost = SUMX(Sales, Sales[Quantity] * Sales[UnitCost])`

Total Profit:

`Total Profit = [Total Sales] - [Total Cost]`

Total Quantity:

`Total Quantity = SUM(Sales[Quantity])`

Profit Margin:

`Profit Margin = DIVIDE([Total Profit], [Total Sales], 0)`

Average Selling Price:

`Average Selling Price = DIVIDE([Total Sales], [Total Quantity])`

Transaction Count:

`Transaction Count = COUNTROWS(Sales)`

### Expected results

| Measure | Result |
|---|---:|
| Total Sales | 4,995 |
| Total Cost | 2,840 |
| Total Profit | 2,155 |
| Total Quantity | 39 |
| Transaction Count | 10 |
| Profit Margin | 43.04% |

The profit margin is calculated as:

`Profit Margin = Total Profit / Total Sales * 100`

A measure can produce different results without changing its definition because its evaluation context changes.

For example, `[Total Sales]` returns the entire sales amount when no category filter is applied. When the Electronics category is selected, the same measure returns 3,000.

### Measure characteristics

- Evaluated when queried.
- Responds to filter context.
- Can reference other measures.
- Supports aggregation across dimensions.
- Does not inherently create one stored value per source row.
- Can be reused across multiple report visuals.

Measures are generally preferred for dynamic analytical calculations.

## 5. Calculated Columns

A calculated column is an expression evaluated separately for each row of a table.

Its result becomes a column in the model and is generally calculated during data refresh or model processing.

### Example calculated columns

Revenue:

`Revenue = Sales[Quantity] * RELATED(Product[UnitPrice])`

Total Cost:

`Total Cost = Sales[Quantity] * Sales[UnitCost]`

Profit:

`Profit = Sales[Revenue] - Sales[Total Cost]`

Profitability:

`Profitability = IF(Sales[Profit] > 0, "Profitable", "Non-Profitable")`

The examples use the current row's values.

### Characteristics

- Evaluated row by row.
- Results are stored in the model.
- Consume model memory.
- Can be used in grouping, filtering, and relationships.
- Usually update during model refresh.
- Do not dynamically recalculate their stored values for every visual interaction.

A calculated column is appropriate when a row-level attribute is required repeatedly, such as a transaction classification or product grouping.

A measure is more suitable when the result must respond dynamically to report filters.

### Calculated column versus measure

| Property | Calculated Column | Measure |
|---|---|---|
| Evaluation | Row by row | At query time |
| Storage | Stored result | Usually not stored per row |
| Context | Row context during calculation | Filter context during evaluation |
| Report filtering | Can be used as a field | Changes calculation result |
| Memory usage | Adds model storage | Generally lower persistent storage |
| Typical use | Classification and grouping | Dynamic aggregation |

A frequent modeling mistake is creating a calculated column for a value that should be a dynamic measure.

For example, storing a single overall sales total in every transaction row is inefficient and can produce misleading results when users filter reports.

## 6. Calculated Tables

A calculated table is a table created from a DAX table expression.

Its contents are generally calculated during model processing or refresh rather than being recalculated independently for every visual interaction.

### Example: product table

`Product List = DISTINCT(Product[ProductName])`

### Example: category summary

`Category Summary = SUMMARIZE(Product, Product[Category], "Product Count", COUNTROWS(Product))`

### Example: filtered product table

`High Value Products = FILTER(Product, Product[UnitPrice] >= 500)`

### Characteristics

- Produces a complete table rather than one scalar value.
- Can contain calculated rows and columns.
- Can participate in relationships.
- Can support segmentation and intermediate modeling.
- Consumes model memory.
- Is generally recalculated during refresh or processing.

Calculated tables are useful for disconnected parameter tables, derived dimensions, grouped structures, and other model-level requirements.

They should not be confused with measures or ordinary calculated columns.

## 7. Evaluation Context

Evaluation context determines which data is available when a DAX expression is evaluated.

The two principal contexts are:

1. Row context.
2. Filter context.

Understanding their differences is essential for writing correct DAX expressions.

## 8. Row Context

Row context identifies the current row being evaluated.

It commonly appears in:

- Calculated columns.
- Iterator functions.
- Expressions that operate on individual table rows.

Example:

`Line Revenue = Sales[Quantity] * Sales[UnitCost]`

For every sales row, DAX retrieves the current row's quantity and unit cost and multiplies them.

An iterator such as `SUMX` also creates row context for its expression.

Example:

`Total Sales = SUMX(Sales, Sales[Quantity] * RELATED(Product[UnitPrice]))`

The expression is evaluated separately for each row of Sales. The resulting values are then summed.

### Important distinction

Row context identifies a row. It does not automatically filter every related table or change the evaluation of every measure.

The `RELATED` function retrieves a value through an appropriate existing relationship. It is not equivalent to automatically converting row context into filter context.

## 9. Filter Context

Filter context defines the rows and values available to an expression.

It can originate from:

- Visual-level filters.
- Page-level filters.
- Report-level filters.
- Slicers.
- Relationships.
- DAX functions.
- Query conditions.

Example:

`Total Sales = SUMX(Sales, Sales[Quantity] * RELATED(Product[UnitPrice]))`

When a report visual groups the result by Product Category, each category supplies a different filter context.

### Example results

| Category | Sales | Quantity |
|---|---:|---:|
| Electronics | 3,000 | 9 |
| Furniture | 2,600 | 15 |
| Stationery | 750 | 15 |
| Total | 4,995 | 39 |

The same measure is evaluated repeatedly under different filter contexts.

The total row is evaluated in its own context. It should not generally be assumed to equal the arithmetic sum of displayed percentages or other non-additive measures.

### Filter propagation

In a conventional single-direction star schema, a filter applied to a dimension can propagate to its related fact table.

For example:

`Product[Category] = "Electronics"`

restricts the products considered by the sales calculation.

This relationship-driven behavior is a fundamental part of tabular modeling.

## 10. Context Transition

Context transition converts an existing row context into filter context.

It is particularly important when `CALCULATE` or `CALCULATETABLE` is evaluated in a row context.

### Example

`Sales by Product = CALCULATE([Total Sales])`

When this expression is evaluated inside a suitable iterator over products, `CALCULATE` converts the current product row into corresponding filters.

The measure then evaluates using the resulting filter context.

### Why context transition matters

Consider an iterator over a product table.

The iterator creates row context. A measure evaluated within that row context undergoes automatic context transition.

This explains why measures inside iterators can produce different results from ordinary scalar expressions.

### Practical distinction

- Row context identifies the current row.
- Filter context restricts the visible data.
- Context transition converts applicable row-context values into filters.

These concepts are related but not interchangeable.

## 11. CALCULATE

`CALCULATE` evaluates an expression after modifying filter context.

It is one of the most important DAX functions.

### Syntax

`CALCULATE(Expression, Filter1, Filter2, ...)`

### Example: Electronics sales

`Electronics Sales = CALCULATE([Total Sales], Product[Category] = "Electronics")`

This expression evaluates the Total Sales measure under the specified category filter.

Expected result:

`3000`

### Example: removing a category filter

`All Category Sales = CALCULATE([Total Sales], REMOVEFILTERS(Product[Category]))`

This removes the applicable category filter while retaining other filters that remain active.

### Filter replacement

A Boolean filter argument normally replaces an existing filter on the same column unless the expression explicitly uses behavior such as `KEEPFILTERS`.

For example:

`CALCULATE([Total Sales], Product[Category] = "Furniture")`

evaluates the expression with the Furniture category filter.

The distinction between replacing filters and intersecting filters is important when multiple report filters are involved.

### CALCULATE and context transition

`CALCULATE` also performs context transition when invoked in an existing row context.

Its behavior therefore extends beyond simply adding a filter.

## 12. FILTER

`FILTER` returns a table containing rows that satisfy a specified condition.

### Syntax

`FILTER(Table, Condition)`

Example:

`High Value Sales = FILTER(Sales, Sales[Quantity] >= 5)`

A more analytical example is:

`High Value Revenue = SUMX(FILTER(Sales, Sales[Quantity] >= 5), Sales[Quantity] * RELATED(Product[UnitPrice]))`

The expression first identifies eligible sales rows and then calculates revenue for those rows.

### FILTER versus CALCULATE

| Function | Main purpose |
|---|---|
| FILTER | Produces a filtered table |
| CALCULATE | Evaluates an expression under modified filter context |

FILTER is often used as a table filter argument inside CALCULATE.

Example:

`Large Transaction Sales = CALCULATE([Total Sales], FILTER(Sales, Sales[Quantity] >= 5))`

FILTER evaluates the condition for the relevant rows. CALCULATE uses the resulting table filter when evaluating the measure.

## 13. ALL and Filter Removal

`ALL` can remove filters from a table or column and can return an unfiltered table expression.

Example:

`All Category Sales = CALCULATE([Total Sales], ALL(Product[Category]))`

This calculation removes the category filter.

Another example:

`All Product Sales = CALCULATE([Total Sales], ALL(Product))`

This removes filters from the Product table, subject to DAX relationship and filter-propagation behavior.

### ALL and percentage calculations

`Category Contribution = DIVIDE([Total Sales], CALCULATE([Total Sales], REMOVEFILTERS(Product[Category])))`

This calculates the category's contribution to sales across all categories while retaining other applicable filters.

### Important distinction

Removing one column's filter is not always equivalent to removing every filter from a table.

The exact result depends on the table structure, relationships, and other active filters.

Functions such as `ALL`, `REMOVEFILTERS`, and `ALLSELECTED` have different purposes and should not be treated as interchangeable.

## 14. VALUES and DISTINCTCOUNT

`VALUES` returns distinct values visible in the current filter context.

Example:

`Visible Categories = VALUES(Product[Category])`

When the current context contains only Electronics, the result contains the Electronics category.

`DISTINCTCOUNT` counts distinct values in a column.

Example:

`Distinct Products = DISTINCTCOUNT(Sales[ProductID])`

The result depends on the current filter context.

### Important distinction

- `VALUES` returns a table of visible distinct values.
- `DISTINCTCOUNT` returns a scalar count.
- `COUNTROWS` counts rows rather than distinct values.

These functions can produce different results when duplicate values exist.

## 15. SUMX and Iterator Functions

`SUMX` evaluates an expression for each row in a table and adds the resulting values.

### Syntax

`SUMX(Table, Expression)`

Example:

`Total Sales = SUMX(Sales, Sales[Quantity] * RELATED(Product[UnitPrice]))`

This expression:

1. Receives the Sales table.
2. Iterates over its rows.
3. Evaluates the expression for each row.
4. Retrieves the related product price.
5. Multiplies price by quantity.
6. Adds the calculated values.

### SUM versus SUMX

| Property | SUM | SUMX |
|---|---|---|
| Input | Column | Table and expression |
| Operation | Adds existing column values | Evaluates an expression per row |
| Row iteration | Not explicitly required | Yes |
| Typical use | Existing numeric column | Calculated row-level expressions |

Example:

`Total Quantity = SUM(Sales[Quantity])`

Example:

`Total Sales = SUMX(Sales, Sales[Quantity] * RELATED(Product[UnitPrice]))`

SUMX is appropriate when the required aggregation depends on an expression that must be evaluated separately for each row.

## 16. DAX Expression Categories

DAX expressions can be classified by their return type and evaluation purpose.

| Expression type | Output | Example |
|---|---|---|
| Scalar expression | One value | `[Total Sales]` |
| Table expression | A table | `FILTER(Product, Product[UnitPrice] > 500)` |
| Measure | Dynamic scalar result | `[Total Profit]` |
| Calculated column | Row-level stored value | `Sales[Quantity] * Sales[UnitCost]` |
| Calculated table | Derived table | `SUMMARIZE(Product, Product[Category])` |

Understanding whether a function expects a scalar, column, or table is important for avoiding DAX errors.

For example, FILTER returns a table and cannot independently serve as a scalar numeric measure.

## 17. Implementation Architecture

### Python

File: `dax_fundamentals.py`

The Python implementation models the analytical workflow through dataclasses and an evaluation-context object.

Important components:

- `Product` and `Sale`: immutable business records.
- `EvaluationContext`: stores active filters and row context.
- `DAXModel`: manages relationships, filtering, and measures.
- `calculate()`: applies filters and context transition.
- `filter_sales()`: evaluates row-level predicates.
- `sumx()`: performs expression-based aggregation.
- `create_calculated_columns()`: generates row-level results.
- `create_calculated_tables()`: creates derived table structures.
- `category_report()`: produces grouped analytical results.

The implementation uses `Decimal` to avoid the common binary floating-point inaccuracies associated with financial values.

It also validates product references, duplicate identifiers, quantities, and costs.

### JavaScript

File: `dax_fundamentals.js`

The JavaScript implementation uses an event-oriented and immutable-context design.

Important components:

- `FilterContext`: stores filter state.
- `DAXModel`: provides the analytical operations.
- `Map`: stores products and registered measures.
- `Set`: represents distinct filter values.
- `calculate()`: changes the evaluation context.
- `filter()`: applies predicates to visible transactions.
- `sumX()`: evaluates expressions over arrays.
- `exportReport()`: writes a structured JSON report.

The model uses asynchronous file operations and exclusive file creation to avoid silently overwriting existing reports.

### C++17

File: `dax_fundamentals.cpp`

The C++ implementation emphasizes explicit domain modeling and evaluation behavior.

Important components:

- `Product` and `Sale` structures.
- `EvaluationContext` for filter and row contexts.
- `DAXEngine` for analytical operations.
- STL containers for filter management and relationships.
- `optional` for calculations that have no valid result.
- `calculateContext()` for filter modification and context transition.
- `sumX()` for iterator-based aggregation.

The engine uses an unordered map for product lookup and avoids repeated linear searches when resolving product relationships.

### Java 17

File: `DAXFundamentals.java`

The Java implementation uses enterprise-oriented service design.

Important components:

- Records for immutable business entities.
- Enums for product categories and profitability.
- `EvaluationContext` for filter and row contexts.
- `Measure` as a functional interface.
- `AnalyticsService` for analytical operations.
- Immutable collections for model data.
- Streams for filtering, grouping, and aggregation.
- `DAXException` for domain validation failures.

`BigDecimal` is used for monetary calculations, with explicit rounding for percentage calculations.

### PostgreSQL

File: `dax_fundamentals.sql`

The SQL implementation provides a relational analytical model.

Important objects:

| Object | Purpose |
|---|---|
| `dim_category` | Product category dimension |
| `dim_product` | Product dimension |
| `dim_date` | Calendar dimension |
| `fact_sales` | Transaction fact table |
| `vw_sales_calculated_columns` | Row-level calculated expressions |
| `vw_sales_measures` | Category-level aggregations |
| `mv_category_summary` | Materialized calculated-table equivalent |
| `vw_monthly_sales` | Monthly aggregations |
| `vw_product_performance` | Product-level reporting |
| `fn_category_sales` | Parameterized category calculation |
| `fn_sumx_revenue` | Row-expression aggregation |
| `fn_high_value_sales` | Filtered transaction retrieval |
| `fn_validate_sales` | Data validation |

The SQL implementation also includes foreign keys, check constraints, indexes, transactions, materialized views, and reporting queries.

These objects demonstrate relational equivalents of selected analytical operations. PostgreSQL does not implement DAX evaluation context or model semantics.

## 18. Expected Analytical Results

The first ten transactions produce the following totals.

| Metric | Expected Value |
|---|---:|
| Revenue | 4,995.00 |
| Cost | 2,840.00 |
| Profit | 2,155.00 |
| Quantity | 39 |
| Transactions | 10 |
| Profit Margin | 43.04% |

### Category-level results

| Category | Revenue | Cost | Profit | Quantity |
|---|---:|---:|---:|---:|
| Electronics | 3,000 | 2,100 | 900 | 9 |
| Furniture | 2,600 | 1,680 | 920 | 15 |
| Stationery | 750 | 300 | 450 | 15 |
| Total | 4,995 | 2,840 | 2,155 | 39 |

The PostgreSQL script subsequently inserts one additional transaction to demonstrate transactional loading. Its final totals are therefore:

| Metric | Value After Additional Transaction |
|---|---:|
| Revenue | 5,995 |
| Cost | 3,540 |
| Profit | 2,455 |
| Quantity | 40 |
| Transactions | 11 |

The initial Python, JavaScript, C++17, and Java 17 examples validate the original ten transactions.

## 19. Important Distinctions

The following concepts must remain separate.

| Concept | Meaning |
|---|---|
| Measure | Dynamic scalar calculation |
| Calculated column | Stored row-level calculation |
| Calculated table | Derived model table |
| Row context | Current row being evaluated |
| Filter context | Restrictions on visible data |
| Context transition | Conversion of row context into filter context |
| CALCULATE | Evaluates an expression under modified filter context |
| FILTER | Returns rows satisfying a condition |
| ALL | Removes applicable filters or returns an unfiltered table expression |
| VALUES | Returns visible distinct values |
| DISTINCTCOUNT | Counts distinct visible values |
| SUMX | Evaluates an expression for each row and sums the results |

These concepts are interconnected, but they solve different modeling and evaluation problems.

## 20. Edge Cases and Validation

Analytical models must handle conditions that can produce incorrect or misleading results.

### Division by zero

A profit margin cannot be calculated when revenue is zero.

DAX:

`Profit Margin = DIVIDE([Total Profit], [Total Sales], 0)`

The programming-language implementations use a nullable result or equivalent handling.

### Empty filter context

A filter may produce no matching transactions.

Expected behavior:

- SUM returns zero for an empty input in the implemented models.
- COUNTROWS returns zero.
- DISTINCTCOUNT returns zero.
- Profit margin is undefined when revenue is zero.

### Invalid relationships

A sales transaction referring to a nonexistent product violates referential integrity.

The Python, JavaScript, C++17, and Java 17 implementations validate product references.

PostgreSQL enforces the relationship through a foreign key.

### Duplicate identifiers

Duplicate product or transaction identifiers can create ambiguous model relationships.

Primary keys and application-level validation prevent these conditions.

### Negative values

The sample model rejects negative quantities and costs. Actual business systems may require separate treatment for refunds, returns, credit notes, and adjustments.

Such events should be modeled explicitly rather than silently mixing them with ordinary sales.

### Decimal precision

Financial calculations should use appropriate decimal representations and rounding policies.

Python uses `Decimal`, Java uses `BigDecimal`, and PostgreSQL uses `NUMERIC`.

The C++17 and JavaScript educational implementations use floating-point values, which are suitable for demonstrating the evaluation logic but require decimal or scaled-integer arithmetic for financial production workloads.

## 21. Performance and Modeling Considerations

### Measures versus calculated columns

Calculated columns increase model storage because their values are stored for each row.

Measures usually provide a more efficient approach for dynamic aggregations.

Use calculated columns when the result is a genuine row-level attribute required by the model.

Use measures when a calculation should respond to report interactions.

### Star schema

A star schema generally improves analytical clarity and reduces unnecessary relationship complexity.

Dimension tables should contain descriptive attributes, while fact tables should contain business events and measurable quantities.

### Iterator functions

Functions such as SUMX evaluate expressions over table rows.

Their computational cost depends on the size of the input table and the complexity of the expression.

Prefer simple column aggregations when they provide the required result.

### Filter propagation

Incorrect relationships can produce incorrect measures even when the DAX expression is syntactically valid.

Relationship cardinality, active relationships, and filter direction should be examined before changing the measure.

### Materialized tables

Calculated tables and materialized views store derived data.

They introduce refresh and storage considerations.

A materialized view must be refreshed when its source data changes. A DAX calculated table is processed according to the tabular model's refresh lifecycle.

### Query optimization

The PostgreSQL implementation uses indexes on transaction dates, product identifiers, and category relationships.

Actual index effectiveness should be measured with query plans rather than assumed.

## 22. Limitations of the Implementations

These files demonstrate selected DAX concepts. They do not implement the complete DAX language or reproduce every Power BI engine behavior.

The following advanced features are outside the scope of the simulation:

- Complete DAX parser and expression grammar.
- Full context transition and expanded-table semantics.
- Complex relationship propagation.
- Bidirectional and inactive relationships.
- Calculation groups.
- Time-intelligence functions.
- Row-level security evaluation.
- Virtual relationships.
- Composite models.
- DirectQuery execution.
- VertiPaq storage and query optimization.
- Complete blank-value semantics.
- DAX query language and query-plan execution.
- Engine-specific dependency and refresh behavior.

The implementations use simplified filter maps and explicit relationship lookups to demonstrate core concepts. Real DAX behavior depends on the tabular model engine and its complete evaluation rules.

## 23. Execution and Verification

| File | Runtime | Execution |
|---|---|---|
| Python | Python 3.10+ | `python dax_fundamentals.py` |
| JavaScript | Node.js 18+ | `node dax_fundamentals.js` |
| C++17 | C++17 compiler | `g++ -std=c++17 -O2 dax_fundamentals.cpp -o dax_fundamentals` |
| Java | Java 17 | `javac DAXFundamentals.java` followed by `java DAXFundamentals` |
| PostgreSQL | PostgreSQL 14+ | Execute `dax_fundamentals.sql` using `psql` |

The programming-language files contain assertions or explicit validation checks for the sample calculations.

The SQL file verifies its final aggregate values after the additional transaction is inserted.

Successful execution should produce category-level reports and a final validation message from each implementation.
