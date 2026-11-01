#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

enum class MeasureType {
    Mean,
    Median,
    Mode,
    WeightedMean,
    GeometricMean,
    HarmonicMean
};

struct WeightedObservation {
    double value;
    double weight;
};

class MeasureError : public std::runtime_error {
public:
    explicit MeasureError(const std::string& message)
        : std::runtime_error(message) {}
};

class CentralTendency {
private:
    static void validate(const std::vector<double>& values) {
        if (values.empty()) {
            throw MeasureError("Dataset must not be empty.");
        }

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw MeasureError("Dataset contains a non-finite value.");
            }
        }
    }

public:
    static double mean(const std::vector<double>& values) {
        validate(values);

        return std::accumulate(values.begin(), values.end(), 0.0)
            / static_cast<double>(values.size());
    }

    static double median(std::vector<double> values) {
        validate(values);

        const auto middle = values.begin() + values.size() / 2;
        std::nth_element(values.begin(), middle, values.end());

        if (values.size() % 2 == 1) {
            return *middle;
        }

        const double upper = *middle;
        const auto lowerIterator = std::max_element(
            values.begin(), middle
        );

        return (*lowerIterator + upper) / 2.0;
    }

    static std::vector<double> mode(const std::vector<double>& values) {
        validate(values);

        std::map<double, std::size_t> frequency;

        for (double value : values) {
            ++frequency[value];
        }

        std::size_t maximum = 0;
        for (const auto& [value, count] : frequency) {
            maximum = std::max(maximum, count);
        }

        if (maximum == 1) {
            return {};
        }

        std::vector<double> modes;
        for (const auto& [value, count] : frequency) {
            if (count == maximum) {
                modes.push_back(value);
            }
        }

        return modes;
    }

    static double weightedMean(
        const std::vector<WeightedObservation>& observations
    ) {
        if (observations.empty()) {
            throw MeasureError("Weighted observations must not be empty.");
        }

        double weightedTotal = 0.0;
        double totalWeight = 0.0;

        for (const auto& observation : observations) {
            if (!std::isfinite(observation.value) ||
                !std::isfinite(observation.weight)) {
                throw MeasureError("Values and weights must be finite.");
            }

            if (observation.weight < 0.0) {
                throw MeasureError("Negative weights are not permitted.");
            }

            weightedTotal += observation.value * observation.weight;
            totalWeight += observation.weight;
        }

        if (totalWeight <= 0.0) {
            throw MeasureError("Total weight must be greater than zero.");
        }

        return weightedTotal / totalWeight;
    }

    static double geometricMean(const std::vector<double>& values) {
        validate(values);

        double logarithmicSum = 0.0;

        for (double value : values) {
            if (value <= 0.0) {
                throw MeasureError(
                    "Geometric mean requires strictly positive values."
                );
            }

            logarithmicSum += std::log(value);
        }

        return std::exp(logarithmicSum / values.size());
    }

    static double harmonicMean(const std::vector<double>& values) {
        validate(values);

        double reciprocalSum = 0.0;

        for (double value : values) {
            if (value <= 0.0) {
                throw MeasureError(
                    "Harmonic mean requires strictly positive values."
                );
            }

            reciprocalSum += 1.0 / value;
        }

        return static_cast<double>(values.size()) / reciprocalSum;
    }
};

class RepositoryGovernanceMetrics {
private:
    std::vector<double> mergeTimes;

public:
    void recordMergeTime(double hours) {
        if (!std::isfinite(hours) || hours <= 0.0) {
            throw MeasureError("Merge time must be a positive finite value.");
        }

        mergeTimes.push_back(hours);
    }

    double typicalMergeTime() const {
        if (mergeTimes.empty()) {
            throw MeasureError("No merge-time observations exist.");
        }

        return CentralTendency::median(mergeTimes);
    }

    double averageMergeTime() const {
        return CentralTendency::mean(mergeTimes);
    }

    std::vector<double> commonMergeTimes() const {
        return CentralTendency::mode(mergeTimes);
    }
};

void printValues(const std::vector<double>& values) {
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ", ";
        }
        std::cout << values[i];
    }
}

void printDataset(const std::string& name,
                  const std::vector<double>& values) {
    std::cout << "\n" << name << "\n";
    std::cout << std::string(name.size(), '-') << "\n";

    std::cout << "Values: ";
    printValues(values);
    std::cout << "\n";

    std::cout << "Mean: " << CentralTendency::mean(values) << "\n";
    std::cout << "Median: " << CentralTendency::median(values) << "\n";

    const auto modes = CentralTendency::mode(values);
    std::cout << "Mode: ";

    if (modes.empty()) {
        std::cout << "No mode";
    } else {
        printValues(modes);
    }

    std::cout << "\n";
}

int main() {
    std::cout << std::fixed << std::setprecision(4);

    try {
        const std::vector<double> reviewTimes{
            2.0, 3.0, 3.0, 4.0, 5.0, 7.0, 40.0
        };

        const std::vector<double> deploymentMultipliers{
            1.02, 1.05, 1.03, 1.08
        };

        const std::vector<double> throughputRates{
            30.0, 40.0, 50.0
        };

        printDataset("Pull Request Review Times", reviewTimes);
        printDataset("Deployment Growth Multipliers", deploymentMultipliers);
        printDataset("Throughput Rates", throughputRates);

        std::cout << "\nSpecialized Measures\n";
        std::cout << "-------------------\n";

        std::cout
            << "Geometric mean: "
            << CentralTendency::geometricMean(deploymentMultipliers)
            << "\n";

        std::cout
            << "Harmonic mean: "
            << CentralTendency::harmonicMean(throughputRates)
            << "\n";

        const std::vector<WeightedObservation> qualityScores{
            {82.0, 0.20},
            {88.0, 0.30},
            {94.0, 0.50}
        };

        std::cout
            << "Weighted quality score: "
            << CentralTendency::weightedMean(qualityScores)
            << "\n";

        RepositoryGovernanceMetrics metrics;

        for (double hours : {3.0, 5.0, 4.0, 4.0, 8.0, 35.0}) {
            metrics.recordMergeTime(hours);
        }

        std::cout << "\nGovernance Metrics\n";
        std::cout << "-----------------\n";
        std::cout << "Average merge time: "
                  << metrics.averageMergeTime() << " hours\n";
        std::cout << "Typical merge time: "
                  << metrics.typicalMergeTime() << " hours\n";

        const auto common = metrics.commonMergeTimes();
        std::cout << "Most common merge time(s): ";
        printValues(common);
        std::cout << " hours\n";

        std::cout << "\nFailure Conditions\n";
        std::cout << "------------------\n";

        try {
            CentralTendency::geometricMean({10.0, 0.0, 20.0});
        } catch (const MeasureError& error) {
            std::cout << "Geometric mean rejected: "
                      << error.what() << "\n";
        }

        try {
            CentralTendency::harmonicMean({20.0, -5.0, 40.0});
        } catch (const MeasureError& error) {
            std::cout << "Harmonic mean rejected: "
                      << error.what() << "\n";
        }

        try {
            CentralTendency::weightedMean({
                {10.0, 0.0},
                {20.0, 0.0}
            });
        } catch (const MeasureError& error) {
            std::cout << "Weighted mean rejected: "
                      << error.what() << "\n";
        }

        const double testMean = CentralTendency::mean({2.0, 4.0, 6.0});
        const double testMedian = CentralTendency::median({1.0, 2.0, 3.0, 4.0});

        if (std::abs(testMean - 4.0) > 1e-9 ||
            std::abs(testMedian - 2.5) > 1e-9) {
            throw MeasureError("Built-in validation tests failed.");
        }

        std::cout << "\nValidation tests passed.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
