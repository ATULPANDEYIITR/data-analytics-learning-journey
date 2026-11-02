import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;

public class DispersionAnalysis {

    enum VariabilityLevel {
        LOW,
        MODERATE,
        HIGH,
        UNDEFINED
    }

    record DispersionReport(
            int count,
            double minimum,
            double maximum,
            double range,
            double mean,
            double populationVariance,
            double sampleVariance,
            double populationStandardDeviation,
            double sampleStandardDeviation,
            double q1,
            double q3,
            double iqr,
            double mad,
            double coefficientOfVariationPercent) {
    }

    static class DispersionException extends RuntimeException {
        DispersionException(String message) {
            super(message);
        }
    }

    interface DispersionPolicy {
        VariabilityLevel classify(double coefficientOfVariation);
    }

    static final class StandardVariabilityPolicy
            implements DispersionPolicy {

        @Override
        public VariabilityLevel classify(double cv) {
            if (!Double.isFinite(cv)) {
                return VariabilityLevel.UNDEFINED;
            }

            if (cv < 10.0) {
                return VariabilityLevel.LOW;
            }

            if (cv < 20.0) {
                return VariabilityLevel.MODERATE;
            }

            return VariabilityLevel.HIGH;
        }
    }

    static final class DispersionService {

        DispersionReport analyze(List<Double> input) {
            validate(input);

            List<Double> values = new ArrayList<>(input);
            double mean = values.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElseThrow();

            double squaredDeviationSum = values.stream()
                    .mapToDouble(value -> {
                        double deviation = value - mean;
                        return deviation * deviation;
                    })
                    .sum();

            double populationVariance =
                    squaredDeviationSum / values.size();

            double sampleVariance =
                    values.size() > 1
                            ? squaredDeviationSum / (values.size() - 1)
                            : Double.NaN;

            List<Double> ordered = values.stream()
                    .sorted()
                    .toList();

            double minimum = ordered.get(0);
            double maximum = ordered.get(ordered.size() - 1);

            double q1 = percentile(ordered, 0.25);
            double q3 = percentile(ordered, 0.75);
            double median = percentile(ordered, 0.50);

            List<Double> absoluteDeviations = values.stream()
                    .map(value -> Math.abs(value - median))
                    .sorted()
                    .toList();

            double mad = median(absoluteDeviations);

            double populationSD = Math.sqrt(populationVariance);

            double cv = mean == 0.0
                    ? Double.NaN
                    : populationSD / Math.abs(mean) * 100.0;

            return new DispersionReport(
                    values.size(),
                    minimum,
                    maximum,
                    maximum - minimum,
                    mean,
                    populationVariance,
                    sampleVariance,
                    populationSD,
                    Double.isNaN(sampleVariance)
                            ? Double.NaN
                            : Math.sqrt(sampleVariance),
                    q1,
                    q3,
                    q3 - q1,
                    mad,
                    cv
            );
        }

        private static void validate(List<Double> values) {
            if (values == null || values.isEmpty()) {
                throw new DispersionException(
                        "At least one observation is required."
                );
            }

            for (Double value : values) {
                if (value == null || !Double.isFinite(value)) {
                    throw new DispersionException(
                            "Observations must be finite numbers."
                    );
                }
            }
        }

        private static double percentile(
                List<Double> ordered,
                double probability) {

            if (ordered.size() == 1) {
                return ordered.get(0);
            }

            double position =
                    (ordered.size() - 1) * probability;

            int lower = (int) Math.floor(position);
            int upper = Math.min(
                    lower + 1,
                    ordered.size() - 1
            );

            double fraction = position - lower;

            return ordered.get(lower)
                    + fraction *
                    (ordered.get(upper) - ordered.get(lower));
        }

        private static double median(List<Double> ordered) {
            Objects.requireNonNull(ordered);

            int middle = ordered.size() / 2;

            if (ordered.size() % 2 == 0) {
                return (
                        ordered.get(middle - 1)
                                + ordered.get(middle)
                ) / 2.0;
            }

            return ordered.get(middle);
        }
    }

    static final class DispersionReportWriter {

        void write(DispersionReport report, Path target)
                throws IOException {

            List<String> lines = List.of(
                    "count=" + report.count(),
                    "minimum=" + report.minimum(),
                    "maximum=" + report.maximum(),
                    "range=" + report.range(),
                    "mean=" + report.mean(),
                    "population_variance="
                            + report.populationVariance(),
                    "sample_variance="
                            + report.sampleVariance(),
                    "population_standard_deviation="
                            + report.populationStandardDeviation(),
                    "sample_standard_deviation="
                            + report.sampleStandardDeviation(),
                    "q1=" + report.q1(),
                    "q3=" + report.q3(),
                    "iqr=" + report.iqr(),
                    "mad=" + report.mad(),
                    "coefficient_of_variation_percent="
                            + report.coefficientOfVariationPercent()
            );

            Files.write(target, lines);
        }
    }

    static void printReport(
            DispersionReport report,
            DispersionPolicy policy) {

        System.out.println("Measures of Dispersion");
        System.out.println("======================");
        System.out.printf("Count: %d%n", report.count());
        System.out.printf("Minimum: %.4f%n", report.minimum());
        System.out.printf("Maximum: %.4f%n", report.maximum());
        System.out.printf("Range: %.4f%n", report.range());
        System.out.printf("Mean: %.4f%n", report.mean());
        System.out.printf(
                "Population variance: %.4f%n",
                report.populationVariance()
        );
        System.out.printf(
                "Sample variance: %.4f%n",
                report.sampleVariance()
        );
        System.out.printf(
                "Population standard deviation: %.4f%n",
                report.populationStandardDeviation()
        );
        System.out.printf(
                "Sample standard deviation: %.4f%n",
                report.sampleStandardDeviation()
        );
        System.out.printf("Q1: %.4f%n", report.q1());
        System.out.printf("Q3: %.4f%n", report.q3());
        System.out.printf("IQR: %.4f%n", report.iqr());
        System.out.printf("MAD: %.4f%n", report.mad());
        System.out.printf(
                "Coefficient of variation: %.4f%%%n",
                report.coefficientOfVariationPercent()
        );
        System.out.println(
                "Variability level: " +
                        policy.classify(
                                report.coefficientOfVariationPercent()
                        )
        );
    }

    static void runTests() {
        DispersionService service = new DispersionService();

        DispersionReport report = service.analyze(
                List.of(12.0, 15.0, 14.0, 10.0, 18.0,
                        20.0, 13.0, 16.0, 15.0, 11.0)
        );

        if (report.count() != 10
                || report.minimum() != 10.0
                || report.maximum() != 20.0
                || report.range() != 10.0
                || Math.abs(report.mean() - 14.4) > 1e-9
                || report.populationVariance() <= 0
                || report.iqr() <= 0
                || report.mad() <= 0) {
            throw new AssertionError("Primary validation failed.");
        }

        DispersionReport single =
                service.analyze(List.of(5.0));

        if (single.range() != 0.0
                || single.populationVariance() != 0.0
                || single.iqr() != 0.0
                || single.mad() != 0.0) {
            throw new AssertionError(
                    "Single-observation validation failed."
            );
        }

        try {
            service.analyze(List.of());
            throw new AssertionError(
                    "Empty input should fail."
            );
        } catch (DispersionException expected) {
        }

        try {
            service.analyze(
                    List.of(1.0, Double.NaN)
            );
            throw new AssertionError(
                    "NaN input should fail."
            );
        } catch (DispersionException expected) {
        }
    }

    public static void main(String[] args) {
        try {
            List<Double> observations = List.of(
                    12.0, 15.0, 14.0, 10.0, 18.0,
                    20.0, 13.0, 16.0, 15.0, 11.0
            );

            DispersionService service = new DispersionService();
            DispersionPolicy policy =
                    new StandardVariabilityPolicy();

            DispersionReport report =
                    service.analyze(observations);

            printReport(report, policy);

            Path output = Path.of("dispersion_report.txt");
            new DispersionReportWriter().write(report, output);
            System.out.println(
                    "Report written to: " + output.toAbsolutePath()
            );

            runTests();
            System.out.println("Validation tests: passed");
        } catch (IOException | RuntimeException error) {
            System.err.println(
                    "Execution failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
