# Regression Diagnostics: Multicollinearity, Heteroscedasticity, Residual Analysis and Influence Points

## 1. Technical Scope

Regression diagnostics are procedures used to evaluate whether a fitted regression model satisfies the assumptions and numerical conditions required for reliable statistical interpretation.

A regression model can produce a high coefficient of determination while still exhibiting serious estimation or inference problems. Diagnostic analysis examines predictor relationships, error variance, residual behavior, and individual observations that may disproportionately affect estimated coefficients.

This project implements a diagnostic workflow using five independent technical approaches:

| Implementation | Engineering perspective | Main responsibilities |
|---|---|---|
| Python | Statistical computation | OLS, VIF, Breusch-Pagan, Jarque-Bera, influence and HC3 |
| JavaScript | Event-driven analysis | Diagnostic events, policy evaluation and asynchronous reporting |
| C++17 | Numerical engine | Matrix operations, governance thresholds and merge-like diagnostic decisions |
| Java 17 | Enterprise architecture | Immutable domain objects, diagnostic rules and controlled model lifecycle |
| PostgreSQL | Relational persistence | Observations, predictors, policies, test results, reporting and integrity |

The implementations share a common statistical domain but use different programming and architectural techniques.

## 2. Regression Model Fundamentals

Multiple linear regression represents a response variable as a linear combination of predictors:

\[
y_i = \beta_0 + \beta_1x_{i1}
+ \beta_2x_{i2} + \cdots
+ \beta_kx_{ik} + \epsilon_i
\]

Where:

- \(y_i\) is the observed response.
- \(\beta_0\) is the intercept.
- \(\beta_j\) represents the coefficient of predictor \(j\).
- \(x_{ij}\) is the value of predictor \(j\) for observation \(i\).
- \(\epsilon_i\) is the random error.

The Ordinary Least Squares method estimates coefficients by minimizing the residual sum of squares:

\[
SSE = \sum_{i=1}^{n}(y_i-\hat y_i)^2
\]

In matrix notation:

\[
\hat{\beta}=(X^TX)^{-1}X^Ty
\]

This expression requires an invertible design matrix cross-product. Perfect multicollinearity makes the ordinary inverse unavailable.

The implementations use Gaussian elimination with partial pivoting for their educational numerical engines. This approach makes the underlying computations explicit, although production statistical systems should consider QR decomposition or singular value decomposition for improved numerical stability.

### 2.1 Fitted values and residuals

The fitted value is:

\[
\hat y_i = x_i^T\hat{\beta}
\]

The residual is:

\[
e_i = y_i-\hat y_i
\]

Residuals represent the differences between observed and fitted response values.

Residual analysis is central to the diagnostic process because it provides evidence about model specification, error variance, unusual observations, and potential departures from distributional assumptions.

### 2.2 Coefficient of determination

\[
R^2 = 1-\frac{SSE}{SST}
\]

Adjusted R-squared accounts for the number of predictors:

\[
R^2_{adj}
=
1-(1-R^2)\frac{n-1}{n-k-1}
\]

A high R-squared does not establish that a model is correctly specified or that its assumptions hold.

## 3. Multicollinearity

Multicollinearity occurs when two or more explanatory variables have substantial linear relationships.

It is important to distinguish correlation between predictors from correlation between predictors and the response. Multicollinearity concerns the predictor matrix.

### 3.1 Consequences

Multicollinearity can produce:

- Unstable coefficient estimates.
- Increased coefficient standard errors.
- Wide confidence intervals.
- Unexpected coefficient signs.
- Sensitivity to changes in the observations.
- Difficulty separating individual predictor effects.

A model may retain high predictive accuracy while individual coefficient interpretations become unreliable.

### 3.2 Correlation matrix

For predictors \(X_j\) and \(X_l\), the Pearson correlation coefficient is:

\[
r_{jl} =
\frac{
\sum_i(x_{ij}-\bar{x}_j)(x_{il}-\bar{x}_l)
}{
\sqrt{
\sum_i(x_{ij}-\bar{x}_j)^2
\sum_i(x_{il}-\bar{x}_l)^2
}
}
\]

A correlation matrix identifies pairwise linear relationships.

Pairwise correlations cannot detect every form of multicollinearity. A predictor may be strongly explained by a combination of several other predictors even when no individual pairwise correlation appears extreme.

### 3.3 Variance Inflation Factor

VIF evaluates how strongly a predictor can be explained by the remaining predictors.

For predictor \(j\):

\[
VIF_j = \frac{1}{1-R_j^2}
\]

Here, \(R_j^2\) is obtained from an auxiliary regression in which predictor \(j\) becomes the dependent variable and the other predictors become explanatory variables.

Interpretation commonly uses the following screening ranges:

| VIF | Interpretation |
|---:|---|
| Approximately 1 | Little or no linear inflation |
| 1 to 5 | Usually limited inflation |
| 5 to 10 | Potentially substantial inflation |
| Above 10 | Serious inflation requiring investigation |

These are screening conventions rather than universal statistical decision boundaries.

### 3.4 Implementation

Python and JavaScript perform auxiliary regressions for each predictor.

C++ uses STL containers and matrix operations to construct the auxiliary design matrices.

Java encapsulates VIF evaluation in the regression service and exposes results to a dedicated diagnostic rule.

PostgreSQL stores predictor-specific VIF values in `predictor_diagnostic`. The supplied values represent numerical results from an external regression calculation. The SQL script does not incorrectly claim that an ordinary relational aggregate calculates general multiple-predictor VIF.

### 3.5 Practical responses

Potential responses include:

- Removing redundant predictors when justified by domain knowledge.
- Combining closely related measurements.
- Applying regularization.
- Collecting additional observations with more independent predictor variation.
- Retaining correlated predictors when the research objective requires them, while acknowledging coefficient uncertainty.

Removing predictors solely to reduce VIF can introduce omitted-variable bias.

## 4. Heteroscedasticity

Heteroscedasticity occurs when the conditional variance of the regression error is not constant.

The classical homoscedasticity assumption is:

\[
Var(\epsilon_i|X)=\sigma^2
\]

Under heteroscedasticity:

\[
Var(\epsilon_i|X)=\sigma_i^2
\]

The error variance changes across observations or predictor values.

### 4.1 Consequences

Under the standard exogeneity assumptions, OLS coefficients can remain unbiased, but conventional OLS standard errors may become incorrect.

This can affect:

- Hypothesis tests.
- Confidence intervals.
- Statistical significance.
- Model comparison.
- Decisions based on coefficient uncertainty.

### 4.2 Residual plots

A residual-versus-fitted plot is useful for detecting changes in residual spread.

Common patterns include:

| Pattern | Possible interpretation |
|---|---|
| Random, approximately constant spread | Consistent with homoscedasticity |
| Funnel-shaped spread | Possible heteroscedasticity |
| Increasing residual dispersion | Variance may increase with fitted values |
| Curved pattern | Possible nonlinear model specification |
| Clusters | Possible group-specific variance or missing structure |

Visual evidence should be interpreted with the data-generating process in mind.

### 4.3 Breusch-Pagan test

The Breusch-Pagan procedure evaluates whether squared residuals are systematically related to explanatory variables.

An auxiliary regression is fitted:

\[
e_i^2 =
\gamma_0+\gamma_1x_{i1}
+\cdots+\gamma_kx_{ik}+u_i
\]

The Lagrange Multiplier statistic is:

\[
LM=nR^2_{aux}
\]

Under the conventional null hypothesis:

\[
H_0: Var(\epsilon_i|X)=\sigma^2
\]

The statistic is asymptotically compared with a chi-square distribution having \(k\) degrees of freedom.

A low p-value provides evidence against constant conditional variance.

The test does not identify every possible variance pattern and should not be treated as proof that heteroscedasticity is absent when its p-value is large.

### 4.4 HC3 robust standard errors

The Python, JavaScript, C++17 and Java 17 implementations calculate HC3 heteroscedasticity-consistent standard errors.

The HC3 covariance estimator is:

\[
\widehat{Var}_{HC3}(\hat{\beta}) =
(X^TX)^{-1}
X^T
\widehat{\Omega}_{HC3}
X
(X^TX)^{-1}
\]

Where:

\[
\widehat{\Omega}_{HC3}
=
diag\left(
\frac{e_i^2}{(1-h_{ii})^2}
\right)
\]

The diagonal term \(h_{ii}\) represents the leverage of observation \(i\).

HC3 adjusts the contribution of observations according to their leverage and residual size.

It changes estimated covariance and standard errors, not the original OLS coefficient estimates.

Robust standard errors do not correct omitted variables, endogeneity, nonlinear relationships, or incorrect functional forms.

## 5. Residual Analysis

Residual analysis evaluates the differences between observed and fitted values.

A residual is not identical to the unobservable regression error. Residuals are calculated after estimating the model and are constrained by the fitted regression structure.

### 5.1 Residual mean

For OLS with an intercept:

\[
\sum_{i=1}^{n}e_i \approx 0
\]

This is an algebraic property of the fitted model rather than independent evidence that the regression assumptions are satisfied.

### 5.2 Residual variance

The residual mean square is:

\[
MSE=\frac{SSE}{n-k-1}
\]

The residual standard error is:

\[
RSE=\sqrt{MSE}
\]

The denominator accounts for the number of estimated regression parameters.

### 5.3 Normality assessment

Normality is relevant to certain finite-sample inferential procedures under the classical linear model.

The Jarque-Bera statistic evaluates skewness and kurtosis:

\[
JB =
\frac{n}{6}
\left[
S^2+\frac{(K-3)^2}{4}
\right]
\]

Where:

- \(S\) represents sample skewness.
- \(K\) represents sample kurtosis.

Under the conventional asymptotic reference distribution, the statistic follows a chi-square distribution with two degrees of freedom.

A low p-value indicates evidence against normality.

The Jarque-Bera test is not a substitute for examining residual plots or quantile-quantile plots. It can also become highly sensitive to small distributional departures in large samples.

### 5.4 Residual diagnostic distinctions

| Diagnostic | Primary question |
|---|---|
| Residual mean | Are residuals centered around zero? |
| Residual variance | How large is the remaining unexplained variation? |
| Residual-versus-fitted plot | Is there a systematic residual pattern? |
| Normal Q-Q plot | Do residual quantiles approximately follow a normal distribution? |
| Jarque-Bera | Is there statistical evidence of skewness or kurtosis departure? |
| Residual-versus-predictor plot | Does a predictor exhibit unexplained structure? |

Normality is not required for the OLS coefficient calculation itself.

## 6. Influence Points and Leverage

An unusual observation does not necessarily have a substantial influence on a fitted regression model.

Three related concepts must be distinguished.

### 6.1 Outliers

An outlier has an unusual response value relative to the fitted model.

A large residual is an indication that the observation is poorly explained by the fitted relationship.

### 6.2 Leverage

Leverage measures how unusual an observation's predictor values are relative to the predictor distribution.

The hat matrix is:

\[
H=X(X^TX)^{-1}X^T
\]

The leverage of observation \(i\) is:

\[
h_{ii}=H_{ii}
\]

For a regression model with an intercept and \(k\) predictors:

\[
\sum_{i=1}^{n}h_{ii}=k+1
\]

Average leverage is therefore:

\[
\bar h=\frac{k+1}{n}
\]

The frequently used screening threshold is:

\[
h_{ii}>\frac{2(k+1)}{n}
\]

High leverage alone does not establish that an observation is influential.

### 6.3 Studentized residuals

An internally studentized residual is:

\[
r_i =
\frac{e_i}
{\sqrt{MSE(1-h_{ii})}}
\]

It adjusts the residual scale according to leverage.

Values with large absolute magnitude deserve investigation.

The implementation uses the full-model MSE. This is an internal studentization calculation, not an externally studentized residual based on deleting the observation and refitting the model.

### 6.4 Cook's distance

Cook's distance evaluates the combined effect of residual magnitude and leverage.

\[
D_i =
\frac{r_i^2h_{ii}}
{(k+1)(1-h_{ii})}
\]

A common screening convention is:

\[
D_i>\frac{4}{n}
\]

Cook's distance measures the potential influence of an observation on the fitted regression coefficients.

An observation with a small residual can still be influential when its leverage is sufficiently high.

### 6.5 Influence investigation

An observation exceeding a screening threshold should be investigated rather than automatically removed.

The investigation should consider:

- Data-entry errors.
- Measurement errors.
- Incorrect units.
- Unusual but legitimate operating conditions.
- Population changes.
- Missing explanatory variables.
- Model misspecification.
- Whether the observation belongs to the intended target population.

A useful sensitivity analysis compares the original fitted model with a separately refitted model after a documented exclusion.

The original dataset should remain preserved.

## 7. Relationship Between Diagnostic Procedures

The four principal diagnostic areas answer different statistical questions.

| Area | Main object | Main diagnostic | Primary implication |
|---|---|---|---|
| Multicollinearity | Predictor matrix | VIF | Coefficient instability |
| Heteroscedasticity | Conditional error variance | Breusch-Pagan | Conventional standard-error reliability |
| Residual analysis | Model errors and residual patterns | Plots and Jarque-Bera | Distributional and specification assessment |
| Influence analysis | Individual observations | Leverage and Cook's distance | Sensitivity of fitted coefficients |

The diagnostic procedures are complementary.

For example, a model may exhibit high multicollinearity and heteroscedasticity simultaneously. Correcting one problem does not automatically correct the other.

Likewise, HC3 standard errors do not eliminate multicollinearity, and removing an influential observation does not guarantee normally distributed residuals.

## 8. End-to-End Diagnostic Workflow

The implementations follow this analytical sequence:

    Raw observations
          |
          v
    Dataset validation
          |
          v
    Predictor matrix construction
          |
          v
    OLS estimation
          |
          v
    Fitted values and residuals
          |
          +---------------------------+
          |                           |
          v                           v
    Multicollinearity             Residual analysis
    Correlation and VIF           Normality and patterns
          |                           |
          v                           v
    Predictor assessment         Breusch-Pagan test
          |                           |
          +-------------+-------------+
                        |
                        v
                Influence analysis
                Leverage and Cook's D
                        |
                        v
                HC3 standard errors
                        |
                        v
                Diagnostic policy
                        |
                        v
                Findings and report

The workflow separates model estimation from diagnostic evaluation.

A fitted model is a mathematical representation of the observed data. Diagnostic results are evidence used to determine whether the model is suitable for a particular analytical purpose.

## 9. Python Implementation

The Python script uses standard-library components and explicit numerical routines.

### 9.1 Domain structures

`Observation` is a dataclass containing:

- An observation identifier.
- A list of predictor values.
- The response value.

`DiagnosticThresholds` stores configurable screening thresholds.

`DiagnosticResult` records the name, statistic, threshold, severity, and explanation of a finding.

`DiagnosticStatus` distinguishes passing, warning, and failing results.

### 9.2 Numerical implementation

The numerical engine implements:

- Gaussian elimination with partial pivoting.
- Matrix inversion through repeated linear-system solutions.
- Matrix multiplication and transposition.
- OLS coefficient estimation.
- Auxiliary regressions for VIF.
- Auxiliary regression for Breusch-Pagan.
- Leverage calculation from the hat matrix.
- Studentized residuals.
- Cook's distance.
- HC3 standard errors.

The implementation avoids external numerical libraries to make the mathematical operations inspectable.

### 9.3 Reporting and validation

The script includes:

- Input validation.
- Duplicate identifier detection.
- Non-finite value detection.
- Singular matrix handling.
- Statistical assertions.
- JSON report generation.
- Temporary-file replacement for safer report writing.

The report includes coefficient estimates, fit statistics, VIF values, test statistics, robust standard errors, and diagnostic findings.

## 10. JavaScript Implementation

The JavaScript file presents a complementary event-driven design.

### 10.1 Diagnostic event bus

`DiagnosticEventBus` uses a `Map` of event names to `Set` collections of listeners.

It provides:

- Event registration.
- Listener removal.
- Event publication.
- Independent listener execution.
- Listener failure isolation.

The fitted model emits an event after successful estimation.

This separates numerical execution from reporting and downstream processing.

### 10.2 Model lifecycle

The model moves through two principal states:

| State | Meaning |
|---|---|
| INITIALIZED | Dataset validated and design matrix constructed |
| FITTED | Coefficients and residuals calculated |

The diagnostic policy requires a fitted model.

Repeated fitting is rejected to avoid accidental state replacement.

### 10.3 Policy evaluation

`DiagnosticPolicy` evaluates statistical results against configurable thresholds.

Its output includes:

- Predictor-specific VIF findings.
- Breusch-Pagan results.
- Jarque-Bera results.
- Observation-level influence findings.
- HC3 standard errors.

### 10.4 Asynchronous reporting

The report is exported through Node.js file operations.

The temporary-file approach reduces the risk of leaving an incomplete report when file writing fails.

The event bus is synchronous. File persistence is asynchronous and handled using promises.

## 11. C++17 Implementation

The C++ implementation emphasizes numerical control and explicit domain structures.

### 11.1 Domain structures

The implementation defines:

- `Observation`
- `Finding`
- `Policy`
- `Severity`
- `RegressionEngine`

STL vectors represent observations, coefficients, residuals, and matrices.

### 11.2 Numerical processing

The matrix engine performs:

- Transposition.
- Multiplication.
- Linear-system solving.
- Matrix inversion.
- Auxiliary regression.
- Statistical probability calculations.

Partial pivoting is used to reduce numerical instability during Gaussian elimination.

### 11.3 Diagnostic engine

`RegressionEngine` exposes independent diagnostic methods:

| Method | Responsibility |
|---|---|
| `fit()` | Estimate regression coefficients |
| `leverage()` | Calculate diagonal hat-matrix values |
| `studentizedResiduals()` | Calculate internally studentized residuals |
| `cooksDistance()` | Calculate influence measures |
| `vif()` | Evaluate predictor inflation |
| `breuschPagan()` | Evaluate conditional variance |
| `jarqueBera()` | Evaluate residual normality |
| `hc3StandardErrors()` | Calculate robust standard errors |
| `evaluate()` | Apply diagnostic policy |

The implementation explicitly checks that the model is fitted before diagnostic calculations.

The leverage trace test provides an independent numerical validation:

\[
trace(H)=k+1
\]

This is an important invariant for regression models with full-rank design matrices.

## 12. Java 17 Enterprise Implementation

The Java implementation separates statistical computation, policy evaluation, and diagnostic reporting.

### 12.1 Immutable domain objects

Java records represent observations, model results, diagnostic findings, and policy configurations.

Immutable lists prevent accidental modification of predictor and result collections after construction.

This reduces unintended changes during report generation.

### 12.2 Diagnostic interfaces

`DiagnosticRule` defines a common evaluation contract.

Four rule implementations cover:

- Multicollinearity.
- Heteroscedasticity.
- Residual normality.
- Influence.

`DiagnosticService` executes the registered rules and collects their findings.

This architecture permits diagnostic rules to be tested and maintained independently.

### 12.3 Model state management

The model uses explicit lifecycle states:

| State | Permitted meaning |
|---|---|
| CREATED | Dataset accepted |
| FITTED | OLS estimation completed |
| DIAGNOSTICS_COMPLETED | Diagnostic rules evaluated |

Invalid state transitions are rejected.

For example, diagnostic evaluation cannot occur before fitting.

### 12.4 Enterprise implications

The design separates:

- Domain validation.
- Numerical estimation.
- Diagnostic policy.
- Statistical findings.
- Reporting.

This makes it easier to introduce role-based authorization, audit records, model versioning, and approval workflows in a larger enterprise system.

The current program is a single-process implementation. It does not itself provide distributed execution, database persistence, or user authentication.

## 13. PostgreSQL Relational Model

The SQL implementation manages the persistence and reporting layer.

The database does not attempt to replace a numerical linear algebra engine. It stores calculated coefficients and diagnostic outputs while enforcing relationships and integrity.

### 13.1 Entity relationships

    Analyst
       |
       v
    Regression Model
       |
       +--------------------+
       |                    |
       v                    v
    Predictors          Observations
       |                    |
       |                    v
       |              Predictor Values
       |                    |
       +--------------------+
       |
       v
    Predictor Diagnostics

    Regression Model
       |
       +--------------------+
       |                    |
       v                    v
    Auxiliary Tests     Diagnostic Results
                            |
                            v
                      Diagnostic Policy

    Observation
       |
       v
    Influence Measures

### 13.2 Main tables

| Table | Purpose |
|---|---|
| `analyst` | Identifies model owners |
| `regression_model` | Stores model metadata and lifecycle |
| `model_predictor` | Stores predictor definitions and coefficients |
| `observation` | Stores actual values, fitted values and residuals |
| `observation_predictor_value` | Stores predictor measurements |
| `diagnostic_policy` | Stores diagnostic thresholds |
| `diagnostic_result` | Stores diagnostic findings |
| `influence_measure` | Stores observation-level influence statistics |
| `auxiliary_test` | Stores statistical test results |
| `predictor_diagnostic` | Stores predictor-specific VIF information |

### 13.3 Database integrity

Primary keys identify individual records.

Foreign keys preserve model, predictor, and observation relationships.

Unique constraints prevent duplicate observation identifiers within the same model.

Check constraints enforce valid statistical ranges and policy thresholds.

Triggers calculate residuals when fitted or observed values change.

Another trigger ensures that predictor measurements belong to the same regression model as their observations.

### 13.4 Model lifecycle

The database uses a controlled state model:

- `CREATED`
- `FITTED`
- `DIAGNOSTICS_COMPLETED`
- `REJECTED`
- `ARCHIVED`

Lifecycle triggers prevent invalid transitions, such as reopening an archived model.

### 13.5 Reporting

The SQL script provides:

- Model-level retrieval.
- Coefficient and HC3 standard-error reporting.
- VIF assessment.
- Residual summaries.
- Auxiliary test retrieval.
- Influence rankings.
- Diagnostic severity aggregation.
- Model eligibility evaluation.
- Missing fitted-value validation.
- Predictor completeness validation.

### 13.6 Transactions

The sample includes a transaction that temporarily moves an influential observation into an investigation state.

The transaction is rolled back to preserve the original demonstration dataset.

This illustrates the distinction between a diagnostic finding and an authorized data-management decision.

### 13.7 Numerical boundary

The database stores supplied VIF, influence, and auxiliary-test results.

These values are illustrative demonstration records.

General multiple-predictor VIF and complete regression influence statistics require numerical calculations using the relevant design matrix and fitted residuals. They should not be inferred from simple SQL aggregates.

A production integration should associate every imported statistic with a model version, calculation method, execution timestamp, and data snapshot.

## 14. Experimental Dataset

All five implementations use a deterministic dataset containing 80 observations and two predictors.

The predictors are constructed as:

\[
X_1=i
\]

\[
X_2=0.92i+0.8(i\bmod 7)
\]

The response is generated as:

\[
Y=12+2.5X_1+1.3X_2+\epsilon_i
\]

The error term is:

\[
\epsilon_i =
((i\bmod 9)-4)(0.4+0.025i)
\]

For observation 72, an additional disturbance of 35 is introduced.

This construction provides several diagnostic characteristics:

| Dataset characteristic | Intended diagnostic purpose |
|---|---|
| Strongly related predictors | Multicollinearity |
| Error magnitude increasing with observation index | Heteroscedasticity investigation |
| Deterministic error variation | Residual distribution assessment |
| Additional disturbance at observation 72 | Outlier and influence investigation |

The dataset is designed for demonstration rather than as a validated representation of a real-world population.

The generating coefficients are known, but estimated coefficients need not exactly equal them because the simulated errors affect the fitted regression.

The database example uses supplied illustrative diagnostic statistics rather than claiming numerical equivalence with the independently executed implementations.

## 15. Thresholds and Statistical Interpretation

Thresholds are screening tools, not universal acceptance rules.

| Measure | Demonstration threshold | Interpretation |
|---|---:|---|
| VIF warning | 5 | Investigate predictor redundancy |
| VIF critical | 10 | Serious inflation |
| Breusch-Pagan | p-value below 0.05 | Evidence against constant variance |
| Jarque-Bera | p-value below 0.05 | Evidence against normality |
| Cook's distance | \(4/n\) | Influence screening |
| Leverage | \(2(k+1)/n\) | High-leverage screening |
| Studentized residual | Absolute value above 3 | Large residual screening |

A threshold exceedance does not automatically invalidate a model.

The interpretation should consider sample size, domain requirements, study design, measurement quality, and the intended use of the regression.

## 16. Edge Cases and Failure Handling

The implementations address several conditions that can prevent meaningful diagnostics.

| Condition | Handling |
|---|---|
| Empty dataset | Reject execution |
| Missing predictors | Reject invalid observation structure |
| Duplicate identifiers | Reject duplicate records |
| Non-finite numeric values | Reject invalid measurements |
| Insufficient observations | Reject model fitting |
| Singular design matrix | Report numerical estimation failure |
| Constant response | Reject R-squared calculation |
| Zero residual variance | Reject undefined studentization |
| Constant auxiliary-regression target | Handle as an undefined or degenerate test case |
| Invalid statistical threshold | Reject policy configuration |
| Missing fitted values | Identify through database validation |
| Invalid model transition | Reject through application and database controls |
| File-write failure | Report the error and remove temporary output |

A singular matrix may arise from perfect multicollinearity or redundant predictors.

A numerically near-singular matrix can also produce unstable estimates even when an exact inverse technically exists.

The tolerance used by the educational solvers is not a complete condition-number assessment.

## 17. Performance and Numerical Considerations

Let:

- \(n\) represent observations.
- \(k\) represent predictors.
- \(p=k+1\) represent regression parameters.

The dominant matrix operations have approximate complexity:

| Operation | Time complexity |
|---|---|
| Construct design matrix | \(O(nk)\) |
| Calculate \(X^TX\) | \(O(nk^2)\) |
| Solve regression system | \(O(k^3)\) |
| Calculate fitted values | \(O(nk)\) |
| Calculate leverage | \(O(nk^2+k^3)\) |
| Calculate one auxiliary VIF regression | \(O(nk^2+k^3)\) |
| Calculate all VIF values | Repeated auxiliary regression cost |
| Calculate HC3 covariance | \(O(nk^2+k^3)\) |

The educational implementations explicitly form and invert matrix products.

For larger datasets or poorly conditioned predictor matrices, QR or SVD-based estimation is preferable.

The implementation also calculates the complete hat matrix in several languages for clarity. Production systems should calculate only the required diagonal leverage values rather than storing an \(n \times n\) matrix.

The SQL indexes prioritize model-specific retrieval, diagnostic filtering, and influence ranking.

## 18. Security and Data Governance

Regression datasets may contain confidential operational, financial, customer, or research information.

A production deployment should enforce:

- Least-privilege database roles.
- Parameterized queries.
- Restricted modification of fitted model results.
- Immutable model version identifiers.
- Audit records for diagnostic execution.
- Controlled observation exclusion.
- Encrypted storage and communication.
- Access restrictions on exported reports.
- Retention policies for original observations.
- Validation of externally calculated statistics.

Diagnostic reports should preserve the distinction between an observation flagged for investigation and an observation authorized for exclusion.

Statistical findings should remain traceable to the original model version and data snapshot.

## 19. Limitations

These implementations are deliberately self-contained numerical learning artifacts.

They do not provide every feature of a comprehensive statistical package.

Specific limitations include:

- No complete QR or SVD regression implementation.
- No automatic nonlinear model selection.
- No comprehensive residual visualization.
- No formal Shapiro-Wilk test.
- No full White test implementation.
- No automatic generalized least squares estimation.
- No bootstrap confidence intervals.
- No automatic deletion or correction of influential observations.
- No complete externally studentized residual refitting procedure.
- No general-purpose production numerical condition-number assessment.
- No database-side OLS coefficient estimation.

The Breusch-Pagan and Jarque-Bera procedures use asymptotic chi-square reference distributions.

The sample is deterministic, and the demonstration thresholds should not be interpreted as mandatory acceptance criteria for all regression applications.

## 20. Integrated Technical Distinctions

The most important distinction is between estimation, diagnostic evidence, statistical inference, and model governance.

| Activity | Meaning |
|---|---|
| Regression estimation | Calculates model coefficients |
| Multicollinearity assessment | Examines relationships among predictors |
| Heteroscedasticity assessment | Examines conditional error variance |
| Residual analysis | Examines unexplained patterns and distributional behavior |
| Influence analysis | Identifies observations that may substantially affect estimation |
| Robust covariance estimation | Adjusts estimated coefficient uncertainty |
| Diagnostic policy evaluation | Classifies results against specified screening rules |
| Database governance | Preserves model, observation, and diagnostic integrity |

These activities should not be treated as interchangeable.

A model can be computationally fitted without being statistically appropriate for its intended purpose.

A model can pass one diagnostic and fail another.

A model can have high predictive performance while exhibiting unreliable coefficient inference.

A diagnostic warning should therefore initiate investigation rather than trigger an automatic model rejection or data deletion.
