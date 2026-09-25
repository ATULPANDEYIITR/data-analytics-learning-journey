/*
 * SQL Aggregations - C++ Industry-Style Case Study
 *
 * Scenario:
 * A commerce analytics system receives order records and needs to produce
 * trustworthy operational and financial reports.
 *
 * The program models important SQL aggregation semantics:
 *   COUNT(*)
 *   COUNT(column)
 *   COUNT(DISTINCT column)
 *   SUM
 *   AVG
 *   MIN
 *   MAX
 *   NULL handling
 *   COALESCE-style fallback behavior
 *   conditional aggregation
 *   GROUP BY
 *   HAVING-style filtering
 *   aggregate expressions
 *   join multiplication risks
 *
 * The implementation uses std::optional to represent SQL NULL.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp -o aggregation_case_study
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

struct Order {
    int orderId;
    string customer;
    string category;
    optional<int> quantity;
    optional<double> unitPrice;
    optional<double> discount;
    string status;
};

struct CategoryReport {
    string category;
    size_t orderCount = 0;
    size_t knownQuantityCount = 0;
    long long totalUnits = 0;
    optional<double> averageQuantity;
    optional<double> minimumQuantity;
    optional<double> maximumQuantity;
    optional<double> grossRevenue;
    optional<double> netRevenue;
};

template <typename T>
optional<T> sumOptional(const vector<optional<T>>& values) {
    bool foundValue = false;
    T total{};

    for (const auto& value : values) {
        // SQL SUM ignores NULL values.
        if (value.has_value()) {
            total += *value;
            foundValue = true;
        }
    }

    // SQL SUM returns NULL when there are no non-NULL values.
    if (!foundValue) {
        return nullopt;
    }

    return total;
}

template <typename T>
optional<double> averageOptional(const vector<optional<T>>& values) {
    double total = 0.0;
    size_t count = 0;

    for (const auto& value : values) {
        // SQL AVG ignores NULL values.
        if (value.has_value()) {
            total += static_cast<double>(*value);
            ++count;
        }
    }

    if (count == 0) {
        return nullopt;
    }

    return total / static_cast<double>(count);
}

template <typename T>
optional<T> minimumOptional(const vector<optional<T>>& values) {
    optional<T> result;

    for (const auto& value : values) {
        if (!value.has_value()) {
            continue;
        }

        if (!result.has_value() || *value < *result) {
            result = value;
        }
    }

    return result;
}

template <typename T>
optional<T> maximumOptional(const vector<optional<T>>& values) {
    optional<T> result;

    for (const auto& value : values) {
        if (!value.has_value()) {
            continue;
        }

        if (!result.has_value() || *value > *result) {
            result = value;
        }
    }

    return result;
}

template <typename T>
T coalesce(const optional<T>& value, T fallback) {
    // SQL COALESCE(value, fallback).
    return value.has_value() ? *value : fallback;
}

optional<double> nullIf(double value, double comparison) {
    // SQL NULLIF(value, comparison).
    if (value == comparison) {
        return nullopt;
    }

    return value;
}

string formatOptional(const optional<double>& value, int precision = 2) {
    if (!value.has_value()) {
        return "NULL";
    }

    ostringstream output;
    output << fixed << setprecision(precision) << *value;
    return output.str();
}

string formatOptionalInt(const optional<int>& value) {
    if (!value.has_value()) {
        return "NULL";
    }

    return to_string(*value);
}

vector<Order> createOrders() {
    return {
        {101, "Alice", "Laptop", 2, 80000.0, 0.10, "completed"},
        {102, "Bob", "Phone", 3, 30000.0, nullopt, "completed"},
        {103, "Alice", "Monitor", 1, 20000.0, 0.05, "completed"},
        {104, "Cara", "Phone", 2, nullopt, 0.10, "pending"},
        {105, "Bob", "Laptop", 1, 80000.0, nullopt, "completed"},
        {106, "Cara", "Tablet", 4, 25000.0, 0.15, "completed"},
        {107, "Alice", "Tablet", nullopt, 25000.0, 0.05, "cancelled"},
        {108, "David", "Phone", 5, 30000.0, 0.20, "completed"},
        {109, "Eva", "Laptop", nullopt, 80000.0, nullopt, "completed"}
    };
}

void printHeader(const string& title) {
    cout << "\n"
         << string(92, '=')
         << "\n"
         << title
         << "\n"
         << string(92, '=')
         << "\n";
}

void printOrders(const vector<Order>& orders) {
    cout << left
         << setw(8) << "ID"
         << setw(12) << "Customer"
         << setw(12) << "Category"
         << setw(10) << "Qty"
         << setw(14) << "UnitPrice"
         << setw(12) << "Discount"
         << setw(14) << "Status"
         << "\n";

    cout << string(82, '-') << "\n";

    for (const auto& order : orders) {
        cout << left
             << setw(8) << order.orderId
             << setw(12) << order.customer
             << setw(12) << order.category
             << setw(10) << formatOptionalInt(order.quantity)
             << setw(14) << formatOptional(order.unitPrice)
             << setw(12) << formatOptional(order.discount)
             << setw(14) << order.status
             << "\n";
    }
}

size_t countRows(const vector<Order>& orders) {
    // SQL COUNT(*).
    return orders.size();
}

size_t countQuantity(const vector<Order>& orders) {
    // SQL COUNT(quantity).
    return count_if(
        orders.begin(),
        orders.end(),
        [](const Order& order) {
            return order.quantity.has_value();
        }
    );
}

size_t countDistinctCustomers(const vector<Order>& orders) {
    // SQL COUNT(DISTINCT customer).
    set<string> customers;

    for (const auto& order : orders) {
        customers.insert(order.customer);
    }

    return customers.size();
}

optional<double> orderGrossValue(const Order& order) {
    /*
     * Aggregate expressions operate on row-level expressions first.
     *
     * SQL:
     *   quantity * unit_price
     *
     * If either operand is NULL, SQL's expression result is NULL.
     */
    if (!order.quantity.has_value() || !order.unitPrice.has_value()) {
        return nullopt;
    }

    return static_cast<double>(*order.quantity) * *order.unitPrice;
}

optional<double> orderNetValue(const Order& order) {
    /*
     * SQL:
     *
     * quantity * unit_price *
     * (1 - COALESCE(discount, 0))
     */
    if (!order.quantity.has_value() || !order.unitPrice.has_value()) {
        return nullopt;
    }

    const double normalizedDiscount = coalesce(order.discount, 0.0);

    return (
        static_cast<double>(*order.quantity) *
        *order.unitPrice *
        (1.0 - normalizedDiscount)
    );
}

void basicAggregationReport(const vector<Order>& orders) {
    printHeader("1. BASIC AGGREGATIONS");

    vector<optional<double>> prices;

    for (const auto& order : orders) {
        prices.push_back(order.unitPrice);
    }

    cout << "COUNT(*)                  : " << countRows(orders) << "\n";
    cout << "COUNT(quantity)           : " << countQuantity(orders) << "\n";
    cout << "COUNT(DISTINCT customer)  : "
         << countDistinctCustomers(orders)
         << "\n";
    cout << "SUM(unit_price)           : "
         << formatOptional(sumOptional(prices))
         << "\n";
    cout << "AVG(unit_price)           : "
         << formatOptional(averageOptional(prices))
         << "\n";
    cout << "MIN(unit_price)           : "
         << formatOptional(minimumOptional(prices))
         << "\n";
    cout << "MAX(unit_price)           : "
         << formatOptional(maximumOptional(prices))
         << "\n";
}

vector<Order> filterByStatus(
    const vector<Order>& orders,
    const string& status
) {
    vector<Order> result;

    for (const auto& order : orders) {
        if (order.status == status) {
            result.push_back(order);
        }
    }

    return result;
}

void revenueReport(const vector<Order>& orders) {
    printHeader("2. REVENUE AGGREGATION");

    const auto completed = filterByStatus(orders, "completed");

    vector<optional<double>> grossValues;
    vector<optional<double>> netValues;

    for (const auto& order : completed) {
        grossValues.push_back(orderGrossValue(order));
        netValues.push_back(orderNetValue(order));
    }

    cout << "Completed order rows : " << completed.size() << "\n";
    cout << "Gross revenue        : "
         << formatOptional(sumOptional(grossValues))
         << "\n";
    cout << "Net revenue          : "
         << formatOptional(sumOptional(netValues))
         << "\n";
    cout << "Average order value  : "
         << formatOptional(averageOptional(netValues))
         << "\n";

    cout << "\nEquivalent SQL structure:\n";
    cout << "SELECT\n"
         << "    SUM(quantity * unit_price) AS gross_revenue,\n"
         << "    SUM(quantity * unit_price *\n"
         << "        (1 - COALESCE(discount, 0))) AS net_revenue\n"
         << "FROM orders\n"
         << "WHERE status = 'completed';\n";
}

vector<CategoryReport> buildCategoryReports(
    const vector<Order>& orders
) {
    /*
     * GROUP BY category is represented with a map.
     *
     * std::map provides deterministic alphabetical ordering.
     */
    map<string, vector<Order>> groups;

    for (const auto& order : orders) {
        groups[order.category].push_back(order);
    }

    vector<CategoryReport> reports;

    for (const auto& [category, rows] : groups) {
        CategoryReport report;
        report.category = category;
        report.orderCount = rows.size();

        vector<optional<int>> quantities;
        vector<optional<double>> grossValues;
        vector<optional<double>> netValues;

        for (const auto& order : rows) {
            quantities.push_back(order.quantity);
            grossValues.push_back(orderGrossValue(order));
            netValues.push_back(orderNetValue(order));
        }

        report.knownQuantityCount =
            count_if(
                quantities.begin(),
                quantities.end(),
                [](const optional<int>& value) {
                    return value.has_value();
                }
            );

        const auto totalQuantity = sumOptional(quantities);

        if (totalQuantity.has_value()) {
            report.totalUnits = *totalQuantity;
        }

        report.averageQuantity = averageOptional(quantities);
        report.minimumQuantity = minimumOptional(quantities);
        report.maximumQuantity = maximumOptional(quantities);
        report.grossRevenue = sumOptional(grossValues);
        report.netRevenue = sumOptional(netValues);

        reports.push_back(report);
    }

    return reports;
}

void printCategoryReports(const vector<CategoryReport>& reports) {
    printHeader("3. GROUP BY CATEGORY REPORT");

    cout << left
         << setw(12) << "Category"
         << setw(10) << "Orders"
         << setw(12) << "KnownQty"
         << setw(12) << "Units"
         << setw(14) << "AvgQty"
         << setw(14) << "MinQty"
         << setw(14) << "MaxQty"
         << setw(16) << "NetRevenue"
         << "\n";

    cout << string(104, '-') << "\n";

    for (const auto& report : reports) {
        cout << left
             << setw(12) << report.category
             << setw(10) << report.orderCount
             << setw(12) << report.knownQuantityCount
             << setw(12) << report.totalUnits
             << setw(14) << formatOptional(report.averageQuantity)
             << setw(14) << formatOptional(
                    report.minimumQuantity.has_value()
                        ? optional<double>(
                            static_cast<double>(*report.minimumQuantity)
                        )
                        : nullopt
                )
             << setw(14) << formatOptional(
                    report.maximumQuantity.has_value()
                        ? optional<double>(
                            static_cast<double>(*report.maximumQuantity)
                        )
                        : nullopt
                )
             << setw(16) << formatOptional(report.netRevenue)
             << "\n";
    }
}

void havingStyleAnalysis(
    const vector<CategoryReport>& reports,
    double minimumRevenue
) {
    /*
     * SQL HAVING filters groups after GROUP BY.
     *
     * This loop represents:
     *
     * HAVING SUM(...) >= minimumRevenue
     */
    printHeader("4. HAVING-STYLE GROUP FILTER");

    cout << "Minimum net revenue threshold: "
         << fixed << setprecision(2)
         << minimumRevenue << "\n\n";

    for (const auto& report : reports) {
        if (
            report.netRevenue.has_value() &&
            *report.netRevenue >= minimumRevenue
        ) {
            cout << report.category
                 << " -> "
                 << formatOptional(report.netRevenue)
                 << "\n";
        }
    }
}

void conditionalAggregation(const vector<Order>& orders) {
    printHeader("5. CONDITIONAL AGGREGATION");

    /*
     * SQL pattern:
     *
     * SUM(CASE WHEN condition THEN 1 ELSE 0 END)
     *
     * This is frequently used for KPI dashboards.
     */
    size_t completed = 0;
    size_t pending = 0;
    size_t cancelled = 0;
    size_t missingQuantity = 0;

    for (const auto& order : orders) {
        if (order.status == "completed") {
            ++completed;
        }

        if (order.status == "pending") {
            ++pending;
        }

        if (order.status == "cancelled") {
            ++cancelled;
        }

        if (!order.quantity.has_value()) {
            ++missingQuantity;
        }
    }

    cout << "Completed orders : " << completed << "\n";
    cout << "Pending orders   : " << pending << "\n";
    cout << "Cancelled orders : " << cancelled << "\n";
    cout << "Missing quantity : " << missingQuantity << "\n";
}

void customerAnalysis(const vector<Order>& orders) {
    printHeader("6. CUSTOMER-LEVEL AGGREGATION");

    map<string, vector<Order>> groups;

    for (const auto& order : orders) {
        groups[order.customer].push_back(order);
    }

    cout << left
         << setw(14) << "Customer"
         << setw(10) << "Orders"
         << setw(16) << "NetRevenue"
         << setw(16) << "AvgOrderValue"
         << "\n";

    cout << string(56, '-') << "\n";

    for (const auto& [customer, rows] : groups) {
        vector<optional<double>> revenue;

        for (const auto& order : rows) {
            if (order.status == "completed") {
                revenue.push_back(orderNetValue(order));
            }
        }

        cout << left
             << setw(14) << customer
             << setw(10) << rows.size()
             << setw(16) << formatOptional(sumOptional(revenue))
             << setw(16) << formatOptional(averageOptional(revenue))
             << "\n";
    }
}

void joinMultiplicationCaseStudy(const vector<Order>& orders) {
    printHeader("7. ONE-TO-MANY JOIN MULTIPLICATION");

    struct OrderTag {
        int orderId;
        string tag;
    };

    const vector<OrderTag> tags = {
        {101, "priority"},
        {101, "online"},
        {102, "online"},
        {103, "store"}
    };

    /*
     * Suppose a query joins orders to tags.
     * Order 101 appears twice because it has two tags.
     *
     * SELECT COUNT(*) counts joined rows, not original orders.
     */
    vector<pair<int, string>> joinedRows;

    for (const auto& order : orders) {
        for (const auto& tag : tags) {
            if (order.orderId == tag.orderId) {
                joinedRows.emplace_back(order.orderId, tag.tag);
            }
        }
    }

    set<int> distinctOrderIds;

    for (const auto& joined : joinedRows) {
        distinctOrderIds.insert(joined.first);
    }

    cout << "Joined row count: " << joinedRows.size() << "\n";
    cout << "Distinct order count: " << distinctOrderIds.size() << "\n";

    cout << "\nThe distinction corresponds to:\n";
    cout << "COUNT(*)\n";
    cout << "COUNT(DISTINCT orders.order_id)\n";

    cout << "\nA SUM over a measure from the duplicated side can also be inflated.\n";
}

void nullSemanticsCaseStudy() {
    printHeader("8. NULL SEMANTICS");

    const vector<optional<double>> values = {
        10.0,
        20.0,
        nullopt,
        30.0,
        nullopt
    };

    cout << "Input values: 10, 20, NULL, 30, NULL\n";
    cout << "COUNT(*) conceptual rows: " << values.size() << "\n";

    size_t knownValues = count_if(
        values.begin(),
        values.end(),
        [](const optional<double>& value) {
            return value.has_value();
        }
    );

    cout << "COUNT(value): " << knownValues << "\n";
    cout << "SUM(value): "
         << formatOptional(sumOptional(values))
         << "\n";
    cout << "AVG(value): "
         << formatOptional(averageOptional(values))
         << "\n";
    cout << "MIN(value): "
         << formatOptional(minimumOptional(values))
         << "\n";
    cout << "MAX(value): "
         << formatOptional(maximumOptional(values))
         << "\n";

    cout << "\nEmpty-set behavior:\n";

    const vector<optional<double>> empty;

    cout << "COUNT(*) = " << empty.size() << "\n";
    cout << "SUM = " << formatOptional(sumOptional(empty)) << "\n";
    cout << "AVG = " << formatOptional(averageOptional(empty)) << "\n";
    cout << "MIN = " << formatOptional(minimumOptional(empty)) << "\n";
    cout << "MAX = " << formatOptional(maximumOptional(empty)) << "\n";
}

void safeRatioCaseStudy() {
    printHeader("9. SAFE RATIO CALCULATION");

    const double successful = 0.0;
    const double attempts = 0.0;

    const auto safeDenominator = nullIf(attempts, 0.0);

    optional<double> rate;

    if (safeDenominator.has_value()) {
        rate = successful / *safeDenominator;
    } else {
        rate = nullopt;
    }

    cout << "Successful: " << successful << "\n";
    cout << "Attempts: " << attempts << "\n";
    cout << "Safe rate: " << formatOptional(rate) << "\n";

    cout << "\nSQL equivalent:\n";
    cout << "SUM(successful) / NULLIF(SUM(attempts), 0)\n";
}

void complexityAnalysis() {
    printHeader("10. ALGORITHM AND PERFORMANCE ANALYSIS");

    cout << R"(
For n input rows:

COUNT(*):
  Typical aggregation cost: O(n)

SUM:
  Typical aggregation cost: O(n)

AVG:
  Typical aggregation cost: O(n)

MIN / MAX:
  Typical aggregation cost: O(n)

GROUP BY:
  Hash-based implementations are commonly O(n) expected time.
  Sort-based implementations are commonly O(n log n).

COUNT(DISTINCT value):
  Usually requires maintaining a distinct-value structure or sorting.
  Memory and time depend on the number of unique values.

ORDER BY after aggregation:
  If k groups are produced, sorting them generally costs O(k log k).

The exact behavior depends on the database engine, optimizer, indexes,
data distribution, execution plan, memory limits, and parallelism.
)";
}

void productionDesignConsiderations() {
    printHeader("11. PRODUCTION DESIGN CONSIDERATIONS");

    cout << R"(
1. Define exactly what one row represents before writing an aggregate.
2. Decide whether the metric counts rows, entities, events, or distinct IDs.
3. Understand whether NULL means unknown, missing, not applicable, or unavailable.
4. Do not blindly replace every NULL with zero.
5. Check one-to-many joins before SUM or COUNT.
6. Use conditional aggregation for compact KPI reports.
7. Use HAVING for conditions on aggregate results.
8. Use WHERE for row-level filtering.
9. Use appropriate numeric precision for financial calculations.
10. Test empty input sets.
11. Test NULL-heavy input.
12. Test duplicate records.
13. Test zero denominators in ratios.
14. Inspect execution plans for large production datasets.
15. Validate business definitions independently of SQL syntax.
)";
}

void runAssertions(const vector<Order>& orders) {
    printHeader("12. AUTOMATED VALIDATION");

    assert(countRows(orders) == 9);
    assert(countQuantity(orders) == 7);
    assert(countDistinctCustomers(orders) == 5);

    vector<optional<double>> prices;

    for (const auto& order : orders) {
        prices.push_back(order.unitPrice);
    }

    const auto minPrice = minimumOptional(prices);
    const auto maxPrice = maximumOptional(prices);

    assert(minPrice.has_value());
    assert(maxPrice.has_value());
    assert(*minPrice == 20000.0);
    assert(*maxPrice == 80000.0);

    const auto emptySum = sumOptional(vector<optional<double>>{});
    const auto emptyAverage = averageOptional(vector<optional<double>>{});

    assert(!emptySum.has_value());
    assert(!emptyAverage.has_value());

    cout << "PASS: COUNT(*)\n";
    cout << "PASS: COUNT(quantity)\n";
    cout << "PASS: COUNT(DISTINCT customer)\n";
    cout << "PASS: MIN(unit_price)\n";
    cout << "PASS: MAX(unit_price)\n";
    cout << "PASS: Empty SUM returns NULL\n";
    cout << "PASS: Empty AVG returns NULL\n";
    cout << "\nAll validation checks passed.\n";
}

void sqlReferenceQueries() {
    printHeader("13. SQL REFERENCE QUERIES");

    cout << R"(
Basic aggregate:

SELECT
    COUNT(*) AS row_count,
    COUNT(quantity) AS known_quantity_count,
    SUM(quantity) AS total_quantity,
    AVG(quantity) AS average_quantity,
    MIN(quantity) AS minimum_quantity,
    MAX(quantity) AS maximum_quantity
FROM orders;


Grouped aggregation:

SELECT
    category,
    COUNT(*) AS order_count,
    SUM(quantity) AS total_units,
    AVG(quantity) AS average_quantity
FROM orders
GROUP BY category;


Conditional aggregation:

SELECT
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
        AS completed_orders,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END)
        AS pending_orders
FROM orders;


NULL-safe financial aggregation:

SELECT
    SUM(
        quantity * unit_price *
        (1 - COALESCE(discount, 0))
    ) AS net_revenue
FROM orders
WHERE status = 'completed';


Group filtering:

SELECT
    category,
    SUM(quantity * unit_price) AS revenue
FROM orders
GROUP BY category
HAVING SUM(quantity * unit_price) > 100000;


Unique entity counting:

SELECT COUNT(DISTINCT customer)
FROM orders;
)";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    printHeader("SQL AGGREGATIONS - C++ INDUSTRY CASE STUDY");

    cout << R"(
Business scenario:
An e-commerce analytics service must calculate operational and financial
metrics from order data while preserving the semantics of missing values.

The C++ program uses std::optional to model SQL NULL and standard-library
containers to model grouping and distinct-value operations.
)";

    const vector<Order> orders = createOrders();

    printHeader("RAW ORDER DATA");
    printOrders(orders);

    basicAggregationReport(orders);
    revenueReport(orders);

    const vector<CategoryReport> categoryReports =
        buildCategoryReports(orders);

    printCategoryReports(categoryReports);
    havingStyleAnalysis(categoryReports, 100000.0);

    conditionalAggregation(orders);
    customerAnalysis(orders);
    joinMultiplicationCaseStudy(orders);
    nullSemanticsCaseStudy();
    safeRatioCaseStudy();
    complexityAnalysis();
    productionDesignConsiderations();
    sqlReferenceQueries();
    runAssertions(orders);

    printHeader("CASE STUDY CHECKLIST");

    const vector<string> checklist = {
        "COUNT(*) and COUNT(column)",
        "COUNT(DISTINCT ...)",
        "SUM and aggregate expressions",
        "AVG and NULL values",
        "MIN and MAX",
        "GROUP BY",
        "HAVING-style filtering",
        "Conditional aggregation",
        "COALESCE-style NULL handling",
        "NULLIF-style safe division",
        "Join multiplication",
        "Complexity considerations",
        "Production validation"
    };

    for (const auto& item : checklist) {
        cout << "[ ] " << item << "\n";
    }

    return 0;
}
