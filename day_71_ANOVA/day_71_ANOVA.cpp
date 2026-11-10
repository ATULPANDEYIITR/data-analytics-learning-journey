#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>
#include <limits>

using namespace std;

/*
 * ANOVA Statistical Analysis Engine
 *
 * C++17
 *
 * Implements:
 * - One-way ANOVA
 * - Balanced two-way ANOVA
 * - Main effects and interaction
 * - Levene variance diagnostic
 * - Jarque-Bera residual diagnostic
 * - Welch and pooled-variance pairwise comparisons
 * - Holm multiple-testing correction
 * - Effect sizes
 * - Domain validation and automated tests
 *
 * No external libraries.
 */

// ============================================================
// 1. DOMAIN MODEL
// ============================================================

enum class AnalysisType {
    ONE_WAY,
    TWO_WAY
};

struct Observation {
    double value;
    string factorA;
    string factorB;
};

struct GroupStatistics {
    size_t count;
    double mean;
    double variance;
    double minimum;
    double maximum;
};

struct ANOVAResult {
    string source;
    int dfBetween;
    int dfWithin;
    double ssBetween;
    double ssWithin;
    double msBetween;
    double msWithin;
    double fStatistic;
    double pValue;
    double etaSquared;
    double omegaSquared;
};

struct EffectResult {
    string source;
    int df;
    double ss;
    double ms;
    double f;
    double p;
};

struct PairwiseResult {
    string first;
    string second;
    double difference;
    double statistic;
    double rawP;
    double adjustedP;
    bool significant;
    string method;
};


// ============================================================
// 2. VALIDATION AND STATISTICAL UTILITIES
// ============================================================

class ANOVAException : public runtime_error {
public:
    explicit ANOVAException(const string& message)
        : runtime_error(message) {}
};


double calculateMean(const vector<double>& values) {
    if (values.empty()) {
        throw ANOVAException("Empty observation collection.");
    }

    return accumulate(
        values.begin(),
        values.end(),
        0.0
    ) / values.size();
}


double sampleVariance(const vector<double>& values) {
    if (values.size() < 2) {
        throw ANOVAException("At least two values are required.");
    }

    double avg = calculateMean(values);
    double sum = 0.0;

    for (double x : values) {
        sum += (x - avg) * (x - avg);
    }

    return sum / (values.size() - 1);
}


double sumSquares(
    const vector<double>& values,
    double center
) {
    double result = 0;

    for (double x : values) {
        result += (x - center) * (x - center);
    }

    return result;
}


double median(vector<double> values) {
    if (values.empty()) {
        throw ANOVAException("Cannot calculate empty median.");
    }

    sort(values.begin(), values.end());

    size_t n = values.size();

    if (n % 2 == 1) {
        return values[n / 2];
    }

    return (
        values[n / 2 - 1] + values[n / 2]
    ) / 2.0;
}


// ============================================================
// 3. DISTRIBUTION FUNCTIONS
// ============================================================

double betaFraction(double a, double b, double x) {
    const double EPS = 3e-14;
    const double FLOOR = 1e-30;

    double qab = a + b;
    double qap = a + 1;
    double qam = a - 1;

    double c = 1;
    double d = 1 - qab * x / qap;

    if (abs(d) < FLOOR) d = FLOOR;

    d = 1 / d;

    double h = d;

    for (int m = 1; m <= 300; ++m) {
        int m2 = 2 * m;

        double aa = m * (b - m) * x
            / ((qam + m2) * (a + m2));

        d = 1 + aa * d;
        if (abs(d) < FLOOR) d = FLOOR;

        c = 1 + aa / c;
        if (abs(c) < FLOOR) c = FLOOR;

        d = 1 / d;
        h *= d * c;

        aa = -(a + m) * (qab + m) * x
            / ((a + m2) * (qap + m2));

        d = 1 + aa * d;
        if (abs(d) < FLOOR) d = FLOOR;

        c = 1 + aa / c;
        if (abs(c) < FLOOR) c = FLOOR;

        d = 1 / d;

        double delta = d * c;
        h *= delta;

        if (abs(delta - 1) < EPS) break;
    }

    return h;
}


double regularizedBeta(double x, double a, double b) {
    if (a <= 0 || b <= 0) {
        throw ANOVAException("Invalid beta parameters.");
    }

    if (x <= 0) return 0;
    if (x >= 1) return 1;

    double front = exp(
        lgamma(a + b)
        - lgamma(a)
        - lgamma(b)
        + a * log(x)
        + b * log1p(-x)
    );

    if (x < (a + 1) / (a + b + 2)) {
        return front * betaFraction(a, b, x) / a;
    }

    return 1 - front
        * betaFraction(b, a, 1 - x) / b;
}


double fSurvival(double f, int df1, int df2) {
    if (df1 <= 0 || df2 <= 0) {
        throw ANOVAException("Invalid F distribution degrees of freedom.");
    }

    if (f <= 0) return 1;

    return regularizedBeta(
        df2 / (df2 + df1 * f),
        df2 / 2.0,
        df1 / 2.0
    );
}


double tCDF(double t, double df) {
    double x = df / (df + t * t);

    double ib = regularizedBeta(
        x,
        df / 2,
        0.5
    );

    return t >= 0 ? 1 - ib / 2 : ib / 2;
}


double tPValue(double t, double df) {
    return min(
        1.0,
        2 * (1 - tCDF(abs(t), df))
    );
}


// ============================================================
// 4. DATASET MANAGEMENT
// ============================================================

class Dataset {
private:
    vector<Observation> observations;

public:
    explicit Dataset(vector<Observation> input)
        : observations(move(input)) {

        if (observations.empty()) {
            throw ANOVAException("Dataset cannot be empty.");
        }

        for (const auto& item : observations) {
            if (!isfinite(item.value)) {
                throw ANOVAException("Non-finite observation.");
            }

            if (item.factorA.empty()) {
                throw ANOVAException("Factor A cannot be empty.");
            }
        }
    }

    const vector<Observation>& getObservations() const {
        return observations;
    }

    map<string, vector<double>> groupByA() const {
        map<string, vector<double>> groups;

        for (const auto& item : observations) {
            groups[item.factorA].push_back(item.value);
        }

        return groups;
    }

    map<pair<string, string>, vector<double>> groupByFactors() const {
        map<pair<string, string>, vector<double>> cells;

        for (const auto& item : observations) {
            if (item.factorB.empty()) {
                throw ANOVAException(
                    "Factor B is required for two-way ANOVA."
                );
            }

            cells[{item.factorA, item.factorB}].push_back(
                item.value
            );
        }

        return cells;
    }
};


// ============================================================
// 5. DESCRIPTIVE STATISTICS
// ============================================================

map<string, GroupStatistics> describe(const Dataset& dataset) {
    map<string, GroupStatistics> result;

    for (const auto& [name, values] : dataset.groupByA()) {
        result[name] = {
            values.size(),
            calculateMean(values),
            sampleVariance(values),
            *min_element(values.begin(), values.end()),
            *max_element(values.begin(), values.end())
        };
    }

    return result;
}


// ============================================================
// 6. ONE-WAY ANOVA
// ============================================================

ANOVAResult oneWayANOVA(const Dataset& dataset) {
    auto groups = dataset.groupByA();

    if (groups.size() < 2) {
        throw ANOVAException("At least two groups are required.");
    }

    vector<double> all;

    for (const auto& [name, values] : groups) {
        if (values.size() < 2) {
            throw ANOVAException(
                "Every group requires two observations."
            );
        }

        all.insert(all.end(), values.begin(), values.end());
    }

    double grand = calculateMean(all);

    double ssBetween = 0;
    double ssWithin = 0;

    for (const auto& [name, values] : groups) {
        double groupMean = calculateMean(values);

        ssBetween += values.size()
            * pow(groupMean - grand, 2);

        ssWithin += sumSquares(values, groupMean);
    }

    int k = static_cast<int>(groups.size());
    int n = static_cast<int>(all.size());

    int dfBetween = k - 1;
    int dfWithin = n - k;

    if (dfWithin <= 0) {
        throw ANOVAException("Insufficient residual degrees of freedom.");
    }

    double msBetween = ssBetween / dfBetween;
    double msWithin = ssWithin / dfWithin;

    double f = msWithin == 0
        ? (msBetween == 0 ? 0 : numeric_limits<double>::infinity())
        : msBetween / msWithin;

    double p = isinf(f)
        ? 0
        : fSurvival(f, dfBetween, dfWithin);

    double totalSS = ssBetween + ssWithin;

    double eta = totalSS == 0
        ? 0
        : ssBetween / totalSS;

    double omega = totalSS + msWithin == 0
        ? 0
        : max(
            0.0,
            (ssBetween - dfBetween * msWithin)
            / (totalSS + msWithin)
        );

    return {
        "Group",
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
    };
}


// ============================================================
// 7. TWO-WAY ANOVA
// ============================================================

struct TwoWayResult {
    EffectResult factorA;
    EffectResult factorB;
    EffectResult interaction;
    double errorSS;
    int errorDF;
    double errorMS;
};


TwoWayResult twoWayANOVA(const Dataset& dataset) {
    auto cells = dataset.groupByFactors();

    set<string> levelsA;
    set<string> levelsB;

    for (const auto& [key, values] : cells) {
        levelsA.insert(key.first);
        levelsB.insert(key.second);
    }

    int a = static_cast<int>(levelsA.size());
    int b = static_cast<int>(levelsB.size());

    if (a < 2 || b < 2) {
        throw ANOVAException("Both factors require at least two levels.");
    }

    if (static_cast<int>(cells.size()) != a * b) {
        throw ANOVAException("Missing factorial cells.");
    }

    int replication = static_cast<int>(
        cells.begin()->second.size()
    );

    if (replication < 2) {
        throw ANOVAException("Insufficient cell replication.");
    }

    for (const auto& [key, values] : cells) {
        if (static_cast<int>(values.size()) != replication) {
            throw ANOVAException(
                "Balanced factorial design required."
            );
        }
    }

    vector<double> all;

    for (const auto& [key, values] : cells) {
        all.insert(all.end(), values.begin(), values.end());
    }

    double grand = calculateMean(all);

    map<string, double> meanA;
    map<string, double> meanB;
    map<pair<string, string>, double> meanCell;

    for (const string& level : levelsA) {
        vector<double> values;

        for (const auto& [key, cell] : cells) {
            if (key.first == level) {
                values.insert(values.end(), cell.begin(), cell.end());
            }
        }

        meanA[level] = calculateMean(values);
    }

    for (const string& level : levelsB) {
        vector<double> values;

        for (const auto& [key, cell] : cells) {
            if (key.second == level) {
                values.insert(values.end(), cell.begin(), cell.end());
            }
        }

        meanB[level] = calculateMean(values);
    }

    for (const auto& [key, values] : cells) {
        meanCell[key] = calculateMean(values);
    }

    double ssA = 0;
    double ssB = 0;
    double ssAB = 0;
    double ssError = 0;

    for (const auto& [level, value] : meanA) {
        ssA += b * replication * pow(value - grand, 2);
    }

    for (const auto& [level, value] : meanB) {
        ssB += a * replication * pow(value - grand, 2);
    }

    for (const auto& [key, values] : cells) {
        double interaction = meanCell[key]
            - meanA[key.first]
            - meanB[key.second]
            + grand;

        ssAB += replication * interaction * interaction;

        ssError += sumSquares(values, meanCell[key]);
    }

    int dfA = a - 1;
    int dfB = b - 1;
    int dfAB = dfA * dfB;
    int dfError = a * b * (replication - 1);

    double msError = ssError / dfError;

    auto effect = [&](string name, double ss, int df) {
        double ms = ss / df;

        double f = msError == 0
            ? (ms == 0 ? 0 : numeric_limits<double>::infinity())
            : ms / msError;

        double p = isinf(f)
            ? 0
            : fSurvival(f, df, dfError);

        return EffectResult{
            name, df, ss, ms, f, p
        };
    };

    return {
        effect("Factor A", ssA, dfA),
        effect("Factor B", ssB, dfB),
        effect("Interaction", ssAB, dfAB),
        ssError,
        dfError,
        msError
    };
}


// ============================================================
// 8. LEVENE'S TEST
// ============================================================

ANOVAResult leveneTest(const Dataset& dataset) {
    vector<Observation> transformed;

    for (const auto& [name, values] : dataset.groupByA()) {
        double center = median(values);

        for (double x : values) {
            transformed.push_back({
                abs(x - center),
                name,
                ""
            });
        }
    }

    return oneWayANOVA(Dataset(move(transformed)));
}


// ============================================================
// 9. JARQUE-BERA TEST
// ============================================================

pair<double, double> jarqueBera(
    const vector<double>& residuals
) {
    if (residuals.size() < 3) {
        throw ANOVAException("Insufficient residuals.");
    }

    double avg = calculateMean(residuals);
    double m2 = 0;
    double m3 = 0;
    double m4 = 0;

    for (double x : residuals) {
        double d = x - avg;

        m2 += pow(d, 2);
        m3 += pow(d, 3);
        m4 += pow(d, 4);
    }

    m2 /= residuals.size();
    m3 /= residuals.size();
    m4 /= residuals.size();

    if (m2 == 0) return {0, 1};

    double skew = m3 / pow(m2, 1.5);
    double kurtosis = m4 / (m2 * m2);

    double jb = residuals.size() / 6.0 * (
        skew * skew
        + pow(kurtosis - 3, 2) / 4
    );

    // For two degrees of freedom, chi-square survival = exp(-x/2).
    return {jb, exp(-jb / 2)};
}


// ============================================================
// 10. HOLM CORRECTION
// ============================================================

vector<double> holmCorrection(
    const vector<double>& pValues
) {
    vector<pair<double, size_t>> ordered;

    for (size_t i = 0; i < pValues.size(); ++i) {
        if (!isfinite(pValues[i]) ||
            pValues[i] < 0 ||
            pValues[i] > 1) {
            throw ANOVAException("Invalid p-value.");
        }

        ordered.push_back({pValues[i], i});
    }

    sort(ordered.begin(), ordered.end());

    vector<double> adjusted(pValues.size());

    double maximum = 0;
    size_t m = pValues.size();

    for (size_t rank = 0; rank < m; ++rank) {
        maximum = max(
            maximum,
            min(1.0, (m - rank) * ordered[rank].first)
        );

        adjusted[ordered[rank].second] = maximum;
    }

    return adjusted;
}


// ============================================================
// 11. POST-HOC TESTING
// ============================================================

vector<PairwiseResult> postHoc(
    const Dataset& dataset,
    bool equalVariances = true,
    double alpha = 0.05
) {
    auto groups = dataset.groupByA();

    vector<PairwiseResult> results;

    for (auto first = groups.begin(); first != groups.end(); ++first) {
        auto second = first;
        ++second;

        for (; second != groups.end(); ++second) {
            const auto& a = first->second;
            const auto& b = second->second;

            double difference =
                calculateMean(a) - calculateMean(b);

            double se;
            double df;

            if (equalVariances) {
                df = a.size() + b.size() - 2;

                double pooled = (
                    (a.size() - 1) * sampleVariance(a)
                    + (b.size() - 1) * sampleVariance(b)
                ) / df;

                se = sqrt(
                    pooled * (1.0 / a.size() + 1.0 / b.size())
                );
            } else {
                double va = sampleVariance(a) / a.size();
                double vb = sampleVariance(b) / b.size();

                se = sqrt(va + vb);

                df = pow(va + vb, 2) / (
                    va * va / (a.size() - 1)
                    + vb * vb / (b.size() - 1)
                );
            }

            double t = se == 0
                ? (difference == 0 ? 0
                    : copysign(numeric_limits<double>::infinity(),
                               difference))
                : difference / se;

            double p = isinf(t) ? 0 : tPValue(t, df);

            results.push_back({
                first->first,
                second->first,
                difference,
                t,
                p,
                0,
                false,
                equalVariances
                    ? "Pooled-variance pairwise t"
                    : "Welch pairwise t"
            });
        }
    }

    vector<double> pValues;

    for (const auto& result : results) {
        pValues.push_back(result.rawP);
    }

    auto adjusted = holmCorrection(pValues);

    for (size_t i = 0; i < results.size(); ++i) {
        results[i].adjustedP = adjusted[i];
        results[i].significant = adjusted[i] < alpha;
    }

    return results;
}


// ============================================================
// 12. REPORTING
// ============================================================

void printANOVA(const ANOVAResult& result) {
    cout << "\n" << result.source << "\n";
    cout << "F statistic: " << result.fStatistic << "\n";
    cout << "P value: " << result.pValue << "\n";
    cout << "Eta squared: " << result.etaSquared << "\n";
    cout << "Omega squared: " << result.omegaSquared << "\n";
}


void printEffect(const EffectResult& result) {
    cout << left << setw(16) << result.source
         << " DF=" << result.df
         << " SS=" << result.ss
         << " MS=" << result.ms
         << " F=" << result.f
         << " P=" << result.p
         << "\n";
}


// ============================================================
// 13. AUTOMATED TESTS
// ============================================================

void runTests() {
    Dataset sample({
        {1, "A", ""},
        {2, "A", ""},
        {3, "B", ""},
        {4, "B", ""}
    });

    auto result = oneWayANOVA(sample);

    if (result.dfBetween != 1 || result.dfWithin != 2) {
        throw ANOVAException("One-way ANOVA test failed.");
    }

    if (!(result.fStatistic > 0)) {
        throw ANOVAException("Invalid F statistic.");
    }

    auto corrected = holmCorrection({0.01, 0.03, 0.04});

    for (double p : corrected) {
        if (p < 0 || p > 1) {
            throw ANOVAException("Holm correction failed.");
        }
    }

    Dataset factorial({
        {10, "A", "Low"},
        {11, "A", "Low"},
        {15, "A", "High"},
        {16, "A", "High"},
        {13, "B", "Low"},
        {14, "B", "Low"},
        {23, "B", "High"},
        {24, "B", "High"}
    });

    auto twoWay = twoWayANOVA(factorial);

    if (twoWay.interaction.df != 1) {
        throw ANOVAException("Two-way interaction test failed.");
    }

    if (fSurvival(0, 1, 10) != 1.0) {
        throw ANOVAException("F distribution test failed.");
    }

    cout << "All C++17 tests passed.\n";
}


// ============================================================
// 14. APPLICATION
// ============================================================

int main() {
    try {
        cout << fixed << setprecision(6);

        runTests();

        Dataset manufacturing({
            {21, "Control", ""},
            {23, "Control", ""},
            {22, "Control", ""},
            {24, "Control", ""},
            {20, "Control", ""},
            {22, "Control", ""},

            {25, "Process_A", ""},
            {27, "Process_A", ""},
            {26, "Process_A", ""},
            {28, "Process_A", ""},
            {24, "Process_A", ""},
            {27, "Process_A", ""},

            {30, "Process_B", ""},
            {32, "Process_B", ""},
            {29, "Process_B", ""},
            {31, "Process_B", ""},
            {33, "Process_B", ""},
            {30, "Process_B", ""}
        });

        cout << "\nDESCRIPTIVE STATISTICS\n";

        for (const auto& [name, stats] : describe(manufacturing)) {
            cout << name
                 << " N=" << stats.count
                 << " Mean=" << stats.mean
                 << " SD=" << sqrt(stats.variance)
                 << " Min=" << stats.minimum
                 << " Max=" << stats.maximum
                 << "\n";
        }

        cout << "\nONE-WAY ANOVA\n";

        auto oneWay = oneWayANOVA(manufacturing);
        printANOVA(oneWay);

        cout << "\nLEVENE DIAGNOSTIC\n";

        auto levene = leveneTest(manufacturing);
        printANOVA(levene);

        cout << "\nPOST-HOC COMPARISONS\n";

        for (const auto& item : postHoc(manufacturing)) {
            cout << item.first << " vs " << item.second
                 << " Difference=" << item.difference
                 << " P=" << item.rawP
                 << " Adjusted P=" << item.adjustedP
                 << " Significant=" << boolalpha
                 << item.significant
                 << "\n";
        }

        cout << "\nTWO-WAY ANOVA\n";

        Dataset factorial({
            {10, "Traditional", "Low"},
            {11, "Traditional", "Low"},
            {9, "Traditional", "Low"},
            {10, "Traditional", "Low"},

            {15, "Traditional", "High"},
            {14, "Traditional", "High"},
            {16, "Traditional", "High"},
            {15, "Traditional", "High"},

            {13, "Modern", "Low"},
            {12, "Modern", "Low"},
            {14, "Modern", "Low"},
            {13, "Modern", "Low"},

            {23, "Modern", "High"},
            {22, "Modern", "High"},
            {24, "Modern", "High"},
            {23, "Modern", "High"}
        });

        auto twoWay = twoWayANOVA(factorial);

        printEffect(twoWay.factorA);
        printEffect(twoWay.factorB);
        printEffect(twoWay.interaction);

        vector<double> residuals;

        for (const auto& [key, values] : factorial.groupByFactors()) {
            double avg = calculateMean(values);

            for (double x : values) {
                residuals.push_back(x - avg);
            }
        }

        auto normality = jarqueBera(residuals);

        cout << "\nRESIDUAL NORMALITY DIAGNOSTIC\n";
        cout << "Jarque-Bera: " << normality.first
             << " P-value: " << normality.second
             << "\n";

        cout << "\nAnalysis completed.\n";

    } catch (const exception& error) {
        cerr << "ANOVA ERROR: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
