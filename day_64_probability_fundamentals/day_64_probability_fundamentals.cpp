#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

class ProbabilityError : public std::runtime_error {
public:
    explicit ProbabilityError(const std::string& message)
        : std::runtime_error(message) {}
};

enum class EventRelation {
    Independent,
    Dependent,
    Disjoint,
    Overlapping
};

class ProbabilitySpace {
private:
    std::map<int, double> probabilities;

    void validateEvent(const std::set<int>& event) const {
        for (int outcome : event) {
            if (!probabilities.contains(outcome)) {
                throw ProbabilityError("Event contains an unknown outcome.");
            }
        }
    }

public:
    explicit ProbabilitySpace(std::map<int, double> probabilities)
        : probabilities(std::move(probabilities)) {

        if (this->probabilities.empty()) {
            throw ProbabilityError("Sample space cannot be empty.");
        }

        double total = 0.0;

        for (const auto& [outcome, probability] : this->probabilities) {
            if (!std::isfinite(probability) ||
                probability < 0.0 ||
                probability > 1.0) {
                throw ProbabilityError("Invalid outcome probability.");
            }
            total += probability;
        }

        if (std::abs(total - 1.0) > 1e-12) {
            throw ProbabilityError("Outcome probabilities must sum to 1.");
        }
    }

    double probability(const std::set<int>& event) const {
        validateEvent(event);

        double result = 0.0;
        for (int outcome : event) {
            result += probabilities.at(outcome);
        }

        return result;
    }

    std::set<int> intersection(
        const std::set<int>& a,
        const std::set<int>& b
    ) const {
        validateEvent(a);
        validateEvent(b);

        std::set<int> result;
        std::set_intersection(
            a.begin(), a.end(),
            b.begin(), b.end(),
            std::inserter(result, result.begin())
        );

        return result;
    }

    std::set<int> unionOf(
        const std::set<int>& a,
        const std::set<int>& b
    ) const {
        validateEvent(a);
        validateEvent(b);

        std::set<int> result;
        std::set_union(
            a.begin(), a.end(),
            b.begin(), b.end(),
            std::inserter(result, result.begin())
        );

        return result;
    }

    std::set<int> complement(const std::set<int>& event) const {
        validateEvent(event);

        std::set<int> result;
        for (const auto& [outcome, probability] : probabilities) {
            if (!event.contains(outcome)) {
                result.insert(outcome);
            }
        }

        return result;
    }

    double conditionalProbability(
        const std::set<int>& event,
        const std::set<int>& given
    ) const {
        const double denominator = probability(given);

        if (denominator <= 0.0) {
            throw ProbabilityError(
                "Conditional probability is undefined for a zero-probability condition."
            );
        }

        return probability(intersection(event, given)) / denominator;
    }

    bool independent(
        const std::set<int>& a,
        const std::set<int>& b
    ) const {
        const double lhs = probability(intersection(a, b));
        const double rhs = probability(a) * probability(b);

        return std::abs(lhs - rhs) <= 1e-12;
    }

    EventRelation relation(
        const std::set<int>& a,
        const std::set<int>& b
    ) const {
        const auto common = intersection(a, b);

        if (common.empty()) {
            return EventRelation::Disjoint;
        }

        return independent(a, b)
            ? EventRelation::Independent
            : EventRelation::Overlapping;
    }
};

long double binomialProbability(
    int n,
    int successes,
    long double p
) {
    if (n < 0 || successes < 0 || successes > n) {
        throw ProbabilityError("Invalid binomial parameters.");
    }

    if (p < 0.0L || p > 1.0L) {
        throw ProbabilityError("Binomial probability must be between 0 and 1.");
    }

    const int k = std::min(successes, n - successes);
    long double coefficient = 1.0L;

    for (int i = 1; i <= k; ++i) {
        coefficient *= static_cast<long double>(n - i + 1) / i;
    }

    return coefficient *
           std::pow(p, successes) *
           std::pow(1.0L - p, n - successes);
}

void runExperiment(int trials) {
    if (trials <= 0) {
        throw ProbabilityError("Trial count must be positive.");
    }

    std::mt19937 generator(42);
    std::uniform_int_distribution<int> die(1, 6);

    std::map<int, int> counts;

    for (int i = 0; i < trials; ++i) {
        ++counts[die(generator)];
    }

    std::cout << "\n=== Simulated Die Experiment ===\n";

    for (const auto& [outcome, count] : counts) {
        const double estimated =
            static_cast<double>(count) / trials;

        std::cout << outcome
                  << ": count=" << count
                  << ", estimated P=" << std::fixed
                  << std::setprecision(4)
                  << estimated << '\n';
    }
}

int main() {
    try {
        ProbabilitySpace die({
            {1, 1.0 / 6.0},
            {2, 1.0 / 6.0},
            {3, 1.0 / 6.0},
            {4, 1.0 / 6.0},
            {5, 1.0 / 6.0},
            {6, 1.0 / 6.0}
        });

        const std::set<int> even{2, 4, 6};
        const std::set<int> high{5, 6};
        const std::set<int> odd{1, 3, 5};

        std::cout << "=== Probability Rules ===\n";
        std::cout << "P(even) = "
                  << die.probability(even) << '\n';

        std::cout << "P(high) = "
                  << die.probability(high) << '\n';

        const auto intersection = die.intersection(even, high);
        const auto unionEvent = die.unionOf(even, high);

        std::cout << "P(even intersection high) = "
                  << die.probability(intersection) << '\n';

        std::cout << "P(even union high) = "
                  << die.probability(unionEvent) << '\n';

        std::cout << "P(even | high) = "
                  << die.conditionalProbability(even, high)
                  << '\n';

        std::cout << "Even and high independent = "
                  << std::boolalpha
                  << die.independent(even, high)
                  << '\n';

        // A useful contrast: even and odd are mutually exclusive.
        std::cout << "P(even and odd) = "
                  << die.probability(die.intersection(even, odd))
                  << '\n';

        std::cout << "\n=== Binomial Probability ===\n";
        std::cout << "P(exactly 3 successes, n=10, p=0.2) = "
                  << std::setprecision(8)
                  << static_cast<double>(
                         binomialProbability(10, 3, 0.2L))
                  << '\n';

        runExperiment(10000);

        std::cout << "\n=== Validation ===\n";

        try {
            ProbabilitySpace invalid({
                {1, 0.4},
                {2, 0.4}
            });
        } catch (const ProbabilityError& error) {
            std::cout << "Rejected invalid probability space: "
                      << error.what() << '\n';
        }

    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
