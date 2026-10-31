#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

enum class SamplingMethod {
    SimpleRandom,
    Systematic
};

struct Statistics {
    std::size_t count{};
    double minimum{};
    double maximum{};
    double mean{};
    double median{};
    double populationVariance{};
    double populationStdDev{};
    double sampleVariance{};
    double sampleStdDev{};
};

class StatisticsEngine {
public:
    static void validate(const std::vector<double>& values,
                         const std::string& name) {
        if (values.empty()) {
            throw std::invalid_argument(name + " cannot be empty.");
        }

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument(
                    name + " contains a non-finite value.");
            }
        }
    }

    static double mean(const std::vector<double>& values) {
        validate(values, "values");
        return std::accumulate(values.begin(), values.end(), 0.0)
               / static_cast<double>(values.size());
    }

    static double variance(const std::vector<double>& values,
                           bool sample) {
        validate(values, "values");

        if (sample && values.size() < 2) {
            throw std::invalid_argument(
                "Sample variance requires at least two observations.");
        }

        const double average = mean(values);
        double sum = 0.0;

        for (double value : values) {
            const double difference = value - average;
            sum += difference * difference;
        }

        const double divisor = sample
            ? static_cast<double>(values.size() - 1)
            : static_cast<double>(values.size());

        return sum / divisor;
    }

    static double median(std::vector<double> values) {
        validate(values, "values");
        std::sort(values.begin(), values.end());

        const std::size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (values[middle - 1] + values[middle]) / 2.0;
        }

        return values[middle];
    }

    static std::vector<double> modes(
        const std::vector<double>& values) {

        validate(values, "values");

        std::map<double, std::size_t> frequency;
        for (double value : values) {
            ++frequency[value];
        }

        std::size_t maximum = 0;
        for (const auto& [value, count] : frequency) {
            maximum = std::max(maximum, count);
        }

        std::vector<double> result;
        for (const auto& [value, count] : frequency) {
            if (count == maximum) {
                result.push_back(value);
            }
        }

        return result;
    }

    static Statistics describe(const std::vector<double>& values) {
        validate(values, "values");

        const auto minimum = *std::min_element(
            values.begin(), values.end());
        const auto maximum = *std::max_element(
            values.begin(), values.end());
        const auto average = mean(values);
        const auto popVar = variance(values, false);
        const auto sampleVar = values.size() >= 2
            ? variance(values, true)
            : std::numeric_limits<double>::quiet_NaN();

        return {
            values.size(),
            minimum,
            maximum,
            average,
            median(values),
            popVar,
            std::sqrt(popVar),
            sampleVar,
            std::sqrt(sampleVar)
        };
    }

    static std::vector<double> simpleRandomSample(
        const std::vector<double>& population,
        std::size_t sampleSize,
        unsigned int seed) {

        validate(population, "population");

        if (sampleSize == 0 || sampleSize > population.size()) {
            throw std::invalid_argument("Invalid sample size.");
        }

        std::vector<double> shuffled = population;
        std::mt19937 generator(seed);
        std::shuffle(shuffled.begin(), shuffled.end(), generator);

        shuffled.resize(sampleSize);
        return shuffled;
    }

    static std::vector<double> systematicSample(
        const std::vector<double>& population,
        std::size_t sampleSize) {

        validate(population, "population");

        if (sampleSize == 0 || sampleSize > population.size()) {
            throw std::invalid_argument("Invalid sample size.");
        }

        const double interval =
            static_cast<double>(population.size()) / sampleSize;

        std::vector<double> result;
        result.reserve(sampleSize);

        for (std::size_t i = 0; i < sampleSize; ++i) {
            const auto index =
                static_cast<std::size_t>(std::floor(i * interval));
            result.push_back(population[index]);
        }

        return result;
    }
};

void printVector(const std::vector<double>& values) {
    for (double value : values) {
        std::cout << value << ' ';
    }
    std::cout << '\n';
}

void printStatistics(const Statistics& stats) {
    std::cout << std::fixed << std::setprecision(4)
              << "count=" << stats.count
              << ", minimum=" << stats.minimum
              << ", maximum=" << stats.maximum
              << ", mean=" << stats.mean
              << ", median=" << stats.median
              << ", population_variance="
              << stats.populationVariance
              << ", population_stddev="
              << stats.populationStdDev
              << ", sample_variance="
              << stats.sampleVariance
              << ", sample_stddev="
              << stats.sampleStdDev
              << '\n';
}

int main() {
    try {
        const std::vector<double> population = {
            61, 64, 66, 68, 69,
            71, 72, 73, 74, 75,
            76, 77, 78, 79, 80,
            81, 82, 83, 84, 85,
            86, 87, 88, 90, 92
        };

        const Statistics populationStats =
            StatisticsEngine::describe(population);

        std::cout << "Population:\n";
        printStatistics(populationStats);

        const auto randomSample =
            StatisticsEngine::simpleRandomSample(
                population, 8, 42);

        std::cout << "\nSimple random sample:\n";
        printVector(randomSample);
        printStatistics(StatisticsEngine::describe(randomSample));

        const auto systematic =
            StatisticsEngine::systematicSample(population, 5);

        std::cout << "\nSystematic sample:\n";
        printVector(systematic);
        printStatistics(StatisticsEngine::describe(systematic));

        const double parameter = populationStats.mean;
        const double statistic =
            StatisticsEngine::mean(randomSample);

        std::cout << "\nPopulation parameter (mean): "
                  << parameter << '\n';
        std::cout << "Sample statistic (mean): "
                  << statistic << '\n';

        const double standardError =
            std::sqrt(
                StatisticsEngine::variance(randomSample, true)
                / randomSample.size()
            );

        std::cout << "Standard error: "
                  << standardError << '\n';

        if (populationStats.count != 25) {
            throw std::logic_error("Population validation failed.");
        }

        if (randomSample.size() != 8) {
            throw std::logic_error("Sample validation failed.");
        }

        try {
            StatisticsEngine::simpleRandomSample(
                population, 0, 42);
        } catch (const std::invalid_argument& error) {
            std::cout << "\nExpected validation failure: "
                      << error.what() << '\n';
        }

        try {
            StatisticsEngine::variance({10.0}, true);
        } catch (const std::invalid_argument& error) {
            std::cout << "Expected variance failure: "
                      << error.what() << '\n';
        }

        /*
         * The population mean is a parameter because it describes the
         * complete population. The sample mean is a statistic because
         * it is computed from observed sample data.
         *
         * std::shuffle is O(n), while descriptive calculations are
         * generally O(n), except median which requires sorting and is
         * O(n log n). The implementation keeps all values in memory.
         */
        std::cout << "\nAll checks passed.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Fatal error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
