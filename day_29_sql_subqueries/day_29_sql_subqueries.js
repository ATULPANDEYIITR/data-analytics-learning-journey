/*
 * SQL Subqueries: Scalar, Correlated, Nested, EXISTS, and NOT EXISTS
 *
 * This self-contained JavaScript file demonstrates the conceptual behavior
 * of SQL subqueries without requiring an external database package.
 *
 * The implementation uses JavaScript arrays and functions to model relational
 * operations. The examples deliberately mirror practical SQL patterns:
 *
 * - scalar subqueries
 * - multi-row subqueries
 * - IN / NOT IN
 * - EXISTS / NOT EXISTS
 * - correlated subqueries
 * - nested queries
 * - derived-table style transformations
 * - aggregation
 * - NULL and three-valued-logic considerations
 * - anti-join patterns
 * - performance comparisons
 *
 * Run with:
 *     node sql_subqueries.js
 */

"use strict";

const customers = [
    { customerId: 1, customerName: "Aarav Retail", city: "Lucknow", segment: "Retail" },
    { customerId: 2, customerName: "Bharat Foods", city: "Delhi", segment: "Business" },
    { customerId: 3, customerName: "Crescent Labs", city: "Bengaluru", segment: "Enterprise" },
    { customerId: 4, customerName: "Delta Stores", city: "Mumbai", segment: "Retail" },
    { customerId: 5, customerName: "Evergreen Systems", city: "Pune", segment: "Enterprise" },
    { customerId: 6, customerName: "Future Office", city: "Hyderabad", segment: "Business" },
    { customerId: 7, customerName: "Galaxy Traders", city: "Jaipur", segment: "Business" },
    { customerId: 8, customerName: "Horizon Retail", city: "Kolkata", segment: "Retail" }
];

const products = [
    { productId: 1, productName: "Laptop Pro", category: "Computers", price: 90000, active: true },
    { productId: 2, productName: "Office Laptop", category: "Computers", price: 60000, active: true },
    { productId: 3, productName: "Mechanical Keyboard", category: "Accessories", price: 7000, active: true },
    { productId: 4, productName: "Wireless Mouse", category: "Accessories", price: 2500, active: true },
    { productId: 5, productName: "4K Monitor", category: "Displays", price: 30000, active: true },
    { productId: 6, productName: "USB-C Dock", category: "Accessories", price: 12000, active: true },
    { productId: 7, productName: "Server Rack", category: "Infrastructure", price: 50000, active: true },
    { productId: 8, productName: "Network Switch", category: "Infrastructure", price: 18000, active: true },
    { productId: 9, productName: "Legacy Monitor", category: "Displays", price: 10000, active: false }
];

const orders = [
    { orderId: 101, customerId: 1, orderDate: "2026-01-05", status: "Delivered" },
    { orderId: 102, customerId: 1, orderDate: "2026-02-10", status: "Delivered" },
    { orderId: 103, customerId: 2, orderDate: "2026-01-15", status: "Shipped" },
    { orderId: 104, customerId: 2, orderDate: "2026-03-01", status: "Delivered" },
    { orderId: 105, customerId: 3, orderDate: "2026-01-20", status: "Delivered" },
    { orderId: 106, customerId: 3, orderDate: "2026-02-21", status: "Delivered" },
    { orderId: 107, customerId: 4, orderDate: "2026-02-05", status: "Cancelled" },
    { orderId: 108, customerId: 4, orderDate: "2026-03-11", status: "Delivered" },
    { orderId: 109, customerId: 5, orderDate: "2026-01-25", status: "Delivered" },
    { orderId: 110, customerId: 5, orderDate: "2026-03-14", status: "Delivered" },
    { orderId: 111, customerId: 6, orderDate: "2026-02-18", status: "Pending" },
    { orderId: 112, customerId: 7, orderDate: "2026-03-15", status: "Delivered" }
];

const orderItems = [
    { orderId: 101, productId: 1, quantity: 1, unitPrice: 90000 },
    { orderId: 101, productId: 3, quantity: 2, unitPrice: 7000 },
    { orderId: 102, productId: 5, quantity: 2, unitPrice: 30000 },
    { orderId: 102, productId: 4, quantity: 2, unitPrice: 2500 },
    { orderId: 103, productId: 2, quantity: 3, unitPrice: 60000 },
    { orderId: 103, productId: 4, quantity: 3, unitPrice: 2500 },
    { orderId: 104, productId: 7, quantity: 1, unitPrice: 50000 },
    { orderId: 104, productId: 8, quantity: 2, unitPrice: 18000 },
    { orderId: 105, productId: 1, quantity: 2, unitPrice: 90000 },
    { orderId: 105, productId: 6, quantity: 2, unitPrice: 12000 },
    { orderId: 106, productId: 5, quantity: 3, unitPrice: 30000 },
    { orderId: 106, productId: 3, quantity: 5, unitPrice: 7000 },
    { orderId: 107, productId: 9, quantity: 2, unitPrice: 10000 },
    { orderId: 108, productId: 2, quantity: 2, unitPrice: 60000 },
    { orderId: 108, productId: 4, quantity: 4, unitPrice: 2500 },
    { orderId: 109, productId: 7, quantity: 2, unitPrice: 50000 },
    { orderId: 109, productId: 8, quantity: 2, unitPrice: 18000 },
    { orderId: 110, productId: 1, quantity: 1, unitPrice: 90000 },
    { orderId: 110, productId: 6, quantity: 1, unitPrice: 12000 },
    { orderId: 111, productId: 3, quantity: 3, unitPrice: 7000 },
    { orderId: 112, productId: 8, quantity: 5, unitPrice: 18000 }
];

function printSection(title) {
    console.log(`\n${"=".repeat(78)}\n${title}\n${"=".repeat(78)}`);
}

function printRows(rows) {
    if (rows.length === 0) {
        console.log("(no rows)");
        return;
    }

    console.table(rows);
}

function average(values) {
    if (values.length === 0) {
        return null;
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sum(values) {
    return values.reduce((total, value) => total + value, 0);
}

function scalarSubquery(queryFunction, description) {
    /*
     * A scalar subquery must conceptually represent one value.
     * This helper enforces that contract instead of silently accepting
     * an arbitrary number of values.
     */
    const results = queryFunction();

    if (results.length !== 1) {
        throw new Error(
            `${description}: expected exactly one row, received ${results.length}`
        );
    }

    return results[0];
}

function sqlLikeIn(value, values) {
    /*
     * Models the basic IN relationship:
     * outer_value IN (values returned by subquery)
     */
    return values.includes(value);
}

function sqlLikeExists(queryFunction) {
    /*
     * EXISTS is a Boolean existence test. Only the presence of at least
     * one matching row matters; the contents of that row are irrelevant.
     */
    return queryFunction().length > 0;
}

function sqlLikeNotExists(queryFunction) {
    return !sqlLikeExists(queryFunction);
}

function groupBy(rows, keyFunction) {
    const groups = new Map();

    for (const row of rows) {
        const key = keyFunction(row);

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(row);
    }

    return groups;
}

function orderTotal(orderId) {
    const items = orderItems.filter(item => item.orderId === orderId);

    return sum(items.map(item => item.quantity * item.unitPrice));
}

function scalarSubqueryExamples() {
    printSection("1. Scalar subqueries");

    const averageProductPrice = scalarSubquery(
        () => [{ value: average(products.map(product => product.price)) }],
        "Average product price"
    ).value;

    console.log("Scalar average price:", averageProductPrice);

    const aboveAverageProducts = products
        .filter(product => product.price > averageProductPrice)
        .map(product => ({
            productName: product.productName,
            price: product.price,
            averagePrice: Number(averageProductPrice.toFixed(2))
        }));

    printRows(aboveAverageProducts);

    /*
     * MAX() is another common scalar-subquery pattern.
     */
    const maximumPrice = scalarSubquery(
        () => [{ value: Math.max(...products.map(product => product.price)) }],
        "Maximum product price"
    ).value;

    console.log("\nMost expensive products:");
    printRows(
        products
            .filter(product => product.price === maximumPrice)
            .map(product => ({
                productName: product.productName,
                price: product.price
            }))
    );
}

function multiRowSubqueryExamples() {
    printSection("2. Multi-row subqueries and IN");

    const deliveredCustomerIds = orders
        .filter(order => order.status === "Delivered")
        .map(order => order.customerId);

    /*
     * Equivalent SQL idea:
     *
     * WHERE customer_id IN (
     *     SELECT customer_id
     *     FROM orders
     *     WHERE status = 'Delivered'
     * )
     */
    const customersWithDeliveredOrders = customers
        .filter(customer => sqlLikeIn(customer.customerId, deliveredCustomerIds))
        .map(customer => ({
            customerId: customer.customerId,
            customerName: customer.customerName,
            segment: customer.segment
        }));

    printRows(customersWithDeliveredOrders);

    const deliveredOrderIds = orders
        .filter(order => order.status === "Delivered")
        .map(order => order.orderId);

    const deliveredProductIds = orderItems
        .filter(item => sqlLikeIn(item.orderId, deliveredOrderIds))
        .map(item => item.productId);

    console.log("\nProducts appearing in delivered orders:");
    printRows(
        products
            .filter(product => sqlLikeIn(product.productId, deliveredProductIds))
            .map(product => ({
                productId: product.productId,
                productName: product.productName,
                category: product.category
            }))
    );
}

function existsExamples() {
    printSection("3. EXISTS and NOT EXISTS");

    const customersWithDeliveredOrders = customers
        .filter(customer =>
            sqlLikeExists(() =>
                orders.filter(
                    order =>
                        order.customerId === customer.customerId &&
                        order.status === "Delivered"
                )
            )
        )
        .map(customer => ({
            customerId: customer.customerId,
            customerName: customer.customerName
        }));

    console.log("Customers with at least one delivered order:");
    printRows(customersWithDeliveredOrders);

    const productsNeverOrdered = products
        .filter(product =>
            sqlLikeNotExists(() =>
                orderItems.filter(item => item.productId === product.productId)
            )
        )
        .map(product => ({
            productId: product.productId,
            productName: product.productName
        }));

    console.log("\nProducts with no order-item relationship:");
    printRows(productsNeverOrdered);

    const customersWithoutCancelledOrders = customers
        .filter(customer =>
            sqlLikeNotExists(() =>
                orders.filter(
                    order =>
                        order.customerId === customer.customerId &&
                        order.status === "Cancelled"
                )
            )
        )
        .map(customer => customer.customerName);

    console.log("\nCustomers without cancelled orders:");
    console.log(customersWithoutCancelledOrders);
}

function correlatedSubqueryExamples() {
    printSection("4. Correlated subqueries");

    /*
     * A correlated subquery refers to the current outer row.
     *
     * SQL shape:
     *
     * SELECT c.customer_name,
     *        (SELECT MAX(o.order_date)
     *         FROM orders o
     *         WHERE o.customer_id = c.customer_id)
     * FROM customers c;
     *
     * The JavaScript implementation explicitly performs the lookup for
     * every customer, making the correlation easy to see.
     */
    const customerLatestOrders = customers.map(customer => {
        const customerOrders = orders.filter(
            order => order.customerId === customer.customerId
        );

        const latestOrderDate =
            customerOrders.length === 0
                ? null
                : customerOrders
                    .map(order => order.orderDate)
                    .sort()
                    .at(-1);

        return {
            customerId: customer.customerId,
            customerName: customer.customerName,
            latestOrderDate
        };
    });

    printRows(customerLatestOrders);

    /*
     * Correlated aggregate:
     *
     * Find products priced above the average price of their own category.
     */
    const productsAboveCategoryAverage = products
        .filter(product => product.active)
        .filter(product => {
            const sameCategoryPrices = products
                .filter(
                    other =>
                        other.category === product.category &&
                        other.active
                )
                .map(other => other.price);

            const categoryAverage = average(sameCategoryPrices);

            return product.price > categoryAverage;
        })
        .map(product => ({
            productName: product.productName,
            category: product.category,
            price: product.price
        }));

    console.log("\nProducts above their own category average:");
    printRows(productsAboveCategoryAverage);
}

function nestedSubqueryExample() {
    printSection("5. Nested subqueries");

    /*
     * First level:
     * calculate order totals.
     *
     * Second level:
     * identify orders whose totals exceed a threshold.
     *
     * Outer level:
     * identify the customers owning those orders.
     */
    const highValueOrderIds = orders
        .filter(order => order.status === "Delivered")
        .filter(order => orderTotal(order.orderId) > 100000)
        .map(order => order.orderId);

    const highValueCustomerIds = orders
        .filter(order => sqlLikeIn(order.orderId, highValueOrderIds))
        .map(order => order.customerId);

    const highValueCustomers = customers
        .filter(customer => sqlLikeIn(customer.customerId, highValueCustomerIds))
        .map(customer => ({
            customerId: customer.customerId,
            customerName: customer.customerName
        }));

    printRows(highValueCustomers);
}

function derivedTableExample() {
    printSection("6. Derived-table style processing");

    /*
     * SQL derived-table concept:
     *
     * FROM (
     *     SELECT customer_id, SUM(...) AS revenue
     *     FROM ...
     *     GROUP BY customer_id
     * ) AS customer_revenue
     *
     * JavaScript's map/filter pipeline naturally models the intermediate
     * relation produced by that subquery.
     */
    const customerRevenue = customers.map(customer => {
        const relevantOrders = orders.filter(
            order =>
                order.customerId === customer.customerId &&
                order.status !== "Cancelled"
        );

        const revenue = sum(
            relevantOrders.map(order => orderTotal(order.orderId))
        );

        return {
            customerId: customer.customerId,
            customerName: customer.customerName,
            revenue
        };
    });

    const classifiedCustomers = customerRevenue
        .map(customer => ({
            ...customer,
            customerClass:
                customer.revenue >= 200000
                    ? "High Value"
                    : customer.revenue >= 100000
                        ? "Medium Value"
                        : "Standard"
        }))
        .sort((a, b) => b.revenue - a.revenue);

    printRows(classifiedCustomers);
}

function relationalDivisionExample() {
    printSection("7. Double NOT EXISTS: relational division");

    const requiredProductIds = new Set([3, 4, 6]);

    /*
     * SQL conceptual form:
     *
     * WHERE NOT EXISTS (
     *     SELECT required_product
     *     WHERE NOT EXISTS (
     *         SELECT purchase
     *         WHERE customer bought required_product
     *     )
     * )
     *
     * The outer NOT EXISTS says:
     * "There does not exist a required product that is missing."
     */
    const customersWhoBoughtEverything = customers
        .filter(customer => {
            return [...requiredProductIds].every(requiredProductId => {
                return sqlLikeExists(() =>
                    orders
                        .filter(
                            order =>
                                order.customerId === customer.customerId &&
                                order.status === "Delivered"
                        )
                        .flatMap(order =>
                            orderItems.filter(
                                item =>
                                    item.orderId === order.orderId &&
                                    item.productId === requiredProductId
                            )
                        )
                );
            });
        })
        .map(customer => customer.customerName);

    console.log("Required products:", [...requiredProductIds]);
    console.log("Customers who bought every required product:");
    console.log(customersWhoBoughtEverything);
}

function nullSemanticsExample() {
    printSection("8. NULL and NOT IN");

    const nullableValues = [1, 2, null];
    const candidateValues = [1, 2, 3];

    /*
     * JavaScript's Array.includes() is not a complete model of SQL's NULL
     * semantics. SQL uses three-valued logic:
     *
     * TRUE, FALSE, UNKNOWN.
     *
     * For example:
     *
     * 3 NOT IN (1, 2, NULL)
     *
     * is UNKNOWN in SQL, not TRUE.
     *
     * This is why NOT EXISTS is generally preferred when an anti-existence
     * condition may involve NULL values.
     */
    console.log("Nullable subquery values:", nullableValues);

    const notExistsEquivalent = candidateValues.filter(candidate =>
        sqlLikeNotExists(() =>
            nullableValues.filter(
                value => value !== null && value === candidate
            )
        )
    );

    console.log(
        "NOT EXISTS-style result, ignoring NULL as a matching value:",
        notExistsEquivalent
    );

    console.log(
        "SQL rule: NOT IN becomes UNKNOWN when the tested value is not "
        + "matched and the subquery contains NULL."
    );
}

function windowFunctionComparison() {
    printSection("9. Correlated subquery versus window-style computation");

    /*
     * Correlated approach:
     * compare each product against the maximum price in its category.
     */
    const correlatedResult = products.filter(product => {
        const categoryMaximum = Math.max(
            ...products
                .filter(other => other.category === product.category)
                .map(other => other.price)
        );

        return product.price === categoryMaximum;
    });

    console.log("Correlated-style result:");
    printRows(
        correlatedResult.map(product => ({
            productName: product.productName,
            category: product.category,
            price: product.price
        }))
    );

    /*
     * A window-function SQL solution would calculate:
     *
     * RANK() OVER (
     *     PARTITION BY category
     *     ORDER BY price DESC
     * )
     *
     * JavaScript does not need a window-function API here, so we explicitly
     * group and sort to show the same conceptual operation.
     */
    const groupedProducts = groupBy(products, product => product.category);
    const windowStyleResult = [];

    for (const [category, categoryProducts] of groupedProducts) {
        const sorted = [...categoryProducts].sort((a, b) => b.price - a.price);
        const highestPrice = sorted[0].price;

        for (const product of sorted) {
            if (product.price === highestPrice) {
                windowStyleResult.push({
                    productName: product.productName,
                    category,
                    price: product.price
                });
            }
        }
    }

    console.log("\nWindow-style conceptual result:");
    printRows(windowStyleResult);
}

function performanceComparison() {
    printSection("10. Performance considerations");

    /*
     * The first implementation intentionally performs a correlated scan:
     * for every customer, scan the orders.
     *
     * This resembles the logical structure of a correlated SQL subquery.
     */
    let correlatedComparisons = 0;

    for (const customer of customers) {
        for (const order of orders) {
            correlatedComparisons += 1;

            if (
                order.customerId === customer.customerId &&
                order.status === "Delivered"
            ) {
                break;
            }
        }
    }

    /*
     * An indexed database can avoid scanning the complete orders relation for
     * every customer. A JavaScript Map models the same high-level optimization.
     */
    const ordersByCustomer = new Map();

    for (const order of orders) {
        if (!ordersByCustomer.has(order.customerId)) {
            ordersByCustomer.set(order.customerId, []);
        }

        ordersByCustomer.get(order.customerId).push(order);
    }

    let indexedLookups = 0;

    for (const customer of customers) {
        indexedLookups += 1;

        const customerOrders = ordersByCustomer.get(customer.customerId) ?? [];
        customerOrders.some(order => order.status === "Delivered");
    }

    console.log("Correlated scan comparisons:", correlatedComparisons);
    console.log("Indexed-style customer lookups:", indexedLookups);

    console.log(
        "\nSQL implication: indexes on correlation columns such as "
        + "orders.customer_id can materially affect execution cost."
    );
}

function validation() {
    printSection("11. Validation");

    const averagePrice = average(products.map(product => product.price));

    if (!(averagePrice > 0)) {
        throw new Error("Average product price should be positive.");
    }

    const deliveredCustomers = customers.filter(customer =>
        sqlLikeExists(() =>
            orders.filter(
                order =>
                    order.customerId === customer.customerId &&
                    order.status === "Delivered"
            )
        )
    );

    if (deliveredCustomers.length === 0) {
        throw new Error("At least one customer should have a delivered order.");
    }

    const neverOrderedProducts = products.filter(product =>
        sqlLikeNotExists(() =>
            orderItems.filter(item => item.productId === product.productId)
        )
    );

    if (neverOrderedProducts.some(product => product.productId < 1)) {
        throw new Error("Invalid product identifier detected.");
    }

    console.log("Average price:", averagePrice.toFixed(2));
    console.log("Delivered customers:", deliveredCustomers.length);
    console.log("Never-ordered products:", neverOrderedProducts.length);
    console.log("All validation checks passed.");
}

function main() {
    console.log("SQL SUBQUERIES: JAVASCRIPT STUDY IMPLEMENTATION");

    try {
        scalarSubqueryExamples();
        multiRowSubqueryExamples();
        existsExamples();
        correlatedSubqueryExamples();
        nestedSubqueryExample();
        derivedTableExample();
        relationalDivisionExample();
        nullSemanticsExample();
        windowFunctionComparison();
        performanceComparison();
        validation();

        printSection("Completed");
        console.log(
            "The examples model scalar, multi-row, correlated, nested, "
            + "EXISTS, and NOT EXISTS subquery patterns."
        );
    } catch (error) {
        console.error("Execution failed:", error.message);
        process.exitCode = 1;
    }
}

main();
