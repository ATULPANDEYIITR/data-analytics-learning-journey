#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * POWER BI ADVANCED ANALYTICS
 *
 * C++17 analytical engine.
 *
 * Focus:
 * 1. Decomposition tree
 * 2. Key influencers
 * 3. Linear forecasting
 * 4. Robust anomaly detection
 * 5. Analytical validation
 *
 * Compilation:
 * g++ -std=c++17 -O2 -Wall -Wextra main.cpp -o analytics
 */

class AnalyticsException : public runtime_error {
public:
    explicit AnalyticsException(const string& message)
        : runtime_error(message) {}
};

enum class Severity {
    Normal,
    High,
    Critical
};

struct SalesRecord {
    int id;
    string month;
    string region;
    string product;
    string segment;
    double revenue;
    double marketingSpend;
    int units;
};

struct BusinessMeasures {
    double revenue = 0;
    double marketingSpend = 0;
    double averageRevenue = 0;
    double marketingROI = 0;
    int transactionCount = 0;
    int totalUnits = 0;
};

struct DecompositionNode {
    string dimension;
    string value;
    double revenue = 0;
    double contribution = 0;
    int count = 0;
    vector<DecompositionNode> children;
};

struct Influencer {
    string dimension;
    string value;
    int sampleSize;
    double targetRate;
    double comparisonRate;
    double difference;
};

struct ForecastResult {
    string period;
    double prediction;
    double lowerBound;
    double upperBound;
};

struct Anomaly {
    int transactionId;
    double actual;
    double expected;
    double score;
    Severity severity;
};

class AnalyticsEngine {

private:
    vector<SalesRecord> records;

    static double median(vector<double> values) {
        if (values.empty()) {
            throw AnalyticsException("Cannot calculate empty median.");
        }

        sort(values.begin(), values.end());

        size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (
                values[middle - 1] + values[middle]
            ) / 2.0;
        }

        return values[middle];
    }

    static bool isFinite(double value) {
        return isfinite(value);
    }

    void validate() const {
        if (records.empty()) {
            throw AnalyticsException("Dataset cannot be empty.");
        }

        set<int> ids;

        for (const auto& record : records) {
            if (record.id <= 0 || !ids.insert(record.id).second) {
                throw AnalyticsException(
                    "Invalid or duplicate transaction ID."
                );
            }

            if (record.region.empty() ||
                record.product.empty() ||
                record.segment.empty()) {
                throw AnalyticsException(
                    "Categorical dimensions cannot be empty."
                );
            }

            if (!isFinite(record.revenue) ||
                !isFinite(record.marketingSpend)) {
                throw AnalyticsException(
                    "Financial values must be finite."
                );
            }

            if (record.revenue < 0 ||
                record.marketingSpend < 0 ||
                record.units < 0) {
                throw AnalyticsException(
                    "Negative business values are invalid."
                );
            }
        }
    }

    static string severityName(Severity severity) {
        switch (severity) {
            case Severity::Critical:
                return "CRITICAL";
            case Severity::High:
                return "HIGH";
            default:
                return "NORMAL";
        }
    }

    string dimensionValue(
        const SalesRecord& record,
        const string& dimension
    ) const {

        if (dimension == "region") return record.region;
        if (dimension == "product") return record.product;
        if (dimension == "segment") return record.segment;

        throw AnalyticsException(
            "Unsupported decomposition dimension: " + dimension
        );
    }

    vector<DecompositionNode> buildTree(
        const vector<SalesRecord>& subset,
        const vector<string>& dimensions,
        size_t depth,
        int topN
    ) const {

        if (depth >= dimensions.size()) {
            return {};
        }

        map<string, vector<SalesRecord>> groups;

        for (const auto& record : subset) {
            groups[dimensionValue(record, dimensions[depth])]
                .push_back(record);
        }

        vector<DecompositionNode> nodes;

        double parentRevenue = 0;

        for (const auto& record : subset) {
            parentRevenue += record.revenue;
        }

        for (const auto& [value, group] : groups) {
            double revenue = 0;

            for (const auto& record : group) {
                revenue += record.revenue;
            }

            DecompositionNode node;

            node.dimension = dimensions[depth];
            node.value = value;
            node.revenue = revenue;
            node.count = static_cast<int>(group.size());

            node.contribution = parentRevenue > 0
                ? revenue / parentRevenue * 100.0
                : 0;

            node.children = buildTree(
                group,
                dimensions,
                depth + 1,
                topN
            );

            nodes.push_back(move(node));
        }

        sort(
            nodes.begin(),
            nodes.end(),
            [](const auto& a, const auto& b) {
                return a.revenue > b.revenue;
            }
        );

        if (static_cast<int>(nodes.size()) > topN) {
            nodes.resize(topN);
        }

        return nodes;
    }

    static void printTree(
        const vector<DecompositionNode>& nodes,
        int depth = 0
    ) {

        for (const auto& node : nodes) {
            cout << string(depth * 2, ' ')
                 << node.dimension << "=" << node.value
                 << " | Revenue=" << node.revenue
                 << " | Contribution=" << node.contribution
                 << "% | Records=" << node.count
                 << '\n';

            printTree(node.children, depth + 1);
        }
    }

public:

    explicit AnalyticsEngine(vector<SalesRecord> input)
        : records(move(input)) {
        validate();
    }

    // ========================================================
    // BUSINESS MEASURES
    // ========================================================

    BusinessMeasures calculateMeasures() const {
        BusinessMeasures result;

        result.transactionCount = static_cast<int>(
            records.size()
        );

        for (const auto& record : records) {
            result.revenue += record.revenue;
            result.marketingSpend += record.marketingSpend;
            result.totalUnits += record.units;
        }

        result.averageRevenue =
            result.revenue / records.size();

        result.marketingROI =
            (result.revenue - result.marketingSpend) /
            max(result.marketingSpend, 1.0);

        return result;
    }

    // ========================================================
    // DECOMPOSITION TREE
    // ========================================================

    vector<DecompositionNode> decompositionTree(
        const vector<string>& dimensions,
        int topN = 5
    ) const {

        if (dimensions.empty() || topN < 1) {
            throw AnalyticsException(
                "Dimensions and positive topN are required."
            );
        }

        set<string> uniqueDimensions;

        for (const auto& dimension : dimensions) {
            if (dimension != "region" &&
                dimension != "product" &&
                dimension != "segment") {
                throw AnalyticsException(
                    "Unsupported decomposition dimension."
                );
            }

            if (!uniqueDimensions.insert(dimension).second) {
                throw AnalyticsException(
                    "Duplicate dimensions are invalid."
                );
            }
        }

        return buildTree(
            records,
            dimensions,
            0,
            topN
        );
    }

    // ========================================================
    // KEY INFLUENCERS
    // ========================================================

    vector<Influencer> keyInfluencers(
        int minimumGroupSize = 10
    ) const {

        if (minimumGroupSize < 2) {
            throw AnalyticsException(
                "Minimum group size must be at least two."
            );
        }

        vector<double> revenueValues;

        for (const auto& record : records) {
            revenueValues.push_back(record.revenue);
        }

        const double threshold = median(revenueValues);

        vector<Influencer> results;

        const vector<string> dimensions = {
            "region",
            "product",
            "segment"
        };

        for (const auto& dimension : dimensions) {
            map<string, vector<const SalesRecord*>> groups;

            for (const auto& record : records) {
                groups[dimensionValue(record, dimension)]
                    .push_back(&record);
            }

            for (const auto& [value, group] : groups) {

                if (static_cast<int>(group.size()) <
                    minimumGroupSize) {
                    continue;
                }

                int targetCount = 0;
                int comparisonCount = 0;
                int comparisonSize = 0;

                for (const auto* record : group) {
                    if (record->revenue > threshold) {
                        ++targetCount;
                    }
                }

                for (const auto& record : records) {
                    if (dimensionValue(record, dimension) == value) {
                        continue;
                    }

                    ++comparisonSize;

                    if (record.revenue > threshold) {
                        ++comparisonCount;
                    }
                }

                if (comparisonSize == 0) {
                    continue;
                }

                double targetRate =
                    static_cast<double>(targetCount) / group.size();

                double comparisonRate =
                    static_cast<double>(comparisonCount) /
                    comparisonSize;

                double difference =
                    targetRate - comparisonRate;

                if (difference <= 0) {
                    continue;
                }

                results.push_back({
                    dimension,
                    value,
                    static_cast<int>(group.size()),
                    targetRate,
                    comparisonRate,
                    difference
                });
            }
        }

        sort(
            results.begin(),
            results.end(),
            [](const Influencer& a, const Influencer& b) {
                return a.difference > b.difference;
            }
        );

        return results;
    }

    // ========================================================
    // TIME-SERIES FORECASTING
    // ========================================================

    vector<ForecastResult> forecast(
        int periods = 3
    ) const {

        if (periods < 1 || periods > 36) {
            throw AnalyticsException(
                "Forecast horizon must be between 1 and 36."
            );
        }

        map<string, double> monthly;

        for (const auto& record : records) {
            monthly[record.month] += record.revenue;
        }

        if (monthly.size() < 6) {
            throw AnalyticsException(
                "Six monthly observations are required."
            );
        }

        vector<double> values;

        for (const auto& [month, revenue] : monthly) {
            values.push_back(revenue);
        }

        double xMean = (values.size() - 1) / 2.0;

        double yMean = accumulate(
            values.begin(),
            values.end(),
            0.0
        ) / values.size();

        double numerator = 0;
        double denominator = 0;

        for (size_t i = 0; i < values.size(); ++i) {
            numerator +=
                (static_cast<double>(i) - xMean) *
                (values[i] - yMean);

            denominator +=
                pow(static_cast<double>(i) - xMean, 2);
        }

        if (denominator == 0) {
            throw AnalyticsException(
                "Regression denominator is zero."
            );
        }

        double slope = numerator / denominator;
        double intercept = yMean - slope * xMean;

        vector<double> residuals;

        for (size_t i = 0; i < values.size(); ++i) {
            residuals.push_back(
                values[i] - (intercept + slope * i)
            );
        }

        double residualMean = accumulate(
            residuals.begin(),
            residuals.end(),
            0.0
        ) / residuals.size();

        double squaredError = 0;

        for (double residual : residuals) {
            squaredError += pow(
                residual - residualMean,
                2
            );
        }

        double residualStd = sqrt(
            squaredError / (residuals.size() - 1)
        );

        string lastMonth = monthly.rbegin()->first;

        int year = stoi(lastMonth.substr(0, 4));
        int month = stoi(lastMonth.substr(5, 2));

        vector<ForecastResult> results;

        for (int step = 1; step <= periods; ++step) {
            double index = values.size() - 1 + step;

            double prediction = max(
                0.0,
                intercept + slope * index
            );

            double uncertainty = 1.96 * residualStd *
                sqrt(1.0 + step / static_cast<double>(values.size()));

            int nextMonth = month + step;
            int nextYear = year + (nextMonth - 1) / 12;
            nextMonth = ((nextMonth - 1) % 12) + 1;

            ostringstream period;

            period << nextYear << "-"
                   << setw(2) << setfill('0')
                   << nextMonth;

            results.push_back({
                period.str(),
                prediction,
                max(0.0, prediction - uncertainty),
                prediction + uncertainty
            });
        }

        return results;
    }

    // ========================================================
    // ROBUST ANOMALY DETECTION
    // ========================================================

    vector<Anomaly> detectAnomalies(
        double threshold = 3.5
    ) const {

        if (!isFinite(threshold) || threshold <= 0) {
            throw AnalyticsException(
                "Threshold must be positive and finite."
            );
        }

        vector<double> values;

        for (const auto& record : records) {
            values.push_back(record.revenue);
        }

        double center = median(values);

        vector<double> deviations;

        for (double value : values) {
            deviations.push_back(abs(value - center));
        }

        double mad = median(deviations);

        if (mad == 0) {
            throw AnalyticsException(
                "MAD is zero; anomaly scoring is undefined."
            );
        }

        vector<Anomaly> anomalies;

        for (const auto& record : records) {
            double score =
                0.6745 * (record.revenue - center) / mad;

            if (abs(score) >= threshold) {

                Severity severity = abs(score) >= 7
                    ? Severity::Critical
                    : Severity::High;

                anomalies.push_back({
                    record.id,
                    record.revenue,
                    center,
                    score,
                    severity
                });
            }
        }

        sort(
            anomalies.begin(),
            anomalies.end(),
            [](const Anomaly& a, const Anomaly& b) {
                return abs(a.score) > abs(b.score);
            }
        );

        return anomalies;
    }

    // ========================================================
    // REPORTING
    // ========================================================

    void printReport() const {

        const auto measures = calculateMeasures();

        cout << fixed << setprecision(2);

        cout << "\nBUSINESS MEASURES\n";

        cout << "Transactions: "
             << measures.transactionCount << '\n';

        cout << "Revenue: "
             << measures.revenue << '\n';

        cout << "Marketing spend: "
             << measures.marketingSpend << '\n';

        cout << "Average revenue: "
             << measures.averageRevenue << '\n';

        cout << "Marketing ROI: "
             << measures.marketingROI << '\n';

        cout << "\nDECOMPOSITION TREE\n";

        printTree(
            decompositionTree(
                {"region", "product", "segment"},
                3
            )
        );

        cout << "\nKEY INFLUENCERS\n";

        for (const auto& item : keyInfluencers()) {
            cout << item.dimension
                 << "=" << item.value
                 << " | Target rate=" << item.targetRate
                 << " | Comparison rate="
                 << item.comparisonRate
                 << " | Difference=" << item.difference
                 << '\n';
        }

        cout << "\nFORECAST\n";

        for (const auto& item : forecast(3)) {
            cout << item.period
                 << " | Prediction=" << item.prediction
                 << " | Lower=" << item.lowerBound
                 << " | Upper=" << item.upperBound
                 << '\n';
        }

        cout << "\nANOMALIES\n";

        for (const auto& item : detectAnomalies()) {
            cout << "Transaction=" << item.transactionId
                 << " | Actual=" << item.actual
                 << " | Expected=" << item.expected
                 << " | Score=" << item.score
                 << " | Severity="
                 << severityName(item.severity)
                 << '\n';
        }
    }
};

// ============================================================
// DATA GENERATION
// ============================================================

vector<SalesRecord> generateData(
    int count = 600,
    unsigned int seed = 42
) {

    if (count < 30) {
        throw AnalyticsException(
            "At least 30 records are required."
        );
    }

    mt19937 generator(seed);

    vector<string> regions = {
        "North", "South", "East", "West"
    };

    vector<string> products = {
        "Laptop", "Mobile", "Tablet", "Monitor"
    };

    vector<string> segments = {
        "Consumer", "Corporate", "Small Business"
    };

    uniform_int_distribution<int> regionDist(0, 3);
    uniform_int_distribution<int> productDist(0, 3);
    uniform_int_distribution<int> segmentDist(0, 2);
    uniform_int_distribution<int> unitsDist(1, 12);
    uniform_real_distribution<double> discountDist(0, 20);
    uniform_real_distribution<double> marketingDist(50, 600);
    uniform_real_distribution<double> noiseDist(-90, 90);

    map<string, double> prices = {
        {"Laptop", 850},
        {"Mobile", 420},
        {"Tablet", 300},
        {"Monitor", 260}
    };

    map<string, double> regionalFactors = {
        {"North", 1.15},
        {"South", 1.05},
        {"East", 0.90},
        {"West", 1.10}
    };

    map<string, double> segmentFactors = {
        {"Consumer", 1.0},
        {"Corporate", 1.30},
        {"Small Business", 1.10}
    };

    vector<SalesRecord> records;

    for (int i = 0; i < count; ++i) {

        string region = regions[regionDist(generator)];
        string product = products[productDist(generator)];
        string segment = segments[segmentDist(generator)];

        int units = unitsDist(generator);

        double discount = discountDist(generator);

        double revenue =
            prices[product] *
            units *
            regionalFactors[region] *
            segmentFactors[segment] *
            (1 - discount / 100.0);

        revenue = max(
            0.0,
            revenue + noiseDist(generator)
        );

        if (i == 75 || i == 190 || i == 330 || i == 470) {
            revenue *= 3.5;
        }

        int monthNumber = (i % 365) / 30 + 1;
        int dayNumber = (i % 28) + 1;

        ostringstream month;

        month << "2025-"
              << setw(2) << setfill('0')
              << monthNumber;

        records.push_back({
            i + 1,
            month.str(),
            region,
            product,
            segment,
            revenue,
            marketingDist(generator),
            units
        });
    }

    return records;
}

// ============================================================
// MAIN
// ============================================================

int main() {

    try {
        cout << "POWER BI ADVANCED ANALYTICS ENGINE\n";
        cout << "==================================\n";

        auto records = generateData(600);

        AnalyticsEngine engine(move(records));

        engine.printReport();

        cout << "\nVALIDATION\n";

        const auto measures = engine.calculateMeasures();

        if (measures.transactionCount != 600) {
            throw AnalyticsException(
                "Transaction count validation failed."
            );
        }

        if (engine.forecast(3).size() != 3) {
            throw AnalyticsException(
                "Forecast validation failed."
            );
        }

        cout << "All analytical validations passed.\n";

    } catch (const exception& error) {
        cerr << "ERROR: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
