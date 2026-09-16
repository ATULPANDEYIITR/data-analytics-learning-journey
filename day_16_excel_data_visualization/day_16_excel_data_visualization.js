/*
 * Excel Data Visualization
 * =========================
 *
 * A self-contained JavaScript study program covering:
 *
 * - Bar and column charts
 * - Line charts
 * - Pie charts
 * - Scatter plots
 * - Combo charts
 * - Histograms
 * - Chart selection
 * - Data preparation
 * - Aggregation
 * - Correlation
 * - Distribution analysis
 * - Axis scaling
 * - Validation
 * - Accessibility
 * - Performance
 * - Edge cases
 *
 * The program uses standard JavaScript and requires no external packages.
 * It models the analytical decisions that precede creation of equivalent
 * Excel visualizations.
 *
 * It can run in Node.js.
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. Basic datasets
// -----------------------------------------------------------------------------

const salesByRegion = {
    North: 185000,
    South: 142000,
    East: 163000,
    West: 211000
};

const monthlySales = {
    Jan: 98000,
    Feb: 104000,
    Mar: 112000,
    Apr: 109000,
    May: 121000,
    Jun: 135000,
    Jul: 129000,
    Aug: 143000,
    Sep: 151000,
    Oct: 147000,
    Nov: 166000,
    Dec: 182000
};

const advertisingSpend = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55];

const advertisingSales = [
    112, 118, 125, 131, 139,
    146, 153, 162, 171, 181
];

const deliveryTimes = [
    18, 21, 25, 19, 32, 28, 22, 31, 26, 35,
    40, 37, 29, 23, 21, 34, 27, 25, 30, 33,
    38, 42, 45, 24, 20, 19, 28, 31, 36, 41
];

const expensesByCategory = {
    Salaries: 420000,
    Marketing: 90000,
    Technology: 135000,
    Operations: 75000,
    Travel: 30000
};

const monthlyRevenue = {
    Jan: 1200000,
    Feb: 1320000,
    Mar: 1410000,
    Apr: 1380000,
    May: 1530000,
    Jun: 1680000
};

const monthlyProfitMargin = {
    Jan: 0.12,
    Feb: 0.135,
    Mar: 0.141,
    Apr: 0.128,
    May: 0.152,
    Jun: 0.161
};


// -----------------------------------------------------------------------------
// 2. Utility functions
// -----------------------------------------------------------------------------

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function valuesOf(object) {
    return Object.values(object);
}

function sum(values) {
    return values.reduce((total, value) => total + value, 0);
}

function average(values) {
    if (values.length === 0) {
        throw new Error("Cannot calculate an average of an empty array.");
    }

    return sum(values) / values.length;
}

function median(values) {
    if (values.length === 0) {
        throw new Error("Cannot calculate the median of an empty array.");
    }

    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];
}

function formatNumber(value) {
    return value.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}


// -----------------------------------------------------------------------------
// 3. Bar chart
// -----------------------------------------------------------------------------

function demonstrateBarChart() {
    section("BAR / COLUMN CHART");

    console.log("Purpose: compare values across discrete categories.\n");

    const maximum = Math.max(...valuesOf(salesByRegion));

    for (const [region, sales] of Object.entries(salesByRegion)) {
        const length = Math.round((sales / maximum) * 40);

        console.log(
            `${region.padEnd(8)} | ${"█".repeat(length)} ${formatNumber(sales)}`
        );
    }

    console.log("\nInterpretation:");
    console.log(
        "Bars allow the viewer to compare category magnitudes using a common scale."
    );

    console.log("\nImportant rule:");
    console.log(
        "Vertical columns and horizontal bars belong to the same basic comparison family."
    );
}


// -----------------------------------------------------------------------------
// 4. Line chart
// -----------------------------------------------------------------------------

function demonstrateLineChart() {
    section("LINE CHART");

    console.log("Purpose: show change across an ordered dimension, especially time.\n");

    const values = valuesOf(monthlySales);
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);

    for (const [month, value] of Object.entries(monthlySales)) {
        const position = maximum === minimum
            ? 0
            : Math.round(((value - minimum) / (maximum - minimum)) * 40);

        console.log(
            `${month.padStart(3)} ${" ".repeat(position)}● ${formatNumber(value)}`
        );
    }

    const growth = (
        (values[values.length - 1] - values[0]) /
        values[0]
    ) * 100;

    console.log(`\nJanuary-to-December change: ${growth.toFixed(2)}%`);

    console.log(
        "\nA line implies an ordered progression. It is therefore appropriate "
        + "for months, dates, years, or another meaningful sequence."
    );
}


// -----------------------------------------------------------------------------
// 5. Pie chart
// -----------------------------------------------------------------------------

function calculatePercentages(data) {
    const total = sum(valuesOf(data));

    if (total <= 0) {
        throw new Error("Pie-chart total must be positive.");
    }

    return Object.fromEntries(
        Object.entries(data).map(([category, value]) => [
            category,
            (value / total) * 100
        ])
    );
}

function demonstratePieChart() {
    section("PIE CHART");

    const percentages = calculatePercentages(expensesByCategory);

    console.log("Purpose: show parts of a single whole.\n");

    for (const [category, percentage] of Object.entries(percentages)) {
        console.log(`${category.padEnd(15)} ${percentage.toFixed(2)}%`);
    }

    console.log("\nDesign constraints:");
    console.log("- Categories must represent components of one total.");
    console.log("- Too many slices reduce readability.");
    console.log("- Similar-sized slices are difficult to compare precisely.");
    console.log("- A bar chart can be clearer when exact comparison matters.");
}


// -----------------------------------------------------------------------------
// 6. Scatter plot and correlation
// -----------------------------------------------------------------------------

function pearsonCorrelation(x, y) {
    if (x.length !== y.length) {
        throw new Error("Both variables must contain the same number of observations.");
    }

    if (x.length < 2) {
        throw new Error("At least two observations are required.");
    }

    const xMean = average(x);
    const yMean = average(y);

    let numerator = 0;
    let xVariance = 0;
    let yVariance = 0;

    for (let index = 0; index < x.length; index++) {
        const xDifference = x[index] - xMean;
        const yDifference = y[index] - yMean;

        numerator += xDifference * yDifference;
        xVariance += xDifference ** 2;
        yVariance += yDifference ** 2;
    }

    const denominator = Math.sqrt(xVariance * yVariance);

    return denominator === 0 ? 0 : numerator / denominator;
}

function demonstrateScatterPlot() {
    section("SCATTER PLOT");

    const correlation = pearsonCorrelation(
        advertisingSpend,
        advertisingSales
    );

    console.log("Advertising spend and sales:\n");
    console.log("Spend\tSales");

    advertisingSpend.forEach((spend, index) => {
        console.log(`${spend}\t${advertisingSales[index]}`);
    });

    console.log(`\nPearson correlation: ${correlation.toFixed(4)}`);

    console.log(
        "\nThe scatter plot is used to inspect association, clusters, "
        + "outliers, and possible nonlinear patterns."
    );

    console.log(
        "Correlation measures linear association and does not establish causation."
    );
}


// -----------------------------------------------------------------------------
// 7. Histogram
// -----------------------------------------------------------------------------

function createHistogram(values, binCount) {
    if (values.length === 0) {
        throw new Error("Histogram input cannot be empty.");
    }

    if (!Number.isInteger(binCount) || binCount <= 0) {
        throw new Error("Bin count must be a positive integer.");
    }

    const minimum = Math.min(...values);
    const maximum = Math.max(...values);

    if (minimum === maximum) {
        return [{
            lower: minimum,
            upper: maximum,
            count: values.length
        }];
    }

    const width = (maximum - minimum) / binCount;
    const bins = [];

    for (let index = 0; index < binCount; index++) {
        const lower = minimum + index * width;
        const upper = index === binCount - 1
            ? maximum
            : minimum + (index + 1) * width;

        const count = values.filter((value) => {
            const belongsToRange =
                value >= lower && value < upper;

            const isFinalEndpoint =
                index === binCount - 1 && value === upper;

            return belongsToRange || isFinalEndpoint;
        }).length;

        bins.push({ lower, upper, count });
    }

    return bins;
}

function demonstrateHistogram() {
    section("HISTOGRAM");

    const bins = createHistogram(deliveryTimes, 6);
    const maximumFrequency = Math.max(...bins.map((bin) => bin.count));

    console.log("Delivery-time distribution:\n");

    for (const bin of bins) {
        const length = maximumFrequency === 0
            ? 0
            : Math.round((bin.count / maximumFrequency) * 40);

        console.log(
            `${bin.lower.toFixed(1).padStart(5)} - `
            + `${bin.upper.toFixed(1).padStart(5)} | `
            + `${"█".repeat(length)} ${bin.count}`
        );
    }

    console.log(
        "\nHistogram bars represent numerical intervals. "
        + "Bin width affects the apparent shape of the distribution."
    );
}


// -----------------------------------------------------------------------------
// 8. Combo chart
// -----------------------------------------------------------------------------

function demonstrateComboChart() {
    section("COMBO CHART");

    console.log("Revenue and profit margin use different units.\n");

    console.log("Month\tRevenue\t\tMargin");

    for (const month of Object.keys(monthlyRevenue)) {
        console.log(
            `${month}\t`
            + `${formatNumber(monthlyRevenue[month])}\t`
            + `${(monthlyProfitMargin[month] * 100).toFixed(2)}%`
        );
    }

    console.log("\nTypical Excel design:");
    console.log("- Revenue -> column series.");
    console.log("- Profit margin -> line series.");
    console.log("- Revenue -> primary axis.");
    console.log("- Profit margin -> secondary axis.");

    console.log(
        "\nSecondary axes are useful when units differ, but the two axes "
        + "must be clearly labeled to prevent visual misinterpretation."
    );
}


// -----------------------------------------------------------------------------
// 9. Chart selection
// -----------------------------------------------------------------------------

const ChartType = Object.freeze({
    BAR: "Bar / Column Chart",
    LINE: "Line Chart",
    PIE: "Pie Chart",
    SCATTER: "Scatter Plot",
    COMBO: "Combo Chart",
    HISTOGRAM: "Histogram"
});

function recommendChart({
    analyticalQuestion,
    categoryCount = 0,
    seriesCount = 1,
    hasTimeAxis = false,
    twoNumericVariables = false,
    partsOfWhole = false,
    differentScales = false
}) {
    const warnings = [];

    if (analyticalQuestion === "comparison") {
        if (categoryCount > 20) {
            warnings.push(
                "Many categories may require filtering or aggregation."
            );
        }

        return {
            chart: ChartType.BAR,
            reason: "The task is comparison across categories.",
            warnings
        };
    }

    if (analyticalQuestion === "trend" && hasTimeAxis) {
        if (seriesCount > 5) {
            warnings.push("Too many lines can make the chart difficult to read.");
        }

        return {
            chart: ChartType.LINE,
            reason: "An ordered time axis is suitable for a line chart.",
            warnings
        };
    }

    if (analyticalQuestion === "composition" && partsOfWhole) {
        if (categoryCount <= 7) {
            return {
                chart: ChartType.PIE,
                reason: "A small number of categories represent one whole.",
                warnings
            };
        }

        warnings.push("Many slices reduce pie-chart readability.");

        return {
            chart: ChartType.BAR,
            reason: "Bars make component comparison easier.",
            warnings
        };
    }

    if (analyticalQuestion === "relationship" && twoNumericVariables) {
        return {
            chart: ChartType.SCATTER,
            reason: "Two numerical variables are being compared for association.",
            warnings
        };
    }

    if (analyticalQuestion === "distribution") {
        return {
            chart: ChartType.HISTOGRAM,
            reason: "The task is to examine the distribution of numerical data.",
            warnings
        };
    }

    if (analyticalQuestion === "mixed" && differentScales) {
        warnings.push(
            "Label primary and secondary axes explicitly."
        );

        return {
            chart: ChartType.COMBO,
            reason: "Different measures need different visual forms or scales.",
            warnings
        };
    }

    return {
        chart: ChartType.BAR,
        reason: "Bar charts are a practical default for simple comparisons.",
        warnings
    };
}

function demonstrateChartSelection() {
    section("CHART SELECTION");

    const scenarios = [
        {
            name: "Regional comparison",
            analyticalQuestion: "comparison",
            categoryCount: 4
        },
        {
            name: "Monthly sales trend",
            analyticalQuestion: "trend",
            hasTimeAxis: true
        },
        {
            name: "Budget composition",
            analyticalQuestion: "composition",
            categoryCount: 5,
            partsOfWhole: true
        },
        {
            name: "Advertising relationship",
            analyticalQuestion: "relationship",
            twoNumericVariables: true
        },
        {
            name: "Delivery-time distribution",
            analyticalQuestion: "distribution"
        },
        {
            name: "Revenue and margin",
            analyticalQuestion: "mixed",
            differentScales: true
        }
    ];

    for (const scenario of scenarios) {
        const recommendation = recommendChart(scenario);

        console.log(`\n${scenario.name}`);
        console.log(`Chart: ${recommendation.chart}`);
        console.log(`Reason: ${recommendation.reason}`);

        for (const warning of recommendation.warnings) {
            console.log(`Warning: ${warning}`);
        }
    }
}


// -----------------------------------------------------------------------------
// 10. Data aggregation
// -----------------------------------------------------------------------------

function aggregateBy(rows, groupKey, valueKey) {
    const result = new Map();

    for (const row of rows) {
        const group = row[groupKey];
        const value = row[valueKey];

        if (typeof value !== "number" || Number.isNaN(value)) {
            throw new TypeError(`Non-numeric value: ${value}`);
        }

        result.set(
            group,
            (result.get(group) ?? 0) + value
        );
    }

    return Object.fromEntries(result);
}

function demonstrateAggregation() {
    section("AGGREGATION");

    const transactions = [
        { region: "North", sales: 1200 },
        { region: "North", sales: 800 },
        { region: "South", sales: 900 },
        { region: "South", sales: 1100 },
        { region: "East", sales: 1500 },
        { region: "West", sales: 1700 },
        { region: "West", sales: 600 }
    ];

    const totals = aggregateBy(
        transactions,
        "region",
        "sales"
    );

    console.log("Aggregated chart-ready values:");

    for (const [region, value] of Object.entries(totals)) {
        console.log(`${region.padEnd(8)} ${formatNumber(value)}`);
    }
}


// -----------------------------------------------------------------------------
// 11. Moving averages
// -----------------------------------------------------------------------------

function movingAverage(values, windowSize) {
    if (windowSize <= 0) {
        throw new Error("Window size must be positive.");
    }

    if (windowSize > values.length) {
        throw new Error("Window cannot exceed data length.");
    }

    const result = [];

    for (let index = windowSize - 1; index < values.length; index++) {
        const window = values.slice(
            index - windowSize + 1,
            index + 1
        );

        result.push(average(window));
    }

    return result;
}

function demonstrateMovingAverage() {
    section("MOVING AVERAGE");

    const averages = movingAverage(
        valuesOf(monthlySales),
        3
    );

    averages.forEach((value, index) => {
        const month = Object.keys(monthlySales)[index + 2];

        console.log(
            `${month}: ${formatNumber(value)}`
        );
    });

    console.log(
        "\nA moving average can reduce short-term variation and make a trend "
        + "easier to inspect. It should not replace the original observations."
    );
}


// -----------------------------------------------------------------------------
// 12. Outlier detection
// -----------------------------------------------------------------------------

function detectIqrOutliers(values) {
    if (values.length < 4) {
        return [];
    }

    const sorted = [...values].sort((a, b) => a - b);
    const midpoint = Math.floor(sorted.length / 2);

    const lowerHalf = sorted.slice(0, midpoint);
    const upperHalf = sorted.length % 2 === 0
        ? sorted.slice(midpoint)
        : sorted.slice(midpoint + 1);

    const q1 = median(lowerHalf);
    const q3 = median(upperHalf);
    const iqr = q3 - q1;

    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;

    return values.filter(
        value => value < lowerBound || value > upperBound
    );
}

function demonstrateOutliers() {
    section("OUTLIERS");

    const data = [...deliveryTimes, 95, 110];
    const outliers = detectIqrOutliers(data);

    console.log("Detected outliers:", outliers);

    console.log(
        "\nAn outlier may be an error, a rare legitimate event, or an "
        + "important business signal. Visualization should help investigate it."
    );
}


// -----------------------------------------------------------------------------
// 13. Axis and design checks
// -----------------------------------------------------------------------------

function designReview({
    title,
    axisLabels,
    units,
    legendWhenNeeded,
    threeDEffect,
    tooManySeries
}) {
    const issues = [];

    if (!title) {
        issues.push("Missing descriptive title.");
    }

    if (!axisLabels) {
        issues.push("Axes should be labeled where necessary.");
    }

    if (!units) {
        issues.push("Measurement units should be specified.");
    }

    if (!legendWhenNeeded) {
        issues.push("A legend is required when multiple series need identification.");
    }

    if (threeDEffect) {
        issues.push("Review 3-D effects because perspective can distort magnitude.");
    }

    if (tooManySeries) {
        issues.push("Reduce or reorganize series to preserve readability.");
    }

    return issues;
}

function demonstrateDesignReview() {
    section("DESIGN REVIEW");

    const issues = designReview({
        title: true,
        axisLabels: false,
        units: false,
        legendWhenNeeded: true,
        threeDEffect: true,
        tooManySeries: false
    });

    issues.forEach(issue => console.log(`- ${issue}`));
}


// -----------------------------------------------------------------------------
// 14. Frequency table
// -----------------------------------------------------------------------------

function frequencyTable(values) {
    const counts = new Map();

    for (const value of values) {
        counts.set(value, (counts.get(value) ?? 0) + 1);
    }

    return [...counts.entries()]
        .sort((a, b) => b[1] - a[1]);
}

function demonstrateFrequencyTable() {
    section("CATEGORICAL FREQUENCY ANALYSIS");

    const ratings = [
        "Excellent", "Good", "Good", "Average", "Excellent",
        "Poor", "Good", "Excellent", "Average", "Good",
        "Excellent", "Poor", "Good", "Average", "Excellent"
    ];

    for (const [rating, count] of frequencyTable(ratings)) {
        console.log(`${rating.padEnd(10)} ${count}`);
    }

    console.log(
        "\nCategorical frequency data is naturally suited to a bar chart. "
        + "A histogram is designed for numerical intervals."
    );
}


// -----------------------------------------------------------------------------
// 15. Validation
// -----------------------------------------------------------------------------

function validatePieData(data) {
    const errors = [];
    const values = Object.values(data);

    if (values.length === 0) {
        errors.push("Dataset is empty.");
    }

    for (const [category, value] of Object.entries(data)) {
        if (typeof value !== "number" || Number.isNaN(value)) {
            errors.push(`${category}: value is not numeric.`);
        }

        if (value < 0) {
            errors.push(`${category}: negative values are invalid for ordinary pie slices.`);
        }
    }

    if (sum(values) <= 0) {
        errors.push("Pie-chart total must be positive.");
    }

    return errors;
}

function demonstrateValidation() {
    section("VALIDATION");

    const invalid = {
        A: 30,
        B: -10,
        C: Number.NaN
    };

    const errors = validatePieData(invalid);

    errors.forEach(error => console.log(`- ${error}`));
}


// -----------------------------------------------------------------------------
// 16. Edge cases
// -----------------------------------------------------------------------------

function demonstrateEdgeCases() {
    section("EDGE CASES");

    const tests = [
        {
            name: "Empty histogram",
            run: () => createHistogram([], 5)
        },
        {
            name: "Zero-total pie chart",
            run: () => calculatePercentages({ A: 0, B: 0 })
        },
        {
            name: "Mismatched scatter arrays",
            run: () => pearsonCorrelation([1, 2], [3])
        },
        {
            name: "Moving average larger than dataset",
            run: () => movingAverage([1, 2, 3], 5)
        }
    ];

    for (const test of tests) {
        try {
            test.run();
            console.log(`${test.name}: unexpectedly succeeded`);
        } catch (error) {
            console.log(`${test.name}: handled -> ${error.message}`);
        }
    }
}


// -----------------------------------------------------------------------------
// 17. Performance reasoning
// -----------------------------------------------------------------------------

function estimateVisualizationComplexity(
    rowCount,
    seriesCount,
    categoryCount
) {
    if (
        rowCount <= 1000 &&
        seriesCount <= 5 &&
        categoryCount <= 30
    ) {
        return "Small dataset: usually easy to manage.";
    }

    if (
        rowCount <= 10000 &&
        seriesCount <= 10
    ) {
        return "Moderate dataset: aggregation and filtering may improve usability.";
    }

    return (
        "Large dataset: aggregate, filter, or otherwise reduce visual "
        + "complexity before plotting everything."
    );
}

function demonstratePerformance() {
    section("PERFORMANCE");

    const examples = [
        [500, 2, 12],
        [8000, 5, 50],
        [100000, 15, 500]
    ];

    for (const [rows, series, categories] of examples) {
        console.log(
            `Rows=${rows}, Series=${series}, Categories=${categories}: `
            + estimateVisualizationComplexity(rows, series, categories)
        );
    }
}


// -----------------------------------------------------------------------------
// 18. Mini test suite
// -----------------------------------------------------------------------------

function runTests() {
    section("SELF-TESTS");

    const percentages = calculatePercentages({
        A: 25,
        B: 75
    });

    console.assert(
        Math.round(percentages.A) === 25,
        "Percentage calculation failed."
    );

    console.assert(
        Math.round(percentages.B) === 75,
        "Percentage calculation failed."
    );

    const correlation = pearsonCorrelation(
        [1, 2, 3],
        [2, 4, 6]
    );

    console.assert(
        Math.round(correlation * 1000) / 1000 === 1,
        "Correlation calculation failed."
    );

    const averages = movingAverage(
        [10, 20, 30, 40],
        2
    );

    console.assert(
        JSON.stringify(averages) === JSON.stringify([15, 25, 35]),
        "Moving-average calculation failed."
    );

    const recommendation = recommendChart({
        analyticalQuestion: "trend",
        hasTimeAxis: true
    });

    console.assert(
        recommendation.chart === ChartType.LINE,
        "Chart recommendation failed."
    );

    console.log("Self-tests completed.");
}


// -----------------------------------------------------------------------------
// 19. Main program
// -----------------------------------------------------------------------------

function main() {
    section("EXCEL DATA VISUALIZATION");

    console.log(
        "Bar charts, line charts, pie charts, scatter plots, combo charts, "
        + "histograms, and chart selection principles."
    );

    demonstrateBarChart();
    demonstrateLineChart();
    demonstratePieChart();
    demonstrateScatterPlot();
    demonstrateHistogram();
    demonstrateComboChart();
    demonstrateChartSelection();
    demonstrateAggregation();
    demonstrateMovingAverage();
    demonstrateOutliers();
    demonstrateDesignReview();
    demonstrateFrequencyTable();
    demonstrateValidation();
    demonstrateEdgeCases();
    demonstratePerformance();
    runTests();

    section("CHART SELECTION REFERENCE");

    console.log("Comparison       -> Bar / Column");
    console.log("Time trend       -> Line");
    console.log("Part of whole    -> Pie or Bar");
    console.log("Relationship     -> Scatter");
    console.log("Distribution     -> Histogram");
    console.log("Mixed measures   -> Combo");

    console.log(
        "\nThe analytical question should determine the chart type. "
        + "Formatting should support the message rather than replace it."
    );
}

main();
