/*
 * SQL Subqueries: Industry-Style C++ Case Study
 *
 * Scenario:
 * A retail analytics service must identify customer segments, calculate
 * customer revenue, detect inactive products, find customers with qualifying
 * orders, and answer "bought every required product" questions.
 *
 * The program models relational tables using C++ standard-library containers.
 * Each function corresponds to a common SQL subquery pattern:
 *
 * 1. Scalar subquery
 * 2. Multi-row IN subquery
 * 3. EXISTS
 * 4. NOT EXISTS
 * 5. Correlated subquery
 * 6. Nested subquery
 * 7. Derived-table style aggregation
 * 8. Double NOT EXISTS / relational division
 * 9. NULL-related anti-join considerations
 * 10. Performance comparison between repeated scans and indexed lookup
 *
 * Compile:
 *     g++ -std=c++17 -O2 -Wall -Wextra -pedantic sql_subqueries_case_study.cpp -o subqueries
 *
 * Run:
 *     ./subqueries
 */

#include <algorithm>
#include <cassert>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

struct Customer {
    int id;
    std::string name;
    std::string city;
    std::string segment;
};

struct Product {
    int id;
    std::string name;
    std::string category;
    double price;
    bool active;
};

struct Order {
    int id;
    int customerId;
    std::string date;
    std::string status;
};

struct OrderItem {
    int orderId;
    int productId;
    int quantity;
    double unitPrice;
};

struct CustomerRevenue {
    int customerId;
    std::string customerName;
    double revenue;
};

struct OrderTotal {
    int orderId;
    double value;
};

class SalesAnalytics {
private:
    std::vector<Customer> customers;
    std::vector<Product> products;
    std::vector<Order> orders;
    std::vector<OrderItem> orderItems;

    /*
     * This index models what a relational database index on
     * orders(customer_id) can provide: fast access to related orders.
     */
    std::unordered_map<int, std::vector<const Order*>> ordersByCustomer;

    /*
     * This index models an index on order_items(product_id).
     */
    std::unordered_map<int, std::vector<const OrderItem*>> itemsByProduct;

public:
    SalesAnalytics() {
        loadData();
        buildIndexes();
    }

    void loadData() {
        customers = {
            {1, "Aarav Retail", "Lucknow", "Retail"},
            {2, "Bharat Foods", "Delhi", "Business"},
            {3, "Crescent Labs", "Bengaluru", "Enterprise"},
            {4, "Delta Stores", "Mumbai", "Retail"},
            {5, "Evergreen Systems", "Pune", "Enterprise"},
            {6, "Future Office", "Hyderabad", "Business"},
            {7, "Galaxy Traders", "Jaipur", "Business"},
            {8, "Horizon Retail", "Kolkata", "Retail"}
        };

        products = {
            {1, "Laptop Pro", "Computers", 90000.0, true},
            {2, "Office Laptop", "Computers", 60000.0, true},
            {3, "Mechanical Keyboard", "Accessories", 7000.0, true},
            {4, "Wireless Mouse", "Accessories", 2500.0, true},
            {5, "4K Monitor", "Displays", 30000.0, true},
            {6, "USB-C Dock", "Accessories", 12000.0, true},
            {7, "Server Rack", "Infrastructure", 50000.0, true},
            {8, "Network Switch", "Infrastructure", 18000.0, true},
            {9, "Legacy Monitor", "Displays", 10000.0, false}
        };

        orders = {
            {101, 1, "2026-01-05", "Delivered"},
            {102, 1, "2026-02-10", "Delivered"},
            {103, 2, "2026-01-15", "Shipped"},
            {104, 2, "2026-03-01", "Delivered"},
            {105, 3, "2026-01-20", "Delivered"},
            {106, 3, "2026-02-21", "Delivered"},
            {107, 4, "2026-02-05", "Cancelled"},
            {108, 4, "2026-03-11", "Delivered"},
            {109, 5, "2026-01-25", "Delivered"},
            {110, 5, "2026-03-14", "Delivered"},
            {111, 6, "2026-02-18", "Pending"},
            {112, 7, "2026-03-15", "Delivered"}
        };

        orderItems = {
            {101, 1, 1, 90000},
            {101, 3, 2, 7000},
            {102, 5, 2, 30000},
            {102, 4, 2, 2500},
            {103, 2, 3, 60000},
            {103, 4, 3, 2500},
            {104, 7, 1, 50000},
            {104, 8, 2, 18000},
            {105, 1, 2, 90000},
            {105, 6, 2, 12000},
            {106, 5, 3, 30000},
            {106, 3, 5, 7000},
            {107, 9, 2, 10000},
            {108, 2, 2, 60000},
            {108, 4, 4, 2500},
            {109, 7, 2, 50000},
            {109, 8, 2, 18000},
            {110, 1, 1, 90000},
            {110, 6, 1, 12000},
            {111, 3, 3, 7000},
            {112, 8, 5, 18000}
        };
    }

    void buildIndexes() {
        ordersByCustomer.clear();
        itemsByProduct.clear();

        for (const auto& order : orders) {
            ordersByCustomer[order.customerId].push_back(&order);
        }

        for (const auto& item : orderItems) {
            itemsByProduct[item.productId].push_back(&item);
        }
    }

    static void section(const std::string& title) {
        std::cout << "\n" << std::string(78, '=') << "\n";
        std::cout << title << "\n";
        std::cout << std::string(78, '=') << "\n";
    }

    double averageProductPrice() const {
        if (products.empty()) {
            throw std::runtime_error("Cannot calculate average of empty product set.");
        }

        const double total = std::accumulate(
            products.begin(),
            products.end(),
            0.0,
            [](double current, const Product& product) {
                return current + product.price;
            }
        );

        return total / static_cast<double>(products.size());
    }

    /*
     * Scalar-subquery equivalent:
     *
     * SELECT AVG(price) FROM products
     *
     * The returned value is then used by an outer query.
     */
    void scalarSubquery() const {
        section("1. Scalar subquery: products above global average");

        const double averagePrice = averageProductPrice();

        std::cout << "Global average product price: "
                  << std::fixed << std::setprecision(2)
                  << averagePrice << "\n\n";

        for (const auto& product : products) {
            if (product.price > averagePrice) {
                std::cout << product.name
                          << " | price=" << product.price
                          << " | above average by="
                          << product.price - averagePrice
                          << "\n";
            }
        }
    }

    /*
     * SQL equivalent concept:
     *
     * WHERE customer_id IN (
     *     SELECT customer_id
     *     FROM orders
     *     WHERE status = 'Delivered'
     * )
     *
     * A set gives the C++ implementation the same membership semantics.
     */
    std::unordered_set<int> deliveredCustomerIds() const {
        std::unordered_set<int> result;

        for (const auto& order : orders) {
            if (order.status == "Delivered") {
                result.insert(order.customerId);
            }
        }

        return result;
    }

    void multiRowInSubquery() const {
        section("2. Multi-row IN subquery");

        const auto deliveredIds = deliveredCustomerIds();

        std::cout << "Customers with delivered orders:\n";

        for (const auto& customer : customers) {
            if (deliveredIds.contains(customer.id)) {
                std::cout << customer.id << " | "
                          << customer.name << "\n";
            }
        }
    }

    /*
     * EXISTS should be used when the question is about whether at least one
     * matching row exists, rather than when values from the inner relation
     * are actually needed.
     *
     * SQL shape:
     *
     * WHERE EXISTS (
     *     SELECT 1
     *     FROM orders o
     *     WHERE o.customer_id = c.customer_id
     * )
     */
    bool hasDeliveredOrder(int customerId) const {
        auto iterator = ordersByCustomer.find(customerId);

        if (iterator == ordersByCustomer.end()) {
            return false;
        }

        for (const Order* order : iterator->second) {
            if (order->status == "Delivered") {
                return true;
            }
        }

        return false;
    }

    void existsSubquery() const {
        section("3. EXISTS: customers with at least one delivered order");

        for (const auto& customer : customers) {
            if (hasDeliveredOrder(customer.id)) {
                std::cout << customer.name << "\n";
            }
        }
    }

    /*
     * NOT EXISTS is the anti-existence form.
     *
     * SQL:
     *
     * WHERE NOT EXISTS (
     *     SELECT 1
     *     FROM order_items oi
     *     WHERE oi.product_id = p.product_id
     * )
     */
    bool productWasNeverOrdered(int productId) const {
        auto iterator = itemsByProduct.find(productId);

        return iterator == itemsByProduct.end() || iterator->second.empty();
    }

    void notExistsSubquery() const {
        section("4. NOT EXISTS: products that have never been ordered");

        for (const auto& product : products) {
            if (productWasNeverOrdered(product.id)) {
                std::cout << product.id << " | "
                          << product.name << "\n";
            }
        }
    }

    /*
     * Correlated scalar subquery:
     *
     * SELECT c.customer_name,
     *        (
     *            SELECT MAX(o.order_date)
     *            FROM orders o
     *            WHERE o.customer_id = c.customer_id
     *        )
     * FROM customers c;
     *
     * The inner operation depends on the current customer.
     */
    std::optional<std::string> latestOrderDate(int customerId) const {
        auto iterator = ordersByCustomer.find(customerId);

        if (iterator == ordersByCustomer.end() ||
            iterator->second.empty()) {
            return std::nullopt;
        }

        std::string latest;

        for (const Order* order : iterator->second) {
            if (latest.empty() || order->date > latest) {
                latest = order->date;
            }
        }

        return latest;
    }

    void correlatedScalarSubquery() const {
        section("5. Correlated scalar subquery: latest order per customer");

        for (const auto& customer : customers) {
            const auto latest = latestOrderDate(customer.id);

            std::cout << customer.name << " | latest order=";

            if (latest.has_value()) {
                std::cout << *latest;
            } else {
                std::cout << "NULL";
            }

            std::cout << "\n";
        }
    }

    /*
     * Correlated aggregate:
     *
     * A product is selected when its price is greater than the average price
     * of products in its own category.
     *
     * SQL:
     *
     * WHERE p.price > (
     *     SELECT AVG(p2.price)
     *     FROM products p2
     *     WHERE p2.category = p.category
     * )
     */
    double categoryAverage(const std::string& category) const {
        double total = 0.0;
        std::size_t count = 0;

        for (const auto& product : products) {
            if (product.category == category && product.active) {
                total += product.price;
                ++count;
            }
        }

        if (count == 0) {
            throw std::runtime_error("Category has no active products.");
        }

        return total / static_cast<double>(count);
    }

    void correlatedCategoryComparison() const {
        section("6. Correlated subquery: above category average");

        for (const auto& product : products) {
            if (!product.active) {
                continue;
            }

            const double categoryAvg = categoryAverage(product.category);

            if (product.price > categoryAvg) {
                std::cout << product.name
                          << " | category=" << product.category
                          << " | price=" << product.price
                          << " | category average=" << categoryAvg
                          << "\n";
            }
        }
    }

    /*
     * Derived-table style aggregation.
     *
     * First compute:
     *
     *     SELECT order_id, SUM(quantity * unit_price)
     *
     * Then operate on that intermediate relation.
     */
    std::vector<OrderTotal> calculateOrderTotals() const {
        std::vector<OrderTotal> totals;

        for (const auto& order : orders) {
            double total = 0.0;

            for (const auto& item : orderItems) {
                if (item.orderId == order.id) {
                    total += item.quantity * item.unitPrice;
                }
            }

            totals.push_back({order.id, total});
        }

        return totals;
    }

    void nestedSubquery() const {
        section("7. Nested subquery: customers with delivered orders above 100000");

        const auto totals = calculateOrderTotals();

        /*
         * Inner derived result:
         * identify high-value orders.
         */
        std::unordered_set<int> highValueOrderIds;

        for (const auto& total : totals) {
            if (total.value > 100000.0) {
                highValueOrderIds.insert(total.orderId);
            }
        }

        /*
         * Outer query:
         * translate those order IDs into customer IDs.
         */
        std::unordered_set<int> highValueCustomerIds;

        for (const auto& order : orders) {
            if (
                order.status == "Delivered" &&
                highValueOrderIds.contains(order.id)
            ) {
                highValueCustomerIds.insert(order.customerId);
            }
        }

        for (const auto& customer : customers) {
            if (highValueCustomerIds.contains(customer.id)) {
                std::cout << customer.name << "\n";
            }
        }
    }

    /*
     * Another derived-table example:
     *
     * Aggregate customer revenue first, then classify the intermediate
     * results. Keeping those two logical phases separate often improves
     * readability in complex SQL.
     */
    std::vector<CustomerRevenue> calculateCustomerRevenue() const {
        std::vector<CustomerRevenue> result;

        for (const auto& customer : customers) {
            double revenue = 0.0;

            auto iterator = ordersByCustomer.find(customer.id);

            if (iterator != ordersByCustomer.end()) {
                for (const Order* order : iterator->second) {
                    if (order->status == "Cancelled") {
                        continue;
                    }

                    for (const auto& item : orderItems) {
                        if (item.orderId == order->id) {
                            revenue += item.quantity * item.unitPrice;
                        }
                    }
                }
            }

            result.push_back({customer.id, customer.name, revenue});
        }

        return result;
    }

    void derivedTableClassification() const {
        section("8. Derived-table style customer revenue classification");

        auto revenueRows = calculateCustomerRevenue();

        std::sort(
            revenueRows.begin(),
            revenueRows.end(),
            [](const CustomerRevenue& left, const CustomerRevenue& right) {
                return left.revenue > right.revenue;
            }
        );

        for (const auto& row : revenueRows) {
            std::string classification;

            if (row.revenue >= 200000.0) {
                classification = "High Value";
            } else if (row.revenue >= 100000.0) {
                classification = "Medium Value";
            } else {
                classification = "Standard";
            }

            std::cout << row.customerName
                      << " | revenue=" << row.revenue
                      << " | class=" << classification
                      << "\n";
        }
    }

    /*
     * Relational division:
     *
     * Find customers who purchased every product in a required set.
     *
     * SQL pattern:
     *
     * NOT EXISTS (
     *     SELECT required_product
     *     WHERE NOT EXISTS (
     *         SELECT purchase
     *         WHERE customer bought required_product
     *     )
     * )
     *
     * The key idea is:
     * "There does not exist a required item that is missing."
     */
    bool customerBoughtProduct(int customerId, int productId) const {
        auto iterator = ordersByCustomer.find(customerId);

        if (iterator == ordersByCustomer.end()) {
            return false;
        }

        for (const Order* order : iterator->second) {
            if (order->status != "Delivered") {
                continue;
            }

            for (const auto& item : orderItems) {
                if (
                    item.orderId == order->id &&
                    item.productId == productId
                ) {
                    return true;
                }
            }
        }

        return false;
    }

    void doubleNotExists() const {
        section("9. Double NOT EXISTS: customers who bought every required product");

        const std::set<int> requiredProducts = {3, 4, 6};

        for (const auto& customer : customers) {
            bool missingRequiredProduct = false;

            /*
             * Inner logical test:
             * does a required product exist that this customer did not buy?
             */
            for (int requiredProduct : requiredProducts) {
                if (!customerBoughtProduct(customer.id, requiredProduct)) {
                    missingRequiredProduct = true;
                    break;
                }
            }

            /*
             * Outer NOT EXISTS:
             * accept the customer only when no required product is missing.
             */
            if (!missingRequiredProduct) {
                std::cout << customer.name << "\n";
            }
        }
    }

    /*
     * SQL's NOT IN can be surprising when NULL is present.
     *
     * This helper demonstrates the logical distinction:
     *
     * NOT EXISTS asks whether a matching row exists.
     *
     * NOT IN compares against every value and SQL's three-valued logic means
     * NULL can make the final predicate UNKNOWN.
     */
    void nullSemantics() const {
        section("10. NULL and NOT IN semantics");

        std::vector<std::optional<int>> values = {
            1,
            2,
            std::nullopt
        };

        std::cout << "Subquery values: ";

        for (const auto& value : values) {
            if (value.has_value()) {
                std::cout << *value << " ";
            } else {
                std::cout << "NULL ";
            }
        }

        std::cout << "\n";

        std::cout
            << "SQL consequence: 3 NOT IN (1, 2, NULL) evaluates to UNKNOWN,\n"
            << "not TRUE. For anti-existence logic, NOT EXISTS avoids this\n"
            << "specific NULL trap when the correlation predicate is correct.\n";
    }

    /*
     * Compare correlated lookup with an indexed lookup.
     *
     * A naive correlated implementation can repeatedly scan the orders
     * collection. The indexed version uses ordersByCustomer.
     *
     * This models an important production principle: query shape and indexes
     * influence performance, and assumptions should be verified with actual
     * execution plans and representative data.
     */
    void performanceComparison() const {
        section("11. Performance model: repeated scan versus indexed lookup");

        std::size_t repeatedScanComparisons = 0;

        for (const auto& customer : customers) {
            for (const auto& order : orders) {
                ++repeatedScanComparisons;

                if (
                    order.customerId == customer.id &&
                    order.status == "Delivered"
                ) {
                    break;
                }
            }
        }

        std::size_t indexedLookups = 0;

        for (const auto& customer : customers) {
            ++indexedLookups;

            auto iterator = ordersByCustomer.find(customer.id);

            if (iterator != ordersByCustomer.end()) {
                for (const Order* order : iterator->second) {
                    if (order->status == "Delivered") {
                        break;
                    }
                }
            }
        }

        std::cout
            << "Comparisons in repeated-scan model: "
            << repeatedScanComparisons << "\n";

        std::cout
            << "Customer index lookups: "
            << indexedLookups << "\n";

        std::cout
            << "Production SQL should be evaluated with execution plans,\n"
            << "realistic cardinalities, and appropriate indexes.\n";
    }

    /*
     * A correlated query is not automatically inferior.
     *
     * Optimizers can rewrite queries, use indexes, short-circuit EXISTS,
     * materialize intermediate results, or choose other execution strategies.
     * The logical SQL form and physical execution plan are distinct concepts.
     */
    void architectureConsiderations() const {
        section("12. Architecture and production considerations");

        std::cout
            << "1. Use scalar subqueries when the inner operation naturally\n"
            << "   returns one value, such as AVG(), MAX(), or COUNT().\n\n"

            << "2. Use EXISTS when only relationship existence matters.\n\n"

            << "3. Use NOT EXISTS for anti-existence requirements, especially\n"
            << "   when NULL values could make NOT IN unsafe.\n\n"

            << "4. Use correlated subqueries when the inner calculation\n"
            << "   genuinely depends on the current outer row.\n\n"

            << "5. Consider JOINs, window functions, or derived tables when\n"
            << "   they express the same requirement more clearly.\n\n"

            << "6. Index columns used by correlation predicates and selective\n"
            << "   filters when supported by the database workload.\n\n"

            << "7. Validate scalar-subquery cardinality. A conceptual scalar\n"
            << "   result should have one logical value.\n\n"

            << "8. Use parameterized SQL for application input. Never build\n"
            << "   SQL by concatenating untrusted values.\n\n"

            << "9. Use transactions for multi-step writes involving subqueries\n"
            << "   when atomicity is required.\n\n"

            << "10. Inspect execution plans before optimizing based only on\n"
            << "    intuition.\n";
    }

    void validation() const {
        section("13. Assertions and semantic validation");

        const double average = averageProductPrice();

        assert(average > 0.0);

        const auto deliveredIds = deliveredCustomerIds();

        assert(!deliveredIds.empty());

        for (const auto& customer : customers) {
            if (hasDeliveredOrder(customer.id)) {
                assert(deliveredIds.contains(customer.id));
            }
        }

        for (const auto& product : products) {
            if (productWasNeverOrdered(product.id)) {
                assert(
                    itemsByProduct.find(product.id) == itemsByProduct.end() ||
                    itemsByProduct.at(product.id).empty()
                );
            }
        }

        std::cout
            << "Average price validated: "
            << std::fixed << std::setprecision(2)
            << average << "\n";

        std::cout
            << "Delivered-customer membership validated.\n";

        std::cout
            << "NOT EXISTS product checks validated.\n";

        std::cout
            << "All assertions passed.\n";
    }

    void runCaseStudy() const {
        scalarSubquery();
        multiRowInSubquery();
        existsSubquery();
        notExistsSubquery();
        correlatedScalarSubquery();
        correlatedCategoryComparison();
        nestedSubquery();
        derivedTableClassification();
        doubleNotExists();
        nullSemantics();
        performanceComparison();
        architectureConsiderations();
        validation();
    }
};

int main() {
    try {
        std::cout
            << "SQL SUBQUERIES: C++ INDUSTRY-STYLE CASE STUDY\n"
            << "C++17 standard library implementation\n";

        SalesAnalytics analytics;
        analytics.runCaseStudy();

        std::cout << "\n" << std::string(78, '=') << "\n";
        std::cout << "Case study completed successfully.\n";
        std::cout << std::string(78, '=') << "\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }
}
