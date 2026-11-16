# Power BI Introduction: Business Intelligence Architecture, Desktop, Service, Reports and Dashboards

## 1. Introduction to Business Intelligence

Business Intelligence (BI) refers to the technologies, processes and analytical methods used to convert organizational data into information that supports business decisions.

Organizations generate data through enterprise resource planning systems, customer relationship management platforms, transaction databases, spreadsheets, operational applications and external data providers.

Business Intelligence integrates these sources, organizes the information and presents analytical results through reports, dashboards, visualizations and performance indicators.

Power BI is Microsoft's Business Intelligence platform. It provides capabilities for data acquisition, transformation, modeling, calculation, visualization, collaboration and information distribution.

The central workflow is:

Business Data Sources
→ Data Acquisition
→ Data Transformation
→ Data Modeling
→ Analytical Calculations
→ Reports
→ Dashboards
→ Business Decisions

The five source implementations in this project simulate different technical aspects of this workflow.

## 2. Core Business Intelligence Concepts

### 2.1 Data, Information and Insights

These concepts represent different stages of analytical interpretation.

| Concept | Meaning | Business example |
|---|---|---|
| Data | Raw recorded values | Individual sales transactions |
| Information | Organized and processed data | Monthly sales totals |
| Insight | Interpretation of analytical results | Revenue increased in the North region |
| Decision | Action based on an insight | Increase inventory allocation |
| Performance monitoring | Measurement of subsequent outcomes | Track regional revenue after inventory changes |

A BI system should maintain traceability between source records, transformations, calculations and displayed results.

### 2.2 Descriptive, Diagnostic, Predictive and Prescriptive Analytics

| Analytical category | Primary question | Example |
|---|---|---|
| Descriptive | What happened? | Total quarterly revenue |
| Diagnostic | Why did it happen? | Regional contribution to a revenue decline |
| Predictive | What might happen? | Forecasting future sales |
| Prescriptive | What action should be taken? | Inventory allocation recommendations |

The implementations primarily demonstrate descriptive and diagnostic analytics. They provide a foundation for extending the system with forecasting and optimization techniques.

### 2.3 Key BI Terminology

- **Dataset:** A structured collection of data used for analysis.
- **Semantic model:** A business-oriented representation of data, relationships, calculations and metadata.
- **Measure:** A calculation evaluated within an analytical context.
- **Dimension:** A descriptive entity used to organize and filter facts.
- **Fact:** A measurable business event, such as a sales transaction.
- **KPI:** A Key Performance Indicator used to monitor a business objective.
- **Visualization:** A graphical or tabular representation of analytical information.
- **Refresh:** An operation that retrieves or processes updated source information.
- **Workspace:** A collaborative environment for organizing BI content.
- **Gateway:** A component that enables supported Power BI services to access data sources that require an intermediary connection, commonly on a private network.

## 3. Power BI Architecture

Power BI consists of connected components responsible for different stages of the analytical process.

### 3.1 Architectural Components

| Component | Responsibility |
|---|---|
| Power BI Desktop | Data acquisition, transformation, modeling and report development |
| Power Query | Data extraction, cleaning and transformation |
| Power BI semantic model | Relationships, metadata, measures and analytical logic |
| DAX | Analytical expressions and calculations |
| VertiPaq | In-memory columnar storage and compression |
| DirectQuery | Querying supported underlying data sources |
| Power BI Service | Cloud-based publishing, sharing, refresh and administration |
| Power BI Gateway | Connectivity between supported cloud services and private data sources |
| Power BI Reports | Interactive analytical pages containing visualizations |
| Power BI Dashboards | Service-based collections of tiles and monitored information |

### 3.2 High-Level Architecture

Data Sources
- PostgreSQL
- SQL Server
- Excel
- CSV
- APIs
- Cloud applications

↓

Power BI Desktop

↓

Power Query
- Extraction
- Cleaning
- Transformation
- Type conversion
- Data validation

↓

Semantic Model
- Fact tables
- Dimension tables
- Relationships
- Measures
- Calculated columns

↓

Power BI Reports
- Charts
- Tables
- Matrices
- Slicers
- Filters
- Drill-through

↓

Power BI Service
- Workspaces
- Published semantic models
- Reports
- Dashboards
- Scheduled refresh
- Permissions
- Distribution

The architecture separates data preparation, analytical modeling, presentation and service-based distribution.

## 4. Power BI Desktop

Power BI Desktop is the Windows application used to develop BI solutions.

It provides the primary environment for connecting data sources, transforming information, defining relationships, creating calculations and designing reports.

### 4.1 Main Views

Power BI Desktop has three principal working views.

| View | Purpose |
|---|---|
| Report View | Design interactive report pages and visualizations |
| Table View | Inspect tables and work with calculated columns and data |
| Model View | Create and inspect relationships between tables |

### 4.2 Data Acquisition

Power BI Desktop supports multiple data connection methods.

Examples include:

- Excel workbooks
- CSV files
- PostgreSQL
- SQL Server
- Web sources
- REST API-based integrations
- Supported cloud applications
- SharePoint
- Azure services

The choice of source connection influences refresh behavior, security requirements, transformation capabilities and performance.

### 4.3 Import Mode

Import mode loads data into the Power BI semantic model.

Characteristics:

- Data is stored within the model.
- VertiPaq provides columnar compression.
- Analytical queries can execute against the imported model.
- Data must be refreshed to reflect source changes.
- Model size and refresh duration require management.

Import mode is appropriate when analytical performance and a controlled refresh schedule are important.

### 4.4 DirectQuery Mode

DirectQuery allows supported data sources to be queried without importing the entire analytical dataset into the model.

Characteristics:

- Data remains primarily in the underlying source.
- Queries are sent to the source system.
- Results depend on source availability and query performance.
- Source-system capacity affects report responsiveness.
- Certain modeling and transformation capabilities have mode-specific restrictions.

DirectQuery is useful when data freshness, source-system ownership or dataset size makes full import unsuitable.

### 4.5 Direct Lake

Direct Lake is a storage and query mode associated with Microsoft Fabric and supported OneLake data architectures.

It enables semantic models to work with data stored in supported Delta tables without the conventional full import process or traditional DirectQuery execution for every analytical interaction.

It has specific platform, capacity and feature requirements.

### 4.6 Storage Mode Comparison

| Feature | Import | DirectQuery | Direct Lake |
|---|---|---|---|
| Data location | Imported model | Underlying source | Supported OneLake storage |
| Query execution | Primarily in-memory | Underlying source | Supported Direct Lake engine |
| Source freshness | Depends on refresh | Queries source data | Depends on underlying data and platform behavior |
| Performance | Generally fast analytical queries | Depends on source performance | Designed for large analytical workloads |
| Infrastructure | Semantic model storage | Source availability and capacity | Fabric and OneLake requirements |

## 5. Power Query and Data Transformation

Power Query is the data preparation and transformation component of Power BI.

It implements an ETL/ELT-style workflow:

1. Extract information from supported sources.
2. Transform and clean the data.
3. Load the prepared information into the analytical model or supported destination.

### 5.1 Common Transformations

| Transformation | Purpose |
|---|---|
| Remove Columns | Eliminate unnecessary attributes |
| Filter Rows | Restrict records |
| Change Type | Assign appropriate data types |
| Remove Duplicates | Eliminate duplicate records |
| Replace Values | Standardize inconsistent values |
| Merge Queries | Join related datasets |
| Append Queries | Combine compatible datasets |
| Group By | Aggregate records |
| Split Column | Separate compound fields |
| Pivot | Convert values into columns |
| Unpivot | Convert columns into attribute-value rows |

### 5.2 Power Query M

Power Query uses the M language for defining transformation steps.

A query is represented through a sequence of expressions. Its Applied Steps interface provides a readable representation of transformations.

Important mechanisms include:

- Query dependencies.
- Data type management.
- Error handling.
- Parameterization.
- Query folding.
- Source connectivity.

### 5.3 Query Folding

Query folding occurs when Power Query translates supported transformation operations into native operations executed by the source system.

For example, a filter on a large PostgreSQL table may be translated into a SQL `WHERE` condition.

Benefits include:

- Reduced data transfer.
- Less local processing.
- Better scalability.
- Improved refresh efficiency.

Not all transformations can be folded. The actual behavior depends on the connector, source capabilities and transformation sequence.

## 6. Data Modeling and the Star Schema

A semantic model organizes information into related tables that support analytical calculations.

The star schema is a common dimensional modeling approach.

It consists of a central fact table connected to descriptive dimension tables.

### 6.1 Fact Tables

Fact tables contain measurable business events.

The implemented sales fact table includes:

- Transaction identifier.
- Customer key.
- Product key.
- Date key.
- Quantity.
- Unit price.
- Revenue.
- Cost.
- Profit.

The grain of the table is one sales transaction.

The grain defines what one row represents. It must be established before aggregations and relationships are designed.

### 6.2 Dimension Tables

Dimension tables provide descriptive context.

| Dimension | Attributes |
|---|---|
| Customer | Name, region, customer segment |
| Product | Name, category, unit cost |
| Date | Date, year, quarter, month, day |

Dimensions support grouping, filtering, slicing and drill-down operations.

### 6.3 Star Schema Diagram

DimCustomer ───┐

DimProduct ────┼── FactSales

DimDate ───────┘

The fact table contains measurable events, while the dimension tables describe those events.

### 6.4 Relationship Cardinality

Common relationship patterns include:

| Relationship | Meaning |
|---|---|
| One-to-many | One customer can have multiple transactions |
| Many-to-one | Multiple fact records reference one dimension record |
| One-to-one | Each record corresponds to one record in another table |
| Many-to-many | Multiple records on each side can relate to multiple records on the other side |

A typical sales model uses one-to-many relationships from dimensions to facts.

### 6.5 Relationship Direction

Single-direction filtering generally allows filters to flow from dimension tables to fact tables.

Bidirectional filtering can be useful in specific models, but it may introduce ambiguity, unexpected filter propagation and performance problems.

Relationship direction should be designed according to the analytical requirements.

### 6.6 Slowly Changing Dimensions

Slowly Changing Dimensions (SCD) manage historical changes to descriptive attributes.

Two common approaches are:

- Type 1: Overwrite the previous value.
- Type 2: Preserve historical versions using effective dates and current-record indicators.

The PostgreSQL implementation includes effective-period and current-record fields in its customer dimension as a foundation for Type 2 modeling.

The sample refresh procedure updates current customer attributes and does not implement complete Type 2 history creation.

## 7. DAX and Business Measures

Data Analysis Expressions (DAX) is the formula language used by Power BI semantic models.

DAX supports calculations over model tables and relationships.

### 7.1 Measures

Measures are evaluated when a visual or query requests a value.

Their results depend on the current filter context.

Examples include:

| Measure | Business meaning |
|---|---|
| Total Revenue | Sum of sales revenue |
| Total Cost | Sum of transaction costs |
| Total Profit | Revenue minus cost |
| Profit Margin | Profit divided by revenue |
| Average Order Value | Revenue divided by transaction count |
| Unique Customers | Number of distinct customers |

The implementations calculate these measures programmatically and through PostgreSQL aggregations.

### 7.2 Example DAX Measures

**Total Revenue**

`Total Revenue = SUM(FactSales[Revenue])`

**Total Cost**

`Total Cost = SUM(FactSales[Cost])`

**Total Profit**

`Total Profit = [Total Revenue] - [Total Cost]`

**Profit Margin**

`Profit Margin = DIVIDE([Total Profit], [Total Revenue], 0)`

**Unique Customers**

`Unique Customers = DISTINCTCOUNT(FactSales[CustomerKey])`

**Average Order Value**

`Average Order Value = DIVIDE([Total Revenue], COUNTROWS(FactSales), 0)`

The final measure assumes each fact row represents one order. A production model must distinguish transactions, orders and order lines when their grains differ.

### 7.3 Calculated Columns and Measures

| Characteristic | Calculated Column | Measure |
|---|---|---|
| Evaluation | During model processing or recalculation | At query time |
| Storage | Stored in the model | Usually not stored as a row-by-row result |
| Context | Row context during calculation | Filter context during evaluation |
| Typical use | Classification and attributes | KPIs and aggregations |

### 7.4 Filter Context

Filter context defines the records considered when a calculation executes.

For example:

- A region slicer filters sales to North.
- A year filter restricts sales to 2026.
- A product selection restricts results to the selected product.

A measure recalculates according to the active context.

### 7.5 Row Context

Row context represents the current row being evaluated.

Calculated columns and iterator functions commonly use row context.

### 7.6 Context Transition

Context transition converts row context into filter context in appropriate DAX operations, particularly through `CALCULATE`.

Understanding these contexts is essential for writing accurate analytical expressions.

## 8. Reports and Visualizations

A Power BI report is an interactive collection of one or more report pages.

It presents information through visualizations connected to the semantic model.

### 8.1 Common Visualizations

| Visualization | Purpose |
|---|---|
| Bar Chart | Compare categories |
| Column Chart | Compare values across categories |
| Line Chart | Analyze trends over time |
| Pie Chart | Show proportions |
| Donut Chart | Display proportional composition |
| Table | Display detailed records |
| Matrix | Display hierarchical summaries |
| Card | Display an individual KPI |
| KPI Visual | Compare performance against a target or trend |
| Scatter Chart | Analyze relationships between numerical variables |
| Map | Present geographical information |

Visual selection should match the analytical question.

For example, monthly revenue trends are generally better represented by a line chart than a pie chart.

### 8.2 Report Pages

A report can contain multiple pages organized around business functions.

Example:

**Page 1: Executive Overview**
- Total Revenue.
- Total Profit.
- Profit Margin.
- Monthly Sales.

**Page 2: Regional Analysis**
- Revenue by region.
- Profit by region.
- Regional contribution.
- Customer distribution.

**Page 3: Product Analysis**
- Product revenue.
- Units sold.
- Category performance.
- Product profitability.

**Page 4: Customer Analysis**
- Customer segments.
- Regional customer distribution.
- Customer contribution.
- Transaction details.

### 8.3 Report Interactions

Power BI supports interactive analytical operations.

- Cross-filtering.
- Cross-highlighting.
- Slicers.
- Visual-level filters.
- Page-level filters.
- Report-level filters.
- Drill-down.
- Drill-through.
- Tooltips.
- Bookmarks.
- Page navigation.

These interactions allow users to investigate the same underlying dataset from different perspectives.

## 9. Dashboards

A dashboard is a single-page monitoring surface in Power BI Service.

It consists of tiles that can display information from supported reports, semantic models and other supported content.

Dashboards are different from reports.

| Characteristic | Report | Dashboard |
|---|---|---|
| Primary environment | Desktop and Service | Service |
| Page structure | Multiple pages possible | Single-page surface |
| Visualizations | Interactive report visuals | Dashboard tiles |
| Data sources | Typically one semantic model per report | Tiles can come from different supported sources |
| Slicers | Supported | Not equivalent to report slicers |
| Drill-through | Supported where configured | Not a native dashboard-page interaction |
| Main purpose | Detailed analysis | Monitoring and overview |

### 9.1 Dashboard KPI Design

An executive dashboard should prioritize information relevant to business objectives.

The implemented sales scenario includes:

- Total Revenue.
- Total Cost.
- Total Profit.
- Profit Margin.
- Average Order Value.
- Unique Customers.

Dashboard indicators should have clearly defined calculation rules, reporting periods and data-refresh timestamps.

### 9.2 Reports and Dashboards in Power BI Service

A report can be published from Power BI Desktop to an appropriate workspace in Power BI Service.

Supported dashboard functionality can then be used to pin selected report visuals as tiles.

A dashboard does not simply represent another name for a report.

## 10. Power BI Service and Workspace Architecture

Power BI Service is Microsoft's cloud-based environment for distributing, managing and collaborating on BI content.

### 10.1 Main Service Capabilities

- Workspace management.
- Report publication.
- Semantic model management.
- Dashboard creation.
- Scheduled refresh.
- Data-source credentials.
- Gateway configuration.
- App distribution.
- Access management.
- Usage monitoring.
- Endorsement and governance.
- Deployment pipelines, where supported.

### 10.2 Workspace Roles

Power BI workspace roles include:

| Role | General responsibility |
|---|---|
| Admin | Manage workspace configuration and access |
| Member | Manage workspace content and collaboration |
| Contributor | Create and modify workspace content |
| Viewer | View workspace content subject to applicable permissions |

Workspace permissions should follow least-privilege principles.

A report viewer should not automatically receive administrative or content-editing privileges.

### 10.3 Publishing Workflow

Power BI Desktop
→ Publish
→ Select Workspace
→ Upload Report and Semantic Model
→ Configure Credentials
→ Configure Refresh
→ Verify Access
→ Distribute Content

Publishing a report does not automatically mean every user can access it.

Access depends on workspace permissions, licensing, capacity and sharing configuration.

## 11. Data Refresh and Connectivity

Refresh is the process of updating data used by a semantic model.

### 11.1 Refresh Types

| Refresh approach | Purpose |
|---|---|
| Manual refresh | User initiates a refresh |
| Scheduled refresh | Refresh executes according to a configured schedule |
| API-triggered refresh | A supported API initiates a refresh |
| Incremental refresh | Processes eligible data partitions instead of refreshing the entire historical dataset |
| DirectQuery interaction | Queries supported source data during report interaction |

The exact refresh capabilities depend on semantic model storage mode, licensing, capacity and source connectivity.

### 11.2 Gateway Architecture

For supported private-network sources, a gateway can provide connectivity between Power BI Service and the underlying source.

Power BI Service
→ Gateway
→ Private Network
→ Database

Gateway administration includes:

- Installation.
- Source registration.
- Credential management.
- Availability monitoring.
- Cluster configuration where applicable.
- Connection validation.

### 11.3 Refresh Failure Conditions

Typical causes include:

- Invalid credentials.
- Database unavailability.
- Gateway disconnection.
- Schema changes.
- Missing source columns.
- Data-type conversion errors.
- Query timeouts.
- Capacity constraints.
- Network interruptions.

The implementations include refresh-state management, error reporting and record validation.

## 12. Security and Governance

BI governance ensures that information is accessed, processed and distributed appropriately.

### 12.1 Important Security Controls

**Authentication**

Verifies user identity.

**Authorization**

Determines permitted operations.

**Workspace Access**

Controls access to collaborative BI content.

**Row-Level Security (RLS)**

Restricts which rows users can access.

**Object-Level Security (OLS)**

Restricts access to supported model objects such as tables and columns.

**Data Source Credentials**

Control access to underlying source systems.

**Sensitivity Labels**

Support information classification and protection.

**Audit and Monitoring**

Provide visibility into access and administrative activity.

### 12.2 Row-Level Security Example

A sales organization may permit regional managers to see only their assigned regional transactions.

Example mapping:

| User | Authorized region |
|---|---|
| north_manager | North |
| south_manager | South |
| east_manager | East |
| west_manager | West |

RLS must be configured in the semantic model and supported by the relevant identity and access arrangements.

The application-level access controls in the source implementations are educational simulations, not replacements for Power BI's native security mechanisms.

### 12.3 Data Governance

Important governance responsibilities include:

- Ownership of semantic models.
- Business definitions of measures.
- Dataset certification and endorsement.
- Data lineage.
- Data quality.
- Access reviews.
- Refresh monitoring.
- Retention requirements.
- Sensitive-data classification.

Consistent KPI definitions are particularly important when several departments use the same analytical model.

## 13. Implementation Architecture Across the Five Files

The five implementations demonstrate complementary aspects of the same sales analytics scenario.

| File | Engineering perspective | Implemented functionality |
|---|---|---|
| Python | Data processing and analytical simulation | ETL, star schema, measures, filtering, reports, dashboard and exports |
| JavaScript | Event-driven analytical application | Asynchronous refresh, events, filter context, report generation and exports |
| C++17 | Data and governance engine | Warehouse loading, analytics, permissions and publication eligibility |
| Java 17 | Enterprise domain architecture | Immutable records, services, report transitions, authorization and refresh lifecycle |
| PostgreSQL | Relational warehouse architecture | Source tables, dimensions, fact table, ETL, views, procedures and governance |

### 13.1 Python Implementation

The Python script demonstrates a complete local analytical processing workflow.

Its main components are:

- `Customer`, `Product` and `SalesTransaction` data classes.
- `DataTransformer` for data validation and transformation.
- `StarSchema` for fact and dimension organization.
- `Measures` for business calculations.
- `ReportEngine` for filtering and aggregation.
- `Dashboard` for KPI presentation.
- `RefreshManager` for refresh-state management.
- CSV and JSON export functions.

It uses standard-library collections, dictionaries, data classes, enums, file handling and assertions.

### 13.2 JavaScript Implementation

The JavaScript implementation focuses on event-driven processing.

Its main components are:

- `DataValidator`.
- `ETLPipeline`.
- `DataModel`.
- `MeasureEngine`.
- `FilterContext`.
- `ReportBuilder`.
- `Dashboard`.
- `RefreshService`.

The `EventEmitter` mechanism communicates refresh events to listeners.

Asynchronous operations use Promises and `async`/`await`.

The implementation also provides JSON and CSV exports using Node.js file-system capabilities.

### 13.3 C++17 Implementation

The C++ implementation models an analytical processing and publication engine.

Its main components are:

- `SourceRepository`.
- `DataValidator`.
- `DataWarehouse`.
- `AnalyticsEngine`.
- `QueryEngine`.
- `ReportManager`.
- `AccessControl`.
- `RefreshManager`.
- `DashboardEngine`.

The warehouse uses staging records before replacing its existing in-memory dataset.

This design prevents partial replacement if the transformation fails.

The report publication lifecycle distinguishes draft, review, approval and publication states.

### 13.4 Java 17 Implementation

The Java implementation follows an enterprise service-oriented design.

Its main components are:

- Immutable domain records.
- `DataRepository`.
- `ValidationService`.
- `ETLService`.
- `DimensionalModel`.
- `MeasureService`.
- `FilterService`.
- `ReportService`.
- `AuthorizationService`.
- `RefreshService`.
- `DashboardService`.

Java records provide concise immutable domain types.

The report service validates state transitions rather than permitting arbitrary status changes.

The authorization service separates user permissions from business operations.

### 13.5 PostgreSQL Implementation

The database implementation establishes a relational foundation for BI reporting.

It separates four schemas:

| Schema | Responsibility |
|---|---|
| `bi_source` | Operational source data |
| `bi_warehouse` | Fact and dimension tables |
| `bi_governance` | Users, workspaces, reports and reviews |
| `bi_reporting` | Analytical views |

The database implements referential integrity, uniqueness, check constraints, indexes, generated columns, views, functions and procedures.

Its refresh procedure performs dimension synchronization and fact-table upserts.

The reporting views provide reusable datasets for analytical consumption.

## 14. PostgreSQL Data Model

The database uses a dimensional structure.

### 14.1 Source Tables

**customers**

Stores customer identifiers, names, regions and segments.

**products**

Stores product identifiers, names, categories and unit costs.

**sales_transactions**

Stores transactional sales records and references the source customer and product records.

### 14.2 Warehouse Tables

**dim_customer**

Provides customer dimension records.

**dim_product**

Provides product dimension records.

**dim_date**

Provides calendar attributes.

**fact_sales**

Stores the measurable sales events and foreign keys referencing the dimensions.

### 14.3 Governance Tables

**users**

Stores BI application user identities.

**workspaces**

Represents collaborative analytical environments.

**workspace_members**

Associates users with workspaces and roles.

**reports**

Stores report metadata and publication status.

**report_visuals**

Stores report visual definitions.

**report_reviews**

Stores review decisions and comments.

### 14.4 Reporting Views

The database creates:

- `vw_sales_analysis`
- `vw_dashboard_kpis`
- `vw_regional_sales`
- `vw_product_performance`
- `vw_monthly_sales`

These views provide stable analytical interfaces for reporting applications.

## 15. Business Scenario and Expected Workflow

The implementations use a retail sales organization.

The organization sells laptops, monitors, office furniture and accessories to customers across four regions.

Its analytical requirements include:

- Measuring total sales revenue.
- Calculating product costs and profit.
- Comparing regional performance.
- Identifying high-performing products.
- Evaluating monthly sales.
- Monitoring customer participation.
- Publishing executive reports.

### 15.1 Example Processing Workflow

Source Transactions
→ Data Validation
→ Dimension Lookup
→ Revenue and Cost Calculation
→ Fact Table Loading
→ Analytical Aggregation
→ KPI Generation
→ Report Construction
→ Dashboard Publication

### 15.2 Business Rules

| Rule | Implementation |
|---|---|
| Customer identifiers must be valid | Referential validation |
| Product identifiers must be valid | Referential validation |
| Transaction quantity must be positive | Check constraint and validation |
| Unit price cannot be negative | Check constraint and validation |
| Product cost cannot be negative | Check constraint and validation |
| Revenue equals quantity multiplied by price | Derived calculation |
| Profit equals revenue minus cost | Derived calculation |
| Profit margin uses revenue as denominator | Zero-safe calculation |
| Reports follow controlled publication states | State-transition validation |
| Unauthorized operations are rejected | Access-control checks |

### 15.3 Example Analytical Interpretation

A regional revenue report can identify which regions contribute the largest share of sales.

A product report can distinguish high-revenue products from high-profit products.

These are not necessarily the same products because selling price and product cost differ.

A profit-margin calculation helps distinguish revenue growth from profitability improvement.

The results must be interpreted with consideration for transaction volume, reporting periods and the underlying cost assumptions.

## 16. Performance and Scalability

BI performance depends on data volume, model structure, query design, storage mode, source-system performance and service capacity.

### 16.1 Data Modeling

A well-designed star schema generally simplifies analytical relationships and improves model usability.

Important considerations:

- Use appropriate data types.
- Remove unnecessary columns.
- Avoid unnecessary high-cardinality attributes.
- Establish a clear fact-table grain.
- Prefer meaningful dimension relationships.
- Avoid unnecessary bidirectional filtering.

### 16.2 DAX Performance

Measures should avoid unnecessary iteration over large tables.

Important considerations:

- Use native aggregation functions where appropriate.
- Reduce repeated calculations.
- Use `VAR` for reusable intermediate expressions.
- Avoid unnecessarily complex filter expressions.
- Understand filter-context propagation.
- Evaluate the performance of expensive measures.

### 16.3 Database Performance

The PostgreSQL implementation creates indexes on commonly used foreign keys and date columns.

Composite indexes can support queries that filter by customer and date together.

Indexes have a maintenance cost during writes. They should be justified by actual query patterns.

For large warehouse tables, partitioning, incremental loading and materialized analytical structures may be appropriate.

### 16.4 Processing Complexity

Let:

- `n` represent the number of sales transactions.
- `c` represent the number of customers.
- `p` represent the number of products.
- `k` represent the number of distinct analytical groups.

| Operation | Typical complexity |
|---|---|
| Building customer lookup | O(c) |
| Building product lookup | O(p) |
| Transforming transactions with hash lookups | Expected O(n) |
| Aggregating transactions into hash-based groups | Expected O(n) |
| Sorting k grouped results | O(k log k) |
| Finding distinct customers using a hash set | Expected O(n) |
| Sorting top-product candidates | O(k log k) |
| Indexed relational lookup | Depends on index structure and query plan |

The Python and JavaScript implementations use lookup maps to avoid repeatedly scanning dimension tables for every transaction.

The C++ implementation uses unordered maps for dimension lookups.

The PostgreSQL implementation delegates joins and aggregations to the database query engine.

## 17. Data Quality and Failure Management

A BI solution should not assume that source information is correct.

Important validation areas include:

- Duplicate identifiers.
- Missing foreign keys.
- Invalid dates.
- Negative prices.
- Zero or negative quantities.
- Unexpected categories.
- Missing customer information.
- Invalid data types.
- Inconsistent source schemas.

The implementations distinguish validation failures from refresh failures.

A successful refresh should be accompanied by record reconciliation and calculation checks.

The PostgreSQL refresh procedure records execution status and error messages.

Its inner exception block handles the failed refresh record while allowing the failed data-loading work to roll back.

Production systems should also monitor data freshness, refresh duration, failed partitions and source availability.

## 18. Security Considerations

The examples implement basic access-control and validation concepts.

A production Power BI deployment requires additional platform-level controls.

Important considerations include:

1. Use authenticated organizational identities.
2. Apply least-privilege workspace permissions.
3. Configure RLS for user-specific data access.
4. Use OLS where supported and required.
5. Protect data-source credentials.
6. Secure private-network gateway infrastructure.
7. Classify sensitive information.
8. Monitor access and sharing activity.
9. Control report publication.
10. Review external sharing and export permissions.

The SQL roles are database-level roles. They are separate from Power BI workspace roles.

Database permissions do not automatically establish Power BI semantic-model security.

Likewise, application-level filtering must not be treated as a substitute for enforced authorization.

## 19. Technical Limitations

The implementations are educational simulations of BI concepts, not complete replacements for Microsoft's Power BI platform.

| Area | Implemented behavior | Platform-specific limitation |
|---|---|---|
| Power Query | Programmatic ETL equivalents | Does not execute M |
| Semantic model | In-memory fact and dimension structures | Does not create a Power BI semantic model |
| DAX | Equivalent business calculations | Does not execute DAX |
| Visualizations | Report data and visual definitions | Does not render Power BI visuals |
| Dashboards | KPI collections | Does not create Power BI Service dashboard tiles |
| Refresh | Local or database refresh simulation | Does not invoke the Power BI refresh engine |
| Security | Basic role and permission models | Does not implement Entra ID, native RLS or OLS |
| Workspaces | Relational workspace metadata | Does not create actual Power BI workspaces |
| Publication | Controlled report lifecycle | Does not publish PBIX files |
| Gateway | Architectural explanation | Does not install or administer a gateway |

The PostgreSQL customer dimension demonstrates current-record synchronization but does not implement complete historical Type 2 dimension processing.

The analytical examples also assume that product cost can be used to calculate transaction cost. Actual financial reporting may require purchase-cost history, discounts, returns, taxes, shipping and accounting adjustments.

## 20. Practical Application

A complete organizational BI solution should establish a clear separation between operational systems, data preparation, analytical models and business presentation.

The following responsibilities should be defined:

| Responsibility | Primary function |
|---|---|
| Data engineer | Source integration and warehouse preparation |
| BI developer | Semantic modeling and report development |
| Data analyst | Analytical investigation and KPI interpretation |
| Business owner | Business definitions and reporting requirements |
| Workspace administrator | Access, publication and workspace governance |
| Data owner | Data quality, lineage and appropriate use |

A reliable reporting environment depends on consistent definitions, validated data, controlled access and repeatable refresh operations.

The implementations establish these concepts through a common retail sales domain while demonstrating how different programming languages and relational database technologies can support the underlying Business Intelligence workflow.
