/*
SQL Sorting & Limiting
======================

This file demonstrates the logic and application-side patterns surrounding:

    ORDER BY
    ASC
    DESC
    LIMIT
    OFFSET
    deterministic ordering
    pagination
    keyset pagination
    safe dynamic sorting

JavaScript does not provide a built-in SQL database engine. Therefore this
file uses JavaScript arrays to model relational rows and builds real SQL
statements as strings for database-facing examples.

The array implementations demonstrate the same ordering semantics that an
application must reason about when consuming SQL results.

The file is executable with a modern JavaScript runtime such as Node.js and
requires no external packages.
*/

"use strict";


// -----------------------------------------------------------------------------
// Output helpers
// -----------------------------------------------------------------------------

function heading(title) {
    console.log("\n" + "=".repeat(88));
    console.log(title);
    console.log("=".repeat(88));
}

function subheading(title) {
    console.log("\n" + "-".repeat(88));
    console.log(title);
    console.log("-".repeat(88));
}

function printRows(rows) {
    if (rows.length === 0) {
        console.log("(no rows)");
        return;
    }

    console.table(rows);
}


// -----------------------------------------------------------------------------
// Sample relational data
// -----------------------------------------------------------------------------

const employees = [
    {
        employeeId: 1,
        employeeName: "Aarav",
        department: "Engineering",
        salary: 125000,
        performanceScore: 9.2,
        hireDate: "2021-04-15",
        city: "Delhi"
    },
    {
        employeeId: 2,
        employeeName: "Meera",
        department: "Engineering",
        salary: 125000,
        performanceScore: 8.8,
        hireDate: "2022-08-21",
        city: "Mumbai"
    },
    {
        employeeId: 3,
        employeeName: "Kabir",
        department: "Engineering",
        salary: 98000,
        performanceScore: 9.5,
        hireDate: "2023-01-10",
        city: "Pune"
    },
    {
        employeeId: 4,
        employeeName: "Anaya",
        department: "Engineering",
        salary: 87000,
        performanceScore: null,
        hireDate: "2024-02-19",
        city: "Lucknow"
    },
    {
        employeeId: 5,
        employeeName: "Vihaan",
        department: "Finance",
        salary: 110000,
        performanceScore: 8.9,
        hireDate: "2020-07-01",
        city: "Delhi"
    },
    {
        employeeId: 6,
        employeeName: "Ishita",
        department: "Finance",
        salary: 110000,
        performanceScore: 9.1,
        hireDate: "2021-11-12",
        city: "Bengaluru"
    },
    {
        employeeId: 7,
        employeeName: "Rohan",
        department: "Finance",
        salary: 92000,
        performanceScore: 7.8,
        hireDate: "2023-05-04",
        city: "Mumbai"
    },
    {
        employeeId: 8,
        employeeName: "Diya",
        department: "Finance",
        salary: 76000,
        performanceScore: null,
        hireDate: "2024-06-30",
        city: "Pune"
    },
    {
        employeeId: 9,
        employeeName: "Arjun",
        department: "Sales",
        salary: 105000,
        performanceScore: 8.4,
        hireDate: "2021-02-17",
        city: "Delhi"
    },
    {
        employeeId: 10,
        employeeName: "Sara",
        department: "Sales",
        salary: 105000,
        performanceScore: 8.7,
        hireDate: "2022-03-28",
        city: "Hyderabad"
    },
    {
        employeeId: 11,
        employeeName: "Advik",
        department: "Sales",
        salary: 88000,
        performanceScore: 7.9,
        hireDate: "2023-09-11",
        city: "Lucknow"
    },
    {
        employeeId: 12,
        employeeName: "Tara",
        department: "Sales",
        salary: 69000,
        performanceScore: null,
        hireDate: "2024-01-05",
        city: null
    },
    {
        employeeId: 13,
        employeeName: "Neil",
        department: "Operations",
        salary: 99000,
        performanceScore: 8.1,
        hireDate: "2020-12-19",
        city: "Delhi"
    },
    {
        employeeId: 14,
        employeeName: "Kiara",
        department: "Operations",
        salary: 91000,
        performanceScore: 9.0,
        hireDate: "2022-10-07",
        city: "Mumbai"
    },
    {
        employeeId: 15,
        employeeName: "Yash",
        department: "Operations",
        salary: 91000,
        performanceScore: 8.3,
        hireDate: "2023-03-14",
        city: "Pune"
    },
    {
        employeeId: 16,
        employeeName: "Naina",
        department: "Operations",
        salary: 72000,
        performanceScore: 7.5,
        hireDate: "2024-05-23",
        city: "Lucknow"
    }
];


// -----------------------------------------------------------------------------
// Generic SQL-style comparison
// -----------------------------------------------------------------------------

function compareValues(a, b, direction = "ASC", nullsLast = false) {
    const aIsNull = a === null || a === undefined;
    const bIsNull = b === null || b === undefined;

    if (aIsNull || bIsNull) {
        if (aIsNull && bIsNull) {
            return 0;
        }

        if (nullsLast) {
            return aIsNull ? 1 : -1;
        }

        return aIsNull ? -1 : 1;
    }

    let comparison = 0;

    if (typeof a === "string" && typeof b === "string") {
        comparison = a.localeCompare(b);
    } else if (a < b) {
        comparison = -1;
    } else if (a > b) {
        comparison = 1;
    }

    return direction === "DESC" ? -comparison : comparison;
}


function compareByKeys(firstRow, secondRow, sortKeys) {
    for (const sortKey of sortKeys) {
        const firstValue = firstRow[sortKey.field];
        const secondValue = secondRow[sortKey.field];

        const comparison = compareValues(
            firstValue,
            secondValue,
            sortKey.direction ?? "ASC",
            sortKey.nullsLast ?? false
        );

        if (comparison !== 0) {
            return comparison;
        }
    }

    return 0;
}


function sqlStyleOrderBy(rows, sortKeys) {
    return [...rows].sort(
        (firstRow, secondRow) =>
            compareByKeys(firstRow, secondRow, sortKeys)
    );
}


function limit(rows, count) {
    if (!Number.isInteger(count) || count < 0) {
        throw new RangeError("LIMIT must be a non-negative integer.");
    }

    return rows.slice(0, count);
}


function offsetLimit(rows, offsetValue, count) {
    if (!Number.isInteger(offsetValue) || offsetValue < 0) {
        throw new RangeError("OFFSET must be a non-negative integer.");
    }

    if (!Number.isInteger(count) || count < 0) {
        throw new RangeError("LIMIT must be a non-negative integer.");
    }

    return rows.slice(offsetValue, offsetValue + count);
}


// -----------------------------------------------------------------------------
// Basic ASC and DESC
// -----------------------------------------------------------------------------

function demonstrateAscending() {
    heading("1. ASCENDING ORDER");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "ASC" }
    ]);

    printRows(
        ordered.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    console.log(
        "\nASC orders numeric values from smallest to largest."
    );
}


function demonstrateDescending() {
    heading("2. DESCENDING ORDER");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" }
    ]);

    printRows(
        ordered.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    console.log(
        "\nDESC orders numeric values from largest to smallest."
    );
}


// -----------------------------------------------------------------------------
// Multiple sort keys
// -----------------------------------------------------------------------------

function demonstrateMultipleSortKeys() {
    heading("3. MULTIPLE SORT KEYS");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "department", direction: "ASC" },
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    printRows(
        ordered.map((employee) => ({
            department: employee.department,
            employeeName: employee.employeeName,
            salary: employee.salary,
            employeeId: employee.employeeId
        }))
    );

    console.log(
        `
The first key establishes department order.
The second key orders salaries inside each department.
The unique employeeId completes the ordering.`
    );
}


// -----------------------------------------------------------------------------
// Deterministic ordering
// -----------------------------------------------------------------------------

function demonstrateDeterministicOrdering() {
    heading("4. DETERMINISTIC ORDERING");

    subheading("Ordering only by salary");

    const salaryOnly = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" }
    ]);

    printRows(
        salaryOnly.map((employee) => ({
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    subheading("Ordering by salary plus unique employeeId");

    const deterministic = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    printRows(
        deterministic.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    console.log(
        `
A sort key that is not unique does not fully specify the order of tied rows.
Adding a unique key creates a total ordering for this dataset.`
    );
}


// -----------------------------------------------------------------------------
// LIMIT and OFFSET
// -----------------------------------------------------------------------------

function demonstrateLimit() {
    heading("5. LIMIT");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    const topFive = limit(ordered, 5);

    printRows(
        topFive.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    console.log("\nThis models SQL: ORDER BY salary DESC LIMIT 5.");
}


function demonstrateOffset() {
    heading("6. OFFSET");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    const page = offsetLimit(ordered, 5, 5);

    printRows(
        page.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    console.log(
        "\nThis models SQL: ORDER BY salary DESC LIMIT 5 OFFSET 5."
    );
}


// -----------------------------------------------------------------------------
// Pagination
// -----------------------------------------------------------------------------

function calculateOffset(pageNumber, pageSize) {
    if (!Number.isInteger(pageNumber) || pageNumber < 1) {
        throw new RangeError("Page number must be >= 1.");
    }

    if (!Number.isInteger(pageSize) || pageSize < 1) {
        throw new RangeError("Page size must be >= 1.");
    }

    if (pageSize > 100) {
        throw new RangeError("Page size must not exceed 100.");
    }

    return (pageNumber - 1) * pageSize;
}


function demonstratePagination() {
    heading("7. OFFSET-BASED PAGINATION");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    const pageSize = 4;

    for (let pageNumber = 1; pageNumber <= 5; pageNumber += 1) {
        const offsetValue = calculateOffset(pageNumber, pageSize);
        const page = offsetLimit(
            ordered,
            offsetValue,
            pageSize
        );

        console.log(
            `\nPage ${pageNumber}, OFFSET ${offsetValue}`
        );

        printRows(
            page.map((employee) => ({
                employeeId: employee.employeeId,
                employeeName: employee.employeeName,
                salary: employee.salary
            }))
        );
    }
}


// -----------------------------------------------------------------------------
// Top-N and bottom-N
// -----------------------------------------------------------------------------

function demonstrateTopAndBottomN() {
    heading("8. TOP-N AND BOTTOM-N");

    const highest = limit(
        sqlStyleOrderBy(employees, [
            { field: "salary", direction: "DESC" },
            { field: "employeeId", direction: "ASC" }
        ]),
        3
    );

    console.log("\nTop 3 salaries:");
    printRows(
        highest.map((employee) => ({
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    const lowest = limit(
        sqlStyleOrderBy(employees, [
            { field: "salary", direction: "ASC" },
            { field: "employeeId", direction: "ASC" }
        ]),
        3
    );

    console.log("\nBottom 3 salaries:");
    printRows(
        lowest.map((employee) => ({
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );
}


// -----------------------------------------------------------------------------
// NULL ordering
// -----------------------------------------------------------------------------

function demonstrateNullOrdering() {
    heading("9. EXPLICIT NULL ORDERING");

    const ordered = sqlStyleOrderBy(employees, [
        {
            field: "performanceScore",
            direction: "ASC",
            nullsLast: true
        },
        {
            field: "employeeId",
            direction: "ASC"
        }
    ]);

    printRows(
        ordered.map((employee) => ({
            employeeName: employee.employeeName,
            performanceScore: employee.performanceScore
        }))
    );

    console.log(
        `
The nullsLast option models the important idea of explicitly deciding where
missing values belong rather than depending on a database-specific default.`
    );
}


// -----------------------------------------------------------------------------
// Conditional ordering
// -----------------------------------------------------------------------------

function demonstrateConditionalOrdering() {
    heading("10. CONDITIONAL ORDERING");

    const priority = (employee) => {
        if (employee.performanceScore === null) {
            return 2;
        }

        if (employee.performanceScore >= 9.0) {
            return 0;
        }

        return 1;
    };

    const ordered = [...employees].sort((firstEmployee, secondEmployee) => {
        const priorityComparison =
            priority(firstEmployee) - priority(secondEmployee);

        if (priorityComparison !== 0) {
            return priorityComparison;
        }

        const scoreComparison = compareValues(
            firstEmployee.performanceScore,
            secondEmployee.performanceScore,
            "DESC",
            true
        );

        if (scoreComparison !== 0) {
            return scoreComparison;
        }

        return firstEmployee.employeeId - secondEmployee.employeeId;
    });

    printRows(
        ordered.map((employee) => ({
            employeeName: employee.employeeName,
            performanceScore: employee.performanceScore,
            priority: priority(employee)
        }))
    );
}


// -----------------------------------------------------------------------------
// Expressions in ORDER BY
// -----------------------------------------------------------------------------

function demonstrateExpressionOrdering() {
    heading("11. EXPRESSION-BASED ORDERING");

    const projected = employees.map((employee) => ({
        employeeName: employee.employeeName,
        salary: employee.salary,
        projectedSalary: employee.salary * 1.10,
        employeeId: employee.employeeId
    }));

    projected.sort((firstRow, secondRow) => {
        const salaryComparison =
            secondRow.projectedSalary - firstRow.projectedSalary;

        if (salaryComparison !== 0) {
            return salaryComparison;
        }

        return firstRow.employeeId - secondRow.employeeId;
    });

    printRows(projected.slice(0, 5));
}


// -----------------------------------------------------------------------------
// Filtering plus ordering
// -----------------------------------------------------------------------------

function demonstrateFilteringAndOrdering() {
    heading("12. FILTER + ORDER BY + LIMIT");

    const engineering = employees.filter(
        (employee) => employee.department === "Engineering"
    );

    const result = limit(
        sqlStyleOrderBy(engineering, [
            { field: "salary", direction: "DESC" },
            { field: "employeeId", direction: "ASC" }
        ]),
        3
    );

    printRows(
        result.map((employee) => ({
            employeeName: employee.employeeName,
            department: employee.department,
            salary: employee.salary
        }))
    );

    console.log(
        `
The conceptual SQL pattern is:

WHERE department = 'Engineering'
ORDER BY salary DESC, employee_id ASC
LIMIT 3`
    );
}


// -----------------------------------------------------------------------------
// Top-N per group
// -----------------------------------------------------------------------------

function demonstrateTopNPerGroup() {
    heading("13. TOP-N PER GROUP");

    const departments = [
        ...new Set(employees.map((employee) => employee.department))
    ];

    const result = [];

    for (const department of departments) {
        const departmentEmployees = employees.filter(
            (employee) => employee.department === department
        );

        const topTwo = limit(
            sqlStyleOrderBy(departmentEmployees, [
                { field: "salary", direction: "DESC" },
                { field: "employeeId", direction: "ASC" }
            ]),
            2
        );

        for (const employee of topTwo) {
            result.push({
                department,
                employeeName: employee.employeeName,
                salary: employee.salary
            });
        }
    }

    const finalResult = sqlStyleOrderBy(result, [
        { field: "department", direction: "ASC" },
        { field: "salary", direction: "DESC" }
    ]);

    printRows(finalResult);
}


// -----------------------------------------------------------------------------
// Keyset pagination
// -----------------------------------------------------------------------------

function compareForKeyset(employee, lastSalary, lastEmployeeId) {
    /*
    Stable ordering:

        salary DESC,
        employeeId ASC

    A row comes after the cursor when:

        salary < lastSalary
        OR
        salary = lastSalary AND employeeId > lastEmployeeId
    */

    return (
        employee.salary < lastSalary ||
        (
            employee.salary === lastSalary &&
            employee.employeeId > lastEmployeeId
        )
    );
}


function demonstrateKeysetPagination() {
    heading("14. KEYSET PAGINATION");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    const firstPage = limit(ordered, 5);

    console.log("\nFirst page:");
    printRows(
        firstPage.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    const lastRow = firstPage[firstPage.length - 1];

    const nextPageCandidates = ordered.filter(
        (employee) =>
            compareForKeyset(
                employee,
                lastRow.salary,
                lastRow.employeeId
            )
    );

    const secondPage = limit(nextPageCandidates, 5);

    console.log("\nSecond page:");
    printRows(
        secondPage.map((employee) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            salary: employee.salary
        }))
    );

    console.log(
        `
Keyset pagination uses the previous page's final sort-key values as a cursor.
It avoids increasing OFFSET values for sequential navigation.`
    );
}


// -----------------------------------------------------------------------------
// Dynamic ORDER BY security
// -----------------------------------------------------------------------------

function buildSafeEmployeeQuery(requestedSort, requestedDirection) {
    const allowedColumns = {
        name: "employee_name",
        salary: "salary",
        score: "performance_score",
        hireDate: "hire_date"
    };

    const sortColumn = allowedColumns[requestedSort];

    if (!sortColumn) {
        throw new Error("Unsupported sort column.");
    }

    const direction = String(requestedDirection).toUpperCase();

    if (!["ASC", "DESC"].includes(direction)) {
        throw new Error("Unsupported sort direction.");
    }

    /*
    The column and direction are inserted only after allow-list validation.
    Values such as a department filter should be supplied separately through
    parameterized SQL APIs in a real database driver.
    */
    return `
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY ${sortColumn} ${direction}, employee_id ASC
        LIMIT ?
    `.trim();
}


function demonstrateSafeDynamicOrdering() {
    heading("15. SAFE DYNAMIC ORDERING");

    const safeQuery = buildSafeEmployeeQuery("salary", "DESC");

    console.log(safeQuery);

    try {
        buildSafeEmployeeQuery(
            "salary; DROP TABLE employees",
            "DESC"
        );
    } catch (error) {
        console.log(
            "\nRejected unsafe sort field:",
            error.message
        );
    }

    try {
        buildSafeEmployeeQuery("salary", "DESC; DROP TABLE employees");
    } catch (error) {
        console.log(
            "Rejected unsafe sort direction:",
            error.message
        );
    }
}


// -----------------------------------------------------------------------------
// Pagination validation
// -----------------------------------------------------------------------------

function demonstratePaginationValidation() {
    heading("16. PAGINATION VALIDATION");

    const validRequests = [
        { page: 1, pageSize: 10 },
        { page: 2, pageSize: 20 },
        { page: 5, pageSize: 25 }
    ];

    for (const request of validRequests) {
        console.log(
            request,
            "=> OFFSET",
            calculateOffset(request.page, request.pageSize)
        );
    }

    const invalidRequests = [
        { page: 0, pageSize: 10 },
        { page: 1, pageSize: 0 },
        { page: 1, pageSize: 101 }
    ];

    for (const request of invalidRequests) {
        try {
            calculateOffset(request.page, request.pageSize);
        } catch (error) {
            console.log(
                `Rejected page=${request.page}, pageSize=${request.pageSize}:`,
                error.message
            );
        }
    }
}


// -----------------------------------------------------------------------------
// SQL query examples
// -----------------------------------------------------------------------------

function demonstrateRealSQLPatterns() {
    heading("17. REAL SQL PATTERNS FOR A DATABASE DRIVER");

    const queries = {
        ascending: `
SELECT employee_name, salary
FROM employees
ORDER BY salary ASC;
        `.trim(),

        descending: `
SELECT employee_name, salary
FROM employees
ORDER BY salary DESC;
        `.trim(),

        deterministicTopFive: `
SELECT employee_id, employee_name, salary
FROM employees
ORDER BY salary DESC, employee_id ASC
LIMIT ?;
        `.trim(),

        offsetPagination: `
SELECT employee_id, employee_name, salary
FROM employees
ORDER BY salary DESC, employee_id ASC
LIMIT ? OFFSET ?;
        `.trim(),

        newestEmployees: `
SELECT employee_id, employee_name, hire_date
FROM employees
ORDER BY hire_date DESC, employee_id ASC
LIMIT ?;
        `.trim(),

        filteredTopN: `
SELECT employee_id, employee_name, salary
FROM employees
WHERE department = ?
ORDER BY salary DESC, employee_id ASC
LIMIT ?;
        `.trim()
    };

    for (const [name, query] of Object.entries(queries)) {
        subheading(name);
        console.log(query);
    }
}


// -----------------------------------------------------------------------------
// Performance concepts
// -----------------------------------------------------------------------------

function demonstratePerformanceConsiderations() {
    heading("18. PERFORMANCE CONSIDERATIONS");

    const datasetSizes = [
        100,
        10_000,
        100_000,
        1_000_000
    ];

    for (const size of datasetSizes) {
        console.log(
            `Dataset size: ${size.toLocaleString()} rows`
        );
    }

    console.log(
        `
Important principles:

1. Sorting large result sets can require significant CPU and memory.
2. An appropriate database index can sometimes provide rows in the requested
   order without a separate full sort.
3. LIMIT can reduce the amount of output, but it does not automatically mean
   the database examines only LIMIT rows.
4. Large OFFSET values can require the database to process many preceding rows.
5. Keyset pagination can avoid large offsets for sequential navigation.
6. Indexes have storage and write-maintenance costs.
7. Always inspect the actual database query plan for important production SQL.`
    );
}


// -----------------------------------------------------------------------------
// Complexity discussion
// -----------------------------------------------------------------------------

function demonstrateAlgorithmicReasoning() {
    heading("19. ALGORITHMIC REASONING");

    console.log(
        `
A generic in-memory comparison sort is commonly analyzed as approximately:

    O(n log n)

where n is the number of rows being sorted.

An OFFSET-based request conceptually asks for:

    skip k rows
    return m rows

The database may need to process a substantial portion of the first k + m
ordered rows, depending on its execution strategy.

Keyset pagination instead uses the ordering keys as a boundary, which can
work especially well with a matching index.

Actual database complexity depends on:
- indexes
- selectivity
- query predicates
- statistics
- optimizer decisions
- storage engine
- memory
- data distribution
- database implementation`
    );
}


// -----------------------------------------------------------------------------
// Edge cases
// -----------------------------------------------------------------------------

function demonstrateEdgeCases() {
    heading("20. EDGE CASES");

    const sorted = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    console.log("\nLIMIT larger than dataset:");
    printRows(limit(sorted, 1000));

    console.log("\nOFFSET beyond dataset:");
    printRows(offsetLimit(sorted, 1000, 10));

    console.log("\nLIMIT zero:");
    printRows(limit(sorted, 0));

    console.log("\nEmpty dataset:");

    const empty = [];
    printRows(
        offsetLimit(empty, 0, 10)
    );

    console.log(
        `
JavaScript's array slice naturally returns an empty array for an offset
beyond the available data. SQL databases similarly return zero rows when the
OFFSET moves beyond the result set.`
    );
}


// -----------------------------------------------------------------------------
// Testing
// -----------------------------------------------------------------------------

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}


function demonstrateTests() {
    heading("21. ORDERING TESTS");

    const ordered = sqlStyleOrderBy(employees, [
        { field: "salary", direction: "DESC" },
        { field: "employeeId", direction: "ASC" }
    ]);

    for (let index = 0; index < ordered.length - 1; index += 1) {
        const current = ordered[index];
        const next = ordered[index + 1];

        const valid =
            current.salary > next.salary ||
            (
                current.salary === next.salary &&
                current.employeeId < next.employeeId
            );

        assert(
            valid,
            "Rows are not in deterministic salary/employeeId order."
        );
    }

    assert(
        limit(ordered, 5).length === 5,
        "LIMIT behavior failed."
    );

    assert(
        offsetLimit(ordered, 5, 5).length === 5,
        "OFFSET/LIMIT behavior failed."
    );

    assert(
        offsetLimit(ordered, 1000, 5).length === 0,
        "Large OFFSET behavior failed."
    );

    console.log("All ordering tests passed.");
}


// -----------------------------------------------------------------------------
// Common mistakes
// -----------------------------------------------------------------------------

function demonstrateCommonMistakes() {
    heading("22. COMMON MISTAKES");

    console.log(
        `
Mistake 1:
    SELECT ... LIMIT 5

Problem:
    The query does not define which five rows are required.

Mistake 2:
    ORDER BY salary DESC
    LIMIT 5

when salary is not unique.

Problem:
    Equal-salary rows have no explicit tie-breaker.

Better:
    ORDER BY salary DESC, employee_id ASC
    LIMIT 5

Mistake 3:
    Building ORDER BY directly from raw HTTP query parameters.

Problem:
    SQL injection risk.

Better:
    Map known application sort names to fixed SQL identifiers.

Mistake 4:
    Allowing unlimited page sizes.

Problem:
    A client may request a huge result set and consume database, network,
    and application resources.

Better:
    Validate and cap page size.

Mistake 5:
    Using large OFFSET values for an infinite-scroll API.

Problem:
    Large offsets may become increasingly expensive.

Better:
    Consider keyset pagination when sequential navigation is appropriate.`
    );
}


// -----------------------------------------------------------------------------
// Production API example
// -----------------------------------------------------------------------------

function simulateApiRequest({
    sort = "salary",
    direction = "desc",
    page = 1,
    pageSize = 5
} = {}) {
    const sortFieldMap = {
        name: "employeeName",
        salary: "salary",
        score: "performanceScore",
        hireDate: "hireDate"
    };

    if (!sortFieldMap[sort]) {
        throw new Error("Invalid sort parameter.");
    }

    const normalizedDirection = direction.toUpperCase();

    if (!["ASC", "DESC"].includes(normalizedDirection)) {
        throw new Error("Invalid direction parameter.");
    }

    const offsetValue = calculateOffset(page, pageSize);

    const ordered = sqlStyleOrderBy(employees, [
        {
            field: sortFieldMap[sort],
            direction: normalizedDirection,
            nullsLast: true
        },
        {
            field: "employeeId",
            direction: "ASC"
        }
    ]);

    const pageRows = offsetLimit(
        ordered,
        offsetValue,
        pageSize
    );

    return {
        page,
        pageSize,
        offset: offsetValue,
        sort,
        direction: normalizedDirection,
        returnedRows: pageRows.length,
        data: pageRows
    };
}


function demonstrateApiSimulation() {
    heading("23. APPLICATION API SIMULATION");

    const response = simulateApiRequest({
        sort: "score",
        direction: "desc",
        page: 1,
        pageSize: 5
    });

    console.log(
        JSON.stringify(response, null, 2)
    );
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

function main() {
    console.log(
        `
SQL Sorting & Limiting Study Program

Core topics:
ORDER BY | ASC | DESC | LIMIT | OFFSET | deterministic ordering
pagination | NULL handling | top-N | keyset pagination | security`
    );

    demonstrateAscending();
    demonstrateDescending();
    demonstrateMultipleSortKeys();
    demonstrateDeterministicOrdering();
    demonstrateLimit();
    demonstrateOffset();
    demonstratePagination();
    demonstrateTopAndBottomN();
    demonstrateNullOrdering();
    demonstrateConditionalOrdering();
    demonstrateExpressionOrdering();
    demonstrateFilteringAndOrdering();
    demonstrateTopNPerGroup();
    demonstrateKeysetPagination();
    demonstrateSafeDynamicOrdering();
    demonstratePaginationValidation();
    demonstrateRealSQLPatterns();
    demonstratePerformanceConsiderations();
    demonstrateAlgorithmicReasoning();
    demonstrateEdgeCases();
    demonstrateTests();
    demonstrateCommonMistakes();
    demonstrateApiSimulation();

    heading("24. STUDY CHECKLIST");

    const checklist = [
        "ORDER BY defines result ordering.",
        "ASC means ascending.",
        "DESC means descending.",
        "Multiple keys create hierarchical ordering.",
        "LIMIT restricts the number of returned rows.",
        "OFFSET skips preceding rows.",
        "LIMIT without ORDER BY does not define a meaningful top-N selection.",
        "Unique tie-breakers make ordering deterministic.",
        "Stable ordering is important for pagination.",
        "Large OFFSET values can become inefficient.",
        "Keyset pagination uses ordered values as a continuation cursor.",
        "NULL placement should be explicit when it matters.",
        "Dynamic sort fields require allow-list validation.",
        "Page size should be validated and capped.",
        "Database query plans should guide performance optimization."
    ];

    checklist.forEach((item) => console.log(`[x] ${item}`));
}


main();
