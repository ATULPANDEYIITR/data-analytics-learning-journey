/*
 * Excel Data Visualization
 * =========================
 *
 * Industry-style C++ case study:
 *
 * A sales analytics engine receives transaction records and prepares
 * chart-ready datasets. It classifies analytical questions and recommends
 * an appropriate Excel visualization:
 *
 *   - Bar / Column Chart
 *   - Line Chart
 *   - Pie Chart
 *   - Scatter Plot
 *   - Combo Chart
 *   - Histogram
 *
 * The program demonstrates:
 *
 *   - Structures and classes
 *   - Encapsulation
 *   - STL containers
 *   - Data validation
 *   - Aggregation
 *   - Statistical calculations
 *   - Correlation
 *   - Histogram construction
 *   - Chart-selection rules
 *   - Outlier detection
 *   - Moving averages
 *   - Design validation
 *   - Error handling
 *   - Complexity considerations
 *   - A complete analytical workflow
 *
 * Compile with:
 *   g++ -std=c++17 -O2 visualization_case_study.cpp -o visualization_case_study
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// 1. Core domain types
// -----------------------------------------------------------------------------

enum class ChartType {
    BarColumn,
    Line,
    Pie,
    Scatter,
    Combo,
    Histogram
};

enum class QuestionType {
    Comparison,
    Trend,
    Composition,
    Relationship,
    Distribution,
    Mixed
};

string chartTypeToString(ChartType type) {
    switch (type) {
        case ChartType::BarColumn:
            return "Bar / Column Chart";
        case ChartType::Line:
            return "Line Chart";
        case ChartType::Pie:
            return "Pie Chart";
        case ChartType::Scatter:
            return "Scatter Plot";
        case ChartType::Combo:
            return "Combo Chart";
        case ChartType::Histogram:
            return "Histogram";
    }

    return "Unknown";
}

string questionTypeToString(QuestionType type) {
    switch (type) {
        case QuestionType::Comparison:
            return "Comparison";
        case QuestionType::Trend:
            return "Trend";
        case QuestionType::Composition:
            return "Composition";
        case QuestionType::Relationship:
            return "Relationship";
        case QuestionType::Distribution:
            return "Distribution";
        case QuestionType::Mixed:
            return "Mixed";
    }

    return "Unknown";
}


// -----------------------------------------------------------------------------
// 2. Data models
// -----------------------------------------------------------------------------

struct SalesRecord {
    string month;
    string region;
    string product;
    double revenue;
    double advertisingSpend;
    double deliveryTime;
};

struct ChartRecommendation {
    ChartType type;
    string reason;
    vector<string> warnings;
};

struct HistogramBin {
    double lower;
    double upper;
    size_t frequency;
};


// -----------------------------------------------------------------------------
// 3. Utility functions
// -----------------------------------------------------------------------------

void printSection(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

string formatNumber(double value, int precision = 2) {
    ostringstream output;
    output << fixed << setprecision(precision) << value;
    return output.str();
}

double mean(const vector<double>& values) {
    if (values.empty()) {
        throw invalid_argument("Mean cannot be calculated for empty data.");
    }

    return accumulate(values.begin(), values.end(), 0.0)
        / static_cast<double>(values.size());
}

double sampleStandardDeviation(const vector<double>& values) {
    if (values.size() < 2) {
        return 0.0;
    }

    const double average = mean(values);

    double squaredDifferenceSum = 0.0;

    for (double value : values) {
        squaredDifferenceSum += pow(value - average, 2);
    }

    return sqrt(
        squaredDifferenceSum /
        static_cast<double>(values.size() - 1)
    );
}


// -----------------------------------------------------------------------------
// 4. Analytics engine
// -----------------------------------------------------------------------------

class VisualizationAnalytics {
public:

    /*
     * Aggregate revenue by region.
     *
     * std::map provides deterministic alphabetical ordering, which is useful
     * when generating reproducible reports.
     *
     * Complexity:
     * O(n log k), where n is the number of records and k is the number of
     * unique regions.
     */
    static map<string, double> aggregateRevenueByRegion(
        const vector<SalesRecord>& records
    ) {
        map<string, double> totals;

        for (const auto& record : records) {
            validateRecord(record);
            totals[record.region] += record.revenue;
        }

        return totals;
    }

    /*
     * Aggregate revenue by month.
     *
     * In production, chronological ordering should use an explicit calendar
     * index rather than relying on alphabetic ordering of month names.
     */
    static map<string, double> aggregateRevenueByMonth(
        const vector<SalesRecord>& records
    ) {
        map<string, double> totals;

        for (const auto& record : records) {
            validateRecord(record);
            totals[record.month] += record.revenue;
        }

        return totals;
    }

    /*
     * Extract advertising spend and revenue pairs.
     *
     * This produces the two numerical dimensions needed for a scatter plot.
     */
    static pair<vector<double>, vector<double>> advertisingRelationship(
        const vector<SalesRecord>& records
    ) {
        vector<double> spend;
        vector<double> revenue;

        for (const auto& record : records) {
            validateRecord(record);
            spend.push_back(record.advertisingSpend);
            revenue.push_back(record.revenue);
        }

        return {spend, revenue};
    }

    static double pearsonCorrelation(
        const vector<double>& x,
        const vector<double>& y
    ) {
        if (x.size() != y.size()) {
            throw invalid_argument(
                "Scatter variables must contain equal observation counts."
            );
        }

        if (x.size() < 2) {
            throw invalid_argument(
                "At least two observations are required."
            );
        }

        const double xMean = mean(x);
        const double yMean = mean(y);

        double numerator = 0.0;
        double xSquaredDifference = 0.0;
        double ySquaredDifference = 0.0;

        for (size_t i = 0; i < x.size(); ++i) {
            const double xDifference = x[i] - xMean;
            const double yDifference = y[i] - yMean;

            numerator += xDifference * yDifference;
            xSquaredDifference += xDifference * xDifference;
            ySquaredDifference += yDifference * yDifference;
        }

        const double denominator =
            sqrt(xSquaredDifference * ySquaredDifference);

        if (denominator == 0.0) {
            return 0.0;
        }

        return numerator / denominator;
    }

    /*
     * Construct equal-width histogram bins.
     *
     * Complexity:
     * O(n * b), where n is the number of observations and b is the number
     * of bins. For small business datasets this is simple and transparent.
     */
    static vector<HistogramBin> histogram(
        const vector<double>& values,
        size_t binCount
    ) {
        if (values.empty()) {
            throw invalid_argument(
                "Cannot build a histogram from empty data."
            );
        }

        if (binCount == 0) {
            throw invalid_argument(
                "Histogram must contain at least one bin."
            );
        }

        const auto [minimumIterator, maximumIterator] =
            minmax_element(values.begin(), values.end());

        const double minimum = *minimumIterator;
        const double maximum = *maximumIterator;

        if (minimum == maximum) {
            return {{minimum, maximum, values.size()}};
        }

        const double width =
            (maximum - minimum) /
            static_cast<double>(binCount);

        vector<HistogramBin> bins;

        for (size_t index = 0; index < binCount; ++index) {
            const double lower =
                minimum + static_cast<double>(index) * width;

            const double upper =
                index == binCount - 1
                    ? maximum
                    : minimum + static_cast<double>(index + 1) * width;

            size_t frequency = 0;

            for (double value : values) {
                const bool inNormalRange =
                    value >= lower && value < upper;

                const bool isFinalEndpoint =
                    index == binCount - 1 && value == upper;

                if (inNormalRange || isFinalEndpoint) {
                    ++frequency;
                }
            }

            bins.push_back({lower, upper, frequency});
        }

        return bins;
    }

    /*
     * Three-period moving average.
     *
     * Complexity: O(n * window).
     *
     * For a fixed small window, this is effectively linear. A production
     * implementation for very large data could use a rolling sum to achieve
     * O(n) independent of window size.
     */
    static vector<double> movingAverage(
        const vector<double>& values,
        size_t window
    ) {
        if (window == 0) {
            throw invalid_argument(
                "Moving-average window must be positive."
            );
        }

        if (window > values.size()) {
            throw invalid_argument(
                "Moving-average window exceeds dataset size."
            );
        }

        vector<double> result;

        for (size_t i = window - 1; i < values.size(); ++i) {
            double windowSum = 0.0;

            for (size_t j = i + 1 - window; j <= i; ++j) {
                windowSum += values[j];
            }

            result.push_back(
                windowSum / static_cast<double>(window)
            );
        }

        return result;
    }

    /*
     * IQR-based outlier detection.
     *
     * The 1.5 × IQR rule is a screening method rather than proof that a
     * record is erroneous.
     */
    static vector<double> detectOutliers(
        vector<double> values
    ) {
        if (values.size() < 4) {
            return {};
        }

        sort(values.begin(), values.end());

        const size_t middle = values.size() / 2;

        vector<double> lowerHalf(
            values.begin(),
            values.begin() + middle
        );

        vector<double> upperHalf;

        if (values.size() % 2 == 0) {
            upperHalf.assign(
                values.begin() + middle,
                values.end()
            );
        } else {
            upperHalf.assign(
                values.begin() + middle + 1,
                values.end()
            );
        }

        const double q1 = median(lowerHalf);
        const double q3 = median(upperHalf);
        const double iqr = q3 - q1;

        const double lowerBound = q1 - 1.5 * iqr;
        const double upperBound = q3 + 1.5 * iqr;

        vector<double> outliers;

        for (double value : values) {
            if (value < lowerBound || value > upperBound) {
                outliers.push_back(value);
            }
        }

        return outliers;
    }

    static double median(vector<double> values) {
        if (values.empty()) {
            throw invalid_argument(
                "Median cannot be calculated for empty data."
            );
        }

        sort(values.begin(), values.end());

        const size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (
                values[middle - 1] +
                values[middle]
            ) / 2.0;
        }

        return values[middle];
    }

    static ChartRecommendation recommendChart(
        QuestionType question,
        size_t categoryCount = 0,
        size_t seriesCount = 1,
        bool partsOfWhole = false,
        bool hasTimeAxis = false,
        bool hasTwoNumericVariables = false,
        bool differentScales = false
    ) {
        vector<string> warnings;

        switch (question) {
            case QuestionType::Comparison:
                if (categoryCount > 20) {
                    warnings.push_back(
                        "Many categories may require filtering or aggregation."
                    );
                }

                return {
                    ChartType::BarColumn,
                    "The primary task is comparison across categories.",
                    warnings
                };

            case QuestionType::Trend:
                if (hasTimeAxis) {
                    if (seriesCount > 5) {
                        warnings.push_back(
                            "Many line series can reduce readability."
                        );
                    }

                    return {
                        ChartType::Line,
                        "An ordered time axis supports a line chart.",
                        warnings
                    };
                }

                return {
                    ChartType::BarColumn,
                    "Without an ordered time axis, category comparison is clearer.",
                    warnings
                };

            case QuestionType::Composition:
                if (partsOfWhole && categoryCount <= 7) {
                    return {
                        ChartType::Pie,
                        "A small number of categories represent one whole.",
                        warnings
                    };
                }

                warnings.push_back(
                    "Many composition categories make pie slices difficult to compare."
                );

                return {
                    ChartType::BarColumn,
                    "Bars provide clearer component-size comparison.",
                    warnings
                };

            case QuestionType::Relationship:
                if (hasTwoNumericVariables) {
                    return {
                        ChartType::Scatter,
                        "Two numerical variables are being examined for association.",
                        warnings
                    };
                }

                return {
                    ChartType::BarColumn,
                    "Numerical relationship data was not sufficiently specified.",
                    warnings
                };

            case QuestionType::Distribution:
                return {
                    ChartType::Histogram,
                    "The objective is to inspect a numerical distribution.",
                    warnings
                };

            case QuestionType::Mixed:
                if (differentScales) {
                    warnings.push_back(
                        "Primary and secondary axes must be clearly labeled."
                    );
                }

                return {
                    ChartType::Combo,
                    "Different measures are being displayed together.",
                    warnings
                };
        }

        throw logic_error("Unhandled question type.");
    }

private:

    static void validateRecord(const SalesRecord& record) {
        if (record.region.empty()) {
            throw invalid_argument("Record has an empty region.");
        }

        if (record.product.empty()) {
            throw invalid_argument("Record has an empty product.");
        }

        if (record.month.empty()) {
            throw invalid_argument("Record has an empty month.");
        }

        if (!isfinite(record.revenue) || record.revenue < 0) {
            throw invalid_argument("Revenue must be finite and non-negative.");
        }

        if (!isfinite(record.advertisingSpend) ||
            record.advertisingSpend < 0) {
            throw invalid_argument(
                "Advertising spend must be finite and non-negative."
            );
        }

        if (!isfinite(record.deliveryTime) ||
            record.deliveryTime < 0) {
            throw invalid_argument(
                "Delivery time must be finite and non-negative."
            );
        }
    }
};


// -----------------------------------------------------------------------------
// 5. Reporting layer
// -----------------------------------------------------------------------------

class VisualizationReport {
public:

    static void printRegionTotals(
        const map<string, double>& totals
    ) {
        cout << "\nRegional revenue:\n";

        for (const auto& [region, total] : totals) {
            cout << setw(15)
                 << left
                 << region
                 << right
                 << setw(14)
                 << fixed
                 << setprecision(2)
                 << total
                 << "\n";
        }

        cout << "\nTextual bar representation:\n";

        const double maximum = max_element(
            totals.begin(),
            totals.end(),
            [](const auto& left, const auto& right) {
                return left.second < right.second;
            }
        )->second;

        for (const auto& [region, total] : totals) {
            const size_t barLength =
                maximum == 0
                    ? 0
                    : static_cast<size_t>(
                        round((total / maximum) * 40)
                    );

            cout << setw(10)
                 << region
                 << " | "
                 << string(barLength, '#')
                 << " "
                 << fixed
                 << setprecision(0)
                 << total
                 << "\n";
        }
    }

    static void printHistogram(
        const vector<HistogramBin>& bins
    ) {
        cout << "\nDelivery-time histogram:\n";

        const size_t maximumFrequency =
            max_element(
                bins.begin(),
                bins.end(),
                [](const HistogramBin& left,
                   const HistogramBin& right) {
                    return left.frequency < right.frequency;
                }
            )->frequency;

        for (const auto& bin : bins) {
            const size_t barLength =
                maximumFrequency == 0
                    ? 0
                    : static_cast<size_t>(
                        round(
                            static_cast<double>(bin.frequency)
                            / static_cast<double>(maximumFrequency)
                            * 40.0
                        )
                    );

            cout << fixed
                 << setprecision(1)
                 << setw(6)
                 << bin.lower
                 << " - "
                 << setw(6)
                 << bin.upper
                 << " | "
                 << string(barLength, '#')
                 << " "
                 << bin.frequency
                 << "\n";
        }
    }

    static void printRecommendation(
        const ChartRecommendation& recommendation
    ) {
        cout << "\nRecommended chart: "
             << chartTypeToString(recommendation.type)
             << "\n";

        cout << "Reason: "
             << recommendation.reason
             << "\n";

        for (const string& warning : recommendation.warnings) {
            cout << "Warning: "
                 << warning
                 << "\n";
        }
    }
};


// -----------------------------------------------------------------------------
// 6. Data generator
// -----------------------------------------------------------------------------

vector<SalesRecord> createSampleDataset() {
    /*
     * The dataset deliberately contains repeated category values because
     * real-world transaction data normally needs aggregation before a chart
     * is produced.
     */

    return {
        {"Jan", "North", "Laptop", 120000, 10, 18},
        {"Jan", "South", "Phone", 90000, 8, 21},
        {"Feb", "North", "Laptop", 135000, 12, 25},
        {"Feb", "East", "Tablet", 110000, 11, 19},
        {"Mar", "West", "Laptop", 155000, 14, 32},
        {"Mar", "South", "Phone", 125000, 13, 28},
        {"Apr", "North", "Tablet", 142000, 15, 22},
        {"Apr", "East", "Phone", 131000, 16, 31},
        {"May", "West", "Laptop", 180000, 20, 26},
        {"May", "South", "Tablet", 149000, 19, 35},
        {"Jun", "North", "Phone", 175000, 22, 40},
        {"Jun", "East", "Laptop", 162000, 21, 37},
        {"Jul", "West", "Phone", 188000, 25, 29},
        {"Jul", "South", "Laptop", 159000, 23, 23},
        {"Aug", "North", "Laptop", 195000, 27, 21},
        {"Aug", "East", "Tablet", 171000, 26, 34},
        {"Sep", "West", "Laptop", 210000, 30, 27},
        {"Sep", "South", "Phone", 166000, 29, 25},
        {"Oct", "North", "Tablet", 187000, 31, 30},
        {"Oct", "East", "Phone", 174000, 32, 33},
        {"Nov", "West", "Laptop", 235000, 36, 38},
        {"Nov", "South", "Tablet", 191000, 34, 42},
        {"Dec", "North", "Phone", 225000, 40, 45},
        {"Dec", "East", "Laptop", 218000, 39, 24}
    };
}


// -----------------------------------------------------------------------------
// 7. Business case study
// -----------------------------------------------------------------------------

void runSalesAnalyticsCaseStudy() {
    printSection("INDUSTRY-STYLE SALES ANALYTICS CASE STUDY");

    const vector<SalesRecord> records =
        createSampleDataset();

    cout << "Source records: "
         << records.size()
         << "\n";

    /*
     * Stage 1: aggregate transactional data.
     *
     * Excel equivalent:
     *   PivotTable -> Rows: Region -> Values: Sum of Revenue
     */
    printSection("STAGE 1: REGIONAL AGGREGATION");

    const auto regionalTotals =
        VisualizationAnalytics::aggregateRevenueByRegion(records);

    VisualizationReport::printRegionTotals(regionalTotals);

    const auto regionRecommendation =
        VisualizationAnalytics::recommendChart(
            QuestionType::Comparison,
            regionalTotals.size()
        );

    VisualizationReport::printRecommendation(
        regionRecommendation
    );

    /*
     * Stage 2: time-series analysis.
     *
     * The aggregated monthly values become the source for a line chart.
     */
    printSection("STAGE 2: TIME-SERIES ANALYSIS");

    const auto monthlyTotals =
        VisualizationAnalytics::aggregateRevenueByMonth(records);

    vector<double> monthlyValues;

    for (const auto& [month, value] : monthlyTotals) {
        cout << month
             << ": "
             << fixed
             << setprecision(2)
             << value
             << "\n";

        monthlyValues.push_back(value);
    }

    cout << "\nMean monthly revenue: "
         << mean(monthlyValues)
         << "\n";

    cout << "Sample standard deviation: "
         << sampleStandardDeviation(monthlyValues)
         << "\n";

    const auto trendRecommendation =
        VisualizationAnalytics::recommendChart(
            QuestionType::Trend,
            monthlyTotals.size(),
            1,
            false,
            true
        );

    VisualizationReport::printRecommendation(
        trendRecommendation
    );

    /*
     * Stage 3: smoothing.
     *
     * The moving average is an analytical series that can be placed alongside
     * the original line in Excel when trend smoothing is useful.
     */
    printSection("STAGE 3: THREE-MONTH MOVING AVERAGE");

    const auto averages =
        VisualizationAnalytics::movingAverage(
            monthlyValues,
            3
        );

    for (size_t index = 0; index < averages.size(); ++index) {
        cout << "Window ending at observation "
             << index + 3
             << ": "
             << averages[index]
             << "\n";
    }

    /*
     * Stage 4: relationship analysis.
     *
     * Scatter plots require paired observations, not independently aggregated
     * values that destroy the relationship between observations.
     */
    printSection("STAGE 4: ADVERTISING VS REVENUE");

    const auto [advertising, revenue] =
        VisualizationAnalytics::advertisingRelationship(
            records
        );

    const double correlation =
        VisualizationAnalytics::pearsonCorrelation(
            advertising,
            revenue
        );

    cout << "Pearson correlation: "
         << fixed
         << setprecision(4)
         << correlation
         << "\n";

    const auto scatterRecommendation =
        VisualizationAnalytics::recommendChart(
            QuestionType::Relationship,
            0,
            1,
            false,
            false,
            true
        );

    VisualizationReport::printRecommendation(
        scatterRecommendation
    );

    /*
     * Stage 5: distribution analysis.
     *
     * A histogram converts raw delivery observations into adjacent numerical
     * ranges.
     */
    printSection("STAGE 5: DELIVERY-TIME DISTRIBUTION");

    vector<double> deliveryTimes;

    for (const auto& record : records) {
        deliveryTimes.push_back(record.deliveryTime);
    }

    const auto bins =
        VisualizationAnalytics::histogram(
            deliveryTimes,
            6
        );

    VisualizationReport::printHistogram(bins);

    const auto histogramRecommendation =
        VisualizationAnalytics::recommendChart(
            QuestionType::Distribution
        );

    VisualizationReport::printRecommendation(
        histogramRecommendation
    );

    /*
     * Stage 6: outlier investigation.
     */
    printSection("STAGE 6: OUTLIER SCREENING");

    vector<double> deliveryWithOutliers =
        deliveryTimes;

    deliveryWithOutliers.push_back(95);
    deliveryWithOutliers.push_back(110);

    const auto outliers =
        VisualizationAnalytics::detectOutliers(
            deliveryWithOutliers
        );

    cout << "Potential outliers: ";

    if (outliers.empty()) {
        cout << "none";
    } else {
        for (double value : outliers) {
            cout << value << " ";
        }
    }

    cout << "\n";

    /*
     * Stage 7: mixed-scale visualization.
     *
     * A combo chart is appropriate when revenue and margin are shown together.
     * The C++ program does not draw the Excel chart itself; it produces the
     * analytical recommendation and the chart-ready inputs.
     */
    printSection("STAGE 7: COMBO-CHART SCENARIO");

    cout << "Measure A: Revenue in currency units.\n";
    cout << "Measure B: Profit margin in percentage units.\n";
    cout << "Recommended visual: columns for revenue plus a line for margin.\n";
    cout << "Recommended design: primary and clearly labeled secondary axis.\n";

    const auto comboRecommendation =
        VisualizationAnalytics::recommendChart(
            QuestionType::Mixed,
            12,
            2,
            false,
            true,
            false,
            true
        );

    VisualizationReport::printRecommendation(
        comboRecommendation
    );
}


// -----------------------------------------------------------------------------
// 8. Failure-condition demonstrations
// -----------------------------------------------------------------------------

void demonstrateFailureConditions() {
    printSection("FAILURE CONDITIONS AND EDGE CASES");

    try {
        VisualizationAnalytics::histogram({}, 5);
    } catch (const exception& error) {
        cout << "Empty histogram handled: "
             << error.what()
             << "\n";
    }

    try {
        VisualizationAnalytics::histogram(
            {10, 20, 30},
            0
        );
    } catch (const exception& error) {
        cout << "Zero-bin histogram handled: "
             << error.what()
             << "\n";
    }

    try {
        VisualizationAnalytics::pearsonCorrelation(
            {1, 2, 3},
            {4, 5}
        );
    } catch (const exception& error) {
        cout << "Mismatched scatter data handled: "
             << error.what()
             << "\n";
    }

    try {
        VisualizationAnalytics::movingAverage(
            {1, 2, 3},
            5
        );
    } catch (const exception& error) {
        cout << "Invalid moving-average window handled: "
             << error.what()
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// 9. Automated verification
// -----------------------------------------------------------------------------

void runTests() {
    printSection("SELF-TESTS");

    const double correlation =
        VisualizationAnalytics::pearsonCorrelation(
            {1, 2, 3},
            {2, 4, 6}
        );

    if (abs(correlation - 1.0) > 1e-9) {
        throw runtime_error(
            "Correlation test failed."
        );
    }

    const auto averages =
        VisualizationAnalytics::movingAverage(
            {10, 20, 30, 40},
            2
        );

    const vector<double> expected = {
        15, 25, 35
    };

    if (averages != expected) {
        throw runtime_error(
            "Moving-average test failed."
        );
    }

    const auto bins =
        VisualizationAnalytics::histogram(
            {1, 2, 3, 4},
            2
        );

    size_t totalFrequency = 0;

    for (const auto& bin : bins) {
        totalFrequency += bin.frequency;
    }

    if (totalFrequency != 4) {
        throw runtime_error(
            "Histogram frequency test failed."
        );
    }

    const auto recommendation =
        VisualizationAnalytics::recommendChart(
            QuestionType::Trend,
            12,
            1,
            false,
            true
        );

    if (recommendation.type != ChartType::Line) {
        throw runtime_error(
            "Chart-selection test failed."
        );
    }

    cout << "All self-tests passed.\n";
}


// -----------------------------------------------------------------------------
// 10. Main
// -----------------------------------------------------------------------------

int main() {
    try {
        printSection("EXCEL DATA VISUALIZATION");

        cout << "Technical case study covering:\n";
        cout << "- Bar / column charts\n";
        cout << "- Line charts\n";
        cout << "- Pie charts\n";
        cout << "- Scatter plots\n";
        cout << "- Combo charts\n";
        cout << "- Histograms\n";
        cout << "- Chart selection principles\n";

        runSalesAnalyticsCaseStudy();
        demonstrateFailureConditions();
        runTests();

        printSection("DECISION REFERENCE");

        cout << "Category comparison       -> Bar / Column Chart\n";
        cout << "Time-based trend          -> Line Chart\n";
        cout << "Simple part-to-whole      -> Pie Chart\n";
        cout << "Two numerical variables   -> Scatter Plot\n";
        cout << "Numerical distribution    -> Histogram\n";
        cout << "Mixed measures/scales     -> Combo Chart\n";

        printSection("IMPLEMENTATION TRADE-OFFS");

        cout << "1. Aggregation reduces visual complexity but can hide record-level detail.\n";
        cout << "2. Line charts expose trends but imply meaningful ordering.\n";
        cout << "3. Pie charts communicate composition but make precise comparisons difficult.\n";
        cout << "4. Scatter plots preserve paired observations and expose relationships.\n";
        cout << "5. Histograms depend strongly on bin width.\n";
        cout << "6. Secondary axes solve scale differences but require careful labeling.\n";
        cout << "7. Outlier detection should support investigation rather than automatic deletion.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << "\n";

        return 1;
    }
}
