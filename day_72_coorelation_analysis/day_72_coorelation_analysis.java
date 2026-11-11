import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * Enterprise Correlation Analysis System.
 *
 * Java 17
 * Standard library only.
 *
 * Includes:
 * - Immutable domain records
 * - Pearson, Spearman, Kendall tau-b
 * - Partial correlation
 * - Permutation testing
 * - Configurable analysis policies
 * - Validation and custom exceptions
 * - Concurrent analysis execution
 * - Auditable analysis history
 */

public class CorrelationAnalysis {

    enum Method {
        PEARSON,
        SPEARMAN,
        KENDALL
    }

    enum AssociationStrength {
        NEGLIGIBLE,
        WEAK,
        MODERATE,
        STRONG,
        VERY_STRONG
    }

    enum Direction {
        POSITIVE,
        NEGATIVE,
        NEUTRAL
    }

    static class AnalysisException extends RuntimeException {
        AnalysisException(String message) {
            super(message);
        }
    }

    static class ValidationException extends AnalysisException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class InsufficientDataException extends AnalysisException {
        InsufficientDataException(String message) {
            super(message);
        }
    }

    record Observation(double x, double y) {
        Observation {
            if (!Double.isFinite(x) || !Double.isFinite(y)) {
                throw new ValidationException(
                    "Observation values must be finite."
                );
            }
        }
    }

    record CorrelationMetric(
        Method method,
        double coefficient,
        AssociationStrength strength,
        Direction direction,
        int sampleSize,
        String limitation
    ) {}

    record AnalysisPolicy(
        int minimumSampleSize,
        double significanceLevel,
        boolean requireAllMethods
    ) {
        AnalysisPolicy {
            if (minimumSampleSize < 3) {
                throw new ValidationException(
                    "Minimum sample size must be at least three."
                );
            }

            if (
                significanceLevel <= 0 ||
                significanceLevel >= 1
            ) {
                throw new ValidationException(
                    "Significance level must be between zero and one."
                );
            }
        }

        static AnalysisPolicy standard() {
            return new AnalysisPolicy(3, 0.05, true);
        }

        static AnalysisPolicy enterprise() {
            return new AnalysisPolicy(30, 0.01, true);
        }
    }

    record AnalysisReport(
        long id,
        String name,
        int sampleSize,
        List<CorrelationMetric> metrics,
        InstantHolder timestamp
    ) {
        AnalysisReport {
            metrics = List.copyOf(metrics);
        }
    }

    record InstantHolder(String value) {}

    record PermutationResult(
        double observed,
        double pValue,
        int iterations,
        boolean significant
    ) {}

    record PairCounts(
        long concordant,
        long discordant,
        long tiesX,
        long tiesY
    ) {}

    static final class CorrelationStatistics {

        private CorrelationStatistics() {}

        static List<Observation> validate(
            List<Observation> observations,
            int minimum
        ) {
            Objects.requireNonNull(observations);

            List<Observation> clean = observations.stream()
                .filter(Objects::nonNull)
                .toList();

            if (clean.size() < minimum) {
                throw new InsufficientDataException(
                    "Required " + minimum +
                    " observations; received " + clean.size()
                );
            }

            return clean;
        }

        static double mean(List<Double> values) {
            return values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow(
                    () -> new InsufficientDataException(
                        "Cannot calculate an empty mean."
                    )
                );
        }

        static double pearson(List<Observation> input) {
            List<Observation> data = validate(input, 3);

            double mx = data.stream()
                .mapToDouble(Observation::x)
                .average()
                .orElseThrow();

            double my = data.stream()
                .mapToDouble(Observation::y)
                .average()
                .orElseThrow();

            double numerator = 0;
            double sumX = 0;
            double sumY = 0;

            for (Observation item : data) {
                double dx = item.x() - mx;
                double dy = item.y() - my;

                numerator += dx * dy;
                sumX += dx * dx;
                sumY += dy * dy;
            }

            double denominator = Math.sqrt(sumX * sumY);

            if (denominator == 0) {
                throw new ValidationException(
                    "Pearson correlation is undefined for constant data."
                );
            }

            return numerator / denominator;
        }

        static List<Double> averageRanks(List<Double> values) {
            List<Integer> indices = new ArrayList<>();

            for (int i = 0; i < values.size(); i++) {
                indices.add(i);
            }

            indices.sort(
                Comparator.comparingDouble(values::get)
            );

            Double[] ranks = new Double[values.size()];

            int i = 0;

            while (i < indices.size()) {
                int j = i + 1;

                while (
                    j < indices.size() &&
                    Double.compare(
                        values.get(indices.get(i)),
                        values.get(indices.get(j))
                    ) == 0
                ) {
                    j++;
                }

                double averageRank = (i + 1 + j) / 2.0;

                for (int k = i; k < j; k++) {
                    ranks[indices.get(k)] = averageRank;
                }

                i = j;
            }

            return Arrays.asList(ranks);
        }

        static double spearman(List<Observation> data) {
            data = validate(data, 3);

            List<Double> x = data.stream()
                .map(Observation::x)
                .toList();

            List<Double> y = data.stream()
                .map(Observation::y)
                .toList();

            List<Double> rankX = averageRanks(x);
            List<Double> rankY = averageRanks(y);

            List<Observation> ranked = new ArrayList<>();

            for (int i = 0; i < data.size(); i++) {
                ranked.add(
                    new Observation(rankX.get(i), rankY.get(i))
                );
            }

            return pearson(ranked);
        }

        static PairCounts countPairs(List<Observation> data) {
            long concordant = 0;
            long discordant = 0;
            long tiesX = 0;
            long tiesY = 0;

            for (int i = 0; i < data.size(); i++) {
                for (int j = i + 1; j < data.size(); j++) {
                    Observation a = data.get(i);
                    Observation b = data.get(j);

                    int dx = Double.compare(a.x(), b.x());
                    int dy = Double.compare(a.y(), b.y());

                    if (dx == 0 && dy == 0) continue;

                    if (dx == 0) tiesX++;
                    else if (dy == 0) tiesY++;
                    else if (dx == dy) concordant++;
                    else discordant++;
                }
            }

            return new PairCounts(
                concordant,
                discordant,
                tiesX,
                tiesY
            );
        }

        static double kendall(List<Observation> input) {
            List<Observation> data = validate(input, 3);

            PairCounts counts = countPairs(data);

            double denominator = Math.sqrt(
                (counts.concordant() +
                    counts.discordant() +
                    counts.tiesX()) *
                (double) (
                    counts.concordant() +
                    counts.discordant() +
                    counts.tiesY()
                )
            );

            if (denominator == 0) {
                throw new ValidationException(
                    "Kendall tau-b is undefined."
                );
            }

            return (
                counts.concordant() - counts.discordant()
            ) / denominator;
        }

        static double partialCorrelation(
            List<Double> x,
            List<Double> y,
            List<Double> z
        ) {
            if (
                x.size() != y.size() ||
                x.size() != z.size() ||
                x.size() < 3
            ) {
                throw new ValidationException(
                    "Partial correlation dimensions are invalid."
                );
            }

            if (
                !x.stream().allMatch(Double::isFinite) ||
                !y.stream().allMatch(Double::isFinite) ||
                !z.stream().allMatch(Double::isFinite)
            ) {
                throw new ValidationException(
                    "Partial correlation requires finite values."
                );
            }

            double mx = mean(x);
            double my = mean(y);
            double mz = mean(z);

            double denominator = 0;
            double covarianceX = 0;
            double covarianceY = 0;

            for (int i = 0; i < z.size(); i++) {
                double dz = z.get(i) - mz;

                denominator += dz * dz;
                covarianceX += dz * (x.get(i) - mx);
                covarianceY += dz * (y.get(i) - my);
            }

            if (denominator == 0) {
                throw new ValidationException(
                    "Confounder is constant."
                );
            }

            double slopeX = covarianceX / denominator;
            double slopeY = covarianceY / denominator;

            List<Observation> residuals = new ArrayList<>();

            for (int i = 0; i < z.size(); i++) {
                double rx = x.get(i) - mx
                    - slopeX * (z.get(i) - mz);

                double ry = y.get(i) - my
                    - slopeY * (z.get(i) - mz);

                residuals.add(new Observation(rx, ry));
            }

            return pearson(residuals);
        }

        static AssociationStrength strength(double value) {
            double magnitude = Math.abs(value);

            if (magnitude < 0.10) {
                return AssociationStrength.NEGLIGIBLE;
            }

            if (magnitude < 0.30) {
                return AssociationStrength.WEAK;
            }

            if (magnitude < 0.50) {
                return AssociationStrength.MODERATE;
            }

            if (magnitude < 0.70) {
                return AssociationStrength.STRONG;
            }

            return AssociationStrength.VERY_STRONG;
        }

        static Direction direction(double value) {
            if (value > 0) return Direction.POSITIVE;
            if (value < 0) return Direction.NEGATIVE;

            return Direction.NEUTRAL;
        }
    }

    interface CorrelationCalculator {
        double calculate(List<Observation> data);
    }

    static final class CorrelationService {

        private final AnalysisPolicy policy;

        private final Map<Method, CorrelationCalculator> calculators;

        private final AtomicLong sequence = new AtomicLong(1);

        private final ConcurrentMap<Long, AnalysisReport> history =
            new ConcurrentHashMap<>();

        CorrelationService(AnalysisPolicy policy) {
            this.policy = Objects.requireNonNull(policy);

            Map<Method, CorrelationCalculator> registry =
                new EnumMap<>(Method.class);

            registry.put(
                Method.PEARSON,
                CorrelationStatistics::pearson
            );

            registry.put(
                Method.SPEARMAN,
                CorrelationStatistics::spearman
            );

            registry.put(
                Method.KENDALL,
                CorrelationStatistics::kendall
            );

            this.calculators = Map.copyOf(registry);
        }

        AnalysisReport analyze(
            String name,
            List<Observation> observations
        ) {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Analysis name is required."
                );
            }

            List<Observation> data =
                CorrelationStatistics.validate(
                    observations,
                    policy.minimumSampleSize()
                );

            List<CorrelationMetric> metrics = new ArrayList<>();

            for (Method method : Method.values()) {
                CorrelationCalculator calculator =
                    calculators.get(method);

                double coefficient = calculator.calculate(data);

                String limitation = switch (method) {
                    case PEARSON ->
                        "Linear association; sensitive to outliers.";

                    case SPEARMAN ->
                        "Monotonic rank association; ties affect ranks.";

                    case KENDALL ->
                        "Ordinal concordance; pairwise implementation is O(n^2).";
                };

                metrics.add(
                    new CorrelationMetric(
                        method,
                        coefficient,
                        CorrelationStatistics.strength(coefficient),
                        CorrelationStatistics.direction(coefficient),
                        data.size(),
                        limitation
                    )
                );
            }

            AnalysisReport report = new AnalysisReport(
                sequence.getAndIncrement(),
                name,
                data.size(),
                metrics,
                new InstantHolder(
                    java.time.Instant.now().toString()
                )
            );

            history.put(report.id(), report);

            return report;
        }

        AnalysisReport getReport(long id) {
            AnalysisReport report = history.get(id);

            if (report == null) {
                throw new AnalysisException(
                    "Analysis report not found: " + id
                );
            }

            return report;
        }

        List<AnalysisReport> getHistory() {
            return history.values().stream()
                .sorted(
                    Comparator.comparingLong(AnalysisReport::id)
                )
                .toList();
        }

        PermutationResult permutationTest(
            List<Observation> input,
            int iterations
        ) {
            List<Observation> data =
                CorrelationStatistics.validate(
                    input,
                    policy.minimumSampleSize()
                );

            if (iterations < 100) {
                throw new ValidationException(
                    "At least 100 permutations are required."
                );
            }

            double observed =
                CorrelationStatistics.pearson(data);

            List<Double> x = data.stream()
                .map(Observation::x)
                .toList();

            List<Double> originalY = data.stream()
                .map(Observation::y)
                .toList();

            Random random = new Random(42);

            int extreme = 0;

            for (int i = 0; i < iterations; i++) {
                List<Double> shuffled = new ArrayList<>(originalY);

                Collections.shuffle(shuffled, random);

                List<Observation> permuted = new ArrayList<>();

                for (int j = 0; j < x.size(); j++) {
                    permuted.add(
                        new Observation(x.get(j), shuffled.get(j))
                    );
                }

                double simulated =
                    CorrelationStatistics.pearson(permuted);

                if (Math.abs(simulated) >= Math.abs(observed)) {
                    extreme++;
                }
            }

            double pValue =
                (extreme + 1.0) / (iterations + 1.0);

            return new PermutationResult(
                observed,
                pValue,
                iterations,
                pValue < policy.significanceLevel()
            );
        }

        CompletableFuture<AnalysisReport> analyzeAsync(
            String name,
            List<Observation> observations,
            Executor executor
        ) {
            List<Observation> snapshot = List.copyOf(observations);

            return CompletableFuture.supplyAsync(
                () -> analyze(name, snapshot),
                executor
            );
        }
    }

    static List<Observation> createConfoundedData(
        int size,
        long seed
    ) {
        Random random = new Random(seed);

        List<Observation> result = new ArrayList<>();

        for (int i = 0; i < size; i++) {
            double common = i;

            double x = 3.0 * common
                + random.nextGaussian() * 8;

            double y = 2.5 * common
                + random.nextGaussian() * 8;

            result.add(new Observation(x, y));
        }

        return result;
    }

    static void display(AnalysisReport report) {
        System.out.println("\n" + report.name());

        System.out.println("Sample size: " + report.sampleSize());

        report.metrics().forEach(metric -> {
            System.out.printf(
                "%-10s coefficient=% .6f strength=%-12s direction=%-8s%n",
                metric.method(),
                metric.coefficient(),
                metric.strength(),
                metric.direction()
            );

            System.out.println(
                "  Limitation: " + metric.limitation()
            );
        });
    }

    public static void main(String[] args) {

        CorrelationService service = new CorrelationService(
            AnalysisPolicy.standard()
        );

        try {
            List<Observation> linear = List.of(
                new Observation(1, 2),
                new Observation(2, 4),
                new Observation(3, 6),
                new Observation(4, 8),
                new Observation(5, 10),
                new Observation(6, 12)
            );

            List<Observation> nonlinear = List.of(
                new Observation(1, 1),
                new Observation(2, 4),
                new Observation(3, 9),
                new Observation(4, 16),
                new Observation(5, 25),
                new Observation(6, 36)
            );

            List<Observation> tied = List.of(
                new Observation(1, 2),
                new Observation(2, 1),
                new Observation(2, 3),
                new Observation(4, 4),
                new Observation(5, 4),
                new Observation(5, 6)
            );

            display(service.analyze(
                "Perfect linear relationship", linear
            ));

            display(service.analyze(
                "Nonlinear monotonic relationship", nonlinear
            ));

            display(service.analyze(
                "Tied observations", tied
            ));

            List<Observation> confounded =
                createConfoundedData(100, 42);

            List<Double> x = confounded.stream()
                .map(Observation::x)
                .toList();

            List<Double> y = confounded.stream()
                .map(Observation::y)
                .toList();

            List<Double> z = java.util.stream.IntStream.range(0, 100)
                .mapToDouble(i -> i)
                .boxed()
                .toList();

            System.out.println("\nConfounding demonstration");

            System.out.println(
                "Raw Pearson: " +
                CorrelationStatistics.pearson(confounded)
            );

            System.out.println(
                "Partial Pearson: " +
                CorrelationStatistics.partialCorrelation(x, y, z)
            );

            System.out.println("\nPermutation testing");

            System.out.println(
                service.permutationTest(linear, 1000)
            );

            ExecutorService executor =
                Executors.newFixedThreadPool(2);

            try {
                AnalysisReport asynchronous =
                    service.analyzeAsync(
                        "Asynchronous analysis",
                        linear,
                        executor
                    ).join();

                System.out.println(
                    "\nAsync report ID: " + asynchronous.id()
                );
            } finally {
                executor.shutdown();
            }

            System.out.println("\nAudit history");

            service.getHistory().forEach(
                report -> System.out.println(
                    report.id() + " | " +
                    report.name() + " | n=" +
                    report.sampleSize()
                )
            );

            if (
                Math.abs(
                    CorrelationStatistics.pearson(linear) - 1.0
                ) > 1e-10
            ) {
                throw new AnalysisException(
                    "Pearson verification failed."
                );
            }

            if (
                Math.abs(
                    CorrelationStatistics.spearman(nonlinear) - 1.0
                ) > 1e-10
            ) {
                throw new AnalysisException(
                    "Spearman verification failed."
                );
            }

            if (
                Math.abs(
                    CorrelationStatistics.kendall(nonlinear) - 1.0
                ) > 1e-10
            ) {
                throw new AnalysisException(
                    "Kendall verification failed."
                );
            }

            System.out.println("\nValidation completed.");

        } catch (CompletionException | AnalysisException error) {
            System.err.println(
                "Analysis failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
