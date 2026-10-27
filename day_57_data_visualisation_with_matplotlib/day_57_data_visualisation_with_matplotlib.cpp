#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * C++17 visualization case study.
 *
 * The program implements the analytical side of a visualization pipeline:
 * data validation, scale construction, subplot layout calculation,
 * annotation selection, legend construction, and textual rendering.
 *
 * A rendering engine is kept separate from the data model so that the same
 * validated data can later feed a GUI, plotting library, or export format.
 */

enum class ScaleType {
    Linear,
    Logarithmic
};

enum class Metric {
    Deployments,
    Incidents,
    LeadTimeHours,
    CoveragePercent
};

struct MonthlyRecord {
    std::string month;
    int deployments;
    int incidents;
    double leadTimeHours;
    double coveragePercent;
};

struct TeamSeries {
    std::string name;
    std::vector<MonthlyRecord> records;
};

struct Axis {
    std::string title;
    std::string xLabel;
    std::string yLabel;
    ScaleType scale;
    double yMin;
    double yMax;
};

struct Annotation {
    std::string label;
    std::size_t index;
    double value;
};

struct PlotPanel {
    Axis axis;
    std::vector<std::string> legend;
    std::vector<Annotation> annotations;
};

class VisualizationError : public std::runtime_error {
public:
    explicit VisualizationError(const std::string& message)
        : std::runtime_error(message) {}
};

class VisualizationEngine {
private:
    std::vector<TeamSeries> teams_;

    static bool finite(double value) {
        return std::isfinite(value);
    }

    static void validateMetric(const MonthlyRecord& record,
                               const std::string& team) {
        if (record.deployments < 0) {
            throw VisualizationError(team + ": negative deployment count.");
        }

        if (record.incidents < 0) {
            throw VisualizationError(team + ": negative incident count.");
        }

        if (!finite(record.leadTimeHours) || record.leadTimeHours <= 0.0) {
            throw VisualizationError(
                team + ": lead time must be positive and finite.");
        }

        if (!finite(record.coveragePercent) ||
            record.coveragePercent < 0.0 ||
            record.coveragePercent > 100.0) {
            throw VisualizationError(
                team + ": coverage must be within [0, 100].");
        }
    }

    static double metricValue(const MonthlyRecord& record, Metric metric) {
        switch (metric) {
        case Metric::Deployments:
            return static_cast<double>(record.deployments);
        case Metric::Incidents:
            return static_cast<double>(record.incidents);
        case Metric::LeadTimeHours:
            return record.leadTimeHours;
        case Metric::CoveragePercent:
            return record.coveragePercent;
        }

        throw VisualizationError("Unknown metric.");
    }

    static std::pair<double, double> rangeFor(
        const std::vector<TeamSeries>& teams,
        Metric metric) {

        std::vector<double> values;

        for (const auto& team : teams) {
            for (const auto& record : team.records) {
                values.push_back(metricValue(record, metric));
            }
        }

        if (values.empty()) {
            throw VisualizationError("Cannot calculate range from empty data.");
        }

        auto [minIt, maxIt] =
            std::minmax_element(values.begin(), values.end());

        double minimum = *minIt;
        double maximum = *maxIt;

        if (minimum == maximum) {
            const double padding =
                std::max(1.0, std::abs(minimum) * 0.1);
            minimum -= padding;
            maximum += padding;
        }

        return {minimum, maximum};
    }

    static double normalize(double value,
                            double minimum,
                            double maximum,
                            double outputMinimum,
                            double outputMaximum,
                            ScaleType scale) {
        if (scale == ScaleType::Logarithmic) {
            if (value <= 0.0 || minimum <= 0.0 || maximum <= 0.0) {
                throw VisualizationError(
                    "Logarithmic scale requires positive values.");
            }

            value = std::log10(value);
            minimum = std::log10(minimum);
            maximum = std::log10(maximum);
        }

        if (maximum == minimum) {
            return (outputMinimum + outputMaximum) / 2.0;
        }

        return outputMinimum +
               ((value - minimum) / (maximum - minimum)) *
                   (outputMaximum - outputMinimum);
    }

public:
    explicit VisualizationEngine(std::vector<TeamSeries> teams)
        : teams_(std::move(teams)) {
        validate();
    }

    void validate() const {
        if (teams_.empty()) {
            throw VisualizationError("At least one team is required.");
        }

        const std::size_t expectedSize = teams_.front().records.size();

        if (expectedSize == 0) {
            throw VisualizationError("At least one monthly record is required.");
        }

        for (const auto& team : teams_) {
            if (team.name.empty()) {
                throw VisualizationError("Team name cannot be empty.");
            }

            if (team.records.size() != expectedSize) {
                throw VisualizationError(
                    "All teams must have the same number of periods.");
            }

            std::map<std::string, int> monthCounts;

            for (const auto& record : team.records) {
                ++monthCounts[record.month];
                validateMetric(record, team.name);
            }

            for (const auto& [month, count] : monthCounts) {
                if (count != 1) {
                    throw VisualizationError(
                        team.name + ": duplicate month " + month + ".");
                }
            }
        }
    }

    PlotPanel buildPanel(Metric metric,
                         const std::string& title,
                         ScaleType scale) const {
        auto [minimum, maximum] = rangeFor(teams_, metric);

        if (scale == ScaleType::Logarithmic && minimum <= 0.0) {
            throw VisualizationError(
                "Selected logarithmic panel contains non-positive data.");
        }

        PlotPanel panel{
            Axis{
                title,
                "Month",
                "Metric value",
                scale,
                minimum,
                maximum
            },
            {},
            {}
        };

        for (const auto& team : teams_) {
            panel.legend.push_back(team.name);

            auto maxIt = std::max_element(
                team.records.begin(),
                team.records.end(),
                [metric](const MonthlyRecord& a,
                         const MonthlyRecord& b) {
                    return metricValue(a, metric) <
                           metricValue(b, metric);
                });

            const std::size_t index =
                static_cast<std::size_t>(
                    std::distance(team.records.begin(), maxIt));

            panel.annotations.push_back(
                Annotation{
                    team.name + " maximum",
                    index,
                    metricValue(*maxIt, metric)
                });
        }

        return panel;
    }

    void printPanel(const PlotPanel& panel) const {
        std::cout << "\n[" << panel.axis.title << "]\n";
        std::cout << "Scale: "
                  << (panel.axis.scale == ScaleType::Linear
                          ? "linear"
                          : "logarithmic")
                  << "\n";

        std::cout << "Range: "
                  << std::fixed << std::setprecision(2)
                  << panel.axis.yMin << " to "
                  << panel.axis.yMax << "\n";

        std::cout << "Legend: ";

        for (std::size_t i = 0; i < panel.legend.size(); ++i) {
            if (i != 0) {
                std::cout << ", ";
            }
            std::cout << panel.legend[i];
        }

        std::cout << "\nAnnotations:\n";

        for (const auto& annotation : panel.annotations) {
            std::cout << "  - " << annotation.label
                      << " at period index " << annotation.index
                      << ", value " << annotation.value << "\n";
        }

        std::cout << "Normalized positions:\n";

        for (const auto& team : teams_) {
            std::cout << "  " << team.name << ": ";

            for (const auto& record : team.records) {
                const double normalized = normalize(
                    metricValue(record, Metric::CoveragePercent),
                    0.0,
                    100.0,
                    0.0,
                    1.0,
                    ScaleType::Linear);

                std::cout << std::setprecision(2)
                          << normalized << " ";
            }

            std::cout << "\n";
        }
    }

    void printSubplotLayout() const {
        constexpr int rows = 2;
        constexpr int columns = 2;
        constexpr double figureWidth = 14.0;
        constexpr double figureHeight = 9.0;
        constexpr double horizontalGap = 0.6;
        constexpr double verticalGap = 0.7;

        const double cellWidth =
            (figureWidth - horizontalGap) / columns;
        const double cellHeight =
            (figureHeight - verticalGap) / rows;

        std::cout << "\nSubplot layout\n";
        std::cout << "Figure: " << figureWidth
                  << " x " << figureHeight << "\n";

        for (int row = 0; row < rows; ++row) {
            for (int column = 0; column < columns; ++column) {
                std::cout << "  Axes[" << row << "][" << column << "] "
                          << "cell=" << cellWidth << "x"
                          << cellHeight << "\n";
            }
        }
    }

    void printPerformanceNotes() const {
        std::size_t pointCount = 0;

        for (const auto& team : teams_) {
            pointCount += team.records.size();
        }

        std::cout << "\nComplexity\n";
        std::cout << "Validated records: " << pointCount << "\n";
        std::cout << "Validation: O(n)\n";
        std::cout << "Metric range: O(n)\n";
        std::cout << "Additional memory for range calculation: O(n)\n";
        std::cout << "The rendering layer can stream points when datasets become large.\n";
    }
};

std::vector<TeamSeries> buildDataset() {
    return {
        {
            "Platform",
            {
                {"Jan", 42, 8, 18.0, 76.0},
                {"Feb", 48, 7, 16.0, 79.0},
                {"Mar", 53, 6, 14.0, 82.0},
                {"Apr", 61, 5, 12.0, 85.0},
                {"May", 67, 4, 10.5, 88.0},
                {"Jun", 74, 4, 9.2, 91.0}
            }
        },
        {
            "Payments",
            {
                {"Jan", 31, 10, 24.0, 71.0},
                {"Feb", 35, 9, 22.0, 74.0},
                {"Mar", 39, 8, 19.0, 77.0},
                {"Apr", 44, 7, 17.0, 80.0},
                {"May", 49, 6, 15.0, 83.0},
                {"Jun", 55, 5, 13.5, 86.0}
            }
        },
        {
            "Analytics",
            {
                {"Jan", 25, 5, 20.0, 81.0},
                {"Feb", 28, 5, 18.0, 83.0},
                {"Mar", 34, 4, 15.5, 86.0},
                {"Apr", 38, 3, 13.0, 89.0},
                {"May", 43, 3, 11.5, 92.0},
                {"Jun", 47, 2, 10.0, 94.0}
            }
        }
    };
}

int main() {
    try {
        VisualizationEngine engine(buildDataset());

        auto deployments = engine.buildPanel(
            Metric::Deployments,
            "Monthly Deployments",
            ScaleType::Linear);

        auto leadTime = engine.buildPanel(
            Metric::LeadTimeHours,
            "Lead Time",
            ScaleType::Logarithmic);

        engine.printPanel(deployments);
        engine.printPanel(leadTime);
        engine.printSubplotLayout();
        engine.printPerformanceNotes();

        std::cout << "\nVisualization model validation passed.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Visualization error: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
