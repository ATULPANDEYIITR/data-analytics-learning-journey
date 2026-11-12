# Regression Fundamentals

## 1. Introduction

Simple Linear Regression is a statistical method used to describe and estimate the relationship between one numerical independent variable and one numerical dependent variable.

It models the expected linear relationship between a predictor and a response.

The central mathematical equation is:

\[
\hat{Y} = \beta_0 + \beta_1 X
\]

Where:

| Symbol | Meaning |
|---|---|
| \(X\) | Independent variable or predictor |
| \(Y\) | Observed dependent variable |
| \(\hat{Y}\) | Predicted dependent variable |
| \(\beta_0\) | Intercept |
| \(\beta_1\) | Regression slope |
| \(Y-\hat{Y}\) | Residual |

The implementations use Ordinary Least Squares (OLS), which estimates the coefficients by minimizing the sum of squared residuals.

The practical example examines the relationship between student study hours and examination scores.

## 2. Simple Linear Regression

Simple Linear Regression uses one predictor to estimate one response variable.

For example:

- Independent variable: study hours.
- Dependent variable: examination marks.
- Objective: estimate the expected examination score for a given number of study hours.

The relationship is represented by:

\[
\hat{Y} = \beta_0 + \beta_1X
\]

A linear model represents a straight-line relationship between the predictor and the expected response.

It does not establish that changing the predictor causes a change in the response.

### Ordinary Least Squares

OLS determines the coefficients by minimizing:

\[
SSE = \sum_{i=1}^{n}(Y_i-\hat{Y}_i)^2
\]

Substituting the regression equation:

\[
SSE =
\sum_{i=1}^{n}
(Y_i-\beta_0-\beta_1X_i)^2
\]

The method selects the intercept and slope that produce the smallest possible SSE.

For a simple linear regression model containing an intercept:

\[
\beta_1 =
\frac{
\sum_{i=1}^{n}(X_i-\bar X)(Y_i-\bar Y)
}{
\sum_{i=1}^{n}(X_i-\bar X)^2
}
\]

The intercept is:

\[
\beta_0 = \bar Y-\beta_1\bar X
\]

These formulas are implemented directly in all four programming-language implementations and the PostgreSQL procedure.

### Centered calculations

The implementations calculate the slope using deviations from the means.

This approach avoids some numerical cancellation that can occur when working with large absolute values.

The predictor must have sufficient variation. If every predictor observation is identical, the denominator of the slope equation is zero and the regression coefficient cannot be estimated.

## 3. Regression Coefficients

Regression coefficients describe the estimated relationship between the predictor and response.

### Intercept

The intercept represents the predicted response when the predictor equals zero.

\[
\beta_0 = \hat Y \text{ when } X=0
\]

In the examination example, the intercept represents the predicted examination score for a student with zero study hours.

Its practical interpretation depends on whether zero is meaningful and whether it falls within the relevant data range.

An intercept should not automatically be interpreted as a realistic outcome.

### Slope

The slope represents the estimated change in the response associated with a one-unit increase in the predictor.

\[
\beta_1 =
\frac{\Delta \hat Y}{\Delta X}
\]

For example, a slope of 4 means that the predicted examination score increases by four marks for each additional study hour.

This interpretation describes an estimated association, not necessarily a causal effect.

### Coefficient uncertainty

An estimated coefficient is subject to sampling uncertainty.

The implementations calculate the standard error of the slope:

\[
SE(\beta_1) =
\sqrt{\frac{\hat{\sigma}^2}{S_{xx}}}
\]

Where:

\[
\hat{\sigma}^2 = \frac{SSE}{n-2}
\]

And:

\[
S_{xx} = \sum(X_i-\bar X)^2
\]

The approximate confidence interval is:

\[
\beta_1 \pm 1.96SE(\beta_1)
\]

The value 1.96 corresponds approximately to a 95% normal-based confidence interval for sufficiently large samples.

For small samples, the appropriate Student's t critical value should be used instead.

## 4. Residuals

A residual measures the difference between an observed response and its corresponding predicted response.

\[
e_i = Y_i-\hat Y_i
\]

Residuals provide information about the prediction errors made on the observations used to fit the model.

| Residual | Interpretation |
|---|---|
| Positive | Actual value exceeds predicted value |
| Negative | Actual value is below predicted value |
| Zero | Actual and predicted values are equal |
| Large absolute value | Substantial prediction error |

### Residual calculations

For every observation, the implementations calculate:

1. The actual response.
2. The predicted response.
3. The residual.
4. The absolute residual.
5. The squared residual.

The Python and JavaScript implementations expose residual records through their model interfaces.

The C++ and Java implementations return structured residual reports.

PostgreSQL stores individual predictions and residuals in the `model_predictions` table.

### Sum of Squared Errors

\[
SSE = \sum_{i=1}^{n}e_i^2
\]

SSE measures the total squared prediction error.

OLS chooses coefficients that minimize this quantity.

Squaring makes larger errors contribute disproportionately to the total.

### Residual Standard Error

\[
RSE = \sqrt{\frac{SSE}{n-2}}
\]

The denominator is \(n-2\) because simple linear regression estimates two parameters: the intercept and slope.

RSE estimates the standard deviation of the regression errors under the classical model assumptions.

It is expressed in the same units as the response variable.

## 5. Regression Evaluation Metrics

The implementations calculate several complementary evaluation measures.

### Mean Absolute Error

\[
MAE =
\frac{1}{n}\sum_{i=1}^{n}|Y_i-\hat Y_i|
\]

MAE measures average absolute prediction error.

It is relatively easy to interpret because it uses the original response units.

### Mean Squared Error

\[
MSE =
\frac{1}{n}\sum_{i=1}^{n}(Y_i-\hat Y_i)^2
\]

MSE penalizes large prediction errors more heavily than MAE.

Its units are the squared units of the response variable.

### Root Mean Squared Error

\[
RMSE = \sqrt{MSE}
\]

RMSE returns the error measure to the original response units.

### Coefficient of Determination

R-squared measures the proportion of variation in the observed response explained by the fitted regression model, relative to the mean-only baseline.

\[
R^2 = 1-\frac{SSE}{SST}
\]

Where:

\[
SST = \sum_{i=1}^{n}(Y_i-\bar Y)^2
\]

For a fitted OLS model with an intercept and a nonconstant response, R-squared is between zero and one.

An R-squared of 0.85 indicates that 85% of the observed sample variation in the response is accounted for by the fitted model.

It does not establish:

- Causality.
- Correct model assumptions.
- Reliable predictions on unseen observations.
- Absence of omitted variables.
- Correct functional form.

A high R-squared does not necessarily imply that a model is appropriate.

### Adjusted R-squared

Adjusted R-squared accounts for the number of estimated predictors.

For simple linear regression:

\[
R^2_{adj} =
1-(1-R^2)\frac{n-1}{n-2}
\]

It is useful when comparing models with different numbers of predictors, provided the models are evaluated on comparable observations and response variables.

For a single-predictor model, it can be lower than ordinary R-squared.

## 6. Classical Regression Assumptions

OLS coefficient calculations do not automatically establish that the statistical assumptions are satisfied.

The assumptions concern the relationship between the predictors, the response, and the model errors.

### Linearity

The conditional mean of the response should be adequately represented by a linear function of the predictor.

\[
E(Y|X)=\beta_0+\beta_1X
\]

A nonlinear relationship can produce systematic residual patterns.

A residual-versus-fitted plot is useful for identifying curvature and other systematic structures.

A near-zero average residual is not sufficient evidence of linearity. With an intercept, OLS already produces approximately zero mean residuals.

### Independence

Observations or model errors should be independent under the relevant sampling or data-generation process.

Dependence can occur in:

- Time-series observations.
- Repeated measurements.
- Clustered observations.
- Multiple records from the same individual.
- Spatially related observations.

The implementations calculate a descriptive lag-one residual correlation.

This is not a formal independence test. The ordering of observations must also be meaningful before interpreting lag-based diagnostics.

### Homoscedasticity

Homoscedasticity means that the conditional error variance remains constant across predictor values.

\[
Var(\epsilon|X)=\sigma^2
\]

Heteroscedasticity occurs when error variance changes with the predictor.

It can affect the validity of conventional standard errors and confidence intervals.

The implementations compare residual variance between lower and upper fitted-value groups.

This is a preliminary descriptive indicator, not a formal statistical test.

### Normality of errors

For conventional small-sample inference, the classical linear regression model assumes normally distributed errors conditional on the predictor.

\[
\epsilon|X \sim N(0,\sigma^2)
\]

Normality supports exact small-sample t-based inference under the classical assumptions.

It is not required to calculate OLS coefficients.

The implementations calculate residual skewness as a descriptive indicator.

A skewness value alone cannot establish normality. A Q-Q plot, histogram, and appropriate formal assessment provide additional evidence.

### Assumption assessment

| Assumption | Potential issue | Useful diagnostic |
|---|---|---|
| Linearity | Curved relationship | Residual-versus-fitted plot |
| Independence | Correlated errors | Study design and autocorrelation analysis |
| Homoscedasticity | Changing error variance | Residual-versus-fitted plot and variance tests |
| Normality | Non-normal errors | Q-Q plot and distribution analysis |

## 7. Python Implementation

File: `regression_fundamentals.py`

The Python implementation provides a reusable statistical model using standard-library features.

### Main components

| Component | Responsibility |
|---|---|
| `SimpleLinearRegression` | Fits and evaluates the OLS model |
| `RegressionMetrics` | Stores evaluation measures |
| `AssumptionResult` | Stores diagnostic indicators |
| `ModelState` | Represents model lifecycle |
| `ValidationError` | Reports invalid observations |
| `load_csv()` | Loads numerical observations |
| `run_tests()` | Checks mathematical behavior |
| `print_report()` | Produces a regression report |

### Implementation decisions

- Uses lists for numerical observations and residuals.
- Uses dataclasses for structured statistical results.
- Uses an enum to distinguish fitted and unfitted models.
- Uses centered sums for coefficient estimation.
- Uses exceptions for invalid data and unavailable model operations.
- Provides coefficient standard errors.
- Calculates an approximate slope confidence interval.
- Includes CSV ingestion using the standard library.

### Validation

The model rejects:

- Unequal predictor and response lengths.
- Insufficient observations.
- Non-numeric values.
- NaN and infinite observations.
- Constant or near-constant predictors.
- Invalid prediction inputs.

The implementation does not require NumPy, pandas, SciPy, or scikit-learn.

## 8. JavaScript Implementation

File: `regression_fundamentals.js`

The JavaScript implementation uses Node.js capabilities to provide an event-driven model service.

### Main components

| Component | Responsibility |
|---|---|
| `RegressionDataset` | Validates and stores immutable observations |
| `RegressionModel` | Performs regression and diagnostics |
| `RegressionService` | Registers and retrieves models |
| `RegressionError` | Represents regression failures |
| `ValidationError` | Represents invalid inputs |
| `loadCSV()` | Performs asynchronous file ingestion |
| `parseCSVLine()` | Handles quoted CSV fields |

### Event-driven behavior

The model extends Node.js `EventEmitter`.

After a successful fitting operation, it emits:

- `model:fitted`

The event includes the model version, observation count, slope, and intercept.

This allows other application components to respond to model lifecycle changes without coupling themselves to the numerical calculation.

### State management

The implementation distinguishes:

- `UNFITTED`
- `FITTED`
- `INVALIDATED`

Model parameters are published only after the complete fitting calculation succeeds.

The dataset and parameter objects use immutable structures where practical.

### Asynchronous ingestion

CSV files are loaded using Node.js file-system promises.

The implementation validates:

- Required column names.
- Numeric fields.
- Record counts.
- Quoted CSV values.
- Invalid numeric observations.

The model-fitting operation itself is synchronous because the OLS calculations are computationally straightforward for the demonstration dataset.

## 9. C++17 Implementation

File: `regression_fundamentals.cpp`

The C++ implementation provides a strongly typed numerical model using the Standard Template Library.

### Main components

| Component | Responsibility |
|---|---|
| `Observation` | Stores predictor and response |
| `RegressionMetrics` | Stores model evaluation values |
| `PredictionResult` | Stores actual, predicted, and residual values |
| `AssumptionDiagnostic` | Stores diagnostic results |
| `SimpleLinearRegression` | Implements OLS and model evaluation |
| `RegressionException` | Handles domain errors |
| `ModelState` | Tracks fitting state |

### Implementation decisions

- Uses `std::vector` for observations and residuals.
- Uses `std::accumulate` for numerical aggregation.
- Uses `std::sort` to order predictions for variance diagnostics.
- Uses `std::pair` for coefficient uncertainty intervals.
- Uses `std::move` when transferring locally constructed numerical results.
- Uses exceptions to report invalid model operations.

The implementation reserves vector capacity when the number of observations is known, reducing unnecessary reallocations.

The model validates the complete dataset before committing fitted parameters.

This avoids exposing partially calculated coefficients if validation or numerical computation fails.

### Compilation

The source is compatible with the C++17 standard.

## 10. Java 17 Implementation

File: `RegressionFundamentals.java`

The Java implementation models regression as an enterprise-oriented statistical service.

### Domain types

Java records provide immutable representations of:

- `Observation`
- `Dataset`
- `RegressionMetrics`
- `CoefficientStatistics`
- `ResidualRecord`
- `Diagnostic`
- `ModelResult`

### Service architecture

The implementation separates numerical estimation from model registration and retrieval.

`OrdinaryLeastSquares` implements the `RegressionModel` interface.

`RegressionService` maintains registered models using a concurrent map.

The model lifecycle distinguishes:

- `CREATED`
- `FITTED`
- `FAILED`

The implementation retains a previously fitted model when a subsequent fitting operation fails.

This is useful when a statistical service must continue serving predictions while a new dataset is being evaluated.

### Enterprise-oriented controls

- Immutable observation collections.
- Validation at object construction.
- Explicit model status.
- Custom exception classes.
- Thread-safe model registration.
- Structured evaluation results.
- Separation of estimation and service responsibilities.

The confidence interval uses an approximate normal critical value. Small-sample inference requires an appropriate Student's t critical value.

## 11. PostgreSQL Implementation

File: `regression_fundamentals.sql`

The SQL implementation models the regression workflow as a relational database process.

### Relational architecture

The main relationships are:

    datasets
       |
       +---- observations
       |
       +---- regression_models
                    |
                    +---- model_coefficients
                    |
                    +---- model_predictions
                    |
                    +---- model_metrics
                    |
                    +---- assumption_diagnostics

### Database objects

| Database object | Purpose |
|---|---|
| `datasets` | Stores dataset definitions |
| `observations` | Stores predictor-response pairs |
| `regression_models` | Registers fitted models |
| `model_coefficients` | Stores OLS parameters |
| `model_predictions` | Stores predictions and residuals |
| `model_metrics` | Stores evaluation measures |
| `assumption_diagnostics` | Stores diagnostic indicators |

### Integrity controls

Primary keys identify individual records.

Foreign keys maintain relationships between datasets, observations, and models.

Unique constraints prevent duplicate observation numbers within a dataset and duplicate predictions for the same model-observation pair.

Check constraints enforce:

- Positive observation numbers.
- Sufficient observation counts.
- Nonnegative error metrics.
- Positive predictor variance.
- Valid model states.
- Finite numerical values.

The observation trigger provides additional numerical validation.

### Regression procedure

`fit_regression()` performs the following operations:

1. Locks the selected model record.
2. Retrieves its associated dataset.
3. Calculates predictor and response means.
4. Calculates centered sums.
5. Estimates the slope.
6. Estimates the intercept.
7. Generates fitted values.
8. Calculates residuals.
9. Calculates evaluation metrics.
10. Stores coefficients and model results.
11. Updates assumption diagnostics.
12. Changes the model status to `fitted`.

The procedure executes within the transaction of its calling SQL statement.

A failed fitting operation does not leave partially committed predictions or coefficients.

### Prediction function

`predict_value()` retrieves the fitted intercept and slope and calculates the expected response for a supplied predictor value.

### Reporting views

`regression_model_report` provides a consolidated model-level report.

`residual_report` provides observation-level prediction and residual information.

### Database performance

Indexes support:

- Dataset observation retrieval.
- Predictor-value retrieval.
- Model-status filtering.
- Model-level prediction retrieval.
- Residual reporting.

The implementation uses indexed relational joins and set-based calculations rather than processing individual observations through repeated application-level queries.

## 12. Integrated Workflow

All five implementations follow the same fundamental statistical process.

    Numerical Dataset
          |
          v
    Input Validation
          |
          v
    Calculate X Mean and Y Mean
          |
          v
    Calculate Sxx and Sxy
          |
          v
    Estimate Slope
          |
          v
    Estimate Intercept
          |
          v
    Generate Predictions
          |
          v
    Calculate Residuals
          |
          v
    Calculate SSE and Evaluation Metrics
          |
          v
    Calculate Coefficient Uncertainty
          |
          v
    Examine Regression Assumptions
          |
          v
    Produce Model Report

### Mathematical consistency

| Operation | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| OLS slope | Yes | Yes | Yes | Yes | Yes |
| Intercept | Yes | Yes | Yes | Yes | Yes |
| Predictions | Yes | Yes | Yes | Yes | Yes |
| Residuals | Yes | Yes | Yes | Yes | Yes |
| MAE | Yes | Yes | Yes | Yes | Yes |
| MSE | Yes | Yes | Yes | Yes | Yes |
| RMSE | Yes | Yes | Yes | Yes | Yes |
| R-squared | Yes | Yes | Yes | Yes | Yes |
| Adjusted R-squared | Yes | Yes | Yes | Yes | Yes |
| Coefficient standard errors | Yes | Yes | Yes | Yes | Stored model statistics not exposed as a separate SQL calculation |
| Slope confidence interval | Yes | Yes | Yes | Yes | Not implemented |
| Residual diagnostics | Yes | Yes | Yes | Yes | Yes |

## 13. Edge Cases and Limitations

### Insufficient observations

Simple linear regression estimates two coefficients.

At least three observations are required in these implementations to calculate residual-based uncertainty measures with positive residual degrees of freedom.

### Constant predictor

If all predictor values are identical, the slope denominator becomes zero.

The model cannot estimate a unique slope and must reject the dataset.

### Constant response

When the response is constant, total sum of squares is zero.

If the fitted predictions are also exact, R-squared is conventionally reported as 1 in these implementations.

This is a special case and should not be confused with meaningful explanatory power.

### Outliers

Extreme observations can substantially influence the estimated slope, intercept, and residual variance.

OLS minimizes squared errors, so large residuals receive disproportionate influence.

### Extrapolation

Predictions outside the observed predictor range are extrapolations.

A mathematically valid prediction may not be scientifically or operationally reliable.

The implementations do not automatically prevent extrapolation.

### Omitted variables

A simple regression model may exclude important variables related to the response.

Consequently, an estimated slope can reflect confounding rather than an isolated relationship.

### Descriptive diagnostics

The diagnostic indicators in the source files are screening mechanisms.

They do not constitute a complete formal statistical assessment.

In particular:

- Residual mean does not establish linearity.
- Lag-one correlation does not establish independence.
- A variance ratio does not establish homoscedasticity.
- Skewness does not establish normality.

A complete statistical investigation should consider study design, residual plots, influential observations, and suitable inferential tests.

### In-sample evaluation

The implemented metrics primarily evaluate observations used to fit the model.

They do not provide an independent estimate of predictive performance.

A production predictive workflow should maintain separate training and evaluation datasets.

## 14. Computational Complexity

Let \(n\) represent the number of observations.

| Operation | Time complexity |
|---|---|
| Input validation | \(O(n)\) |
| Mean calculations | \(O(n)\) |
| OLS coefficient estimation | \(O(n)\) |
| Prediction for one observation | \(O(1)\) |
| Prediction for \(m\) observations | \(O(m)\) |
| Residual generation | \(O(n)\) |
| Standard regression metrics | \(O(n)\) |
| Sorting for grouped diagnostics | \(O(n\log n)\) |
| Model storage | \(O(n)\) |

The coefficient estimation itself is linear in the number of observations.

The grouped variance diagnostics require sorting, which increases their computational cost to \(O(n\log n)\).

For large datasets, numerical calculations should use suitable precision, careful handling of extreme values, and appropriate data-processing strategies.

## 15. Practical Applications

Simple Linear Regression can support exploratory analysis in several domains.

| Domain | Predictor | Response |
|---|---|---|
| Education | Study hours | Examination marks |
| Business | Advertising expenditure | Sales revenue |
| Economics | Income | Consumption expenditure |
| Operations | Production hours | Output quantity |
| Technology | Processing time | Transaction volume |
| Research | Experimental dosage | Measured response |

The suitability of the model depends on the underlying data, the research question, the measurement process, and the regression assumptions.

## 16. Key Statistical Distinctions

| Concept | What it describes |
|---|---|
| Regression equation | Mathematical relationship estimated by the model |
| Intercept | Predicted response at zero predictor value |
| Slope | Estimated response change per predictor unit |
| Residual | Observed minus predicted response |
| SSE | Total squared residual error |
| MSE | Average squared prediction error |
| RMSE | Square root of mean squared error |
| R-squared | Proportion of sample response variation accounted for by the fitted model |
| Adjusted R-squared | R-squared adjusted for model complexity |
| Standard error | Estimated sampling uncertainty of a coefficient |
| Confidence interval | Range of coefficient values compatible with the data under the specified inference procedure |
| Homoscedasticity | Constant conditional error variance |
| Independence | Lack of dependence among model errors |
| Normality | Normal conditional distribution of errors |

The central distinction is that coefficient estimation, prediction accuracy, and statistical assumption assessment answer different questions. A regression model can calculate coefficients successfully while still being unsuitable for statistical inference or reliable prediction.
