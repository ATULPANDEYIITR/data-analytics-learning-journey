# Advanced Exploratory Data Analysis

## Scope

This project implements an advanced exploratory data analysis workflow centered on five connected analytical tasks:

- correlation
- covariance
- outlier detection
- numerical transformations
- skewness and feature-distribution analysis

The implementations use a common customer-behavior dataset containing income, spending, visits, tenure, and complaint counts. The four principal analytical concerns are deliberately separated:

| Area | Primary question | Main mechanisms |
|---|---|---|
| Correlation | How strongly do two features move together on a standardized scale? | Pearson and rank correlation |
| Covariance | How does joint variation behave in original measurement units? | Sample covariance |
| Outliers | Which observations are unusually distant from the central distribution? | Quartiles, IQR, Tukey fences |
| Transformations and skewness | How does feature shape affect analysis and interpretation? | Logarithmic, square-root, z-score, robust scaling, skewness |

The implementations do not assume that a strong relationship is causal. A correlation is a descriptive association and requires domain interpretation before it can support a substantive conclusion.

## Analytical Relationship

The workflow follows this structure:

Dataset
→ validation
→ univariate distribution analysis
→ outlier screening
→ transformation analysis
→ covariance
→ correlation
→ rank correlation
→ feature relationship assessment

Each stage uses the result of earlier validation without silently changing the original observations.

## Correlation

Pearson correlation standardizes covariance by the product of the standard deviations:

`r = cov(X,Y) / (sx × sy)`

Its value lies between `-1` and `1`.

A value close to `1` indicates strong positive linear association. A value close to `-1` indicates strong negative linear association. A value near `0` indicates weak linear association, although non-linear dependence can still exist.

The implementations explicitly handle constant features. When a standard deviation is zero, correlation is returned as `0` rather than producing a division-by-zero failure. In a production analytical system, that condition should also be reported because it indicates that the feature contains no observed variation.

The Python implementation builds a complete feature matrix. The JavaScript implementation exposes the same analysis through an event-driven service. The C++ implementation separates statistical operations from the `EDAEngine`. Java represents correlation strategies through the `AssociationMeasure` interface. PostgreSQL uses the native `corr` aggregate.

## Covariance

Covariance retains the measurement scale of the source variables:

`cov(X,Y) = Σ((Xi - X̄)(Yi - Ȳ)) / (n - 1)`

A positive covariance indicates that observations tend to be above or below their respective means together. A negative covariance indicates opposing movement.

Covariance cannot be compared directly across feature pairs when their units or scales differ. For example, income measured in currency units and visits measured as counts produce covariance values whose magnitudes are not directly comparable.

Correlation solves this scale problem through standardization.

The PostgreSQL implementation uses `covar_samp`. The other implementations calculate sample covariance explicitly so that the denominator is `n - 1`.

## Pearson and Rank Correlation

The project also calculates Spearman-style rank correlation.

Rank correlation replaces observations with their ranks before calculating Pearson correlation. This is useful when the relationship is monotonic but not necessarily linear.

For example:

- income may increase rapidly at lower levels and then flatten;
- spending may increase with income without maintaining a constant linear slope;
- a few extreme observations may have a large effect on Pearson correlation.

Comparing Pearson and rank correlation therefore provides a useful diagnostic:

| Result pattern | Interpretation |
|---|---|
| Both high | Strong linear or near-linear monotonic relationship |
| Pearson lower, rank high | Monotonic relationship with non-linear shape |
| Both low | Weak monotonic association |
| Pearson strongly affected by outliers | Inspect distribution and influential observations |

The implementations use tied-rank handling. Equal values receive the average rank of their occupied positions.

## Outlier Detection

The project uses the interquartile range method.

The first and third quartiles are:

`Q1 = 25th percentile`

`Q3 = 75th percentile`

The interquartile range is:

`IQR = Q3 - Q1`

Tukey fences are:

`lower = Q1 - 1.5 × IQR`

`upper = Q3 + 1.5 × IQR`

An observation below the lower fence or above the upper fence is classified as an outlier candidate.

This is a screening mechanism, not an automatic deletion rule.

An extreme income value may be:

- a legitimate high-income customer;
- a valid business account;
- a unit-conversion error;
- a duplicated value;
- a data-entry problem.

The correct response depends on provenance and domain rules. The implementations preserve the original observations and report the candidate values separately.

## Skewness

Skewness describes asymmetry in a distribution.

A positive skew generally indicates a longer or heavier right tail. A negative skew indicates a longer or heavier left tail.

The implementations use an adjusted sample skewness calculation:

`G1 = n / ((n - 1)(n - 2)) × Σ((Xi - X̄) / s)^3`

The sample dataset intentionally contains an unusually large income observation. This creates a right-tail effect that makes income substantially more asymmetric than the more compact behavioral variables.

Skewness is not a direct measure of whether a feature is useful. It is a distributional diagnostic that can influence transformation, visualization, modeling assumptions, and interpretation.

## Transformations

### Logarithmic Transformation

The implementations use `log1p(x)`, which calculates `log(1 + x)`.

It is suitable for non-negative features with substantial right skew and has a useful property at zero:

`log1p(0) = 0`

The implementation rejects values less than or equal to `-1`.

The income example uses `log1p` because income has a large upper-tail observation.

A transformed feature must not be interpreted as though it retained the original measurement scale. A model coefficient based on log-transformed income has a different meaning from a coefficient based on raw income.

### Square-Root Transformation

The square-root transformation is implemented for non-negative observations:

`sqrt(x)`

It is less aggressive than a logarithmic transformation and can be useful for count-like or moderately skewed variables.

Negative values are rejected before transformation.

### Z-Score Standardization

Z-score standardization uses:

`z = (x - mean) / standard deviation`

The result is centered around zero and scaled according to dispersion.

Standardization is useful when numerical scale differences matter, but it does not remove the effect of extreme observations. An extreme observation can still produce an extreme standardized value.

### Robust Scaling

The robust transformation uses the median and IQR:

`robust(x) = (x - median) / IQR`

This reduces sensitivity to extreme observations compared with mean-and-standard-deviation scaling.

If the IQR is zero, the implementation returns zero rather than dividing by zero. A zero IQR indicates that the middle 50 percent of observations have no spread.

## Python Implementation

The Python file provides a complete analytical workflow using standard-library functionality.

Important components include:

| Component | Implementation |
|---|---|
| Data model | `Observation` and `FeatureSummary` dataclasses |
| Validation | finite-value and domain checks |
| Correlation | Pearson coefficient |
| Rank relationship | tied-rank Spearman calculation |
| Covariance | sample covariance |
| Outliers | IQR and Tukey fences |
| Distribution shape | adjusted sample skewness |
| Transformations | log1p, square root, z-score, robust scaling |
| Input | CSV handling |
| Output | structured JSON diagnostic report |
| Testing | executable edge-case validation |

The script creates a temporary CSV dataset, loads it through `csv.DictReader`, performs the analysis, and removes the temporary directory automatically.

This makes the script executable without requiring external packages.

## JavaScript Implementation

The JavaScript file is designed as a Node.js application rather than a direct syntax translation of Python.

The `EDAEngine` extends `EventEmitter`. Feature analysis emits `featureAnalyzed`, and matrix generation emits `matrixReady`.

This event-driven structure separates statistical computation from consumers of analysis results.

The implementation also uses:

- `Map` for analysis results;
- `Set`-compatible data structures where appropriate;
- asynchronous execution through `setImmediate`;
- explicit `EDAError` validation failures;
- immutable copies of transformed arrays;
- tied ranking for Spearman correlation.

The asynchronous boundary models how an analytical service can later integrate with file ingestion, message queues, database access, or other non-blocking operations without changing the statistical layer.

## C++17 Implementation

The C++ implementation is organized as a statistical engine.

`Statistics` owns mathematical operations. `Dataset` owns named feature vectors. `EDAEngine` coordinates feature profiling and relationship analysis.

The design uses:

- `struct` for analytical records;
- `std::vector` for observations;
- `std::map` for named feature collections;
- STL sorting for percentile and rank calculations;
- exception handling for invalid input;
- explicit finite-value validation;
- immutable-by-interface analytical access.

The implementation calculates both Pearson and Spearman relationships and reports high-correlation pairs using a configurable threshold.

The separation between statistical functions and orchestration makes the implementation suitable for extending with additional estimators without embedding domain logic inside individual calculations.

## Java 17 Implementation

The Java implementation models the analytical system using explicit domain abstractions.

`Dataset` validates and stores immutable feature collections. `FeatureProfile` is a record representing computed distribution statistics. `Relationship` is a record representing pairwise analytical results.

The `AssociationMeasure` interface allows different association strategies to be selected explicitly.

Two implementations are provided:

- `PearsonMeasure`
- `SpearmanMeasure`

Transformation behavior is represented by the `Transformation` enum and a corresponding transformation service map.

This structure makes analytical policy explicit. Adding a new transformation does not require changing the dataset representation.

Java's immutable `List.copyOf` is used to prevent accidental modification of the source dataset after validation.

## PostgreSQL Implementation

The PostgreSQL implementation represents the analytical workflow relationally.

The principal entities are:

| Object | Purpose |
|---|---|
| `datasets` | Identifies analytical datasets |
| `observations` | Stores validated source observations |
| `feature_catalog` | Defines supported analytical features |
| `analysis_runs` | Records an analytical execution |
| `feature_statistics` | Stores distribution statistics |
| `feature_relationships` | Stores pairwise covariance and correlation |
| `observation_quality` | Provides screening classifications |
| `relationship_report` | Produces relationship diagnostics |
| `transformed_income` | Provides transformed income values |

Database constraints enforce non-negative domain values and unique customer observations within a dataset.

The database functions provide reusable percentile, feature extraction, profile, and validation operations.

The `feature_profile` function calculates:

- count;
- mean;
- median;
- variance;
- Q1;
- Q3;
- IQR;
- skewness;
- lower fence;
- upper fence;
- outlier count.

PostgreSQL's native statistical aggregates are used for covariance and Pearson correlation.

The transactional analysis block inserts an analysis run, calculates feature statistics, and stores pairwise relationships. The transaction prevents a partially populated analytical run from being committed if an operation fails.

## Feature Relationships

The sample dataset intentionally creates several different relationship structures.

Income and spending generally move together, making them suitable for correlation analysis. Visits and spending provide another behavioral relationship. Complaints have a different interpretation because a high complaint count is not naturally expected to represent stronger engagement.

The analysis therefore distinguishes numerical association from business meaning.

A strong correlation between visits and spending does not prove that visits cause spending. Possible explanations include:

- spending creates more visits;
- visits create more opportunities for spending;
- customer tenure affects both;
- another unmeasured variable affects both.

EDA identifies patterns that require further investigation. It does not establish causal direction.

## Edge Cases

The implementations explicitly address several failure conditions.

### Empty Input

Statistical functions reject empty collections rather than returning misleading numerical values.

### Non-Finite Values

`NaN` and infinite values are rejected before calculations.

### Constant Features

Correlation is guarded against zero standard deviation.

### Small Samples

Sample variance and skewness require sufficient observations.

### Invalid Transformations

Square-root transformations reject negative values. `log1p` rejects values less than or equal to `-1`.

### Zero IQR

Robust scaling avoids division by zero when the central distribution has no spread.

### Ties

Rank correlation assigns average ranks to tied observations.

### Extreme Observations

Outliers are reported rather than automatically removed.

## Performance Considerations

For `n` observations:

| Operation | Typical complexity |
|---|---:|
| Mean | O(n) |
| Variance | O(n) |
| Covariance | O(n) |
| Pearson correlation | O(n) |
| Skewness | O(n) |
| IQR using sorting | O(n log n) |
| Rank generation | O(n log n) |
| Full correlation matrix for `p` features | O(p²n) plus ranking/sorting costs |

The Python and C++ implementations sort copies when percentile calculations are required, preserving the original feature vectors.

For large analytical datasets, materializing every column in memory may become impractical. A production system can compute streaming statistics for some measures while using database or distributed processing for percentile and pairwise calculations.

Correlation matrices can become expensive as the number of features grows because the number of feature pairs increases approximately as `p(p - 1) / 2`.

## Statistical Limitations

Correlation does not imply causation.

Pearson correlation is sensitive to outliers and primarily captures linear association.

Spearman correlation captures monotonic association but does not establish causality.

IQR-based outlier detection assumes that the quartile structure is a useful screening reference. It can behave poorly when a feature is naturally multimodal or has a domain-specific heavy tail.

Skewness can be strongly affected by extreme observations.

Transformations can improve numerical behavior while reducing direct interpretability.

These limitations mean that EDA should be interpreted together with measurement definitions, data provenance, sampling design, and domain knowledge.

## Data Quality and Security Controls

Analytical correctness begins with input validation.

The implementations therefore:

- reject non-finite numeric values;
- enforce non-negative domain values where appropriate;
- validate feature names before dynamic database access;
- avoid modifying raw observations during transformations;
- use parameterized values when constructing dynamic database operations;
- preserve source observations after outlier detection;
- separate transformation output from raw features.

The PostgreSQL implementation uses a controlled feature allowlist before constructing dynamic column references. This prevents arbitrary column identifiers from being accepted by the feature extraction function.

In a production system, access control should also separate raw-data permissions from analytical-result permissions.

## Practical Interpretation Workflow

A disciplined analysis can use the following sequence:

1. Validate schema and measurement ranges.
2. Inspect counts and missingness.
3. Examine central tendency and dispersion.
4. Calculate skewness.
5. Identify potential outliers.
6. Investigate extreme observations against source records.
7. Compare Pearson and rank correlation.
8. Inspect transformations for highly skewed features.
9. Recalculate relationships when transformation is analytically justified.
10. Preserve the original data and document every transformation.

The key distinction is that an analytical transformation is a derived representation. It should not silently replace the raw observation.

## Implementation Comparison

| Concern | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary role | Analytical workflow | Event-driven analytical service | Statistical engine | Enterprise domain model | Relational analytical store |
| Validation | Exceptions | Custom errors | Exceptions | Domain exception | Constraints and functions |
| Correlation | Direct functions | Service methods | `Statistics` | Strategy interface | Native aggregate |
| Outliers | Dataclass profile | Object profile | `FeatureProfile` | Record | Stored statistics |
| Transformations | Enum | Operation strings | Dedicated functions | Enum and service map | Derived view |
| Rank correlation | Tied ranks | Tied ranks | Tied ranks | Tied ranks | Relationship reporting |
| Data storage | Temporary CSV | In-memory objects | In-memory vectors | Immutable collections | Relational tables |
| Transaction support | File lifecycle | Application lifecycle | Application lifecycle | Service lifecycle | Database transaction |

## Conceptual Separation

The project keeps five analytical questions distinct:

`Distribution`
→ What does each feature look like?

`Skewness`
→ Is the distribution asymmetric?

`Outliers`
→ Which observations are unusually distant from the central range?

`Covariance`
→ How do two variables vary together in their original units?

`Correlation`
→ How strong is their standardized association?

`Transformation`
→ Would an alternative representation make the distribution or downstream analysis more appropriate?

These operations are related but are not interchangeable. A transformation is not an outlier treatment, covariance is not correlation, and correlation is not evidence of causation.
