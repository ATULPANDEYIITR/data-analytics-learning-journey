# Power BI Performance Engineering

## 1. Technical Scope

Power BI performance engineering concerns the efficiency of the complete analytical execution path, from source-system access to semantic model evaluation and visual rendering.

A report can be slow for several different reasons:

- An unnecessarily large semantic model increases memory consumption.
- Poor relationship design increases filter-propagation complexity.
- High-cardinality columns increase storage requirements.
- Inefficient DAX expressions create expensive Formula Engine operations.
- DirectQuery requests encounter slow source queries or network latency.
- Excessive visual complexity increases rendering work.
- Refresh operations consume processing capacity.
- Poorly designed aggregations fail to reduce detail-level query workloads.

Performance optimization must identify the actual bottleneck before changing the model.

The implementations in this project establish a common performance-analysis domain while using different engineering approaches in Python, JavaScript, C++17, Java 17, and PostgreSQL.

## 2. Power BI Semantic Model Architecture

A semantic model provides the analytical structure through which reports access business data.

It contains tables, columns, relationships, measures, hierarchies, metadata, and storage configurations.

A typical enterprise sales model follows a star schema.

    Date -----------+
                    |
    Product --------+---- Sales
                    |
    Customer -------+

The central fact table stores business events and numerical measurements. Dimension tables provide descriptive attributes used for filtering, grouping, and reporting.

| Component | Responsibility | Performance consideration |
|---|---|---|
| Fact table | Stores transactions and measurements | Row count, compression, grain |
| Dimension table | Provides descriptive attributes | Cardinality and relationship design |
| Relationship | Propagates filters | Direction, cardinality, ambiguity |
| Measure | Defines analytical calculations | DAX execution cost |
| Aggregation | Stores summarized values | Grain and query coverage |
| Hierarchy | Defines navigation levels | Useful organization and usability |

### 2.1 Fact Tables

Fact tables commonly contain foreign keys, numerical measurements, and transaction identifiers.

Examples include:

- Sales amount
- Quantity
- Product key
- Customer key
- Date key
- Transaction identifier

A fact table containing millions of rows should be designed with particular attention to column selection, data types, compression, and refresh behavior.

The Python, JavaScript, C++, and Java implementations use a two-million-row sales table to demonstrate model analysis.

### 2.2 Dimension Tables

Dimension tables describe the entities represented by fact records.

Examples include:

- Product
- Customer
- Date
- Geography
- Department

A well-designed dimension generally provides a unique key and descriptive attributes.

Surrogate integer keys are frequently preferable to long descriptive text values for relationships because they reduce key width and improve model consistency.

### 2.3 Relationship Design

Relationships define how filters propagate between tables.

The sample implementations use many-to-one relationships from the Sales fact table to Product and Date dimensions.

Important relationship characteristics include:

- Cardinality
- Active or inactive status
- Filter direction
- Unique dimension keys
- Referential integrity
- Many-to-many behavior

Bidirectional filtering should be introduced only when required by the analytical design. It can create ambiguous filter paths and more complicated evaluation behavior.

Many-to-many relationships should be evaluated carefully. Bridge tables can make the relationship structure and business rules more explicit.

## 3. VertiPaq and Model Optimization

VertiPaq is the in-memory analytical storage engine used by Power BI Import models.

It uses column-oriented storage, dictionary encoding, value encoding, compression, and optimized analytical operations.

The physical storage size is influenced by several characteristics.

### 3.1 Cardinality

Cardinality represents the number of distinct values in a column.

For example:

| Column | Example cardinality | Interpretation |
|---|---:|---|
| Country | 10 | Low |
| Product category | 12 | Low |
| Customer key | 180,000 | High |
| Transaction reference | 1,900,000 | Very high |

High cardinality can increase dictionary size and reduce compression efficiency.

A transaction identifier may have nearly one distinct value per row. Such a column can be expensive to retain when it is not needed for reporting.

The implementations detect high-cardinality string columns and produce recommendations.

Cardinality is not, by itself, a reason to delete a column. A transaction identifier required for drill-through, auditing, or reconciliation may be essential.

### 3.2 Dictionary Encoding

Dictionary encoding replaces repeated values with compact integer identifiers.

Conceptually:

| Original value | Encoded value |
|---|---:|
| North | 1 |
| South | 2 |
| East | 3 |
| West | 4 |

A column with few distinct values can benefit substantially from dictionary encoding.

High-cardinality strings require larger dictionaries and may consume considerable memory.

### 3.3 Data Types

Data types influence storage efficiency and calculation behavior.

Common optimization decisions include:

- Use integers for appropriate numeric identifiers.
- Use fixed or appropriate numeric precision for measurements.
- Use Date rather than unnecessarily detailed datetime values when time-of-day information is not needed.
- Remove unnecessary text columns.
- Avoid unnecessarily precise numeric representations.
- Reduce source data precision only when business requirements permit.

The sample implementations calculate approximate encoded and dictionary storage requirements.

These estimates are educational approximations. They are not measurements of actual VertiPaq memory consumption.

### 3.4 Remove Unnecessary Columns

The most direct model-size optimization is frequently removing columns that are not required.

Unused columns can increase:

- Model memory.
- Refresh processing.
- Metadata complexity.
- Deployment size.
- Model maintenance effort.

The sample Sales table contains an unused description field. Each implementation identifies it.

The preferred approach is to remove unnecessary columns as early as possible, including from source queries where appropriate.

### 3.5 Star Schema Optimization

A star schema separates transactional measurements from descriptive attributes.

It generally simplifies:

- Filter propagation.
- Relationship design.
- DAX expressions.
- Measure development.
- Report navigation.

Denormalization is not automatically harmful, and normalization is not automatically optimal. The appropriate design depends on source architecture, semantic model behavior, and business requirements.

## 4. DAX Optimization

Data Analysis Expressions (DAX) is the calculation language used in Power BI semantic models.

DAX performance depends on expression structure, evaluation context, storage-engine capabilities, cardinality, and the amount of intermediate data processed.

### 4.1 Storage Engine and Formula Engine

Power BI analytical calculations involve two important execution components.

| Component | Responsibility | Performance characteristics |
|---|---|---|
| Storage Engine | Retrieves and aggregates model data | Efficient columnar scans and supported aggregations |
| Formula Engine | Evaluates DAX expressions and coordinates calculations | Can become expensive with complex iterators and intermediate tables |

The Storage Engine performs supported data retrieval and aggregation operations.

The Formula Engine evaluates calculation logic, manages evaluation contexts, and coordinates Storage Engine requests.

A DAX expression may involve both engines.

Reducing Formula Engine work is useful when profiling identifies it as a significant bottleneck. It is not a universal objective to eliminate all Formula Engine operations.

### 4.2 Simple Aggregation

A straightforward aggregation is:

`Total Sales := SUM(Sales[SalesAmount])`

This expression allows the engine to aggregate a numeric column directly.

When an appropriate source or model column already contains the required value, this can be more efficient than recalculating the value for every row.

### 4.3 Iterator Functions

Iterator functions evaluate expressions over rows.

An example is:

`Extended Revenue := SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])`

SUMX evaluates the multiplication for each row before aggregating the results.

For a large fact table, this can increase calculation work.

When the extended revenue is a stable business attribute, calculating it upstream in the source system or Power Query may be preferable.

The resulting measure can then use:

`Extended Revenue := SUM(Sales[ExtendedAmount])`

The two approaches are equivalent only when the source calculation preserves the required precision, null handling, and business semantics.

Iterator functions remain necessary for many legitimate analytical calculations. They should not be removed without validating the intended result.

### 4.4 Variables

Variables improve DAX readability and can avoid repeated evaluation when expressions share the same evaluation context.

Example:

`Sales Growth % :=`

- `VAR CurrentSales = [Total Sales]`
- `VAR PreviousSales = CALCULATE([Total Sales], DATEADD('Date'[Date], -1, YEAR))`
- `RETURN DIVIDE(CurrentSales - PreviousSales, PreviousSales)`

Variables are evaluated in their defined context. Reusing a variable does not mean that it will automatically recalculate under a different filter context.

Their use should preserve the intended semantics.

### 4.5 Filter Context

Filter context determines which model rows participate in a calculation.

Important functions include:

| Function | Purpose |
|---|---|
| CALCULATE | Evaluates an expression in a modified filter context |
| FILTER | Produces a filtered table |
| ALL | Removes filters from a specified table or column |
| REMOVEFILTERS | Explicitly removes filters |
| KEEPFILTERS | Preserves and intersects existing filters |
| DIVIDE | Performs division with controlled zero-denominator behavior |
| SUMX | Evaluates an expression over a table |
| DATEADD | Shifts date context |

Broad filter operations should be avoided when narrower filters are sufficient.

For example, filtering an entire fact table unnecessarily may create more work than applying a suitable Boolean filter to the required column.

Optimization must preserve the original filter context and business meaning.

### 4.6 Context Transition

Context transition converts row context into filter context.

It is particularly relevant when CALCULATE is evaluated inside iterators.

Unnecessary context transitions and complex nested expressions can make DAX harder to optimize and maintain.

The sample DAX analyzers identify iterator patterns, broad filters, repeated expressions, and large estimated workloads.

They perform structural analysis rather than parsing and executing the complete DAX language.

## 5. Storage Modes

Power BI supports multiple storage modes. Their selection influences data freshness, source workload, memory requirements, and query latency.

### 5.1 Import

Import mode loads data into the semantic model.

Characteristics:

- Data is stored in the in-memory model.
- Analytical queries can benefit from VertiPaq compression.
- Queries generally avoid contacting the original data source for every interaction.
- Data freshness depends on refresh operations.
- Model memory and refresh duration must be managed.

Import is generally suitable for interactive analytical workloads when the required freshness can be achieved through scheduled or supported incremental refresh processes.

### 5.2 DirectQuery

DirectQuery retains data at the source and translates supported model queries into source queries.

Characteristics:

- Data is queried from the underlying source.
- Source-system performance directly influences report responsiveness.
- Network latency and concurrency matter.
- Query folding and supported query translation are important.
- Source indexes and query plans can influence execution.
- Complex report interactions may generate substantial source workloads.

DirectQuery is useful when source-level freshness or model-size requirements make Import unsuitable.

It is not automatically faster or more current in every practical scenario.

### 5.3 Dual

Dual mode allows a table to behave as Import or DirectQuery depending on the query context in a composite model.

It is particularly useful for dimensions shared between Import and DirectQuery fact tables.

Dual storage can reduce unnecessary source queries in appropriate composite-model scenarios.

The actual execution behavior depends on relationships, query requirements, and model configuration.

### 5.4 Direct Lake

Direct Lake provides access to supported lake-based data without requiring the conventional full Import process.

Its behavior depends on the supported Fabric architecture, source format, capacity, and model configuration.

Direct Lake should not be treated as interchangeable with conventional Import or DirectQuery.

Fallback behavior and operational limitations must be considered for the specific deployment.

### 5.5 Storage Mode Comparison

| Characteristic | Import | DirectQuery | Dual | Direct Lake |
|---|---|---|---|---|
| Main data access | In-memory model | Source queries | Context-dependent | Supported lake storage |
| Source interaction per query | Generally no | Yes | Depends on context | Architecture-dependent |
| Memory requirements | Model storage | Lower local data storage | Mixed | Architecture-dependent |
| Freshness | Refresh-dependent | Source-dependent | Mixed | Source and platform-dependent |
| Main performance concern | Memory and refresh | Source execution | Composite behavior | Capacity and compatibility |

The Python, JavaScript, and Java implementations include storage-mode assessment logic.

The C++ implementation includes storage-mode-aware memory estimation.

The SQL implementation stores storage-mode metadata and generates operational reports.

## 6. Composite Models and Aggregations

Composite models combine tables using different storage modes.

A common design uses:

- Import fact tables for frequently accessed summaries.
- DirectQuery fact tables for detailed or fresher data.
- Dual dimensions for compatible filtering across storage modes.

Aggregations allow summarized data to satisfy suitable queries without scanning the full detail-level fact table.

Example:

    Detailed Sales
         |
         v
    Monthly Aggregation
         |
         v
    Monthly Product Reporting

An aggregation table may store:

- Month.
- Product key.
- Category.
- Total sales.
- Total quantity.

For an aggregation to answer a query correctly, its grain and mappings must cover the requested dimensions, measures, and filter requirements.

A summary table cannot answer every detail-level query.

The PostgreSQL implementation maintains aggregation metadata through `aggregation_definitions`.

This table records the detail table, aggregation table, grain, and expression. It does not implement the Power BI aggregation mapping engine itself.

## 7. Power Query and Query Folding

Power Query provides data extraction and transformation capabilities.

Query folding occurs when supported transformations are translated into operations executed by the source system.

For example:

    Source Table
         |
         v
    Filter Required Dates
         |
         v
    Select Required Columns
         |
         v
    Group Required Records
         |
         v
    Load Semantic Model

When folding is supported, the source system can perform filtering and transformations before returning data.

This can reduce:

- Network transfer.
- Power BI-side transformation work.
- Refresh duration.
- Intermediate data volume.

Common folding-friendly operations include supported filters, projections, joins, and aggregations.

Some transformations prevent folding or change its behavior.

Query folding must be verified for the actual connector, source, transformation sequence, and generated source query.

A metadata flag in these implementations represents recorded folding status, not automatic verification of the actual Power Query execution plan.

## 8. Query Performance Analysis

Query performance should be analyzed by separating the stages of execution.

A useful conceptual decomposition is:

    User Interaction
          |
          v
    Visual Query Generation
          |
          v
    DAX Evaluation
          |
          +------ Storage Engine
          |
          +------ Formula Engine
          |
          +------ External Source
          |
          v
    Result Processing
          |
          v
    Visual Rendering

The measured duration may include different components depending on the diagnostic tool and measurement boundary.

Consequently, the components should not always be interpreted as strictly independent or additive measurements.

### 8.1 Storage Engine Duration

Storage Engine duration indicates the time attributed to columnar data retrieval and supported aggregation operations.

Potential causes of excessive duration include:

- Large scans.
- High-cardinality processing.
- Expensive filtering.
- Complex relationship propagation.
- Large intermediate results.

### 8.2 Formula Engine Duration

Formula Engine duration indicates the time attributed to DAX calculation and orchestration.

Potential causes include:

- Large iterators.
- Complex nested expressions.
- Repeated calculations.
- Expensive context transitions.
- Large virtual tables.
- Complex conditional calculations.

### 8.3 Source Execution Duration

Source execution is particularly important for DirectQuery and composite models.

Relevant factors include:

- Database execution plans.
- Source indexes.
- Query complexity.
- Network latency.
- Database concurrency.
- Source workload capacity.

### 8.4 Visual Rendering Duration

Visual rendering involves presenting query results in the report.

Potential optimization areas include:

- Excessive visual count.
- High-cardinality axes.
- Large numbers of displayed data points.
- Complex custom visuals.
- Unnecessary interactions.
- Excessive cross-filtering.

### 8.5 Cache Behavior

Repeated queries may benefit from caches.

A cache hit can reduce observed execution time, but warm-cache measurements should not be compared directly with cold-cache measurements.

Benchmark reports should identify:

- Cache state.
- Query type.
- Filter context.
- Data volume.
- Concurrent workload.
- Measurement boundary.
- Number of repetitions.

The implementations record cache-hit metadata and provide performance evaluation functions.

## 9. Performance Thresholds and Workload Management

A performance policy converts observations into measurable operational conditions.

The sample policy uses:

| Metric | Demonstration threshold |
|---|---:|
| Formula Engine contribution | 40% |
| Source execution | 500 ms |
| Visual rendering | 300 ms |
| Total query duration | 1,500 ms in PostgreSQL |

These are illustrative engineering thresholds, not universal Power BI service limits or recommended service-level objectives.

Actual thresholds should be defined from business requirements, report complexity, workload distribution, and available capacity.

### 9.1 Query Evaluation

The implementations calculate:

- Total measured duration.
- Formula Engine contribution.
- Source execution duration.
- Visual rendering duration.
- Rows scanned.
- Rows returned.
- Scan efficiency.
- Policy violations.

Scan efficiency is represented as:

`Rows Returned / Rows Scanned`

A low ratio can indicate that a query examines substantially more data than it returns.

It is not sufficient evidence of a performance problem by itself. Columnar storage engines can efficiently scan compressed data, and the number of rows returned does not fully describe the amount of internal processing.

### 9.2 Workload Prioritization

Concurrent analytical workloads can compete for resources.

The JavaScript implementation introduces an asynchronous scheduler with configurable concurrency.

It maintains:

- Active query count.
- Pending queue.
- Completed query count.
- Failed query count.
- Event-driven execution notifications.

The C++ and Java implementations provide priority-based workload ordering.

These are application-level workload simulations. They do not directly control Power BI capacity scheduling or Fabric workload management.

## 10. Implementation Architecture

The five source files implement the same conceptual performance domain from different engineering perspectives.

| File | Main responsibility | Distinct implementation |
|---|---|---|
| Python | Performance analysis and simulation | Dataclasses, enums, model inspection, JSON reporting |
| JavaScript | Workload monitoring | Events, asynchronous execution, Promises, concurrency |
| C++17 | Governance evaluation | Domain classes, STL, policy engine, query prioritization |
| Java 17 | Enterprise performance governance | Records, immutable collections, service classes, validation |
| PostgreSQL | Performance metadata and telemetry | Relational constraints, triggers, views, functions, procedures |

### 10.1 Python

The Python script provides a complete analytical model.

Its main components are:

- `Column`: describes column type and cardinality.
- `Table`: stores table-level metadata and estimates memory.
- `Relationship`: validates model relationships.
- `SemanticModel`: maintains model structure.
- `ModelOptimizer`: detects model design issues.
- `DAXAnalyzer`: evaluates DAX complexity metadata.
- `StorageModeAdvisor`: describes storage-mode trade-offs.
- `QueryMetrics`: validates query execution measurements.
- `QueryPerformanceAnalyzer`: identifies threshold-based bottlenecks.
- `Benchmark`: measures repeated operation durations.

The report is written to `powerbi_performance_report.json`.

Its memory calculations are simplified estimates and should not be interpreted as actual VertiPaq measurements.

### 10.2 JavaScript

The JavaScript implementation focuses on event-driven performance monitoring.

Its main components are:

- `SemanticModel`: maintains table and relationship metadata.
- `PerformancePolicy`: evaluates model and query conditions.
- `DAXCatalog`: identifies common DAX patterns.
- `QueryRequest`: represents analytical work.
- `QueryScheduler`: limits concurrent simulated execution.
- `PerformanceMonitor`: records metrics and emits events.

The scheduler uses Promises and Node.js timers to demonstrate asynchronous workload handling.

The simulated execution duration is not an actual DAX query duration.

The program generates `powerbi_performance_report.json`.

### 10.3 C++17

The C++ implementation emphasizes efficient domain modeling and deterministic evaluation.

Its components include:

- `Column`: validates column metadata.
- `Table`: stores table characteristics.
- `SemanticModel`: maintains model relationships.
- `ModelOptimizer`: evaluates model design.
- `DaxAnalyzer`: inspects DAX execution metadata.
- `QueryEvaluator`: evaluates performance thresholds.
- `WorkloadManager`: orders query tasks by priority.

The implementation uses STL containers, algorithms, validation functions, and exception handling.

Its memory estimation uses arithmetic approximations and does not model all internal VertiPaq compression mechanisms.

### 10.4 Java 17

The Java implementation uses an enterprise service-oriented design.

Its components include:

- Immutable `Column` and `Relationship` records.
- `ModelTable`: represents a semantic model table.
- `SemanticModel`: owns tables and relationships.
- `ModelGovernanceService`: detects structural issues.
- `StoragePolicyService`: evaluates storage configurations.
- `DaxAnalysisService`: inspects DAX patterns.
- `QueryEvaluationService`: enforces performance thresholds.
- `WorkloadService`: prioritizes analytical tasks.

The design separates domain objects, policy definitions, and evaluation services.

Immutable collections reduce accidental modification of model metadata.

### 10.5 PostgreSQL

The PostgreSQL implementation provides a persistent metadata and telemetry repository.

Its principal tables are:

| Table | Purpose |
|---|---|
| `semantic_models` | Semantic model ownership and metadata |
| `model_tables` | Table characteristics and storage modes |
| `model_columns` | Column types, cardinality, and usage |
| `model_relationships` | Relationship structure |
| `dax_measures` | DAX expressions and pattern metadata |
| `query_executions` | Query execution telemetry |
| `performance_policies` | Performance thresholds |
| `optimization_findings` | Detected performance issues |
| `aggregation_definitions` | Aggregation design metadata |

The database uses primary keys, foreign keys, uniqueness constraints, check constraints, indexes, and a relationship-validation trigger.

Its principal analytical objects are:

- `v_query_performance`
- `v_model_inventory`
- `v_query_aggregation`
- `v_storage_mode_report`
- `evaluate_query()`
- `scan_model()`

The SQL workflow separates persistent metadata from derived performance reports.

The database does not connect directly to Power BI or execute DAX. Execution telemetry must be supplied through an appropriate external collection process.

## 11. Performance Optimization Workflow

A practical optimization process should proceed from measurement to controlled modification.

    Establish Baseline
           |
           v
    Identify Slow Reports
           |
           v
    Inspect Query Execution
           |
           v
    Identify Main Bottleneck
           |
           +-------------------+
           |                   |
           v                   v
    Model Optimization     DAX Optimization
           |                   |
           +-------------------+
                   |
                   v
           Storage Mode Review
                   |
                   v
           Source Optimization
                   |
                   v
           Visual Optimization
                   |
                   v
           Repeat Measurements
                   |
                   v
           Validate Results

### Stage 1: Establish Baseline

Record:

- Report response time.
- Query execution time.
- Refresh duration.
- Model size.
- Source execution time.
- Concurrent user load.
- Visual rendering behavior.

### Stage 2: Identify the Bottleneck

Determine whether the primary limitation originates from:

- Model size.
- DAX execution.
- Source queries.
- Network latency.
- Capacity contention.
- Visual rendering.

### Stage 3: Optimize the Model

Review:

- Fact table grain.
- Dimension design.
- Unused columns.
- Data types.
- Cardinality.
- Relationship direction.
- Many-to-many relationships.

### Stage 4: Optimize DAX

Review:

- Iterator operations.
- Repeated calculations.
- Filter expressions.
- Context transitions.
- Virtual tables.
- Aggregation opportunities.

### Stage 5: Review Storage Architecture

Evaluate whether Import, DirectQuery, Dual, Direct Lake, or a composite model best satisfies the required freshness and workload characteristics.

### Stage 6: Validate

Repeat measurements under comparable conditions.

An optimization should be accepted only when it preserves analytical correctness and produces a measurable improvement.

## 12. Execution Instructions

### Python

Requirements: Python 3.10 or later.

Save the first source block as `powerbi_performance.py`.

Run:

`python powerbi_performance.py`

The program performs validation tests, generates an analytical report, and writes `powerbi_performance_report.json`.

### JavaScript

Requirements: Node.js 18 or later.

Save the second source block as `powerbi_performance.js`.

Run:

`node powerbi_performance.js`

The program runs asynchronous workload simulations and writes `powerbi_performance_report.json`.

### C++17

Requirements: A C++17-compatible compiler.

Save the third source block as `powerbi_performance.cpp`.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic powerbi_performance.cpp -o powerbi_performance`

Run:

`./powerbi_performance`

On Windows:

`powerbi_performance.exe`

### Java 17

Requirements: JDK 17.

Save the fourth source block as `PowerBIPerformance.java`.

Compile:

`javac PowerBIPerformance.java`

Run:

`java PowerBIPerformance`

### PostgreSQL

Requirements: PostgreSQL 14 or later.

Save the fifth source block as `powerbi_performance.sql`.

Execute:

`psql -U postgres -d your_database -v ON_ERROR_STOP=1 -f powerbi_performance.sql`

The script creates the `bi_performance` schema, its relational objects, sample metadata, performance policies, and example analytical queries.

It includes a transaction and commits the sample setup and reporting operations.

Run the script against a dedicated development database when testing because it creates database objects and sample records.

## 13. Validation and Failure Handling

All four application implementations validate important domain inputs.

Examples include:

- Empty table names.
- Duplicate columns.
- Invalid storage modes.
- Negative row counts.
- Cardinality exceeding row count.
- Missing relationship tables.
- Missing relationship columns.
- Invalid query durations.
- Negative query measurements.
- Returned rows exceeding scanned rows.
- Invalid performance thresholds.
- Duplicate workload identifiers.

The SQL implementation enforces relational integrity through constraints and a trigger.

The PostgreSQL evaluation function rejects queries that are not completed or do not have an applicable active policy.

Production systems should also account for missing telemetry, incomplete measurements, stale metadata, concurrent updates, permission failures, and differences between service-level and desktop-level execution.

## 14. Limitations and Measurement Boundaries

The implementations are educational performance-engineering systems, not complete Power BI diagnostic integrations.

| Area | Implemented capability | Boundary |
|---|---|---|
| VertiPaq | Approximate memory estimation | No physical engine inspection |
| DAX | Pattern and complexity analysis | No DAX parser or execution engine |
| Storage modes | Metadata and trade-off evaluation | No automatic model conversion |
| DirectQuery | Source latency simulation | No actual database query execution |
| Direct Lake | Storage-mode representation | No Fabric lakehouse connection |
| Query performance | Metrics and policy evaluation | Depends on supplied telemetry |
| Aggregations | Metadata representation | No automatic aggregation mapping |
| Workload | Scheduling simulation | No Power BI capacity control |
| Refresh | Metadata analysis | No actual dataset refresh |

Actual performance diagnosis requires measurements from the relevant Power BI environment.

The simulated metrics must not be confused with actual engine timings.

Performance comparisons should use equivalent report filters, data volumes, cache conditions, model versions, and concurrency levels.

## 15. Practical Engineering Distinctions

Several optimization concepts are related but solve different problems.

| Concept | Main problem addressed |
|---|---|
| Model optimization | Reduces unnecessary model complexity and storage |
| DAX optimization | Reduces calculation work |
| Storage-mode selection | Balances freshness, source workload, and memory |
| Query folding | Pushes supported transformations to the source |
| Aggregations | Avoids unnecessary detail-level processing |
| Source optimization | Improves external query execution |
| Visual optimization | Reduces presentation and interaction overhead |
| Capacity management | Controls available resources and workload contention |
| Performance monitoring | Detects regressions and verifies improvements |

The central engineering principle is to optimize the component responsible for the measured bottleneck rather than applying generic changes to every report.

A smaller semantic model does not automatically guarantee faster DirectQuery execution. A shorter DAX expression does not automatically execute faster. A higher cache-hit rate does not demonstrate better cold-cache performance.

Each change must be validated against the actual execution environment and required analytical results.
