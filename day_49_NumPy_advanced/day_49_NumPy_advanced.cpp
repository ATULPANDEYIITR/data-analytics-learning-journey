#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

class Matrix {
private:
    std::size_t rows_;
    std::size_t cols_;
    std::vector<double> values_;

public:
    Matrix(std::size_t rows, std::size_t cols, double initial = 0.0)
        : rows_(rows), cols_(cols), values_(rows * cols, initial) {}

    Matrix(std::size_t rows, std::size_t cols, std::vector<double> values)
        : rows_(rows), cols_(cols), values_(std::move(values)) {
        if (values_.size() != rows_ * cols_) {
            throw std::invalid_argument("Matrix data size does not match shape.");
        }
    }

    double& operator()(std::size_t row, std::size_t col) {
        return values_.at(row * cols_ + col);
    }

    double operator()(std::size_t row, std::size_t col) const {
        return values_.at(row * cols_ + col);
    }

    std::size_t rows() const { return rows_; }
    std::size_t cols() const { return cols_; }

    Matrix transpose() const {
        Matrix result(cols_, rows_);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                result(col, row) = (*this)(row, col);
            }
        }

        return result;
    }

    std::vector<double> rowMeans() const {
        std::vector<double> result(rows_, 0.0);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                result[row] += (*this)(row, col);
            }

            result[row] /= static_cast<double>(cols_);
        }

        return result;
    }

    std::vector<double> columnMeans() const {
        std::vector<double> result(cols_, 0.0);

        for (std::size_t col = 0; col < cols_; ++col) {
            for (std::size_t row = 0; row < rows_; ++row) {
                result[col] += (*this)(row, col);
            }

            result[col] /= static_cast<double>(rows_);
        }

        return result;
    }

    Matrix multiply(const Matrix& other) const {
        if (cols_ != other.rows_) {
            throw std::invalid_argument(
                "Matrix multiplication requires matching inner dimensions."
            );
        }

        Matrix result(rows_, other.cols_);

        for (std::size_t i = 0; i < rows_; ++i) {
            for (std::size_t k = 0; k < cols_; ++k) {
                const double left = (*this)(i, k);

                for (std::size_t j = 0; j < other.cols_; ++j) {
                    result(i, j) += left * other(k, j);
                }
            }
        }

        return result;
    }

    Matrix addRowVector(const std::vector<double>& vector) const {
        if (vector.size() != cols_) {
            throw std::invalid_argument(
                "Broadcast row vector must match matrix column count."
            );
        }

        Matrix result(rows_, cols_);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                // This is the matrix analogue of broadcasting a shape (columns,)
                // vector across every row.
                result(row, col) = (*this)(row, col) + vector[col];
            }
        }

        return result;
    }

    Matrix multiplyRowVector(const std::vector<double>& vector) const {
        if (vector.size() != cols_) {
            throw std::invalid_argument(
                "Broadcast row vector must match matrix column count."
            );
        }

        Matrix result(rows_, cols_);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                result(row, col) = (*this)(row, col) * vector[col];
            }
        }

        return result;
    }
};

void printMatrix(const std::string& title, const Matrix& matrix) {
    std::cout << "\n" << title
              << " [" << matrix.rows() << " x " << matrix.cols() << "]\n";

    for (std::size_t row = 0; row < matrix.rows(); ++row) {
        for (std::size_t col = 0; col < matrix.cols(); ++col) {
            std::cout << std::setw(11)
                      << std::fixed << std::setprecision(4)
                      << matrix(row, col);
        }
        std::cout << '\n';
    }
}

void printVector(const std::string& title, const std::vector<double>& values) {
    std::cout << "\n" << title << ": ";

    for (double value : values) {
        std::cout << std::fixed << std::setprecision(4)
                  << value << ' ';
    }

    std::cout << '\n';
}

double determinant2x2(const Matrix& matrix) {
    if (matrix.rows() != 2 || matrix.cols() != 2) {
        throw std::invalid_argument("This determinant function expects a 2x2 matrix.");
    }

    return matrix(0, 0) * matrix(1, 1)
         - matrix(0, 1) * matrix(1, 0);
}

Matrix inverse2x2(const Matrix& matrix) {
    const double determinant = determinant2x2(matrix);

    if (std::abs(determinant) < 1e-12) {
        throw std::runtime_error("Matrix is singular or numerically unstable.");
    }

    Matrix result(2, 2);

    result(0, 0) = matrix(1, 1) / determinant;
    result(0, 1) = -matrix(0, 1) / determinant;
    result(1, 0) = -matrix(1, 0) / determinant;
    result(1, 1) = matrix(0, 0) / determinant;

    return result;
}

Matrix generateObservations(
    std::size_t rows,
    std::size_t columns,
    unsigned int seed
) {
    std::mt19937 generator(seed);
    std::normal_distribution<double> distribution(100.0, 15.0);

    Matrix observations(rows, columns);

    for (std::size_t row = 0; row < rows; ++row) {
        for (std::size_t col = 0; col < columns; ++col) {
            observations(row, col) = distribution(generator);
        }
    }

    return observations;
}

Matrix covariance(const Matrix& observations) {
    if (observations.rows() < 2) {
        throw std::invalid_argument("Covariance requires at least two observations.");
    }

    const std::vector<double> means = observations.columnMeans();
    const std::size_t columns = observations.cols();
    Matrix result(columns, columns);

    for (std::size_t i = 0; i < columns; ++i) {
        for (std::size_t j = 0; j < columns; ++j) {
            double sum = 0.0;

            for (std::size_t row = 0; row < observations.rows(); ++row) {
                const double left = observations(row, i) - means[i];
                const double right = observations(row, j) - means[j];

                sum += left * right;
            }

            result(i, j) =
                sum / static_cast<double>(observations.rows() - 1);
        }
    }

    return result;
}

std::vector<double> standardizeColumns(const Matrix& observations) {
    const std::vector<double> means = observations.columnMeans();
    std::vector<double> standardDeviations(observations.cols(), 0.0);

    for (std::size_t col = 0; col < observations.cols(); ++col) {
        for (std::size_t row = 0; row < observations.rows(); ++row) {
            const double difference =
                observations(row, col) - means[col];

            standardDeviations[col] += difference * difference;
        }

        standardDeviations[col] =
            std::sqrt(
                standardDeviations[col] /
                static_cast<double>(observations.rows() - 1)
            );

        if (standardDeviations[col] < 1e-12) {
            throw std::runtime_error("Cannot standardize a constant feature.");
        }
    }

    std::vector<double> standardized(
        observations.rows() * observations.cols()
    );

    for (std::size_t row = 0; row < observations.rows(); ++row) {
        for (std::size_t col = 0; col < observations.cols(); ++col) {
            standardized[row * observations.cols() + col] =
                (observations(row, col) - means[col]) /
                standardDeviations[col];
        }
    }

    return standardized;
}

double vectorMean(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument("Mean of an empty vector is undefined.");
    }

    return std::accumulate(values.begin(), values.end(), 0.0)
        / static_cast<double>(values.size());
}

double vectorVariance(const std::vector<double>& values) {
    if (values.size() < 2) {
        throw std::invalid_argument("Variance requires at least two values.");
    }

    const double mean = vectorMean(values);
    double sum = 0.0;

    for (double value : values) {
        const double difference = value - mean;
        sum += difference * difference;
    }

    return sum / static_cast<double>(values.size() - 1);
}

void runRepositoryAnalyticsCaseStudy() {
    std::cout << "=== Numerical Analytics Case Study ===\n";

    Matrix repositoryMetrics(
        5,
        4,
        {
            120, 18, 7, 92,
            210, 25, 12, 88,
            150, 11, 5, 95,
            300, 31, 15, 84,
            175, 20, 9, 90
        }
    );

    printMatrix("Repository metrics", repositoryMetrics);

    std::vector<double> featureAdjustment = {
        1.0, 1.2, 0.8, 1.05
    };

    Matrix adjusted = repositoryMetrics.multiplyRowVector(featureAdjustment);
    printMatrix("Feature-adjusted metrics using broadcasting semantics", adjusted);

    printVector(
        "Average metric by repository",
        repositoryMetrics.rowMeans()
    );

    printVector(
        "Average metric by feature",
        repositoryMetrics.columnMeans()
    );

    Matrix covarianceMatrix = covariance(repositoryMetrics);
    printMatrix("Feature covariance matrix", covarianceMatrix);

    Matrix transform(
        4,
        2,
        {
            0.40, 0.10,
            0.20, 0.50,
            0.30, 0.20,
            0.10, 0.40
        }
    );

    Matrix projected = repositoryMetrics.multiply(transform);
    printMatrix("Two-dimensional feature projection", projected);

    const std::vector<double> standardized =
        standardizeColumns(repositoryMetrics);

    std::cout << "\nFirst standardized repository row: ";

    for (std::size_t col = 0; col < repositoryMetrics.cols(); ++col) {
        std::cout << std::fixed << std::setprecision(4)
                  << standardized[col] << ' ';
    }

    std::cout << '\n';
}

int main() {
    try {
        std::cout << "Advanced matrix analytics with C++17\n";

        Matrix sales(
            3,
            3,
            {
                100, 120, 90,
                150, 130, 110,
                80, 95, 105
            }
        );

        printMatrix("Sales matrix", sales);

        std::vector<double> seasonalFactors = {
            1.10, 0.95, 1.20
        };

        Matrix seasonalSales =
            sales.multiplyRowVector(seasonalFactors);

        printMatrix(
            "Sales after feature-wise broadcasting",
            seasonalSales
        );

        Matrix transform(
            3,
            2,
            {
                0.6, 0.2,
                0.1, 0.7,
                0.3, 0.1
            }
        );

        Matrix transformed = sales.multiply(transform);

        printMatrix("Matrix transformation", transformed);

        Matrix twoByTwo(
            2,
            2,
            {
                4, 7,
                2, 6
            }
        );

        const double determinant = determinant2x2(twoByTwo);
        std::cout << "\nDeterminant: " << determinant << '\n';

        Matrix inverse = inverse2x2(twoByTwo);
        printMatrix("Inverse", inverse);

        Matrix identity = twoByTwo.multiply(inverse);
        printMatrix("A multiplied by its inverse", identity);

        Matrix observations =
            generateObservations(1000, 4, 2026);

        printMatrix(
            "First five generated observations",
            Matrix(
                5,
                observations.cols(),
                {
                    observations(0, 0), observations(0, 1),
                    observations(0, 2), observations(0, 3),
                    observations(1, 0), observations(1, 1),
                    observations(1, 2), observations(1, 3),
                    observations(2, 0), observations(2, 1),
                    observations(2, 2), observations(2, 3),
                    observations(3, 0), observations(3, 1),
                    observations(3, 2), observations(3, 3),
                    observations(4, 0), observations(4, 1),
                    observations(4, 2), observations(4, 3)
                }
            )
        );

        printMatrix(
            "Generated-data covariance",
            covariance(observations)
        );

        runRepositoryAnalyticsCaseStudy();

        try {
            Matrix invalid(2, 3);
            Matrix incompatible(4, 2);
            invalid.multiply(incompatible);
        } catch (const std::exception& error) {
            std::cout << "\nExpected dimension failure: "
                      << error.what() << '\n';
        }

        try {
            Matrix singular(
                2,
                2,
                {
                    1, 2,
                    2, 4
                }
            );

            inverse2x2(singular);
        } catch (const std::exception& error) {
            std::cout << "Expected singular-matrix failure: "
                      << error.what() << '\n';
        }

        std::cout << "\nC++ numerical case study completed successfully.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal numerical error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
