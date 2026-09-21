/*
SQL Introduction: Databases, Relational Databases, Tables, Rows, Columns,
Primary Keys, Foreign Keys, Schemas, and the SQL Execution Model

This JavaScript file complements the Python study implementation.

The examples use JavaScript as the application layer and describe the SQL
operations that a JavaScript application would normally send to a database.
The file intentionally uses only built-in JavaScript features so that it can
run in Node.js without an npm dependency.

Run:
    node sql_introduction.js

The file demonstrates:
    - relational data modeling
    - SQL statement construction
    - parameterized-query concepts
    - JavaScript data mapping
    - asynchronous database-style application flow
    - transaction structure
    - joins and aggregation
    - validation
    - error handling
    - query execution planning concepts
    - a realistic order-processing service
*/

// -----------------------------------------------------------------------------
// Formatting utilities
// -----------------------------------------------------------------------------

function printTitle(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function printSubtitle(title) {
    console.log("\n" + "-".repeat(78));
    console.log(title);
    console.log("-".repeat(78));
}

function printObject(object) {
    console.log(JSON.stringify(object, null, 2));
}


// -----------------------------------------------------------------------------
// Relational concepts represented in JavaScript
// -----------------------------------------------------------------------------

function demonstrateRelationalRepresentation() {
    printTitle("1. Representing relational concepts in JavaScript");

    /*
     * JavaScript objects can represent individual rows returned from SQL.
     * The database remains responsible for persistent storage and constraints.
     */
    const customerRow = {
        customer_id: 1,
        full_name: "Asha Mehta",
        email: "asha@example.com"
    };

    const productRow = {
        product_id: 1,
        product_name: "Laptop",
        price: 75000,
        stock_quantity: 10
    };

    printObject(customerRow);
    printObject(productRow);

    /*
     * A JavaScript array can represent a collection of rows.
     * It is not a replacement for a relational database because arrays do not
     * provide database-level transactions, constraints, indexing, durability,
     * concurrency control, or SQL query processing.
     */
    const customers = [
        customerRow,
        {
            customer_id: 2,
            full_name: "Rohan Singh",
            email: "rohan@example.com"
        },
        {
            customer_id: 3,
            full_name: "Neha Kapoor",
            email: "neha@example.com"
        }
    ];

    console.log("Number of customer rows:", customers.length);
}


// -----------------------------------------------------------------------------
// Schema represented as metadata
// -----------------------------------------------------------------------------

function createSchemaDefinition() {
    /*
     * This is an application-level description of a relational schema.
     * The actual database schema would normally be created with CREATE TABLE.
     */
    return {
        customers: {
            columns: {
                customer_id: "INTEGER PRIMARY KEY",
                full_name: "TEXT NOT NULL",
                email: "TEXT NOT NULL UNIQUE"
            }
        },

        products: {
            columns: {
                product_id: "INTEGER PRIMARY KEY",
                product_name: "TEXT NOT NULL",
                price: "NUMERIC CHECK(price >= 0)",
                stock_quantity: "INTEGER CHECK(stock_quantity >= 0)"
            }
        },

        orders: {
            columns: {
                order_id: "INTEGER PRIMARY KEY",
                customer_id: "INTEGER REFERENCES customers(customer_id)",
                status: "TEXT NOT NULL"
            }
        },

        order_items: {
            columns: {
                order_id: "INTEGER REFERENCES orders(order_id)",
                product_id: "INTEGER REFERENCES products(product_id)",
                quantity: "INTEGER CHECK(quantity > 0)",
                unit_price: "NUMERIC CHECK(unit_price >= 0)"
            },
            primaryKey: ["order_id", "product_id"]
        }
    };
}

function demonstrateSchema() {
    printTitle("2. Relational schema");

    const schema = createSchemaDefinition();

    for (const [tableName, definition] of Object.entries(schema)) {
        console.log(`\nTable: ${tableName}`);

        for (const [columnName, type] of Object.entries(definition.columns)) {
            console.log(`  ${columnName}: ${type}`);
        }

        if (definition.primaryKey) {
            console.log(
                `  Primary key: (${definition.primaryKey.join(", ")})`
            );
        }
    }

    console.log(
        "\nA schema defines the structure and rules under which database data is stored."
    );
}


// -----------------------------------------------------------------------------
// SQL statement catalog
// -----------------------------------------------------------------------------

function demonstrateSQLStatements() {
    printTitle("3. SQL statements from a JavaScript application");

    const statements = {
        createTable: `
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        `,

        insert: `
            INSERT INTO customers (customer_id, full_name, email)
            VALUES (?, ?, ?)
        `,

        select: `
            SELECT customer_id, full_name, email
            FROM customers
            WHERE customer_id = ?
        `,

        update: `
            UPDATE customers
            SET email = ?
            WHERE customer_id = ?
        `,

        delete: `
            DELETE FROM customers
            WHERE customer_id = ?
        `
    };

    for (const [name, sql] of Object.entries(statements)) {
        console.log(`\n${name.toUpperCase()}:\n${sql.trim()}`);
    }

    console.log(
        "\nThe ? markers represent parameter placeholders in many database drivers."
    );
}


// -----------------------------------------------------------------------------
// Parameterized query demonstration
// -----------------------------------------------------------------------------

function buildParameterizedQuery(email) {
    /*
     * A safe application sends the SQL structure separately from the value.
     * The driver performs the correct parameter binding.
     */
    return {
        sql: `
            SELECT customer_id, full_name, email
            FROM customers
            WHERE email = ?
        `.trim(),
        parameters: [email]
    };
}

function demonstrateParameterizedQueries() {
    printTitle("4. Parameterized queries and SQL injection");

    const ordinaryInput = "asha@example.com";
    const maliciousLookingInput = "' OR 1=1 --";

    const ordinaryQuery = buildParameterizedQuery(ordinaryInput);
    const safeQuery = buildParameterizedQuery(maliciousLookingInput);

    console.log("Ordinary query:");
    printObject(ordinaryQuery);

    console.log("\nMalicious-looking input treated as a value:");
    printObject(safeQuery);

    /*
     * The critical security principle is that the SQL text does not change
     * when the user changes the parameter value.
     *
     * Do not write:
     *
     * const sql = "SELECT ... WHERE email = '" + email + "'";
     *
     * Instead, use the parameter API supplied by the database driver.
     */
}


// -----------------------------------------------------------------------------
// JavaScript validation
// -----------------------------------------------------------------------------

function validateProductInput(product) {
    if (!Number.isInteger(product.product_id) || product.product_id <= 0) {
        throw new Error("product_id must be a positive integer.");
    }

    if (
        typeof product.product_name !== "string" ||
        product.product_name.trim().length === 0
    ) {
        throw new Error("product_name must contain text.");
    }

    if (
        typeof product.price !== "number" ||
        !Number.isFinite(product.price) ||
        product.price < 0
    ) {
        throw new Error("price must be a finite non-negative number.");
    }

    if (
        !Number.isInteger(product.stock_quantity) ||
        product.stock_quantity < 0
    ) {
        throw new Error("stock_quantity must be a non-negative integer.");
    }

    return true;
}

function demonstrateValidation() {
    printTitle("5. Application-level validation");

    const validProduct = {
        product_id: 20,
        product_name: "Desk Microphone",
        price: 8500,
        stock_quantity: 8
    };

    console.log("Valid product:", validateProductInput(validProduct));

    const invalidProduct = {
        product_id: 21,
        product_name: "",
        price: -5,
        stock_quantity: -1
    };

    try {
        validateProductInput(invalidProduct);
    } catch (error) {
        console.log("Validation rejected the product:", error.message);
    }

    /*
     * JavaScript validation improves user-facing error messages.
     * It does not replace database constraints. Two application processes can
     * still attempt to write conflicting values, so the database must enforce
     * important invariants.
     */
}


// -----------------------------------------------------------------------------
// Filtering and sorting without pretending arrays are SQL
// -----------------------------------------------------------------------------

function demonstrateArrayOperationsAsSQLAnalogies() {
    printTitle("6. JavaScript data processing versus SQL processing");

    const products = [
        { product_id: 1, product_name: "Laptop", price: 75000 },
        { product_id: 2, product_name: "Keyboard", price: 5500 },
        { product_id: 3, product_name: "Monitor", price: 18000 },
        { product_id: 4, product_name: "USB-C Hub", price: 3200 }
    ];

    /*
     * filter resembles a simple WHERE operation conceptually.
     * The database should normally perform filtering before sending a large
     * result set to JavaScript.
     */
    const expensiveProducts = products.filter(product => product.price >= 10000);

    /*
     * map resembles a projection/transformation conceptually.
     */
    const productNames = expensiveProducts.map(product => product.product_name);

    /*
     * sort modifies the array. A SQL ORDER BY occurs inside the database query.
     */
    const sortedProducts = [...products].sort(
        (left, right) => right.price - left.price
    );

    console.log("Products >= 10000:");
    printObject(expensiveProducts);

    console.log("\nNames:");
    printObject(productNames);

    console.log("\nSorted products:");
    printObject(sortedProducts);

    console.log(
        "\nFor large datasets, filtering in SQL is usually preferable to retrieving every row first."
    );
}


// -----------------------------------------------------------------------------
// Relationships and joins in application terms
// -----------------------------------------------------------------------------

function demonstrateRelationships() {
    printTitle("7. Relationships and joins");

    const customers = [
        { customer_id: 1, full_name: "Asha Mehta" },
        { customer_id: 2, full_name: "Rohan Singh" }
    ];

    const orders = [
        { order_id: 1001, customer_id: 1, status: "PAID" },
        { order_id: 1002, customer_id: 2, status: "PENDING" }
    ];

    /*
     * This nested lookup illustrates the meaning of:
     *
     * JOIN orders ON orders.customer_id = customers.customer_id
     *
     * A real SQL database can use indexes and optimized join algorithms
     * rather than repeatedly scanning JavaScript arrays.
     */
    const customerById = new Map(
        customers.map(customer => [customer.customer_id, customer])
    );

    const joinedRows = orders.map(order => ({
        order_id: order.order_id,
        customer_name: customerById.get(order.customer_id)?.full_name ?? null,
        status: order.status
    }));

    printObject(joinedRows);
}


// -----------------------------------------------------------------------------
// Aggregation
// -----------------------------------------------------------------------------

function calculateCustomerTotals(customers, orders, orderItems) {
    const totals = new Map();

    for (const customer of customers) {
        totals.set(customer.customer_id, {
            customer_id: customer.customer_id,
            full_name: customer.full_name,
            total_spending: 0
        });
    }

    const orderToCustomer = new Map(
        orders.map(order => [order.order_id, order.customer_id])
    );

    for (const item of orderItems) {
        const customerId = orderToCustomer.get(item.order_id);

        if (customerId === undefined) {
            continue;
        }

        const result = totals.get(customerId);

        if (result) {
            result.total_spending += item.quantity * item.unit_price;
        }
    }

    return [...totals.values()];
}

function demonstrateAggregation() {
    printTitle("8. Aggregation");

    const customers = [
        { customer_id: 1, full_name: "Asha Mehta" },
        { customer_id: 2, full_name: "Rohan Singh" }
    ];

    const orders = [
        { order_id: 1001, customer_id: 1 },
        { order_id: 1002, customer_id: 2 }
    ];

    const orderItems = [
        { order_id: 1001, product_id: 1, quantity: 1, unit_price: 75000 },
        { order_id: 1001, product_id: 2, quantity: 2, unit_price: 5500 },
        { order_id: 1002, product_id: 3, quantity: 1, unit_price: 18000 }
    ];

    const totals = calculateCustomerTotals(
        customers,
        orders,
        orderItems
    );

    printObject(totals);

    console.log(
        "\nEquivalent SQL concepts include SUM, GROUP BY, and joins."
    );
}


// -----------------------------------------------------------------------------
// SQL execution model
// -----------------------------------------------------------------------------

function explainExecutionModel() {
    printTitle("9. SQL execution model");

    const query = `
        SELECT
            c.full_name,
            SUM(oi.quantity * oi.unit_price) AS total_spending
        FROM customers AS c
        JOIN orders AS o
            ON o.customer_id = c.customer_id
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        WHERE o.status = ?
        GROUP BY c.customer_id, c.full_name
        HAVING SUM(oi.quantity * oi.unit_price) > ?
        ORDER BY total_spending DESC
    `.trim();

    console.log(query);

    console.log(`
Conceptual stages:

1. JavaScript sends SQL and bound parameters to a database driver.
2. The driver communicates with the database.
3. The database parses SQL.
4. Names and types are checked against database metadata.
5. The optimizer chooses an execution strategy.
6. Tables and indexes are accessed.
7. Rows are joined, filtered, grouped, and transformed as required.
8. The database returns the result to the driver.
9. The driver converts database values into JavaScript-accessible values.

The logical SELECT processing model is commonly expressed as:
FROM/JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT

Physical execution can differ because the optimizer may reorder operations when
the resulting behavior remains correct.
`);
}


// -----------------------------------------------------------------------------
// Transactions
// -----------------------------------------------------------------------------

async function simulateTransaction(transactionSteps) {
    /*
     * A real database driver would expose BEGIN, COMMIT, and ROLLBACK methods.
     * This small simulation demonstrates the application control flow.
     */
    const completedSteps = [];

    try {
        console.log("BEGIN");

        for (const step of transactionSteps) {
            console.log(`Executing: ${step}`);
            completedSteps.push(step);
        }

        console.log("COMMIT");
        return {
            committed: true,
            completedSteps
        };
    } catch (error) {
        console.log("ROLLBACK");
        return {
            committed: false,
            completedSteps,
            error: error.message
        };
    }
}

async function demonstrateTransactions() {
    printTitle("10. Transactions in asynchronous JavaScript applications");

    const successfulTransaction = await simulateTransaction([
        "INSERT customer",
        "INSERT order",
        "INSERT order item",
        "UPDATE product stock"
    ]);

    printObject(successfulTransaction);

    /*
     * The next transaction intentionally fails. A real database would restore
     * all changes made since BEGIN if ROLLBACK is executed successfully.
     */
    const failedTransaction = await simulateTransaction([
        "INSERT customer",
        "INSERT order",
        "ERROR: invalid foreign key"
    ]);

    printObject(failedTransaction);

    console.log(
        "\nA transaction is particularly important when several writes must succeed or fail together."
    );
}


// -----------------------------------------------------------------------------
// Race-condition example
// -----------------------------------------------------------------------------

function demonstrateStockRaceCondition() {
    printTitle("11. Why application logic alone cannot guarantee stock correctness");

    const product = {
        product_id: 1,
        stock_quantity: 1
    };

    console.log("Initial stock:", product.stock_quantity);

    /*
     * Imagine two requests reading stock_quantity = 1 at nearly the same time.
     *
     * Request A: reads 1
     * Request B: reads 1
     * Request A: decides it can sell one unit
     * Request B: decides it can also sell one unit
     *
     * If both later write stock_quantity = 0, the application may have sold
     * two units while recording only one unit of stock reduction.
     *
     * Real systems use transactions, suitable isolation, row locking,
     * optimistic concurrency controls, atomic UPDATE conditions, or other
     * database-specific mechanisms to prevent this class of problem.
     */

    const requestARead = product.stock_quantity;
    const requestBRead = product.stock_quantity;

    if (requestARead > 0) {
        console.log("Request A believes stock is available.");
    }

    if (requestBRead > 0) {
        console.log("Request B believes stock is available.");
    }

    product.stock_quantity = 0;

    console.log(
        "Final simulated stock:",
        product.stock_quantity,
        "(the example illustrates why concurrency control is required)"
    );
}


// -----------------------------------------------------------------------------
// Realistic application service
// -----------------------------------------------------------------------------

class OrderService {
    constructor(database) {
        this.database = database;
    }

    validateOrderRequest(orderRequest) {
        if (!Number.isInteger(orderRequest.orderId) || orderRequest.orderId <= 0) {
            throw new Error("orderId must be a positive integer.");
        }

        if (
            !Number.isInteger(orderRequest.customerId) ||
            orderRequest.customerId <= 0
        ) {
            throw new Error("customerId must be a positive integer.");
        }

        if (
            !Array.isArray(orderRequest.items) ||
            orderRequest.items.length === 0
        ) {
            throw new Error("At least one order item is required.");
        }

        for (const item of orderRequest.items) {
            if (!Number.isInteger(item.productId) || item.productId <= 0) {
                throw new Error("Every productId must be positive.");
            }

            if (!Number.isInteger(item.quantity) || item.quantity <= 0) {
                throw new Error("Every quantity must be positive.");
            }
        }
    }

    /*
     * The SQL shown here is deliberately parameterized.
     *
     * In a production implementation, each statement would be executed
     * through the selected database driver's API inside one transaction.
     */
    buildOrderTransaction(orderRequest) {
        this.validateOrderRequest(orderRequest);

        const statements = [];

        statements.push({
            sql: `
                SELECT customer_id
                FROM customers
                WHERE customer_id = ?
            `.trim(),
            parameters: [orderRequest.customerId]
        });

        statements.push({
            sql: `
                INSERT INTO orders (order_id, customer_id, status)
                VALUES (?, ?, ?)
            `.trim(),
            parameters: [
                orderRequest.orderId,
                orderRequest.customerId,
                "PAID"
            ]
        });

        for (const item of orderRequest.items) {
            /*
             * The real implementation should obtain the authoritative current
             * product price from the database rather than trusting a client.
             */
            statements.push({
                sql: `
                    SELECT product_id, price, stock_quantity
                    FROM products
                    WHERE product_id = ?
                `.trim(),
                parameters: [item.productId]
            });
        }

        return statements;
    }
}

function demonstrateOrderService() {
    printTitle("12. Industry-style JavaScript database service");

    const service = new OrderService({ name: "relational-database" });

    const orderRequest = {
        orderId: 3001,
        customerId: 2,
        items: [
            { productId: 2, quantity: 1 },
            { productId: 4, quantity: 2 }
        ]
    };

    const transactionPlan = service.buildOrderTransaction(orderRequest);

    transactionPlan.forEach((statement, index) => {
        console.log(`\nStatement ${index + 1}:`);
        console.log(statement.sql);
        console.log("Parameters:", statement.parameters);
    });

    console.log(
        "\nThe service separates validation and SQL construction from the database driver's execution."
    );
}


// -----------------------------------------------------------------------------
// Indexing concepts
// -----------------------------------------------------------------------------

function demonstrateIndexConcepts() {
    printTitle("13. Indexes and performance");

    console.log(`
Suppose an application frequently executes:

    SELECT order_id, status
    FROM orders
    WHERE customer_id = ?

An index such as:

    CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

may allow the database to locate matching rows more efficiently.

Without a suitable index, a database may need to inspect many rows.

An index is not automatically beneficial for every query. It consumes storage
and adds write-maintenance work. The optimizer and database statistics also
influence whether an index is selected.

Performance should be measured using realistic data and execution plans.
`);
}


// -----------------------------------------------------------------------------
// NULL and JavaScript undefined/null distinction
// -----------------------------------------------------------------------------

function demonstrateNullSemantics() {
    printTitle("14. SQL NULL versus JavaScript null and undefined");

    const row = {
        customer_id: 1,
        middle_name: null
    };

    console.log("Database-style missing value:", row.middle_name);
    console.log("JavaScript undefined:", undefined);

    console.log(`
SQL NULL represents an absent or unknown value and participates in SQL's
three-valued logic.

JavaScript has both null and undefined, but these are language-level concepts
and should not automatically be treated as interchangeable with SQL NULL.

Database drivers define how database NULL values are mapped into JavaScript.
Applications should follow the chosen driver's documented behavior.
`);
}


// -----------------------------------------------------------------------------
// Common mistakes
// -----------------------------------------------------------------------------

function demonstrateCommonMistakes() {
    printTitle("15. Common database mistakes in JavaScript applications");

    const mistakes = [
        "Building SQL by concatenating user input.",
        "Assuming JavaScript validation replaces database constraints.",
        "Fetching thousands of rows and filtering them in JavaScript when SQL can filter them.",
        "Executing related writes without a transaction.",
        "Trusting a price supplied by an untrusted client.",
        "Assuming every SQL database uses exactly the same syntax.",
        "Ignoring database errors and continuing as if a write succeeded.",
        "Creating indexes without examining real query patterns.",
        "Assuming JavaScript array order is equivalent to SQL ORDER BY.",
        "Assuming an object or array provides database-level durability and concurrency control."
    ];

    mistakes.forEach((mistake, index) => {
        console.log(`${index + 1}. ${mistake}`);
    });
}


// -----------------------------------------------------------------------------
// Complete study run
// -----------------------------------------------------------------------------

async function main() {
    printTitle("SQL Introduction: JavaScript study implementation");

    demonstrateRelationalRepresentation();
    demonstrateSchema();
    demonstrateSQLStatements();
    demonstrateParameterizedQueries();
    demonstrateValidation();
    demonstrateArrayOperationsAsSQLAnalogies();
    demonstrateRelationships();
    demonstrateAggregation();
    explainExecutionModel();
    await demonstrateTransactions();
    demonstrateStockRaceCondition();
    demonstrateOrderService();
    demonstrateIndexConcepts();
    demonstrateNullSemantics();
    demonstrateCommonMistakes();

    printTitle("16. Final distinctions");

    console.log(`
Database
    Persistent system that stores and manages data.

Relational database
    Database organized around relations/tables and their relationships.

Table
    Structured collection of rows described by columns.

Row
    One record in a table.

Column
    An attribute with a defined meaning and database-level rules.

Primary key
    Constraint used to uniquely identify rows.

Foreign key
    Constraint that represents a relationship to a referenced table.

Schema
    Structural definition of database objects and their rules.

SQL
    Declarative language used to define, query, and modify relational data.

Database engine
    Component that parses SQL, validates it, plans execution, accesses data,
    applies constraints, manages transactions, and returns results.

JavaScript application
    Client/application layer that can send SQL through a database driver,
    process results, validate input, and coordinate application behavior.
`);
}

main().catch(error => {
    console.error("Application failed:", error);
    process.exitCode = 1;
});
