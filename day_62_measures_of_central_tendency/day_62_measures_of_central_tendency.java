import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class CentralTendencyEnterprise {

    enum MeasureType {
        MEAN,
        MEDIAN,
        MODE,
        WEIGHTED_MEAN,
        GEOMETRIC_MEAN,
        HARMONIC_MEAN
    }

    enum ReviewState {
        OPEN,
        APPROVED,
        CHANGES_REQUESTED,
        CLOSED
    }

    record WeightedObservation(double value, double weight) {
        WeightedObservation {
            if (!Double.isFinite(value) || !Double.isFinite(weight)) {
                throw new IllegalArgumentException(
                    "Value and weight must be finite."
                );
            }
            if (weight < 0) {
                throw new IllegalArgumentException(
                    "Weight cannot be negative."
                );
            }
        }
    }

    record ReviewMetric(
        String reviewer,
        ReviewState state,
        double reviewHours
    ) {
        ReviewMetric {
            Objects.requireNonNull(reviewer, "Reviewer is required.");
            Objects.requireNonNull(state, "Review state is required.");

            if (reviewer.isBlank()) {
                throw new IllegalArgumentException(
                    "Reviewer cannot be blank."
                );
            }

            if (!Double.isFinite(reviewHours) || reviewHours <= 0) {
                throw new IllegalArgumentException(
                    "Review hours must be positive and finite."
                );
            }
        }
    }

    interface MeasureCalculator {
        double calculate(List<Double> values);
    }

    static final class MeasureException extends RuntimeException {
        MeasureException(String message) {
            super(message);
        }
    }

    static final class CentralTendencyService {
        private static void validate(List<Double> values) {
            if (values == null || values.isEmpty()) {
                throw new MeasureException(
                    "At least one observation is required."
                );
            }

            if (values.stream().anyMatch(
                value -> value == null || !Double.isFinite(value)
            )) {
                throw new MeasureException(
                    "All observations must be finite numbers."
                );
            }
        }

        static double mean(List<Double> values) {
            validate(values);

            return values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();
        }

        static double median(List<Double> values) {
            validate(values);

            List<Double> ordered = new ArrayList<>(values);
            ordered.sort(Comparator.naturalOrder());

            int middle = ordered.size() / 2;

            if (ordered.size() % 2 == 1) {
                return ordered.get(middle);
            }

            return (ordered.get(middle - 1) + ordered.get(middle)) / 2.0;
        }

        static List<Double> mode(List<Double> values) {
            validate(values);

            Map<Double, Long> frequencies = new HashMap<>();

            for (double value : values) {
                frequencies.merge(value, 1L, Long::sum);
            }

            long maximum = frequencies.values()
                .stream()
                .mapToLong(Long::longValue)
                .max()
                .orElse(0);

            if (maximum == 1) {
                return List.of();
            }

            return frequencies.entrySet()
                .stream()
                .filter(entry -> entry.getValue() == maximum)
                .map(Map.Entry::getKey)
                .sorted()
                .toList();
        }

        static double weightedMean(
            List<WeightedObservation> observations
        ) {
            if (observations == null || observations.isEmpty()) {
                throw new MeasureException(
                    "Weighted observations cannot be empty."
                );
            }

            double weightedTotal = 0;
            double totalWeight = 0;

            for (WeightedObservation observation : observations) {
                weightedTotal +=
                    observation.value() * observation.weight();
                totalWeight += observation.weight();
            }

            if (totalWeight <= 0) {
                throw new MeasureException(
                    "Total weight must be greater than zero."
                );
            }

            return weightedTotal / totalWeight;
        }

        static double geometricMean(List<Double> values) {
            validate(values);

            if (values.stream().anyMatch(value -> value <= 0)) {
                throw new MeasureException(
                    "Geometric mean requires positive observations."
                );
            }

            return Math.exp(
                values.stream()
                    .mapToDouble(Math::log)
                    .average()
                    .orElseThrow()
            );
        }

        static double harmonicMean(List<Double> values) {
            validate(values);

            if (values.stream().anyMatch(value -> value <= 0)) {
                throw new MeasureException(
                    "Harmonic mean requires positive observations."
                );
            }

            double reciprocalSum = values.stream()
                .mapToDouble(value -> 1.0 / value)
                .sum();

            return values.size() / reciprocalSum;
        }
    }

    static final class ReviewAnalyticsService {
        private final List<ReviewMetric> metrics = new ArrayList<>();

        void record(ReviewMetric metric) {
            metrics.add(Objects.requireNonNull(metric));
        }

        List<Double> durations() {
            return metrics.stream()
                .map(ReviewMetric::reviewHours)
                .toList();
        }

        double averageReviewDuration() {
            return CentralTendencyService.mean(durations());
        }

        double typicalReviewDuration() {
            return CentralTendencyService.median(durations());
        }

        Map<MeasureType, Double> summarize() {
            List<Double> durations = durations();

            Map<MeasureType, Double> result =
                new EnumMap<>(MeasureType.class);

            result.put(
                MeasureType.MEAN,
                CentralTendencyService.mean(durations)
            );
            result.put(
                MeasureType.MEDIAN,
                CentralTendencyService.median(durations)
            );
            result.put(
                MeasureType.GEOMETRIC_MEAN,
                CentralTendencyService.geometricMean(durations)
            );
            result.put(
                MeasureType.HARMONIC_MEAN,
                CentralTendencyService.harmonicMean(durations)
            );

            return Map.copyOf(result);
        }
    }

    private static void print(String label, double value) {
        System.out.printf("%-22s %.4f%n", label, value);
    }

    public static void main(String[] args) {
        try {
            List<Double> reviewDurations =
                List.of(2.0, 3.0, 3.0, 4.0, 5.0, 8.0, 40.0);

            List<Double> deploymentMultipliers =
                List.of(1.02, 1.04, 1.06, 1.03);

            List<Double> throughputRates =
                List.of(30.0, 40.0, 50.0);

            System.out.println("Review Duration Analysis");
            System.out.println("========================");

            print(
                "Mean",
                CentralTendencyService.mean(reviewDurations)
            );
            print(
                "Median",
                CentralTendencyService.median(reviewDurations)
            );

            System.out.println(
                "Mode: " +
                CentralTendencyService.mode(reviewDurations)
            );

            print(
                "Geometric mean",
                CentralTendencyService.geometricMean(
                    deploymentMultipliers
                )
            );

            print(
                "Harmonic mean",
                CentralTendencyService.harmonicMean(
                    throughputRates
                )
            );

            List<WeightedObservation> qualityWeights = List.of(
                new WeightedObservation(80, 0.20),
                new WeightedObservation(88, 0.30),
                new WeightedObservation(94, 0.50)
            );

            print(
                "Weighted quality score",
                CentralTendencyService.weightedMean(
                    qualityWeights
                )
            );

            ReviewAnalyticsService analytics =
                new ReviewAnalyticsService();

            analytics.record(
                new ReviewMetric(
                    "reviewer-a",
                    ReviewState.APPROVED,
                    3.0
                )
            );
            analytics.record(
                new ReviewMetric(
                    "reviewer-b",
                    ReviewState.APPROVED,
                    5.0
                )
            );
            analytics.record(
                new ReviewMetric(
                    "reviewer-c",
                    ReviewState.CHANGES_REQUESTED,
                    4.0
                )
            );
            analytics.record(
                new ReviewMetric(
                    "reviewer-d",
                    ReviewState.APPROVED,
                    35.0
                )
            );

            System.out.println("\nEnterprise Review Analytics");
            System.out.println("===========================");

            print(
                "Average duration",
                analytics.averageReviewDuration()
            );
            print(
                "Typical duration",
                analytics.typicalReviewDuration()
            );

            System.out.println("\nMeasure Map");
            analytics.summarize().forEach(
                (measure, value) ->
                    System.out.printf(
                        "%-22s %.4f%n",
                        measure,
                        value
                    )
            );

            System.out.println("\nFailure Conditions");
            System.out.println("==================");

            try {
                CentralTendencyService.geometricMean(
                    List.of(10.0, 0.0, 20.0)
                );
            } catch (MeasureException exception) {
                System.out.println(
                    "Geometric mean rejected: " +
                    exception.getMessage()
                );
            }

            try {
                CentralTendencyService.weightedMean(
                    List.of(
                        new WeightedObservation(10, 0),
                        new WeightedObservation(20, 0)
                    )
                );
            } catch (MeasureException exception) {
                System.out.println(
                    "Weighted mean rejected: " +
                    exception.getMessage()
                );
            }

            if (CentralTendencyService.mean(
                    List.of(2.0, 4.0, 6.0)
                ) != 4.0) {
                throw new AssertionError("Mean test failed.");
            }

            if (CentralTendencyService.median(
                    List.of(1.0, 2.0, 3.0, 4.0)
                ) != 2.5) {
                throw new AssertionError("Median test failed.");
            }

            System.out.println("\nValidation tests passed.");
        } catch (RuntimeException exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
