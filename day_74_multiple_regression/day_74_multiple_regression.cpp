#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * MULTIPLE REGRESSION ENGINE
 *
 * C++17 implementation of ordinary least squares.
 *
 * Supports:
 * - Multiple continuous predictors
 * - Categorical predictors
 * - Reference-category dummy encoding
 * - Numerical interaction terms
 * - Model fitting and prediction
 * - Residual diagnostics
 * - R-squared and adjusted R-squared
 * - Standard errors
 * - Merge-free, deterministic model state
 */

enum class VariableType {
    Numerical,
    Categorical
};

struct Observation {
    double salary;
    double experience;
    double performance;
    string education;
    string department;
};

struct Interaction {
    string first;
    string second;
};

struct ModelMetrics {
    double r_squared = 0.0;
    double adjusted_r_squared = 0.0;
    double rmse = 0.0;
    double mae = 0.0;
    double residual_sum_squares = 0.0;
};

struct RegressionTerm {
    string name;
    double coefficient = 0.0;
    double standard_error = 0.0;
};

class RegressionException : public runtime_error {
public:
    explicit RegressionException(const string& message)
        : runtime_error(message) {}
};

class MatrixSolver {
public:
    static vector<double> solve(
        vector<vector<double>> matrix,
        vector<double> vector_b
    ) {
        int n = static_cast<int>(vector_b.size());

        if (n == 0 || matrix.size() != vector_b.size()) {
            throw RegressionException("Invalid matrix dimensions.");
        }

        for (const auto& row : matrix) {
            if (row.size() != static_cast<size_t>(n)) {
                throw RegressionException("Matrix must be square.");
            }
        }

        for (int col = 0; col < n; ++col) {
            int pivot = col;

            for (int row = col + 1; row < n; ++row) {
                if (
                    abs(matrix[row][col]) >
                    abs(matrix[pivot][col])
                ) {
                    pivot = row;
                }
            }

            if (abs(matrix[pivot][col]) < 1e-12) {
                throw RegressionException(
                    "Singular matrix: predictors are dependent."
                );
            }

            swap(matrix[col], matrix[pivot]);
            swap(vector_b[col], vector_b[pivot]);

            double divisor = matrix[col][col];

            for (int j = col; j < n; ++j) {
                matrix[col][j] /= divisor;
            }

            vector_b[col] /= divisor;

            for (int row = 0; row < n; ++row) {
                if (row == col) continue;

                double factor = matrix[row][col];

                for (int j = col; j < n; ++j) {
                    matrix[row][j] -= factor * matrix[col][j];
                }

                vector_b[row] -= factor * vector_b[col];
            }
        }

        return vector_b;
    }

    static vector<vector<double>> inverse(
        const vector<vector<double>>& matrix
    ) {
        int n = static_cast<int>(matrix.size());

        vector<vector<double>> augmented(
            n,
            vector<double>(2 * n, 0.0)
        );

        for (int i = 0; i < n; ++i) {
            if (matrix[i].size() != static_cast<size_t>(n)) {
                throw RegressionException("Matrix must be square.");
            }

            for (int j = 0; j < n; ++j) {
                augmented[i][j] = matrix[i][j];
            }

            augmented[i][n + i] = 1.0;
        }

        for (int col = 0; col < n; ++col) {
            int pivot = col;

            for (int row = col + 1; row < n; ++row) {
                if (
                    abs(augmented[row][col]) >
                    abs(augmented[pivot][col])
                ) {
                    pivot = row;
                }
            }

            if (abs(augmented[pivot][col]) < 1e-12) {
                throw RegressionException(
                    "Cannot invert singular matrix."
                );
            }

            swap(augmented[col], augmented[pivot]);

            double divisor = augmented[col][col];

            for (double& value : augmented[col]) {
                value /= divisor;
            }

            for (int row = 0; row < n; ++row) {
                if (row == col) continue;

                double factor = augmented[row][col];

                for (int j = 0; j < 2 * n; ++j) {
                    augmented[row][j] -=
                        factor * augmented[col][j];
                }
            }
        }

        vector<vector<double>> result(
            n,
            vector<double>(n)
        );

        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                result[i][j] = augmented[i][n + j];
            }
        }

        return result;
    }
};

class MultipleRegressionEngine {
private:
    vector<string> numerical_variables = {
        "experience",
        "performance"
    };

    vector<string> categorical_variables = {
        "education",
        "department"
    };

    vector<Interaction> interactions = {
        {"experience", "performance"}
    };

    map<string, vector<string>> categories;

    vector<string> feature_names;
    vector<double> coefficients;
    vector<double> standard_errors;
    vector<double> residuals;
    vector<double> predictions;

    vector<vector<double>> design_matrix;
    ModelMetrics metrics;

    bool fitted = false;

    double get_numeric(
        const Observation& observation,
        const string& name
    ) const {
        if (name == "experience") return observation.experience;
        if (name == "performance") return observation.performance;

        throw RegressionException("Unknown numerical variable.");
    }

    string get_category(
        const Observation& observation,
        const string& name
    ) const {
        if (name == "education") return observation.education;
        if (name == "department") return observation.department;

        throw RegressionException("Unknown categorical variable.");
    }

    void validate(const vector<Observation>& data) const {
        if (data.empty()) {
            throw RegressionException("Dataset is empty.");
        }

        for (const auto& observation : data) {
            if (
                !isfinite(observation.salary) ||
                !isfinite(observation.experience) ||
                !isfinite(observation.performance)
            ) {
                throw RegressionException(
                    "Dataset contains non-finite values."
                );
            }

            if (
                observation.experience < 0 ||
                observation.performance < 0 ||
                observation.education.empty() ||
                observation.department.empty()
            ) {
                throw RegressionException(
                    "Invalid observation encountered."
                );
            }
        }
    }

    void discover_categories(
        const vector<Observation>& data
    ) {
        categories.clear();

        for (const auto& variable : categorical_variables) {
            set<string> levels;

            for (const auto& observation : data) {
                levels.insert(get_category(observation, variable));
            }

            if (levels.size() < 2) {
                throw RegressionException(
                    "Categorical variable requires two levels."
                );
            }

            categories[variable] = vector<string>(
                levels.begin(),
                levels.end()
            );
        }
    }

    vector<double> encode(
        const Observation& observation
    ) const {
        vector<double> row;

        row.push_back(1.0);

        for (const auto& variable : numerical_variables) {
            row.push_back(get_numeric(observation, variable));
        }

        for (const auto& variable : categorical_variables) {
            const string value = get_category(observation, variable);

            const auto& levels = categories.at(variable);

            if (
                find(levels.begin(), levels.end(), value) ==
                levels.end()
            ) {
                throw RegressionException(
                    "Unknown categorical level: " + value
                );
            }

            for (size_t i = 1; i < levels.size(); ++i) {
                row.push_back(value == levels[i] ? 1.0 : 0.0);
            }
        }

        for (const auto& interaction : interactions) {
            row.push_back(
                get_numeric(observation, interaction.first) *
                get_numeric(observation, interaction.second)
            );
        }

        return row;
    }

    void create_feature_names() {
        feature_names = {"Intercept"};

        for (const auto& variable : numerical_variables) {
            feature_names.push_back(variable);
        }

        for (const auto& variable : categorical_variables) {
            const auto& levels = categories.at(variable);

            for (size_t i = 1; i < levels.size(); ++i) {
                feature_names.push_back(
                    variable + "[" + levels[i] + "]"
                );
            }
        }

        for (const auto& interaction : interactions) {
            feature_names.push_back(
                interaction.first + ":" + interaction.second
            );
        }
    }

public:
    void fit(const vector<Observation>& data) {
        validate(data);
        discover_categories(data);
        create_feature_names();

        const int n = static_cast<int>(data.size());
        const int p = static_cast<int>(feature_names.size());

        if (n <= p) {
            throw RegressionException(
                "Number of observations must exceed parameter count."
            );
        }

        design_matrix.clear();

        vector<double> y;

        for (const auto& observation : data) {
            design_matrix.push_back(encode(observation));
            y.push_back(observation.salary);
        }

        vector<vector<double>> xtx(
            p,
            vector<double>(p, 0.0)
        );

        vector<double> xty(p, 0.0);

        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < p; ++j) {
                xty[j] += design_matrix[i][j] * y[i];

                for (int k = 0; k < p; ++k) {
                    xtx[j][k] +=
                        design_matrix[i][j] *
                        design_matrix[i][k];
                }
            }
        }

        coefficients = MatrixSolver::solve(xtx, xty);

        predictions.assign(n, 0.0);
        residuals.assign(n, 0.0);

        double mean_y = 0.0;

        for (double value : y) {
            mean_y += value;
        }

        mean_y /= n;

        double sse = 0.0;
        double sst = 0.0;
        double absolute_error = 0.0;

        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < p; ++j) {
                predictions[i] +=
                    design_matrix[i][j] * coefficients[j];
            }

            residuals[i] = y[i] - predictions[i];

            sse += residuals[i] * residuals[i];

            sst += pow(y[i] - mean_y, 2);

            absolute_error += abs(residuals[i]);
        }

        if (sst < 1e-12) {
            throw RegressionException(
                "Target variance is zero."
            );
        }

        metrics.residual_sum_squares = sse;
        metrics.r_squared = 1.0 - sse / sst;

        metrics.adjusted_r_squared =
            1.0 -
            (1.0 - metrics.r_squared) *
            (n - 1.0) / (n - p);

        metrics.rmse = sqrt(sse / n);
        metrics.mae = absolute_error / n;

        const double mse = sse / (n - p);

        auto inverse = MatrixSolver::inverse(xtx);

        standard_errors.resize(p);

        for (int i = 0; i < p; ++i) {
            standard_errors[i] = sqrt(
                max(0.0, mse * inverse[i][i])
            );
        }

        fitted = true;
    }

    double predict(const Observation& observation) const {
        if (!fitted) {
            throw RegressionException("Fit the model first.");
        }

        auto row = encode(observation);

        double prediction = 0.0;

        for (size_t i = 0; i < coefficients.size(); ++i) {
            prediction += row[i] * coefficients[i];
        }

        return prediction;
    }

    void print_report() const {
        if (!fitted) {
            throw RegressionException("No fitted model available.");
        }

        cout << fixed << setprecision(4);

        cout << "\nMULTIPLE REGRESSION COEFFICIENTS\n";

        cout << left
             << setw(32) << "Term"
             << setw(16) << "Coefficient"
             << setw(16) << "Std. Error"
             << '\n';

        cout << string(64, '-') << '\n';

        for (size_t i = 0; i < coefficients.size(); ++i) {
            cout << left
                 << setw(32) << feature_names[i]
                 << setw(16) << coefficients[i]
                 << setw(16) << standard_errors[i]
                 << '\n';
        }

        cout << "\nMODEL DIAGNOSTICS\n";

        cout << "R-squared:          "
             << metrics.r_squared << '\n';

        cout << "Adjusted R-squared: "
             << metrics.adjusted_r_squared << '\n';

        cout << "RMSE:               "
             << metrics.rmse << '\n';

        cout << "MAE:                "
             << metrics.mae << '\n';

        cout << "SSE:                "
             << metrics.residual_sum_squares << '\n';
    }

    const ModelMetrics& get_metrics() const {
        if (!fitted) {
            throw RegressionException("Model not fitted.");
        }

        return metrics;
    }
};

int main() {
    try {
        vector<Observation> employees = {
            {45000, 1, 3, "Bachelor", "Sales"},
            {49000, 2, 4, "Bachelor", "Sales"},
            {53000, 3, 3, "Master", "Sales"},
            {57000, 4, 4, "Master", "Technology"},
            {65000, 5, 5, "Master", "Technology"},
            {61000, 4, 5, "Bachelor", "Technology"},
            {72000, 6, 4, "PhD", "Technology"},
            {76000, 7, 5, "PhD", "Technology"},
            {50000, 2, 3, "Bachelor", "Operations"},
            {55000, 3, 4, "Master", "Operations"},
            {59000, 4, 4, "Bachelor", "Operations"},
            {68000, 6, 5, "PhD", "Operations"},
            {48000, 2, 2, "Bachelor", "Sales"},
            {62000, 5, 4, "Master", "Sales"},
            {70000, 6, 5, "PhD", "Technology"},
            {54000, 3, 3, "Bachelor", "Operations"},
            {74000, 7, 5, "Master", "Technology"},
            {58000, 4, 3, "Master", "Sales"},
            {64000, 5, 5, "Bachelor", "Operations"},
            {79000, 8, 5, "PhD", "Technology"}
        };

        MultipleRegressionEngine engine;

        engine.fit(employees);

        engine.print_report();

        Observation new_employee = {
            0,
            5,
            4,
            "Master",
            "Technology"
        };

        cout << "\nPREDICTED SALARY\n";

        cout << fixed << setprecision(2)
             << engine.predict(new_employee)
             << '\n';

        cout << "\nMODEL VALIDATION\n";

        if (
            engine.get_metrics().r_squared < 0 ||
            engine.get_metrics().r_squared > 1
        ) {
            cerr << "Warning: unusual R-squared value.\n";
        }

        cout << "Regression engine completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Regression failure: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
