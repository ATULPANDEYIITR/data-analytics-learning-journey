# Data Visualization with Matplotlib

## Scope

This project models a complete data-visualization workflow around monthly software-delivery metrics.

The central visualization concepts are:

- Figure and axes objects
- Labels and titles
- Legends
- Annotations
- Linear and logarithmic scales
- Subplots
- Line charts
- Bar charts
- Axis ranges and tick formatting
- Validation before plotting
- Visualization-ready relational data
- Rendering-state management

The dataset represents three engineering teams:

| Team | Metrics |
|---|---|
| Platform | Deployments, incidents, lead time, coverage |
| Payments | Deployments, incidents, lead time, coverage |
| Analytics | Deployments, incidents, lead time, coverage |

The four metrics have different analytical meanings. Deployments measure delivery volume, incidents measure operational failures, lead time measures delivery latency, and coverage measures automated-test coverage.

## Visualization Model

The workflow separates data from presentation:

    Raw observations
          |
          v
    Validation
          |
          v
    Metric selection
          |
          v
    Scale selection
          |
          v
    Axes configuration
          |
          +----> Labels
          |
          +----> Legend
          |
          +----> Annotations
          |
          +----> Grid and ticks
          |
          v
    Figure / subplot layout
          |
          v
    Rendered visualization

A `Figure` represents the complete visual canvas. An `Axes` object represents an individual plotting region inside that figure.

The Python implementation uses a 2 × 2 subplot layout so that multiple metrics can be compared without forcing unrelated measurements onto one axis.

## Figure and Axes

The Python implementation creates one figure containing four axes.

The first axis displays deployment trends as lines. The second displays incidents as grouped bars. The third displays lead time with a logarithmic y-axis. The fourth displays test coverage as a percentage trend.

This distinction matters because a figure controls the complete composition while each axes object controls its own coordinate system, labels, title, ticks, grid, legend, and plotted data.

The JavaScript, C++, and Java implementations model this separation independently rather than reproducing the Matplotlib API.

## Labels and Titles

Each plot has:

- a descriptive title
- an x-axis label
- a y-axis label
- period labels
- metric-specific units where appropriate

Labels provide semantic context. A value such as `10` is ambiguous without knowing whether it represents deployments, incidents, hours, or percent coverage.

The Python implementation also applies a figure-level title to describe the complete dashboard.

## Legends

The line charts identify Platform, Payments, and Analytics through legends.

A legend maps visual series to domain entities. It is especially important when several teams occupy the same axes.

The implementation supplies meaningful team names rather than relying on automatically generated identifiers.

The database stores whether a chart requires a legend through the `show_legend` field in `chart_definitions`.

## Annotations

Annotations add explanatory information to a particular data point.

The Python deployment chart identifies the highest final deployment value and connects the annotation to its corresponding point with an arrow.

The C++ model represents annotations explicitly through an `Annotation` structure containing:

- annotation label
- period index
- metric value

The Java implementation uses the same domain concept through the immutable `Annotation` record.

This separates annotation selection from the eventual rendering mechanism.

## Scales

A linear scale represents equal numerical differences using equal visual distances.

For example:

    0 ---- 20 ---- 40 ---- 60 ---- 80

A logarithmic scale represents multiplicative changes more naturally:

    1 ---- 10 ---- 100 ---- 1000

Lead time is positive in every source record, so it is suitable for logarithmic visualization.

The Python implementation uses a logarithmic y-axis for lead time.

The C++ implementation explicitly rejects a logarithmic configuration when any selected value is zero or negative.

The Java policy service performs the same validation before constructing a plot definition.

The PostgreSQL validation query checks whether lead-time observations are positive before they are passed to a logarithmic visualization.

## Subplots

The Python dashboard contains four independent axes:

    +---------------------------+---------------------------+
    | Monthly Deployments       | Production Incidents     |
    | line chart                | grouped bar chart        |
    +---------------------------+---------------------------+
    | Lead Time                 | Automated Test Coverage  |
    | logarithmic scale         | percentage line chart    |
    +---------------------------+---------------------------+

Each subplot has its own scale and interpretation.

This prevents incompatible units from being combined into a single coordinate system.

The Java implementation represents the dashboard as named plot definitions, while the C++ implementation calculates a 2 × 2 layout model containing four panel positions.

## Python Implementation

The Python source is the primary Matplotlib implementation.

### Data model

The script uses immutable dataclasses:

- `MonthlyMetric`
- `TeamSeries`

`MonthlyMetric` represents one period of observations.

`TeamSeries` represents all observations for one team and exposes convenient metric lists for plotting.

Validation rejects:

- empty team names
- empty metric collections
- duplicate months
- negative deployment counts
- negative incident counts
- non-positive lead time
- coverage outside 0–100 percent

### Figure construction

`create_dashboard()` creates the figure and four axes using `plt.subplots()`.

The figure uses constrained layout to reduce collisions between:

- titles
- axis labels
- tick labels
- legends
- annotations

The source saves the figure at a controlled resolution and closes it after saving to avoid retaining unnecessary figure objects.

### Formatting

The deployment and incident axes use integer tick locations.

Coverage uses a custom percentage formatter.

The lead-time chart uses a logarithmic scale and retains grid lines for both major and minor logarithmic positions.

### Validation

`run_self_checks()` verifies the expected data invariants before rendering.

This is useful in automated execution because invalid data can be detected before a misleading figure is produced.

## JavaScript Implementation

The JavaScript file uses Node.js standard-library functionality.

It does not attempt to reproduce Matplotlib. Instead, it models a browser-oriented visualization pipeline.

### Data processing

The source validates:

- array lengths
- integer deployment values
- integer incident values
- positive lead-time values
- coverage ranges

It calculates percentage changes and constructs linear coordinate mappings.

### Event-driven state

`VisualizationState` extends `EventEmitter`.

It maintains:

- selected team
- selected metric

Changing either state emits a `selectionChanged` event.

This represents a common interactive visualization workflow in which user selections alter the current visualization without changing the underlying dataset.

### SVG rendering

The program produces an SVG file directly.

The renderer:

- calculates x coordinates
- calculates y coordinates
- draws axes
- draws grid lines
- draws a polyline
- places data markers
- labels periods
- attaches point-specific values through SVG `<title>` elements

SVG text is escaped before insertion so that metric names cannot inject arbitrary markup into the generated document.

## C++17 Implementation

The C++ program models a visualization engine rather than a plotting API.

### Domain types

The program defines:

- `MonthlyRecord`
- `TeamSeries`
- `Axis`
- `Annotation`
- `PlotPanel`

It uses enumerations for:

- `ScaleType`
- `Metric`

This avoids passing loosely defined strings through the analytical pipeline.

### Scale normalization

The `normalize()` function converts a metric from a data domain to a rendering range.

Linear normalization uses the standard affine transformation:

`output = output_min + ((value - input_min) / (input_max - input_min)) * (output_max - output_min)`

For logarithmic scaling, the values are transformed using base-10 logarithms before normalization.

The implementation explicitly rejects non-positive values for logarithmic scaling.

### Performance

Validation and range calculation are linear in the number of observations.

The engine keeps the rendering model separate from the data model so that a future renderer can consume validated values without changing the analytical layer.

## Java 17 Implementation

The Java source models an enterprise-style visualization service.

### Domain modeling

Java records provide immutable representations for:

- monthly metrics
- team series
- annotations
- axis policies
- plot definitions

This prevents accidental mutation of visualization configuration after it has been validated.

### Policy separation

`VisualizationPolicy` defines a contract for visualization validation.

`DefaultVisualizationPolicy` checks:

- non-empty datasets
- equal period counts
- duplicate periods
- logarithmic-scale constraints

`PlotService` is responsible for constructing a valid plot definition after the policy accepts the input.

This separates policy decisions from rendering configuration.

### Streams and immutable collections

Streams are used for metric extraction and aggregation.

`List.copyOf()` and records provide immutable domain state.

The resulting design makes it difficult for downstream rendering code to silently alter the validated data.

## PostgreSQL Implementation

The PostgreSQL script stores visualization-ready source data and chart configuration.

### Relational model

The primary relationships are:

    teams
      |
      +---- team_metrics ---- reporting_periods
                     |
                     v
              visualization_dataset
                     |
                     v
              chart_definitions

`teams` contains the entities being compared.

`reporting_periods` provides ordered time periods.

`team_metrics` stores observations for a team and period.

`chart_definitions` stores visualization metadata such as metric type and scale type.

### Constraints

Database constraints enforce important invariants:

- team names are unique
- period names are unique
- team-period combinations are unique
- deployment counts cannot be negative
- incident counts cannot be negative
- lead time must be positive
- coverage must remain between 0 and 100
- logarithmic charts must use positive source values

These rules prevent invalid analytical data from silently reaching the plotting layer.

### Indexing

The database contains indexes for:

- period-based retrieval
- team and period retrieval

The indexes support common dashboard queries without indexing every column indiscriminately.

### View

`visualization_dataset` provides a clean relational view for downstream analysis.

It joins team, period, and metric information into a plotting-friendly result.

### CTEs and window functions

The reporting queries use CTEs to isolate intermediate calculations.

Window functions calculate:

- first deployment value
- last deployment value
- first lead-time value
- last lead-time value
- per-team ranking

These operations allow the database to prepare analytical data before it reaches the visualization layer.

## Metric Interpretation

| Metric | Chart form | Main purpose | Scale |
|---|---|---|---|
| Deployments | Line | Delivery volume over time | Linear |
| Incidents | Grouped bars | Compare operational failures | Linear |
| Lead time | Line | Compare delivery latency | Logarithmic |
| Coverage | Line | Track testing completeness | Linear percentage |

The chart form is selected according to the analytical question rather than simply applying one chart type to every metric.

## Edge Cases

The implementations account for several problematic conditions.

### Empty datasets

The Python, C++, and Java implementations reject empty visualization datasets.

### Duplicate periods

Duplicate periods can cause misleading lines and incorrect temporal ordering. The source models therefore reject duplicate period identifiers.

### Constant values

If a metric has the same minimum and maximum value, normalization would otherwise divide by zero. The C++ and Python implementations provide padding or midpoint behavior for this condition.

### Logarithmic scales

Zero and negative values cannot be represented on a conventional logarithmic axis. Every implementation that models logarithmic behavior validates positivity.

### Invalid percentages

Coverage values outside 0–100 are rejected at both application and database levels.

### Large datasets

For large datasets, validation and basic aggregation remain linear in the number of observations. Rendering cost depends on the number of visual primitives and can become the dominant factor.

## Security Considerations

Visualization code can process data originating from files, databases, APIs, or user-controlled sources.

The implementations therefore avoid treating source data as executable content.

The JavaScript SVG renderer escapes XML-sensitive characters before inserting text into the document.

The PostgreSQL model uses constraints instead of relying solely on application validation.

The Python output path is explicitly resolved and its parent directory is created before saving the figure.

Database access should use a restricted database role in production. Visualization users generally need read access to analytical views rather than unrestricted write access to operational tables.

## Practical Workflow

A production workflow can separate responsibilities as follows:

    Operational data
          |
          v
    PostgreSQL validation
          |
          v
    Analytical query / view
          |
          v
    Python data ingestion
          |
          v
    Metric validation
          |
          v
    Figure + Axes
          |
          +---- labels
          +---- legends
          +---- annotations
          +---- scale
          +---- subplot layout
          |
          v
    PNG / SVG / other output

The JavaScript implementation demonstrates an alternative event-driven presentation model, while C++ and Java demonstrate how the same visualization decisions can be represented as strongly typed domain services.

## Implementation Comparison

| Implementation | Primary role | Distinct mechanism |
|---|---|---|
| Python | Matplotlib dashboard | Figure, axes, subplots, annotations, formatters |
| JavaScript | Interactive visualization model | Event-driven state and SVG |
| C++17 | Visualization engine | Strongly typed scale and normalization model |
| Java 17 | Enterprise service | Immutable records and policy objects |
| PostgreSQL | Data preparation | Relational constraints, views, CTEs, window functions |

The implementations share the same analytical domain but deliberately use different engineering structures.

## Limitations

The Python source renders a static dashboard rather than implementing a browser interaction layer.

The JavaScript source generates SVG directly and does not provide a complete browser application framework.

The C++ and Java programs model visualization decisions and validation but do not depend on an external plotting library.

The PostgreSQL layer prepares and validates visualization data but does not render images.

These boundaries keep data storage, analytical validation, visualization policy, and rendering concerns separate.
