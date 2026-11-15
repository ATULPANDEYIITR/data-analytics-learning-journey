import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;

/*
 * Statistical Analysis Project
 *
 * Java 17 enterprise-oriented implementation.
 *
 * Features:
 * - Immutable domain records
 * - Dataset validation
 * - Descriptive statistics
 * - Pearson correlation
 * - Linear regression
 * - Bootstrap confidence intervals
 * - Permutation hypothesis testing
 * - Analysis services
 * - Structured reporting
 */

public class StatisticalAnalysis {

    private static final double ALPHA = 0.05;

    enum Decision {
        REJECT_NULL,
        FAIL_TO_REJECT_NULL
    }

    record Observation(
        int participantId,
        double studyHours,
        double examScore
    ) {
        Observation {
            if (participantId <= 0) {
                throw new IllegalArgumentException(
                    "Participant ID must be positive."
                );
            }

            if (!Double.isFinite(studyHours) || studyHours < 0) {
                throw new IllegalArgumentException(
                    "Study hours must be finite and non-negative."
                );
            }

            if (
                !Double.isFinite(examScore)
                || examScore < 0
                || examScore > 100
            ) {
                throw new IllegalArgumentException(
                    "Exam score must be between 0 and 100."
                );
            }
        }
    }

    record DescriptiveStatistics(
        int count,
        double mean,
        double standardDeviation,
        double minimum,
        double maximum
    ) {}

    record ConfidenceInterval(
        double lower,
        double upper,
        double confidenceLevel
    ) {
        ConfidenceInterval {
            if (
                !Double.isFinite(lower)
                || !Double.isFinite(upper)
                || lower > upper
                || confidenceLevel <= 0
                || confidenceLevel >= 1
            ) {
                throw new IllegalArgumentException(
                    "Invalid confidence interval."
                );
            }
        }
    }

    record RegressionResult(
        double slope,
        double intercept,
        double rSquared,
        double rmse,
        double mae
    ) {}

    record HypothesisResult(
        String nullHypothesis,
        String alternativeHypothesis,
        double significanceLevel,
        double pValue,
        Decision decision
    ) {}

    record AnalysisReport(
        int sampleSize,
        DescriptiveStatistics studyHours,
        DescriptiveStatistics examScores,
        double correlation,
        ConfidenceInterval correlationCI,
        ConfidenceInterval slopeCI,
        RegressionResult regression,
        HypothesisResult hypothesis
    ) {}

    static class StatisticalException extends RuntimeException {
        StatisticalException(String message) {
            super(message);
        }
    }

    interface StatisticalTest {
        double evaluate(
            List<Double> first,
            List<Double> second
        );
    }

    static class DatasetRepository {
        private final List<Observation> records;

        DatasetRepository(List<Observation> records) {
            if (records == null || records.size() < 4) {
                throw new IllegalArgumentException(
                    "At least four observations are required."
                );
            }

            Set<Integer> identifiers = new HashSet<>();

            for (Observation record : records) {
                if (!identifiers.add(record.participantId())) {
                    throw new IllegalArgumentException(
                        "Duplicate participant ID."
                    );
                }
            }

            this.records = List.copyOf(records);
        }

        List<Observation> getRecords() {
            return records;
        }

        List<Double> studyHours() {
            return records.stream()
                .map(Observation::studyHours)
                .toList();
        }

        List<Double> examScores() {
            return records.stream()
                .map(Observation::examScore)
                .toList();
        }
    }

    static class StatisticalMath {

        static double mean(List<Double> values) {
            if (values.isEmpty()) {
                throw new StatisticalException("Empty sample.");
            }

            return values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();
        }

        static double standardDeviation(List<Double> values) {
            if (values.size() < 2) {
                throw new StatisticalException(
                    "At least two observations are required."
                );
            }

            double center = mean(values);

            double squaredSum = values.stream()
                .mapToDouble(value -> Math.pow(value - center, 2))
                .sum();

            return Math.sqrt(squaredSum / (values.size() - 1));
        }

        static double pearson(
            List<Double> x,
            List<Double> y
        ) {
            if (x.size() != y.size() || x.size() < 3) {
                throw new StatisticalException(
                    "Invalid correlation sample."
                );
            }

            double mx = mean(x);
            double my = mean(y);

            double numerator = 0;
            double sx = 0;
            double sy = 0;

            for (int i = 0; i < x.size(); i++) {
                double dx = x.get(i) - mx;
                double dy = y.get(i) - my;

                numerator += dx * dy;
                sx += dx * dx;
                sy += dy * dy;
            }

            double denominator = Math.sqrt(sx * sy);

            if (denominator == 0) {
                throw new StatisticalException(
                    "Correlation is undefined."
                );
            }

            return numerator / denominator;
        }

        static RegressionResult regression(
            List<Double> x,
            List<Double> y
        ) {
            if (x.size() != y.size() || x.size() < 3) {
                throw new StatisticalException(
                    "Invalid regression sample."
                );
            }

            double mx = mean(x);
            double my = mean(y);

            double numerator = 0;
            double denominator = 0;

            for (int i = 0; i < x.size(); i++) {
                numerator += (x.get(i) - mx) * (y.get(i) - my);
                denominator += Math.pow(x.get(i) - mx, 2);
            }

            if (denominator == 0) {
                throw new StatisticalException(
                    "Regression slope is undefined."
                );
            }

            double slope = numerator / denominator;
            double intercept = my - slope * mx;

            double residualSum = 0;
            double totalSum = 0;
            double absoluteError = 0;

            for (int i = 0; i < x.size(); i++) {
                double prediction = intercept + slope * x.get(i);
                double residual = y.get(i) - prediction;

                residualSum += residual * residual;
                totalSum += Math.pow(y.get(i) - my, 2);
                absoluteError += Math.abs(residual);
            }

            return new RegressionResult(
                slope,
                intercept,
                1 - residualSum / totalSum,
                Math.sqrt(residualSum / x.size()),
                absoluteError / x.size()
            );
        }

        static double percentile(
            List<Double> values,
            double probability
        ) {
            if (
                values.isEmpty()
                || probability < 0
                || probability > 1
            ) {
                throw new StatisticalException(
                    "Invalid percentile request."
                );
            }

            List<Double> sorted = new ArrayList<>(values);
            Collections.sort(sorted);

            double position = probability * (sorted.size() - 1);

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            double fraction = position - lower;

            return sorted.get(lower) * (1 - fraction)
                + sorted.get(upper) * fraction;
        }
    }

    static class InferenceService {

        private final Random random;

        InferenceService(long seed) {
            this.random = new Random(seed);
        }

        ConfidenceInterval bootstrap(
            DatasetRepository repository,
            StatisticalTest statistic,
            int iterations,
            double confidence
        ) {
            if (iterations < 1000 || confidence <= 0 || confidence >= 1) {
                throw new IllegalArgumentException(
                    "Invalid bootstrap configuration."
                );
            }

            List<Double> x = repository.studyHours();
            List<Double> y = repository.examScores();

            List<Double> estimates = new ArrayList<>();
            int n = x.size();

            for (int iteration = 0; iteration < iterations; iteration++) {
                List<Double> sampleX = new ArrayList<>();
                List<Double> sampleY = new ArrayList<>();

                // Preserve the paired structure of each observation.
                for (int i = 0; i < n; i++) {
                    int index = random.nextInt(n);

                    sampleX.add(x.get(index));
                    sampleY.add(y.get(index));
                }

                try {
                    estimates.add(statistic.evaluate(sampleX, sampleY));
                } catch (StatisticalException ignored) {
                    // Degenerate resamples are excluded.
                }
            }

            if (estimates.size() < iterations * 0.95) {
                throw new StatisticalException(
                    "Too many invalid bootstrap samples."
                );
            }

            double tail = (1 - confidence) / 2;

            return new ConfidenceInterval(
                StatisticalMath.percentile(estimates, tail),
                StatisticalMath.percentile(estimates, 1 - tail),
                confidence
            );
        }

        double permutationTest(
            DatasetRepository repository,
            int iterations
        ) {
            if (iterations < 1000) {
                throw new IllegalArgumentException(
                    "At least 1000 permutations are required."
                );
            }

            List<Double> x = repository.studyHours();
            List<Double> y = repository.examScores();

            double observed = Math.abs(
                StatisticalMath.pearson(x, y)
            );

            int extreme = 0;

            for (int iteration = 0; iteration < iterations; iteration++) {
                List<Double> randomized = new ArrayList<>(y);
                Collections.shuffle(randomized, random);

                double simulated = Math.abs(
                    StatisticalMath.pearson(x, randomized)
                );

                if (simulated >= observed) {
                    extreme++;
                }
            }

            return (extreme + 1.0) / (iterations + 1.0);
        }
    }

    static class AnalysisService {

        private final DatasetRepository repository;
        private final InferenceService inference;

        AnalysisService(DatasetRepository repository) {
            this.repository = repository;
            this.inference = new InferenceService(42);
        }

        private DescriptiveStatistics describe(
            List<Double> values
        ) {
            return new DescriptiveStatistics(
                values.size(),
                StatisticalMath.mean(values),
                StatisticalMath.standardDeviation(values),
                values.stream().mapToDouble(Double::doubleValue).min()
                    .orElseThrow(),
                values.stream().mapToDouble(Double::doubleValue).max()
                    .orElseThrow()
            );
        }

        AnalysisReport execute() {
            List<Double> x = repository.studyHours();
            List<Double> y = repository.examScores();

            double correlation = StatisticalMath.pearson(x, y);

            RegressionResult regression =
                StatisticalMath.regression(x, y);

            ConfidenceInterval correlationCI =
                inference.bootstrap(
                    repository,
                    StatisticalMath::pearson,
                    5000,
                    0.95
                );

            ConfidenceInterval slopeCI =
                inference.bootstrap(
                    repository,
                    (a, b) -> StatisticalMath.regression(a, b).slope(),
                    5000,
                    0.95
                );

            double pValue = inference.permutationTest(
                repository,
                10000
            );

            Decision decision = pValue < ALPHA
                ? Decision.REJECT_NULL
                : Decision.FAIL_TO_REJECT_NULL;

            HypothesisResult hypothesis = new HypothesisResult(
                "Population correlation equals zero.",
                "Population correlation differs from zero.",
                ALPHA,
                pValue,
                decision
            );

            return new AnalysisReport(
                repository.getRecords().size(),
                describe(x),
                describe(y),
                correlation,
                correlationCI,
                slopeCI,
                regression,
                hypothesis
            );
        }
    }

    static class ReportService {

        void print(AnalysisReport report) {
            System.out.println(
                "\n======================================"
            );

            System.out.println("STATISTICAL ANALYSIS REPORT");

            System.out.println(
                "======================================"
            );

            System.out.println("Sample size: " + report.sampleSize());

            System.out.println(
                "\nStudy hours: " + report.studyHours()
            );

            System.out.println(
                "Exam scores: " + report.examScores()
            );

            System.out.println(
                "\nPearson correlation: " + report.correlation()
            );

            System.out.println(
                "Correlation CI: " + report.correlationCI()
            );

            System.out.println(
                "Slope CI: " + report.slopeCI()
            );

            System.out.println(
                "\nRegression: " + report.regression()
            );

            System.out.println(
                "\nHypothesis test: " + report.hypothesis()
            );

            System.out.println(
                "\nInterpretation: Correlation does not establish causation."
            );
        }

        void save(AnalysisReport report) throws IOException {
            String content = """
                STATISTICAL ANALYSIS REPORT
                Sample size: %d
                Correlation: %.8f
                Correlation confidence interval: %.8f, %.8f
                Regression slope: %.8f
                Slope confidence interval: %.8f, %.8f
                R-squared: %.8f
                Permutation p-value: %.8f
                Decision: %s
                """.formatted(
                    report.sampleSize(),
                    report.correlation(),
                    report.correlationCI().lower(),
                    report.correlationCI().upper(),
                    report.regression().slope(),
                    report.slopeCI().lower(),
                    report.slopeCI().upper(),
                    report.regression().rSquared(),
                    report.hypothesis().pValue(),
                    report.hypothesis().decision()
                );

            Path destination = Path.of(
                "statistical_analysis_report.txt"
            );

            Path temporary = Path.of(
                "statistical_analysis_report.txt.tmp"
            );

            Files.writeString(
                temporary,
                content,
                StandardCharsets.UTF_8
            );

            try {
                Files.move(
                    temporary,
                    destination,
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING
                );
            } catch (IOException error) {
                Files.deleteIfExists(temporary);
                throw error;
            }
        }
    }

    private static List<Observation> sampleData() {
        return List.of(
            new Observation(1, 1.0, 48),
            new Observation(2, 1.5, 52),
            new Observation(3, 2.0, 55),
            new Observation(4, 2.5, 58),
            new Observation(5, 3.0, 62),
            new Observation(6, 3.5, 65),
            new Observation(7, 4.0, 68),
            new Observation(8, 4.5, 70),
            new Observation(9, 5.0, 74),
            new Observation(10, 5.5, 77),
            new Observation(11, 6.0, 80),
            new Observation(12, 7.0, 86)
        );
    }

    public static void main(String[] args) {
        try {
            DatasetRepository repository =
                new DatasetRepository(sampleData());

            AnalysisService service =
                new AnalysisService(repository);

            AnalysisReport report = service.execute();

            ReportService reporting = new ReportService();

            reporting.print(report);
            reporting.save(report);

            System.out.println(
                "\nReport saved successfully."
            );

        } catch (Exception error) {
            System.err.println(
                "Analysis failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
