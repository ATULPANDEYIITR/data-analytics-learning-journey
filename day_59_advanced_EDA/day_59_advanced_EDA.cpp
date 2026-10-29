#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using Values = std::vector<double>;

struct FeatureProfile {
    std::string name;
    std::size_t count{};
    double mean{};
    double median{};
    double variance{};
    double skewness{};
    double q1{};
    double q3{};
    double lowerFence{};
    double upperFence{};
    Values outliers;
};

struct Dataset {
    std::map<std::string, Values> features;
};

class Statistics {
public:
    static void validate(const Values& values, const std::string& name) {
        if (values.empty()) {
            throw std::invalid_argument(name + " is empty");
        }

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument(name + " contains non-finite data");
            }
        }
    }

    static double mean(const Values& values) {
        validate(values, "values");
        return std::accumulate(values.begin(), values.end(), 0.0) /
               static_cast<double>(values.size());
    }

    static double quantile(Values values, double q) {
        validate(values, "values");
        if (q < 0.0 || q > 1.0) {
            throw std::invalid_argument("quantile must be in [0, 1]");
        }

        std::sort(values.begin(), values.end());
        double position = (values.size() - 1) * q;
        std::size_t lower = static_cast<std::size_t>(position);
        std::size_t upper = std::min(lower + 1, values.size() - 1);
        double weight = position - static_cast<double>(lower);

        return values[lower] * (1.0 - weight) + values[upper] * weight;
    }

    static double median(const Values& values) {
        return quantile(values, 0.5);
    }

    static double variance(const Values& values, bool sample = true) {
        validate(values, "values");

        if (sample && values.size() < 2) {
            throw std::invalid_argument("sample variance requires two values");
        }

        const double m = mean(values);
        const double divisor =
            static_cast<double>(sample ? values.size() - 1 : values.size());

        double total = 0.0;
        for (double value : values) {
            total += std::pow(value - m, 2);
        }

        return total / divisor;
    }

    static double covariance(const Values& x, const Values& y) {
        validate(x, "x");
        validate(y, "y");

        if (x.size() != y.size() || x.size() < 2) {
            throw std::invalid_argument("covariance requires equal samples");
        }

        const double mx = mean(x);
        const double my = mean(y);
        double total = 0.0;

        for (std::size_t i = 0; i < x.size(); ++i) {
            total += (x[i] - mx) * (y[i] - my);
        }

        return total / static_cast<double>(x.size() - 1);
    }

    static double pearson(const Values& x, const Values& y) {
        const double cov = covariance(x, y);
        const double sx = std::sqrt(variance(x));
        const double sy = std::sqrt(variance(y));

        if (sx == 0.0 || sy == 0.0) {
            return 0.0;
        }

        return cov / (sx * sy);
    }

    static double skewness(const Values& values) {
        validate(values, "values");
        if (values.size() < 3) {
            return 0.0;
        }

        const double m = mean(values);
        const double s = std::sqrt(variance(values));

        if (s == 0.0) {
            return 0.0;
        }

        double total = 0.0;
        for (double value : values) {
            total += std::pow((value - m) / s, 3);
        }

        const double n = static_cast<double>(values.size());
        return n / ((n - 1.0) * (n - 2.0)) * total;
    }

    static Values ranks(const Values& values) {
        validate(values, "values");

        std::vector<std::pair<double, std::size_t>> ordered;
        ordered.reserve(values.size());

        for (std::size_t i = 0; i < values.size(); ++i) {
            ordered.emplace_back(values[i], i);
        }

        std::sort(
            ordered.begin(),
            ordered.end(),
            [](const auto& a, const auto& b) {
                if (a.first != b.first) return a.first < b.first;
                return a.second < b.second;
            }
        );

        Values result(values.size());

        std::size_t i = 0;
        while (i < ordered.size()) {
            std::size_t j = i;
            while (j + 1 < ordered.size() &&
                   ordered[j + 1].first == ordered[i].first) {
                ++j;
            }

            double rank = (static_cast<double>(i + 1) +
                           static_cast<double>(j + 1)) / 2.0;

            for (std::size_t k = i; k <= j; ++k) {
                result[ordered[k].second] = rank;
            }

            i = j + 1;
        }

        return result;
    }

    static double spearman(const Values& x, const Values& y) {
        return pearson(ranks(x), ranks(y));
    }

    static FeatureProfile profile(
        const std::string& name,
        const Values& values
    ) {
        validate(values, name);

        FeatureProfile result;
        result.name = name;
        result.count = values.size();
        result.mean = mean(values);
        result.median = median(values);
        result.variance = variance(values, false);
        result.skewness = skewness(values);
        result.q1 = quantile(values, 0.25);
        result.q3 = quantile(values, 0.75);

        const double iqr = result.q3 - result.q1;
        result.lowerFence = result.q1 - 1.5 * iqr;
        result.upperFence = result.q3 + 1.5 * iqr;

        for (double value : values) {
            if (value < result.lowerFence ||
                value > result.upperFence) {
                result.outliers.push_back(value);
            }
        }

        return result;
    }

    static Values log1p(const Values& values) {
        validate(values, "values");

        Values result;
        result.reserve(values.size());

        for (double value : values) {
            if (value <= -1.0) {
                throw std::invalid_argument(
                    "log1p requires values greater than -1"
                );
            }
            result.push_back(std::log1p(value));
        }

        return result;
    }

    static Values robustScale(const Values& values) {
        validate(values, "values");

        const double med = median(values);
        const double scale = quantile(values, 0.75) -
                             quantile(values, 0.25);

        Values result;
        result.reserve(values.size());

        for (double value : values) {
            result.push_back(
                scale == 0.0 ? 0.0 : (value - med) / scale
            );
        }

        return result;
    }
};

class EDAEngine {
public:
    explicit EDAEngine(Dataset data)
        : data_(std::move(data)) {}

    std::map<std::string, FeatureProfile> profiles() const {
        std::map<std::string, FeatureProfile> result;

        for (const auto& [name, values] : data_.features) {
            result.emplace(name, Statistics::profile(name, values));
        }

        return result;
    }

    std::map<std::string, std::map<std::string, double>>
    correlationMatrix() const {
        std::map<std::string, std::map<std::string, double>> result;

        for (const auto& [left, leftValues] : data_.features) {
            for (const auto& [right, rightValues] : data_.features) {
                result[left][right] =
                    Statistics::pearson(leftValues, rightValues);
            }
        }

        return result;
    }

    void printHighRelationships(double threshold) const {
        std::vector<std::string> names;

        for (const auto& [name, unused] : data_.features) {
            names.push_back(name);
        }

        std::cout << "\nHIGH-CORRELATION RELATIONSHIPS\n";

        for (std::size_t i = 0; i < names.size(); ++i) {
            for (std::size_t j = i + 1; j < names.size(); ++j) {
                const double r = Statistics::pearson(
                    data_.features.at(names[i]),
                    data_.features.at(names[j])
                );

                if (std::abs(r) >= threshold) {
                    std::cout << "  "
                              << names[i] << " <-> "
                              << names[j] << ": "
                              << std::fixed << std::setprecision(3)
                              << r << '\n';
                }
            }
        }
    }

private:
    Dataset data_;
};

Dataset makeDataset() {
    const std::vector<std::vector<double>> rows{
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

    const std::vector<std::string> names{
        "income", "spending", "visits", "tenure", "complaints"
    };

    Dataset dataset;

    for (std::size_t column = 0; column < names.size(); ++column) {
        Values values;

        for (const auto& row : rows) {
            values.push_back(row[column]);
        }

        dataset.features.emplace(names[column], std::move(values));
    }

    return dataset;
}

int main() {
    try {
        const Dataset dataset = makeDataset();
        const EDAEngine engine(dataset);

        const auto profiles = engine.profiles();

        std::cout << "ADVANCED EXPLORATORY DATA ANALYSIS\n";
        std::cout << "=================================\n";

        for (const auto& [name, profile] : profiles) {
            std::cout << "\n" << name << '\n'
                      << "  count     : " << profile.count << '\n'
                      << "  mean      : " << std::fixed
                      << std::setprecision(3) << profile.mean << '\n'
                      << "  median    : " << profile.median << '\n'
                      << "  variance  : " << profile.variance << '\n'
                      << "  skewness  : " << profile.skewness << '\n'
                      << "  IQR fence : [" << profile.lowerFence
                      << ", " << profile.upperFence << "]\n"
                      << "  outliers  : ";

            for (double value : profile.outliers) {
                std::cout << value << ' ';
            }
            std::cout << '\n';
        }

        const auto matrix = engine.correlationMatrix();

        std::cout << "\nCORRELATION MATRIX\n";
        for (const auto& [rowName, row] : matrix) {
            std::cout << std::setw(14) << rowName << " ";
            for (const auto& [columnName, value] : row) {
                std::cout << std::setw(8)
                          << std::fixed << std::setprecision(3)
                          << value;
            }
            std::cout << '\n';
        }

        const auto& income = dataset.features.at("income");
        const auto& spending = dataset.features.at("spending");

        std::cout << "\nRELATIONSHIP DIAGNOSTIC\n";
        std::cout << "Income/spending covariance: "
                  << Statistics::covariance(income, spending) << '\n';
        std::cout << "Income/spending Pearson: "
                  << Statistics::pearson(income, spending) << '\n';
        std::cout << "Income/spending Spearman: "
                  << Statistics::spearman(income, spending) << '\n';

        const Values logIncome = Statistics::log1p(income);

        std::cout << "\nTRANSFORMATION DIAGNOSTIC\n";
        std::cout << "Income skewness before: "
                  << Statistics::skewness(income) << '\n';
        std::cout << "Income skewness after log1p: "
                  << Statistics::skewness(logIncome) << '\n';

        const Values robustSpending =
            Statistics::robustScale(spending);

        std::cout << "Robust-scaled spending range: "
                  << *std::min_element(
                         robustSpending.begin(), robustSpending.end())
                  << " to "
                  << *std::max_element(
                         robustSpending.begin(), robustSpending.end())
                  << '\n';

        engine.printHighRelationships(0.70);

        std::cout << "\nENGINEERING CONTROLS\n";
        std::cout << "- IQR fences flag observations without automatically deleting them.\n";
        std::cout << "- Pearson measures linear association; Spearman measures monotonic association.\n";
        std::cout << "- Covariance depends on measurement units; correlation is standardized.\n";
        std::cout << "- Transformations can improve distributional behavior but alter interpretation.\n";
        std::cout << "- Constant features produce zero correlation in this implementation.\n";
        std::cout << "- Non-finite values are rejected before statistical computation.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "EDA failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
