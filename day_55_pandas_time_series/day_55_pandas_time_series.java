import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

public class TimeSeriesAnalytics {

    record Observation(
            Instant timestamp,
            double temperature,
            double pressure,
            double energyKwh
    ) {
        Observation {
            Objects.requireNonNull(timestamp, "timestamp");

            if (!Double.isFinite(temperature)
                    || !Double.isFinite(pressure)
                    || !Double.isFinite(energyKwh)) {
                throw new IllegalArgumentException(
                        "Measurements must be finite."
                );
            }

            if (energyKwh < 0) {
                throw new IllegalArgumentException(
                        "Energy cannot be negative."
                );
            }
        }
    }

    record DailyAggregate(
            Instant day,
            double temperatureMean,
            double pressureMean,
            double energyTotal,
            int observations
    ) {}

    record RollingResult(
            Instant timestamp,
            double temperature,
            double mean,
            double standardDeviation,
            int observations
    ) {}

    enum ReviewState {
        RAW,
        SORTED,
        ANALYZED
    }

    static class TimeSeriesException extends RuntimeException {
        TimeSeriesException(String message) {
            super(message);
        }
    }

    static final class TimeSeries {
        private final List<Observation> observations;
        private ReviewState state;

        TimeSeries(List<Observation> input) {
            if (input == null || input.isEmpty()) {
                throw new TimeSeriesException(
                        "Time series cannot be empty."
                );
            }

            List<Observation> copy = new ArrayList<>(input);
            copy.sort(Comparator.comparing(Observation::timestamp));

            for (int i = 1; i < copy.size(); i++) {
                if (copy.get(i).timestamp()
                        .equals(copy.get(i - 1).timestamp())) {
                    throw new TimeSeriesException(
                            "Duplicate timestamps are not allowed."
                    );
                }
            }

            this.observations = List.copyOf(copy);
            this.state = ReviewState.SORTED;
        }

        List<Observation> observations() {
            return observations;
        }

        List<DailyAggregate> resampleDaily() {
            Map<Instant, List<Observation>> buckets =
                    new TreeMap<>();

            for (Observation observation : observations) {
                ZonedDateTime utc = observation.timestamp()
                        .atZone(ZoneOffset.UTC);

                Instant day = utc.toLocalDate()
                        .atStartOfDay(ZoneOffset.UTC)
                        .toInstant();

                buckets.computeIfAbsent(day, ignored -> new ArrayList<>())
                        .add(observation);
            }

            List<DailyAggregate> result = new ArrayList<>();

            for (Map.Entry<Instant, List<Observation>> entry
                    : buckets.entrySet()) {

                List<Observation> values = entry.getValue();

                double temperatureMean = values.stream()
                        .mapToDouble(Observation::temperature)
                        .average()
                        .orElseThrow();

                double pressureMean = values.stream()
                        .mapToDouble(Observation::pressure)
                        .average()
                        .orElseThrow();

                double energyTotal = values.stream()
                        .mapToDouble(Observation::energyKwh)
                        .sum();

                result.add(
                        new DailyAggregate(
                                entry.getKey(),
                                temperatureMean,
                                pressureMean,
                                energyTotal,
                                values.size()
                        )
                );
            }

            state = ReviewState.ANALYZED;
            return result;
        }

        List<RollingResult> rolling(Duration window) {
            if (window.isZero() || window.isNegative()) {
                throw new IllegalArgumentException(
                        "Rolling window must be positive."
                );
            }

            List<RollingResult> result = new ArrayList<>();
            int left = 0;

            for (int right = 0; right < observations.size(); right++) {
                Instant current = observations.get(right).timestamp();

                while (
                        left < right
                                && Duration.between(
                                        observations.get(left).timestamp(),
                                        current
                                ).compareTo(window) > 0
                ) {
                    left++;
                }

                List<Double> values = new ArrayList<>();

                for (int i = left; i <= right; i++) {
                    values.add(observations.get(i).temperature());
                }

                double mean = values.stream()
                        .mapToDouble(Double::doubleValue)
                        .average()
                        .orElseThrow();

                double standardDeviation =
                        sampleStandardDeviation(values, mean);

                result.add(
                        new RollingResult(
                                current,
                                observations.get(right).temperature(),
                                mean,
                                standardDeviation,
                                values.size()
                        )
                );
            }

            state = ReviewState.ANALYZED;
            return result;
        }

        List<Map<String, Object>> shiftAndDifference(
                String field
        ) {
            if (!field.equals("temperature")
                    && !field.equals("pressure")
                    && !field.equals("energyKwh")) {
                throw new IllegalArgumentException(
                        "Unsupported field: " + field
                );
            }

            List<Map<String, Object>> result = new ArrayList<>();

            for (int i = 0; i < observations.size(); i++) {
                Observation current = observations.get(i);

                double currentValue = valueOf(current, field);

                Map<String, Object> row = new HashMap<>();
                row.put("timestamp", current.timestamp());
                row.put("current", currentValue);

                if (i == 0) {
                    row.put("previous", null);
                    row.put("difference", null);
                } else {
                    double previousValue =
                            valueOf(observations.get(i - 1), field);

                    row.put("previous", previousValue);
                    row.put(
                            "difference",
                            currentValue - previousValue
                    );
                }

                result.add(row);
            }

            return result;
        }

        Map<Integer, List<Observation>> groupByHour() {
            Map<Integer, List<Observation>> groups = new TreeMap<>();

            for (Observation observation : observations) {
                int hour = observation.timestamp()
                        .atZone(ZoneOffset.UTC)
                        .getHour();

                groups.computeIfAbsent(
                        hour,
                        ignored -> new ArrayList<>()
                ).add(observation);
            }

            return groups;
        }

        ReviewState state() {
            return state;
        }
    }

    static double valueOf(Observation observation, String field) {
        return switch (field) {
            case "temperature" -> observation.temperature();
            case "pressure" -> observation.pressure();
            case "energyKwh" -> observation.energyKwh();
            default -> throw new IllegalArgumentException(
                    "Unknown field: " + field
            );
        };
    }

    static double sampleStandardDeviation(
            List<Double> values,
            double mean
    ) {
        if (values.size() < 2) {
            return 0.0;
        }

        double squared = 0.0;

        for (double value : values) {
            squared += Math.pow(value - mean, 2);
        }

        return Math.sqrt(
                squared / (values.size() - 1)
        );
    }

    static TimeSeries createSeries() {
        return new TimeSeries(List.of(
                new Observation(
                        Instant.parse("2026-01-01T08:00:00Z"),
                        21.2, 1008, 3.1
                ),
                new Observation(
                        Instant.parse("2026-01-01T12:00:00Z"),
                        22.1, 1007, 2.4
                ),
                new Observation(
                        Instant.parse("2026-01-02T09:30:00Z"),
                        20.8, 1009, 3.7
                ),
                new Observation(
                        Instant.parse("2026-01-03T10:00:00Z"),
                        23.4, 1006, 4.0
                ),
                new Observation(
                        Instant.parse("2026-01-05T14:00:00Z"),
                        24.0, 1005, 5.1
                ),
                new Observation(
                        Instant.parse("2026-01-06T11:15:00Z"),
                        23.2, 1007, 4.4
                ),
                new Observation(
                        Instant.parse("2026-01-08T16:30:00Z"),
                        25.1, 1004, 5.8
                ),
                new Observation(
                        Instant.parse("2026-01-10T09:00:00Z"),
                        26.0, 1003, 6.2
                ),
                new Observation(
                        Instant.parse("2026-01-12T13:45:00Z"),
                        24.7, 1005, 5.0
                ),
                new Observation(
                        Instant.parse("2026-01-14T15:00:00Z"),
                        27.2, 1002, 6.7
                )
        ));
    }

    public static void main(String[] args) {
        TimeSeries series = createSeries();

        System.out.println("=== Daily Resampling ===");

        for (DailyAggregate aggregate : series.resampleDaily()) {
            System.out.printf(
                    "%s | temperature=%.2f | pressure=%.2f "
                            + "| energy=%.2f | observations=%d%n",
                    aggregate.day(),
                    aggregate.temperatureMean(),
                    aggregate.pressureMean(),
                    aggregate.energyTotal(),
                    aggregate.observations()
            );
        }

        System.out.println("\n=== Seven-Day Rolling Window ===");

        for (RollingResult result :
                series.rolling(Duration.ofDays(7))) {

            System.out.printf(
                    "%s | value=%.2f | mean=%.2f | std=%.2f "
                            + "| observations=%d%n",
                    result.timestamp(),
                    result.temperature(),
                    result.mean(),
                    result.standardDeviation(),
                    result.observations()
            );
        }

        System.out.println("\n=== Shift and Difference ===");
        series.shiftAndDifference("temperature")
                .forEach(System.out::println);

        System.out.println("\n=== Hour Grouping ===");
        series.groupByHour()
                .forEach((hour, values) ->
                        System.out.printf(
                                "hour=%d | observations=%d%n",
                                hour,
                                values.size()
                        )
                );

        if (series.observations().size() != 10) {
            throw new AssertionError("Unexpected observation count.");
        }

        if (series.state() != ReviewState.ANALYZED) {
            throw new AssertionError("Analysis state was not reached.");
        }

        System.out.println("\nValidation checks passed.");
    }
}
