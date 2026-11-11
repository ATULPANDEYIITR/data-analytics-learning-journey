#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Method {
    Pearson,
    Spearman,
    Kendall
};

struct Observation {
    double x;
    double y;
};

struct CorrelationResult {
    Method method;
    double coefficient;
    size_t sampleSize;
    string interpretation;
};

struct PairCounts {
    long long concordant = 0;
    long long discordant = 0;
    long long tiesX = 0;
    long long tiesY = 0;
};

class CorrelationException : public runtime_error {
public:
    explicit CorrelationException(const string& message)
        : runtime_error(message) {}
};

class CorrelationEngine {
private:
    static constexpr size_t MINIMUM_SAMPLE_SIZE = 3;

    static vector<Observation> validate(
        const vector<Observation>& data
    ) {
        if (data.size() < MINIMUM_SAMPLE_SIZE) {
            throw CorrelationException(
                "At least three observations are required."
            );
        }

        for (const auto& item : data) {
            if (
                !isfinite(item.x) ||
                !isfinite(item.y)
            ) {
                throw CorrelationException(
                    "Non-finite observations are not permitted."
                );
            }
        }

        return data;
    }

    static vector<double> extractX(
        const vector<Observation>& data
    ) {
        vector<double> result;

        for (const auto& item : data) {
            result.push_back(item.x);
        }

        return result;
    }

    static vector<double> extractY(
        const vector<Observation>& data
    ) {
        vector<double> result;

        for (const auto& item : data) {
            result.push_back(item.y);
        }

        return result;
    }

    static vector<double> ranks(
        const vector<double>& values
    ) {
        vector<pair<double, size_t>> ordered;

        for (size_t i = 0; i < values.size(); ++i) {
            ordered.push_back({values[i], i});
        }

        sort(
            ordered.begin(),
            ordered.end(),
            [](const auto& a, const auto& b) {
                return a.first < b.first;
            }
        );

        vector<double> result(values.size());

        size_t i = 0;

        while (i < ordered.size()) {
            size_t j = i + 1;

            while (
                j < ordered.size() &&
                ordered[j].first == ordered[i].first
            ) {
                ++j;
            }

            double averageRank =
                (static_cast<double>(i + 1) +
                 static_cast<double>(j)) / 2.0;

            for (size_t k = i; k < j; ++k) {
                result[ordered[k].second] = averageRank;
            }

            i = j;
        }

        return result;
    }

    static string interpret(double value) {
        double magnitude = abs(value);

        string strength;

        if (magnitude < 0.10) strength = "negligible";
        else if (magnitude < 0.30) strength = "weak";
        else if (magnitude < 0.50) strength = "moderate";
        else if (magnitude < 0.70) strength = "strong";
        else strength = "very strong";

        string direction =
            value > 0 ? "positive" :
            value < 0 ? "negative" : "neutral";

        return strength + " " + direction + " association";
    }

public:
    static double pearson(
        const vector<Observation>& input
    ) {
        const auto data = validate(input);

        double meanX = 0;
        double meanY = 0;

        for (const auto& item : data) {
            meanX += item.x;
            meanY += item.y;
        }

        meanX /= data.size();
        meanY /= data.size();

        double numerator = 0;
        double sumX = 0;
        double sumY = 0;

        for (const auto& item : data) {
            double dx = item.x - meanX;
            double dy = item.y - meanY;

            numerator += dx * dy;
            sumX += dx * dx;
            sumY += dy * dy;
        }

        double denominator = sqrt(sumX * sumY);

        if (denominator == 0) {
            throw CorrelationException(
                "Pearson correlation undefined for constant variables."
            );
        }

        return numerator / denominator;
    }

    static double spearman(
        const vector<Observation>& input
    ) {
        const auto data = validate(input);

        auto x = ranks(extractX(data));
        auto y = ranks(extractY(data));

        vector<Observation> ranked;

        for (size_t i = 0; i < x.size(); ++i) {
            ranked.push_back({x[i], y[i]});
        }

        return pearson(ranked);
    }

    static double kendallTauB(
        const vector<Observation>& input
    ) {
        const auto data = validate(input);

        PairCounts counts;

        for (size_t i = 0; i < data.size(); ++i) {
            for (size_t j = i + 1; j < data.size(); ++j) {
                int dx =
                    (data[i].x > data[j].x) -
                    (data[i].x < data[j].x);

                int dy =
                    (data[i].y > data[j].y) -
                    (data[i].y < data[j].y);

                if (dx == 0 && dy == 0) continue;

                if (dx == 0) {
                    ++counts.tiesX;
                } else if (dy == 0) {
                    ++counts.tiesY;
                } else if (dx == dy) {
                    ++counts.concordant;
                } else {
                    ++counts.discordant;
                }
            }
        }

        double denominator = sqrt(
            static_cast<double>(
                counts.concordant +
                counts.discordant +
                counts.tiesX
            ) *
            static_cast<double>(
                counts.concordant +
                counts.discordant +
                counts.tiesY
            )
        );

        if (denominator == 0) {
            throw CorrelationException(
                "Kendall tau-b is undefined."
            );
        }

        return (
            static_cast<double>(
                counts.concordant - counts.discordant
            ) / denominator
        );
    }

    static vector<CorrelationResult> analyze(
        const vector<Observation>& data
    ) {
        validate(data);

        vector<CorrelationResult> results;

        const vector<pair<Method, double>> values = {
            {Method::Pearson, pearson(data)},
            {Method::Spearman, spearman(data)},
            {Method::Kendall, kendallTauB(data)}
        };

        for (const auto& item : values) {
            results.push_back({
                item.first,
                item.second,
                data.size(),
                interpret(item.second)
            });
        }

        return results;
    }

    static double partialCorrelation(
        const vector<double>& x,
        const vector<double>& y,
        const vector<double>& z
    ) {
        if (
            x.size() != y.size() ||
            x.size() != z.size() ||
            x.size() < MINIMUM_SAMPLE_SIZE
        ) {
            throw CorrelationException(
                "Invalid partial correlation dimensions."
            );
        }

        double meanX = accumulate(x.begin(), x.end(), 0.0)
            / x.size();

        double meanY = accumulate(y.begin(), y.end(), 0.0)
            / y.size();

        double meanZ = accumulate(z.begin(), z.end(), 0.0)
            / z.size();

        double denominator = 0;
        double numeratorX = 0;
        double numeratorY = 0;

        for (size_t i = 0; i < z.size(); ++i) {
            if (
                !isfinite(x[i]) ||
                !isfinite(y[i]) ||
                !isfinite(z[i])
            ) {
                throw CorrelationException(
                    "Non-finite partial correlation input."
                );
            }

            double dz = z[i] - meanZ;

            denominator += dz * dz;
            numeratorX += dz * (x[i] - meanX);
            numeratorY += dz * (y[i] - meanY);
        }

        if (denominator == 0) {
            throw CorrelationException(
                "Confounding variable is constant."
            );
        }

        double slopeX = numeratorX / denominator;
        double slopeY = numeratorY / denominator;

        vector<Observation> residuals;

        for (size_t i = 0; i < z.size(); ++i) {
            double residualX =
                x[i] - meanX - slopeX * (z[i] - meanZ);

            double residualY =
                y[i] - meanY - slopeY * (z[i] - meanZ);

            residuals.push_back({
                residualX,
                residualY
            });
        }

        return pearson(residuals);
    }

    static double permutationTest(
        const vector<Observation>& input,
        size_t iterations = 2000,
        unsigned int seed = 42
    ) {
        const auto data = validate(input);

        if (iterations < 100) {
            throw CorrelationException(
                "At least 100 permutations are required."
            );
        }

        double observed = pearson(data);

        vector<double> x = extractX(data);
        vector<double> y = extractY(data);

        mt19937 generator(seed);

        size_t extreme = 0;

        for (size_t i = 0; i < iterations; ++i) {
            shuffle(y.begin(), y.end(), generator);

            vector<Observation> shuffled;

            for (size_t j = 0; j < x.size(); ++j) {
                shuffled.push_back({x[j], y[j]});
            }

            double simulated = pearson(shuffled);

            if (abs(simulated) >= abs(observed)) {
                ++extreme;
            }
        }

        return static_cast<double>(extreme + 1)
            / static_cast<double>(iterations + 1);
    }
};

void printResults(
    const string& title,
    const vector<Observation>& data
) {
    cout << "\n" << title << "\n";

    for (const auto& result :
         CorrelationEngine::analyze(data)) {

        string method;

        switch (result.method) {
            case Method::Pearson:
                method = "Pearson";
                break;

            case Method::Spearman:
                method = "Spearman";
                break;

            case Method::Kendall:
                method = "Kendall tau-b";
                break;
        }

        cout << left << setw(16) << method
             << " coefficient = "
             << setw(10) << result.coefficient
             << " n = " << result.sampleSize
             << " | " << result.interpretation
             << "\n";
    }
}

int main() {
    try {
        cout << fixed << setprecision(6);

        vector<Observation> linear = {
            {1, 2},
            {2, 4},
            {3, 6},
            {4, 8},
            {5, 10},
            {6, 12}
        };

        vector<Observation> nonlinear = {
            {1, 1},
            {2, 4},
            {3, 9},
            {4, 16},
            {5, 25},
            {6, 36}
        };

        vector<Observation> tied = {
            {1, 2},
            {2, 1},
            {2, 3},
            {4, 4},
            {5, 4},
            {5, 6}
        };

        printResults("Perfect linear relationship", linear);
        printResults("Nonlinear monotonic relationship", nonlinear);
        printResults("Tied observations", tied);

        // A shared driver creates an apparent raw relationship.
        mt19937 generator(42);
        normal_distribution<double> noise(0.0, 8.0);

        vector<double> x, y, z;

        for (int i = 0; i < 100; ++i) {
            double common = static_cast<double>(i);

            z.push_back(common);
            x.push_back(3.0 * common + noise(generator));
            y.push_back(2.5 * common + noise(generator));
        }

        vector<Observation> confounded;

        for (size_t i = 0; i < x.size(); ++i) {
            confounded.push_back({x[i], y[i]});
        }

        cout << "\nConfounding analysis\n";

        cout << "Raw Pearson: "
             << CorrelationEngine::pearson(confounded)
             << "\n";

        cout << "Partial Pearson: "
             << CorrelationEngine::partialCorrelation(x, y, z)
             << "\n";

        cout << "\nPermutation test\n";

        cout << "Estimated p-value: "
             << CorrelationEngine::permutationTest(
                    linear, 1000, 42
                )
             << "\n";

        // Correctness checks.
        if (abs(CorrelationEngine::pearson(linear) - 1.0) > 1e-10) {
            throw CorrelationException("Pearson test failed.");
        }

        if (abs(CorrelationEngine::spearman(nonlinear) - 1.0) > 1e-10) {
            throw CorrelationException("Spearman test failed.");
        }

        if (
            abs(CorrelationEngine::kendallTauB(nonlinear) - 1.0)
            > 1e-10
        ) {
            throw CorrelationException("Kendall test failed.");
        }

        cout << "\nAll validation tests passed.\n";

    } catch (const exception& error) {
        cerr << "Analysis error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
