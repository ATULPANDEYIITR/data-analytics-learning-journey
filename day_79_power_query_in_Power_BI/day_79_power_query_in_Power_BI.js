"use strict";

/*
 * Power Query-style transformation engine.
 * Runtime: Node.js 18+
 *
 * Demonstrates:
 * - Data cleaning and validation
 * - Data type conversion
 * - Merge and append
 * - Asynchronous query evaluation
 * - Dependency management
 * - Event-driven execution
 * - Transformation error handling
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class TransformationError extends Error {}
class DependencyError extends Error {}

const DataType = Object.freeze({
    TEXT: "text",
    INTEGER: "integer",
    DECIMAL: "decimal",
    DATE: "date",
    BOOLEAN: "boolean"
});

function validateTable(table) {
    if (!table || !Array.isArray(table.columns) ||
        !Array.isArray(table.rows)) {
        throw new TransformationError("Invalid table structure.");
    }

    if (table.columns.length === 0 ||
        new Set(table.columns).size !== table.columns.length) {
        throw new TransformationError("Invalid column definitions.");
    }

    for (const row of table.rows) {
        if (table.columns.some(column =>
            !Object.hasOwn(row, column))) {
            throw new TransformationError("Row schema mismatch.");
        }
    }
}

function createTable(name, columns, rows) {
    const table = { name, columns: [...columns], rows };
    validateTable(table);
    return table;
}

function cleanValue(value) {
    if (typeof value !== "string") return value;

    const cleaned = value.trim().replace(/\s+/g, " ");
    return cleaned === "" ? null : cleaned;
}

function cleanTable(table) {
    return createTable(
        table.name,
        table.columns,
        table.rows.map(row =>
            Object.fromEntries(
                Object.entries(row).map(([key, value]) =>
                    [key, cleanValue(value)]
                )
            )
        )
    );
}

function convertValue(value, type) {
    if (value === null || value === undefined) return null;

    switch (type) {
        case DataType.TEXT:
            return String(value);

        case DataType.INTEGER: {
            if (!/^-?\d+$/.test(String(value).trim())) {
                throw new TransformationError(
                    `Invalid integer: ${value}`
                );
            }

            const number = Number(value);

            if (!Number.isSafeInteger(number)) {
                throw new TransformationError(
                    `Unsafe integer: ${value}`
                );
            }

            return number;
        }

        case DataType.DECIMAL: {
            const number = Number(value);

            if (!Number.isFinite(number)) {
                throw new TransformationError(
                    `Invalid decimal: ${value}`
                );
            }

            return number;
        }

        case DataType.DATE: {
            const text = String(value);

            if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) {
                throw new TransformationError(
                    `Invalid ISO date: ${value}`
                );
            }

            const parsed = new Date(`${text}T00:00:00Z`);

            if (Number.isNaN(parsed.getTime()) ||
                parsed.toISOString().slice(0, 10) !== text) {
                throw new TransformationError(
                    `Invalid calendar date: ${value}`
                );
            }

            return text;
        }

        case DataType.BOOLEAN: {
            if (typeof value === "boolean") return value;

            const normalized = String(value).toLowerCase();

            if (["true", "1", "yes"].includes(normalized)) {
                return true;
            }

            if (["false", "0", "no"].includes(normalized)) {
                return false;
            }

            throw new TransformationError(
                `Invalid boolean: ${value}`
            );
        }

        default:
            throw new TransformationError(
                `Unsupported type: ${type}`
            );
    }
}

function changeTypes(table, schema, strict = true) {
    for (const column of Object.keys(schema)) {
        if (!table.columns.includes(column)) {
            throw new TransformationError(
                `Unknown column: ${column}`
            );
        }
    }

    const rows = table.rows.map((row, index) => {
        const output = { ...row };

        for (const [column, type] of Object.entries(schema)) {
            try {
                output[column] = convertValue(row[column], type);
            } catch (error) {
                if (strict) {
                    throw new TransformationError(
                        `Row ${index}, ${column}: ${error.message}`
                    );
                }

                output[column] = null;
            }
        }

        return output;
    });

    return createTable(table.name, table.columns, rows);
}

function removeDuplicates(table, keys = table.columns) {
    const seen = new Set();
    const rows = [];

    for (const row of table.rows) {
        const key = JSON.stringify(keys.map(k => row[k]));

        if (!seen.has(key)) {
            seen.add(key);
            rows.push({ ...row });
        }
    }

    return createTable(table.name, table.columns, rows);
}

function filterRows(table, predicate) {
    return createTable(
        table.name,
        table.columns,
        table.rows.filter(predicate).map(row => ({ ...row }))
    );
}

function addColumn(table, name, expression) {
    if (table.columns.includes(name)) {
        throw new TransformationError("Column already exists.");
    }

    return createTable(
        table.name,
        [...table.columns, name],
        table.rows.map(row => ({
            ...row,
            [name]: expression(row)
        }))
    );
}

function mergeTables(left, right, leftKey, rightKey) {
    if (!left.columns.includes(leftKey) ||
        !right.columns.includes(rightKey)) {
        throw new TransformationError("Invalid merge keys.");
    }

    const rightColumns = right.columns.filter(
        column => column !== rightKey
    );

    const names = new Map();

    for (const column of rightColumns) {
        const output = left.columns.includes(column)
            ? `${column}_right`
            : column;

        if (left.columns.includes(output) ||
            [...names.values()].includes(output)) {
            throw new TransformationError(
                "Merge produces duplicate column names."
            );
        }

        names.set(column, output);
    }

    const index = new Map();

    for (const row of right.rows) {
        const key = row[rightKey];

        if (key === null || key === undefined) continue;

        if (!index.has(key)) index.set(key, []);
        index.get(key).push(row);
    }

    const rows = [];

    for (const row of left.rows) {
        const matches = index.get(row[leftKey]) || [];

        if (matches.length === 0) {
            const output = { ...row };

            for (const name of names.values()) {
                output[name] = null;
            }

            rows.push(output);
            continue;
        }

        for (const match of matches) {
            const output = { ...row };

            for (const [original, renamed] of names) {
                output[renamed] = match[original];
            }

            rows.push(output);
        }
    }

    return createTable(
        `${left.name}_merged`,
        [...left.columns, ...names.values()],
        rows
    );
}

function appendTables(tables) {
    if (!tables.length) {
        throw new TransformationError("No tables supplied.");
    }

    const columns = [
        ...new Set(tables.flatMap(table => table.columns))
    ];

    const rows = tables.flatMap(table =>
        table.rows.map(row =>
            Object.fromEntries(
                columns.map(column => [
                    column,
                    row[column] ?? null
                ])
            )
        )
    );

    return createTable("appended", columns, rows);
}

function groupBy(table, groupColumn, valueColumn) {
    if (!table.columns.includes(groupColumn) ||
        !table.columns.includes(valueColumn)) {
        throw new TransformationError("Invalid grouping columns.");
    }

    const groups = new Map();

    for (const row of table.rows) {
        const key = row[groupColumn];

        groups.set(
            key,
            (groups.get(key) || 0) + row[valueColumn]
        );
    }

    return createTable(
        "grouped",
        [groupColumn, "total"],
        [...groups.entries()].map(([key, total]) => ({
            [groupColumn]: key,
            total
        }))
    );
}

class QueryEngine extends EventEmitter {
    constructor() {
        super();
        this.queries = new Map();
        this.cache = new Map();
    }

    register(name, dependencies, transform) {
        if (this.queries.has(name)) {
            throw new DependencyError(
                `Duplicate query: ${name}`
            );
        }

        this.queries.set(name, {
            name,
            dependencies,
            transform,
            status: "created"
        });
    }

    order() {
        const completed = new Set();
        const active = new Set();
        const result = [];

        const visit = name => {
            if (!this.queries.has(name)) {
                throw new DependencyError(
                    `Missing dependency: ${name}`
                );
            }

            if (active.has(name)) {
                throw new DependencyError(
                    `Circular dependency at ${name}`
                );
            }

            if (completed.has(name)) return;

            active.add(name);

            for (const dependency of
                this.queries.get(name).dependencies) {
                visit(dependency);
            }

            active.delete(name);
            completed.add(name);
            result.push(name);
        };

        for (const name of this.queries.keys()) {
            visit(name);
        }

        return result;
    }

    async execute() {
        const results = new Map();

        for (const name of this.order()) {
            const query = this.queries.get(name);
            query.status = "running";

            this.emit("queryStarted", name);

            try {
                const dependencies = Object.fromEntries(
                    query.dependencies.map(dependency => [
                        dependency,
                        results.get(dependency)
                    ])
                );

                const result = await query.transform(
                    dependencies
                );

                validateTable(result);

                query.status = "completed";
                results.set(name, result);
                this.cache.set(name, result);

                this.emit("queryCompleted", {
                    name,
                    rows: result.rows.length
                });
            } catch (error) {
                query.status = "failed";

                this.emit("queryFailed", {
                    name,
                    error: error.message
                });

                throw error;
            }
        }

        return results;
    }
}

async function main() {
    const customers = createTable(
        "customers",
        ["customer_id", "name", "region"],
        [
            { customer_id: "1", name: " Alice ", region: "North" },
            { customer_id: "2", name: "Bob", region: "South" },
            { customer_id: "3", name: "Carol", region: "North" }
        ]
    );

    const orders = createTable(
        "orders",
        ["order_id", "customer_id", "amount", "order_date"],
        [
            {
                order_id: "101",
                customer_id: "1",
                amount: "1250.50",
                order_date: "2026-01-10"
            },
            {
                order_id: "102",
                customer_id: "2",
                amount: "800.00",
                order_date: "2026-01-12"
            },
            {
                order_id: "103",
                customer_id: "1",
                amount: "450.25",
                order_date: "2026-02-02"
            },
            {
                order_id: "104",
                customer_id: "99",
                amount: "300.00",
                order_date: "2026-02-05"
            }
        ]
    );

    const archived = createTable(
        "archived",
        orders.columns,
        [{
            order_id: "90",
            customer_id: "2",
            amount: "500.00",
            order_date: "2025-12-15"
        }]
    );

    const cleanedCustomers = removeDuplicates(
        cleanTable(customers),
        ["customer_id"]
    );

    const typedCustomers = changeTypes(
        cleanedCustomers,
        { customer_id: DataType.INTEGER }
    );

    const typedOrders = changeTypes(
        orders,
        {
            order_id: DataType.INTEGER,
            customer_id: DataType.INTEGER,
            amount: DataType.DECIMAL,
            order_date: DataType.DATE
        }
    );

    const typedArchived = changeTypes(
        archived,
        {
            order_id: DataType.INTEGER,
            customer_id: DataType.INTEGER,
            amount: DataType.DECIMAL,
            order_date: DataType.DATE
        }
    );

    const merged = mergeTables(
        typedOrders,
        typedCustomers,
        "customer_id",
        "customer_id"
    );

    const appended = appendTables([
        typedOrders,
        typedArchived
    ]);

    const categorized = addColumn(
        appended,
        "category",
        row => row.amount >= 1000
            ? "High Value"
            : "Standard"
    );

    const grouped = groupBy(
        categorized,
        "category",
        "amount"
    );

    const engine = new QueryEngine();

    engine.on("queryStarted", name =>
        console.log(`Executing: ${name}`)
    );

    engine.on("queryCompleted", result =>
        console.log(
            `Completed: ${result.name}, ${result.rows} rows`
        )
    );

    engine.on("queryFailed", failure =>
        console.error("Query failed:", failure)
    );

    engine.register("source", [], async () => typedOrders);

    engine.register("filtered", ["source"], async data =>
        filterRows(
            data.source,
            row => row.amount >= 500
        )
    );

    engine.register("summary", ["filtered"], async data => {
        const rows = data.filtered.rows;

        return createTable(
            "summary",
            ["count", "total"],
            [{
                count: rows.length,
                total: rows.reduce(
                    (sum, row) => sum + row.amount,
                    0
                )
            }]
        );
    });

    const results = await engine.execute();

    const report = {
        merged,
        appended: categorized,
        grouped,
        summary: results.get("summary")
    };

    await fs.writeFile(
        "power_query_report.json",
        JSON.stringify(report, null, 2),
        "utf8"
    );

    console.log("\nSummary:");
    console.log(results.get("summary"));

    console.log("\nExported power_query_report.json");

    if (merged.rows.length !== 4 ||
        categorized.rows.length !== 5) {
        throw new Error("Unexpected transformation result.");
    }

    console.log("All checks passed.");
}

main().catch(error => {
    console.error("Pipeline terminated:", error.message);
    process.exitCode = 1;
});
