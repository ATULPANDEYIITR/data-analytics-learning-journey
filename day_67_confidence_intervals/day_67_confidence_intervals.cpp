#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class IntervalMethod {
    Normal,
    StudentT,
    Wilson,
    Bootstrap
};

struct ConfidenceInterval {
    double estimate;
    double lower;
    double upper;
    double confidence;
    double marginOfError;
    IntervalMethod method;
    size_t sampleSize;

    double width() const {
        return upper - lower;
    }

    bool contains(double value) const {
        return value >= lower && value <= upper;
    }
};

class ConfidenceIntervalEngine {
private:
    static const vector<double>& t95Table() {
        static const vector<double> values = {
            12.706, 4.303, 3.182, 2.776, 2.571,
            2.447, 2.365, 2.306, 2.262, 2.228,
            2.201, 2.179, 2.160, 2.145, 2.131,
            2.120, 2.110, 2.101, 2.093, 2.086,
            2.080, 2.074, 2.069, 2.064, 2.060,
            2.056, 2.052, 2.048, 2.045, 2.042
        };
        return values;
    }

    static void validateConfidence(double confidence) {
        if (!isfinite(confidence) ||
            confidence <= 0.0 ||
            confidence >= 1.0) {
            throw invalid_argument(
                "Confidence must be strictly between zero and one."
            );
        }
    }

    static void validateSample(
        const vector<double>& values,
        size_t minimum = 1
    ) {
        if (values.size() < minimum) {
            throw invalid_argument("Insufficient sample observations.");
        }

        for (double value : values) {
            if (!isfinite(value)) {
                throw invalid_argument(
                    "Sample contains non-finite observations."
                );
            }
        }
    }

    static double normalCDFInverse(double p) {
        if (p <= 0.0 || p >= 1.0) {
            throw invalid_argument("Probability must be between zero and one.");
        }

        const double a[] = {
            -39.69683028665376,
            220.9460984245205,
            -275.9285104469687,
            138.3577518672690,
            -30.66479806614716,
            2.506628277459239
        };

        const double b[] = {
            -54.47609879822406,
            161.5858368580409,
            -155.6989798598866,
            66.80131188771972,
            -13.28068155288572
        };

        const double c[] = {
            -0.007784894002430293,
            -0.3223964580411365,
            -2.400758277161838,
            -2.549732539343734,
            4.374664141464968,
            2.938163982698783
        };

        const double d[] = {
            0.007784695709041462,
            0.3224671290700398,
            2.445134137142996,
            3.754408661907416
        };

        const double low = 0.02425;
        const double high = 1.0 - low;

        if (p < low) {
            double q = sqrt(-2.0 * log(p));

            return -(
                (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
                    + c[4]) * q + c[5]) /
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
            );
        }

        if (p > high) {
            double q = sqrt(-2.0 * log(1.0 - p));

            return (
                (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
                    + c[4]) * q + c[5]) /
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
            );
        }

        double q = p - 0.5;
        double r = q * q;

        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r
                + a[4]) * r + a[5]) * q /
            (((((b[0] * r + b[1]) * r + b[2]) * r
                + b[3]) * r + b[4]) * r + 1.0)
        );
    }

    static double quantile(vector<double> values, double p) {
        if (values.empty() || p < 0.0 || p > 1.0) {
            throw invalid_argument("Invalid quantile input.");
        }

        sort(values.begin(), values.end());

        double position = p * (values.size() - 1);
        size_t lower = static_cast<size_t>(floor(position));
        size_t upper = static_cast<size_t>(ceil(position));

        double weight = position - lower;

        return values[lower] * (1.0 - weight)
            + values[upper] * weight;
    }

    static ConfidenceInterval build(
        double estimate,
        double lower,
        double upper,
        double confidence,
        IntervalMethod method,
        size_t sampleSize
    ) {
        if (!isfinite(estimate) ||
            !isfinite(lower) ||
            !isfinite(upper) ||
            lower > upper) {
            throw runtime_error("Invalid confidence interval.");
        }

        return {
            estimate,
            lower,
            upper,
            confidence,
            (upper - lower) / 2.0,
            method,
            sampleSize
        };
    }

public:
    static double mean(const vector<double>& values) {
        validateSample(values);

        return accumulate(values.begin(), values.end(), 0.0)
            / static_cast<double>(values.size());
    }

    static double sampleVariance(const vector<double>& values) {
        validateSample(values, 2);

        double average = mean(values);
        double sum = 0.0;

        for (double value : values) {
            double difference = value - average;
            sum += difference * difference;
        }

        return sum / static_cast<double>(values.size() - 1);
    }

    static double standardDeviation(const vector<double>& values) {
        return sqrt(sampleVariance(values));
    }

    static double normalCritical(double confidence) {
        validateConfidence(confidence);

        return normalCDFInverse(0.5 + confidence / 2.0);
    }

    static double tCritical95(size_t degreesOfFreedom) {
        if (degreesOfFreedom == 0) {
            throw invalid_argument("Degrees of freedom must be positive.");
        }

        const auto& table = t95Table();

        if (degreesOfFreedom <= table.size()) {
            return table[degreesOfFreedom - 1];
        }

        return normalCritical(0.95);
    }

    static ConfidenceInterval normalMean(
        const vector<double>& values,
        double confidence = 0.95,
        double populationSD = -1.0
    ) {
        validateSample(values, 2);
        validateConfidence(confidence);

        double sd = populationSD >= 0.0
            ? populationSD
            : standardDeviation(values);

        if (!isfinite(sd) || sd < 0.0) {
            throw invalid_argument("Invalid population standard deviation.");
        }

        double estimate = mean(values);
        double standardError = sd / sqrt(values.size());
        double margin = normalCritical(confidence) * standardError;

        return build(
            estimate,
            estimate - margin,
            estimate + margin,
            confidence,
            IntervalMethod::Normal,
            values.size()
        );
    }

    static ConfidenceInterval studentT(
        const vector<double>& values,
        double confidence = 0.95
    ) {
        validateSample(values, 2);
        validateConfidence(confidence);

        if (confidence != 0.95) {
            throw invalid_argument(
                "Student t table supports 95% confidence only."
            );
        }

        double estimate = mean(values);
        double standardError = standardDeviation(values) / sqrt(values.size());
        double margin = tCritical95(values.size() - 1) * standardError;

        return build(
            estimate,
            estimate - margin,
            estimate + margin,
            confidence,
            IntervalMethod::StudentT,
            values.size()
        );
    }

    static ConfidenceInterval wilson(
        size_t successes,
        size_t trials,
        double confidence = 0.95
    ) {
        validateConfidence(confidence);

        if (trials == 0 || successes > trials) {
            throw invalid_argument("Invalid binomial counts.");
        }

        double p = static_cast<double>(successes) / trials;
        double z = normalCritical(confidence);
        double z2 = z * z;

        double denominator = 1.0 + z2 / trials;

        double center =
            (p + z2 / (2.0 * trials)) / denominator;

        double adjustment =
            z * sqrt(
                p * (1.0 - p) / trials
                + z2 / (4.0 * trials * trials)
            ) / denominator;

        return build(
            p,
            max(0.0, center - adjustment),
            min(1.0, center + adjustment),
            confidence,
            IntervalMethod::Wilson,
            trials
        );
    }

    static ConfidenceInterval bootstrap(
        const vector<double>& values,
        size_t repetitions = 10000,
        double confidence = 0.95,
        uint32_t seed = 42
    ) {
        validateSample(values, 2);
        validateConfidence(confidence);

        if (repetitions < 100) {
            throw invalid_argument(
                "At least 100 bootstrap repetitions are required."
            );
        }

        mt19937 generator(seed);
        uniform_int_distribution<size_t> distribution(
            0, values.size() - 1
        );

        vector<double> estimates;
        estimates.reserve(repetitions);

        vector<double> sample(values.size());

        for (size_t iteration = 0; iteration < repetitions; ++iteration) {
            for (double& value : sample) {
                value = values[distribution(generator)];
            }

            estimates.push_back(mean(sample));
        }

        double estimate = mean(values);
        double alpha = (1.0 - confidence) / 2.0;

        double lower = quantile(estimates, alpha);
        double upper = quantile(estimates, 1.0 - alpha);

        return build(
            estimate,
            lower,
            upper,
            confidence,
            IntervalMethod::Bootstrap,
            values.size()
        );
    }

    static double marginOfError(
        double populationSD,
        size_t sampleSize,
        double confidence = 0.95
    ) {
        validateConfidence(confidence);

        if (!isfinite(populationSD) || populationSD < 0.0 ||
            sampleSize == 0) {
            throw invalid_argument("Invalid margin-of-error parameters.");
        }

        return normalCritical(confidence)
            * populationSD / sqrt(sampleSize);
    }

    static size_t requiredSampleSize(
        double populationSD,
        double desiredMargin,
        double confidence = 0.95
    ) {
        validateConfidence(confidence);

        if (!isfinite(populationSD) || populationSD < 0.0 ||
            !isfinite(desiredMargin) || desiredMargin <= 0.0) {
            throw invalid_argument("Invalid sample-size parameters.");
        }

        double required = pow(
            normalCritical(confidence) * populationSD / desiredMargin,
            2.0
        );

        if (required > static_cast<double>(
            numeric_limits<size_t>::max()
        )) {
            throw overflow_error("Required sample size exceeds capacity.");
        }

        return static_cast<size_t>(ceil(required));
    }
};

string methodName(IntervalMethod method) {
    switch (method) {
        case IntervalMethod::Normal:
            return "Normal mean";
        case IntervalMethod::StudentT:
            return "Student t";
        case IntervalMethod::Wilson:
            return "Wilson proportion";
        case IntervalMethod::Bootstrap:
            return "Bootstrap percentile";
    }

    return "Unknown";
}

void display(const ConfidenceInterval& interval) {
    cout << left << setw(22) << methodName(interval.method)
         << " Estimate: " << setw(10) << interval.estimate
         << " CI: [" << interval.lower << ", " << interval.upper << "]"
         << " MOE: " << interval.marginOfError
         << " n=" << interval.sampleSize << '\n';
}

void runTests() {
    vector<double> data = {12, 14, 15, 13, 16, 18, 14, 15, 17, 16};

    auto interval = ConfidenceIntervalEngine::studentT(data);

    if (!(interval.lower < interval.estimate &&
          interval.estimate < interval.upper)) {
        throw runtime_error("Student t test failed.");
    }

    auto proportion = ConfidenceIntervalEngine::wilson(72, 100);

    if (proportion.lower < 0.0 ||
        proportion.upper > 1.0 ||
        !proportion.contains(proportion.estimate)) {
        throw runtime_error("Wilson interval test failed.");
    }

    auto bootstrap = ConfidenceIntervalEngine::bootstrap(
        data, 1000, 0.95, 42
    );

    if (!bootstrap.contains(bootstrap.estimate)) {
        throw runtime_error("Bootstrap test failed.");
    }

    if (ConfidenceIntervalEngine::requiredSampleSize(10, 2) != 97) {
        throw runtime_error("Sample-size test failed.");
    }

    bool rejected = false;

    try {
        ConfidenceIntervalEngine::wilson(110, 100);
    } catch (const invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw runtime_error("Invalid count test failed.");
    }

    cout << "All tests passed.\n";
}

int main() {
    try {
        cout << fixed << setprecision(4);

        vector<double> responseTimes = {
            12.4, 13.1, 11.8, 14.2, 12.9,
            13.7, 12.1, 14.0, 13.3, 12.7,
            11.9, 13.5, 14.1, 12.6, 13.0
        };

        cout << "CONFIDENCE INTERVAL ANALYSIS\n";
        cout << string(65, '=') << '\n';

        cout << "\n1. Point estimates\n";
        cout << "Mean: "
             << ConfidenceIntervalEngine::mean(responseTimes) << '\n';

        cout << "Standard deviation: "
             << ConfidenceIntervalEngine::standardDeviation(responseTimes)
             << '\n';

        cout << "\n2. Mean intervals\n";

        auto normal =
            ConfidenceIntervalEngine::normalMean(responseTimes);

        auto student =
            ConfidenceIntervalEngine::studentT(responseTimes);

        display(normal);
        display(student);

        cout << "\n3. Conversion proportion\n";

        auto conversion =
            ConfidenceIntervalEngine::wilson(735, 1000);

        display(conversion);

        cout << "\n4. Bootstrap interval\n";

        auto bootstrap =
            ConfidenceIntervalEngine::bootstrap(responseTimes, 5000);

        display(bootstrap);

        cout << "\n5. Margin of error\n";

        cout << ConfidenceIntervalEngine::marginOfError(10, 100)
             << '\n';

        cout << "\n6. Required sample size\n";

        cout << ConfidenceIntervalEngine::requiredSampleSize(10, 2)
             << '\n';

        cout << "\n7. Repeated-sampling interpretation\n";
        cout << "A 95% confidence procedure captures the fixed population "
             << "parameter in approximately 95% of repeated samples "
             << "when its assumptions hold.\n";

        cout << "\n8. Validation tests\n";
        runTests();

    } catch (const exception& error) {
        cerr << "Analysis error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
