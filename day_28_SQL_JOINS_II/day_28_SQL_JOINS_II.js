/*
 * SQL Joins II
 * ============
 *
 * Topics:
 *   - Self joins
 *   - Cross joins
 *   - Multiple joins
 *   - Join cardinality
 *   - Duplicate explosion
 *   - Many-to-many relationships
 *   - Semi-joins and anti-joins
 *   - Pre-aggregation
 *   - Join algorithms
 *   - Cardinality diagnostics
 *
 * Runtime:
 *   Node.js 18+ recommended.
 *
 * This file implements relational operations in plain JavaScript so the
 * examples can execute without an external database.
 */

"use strict";

// ============================================================================
// 1. BASIC UTILITIES
// ============================================================================

function printTitle(title) {
    console.log("\n" + "=".repeat(88));
    console.log(title);
    console.log("=".repeat(88));
}

function printRows(rows, limit = 20) {
    if (rows.length === 0) {
        console.log("(no rows)");
        return;
    }

    const shown = rows.slice(0, limit);
    const columns = [];

    for (const row of shown) {
        for (const key of Object.keys(row)) {
            if (!columns.includes(key)) {
                columns.push(key);
            }
        }
    }

    const widths = {};
    for (const column of columns) {
        widths[column] = Math.max(
            column.length,
            ...shown.map(row => String(row[column] ?? "").length)
        );
    }

    console.log(
        columns.map(column => column.padEnd(widths[column])).join(" | ")
    );

    console.log(
        columns.map(column => "-".repeat(widths[column])).join("-+-")
    );

    for (const row of shown) {
        console.log(
            columns
                .map(column => String(row[column] ?? "").padEnd(widths[column]))
                .join(" | ")
        );
    }

    if (rows.length > limit) {
        console.log(`... ${rows.length - limit} more row(s)`);
    }
}

function combineRows(left, right, leftPrefix = "left", rightPrefix = "right") {
    const result = {};

    for (const [key, value] of Object.entries(left)) {
        if (Object.prototype.hasOwnProperty.call(right, key)) {
            result[`${leftPrefix}.${key}`] = value;
        } else {
            result[key] = value;
        }
    }

    for (const [key, value] of Object.entries(right)) {
        if (Object.prototype.hasOwnProperty.call(left, key)) {
            result[`${rightPrefix}.${key}`] = value;
        } else {
            result[key] = value;
        }
    }

    return result;
}

function getColumns(rows) {
    const columns = [];

    for (const row of rows) {
        for (const key of Object.keys(row)) {
            if (!columns.includes(key)) {
                columns.push(key);
            }
        }
    }

    return columns;
}

function countBy(rows, key) {
    const counts = new Map();

    for (const row of rows) {
        const value = row[key];
        counts.set(value, (counts.get(value) || 0) + 1);
    }

    return counts;
}

function duplicateGroups(rows, key) {
    const counts = countBy(rows, key);
    return [...counts.entries()]
        .filter(([, count]) => count > 1)
        .map(([value, count]) => ({ value, count }));
}

// ============================================================================
// 2. SAMPLE TABLES
// ============================================================================

const employees = [
    { employee_id: 1, employee_name: "Asha", manager_id: 4, department_id: 10 },
    { employee_id: 2, employee_name: "Bharat", manager_id: 4, department_id: 10 },
    { employee_id: 3, employee_name: "Chitra", manager_id: 5, department_id: 20 },
    { employee_id: 4, employee_name: "Dev", manager_id: 6, department_id: 10 },
    { employee_id: 5, employee_name: "Esha", manager_id: 6, department_id: 20 },
    { employee_id: 6, employee_name: "Farhan", manager_id: null, department_id: 30 },
    { employee_id: 7, employee_name: "Gita", manager_id: 4, department_id: 10 }
];

const departments = [
    { department_id: 10, department_name: "Engineering" },
    { department_id: 20, department_name: "Research" },
    { department_id: 30, department_name: "Security" }
];

const projects = [
    { project_id: 101, project_name: "Atlas", department_id: 10 },
    { project_id: 102, project_name: "Beacon", department_id: 10 },
    { project_id: 103, project_name: "Cipher", department_id: 20 },
    { project_id: 104, project_name: "Dragon", department_id: 30 }
];

const employeeProjects = [
    { employee_id: 1, project_id: 101 },
    { employee_id: 1, project_id: 102 },
    { employee_id: 2, project_id: 101 },
    { employee_id: 3, project_id: 103 },
    { employee_id: 4, project_id: 101 },
    { employee_id: 4, project_id: 102 },
    { employee_id: 4, project_id: 104 },
    { employee_id: 5, project_id: 103 },
    { employee_id: 6, project_id: 104 },
    { employee_id: 7, project_id: 102 }
];

const orders = [
    { order_id: 1001, customer_id: 1, order_total: 500 },
    { order_id: 1002, customer_id: 1, order_total: 300 },
    { order_id: 1003, customer_id: 2, order_total: 900 },
    { order_id: 1004, customer_id: 3, order_total: 200 }
];

const orderItems = [
    { order_item_id: 1, order_id: 1001, product: "Keyboard", quantity: 2 },
    { order_item_id: 2, order_id: 1001, product: "Mouse", quantity: 1 },
    { order_item_id: 3, order_id: 1002, product: "Monitor", quantity: 2 },
    { order_item_id: 4, order_id: 1003, product: "Laptop", quantity: 1 },
    { order_item_id: 5, order_id: 1003, product: "Mouse", quantity: 4 },
    { order_item_id: 6, order_id: 1004, product: "Keyboard", quantity: 1 }
];

const payments = [
    { payment_id: 1, order_id: 1001, payment_method: "Card", amount: 500 },
    { payment_id: 2, order_id: 1002, payment_method: "Card", amount: 300 },
    { payment_id: 3, order_id: 1003, payment_method: "UPI", amount: 500 },
    { payment_id: 4, order_id: 1003, payment_method: "Card", amount: 400 },
    { payment_id: 5, order_id: 1004, payment_method: "UPI", amount: 200 }
];

const customers = [
    { customer_id: 1, customer_name: "Acme" },
    { customer_id: 2, customer_name: "Globex" },
    { customer_id: 3, customer_name: "Initech" }
];

// ============================================================================
// 3. INNER JOIN
// ============================================================================

function innerJoin(left, right, leftKey, rightKey) {
    /*
     * A hash index turns repeated searches into direct lookups.
     *
     * If a key occurs m times in left and n times in right, that key produces
     * m * n result rows. The hash index changes lookup cost, not the logical
     * cardinality of the result.
     */
    const index = new Map();

    for (const rightRow of right) {
        const key = rightRow[rightKey];

        // SQL equality joins do not match NULL with NULL.
        if (key === null || key === undefined) {
            continue;
        }

        if (!index.has(key)) {
            index.set(key, []);
        }

        index.get(key).push(rightRow);
    }

    const result = [];

    for (const leftRow of left) {
        const key = leftRow[leftKey];

        if (key === null || key === undefined) {
            continue;
        }

        for (const rightRow of index.get(key) || []) {
            result.push(combineRows(leftRow, rightRow));
        }
    }

    return result;
}

// ============================================================================
// 4. LEFT JOIN
// ============================================================================

function leftJoin(left, right, leftKey, rightKey) {
    const index = new Map();
    const rightColumns = getColumns(right);

    for (const rightRow of right) {
        const key = rightRow[rightKey];

        if (key === null || key === undefined) {
            continue;
        }

        if (!index.has(key)) {
            index.set(key, []);
        }

        index.get(key).push(rightRow);
    }

    const result = [];

    for (const leftRow of left) {
        const key = leftRow[leftKey];
        const matches =
            key === null || key === undefined
                ? []
                : index.get(key) || [];

        if (matches.length === 0) {
            const nullRight = Object.fromEntries(
                rightColumns.map(column => [column, null])
            );

            result.push(combineRows(leftRow, nullRight));
        } else {
            for (const rightRow of matches) {
                result.push(combineRows(leftRow, rightRow));
            }
        }
    }

    return result;
}

// ============================================================================
// 5. CROSS JOIN
// ============================================================================

function crossJoin(left, right) {
    /*
     * CROSS JOIN deliberately creates the Cartesian product.
     *
     * Output size:
     *     left.length * right.length
     */
    const result = [];

    for (const leftRow of left) {
        for (const rightRow of right) {
            result.push(combineRows(leftRow, rightRow));
        }
    }

    return result;
}

// ============================================================================
// 6. SELF JOIN
// ============================================================================

function selfJoin(table, leftKey, rightKey) {
    /*
     * The same physical array is used twice.
     *
     * The two logical roles are:
     *     employee
     *     manager
     *
     * This corresponds to:
     *
     *     employees AS e
     *     JOIN employees AS m
     */
    const index = new Map();

    for (const row of table) {
        const key = row[rightKey];

        if (key === null || key === undefined) {
            continue;
        }

        if (!index.has(key)) {
            index.set(key, []);
        }

        index.get(key).push(row);
    }

    const result = [];

    for (const employee of table) {
        const managerId = employee[leftKey];

        if (managerId === null || managerId === undefined) {
            continue;
        }

        for (const manager of index.get(managerId) || []) {
            result.push(
                combineRows(
                    employee,
                    manager,
                    "employee",
                    "manager"
                )
            );
        }
    }

    return result;
}

// ============================================================================
// 7. BASIC JOIN
// ============================================================================

printTitle("1. INNER JOIN");

const employeeDepartment = innerJoin(
    employees,
    departments,
    "department_id",
    "department_id"
);

printRows(employeeDepartment);

console.log(
    "\nEach employee matches the department having the same department_id."
);

// ============================================================================
// 8. SELF JOIN
// ============================================================================

printTitle("2. SELF JOIN: EMPLOYEE TO MANAGER");

const employeeManager = selfJoin(
    employees,
    "manager_id",
    "employee_id"
);

for (const row of employeeManager) {
    console.log(
        `${row["employee.employee_name"]} -> ${row["manager.employee_name"]}`
    );
}

console.log(
    "\nAliases provide different logical roles for the same table."
);

// ============================================================================
// 9. SELF JOIN PAIRS
// ============================================================================

printTitle("3. SELF JOIN: EMPLOYEE PAIRS");

const sameDepartmentPairs = [];

for (let i = 0; i < employees.length; i++) {
    for (let j = i + 1; j < employees.length; j++) {
        const first = employees[i];
        const second = employees[j];

        if (first.department_id === second.department_id) {
            sameDepartmentPairs.push({
                employee_a: first.employee_name,
                employee_b: second.employee_name,
                department_id: first.department_id
            });
        }
    }
}

printRows(sameDepartmentPairs);

console.log(
    "\nUsing i + 1 is equivalent to enforcing a strict ordering such as "
    "e1.employee_id < e2.employee_id."
);

// ============================================================================
// 10. CROSS JOIN
// ============================================================================

printTitle("4. CROSS JOIN");

const regions = [
    { region: "North" },
    { region: "South" }
];

const quarters = [
    { quarter: "Q1" },
    { quarter: "Q2" },
    { quarter: "Q3" },
    { quarter: "Q4" }
];

const planningGrid = crossJoin(regions, quarters);

printRows(planningGrid);

console.log(
    `\n${regions.length} regions × ${quarters.length} quarters = ` +
    `${planningGrid.length} combinations`
);

// ============================================================================
// 11. JOIN CARDINALITY
// ============================================================================

printTitle("5. JOIN CARDINALITY");

function estimateJoinCardinality(left, right, leftKey, rightKey) {
    const leftCounts = countBy(left, leftKey);
    const rightCounts = countBy(right, rightKey);

    let result = 0;

    for (const [key, leftCount] of leftCounts.entries()) {
        if (key === null || key === undefined) {
            continue;
        }

        result += leftCount * (rightCounts.get(key) || 0);
    }

    return result;
}

console.log(
    "Employee-department output:",
    estimateJoinCardinality(
        employees,
        departments,
        "department_id",
        "department_id"
    )
);

console.log(
    "3 left duplicates × 4 right duplicates:",
    estimateJoinCardinality(
        [
            { key: "A" },
            { key: "A" },
            { key: "A" }
        ],
        [
            { key: "A" },
            { key: "A" },
            { key: "A" },
            { key: "A" }
        ],
        "key",
        "key"
    )
);

// ============================================================================
// 12. DUPLICATE EXPLOSION
// ============================================================================

printTitle("6. DUPLICATE EXPLOSION");

const oneOrder = [
    { order_id: 9001, customer_id: 99 }
];

const threeItems = [
    { order_id: 9001, item: "A" },
    { order_id: 9001, item: "B" },
    { order_id: 9001, item: "C" }
];

const fourPayments = [
    { order_id: 9001, payment: "P1" },
    { order_id: 9001, payment: "P2" },
    { order_id: 9001, payment: "P3" },
    { order_id: 9001, payment: "P4" }
];

const orderItems = innerJoin(
    oneOrder,
    threeItems,
    "order_id",
    "order_id"
);

const exploded = innerJoin(
    orderItems,
    fourPayments,
    "order_id",
    "order_id"
);

console.log("Order × items:", orderItems.length);
console.log("Order × items × payments:", exploded.length);

printRows(exploded);

console.log(
    "\nThe 3 item rows and 4 payment rows are independent children of the "
    + "same order, so they produce 3 × 4 = 12 combinations."
);

// ============================================================================
// 13. WRONG AGGREGATION
// ============================================================================

printTitle("7. WRONG AGGREGATION AFTER EXPLOSION");

const order1003Items = orderItems.filter(row => row.order_id === 1003);
const order1003Payments = payments.filter(row => row.order_id === 1003);

const actualQuantity = order1003Items.reduce(
    (sum, row) => sum + row.quantity,
    0
);

const actualPayment = order1003Payments.reduce(
    (sum, row) => sum + row.amount,
    0
);

const naiveCombinations = [];

for (const item of order1003Items) {
    for (const payment of order1003Payments) {
        naiveCombinations.push({
            order_id: 1003,
            quantity: item.quantity,
            payment_amount: payment.amount
        });
    }
}

const naiveQuantity = naiveCombinations.reduce(
    (sum, row) => sum + row.quantity,
    0
);

const naivePayment = naiveCombinations.reduce(
    (sum, row) => sum + row.payment_amount,
    0
);

console.log("Actual quantity:", actualQuantity);
console.log("Naive quantity:", naiveQuantity);
console.log("Actual payment:", actualPayment);
console.log("Naive payment:", naivePayment);

console.log(
    "\nThe incorrect totals result from repeated facts, not from SUM itself."
);

// ============================================================================
// 14. PRE-AGGREGATION
// ============================================================================

printTitle("8. PRE-AGGREGATION");

function groupSum(rows, groupKey, valueKey, outputKey) {
    const totals = new Map();

    for (const row of rows) {
        const key = row[groupKey];
        const value = Number(row[valueKey]) || 0;

        totals.set(key, (totals.get(key) || 0) + value);
    }

    return [...totals.entries()].map(([key, total]) => ({
        [groupKey]: key,
        [outputKey]: total
    }));
}

function groupCount(rows, groupKey, outputKey) {
    const counts = countBy(rows, groupKey);

    return [...counts.entries()].map(([key, count]) => ({
        [groupKey]: key,
        [outputKey]: count
    }));
}

const itemTotalsByOrder = groupSum(
    orderItems,
    "order_id",
    "quantity",
    "total_quantity"
);

const paymentTotalsByOrder = groupSum(
    payments,
    "order_id",
    "amount",
    "total_paid"
);

const safeOrderMetrics = innerJoin(
    itemTotalsByOrder,
    paymentTotalsByOrder,
    "order_id",
    "order_id"
);

printRows(safeOrderMetrics);

console.log(
    "\nEach aggregate now has one row per order before the aggregates are joined."
);

// ============================================================================
// 15. MULTIPLE JOINS
// ============================================================================

printTitle("9. MULTIPLE JOINS");

const employeeProjectLinks = innerJoin(
    employees,
    employeeProjects,
    "employee_id",
    "employee_id"
);

const employeeProjectDetails = innerJoin(
    employeeProjectLinks,
    projects,
    "project_id",
    "project_id"
);

printRows(employeeProjectDetails);

console.log(
    "\nThe intermediate result must be understood before the next join is added."
);

// ============================================================================
// 16. MANY-TO-MANY
// ============================================================================

printTitle("10. MANY-TO-MANY RELATIONSHIP");

console.log(
    "employees -> employeeProjects -> projects"
);

console.log(
    "The bridge table stores one row per employee-project relationship."
);

const employeeProjectPairs = employeeProjects.map(row => ({
    employee_id: row.employee_id,
    project_id: row.project_id
}));

printRows(employeeProjectPairs);

// ============================================================================
// 17. SEMI-JOIN
// ============================================================================

printTitle("11. SEMI-JOIN: EXISTS-LIKE BEHAVIOR");

const projectEmployeeIds = new Set(
    employeeProjects.map(row => row.employee_id)
);

const employeesWithProjects = employees.filter(
    employee => projectEmployeeIds.has(employee.employee_id)
);

printRows(employeesWithProjects);

console.log(
    "\nA semi-join answers whether a match exists without returning every match."
);

// ============================================================================
// 18. ANTI-JOIN
// ============================================================================

printTitle("12. ANTI-JOIN: NOT EXISTS-LIKE BEHAVIOR");

const employeesWithoutProjects = employees.filter(
    employee => !projectEmployeeIds.has(employee.employee_id)
);

printRows(employeesWithoutProjects);

console.log(
    "\nAn anti-join returns left-side rows for which no matching right-side "
    + "relationship exists."
);

// ============================================================================
// 19. LEFT JOIN
// ============================================================================

printTitle("13. LEFT JOIN");

const allEmployees = leftJoin(
    employees,
    departments,
    "department_id",
    "department_id"
);

printRows(allEmployees);

console.log(
    "\nLEFT JOIN preserves the left-side row even when the right side is absent."
);

// ============================================================================
// 20. NULL BEHAVIOR
// ============================================================================

printTitle("14. NULL JOIN BEHAVIOR");

const nullLeft = [
    { id: 1, key: null },
    { id: 2, key: "A" }
];

const nullRight = [
    { id: 10, key: null },
    { id: 11, key: "A" }
];

const nullResult = innerJoin(
    nullLeft,
    nullRight,
    "key",
    "key"
);

printRows(nullResult);

console.log(
    "\nOrdinary SQL equality does not make NULL = NULL true."
);

// ============================================================================
// 21. CARDINALITY PROFILING
// ============================================================================

printTitle("15. CARDINALITY PROFILING");

function profileKey(rows, key) {
    const counts = countBy(rows, key);

    const nonNullEntries = [...counts.entries()]
        .filter(([value]) => value !== null && value !== undefined);

    return {
        rows: rows.length,
        distinctNonNullValues: nonNullEntries.length,
        nullCount: counts.get(null) || 0,
        duplicateGroups: nonNullEntries
            .filter(([, count]) => count > 1)
            .map(([value, count]) => ({ value, count })),
        maximumFrequency: Math.max(
            0,
            ...[...counts.values()]
        )
    };
}

console.log(
    "employees.department_id:",
    profileKey(employees, "department_id")
);

console.log(
    "orders.customer_id:",
    profileKey(orders, "customer_id")
);

console.log(
    "orderItems.order_id:",
    profileKey(orderItems, "order_id")
);

console.log(
    "payments.order_id:",
    profileKey(payments, "order_id")
);

// ============================================================================
// 22. MULTIPLICITY CHECK
// ============================================================================

printTitle("16. MULTIPLICITY CHECK");

const firstJoin = innerJoin(
    orders,
    orderItems,
    "order_id",
    "order_id"
);

const secondJoin = innerJoin(
    firstJoin,
    payments,
    "order_id",
    "order_id"
);

console.log("orders:", orders.length);
console.log("orders × items:", firstJoin.length);
console.log("orders × items × payments:", secondJoin.length);

console.log(
    "\nCounts should be inspected after every significant join."
);

// ============================================================================
// 23. DISTINCT IS NOT A FIX FOR WRONG GRAIN
// ============================================================================

printTitle("17. DISTINCT IS NOT A UNIVERSAL FIX");

console.log(
    "If an item and a payment represent independent facts, their combinations "
    + "are distinct facts at the exploded grain."
);

console.log(
    "Removing duplicates blindly can discard legitimate rows and cannot "
    + "reconstruct the intended aggregate."
);

// ============================================================================
// 24. NON-EQUI JOIN
// ============================================================================

printTitle("18. NON-EQUI JOIN");

const salaryBands = [
    { band: "Junior", minimum: 0, maximum: 50000 },
    { band: "Mid", minimum: 50001, maximum: 100000 },
    { band: "Senior", minimum: 100001, maximum: 200000 }
];

const employeeSalaries = [
    { employee_id: 1, employee_name: "Asha", salary: 72000 },
    { employee_id: 2, employee_name: "Bharat", salary: 45000 },
    { employee_id: 3, employee_name: "Chitra", salary: 130000 }
];

const salaryMatches = [];

for (const employee of employeeSalaries) {
    for (const band of salaryBands) {
        if (
            employee.salary >= band.minimum &&
            employee.salary <= band.maximum
        ) {
            salaryMatches.push({
                employee: employee.employee_name,
                salary: employee.salary,
                band: band.band
            });
        }
    }
}

printRows(salaryMatches);

console.log(
    "\nRange joins require the same cardinality analysis as equality joins."
);

// ============================================================================
// 25. OVERLAPPING RANGE WARNING
// ============================================================================

printTitle("19. OVERLAPPING RANGE CARDINALITY");

const overlappingRanges = [
    { label: "A", minimum: 0, maximum: 100 },
    { label: "B", minimum: 50, maximum: 150 }
];

const valueRows = [
    { value_id: 1, value: 75 }
];

const rangeMatches = [];

for (const valueRow of valueRows) {
    for (const range of overlappingRanges) {
        if (
            valueRow.value >= range.minimum &&
            valueRow.value <= range.maximum
        ) {
            rangeMatches.push({
                value_id: valueRow.value_id,
                value: valueRow.value,
                range: range.label
            });
        }
    }
}

printRows(rangeMatches);

console.log(
    "\nOne value can match multiple ranges when ranges overlap."
);

// ============================================================================
// 26. NESTED LOOP JOIN
// ============================================================================

printTitle("20. NESTED-LOOP JOIN");

function nestedLoopJoin(left, right, leftKey, rightKey) {
    const result = [];

    for (const leftRow of left) {
        for (const rightRow of right) {
            const leftValue = leftRow[leftKey];
            const rightValue = rightRow[rightKey];

            if (
                leftValue !== null &&
                leftValue !== undefined &&
                leftValue === rightValue
            ) {
                result.push(combineRows(leftRow, rightRow));
            }
        }
    }

    return result;
}

const benchmarkLeft = Array.from(
    { length: 1000 },
    (_, index) => ({ key: index, value: index * 10 })
);

const benchmarkRight = Array.from(
    { length: 1000 },
    (_, index) => ({ key: index, value: index * 20 })
);

let start = process.hrtime.bigint();

const nestedResult = nestedLoopJoin(
    benchmarkLeft,
    benchmarkRight,
    "key",
    "key"
);

let elapsedNested = Number(process.hrtime.bigint() - start) / 1e6;

console.log("Nested-loop result rows:", nestedResult.length);
console.log(`Nested-loop time: ${elapsedNested.toFixed(3)} ms`);

// ============================================================================
// 27. HASH JOIN BENCHMARK
// ============================================================================

printTitle("21. HASH JOIN");

start = process.hrtime.bigint();

const hashResult = innerJoin(
    benchmarkLeft,
    benchmarkRight,
    "key",
    "key"
);

const elapsedHash = Number(process.hrtime.bigint() - start) / 1e6;

console.log("Hash-join result rows:", hashResult.length);
console.log(`Hash-join time: ${elapsedHash.toFixed(3)} ms`);

console.log(
    "\nThe exact timing depends on hardware and runtime conditions. "
    + "The algorithmic distinction is more important than this microbenchmark."
);

// ============================================================================
// 28. OUTPUT CARDINALITY STILL MATTERS
// ============================================================================

printTitle("22. LARGE MATCHING GROUP");

const largeLeft = Array.from(
    { length: 100 },
    (_, index) => ({ key: "HOT", left: index })
);

const largeRight = Array.from(
    { length: 100 },
    (_, index) => ({ key: "HOT", right: index })
);

const largeOutput = innerJoin(
    largeLeft,
    largeRight,
    "key",
    "key"
);

console.log(
    "Expected output:",
    largeLeft.length * largeRight.length
);

console.log(
    "Actual output:",
    largeOutput.length
);

// ============================================================================
// 29. DATA SKEW
// ============================================================================

printTitle("23. DATA SKEW");

const skewedLeft = [
    ...Array.from({ length: 1000 }, (_, i) => ({
        key: "HOT",
        value: i
    })),
    { key: "COLD", value: 1 }
];

const skewedRight = [
    ...Array.from({ length: 2000 }, (_, i) => ({
        key: "HOT",
        value: i
    })),
    { key: "COLD", value: 2 }
];

console.log(
    "HOT contribution:",
    1000 * 2000
);

console.log(
    "COLD contribution:",
    1
);

console.log(
    "Total:",
    estimateJoinCardinality(
        skewedLeft,
        skewedRight,
        "key",
        "key"
    )
);

console.log(
    "\nA highly duplicated key can dominate the result even when the total "
    + "number of distinct keys is small."
);

// ============================================================================
// 30. MANY-TO-MANY DUPLICATE LINK DETECTION
// ============================================================================

printTitle("24. BRIDGE TABLE DUPLICATE DETECTION");

const duplicateLinks = [
    ...employeeProjects,
    { employee_id: 1, project_id: 101 }
];

const pairCounter = new Map();

for (const row of duplicateLinks) {
    const pair = `${row.employee_id}:${row.project_id}`;
    pairCounter.set(pair, (pairCounter.get(pair) || 0) + 1);
}

console.log(
    [...pairCounter.entries()]
        .filter(([, count]) => count > 1)
        .map(([pair, count]) => ({ pair, count }))
);

console.log(
    "\nA composite uniqueness constraint can prevent duplicate bridge records."
);

// ============================================================================
// 31. REFERENTIAL INTEGRITY
// ============================================================================

printTitle("25. REFERENTIAL INTEGRITY");

const employeeIds = new Set(
    employees.map(employee => employee.employee_id)
);

const projectIds = new Set(
    projects.map(project => project.project_id)
);

const invalidEmployeeLinks = employeeProjects.filter(
    link => !employeeIds.has(link.employee_id)
);

const invalidProjectLinks = employeeProjects.filter(
    link => !projectIds.has(link.project_id)
);

console.log("Invalid employee links:", invalidEmployeeLinks);
console.log("Invalid project links:", invalidProjectLinks);

// ============================================================================
// 32. SAFE ORDER ANALYTICS
// ============================================================================

printTitle("26. SAFE ORDER ANALYTICS");

function buildOrderAnalytics(ordersTable, itemsTable, paymentsTable) {
    const itemCount = new Map();
    const quantitySum = new Map();

    for (const item of itemsTable) {
        const id = item.order_id;

        itemCount.set(id, (itemCount.get(id) || 0) + 1);
        quantitySum.set(
            id,
            (quantitySum.get(id) || 0) + item.quantity
        );
    }

    const paymentCount = new Map();
    const paymentSum = new Map();

    for (const payment of paymentsTable) {
        const id = payment.order_id;

        paymentCount.set(
            id,
            (paymentCount.get(id) || 0) + 1
        );

        paymentSum.set(
            id,
            (paymentSum.get(id) || 0) + payment.amount
        );
    }

    return ordersTable.map(order => ({
        order_id: order.order_id,
        item_count: itemCount.get(order.order_id) || 0,
        total_quantity: quantitySum.get(order.order_id) || 0,
        payment_count: paymentCount.get(order.order_id) || 0,
        total_paid: paymentSum.get(order.order_id) || 0
    }));
}

const analytics = buildOrderAnalytics(
    orders,
    orderItems,
    payments
);

printRows(analytics);

// ============================================================================
// 33. CUSTOMER REPORT
// ============================================================================

printTitle("27. CUSTOMER REPORT");

const customerOrderCount = new Map();
const customerOrderValue = new Map();

for (const order of orders) {
    const customerId = order.customer_id;

    customerOrderCount.set(
        customerId,
        (customerOrderCount.get(customerId) || 0) + 1
    );

    customerOrderValue.set(
        customerId,
        (customerOrderValue.get(customerId) || 0) + order.order_total
    );
}

const customerReport = customers.map(customer => ({
    customer_id: customer.customer_id,
    customer_name: customer.customer_name,
    order_count: customerOrderCount.get(customer.customer_id) || 0,
    total_order_value:
        customerOrderValue.get(customer.customer_id) || 0
}));

printRows(customerReport);

// ============================================================================
// 34. CARDINALITY ASSERTIONS
// ============================================================================

printTitle("28. CARDINALITY ASSERTIONS");

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(
            `${message}: expected ${expected}, received ${actual}`
        );
    }
}

assertEqual(
    crossJoin(
        [{ x: 1 }, { x: 2 }],
        [{ y: 1 }, { y: 2 }, { y: 3 }]
    ).length,
    6,
    "Cross join cardinality"
);

assertEqual(
    estimateJoinCardinality(
        [{ key: "A" }, { key: "A" }],
        [{ key: "A" }, { key: "A" }, { key: "A" }],
        "key",
        "key"
    ),
    6,
    "Duplicate key cardinality"
);

assertEqual(
    largeOutput.length,
    10000,
    "Large matching group cardinality"
);

assertEqual(
    employeesWithoutProjects.length,
    0,
    "Employee project relationship"
);

console.log("All cardinality assertions passed.");

// ============================================================================
// 35. SQL PATTERN REFERENCE
// ============================================================================

printTitle("29. SQL PATTERN REFERENCE");

const sqlPatterns = {
    selfJoin:
        "SELECT e.employee_name, m.employee_name AS manager_name " +
        "FROM employees AS e " +
        "LEFT JOIN employees AS m " +
        "ON e.manager_id = m.employee_id;",

    crossJoin:
        "SELECT d.department_name, p.project_name " +
        "FROM departments AS d " +
        "CROSS JOIN projects AS p;",

    multipleJoins:
        "SELECT e.employee_name, p.project_name " +
        "FROM employees AS e " +
        "JOIN employee_projects AS ep " +
        "ON ep.employee_id = e.employee_id " +
        "JOIN projects AS p " +
        "ON p.project_id = ep.project_id;",

    semiJoin:
        "SELECT e.* FROM employees AS e " +
        "WHERE EXISTS (" +
        "SELECT 1 FROM employee_projects AS ep " +
        "WHERE ep.employee_id = e.employee_id" +
        ");",

    antiJoin:
        "SELECT e.* FROM employees AS e " +
        "WHERE NOT EXISTS (" +
        "SELECT 1 FROM employee_projects AS ep " +
        "WHERE ep.employee_id = e.employee_id" +
        ");",

    preAggregation:
        "SELECT o.order_id, i.total_quantity, p.total_paid " +
        "FROM orders AS o " +
        "LEFT JOIN (" +
        "SELECT order_id, SUM(quantity) AS total_quantity " +
        "FROM order_items GROUP BY order_id" +
        ") AS i ON i.order_id = o.order_id " +
        "LEFT JOIN (" +
        "SELECT order_id, SUM(amount) AS total_paid " +
        "FROM payments GROUP BY order_id" +
        ") AS p ON p.order_id = o.order_id;"
};

for (const [name, sql] of Object.entries(sqlPatterns)) {
    console.log(`\n${name.toUpperCase()}:\n${sql}`);
}

// ============================================================================
// 36. PRODUCTION CHECKLIST
// ============================================================================

printTitle("30. PRODUCTION JOIN CHECKLIST");

const checklist = [
    "Define the row grain of every input table.",
    "Identify primary keys and foreign keys.",
    "Profile duplicate join keys.",
    "Check NULL behavior.",
    "Estimate output cardinality.",
    "Treat CROSS JOIN as explicitly multiplicative.",
    "Use aliases for self joins.",
    "Model many-to-many relationships with bridge tables.",
    "Pre-aggregate independent one-to-many relationships when needed.",
    "Do not use DISTINCT as a substitute for correct join logic.",
    "Validate aggregate results.",
    "Use suitable indexes in real database systems.",
    "Inspect execution plans for expensive production queries.",
    "Consider skewed and highly duplicated keys.",
    "Test empty inputs and missing matches.",
    "Test NULL and duplicate values.",
    "Guard against accidental Cartesian products."
];

for (const item of checklist) {
    console.log(`- ${item}`);
}

// ============================================================================
// 37. FINAL MESSAGE
// ============================================================================

printTitle("31. COMPLETION CHECK");

console.log(
    "SQL Joins II demonstrations completed successfully."
);
