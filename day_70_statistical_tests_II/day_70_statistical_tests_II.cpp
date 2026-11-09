#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Statistical Tests II
 *
 * C++17 statistical inference and governance engine.
 *
 * Implements:
 * 1. Chi-square goodness-of-fit.
 * 2. Chi-square independence.
 * 3. One-sample proportion z-test.
 * 4. Two-sample proportion z-test.
 *
 * Standard library only.
 */

namespace statistics {

constexpr double EPSILON = 1e-14;
constexpr double MINIMUM = 1e-300;

class StatisticalError : public std::runtime_error {
public:
    explicit StatisticalError(const std::string& message)
        : std::runtime_error(message) {}
};

enum class TestType {
    GoodnessOfFit,
    Independence,
    OneProportion,
    TwoProportion
};

struct TestResult {
    std::string testName;
    double statistic{};
    int degreesOfFreedom{};
    double pValue{};
    double alpha{};
    bool rejectNull{};
    std::size_t sampleSize{};
    double effectSize{};
    std::string interpretation;
};

void validateAlpha(double alpha) {
    if (!std::isfinite(alpha) || alpha <= 0 || alpha >= 1) {
        throw StatisticalError(
            "Alpha must be strictly between zero and one."
        );
    }
}

void validateCounts(const std::vector<int>& values) {
    if (values.empty()) {
        throw StatisticalError("Count vector cannot be empty.");
    }

    for (int value : values) {
        if (value < 0) {
            throw StatisticalError(
                "Counts cannot be negative."
            );
        }
    }
}

double regularizedGammaQ(double a, double x) {
    if (a <= 0 || x < 0) {
        throw StatisticalError("Invalid gamma parameters.");
    }

    if (x == 0) return 1.0;

    const double logFactor =
        -x + a * std::log(x) - std::lgamma(a);

    if (x < a + 1.0) {
        double ap = a;
        double term = 1.0 / a;
        double sum = term;

        for (int i = 0; i < 10000; ++i) {
            ap += 1.0;
            term *= x / ap;
            sum += term;

            if (std::abs(term) < std::abs(sum) * EPSILON) {
                double p = sum * std::exp(logFactor);
                return std::clamp(1.0 - p, 0.0, 1.0);
            }
        }

        throw StatisticalError(
            "Gamma series did not converge."
        );
    }

    double b = x + 1.0 - a;
    double c = 1.0 / MINIMUM;
    double d = 1.0 / b;
    double h = d;

    for (int i = 1; i <= 10000; ++i) {
        const double an = -static_cast<double>(i) *
            (static_cast<double>(i) - a);

        b += 2.0;

        d = an * d + b;
        if (std::abs(d) < MINIMUM) d = MINIMUM;

        c = b + an / c;
        if (std::abs(c) < MINIMUM) c = MINIMUM;

        d = 1.0 / d;
        const double delta = d * c;
        h *= delta;

        if (std::abs(delta - 1.0) < EPSILON) {
            return std::clamp(
                std::exp(logFactor) * h,
                0.0,
                1.0
            );
        }
    }

    throw StatisticalError(
        "Gamma continued fraction did not converge."
    );
}

double chiSquarePValue(double statistic, int df) {
    if (
        !std::isfinite(statistic) ||
        statistic < 0 ||
        df <= 0
    ) {
        throw StatisticalError(
            "Invalid chi-square statistic or degrees of freedom."
        );
    }

    return regularizedGammaQ(
        df / 2.0,
        statistic / 2.0
    );
}

double normalTwoSidedPValue(double z) {
    return std::erfc(std::abs(z) / std::sqrt(2.0));
}

TestResult buildResult(
    const std::string& name,
    double statistic,
    int df,
    double p,
    double alpha,
    std::size_t sampleSize,
    double effectSize,
    const std::string& interpretation
) {
    return {
        name,
        statistic,
        df,
        p,
        alpha,
        p < alpha,
        sampleSize,
        effectSize,
        interpretation
    };
}

TestResult goodnessOfFit(
    const std::vector<int>& observed,
    const std::vector<double>& expected,
    double alpha = 0.05
) {
    validateAlpha(alpha);
    validateCounts(observed);

    if (
        observed.size() < 2 ||
        observed.size() != expected.size()
    ) {
        throw StatisticalError(
            "Observed and expected arrays must match "
            "and contain at least two categories."
        );
    }

    for (double value : expected) {
        if (!std::isfinite(value) || value <= 0) {
            throw StatisticalError(
                "Expected frequencies must be positive."
            );
        }
    }

    const double observedTotal = std::accumulate(
        observed.begin(), observed.end(), 0.0
    );

    const double expectedTotal = std::accumulate(
        expected.begin(), expected.end(), 0.0
    );

    if (
        observedTotal <= 0 ||
        std::abs(observedTotal - expectedTotal) > 1e-9
    ) {
        throw StatisticalError(
            "Observed and expected totals must match."
        );
    }

    double statistic = 0;

    for (std::size_t i = 0; i < observed.size(); ++i) {
        const double difference =
            observed[i] - expected[i];

        statistic += difference * difference / expected[i];
    }

    const int df = static_cast<int>(observed.size()) - 1;
    const double p = chiSquarePValue(statistic, df);

    return buildResult(
        "Chi-square goodness-of-fit",
        statistic,
        df,
        p,
        alpha,
        static_cast<std::size_t>(observedTotal),
        std::sqrt(statistic / observedTotal),
        p < alpha
            ? "Observed frequencies differ significantly."
            : "Insufficient evidence of distribution difference."
    );
}

TestResult independenceTest(
    const std::vector<std::vector<int>>& table,
    double alpha = 0.05,
    bool yatesCorrection = false
) {
    validateAlpha(alpha);

    if (table.size() < 2 || table.front().size() < 2) {
        throw StatisticalError(
            "At least two rows and two columns are required."
        );
    }

    const std::size_t rows = table.size();
    const std::size_t cols = table.front().size();

    std::vector<double> rowTotals(rows, 0);
    std::vector<double> columnTotals(cols, 0);

    for (std::size_t i = 0; i < rows; ++i) {
        if (table[i].size() != cols) {
            throw StatisticalError(
                "Contingency table must be rectangular."
            );
        }

        validateCounts(table[i]);

        for (std::size_t j = 0; j < cols; ++j) {
            rowTotals[i] += table[i][j];
            columnTotals[j] += table[i][j];
        }
    }

    const double total = std::accumulate(
        rowTotals.begin(), rowTotals.end(), 0.0
    );

    if (
        total <= 0 ||
        std::any_of(rowTotals.begin(), rowTotals.end(),
            [](double x) { return x == 0; }) ||
        std::any_of(columnTotals.begin(), columnTotals.end(),
            [](double x) { return x == 0; })
    ) {
        throw StatisticalError(
            "Every row and column must contain observations."
        );
    }

    double statistic = 0;
    double minimumExpected =
        std::numeric_limits<double>::max();

    for (std::size_t i = 0; i < rows; ++i) {
        for (std::size_t j = 0; j < cols; ++j) {
            const double expected =
                rowTotals[i] * columnTotals[j] / total;

            minimumExpected = std::min(
                minimumExpected,
                expected
            );

            double difference = std::abs(
                table[i][j] - expected
            );

            if (yatesCorrection && rows == 2 && cols == 2) {
                difference = std::max(
                    0.0,
                    difference - 0.5
                );
            }

            statistic += difference * difference / expected;
        }
    }

    const int df = static_cast<int>(
        (rows - 1) * (cols - 1)
    );

    const double p = chiSquarePValue(statistic, df);

    const double v = std::sqrt(
        statistic /
        (total * std::min(rows - 1, cols - 1))
    );

    std::string message = p < alpha
        ? "Evidence of categorical association."
        : "Insufficient evidence of categorical association.";

    if (minimumExpected < 5) {
        message += " Expected cell count below five.";
    }

    return buildResult(
        "Chi-square independence",
        statistic,
        df,
        p,
        alpha,
        static_cast<std::size_t>(total),
        v,
        message
    );
}

TestResult oneProportionTest(
    int successes,
    int trials,
    double p0,
    double alpha = 0.05
) {
    validateAlpha(alpha);

    if (
        trials <= 0 ||
        successes < 0 ||
        successes > trials ||
        !std::isfinite(p0) ||
        p0 <= 0 ||
        p0 >= 1
    ) {
        throw StatisticalError(
            "Invalid one-proportion test inputs."
        );
    }

    const double observed =
        static_cast<double>(successes) / trials;

    const double se = std::sqrt(
        p0 * (1 - p0) / trials
    );

    const double z = (observed - p0) / se;
    const double p = normalTwoSidedPValue(z);

    return buildResult(
        "One-sample proportion z-test",
        z,
        0,
        p,
        alpha,
        trials,
        observed - p0,
        p < alpha
            ? "Population proportion differs from hypothesized value."
            : "Insufficient evidence of a proportion difference."
    );
}

TestResult twoProportionTest(
    int x1,
    int n1,
    int x2,
    int n2,
    double alpha = 0.05
) {
    validateAlpha(alpha);

    if (
        n1 <= 0 || n2 <= 0 ||
        x1 < 0 || x1 > n1 ||
        x2 < 0 || x2 > n2
    ) {
        throw StatisticalError(
            "Invalid two-proportion test inputs."
        );
    }

    const double p1 = static_cast<double>(x1) / n1;
    const double p2 = static_cast<double>(x2) / n2;

    const double pooled =
        static_cast<double>(x1 + x2) / (n1 + n2);

    if (pooled == 0 || pooled == 1) {
        throw StatisticalError("Pooled variance is zero.");
    }

    const double se = std::sqrt(
        pooled * (1 - pooled) *
        (1.0 / n1 + 1.0 / n2)
    );

    const double z = (p1 - p2) / se;
    const double p = normalTwoSidedPValue(z);

    return buildResult(
        "Two-sample proportion z-test",
        z,
        0,
        p,
        alpha,
        static_cast<std::size_t>(n1 + n2),
        p1 - p2,
        p < alpha
            ? "Population proportions differ significantly."
            : "Insufficient evidence of a difference."
    );
}

class AnalysisEngine {
private:
    double alpha_;
    std::vector<TestResult> results_;

public:
    explicit AnalysisEngine(double alpha = 0.05)
        : alpha_(alpha) {
        validateAlpha(alpha_);
    }

    template <typename Function>
    void execute(Function operation) {
        // Each successful operation produces an immutable result
        // that is stored for reporting.
        TestResult result = operation(alpha_);
        results_.push_back(std::move(result));
    }

    const std::vector<TestResult>& results() const {
        return results_;
    }

    void printReport() const {
        std::cout << "\nSTATISTICAL ANALYSIS REPORT\n";

        std::cout << std::left
                  << std::setw(37) << "Test"
                  << std::setw(14) << "Statistic"
                  << std::setw(14) << "P-value"
                  << std::setw(12) << "Reject H0"
                  << '\n';

        std::cout << std::string(77, '-') << '\n';

        for (const auto& result : results_) {
            std::cout
                << std::left
                << std::setw(37) << result.testName
                << std::setw(14) << result.statistic
                << std::setw(14) << result.pValue
                << std::setw(12)
                << (result.rejectNull ? "Yes" : "No")
                << '\n';

            std::cout
                << "  " << result.interpretation
                << "\n";
        }
    }
};

void runTests() {
    const double reference =
        chiSquarePValue(3.8414588207, 1);

    if (std::abs(reference - 0.05) > 1e-7) {
        throw StatisticalError(
            "Chi-square reference test failed."
        );
    }

    if (
        goodnessOfFit({50, 50}, {50, 50}).statistic != 0
    ) {
        throw StatisticalError("Goodness-of-fit test failed.");
    }

    if (
        independenceTest({{10, 10}, {10, 10}}).statistic != 0
    ) {
        throw StatisticalError("Independence test failed.");
    }

    if (oneProportionTest(50, 100, 0.5).statistic != 0) {
        throw StatisticalError("One-proportion test failed.");
    }

    if (twoProportionTest(50, 100, 50, 100).statistic != 0) {
        throw StatisticalError("Two-proportion test failed.");
    }

    bool rejected = false;

    try {
        goodnessOfFit({10, 20}, {15, 15});
    } catch (const StatisticalError&) {
        rejected = true;
    }

    if (!rejected) {
        throw StatisticalError(
            "Invalid expected frequencies were accepted."
        );
    }

    std::cout << "All C++ statistical tests passed.\n";
}

} // namespace statistics

int main() {
    using namespace statistics;

    try {
        runTests();

        AnalysisEngine engine(0.05);

        engine.execute([](double alpha) {
            return goodnessOfFit(
                {48, 52, 45, 55},
                {50, 50, 50, 50},
                alpha
            );
        });

        engine.execute([](double alpha) {
            return independenceTest(
                {{40, 20}, {15, 45}},
                alpha
            );
        });

        engine.execute([](double alpha) {
            return independenceTest(
                {{40, 20}, {15, 45}},
                alpha,
                true
            );
        });

        engine.execute([](double alpha) {
            return oneProportionTest(
                120, 200, 0.50, alpha
            );
        });

        engine.execute([](double alpha) {
            return twoProportionTest(
                140, 200, 110, 200, alpha
            );
        });

        engine.printReport();

    } catch (const std::exception& error) {
        std::cerr
            << "Statistical processing error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
