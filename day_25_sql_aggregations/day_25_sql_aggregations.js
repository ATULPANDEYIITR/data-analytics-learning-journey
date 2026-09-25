/*
 * SQL Aggregations: JavaScript Study Companion
 *
 * This file demonstrates the conceptual behavior of SQL aggregation functions
 * using ordinary JavaScript data structures.
 *
 * The program intentionally models SQL NULL behavior with JavaScript null.
 * It also includes SQL statements as strings so that the relationship between
 * the JavaScript calculations and actual SQL syntax remains explicit.
 *
 * No external npm package is required.
 */

"use strict";

const employees = [
    {
        employeeId: 1,
        name: "Asha",
        department: "Engineering",
        salary: 90000,
        bonus: 10000,
        score: 92
    },
    {
        employeeId: 2,
        name: "Ravi",
        department: "Engineering",
        salary: 85000,
        bonus: null,
        score: 88
    },
    {
        employeeId: 3,
        name: "Meera",
        department: "Engineering",
        salary: null,
        bonus: 8000,
        score: 95
    },
    {
        employeeId: 4,
        name: "Kabir",
        department: "Sales",
        salary: 70000,
        bonus: 7000,
        score: 81
    },
    {
        employeeId: 5,
        name: "Nisha",
        department: "Sales",
        salary: 72000,
        bonus: null,
        score: 79
    },
    {
        employeeId: 6,
        name: "Arjun",
        department: "Sales",
        salary: null,
        bonus: 5000,
        score: null
    },
    {
        employeeId: 7,
        name: "Isha",
        department: "HR",
        salary: 65000,
        bonus: 4000,
        score: 91
    },
    {
        employeeId: 8,
        name: "Vikram",
        department: "HR",
        salary: 62000,
        bonus: null,
        score: 85
    },
    {
        employeeId: 9,
        name: "Tara",
        department: "Research",
        salary: null,
        bonus: null,
        score: null
    }
];

const orders = [
    {
        orderId: 101,
        customer: "Alice",
        category: "Laptop",
        quantity: 2,
        unitPrice: 80000,
        discount: 0.10,
        status: "completed"
    },
    {
        orderId: 102,
        customer: "Bob",
        category: "Phone",
        quantity: 3,
        unitPrice: 30000,
        discount: null,
        status: "completed"
    },
    {
        orderId: 103,
        customer: "Alice",
        category: "Monitor",
        quantity: 1,
        unitPrice: 20000,
        discount: 0.05,
        status: "completed"
    },
    {
        orderId: 104,
        customer: "Cara",
        category: "Phone",
        quantity: 2,
        unitPrice: null,
        discount: 0.10,
        status: "pending"
    },
    {
        orderId: 105,
        customer: "Bob",
        category: "Laptop",
        quantity: 1,
        unitPrice: 80000,
        discount: null,
        status: "completed"
    },
    {
        orderId: 106,
        customer: "Cara",
        category: "Tablet",
        quantity: 4,
        unitPrice: 25000,
        discount: 0.15,
        status: "completed"
    },
    {
        orderId: 107,
        customer: "Alice",
        category: "Tablet",
        quantity: null,
        unitPrice: 25000,
        discount: 0.05,
        status: "cancelled"
    }
];

function title(text) {
    console.log(`\n${"=".repeat(80)}\n${text}\n${"=".repeat(80)}`);
}

function sqlNull(value) {
    return value === null || value === undefined;
}

function sqlCountStar(rows) {
    // SQL COUNT(*) counts rows regardless of NULL values.
    return rows.length;
}

function sqlCountColumn(rows, selector) {
    // SQL COUNT(column) ignores rows where the selected expression is NULL.
    return rows.filter(row => !sqlNull(selector(row))).length;
}

function sqlCountDistinct(rows, selector) {
    // SQL COUNT(DISTINCT expression) ignores NULL and counts unique values.
    const values = rows
        .map(selector)
        .filter(value => !sqlNull(value));

    return new Set(values).size;
}

function sqlSum(rows, selector) {
    // SQL SUM ignores NULL values.
    const values = rows
        .map(selector)
        .filter(value => !sqlNull(value));

    // SUM over an empty input set is NULL in SQL.
    if (values.length === 0) {
        return null;
    }

    return values.reduce((total, value) => total + value, 0);
}

function sqlAverage(rows, selector) {
    // AVG is based only on non-NULL values.
    const values = rows
        .map(selector)
        .filter(value => !sqlNull(value));

    if (values.length === 0) {
        return null;
    }

    return values.reduce((total, value) => total + value, 0) / values.length;
}

function sqlMin(rows, selector) {
    const values = rows
        .map(selector)
        .filter(value => !sqlNull(value));

    return values.length === 0 ? null : Math.min(...values);
}

function sqlMax(rows, selector) {
    const values = rows
        .map(selector)
        .filter(value => !sqlNull(value));

    return values.length === 0 ? null : Math.max(...values);
}

function coalesce(value, fallback) {
    // This models SQL COALESCE for the common two-value case.
    return sqlNull(value) ? fallback : value;
}

function sqlNullIf(value, comparison) {
    // NULLIF(a, b) returns NULL when a equals b.
    return value === comparison ? null : value;
}

function groupRows(rows, keySelector) {
    const groups = new Map();

    for (const row of rows) {
        const key = keySelector(row);

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(row);
    }

    return groups;
}

function printObject(object) {
    console.log(JSON.stringify(object, null, 2));
}

function beginnerExamples() {
    title("1. COUNT");

    console.log("COUNT(*) =", sqlCountStar(employees));
    console.log(
        "COUNT(salary) =",
        sqlCountColumn(employees, employee => employee.salary)
    );
    console.log(
        "COUNT(bonus) =",
        sqlCountColumn(employees, employee => employee.bonus)
    );
    console.log(
        "COUNT(DISTINCT department) =",
        sqlCountDistinct(employees, employee => employee.department)
    );

    console.log(
        "Missing salaries =",
        sqlCountStar(employees) -
        sqlCountColumn(employees, employee => employee.salary)
    );
}

function sumAndAverageExamples() {
    title("2. SUM and AVG");

    console.log(
        "Total salary =",
        sqlSum(employees, employee => employee.salary)
    );

    console.log(
        "Total bonus =",
        sqlSum(employees, employee => employee.bonus)
    );

    console.log(
        "Average salary =",
        sqlAverage(employees, employee => employee.salary)
    );

    console.log(
        "Average score =",
        sqlAverage(employees, employee => employee.score)
    );

    console.log(
        "Minimum salary =",
        sqlMin(employees, employee => employee.salary)
    );

    console.log(
        "Maximum salary =",
        sqlMax(employees, employee => employee.salary)
    );
}

function groupByExamples() {
    title("3. GROUP BY");

    const groups = groupRows(employees, employee => employee.department);

    for (const [department, rows] of groups) {
        const result = {
            department,
            employeeCount: sqlCountStar(rows),
            employeesWithSalary: sqlCountColumn(rows, employee => employee.salary),
            salarySum: sqlSum(rows, employee => employee.salary),
            averageSalary: sqlAverage(rows, employee => employee.salary),
            minimumSalary: sqlMin(rows, employee => employee.salary),
            maximumSalary: sqlMax(rows, employee => employee.salary)
        };

        printObject(result);
    }
}

function conditionalAggregation() {
    title("4. CONDITIONAL AGGREGATION");

    const highSalaryCount = employees.filter(
        employee => employee.salary !== null && employee.salary >= 80000
    ).length;

    const missingSalaryCount = employees.filter(
        employee => employee.salary === null
    ).length;

    const highPerformanceCount = employees.filter(
        employee => employee.score !== null && employee.score >= 90
    ).length;

    console.log({
        highSalaryCount,
        missingSalaryCount,
        highPerformanceCount
    });

    console.log(
        "\nSQL equivalent concept:",
        "SUM(CASE WHEN salary >= 80000 THEN 1 ELSE 0 END)"
    );
}

function aggregateExpressions() {
    title("5. AGGREGATE EXPRESSIONS");

    const completedOrders = orders.filter(
        order => order.status === "completed"
    );

    const grossRevenue = sqlSum(
        completedOrders,
        order => {
            if (order.quantity === null || order.unitPrice === null) {
                return null;
            }

            return order.quantity * order.unitPrice;
        }
    );

    const netRevenue = sqlSum(
        completedOrders,
        order => {
            if (order.quantity === null || order.unitPrice === null) {
                return null;
            }

            const normalizedDiscount = coalesce(order.discount, 0);

            return (
                order.quantity *
                order.unitPrice *
                (1 - normalizedDiscount)
            );
        }
    );

    const averageOrderValue = sqlAverage(
        completedOrders,
        order => {
            if (order.quantity === null || order.unitPrice === null) {
                return null;
            }

            const normalizedDiscount = coalesce(order.discount, 0);

            return (
                order.quantity *
                order.unitPrice *
                (1 - normalizedDiscount)
            );
        }
    );

    console.log({
        grossRevenue,
        netRevenue,
        averageOrderValue
    });
}

function nullHandling() {
    title("6. NULL HANDLING");

    const values = [10, 20, null, 30, null];

    console.log("Input:", values);
    console.log("COUNT(*) concept:", values.length);
    console.log(
        "COUNT(value) concept:",
        values.filter(value => value !== null).length
    );
    console.log("SUM(value):", sqlSum(values.map(value => ({ value })), row => row.value));
    console.log("AVG(value):", sqlAverage(values.map(value => ({ value })), row => row.value));
    console.log("MIN(value):", sqlMin(values.map(value => ({ value })), row => row.value));
    console.log("MAX(value):", sqlMax(values.map(value => ({ value })), row => row.value));

    console.log(
        "\nCOALESCE(NULL, 0) =",
        coalesce(null, 0)
    );

    console.log(
        "NULLIF(0, 0) =",
        sqlNullIf(0, 0)
    );
}

function emptySetBehavior() {
    title("7. EMPTY INPUT");

    const emptyRows = [];

    console.log("COUNT(*) =", sqlCountStar(emptyRows));
    console.log("SUM(value) =", sqlSum(emptyRows, row => row.value));
    console.log("AVG(value) =", sqlAverage(emptyRows, row => row.value));
    console.log("MIN(value) =", sqlMin(emptyRows, row => row.value));
    console.log("MAX(value) =", sqlMax(emptyRows, row => row.value));

    console.log(
        "\nThis models the important SQL distinction:",
        "COUNT returns 0; SUM/AVG/MIN/MAX return NULL."
    );
}

function orderAnalytics() {
    title("8. ORDER ANALYTICS");

    const completedOrders = orders.filter(
        order => order.status === "completed"
    );

    const groups = groupRows(
        completedOrders,
        order => order.category
    );

    const report = [];

    for (const [category, rows] of groups) {
        report.push({
            category,
            completedOrders: sqlCountStar(rows),
            units: sqlSum(rows, order => order.quantity),
            averageQuantity: sqlAverage(rows, order => order.quantity),
            revenue: sqlSum(rows, order => {
                if (order.quantity === null || order.unitPrice === null) {
                    return null;
                }

                return (
                    order.quantity *
                    order.unitPrice *
                    (1 - coalesce(order.discount, 0))
                );
            })
        });
    }

    report.sort((a, b) => (b.revenue ?? -Infinity) - (a.revenue ?? -Infinity));

    printObject(report);
}

function whereVsHaving() {
    title("9. WHERE VS HAVING");

    const filteredRows = employees.filter(
        employee => employee.department !== "HR"
    );

    const groups = groupRows(
        filteredRows,
        employee => employee.department
    );

    for (const [department, rows] of groups) {
        const averageSalary = sqlAverage(rows, employee => employee.salary);

        // This models HAVING AVG(salary) >= 70000.
        if (averageSalary !== null && averageSalary >= 70000) {
            console.log({
                department,
                employeeCount: sqlCountStar(rows),
                averageSalary
            });
        }
    }

    console.log(
        "\nWHERE filters rows before GROUP BY; HAVING filters groups after aggregation."
    );
}

function distinctAndDuplicates() {
    title("10. DISTINCT");

    console.log(
        "All order rows:",
        sqlCountStar(orders)
    );

    console.log(
        "Customer values:",
        sqlCountColumn(orders, order => order.customer)
    );

    console.log(
        "Distinct customers:",
        sqlCountDistinct(orders, order => order.customer)
    );

    console.log(
        "Distinct categories:",
        sqlCountDistinct(orders, order => order.category)
    );
}

function ratioExample() {
    title("11. SAFE RATIOS");

    const attempts = 0;
    const successes = 0;

    const denominator = sqlNullIf(attempts, 0);

    const successRate =
        denominator === null
            ? null
            : successes / denominator;

    console.log({
        successes,
        attempts,
        successRate
    });

    console.log(
        "SQL pattern:",
        "SUM(successful) / NULLIF(SUM(attempts), 0)"
    );
}

function joinMultiplicationConcept() {
    title("12. JOIN MULTIPLICATION");

    const employeeProjects = [
        { employeeId: 1, project: "Atlas" },
        { employeeId: 1, project: "Beacon" },
        { employeeId: 2, project: "Atlas" },
        { employeeId: 3, project: "Cipher" }
    ];

    const joinedRows = [];

    for (const employee of employees) {
        for (const project of employeeProjects) {
            if (employee.employeeId === project.employeeId) {
                joinedRows.push({
                    employeeId: employee.employeeId,
                    name: employee.name,
                    salary: employee.salary,
                    project: project.project
                });
            }
        }
    }

    console.log("Joined rows:", joinedRows.length);

    console.log(
        "COUNT(*) concept:",
        joinedRows.length
    );

    console.log(
        "COUNT(DISTINCT employee_id) concept:",
        new Set(joinedRows.map(row => row.employeeId)).size
    );

    console.log(
        "Important: SUM(employee.salary) after a one-to-many join can multiply salary."
    );
}

function performanceConsiderations() {
    title("13. PERFORMANCE CONSIDERATIONS");

    console.log(
        [
            "1. Filter rows early when the business meaning allows it.",
            "2. Avoid unnecessary DISTINCT operations because deduplication has a cost.",
            "3. Index columns used heavily in WHERE, JOIN, and GROUP BY when justified.",
            "4. Inspect query plans for production workloads.",
            "5. Avoid aggregating duplicated rows caused by one-to-many joins.",
            "6. Reduce transferred data by selecting only required columns.",
            "7. Test aggregation queries with realistic data volumes."
        ].join("\n")
    );
}

function actualSqlExamples() {
    title("14. ACTUAL SQL SYNTAX REFERENCE");

    const queries = {
        countRows: `
SELECT COUNT(*)
FROM employees;
`,
        countKnownValues: `
SELECT COUNT(salary)
FROM employees;
`,
        countDistinct: `
SELECT COUNT(DISTINCT department)
FROM employees;
`,
        summary: `
SELECT
    COUNT(*) AS employees,
    SUM(salary) AS salary_sum,
    AVG(salary) AS average_salary,
    MIN(salary) AS minimum_salary,
    MAX(salary) AS maximum_salary
FROM employees;
`,
        groupedSummary: `
SELECT
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department;
`,
        conditionalAggregation: `
SELECT
    SUM(CASE WHEN salary >= 80000 THEN 1 ELSE 0 END)
        AS high_salary_count
FROM employees;
`,
        nullSafeRevenue: `
SELECT
    SUM(
        quantity * unit_price *
        (1 - COALESCE(discount, 0))
    ) AS net_revenue
FROM orders
WHERE order_status = 'completed';
`,
        having: `
SELECT
    department,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department
HAVING AVG(salary) >= 70000;
`
    };

    for (const [name, query] of Object.entries(queries)) {
        console.log(`\n${name}:\n${query.trim()}`);
    }
}

function runValidationTests() {
    title("15. VALIDATION TESTS");

    const tests = [
        {
            name: "COUNT(*) includes all rows",
            actual: sqlCountStar(employees),
            expected: 9
        },
        {
            name: "COUNT(salary) excludes NULL",
            actual: sqlCountColumn(employees, employee => employee.salary),
            expected: 6
        },
        {
            name: "COUNT(DISTINCT department)",
            actual: sqlCountDistinct(employees, employee => employee.department),
            expected: 4
        },
        {
            name: "MIN salary",
            actual: sqlMin(employees, employee => employee.salary),
            expected: 62000
        },
        {
            name: "MAX salary",
            actual: sqlMax(employees, employee => employee.salary),
            expected: 90000
        },
        {
            name: "SUM on empty input",
            actual: sqlSum([], row => row.value),
            expected: null
        },
        {
            name: "AVG on empty input",
            actual: sqlAverage([], row => row.value),
            expected: null
        }
    ];

    let passed = 0;

    for (const test of tests) {
        const success = Object.is(test.actual, test.expected);

        console.log(
            `${success ? "PASS" : "FAIL"}: ${test.name}`
        );

        if (!success) {
            console.log({
                expected: test.expected,
                actual: test.actual
            });
        }

        passed += success ? 1 : 0;
    }

    console.log(`\n${passed}/${tests.length} tests passed.`);

    if (passed !== tests.length) {
        throw new Error("Aggregation validation failed.");
    }
}

function main() {
    title("SQL AGGREGATIONS - JAVASCRIPT STUDY COMPANION");

    beginnerExamples();
    sumAndAverageExamples();
    groupByExamples();
    conditionalAggregation();
    aggregateExpressions();
    nullHandling();
    emptySetBehavior();
    orderAnalytics();
    whereVsHaving();
    distinctAndDuplicates();
    ratioExample();
    joinMultiplicationConcept();
    performanceConsiderations();
    actualSqlExamples();
    runValidationTests();

    title("STUDY CHECKLIST");

    const checklist = [
        "COUNT(*) versus COUNT(column)",
        "COUNT(DISTINCT column)",
        "SUM and NULL values",
        "AVG and NULL values",
        "MIN and MAX",
        "GROUP BY",
        "WHERE versus HAVING",
        "CASE-based conditional aggregation",
        "COALESCE and NULLIF",
        "Aggregate expressions",
        "Empty-set behavior",
        "Join multiplication",
        "Performance considerations"
    ];

    for (const item of checklist) {
        console.log(`[ ] ${item}`);
    }
}

main();
