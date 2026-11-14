#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * C++17 Regression Diagnostics Engine
 *
 * Domain:
 * - Regression model estimation
 * - Multicollinearity assessment
 * - Heteroscedasticity testing
 * - Residual diagnostics
 * - Influence analysis
 * - HC3 robust standard errors
 *
 * Complexity:
 * O(n p^2 + p^3) for model fitting and matrix operations,
 * excluding auxiliary diagnostic regressions.
 */

using Matrix = vector<vector<double>>;

enum class Severity {
    PASS,
    WARNING,
    FAIL
};

struct Observation {
    string id;
    vector<double> features;
    double target;
};

struct Finding {
    string category;
    string subject;
    double statistic;
    double threshold;
    Severity severity;
    string explanation;
};

struct Policy {
    double vifWarning = 5.0;
    double vifCritical = 10.0;
    double bpAlpha = 0.05;
    double cookMultiplier = 4.0;
    double leverageMultiplier = 2.0;
    double studentizedLimit = 3.0;
};

double dot(const vector<double>& a,
           const vector<double>& b) {
    if (a.size() != b.size()) {
        throw runtime_error("Vector dimension mismatch.");
    }

    return inner_product(
        a.begin(), a.end(), b.begin(), 0.0
    );
}

double average(const vector<double>& values) {
    if (values.empty()) {
        throw runtime_error("Cannot calculate empty mean.");
    }

    return accumulate(
        values.begin(), values.end(), 0.0
    ) / values.size();
}

Matrix transpose(const Matrix& matrix) {
    if (matrix.empty()) return {};

    Matrix result(
        matrix[0].size(),
        vector<double>(matrix.size())
    );

    for (size_t i = 0; i < matrix.size(); ++i) {
        for (size_t j = 0; j < matrix[i].size(); ++j) {
            result[j][i] = matrix[i][j];
        }
    }

    return result;
}

Matrix multiply(const Matrix& a, const Matrix& b) {
    if (a.empty() || b.empty() ||
        a[0].size() != b.size()) {
        throw runtime_error("Invalid matrix multiplication.");
    }

    Matrix result(
        a.size(),
        vector<double>(b[0].size(), 0.0)
    );

    for (size_t i = 0; i < a.size(); ++i) {
        for (size_t k = 0; k < b.size(); ++k) {
            for (size_t j = 0; j < b[0].size(); ++j) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }

    return result;
}

vector<double> solve(Matrix matrix,
                     vector<double> rhs) {
    const size_t n = rhs.size();

    if (matrix.size() != n) {
        throw runtime_error("Invalid linear system.");
    }

    for (size_t i = 0; i < n; ++i) {
        if (matrix[i].size() != n) {
            throw runtime_error("Matrix must be square.");
        }
    }

    for (size_t col = 0; col < n; ++col) {
        size_t pivot = col;

        for (size_t row = col + 1; row < n; ++row) {
            if (abs(matrix[row][col]) >
                abs(matrix[pivot][col])) {
                pivot = row;
            }
        }

        if (abs(matrix[pivot][col]) < 1e-12) {
            throw runtime_error(
                "Singular matrix: perfect or severe multicollinearity."
            );
        }

        swap(matrix[col], matrix[pivot]);
        swap(rhs[col], rhs[pivot]);

        double divisor = matrix[col][col];

        for (size_t j = col; j < n; ++j) {
            matrix[col][j] /= divisor;
        }

        rhs[col] /= divisor;

        for (size_t row = 0; row < n; ++row) {
            if (row == col) continue;

            double factor = matrix[row][col];

            for (size_t j = col; j < n; ++j) {
                matrix[row][j] -=
                    factor * matrix[col][j];
            }

            rhs[row] -= factor * rhs[col];
        }
    }

    return rhs;
}

Matrix inverse(const Matrix& matrix) {
    size_t n = matrix.size();

    Matrix result(n, vector<double>(n));

    for (size_t col = 0; col < n; ++col) {
        vector<double> unit(n, 0.0);
        unit[col] = 1.0;

        vector<double> solution = solve(
            matrix, unit
        );

        for (size_t row = 0; row < n; ++row) {
            result[row][col] = solution[row];
        }
    }

    return result;
}

double chiSquareSurvival(double statistic,
                         int degrees) {
    if (statistic < 0 || degrees <= 0) {
        throw runtime_error(
            "Invalid chi-square distribution parameters."
        );
    }

    const double a = degrees / 2.0;
    const double x = statistic / 2.0;

    if (x == 0) return 1.0;

    const double logFactor =
        -x + a * log(x) - lgamma(a);

    const double factor = exp(logFactor);

    if (x < a + 1.0) {
        double ap = a;
        double term = 1.0 / a;
        double sum = term;

        for (int i = 0; i < 1000; ++i) {
            ap += 1.0;
            term *= x / ap;
            sum += term;

            if (abs(term) < abs(sum) * 1e-14) {
                break;
            }
        }

        return max(
            0.0,
            min(1.0, 1.0 - sum * factor)
        );
    }

    double b = x + 1.0 - a;
    double c = 1e300;
    double d = 1.0 / b;
    double h = d;

    for (int i = 1; i < 1000; ++i) {
        double an = -i * (i - a);
        b += 2.0;

        d = an * d + b;
        if (abs(d) < 1e-300) d = 1e-300;

        c = b + an / c;
        if (abs(c) < 1e-300) c = 1e-300;

        d = 1.0 / d;

        double delta = d * c;
        h *= delta;

        if (abs(delta - 1.0) < 1e-14) break;
    }

    return max(0.0, min(1.0, factor * h));
}

string severityName(Severity severity) {
    switch (severity) {
        case Severity::PASS: return "PASS";
        case Severity::WARNING: return "WARNING";
        case Severity::FAIL: return "FAIL";
    }

    return "UNKNOWN";
}

class RegressionEngine {
private:
    vector<Observation> observations;
    Matrix X;
    vector<double> y;
    vector<double> beta;
    vector<double> fitted;
    vector<double> residuals;
    Matrix xtxInverse;

    size_t n;
    size_t p;

    double sse = 0.0;
    double mse = 0.0;
    double rSquared = 0.0;

    bool fittedState = false;

    void validate() {
        if (observations.empty()) {
            throw runtime_error("Dataset is empty.");
        }

        p = observations[0].features.size() + 1;
        n = observations.size();

        if (p <= 1 || n <= p) {
            throw runtime_error(
                "Insufficient observations or predictors."
            );
        }

        map<string, bool> identifiers;

        for (const auto& observation : observations) {
            if (observation.id.empty() ||
                identifiers[observation.id]) {
                throw runtime_error(
                    "Missing or duplicate observation ID."
                );
            }

            identifiers[observation.id] = true;

            if (observation.features.size() != p - 1) {
                throw runtime_error(
                    "Inconsistent predictor dimensions."
                );
            }

            if (!isfinite(observation.target)) {
                throw runtime_error(
                    "Non-finite target value."
                );
            }

            for (double value : observation.features) {
                if (!isfinite(value)) {
                    throw runtime_error(
                        "Non-finite predictor value."
                    );
                }
            }
        }
    }

    vector<double> auxiliaryFit(
        const vector<double>& target,
        const Matrix& design
    ) const {
        Matrix xt = transpose(design);
        Matrix xtx = multiply(xt, design);

        vector<double> xty(xt.size());

        for (size_t i = 0; i < xt.size(); ++i) {
            xty[i] = dot(xt[i], target);
        }

        return solve(xtx, xty);
    }

    double auxiliaryRSquared(
        const vector<double>& target,
        const Matrix& design
    ) const {
        vector<double> coefficients = auxiliaryFit(
            target, design
        );

        double center = average(target);
        double sseAux = 0.0;
        double sstAux = 0.0;

        for (size_t i = 0; i < target.size(); ++i) {
            double prediction = dot(
                design[i], coefficients
            );

            sseAux += pow(target[i] - prediction, 2);
            sstAux += pow(target[i] - center, 2);
        }

        if (sstAux < 1e-15) {
            throw runtime_error(
                "Auxiliary regression target has zero variance."
            );
        }

        return max(
            0.0,
            min(1.0, 1.0 - sseAux / sstAux)
        );
    }

public:
    explicit RegressionEngine(
        vector<Observation> data
    ) : observations(move(data)), n(0), p(0) {
        validate();

        X.resize(n);
        y.resize(n);

        for (size_t i = 0; i < n; ++i) {
            X[i].push_back(1.0);

            for (double value : observations[i].features) {
                X[i].push_back(value);
            }

            y[i] = observations[i].target;
        }
    }

    void fit() {
        Matrix xt = transpose(X);
        Matrix xtx = multiply(xt, X);

        xtxInverse = inverse(xtx);

        vector<double> xty(p, 0.0);

        for (size_t i = 0; i < p; ++i) {
            xty[i] = dot(xt[i], y);
        }

        beta.resize(p);

        for (size_t i = 0; i < p; ++i) {
            beta[i] = dot(xtxInverse[i], xty);
        }

        fitted.resize(n);
        residuals.resize(n);

        for (size_t i = 0; i < n; ++i) {
            fitted[i] = dot(X[i], beta);
            residuals[i] = y[i] - fitted[i];
            sse += residuals[i] * residuals[i];
        }

        mse = sse / (n - p);

        double center = average(y);
        double sst = 0.0;

        for (double value : y) {
            sst += pow(value - center, 2);
        }

        if (sst <= 1e-15) {
            throw runtime_error(
                "Target variable has zero variance."
            );
        }

        rSquared = 1.0 - sse / sst;
        fittedState = true;
    }

    void requireFitted() const {
        if (!fittedState) {
            throw runtime_error(
                "Model must be fitted before diagnostics."
            );
        }
    }

    vector<double> leverage() const {
        requireFitted();

        Matrix hat = multiply(
            multiply(X, xtxInverse),
            transpose(X)
        );

        vector<double> result(n);

        for (size_t i = 0; i < n; ++i) {
            result[i] = hat[i][i];
        }

        return result;
    }

    vector<double> studentizedResiduals() const {
        requireFitted();

        if (mse <= 0) {
            throw runtime_error(
                "Studentized residuals are undefined."
            );
        }

        vector<double> h = leverage();
        vector<double> result(n);

        for (size_t i = 0; i < n; ++i) {
            result[i] = residuals[i] /
                sqrt(mse * max(1e-15, 1.0 - h[i]));
        }

        return result;
    }

    vector<double> cooksDistance() const {
        vector<double> h = leverage();
        vector<double> r = studentizedResiduals();

        vector<double> result(n);

        for (size_t i = 0; i < n; ++i) {
            result[i] = r[i] * r[i] * h[i] /
                (p * max(1e-15, 1.0 - h[i]));
        }

        return result;
    }

    vector<double> vif() const {
        requireFitted();

        Matrix columns = transpose(X);
        vector<double> result;

        for (size_t predictor = 1;
             predictor < p;
             ++predictor) {

            Matrix auxiliary(n, vector<double>{1.0});

            for (size_t row = 0; row < n; ++row) {
                for (size_t col = 1; col < p; ++col) {
                    if (col != predictor) {
                        auxiliary[row].push_back(
                            X[row][col]
                        );
                    }
                }
            }

            if (p == 2) {
                result.push_back(1.0);
                continue;
            }

            vector<double> target = columns[predictor];

            double rSquared = auxiliaryRSquared(
                target, auxiliary
            );

            result.push_back(
                1.0 / max(1e-15, 1.0 - rSquared)
            );
        }

        return result;
    }

    pair<double, double> breuschPagan() const {
        requireFitted();

        vector<double> squared(n);

        for (size_t i = 0; i < n; ++i) {
            squared[i] = residuals[i] * residuals[i];
        }

        double rSquared = auxiliaryRSquared(
            squared, X
        );

        double statistic = n * rSquared;

        return {
            statistic,
            chiSquareSurvival(
                statistic,
                static_cast<int>(p - 1)
            )
        };
    }

    pair<double, double> jarqueBera() const {
        requireFitted();

        double center = average(residuals);
        double v = 0.0;

        for (double value : residuals) {
            v += pow(value - center, 2);
        }

        v /= n;

        if (v <= 1e-15) return {0.0, 1.0};

        double third = 0.0;
        double fourth = 0.0;

        for (double value : residuals) {
            double difference = value - center;
            third += pow(difference, 3);
            fourth += pow(difference, 4);
        }

        double skew = third / n / pow(v, 1.5);
        double kurtosis = fourth / n / (v * v);

        double statistic = n / 6.0 * (
            skew * skew +
            pow(kurtosis - 3.0, 2) / 4.0
        );

        return {
            statistic,
            chiSquareSurvival(statistic, 2)
        };
    }

    vector<double> hc3StandardErrors() const {
        vector<double> h = leverage();
        Matrix weighted = X;

        for (size_t i = 0; i < n; ++i) {
            double adjusted = residuals[i] /
                max(1e-12, 1.0 - h[i]);

            double weight = adjusted * adjusted;

            for (double& value : weighted[i]) {
                value *= weight;
            }
        }

        Matrix middle = multiply(
            transpose(X), weighted
        );

        Matrix covariance = multiply(
            multiply(xtxInverse, middle),
            xtxInverse
        );

        vector<double> result(p);

        for (size_t i = 0; i < p; ++i) {
            result[i] = sqrt(
                max(0.0, covariance[i][i])
            );
        }

        return result;
    }

    void evaluate(const Policy& policy) const {
        requireFitted();

        cout << "\nREGRESSION GOVERNANCE REPORT\n";
        cout << "============================\n";

        cout << "Observations: " << n << '\n';
        cout << "Parameters: " << p << '\n';
        cout << "R-squared: " << rSquared << '\n';
        cout << "Adjusted R-squared: "
             << 1.0 - (1.0 - rSquared) *
                (n - 1.0) / (n - p) << '\n';

        cout << "\nCoefficients:\n";

        for (size_t i = 0; i < beta.size(); ++i) {
            cout << "Beta " << i << ": "
                 << beta[i] << '\n';
        }

        cout << "\nVIF:\n";

        vector<double> vifValues = vif();

        for (size_t i = 0; i < vifValues.size(); ++i) {
            Severity severity =
                vifValues[i] >= policy.vifCritical
                    ? Severity::FAIL
                    : vifValues[i] >= policy.vifWarning
                        ? Severity::WARNING
                        : Severity::PASS;

            cout << "X" << i + 1 << ": "
                 << vifValues[i] << " ["
                 << severityName(severity) << "]\n";
        }

        auto bp = breuschPagan();

        cout << "\nBreusch-Pagan:\n";
        cout << "LM: " << bp.first << '\n';
        cout << "p-value: " << bp.second << '\n';
        cout << "Decision: "
             << (bp.second < policy.bpAlpha
                 ? "HETEROSCEDASTICITY EVIDENCE"
                 : "NO SIGNIFICANT EVIDENCE")
             << '\n';

        auto jb = jarqueBera();

        cout << "\nJarque-Bera:\n";
        cout << "Statistic: " << jb.first << '\n';
        cout << "p-value: " << jb.second << '\n';

        vector<double> h = leverage();
        vector<double> cooks = cooksDistance();
        vector<double> studentized =
            studentizedResiduals();

        cout << "\nInfluential observations:\n";

        double cookThreshold =
            policy.cookMultiplier / n;

        double leverageThreshold =
            policy.leverageMultiplier * p / n;

        bool found = false;

        for (size_t i = 0; i < n; ++i) {
            if (cooks[i] > cookThreshold ||
                h[i] > leverageThreshold ||
                abs(studentized[i]) >
                    policy.studentizedLimit) {

                found = true;

                cout << observations[i].id
                     << " | Cook's D=" << cooks[i]
                     << " | Leverage=" << h[i]
                     << " | Studentized residual="
                     << studentized[i] << '\n';
            }
        }

        if (!found) {
            cout << "No observations exceed screening thresholds.\n";
        }

        cout << "\nHC3 standard errors:\n";

        vector<double> errors = hc3StandardErrors();

        for (size_t i = 0; i < errors.size(); ++i) {
            cout << "Beta " << i << ": "
                 << errors[i] << '\n';
        }
    }

    size_t sampleSize() const {
        return n;
    }

    double goodnessOfFit() const {
        requireFitted();
        return rSquared;
    }

    const vector<double>& coefficients() const {
        requireFitted();
        return beta;
    }
};

vector<Observation> createDataset() {
    vector<Observation> data;

    for (int i = 1; i <= 80; ++i) {
        double x1 = i;
        double x2 = 0.92 * i + (i % 7) * 0.8;

        double error = ((i % 9) - 4) *
            (0.4 + 0.025 * i);

        if (i == 72) error += 35.0;

        double y = 12.0 + 2.5 * x1 +
            1.3 * x2 + error;

        data.push_back({
            "OBS-" + to_string(i),
            {x1, x2},
            y
        });
    }

    return data;
}

void runTests() {
    RegressionEngine model(createDataset());

    model.fit();

    if (model.sampleSize() != 80) {
        throw runtime_error("Sample size test failed.");
    }

    if (model.goodnessOfFit() < 0 ||
        model.goodnessOfFit() > 1) {
        throw runtime_error("R-squared validation failed.");
    }

    auto bp = model.breuschPagan();

    if (bp.second < 0 || bp.second > 1) {
        throw runtime_error("Invalid Breusch-Pagan p-value.");
    }

    auto vifValues = model.vif();

    for (double value : vifValues) {
        if (value < 1.0) {
            throw runtime_error("Invalid VIF.");
        }
    }

    auto h = model.leverage();

    double sumLeverage = accumulate(
        h.begin(), h.end(), 0.0
    );

    if (abs(sumLeverage - 3.0) > 1e-6) {
        throw runtime_error(
            "Hat matrix trace validation failed."
        );
    }

    if (abs(
        chiSquareSurvival(5.9914645, 2) - 0.05
    ) > 1e-5) {
        throw runtime_error(
            "Chi-square probability validation failed."
        );
    }

    cout << "All C++ diagnostic tests passed.\n";
}

int main() {
    try {
        cout << fixed << setprecision(6);

        runTests();

        RegressionEngine model(createDataset());
        model.fit();

        Policy policy;
        model.evaluate(policy);

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
