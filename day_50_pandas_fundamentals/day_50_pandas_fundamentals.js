"use strict";

/*
 * A lightweight JavaScript model of Pandas-style tabular operations.
 * It intentionally uses native arrays and objects so the implementation
 * remains executable with Node.js without external packages.
 */

class DataFrame {
    constructor(rows) {
        if (!Array.isArray(rows) || rows.length === 0) {
            throw new TypeError("DataFrame requires a non-empty array of rows.");
        }

        this.rows = rows.map((row) => ({ ...row }));

        const columns = Object.keys(this.rows[0]);
        if (columns.length === 0) {
            throw new TypeError("Rows must contain at least one column.");
        }

        for (const row of this.rows) {
            if (typeof row !== "object" || row === null) {
                throw new TypeError("Every row must be an object.");
            }

            for (const column of columns) {
                if (!(column in row)) {
                    throw new TypeError(`Missing column: ${column}`);
                }
            }
        }

        this.columns = columns;
    }

    select(...columns) {
        if (columns.length === 0) {
            throw new Error("At least one column must be selected.");
        }

        for (const column of columns) {
            if (!this.columns.includes(column)) {
                throw new Error(`Unknown column: ${column}`);
            }
        }

        return new DataFrame(
            this.rows.map((row) => {
                const selected = {};
                for (const column of columns) {
                    selected[column] = row[column];
                }
                return selected;
            })
        );
    }

    filter(predicate) {
        if (typeof predicate !== "function") {
            throw new TypeError("filter requires a predicate function.");
        }

        return new DataFrame(this.rows.filter(predicate));
    }

    assign(column, valueFunction) {
        if (!column || typeof valueFunction !== "function") {
            throw new TypeError("assign requires a column and function.");
        }

        return new DataFrame(
            this.rows.map((row, index) => ({
                ...row,
                [column]: valueFunction(row, index),
            }))
        );
    }

    sortBy(column, descending = false) {
        if (!this.columns.includes(column)) {
            throw new Error(`Unknown column: ${column}`);
        }

        const sorted = [...this.rows].sort((a, b) => {
            if (a[column] === b[column]) return 0;
            if (a[column] === null || a[column] === undefined) return 1;
            if (b[column] === null || b[column] === undefined) return -1;

            const result = a[column] < b[column] ? -1 : 1;
            return descending ? -result : result;
        });

        return new DataFrame(sorted);
    }

    groupBy(column) {
        if (!this.columns.includes(column)) {
            throw new Error(`Unknown grouping column: ${column}`);
        }

        const groups = new Map();

        for (const row of this.rows) {
            const key = row[column];

            if (!groups.has(key)) {
                groups.set(key, []);
            }

            groups.get(key).push(row);
        }

        return groups;
    }

    toJSON() {
        return this.rows.map((row) => ({ ...row }));
    }

    print(title) {
        console.log(`\n${title}`);
        console.table(this.rows);
    }
}

class Series {
    constructor(values, name = "value") {
        if (!Array.isArray(values)) {
            throw new TypeError("Series requires an array.");
        }

        this.values = [...values];
        this.name = name;
    }

    at(index) {
        if (!Number.isInteger(index) || index < 0 || index >= this.values.length) {
            throw new RangeError("Series index is out of range.");
        }

        return this.values[index];
    }

    map(callback) {
        return new Series(this.values.map(callback), this.name);
    }

    filter(predicate) {
        return new Series(this.values.filter(predicate), this.name);
    }

    mean() {
        const numbers = this.values.filter(
            (value) => typeof value === "number" && Number.isFinite(value)
        );

        if (numbers.length === 0) {
            return null;
        }

        return numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
    }
}

async function processData() {
    const salarySeries = new Series(
        [95000, 72000, 105000, 68000, 88000],
        "salary"
    );

    console.log("Series values:", salarySeries.values);
    console.log("Mean salary:", salarySeries.mean());
    console.log("Third salary:", salarySeries.at(2));

    const employees = new DataFrame([
        {
            employee: "Asha",
            department: "Engineering",
            salary: 95000,
            performance: 4.5,
            active: true,
        },
        {
            employee: "Ravi",
            department: "Sales",
            salary: 72000,
            performance: 3.8,
            active: true,
        },
        {
            employee: "Meera",
            department: "Engineering",
            salary: 105000,
            performance: 4.8,
            active: true,
        },
        {
            employee: "John",
            department: "Sales",
            salary: 68000,
            performance: 3.2,
            active: false,
        },
        {
            employee: "Fatima",
            department: "Finance",
            salary: 88000,
            performance: 4.1,
            active: true,
        },
    ]);

    employees.print("Original DataFrame");

    employees
        .select("employee", "salary")
        .print("Selected columns");

    employees
        .filter((row) => row.active && row.performance >= 4)
        .print("Filtered rows");

    const enriched = employees.assign(
        "bonus",
        (row) => row.salary * row.performance / 100
    ).assign(
        "totalCompensation",
        (row) => row.salary + row.bonus
    );

    enriched.print("Derived columns");

    enriched
        .sortBy("totalCompensation", true)
        .print("Sorted by compensation");

    const groups = enriched.groupBy("department");
    const summary = [];

    for (const [department, rows] of groups) {
        const averageSalary =
            rows.reduce((sum, row) => sum + row.salary, 0) / rows.length;

        summary.push({
            department,
            employees: rows.length,
            averageSalary: Number(averageSalary.toFixed(2)),
        });
    }

    new DataFrame(summary).print("Department aggregation");

    const engineering = enriched.filter(
        (row) => row.department === "Engineering"
    );

    if (engineering.rows.length !== 2) {
        throw new Error("Unexpected Engineering employee count.");
    }

    console.log("\nValidation completed successfully.");
}

processData().catch((error) => {
    console.error("Data-processing failure:", error.message);
    process.exitCode = 1;
});
