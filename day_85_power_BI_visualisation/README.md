# Power BI Visualization: Interactive Analytical Dashboards

## 1. Project Scope

This project implements the fundamental and advanced mechanisms used in Power BI dashboard visualization.

The subject is organized around seven visualization and interaction components:

1. Cards
2. Tables
3. Matrices
4. Charts
5. Maps
6. Slicers
7. Drill-through and bookmarks

The implementations use a retail sales dataset containing transactions, geographical locations, products, categories, salespersons, quantities, prices, and discounts.

The central objective is to demonstrate how transactional data becomes aggregated analytical information and how users interact with that information through a dashboard.

## 2. Analytical Data Model

The retail dataset contains the following entities:

| Entity | Description |
|---|---|
| Transaction | Individual sales transaction |
| Date | Transaction date |
| Region | Geographic sales region |
| City | Transaction location |
| Category | Product classification |
| Product | Individual product |
| Salesperson | Person responsible for the transaction |
| Quantity | Number of units sold |
| Unit Price | Price per unit |
| Discount | Discount applied to the transaction |

### Calculated measures

The implementations use consistent calculations.

**Gross Sales**

\[
GrossSales = Quantity \times UnitPrice
\]

**Net Sales**

\[
NetSales = GrossSales \times (1-Discount)
\]

**Estimated Profit**

\[
Profit = NetSales \times 0.25
\]

The profit calculation uses a fixed illustrative margin of 25%. It does not represent an actual accounting profit calculation because operating expenses, taxes, inventory costs, and other business expenses are not modeled.

### Dataset flow

Sales Transactions
       |
       v
Data Validation
       |
       v
Dimension Relationships
       |
       v
Calculated Measures
       |
       v
Filter Context
       |
       v
Aggregation
       |
       v
Visualization Datasets
       |
       v
Dashboard Interaction


3. Cards
A Card is a single-value visualization used to display an important business measure.

Typical applications include:
- Total sales
- Total profit
- Total transactions
- Average transaction value
- Units sold
- Customer count
A sales card calculates the sum of net sales across the currently selected dataset.
\[
TotalSales = \sum_{i=1}^{n} NetSales_i
\]

Implementation
Language	Mechanism
Python	card()
JavaScript	VisualEngine.card()
C++17	displayCard()
Java 17	CardResult and card()
PostgreSQL	calculate_kpi()

Cards depend on the active filter context. Selecting a region or product category changes the records included in the aggregation.

A card is appropriate for a single KPI. It is not intended to replace a detailed transaction table.
4. Tables
Tables display detailed or grouped records using rows and columns.

A regional sales table can contain:
Region	Category	Net Sales	Profit
North	Electronics	Aggregated value	Aggregated value
South	Electronics	Aggregated value	Aggregated value
West	Clothing	Aggregated value	Aggregated value

A table can display:
- Dimensions
- Measures
- Transaction details
- Grouped values
- Calculated columns
- Totals
The implementations group records by selected dimensions and calculate the requested measures.
Aggregation process
1. Identify grouping dimensions.
2. Read the filtered transaction records.
3. Construct a grouping key.
4. Accumulate numerical measures.
5. Return ordered table rows.
The Python implementation uses dictionaries and defaultdict.

The JavaScript implementation uses Map.

The C++ implementation uses STL maps.

The Java implementation uses collections and stream-based grouping.

PostgreSQL performs grouping through GROUP BY.
Table versus card
A card communicates one aggregated value.

A table communicates multiple values associated with identifiable dimensions.
5. Matrices
A Matrix is a cross-tabulated visualization that organizes information using row and column dimensions.

For example:
- Rows: Region
- Columns: Product Category
- Values: Net Sales
The matrix represents the relationship between two dimensions and one numerical measure.

Conceptually:
\[
M_{ij} = \sum NetSales
\]

Where:
- \(i\) represents a region.
- \(j\) represents a product category.
- \(M_{ij}\) represents sales for that combination.
Matrix characteristics
- Row groups
- Column groups
- Aggregated values
- Row subtotals
- Column subtotals
- Grand totals
- Hierarchical expansion
- Cross-dimensional comparisons
The Python implementation creates a nested aggregation structure.

The JavaScript implementation uses a Map keyed by dimension combinations.

The C++ implementation uses nested ordered maps.

The Java implementation uses typed matrix results and grouped collections.

The PostgreSQL function regional_category_matrix() returns the aggregated region-category combinations.
Matrix versus table
A table displays records in a conventional tabular arrangement.

A matrix reorganizes measures across two or more analytical dimensions. It is particularly useful for comparing combinations and identifying patterns across categories.
6. Charts
Charts communicate patterns, comparisons, trends, and proportions.

The project implements three chart categories.
6.1 Bar Chart
A bar chart compares numerical values across categorical dimensions.

Example:
- Dimension: Product Category
- Measure: Net Sales
Applications:
- Regional performance comparison
- Product sales comparison
- Salesperson performance
- Category ranking
The implementation groups transactions by category and calculates total net sales.
6.2 Line Chart
A line chart represents changes in a numerical measure over an ordered dimension, generally time.

Example:
- X-axis: Sales Month
- Y-axis: Net Sales
Applications:
- Monthly revenue trends
- Seasonal performance
- Growth patterns
- Historical comparisons
The dataset uses monthly aggregation.

The month dimension follows the YYYY-MM format, preserving chronological ordering.

A production Power BI model would normally use a dedicated date dimension with year, quarter, month, and day attributes.
6.3 Pie Chart
A pie chart represents the contribution of individual categories to a total.

The percentage contribution is:
\[
Contribution_i =
\frac{CategorySales_i}{TotalSales}
\times 100
\]

Applications:
- Product category contribution
- Revenue distribution
- Market composition
Pie charts are most effective when the number of categories is limited.

When many categories exist, a bar chart generally provides clearer comparisons.
Chart implementation comparison
Chart	Dimension	Measure	Analytical purpose
Bar	Category	Net Sales	Comparison
Line	Month	Net Sales	Trend
Pie	Category	Net Sales	Proportion

The five implementations generate chart-ready datasets. Actual graphical rendering is handled by a visualization client.
7. Maps
Maps associate analytical measures with geographic locations.

The project aggregates transactions by region and city.

The geographic dataset contains:
- Region
- City
- Latitude
- Longitude
- Total sales
- Transaction count
Geographic visualization workflow
Transaction Records
        |
        v
City and Region Mapping
        |
        v
Geographic Aggregation
        |
        v
Coordinate Validation
        |
        v
Sales Measure Calculation
        |
        v
Map Visualization


Map visualization types
Type	Purpose
Bubble map	Compare values through marker size
Filled map	Compare geographic areas
Point map	Display individual locations
Shape map	Compare predefined geographic boundaries

The Python, JavaScript, C++, and Java implementations produce geographic aggregates.

The PostgreSQL implementation provides the geographic_sales view.

The SQL schema stores latitude and longitude with range constraints.

Missing coordinates are treated as a data-quality issue rather than being replaced with fabricated values.

A production geographic implementation must also validate coordinate accuracy, geographic reference systems, location ambiguity, and map-provider requirements.
8. Slicers
Slicers are interactive filtering controls placed on a dashboard or report page.

They allow users to select the data they want to analyze.

The project implements the following filtering patterns.
Slicer type	Example	Behavior
Single selection	Region = North	Selects one value
Multiple selection	North and South	Selects several values
Numeric range	Sales between two amounts	Applies numerical boundaries
Date range	January to March	Restricts transaction dates

Filter context
A slicer changes the set of records available to dependent visualizations.

If the active filter is:

Region = North

The sales card, table, matrix, and chart must calculate their values using northern-region transactions.

When another filter is applied:

Category = Electronics

Both conditions must be satisfied.

Formally:
\[
FilteredData =
\{r \in D : F_1(r) \land F_2(r)\}
\]

Where:
- \(D\) is the original dataset.
- \(F_1\) is the regional filter.
- \(F_2\) is the category filter.
Cross-filtering
Cross-filtering occurs when an interaction with one visualization affects other visualizations.

For example:
1. A user selects Electronics in a category chart.
2. The dashboard establishes the corresponding filter context.
3. The regional table is recalculated.
4. The sales card displays the filtered sales.
5. The map displays the corresponding geographic distribution.
Cross-filtering is an interaction mechanism. It should not be confused with permanently modifying source transactions.
Implementation
Language	Filter mechanism
Python	Dictionary-based filter state
JavaScript	FilterEngine and Map
C++17	Ordered filter map
Java 17	DashboardFilter record
PostgreSQL	dashboard_filter_states

The database stores user-specific filter selections as JSONB.

The application remains responsible for interpreting those selections and applying appropriate access controls.
9. Drill-through
Drill-through provides navigation from an aggregated analytical view to a detailed report page.

For example:

A user selects the North region in a regional sales table.

The dashboard opens a transaction detail page containing the relevant records.
Drill-through workflow
Regional Sales Table
        |
        v
Select North Region
        |
        v
Capture Filter Context
        |
        v
Validate Target Page
        |
        v
Apply Dimension Filter
        |
        v
Retrieve Matching Transactions
        |
        v
Display Detailed Report


Drill-through information
The detailed report can contain:
- Transaction ID
- Transaction date
- Region
- City
- Product category
- Product
- Quantity
- Net sales
- Profit
Drill-through versus drill-down
These mechanisms serve different purposes.
Feature	Drill-through	Drill-down
Primary behavior	Navigate to another report page	Expand a hierarchy
Context	Transfers selected dimension values	Changes displayed hierarchy level
Example	Region to transaction details	Year to quarter to month
Destination	Another report page	Deeper level of the same hierarchy

The implementations validate the source dimension and target destination before returning detail records.

The Java implementation introduces a dashboard policy that controls permitted navigation.

The PostgreSQL implementation uses drillthrough_pages to configure available routes.
10. Bookmarks
Bookmarks preserve a particular dashboard presentation state.

A bookmark can represent a saved analytical perspective.

For example:

North Region Analysis

The saved state can contain:
- Active slicer selections
- Selected visualization
- Visual visibility settings
- Other dashboard presentation settings
Bookmark workflow
Configure Slicers
       |
       v
Select Visual
       |
       v
Save Bookmark
       |
       v
Change Dashboard State
       |
       v
Restore Bookmark
       |
       v
Recover Saved State


Bookmarks versus filters
A filter defines which records are included in an analysis.

A bookmark preserves a particular dashboard state.

Restoring a bookmark does not modify the original transaction dataset.

The implementations use:
Language	Bookmark mechanism
Python	DashboardBookmark
JavaScript	BookmarkManager
C++17	Bookmark structure
Java 17	Immutable Bookmark record
PostgreSQL	dashboard_bookmarks

The SQL implementation stores filter snapshots and visual visibility information using JSONB.

In an actual Power BI report, bookmarks can also preserve display settings and support navigation between report views.
11. Dashboard Architecture
The visualization components operate as parts of a coordinated analytical system.
                  DATA SOURCE
                       |
                       v
               DATA PREPARATION
                       |
                       v
                DATA MODEL
                       |
                       v
              CALCULATED MEASURES
                       |
                       v
                FILTER CONTEXT
                       |
          +------------+------------+
          |            |            |
          v            v            v
        CARDS        TABLES       MATRICES
          |            |            |
          +------------+------------+
                       |
                       v
                    CHARTS
                       |
                       v
                     MAPS
                       |
          +------------+------------+
          |                         |
          v                         v
       SLICERS                 CROSS-FILTERING
          |                         |
          +------------+------------+
                       |
                       v
                DRILL-THROUGH
                       |
                       v
                   BOOKMARKS
                       |
                       v
               DASHBOARD STATE


The architecture separates analytical data from visualization configuration and interaction state.

This separation makes it possible to reuse the same measures across multiple visualizations.
12. Python Implementation
File: powerbi_visualization.py

The Python implementation provides a self-contained analytical engine.
Important components
Component	Responsibility
SalesRecord	Immutable transaction representation
VisualizationType	Supported visualization categories
Aggregation	Aggregation operations
SalesDashboard	Dashboard execution
DashboardBookmark	Saved dashboard state
VisualConfiguration	Visualization metadata
ValidationError	Input validation
DrillThroughError	Navigation failures

Technical mechanisms
- Dataclasses represent transaction records.
- Enums constrain visualization and aggregation types.
- Dictionaries maintain filter and bookmark state.
- Sets support multi-selection.
- defaultdict supports grouped aggregation.
- JSON provides report serialization.
- Exceptions represent invalid operations.
The script exports an analytical report to powerbi_output/dashboard.json.

The export contains card values, table results, matrix results, chart datasets, map aggregates, and active filter state.
Execution
Run:

python powerbi_visualization.py

No external packages are required.
13. JavaScript Implementation
File: powerbi_visualization.js

The JavaScript implementation uses an event-driven architecture.
Important components
Component	Responsibility
SalesTransaction	Transaction domain object
DashboardStore	Dataset management
FilterEngine	Slicer evaluation
VisualEngine	Visualization aggregation
BookmarkManager	Bookmark persistence within runtime
DashboardController	Dashboard orchestration

Event-driven behavior
The dashboard emits events for:
- slicer:changed
- slicer:cleared
- visual:rendered
- visual:selected
- navigation:drillthrough
- navigation:back
- bookmark:saved
- bookmark:restored
- data:refreshed
- report:exported
These events allow other application components to respond to dashboard changes without tightly coupling every visualization to the filter implementation.
Asynchronous processing
Dataset replacement validates the incoming records before updating the existing dataset.

Report export uses Node.js asynchronous file operations.

The implementation also uses structured cloning when preserving dashboard state.
Execution
Run:

node powerbi_visualization.js

The program creates powerbi_dashboard_report.json.

No npm dependencies are required.
14. C++17 Implementation
File: powerbi_visualization.cpp

The C++ implementation focuses on computational efficiency and explicit data structures.
Important components
Component	Responsibility
Transaction	Transaction representation
VisualResult	Visualization result structure
Bookmark	Saved dashboard state
Dashboard	Analytical engine
Aggregation	Aggregation strategies
VisualType	Visualization classification

Engineering decisions
- vector stores transaction records.
- map maintains deterministic grouped results.
- set identifies distinct values.
- STL algorithms implement filtering and aggregation.
- Exceptions handle invalid input and navigation failures.
The program includes a textual bar-chart representation so that the generated analytical values can be inspected without a graphical rendering library.
Execution
Compile:

g++ -std=c++17 -O2 -Wall -Wextra -pedantic powerbi_visualization.cpp -o powerbi_visualization

Run:

./powerbi_visualization

On Windows:

powerbi_visualization.exe

No external libraries are required.
15. Java 17 Implementation
File: PowerBIDashboard.java

The Java implementation uses an enterprise-oriented service architecture.
Domain model
The implementation introduces:
- Transaction
- DashboardFilter
- Range
- Bookmark
- CardResult
- TableRow
- MatrixResult
- MapLocation
- DrillThroughResult
Java records provide immutable data structures for these domain objects.
Service architecture
DashboardRepository manages the transaction dataset.

DashboardService performs analytical operations and maintains the dashboard state.

DashboardPolicy defines navigation and bookmark authorization requirements.

EnterpriseDashboardPolicy implements those requirements.
State management
The dashboard supports:
- READY
- FILTERED
- NAVIGATING
- REFRESHING
- FAILED
A refresh validates the replacement dataset before changing the repository state.

This prevents an invalid replacement from partially overwriting existing records.
Execution
Compile:

javac --release 17 PowerBIDashboard.java

Run:

java PowerBIDashboard

No third-party dependencies are required.
16. PostgreSQL Implementation
File: powerbi_visualization.sql

The PostgreSQL implementation establishes a relational analytical data model.
Database entities
Table or View	Purpose
regions	Geographic regions
cities	Geographic locations
product_categories	Product classifications
products	Product master records
salespersons	Sales personnel
sales_transactions	Transaction fact data
sales_analytics	Analytical reporting view
dashboards	Dashboard definitions
visualizations	Visual configuration
slicers	Slicer definitions
dashboard_filter_states	User-specific filter state
dashboard_bookmarks	Saved dashboard states
drillthrough_pages	Navigation configuration
dataset_refreshes	Refresh history

Relational design
The transaction table references the product, city, and salesperson dimensions.

This separates reusable descriptive information from transaction-level measures.

The sales_analytics view joins these dimensions and calculates reusable analytical values.
Database functions
Function	Purpose
calculate_kpi()	KPI aggregation
regional_category_matrix()	Matrix dataset
monthly_sales_chart()	Time-series dataset
category_contribution()	Pie-chart contribution
get_drillthrough_details()	Detail navigation
restore_bookmark()	Saved-state retrieval

Stored procedure
save_filter_state() performs an upsert of a user's slicer selection.

The unique constraint on dashboard, user, and field prevents duplicate filter-state records.
Trigger
validate_bookmark_snapshot() validates bookmark names and JSON object structures before insertion or update.
Indexing
Indexes support common access patterns:
- Transaction date
- City and transaction date
- Product and transaction date
- Salesperson and transaction date
- Product category
- Dashboard and user filter state
Transaction handling
The SQL file uses a transaction to establish the schema, reference data, sample records, configuration, and reporting objects.

A failure during execution prevents the transaction from being committed.
Execution
Run the complete SQL script using a PostgreSQL client connected to a database where the executing user has schema and table creation privileges.

For example:

psql -d analytics_db -f powerbi_visualization.sql

The script creates the powerbi schema.
17. Aggregation and Performance
Visualization performance depends on the size of the source dataset, the number of active filters, the grouping dimensions, and the complexity of calculations.
Computational complexity
Let:
- \(n\) represent the number of transaction records.
- \(g\) represent the number of resulting groups.
- \(k\) represent the number of active filters.
Operation	Approximate complexity
Single-pass filtering	\(O(nk)\)
Simple KPI aggregation	\(O(n)\)
Hash-based grouping	Average \(O(n)\)
Ordered grouping	\(O(n\log n)\)
Matrix construction	Depends on grouping and distinct dimensions
Bookmark restoration	Proportional to saved state size

The implementations use in-memory datasets and are intended for educational analytical workloads.

Large production datasets require additional considerations.
Performance strategies
- Apply filters as early as possible.
- Aggregate at the appropriate dimensional level.
- Avoid unnecessary high-cardinality visualizations.
- Reuse calculated measures.
- Index frequently filtered database columns.
- Reduce unnecessary detail rows.
- Use incremental refresh where supported.
- Avoid excessive visual interactions.
- Evaluate query execution plans.
- Separate expensive calculations from frequently requested dashboard operations.
Power BI performance also depends on the selected storage mode and semantic model design.

Import mode, DirectQuery, and composite models have different execution and refresh characteristics.
18. Security and Data Quality
A dashboard can expose sensitive business information if authorization is not properly implemented.

Important controls include:
- Authentication
- Role-based access control
- Row-level security
- Object-level security where required
- Database least-privilege permissions
- Validated report parameters
- Controlled drill-through access
- Secure data refresh credentials
- Audit logging
- Data classification
The Java implementation includes a navigation policy.

The SQL implementation includes relational constraints and controlled drill-through configuration.

These mechanisms demonstrate authorization boundaries, but they do not constitute a complete enterprise identity or row-level security implementation.
Data quality checks
The analytical model validates:
- Positive transaction quantities
- Nonnegative prices
- Valid discount percentages
- Unique transaction identifiers
- Valid geographic coordinates
- Nonempty dimension values
- Valid date ranges
Incorrect source data can produce misleading visualizations even when the visualization calculations are technically correct.
19. Important Distinctions
Concept	Main purpose
Card	Communicate a single KPI
Table	Display detailed or grouped records
Matrix	Compare values across multiple dimensions
Bar chart	Compare categories
Line chart	Analyze trends over time
Pie chart	Show proportional contribution
Map	Display geographically associated measures
Slicer	Control the active filter context
Cross-filtering	Propagate selection between visualizations
Drill-through	Navigate to filtered detail pages
Drill-down	Expand a hierarchical dimension
Bookmark	Preserve a dashboard presentation state

These mechanisms are related but are not interchangeable.

A visualization presents information.

A slicer changes the analytical context.

Drill-through changes the reporting destination.

A bookmark preserves a selected dashboard state.
20. Implementation Limitations
The five implementations demonstrate analytical dataset generation and dashboard-state management rather than reproducing the complete Power BI rendering platform.
Capability	Implementation status
KPI calculation	Implemented
Table aggregation	Implemented
Matrix aggregation	Implemented
Bar-chart data	Implemented
Line-chart data	Implemented
Pie-chart data	Implemented
Geographic aggregation	Implemented
Geographic rendering	Requires visualization client
Slicer evaluation	Implemented
Cross-filtering foundation	Implemented
Drill-through data retrieval	Implemented
Bookmark state management	Implemented
Persistent SQL bookmarks	Implemented
Real-time Power BI synchronization	Not implemented
Power BI semantic model integration	Not implemented
Power BI report publishing	Not implemented
Enterprise identity integration	Not implemented
Production row-level security	Not implemented

The SQL implementation stores visualization definitions and returns datasets suitable for reporting applications. It does not render Power BI visuals.

The JavaScript implementation demonstrates event-driven dashboard behavior, but it does not provide an HTML user interface.

The C++ implementation focuses on analytical computation and terminal-based output.

The Java implementation demonstrates enterprise domain modeling, policy evaluation, and state management.

The Python implementation provides a compact, executable analytical workflow.
21. Practical Analytical Workflow
A realistic dashboard analysis follows this sequence:
1. Load and validate transaction data.
2. Establish relationships between fact and dimension tables.
3. Define reusable measures.
4. Configure cards for high-level KPIs.
5. Create tables for detailed comparisons.
6. Create matrices for cross-dimensional analysis.
7. Configure charts for comparisons, trends, and proportions.
8. Add geographic visualizations where location data is reliable.
9. Introduce slicers for interactive filtering.
10. Verify cross-filtering behavior.
11. Configure drill-through destinations.
12. Save frequently used analytical perspectives as bookmarks.
13. Validate calculations against source transactions.
14. Evaluate refresh performance and access permissions.
The resulting dashboard provides multiple analytical views over the same underlying business data while keeping transaction records, calculated measures, visualization definitions, and interaction state logically separate.
