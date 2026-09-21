/*
SQL Introduction: relational database case study

This C++17 program models a small order-management system around the concepts
of relational databases, tables, rows, columns, primary keys, foreign keys,
schemas, constraints, joins, transactions, and SQL execution.

The program intentionally uses the C++ standard library only. It models the
database layer in memory because an external SQL client library would otherwise
be required for actual database connectivity.

The architecture is designed to make the database concepts visible:

    CustomerTable
    ProductTable
    OrderTable
    OrderItemTable

Relationships:

    Customer 1 ---- many Order
    Order    1 ---- many OrderItem
    Product  1 ---- many OrderItem

OrderItem therefore acts as the junction between Order and Product.

Compile with:

    g++ -std=c++17 -O2 -Wall -Wextra -pedantic sql_introduction_case_study.cpp -o sql_case_study

Run:

    ./sql_case_study

On Windows with MinGW:

    .\sql_case_study.exe
*/

#include <algorithm>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// Domain types
// -----------------------------------------------------------------------------

struct Customer {
    int customerId;
    string fullName;
    string email;
};

struct Product {
    int productId;
    string productName;
    long long pricePaise;
    int stockQuantity;
};

struct Order {
    int orderId;
    int customerId;
    string status;
};

struct OrderItem {
    int orderId;
    int productId;
    int quantity;
    long long unitPricePaise;
};


// -----------------------------------------------------------------------------
// Formatting
// -----------------------------------------------------------------------------

string money(long long paise) {
    ostringstream output;
    output << "Rs. " << (paise / 100) << "."
           << setw(2) << setfill('0') << (paise % 100);
    return output.str();
}

void printTitle(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

void printSubtitle(const string& title) {
    cout << "\n" << string(78, '-') << "\n";
    cout << title << "\n";
    cout << string(78, '-') << "\n";
}


// -----------------------------------------------------------------------------
// Exceptions
// -----------------------------------------------------------------------------

class DatabaseError : public runtime_error {
public:
    explicit DatabaseError(const string& message)
        : runtime_error(message) {}
};

class ConstraintViolation : public DatabaseError {
public:
    explicit ConstraintViolation(const string& message)
        : DatabaseError(message) {}
};

class NotFoundError : public DatabaseError {
public:
    explicit NotFoundError(const string& message)
        : DatabaseError(message) {}
};


// -----------------------------------------------------------------------------
// Relational table storage
// -----------------------------------------------------------------------------

class CustomerTable {
private:
    map<int, Customer> rowsById;
    set<string> emails;

public:
    void insert(const Customer& customer) {
        if (customer.customerId <= 0) {
            throw ConstraintViolation("customer_id must be positive.");
        }

        if (customer.fullName.empty()) {
            throw ConstraintViolation("full_name cannot be empty.");
        }

        if (customer.email.empty()) {
            throw ConstraintViolation("email cannot be empty.");
        }

        if (rowsById.contains(customer.customerId)) {
            throw ConstraintViolation("Duplicate customer primary key.");
        }

        if (emails.contains(customer.email)) {
            throw ConstraintViolation("Duplicate customer email.");
        }

        rowsById.emplace(customer.customerId, customer);
        emails.insert(customer.email);
    }

    const Customer& get(int customerId) const {
        auto iterator = rowsById.find(customerId);

        if (iterator == rowsById.end()) {
            throw NotFoundError("Customer does not exist.");
        }

        return iterator->second;
    }

    bool exists(int customerId) const {
        return rowsById.contains(customerId);
    }

    const map<int, Customer>& rows() const {
        return rowsById;
    }
};


class ProductTable {
private:
    map<int, Product> rowsById;

public:
    void insert(const Product& product) {
        if (product.productId <= 0) {
            throw ConstraintViolation("product_id must be positive.");
        }

        if (product.productName.empty()) {
            throw ConstraintViolation("product_name cannot be empty.");
        }

        if (product.pricePaise < 0) {
            throw ConstraintViolation("price cannot be negative.");
        }

        if (product.stockQuantity < 0) {
            throw ConstraintViolation("stock_quantity cannot be negative.");
        }

        if (rowsById.contains(product.productId)) {
            throw ConstraintViolation("Duplicate product primary key.");
        }

        rowsById.emplace(product.productId, product);
    }

    Product& getMutable(int productId) {
        auto iterator = rowsById.find(productId);

        if (iterator == rowsById.end()) {
            throw NotFoundError("Product does not exist.");
        }

        return iterator->second;
    }

    const Product& get(int productId) const {
        auto iterator = rowsById.find(productId);

        if (iterator == rowsById.end()) {
            throw NotFoundError("Product does not exist.");
        }

        return iterator->second;
    }

    const map<int, Product>& rows() const {
        return rowsById;
    }
};


class OrderTable {
private:
    map<int, Order> rowsById;

public:
    void insert(const Order& order, const CustomerTable& customers) {
        if (order.orderId <= 0) {
            throw ConstraintViolation("order_id must be positive.");
        }

        if (rowsById.contains(order.orderId)) {
            throw ConstraintViolation("Duplicate order primary key.");
        }

        /*
         * This is the application-level equivalent of:

             FOREIGN KEY (customer_id)
             REFERENCES customers(customer_id)

         * The referenced parent must exist.
         */
        if (!customers.exists(order.customerId)) {
            throw ConstraintViolation(
                "Foreign-key violation: customer does not exist."
            );
        }

        if (order.status.empty()) {
            throw ConstraintViolation("Order status cannot be empty.");
        }

        rowsById.emplace(order.orderId, order);
    }

    const Order& get(int orderId) const {
        auto iterator = rowsById.find(orderId);

        if (iterator == rowsById.end()) {
            throw NotFoundError("Order does not exist.");
        }

        return iterator->second;
    }

    bool exists(int orderId) const {
        return rowsById.contains(orderId);
    }

    void erase(int orderId) {
        rowsById.erase(orderId);
    }

    const map<int, Order>& rows() const {
        return rowsById;
    }
};


// -----------------------------------------------------------------------------
// Composite primary key for order_items
// -----------------------------------------------------------------------------

struct OrderItemKey {
    int orderId;
    int productId;

    bool operator<(const OrderItemKey& other) const {
        return tie(orderId, productId)
            < tie(other.orderId, other.productId);
    }
};


class OrderItemTable {
private:
    map<OrderItemKey, OrderItem> rowsByKey;

public:
    void insert(
        const OrderItem& item,
        const OrderTable& orders,
        const ProductTable& products
    ) {
        if (!orders.exists(item.orderId)) {
            throw ConstraintViolation(
                "Foreign-key violation: order does not exist."
            );
        }

        /*
         * This models:

             FOREIGN KEY (product_id)
             REFERENCES products(product_id)
         */
        products.get(item.productId);

        if (item.quantity <= 0) {
            throw ConstraintViolation("quantity must be positive.");
        }

        if (item.unitPricePaise < 0) {
            throw ConstraintViolation("unit_price cannot be negative.");
        }

        OrderItemKey key{item.orderId, item.productId};

        /*
         * Composite primary key:

             PRIMARY KEY (order_id, product_id)

         * The pair must be unique.
         */
        if (rowsByKey.contains(key)) {
            throw ConstraintViolation(
                "Duplicate order_items composite primary key."
            );
        }

        rowsByKey.emplace(key, item);
    }

    const map<OrderItemKey, OrderItem>& rows() const {
        return rowsByKey;
    }

    vector<OrderItem> findByOrder(int orderId) const {
        vector<OrderItem> result;

        for (const auto& [key, item] : rowsByKey) {
            if (key.orderId == orderId) {
                result.push_back(item);
            }
        }

        return result;
    }

    void eraseByOrder(int orderId) {
        for (auto iterator = rowsByKey.begin();
             iterator != rowsByKey.end();) {

            if (iterator->first.orderId == orderId) {
                iterator = rowsByKey.erase(iterator);
            } else {
                ++iterator;
            }
        }
    }
};


// -----------------------------------------------------------------------------
// Database schema
// -----------------------------------------------------------------------------

class Database {
public:
    CustomerTable customers;
    ProductTable products;
    OrderTable orders;
    OrderItemTable orderItems;

    /*
     * The class represents a schema containing four tables.

     * In a real relational DBMS, the database engine would store metadata
     * describing tables, columns, constraints, indexes, and relationships.
     */
};


// -----------------------------------------------------------------------------
// Seed data
// -----------------------------------------------------------------------------

void seedDatabase(Database& database) {
    database.customers.insert({
        1,
        "Asha Mehta",
        "asha@example.com"
    });

    database.customers.insert({
        2,
        "Rohan Singh",
        "rohan@example.com"
    });

    database.customers.insert({
        3,
        "Neha Kapoor",
        "neha@example.com"
    });

    database.customers.insert({
        4,
        "Vikram Rao",
        "vikram@example.com"
    });

    database.products.insert({
        1,
        "Laptop",
        7500000,
        10
    });

    database.products.insert({
        2,
        "Mechanical Keyboard",
        550000,
        25
    });

    database.products.insert({
        3,
        "Monitor",
        1800000,
        15
    });

    database.products.insert({
        4,
        "USB-C Hub",
        320000,
        40
    });

    database.products.insert({
        5,
        "Webcam",
        450000,
        20
    });
}


// -----------------------------------------------------------------------------
// Display tables
// -----------------------------------------------------------------------------

void displayCustomers(const Database& database) {
    printSubtitle("customers");

    cout << left
         << setw(14) << "customer_id"
         << setw(24) << "full_name"
         << setw(32) << "email"
         << "\n";

    for (const auto& [id, customer] : database.customers.rows()) {
        cout << left
             << setw(14) << customer.customerId
             << setw(24) << customer.fullName
             << setw(32) << customer.email
             << "\n";
    }
}

void displayProducts(const Database& database) {
    printSubtitle("products");

    cout << left
         << setw(12) << "product_id"
         << setw(26) << "product_name"
         << setw(16) << "price"
         << setw(16) << "stock"
         << "\n";

    for (const auto& [id, product] : database.products.rows()) {
        cout << left
             << setw(12) << product.productId
             << setw(26) << product.productName
             << setw(16) << money(product.pricePaise)
             << setw(16) << product.stockQuantity
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// INSERT and relationship creation
// -----------------------------------------------------------------------------

void createOrder(
    Database& database,
    int orderId,
    int customerId,
    const vector<pair<int, int>>& requestedItems
) {
    if (requestedItems.empty()) {
        throw DatabaseError("An order requires at least one product.");
    }

    /*
     * The first phase validates everything that can be checked before writes.

     * A real DBMS would normally handle the transaction around the entire
     * operation. This program uses a snapshot to provide rollback behavior.
     */
    map<int, int> consolidatedQuantities;

    for (const auto& [productId, quantity] : requestedItems) {
        if (productId <= 0 || quantity <= 0) {
            throw ConstraintViolation(
                "Product ID and quantity must be positive."
            );
        }

        consolidatedQuantities[productId] += quantity;
    }

    /*
     * Check customer foreign key.
     */
    database.customers.get(customerId);

    /*
     * Check all products and stock before changing anything.
     */
    for (const auto& [productId, quantity] : consolidatedQuantities) {
        const Product& product = database.products.get(productId);

        if (product.stockQuantity < quantity) {
            throw ConstraintViolation(
                "Insufficient stock for " + product.productName
            );
        }
    }

    /*
     * Transaction snapshot.
     *
     * A real database transaction does not normally copy the entire database
     * into application memory. The snapshot is used here to make transaction
     * semantics visible without an external SQL library.
     */
    Database backup = database;

    try {
        database.orders.insert({
            orderId,
            customerId,
            "PAID"
        }, database.customers);

        for (const auto& [productId, quantity] : consolidatedQuantities) {
            const Product& product = database.products.get(productId);

            database.orderItems.insert({
                orderId,
                productId,
                quantity,
                product.pricePaise
            }, database.orders, database.products);

            Product& mutableProduct =
                database.products.getMutable(productId);

            mutableProduct.stockQuantity -= quantity;
        }

    } catch (...) {
        /*
         * Any failure restores all changes performed by this transaction.
         */
        database = backup;
        throw;
    }
}


// -----------------------------------------------------------------------------
// Join demonstration
// -----------------------------------------------------------------------------

struct OrderReportRow {
    int orderId;
    string customerName;
    string productName;
    int quantity;
    long long unitPricePaise;
    long long lineTotalPaise;
};

vector<OrderReportRow> buildOrderReport(const Database& database) {
    vector<OrderReportRow> report;

    /*
     * This loop is the in-memory equivalent of a relational JOIN:

         orders
         JOIN customers
           ON orders.customer_id = customers.customer_id
         JOIN order_items
           ON order_items.order_id = orders.order_id
         JOIN products
           ON products.product_id = order_items.product_id

     * The map-based tables provide approximately logarithmic key lookup.
     */
    for (const auto& [orderId, order] : database.orders.rows()) {
        const Customer& customer =
            database.customers.get(order.customerId);

        vector<OrderItem> items =
            database.orderItems.findByOrder(orderId);

        for (const OrderItem& item : items) {
            const Product& product =
                database.products.get(item.productId);

            report.push_back({
                orderId,
                customer.fullName,
                product.productName,
                item.quantity,
                item.unitPricePaise,
                static_cast<long long>(item.quantity)
                    * item.unitPricePaise
            });
        }
    }

    return report;
}

void displayOrderReport(const Database& database) {
    printSubtitle("Joined order report");

    const auto report = buildOrderReport(database);

    cout << left
         << setw(12) << "order_id"
         << setw(22) << "customer"
         << setw(26) << "product"
         << setw(10) << "qty"
         << setw(16) << "unit_price"
         << setw(16) << "line_total"
         << "\n";

    for (const auto& row : report) {
        cout << left
             << setw(12) << row.orderId
             << setw(22) << row.customerName
             << setw(26) << row.productName
             << setw(10) << row.quantity
             << setw(16) << money(row.unitPricePaise)
             << setw(16) << money(row.lineTotalPaise)
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// Aggregation
// -----------------------------------------------------------------------------

struct CustomerTotal {
    int customerId;
    string customerName;
    long long totalPaise;
};

vector<CustomerTotal> calculateCustomerTotals(const Database& database) {
    map<int, long long> totals;

    for (const auto& [id, customer] : database.customers.rows()) {
        totals[id] = 0;
    }

    /*
     * This models:

         SELECT
             customer_id,
             SUM(quantity * unit_price)
         GROUP BY customer_id

     * The map key represents the GROUP BY key.
     */
    for (const auto& [orderId, order] : database.orders.rows()) {
        const auto items =
            database.orderItems.findByOrder(orderId);

        for (const auto& item : items) {
            totals[order.customerId] +=
                static_cast<long long>(item.quantity)
                * item.unitPricePaise;
        }
    }

    vector<CustomerTotal> result;

    for (const auto& [customerId, total] : totals) {
        const Customer& customer =
            database.customers.get(customerId);

        result.push_back({
            customerId,
            customer.fullName,
            total
        });
    }

    sort(
        result.begin(),
        result.end(),
        [](const CustomerTotal& left, const CustomerTotal& right) {
            return left.totalPaise > right.totalPaise;
        }
    );

    return result;
}

void displayCustomerTotals(const Database& database) {
    printSubtitle("Customer spending aggregation");

    const auto totals = calculateCustomerTotals(database);

    for (const auto& total : totals) {
        cout << setw(22) << left
             << total.customerName
             << money(total.totalPaise)
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// Constraint testing
// -----------------------------------------------------------------------------

void demonstrateConstraintFailures(Database& database) {
    printTitle("Constraint and failure cases");

    printSubtitle("Duplicate primary key");

    try {
        database.customers.insert({
            1,
            "Duplicate Customer",
            "different@example.com"
        });
    } catch (const ConstraintViolation& error) {
        cout << "Expected error: " << error.what() << "\n";
    }

    printSubtitle("Duplicate unique email");

    try {
        database.customers.insert({
            50,
            "Another Customer",
            "asha@example.com"
        });
    } catch (const ConstraintViolation& error) {
        cout << "Expected error: " << error.what() << "\n";
    }

    printSubtitle("Invalid foreign key");

    try {
        database.orders.insert({
            999,
            999999,
            "PENDING"
        }, database.customers);
    } catch (const ConstraintViolation& error) {
        cout << "Expected error: " << error.what() << "\n";
    }

    printSubtitle("Invalid quantity");

    try {
        database.orderItems.insert({
            100,
            1,
            0,
            7500000
        }, database.orders, database.products);
    } catch (const DatabaseError& error) {
        cout << "Expected error: " << error.what() << "\n";
    }
}


// -----------------------------------------------------------------------------
// Transaction demonstration
// -----------------------------------------------------------------------------

void demonstrateTransactions(Database& database) {
    printTitle("Transaction and rollback case study");

    printSubtitle("Successful transaction");

    try {
        createOrder(
            database,
            1001,
            1,
            {
                {1, 1},
                {2, 2},
                {4, 1}
            }
        );

        cout << "Order 1001 committed successfully.\n";
    } catch (const DatabaseError& error) {
        cout << "Unexpected failure: " << error.what() << "\n";
    }

    printSubtitle("Failed transaction");

    const int stockBefore =
        database.products.get(3).stockQuantity;

    try {
        createOrder(
            database,
            1002,
            2,
            {
                {3, stockBefore + 1000}
            }
        );

        cout << "Unexpected success.\n";
    } catch (const DatabaseError& error) {
        cout << "Expected failure: " << error.what() << "\n";
    }

    const int stockAfter =
        database.products.get(3).stockQuantity;

    cout << "Stock before failed transaction: "
         << stockBefore << "\n";

    cout << "Stock after failed transaction: "
         << stockAfter << "\n";

    cout << "Rollback preserved stock: "
         << boolalpha
         << (stockBefore == stockAfter)
         << "\n";
}


// -----------------------------------------------------------------------------
// Referential actions
// -----------------------------------------------------------------------------

void demonstrateCascadeDelete(Database& database) {
    printTitle("ON DELETE CASCADE concept");

    cout << R"(
The SQL schema can define:

    FOREIGN KEY (order_id)
    REFERENCES orders(order_id)
    ON DELETE CASCADE

This means order_items are dependent records of an order.

Deleting the order should therefore remove its dependent order_items.

The in-memory implementation performs the dependent deletion explicitly to
demonstrate the same relationship.
)" << "\n";

    const auto itemsBefore =
        database.orderItems.findByOrder(1001);

    cout << "Order items before deletion: "
         << itemsBefore.size() << "\n";

    database.orderItems.eraseByOrder(1001);
    database.orders.erase(1001);

    const auto itemsAfter =
        database.orderItems.findByOrder(1001);

    cout << "Order items after deletion: "
         << itemsAfter.size() << "\n";
}


// -----------------------------------------------------------------------------
// Schema explanation
// -----------------------------------------------------------------------------

void explainSchema() {
    printTitle("Relational schema represented by the case study");

    cout << R"(
CUSTOMERS
    customer_id       PRIMARY KEY
    full_name         NOT NULL
    email             NOT NULL, UNIQUE

PRODUCTS
    product_id        PRIMARY KEY
    product_name      NOT NULL
    price             NON-NEGATIVE
    stock_quantity    NON-NEGATIVE

ORDERS
    order_id          PRIMARY KEY
    customer_id       FOREIGN KEY -> customers.customer_id
    status            NOT NULL

ORDER_ITEMS
    order_id          FOREIGN KEY -> orders.order_id
    product_id        FOREIGN KEY -> products.product_id
    quantity          POSITIVE
    unit_price        NON-NEGATIVE

    PRIMARY KEY (order_id, product_id)

Relationship cardinalities:

    customers 1 ---- many orders
    orders    1 ---- many order_items
    products  1 ---- many order_items

The order_items table converts the conceptual many-to-many relationship
between orders and products into two one-to-many relationships.
)" << "\n";
}


// -----------------------------------------------------------------------------
// SQL execution model explanation
// -----------------------------------------------------------------------------

void explainSQLExecutionModel() {
    printTitle("SQL execution model");

    cout << R"(
A JavaScript, Python, C++, Java, or other application normally communicates
with a database through a database driver.

A simplified execution lifecycle is:

    Application
        |
        | SQL + parameters
        v
    Database driver
        |
        v
    Database engine
        |
        +--> Parse SQL
        |
        +--> Resolve tables and columns
        |
        +--> Validate syntax and constraints
        |
        +--> Optimize execution plan
        |
        +--> Read indexes and table data
        |
        +--> Join/filter/group/order
        |
        +--> Return result
        |
        v
    Database driver
        |
        v
    Application

The application normally specifies what result it needs. The optimizer
chooses a physical strategy for obtaining it.

For a query such as:

    SELECT product_name
    FROM products
    WHERE price >= 5000
    ORDER BY price DESC;

the logical concepts include:

    FROM
    WHERE
    SELECT
    ORDER BY

The database may use an index, a table scan, sorting, or another strategy
depending on statistics, indexes, table size, database configuration, and
the optimizer.
)" << "\n";
}


// -----------------------------------------------------------------------------
// Performance discussion
// -----------------------------------------------------------------------------

void explainPerformance() {
    printTitle("Performance considerations");

    cout << R"(
1. Primary-key lookup

The case study uses std::map for primary-key lookup. Lookup is typically
O(log n). Real database engines use specialized storage structures and
indexes.

2. Indexes

A database index can reduce the amount of data that must be examined for
selective queries.

3. Joins

Join performance depends on table size, indexes, join conditions, data
distribution, and the chosen execution plan.

4. Aggregation

GROUP BY operations can require memory, sorting, hashing, or other internal
structures.

5. Network transfer

An application should avoid retrieving unnecessary columns and rows because
data transfer between the database and application is itself a cost.

6. Transactions

Transactions provide correctness but can introduce contention. Transaction
scope should be carefully designed.

7. Premature optimization

An index or query rewrite should normally be justified by measurement and
execution-plan analysis rather than intuition alone.
)" << "\n";
}


// -----------------------------------------------------------------------------
// Security discussion
// -----------------------------------------------------------------------------

void explainSecurity() {
    printTitle("Security considerations");

    cout << R"(
SQL injection
    Use parameterized queries. Never concatenate untrusted values into SQL.

Least privilege
    Application database accounts should have only the permissions they need.

Authentication
    Database credentials must be protected and should not be hard-coded into
    source code.

Authorization
    Application users should not automatically receive database privileges.

Input validation
    Validate expected types, ranges, and formats at application boundaries.

Database constraints
    Enforce critical invariants in the database because multiple application
    processes can access the same data.

Secrets
    Credentials should be supplied through an appropriate secret-management
    mechanism or environment-specific configuration rather than committed to
    source control.

Auditing
    Sensitive systems may require database or application-level audit records.
)" << "\n";
}


// -----------------------------------------------------------------------------
// Complexity analysis
// -----------------------------------------------------------------------------

void explainComplexity() {
    printTitle("Algorithmic reasoning");

    cout << R"(
The in-memory case study is not a complete SQL engine, but its data structures
illustrate why database systems maintain indexes.

std::map lookup:
    approximately O(log n)

Sequential scan:
    O(n)

Finding every order item belonging to an order in the current implementation:
    O(m)

where m is the number of order-item rows.

A database can maintain an index on order_items(order_id), making lookup of
items for one order substantially more efficient for large datasets.

Sorting n rows:
    commonly O(n log n)

Aggregation:
    depends on the implementation. Hash aggregation can approach O(n) average
    behavior, while sort-based approaches can require O(n log n).

Actual database performance depends on the physical engine, storage layout,
statistics, indexes, memory, concurrency, and query optimizer.
)" << "\n";
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        printTitle("SQL Introduction: C++ relational database case study");

        explainSchema();

        Database database;
        seedDatabase(database);

        printTitle("Initial relational data");
        displayCustomers(database);
        displayProducts(database);

        demonstrateConstraintFailures(database);

        demonstrateTransactions(database);

        printTitle("Data after successful order");
        displayProducts(database);

        displayOrderReport(database);
        displayCustomerTotals(database);

        explainSQLExecutionModel();

        demonstrateCascadeDelete(database);

        explainPerformance();
        explainSecurity();
        explainComplexity();

        printTitle("Case study observations");

        cout << R"(
The implementation demonstrates why relational databases separate entities
into related tables instead of placing every attribute into one large row.

The primary key gives each entity an identity.

The foreign key connects dependent records to their parent records.

The composite primary key in order_items prevents duplicate product entries
within the same order.

Constraints protect important invariants.

The transaction boundary ensures that creating an order and reducing stock
are treated as one logical operation.

The join report reconstructs useful information from normalized tables.

Aggregation computes customer-level totals from multiple related rows.

A production SQL engine performs these operations using optimized storage,
indexes, query plans, concurrency mechanisms, durable transactions, and
database-specific execution strategies.
)" << "\n";

        return 0;

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }
}
