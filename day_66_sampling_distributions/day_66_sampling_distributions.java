import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/*
 * Enterprise Sampling Distribution Analysis
 *
 * Java 17 implementation.
 *
 * Domain:
 * Customer transaction analytics and quality monitoring.
 *
 * Features:
 * - Immutable population and statistical records
 * - Sample generation
 * - Sampling mean and standard error
 * - Finite population correction
 * - Central Limit Theorem experiments
 * - Law of Large Numbers
 * - Asynchronous experiment execution
 * - Experiment lifecycle and validation
 * - Confidence interval estimation
 */

public class SamplingDistributions {

    enum SamplingMethod {
        WITH_REPLACEMENT,
        WITHOUT_REPLACEMENT
    }

    enum ExperimentStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    static class SamplingException extends RuntimeException {
        public SamplingException(String message) {
            super(message);
        }
    }

    record PopulationStatistics(
        int size,
        double mean,
        double variance,
        double standardDeviation
    ) {}

    record SampleStatistics(
        int size,
        double mean,
        double variance,
        double standardDeviation
    ) {}

    record SamplingPolicy(
        int minimumSampleSize,
        int minimumRepetitions,
        boolean allowReplacement
    ) {
        public SamplingPolicy {
            if (minimumSampleSize <= 0 || minimumRepetitions < 2) {
                throw new IllegalArgumentException(
                    "Invalid sampling policy."
                );
            }
        }

        void validate(
            int sampleSize,
            int populationSize,
            int repetitions,
            SamplingMethod method
        ) {
            if (sampleSize < minimumSampleSize) {
                throw new SamplingException(
                    "Sample size is below the minimum policy."
                );
            }

            if (repetitions < minimumRepetitions) {
                throw new SamplingException(
                    "Insufficient simulation repetitions."
                );
            }

            if (
                method == SamplingMethod.WITHOUT_REPLACEMENT &&
                sampleSize > populationSize
            ) {
                throw new SamplingException(
                    "Sample exceeds population size."
                );
            }

            if (
                method == SamplingMethod.WITH_REPLACEMENT &&
                !allowReplacement
            ) {
                throw new SamplingException(
                    "Sampling with replacement is prohibited."
                );
            }
        }
    }

    record ExperimentRequest(
        int sampleSize,
        int repetitions,
        SamplingMethod method
    ) {
        public ExperimentRequest {
            Objects.requireNonNull(method, "Sampling method is required.");

            if (sampleSize <= 0 || repetitions < 2) {
                throw new IllegalArgumentException(
                    "Invalid experiment request."
                );
            }
        }
    }

    record SamplingResult(
        UUID experimentId,
        int sampleSize,
        int repetitions,
        SamplingMethod method,
        double samplingMean,
        double populationMean,
        double theoreticalStandardError,
        double empiricalStandardError,
        double bias,
        double minimum,
        double maximum
    ) {}

    record ConfidenceInterval(
        double estimate,
        double standardError,
        double confidenceLevel,
        double lowerBound,
        double upperBound
    ) {}

    static class Population {
        private final String name;
        private final List<Double> observations;
        private final PopulationStatistics statistics;

        Population(String name, List<Double> observations) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Population name is required."
                );
            }

            if (observations == null || observations.isEmpty()) {
                throw new IllegalArgumentException(
                    "Population cannot be empty."
                );
            }

            for (Double value : observations) {
                if (
                    value == null ||
                    !Double.isFinite(value)
                ) {
                    throw new IllegalArgumentException(
                        "Population contains invalid observations."
                    );
                }
            }

            this.name = name;
            this.observations = List.copyOf(observations);

            this.statistics = calculateStatistics();
        }

        private PopulationStatistics calculateStatistics() {
            int size = observations.size();

            double mean = observations.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();

            double variance = observations.stream()
                .mapToDouble(value -> Math.pow(value - mean, 2))
                .sum() / size;

            return new PopulationStatistics(
                size,
                mean,
                variance,
                Math.sqrt(variance)
            );
        }

        String name() {
            return name;
        }

        List<Double> observations() {
            return observations;
        }

        PopulationStatistics statistics() {
            return statistics;
        }

        SampleStatistics calculateSampleStatistics(
            List<Double> sample
        ) {
            if (sample == null || sample.isEmpty()) {
                throw new SamplingException("Sample cannot be empty.");
            }

            double mean = sample.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();

            double variance = sample.size() < 2
                ? 0.0
                : sample.stream()
                    .mapToDouble(value ->
                        Math.pow(value - mean, 2)
                    )
                    .sum() / (sample.size() - 1);

            return new SampleStatistics(
                sample.size(),
                mean,
                variance,
                Math.sqrt(variance)
            );
        }

        double standardError(
            int sampleSize,
            SamplingMethod method
        ) {
            if (sampleSize <= 0) {
                throw new SamplingException(
                    "Sample size must be positive."
                );
            }

            if (
                method == SamplingMethod.WITHOUT_REPLACEMENT &&
                sampleSize > observations.size()
            ) {
                throw new SamplingException("Invalid sample size.");
            }

            double se = statistics.standardDeviation()
                / Math.sqrt(sampleSize);

            if (method == SamplingMethod.WITHOUT_REPLACEMENT) {
                double correction = observations.size() == 1
                    ? 0.0
                    : Math.sqrt(
                        (double) (observations.size() - sampleSize)
                        / (observations.size() - 1)
                    );

                se *= correction;
            }

            return se;
        }

        List<Double> drawSample(
            int sampleSize,
            SamplingMethod method,
            Random random
        ) {
            Objects.requireNonNull(random);

            if (sampleSize <= 0) {
                throw new SamplingException(
                    "Sample size must be positive."
                );
            }

            if (
                method == SamplingMethod.WITHOUT_REPLACEMENT &&
                sampleSize > observations.size()
            ) {
                throw new SamplingException(
                    "Sample exceeds population size."
                );
            }

            List<Double> sample = new ArrayList<>(sampleSize);

            if (method == SamplingMethod.WITH_REPLACEMENT) {
                for (int i = 0; i < sampleSize; i++) {
                    sample.add(
                        observations.get(random.nextInt(observations.size()))
                    );
                }
            } else {
                List<Double> shuffled = new ArrayList<>(observations);

                Collections.shuffle(shuffled, random);

                sample.addAll(shuffled.subList(0, sampleSize));
            }

            return List.copyOf(sample);
        }
    }

    static class ExperimentService {
        private final Population population;
        private final SamplingPolicy policy;
        private final Random random;

        ExperimentService(
            Population population,
            SamplingPolicy policy,
            long seed
        ) {
            this.population = Objects.requireNonNull(population);
            this.policy = Objects.requireNonNull(policy);
            this.random = new Random(seed);
        }

        synchronized SamplingResult execute(
            ExperimentRequest request
        ) {
            policy.validate(
                request.sampleSize(),
                population.statistics().size(),
                request.repetitions(),
                request.method()
            );

            UUID experimentId = UUID.randomUUID();

            double runningMean = 0.0;
            double runningM2 = 0.0;

            double minimum = Double.POSITIVE_INFINITY;
            double maximum = Double.NEGATIVE_INFINITY;

            // Welford's online algorithm reduces memory usage
            // to O(1) for the simulated sampling distribution.
            for (int i = 1; i <= request.repetitions(); i++) {
                List<Double> sample = population.drawSample(
                    request.sampleSize(),
                    request.method(),
                    random
                );

                double sampleMean = sample.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElseThrow();

                double delta = sampleMean - runningMean;

                runningMean += delta / i;

                double delta2 = sampleMean - runningMean;

                runningM2 += delta * delta2;

                minimum = Math.min(minimum, sampleMean);
                maximum = Math.max(maximum, sampleMean);
            }

            double empiricalVariance =
                runningM2 / (request.repetitions() - 1);

            return new SamplingResult(
                experimentId,
                request.sampleSize(),
                request.repetitions(),
                request.method(),
                runningMean,
                population.statistics().mean(),
                population.standardError(
                    request.sampleSize(),
                    request.method()
                ),
                Math.sqrt(Math.max(0, empiricalVariance)),
                runningMean - population.statistics().mean(),
                minimum,
                maximum
            );
        }

        List<SamplingResult> runCLT(
            List<Integer> sampleSizes,
            int repetitions
        ) {
            if (sampleSizes == null || sampleSizes.isEmpty()) {
                throw new SamplingException(
                    "At least one sample size is required."
                );
            }

            return sampleSizes.stream()
                .map(size -> execute(
                    new ExperimentRequest(
                        size,
                        repetitions,
                        SamplingMethod.WITH_REPLACEMENT
                    )
                ))
                .collect(Collectors.toUnmodifiableList());
        }

        List<Map<String, Double>> runLLN(
            List<Integer> sampleSizes
        ) {
            List<Map<String, Double>> results = new ArrayList<>();

            for (int size : sampleSizes) {
                List<Double> sample = population.drawSample(
                    size,
                    SamplingMethod.WITH_REPLACEMENT,
                    random
                );

                double mean = sample.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElseThrow();

                results.add(Map.of(
                    "sampleSize", (double) size,
                    "sampleMean", mean,
                    "populationMean", population.statistics().mean(),
                    "absoluteError", Math.abs(
                        mean - population.statistics().mean()
                    )
                ));
            }

            return List.copyOf(results);
        }
    }

    static class ExperimentManager implements AutoCloseable {
        private final ExecutorService executor;
        private final ExperimentService service;

        ExperimentManager(ExperimentService service, int threads) {
            if (threads <= 0) {
                throw new IllegalArgumentException(
                    "Thread count must be positive."
                );
            }

            this.service = service;
            this.executor = Executors.newFixedThreadPool(threads);
        }

        CompletableFuture<SamplingResult> submit(
            ExperimentRequest request
        ) {
            return CompletableFuture.supplyAsync(
                () -> service.execute(request),
                executor
            );
        }

        @Override
        public void close() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException error) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();

                throw new SamplingException(
                    "Experiment shutdown interrupted."
                );
            }
        }
    }

    static ConfidenceInterval calculateConfidenceInterval(
        double estimate,
        double standardError,
        double confidenceLevel
    ) {
        if (
            !Double.isFinite(estimate) ||
            !Double.isFinite(standardError) ||
            standardError < 0
        ) {
            throw new SamplingException(
                "Invalid confidence interval parameters."
            );
        }

        double criticalValue;

        if (confidenceLevel == 0.90) {
            criticalValue = 1.645;
        } else if (confidenceLevel == 0.95) {
            criticalValue = 1.96;
        } else if (confidenceLevel == 0.99) {
            criticalValue = 2.576;
        } else {
            throw new SamplingException(
                "Supported confidence levels: 0.90, 0.95, 0.99."
            );
        }

        double margin = criticalValue * standardError;

        return new ConfidenceInterval(
            estimate,
            standardError,
            confidenceLevel,
            estimate - margin,
            estimate + margin
        );
    }

    static void runTests() {
        Population population = new Population(
            "Test Population",
            List.of(10.0, 20.0, 30.0, 40.0, 50.0)
        );

        if (population.statistics().mean() != 30.0) {
            throw new AssertionError("Mean test failed.");
        }

        if (population.statistics().variance() != 200.0) {
            throw new AssertionError("Variance test failed.");
        }

        double se = population.standardError(
            4,
            SamplingMethod.WITH_REPLACEMENT
        );

        if (Math.abs(se - Math.sqrt(50)) > 1e-10) {
            throw new AssertionError("Standard error test failed.");
        }

        List<Double> sample = population.drawSample(
            3,
            SamplingMethod.WITHOUT_REPLACEMENT,
            new Random(42)
        );

        if (sample.stream().distinct().count() != 3) {
            throw new AssertionError("Unique sample test failed.");
        }

        boolean rejected = false;

        try {
            population.drawSample(
                6,
                SamplingMethod.WITHOUT_REPLACEMENT,
                new Random(42)
            );
        } catch (SamplingException error) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError("Invalid sample was accepted.");
        }

        ConfidenceInterval interval =
            calculateConfidenceInterval(30, 2, 0.95);

        if (
            interval.lowerBound() >= 30 ||
            interval.upperBound() <= 30
        ) {
            throw new AssertionError("Confidence interval test failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        runTests();

        List<Double> observations = new ArrayList<>();

        observations.addAll(Collections.nCopies(500, 5.0));
        observations.addAll(Collections.nCopies(250, 15.0));
        observations.addAll(Collections.nCopies(150, 30.0));
        observations.addAll(Collections.nCopies(100, 100.0));

        Population population = new Population(
            "Customer Transaction Population",
            observations
        );

        SamplingPolicy policy = new SamplingPolicy(
            1,
            100,
            true
        );

        ExperimentService service = new ExperimentService(
            population,
            policy,
            2026
        );

        System.out.println("\nPOPULATION STATISTICS");
        System.out.println(population.statistics());

        System.out.println("\nSAMPLE STATISTICS");

        List<Double> sample = population.drawSample(
            30,
            SamplingMethod.WITHOUT_REPLACEMENT,
            new Random(100)
        );

        System.out.println(
            population.calculateSampleStatistics(sample)
        );

        System.out.println("\nCENTRAL LIMIT THEOREM");

        List<SamplingResult> clt = service.runCLT(
            List.of(2, 5, 10, 30, 50, 100),
            10000
        );

        clt.forEach(System.out::println);

        System.out.println("\nLAW OF LARGE NUMBERS");

        service.runLLN(
            List.of(10, 50, 100, 500, 1000)
        ).forEach(System.out::println);

        System.out.println("\nFINITE POPULATION CORRECTION");

        for (int size : List.of(10, 50, 100, 250)) {
            System.out.println(
                "Sample size: " + size
                + ", with replacement: "
                + population.standardError(
                    size,
                    SamplingMethod.WITH_REPLACEMENT
                )
                + ", without replacement: "
                + population.standardError(
                    size,
                    SamplingMethod.WITHOUT_REPLACEMENT
                )
            );
        }

        System.out.println("\n95% CONFIDENCE INTERVAL");

        SamplingResult result = clt.get(clt.size() - 1);

        System.out.println(
            calculateConfidenceInterval(
                result.samplingMean(),
                result.theoreticalStandardError(),
                0.95
            )
        );

        System.out.println("\nASYNC EXPERIMENT EXECUTION");

        try (ExperimentManager manager = new ExperimentManager(
            service,
            2
        )) {
            CompletableFuture<SamplingResult> future = manager.submit(
                new ExperimentRequest(
                    100,
                    10000,
                    SamplingMethod.WITH_REPLACEMENT
                )
            );

            System.out.println(future.join());
        }

        System.out.println("\nAnalysis completed.");
    }
}
