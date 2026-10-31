# Statistics Fundamentals

## Scope

This project implements the foundations of statistical reasoning through a common numerical domain: a finite population of observations from which samples are selected and summarized.

The four central concepts are kept distinct:

| Concept | Meaning | Example in this project |
|---|---|---|
| Population | Complete collection under study | All 25 assessment scores |
| Sample | Observed subset selected from the population | 8 selected scores |
| Parameter | Numerical property of the population | Population mean |
| Statistic | Numerical property calculated from a sample | Sample mean |

The implementations cover population and sample construction, sampling, descriptive statistics, variance, standard deviation, median, mode, standard error, validation, persistence, and failure handling.

## Statistical Model

The domain relationship is:

    Population
        |
        +-- population units
        |
        +-- parameter
        |     +-- population mean
        |     +-- population variance
        |     +-- population standard deviation
        |
        +-- Sampling method
              |
              +-- Simple random sample
              +-- Systematic sample
              +-- Stratified sample
                    |
                    +-- Sample
                          |
                          +-- statistic
                                +-- sample mean
                                +-- sample variance
                                +-- sample standard deviation
                                +-- standard error

The distinction between parameter and statistic is fundamental. A population parameter describes the complete population. A statistic is calculated from observed sample data and can be used to estimate a population parameter.

## Population

The population is represented by 25 numerical observations ranging from 61 to 92.

The Python implementation uses the immutable `Population` dataclass. The JavaScript implementation stores the population in a validated array managed by `StatisticsPipeline`. C++ uses a `std::vector<double>`, while Java uses the immutable `Population` record.

The PostgreSQL model separates the population definition from its individual population units. This permits relational constraints, indexed retrieval, grouping by strata, and reproducible statistical queries.

A population is not necessarily every object existing in the world. It is the complete set defined by the statistical question. A study about a specific examination cohort, production batch, or transaction period can therefore have a finite population with a precise boundary.

## Sample

A sample is a subset selected from a population.

The project implements three sampling perspectives:

| Sampling method | Mechanism | Main characteristic |
|---|---|---|
| Simple random | Randomly selects units | Each population unit can be selected without deterministic ordering |
| Systematic | Selects observations at a fixed interval | Efficient when an ordered population is available |
| Stratified | Samples separately within groups | Preserves representation of defined subgroups |

The Python implementation demonstrates all three. The JavaScript implementation focuses on simple random and systematic selection. C++ focuses on deterministic reproducible random sampling and systematic selection. PostgreSQL stores sample membership explicitly through `sample_units`.

Sample size is validated against the population size. Empty samples are rejected because statistics such as the mean cannot be computed from zero observations.

Sampling introduces uncertainty. A sample statistic can differ from the corresponding population parameter even when the sampling process is valid.

## Parameter and Statistic

The population mean is a parameter:

`μ = Σxᵢ / N`

where `N` is the population size.

The sample mean is a statistic:

`x̄ = Σxᵢ / n`

where `n` is the sample size.

For the supplied population, the complete population mean is the reference parameter. A selected sample produces its own mean, which is an estimate of that parameter.

The implementations intentionally print both values so the distinction is observable rather than only defined conceptually.

A parameter generally cannot be replaced by a statistic without acknowledging sampling uncertainty. A statistic is calculated from observed data; a parameter describes the target population.

## Descriptive Statistics

Descriptive statistics reduce a collection of observations to interpretable numerical summaries.

The project calculates:

- Count
- Minimum
- Maximum
- Mean
- Median
- Mode
- Population variance
- Population standard deviation
- Sample variance
- Sample standard deviation
- Standard error of the sample mean

### Mean

The arithmetic mean is sensitive to every observation and is therefore useful for numerical data when extreme values do not dominate the interpretation.

The implementations use direct summation and division by the appropriate number of observations.

Population variance divides by `N`:

`σ² = Σ(xᵢ - μ)² / N`

Sample variance divides by `n - 1`:

`s² = Σ(xᵢ - x̄)² / (n - 1)`

The distinction matters. Using the population denominator for a sample changes the variance estimate.

### Median

The median is the central ordered observation.

For an odd number of observations, it is the middle value. For an even number, it is the arithmetic mean of the two middle values.

Python uses `statistics.median`. JavaScript, C++, and Java explicitly sort the observations before identifying the middle position. PostgreSQL uses ordered-set aggregation with `percentile_cont(0.5)`.

Median computation requires ordering. The explicit sorting implementations therefore have `O(n log n)` time complexity.

### Mode

The mode is the most frequently occurring value.

The implementations construct frequency maps and return every value tied for the highest frequency. This avoids assuming that a dataset must have exactly one mode.

A dataset can therefore be:

- Unimodal
- Multimodal
- Constant
- Free of a meaningful repeated value

The project treats the highest observed frequency as the operational definition of mode.

## Variance and Standard Deviation

Variance measures average squared deviation from the mean.

Squaring prevents positive and negative deviations from cancelling and gives larger deviations greater weight.

Standard deviation is the square root of variance, returning the measure to the original unit of the observations.

The project keeps population and sample calculations separate:

| Quantity | Denominator |
|---|---:|
| Population variance | `N` |
| Sample variance | `n - 1` |
| Population standard deviation | `sqrt(population variance)` |
| Sample standard deviation | `sqrt(sample variance)` |

Sample variance requires at least two observations. Every implementation explicitly rejects a one-element sample when sample variance is requested.

## Standard Error

The standard error of the sample mean is calculated as:

`SE(x̄) = s / sqrt(n)`

where `s` is the sample standard deviation.

Standard deviation describes variation among observations. Standard error describes the estimated variability of the sample mean across repeated samples under the corresponding sampling assumptions.

The distinction prevents two different quantities from being treated as interchangeable.

## Python Implementation

The Python file models statistical entities with `dataclass` types.

`Population` validates the complete population. `Sample` records both selected values and the population size. `DescriptiveStatistics` stores calculated results as one structured object.

The statistical functions are deliberately separated:

- `population_variance` calculates variance using `N`.
- `sample_variance` calculates variance using `n - 1`.
- `describe` combines descriptive measures.
- `simple_random_sample` performs seeded random selection.
- `systematic_sample` selects observations at a calculated interval.
- `stratified_sample` samples independently within named strata.
- `standard_error_of_mean` calculates uncertainty of the sample mean.

The script also writes a statistics record to a temporary CSV file. Assertions verify core results, while invalid sample sizes and invalid variance requests demonstrate explicit failure handling.

Seeded sampling makes examples reproducible. Production sampling should use an appropriate source of randomness when predictability would create a security or study-design problem.

## JavaScript Implementation

The JavaScript implementation uses a different architecture centered on an event-driven `StatisticsPipeline`.

`Map` is used for frequency counting, while `EventEmitter` separates statistical calculation from reporting and export events.

The pipeline emits:

- `statistics` after a sample has been analyzed
- `exported` after JSON output has been written

The implementation uses Node.js standard-library modules only. A seeded pseudo-random generator provides deterministic demonstrations without external packages.

The JSON export uses a temporary operating-system directory. This keeps generated files outside the source tree and avoids hard-coded filesystem assumptions.

Validation is represented by a custom `StatisticsError`, allowing expected domain failures to be distinguished from unexpected runtime failures.

## C++17 Implementation

The C++ implementation uses a `StatisticsEngine` with static operations over `std::vector<double>`.

The design emphasizes explicit numerical operations and STL algorithms:

- `std::accumulate` calculates totals.
- `std::sort` supports median calculation.
- `std::shuffle` performs seeded random sampling.
- `std::map` stores value frequencies.
- `std::min_element` and `std::max_element` identify range boundaries.

The C++ program treats invalid numerical values as domain errors and propagates them through `std::invalid_argument`.

The architecture also makes computational cost visible. Mean, variance, range, and frequency construction are linear in the number of observations. Median requires sorting and is `O(n log n)` in this implementation. Random sampling through shuffling is also linear after the population has been copied.

## Java 17 Implementation

The Java implementation uses records to model immutable population, sample, and statistics data.

The domain types are:

- `Population`
- `Sample`
- `DescriptiveStatistics`

`StatisticsException` represents invalid statistical operations.

Java streams are used for mean calculation and frequency grouping. `TreeMap` provides ordered frequency keys, making returned modes deterministic.

The implementation explicitly separates population variance from sample variance. A `Double` is used for sample variance in the statistics record because a single observation cannot produce a valid sample variance.

The design is suitable for an enterprise service layer because validation, domain state, calculation, and presentation are separated into named methods rather than being concentrated in `main`.

## PostgreSQL Relational Model

The database models the statistical domain as related entities.

    populations
         |
         +---- population_units
         |
         +---- samples
                  |
                  +---- sample_units
                           |
                           +---- descriptive_statistics
                           |
                           +---- sampling_audit

`populations` defines the study population.

`population_units` stores individual observations and optional strata.

`samples` records the sampling method and requested size.

`sample_units` creates the many-to-many-style membership relationship between samples and population observations while preventing duplicate selection within a sample.

`descriptive_statistics` stores computed results for reporting.

`sampling_audit` records sample creation events.

## Database Constraints

Important statistical invariants are enforced at database level.

Primary keys identify every entity. Foreign keys prevent orphaned sample membership and statistics. Unique constraints prevent duplicate population unit keys and duplicate sample positions.

Check constraints reject:

- Empty population names
- Non-positive sample sizes
- Invalid selection positions
- A sample associated with fewer valid observations than required

A trigger validates the requested sample size against the current population size before a sample is inserted.

This is important because application-level validation alone does not protect a database from other clients or concurrent application paths.

## PostgreSQL Statistical Queries

The database demonstrates several statistical operations.

`avg` calculates means.

`var_pop` calculates population variance.

`var_samp` calculates sample variance.

`stddev_pop` calculates population standard deviation.

`stddev_samp` calculates sample standard deviation.

`percentile_cont(0.5)` calculates the continuous median.

Window functions provide ordered row positions for the reusable median calculation in the stored function.

The views `population_statistics` and `sample_statistics` provide reporting-oriented interfaces without duplicating the underlying population and sample data.

## Transactional Sampling

Sample creation and sample membership insertion are performed within a transaction.

The workflow is:

    BEGIN
      create sample
      select population units
      record sample membership
      calculate descriptive statistics
    COMMIT

If an operation fails before commit, the transaction can be rolled back so a partially created sample is not presented as valid statistical data.

The final failure demonstration uses a savepoint so an intentionally invalid sample-size operation can be observed without making the complete SQL script fail.

## Validation and Failure Modes

The implementations deliberately reject invalid states.

| Failure | Reason |
|---|---|
| Empty population | No statistical observation exists |
| Empty sample | No sample statistic can be calculated |
| Sample larger than population | Invalid selection |
| One-observation sample variance | `n - 1` becomes zero |
| Non-finite numeric value | Invalid numerical input |
| Unknown stratum | Sampling request does not match population structure |
| Duplicate sample unit | Same population observation cannot occupy two sample positions in one sample |

Validation is implemented at multiple layers. Source programs reject invalid input before calculation, while PostgreSQL constraints and triggers protect persistent data.

## Sampling and Representation

Simple random sampling is appropriate when each population unit should have a controlled random-selection opportunity.

Systematic sampling is operationally efficient when observations are arranged in a meaningful sequence and a fixed interval is acceptable.

Stratified sampling is useful when the population contains meaningful subgroups and the sampling design requires explicit representation of those groups.

These methods are not interchangeable. A valid sampling design depends on how the population is defined, ordered, grouped, and accessed.

## Performance Considerations

For `n` observations:

| Operation | Typical implementation cost |
|---|---:|
| Count | `O(n)` in in-memory implementations |
| Mean | `O(n)` |
| Variance | `O(n)` |
| Minimum / maximum | `O(n)` |
| Frequency counting | `O(n)` expected with hash-based maps |
| Median by sorting | `O(n log n)` |
| Simple random sampling by shuffle | `O(n)` |
| Systematic sampling | `O(n)` for validation and `O(k)` selection after population access |

For very large datasets, storing every observation in application memory may be inappropriate. The PostgreSQL implementation demonstrates a database-oriented approach where aggregation can be performed close to the stored data.

Numerical precision also matters for large or highly variable datasets. Production systems may require careful numeric types, stable aggregation strategies, and explicit handling of missing or invalid observations.

## Security and Data Integrity

Statistical calculations can be technically correct while the underlying data is wrong or improperly controlled.

The project therefore treats validation and integrity as part of the statistical workflow.

Database foreign keys prevent references to nonexistent population units. Check constraints prevent structurally invalid records. Transactions prevent partially committed sampling workflows.

The source implementations avoid dynamic code execution and do not require external packages for their core calculations.

When statistical data contains sensitive records, access control, auditing, encryption, retention rules, and controlled export must be handled at the surrounding application and database layers. The statistical formulas themselves do not provide privacy protection.

## Practical Interpretation

A descriptive statistic is only meaningful relative to the data collection design.

A sample mean that differs from the population mean is not automatically an error. Sampling variation naturally produces different statistics from different samples.

Similarly, a large standard deviation does not indicate that the calculation failed. It indicates greater dispersion in the observations.

Interpretation should therefore keep three questions separate:

1. What population is being studied?
2. How was the sample selected?
3. What statistic was calculated from the selected observations?

Those questions connect population definition, sampling design, and descriptive analysis without treating them as the same concept.

## File Responsibilities

| File | Primary responsibility |
|---|---|
| Python | Statistical model, multiple sampling methods, validation, CSV persistence, assertions |
| JavaScript | Event-driven statistics pipeline, seeded sampling, validation, JSON export |
| C++17 | STL-based numerical engine, explicit algorithms, deterministic sampling, exception handling |
| Java 17 | Immutable enterprise-style domain model, records, streams, service methods, validation |
| PostgreSQL | Relational statistical model, constraints, triggers, views, functions, transactions, reporting |

## Operational Workflow

    Define population
          |
          v
    Validate observations
          |
          v
    Select sampling method
          |
          v
    Create sample
          |
          v
    Validate sample membership
          |
          v
    Calculate descriptive statistics
          |
          +----> Sample statistic
          |
          +----> Sampling standard error
          |
          v
    Compare with population parameter
          |
          v
    Persist or report results

The workflow preserves the distinction between the population, the sample, the numerical characteristics of each, and the uncertainty introduced by sampling.
