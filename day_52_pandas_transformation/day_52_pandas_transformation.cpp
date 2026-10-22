#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct Order {
    int id;
    std::string customer;
    std::string region;
    std::string product;
    int quantity;
    double unitPrice;
    std::string status;
    double grossAmount = 0.0;
    double discountRate = 0.0;
    double netAmount = 0.0;
    std::string priority;
    std::string regionCode;
};

class RepositoryTransformationEngine {
private:
    static std::string normalizeStatus(const std::string& status) {
        static const std::unordered_map<std::string, std::string> replacements{
            {"completed", "Completed"},
            {"pending", "Pending"},
            {"cancelled", "Cancelled"}
        };

        auto it = replacements.find(status);
        return it == replacements.end() ? status : it->second;
    }

    static std::string regionCode(const std::string& region) {
        static const std::unordered_map<std::string, std::string> codes{
            {"North", "N"},
            {"South", "S"},
            {"East", "E"},
            {"West", "W"}
        };

        auto it = codes.find(region);
        return it == codes.end() ? "UNKNOWN" : it->second;
    }

    static std::string classifyPriority(double amount) {
        if (amount >= 100000.0) {
            return "High";
        }
        if (amount >= 30000.0) {
            return "Medium";
        }
        return "Low";
    }

    static void validate(const std::vector<Order>& orders) {
        std::unordered_set<int> ids;

        for (const auto& order : orders) {
            if (order.id <= 0) {
                throw std::invalid_argument("Order ID must be positive");
            }

            if (!ids.insert(order.id).second) {
                throw std::invalid_argument(
                    "Duplicate order ID: " + std::to_string(order.id)
                );
            }

            if (order.quantity <= 0) {
                throw std::invalid_argument(
                    "Quantity must be positive for order " +
                    std::to_string(order.id)
                );
            }

            if (order.unitPrice < 0.0) {
                throw std::invalid_argument(
                    "Unit price cannot be negative for order " +
                    std::to_string(order.id)
                );
            }
        }
    }

public:
    static std::vector<Order> transform(std::vector<Order> orders) {
        validate(orders);

        // The transformation is performed in one pass: O(n) time and O(1)
        // additional storage per record. This differs from a dataframe model
        // by making ownership and mutation explicit.
        for (auto& order : orders) {
            order.status = normalizeStatus(order.status);
            order.regionCode = regionCode(order.region);

            order.grossAmount =
                static_cast<double>(order.quantity) * order.unitPrice;

            order.discountRate =
                order.grossAmount >= 100000.0
                    ? 0.10
                    : order.grossAmount >= 50000.0
                        ? 0.05
                        : 0.0;

            order.netAmount =
                order.grossAmount * (1.0 - order.discountRate);

            order.priority = classifyPriority(order.netAmount);
        }

        return orders;
    }

    static std::vector<Order> filterActive(
        const std::vector<Order>& orders
    ) {
        std::vector<Order> result;
        result.reserve(orders.size());

        std::copy_if(
            orders.begin(),
            orders.end(),
            std::back_inserter(result),
            [](const Order& order) {
                return order.status != "Cancelled" &&
                       order.netAmount >= 30000.0;
            }
        );

        return result;
    }

    static void sortForOperations(std::vector<Order>& orders) {
        static const std::unordered_map<std::string, int> rank{
            {"High", 0},
            {"Medium", 1},
            {"Low", 2}
        };

        std::stable_sort(
            orders.begin(),
            orders.end(),
            [&rank](const Order& a, const Order& b) {
                int priorityA = rank.at(a.priority);
                int priorityB = rank.at(b.priority);

                if (priorityA != priorityB) {
                    return priorityA < priorityB;
                }

                return a.netAmount > b.netAmount;
            }
        );
    }

    static void print(const std::vector<Order>& orders) {
        std::cout << std::left
                  << std::setw(6) << "ID"
                  << std::setw(10) << "Region"
                  << std::setw(14) << "Product"
                  << std::setw(10) << "Status"
                  << std::setw(12) << "Gross"
                  << std::setw(12) << "Net"
                  << std::setw(10) << "Priority"
                  << '\n';

        std::cout << std::string(74, '-') << '\n';

        for (const auto& order : orders) {
            std::cout << std::left
                      << std::setw(6) << order.id
                      << std::setw(10) << order.regionCode
                      << std::setw(14) << order.product
                      << std::setw(10) << order.status
                      << std::setw(12) << std::fixed
                      << std::setprecision(2) << order.grossAmount
                      << std::setw(12) << order.netAmount
                      << std::setw(10) << order.priority
                      << '\n';
        }
    }

    static std::map<std::string, double> regionalRevenue(
        const std::vector<Order>& orders
    ) {
        std::map<std::string, double> result;

        for (const auto& order : orders) {
            if (order.status == "Completed") {
                result[order.region] += order.netAmount;
            }
        }

        return result;
    }
};

int main() {
    try {
        std::vector<Order> orders{
            {1001, "Asha", "North", "Laptop", 2, 75000, "completed"},
            {1002, "Ravi", "South", "Monitor", 3, 18000, "completed"},
            {1003, "Meera", "West", "Keyboard", 5, 3500, "pending"},
            {1004, "Kabir", "East", "Laptop", 1, 82000, "cancelled"},
            {1005, "Asha", "North", "Mouse", 4, 1500, "completed"},
            {1006, "Ravi", "South", "Laptop", 2, 78000, "completed"},
            {1007, "Meera", "West", "Monitor", 2, 19500, "pending"}
        };

        auto transformed =
            RepositoryTransformationEngine::transform(orders);

        auto active =
            RepositoryTransformationEngine::filterActive(transformed);

        RepositoryTransformationEngine::sortForOperations(active);

        std::cout << "TRANSFORMED ORDERS\n";
        RepositoryTransformationEngine::print(transformed);

        std::cout << "\nFILTERED AND SORTED ORDERS\n";
        RepositoryTransformationEngine::print(active);

        std::cout << "\nREGIONAL COMPLETED REVENUE\n";
        auto revenue =
            RepositoryTransformationEngine::regionalRevenue(transformed);

        for (const auto& [region, amount] : revenue) {
            std::cout << region << ": "
                      << std::fixed << std::setprecision(2)
                      << amount << '\n';
        }

        // A failed transformation is surfaced as an exception instead of
        // silently producing an invalid record.
        auto invalid = orders;
        invalid[0].quantity = 0;

        try {
            RepositoryTransformationEngine::transform(invalid);
        } catch (const std::exception& ex) {
            std::cout << "\nValidation correctly rejected invalid data: "
                      << ex.what() << '\n';
        }

    } catch (const std::exception& ex) {
        std::cerr << "Fatal transformation error: "
                  << ex.what() << '\n';
        return 1;
    }

    return 0;
}
