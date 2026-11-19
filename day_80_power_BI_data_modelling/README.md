# Power BI Data Modeling: Fact Tables, Dimension Tables, Star Schema, Relationships and Cardinality

## 1. Domain Overview

Power BI data modeling is the process of organizing data into a semantic structure that supports reliable filtering, aggregation, calculation and reporting.

A well-designed model separates measurable business events from the descriptive information used to analyze those events.

The central design pattern implemented in these five programs is the **star schema**.

The example uses a retail sales business with the following entities:

- Products
- Customers
- Calendar dates
- Stores
- Sales transactions

The model supports questions such as:

- What is the total sales revenue?
- Which product category generates the highest revenue?
- Which customer region contributes the most sales?
- How many units were sold?
- What is the average order value?
- How does sales performance change over time?

The implementations use the same business domain but demonstrate different engineering approaches: Python provides a modeling simulator, JavaScript implements an event-driven semantic model, C++ implements an indexed analytical engine, Java provides enterprise governance, and PostgreSQL establishes relational integrity.

## 2. Fact Tables

A fact table stores measurable business events.

In the retail model, `FactSales` represents individual sales order lines.

Its grain is:

**One row represents one product line within one customer order.**

This definition is essential because every measure and relationship depends on the level of detail represented by a row.

### Fact table structure

| Column | Purpose | Classification |
|---|---|---|
| sales_key / sales_id | Unique transaction-line identifier | Primary key |
| order_id | Business order identifier | Degenerate dimension attribute |
| order_line_number | Position within an order | Transaction identifier |
| order_date_key | Order date reference | Foreign key |
| ship_date_key | Shipping date reference | Foreign key |
| product_key | Product reference | Foreign key |
| customer_key | Customer reference | Foreign key |
| store_key | Store reference | Foreign key |
| quantity | Number of units sold | Measure |
| unit_price | Selling price per unit | Measure |
| discount_amount | Transaction discount | Measure |
| sales_amount | Net sales value | Measure |
| cost_amount | Product cost | Measure |

### Transaction grain

Grain defines what one record represents.

For example, an order containing three products produces three fact-table records.

| Order ID | Product | Quantity | Sales |
|---|---|---:|---:|
| ORD001 | Laptop Pro | 1 | 75,000 |
| ORD001 | Wireless Mouse | 2 | 2,400 |
| ORD002 | Mechanical Keyboard | 1 | 3,500 |

The order total for ORD001 is 77,400.

The order identifier appears more than once because the fact table records individual order lines rather than complete orders.

A different grain, such as one row per order, would require a different fact-table design.

### Additive, semi-additive and non-additive measures

Measures must be selected according to their aggregation behavior.

| Measure | Classification | Explanation |
|---|---|---|
| Sales amount | Additive | Can be summed across products, customers and dates |
| Quantity | Additive | Can be summed across transaction lines |
| Cost amount | Additive | Can be summed across transaction lines |
| Inventory balance | Semi-additive | Can be summed across products but usually not across time |
| Average order value | Non-additive | Must be calculated from order-level totals |
| Profit margin | Non-additive | Must be recalculated from aggregated profit and revenue |

Average order value is:

`Average Order Value = Total Sales / Distinct Orders`

It must not be calculated by averaging individual order-line values.

The implementations explicitly aggregate sales by order before calculating the average.

## 3. Dimension Tables

Dimension tables contain descriptive attributes that provide analytical context to fact-table measures.

The retail model contains four primary dimensions.

### 3.1 DimProduct

Stores product-related descriptive information.

| Column | Purpose |
|---|---|
| product_key | Surrogate primary key |
| product_code | Business identifier |
| product_name | Product description |
| category | Product category |
| subcategory | More detailed classification |
| brand | Manufacturer or brand |
| unit_cost | Reference product cost |
| is_active | Product availability status |

Example hierarchy:

`Electronics → Computers → Laptop Pro`

This hierarchy supports category, subcategory and individual product analysis.

### 3.2 DimCustomer

Stores customer characteristics.

| Column | Purpose |
|---|---|
| customer_key | Surrogate primary key |
| customer_code | Business identifier |
| customer_name | Customer description |
| region | Geographic classification |
| city | Customer location |
| customer_segment | Customer grouping |
| registration_date | Customer registration date |
| is_active | Current customer status |

Customer attributes support geographic and segment-based reporting.

### 3.3 DimDate

Provides standardized calendar attributes.

| Column | Purpose |
|---|---|
| date_key | Integer surrogate key |
| full_date | Actual calendar date |
| calendar_year | Year |
| calendar_month | Month number |
| calendar_quarter | Financial or calendar quarter |
| month_name | Month description |
| day_of_week | Weekday classification |
| is_weekend | Weekend indicator |

A date dimension avoids repeatedly extracting calendar attributes from transaction timestamps.

A complete production date dimension should contain every required date in the reporting period, including dates without sales.

In Power BI, the date table should be marked as the model's date table when appropriate.

### 3.4 DimStore

Stores business-location attributes.

| Column | Purpose |
|---|---|
| store_key | Surrogate primary key |
| store_code | Business identifier |
| store_name | Store description |
| city | Location |
| region | Geographic classification |
| store_type | Store classification |
| is_active | Operational status |

Store dimensions support comparisons between locations and operational units.

## 4. Star Schema

A star schema places a central fact table at the center of a model and connects it to descriptive dimension tables.

<escape>
                         DimDate
                            |
                            |
DimProduct -------- FactSales -------- DimCustomer
                            |
                            |
                         DimStore
</escape>

The central fact table contains foreign keys referencing dimension tables.

Dimensions provide descriptive context, while the fact table supplies measurable events.

### Relationship overview

| Fact table | Dimension table | Fact-side key | Dimension-side key |
|---|---|---|---|
| FactSales | DimDate | order_date_key | date_key |
| FactSales | DimProduct | product_key | product_key |
| FactSales | DimCustomer | customer_key | customer_key |
| FactSales | DimStore | store_key | store_key |

The usual relationship is one-to-many when viewed from the dimension toward the fact table.

In Power BI's relationship dialog, this appears as:

- One side: Dimension
- Many side: Fact

In the source implementations, the same relationship is represented as `MANY_TO_ONE` when described from the fact table toward its dimension.

This difference in naming reflects the direction from which cardinality is expressed, not a different relationship.

### Advantages

- Simple analytical structure.
- Efficient dimension-based filtering.
- Clear separation of descriptive and measurable information.
- Reduced complexity in analytical queries.
- Easier implementation of measures.
- More predictable filter propagation.

### Star schema versus snowflake schema

A snowflake schema normalizes dimension attributes into additional related tables.

For example:

`DimProduct → DimSubcategory → DimCategory`

The star schema stores category and subcategory attributes directly in `DimProduct`.

| Characteristic | Star schema | Snowflake schema |
|---|---|---|
| Dimension structure | More denormalized | More normalized |
| Number of joins | Usually fewer | Usually more |
| Analytical simplicity | High | More complex |
| Attribute duplication | Potentially higher | Lower |
| Typical Power BI usability | Often preferred | Useful in selected cases |

The star schema is generally a strong starting point for Power BI analytical models.

## 5. Primary Keys, Foreign Keys and Surrogate Keys

### Primary keys

A primary key uniquely identifies a record in a table.

Examples:

- `product_key` in DimProduct
- `customer_key` in DimCustomer
- `sales_key` in FactSales

A primary key cannot contain NULL values or duplicate values.

### Foreign keys

A foreign key references a key in another table.

For example:

`FactSales.product_key → DimProduct.product_key`

The referenced dimension key must exist for every valid fact record.

A fact record referencing a nonexistent product is an orphan record.

The PostgreSQL implementation prevents this through foreign-key constraints.

The Python, JavaScript, C++ and Java implementations explicitly validate foreign-key membership.

### Surrogate keys

A surrogate key is an artificial identifier assigned to a dimension record.

For example:

| product_key | product_code | product_name |
|---:|---|---|
| 101 | PRD001 | Laptop Pro |
| 102 | PRD002 | Wireless Mouse |
| 103 | PRD003 | Mechanical Keyboard |

The surrogate key is independent of the business identifier.

Surrogate keys are useful when:

- Business identifiers change.
- Source systems use different identification formats.
- Historical dimension versions must be preserved.
- Multiple source systems contribute records.
- Dimension attributes require historical tracking.

The SQL implementation uses identity-generated keys for product, customer and store dimensions, while its example data explicitly assigns known keys for reproducibility.

## 6. Relationships and Cardinality

A relationship connects tables through corresponding columns.

Cardinality defines the number of records that can participate on each side.

### 6.1 One-to-one

One record in the first table corresponds to one record in the second table.

Example:

`Employee ↔ EmployeeSecurityProfile`

Both relationship columns must contain unique values.

One-to-one relationships should be used only when the business model requires them.

### 6.2 One-to-many

One record in a dimension can correspond to multiple records in a fact table.

Example:

`DimProduct (1) → FactSales (*)`

A product can appear in multiple sales transactions.

The product key must be unique in the dimension but may repeat in the fact table.

This is the normal relationship pattern in a star schema.

### 6.3 Many-to-one

This expresses the same one-to-many relationship from the opposite perspective.

Example:

`FactSales (*) → DimProduct (1)`

The fact table contains multiple product references, while the dimension contains one record for each product key.

The Python, JavaScript, C++ and Java relationship metadata use this representation.

### 6.4 Many-to-many

Multiple records on both sides can correspond to one another.

Example:

`Students ↔ Courses`

A student can attend multiple courses, and a course can have multiple students.

Many-to-many relationships can create ambiguous filter paths and unexpected aggregation results.

A bridge table is often preferable.

For example:

`DimStudent → BridgeEnrollment → DimCourse`

In analytical models, many-to-many relationships require deliberate design rather than automatic acceptance.

### Cardinality comparison

| Cardinality | Uniqueness requirement | Typical application |
|---|---|---|
| One-to-one | Unique on both sides | One-to-one entity association |
| One-to-many | Unique on one side | Dimension to fact |
| Many-to-one | Unique on referenced dimension side | Fact to dimension |
| Many-to-many | Neither side necessarily unique | Bridge-table or specialized relationship |

## 7. Filter Direction and Relationship Propagation

A relationship does more than connect two tables. It determines how filters propagate through the semantic model.

### Single-direction filtering

In a conventional star schema:

`DimProduct → FactSales`

Selecting the Accessories category filters the product dimension and then restricts the fact records to the corresponding products.

The resulting fact records contribute to the sales measure.

Single-direction filtering is generally the preferred starting point.

It provides predictable filter propagation and reduces ambiguity.

### Bidirectional filtering

Bidirectional filtering permits filters to propagate in both directions.

It can be useful for selected analytical scenarios, but it introduces additional risks:

- Multiple competing filter paths.
- Ambiguous calculations.
- Unexpected filter interactions.
- More complicated troubleshooting.
- Potential performance overhead.

The Java enterprise implementation explicitly flags bidirectional relationships for review.

The JavaScript model implements dimension-to-fact propagation as its primary operation.

The C++ implementation uses dimension indexes to identify matching fact records.

The Python implementation uses dimension lookup dictionaries to perform aggregations.

## 8. Role-Playing Dimensions

A role-playing dimension is one physical dimension used for multiple business purposes.

The date dimension is a common example.

A sales fact can contain:

- Order date.
- Shipping date.
- Delivery date.
- Invoice date.

All four attributes can refer to the same date dimension.

For example:

`FactSales.order_date_key → DimDate.date_key`

`FactSales.ship_date_key → DimDate.date_key`

In Power BI, multiple relationships can exist between the same tables, but only one relationship between a given pair of tables is normally active at a time.

An inactive relationship can be activated in a measure using `USERELATIONSHIP`.

Conceptual DAX example:

`Sales by Ship Date = CALCULATE([Total Sales], USERELATIONSHIP(FactSales[ship_date_key], DimDate[date_key]))`

The PostgreSQL implementation demonstrates this distinction through separate order-date and shipping-date reporting views.

An alternative is to create separate role-playing dimension tables such as `DimOrderDate` and `DimShipDate`.

This can simplify reporting when users frequently analyze multiple date roles simultaneously.

## 9. Relationship Integrity and Model Validation

A valid semantic model requires more than the presence of relationships.

It requires structural and data-quality validation.

### Key validation

Dimension primary keys must be unique.

The following conditions should be checked:

- Duplicate dimension keys.
- Missing dimension keys.
- Invalid foreign keys.
- NULL relationship keys.
- Incompatible relationship-column data types.

### Cardinality validation

For a fact-to-dimension many-to-one relationship:

- The fact-side key may repeat.
- The dimension-side key must be unique.

For a one-to-one relationship, both sides must be unique.

For a many-to-many relationship, the model should be evaluated for the need for a bridge table.

### Referential integrity

Every valid fact foreign key should reference an existing dimension key.

For example:

`FactSales.product_key = 999`

is invalid when product key 999 does not exist in DimProduct.

The SQL database rejects this record through its foreign-key constraint.

The other implementations reject it through explicit application-level validation.

### Data-quality considerations

| Validation | Failure | Consequence |
|---|---|---|
| Unique dimension keys | Duplicate product key | Ambiguous relationship |
| Foreign-key integrity | Missing product | Unmatched transaction |
| Correct grain | Duplicate order lines | Inflated measures |
| Data types | Integer-to-text mismatch | Relationship incompatibility |
| Valid quantity | Zero or negative quantity | Invalid sales record |
| Correct measure calculation | Incorrect sales amount | Financial reporting error |
| Cardinality | Duplicate dimension-side key | Incorrect relationship behavior |

## 10. Python Implementation

**File:** `power_bi_data_modeling.py`

The Python implementation is a self-contained data-modeling simulator.

### Main components

| Component | Responsibility |
|---|---|
| `Table` | Stores columns, metadata and records |
| `Column` | Defines column type and key status |
| `Relationship` | Describes table relationships |
| `DataModel` | Manages tables and validates relationships |
| `AnalyticalEngine` | Performs dimensional aggregation |
| `TableType` | Distinguishes facts from dimensions |
| `Cardinality` | Represents relationship cardinality |
| `FilterDirection` | Represents filter direction |

### Implemented workflows

1. Create dimension tables.
2. Define the sales fact table.
3. Load sample records.
4. Register relationships.
5. Validate primary keys.
6. Check relationship cardinality.
7. Detect orphan foreign keys.
8. Calculate sales by category.
9. Calculate sales by region.
10. Calculate sales by year.
11. Calculate average order value.
12. Demonstrate invalid record handling.

The implementation uses dictionaries for table storage and lookup operations.

This makes dimension lookups efficient and avoids repeated linear searches during analytical aggregation.

### Execution

Run:

`python power_bi_data_modeling.py`

The program uses only the Python standard library.

## 11. JavaScript Implementation

**File:** `power_bi_data_modeling.js`

The JavaScript implementation uses an event-driven semantic-model architecture.

### Main components

| Component | Responsibility |
|---|---|
| `DataTable` | Maintains records and primary-key indexes |
| `Relationship` | Defines relationship metadata |
| `SemanticModel` | Manages tables, relationships and model state |
| `EventEmitter` | Publishes model lifecycle events |
| `ModelError` | Handles validation failures |

### Event-driven operations

The model emits events when:

- A table is registered.
- A relationship is registered.
- Validation completes.
- A refresh starts.
- A refresh succeeds.
- A refresh fails.

This design separates data-model operations from monitoring and operational behavior.

### Asynchronous refresh

The refresh workflow follows:

`READY → REFRESHING → READY`

A failed operation produces:

`READY → REFRESHING → FAILED`

A failed refresh does not increment the successful model version.

The implementation also prevents overlapping refresh operations.

### Analytical operations

The JavaScript implementation includes:

- Product filtering.
- Dimension-to-fact filter propagation.
- Sales aggregation by product.
- Sales aggregation by customer.
- Relationship validation.
- Refresh monitoring.

`Map` provides indexed dimension storage, while `Set` supports membership checks during filter propagation.

### Execution

Run:

`node power_bi_data_modeling.js`

No npm packages are required.

## 12. C++17 Implementation

**File:** `power_bi_data_modeling.cpp`

The C++ implementation focuses on a compact analytical engine with explicit domain structures and indexed dimension lookups.

### Main structures

| Structure | Purpose |
|---|---|
| `Product` | Product dimension record |
| `Customer` | Customer dimension record |
| `CalendarDate` | Date dimension record |
| `Store` | Store dimension record |
| `SalesFact` | Sales transaction |
| `Relationship` | Relationship metadata |

### RetailDataModel

The `RetailDataModel` class manages the model's records and integrity rules.

It maintains:

- Product-key index.
- Customer-key index.
- Date-key index.
- Store-key index.
- Sales primary-key set.
- Relationship metadata.

The indexes use `unordered_map` and `unordered_set`.

This provides average constant-time key lookups, assuming a suitable hash distribution.

### Implemented analytical operations

- Total sales.
- Total quantity.
- Average order value.
- Sales by category.
- Sales by customer region.
- Sales by year.
- Category-based fact filtering.
- Region-based fact filtering.

The program also rejects duplicate dimension keys, duplicate sales identifiers and orphan foreign keys.

### Execution

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic power_bi_data_modeling.cpp -o power_bi_data_modeling`

Run:

`./power_bi_data_modeling`

On Windows:

`power_bi_data_modeling.exe`

No external libraries are required.

## 13. Java 17 Implementation

**File:** `PowerBIDataModel.java`

The Java implementation introduces enterprise-oriented model governance.

It separates data structures, validation policies, publication state and analytical operations.

### Enterprise domain types

| Component | Responsibility |
|---|---|
| `Product` | Immutable product record |
| `Customer` | Immutable customer record |
| `CalendarDate` | Validated calendar record |
| `Store` | Store dimension record |
| `SalesFact` | Validated transaction record |
| `Relationship` | Relationship definition |
| `RetailRepository` | Model data and indexes |
| `ModelPolicy` | Validation-policy interface |
| `StarSchemaPolicy` | Star-schema governance |
| `ModelGovernanceService` | Validation and publication |
| `AnalyticsService` | Analytical calculations |

### Records and immutability

Java 17 records provide compact immutable domain objects.

The constructors enforce:

- Valid identifiers.
- Non-null attributes.
- Valid quantities.
- Non-negative monetary values.
- Correct sales calculations.
- Consistent date attributes.

### Model governance

The publication service follows:

`DRAFT → VALIDATED → PUBLISHED`

When validation fails:

`DRAFT → FAILED`

The service evaluates repository integrity and registered model policies before publication.

A model cannot be published if the policy evaluation identifies structural issues.

### Performance

The repository uses `HashMap` indexes for dimension lookups and `HashSet` for identifier uniqueness.

Analytical aggregation uses Java collections and streams where appropriate.

### Execution

Compile:

`javac --release 17 PowerBIDataModel.java`

Run:

`java PowerBIDataModel`

No third-party dependencies are required.

## 14. PostgreSQL Implementation

**File:** `power_bi_data_modeling.sql`

The PostgreSQL implementation establishes the relational structure of the retail model.

It is the database-integrity counterpart to the application-level models.

### Database objects

| Object | Purpose |
|---|---|
| `retail_model` | Database schema |
| `dim_date` | Calendar dimension |
| `dim_product` | Product dimension |
| `dim_customer` | Customer dimension |
| `dim_store` | Store dimension |
| `fact_sales` | Sales fact table |
| `model_table_metadata` | Table-level metadata |
| `model_relationships` | Relationship metadata |
| `model_publication` | Model publication records |

### Constraints

The SQL uses:

- Primary-key constraints.
- Foreign-key constraints.
- Unique constraints.
- Check constraints.
- Identity-generated identifiers.
- Transactional operations.

The fact table enforces its sales calculation:

`Sales Amount = Quantity × Unit Price − Discount`

This prevents inconsistent transaction amounts from entering the database.

### Relationship validation

The `validate_model_relationships()` function evaluates registered relationships.

It checks:

- Dimension-side uniqueness.
- Source-side uniqueness when required.
- Orphan foreign keys.
- Many-to-many relationship warnings.

### Publication workflow

The `publish_model()` function creates a model publication record, evaluates relationship validation and publishes a version only when the checks pass.

Publication failures are recorded with their validation-error count.

### Analytical views

| View | Purpose |
|---|---|
| `vw_sales_enriched` | Joins fact and dimension attributes |
| `vw_sales_by_product` | Product-level analysis |
| `vw_sales_by_region` | Customer-region analysis |
| `vw_sales_by_month` | Calendar-based analysis |
| `vw_sales_by_ship_date` | Shipping-date analysis |
| `vw_model_table_inventory` | Table metadata and row counts |
| `vw_relationship_inventory` | Relationship configuration |
| `vw_model_quality` | Model-quality indicators |

### Indexing

Indexes are created on frequently used fact foreign keys.

These support common analytical joins and filtering operations.

The dimension tables also have indexes on commonly filtered descriptive attributes.

Index selection in production should be based on actual query plans, data distribution and workload.

### Execution

Run the script using:

`psql -U postgres -d your_database -f power_bi_data_modeling.sql`

The executing database user must have schema and object creation privileges.

The script uses a transaction so that the schema and initial model setup are applied atomically.

## 15. Power BI Relationship Design

The implemented model corresponds to the following logical configuration in Power BI.

| From table | To table | Cardinality | Default direction |
|---|---|---|---|
| DimProduct | FactSales | One-to-many | Single |
| DimCustomer | FactSales | One-to-many | Single |
| DimDate | FactSales | One-to-many | Single |
| DimStore | FactSales | One-to-many | Single |

The source implementations express these relationships from the fact side as many-to-one.

The Power BI model should normally use the dimension table as the one side and the fact table as the many side.

### Relationship configuration checks

When configuring a relationship, verify:

- Both columns have compatible data types.
- The dimension-side key is unique.
- The fact-side key can repeat.
- The relationship is active when required.
- The cross-filter direction is intentional.
- No unnecessary ambiguous paths exist.
- Unmatched foreign keys have been addressed.

A relationship that exists technically is not necessarily a correct business relationship.

## 16. Power BI Measures

The following measures correspond to the business calculations implemented in the source files.

### Total Sales

`Total Sales = SUM(FactSales[sales_amount])`

Calculates total revenue.

### Total Quantity

`Total Quantity = SUM(FactSales[quantity])`

Calculates the number of units sold.

### Total Cost

`Total Cost = SUM(FactSales[cost_amount])`

Calculates total product cost.

### Gross Profit

`Gross Profit = [Total Sales] - [Total Cost]`

Calculates the difference between sales and costs.

### Profit Margin

`Profit Margin = DIVIDE([Gross Profit], [Total Sales], 0)`

Calculates the gross-profit percentage.

### Distinct Orders

`Distinct Orders = DISTINCTCOUNT(FactSales[order_id])`

Counts unique orders rather than transaction lines.

### Average Order Value

`Average Order Value = DIVIDE([Total Sales], [Distinct Orders], 0)`

Calculates the average sales value per order.

These are measures, not calculated columns. Their values are evaluated in the current filter context.

## 17. Performance and Storage Considerations

Power BI performance depends on the data model, source structure, storage mode, query design and report interactions.

### Model design

- Keep fact tables at a clearly defined grain.
- Avoid unnecessary columns in fact tables.
- Use integer surrogate keys for dimension relationships where appropriate.
- Avoid unnecessary many-to-many relationships.
- Prefer predictable single-direction filtering.
- Use dimensions for descriptive attributes.
- Avoid storing repeated descriptive text in large fact tables.

### VertiPaq storage

Power BI Import mode uses the VertiPaq columnar storage engine.

Columnar storage compresses data by storing and processing columns efficiently.

Compression generally benefits from:

- Repeated values.
- Appropriate data types.
- Reduced cardinality.
- Removal of unused columns.
- Integer relationship keys.
- Well-designed dimensions.

High-cardinality columns such as unique transaction identifiers can consume significant memory.

### Relationship performance

Relationships are fundamental to filter propagation.

Poorly designed relationships can cause:

- Ambiguous calculations.
- Incorrect aggregation.
- Increased model complexity.
- Unnecessary filtering work.

The model should be designed around business relationships rather than simply connecting every available table.

### Import, DirectQuery and composite models

| Mode | Storage behavior | Main consideration |
|---|---|---|
| Import | Data is loaded into the semantic model | Fast interactive analysis with refresh requirements |
| DirectQuery | Queries are sent to the underlying source | Source-system performance and query limitations |
| Composite | Combines storage modes | More flexible but requires additional modeling decisions |

The five implementations demonstrate logical and relational modeling. They do not implement Power BI's VertiPaq storage engine or execute Power BI semantic-model refreshes.

## 18. Slowly Changing Dimensions

Dimension attributes can change over time.

For example, a customer may move from the North region to the South region.

A model must decide whether historical transactions should be analyzed using the customer's current region or the region applicable when the transaction occurred.

### Type 1

The existing dimension record is overwritten.

- No historical attribute version is retained.
- Historical reporting reflects the current value.

### Type 2

A new dimension record is created for each tracked historical change.

Typical columns include:

| Column | Purpose |
|---|---|
| customer_key | Surrogate version key |
| customer_code | Stable business identifier |
| region | Historical region |
| effective_from | Version start date |
| effective_to | Version end date |
| is_current | Current-version indicator |

For Type 2, the fact table must reference the correct historical surrogate key at load time.

This preserves historical customer attributes.

The supplied implementations use static dimension examples and do not implement a complete Type 2 loading process.

## 19. Bridge Tables and Complex Relationships

Some business relationships are inherently many-to-many.

For example, one customer can belong to several loyalty programs, while each program can contain several customers.

A bridge table represents the associations explicitly.

Example:

| customer_key | program_key |
|---:|---:|
| 201 | 501 |
| 201 | 502 |
| 202 | 501 |

The structure becomes:

`DimCustomer → BridgeCustomerProgram ← DimProgram`

This makes the many-to-many business relationship explicit.

Bridge-table design must consider:

- Duplicate association records.
- Filter propagation.
- Double counting.
- Allocation weights where measures must be distributed.
- Ambiguous analytical paths.

A many-to-many relationship should not be introduced simply to resolve an incorrectly designed dimension.

## 20. Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Table modeling | Yes | Yes | Struct-based | Record-based | Relational |
| Fact and dimensions | Yes | Yes | Yes | Yes | Yes |
| Relationship metadata | Yes | Yes | Yes | Yes | Yes |
| Cardinality validation | Yes | Yes | Partial metadata validation | Yes | Yes |
| Referential integrity | Application validation | Application validation | Indexed validation | Repository validation | Foreign keys |
| Filter propagation | Lookup-based aggregation | Explicit filter engine | Indexed filtering | Stream-based filtering | SQL joins |
| Aggregation | Yes | Yes | Yes | Yes | Views and queries |
| Refresh lifecycle | Static simulation | Asynchronous events | Static execution | Publication lifecycle | Transactional publication |
| Model diagnostics | Yes | Yes | Yes | Yes | Yes |

Each implementation addresses a different engineering concern.

Python emphasizes transparent modeling and experimentation.

JavaScript emphasizes event-driven behavior and asynchronous refresh management.

C++ emphasizes indexed lookups and efficient data processing.

Java emphasizes immutable domain objects, reusable policy interfaces and model publication governance.

PostgreSQL emphasizes durable relational integrity, metadata and transactional data operations.

## 21. Limitations and Practical Considerations

The implementations intentionally use a small, static retail dataset.

They demonstrate modeling principles rather than reproduce the complete internal behavior of Power BI.

Important limitations include:

- The examples do not connect to an actual Power BI workspace.
- They do not create a Power BI `.pbix` file.
- They do not implement VertiPaq compression.
- They do not execute DAX through a Power BI engine.
- They do not implement incremental refresh.
- They do not implement complete Slowly Changing Dimension Type 2 processing.
- They do not implement row-level security.
- They do not model every Power BI relationship configuration.
- The SQL relationship metadata function validates the registered sample relationships rather than dynamically discovering every database constraint.
- The JavaScript, Python, C++ and Java implementations are application-level simulations of semantic-model behavior.

For a production analytical warehouse, additional controls would normally include source-system reconciliation, incremental loading, historical dimension management, audit logging, access control, refresh monitoring and automated data-quality testing.

The fundamental design remains consistent:

**Fact tables record business events. Dimension tables describe those events. Relationships connect them. Cardinality defines the association. Filter propagation determines how analytical selections affect measures.**
