#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Alternative {
    TWO_SIDED,
    GREATER,
    LESS
};

enum class Decision {
    REJECT_H0,
    FAIL_TO_REJECT_H0
};

struct Hypothesis {
    string name;
    double nullMean;
    double alpha;
    Alternative alternative;

    void validate() const {
        if (name.empty()) {
            throw invalid_argument("Hypothesis name is required.");
        }

        if (!isfinite(nullMean)) {
            throw invalid_argument("Null mean must be finite.");
        }

        if (!(alpha > 0.0 && alpha < 1.0)) {
            throw invalid_argument("Alpha must be between 0 and 1.");
        }
    }
};

struct TestResult {
    string testName;
    size_t sampleSize;
    double sampleMean;
    double standardError;
    double statistic;
    double pValue;
    double alpha;
    double effect;
    double ciLower;
    double ciUpper;
    Decision decision;
};

class Statistics {
public:
    static void validateSample(const vector<double>& data) {
        if (data.size() < 2) {
            throw invalid_argument(
                "At least two observations are required."
            );
        }

        for (double value : data) {
            if (!isfinite(value)) {
                throw invalid_argument(
                    "Sample contains a non-finite value."
                );
            }
        }
    }

    static double mean(const vector<double>& data) {
        validateSample(data);

        return accumulate(
            data.begin(),
            data.end(),
            0.0
        ) / static_cast<double>(data.size());
    }

    static double sampleVariance(const vector<double>& data) {
        validateSample(data);

        double average = mean(data);
        double squaredDifference = 0.0;

        for (double value : data) {
            double difference = value - average;
            squaredDifference += difference * difference;
        }

        return squaredDifference /
            static_cast<double>(data.size() - 1);
    }

    static double normalCDF(double x) {
        return 0.5 * erfc(-x / sqrt(2.0));
    }

    static double normalPValue(
        double z,
        Alternative alternative
    ) {
        switch (alternative) {
            case Alternative::TWO_SIDED:
                return erfc(abs(z) / sqrt(2.0));

            case Alternative::GREATER:
                return normalCDF(-z);

            case Alternative::LESS:
                return normalCDF(z);
        }

        throw invalid_argument("Unknown alternative.");
    }

    static double criticalValue(double alpha) {
        // Binary search for the two-sided normal critical value.
        double low = 0.0;
        double high = 10.0;

        for (int i = 0; i < 120; ++i) {
            double mid = (low + high) / 2.0;

            double tailProbability =
                2.0 * (1.0 - normalCDF(mid));

            if (tailProbability > alpha) {
                low = mid;
            } else {
                high = mid;
            }
        }

        return (low + high) / 2.0;
    }
};

class HypothesisTestingEngine {
public:
    static TestResult oneSampleZTest(
        const vector<double>& sample,
        const Hypothesis& hypothesis,
        double populationStd
    ) {
        hypothesis.validate();
        Statistics::validateSample(sample);

        if (!isfinite(populationStd) || populationStd <= 0) {
            throw invalid_argument(
                "Population standard deviation must be positive."
            );
        }

        double average = Statistics::mean(sample);

        double standardError =
            populationStd / sqrt(
                static_cast<double>(sample.size())
            );

        double z = (
            average - hypothesis.nullMean
        ) / standardError;

        double pValue = Statistics::normalPValue(
            z,
            hypothesis.alternative
        );

        double critical = Statistics::criticalValue(
            hypothesis.alpha
        );

        double lower = -numeric_limits<double>::infinity();
        double upper = numeric_limits<double>::infinity();

        if (hypothesis.alternative == Alternative::TWO_SIDED) {
            lower = average - critical * standardError;
            upper = average + critical * standardError;
        } else if (hypothesis.alternative == Alternative::GREATER) {
            lower = average - critical * standardError;
        } else {
            upper = average + critical * standardError;
        }

        return {
            "One-sample Z-test",
            sample.size(),
            average,
            standardError,
            z,
            pValue,
            hypothesis.alpha,
            average - hypothesis.nullMean,
            lower,
            upper,
            pValue < hypothesis.alpha
                ? Decision::REJECT_H0
                : Decision::FAIL_TO_REJECT_H0
        };
    }

    static TestResult twoSampleZTest(
        const vector<double>& control,
        const vector<double>& treatment,
        double alpha = 0.05,
        Alternative alternative = Alternative::TWO_SIDED
    ) {
        Statistics::validateSample(control);
        Statistics::validateSample(treatment);

        if (!(alpha > 0 && alpha < 1)) {
            throw invalid_argument("Invalid alpha.");
        }

        double controlMean = Statistics::mean(control);
        double treatmentMean = Statistics::mean(treatment);

        double controlStd = sqrt(
            Statistics::sampleVariance(control)
        );

        double treatmentStd = sqrt(
            Statistics::sampleVariance(treatment)
        );

        double standardError = sqrt(
            controlStd * controlStd / control.size() +
            treatmentStd * treatmentStd / treatment.size()
        );

        double difference = treatmentMean - controlMean;

        double z = standardError == 0
            ? (difference == 0
                ? 0
                : copysign(
                    numeric_limits<double>::infinity(),
                    difference
                ))
            : difference / standardError;

        double pValue = Statistics::normalPValue(
            z,
            alternative
        );

        double critical = Statistics::criticalValue(alpha);

        return {
            "Independent two-sample large-sample Z approximation",
            control.size() + treatment.size(),
            treatmentMean,
            standardError,
            z,
            pValue,
            alpha,
            difference,
            difference - critical * standardError,
            difference + critical * standardError,
            pValue < alpha
                ? Decision::REJECT_H0
                : Decision::FAIL_TO_REJECT_H0
        };
    }
};

struct ErrorAnalysis {
    double alpha;
    double beta;
    double power;
};

class PowerAnalysis {
public:
    static ErrorAnalysis calculate(
        double nullMean,
        double trueMean,
        double populationStd,
        size_t sampleSize,
        double alpha
    ) {
        if (
            populationStd <= 0 ||
            sampleSize < 2 ||
            !(alpha > 0 && alpha < 1)
        ) {
            throw invalid_argument(
                "Invalid power analysis parameters."
            );
        }

        double standardError =
            populationStd / sqrt(
                static_cast<double>(sampleSize)
            );

        double critical = Statistics::criticalValue(alpha);

        double lower = nullMean - critical * standardError;
        double upper = nullMean + critical * standardError;

        double beta =
            Statistics::normalCDF(
                (upper - trueMean) / standardError
            ) -
            Statistics::normalCDF(
                (lower - trueMean) / standardError
            );

        return {
            alpha,
            beta,
            1.0 - beta
        };
    }
};

class Report {
public:
    static void print(const TestResult& result) {
        cout << "\nTest: " << result.testName << '\n';
        cout << "Sample size: " << result.sampleSize << '\n';
        cout << "Mean: " << result.sampleMean << '\n';
        cout << "Standard error: " << result.standardError << '\n';
        cout << "Statistic: " << result.statistic << '\n';
        cout << "P-value: " << result.pValue << '\n';
        cout << "Alpha: " << result.alpha << '\n';
        cout << "Effect estimate: " << result.effect << '\n';

        cout << "Confidence interval: ["
             << result.ciLower << ", "
             << result.ciUpper << "]\n";

        cout << "Decision: "
             << (
                 result.decision == Decision::REJECT_H0
                     ? "Reject H0"
                     : "Fail to reject H0"
             )
             << '\n';
    }

    static void saveCSV(
        const TestResult& result,
        const string& filename
    ) {
        if (
            filename.empty() ||
            filename.find_first_of("/\\") != string::npos
        ) {
            throw invalid_argument("Invalid output filename.");
        }

        ofstream file(filename);

        if (!file) {
            throw runtime_error("Unable to create report.");
        }

        file << "test,sample_size,statistic,p_value,alpha,effect,decision\n";

        file << result.testName << ','
             << result.sampleSize << ','
             << setprecision(12) << result.statistic << ','
             << result.pValue << ','
             << result.alpha << ','
             << result.effect << ','
             << (
                 result.decision == Decision::REJECT_H0
                     ? "REJECT_H0"
                     : "FAIL_TO_REJECT_H0"
             )
             << '\n';

        if (!file.good()) {
            throw runtime_error("Failed while writing report.");
        }
    }
};

int main() {
    try {
        cout << fixed << setprecision(6);

        vector<double> productionMeasurements = {
            52.1, 50.8, 53.2, 51.7,
            54.0, 52.9, 51.4, 53.5,
            52.4, 54.1, 51.9, 53.0
        };

        Hypothesis hypothesis {
            "Production process mean",
            50.0,
            0.05,
            Alternative::TWO_SIDED
        };

        TestResult result =
            HypothesisTestingEngine::oneSampleZTest(
                productionMeasurements,
                hypothesis,
                3.0
            );

        cout << "HYPOTHESIS TESTING ENGINE\n";
        cout << "=========================\n";

        cout << "\nH0: Population mean = 50\n";
        cout << "H1: Population mean != 50\n";

        Report::print(result);

        vector<double> control = {
            48, 50, 52, 49, 51, 50, 53, 48, 49, 51
        };

        vector<double> treatment = {
            53, 55, 54, 52, 56, 53, 55, 54, 52, 56
        };

        TestResult comparison =
            HypothesisTestingEngine::twoSampleZTest(
                control,
                treatment
            );

        cout << "\nGROUP COMPARISON";
        Report::print(comparison);

        ErrorAnalysis errors = PowerAnalysis::calculate(
            50.0,
            52.0,
            3.0,
            30,
            0.05
        );

        cout << "\nERROR AND POWER ANALYSIS\n";
        cout << "Type I error limit: " << errors.alpha << '\n';
        cout << "Type II error probability: " << errors.beta << '\n';
        cout << "Statistical power: " << errors.power << '\n';

        Report::saveCSV(
            result,
            "hypothesis_test_report.csv"
        );

        cout << "\nReport saved successfully.\n";

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
