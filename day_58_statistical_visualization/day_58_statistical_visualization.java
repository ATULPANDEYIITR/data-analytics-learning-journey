import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class StatisticalVisualization {

    enum PlotType {
        HISTOGRAM,
        BOX,
        VIOLIN,
        SCATTER,
        DENSITY,
        CATEGORICAL
    }

    static final class VisualizationException extends RuntimeException {
        VisualizationException(String message) {
            super(message);
        }
    }

    record FiveNumberSummary(
            double minimum,
            double q1,
            double median,
            double q3,
            double maximum,
            double lowerFence,
            double upperFence,
            List<Double> outliers
    ) {}

    record CategorySummary(
            String category,
            int count,
            double percentage
    ) {}

    static final class NumericDataset {
        private final List<Double> values;

        NumericDataset(List<Double> values) {
            Objects.requireNonNull(values, "values");

            if (values.isEmpty()) {
                throw new VisualizationException("Dataset cannot be empty.");
            }

            for (Double value : values) {
                if (value == null || !Double.isFinite(value)) {
                    throw new VisualizationException(
                            "Dataset values must be finite numbers."
                    );
                }
            }

            this.values = List.copyOf(values);
        }

        List<Double> values() {
            return values;
        }

        int size() {
            return values.size();
        }

        double mean() {
            return values.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElseThrow();
        }

        double standardDeviation() {
            double average = mean();

            return Math.sqrt(
                    values.stream()
                            .mapToDouble(value ->
                                    Math.pow(value - average, 2))
                            .average()
                            .orElse(0.0)
            );
        }

        double percentile(double percentage) {
            if (percentage < 0 || percentage > 100) {
                throw new VisualizationException(
                        "Percentile must be between 0 and 100."
                );
            }

            List<Double> sorted = new ArrayList<>(values);
            sorted.sort(Comparator.naturalOrder());

            double position =
                    (sorted.size() - 1) * percentage / 100.0;

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            if (lower == upper) {
                return sorted.get(lower);
            }

            double fraction = position - lower;

            return sorted.get(lower)
                    + (sorted.get(upper) - sorted.get(lower)) * fraction;
        }

        FiveNumberSummary fiveNumberSummary() {
            double minimum = values.stream()
                    .mapToDouble(Double::doubleValue)
                    .min()
                    .orElseThrow();

            double maximum = values.stream()
                    .mapToDouble(Double::doubleValue)
                    .max()
                    .orElseThrow();

            double q1 = percentile(25);
            double median = percentile(50);
            double q3 = percentile(75);
            double iqr = q3 - q1;

            double lowerFence = q1 - 1.5 * iqr;
            double upperFence = q3 + 1.5 * iqr;

            List<Double> outliers = values.stream()
                    .filter(value ->
                            value < lowerFence || value > upperFence)
                    .toList();

            return new FiveNumberSummary(
                    minimum,
                    q1,
                    median,
                    q3,
                    maximum,
                    lowerFence,
                    upperFence,
                    outliers
            );
        }

        List<double[]> kernelDensity(int points) {
            if (points < 2) {
                throw new VisualizationException(
                        "Density requires at least two points."
                );
            }

            FiveNumberSummary summary = fiveNumberSummary();

            double sigma = standardDeviation();

            if (sigma == 0.0) {
                sigma = Math.max(Math.abs(summary.minimum()) * 0.05, 1.0);
            }

            double bandwidth =
                    1.06 * sigma * Math.pow(size(), -0.2);

            bandwidth = Math.max(bandwidth, 1e-9);

            double start =
                    summary.minimum() - 3.0 * bandwidth;

            double end =
                    summary.maximum() + 3.0 * bandwidth;

            double normalizer =
                    size() * bandwidth * Math.sqrt(2 * Math.PI);

            List<double[]> result = new ArrayList<>();

            for (int i = 0; i < points; i++) {
                double x =
                        start + (end - start) * i / (points - 1);

                double density = 0.0;

                for (double value : values) {
                    double z = (x - value) / bandwidth;
                    density += Math.exp(-0.5 * z * z);
                }

                density /= normalizer;
                result.add(new double[]{x, density});
            }

            return result;
        }
    }

    interface PlotRenderer {
        void render(StringBuilder svg);
    }

    static final class BoxPlotRenderer implements PlotRenderer {
        private final NumericDataset data;

        BoxPlotRenderer(NumericDataset data) {
            this.data = data;
        }

        @Override
        public void render(StringBuilder svg) {
            FiveNumberSummary summary =
                    data.fiveNumberSummary();

            double x = 400;
            double y = 70;
            double width = 300;
            double height = 220;

            double minimum = summary.minimum();
            double maximum = summary.maximum();

            if (minimum == maximum) {
                minimum -= 1;
                maximum += 1;
            }

            double centerY = y + height / 2;

            java.util.function.DoubleFunction<Double> scale =
                    value -> x +
                            (value - minimum) /
                            (maximum - minimum) *
                            width;

            svg.append("<line x1=\"")
                    .append(scale.apply(summary.minimum()))
                    .append("\" y1=\"").append(centerY)
                    .append("\" x2=\"")
                    .append(scale.apply(summary.q1()))
                    .append("\" y2=\"").append(centerY)
                    .append("\" stroke=\"black\"/>");

            svg.append("<line x1=\"")
                    .append(scale.apply(summary.q3()))
                    .append("\" y1=\"").append(centerY)
                    .append("\" x2=\"")
                    .append(scale.apply(summary.maximum()))
                    .append("\" y2=\"").append(centerY)
                    .append("\" stroke=\"black\"/>");

            svg.append("<rect x=\"")
                    .append(scale.apply(summary.q1()))
                    .append("\" y=\"").append(y + height * .25)
                    .append("\" width=\"")
                    .append(scale.apply(summary.q3())
                            - scale.apply(summary.q1()))
                    .append("\" height=\"").append(height * .5)
                    .append("\" fill=\"#72b7b2\" stroke=\"black\"/>");

            svg.append("<line x1=\"")
                    .append(scale.apply(summary.median()))
                    .append("\" y1=\"").append(y + height * .25)
                    .append("\" x2=\"")
                    .append(scale.apply(summary.median()))
                    .append("\" y2=\"").append(y + height * .75)
                    .append("\" stroke=\"black\" stroke-width=\"2\"/>");

            for (double outlier : summary.outliers()) {
                svg.append("<circle cx=\"")
                        .append(scale.apply(outlier))
                        .append("\" cy=\"").append(centerY)
                        .append("\" r=\"4\" fill=\"#e45756\"/>");
            }

            svg.append("<text x=\"400\" y=\"62\" ")
                    .append("font-family=\"sans-serif\">Box Plot</text>");
        }
    }

    static final class GovernanceReport {
        private final EnumMap<PlotType, PlotRenderer> renderers =
                new EnumMap<>(PlotType.class);

        void register(PlotType type, PlotRenderer renderer) {
            renderers.put(type, renderer);
        }

        void renderAll(StringBuilder svg) {
            renderers.values().forEach(renderer -> renderer.render(svg));
        }
    }

    static void axes(
            StringBuilder svg,
            double x,
            double y,
            double width,
            double height
    ) {
        svg.append("<line x1=\"")
                .append(x)
                .append("\" y1=\"")
                .append(y + height)
                .append("\" x2=\"")
                .append(x + width)
                .append("\" y2=\"")
                .append(y + height)
                .append("\" stroke=\"black\"/>");

        svg.append("<line x1=\"")
                .append(x)
                .append("\" y1=\"")
                .append(y)
                .append("\" x2=\"")
                .append(x)
                .append("\" y2=\"")
                .append(y + height)
                .append("\" stroke=\"black\"/>");
    }

    static void renderHistogram(
            StringBuilder svg,
            NumericDataset data
    ) {
        double x = 50;
        double y = 70;
        double width = 300;
        double height = 220;
        int bins = 8;

        double minimum = data.values().stream()
                .mapToDouble(Double::doubleValue)
                .min()
                .orElseThrow();

        double maximum = data.values().stream()
                .mapToDouble(Double::doubleValue)
                .max()
                .orElseThrow();

        axes(svg, x, y, width, height);

        double range = maximum - minimum;

        if (range == 0) {
            range = 1;
            maximum = minimum + range;
        }

        double binWidth = range / bins;
        int[] counts = new int[bins];

        for (double value : data.values()) {
            int index = (int) Math.floor(
                    (value - minimum) / binWidth
            );
            index = Math.min(index, bins - 1);
            counts[index]++;
        }

        int maximumCount = 0;
        for (int count : counts) {
            maximumCount = Math.max(maximumCount, count);
        }

        for (int i = 0; i < bins; i++) {
            double barHeight =
                    maximumCount == 0
                            ? 0
                            : height * counts[i] / maximumCount;

            double bx = x + i * width / bins;
            double by = y + height - barHeight;

            svg.append("<rect x=\"").append(bx)
                    .append("\" y=\"").append(by)
                    .append("\" width=\"")
                    .append(width / bins - 2)
                    .append("\" height=\"").append(barHeight)
                    .append("\" fill=\"#4c78a8\"/>");
        }

        svg.append("<text x=\"50\" y=\"62\" ")
                .append("font-family=\"sans-serif\">Histogram</text>");
    }

    static void renderViolin(
            StringBuilder svg,
            NumericDataset data
    ) {
        double x = 750;
        double y = 70;
        double width = 300;
        double height = 220;

        List<double[]> density = data.kernelDensity(60);

        double maxDensity = density.stream()
                .mapToDouble(point -> point[1])
                .max()
                .orElse(1.0);

        double minimum = density.getFirst()[0];
        double maximum = density.getLast()[0];
        double center = x + width / 2;

        List<String> left = new ArrayList<>();
        List<String> right = new ArrayList<>();

        for (double[] point : density) {
            double py =
                    y + height -
                    (point[0] - minimum) /
                            (maximum - minimum) * height;

            double half =
                    point[1] / maxDensity * width * .45;

            left.add((center - half) + "," + py);
            right.add((center + half) + "," + py);
        }

        StringBuilder polygon = new StringBuilder();

        left.forEach(point ->
                polygon.append(point).append(" "));

        for (int i = right.size() - 1; i >= 0; i--) {
            polygon.append(right.get(i)).append(" ");
        }

        svg.append("<polygon points=\"")
                .append(polygon)
                .append("\" fill=\"#f2cf5b\" stroke=\"black\"/>");

        svg.append("<text x=\"750\" y=\"62\" ")
                .append("font-family=\"sans-serif\">Violin Plot</text>");
    }

    static void renderScatter(
            StringBuilder svg,
            NumericDataset xData,
            NumericDataset yData
    ) {
        if (xData.size() != yData.size()) {
            throw new VisualizationException(
                    "Scatter datasets must have equal lengths."
            );
        }

        double x = 50;
        double y = 390;
        double width = 300;
        double height = 220;

        axes(svg, x, y, width, height);

        double xmin = xData.values().stream()
                .mapToDouble(Double::doubleValue).min().orElseThrow();
        double xmax = xData.values().stream()
                .mapToDouble(Double::doubleValue).max().orElseThrow();
        double ymin = yData.values().stream()
                .mapToDouble(Double::doubleValue).min().orElseThrow();
        double ymax = yData.values().stream()
                .mapToDouble(Double::doubleValue).max().orElseThrow();

        double xRange = xmax == xmin ? 1 : xmax - xmin;
        double yRange = ymax == ymin ? 1 : ymax - ymin;

        for (int i = 0; i < xData.size(); i++) {
            double px =
                    x + (xData.values().get(i) - xmin) /
                            xRange * width;

            double py =
                    y + height -
                            (yData.values().get(i) - ymin) /
                                    yRange * height;

            svg.append("<circle cx=\"")
                    .append(px)
                    .append("\" cy=\"")
                    .append(py)
                    .append("\" r=\"3.5\" fill=\"#54a24b\"/>");
        }

        svg.append("<text x=\"50\" y=\"382\" ")
                .append("font-family=\"sans-serif\">Scatter Plot</text>");
    }

    static void renderDensity(
            StringBuilder svg,
            NumericDataset data
    ) {
        double x = 400;
        double y = 390;
        double width = 300;
        double height = 220;

        List<double[]> density = data.kernelDensity(80);

        double maxDensity = density.stream()
                .mapToDouble(point -> point[1])
                .max()
                .orElse(1.0);

        double minimum = density.getFirst()[0];
        double maximum = density.getLast()[0];

        axes(svg, x, y, width, height);

        svg.append("<polyline points=\"");

        for (double[] point : density) {
            double px =
                    x + (point[0] - minimum) /
                            (maximum - minimum) * width;

            double py =
                    y + height -
                            point[1] / maxDensity * height;

            svg.append(px)
                    .append(",")
                    .append(py)
                    .append(" ");
        }

        svg.append("\" fill=\"none\" stroke=\"#b279a2\" stroke-width=\"2\"/>");

        svg.append("<text x=\"400\" y=\"382\" ")
                .append("font-family=\"sans-serif\">Density Plot</text>");
    }

    static void renderCategorical(
            StringBuilder svg,
            List<String> categories
    ) {
        if (categories.isEmpty()) {
            throw new VisualizationException(
                    "Categorical data cannot be empty."
            );
        }

        Map<String, Long> counts = categories.stream()
                .map(String::trim)
                .peek(category -> {
                    if (category.isEmpty()) {
                        throw new VisualizationException(
                                "Category labels cannot be empty."
                        );
                    }
                })
                .collect(
                        java.util.stream.Collectors.groupingBy(
                                value -> value,
                                LinkedHashMap::new,
                                java.util.stream.Collectors.counting()
                        )
                );

        double x = 750;
        double y = 390;
        double width = 300;
        double height = 220;

        axes(svg, x, y, width, height);

        long maximum = counts.values().stream()
                .mapToLong(Long::longValue)
                .max()
                .orElse(1);

        double barWidth = width / counts.size();
        int index = 0;

        for (Map.Entry<String, Long> entry : counts.entrySet()) {
            double barHeight =
                    height * entry.getValue() / maximum;

            double bx =
                    x + index * barWidth + 4;

            double by =
                    y + height - barHeight;

            svg.append("<rect x=\"").append(bx)
                    .append("\" y=\"").append(by)
                    .append("\" width=\"").append(barWidth - 8)
                    .append("\" height=\"").append(barHeight)
                    .append("\" fill=\"#ff9da6\"/>");

            svg.append("<text x=\"").append(bx)
                    .append("\" y=\"").append(y + height + 18)
                    .append("\" font-family=\"sans-serif\" font-size=\"11\">")
                    .append(entry.getKey())
                    .append("</text>");

            index++;
        }

        svg.append("<text x=\"750\" y=\"382\" ")
                .append("font-family=\"sans-serif\">Categorical Plot</text>");
    }

    public static void main(String[] args) {
        NumericDataset measurements = new NumericDataset(List.of(
                42.0, 45.0, 47.0, 48.0, 49.0,
                50.0, 51.0, 52.0, 52.0, 53.0,
                54.0, 55.0, 56.0, 57.0, 58.0,
                59.0, 61.0, 62.0, 63.0, 65.0,
                68.0, 70.0, 74.0, 79.0, 91.0
        ));

        List<Double> xValues = new ArrayList<>();

        for (int i = 1; i <= measurements.size(); i++) {
            xValues.add((double) i);
        }

        NumericDataset xData = new NumericDataset(xValues);

        List<String> categories = List.of(
                "API", "API", "Web", "Web", "Web", "Mobile", "API",
                "Mobile", "Web", "API", "Desktop", "Web", "Mobile", "API"
        );

        StringBuilder svg = new StringBuilder();

        svg.append("""
                <svg xmlns="http://www.w3.org/2000/svg"
                     width="1100" height="900"
                     viewBox="0 0 1100 900">
                <rect width="100%" height="100%" fill="white"/>
                <text x="30" y="32" font-family="sans-serif"
                      font-size="20" font-weight="bold">
                    Statistical Visualization Report
                </text>
                """);

        renderHistogram(svg, measurements);
        new BoxPlotRenderer(measurements).render(svg);
        renderViolin(svg, measurements);
        renderScatter(svg, xData, measurements);
        renderDensity(svg, measurements);
        renderCategorical(svg, categories);

        FiveNumberSummary summary =
                measurements.fiveNumberSummary();

        svg.append("<text x=\"50\" y=\"680\" ")
                .append("font-family=\"sans-serif\" font-size=\"14\">")
                .append("Count: ").append(measurements.size())
                .append(" | Mean: ").append("%.2f".formatted(measurements.mean()))
                .append(" | SD: ")
                .append("%.2f".formatted(measurements.standardDeviation()))
                .append("</text>");

        svg.append("<text x=\"50\" y=\"710\" ")
                .append("font-family=\"sans-serif\" font-size=\"14\">")
                .append("Q1: ").append("%.2f".formatted(summary.q1()))
                .append(" | Median: ").append("%.2f".formatted(summary.median()))
                .append(" | Q3: ").append("%.2f".formatted(summary.q3()))
                .append(" | Outliers: ").append(summary.outliers().size())
                .append("</text>");

        svg.append("</svg>");

        try {
            Files.writeString(
                    Path.of("statistical_visualization_report_java.svg"),
                    svg.toString()
            );
        } catch (IOException error) {
            throw new VisualizationException(
                    "Unable to write SVG: " + error.getMessage()
            );
        }

        if (summary.outliers().isEmpty()) {
            throw new VisualizationException(
                    "Expected the sample to contain an IQR outlier."
            );
        }

        System.out.println(
                "Wrote statistical_visualization_report_java.svg"
        );
        System.out.printf(
                "n=%d, mean=%.2f, sd=%.2f, outliers=%d%n",
                measurements.size(),
                measurements.mean(),
                measurements.standardDeviation(),
                summary.outliers().size()
        );
    }
}
