import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/*
 * Java 17 Enterprise-Style Exploratory Data Analysis.
 *
 * Dataset: UCI Iris.
 * Default: local iris.csv or embedded genuine subset.
 *
 * Features:
 * - Immutable domain records
 * - Explicit validation and exception handling
 * - Dataset ingestion service
 * - Group-based statistical analysis
 * - IQR outlier detection
 * - Pearson correlation
 * - Analytical report generation
 * - Cleaned CSV export
 */

public class IrisEDA {

    private static final List<String> FEATURES = List.of(
        "sepal_length",
        "sepal_width",
        "petal_length",
        "petal_width"
    );

    private static final String SAMPLE_DATA = """
        5.1,3.5,1.4,0.2,setosa
        4.9,3.0,1.4,0.2,setosa
        4.7,3.2,1.3,0.2,setosa
        4.6,3.1,1.5,0.2,setosa
        5.0,3.6,1.4,0.2,setosa
        7.0,3.2,4.7,1.4,versicolor
        6.4,3.2,4.5,1.5,versicolor
        6.9,3.1,4.9,1.5,versicolor
        5.5,2.3,4.0,1.3,versicolor
        6.5,2.8,4.6,1.5,versicolor
        6.3,3.3,6.0,2.5,virginica
        5.8,2.7,5.1,1.9,virginica
        7.1,3.0,5.9,2.1,virginica
        6.3,2.9,5.6,1.8,virginica
        6.5,3.0,5.8,2.2,virginica
        """;

    enum Species {
        SETOSA,
        VERSICOLOR,
        VIRGINICA;

        static Species parse(String input)
                throws DataValidationException {

            String normalized = input
                .trim()
                .toLowerCase(Locale.ROOT)
                .replace("iris-", "")
                .replace(" ", "");

            if (normalized.equals("versicolour")) {
                normalized = "versicolor";
            }

            return switch (normalized) {
                case "setosa" -> SETOSA;
                case "versicolor" -> VERSICOLOR;
                case "virginica" -> VIRGINICA;
                default -> throw new DataValidationException(
                    "Unknown species: " + input
                );
            };
        }
    }

    static class DataValidationException
            extends Exception {

        DataValidationException(String message) {
            super(message);
        }

        DataValidationException(
            String message,
            Throwable cause
        ) {
            super(message, cause);
        }
    }

    record Flower(
        double sepalLength,
        double sepalWidth,
        double petalLength,
        double petalWidth,
        Species species
    ) {

        Flower {
            Objects.requireNonNull(species);

            double[] values = {
                sepalLength,
                sepalWidth,
                petalLength,
                petalWidth
            };

            for (double value : values) {
                if (
                    !Double.isFinite(value) ||
                    value <= 0 ||
                    value >= 10
                ) {
                    throw new IllegalArgumentException(
                        "Invalid flower measurement: " + value
                    );
                }
            }
        }

        double feature(int index) {
            return switch (index) {
                case 0 -> sepalLength;
                case 1 -> sepalWidth;
                case 2 -> petalLength;
                case 3 -> petalWidth;
                default -> throw new IndexOutOfBoundsException(
                    "Unknown feature index: " + index
                );
            };
        }
    }

    record Dataset(
        List<Flower> observations,
        List<String> rejectedRows,
        String source
    ) {
        Dataset {
            observations = List.copyOf(observations);
            rejectedRows = List.copyOf(rejectedRows);

            if (observations.isEmpty()) {
                throw new IllegalArgumentException(
                    "Dataset cannot be empty."
                );
            }
        }
    }

    record Statistics(
        double minimum,
        double q1,
        double median,
        double mean,
        double q3,
        double maximum,
        double standardDeviation,
        long outlierCount
    ) {}

    record CorrelationResult(
        List<String> features,
        double[][] values
    ) {
        CorrelationResult {
            features = List.copyOf(features);

            double[][] copy = new double[values.length][];

            for (int i = 0; i < values.length; i++) {
                copy[i] = values[i].clone();
            }

            values = copy;
        }
    }

    static final class DatasetLoader {

        Dataset load(Path inputPath)
                throws IOException, DataValidationException {

            String content;
            String source;

            if (Files.exists(inputPath)) {
                content = Files.readString(
                    inputPath,
                    StandardCharsets.UTF_8
                );

                source = "Local CSV: " + inputPath;

            } else {
                content = SAMPLE_DATA;
                source = "Embedded genuine Iris observation subset";
            }

            return parse(content, source);
        }

        Dataset parse(
            String content,
            String source
        ) throws DataValidationException {

            List<Flower> accepted = new ArrayList<>();
            List<String> rejected = new ArrayList<>();
            Set<Flower> seen = new java.util.HashSet<>();

            AtomicInteger lineNumber = new AtomicInteger();

            try (
                BufferedReader reader = new BufferedReader(
                    new StringReader(content)
                )
            ) {

                String line;

                while ((line = reader.readLine()) != null) {
                    int currentLine = lineNumber.incrementAndGet();

                    line = line.trim();

                    if (line.isEmpty()) {
                        continue;
                    }

                    if (
                        line.toLowerCase(Locale.ROOT)
                            .startsWith("sepal_length,") ||
                        line.startsWith("SepalLengthCm,")
                    ) {
                        continue;
                    }

                    try {
                        Flower flower = parseRow(line);

                        if (!seen.add(flower)) {
                            rejected.add(
                                "Line " + currentLine +
                                ": duplicate observation."
                            );
                        }

                        accepted.add(flower);

                    } catch (
                        DataValidationException |
                        IllegalArgumentException exception
                    ) {
                        rejected.add(
                            "Line " + currentLine +
                            ": " + exception.getMessage()
                        );
                    }
                }

            } catch (IOException exception) {
                throw new DataValidationException(
                    "Could not read dataset content.",
                    exception
                );
            }

            if (accepted.isEmpty()) {
                throw new DataValidationException(
                    "No valid observations were loaded."
                );
            }

            return new Dataset(
                accepted,
                rejected,
                source
            );
        }

        private Flower parseRow(String line)
                throws DataValidationException {

            String[] fields = line.split(",", -1);

            if (fields.length != 5) {
                throw new DataValidationException(
                    "Expected five columns."
                );
            }

            double[] measurements = new double[4];

            for (int index = 0; index < 4; index++) {
                try {
                    measurements[index] = Double.parseDouble(
                        fields[index].trim()
                    );
                } catch (NumberFormatException exception) {
                    throw new DataValidationException(
                        "Invalid numerical measurement.",
                        exception
                    );
                }
            }

            Species species = Species.parse(fields[4]);

            try {
                return new Flower(
                    measurements[0],
                    measurements[1],
                    measurements[2],
                    measurements[3],
                    species
                );
            } catch (IllegalArgumentException exception) {
                throw new DataValidationException(
                    exception.getMessage(),
                    exception
                );
            }
        }
    }

    static final class DescriptiveStatisticsService {

        private double mean(double[] values) {
            if (values.length == 0) {
                throw new IllegalArgumentException(
                    "Empty measurement array."
                );
            }

            return Arrays.stream(values)
                .average()
                .orElseThrow();
        }

        private double quantile(
            double[] input,
            double probability
        ) {
            if (
                input.length == 0 ||
                probability < 0 ||
                probability > 1
            ) {
                throw new IllegalArgumentException(
                    "Invalid quantile arguments."
                );
            }

            double[] values = input.clone();
            Arrays.sort(values);

            double position =
                (values.length - 1) * probability;

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            if (lower == upper) {
                return values[lower];
            }

            double fraction = position - lower;

            return values[lower] * (1 - fraction)
                + values[upper] * fraction;
        }

        private double sampleStandardDeviation(
            double[] values
        ) {
            if (values.length < 2) {
                return 0;
            }

            double average = mean(values);

            double sum = Arrays.stream(values)
                .map(value -> Math.pow(value - average, 2))
                .sum();

            return Math.sqrt(sum / (values.length - 1));
        }

        Statistics analyze(double[] values) {
            double q1 = quantile(values, 0.25);
            double q3 = quantile(values, 0.75);

            double iqr = q3 - q1;

            double lower = q1 - 1.5 * iqr;
            double upper = q3 + 1.5 * iqr;

            long outliers = Arrays.stream(values)
                .filter(value ->
                    value < lower || value > upper
                )
                .count();

            return new Statistics(
                Arrays.stream(values).min().orElseThrow(),
                q1,
                quantile(values, 0.5),
                mean(values),
                q3,
                Arrays.stream(values).max().orElseThrow(),
                sampleStandardDeviation(values),
                outliers
            );
        }
    }

    static final class GroupAnalysisService {

        Map<Species, List<Flower>> group(
            List<Flower> observations
        ) {
            return observations.stream()
                .collect(Collectors.groupingBy(
                    Flower::species,
                    () -> new EnumMap<>(Species.class),
                    Collectors.toList()
                ));
        }

        Map<Species, Long> distribution(
            List<Flower> observations
        ) {
            Map<Species, Long> result =
                new EnumMap<>(Species.class);

            for (Species species : Species.values()) {
                result.put(species, 0L);
            }

            observations.stream()
                .collect(Collectors.groupingBy(
                    Flower::species,
                    Collectors.counting()
                ))
                .forEach(result::put);

            return result;
        }

        Map<Species, List<Double>> featureMeans(
            List<Flower> observations
        ) {
            Map<Species, List<Double>> result =
                new EnumMap<>(Species.class);

            for (Map.Entry<Species, List<Flower>> entry :
                    group(observations).entrySet()) {

                List<Double> means = new ArrayList<>();

                for (int feature = 0; feature < 4; feature++) {
                    final int current = feature;

                    double average = entry.getValue()
                        .stream()
                        .mapToDouble(
                            flower -> flower.feature(current)
                        )
                        .average()
                        .orElseThrow();

                    means.add(average);
                }

                result.put(
                    entry.getKey(),
                    List.copyOf(means)
                );
            }

            return result;
        }
    }

    static final class CorrelationService {

        double calculate(double[] first, double[] second) {
            if (
                first.length != second.length ||
                first.length < 2
            ) {
                return Double.NaN;
            }

            double meanFirst = Arrays.stream(first)
                .average()
                .orElseThrow();

            double meanSecond = Arrays.stream(second)
                .average()
                .orElseThrow();

            double numerator = 0;
            double firstSum = 0;
            double secondSum = 0;

            for (int index = 0; index < first.length; index++) {
                double x = first[index] - meanFirst;
                double y = second[index] - meanSecond;

                numerator += x * y;
                firstSum += x * x;
                secondSum += y * y;
            }

            double denominator =
                Math.sqrt(firstSum * secondSum);

            return denominator == 0
                ? Double.NaN
                : numerator / denominator;
        }

        CorrelationResult matrix(
            List<Flower> observations
        ) {
            double[][] values = new double[4][4];

            for (int row = 0; row < 4; row++) {
                for (int column = 0; column < 4; column++) {
                    final int first = row;
                    final int second = column;

                    double[] firstValues = observations.stream()
                        .mapToDouble(
                            flower -> flower.feature(first)
                        )
                        .toArray();

                    double[] secondValues = observations.stream()
                        .mapToDouble(
                            flower -> flower.feature(second)
                        )
                        .toArray();

                    values[row][column] = calculate(
                        firstValues,
                        secondValues
                    );
                }
            }

            return new CorrelationResult(
                FEATURES,
                values
            );
        }
    }

    static final class AnalyticalReportService {

        private final DescriptiveStatisticsService statistics;
        private final GroupAnalysisService groups;
        private final CorrelationService correlations;

        AnalyticalReportService() {
            statistics = new DescriptiveStatisticsService();
            groups = new GroupAnalysisService();
            correlations = new CorrelationService();
        }

        String generate(Dataset dataset) {

            List<Flower> observations = dataset.observations();

            Map<Species, Long> distribution =
                groups.distribution(observations);

            Map<Species, List<Double>> speciesMeans =
                groups.featureMeans(observations);

            Map<Species, List<Flower>> speciesGroups =
                groups.group(observations);

            CorrelationResult matrix =
                correlations.matrix(observations);

            long duplicateCount = observations.stream()
                .distinct()
                .count();

            StringBuilder report = new StringBuilder();

            report.append("# Exploratory Data Analysis: Iris Dataset\n\n");

            report.append("Generated: ")
                .append(java.time.Instant.now())
                .append("\n\n");

            report.append("## 1. Dataset Overview\n\n");
            report.append("- Source: ")
                .append(dataset.source())
                .append("\n");
            report.append("- Valid observations: ")
                .append(observations.size())
                .append("\n");
            report.append("- Numerical features: 4\n");
            report.append("- Categorical target: species\n");
            report.append("- Measurement unit: centimetres\n\n");

            report.append("## 2. Data Quality\n\n");
            report.append("| Metric | Value |\n");
            report.append("|---|---:|\n");
            report.append("| Accepted observations | ")
                .append(observations.size())
                .append(" |\n");
            report.append("| Rejected records | ")
                .append(dataset.rejectedRows().size())
                .append(" |\n");
            report.append("| Missing values in accepted records | 0 |\n");
            report.append("| Duplicate observations | ")
                .append(observations.size() - duplicateCount)
                .append(" |\n\n");

            report.append("## 3. Species Distribution\n\n");
            report.append("| Species | Count | Percentage |\n");
            report.append("|---|---:|---:|\n");

            distribution.forEach((species, count) -> {
                double percentage =
                    100.0 * count / observations.size();

                report.append("| ")
                    .append(species)
                    .append(" | ")
                    .append(count)
                    .append(" | ")
                    .append(String.format(
                        Locale.ROOT,
                        "%.2f%%",
                        percentage
                    ))
                    .append(" |\n");
            });

            report.append("\n## 4. Descriptive Statistics\n\n");

            report.append(
                "| Feature | Min | Q1 | Median | Mean | Q3 | Max | SD | Outliers |\n"
            );

            report.append(
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
            );

            for (int index = 0; index < 4; index++) {
                final int current = index;

                double[] values = observations.stream()
                    .mapToDouble(
                        flower -> flower.feature(current)
                    )
                    .toArray();

                Statistics result = statistics.analyze(values);

                report.append("| ")
                    .append(FEATURES.get(index));

                report.append(String.format(
                    Locale.ROOT,
                    " | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %d |\n",
                    result.minimum(),
                    result.q1(),
                    result.median(),
                    result.mean(),
                    result.q3(),
                    result.maximum(),
                    result.standardDeviation(),
                    result.outlierCount()
                ));
            }

            report.append("\n## 5. Species-Level Feature Means\n\n");

            report.append(
                "| Species | Sepal length | Sepal width | Petal length | Petal width |\n"
            );

            report.append("|---|---:|---:|---:|---:|\n");

            speciesMeans.forEach((species, values) -> {
                report.append("| ").append(species);

                for (double value : values) {
                    report.append(String.format(
                        Locale.ROOT,
                        " | %.3f",
                        value
                    ));
                }

                report.append(" |\n");
            });

            report.append("\n## 6. Pearson Correlation Matrix\n\n");

            report.append("| Feature | ")
                .append(String.join(" | ", FEATURES))
                .append(" |\n");

            report.append(
                "|" + "---|".repeat(FEATURES.size() + 1) + "\n"
            );

            for (int row = 0; row < 4; row++) {
                report.append("| ").append(FEATURES.get(row));

                for (int column = 0; column < 4; column++) {
                    double value = matrix.values()[row][column];

                    report.append(" | ");

                    if (Double.isFinite(value)) {
                        report.append(String.format(
                            Locale.ROOT,
                            "%.4f",
                            value
                        ));
                    } else {
                        report.append("N/A");
                    }
                }

                report.append(" |\n");
            }

            double petalCorrelation = matrix.values()[2][3];

            report.append("\n## 7. Analytical Findings\n\n");

            report.append("- Petal length and petal width correlation: ")
                .append(String.format(
                    Locale.ROOT,
                    "%.4f",
                    petalCorrelation
                ))
                .append(".\n");

            Map.Entry<Species, List<Double>> largest =
                speciesMeans.entrySet()
                    .stream()
                    .max((a, b) ->
                        Double.compare(a.getValue().get(2),
                                       b.getValue().get(2))
                    )
                    .orElseThrow();

            Map.Entry<Species, List<Double>> smallest =
                speciesMeans.entrySet()
                    .stream()
                    .min((a, b) ->
                        Double.compare(a.getValue().get(2),
                                       b.getValue().get(2))
                    )
                    .orElseThrow();

            report.append("- Highest mean petal length: ")
                .append(largest.getKey())
                .append(" (")
                .append(String.format(
                    Locale.ROOT,
                    "%.3f cm",
                    largest.getValue().get(2)
                ))
                .append(").\n");

            report.append("- Lowest mean petal length: ")
                .append(smallest.getKey())
                .append(" (")
                .append(String.format(
                    Locale.ROOT,
                    "%.3f cm",
                    smallest.getValue().get(2)
                ))
                .append(").\n");

            report.append(
                "- Outliers are detected using the 1.5 × IQR rule.\n"
            );

            report.append(
                "- Outlier detection does not automatically remove observations.\n"
            );

            report.append(
                "- Pearson correlation does not establish causality.\n"
            );

            report.append("\n## 8. Limitations\n\n");
            report.append(
                "- The complete dataset contains 150 observations.\n"
            );

            report.append(
                "- It has three predefined species categories.\n"
            );

            report.append(
                "- The dataset has limited biological coverage.\n"
            );

            report.append(
                "- The embedded fallback is only a genuine subset.\n"
            );

            report.append("\n## 9. Provenance\n\n");

            report.append(
                "Fisher, R. A. (1936). The Use of Multiple Measurements in Taxonomic Problems.\n\n"
            );

            report.append(
                "UCI Machine Learning Repository: Iris Dataset.\n\n"
            );

            report.append(
                "https://doi.org/10.24432/C56C76\n\n"
            );

            report.append("License: CC BY 4.0.\n");

            return report.toString();
        }
    }

    static final class ReportExporter {

        void export(
            Dataset dataset,
            Path outputDirectory,
            String report
        ) throws IOException {

            Files.createDirectories(outputDirectory);

            Path reportPath =
                outputDirectory.resolve("analytical_report.md");

            Path cleanedPath =
                outputDirectory.resolve("iris_cleaned.csv");

            try (
                BufferedWriter writer = Files.newBufferedWriter(
                    reportPath,
                    StandardCharsets.UTF_8
                )
            ) {
                writer.write(report);
            }

            try (
                BufferedWriter writer = Files.newBufferedWriter(
                    cleanedPath,
                    StandardCharsets.UTF_8
                )
            ) {

                writer.write(
                    "sepal_length,sepal_width,petal_length,petal_width,species\n"
                );

                for (Flower flower : dataset.observations()) {
                    writer.write(String.format(
                        Locale.ROOT,
                        "%.2f,%.2f,%.2f,%.2f,%s%n",
                        flower.sepalLength(),
                        flower.sepalWidth(),
                        flower.petalLength(),
                        flower.petalWidth(),
                        flower.species().name().toLowerCase(Locale.ROOT)
                    ));
                }
            }

            if (!dataset.rejectedRows().isEmpty()) {
                Files.write(
                    outputDirectory.resolve("rejected_rows.txt"),
                    dataset.rejectedRows(),
                    StandardCharsets.UTF_8
                );
            }
        }
    }

    public static void main(String[] args) {
        Path inputPath = args.length > 0
            ? Path.of(args[0])
            : Path.of("iris.csv");

        Path outputDirectory = args.length > 1
            ? Path.of(args[1])
            : Path.of("iris_eda_output");

        try {
            DatasetLoader loader = new DatasetLoader();

            Dataset dataset = loader.load(inputPath);

            AnalyticalReportService reportService =
                new AnalyticalReportService();

            String report = reportService.generate(dataset);

            ReportExporter exporter = new ReportExporter();

            exporter.export(
                dataset,
                outputDirectory,
                report
            );

            System.out.println("\nIRIS EXPLORATORY DATA ANALYSIS");
            System.out.println("======================================");

            System.out.println("Source: " + dataset.source());

            System.out.println(
                "Valid observations: " +
                dataset.observations().size()
            );

            System.out.println(
                "Rejected records: " +
                dataset.rejectedRows().size()
            );

            GroupAnalysisService groups =
                new GroupAnalysisService();

            Map<Species, Long> distribution =
                groups.distribution(dataset.observations());

            System.out.println("\nSpecies distribution:");

            distribution.forEach((species, count) ->
                System.out.println(
                    "  " + species + ": " + count
                )
            );

            System.out.println(
                "\nGenerated: " +
                outputDirectory.resolve("analytical_report.md")
            );

            System.out.println(
                "Generated: " +
                outputDirectory.resolve("iris_cleaned.csv")
            );

            System.out.println("\nAnalysis completed successfully.");

        } catch (
            IOException |
            DataValidationException |
            IllegalArgumentException exception
        ) {
            System.err.println(
                "EDA failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
