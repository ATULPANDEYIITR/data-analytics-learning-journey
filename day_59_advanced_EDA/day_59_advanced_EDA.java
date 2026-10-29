import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class AdvancedEDA {

    enum Transformation {
        NONE, LOG1P, Z_SCORE, ROBUST
    }

    record FeatureProfile(
        String name,
        int count,
        double mean,
        double median,
        double variance,
        double skewness,
        double q1,
        double q3,
        double lowerFence,
        double upperFence,
        List<Double> outliers
    ) {}

    record Relationship(
        String left,
        String right,
        double covariance,
        double pearson,
        double spearman
    ) {}

    static final class EDAException extends RuntimeException {
        EDAException(String message) {
            super(message);
        }
    }

    interface AssociationMeasure {
        double calculate(List<Double> x, List<Double> y);
    }

    static final class PearsonMeasure implements AssociationMeasure {
        @Override
        public double calculate(List<Double> x, List<Double> y) {
            return pearson(x, y);
        }
    }

    static final class SpearmanMeasure implements AssociationMeasure {
        @Override
        public double calculate(List<Double> x, List<Double> y) {
            return pearson(ranks(x), ranks(y));
        }
    }

    static final class Dataset {
        private final Map<String, List<Double>> features;

        Dataset(Map<String, List<Double>> features) {
            this.features = new LinkedHashMap<>();

            features.forEach((name, values) -> {
                validate(values, name);
                this.features.put(
                    name,
                    List.copyOf(values)
                );
            });
        }

        Map<String, List<Double>> features() {
            return Collections.unmodifiableMap(features);
        }
    }

    static final class AnalysisService {
        private final Dataset dataset;
        private final Map<Transformation, TransformationService>
            transformations = new EnumMap<>(Transformation.class);

        AnalysisService(Dataset dataset) {
            this.dataset = Objects.requireNonNull(dataset);

            transformations.put(
                Transformation.NONE,
                values -> List.copyOf(values)
            );

            transformations.put(
                Transformation.LOG1P,
                AdvancedEDA::log1p
            );

            transformations.put(
                Transformation.Z_SCORE,
                AdvancedEDA::zScore
            );

            transformations.put(
                Transformation.ROBUST,
                AdvancedEDA::robustScale
            );
        }

        Map<String, FeatureProfile> profileFeatures() {
            Map<String, FeatureProfile> result = new LinkedHashMap<>();

            for (var entry : dataset.features().entrySet()) {
                result.put(
                    entry.getKey(),
                    profile(entry.getKey(), entry.getValue())
                );
            }

            return result;
        }

        List<Relationship> relationships() {
            List<Relationship> result = new ArrayList<>();
            List<String> names = new ArrayList<>(
                dataset.features().keySet()
            );

            AssociationMeasure spearman = new SpearmanMeasure();

            for (int i = 0; i < names.size(); i++) {
                for (int j = i + 1; j < names.size(); j++) {
                    String left = names.get(i);
                    String right = names.get(j);

                    List<Double> x = dataset.features().get(left);
                    List<Double> y = dataset.features().get(right);

                    result.add(new Relationship(
                        left,
                        right,
                        covariance(x, y),
                        new PearsonMeasure().calculate(x, y),
                        spearman.calculate(x, y)
                    ));
                }
            }

            return List.copyOf(result);
        }

        List<Double> transform(
            String feature,
            Transformation transformation
        ) {
            List<Double> values = dataset.features().get(feature);

            if (values == null) {
                throw new EDAException(
                    "Unknown feature: " + feature
                );
            }

            return transformations.get(transformation)
                .apply(values);
        }
    }

    interface TransformationService {
        List<Double> apply(List<Double> values);
    }

    static void validate(List<Double> values, String name) {
        if (values == null || values.isEmpty()) {
            throw new EDAException(name + " is empty");
        }

        for (Double value : values) {
            if (value == null || !Double.isFinite(value)) {
                throw new EDAException(
                    name + " contains invalid numeric data"
                );
            }
        }
    }

    static double mean(List<Double> values) {
        validate(values, "values");
        return values.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElseThrow();
    }

    static double quantile(List<Double> values, double q) {
        validate(values, "values");

        if (q < 0 || q > 1) {
            throw new EDAException("Invalid quantile");
        }

        List<Double> sorted = new ArrayList<>(values);
        Collections.sort(sorted);

        double position = (sorted.size() - 1) * q;
        int lower = (int) position;
        int upper = Math.min(lower + 1, sorted.size() - 1);
        double weight = position - lower;

        return sorted.get(lower) * (1 - weight)
            + sorted.get(upper) * weight;
    }

    static double median(List<Double> values) {
        return quantile(values, 0.5);
    }

    static double variance(List<Double> values, boolean sample) {
        validate(values, "values");

        if (sample && values.size() < 2) {
            throw new EDAException("Insufficient observations");
        }

        double average = mean(values);
        double total = 0;

        for (double value : values) {
            total += Math.pow(value - average, 2);
        }

        return total / (sample
            ? values.size() - 1
            : values.size());
    }

    static double covariance(
        List<Double> x,
        List<Double> y
    ) {
        validate(x, "x");
        validate(y, "y");

        if (x.size() != y.size() || x.size() < 2) {
            throw new EDAException(
                "Covariance requires equal samples"
            );
        }

        double mx = mean(x);
        double my = mean(y);
        double total = 0;

        for (int i = 0; i < x.size(); i++) {
            total += (x.get(i) - mx)
                * (y.get(i) - my);
        }

        return total / (x.size() - 1);
    }

    static double pearson(
        List<Double> x,
        List<Double> y
    ) {
        double cov = covariance(x, y);
        double sx = Math.sqrt(variance(x, true));
        double sy = Math.sqrt(variance(y, true));

        return sx == 0 || sy == 0
            ? 0
            : cov / (sx * sy);
    }

    static double skewness(List<Double> values) {
        validate(values, "values");

        if (values.size() < 3) {
            return 0;
        }

        double m = mean(values);
        double s = Math.sqrt(variance(values, true));

        if (s == 0) {
            return 0;
        }

        double total = 0;
        for (double value : values) {
            total += Math.pow((value - m) / s, 3);
        }

        double n = values.size();

        return n / ((n - 1) * (n - 2)) * total;
    }

    static List<Double> ranks(List<Double> values) {
        record Indexed(double value, int index) {}

        List<Indexed> sorted = new ArrayList<>();

        for (int i = 0; i < values.size(); i++) {
            sorted.add(new Indexed(values.get(i), i));
        }

        sorted.sort((a, b) -> {
            int comparison = Double.compare(
                a.value(),
                b.value()
            );
            return comparison != 0
                ? comparison
                : Integer.compare(a.index(), b.index());
        });

        List<Double> result = new ArrayList<>(
            Collections.nCopies(values.size(), 0.0)
        );

        int i = 0;
        while (i < sorted.size()) {
            int j = i;

            while (j + 1 < sorted.size()
                && Double.compare(
                    sorted.get(j + 1).value(),
                    sorted.get(i).value()
                ) == 0) {
                j++;
            }

            double rank = (i + j + 2) / 2.0;

            for (int k = i; k <= j; k++) {
                result.set(
                    sorted.get(k).index(),
                    rank
                );
            }

            i = j + 1;
        }

        return result;
    }

    static FeatureProfile profile(
        String name,
        List<Double> values
    ) {
        validate(values, name);

        double q1 = quantile(values, 0.25);
        double q3 = quantile(values, 0.75);
        double iqr = q3 - q1;
        double lower = q1 - 1.5 * iqr;
        double upper = q3 + 1.5 * iqr;

        List<Double> outliers = values.stream()
            .filter(value -> value < lower || value > upper)
            .toList();

        return new FeatureProfile(
            name,
            values.size(),
            mean(values),
            median(values),
            variance(values, false),
            skewness(values),
            q1,
            q3,
            lower,
            upper,
            outliers
        );
    }

    static List<Double> log1p(List<Double> values) {
        validate(values, "values");

        return values.stream()
            .map(value -> {
                if (value <= -1) {
                    throw new EDAException(
                        "log1p requires values greater than -1"
                    );
                }
                return Math.log1p(value);
            })
            .toList();
    }

    static List<Double> zScore(List<Double> values) {
        double m = mean(values);
        double s = Math.sqrt(variance(values, false));

        return values.stream()
            .map(value -> s == 0
                ? 0.0
                : (value - m) / s)
            .toList();
    }

    static List<Double> robustScale(List<Double> values) {
        double med = median(values);
        double scale =
            quantile(values, 0.75) -
            quantile(values, 0.25);

        return values.stream()
            .map(value -> scale == 0
                ? 0.0
                : (value - med) / scale)
            .toList();
    }

    static Dataset sampleDataset() {
        double[][] rows = {
            {42000, 1100, 3, 8, 2},
            {48000, 1350, 4, 14, 1},
            {51000, 1500, 5, 18, 1},
            {56000, 1720, 6, 25, 0},
            {62000, 1900, 7, 30, 0},
            {68000, 2150, 8, 36, 1},
            {72000, 2450, 9, 42, 0},
            {79000, 2600, 10, 48, 0},
            {85000, 3000, 11, 52, 1},
            {91000, 3200, 12, 60, 0},
            {47000, 1250, 4, 12, 3},
            {53000, 1550, 5, 21, 2},
            {60000, 1820, 7, 28, 1},
            {74000, 2300, 9, 45, 0},
            {1500000, 3500, 3, 10, 5},
            {45000, 1050, 2, 5, 7}
        };

        String[] names = {
            "income",
            "spending",
            "visits",
            "tenure",
            "complaints"
        };

        Map<String, List<Double>> features =
            new LinkedHashMap<>();

        for (int column = 0; column < names.length; column++) {
            List<Double> values = new ArrayList<>();

            for (double[] row : rows) {
                values.add(row[column]);
            }

            features.put(names[column], values);
        }

        return new Dataset(features);
    }

    public static void main(String[] args) {
        try {
            AnalysisService service =
                new AnalysisService(sampleDataset());

            System.out.println(
                "ADVANCED EXPLORATORY DATA ANALYSIS"
            );
            System.out.println(
                "================================="
            );

            for (FeatureProfile profile :
                service.profileFeatures().values()) {

                System.out.printf(
                    "%n%s%n  count=%d%n  mean=%.3f%n" +
                    "  median=%.3f%n  variance=%.3f%n" +
                    "  skewness=%.3f%n  IQR=[%.3f, %.3f]%n" +
                    "  outliers=%s%n",
                    profile.name(),
                    profile.count(),
                    profile.mean(),
                    profile.median(),
                    profile.variance(),
                    profile.skewness(),
                    profile.lowerFence(),
                    profile.upperFence(),
                    profile.outliers()
                );
            }

            System.out.println("\nRELATIONSHIPS");

            for (Relationship relationship :
                service.relationships()) {

                if (Math.abs(relationship.pearson()) >= 0.70) {
                    System.out.printf(
                        "%s <-> %s: covariance=%.3f, " +
                        "Pearson=%.3f, Spearman=%.3f%n",
                        relationship.left(),
                        relationship.right(),
                        relationship.covariance(),
                        relationship.pearson(),
                        relationship.spearman()
                    );
                }
            }

            List<Double> incomeLog =
                service.transform(
                    "income",
                    Transformation.LOG1P
                );

            List<Double> income =
                service.transform(
                    "income",
                    Transformation.NONE
                );

            System.out.println("\nTRANSFORMATION DIAGNOSTIC");
            System.out.printf(
                "Income skewness: %.3f -> %.3f%n",
                skewness(income),
                skewness(incomeLog)
            );

            System.out.println("\nENGINEERING CONTROLS");
            System.out.println(
                "- Domain types prevent transformation-state confusion."
            );
            System.out.println(
                "- Immutable dataset copies prevent accidental mutation."
            );
            System.out.println(
                "- IQR outliers are reported without automatic deletion."
            );
            System.out.println(
                "- Pearson and Spearman answer different relationship questions."
            );
            System.out.println(
                "- Transformation parameters must be fitted on training data only."
            );
        }
        catch (EDAException error) {
            System.err.println(
                "EDA validation failure: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
