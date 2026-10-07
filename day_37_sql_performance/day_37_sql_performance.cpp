#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

/*
 * Repository-scale order analytics performance case study.
 *
 * The system models the core reasoning used by a relational database
 * optimizer:
 *
 *   sequential scan
 *   indexed access
 *   filtering selectivity
 *   composite index design
 *   nested-loop joins
 *   indexed nested-loop joins
 *   hash joins
 *   estimated versus actual cardinality
 *
 * The data structures are deliberately explicit so that access-path costs
 * can be observed rather than hidden behind a database engine.
 */

struct Order {
    int orderId;
    int customerId;
    int orderDay;
    int status;
    double amount;
};

struct Customer {
    int customerId;
    int region;
};

struct PlanEstimate {
    std::string accessPath;
    double cost;
    std::size_t estimatedRows;
};

struct ExecutionResult {
    std::size_t returnedRows{};
    std::size_t examinedRows{};
};

using CustomerIndex = std::unordered_map<int, std::vector<const Order*>>;

std::vector<Customer> generateCustomers(std::size_t count) {
    std::vector<Customer> customers;
    customers.reserve(count);

    for (std::size_t i = 1; i <= count; ++i) {
        customers.push_back(
            Customer{
                static_cast<int>(i),
                static_cast<int>(i % 4)
            }
        );
    }

    return customers;
}

std::vector<Order> generateOrders(
    std::size_t count,
    std::size_t customerCount
) {
    std::mt19937 generator(42);
    std::uniform_int_distribution<int> customerDistribution(
        1,
        static_cast<int>(customerCount)
    );
    std::uniform_int_distribution<int> dayDistribution(1, 273);
    std::uniform_int_distribution<int> statusDistribution(1, 100);
    std::uniform_real_distribution<double> amountDistribution(
        10.0,
        25000.0
    );

    std::vector<Order> orders;
    orders.reserve(count);

    for (std::size_t i = 1; i <= count; ++i) {
        const int statusRoll = statusDistribution(generator);
        int status;

        if (statusRoll <= 5) {
            status = 0; // pending
        } else if (statusRoll <= 40) {
            status = 1; // paid
        } else if (statusRoll <= 85) {
            status = 2; // shipped
        } else if (statusRoll <= 93) {
            status = 3; // cancelled
        } else {
            status = 4; // refunded
        }

        orders.push_back(
            Order{
                static_cast<int>(i),
                customerDistribution(generator),
                dayDistribution(generator),
                status,
                amountDistribution(generator)
            }
        );
    }

    return orders;
}

CustomerIndex buildCustomerIndex(
    const std::vector<Order>& orders
) {
    CustomerIndex index;

    for (const Order& order : orders) {
        index[order.customerId].push_back(&order);
    }

    return index;
}

ExecutionResult sequentialScan(
    const std::vector<Order>& orders,
    const std::function<bool(const Order&)>& predicate
) {
    ExecutionResult result;

    for (const Order& order : orders) {
        ++result.examinedRows;

        if (predicate(order)) {
            ++result.returnedRows;
        }
    }

    return result;
}

ExecutionResult indexedScan(
    const CustomerIndex& index,
    int customerId,
    const std::function<bool(const Order&)>& predicate
) {
    ExecutionResult result;

    auto found = index.find(customerId);

    if (found == index.end()) {
        return result;
    }

    for (const Order* order : found->second) {
        ++result.examinedRows;

        if (predicate(*order)) {
            ++result.returnedRows;
        }
    }

    return result;
}

PlanEstimate chooseAccessPath(
    std::size_t tableRows,
    std::size_t matchingRows
) {
    if (tableRows == 0) {
        return {"Sequential Scan", 0.0, 0};
    }

    const double sequentialCost =
        static_cast<double>(tableRows) * 0.01;

    const double treeTraversal =
        std::ceil(std::log2(
            static_cast<double>(std::max<std::size_t>(2, tableRows))
        ));

    const double indexCost =
        treeTraversal +
        static_cast<double>(matchingRows) * 4.0 * 0.05 +
        static_cast<double>(matchingRows) * 0.01;

    if (indexCost < sequentialCost) {
        return {
            "Index Scan",
            indexCost,
            matchingRows
        };
    }

    return {
        "Sequential Scan",
        sequentialCost,
        matchingRows
    };
}

std::size_t estimateCustomerRows(
    const std::vector<Order>& orders,
    int customerId
) {
    return static_cast<std::size_t>(
        std::count_if(
            orders.begin(),
            orders.end(),
            [customerId](const Order& order) {
                return order.customerId == customerId;
            }
        )
    );
}

std::size_t naiveNestedLoopJoin(
    const std::vector<Customer>& customers,
    const std::vector<Order>& orders
) {
    std::size_t comparisons = 0;
    std::size_t matches = 0;

    for (const Customer& customer : customers) {
        for (const Order& order : orders) {
            ++comparisons;

            if (customer.customerId == order.customerId) {
                ++matches;
            }
        }
    }

    std::cout
        << "Nested-loop matches: " << matches << '\n';

    return comparisons;
}

std::size_t indexedNestedLoopJoin(
    const std::vector<Customer>& customers,
    const CustomerIndex& index
) {
    std::size_t lookups = 0;
    std::size_t matches = 0;

    for (const Customer& customer : customers) {
        ++lookups;

        auto found = index.find(customer.customerId);

        if (found != index.end()) {
            matches += found->second.size();
        }
    }

    std::cout
        << "Indexed nested-loop matches: " << matches << '\n';

    return lookups;
}

std::size_t hashJoin(
    const std::vector<Customer>& customers,
    const std::vector<Order>& orders
) {
    std::unordered_map<int, const Customer*> customerHash;

    customerHash.reserve(customers.size());

    for (const Customer& customer : customers) {
        customerHash.emplace(
            customer.customerId,
            &customer
        );
    }

    std::size_t probes = 0;
    std::size_t matches = 0;

    for (const Order& order : orders) {
        ++probes;

        if (customerHash.find(order.customerId) !=
            customerHash.end()) {
            ++matches;
        }
    }

    std::cout
        << "Hash-join matches: " << matches << '\n';

    return probes;
}

void printPlan(
    const PlanEstimate& plan,
    std::size_t actualRows
) {
    std::cout
        << std::left
        << std::setw(22)
        << plan.accessPath
        << " estimated_rows="
        << std::setw(8)
        << plan.estimatedRows
        << " actual_rows="
        << std::setw(8)
        << actualRows
        << " cost="
        << std::fixed
        << std::setprecision(2)
        << plan.cost
        << '\n';

    if (plan.estimatedRows == 0) {
        return;
    }

    const double ratio =
        static_cast<double>(actualRows) /
        static_cast<double>(plan.estimatedRows);

    if (ratio > 10.0 || ratio < 0.1) {
        std::cout
            << "  Warning: substantial cardinality mismatch. "
            << "Statistics or data distribution may need investigation.\n";
    }
}

void compositeIndexCaseStudy(
    const std::vector<Order>& orders
) {
    /*
     * A composite index on (customer_id, order_day) is represented here by
     * sorting each customer's rows by day. The leading equality predicate
     * narrows the search to one customer, then a binary search identifies
     * the beginning of the date range.
     */
    CustomerIndex index = buildCustomerIndex(orders);

    for (auto& [customerId, customerOrders] : index) {
        std::sort(
            customerOrders.begin(),
            customerOrders.end(),
            [](const Order* left, const Order* right) {
                return left->orderDay < right->orderDay;
            }
        );
    }

    const int customerId = 731;
    const int minimumDay = 244;

    auto found = index.find(customerId);

    if (found == index.end()) {
        std::cout
            << "Composite index lookup returned no rows.\n";
        return;
    }

    const auto& customerOrders = found->second;

    auto firstMatching = std::lower_bound(
        customerOrders.begin(),
        customerOrders.end(),
        minimumDay,
        [](const Order* order, int day) {
            return order->orderDay < day;
        }
    );

    const std::size_t resultCount =
        static_cast<std::size_t>(
            customerOrders.end() - firstMatching
        );

    std::cout
        << "Composite-index case: customer="
        << customerId
        << " date-day>="
        << minimumDay
        << " matching_rows="
        << resultCount
        << '\n';
}

void filterEfficiencyCaseStudy(
    const std::vector<Order>& orders
) {
    std::cout
        << "\n=== Filtering Efficiency ===\n";

    const int targetStatus = 2;
    const int minimumDay = 244;

    const auto sequential = sequentialScan(
        orders,
        [targetStatus, minimumDay](const Order& order) {
            return order.status == targetStatus &&
                   order.orderDay >= minimumDay;
        }
    );

    const CustomerIndex index =
        buildCustomerIndex(orders);

    const auto indexed = indexedScan(
        index,
        731,
        [minimumDay](const Order& order) {
            return order.status == 2 &&
                   order.orderDay >= minimumDay;
        }
    );

    std::cout
        << "Sequential scan examined="
        << sequential.examinedRows
        << " returned="
        << sequential.returnedRows
        << '\n';

    std::cout
        << "Indexed customer lookup examined="
        << indexed.examinedRows
        << " returned="
        << indexed.returnedRows
        << '\n';
}

void joinOptimizationCaseStudy(
    const std::vector<Customer>& customers,
    const std::vector<Order>& orders
) {
    std::cout
        << "\n=== Join Strategy Case Study ===\n";

    /*
     * The full production-like dataset is intentionally not passed through
     * the O(N*M) nested-loop implementation. That would obscure the lesson
     * by spending most of the runtime performing comparisons.
     *
     * A reduced sample demonstrates the algorithmic difference safely.
     */
    std::vector<Customer> sampleCustomers(
        customers.begin(),
        customers.begin() + 100
    );

    std::vector<Order> sampleOrders(
        orders.begin(),
        orders.begin() + 2000
    );

    const std::size_t nestedComparisons =
        naiveNestedLoopJoin(
            sampleCustomers,
            sampleOrders
        );

    CustomerIndex index =
        buildCustomerIndex(sampleOrders);

    const std::size_t indexedLookups =
        indexedNestedLoopJoin(
            sampleCustomers,
            index
        );

    const std::size_t hashProbes =
        hashJoin(
            sampleCustomers,
            sampleOrders
        );

    std::cout
        << "Naive nested-loop comparisons="
        << nestedComparisons
        << '\n';

    std::cout
        << "Indexed nested-loop lookups="
        << indexedLookups
        << '\n';

    std::cout
        << "Hash-join probes="
        << hashProbes
        << '\n';

    /*
     * This distinction matters in real SQL:
     *
     * - A nested loop can be ideal for a tiny outer relation and selective
     *   indexed access on the inner relation.
     * - A hash join can be attractive for large equality joins when memory
     *   can accommodate the hash table.
     * - An optimizer may choose a different plan after statistics or data
     *   volume change.
     */
}

void performanceImplications() {
    std::cout
        << "\n=== Performance Implications ===\n";

    std::cout
        << "B-tree index lookup: approximately O(log N) to locate "
           "an ordered key, followed by work for matching rows.\n";

    std::cout
        << "Sequential scan: O(N) row examination, but with excellent "
           "sequential I/O characteristics and low planning complexity.\n";

    std::cout
        << "Hash join: expected O(N+M) for equality joins under normal "
           "hash behavior, subject to memory and spill behavior.\n";

    std::cout
        << "Naive nested loop: O(N*M), which becomes unsuitable when "
           "both relations grow without selective indexed access.\n";
}

int main() {
    constexpr std::size_t customerCount = 10'000;
    constexpr std::size_t orderCount = 100'000;

    std::cout
        << "SQL PERFORMANCE CASE STUDY\n"
        << "==========================\n";

    const auto customers =
        generateCustomers(customerCount);

    const auto orders =
        generateOrders(
            orderCount,
            customerCount
        );

    std::cout
        << "Customers: "
        << customers.size()
        << "\nOrders: "
        << orders.size()
        << "\n";

    const int targetCustomer = 731;

    const std::size_t actualMatchingRows =
        estimateCustomerRows(
            orders,
            targetCustomer
        );

    const PlanEstimate plan =
        chooseAccessPath(
            orders.size(),
            actualMatchingRows
        );

    std::cout
        << "\n=== Access Path Selection ===\n";

    printPlan(
        plan,
        actualMatchingRows
    );

    filterEfficiencyCaseStudy(orders);
    compositeIndexCaseStudy(orders);
    joinOptimizationCaseStudy(customers, orders);
    performanceImplications();

    std::cout
        << "\n=== Database Validation Principle ===\n"
        << "The simulator illustrates optimizer reasoning but does not "
           "replace PostgreSQL execution plans.\n"
        << "For a real query, inspect EXPLAIN (ANALYZE, BUFFERS), compare "
           "estimated and actual cardinalities, inspect scan and join "
           "nodes, and validate indexes against representative data.\n";

    return 0;
}
