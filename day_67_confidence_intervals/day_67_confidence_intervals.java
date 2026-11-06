import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.TreeMap;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.stream.IntStream;

public class ConfidenceIntervalAnalysis {

    enum Method {
        NORMAL,
        STUDENT_T,
        WILSON,
        BOOTSTRAP
    }

    record ConfidenceInterval(
        double estimate,
        double lower,
        double upper,
        double confidence,
        double marginOfError,
        Method method,
        int sampleSize
    ) {
        ConfidenceInterval {
            if (!Double.isFinite(estimate) ||
                !Double.isFinite(lower) ||
                !Double.isFinite(upper) ||
                lower > upper ||
                confidence <= 0 ||
                confidence >= 1 ||
                sampleSize <= 0) {
                throw new IllegalArgumentException(
                    "Invalid confidence interval."
                );
            }
        }

        boolean contains(double value) {
            return value >= lower && value <= upper;
        }

        double width() {
            return upper - lower;
        }
    }

    record Campaign(
        String campaignId,
        int successes,
        int trials
    ) {
        Campaign {
            Objects.requireNonNull(campaignId);

            if (campaignId.isBlank()) {
                throw new IllegalArgumentException(
                    "Campaign identifier cannot be blank."
                );
            }

            if (trials <= 0 || successes < 0 || successes > trials) {
                throw new IllegalArgumentException(
                    "Invalid campaign observations."
                );
            }
        }
    }

    static final class AnalysisException extends RuntimeException {
        AnalysisException(String message) {
            super(message);
        }
    }

    private static final double[] T95 = {
        12.706, 4.303, 3.182, 2.776, 2.571,
        2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131,
        2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060,
        2.056, 2.052, 2.048, 2.045, 2.042
    };

    private static void validateSample(List<Double> data, int minimum) {
        Objects.requireNonNull(data, "Sample cannot be null.");

        if (data.size() < minimum) {
            throw new IllegalArgumentException(
                "Insufficient observations."
            );
        }

        for (Double value : data) {
            if (value == null || !Double.isFinite(value)) {
                throw new IllegalArgumentException(
                    "Sample contains invalid observations."
                );
            }
        }
    }

    private static void validateConfidence(double confidence) {
        if (!Double.isFinite(confidence) ||
            confidence <= 0 ||
            confidence >= 1) {
            throw new IllegalArgumentException(
                "Confidence must be between zero and one."
            );
        }
    }

    static double mean(List<Double> values) {
        validateSample(values, 1);

        // Compensated summation reduces floating-point accumulation error.
        double sum = 0;
        double compensation = 0;

        for (double value : values) {
            double adjusted = value - compensation;
            double next = sum + adjusted;
            compensation = (next - sum) - adjusted;
            sum = next;
        }

        return sum / values.size();
    }

    static double sampleVariance(List<Double> values) {
        validateSample(values, 2);

        double average = mean(values);

        return values.stream()
            .mapToDouble(value -> Math.pow(value - average, 2))
            .sum() / (values.size() - 1);
    }

    static double standardDeviation(List<Double> values) {
        return Math.sqrt(sampleVariance(values));
    }

    static double normalInverse(double p) {
        if (!Double.isFinite(p) || p <= 0 || p >= 1) {
            throw new IllegalArgumentException(
                "Probability must be between zero and one."
            );
        }

        double[] a = {
            -39.69683028665376,
            220.9460984245205,
            -275.9285104469687,
            138.3577518672690,
            -30.66479806614716,
            2.506628277459239
        };

        double[] b = {
            -54.47609879822406,
            161.5858368580409,
            -155.6989798598866,
            66.80131188771972,
            -13.28068155288572
        };

        double[] c = {
            -0.007784894002430293,
            -0.3223964580411365,
            -2.400758277161838,
            -2.549732539343734,
            4.374664141464968,
            2.938163982698783
        };

        double[] d = {
            0.007784695709041462,
            0.3224671290700398,
            2.445134137142996,
            3.754408661907416
        };

        double low = 0.02425;
        double high = 1 - low;

        if (p < low) {
            double q = Math.sqrt(-2 * Math.log(p));

            return -(
                (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
                    + c[4]) * q + c[5]) /
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
            );
        }

        if (p > high) {
            double q = Math.sqrt(-2 * Math.log(1 - p));

            return (
                (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
                    + c[4]) * q + c[5]) /
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
            );
        }

        double q = p - 0.5;
        double r = q * q;

        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r
                + a[4]) * r + a[5]) * q /
            (((((b[0] * r + b[1]) * r + b[2]) * r
                + b[3]) * r + b[4]) * r + 1)
        );
    }

    static double normalCritical(double confidence) {
        validateConfidence(confidence);
        return normalInverse(0.5 + confidence / 2);
    }

    static double tCritical95(int df) {
        if (df < 1) {
            throw new IllegalArgumentException(
                "Degrees of freedom must be positive."
            );
        }

        return df <= T95.length
            ? T95[df - 1]
            : normalCritical(0.95);
    }

    static double quantile(List<Double> sorted, double p) {
        if (sorted.isEmpty() || p < 0 || p > 1) {
            throw new IllegalArgumentException("Invalid quantile input.");
        }

        double position = p * (sorted.size() - 1);
        int lower = (int) Math.floor(position);
        int upper = (int) Math.ceil(position);
        double weight = position - lower;

        return sorted.get(lower) * (1 - weight)
            + sorted.get(upper) * weight;
    }

    static ConfidenceInterval normalMean(
        List<Double> values,
        double confidence,
        Double populationSD
    ) {
        validateSample(values, 2);
        validateConfidence(confidence);

        double sd = populationSD == null
            ? standardDeviation(values)
            : populationSD;

        if (!Double.isFinite(sd) || sd < 0) {
            throw new IllegalArgumentException(
                "Invalid population standard deviation."
            );
        }

        double estimate = mean(values);
        double standardError = sd / Math.sqrt(values.size());
        double margin = normalCritical(confidence) * standardError;

        return new ConfidenceInterval(
            estimate,
            estimate - margin,
            estimate + margin,
            confidence,
            margin,
            Method.NORMAL,
            values.size()
        );
    }

    static ConfidenceInterval studentT(
        List<Double> values,
        double confidence
    ) {
        validateSample(values, 2);
        validateConfidence(confidence);

        if (confidence != 0.95) {
            throw new IllegalArgumentException(
                "Student t table supports 95% confidence only."
            );
        }

        double estimate = mean(values);
        double standardError =
            standardDeviation(values) / Math.sqrt(values.size());

        double margin =
            tCritical95(values.size() - 1) * standardError;

        return new ConfidenceInterval(
            estimate,
            estimate - margin,
            estimate + margin,
            confidence,
            margin,
            Method.STUDENT_T,
            values.size()
        );
    }

    static ConfidenceInterval wilson(
        int successes,
        int trials,
        double confidence
    ) {
        validateConfidence(confidence);

        if (trials <= 0 || successes < 0 || successes > trials) {
            throw new IllegalArgumentException(
                "Invalid binomial counts."
            );
        }

        double p = (double) successes / trials;
        double z = normalCritical(confidence);
        double z2 = z * z;
        double denominator = 1 + z2 / trials;

        double center =
            (p + z2 / (2 * trials)) / denominator;

        double adjustment = z * Math.sqrt(
            p * (1 - p) / trials
            + z2 / (4.0 * trials * trials)
        ) / denominator;

        double lower = Math.max(0, center - adjustment);
        double upper = Math.min(1, center + adjustment);

        return new ConfidenceInterval(
            p,
            lower,
            upper,
            confidence,
            (upper - lower) / 2,
            Method.WILSON,
            trials
        );
    }

    static ConfidenceInterval bootstrap(
        List<Double> values,
        double confidence,
        int repetitions,
        long seed
    ) {
        validateSample(values, 2);
        validateConfidence(confidence);

        if (repetitions < 100) {
            throw new IllegalArgumentException(
                "At least 100 repetitions required."
            );
        }

        Random random = new Random(seed);
        int n = values.size();

        List<Double> estimates = new ArrayList<>(repetitions);
        List<Double> sample = new ArrayList<>(n);

        for (int iteration = 0; iteration < repetitions; iteration++) {
            sample.clear();

            for (int i = 0; i < n; i++) {
                sample.add(values.get(random.nextInt(n)));
            }

            estimates.add(mean(sample));
        }

        Collections.sort(estimates);

        double alpha = (1 - confidence) / 2;
        double estimate = mean(values);
        double lower = quantile(estimates, alpha);
        double upper = quantile(estimates, 1 - alpha);

        return new ConfidenceInterval(
            estimate,
            lower,
            upper,
            confidence,
            (upper - lower) / 2,
            Method.BOOTSTRAP,
            n
        );
    }

    static double marginOfError(
        double sd,
        int sampleSize,
        double confidence
    ) {
        validateConfidence(confidence);

        if (!Double.isFinite(sd) || sd < 0 || sampleSize <= 0) {
            throw new IllegalArgumentException(
                "Invalid margin-of-error inputs."
            );
        }

        return normalCritical(confidence)
            * sd / Math.sqrt(sampleSize);
    }

    static int requiredSampleSize(
        double sd,
        double desiredMargin,
        double confidence
    ) {
        validateConfidence(confidence);

        if (!Double.isFinite(sd) || sd < 0 ||
            !Double.isFinite(desiredMargin) ||
            desiredMargin <= 0) {
            throw new IllegalArgumentException(
                "Invalid sample-size inputs."
            );
        }

        double result = Math.pow(
            normalCritical(confidence) * sd / desiredMargin,
            2
        );

        if (result > Integer.MAX_VALUE) {
            throw new ArithmeticException("Sample size exceeds integer capacity.");
        }

        return (int) Math.ceil(result);
    }

    // Campaign-level calculations are independent and can run concurrently.
    static CompletableFuture<Map<String, ConfidenceInterval>>
    analyzeCampaigns(List<Campaign> campaigns) {
        List<CompletableFuture<Map.Entry<String, ConfidenceInterval>>> tasks =
            campaigns.stream()
                .map(campaign -> CompletableFuture.supplyAsync(() ->
                    Map.entry(
                        campaign.campaignId(),
                        wilson(
                            campaign.successes(),
                            campaign.trials(),
                            0.95
                        )
                    )
                ))
                .toList();

        CompletableFuture<Void> all = CompletableFuture.allOf(
            tasks.toArray(new CompletableFuture[0])
        );

        return all.thenApply(ignored -> {
            Map<String, ConfidenceInterval> results = new TreeMap<>();

            for (CompletableFuture<Map.Entry<String, ConfidenceInterval>> task
                : tasks) {
                Map.Entry<String, ConfidenceInterval> entry = task.join();

                if (results.put(entry.getKey(), entry.getValue()) != null) {
                    throw new AnalysisException(
                        "Duplicate campaign identifier."
                    );
                }
            }

            return Map.copyOf(results);
        });
    }

    static void printInterval(ConfidenceInterval interval) {
        System.out.printf(
            "%-12s estimate=%8.4f CI=[%8.4f, %8.4f] MOE=%7.4f n=%d%n",
            interval.method(),
            interval.estimate(),
            interval.lower(),
            interval.upper(),
            interval.marginOfError(),
            interval.sampleSize()
        );
    }

    static void runTests() {
        List<Double> data =
            List.of(12.0, 14.0, 15.0, 13.0, 16.0,
                    18.0, 14.0, 15.0, 17.0, 16.0);

        ConfidenceInterval interval = studentT(data, 0.95);

        if (!(interval.lower() < interval.estimate() &&
              interval.estimate() < interval.upper())) {
            throw new AssertionError("Student t test failed.");
        }

        ConfidenceInterval proportion = wilson(72, 100, 0.95);

        if (proportion.lower() < 0 ||
            proportion.upper() > 1 ||
            !proportion.contains(proportion.estimate())) {
            throw new AssertionError("Wilson test failed.");
        }

        ConfidenceInterval bootstrap =
            bootstrap(data, 0.95, 1000, 42);

        if (!bootstrap.contains(bootstrap.estimate())) {
            throw new AssertionError("Bootstrap test failed.");
        }

        if (requiredSampleSize(10, 2, 0.95) != 97) {
            throw new AssertionError("Sample size test failed.");
        }

        try {
            wilson(110, 100, 0.95);
            throw new AssertionError("Invalid count was accepted.");
        } catch (IllegalArgumentException expected) {
            // Expected validation behavior.
        }

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {
        try {
            List<Double> responseTimes = List.of(
                12.4, 13.1, 11.8, 14.2, 12.9,
                13.7, 12.1, 14.0, 13.3, 12.7,
                11.9, 13.5, 14.1, 12.6, 13.0
            );

            System.out.println("CONFIDENCE INTERVAL ANALYSIS");
            System.out.println("=".repeat(60));

            System.out.println("\nPoint estimate");
            System.out.printf("Mean: %.4f%n", mean(responseTimes));
            System.out.printf(
                "Standard deviation: %.4f%n",
                standardDeviation(responseTimes)
            );

            System.out.println("\nMean confidence intervals");

            printInterval(
                normalMean(responseTimes, 0.95, null)
            );

            printInterval(
                studentT(responseTimes, 0.95)
            );

            System.out.println("\nConversion proportion");

            printInterval(wilson(735, 1000, 0.95));

            System.out.println("\nBootstrap interval");

            printInterval(
                bootstrap(responseTimes, 0.95, 5000, 42)
            );

            System.out.println("\nSample-size planning");

            System.out.println(
                "Margin of error: " + marginOfError(10, 100, 0.95)
            );

            System.out.println(
                "Required sample size: " +
                requiredSampleSize(10, 2, 0.95)
            );

            System.out.println("\nEnterprise campaign analysis");

            List<Campaign> campaigns = List.of(
                new Campaign("C001", 735, 1000),
                new Campaign("C002", 420, 600),
                new Campaign("C003", 92, 120)
            );

            Map<String, ConfidenceInterval> reports =
                analyzeCampaigns(campaigns).join();

            reports.forEach((id, result) -> {
                System.out.println(id);
                printInterval(result);
            });

            System.out.println(
                "\nInterpretation: A 95% confidence procedure captures " +
                "the fixed parameter in approximately 95% of repeated " +
                "samples under its assumptions."
            );

            runTests();

        } catch (CompletionException error) {
            System.err.println(
                "Concurrent analysis failed: " + error.getCause().getMessage()
            );
            System.exit(1);
        } catch (Exception error) {
            System.err.println("Analysis failed: " + error.getMessage());
            System.exit(1);
        }
    }
}
