#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Statistical Tests I
 * C++17 implementation of one-sample, independent,
 * pooled independent, and paired Student's t-tests.
 */

enum class TestType {
    OneSample,
    Welch,
    Pooled,
    Paired
};

string testName(TestType type) {
    switch (type) {
        case TestType::OneSample:
            return "One-sample t-test";
        case TestType::Welch:
            return "Independent Welch t-test";
        case TestType::Pooled:
            return "Independent pooled t-test";
        case TestType::Paired:
            return "Paired t-test";
    }

    throw invalid_argument("Unknown test type.");
}

struct TestResult {
    string name;
    double statistic;
    double degreesOfFreedom;
    double pValue;
    double alpha;
    int sampleSize;
    double meanDifference;
    bool significant;
};

class Statistics {
public:
    static void validateAlpha(double alpha) {
        if (!isfinite(alpha) || alpha <= 0 || alpha >= 1) {
            throw invalid_argument(
                "Alpha must be between zero and one."
            );
        }
    }

    static vector<double> validate(
        const vector<double>& values,
        const string& name
    ) {
        if (values.size() < 2) {
            throw invalid_argument(
                name + " requires at least two observations."
            );
        }

        for (double value : values) {
            if (!isfinite(value)) {
                throw invalid_argument(
                    name + " contains a non-finite observation."
                );
            }
        }

        return values;
    }

    static double average(const vector<double>& values) {
        return accumulate(
            values.begin(),
            values.end(),
            0.0
        ) / values.size();
    }

    static double variance(const vector<double>& values) {
        double center = average(values);
        double sum = 0.0;

        for (double value : values) {
            sum += (value - center) * (value - center);
        }

        return sum / (values.size() - 1);
    }

    static double logGamma(double z) {
        static const double coefficients[] = {
            676.5203681218851,
            -1259.1392167224028,
            771.3234287776531,
            -176.6150291621406,
            12.507343278686905,
            -0.13857109526572012,
            9.984369578019572e-6,
            1.5056327351493116e-7
        };

        if (z < 0.5) {
            return log(M_PI) -
                log(abs(sin(M_PI * z))) -
                logGamma(1.0 - z);
        }

        z -= 1.0;

        double x = 0.99999999999980993;

        for (int i = 0; i < 8; ++i) {
            x += coefficients[i] / (z + i + 1.0);
        }

        double t = z + 7.5;

        return 0.5 * log(2.0 * M_PI)
            + (z + 0.5) * log(t)
            - t
            + log(x);
    }

    static double betaFraction(
        double a,
        double b,
        double x
    ) {
        const int maximumIterations = 300;
        const double epsilon = 3e-14;
        const double tiny = 1e-300;

        double qab = a + b;
        double qap = a + 1.0;
        double qam = a - 1.0;

        double c = 1.0;
        double d = 1.0 - qab * x / qap;

        if (abs(d) < tiny) d = tiny;

        d = 1.0 / d;

        double h = d;

        for (int m = 1; m <= maximumIterations; ++m) {
            int m2 = 2 * m;

            double aa = m * (b - m) * x /
                ((qam + m2) * (a + m2));

            d = 1.0 + aa * d;
            if (abs(d) < tiny) d = tiny;

            c = 1.0 + aa / c;
            if (abs(c) < tiny) c = tiny;

            d = 1.0 / d;
            h *= d * c;

            aa = -((a + m) * (qab + m) * x) /
                ((a + m2) * (qap + m2));

            d = 1.0 + aa * d;
            if (abs(d) < tiny) d = tiny;

            c = 1.0 + aa / c;
            if (abs(c) < tiny) c = tiny;

            d = 1.0 / d;

            double delta = d * c;
            h *= delta;

            if (abs(delta - 1.0) < epsilon) {
                return h;
            }
        }

        throw runtime_error(
            "Incomplete beta calculation did not converge."
        );
    }

    static double regularizedBeta(
        double x,
        double a,
        double b
    ) {
        if (a <= 0 || b <= 0) {
            throw invalid_argument(
                "Beta parameters must be positive."
            );
        }

        if (x <= 0) return 0.0;
        if (x >= 1) return 1.0;

        double front = exp(
            logGamma(a + b)
            - logGamma(a)
            - logGamma(b)
            + a * log(x)
            + b * log1p(-x)
        );

        if (x < (a + 1.0) / (a + b + 2.0)) {
            return front * betaFraction(a, b, x) / a;
        }

        return 1.0 -
            front * betaFraction(b, a, 1.0 - x) / b;
    }

    static double studentTPValue(
        double statistic,
        double df
    ) {
        if (df <= 0 || !isfinite(df)) {
            throw invalid_argument(
                "Degrees of freedom must be positive."
            );
        }

        double x = df / (df + statistic * statistic);

        return regularizedBeta(x, df / 2.0, 0.5);
    }

    static TestResult createResult(
        TestType type,
        double statistic,
        double df,
        double pValue,
        double alpha,
        int sampleSize,
        double difference
    ) {
        return {
            testName(type),
            statistic,
            df,
            pValue,
            alpha,
            sampleSize,
            difference,
            pValue < alpha
        };
    }

    static TestResult oneSample(
        const vector<double>& sample,
        double populationMean,
        double alpha = 0.05
    ) {
        auto data = validate(sample, "Sample");
        validateAlpha(alpha);

        if (!isfinite(populationMean)) {
            throw invalid_argument(
                "Population mean must be finite."
            );
        }

        int n = static_cast<int>(data.size());

        double difference = average(data) - populationMean;
        double v = variance(data);

        if (v == 0) {
            if (difference == 0) {
                throw domain_error(
                    "The t-statistic is undefined."
                );
            }

            return createResult(
                TestType::OneSample,
                copysign(numeric_limits<double>::infinity(), difference),
                n - 1,
                0.0,
                alpha,
                n,
                difference
            );
        }

        double statistic = difference / sqrt(v / n);

        return createResult(
            TestType::OneSample,
            statistic,
            n - 1,
            studentTPValue(statistic, n - 1),
            alpha,
            n,
            difference
        );
    }

    static TestResult independent(
        const vector<double>& first,
        const vector<double>& second,
        bool equalVariance = false,
        double alpha = 0.05
    ) {
        auto a = validate(first, "First group");
        auto b = validate(second, "Second group");

        validateAlpha(alpha);

        double n1 = a.size();
        double n2 = b.size();

        double m1 = average(a);
        double m2 = average(b);

        double v1 = variance(a);
        double v2 = variance(b);

        double difference = m1 - m2;
        double standardError;
        double df;
        TestType type;

        if (equalVariance) {
            df = n1 + n2 - 2;

            double pooled = (
                (n1 - 1) * v1 +
                (n2 - 1) * v2
            ) / df;

            standardError = sqrt(
                pooled * (1.0 / n1 + 1.0 / n2)
            );

            type = TestType::Pooled;
        } else {
            double term1 = v1 / n1;
            double term2 = v2 / n2;

            standardError = sqrt(term1 + term2);

            double denominator =
                term1 * term1 / (n1 - 1)
                + term2 * term2 / (n2 - 1);

            df = (term1 + term2) *
                (term1 + term2) / denominator;

            type = TestType::Welch;
        }

        if (standardError == 0) {
            if (difference == 0) {
                throw domain_error(
                    "The t-statistic is undefined."
                );
            }

            return createResult(
                type,
                copysign(
                    numeric_limits<double>::infinity(),
                    difference
                ),
                df,
                0.0,
                alpha,
                static_cast<int>(n1 + n2),
                difference
            );
        }

        double statistic = difference / standardError;

        return createResult(
            type,
            statistic,
            df,
            studentTPValue(statistic, df),
            alpha,
            static_cast<int>(n1 + n2),
            difference
        );
    }

    static TestResult paired(
        const vector<double>& before,
        const vector<double>& after,
        double alpha = 0.05
    ) {
        auto x = validate(before, "Before");
        auto y = validate(after, "After");

        validateAlpha(alpha);

        if (x.size() != y.size()) {
            throw invalid_argument(
                "Paired samples must have equal lengths."
            );
        }

        vector<double> differences;

        for (size_t i = 0; i < x.size(); ++i) {
            differences.push_back(y[i] - x[i]);
        }

        int n = static_cast<int>(differences.size());

        double difference = average(differences);
        double v = variance(differences);

        if (v == 0) {
            if (difference == 0) {
                throw domain_error(
                    "All paired differences are zero."
                );
            }

            return createResult(
                TestType::Paired,
                copysign(
                    numeric_limits<double>::infinity(),
                    difference
                ),
                n - 1,
                0.0,
                alpha,
                n,
                difference
            );
        }

        double statistic = difference / sqrt(v / n);

        return createResult(
            TestType::Paired,
            statistic,
            n - 1,
            studentTPValue(statistic, n - 1),
            alpha,
            n,
            difference
        );
    }
};

class ReportManager {
private:
    vector<TestResult> results;

public:
    void add(const TestResult& result) {
        results.push_back(result);
    }

    void display() const {
        cout << fixed << setprecision(6);

        for (const auto& result : results) {
            cout << "\n" << result.name << "\n";

            cout << "t-statistic: "
                 << result.statistic << "\n";

            cout << "Degrees of freedom: "
                 << result.degreesOfFreedom << "\n";

            cout << "p-value: "
                 << result.pValue << "\n";

            cout << "Mean difference: "
                 << result.meanDifference << "\n";

            cout << "Alpha: "
                 << result.alpha << "\n";

            cout << "Decision: "
                 << (result.significant
                    ? "Reject H0"
                    : "Fail to reject H0")
                 << "\n";
        }
    }

    void exportCSV(const string& filename) const {
        // File names should be controlled by the application.
        // The CSV contains numerical results, not executable formulas.
        if (results.empty()) {
            throw runtime_error("No results available.");
        }

        ofstreamPlaceholder:
        FILE* file = fopen(filename.c_str(), "w");

        if (!file) {
            throw runtime_error("Could not open report file.");
        }

        fprintf(
            file,
            "test,statistic,df,p_value,alpha,sample_size,"
            "mean_difference,significant\n"
        );

        for (const auto& result : results) {
            fprintf(
                file,
                "\"%s\",%.12g,%.12g,%.12g,%.12g,%d,%.12g,%s\n",
                result.name.c_str(),
                result.statistic,
                result.degreesOfFreedom,
                result.pValue,
                result.alpha,
                result.sampleSize,
                result.meanDifference,
                result.significant ? "true" : "false"
            );
        }

        fclose(file);
    }
};

int main() {
    try {
        ReportManager reports;

        vector<double> deliveryTimes = {
            28, 31, 29, 32, 30, 27, 34, 31, 29, 30
        };

        reports.add(
            Statistics::oneSample(deliveryTimes, 30.0)
        );

        vector<double> control = {
            72, 75, 78, 74, 71, 80, 77, 76
        };

        vector<double> treatment = {
            81, 84, 79, 86, 82, 83, 85, 80
        };

        reports.add(
            Statistics::independent(
                control,
                treatment,
                false
            )
        );

        reports.add(
            Statistics::independent(
                control,
                treatment,
                true
            )
        );

        vector<double> before = {
            65, 70, 72, 68, 75, 71, 69, 73
        };

        vector<double> after = {
            72, 74, 76, 75, 79, 76, 74, 78
        };

        reports.add(
            Statistics::paired(before, after)
        );

        reports.display();

        reports.exportCSV("statistical_results.csv");

        // Numerical validation.
        if (abs(Statistics::studentTPValue(0.0, 10) - 1.0)
            > 1e-10) {
            throw runtime_error("Numerical validation failed.");
        }

        cout << "\nNumerical validation passed.\n";

        try {
            Statistics::paired({1, 2, 3}, {1, 2});
        } catch (const exception& error) {
            cout << "Expected validation: "
                 << error.what() << "\n";
        }

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
