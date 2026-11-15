#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Statistical Analysis Project
 *
 * C++17 implementation:
 * - Descriptive statistics
 * - Pearson correlation
 * - Linear regression
 * - Bootstrap confidence intervals
 * - Permutation hypothesis testing
 * - Statistical decision reporting
 *
 * No external libraries.
 */

struct Observation {
    int participantId;
    double studyHours;
    double examScore;
};

struct ConfidenceInterval {
    double lower;
    double upper;
    double level;
};

struct RegressionResult {
    double slope;
    double intercept;
    double rSquared;
    double rmse;
    double mae;
};

struct AnalysisResult {
    double correlation;
    double pValue;
    ConfidenceInterval correlationCI;
    ConfidenceInterval slopeCI;
    RegressionResult regression;
};

class StatisticalException : public std::runtime_error {
public:
    explicit StatisticalException(const std::string& message)
        : std::runtime_error(message) {}
};

class StatisticalEngine {
private:
    std::vector<Observation> observations;
    std::mt19937 generator;

    static constexpr double ALPHA = 0.05;

    static double mean(const std::vector<double>& values) {
        if (values.empty()) {
            throw StatisticalException("Empty dataset.");
        }

        return std::accumulate(
            values.begin(), values.end(), 0.0
        ) / values.size();
    }

    static double percentile(
        std::vector<double> values,
        double probability
    ) {
        if (values.empty() || probability < 0 || probability > 1) {
            throw StatisticalException("Invalid percentile.");
        }

        std::sort(values.begin(), values.end());

        double position = probability * (values.size() - 1);
        std::size_t lower = static_cast<std::size_t>(position);
        std::size_t upper = static_cast<std::size_t>(
            std::ceil(position)
        );

        double fraction = position - lower;

        return values[lower] * (1 - fraction)
            + values[upper] * fraction;
    }

    static void validate(
        const std::vector<Observation>& data
    ) {
        if (data.size() < 4) {
            throw StatisticalException(
                "At least four observations are required."
            );
        }

        std::vector<int> identifiers;

        for (const auto& item : data) {
            if (item.participantId <= 0) {
                throw StatisticalException("Invalid participant ID.");
            }

            if (
                !std::isfinite(item.studyHours)
                || item.studyHours < 0
            ) {
                throw StatisticalException("Invalid study hours.");
            }

            if (
                !std::isfinite(item.examScore)
                || item.examScore < 0
                || item.examScore > 100
            ) {
                throw StatisticalException("Invalid exam score.");
            }

            identifiers.push_back(item.participantId);
        }

        std::sort(identifiers.begin(), identifiers.end());

        if (
            std::adjacent_find(
                identifiers.begin(), identifiers.end()
            ) != identifiers.end()
        ) {
            throw StatisticalException("Duplicate participant ID.");
        }
    }

    static std::pair<
        std::vector<double>,
        std::vector<double>
    > extract(
        const std::vector<Observation>& data
    ) {
        std::vector<double> x;
        std::vector<double> y;

        for (const auto& item : data) {
            x.push_back(item.studyHours);
            y.push_back(item.examScore);
        }

        return {x, y};
    }

public:
    explicit StatisticalEngine(
        std::vector<Observation> data,
        unsigned int seed = 42
    ) : observations(std::move(data)), generator(seed) {
        validate(observations);

        auto [x, y] = extract(observations);

        if (
            *std::min_element(x.begin(), x.end())
                == *std::max_element(x.begin(), x.end())
            ||
            *std::min_element(y.begin(), y.end())
                == *std::max_element(y.begin(), y.end())
        ) {
            throw StatisticalException(
                "Both variables must contain variation."
            );
        }
    }

    static double pearson(
        const std::vector<double>& x,
        const std::vector<double>& y
    ) {
        if (x.size() != y.size() || x.size() < 3) {
            throw StatisticalException(
                "Invalid correlation sample."
            );
        }

        double mx = mean(x);
        double my = mean(y);

        double numerator = 0;
        double sx = 0;
        double sy = 0;

        for (std::size_t i = 0; i < x.size(); ++i) {
            double dx = x[i] - mx;
            double dy = y[i] - my;

            numerator += dx * dy;
            sx += dx * dx;
            sy += dy * dy;
        }

        double denominator = std::sqrt(sx * sy);

        if (denominator == 0) {
            throw StatisticalException(
                "Correlation is undefined."
            );
        }

        return numerator / denominator;
    }

    static RegressionResult regression(
        const std::vector<double>& x,
        const std::vector<double>& y
    ) {
        if (x.size() != y.size() || x.size() < 3) {
            throw StatisticalException("Invalid regression sample.");
        }

        double mx = mean(x);
        double my = mean(y);

        double numerator = 0;
        double denominator = 0;

        for (std::size_t i = 0; i < x.size(); ++i) {
            numerator += (x[i] - mx) * (y[i] - my);
            denominator += std::pow(x[i] - mx, 2);
        }

        if (denominator == 0) {
            throw StatisticalException("Undefined regression slope.");
        }

        double slope = numerator / denominator;
        double intercept = my - slope * mx;

        double residualSum = 0;
        double totalSum = 0;
        double absoluteError = 0;

        for (std::size_t i = 0; i < x.size(); ++i) {
            double prediction = intercept + slope * x[i];
            double residual = y[i] - prediction;

            residualSum += residual * residual;
            totalSum += std::pow(y[i] - my, 2);
            absoluteError += std::abs(residual);
        }

        return {
            slope,
            intercept,
            1.0 - residualSum / totalSum,
            std::sqrt(residualSum / x.size()),
            absoluteError / x.size()
        };
    }

    ConfidenceInterval bootstrap(
        bool calculateSlope,
        int iterations = 5000,
        double confidence = 0.95
    ) {
        if (iterations < 1000 || confidence <= 0 || confidence >= 1) {
            throw StatisticalException("Invalid bootstrap configuration.");
        }

        std::vector<double> estimates;
        std::uniform_int_distribution<std::size_t> distribution(
            0, observations.size() - 1
        );

        for (int iteration = 0; iteration < iterations; ++iteration) {
            std::vector<Observation> sample;
            sample.reserve(observations.size());

            // Resample paired records, not individual columns.
            for (std::size_t i = 0; i < observations.size(); ++i) {
                sample.push_back(observations[distribution(generator)]);
            }

            auto [x, y] = extract(sample);

            try {
                estimates.push_back(
                    calculateSlope
                        ? regression(x, y).slope
                        : pearson(x, y)
                );
            } catch (const StatisticalException&) {
                continue;
            }
        }

        if (estimates.size() < iterations * 0.95) {
            throw StatisticalException(
                "Too many invalid bootstrap samples."
            );
        }

        double tail = (1 - confidence) / 2;

        return {
            percentile(estimates, tail),
            percentile(estimates, 1 - tail),
            confidence
        };
    }

    double permutationTest(int iterations = 10000) {
        if (iterations < 1000) {
            throw StatisticalException(
                "At least 1000 permutations are required."
            );
        }

        auto [x, y] = extract(observations);

        double observed = std::abs(pearson(x, y));
        int extreme = 0;

        for (int iteration = 0; iteration < iterations; ++iteration) {
            auto randomizedY = y;
            std::shuffle(
                randomizedY.begin(),
                randomizedY.end(),
                generator
            );

            double simulated = std::abs(
                pearson(x, randomizedY)
            );

            if (simulated >= observed) {
                ++extreme;
            }
        }

        return static_cast<double>(extreme + 1)
            / (iterations + 1);
    }

    AnalysisResult analyze() {
        auto [x, y] = extract(observations);

        double correlation = pearson(x, y);

        RegressionResult model = regression(x, y);

        ConfidenceInterval correlationCI = bootstrap(false);
        ConfidenceInterval slopeCI = bootstrap(true);

        double pValue = permutationTest();

        return {
            correlation,
            pValue,
            correlationCI,
            slopeCI,
            model
        };
    }

    std::map<std::string, double> descriptiveStatistics(
        const std::vector<double>& values
    ) {
        double center = mean(values);

        double squaredSum = 0;

        for (double value : values) {
            squaredSum += std::pow(value - center, 2);
        }

        double standardDeviation = std::sqrt(
            squaredSum / (values.size() - 1)
        );

        return {
            {"mean", center},
            {"standard_deviation", standardDeviation},
            {"minimum", *std::min_element(values.begin(), values.end())},
            {"maximum", *std::max_element(values.begin(), values.end())}
        };
    }

    void printReport(const AnalysisResult& result) {
        auto [x, y] = extract(observations);

        auto study = descriptiveStatistics(x);
        auto scores = descriptiveStatistics(y);

        std::cout << std::fixed << std::setprecision(5);

        std::cout << "\n========================================\n";
        std::cout << "STATISTICAL ANALYSIS REPORT\n";
        std::cout << "========================================\n";

        std::cout << "Sample size: " << observations.size() << "\n";

        std::cout << "\nStudy hours:\n";
        for (const auto& [name, value] : study) {
            std::cout << name << ": " << value << "\n";
        }

        std::cout << "\nExamination scores:\n";
        for (const auto& [name, value] : scores) {
            std::cout << name << ": " << value << "\n";
        }

        std::cout << "\nHypothesis testing:\n";
        std::cout << "H0: Population correlation equals zero.\n";
        std::cout << "H1: Population correlation is not zero.\n";
        std::cout << "Pearson correlation: "
                  << result.correlation << "\n";

        std::cout << "Permutation p-value: "
                  << result.pValue << "\n";

        std::cout << "Decision: "
                  << (
                      result.pValue < ALPHA
                          ? "Reject H0"
                          : "Fail to reject H0"
                  ) << "\n";

        std::cout << "\nCorrelation confidence interval:\n";
        std::cout << "["
                  << result.correlationCI.lower << ", "
                  << result.correlationCI.upper << "]\n";

        std::cout << "\nRegression:\n";
        std::cout << "Slope: " << result.regression.slope << "\n";
        std::cout << "Intercept: " << result.regression.intercept << "\n";
        std::cout << "Slope confidence interval: ["
                  << result.slopeCI.lower << ", "
                  << result.slopeCI.upper << "]\n";
        std::cout << "R-squared: "
                  << result.regression.rSquared << "\n";
        std::cout << "RMSE: "
                  << result.regression.rmse << "\n";
        std::cout << "MAE: "
                  << result.regression.mae << "\n";

        std::cout << "\nInterpretation:\n";
        std::cout << (
            result.correlation > 0
                ? "Positive association detected.\n"
                : "Negative association detected.\n"
        );

        std::cout << "Association does not establish causation.\n";
    }

    void saveReport(const AnalysisResult& result) {
        std::ofstream file(
            "statistical_analysis_report.txt",
            std::ios::out | std::ios::trunc
        );

        if (!file) {
            throw StatisticalException(
                "Unable to open report output file."
            );
        }

        file << std::setprecision(10);
        file << "Statistical Analysis Report\n";
        file << "Sample size: " << observations.size() << "\n";
        file << "Correlation: " << result.correlation << "\n";
        file << "Permutation p-value: " << result.pValue << "\n";
        file << "Correlation CI: "
             << result.correlationCI.lower << ", "
             << result.correlationCI.upper << "\n";
        file << "Regression slope: "
             << result.regression.slope << "\n";
        file << "Slope CI: "
             << result.slopeCI.lower << ", "
             << result.slopeCI.upper << "\n";
        file << "R-squared: "
             << result.regression.rSquared << "\n";

        if (!file.good()) {
            throw StatisticalException("Report writing failed.");
        }
    }
};

int main() {
    try {
        std::vector<Observation> data = {
            {1, 1.0, 48},
            {2, 1.5, 52},
            {3, 2.0, 55},
            {4, 2.5, 58},
            {5, 3.0, 62},
            {6, 3.5, 65},
            {7, 4.0, 68},
            {8, 4.5, 70},
            {9, 5.0, 74},
            {10, 5.5, 77},
            {11, 6.0, 80},
            {12, 7.0, 86}
        };

        StatisticalEngine engine(data, 42);

        AnalysisResult result = engine.analyze();

        engine.printReport(result);
        engine.saveReport(result);

        std::cout << "\nReport saved successfully.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << "\n";

        return 1;
    }

    return 0;
}
