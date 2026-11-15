# Statistical Analysis Project

## Project Overview

This project implements a complete statistical analysis workflow using Python, JavaScript, C++17, Java 17, and PostgreSQL.

The central research question is:

**Is there a statistically measurable relationship between the amount of time students spend studying and their examination performance?**

The project demonstrates how a research question becomes a statistical hypothesis, how observations are transformed into quantitative evidence, how uncertainty is measured, and how findings are communicated.

The same research scenario is implemented through five different technical approaches. Each implementation emphasizes different aspects of statistical computation, application architecture, and data management.

## Research Scenario

The dataset contains 12 synthetic student observations.

| Variable | Description | Measurement |
|---|---|---|
| Participant ID | Unique participant identifier | Integer |
| Study hours | Time spent studying | Hours |
| Exam score | Examination performance | 0–100 |

The dataset is synthetic and is intended for methodological demonstration rather than educational policy decisions.

### Research Question

Does the number of study hours have a statistically significant association with examination scores?

### Research Objectives

- Describe the distribution of study hours and examination scores.
- Measure the direction and strength of their relationship.
- Estimate the linear relationship between the variables.
- Formulate and evaluate statistical hypotheses.
- Calculate confidence intervals.
- Quantify uncertainty using resampling.
- Communicate findings without overstating the available evidence.

## Statistical Foundations

### 1. Population and Sample

A population represents the complete group about which a researcher wants to draw conclusions.

A sample represents the observations actually collected.

In this project:

- Population: students within the target research population.
- Sample: 12 synthetic student observations.
- Observation: one student's study hours and examination score.
- Sample size: 12.

Statistical conclusions based on a sample contain uncertainty. A numerical result from a small sample should not automatically be interpreted as a population-wide relationship.

### 2. Variables

The analysis uses two quantitative variables.

**Independent or explanatory variable:** Study hours.

**Dependent or response variable:** Examination score.

The distinction identifies the direction of the regression model. It does not establish that studying time causes an examination result.

### 3. Descriptive Statistics

Descriptive statistics organize and summarize observed data.

| Measure | Statistical meaning |
|---|---|
| Mean | Arithmetic average |
| Median | Middle value after sorting |
| Standard deviation | Dispersion around the mean |
| Minimum | Smallest observation |
| Maximum | Largest observation |
| Sample size | Number of observations |

The sample standard deviation uses the denominator \(n-1\), reflecting the estimation of population variability from sample observations.

The implementations report descriptive statistics separately for study hours and examination scores.

### 4. Hypothesis Formulation

Hypothesis testing begins with two competing statements.

**Null hypothesis (H0):**

The population correlation between study hours and examination scores equals zero.

\[
H_0:\rho=0
\]

**Alternative hypothesis (H1):**

The population correlation differs from zero.

\[
H_1:\rho\neq 0
\]

This is a two-sided hypothesis test.

The significance level is:

\[
\alpha=0.05
\]

The significance level represents the prespecified probability threshold for rejecting the null hypothesis under the testing procedure.

It is not the probability that the null hypothesis is true.

## Relationship Analysis

### 5. Pearson Correlation

Pearson's correlation coefficient measures the strength and direction of a linear association between two quantitative variables.

\[
r=
\frac{
\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})
}{
\sqrt{
\sum_{i=1}^{n}(x_i-\bar{x})^2
\sum_{i=1}^{n}(y_i-\bar{y})^2
}
}
\]

The coefficient lies between -1 and +1.

| Correlation | Interpretation |
|---|---|
| +1 | Perfect positive linear relationship |
| Between 0 and +1 | Positive linear relationship |
| 0 | No linear correlation |
| Between -1 and 0 | Negative linear relationship |
| -1 | Perfect negative linear relationship |

A correlation near zero does not necessarily establish the absence of every possible relationship. Nonlinear relationships may exist even when Pearson correlation is small.

The implementations reject undefined correlations when either variable has zero variance.

### 6. Simple Linear Regression

Linear regression models the expected relationship between an explanatory variable and a response variable.

\[
\hat{y}=\beta_0+\beta_1x
\]

Where:

- \(\hat{y}\) is the predicted examination score.
- \(x\) is study time.
- \(\beta_0\) is the intercept.
- \(\beta_1\) is the regression slope.

The slope measures the expected change in the predicted examination score for a one-unit increase in study hours.

The regression implementations calculate:

- Slope.
- Intercept.
- Predicted values.
- Residuals.
- R-squared.
- Root Mean Squared Error.
- Mean Absolute Error.

### 7. Model Evaluation

R-squared measures the proportion of observed response-variable variation explained by the fitted linear model.

\[
R^2=1-\frac{SS_{res}}{SS_{tot}}
\]

RMSE measures the square root of the average squared prediction error.

\[
RMSE=
\sqrt{
\frac{1}{n}
\sum_{i=1}^{n}(y_i-\hat{y}_i)^2
}
\]

MAE measures the average absolute prediction error.

\[
MAE=
\frac{1}{n}
\sum_{i=1}^{n}|y_i-\hat{y}_i|
\]

These metrics describe model fit. A high R-squared does not establish causality, and predictive accuracy should be assessed on independent data when prediction is the objective.

## Hypothesis Testing and Statistical Inference

### 8. Permutation Testing

Permutation testing evaluates how unusual an observed statistic would be under a null hypothesis that makes the relevant observations exchangeable.

The implemented procedure:

1. Calculate the observed absolute Pearson correlation.
2. Keep the study-hour observations fixed.
3. Randomly reorder the examination scores.
4. Recalculate the correlation.
5. Count permutations producing a statistic at least as extreme as the observed statistic.
6. Repeat the procedure.
7. Calculate the Monte Carlo p-value.

The estimated p-value is:

\[
p=
\frac{b+1}{B+1}
\]

Where:

- \(b\) is the number of extreme permutation statistics.
- \(B\) is the number of permutations.

The plus-one correction prevents a reported Monte Carlo p-value of exactly zero.

The implementations use 10,000 permutations.

The procedure assumes exchangeability under the null hypothesis. If observations are clustered, repeated measurements, or otherwise dependent, the permutation scheme must preserve the relevant dependence structure.

### 9. P-Value Interpretation

A p-value measures how extreme the observed test statistic is relative to the reference distribution under the null hypothesis.

Decision rule:

\[
p<0.05 \Rightarrow \text{Reject }H_0
\]

\[
p\geq0.05 \Rightarrow \text{Fail to reject }H_0
\]

Failing to reject the null hypothesis does not prove that the population correlation equals zero.

Statistical significance also does not establish practical importance.

### 10. Bootstrap Confidence Intervals

Bootstrap resampling estimates the sampling uncertainty of a statistic by repeatedly drawing samples with replacement.

The project uses paired bootstrap resampling.

This distinction is important: study hours and examination scores belong to the same participant. Resampling the two columns independently would destroy their observed pairing.

The procedure:

1. Draw 12 observations with replacement.
2. Preserve both measurements belonging to each selected participant.
3. Calculate the statistic.
4. Repeat 5,000 times.
5. Sort the resulting estimates.
6. Extract the lower and upper percentile limits.

For a 95% percentile bootstrap interval:

\[
CI_{95\%}=
\left[
Q_{0.025},
Q_{0.975}
\right]
\]

The project calculates intervals for:

- Pearson correlation.
- Regression slope.

A bootstrap interval is an estimate of statistical uncertainty, not a guarantee that the true parameter lies inside the interval with 95% probability after observing the data.

With a small sample, bootstrap intervals can be unstable. Degenerate resamples, influential observations, and limited representation of the population should be considered.

### 11. Fisher Transformation in PostgreSQL

The PostgreSQL implementation calculates an approximate confidence interval for Pearson correlation using Fisher's transformation.

\[
z=\frac{1}{2}
\ln\left(\frac{1+r}{1-r}\right)
\]

The approximate standard error is:

\[
SE_z=\frac{1}{\sqrt{n-3}}
\]

The interval is calculated on the transformed scale and converted back using the hyperbolic tangent function.

\[
CI=
\tanh
\left(
z\pm z_{\alpha/2}SE_z
\right)
\]

The SQL implementation supports 90%, 95%, and 99% confidence levels.

This is a normal-approximation interval. Its reliability depends on sample size and the assumptions underlying the correlation model.

The SQL implementation does not claim that Fisher intervals and bootstrap percentile intervals are interchangeable.

## Interpretation and Reporting

### 12. Statistical Conclusions

A statistical report should distinguish the following:

| Component | Question answered |
|---|---|
| Descriptive statistics | What does the observed sample look like? |
| Correlation | How strongly are the variables linearly associated? |
| Regression | What linear relationship describes the observations? |
| Hypothesis test | How unusual is the observed statistic under H0? |
| Confidence interval | What range of parameter values is compatible with the estimation procedure? |
| Model evaluation | How closely does the fitted model describe the observations? |

A defensible conclusion should include:

- Sample size.
- Statistical method.
- Estimated effect.
- Confidence interval.
- P-value.
- Significance threshold.
- Important limitations.
- Distinction between association and causation.

A statistically significant relationship does not prove that increasing study hours causes higher examination scores. Other variables, such as prior knowledge, teaching quality, learning conditions, and participant characteristics, may influence both measurements.

## Software Architecture

### 13. Python Implementation

The Python implementation emphasizes statistical modeling and reproducible experimentation.

| Component | Responsibility |
|---|---|
| Observation | Validated immutable observation |
| StatisticalAnalyzer | Core statistical calculations |
| bootstrap_interval | Percentile bootstrap estimation |
| permutation_test | Monte Carlo hypothesis testing |
| regression | Linear model evaluation |
| generate_report | Structured reporting |
| run_validation_tests | Mathematical and input validation |

Python uses dataclasses, type annotations, exceptions, dictionaries, lists, and standard-library statistical functions.

The random generator is initialized with a fixed seed to make the resampling sequence reproducible.

The report is written as JSON through an atomic replacement workflow.

### 14. JavaScript Implementation

The JavaScript implementation uses an event-driven architecture.

| Component | Responsibility |
|---|---|
| StatisticalEngine | Statistical processing |
| EventEmitter | Analysis lifecycle notifications |
| createRandom | Deterministic random number generation |
| bootstrap | Resampling-based estimation |
| permutationTest | Asynchronous permutation inference |
| regression | Model fitting |
| saveReport | Persistent report storage |

The analysis emits lifecycle events:

- `analysisStarted`
- `progress`
- `analysisCompleted`
- `analysisFailed`

The permutation procedure periodically yields control to the Node.js event loop through `setImmediate`.

This makes progress notifications possible without introducing third-party packages.

### 15. C++17 Implementation

The C++ implementation emphasizes computational control and explicit data structures.

| Component | Responsibility |
|---|---|
| Observation | Statistical observation structure |
| StatisticalEngine | Statistical processing |
| ConfidenceInterval | Interval representation |
| RegressionResult | Regression output |
| AnalysisResult | Consolidated analytical output |
| printReport | Human-readable reporting |
| saveReport | Persistent report storage |

The implementation uses:

- STL vectors for observations.
- Maps for descriptive statistics.
- Algorithms for sorting and aggregation.
- Mersenne Twister random-number generation.
- Standard exceptions for failure handling.

Bootstrap samples preserve complete observations, preventing accidental separation of paired variables.

### 16. Java 17 Implementation

The Java implementation uses explicit enterprise-oriented domain types and service separation.

| Component | Responsibility |
|---|---|
| Observation | Immutable participant measurement |
| DatasetRepository | Validated dataset storage |
| StatisticalMath | Mathematical calculations |
| InferenceService | Bootstrap and permutation inference |
| AnalysisService | Analysis orchestration |
| ReportService | Reporting and persistence |
| AnalysisReport | Immutable analysis result |

Java records provide concise immutable representations of observations and analytical results.

The repository rejects duplicate participant identifiers and stores the validated dataset as an immutable list.

The separation between statistical mathematics, inference, orchestration, and reporting improves maintainability.

### 17. PostgreSQL Implementation

The PostgreSQL implementation demonstrates relational data management and database-side statistical analysis.

| Database object | Purpose |
|---|---|
| datasets | Research dataset metadata |
| participants | Participant identifiers |
| observations | Study hours and examination scores |
| analysis_runs | Hypotheses and execution configuration |
| statistical_results | Persisted analytical findings |
| observation_audit | Observation modification history |
| v_descriptive_statistics | Descriptive and regression view |
| correlation_confidence_interval | Fisher-transformation calculation |
| generate_statistical_report | Reporting function |
| complete_analysis | Transactional workflow procedure |

PostgreSQL provides built-in aggregate and statistical regression functions, including:

- `AVG`
- `STDDEV_SAMP`
- `CORR`
- `REGR_SLOPE`
- `REGR_INTERCEPT`
- `REGR_R2`

Constraints enforce measurement ranges, unique participant references, valid significance levels, and valid result ranges.

Indexes support common dataset and analysis retrieval patterns.

The audit trigger records inserts, updates, and deletes on observations.

The workflow procedure deliberately refuses to finalize an analysis without a valid permutation p-value. Descriptive SQL aggregates alone cannot substitute for a completed permutation test.

## Technical Workflow

### 18. End-to-End Statistical Process

The project follows this research pipeline:

Research question  
↓  
Population and sample definition  
↓  
Observation collection  
↓  
Data validation  
↓  
Descriptive statistics  
↓  
Hypothesis formulation  
↓  
Correlation analysis  
↓  
Linear regression  
↓  
Permutation hypothesis testing  
↓  
Bootstrap confidence intervals  
↓  
Model evaluation  
↓  
Statistical interpretation  
↓  
Report generation

Each stage has a separate analytical purpose. A model estimate, a statistical test, and a confidence interval provide different kinds of evidence.

## Execution

### 19. Python

Requirements: Python 3.10 or later.

Save the first implementation as `statistical_analysis.py`.

Run it using:

`python statistical_analysis.py`

Output:

`statistical_analysis_report.json`

### 20. JavaScript

Requirements: Node.js 18 or later.

Save the second implementation as `statistical_analysis.js`.

Run it using:

`node statistical_analysis.js`

Output:

`statistical_analysis_report.json`

### 21. C++17

Requirements: C++17-compatible compiler.

Save the third implementation as `statistical_analysis.cpp`.

Compile using:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic statistical_analysis.cpp -o statistical_analysis`

Run using:

`./statistical_analysis`

On Windows:

`statistical_analysis.exe`

Output:

`statistical_analysis_report.txt`

### 22. Java 17

Requirements: JDK 17 or later.

Save the fourth implementation as `StatisticalAnalysis.java`.

Compile using:

`javac StatisticalAnalysis.java`

Run using:

`java StatisticalAnalysis`

Output:

`statistical_analysis_report.txt`

### 23. PostgreSQL

Requirements: PostgreSQL 14 or later.

Save the fifth implementation as `statistical_analysis.sql`.

Execute using:

`psql -U postgres -d your_database -f statistical_analysis.sql`

The script creates the `statistical_lab` schema and its associated relational objects.

It drops and recreates that schema at the beginning. Existing objects inside that schema are therefore removed.

Use a dedicated development database when executing the complete script.

## Validation and Reliability

### 24. Input Validation

The implementations enforce:

- Positive participant identifiers.
- Unique participant identifiers.
- Finite numerical observations.
- Non-negative study hours.
- Examination scores between 0 and 100.
- Sufficient sample size.
- Non-zero variation in both variables.
- Valid confidence levels.
- Minimum bootstrap iteration counts.
- Minimum permutation iteration counts.

Invalid inputs are rejected rather than silently incorporated into statistical calculations.

### 25. Edge Cases

| Condition | Expected behavior |
|---|---|
| Empty dataset | Reject analysis |
| Fewer than four observations | Reject analysis |
| Duplicate participant IDs | Reject dataset |
| Negative study hours | Reject observation |
| Examination score above 100 | Reject observation |
| Constant study hours | Reject correlation or regression |
| Constant examination scores | Reject correlation |
| Invalid confidence level | Reject interval request |
| Too few resampling iterations | Reject inference request |
| Degenerate bootstrap sample | Exclude invalid estimate |
| File-writing failure | Report execution failure |

### 26. Computational Complexity

Let \(n\) represent sample size, \(B\) the number of bootstrap iterations, and \(P\) the number of permutations.

| Operation | Approximate time complexity |
|---|---|
| Mean | O(n) |
| Standard deviation | O(n) |
| Pearson correlation | O(n) |
| Linear regression | O(n) |
| Bootstrap estimation | O(Bn) |
| Permutation testing | O(Pn) |
| Sorting bootstrap estimates | O(B log B) |

The primary computational cost comes from resampling.

For large datasets, parallel execution, vectorized numerical libraries, and carefully designed permutation schemes may substantially reduce runtime.

Parallel implementations must manage independent random streams correctly to preserve reproducibility.

## Limitations and Research Considerations

### 27. Small Sample Size

Twelve observations are insufficient for strong population-wide conclusions in many research settings.

The example demonstrates computational methods rather than establishing a general educational relationship.

### 28. Observational Data

The dataset does not result from a randomized experiment.

The analysis cannot isolate the causal effect of study hours.

### 29. Model Assumptions

Pearson correlation measures linear association.

Simple linear regression assumes an appropriate linear functional form. Classical regression inference additionally requires attention to residual behavior, independence, homoscedasticity, and distributional assumptions where relevant.

The bootstrap intervals and permutation test in the source implementations use their respective resampling assumptions and should not be interpreted as universal replacements for model-based inference.

### 30. Multiple Testing

Conducting many hypothesis tests increases the probability of obtaining apparently significant findings by chance.

A larger research project should prespecify primary hypotheses and apply appropriate multiple-comparison procedures when multiple confirmatory tests are conducted.

### 31. Data Governance

Statistical reporting should preserve:

- Dataset provenance.
- Observation definitions.
- Analysis parameters.
- Random seeds.
- Sample size.
- Statistical method.
- Confidence level.
- Hypothesis decisions.
- Report-generation timestamps.

The PostgreSQL audit mechanism provides a basic record of observation changes. A production research system would also require appropriate database roles, access controls, backup policies, retention rules, and controlled execution permissions.

## Expected Research Deliverable

The completed project demonstrates a reproducible statistical analysis workflow in five programming and database environments.

The central analytical distinction remains consistent throughout the implementations:

- Descriptive statistics summarize the observed sample.
- Correlation quantifies linear association.
- Regression describes a fitted relationship.
- Hypothesis testing evaluates evidence against a specified null hypothesis.
- Confidence intervals quantify estimation uncertainty.
- Statistical reporting communicates findings within the limits of the research design.

The numerical evidence must always be interpreted in relation to the sample, assumptions, research question, and limitations of the underlying data.
