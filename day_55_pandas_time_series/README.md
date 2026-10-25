# Pandas Time Series: DatetimeIndex, Resampling, Rolling Windows, Shifting, and Time-Based Grouping

## Scope

This project studies time-series analysis through five related operations:

- `DatetimeIndex` for chronological indexing and time-aware selection
- resampling for changing the temporal resolution of observations
- rolling windows for local temporal statistics
- shifting and differences for comparing observations across time
- time-based grouping for calendar and time-of-day analysis

The implementations use a sensor-monitoring scenario with irregular observations containing temperature, atmospheric pressure, and energy consumption.

The five source files deliberately use different implementation approaches. Python models the workflow with Pandas directly. JavaScript implements the same analytical concepts with timestamp-based collections and event-oriented processing. C++17 implements an explicit time-series analytics class. Java 17 uses immutable records, domain validation, services, and explicit analytical state. PostgreSQL represents the same concepts through relational tables, window functions, views, aggregation, and time-range queries.

## Domain Model

The logical relationship is:

`Sensor → Timestamped Observations → Chronological Index → Temporal Transformation → Derived Metrics → Analysis`

Each observation contains:

| Field | Meaning |
|---|---|
| `timestamp` | Exact observation time |
| `temperature` | Temperature measurement |
| `pressure` | Pressure measurement |
| `energy_kwh` | Energy consumed since the previous measurement interval |

The observations are intentionally irregular. They do not arrive at a constant interval, which makes time-based windows and resampling materially different from simple row-based operations.

## DatetimeIndex

A Pandas `DatetimeIndex` is an index whose values represent timestamps.

The Python implementation creates the index with `pd.DatetimeIndex` and validates several important properties:

- timestamps are chronological
- timestamps are unique
- the index contains actual datetime values
- timezone information is handled explicitly

The index is normalized to UTC in the example.

A time-series index is different from an ordinary integer index because Pandas can use temporal information when selecting data, resampling observations, and calculating time-based windows.

The source data contains gaps between observations. Those gaps are preserved until a temporal transformation explicitly changes the frequency.

For example, observations may exist at:

| Timestamp | Temperature |
|---|---:|
| 2026-01-01 08:00 | 21.2 |
| 2026-01-01 12:00 | 22.1 |
| 2026-01-02 09:30 | 20.8 |
| 2026-01-05 14:00 | 24.0 |

The difference between these timestamps matters when a time-based rolling window is calculated.

## Timezones

Timezone handling is an important production consideration.

A naive timestamp does not identify a specific instant globally. An aware timestamp includes timezone information and can therefore be converted safely between timezones.

The Python implementation uses UTC timestamps. The Java implementation uses `Instant`, which represents an absolute point in time. The JavaScript implementation uses `Date`, which internally represents an instant as milliseconds from the Unix epoch. PostgreSQL uses `TIMESTAMPTZ`.

These representations reduce ambiguity when observations originate from multiple systems.

Timezone conversion and timezone localization are distinct operations:

| Operation | Meaning |
|---|---|
| Localization | Assign a timezone to a timestamp that lacks timezone information |
| Conversion | Convert an already timezone-aware timestamp to another timezone |

Incorrectly treating conversion as localization can shift the represented instant and produce incorrect temporal analysis.

## Resampling

Resampling changes the frequency of a time series.

The Python implementation uses `resample("D")` to produce daily aggregates.

The daily result calculates:

- mean temperature
- mean pressure
- total energy consumption

The aggregation functions are intentionally different because the measurements have different meanings.

Temperature and pressure are point measurements, so their daily mean is meaningful for this scenario. Energy consumption is cumulative over observation intervals, so summation is appropriate.

The PostgreSQL implementation expresses the same operation using:

`date_trunc('day', observed_at)`

followed by grouped aggregation.

The daily workflow is conceptually:

`Irregular observations → Calendar day → Aggregate measurements`

Resampling does not mean interpolation. If a day has no observation, resampling may create a missing temporal bucket depending on the operation and subsequent handling.

## Resampling Versus Interpolation

These operations solve different problems.

| Operation | Purpose |
|---|---|
| Resampling | Changes the temporal frequency |
| Interpolation | Estimates missing values |
| Forward fill | Carries an earlier value forward |
| Backward fill | Uses a later value |
| Aggregation | Combines observations |
| As-frequency conversion | Exposes expected time slots without automatically estimating values |

The Python implementation includes hourly resampling followed by time interpolation with a bounded interpolation limit.

The limit prevents an arbitrarily large data gap from being silently filled.

That distinction is important in production analytics. A missing sensor reading and a genuine period without observations should not automatically be treated as the same thing.

## Rolling Windows

A rolling window calculates statistics over a moving temporal neighborhood.

The Python implementation uses a seven-day time-based window:

`rolling("7D")`

This is different from a seven-row window.

Consider observations separated by:

- 1 hour
- 2 hours
- 1 day
- 4 days
- 10 days

A seven-row rolling window always considers seven observations.

A seven-day time-based window considers observations whose timestamps fall inside the specified temporal interval.

This distinction becomes important when data arrival is irregular.

The implementation calculates:

- rolling temperature mean
- rolling temperature standard deviation
- rolling energy total
- rolling observation count

The C++ and Java implementations reproduce the time-based behavior by comparing timestamp differences instead of assuming a fixed number of rows.

## Rolling Window Boundaries

A temporal rolling calculation must define which observations belong to a window.

For an observation at time `T`, the seven-day calculation examines timestamps within the configured temporal interval preceding `T`.

Boundary semantics matter because an observation exactly at the edge of the interval can affect the result.

Pandas provides explicit window semantics through its rolling-window API. The other implementations encode the equivalent temporal comparison directly.

This is one reason time-based rolling analysis is more complex than a simple list slice.

## Minimum Observations

The Python rolling calculations use `min_periods` where appropriate.

This prevents a rolling metric from being treated as statistically meaningful when insufficient observations exist.

For example, a standard deviation cannot provide a meaningful sample estimate from a single observation.

The Java and C++ implementations return zero for a rolling standard deviation when fewer than two observations exist. This is a deliberate representation for the standalone implementations, while Pandas can represent the corresponding unavailable statistic as `NaN`.

The distinction matters when consuming analytical results downstream.

## Shifting

Shifting moves values relative to their original timestamps.

The Python implementation uses:

`shift(1)`

to obtain the previous temperature.

For an ordered series:

| Time | Current | Previous |
|---|---:|---:|
| T1 | 21.2 | missing |
| T2 | 22.1 | 21.2 |
| T3 | 20.8 | 22.1 |

The first observation has no previous observation, so its shifted value is missing.

The operation does not require the timestamps themselves to move. It changes the alignment of values.

This makes shifting useful for:

- lag features
- period-over-period comparison
- change detection
- forecasting features
- anomaly analysis

## Difference

The difference between consecutive values can be calculated from a shift:

`current - previous`

The Python implementation uses `diff()` for this purpose.

The first row has no predecessor and therefore produces a missing result.

The JavaScript, C++, Java, and PostgreSQL implementations explicitly reproduce this behavior.

PostgreSQL uses the `LAG` window function, which is the relational equivalent of obtaining a previous observation within an ordered partition.

## Percentage Change

Percentage change measures relative rather than absolute movement.

For two consecutive values:

`(current - previous) / previous × 100`

The implementation protects against division by zero.

A percentage change should not be interpreted when the previous value is zero because the mathematical denominator is undefined.

This is why production time-series transformations require validation rather than blindly applying formulas.

## Time-Based Grouping

Time-based grouping categorizes observations according to calendar or clock properties.

The Python implementation groups observations by:

- week
- month
- hour of day

The PostgreSQL implementation uses `date_trunc` and `EXTRACT`.

The JavaScript implementation groups observations by week and hour.

The Java implementation exposes hour-of-day grouping through a typed collection.

Grouping by calendar period is different from resampling.

Resampling generally establishes a temporal frequency and then applies aggregation. Grouping directly by a temporal property can combine observations according to a calendar characteristic without necessarily constructing every missing time bucket.

## Calendar Grouping

Weekly analysis can answer questions such as:

- Which week had the highest energy consumption?
- What was the average temperature by week?
- How many observations arrived during each week?
- Did measurement density change over time?

The PostgreSQL weekly view calculates:

- average temperature
- maximum temperature
- minimum temperature
- total energy
- observation count

This produces an analytical representation without modifying the underlying readings.

## Time-of-Day Grouping

Hour-of-day grouping ignores the date and focuses on clock time.

For example, all observations recorded around 09:00 can be analyzed together.

This can identify recurring daily patterns.

The analysis must be interpreted carefully when observations come from different timezones. Grouping by UTC hour is not automatically equivalent to grouping by local operational hour.

The source implementations therefore use explicit UTC behavior.

## Python Implementation

The Python implementation is the most direct representation of the requested Pandas concepts.

### Main structures

`TimeSeriesConfig` stores configurable temporal parameters.

`build_sensor_series()` creates an irregular time series with a timezone-aware `DatetimeIndex`.

`validate_datetime_index()` verifies chronological ordering, uniqueness, and non-empty data.

`normalize_timezone()` handles timezone localization or conversion.

`daily_resampling()` performs daily aggregation.

`hourly_interpolation()` demonstrates frequency conversion followed by bounded time interpolation.

`calculate_time_based_rolling()` calculates rolling temporal statistics.

`calculate_shifts_and_changes()` produces lagged values, differences, and percentage changes.

`group_by_calendar_period()` performs weekly grouping.

`group_by_month_and_hour()` demonstrates multidimensional temporal grouping.

`detect_temperature_anomalies()` compares current temperature with a rolling baseline.

`demonstrate_file_round_trip()` verifies that the time-series index can be persisted and reconstructed.

### Validation

The Python script checks:

- index type
- ordering
- duplicate timestamps
- empty datasets
- valid anomaly thresholds
- successful transformations

Assertions at the end verify that the principal analytical operations produced expected structures.

## JavaScript Implementation

The JavaScript implementation does not attempt to reproduce Pandas APIs mechanically.

Instead, it uses an explicit `TimeSeries` class backed by ordered `TimeSeriesPoint` objects.

`TimeSeriesPoint` validates timestamps and stores measurements immutably.

`TimeSeries` sorts observations chronologically and rejects duplicate timestamps.

The class implements:

| Method | Purpose |
|---|---|
| `resampleDaily()` | Daily aggregation |
| `rollingTimeWindow()` | Temporal rolling statistics |
| `shiftAndDiff()` | Previous-value and difference calculations |
| `groupByWeek()` | Weekly calendar grouping |
| `groupByHour()` | Time-of-day grouping |

JavaScript `Map` objects are used for temporal buckets. `Date` objects provide timestamp arithmetic.

The rolling implementation uses a moving left boundary rather than repeatedly scanning the entire dataset. This gives the algorithm a more scalable structure for ordered time-series data.

The program uses only Node.js standard functionality.

## C++17 Implementation

The C++ program treats the time series as an explicit domain object.

`Timestamp` represents a timestamp and provides deterministic ordering.

`Observation` stores the measurements.

`TimeSeries` owns and validates the observations.

The implementation uses:

- `std::vector` for ordered observations
- `std::map` for temporal buckets
- `std::tuple` for calendar keys
- STL algorithms for sorting and accumulation
- exceptions for invalid input
- assertions for final validation

The C++ implementation deliberately uses an explicit data model rather than a dataframe abstraction.

This makes the mechanics of temporal processing visible:

`sort → identify temporal boundary → collect observations → aggregate`

The rolling implementation maintains a left boundary and advances it as the right boundary moves forward.

For `n` observations, the boundary movement is monotonic, although the current implementation still constructs a temporary value collection for each result. A production implementation could maintain rolling sums and squared sums to reduce repeated work.

## Java 17 Implementation

The Java implementation uses records to represent immutable domain values.

`Observation` validates measurement values at construction time.

`DailyAggregate` represents daily resampling results.

`RollingResult` represents the output of a rolling calculation.

`ReviewState` represents the analytical lifecycle of the `TimeSeries` object.

The implementation uses:

- `Instant` for absolute timestamps
- `Duration` for temporal windows
- records for immutable result objects
- `List` for ordered observations
- `TreeMap` for deterministic temporal grouping
- streams for aggregation
- explicit exceptions for invalid input

`TimeSeries` sorts its input and rejects duplicate timestamps before analysis.

This separates data validation from analytical operations and makes invalid state harder to propagate.

## PostgreSQL Implementation

The PostgreSQL implementation represents the same time-series concepts relationally.

The primary tables are:

### `sensors`

Stores sensor identity and timezone metadata.

### `sensor_readings`

Stores timestamped measurements.

Important constraints include:

- foreign-key relationship to `sensors`
- unique `(sensor_id, observed_at)`
- valid temperature range
- positive pressure
- non-negative energy

The unique timestamp constraint is the database equivalent of rejecting duplicate entries in a `DatetimeIndex`.

## PostgreSQL Indexing

The primary analytical index is:

`(sensor_id, observed_at)`

This supports queries that retrieve one sensor's observations in chronological order.

A separate timestamp index supports time-oriented access across sensors.

Indexes have a storage and write-maintenance cost, so they should correspond to actual query patterns.

## PostgreSQL Window Functions

The `sensor_changes` view uses `LAG`.

This corresponds conceptually to Pandas `shift(1)`.

The query partitions observations by sensor and orders them by timestamp.

This is essential because a previous value must be previous within the same sensor's chronological stream rather than simply previous in the entire table.

The `seven_day_rolling_metrics` view uses PostgreSQL window frames with an interval-based `RANGE` specification.

It calculates:

- rolling mean
- rolling standard deviation
- rolling energy
- rolling observation count

This is a database-native representation of time-based rolling analysis.

## PostgreSQL Views

The SQL script creates separate analytical views:

| View | Purpose |
|---|---|
| `daily_sensor_summary` | Daily resampling |
| `sensor_changes` | Shift and difference analysis |
| `seven_day_rolling_metrics` | Seven-day rolling metrics |
| `weekly_sensor_summary` | Weekly grouping |
| `hourly_sensor_summary` | Hour-of-day grouping |

The source readings remain unchanged while derived analytical representations are exposed through views.

This is useful when analytical logic should be reusable without duplicating derived data.

## Parameterized Time Retrieval

The `readings_between` function accepts:

- sensor code
- start timestamp
- end timestamp

The function returns readings within the half-open interval:

`start <= timestamp < end`

Half-open intervals are useful because adjacent time windows can be combined without overlapping at their boundary.

For example:

`[10:00, 11:00)`

and

`[11:00, 12:00)`

do not duplicate the observation at 11:00.

## Data Quality Rules

Time-series analysis is sensitive to poor input quality.

The implementations address several common conditions:

| Failure condition | Handling |
|---|---|
| Empty dataset | Rejected |
| Duplicate timestamp | Rejected |
| Unsorted observations | Sorted or rejected depending on implementation |
| Invalid timestamp | Rejected |
| Negative energy | Rejected |
| Invalid pressure | Rejected |
| Excessive interpolation gap | Limited |
| Zero denominator | Percentage change omitted |
| Insufficient rolling observations | Explicitly handled |
| Invalid rolling duration | Rejected |

These controls prevent analytical errors from being hidden inside downstream calculations.

## Missing Observations

Missing timestamps and missing values are separate concepts.

A timestamp gap means there was no recorded observation at that time.

A missing value means an observation exists but one of its measurements is unavailable.

Resampling can expose missing temporal slots. Interpolation can estimate values for some gaps. Neither operation proves that the estimated value is physically correct.

For sensor systems, interpolation should therefore be bounded and accompanied by data-quality metadata when used operationally.

## Performance Considerations

For an ordered time series containing `n` observations:

- sorting generally costs `O(n log n)`
- sequential grouping is approximately `O(n)`
- simple lag calculations are `O(n)`
- bucket aggregation is approximately `O(n)` after chronological organization
- naive rolling calculations can become expensive when each window is rebuilt independently

The Python and database implementations benefit from optimized internal operations.

For large datasets, the C++ and Java rolling implementations can be improved by maintaining incremental state such as:

- rolling sum
- rolling squared sum
- observation count
- moving window boundaries

This can avoid repeatedly scanning every value inside each window.

Database performance also depends heavily on timestamp ordering, partitioning strategy, index selectivity, and query range.

## Numerical Considerations

Rolling standard deviation is sensitive to the number of observations.

Sample standard deviation uses `n - 1` in the denominator and therefore requires at least two observations.

Floating-point calculations can also accumulate small numerical errors.

For financial, scientific, or industrial measurements requiring strict numerical guarantees, precision requirements should be determined before selecting storage and computation types.

The PostgreSQL example uses numeric columns rather than floating-point database types for measurement storage.

## Security and Operational Considerations

Time-series processing is usually a data-integrity problem as much as a computational problem.

Production systems should consider:

- validating incoming timestamps
- rejecting impossible measurements
- controlling who can insert or modify raw observations
- using parameterized database operations
- enforcing uniqueness at the database layer
- preventing unbounded query ranges
- recording source and ingestion metadata
- separating raw observations from derived analytics
- monitoring delayed or missing data
- protecting exported files containing operational measurements

The PostgreSQL function uses parameters rather than constructing SQL statements from user-provided strings.

The Python persistence example uses a temporary directory and does not rely on an unsafe fixed output location.

## Conceptual Comparison

| Concept | Pandas | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Time index | `DatetimeIndex` | Ordered `Date` values | `Timestamp` | `Instant` | `TIMESTAMPTZ` |
| Resampling | `resample()` | Temporal buckets | `map` buckets | `TreeMap` buckets | `date_trunc()` |
| Rolling | `rolling()` | Moving boundary | Moving boundary | `Duration` boundary | Window `RANGE` |
| Shift | `shift()` | Previous array element | Previous vector element | Previous list element | `LAG()` |
| Difference | `diff()` | Subtraction | Subtraction | Subtraction | Arithmetic over `LAG()` |
| Grouping | `groupby()` | `Map` | `std::map` | `TreeMap` | `GROUP BY` |
| Validation | Exceptions and assertions | Exceptions | Exceptions | Exceptions and records | Constraints |
| Persistence | CSV round trip | In-memory | In-memory | In-memory | Relational tables |

## Distinction Between the Core Operations

The operations should not be treated as interchangeable.

`DatetimeIndex` establishes chronological structure.

Resampling changes the temporal resolution and usually combines observations.

Rolling windows calculate statistics over moving temporal neighborhoods.

Shifting changes value alignment relative to time.

Differences compare a value against an earlier value.

Grouping partitions observations according to temporal properties.

A practical workflow can combine them:

`DatetimeIndex → validate → resample → rolling analysis → shift/difference → group/report`

Each stage answers a different analytical question.

## Practical Sensor Workflow

A realistic operational pipeline can be represented as:

`Raw sensor readings`
  
`↓`

`Timestamp validation`

`↓`

`Chronological ordering`

`↓`

`Data-quality validation`

`↓`

`Frequency transformation`

`↓`

`Rolling baseline`

`↓`

`Lag and change calculation`

`↓`

`Calendar/time-of-day grouping`

`↓`

`Operational reporting`

This separation makes it easier to identify whether an unusual result came from raw data quality, temporal transformation, or analytical logic.

## Implemented Edge Cases

The examples deliberately include irregular intervals rather than perfectly uniform observations.

This allows the implementations to demonstrate why temporal windows should not automatically be interpreted as row counts.

The first shifted value has no predecessor.

The first rolling observations have fewer values than later windows.

Daily resampling can produce one or more observations per day.

Weekly grouping can contain different numbers of observations.

Hour-of-day grouping can contain sparse hours.

The dataset therefore exercises several conditions that occur in real operational time-series systems.

## Limitations

The implementations are educational analytical models rather than complete distributed time-series platforms.

They do not implement:

- distributed ingestion
- streaming checkpoint recovery
- late-arriving event reconciliation
- daylight-saving-time business calendars
- sensor calibration management
- outlier correction based on domain physics
- distributed storage
- partition lifecycle management

Those concerns require additional architectural decisions beyond the core Pandas time-series operations represented here.

The central focus remains the correct handling of timestamped observations, temporal transformations, rolling calculations, shifts, and time-based grouping.
