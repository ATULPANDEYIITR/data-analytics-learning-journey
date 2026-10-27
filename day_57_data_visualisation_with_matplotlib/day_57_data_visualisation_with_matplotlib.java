import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/*
 * Java 17 enterprise-oriented visualization model.
 *
 * The program separates domain data, validation, visualization policies,
 * subplot configuration, annotations, and reporting. It models the decisions
 * a visualization service makes before handing validated data to a rendering
 * engine.
 */

public class DataVisualizationApp {

    enum ScaleType {
        LINEAR,
        LOGARITHMIC
    }

    enum Metric {
        DEPLOYMENTS,
        INCIDENTS,
        LEAD_TIME_HOURS,
        COVERAGE_PERCENT
    }

    record MonthlyMetric(
        String month,
        int deployments,
        int incidents,
        double leadTimeHours,
        double coveragePercent
    ) {
        MonthlyMetric {
            Objects.requireNonNull(month, "month");
            if (month.isBlank()) {
                throw new IllegalArgumentException("Month cannot be blank.");
            }
            if (deployments < 0) {
                throw new IllegalArgumentException(
                    "Deployments cannot be negative."
                );
            }
            if (incidents < 0) {
                throw new IllegalArgumentException(
                    "Incidents cannot be negative."
                );
            }
            if (!Double.isFinite(leadTimeHours) || leadTimeHours <= 0) {
                throw new IllegalArgumentException(
                    "Lead time must be positive and finite."
                );
            }
            if (!Double.isFinite(coveragePercent)
                    || coveragePercent < 0
                    || coveragePercent > 100) {
                throw new IllegalArgumentException(
                    "Coverage must be between 0 and 100."
                );
            }
        }
    }

    record TeamSeries(
        String name,
        List<MonthlyMetric> metrics
    ) {
        TeamSeries {
            Objects.requireNonNull(name, "name");
            Objects.requireNonNull(metrics, "metrics");

            if (name.isBlank()) {
                throw new IllegalArgumentException("Team name cannot be blank.");
            }

            if (metrics.isEmpty()) {
                throw new IllegalArgumentException(
                    "A team needs at least one metric."
                );
            }

            metrics = List.copyOf(metrics);
        }

        List<Double> values(Metric metric) {
            return metrics.stream()
                .map(metricValue(metric))
                .toList();
        }

        private static java.util.function.Function<MonthlyMetric, Double>
        metricValue(Metric metric) {
            return metricRecord -> switch (metric) {
                case DEPLOYMENTS ->
                    (double) metricRecord.deployments();
                case INCIDENTS ->
                    (double) metricRecord.incidents();
                case LEAD_TIME_HOURS ->
                    metricRecord.leadTimeHours();
                case COVERAGE_PERCENT ->
                    metricRecord.coveragePercent();
            };
        }
    }

    record Annotation(
        String label,
        int periodIndex,
        double value
    ) {}

    record AxisPolicy(
        String title,
        String xLabel,
        String yLabel,
        ScaleType scale,
        double minimum,
        double maximum
    ) {
        AxisPolicy {
            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException("Axis title is required.");
            }
            if (minimum > maximum) {
                throw new IllegalArgumentException(
                    "Axis minimum cannot exceed maximum."
                );
            }
            if (scale == ScaleType.LOGARITHMIC
                    && minimum <= 0) {
                throw new IllegalArgumentException(
                    "Logarithmic axes require positive lower bounds."
                );
            }
        }
    }

    record PlotDefinition(
        String title,
        AxisPolicy axis,
        List<String> legendEntries,
        List<Annotation> annotations
    ) {
        PlotDefinition {
            title = Objects.requireNonNull(title);
            axis = Objects.requireNonNull(axis);
            legendEntries = List.copyOf(legendEntries);
            annotations = List.copyOf(annotations);
        }
    }

    static final class VisualizationValidationException
        extends RuntimeException {

        VisualizationValidationException(String message) {
            super(message);
        }
    }

    interface VisualizationPolicy {
        void validate(List<TeamSeries> teams, Metric metric, ScaleType scale);
    }

    static final class DefaultVisualizationPolicy
        implements VisualizationPolicy {

        @Override
        public void validate(
            List<TeamSeries> teams,
            Metric metric,
            ScaleType scale
        ) {
            Objects.requireNonNull(teams);
            Objects.requireNonNull(metric);
            Objects.requireNonNull(scale);

            if (teams.isEmpty()) {
                throw new VisualizationValidationException(
                    "At least one series is required."
                );
            }

            int expectedPeriods = teams.get(0).metrics().size();

            for (TeamSeries team : teams) {
                if (team.metrics().size() != expectedPeriods) {
                    throw new VisualizationValidationException(
                        "All series must contain the same number of periods."
                    );
                }

                List<String> months = team.metrics().stream()
                    .map(MonthlyMetric::month)
                    .toList();

                if (months.stream().distinct().count() != months.size()) {
                    throw new VisualizationValidationException(
                        team.name() + ": duplicate periods detected."
                    );
                }

                if (scale == ScaleType.LOGARITHMIC
                        && team.values(metric).stream()
                            .anyMatch(value -> value <= 0)) {
                    throw new VisualizationValidationException(
                        team.name()
                        + ": logarithmic visualization contains "
                        + "a non-positive value."
                    );
                }
            }
        }
    }

    static final class PlotService {
        private final VisualizationPolicy policy;

        PlotService(VisualizationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        PlotDefinition createPlot(
            List<TeamSeries> teams,
            Metric metric,
            ScaleType scale,
            String title
        ) {
            policy.validate(teams, metric, scale);

            List<Double> allValues = teams.stream()
                .flatMap(team -> team.values(metric).stream())
                .toList();

            double minimum = Collections.min(allValues);
            double maximum = Collections.max(allValues);

            if (minimum == maximum) {
                double padding = Math.max(1.0, Math.abs(minimum) * 0.1);
                minimum -= padding;
                maximum += padding;
            }

            List<Annotation> annotations = new ArrayList<>();

            for (TeamSeries team : teams) {
                List<Double> values = team.values(metric);

                int maxIndex = 0;
                for (int index = 1; index < values.size(); index++) {
                    if (values.get(index) > values.get(maxIndex)) {
                        maxIndex = index;
                    }
                }

                annotations.add(
                    new Annotation(
                        team.name() + " maximum",
                        maxIndex,
                        values.get(maxIndex)
                    )
                );
            }

            AxisPolicy axis = new AxisPolicy(
                title,
                "Month",
                metricLabel(metric),
                scale,
                minimum,
                maximum
            );

            return new PlotDefinition(
                title,
                axis,
                teams.stream().map(TeamSeries::name).toList(),
                annotations
            );
        }

        private static String metricLabel(Metric metric) {
            return switch (metric) {
                case DEPLOYMENTS -> "Deployments";
                case INCIDENTS -> "Incidents";
                case LEAD_TIME_HOURS -> "Lead Time (hours)";
                case COVERAGE_PERCENT -> "Coverage (%)";
            };
        }
    }

    static final class VisualizationReport {
        static void print(PlotDefinition plot) {
            System.out.println("\n" + plot.title());
            System.out.println("=".repeat(plot.title().length()));

            AxisPolicy axis = plot.axis();

            System.out.printf(
                "Scale: %s%n",
                axis.scale()
            );

            System.out.printf(
                "Y range: %.2f to %.2f%n",
                axis.minimum(),
                axis.maximum()
            );

            System.out.println(
                "Legend: " + String.join(", ", plot.legendEntries())
            );

            System.out.println("Annotations:");
            plot.annotations().forEach(annotation ->
                System.out.printf(
                    "  %s at period %d = %.2f%n",
                    annotation.label(),
                    annotation.periodIndex(),
                    annotation.value()
                )
            );
        }
    }

    static List<TeamSeries> createDataset() {
        return List.of(
            new TeamSeries(
                "Platform",
                List.of(
                    new MonthlyMetric("Jan", 42, 8, 18.0, 76),
                    new MonthlyMetric("Feb", 48, 7, 16.0, 79),
                    new MonthlyMetric("Mar", 53, 6, 14.0, 82),
                    new MonthlyMetric("Apr", 61, 5, 12.0, 85),
                    new MonthlyMetric("May", 67, 4, 10.5, 88),
                    new MonthlyMetric("Jun", 74, 4, 9.2, 91)
                )
            ),
            new TeamSeries(
                "Payments",
                List.of(
                    new MonthlyMetric("Jan", 31, 10, 24.0, 71),
                    new MonthlyMetric("Feb", 35, 9, 22.0, 74),
                    new MonthlyMetric("Mar", 39, 8, 19.0, 77),
                    new MonthlyMetric("Apr", 44, 7, 17.0, 80),
                    new MonthlyMetric("May", 49, 6, 15.0, 83),
                    new MonthlyMetric("Jun", 55, 5, 13.5, 86)
                )
            ),
            new TeamSeries(
                "Analytics",
                List.of(
                    new MonthlyMetric("Jan", 25, 5, 20.0, 81),
                    new MonthlyMetric("Feb", 28, 5, 18.0, 83),
                    new MonthlyMetric("Mar", 34, 4, 15.5, 86),
                    new MonthlyMetric("Apr", 38, 3, 13.0, 89),
                    new MonthlyMetric("May", 43, 3, 11.5, 92),
                    new MonthlyMetric("Jun", 47, 2, 10.0, 94)
                )
            )
        );
    }

    static void printSubplotModel() {
        Map<Integer, String> panels = Map.of(
            1, "Deployment trend",
            2, "Incident comparison",
            3, "Lead-time logarithmic scale",
            4, "Coverage trend"
        );

        System.out.println("\nEnterprise dashboard layout");
        panels.forEach((position, name) ->
            System.out.printf(
                "Panel %d: %s%n",
                position,
                name
            )
        );
    }

    public static void main(String[] args) {
        List<TeamSeries> teams = createDataset();

        VisualizationPolicy policy =
            new DefaultVisualizationPolicy();

        PlotService service = new PlotService(policy);

        PlotDefinition deployments = service.createPlot(
            teams,
            Metric.DEPLOYMENTS,
            ScaleType.LINEAR,
            "Monthly Deployments"
        );

        PlotDefinition leadTime = service.createPlot(
            teams,
            Metric.LEAD_TIME_HOURS,
            ScaleType.LOGARITHMIC,
            "Lead Time"
        );

        VisualizationReport.print(deployments);
        VisualizationReport.print(leadTime);
        printSubplotModel();

        Optional<TeamSeries> analytics = teams.stream()
            .filter(team -> team.name().equals("Analytics"))
            .findFirst();

        analytics.ifPresent(team ->
            System.out.printf(
                "%nSelected team: %s, final coverage: %.1f%%%n",
                team.name(),
                team.metrics().getLast().coveragePercent()
            )
        );

        System.out.println(
            "\nVisualization policy validation completed successfully."
        );
    }
}
