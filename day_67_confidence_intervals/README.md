# Confidence Intervals

## 1. Scope

This project implements statistical estimation and uncertainty quantification across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The implementations cover four related but distinct areas:

1. Point estimates.
2. Confidence intervals.
3. Margin of error and sample-size planning.
4. Bootstrap percentile intervals.

The central objective is to estimate population parameters from sample observations while explicitly representing uncertainty.

The implementations use a website response-time dataset and a marketing conversion dataset. The response-time observations demonstrate estimation of a population mean. The conversion observations demonstrate estimation of a population proportion.

## 2. Statistical foundations

### Point estimates

A point estimate is a single numerical value calculated from sample data to estimate an unknown population parameter.

For observations \(x_1,x_2,\ldots,x_n\), the sample mean is:

\[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\]

The sample variance is:

\[
s^2=\frac{1}{n-1}
\sum_{i=1}^{n}(x_i-\bar{x})^2
\]

The sample standard deviation is:

\[
s=\sqrt{s^2}
\]

The denominator \(n-1\) applies Bessel's correction when estimating population variance from a sample.

For a binary outcome, the sample proportion is:

\[
\hat{p}=\frac{x}{n}
\]

Where:

- \(x\) is the number of observed successes.
- \(n\) is the number of trials.
- \(\hat p\) is the estimated success probability.

A point estimate does not communicate how uncertain the estimate is. Confidence intervals address that limitation.

### Confidence intervals

A confidence interval is an interval produced by a statistical procedure intended to capture an unknown population parameter with a specified long-run frequency.

The general form is:

\[
\text{Point Estimate}\pm\text{Margin of Error}
\]

For a 95% confidence procedure, approximately 95% of intervals constructed from repeated independent samples under the model assumptions would contain the fixed population parameter.

A 95% confidence interval does not mean that there is a 95% probability that a fixed population parameter lies inside one already calculated interval.

The confidence level describes the repeated-sampling behavior of the procedure.

### Standard error

Standard error measures the estimated variability of a statistic across repeated samples.

For the sample mean:

\[
SE(\bar{x})=\frac{s}{\sqrt{n}}
\]

When the population standard deviation \(\sigma\) is known:

\[
SE(\bar{x})=\frac{\sigma}{\sqrt{n}}
\]

For a sample proportion, the estimated standard error is:

\[
SE(\hat p)=
\sqrt{\frac{\hat p(1-\hat p)}{n}}
\]

Standard error is different from sample standard deviation. Standard deviation describes the dispersion of individual observations. Standard error describes the uncertainty of an estimated statistic.

## 3. Normal confidence intervals

When the population standard deviation is known, a normal confidence interval for a population mean is:

\[
\bar{x}\pm z_{\alpha/2}
\frac{\sigma}{\sqrt n}
\]

Where:

- \(\bar{x}\) is the sample mean.
- \(z_{\alpha/2}\) is the standard normal critical value.
- \(\sigma\) is the population standard deviation.
- \(n\) is the sample size.

When the population standard deviation is unknown, substituting the sample standard deviation and using a normal critical value is an approximation.

The Python, JavaScript, C++17, and Java 17 implementations provide this calculation. Their normal critical-value functions use a rational approximation to the inverse standard normal distribution.

The PostgreSQL implementation provides the same calculation through database functions.

A normal interval is useful when the population standard deviation is known or when a sufficiently accurate large-sample approximation is justified.

## 4. Student's t confidence intervals

When the population standard deviation is unknown, a Student's t interval is generally more appropriate for estimating a population mean under the assumptions of independent observations and an approximately normal sampling distribution.

Its formula is:

\[
\bar{x}\pm t_{\alpha/2,n-1}
\frac{s}{\sqrt n}
\]

The t distribution accounts for the additional uncertainty associated with estimating the population standard deviation.

Its tails are heavier than those of the standard normal distribution, particularly at small sample sizes.

As the degrees of freedom increase, the t distribution approaches the standard normal distribution.

The implementations include a table of two-sided 95% critical values for degrees of freedom from 1 through 30. Larger degrees of freedom use the normal approximation.

The t-table implementation deliberately restricts its supported confidence level to 95%. It should not be treated as a complete arbitrary-confidence Student's t quantile implementation.

## 5. Confidence intervals for proportions

The basic Wald interval for a population proportion is:

\[
\hat p\pm z_{\alpha/2}
\sqrt{\frac{\hat p(1-\hat p)}{n}}
\]

This method can produce poor coverage, particularly with small samples or proportions near zero and one. It can also produce bounds outside the valid probability range.

The implementations use the Wilson score interval instead.

Its denominator is:

\[
D=1+\frac{z^2}{n}
\]

Its center is:

\[
C=
\frac{\hat p+\frac{z^2}{2n}}{D}
\]

Its adjustment is:

\[
A=
\frac{z}{D}
\sqrt{
\frac{\hat p(1-\hat p)}{n}
+
\frac{z^2}{4n^2}
}
\]

The interval is:

\[
[C-A,C+A]
\]

The bounds are constrained to the probability range from zero to one.

The Wilson method is demonstrated using 735 conversions from 1,000 trials.

It also handles important edge cases:

- Zero successes.
- All successes.
- Small trial counts.
- Proportions close to zero.
- Proportions close to one.

## 6. Margin of error

The margin of error represents the distance from the point estimate to either bound of a symmetric confidence interval.

For a normal mean interval:

\[
MOE=z_{\alpha/2}\frac{\sigma}{\sqrt n}
\]

The margin of error is affected by three factors:

| Factor | Effect |
|---|---|
| Confidence level | Higher confidence increases the critical value and interval width. |
| Population variability | Higher standard deviation increases uncertainty. |
| Sample size | Larger samples reduce standard error. |

The margin of error decreases proportionally to the inverse square root of sample size.

For example, quadrupling the sample size approximately halves the margin of error, assuming the other inputs remain unchanged.

The implementations expose reusable functions for calculating the margin of error from a standard deviation, sample size, and confidence level.

## 7. Required sample size

Sample-size planning determines how many observations are needed to achieve a target margin of error.

For a normal mean interval:

\[
n=
\left(
\frac{z_{\alpha/2}\sigma}{E}
\right)^2
\]

Where:

- \(E\) is the desired margin of error.
- \(\sigma\) is the assumed population standard deviation.
- \(z_{\alpha/2}\) is the critical value.

The result must be rounded upward because a fractional observation cannot be collected.

For a standard deviation of 10, a desired margin of error of 2, and 95% confidence:

\[
n=
\left(
\frac{1.959964\times10}{2}
\right)^2
\]

The required sample size is 97.

This calculation assumes an appropriate sampling design and a sufficiently reliable estimate of population variability.

It does not automatically account for nonresponse, clustering, finite population corrections, or other complex survey-design effects.

## 8. Bootstrap confidence intervals

Bootstrap estimation uses repeated sampling with replacement from the observed dataset.

It provides an empirical approach to estimating the sampling distribution of a statistic.

### Bootstrap workflow

The implemented percentile procedure follows these stages:

1. Validate the original sample.
2. Set the number of bootstrap repetitions.
3. Initialize a reproducible random-number generator.
4. Draw a sample of the original size with replacement.
5. Calculate the selected statistic.
6. Repeat the sampling process.
7. Sort the bootstrap estimates.
8. Extract the lower and upper empirical percentiles.

For a confidence level \(1-\alpha\), the percentile interval is:

\[
[
Q_{\alpha/2},
Q_{1-\alpha/2}
]
\]

Where \(Q_p\) is the empirical p-th percentile of bootstrap estimates.

The implementations use 5,000 bootstrap repetitions in their main demonstrations.

A fixed seed supports reproducibility.

### Bootstrap statistics

The Python implementation accepts a callable statistic, allowing the same bootstrap engine to calculate intervals for different statistics, including:

- Mean.
- Median.
- Other user-defined numerical statistics.

The JavaScript, C++17, Java 17, and PostgreSQL implementations demonstrate bootstrap resampling of the sample mean.

### Bootstrap limitations

Bootstrap intervals are not automatically reliable for every dataset.

Potential limitations include:

- Very small samples.
- Strong dependence between observations.
- Poor representation of population tails.
- Highly skewed or discontinuous statistics.
- Rare events that are absent from the observed sample.

The percentile interval is not the only bootstrap method. Basic, studentized, and bias-corrected and accelerated intervals use different procedures and can have different coverage properties.

For dependent observations, methods such as block bootstrap may be more appropriate than ordinary independent resampling.

## 9. Dataset and analysis workflow

The project uses two example datasets.

### Website response times

The response-time sample contains 15 numerical observations measured in milliseconds.

It is used to calculate:

- Sample mean.
- Sample variance.
- Sample standard deviation.
- Normal mean confidence interval.
- Student's t confidence interval.
- Bootstrap percentile interval.

The sample illustrates the estimation of a continuous population parameter.

### Marketing conversion

The conversion dataset contains:

| Measure | Value |
|---|---:|
| Successful conversions | 735 |
| Total trials | 1,000 |
| Estimated conversion rate | 0.735 |
| Confidence level | 95% |

It demonstrates Wilson proportion estimation.

### Processing sequence

The common workflow is:

Observation collection
→ Input validation
→ Point estimation
→ Standard error estimation
→ Critical value selection
→ Confidence interval calculation
→ Margin-of-error calculation
→ Validation
→ Reporting

The PostgreSQL implementation additionally persists observations, analysis runs, and interval results.

## 10. Python implementation

The Python script uses standard-library modules rather than external statistical packages.

| Component | Responsibility |
|---|---|
| `ConfidenceInterval` | Immutable interval representation. |
| `IntervalMethod` | Identifies the calculation method. |
| `validate_sample()` | Checks observation counts and numerical values. |
| `normal_critical_value()` | Calculates normal critical values. |
| `normal_mean_interval()` | Estimates normal mean intervals. |
| `t_mean_interval()` | Estimates Student's t intervals. |
| `proportion_interval()` | Calculates Wilson intervals. |
| `bootstrap_interval()` | Performs percentile bootstrap estimation. |
| `required_sample_size()` | Plans sample sizes. |
| `save_results()` | Exports results to JSON. |

The dataclass makes interval results explicit and immutable.

The bootstrap function accepts a statistic argument, separating the resampling mechanism from the statistic being estimated.

The random generator is initialized with a seed to support reproducible results.

The test function checks interval ordering, proportion boundaries, bootstrap behavior, sample-size calculations, and invalid inputs.

The implementation has no external dependency requirements.

## 11. JavaScript implementation

The JavaScript file provides an event-driven analysis perspective using Node.js.

It uses:

- Classes for deterministic random-number generation.
- Objects for interval results.
- Arrays for bootstrap estimates.
- Promises for concurrent campaign processing.
- `Promise.all()` for coordinated asynchronous execution.
- Node.js file APIs for JSON report export.
- `crypto.randomUUID()` for identifying analysis runs.

The `RandomGenerator` class isolates bootstrap random-number state.

The campaign-analysis function calculates Wilson intervals independently for multiple campaigns.

Concurrent calculations are collected into a map keyed by campaign identifier.

Validation errors and analysis errors are represented by separate exception classes.

The asynchronous workflow is useful when an application needs to process multiple independent statistical reports without coupling their calculation logic.

The built-in pseudorandom generator is suitable for reproducible statistical simulation, not for cryptographic security.

## 12. C++17 implementation

The C++17 program uses an object-oriented statistical engine.

The `ConfidenceInterval` structure stores:

- Point estimate.
- Lower bound.
- Upper bound.
- Confidence level.
- Margin of error.
- Calculation method.
- Sample size.

The `ConfidenceIntervalEngine` class centralizes statistical calculations and input validation.

STL vectors store samples and bootstrap estimates. Sorting supports percentile extraction, while standard algorithms support numerical aggregation.

The bootstrap procedure uses `std::mt19937` with a supplied seed.

The implementation also checks sample-size overflow before converting the required count to `size_t`.

The design keeps statistical computation separate from presentation and test execution.

No external C++ libraries are required.

## 13. Java 17 implementation

The Java implementation models confidence interval analysis as an enterprise statistical service.

Its main domain types include:

| Type | Purpose |
|---|---|
| `ConfidenceInterval` | Immutable calculation result. |
| `Campaign` | Validated conversion-study input. |
| `Method` | Statistical method classification. |
| `AnalysisException` | Calculation-related failure. |

Java records provide immutable domain objects with constructor validation.

The campaign-processing service uses `CompletableFuture` to execute independent campaign calculations concurrently.

A sorted map produces deterministic reporting order.

The implementation validates campaign identifiers, sample sizes, proportions, confidence levels, and numerical values.

The statistical calculation layer remains independent of the concurrent reporting layer.

This separation is useful in systems where statistical computations form part of a larger reporting or analytics service.

## 14. PostgreSQL implementation

The SQL script models a persistent statistical-analysis workflow.

It uses a dedicated `statistics_lab` schema.

### Relational structure

The principal relationships are:

Study
→ Observation Group
→ Observations
→ Analysis Run
→ Interval Result

Proportion observations are stored separately because they represent successes and trials rather than individual continuous measurements.

### Database objects

| Object | Purpose |
|---|---|
| `study` | Stores study metadata. |
| `observation_group` | Defines individual analytical datasets. |
| `observation` | Stores continuous numerical observations. |
| `proportion_observation` | Stores binomial counts. |
| `analysis_run` | Tracks calculation configuration and execution state. |
| `interval_result` | Persists calculated interval outputs. |
| `confidence_interval_report` | Provides consolidated analytical reporting. |

### Integrity enforcement

Primary keys identify records.

Foreign keys enforce relationships between studies, groups, observations, and analysis runs.

Unique constraints prevent duplicate study codes and group codes within a study.

Check constraints enforce valid confidence levels, positive trial counts, valid success counts, and valid interval boundaries.

Indexes support retrieval by group, observation time, value, analysis status, and result identifier.

### Database functions

The SQL implementation includes:

- `inverse_normal_cdf()`
- `normal_critical_value()`
- `point_mean()`
- `point_sample_variance()`
- `student_t_critical_95()`
- `calculate_mean_interval()`
- `calculate_wilson_interval()`
- `calculate_margin_of_error()`
- `calculate_required_sample_size()`
- `calculate_bootstrap_interval()`

The normal inverse function uses a rational approximation.

The Student's t function uses tabulated 95% critical values for smaller degrees of freedom and a normal approximation for larger samples.

### Analysis lifecycle

The database uses four analysis states:

| State | Meaning |
|---|---|
| `CREATED` | Analysis has been registered. |
| `RUNNING` | Calculation has started. |
| `COMPLETED` | Result has been persisted. |
| `FAILED` | Calculation has failed. |

The state-management trigger prevents terminal states from being reopened through ordinary updates.

The `execute_analysis()` procedure locks the analysis-run record, validates its state, calculates the requested interval, and persists the result.

A transaction protects the analysis operation. If the calculation fails, the procedure records failure information and rethrows the exception so the calling transaction can handle the failure.

The procedure supports normal, Student's t, Wilson, and bootstrap calculations.

### Bootstrap implementation in PostgreSQL

The database bootstrap function creates repeated samples using a deterministic private pseudorandom-number sequence.

It stores the bootstrap estimates, sorts them, and extracts interpolated empirical percentiles.

Its computational cost increases with both sample size and repetition count.

The implementation is intended for educational and moderate-sized analytical workloads. Large-scale bootstrap workloads are generally better processed in a dedicated statistical execution service.

## 15. Method comparison

| Method | Parameter | Main requirement | Important limitation |
|---|---|---|---|
| Normal mean | Population mean | Known population SD or justified approximation | Approximation may be weak for small samples. |
| Student's t | Population mean | Independent observations and appropriate sampling distribution | Current implementations use a limited 95% t table. |
| Wilson | Population proportion | Binomial sampling model | Does not automatically account for clustered observations. |
| Percentile bootstrap | Selected statistic | Representative sample and suitable resampling design | Can perform poorly with small or dependent samples. |

Method selection must reflect the parameter being estimated, the sampling process, and the assumptions of the statistical model.

A proportion interval should not be substituted for a continuous mean interval. A bootstrap interval should not be interpreted as automatically assumption-free.

## 16. Edge cases and failure handling

The implementations explicitly address the following conditions:

| Condition | Handling |
|---|---|
| Empty sample | Rejected. |
| One observation for mean intervals | Rejected. |
| NaN observations | Rejected. |
| Infinite observations | Rejected. |
| Confidence level outside (0, 1) | Rejected. |
| Negative standard deviation | Rejected. |
| Zero sample size | Rejected. |
| Zero trials | Rejected. |
| Successes greater than trials | Rejected. |
| Bootstrap repetitions below 100 | Rejected. |
| Non-finite bootstrap statistic | Rejected where supported. |
| Invalid interval bounds | Rejected. |
| Excessive sample-size calculation | Overflow checked where supported. |

These checks prevent invalid calculations from silently entering reports.

## 17. Performance considerations

For a sample of size \(n\):

| Operation | Typical complexity |
|---|---|
| Mean | \(O(n)\) |
| Sample variance | \(O(n)\) |
| Standard error | \(O(n)\) when calculated from raw observations |
| Normal interval | \(O(n)\) including estimation |
| Wilson interval | \(O(1)\) |
| Bootstrap with \(B\) repetitions | \(O(Bn)\) |
| Bootstrap percentile sorting | \(O(B\log B)\) |
| Required sample size | \(O(1)\) |

Bootstrap estimation is generally the most computationally expensive operation.

The Python and JavaScript implementations retain bootstrap estimates in memory.

The C++ implementation reserves vector capacity before generating estimates.

The Java implementation reuses the bootstrap sample collection.

The PostgreSQL implementation performs repeated sampling and percentile sorting inside the database.

For large production datasets, bootstrap repetitions can be parallelized or processed in batches, provided the random-number streams are managed carefully and the resulting procedure remains statistically valid.

## 18. Security and data governance

Statistical observations can contain commercially sensitive or personally identifiable information.

Production systems should apply:

- Role-based database access.
- Least-privilege permissions.
- Restricted access to raw observations.
- Secure report storage.
- Parameterized database operations.
- Audit records for analysis configuration.
- Controlled retention and deletion policies.
- Protection of exported analytical datasets.

Analysis identifiers and metadata should not expose confidential observation values unnecessarily.

Random seeds support reproducibility but should not be treated as security credentials.

## 19. Interpretation and practical limitations

Confidence intervals describe uncertainty under a statistical procedure. They do not correct poor data collection.

Important sources of uncertainty include:

- Sampling variability.
- Measurement error.
- Selection bias.
- Nonresponse.
- Missing observations.
- Dependence between observations.
- Model misspecification.
- Distributional assumptions.

A narrow confidence interval does not guarantee an unbiased estimate.

A large sample can produce a narrow interval around a biased estimate if the sampling process is systematically distorted.

Likewise, a 95% confidence interval does not mean that 95% of individual observations fall inside its bounds.

Confidence intervals should be reported together with the point estimate, sample size, confidence level, calculation method, and relevant assumptions.

For business reporting, a confidence interval for a conversion rate should be distinguished from an interval for the difference between two conversion rates. Comparing two separate intervals is not a substitute for a direct statistical analysis of the difference.

The same distinction applies to comparisons between average response times, experimental groups, and other population parameters.

## 20. Execution requirements

| Deliverable | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Node.js built-in modules |
| C++17 | C++17 compiler | Standard library |
| Java | Java 17 | Standard library |
| PostgreSQL | PostgreSQL 14+ | PostgreSQL built-in capabilities |

The source implementations are independent. Each can execute its own statistical workflow without requiring another language implementation.

The PostgreSQL script creates its own schema and analytical objects. Its objects are scoped to `statistics_lab`, and its sample data uses stable business identifiers to prevent duplicate seed records.

The PostgreSQL script should be executed with a database account authorized to create schemas, tables, functions, procedures, triggers, and views.
