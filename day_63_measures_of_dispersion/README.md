# Measures of Dispersion

## Scope

This project implements six important measures of statistical dispersion:

| Measure | Meaning | Main use |
|---|---|---|
| Range | Maximum minus minimum | Fast assessment of total spread |
| Variance | Average squared deviation from the mean | Quantifying squared dispersion |
| Standard deviation | Square root of variance | Dispersion in the original measurement unit |
| IQR | Q3 minus Q1 | Robust spread of the central 50% |
| MAD | Median absolute deviation from the median | Robust deviation measure |
| Coefficient of variation | Standard deviation relative to the absolute mean | Comparing relative variability across scales |

The implementations use the same representative observations so that the measures can be compared directly while each programming language uses its own appropriate design mechanisms.

## Statistical Model

The example dataset is:

`12, 15, 14, 10, 18, 20, 13, 16, 15, 11`

The arithmetic mean is `14.4`.

The range is:

`maximum - minimum`

For this dataset:

`20 - 10 = 10`

Population variance uses division by `n`:

`σ² = Σ(x - μ)² / n`

Sample variance uses division by `n - 1`:

`s² = Σ(x - x̄)² / (n - 1)`

Population standard deviation is the square root of population variance. Sample standard deviation is the square root of sample variance.

The interquartile range is:

`IQR = Q3 - Q1`

The median absolute deviation is:

`MAD = median(|xi - median(x)|)`

The coefficient of variation is calculated as:

`CV = population standard deviation / |mean| × 100`

The absolute value of the mean is used in the denominator so that the relative magnitude is not affected by the sign of the mean.

When the mean is zero, the coefficient of variation is treated as undefined rather than producing a misleading numeric result.

## Relationship Between the Measures

The measures describe different properties of the same distribution.

- Range uses only the two extreme observations.
- Variance uses every observation and squares deviations, so large deviations receive greater weight.
- Standard deviation expresses the same squared-deviation information in the original unit.
- IQR ignores the lower and upper quarters and concentrates on the central half.
- MAD uses distances from the median and is less affected by extreme observations.
- CV expresses standard deviation relative to the mean and is useful when comparing datasets with different scales.

Range and standard deviation are sensitive to extreme observations. IQR and MAD are more resistant to outliers. CV is useful for relative comparison but becomes inappropriate when the mean is zero or close to zero.

## Python Implementation

The Python implementation uses a `DispersionReport` dataclass to hold the complete calculated result.

The calculation pipeline is separated into validation, descriptive statistics, percentile calculation, report construction, persistence, and tests.

Important mechanisms include:

- Lists for observations.
- Dictionaries for serialized report data.
- `Enum` for named dispersion methods.
- Dataclass-based immutable result representation.
- Explicit input validation.
- Exception handling through `DispersionError`.
- Percentile interpolation for Q1 and Q3.
- Population and sample variance as separate quantities.
- JSON report persistence using the standard library.
- Assertions covering normal input, a single observation, empty input, and invalid numeric input.

The Python implementation also classifies coefficient-of-variation values into low, moderate, and high relative dispersion.

## JavaScript Implementation

The JavaScript implementation treats dispersion analysis as an event-driven processing operation.

`DispersionMonitor` extends Node.js `EventEmitter`. Each calculation produces a structured event containing the source, timestamp, and statistical report.

Two event types are used:

- `calculated` is emitted for every successful calculation.
- `high-variability` is emitted when the coefficient of variation exceeds the configured threshold.

The implementation uses:

- Objects for structured reports.
- `Array` operations for aggregation and transformation.
- `Set`-compatible JavaScript collection semantics through native structures where appropriate.
- Classes for monitoring and analysis responsibilities.
- Promises and `async`/`await` for report persistence.
- Node.js `fs/promises` for file output.
- File permissions restricted to the current user when writing the temporary report.
- Custom validation errors.
- Runtime assertions for edge cases.

The event-driven design separates calculation from operational response. A monitoring application could therefore consume the calculated event without modifying the statistical engine.

## C++17 Implementation

The C++17 program models dispersion calculation as an explicit `DispersionEngine`.

The result is stored in a `DispersionReport` structure, while `VariabilityLevel` represents the classification state.

The implementation uses:

- `std::vector<double>` for observations.
- STL algorithms for sorting and extrema.
- `std::accumulate` for summation.
- Explicit percentile interpolation.
- Exception-based validation.
- `std::ofstream` for report persistence.
- `std::minmax_element` for efficient extrema discovery.
- `std::isfinite` to reject invalid numeric values.

The implementation performs the complete calculation without third-party libraries.

The single-observation case is handled explicitly. Population variance remains defined for one observation, while sample variance is undefined because `n - 1` equals zero.

The calculation requires sorting for percentile and median operations. The dominant sorting cost is `O(n log n)`, while the arithmetic aggregation itself is `O(n)`.

## Java 17 Implementation

The Java implementation uses an enterprise-style service structure.

`DispersionService` owns statistical calculation and validation. `DispersionReport` is a Java record that provides an immutable representation of the result. `DispersionPolicy` separates variability classification from calculation.

The implementation uses:

- Records for immutable result data.
- Interfaces for policy abstraction.
- A concrete `StandardVariabilityPolicy`.
- Java collections for observations.
- Streams for numerical aggregation and transformations.
- A custom `DispersionException`.
- `Path` and `Files` for report persistence.
- Explicit state-free calculation methods.
- Separate validation and reporting responsibilities.

This separation prevents statistical computation from becoming coupled to a particular presentation or classification policy.

## PostgreSQL Data Model

The SQL implementation models dispersion analysis relationally.

The main relationships are:

`datasets -> observations -> dispersion_reports`

`measure_catalog` stores definitions for the supported measures.

The `datasets` table identifies independent observation collections. The `observations` table stores individual numeric measurements. The `dispersion_reports` table stores calculated aggregate results.

Foreign keys ensure that observations and reports cannot reference nonexistent datasets.

The observation table contains a validation trigger that rejects non-finite values. Check constraints on the report table enforce non-negative range, IQR, and MAD values.

## PostgreSQL Statistical Operations

The PostgreSQL implementation uses native statistical aggregates:

- `VAR_POP`
- `VAR_SAMP`
- `STDDEV_POP`
- `STDDEV_SAMP`
- `PERCENTILE_CONT`
- `AVG`
- `MIN`
- `MAX`

`PERCENTILE_CONT` provides continuous percentile interpolation, matching the interpolation approach used in the application implementations.

A common table expression calculates the principal statistics first. A second CTE calculates MAD from the median.

The `refresh_dispersion_report` function provides a reusable database-side recalculation workflow. It uses `INSERT ... ON CONFLICT DO UPDATE` so that an existing dataset report is refreshed atomically.

## Database Validation and Failure Cases

The database implementation explicitly covers several failure conditions.

An empty dataset cannot produce a dispersion report through `refresh_dispersion_report`; the function raises an exception.

A zero-mean dataset is included to demonstrate that coefficient of variation is undefined in that situation.

The database prevents non-finite observations through both a numeric validation trigger and the data model's constraints.

The sample variance naturally becomes `NULL` for a single-observation dataset because PostgreSQL's sample variance aggregate has no valid `n - 1` denominator for one observation.

## Complexity

For `n` observations:

| Operation | Typical complexity |
|---|---:|
| Minimum and maximum | O(n) |
| Mean | O(n) |
| Variance | O(n) |
| Standard deviation | O(n) after variance |
| Median | O(n log n) with sorting |
| Q1 and Q3 | O(n log n) with sorting |
| MAD | O(n log n) with sorting |
| CV | O(1) after standard deviation |

The main computational cost is sorting for percentile and median-based measures.

For large datasets, percentile calculations can use database-specific execution plans or selection algorithms where appropriate. Exact percentile calculations trade additional computation for deterministic results.

## Robustness and Edge Cases

The implementations handle:

- Empty input.
- One observation.
- Repeated observations.
- Constant observations.
- Negative observations.
- Zero mean.
- Non-finite numeric input.
- Population versus sample variance.
- Extreme observations.
- Outlier-sensitive versus robust measures.

A constant dataset has zero range, variance, standard deviation, IQR, and MAD. Its coefficient of variation is zero when the mean is non-zero.

A dataset with a zero mean can still have substantial dispersion, but its coefficient of variation is undefined. This distinction prevents CV from being interpreted as a universal measure.

## Interpretation

Consider two datasets with similar standard deviations but very different means. Their absolute variability may be comparable while their relative variability is not.

Standard deviation is therefore appropriate when the measurement scale itself is meaningful.

CV is useful when relative variation is the primary comparison, provided the means are sufficiently far from zero.

IQR and MAD are preferred when extreme observations could distort mean-based measures.

Range is useful for quick operational bounds but should not be treated as a complete description of distributional variability because it depends only on two observations.

## Validation Coverage

All application implementations test:

- The representative ten-observation dataset.
- Minimum and maximum detection.
- Range calculation.
- Positive variance.
- Positive IQR.
- Positive MAD.
- Single-observation behavior.
- Empty-input rejection.
- Non-finite-input rejection.

The PostgreSQL implementation also validates database-level behavior through constraints, triggers, aggregate queries, report refresh logic, and a zero-mean dataset.

## Practical Distinctions

Dispersion is not synonymous with deviation from a target.

A dataset can have low dispersion while being consistently far from a desired target. Conversely, it can have high dispersion while its mean is close to the target.

The measures implemented here quantify spread within the observations. They do not by themselves establish whether the observed values are desirable, correct, or compliant with an external target.

Variance and standard deviation describe spread around the mean. IQR and MAD describe spread using median-based or percentile-based information. CV describes relative spread. Range describes the full observed interval.

These distinctions determine which measure is appropriate for a particular analytical decision.
