import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

public class NumpyFundamentalsEnterprise {

    enum DataType {
        FLOAT64,
        INT32
    }

    record Shape(int rows, int columns) {
        public Shape {
            if (rows <= 0 || columns <= 0) {
                throw new IllegalArgumentException("Shape dimensions must be positive");
            }
        }

        public int size() {
            return rows * columns;
        }

        @Override
        public String toString() {
            return "(" + rows + ", " + columns + ")";
        }
    }

    static final class NumericGrid {
        private final Shape shape;
        private final double[] data;
        private final DataType dataType;

        NumericGrid(int rows, int columns, double[] values) {
            this.shape = new Shape(rows, columns);
            this.dataType = DataType.FLOAT64;

            if (values.length != shape.size()) {
                throw new IllegalArgumentException(
                    "Value count does not match shape " + shape
                );
            }

            this.data = values.clone();
            validateFiniteValues();
        }

        NumericGrid(int rows, int columns, double initialValue) {
            this.shape = new Shape(rows, columns);
            this.dataType = DataType.FLOAT64;
            this.data = new double[shape.size()];
            Arrays.fill(this.data, initialValue);
            validateFiniteValues();
        }

        private int offset(int row, int column) {
            if (row < 0 || row >= shape.rows()
                    || column < 0 || column >= shape.columns()) {
                throw new IndexOutOfBoundsException(
                    "Index (" + row + ", " + column + ") outside " + shape
                );
            }
            return row * shape.columns() + column;
        }

        private void validateFiniteValues() {
            for (double value : data) {
                if (!Double.isFinite(value)) {
                    throw new IllegalArgumentException(
                        "Enterprise numeric data cannot contain NaN or infinity"
                    );
                }
            }
        }

        double get(int row, int column) {
            return data[offset(row, column)];
        }

        void set(int row, int column, double value) {
            if (!Double.isFinite(value)) {
                throw new IllegalArgumentException("Value must be finite");
            }
            data[offset(row, column)] = value;
        }

        Shape shape() {
            return shape;
        }

        DataType dataType() {
            return dataType;
        }

        NumericGrid map(java.util.function.DoubleUnaryOperator operation) {
            Objects.requireNonNull(operation);

            double[] result = new double[data.length];
            for (int i = 0; i < data.length; i++) {
                result[i] = operation.applyAsDouble(data[i]);
            }

            return new NumericGrid(shape.rows(), shape.columns(), result);
        }

        NumericGrid elementWiseMultiply(NumericGrid other) {
            requireSameShape(other);

            double[] result = new double[data.length];
            for (int i = 0; i < data.length; i++) {
                result[i] = data[i] * other.data[i];
            }

            return new NumericGrid(shape.rows(), shape.columns(), result);
        }

        NumericGrid add(NumericGrid other) {
            requireSameShape(other);

            double[] result = new double[data.length];
            for (int i = 0; i < data.length; i++) {
                result[i] = data[i] + other.data[i];
            }

            return new NumericGrid(shape.rows(), shape.columns(), result);
        }

        double[] row(int row) {
            if (row < 0 || row >= shape.rows()) {
                throw new IndexOutOfBoundsException("Invalid row");
            }

            double[] result = new double[shape.columns()];
            System.arraycopy(
                data,
                row * shape.columns(),
                result,
                0,
                shape.columns()
            );
            return result;
        }

        NumericGrid transpose() {
            double[] result = new double[data.length];

            for (int row = 0; row < shape.rows(); row++) {
                for (int column = 0; column < shape.columns(); column++) {
                    result[column * shape.rows() + row] =
                        get(row, column);
                }
            }

            return new NumericGrid(shape.columns(), shape.rows(), result);
        }

        double sum() {
            return Arrays.stream(data).sum();
        }

        double mean() {
            return sum() / data.length;
        }

        double max() {
            return Arrays.stream(data).max().orElseThrow();
        }

        private void requireSameShape(NumericGrid other) {
            if (!shape.equals(other.shape)) {
                throw new IllegalArgumentException(
                    "Shape mismatch: " + shape + " versus " + other.shape
                );
            }
        }

        @Override
        public String toString() {
            StringBuilder builder = new StringBuilder();

            for (int row = 0; row < shape.rows(); row++) {
                builder.append("[");
                for (int column = 0; column < shape.columns(); column++) {
                    builder.append(get(row, column));
                    if (column + 1 < shape.columns()) {
                        builder.append(", ");
                    }
                }
                builder.append("]");

                if (row + 1 < shape.rows()) {
                    builder.append(System.lineSeparator());
                }
            }

            return builder.toString();
        }
    }


    interface NumericPolicy {
        boolean accepts(double value);

        String description();
    }


    static final class FiniteValuePolicy implements NumericPolicy {
        @Override
        public boolean accepts(double value) {
            return Double.isFinite(value);
        }

        @Override
        public String description() {
            return "Only finite numeric values are accepted";
        }
    }


    static final class ThresholdPolicy implements NumericPolicy {
        private final double threshold;

        ThresholdPolicy(double threshold) {
            this.threshold = threshold;
        }

        @Override
        public boolean accepts(double value) {
            return value >= threshold;
        }

        @Override
        public String description() {
            return "Values must be greater than or equal to " + threshold;
        }
    }


    static final class NumericService {
        private final List<NumericPolicy> policies = new ArrayList<>();

        void registerPolicy(NumericPolicy policy) {
            policies.add(Objects.requireNonNull(policy));
        }

        void validate(NumericGrid grid) {
            for (int row = 0; row < grid.shape().rows(); row++) {
                for (int column = 0; column < grid.shape().columns(); column++) {
                    double value = grid.get(row, column);

                    for (NumericPolicy policy : policies) {
                        if (!policy.accepts(value)) {
                            throw new IllegalArgumentException(
                                "Value " + value + " violates: "
                                + policy.description()
                            );
                        }
                    }
                }
            }
        }

        NumericGrid normalizeRows(NumericGrid grid) {
            double[] result = new double[
                grid.shape().rows() * grid.shape().columns()
            ];

            for (int row = 0; row < grid.shape().rows(); row++) {
                double[] values = grid.row(row);
                double max = Arrays.stream(values).max().orElseThrow();

                if (max == 0.0) {
                    throw new ArithmeticException(
                        "Cannot normalize a row whose maximum is zero"
                    );
                }

                for (int column = 0; column < grid.shape().columns(); column++) {
                    result[row * grid.shape().columns() + column] =
                        values[column] / max;
                }
            }

            return new NumericGrid(
                grid.shape().rows(),
                grid.shape().columns(),
                result
            );
        }
    }


    static NumericGrid matrixMultiply(
        NumericGrid left,
        NumericGrid right
    ) {
        if (left.shape().columns() != right.shape().rows()) {
            throw new IllegalArgumentException(
                "Matrix multiplication requires matching inner dimensions"
            );
        }

        double[] result = new double[
            left.shape().rows() * right.shape().columns()
        ];

        for (int row = 0; row < left.shape().rows(); row++) {
            for (int column = 0; column < right.shape().columns(); column++) {
                double total = 0.0;

                for (int shared = 0; shared < left.shape().columns(); shared++) {
                    total += left.get(row, shared)
                        * right.get(shared, column);
                }

                result[row * right.shape().columns() + column] = total;
            }
        }

        return new NumericGrid(
            left.shape().rows(),
            right.shape().columns(),
            result
        );
    }


    static void print(String title, NumericGrid grid) {
        System.out.println(title);
        System.out.println(grid);
        System.out.println("shape=" + grid.shape()
            + ", dtype=" + grid.dataType());
    }


    static void fundamentals() {
        System.out.println("=== Enterprise numeric grid fundamentals ===");

        NumericGrid measurements = new NumericGrid(
            3,
            4,
            new double[]{
                82, 91, 77, 88,
                95, 84, 90, 73,
                68, 79, 85, 92
            }
        );

        print("Measurements", measurements);

        System.out.println("First value: " + measurements.get(0, 0));
        System.out.println(
            "Last value: "
            + measurements.get(
                measurements.shape().rows() - 1,
                measurements.shape().columns() - 1
            )
        );

        System.out.println(
            "Second row: " + Arrays.toString(measurements.row(1))
        );

        NumericGrid normalized = measurements.map(value -> value / 100.0);
        print("Element-wise normalization", normalized);

        NumericGrid transposed = measurements.transpose();
        print("Transposed grid", transposed);
    }


    static void enterprisePrediction() {
        System.out.println("\n=== Enterprise demand model ===");

        NumericGrid features = new NumericGrid(
            4,
            3,
            new double[]{
                1, 20, 0.0,
                1, 25, 0.5,
                1, 30, 1.0,
                1, 35, 1.5
            }
        );

        NumericGrid coefficients = new NumericGrid(
            3,
            1,
            new double[]{
                10,
                2.5,
                20
            }
        );

        NumericGrid predictions = matrixMultiply(features, coefficients);

        print("Feature matrix", features);
        print("Coefficient vector", coefficients);
        print("Predictions", predictions);

        System.out.println("Prediction mean: " + predictions.mean());
        System.out.println("Maximum prediction: " + predictions.max());
    }


    static void policyValidation() {
        System.out.println("\n=== Policy-driven numeric validation ===");

        NumericService service = new NumericService();
        service.registerPolicy(new FiniteValuePolicy());

        NumericGrid valid = new NumericGrid(
            2,
            2,
            new double[]{10, 20, 30, 40}
        );

        service.validate(valid);
        System.out.println("Finite-value policy accepted the grid.");

        NumericService thresholdService = new NumericService();
        thresholdService.registerPolicy(new FiniteValuePolicy());
        thresholdService.registerPolicy(new ThresholdPolicy(50));

        try {
            thresholdService.validate(valid);
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Policy rejection: " + error.getMessage()
            );
        }
    }


    static void failureHandling() {
        System.out.println("\n=== Invalid shape and indexing handling ===");

        NumericGrid left = new NumericGrid(2, 3, 1.0);
        NumericGrid incompatible = new NumericGrid(2, 2, 1.0);

        try {
            matrixMultiply(left, incompatible);
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected incompatible matrices: " + error.getMessage()
            );
        }

        try {
            left.get(10, 0);
        } catch (IndexOutOfBoundsException error) {
            System.out.println(
                "Rejected invalid index: " + error.getMessage()
            );
        }

        try {
            new NumericGrid(
                2,
                2,
                new double[]{1, 2, 3}
            );
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected invalid data size: " + error.getMessage()
            );
        }
    }


    public static void main(String[] args) {
        try {
            fundamentals();
            enterprisePrediction();
            policyValidation();
            failureHandling();

            System.out.println(
                "\nJava 17 NumPy fundamentals model completed."
            );
        } catch (RuntimeException error) {
            System.err.println(
                "Application failure: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
