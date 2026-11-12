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
 * Regression Fundamentals
 *
 * C++17 ordinary least squares implementation.
 *
 * Includes:
 * - Domain modeling
 * - OLS coefficient estimation
 * - Residual analysis
 * - Regression metrics
 * - Coefficient standard errors
 * - Confidence intervals
 * - Assumption indicators
 * - Validation and automated tests
 */

enum class ModelState {
    Unfitted,
    Fitted
};

struct Observation {
    double x;
    double y;
};

struct RegressionMetrics {
    double mae;
    double mse;
    double rmse;
    double rSquared;
    double adjustedRSquared;
    double residualStandardError;
};

struct PredictionResult {
    double actual;
    double predicted;
    double residual;
};

struct AssumptionDiagnostic {
    string name;
    double statistic;
    bool indicatorPassed;
    string interpretation;
};

class RegressionException : public runtime_error {
public:
    explicit RegressionException(const string& message)
        : runtime_error(message) {}
};

class SimpleLinearRegression {
private:
    vector<Observation> observations;
    vector<double> fittedValues;
    vector<double> residuals;

    double slope = 0.0;
    double intercept = 0.0;

    double xMean = 0.0;
    double yMean = 0.0;

    double sxx = 0.0;
    double syy = 0.0;
    double sse = 0.0;

    double tolerance = 1e-12;

    ModelState state = ModelState::Unfitted;

    void ensureFitted() const {
        if (state != ModelState::Fitted) {
            throw RegressionException(
                "Model must be fitted before this operation."
            );
        }
    }

    static double mean(const vector<double>& values) {
        if (values.empty()) {
            throw RegressionException("Cannot calculate empty mean.");
        }

        return accumulate(
            values.begin(),
            values.end(),
            0.0
        ) / values.size();
    }

    static double sampleVariance(const vector<double>& values) {
        if (values.size() < 2) return 0.0;

        const double avg = mean(values);

        double sum = 0.0;

        for (double value : values) {
            sum += (value - avg) * (value - avg);
        }

        return sum / (values.size() - 1);
    }

public:
    explicit SimpleLinearRegression(double varianceTolerance = 1e-12)
        : tolerance(varianceTolerance) {

        if (!isfinite(tolerance) || tolerance <= 0) {
            throw RegressionException(
                "Variance tolerance must be positive."
            );
        }
    }

    void fit(const vector<Observation>& data) {
        if (data.size() < 3) {
            throw RegressionException(
                "At least three observations are required."
            );
        }

        for (const auto& row : data) {
            if (!isfinite(row.x) || !isfinite(row.y)) {
                throw RegressionException(
                    "Dataset contains non-finite values."
                );
            }
        }

        vector<double> xValues;
        vector<double> yValues;

        xValues.reserve(data.size());
        yValues.reserve(data.size());

        for (const auto& row : data) {
            xValues.push_back(row.x);
            yValues.push_back(row.y);
        }

        const double localXMean = mean(xValues);
        const double localYMean = mean(yValues);

        double localSxx = 0.0;
        double localSyy = 0.0;
        double localSxy = 0.0;

        // Centered sums reduce numerical cancellation.
        for (const auto& row : data) {
            const double dx = row.x - localXMean;
            const double dy = row.y - localYMean;

            localSxx += dx * dx;
            localSyy += dy * dy;
            localSxy += dx * dy;
        }

        if (localSxx <= tolerance) {
            throw RegressionException(
                "Predictor has zero or near-zero variance."
            );
        }

        const double localSlope = localSxy / localSxx;
        const double localIntercept =
            localYMean - localSlope * localXMean;

        vector<double> localFitted;
        vector<double> localResiduals;

        localFitted.reserve(data.size());
        localResiduals.reserve(data.size());

        double localSse = 0.0;

        for (const auto& row : data) {
            const double prediction =
                localIntercept + localSlope * row.x;

            const double residual = row.y - prediction;

            localFitted.push_back(prediction);
            localResiduals.push_back(residual);

            localSse += residual * residual;
        }

        // Commit model state only after all calculations succeed.
        observations = data;
        fittedValues = move(localFitted);
        residuals = move(localResiduals);

        slope = localSlope;
        intercept = localIntercept;
        xMean = localXMean;
        yMean = localYMean;
        sxx = localSxx;
        syy = localSyy;
        sse = localSse;

        state = ModelState::Fitted;
    }

    double predict(double x) const {
        ensureFitted();

        if (!isfinite(x)) {
            throw RegressionException(
                "Prediction input must be finite."
            );
        }

        return intercept + slope * x;
    }

    vector<double> predict(
        const vector<double>& inputs
    ) const {

        ensureFitted();

        vector<double> result;
        result.reserve(inputs.size());

        for (double x : inputs) {
            result.push_back(predict(x));
        }

        return result;
    }

    RegressionMetrics calculateMetrics() const {
        ensureFitted();

        const size_t n = observations.size();

        double absoluteError = 0.0;

        for (double error : residuals) {
            absoluteError += abs(error);
        }

        const double rSquared =
            syy > tolerance
            ? 1.0 - sse / syy
            : (sse <= tolerance ? 1.0 : 0.0);

        const double mse = sse / n;

        const double adjustedRSquared =
            1.0 - (1.0 - rSquared) *
            static_cast<double>(n - 1) /
            static_cast<double>(n - 2);

        const double residualStandardError =
            sqrt(sse / (n - 2));

        return {
            absoluteError / n,
            mse,
            sqrt(mse),
            rSquared,
            adjustedRSquared,
            residualStandardError
        };
    }

    pair<double, double> coefficientStandardErrors() const {
        ensureFitted();

        const double n = observations.size();

        const double sigmaSquared = sse / (n - 2);

        const double slopeSE = sqrt(
            sigmaSquared / sxx
        );

        const double interceptSE = sqrt(
            sigmaSquared *
            (1.0 / n + xMean * xMean / sxx)
        );

        return {interceptSE, slopeSE};
    }

    pair<double, double> slopeConfidenceInterval(
        double criticalValue = 1.96
    ) const {

        ensureFitted();

        if (!isfinite(criticalValue) || criticalValue <= 0) {
            throw RegressionException(
                "Critical value must be positive."
            );
        }

        const auto errors = coefficientStandardErrors();
        const double slopeSE = errors.second;

        return {
            slope - criticalValue * slopeSE,
            slope + criticalValue * slopeSE
        };
    }

    vector<PredictionResult> getResidualReport() const {
        ensureFitted();

        vector<PredictionResult> report;
        report.reserve(observations.size());

        for (size_t i = 0; i < observations.size(); i++) {
            report.push_back({
                observations[i].y,
                fittedValues[i],
                residuals[i]
            });
        }

        return report;
    }

    vector<AssumptionDiagnostic> diagnose() const {
        ensureFitted();

        const size_t n = residuals.size();

        const double residualMean = mean(residuals);
        const double variance = sampleVariance(residuals);

        double skewness = 0.0;

        if (variance > 0) {
            for (double error : residuals) {
                skewness += pow(
                    (error - residualMean) / sqrt(variance),
                    3
                );
            }

            skewness /= n;
        }

        double lagNumerator = 0.0;
        double denominator = 0.0;

        for (size_t i = 0; i < n; i++) {
            denominator += residuals[i] * residuals[i];

            if (i > 0) {
                lagNumerator += residuals[i] * residuals[i - 1];
            }
        }

        const double lagCorrelation =
            denominator > 0
            ? lagNumerator / denominator
            : 0.0;

        vector<pair<double, double>> ordered;

        for (size_t i = 0; i < n; i++) {
            ordered.push_back({
                fittedValues[i],
                residuals[i]
            });
        }

        sort(
            ordered.begin(),
            ordered.end(),
            [](const auto& a, const auto& b) {
                return a.first < b.first;
            }
        );

        const size_t split = n / 2;

        vector<double> lowerErrors;
        vector<double> upperErrors;

        for (size_t i = 0; i < n; i++) {
            if (i < split) {
                lowerErrors.push_back(ordered[i].second);
            } else {
                upperErrors.push_back(ordered[i].second);
            }
        }

        const double lowerVariance = sampleVariance(lowerErrors);
        const double upperVariance = sampleVariance(upperErrors);

        const double varianceRatio =
            max(lowerVariance, upperVariance) /
            max(min(lowerVariance, upperVariance), 1e-15);

        return {
            {
                "Residual mean",
                abs(residualMean),
                abs(residualMean) < 1e-8,
                "OLS with an intercept produces approximately zero mean residuals."
            },
            {
                "Lag-one correlation",
                abs(lagCorrelation),
                abs(lagCorrelation) < 0.3,
                "Descriptive indicator of residual dependence."
            },
            {
                "Variance ratio",
                varianceRatio,
                varianceRatio < 4.0,
                "Compares residual spread across fitted-value groups."
            },
            {
                "Absolute skewness",
                abs(skewness),
                abs(skewness) < 1.0,
                "Descriptive indicator of residual symmetry."
            }
        };
    }

    void printReport() const {
        ensureFitted();

        const auto metrics = calculateMetrics();
        const auto errors = coefficientStandardErrors();
        const auto interval = slopeConfidenceInterval();

        cout << fixed << setprecision(6);

        cout << "\nREGRESSION MODEL\n";
        cout << "--------------------------------------\n";

        cout << "Equation: y = "
             << intercept << " + "
             << slope << "x\n";

        cout << "Observations: " << observations.size() << "\n";

        cout << "\nCOEFFICIENTS\n";
        cout << "Intercept: " << intercept << "\n";
        cout << "Slope: " << slope << "\n";
        cout << "Intercept SE: " << errors.first << "\n";
        cout << "Slope SE: " << errors.second << "\n";

        cout << "\nMETRICS\n";
        cout << "MAE: " << metrics.mae << "\n";
        cout << "MSE: " << metrics.mse << "\n";
        cout << "RMSE: " << metrics.rmse << "\n";
        cout << "R-squared: " << metrics.rSquared << "\n";
        cout << "Adjusted R-squared: "
             << metrics.adjustedRSquared << "\n";
        cout << "Residual standard error: "
             << metrics.residualStandardError << "\n";

        cout << "\nSLOPE CONFIDENCE INTERVAL\n";
        cout << "[" << interval.first
             << ", " << interval.second << "]\n";

        cout << "\nRESIDUAL REPORT\n";

        for (const auto& row : getResidualReport()) {
            cout << "Actual: " << row.actual
                 << ", Predicted: " << row.predicted
                 << ", Residual: " << row.residual
                 << "\n";
        }

        cout << "\nASSUMPTION INDICATORS\n";

        for (const auto& item : diagnose()) {
            cout << item.name
                 << ": " << item.statistic
                 << " | "
                 << (item.indicatorPassed ? "PASS" : "INVESTIGATE")
                 << "\n";

            cout << item.interpretation << "\n";
        }
    }

    double getSlope() const {
        ensureFitted();
        return slope;
    }

    double getIntercept() const {
        ensureFitted();
        return intercept;
    }

    ModelState getState() const {
        return state;
    }
};

void runTests() {
    SimpleLinearRegression model;

    model.fit({
        {1, 3},
        {2, 5},
        {3, 7},
        {4, 9},
        {5, 11}
    });

    if (abs(model.getSlope() - 2.0) > 1e-10) {
        throw RegressionException("Slope test failed.");
    }

    if (abs(model.getIntercept() - 1.0) > 1e-10) {
        throw RegressionException("Intercept test failed.");
    }

    if (abs(model.predict(6) - 13.0) > 1e-10) {
        throw RegressionException("Prediction test failed.");
    }

    if (abs(model.calculateMetrics().rSquared - 1.0) > 1e-10) {
        throw RegressionException("R-squared test failed.");
    }

    try {
        SimpleLinearRegression invalid;

        invalid.fit({
            {1, 2},
            {1, 3},
            {1, 4}
        });

        throw RegressionException(
            "Constant predictor was not rejected."
        );

    } catch (const RegressionException& error) {
        if (
            string(error.what()) ==
            "Constant predictor was not rejected."
        ) {
            throw;
        }
    }

    try {
        SimpleLinearRegression insufficient;

        insufficient.fit({
            {1, 2},
            {2, 3}
        });

        throw RegressionException(
            "Insufficient observations were accepted."
        );

    } catch (const RegressionException& error) {
        if (
            string(error.what()) ==
            "Insufficient observations were accepted."
        ) {
            throw;
        }
    }

    cout << "\nAll C++17 tests passed.\n";
}

int main() {
    try {
        vector<Observation> dataset = {
            {1, 42},
            {2, 46},
            {3, 53},
            {4, 57},
            {5, 61},
            {6, 68},
            {7, 72},
            {8, 79}
        };

        SimpleLinearRegression model;
        model.fit(dataset);

        model.printReport();

        cout << "\nNEW PREDICTIONS\n";

        for (double x : {2.5, 5.5, 9.0}) {
            cout << "X = " << x
                 << ", predicted Y = "
                 << model.predict(x)
                 << "\n";
        }

        runTests();

    } catch (const exception& error) {
        cerr << "Regression error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
