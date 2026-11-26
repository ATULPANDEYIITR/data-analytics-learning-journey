# Power BI Advanced Analytics

## Decomposition Trees, Key Influencers, Forecasting and Anomaly Detection

## 1. Analytical Domain

Power BI Advanced Analytics extends conventional business intelligence beyond descriptive reporting. It supports the investigation of business performance, identification of influential factors, estimation of future outcomes and detection of unusual observations.

This implementation uses a retail sales analytics scenario involving:

- Four geographical regions.
- Four products.
- Three customer segments.
- Three sales channels.
- Transaction-level revenue and quantity.
- Marketing expenditure.
- Discount percentages.
- Customer satisfaction measurements.
- Monthly revenue observations.

The analytical architecture separates business data, statistical calculations, analytical results and reporting.

### Analytical architecture

    Transaction Data
          |
          v
    Data Validation
          |
          v
    Business Measures
          |
          +-----------------------+
          |                       |
          v                       v
    Decomposition Tree      Key Influencers
          |                       |
          v                       v
    Contribution Analysis    Factor Comparison
          |                       |
          +-----------+-----------+
                      |
          +-----------+-----------+
          |                       |
          v                       v
      Forecasting           Anomaly Detection
          |                       |
          v                       v
      Future Revenue       Unusual Observations
          |                       |
          +-----------+-----------+
                      |
                      v
               Analytical Reporting

The five source files implement this architecture using different engineering approaches. They share the same business problem but are not intended to produce identical statistical results because their generated datasets, numerical procedures and data representations differ.

---

## 2. Business Data and Analytical Measures

### 2.1 Transaction-level data

The principal analytical entity is a sales transaction.

| Attribute | Description |
|---|---|
| Transaction ID | Unique transaction identifier |
| Transaction date | Date of the transaction |
| Region | Geographical sales region |
| Product | Product purchased |
| Segment | Customer classification |
| Channel | Sales distribution channel |
| Revenue | Financial value of the transaction |
| Units | Quantity sold |
| Marketing spend | Associated marketing expenditure |
| Discount | Applied discount percentage |
| Satisfaction | Customer satisfaction score |

These attributes have different analytical roles.

- Revenue and units are numerical measures.
- Region, product, segment and channel are categorical dimensions.
- Transaction date provides the temporal dimension.
- Marketing expenditure, discounts and satisfaction are additional explanatory variables.

### 2.2 Business measures

The implementations calculate several business measures.

**Total revenue**

\[
Revenue = \sum_{i=1}^{n} Revenue_i
\]

**Average transaction revenue**

\[
AverageRevenue =
\frac{\sum Revenue_i}{n}
\]

**Total quantity**

\[
UnitsSold = \sum_{i=1}^{n} Units_i
\]

**Marketing ROI**

\[
MarketingROI =
\frac{Revenue-MarketingSpend}{MarketingSpend}
\]

Marketing ROI is implemented as a simplified operational measure. It should not automatically be interpreted as incremental marketing return because the calculation does not isolate marketing-attributable revenue or account for all operating costs.

**Average customer satisfaction**

\[
AverageSatisfaction =
\frac{\sum Satisfaction_i}{n}
\]

These measures provide the numerical foundation for subsequent analytical operations.

---

## 3. Decomposition Trees

### 3.1 Concept

A decomposition tree is an interactive analytical visual in Power BI that breaks down a selected numerical measure across multiple dimensions.

It supports hierarchical exploration of a business result.

For example, a sales analyst investigating total revenue can examine:

1. Revenue by region.
2. Revenue by product within a selected region.
3. Revenue by channel within a selected product.
4. Further breakdowns using other available dimensions.

The purpose is to understand how different categories contribute to an aggregate business measure.

### 3.2 Hierarchical decomposition

Consider the following structure:

    Total Revenue
        |
        +-- North
        |     |
        |     +-- Laptop
        |     |      |
        |     |      +-- Online
        |     |      +-- Retail
        |     |      +-- Partner
        |     |
        |     +-- Mobile
        |
        +-- South
        |     |
        |     +-- Laptop
        |     +-- Tablet
        |
        +-- East
        |
        +-- West

Each child node represents a subset of its parent node.

### 3.3 Revenue contribution

The contribution of a category is:

\[
Contribution =
\frac{CategoryRevenue}{ParentRevenue}
\times 100
\]

For example, if North generates revenue of ₹300,000 and total revenue is ₹1,000,000:

\[
Contribution =
\frac{300000}{1000000}\times100
=30\%
\]

The contribution percentage is relative to the parent node. When the parent represents total revenue, it is also the percentage of total revenue.

### 3.4 Implementation

| File | Implementation |
|---|---|
| Python | Recursive `DecompositionNode` construction |
| JavaScript | Recursive tree construction using `Map` |
| C++17 | Recursive grouping with STL containers |
| Java 17 | Immutable decomposition records and service classes |
| PostgreSQL | Dimension joins, aggregation and decomposition function |

The implementations group records by dimension, calculate revenue, calculate contribution and recursively generate child nodes.

### 3.5 Important mechanisms

**Recursive processing**

Each level receives a filtered subset of the preceding level.

**Top-N selection**

The implementations can restrict the number of displayed categories at each level. This reduces visual complexity.

**Parent-relative contribution**

Each child contribution is calculated against its immediate parent rather than automatically against the entire dataset.

**Dimension validation**

Unsupported dimensions and repeated dimensions are rejected.

### 3.6 Decomposition versus simple aggregation

A simple aggregation produces a result such as revenue by region.

A decomposition tree supports progressive investigation:

- Which region contributes the most?
- Which product explains the revenue within that region?
- Which channel contributes most to that product's result?

A decomposition tree therefore provides an interactive analytical path rather than only a static grouped result.

### 3.7 Performance considerations

For a dataset containing \(n\) records and \(d\) decomposition levels, the recursive implementations repeatedly group subsets of records.

The approximate processing cost depends on the distribution of records across branches. In the worst case, repeated processing can approach \(O(nd)\), excluding sorting costs.

Sorting categories at each node introduces additional overhead.

For larger analytical models:

- Pre-aggregate commonly used dimensions.
- Limit unnecessary hierarchy depth.
- Apply filters before aggregation.
- Use appropriate database indexes.
- Avoid unnecessary high-cardinality dimensions.
- Consider Import mode, DirectQuery mode and aggregation tables according to workload requirements.

---

## 4. Key Influencers

### 4.1 Concept

The Key Influencers visual investigates which factors are associated with a selected outcome.

An analyst can investigate questions such as:

- Which region is associated with higher revenue?
- Which product category is associated with higher sales?
- Which customer segment has higher satisfaction?
- Which channel is associated with higher discount levels?

Unlike a decomposition tree, which breaks down a measure across selected dimensions, Key Influencers evaluates relationships between explanatory attributes and a target outcome.

### 4.2 Target definition

The implementations support three analytical targets:

| Target | Definition |
|---|---|
| High revenue | Revenue above the dataset median |
| High satisfaction | Satisfaction above the dataset median |
| High discount | Discount above the dataset median |

The median is used to establish a binary analytical outcome.

For example:

\[
HighRevenue_i =
\begin{cases}
1 & Revenue_i > MedianRevenue\\
0 & Otherwise
\end{cases}
\]

This transforms a continuous numerical variable into a binary classification target for the implemented comparison.

### 4.3 Group comparison

For a categorical value, the target rate is:

\[
TargetRate =
\frac{TargetObservationsInGroup}
{ObservationsInGroup}
\]

The comparison rate is calculated using observations outside that group:

\[
ComparisonRate =
\frac{TargetObservationsOutsideGroup}
{ObservationsOutsideGroup}
\]

The difference is:

\[
Difference =
TargetRate-ComparisonRate
\]

A positive difference indicates that the group has a higher observed target rate than the comparison population.

Relative change is:

\[
RelativeChange =
\frac{TargetRate-ComparisonRate}
{ComparisonRate}
\times100
\]

When the comparison rate is zero, relative change is undefined mathematically. The implementations handle this edge case explicitly rather than dividing by zero.

### 4.4 Example

Suppose:

| Metric | Corporate segment | Other segments |
|---|---:|---:|
| Observations | 100 | 200 |
| High-revenue observations | 65 | 90 |
| High-revenue rate | 65% | 45% |

Then:

\[
Difference=65\%-45\%=20\%
\]

The Corporate segment has a 20-percentage-point higher observed high-revenue rate.

This does not establish that the customer segment causes higher revenue.

### 4.5 Implementation details

The Python implementation uses dictionaries and grouped observations.

The JavaScript implementation uses `Map` for categorical grouping and event notifications after analytical execution.

The C++ implementation uses STL maps and vectors.

The Java implementation uses domain records, enumerations, streams and an `InfluencerService`.

The PostgreSQL implementation calculates group-level rates using SQL aggregation and comparison logic.

### 4.6 Interpretation limitations

The implemented influencer analysis is a descriptive association analysis.

It does not implement:

- Multivariable logistic regression.
- Statistical significance testing.
- Causal inference.
- Confounding adjustment.
- Propensity-score matching.
- Multiple-testing correction.
- Confidence intervals for group differences.

The same distinction applies when interpreting Power BI Key Influencers results.

An influential category in an analytical visual should not automatically be treated as a causal business driver.

### 4.7 Sample-size considerations

A category containing very few observations may produce an unstable target rate.

The implementations therefore support a minimum group-size threshold.

For enterprise reporting, further controls should include confidence intervals, minimum population requirements and statistical significance assessment.

---

## 5. Time-Series Forecasting

### 5.1 Concept

Forecasting estimates future values using historical observations.

In Power BI, forecasting can be applied to time-series visuals to estimate future trends and display uncertainty intervals.

Typical applications include:

- Monthly sales forecasting.
- Revenue planning.
- Inventory requirements.
- Demand estimation.
- Marketing expenditure planning.
- Operational capacity planning.

### 5.2 Time-series aggregation

The transaction-level dataset is converted into monthly revenue observations.

\[
MonthlyRevenue_t =
\sum_{i \in Month_t} Revenue_i
\]

This aggregation is essential because individual transaction records are not directly equivalent to monthly business performance.

The implementations sort observations chronologically before calculating the forecast.

### 5.3 Linear regression

The forecasting implementations use a linear trend model.

\[
\hat{Y_t}=a+bt
\]

Where:

- \(\hat{Y_t}\) is predicted revenue.
- \(a\) is the intercept.
- \(b\) is the estimated trend.
- \(t\) is the time index.

The slope is:

\[
b =
\frac{
\sum(t-\bar{t})(Y_t-\bar{Y})
}{
\sum(t-\bar{t})^2
}
\]

The intercept is:

\[
a=\bar{Y}-b\bar{t}
\]

The estimated future revenue is:

\[
Forecast_{t+h}=a+b(t+h)
\]

### 5.4 Forecast uncertainty

The implementations calculate residuals:

\[
e_t=Y_t-\hat{Y_t}
\]

Residual standard deviation estimates the historical variation around the fitted trend.

An approximate forecast interval is calculated as:

\[
Forecast \pm 1.96 \times
ResidualStd \times
\sqrt{1+\frac{h}{n}}
\]

Where:

- \(h\) is the forecast horizon.
- \(n\) is the number of historical observations.
- 1.96 is the approximate normal 95% multiplier.

The resulting interval is a simplified uncertainty estimate, not a calibrated prediction interval from a complete statistical time-series model.

### 5.5 Forecasting workflow

    Transaction Records
           |
           v
    Monthly Aggregation
           |
           v
    Chronological Ordering
           |
           v
    Regression Estimation
           |
           v
    Residual Calculation
           |
           v
    Future Revenue Prediction
           |
           v
    Uncertainty Intervals
           |
           v
    Forecast Reporting

### 5.6 Forecast policy

The Java implementation defines an explicit `ForecastPolicy` record.

It specifies:

- Minimum historical observations.
- Maximum forecasting horizon.
- Confidence multiplier.

The other implementations enforce equivalent input validation through their respective functions and methods.

The PostgreSQL function uses `REGR_SLOPE`, `REGR_INTERCEPT` and residual standard deviation.

### 5.7 Seasonality and limitations

A linear regression model identifies an overall trend but does not automatically capture:

- Monthly seasonal patterns.
- Holiday effects.
- Promotions.
- Structural market changes.
- Economic cycles.
- Sudden changes in customer behaviour.

The Python implementation exposes a seasonal adjustment option based on historical residuals at corresponding seasonal positions. This is a basic adjustment rather than a complete seasonal forecasting model.

For production forecasting, model selection should consider:

- Seasonal decomposition.
- Exponential smoothing.
- ARIMA.
- Seasonal ARIMA.
- External explanatory variables.
- Rolling-origin validation.
- Forecast error metrics.

### 5.8 Forecast evaluation

Forecast performance should be evaluated against observations that were not used to estimate the model.

Common metrics include:

**Mean Absolute Error**

\[
MAE =
\frac{1}{n}
\sum_{i=1}^{n}|Y_i-\hat{Y_i}|
\]

**Root Mean Squared Error**

\[
RMSE =
\sqrt{
\frac{1}{n}
\sum_{i=1}^{n}(Y_i-\hat{Y_i})^2
}
\]

**Mean Absolute Percentage Error**

\[
MAPE =
\frac{100}{n}
\sum_{i=1}^{n}
\left|
\frac{Y_i-\hat{Y_i}}{Y_i}
\right|
\]

MAPE requires special treatment when actual values are zero or close to zero.

None of these evaluation metrics should be inferred from the forecast intervals alone.

---

## 6. Anomaly Detection

### 6.1 Concept

Anomaly detection identifies observations that differ substantially from expected or typical behaviour.

In business intelligence, anomalies can indicate:

- Unusually high revenue.
- Unexpected revenue declines.
- Abnormal transaction values.
- Data-entry errors.
- Unusual discount levels.
- Potential operational disruptions.

An anomaly is an observation requiring investigation. It is not automatically evidence of fraud, error or misconduct.

### 6.2 Median and median absolute deviation

The implementations use the Median Absolute Deviation method.

First calculate the median:

\[
M=Median(X)
\]

Then calculate absolute deviations:

\[
D_i=|X_i-M|
\]

Calculate the median absolute deviation:

\[
MAD=Median(D)
\]

The robust anomaly score is:

\[
ModifiedZ_i =
\frac{0.6745(X_i-M)}{MAD}
\]

An observation is classified as anomalous when:

\[
|ModifiedZ_i|\geq3.5
\]

The threshold is configurable.

### 6.3 Why median absolute deviation?

Traditional standard deviation is sensitive to extreme observations.

For example, a few unusually large transactions can increase the mean and standard deviation, making other unusual transactions harder to identify.

The median and MAD are more resistant to extreme values.

### 6.4 Severity classification

The implementations classify observations into two anomaly severity categories.

| Anomaly score magnitude | Classification |
|---|---|
| Below 3.5 | Normal |
| 3.5 to below 7 | High |
| 7 or greater | Critical |

The direction is also meaningful:

- Positive score: unusually high observation.
- Negative score: unusually low observation.

The Python, JavaScript and Java implementations preserve the signed score. The C++ implementation does the same through its `Anomaly` structure.

### 6.5 Anomaly workflow

    Historical Revenue
           |
           v
       Median
           |
           v
     Absolute Deviations
           |
           v
          MAD
           |
           v
     Modified Z-Scores
           |
           v
     Threshold Evaluation
           |
           v
     Severity Classification
           |
           v
      Investigation Report

### 6.6 Important edge cases

**Zero MAD**

If all observations are identical, MAD is zero. The modified Z-score cannot be calculated.

The implementations explicitly reject this situation rather than silently dividing by zero.

**Negative deviations**

Anomalies can be positive or negative. Both directions must be preserved.

**Extreme observations**

The detector identifies unusual values relative to the dataset distribution. It does not establish why the values occurred.

**Changing business distributions**

A global median can be misleading when different products or regions naturally have different revenue distributions.

Production systems may need separate anomaly models by region, product, season or transaction type.

### 6.7 Power BI anomaly detection distinction

Power BI provides anomaly-detection capabilities for supported time-series visual configurations.

The implementations in this project demonstrate a separate statistical anomaly-detection mechanism based on MAD.

They should not be interpreted as reproductions of Power BI's internal anomaly-detection implementation.

---

## 7. Python Implementation

**File:** `main.py`

The Python implementation is designed as a self-contained analytical application.

### 7.1 Data structures

The implementation uses:

| Structure | Purpose |
|---|---|
| `SalesRecord` | Immutable transaction representation |
| `DecompositionNode` | Recursive analytical hierarchy |
| `InfluencerResult` | Group comparison results |
| `ForecastPoint` | Future revenue estimate |
| `AnomalyResult` | Anomaly classification |
| `SalesAnalytics` | Analytical service |

Dataclasses provide structured records and reduce unnecessary boilerplate.

Enumerations define analytical categories.

Dictionaries support categorical grouping.

Lists preserve ordered transaction and forecast collections.

Sets enforce transaction identifier uniqueness.

### 7.2 Analytical execution

The main function executes the following sequence:

1. Generate transaction records.
2. Validate the dataset.
3. Calculate business measures.
4. Build a decomposition tree.
5. Evaluate key influencers.
6. Aggregate monthly revenue.
7. Forecast future observations.
8. Detect anomalies.
9. Export the report.
10. Execute assertions.

### 7.3 Report export

The report is exported as JSON.

The implementation writes to a temporary file before replacing the destination file.

This reduces the risk of leaving a partially written report after a failed write.

The exported report contains:

- Business metrics.
- Decomposition results.
- Influencer comparisons.
- Forecast estimates.
- Anomaly classifications.

The destination directory is created when necessary.

---

## 8. JavaScript Implementation

**File:** `main.js`

The JavaScript implementation uses an event-driven architecture.

### 8.1 Main components

| Component | Responsibility |
|---|---|
| `RandomGenerator` | Deterministic data generation |
| `AnalyticsEngine` | Analytical execution |
| `Map` | Grouped categorical observations |
| `Set` | Identifier uniqueness |
| `EventTarget` | Analytical event publication |
| `Promise` | Asynchronous report generation |
| Node.js filesystem | Persistent JSON reporting |

### 8.2 Event-driven processing

The engine emits events when analytical operations finish.

Examples include:

- `decomposition-complete`
- `influencers-complete`
- `forecast-complete`
- `anomalies-complete`
- `report-complete`

An application can subscribe to these events without placing event-handling logic inside every analytical method.

This separation is useful in applications that update dashboards, log analytical activity or coordinate several services.

### 8.3 Immutability

The engine stores frozen transaction objects.

Its internal record collection is protected from ordinary external mutation.

The `getRecords()` method returns copies instead of exposing the internal collection.

This improves reliability when multiple application components consume the same dataset.

### 8.4 Caching

The implementation caches frequently requested calculations, including business measures and monthly revenue.

The cache reduces repeated aggregation work when the underlying dataset remains unchanged.

The engine does not expose an update operation. If the underlying data changes, a new engine instance should be created so cached values cannot become stale.

### 8.5 Asynchronous reporting

Report generation uses Node.js filesystem promises.

The implementation:

- Resolves the destination path.
- Creates the parent directory.
- Generates a unique temporary filename.
- Writes JSON with restrictive file permissions.
- Renames the temporary file to the destination.
- Removes temporary files when an operation fails.

In production, filesystem permissions and destination-directory access must still be controlled.

---

## 9. C++17 Implementation

**File:** `main.cpp`

The C++ implementation emphasizes explicit domain structures, controlled memory ownership and STL-based analytical processing.

### 9.1 Domain structures

The program defines:

- `SalesRecord`
- `BusinessMeasures`
- `DecompositionNode`
- `Influencer`
- `ForecastResult`
- `Anomaly`

The `AnalyticsEngine` owns its transaction collection and provides analytical operations through member functions.

### 9.2 STL mechanisms

| STL component | Application |
|---|---|
| `vector` | Transaction and result collections |
| `map` | Dimension grouping and monthly aggregation |
| `set` | Duplicate identifier validation |
| `sort` | Ranking and anomaly ordering |
| `accumulate` | Aggregate numerical calculations |
| `mt19937` | Deterministic random data generation |
| `pow` | Regression and variance calculations |

### 9.3 Memory management

The implementation uses standard containers and value semantics.

It avoids manual memory allocation and external dependencies.

The constructor moves the input transaction collection into the analytical engine.

This reduces unnecessary copying while maintaining clear ownership.

### 9.4 Failure handling

Invalid dimensions, duplicate transaction identifiers, invalid thresholds, insufficient observations and zero MAD values result in explicit exceptions.

The main function catches standard exceptions and returns a non-zero exit status when execution fails.

---

## 10. Java 17 Implementation

**File:** `Main.java`

The Java implementation follows an enterprise-oriented service architecture.

### 10.1 Layered design

    AnalyticsApplication
            |
            v
       SalesRepository
            |
            +----------------------+
            |                      |
            v                      v
     MeasurementService     DecompositionService
            |                      |
            v                      v
     InfluencerService       ForecastService
            |                      |
            +----------+-----------+
                       |
                       v
                 AnomalyService

The repository provides validated transaction data.

Individual services own distinct analytical responsibilities.

The application coordinates the services.

### 10.2 Records and enumerations

Java 17 records provide immutable domain representations.

Examples include:

- `SalesTransaction`
- `BusinessMetrics`
- `DecompositionNode`
- `InfluencerResult`
- `ForecastPoint`
- `AnomalyResult`
- `ForecastPolicy`
- `AnomalyPolicy`

Enumerations provide controlled values for:

- Analytical dimensions.
- Target variables.
- Anomaly severity.

This reduces the risk of inconsistent category names and invalid policy configurations.

### 10.3 Service separation

**MeasurementService**

Calculates aggregate business metrics.

**DecompositionService**

Constructs hierarchical revenue breakdowns.

**InfluencerService**

Evaluates group-level target rates.

**ForecastService**

Performs regression-based time-series forecasting.

**AnomalyService**

Applies MAD-based anomaly classification.

### 10.4 Policy objects

The forecasting service receives a `ForecastPolicy`.

The anomaly service receives an `AnomalyPolicy`.

This separates analytical configuration from analytical execution.

Policy validation occurs when the objects are constructed.

Such a design supports enterprise configuration management and makes policy changes easier to test.

---

## 11. PostgreSQL Implementation

**File:** `advanced_analytics.sql`

The SQL implementation models an analytical warehouse using a dimensional data architecture.

### 11.1 Schema design

The database uses the `powerbi_analytics` schema.

Its principal entities are:

| Table | Purpose |
|---|---|
| `dim_region` | Geographical classifications |
| `dim_product` | Product attributes |
| `dim_customer_segment` | Customer categories |
| `dim_channel` | Distribution channels |
| `dim_date` | Calendar attributes |
| `fact_sales` | Transaction-level measures |
| `analysis_run` | Analytical execution history |
| `influencer_result` | Stored influencer comparisons |
| `forecast_result` | Forecast observations |
| `anomaly_result` | Detected anomalies |

### 11.2 Dimensional modelling

The fact table references the dimension tables using foreign keys.

    dim_region --------+
                       |
    dim_product ------+
                       |
    dim_customer_segment
                       |
    dim_channel ------+---- fact_sales
                       |
    dim_date ---------+

This design avoids repeatedly storing descriptive attributes in every fact record.

It supports analytical joins and dimensional aggregation.

### 11.3 Integrity controls

The schema includes:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Numeric range checks.
- Severity validation.
- Analytical execution-state validation.
- Unique forecast periods per execution.
- Unique anomaly records per execution and transaction.

These controls protect data integrity at the database level.

### 11.4 SQL analytical functions

The implementation includes the following database functions:

| Function | Purpose |
|---|---|
| `fn_decomposition_tree` | Revenue aggregation by dimension |
| `fn_key_influencers` | Group-level target-rate comparisons |
| `fn_revenue_forecast` | Monthly trend prediction |
| `fn_detect_anomalies` | MAD-based anomaly detection |
| `fn_start_analysis` | Initiates an analytical execution |

The procedure `sp_complete_analysis` finalizes an execution and stores its result count.

### 11.5 Views

The SQL file defines:

- `vw_business_metrics`
- `vw_monthly_revenue`
- `vw_region_product_revenue`
- `vw_product_performance`

These views provide reusable analytical datasets.

They can also serve as database sources for Power BI reporting models.

### 11.6 Common Table Expressions

The SQL functions and reporting queries use CTEs to separate logical analytical stages.

For example, key influencer processing separates:

1. Group-level observations.
2. Overall target rates.
3. Comparison calculations.
4. Final ranking.

This makes the analytical logic easier to inspect and maintain.

### 11.7 Analytical execution history

The `analysis_run` table records each execution.

Its status progresses through:

    PENDING
       |
       v
    RUNNING
       |
       +----------+
       |          |
       v          v
    COMPLETED   FAILED

Completed and failed runs are treated as terminal states by the validation trigger.

This provides a basic audit trail for analytical execution.

### 11.8 Indexing

Indexes are created for commonly used filtering and joining columns.

Examples include:

- Transaction date.
- Region and transaction date.
- Product.
- Segment.
- Channel.
- Revenue.
- Analytical execution type.
- Anomaly severity.

Index selection should be validated using actual query workloads and `EXPLAIN ANALYZE`.

Indexes improve some retrieval operations but increase storage consumption and write overhead.

### 11.9 Transaction handling

The SQL script uses an explicit transaction for schema creation, data insertion and analytical validation.

Analytical execution records and their corresponding result records are also written within transactional execution blocks.

A failed transaction should not leave partially committed analytical results.

---

## 12. Relationship Between the Four Analytical Techniques

Although the four techniques operate on related business data, they answer different questions.

| Technique | Primary question | Analytical output |
|---|---|---|
| Decomposition tree | Where does the result come from? | Hierarchical contribution |
| Key Influencers | Which factors are associated with the outcome? | Comparative influence indicators |
| Forecasting | What might happen next? | Future estimates and intervals |
| Anomaly detection | What differs from expected behaviour? | Unusual observations and scores |

### Integrated business scenario

Assume a retail company observes a decline in monthly revenue.

The analytical investigation can proceed as follows.

**Stage 1: Decomposition tree**

Identify the region, product and channel combinations contributing to the decline.

**Stage 2: Key Influencers**

Investigate whether particular customer segments, products or channels are associated with the selected revenue outcome.

**Stage 3: Forecasting**

Estimate future monthly revenue using historical observations.

**Stage 4: Anomaly detection**

Identify unusually low or high transactions that may require further investigation.

The four methods provide complementary analytical evidence. None independently establishes the cause of a business outcome.

---

## 13. Data Modelling and Power BI Integration

The PostgreSQL schema provides a relational foundation for a Power BI semantic model.

A typical model uses:

- `fact_sales` as the central fact table.
- `dim_date` as the date dimension.
- `dim_region` as the geographical dimension.
- `dim_product` as the product dimension.
- `dim_customer_segment` as the customer dimension.
- `dim_channel` as the distribution dimension.

The fact table contains additive and non-additive measures.

### Suggested core DAX measures

**Total Revenue**

    Total Revenue =
    SUM(fact_sales[revenue])

**Total Units**

    Total Units =
    SUM(fact_sales[units])

**Average Transaction Revenue**

    Average Transaction Revenue =
    AVERAGE(fact_sales[revenue])

**Marketing Spend**

    Marketing Spend =
    SUM(fact_sales[marketing_spend])

**Marketing ROI**

    Marketing ROI =
    DIVIDE(
        [Total Revenue] - [Marketing Spend],
        [Marketing Spend]
    )

**Average Satisfaction**

    Average Satisfaction =
    AVERAGE(fact_sales[satisfaction_score])

These measures provide reusable calculations for Power BI visuals.

### Visual selection

| Business requirement | Power BI visual |
|---|---|
| Investigate revenue contribution | Decomposition tree |
| Identify associated factors | Key Influencers |
| Estimate future revenue | Line chart with forecasting |
| Identify unusual time-series observations | Line chart with anomaly detection |
| Compare regional revenue | Bar chart |
| Monitor monthly performance | Line chart |
| Monitor business performance | KPI cards |

The forecasting and anomaly-detection capabilities have visual and data-configuration requirements. They should be evaluated in the actual Power BI environment rather than assumed to be available for every data source or chart configuration.

---

## 14. Testing and Validation

The implementations include executable validation mechanisms.

| Validation | Purpose |
|---|---|
| Non-empty dataset | Prevent meaningless analysis |
| Unique transaction IDs | Preserve record identity |
| Valid categorical fields | Prevent invalid grouping |
| Finite numerical values | Prevent invalid statistical calculations |
| Non-negative revenue | Enforce financial constraints |
| Discount range | Protect discount calculations |
| Satisfaction range | Preserve measurement validity |
| Minimum observation count | Prevent unsupported forecasting |
| Positive anomaly threshold | Protect anomaly scoring |
| Non-zero MAD | Prevent division by zero |
| Valid decomposition dimensions | Prevent invalid grouping |
| Valid forecast horizon | Control computational workload |

### Statistical validation

A production implementation should also evaluate:

- Forecast error on holdout observations.
- Residual distribution.
- Forecast interval coverage.
- Stability of influencer rankings.
- Group sample sizes.
- Anomaly precision and recall when labelled observations exist.
- Model performance across different regions and periods.

### Reproducibility

The Python, JavaScript, C++ and Java implementations use deterministic random seeds or fixed synthetic datasets.

This makes repeated executions more consistent and helps identify unexpected changes in analytical output.

---

## 15. Performance and Production Considerations

### Data volume

The demonstration dataset contains 600 transactions.

A production retail warehouse may contain millions of transactions.

For larger workloads:

- Push aggregation operations into PostgreSQL when appropriate.
- Avoid repeatedly scanning the entire dataset.
- Use materialized views for expensive recurring aggregations.
- Apply date and dimensional filters early.
- Use incremental refresh where supported.
- Evaluate query plans.
- Monitor memory consumption.
- Partition large fact tables when workload patterns justify it.

### Analytical accuracy

The implementations deliberately use relatively simple statistical procedures.

Their main purpose is to demonstrate analytical mechanisms and their engineering requirements.

The linear forecasting model does not replace comprehensive forecasting methods.

The group comparisons do not establish causal influence.

The MAD detector does not identify the cause of unusual observations.

### Security

Production systems should enforce:

- Database least-privilege access.
- Appropriate authentication.
- Row-level security where required.
- Restricted report access.
- Secure connection configuration.
- Protection of commercially sensitive transaction records.
- Audit logging.
- Controlled report-export destinations.
- Validation of externally supplied analytical parameters.

### Data governance

Analytical outputs should retain their provenance.

Important metadata includes:

- Data extraction timestamp.
- Source system.
- Analytical execution identifier.
- Applied filters.
- Selected dimensions.
- Forecast horizon.
- Statistical method.
- Threshold configuration.
- Dataset version.
- Execution status.

The PostgreSQL `analysis_run` table provides a starting point for maintaining execution history.

---

## 16. Technical Limitations

The following distinctions are important when applying these implementations to actual Power BI projects.

| Area | Demonstration implementation | Production consideration |
|---|---|---|
| Decomposition | Recursive top-N aggregation | Interactive Power BI visual and model configuration |
| Influencers | Median-based binary target and group comparisons | Multivariable analysis and statistical validation |
| Forecasting | Linear regression trend | Seasonality, model selection and backtesting |
| Anomalies | MAD-based numerical detector | Time-series-specific detection and operational investigation |
| Data | Deterministic synthetic records | Validated business data |
| Reporting | Console and JSON output | Power BI semantic model and governed reporting |
| Storage | PostgreSQL relational schema | Workload-specific warehouse architecture |
| Execution | Local application execution | Scheduled, monitored analytical pipelines |

The Python seasonal adjustment is simplified and is not a complete seasonal forecasting algorithm.

The JavaScript event-driven engine uses Node.js event and filesystem capabilities; it does not provide a browser-based dashboard.

The C++ implementation focuses on computational logic rather than visual rendering.

The Java implementation separates business services and policy configuration but does not include an enterprise application server.

The PostgreSQL functions provide executable database-side analytics but do not implement every analytical algorithm available in Power BI.

These distinctions prevent the demonstration code from being mistaken for an exact implementation of the Power BI product internals.

---

## 17. File Structure

The six deliverables can be stored as:

| File | Purpose |
|---|---|
| `main.py` | Python analytical engine |
| `main.js` | Event-driven JavaScript analytical engine |
| `main.cpp` | C++17 statistical implementation |
| `Main.java` | Java 17 enterprise analytical services |
| `advanced_analytics.sql` | PostgreSQL warehouse and analytical functions |
| `README.md` | Technical documentation |

The source implementations use standard libraries and PostgreSQL built-in capabilities, without third-party application dependencies.

## 18. Execution Requirements

| Implementation | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10+ | None |
| JavaScript | Node.js 18+ | None |
| C++17 | C++17 compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 15+ | None |

The Python and JavaScript applications export JSON reports to their execution directories.

The C++ and Java applications display their analytical results in the terminal.

The PostgreSQL implementation stores business data, execution history, forecast results and anomaly results in relational tables.

The five implementations provide separate, executable perspectives on the same Power BI Advanced Analytics domain.
