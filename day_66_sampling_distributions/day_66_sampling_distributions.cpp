#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

enum class SamplingMethod {
    WITH_REPLACEMENT,
    WITHOUT_REPLACEMENT
};

struct PopulationStatistics {
    size_t size;
    double mean;
    double variance;
    double standardDeviation;
};

struct SamplingResult {
    size_t sampleSize;
    size_t repetitions;
    double samplingMean;
    double theoreticalSE;
    double empiricalSE;
    double bias;
    double minimum;
    double maximum;
};

class SamplingEngine {
private:
    vector<double> population;
    PopulationStatistics stats;
    mt19937_64 generator;

    void validateSampleSize(size_t sampleSize) const {
        if (sampleSize == 0) {
            throw invalid_argument(
                "Sample size must be greater than zero."
            );
        }

        if (
            sampleSize > population.size()
        ) {
            throw invalid_argument(
                "Sample size exceeds population size."
            );
        }
    }

    void calculatePopulationStatistics() {
        const size_t n = population.size();

        double sum = 0.0;

        for (double value : population) {
            sum += value;
        }

        const double mean = sum / n;

        double squaredDifferences = 0.0;

        for (double value : population) {
            const double difference = value - mean;
            squaredDifferences += difference * difference;
        }

        const double variance = squaredDifferences / n;

        stats = {
            n,
            mean,
            variance,
            sqrt(variance)
        };
    }

public:
    explicit SamplingEngine(
        vector<double> observations,
        uint64_t seed = 2026
    ) : population(move(observations)), generator(seed) {

        if (population.empty()) {
            throw invalid_argument("Population cannot be empty.");
        }

        for (double value : population) {
            if (!isfinite(value)) {
                throw invalid_argument(
                    "Population contains a non-finite value."
                );
            }
        }

        calculatePopulationStatistics();
    }

    const PopulationStatistics& getPopulationStatistics() const {
        return stats;
    }

    vector<double> drawSample(
        size_t sampleSize,
        SamplingMethod method
    ) {
        validateSampleSize(sampleSize);

        vector<double> sample;
        sample.reserve(sampleSize);

        if (method == SamplingMethod::WITH_REPLACEMENT) {
            uniform_int_distribution<size_t> distribution(
                0,
                population.size() - 1
            );

            for (size_t i = 0; i < sampleSize; ++i) {
                sample.push_back(
                    population[distribution(generator)]
                );
            }
        } else {
            // Partial Fisher-Yates sampling.
            // Complexity: O(N) to initialize indices and O(n)
            // to select a sample of size n.
            vector<size_t> indices(population.size());

            for (size_t i = 0; i < indices.size(); ++i) {
                indices[i] = i;
            }

            for (size_t i = 0; i < sampleSize; ++i) {
                uniform_int_distribution<size_t> distribution(
                    i,
                    indices.size() - 1
                );

                size_t j = distribution(generator);

                swap(indices[i], indices[j]);

                sample.push_back(population[indices[i]]);
            }
        }

        return sample;
    }

    static double calculateMean(
        const vector<double>& values
    ) {
        if (values.empty()) {
            throw invalid_argument("Cannot calculate empty mean.");
        }

        double sum = 0.0;

        for (double value : values) {
            sum += value;
        }

        return sum / values.size();
    }

    static double calculateSampleVariance(
        const vector<double>& values
    ) {
        if (values.size() < 2) {
            throw invalid_argument(
                "At least two observations are required."
            );
        }

        const double mean = calculateMean(values);

        double sum = 0.0;

        for (double value : values) {
            sum += pow(value - mean, 2);
        }

        return sum / (values.size() - 1);
    }

    double theoreticalStandardError(
        size_t sampleSize,
        SamplingMethod method
    ) const {
        validateSampleSize(sampleSize);

        double se =
            stats.standardDeviation / sqrt(
                static_cast<double>(sampleSize)
            );

        if (method == SamplingMethod::WITHOUT_REPLACEMENT) {
            const double correction =
                stats.size == 1
                ? 0.0
                : sqrt(
                    static_cast<double>(stats.size - sampleSize)
                    / static_cast<double>(stats.size - 1)
                );

            se *= correction;
        }

        return se;
    }

    SamplingResult simulate(
        size_t sampleSize,
        size_t repetitions,
        SamplingMethod method
    ) {
        validateSampleSize(sampleSize);

        if (repetitions < 2) {
            throw invalid_argument(
                "At least two repetitions are required."
            );
        }

        // Welford's algorithm computes the empirical variance
        // without retaining every simulated sample mean.
        double runningMean = 0.0;
        double runningM2 = 0.0;

        double minimum = numeric_limits<double>::max();
        double maximum = numeric_limits<double>::lowest();

        for (size_t i = 1; i <= repetitions; ++i) {
            const vector<double> sample = drawSample(
                sampleSize,
                method
            );

            const double sampleMean = calculateMean(sample);

            const double delta = sampleMean - runningMean;

            runningMean += delta / static_cast<double>(i);

            const double delta2 = sampleMean - runningMean;

            runningM2 += delta * delta2;

            minimum = min(minimum, sampleMean);
            maximum = max(maximum, sampleMean);
        }

        const double empiricalVariance =
            runningM2 / static_cast<double>(repetitions - 1);

        const double empiricalSE = sqrt(
            max(0.0, empiricalVariance)
        );

        return {
            sampleSize,
            repetitions,
            runningMean,
            theoreticalStandardError(sampleSize, method),
            empiricalSE,
            runningMean - stats.mean,
            minimum,
            maximum
        };
    }

    vector<pair<size_t, double>> lawOfLargeNumbers(
        const vector<size_t>& sampleSizes,
        SamplingMethod method
    ) {
        vector<pair<size_t, double>> results;

        for (size_t size : sampleSizes) {
            validateSampleSize(size);

            vector<double> sample = drawSample(size, method);

            results.emplace_back(
                size,
                calculateMean(sample)
            );
        }

        return results;
    }

    static pair<double, double> normalConfidenceInterval(
        double estimate,
        double standardError,
        double criticalValue = 1.96
    ) {
        if (
            !isfinite(estimate) ||
            !isfinite(standardError) ||
            standardError < 0 ||
            criticalValue <= 0 ||
            !isfinite(criticalValue)
        ) {
            throw invalid_argument(
                "Invalid confidence interval parameters."
            );
        }

        const double margin = criticalValue * standardError;

        return {
            estimate - margin,
            estimate + margin
        };
    }
};

string methodName(SamplingMethod method) {
    return method == SamplingMethod::WITH_REPLACEMENT
        ? "With replacement"
        : "Without replacement";
}

void runTests() {
    SamplingEngine engine({10, 20, 30, 40, 50}, 42);

    const auto& stats = engine.getPopulationStatistics();

    if (stats.size != 5 || abs(stats.mean - 30.0) > 1e-10) {
        throw runtime_error("Population statistics test failed.");
    }

    if (abs(stats.variance - 200.0) > 1e-10) {
        throw runtime_error("Population variance test failed.");
    }

    const double se = engine.theoreticalStandardError(
        4,
        SamplingMethod::WITH_REPLACEMENT
    );

    if (abs(se - sqrt(50.0)) > 1e-10) {
        throw runtime_error("Standard error test failed.");
    }

    const auto sample = engine.drawSample(
        3,
        SamplingMethod::WITHOUT_REPLACEMENT
    );

    unordered_set<double> uniqueValues(
        sample.begin(),
        sample.end()
    );

    if (uniqueValues.size() != 3) {
        throw runtime_error("Sampling uniqueness test failed.");
    }

    bool rejected = false;

    try {
        engine.drawSample(
            6,
            SamplingMethod::WITHOUT_REPLACEMENT
        );
    } catch (const invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw runtime_error("Invalid sample was accepted.");
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        runTests();

        vector<double> population;

        // Simulated customer transaction population.
        population.insert(population.end(), 500, 5.0);
        population.insert(population.end(), 250, 15.0);
        population.insert(population.end(), 150, 30.0);
        population.insert(population.end(), 100, 100.0);

        SamplingEngine engine(population, 2026);

        const auto& stats = engine.getPopulationStatistics();

        cout << fixed << setprecision(5);

        cout << "\nPOPULATION STATISTICS\n";
        cout << "Population size: " << stats.size << '\n';
        cout << "Population mean: " << stats.mean << '\n';
        cout << "Population variance: " << stats.variance << '\n';
        cout << "Population SD: " << stats.standardDeviation << '\n';

        cout << "\nSAMPLE STATISTICS\n";

        auto sample = engine.drawSample(
            30,
            SamplingMethod::WITHOUT_REPLACEMENT
        );

        cout << "Sample size: " << sample.size() << '\n';
        cout << "Sample mean: "
             << SamplingEngine::calculateMean(sample) << '\n';

        cout << "Sample variance: "
             << SamplingEngine::calculateSampleVariance(sample) << '\n';

        cout << "\nCENTRAL LIMIT THEOREM\n";

        const vector<size_t> sampleSizes = {
            2, 5, 10, 30, 50, 100
        };

        for (size_t size : sampleSizes) {
            const auto result = engine.simulate(
                size,
                10000,
                SamplingMethod::WITH_REPLACEMENT
            );

            cout << "\nSample size: " << result.sampleSize << '\n';
            cout << "Sampling mean: " << result.samplingMean << '\n';
            cout << "Theoretical SE: " << result.theoreticalSE << '\n';
            cout << "Empirical SE: " << result.empiricalSE << '\n';
            cout << "Bias: " << result.bias << '\n';
        }

        cout << "\nLAW OF LARGE NUMBERS\n";

        auto lln = engine.lawOfLargeNumbers(
            {10, 50, 100, 500, 1000},
            SamplingMethod::WITH_REPLACEMENT
        );

        for (const auto& [size, mean] : lln) {
            cout << "n=" << size
                 << " sample mean=" << mean
                 << " absolute error=" << abs(mean - stats.mean)
                 << '\n';
        }

        cout << "\nFINITE POPULATION CORRECTION\n";

        for (size_t size : {10, 50, 100, 250}) {
            cout << "n=" << size
                 << " with replacement="
                 << engine.theoreticalStandardError(
                     size,
                     SamplingMethod::WITH_REPLACEMENT
                 )
                 << " without replacement="
                 << engine.theoreticalStandardError(
                     size,
                     SamplingMethod::WITHOUT_REPLACEMENT
                 )
                 << '\n';
        }

        cout << "\n95% CONFIDENCE INTERVAL\n";

        const auto result = engine.simulate(
            100,
            10000,
            SamplingMethod::WITH_REPLACEMENT
        );

        const auto interval =
            SamplingEngine::normalConfidenceInterval(
                result.samplingMean,
                result.theoreticalSE
            );

        cout << "Estimate: " << result.samplingMean << '\n';
        cout << "Lower bound: " << interval.first << '\n';
        cout << "Upper bound: " << interval.second << '\n';

        cout << "\nSimulation completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
