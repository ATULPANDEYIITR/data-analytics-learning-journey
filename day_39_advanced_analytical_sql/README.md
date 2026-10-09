# Advanced Analytical SQL

## Scope

Advanced analytical SQL transforms ordered observations into statistical summaries, time-dependent metrics, and continuity reports. This module concentrates on five closely related techniques:

- **Percentiles and median** describe the distribution of observed values without requiring every observation to have equal importance in a business interpretation.
- **Conditional aggregation** calculates several business measures from the same relational dataset while applying different eligibility conditions to each measure.
- **Rolling calculations** evaluate a moving frame of observations or dates, exposing changes that ordinary grouped summaries can conceal.
- **Gaps and islands** identify missing intervals and consecutive runs in dates or ordered identifiers.
- **Data-quality analysis** distinguishes a missing observation from a recorded zero and makes reporting assumptions explicit.

The examples use daily revenue, order counts, business departments, and observation statuses. The PostgreSQL implementation is executable in a PostgreSQL environment and uses temporary tables so that the analytical examples do not permanently alter the database.

## Statistical percentiles and median

A percentile identifies a position within an ordered distribution. The median is the 50th percentile. The 90th percentile, for example, describes an upper-tail threshold: approximately 90% of the distribution lies at or below that threshold, subject to the percentile definition and ties.

PostgreSQL provides two important ordered-set aggregates:

- `PERCENTILE_CONT(p) WITHIN GROUP (ORDER BY value)` computes a continuous percentile. When the desired position falls between observations, it interpolates between adjacent ordered values.
- `PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY value)` returns an actual observed value using the discrete cumulative-distribution definition.

For the ordered values 10, 20, 30, and 40, the continuous median is 25 because the middle position falls halfway between 20 and 30. The discrete median is 20 because it selects an existing observation according to the discrete percentile rule.

The distinction matters in operational reporting. Interpolated percentiles are useful for describing a distribution smoothly, while discrete percentiles are useful when the threshold must correspond to an actual observed measurement.

### PostgreSQL implementation

The SQL script calculates the median and upper percentiles of completed daily revenue separately for each department. Its percentile aggregates include a `FILTER` clause, so cancelled and pending records do not enter the distribution.

The array form of `PERCENTILE_CONT` calculates multiple percentile values within one aggregate expression. The corresponding discrete form returns actual values from the ordered sample.

### Important statistical decisions

The percentile population must be defined before calculating a result. A median that includes cancelled observations is not interchangeable with a median of completed revenue. The SQL examples filter completed records explicitly.

An empty filtered population yields a null aggregate rather than a meaningful numeric threshold. Application code should preserve that distinction rather than silently replacing the result with zero.

Percentiles do not prove that an observation is erroneous. The upper 5% of valid revenue observations may reflect legitimate demand peaks. Threshold-based outlier screening should trigger investigation, not automatic deletion.

## Conditional aggregation

Conditional aggregation calculates multiple measures from the same set of rows without requiring a separate query for every metric.

PostgreSQL's aggregate `FILTER` clause applies a condition to one aggregate while leaving the surrounding group unchanged. For example, `SUM(revenue) FILTER (WHERE status = 'completed')` sums revenue only for completed records, while `COUNT(*) FILTER (WHERE status = 'cancelled')` independently counts cancelled records.

A `CASE` expression provides another approach. `SUM(CASE WHEN status = 'completed' THEN revenue ELSE 0 END)` converts each row into a contribution to the completed-revenue total. This form is especially useful when the contribution itself must be transformed or when a report needs to remain compatible with SQL dialects that do not support aggregate `FILTER`.

The examples distinguish:

- Completed revenue and completed orders, which describe fulfilled business activity.
- Cancelled orders and cancelled-day counts, which describe cancellations.
- Pending-day counts, which describe work that has not reached completion.
- The average revenue of completed days, which differs from the average revenue of all recorded days.

The difference between `COUNT(*)` and `COUNT(column)` is important when null values are possible. `COUNT(*)` counts rows; `COUNT(column)` counts only rows where the selected expression is not null. Similarly, `SUM` ignores null inputs. A missing value must not be interpreted as zero unless the data model and business definition support that assumption.

Conditional aggregation is particularly useful in operational scorecards, financial reporting, fulfillment monitoring, service-level reports, and reconciliation queries.

## Rolling calculations

A rolling calculation evaluates an ordered frame relative to each current row. The SQL script uses window functions with explicit partitioning, ordering, and frame boundaries.

The expression `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` describes a frame containing the current observation and at most two preceding observations. A running or rolling sum is then calculated for every row without collapsing the output into one row per department.

### Row-based frames versus calendar-based frames

These are different analytical operations.

A row-based frame counts observations. If a department has records on Monday, Tuesday, and Friday, the three-row frame for Friday can include all three records even though they span five calendar days.

A calendar-based frame describes a date interval. A seven-calendar-day calculation should account for every date in the seven-day period, including dates without source records.

The SQL implementation generates a date spine with `generate_series`, combines each department with each reporting date, and left-joins observed daily data. This makes the calendar explicit before the rolling window is evaluated.

The sample uses zero revenue for dates without records. That is a business assumption, not a universal rule. In some systems, no row means no activity; in others, it means the feed failed or the value is unknown. The dense series retains an observation indicator so missing records can be distinguished from observed rows with zero revenue.

### Partitioning and ordering

`PARTITION BY department` prevents one department's observations from entering another department's frame. `ORDER BY business_date` defines the sequence.

The date and department combination is unique in the sample table. If multiple observations per date are allowed in a production dataset, the query must define whether the analysis operates on transactions or on daily aggregates. Transaction-level rolling frames require a deterministic tie-breaker, such as a unique transaction identifier, when timestamps are equal.

### Performance considerations

Window calculations typically require ordering within each partition. Indexes that begin with the partitioning key and ordering key can help PostgreSQL locate relevant data, although the planner may still choose a sort based on cardinality and cost estimates.

Generating a dense calendar increases the number of rows to be processed. Limit the reporting interval and department population to the actual analytical requirement. For large recurring reports, a maintained calendar table or preaggregated daily fact table can make the intended date semantics easier to manage.

## Gaps and islands

Gaps and islands analysis finds either absent intervals or consecutive runs of present values.

An **island** is a maximal consecutive sequence. A **gap** is an interval within the reporting boundaries that contains no observed date or identifier.

### Date islands

The PostgreSQL implementation first removes duplicate department/date pairs. It then assigns each date a row number ordered within its department.

For consecutive dates, the difference between the date and the row number remains constant. Grouping by that difference identifies islands. The same idea applies to consecutive integer identifiers, where `identifier - ROW_NUMBER()` provides a stable grouping key for each run.

This technique is useful for reporting streaks, service-availability periods, employee attendance sequences, recurring activity, and uninterrupted event histories.

### Missing-date intervals

Islands over observed dates do not automatically reveal missing dates at the beginning or end of a reporting period. The query must define the reporting boundaries and construct the expected calendar.

The SQL script generates each date in the inclusive interval, left-joins observed department/date pairs, and retains dates without observations. It then groups consecutive missing dates using the same difference-key principle.

The explicit reporting range is essential. Without it, leading and trailing gaps cannot be inferred reliably because the dataset does not indicate how far the analysis should extend.

### Missing observations versus zero values

A date with a recorded revenue of zero is an observed date. A date with no source record is absent. Those states have different meanings for audit, operational monitoring, and rolling calculations.

The data-quality query classifies each date as `missing_record`, `recorded_zero_revenue`, or `recorded_nonzero_revenue`. This distinction helps detect feed failures without incorrectly treating legitimate zero-activity periods as missing data.

## Python implementation

The Python script implements the analytical rules with standard-library data structures and executable assertions.

Its `percentile_cont` function sorts values and interpolates at the fractional position \(p(n-1)\). The `percentile_disc` function selects the first ordered value meeting the discrete percentile position. Both functions validate the percentile range and reject empty samples.

`conditional_aggregation` separates completed, cancelled, and pending records before calculating revenue and order measures. It avoids including cancelled or pending revenue in the completed-revenue metric.

`rolling_metrics` calculates a trailing frame of rows after sorting observations by date. `calendar_rolling_metrics` instead iterates over dates and fills absent dates with zero. The code documents the assumption that this represents zero activity rather than unknown activity.

`consecutive_date_islands` deduplicates observed dates before identifying maximal consecutive runs. `missing_date_gaps` accepts explicit inclusive boundaries, so leading and trailing gaps inside the reporting interval are detected.

The self-tests cover interpolated and discrete percentiles, empty inputs, consecutive dates, integer islands, and missing intervals. They provide executable checks of the analytical definitions rather than relying only on printed examples.

## JavaScript implementation

The JavaScript implementation emphasizes reusable analysis functions and controlled input validation.

Revenue is represented as integer paise instead of binary floating-point currency values. Percentile interpolation may produce fractional paise internally, so it is a statistical estimate rather than a directly posted financial amount. Rounding should be applied only where the reporting or financial specification requires it.

`DailyAnalytics` exposes department summaries, completed-revenue percentiles, row-based rolling calculations, calendar-based rolling calculations, date islands, and missing-date intervals. Its private record collection prevents callers from directly replacing the stored collection.

The implementation validates ISO date strings by checking both the syntax and the parsed calendar date. It also rejects invalid statuses, negative amounts, and invalid order counts.

The rolling-row algorithm retains only the observations that can participate in the next frame. For a frame size of \(k\), the retained partition history is bounded by \(k\) records per active partition, rather than requiring an additional full copy of every preceding observation. The calendar implementation is intentionally direct and is appropriate for bounded reporting periods; a larger reporting workload would benefit from a rolling accumulator.

## C++ case study

The C++ program models daily operational data for North and South distribution regions. Its `DailyRecord` structure captures the date, region, integer-paise revenue, order count, and status. The `OperationalAnalytics` class validates records and provides separate methods for conditional aggregates, percentiles, rolling frames, and date continuity analysis.

The date utilities validate calendar dates, convert them into a serial-day representation, and convert back to calendar dates. Serial-day arithmetic makes consecutive-date comparisons independent of month lengths and leap-year boundaries.

The percentile methods operate on copies of the supplied values so that sorting does not change the caller's data. They reject empty samples and out-of-range percentile values. The rolling methods partition data by region to avoid cross-region contamination.

The implementation distinguishes row-based windows from calendar windows. The row-based method selects preceding observations in a sorted partition. The calendar-based method iterates over each date in an explicit interval and looks up revenue for the preceding calendar days.

The date-island and gap functions use sorted, deduplicated dates and contiguous-run boundaries. Missing intervals are limited to a supplied inclusive reporting period.

The case study demonstrates how an analytical engine can enforce input invariants before calculating statistical metrics. It also illustrates trade-offs: exact integer currency storage avoids common floating-point errors, while percentile interpolation requires a floating-point or rational representation for intermediate values.

## Java implementation

The Java program uses immutable records for `DailyRecord`, `PercentileReport`, `Island`, `Gap`, `RollingResult`, and `DepartmentSummary`. The compact record constructors enforce essential domain invariants when data is created.

The `Status` enum restricts each record to a known business state. A `switch` expression in the aggregation logic makes the handling of completed, cancelled, and pending observations explicit. A department with no completed revenue observations receives a null median, rather than a misleading zero.

`BigDecimal` represents monetary values and provides explicit rounding for displayed output. Percentile interpolation uses a decimal fractional position, while the selected percentile definition determines whether an interpolated or observed value is returned.

The rolling methods partition observations by department and order each partition by date. The calendar method aggregates daily revenue and calculates totals over explicit date intervals. `findIslands` and `findGaps` use `LocalDate` operations, which avoid manual calendar arithmetic and handle month and year transitions correctly.

The Java self-tests check percentile semantics, empty-sample rejection, and date-island behavior. The program uses only Java 17 standard-library features and can be compiled without external dependencies.

## PostgreSQL relational model

The SQL script creates a temporary `analytics_daily` table with a generated primary key, nonnegative numeric constraints, a constrained status domain, and a unique department/date combination.

The uniqueness constraint establishes that each department has at most one daily record. If multiple observations per day are needed, the model should instead separate transaction-level facts from daily aggregates.

The index on `(department, business_date)` supports access patterns that filter by department and order by date. The index on `(status, business_date)` supports status-oriented reporting. Whether either index is worthwhile for a small table depends on the workload; indexes consume storage and add write costs.

The ordered-set aggregate queries calculate continuous and discrete percentiles. Conditional aggregation combines several measures in one grouped query. Window queries preserve row-level output while calculating rolling totals. Date-spine queries explicitly construct the expected calendar before identifying absent observations or calculating calendar-based rolling totals.

The constraint demonstration uses nested exception blocks. Each expected constraint violation is handled inside its own subtransaction, allowing the surrounding script to continue. The final `ROLLBACK` removes the temporary analytical setup and sample records from the transaction.

## Edge cases and interpretation

- **Duplicate dates:** Date-island analysis should deduplicate observations when the unit of continuity is a calendar date. Duplicate transaction rows must not automatically be removed from transaction-level statistical analysis.
- **Tied values:** Multiple observations can share a percentile threshold. Percentile position does not imply that exactly a given percentage of rows is strictly below the result.
- **Empty samples:** A filtered group may contain no eligible values. The application should preserve a null or explicit missing result instead of manufacturing a numeric threshold.
- **Sparse observations:** A row-based rolling frame and a calendar-based rolling frame can contain different observations. The intended time semantics must determine which method is used.
- **Unknown activity:** Filling absent dates with zero can hide ingestion failures. Retain a presence indicator whenever source completeness matters.
- **Reporting boundaries:** Gap detection requires an explicit range to identify missing intervals at the beginning or end of a reporting period.
- **Ordering ties:** Window calculations need a deterministic ordering whenever multiple rows can share the same partition key and ordering value.
- **Financial precision:** Currency should use fixed-scale database numerics or integer minor units, with an explicit rounding policy for displayed or posted results.

## Practical use

Percentiles help establish distribution-based service thresholds, compare regional performance, and identify observations that deserve investigation. Conditional aggregation creates compact operational scorecards with separate counts and amounts for each business state. Rolling calculations expose short-term trends, while gaps-and-islands analysis detects reporting interruptions and sustained activity periods.

These techniques are most reliable when the observation grain, eligible population, reporting boundaries, treatment of missing dates, and statistical definitions are specified before the query is written.
