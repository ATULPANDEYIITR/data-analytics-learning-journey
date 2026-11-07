# Hypothesis Testing and Statistical Decision Engine

## Project Overview

This project implements hypothesis testing as a reproducible statistical decision process across Python, JavaScript, C++17, Java 17, and PostgreSQL.

It examines whether observed sample evidence provides sufficient statistical support to reject a specified null hypothesis.

The implementations cover statistical assumptions, test statistics, p-values, significance thresholds, decision rules, Type I and Type II errors, statistical power, confidence intervals, and multiple-hypothesis testing.

Each language provides a different implementation perspective:

| Implementation | Primary responsibility |
|---|---|
| Python | Statistical analysis, probability calculations, and reporting |
| JavaScript | Event-driven experiment execution and two-proportion testing |
| C++17 | Efficient statistical calculation and decision processing |
| Java 17 | Enterprise experiment lifecycle and Welch testing |
| PostgreSQL | Persistent experiment records, evaluation, and audit reporting |

## 1. Statistical Foundations

### 1.1 Population and Sample

A population represents the complete set of observations under investigation.

A sample is a subset collected to estimate population characteristics.

Important statistical quantities include:

| Quantity | Meaning |
|---|---|
| Population mean | Average of the entire population |
| Sample mean | Average of observed sample values |
| Population variance | Dispersion across the population |
| Sample variance | Estimated population dispersion |
| Standard deviation | Square root of variance |
| Standard error | Estimated variability of a sample statistic |
| Sample size | Number of observations |

For a sample containing \(n\) observations:

\[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\]

The sample variance is:

\[
s^2=\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}
\]

The standard error of the sample mean is:

\[
SE=\frac{s}{\sqrt{n}}
\]

When population standard deviation is known:

\[
SE=\frac{\sigma}{\sqrt{n}}
\]

The distinction between population standard deviation and sample standard deviation determines which statistical test is appropriate.

## 2. Null and Alternative Hypotheses

Hypothesis testing starts with two competing statements about a population parameter.

### 2.1 Null Hypothesis

The null hypothesis, denoted by \(H_0\), represents the reference condition being evaluated.

It commonly expresses:

- Equality between population means.
- Equality between population proportions.
- No difference between experimental groups.
- No association between variables.
- No effect of an intervention.

Example:

\[
H_0:\mu=50
\]

This states that the population mean equals 50.

### 2.2 Alternative Hypothesis

The alternative hypothesis, denoted by \(H_1\) or \(H_a\), represents the departure from the null hypothesis being investigated.

Three common alternatives are supported.

| Alternative | Mathematical expression | Interpretation |
|---|---|---|
| Two-sided | \(\mu\neq\mu_0\) | Any difference |
| Greater | \(\mu>\mu_0\) | Positive difference |
| Less | \(\mu<\mu_0\) | Negative difference |

For a two-sided test:

\[
H_0:\mu=50
\]

\[
H_1:\mu\neq50
\]

For a greater-than test:

\[
H_0:\mu\leq50
\]

\[
H_1:\mu>50
\]

The statistical calculation uses the boundary value of the null hypothesis.

The direction of the alternative must be specified before examining the results. Changing the direction after observing the data can invalidate the intended significance level.

## 3. Significance Levels

The significance level is represented by \(\alpha\).

It defines the maximum probability of a Type I error under the statistical testing procedure.

Common significance levels are:

| Significance level | Interpretation |
|---|---|
| 0.10 | 10% Type I error threshold |
| 0.05 | 5% Type I error threshold |
| 0.01 | 1% Type I error threshold |
| 0.001 | 0.1% Type I error threshold |

A significance level must be selected before evaluating the hypothesis.

A smaller significance level makes rejection more demanding. It can also reduce statistical power when sample size and effect size remain unchanged.

The significance level is not the probability that the null hypothesis is true.

## 4. Test Statistics

A test statistic measures how far an observed result is from the value expected under the null hypothesis.

### 4.1 One-Sample Z-Test

The Z-test is appropriate for a population mean when the population standard deviation is known and the sampling assumptions are satisfied.

\[
Z=\frac{\bar{x}-\mu_0}{\sigma/\sqrt{n}}
\]

Where:

- \(\bar{x}\) is the observed sample mean.
- \(\mu_0\) is the hypothesized population mean.
- \(\sigma\) is the known population standard deviation.
- \(n\) is the sample size.

The Python, C++17, and PostgreSQL implementations include one-sample Z-test calculations.

### 4.2 One-Sample Student t-Test

When population standard deviation is unknown, the sample standard deviation is used.

\[
t=\frac{\bar{x}-\mu_0}{s/\sqrt{n}}
\]

Degrees of freedom:

\[
df=n-1
\]

The Student t-distribution accounts for the additional uncertainty associated with estimating the population standard deviation.

The Python implementation evaluates the Student t-distribution using the regularized incomplete beta function.

The Java implementation uses the same numerical approach for its independent two-sample Welch t-test.

### 4.3 Independent Two-Sample Welch t-Test

Welch's t-test evaluates whether two independent population means differ.

It does not require equal population variances.

The test statistic is:

\[
t=
\frac{\bar{x}_1-\bar{x}_2}
{\sqrt{\frac{s_1^2}{n_1}+\frac{s_2^2}{n_2}}}
\]

The degrees of freedom are approximated using the Welch-Satterthwaite equation:

\[
df=
\frac{
\left(\frac{s_1^2}{n_1}+\frac{s_2^2}{n_2}\right)^2
}{
\frac{(s_1^2/n_1)^2}{n_1-1}
+
\frac{(s_2^2/n_2)^2}{n_2-1}
}
\]

This method is useful when experimental groups have different sample sizes or variances.

The Java implementation models this test through a `StatisticalTest` interface.

### 4.4 Two-Proportion Z-Test

A two-proportion Z-test compares success proportions between two independent groups.

\[
\hat p_1=\frac{x_1}{n_1}
\]

\[
\hat p_2=\frac{x_2}{n_2}
\]

Under the null hypothesis of equal population proportions, the pooled proportion is:

\[
\hat p=
\frac{x_1+x_2}{n_1+n_2}
\]

The standard error under the null hypothesis is:

\[
SE=
\sqrt{
\hat p(1-\hat p)
\left(
\frac{1}{n_1}+\frac{1}{n_2}
\right)
}
\]

The test statistic is:

\[
Z=\frac{\hat p_2-\hat p_1}{SE}
\]

The JavaScript implementation uses this test for an experimental website conversion scenario.

The pooled standard error used for the null-hypothesis test is different from the unpooled standard error used for the confidence interval of the observed difference.

## 5. P-Values

A p-value measures the probability, assuming the null hypothesis and model assumptions are true, of observing a test statistic at least as extreme as the one obtained, in the direction specified by the alternative hypothesis.

For a two-sided Z-test:

\[
p=2P(Z\geq|z_{\text{observed}}|)
\]

For a greater-than test:

\[
p=P(Z\geq z_{\text{observed}})
\]

For a less-than test:

\[
p=P(Z\leq z_{\text{observed}})
\]

### Decision Rule

\[
p<\alpha\Rightarrow\text{Reject }H_0
\]

\[
p\geq\alpha\Rightarrow\text{Fail to reject }H_0
\]

Failing to reject the null hypothesis does not establish that the null hypothesis is true.

A p-value is not:

- The probability that the null hypothesis is true.
- The probability that the observed result occurred by chance alone.
- A measure of practical importance.
- A direct measure of effect size.

The implementations retain the actual p-value alongside the decision so that the numerical evidence remains available for reporting.

## 6. Type I and Type II Errors

Hypothesis testing involves two possible decision errors.

### 6.1 Type I Error

A Type I error occurs when a true null hypothesis is rejected.

Its probability is represented by \(\alpha\).

Example:

A production process actually meets its specified average measurement, but the test incorrectly concludes that its mean differs.

### 6.2 Type II Error

A Type II error occurs when a false null hypothesis is not rejected.

Its probability is represented by \(\beta\).

Example:

A production process has experienced a genuine increase in its average measurement, but the statistical test fails to detect the change.

### 6.3 Decision Matrix

| Actual condition | Reject H0 | Fail to reject H0 |
|---|---|---|
| H0 is true | Type I error | Correct decision |
| H0 is false | Correct decision | Type II error |

The two error probabilities are related to the test design, sample size, significance level, variability, and true effect size.

Reducing the probability of one type of error can increase the probability of the other unless the study design is improved.

## 7. Statistical Power

Statistical power measures the probability of correctly rejecting a false null hypothesis.

\[
\text{Power}=1-\beta
\]

For example, if:

\[
\beta=0.20
\]

Then:

\[
\text{Power}=0.80
\]

This represents an 80% probability of detecting the specified effect under the assumed statistical model.

Power depends on:

- Sample size.
- Effect size.
- Population variability.
- Significance level.
- Direction of the alternative hypothesis.
- Statistical test design.

The Python and C++17 implementations include power-estimation functions for a two-sided large-sample Z-test.

The Java implementation provides the corresponding enterprise experiment analysis service.

The estimates depend on the specified alternative population mean and should not be interpreted as universal properties of a test.

## 8. Confidence Intervals

A confidence interval provides a range of parameter values compatible with the observed data under a specified confidence procedure.

For a large-sample mean with known population standard deviation:

\[
CI=
\bar{x}\pm z_{\alpha/2}\frac{\sigma}{\sqrt n}
\]

For a sample mean with unknown population standard deviation:

\[
CI=
\bar{x}\pm t_{\alpha/2,df}\frac{s}{\sqrt n}
\]

For an independent difference in means:

\[
CI=
(\bar{x}_1-\bar{x}_2)
\pm
t_{\alpha/2,df}\times SE
\]

A 95% confidence interval describes the long-run coverage of the interval-generating procedure under its assumptions. It does not mean there is a 95% probability that a fixed population parameter lies inside an already calculated interval.

The Python implementation uses a normal critical-value approximation for its displayed t-test confidence interval. Its t-test p-value uses the Student t-distribution. For publication-quality reporting, the confidence interval should use the corresponding Student t critical value.

The Java implementation calculates Welch confidence intervals using a numerical Student t quantile.

## 9. Multiple Hypothesis Testing

Testing multiple hypotheses increases the risk of obtaining false-positive findings.

If multiple independent tests are conducted at significance level 0.05, the probability of at least one Type I error increases as the number of tests increases.

### 9.1 Bonferroni Correction

The Bonferroni method adjusts the significance threshold:

\[
\alpha_{\text{adjusted}}=\frac{\alpha}{m}
\]

Where \(m\) is the number of tests.

This controls the family-wise error rate but can be conservative.

### 9.2 Benjamini-Hochberg Procedure

The Benjamini-Hochberg procedure controls the false discovery rate.

Arrange the p-values in ascending order:

\[
p_{(1)}\leq p_{(2)}\leq\cdots\leq p_{(m)}
\]

Find the largest rank \(k\) satisfying:

\[
p_{(k)}\leq\frac{k}{m}\alpha
\]

Reject the hypotheses corresponding to the first \(k\) ordered p-values.

Python, JavaScript, Java, and PostgreSQL include Benjamini-Hochberg decision processing.

The SQL implementation also stores adjusted p-values and significance decisions for each batch.

## 10. Experiment Workflow

The implementations follow a consistent statistical workflow.

    Define research question
            |
            v
    Specify H0 and H1
            |
            v
    Select significance level
            |
            v
    Select statistical test
            |
            v
    Collect and validate observations
            |
            v
    Calculate sample statistics
            |
            v
    Calculate test statistic
            |
            v
    Calculate p-value
            |
            v
    Compare p-value with alpha
            |
            v
    Evaluate statistical decision
            |
            v
    Report effect size and uncertainty
            |
            v
    Preserve results and audit history

The research hypothesis, statistical assumptions, and decision policy should be documented before examining experimental outcomes.

## 11. Python Implementation

### Responsibilities

The Python program provides a statistical calculation and reporting environment.

Its principal components are:

| Component | Responsibility |
|---|---|
| `Hypothesis` | Stores null value, alternative, and alpha |
| `Alternative` | Defines test direction |
| `Decision` | Represents the statistical decision |
| `TestResult` | Stores calculated results |
| `normal_cdf` | Calculates normal cumulative probabilities |
| `regularized_beta` | Evaluates the incomplete beta function |
| `student_t_cdf` | Evaluates Student t probabilities |
| `one_sample_z_test` | Performs a one-sample Z-test |
| `one_sample_t_test` | Performs a one-sample t-test |
| `benjamini_hochberg` | Performs multiple-testing correction |
| `estimate_type_ii_error` | Estimates beta and power |
| `save_report` | Exports structured JSON |

### Numerical Design

The implementation uses `math.erfc`, `math.lgamma`, and a continued-fraction calculation for the regularized incomplete beta function.

This avoids requiring an external statistics package.

The implementation validates:

- Minimum sample size.
- Finite numerical observations.
- Positive population standard deviation.
- Valid significance levels.
- Valid p-values.
- Alternative hypothesis selection.

The report excludes raw observations to reduce unnecessary exposure of potentially sensitive experimental data.

### Execution

Run the program using Python 3:

`python hypothesis_testing.py`

The program creates `hypothesis_test_report.json`.

## 12. JavaScript Implementation

### Responsibilities

The JavaScript program models an asynchronous experiment-processing workflow.

| Component | Responsibility |
|---|---|
| `Experiment` | Manages experiment execution |
| `EventEmitter` | Publishes lifecycle events |
| `TwoProportionTest` | Compares independent proportions |
| `MultipleTesting` | Performs false discovery rate correction |
| `ValidationError` | Represents invalid inputs |
| `StatisticalError` | Represents workflow errors |

### Experiment State Management

The experiment lifecycle is:

    CREATED
       |
       v
    RUNNING
       |
       +------> COMPLETED
       |
       +------> FAILED

An experiment cannot be executed twice after leaving its initial state.

The event-driven model separates statistical execution from event notification.

### Asynchronous Processing

The implementation uses:

- Promises.
- `async` and `await`.
- Node.js event emitters.
- Asynchronous file operations.

The report writer uses exclusive file creation and restrictive file permissions.

### Execution

Run using Node.js:

`node hypothesis_testing.js`

The program produces `hypothesis_test_report.json`.

## 13. C++17 Implementation

### Responsibilities

The C++ implementation emphasizes numerical operations, explicit domain structures, and controlled resource usage.

| Component | Responsibility |
|---|---|
| `Hypothesis` | Stores the test definition |
| `Statistics` | Calculates sample statistics and probabilities |
| `HypothesisTestingEngine` | Executes hypothesis tests |
| `PowerAnalysis` | Estimates Type II error and power |
| `TestResult` | Stores evaluation output |
| `Report` | Displays and exports results |

### Statistical Operations

The implementation supports:

- One-sample Z-tests.
- Independent large-sample Z approximations.
- Two-sided and directional alternatives.
- Confidence interval calculations.
- Power estimation.
- CSV reporting.

It uses `std::vector` for observations and standard algorithms for numerical processing.

### Execution

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic hypothesis_testing.cpp -o hypothesis_testing`

Run:

`./hypothesis_testing`

On Windows:

`hypothesis_testing.exe`

The program produces `hypothesis_test_report.csv`.

## 14. Java 17 Implementation

### Responsibilities

The Java implementation represents hypothesis testing as an enterprise statistical service.

Its domain model uses records, interfaces, enums, immutable collections, and explicit state transitions.

| Component | Responsibility |
|---|---|
| `Hypothesis` | Immutable hypothesis definition |
| `SampleSummary` | Validated sample statistics |
| `StatisticalTest` | Statistical test contract |
| `WelchTTest` | Independent two-sample test |
| `Experiment` | Experiment lifecycle management |
| `PowerAnalysis` | Type II error and power |
| `MultipleTesting` | Multiple-testing decisions |
| `ReportService` | Reporting and persistence |

### Domain Design

The `StatisticalTest` interface separates the statistical method from experiment management.

The experiment service owns the transition from `CREATED` to `RUNNING`, followed by either `COMPLETED` or `FAILED`.

The Welch implementation accounts for unequal group variances and unequal sample sizes.

The statistical calculations use a numerical approximation of the regularized incomplete beta function for Student t probabilities.

### Execution

Compile:

`javac --release 17 HypothesisTesting.java`

Run:

`java HypothesisTesting`

The program produces `hypothesis_test_report.json`.

## 15. PostgreSQL Implementation

### Database Architecture

The database uses the `statistics_lab` schema.

Its relational model separates experiment definitions, observations, statistical evaluations, error analysis, and multiple-testing batches.

| Table | Purpose |
|---|---|
| `experiments` | Experiment registry and lifecycle |
| `hypotheses` | Null and alternative definitions |
| `observations` | Individual measured values |
| `test_results` | Calculated test outcomes |
| `error_analysis` | Type I and Type II error probabilities |
| `power_analysis` | Planned sample size and estimated power |
| `multiple_testing_batches` | Groups of statistical comparisons |
| `multiple_testing_items` | Individual p-values and adjusted results |
| `experiment_audit` | Evaluation history |

### Data Relationships

    experiments
        |
        +---- hypotheses
        |         |
        |         +---- test_results
        |         |
        |         +---- error_analysis
        |         |
        |         +---- power_analysis
        |
        +---- observations
        |
        +---- experiment_audit

    multiple_testing_batches
        |
        +---- multiple_testing_items
                    |
                    +---- hypotheses

### Database Integrity

The schema uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated domain types.
- Performance-oriented indexes.
- Status-transition triggers.
- Transactional evaluation.
- JSONB audit records.

The `evaluate_one_sample_z` function retrieves sample observations, calculates the sample mean and standard error, computes the Z statistic and p-value, determines the decision, and records the evaluation.

The `group_statistics` view provides descriptive statistics for each experiment and group.

The database stores numerical outcomes independently of reporting queries, making results available for subsequent analysis.

### Important Database Limitation

The PostgreSQL evaluation function implements a one-sample Z-test and requires a known population standard deviation.

Its normal probability calculation uses a numerical approximation.

The power-analysis sample records are illustrative values rather than automatically derived estimates.

The database schema does not claim to implement a general Student t-test or every possible statistical model.

### Execution

Run the complete SQL file using PostgreSQL:

`psql -U postgres -d your_database -f hypothesis_testing.sql`

The script creates the schema, database objects, sample records, evaluation results, multiple-testing records, and reporting queries.

The transaction ensures that the setup and sample workflow are committed together.

## 16. Implementation Comparison

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Null hypothesis | Yes | Yes | Yes | Yes | Yes |
| Alternative hypothesis | Yes | Yes | Yes | Yes | Yes |
| Significance level | Yes | Yes | Yes | Yes | Yes |
| P-value | Yes | Yes | Yes | Yes | Yes |
| One-sample Z-test | Yes | No | Yes | No | Yes |
| One-sample t-test | Yes | No | No | No | No |
| Two-sample test | No | Proportion Z | Mean Z approximation | Welch t | No |
| Type I error | Yes | Interpretation | Yes | Yes | Yes |
| Type II error | Yes | Interpretation | Yes | Yes | Yes |
| Statistical power | Yes | No | Yes | Yes | Stored estimates |
| Confidence intervals | Yes | Yes | Yes | Yes | Partial |
| Multiple testing | Yes | Yes | No | Yes | Yes |
| Persistent reports | JSON | JSON | CSV | JSON | Relational tables |
| Experiment lifecycle | No | Yes | No | Yes | Yes |

## 17. Assumptions and Limitations

Hypothesis tests are valid only when their statistical assumptions are sufficiently satisfied.

### Sampling Assumptions

- Observations should represent the population or sampling process being studied.
- Independent tests require independent observations across groups.
- The sampling distribution must support the selected approximation.
- Extreme outliers and strong distributional departures should be investigated.
- The selected statistical test must match the measurement scale and research design.

### Numerical Limitations

The implementations use standard-library numerical approximations rather than a dedicated statistical distribution library.

The normal CDF approximations have finite numerical accuracy.

The incomplete beta calculations use convergence limits.

Extreme tail probabilities can require higher numerical precision than ordinary applications.

The C++17 implementation uses a normal approximation for its large-sample group comparison rather than implementing Welch's t-distribution.

The Python t-test confidence interval uses a normal critical-value approximation and should be refined using a Student t quantile when precise interval coverage is required.

The JavaScript proportion test assumes sufficiently large samples for its normal approximation.

The SQL implementation is restricted to its documented one-sample Z-test workflow.

## 18. Performance and Security Considerations

### Performance

- Sample mean and variance calculations are linear in sample size.
- Sorting p-values for Benjamini-Hochberg correction requires \(O(m\log m)\) time.
- Continued-fraction calculations have bounded iteration counts.
- Database indexes accelerate experiment and result retrieval.
- Large datasets should be aggregated or processed in controlled batches.
- Expensive statistical calculations should be separated from interactive reporting operations.

### Security

- Validate all numerical inputs before calculations.
- Reject NaN and infinite observations.
- Use parameterized SQL when integrating the schema with applications.
- Restrict access to experiment observations and reports.
- Avoid exposing raw experimental data unnecessarily.
- Maintain an audit history of statistical decisions.
- Protect report files with appropriate operating-system permissions.
- Do not treat a statistical result as proof of causation.

### Reproducibility

A reproducible statistical evaluation should preserve:

- Experiment identification.
- Hypothesis definition.
- Alternative direction.
- Significance level.
- Sample size.
- Statistical test name.
- Test statistic.
- P-value.
- Effect estimate.
- Confidence interval.
- Evaluation timestamp.
- Statistical decision.

For stronger research governance, also preserve the data collection protocol, analysis version, missing-data policy, exclusions, and multiple-testing plan.

## 19. Practical Statistical Interpretation

Consider an experiment evaluating whether a revised production process changes the average measurement from 50.

The hypotheses are:

\[
H_0:\mu=50
\]

\[
H_1:\mu\neq50
\]

The significance level is:

\[
\alpha=0.05
\]

Suppose the resulting p-value is:

\[
p=0.018
\]

Since:

\[
0.018<0.05
\]

The null hypothesis is rejected.

The statistical evidence supports a difference from the reference mean under the specified model.

This does not establish that the change is operationally important or that the intervention caused the difference.

Effect size, uncertainty, sampling design, measurement quality, and practical consequences must also be considered.

A statistically significant result can have a negligible practical effect. A statistically non-significant result can still be compatible with an important effect when the sample size is insufficient.

The final decision should therefore be reported with the test statistic, p-value, significance level, effect estimate, confidence interval, and relevant assumptions.
