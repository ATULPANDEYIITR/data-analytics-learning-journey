#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

class Matrix {
private:
    std::size_t rows_;
    std::size_t columns_;
    std::vector<double> data_;

    std::size_t index(std::size_t row, std::size_t column) const {
        if (row >= rows_ || column >= columns_) {
            throw std::out_of_range("Matrix index outside shape");
        }
        return row * columns_ + column;
    }

public:
    Matrix(std::size_t rows, std::size_t columns, double initial = 0.0)
        : rows_(rows), columns_(columns), data_(rows * columns, initial) {
        if (rows == 0 || columns == 0) {
            throw std::invalid_argument("Matrix dimensions must be positive");
        }
    }

    Matrix(std::size_t rows, std::size_t columns, const std::vector<double>& values)
        : rows_(rows), columns_(columns), data_(values) {
        if (rows == 0 || columns == 0) {
            throw std::invalid_argument("Matrix dimensions must be positive");
        }
        if (values.size() != rows * columns) {
            throw std::invalid_argument("Value count does not match matrix shape");
        }
    }

    double& at(std::size_t row, std::size_t column) {
        return data_[index(row, column)];
    }

    double at(std::size_t row, std::size_t column) const {
        return data_[index(row, column)];
    }

    std::size_t rows() const {
        return rows_;
    }

    std::size_t columns() const {
        return columns_;
    }

    std::vector<double> row(std::size_t row_number) const {
        if (row_number >= rows_) {
            throw std::out_of_range("Invalid row");
        }

        auto begin = data_.begin() + static_cast<std::ptrdiff_t>(row_number * columns_);
        return std::vector<double>(begin, begin + static_cast<std::ptrdiff_t>(columns_));
    }

    Matrix operator+(const Matrix& other) const {
        requireSameShape(other);

        Matrix result(rows_, columns_);
        for (std::size_t i = 0; i < data_.size(); ++i) {
            result.data_[i] = data_[i] + other.data_[i];
        }
        return result;
    }

    Matrix elementWiseMultiply(const Matrix& other) const {
        requireSameShape(other);

        Matrix result(rows_, columns_);
        for (std::size_t i = 0; i < data_.size(); ++i) {
            result.data_[i] = data_[i] * other.data_[i];
        }
        return result;
    }

    Matrix operator*(double scalar) const {
        Matrix result(rows_, columns_);
        for (std::size_t i = 0; i < data_.size(); ++i) {
            result.data_[i] = data_[i] * scalar;
        }
        return result;
    }

    Matrix transpose() const {
        Matrix result(columns_, rows_);
        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t column = 0; column < columns_; ++column) {
                result.at(column, row) = at(row, column);
            }
        }
        return result;
    }

    double sum() const {
        return std::accumulate(data_.begin(), data_.end(), 0.0);
    }

    double mean() const {
        return sum() / static_cast<double>(data_.size());
    }

    double max() const {
        return *std::max_element(data_.begin(), data_.end());
    }

    void requireSameShape(const Matrix& other) const {
        if (rows_ != other.rows_ || columns_ != other.columns_) {
            throw std::invalid_argument("Matrix shapes must match");
        }
    }

    void print(const std::string& title) const {
        std::cout << title << "\n";
        for (std::size_t row = 0; row < rows_; ++row) {
            std::cout << "[";
            for (std::size_t column = 0; column < columns_; ++column) {
                std::cout << std::fixed << std::setprecision(2)
                          << at(row, column);
                if (column + 1 < columns_) {
                    std::cout << ", ";
                }
            }
            std::cout << "]\n";
        }
    }
};


Matrix matrixMultiply(const Matrix& left, const Matrix& right) {
    if (left.columns() != right.rows()) {
        throw std::invalid_argument(
            "Matrix multiplication requires left.columns == right.rows"
        );
    }

    Matrix result(left.rows(), right.columns());

    // The three nested loops implement the mathematical dot product.
    // Complexity is O(m*n*k) for an m x k matrix multiplied by a k x n matrix.
    for (std::size_t i = 0; i < left.rows(); ++i) {
        for (std::size_t j = 0; j < right.columns(); ++j) {
            double total = 0.0;
            for (std::size_t k = 0; k < left.columns(); ++k) {
                total += left.at(i, k) * right.at(k, j);
            }
            result.at(i, j) = total;
        }
    }

    return result;
}


std::vector<bool> greaterThan(const Matrix& matrix, double threshold) {
    std::vector<bool> mask;

    for (std::size_t row = 0; row < matrix.rows(); ++row) {
        for (std::size_t column = 0; column < matrix.columns(); ++column) {
            mask.push_back(matrix.at(row, column) > threshold);
        }
    }

    return mask;
}


Matrix filterToBinaryMask(const Matrix& matrix, double threshold) {
    Matrix result(matrix.rows(), matrix.columns());

    for (std::size_t row = 0; row < matrix.rows(); ++row) {
        for (std::size_t column = 0; column < matrix.columns(); ++column) {
            result.at(row, column) =
                matrix.at(row, column) > threshold ? 1.0 : 0.0;
        }
    }

    return result;
}


double determinant2x2(const Matrix& matrix) {
    if (matrix.rows() != 2 || matrix.columns() != 2) {
        throw std::invalid_argument("Only 2x2 matrices are supported");
    }

    return matrix.at(0, 0) * matrix.at(1, 1)
         - matrix.at(0, 1) * matrix.at(1, 0);
}


void demonstrateDataLayout() {
    std::cout << "=== Array shape and contiguous storage ===\n";

    Matrix measurements(3, 4, {
        82, 91, 77, 88,
        95, 84, 90, 73,
        68, 79, 85, 92
    });

    measurements.print("Measurements:");
    std::cout << "Rows: " << measurements.rows()
              << ", columns: " << measurements.columns() << "\n";

    std::cout << "Second row: ";
    for (double value : measurements.row(1)) {
        std::cout << value << " ";
    }
    std::cout << "\n";
}


void demonstrateElementWiseProcessing() {
    std::cout << "\n=== Element-wise processing ===\n";

    Matrix sales(2, 3, {
        100, 120, 150,
        80, 140, 180
    });

    Matrix quantities(2, 3, {
        2, 1, 3,
        4, 2, 1
    });

    Matrix revenue = sales.elementWiseMultiply(quantities);
    Matrix adjusted = revenue * 0.90;

    sales.print("Unit prices:");
    quantities.print("Quantities:");
    revenue.print("Revenue:");
    adjusted.print("Ten percent reduction:");

    std::cout << "Revenue mean: " << revenue.mean() << "\n";
    std::cout << "Maximum revenue: " << revenue.max() << "\n";
}


void demonstrateBooleanSelection() {
    std::cout << "\n=== Boolean mask reasoning ===\n";

    Matrix scores(3, 3, {
        61, 74, 88,
        92, 55, 79,
        96, 83, 67
    });

    scores.print("Scores:");

    auto mask = greaterThan(scores, 85);
    Matrix selected = filterToBinaryMask(scores, 85);

    std::cout << "Mask for values greater than 85: ";
    for (bool value : mask) {
        std::cout << (value ? "true " : "false ");
    }
    std::cout << "\n";

    selected.print("Binary selection mask:");
}


void demonstrateMatrixCaseStudy() {
    std::cout << "\n=== Demand prediction case study ===\n";

    // Each row represents an observation. Columns represent temperature and
    // promotion intensity. The coefficient matrix produces two output models.
    Matrix features(4, 3, {
        1, 20, 0.0,
        1, 25, 0.5,
        1, 30, 1.0,
        1, 35, 1.5
    });

    Matrix coefficients(3, 2, {
        10, 5,
        2.5, 1.0,
        20, 12
    });

    Matrix predictions = matrixMultiply(features, coefficients);

    features.print("Feature matrix:");
    coefficients.print("Coefficient matrix:");
    predictions.print("Prediction matrix:");

    Matrix transposed = features.transpose();
    transposed.print("Transposed features:");
}


void demonstrateShapeFailures() {
    std::cout << "\n=== Shape validation and failure handling ===\n";

    Matrix left(2, 3, 1.0);
    Matrix incompatible(4, 2, 1.0);

    try {
        matrixMultiply(left, incompatible);
    } catch (const std::invalid_argument& error) {
        std::cout << "Rejected invalid multiplication: "
                  << error.what() << "\n";
    }

    try {
        Matrix wrong(2, 2, {1, 2, 3});
        wrong.print("This will never execute");
    } catch (const std::invalid_argument& error) {
        std::cout << "Rejected invalid construction: "
                  << error.what() << "\n";
    }

    try {
        left.at(10, 0);
    } catch (const std::out_of_range& error) {
        std::cout << "Rejected invalid indexing: "
                  << error.what() << "\n";
    }
}


void demonstrateNumericStability() {
    std::cout << "\n=== Numeric considerations ===\n";

    Matrix matrix(2, 2, {
        4.0, 1.0,
        2.0, 3.0
    });

    const double determinant = determinant2x2(matrix);

    matrix.print("Matrix:");
    std::cout << "Determinant: " << determinant << "\n";

    if (std::abs(determinant) < 1e-12) {
        std::cout << "The matrix is numerically singular.\n";
    } else {
        std::cout << "The matrix is invertible for this example.\n";
    }

    // Floating-point equality should generally use a tolerance when numerical
    // calculations may accumulate rounding error.
    const double computed = 0.1 + 0.2;
    const double expected = 0.3;
    std::cout << "0.1 + 0.2 approximately equals 0.3: "
              << (std::abs(computed - expected) < 1e-12 ? "true" : "false")
              << "\n";
}


int main() {
    try {
        demonstrateDataLayout();
        demonstrateElementWiseProcessing();
        demonstrateBooleanSelection();
        demonstrateMatrixCaseStudy();
        demonstrateShapeFailures();
        demonstrateNumericStability();

        std::cout << "\nC++17 NumPy fundamentals case study completed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
