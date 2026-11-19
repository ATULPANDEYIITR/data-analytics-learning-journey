"use strict";

/*
 * POWER BI DATA MODELING
 * Event-driven semantic model and relationship evaluation.
 *
 * Demonstrates:
 * - Star schema metadata
 * - Fact and dimension tables
 * - Cardinality validation
 * - Filter propagation
 * - Relationship activation
 * - Cross-filter direction
 * - Analytical aggregation
 * - Model refresh and validation events
 * - Asynchronous refresh failure handling
 *
 * Runtime: Node.js 18+
 * No external dependencies.
 */

const EventEmitter = require("node:events");
const crypto = require("node:crypto");

const Cardinality = Object.freeze({
    ONE_TO_ONE: "ONE_TO_ONE",
    ONE_TO_MANY: "ONE_TO_MANY",
    MANY_TO_ONE: "MANY_TO_ONE",
    MANY_TO_MANY: "MANY_TO_MANY"
});

const TableType = Object.freeze({
    FACT: "FACT",
    DIMENSION: "DIMENSION"
});

const FilterDirection = Object.freeze({
    SINGLE: "SINGLE",
    BOTH: "BOTH"
});

class ModelError extends Error {
    constructor(message) {
        super(message);
        this.name = "ModelError";
    }
}

class DataTable {
    constructor(name, type, primaryKey, columns) {
        if (!name || !primaryKey || !Array.isArray(columns)) {
            throw new ModelError("Invalid table definition");
        }

        this.name = name;
        this.type = type;
        this.primaryKey = primaryKey;
        this.columns = new Set(columns);
        this.rows = [];
        this.index = new Map();
    }

    insert(record) {
        const keys = Object.keys(record);

        for (const key of keys) {
            if (!this.columns.has(key)) {
                throw new ModelError(
                    `${this.name}: unknown column ${key}`
                );
            }
        }

        for (const column of this.columns) {
            if (!(column in record)) {
                throw new ModelError(
                    `${this.name}: missing column ${column}`
                );
            }

            if (record[column] === null ||
                record[column] === undefined) {
                throw new ModelError(
                    `${this.name}.${column} cannot be NULL`
                );
            }
        }

        const primaryValue = record[this.primaryKey];

        if (this.index.has(primaryValue)) {
            throw new ModelError(
                `${this.name}: duplicate primary key ${primaryValue}`
            );
        }

        const immutableRecord = Object.freeze({ ...record });

        this.rows.push(immutableRecord);
        this.index.set(primaryValue, immutableRecord);
    }

    findByKey(value) {
        return this.index.get(value) || null;
    }

    get size() {
        return this.rows.length;
    }
}

class Relationship {
    constructor({
        name,
        fromTable,
        fromColumn,
        toTable,
        toColumn,
        cardinality,
        direction = FilterDirection.SINGLE,
        active = true
    }) {
        Object.assign(this, {
            name,
            fromTable,
            fromColumn,
            toTable,
            toColumn,
            cardinality,
            direction,
            active
        });
    }
}

class SemanticModel extends EventEmitter {
    constructor(name) {
        super();

        this.name = name;
        this.tables = new Map();
        this.relationships = new Map();
        this.refreshState = "READY";
        this.version = 0;
    }

    addTable(table) {
        if (this.tables.has(table.name)) {
            throw new ModelError(
                `Duplicate table ${table.name}`
            );
        }

        this.tables.set(table.name, table);
        this.emit("tableAdded", table.name);
    }

    addRelationship(relationship) {
        if (this.relationships.has(relationship.name)) {
            throw new ModelError(
                `Duplicate relationship ${relationship.name}`
            );
        }

        const source = this.tables.get(relationship.fromTable);
        const target = this.tables.get(relationship.toTable);

        if (!source || !target) {
            throw new ModelError(
                "Both relationship tables must exist"
            );
        }

        if (!source.columns.has(relationship.fromColumn) ||
            !target.columns.has(relationship.toColumn)) {
            throw new ModelError(
                "Relationship column does not exist"
            );
        }

        if (!Object.values(Cardinality).includes(
            relationship.cardinality
        )) {
            throw new ModelError("Invalid cardinality");
        }

        this.relationships.set(
            relationship.name,
            relationship
        );

        this.emit("relationshipAdded", relationship.name);
    }

    validate() {
        const issues = [];

        for (const relationship of this.relationships.values()) {
            if (!relationship.active) {
                continue;
            }

            const source = this.tables.get(
                relationship.fromTable
            );

            const target = this.tables.get(
                relationship.toTable
            );

            const sourceValues = source.rows.map(
                row => row[relationship.fromColumn]
            );

            const targetValues = target.rows.map(
                row => row[relationship.toColumn]
            );

            const uniqueSource = new Set(sourceValues);
            const uniqueTarget = new Set(targetValues);

            if (
                relationship.cardinality ===
                    Cardinality.MANY_TO_ONE &&
                uniqueSource.size !== sourceValues.length
            ) {
                issues.push(
                    `${relationship.name}: source is not unique`
                );
            }

            if (
                relationship.cardinality ===
                    Cardinality.ONE_TO_MANY &&
                uniqueTarget.size !== targetValues.length
            ) {
                issues.push(
                    `${relationship.name}: target is not unique`
                );
            }

            if (
                relationship.cardinality ===
                    Cardinality.ONE_TO_ONE &&
                (
                    uniqueSource.size !== sourceValues.length ||
                    uniqueTarget.size !== targetValues.length
                )
            ) {
                issues.push(
                    `${relationship.name}: one-to-one violation`
                );
            }

            const targetSet = new Set(targetValues);

            for (const value of sourceValues) {
                if (!targetSet.has(value)) {
                    issues.push(
                        `${relationship.name}: orphan key ${value}`
                    );
                }
            }

            if (
                relationship.cardinality ===
                Cardinality.MANY_TO_MANY
            ) {
                issues.push(
                    `${relationship.name}: explicit bridge-table review required`
                );
            }
        }

        this.emit("validated", {
            valid: issues.length === 0,
            issues
        });

        return issues;
    }

    getDimensionFilter(relationshipName, selectedValues) {
        const relationship = this.relationships.get(
            relationshipName
        );

        if (!relationship || !relationship.active) {
            throw new ModelError(
                "Relationship is missing or inactive"
            );
        }

        if (
            relationship.cardinality !== Cardinality.MANY_TO_ONE
        ) {
            throw new ModelError(
                "Expected a fact-to-dimension relationship"
            );
        }

        const dimension = this.tables.get(
            relationship.toTable
        );

        const selected = new Set(selectedValues);

        const matchingKeys = new Set(
            dimension.rows
                .filter(row => selected.has(row[relationship.toColumn]))
                .map(row => row[relationship.toColumn])
        );

        const fact = this.tables.get(
            relationship.fromTable
        );

        return fact.rows.filter(row =>
            matchingKeys.has(row[relationship.fromColumn])
        );
    }

    aggregate(rows, groupColumn, valueColumn) {
        const totals = new Map();

        for (const row of rows) {
            const key = row[groupColumn];
            const value = Number(row[valueColumn]);

            if (!Number.isFinite(value)) {
                throw new ModelError(
                    `Invalid numeric value in ${valueColumn}`
                );
            }

            totals.set(
                key,
                (totals.get(key) || 0) + value
            );
        }

        return Object.fromEntries(totals);
    }

    async refresh(loader) {
        if (this.refreshState === "REFRESHING") {
            throw new ModelError(
                "A refresh is already running"
            );
        }

        this.refreshState = "REFRESHING";
        this.emit("refreshStarted");

        try {
            await loader();

            const issues = this.validate();

            if (issues.length > 0) {
                throw new ModelError(issues.join("; "));
            }

            this.version += 1;
            this.refreshState = "READY";

            this.emit("refreshCompleted", {
                version: this.version
            });

            return this.version;
        } catch (error) {
            this.refreshState = "FAILED";

            this.emit("refreshFailed", {
                message: error.message
            });

            throw error;
        }
    }

    describe() {
        console.log(`\nMODEL: ${this.name}`);

        for (const table of this.tables.values()) {
            console.log(
                `${table.name.padEnd(18)} ` +
                `${table.type.padEnd(12)} ` +
                `Rows=${table.size}`
            );
        }

        console.log("\nRELATIONSHIPS");

        for (const relationship of this.relationships.values()) {
            console.log(
                `${relationship.fromTable}.${relationship.fromColumn}` +
                ` -> ${relationship.toTable}.${relationship.toColumn}` +
                ` | ${relationship.cardinality}` +
                ` | ${relationship.direction}`
            );
        }
    }
}

function createRetailModel() {
    const model = new SemanticModel(
        "Retail Analytics Semantic Model"
    );

    const dimensions = [
        new DataTable(
            "DimProduct",
            TableType.DIMENSION,
            "product_key",
            ["product_key", "product_name", "category", "brand"]
        ),
        new DataTable(
            "DimCustomer",
            TableType.DIMENSION,
            "customer_key",
            ["customer_key", "customer_name", "region", "segment"]
        ),
        new DataTable(
            "DimDate",
            TableType.DIMENSION,
            "date_key",
            ["date_key", "year", "month", "quarter"]
        ),
        new DataTable(
            "DimStore",
            TableType.DIMENSION,
            "store_key",
            ["store_key", "store_name", "city"]
        )
    ];

    const fact = new DataTable(
        "FactSales",
        TableType.FACT,
        "sales_id",
        [
            "sales_id",
            "order_id",
            "product_key",
            "customer_key",
            "date_key",
            "store_key",
            "quantity",
            "unit_price",
            "sales_amount"
        ]
    );

    for (const table of [...dimensions, fact]) {
        model.addTable(table);
    }

    const product = model.tables.get("DimProduct");
    product.insert({
        product_key: 101,
        product_name: "Laptop Pro",
        category: "Electronics",
        brand: "Apex"
    });
    product.insert({
        product_key: 102,
        product_name: "Wireless Mouse",
        category: "Accessories",
        brand: "Nova"
    });
    product.insert({
        product_key: 103,
        product_name: "Mechanical Keyboard",
        category: "Accessories",
        brand: "Nova"
    });

    const customer = model.tables.get("DimCustomer");
    customer.insert({
        customer_key: 201,
        customer_name: "Aarav Sharma",
        region: "North",
        segment: "Premium"
    });
    customer.insert({
        customer_key: 202,
        customer_name: "Meera Singh",
        region: "South",
        segment: "Standard"
    });

    const dates = model.tables.get("DimDate");
    dates.insert({
        date_key: 20260101,
        year: 2026,
        month: 1,
        quarter: 1
    });
    dates.insert({
        date_key: 20260201,
        year: 2026,
        month: 2,
        quarter: 1
    });

    const stores = model.tables.get("DimStore");
    stores.insert({
        store_key: 301,
        store_name: "Lucknow Central",
        city: "Lucknow"
    });
    stores.insert({
        store_key: 302,
        store_name: "Delhi Central",
        city: "Delhi"
    });

    const sales = model.tables.get("FactSales");

    const transactions = [
        [1, "ORD001", 101, 201, 20260101, 301, 1, 75000],
        [2, "ORD001", 102, 201, 20260101, 301, 2, 1200],
        [3, "ORD002", 103, 202, 20260101, 302, 1, 3500],
        [4, "ORD003", 101, 202, 20260201, 302, 1, 75000]
    ];

    for (const [
        salesId, orderId, productKey, customerKey,
        dateKey, storeKey, quantity, unitPrice
    ] of transactions) {
        sales.insert({
            sales_id: salesId,
            order_id: orderId,
            product_key: productKey,
            customer_key: customerKey,
            date_key: dateKey,
            store_key: storeKey,
            quantity,
            unit_price: unitPrice,
            sales_amount: quantity * unitPrice
        });
    }

    const definitions = [
        ["ProductSales", "product_key", "DimProduct", "product_key"],
        ["CustomerSales", "customer_key", "DimCustomer", "customer_key"],
        ["DateSales", "date_key", "DimDate", "date_key"],
        ["StoreSales", "store_key", "DimStore", "store_key"]
    ];

    for (const [name, fromColumn, toTable, toColumn] of definitions) {
        model.addRelationship(new Relationship({
            name,
            fromTable: "FactSales",
            fromColumn,
            toTable,
            toColumn,
            cardinality: Cardinality.MANY_TO_ONE,
            direction: FilterDirection.SINGLE
        }));
    }

    return model;
}

async function main() {
    const model = createRetailModel();

    model.on("tableAdded", name =>
        console.log("Table registered:", name)
    );

    model.on("validated", result =>
        console.log(
            "Validation:",
            result.valid ? "PASSED" : "FAILED"
        )
    );

    model.on("refreshCompleted", result =>
        console.log("Refresh version:", result.version)
    );

    model.on("refreshFailed", result =>
        console.error("Refresh failed:", result.message)
    );

    model.describe();

    const issues = model.validate();

    if (issues.length) {
        throw new ModelError(issues.join("; "));
    }

    const selectedProducts = [101, 102];

    const filteredSales = model.getDimensionFilter(
        "ProductSales",
        selectedProducts
    );

    console.log("\nFILTERED FACT ROWS:", filteredSales.length);

    console.log(
        "SALES BY PRODUCT:",
        model.aggregate(
            filteredSales,
            "product_key",
            "sales_amount"
        )
    );

    console.log(
        "SALES BY CUSTOMER:",
        model.aggregate(
            model.tables.get("FactSales").rows,
            "customer_key",
            "sales_amount"
        )
    );

    await model.refresh(async () => {
        await new Promise(resolve => setTimeout(resolve, 20));
        console.log("\nData refresh completed.");
    });

    console.log("\nMODEL STATE:", model.refreshState);
    console.log("MODEL VERSION:", model.version);

    // A failed refresh does not increment the model version.
    try {
        await model.refresh(async () => {
            throw new Error("Source database unavailable");
        });
    } catch (error) {
        console.log("Handled refresh exception:", error.message);
    }

    console.log("FINAL STATE:", model.refreshState);

    // A unique identifier can be used to correlate model operations.
    console.log(
        "Execution correlation ID:",
        crypto.randomUUID()
    );
}

main().catch(error => {
    console.error("Application error:", error.message);
    process.exitCode = 1;
});
