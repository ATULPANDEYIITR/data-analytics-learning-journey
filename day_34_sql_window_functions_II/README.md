# SQL Window Functions II

## Scope

This module focuses on analytical SQL window functions that operate across related rows without collapsing those rows into a single aggregate result.

The implementations concentrate on:

- `LAG`
- `LEAD`
- `FIRST_VALUE`
- `LAST_VALUE`
- running totals
- moving averages
- partitions
- ordering
- explicit window frames
- row-relative comparisons
- time-series gaps
- analytical business rules

The examples use daily revenue for multiple regions and products. This gives the window functions a meaningful analytical setting: revenue can be compared with prior and future observations, cumulative performance can be calculated, and short-term fluctuations can be smoothed without losing the original daily records.

## Why Window Functions Matter

A grouped aggregate such as `SUM(revenue) GROUP BY region` changes the shape of a result by reducing many rows into fewer rows.

A window function behaves differently. It calculates an analytical value while retaining the underlying row.

For example, a daily revenue table might contain:

- 2026-09-01: 1200
- 2026-09-02: 1350
- 2026-09-03: 1280

A grouped total can produce one value for the entire group. `LAG` can instead attach the previous day's revenue to each daily row:

| Date | Revenue | Previous Revenue |
|---|---:|---:|
| 2026-09-01 | 1200 | NULL |
| 2026-09-02 | 1350 | 1200 |
| 2026-09-03 | 1280 | 1350 |

The original observations remain available, which makes window functions particularly useful for time-series analysis, change detection, cumulative metrics, and comparative reporting.

## Core Window Structure

A typical window expression has the form:

`FUNCTION(value) OVER (PARTITION BY grouping_columns ORDER BY ordering_columns frame_definition)`

Each part has a distinct responsibility.

`PARTITION BY` determines which rows belong to the same analytical group.

`ORDER BY` establishes the sequence in which relative positions are interpreted.

The frame determines which rows are visible to frame-sensitive functions such as aggregate windows and `LAST_VALUE`.

For example:

`SUM(revenue) OVER (PARTITION BY region, product ORDER BY sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`

means that each region/product history receives an independent cumulative total, ordered by date, beginning at the first row and ending at the current row.

## LAG

`LAG` retrieves a value from an earlier row in the ordered window.

A common expression is:

`LAG(revenue) OVER (PARTITION BY region, product ORDER BY sale_date)`

For the first row in each partition, there is no previous row, so the result is normally `NULL`.

This makes `LAG` useful for:

- day-over-day revenue changes
- month-over-month comparisons
- detecting sudden increases or decreases
- calculating percentage changes
- identifying changes in state
- comparing an event with the previous event

The Python implementation demonstrates `LAG` through SQLite and calculates both absolute and percentage changes.

The JavaScript implementation models the same row-relative behavior with partition arrays and an explicit `lag()` function.

The C++ implementation represents the absence of a previous row using `std::optional<double>`, which is a useful distinction from treating a missing value as zero.

### Offset

`LAG` can use an offset greater than one.

`LAG(revenue, 2)`

asks for the revenue two ordered rows earlier.

This is different from asking for a date two calendar days earlier. Window offsets operate on rows. If a dataset has missing dates, the second previous row might represent a much larger calendar interval.

## LEAD

`LEAD` is the forward-looking counterpart to `LAG`.

`LEAD(revenue) OVER (PARTITION BY region, product ORDER BY sale_date)`

retrieves the revenue from the next ordered row.

The final row of each partition has no following row and therefore receives `NULL` unless a default value is explicitly supplied.

`LEAD` is useful for:

- examining what happened immediately after an event
- calculating the change from the current observation to the next observation
- identifying intervals between events
- finding the next state transition
- comparing a current value with its future observation in historical analysis

The JavaScript implementation combines `LAG` and `LEAD` to classify a local sequence as rising, falling, or potentially turning.

## LAG and LEAD Together

The two functions allow a row to see both sides of its position in an ordered sequence.

For a sequence such as:

`100, 120, 140, 130, 110`

the middle value `140` has:

- previous value: `120`
- current value: `140`
- next value: `130`

That information can support turning-point detection.

A useful distinction is that this type of analysis is appropriate for historical datasets because `LEAD` requires future data. It should not be interpreted as a real-time prediction mechanism.

A real-time dashboard cannot use tomorrow's revenue simply because the historical SQL query can.

## FIRST_VALUE

`FIRST_VALUE` retrieves a value from the first row visible to the function's window frame.

For a partition ordered by `sale_date`, this expression:

`FIRST_VALUE(revenue) OVER (PARTITION BY region, product ORDER BY sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)`

makes the initial revenue available on every row of the partition.

This supports analyses such as:

- current revenue versus initial revenue
- growth from the beginning of a measurement period
- baseline comparisons
- identifying the starting state of an entity

The first value is different from a grouped minimum. The first row is determined by the window ordering, while a minimum identifies the smallest value regardless of its position.

## LAST_VALUE and Window Frames

`LAST_VALUE` requires particular care.

A common assumption is that:

`LAST_VALUE(revenue) OVER (PARTITION BY region, product ORDER BY sale_date)`

always means "the final revenue in the partition."

The result depends on the window frame.

When the frame ends at the current row, the last row visible to the function is the current row. Consequently, `LAST_VALUE` can return the current revenue rather than the final revenue of the entire partition.

To request the final value from the complete partition, an explicit frame can be used:

`LAST_VALUE(revenue) OVER (PARTITION BY region, product ORDER BY sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)`

The phrase `UNBOUNDED FOLLOWING` is important because it extends the frame through the end of the partition.

The Python, JavaScript, and C++ artifacts deliberately expose this distinction because it is one of the most important practical details when using `LAST_VALUE`.

## Running Totals

A running total accumulates values from the beginning of a partition through the current row.

The essential expression is:

`SUM(revenue) OVER (PARTITION BY region, product ORDER BY sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`

For revenue values `100`, `120`, and `80`, the running totals are:

| Date Position | Revenue | Running Total |
|---|---:|---:|
| First | 100 | 100 |
| Second | 120 | 220 |
| Third | 80 | 300 |

Unlike a normal grouped `SUM`, the windowed sum retains the daily records.

Running totals are useful for:

- cumulative revenue
- cumulative costs
- cumulative units sold
- cumulative operational events
- progress against a target
- year-to-date or period-to-date measurements

The C++ case study maintains the cumulative value incrementally as it processes each sorted partition. That avoids repeatedly summing all previous rows.

## Moving Averages

A moving average evaluates a bounded window around the current row.

The Python implementation uses:

`AVG(revenue) OVER (PARTITION BY region, product ORDER BY sale_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`

This creates a three-row trailing window.

For values:

`100, 120, 80, 140`

the moving averages are:

| Revenue | Three-row frame | Average |
|---:|---|---:|
| 100 | 100 | 100.00 |
| 120 | 100, 120 | 110.00 |
| 80 | 100, 120, 80 | 100.00 |
| 140 | 120, 80, 140 | 113.33 |

The first rows use fewer observations because earlier rows do not exist.

This is preferable to silently inserting zeroes. A missing historical observation and an actual revenue value of zero have different meanings.

## Trailing Versus Centered Windows

A trailing window contains the current row and earlier observations.

`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`

is a trailing three-row window.

A centered window can contain observations before and after the current row:

`ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING`

Centered windows can be useful for retrospective analysis and smoothing historical datasets.

They are not suitable for a real-time metric that must be calculated using only information available at the current instant because the following row may not yet exist.

The Python implementation demonstrates a centered average specifically to make this distinction explicit.

## PARTITION BY Is Analytical Isolation

Suppose revenue exists for both North and South.

Without:

`PARTITION BY region`

the previous row for a North observation could be a South observation after the global ordering is applied.

That would create an incorrect comparison.

With:

`PARTITION BY region, product`

each region/product combination receives its own independent history.

The examples therefore use both region and product as partition keys.

This distinction is fundamental:

- `PARTITION BY` determines which rows are analytically grouped.
- `ORDER BY` determines their sequence inside each group.
- the frame determines which rows are visible for frame-sensitive operations.

## Row Order Is Not the Same as Calendar Distance

`LAG` and `LEAD` are based on row positions.

The dataset intentionally contains missing dates for South/Security.

If the stored observations are:

- September 1
- September 2
- September 4
- September 5
- September 7

then `LAG` on September 4 returns September 2.

It does not return a synthetic September 3 record.

This matters when analysts describe a calculation as "previous day." If the source data can contain missing dates, the query should distinguish between:

- previous recorded observation
- previous calendar day

The Python, JavaScript, and C++ implementations expose the calendar gap so that this distinction can be tested rather than assumed.

## Combining Window Operations

Complex analytical calculations often require multiple logical stages.

For example, a running total can be calculated first:

`SUM(revenue) OVER (...) AS running_revenue`

A second analytical operation can then compare the resulting running total with its previous value.

A common SQL approach is to use a CTE:

`WITH cumulative AS (...) SELECT LAG(running_revenue) OVER (...) FROM cumulative`

The CTE provides a logical intermediate result.

This is important because window functions are not simply arbitrary nested scalar functions. Separating analytical stages makes the calculation easier to reason about and avoids unsupported or ambiguous nesting patterns.

## Python Implementation

The Python program uses SQLite through the standard-library `sqlite3` module.

It creates an in-memory relational database containing:

- `sale_id`
- `sale_date`
- `region`
- `product`
- `revenue`

The script demonstrates actual SQL rather than manually pretending that Python lists are SQL tables.

Its `LAG` example computes previous revenue and the absolute difference from that previous observation.

Its `LEAD` example shows both a nullable next value and a supplied default value.

Its `FIRST_VALUE` query uses a full partition frame to make the starting observation explicit.

Its `LAST_VALUE` query intentionally displays both a current-row frame and a full-partition frame. This exposes the common `LAST_VALUE` frame error directly in executable output.

Its running-total query uses an unbounded preceding frame ending at the current row.

Its moving-average query uses two preceding rows plus the current row.

The percentage-change query uses `NULLIF` to avoid division by zero.

The missing-date query compares the current date with the date returned by `LAG`, demonstrating that row-relative navigation does not automatically imply calendar continuity.

The script also creates an index on `(region, product, sale_date)` and inspects the execution plan. Indexing does not guarantee that all window processing becomes free, but matching common partition and ordering columns can be useful when designing larger analytical workloads.

## JavaScript Implementation

The JavaScript file takes a different approach.

Instead of translating the SQLite queries, it models the analytical behavior as a Node.js event-processing service.

`partitionAndSort()` uses a `Map` to construct independent region/product histories.

The `lag()` and `lead()` functions operate on explicit row positions.

`firstValue()` and `lastValue()` demonstrate full-partition boundary values.

`runningTotal()` and `movingAverage()` represent cumulative and bounded-frame calculations.

The report builder creates a richer analytical object for each observation. Each result can contain:

- current revenue
- previous revenue
- next revenue
- first revenue
- final revenue
- running revenue
- three-row moving average
- calendar gap
- percentage change

The `WindowAnalyticsService` extends Node's `EventEmitter`.

The service emits `reportReady` when the analytical report has been created and emits `changeDetected` when the resulting percentage-change policy identifies a large movement.

This separation reflects an application architecture in which calculation and event handling are separate concerns.

The JavaScript implementation also validates input and uses `Promise`-based asynchronous execution so that the analytical stage could later be connected to database or service I/O without redesigning the event interface.

## C++ Case Study

The C++ program models a revenue-governance engine.

The input contains regional product histories. The system first validates every sale, partitions the records by region and product, and sorts each partition by date.

The window calculation then produces a `WindowRow` containing the original sale plus analytical fields.

`std::optional<double>` represents values that SQL would normally return as `NULL`, particularly the missing previous value on the first row and missing next value on the final row.

The running total is maintained incrementally during partition processing.

The moving average uses a bounded three-row frame.

The percentage-change calculation checks for a missing baseline and a zero baseline before performing division.

The calendar-gap calculation makes missing dates visible.

The program also contains a dedicated demonstration of `LAST_VALUE` frame semantics. It shows how a current-row frame differs from a full-partition frame.

The policy layer identifies changes whose absolute percentage exceeds a configured threshold. This demonstrates the distinction between a window calculation and the business rule that consumes its result.

## Window Frames

A window frame defines a subset of the ordered partition available to a frame-sensitive operation.

Common boundaries used in this module include:

`UNBOUNDED PRECEDING`

The frame begins at the first row of the partition.

`CURRENT ROW`

The frame includes the current position.

`UNBOUNDED FOLLOWING`

The frame extends through the final row of the partition.

`2 PRECEDING`

The frame reaches two rows before the current row.

For a trailing three-row calculation:

`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`

the maximum frame size is three rows.

At the beginning of a partition, the actual frame is smaller because nonexistent rows cannot be included.

## Common Mistakes

### Forgetting the partition

A query that compares all regions together may produce valid SQL but invalid business logic.

The fix is to identify the entity whose history should be independent and include it in `PARTITION BY`.

### Assuming LAG means previous calendar day

`LAG` means previous ordered row.

Missing dates, late-arriving events, filtered rows, and sparse event streams can make the previous row several calendar days away.

### Misreading LAST_VALUE

A default or implicit frame can cause `LAST_VALUE` to return the current row.

When the objective is the final value of the entire ordered partition, make the full frame explicit.

### Treating NULL as zero

The absence of a previous row is not the same as a previous revenue of zero.

Replacing `NULL` with zero should be an intentional business rule rather than an automatic cleanup step.

### Dividing by a zero baseline

Percentage-change formulas can fail or produce misleading results when the previous value is zero.

The Python implementation uses `NULLIF` to prevent division by zero, while the JavaScript and C++ versions explicitly test the baseline.

### Ignoring ties in ORDER BY

A window ordered by a non-unique column may have multiple rows at the same ordering position.

For deterministic analytical results, use an ordering expression that uniquely establishes the intended sequence when the source can contain ties.

## Edge Cases

The first row of every partition has no previous row.

The final row of every partition has no next row.

A partition may contain only one row. In that case, `LAG` and `LEAD` are both absent, while `FIRST_VALUE` and full-partition `LAST_VALUE` refer to the same row.

An empty query result contains no window rows. It should not automatically be interpreted as a metric equal to zero.

A previous revenue of zero requires special treatment for percentage growth.

Missing dates require a distinction between row sequence and calendar sequence.

A moving average at the beginning of a partition has fewer observations than its nominal window width.

## Performance Considerations

Window functions generally require the database to organize rows according to the partitioning and ordering requirements.

For a dataset with `n` rows, sorting can become an important cost when an appropriate access path is unavailable.

The C++ case study explicitly sorts each partition and then performs analytical processing in linear time after sorting.

The running total is calculated incrementally rather than recomputing all preceding rows for every result.

Moving averages have different implementation choices. A simple bounded loop is easy to understand, while production-scale implementations can use incremental window state when the frame and operation permit it.

Database indexes should be designed around real query patterns rather than created mechanically. An index aligned with partition and ordering columns can sometimes reduce sorting or improve access, but the database optimizer, cardinality, storage engine, and workload determine the actual benefit.

## Historical Analysis Versus Real-Time Analysis

`LEAD` and centered windows are naturally suited to historical analysis because they can use future rows relative to the current observation.

A production real-time system must be careful not to expose information that was unavailable when an event occurred.

A trailing moving average is generally more appropriate for online monitoring because it only depends on current and earlier observations.

This distinction is important in forecasting evaluation, anomaly detection, operational monitoring, and financial time-series analysis.

## Security and Data Integrity

Window functions themselves do not prevent unsafe SQL construction.

Application code should use parameterized queries when user-controlled values are incorporated into SQL. The Python implementation demonstrates this with a bound revenue threshold rather than concatenating a value into a query string.

Data validation should also occur before analytical calculations.

Negative revenue may be legitimate in some domains, such as refunds or chargebacks, but if the data model explicitly defines revenue as non-negative, that constraint should be enforced consistently.

For financial or operational reporting, source corrections and late-arriving records can change historical windows. Reports should therefore have clearly defined data freshness and correction policies.

## Debugging Window Queries

A useful debugging method is to temporarily expose the underlying analytical columns.

For a `LAG` query, inspect:

`current_value`

`previous_value`

`current_value - previous_value`

For a moving average, inspect the actual rows included by the frame.

For `LAST_VALUE`, inspect the frame definition before changing the function.

For partition errors, include the partition columns in the result and sort output by those columns.

For missing-date problems, calculate the calendar difference between the current row and the row returned by `LAG`.

This approach is more reliable than looking only at the final aggregate metric because it exposes the intermediate row relationships that produced the result.

## Practical Analytical Relationships

These functions become especially powerful when combined.

`LAG` establishes historical context.

`LEAD` establishes forward context.

`FIRST_VALUE` establishes a starting reference.

`LAST_VALUE` establishes an ending reference when the frame covers the intended final row.

A running total describes cumulative progress.

A moving average describes local behavior over a bounded frame.

Together, they allow a daily revenue record to carry both its local context and its broader position inside the historical partition.

For example, one report row can answer:

- What was the revenue?
- What was the previous recorded revenue?
- What comes next?
- What was the initial revenue?
- What is the final historical revenue?
- How much revenue has accumulated so far?
- What is the recent three-row average?
- How many calendar days separate this observation from the previous one?
- How large was the percentage change?

The important design principle is that each calculation answers a different analytical question. They should not be treated as interchangeable forms of aggregation.
