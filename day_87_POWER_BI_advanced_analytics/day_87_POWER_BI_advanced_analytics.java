import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * POWER BI ADVANCED ANALYTICS
 *
 * Enterprise-oriented analytical domain model.
 *
 * Capabilities:
 * - Decomposition tree analysis
 * - Key influencer evaluation
 * - Monthly revenue forecasting
 * - Robust anomaly detection
 * - Immutable domain records
 * - Explicit analytical policies
 * - Validation and service boundaries
 *
 * Runtime: Java 17
 * External dependencies: None
 *
 * Compile:
 * javac Main.java
 *
 * Execute:
 * java Main
 */

public class Main {

    // ========================================================
    // DOMAIN EXCEPTIONS
    // ========================================================

    static class AnalyticsException extends RuntimeException {
        AnalyticsException(String message) {
            super(message);
        }
    }

    static class ValidationException extends AnalyticsException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class InsufficientDataException
            extends AnalyticsException {

        InsufficientDataException(String message) {
            super(message);
        }
    }

    // ========================================================
    // DOMAIN ENUMERATIONS
    // ========================================================

    enum Dimension {
        REGION,
        PRODUCT,
        SEGMENT,
        CHANNEL
    }

    enum AnalyticalTarget {
        HIGH_REVENUE,
        HIGH_SATISFACTION,
        HIGH_DISCOUNT
    }

    enum AnomalySeverity {
        NORMAL,
        HIGH,
        CRITICAL
    }

    // ========================================================
    // DOMAIN RECORDS
    // ========================================================

    record SalesTransaction(
            int transactionId,
            YearMonth period,
            String region,
            String product,
            String segment,
            String channel,
            double revenue,
            int units,
            double marketingSpend,
            double discount,
            double satisfaction
    ) {

        SalesTransaction {
            Objects.requireNonNull(period, "Period is required.");

            requireText(region, "Region");
            requireText(product, "Product");
            requireText(segment, "Segment");
            requireText(channel, "Channel");

            if (transactionId <= 0) {
                throw new ValidationException(
                        "Transaction ID must be positive."
                );
            }

            if (!Double.isFinite(revenue) ||
                    !Double.isFinite(marketingSpend) ||
                    !Double.isFinite(discount) ||
                    !Double.isFinite(satisfaction)) {

                throw new ValidationException(
                        "Numeric values must be finite."
                );
            }

            if (revenue < 0 || marketingSpend < 0 || units < 0) {
                throw new ValidationException(
                        "Negative financial or quantity values."
                );
            }

            if (discount < 0 || discount > 100) {
                throw new ValidationException(
                        "Discount must be between 0 and 100."
                );
            }

            if (satisfaction < 0 || satisfaction > 10) {
                throw new ValidationException(
                        "Satisfaction must be between 0 and 10."
                );
            }
        }

        private static void requireText(
                String value,
                String field
        ) {
            if (value == null || value.isBlank()) {
                throw new ValidationException(
                        field + " cannot be empty."
                );
            }
        }

        String dimensionValue(Dimension dimension) {
            return switch (dimension) {
                case REGION -> region;
                case PRODUCT -> product;
                case SEGMENT -> segment;
                case CHANNEL -> channel;
            };
        }

        double targetValue(AnalyticalTarget target) {
            return switch (target) {
                case HIGH_REVENUE -> revenue;
                case HIGH_SATISFACTION -> satisfaction;
                case HIGH_DISCOUNT -> discount;
            };
        }
    }

    record BusinessMetrics(
            int transactions,
            double totalRevenue,
            int totalUnits,
            double averageRevenue,
            double marketingSpend,
            double marketingROI
    ) {}

    record DecompositionNode(
            Dimension dimension,
            String value,
            double revenue,
            int recordCount,
            double contributionPercent,
            List<DecompositionNode> children
    ) {
        DecompositionNode {
            children = List.copyOf(children);
        }
    }

    record InfluencerResult(
            Dimension dimension,
            String value,
            int sampleSize,
            int comparisonSize,
            double targetRate,
            double comparisonRate,
            double difference
    ) {}

    record ForecastPoint(
            YearMonth period,
            double predicted,
            double lowerBound,
            double upperBound
    ) {}

    record AnomalyResult(
            int transactionId,
            double actual,
            double expected,
            double score,
            AnomalySeverity severity
    ) {}

    record ForecastPolicy(
            int minimumObservations,
            int maximumHorizon,
            double confidenceMultiplier
    ) {
        ForecastPolicy {
            if (minimumObservations < 3 ||
                    maximumHorizon < 1 ||
                    confidenceMultiplier <= 0) {

                throw new ValidationException(
                        "Invalid forecasting policy."
                );
            }
        }
    }

    record AnomalyPolicy(
            double threshold,
            double criticalThreshold
    ) {
        AnomalyPolicy {
            if (!Double.isFinite(threshold) ||
                    !Double.isFinite(criticalThreshold) ||
                    threshold <= 0 ||
                    criticalThreshold <= threshold) {

                throw new ValidationException(
                        "Invalid anomaly policy."
                );
            }
        }
    }

    // ========================================================
    // STATISTICAL UTILITIES
    // ========================================================

    static final class Statistics {

        private Statistics() {}

        static double mean(List<Double> values) {
            if (values.isEmpty()) {
                throw new InsufficientDataException(
                        "Cannot calculate mean of empty data."
                );
            }

            return values.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElseThrow();
        }

        static double median(List<Double> values) {
            if (values.isEmpty()) {
                throw new InsufficientDataException(
                        "Cannot calculate median of empty data."
                );
            }

            List<Double> sorted = values.stream()
                    .sorted()
                    .toList();

            int middle = sorted.size() / 2;

            if (sorted.size() % 2 == 0) {
                return (
                        sorted.get(middle - 1) +
                        sorted.get(middle)
                ) / 2.0;
            }

            return sorted.get(middle);
        }

        static double standardDeviation(
                List<Double> values
        ) {
            if (values.size() < 2) {
                throw new InsufficientDataException(
                        "Two observations are required."
                );
            }

            double mean = mean(values);

            double variance = values.stream()
                    .mapToDouble(
                            value -> Math.pow(value - mean, 2)
                    )
                    .sum() / (values.size() - 1);

            return Math.sqrt(variance);
        }

        static double[] linearRegression(
                List<Double> values
        ) {
            if (values.size() < 3) {
                throw new InsufficientDataException(
                        "Three observations are required."
                );
            }

            double xMean = (values.size() - 1) / 2.0;
            double yMean = mean(values);

            double numerator = 0;
            double denominator = 0;

            for (int i = 0; i < values.size(); i++) {
                numerator +=
                        (i - xMean) * (values.get(i) - yMean);

                denominator += Math.pow(i - xMean, 2);
            }

            if (denominator == 0) {
                throw new InsufficientDataException(
                        "Regression denominator is zero."
                );
            }

            double slope = numerator / denominator;
            double intercept = yMean - slope * xMean;

            return new double[]{intercept, slope};
        }
    }

    // ========================================================
    // DATA ACCESS AND VALIDATION
    // ========================================================

    static final class SalesRepository {

        private final List<SalesTransaction> transactions;

        SalesRepository(List<SalesTransaction> input) {
            if (input == null || input.isEmpty()) {
                throw new InsufficientDataException(
                        "Transaction collection cannot be empty."
                );
            }

            Set<Integer> ids = new HashSet<>();

            for (SalesTransaction transaction : input) {
                Objects.requireNonNull(transaction);

                if (!ids.add(transaction.transactionId())) {
                    throw new ValidationException(
                            "Duplicate transaction ID."
                    );
                }
            }

            this.transactions = List.copyOf(input);
        }

        List<SalesTransaction> findAll() {
            return transactions;
        }

        int size() {
            return transactions.size();
        }
    }

    // ========================================================
    // MEASUREMENT SERVICE
    // ========================================================

    static final class MeasurementService {

        BusinessMetrics calculate(
                SalesRepository repository
        ) {
            List<SalesTransaction> records = repository.findAll();

            double revenue = records.stream()
                    .mapToDouble(SalesTransaction::revenue)
                    .sum();

            double marketing = records.stream()
                    .mapToDouble(SalesTransaction::marketingSpend)
                    .sum();

            int units = records.stream()
                    .mapToInt(SalesTransaction::units)
                    .sum();

            return new BusinessMetrics(
                    records.size(),
                    revenue,
                    units,
                    revenue / records.size(),
                    marketing,
                    (revenue - marketing) / Math.max(marketing, 1)
            );
        }
    }

    // ========================================================
    // DECOMPOSITION SERVICE
    // ========================================================

    static final class DecompositionService {

        List<DecompositionNode> analyze(
                SalesRepository repository,
                List<Dimension> dimensions,
                int topN
        ) {

            Objects.requireNonNull(dimensions);

            if (dimensions.isEmpty() || topN < 1) {
                throw new ValidationException(
                        "Dimensions and positive topN are required."
                );
            }

            if (dimensions.stream().distinct().count()
                    != dimensions.size()) {

                throw new ValidationException(
                        "Duplicate dimensions are invalid."
                );
            }

            return build(
                    repository.findAll(),
                    dimensions,
                    0,
                    topN
            );
        }

        private List<DecompositionNode> build(
                List<SalesTransaction> records,
                List<Dimension> dimensions,
                int depth,
                int topN
        ) {

            if (depth >= dimensions.size()) {
                return List.of();
            }

            Dimension dimension = dimensions.get(depth);

            Map<String, List<SalesTransaction>> groups =
                    records.stream().collect(
                            Collectors.groupingBy(
                                    record -> record.dimensionValue(dimension),
                                    LinkedHashMap::new,
                                    Collectors.toList()
                            )
                    );

            double parentRevenue = records.stream()
                    .mapToDouble(SalesTransaction::revenue)
                    .sum();

            return groups.entrySet().stream()
                    .map(entry -> {

                        List<SalesTransaction> group =
                                entry.getValue();

                        double revenue = group.stream()
                                .mapToDouble(
                                        SalesTransaction::revenue
                                )
                                .sum();

                        double contribution = parentRevenue > 0
                                ? revenue / parentRevenue * 100
                                : 0;

                        return new DecompositionNode(
                                dimension,
                                entry.getKey(),
                                revenue,
                                group.size(),
                                contribution,
                                build(
                                        group,
                                        dimensions,
                                        depth + 1,
                                        topN
                                )
                        );
                    })
                    .sorted(
                            Comparator.comparingDouble(
                                    DecompositionNode::revenue
                            ).reversed()
                    )
                    .limit(topN)
                    .toList();
        }
    }

    // ========================================================
    // KEY INFLUENCER SERVICE
    // ========================================================

    static final class InfluencerService {

        List<InfluencerResult> analyze(
                SalesRepository repository,
                AnalyticalTarget target,
                int minimumGroupSize
        ) {

            if (minimumGroupSize < 2) {
                throw new ValidationException(
                        "Minimum group size must be at least two."
                );
            }

            List<SalesTransaction> records =
                    repository.findAll();

            List<Double> targetValues = records.stream()
                    .map(record -> record.targetValue(target))
                    .toList();

            double threshold = Statistics.median(targetValues);

            List<InfluencerResult> results = new ArrayList<>();

            for (Dimension dimension : Dimension.values()) {

                Map<String, List<SalesTransaction>> groups =
                        records.stream().collect(
                                Collectors.groupingBy(
                                        record -> record.dimensionValue(dimension)
                                )
                        );

                for (var entry : groups.entrySet()) {

                    String value = entry.getKey();
                    List<SalesTransaction> group = entry.getValue();

                    if (group.size() < minimumGroupSize) {
                        continue;
                    }

                    List<SalesTransaction> comparison =
                            records.stream()
                                    .filter(
                                            record -> !record
                                                    .dimensionValue(dimension)
                                                    .equals(value)
                                    )
                                    .toList();

                    if (comparison.isEmpty()) {
                        continue;
                    }

                    double targetRate = group.stream()
                            .filter(
                                    record -> record.targetValue(target)
                                            > threshold
                            )
                            .count() / (double) group.size();

                    double comparisonRate = comparison.stream()
                            .filter(
                                    record -> record.targetValue(target)
                                            > threshold
                            )
                            .count() / (double) comparison.size();

                    double difference =
                            targetRate - comparisonRate;

                    if (difference > 0) {
                        results.add(
                                new InfluencerResult(
                                        dimension,
                                        value,
                                        group.size(),
                                        comparison.size(),
                                        targetRate,
                                        comparisonRate,
                                        difference
                                )
                        );
                    }
                }
            }

            return results.stream()
                    .sorted(
                            Comparator.comparingDouble(
                                    InfluencerResult::difference
                            ).reversed()
                    )
                    .toList();
        }
    }

    // ========================================================
    // FORECASTING SERVICE
    // ========================================================

    static final class ForecastService {

        private final ForecastPolicy policy;

        ForecastService(ForecastPolicy policy) {
            this.policy = policy;
        }

        List<ForecastPoint> forecast(
                SalesRepository repository,
                int horizon
        ) {

            if (horizon < 1 ||
                    horizon > policy.maximumHorizon()) {

                throw new ValidationException(
                        "Forecast horizon violates policy."
                );
            }

            Map<YearMonth, Double> monthly = new java.util.TreeMap<>();

            for (SalesTransaction transaction :
                    repository.findAll()) {

                monthly.merge(
                        transaction.period(),
                        transaction.revenue(),
                        Double::sum
                );
            }

            if (monthly.size() < policy.minimumObservations()) {
                throw new InsufficientDataException(
                        "Insufficient monthly observations."
                );
            }

            List<Double> values = new ArrayList<>(
                    monthly.values()
            );

            double[] regression =
                    Statistics.linearRegression(values);

            double intercept = regression[0];
            double slope = regression[1];

            List<Double> residuals = new ArrayList<>();

            for (int i = 0; i < values.size(); i++) {
                residuals.add(
                        values.get(i) - (intercept + slope * i)
                );
            }

            double residualStd =
                    Statistics.standardDeviation(residuals);

            YearMonth lastPeriod = monthly.keySet().stream()
                    .max(YearMonth::compareTo)
                    .orElseThrow();

            List<ForecastPoint> results = new ArrayList<>();

            for (int step = 1; step <= horizon; step++) {

                int index = values.size() - 1 + step;

                double prediction = Math.max(
                        0,
                        intercept + slope * index
                );

                double uncertainty =
                        policy.confidenceMultiplier() *
                        residualStd *
                        Math.sqrt(1.0 + step / (double) values.size());

                results.add(
                        new ForecastPoint(
                                lastPeriod.plusMonths(step),
                                prediction,
                                Math.max(0, prediction - uncertainty),
                                prediction + uncertainty
                        )
                );
            }

            return List.copyOf(results);
        }
    }

    // ========================================================
    // ANOMALY DETECTION SERVICE
    // ========================================================

    static final class AnomalyService {

        private final AnomalyPolicy policy;

        AnomalyService(AnomalyPolicy policy) {
            this.policy = policy;
        }

        List<AnomalyResult> detect(
                SalesRepository repository
        ) {

            List<SalesTransaction> records =
                    repository.findAll();

            List<Double> values = records.stream()
                    .map(SalesTransaction::revenue)
                    .toList();

            double center = Statistics.median(values);

            List<Double> deviations = values.stream()
                    .map(value -> Math.abs(value - center))
                    .toList();

            double mad = Statistics.median(deviations);

            if (mad == 0) {
                throw new InsufficientDataException(
                        "MAD is zero; robust anomaly detection unavailable."
                );
            }

            return records.stream()
                    .map(record -> {

                        double score =
                                0.6745 *
                                (record.revenue() - center) / mad;

                        AnomalySeverity severity;

                        if (Math.abs(score) >=
                                policy.criticalThreshold()) {
                            severity = AnomalySeverity.CRITICAL;

                        } else if (Math.abs(score) >=
                                policy.threshold()) {
                            severity = AnomalySeverity.HIGH;

                        } else {
                            severity = AnomalySeverity.NORMAL;
                        }

                        return new AnomalyResult(
                                record.transactionId(),
                                record.revenue(),
                                center,
                                score,
                                severity
                        );
                    })
                    .filter(
                            result -> result.severity()
                                    != AnomalySeverity.NORMAL
                    )
                    .sorted(
                            Comparator.comparingDouble(
                                    (AnomalyResult result) ->
                                            Math.abs(result.score())
                            ).reversed()
                    )
                    .toList();
        }
    }

    // ========================================================
    // REPORT ORCHESTRATION
    // ========================================================

    static final class AnalyticsApplication {

        private final SalesRepository repository;
        private final MeasurementService measurementService;
        private final DecompositionService decompositionService;
        private final InfluencerService influencerService;
        private final ForecastService forecastService;
        private final AnomalyService anomalyService;

        AnalyticsApplication(List<SalesTransaction> records) {
            repository = new SalesRepository(records);

            measurementService = new MeasurementService();
            decompositionService = new DecompositionService();
            influencerService = new InfluencerService();

            forecastService = new ForecastService(
                    new ForecastPolicy(6, 36, 1.96)
            );

            anomalyService = new AnomalyService(
                    new AnomalyPolicy(3.5, 7.0)
            );
        }

        void execute() {

            System.out.println("\n1. BUSINESS METRICS");

            System.out.println(
                    measurementService.calculate(repository)
            );

            System.out.println("\n2. DECOMPOSITION TREE");

            List<DecompositionNode> tree =
                    decompositionService.analyze(
                            repository,
                            List.of(
                                    Dimension.REGION,
                                    Dimension.PRODUCT,
                                    Dimension.CHANNEL
                            ),
                            3
                    );

            tree.forEach(System.out::println);

            System.out.println("\n3. KEY INFLUENCERS");

            influencerService.analyze(
                    repository,
                    AnalyticalTarget.HIGH_REVENUE,
                    10
            ).stream()
                    .limit(10)
                    .forEach(System.out::println);

            System.out.println("\n4. REVENUE FORECAST");

            forecastService.forecast(repository, 3)
                    .forEach(System.out::println);

            System.out.println("\n5. ANOMALY DETECTION");

            anomalyService.detect(repository)
                    .stream()
                    .limit(10)
                    .forEach(System.out::println);

            System.out.println("\n6. VALIDATION");

            if (repository.size() != 600) {
                throw new ValidationException(
                        "Unexpected record count."
                );
            }

            if (forecastService.forecast(repository, 3).size() != 3) {
                throw new ValidationException(
                        "Forecast validation failed."
                );
            }

            System.out.println(
                    "Enterprise analytical validations passed."
            );
        }
    }

    // ========================================================
    // SAMPLE DATA GENERATION
    // ========================================================

    static List<SalesTransaction> generateData(
            int count,
            long seed
    ) {

        if (count < 30) {
            throw new ValidationException(
                    "At least 30 records are required."
            );
        }

        java.util.Random random = new java.util.Random(seed);

        List<String> regions = List.of(
                "North", "South", "East", "West"
        );

        List<String> products = List.of(
                "Laptop", "Mobile", "Tablet", "Monitor"
        );

        List<String> segments = List.of(
                "Consumer", "Corporate", "Small Business"
        );

        List<String> channels = List.of(
                "Online", "Retail", "Partner"
        );

        Map<String, Double> prices = Map.of(
                "Laptop", 850.0,
                "Mobile", 420.0,
                "Tablet", 300.0,
                "Monitor", 260.0
        );

        Map<String, Double> regionFactors = Map.of(
                "North", 1.15,
                "South", 1.05,
                "East", 0.90,
                "West", 1.10
        );

        Map<String, Double> segmentFactors = Map.of(
                "Consumer", 1.0,
                "Corporate", 1.30,
                "Small Business", 1.10
        );

        List<SalesTransaction> records = new ArrayList<>();

        YearMonth startingPeriod = YearMonth.of(2025, 1);

        for (int i = 0; i < count; i++) {

            String region = regions.get(random.nextInt(4));
            String product = products.get(random.nextInt(4));
            String segment = segments.get(random.nextInt(3));
            String channel = channels.get(random.nextInt(3));

            int units = 1 + random.nextInt(12);

            double discount = random.nextDouble() * 20;

            double revenue =
                    prices.get(product) *
                    units *
                    regionFactors.get(region) *
                    segmentFactors.get(segment) *
                    (1 - discount / 100.0);

            revenue = Math.max(
                    0,
                    revenue + random.nextGaussian() * 90
            );

            if (Set.of(75, 190, 330, 470).contains(i)) {
                revenue *= 3.5;
            }

            double marketing = 50 + random.nextDouble() * 550;

            double satisfaction = Math.min(
                    10,
                    Math.max(
                            0,
                            7.5 + random.nextGaussian() * 1.1
                    )
            );

            records.add(
                    new SalesTransaction(
                            i + 1,
                            startingPeriod.plusMonths(
                                    (i % 365) / 30
                            ),
                            region,
                            product,
                            segment,
                            channel,
                            Math.round(revenue * 100) / 100.0,
                            units,
                            Math.round(marketing * 100) / 100.0,
                            Math.round(discount * 100) / 100.0,
                            Math.round(satisfaction * 100) / 100.0
                    )
            );
        }

        return records;
    }

    // ========================================================
    // MAIN
    // ========================================================

    public static void main(String[] args) {

        try {
            System.out.println(
                    "POWER BI ADVANCED ANALYTICS"
            );

            System.out.println(
                    "Report ID: " + UUID.randomUUID()
            );

            AnalyticsApplication application =
                    new AnalyticsApplication(
                            generateData(600, 42)
                    );

            application.execute();

        } catch (AnalyticsException exception) {
            System.err.println(
                    "ANALYTICS ERROR: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
