#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Probability Distributions
 *
 * C++17 statistical simulation and probability calculation engine.
 *
 * Supports:
 * Bernoulli, Binomial, Geometric, Poisson,
 * Uniform, Normal, and Exponential distributions.
 *
 * The implementation uses polymorphism, validated parameters,
 * standard-library random engines, and numerical calculations.
 */

namespace probability {

constexpr double PI = 3.14159265358979323846;

class DistributionError : public std::invalid_argument {
public:
    explicit DistributionError(const std::string& message)
        : std::invalid_argument(message) {}
};

void validateProbability(double p) {
    if (!std::isfinite(p) || p < 0.0 || p > 1.0) {
        throw DistributionError("Probability must be in [0, 1].");
    }
}

void validatePositive(double value, const std::string& name) {
    if (!std::isfinite(value) || value <= 0.0) {
        throw DistributionError(name + " must be finite and positive.");
    }
}

void validateFinite(double value, const std::string& name) {
    if (!std::isfinite(value)) {
        throw DistributionError(name + " must be finite.");
    }
}

void validateCount(std::size_t value, std::size_t maximum = 1000000) {
    if (value > maximum) {
        throw DistributionError("Count exceeds the configured limit.");
    }
}

double logCombination(int n, int k) {
    if (k < 0 || k > n) {
        return -std::numeric_limits<double>::infinity();
    }

    return std::lgamma(n + 1.0)
        - std::lgamma(k + 1.0)
        - std::lgamma(n - k + 1.0);
}

struct Statistics {
    double mean;
    double variance;
    double standardDeviation;
};

class Distribution {
protected:
    std::mt19937_64 engine;

public:
    explicit Distribution(std::uint64_t seed)
        : engine(seed) {}

    virtual ~Distribution() = default;

    virtual double mean() const = 0;
    virtual double variance() const = 0;
    virtual double sample() = 0;
    virtual double cdf(double x) const = 0;

    virtual Statistics statistics() const {
        const double v = variance();

        return {
            mean(),
            v,
            std::sqrt(v)
        };
    }

    std::vector<double> sampleMany(std::size_t count) {
        validateCount(count);

        std::vector<double> result;
        result.reserve(count);

        for (std::size_t i = 0; i < count; ++i) {
            result.push_back(sample());
        }

        return result;
    }

    static Statistics empiricalStatistics(
        const std::vector<double>& values
    ) {
        if (values.empty()) {
            throw DistributionError("Sample cannot be empty.");
        }

        const double average =
            std::accumulate(values.begin(), values.end(), 0.0)
            / static_cast<double>(values.size());

        double squaredDifferences = 0.0;

        for (double value : values) {
            squaredDifferences += (value - average) * (value - average);
        }

        const double variance =
            squaredDifferences / static_cast<double>(values.size());

        return {
            average,
            variance,
            std::sqrt(variance)
        };
    }
};

class Bernoulli final : public Distribution {
private:
    double p;

public:
    Bernoulli(double probability, std::uint64_t seed = 1)
        : Distribution(seed), p(probability) {
        validateProbability(p);
    }

    double pmf(int x) const {
        if (x != 0 && x != 1) return 0.0;
        return x == 1 ? p : 1.0 - p;
    }

    double cdf(double x) const override {
        if (x < 0.0) return 0.0;
        if (x < 1.0) return 1.0 - p;
        return 1.0;
    }

    double mean() const override {
        return p;
    }

    double variance() const override {
        return p * (1.0 - p);
    }

    double sample() override {
        std::bernoulli_distribution distribution(p);
        return distribution(engine) ? 1.0 : 0.0;
    }
};

class Binomial final : public Distribution {
private:
    int n;
    double p;

public:
    Binomial(int trials, double probability, std::uint64_t seed = 2)
        : Distribution(seed), n(trials), p(probability) {
        if (n < 0 || n > 1000000) {
            throw DistributionError(
                "Binomial trial count must be between 0 and 1000000."
            );
        }

        validateProbability(p);
    }

    double pmf(int k) const {
        if (k < 0 || k > n) return 0.0;

        if (p == 0.0) return k == 0 ? 1.0 : 0.0;
        if (p == 1.0) return k == n ? 1.0 : 0.0;

        const double logProbability =
            logCombination(n, k)
            + k * std::log(p)
            + (n - k) * std::log1p(-p);

        return std::exp(logProbability);
    }

    double cdf(double x) const override {
        if (x < 0.0) return 0.0;
        if (x >= n) return 1.0;

        const int upper = static_cast<int>(std::floor(x));
        double total = 0.0;

        for (int k = 0; k <= upper; ++k) {
            total += pmf(k);
        }

        return std::min(1.0, total);
    }

    double mean() const override {
        return n * p;
    }

    double variance() const override {
        return n * p * (1.0 - p);
    }

    double sample() override {
        std::binomial_distribution<int> distribution(n, p);
        return static_cast<double>(distribution(engine));
    }
};

class Geometric final : public Distribution {
private:
    double p;

public:
    Geometric(double probability, std::uint64_t seed = 3)
        : Distribution(seed), p(probability) {
        validateProbability(p);

        if (p == 0.0) {
            throw DistributionError(
                "Geometric probability must be greater than zero."
            );
        }
    }

    double pmf(int k) const {
        if (k < 1) return 0.0;
        if (p == 1.0) return k == 1 ? 1.0 : 0.0;

        return p * std::pow(1.0 - p, k - 1);
    }

    double cdf(double x) const override {
        if (x < 1.0) return 0.0;
        if (p == 1.0) return 1.0;

        const int k = static_cast<int>(std::floor(x));

        return -std::expm1(k * std::log1p(-p));
    }

    double mean() const override {
        return 1.0 / p;
    }

    double variance() const override {
        return (1.0 - p) / (p * p);
    }

    double sample() override {
        if (p == 1.0) return 1.0;

        std::geometric_distribution<int> distribution(p);
        return static_cast<double>(distribution(engine));
    }
};

class Poisson final : public Distribution {
private:
    double lambda;

public:
    Poisson(double rate, std::uint64_t seed = 4)
        : Distribution(seed), lambda(rate) {
        validateFinite(lambda, "Poisson rate");

        if (lambda < 0.0 || lambda > 1000000.0) {
            throw DistributionError(
                "Poisson rate must be between 0 and 1000000."
            );
        }
    }

    double pmf(int k) const {
        if (k < 0) return 0.0;
        if (lambda == 0.0) return k == 0 ? 1.0 : 0.0;

        return std::exp(
            -lambda
            + k * std::log(lambda)
            - std::lgamma(k + 1.0)
        );
    }

    double cdf(double x) const override {
        if (x < 0.0) return 0.0;
        if (lambda == 0.0) return 1.0;

        const int upper = static_cast<int>(std::floor(x));
        double total = 0.0;

        for (int k = 0; k <= upper; ++k) {
            total += pmf(k);
        }

        return std::min(1.0, total);
    }

    double mean() const override {
        return lambda;
    }

    double variance() const override {
        return lambda;
    }

    double sample() override {
        if (lambda == 0.0) return 0.0;

        std::poisson_distribution<int> distribution(lambda);
        return static_cast<double>(distribution(engine));
    }
};

class Uniform final : public Distribution {
private:
    double a;
    double b;

public:
    Uniform(double lower, double upper, std::uint64_t seed = 5)
        : Distribution(seed), a(lower), b(upper) {
        validateFinite(a, "Lower bound");
        validateFinite(b, "Upper bound");

        if (a >= b) {
            throw DistributionError("Uniform distribution requires a < b.");
        }
    }

    double pdf(double x) const {
        return x >= a && x <= b ? 1.0 / (b - a) : 0.0;
    }

    double cdf(double x) const override {
        if (x <= a) return 0.0;
        if (x >= b) return 1.0;

        return (x - a) / (b - a);
    }

    double mean() const override {
        return (a + b) / 2.0;
    }

    double variance() const override {
        return (b - a) * (b - a) / 12.0;
    }

    double sample() override {
        std::uniform_real_distribution<double> distribution(a, b);
        return distribution(engine);
    }
};

class Normal final : public Distribution {
private:
    double mu;
    double sigma;

public:
    Normal(double meanValue, double standardDeviation,
           std::uint64_t seed = 6)
        : Distribution(seed), mu(meanValue), sigma(standardDeviation) {
        validateFinite(mu, "Normal mean");
        validatePositive(sigma, "Normal standard deviation");
    }

    double pdf(double x) const {
        const double z = (x - mu) / sigma;

        return std::exp(-0.5 * z * z)
            / (sigma * std::sqrt(2.0 * PI));
    }

    double cdf(double x) const override {
        return 0.5 * std::erfc(
            -(x - mu) / (sigma * std::sqrt(2.0))
        );
    }

    double mean() const override {
        return mu;
    }

    double variance() const override {
        return sigma * sigma;
    }

    double sample() override {
        std::normal_distribution<double> distribution(mu, sigma);
        return distribution(engine);
    }

    double standardize(double x) const {
        return (x - mu) / sigma;
    }

    double intervalProbability(double lower, double upper) const {
        if (lower > upper) {
            throw DistributionError(
                "Lower bound cannot exceed upper bound."
            );
        }

        return cdf(upper) - cdf(lower);
    }
};

class Exponential final : public Distribution {
private:
    double lambda;

public:
    Exponential(double rate, std::uint64_t seed = 7)
        : Distribution(seed), lambda(rate) {
        validatePositive(lambda, "Exponential rate");
    }

    double pdf(double x) const {
        if (x < 0.0) return 0.0;
        return lambda * std::exp(-lambda * x);
    }

    double cdf(double x) const override {
        if (x < 0.0) return 0.0;
        return -std::expm1(-lambda * x);
    }

    double survival(double x) const {
        if (x < 0.0) return 1.0;
        return std::exp(-lambda * x);
    }

    double mean() const override {
        return 1.0 / lambda;
    }

    double variance() const override {
        return 1.0 / (lambda * lambda);
    }

    double sample() override {
        std::exponential_distribution<double> distribution(lambda);
        return distribution(engine);
    }
};

struct SimulationReport {
    std::string name;
    Statistics theoretical;
    Statistics empirical;
    double minimum;
    double maximum;
};

SimulationReport simulate(
    const std::string& name,
    Distribution& distribution,
    std::size_t sampleSize
) {
    validateCount(sampleSize);

    if (sampleSize == 0) {
        throw DistributionError("Simulation size must be positive.");
    }

    const std::vector<double> values =
        distribution.sampleMany(sampleSize);

    const auto limits = std::minmax_element(
        values.begin(), values.end()
    );

    return {
        name,
        distribution.statistics(),
        Distribution::empiricalStatistics(values),
        *limits.first,
        *limits.second
    };
}

void printReport(const SimulationReport& report) {
    std::cout << "\n" << report.name << "\n";
    std::cout << std::string(55, '-') << "\n";

    std::cout << "Theoretical mean:     "
              << report.theoretical.mean << "\n";

    std::cout << "Empirical mean:       "
              << report.empirical.mean << "\n";

    std::cout << "Theoretical variance: "
              << report.theoretical.variance << "\n";

    std::cout << "Empirical variance:   "
              << report.empirical.variance << "\n";

    std::cout << "Minimum:              "
              << report.minimum << "\n";

    std::cout << "Maximum:              "
              << report.maximum << "\n";
}

void validateCalculations() {
    Bernoulli bernoulli(0.4);
    if (std::abs(bernoulli.pmf(0) + bernoulli.pmf(1) - 1.0) > 1e-10) {
        throw std::runtime_error("Bernoulli normalization failed.");
    }

    Binomial binomial(10, 0.5);
    double binomialTotal = 0.0;

    for (int k = 0; k <= 10; ++k) {
        binomialTotal += binomial.pmf(k);
    }

    if (std::abs(binomialTotal - 1.0) > 1e-10) {
        throw std::runtime_error("Binomial normalization failed.");
    }

    Normal normal(0.0, 1.0);
    if (std::abs(normal.cdf(0.0) - 0.5) > 1e-10) {
        throw std::runtime_error("Normal CDF validation failed.");
    }

    Exponential exponential(2.0);
    if (std::abs(exponential.mean() - 0.5) > 1e-10) {
        throw std::runtime_error("Exponential mean validation failed.");
    }

    Poisson poisson(0.0);
    if (std::abs(poisson.pmf(0) - 1.0) > 1e-10) {
        throw std::runtime_error("Poisson boundary validation failed.");
    }

    std::cout << "\nAll calculation assertions passed.\n";
}

void displayProbabilityExamples() {
    Bernoulli bernoulli(0.7);
    Binomial binomial(10, 0.3);
    Geometric geometric(0.25);
    Poisson poisson(4.0);
    Uniform uniform(0.0, 10.0);
    Normal normal(100.0, 15.0);
    Exponential exponential(0.5);

    std::cout << "\nPROBABILITY CALCULATIONS\n";
    std::cout << "========================\n";

    std::cout << "Bernoulli P(X=1): "
              << bernoulli.pmf(1) << "\n";

    std::cout << "Binomial P(X=3): "
              << binomial.pmf(3) << "\n";

    std::cout << "Binomial P(X<=3): "
              << binomial.cdf(3) << "\n";

    std::cout << "Geometric P(X=4): "
              << geometric.pmf(4) << "\n";

    std::cout << "Poisson P(X=2): "
              << poisson.pmf(2) << "\n";

    std::cout << "Uniform PDF at 5: "
              << uniform.pdf(5) << "\n";

    std::cout << "Normal P(X<=115): "
              << normal.cdf(115) << "\n";

    std::cout << "Normal P(85<=X<=115): "
              << normal.intervalProbability(85, 115) << "\n";

    std::cout << "Exponential P(X>2): "
              << exponential.survival(2) << "\n";
}

void demonstrateEdgeCases() {
    std::cout << "\nEDGE CASES\n";
    std::cout << "==========\n";

    Bernoulli certainSuccess(1.0);
    Bernoulli certainFailure(0.0);
    Binomial zeroTrials(0, 0.5);
    Poisson zeroRate(0.0);
    Geometric certainFirstTrial(1.0);

    std::cout << "Bernoulli p=1 sample: "
              << certainSuccess.sample() << "\n";

    std::cout << "Bernoulli p=0 sample: "
              << certainFailure.sample() << "\n";

    std::cout << "Binomial n=0, P(X=0): "
              << zeroTrials.pmf(0) << "\n";

    std::cout << "Poisson lambda=0, P(X=0): "
              << zeroRate.pmf(0) << "\n";

    std::cout << "Geometric p=1 sample: "
              << certainFirstTrial.sample() << "\n";
}

} // namespace probability

int main() {
    using namespace probability;

    try {
        std::cout << std::fixed << std::setprecision(6);

        displayProbabilityExamples();

        std::cout << "\nMONTE CARLO SIMULATIONS\n";
        std::cout << "=======================\n";

        Bernoulli bernoulli(0.4, 101);
        Binomial binomial(20, 0.4, 102);
        Geometric geometric(0.2, 103);
        Poisson poisson(5.0, 104);
        Uniform uniform(10.0, 20.0, 105);
        Normal normal(50.0, 10.0, 106);
        Exponential exponential(0.5, 107);

        const std::size_t sampleSize = 10000;

        std::vector<SimulationReport> reports;

        reports.push_back(simulate("Bernoulli", bernoulli, sampleSize));
        reports.push_back(simulate("Binomial", binomial, sampleSize));
        reports.push_back(simulate("Geometric", geometric, sampleSize));
        reports.push_back(simulate("Poisson", poisson, sampleSize));
        reports.push_back(simulate("Uniform", uniform, sampleSize));
        reports.push_back(simulate("Normal", normal, sampleSize));
        reports.push_back(simulate("Exponential", exponential, sampleSize));

        for (const auto& report : reports) {
            printReport(report);
        }

        demonstrateEdgeCases();
        validateCalculations();

        std::cout << "\nExecution completed successfully.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << "\n";

        return 1;
    }

    return 0;
}
