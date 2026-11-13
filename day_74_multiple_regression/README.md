# Multiple Regression: Predictors, Categorical Variables, Interactions and Interpretation

## 1. Technical Overview

Multiple regression is a statistical method used to estimate the relationship between one dependent variable and two or more independent variables.

It extends simple linear regression by allowing several predictors to explain variation in the target variable simultaneously.

The implemented scenario examines employee salary using:

- Professional experience.
- Performance rating.
- Educational qualification.
- Department.
- Interaction between experience and performance.

The central objective is to estimate the conditional relationship between these characteristics and employee compensation while controlling for the other included predictors.

The five implementations provide different engineering perspectives:

| Implementation | Main responsibility |
|---|---|
| Python | Statistical modeling, diagnostics and interpretation |
| JavaScript | Event-driven regression analysis and asynchronous processing |
| C++17 | Efficient regression engine using STL and matrix operations |
| Java 17 | Enterprise-oriented model architecture and service management |
| PostgreSQL | Relational data management, model fitting and reporting |

All five implementations use ordinary least squares (OLS) and reference-category encoding for categorical predictors.

---

## 2. Mathematical Foundation

### 2.1 Multiple Linear Regression

The general multiple regression equation is:

\[
Y_i = \beta_0+\beta_1X_{i1}+\cdots+
\beta_pX_{ip}+\epsilon_i
\]

Where:

| Symbol | Meaning |
|---|---|
| \(Y_i\) | Dependent variable for observation \(i\) |
| \(X_{ij}\) | Value of predictor \(j\) |
| \(\beta_0\) | Intercept |
| \(\beta_j\) | Regression coefficient |
| \(\epsilon_i\) | Error term |
| \(p\) | Number of predictor terms |

The model estimates the conditional expected value of the dependent variable.

For the employee compensation example:

\[
Salary=f(Experience,Performance,Education,Department)
\]

The inclusion of several predictors allows the estimated relationship with one predictor to be interpreted while holding the other model terms constant.

### 2.2 Ordinary Least Squares

OLS estimates coefficients by minimizing the sum of squared residuals.

\[
SSE=\sum_{i=1}^{n}(Y_i-\hat Y_i)^2
\]

In matrix notation:

\[
\hat{\beta}=(X^TX)^{-1}X^TY
\]

Where:

- \(X\) is the design matrix.
- \(X^T\) is its transpose.
- \(Y\) is the target vector.
- \(\hat{\beta}\) is the estimated coefficient vector.

The implementation constructs the design matrix and solves the associated linear system using Gaussian elimination with partial pivoting.

This avoids requiring a third-party numerical package.

A singular matrix indicates that the available predictors cannot independently identify all model coefficients.

---

## 3. Multiple Predictors

A predictor is an explanatory variable included in the regression equation.

The employee compensation model contains two continuous predictors.

| Predictor | Data type | Meaning |
|---|---|---|
| Experience | Numerical | Years of professional experience |
| Performance | Numerical | Employee performance rating |
| Education | Categorical | Qualification level |
| Department | Categorical | Organizational department |

### 3.1 Numerical Predictors

Numerical predictors have measurable values.

Examples include:

- Age.
- Experience.
- Revenue.
- Expenditure.
- Performance scores.
- Production volume.

For a model without interactions, a numerical coefficient represents the expected change in the dependent variable associated with a one-unit increase in that predictor, holding the remaining model terms constant.

For example, an experience coefficient describes the conditional salary difference associated with one additional year of experience.

This interpretation depends on the model specification and does not establish causation.

### 3.2 Controlling for Other Predictors

A major advantage of multiple regression is its ability to account for several variables simultaneously.

Consider two employees with different experience levels but identical values for performance, education and department.

The experience coefficient estimates the model-implied salary difference between their experience values.

This is a conditional comparison, not necessarily a causal effect.

---

## 4. Categorical Variables

Categorical variables represent groups rather than numerical measurements.

Examples include:

- Education: Bachelor, Master, PhD.
- Department: Operations, Sales, Technology.
- Employment type: Permanent, Contract.
- Region: North, South, East, West.

A categorical variable cannot be interpreted as an ordinary continuous numerical predictor.

Assigning arbitrary numbers to categories can introduce an artificial ordering and distance.

### 4.1 Dummy Variable Encoding

The implementations use reference-category encoding.

Suppose education has three categories:

| Education | Bachelor | Master | PhD |
|---|---:|---:|---:|
| Bachelor | 0 | 0 | 0 |
| Master | 1 | 0 | 0 |
| PhD | 0 | 1 | 1 |

The actual model uses two dummy variables:

| Education | Master dummy | PhD dummy |
|---|---:|---:|
| Bachelor | 0 | 0 |
| Master | 1 | 0 |
| PhD | 0 | 1 |

Bachelor becomes the reference category.

For \(k\) categories, the standard reference-category approach introduces \(k-1\) dummy variables.

This avoids perfect multicollinearity between the intercept and a complete set of category indicators.

### 4.2 Reference-Category Interpretation

The coefficient of `education[Master]` represents the estimated difference between Master and Bachelor employees, holding other included terms constant.

The coefficient of `education[PhD]` represents the estimated difference between PhD and Bachelor employees.

The reference category has no separate dummy coefficient.

Its effect is incorporated into the intercept and the other relevant model terms.

### 4.3 Why Reference Categories Matter

Changing the reference category changes the individual dummy-variable coefficients and intercept.

It does not necessarily change fitted values or the model's explanatory power when the underlying categorical specification remains equivalent.

The reference category must therefore be reported when communicating regression results.

The implementations select category levels deterministically through alphabetical ordering.

---

## 5. Interaction Effects

An interaction occurs when the relationship between one predictor and the dependent variable depends on the value of another predictor.

A model containing only additive effects assumes that each predictor's coefficient remains constant across the values of the other predictors.

Interaction terms relax this assumption.

### 5.1 Mathematical Representation

The implemented numerical interaction is:

\[
Salary=\beta_0+
\beta_1Experience+
\beta_2Performance+
\beta_3(Experience\times Performance)
+\epsilon
\]

The interaction coefficient is:

\[
\beta_3
\]

The marginal effect of experience becomes:

\[
\frac{\partial Salary}{\partial Experience}
=
\beta_1+\beta_3Performance
\]

The marginal effect of performance becomes:

\[
\frac{\partial Salary}{\partial Performance}
=
\beta_2+\beta_3Experience
\]

Consequently, the experience coefficient alone is not the complete effect of experience when the interaction is included.

### 5.2 Interpretation

A positive interaction coefficient indicates that the estimated marginal effect of one predictor increases as the other predictor increases.

A negative interaction coefficient indicates that the estimated marginal effect decreases as the other predictor increases.

The interpretation depends on the scales and units of the interacting predictors.

### 5.3 Numerical Interaction Example

Suppose an organization investigates whether professional experience has a different salary relationship for employees with different performance ratings.

The interaction:

`experience:performance`

allows the experience relationship to vary with performance.

A model without this interaction imposes a constant experience coefficient across all performance levels.

A model with this interaction estimates a performance-dependent experience relationship.

### 5.4 Categorical Interactions

Interactions can also involve categorical variables.

For example:

`experience × department`

would allow the experience relationship to differ across departments.

A model containing this interaction requires additional terms for the appropriate department dummy variables multiplied by experience.

The supplied implementations deliberately restrict interactions to numerical predictors to keep the model specification consistent across all five languages.

The mathematical framework supports categorical interactions through expanded design matrices.

---

## 6. Coefficient Interpretation

A coefficient measures a conditional relationship within the specified regression model.

Its interpretation depends on:

- Predictor measurement units.
- Reference categories.
- Other included predictors.
- Interaction terms.
- Model assumptions.

### 6.1 Intercept

The intercept represents the expected target value when numerical predictors equal zero and categorical variables are at their reference levels.

An intercept may have limited practical meaning when zero is outside the observed predictor range.

### 6.2 Numerical Coefficients

A numerical coefficient estimates the expected target change associated with a one-unit predictor increase, conditional on the other model terms.

When interactions exist, the corresponding marginal effect must include the interaction contribution.

### 6.3 Categorical Coefficients

Categorical coefficients compare a particular category against the reference category.

They are not ordinary numerical slopes.

### 6.4 Interaction Coefficients

Interaction coefficients describe how the conditional relationship between one predictor and the target changes with another predictor.

They should be interpreted together with their corresponding main effects.

### 6.5 Statistical Uncertainty

The Python, JavaScript, C++17 and Java implementations calculate coefficient standard errors from the estimated residual variance and the inverse design cross-product matrix.

\[
SE(\hat{\beta}_j)
=
\sqrt{
\widehat{\sigma}^2
[(X^TX)^{-1}]_{jj}
}
\]

The standard error measures estimation uncertainty under the conventional OLS assumptions.

A coefficient estimate alone does not establish statistical significance.

The supplied implementations do not calculate exact coefficient p-values or account for heteroskedasticity-robust standard errors.

---

## 7. Model Evaluation

A regression model should be assessed through multiple measures rather than a single statistic.

### 7.1 R-Squared

R-squared measures the proportion of observed target variation explained by the fitted model.

\[
R^2=1-\frac{SSE}{SST}
\]

Where:

- SSE is the residual sum of squares.
- SST is the total sum of squares.

A larger value indicates a better in-sample fit under the usual intercept-containing OLS formulation.

It does not establish causation or guarantee good predictions on new observations.

### 7.2 Adjusted R-Squared

Adjusted R-squared accounts for the number of estimated parameters.

\[
R^2_{adj}
=
1-(1-R^2)\frac{n-1}{n-p}
\]

Where:

- \(n\) represents observations.
- \(p\) represents estimated model parameters, including the intercept.

This measure is useful when comparing models with different numbers of predictors, provided they use the same target and observations.

### 7.3 Root Mean Squared Error

\[
RMSE=\sqrt{\frac{SSE}{n}}
\]

RMSE expresses prediction error in the same units as the target variable.

Larger residuals have a stronger effect because the errors are squared.

### 7.4 Mean Absolute Error

\[
MAE=\frac{1}{n}\sum_{i=1}^{n}|Y_i-\hat Y_i|
\]

MAE provides an average absolute prediction error.

It is generally less sensitive to extreme residuals than RMSE.

### 7.5 Residual Analysis

A residual is the difference between an observed and predicted target value.

\[
e_i=Y_i-\hat Y_i
\]

Residual examination helps identify:

- Nonlinearity.
- Unequal error variance.
- Outliers.
- Potential influential observations.
- Model misspecification.

The implementations retain residuals for further examination.

---

## 8. Assumptions and Statistical Diagnostics

OLS estimation is not sufficient by itself to establish that a model is appropriate.

The following assumptions and diagnostics require attention.

| Assumption or issue | Meaning | Diagnostic approach |
|---|---|---|
| Linearity | Conditional mean is correctly represented by included terms | Residual plots |
| Independence | Errors are independent across observations | Study design and residual analysis |
| Homoscedasticity | Error variance is approximately constant | Residual-versus-fitted plot |
| Multicollinearity | Predictors are not perfectly or excessively correlated | VIF and correlation analysis |
| Normality | Error distribution is approximately normal for conventional small-sample inference | Q-Q plot |
| Influential observations | Individual observations do not dominate estimates | Leverage and Cook's distance |
| Specification | Relevant nonlinearities and interactions are considered | Model comparison |

### 8.1 Multicollinearity

Multicollinearity occurs when predictors are strongly related.

Perfect multicollinearity makes the design matrix singular and prevents unique coefficient estimation.

Variance Inflation Factor is:

\[
VIF_j=\frac{1}{1-R_j^2}
\]

Where \(R_j^2\) is obtained by regressing predictor \(j\) on the remaining predictors.

The Python implementation includes numerical-predictor VIF calculation.

High VIF values indicate increased coefficient uncertainty, although they do not automatically invalidate the model.

### 8.2 Model Specification

An omitted important variable can distort estimated coefficients when it is associated with included predictors.

A model can also be misspecified when a nonlinear relationship is represented using an inadequate linear structure.

Interaction terms and polynomial terms can improve specification when supported by the research question and data.

### 8.3 Limitations of the Implemented Diagnostics

The implementations provide core OLS estimation and selected diagnostics.

They do not provide a complete statistical inference package.

Production-grade research may also require:

- Robust standard errors.
- Confidence intervals based on an appropriate distribution.
- Exact or approximate coefficient significance tests.
- Residual distribution tests.
- Cook's distance.
- Leverage statistics.
- Cross-validation.
- Train-test evaluation.
- Regularization for unstable high-dimensional models.

---

## 9. Python Implementation

### 9.1 Architecture

The Python implementation separates statistical responsibilities into reusable components.

| Component | Responsibility |
|---|---|
| `Interaction` | Represents a two-variable interaction |
| `RegressionResult` | Stores estimated coefficients and diagnostics |
| `MultipleRegression` | Handles model specification, encoding and estimation |
| `solve_linear_system()` | Estimates OLS coefficients |
| `invert_matrix()` | Supports standard-error calculations |
| `calculate_vif()` | Calculates numerical-predictor VIF |
| `main()` | Runs the employee compensation example |

### 9.2 Design Decisions

The implementation uses:

- Dataclasses for structured statistical results.
- Lists and dictionaries for observations.
- Sets for identifying categorical levels.
- Gaussian elimination with partial pivoting.
- Explicit validation for missing and invalid values.
- Reference-category encoding.
- Separate prediction and interpretation methods.

The design does not depend on external numerical packages.

### 9.3 Prediction Workflow

The prediction process follows:

`Raw Input → Validation → Category Encoding → Interaction Calculation → Linear Prediction`

Prediction requires the same categorical levels used during model fitting.

An unknown category is rejected rather than silently encoded as a reference category.

### 9.4 Computational Complexity

For \(n\) observations and \(p\) model parameters:

| Operation | Approximate complexity |
|---|---|
| Design matrix construction | \(O(np)\) |
| Cross-product calculation | \(O(np^2)\) |
| Gaussian elimination | \(O(p^3)\) |
| Matrix inversion | \(O(p^3)\) |
| Prediction per observation | \(O(p)\) |

The normal-equation approach is suitable for educational and moderate-sized examples.

It can become numerically unstable when predictors are poorly scaled or strongly collinear.

QR decomposition or singular value decomposition is preferable for demanding numerical applications.

---

## 10. JavaScript Implementation

### 10.1 Engineering Perspective

The JavaScript implementation emphasizes asynchronous execution and event-driven model management.

It uses Node.js standard-library functionality rather than requiring an external statistics package.

### 10.2 Main Components

| Component | Responsibility |
|---|---|
| `Dataset` | Validates dataset structure |
| `RegressionEngine` | Encodes predictors and fits OLS |
| `RegressionWorkflow` | Coordinates analysis execution |
| `EventEmitter` | Communicates model lifecycle events |
| `saveReport()` | Persists model results as JSON |

### 10.3 Event-Driven Workflow

The model lifecycle uses events:

`analysis:started`

`model:fitted`

`analysis:completed`

`analysis:ready`

`analysis:failed`

These events separate computation from application-level reporting.

For example, an application can subscribe to `analysis:completed` to update an operational dashboard without embedding dashboard logic inside the regression engine.

### 10.4 Asynchronous Processing

The fitting operation is asynchronous.

This permits the workflow to integrate with other asynchronous Node.js services.

The mathematical calculations remain CPU-bound and synchronous after the initial event-loop yield.

For large datasets, actual parallel computation requires worker threads or an appropriate external numerical service.

### 10.5 Model Versioning

Each successful fit increments the model version.

This provides a simple mechanism for identifying successive model estimates and associating reports with a particular fitted model.

The workflow retains the resulting model history in memory.

---

## 11. C++17 Implementation

### 11.1 Engineering Perspective

The C++ implementation focuses on explicit data structures, controlled memory usage and matrix computation.

It uses the Standard Template Library without third-party dependencies.

### 11.2 Main Components

| Component | Responsibility |
|---|---|
| `Observation` | Represents an employee record |
| `Interaction` | Describes an interaction term |
| `ModelMetrics` | Stores evaluation metrics |
| `RegressionTerm` | Stores coefficient information |
| `MatrixSolver` | Solves and inverts matrices |
| `MultipleRegressionEngine` | Controls the complete fitting workflow |

### 11.3 Matrix Processing

The engine creates a dense design matrix.

It then constructs:

- \(X^TX\)
- \(X^TY\)
- Estimated coefficient vector.
- Prediction vector.
- Residual vector.

The matrix solver uses partial pivoting to reduce numerical problems caused by small pivot values.

### 11.4 Tradeoffs

Dense matrix storage is straightforward for a relatively small number of predictors.

It becomes inefficient when categorical variables have thousands of levels or when the model has many sparse features.

Sparse matrix representations would be more appropriate for high-dimensional categorical datasets.

---

## 12. Java 17 Implementation

### 12.1 Enterprise-Oriented Architecture

The Java implementation uses explicit domain objects and a service-oriented structure.

Its architecture separates:

- Employee records.
- Predictor interactions.
- Regression policies.
- Feature encoding.
- Statistical computation.
- Model results.
- Prediction services.

### 12.2 Java 17 Features

The implementation uses:

| Feature | Application |
|---|---|
| Records | Immutable domain and result objects |
| Enums | Model lifecycle states |
| Interfaces | Regression policy abstraction |
| Generics | Typed collections |
| Streams | Category extraction and reporting |
| Collections | Model configuration and category management |
| Custom exceptions | Statistical and validation failures |
| Switch expressions | Numerical predictor resolution |

### 12.3 Regression Policy

`MinimumSamplePolicy` enforces a minimum observation condition.

The number of observations must exceed the number of estimated parameters.

This is necessary for positive residual degrees of freedom under the implementation's conventional OLS variance calculation.

### 12.4 State Management

The service tracks:

- `CREATED`
- `VALIDATED`
- `FITTED`
- `FAILED`

A model cannot be used for prediction before a successful fit.

The result object is immutable, reducing accidental modification of previously estimated model information.

### 12.5 Enterprise Implications

The architecture can support additional policies for:

- Dataset approval.
- Predictor restrictions.
- Model version management.
- Access-controlled reporting.
- Model validation.
- Statistical governance.

The current implementation demonstrates the core service and policy structure without implementing an external enterprise authorization system.

---

## 13. PostgreSQL Implementation

### 13.1 Relational Architecture

The SQL implementation represents the regression workflow as a relational data model.

Its main relationships are:

`Datasets → Employees → Regression Models → Model Terms`

`Regression Models → Model Categories`

`Regression Models → Model Predictions`

`Regression Models → Model Interactions`

### 13.2 Database Objects

| Database object | Responsibility |
|---|---|
| `datasets` | Stores dataset metadata |
| `employees` | Stores employee observations |
| `regression_models` | Stores model configurations and evaluation results |
| `model_terms` | Stores estimated coefficients |
| `model_categories` | Stores categorical encoding and reference levels |
| `model_interactions` | Stores interaction specifications |
| `model_predictions` | Stores actual values, predictions and residuals |

### 13.3 Integrity Controls

Primary keys provide record identity.

Foreign keys enforce relationships between datasets, employees and models.

Unique constraints prevent duplicate model names within a dataset and duplicate model terms within a model.

Check constraints restrict invalid salary, experience and performance values.

### 13.4 SQL-Based OLS Estimation

The `fit_employee_regression()` function constructs a numerical design matrix from relational observations.

The function:

1. Identifies categorical levels.
2. Selects reference categories.
3. Generates dummy-variable columns.
4. Creates the interaction column.
5. Constructs \(X^TX\) and \(X^TY\).
6. Solves the linear system.
7. Calculates predictions and residuals.
8. Calculates regression metrics.
9. Persists model terms and predictions.
10. Updates the model lifecycle status.

The `solve_ols_system()` function performs Gaussian elimination with partial pivoting.

This allows the regression estimation to run inside PostgreSQL without requiring an additional statistical extension.

### 13.5 Reporting Views

The database provides:

- `v_model_performance`
- `v_model_coefficients`
- `v_prediction_diagnostics`

These views separate statistical reporting from the underlying transactional tables.

### 13.6 Prediction Function

`predict_employee_salary()` accepts:

- Experience.
- Performance.
- Education.
- Department.
- Model identifier.

It validates the input categories against the fitted model's category levels.

It then calculates the prediction from the stored coefficients.

### 13.7 Transaction Management

The script executes schema creation, sample-data insertion, model configuration and model fitting within a transaction.

A failed fitting operation raises an exception.

The surrounding transaction can therefore be rolled back to avoid committing an incomplete database setup.

### 13.8 Database Performance

The implementation creates indexes for:

- Dataset identification.
- Department-based filtering.
- Education-based filtering.

These indexes support common retrieval operations.

For much larger datasets, additional indexes should be selected according to actual query plans rather than created indiscriminately.

---

## 14. Differences Between the Five Implementations

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary focus | Statistical analysis | Event-driven processing | Computational engine | Enterprise architecture | Relational workflow |
| Data representation | Dictionaries and lists | Objects and arrays | Structs and vectors | Records and collections | Relational tables |
| Categorical encoding | Dynamic | Dynamic | Dynamic | Dynamic | SQL-generated |
| Interactions | Configurable numerical terms | Configurable numerical terms | Explicit numerical terms | Explicit numerical terms | Stored interaction specification |
| Model lifecycle | Fit and predict | Event-driven | Fitted state | Explicit status | Database status |
| Diagnostics | R², adjusted R², RMSE, MAE, VIF | R², adjusted R², RMSE, MAE | R², adjusted R², RMSE, MAE | R², adjusted R², RMSE, MAE | R², adjusted R², RMSE, MAE |
| Persistence | Optional JSON/reporting | JSON report | In-memory | In-memory | Relational tables |

The implementations share the same statistical objective but organize computation and state management differently.

The JavaScript workflow emphasizes asynchronous integration.

The Java implementation emphasizes policy-based service design.

The C++ implementation emphasizes explicit numerical processing.

The PostgreSQL implementation emphasizes durable relational storage and transactional execution.

---

## 15. Practical Application Scenarios

Multiple regression is applicable to several analytical problems.

| Application | Dependent variable | Potential predictors |
|---|---|---|
| Employee compensation | Salary | Experience, education, performance, department |
| Business forecasting | Revenue | Advertising, pricing, seasonality, region |
| Healthcare analytics | Length of stay | Age, clinical indicators, treatment category |
| Operations management | Production output | Machine hours, labor hours, equipment category |
| Financial analysis | Investment return | Market indicators, interest rates, sector |
| Education research | Examination score | Study time, attendance, educational background |

Categorical predictors allow the analysis of differences between groups.

Interaction terms allow relationships to vary across relevant conditions.

The choice of predictors should be justified by the research question and the data-generating process.

---

## 16. Edge Cases and Failure Handling

The implementations explicitly address several important failure conditions.

| Condition | Expected handling |
|---|---|
| Empty dataset | Reject model fitting |
| Missing predictor | Reject incomplete input |
| Non-finite numerical value | Reject invalid observation |
| Only one category level | Reject categorical encoding |
| Unknown prediction category | Reject prediction |
| Insufficient observations | Reject estimation |
| Perfect multicollinearity | Raise singular-matrix error |
| Zero target variance | Reject R-squared calculation |
| Prediction before fitting | Reject prediction |
| Invalid interaction specification | Reject model configuration |

### Numerical Stability

The normal-equation approach can be sensitive to numerical precision.

Partial pivoting improves the Gaussian elimination process but does not eliminate the conditioning problems of \(X^TX\).

For large or ill-conditioned regression problems, QR decomposition or singular value decomposition is preferable.

### Missing Data

The supplied implementations reject missing or invalid predictor values.

They do not automatically perform:

- Mean imputation.
- Median imputation.
- Category imputation.
- Complete-case deletion.
- Multiple imputation.

Missing-data treatment should be selected according to the research design rather than applied automatically.

### Outliers

The implementations calculate residuals but do not automatically remove outliers.

An unusual observation may represent a data error, a genuine exceptional case or an important population characteristic.

Removal requires a documented analytical justification.

---

## 17. Security and Production Considerations

Regression systems may process confidential employee, customer, healthcare or financial information.

Appropriate controls include:

- Restricting access to source datasets.
- Enforcing role-based database permissions.
- Protecting stored model outputs.
- Avoiding sensitive information in application logs.
- Validating imported datasets.
- Separating development and production data.
- Recording model versions and fitting timestamps.
- Maintaining audit records for analytical changes.
- Protecting exported reports.
- Using parameterized SQL for application-supplied values.

The PostgreSQL schema uses relational constraints and controlled function inputs.

In a production deployment, database roles and privileges should be configured separately for dataset ingestion, model execution and report access.

The JSON reporting workflow in JavaScript uses restrictive file permissions where supported by the operating system.

Application-level access control remains necessary.

---

## 18. Technical Limitations

The implementations are deliberately self-contained and demonstrate foundational OLS mechanisms.

Their limitations include:

1. Dense normal-equation calculations.
2. No robust heteroskedasticity-consistent standard errors.
3. No exact coefficient significance tests.
4. No automated confidence intervals.
5. No automatic nonlinear-term discovery.
6. No cross-validation.
7. No regularized regression.
8. No automatic missing-data treatment.
9. Limited interaction-term configuration in the C++, Java and SQL examples.
10. No large-scale distributed model fitting.

The SQL implementation stores coefficient estimates and conventional model metrics. Its standard-error fields are not populated by the fitting function.

The Python VIF implementation considers numerical predictors separately and should not be interpreted as a complete multicollinearity diagnostic for the entire expanded design matrix.

These limitations should be considered before using the examples for formal statistical inference or operational decisions.

---

## 19. Execution and File Organization

Use the following filenames:

| File | Filename |
|---|---|
| Python | `multiple_regression.py` |
| JavaScript | `multiple_regression.js` |
| C++17 | `multiple_regression.cpp` |
| Java 17 | `MultipleRegression.java` |
| PostgreSQL | `multiple_regression.sql` |
| Documentation | `README.md` |

### Python

Requires Python 3.10 or later.

Execution:

`python multiple_regression.py`

### JavaScript

Requires Node.js 18 or later.

Execution:

`node multiple_regression.js`

The execution produces a JSON model report in the working directory.

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic multiple_regression.cpp -o multiple_regression`

Execute:

`./multiple_regression`

On Windows:

`.\multiple_regression.exe`

### Java 17

Compile:

`javac MultipleRegression.java`

Execute:

`java MultipleRegression`

### PostgreSQL

Execute the complete SQL script using a PostgreSQL 14 or later database.

The script creates the `regression_lab` schema, inserts the sample dataset, estimates the model and executes reporting queries.

The script should be executed using a database role authorized to create schemas, tables, functions, views and indexes.

---

## 20. Educational Concepts Demonstrated

| Concept | Practical implementation |
|---|---|
| Multiple regression | Several explanatory variables |
| Conditional coefficient | Effect holding other model terms constant |
| Categorical encoding | Reference-category dummy variables |
| Interaction | Product of experience and performance |
| Design matrix | Numerical representation of regression terms |
| OLS | Minimization of squared residuals |
| Matrix inversion | Standard-error estimation |
| Gaussian elimination | Linear-system solution |
| Multicollinearity | Singular-matrix handling and VIF |
| Model fit | R-squared and adjusted R-squared |
| Prediction error | RMSE and MAE |
| Residual analysis | Actual minus predicted values |
| Data validation | Rejection of invalid observations |
| Model lifecycle | Fitting and prediction states |
| Persistence | Stored model terms and predictions |

The central distinction is that multiple regression does not merely combine several independent variables into one equation. It estimates their conditional relationships, accounts for categorical group membership through an appropriate encoding scheme, and permits the relationship between predictors and the target to vary through interaction terms.

A sound interpretation therefore requires examining the complete model specification rather than interpreting individual coefficients in isolation.
