/*
 * SQL Filtering: WHERE, comparison operators, AND, OR, NOT, IN, BETWEEN,
 * LIKE, IS NULL
 *
 * This file demonstrates SQL filtering from beginner concepts through
 * application-level patterns using JavaScript and an in-memory SQL-like
 * filtering model.
 *
 * It intentionally uses plain JavaScript so that it runs without npm packages.
 * The functions mirror the semantics of the SQL predicates being studied.
 *
 * Run:
 *     node sql_filtering.js
 */

"use strict";


// ---------------------------------------------------------------------------
// 1. SAMPLE DATA
// ---------------------------------------------------------------------------

const employees = [
    {
        id: 1,
        name: "Aarav Sharma",
        department: "Engineering",
        salary: 145000,
        age: 42,
        city: "Bengaluru",
        email: "aarav@example.com",
        active: true,
    },
    {
        id: 2,
        name: "Priya Singh",
        department: "Engineering",
        salary: 118000,
        age: 34,
        city: "Lucknow",
        email: "priya@example.com",
        active: true,
    },
    {
        id: 3,
        name: "Rahul Verma",
        department: "Engineering",
        salary: 92000,
        age: 28,
        city: "Delhi",
        email: "rahul@example.com",
        active: true,
    },
    {
        id: 4,
        name: "Neha Gupta",
        department: "Finance",
        salary: 87000,
        age: 31,
        city: "Mumbai",
        email: "neha@example.com",
        active: true,
    },
    {
        id: 5,
        name: "Vikram Rao",
        department: "Finance",
        salary: 71000,
        age: 39,
        city: "Pune",
        email: null,
        active: true,
    },
    {
        id: 6,
        name: "Ananya Mehta",
        department: "Human Resources",
        salary: 68000,
        age: 29,
        city: "Delhi",
        email: "ananya@example.com",
        active: true,
    },
    {
        id: 7,
        name: "Karan Malhotra",
        department: "Finance",
        salary: 130000,
        age: 45,
        city: "Mumbai",
        email: "karan@example.com",
        active: true,
    },
    {
        id: 8,
        name: "Ishita Kapoor",
        department: "Sales",
        salary: 76000,
        age: 27,
        city: "Lucknow",
        email: "ishita@example.com",
        active: true,
    },
    {
        id: 9,
        name: "Dev Patel",
        department: "Sales",
        salary: 73000,
        age: 30,
        city: "Ahmedabad",
        email: "dev@example.com",
        active: true,
    },
    {
        id: 10,
        name: "Riya Nair",
        department: "Sales",
        salary: 110000,
        age: 38,
        city: "Kochi",
        email: "riya@example.com",
        active: true,
    },
    {
        id: 11,
        name: "Arjun Das",
        department: "Security",
        salary: 105000,
        age: 33,
        city: "Hyderabad",
        email: "arjun@example.com",
        active: true,
    },
    {
        id: 12,
        name: "Meera Joshi",
        department: "Security",
        salary: 138000,
        age: 41,
        city: "Pune",
        email: "meera@example.com",
        active: true,
    },
    {
        id: 13,
        name: "Kabir Khan",
        department: "Engineering",
        salary: 35000,
        age: 21,
        city: "Jaipur",
        email: "kabir@example.com",
        active: false,
    },
    {
        id: 14,
        name: "Sara Ali",
        department: null,
        salary: 98000,
        age: 36,
        city: null,
        email: "sara@example.com",
        active: true,
    },
];


// ---------------------------------------------------------------------------
// 2. DISPLAY HELPERS
// ---------------------------------------------------------------------------

function printRows(rows, title = "") {
    if (title) {
        console.log(`\n--- ${title} ---`);
    }

    if (rows.length === 0) {
        console.log("(no rows)");
        return;
    }

    console.table(rows);
}

function printExpression(title, value) {
    console.log(`${title}: ${value}`);
}


// ---------------------------------------------------------------------------
// 3. BASIC WHERE EQUIVALENT
// ---------------------------------------------------------------------------

function demonstrateWhere() {
    /*
     * SQL:
     *
     * SELECT *
     * FROM employees
     * WHERE salary > 100000;
     *
     * In JavaScript's array-processing model, Array.prototype.filter()
     * expresses the same row-selection idea.
     */
    const highEarners = employees.filter(employee => employee.salary > 100000);

    printRows(
        highEarners,
        "WHERE salary > 100000"
    );
}


// ---------------------------------------------------------------------------
// 4. COMPARISON OPERATORS
// ---------------------------------------------------------------------------

function demonstrateComparisons() {
    /*
     * SQL uses:
     *     =, <>, !=, >, <, >=, <=
     *
     * JavaScript has:
     *     ===, !==, >, <, >=, <=
     *
     * Strict equality (===) is preferred in JavaScript because it does not
     * perform implicit type conversion.
     */

    const equalSalary = employees.filter(
        employee => employee.salary === 98000
    );

    const notEqualSalary = employees.filter(
        employee => employee.salary !== 98000
    );

    const olderThan40 = employees.filter(
        employee => employee.age > 40
    );

    const youngerThan30 = employees.filter(
        employee => employee.age < 30
    );

    const salaryAtLeast100k = employees.filter(
        employee => employee.salary >= 100000
    );

    const salaryAtMost70000 = employees.filter(
        employee => employee.salary <= 70000
    );

    printRows(equalSalary, "Equality");
    printRows(notEqualSalary, "Not equal");
    printRows(olderThan40, "Greater than");
    printRows(youngerThan30, "Less than");
    printRows(salaryAtLeast100k, "Greater than or equal to");
    printRows(salaryAtMost70000, "Less than or equal to");
}


// ---------------------------------------------------------------------------
// 5. AND
// ---------------------------------------------------------------------------

function demonstrateAnd() {
    /*
     * SQL:
     *     WHERE salary >= 80000 AND age < 40
     *
     * JavaScript:
     *     employee.salary >= 80000 && employee.age < 40
     */
    const result = employees.filter(
        employee =>
            employee.salary >= 80000 &&
            employee.age < 40
    );

    printRows(result, "AND: salary >= 80000 AND age < 40");
}


// ---------------------------------------------------------------------------
// 6. OR
// ---------------------------------------------------------------------------

function demonstrateOr() {
    /*
     * SQL OR corresponds to JavaScript's ||.
     */
    const result = employees.filter(
        employee =>
            employee.city === "Lucknow" ||
            employee.city === "Mumbai"
    );

    printRows(result, "OR: Lucknow or Mumbai");

    /*
     * Parentheses make the business rule explicit:
     *
     * (Engineering OR Security) AND salary >= 100000
     */
    const groupedResult = employees.filter(
        employee =>
            (
                employee.department === "Engineering" ||
                employee.department === "Security"
            ) &&
            employee.salary >= 100000
    );

    printRows(
        groupedResult,
        "(Engineering OR Security) AND salary >= 100000"
    );
}


// ---------------------------------------------------------------------------
// 7. NOT
// ---------------------------------------------------------------------------

function demonstrateNot() {
    /*
     * SQL:
     *     WHERE NOT city = 'Delhi'
     *
     * JavaScript:
     *     !(employee.city === "Delhi")
     */
    const result = employees.filter(
        employee => !(employee.city === "Delhi")
    );

    printRows(result, "NOT city = Delhi");
}


// ---------------------------------------------------------------------------
// 8. IN
// ---------------------------------------------------------------------------

function demonstrateIn() {
    /*
     * SQL:
     *     WHERE city IN ('Delhi', 'Mumbai', 'Lucknow')
     *
     * JavaScript's Set provides a natural membership test.
     */
    const allowedCities = new Set([
        "Delhi",
        "Mumbai",
        "Lucknow",
    ]);

    const result = employees.filter(
        employee => allowedCities.has(employee.city)
    );

    printRows(result, "IN: Delhi, Mumbai, Lucknow");

    /*
     * NOT IN:
     */
    const excludedCities = new Set([
        "Delhi",
        "Mumbai",
    ]);

    const notInResult = employees.filter(
        employee => !excludedCities.has(employee.city)
    );

    printRows(notInResult, "NOT IN: excluding Delhi and Mumbai");
}


// ---------------------------------------------------------------------------
// 9. BETWEEN
// ---------------------------------------------------------------------------

function between(value, lower, upper) {
    /*
     * SQL BETWEEN is inclusive:
     *
     * value BETWEEN lower AND upper
     *
     * is equivalent to:
     *
     * value >= lower AND value <= upper
     */
    return value >= lower && value <= upper;
}

function demonstrateBetween() {
    const result = employees.filter(
        employee => between(employee.salary, 80000, 100000)
    );

    printRows(
        result,
        "BETWEEN 80000 AND 100000, inclusive"
    );

    /*
     * JavaScript Date objects can also be compared numerically by their
     * underlying millisecond timestamps.
     */
    const orders = [
        { id: 1001, date: "2026-01-05", total: 120000 },
        { id: 1002, date: "2026-01-11", total: 5400 },
        { id: 1003, date: "2026-02-14", total: 9000 },
        { id: 1004, date: "2026-02-20", total: 32000 },
        { id: 1005, date: "2026-03-02", total: 13000 },
        { id: 1006, date: "2026-03-15", total: 85000 },
        { id: 1007, date: "2026-04-01", total: 37000 },
    ];

    const start = new Date("2026-02-01T00:00:00Z");
    const end = new Date("2026-03-31T23:59:59.999Z");

    const dateResult = orders.filter(order => {
        const date = new Date(`${order.date}T00:00:00Z`);
        return date >= start && date <= end;
    });

    printRows(
        dateResult,
        "Orders between February 1 and March 31"
    );
}


// ---------------------------------------------------------------------------
// 10. LIKE
// ---------------------------------------------------------------------------

function sqlLike(value, pattern) {
    /*
     * This helper implements the two most important SQL LIKE wildcards:
     *
     *     % -> zero or more characters
     *     _ -> exactly one character
     *
     * The conversion is intentionally explicit so that the SQL pattern
     * semantics can be studied without an external library.
     */
    if (value === null || value === undefined) {
        return false;
    }

    let regularExpression = "^";

    for (let index = 0; index < pattern.length; index += 1) {
        const character = pattern[index];

        if (character === "%") {
            regularExpression += ".*";
        } else if (character === "_") {
            regularExpression += ".";
        } else {
            regularExpression += character.replace(
                /[.*+?^${}()|[\]\\]/g,
                "\\$&"
            );
        }
    }

    regularExpression += "$";

    return new RegExp(regularExpression, "i").test(String(value));
}

function demonstrateLike() {
    const startsWithA = employees.filter(
        employee => sqlLike(employee.name, "A%")
    );

    const containsAr = employees.filter(
        employee => sqlLike(employee.name, "%ar%")
    );

    const secondCharacterE = employees.filter(
        employee => sqlLike(employee.name, "_e%")
    );

    printRows(startsWithA, "LIKE 'A%'");
    printRows(containsAr, "LIKE '%ar%'");
    printRows(secondCharacterE, "LIKE '_e%'");
}


// ---------------------------------------------------------------------------
// 11. IS NULL
// ---------------------------------------------------------------------------

function demonstrateNull() {
    /*
     * SQL:
     *     WHERE email IS NULL
     *
     * JavaScript:
     *     employee.email === null
     *
     * JavaScript also has undefined, which is distinct from null. A database
     * NULL normally maps to null when application code explicitly represents
     * the database value.
     */
    const missingEmail = employees.filter(
        employee => employee.email === null
    );

    const availableEmail = employees.filter(
        employee => employee.email !== null
    );

    printRows(missingEmail, "IS NULL");
    printRows(availableEmail, "IS NOT NULL");

    /*
     * This is deliberately not presented as a SQL equivalent:
     *
     * employee.email === null
     *
     * is JavaScript equality against null, while SQL requires IS NULL because
     * SQL NULL participates in three-valued logic.
     */
}


// ---------------------------------------------------------------------------
// 12. THREE-VALUED LOGIC
// ---------------------------------------------------------------------------

function sqlEquals(left, right) {
    /*
     * A simplified SQL-style equality operation.
     *
     * null compared to anything with normal equality is UNKNOWN.
     */
    if (left === null || right === null) {
        return null;
    }

    return left === right;
}

function sqlNot(value) {
    if (value === null) {
        return null;
    }

    return !value;
}

function sqlAnd(left, right) {
    /*
     * SQL AND truth table:
     *
     * TRUE AND TRUE       = TRUE
     * TRUE AND FALSE      = FALSE
     * TRUE AND UNKNOWN    = UNKNOWN
     * FALSE AND UNKNOWN   = FALSE
     * UNKNOWN AND UNKNOWN = UNKNOWN
     */
    if (left === false || right === false) {
        return false;
    }

    if (left === null || right === null) {
        return null;
    }

    return true;
}

function sqlOr(left, right) {
    /*
     * SQL OR truth table:
     *
     * TRUE OR anything     = TRUE
     * FALSE OR FALSE       = FALSE
     * FALSE OR UNKNOWN     = UNKNOWN
     * UNKNOWN OR UNKNOWN   = UNKNOWN
     */
    if (left === true || right === true) {
        return true;
    }

    if (left === null || right === null) {
        return null;
    }

    return false;
}

function demonstrateThreeValuedLogic() {
    printExpression(
        "SQL NULL = 5",
        sqlEquals(null, 5)
    );

    printExpression(
        "SQL NULL = NULL",
        sqlEquals(null, null)
    );

    printExpression(
        "TRUE AND UNKNOWN",
        sqlAnd(true, null)
    );

    printExpression(
        "FALSE AND UNKNOWN",
        sqlAnd(false, null)
    );

    printExpression(
        "TRUE OR UNKNOWN",
        sqlOr(true, null)
    );

    printExpression(
        "FALSE OR UNKNOWN",
        sqlOr(false, null)
    );

    printExpression(
        "NOT UNKNOWN",
        sqlNot(null)
    );
}


// ---------------------------------------------------------------------------
// 13. FILTER COMPOSITION
// ---------------------------------------------------------------------------

function demonstrateComplexFilter() {
    /*
     * Complex SQL:
     *
     * WHERE active = 1
     *   AND department IN ('Engineering', 'Security')
     *   AND salary BETWEEN 90000 AND 140000
     *   AND email IS NOT NULL
     *
     * The JavaScript version uses small predicates composed with &&.
     */
    const departments = new Set([
        "Engineering",
        "Security",
    ]);

    const result = employees.filter(employee =>
        employee.active === true &&
        departments.has(employee.department) &&
        between(employee.salary, 90000, 140000) &&
        employee.email !== null
    );

    printRows(
        result,
        "Complex multi-condition filter"
    );
}


// ---------------------------------------------------------------------------
// 14. REUSABLE PREDICATES
// ---------------------------------------------------------------------------

const predicates = {
    active(employee) {
        return employee.active === true;
    },

    salaryAtLeast(amount) {
        return employee => employee.salary >= amount;
    },

    salaryBetween(lower, upper) {
        return employee => between(employee.salary, lower, upper);
    },

    departmentIn(names) {
        const allowed = new Set(names);
        return employee => allowed.has(employee.department);
    },

    cityIn(cities) {
        const allowed = new Set(cities);
        return employee => allowed.has(employee.city);
    },

    hasEmail(employee) {
        return employee.email !== null;
    },
};

function demonstrateReusablePredicates() {
    const result = employees.filter(
        predicates.active
    ).filter(
        predicates.salaryBetween(70000, 140000)
    ).filter(
        predicates.departmentIn(["Engineering", "Security", "Finance"])
    ).filter(
        predicates.hasEmail
    );

    printRows(
        result,
        "Reusable predicate pipeline"
    );
}


// ---------------------------------------------------------------------------
// 15. OPTIONAL FILTER OBJECT
// ---------------------------------------------------------------------------

function searchEmployees({
    minimumSalary = null,
    maximumSalary = null,
    cities = null,
    departments = null,
    activeOnly = false,
    namePattern = null,
    requireEmail = false,
} = {}) {
    /*
     * This models an application search screen where users may supply any
     * combination of filters.
     */
    const citySet = cities ? new Set(cities) : null;
    const departmentSet = departments ? new Set(departments) : null;

    return employees.filter(employee => {
        if (
            minimumSalary !== null &&
            employee.salary < minimumSalary
        ) {
            return false;
        }

        if (
            maximumSalary !== null &&
            employee.salary > maximumSalary
        ) {
            return false;
        }

        if (
            citySet !== null &&
            !citySet.has(employee.city)
        ) {
            return false;
        }

        if (
            departmentSet !== null &&
            !departmentSet.has(employee.department)
        ) {
            return false;
        }

        if (
            activeOnly &&
            employee.active !== true
        ) {
            return false;
        }

        if (
            namePattern !== null &&
            !sqlLike(employee.name, namePattern)
        ) {
            return false;
        }

        if (
            requireEmail &&
            employee.email === null
        ) {
            return false;
        }

        return true;
    });
}

function demonstrateOptionalSearch() {
    const result = searchEmployees({
        minimumSalary: 70000,
        maximumSalary: 140000,
        cities: ["Lucknow", "Delhi", "Pune", "Hyderabad"],
        activeOnly: true,
        namePattern: "%a%",
        requireEmail: true,
    });

    printRows(
        result,
        "Optional application filters"
    );
}


// ---------------------------------------------------------------------------
// 16. SHORT-CIRCUITING AND PREDICATE ORDER
// ---------------------------------------------------------------------------

function demonstrateShortCircuiting() {
    /*
     * JavaScript && and || short-circuit.
     *
     * The same logical idea is important when thinking about SQL, although
     * database optimizers are free to reorder predicates for execution.
     *
     * Do not rely on SQL textual predicate order for correctness or side
     * effects. SQL expressions should be written so every predicate is valid
     * independently of execution order.
     */
    let expensiveChecks = 0;

    const result = employees.filter(employee => {
        if (!employee.active) {
            return false;
        }

        expensiveChecks += 1;
        return employee.salary >= 100000;
    });

    printRows(
        result,
        "Predicate short-circuiting in JavaScript"
    );

    printExpression(
        "Expensive checks performed",
        expensiveChecks
    );
}


// ---------------------------------------------------------------------------
// 17. EDGE CASES
// ---------------------------------------------------------------------------

function demonstrateEdgeCases() {
    /*
     * BETWEEN includes both endpoints.
     */
    const exactBoundary = between(100000, 100000, 100000);

    /*
     * null does not behave like an ordinary number.
     */
    const nullComparison = sqlEquals(null, 100000);

    /*
     * An empty membership set means no values are members.
     */
    const emptySet = new Set();
    const emptyMembershipResult = employees.filter(
        employee => emptySet.has(employee.city)
    );

    printExpression(
        "100000 BETWEEN 100000 AND 100000",
        exactBoundary
    );

    printExpression(
        "SQL-style NULL = 100000",
        nullComparison
    );

    printRows(
        emptyMembershipResult,
        "Membership in an empty set"
    );
}


// ---------------------------------------------------------------------------
// 18. DATE FILTERING
// ---------------------------------------------------------------------------

function demonstrateDateFiltering() {
    const orders = [
        { id: 1001, date: "2026-01-05", status: "Shipped" },
        { id: 1002, date: "2026-01-11", status: "Delivered" },
        { id: 1003, date: "2026-02-14", status: "Pending" },
        { id: 1004, date: "2026-02-20", status: "Delivered" },
        { id: 1005, date: "2026-03-02", status: "Cancelled" },
        { id: 1006, date: "2026-03-15", status: "Shipped" },
        { id: 1007, date: "2026-04-01", status: "Delivered" },
    ];

    /*
     * ISO YYYY-MM-DD strings have a useful property: lexicographical order
     * corresponds to chronological order when the representation is complete
     * and consistently formatted.
     *
     * A half-open interval [start, end) is convenient for date/time ranges.
     */
    const start = "2026-03-01";
    const end = "2026-04-01";

    const marchOrders = orders.filter(
        order => order.date >= start && order.date < end
    );

    printRows(
        marchOrders,
        "Half-open date filter for March"
    );
}


// ---------------------------------------------------------------------------
// 19. FILTERING AND TRANSFORMATION
// ---------------------------------------------------------------------------

function demonstrateFilterAndMap() {
    /*
     * SQL often performs filtering and projection:
     *
     * SELECT employee_name, salary
     * FROM employees
     * WHERE salary >= 100000;
     *
     * JavaScript can express this with filter() followed by map().
     */
    const result = employees
        .filter(employee => employee.salary >= 100000)
        .map(employee => ({
            name: employee.name,
            salary: employee.salary,
        }));

    printRows(
        result,
        "Filter followed by projection"
    );
}


// ---------------------------------------------------------------------------
// 20. SQL-LIKE SECURITY PRINCIPLE
// ---------------------------------------------------------------------------

function demonstrateParameterizedQueryConcept() {
    /*
     * JavaScript database drivers normally support parameterized SQL:
     *
     *     connection.execute(
     *         "SELECT * FROM employees WHERE city = ?",
     *         [userCity]
     *     );
     *
     * This file does not connect to a database, so the example is represented
     * as data rather than executed SQL.
     */
    const userCity = "' OR 1=1 --";

    const parameterizedQuery = {
        sql: "SELECT * FROM employees WHERE city = ?",
        parameters: [userCity],
    };

    console.log("\n--- Parameterized query concept ---");
    console.log(parameterizedQuery);
}


// ---------------------------------------------------------------------------
// 21. TESTS
// ---------------------------------------------------------------------------

function runTests() {
    const highEarners = employees.filter(
        employee => employee.salary > 100000
    );

    console.assert(
        highEarners.every(employee => employee.salary > 100000),
        "Every high earner must satisfy salary > 100000"
    );

    const missingEmails = employees.filter(
        employee => employee.email === null
    );

    console.assert(
        missingEmails.every(employee => employee.email === null),
        "Every missing-email row must contain null"
    );

    console.assert(
        between(80000, 80000, 100000) === true,
        "BETWEEN lower boundary must be inclusive"
    );

    console.assert(
        between(100000, 80000, 100000) === true,
        "BETWEEN upper boundary must be inclusive"
    );

    console.assert(
        between(100001, 80000, 100000) === false,
        "Value above BETWEEN range must fail"
    );

    console.assert(
        sqlEquals(null, 5) === null,
        "SQL-style NULL equality should produce UNKNOWN"
    );

    console.log("\n--- Tests ---");
    console.log("All filtering assertions passed.");
}


// ---------------------------------------------------------------------------
// 22. MAIN
// ---------------------------------------------------------------------------

function main() {
    console.log("=".repeat(78));
    console.log("SQL FILTERING: JAVASCRIPT STUDY PROGRAM");
    console.log("=".repeat(78));

    demonstrateWhere();
    demonstrateComparisons();
    demonstrateAnd();
    demonstrateOr();
    demonstrateNot();
    demonstrateIn();
    demonstrateBetween();
    demonstrateLike();
    demonstrateNull();
    demonstrateThreeValuedLogic();
    demonstrateComplexFilter();
    demonstrateReusablePredicates();
    demonstrateOptionalSearch();
    demonstrateShortCircuiting();
    demonstrateEdgeCases();
    demonstrateDateFiltering();
    demonstrateFilterAndMap();
    demonstrateParameterizedQueryConcept();
    runTests();

    console.log("\n" + "=".repeat(78));
    console.log("ALL JAVASCRIPT LESSONS COMPLETED");
    console.log("=".repeat(78));
}

main();
