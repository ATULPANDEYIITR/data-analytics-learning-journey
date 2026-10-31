import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class StatisticsFundamentals {

    enum SamplingMethod {
        SIMPLE_RANDOM,
        SYSTEMATIC
    }

    record Population(List<Double> values) {
        Population {
            Objects.requireNonNull(values, "values");
            if (values.isEmpty()) {
                throw new StatisticsException("Population cannot be empty.");
            }
            values = List.copyOf(values);
            validate(values, "population");
        }
    }

    record Sample(List<Double> values, int populationSize) {
        Sample {
            Objects.requireNonNull(values, "values");
            if (values.isEmpty()) {
                throw new StatisticsException("Sample cannot be empty.");
            }
            if (populationSize < values.size()) {
                throw new StatisticsException(
                    "Population size cannot be smaller than sample size."
                );
            }
            values = List.copyOf(values);
            validate(values, "sample");
        }
    }

    record DescriptiveStatistics(
        int count,
        double minimum,
        double maximum,
        double mean,
        double median,
        List<Double> modes,
        double populationVariance,
        double populationStandardDeviation,
        Double sampleVariance,
        Double sampleStandardDeviation
    ) {}

    static class StatisticsException extends RuntimeException {
        StatisticsException(String message) {
            super(message);
        }
    }

    static void validate(List<Double> values, String name) {
        for (Double value : values) {
            if (value == null || !Double.isFinite(value)) {
                throw new StatisticsException(
                    name + " contains a non-finite value."
                );
            }
        }
    }

    static double mean(List<Double> values) {
        validate(values, "values");
        return values.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElseThrow(() ->
                new StatisticsException("Cannot calculate mean."));
    }

    static double median(List<Double> values) {
        validate(values, "values");

        List<Double> sorted = new ArrayList<>(values);
        sorted.sort(Comparator.naturalOrder());

        int middle = sorted.size() / 2;

        if (sorted.size() % 2 == 0) {
            return (sorted.get(middle - 1) + sorted.get(middle)) / 2.0;
        }

        return sorted.get(middle);
    }

    static double variance(List<Double> values, boolean sample) {
        validate(values, "values");

        if (sample && values.size() < 2) {
            throw new StatisticsException(
                "Sample variance requires at least two observations."
            );
        }

        double average = mean(values);

        double squaredDeviation = values.stream()
            .mapToDouble(value -> Math.pow(value - average, 2))
            .sum();

        int divisor = sample ? values.size() - 1 : values.size();
        return squaredDeviation / divisor;
    }

    static List<Double> modes(List<Double> values) {
        validate(values, "values");

        Map<Double, Long> frequencies = values.stream()
            .collect(Collectors.groupingBy(
                value -> value,
                TreeMap::new,
                Collectors.counting()
            ));

        long maximum = Collections.max(frequencies.values());

        return frequencies.entrySet()
            .stream()
            .filter(entry -> entry.getValue() == maximum)
            .map(Map.Entry::getKey)
            .toList();
    }

    static DescriptiveStatistics describe(List<Double> values) {
        validate(values, "values");

        double populationVariance = variance(values, false);
        Double sampleVariance =
            values.size() >= 2 ? variance(values, true) : null;

        return new DescriptiveStatistics(
            values.size(),
            Collections.min(values),
            Collections.max(values),
            mean(values),
            median(values),
            modes(values),
            populationVariance,
            Math.sqrt(populationVariance),
            sampleVariance,
            sampleVariance == null
                ? null
                : Math.sqrt(sampleVariance)
        );
    }

    static Sample simpleRandomSample(
        Population population,
        int sampleSize,
        long seed
    ) {
        if (sampleSize < 1 || sampleSize > population.values().size()) {
            throw new StatisticsException("Invalid sample size.");
        }

        List<Double> shuffled =
            new ArrayList<>(population.values());

        Collections.shuffle(shuffled, new Random(seed));

        return new Sample(
            shuffled.subList(0, sampleSize),
            population.values().size()
        );
    }

    static Sample systematicSample(
        Population population,
        int sampleSize
    ) {
        if (sampleSize < 1 ||
            sampleSize > population.values().size()) {
            throw new StatisticsException("Invalid sample size.");
        }

        double interval =
            (double) population.values().size() / sampleSize;

        List<Double> result = new ArrayList<>();

        for (int i = 0; i < sampleSize; i++) {
            int index = (int) Math.floor(i * interval);
            result.add(population.values().get(index));
        }

        return new Sample(
            result,
            population.values().size()
        );
    }

    static double standardError(Sample sample) {
        return Math.sqrt(
            variance(sample.values(), true) /
            sample.values().size()
        );
    }

    static void printStatistics(DescriptiveStatistics statistics) {
        System.out.printf(
            "count=%d, min=%.2f, max=%.2f, mean=%.2f, median=%.2f%n",
            statistics.count(),
            statistics.minimum(),
            statistics.maximum(),
            statistics.mean(),
            statistics.median()
        );

        System.out.printf(
            "modes=%s, population variance=%.4f, population SD=%.4f%n",
            statistics.modes(),
            statistics.populationVariance(),
            statistics.populationStandardDeviation()
        );

        System.out.printf(
            "sample variance=%.4f, sample SD=%.4f%n",
            statistics.sampleVariance(),
            statistics.sampleStandardDeviation()
        );
    }

    public static void main(String[] args) {
        try {
            Population population = new Population(List.of(
                61.0, 64.0, 66.0, 68.0, 69.0,
                71.0, 72.0, 73.0, 74.0, 75.0,
                76.0, 77.0, 78.0, 79.0, 80.0,
                81.0, 82.0, 83.0, 84.0, 85.0,
                86.0, 87.0, 88.0, 90.0, 92.0
            ));

            DescriptiveStatistics populationStats =
                describe(population.values());

            System.out.println("Population statistics:");
            printStatistics(populationStats);

            Sample randomSample =
                simpleRandomSample(population, 8, 42);

            System.out.println("\nSimple random sample:");
            System.out.println(randomSample.values());
            printStatistics(describe(randomSample.values()));

            Sample systematic =
                systematicSample(population, 5);

            System.out.println("\nSystematic sample:");
            System.out.println(systematic.values());
            printStatistics(describe(systematic.values()));

            double parameter = populationStats.mean();
            double statistic = mean(randomSample.values());

            System.out.printf(
                "%nPopulation parameter: %.4f%n",
                parameter
            );

            System.out.printf(
                "Sample statistic: %.4f%n",
                statistic
            );

            System.out.printf(
                "Standard error: %.4f%n",
                standardError(randomSample)
            );

            if (populationStats.count() != 25) {
                throw new StatisticsException(
                    "Population count validation failed."
                );
            }

            if (randomSample.values().size() != 8) {
                throw new StatisticsException(
                    "Sample size validation failed."
                );
            }

            try {
                simpleRandomSample(population, 0, 42);
            } catch (StatisticsException expected) {
                System.out.println(
                    "\nExpected validation failure: " +
                    expected.getMessage()
                );
            }

            try {
                variance(List.of(10.0), true);
            } catch (StatisticsException expected) {
                System.out.println(
                    "Expected variance failure: " +
                    expected.getMessage()
                );
            }

            /*
             * Records provide immutable domain objects for population
             * and sample state. Streams handle aggregation while the
             * explicit service methods keep statistical rules visible.
             */
            System.out.println("\nAll checks passed.");
        } catch (RuntimeException error) {
            System.err.println("Fatal error: " + error.getMessage());
            System.exit(1);
        }
    }
}
