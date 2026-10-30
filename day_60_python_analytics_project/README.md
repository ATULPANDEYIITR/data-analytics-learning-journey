# Comprehensive Exploratory Data Analysis of the Iris Dataset

## 1. Project Overview

This project implements an end-to-end exploratory data analysis (EDA) workflow using the Iris flower measurements dataset from the UCI Machine Learning Repository.

The objective is to examine the statistical characteristics, distributions, relationships, data quality, and species-level differences in a real-world biological dataset.

The project contains five independent technical implementations:

| Implementation | Primary responsibility |
|---|---|
| Python | Statistical analysis, data cleaning, and analytical report generation |
| JavaScript | Event-driven data processing and structured analytical reporting |
| C++17 | Efficient numerical analysis and statistical computation |
| Java 17 | Enterprise-oriented analytical services and immutable domain modeling |
| PostgreSQL | Relational ingestion, validation, analytical views, and database reporting |

All implementations focus on the same dataset and analytical objectives while using the features and architectural strengths of their respective languages.

## 2. Dataset Description

**Dataset:** Iris

**Original researcher:** Ronald A. Fisher

**Publication year:** 1936

**Repository:** UCI Machine Learning Repository

**Dataset DOI:** https://doi.org/10.24432/C56C76

**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

The complete dataset contains 150 flower observations distributed equally across three species.

Each observation has four numerical measurements and one categorical target variable.

### Dataset structure

| Variable | Data type | Unit | Description |
|---|---|---|---|
| sepal_length | Continuous | cm | Length of the sepal |
| sepal_width | Continuous | cm | Width of the sepal |
| petal_length | Continuous | cm | Length of the petal |
| petal_width | Continuous | cm | Width of the petal |
| species | Categorical | None | Iris species classification |

### Species categories

- Setosa
- Versicolor
- Virginica

The balanced distribution is useful for comparing group-level statistics without an initially unequal class frequency.

The measurements are actual observations rather than artificially generated numerical examples.

### Data access and reproducibility

The Python and JavaScript implementations attempt to acquire the complete original dataset when a local CSV is unavailable. Both also support an embedded subset when remote access is unavailable.

The C++17 and Java 17 implementations use a local `iris.csv` when supplied and otherwise use the embedded 15-observation subset.

The PostgreSQL implementation inserts 15 genuine observations and one deliberately malformed staging record to demonstrate validation and rejection handling.

Results produced from the embedded subset must not be presented as statistics for all 150 observations.

## 3. Understanding Exploratory Data Analysis

Exploratory Data Analysis is a systematic process of investigating a dataset before drawing statistical or predictive conclusions.

It examines the structure and characteristics of observations without assuming that every variable follows a predetermined statistical distribution.

The workflow used in this project is:

```text
Original Dataset
       |
       v
Data Acquisition
       |
       v
Initial Inspection
       |
       v
Schema Validation
       |
       v
Data Quality Assessment
       |
       v
Data Cleaning
       |
       v
Descriptive Statistics
       |
       v
Distribution Analysis
       |
       v
Species-Level Comparison
       |
       v
Correlation Analysis
       |
       v
Outlier Detection
       |
       v
Analytical Interpretation
       |
       v
Report and Cleaned Dataset
```

Each stage addresses a different analytical question.

| Stage                 | Main question                                               |
| --------------------- | ----------------------------------------------------------- |
| Acquisition           | Where did the observations originate?                       |
| Inspection            | What does the dataset contain?                              |
| Validation            | Are the values structurally and numerically acceptable?     |
| Cleaning              | Which records require exclusion or correction?              |
| Descriptive analysis  | What are the central values and variability?                |
| Distribution analysis | How are observations divided among species?                 |
| Comparative analysis  | How do measurements differ between species?                 |
| Correlation           | Which numerical measurements vary together?                 |
| Outlier analysis      | Which values fall outside an established statistical range? |
| Reporting             | What can be supported by the observed data?                 |

## 4. Data Acquisition and Schema Validation

The original dataset is distributed as a CSV file.

The implementations recognize the following schema:

```
sepal_length,sepal_width,petal_length,petal_width,species
```

Some original UCI files use five columns without a header. The Python and JavaScript loaders handle both formats.

The species labels are normalized to three canonical categories:

| Original label   | Normalized value |
| ---------------- | ---------------- |
| Iris-setosa      | setosa           |
| Iris-versicolor  | versicolor       |
| Iris-virginica   | virginica        |
| Iris-versicolour | versicolor       |

Normalization provides consistent categorical grouping without changing the numerical measurements.

### Validation rules

The implementations verify:

- Five columns per observation.
- Numerical measurements can be converted to floating-point values.
- Measurements are finite.
- Measurements are greater than zero and below ten.
- Species labels belong to the recognized categories.
- Empty datasets are rejected.
- Invalid observations are reported instead of silently interpreted as valid data.

Validation is performed before statistical calculations.

This separation prevents malformed input from contaminating descriptive statistics and group comparisons.

## 5. Data Quality Assessment

Data quality assessment identifies potential problems that could affect analytical conclusions.

### Missing values

A missing value represents an unavailable observation.

A missing measurement must not be treated as zero because zero would represent a numerical value rather than an absence of data.

The Python, JavaScript, C++, and Java implementations reject records containing missing measurements during ingestion.

The PostgreSQL implementation maintains a permissive raw staging table and records missing-field failures before data is transferred into the validated analytical table.

The accepted observation table uses `NOT NULL` constraints.

### Duplicate observations

A duplicate observation has identical numerical measurements and the same species category.

Duplicates can influence frequency calculations and descriptive statistics.

The Python, JavaScript, and Java implementations identify identical observations during loading.

The PostgreSQL staging process preserves source-row identities and does not automatically delete repeated measurements. This is intentional because two genuine flowers could theoretically have identical recorded measurements.

Duplicate detection and duplicate removal are separate operations.

### Invalid numerical values

Invalid measurements include:

- Text in a numerical field.
- Non-finite numerical values.
- Missing measurements.
- Values outside the defined validation range.

An invalid row is not allowed to enter the accepted analytical dataset.

### Data quality metrics

The generated reports consider:

| Metric                 | Purpose                              |
| ---------------------- | ------------------------------------ |
| Valid observations     | Number of accepted rows              |
| Rejected rows          | Number of records failing validation |
| Missing cells          | Missing-value assessment             |
| Duplicate observations | Repeated-record detection            |
| Species count          | Number of represented categories     |
| Rejection reason       | Explanation of ingestion failure     |

The data-quality report describes the accepted analytical sample separately from the rejected input records.

## 6. Descriptive Statistical Analysis

Descriptive statistics provide a numerical description of each measurement.

The project calculates the following statistics for all four numerical features.

### Minimum

The smallest observed value.

### Maximum

The largest observed value.

### Mean

The arithmetic average:

\\[ \bar{x}=\frac{1}{n}\sum\_{i=1}^{n}x_i \\]

The mean describes the average measurement but can be influenced by unusually large or small observations.

### Median

The middle observation after sorting the measurements.

For an even number of observations, the median is calculated as the average of the two central observations.

The median is less sensitive to extreme values than the mean.

### Quartiles

Quartiles divide the ordered observations into four portions.

- Q1 represents the 25th percentile.
- Q2 represents the 50th percentile.
- Q3 represents the 75th percentile.

The implementations use linear interpolation between adjacent sorted observations.

### Interquartile Range

The interquartile range measures the spread of the central half of the observations.

\\[ IQR=Q_3-Q_1 \\]

A larger IQR indicates greater dispersion among the middle observations.

### Sample standard deviation

The project uses the sample standard deviation:

\\[ s= \sqrt{ \frac{\sum\_{i=1}^{n}(x_i-\bar{x})^2} {n-1} } \\]

The denominator uses \\(n-1\\), rather than \\(n\\), because the calculation estimates sample variability.

### Statistical output

| Feature      | Calculated statistics                                      |
| ------------ | ---------------------------------------------------------- |
| Sepal length | Minimum, Q1, median, mean, Q3, maximum, standard deviation |
| Sepal width  | Minimum, Q1, median, mean, Q3, maximum, standard deviation |
| Petal length | Minimum, Q1, median, mean, Q3, maximum, standard deviation |
| Petal width  | Minimum, Q1, median, mean, Q3, maximum, standard deviation |

The project reports feature-specific statistics so that the numerical differences between measurements remain visible.

## 7. Species Distribution Analysis

Species distribution analysis examines the number and percentage of observations associated with each category.

The percentage of observations belonging to a species is:

\\[ P_i=\frac{n_i}{N}\times100 \\]

Where:

- \\(n_i\\) is the number of observations in a species category.
- \\(N\\) is the total number of accepted observations.

The complete Iris dataset contains 50 observations per species.

Its category distribution is:

| Species    | Observations | Percentage |
| ---------- | ------------ | ---------- |
| Setosa     | 50           | 33.33%     |
| Versicolor | 50           | 33.33%     |
| Virginica  | 50           | 33.33%     |
| Total      | 150          | 100%       |

This balanced distribution is a property of the complete dataset, not an assumption applied during analysis.

The implementations calculate the actual distribution from loaded observations.

## 8. Species-Level Comparative Analysis

Global statistics combine all three species.

Such statistics can conceal differences between groups.

For example, the global mean petal length combines smaller and larger petal measurements from distinct species.

Species-level analysis calculates the average measurement separately for each category.

\\[ \bar{x}\_{species} = \frac{1}{n\_{species}} \sum x_i \\]

The comparison examines:

- Mean sepal length.
- Mean sepal width.
- Mean petal length.
- Mean petal width.

### Analytical interpretation

Petal measurements are particularly useful for distinguishing the three Iris categories.

Setosa generally exhibits substantially smaller petal measurements than Versicolor and Virginica.

Virginica generally has larger average petal measurements than Versicolor.

These differences describe patterns within the dataset. They do not establish that any single measurement independently determines a biological species.

## 9. Correlation Analysis

Correlation measures the strength and direction of the linear relationship between two numerical variables.

This project uses Pearson's correlation coefficient.

\\[ r= \frac{ \sum\_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y}) }{ \sqrt{ \sum\_{i=1}^{n}(x_i-\bar{x})^2 \sum\_{i=1}^{n}(y_i-\bar{y})^2 } } \\]

The coefficient lies between -1 and +1.

| Correlation | Interpretation                      |
| ----------- | ----------------------------------- |
| +1          | Perfect positive linear association |
| 0           | No linear association               |
| -1          | Perfect negative linear association |

The project calculates six unique feature pairs and presents a complete four-variable correlation matrix.

### Important distinctions

A positive correlation does not prove causality.

A correlation near zero does not necessarily mean that two variables are unrelated because nonlinear relationships may exist.

The complete Iris dataset generally shows a particularly strong positive relationship between petal length and petal width.

The exact value must be calculated from the actual observations being analyzed.

### Numerical reliability

Each implementation checks whether the denominator of the Pearson calculation is zero.

A zero-variance feature cannot produce a defined Pearson correlation coefficient.

Such a result is represented as unavailable rather than causing an invalid numerical calculation.

## 10. Outlier Detection

Outliers are observations that are unusually distant from the central distribution of a feature.

This project applies the 1.5 × IQR method.

The lower boundary is:

\\[ L=Q_1-1.5(IQR) \\]

The upper boundary is:

\\[ U=Q_3+1.5(IQR) \\]

An observation is flagged when:

\\[ x\<L \\]

or

\\[ x>U \\]

Outliers are identified separately for each numerical feature.

### Why outliers are not automatically removed

An unusually large observation does not necessarily indicate an incorrect measurement.

It may represent:

- Genuine biological variability.
- An unusual specimen.
- A measurement problem.
- An incorrect data entry.

Removing an observation without investigating its origin can introduce bias.

The project therefore reports outlier counts and preserves valid observations.

The PostgreSQL implementation also exposes the lower and upper IQR boundaries for every identified outlier.

## 11. Implementation Architecture

### Python: Statistical analytics and reporting

The Python implementation is organized around reusable domain structures and analytical functions.

| Component                | Responsibility                                                  |
| ------------------------ | --------------------------------------------------------------- |
| `Flower`                 | Immutable representation of an observation                      |
| `Dataset`                | Accepted observations, rejected records, and source information |
| `StatisticsResult`       | Structured numerical results                                    |
| `load_dataset()`         | Local loading, remote acquisition, and fallback                 |
| `parse_observation()`    | Measurement and species validation                              |
| `calculate_statistics()` | Descriptive statistics and outlier detection                    |
| `pearson_correlation()`  | Pearson correlation                                             |
| `analyze_by_species()`   | Category-specific averages                                      |
| `create_report()`        | Markdown report construction                                    |
| `export_cleaned_data()`  | Clean CSV generation                                            |

Python uses:

- Dataclasses for structured observation models.
- Lists for ordered records.
- Dictionaries and counters for categorical aggregation.
- Sets for duplicate detection.
- The standard `statistics` module for descriptive calculations.
- `urllib` for dataset acquisition.
- `csv` for structured input and output.
- `argparse` for command-line configuration.
- `pathlib` for file management.

No external Python package is required.

### JavaScript: Event-driven analytical processing

The JavaScript implementation uses an event-driven architecture.

`DatasetRepository` handles dataset loading, CSV interpretation, and validation.

`AnalysisEvents` extends Node.js `EventEmitter` to track accepted and rejected records.

`EDAEngine` performs the main statistical operations.

This separation makes dataset ingestion independent of the analytical calculations.

The implementation uses:

- Classes for processing services.
- `Map` for species distribution and statistics.
- `Set` for duplicate detection.
- Immutable observation objects.
- Promises and asynchronous file operations.
- Native `fetch` for remote dataset retrieval.
- `EventEmitter` for ingestion events.
- `Promise.all()` for independent output operations.

The event counter provides a clear distinction between accepted and rejected ingestion events.

The implementation requires Node.js 18 or later and does not require npm packages.

### C++17: Numerical analysis engine

The C++ implementation emphasizes explicit data structures, numerical computations, and controlled resource usage.

| Component               | Responsibility                             |
| ----------------------- | ------------------------------------------ |
| `Flower`                | Typed measurement representation           |
| `Species`               | Enumerated species categories              |
| `Dataset`               | Accepted observations and rejected records |
| `Statistics`            | Computed statistical measures              |
| `CorrelationMatrix`     | Pairwise correlation results               |
| `parseRow()`            | Record validation                          |
| `quantile()`            | Interpolated quartile calculation          |
| `calculateStatistics()` | Statistical computation                    |
| `pearsonCorrelation()`  | Linear association calculation             |
| `writeReport()`         | Markdown report generation                 |

The implementation uses `std::array` for fixed-width feature measurements and `std::vector` for observations.

`std::optional` represents an undefined correlation result.

`std::map` supports species grouping and ordered aggregation.

The implementation uses C++17 facilities, standard file streams, algorithms, and exception handling.

Its sorting-based percentile implementation requires \\(O(n\log n)\\) time for each feature.

Memory usage is \\(O(n)\\) for the observation collection and intermediate feature vectors.

### Java 17: Enterprise-oriented analytical services

The Java implementation models the analytical process through explicit domain and service components.

Its major components are:

- `Species`: Enumerated species categories.
- `Flower`: Immutable observation record.
- `Dataset`: Immutable accepted and rejected record collections.
- `Statistics`: Structured statistical output.
- `DatasetLoader`: Data ingestion and validation.
- `DescriptiveStatisticsService`: Statistical calculations.
- `GroupAnalysisService`: Category aggregation.
- `CorrelationService`: Pearson calculations.
- `AnalyticalReportService`: Report construction.
- `ReportExporter`: File generation.

Java 17 records simplify immutable domain representation.

Enum-based species modeling prevents unrestricted category values from entering the analysis.

Streams and collectors support category aggregation.

`EnumMap` efficiently associates species categories with their corresponding results.

Custom checked exceptions distinguish data-validation failures from ordinary runtime errors.

The separation between domain types, services, and reporting makes the implementation suitable for extension into larger analytical applications.

### PostgreSQL: Relational analytics and data governance

The PostgreSQL implementation provides database-level validation, ingestion management, and analytical reporting.

Its relational structure contains two principal tables.

raw_iris

Stores incoming source records before validation.

iris_observations

Stores only accepted numerical observations.

The relationship between these tables is enforced through a foreign key.

Each accepted observation retains its original staging record reference.

The `process_pending_rows()` procedure performs validation and controlled promotion into the analytical table.

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Indexes.
- Views.
- Stored procedures.
- PL/pgSQL functions.
- Triggers.
- Transactions.
- Common Table Expressions.
- Ordered-set aggregate functions.
- Window functions.

The audit trigger prevents modification or deletion of processed staging records.

This preserves the relationship between source input and its processing decision.

The analytical views separate data ingestion from downstream reporting.

## 12. PostgreSQL Relational Model

The database architecture is:

```
                 raw_iris
                    |
                    |
          Validation Procedure
                    |
           +--------+--------+
           |                 |
           v                 v
      ACCEPTED             REJECTED
           |
           v
    iris_observations
           |
     +-----+------+----------------+
     |            |                |
     v            v                v
 Descriptive   Species          Correlation
 Statistics   Distribution       Analysis
     |
     v
 Outlier Analysis
     |
     v
 Analytical Views
     |
     v
 Reporting Queries
```

### Data integrity

The analytical table enforces measurement and category restrictions independently of the application code.

This is important because validation should not depend exclusively on a particular programming language or application.

Database constraints provide an additional protection layer.

### Ingestion state management

Each incoming record has one of three states:

| State    | Meaning                                         |
| -------- | ----------------------------------------------- |
| PENDING  | Awaiting validation                             |
| ACCEPTED | Successfully promoted into the analytical table |
| REJECTED | Failed data validation                          |

The original staging record remains available for auditing.

The sample malformed record demonstrates how an invalid measurement is rejected without preventing unrelated valid records from being processed.

## 13. Analytical Outputs

Each implementation generates an analytical report and a cleaned CSV file.

### Python outputs

The default output directory is `iris_eda_output`.

| File                 | Content                                 |
| -------------------- | --------------------------------------- |
| analytical_report.md | Full EDA report                         |
| iris_cleaned.csv     | Validated observations                  |
| rejected_rows.txt    | Rejected input records, when applicable |

### JavaScript outputs

The JavaScript implementation generates the same report structure and cleaned data format.

Its ingestion events also provide operational information about accepted and rejected rows.

### C++17 outputs

The C++ implementation generates:

- `iris_eda_report.md`
- `iris_cleaned.csv`

### Java outputs

The Java implementation generates:

- `iris_eda_output/analytical_report.md`
- `iris_eda_output/iris_cleaned.csv`

A rejection file is generated when the input contains invalid rows.

### PostgreSQL outputs

The SQL implementation stores the validated observations and provides reporting views.

The analytical results are retrieved through SQL queries rather than writing a separate Markdown file from the database.

## 14. Execution Instructions

All five implementations can be executed independently.

### Python

Required runtime: Python 3.10 or later.

Default execution:

`python iris_eda.py`

Offline execution:

`python iris_eda.py --offline`

Custom input and output paths:

`python iris_eda.py --input iris.csv --output-dir analysis_results`

The complete CSV is downloaded when the default input file is absent and remote access is available.

### JavaScript

Required runtime: Node.js 18 or later.

Default execution:

`node iris_eda.js`

Offline execution:

`node iris_eda.js --offline`

Custom paths:

`node iris_eda.js iris.csv analysis_results`

No npm installation is necessary.

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic iris_eda.cpp -o iris_eda`

Run:

`./iris_eda`

Windows:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic iris_eda.cpp -o iris_eda.exe`

`.\iris_eda.exe`

To use a complete locally available dataset:

`.\iris_eda.exe iris.csv`

### Java 17

Compile:

`javac IrisEDA.java`

Run:

`java IrisEDA`

Specify custom input and output locations:

`java IrisEDA iris.csv analysis_results`

### PostgreSQL

Execute the SQL file using `psql`:

`psql -U postgres -d postgres -f iris_eda.sql`

The script creates the `iris_eda` schema and its tables, functions, views, triggers, indexes, and sample records.

It can be executed again because it removes and recreates its dedicated schema.

The script requires permission to create and drop the schema.

## 15. Analytical Methodology and Statistical Consistency

The implementations use consistent analytical definitions.

| Analytical measure       | Method                               |
| ------------------------ | ------------------------------------ |
| Mean                     | Arithmetic mean                      |
| Median                   | 50th percentile                      |
| Q1                       | 25th percentile                      |
| Q3                       | 75th percentile                      |
| Standard deviation       | Sample standard deviation            |
| Outlier detection        | 1.5 × IQR                            |
| Correlation              | Pearson correlation                  |
| Species aggregation      | Arithmetic mean within each category |
| Duplicate identification | Identical feature values and species |

The Python, JavaScript, C++, and Java implementations use interpolated percentiles.

PostgreSQL uses `percentile_cont`, which implements a continuous percentile calculation.

This consistency helps prevent differences caused merely by using incompatible statistical definitions.

Numerical results may still exhibit small differences because of floating-point precision and decimal storage.

## 16. Performance Considerations

The complete Iris dataset contains only 150 observations.

Most operations are computationally inexpensive at this scale.

The same implementation patterns remain relevant for larger datasets.

| Operation                        | Approximate complexity             |
| -------------------------------- | ---------------------------------- |
| Dataset loading                  | O(n)                               |
| Row validation                   | O(n)                               |
| Species counting                 | O(n) expected                      |
| Feature extraction               | O(n)                               |
| Sorting for quartiles            | O(n log n)                         |
| Mean and standard deviation      | O(n)                               |
| One Pearson correlation          | O(n)                               |
| Four-variable correlation matrix | O(1) feature pairs × O(n)          |
| Duplicate detection              | O(n) expected with hash-based sets |
| Species aggregation              | O(n) expected                      |

The implementations avoid repeatedly scanning the dataset when a reusable feature grouping or aggregation provides a clearer workflow.

For significantly larger datasets, database-side aggregation, streaming ingestion, partitioning, and incremental analytical processing may become useful.

## 17. Security and Reliability

Although the dataset is public and non-sensitive, reliable ingestion remains important.

The implementations apply several protective measures.

### Input validation

Numerical conversions are guarded against malformed strings and non-finite measurements.

### Controlled file handling

The implementations use standard file operations and report failures when output files cannot be created.

### Remote data acquisition

Python applies a network timeout and a request identification header.

JavaScript uses a request timeout and verifies the HTTP response.

Both implementations provide an offline fallback.

### Database integrity

PostgreSQL uses constraints, foreign keys, controlled state changes, and a staging audit mechanism.

### Error handling

Invalid records are separated from valid observations.

An invalid row should not silently become a zero measurement or an unrecognized species.

### Reproducibility

Dataset provenance is recorded in the analytical report.

The input source must be retained when analytical results are used in research or formal reporting.

## 18. Limitations and Interpretation

EDA identifies patterns and potential problems. It does not independently establish scientific explanations.

Several limitations apply to this project.

1. The Iris dataset is small compared with contemporary operational datasets.
2. Its three species categories are predefined.
3. Its balanced class distribution should not be generalized to natural population frequencies.
4. Pearson correlation does not detect every nonlinear relationship.
5. IQR outliers are statistical flags and require domain interpretation.
6. Statistical differences between species do not independently establish biological causation.
7. Results from the embedded 15-row subset cannot substitute for complete-dataset findings.

The project is therefore an analytical study of the available measurements, not a biological experiment or a new taxonomic classification claim.

## 19. Research and Reporting Interpretation

A technically defensible analytical report should distinguish observations, calculations, and interpretations.

For this dataset:

Observation: Petal lengths and widths vary across the three species categories.

Calculation: Species-specific means and Pearson correlations quantify selected numerical differences and relationships.

Interpretation: Petal measurements provide useful separation between the species represented in the dataset.

Limitation: These relationships do not establish causation or guarantee comparable discrimination in an unrelated biological population.

This distinction ensures that statistical results are not overstated.

## 20. Project Completion Criteria

The project is considered operational when:

- A valid dataset can be loaded.
- Accepted observations pass numerical and categorical validation.
- Invalid input is identified and reported.
- Dataset quality metrics are available.
- Descriptive statistics are calculated.
- Species distributions are calculated.
- Species-specific means are generated.
- Pearson correlations are calculated.
- IQR outlier analysis is completed.
- A cleaned CSV is generated.
- An analytical report is generated.
- The output clearly identifies the dataset source and applicable limitations.

The five implementations provide independent approaches to the same EDA workflow while preserving the distinction between ingestion, validation, numerical analysis, interpretation, and reporting.
