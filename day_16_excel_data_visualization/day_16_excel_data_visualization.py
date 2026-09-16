"""
Excel Data Visualization
========================

A standalone study program covering the principles behind Excel data
visualization, including:

- Bar/column charts
- Line charts
- Pie charts
- Scatter plots
- Combo charts
- Histograms
- Chart selection principles
- Data preparation
- Aggregation
- Axis selection
- Categorical versus numerical data
- Time-series visualization
- Distribution visualization
- Correlation visualization
- Secondary axes
- Misleading charts
- Accessibility
- Performance
- Validation
- Practical chart-selection logic

The examples use only Python's standard library so that the file remains
self-contained. The program models the analytical decisions normally made
before constructing the equivalent Excel charts.

This program does not create an .xlsx file. It teaches and demonstrates the
data structures, calculations, selection rules, and validation logic that
underlie effective Excel visualization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt, pi
from statistics import mean, median, stdev
from typing import Any, Callable, Iterable, Sequence
from collections import Counter, defaultdict
import random


# ---------------------------------------------------------------------------
# 1. Fundamental terminology
# ---------------------------------------------------------------------------

class ChartType(Enum):
    """Main chart families discussed in this study."""

    BAR = "Bar / Column Chart"
    LINE = "Line Chart"
    PIE = "Pie Chart"
    SCATTER = "Scatter Plot"
    COMBO = "Combo Chart"
    HISTOGRAM = "Histogram"


class MeasurementType(Enum):
    """A simplified classification of the variable being visualized."""

    CATEGORICAL = "Categorical"
    DISCRETE_NUMERICAL = "Discrete numerical"
    CONTINUOUS_NUMERICAL = "Continuous numerical"
    TIME = "Time"


class RelationshipType(Enum):
    """Question types that visualization can help answer."""

    COMPARISON = "Compare categories"
    TREND = "Observe change over time"
    COMPOSITION = "Show parts of a whole"
    RELATIONSHIP = "Study relationship between two variables"
    DISTRIBUTION = "Study frequency/distribution"
    MIXED = "Compare different measures together"


@dataclass
class DataColumn:
    """Metadata describing one dataset column."""

    name: str
    measurement_type: MeasurementType
    values: list[Any]

    @property
    def count(self) -> int:
        return len(self.values)


@dataclass
class ChartRecommendation:
    """Result returned by the chart-selection engine."""

    chart_type: ChartType
    reason: str
    warnings: list[str]


# ---------------------------------------------------------------------------
# 2. Sample data
# ---------------------------------------------------------------------------

SALES_BY_REGION = {
    "North": 185000,
    "South": 142000,
    "East": 163000,
    "West": 211000,
}

MONTHLY_SALES = {
    "Jan": 98000,
    "Feb": 104000,
    "Mar": 112000,
    "Apr": 109000,
    "May": 121000,
    "Jun": 135000,
    "Jul": 129000,
    "Aug": 143000,
    "Sep": 151000,
    "Oct": 147000,
    "Nov": 166000,
    "Dec": 182000,
}

EXPENSES_BY_CATEGORY = {
    "Salaries": 420000,
    "Marketing": 90000,
    "Technology": 135000,
    "Operations": 75000,
    "Travel": 30000,
}

ADVERTISING_SPEND = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
ADVERTISING_SALES = [112, 118, 125, 131, 139, 146, 153, 162, 171, 181]

DELIVERY_TIMES = [
    18, 21, 25, 19, 32, 28, 22, 31, 26, 35,
    40, 37, 29, 23, 21, 34, 27, 25, 30, 33,
    38, 42, 45, 24, 20, 19, 28, 31, 36, 41,
]

# A mixed-scale example useful for a combo chart.
MONTHLY_REVENUE = {
    "Jan": 1200000,
    "Feb": 1320000,
    "Mar": 1410000,
    "Apr": 1380000,
    "May": 1530000,
    "Jun": 1680000,
}

MONTHLY_PROFIT_MARGIN = {
    "Jan": 0.12,
    "Feb": 0.135,
    "Mar": 0.141,
    "Apr": 0.128,
    "May": 0.152,
    "Jun": 0.161,
}


# ---------------------------------------------------------------------------
# 3. Basic data inspection
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    """Print a consistent section heading."""

    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_dictionary(data: dict[str, Any], unit: str = "") -> None:
    """Display dictionary-based data in a chart-friendly table."""

    for category, value in data.items():
        suffix = unit
        print(f"{category:15} {value:>12,.2f}{suffix}")


def inspect_numeric_data(values: Sequence[float]) -> dict[str, float]:
    """
    Calculate basic descriptive statistics.

    These calculations are useful before choosing a visualization because
    the range, central tendency, and spread affect interpretation.
    """

    if not values:
        raise ValueError("Cannot inspect an empty numeric dataset.")

    numeric_values = [float(value) for value in values]

    result = {
        "count": len(numeric_values),
        "minimum": min(numeric_values),
        "maximum": max(numeric_values),
        "mean": mean(numeric_values),
        "median": median(numeric_values),
    }

    if len(numeric_values) >= 2:
        result["sample_standard_deviation"] = stdev(numeric_values)
    else:
        result["sample_standard_deviation"] = 0.0

    return result


# ---------------------------------------------------------------------------
# 4. Bar and column charts
# ---------------------------------------------------------------------------

def demonstrate_bar_chart() -> None:
    """
    Demonstrate the logic behind a bar/column chart.

    A bar chart is appropriate when the primary question is comparison across
    categories. Excel often calls vertical versions "column charts".
    """

    print_section("BAR / COLUMN CHART")

    print("Purpose: compare values across discrete categories.")
    print("Example: regional sales.")
    print_dictionary(SALES_BY_REGION, " units")

    highest_region = max(SALES_BY_REGION, key=SALES_BY_REGION.get)
    lowest_region = min(SALES_BY_REGION, key=SALES_BY_REGION.get)

    print(f"\nHighest region: {highest_region}")
    print(f"Lowest region: {lowest_region}")

    print("\nText representation of the chart:")
    maximum = max(SALES_BY_REGION.values())

    for region, value in SALES_BY_REGION.items():
        bar_length = round(value / maximum * 45)
        print(f"{region:>6} | {'█' * bar_length} {value:,}")

    print("\nImportant principles:")
    print("- Use categories on one axis and a numerical measure on the other.")
    print("- Sort categories when ranking is more important than original order.")
    print("- Use a zero baseline when comparing bar lengths.")
    print("- Avoid excessive decorative effects such as 3-D perspective.")


# ---------------------------------------------------------------------------
# 5. Line charts
# ---------------------------------------------------------------------------

def demonstrate_line_chart() -> None:
    """
    Demonstrate time-series visualization.

    A line chart emphasizes continuity and movement across an ordered axis,
    particularly time.
    """

    print_section("LINE CHART")

    print("Purpose: show trends, patterns, seasonality, and change over time.")
    print_dictionary(MONTHLY_SALES, " units")

    values = list(MONTHLY_SALES.values())
    growth = (values[-1] - values[0]) / values[0] * 100

    print(f"\nChange from January to December: {growth:.2f}%")

    print("\nTrend representation:")
    minimum = min(values)
    maximum = max(values)

    for month, value in MONTHLY_SALES.items():
        normalized = 0 if maximum == minimum else (value - minimum) / (
            maximum - minimum
        )
        position = int(normalized * 40)
        print(f"{month:>3} {' ' * position}● {value:,}")

    print("\nLine-chart principles:")
    print("- The x-axis should have meaningful order.")
    print("- Time is a common x-axis.")
    print("- Lines imply continuity; do not use them for unrelated categories.")
    print("- Multiple lines should represent comparable measures.")
    print("- Too many series reduce readability.")


# ---------------------------------------------------------------------------
# 6. Pie charts
# ---------------------------------------------------------------------------

def calculate_percentages(data: dict[str, float]) -> dict[str, float]:
    """Convert positive category values into percentages."""

    total = sum(data.values())

    if total <= 0:
        raise ValueError("Pie-chart data must have a positive total.")

    return {
        category: value / total * 100
        for category, value in data.items()
    }


def demonstrate_pie_chart() -> None:
    """
    Demonstrate composition analysis.

    Pie charts work best when categories represent parts of a single whole.
    """

    print_section("PIE CHART")

    percentages = calculate_percentages(EXPENSES_BY_CATEGORY)

    print("Purpose: show how categories contribute to one whole.\n")

    for category, percentage in percentages.items():
        print(f"{category:15} {percentage:6.2f}%")

    print(f"\nTotal categories: {len(percentages)}")

    if len(percentages) > 7:
        print("Warning: many slices can make a pie chart difficult to read.")

    largest_category = max(percentages, key=percentages.get)
    print(f"Largest component: {largest_category}")

    print("\nPie-chart limitations:")
    print("- It is difficult to compare similar slice sizes precisely.")
    print("- Too many categories create visual clutter.")
    print("- A bar chart is often clearer when precise comparison matters.")
    print("- The values must represent components of the same total.")


# ---------------------------------------------------------------------------
# 7. Scatter plots
# ---------------------------------------------------------------------------

def pearson_correlation(x_values: Sequence[float],
                        y_values: Sequence[float]) -> float:
    """
    Calculate Pearson's correlation coefficient.

    r ranges approximately from -1 to +1:
        +1 = strong positive linear relationship
         0 = no linear correlation
        -1 = strong negative linear relationship

    Correlation does not establish causation.
    """

    if len(x_values) != len(y_values):
        raise ValueError("Both variables must have the same number of values.")

    if len(x_values) < 2:
        raise ValueError("At least two observations are required.")

    x_mean = mean(x_values)
    y_mean = mean(y_values)

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    )

    x_sum = sum((x - x_mean) ** 2 for x in x_values)
    y_sum = sum((y - y_mean) ** 2 for y in y_values)

    denominator = sqrt(x_sum * y_sum)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def demonstrate_scatter_plot() -> None:
    """Demonstrate relationship analysis between two numerical variables."""

    print_section("SCATTER PLOT")

    correlation = pearson_correlation(
        ADVERTISING_SPEND,
        ADVERTISING_SALES,
    )

    print("Purpose: investigate the relationship between two numerical variables.")
    print("\nAdvertising spend and sales:")
    print(f"{'Spend':>10} {'Sales':>10}")

    for spend, sales in zip(ADVERTISING_SPEND, ADVERTISING_SALES):
        print(f"{spend:>10} {sales:>10}")

    print(f"\nPearson correlation: {correlation:.4f}")

    if correlation > 0.7:
        interpretation = "strong positive linear association"
    elif correlation > 0.3:
        interpretation = "moderate positive linear association"
    elif correlation < -0.7:
        interpretation = "strong negative linear association"
    elif correlation < -0.3:
        interpretation = "moderate negative linear association"
    else:
        interpretation = "weak linear association"

    print(f"Interpretation: {interpretation}")

    print("\nImportant distinction:")
    print("A scatter plot can reveal association, clusters, outliers,")
    print("non-linearity, and unusual observations. It does not by itself")
    print("prove that one variable causes the other.")


# ---------------------------------------------------------------------------
# 8. Histograms
# ---------------------------------------------------------------------------

def create_histogram_bins(
    values: Sequence[float],
    number_of_bins: int = 5,
) -> list[tuple[float, float, int]]:
    """
    Build equal-width histogram bins.

    Histograms summarize the distribution of continuous or approximately
    continuous numerical data.
    """

    if not values:
        raise ValueError("Histogram data cannot be empty.")

    if number_of_bins <= 0:
        raise ValueError("Number of bins must be positive.")

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        return [(minimum, maximum, len(values))]

    width = (maximum - minimum) / number_of_bins
    bins: list[tuple[float, float, int]] = []

    for index in range(number_of_bins):
        lower = minimum + index * width
        upper = (
            maximum
            if index == number_of_bins - 1
            else minimum + (index + 1) * width
        )

        count = sum(
            1
            for value in values
            if (lower <= value < upper)
            or (index == number_of_bins - 1 and value == upper)
        )

        bins.append((lower, upper, count))

    return bins


def demonstrate_histogram() -> None:
    """Demonstrate distribution analysis using equal-width bins."""

    print_section("HISTOGRAM")

    statistics = inspect_numeric_data(DELIVERY_TIMES)

    print("Delivery-time statistics:")
    for key, value in statistics.items():
        print(f"{key:30}: {value:.2f}")

    print("\nHistogram:")
    bins = create_histogram_bins(DELIVERY_TIMES, 6)

    maximum_frequency = max(count for _, _, count in bins)

    for lower, upper, count in bins:
        bar_length = (
            0
            if maximum_frequency == 0
            else round(count / maximum_frequency * 40)
        )

        print(
            f"{lower:5.1f} - {upper:5.1f} | "
            f"{'█' * bar_length} {count}"
        )

    print("\nHistogram principles:")
    print("- Adjacent bins represent ranges of numerical values.")
    print("- Histogram bars normally touch because the ranges are continuous.")
    print("- Bin width strongly affects the visible shape.")
    print("- Too few bins can hide structure.")
    print("- Too many bins can make random variation look meaningful.")


# ---------------------------------------------------------------------------
# 9. Combo charts
# ---------------------------------------------------------------------------

def demonstrate_combo_chart() -> None:
    """
    Demonstrate a combo chart using revenue and profit margin.

    Revenue and margin use different scales, so a secondary axis can be
    useful. A secondary axis must be labeled clearly because it can also
    make relationships appear stronger or weaker than they are.
    """

    print_section("COMBO CHART")

    print("Revenue and profit margin use different units:")
    print(f"{'Month':>6} {'Revenue':>14} {'Margin':>12}")

    for month in MONTHLY_REVENUE:
        revenue = MONTHLY_REVENUE[month]
        margin = MONTHLY_PROFIT_MARGIN[month]
        print(f"{month:>6} {revenue:>14,.0f} {margin:>11.2%}")

    print("\nSuggested Excel design:")
    print("- Columns: monthly revenue")
    print("- Line: profit margin")
    print("- Revenue: primary vertical axis")
    print("- Margin: secondary vertical axis")
    print("- Both series: same monthly horizontal axis")

    print("\nSecondary-axis warning:")
    print(
        "Two axes can improve readability when units differ, but poorly "
        "chosen axis limits can visually exaggerate or minimize differences."
    )


# ---------------------------------------------------------------------------
# 10. Chart-selection engine
# ---------------------------------------------------------------------------

def recommend_chart(
    *,
    x_type: MeasurementType,
    y_type: MeasurementType,
    relationship: RelationshipType,
    category_count: int = 0,
    series_count: int = 1,
    values_are_parts_of_whole: bool = False,
    different_scales: bool = False,
) -> ChartRecommendation:
    """
    Recommend a chart based on analytical intent rather than aesthetics.

    This is deliberately rule-based. Real analytical decisions require
    context, but these rules cover common Excel situations.
    """

    warnings: list[str] = []

    if relationship == RelationshipType.COMPOSITION:
        if values_are_parts_of_whole and category_count <= 7:
            return ChartRecommendation(
                ChartType.PIE,
                "The values represent parts of one whole and there are few categories.",
                warnings,
            )

        warnings.append(
            "A pie chart may become difficult to compare with many categories."
        )
        return ChartRecommendation(
            ChartType.BAR,
            "A bar chart makes component-size comparison easier.",
            warnings,
        )

    if relationship == RelationshipType.RELATIONSHIP:
        return ChartRecommendation(
            ChartType.SCATTER,
            "Two numerical variables are being examined for association.",
            warnings,
        )

    if relationship == RelationshipType.DISTRIBUTION:
        return ChartRecommendation(
            ChartType.HISTOGRAM,
            "The goal is to examine the distribution of numerical observations.",
            warnings,
        )

    if relationship == RelationshipType.TREND:
        if x_type == MeasurementType.TIME:
            if series_count > 5:
                warnings.append("Many lines may reduce readability.")
            return ChartRecommendation(
                ChartType.LINE,
                "An ordered time axis makes a line chart appropriate for trends.",
                warnings,
            )

    if relationship == RelationshipType.MIXED:
        if different_scales:
            warnings.append(
                "Clearly label both axes when using a secondary axis."
            )
        return ChartRecommendation(
            ChartType.COMBO,
            "Different measures can be shown together using columns and a line.",
            warnings,
        )

    if relationship == RelationshipType.COMPARISON:
        if category_count > 20:
            warnings.append(
                "Many categories may require sorting, filtering, grouping, "
                "or a different visualization."
            )
        return ChartRecommendation(
            ChartType.BAR,
            "The primary analytical task is category comparison.",
            warnings,
        )

    return ChartRecommendation(
        ChartType.BAR,
        "A bar chart is a reasonable default for simple category comparison.",
        warnings,
    )


def demonstrate_chart_selection() -> None:
    """Demonstrate several chart-selection scenarios."""

    print_section("CHART SELECTION ENGINE")

    scenarios = [
        (
            "Regional sales comparison",
            dict(
                x_type=MeasurementType.CATEGORICAL,
                y_type=MeasurementType.CONTINUOUS_NUMERICAL,
                relationship=RelationshipType.COMPARISON,
                category_count=4,
            ),
        ),
        (
            "Monthly sales trend",
            dict(
                x_type=MeasurementType.TIME,
                y_type=MeasurementType.CONTINUOUS_NUMERICAL,
                relationship=RelationshipType.TREND,
                category_count=12,
            ),
        ),
        (
            "Expense composition",
            dict(
                x_type=MeasurementType.CATEGORICAL,
                y_type=MeasurementType.CONTINUOUS_NUMERICAL,
                relationship=RelationshipType.COMPOSITION,
                category_count=5,
                values_are_parts_of_whole=True,
            ),
        ),
        (
            "Advertising relationship",
            dict(
                x_type=MeasurementType.CONTINUOUS_NUMERICAL,
                y_type=MeasurementType.CONTINUOUS_NUMERICAL,
                relationship=RelationshipType.RELATIONSHIP,
            ),
        ),
        (
            "Delivery-time distribution",
            dict(
                x_type=MeasurementType.CONTINUOUS_NUMERICAL,
                y_type=MeasurementType.DISCRETE_NUMERICAL,
                relationship=RelationshipType.DISTRIBUTION,
            ),
        ),
        (
            "Revenue and margin",
            dict(
                x_type=MeasurementType.TIME,
                y_type=MeasurementType.CONTINUOUS_NUMERICAL,
                relationship=RelationshipType.MIXED,
                different_scales=True,
            ),
        ),
    ]

    for name, parameters in scenarios:
        recommendation = recommend_chart(**parameters)
        print(f"\n{name}")
        print(f"Recommended: {recommendation.chart_type.value}")
        print(f"Reason: {recommendation.reason}")

        for warning in recommendation.warnings:
            print(f"Warning: {warning}")


# ---------------------------------------------------------------------------
# 11. Data validation
# ---------------------------------------------------------------------------

def validate_bar_data(data: dict[str, float]) -> list[str]:
    """Validate common requirements for a category-value chart."""

    errors: list[str] = []

    if not data:
        errors.append("Dataset is empty.")

    if any(not category.strip() for category in data):
        errors.append("A category name is empty.")

    for category, value in data.items():
        if not isinstance(value, (int, float)):
            errors.append(f"{category}: value is not numeric.")
        elif value != value:
            errors.append(f"{category}: value is NaN.")
        elif value < 0:
            errors.append(
                f"{category}: negative values may require careful interpretation."
            )

    return errors


def validate_pie_data(data: dict[str, float]) -> list[str]:
    """Validate common requirements for pie-chart data."""

    errors = validate_bar_data(data)

    if any(value < 0 for value in data.values()):
        errors.append("Negative values cannot be represented as ordinary pie slices.")

    if sum(data.values()) <= 0:
        errors.append("The total must be positive.")

    return errors


def demonstrate_validation() -> None:
    """Show how bad input should be identified before visualization."""

    print_section("DATA VALIDATION")

    valid_data = {
        "A": 30,
        "B": 45,
        "C": 25,
    }

    invalid_data = {
        "A": 30,
        "B": -10,
        "C": float("nan"),
    }

    print("Valid bar data:")
    print(validate_bar_data(valid_data) or "No validation errors.")

    print("\nPotentially invalid data:")
    for error in validate_pie_data(invalid_data):
        print(f"- {error}")


# ---------------------------------------------------------------------------
# 12. Axis scaling and misleading charts
# ---------------------------------------------------------------------------

def normalize(values: Sequence[float]) -> list[float]:
    """
    Normalize values to the [0, 1] interval.

    Normalization is useful for comparison but should not be confused with
    choosing appropriate chart-axis limits.
    """

    if not values:
        return []

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        return [0.5] * len(values)

    return [
        (value - minimum) / (maximum - minimum)
        for value in values
    ]


def demonstrate_axis_effect() -> None:
    """
    Demonstrate why axis limits affect visual interpretation.

    The underlying values remain identical even when the visible range is
    changed.
    """

    print_section("AXIS SCALING AND MISLEADING VISUALIZATION")

    values = [98, 99, 100, 101, 102]

    print("Original values:", values)
    print("Full zero-based range: 0 to 102")
    print("Narrow analytical range: 97 to 103")

    print(
        "\nThe narrow range makes small numerical differences visually larger. "
        "This can be legitimate for close measurements when clearly labeled, "
        "but it becomes misleading when the chart implies a much larger "
        "difference than the data support."
    )

    print("\nBest practice:")
    print("- Check axis minimum and maximum.")
    print("- Label units.")
    print("- Avoid unnecessary 3-D distortion.")
    print("- Do not hide meaningful variation through poor scaling.")


# ---------------------------------------------------------------------------
# 13. Aggregation and pivot-style preparation
# ---------------------------------------------------------------------------

def aggregate_sum(
    rows: Iterable[dict[str, Any]],
    group_key: str,
    value_key: str,
) -> dict[Any, float]:
    """
    Aggregate raw records into category totals.

    Excel PivotTables frequently perform this kind of grouping before a chart
    is created.
    """

    result: dict[Any, float] = defaultdict(float)

    for row in rows:
        group = row[group_key]
        value = row[value_key]

        if not isinstance(value, (int, float)):
            raise TypeError(f"Non-numeric value encountered: {value!r}")

        result[group] += value

    return dict(result)


def demonstrate_aggregation() -> None:
    """Show how transaction-level records become chart-ready data."""

    print_section("DATA AGGREGATION")

    transactions = [
        {"region": "North", "sales": 1200},
        {"region": "North", "sales": 800},
        {"region": "South", "sales": 900},
        {"region": "South", "sales": 1100},
        {"region": "East", "sales": 1500},
        {"region": "West", "sales": 1700},
        {"region": "West", "sales": 600},
    ]

    aggregated = aggregate_sum(transactions, "region", "sales")

    print("Raw records:")
    for transaction in transactions:
        print(transaction)

    print("\nChart-ready regional totals:")
    print_dictionary(aggregated)


# ---------------------------------------------------------------------------
# 14. Moving averages for line-chart analysis
# ---------------------------------------------------------------------------

def moving_average(values: Sequence[float], window: int) -> list[float]:
    """
    Calculate a simple moving average.

    A moving average can help reveal a trend by reducing short-term noise.
    """

    if window <= 0:
        raise ValueError("Window must be positive.")

    if window > len(values):
        raise ValueError("Window cannot exceed the number of observations.")

    return [
        mean(values[index - window + 1:index + 1])
        for index in range(window - 1, len(values))
    ]


def demonstrate_advanced_line_analysis() -> None:
    """Demonstrate smoothing and trend analysis."""

    print_section("ADVANCED LINE-CHART ANALYSIS")

    values = list(MONTHLY_SALES.values())
    averages = moving_average(values, 3)

    print("Three-month moving averages:")
    for index, average_value in enumerate(averages, start=3):
        month = list(MONTHLY_SALES)[index - 1]
        print(f"{month:>3}: {average_value:,.2f}")

    print(
        "\nA moving average is an analytical transformation, not merely a "
        "visual formatting feature. The original observations should remain "
        "available when the transformation could affect interpretation."
    )


# ---------------------------------------------------------------------------
# 15. Outlier detection
# ---------------------------------------------------------------------------

def detect_iqr_outliers(values: Sequence[float]) -> list[float]:
    """
    Detect outliers using the 1.5 × IQR rule.

    This is useful when inspecting distributions before building a histogram
    or scatter plot.
    """

    if len(values) < 4:
        return []

    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2

    if len(sorted_values) % 2 == 0:
        lower_half = sorted_values[:midpoint]
        upper_half = sorted_values[midpoint:]
    else:
        lower_half = sorted_values[:midpoint]
        upper_half = sorted_values[midpoint + 1:]

    q1 = median(lower_half)
    q3 = median(upper_half)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return [
        value
        for value in values
        if value < lower_bound or value > upper_bound
    ]


def demonstrate_outliers() -> None:
    """Show how outliers can affect visualization."""

    print_section("OUTLIERS")

    values = DELIVERY_TIMES + [95, 110]

    outliers = detect_iqr_outliers(values)

    print("Data:", values)
    print("Detected IQR outliers:", outliers)

    print(
        "\nAn outlier should not automatically be deleted. It may represent "
        "a legitimate rare observation, measurement error, data-entry error, "
        "or a meaningful operational event."
    )


# ---------------------------------------------------------------------------
# 16. Small statistical comparison
# ---------------------------------------------------------------------------

def coefficient_of_variation(values: Sequence[float]) -> float:
    """Calculate sample coefficient of variation as a percentage."""

    if len(values) < 2:
        return 0.0

    average = mean(values)

    if average == 0:
        raise ZeroDivisionError(
            "Coefficient of variation is undefined when the mean is zero."
        )

    return stdev(values) / average * 100


def demonstrate_statistical_context() -> None:
    """Show statistics that can inform chart interpretation."""

    print_section("STATISTICAL CONTEXT")

    statistics = inspect_numeric_data(DELIVERY_TIMES)
    cv = coefficient_of_variation(DELIVERY_TIMES)

    print(f"Mean: {statistics['mean']:.2f}")
    print(f"Median: {statistics['median']:.2f}")
    print(
        f"Standard deviation: "
        f"{statistics['sample_standard_deviation']:.2f}"
    )
    print(f"Coefficient of variation: {cv:.2f}%")

    print(
        "\nA histogram communicates distribution shape visually, while "
        "statistics provide numerical descriptions. They answer related "
        "questions and should not be treated as interchangeable."
    )


# ---------------------------------------------------------------------------
# 17. Accessibility and design validation
# ---------------------------------------------------------------------------

def chart_design_checklist(
    *,
    has_title: bool,
    has_axis_labels: bool,
    has_units: bool,
    has_legend_when_needed: bool,
    uses_3d_effect: bool,
    has_too_many_series: bool,
) -> list[str]:
    """Return design issues that should be reviewed before publication."""

    issues: list[str] = []

    if not has_title:
        issues.append("Add a descriptive chart title.")

    if not has_axis_labels:
        issues.append("Label axes when their meaning is not obvious.")

    if not has_units:
        issues.append("Specify units such as INR, USD, %, kg, or hours.")

    if not has_legend_when_needed:
        issues.append("Add a legend when multiple series require identification.")

    if uses_3d_effect:
        issues.append(
            "Review 3-D effects because perspective can distort perceived size."
        )

    if has_too_many_series:
        issues.append(
            "Reduce or reorganize series to preserve readability."
        )

    return issues


def demonstrate_design_review() -> None:
    """Demonstrate a pre-publication chart review."""

    print_section("CHART DESIGN REVIEW")

    issues = chart_design_checklist(
        has_title=True,
        has_axis_labels=False,
        has_units=False,
        has_legend_when_needed=True,
        uses_3d_effect=True,
        has_too_many_series=False,
    )

    for issue in issues:
        print(f"- {issue}")


# ---------------------------------------------------------------------------
# 18. Decision matrix
# ---------------------------------------------------------------------------

def print_decision_matrix() -> None:
    """Print a compact chart-selection reference."""

    print_section("CHART SELECTION DECISION MATRIX")

    matrix = [
        ("Compare categories", "Bar / Column", "Region, product, department"),
        ("Trend over time", "Line", "Monthly revenue"),
        ("Parts of one whole", "Pie / Bar", "Budget composition"),
        ("Two numerical variables", "Scatter", "Ad spend vs sales"),
        ("Distribution", "Histogram", "Delivery times"),
        ("Different measures/scales", "Combo", "Revenue + margin"),
    ]

    print(f"{'Question':<28} {'Chart':<18} {'Example'}")
    print("-" * 78)

    for question, chart, example in matrix:
        print(f"{question:<28} {chart:<18} {example}")


# ---------------------------------------------------------------------------
# 19. Common mistakes
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    """Print common Excel visualization errors and their implications."""

    print_section("COMMON MISTAKES")

    mistakes = {
        "Wrong chart for the question":
            "A visually attractive chart can still communicate the wrong analytical relationship.",
        "Pie chart with many categories":
            "Small slices become difficult to compare.",
        "Line chart for unordered categories":
            "Connecting unrelated categories implies continuity that does not exist.",
        "Dual axis without explanation":
            "Different scales can create misleading visual associations.",
        "Missing units":
            "The viewer may not know whether values represent INR, %, units, or another measure.",
        "Excessive decimal precision":
            "Unnecessary precision increases visual noise.",
        "3-D effects":
            "Perspective changes apparent area and length.",
        "Unsorted ranking":
            "Important high-to-low comparisons become harder to see.",
        "Ignoring missing values":
            "The chart may imply a complete dataset when observations are absent.",
        "Deleting outliers automatically":
            "Legitimate unusual events may disappear from analysis.",
    }

    for mistake, explanation in mistakes.items():
        print(f"\n{mistake}")
        print(f"  {explanation}")


# ---------------------------------------------------------------------------
# 20. Performance considerations
# ---------------------------------------------------------------------------

def estimate_visualization_work(
    row_count: int,
    series_count: int,
    category_count: int,
) -> str:
    """
    Provide a qualitative complexity warning.

    Excel charts can become difficult to render and interpret when datasets
    become very large. The exact practical threshold depends on Excel version,
    hardware, chart type, formulas, formatting, and workbook architecture.
    """

    if row_count <= 1000 and series_count <= 5 and category_count <= 30:
        return "Small: normally easy to inspect and manage."

    if row_count <= 10000 and series_count <= 10:
        return "Moderate: aggregation and filtering may improve usability."

    return (
        "Large: aggregate data, limit visible categories, avoid unnecessary "
        "markers, and consider whether every row needs to be plotted."
    )


def demonstrate_performance() -> None:
    """Show how dataset size affects chart design decisions."""

    print_section("PERFORMANCE")

    examples = [
        (500, 2, 12),
        (8000, 5, 50),
        (100000, 15, 500),
    ]

    for rows, series, categories in examples:
        result = estimate_visualization_work(rows, series, categories)
        print(
            f"Rows={rows:,}, Series={series}, Categories={categories}: "
            f"{result}"
        )


# ---------------------------------------------------------------------------
# 21. Reproducible analytical pipeline
# ---------------------------------------------------------------------------

def visualization_pipeline(
    raw_rows: list[dict[str, Any]],
    group_key: str,
    value_key: str,
) -> dict[str, Any]:
    """
    Model a practical visualization pipeline:

        raw data
            ↓
        validation
            ↓
        aggregation
            ↓
        descriptive statistics
            ↓
        chart selection
            ↓
        design review

    Keeping these stages separate makes analytical workflows easier to debug.
    """

    if not raw_rows:
        raise ValueError("No source records supplied.")

    aggregated = aggregate_sum(raw_rows, group_key, value_key)
    statistics = inspect_numeric_data(list(aggregated.values()))

    recommendation = recommend_chart(
        x_type=MeasurementType.CATEGORICAL,
        y_type=MeasurementType.CONTINUOUS_NUMERICAL,
        relationship=RelationshipType.COMPARISON,
        category_count=len(aggregated),
    )

    return {
        "aggregated": aggregated,
        "statistics": statistics,
        "chart": recommendation,
    }


def demonstrate_pipeline() -> None:
    """Run an end-to-end chart-preparation example."""

    print_section("END-TO-END VISUALIZATION PIPELINE")

    records = [
        {"department": "Engineering", "revenue": 250000},
        {"department": "Engineering", "revenue": 180000},
        {"department": "Sales", "revenue": 320000},
        {"department": "Sales", "revenue": 210000},
        {"department": "Finance", "revenue": 140000},
        {"department": "Operations", "revenue": 175000},
    ]

    result = visualization_pipeline(
        records,
        "department",
        "revenue",
    )

    print("Aggregated values:")
    print_dictionary(result["aggregated"])

    print("\nStatistics:")
    for key, value in result["statistics"].items():
        print(f"{key}: {value:.2f}")

    recommendation: ChartRecommendation = result["chart"]
    print(f"\nSelected chart: {recommendation.chart_type.value}")
    print(f"Reason: {recommendation.reason}")


# ---------------------------------------------------------------------------
# 22. Simulated categorical frequency chart
# ---------------------------------------------------------------------------

def demonstrate_frequency_analysis() -> None:
    """
    Show a frequency table.

    Frequency tables are often a useful intermediate representation before
    creating a bar chart or histogram.
    """

    print_section("FREQUENCY ANALYSIS")

    customer_ratings = [
        "Excellent", "Good", "Good", "Average", "Excellent",
        "Poor", "Good", "Excellent", "Average", "Good",
        "Excellent", "Poor", "Good", "Average", "Excellent",
    ]

    frequencies = Counter(customer_ratings)

    for rating, frequency in frequencies.most_common():
        print(f"{rating:>10}: {frequency}")

    print(
        "\nFor categorical ratings, a bar chart is generally more appropriate "
        "than a histogram because the categories are labels rather than "
        "continuous numerical intervals."
    )


# ---------------------------------------------------------------------------
# 23. Edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    """Demonstrate important exceptional inputs."""

    print_section("EDGE CASES")

    edge_cases: list[tuple[str, Callable[[], Any]]] = [
        (
            "Empty histogram",
            lambda: create_histogram_bins([]),
        ),
        (
            "Zero-total pie chart",
            lambda: calculate_percentages({"A": 0, "B": 0}),
        ),
        (
            "Mismatched scatter lengths",
            lambda: pearson_correlation([1, 2, 3], [4, 5]),
        ),
        (
            "Moving average larger than dataset",
            lambda: moving_average([1, 2, 3], 5),
        ),
    ]

    for description, operation in edge_cases:
        print(f"\n{description}:")
        try:
            result = operation()
            print("Result:", result)
        except (ValueError, TypeError, ZeroDivisionError) as error:
            print(f"Handled error: {error}")


# ---------------------------------------------------------------------------
# 24. Mini test suite
# ---------------------------------------------------------------------------

def run_tests() -> None:
    """Run lightweight assertions for important calculations."""

    print_section("SELF-TESTS")

    percentages = calculate_percentages({"A": 25, "B": 75})
    assert round(percentages["A"], 2) == 25.00
    assert round(percentages["B"], 2) == 75.00

    correlation = pearson_correlation([1, 2, 3], [2, 4, 6])
    assert round(correlation, 5) == 1.0

    averages = moving_average([10, 20, 30, 40], 2)
    assert averages == [15, 25, 35]

    histogram = create_histogram_bins([1, 2, 3, 4], 2)
    assert sum(item[2] for item in histogram) == 4

    recommendation = recommend_chart(
        x_type=MeasurementType.TIME,
        y_type=MeasurementType.CONTINUOUS_NUMERICAL,
        relationship=RelationshipType.TREND,
    )
    assert recommendation.chart_type == ChartType.LINE

    print("All self-tests passed.")


# ---------------------------------------------------------------------------
# 25. Main study program
# ---------------------------------------------------------------------------

def main() -> None:
    """Execute the complete educational demonstration."""

    print_section("EXCEL DATA VISUALIZATION")
    print("Topic: Bar charts, line charts, pie charts, scatter plots,")
    print("combo charts, histograms, and chart selection principles.")

    demonstrate_bar_chart()
    demonstrate_line_chart()
    demonstrate_pie_chart()
    demonstrate_scatter_plot()
    demonstrate_histogram()
    demonstrate_combo_chart()
    demonstrate_chart_selection()
    demonstrate_validation()
    demonstrate_axis_effect()
    demonstrate_aggregation()
    demonstrate_advanced_line_analysis()
    demonstrate_outliers()
    demonstrate_statistical_context()
    demonstrate_design_review()
    print_decision_matrix()
    demonstrate_common_mistakes()
    demonstrate_performance()
    demonstrate_pipeline()
    demonstrate_frequency_analysis()
    demonstrate_edge_cases()
    run_tests()

    print_section("REFERENCE PRINCIPLES")
    principles = [
        "Start with the analytical question, not the chart type.",
        "Compare categories with bars or columns.",
        "Show ordered trends with lines.",
        "Use pie charts only for simple part-to-whole situations.",
        "Use scatter plots for relationships between numerical variables.",
        "Use histograms for numerical distributions.",
        "Use combo charts when related measures require different visual forms.",
        "Prepare and validate data before chart creation.",
        "Label axes, units, legends, and titles clearly.",
        "Inspect outliers and missing values rather than silently removing them.",
        "Avoid visual effects that distort quantitative comparison.",
        "Treat secondary axes carefully and label them explicitly.",
        "Keep the visualization proportional to the analytical question.",
    ]

    for number, principle in enumerate(principles, start=1):
        print(f"{number:02}. {principle}")


if __name__ == "__main__":
    main()
