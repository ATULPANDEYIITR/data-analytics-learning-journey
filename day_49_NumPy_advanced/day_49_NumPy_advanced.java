import java.util.Arrays;
import java.util.Random;
import java.util.stream.DoubleStream;

public class AdvancedNumpyConcepts {

    record Matrix(int rows, int columns, double[][] values) {
        Matrix {
            if (rows <= 0 || columns <= 0) {
                throw new IllegalArgumentException("Matrix dimensions must be positive.");
            }

            if (values.length != rows) {
                throw new IllegalArgumentException("Row count does not match matrix shape.");
            }

            for (double[] row : values) {
                if (row.length != columns) {
                    throw new IllegalArgumentException(
                        "Every row must contain exactly " + columns + " values."
                    );
                }
            }
        }

        static Matrix of(double[][] input) {
            if (input.length == 0) {
                throw new IllegalArgumentException("Matrix cannot be empty.");
            }

            double[][] copy = new double[input.length][];

            for (int row = 0; row < input.length; row++) {
                copy[row] = input[row].clone();
            }

            return new Matrix(
                input.length,
                input[0].length,
                copy
            );
        }

        double get(int row, int column) {
            return values[row][column];
        }

        Matrix addBroadcast(double[] vector) {
            if (vector.length != columns) {
                throw new IllegalArgumentException(
                    "Broadcast vector must have one value per matrix column."
                );
            }

            double[][] result = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    result[row][column] =
                        values[row][column] + vector[column];
                }
            }

            return Matrix.of(result);
        }

        Matrix multiplyBroadcast(double[] vector) {
            if (vector.length != columns) {
                throw new IllegalArgumentException(
                    "Broadcast vector must have one value per matrix column."
                );
            }

            double[][] result = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    result[row][column] =
                        values[row][column] * vector[column];
                }
            }

            return Matrix.of(result);
        }

        Matrix multiply(Matrix other) {
            if (columns != other.rows) {
                throw new IllegalArgumentException(
                    "Matrix multiplication requires compatible dimensions."
                );
            }

            double[][] result = new double[rows][other.columns];

            for (int row = 0; row < rows; row++) {
                for (int shared = 0; shared < columns; shared++) {
                    for (int column = 0; column < other.columns; column++) {
                        result[row][column] +=
                            values[row][shared] * other.values[shared][column];
                    }
                }
            }

            return Matrix.of(result);
        }

        Matrix transpose() {
            double[][] result = new double[columns][rows];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    result[column][row] = values[row][column];
                }
            }

            return Matrix.of(result);
        }

        double[] meanByColumn() {
            double[] result = new double[columns];

            for (int column = 0; column < columns; column++) {
                for (int row = 0; row < rows; row++) {
                    result[column] += values[row][column];
                }

                result[column] /= rows;
            }

            return result;
        }

        double[] meanByRow() {
            double[] result = new double[rows];

            for (int row = 0; row < rows; row++) {
                result[row] =
                    DoubleStream.of(values[row]).average().orElse(0.0);
            }

            return result;
        }

        double[] flatten() {
            return Arrays.stream(values)
                .flatMapToDouble(Arrays::stream)
                .toArray();
        }

        @Override
        public String toString() {
            StringBuilder builder = new StringBuilder();

            for (double[] row : values) {
                builder.append(Arrays.toString(row)).append('\n');
            }

            return builder.toString();
        }
    }

    enum Metric {
        COMMIT_COUNT,
        REVIEW_COUNT,
        FAILURE_RATE,
        DELIVERY_SCORE
    }

    record RepositoryMetrics(
        String repository,
        double commitCount,
        double reviewCount,
        double failureRate,
        double deliveryScore
    ) {
        double[] vector() {
            return new double[] {
                commitCount,
                reviewCount,
                failureRate,
                deliveryScore
            };
        }
    }

    static final class AnalyticsService {

        Matrix repositoryMatrix(RepositoryMetrics[] repositories) {
            double[][] data = new double[repositories.length][Metric.values().length];

            for (int row = 0; row < repositories.length; row++) {
                data[row] = repositories[row].vector();
            }

            return Matrix.of(data);
        }

        double[] standardizedFeatureScores(Matrix matrix) {
            double[] means = matrix.meanByColumn();
            double[] standardDeviations = new double[matrix.columns];

            for (int column = 0; column < matrix.columns; column++) {
                double squaredDifference = 0.0;

                for (int row = 0; row < matrix.rows; row++) {
                    double difference =
                        matrix.values[row][column] - means[column];

                    squaredDifference += difference * difference;
                }

                standardDeviations[column] =
                    Math.sqrt(squaredDifference / matrix.rows);

                if (standardDeviations[column] == 0.0) {
                    throw new IllegalArgumentException(
                        "Cannot standardize a constant feature."
                    );
                }
            }

            double[] scores = new double[matrix.columns];

            for (int column = 0; column < matrix.columns; column++) {
                double total = 0.0;

                for (int row = 0; row < matrix.rows; row++) {
                    total +=
                        (matrix.values[row][column] - means[column])
                        / standardDeviations[column];
                }

                scores[column] = total / matrix.rows;
            }

            return scores;
        }

        Matrix randomNormalData(
            int rows,
            int columns,
            double[] means,
            double[] deviations,
            long seed
        ) {
            if (means.length != columns || deviations.length != columns) {
                throw new IllegalArgumentException(
                    "Each feature requires a mean and standard deviation."
                );
            }

            for (double deviation : deviations) {
                if (deviation <= 0.0) {
                    throw new IllegalArgumentException(
                        "Standard deviation must be positive."
                    );
                }
            }

            Random random = new Random(seed);
            double[][] data = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    data[row][column] =
                        means[column]
                        + deviations[column] * random.nextGaussian();
                }
            }

            return Matrix.of(data);
        }
    }

    static void printVector(String title, double[] values) {
        System.out.println(title + ": " + Arrays.toString(values));
    }

    static void printMatrix(String title, Matrix matrix) {
        System.out.println("\n" + title);
        System.out.println(
            "shape=(" + matrix.rows + ", " + matrix.columns + ")"
        );
        System.out.print(matrix);
    }

    static double determinant2x2(Matrix matrix) {
        if (matrix.rows != 2 || matrix.columns != 2) {
            throw new IllegalArgumentException("Expected a 2x2 matrix.");
        }

        return matrix.values[0][0] * matrix.values[1][1]
            - matrix.values[0][1] * matrix.values[1][0];
    }

    static Matrix inverse2x2(Matrix matrix) {
        double determinant = determinant2x2(matrix);

        if (Math.abs(determinant) < 1e-12) {
            throw new IllegalArgumentException(
                "Matrix is singular or numerically unstable."
            );
        }

        double[][] inverse = {
            {
                matrix.values[1][1] / determinant,
                -matrix.values[0][1] / determinant
            },
            {
                -matrix.values[1][0] / determinant,
                matrix.values[0][0] / determinant
            }
        };

        return Matrix.of(inverse);
    }

    static void runEnterpriseAnalytics() {
        RepositoryMetrics[] repositories = {
            new RepositoryMetrics("payments-api", 240, 42, 0.03, 0.91),
            new RepositoryMetrics("identity-service", 180, 35, 0.02, 0.95),
            new RepositoryMetrics("risk-engine", 310, 51, 0.07, 0.82),
            new RepositoryMetrics("reporting-platform", 140, 24, 0.04, 0.89)
        };

        AnalyticsService service = new AnalyticsService();
        Matrix metrics = service.repositoryMatrix(repositories);

        printMatrix("Enterprise repository metrics", metrics);

        double[] weights = {
            0.25, 0.25, -0.30, 0.20
        };

        Matrix weighted = metrics.multiplyBroadcast(weights);
        printMatrix(
            "Feature-weighted repository metrics",
            weighted
        );

        printVector(
            "Mean metric by repository",
            metrics.meanByRow()
        );

        printVector(
            "Mean metric by feature",
            metrics.meanByColumn()
        );

        printVector(
            "Standardized feature means",
            service.standardizedFeatureScores(metrics)
        );

        Matrix generated = service.randomNormalData(
            8,
            3,
            new double[] {50.0, 100.0, 0.75},
            new double[] {5.0, 12.0, 0.08},
            2026L
        );

        printMatrix(
            "Seeded enterprise simulation data",
            generated
        );

        Matrix projection = metrics.multiply(
            Matrix.of(new double[][] {
                {0.50, 0.20},
                {0.20, 0.60},
                {0.10, 0.30},
                {0.40, 0.10}
            })
        );

        printMatrix(
            "Two-dimensional metric projection",
            projection
        );
    }

    public static void main(String[] args) {
        System.out.println(
            "Advanced numerical array and matrix processing with Java 17"
        );

        Matrix sales = Matrix.of(new double[][] {
            {120, 80, 200},
            {150, 90, 180},
            {100, 70, 220}
        });

        double[] taxRates = {0.05, 0.12, 0.18};

        Matrix taxes = sales.multiplyBroadcast(taxRates);
        Matrix finalSales = sales.addBroadcast(taxes.flatten());

        printMatrix("Sales", sales);
        printMatrix("Column-wise tax application", taxes);

        // The enterprise example uses an explicit Matrix abstraction because
        // Java does not provide NumPy's native broadcasting model.
        // Broadcast behavior is encoded as a domain operation instead.
        Matrix adjusted = sales.multiplyBroadcast(taxRates);
        printMatrix("Broadcast-adjusted sales", adjusted);

        printVector("Column means", sales.meanByColumn());
        printVector("Row means", sales.meanByRow());
        printMatrix("Transposed sales", sales.transpose());

        Matrix left = Matrix.of(new double[][] {
            {2, 1},
            {4, 3}
        });

        Matrix right = Matrix.of(new double[][] {
            {5, 2},
            {1, 6}
        });

        printMatrix(
            "Matrix multiplication",
            left.multiply(right)
        );

        double determinant = determinant2x2(left);
        System.out.println("\nDeterminant: " + determinant);

        Matrix inverse = inverse2x2(left);
        printMatrix("Inverse", inverse);
        printMatrix("Inverse verification", left.multiply(inverse));

        try {
            Matrix incompatible = Matrix.of(new double[][] {
                {1, 2, 3}
            });

            left.multiply(incompatible);
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "\nExpected matrix validation failure: "
                + exception.getMessage()
            );
        }

        try {
            inverse2x2(Matrix.of(new double[][] {
                {1, 2},
                {2, 4}
            }));
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "Expected singular-matrix failure: "
                + exception.getMessage()
            );
        }

        runEnterpriseAnalytics();

        System.out.println("\nCompleted successfully.");
    }
}
