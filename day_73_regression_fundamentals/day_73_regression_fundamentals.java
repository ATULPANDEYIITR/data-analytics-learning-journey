import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

/*
 * Regression Fundamentals
 *
 * Enterprise-oriented ordinary least squares implementation.
 *
 * Features:
 * - Immutable domain records
 * - Regression service
 * - Model lifecycle
 * - Coefficient estimation
 * - Residual analysis
 * - Regression metrics
 * - Assumption indicators
 * - Confidence intervals
 * - Input validation
 * - Custom exceptions
 * - Automated verification
 */

public class RegressionFundamentals {

    enum ModelStatus {
        CREATED,
        FITTED,
        FAILED
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

    record Observation(double x, double y) {
        Observation {
            if (!Double.isFinite(x) || !Double.isFinite(y)) {
                throw new ValidationException(
                    "Observations must contain finite numeric values."
                );
            }
        }
    }

    record Dataset(String name, List<Observation> observations) {

        Dataset {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Dataset name is required."
                );
            }

            if (observations == null || observations.size() < 3) {
                throw new ValidationException(
                    "At least three observations are required."
                );
            }

            observations = List.copyOf(observations);
        }

        int size() {
            return observations.size();
        }
    }

    record RegressionMetrics(
        double mae,
        double mse,
        double rmse,
        double rSquared,
        double adjustedRSquared,
        double residualStandardError
    ) {}

    record CoefficientStatistics(
        double interceptStandardError,
        double slopeStandardError,
        double slopeLowerBound,
        double slopeUpperBound
    ) {}

    record ResidualRecord(
        double actual,
        double predicted,
        double residual
    ) {}

    record Diagnostic(
        String name,
        double statistic,
        boolean indicatorPassed,
        String interpretation
    ) {}

    record ModelResult(
        String modelName,
        double intercept,
        double slope,
        int observations,
        RegressionMetrics metrics,
        CoefficientStatistics coefficientStatistics,
        List<ResidualRecord> residuals,
        List<Diagnostic> diagnostics
    ) {
        ModelResult {
            residuals = List.copyOf(residuals);
            diagnostics = List.copyOf(diagnostics);
        }
    }

    interface RegressionModel {
        ModelResult fit(Dataset dataset);

        double predict(double x);

        ModelStatus status();
    }

    static class OrdinaryLeastSquares implements RegressionModel {

        private final String modelName;
        private final double tolerance;

        private ModelStatus status = ModelStatus.CREATED;

        private double slope;
        private double intercept;

        private Dataset trainingDataset;
        private ModelResult result;

        OrdinaryLeastSquares(String modelName) {
            this(modelName, 1e-12);
        }

        OrdinaryLeastSquares(String modelName, double tolerance) {

            if (modelName == null || modelName.isBlank()) {
                throw new ValidationException(
                    "Model name is required."
                );
            }

            if (!Double.isFinite(tolerance) || tolerance <= 0) {
                throw new ValidationException(
                    "Tolerance must be positive."
                );
            }

            this.modelName = modelName;
            this.tolerance = tolerance;
        }

        @Override
        public synchronized ModelResult fit(Dataset dataset) {

            Objects.requireNonNull(dataset, "Dataset cannot be null.");

            try {
                List<Observation> rows = dataset.observations();

                int n = rows.size();

                double xMean = rows.stream()
                    .mapToDouble(Observation::x)
                    .average()
                    .orElseThrow();

                double yMean = rows.stream()
                    .mapToDouble(Observation::y)
                    .average()
                    .orElseThrow();

                double sxx = 0;
                double syy = 0;
                double sxy = 0;

                for (Observation row : rows) {

                    double dx = row.x() - xMean;
                    double dy = row.y() - yMean;

                    sxx += dx * dx;
                    syy += dy * dy;
                    sxy += dx * dy;
                }

                if (sxx <= tolerance) {
                    throw new ValidationException(
                        "Predictor has insufficient variance."
                    );
                }

                double candidateSlope = sxy / sxx;

                double candidateIntercept =
                    yMean - candidateSlope * xMean;

                List<ResidualRecord> residuals = new ArrayList<>();

                double sse = 0;
                double absoluteError = 0;

                for (Observation row : rows) {

                    double predicted =
                        candidateIntercept + candidateSlope * row.x();

                    double residual = row.y() - predicted;

                    residuals.add(
                        new ResidualRecord(
                            row.y(),
                            predicted,
                            residual
                        )
                    );

                    sse += residual * residual;
                    absoluteError += Math.abs(residual);
                }

                double rSquared = syy > tolerance
                    ? 1.0 - sse / syy
                    : (sse <= tolerance ? 1.0 : 0.0);

                double mse = sse / n;

                double adjustedRSquared =
                    1.0 - (1.0 - rSquared) *
                    (n - 1.0) / (n - 2.0);

                double residualVariance = sse / (n - 2.0);

                double slopeSE = Math.sqrt(
                    residualVariance / sxx
                );

                double interceptSE = Math.sqrt(
                    residualVariance *
                    (1.0 / n + xMean * xMean / sxx)
                );

                double criticalValue = 1.96;

                RegressionMetrics metrics = new RegressionMetrics(
                    absoluteError / n,
                    mse,
                    Math.sqrt(mse),
                    rSquared,
                    adjustedRSquared,
                    Math.sqrt(residualVariance)
                );

                CoefficientStatistics statistics =
                    new CoefficientStatistics(
                        interceptSE,
                        slopeSE,
                        candidateSlope - criticalValue * slopeSE,
                        candidateSlope + criticalValue * slopeSE
                    );

                List<Diagnostic> diagnostics =
                    calculateDiagnostics(residuals);

                ModelResult candidateResult = new ModelResult(
                    modelName,
                    candidateIntercept,
                    candidateSlope,
                    n,
                    metrics,
                    statistics,
                    residuals,
                    diagnostics
                );

                // Publish the new model state only after successful fitting.
                this.slope = candidateSlope;
                this.intercept = candidateIntercept;
                this.trainingDataset = dataset;
                this.result = candidateResult;
                this.status = ModelStatus.FITTED;

                return candidateResult;

            } catch (RuntimeException exception) {
                // Preserve a previously fitted model after a failed refit.
                if (status != ModelStatus.FITTED) {
                    status = ModelStatus.FAILED;
                }

                throw exception;
            }
        }

        private List<Diagnostic> calculateDiagnostics(
            List<ResidualRecord> rows
        ) {

            int n = rows.size();

            List<Double> residuals = rows.stream()
                .map(ResidualRecord::residual)
                .toList();

            double mean = residuals.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0);

            double variance = residuals.stream()
                .mapToDouble(value -> Math.pow(value - mean, 2))
                .sum() / (n - 1);

            double skewness = 0;

            if (variance > 0) {
                skewness = residuals.stream()
                    .mapToDouble(value ->
                        Math.pow(
                            (value - mean) / Math.sqrt(variance),
                            3
                        )
                    )
                    .sum() / n;
            }

            double lagNumerator = 0;
            double denominator = 0;

            for (int i = 0; i < n; i++) {

                double current = residuals.get(i);

                denominator += current * current;

                if (i > 0) {
                    lagNumerator += current * residuals.get(i - 1);
                }
            }

            double lagCorrelation = denominator > 0
                ? lagNumerator / denominator
                : 0;

            List<ResidualRecord> ordered = rows.stream()
                .sorted(
                    Comparator.comparingDouble(
                        ResidualRecord::predicted
                    )
                )
                .toList();

            int split = n / 2;

            double lowerVariance = sampleVariance(
                ordered.subList(0, split)
                    .stream()
                    .map(ResidualRecord::residual)
                    .toList()
            );

            double upperVariance = sampleVariance(
                ordered.subList(split, n)
                    .stream()
                    .map(ResidualRecord::residual)
                    .toList()
            );

            double varianceRatio =
                Math.max(lowerVariance, upperVariance) /
                Math.max(
                    Math.min(lowerVariance, upperVariance),
                    1e-15
                );

            return List.of(
                new Diagnostic(
                    "Residual mean",
                    Math.abs(mean),
                    Math.abs(mean) < 1e-8,
                    "OLS with an intercept should produce approximately zero mean residuals."
                ),
                new Diagnostic(
                    "Lag-one correlation",
                    Math.abs(lagCorrelation),
                    Math.abs(lagCorrelation) < 0.3,
                    "Descriptive indicator of residual independence."
                ),
                new Diagnostic(
                    "Residual variance ratio",
                    varianceRatio,
                    varianceRatio < 4,
                    "Compares residual variance across fitted-value groups."
                ),
                new Diagnostic(
                    "Absolute skewness",
                    Math.abs(skewness),
                    Math.abs(skewness) < 1,
                    "Descriptive indicator of residual symmetry."
                )
            );
        }

        private static double sampleVariance(List<Double> values) {

            if (values.size() < 2) return 0;

            double average = values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0);

            return values.stream()
                .mapToDouble(value ->
                    Math.pow(value - average, 2)
                )
                .sum() / (values.size() - 1);
        }

        @Override
        public synchronized double predict(double x) {

            if (status != ModelStatus.FITTED) {
                throw new RegressionException(
                    "Model has not been fitted."
                );
            }

            if (!Double.isFinite(x)) {
                throw new ValidationException(
                    "Prediction input must be finite."
                );
            }

            return intercept + slope * x;
        }

        @Override
        public ModelStatus status() {
            return status;
        }

        public Optional<ModelResult> result() {
            return Optional.ofNullable(result);
        }

        public String equation() {

            if (status != ModelStatus.FITTED) {
                throw new RegressionException(
                    "Model has not been fitted."
                );
            }

            return "y = " + intercept + " + " + slope + "x";
        }
    }

    static class RegressionService {

        private final Map<String, RegressionModel> models =
            new java.util.concurrent.ConcurrentHashMap<>();

        public void register(
            String name,
            RegressionModel model
        ) {

            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Registration name is required."
                );
            }

            Objects.requireNonNull(model);

            RegressionModel previous =
                models.putIfAbsent(name, model);

            if (previous != null) {
                throw new RegressionException(
                    "Model name already registered."
                );
            }
        }

        public RegressionModel get(String name) {

            RegressionModel model = models.get(name);

            if (model == null) {
                throw new RegressionException(
                    "Model does not exist: " + name
                );
            }

            return model;
        }

        public boolean remove(String name) {
            return models.remove(name) != null;
        }

        public List<String> registeredModels() {
            return models.keySet().stream()
                .sorted()
                .toList();
        }
    }

    static Dataset examinationDataset() {

        return new Dataset(
            "Student Examination Performance",
            List.of(
                new Observation(1, 42),
                new Observation(2, 46),
                new Observation(3, 53),
                new Observation(4, 57),
                new Observation(5, 61),
                new Observation(6, 68),
                new Observation(7, 72),
                new Observation(8, 79)
            )
        );
    }

    static void runTests() {

        Dataset perfect = new Dataset(
            "Perfect Linear Dataset",
            List.of(
                new Observation(1, 3),
                new Observation(2, 5),
                new Observation(3, 7),
                new Observation(4, 9),
                new Observation(5, 11)
            )
        );

        OrdinaryLeastSquares model =
            new OrdinaryLeastSquares("test-model");

        ModelResult result = model.fit(perfect);

        if (Math.abs(result.slope() - 2) > 1e-10) {
            throw new AssertionError("Slope test failed.");
        }

        if (Math.abs(result.intercept() - 1) > 1e-10) {
            throw new AssertionError("Intercept test failed.");
        }

        if (Math.abs(model.predict(6) - 13) > 1e-10) {
            throw new AssertionError("Prediction test failed.");
        }

        if (Math.abs(result.metrics().rSquared() - 1) > 1e-10) {
            throw new AssertionError("R-squared test failed.");
        }

        try {
            Dataset invalid = new Dataset(
                "Constant Predictor",
                List.of(
                    new Observation(1, 2),
                    new Observation(1, 3),
                    new Observation(1, 4)
                )
            );

            new OrdinaryLeastSquares("invalid").fit(invalid);

            throw new AssertionError(
                "Constant predictor was accepted."
            );

        } catch (ValidationException expected) {
            // Expected validation failure.
        }

        System.out.println("\nAll Java 17 tests passed.");
    }

    static void printReport(ModelResult result) {

        System.out.println("\nENTERPRISE REGRESSION REPORT");
        System.out.println("====================================");

        System.out.println("Model: " + result.modelName());
        System.out.println("Observations: " + result.observations());

        System.out.printf(
            "Equation: y = %.6f + %.6fx%n",
            result.intercept(),
            result.slope()
        );

        System.out.println("\nREGRESSION METRICS");

        RegressionMetrics metrics = result.metrics();

        System.out.printf("MAE: %.6f%n", metrics.mae());
        System.out.printf("MSE: %.6f%n", metrics.mse());
        System.out.printf("RMSE: %.6f%n", metrics.rmse());
        System.out.printf("R-squared: %.6f%n", metrics.rSquared());

        System.out.printf(
            "Adjusted R-squared: %.6f%n",
            metrics.adjustedRSquared()
        );

        System.out.printf(
            "Residual standard error: %.6f%n",
            metrics.residualStandardError()
        );

        System.out.println("\nCOEFFICIENT UNCERTAINTY");

        CoefficientStatistics statistics =
            result.coefficientStatistics();

        System.out.printf(
            "Intercept SE: %.6f%n",
            statistics.interceptStandardError()
        );

        System.out.printf(
            "Slope SE: %.6f%n",
            statistics.slopeStandardError()
        );

        System.out.printf(
            "Approximate slope confidence interval: [%.6f, %.6f]%n",
            statistics.slopeLowerBound(),
            statistics.slopeUpperBound()
        );

        System.out.println("\nRESIDUALS");

        for (ResidualRecord row : result.residuals()) {
            System.out.printf(
                "Actual: %.2f | Predicted: %.2f | Residual: %.2f%n",
                row.actual(),
                row.predicted(),
                row.residual()
            );
        }

        System.out.println("\nASSUMPTION INDICATORS");

        for (Diagnostic diagnostic : result.diagnostics()) {
            System.out.printf(
                "%s: %.6f [%s]%n",
                diagnostic.name(),
                diagnostic.statistic(),
                diagnostic.indicatorPassed()
                    ? "PASS"
                    : "INVESTIGATE"
            );

            System.out.println(diagnostic.interpretation());
        }
    }

    public static void main(String[] args) {

        try {

            Dataset dataset = examinationDataset();

            OrdinaryLeastSquares model =
                new OrdinaryLeastSquares(
                    "examination-performance"
                );

            RegressionService service = new RegressionService();

            service.register("academic-model", model);

            ModelResult result = service.get("academic-model")
                .fit(dataset);

            printReport(result);

            System.out.println("\nNEW PREDICTIONS");

            for (double hours : List.of(2.5, 5.5, 9.0)) {

                System.out.printf(
                    "Study hours: %.1f | Predicted marks: %.3f%n",
                    hours,
                    model.predict(hours)
                );
            }

            System.out.println("\nREGISTERED MODELS");
            System.out.println(service.registeredModels());

            runTests();

        } catch (RegressionException exception) {

            System.err.println(
                "Regression operation failed: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
