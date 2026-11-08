# Statistical Tests I

## 1. Project Overview

This project implements four fundamental inferential statistical procedures across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The statistical methods are:

1. One-sample Student's t-test.
2. Independent two-sample Welch's t-test.
3. Independent two-sample pooled t-test.
4. Paired Student's t-test.

The implementations calculate sample statistics, standard errors, t-statistics, degrees of freedom, two-sided p-values, and decisions based on a significance level.

The central objective is to determine whether observed sample differences provide sufficient statistical evidence against a specified null hypothesis.

## 2. Statistical Foundations

### 2.1 Hypothesis Testing

A statistical hypothesis is a statement about a population parameter.

- Null hypothesis (H0): The assumed population condition or absence of a difference.
- Alternative hypothesis (H1): The condition being investigated.
- Significance level (alpha): The maximum tolerated Type I error probability under the testing procedure.
- Test statistic: A standardized measure of departure from the null hypothesis.
- P-value: The probability, assuming the null hypothesis, of observing a test statistic at least as extreme as the one obtained.
- Degrees of freedom: A quantity determining the reference distribution used for inference.

The implementations use two-sided tests.

The decision rule is:

- If p-value is less than alpha, reject H0.
- Otherwise, fail to reject H0.

Failing to reject H0 does not establish that H0 is true.

A p-value is not the probability that the null hypothesis is true.

### 2.2 Sample Mean

For observations \(x_1,x_2,\ldots,x_n\), the arithmetic mean is:

\[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\]

The mean estimates the population's central value.

### 2.3 Sample Variance

The unbiased sample variance is:

\[
s^2=\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}
\]

The sample standard deviation is:

\[
s=\sqrt{s^2}
\]

The denominator \(n-1\) accounts for the loss of one degree of freedom when estimating the sample mean.

### 2.4 Standard Error

Standard error measures the estimated variability of a statistic across repeated samples.

For a single sample:

\[
SE=\frac{s}{\sqrt{n}}
\]

A smaller standard error generally indicates a more precise estimate of the sample mean.

## 3. One-Sample Student's t-Test

### Purpose

The one-sample t-test determines whether a sample mean differs significantly from a specified population reference mean.

Example: A logistics organization specifies an average delivery target of 30 hours. A sample of delivery times is collected to evaluate whether the observed average differs from this target.

### Hypotheses

\[
H_0:\mu=\mu_0
\]

\[
H_1:\mu\neq\mu_0
\]

Where:

- \(\mu\) is the population mean.
- \(\mu_0\) is the hypothesized population mean.

### Test Statistic

\[
t=\frac{\bar{x}-\mu_0}{s/\sqrt{n}}
\]

Degrees of freedom:

\[
df=n-1
\]

### Assumptions

- Observations are independent.
- The sample is representative of the target population.
- The population is approximately normally distributed for small samples.
- Measurements are quantitative.
- Extreme outliers do not invalidate the mean-based inference.

The procedure does not require a known population standard deviation.

### Implementation

Python, JavaScript, C++, and Java implement the complete calculation, including the two-sided p-value.

PostgreSQL calculates the mean difference, sample variance, standard error, and t-statistic.

## 4. Independent Two-Sample Tests

### Purpose

Independent two-sample tests compare the means of two separate populations.

Example: An organization compares employee assessment scores from two different training methods.

The employees in the first group are different from those in the second group.

### Hypotheses

\[
H_0:\mu_1-\mu_2=0
\]

\[
H_1:\mu_1-\mu_2\neq0
\]

The two independent-sample implementations provide different approaches to variance estimation.

### 4.1 Welch's t-Test

Welch's t-test compares two independent population means without assuming equal population variances.

It is the default independent-sample procedure in the implementations.

The test statistic is:

\[
t=
\frac{\bar{x}_1-\bar{x}_2}
{\sqrt{\frac{s_1^2}{n_1}+\frac{s_2^2}{n_2}}}
\]

The approximate degrees of freedom are calculated using the Welch-Satterthwaite equation:

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

Welch's procedure is particularly useful when:

- Group sample sizes differ.
- Group variances differ.
- Equal population variance cannot reasonably be assumed.

### 4.2 Pooled Independent t-Test

The pooled t-test assumes equal population variances.

The pooled variance is:

\[
s_p^2=
\frac{
(n_1-1)s_1^2+(n_2-1)s_2^2
}{
n_1+n_2-2
}
\]

The test statistic is:

\[
t=
\frac{\bar{x}_1-\bar{x}_2}
{s_p\sqrt{\frac{1}{n_1}+\frac{1}{n_2}}}
\]

Degrees of freedom:

\[
df=n_1+n_2-2
\]

The equal-variance assumption must be justified by the study design or appropriate analysis.

The pooled test should not be selected merely because it produces a smaller p-value.

### 4.3 Important Distinction

| Property | Welch test | Pooled test |
|---|---|---|
| Independent groups | Required | Required |
| Equal variance assumption | Not required | Required |
| Variance estimation | Separate | Combined |
| Degrees of freedom | Approximate | \(n_1+n_2-2\) |
| General default | Preferred | When equal variance is justified |

Neither procedure is suitable for observations that are actually paired or repeated measurements from the same subjects.

## 5. Paired Student's t-Test

### Purpose

The paired t-test evaluates the mean difference between two related measurements.

Example: Employee performance is measured before and after a training intervention.

Each employee contributes two observations.

The observations are related because they belong to the same employee.

### Difference Calculation

For each subject:

\[
d_i=x_{after,i}-x_{before,i}
\]

The mean difference is:

\[
\bar{d}=\frac{1}{n}\sum_{i=1}^{n}d_i
\]

The sample variance of differences is:

\[
s_d^2=
\frac{\sum_{i=1}^{n}(d_i-\bar{d})^2}{n-1}
\]

### Hypotheses

\[
H_0:\mu_d=0
\]

\[
H_1:\mu_d\neq0
\]

### Test Statistic

\[
t=\frac{\bar{d}}{s_d/\sqrt{n}}
\]

Degrees of freedom:

\[
df=n-1
\]

### Assumptions

- Measurements are correctly matched.
- Differences between observations are independent across subjects.
- Differences are approximately normally distributed for small samples.
- The measurement scale is quantitative.

The normality assumption applies to the differences, not separately to the before and after measurements.

### Important Distinction

A paired test is not an independent two-sample test.

Treating related observations as independent discards the relationship between measurements and can produce incorrect standard errors and conclusions.

## 6. Student's t-Distribution and P-Value Calculation

All four programming-language implementations calculate two-sided p-values from Student's t-distribution.

For a t-statistic \(t\) with \(df\) degrees of freedom:

\[
p=2P(T_{df}\geq |t|)
\]

The implementations use the regularized incomplete beta function.

The transformation is:

\[
x=\frac{df}{df+t^2}
\]

The two-sided p-value becomes:

\[
p=I_x\left(\frac{df}{2},\frac{1}{2}\right)
\]

Where \(I_x(a,b)\) is the regularized incomplete beta function.

The numerical implementation uses:

- The Lanczos approximation for the logarithm of the gamma function.
- A continued-fraction evaluation of the incomplete beta function.
- Symmetry to improve numerical stability.
- Convergence checks to detect calculation failures.

This approach avoids relying on normal-distribution approximations for Student's t-test p-values.

## 7. Cross-Language Implementation Design

### Python

The Python implementation provides a reusable statistical analysis framework.

Important components:

| Component | Responsibility |
|---|---|
| `TestType` | Identifies statistical procedures |
| `TestResult` | Stores inferential results |
| `validate_sample()` | Checks sample size and numeric values |
| `sample_variance()` | Calculates unbiased variance |
| `regularized_beta()` | Calculates the regularized incomplete beta function |
| `student_t_p_value()` | Calculates two-sided p-values |
| `one_sample_t_test()` | Executes one-sample testing |
| `independent_t_test()` | Executes Welch or pooled testing |
| `paired_t_test()` | Executes paired testing |
| `StatisticalTestRunner` | Collects and exports results |

Python uses `dataclasses` for structured results, `Enum` for test classification, and standard-library CSV and JSON support.

The implementation uses `math.fsum()` for more accurate summation of floating-point observations.

### JavaScript

The JavaScript implementation emphasizes event-driven execution and controlled result management.

Important components:

- `TestResult`: Structured test output.
- `StatisticalWorkspace`: Manages test execution and result storage.
- `Map` is not necessary for the small demonstration dataset; arrays provide simpler result ordering.
- Private class fields protect workspace state.
- Promises and asynchronous file operations support report export.
- Input validation prevents invalid numerical observations.

The implementation uses Node.js filesystem operations with exclusive file creation to avoid accidentally overwriting existing reports.

### C++17

The C++ implementation emphasizes computational control and explicit domain modeling.

Important components:

- `TestType`: Enumeration of supported tests.
- `TestResult`: Statistical result structure.
- `Statistics`: Numerical algorithms and validation.
- `ReportManager`: Result collection and CSV reporting.

STL vectors store observations, and standard algorithms provide aggregation operations.

Exceptions handle invalid samples, numerical convergence failures, and file access errors.

### Java 17

The Java implementation uses an enterprise service-oriented design.

Important components:

- `Sample`: Validated immutable sample data.
- `TestResult`: Immutable result record.
- `TestService`: Common execution interface.
- `OneSampleTest`: One-sample testing service.
- `IndependentTest`: Independent-group testing service.
- `PairedTest`: Paired testing service.
- `StatisticalTestManager`: Coordinates execution and reporting.

The interface allows additional statistical procedures to be introduced without changing the report manager.

Java records provide immutable result structures, while collections and streams support sample management.

## 8. PostgreSQL Relational Model

The SQL implementation represents statistical experiments as relational records.

### Entity Relationships

Experiments
    |
    | 1:N
    |
Experiment Groups
    |
    | 1:N
    |
Observations

## Database Structure

| Table | Purpose |
|---|---|
| `experiments` | Stores experiment definitions and testing policies |
| `experiment_groups` | Identifies single, control, and treatment groups |
| `observations` | Stores individual quantitative measurements |

### Integrity Controls

The database uses:

- Primary keys for unique identification.
- Foreign keys for relational consistency.
- Check constraints for valid test types and significance levels.
- Unique constraints for experiment-group combinations.
- A partial unique index to prevent duplicate subject measurements within a group.
- Triggers to enforce group-count restrictions.
- Transactions and savepoints for controlled data operations.

### Statistical Views

| View | Analysis |
|---|---|
| `one_sample_test_statistics` | One-sample test calculations |
| `independent_test_statistics` | Welch and pooled calculations |
| `paired_test_statistics` | Paired differences and test statistics |

The SQL views calculate descriptive statistics and inferential test statistics.

The database implementation intentionally leaves exact Student's t-distribution p-value evaluation to the programming-language implementations rather than presenting an unimplemented or approximate result as an exact p-value.

### Query Operations

The SQL script demonstrates:

- Experiment retrieval.
- Group-level descriptive statistics.
- Sample-size validation.
- Missing paired-subject detection.
- Test-statistic calculations.
- Degrees-of-freedom calculations.
- Transactional experiment creation.

## 9. Numerical and Data Validation

The implementations address several important failure conditions.

| Condition | Handling |
|---|---|
| Fewer than two observations | Reject sample |
| NaN or infinite observations | Reject sample |
| Invalid alpha | Reject configuration |
| Unequal paired sample sizes | Reject paired test |
| Invalid hypothesized mean | Reject one-sample test |
| Zero sample variance | Handle undefined or infinite t-statistic |
| Zero variance in both independent groups | Reject undefined comparison |
| Incomplete beta convergence | Raise numerical error |
| Invalid file destination | Report export failure |
| Missing paired subject | Exclude unmatched observations from paired calculations |

### Zero-Variance Cases

A zero sample variance requires special treatment.

If every observation equals the hypothesized mean, the standard error and numerator are both zero. The t-statistic is undefined.

If all observations are identical but differ from the hypothesized mean, the mathematical limiting statistic is infinite.

The implementations distinguish these situations rather than silently dividing by zero.

## 10. Statistical Interpretation

Consider a study comparing two training methods.

Suppose the test returns:

| Metric | Interpretation |
|---|---|
| Mean difference | Observed difference between group means |
| t-statistic | Standardized difference |
| Degrees of freedom | Determines the reference t-distribution |
| p-value | Measures evidence against the null hypothesis |
| Alpha | Predefined significance threshold |

A statistically significant result indicates evidence of a difference under the model assumptions.

It does not establish:

- Practical importance.
- Causation.
- Absence of bias.
- Representativeness of the sample.
- Generalizability to every population.

Effect sizes and confidence intervals should accompany statistical significance when results are used for research or organizational decisions.

A statistically nonsignificant result also does not establish equivalence between groups.

## 11. Performance and Numerical Considerations

For a sample containing \(n\) observations:

- Mean calculation: \(O(n)\).
- Sample variance: \(O(n)\).
- Paired difference construction: \(O(n)\).
- Independent-group calculations: \(O(n_1+n_2)\).
- Result storage: \(O(k)\), where \(k\) is the number of tests.
- Incomplete beta evaluation: Iterative numerical computation with a bounded iteration count.

The implementations use direct calculations because the demonstration datasets are relatively small.

For large datasets, production implementations should consider:

- Streaming mean and variance algorithms.
- Compensated summation.
- Batch-based processing.
- Parallel processing where appropriate.
- Input range and floating-point overflow controls.
- Independent numerical validation against a trusted statistical reference implementation.

The incomplete beta approximation should be tested against known reference values before being used in regulated or high-stakes statistical workflows.

## 12. Statistical Design Limitations

The four procedures implemented here are parametric mean-comparison tests.

They do not automatically solve problems involving:

- Strongly skewed small samples.
- Severe outliers.
- Dependent observations in supposedly independent groups.
- Repeated-measures structures involving more than two conditions.
- Multiple-comparison error inflation.
- Clustered observations.
- Complex survey sampling.
- Missing-data mechanisms.
- Non-inferiority or equivalence testing.

Alternative methods may be required when the assumptions are not satisfied.

The choice between one-sample, independent, and paired testing must be determined by the research design before interpreting the results.

## 13. Execution

| File | Runtime |
|---|---|
| Python implementation | Python 3.10+ |
| JavaScript implementation | Node.js 18+ |
| C++ implementation | C++17-compatible compiler |
| Java implementation | Java 17 |
| PostgreSQL implementation | PostgreSQL 15+ |

Python and JavaScript use only their respective standard libraries.

C++17 uses the standard library.

Java 17 uses built-in language and standard-library features.

PostgreSQL uses native relational database capabilities and PL/pgSQL.

The programming implementations generate CSV and JSON reports where supported. The SQL implementation creates reusable experiment tables, statistical views, indexes, validation mechanisms, and sample records.

## 14. Practical Research Workflow

```text
Define Research Question
          |
          v
Identify Population Parameter
          |
          v
Determine Sample Relationship
          |
          +--------------------------+
          |                          |
          v                          v
     One Sample                Two Samples
          |                          |
          |                 +--------+--------+
          |                 |                 |
          |                 v                 v
          |              Paired          Independent
          |                 |                 |
          v                 v                 v
     One-Sample t       Paired t       Welch / Pooled t
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                    Validate Assumptions
                            |
                            v
                     Calculate t-Statistic
                            |
                            v
                    Calculate P-Value
                            |
                            v
                   Compare Against Alpha
                            |
                            v
                   Interpret the Results
                            |
                            v
                   Record and Report Findings
