# SQL Analytics Patterns

## Scope

This implementation set focuses on five closely related analytical patterns:

- **Top-N analysis** ranks entities such as products, customers, or channels by a measurable metric while making tie behavior explicit.
- **Cohort preparation** assigns users to stable groups based on a defining event such as signup, acquisition, activation, or first purchase.
- **Retention calculations** measure continued activity for members of each cohort across elapsed periods.
- **Funnel queries** measure progression through an ordered sequence of behavioral stages using distinct entities rather than raw event volume.
- **Segmentation** converts user-level behavioral and business measures into interpretable groups that can be compared across dimensions such as acquisition channel or country.

The six deliverables approach these patterns from different technical perspectives. Python provides an executable analytical simulation, JavaScript models event-driven processing, C++ implements a memory-oriented analytical engine, Java models an enterprise service with explicit domain types, and PostgreSQL demonstrates the database-native form of the patterns.

## Analytical Data Model

The examples use a fact-and-dimension structure.

`users` represents relatively stable user attributes such as signup date, country, and acquisition channel. `events` represents behavioral facts that occur at particular timestamps. `products` represents product attributes.

This separation is important because analytical metrics should generally be calculated from facts rather than stored as mutable attributes on dimension records.

For example, revenue should be derived from purchase events. Storing a permanently calculated revenue value on `products` would make historical correction, duplicate-event handling, and time-based analysis more difficult.

The analytical flow can therefore be represented as:

`raw events + dimensions -> prepared analytical rows -> entity-level metrics -> ranking/cohorts/funnels/segments -> aggregate reporting`

SQL CTEs are especially useful for expressing these intermediate transformations without creating unnecessary permanent tables.

## Top-N Analysis

Top-N analysis answers questions such as:

- Which products generated the most revenue?
- Which acquisition channels produced the largest customer base?
- Which customer segments have the highest value?
- Which categories contain the strongest-performing entities?

The central SQL mechanism is a window function.

The SQL implementation demonstrates `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()` together because they answer different questions.

`ROW_NUMBER()` assigns every row a unique position even when metrics tie. This is useful when exactly three physical rows must be selected.

`RANK()` gives tied rows the same rank and leaves gaps after a tie.

`DENSE_RANK()` gives tied rows the same rank without gaps. If two products are tied at rank 2, the next distinct value is rank 3.

The PostgreSQL example uses `DENSE_RANK()` for a Top-N report so equal revenue values are not arbitrarily separated.

The Python, JavaScript, C++, and Java implementations reproduce the same analytical distinction with explicit ordering and rank state rather than relying on a database window engine.

A critical design decision is whether "Top 3" means:

- exactly three rows, or
- every entity whose rank is at most three.

Those definitions produce different results when ties occur.

### Tie behavior

Consider revenues of:

`18,200`, `15,700`, `15,700`, `11,900`

A row-position interpretation returns three entities. A dense-rank interpretation also returns three entities because both tied products occupy rank 2.

If three entities tie for second place, a dense-rank Top-3 query can return more than three rows. That is not an error. It is a consequence of the selected ranking semantics.

## Cohort Preparation

A cohort is a group whose members share a defining temporal characteristic.

The examples use signup month:

`date_trunc('month', signup_at)`

The resulting value is retained as `cohort_month`.

This preparation step should occur before retention calculation. A retention query becomes difficult to reason about when every downstream expression independently reconstructs a user's cohort.

The cohort preparation in the Python implementation produces a user-level row containing:

- user identifier
- signup date
- cohort month
- country
- acquisition channel

The Java implementation models the same relationship with `YearMonth`, making the cohort period an explicit domain value rather than an arbitrary string.

The PostgreSQL query creates a `cohort_users` CTE. This is intentionally separate from the activity calculation because signup information describes the user's cohort while events describe later behavior.

## Retention Calculations

Retention asks whether members of an original cohort remain active after the cohort's starting period.

The implementation uses monthly periods.

A user who signs up in January and performs a qualifying activity in February has:

`period_number = 1`

A user active again in March has:

`period_number = 2`

The denominator is the size of the original cohort. It is not the size of the previous month's active population.

The SQL calculation therefore separates:

- cohort size
- distinct active users
- elapsed period

The critical operation is deduplication.

A user may generate many activity events during a month. Retention should normally count that user once:

`COUNT(DISTINCT user_id)`

not once for every event.

The examples treat login, product viewing, cart activity, and purchase as retention activity. The definition is intentionally explicit because "active user" has no universal meaning. A business may instead define activity as a completed transaction, meaningful feature usage, or another domain-specific event.

### Cohort retention interpretation

If a cohort contains 100 users and 42 unique users are active during period 1:

`retention = 42 / 100 = 42%`

The result does not mean that each retained user performed exactly one action. It means that 42 distinct members of the original cohort satisfied the activity definition during the measurement period.

## Funnel Queries

A funnel represents an ordered progression.

The example uses:

`signup -> product_view -> cart -> checkout -> purchase`

Each stage counts unique users who reached that event.

The use of unique users is important. Suppose one user views a product ten times. Ten event rows do not represent ten customers reaching the product-view stage.

The PostgreSQL implementation therefore uses filtered distinct counts:

`COUNT(DISTINCT user_id) FILTER (WHERE event_name = 'view_product')`

The next-stage conversion is calculated against the immediately preceding stage.

If 1,000 users view a product and 250 add an item to a cart:

`250 / 1,000 = 25%`

This is different from overall conversion, which might compare purchasers with all signups.

### Funnel failure modes

A funnel can be distorted by several data problems:

- repeated events can inflate raw event counts;
- missing events can make a user appear to skip a stage;
- events arriving out of order can create impossible-looking journeys;
- duplicate ingestion can inflate activity;
- different stage definitions can make comparisons between reports invalid;
- using event counts instead of distinct users can turn a user funnel into an event-volume report.

The examples address the first issue by using sets in the application implementations and `COUNT(DISTINCT ...)` in PostgreSQL.

## Segmentation

Segmentation groups entities according to explicit analytical rules.

The example creates four behavioral segments:

| Segment | Rule |
| --- | --- |
| `high_value` | At least two purchases or revenue of at least 300 |
| `buyer` | At least one purchase but not high value |
| `engaged_non_buyer` | At least three qualifying activity events without a purchase |
| `low_activity` | Does not meet the other thresholds |

The rules are evaluated after creating user-level metrics.

This order matters. Segmenting individual event rows would produce multiple classifications for the same user and make the final result difficult to interpret.

The SQL implementation first calculates:

- activity events
- purchase count
- purchase revenue

It then applies a `CASE` expression.

The Python, JavaScript, C++, and Java implementations use the same business rule but represent the intermediate metrics using language-specific structures.

## Segment Analysis Versus Cohort Analysis

Cohorts and segments can both group users, but they answer different questions.

A cohort normally has a temporal or acquisition definition:

`users who signed up in January`

A segment normally has a behavioral or business definition:

`users with at least one purchase`

A cohort can contain multiple segments, and a segment can contain users from multiple cohorts.

This distinction makes combined analysis useful. For example, retention can be compared between high-value and low-activity users within the same signup cohort.

## Python Implementation

The Python program is an executable simulation of the analytical workflow.

The `Event`, `User`, and `ProductSale` data classes provide explicit structures for facts and dimensions. `build_events()` creates a realistic sequence of signup, product, cart, checkout, purchase, and login events.

`top_n_products()` demonstrates dense ranking and explicitly rejects a non-positive Top-N value.

`prepare_cohort_rows()` establishes the cohort dimension before retention is calculated.

`retention_by_month()` maintains distinct user-period activity and uses the original cohort size as the denominator.

`funnel_analysis()` tracks the set of event types observed for each user, allowing every funnel stage to count each user at most once.

`segment_users()` creates auditable behavioral rules based on activity, purchase count, and revenue.

The program also includes explicit handling for an empty Top-N dataset and zero-denominator conversion.

## JavaScript Implementation

The JavaScript program takes a complementary event-driven approach.

`AnalyticsEvent` validates event construction and freezes event properties so an event's captured attributes cannot be accidentally mutated after creation.

`Map` and `Set` are used heavily because they naturally represent analytical relationships:

- `Map` associates users with metrics;
- `Set` removes duplicate stage or activity observations;
- grouped `Map` instances represent cohorts and segment populations.

The asynchronous `AnalyticsPipeline` demonstrates how purchase events could feed multiple analytical handlers. One handler aggregates purchase revenue while another identifies high-value purchases.

This event-driven perspective is useful when analytics are produced from streaming application events rather than only from periodic database queries.

The file still calculates Top-N, cohorts, retention, funnels, and segments locally so the analytical rules remain observable.

## C++ Case Study

The C++ implementation represents a memory-oriented repository-style analytics engine for a product analytics workload.

The system separates:

- `User` dimension data;
- `Event` fact data;
- `Product` metrics;
- `UserMetrics` derived measures;
- `FunnelRow` analytical output.

`topNProducts()` uses sorting followed by dense-rank logic.

`buildRetentionActivity()` uses nested maps and sets. The set at the user-period level is particularly important because it guarantees that repeated activity does not multiply the retention count.

`calculateFunnel()` stores event types in a set per user. A user therefore contributes at most one unit to any funnel stage.

`calculateMetrics()` performs the user-level aggregation needed by segmentation.

The program also demonstrates an explicit exception path for invalid Top-N input.

For very large event volumes, materializing every event in memory would become expensive. Database-side aggregation, streaming processing, columnar analytical systems, or partitioned processing would normally be considered before using this in-memory architecture at production scale.

## Java Implementation

The Java program models the analytical domain with explicit types.

`User`, `Event`, `Product`, `FunnelRow`, and `SegmentMetrics` are records, which provide immutable value-oriented representations of analytical data.

`EventType` is an enum, preventing arbitrary strings from silently creating unsupported event types inside the Java application.

`AnalyticsService` contains the analytical operations.

`prepareCohorts()` groups users by `YearMonth`.

`retention()` first creates cohort membership and then builds distinct active-user sets for each cohort and period.

`funnel()` represents stages through the `FunnelStage` record and counts users against event-type sets.

`calculateMetrics()` uses mutable builders internally and returns immutable `SegmentMetrics` values.

`classifySegments()` applies explicit business rules after the metrics have been computed.

This structure keeps domain data, derived measures, and classification decisions separate, which is useful when analytics rules must be tested or changed independently.

## SQL Data Model

The PostgreSQL implementation is the database-native version of the analytical workflow.

The schema contains:

| Table | Analytical role |
| --- | --- |
| `users` | User dimensions and cohort attributes |
| `products` | Product dimensions |
| `events` | Behavioral and transaction facts |

The foreign key from `events.user_id` to `users.user_id` prevents activity from referencing nonexistent users.

The event `CHECK` constraint restricts the supported event vocabulary.

The amount constraints prevent negative values and ensure that non-purchase events cannot silently carry revenue.

The `idx_events_user_time` index supports queries that retrieve activity for individual users in chronological order.

The `idx_events_name_time` index supports filtering by event type and time.

The signup index supports cohort-oriented time filtering.

## SQL CTE Structure

The SQL examples deliberately use CTEs to create analytical stages.

A cohort query can be understood as:

`cohort_users -> activity -> cohort_sizes -> retained -> retention_rate`

A segmentation query follows:

`user_metrics -> segmented -> segment_summary`

This structure makes intermediate data definitions visible and reduces the risk of applying business rules at the wrong granularity.

CTEs are especially useful when an analytical query contains multiple transformations that should be logically separate but do not justify permanent staging tables.

## Window Functions

Window functions calculate values across related rows without collapsing the rows into a single aggregate result.

The example compares:

`ROW_NUMBER() OVER (ORDER BY revenue DESC)`

`RANK() OVER (ORDER BY revenue DESC)`

`DENSE_RANK() OVER (ORDER BY revenue DESC)`

This distinction is fundamental to Top-N analytics.

A normal aggregate such as `SUM()` collapses groups. A window function can calculate a rank while preserving each product row.

Window functions are also useful for adjacent-stage comparisons, period-over-period analysis, running totals, percentile calculations, and ordered behavioral analysis.

## Database-Level Integrity

The SQL schema does not depend exclusively on application code.

The database rejects:

- events referencing nonexistent users;
- unsupported event names;
- negative monetary values;
- positive amounts attached to non-purchase events.

These rules protect analytical correctness at the storage boundary.

This matters because analytical databases often receive data from multiple ingestion paths. If only one application validates a rule, another ingestion process can bypass that validation.

Database constraints therefore provide a final integrity boundary.

## Performance Considerations

Analytical queries can become expensive when event tables grow rapidly.

The most important optimization decisions in these examples are based on access patterns rather than adding indexes indiscriminately.

The user/time event index helps queries that repeatedly inspect one user's history.

The event-name/time index helps event-specific analysis such as purchase or signup filtering.

For very large datasets, additional strategies may include partitioning event data by time, maintaining summary tables, incremental materialization, column-oriented storage, pre-aggregated facts, or workload-specific indexes.

`COUNT(DISTINCT user_id)` can be substantially more expensive than a simple count because the database must eliminate duplicate identities. The cost is justified when unique-user semantics are required, but it should not be replaced with a simple count merely to make a query faster.

## Analytical Correctness

The most important correctness rule across these patterns is choosing the right grain.

Examples:

- Top-N normally operates at an entity grain such as product or customer.
- Cohort preparation operates at user grain.
- Retention operates at user-period grain before cohort aggregation.
- Funnel measurement operates at user-stage grain before stage aggregation.
- Segmentation normally operates at user grain after behavioral metrics have been calculated.

A common analytical defect occurs when a query joins two event-level datasets without reducing either side first. Such a join can multiply rows and inflate counts.

The implementations avoid this problem by creating user-level or user-period-level structures before producing final aggregates.

## Edge Cases

Top-N analysis must define tie behavior and what happens when the requested N is zero or larger than the available population.

Retention must define the qualifying activity events, the cohort boundary, the time period, and the denominator.

Funnels must define whether a user needs to reach stages in chronological order or merely possess evidence of each event type.

Segmentation must define precedence when multiple rules match the same user. In the supplied rule set, `high_value` is checked before `buyer`, because a high-value buyer must not be classified as an ordinary buyer.

Zero denominators must be handled explicitly. A conversion percentage is undefined when the previous funnel stage contains zero users. The implementations return zero rather than raising a division error.

Missing user records must not silently become valid analytical entities. The SQL foreign key prevents such event rows from entering the database.

## Common Analytical Mistakes

Counting event rows instead of distinct users changes the meaning of retention and funnels.

Using the previous month's active users as the retention denominator produces a rolling activity ratio rather than classic cohort retention.

Using `ROW_NUMBER()` when the business expects tied entities to share a rank can arbitrarily exclude valid Top-N results.

Assigning segments before aggregating user behavior can produce contradictory classifications for the same person.

Mixing cohort definitions between reports makes retention comparisons unreliable. A cohort based on signup month is not equivalent to one based on first purchase month.

Joining raw event tables without controlling the grain can multiply facts and inflate revenue, counts, and conversion rates.

## Practical Interpretation

These patterns are most useful when treated as complementary analytical building blocks.

Top-N identifies concentration and leaders.

Cohort preparation creates a stable analytical population.

Retention measures persistence within that population.

Funnels identify where users are lost during an ordered process.

Segmentation explains behavioral differences between user groups.

Together they allow a business question to move from aggregate performance toward behavioral diagnosis without treating every analytical problem as the same type of query.

The central design principle is to make the entity grain, time grain, denominator, ranking semantics, and business rules explicit before calculating the final metric.
