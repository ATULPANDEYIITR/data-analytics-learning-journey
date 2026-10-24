#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

struct Customer {
    int id;
    string name;
    string region;
};

struct Order {
    int id;
    int customerId;
    double amount;
    string status;
};

struct Contact {
    int customerId;
    string email;
};

struct MergedOrder {
    int customerId;
    string customerName;
    string region;
    int orderId;
    double amount;
    string status;
    bool customerMatched;
};

enum class JoinType {
    Inner,
    Left,
    Right,
    Full
};

enum class Relationship {
    OneToOne,
    OneToMany
};

class CombinationError : public runtime_error {
public:
    explicit CombinationError(const string& message)
        : runtime_error(message) {}
};

unordered_map<int, Customer> indexCustomers(
    const vector<Customer>& customers
) {
    unordered_map<int, Customer> index;

    for (const auto& customer : customers) {
        if (!index.emplace(customer.id, customer).second) {
            throw CombinationError(
                "Duplicate customer key: " + to_string(customer.id)
            );
        }
    }

    return index;
}

unordered_map<int, vector<Order>> groupOrders(
    const vector<Order>& orders
) {
    unordered_map<int, vector<Order>> grouped;

    for (const auto& order : orders) {
        grouped[order.customerId].push_back(order);
    }

    return grouped;
}

void validateRelationship(
    const vector<Customer>& customers,
    const vector<Order>& orders,
    Relationship relationship
) {
    if (relationship == Relationship::OneToOne) {
        unordered_map<int, int> customerCounts;
        unordered_map<int, int> orderCounts;

        for (const auto& customer : customers) {
            ++customerCounts[customer.id];
        }

        for (const auto& order : orders) {
            ++orderCounts[order.customerId];
        }

        for (const auto& [key, count] : customerCounts) {
            if (count > 1 && orderCounts.contains(key)) {
                throw CombinationError(
                    "One-to-one relationship violated by customer key " +
                    to_string(key)
                );
            }
        }

        for (const auto& [key, count] : orderCounts) {
            if (count > 1 && customerCounts.contains(key)) {
                throw CombinationError(
                    "One-to-one relationship violated by order key " +
                    to_string(key)
                );
            }
        }
    }

    if (relationship == Relationship::OneToMany) {
        unordered_map<int, int> customerCounts;

        for (const auto& customer : customers) {
            ++customerCounts[customer.id];
        }

        for (const auto& [key, count] : customerCounts) {
            if (count > 1) {
                throw CombinationError(
                    "Left side is not unique for key " + to_string(key)
                );
            }
        }
    }
}

vector<MergedOrder> mergeOrders(
    const vector<Customer>& customers,
    const vector<Order>& orders,
    JoinType joinType,
    Relationship relationship
) {
    validateRelationship(customers, orders, relationship);

    const auto customerIndex = indexCustomers(customers);
    const auto orderGroups = groupOrders(orders);

    vector<MergedOrder> result;
    set<int> matchedCustomerIds;

    for (const auto& customer : customers) {
        auto it = orderGroups.find(customer.id);

        if (it != orderGroups.end()) {
            matchedCustomerIds.insert(customer.id);

            for (const auto& order : it->second) {
                result.push_back({
                    customer.id,
                    customer.name,
                    customer.region,
                    order.id,
                    order.amount,
                    order.status,
                    true
                });
            }
        } else if (
            joinType == JoinType::Left ||
            joinType == JoinType::Full
        ) {
            result.push_back({
                customer.id,
                customer.name,
                customer.region,
                -1,
                0.0,
                "NO_ORDER",
                false
            });
        }
    }

    if (joinType == JoinType::Right || joinType == JoinType::Full) {
        for (const auto& order : orders) {
            if (!customerIndex.contains(order.customerId)) {
                result.push_back({
                    order.customerId,
                    "UNKNOWN_CUSTOMER",
                    "UNKNOWN",
                    order.id,
                    order.amount,
                    order.status,
                    false
                });
            }
        }
    }

    return result;
}

vector<Customer> customerDifference(
    const vector<Customer>& customers,
    const vector<Order>& orders
) {
    unordered_set<int> orderKeys;

    for (const auto& order : orders) {
        orderKeys.insert(order.customerId);
    }

    vector<Customer> result;

    for (const auto& customer : customers) {
        if (!orderKeys.contains(customer.id)) {
            result.push_back(customer);
        }
    }

    return result;
}

vector<Order> orderDifference(
    const vector<Customer>& customers,
    const vector<Order>& orders
) {
    unordered_set<int> customerKeys;

    for (const auto& customer : customers) {
        customerKeys.insert(customer.id);
    }

    vector<Order> result;

    for (const auto& order : orders) {
        if (!customerKeys.contains(order.customerId)) {
            result.push_back(order);
        }
    }

    return result;
}

vector<Order> concatRows(
    const vector<Order>& first,
    const vector<Order>& second,
    bool verifyIntegrity
) {
    vector<Order> result;
    result.reserve(first.size() + second.size());

    set<int> ids;

    auto append = [&](const vector<Order>& source) {
        for (const auto& order : source) {
            if (verifyIntegrity && !ids.insert(order.id).second) {
                throw CombinationError(
                    "Duplicate order ID during concatenation: " +
                    to_string(order.id)
                );
            }

            result.push_back(order);
        }
    };

    append(first);
    append(second);

    return result;
}

map<int, double> aggregateCustomerAmounts(
    const vector<MergedOrder>& rows
) {
    map<int, double> totals;

    for (const auto& row : rows) {
        if (row.orderId != -1) {
            totals[row.customerId] += row.amount;
        }
    }

    return totals;
}

void printMerged(const vector<MergedOrder>& rows) {
    cout << "\n=== Merge Result ===\n";
    cout << left
         << setw(10) << "Customer"
         << setw(16) << "Name"
         << setw(10) << "Order"
         << setw(12) << "Amount"
         << setw(12) << "Status"
         << '\n';

    for (const auto& row : rows) {
        cout << left
             << setw(10) << row.customerId
             << setw(16) << row.customerName
             << setw(10) << row.orderId
             << setw(12) << fixed << setprecision(2) << row.amount
             << setw(12) << row.status
             << '\n';
    }
}

int main() {
    try {
        const vector<Customer> customers = {
            {1, "Atul", "North"},
            {2, "Priya", "South"},
            {3, "Rahul", "North"},
            {4, "Neha", "West"}
        };

        const vector<Order> orders = {
            {101, 1, 1200.0, "paid"},
            {102, 2, 850.0, "paid"},
            {103, 2, 450.0, "pending"},
            {104, 5, 700.0, "paid"},
            {105, 3, 1500.0, "paid"}
        };

        const vector<Order> january = {
            {101, 1, 1200.0, "paid"},
            {102, 2, 850.0, "paid"}
        };

        const vector<Order> february = {
            {103, 2, 450.0, "pending"},
            {104, 5, 700.0, "paid"},
            {105, 3, 1500.0, "paid"}
        };

        const auto merged = mergeOrders(
            customers,
            orders,
            JoinType::Left,
            Relationship::OneToMany
        );

        printMerged(merged);

        const auto totals = aggregateCustomerAmounts(merged);

        cout << "\n=== Customer Aggregates ===\n";
        for (const auto& [customerId, amount] : totals) {
            cout << "Customer " << customerId
                 << ": " << fixed << setprecision(2)
                 << amount << '\n';
        }

        const auto missingCustomers =
            customerDifference(customers, orders);

        cout << "\n=== Customers Without Orders ===\n";
        for (const auto& customer : missingCustomers) {
            cout << customer.id << " " << customer.name << '\n';
        }

        const auto orphanOrders =
            orderDifference(customers, orders);

        cout << "\n=== Orders Without Customers ===\n";
        for (const auto& order : orphanOrders) {
            cout << order.id << " customer=" << order.customerId << '\n';
        }

        const auto combined =
            concatRows(january, february, true);

        cout << "\n=== Concatenated Orders ===\n";
        for (const auto& order : combined) {
            cout << order.id << " "
                 << order.customerId << " "
                 << order.amount << '\n';
        }

        cout << "\n=== Expected Relationship Failure ===\n";

        vector<Customer> duplicateCustomers = customers;
        duplicateCustomers.push_back({1, "Duplicate", "East"});

        try {
            mergeOrders(
                duplicateCustomers,
                orders,
                JoinType::Left,
                Relationship::OneToMany
            );
        } catch (const CombinationError& error) {
            cout << error.what() << '\n';
        }

        if (merged.size() != 6) {
            throw CombinationError("Unexpected left merge size.");
        }

        if (orphanOrders.size() != 1 ||
            orphanOrders.front().id != 104) {
            throw CombinationError("Unexpected orphan-order detection.");
        }

        cout << "\nAll C++17 validation checks passed.\n";
        cout << "Key-based combination uses hash indexes, giving "
             << "approximately O(n + m) expected merge time.\n";
        cout << "Result materialization requires O(n + m + r) memory, "
             << "where r is the number of produced joined rows.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
