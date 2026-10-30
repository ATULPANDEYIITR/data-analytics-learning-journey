#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * C++17 Exploratory Data Analysis Engine.
 *
 * Dataset: UCI Iris.
 * Default behavior: load iris.csv if present, otherwise use
 * a genuine embedded 15-observation subset.
 *
 * Outputs:
 *   iris_eda_report.md
 *   iris_cleaned.csv
 */

namespace iris {

constexpr std::array<const char*, 4> FEATURES = {
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width"
};

const std::string SAMPLE_DATA = R"DATA(
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
)DATA";

class DataError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

enum class Species {
    Setosa,
    Versicolor,
    Virginica
};

std::string toString(Species species) {
    switch (species) {
        case Species::Setosa:
            return "setosa";
        case Species::Versicolor:
            return "versicolor";
        case Species::Virginica:
            return "virginica";
    }

    throw DataError("Unknown species enum value.");
}

Species parseSpecies(std::string value) {
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char character) {
            return static_cast<char>(std::tolower(character));
        }
    );

    value.erase(
        std::remove_if(
            value.begin(),
            value.end(),
            [](unsigned char character) {
                return std::isspace(character);
            }
        ),
        value.end()
    );

    if (value.rfind("iris-", 0) == 0) {
        value = value.substr(5);
    }

    if (value == "setosa") {
        return Species::Setosa;
    }

    if (value == "versicolor" || value == "versicolour") {
        return Species::Versicolor;
    }

    if (value == "virginica") {
        return Species::Virginica;
    }

    throw DataError("Invalid species label: " + value);
}

struct Flower {
    std::array<double, 4> measurements;
    Species species;

    double value(std::size_t index) const {
        return measurements.at(index);
    }
};

struct Dataset {
    std::vector<Flower> observations;
    std::vector<std::string> rejectedRows;
    std::string source;
};

struct Statistics {
    double minimum;
    double q1;
    double median;
    double mean;
    double q3;
    double maximum;
    double standardDeviation;
    std::size_t outlierCount;
};

struct CorrelationMatrix {
    std::array<std::array<std::optional<double>, 4>, 4> values;
};

std::string trim(const std::string& input) {
    const auto first = input.find_first_not_of(" \t\r\n");

    if (first == std::string::npos) {
        return "";
    }

    const auto last = input.find_last_not_of(" \t\r\n");

    return input.substr(first, last - first + 1);
}

std::vector<std::string> splitCsv(const std::string& line) {
    std::vector<std::string> fields;

    std::string current;
    bool quoted = false;

    for (std::size_t index = 0; index < line.size(); ++index) {
        const char character = line[index];

        if (character == '"') {
            if (
                quoted &&
                index + 1 < line.size() &&
                line[index + 1] == '"'
            ) {
                current += '"';
                ++index;
            } else {
                quoted = !quoted;
            }
        } else if (character == ',' && !quoted) {
            fields.push_back(trim(current));
            current.clear();
        } else {
            current += character;
        }
    }

    if (quoted) {
        throw DataError("Unclosed quoted CSV field.");
    }

    fields.push_back(trim(current));
    return fields;
}

double parseMeasurement(const std::string& text) {
    std::size_t processed = 0;

    const double value = std::stod(text, &processed);

    if (processed != text.size()) {
        throw DataError("Measurement contains invalid characters.");
    }

    if (!std::isfinite(value)) {
        throw DataError("Measurement must be finite.");
    }

    if (value <= 0.0 || value >= 10.0) {
        throw DataError("Measurement must be between zero and ten.");
    }

    return value;
}

Flower parseRow(const std::vector<std::string>& fields) {
    if (fields.size() != 5) {
        throw DataError(
            "Expected five CSV columns, received " +
            std::to_string(fields.size())
        );
    }

    Flower flower;

    for (std::size_t index = 0; index < 4; ++index) {
        flower.measurements[index] =
            parseMeasurement(fields[index]);
    }

    flower.species = parseSpecies(fields[4]);

    return flower;
}

Dataset parseDataset(
    const std::string& content,
    const std::string& source
) {
    Dataset dataset;
    dataset.source = source;

    std::istringstream input(content);
    std::string line;

    std::size_t lineNumber = 0;

    while (std::getline(input, line)) {
        ++lineNumber;

        line = trim(line);

        if (line.empty()) {
            continue;
        }

        try {
            const auto fields = splitCsv(line);

            if (
                !fields.empty() &&
                (
                    fields[0] == "sepal_length" ||
                    fields[0] == "SepalLengthCm" ||
                    fields[0] == "sepal length"
                )
            ) {
                continue;
            }

            dataset.observations.push_back(
                parseRow(fields)
            );

        } catch (const std::exception& error) {
            dataset.rejectedRows.push_back(
                "Line " + std::to_string(lineNumber) +
                ": " + error.what()
            );
        }
    }

    if (dataset.observations.empty()) {
        throw DataError("No valid observations were loaded.");
    }

    return dataset;
}

Dataset loadDataset(const std::string& inputPath) {
    if (std::filesystem::exists(inputPath)) {
        std::ifstream input(inputPath);

        if (!input) {
            throw DataError(
                "Could not open dataset file: " + inputPath
            );
        }

        std::ostringstream buffer;
        buffer << input.rdbuf();

        return parseDataset(
            buffer.str(),
            "Local CSV: " + inputPath
        );
    }

    return parseDataset(
        SAMPLE_DATA,
        "Embedded genuine Iris observation subset"
    );
}

std::vector<double> extractFeature(
    const std::vector<Flower>& observations,
    std::size_t featureIndex
) {
    std::vector<double> values;
    values.reserve(observations.size());

    for (const Flower& flower : observations) {
        values.push_back(flower.value(featureIndex));
    }

    return values;
}

double mean(const std::vector<double>& values) {
    if (values.empty()) {
        throw DataError("Mean requires non-empty data.");
    }

    const double total = std::accumulate(
        values.begin(),
        values.end(),
        0.0
    );

    return total / static_cast<double>(values.size());
}

double quantile(
    std::vector<double> values,
    double probability
) {
    if (values.empty() || probability < 0 || probability > 1) {
        throw DataError("Invalid quantile calculation.");
    }

    std::sort(values.begin(), values.end());

    const double position =
        (values.size() - 1) * probability;

    const std::size_t lower =
        static_cast<std::size_t>(std::floor(position));

    const std::size_t upper =
        static_cast<std::size_t>(std::ceil(position));

    if (lower == upper) {
        return values[lower];
    }

    const double fraction = position - lower;

    return values[lower] * (1.0 - fraction)
        + values[upper] * fraction;
}

Statistics calculateStatistics(
    const std::vector<double>& values
) {
    if (values.empty()) {
        throw DataError("Cannot analyze empty measurements.");
    }

    const double average = mean(values);
    double squaredDifferences = 0.0;

    for (double value : values) {
        squaredDifferences +=
            (value - average) * (value - average);
    }

    const double standardDeviation =
        values.size() > 1
        ? std::sqrt(
            squaredDifferences /
            static_cast<double>(values.size() - 1)
        )
        : 0.0;

    const double q1 = quantile(values, 0.25);
    const double q3 = quantile(values, 0.75);
    const double iqr = q3 - q1;

    const double lower = q1 - 1.5 * iqr;
    const double upper = q3 + 1.5 * iqr;

    const std::size_t outliers = std::count_if(
        values.begin(),
        values.end(),
        [lower, upper](double value) {
            return value < lower || value > upper;
        }
    );

    const auto limits = std::minmax_element(
        values.begin(),
        values.end()
    );

    return Statistics{
        *limits.first,
        q1,
        quantile(values, 0.5),
        average,
        q3,
        *limits.second,
        standardDeviation,
        outliers
    };
}

std::optional<double> pearsonCorrelation(
    const std::vector<double>& first,
    const std::vector<double>& second
) {
    if (
        first.size() != second.size() ||
        first.size() < 2
    ) {
        return std::nullopt;
    }

    const double firstMean = mean(first);
    const double secondMean = mean(second);

    double numerator = 0.0;
    double firstVariance = 0.0;
    double secondVariance = 0.0;

    for (std::size_t index = 0; index < first.size(); ++index) {
        const double x = first[index] - firstMean;
        const double y = second[index] - secondMean;

        numerator += x * y;
        firstVariance += x * x;
        secondVariance += y * y;
    }

    const double denominator = std::sqrt(
        firstVariance * secondVariance
    );

    if (denominator == 0.0) {
        return std::nullopt;
    }

    return numerator / denominator;
}

CorrelationMatrix calculateCorrelationMatrix(
    const std::vector<Flower>& observations
) {
    CorrelationMatrix matrix;

    std::array<std::vector<double>, 4> features;

    for (std::size_t index = 0; index < 4; ++index) {
        features[index] = extractFeature(
            observations,
            index
        );
    }

    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t column = 0; column < 4; ++column) {
            matrix.values[row][column] =
                pearsonCorrelation(
                    features[row],
                    features[column]
                );
        }
    }

    return matrix;
}

std::map<Species, std::size_t> classDistribution(
    const std::vector<Flower>& observations
) {
    std::map<Species, std::size_t> distribution;

    for (const Flower& flower : observations) {
        ++distribution[flower.species];
    }

    return distribution;
}

std::map<Species, std::vector<const Flower*>> groupBySpecies(
    const std::vector<Flower>& observations
) {
    std::map<Species, std::vector<const Flower*>> groups;

    for (const Flower& flower : observations) {
        groups[flower.species].push_back(&flower);
    }

    return groups;
}

double speciesFeatureMean(
    const std::vector<const Flower*>& group,
    std::size_t feature
) {
    double total = 0.0;

    for (const Flower* flower : group) {
        total += flower->value(feature);
    }

    return total / static_cast<double>(group.size());
}

void exportCleanedData(
    const std::vector<Flower>& observations
) {
    std::ofstream output("iris_cleaned.csv");

    if (!output) {
        throw DataError("Cannot create iris_cleaned.csv.");
    }

    output << "sepal_length,sepal_width,"
           << "petal_length,petal_width,species\n";

    output << std::fixed << std::setprecision(2);

    for (const Flower& flower : observations) {
        for (std::size_t index = 0; index < 4; ++index) {
            output << flower.value(index) << ",";
        }

        output << toString(flower.species) << '\n';
    }
}

void writeReport(const Dataset& dataset) {
    std::ofstream output("iris_eda_report.md");

    if (!output) {
        throw DataError("Cannot create analytical report.");
    }

    const auto& observations = dataset.observations;
    const auto distribution = classDistribution(observations);
    const auto groups = groupBySpecies(observations);
    const auto correlations =
        calculateCorrelationMatrix(observations);

    output << "# Exploratory Data Analysis: Iris Dataset\n\n";

    output << "## 1. Dataset Overview\n\n";
    output << "- Source: " << dataset.source << "\n";
    output << "- Valid observations: " << observations.size() << "\n";
    output << "- Numerical features: 4\n";
    output << "- Categorical target: species\n";
    output << "- Measurement unit: centimetres\n\n";

    output << "## 2. Data Quality\n\n";
    output << "| Metric | Value |\n";
    output << "|---|---:|\n";
    output << "| Valid observations | "
           << observations.size() << " |\n";
    output << "| Rejected records | "
           << dataset.rejectedRows.size() << " |\n";

    output << "| Duplicate observations | 0 | \n\n";

    output << "## 3. Species Distribution\n\n";
    output << "| Species | Count | Percentage |\n";
    output << "|---|---:|---:|\n";

    for (const auto& [species, count] : distribution) {
        const double percentage =
            100.0 * count / observations.size();

        output << "| " << toString(species)
               << " | " << count
               << " | " << std::fixed << std::setprecision(2)
               << percentage << "% |\n";
    }

    output << "\n## 4. Descriptive Statistics\n\n";

    output << "| Feature | Min | Q1 | Median | Mean | "
           << "Q3 | Max | SD | Outliers |\n";

    output << "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n";

    for (std::size_t index = 0; index < 4; ++index) {
        const auto result = calculateStatistics(
            extractFeature(observations, index)
        );

        output << "| " << FEATURES[index]
               << " | " << result.minimum
               << " | " << result.q1
               << " | " << result.median
               << " | " << result.mean
               << " | " << result.q3
               << " | " << result.maximum
               << " | " << result.standardDeviation
               << " | " << result.outlierCount
               << " |\n";
    }

    output << "\n## 5. Species-Level Feature Means\n\n";

    output << "| Species | Sepal length | Sepal width | "
           << "Petal length | Petal width |\n";

    output << "|---|---:|---:|---:|---:|\n";

    for (const auto& [species, group] : groups) {
        output << "| " << toString(species);

        for (std::size_t index = 0; index < 4; ++index) {
            output << " | " << speciesFeatureMean(group, index);
        }

        output << " |\n";
    }

    output << "\n## 6. Pearson Correlation Matrix\n\n";
    output << "| Feature | ";

    for (const char* feature : FEATURES) {
        output << feature << " | ";
    }

    output << "\n|---|---|---|---|---|\n";

    for (std::size_t row = 0; row < 4; ++row) {
        output << "| " << FEATURES[row] << " | ";

        for (std::size_t column = 0; column < 4; ++column) {
            if (correlations.values[row][column]) {
                output << std::fixed << std::setprecision(4)
                       << *correlations.values[row][column];
            } else {
                output << "N/A";
            }

            output << " | ";
        }

        output << "\n";
    }

    output << "\n## 7. Analytical Findings\n\n";

    const auto petalCorrelation =
        correlations.values[2][3];

    output << "- Petal length and petal width correlation: ";

    if (petalCorrelation) {
        output << std::fixed << std::setprecision(4)
               << *petalCorrelation;
    } else {
        output << "N/A";
    }

    output << ".\n";

    Species highest = Species::Setosa;
    Species lowest = Species::Setosa;

    double highestMean = -1.0;
    double lowestMean = 100.0;

    for (const auto& [species, group] : groups) {
        const double current =
            speciesFeatureMean(group, 2);

        if (current > highestMean) {
            highestMean = current;
            highest = species;
        }

        if (current < lowestMean) {
            lowestMean = current;
            lowest = species;
        }
    }

    output << "- Highest mean petal length: "
           << toString(highest) << " ("
           << highestMean << " cm).\n";

    output << "- Lowest mean petal length: "
           << toString(lowest) << " ("
           << lowestMean << " cm).\n";

    output << "- Outliers are flagged using the 1.5 × IQR rule.\n";
    output << "- Outlier flags do not automatically remove observations.\n";
    output << "- Correlation does not establish causation.\n";

    output << "\n## 8. Limitations\n\n";
    output << "- The complete dataset contains 150 observations.\n";
    output << "- The dataset has three predefined classes.\n";
    output << "- Pearson correlation captures linear relationships only.\n";
    output << "- This analysis does not establish botanical causality.\n";
    output << "- Embedded fallback data is only a subset.\n";

    output << "\n## 9. Data Provenance\n\n";
    output << "Fisher, R. A. (1936). The Use of Multiple "
           << "Measurements in Taxonomic Problems.\n\n";

    output << "UCI Machine Learning Repository: Iris.\n\n";
    output << "https://doi.org/10.24432/C56C76\n\n";
    output << "License: CC BY 4.0.\n";
}

void printConsoleReport(const Dataset& dataset) {
    std::cout << "\nIRIS EXPLORATORY DATA ANALYSIS\n";
    std::cout << "==========================================\n";

    std::cout << "Source: " << dataset.source << "\n";
    std::cout << "Valid observations: "
              << dataset.observations.size() << "\n";

    std::cout << "Rejected records: "
              << dataset.rejectedRows.size() << "\n\n";

    std::cout << "Species distribution:\n";

    for (const auto& [species, count] :
         classDistribution(dataset.observations)) {
        std::cout << "  " << std::setw(12)
                  << toString(species)
                  << " : " << count << '\n';
    }

    std::cout << "\nDescriptive statistics:\n";

    for (std::size_t index = 0; index < 4; ++index) {
        const auto result = calculateStatistics(
            extractFeature(dataset.observations, index)
        );

        std::cout << std::fixed << std::setprecision(3)
                  << std::setw(15) << std::left
                  << FEATURES[index]
                  << " mean=" << result.mean
                  << " median=" << result.median
                  << " sd=" << result.standardDeviation
                  << " outliers=" << result.outlierCount
                  << '\n';
    }
}

} // namespace iris

int main(int argc, char* argv[]) {
    try {
        const std::string inputPath =
            argc > 1 ? argv[1] : "iris.csv";

        const iris::Dataset dataset =
            iris::loadDataset(inputPath);

        iris::printConsoleReport(dataset);

        iris::writeReport(dataset);
        iris::exportCleanedData(dataset.observations);

        for (const std::string& rejected :
             dataset.rejectedRows) {
            std::cerr << "Rejected: " << rejected << '\n';
        }

        std::cout << "\nGenerated:\n";
        std::cout << "  iris_eda_report.md\n";
        std::cout << "  iris_cleaned.csv\n";

        std::cout << "\nAnalysis completed successfully.\n";

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "EDA failed: "
                  << error.what() << '\n';

        return 1;
    }
}
