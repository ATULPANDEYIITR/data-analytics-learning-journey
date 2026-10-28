#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

class VisualizationError : public runtime_error {
public:
    explicit VisualizationError(const string& message)
        : runtime_error(message) {}
};

struct FiveNumberSummary {
    double minimum{};
    double q1{};
    double median{};
    double q3{};
    double maximum{};
    double lowerFence{};
    double upperFence{};
    vector<double> outliers;
};

struct Histogram {
    vector<double> edges;
    vector<int> counts;
};

class NumericDataset {
private:
    vector<double> values_;

    static void validate(const vector<double>& values) {
        if (values.empty()) {
            throw VisualizationError("Dataset cannot be empty.");
        }

        for (double value : values) {
            if (!isfinite(value)) {
                throw VisualizationError("Dataset contains a non-finite value.");
            }
        }
    }

public:
    explicit NumericDataset(vector<double> values)
        : values_(move(values)) {
        validate(values_);
    }

    const vector<double>& values() const {
        return values_;
    }

    size_t size() const {
        return values_.size();
    }

    double mean() const {
        return accumulate(values_.begin(), values_.end(), 0.0) / size();
    }

    double standardDeviation() const {
        const double average = mean();
        double sum = 0.0;

        for (double value : values_) {
            const double difference = value - average;
            sum += difference * difference;
        }

        return sqrt(sum / static_cast<double>(size()));
    }

    double percentile(double p) const {
        if (p < 0.0 || p > 100.0) {
            throw VisualizationError("Percentile must be between 0 and 100.");
        }

        vector<double> sorted = values_;
        sort(sorted.begin(), sorted.end());

        const double position =
            (sorted.size() - 1) * p / 100.0;

        const size_t lower = static_cast<size_t>(floor(position));
        const size_t upper = static_cast<size_t>(ceil(position));

        if (lower == upper) {
            return sorted[lower];
        }

        const double fraction = position - lower;
        return sorted[lower] +
               (sorted[upper] - sorted[lower]) * fraction;
    }

    FiveNumberSummary fiveNumberSummary() const {
        FiveNumberSummary summary;
        summary.minimum = *min_element(values_.begin(), values_.end());
        summary.q1 = percentile(25.0);
        summary.median = percentile(50.0);
        summary.q3 = percentile(75.0);
        summary.maximum = *max_element(values_.begin(), values_.end());

        const double iqr = summary.q3 - summary.q1;
        summary.lowerFence = summary.q1 - 1.5 * iqr;
        summary.upperFence = summary.q3 + 1.5 * iqr;

        for (double value : values_) {
            if (value < summary.lowerFence ||
                value > summary.upperFence) {
                summary.outliers.push_back(value);
            }
        }

        return summary;
    }

    Histogram histogram(size_t bins) const {
        if (bins == 0) {
            throw VisualizationError("Histogram requires at least one bin.");
        }

        const double minimum =
            *min_element(values_.begin(), values_.end());
        const double maximum =
            *max_element(values_.begin(), values_.end());

        Histogram result;
        result.counts.assign(bins, 0);

        if (minimum == maximum) {
            result.edges.resize(bins + 1);
            for (size_t i = 0; i <= bins; ++i) {
                result.edges[i] = minimum - 0.5 + static_cast<double>(i);
            }
            result.counts[0] = static_cast<int>(size());
            return result;
        }

        const double width = (maximum - minimum) / bins;
        result.edges.resize(bins + 1);

        for (size_t i = 0; i <= bins; ++i) {
            result.edges[i] = minimum + width * i;
        }

        for (double value : values_) {
            size_t index = static_cast<size_t>(
                floor((value - minimum) / width)
            );

            index = min(index, bins - 1);
            ++result.counts[index];
        }

        return result;
    }

    vector<pair<double, double>> kde(size_t points = 80) const {
        if (points < 2) {
            throw VisualizationError(
                "Density requires at least two evaluation points."
            );
        }

        const auto summary = fiveNumberSummary();
        double sigma = standardDeviation();

        if (sigma == 0.0) {
            sigma = max(abs(summary.minimum) * 0.05, 1.0);
        }

        double bandwidth =
            1.06 * sigma * pow(static_cast<double>(size()), -0.2);

        bandwidth = max(bandwidth, 1e-9);

        const double start = summary.minimum - 3.0 * bandwidth;
        const double end = summary.maximum + 3.0 * bandwidth;
        const double normalizer =
            size() * bandwidth * sqrt(2.0 * M_PI);

        vector<pair<double, double>> result;
        result.reserve(points);

        for (size_t i = 0; i < points; ++i) {
            const double x =
                start + (end - start) * i / (points - 1);

            double density = 0.0;

            for (double value : values_) {
                const double z = (x - value) / bandwidth;
                density += exp(-0.5 * z * z);
            }

            density /= normalizer;
            result.emplace_back(x, density);
        }

        return result;
    }
};

string escapeXml(const string& value) {
    string result;

    for (char character : value) {
        switch (character) {
            case '&': result += "&amp;"; break;
            case '<': result += "&lt;"; break;
            case '>': result += "&gt;"; break;
            case '"': result += "&quot;"; break;
            default: result += character;
        }
    }

    return result;
}

void axes(ostream& out, double x, double y, double width, double height) {
    out << "<line x1=\"" << x
        << "\" y1=\"" << y + height
        << "\" x2=\"" << x + width
        << "\" y2=\"" << y + height
        << "\" stroke=\"black\"/>\n";

    out << "<line x1=\"" << x
        << "\" y1=\"" << y
        << "\" x2=\"" << x
        << "\" y2=\"" << y + height
        << "\" stroke=\"black\"/>\n";
}

void drawHistogram(
    ostream& out,
    const NumericDataset& data,
    double x,
    double y,
    double width,
    double height
) {
    const Histogram histogram = data.histogram(8);
    axes(out, x, y, width, height);

    const int maximum =
        *max_element(histogram.counts.begin(), histogram.counts.end());

    const double barWidth =
        width / static_cast<double>(histogram.counts.size());

    for (size_t i = 0; i < histogram.counts.size(); ++i) {
        const double barHeight =
            maximum == 0
                ? 0.0
                : height * histogram.counts[i] / maximum;

        const double bx = x + i * barWidth;
        const double by = y + height - barHeight;

        out << "<rect x=\"" << bx
            << "\" y=\"" << by
            << "\" width=\"" << barWidth - 2
            << "\" height=\"" << barHeight
            << "\" fill=\"#4c78a8\"/>\n";
    }

    out << "<text x=\"" << x << "\" y=\"" << y - 8
        << "\" font-family=\"sans-serif\">Histogram</text>\n";
}

void drawBox(
    ostream& out,
    const NumericDataset& data,
    double x,
    double y,
    double width,
    double height
) {
    const auto summary = data.fiveNumberSummary();
    axes(out, x, y, width, height);

    double minimum = summary.minimum;
    double maximum = summary.maximum;

    if (minimum == maximum) {
        minimum -= 1.0;
        maximum += 1.0;
    }

    const auto scale = [&](double value) {
        return x + (value - minimum) / (maximum - minimum) * width;
    };

    const double centerY = y + height / 2.0;
    const double q1 = scale(summary.q1);
    const double q3 = scale(summary.q3);

    out << "<line x1=\"" << scale(summary.minimum)
        << "\" y1=\"" << centerY
        << "\" x2=\"" << q1
        << "\" y2=\"" << centerY
        << "\" stroke=\"black\"/>\n";

    out << "<line x1=\"" << q3
        << "\" y1=\"" << centerY
        << "\" x2=\"" << scale(summary.maximum)
        << "\" y2=\"" << centerY
        << "\" stroke=\"black\"/>\n";

    out << "<rect x=\"" << q1
        << "\" y=\"" << y + height * .25
        << "\" width=\"" << q3 - q1
        << "\" height=\"" << height * .5
        << "\" fill=\"#72b7b2\" stroke=\"black\"/>\n";

    out << "<line x1=\"" << scale(summary.median)
        << "\" y1=\"" << y + height * .25
        << "\" x2=\"" << scale(summary.median)
        << "\" y2=\"" << y + height * .75
        << "\" stroke=\"black\" stroke-width=\"2\"/>\n";

    for (double outlier : summary.outliers) {
        out << "<circle cx=\"" << scale(outlier)
            << "\" cy=\"" << centerY
            << "\" r=\"4\" fill=\"#e45756\"/>\n";
    }

    out << "<text x=\"" << x << "\" y=\"" << y - 8
        << "\" font-family=\"sans-serif\">Box Plot</text>\n";
}

void drawViolin(
    ostream& out,
    const NumericDataset& data,
    double x,
    double y,
    double width,
    double height
) {
    const auto density = data.kde(60);
    const double maximumDensity = max_element(
        density.begin(), density.end(),
        [](const auto& a, const auto& b) {
            return a.second < b.second;
        }
    )->second;

    const double minimum = density.front().first;
    const double maximum = density.back().first;
    const double center = x + width / 2.0;

    vector<pair<double, double>> left;
    vector<pair<double, double>> right;

    for (const auto& [value, densityValue] : density) {
        const double py =
            y + height -
            (value - minimum) / (maximum - minimum) * height;

        const double halfWidth =
            densityValue / maximumDensity * width * 0.45;

        left.emplace_back(center - halfWidth, py);
        right.emplace_back(center + halfWidth, py);
    }

    out << "<polygon points=\"";

    for (const auto& point : left) {
        out << point.first << "," << point.second << " ";
    }

    for (auto it = right.rbegin(); it != right.rend(); ++it) {
        out << it->first << "," << it->second << " ";
    }

    out << "\" fill=\"#f2cf5b\" stroke=\"black\"/>\n";

    out << "<text x=\"" << x << "\" y=\"" << y - 8
        << "\" font-family=\"sans-serif\">Violin Plot</text>\n";
}

void drawScatter(
    ostream& out,
    const NumericDataset& xData,
    const NumericDataset& yData,
    double x,
    double y,
    double width,
    double height
) {
    if (xData.size() != yData.size()) {
        throw VisualizationError(
            "Scatter datasets must have equal lengths."
        );
    }

    const auto& xs = xData.values();
    const auto& ys = yData.values();

    const double xmin = *min_element(xs.begin(), xs.end());
    const double xmax = *max_element(xs.begin(), xs.end());
    const double ymin = *min_element(ys.begin(), ys.end());
    const double ymax = *max_element(ys.begin(), ys.end());

    const double xrange = xmax == xmin ? 1.0 : xmax - xmin;
    const double yrange = ymax == ymin ? 1.0 : ymax - ymin;

    axes(out, x, y, width, height);

    for (size_t i = 0; i < xs.size(); ++i) {
        const double px =
            x + (xs[i] - xmin) / xrange * width;
        const double py =
            y + height - (ys[i] - ymin) / yrange * height;

        out << "<circle cx=\"" << px
            << "\" cy=\"" << py
            << "\" r=\"3.5\" fill=\"#54a24b\"/>\n";
    }

    out << "<text x=\"" << x << "\" y=\"" << y - 8
        << "\" font-family=\"sans-serif\">Scatter Plot</text>\n";
}

void drawDensity(
    ostream& out,
    const NumericDataset& data,
    double x,
    double y,
    double width,
    double height
) {
    const auto density = data.kde();
    double maximumDensity = 0.0;

    for (const auto& point : density) {
        maximumDensity = max(maximumDensity, point.second);
    }

    const double minimum = density.front().first;
    const double maximum = density.back().first;

    axes(out, x, y, width, height);

    out << "<polyline points=\"";

    for (const auto& [value, densityValue] : density) {
        const double px =
            x + (value - minimum) / (maximum - minimum) * width;

        const double py =
            y + height -
            densityValue / maximumDensity * height;

        out << px << "," << py << " ";
    }

    out << "\" fill=\"none\" stroke=\"#b279a2\" stroke-width=\"2\"/>\n";

    out << "<text x=\"" << x << "\" y=\"" << y - 8
        << "\" font-family=\"sans-serif\">Density Plot</text>\n";
}

void drawCategorical(
    ostream& out,
    const vector<string>& categories,
    double x,
    double y,
    double width,
    double height
) {
    if (categories.empty()) {
        throw VisualizationError("Categorical data cannot be empty.");
    }

    map<string, int> counts;

    for (const string& category : categories) {
        if (category.empty()) {
            throw VisualizationError("Category labels cannot be empty.");
        }
        ++counts[category];
    }

    int maximum = 0;
    for (const auto& [category, count] : counts) {
        maximum = max(maximum, count);
    }

    axes(out, x, y, width, height);

    const double barWidth =
        width / static_cast<double>(counts.size());

    size_t index = 0;

    for (const auto& [category, count] : counts) {
        const double barHeight =
            height * count / maximum;

        const double bx =
            x + index * barWidth + 4;

        const double by =
            y + height - barHeight;

        out << "<rect x=\"" << bx
            << "\" y=\"" << by
            << "\" width=\"" << barWidth - 8
            << "\" height=\"" << barHeight
            << "\" fill=\"#ff9da6\"/>\n";

        out << "<text x=\"" << bx
            << "\" y=\"" << y + height + 18
            << "\" font-family=\"sans-serif\" font-size=\"11\">"
            << escapeXml(category)
            << "</text>\n";

        ++index;
    }

    out << "<text x=\"" << x << "\" y=\"" << y - 8
        << "\" font-family=\"sans-serif\">Categorical Plot</text>\n";
}

int main() {
    try {
        NumericDataset measurements({
            42, 45, 47, 48, 49, 50, 51, 52, 52, 53,
            54, 55, 56, 57, 58, 59, 61, 62, 63, 65,
            68, 70, 74, 79, 91
        });

        vector<double> xValues;
        for (size_t i = 0; i < measurements.size(); ++i) {
            xValues.push_back(static_cast<double>(i + 1));
        }

        NumericDataset xData(xValues);

        vector<string> categories = {
            "API", "API", "Web", "Web", "Web", "Mobile", "API",
            "Mobile", "Web", "API", "Desktop", "Web", "Mobile", "API"
        };

        ofstream output("statistical_visualization_report_cpp.svg");

        if (!output) {
            throw VisualizationError("Unable to open SVG output.");
        }

        output << fixed << setprecision(2);

        output
            << "<svg xmlns=\"http://www.w3.org/2000/svg\" "
            << "width=\"1100\" height=\"900\" viewBox=\"0 0 1100 900\">\n"
            << "<rect width=\"100%\" height=\"100%\" fill=\"white\"/>\n"
            << "<text x=\"30\" y=\"32\" font-family=\"sans-serif\" "
            << "font-size=\"20\" font-weight=\"bold\">"
            << "Statistical Visualization Report</text>\n";

        drawHistogram(output, measurements, 50, 70, 300, 220);
        drawBox(output, measurements, 400, 70, 300, 220);
        drawViolin(output, measurements, 750, 70, 300, 220);
        drawScatter(output, xData, measurements, 50, 390, 300, 220);
        drawDensity(output, measurements, 400, 390, 300, 220);
        drawCategorical(output, categories, 750, 390, 300, 220);

        const auto summary = measurements.fiveNumberSummary();

        output
            << "<text x=\"50\" y=\"680\" font-family=\"sans-serif\" "
            << "font-size=\"14\">"
            << "Count: " << measurements.size()
            << " | Mean: " << measurements.mean()
            << " | SD: " << measurements.standardDeviation()
            << "</text>\n";

        output
            << "<text x=\"50\" y=\"710\" font-family=\"sans-serif\" "
            << "font-size=\"14\">"
            << "Q1: " << summary.q1
            << " | Median: " << summary.median
            << " | Q3: " << summary.q3
            << " | Outliers: " << summary.outliers.size()
            << "</text>\n";

        output << "</svg>\n";

        if (!output) {
            throw VisualizationError("Failed while writing SVG.");
        }

        cout << "Wrote statistical_visualization_report_cpp.svg\n";
        cout << "n=" << measurements.size()
             << ", mean=" << measurements.mean()
             << ", sd=" << measurements.standardDeviation()
             << ", outliers=" << summary.outliers.size()
             << '\n';

        return 0;
    }
    catch (const exception& error) {
        cerr << "Visualization failed: "
             << error.what() << '\n';
        return 1;
    }
}
