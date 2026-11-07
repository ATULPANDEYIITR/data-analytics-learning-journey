import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Enterprise Hypothesis Testing and Experiment Governance.
 *
 * Java 17, standard library only.
 *
 * Implements:
 * - Independent two-sample Welch t-test
 * - Null and alternative hypotheses
 * - P-value calculation
 * - Significance-level policies
 * - Type I and Type II error modeling
 * - Statistical power
 * - Multiple-testing correction
 * - Experiment lifecycle management
 * - Immutable statistical results
 * - Audit-oriented reporting
 */
public class HypothesisTesting {

    enum Alternative {
        TWO_SIDED,
        GREATER,
        LESS
    }

    enum ExperimentState {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum Decision {
        REJECT_H0,
        FAIL_TO_REJECT_H0
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class ExperimentException extends RuntimeException {
        ExperimentException(String message) {
            super(message);
        }
    }

    record Hypothesis(
        String name,
        double nullDifference,
        Alternative alternative,
        double alpha
    ) {
        Hypothesis {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Hypothesis name is required."
                );
            }

            Objects.requireNonNull(alternative);

            if (!Double.isFinite(nullDifference)) {
                throw new ValidationException(
                    "Null difference must be finite."
                );
            }

            validateAlpha(alpha);
        }
    }

    record SampleSummary(
        long count,
        double mean,
        double variance
    ) {
        SampleSummary {
            if (count < 2) {
                throw new ValidationException(
                    "Each sample requires at least two observations."
                );
            }

            if (
                !Double.isFinite(mean) ||
                !Double.isFinite(variance) ||
                variance < 0
            ) {
                throw new ValidationException(
                    "Invalid sample statistics."
                );
            }
        }

        static SampleSummary from(List<Double> values) {
            validateSample(values);

            double mean = values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();

            double squaredDifferences = values.stream()
                .mapToDouble(value -> {
                    double difference = value - mean;
                    return difference * difference;
                })
                .sum();

            double variance = squaredDifferences /
                (values.size() - 1);

            return new SampleSummary(
                values.size(),
                mean,
                variance
            );
        }
    }

    record TestResult(
        UUID experimentId,
        String testName,
        long totalObservations,
        double statistic,
        double degreesOfFreedom,
        double pValue,
        double alpha,
        double effectEstimate,
        double standardError,
        double confidenceLower,
        double confidenceUpper,
        Decision decision
    ) {}

    record ErrorMetrics(
        double alpha,
        double beta,
        double power
    ) {}

    interface StatisticalTest {
        TestResult execute(
            UUID experimentId,
            Hypothesis hypothesis,
            SampleSummary control,
            SampleSummary treatment
        );
    }

    static void validateAlpha(double alpha) {
        if (
            !Double.isFinite(alpha) ||
            alpha <= 0 ||
            alpha >= 1
        ) {
            throw new ValidationException(
                "Alpha must be between 0 and 1."
            );
        }
    }

    static void validateSample(List<Double> sample) {
        if (sample == null || sample.size() < 2) {
            throw new ValidationException(
                "At least two observations are required."
            );
        }

        for (Double value : sample) {
            if (value == null || !Double.isFinite(value)) {
                throw new ValidationException(
                    "Sample contains an invalid observation."
                );
            }
        }
    }

    static double normalCDF(double x) {
        // Abramowitz-Stegun approximation.
        double z = Math.abs(x);
        double t = 1.0 / (1.0 + 0.2316419 * z);

        double density =
            Math.exp(-0.5 * z * z) /
            Math.sqrt(2.0 * Math.PI);

        double polynomial = t * (
            0.319381530 +
            t * (
                -0.356563782 +
                t * (
                    1.781477937 +
                    t * (
                        -1.821255978 +
                        t * 1.330274429
                    )
                )
            )
        );

        double upper = density * polynomial;

        return x >= 0 ? 1 - upper : upper;
    }

    static double normalQuantile(double p) {
        if (!(p > 0 && p < 1)) {
            throw new ValidationException(
                "Probability must be between 0 and 1."
            );
        }

        double low = -10;
        double high = 10;

        for (int i = 0; i < 120; i++) {
            double mid = (low + high) / 2;

            if (normalCDF(mid) < p) {
                low = mid;
            } else {
                high = mid;
            }
        }

        return (low + high) / 2;
    }

    static double logGamma(double z) {
        double[] coefficients = {
            676.5203681218851,
            -1259.1392167224028,
            771.32342877765313,
            -176.61502916214059,
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

        double x = 0.99999999999980993;

        for (int i = 0; i < coefficients.length; i++) {
            x += coefficients[i] / (z + i + 1);
        }

        double t = z + coefficients.length - 0.5;

        return 0.5 * Math.log(2 * Math.PI)
            + (z + 0.5) * Math.log(t)
            - t
            + Math.log(x);
    }

    static double betaFraction(double a, double b, double x) {
        double qab = a + b;
        double qap = a + 1;
        double qam = a - 1;

        double c = 1;
        double d = 1 - qab * x / qap;
        double tiny = 1e-300;

        if (Math.abs(d) < tiny) {
            d = tiny;
        }

        d = 1 / d;
        double h = d;

        for (int m = 1; m <= 300; m++) {
            int m2 = 2 * m;

            double aa =
                m * (b - m) * x /
                ((qam + m2) * (a + m2));

            d = 1 + aa * d;
            if (Math.abs(d) < tiny) d = tiny;

            c = 1 + aa / c;
            if (Math.abs(c) < tiny) c = tiny;

            d = 1 / d;
            h *= d * c;

            aa = -(a + m) * (qab + m) * x /
                ((a + m2) * (qap + m2));

            d = 1 + aa * d;
            if (Math.abs(d) < tiny) d = tiny;

            c = 1 + aa / c;
            if (Math.abs(c) < tiny) c = tiny;

            d = 1 / d;

            double delta = d * c;
            h *= delta;

            if (Math.abs(delta - 1) < 3e-14) {
                return h;
            }
        }

        throw new ArithmeticException(
            "Beta continued fraction failed to converge."
        );
    }

    static double regularizedBeta(
        double x,
        double a,
        double b
    ) {
        if (a <= 0 || b <= 0) {
            throw new ValidationException(
                "Beta parameters must be positive."
            );
        }

        if (x <= 0) return 0;
        if (x >= 1) return 1;

        double factor = Math.exp(
            logGamma(a + b)
                - logGamma(a)
                - logGamma(b)
                + a * Math.log(x)
                + b * Math.log1p(-x)
        );

        if (x < (a + 1) / (a + b + 2)) {
            return factor * betaFraction(a, b, x) / a;
        }

        return 1 - (
            factor * betaFraction(b, a, 1 - x) / b
        );
    }

    static double studentTCdf(double t, double df) {
        double x = df / (df + t * t);

        double beta = regularizedBeta(
            x,
            df / 2,
            0.5
        );

        return t >= 0
            ? 1 - beta / 2
            : beta / 2;
    }

    static double calculateTPValue(
        double t,
        double df,
        Alternative alternative
    ) {
        double cdf = studentTCdf(t, df);

        return switch (alternative) {
            case TWO_SIDED ->
                Math.min(1, 2 * Math.min(cdf, 1 - cdf));
            case GREATER -> 1 - cdf;
            case LESS -> cdf;
        };
    }

    static double welchCriticalValue(
        double alpha,
        double degreesOfFreedom
    ) {
        double probability = 1 - alpha / 2;
        double low = -15;
        double high = 15;

        for (int i = 0; i < 140; i++) {
            double mid = (low + high) / 2;

            if (studentTCdf(mid, degreesOfFreedom) < probability) {
                low = mid;
            } else {
                high = mid;
            }
        }

        return (low + high) / 2;
    }

    static class WelchTTest implements StatisticalTest {

        @Override
        public TestResult execute(
            UUID experimentId,
            Hypothesis hypothesis,
            SampleSummary control,
            SampleSummary treatment
        ) {
            double varianceControl =
                control.variance() / control.count();

            double varianceTreatment =
                treatment.variance() / treatment.count();

            double standardError = Math.sqrt(
                varianceControl + varianceTreatment
            );

            double difference =
                treatment.mean() - control.mean();

            double adjustedDifference =
                difference - hypothesis.nullDifference();

            double dfNumerator = Math.pow(
                varianceControl + varianceTreatment,
                2
            );

            double dfDenominator =
                Math.pow(varianceControl, 2) /
                    (control.count() - 1)
                +
                Math.pow(varianceTreatment, 2) /
                    (treatment.count() - 1);

            if (dfDenominator == 0) {
                throw new ValidationException(
                    "Cannot estimate Welch degrees of freedom."
                );
            }

            double df = dfNumerator / dfDenominator;

            double statistic = standardError == 0
                ? (
                    adjustedDifference == 0
                        ? 0
                        : Math.copySign(
                            Double.POSITIVE_INFINITY,
                            adjustedDifference
                        )
                )
                : adjustedDifference / standardError;

            double pValue = Double.isFinite(statistic)
                ? calculateTPValue(
                    statistic,
                    df,
                    hypothesis.alternative()
                )
                : (
                    (hypothesis.alternative() == Alternative.TWO_SIDED
                        || (hypothesis.alternative() == Alternative.GREATER
                            && statistic > 0)
                        || (hypothesis.alternative() == Alternative.LESS
                            && statistic < 0))
                        ? 0 : 1
                );

            double critical = welchCriticalValue(
                hypothesis.alpha(),
                df
            );

            double lower = difference - critical * standardError;
            double upper = difference + critical * standardError;

            Decision decision = pValue < hypothesis.alpha()
                ? Decision.REJECT_H0
                : Decision.FAIL_TO_REJECT_H0;

            return new TestResult(
                experimentId,
                "Welch independent two-sample t-test",
                control.count() + treatment.count(),
                statistic,
                df,
                pValue,
                hypothesis.alpha(),
                difference,
                standardError,
                lower,
                upper,
                decision
            );
        }
    }

    static class Experiment {
        private final UUID id;
        private final Hypothesis hypothesis;
        private final List<Double> control;
        private final List<Double> treatment;
        private ExperimentState state;

        Experiment(
            Hypothesis hypothesis,
            List<Double> control,
            List<Double> treatment
        ) {
            this.id = UUID.randomUUID();
            this.hypothesis = Objects.requireNonNull(hypothesis);
            this.control = List.copyOf(control);
            this.treatment = List.copyOf(treatment);
            this.state = ExperimentState.CREATED;

            validateSample(this.control);
            validateSample(this.treatment);
        }

        synchronized TestResult execute(StatisticalTest test) {
            if (state != ExperimentState.CREATED) {
                throw new ExperimentException(
                    "Experiment cannot be executed in state " + state
                );
            }

            state = ExperimentState.RUNNING;

            try {
                TestResult result = test.execute(
                    id,
                    hypothesis,
                    SampleSummary.from(control),
                    SampleSummary.from(treatment)
                );

                state = ExperimentState.COMPLETED;
                return result;

            } catch (RuntimeException exception) {
                state = ExperimentState.FAILED;
                throw exception;
            }
        }

        ExperimentState getState() {
            return state;
        }

        UUID getId() {
            return id;
        }
    }

    static class PowerAnalysis {
        static ErrorMetrics estimate(
            double nullMean,
            double trueMean,
            double populationStd,
            int sampleSize,
            double alpha
        ) {
            validateAlpha(alpha);

            if (
                !Double.isFinite(populationStd) ||
                populationStd <= 0 ||
                sampleSize < 2
            ) {
                throw new ValidationException(
                    "Invalid power analysis parameters."
                );
            }

            double standardError =
                populationStd / Math.sqrt(sampleSize);

            double critical = normalQuantile(1 - alpha / 2);

            double lower = nullMean - critical * standardError;
            double upper = nullMean + critical * standardError;

            double beta =
                normalCDF((upper - trueMean) / standardError)
                -
                normalCDF((lower - trueMean) / standardError);

            return new ErrorMetrics(
                alpha,
                beta,
                1 - beta
            );
        }
    }

    static class MultipleTesting {
        static Map<Integer, Boolean> benjaminiHochberg(
            List<Double> pValues,
            double alpha
        ) {
            validateAlpha(alpha);

            if (pValues == null) {
                throw new ValidationException(
                    "P-value collection is required."
                );
            }

            for (double p : pValues) {
                if (!Double.isFinite(p) || p < 0 || p > 1) {
                    throw new ValidationException(
                        "Invalid p-value."
                    );
                }
            }

            List<Integer> indexes = new ArrayList<>();

            for (int i = 0; i < pValues.size(); i++) {
                indexes.add(i);
            }

            indexes.sort(
                Comparator.comparingDouble(pValues::get)
            );

            int largestRank = 0;
            int count = pValues.size();

            for (int i = 0; i < count; i++) {
                double threshold =
                    alpha * (i + 1) / count;

                if (pValues.get(indexes.get(i)) <= threshold) {
                    largestRank = i + 1;
                }
            }

            Map<Integer, Boolean> decisions =
                new ConcurrentHashMap<>();

            for (int i = 0; i < count; i++) {
                decisions.put(i, false);
            }

            for (int i = 0; i < largestRank; i++) {
                decisions.put(indexes.get(i), true);
            }

            return Map.copyOf(decisions);
        }
    }

    static class ReportService {
        static void print(TestResult result) {
            System.out.println("\n" + result.testName());

            System.out.println(
                "Experiment ID: " + result.experimentId()
            );

            System.out.printf(
                "Observations: %d%n",
                result.totalObservations()
            );

            System.out.printf(
                "Statistic: %.6f%n",
                result.statistic()
            );

            System.out.printf(
                "Degrees of freedom: %.4f%n",
                result.degreesOfFreedom()
            );

            System.out.printf(
                "P-value: %.8f%n",
                result.pValue()
            );

            System.out.printf(
                "Significance level: %.4f%n",
                result.alpha()
            );

            System.out.printf(
                "Effect estimate: %.6f%n",
                result.effectEstimate()
            );

            System.out.printf(
                "Confidence interval: [%.6f, %.6f]%n",
                result.confidenceLower(),
                result.confidenceUpper()
            );

            System.out.println(
                "Decision: " + result.decision()
            );
        }

        static void save(
            TestResult result,
            String filename
        ) throws IOException {
            if (!filename.matches("[a-zA-Z0-9_.-]+\\.json")) {
                throw new ValidationException(
                    "Invalid report filename."
                );
            }

            String content = """
                {
                  "experimentId": "%s",
                  "testName": "%s",
                  "observations": %d,
                  "statistic": %.12f,
                  "degreesOfFreedom": %.12f,
                  "pValue": %.12f,
                  "alpha": %.12f,
                  "effectEstimate": %.12f,
                  "confidenceLower": %.12f,
                  "confidenceUpper": %.12f,
                  "decision": "%s"
                }
                """.formatted(
                    result.experimentId(),
                    result.testName(),
                    result.totalObservations(),
                    result.statistic(),
                    result.degreesOfFreedom(),
                    result.pValue(),
                    result.alpha(),
                    result.effectEstimate(),
                    result.confidenceLower(),
                    result.confidenceUpper(),
                    result.decision()
                );

            Files.writeString(
                Path.of(filename),
                content,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW,
                StandardOpenOption.WRITE
            );
        }
    }

    public static void main(String[] args) {
        try {
            Hypothesis hypothesis = new Hypothesis(
                "Website conversion experiment",
                0.0,
                Alternative.TWO_SIDED,
                0.05
            );

            List<Double> control = List.of(
                48.2, 49.1, 50.0, 48.8, 51.2,
                49.5, 50.1, 48.9, 49.8, 50.4,
                49.2, 50.5
            );

            List<Double> treatment = List.of(
                52.1, 53.0, 51.8, 54.2, 52.9,
                53.5, 51.7, 54.0, 52.5, 53.2,
                52.8, 54.1
            );

            Experiment experiment = new Experiment(
                hypothesis,
                control,
                treatment
            );

            TestResult result = experiment.execute(
                new WelchTTest()
            );

            System.out.println("ENTERPRISE HYPOTHESIS TESTING");
            System.out.println("=============================");

            System.out.println(
                "Experiment state: " + experiment.getState()
            );

            ReportService.print(result);

            ErrorMetrics errors = PowerAnalysis.estimate(
                50,
                52,
                3,
                30,
                0.05
            );

            System.out.println("\nERROR AND POWER ANALYSIS");

            System.out.printf(
                "Type I error limit: %.6f%n",
                errors.alpha()
            );

            System.out.printf(
                "Type II error probability: %.6f%n",
                errors.beta()
            );

            System.out.printf(
                "Statistical power: %.6f%n",
                errors.power()
            );

            List<Double> pValues = List.of(
                0.001, 0.015, 0.04, 0.12, 0.30
            );

            System.out.println("\nMULTIPLE TESTING");

            System.out.println(
                MultipleTesting.benjaminiHochberg(
                    pValues,
                    0.05
                )
            );

            ReportService.save(
                result,
                "hypothesis_test_report.json"
            );

            System.out.println("\nReport saved successfully.");

        } catch (Exception exception) {
            System.err.println(
                exception.getClass().getSimpleName()
                    + ": " + exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
