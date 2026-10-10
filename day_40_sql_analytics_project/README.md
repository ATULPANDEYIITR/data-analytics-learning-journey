# SQL Analytics Project

## Project Scope

This project builds an end-to-end business analytics database for a retail operation. The data model connects customers, customer segments, regions, sales representatives, products, product categories, orders, and order line items.

The analytical layer is designed around business questions rather than isolated SQL syntax. It covers revenue, profitability, customer value, product performance, regional performance, sales representative performance, order outcomes, discount behavior, time-series analysis, ranking, contribution analysis, data quality, and database-level integrity.

The six deliverables use different technical perspectives:

| Deliverable | Technical focus |
|---|---|
| Python | Reproducible analytics pipeline, validation, SQLite execution, reporting export |
| JavaScript | Event-driven analytics, asynchronous ingestion, validation, KPI computation |
| C++ | Strongly typed analytics engine and performance-oriented aggregation |
| Java | Enterprise domain model, immutable records, validation, streams, service boundaries |
| SQL | Normalized relational model, constraints, indexes, views, CTEs, window functions, transactions |
| README | Architecture, analytical reasoning, implementation distinctions, and operational interpretation |

The central business flow is:

`Business Data → Relational Model → Validated Transactions → Analytical Views → KPIs → Business Questions → Decision Support`

---

## Business Domain

The database represents a company selling products across four regions.

Customers belong to one of three commercial segments:

- **Consumer** represents individual buyers whose purchasing behavior can be compared against business customers.
- **Corporate** represents organizations with potentially larger and more frequent purchases.
- **Small Business** represents smaller commercial customers whose order patterns may differ from corporate accounts.

Products are organized into four categories:

- **Electronics** contains technology products such as laptops, routers, and security monitors.
- **Office Equipment** contains operational equipment such as printers and scanners.
- **Furniture** contains workplace products such as desks and ergonomic chairs.
- **Software** contains subscription or license-oriented products such as the analytics suite.

Orders have explicit operational states:

`Completed`, `Cancelled`, `Returned`, and `Pending`.

This distinction is important because revenue analysis should not automatically treat every order as realized revenue. The analytical views intentionally use completed transactions for recognized sales metrics while separate questions measure cancelled, returned, and pending activity.

---

## Relational Model

The SQL schema separates descriptive entities from transactional facts.

The principal relationships are:

`regions → customers`

`regions → sales_reps`

`categories → products`

`customers → orders`

`sales_reps → orders`

`orders → order_items`

`products → order_items`

An `orders` row describes the transaction itself. An `order_items` row describes what was purchased within that transaction.

This separation prevents a multi-product order from being represented as repeated customer or order attributes. It also allows product-level, category-level, customer-level, and order-level analysis without duplicating the core transactional entities.

The `order_items` table stores the effective unit price and unit cost used for the transaction. This is important because analytical history should not depend entirely on today's product master price.

---

## Database Integrity

The PostgreSQL implementation places business rules directly in the database where appropriate.

Primary keys identify every entity. Foreign keys prevent relationships from referencing nonexistent records. Unique constraints prevent duplicate category names, region names, and product names.

The product constraints enforce:

- A positive selling price.
- A non-negative cost.
- A cost that cannot exceed the selling price.

The order constraints enforce valid operational states and a discount between zero and one.

The order-item constraints require positive quantities and valid transaction economics.

The composite uniqueness rule on `(order_id, product_id)` prevents the same product from appearing twice in a single order in this particular model.

These constraints reduce the risk that downstream dashboards calculate KPIs from structurally invalid data.

---

## Revenue and Profitability Logic

Net revenue for a line item is:

`quantity × unit_price × (1 - discount_rate)`

Gross profit is:

`quantity × ((unit_price × (1 - discount_rate)) - unit_cost)`

Gross margin is:

`gross_profit / revenue × 100`

The calculations deliberately use transaction-level price and cost values. This prevents later changes to the product catalog from rewriting historical economics.

The SQL view `completed_order_lines` centralizes these calculations. It acts as an analytical foundation for many downstream questions.

---

## Python Implementation

The Python program builds the complete demonstration database using only the standard library.

Its `SCHEMA` definition creates tables, constraints, indexes, and analytical views. The `seed_database` function creates deterministic business data rather than relying on random values, which makes analytical results reproducible.

The `QUERIES` collection contains more than forty business questions. Each question is represented as a named query so the execution layer can run, display, and validate analytical results consistently.

The Python implementation specifically demonstrates:

- Relational schema creation through `sqlite3`.
- Foreign-key enforcement.
- Deterministic transaction generation.
- Revenue and profit calculations.
- Customer lifetime value.
- Product performance.
- Regional analysis.
- Segment analysis.
- Sales representative performance.
- Cancellation and return metrics.
- Window-function analysis.
- Running revenue.
- Moving averages.
- Revenue concentration.
- Data-quality checks.
- Query-plan inspection.
- CSV report generation.

The `validate_database` function performs database integrity checks before analytics are executed. This reflects an important analytics principle: reporting should not silently consume invalid source data.

The CSV export creates a customer-oriented analytical report that can be consumed by spreadsheet or reporting workflows.

---

## JavaScript Implementation

The JavaScript program uses an event-driven design instead of reproducing the Python database implementation.

Orders are represented as structured JavaScript objects containing customer attributes, transaction state, discount information, and line items.

The `assertValidOrder` function validates the transaction boundary. It rejects invalid quantities, unsupported states, invalid discounts, malformed dates, missing line items, and economically inconsistent prices and costs.

The analytics functions use JavaScript collections and `Map` structures for aggregation.

`aggregateBy` provides a reusable aggregation mechanism, while specialized functions calculate regional revenue, segment revenue, category revenue, product performance, customer lifetime value, and monthly revenue.

The event system adds a different architectural perspective. The `analytics:completed` event triggers KPI calculation and reporting after asynchronous ingestion completes.

The `ingestOrders` function uses a Promise to model an asynchronous data-ingestion boundary. A production implementation could replace that boundary with an API, message queue, stream, or database reader without changing the analytical functions.

This separation demonstrates why ingestion and analytics should not be tightly coupled.

---

## C++ Case Study

The C++ implementation treats analytics as a strongly typed business-performance engine.

The domain is represented by:

- `OrderStatus`
- `LineItem`
- `Order`
- `Metric`
- `AnalyticsEngine`

The `AnalyticsEngine` validates orders before calculations occur. Invalid quantities, prices, costs, discounts, or empty orders are rejected through exceptions.

The regional and category aggregations use `std::map`, providing deterministic ordered output. Customer aggregation uses `std::unordered_map`, emphasizing efficient hash-based lookup where sorted output is not required during the accumulation phase.

The monthly analysis uses an ordered map so that time-series output remains chronologically ordered.

The implementation also separates revenue and profit calculations into functions. This reduces the risk of applying different business formulas in different analytical reports.

The best-region calculation demonstrates a business selection query over aggregated metrics.

The invalid-product example shows a failure condition in which a cost greater than the selling price is rejected before the analytics engine can produce misleading profitability results.

For `N` orders with an average of `L` line items, the primary aggregation work is approximately `O(N × L)`, with ordered map operations adding logarithmic lookup costs relative to the number of groups.

---

## Java Enterprise Model

The Java implementation emphasizes explicit domain modeling.

Java records represent immutable business entities:

`Product`, `OrderItem`, `Customer`, `SalesOrder`, and analytical metric records.

Enums model controlled business vocabularies such as `OrderStatus` and `CustomerSegment`. This prevents arbitrary strings from silently becoming new business states.

Validation is embedded in record constructors. An invalid product cannot be constructed with a negative cost or a cost higher than its selling price. An invalid order cannot be constructed with an invalid discount or no line items.

`AnalyticsService` acts as the analytical service boundary. It receives validated domain objects and produces customer, category, regional, and monthly analytical views.

Java Streams are used where grouping and aggregation naturally match the business operation. `Collectors.groupingBy` creates grouped analytical structures, while stream reductions calculate revenue and profit.

The model uses `BigDecimal` instead of binary floating-point arithmetic for monetary calculations. This is an important enterprise design decision because financial values should not depend on floating-point representation artifacts.

The service also exposes a completion-rate calculation and an optional highest-value customer result.

---

## SQL Analytical Layer

The SQL implementation is the primary relational analytics artifact.

The schema is created under `business_analytics`, allowing the entire project to be isolated from unrelated database objects.

The SQL file contains:

- Normalized business tables.
- Primary and foreign keys.
- Unique constraints.
- Check constraints.
- Supporting indexes.
- Sample transactional data.
- Analytical views.
- Common table expressions.
- Window functions.
- Ranking.
- Contribution analysis.
- Data-quality checks.
- Transaction handling.
- Query-plan inspection.

The `completed_order_lines` view is especially important because it creates a reusable analytical grain: one row per completed order-product combination.

The `customer_lifetime_value` view aggregates that transactional foundation into customer-level metrics.

The `product_performance` view provides product-level revenue, units, and profit.

This layered design avoids writing every analytical question directly against the raw normalized tables.

---

## Time-Series Analytics

The project treats time as an analytical dimension rather than merely displaying dates.

Monthly revenue is calculated with `DATE_TRUNC`.

The monthly growth query uses `LAG` to compare the current month against the previous month.

The running-revenue query uses a windowed `SUM` to show cumulative performance.

The three-month moving-average query uses a window frame containing the current month and two preceding months.

These techniques answer different questions:

- Monthly revenue identifies the absolute performance of each period.
- Growth measures directional change.
- Running revenue measures cumulative business contribution.
- Moving averages reduce short-term volatility and expose broader trends.

A moving average should not be interpreted as actual revenue. It is a derived analytical signal.

---

## Customer Analytics

Customer analysis uses `customer_lifetime_value` as its main analytical view.

Lifetime revenue measures the cumulative value of completed transactions for a customer.

Lifetime profit adds an economic dimension that revenue alone cannot provide.

Repeat-customer analysis uses completed-order count rather than merely counting every order state. This avoids treating cancelled or pending activity as successful purchasing behavior.

The segment-average query compares each customer's lifetime value against the average value of the customer's own segment. This is more informative than comparing every customer against one global average because commercial segments can have substantially different purchasing patterns.

Revenue-contribution analysis calculates each customer's share of total realized revenue and can be extended into cumulative contribution analysis.

---

## Product Analytics

Product performance combines units, revenue, and gross profit.

A product can sell many units without generating the highest revenue. A high-priced product can generate substantial revenue while contributing fewer units. A product can also generate strong revenue with a relatively weak margin.

For that reason, the project does not treat revenue ranking as equivalent to product profitability ranking.

The product-margin query calculates:

`gross profit / revenue`

The low-margin analysis identifies products whose revenue contribution may conceal weak economics.

The product contribution analysis measures each product's share of total realized revenue.

The project also includes a query for products that have no completed sales. This is useful for identifying catalog items that exist operationally but are absent from realized sales activity.

---

## Regional and Segment Analytics

Regional analysis connects customers to their assigned regions and then aggregates completed sales.

The project calculates regional revenue, regional profit, regional share, average customer revenue, and category performance within each region.

The regional-category query is particularly useful because a category that performs well globally may not perform well uniformly across regions.

The best-category-per-region query uses a partitioned window ranking. Each region receives its own category ranking rather than competing against all categories across the entire business.

Segment analysis applies the same principle to Consumer, Corporate, and Small Business customers.

---

## Sales Representative Analytics

Sales representatives are directly connected to orders.

The project measures representative revenue, representative gross profit, and completed order count.

Revenue and order count should not be interpreted as interchangeable performance measures. A representative can have many small transactions while another handles fewer high-value transactions.

The data model allows representative results to be joined back to regions, customers, products, and time periods for deeper analysis.

---

## Order-State Analysis

The database distinguishes four order states.

**Completed** orders form the main realized-sales population.

**Cancelled** orders represent demand that did not become completed revenue.

**Returned** orders identify completed commercial activity that subsequently resulted in a return state.

**Pending** orders represent unresolved operational work.

This distinction supports operational questions that a simple sales-total query cannot answer.

Cancellation rate and return rate are calculated from the complete order population rather than from completed orders only. This makes the denominator meaningful for operational monitoring.

Pending-order queries identify transactions requiring attention.

Cancelled and returned order-value queries estimate the monetary scale associated with non-standard outcomes.

---

## Discount Analysis

Discounts are stored at the order level.

This allows the analytical layer to compare realized revenue across discount levels and customer segments.

The project calculates average discount by segment and revenue associated with each discount rate.

Discount analysis should not be interpreted as a causal pricing study. A higher discount level may be associated with larger transactions, strategic customers, clearance activity, or other business conditions.

The database can support deeper analysis by adding campaign, salesperson, channel, or pricing-policy dimensions.

---

## Ranking and Window Functions

Window functions provide analytical context without collapsing the underlying rows as ordinary aggregation does.

`RANK()` identifies product or regional leaders while preserving analytical grouping.

`DENSE_RANK()` provides compact ranking values where ties share the same rank.

`LAG()` compares a period against its previous period.

Windowed `SUM()` produces cumulative totals.

Windowed `AVG()` produces moving averages.

Partitioned ranking allows questions such as "best category within each region" instead of only asking "best category globally."

These operations are central to analytical SQL because they support comparisons between rows while retaining row-level context.

---

## Revenue Concentration

Total revenue can hide concentration risk.

The cumulative customer-contribution query orders customers by lifetime revenue and calculates their cumulative contribution to total revenue.

If a small number of customers account for a large share of revenue, the business may have significant customer concentration exposure.

The query does not label a particular concentration level as inherently good or bad. Interpretation depends on customer contracts, market structure, switching costs, account diversification, and business strategy.

The SQL structure provides the measurement needed for that interpretation.

---

## Data Quality

The project treats data quality as part of analytics rather than as a separate afterthought.

The Python implementation checks foreign-key integrity and product economics.

The SQL implementation checks for invalid order-item economics and orphaned order items.

The product model prevents negative or impossible economics through database constraints.

The customer analysis can identify customers without completed purchases.

The product analysis can identify catalog products without completed sales.

These checks are useful because analytical errors often originate from invalid source relationships rather than incorrect aggregation syntax.

---

## Performance Considerations

Indexes are created around common analytical access paths.

`idx_orders_date` supports date-based filtering.

`idx_orders_customer` supports customer-to-order access.

`idx_orders_status_date` supports common operational and time-based filtering.

`idx_order_items_product` supports product-level aggregation and joins.

`idx_customers_segment_region` supports segment and regional access patterns.

Indexes have a write and storage cost. Creating an index for every possible analytical query is not a sound strategy. Indexes should be driven by query frequency, cardinality, selectivity, and actual execution plans.

The SQL script ends with `EXPLAIN (ANALYZE, BUFFERS)` for a common completed-order time filter. In PostgreSQL, this makes the optimizer's chosen execution path visible and helps distinguish a theoretically useful index from an index that actually improves execution.

---

## Transactional Integrity

The SQL implementation demonstrates a transaction boundary using `BEGIN` and `COMMIT`.

Transactions matter when several database changes must succeed or fail as one logical unit.

Analytics databases frequently contain data-loading workflows where partial updates can produce misleading reports. Transaction boundaries reduce the risk of exposing intermediate states.

The example transaction is intentionally harmless and preserves valid business data while demonstrating the database transaction mechanism.

---

## Practical Analytical Questions Covered

The project answers substantially more than forty questions, including:

- Total realized revenue.
- Total gross profit.
- Gross margin.
- Completed order count.
- Average order value.
- Revenue by month.
- Monthly growth.
- Running revenue.
- Moving-average revenue.
- Revenue by region.
- Profit by region.
- Revenue by segment.
- Profit by segment.
- Revenue by category.
- Units by category.
- Product revenue ranking.
- Product unit ranking.
- Product margin.
- Customer lifetime value.
- Repeat customers.
- Customers above segment average.
- Customer revenue contribution.
- Sales representative revenue.
- Sales representative profit.
- Sales representative order count.
- Order-status distribution.
- Cancellation rate.
- Return rate.
- Pending orders.
- Cancelled order value.
- Returned order value.
- Average units per order.
- High-value orders.
- Customer-category revenue.
- Regional-category performance.
- Best category by region.
- Average discount by segment.
- Revenue by discount level.
- Order-value bands.
- Customer revenue concentration.
- Low-margin products.
- Products without completed sales.
- Customers without completed purchases.
- Average customer revenue by region.
- Segment revenue ranking.
- Highest-revenue month.
- Highest-profit product.
- Highest-margin product.
- Regional revenue share.
- Monthly category mix.
- Customer acquisition cohort analysis.
- Completed orders by segment and month.
- Customers above a revenue threshold.
- Order-level profitability.
- Invalid transaction economics.
- Orphan order-item detection.

The questions are intentionally different in analytical purpose. Some measure scale, some measure efficiency, some compare groups, some measure change over time, and others validate the data itself.

---

## Important Analytical Distinctions

Revenue is not the same as profit. A product can generate high sales while producing relatively weak gross profit.

Order count is not the same as customer value. Many low-value orders can produce less revenue than a small number of high-value transactions.

Completed revenue is not the same as order demand. Cancelled, returned, and pending transactions provide separate operational information.

A global category leader is not necessarily the category leader in every region.

A customer with high revenue is not automatically the most profitable customer.

A higher discount rate is not automatically harmful or beneficial because the effect depends on transaction volume, price, cost, and customer behavior.

A monthly revenue increase does not by itself establish a long-term trend. The moving-average calculation provides another perspective on the time series.

---

## Common Analytical Failure Modes

A frequent error is summing all orders without filtering operational state. This can cause pending, cancelled, or returned activity to be interpreted as realized sales.

Another failure is calculating historical revenue from the current product master price. Transaction-level pricing should be preserved when historical reporting matters.

Joining multiple one-to-many relationships without controlling aggregation grain can multiply rows and inflate revenue. The SQL views avoid this by establishing a deliberate order-line analytical grain.

Using revenue as a proxy for profitability can produce misleading product rankings.

Ignoring null or zero-denominator conditions can create invalid ratios or runtime errors.

Creating indexes without examining real execution plans can increase database maintenance cost without improving analytical performance.

Relying exclusively on application validation can leave alternate data-ingestion paths capable of inserting invalid records. Critical relational rules should be enforced at the database layer when appropriate.

---

## Implementation Boundaries

The Python implementation prioritizes reproducible execution and report export.

The JavaScript implementation emphasizes event-driven and asynchronous application behavior.

The C++ implementation emphasizes strongly typed data structures, deterministic aggregation, and computational characteristics.

The Java implementation emphasizes enterprise domain modeling, immutable data structures, explicit business states, and service-oriented analytics.

The PostgreSQL implementation is the most complete relational representation. It provides the database constraints, relationships, indexes, views, transactions, and analytical SQL that form the project's core database layer.

These implementations intentionally do not duplicate one another line for line. Each language demonstrates how the same business analytics problem can be approached according to the strengths and responsibilities of that environment.

---

## Production Considerations

A production implementation would normally separate operational transactions from analytical workloads when scale and reporting concurrency require it.

Historical pricing, taxation, returns, refunds, currency conversion, sales channels, payment states, and shipment states may require additional fact tables and dimensions.

Large datasets would benefit from appropriate partitioning, materialized views, incremental aggregation, query monitoring, statistics maintenance, and workload-specific indexes.

Financial reporting would require explicit currency and accounting rules.

Customer analytics would require appropriate privacy controls and access policies.

Analytical definitions should be documented as governed metrics so that "revenue," "completed order," "gross profit," and "customer lifetime value" have consistent meanings across dashboards and teams.

The central design principle remains the same: reliable business analytics begins with a well-defined data model, enforces valid states, establishes the correct analytical grain, and only then performs aggregation and interpretation.
