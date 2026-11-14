import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * Regression Diagnostics Enterprise Engine
 *
 * Java 17
 *
 * Components:
 * - Immutable observation records
 * - OLS estimation service
 * - Multicollinearity assessment
 * - Breusch-Pagan heteroscedasticity testing
 * - Residual normality diagnostics
 * - Leverage and influence assessment
 * - HC3 covariance estimation
 * - Configurable diagnostic policies
 * - Explicit model lifecycle and validation
 */

public class RegressionDiagnostics {

    enum ModelState {
        CREATED,
        FITTED,
        DIAGNOSTICS_COMPLETED
    }

    enum Severity {
        PASS,
        WARNING,
        FAIL
    }

    enum DiagnosticCategory {
        MULTICOLLINEARITY,
        HETEROSCEDASTICITY,
        RESIDUAL_NORMALITY,
        HIGH_LEVERAGE,
        INFLUENTIAL_OBSERVATION,
        LARGE_RESIDUAL
    }

    static class RegressionException extends RuntimeException {
        RegressionException(String message) {
            super(message);
        }
    }

    record Observation(
        String id,
        List<Double> features,
        double target
    ) {
        Observation {
            if (id == null || id.isBlank()) {
                throw new RegressionException(
                    "Observation ID is required."
                );
            }

            Objects.requireNonNull(features);

            features = List.copyOf(features);

            if (features.isEmpty()) {
                throw new RegressionException(
                    "At least one predictor is required."
                );
            }

            if (!Double.isFinite(target) ||
                features.stream().anyMatch(
                    value -> value == null ||
                        !Double.isFinite(value)
                )) {
                throw new RegressionException(
                    "Non-finite observation value."
                );
            }
        }
    }

    record DiagnosticFinding(
        DiagnosticCategory category,
        String subject,
        double statistic,
        double threshold,
        Severity severity,
        String explanation
    ) {}

    record RegressionPolicy(
        double vifWarning,
        double vifCritical,
        double significanceLevel,
        double cookMultiplier,
        double leverageMultiplier,
        double studentizedLimit
    ) {
        RegressionPolicy {
            if (vifWarning <= 0 ||
                vifCritical <= vifWarning ||
                significanceLevel <= 0 ||
                significanceLevel >= 1 ||
                cookMultiplier <= 0 ||
                leverageMultiplier <= 0 ||
                studentizedLimit <= 0) {
                throw new IllegalArgumentException(
                    "Invalid diagnostic policy."
                );
            }
        }

        static RegressionPolicy standard() {
            return new RegressionPolicy(
                5.0, 10.0, 0.05, 4.0, 2.0, 3.0
            );
        }
    }

    record ModelResult(
        List<Double> coefficients,
        List<Double> fittedValues,
        List<Double> residuals,
        double rSquared,
        double adjustedRSquared,
        double residualStandardError,
        int sampleSize,
        int parameterCount
    ) {
        ModelResult {
            coefficients = List.copyOf(coefficients);
            fittedValues = List.copyOf(fittedValues);
            residuals = List.copyOf(residuals);
        }
    }

    static final class LinearAlgebra {

        static double dot(
            List<Double> a,
            List<Double> b
        ) {
            if (a.size() != b.size()) {
                throw new RegressionException(
                    "Vector dimension mismatch."
                );
            }

            double result = 0;

            for (int i = 0; i < a.size(); i++) {
                result += a.get(i) * b.get(i);
            }

            return result;
        }

        static double[][] transpose(double[][] matrix) {
            double[][] result = new double[
                matrix[0].length
            ][matrix.length];

            for (int i = 0; i < matrix.length; i++) {
                for (int j = 0; j < matrix[i].length; j++) {
                    result[j][i] = matrix[i][j];
                }
            }

            return result;
        }

        static double[][] multiply(
            double[][] a,
            double[][] b
        ) {
            if (a[0].length != b.length) {
                throw new RegressionException(
                    "Invalid matrix dimensions."
                );
            }

            double[][] result = new double[
                a.length
            ][b[0].length];

            for (int i = 0; i < a.length; i++) {
                for (int k = 0; k < b.length; k++) {
                    for (int j = 0; j < b[0].length; j++) {
                        result[i][j] +=
                            a[i][k] * b[k][j];
                    }
                }
            }

            return result;
        }

        static double[] solve(
            double[][] source,
            double[] rhs
        ) {
            int n = rhs.length;

            double[][] matrix = new double[n][n + 1];

            for (int i = 0; i < n; i++) {
                if (source[i].length != n) {
                    throw new RegressionException(
                        "Matrix must be square."
                    );
                }

                System.arraycopy(
                    source[i], 0, matrix[i], 0, n
                );

                matrix[i][n] = rhs[i];
            }

            for (int col = 0; col < n; col++) {
                int pivot = col;

                for (int row = col + 1; row < n; row++) {
                    if (Math.abs(matrix[row][col]) >
                        Math.abs(matrix[pivot][col])) {
                        pivot = row;
                    }
                }

                if (Math.abs(matrix[pivot][col]) < 1e-12) {
                    throw new RegressionException(
                        "Singular matrix detected."
                    );
                }

                double[] temp = matrix[col];
                matrix[col] = matrix[pivot];
                matrix[pivot] = temp;

                double divisor = matrix[col][col];

                for (int j = col; j <= n; j++) {
                    matrix[col][j] /= divisor;
                }

                for (int row = 0; row < n; row++) {
                    if (row == col) continue;

                    double factor = matrix[row][col];

                    for (int j = col; j <= n; j++) {
                        matrix[row][j] -=
                            factor * matrix[col][j];
                    }
                }
            }

            double[] result = new double[n];

            for (int i = 0; i < n; i++) {
                result[i] = matrix[i][n];
            }

            return result;
        }

        static double[][] inverse(double[][] matrix) {
            int n = matrix.length;

            double[][] result = new double[n][n];

            for (int col = 0; col < n; col++) {
                double[] unit = new double[n];
                unit[col] = 1;

                double[] solution = solve(matrix, unit);

                for (int row = 0; row < n; row++) {
                    result[row][col] = solution[row];
                }
            }

            return result;
        }
    }

    static final class Statistics {

        static double mean(double[] values) {
            return Arrays.stream(values).average()
                .orElseThrow();
        }

        static double chiSquareSurvival(
            double statistic,
            int degrees
        ) {
            if (statistic < 0 || degrees <= 0) {
                throw new IllegalArgumentException(
                    "Invalid chi-square parameters."
                );
            }

            double a = degrees / 2.0;
            double x = statistic / 2.0;

            if (x == 0) return 1.0;

            double factor = Math.exp(
                -x + a * Math.log(x) - logGamma(a)
            );

            if (x < a + 1) {
                double ap = a;
                double term = 1.0 / a;
                double sum = term;

                for (int i = 0; i < 1000; i++) {
                    ap++;
                    term *= x / ap;
                    sum += term;

                    if (Math.abs(term) <
                        Math.abs(sum) * 1e-14) {
                        break;
                    }
                }

                return Math.max(
                    0, Math.min(1, 1 - sum * factor)
                );
            }

            double b = x + 1 - a;
            double c = 1e300;
            double d = 1 / b;
            double h = d;

            for (int i = 1; i < 1000; i++) {
                double an = -i * (i - a);
                b += 2;

                d = an * d + b;
                if (Math.abs(d) < 1e-300) d = 1e-300;

                c = b + an / c;
                if (Math.abs(c) < 1e-300) c = 1e-300;

                d = 1 / d;

                double delta = d * c;
                h *= delta;

                if (Math.abs(delta - 1) < 1e-14) break;
            }

            return Math.max(
                0, Math.min(1, factor * h)
            );
        }

        static double logGamma(double z) {
            double[] coefficients = {
                676.5203681218851,
                -1259.1392167224028,
                771.3234287776531,
                -176.6150291621406,
                12.507343278686905,
                -0.13857109526572012,
                9.9843695780195716e-6,
                1.5056327351493116e-7
            };

            if (z < 0.5) {
                return Math.log(Math.PI)
                    - Math.log(Math.sin(Math.PI * z))
                    - logGamma(1 - z);
            }

            z -= 1;

            double sum = 0.99999999999980993;

            for (int i = 0; i < coefficients.length; i++) {
                sum += coefficients[i] / (z + i + 1);
            }

            double t = z + coefficients.length - 0.5;

            return 0.5 * Math.log(2 * Math.PI)
                + (z + 0.5) * Math.log(t)
                - t + Math.log(sum);
        }
    }

    static final class RegressionService {

        private final List<Observation> observations;
        private final int n;
        private final int p;

        private final double[][] X;
        private final double[] y;

        private double[] beta;
        private double[] fitted;
        private double[] residuals;
        private double[][] xtxInverse;

        private double sse;
        private double mse;
        private double rSquared;

        private ModelState state = ModelState.CREATED;

        RegressionService(List<Observation> input) {
            if (input == null || input.isEmpty()) {
                throw new RegressionException(
                    "Observations cannot be empty."
                );
            }

            observations = List.copyOf(input);

            Set<String> identifiers = new HashSet<>();

            int features = observations.get(0)
                .features().size();

            for (Observation observation : observations) {
                if (!identifiers.add(observation.id())) {
                    throw new RegressionException(
                        "Duplicate observation ID."
                    );
                }

                if (observation.features().size() != features) {
                    throw new RegressionException(
                        "Inconsistent feature dimensions."
                    );
                }
            }

            n = observations.size();
            p = features + 1;

            if (n <= p) {
                throw new RegressionException(
                    "Insufficient observations."
                );
            }

            X = new double[n][p];
            y = new double[n];

            for (int i = 0; i < n; i++) {
                X[i][0] = 1.0;

                for (int j = 0; j < features; j++) {
                    X[i][j + 1] =
                        observations.get(i).features().get(j);
                }

                y[i] = observations.get(i).target();
            }
        }

        void fit() {
            if (state != ModelState.CREATED) {
                throw new RegressionException(
                    "Invalid model state transition."
                );
            }

            double[][] xt = LinearAlgebra.transpose(X);
            double[][] xtx = LinearAlgebra.multiply(xt, X);

            xtxInverse = LinearAlgebra.inverse(xtx);

            double[] xty = new double[p];

            for (int i = 0; i < p; i++) {
                for (int j = 0; j < n; j++) {
                    xty[i] += xt[i][j] * y[j];
                }
            }

            beta = new double[p];

            for (int i = 0; i < p; i++) {
                for (int j = 0; j < p; j++) {
                    beta[i] += xtxInverse[i][j] * xty[j];
                }
            }

            fitted = new double[n];
            residuals = new double[n];

            for (int i = 0; i < n; i++) {
                for (int j = 0; j < p; j++) {
                    fitted[i] += X[i][j] * beta[j];
                }

                residuals[i] = y[i] - fitted[i];
                sse += residuals[i] * residuals[i];
            }

            mse = sse / (n - p);

            double center = Statistics.mean(y);
            double sst = 0;

            for (double value : y) {
                sst += Math.pow(value - center, 2);
            }

            if (sst <= 1e-15) {
                throw new RegressionException(
                    "Target variance is zero."
                );
            }

            rSquared = 1 - sse / sst;

            state = ModelState.FITTED;
        }

        private void requireFitted() {
            if (state == ModelState.CREATED) {
                throw new RegressionException(
                    "Fit the model before diagnostics."
                );
            }
        }

        double[] leverage() {
            requireFitted();

            double[][] hat = LinearAlgebra.multiply(
                LinearAlgebra.multiply(X, xtxInverse),
                LinearAlgebra.transpose(X)
            );

            double[] result = new double[n];

            for (int i = 0; i < n; i++) {
                result[i] = hat[i][i];
            }

            return result;
        }

        double[] studentizedResiduals() {
            requireFitted();

            if (mse <= 0) {
                throw new RegressionException(
                    "Residual variance is zero."
                );
            }

            double[] h = leverage();
            double[] result = new double[n];

            for (int i = 0; i < n; i++) {
                result[i] = residuals[i] /
                    Math.sqrt(
                        mse * Math.max(1e-15, 1 - h[i])
                    );
            }

            return result;
        }

        double[] cooksDistance() {
            double[] h = leverage();
            double[] r = studentizedResiduals();
            double[] result = new double[n];

            for (int i = 0; i < n; i++) {
                result[i] = r[i] * r[i] * h[i] /
                    (p * Math.max(1e-15, 1 - h[i]));
            }

            return result;
        }

        double[] vif() {
            requireFitted();

            double[][] columns =
                LinearAlgebra.transpose(X);

            double[] result = new double[p - 1];

            for (int predictor = 1; predictor < p; predictor++) {
                if (p == 2) {
                    result[predictor - 1] = 1;
                    continue;
                }

                double[][] auxiliary = new double[n][p - 1];

                for (int row = 0; row < n; row++) {
                    auxiliary[row][0] = 1;

                    int index = 1;

                    for (int col = 1; col < p; col++) {
                        if (col != predictor) {
                            auxiliary[row][index++] =
                                X[row][col];
                        }
                    }
                }

                double[] target = columns[predictor];

                double[][] xt = LinearAlgebra.transpose(
                    auxiliary
                );

                double[][] inverse = LinearAlgebra.inverse(
                    LinearAlgebra.multiply(xt, auxiliary)
                );

                double[] xty = new double[p - 1];

                for (int i = 0; i < xty.length; i++) {
                    for (int j = 0; j < n; j++) {
                        xty[i] += xt[i][j] * target[j];
                    }
                }

                double[] betaAux = new double[p - 1];

                for (int i = 0; i < betaAux.length; i++) {
                    for (int j = 0; j < betaAux.length; j++) {
                        betaAux[i] += inverse[i][j] * xty[j];
                    }
                }

                double center = Statistics.mean(target);
                double sseAux = 0;
                double sstAux = 0;

                for (int i = 0; i < n; i++) {
                    double prediction = 0;

                    for (int j = 0; j < betaAux.length; j++) {
                        prediction += auxiliary[i][j] *
                            betaAux[j];
                    }

                    sseAux += Math.pow(
                        target[i] - prediction, 2
                    );

                    sstAux += Math.pow(
                        target[i] - center, 2
                    );
                }

                if (sstAux <= 1e-15) {
                    throw new RegressionException(
                        "Constant predictor."
                    );
                }

                double rSquared = 1 - sseAux / sstAux;

                result[predictor - 1] =
                    1.0 / Math.max(1e-15, 1 - rSquared);
            }

            return result;
        }

        double[] breuschPagan() {
            requireFitted();

            double[] squared = Arrays.stream(residuals)
                .map(value -> value * value)
                .toArray();

            double center = Statistics.mean(squared);
            double sst = 0;

            for (double value : squared) {
                sst += Math.pow(value - center, 2);
            }

            if (sst <= 1e-15) {
                return new double[]{0, 1};
            }

            double[][] xt = LinearAlgebra.transpose(X);

            double[][] inverse = LinearAlgebra.inverse(
                LinearAlgebra.multiply(xt, X)
            );

            double[] xty = new double[p];

            for (int i = 0; i < p; i++) {
                for (int j = 0; j < n; j++) {
                    xty[i] += xt[i][j] * squared[j];
                }
            }

            double[] coefficients = new double[p];

            for (int i = 0; i < p; i++) {
                for (int j = 0; j < p; j++) {
                    coefficients[i] +=
                        inverse[i][j] * xty[j];
                }
            }

            double sseAux = 0;

            for (int i = 0; i < n; i++) {
                double prediction = 0;

                for (int j = 0; j < p; j++) {
                    prediction += X[i][j] *
                        coefficients[j];
                }

                sseAux += Math.pow(
                    squared[i] - prediction, 2
                );
            }

            double statistic = n *
                Math.max(0, Math.min(1, 1 - sseAux / sst));

            return new double[]{
                statistic,
                Statistics.chiSquareSurvival(
                    statistic, p - 1
                )
            };
        }

        double[] jarqueBera() {
            requireFitted();

            double center = Statistics.mean(residuals);
            double variance = Arrays.stream(residuals)
                .map(value -> Math.pow(value - center, 2))
                .average().orElse(0);

            if (variance <= 1e-15) {
                return new double[]{0, 1};
            }

            double third = Arrays.stream(residuals)
                .map(value -> Math.pow(value - center, 3))
                .average().orElse(0);

            double fourth = Arrays.stream(residuals)
                .map(value -> Math.pow(value - center, 4))
                .average().orElse(0);

            double skew = third / Math.pow(variance, 1.5);
            double kurtosis = fourth / Math.pow(variance, 2);

            double statistic = n / 6.0 * (
                skew * skew +
                Math.pow(kurtosis - 3, 2) / 4
            );

            return new double[]{
                statistic,
                Statistics.chiSquareSurvival(statistic, 2)
            };
        }

        double[] hc3StandardErrors() {
            double[] h = leverage();
            double[][] weighted = new double[n][p];

            for (int i = 0; i < n; i++) {
                double adjusted = residuals[i] /
                    Math.max(1e-12, 1 - h[i]);

                double weight = adjusted * adjusted;

                for (int j = 0; j < p; j++) {
                    weighted[i][j] = X[i][j] * weight;
                }
            }

            double[][] middle = LinearAlgebra.multiply(
                LinearAlgebra.transpose(X),
                weighted
            );

            double[][] covariance = LinearAlgebra.multiply(
                LinearAlgebra.multiply(
                    xtxInverse, middle
                ),
                xtxInverse
            );

            double[] result = new double[p];

            for (int i = 0; i < p; i++) {
                result[i] = Math.sqrt(
                    Math.max(0, covariance[i][i])
                );
            }

            return result;
        }

        ModelResult result() {
            requireFitted();

            return new ModelResult(
                Arrays.stream(beta).boxed().toList(),
                Arrays.stream(fitted).boxed().toList(),
                Arrays.stream(residuals).boxed().toList(),
                rSquared,
                1 - (1 - rSquared) * (n - 1.0) / (n - p),
                Math.sqrt(mse),
                n,
                p
            );
        }

        List<Observation> observations() {
            return observations;
        }

        void completeDiagnostics() {
            requireFitted();
            state = ModelState.DIAGNOSTICS_COMPLETED;
        }

        ModelState state() {
            return state;
        }
    }

    interface DiagnosticRule {
        List<DiagnosticFinding> evaluate(
            RegressionService model,
            RegressionPolicy policy
        );
    }

    static final class MulticollinearityRule
        implements DiagnosticRule {

        @Override
        public List<DiagnosticFinding> evaluate(
            RegressionService model,
            RegressionPolicy policy
        ) {
            double[] values = model.vif();

            List<DiagnosticFinding> findings =
                new ArrayList<>();

            for (int i = 0; i < values.length; i++) {
                Severity severity =
                    values[i] >= policy.vifCritical()
                        ? Severity.FAIL
                        : values[i] >= policy.vifWarning()
                            ? Severity.WARNING
                            : Severity.PASS;

                findings.add(new DiagnosticFinding(
                    DiagnosticCategory.MULTICOLLINEARITY,
                    "X" + (i + 1),
                    values[i],
                    policy.vifWarning(),
                    severity,
                    "Variance inflation factor."
                ));
            }

            return findings;
        }
    }

    static final class HeteroscedasticityRule
        implements DiagnosticRule {

        @Override
        public List<DiagnosticFinding> evaluate(
            RegressionService model,
            RegressionPolicy policy
        ) {
            double[] result = model.breuschPagan();

            return List.of(new DiagnosticFinding(
                DiagnosticCategory.HETEROSCEDASTICITY,
                "Breusch-Pagan",
                result[1],
                policy.significanceLevel(),
                result[1] < policy.significanceLevel()
                    ? Severity.WARNING
                    : Severity.PASS,
                "Low p-value indicates evidence of nonconstant variance."
            ));
        }
    }

    static final class ResidualNormalityRule
        implements DiagnosticRule {

        @Override
        public List<DiagnosticFinding> evaluate(
            RegressionService model,
            RegressionPolicy policy
        ) {
            double[] result = model.jarqueBera();

            return List.of(new DiagnosticFinding(
                DiagnosticCategory.RESIDUAL_NORMALITY,
                "Jarque-Bera",
                result[1],
                0.05,
                result[1] < 0.05
                    ? Severity.WARNING
                    : Severity.PASS,
                "Low p-value indicates departure from normality."
            ));
        }
    }

    static final class InfluenceRule
        implements DiagnosticRule {

        @Override
        public List<DiagnosticFinding> evaluate(
            RegressionService model,
            RegressionPolicy policy
        ) {
            double[] leverage = model.leverage();
            double[] cooks = model.cooksDistance();
            double[] residuals = model.studentizedResiduals();

            List<DiagnosticFinding> findings =
                new ArrayList<>();

            double cookThreshold =
                policy.cookMultiplier() / model.observations().size();

            double leverageThreshold =
                policy.leverageMultiplier() *
                (model.result().parameterCount()) /
                model.observations().size();

            for (int i = 0; i < leverage.length; i++) {
                Observation observation =
                    model.observations().get(i);

                if (cooks[i] > cookThreshold) {
                    findings.add(new DiagnosticFinding(
                        DiagnosticCategory.INFLUENTIAL_OBSERVATION,
                        observation.id(),
                        cooks[i],
                        cookThreshold,
                        Severity.WARNING,
                        "Cook's distance screening threshold exceeded."
                    ));
                }

                if (leverage[i] > leverageThreshold) {
                    findings.add(new DiagnosticFinding(
                        DiagnosticCategory.HIGH_LEVERAGE,
                        observation.id(),
                        leverage[i],
                        leverageThreshold,
                        Severity.WARNING,
                        "Unusually high predictor-space leverage."
                    ));
                }

                if (Math.abs(residuals[i]) >
                    policy.studentizedLimit()) {
                    findings.add(new DiagnosticFinding(
                        DiagnosticCategory.LARGE_RESIDUAL,
                        observation.id(),
                        residuals[i],
                        policy.studentizedLimit(),
                        Severity.WARNING,
                        "Large internally studentized residual."
                    ));
                }
            }

            return findings;
        }
    }

    static final class DiagnosticService {

        private final List<DiagnosticRule> rules;

        DiagnosticService() {
            rules = List.of(
                new MulticollinearityRule(),
                new HeteroscedasticityRule(),
                new ResidualNormalityRule(),
                new InfluenceRule()
            );
        }

        List<DiagnosticFinding> evaluate(
            RegressionService model,
            RegressionPolicy policy
        ) {
            return rules.stream()
                .flatMap(rule -> rule.evaluate(
                    model, policy
                ).stream())
                .toList();
        }
    }

    static List<Observation> sampleData() {
        List<Observation> data = new ArrayList<>();

        for (int i = 1; i <= 80; i++) {
            double x1 = i;
            double x2 = 0.92 * i + (i % 7) * 0.8;

            double error = ((i % 9) - 4) *
                (0.4 + 0.025 * i);

            if (i == 72) error += 35;

            double y = 12 + 2.5 * x1 + 1.3 * x2 + error;

            data.add(new Observation(
                "OBS-" + i,
                List.of(x1, x2),
                y
            ));
        }

        return List.copyOf(data);
    }

    static void runTests(
        RegressionService model,
        ModelResult result
    ) {
        if (result.sampleSize() != 80) {
            throw new RegressionException(
                "Sample size test failed."
            );
        }

        if (result.coefficients().size() != 3) {
            throw new RegressionException(
                "Coefficient dimension test failed."
            );
        }

        if (result.rSquared() < 0 ||
            result.rSquared() > 1) {
            throw new RegressionException(
                "R-squared validation failed."
            );
        }

        double[] h = model.leverage();

        double trace = Arrays.stream(h).sum();

        if (Math.abs(trace - 3.0) > 1e-6) {
            throw new RegressionException(
                "Hat matrix trace test failed."
            );
        }

        double probability =
            Statistics.chiSquareSurvival(5.9914645, 2);

        if (Math.abs(probability - 0.05) > 1e-5) {
            throw new RegressionException(
                "Chi-square test failed."
            );
        }

        System.out.println(
            "All Java regression tests passed."
        );
    }

    public static void main(String[] args) {
        try {
            RegressionService model =
                new RegressionService(sampleData());

            model.fit();

            ModelResult result = model.result();

            runTests(model, result);

            DiagnosticService service =
                new DiagnosticService();

            RegressionPolicy policy =
                RegressionPolicy.standard();

            List<DiagnosticFinding> findings =
                service.evaluate(model, policy);

            model.completeDiagnostics();

            System.out.println(
                "\nENTERPRISE REGRESSION DIAGNOSTICS"
            );

            System.out.println(
                "================================="
            );

            System.out.println(
                "Observations: " + result.sampleSize()
            );

            System.out.println(
                "R-squared: " + result.rSquared()
            );

            System.out.println(
                "Adjusted R-squared: " +
                result.adjustedRSquared()
            );

            System.out.println(
                "Residual standard error: " +
                result.residualStandardError()
            );

            System.out.println(
                "Coefficients: " + result.coefficients()
            );

            System.out.println(
                "HC3 standard errors: " +
                Arrays.toString(model.hc3StandardErrors())
            );

            System.out.println("\nFindings:");

            findings.stream()
                .filter(f -> f.severity() != Severity.PASS)
                .forEach(f -> System.out.printf(
                    "[%s] %s | %s | statistic=%.5f | threshold=%.5f%n",
                    f.severity(),
                    f.category(),
                    f.subject(),
                    f.statistic(),
                    f.threshold()
                ));

            Map<Severity, Long> counts =
                findings.stream().collect(
                    Collectors.groupingBy(
                        DiagnosticFinding::severity,
                        Collectors.counting()
                    )
                );

            System.out.println("\nFinding counts: " + counts);

            System.out.println(
                "Final model state: " + model.state()
            );

        } catch (RegressionException |
                 IllegalArgumentException error) {

            System.err.println(
                "Execution failed: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
