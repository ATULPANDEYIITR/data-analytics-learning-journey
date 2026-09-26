"use strict";

/*
 * SQL JOINS I
 * ===========
 *
 * This JavaScript file complements the Python/SQLite implementation by
 * implementing relational join behavior directly with JavaScript arrays.
 *
 * It demonstrates:
 *   - join keys
 *   - INNER JOIN
 *   - LEFT JOIN
 *   - RIGHT JOIN
 *   - FULL OUTER JOIN
 *   - composite keys
 *   - duplicate keys
 *   - NULL/missing matches
 *   - one-to-many relationships
 *   - semi-joins and anti-joins
 *   - aggregation after joins
 *   - performance considerations
 *
 * Run with:
 *   node sql-joins.js
 *
 * The implementation intentionally uses no external packages.
 */

// ============================================================================
// 1. DATA
// ============================================================================

const departments = [
    { departmentId: 10, departmentName: "Engineering" },
    { departmentId: 20, departmentName: "Finance" },
    { departmentId: 30, departmentName: "Human Resources" },
    { departmentId: 40, departmentName: "Security" },
    { departmentId: 50, departmentName: "Research" }
];

const employees = [
    { employeeId: 1, employeeName: "Asha", departmentId: 10, managerId: null, salary: 95000 },
    { employeeId: 2, employeeName: "Ravi", departmentId: 10, managerId: 1, salary: 82000 },
    { employeeId: 3, employeeName: "Meera", departmentId: 20, managerId: 1, salary: 78000 },
    { employeeId: 4, employeeName: "Kabir", departmentId: null, managerId: 1, salary: 70000 },
    { employeeId: 5, employeeName: "Isha", departmentId: 30, managerId: 1, salary: 68000 },
    { employeeId: 6, employeeName: "Arjun", departmentId: 40, managerId: 1, salary: 88000 }
];

const projects = [
    { projectId: 101, projectName: "Cloud Migration" },
    { projectId: 102, projectName: "Fraud Detection" },
    { projectId: 103, projectName: "Security Audit" }
];

const employeeProjects = [
    { employeeId: 1, projectId: 101, role: "Architect" },
    { employeeId: 1, projectId: 103, role: "Lead" },
    { employeeId: 2, projectId: 101, role: "Developer" },
    { employeeId: 3, projectId: 102, role: "Analyst" },
    { employeeId: 6, projectId: 103, role: "Security Engineer" }
];

const regionalSales = [
    { region: "North", product: "Laptop", amount: 100000 },
    { region: "North", product: "Phone", amount: 70000 },
    { region: "South", product: "Laptop", amount: 85000 },
    { region: "West", product: "Tablet", amount: 45000 }
];

const regionalTargets = [
    { region: "North", product: "Laptop", target: 90000 },
    { region: "North", product: "Phone", target: 80000 },
    { region: "South", product: "Laptop", target: 80000 },
    { region: "East", product: "Tablet", target: 40000 }
];


// ============================================================================
// 2. OUTPUT UTILITIES
// ============================================================================

function printSection(title) {
    console.log(`\n${"=".repeat(78)}\n${title}\n${"=".repeat(78)}`);
}

function printRows(title, rows) {
    console.log(`\n${title}`);
    console.table(rows);
}


// ============================================================================
// 3. BASIC INNER JOIN
// ============================================================================

function innerJoin(leftRows, rightRows, leftKey, rightKey, combine) {
    const results = [];

    /*
     * An index avoids repeatedly scanning the entire right table.
     *
     * Without an index-like Map:
     *     O(leftRows * rightRows)
     *
     * With a hash Map:
     *     approximately O(leftRows + rightRows)
     *
     * Real SQL engines have considerably more sophisticated join
     * algorithms and optimizers, but this demonstrates the basic idea.
     */
    const index = new Map();

    for (const rightRow of rightRows) {
        const key = rightRow[rightKey];

        if (!index.has(key)) {
            index.set(key, []);
        }

        index.get(key).push(rightRow);
    }

    for (const leftRow of leftRows) {
        const matches = index.get(leftRow[leftKey]) || [];

        for (const rightRow of matches) {
            results.push(combine(leftRow, rightRow));
        }
    }

    return results;
}


// ============================================================================
// 4. LEFT JOIN
// ============================================================================

function leftJoin(leftRows, rightRows, leftKey, rightKey, combine) {
    const results = [];
    const index = new Map();

    for (const rightRow of rightRows) {
        const key = rightRow[rightKey];

        if (!index.has(key)) {
            index.set(key, []);
        }

        index.get(key).push(rightRow);
    }

    for (const leftRow of leftRows) {
        const matches = index.get(leftRow[leftKey]) || [];

        if (matches.length === 0) {
            /*
             * null represents the absent right-side relation.
             * It is important not to silently drop the left row.
             */
            results.push(combine(leftRow, null));
            continue;
        }

        for (const rightRow of matches) {
            results.push(combine(leftRow, rightRow));
        }
    }

    return results;
}


// ============================================================================
// 5. RIGHT JOIN
// ============================================================================

function rightJoin(leftRows, rightRows, leftKey, rightKey, combine) {
    /*
     * RIGHT JOIN is equivalent to reversing the tables and performing
     * a LEFT JOIN. The combiner is reversed to preserve output meaning.
     */
    return leftJoin(
        rightRows,
        leftRows,
        rightKey,
        leftKey,
        (rightRow, leftRow) => combine(leftRow, rightRow)
    );
}


// ============================================================================
// 6. FULL OUTER JOIN
// ============================================================================

function fullOuterJoin(leftRows, rightRows, leftKey, rightKey, combine) {
    const results = [];
    const rightIndex = new Map();
    const matchedRightIndexes = new Set();

    for (let index = 0; index < rightRows.length; index += 1) {
        const rightRow = rightRows[index];
        const key = rightRow[rightKey];

        if (!rightIndex.has(key)) {
            rightIndex.set(key, []);
        }

        rightIndex.get(key).push({ index, row: rightRow });
    }

    for (const leftRow of leftRows) {
        const matches = rightIndex.get(leftRow[leftKey]) || [];

        if (matches.length === 0) {
            results.push(combine(leftRow, null));
            continue;
        }

        for (const match of matches) {
            matchedRightIndexes.add(match.index);
            results.push(combine(leftRow, match.row));
        }
    }

    /*
     * Every right row that was never matched must still appear in a
     * FULL OUTER JOIN result.
     */
    for (let index = 0; index < rightRows.length; index += 1) {
        if (!matchedRightIndexes.has(index)) {
            results.push(combine(null, rightRows[index]));
        }
    }

    return results;
}


// ============================================================================
// 7. BASIC JOIN EXAMPLES
// ============================================================================

function demonstrateBasicJoins() {
    printSection("1. INNER JOIN");

    const innerResults = innerJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            departmentName: department.departmentName
        })
    );

    printRows("Employees with matching departments", innerResults);

    printSection("2. LEFT JOIN");

    const leftResults = leftJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({
            employeeName: employee.employeeName,
            departmentName: department ? department.departmentName : null
        })
    );

    printRows("Every employee, including employees without departments", leftResults);

    printSection("3. RIGHT JOIN");

    const rightResults = rightJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({
            employeeName: employee ? employee.employeeName : null,
            departmentName: department.departmentName
        })
    );

    printRows("Every department, including departments without employees", rightResults);

    printSection("4. FULL OUTER JOIN");

    const fullResults = fullOuterJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({
            employeeName: employee ? employee.employeeName : null,
            departmentName: department ? department.departmentName : null
        })
    );

    printRows("Matched and unmatched rows from both relations", fullResults);
}


// ============================================================================
// 8. COMPOSITE KEYS
// ============================================================================

function makeCompositeKey(row, columns) {
    /*
     * JSON.stringify provides an unambiguous representation for the
     * small scalar values used here.
     */
    return JSON.stringify(columns.map(column => row[column]));
}

function compositeInnerJoin(leftRows, rightRows, columns, combine) {
    const index = new Map();

    for (const rightRow of rightRows) {
        const key = makeCompositeKey(rightRow, columns);

        if (!index.has(key)) {
            index.set(key, []);
        }

        index.get(key).push(rightRow);
    }

    const results = [];

    for (const leftRow of leftRows) {
        const key = makeCompositeKey(leftRow, columns);
        const matches = index.get(key) || [];

        for (const rightRow of matches) {
            results.push(combine(leftRow, rightRow));
        }
    }

    return results;
}

function demonstrateCompositeKeys() {
    printSection("5. COMPOSITE JOIN KEYS");

    const results = compositeInnerJoin(
        regionalSales,
        regionalTargets,
        ["region", "product"],
        (sale, target) => ({
            region: sale.region,
            product: sale.product,
            amount: sale.amount,
            target: target.target,
            variance: sale.amount - target.target
        })
    );

    printRows("Sales matched to targets using region + product", results);
}


// ============================================================================
// 9. ONE-TO-MANY AND MANY-TO-MANY
// ============================================================================

function demonstrateRelationshipCardinality() {
    printSection("6. ONE-TO-MANY RELATIONSHIP");

    const departmentEmployees = leftJoin(
        departments,
        employees,
        "departmentId",
        "departmentId",
        (department, employee) => ({
            department: department.departmentName,
            employee: employee ? employee.employeeName : null
        })
    );

    printRows("Department to employee relationship", departmentEmployees);

    printSection("7. MANY-TO-MANY RELATIONSHIP");

    const employeeToProject = innerJoin(
        employees,
        employeeProjects,
        "employeeId",
        "employeeId",
        (employee, assignment) => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName,
            projectId: assignment.projectId,
            role: assignment.role
        })
    );

    const completeProjectData = innerJoin(
        employeeToProject,
        projects,
        "projectId",
        "projectId",
        (assignment, project) => ({
            employeeName: assignment.employeeName,
            projectName: project.projectName,
            role: assignment.role
        })
    );

    printRows("Employees assigned to projects", completeProjectData);
}


// ============================================================================
// 10. NULL AND UNMATCHED RECORDS
// ============================================================================

function demonstrateUnmatchedRecords() {
    printSection("8. FINDING UNMATCHED LEFT-SIDE RECORDS");

    const unmatchedEmployees = leftJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({
            employeeName: employee.employeeName,
            departmentId: employee.departmentId,
            hasDepartment: department !== null
        })
    ).filter(row => !row.hasDepartment);

    printRows("Employees without a matching department", unmatchedEmployees);

    printSection("9. FINDING UNMATCHED RIGHT-SIDE RECORDS");

    const unmatchedDepartments = rightJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({
            employeeName: employee ? employee.employeeName : null,
            departmentName: department.departmentName,
            hasEmployee: employee !== null
        })
    ).filter(row => !row.hasEmployee);

    printRows("Departments without employees", unmatchedDepartments);
}


// ============================================================================
// 11. SEMI-JOIN AND ANTI-JOIN
// ============================================================================

function demonstrateSemiAndAntiJoins() {
    printSection("10. SEMI-JOIN");

    const projectEmployeeIds = new Set(
        employeeProjects.map(assignment => assignment.employeeId)
    );

    const employeesWithProjects = employees.filter(
        employee => projectEmployeeIds.has(employee.employeeId)
    );

    printRows(
        "Employees having at least one project",
        employeesWithProjects.map(employee => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName
        }))
    );

    printSection("11. ANTI-JOIN");

    const employeesWithoutProjects = employees.filter(
        employee => !projectEmployeeIds.has(employee.employeeId)
    );

    printRows(
        "Employees having no projects",
        employeesWithoutProjects.map(employee => ({
            employeeId: employee.employeeId,
            employeeName: employee.employeeName
        }))
    );
}


// ============================================================================
// 12. SELF JOIN
// ============================================================================

function demonstrateSelfJoin() {
    printSection("12. SELF JOIN");

    const managerIndex = new Map(
        employees.map(employee => [employee.employeeId, employee])
    );

    const reportingStructure = employees.map(employee => {
        const manager = employee.managerId === null
            ? null
            : managerIndex.get(employee.managerId) || null;

        return {
            employee: employee.employeeName,
            manager: manager ? manager.employeeName : null
        };
    });

    printRows("Employee-manager hierarchy", reportingStructure);
}


// ============================================================================
// 13. AGGREGATION AFTER JOIN
// ============================================================================

function demonstrateAggregation() {
    printSection("13. AGGREGATION AFTER LEFT JOIN");

    const joined = leftJoin(
        departments,
        employees,
        "departmentId",
        "departmentId",
        (department, employee) => ({
            departmentId: department.departmentId,
            departmentName: department.departmentName,
            employee
        })
    );

    const grouped = new Map();

    for (const row of joined) {
        if (!grouped.has(row.departmentId)) {
            grouped.set(row.departmentId, {
                departmentId: row.departmentId,
                departmentName: row.departmentName,
                employeeCount: 0,
                totalSalary: 0
            });
        }

        const group = grouped.get(row.departmentId);

        /*
         * Count only real employee rows.
         * A LEFT JOIN creates null for the absent employee.
         */
        if (row.employee !== null) {
            group.employeeCount += 1;
            group.totalSalary += row.employee.salary;
        }
    }

    const result = [...grouped.values()].map(group => ({
        departmentId: group.departmentId,
        departmentName: group.departmentName,
        employeeCount: group.employeeCount,
        averageSalary: group.employeeCount === 0
            ? 0
            : group.totalSalary / group.employeeCount
    }));

    printRows("Department statistics", result);
}


// ============================================================================
// 14. JOIN WITH BUSINESS CONDITIONS
// ============================================================================

function demonstrateJoinCondition() {
    printSection("14. JOIN WITH ADDITIONAL BUSINESS CONDITION");

    const results = compositeInnerJoin(
        regionalSales,
        regionalTargets,
        ["region", "product"],
        (sale, target) => ({
            region: sale.region,
            product: sale.product,
            amount: sale.amount,
            target: target.target,
            status: sale.amount >= target.target ? "TARGET_MET" : "BELOW_TARGET"
        })
    );

    printRows("Sales performance", results);
}


// ============================================================================
// 15. DUPLICATE JOIN KEYS
// ============================================================================

function demonstrateDuplicateKeys() {
    printSection("15. DUPLICATE JOIN KEYS");

    const aliases = [
        { employeeId: 1, alias: "Asha P." },
        { employeeId: 1, alias: "Architect Asha" },
        { employeeId: 2, alias: "Ravi K." }
    ];

    const results = innerJoin(
        employees.filter(employee => employee.employeeId <= 2),
        aliases,
        "employeeId",
        "employeeId",
        (employee, alias) => ({
            employee: employee.employeeName,
            alias: alias.alias
        })
    );

    printRows(
        "One employee can produce multiple rows when the right key is duplicated",
        results
    );

    console.log(
        "\nImportant: duplicated output is a property of the relationship, " +
        "not automatically a join error."
    );
}


// ============================================================================
// 16. JOIN VALIDATION
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Validation failed: ${message}`);
    }
}

function runValidation() {
    printSection("16. AUTOMATED VALIDATION");

    const innerResults = innerJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({ employee, department })
    );

    const leftResults = leftJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({ employee, department })
    );

    const fullResults = fullOuterJoin(
        employees,
        departments,
        "departmentId",
        "departmentId",
        (employee, department) => ({ employee, department })
    );

    assert(innerResults.length === 5, "INNER JOIN should contain five matches.");
    assert(leftResults.length === 6, "LEFT JOIN should preserve six employees.");
    assert(fullResults.length === 7, "FULL OUTER JOIN should contain seven rows.");

    console.log("All JavaScript join validations passed.");
}


// ============================================================================
// 17. PERFORMANCE DEMONSTRATION
// ============================================================================

function benchmarkIndexedJoin() {
    printSection("17. PERFORMANCE CONSIDERATIONS");

    const largeLeft = Array.from({ length: 10000 }, (_, index) => ({
        id: index,
        value: index * 2
    }));

    const largeRight = Array.from({ length: 10000 }, (_, index) => ({
        id: index,
        description: `Record ${index}`
    }));

    const start = performance.now();

    const results = innerJoin(
        largeLeft,
        largeRight,
        "id",
        "id",
        (left, right) => ({
            id: left.id,
            value: left.value,
            description: right.description
        })
    );

    const elapsed = performance.now() - start;

    console.log(`Joined rows: ${results.length}`);
    console.log(`Indexed hash-style join time: ${elapsed.toFixed(2)} ms`);

    console.log(
        "The Map-based implementation avoids a full right-table scan " +
        "for every left row."
    );
}


// ============================================================================
// 18. CONCEPTUAL RULES
// ============================================================================

function printRules() {
    printSection("18. CORE SQL JOIN RULES");

    const rules = [
        "INNER JOIN: only matching rows.",
        "LEFT JOIN: all left rows plus matching right rows.",
        "RIGHT JOIN: all right rows plus matching left rows.",
        "FULL OUTER JOIN: all rows from both sides.",
        "Join keys define row correspondence.",
        "Foreign keys commonly reference primary keys.",
        "A non-unique join key can multiply result rows.",
        "NULL does not compare equal to NULL with ordinary equality.",
        "Use IS NULL and IS NOT NULL for NULL checks.",
        "A WHERE condition can remove NULL-extended rows from an outer join.",
        "Composite keys require all relevant key columns in the predicate.",
        "Indexes can improve join performance but consume storage and write cost.",
        "Always determine the intended result grain before writing a join.",
        "Use parameterized SQL when values originate outside trusted code."
    ];

    rules.forEach((rule, index) => {
        console.log(`${index + 1}. ${rule}`);
    });
}


// ============================================================================
// 19. MAIN
// ============================================================================

function main() {
    demonstrateBasicJoins();
    demonstrateCompositeKeys();
    demonstrateRelationshipCardinality();
    demonstrateUnmatchedRecords();
    demonstrateSemiAndAntiJoins();
    demonstrateSelfJoin();
    demonstrateAggregation();
    demonstrateJoinCondition();
    demonstrateDuplicateKeys();
    runValidation();
    benchmarkIndexedJoin();
    printRules();

    printSection("STUDY FILE COMPLETED");
}

main();
