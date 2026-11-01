# Measures of Central Tendency

## Scope

This project implements six measures used to describe the center of a numerical dataset:

| Measure | Primary interpretation | Key condition |
|---|---|---|
| Mean | Arithmetic average | Values may be positive, zero, or negative |
| Median | Middle ordered observation | Values are ordered before selection |
| Mode | Most frequent observation | A dataset can have no mode or multiple modes |
| Weighted mean | Average adjusted by importance or frequency | Total weight must be positive |
| Geometric mean | Multiplicative average | Every value must be strictly positive |
| Harmonic mean | Reciprocal-based average | Every value must be strictly positive |

The implementations use repository-development metrics as realistic numerical data. Review durations, deployment multipliers, throughput rates, quality scores, and operational measurements illustrate why different measures can produce materially different descriptions of the same population.

The five source files are independent implementations of the same statistical domain. They are not translations of one another.

## Central Concept

A measure of central tendency attempts to represent a dataset with a central or typical value. The appropriate measure depends on the structure of the data and the question being asked.

For a dataset

`x₁, x₂, ..., xₙ`

the arithmetic mean is:

`mean = (x₁ + x₂ + ... + xₙ) / n`

The median is determined after sorting the observations. For an odd number of observations, it is the middle value. For an even number, it is the arithmetic mean of the two central observations.

The mode is the value or set of values with the highest frequency.

These three measures are not interchangeable. A highly skewed dataset can have a mean that is substantially larger than its median. A repeated operational value can create a meaningful mode even when the mean and median differ.

## Mean

The arithmetic mean treats every observation equally.

For example, review durations such as:

`2, 3, 3, 4, 5, 8, 40`

have a large observation at `40`. That observation pulls the arithmetic mean upward.

The mean is useful when all observations have comparable importance and extreme values are meaningful rather than erroneous. It is sensitive to outliers because every observation contributes directly to the sum.

The Python implementation uses `Decimal` arithmetic to reduce avoidable floating-point representation effects. The JavaScript, C++17, and Java implementations use floating-point arithmetic appropriate for their standalone executable examples.

The PostgreSQL implementation uses `NUMERIC` for stored observations and calculated values, providing decimal arithmetic suitable for reporting-oriented workloads.

## Median

The median depends on position rather than the magnitude of every observation.

For an odd number of ordered observations, the middle observation is selected. For an even number, the two middle observations are averaged.

For:

`2, 3, 3, 4, 5, 8, 40`

the median is `4`.

The extreme value `40` therefore has little effect on the median's location. This makes the median useful for skewed operational measurements such as review time, response time, delivery time, or processing duration.

The Python implementation sorts the values directly. The JavaScript implementation creates a copy before sorting so the caller's array is not modified. The C++ implementation uses `std::nth_element`, which avoids requiring a complete sort for median selection. The Java implementation explicitly creates and sorts a copy. PostgreSQL uses `percentile_cont(0.5)`.

## Mode

The mode identifies the most frequent observation.

A dataset can have:

- no mode when every value occurs once
- one mode when one value has the highest frequency
- multiple modes when several values share the highest frequency

The implementations return all tied modes rather than arbitrarily selecting one.

Frequency maps are used in Python, JavaScript, and Java. C++ uses `std::map`, which also provides ordered output. PostgreSQL calculates frequencies with `GROUP BY` and selects values whose frequency equals the maximum frequency.

Mode is particularly useful when repeated discrete observations have operational meaning. It is less useful for continuously measured data where exact repeated values may be rare.

## Weighted Mean

A weighted mean gives observations different levels of influence.

The formula is:

`weighted mean = Σ(xᵢwᵢ) / Σwᵢ`

A realistic quality evaluation might use:

| Score | Weight |
|---:|---:|
| 80 | 0.20 |
| 88 | 0.30 |
| 94 | 0.50 |

The score with weight `0.50` contributes more strongly than the score with weight `0.20`.

The implementations validate weights and reject negative weights. A total weight of zero is rejected because division by zero would make the measure undefined.

Weights can represent importance, frequency, sampling contribution, credit allocation, or another domain-specific basis for unequal influence. The meaning of a weight must be established by the application rather than inferred from the calculation itself.

## Geometric Mean

The geometric mean is appropriate for multiplicative quantities such as growth multipliers, ratios, and proportional changes.

For positive observations:

`geometric mean = (x₁ × x₂ × ... × xₙ)^(1/n)`

The implementations calculate it through logarithms:

`exp(average(log(x)))`

This approach avoids directly multiplying a large number of observations and reduces the risk of intermediate overflow.

Every observation must be strictly positive. Zero and negative observations are rejected.

For growth multipliers such as:

`1.02, 1.04, 1.06, 1.03`

the geometric mean represents a multiplicative central rate more naturally than the arithmetic mean.

## Harmonic Mean

The harmonic mean is defined as:

`harmonic mean = n / Σ(1/xᵢ)`

It is useful for positive rates where observations describe quantities such as speed, throughput, or rate-like measurements.

For example:

`30, 40, 50`

can be summarized with the harmonic mean when the domain requires a reciprocal-based average.

Zero and negative values are rejected because the reciprocal calculation would be undefined or outside the intended interpretation.

The harmonic mean is strongly influenced by small positive values. This property is useful when low rates should have greater influence on the resulting average.

## Relationship Between the Measures

For positive observations, the three classical means follow:

`harmonic mean ≤ geometric mean ≤ arithmetic mean`

Equality occurs when all observations are equal.

This relationship provides a useful validation property. It should not be interpreted as meaning that one measure is universally better than another. Each measure represents a different mathematical interpretation.

A useful decision structure is:

| Data characteristic | Suitable measure |
|---|---|
| Comparable numerical observations | Mean |
| Strong skew or extreme observations | Median |
| Repeated categorical or discrete value | Mode |
| Unequal observation importance | Weighted mean |
| Multiplicative growth or ratios | Geometric mean |
| Positive rates or reciprocal quantities | Harmonic mean |

## Realistic Operational Scenario

The examples model measurements commonly encountered in repository engineering and operational analytics.

A simplified data relationship is:

`Repository`
`    ↓`
`Operational observations`
`    ↓`
`Numerical measurements`
`    ↓`
`Central-tendency calculations`
`    ↓`
`Operational interpretation`

Review durations demonstrate the difference between mean and median when a small number of unusually long observations exist.

Deployment multipliers demonstrate why geometric averaging is appropriate for multiplicative quantities.

Throughput rates demonstrate why the harmonic mean can be preferable to the arithmetic mean when the measurements are rates.

Quality scores demonstrate weighted averaging when individual assessments do not have equal importance.

## Python Implementation

The Python source uses a `Dataset` dataclass to enforce a consistent representation of numerical observations.

`Decimal` is used for higher-precision decimal arithmetic. This is useful for reporting and educational calculations where binary floating-point representation can produce small representation artifacts.

The implementation separates:

- dataset validation
- basic measures
- weighted observations
- specialized means
- formatting
- demonstrations
- failure testing

`MeasureError` provides domain-specific validation failures.

The mode implementation stores frequencies in a dictionary and returns all modes tied at the maximum frequency.

The geometric and harmonic means explicitly validate positivity before calculation.

The script also includes assertions for core calculations and failure-condition demonstrations. It can be executed directly without external packages.

## JavaScript Implementation

The JavaScript source uses Node.js standard functionality and models the calculation service through a class.

`Map` is used for frequency counting, while `Set`-style collection behavior is represented through native collection operations where appropriate.

The implementation contains an asynchronous metric collection example. Values are resolved through promises and then passed to a running metric stream.

`RepositoryMetricsStream` maintains:

- the observations
- the running sum
- the current count

This allows the arithmetic mean to be maintained incrementally while the median and mode are calculated from retained observations.

Input validation rejects:

- empty datasets
- non-numeric observations
- non-finite numbers
- negative weights
- zero total weight
- non-positive values for geometric means
- non-positive values for harmonic means

Node's built-in `assert` module provides executable validation tests without external dependencies.

## C++17 Implementation

The C++17 source treats the problem as a numerical analytics engine.

The implementation uses:

- `enum class` for measure categories
- `struct` for weighted observations
- custom exceptions for domain failures
- STL containers for datasets
- `std::accumulate` for arithmetic totals
- `std::nth_element` for efficient median selection
- `std::map` for frequency counting
- standard mathematical functions for logarithmic calculations

The use of `std::nth_element` is a deliberate implementation choice. A complete sort is not necessary to identify the median, although an additional local operation is required for the lower middle value when the dataset size is even.

A repository governance metrics class records review and merge-related durations and exposes mean, median, and mode as operational summaries.

The program also demonstrates invalid geometric, harmonic, and weighted calculations and verifies basic results before terminating successfully.

## Java 17 Implementation

The Java implementation uses explicit domain modeling.

The `WeightedObservation` record validates numerical values and weights when instances are created.

`ReviewMetric` represents an operational review measurement with:

- reviewer identity
- review state
- review duration

The `ReviewState` enum distinguishes `OPEN`, `APPROVED`, `CHANGES_REQUESTED`, and `CLOSED`.

`CentralTendencyService` contains the statistical rules, while `ReviewAnalyticsService` owns a collection of operational review measurements and derives statistics from them.

Java streams are used for:

- averaging
- validation
- frequency processing
- positive-value validation
- reciprocal calculations

The measure results are exposed through an `EnumMap`, making the relationship between a measure type and its calculated value explicit.

This design separates statistical calculation from the enterprise domain that supplies the measurements.

## PostgreSQL Implementation

The PostgreSQL implementation models central-tendency calculations as a relational analytics workflow.

The schema contains:

- `dataset`
- `observation`
- `measure_result`
- `calculation_event`

`dataset` identifies a logical measurement collection.

`observation` stores individual numerical values and optional weights. A unique constraint prevents duplicate observation positions within a dataset.

`measure_result` stores calculated results and prevents duplicate measure records for the same dataset through a composite uniqueness constraint.

`calculation_event` records successful and rejected calculation outcomes.

The database uses `NUMERIC` instead of binary floating-point columns for stored measurements and calculated reporting values.

## PostgreSQL Functions

The SQL implementation contains separate functions for:

- arithmetic mean
- median
- mode
- weighted mean
- geometric mean
- harmonic mean

The median uses PostgreSQL's `percentile_cont` ordered-set aggregate.

The mode function uses grouped frequencies and identifies all values tied for maximum frequency.

The weighted mean function explicitly checks that the total weight is positive.

The geometric and harmonic mean functions explicitly reject datasets containing zero or negative values.

The geometric mean uses:

`EXP(AVG(LN(value)))`

The harmonic mean uses:

`COUNT(*) / SUM(1 / value)`

These expressions reflect the mathematical definitions while using PostgreSQL's numeric and aggregate capabilities.

## Transactional Workflow

The `refresh_measure_results` procedure calculates and persists multiple measures for a selected dataset.

The procedure uses `INSERT ... ON CONFLICT DO UPDATE` so repeated refreshes update existing results instead of producing duplicate rows.

Transactions surround refresh operations so a group of result updates can be committed atomically.

This is important when a reporting table must not expose a partially refreshed calculation set.

## Database-Level Validation

The database enforces several rules directly.

Examples include:

- non-empty dataset names
- non-negative weights
- valid measure names
- valid event statuses
- unique observation positions
- valid dataset references
- valid result references

Triggers create calculation events when result records are inserted or updated.

This makes the database more than a passive storage layer. It preserves structural invariants and records calculation activity.

## Reporting Queries

The database provides a dataset report containing:

- observation count
- mean
- median
- minimum
- maximum
- total

A separate weighted report exposes:

- total weight
- weighted total
- weighted mean

Additional queries demonstrate:

- mode extraction
- ordered observations
- median positions
- stored calculation results
- calculation-event aggregation

Indexes are limited to the dataset/value access pattern because unnecessary indexing would increase write cost without providing a clear analytical benefit.

## Edge Cases

The implementations explicitly address several failure conditions.

### Empty datasets

No central-tendency calculation can be performed without at least one observation. All executable implementations reject empty datasets.

### Non-finite values

The Python, JavaScript, C++, and Java implementations reject non-finite numerical input where their runtime exposes the necessary validation mechanisms.

### Zero total weight

A weighted mean with zero total weight is undefined and therefore rejected.

### Negative weights

The weighted implementations reject negative weights. A particular statistical model may permit signed coefficients in specialized applications, but that is not the weighting model used here.

### Zero values for geometric mean

Zero makes the logarithmic formulation invalid and is rejected.

### Negative values for geometric mean

Negative observations are outside the real-valued geometric mean model used here and are rejected.

### Zero values for harmonic mean

The reciprocal of zero is undefined, so zero is rejected.

### Negative values for harmonic mean

Negative observations are rejected because the implementation models positive rate-like quantities.

### No mode

When every observation has frequency one, the implementations report that there is no mode.

### Multiple modes

When several observations share the highest frequency, all tied modes are returned.

### Outliers

The review-duration example includes a large observation to demonstrate the different behavior of mean and median.

## Precision and Numerical Considerations

Central-tendency calculations can be affected by numerical representation.

Python uses `Decimal` for the main implementation.

PostgreSQL uses `NUMERIC`.

C++17 and Java use `double`, while JavaScript uses the standard JavaScript `number` type.

For large production datasets, numerical precision requirements should be determined before selecting the storage and computation types.

The geometric mean is calculated through logarithms rather than direct multiplication. This avoids unnecessary intermediate products that can overflow or underflow.

## Computational Complexity

For `n` observations:

| Operation | Typical complexity | Notes |
|---|---:|---|
| Mean | O(n) | One pass |
| Weighted mean | O(n) | One pass |
| Geometric mean | O(n) | One logarithm per observation |
| Harmonic mean | O(n) | One reciprocal per observation |
| Mode | O(n) expected | Frequency map |
| Median | O(n) to O(n log n) | Depends on selection or sorting strategy |

Memory usage depends on the implementation.

A streaming mean can be calculated with constant additional memory. Median and mode generally require retaining observations or frequency information unless a specialized external or streaming algorithm is introduced.

## Distinguishing the Measures

The six measures answer different questions.

Mean asks:

`What is the arithmetic balance point?`

Median asks:

`What observation lies at the center of the ordered population?`

Mode asks:

`Which observation occurs most frequently?`

Weighted mean asks:

`What is the arithmetic average after assigning unequal importance?`

Geometric mean asks:

`What multiplicative factor represents the observations centrally?`

Harmonic mean asks:

`What reciprocal-based average represents these positive rates?`

Selecting a measure should therefore follow the measurement model rather than convenience.

## Practical Interpretation

For skewed review-duration data, the median can describe a typical review more reliably than the mean.

For repeated discrete measurements, the mode can reveal the most common operational value.

For quality assessments with explicit importance weights, the weighted mean reflects the weighting policy.

For growth multipliers, the geometric mean preserves multiplicative interpretation.

For rate measurements such as throughput or speed, the harmonic mean accounts for reciprocal behavior.

These distinctions prevent a single averaging method from being applied indiscriminately to incompatible measurement types.
