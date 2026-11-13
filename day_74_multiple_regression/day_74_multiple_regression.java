import java.util.*;
import java.util.stream.Collectors;

/*
 * MULTIPLE REGRESSION
 *
 * Enterprise-oriented Java 17 implementation.
 *
 * Features:
 * - Explicit domain records
 * - Numerical and categorical predictors
 * - Dummy-variable encoding
 * - Interaction effects
 * - OLS estimation
 * - Coefficient standard errors
 * - Model diagnostics
 * - Immutable model results
 * - Prediction service
 * - Validation and custom exceptions
 */

public class MultipleRegression {

    enum PredictorType {
        NUMERICAL,
        CATEGORICAL
    }

    enum ModelStatus {
        CREATED,
        VALIDATED,
        FITTED,
        FAILED
    }

    record Employee(
        double salary,
        double experience,
        double performance,
        String education,
        String department
    ) {
        Employee {
            if (
                !Double.isFinite(salary) ||
                !Double.isFinite(experience) ||
                !Double.isFinite(performance)
            ) {
                throw new IllegalArgumentException(
                    "Employee contains invalid numerical values."
                );
            }

            if (
                experience < 0 ||
                performance < 0 ||
                education == null ||
                education.isBlank() ||
                department == null ||
                department.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Employee contains invalid attributes."
                );
            }
        }
    }

    record Interaction(String first, String second) {}

    record ModelMetrics(
        double rSquared,
        double adjustedRSquared,
        double rmse,
        double mae,
        double sse,
        int observations,
        int parameters,
        int degreesOfFreedom
    ) {}

    record Coefficient(
        String term,
        double estimate,
        double standardError
    ) {}

    record ModelResult(
        long version,
        List<Coefficient> coefficients,
        ModelMetrics metrics,
        List<Double> predictions,
        List<Double> residuals,
        Map<String, List<String>> categoryLevels
    ) {
        ModelResult {
            coefficients = List.copyOf(coefficients);
            predictions = List.copyOf(predictions);
            residuals = List.copyOf(residuals);

            Map<String, List<String>> copied = new LinkedHashMap<>();

            categoryLevels.forEach(
                (key, value) -> copied.put(key, List.copyOf(value))
            );

            categoryLevels = Collections.unmodifiableMap(copied);
        }
    }

    static class RegressionException extends RuntimeException {
        RegressionException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RegressionException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class SingularMatrixException extends RegressionException {
        SingularMatrixException(String message) {
            super(message);
        }
    }

    interface RegressionPolicy {
        void validate(int observations, int parameters);
    }

    static class MinimumSamplePolicy implements RegressionPolicy {

        @Override
        public void validate(int observations, int parameters) {
            if (observations <= parameters) {
                throw new ValidationException(
                    "Observations must exceed the number of parameters."
                );
            }
        }
    }

    static class MatrixSolver {

        static double[] solve(double[][] matrix, double[] vector) {
            int n = vector.length;

            double[][] a = new double[n][n + 1];

            for (int i = 0; i < n; i++) {
                System.arraycopy(matrix[i], 0, a[i], 0, n);
                a[i][n] = vector[i];
            }

            for (int col = 0; col < n; col++) {
                int pivot = col;

                for (int row = col + 1; row < n; row++) {
                    if (
                        Math.abs(a[row][col]) >
                        Math.abs(a[pivot][col])
                    ) {
                        pivot = row;
                    }
                }

                if (Math.abs(a[pivot][col]) < 1e-12) {
                    throw new SingularMatrixException(
                        "Perfect multicollinearity detected."
                    );
                }

                double[] temp = a[col];
                a[col] = a[pivot];
                a[pivot] = temp;

                double divisor = a[col][col];

                for (int j = col; j <= n; j++) {
                    a[col][j] /= divisor;
                }

                for (int row = 0; row < n; row++) {
                    if (row == col) continue;

                    double factor = a[row][col];

                    for (int j = col; j <= n; j++) {
                        a[row][j] -= factor * a[col][j];
                    }
                }
            }

            double[] result = new double[n];

            for (int i = 0; i < n; i++) {
                result[i] = a[i][n];
            }

            return result;
        }

        static double[][] inverse(double[][] matrix) {
            int n = matrix.length;

            double[][] a = new double[n][2 * n];

            for (int i = 0; i < n; i++) {
                System.arraycopy(matrix[i], 0, a[i], 0, n);
                a[i][n + i] = 1.0;
            }

            for (int col = 0; col < n; col++) {
                int pivot = col;

                for (int row = col + 1; row < n; row++) {
                    if (
                        Math.abs(a[row][col]) >
                        Math.abs(a[pivot][col])
                    ) {
                        pivot = row;
                    }
                }

                if (Math.abs(a[pivot][col]) < 1e-12) {
                    throw new SingularMatrixException(
                        "Matrix cannot be inverted."
                    );
                }

                double[] temp = a[col];
                a[col] = a[pivot];
                a[pivot] = temp;

                double divisor = a[col][col];

                for (int j = 0; j < 2 * n; j++) {
                    a[col][j] /= divisor;
                }

                for (int row = 0; row < n; row++) {
                    if (row == col) continue;

                    double factor = a[row][col];

                    for (int j = 0; j < 2 * n; j++) {
                        a[row][j] -= factor * a[col][j];
                    }
                }
            }

            double[][] inverse = new double[n][n];

            for (int i = 0; i < n; i++) {
                System.arraycopy(
                    a[i], n, inverse[i], 0, n
                );
            }

            return inverse;
        }
    }

    static class DesignMatrixBuilder {

        private final List<Interaction> interactions;

        private final Map<String, List<String>> categoryLevels =
            new LinkedHashMap<>();

        private final List<String> termNames = new ArrayList<>();

        DesignMatrixBuilder(List<Interaction> interactions) {
            this.interactions = List.copyOf(interactions);
        }

        void fitEncoding(List<Employee> employees) {
            categoryLevels.clear();

            List<String> educationLevels = employees.stream()
                .map(Employee::education)
                .distinct()
                .sorted()
                .toList();

            List<String> departmentLevels = employees.stream()
                .map(Employee::department)
                .distinct()
                .sorted()
                .toList();

            if (
                educationLevels.size() < 2 ||
                departmentLevels.size() < 2
            ) {
                throw new ValidationException(
                    "Categorical predictors require at least two levels."
                );
            }

            categoryLevels.put("education", educationLevels);
            categoryLevels.put("department", departmentLevels);

            termNames.clear();

            termNames.add("Intercept");
            termNames.add("experience");
            termNames.add("performance");

            educationLevels.stream()
                .skip(1)
                .forEach(level ->
                    termNames.add("education[" + level + "]")
                );

            departmentLevels.stream()
                .skip(1)
                .forEach(level ->
                    termNames.add("department[" + level + "]")
                );

            for (Interaction interaction : interactions) {
                if (
                    !List.of("experience", "performance")
                        .contains(interaction.first()) ||
                    !List.of("experience", "performance")
                        .contains(interaction.second())
                ) {
                    throw new ValidationException(
                        "Interactions must use supported numerical predictors."
                    );
                }

                termNames.add(
                    interaction.first() + ":" + interaction.second()
                );
            }
        }

        double[] encode(Employee employee) {
            List<Double> values = new ArrayList<>();

            values.add(1.0);
            values.add(employee.experience());
            values.add(employee.performance());

            for (
                String level :
                categoryLevels.get("education").stream().skip(1).toList()
            ) {
                values.add(
                    employee.education().equals(level) ? 1.0 : 0.0
                );
            }

            for (
                String level :
                categoryLevels.get("department").stream().skip(1).toList()
            ) {
                values.add(
                    employee.department().equals(level) ? 1.0 : 0.0
                );
            }

            for (Interaction interaction : interactions) {
                double first = numericalValue(
                    employee, interaction.first()
                );

                double second = numericalValue(
                    employee, interaction.second()
                );

                values.add(first * second);
            }

            return values.stream()
                .mapToDouble(Double::doubleValue)
                .toArray();
        }

        private double numericalValue(Employee employee, String name) {
            return switch (name) {
                case "experience" -> employee.experience();
                case "performance" -> employee.performance();
                default -> throw new ValidationException(
                    "Unsupported numerical variable."
                );
            };
        }

        List<String> getTermNames() {
            return List.copyOf(termNames);
        }

        Map<String, List<String>> getCategoryLevels() {
            return Map.copyOf(categoryLevels);
        }
    }

    static class RegressionService {

        private final RegressionPolicy policy;
        private final DesignMatrixBuilder builder;

        private ModelStatus status = ModelStatus.CREATED;
        private long version = 0;
        private double[] coefficients;

        RegressionService(RegressionPolicy policy) {
            this.policy = policy;

            this.builder = new DesignMatrixBuilder(
                List.of(
                    new Interaction(
                        "experience",
                        "performance"
                    )
                )
            );
        }

        ModelResult fit(List<Employee> employees) {
            try {
                if (employees == null || employees.isEmpty()) {
                    throw new ValidationException("Dataset is empty.");
                }

                builder.fitEncoding(employees);

                int n = employees.size();
                int p = builder.getTermNames().size();

                policy.validate(n, p);

                status = ModelStatus.VALIDATED;

                double[][] x = new double[n][p];
                double[] y = new double[n];

                for (int i = 0; i < n; i++) {
                    x[i] = builder.encode(employees.get(i));
                    y[i] = employees.get(i).salary();
                }

                double[][] xtx = new double[p][p];
                double[] xty = new double[p];

                for (int i = 0; i < n; i++) {
                    for (int j = 0; j < p; j++) {
                        xty[j] += x[i][j] * y[i];

                        for (int k = 0; k < p; k++) {
                            xtx[j][k] += x[i][j] * x[i][k];
                        }
                    }
                }

                coefficients = MatrixSolver.solve(xtx, xty);

                double[] predictions = new double[n];
                double[] residuals = new double[n];

                double mean = Arrays.stream(y).average().orElseThrow();

                double sse = 0.0;
                double sst = 0.0;
                double absoluteError = 0.0;

                for (int i = 0; i < n; i++) {
                    for (int j = 0; j < p; j++) {
                        predictions[i] +=
                            x[i][j] * coefficients[j];
                    }

                    residuals[i] = y[i] - predictions[i];

                    sse += Math.pow(residuals[i], 2);
                    sst += Math.pow(y[i] - mean, 2);

                    absoluteError += Math.abs(residuals[i]);
                }

                if (sst < 1e-12) {
                    throw new ValidationException(
                        "Target variance is zero."
                    );
                }

                double r2 = 1.0 - sse / sst;

                double adjustedR2 =
                    1.0 - (1.0 - r2) * (n - 1.0) / (n - p);

                double rmse = Math.sqrt(sse / n);
                double mae = absoluteError / n;

                double mse = sse / (n - p);

                double[][] inverse = MatrixSolver.inverse(xtx);

                List<Coefficient> coefficientTable =
                    new ArrayList<>();

                List<String> terms = builder.getTermNames();

                for (int i = 0; i < p; i++) {
                    double standardError = Math.sqrt(
                        Math.max(0.0, mse * inverse[i][i])
                    );

                    coefficientTable.add(
                        new Coefficient(
                            terms.get(i),
                            coefficients[i],
                            standardError
                        )
                    );
                }

                ModelMetrics metrics = new ModelMetrics(
                    r2,
                    adjustedR2,
                    rmse,
                    mae,
                    sse,
                    n,
                    p,
                    n - p
                );

                status = ModelStatus.FITTED;

                return new ModelResult(
                    ++version,
                    coefficientTable,
                    metrics,
                    Arrays.stream(predictions).boxed().toList(),
                    Arrays.stream(residuals).boxed().toList(),
                    builder.getCategoryLevels()
                );

            } catch (RuntimeException exception) {
                status = ModelStatus.FAILED;
                throw exception;
            }
        }

        double predict(Employee employee) {
            if (status != ModelStatus.FITTED || coefficients == null) {
                throw new RegressionException(
                    "Prediction requires a fitted model."
                );
            }

            double[] features = builder.encode(employee);

            double result = 0.0;

            for (int i = 0; i < coefficients.length; i++) {
                result += features[i] * coefficients[i];
            }

            return result;
        }

        ModelStatus getStatus() {
            return status;
        }
    }

    static void printReport(ModelResult result) {
        System.out.println("\nCOEFFICIENT TABLE");

        System.out.printf(
            "%-35s %-18s %-18s%n",
            "Term",
            "Estimate",
            "Standard Error"
        );

        for (Coefficient coefficient : result.coefficients()) {
            System.out.printf(
                "%-35s %-18.4f %-18.4f%n",
                coefficient.term(),
                coefficient.estimate(),
                coefficient.standardError()
            );
        }

        ModelMetrics metrics = result.metrics();

        System.out.println("\nMODEL PERFORMANCE");

        System.out.printf("R-squared:          %.4f%n", metrics.rSquared());
        System.out.printf(
            "Adjusted R-squared: %.4f%n",
            metrics.adjustedRSquared()
        );
        System.out.printf("RMSE:               %.2f%n", metrics.rmse());
        System.out.printf("MAE:                %.2f%n", metrics.mae());
        System.out.printf("Observations:       %d%n", metrics.observations());
        System.out.printf("Parameters:         %d%n", metrics.parameters());

        System.out.println("\nREFERENCE CATEGORIES");

        result.categoryLevels().forEach((name, levels) ->
            System.out.println(
                name + ": " + levels.get(0)
            )
        );
    }

    public static void main(String[] args) {

        List<Employee> employees = List.of(
            new Employee(45000, 1, 3, "Bachelor", "Sales"),
            new Employee(49000, 2, 4, "Bachelor", "Sales"),
            new Employee(53000, 3, 3, "Master", "Sales"),
            new Employee(57000, 4, 4, "Master", "Technology"),
            new Employee(65000, 5, 5, "Master", "Technology"),
            new Employee(61000, 4, 5, "Bachelor", "Technology"),
            new Employee(72000, 6, 4, "PhD", "Technology"),
            new Employee(76000, 7, 5, "PhD", "Technology"),
            new Employee(50000, 2, 3, "Bachelor", "Operations"),
            new Employee(55000, 3, 4, "Master", "Operations"),
            new Employee(59000, 4, 4, "Bachelor", "Operations"),
            new Employee(68000, 6, 5, "PhD", "Operations"),
            new Employee(48000, 2, 2, "Bachelor", "Sales"),
            new Employee(62000, 5, 4, "Master", "Sales"),
            new Employee(70000, 6, 5, "PhD", "Technology"),
            new Employee(54000, 3, 3, "Bachelor", "Operations"),
            new Employee(74000, 7, 5, "Master", "Technology"),
            new Employee(58000, 4, 3, "Master", "Sales"),
            new Employee(64000, 5, 5, "Bachelor", "Operations"),
            new Employee(79000, 8, 5, "PhD", "Technology")
        );

        RegressionService service = new RegressionService(
            new MinimumSamplePolicy()
        );

        try {
            ModelResult result = service.fit(employees);

            printReport(result);

            Employee newEmployee = new Employee(
                0,
                5,
                4,
                "Master",
                "Technology"
            );

            System.out.println("\nPREDICTION");

            System.out.printf(
                "Predicted salary: %.2f%n",
                service.predict(newEmployee)
            );

            System.out.println(
                "\nModel status: " + service.getStatus()
            );

            System.out.println(
                "Model version: " + result.version()
            );

        } catch (RegressionException exception) {
            System.err.println(
                "Regression operation failed: " + exception.getMessage()
            );
        }
    }
}
