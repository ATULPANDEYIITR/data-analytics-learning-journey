# Statistical Tests II

## Technical Scope

This project implements four statistical inference methods:

- Chi-square goodness-of-fit tests.
- Chi-square tests of independence.
- One-sample proportion tests.
- Two-sample proportion tests.

The implementations examine categorical frequency distributions, relationships between categorical variables, and differences between population proportions.

The five source files provide complementary implementations using Python, JavaScript, C++17, Java 17, and PostgreSQL.

## Statistical Foundations

### Hypothesis Testing

Hypothesis testing uses sample observations to evaluate a claim about a population.

Every implemented test follows this general structure:

1. Define the null hypothesis, H0.
2. Define the alternative hypothesis, H1.
3. Select a significance level.
4. Calculate the test statistic.
5. Determine the degrees of freedom where applicable.
6. Calculate the p-value.
7. Compare the p-value with the significance level.
8. Report the statistical decision.

The default significance level is:

\[
\alpha = 0.05
\]

The decision rule is:

\[
p < \alpha \Rightarrow \text{Reject }H_0
\]

\[
p \geq \alpha \Rightarrow \text{Fail to reject }H_0
\]

Failing to reject the null hypothesis does not establish that the null hypothesis is true.

A p-value measures how unusual the observed result, or a more extreme result, would be under the null hypothesis and the assumed statistical model.

It is not the probability that the null hypothesis is true.

## 1. Chi-Square Goodness-of-Fit Test

### Purpose

The goodness-of-fit test determines whether an observed categorical frequency distribution is consistent with a specified theoretical distribution.

Examples include:

- Testing whether product demand is distributed equally across four categories.
- Examining whether customer preferences match an expected distribution.
- Evaluating whether observed defect classifications follow historical proportions.
- Testing whether survey responses follow specified population probabilities.

### Hypotheses

The null hypothesis states that the observed population distribution follows the specified theoretical distribution.

The alternative hypothesis states that at least one category probability differs.

### Test Statistic

\[
\chi^2 =
\sum_{i=1}^{k}
\frac{(O_i-E_i)^2}{E_i}
\]

Where:

| Symbol | Meaning |
|---|---|
| \(O_i\) | Observed frequency |
| \(E_i\) | Expected frequency |
| \(k\) | Number of categories |
| \(\chi^2\) | Chi-square statistic |

Expected frequencies are calculated from the theoretical probabilities:

\[
E_i = n p_i
\]

Where \(n\) is the total sample size and \(p_i\) is the expected probability for category \(i\).

### Degrees of Freedom

When no distribution parameters are estimated from the sample:

\[
df=k-1
\]

When parameters are estimated from the data, the degrees of freedom must account for the number of independently estimated parameters.

### Implementation

The Python, JavaScript, C++, and Java implementations:

- Validate observed frequencies.
- Validate expected frequencies.
- Require at least two categories.
- Check that observed and expected totals match.
- Calculate the chi-square statistic.
- Calculate the p-value using the regularized upper incomplete gamma function.
- Determine statistical significance.
- Calculate a standardized discrepancy measure.

The PostgreSQL implementation stores each category as a separate observation and calculates the statistic through an aggregation query.

### Example

| Category | Observed | Expected |
|---|---:|---:|
| A | 48 | 50 |
| B | 52 | 50 |
| C | 45 | 50 |
| D | 55 | 50 |
| Total | 200 | 200 |

The calculation evaluates the cumulative deviation between observed and expected frequencies.

### Assumptions

- Observations are independent.
- Categories are mutually exclusive.
- Every observation belongs to one category.
- Expected frequencies are sufficiently large for the chi-square approximation.
- Expected frequencies must be positive.

A common practical guideline is that expected frequencies should generally be at least five. More detailed assessment is appropriate when multiple expected cells are small.

The goodness-of-fit test is not a test of independence between two variables.

## 2. Chi-Square Test of Independence

### Purpose

The independence test evaluates whether two categorical variables are statistically associated.

Examples include:

- Training method and employee preference.
- Gender category and product preference.
- Payment method and transaction outcome.
- Education category and employment status.
- Marketing channel and customer conversion classification.

### Hypotheses

\[
H_0: X \text{ and } Y \text{ are independent}
\]

\[
H_1: X \text{ and } Y \text{ are associated}
\]

### Contingency Tables

A contingency table contains observed frequencies for combinations of two categorical variables.

Example:

| Training Method | Preferred | Not Preferred | Total |
|---|---:|---:|---:|
| Online | 40 | 20 | 60 |
| Classroom | 15 | 45 | 60 |
| Total | 55 | 65 | 120 |

Each cell represents the frequency of a particular combination.

### Expected Frequency

Under the independence assumption:

\[
E_{ij} =
\frac{R_i C_j}{N}
\]

Where:

- \(R_i\) is the corresponding row total.
- \(C_j\) is the corresponding column total.
- \(N\) is the grand total.

### Test Statistic

\[
\chi^2 =
\sum_{i=1}^{r}
\sum_{j=1}^{c}
\frac{(O_{ij}-E_{ij})^2}{E_{ij}}
\]

### Degrees of Freedom

\[
df=(r-1)(c-1)
\]

Where:

- \(r\) is the number of rows.
- \(c\) is the number of columns.

### Cramer's V

Statistical significance does not describe the strength of an association.

Cramer's V provides an effect-size measure:

\[
V =
\sqrt{
\frac{\chi^2}
{N\min(r-1,c-1)}
}
\]

Its value ranges from zero to one.

Interpretation depends on the table dimensions and research context. A statistically significant association does not necessarily imply a practically important relationship.

### Yates' Continuity Correction

For a 2 × 2 contingency table, the implementations optionally support Yates' correction.

\[
\chi^2_Y =
\sum
\frac{
\left(\max(0,|O-E|-0.5)\right)^2
}{E}
\]

The correction adjusts for the difference between discrete frequency observations and the continuous chi-square approximation.

It is optional and is not applied to larger contingency tables in these implementations.

### Assumptions

- Observations are independent.
- Categories are mutually exclusive.
- The contingency table contains valid frequencies.
- Expected cell frequencies are sufficiently large.

For sparse tables, exact methods such as Fisher's exact test may be more appropriate, particularly for 2 × 2 tables.

The independence test establishes evidence of association, not causation.

## 3. One-Sample Proportion Test

### Purpose

The one-sample proportion test determines whether a population proportion differs from a specified reference value.

Examples include:

- Whether customer satisfaction exceeds a target.
- Whether a manufacturing defect rate differs from a standard.
- Whether an acceptance rate differs from 50%.
- Whether a conversion rate differs from a historical benchmark.

### Hypotheses

For the implemented two-sided test:

\[
H_0:p=p_0
\]

\[
H_1:p\neq p_0
\]

Where:

- \(p\) is the unknown population proportion.
- \(p_0\) is the hypothesized population proportion.

### Observed Proportion

\[
\hat p=\frac{x}{n}
\]

Where:

- \(x\) is the number of successes.
- \(n\) is the total number of trials.

### Standard Error Under the Null Hypothesis

\[
SE =
\sqrt{
\frac{p_0(1-p_0)}{n}
}
\]

### Test Statistic

\[
z =
\frac{\hat p-p_0}{SE}
\]

The two-sided p-value is calculated from the standard normal distribution.

### Implementation Rules

- The number of trials must be positive.
- Successes cannot be negative.
- Successes cannot exceed trials.
- The hypothesized proportion must be strictly between zero and one.
- The test uses the null-hypothesis standard error.

### Statistical Assumptions

- Trials are independent.
- Each trial has the same success probability under the assumed model.
- Outcomes are binary.
- The sample is sufficiently large for the normal approximation.

The familiar guideline of at least ten expected successes and ten expected failures under the null hypothesis is a useful diagnostic, not a universal guarantee of approximation accuracy.

For small samples or extreme probabilities, exact binomial testing is preferable.

## 4. Two-Sample Proportion Test

### Purpose

The two-sample proportion test evaluates whether two independent populations have different success proportions.

Examples include:

- Comparing conversion rates between two marketing campaigns.
- Comparing defect rates across two production lines.
- Comparing acceptance rates between two service providers.
- Evaluating the success rates of two independent processes.

### Hypotheses

\[
H_0:p_1=p_2
\]

\[
H_1:p_1\neq p_2
\]

### Individual Sample Proportions

\[
\hat p_1=\frac{x_1}{n_1}
\]

\[
\hat p_2=\frac{x_2}{n_2}
\]

### Pooled Proportion

Under the null hypothesis, the two population proportions are equal.

The pooled estimate is:

\[
\hat p=
\frac{x_1+x_2}{n_1+n_2}
\]

### Standard Error

\[
SE =
\sqrt{
\hat p(1-\hat p)
\left(
\frac{1}{n_1}+\frac{1}{n_2}
\right)
}
\]

### Test Statistic

\[
z =
\frac{\hat p_1-\hat p_2}{SE}
\]

The p-value is obtained from the two-sided standard normal distribution.

### Effect Size

The implementations report the observed difference:

\[
\Delta=\hat p_1-\hat p_2
\]

This provides a direct measure of the difference between sample proportions.

A proportion difference of 0.10 represents a ten-percentage-point difference, not necessarily a ten-percent relative increase.

### Assumptions

- The samples are independent.
- Observations within each sample are independent.
- Each outcome is binary.
- The normal approximation is appropriate.
- The pooled variance is nonzero.

Paired observations require a different statistical procedure.

## Distinction Between the Four Tests

| Test | Statistical question | Input structure | Statistic |
|---|---|---|---|
| Goodness-of-fit | Does one categorical distribution match an expected distribution? | Observed and expected frequencies | Chi-square |
| Independence | Are two categorical variables associated? | Contingency table | Chi-square |
| One proportion | Does one population proportion differ from a reference value? | One success count and one sample size | Z |
| Two proportions | Do two independent population proportions differ? | Two success counts and two sample sizes | Z |

The first two tests use chi-square distributions.

The other two use the standard normal distribution.

Although the square of a standard normal variable follows a chi-square distribution with one degree of freedom, the proportion tests are implemented directly as two-sided z-tests.

## P-Value Computation

### Chi-Square Distribution

The chi-square upper-tail probability is:

\[
p =
Q\left(
\frac{df}{2},
\frac{\chi^2}{2}
\right)
\]

Where \(Q(a,x)\) is the regularized upper incomplete gamma function.

The Python, JavaScript, C++17, and Java 17 implementations use:

- A convergent series for the lower part of the gamma-function domain.
- A continued fraction for the upper part.
- Numerical convergence checks.
- Probability bounds to prevent numerical results outside the interval [0,1].

These methods avoid the need for third-party numerical packages.

### Normal Distribution

The two-sided normal probability is:

\[
p=2[1-\Phi(|z|)]
\]

Where \(\Phi\) represents the standard normal cumulative distribution function.

Python uses the standard-library complementary error function.

JavaScript and Java use numerical approximations, while C++ uses the standard-library complementary error function.

### PostgreSQL Approximation

PostgreSQL does not use the same incomplete-gamma implementation in this project.

Its chi-square p-value calculation uses the Wilson-Hilferty transformation:

\[
Z \approx
\frac{
(\chi^2/df)^{1/3}
-
(1-2/(9df))
}{
\sqrt{2/(9df)}
}
\]

The upper normal tail approximates the chi-square upper-tail probability.

The proportion tests also use a normal-tail approximation.

These SQL calculations are intended for database workflow demonstrations. They should not replace higher-precision statistical calculations when small p-value differences affect important decisions.

## Implementation Architecture

### Python

The Python implementation uses:

- `dataclasses` for immutable result structures.
- `Enum` for statistical test categories.
- Lists for frequency distributions and contingency tables.
- Functions for each statistical procedure.
- Explicit validation and custom exceptions.
- `math.lgamma` for logarithmic gamma calculations.
- `math.erfc` for normal-tail probabilities.
- JSON serialization for persistent reporting.
- Assertions for numerical and input-validation tests.

`StatisticalAnalysis` maintains the execution history and exports completed results.

The design separates the numerical algorithms from the analysis workflow.

### JavaScript

The JavaScript implementation uses an event-driven analysis engine.

Important mechanisms include:

- Private class fields.
- `Map` for storing completed analyses.
- `EventEmitter` for lifecycle notifications.
- Promises for asynchronous execution.
- `Promise.all` for independent analytical jobs.
- Immutable result objects.
- Structured error handling.
- Atomic report replacement through a temporary file.

The analysis engine emits:

| Event | Meaning |
|---|---|
| `started` | Analysis execution begins |
| `completed` | Statistical calculation succeeds |
| `failed` | Analysis execution fails |
| `exported` | Report export completes |

This design supports integration with larger asynchronous data-processing systems.

The execution model is asynchronous, while the statistical calculations themselves are CPU-bound synchronous operations.

### C++17

The C++ implementation emphasizes explicit domain modeling and controlled execution.

Its main components include:

- `StatisticalError` for domain-specific exceptions.
- `TestResult` for analytical results.
- Separate functions for each test.
- STL vectors for categorical data.
- Numerical algorithms using `std::lgamma`.
- `std::erfc` for normal probabilities.
- `std::clamp` for probability bounds.
- `AnalysisEngine` for collecting and reporting results.

The engine stores results in a vector and provides a consistent report.

The design avoids external dependencies and uses compile-time type checking where possible.

### Java 17

The Java implementation uses an enterprise-oriented service architecture.

Its main domain components include:

| Component | Responsibility |
|---|---|
| `StatisticalPolicy` | Defines the significance level and decision rule |
| `TestResult` | Immutable statistical result |
| `InputValidator` | Validates frequency and expected-value inputs |
| `GoodnessOfFitService` | Executes distribution testing |
| `IndependenceService` | Evaluates categorical associations |
| `ProportionService` | Executes proportion tests |
| `AnalysisSession` | Manages analysis lifecycle and results |

Java records provide immutable data structures.

The `StatisticalOperation` interface separates execution from orchestration.

`AnalysisSession` maintains an explicit lifecycle:

`CREATED → VALIDATED → EXECUTED → REPORTED`

An execution failure moves the session into `FAILED`.

The session rejects additional operations after reporting or failure.

This design is suitable for integration into service-oriented analytical applications.

### PostgreSQL

The PostgreSQL implementation models statistical analysis as a relational workflow.

The database separates experimental metadata, statistical hypotheses, raw observations, and calculated results.

#### Relational Structure

    Experiments
        |
        +---- Statistical Analyses
                    |
                    +---- Goodness-of-Fit Observations
                    |
                    +---- Contingency Observations
                    |
                    +---- Proportion Observations
                    |
                    +---- Proportion Hypotheses

                    |
                    +---- Analysis Results

#### Main Tables

| Table | Purpose |
|---|---|
| `experiments` | Stores experiment metadata and significance levels |
| `statistical_analyses` | Stores hypotheses, execution states, statistics, and decisions |
| `goodness_of_fit_observations` | Stores observed and expected categorical frequencies |
| `contingency_observations` | Stores observed contingency-table cells |
| `proportion_observations` | Stores success and trial counts |
| `proportion_hypotheses` | Stores reference proportions for one-sample tests |

#### Database Integrity

The implementation uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated types.
- Indexes.
- A validation trigger.
- Stored procedures.
- Transactional execution.
- A reporting view.

Constraints protect fundamental data integrity.

The validation trigger ensures that completed analyses have the required result fields.

Stored procedures perform statistical calculations and update the corresponding analysis records.

#### Transaction Management

The sample experiments and their statistical calculations are executed transactionally.

If an execution procedure raises an exception, PostgreSQL can roll back the transaction instead of retaining a partially completed workflow.

#### Reporting

The `analysis_report` view combines experiment information with statistical results.

The SQL script also includes:

- Test-category aggregation.
- Statistical significance reporting.
- Expected-frequency validation.
- Contingency-table expected-frequency calculations.
- Proportion validation.
- Analysis eligibility checks.
- Completed-analysis counts.

## Effect Sizes and Statistical Significance

Statistical significance and practical importance are different concepts.

A small difference can become statistically significant when the sample size is large.

A large difference can remain statistically uncertain when the sample size is small.

The implementations therefore report effect-size information:

| Test | Effect-size measure |
|---|---|
| Goodness-of-fit | \(\sqrt{\chi^2/N}\), a standardized discrepancy measure |
| Independence | Cramer's V |
| One proportion | Observed proportion minus hypothesized proportion |
| Two proportions | Difference between sample proportions |

These measures should be interpreted in their statistical context.

For goodness-of-fit, the reported discrepancy measure is not a substitute for a conventional goodness-of-fit effect-size measure when distribution parameters have been estimated.

## Edge Cases and Failure Handling

The implementations explicitly address:

- Empty datasets.
- Negative frequencies.
- Zero sample sizes.
- Invalid significance levels.
- Mismatched expected and observed categories.
- Expected frequencies equal to zero.
- Unequal observed and expected totals.
- Non-rectangular contingency tables.
- Empty contingency rows or columns.
- Missing contingency-table combinations in PostgreSQL.
- Success counts exceeding trial counts.
- Zero pooled proportion variance.
- Numerical convergence failures.
- Invalid probability results.
- Duplicate JavaScript analysis identifiers.
- Invalid report filenames.
- Failed analysis sessions.

These validations prevent many invalid calculations before statistical inference begins.

## Computational Complexity

Let:

- \(k\) represent the number of goodness-of-fit categories.
- \(r\) represent the number of contingency-table rows.
- \(c\) represent the number of contingency-table columns.

| Operation | Time complexity |
|---|---|
| Goodness-of-fit | \(O(k)\) |
| Independence test | \(O(rc)\) |
| One-proportion test | \(O(1)\) |
| Two-proportion test | \(O(1)\) |
| Result reporting | \(O(m)\), for \(m\) stored results |

The numerical gamma-function calculations use iterative convergence algorithms.

Their execution cost depends on the number of iterations required for numerical convergence.

For very large categorical datasets, aggregation should be performed near the data source rather than transferring all raw records into an application.

## Practical Statistical Limitations

The implementations use two-sided tests for both proportion procedures.

One-sided hypotheses require a separate directional-tail calculation.

The proportion z-tests are large-sample approximations. Exact binomial procedures may be preferable for small samples.

The chi-square tests assume independent observations. Repeated measurements, clustered observations, and paired categorical data require methods that account for their dependence structure.

The independence test does not establish causal relationships.

Multiple simultaneous hypothesis tests can increase the probability of false-positive findings. Research involving multiple comparisons should consider appropriate correction procedures, such as Holm's method or the Benjamini-Hochberg procedure.

The SQL implementation provides approximate p-values and is intended to demonstrate relational statistical processing rather than replace a dedicated high-precision statistical calculation.

## Execution Requirements

| Implementation | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Node.js standard library |
| C++ | C++17 compiler | Standard library |
| Java | Java 17 | Java standard library |
| PostgreSQL | PostgreSQL 14+ | PostgreSQL database |

### Python

The script executes numerical validation, example analyses, and JSON report export.

### JavaScript

The file executes validation, asynchronous analysis jobs, event notifications, and JSON report export.

### C++17

Compile with the C++17 language standard.

### Java 17

Compile the source using the Java 17 compiler and execute the resulting class.

### PostgreSQL

Execute the SQL script against a PostgreSQL database using a role with permission to create schemas, tables, types, functions, triggers, and procedures.

The SQL script creates the `statistical_tests` schema and populates it with four sample experiments.

## Technical Interpretation

The four procedures answer different statistical questions.

Goodness-of-fit evaluates a single categorical distribution against an expected model.

Independence evaluates the relationship between two categorical variables.

One-sample proportion testing compares a population proportion with a specified benchmark.

Two-sample proportion testing compares two independent population proportions.

Their results should be interpreted using the underlying hypotheses, assumptions, sampling design, expected frequencies, significance level, and effect sizes rather than the p-value alone.
