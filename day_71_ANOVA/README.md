# ANOVA: Statistical Analysis and Experimental Design

## 1. Introduction

Analysis of Variance (ANOVA) is a statistical method for examining whether the means of two or more populations differ significantly.

ANOVA evaluates differences between group means relative to the variability observed within groups.

The central test statistic is the F-statistic:

\[
F = \frac{MS_{\text{between}}}{MS_{\text{within}}}
\]

Where:

- \(MS_{\text{between}}\) measures variation associated with differences between groups.
- \(MS_{\text{within}}\) measures residual variation within groups.

A sufficiently large F-statistic provides evidence against the null hypothesis.

ANOVA does not automatically identify which groups differ. Post-hoc comparisons are used to investigate specific differences after an appropriate overall analysis.

The implementations cover two principal experimental designs:

- One-way ANOVA.
- Two-way ANOVA with interaction.

They also implement assumption diagnostics, effect-size calculations, multiple-comparison correction, experimental data validation, and statistical reporting.

## 2. Statistical Foundations

### 2.1 Null and alternative hypotheses

For one-way ANOVA involving \(k\) groups, the null hypothesis is:

\[
H_0:\mu_1=\mu_2=\cdots=\mu_k
\]

The alternative hypothesis is:

\[
H_1:\exists i,j \text{ such that } \mu_i\neq\mu_j
\]

The null hypothesis states that all population means are equal.

Rejecting the null hypothesis indicates evidence that at least one population mean differs.

It does not establish that every group differs from every other group.

### 2.2 Sum of squares

ANOVA partitions total variability into separate components.

**Total sum of squares**

\[
SS_T=\sum_{i=1}^{N}(x_i-\bar{x})^2
\]

**Between-group sum of squares**

\[
SS_B=\sum_{j=1}^{k}n_j(\bar{x}_j-\bar{x})^2
\]

**Within-group sum of squares**

\[
SS_W=\sum_{j=1}^{k}\sum_{i=1}^{n_j}
(x_{ij}-\bar{x}_j)^2
\]

The fundamental decomposition is:

\[
SS_T=SS_B+SS_W
\]

Where:

- \(N\) represents the total number of observations.
- \(n_j\) represents the sample size of group \(j\).
- \(\bar{x}_j\) represents the mean of group \(j\).
- \(\bar{x}\) represents the grand mean.

### 2.3 Degrees of freedom

For one-way ANOVA:

| Source | Degrees of freedom |
|---|---:|
| Between groups | \(k-1\) |
| Within groups | \(N-k\) |
| Total | \(N-1\) |

Mean squares are calculated by dividing their corresponding sums of squares by their degrees of freedom.

\[
MS_B=\frac{SS_B}{k-1}
\]

\[
MS_W=\frac{SS_W}{N-k}
\]

The F-statistic compares these two estimates of variability.

## 3. One-Way ANOVA

One-way ANOVA examines the effect of one categorical independent variable on a continuous dependent variable.

The independent variable is called a factor.

Its categories are called factor levels or groups.

### Example: Manufacturing process comparison

A manufacturing organization wants to compare three production processes.

| Group | Observations |
|---|---|
| Control | 21, 23, 22, 24, 20, 22 |
| Treatment A | 25, 27, 26, 28, 24, 27 |
| Treatment B | 30, 32, 29, 31, 33, 30 |

The dependent variable is the measured production response.

The independent variable is the manufacturing process.

The analysis proceeds through:

1. Validate the observations and group definitions.
2. Calculate group means.
3. Calculate the grand mean.
4. Calculate between-group variability.
5. Calculate within-group variability.
6. Calculate degrees of freedom.
7. Calculate mean squares.
8. Calculate the F-statistic.
9. Obtain the upper-tail F probability.
10. Calculate effect sizes.
11. Conduct appropriate post-hoc comparisons.

### Interpretation

A p-value below the selected significance threshold provides evidence against equal population means.

A p-value above the threshold does not prove that the population means are identical.

The analysis must also consider effect size, sample size, uncertainty, assumptions, and practical significance.

## 4. Two-Way ANOVA

Two-way ANOVA evaluates the effects of two categorical independent variables on one continuous dependent variable.

It distinguishes three statistical effects:

- Main effect of Factor A.
- Main effect of Factor B.
- Interaction between Factor A and Factor B.

### Example: Technology and temperature

A production organization investigates whether production technology and operating temperature affect output.

| Technology | Temperature | Observations |
|---|---|---|
| Traditional | Low | 10, 11, 9, 10 |
| Traditional | High | 15, 14, 16, 15 |
| Modern | Low | 13, 12, 14, 13 |
| Modern | High | 23, 22, 24, 23 |

The design contains:

- Factor A: Production technology.
- Factor B: Operating temperature.
- Dependent variable: Production output.

### 4.1 Main effect of Factor A

The main effect of Factor A examines whether average output differs between production technologies, averaging across temperature levels.

### 4.2 Main effect of Factor B

The main effect of Factor B examines whether average output differs between temperature levels, averaging across production technologies.

### 4.3 Interaction effect

An interaction occurs when the effect of one factor depends on the level of another factor.

For example, modern production technology may provide a much greater improvement at high temperature than at low temperature.

The interaction sum of squares is:

\[
SS_{AB}
=
r\sum_{i=1}^{a}\sum_{j=1}^{b}
(\bar{x}_{ij}-\bar{x}_{i.}-\bar{x}_{.j}+\bar{x})^2
\]

Where:

- \(r\) is the number of observations per cell.
- \(\bar{x}_{ij}\) is the mean for a particular factor combination.
- \(\bar{x}_{i.}\) is the marginal mean for Factor A.
- \(\bar{x}_{.j}\) is the marginal mean for Factor B.

The degrees of freedom are:

| Effect | Degrees of freedom |
|---|---:|
| Factor A | \(a-1\) |
| Factor B | \(b-1\) |
| Interaction | \((a-1)(b-1)\) |
| Error | \(ab(r-1)\) |

### 4.4 Interpreting interactions

A statistically significant interaction changes how the main effects should be interpreted.

When an interaction is present, researchers should examine simple effects or suitable comparisons within factor combinations.

An average main effect can conceal important differences between individual combinations.

The supplied implementations use a balanced factorial design with equal replication across cells.

## 5. ANOVA Assumptions

ANOVA results depend on assumptions about the experimental data and statistical model.

### 5.1 Independence of observations

Each observation should be independent of other observations under the assumed experimental design.

Independence is primarily established through sampling and experimental design.

It cannot be demonstrated simply by examining a numerical dataset.

Potential violations include:

- Repeated measurements treated as independent.
- Multiple observations from the same subject.
- Clustered sampling.
- Correlated observations from the same production facility.
- Measurements collected from related individuals.

Repeated-measures and clustered designs may require different statistical models.

### 5.2 Normality of residuals

The normality assumption concerns model residuals, not necessarily the original pooled observations.

Residuals represent deviations from the fitted group or factorial-cell means.

The implementations calculate the Jarque-Bera statistic using sample residual moments.

\[
JB=
\frac{n}{6}
\left[
S^2+\frac{(K-3)^2}{4}
\right]
\]

Where:

- \(S\) is sample skewness.
- \(K\) is sample kurtosis.
- \(n\) is the number of residuals.

Under the null hypothesis of normality, the asymptotic reference distribution is chi-square with two degrees of freedom.

Jarque-Bera is a diagnostic rather than definitive evidence of normality.

Small samples may provide limited power, while very large samples can identify practically minor deviations.

Graphical residual analysis and subject-matter assessment remain important.

### 5.3 Homogeneity of variance

Classical ANOVA assumes equal population variances across groups.

The implementations use a median-centered Levene diagnostic.

For each observation:

\[
Z_{ij}=|X_{ij}-\widetilde{X}_j|
\]

Where \(\widetilde{X}_j\) is the group median.

An ANOVA is then performed on the transformed observations.

This median-centered form is commonly known as the Brown-Forsythe modification of Levene's test.

A small diagnostic p-value indicates evidence of unequal variances.

It does not directly establish that the original ANOVA result is invalid, but it signals that an alternative method or sensitivity analysis may be necessary.

### 5.4 Assumption interpretation

| Assumption | Assessment | Practical implication |
|---|---|---|
| Independence | Experimental design | Consider repeated-measures or clustered models when necessary |
| Normality | Residual diagnostics | Examine skewness, outliers, and residual distributions |
| Equal variances | Levene/Brown-Forsythe | Consider Welch ANOVA for one-way designs |
| Balanced factorial design | Cell counts | Confirm equal replication before using the supplied two-way implementation |

## 6. Post-Hoc Testing

The overall ANOVA F-test determines whether there is evidence of differences among population means.

It does not identify the specific pairs responsible for the difference.

Post-hoc procedures evaluate individual comparisons while controlling the error associated with multiple testing.

### 6.1 Pairwise pooled-variance t-tests

The pooled-variance pairwise test uses a common variance estimate.

\[
s_p^2=
\frac{(n_1-1)s_1^2+(n_2-1)s_2^2}
{n_1+n_2-2}
\]

The test statistic is:

\[
t=
\frac{\bar{x}_1-\bar{x}_2}
{\sqrt{s_p^2(1/n_1+1/n_2)}}
\]

The Python, JavaScript, C++17, Java 17, and PostgreSQL implementations provide pooled-variance pairwise comparisons.

These comparisons are not a complete implementation of Tukey HSD.

Tukey HSD uses the studentized-range distribution to control the family-wise error rate across all pairwise comparisons. A pooled pairwise t-test followed by Holm correction is a distinct procedure and must not be reported as Tukey HSD.

### 6.2 Welch pairwise comparisons

Welch's pairwise test does not assume equal group variances.

Its standard error is:

\[
SE=
\sqrt{\frac{s_1^2}{n_1}+\frac{s_2^2}{n_2}}
\]

Its approximate degrees of freedom are calculated using the Welch-Satterthwaite equation:

\[
df=
\frac{
(v_1+v_2)^2
}{
v_1^2/(n_1-1)+v_2^2/(n_2-1)
}
\]

Where:

\[
v_1=\frac{s_1^2}{n_1},
\qquad
v_2=\frac{s_2^2}{n_2}
\]

Welch pairwise comparisons are useful when the group variances differ.

They should not be confused with the overall Welch one-way ANOVA procedure.

### 6.3 Holm correction

Testing several pairs increases the probability of obtaining at least one false-positive result.

Holm correction controls the family-wise error rate.

Its procedure is:

1. Sort the raw p-values in ascending order.
2. Multiply the smallest p-value by the total number of comparisons.
3. Multiply the next p-value by one fewer comparison.
4. Continue until all comparisons are processed.
5. Apply the cumulative maximum to preserve monotonicity.
6. Limit adjusted p-values to a maximum of one.

For ordered p-values:

\[
p_{(1)}\leq p_{(2)}\leq\cdots\leq p_{(m)}
\]

The adjusted values are:

\[
p_{(i),adj}
=
\min\left(
1,
\max_{j\leq i}
[(m-j+1)p_{(j)}]
\right)
\]

The final adjusted p-values are mapped back to their original comparisons.

### 6.4 Post-hoc method selection

| Method | Variance assumption | Purpose |
|---|---|---|
| Tukey HSD | Equal variances | All pairwise mean comparisons |
| Tukey-Kramer | Equal variances; unequal sample sizes allowed | All pairwise comparisons |
| Holm-adjusted pooled t-tests | Equal variances | Pairwise comparisons with family-wise correction |
| Holm-adjusted Welch tests | Unequal variances allowed | Pairwise comparisons with family-wise correction |
| Games-Howell | Unequal variances allowed | Pairwise comparisons without a common variance assumption |

The implementations provide Holm-adjusted pooled and Welch pairwise tests.

They do not implement Tukey HSD, Tukey-Kramer, or Games-Howell.

## 7. Effect Sizes

Statistical significance does not necessarily indicate practical importance.

Effect sizes quantify the magnitude of an observed effect.

### 7.1 Eta-squared

\[
\eta^2=\frac{SS_B}{SS_T}
\]

Eta-squared measures the proportion of observed total variability associated with the between-group effect in the fitted one-way ANOVA.

Its value ranges from zero to one.

### 7.2 Omega-squared

\[
\omega^2=
\frac{SS_B-df_B MS_W}
{SS_T+MS_W}
\]

Omega-squared adjusts the estimated effect size for sampling bias.

The implementations constrain negative estimates to zero for reporting.

Eta-squared and omega-squared should be interpreted in the context of the research domain, experimental design, and measurement scale.

The one-way effect-size calculations should not be transferred directly to every term in a factorial ANOVA without specifying the appropriate effect-size definition.

## 8. Four Distinct Statistical and Engineering Perspectives

The five source files implement related statistical concepts through different software architectures.

| File | Engineering perspective | Main functionality |
|---|---|---|
| Python | Statistical toolkit | Data analysis, validation, diagnostics, post-hoc testing, JSON reporting |
| JavaScript | Event-driven analysis service | Asynchronous jobs, lifecycle events, immutable experiment records, statistical processing |
| C++17 | Computational engine | STL-based domain modeling, distribution calculations, factorial analysis, validation |
| Java 17 | Enterprise statistical service | Records, immutable datasets, service classes, analysis lifecycle, policy-oriented validation |
| PostgreSQL | Relational statistical system | Experimental data management, integrity enforcement, SQL-based ANOVA, results and reporting |

### 8.1 Python implementation

The Python implementation uses:

- Dataclasses for observations and statistical results.
- Enumerations for analysis and diagnostic states.
- Dictionaries for group-level aggregation.
- Lists for observations and residuals.
- Sets and mappings for factorial organization.
- Exceptions for invalid statistical inputs.
- CSV processing for importing experimental measurements.
- JSON serialization for exporting statistical results.

The incomplete beta function is implemented using a continued-fraction expansion.

This allows the program to calculate F-distribution probabilities without external statistical packages.

The implementation separates:

- Data management.
- Statistical computation.
- Assumption diagnostics.
- Post-hoc comparisons.
- Reporting.

The one-way and two-way analyses use different computational paths because their sums-of-squares decompositions differ.

### 8.2 JavaScript implementation

The JavaScript implementation models statistical analysis as an asynchronous service.

Its engineering components include:

- Private class fields for experiment observations.
- Immutable observation objects.
- Maps for group and factorial-cell aggregation.
- Promises for asynchronous analysis execution.
- EventEmitter for job-state notifications.
- UUIDs for identifying analysis jobs.
- Structured JSON reports.
- Explicit failure and completion states.

The analysis service separates experiment processing from the lifecycle of an analysis job.

A job can move through:

`CREATED → VALIDATING → RUNNING → COMPLETED`

An unsuccessful job transitions to:

`FAILED`

This distinction is useful in applications that process multiple experiments or execute statistical jobs through an API.

### 8.3 C++17 implementation

The C++ implementation emphasizes computational structures and explicit domain modeling.

It uses:

- Structures for observations and results.
- Enumerations for analysis types.
- Maps for group and cell aggregation.
- Vectors for numerical data.
- STL algorithms for aggregation and sorting.
- Exceptions for validation failures.
- Functions for distribution calculations.
- Value-based data structures for statistical results.

The incomplete beta calculation is implemented using an iterative continued fraction.

The balanced two-way implementation computes marginal means, cell means, main-effect sums of squares, interaction sums of squares, and residual sums of squares.

The implementation avoids third-party dependencies and uses standard C++17 facilities.

### 8.4 Java 17 implementation

The Java implementation uses an enterprise-oriented service architecture.

Its domain model includes:

- Immutable `Observation` records.
- `Dataset` as the experiment-data boundary.
- `ANOVAResult` as the statistical result model.
- `EffectResult` for factorial effects.
- `PairwiseResult` for post-hoc decisions.
- `Diagnostic` for assumption assessments.
- `AnalysisService` for job processing.
- Enums for analysis and lifecycle states.
- Custom exceptions for validation failures.

The service records analysis identifiers, timestamps, completion states, and errors.

The separation between statistical calculations and service orchestration supports integration into larger research or enterprise applications.

### 8.5 PostgreSQL implementation

The SQL implementation treats experiments as relational entities.

Its structure separates:

- Experiment definitions.
- Factor definitions.
- Factor levels.
- Observations.
- Analysis executions.
- ANOVA results.
- Assumption diagnostics.
- Pairwise comparisons.

The database enforces data integrity through:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Observation validation triggers.
- Transaction boundaries.
- Experiment-state transitions.

SQL functions calculate one-way and balanced two-way ANOVA results.

The reporting views combine experiment metadata and stored statistical results.

The database is responsible for maintaining consistent experimental records, while the statistical functions perform the calculations.

## 9. PostgreSQL Relational Model

The principal relationships are:

`Experiment`

→ `Factors`

→ `Factor Levels`

→ `Observations`

→ `Analysis Runs`

→ `ANOVA Results`

→ `Assumption Diagnostics`

→ `Post-Hoc Comparisons`

### Entity responsibilities

| Entity | Responsibility |
|---|---|
| `experiments` | Defines an experimental study and its analysis method |
| `factors` | Defines the categorical independent variables |
| `factor_levels` | Stores the categories belonging to each factor |
| `observations` | Stores individual measured responses |
| `analysis_runs` | Records individual statistical executions |
| `anova_results` | Stores F-statistics, p-values, degrees of freedom and effect sizes |
| `assumption_diagnostics` | Stores assumption-test outcomes |
| `posthoc_comparisons` | Stores pairwise results and adjusted p-values |

### Data-integrity decisions

The observation trigger verifies that:

- Factor A belongs to the correct experiment.
- Factor A has the correct role.
- Two-way observations include Factor B.
- One-way observations do not include Factor B.
- Factor B belongs to the correct experiment.
- Factor B has the correct role.
- Observations are not inserted into a closed experiment.

The database also restricts modifications after collection closes.

The experiment lifecycle is controlled through an explicit stored procedure.

## 10. Statistical Workflow

The complete analytical workflow is:

`Experiment Design`

↓

`Factor Definition`

↓

`Factor-Level Definition`

↓

`Observation Collection`

↓

`Data Validation`

↓

`Descriptive Statistics`

↓

`ANOVA Assumption Diagnostics`

↓

`One-Way or Two-Way ANOVA`

↓

`Effect-Size Calculation`

↓

`Post-Hoc Comparisons`

↓

`Multiple-Testing Correction`

↓

`Statistical Reporting`

Each stage has a separate purpose.

Data validation determines whether the experiment is suitable for the selected implementation.

Assumption diagnostics assess the appropriateness of the statistical model.

ANOVA evaluates the specified group or factorial effects.

Post-hoc comparisons investigate particular differences.

Reporting presents the statistical results with their assumptions and limitations.

## 11. Edge Cases and Failure Handling

The implementations explicitly handle several important conditions.

| Condition | Handling |
|---|---|
| Empty dataset | Reject |
| Non-finite observation | Reject |
| Missing factor name | Reject |
| Fewer than two groups | Reject |
| Insufficient observations per group | Reject |
| Missing factorial cell | Reject |
| Unequal factorial replication | Reject |
| Zero residual variance | Handle as a boundary case |
| Invalid degrees of freedom | Reject |
| Invalid p-value | Reject |
| Invalid experiment transition | Reject |
| Unsupported analysis method | Reject |
| Invalid database factor relationship | Reject through trigger |

A zero residual mean square requires special care.

If both between-group and within-group mean squares are zero, the implementation returns an F-statistic of zero and a p-value of one.

If within-group mean square is zero but between-group mean square is positive, the F-statistic is treated as infinite with an upper-tail probability of zero.

Such cases should be reviewed for deterministic data, measurement precision, and experimental design problems.

## 12. Performance Considerations

The implementations use group-based aggregation to avoid repeatedly scanning observations for every statistical calculation.

For \(N\) observations:

- Dataset construction requires \(O(N)\) time.
- Group aggregation requires approximately \(O(N)\) time with hash-based mappings.
- Sorting-based ordering of group labels requires additional \(O(k\log k)\) time.
- One-way ANOVA requires \(O(N)\) statistical computation after grouping.
- Balanced two-way ANOVA requires \(O(N+ab)\) computation for the implemented cell and marginal calculations.
- Pairwise post-hoc comparisons require \(O(k^2)\) comparisons.
- Holm correction requires \(O(k^2\log k)\) time when the number of comparisons is \(O(k^2)\).

For large datasets, storing every observation in memory may be less efficient than database-side aggregation.

The PostgreSQL indexes support experiment-based retrieval, factor-level filtering, analysis-history access, and reporting joins.

The database stores individual observations rather than only precomputed summaries, preserving the information required for subsequent statistical analyses.

## 13. Security and Research Governance

Experimental data may contain confidential organizational or personal information.

The PostgreSQL implementation separates experiment definitions from observations and analysis results.

Production deployment should apply:

- Role-based access control.
- Least-privilege database accounts.
- Restricted schema permissions.
- Encrypted database connections.
- Secure backups.
- Audit logging.
- Controlled data retention.
- Appropriate de-identification of subject identifiers.
- Access restrictions on exported statistical reports.

The sample database uses subject codes instead of personal identifiers.

In production environments, database privileges should prevent unauthorized modification of completed experiments and statistical results.

A stronger deployment can use immutable analysis-run records, versioned datasets, and cryptographic hashes to establish reproducibility.

## 14. Limitations and Statistical Boundaries

The implementations intentionally support a defined subset of ANOVA methods.

| Capability | Implementation status |
|---|---|
| One-way classical ANOVA | Implemented |
| Balanced two-way ANOVA | Implemented |
| Two-way interaction | Implemented |
| Median-centered Levene diagnostic | Implemented |
| Jarque-Bera diagnostic | Implemented |
| Pooled pairwise t-tests | Implemented |
| Welch pairwise comparisons | Implemented |
| Holm correction | Implemented |
| Eta-squared | Implemented for one-way ANOVA |
| Omega-squared | Implemented for one-way ANOVA |
| Tukey HSD | Not implemented |
| Tukey-Kramer | Not implemented |
| Games-Howell | Not implemented |
| Overall Welch one-way ANOVA | Not implemented |
| Repeated-measures ANOVA | Not implemented |
| Mixed-effects ANOVA | Not implemented |
| Unbalanced two-way ANOVA | Not implemented |
| Multifactorial ANOVA beyond two factors | Not implemented |
| Generalized linear models | Not implemented |

The two-way implementations require balanced factorial designs with at least two observations per cell.

This restriction avoids ambiguity associated with different sums-of-squares conventions in unbalanced factorial designs.

For unbalanced designs, researchers must specify the model and sums-of-squares convention, such as Type I, Type II, or Type III.

The Python, JavaScript, C++17, and Java implementations calculate the Jarque-Bera diagnostic and median-centered Levene test without third-party statistical libraries.

The JavaScript, C++, and Java implementations use the same principal mathematical approach for the F-distribution survival probability.

These educational implementations should be validated against an established statistical reference implementation before use in regulated, clinical, or other high-stakes research.

The PostgreSQL script provides a database-oriented implementation of the core calculations, but it does not independently implement the complete assumption-diagnostic and Welch post-hoc workflows.

## 15. Reproducibility and Interpretation

A reproducible ANOVA analysis should preserve:

- The experimental design.
- Factor definitions.
- Factor-level definitions.
- Original observations.
- Exclusion decisions.
- Statistical method.
- Significance threshold.
- Degrees of freedom.
- Sum-of-squares calculations.
- Assumption diagnostics.
- Post-hoc method.
- Multiple-testing adjustment.
- Effect sizes.
- Software implementation version.

A statistical report should not present a p-value as the sole measure of research quality.

Interpretation should distinguish:

- Statistical significance.
- Magnitude of the effect.
- Practical importance.
- Uncertainty.
- Model assumptions.
- Experimental limitations.

A statistically significant difference does not automatically imply a meaningful operational improvement.

Likewise, a statistically non-significant result does not establish equivalence between treatments.

Equivalence requires an appropriate equivalence-testing framework and predefined equivalence margins.

## 16. Execution Requirements

| Deliverable | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10+ | None |
| JavaScript | Node.js 18+ | None |
| C++17 | C++17 compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 14+ | None |

### Python

Run the script directly using Python.

The script performs automated assertions, generates one-way and two-way ANOVA results, calculates diagnostics, performs post-hoc comparisons, and exports `anova_report.json`.

### JavaScript

Run the JavaScript file using Node.js.

The application executes statistical tests, creates an analysis job, emits lifecycle events, calculates statistical results, and exports `anova_javascript_report.json`.

### C++17

Compile using a C++17-compatible compiler.

The executable runs automated statistical tests before processing the manufacturing and factorial examples.

### Java 17

Compile the source file using Java 17 and execute its public class.

The application validates experimental data, executes the enterprise analysis service, and reports the statistical results.

### PostgreSQL

Execute the SQL script using a PostgreSQL 14 or newer database.

The script creates the `anova` schema, defines its relational structures and statistical functions, inserts two experimental datasets, executes the analyses, and generates reporting queries.

The database script uses a transaction so that an unsuccessful execution does not leave a partially committed schema and sample dataset.

## 17. Technical Terminology

| Term | Meaning |
|---|---|
| ANOVA | Analysis of Variance |
| Factor | Categorical independent variable |
| Factor level | Category belonging to a factor |
| Dependent variable | Continuous response being analyzed |
| Grand mean | Mean across all observations |
| Cell mean | Mean for a particular factorial combination |
| Main effect | Average effect of an individual factor |
| Interaction | Effect of one factor depending on another factor |
| Residual | Difference between observed and fitted values |
| Sum of squares | Measure of accumulated squared deviations |
| Mean square | Sum of squares divided by degrees of freedom |
| F-statistic | Ratio of relevant mean squares |
| P-value | Probability of an equally or more extreme statistic under the null hypothesis |
| Post-hoc test | Follow-up comparison examining specific group differences |
| Family-wise error rate | Probability of at least one false rejection across a family of tests |
| Holm correction | Step-down multiple-testing adjustment |
| Eta-squared | Proportion of observed total variability associated with an effect |
| Omega-squared | Bias-adjusted estimate of the proportion of population variability associated with an effect |
| Levene's test | Test for equality of group variances |
| Jarque-Bera test | Residual normality diagnostic based on skewness and kurtosis |
| Balanced design | Factorial design with equal observations in every cell |

## 18. Learning Outcomes

The implementations establish a practical connection between statistical theory and software engineering.

The Python and JavaScript implementations demonstrate statistical computation, numerical functions, validation, and reporting.

The C++ implementation demonstrates numerical algorithms, domain modeling, STL-based computation, and explicit control of statistical operations.

The Java implementation demonstrates immutable statistical models, service-oriented execution, and lifecycle management.

The PostgreSQL implementation demonstrates how experiments, factor definitions, observations, statistical results, and reporting can be maintained within a relational database.

The central distinction remains important:

**ANOVA evaluates differences between means, assumption diagnostics examine the suitability of the statistical model, and post-hoc procedures identify particular group differences while accounting for multiple comparisons.**
