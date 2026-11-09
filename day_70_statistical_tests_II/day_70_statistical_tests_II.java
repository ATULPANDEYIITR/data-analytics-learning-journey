import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/*
 * Statistical Tests II
 *
 * Enterprise statistical testing service.
 *
 * Java 17
 * No external dependencies.
 *
 * Includes:
 * - Chi-square goodness-of-fit.
 * - Chi-square independence.
 * - One-sample proportion testing.
 * - Two-sample proportion testing.
 * - Immutable domain records.
 * - Validation and custom exceptions.
 * - Analysis lifecycle management.
 * - Policy-based statistical decisions.
 */

public class StatisticalTestsII {

    enum TestType {
        GOODNESS_OF_FIT,
        INDEPENDENCE,
        ONE_PROPORTION,
        TWO_PROPORTION
    }

    enum Decision {
        REJECT_NULL,
        FAIL_TO_REJECT_NULL
    }

    enum AnalysisState {
        CREATED,
        VALIDATED,
        EXECUTED,
        REPORTED,
        FAILED
    }

    static class StatisticalException extends RuntimeException {
        StatisticalException(String message) {
            super(message);
        }
    }

    record StatisticalPolicy(double alpha) {
        StatisticalPolicy {
            if (!Double.isFinite(alpha) || alpha <= 0 || alpha >= 1) {
                throw new StatisticalException(
                    "Alpha must be between zero and one."
                );
            }
        }

        boolean reject(double pValue) {
            return pValue < alpha;
        }
    }

    record TestResult(
        TestType type,
        double statistic,
        int degreesOfFreedom,
        double pValue,
        double alpha,
        Decision decision,
        int sampleSize,
        double effectSize,
        String interpretation
    ) {
        TestResult {
            Objects.requireNonNull(type);
            Objects.requireNonNull(decision);
            Objects.requireNonNull(interpretation);

            if (
                !Double.isFinite(statistic) ||
                !Double.isFinite(pValue) ||
                pValue < 0 ||
                pValue > 1
            ) {
                throw new StatisticalException(
                    "Invalid statistical result."
                );
            }
        }
    }

    interface StatisticalOperation {
        TestResult execute(StatisticalPolicy policy);
    }

    static class StatisticalMath {

        private static final double EPSILON = 1e-14;
        private static final double MINIMUM = 1e-300;

        private static double logGamma(double z) {
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

        static double regularizedGammaQ(double a, double x) {
            if (a <= 0 || x < 0) {
                throw new StatisticalException(
                    "Invalid gamma function parameters."
                );
            }

            if (x == 0) return 1;

            double logFactor =
                -x + a * Math.log(x) - logGamma(a);

            if (x < a + 1) {
                double ap = a;
                double term = 1 / a;
                double sum = term;

                for (int i = 0; i < 10000; i++) {
                    ap++;
                    term *= x / ap;
                    sum += term;

                    if (Math.abs(term) < Math.abs(sum) * EPSILON) {
                        return Math.max(
                            0,
                            Math.min(
                                1,
                                1 - sum * Math.exp(logFactor)
                            )
                        );
                    }
                }

                throw new StatisticalException(
                    "Gamma series failed to converge."
                );
            }

            double b = x + 1 - a;
            double c = 1 / MINIMUM;
            double d = 1 / b;
            double h = d;

            for (int i = 1; i <= 10000; i++) {
                double an = -i * (i - a);

                b += 2;

                d = an * d + b;
                if (Math.abs(d) < MINIMUM) d = MINIMUM;

                c = b + an / c;
                if (Math.abs(c) < MINIMUM) c = MINIMUM;

                d = 1 / d;

                double delta = d * c;
                h *= delta;

                if (Math.abs(delta - 1) < EPSILON) {
                    return Math.max(
                        0,
                        Math.min(1, Math.exp(logFactor) * h)
                    );
                }
            }

            throw new StatisticalException(
                "Gamma continued fraction failed to converge."
            );
        }

        static double chiSquarePValue(double statistic, int df) {
            if (
                !Double.isFinite(statistic) ||
                statistic < 0 ||
                df <= 0
            ) {
                throw new StatisticalException(
                    "Invalid chi-square parameters."
                );
            }

            return regularizedGammaQ(
                df / 2.0,
                statistic / 2.0
            );
        }

        static double normalPValue(double z) {
            return erfc(Math.abs(z) / Math.sqrt(2));
        }

        private static double erfc(double x) {
            double t = 1 / (1 + 0.5 * x);

            return t * Math.exp(
                -x * x - 1.26551223
                + t * (
                    1.00002368
                    + t * (
                        0.37409196
                        + t * (
                            0.09678418
                            + t * (
                                -0.18628806
                                + t * (
                                    0.27886807
                                    + t * (
                                        -1.13520398
                                        + t * (
                                            1.48851587
                                            + t * (
                                                -0.82215223
                                                + t * 0.17087277
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            );
        }
    }

    static class InputValidator {

        static void validateCounts(int[] counts) {
            if (counts == null || counts.length == 0) {
                throw new StatisticalException(
                    "Counts cannot be empty."
                );
            }

            for (int count : counts) {
                if (count < 0) {
                    throw new StatisticalException(
                        "Counts cannot be negative."
                    );
                }
            }
        }

        static void validateExpected(double[] expected) {
            if (expected == null || expected.length == 0) {
                throw new StatisticalException(
                    "Expected frequencies cannot be empty."
                );
            }

            for (double value : expected) {
                if (!Double.isFinite(value) || value <= 0) {
                    throw new StatisticalException(
                        "Expected frequencies must be positive."
                    );
                }
            }
        }
    }

    static class GoodnessOfFitService {

        TestResult execute(
            int[] observed,
            double[] expected,
            StatisticalPolicy policy
        ) {
            InputValidator.validateCounts(observed);
            InputValidator.validateExpected(expected);

            if (
                observed.length < 2 ||
                observed.length != expected.length
            ) {
                throw new StatisticalException(
                    "Observed and expected categories must match."
                );
            }

            int total = 0;
            double expectedTotal = 0;

            for (int value : observed) total += value;
            for (double value : expected) expectedTotal += value;

            if (
                total == 0 ||
                Math.abs(total - expectedTotal) > 1e-9
            ) {
                throw new StatisticalException(
                    "Expected and observed totals must match."
                );
            }

            double statistic = 0;

            for (int i = 0; i < observed.length; i++) {
                double difference = observed[i] - expected[i];

                statistic +=
                    difference * difference / expected[i];
            }

            int df = observed.length - 1;

            double p = StatisticalMath.chiSquarePValue(
                statistic,
                df
            );

            Decision decision = policy.reject(p)
                ? Decision.REJECT_NULL
                : Decision.FAIL_TO_REJECT_NULL;

            return new TestResult(
                TestType.GOODNESS_OF_FIT,
                statistic,
                df,
                p,
                policy.alpha(),
                decision,
                total,
                Math.sqrt(statistic / total),
                decision == Decision.REJECT_NULL
                    ? "Observed distribution differs significantly."
                    : "Insufficient evidence of distribution difference."
            );
        }
    }

    static class IndependenceService {

        TestResult execute(
            int[][] table,
            StatisticalPolicy policy,
            boolean yatesCorrection
        ) {
            if (
                table == null ||
                table.length < 2 ||
                table[0] == null ||
                table[0].length < 2
            ) {
                throw new StatisticalException(
                    "A contingency table requires at least 2 by 2 cells."
                );
            }

            int rows = table.length;
            int cols = table[0].length;

            double[] rowTotals = new double[rows];
            double[] columnTotals = new double[cols];

            for (int i = 0; i < rows; i++) {
                if (table[i] == null || table[i].length != cols) {
                    throw new StatisticalException(
                        "Contingency table must be rectangular."
                    );
                }

                InputValidator.validateCounts(table[i]);

                for (int j = 0; j < cols; j++) {
                    rowTotals[i] += table[i][j];
                    columnTotals[j] += table[i][j];
                }
            }

            double total = 0;

            for (double value : rowTotals) total += value;

            if (
                total == 0 ||
                java.util.Arrays.stream(rowTotals).anyMatch(x -> x == 0) ||
                java.util.Arrays.stream(columnTotals).anyMatch(x -> x == 0)
            ) {
                throw new StatisticalException(
                    "All rows and columns must contain observations."
                );
            }

            double statistic = 0;
            double minimumExpected = Double.MAX_VALUE;

            for (int i = 0; i < rows; i++) {
                for (int j = 0; j < cols; j++) {
                    double expected =
                        rowTotals[i] * columnTotals[j] / total;

                    minimumExpected = Math.min(
                        minimumExpected,
                        expected
                    );

                    double difference = Math.abs(
                        table[i][j] - expected
                    );

                    if (yatesCorrection && rows == 2 && cols == 2) {
                        difference = Math.max(
                            0,
                            difference - 0.5
                        );
                    }

                    statistic +=
                        difference * difference / expected;
                }
            }

            int df = (rows - 1) * (cols - 1);

            double p = StatisticalMath.chiSquarePValue(
                statistic,
                df
            );

            double v = Math.sqrt(
                statistic /
                (total * Math.min(rows - 1, cols - 1))
            );

            String interpretation = p < policy.alpha()
                ? "Evidence of association between variables."
                : "Insufficient evidence of association.";

            if (minimumExpected < 5) {
                interpretation +=
                    " At least one expected count is below five.";
            }

            return new TestResult(
                TestType.INDEPENDENCE,
                statistic,
                df,
                p,
                policy.alpha(),
                policy.reject(p)
                    ? Decision.REJECT_NULL
                    : Decision.FAIL_TO_REJECT_NULL,
                (int) total,
                v,
                interpretation
            );
        }
    }

    static class ProportionService {

        TestResult oneSample(
            int successes,
            int trials,
            double p0,
            StatisticalPolicy policy
        ) {
            if (
                trials <= 0 ||
                successes < 0 ||
                successes > trials ||
                !Double.isFinite(p0) ||
                p0 <= 0 ||
                p0 >= 1
            ) {
                throw new StatisticalException(
                    "Invalid one-sample proportion parameters."
                );
            }

            double observed = (double) successes / trials;

            double standardError = Math.sqrt(
                p0 * (1 - p0) / trials
            );

            double z = (observed - p0) / standardError;

            double p = StatisticalMath.normalPValue(z);

            return new TestResult(
                TestType.ONE_PROPORTION,
                z,
                0,
                p,
                policy.alpha(),
                policy.reject(p)
                    ? Decision.REJECT_NULL
                    : Decision.FAIL_TO_REJECT_NULL,
                trials,
                observed - p0,
                policy.reject(p)
                    ? "Population proportion differs from p0."
                    : "Insufficient evidence of a difference from p0."
            );
        }

        TestResult twoSample(
            int x1,
            int n1,
            int x2,
            int n2,
            StatisticalPolicy policy
        ) {
            if (
                n1 <= 0 || n2 <= 0 ||
                x1 < 0 || x1 > n1 ||
                x2 < 0 || x2 > n2
            ) {
                throw new StatisticalException(
                    "Invalid two-sample proportion parameters."
                );
            }

            double p1 = (double) x1 / n1;
            double p2 = (double) x2 / n2;

            double pooled =
                (double) (x1 + x2) / (n1 + n2);

            if (pooled == 0 || pooled == 1) {
                throw new StatisticalException(
                    "Pooled variance is zero."
                );
            }

            double se = Math.sqrt(
                pooled * (1 - pooled) *
                (1.0 / n1 + 1.0 / n2)
            );

            double z = (p1 - p2) / se;
            double p = StatisticalMath.normalPValue(z);

            return new TestResult(
                TestType.TWO_PROPORTION,
                z,
                0,
                p,
                policy.alpha(),
                policy.reject(p)
                    ? Decision.REJECT_NULL
                    : Decision.FAIL_TO_REJECT_NULL,
                n1 + n2,
                p1 - p2,
                policy.reject(p)
                    ? "The population proportions differ significantly."
                    : "Insufficient evidence of a difference."
            );
        }
    }

    static class AnalysisSession {

        private final StatisticalPolicy policy;
        private final List<TestResult> results = new ArrayList<>();
        private AnalysisState state = AnalysisState.CREATED;

        AnalysisSession(StatisticalPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void execute(StatisticalOperation operation) {
            if (
                state == AnalysisState.FAILED ||
                state == AnalysisState.REPORTED
            ) {
                throw new StatisticalException(
                    "Session cannot accept additional operations."
                );
            }

            try {
                state = AnalysisState.VALIDATED;

                TestResult result = operation.execute(policy);

                results.add(result);
                state = AnalysisState.EXECUTED;

            } catch (RuntimeException exception) {
                state = AnalysisState.FAILED;
                throw exception;
            }
        }

        List<TestResult> report() {
            if (results.isEmpty()) {
                throw new StatisticalException(
                    "No completed analyses are available."
                );
            }

            state = AnalysisState.REPORTED;

            return Collections.unmodifiableList(
                new ArrayList<>(results)
            );
        }

        AnalysisState state() {
            return state;
        }
    }

    static void runTests() {
        StatisticalPolicy policy = new StatisticalPolicy(0.05);

        double reference =
            StatisticalMath.chiSquarePValue(
                3.8414588207,
                1
            );

        if (Math.abs(reference - 0.05) > 1e-7) {
            throw new AssertionError(
                "Chi-square reference test failed."
            );
        }

        TestResult goodness = new GoodnessOfFitService().execute(
            new int[]{50, 50},
            new double[]{50, 50},
            policy
        );

        if (goodness.statistic() != 0) {
            throw new AssertionError("Goodness-of-fit failed.");
        }

        TestResult independence = new IndependenceService().execute(
            new int[][]{{10, 10}, {10, 10}},
            policy,
            false
        );

        if (independence.statistic() != 0) {
            throw new AssertionError("Independence test failed.");
        }

        TestResult one = new ProportionService().oneSample(
            50, 100, 0.5, policy
        );

        if (one.statistic() != 0) {
            throw new AssertionError("One-proportion test failed.");
        }

        TestResult two = new ProportionService().twoSample(
            50, 100, 50, 100, policy
        );

        if (two.statistic() != 0) {
            throw new AssertionError("Two-proportion test failed.");
        }

        System.out.println("All Java statistical tests passed.");
    }

    public static void main(String[] args) {
        try {
            runTests();

            StatisticalPolicy policy =
                new StatisticalPolicy(0.05);

            AnalysisSession session =
                new AnalysisSession(policy);

            GoodnessOfFitService goodness =
                new GoodnessOfFitService();

            IndependenceService independence =
                new IndependenceService();

            ProportionService proportions =
                new ProportionService();

            session.execute(p -> goodness.execute(
                new int[]{48, 52, 45, 55},
                new double[]{50, 50, 50, 50},
                p
            ));

            session.execute(p -> independence.execute(
                new int[][]{
                    {40, 20},
                    {15, 45}
                },
                p,
                false
            ));

            session.execute(p -> independence.execute(
                new int[][]{
                    {40, 20},
                    {15, 45}
                },
                p,
                true
            ));

            session.execute(p -> proportions.oneSample(
                120, 200, 0.50, p
            ));

            session.execute(p -> proportions.twoSample(
                140, 200,
                110, 200,
                p
            ));

            System.out.println("\nENTERPRISE ANALYSIS REPORT");

            for (TestResult result : session.report()) {
                System.out.printf(
                    "%-25s statistic=%10.5f p=%10.7f decision=%s%n",
                    result.type(),
                    result.statistic(),
                    result.pValue(),
                    result.decision()
                );

                System.out.println(
                    "  " + result.interpretation()
                );
            }

            System.out.println(
                "Session state: " + session.state()
            );

        } catch (StatisticalException exception) {
            System.err.println(
                "Analysis failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
