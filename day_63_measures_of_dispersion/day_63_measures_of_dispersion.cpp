#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

enum class VariabilityLevel {
    Low,
    Moderate,
    High,
    Undefined
};

struct DispersionReport {
    std::size_t count{};
    double minimum{};
    double maximum{};
    double range{};
    double mean{};
    double populationVariance{};
    double sampleVariance{};
    double populationStandardDeviation{};
    double sampleStandardDeviation{};
    double q1{};
    double q3{};
    double iqr{};
    double mad{};
    double coefficientOfVariation{};
};

class DispersionEngine {
private:
    static void validate(const std::vector<double>& values) {
        if (values.empty()) {
            throw std::invalid_argument(
                "At least one observation is required."
            );
        }

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument(
                    "All observations must be finite."
                );
            }
        }
    }

    static double percentile(
        std::vector<double> values,
        double probability
    ) {
        std::sort(values.begin(), values.end());

        if (values.size() == 1) {
            return values.front();
        }

        const double position =
            (values.size() - 1) * probability;

        const auto lower =
            static_cast<std::size_t>(std::floor(position));

        const auto upper =
            std::min(lower + 1, values.size() - 1);

        const double fraction = position - lower;

        return values[lower] +
            fraction * (values[upper] - values[lower]);
    }

    static double median(std::vector<double> values) {
        std::sort(values.begin(), values.end());

        const std::size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (values[middle - 1] + values[middle]) / 2.0;
        }

        return values[middle];
    }

public:
    DispersionReport calculate(
        const std::vector<double>& values
    ) const {
        validate(values);

        const double sum =
            std::accumulate(values.begin(), values.end(), 0.0);

        const double average = sum / values.size();

        double squaredDeviationSum = 0.0;

        for (double value : values) {
            const double deviation = value - average;
            squaredDeviationSum += deviation * deviation;
        }

        const double populationVariance =
            squaredDeviationSum / values.size();

        const double sampleVariance =
            values.size() > 1
                ? squaredDeviationSum / (values.size() - 1)
                : std::numeric_limits<double>::quiet_NaN();

        const auto [minIt, maxIt] =
            std::minmax_element(values.begin(), values.end());

        const double q1 = percentile(values, 0.25);
        const double q3 = percentile(values, 0.75);
        const double med = median(values);

        std::vector<double> deviations;
        deviations.reserve(values.size());

        for (double value : values) {
            deviations.push_back(std::abs(value - med));
        }

        const double mad = median(deviations);
        const double populationSD = std::sqrt(populationVariance);

        const double cv =
            average == 0.0
                ? std::numeric_limits<double>::quiet_NaN()
                : (populationSD / std::abs(average)) * 100.0;

        return {
            values.size(),
            *minIt,
            *maxIt,
            *maxIt - *minIt,
            average,
            populationVariance,
            sampleVariance,
            populationSD,
            values.size() > 1
                ? std::sqrt(sampleVariance)
                : std::numeric_limits<double>::quiet_NaN(),
            q1,
            q3,
            q3 - q1,
            mad,
            cv
        };
    }

    static VariabilityLevel classify(double cv) {
        if (!std::isfinite(cv)) {
            return VariabilityLevel::Undefined;
        }

        if (cv < 10.0) {
            return VariabilityLevel::Low;
        }

        if (cv < 20.0) {
            return VariabilityLevel::Moderate;
        }

        return VariabilityLevel::High;
    }
};

static void printReport(const DispersionReport& report) {
    std::cout << std::fixed << std::setprecision(4);

    std::cout << "Measures of Dispersion\n";
    std::cout << "======================\n";
    std::cout << "Count: " << report.count << '\n';
    std::cout << "Minimum: " << report.minimum << '\n';
    std::cout << "Maximum: " << report.maximum << '\n';
    std::cout << "Range: " << report.range << '\n';
    std::cout << "Mean: " << report.mean << '\n';
    std::cout << "Population variance: "
              << report.populationVariance << '\n';
    std::cout << "Sample variance: "
              << report.sampleVariance << '\n';
    std::cout << "Population standard deviation: "
              << report.populationStandardDeviation << '\n';
    std::cout << "Sample standard deviation: "
              << report.sampleStandardDeviation << '\n';
    std::cout << "Q1: " << report.q1 << '\n';
    std::cout << "Q3: " << report.q3 << '\n';
    std::cout << "IQR: " << report.iqr << '\n';
    std::cout << "MAD: " << report.mad << '\n';
    std::cout << "Coefficient of variation (%): "
              << report.coefficientOfVariation << '\n';
}

static void saveReport(
    const DispersionReport& report,
    const std::string& filename
) {
    std::ofstream output(filename, std::ios::out | std::ios::trunc);

    if (!output) {
        throw std::runtime_error(
            "Unable to open output file."
        );
    }

    output << std::setprecision(10);
    output << "count=" << report.count << '\n';
    output << "minimum=" << report.minimum << '\n';
    output << "maximum=" << report.maximum << '\n';
    output << "range=" << report.range << '\n';
    output << "mean=" << report.mean << '\n';
    output << "population_variance="
           << report.populationVariance << '\n';
    output << "sample_variance="
           << report.sampleVariance << '\n';
    output << "population_standard_deviation="
           << report.populationStandardDeviation << '\n';
    output << "sample_standard_deviation="
           << report.sampleStandardDeviation << '\n';
    output << "q1=" << report.q1 << '\n';
    output << "q3=" << report.q3 << '\n';
    output << "iqr=" << report.iqr << '\n';
    output << "mad=" << report.mad << '\n';
    output << "coefficient_of_variation="
           << report.coefficientOfVariation << '\n';
}

static void runTests() {
    DispersionEngine engine;

    const std::vector<double> values{
        12, 15, 14, 10, 18, 20, 13, 16, 15, 11
    };

    const auto report = engine.calculate(values);

    if (report.count != 10 ||
        report.minimum != 10 ||
        report.maximum != 20 ||
        report.range != 10 ||
        std::abs(report.mean - 14.4) > 1e-9 ||
        report.populationVariance <= 0 ||
        report.iqr <= 0 ||
        report.mad <= 0) {
        throw std::runtime_error("Primary validation failed.");
    }

    const auto single = engine.calculate({5});

    if (single.range != 0 ||
        single.populationVariance != 0 ||
        single.iqr != 0 ||
        single.mad != 0) {
        throw std::runtime_error("Single-value validation failed.");
    }

    try {
        engine.calculate({});
        throw std::runtime_error("Empty input was accepted.");
    } catch (const std::invalid_argument&) {
    }

    try {
        engine.calculate({
            1.0,
            std::numeric_limits<double>::quiet_NaN()
        });
        throw std::runtime_error("NaN input was accepted.");
    } catch (const std::invalid_argument&) {
    }
}

int main() {
    try {
        const std::vector<double> observations{
            12, 15, 14, 10, 18, 20, 13, 16, 15, 11
        };

        DispersionEngine engine;
        const DispersionReport report =
            engine.calculate(observations);

        printReport(report);

        saveReport(report, "dispersion_report.txt");

        const auto level =
            DispersionEngine::classify(
                report.coefficientOfVariation
            );

        std::cout << "\nVariability classification: ";

        switch (level) {
            case VariabilityLevel::Low:
                std::cout << "Low";
                break;
            case VariabilityLevel::Moderate:
                std::cout << "Moderate";
                break;
            case VariabilityLevel::High:
                std::cout << "High";
                break;
            case VariabilityLevel::Undefined:
                std::cout << "Undefined";
                break;
        }

        std::cout << '\n';

        runTests();
        std::cout << "Validation tests: passed\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Execution failed: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
