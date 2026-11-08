import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/*
 * Statistical Tests I
 *
 * Enterprise-oriented statistical testing service.
 * Java 17, standard library only.
 *
 * Supports:
 * 1. One-sample t-test.
 * 2. Independent Welch t-test.
 * 3. Independent pooled t-test.
 * 4. Paired t-test.
 */

public class StatisticalTests {

    enum TestType {
        ONE_SAMPLE,
        INDEPENDENT_WELCH,
        INDEPENDENT_POOLED,
        PAIRED
    }

    record TestResult(
        TestType testType,
        double statistic,
        double degreesOfFreedom,
        double pValue,
        double alpha,
        int sampleSize,
        double meanDifference,
        boolean significant
    ) {
        public TestResult {
            Objects.requireNonNull(testType);

            if (degreesOfFreedom <= 0 || sampleSize < 2) {
                throw new IllegalArgumentException(
                    "Invalid test result metadata."
                );
            }

            if (pValue < 0 || pValue > 1 || alpha <= 0 || alpha >= 1) {
                throw new IllegalArgumentException(
                    "Invalid probability values."
                );
            }
        }

        public String decision() {
            return significant
                ? "Reject the null hypothesis."
                : "Fail to reject the null hypothesis.";
        }
    }

    static class Sample {
        private final List<Double> values;

        Sample(List<Double> values, String name) {
            Objects.requireNonNull(values);

            if (values.size() < 2) {
                throw new IllegalArgumentException(
                    name + " requires at least two observations."
                );
            }

            List<Double> validated = new ArrayList<>();

            for (Double value : values) {
                if (value == null || !Double.isFinite(value)) {
                    throw new IllegalArgumentException(
                        name + " contains invalid observations."
                    );
                }

                validated.add(value);
            }

            this.values = List.copyOf(validated);
        }

        int size() {
            return values.size();
        }

        double mean() {
            return values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();
        }

        double variance() {
            double average = mean();

            return values.stream()
                .mapToDouble(value ->
                    Math.pow(value - average, 2)
                )
                .sum() / (size() - 1);
        }
    }

    static class StatisticalMath {

        private StatisticalMath() {}

        static void validateAlpha(double alpha) {
            if (!Double.isFinite(alpha) ||
                alpha <= 0 || alpha >= 1) {

                throw new IllegalArgumentException(
                    "Alpha must be between zero and one."
                );
            }
        }

        // Lanczos approximation.
        static double logGamma(double z) {
            double[] coefficients = {
                676.5203681218851,
                -1259.1392167224028,
                771.3234287776531,
                -176.6150291621406,
                12.507343278686905,
                -0.13857109526572012,
                9.984369578019572e-6,
                1.5056327351493116e-7
            };

            if (z < 0.5) {
                return Math.log(Math.PI)
                    - Math.log(Math.abs(Math.sin(Math.PI * z)))
                    - logGamma(1.0 - z);
            }

            z -= 1.0;

            double x = 0.99999999999980993;

            for (int i = 0; i < coefficients.length; i++) {
                x += coefficients[i] / (z + i + 1.0);
            }

            double t = z + 7.5;

            return 0.5 * Math.log(2.0 * Math.PI)
                + (z + 0.5) * Math.log(t)
                - t
                + Math.log(x);
        }

        static double betaFraction(double a, double b, double x) {
            int maximumIterations = 300;
            double epsilon = 3e-14;
            double tiny = 1e-300;

            double qab = a + b;
            double qap = a + 1.0;
            double qam = a - 1.0;

            double c = 1.0;
            double d = 1.0 - qab * x / qap;

            if (Math.abs(d) < tiny) {
                d = tiny;
            }

            d = 1.0 / d;

            double h = d;

            for (int m = 1; m <= maximumIterations; m++) {
                int m2 = 2 * m;

                double aa = m * (b - m) * x /
                    ((qam + m2) * (a + m2));

                d = 1.0 + aa * d;
                if (Math.abs(d) < tiny) d = tiny;

                c = 1.0 + aa / c;
                if (Math.abs(c) < tiny) c = tiny;

                d = 1.0 / d;
                h *= d * c;

                aa = -((a + m) * (qab + m) * x) /
                    ((a + m2) * (qap + m2));

                d = 1.0 + aa * d;
                if (Math.abs(d) < tiny) d = tiny;

                c = 1.0 + aa / c;
                if (Math.abs(c) < tiny) c = tiny;

                d = 1.0 / d;

                double delta = d * c;
                h *= delta;

                if (Math.abs(delta - 1.0) < epsilon) {
                    return h;
                }
            }

            throw new ArithmeticException(
                "Incomplete beta calculation did not converge."
            );
        }

        static double regularizedBeta(
            double x,
            double a,
            double b
        ) {
            if (a <= 0 || b <= 0) {
                throw new IllegalArgumentException(
                    "Beta parameters must be positive."
                );
            }

            if (x <= 0) return 0;
            if (x >= 1) return 1;

            double front = Math.exp(
                logGamma(a + b)
                - logGamma(a)
                - logGamma(b)
                + a * Math.log(x)
                + b * Math.log1p(-x)
            );

            if (x < (a + 1.0) / (a + b + 2.0)) {
                return front * betaFraction(a, b, x) / a;
            }

            return 1.0 -
                front * betaFraction(b, a, 1.0 - x) / b;
        }

        static double studentTPValue(double statistic, double df) {
            if (df <= 0 || !Double.isFinite(df)) {
                throw new IllegalArgumentException(
                    "Degrees of freedom must be positive."
                );
            }

            double x = df / (df + statistic * statistic);

            return regularizedBeta(x, df / 2.0, 0.5);
        }
    }

    interface TestService {
        TestResult execute(double alpha);
    }

    static class OneSampleTest implements TestService {
        private final Sample sample;
        private final double hypothesizedMean;

        OneSampleTest(
            List<Double> observations,
            double hypothesizedMean
        ) {
            sample = new Sample(observations, "One-sample data");

            if (!Double.isFinite(hypothesizedMean)) {
                throw new IllegalArgumentException(
                    "Hypothesized mean must be finite."
                );
            }

            this.hypothesizedMean = hypothesizedMean;
        }

        @Override
        public TestResult execute(double alpha) {
            StatisticalMath.validateAlpha(alpha);

            int n = sample.size();

            double difference = sample.mean() - hypothesizedMean;
            double variance = sample.variance();

            if (variance == 0 && difference == 0) {
                throw new ArithmeticException(
                    "The t-statistic is undefined."
                );
            }

            double statistic;
            double pValue;

            if (variance == 0) {
                statistic = Math.copySign(
                    Double.POSITIVE_INFINITY,
                    difference
                );
                pValue = 0;
            } else {
                statistic = difference / Math.sqrt(variance / n);

                pValue = StatisticalMath.studentTPValue(
                    statistic,
                    n - 1
                );
            }

            return new TestResult(
                TestType.ONE_SAMPLE,
                statistic,
                n - 1,
                pValue,
                alpha,
                n,
                difference,
                pValue < alpha
            );
        }
    }

    static class IndependentTest implements TestService {
        private final Sample first;
        private final Sample second;
        private final boolean equalVariance;

        IndependentTest(
            List<Double> first,
            List<Double> second,
            boolean equalVariance
        ) {
            this.first = new Sample(first, "First group");
            this.second = new Sample(second, "Second group");
            this.equalVariance = equalVariance;
        }

        @Override
        public TestResult execute(double alpha) {
            StatisticalMath.validateAlpha(alpha);

            int n1 = first.size();
            int n2 = second.size();

            double v1 = first.variance();
            double v2 = second.variance();

            double difference = first.mean() - second.mean();

            double standardError;
            double df;
            TestType type;

            if (equalVariance) {
                df = n1 + n2 - 2;

                double pooled = (
                    (n1 - 1) * v1 +
                    (n2 - 1) * v2
                ) / df;

                standardError = Math.sqrt(
                    pooled * (1.0 / n1 + 1.0 / n2)
                );

                type = TestType.INDEPENDENT_POOLED;

            } else {
                double term1 = v1 / n1;
                double term2 = v2 / n2;

                standardError = Math.sqrt(term1 + term2);

                df = Math.pow(term1 + term2, 2) / (
                    term1 * term1 / (n1 - 1) +
                    term2 * term2 / (n2 - 1)
                );

                type = TestType.INDEPENDENT_WELCH;
            }

            if (standardError == 0 && difference == 0) {
                throw new ArithmeticException(
                    "The t-statistic is undefined."
                );
            }

            double statistic = standardError == 0
                ? Math.copySign(Double.POSITIVE_INFINITY, difference)
                : difference / standardError;

            double pValue = standardError == 0
                ? 0
                : StatisticalMath.studentTPValue(statistic, df);

            return new TestResult(
                type,
                statistic,
                df,
                pValue,
                alpha,
                n1 + n2,
                difference,
                pValue < alpha
            );
        }
    }

    static class PairedTest implements TestService {
        private final Sample before;
        private final Sample after;

        PairedTest(List<Double> before, List<Double> after) {
            this.before = new Sample(before, "Before observations");
            this.after = new Sample(after, "After observations");

            if (this.before.size() != this.after.size()) {
                throw new IllegalArgumentException(
                    "Paired samples must have equal lengths."
                );
            }
        }

        @Override
        public TestResult execute(double alpha) {
            StatisticalMath.validateAlpha(alpha);

            List<Double> differences = new ArrayList<>();

            for (int i = 0; i < before.size(); i++) {
                differences.add(
                    after.values.get(i) - before.values.get(i)
                );
            }

            Sample pairedDifferences = new Sample(
                differences,
                "Paired differences"
            );

            int n = pairedDifferences.size();

            double difference = pairedDifferences.mean();
            double variance = pairedDifferences.variance();

            if (variance == 0 && difference == 0) {
                throw new ArithmeticException(
                    "All paired differences are zero."
                );
            }

            double statistic;
            double pValue;

            if (variance == 0) {
                statistic = Math.copySign(
                    Double.POSITIVE_INFINITY,
                    difference
                );
                pValue = 0;
            } else {
                statistic = difference / Math.sqrt(variance / n);

                pValue = StatisticalMath.studentTPValue(
                    statistic,
                    n - 1
                );
            }

            return new TestResult(
                TestType.PAIRED,
                statistic,
                n - 1,
                pValue,
                alpha,
                n,
                difference,
                pValue < alpha
            );
        }
    }

    static class StatisticalTestManager {
        private final double alpha;
        private final List<TestResult> results = new ArrayList<>();

        StatisticalTestManager(double alpha) {
            StatisticalMath.validateAlpha(alpha);
            this.alpha = alpha;
        }

        public TestResult run(TestService service) {
            TestResult result = service.execute(alpha);
            results.add(result);
            return result;
        }

        public List<TestResult> getResults() {
            return List.copyOf(results);
        }

        public void displayReport() {
            for (TestResult result : results) {
                System.out.println("\n" + result.testType());

                System.out.printf(
                    "Statistic: %.6f%n",
                    result.statistic()
                );

                System.out.printf(
                    "Degrees of freedom: %.4f%n",
                    result.degreesOfFreedom()
                );

                System.out.printf(
                    "p-value: %.8g%n",
                    result.pValue()
                );

                System.out.printf(
                    "Mean difference: %.6f%n",
                    result.meanDifference()
                );

                System.out.println(result.decision());
            }
        }

        public void exportCSV(Path path) throws IOException {
            if (results.isEmpty()) {
                throw new IllegalStateException(
                    "No test results available."
                );
            }

            try (BufferedWriter writer = Files.newBufferedWriter(
                path,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW,
                StandardOpenOption.WRITE
            )) {
                writer.write(
                    "test,statistic,df,p_value,alpha,sample_size,"
                    + "mean_difference,significant"
                );

                writer.newLine();

                for (TestResult result : results) {
                    writer.write(String.format(
                        java.util.Locale.ROOT,
                        "%s,%.12g,%.12g,%.12g,%.12g,%d,%.12g,%b",
                        result.testType(),
                        result.statistic(),
                        result.degreesOfFreedom(),
                        result.pValue(),
                        result.alpha(),
                        result.sampleSize(),
                        result.meanDifference(),
                        result.significant()
                    ));

                    writer.newLine();
                }
            }
        }
    }

    public static void main(String[] args) {
        try {
            StatisticalTestManager manager =
                new StatisticalTestManager(0.05);

            List<Double> deliveryTimes = List.of(
                28.0, 31.0, 29.0, 32.0, 30.0,
                27.0, 34.0, 31.0, 29.0, 30.0
            );

            manager.run(
                new OneSampleTest(deliveryTimes, 30.0)
            );

            List<Double> control = List.of(
                72.0, 75.0, 78.0, 74.0,
                71.0, 80.0, 77.0, 76.0
            );

            List<Double> treatment = List.of(
                81.0, 84.0, 79.0, 86.0,
                82.0, 83.0, 85.0, 80.0
            );

            manager.run(
                new IndependentTest(
                    control,
                    treatment,
                    false
                )
            );

            manager.run(
                new IndependentTest(
                    control,
                    treatment,
                    true
                )
            );

            List<Double> before = List.of(
                65.0, 70.0, 72.0, 68.0,
                75.0, 71.0, 69.0, 73.0
            );

            List<Double> after = List.of(
                72.0, 74.0, 76.0, 75.0,
                79.0, 76.0, 74.0, 78.0
            );

            manager.run(new PairedTest(before, after));

            manager.displayReport();

            manager.exportCSV(
                Path.of("statistical_results.csv")
            );

            if (Math.abs(
                StatisticalMath.studentTPValue(0, 10) - 1
            ) > 1e-10) {
                throw new ArithmeticException(
                    "Numerical validation failed."
                );
            }

            System.out.println("\nNumerical validation passed.");

        } catch (Exception error) {
            System.err.println(
                "Statistical execution failed: " +
                error.getMessage()
            );

            System.exit(1);
        }
    }
}
