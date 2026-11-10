import java.util.*;
import java.util.stream.Collectors;

/*
 * ANOVA Enterprise Statistical Analysis System
 *
 * Java 17
 *
 * Features:
 * - Immutable experimental observations
 * - One-way ANOVA
 * - Balanced two-way ANOVA
 * - Main effects and interaction
 * - Assumption diagnostics
 * - Levene variance test
 * - Jarque-Bera residual normality test
 * - Pooled and Welch pairwise comparisons
 * - Holm multiple-testing correction
 * - Effect sizes
 * - Enterprise analysis services
 * - Explicit workflow states
 * - Validation and automated tests
 *
 * No third-party dependencies.
 */

public class ANOVAEnterprise {

    private static final double ALPHA = 0.05;

    // ========================================================
    // 1. EXCEPTIONS
    // ========================================================

    static class AnalysisException extends RuntimeException {
        AnalysisException(String message) {
            super(message);
        }
    }


    // ========================================================
    // 2. ENUMERATIONS
    // ========================================================

    enum AnalysisType {
        ONE_WAY,
        TWO_WAY
    }

    enum AnalysisState {
        CREATED,
        VALIDATING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum DiagnosticStatus {
        PASS,
        WARNING,
        DESIGN_DEPENDENT
    }


    // ========================================================
    // 3. IMMUTABLE DOMAIN RECORDS
    // ========================================================

    record Observation(
        double value,
        String factorA,
        String factorB
    ) {
        Observation {
            if (!Double.isFinite(value)) {
                throw new AnalysisException(
                    "Observation must be finite."
                );
            }

            if (factorA == null || factorA.isBlank()) {
                throw new AnalysisException(
                    "Factor A is required."
                );
            }

            if (factorB != null && factorB.isBlank()) {
                throw new AnalysisException(
                    "Factor B cannot be blank."
                );
            }
        }
    }


    record ANOVAResult(
        String analysis,
        String source,
        int dfBetween,
        int dfWithin,
        double ssBetween,
        double ssWithin,
        double msBetween,
        double msWithin,
        double fStatistic,
        double pValue,
        double etaSquared,
        double omegaSquared
    ) {}


    record EffectResult(
        String source,
        int df,
        double sumSquares,
        double meanSquare,
        double fStatistic,
        double pValue
    ) {}


    record PairwiseResult(
        String groupA,
        String groupB,
        double difference,
        double statistic,
        double rawPValue,
        double adjustedPValue,
        boolean significant,
        String method
    ) {}


    record Diagnostic(
        String name,
        double statistic,
        double pValue,
        DiagnosticStatus status,
        String explanation
    ) {}


    record TwoWayResult(
        EffectResult factorA,
        EffectResult factorB,
        EffectResult interaction,
        double errorSS,
        int errorDF,
        double errorMS
    ) {}


    record AnalysisJob(
        UUID id,
        AnalysisState state,
        InstantPair timestamps,
        String error
    ) {}


    record InstantPair(
        long startedAt,
        long completedAt
    ) {}


    // ========================================================
    // 4. DATASET
    // ========================================================

    static final class Dataset {

        private final List<Observation> observations;

        Dataset(List<Observation> observations) {
            if (observations == null || observations.isEmpty()) {
                throw new AnalysisException(
                    "Dataset cannot be empty."
                );
            }

            this.observations = List.copyOf(observations);
        }

        List<Observation> observations() {
            return observations;
        }

        Map<String, List<Double>> groups() {
            Map<String, List<Double>> groups = new TreeMap<>();

            for (Observation observation : observations) {
                groups.computeIfAbsent(
                    observation.factorA(),
                    key -> new ArrayList<>()
                ).add(observation.value());
            }

            return groups;
        }

        Map<CellKey, List<Double>> cells() {
            Map<CellKey, List<Double>> cells = new TreeMap<>(
                Comparator.comparing(CellKey::factorA)
                    .thenComparing(CellKey::factorB)
            );

            for (Observation observation : observations) {
                if (observation.factorB() == null) {
                    throw new AnalysisException(
                        "Factor B is required for two-way ANOVA."
                    );
                }

                CellKey key = new CellKey(
                    observation.factorA(),
                    observation.factorB()
                );

                cells.computeIfAbsent(
                    key,
                    ignored -> new ArrayList<>()
                ).add(observation.value());
            }

            return cells;
        }
    }


    record CellKey(String factorA, String factorB) {}


    // ========================================================
    // 5. NUMERICAL UTILITIES
    // ========================================================

    static double mean(List<Double> values) {
        if (values.isEmpty()) {
            throw new AnalysisException("Empty group.");
        }

        return values.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElseThrow();
    }


    static double variance(List<Double> values) {
        if (values.size() < 2) {
            throw new AnalysisException(
                "At least two observations are required."
            );
        }

        double average = mean(values);

        return values.stream()
            .mapToDouble(x -> Math.pow(x - average, 2))
            .sum() / (values.size() - 1);
    }


    static double sumSquares(
        List<Double> values,
        double center
    ) {
        return values.stream()
            .mapToDouble(x -> Math.pow(x - center, 2))
            .sum();
    }


    static double median(List<Double> values) {
        List<Double> sorted = new ArrayList<>(values);

        Collections.sort(sorted);

        int n = sorted.size();

        return n % 2 == 1
            ? sorted.get(n / 2)
            : (sorted.get(n / 2 - 1) + sorted.get(n / 2)) / 2;
    }


    // ========================================================
    // 6. SPECIAL FUNCTIONS
    // ========================================================

    static double logGamma(double z) {
        double[] coefficients = {
            676.5203681218851,
            -1259.1392167224028,
            771.3234287776531,
            -176.6150291621406,
            12.507343278686905,
            -0.13857109526572012,
            9.984369578019572e-6,
            1.5056327351493116e-7
        };

        if (z < 0.5) {
            return Math.log(Math.PI)
                - Math.log(Math.sin(Math.PI * z))
                - logGamma(1 - z);
        }

        z -= 1;

        double x = 0.9999999999998099;

        for (int i = 0; i < coefficients.length; i++) {
            x += coefficients[i] / (z + i + 1);
        }

        double t = z + coefficients.length - 0.5;

        return 0.5 * Math.log(2 * Math.PI)
            + (z + 0.5) * Math.log(t)
            - t
            + Math.log(x);
    }


    static double betaFraction(double a, double b, double x) {
        double qab = a + b;
        double qap = a + 1;
        double qam = a - 1;

        double c = 1;
        double d = 1 - qab * x / qap;

        if (Math.abs(d) < 1e-30) d = 1e-30;

        d = 1 / d;

        double h = d;

        for (int m = 1; m <= 300; m++) {
            int m2 = 2 * m;

            double aa = m * (b - m) * x
                / ((qam + m2) * (a + m2));

            d = 1 + aa * d;
            if (Math.abs(d) < 1e-30) d = 1e-30;

            c = 1 + aa / c;
            if (Math.abs(c) < 1e-30) c = 1e-30;

            d = 1 / d;
            h *= d * c;

            aa = -(a + m) * (qab + m) * x
                / ((a + m2) * (qap + m2));

            d = 1 + aa * d;
            if (Math.abs(d) < 1e-30) d = 1e-30;

            c = 1 + aa / c;
            if (Math.abs(c) < 1e-30) c = 1e-30;

            d = 1 / d;

            double delta = d * c;
            h *= delta;

            if (Math.abs(delta - 1) < 3e-14) break;
        }

        return h;
    }


    static double regularizedBeta(
        double x,
        double a,
        double b
    ) {
        if (a <= 0 || b <= 0) {
            throw new AnalysisException(
                "Invalid beta distribution parameters."
            );
        }

        if (x <= 0) return 0;
        if (x >= 1) return 1;

        double front = Math.exp(
            logGamma(a + b)
            - logGamma(a)
            - logGamma(b)
            + a * Math.log(x)
            + b * Math.log1p(-x)
        );

        if (x < (a + 1) / (a + b + 2)) {
            return front * betaFraction(a, b, x) / a;
        }

        return 1 - front
            * betaFraction(b, a, 1 - x) / b;
    }


    static double fSurvival(double f, int df1, int df2) {
        if (df1 <= 0 || df2 <= 0) {
            throw new AnalysisException("Invalid F degrees of freedom.");
        }

        if (f <= 0) return 1;

        return regularizedBeta(
            df2 / (df2 + df1 * f),
            df2 / 2.0,
            df1 / 2.0
        );
    }


    static double tCDF(double t, double df) {
        double ib = regularizedBeta(
            df / (df + t * t),
            df / 2,
            0.5
        );

        return t >= 0 ? 1 - ib / 2 : ib / 2;
    }


    static double tPValue(double t, double df) {
        return Math.min(
            1,
            2 * (1 - tCDF(Math.abs(t), df))
        );
    }


    // ========================================================
    // 7. DESCRIPTIVE ANALYSIS
    // ========================================================

    static Map<String, Map<String, Double>> describe(
        Dataset dataset
    ) {
        Map<String, Map<String, Double>> result = new TreeMap<>();

        dataset.groups().forEach((name, values) -> {
            double avg = mean(values);
            double variance = variance(values);

            Map<String, Double> statistics = new LinkedHashMap<>();

            statistics.put("count", (double) values.size());
            statistics.put("mean", avg);
            statistics.put("median", median(values));
            statistics.put("variance", variance);
            statistics.put("standardDeviation", Math.sqrt(variance));
            statistics.put("minimum", values.stream()
                .mapToDouble(Double::doubleValue).min().orElseThrow());
            statistics.put("maximum", values.stream()
                .mapToDouble(Double::doubleValue).max().orElseThrow());

            result.put(name, statistics);
        });

        return result;
    }


    // ========================================================
    // 8. ONE-WAY ANOVA SERVICE
    // ========================================================

    static ANOVAResult oneWayANOVA(Dataset dataset) {
        Map<String, List<Double>> groups = dataset.groups();

        if (groups.size() < 2) {
            throw new AnalysisException(
                "At least two groups are required."
            );
        }

        List<Double> all = new ArrayList<>();

        for (List<Double> values : groups.values()) {
            if (values.size() < 2) {
                throw new AnalysisException(
                    "Each group requires two observations."
                );
            }

            all.addAll(values);
        }

        double grand = mean(all);

        double ssBetween = 0;
        double ssWithin = 0;

        for (List<Double> values : groups.values()) {
            double groupMean = mean(values);

            ssBetween += values.size()
                * Math.pow(groupMean - grand, 2);

            ssWithin += sumSquares(values, groupMean);
        }

        int dfBetween = groups.size() - 1;
        int dfWithin = all.size() - groups.size();

        if (dfWithin <= 0) {
            throw new AnalysisException("Insufficient residual degrees of freedom.");
        }

        double msBetween = ssBetween / dfBetween;
        double msWithin = ssWithin / dfWithin;

        double f = msWithin == 0
            ? (msBetween == 0 ? 0 : Double.POSITIVE_INFINITY)
            : msBetween / msWithin;

        double p = Double.isInfinite(f)
            ? 0
            : fSurvival(f, dfBetween, dfWithin);

        double total = ssBetween + ssWithin;

        double eta = total == 0 ? 0 : ssBetween / total;

        double omega = total + msWithin == 0
            ? 0
            : Math.max(
                0,
                (ssBetween - dfBetween * msWithin)
                / (total + msWithin)
            );

        return new ANOVAResult(
            "One-way ANOVA",
            "Factor A",
            dfBetween,
            dfWithin,
            ssBetween,
            ssWithin,
            msBetween,
            msWithin,
            f,
            p,
            eta,
            omega
        );
    }


    // ========================================================
    // 9. TWO-WAY ANOVA SERVICE
    // ========================================================

    static TwoWayResult twoWayANOVA(Dataset dataset) {
        Map<CellKey, List<Double>> cells = dataset.cells();

        Set<String> factorA = new TreeSet<>();
        Set<String> factorB = new TreeSet<>();

        cells.keySet().forEach(key -> {
            factorA.add(key.factorA());
            factorB.add(key.factorB());
        });

        int a = factorA.size();
        int b = factorB.size();

        if (a < 2 || b < 2) {
            throw new AnalysisException(
                "Both factors require at least two levels."
            );
        }

        if (cells.size() != a * b) {
            throw new AnalysisException("Missing factorial cells.");
        }

        int replication = cells.values().iterator().next().size();

        if (replication < 2) {
            throw new AnalysisException(
                "At least two observations per cell are required."
            );
        }

        if (cells.values().stream()
            .anyMatch(values -> values.size() != replication)) {
            throw new AnalysisException(
                "Balanced factorial design required."
            );
        }

        List<Double> all = cells.values().stream()
            .flatMap(Collection::stream)
            .toList();

        double grand = mean(all);

        Map<String, Double> meansA = new HashMap<>();
        Map<String, Double> meansB = new HashMap<>();

        for (String level : factorA) {
            List<Double> values = new ArrayList<>();

            cells.forEach((key, cell) -> {
                if (key.factorA().equals(level)) {
                    values.addAll(cell);
                }
            });

            meansA.put(level, mean(values));
        }

        for (String level : factorB) {
            List<Double> values = new ArrayList<>();

            cells.forEach((key, cell) -> {
                if (key.factorB().equals(level)) {
                    values.addAll(cell);
                }
            });

            meansB.put(level, mean(values));
        }

        double ssA = 0;
        double ssB = 0;
        double ssAB = 0;
        double ssError = 0;

        for (String level : factorA) {
            ssA += b * replication
                * Math.pow(meansA.get(level) - grand, 2);
        }

        for (String level : factorB) {
            ssB += a * replication
                * Math.pow(meansB.get(level) - grand, 2);
        }

        for (var entry : cells.entrySet()) {
            CellKey key = entry.getKey();
            List<Double> values = entry.getValue();

            double cellMean = mean(values);

            double interaction = cellMean
                - meansA.get(key.factorA())
                - meansB.get(key.factorB())
                + grand;

            ssAB += replication * interaction * interaction;

            ssError += sumSquares(values, cellMean);
        }

        int dfA = a - 1;
        int dfB = b - 1;
        int dfAB = dfA * dfB;
        int dfError = a * b * (replication - 1);

        double msError = ssError / dfError;

        return new TwoWayResult(
            createEffect("Factor A", ssA, dfA, msError, dfError),
            createEffect("Factor B", ssB, dfB, msError, dfError),
            createEffect("Interaction", ssAB, dfAB, msError, dfError),
            ssError,
            dfError,
            msError
        );
    }


    static EffectResult createEffect(
        String source,
        double ss,
        int df,
        double msError,
        int dfError
    ) {
        double ms = ss / df;

        double f = msError == 0
            ? (ms == 0 ? 0 : Double.POSITIVE_INFINITY)
            : ms / msError;

        double p = Double.isInfinite(f)
            ? 0
            : fSurvival(f, df, dfError);

        return new EffectResult(
            source, df, ss, ms, f, p
        );
    }


    // ========================================================
    // 10. ASSUMPTION DIAGNOSTICS
    // ========================================================

    static ANOVAResult leveneTest(Dataset dataset) {
        List<Observation> transformed = new ArrayList<>();

        dataset.groups().forEach((name, values) -> {
            double center = median(values);

            for (double value : values) {
                transformed.add(new Observation(
                    Math.abs(value - center),
                    name,
                    null
                ));
            }
        });

        return oneWayANOVA(new Dataset(transformed));
    }


    static double[] jarqueBera(List<Double> residuals) {
        if (residuals.size() < 3) {
            throw new AnalysisException("Insufficient residuals.");
        }

        double avg = mean(residuals);

        double m2 = residuals.stream()
            .mapToDouble(x -> Math.pow(x - avg, 2))
            .average().orElseThrow();

        if (m2 == 0) return new double[]{0, 1};

        double m3 = residuals.stream()
            .mapToDouble(x -> Math.pow(x - avg, 3))
            .average().orElseThrow();

        double m4 = residuals.stream()
            .mapToDouble(x -> Math.pow(x - avg, 4))
            .average().orElseThrow();

        double skew = m3 / Math.pow(m2, 1.5);
        double kurtosis = m4 / (m2 * m2);

        double jb = residuals.size() / 6.0 * (
            skew * skew
            + Math.pow(kurtosis - 3, 2) / 4
        );

        return new double[]{jb, Math.exp(-jb / 2)};
    }


    static List<Diagnostic> diagnostics(Dataset dataset) {
        List<Double> residuals = new ArrayList<>();

        dataset.groups().values().forEach(values -> {
            double avg = mean(values);

            values.forEach(x -> residuals.add(x - avg));
        });

        ANOVAResult levene = leveneTest(dataset);
        double[] jb = jarqueBera(residuals);

        return List.of(
            new Diagnostic(
                "Independence",
                0,
                Double.NaN,
                DiagnosticStatus.DESIGN_DEPENDENT,
                "Must be justified through experimental design."
            ),
            new Diagnostic(
                "Variance homogeneity",
                levene.fStatistic(),
                levene.pValue(),
                levene.pValue() >= ALPHA
                    ? DiagnosticStatus.PASS
                    : DiagnosticStatus.WARNING,
                "Median-centered Levene test."
            ),
            new Diagnostic(
                "Residual normality",
                jb[0],
                jb[1],
                jb[1] >= ALPHA
                    ? DiagnosticStatus.PASS
                    : DiagnosticStatus.WARNING,
                "Jarque-Bera diagnostic."
            )
        );
    }


    // ========================================================
    // 11. HOLM CORRECTION
    // ========================================================

    static double[] holmCorrection(double[] pValues) {
        List<Integer> order = new ArrayList<>();

        for (int i = 0; i < pValues.length; i++) {
            if (!Double.isFinite(pValues[i])
                || pValues[i] < 0
                || pValues[i] > 1) {
                throw new AnalysisException("Invalid p-value.");
            }

            order.add(i);
        }

        order.sort(
            Comparator.comparingDouble(i -> pValues[i])
        );

        double[] adjusted = new double[pValues.length];

        double maximum = 0;

        for (int rank = 0; rank < order.size(); rank++) {
            int index = order.get(rank);

            maximum = Math.max(
                maximum,
                Math.min(
                    1,
                    (order.size() - rank) * pValues[index]
                )
            );

            adjusted[index] = maximum;
        }

        return adjusted;
    }


    // ========================================================
    // 12. POST-HOC COMPARISONS
    // ========================================================

    static List<PairwiseResult> postHoc(
        Dataset dataset,
        boolean equalVariances
    ) {
        Map<String, List<Double>> groups = dataset.groups();

        List<String> names = new ArrayList<>(groups.keySet());

        List<PairwiseResult> results = new ArrayList<>();

        for (int i = 0; i < names.size(); i++) {
            for (int j = i + 1; j < names.size(); j++) {

                List<Double> a = groups.get(names.get(i));
                List<Double> b = groups.get(names.get(j));

                double difference = mean(a) - mean(b);

                double se;
                double df;

                if (equalVariances) {
                    df = a.size() + b.size() - 2;

                    double pooled = (
                        (a.size() - 1) * variance(a)
                        + (b.size() - 1) * variance(b)
                    ) / df;

                    se = Math.sqrt(
                        pooled * (1.0 / a.size() + 1.0 / b.size())
                    );
                } else {
                    double va = variance(a) / a.size();
                    double vb = variance(b) / b.size();

                    se = Math.sqrt(va + vb);

                    df = Math.pow(va + vb, 2) / (
                        va * va / (a.size() - 1)
                        + vb * vb / (b.size() - 1)
                    );
                }

                double t = se == 0
                    ? (difference == 0 ? 0
                        : Math.copySign(Double.POSITIVE_INFINITY, difference))
                    : difference / se;

                double p = Double.isInfinite(t)
                    ? 0
                    : tPValue(t, df);

                results.add(new PairwiseResult(
                    names.get(i),
                    names.get(j),
                    difference,
                    t,
                    p,
                    0,
                    false,
                    equalVariances
                        ? "Pooled-variance pairwise t"
                        : "Welch pairwise t"
                ));
            }
        }

        double[] raw = results.stream()
            .mapToDouble(PairwiseResult::rawPValue)
            .toArray();

        double[] adjusted = holmCorrection(raw);

        List<PairwiseResult> finalResults = new ArrayList<>();

        for (int i = 0; i < results.size(); i++) {
            PairwiseResult item = results.get(i);

            finalResults.add(new PairwiseResult(
                item.groupA(),
                item.groupB(),
                item.difference(),
                item.statistic(),
                item.rawPValue(),
                adjusted[i],
                adjusted[i] < ALPHA,
                item.method() + " with Holm correction"
            ));
        }

        return List.copyOf(finalResults);
    }


    // ========================================================
    // 13. ENTERPRISE ANALYSIS SERVICE
    // ========================================================

    static final class AnalysisService {

        private final Map<UUID, AnalysisJob> jobs =
            new LinkedHashMap<>();

        synchronized AnalysisJob getJob(UUID id) {
            return jobs.get(id);
        }

        synchronized Collection<AnalysisJob> getJobs() {
            return List.copyOf(jobs.values());
        }

        ANOVAResult execute(Dataset dataset) {
            UUID id = UUID.randomUUID();

            long started = System.currentTimeMillis();

            AnalysisJob job = new AnalysisJob(
                id,
                AnalysisState.CREATED,
                new InstantPair(0, 0),
                null
            );

            synchronized (this) {
                jobs.put(id, job);
            }

            try {
                updateJob(id, AnalysisState.VALIDATING, started, 0, null);

                dataset.groups().forEach((name, values) -> {
                    if (values.size() < 2) {
                        throw new AnalysisException(
                            "Invalid experimental group: " + name
                        );
                    }
                });

                updateJob(id, AnalysisState.RUNNING, started, 0, null);

                ANOVAResult result = oneWayANOVA(dataset);

                updateJob(
                    id,
                    AnalysisState.COMPLETED,
                    started,
                    System.currentTimeMillis(),
                    null
                );

                return result;

            } catch (RuntimeException exception) {
                updateJob(
                    id,
                    AnalysisState.FAILED,
                    started,
                    System.currentTimeMillis(),
                    exception.getMessage()
                );

                throw exception;
            }
        }

        private synchronized void updateJob(
            UUID id,
            AnalysisState state,
            long started,
            long completed,
            String error
        ) {
            jobs.put(
                id,
                new AnalysisJob(
                    id,
                    state,
                    new InstantPair(started, completed),
                    error
                )
            );
        }
    }


    // ========================================================
    // 14. AUTOMATED TESTS
    // ========================================================

    static void runTests() {
        Dataset sample = new Dataset(List.of(
            new Observation(1, "A", null),
            new Observation(2, "A", null),
            new Observation(3, "B", null),
            new Observation(4, "B", null)
        ));

        ANOVAResult oneWay = oneWayANOVA(sample);

        if (oneWay.dfBetween() != 1
            || oneWay.dfWithin() != 2
            || oneWay.fStatistic() <= 0) {
            throw new AssertionError("One-way test failed.");
        }

        Dataset factorial = new Dataset(List.of(
            new Observation(10, "A", "Low"),
            new Observation(11, "A", "Low"),
            new Observation(15, "A", "High"),
            new Observation(16, "A", "High"),
            new Observation(13, "B", "Low"),
            new Observation(14, "B", "Low"),
            new Observation(23, "B", "High"),
            new Observation(24, "B", "High")
        ));

        TwoWayResult twoWay = twoWayANOVA(factorial);

        if (twoWay.interaction().df() != 1) {
            throw new AssertionError("Two-way test failed.");
        }

        double[] corrected = holmCorrection(
            new double[]{0.01, 0.03, 0.04}
        );

        if (Arrays.stream(corrected)
            .anyMatch(p -> p < 0 || p > 1)) {
            throw new AssertionError("Holm test failed.");
        }

        if (fSurvival(0, 1, 10) != 1) {
            throw new AssertionError("F distribution test failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }


    // ========================================================
    // 15. APPLICATION
    // ========================================================

    public static void main(String[] args) {
        try {
            runTests();

            Dataset experiment = new Dataset(List.of(
                new Observation(21, "Control", null),
                new Observation(23, "Control", null),
                new Observation(22, "Control", null),
                new Observation(24, "Control", null),
                new Observation(20, "Control", null),
                new Observation(22, "Control", null),

                new Observation(25, "Treatment A", null),
                new Observation(27, "Treatment A", null),
                new Observation(26, "Treatment A", null),
                new Observation(28, "Treatment A", null),
                new Observation(24, "Treatment A", null),
                new Observation(27, "Treatment A", null),

                new Observation(30, "Treatment B", null),
                new Observation(32, "Treatment B", null),
                new Observation(29, "Treatment B", null),
                new Observation(31, "Treatment B", null),
                new Observation(33, "Treatment B", null),
                new Observation(30, "Treatment B", null)
            ));

            System.out.println("\nDESCRIPTIVE STATISTICS");

            describe(experiment).forEach((name, values) ->
                System.out.println(name + " " + values)
            );

            AnalysisService service = new AnalysisService();

            ANOVAResult result = service.execute(experiment);

            System.out.println("\nONE-WAY ANOVA");
            System.out.println(result);

            System.out.println("\nASSUMPTION DIAGNOSTICS");

            diagnostics(experiment).forEach(System.out::println);

            System.out.println("\nPOST-HOC COMPARISONS");

            postHoc(experiment, true).forEach(System.out::println);

            System.out.println("\nWELCH POST-HOC COMPARISONS");

            postHoc(experiment, false).forEach(System.out::println);

            Dataset factorial = new Dataset(List.of(
                new Observation(10, "Traditional", "Low"),
                new Observation(11, "Traditional", "Low"),
                new Observation(9, "Traditional", "Low"),
                new Observation(10, "Traditional", "Low"),

                new Observation(15, "Traditional", "High"),
                new Observation(14, "Traditional", "High"),
                new Observation(16, "Traditional", "High"),
                new Observation(15, "Traditional", "High"),

                new Observation(13, "Modern", "Low"),
                new Observation(12, "Modern", "Low"),
                new Observation(14, "Modern", "Low"),
                new Observation(13, "Modern", "Low"),

                new Observation(23, "Modern", "High"),
                new Observation(22, "Modern", "High"),
                new Observation(24, "Modern", "High"),
                new Observation(23, "Modern", "High")
            ));

            System.out.println("\nTWO-WAY ANOVA");

            TwoWayResult twoWay = twoWayANOVA(factorial);

            System.out.println(twoWay.factorA());
            System.out.println(twoWay.factorB());
            System.out.println(twoWay.interaction());

            System.out.println("\nANALYSIS JOBS");

            service.getJobs().forEach(System.out::println);

        } catch (AnalysisException exception) {
            System.err.println(
                "ANALYSIS VALIDATION ERROR: " + exception.getMessage()
            );

            System.exitCodePlaceholder();
        }
    }
}
