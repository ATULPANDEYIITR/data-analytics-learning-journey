/*
    SQL CASE Expressions: Repository Revenue Governance Case Study
    ================================================================

    This C++17 program models a reporting and governance engine for a
    subscription-commerce repository.

    The scenario requires the system to classify repository-owned customer
    accounts and transactions using rules that would naturally be expressed
    with SQL CASE expressions.

    The program demonstrates:

    - searched CASE semantics through ordered predicates
    - simple CASE semantics through equality mappings
    - numeric bucketing
    - conditional transformations
    - business-rule precedence
    - conditional aggregation
    - explicit NULL-like state handling
    - validation of mutually exclusive ranges
    - configurable rule evaluation
    - merge-safe reporting output
    - algorithmic complexity and data-structure choices

    Compile:
        g++ -std=c++17 -O2 -Wall -Wextra -pedantic case_engine.cpp -o case_engine
*/

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

struct Customer {
    int id;
    std::string name;
    std::string region;
    std::optional<std::string> tier;
    double annualSpend;
};

struct Order {
    int id;
    int customerId;
    double amount;
    std::string status;
    std::optional<double> discountRate;
    std::optional<int> shippingDays;
};

struct Bucket {
    std::string label;
    double minimum;
    std::optional<double> maximum;
};

struct RegionMetrics {
    int totalOrders = 0;
    int completedOrders = 0;
    int cancelledOrders = 0;
    double completedRevenue = 0.0;
};

class CaseEngine {
public:
    /*
        This function represents a searched CASE:

            CASE
                WHEN annual_spend >= 200000 THEN 'Enterprise'
                WHEN annual_spend >= 100000 THEN 'Premium'
                WHEN annual_spend >= 50000  THEN 'Growth'
                ELSE 'Standard'
            END

        The order is significant because the first matching condition wins.
    */
    static std::string classifySpend(double annualSpend) {
        if (annualSpend >= 200000.0) {
            return "Enterprise";
        }

        if (annualSpend >= 100000.0) {
            return "Premium";
        }

        if (annualSpend >= 50000.0) {
            return "Growth";
        }

        return "Standard";
    }

    /*
        This models a simple CASE where one expression is compared with fixed
        equality values:

            CASE region
                WHEN 'North' THEN ...
                WHEN 'South' THEN ...
                ...
            END
    */
    static std::string describeRegion(const std::string& region) {
        if (region == "North") {
            return "Northern Territory";
        }

        if (region == "South") {
            return "Southern Territory";
        }

        if (region == "East") {
            return "Eastern Territory";
        }

        if (region == "West") {
            return "Western Territory";
        }

        return "Unassigned Territory";
    }

    /*
        This CASE-like operation distinguishes a missing discount from an
        explicit zero. SQL NULL is not equivalent to zero, so the optional
        representation is important in the C++ model.
    */
    static std::string classifyDiscount(
        const std::optional<double>& discountRate
    ) {
        if (!discountRate.has_value()) {
            return "Discount not recorded";
        }

        if (*discountRate == 0.0) {
            return "No discount";
        }

        if (*discountRate < 0.10) {
            return "Low discount";
        }

        if (*discountRate < 0.20) {
            return "Standard discount";
        }

        return "High discount";
    }

    /*
        Numeric CASE bucketing uses half-open intervals:

            amount < 5000       => Small
            amount < 15000      => Medium
            amount < 50000      => Large
            otherwise           => Enterprise

        Because the conditions are ordered from the smallest boundary upward,
        each non-negative amount maps to one bucket.
    */
    static std::string bucketAmount(double amount) {
        if (amount < 0.0) {
            return "Invalid";
        }

        if (amount < 5000.0) {
            return "Small";
        }

        if (amount < 15000.0) {
            return "Medium";
        }

        if (amount < 50000.0) {
            return "Large";
        }

        return "Enterprise";
    }

    /*
        Business-rule CASE expressions frequently combine multiple columns.

        The cancellation rule has precedence over fulfillment rules. A delayed
        cancelled order must not accidentally be classified as a fulfillment
        escalation.
    */
    static std::string operationalAction(const Order& order) {
        if (order.status == "cancelled") {
            return "Do not process";
        }

        if (!order.shippingDays.has_value()) {
            return "Investigate shipping data";
        }

        if (*order.shippingDays > 7 && order.amount >= 20000.0) {
            return "Escalate delayed high-value order";
        }

        if (order.amount >= 50000.0) {
            return "Priority fulfillment";
        }

        if (*order.shippingDays > 7) {
            return "Shipping review";
        }

        return "Normal fulfillment";
    }

    /*
        This is a configurable CASE evaluator. Each Rule has a predicate and
        a result label. The function deliberately stops after the first match,
        preserving SQL CASE semantics.
    */
    struct Rule {
        std::string label;
        bool (*matches)(double);
    };

    static std::string evaluateRules(
        double value,
        const std::vector<Rule>& rules,
        const std::string& fallback
    ) {
        for (const Rule& rule : rules) {
            if (rule.matches == nullptr) {
                throw std::invalid_argument(
                    "CASE rule contains a null predicate"
                );
            }

            if (rule.matches(value)) {
                return rule.label;
            }
        }

        return fallback;
    }

    /*
        Validate bucket configuration before it becomes production business
        logic. Overlapping intervals make the classification dependent on
        WHEN ordering rather than representing a clean domain partition.
    */
    static void validateBuckets(std::vector<Bucket> buckets) {
        if (buckets.empty()) {
            throw std::invalid_argument(
                "At least one CASE bucket is required"
            );
        }

        std::sort(
            buckets.begin(),
            buckets.end(),
            [](const Bucket& left, const Bucket& right) {
                return left.minimum < right.minimum;
            }
        );

        for (std::size_t i = 0; i < buckets.size(); ++i) {
            const Bucket& current = buckets[i];

            if (!std::isfinite(current.minimum)) {
                throw std::invalid_argument(
                    "Bucket minimum must be finite"
                );
            }

            if (
                current.maximum.has_value() &&
                (!std::isfinite(*current.maximum) ||
                 *current.maximum <= current.minimum)
            ) {
                throw std::invalid_argument(
                    "Bucket maximum must be finite and greater than minimum"
                );
            }

            if (
                i > 0 &&
                buckets[i - 1].maximum.has_value() &&
                current.minimum < *buckets[i - 1].maximum
            ) {
                throw std::invalid_argument(
                    "Overlapping CASE buckets detected"
                );
            }
        }
    }

    /*
        Conditional aggregation is modeled explicitly here.

        A SQL query would commonly use:

            SUM(CASE WHEN status = 'completed'
                     THEN amount
                     ELSE 0
                END)

        The C++ implementation groups the same business metric by region.
    */
    static std::map<std::string, RegionMetrics> calculateRegionalMetrics(
        const std::vector<Customer>& customers,
        const std::vector<Order>& orders
    ) {
        std::unordered_map<int, const Customer*> customerIndex;

        for (const Customer& customer : customers) {
            customerIndex.emplace(customer.id, &customer);
        }

        std::map<std::string, RegionMetrics> metrics;

        for (const Order& order : orders) {
            auto customerIterator = customerIndex.find(order.customerId);

            if (customerIterator == customerIndex.end()) {
                throw std::runtime_error(
                    "Order references an unknown customer: " +
                    std::to_string(order.id)
                );
            }

            const Customer& customer = *customerIterator->second;
            RegionMetrics& region = metrics[customer.region];

            ++region.totalOrders;

            if (order.status == "completed") {
                ++region.completedOrders;
                region.completedRevenue += order.amount;
            } else if (order.status == "cancelled") {
                ++region.cancelledOrders;
            }
        }

        return metrics;
    }
};

static bool premiumRule(double value) {
    return value >= 100000.0;
}

static bool growthRule(double value) {
    return value >= 50000.0;
}

static bool standardRule(double) {
    return true;
}

void printCustomerClassifications(
    const std::vector<Customer>& customers
) {
    std::cout << "\n--- Customer CASE classifications ---\n";

    for (const Customer& customer : customers) {
        std::cout
            << std::left
            << std::setw(10) << customer.name
            << std::setw(14)
            << CaseEngine::classifySpend(customer.annualSpend)
            << std::setw(24)
            << CaseEngine::describeRegion(customer.region);

        if (customer.tier.has_value()) {
            std::cout << *customer.tier;
        } else {
            std::cout << "Tier missing";
        }

        std::cout << '\n';
    }
}

void printOrderDecisions(
    const std::vector<Order>& orders
) {
    std::cout << "\n--- Order CASE decisions ---\n";

    for (const Order& order : orders) {
        std::cout
            << "Order " << order.id
            << " | bucket=" << CaseEngine::bucketAmount(order.amount)
            << " | discount="
            << CaseEngine::classifyDiscount(order.discountRate)
            << " | action="
            << CaseEngine::operationalAction(order)
            << '\n';
    }
}

void demonstrateConfigurableBuckets() {
    std::cout << "\n--- Validating configurable CASE buckets ---\n";

    std::vector<Bucket> validBuckets{
        {"Small", 0.0, 5000.0},
        {"Medium", 5000.0, 15000.0},
        {"Large", 15000.0, 50000.0},
        {"Enterprise", 50000.0, std::nullopt},
    };

    CaseEngine::validateBuckets(validBuckets);

    std::cout
        << "Valid configuration accepted: "
        << validBuckets.size()
        << " mutually exclusive ranges.\n";

    std::vector<Bucket> overlappingBuckets{
        {"Small", 0.0, 10000.0},
        {"Medium", 5000.0, 15000.0},
    };

    try {
        CaseEngine::validateBuckets(overlappingBuckets);
        std::cout << "Unexpected result: overlap was accepted.\n";
    } catch (const std::exception& exception) {
        std::cout
            << "Invalid configuration rejected: "
            << exception.what()
            << '\n';
    }
}

void demonstrateRulePrecedence() {
    std::cout << "\n--- CASE rule precedence ---\n";

    /*
        This deliberately places Growth before Premium.

        For 120000, both predicates are true. SQL CASE returns the result of
        the first matching WHEN, so Premium becomes unreachable for this
        overlapping portion of the domain.
    */
    const std::vector<CaseEngine::Rule> poorlyOrderedRules{
        {"Growth", growthRule},
        {"Premium", premiumRule},
        {"Standard", standardRule},
    };

    std::cout
        << "120000 classified as: "
        << CaseEngine::evaluateRules(
               120000.0,
               poorlyOrderedRules,
               "Unclassified"
           )
        << '\n';

    std::cout
        << "This illustrates why overlapping CASE predicates require explicit "
           "precedence or should be converted into mutually exclusive ranges.\n";
}

void printRegionalMetrics(
    const std::map<std::string, RegionMetrics>& metrics
) {
    std::cout << "\n--- Conditional aggregation by region ---\n";

    std::cout
        << std::left
        << std::setw(12) << "Region"
        << std::setw(12) << "Orders"
        << std::setw(18) << "Completed"
        << std::setw(18) << "Cancelled"
        << "Completed revenue\n";

    std::cout << std::string(75, '-') << '\n';

    std::cout << std::fixed << std::setprecision(2);

    for (const auto& [region, metric] : metrics) {
        std::cout
            << std::setw(12) << region
            << std::setw(12) << metric.totalOrders
            << std::setw(18) << metric.completedOrders
            << std::setw(18) << metric.cancelledOrders
            << metric.completedRevenue
            << '\n';
    }
}

void demonstrateBoundaryValues() {
    std::cout << "\n--- CASE bucket boundaries ---\n";

    const std::vector<double> values{
        0.0,
        4999.99,
        5000.0,
        14999.99,
        15000.0,
        49999.99,
        50000.0,
    };

    for (double value : values) {
        std::cout
            << std::fixed
            << std::setprecision(2)
            << value
            << " -> "
            << CaseEngine::bucketAmount(value)
            << '\n';
    }
}

int main() {
    try {
        const std::vector<Customer> customers{
            {1, "Asha", "North", "Gold", 125000.0},
            {2, "Ravi", "South", "Silver", 64000.0},
            {3, "Meera", "West", std::nullopt, 18000.0},
            {4, "Kabir", "East", "Bronze", 42000.0},
            {5, "Neha", "North", "Gold", 225000.0},
        };

        const std::vector<Order> orders{
            {101, 1, 18000.0, "completed", 0.10, 2},
            {102, 1, 42000.0, "completed", 0.05, 4},
            {103, 2, 7600.0, "pending", 0.05, 6},
            {104, 3, 2500.0, "completed", std::nullopt, 9},
            {105, 3, 14000.0, "completed", 0.20, 5},
            {106, 4, 48000.0, "completed", 0.05, 2},
            {107, 5, 65000.0, "completed", 0.12, 1},
        };

        printCustomerClassifications(customers);
        printOrderDecisions(orders);

        demonstrateConfigurableBuckets();
        demonstrateRulePrecedence();
        demonstrateBoundaryValues();

        const auto metrics =
            CaseEngine::calculateRegionalMetrics(customers, orders);

        printRegionalMetrics(metrics);

        std::cout << "\n--- Technical properties ---\n";
        std::cout
            << "Customer lookup uses unordered_map indexing: expected O(1) "
               "lookup per order.\n";

        std::cout
            << "Regional aggregation processes each order once: O(O), "
               "excluding hash-table behavior constants.\n";

        std::cout
            << "Bucket validation sorts ranges: O(B log B), where B is the "
               "number of configured CASE ranges.\n";

        std::cout
            << "Optional fields model SQL NULL explicitly so missing values "
               "cannot silently become valid numeric values.\n";

        std::cout
            << "The first-match rule evaluator mirrors SQL CASE semantics, "
               "so predicate order is part of the business-rule contract.\n";

        return 0;
    } catch (const std::exception& exception) {
        std::cerr
            << "Case engine failed: "
            << exception.what()
            << '\n';

        return 1;
    }
}
