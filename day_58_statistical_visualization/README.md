# Statistical Visualization

## Scope

This project implements a compact statistical visualization toolkit across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The six visualization families are treated as distinct analytical views:

| Visualization | Primary purpose | Typical analytical question |
|---|---|---|
| Histogram | Distribution by intervals | How are numerical observations distributed across ranges? |
| Box plot | Robust distribution summary | Where are the center, quartiles, spread, and potential outliers? |
| Violin plot | Distribution shape plus density | Where is probability mass concentrated and how does the distribution behave? |
| Scatter plot | Relationship between two numerical variables | Does one numerical variable vary systematically with another? |
| Density plot | Smoothed numerical distribution | What is the estimated continuous distribution shape? |
| Categorical plot | Frequency comparison | Which categories occur most often? |

The implementations use the same statistical concepts while deliberately using different programming models.

## Conceptual Model

A visualization is not merely a graphical representation. It is a transformation from observations into a visual encoding.

A useful workflow is:

`raw observations -> validation -> descriptive statistics -> statistical transformation -> visual encoding -> interpretation`

The transformations differ by plot type.

For a histogram, observations are assigned to intervals.

For a box plot, ordered observations are reduced to quartiles, fences, and outlier candidates.

For a violin plot and density plot, a kernel density estimate produces a smoothed approximation of the distribution.

For a scatter plot, each observation remains a two-dimensional coordinate.

For a categorical plot, labels are grouped and converted into frequencies and percentages.

## Histogram

The histogram implementations divide a numerical range into bins.

For observations `x`, a fixed-width bin assignment can be expressed as:

`bin(x) = floor((x - minimum) / bin_width)`

The final interval requires special handling because the maximum observation can otherwise produce an index equal to the number of bins.

The implementations therefore clamp the final index to the last valid bin.

Histograms are useful for identifying:

- concentration
- skewness
- approximate modality
- gaps
- unusually sparse regions
- extreme observations

Bin width affects interpretation. Too few bins can hide structure, while too many bins can make random variation appear meaningful.

## Box Plot

The box plot implementation calculates:

- minimum
- first quartile
- median
- third quartile
- maximum
- interquartile range
- lower fence
- upper fence
- observations outside the fences

The interquartile range is:

`IQR = Q3 - Q1`

The standard Tukey-style fences used by the implementations are:

`lower fence = Q1 - 1.5 * IQR`

`upper fence = Q3 + 1.5 * IQR`

Values outside these fences are displayed as potential outliers.

A box plot does not imply that every point outside the fences is erroneous. An outlier may represent a legitimate rare observation, measurement variation, a different population, or a data-quality problem.

The implementations use percentile interpolation rather than assuming that quartile positions always correspond to exact observations.

## Violin Plot

A violin plot combines distribution density with a mirrored shape.

The implementation estimates density using a Gaussian kernel:

`f(x) = 1 / (n h) * sum(K((x - xi) / h))`

with a Gaussian kernel and a bandwidth based on a Silverman-style rule:

`h = 1.06 * sigma * n^(-1/5)`

The density is sampled at multiple points and mirrored around a central axis.

This makes the violin plot useful when the shape of a distribution matters more than the five-number summary.

A violin plot can expose:

- multiple concentration regions
- asymmetry
- long tails
- broad or narrow distributions

Bandwidth selection is a trade-off. A small bandwidth preserves local structure but can become noisy. A large bandwidth produces a smoother representation but can conceal multimodality.

## Scatter Plot

A scatter plot represents paired observations as coordinates:

`(x1, y1), (x2, y2), ..., (xn, yn)`

The implementations explicitly validate that the two datasets have equal lengths.

The plot preserves the individual observations rather than reducing them to aggregate bins.

Scatter plots can reveal:

- positive or negative association
- nonlinear structure
- clusters
- heteroscedasticity
- isolated observations
- gaps in the observed range

A scatter plot alone does not establish causation.

## Density Plot

The density plot uses the same kernel density estimation mechanism as the violin plot but displays the resulting one-dimensional curve directly.

The distinction is visual and analytical:

- a density plot emphasizes the estimated distribution curve
- a violin plot uses the same type of density information as a mirrored distribution shape

The density curve is evaluated over an extended range so that the visual representation includes the estimated tails around the observed minimum and maximum.

## Categorical Plot

Categorical visualization begins by grouping labels.

For a category `c`:

`frequency(c) = number of observations belonging to c`

The implementations also calculate:

`percentage(c) = frequency(c) / total_observations * 100`

The category plot sorts categories by frequency where appropriate, making differences in representation easy to inspect.

Empty labels are rejected because they create ambiguous analytical categories.

## Python Implementation

The Python implementation is a self-contained statistical toolkit using only the standard library.

Important components include:

| Component | Implementation |
|---|---|
| Dataset representation | Frozen `dataclass` |
| Plot classification | `Enum` |
| Validation | Custom `VisualizationError` |
| Distribution summary | `FiveNumberSummary` |
| Histogram | Explicit bin calculation |
| Density | Gaussian kernel estimator |
| Categorical analysis | Dictionary-based counting |
| Visualization output | SVG generation |
| Validation tests | Runtime assertions |
| File output | `pathlib.Path` |

The script creates `statistical_visualization_report.svg`.

The SVG contains six panels and a numerical summary. Because SVG is generated directly, the program does not require a plotting package.

The implementation also validates finite numerical input and rejects empty datasets.

## JavaScript Implementation

The JavaScript implementation is designed for Node.js and uses the standard library.

Its main statistical abstraction is `NumericDataset`.

JavaScript-specific mechanisms include:

- classes
- `Map` for categorical frequency aggregation
- asynchronous `main`
- `fs.writeFileSync`
- immutable copies of numerical input
- explicit error propagation
- structured objects for statistical results

The visualization dashboard collects SVG fragments through a dedicated `VisualizationDashboard` class.

The implementation produces `statistical_visualization_report_js.svg`.

The JavaScript version complements the Python version by emphasizing object-oriented state management, JavaScript collections, and Node.js file handling rather than reproducing Python syntax mechanically.

## C++17 Implementation

The C++ implementation treats the visualization system as a technical case study built from explicit domain classes.

The central `NumericDataset` class owns validated numerical observations and provides:

- mean calculation
- population standard deviation
- percentile interpolation
- five-number summaries
- IQR outlier detection
- histogram generation
- kernel density estimation

The implementation uses STL containers and algorithms such as `vector`, `map`, `min_element`, `max_element`, `accumulate`, and `sort`.

Exception handling is implemented through `VisualizationError`.

SVG output is written through an `ofstream`.

The generated file is `statistical_visualization_report_cpp.svg`.

C++17 provides explicit ownership and data structures while keeping the implementation independent of third-party plotting libraries.

## Java 17 Implementation

The Java implementation models statistical visualization through domain-oriented classes and interfaces.

Important Java mechanisms include:

- records for immutable statistical results
- enums for visualization types
- an interface for plot renderers
- an `EnumMap` for renderer registration
- immutable dataset storage
- Java Streams for descriptive statistics and categorical grouping
- custom exceptions
- explicit validation

The `PlotRenderer` interface establishes a renderer boundary, while `BoxPlotRenderer` demonstrates a separate domain component.

The implementation creates `statistical_visualization_report_java.svg`.

The design makes it possible to treat each plot as a distinct rendering strategy while keeping statistical data separate from SVG output.

## PostgreSQL Implementation

The PostgreSQL implementation represents visualization as a relational workflow.

The model contains:

`dataset -> observation`

and, for paired numerical observations:

`dataset -> scatter_point`

Visualization requests are represented separately:

`dataset -> visualization_request -> visualization_result`

This separation distinguishes source data from a request to analyze or render that data.

### Relational Controls

The schema uses:

- primary keys
- foreign keys
- unique constraints
- check constraints
- partial indexes
- trigger-based validation
- PostgreSQL functions
- transactions
- common table expressions

Numerical and categorical observations are mutually exclusive through a check constraint.

Observation indexes are unique within each dataset.

Visualization types are restricted to the six supported plot families.

Histogram bin counts are constrained to a practical range.

## PostgreSQL Statistical Operations

The SQL implementation uses PostgreSQL's `percentile_cont` for quartile calculation.

The `numeric_five_number_summary` function exposes:

- minimum
- Q1
- median
- Q3
- maximum
- IQR
- lower fence
- upper fence

The IQR query can then identify potential outliers directly in SQL.

Histogram frequencies are produced with `width_bucket`.

Categorical frequencies use `GROUP BY`, while percentages use a window aggregation over grouped counts.

Scatter data remains in paired form so a client-side or reporting layer can consume the coordinates without reconstructing relationships between independent tables.

## Workflow Validation

Visualization requests are validated according to their required data type.

| Plot | Required data |
|---|---|
| Histogram | Numerical observations |
| Box plot | Numerical observations |
| Violin plot | Numerical observations |
| Density plot | Numerical observations |
| Scatter plot | Paired numerical coordinates |
| Categorical plot | Category observations |

The trigger `trg_visualization_validation` automatically creates a corresponding result record.

This produces explicit workflow states:

`pending -> valid -> completed`

or:

`pending -> invalid`

The sample data contains valid requests for all six visualization types.

## Edge Cases

The implementations handle several important edge conditions.

### Empty numerical input

Empty numerical datasets are rejected before statistical calculations occur.

### Non-finite values

NaN and infinite values are rejected because they can invalidate ordering, range calculations, and density estimation.

### Constant numerical data

A constant dataset has zero variance. The density implementation therefore uses a fallback scale so that division by zero does not occur.

### Identical histogram values

When minimum and maximum are identical, a synthetic plotting interval is created and all observations are assigned to the first bin.

### Equal scatter lengths

Scatter plots require one x-coordinate for every y-coordinate. Unequal arrays are rejected.

### Empty categories

Empty categorical labels are rejected because they produce ambiguous frequency groups.

### Outliers

Outlier detection is based on IQR fences rather than deletion. The original observations remain available for analysis.

## Performance Considerations

Most descriptive operations require scanning the observations.

For `n` numerical observations:

| Operation | Typical complexity |
|---|---:|
| Mean | O(n) |
| Population standard deviation | O(n) |
| Histogram | O(n + b) |
| Percentile with sorting | O(n log n) |
| IQR outlier detection after quartiles | O(n) |
| KDE with `n` observations and `m` evaluation points | O(nm) |
| Categorical counting | O(n) expected with hash-based maps |

Kernel density estimation is the most computationally expensive operation in these implementations because each evaluation point considers every observation.

For larger datasets, a production system would normally reduce the number of KDE evaluation points, use specialized numerical libraries, cache density calculations, or employ approximation techniques.

The PostgreSQL indexes focus on dataset-scoped numerical and categorical retrieval. They are useful for filtering observations by dataset and value type without indiscriminately indexing every column.

## Security and Data Integrity

The implementations avoid dynamic execution of arbitrary input.

Category labels are XML-escaped before insertion into SVG text.

The PostgreSQL schema enforces domain restrictions through database constraints rather than relying entirely on application validation.

Important integrity controls include:

- foreign keys
- mutually exclusive observation fields
- positive observation indexes
- valid visualization types
- bounded histogram bin counts
- non-empty category labels
- unique dataset observation positions

The database therefore rejects several classes of malformed state even when application-level validation is bypassed.

## Comparison of the Five Implementations

| Language | Main perspective | Output |
|---|---|---|
| Python | Statistical toolkit and validation | SVG report |
| JavaScript | Object and event-oriented Node.js processing | SVG report |
| C++17 | Explicit numerical and rendering engine | SVG report |
| Java 17 | Enterprise-style domain and renderer model | SVG report |
| PostgreSQL | Relational statistical workflow and validation | Query results |

All implementations use the same underlying analytical distinctions, but their architecture differs.

Python emphasizes concise numerical workflows and standard-library data modeling.

JavaScript emphasizes maps, object state, and Node.js file processing.

C++17 emphasizes explicit data structures, algorithms, and deterministic resource handling.

Java 17 emphasizes immutable domain objects, renderer interfaces, records, and service-oriented structure.

PostgreSQL emphasizes relational integrity, aggregation, statistical functions, and database-enforced workflow state.

## Practical Interpretation

The visualization types should not be treated as interchangeable.

A histogram is primarily a binned distribution view.

A box plot compresses distribution information into robust summary statistics.

A violin plot emphasizes distribution shape and density.

A scatter plot examines paired numerical relationships.

A density plot emphasizes a smoothed estimate of a numerical distribution.

A categorical plot compares frequencies among discrete labels.

A strong statistical workflow selects the visualization according to the structure of the data and the analytical question rather than selecting a plot solely for appearance.

## Generated Artifacts

Running the five executable implementations produces SVG reports similar in structure to:

`statistical_visualization_report.svg`

`statistical_visualization_report_js.svg`

`statistical_visualization_report_cpp.svg`

`statistical_visualization_report_java.svg`

The PostgreSQL script instead creates the relational model, inserts representative observations, validates visualization requests, and executes analytical queries.

## Execution Requirements

| Implementation | Requirement |
|---|---|
| Python | Python 3 |
| JavaScript | Node.js |
| C++17 | C++ compiler with C++17 support |
| Java | Java 17 or later |
| PostgreSQL | PostgreSQL with standard SQL procedural language support |

No third-party plotting library is required by the five implementations.

The generated SVG files are ordinary text-based vector documents and can be opened directly by an SVG-capable browser or viewer.
