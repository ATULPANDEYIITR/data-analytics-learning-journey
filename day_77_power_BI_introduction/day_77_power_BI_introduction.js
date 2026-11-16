"use strict";

/**
 * POWER BI INTRODUCTION
 * Event-driven Business Intelligence simulation.
 *
 * Features:
 * - Data ingestion and validation
 * - Analytical transformations
 * - Star-schema modeling
 * - DAX-style measure evaluation
 * - Interactive filter context
 * - Report and dashboard generation
 * - Asynchronous refresh management
 * - Event-driven notifications
 * - Export to JSON and CSV
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const EventEmitter = require("node:events");

// ============================================================
// 1. CONFIGURATION
// ============================================================

const CONFIG = Object.freeze({
    currency: "INR",
    outputDirectory: path.resolve("power-bi-output"),
    maximumRecords: 100000,
    refreshTimeoutMs: 10000
});

const RefreshState = Object.freeze({
    IDLE: "IDLE",
    RUNNING: "RUNNING",
    SUCCESS: "SUCCESS",
    FAILED: "FAILED"
});

// ============================================================
// 2. CUSTOM ERRORS
// ============================================================

class BIError extends Error {
    constructor(message, code = "BI_ERROR") {
        super(message);
        this.name = "BIError";
        this.code = code;
    }
}

class ValidationError extends BIError {
    constructor(message) {
        super(message, "VALIDATION_ERROR");
        this.name = "ValidationError";
    }
}

class RefreshError extends BIError {
    constructor(message) {
        super(message, "REFRESH_ERROR");
        this.name = "RefreshError";
    }
}

// ============================================================
// 3. SOURCE DATA
// ============================================================

const customers = Object.freeze([
    { id: 1, name: "Aarav Sharma", region: "North", segment: "Enterprise" },
    { id: 2, name: "Meera Verma", region: "South", segment: "Consumer" },
    { id: 3, name: "Rohan Gupta", region: "East", segment: "Enterprise" },
    { id: 4, name: "Ananya Singh", region: "West", segment: "Consumer" },
    { id: 5, name: "Kabir Patel", region: "North", segment: "Small Business" }
]);

const products = Object.freeze([
    { id: 101, name: "Laptop", category: "Electronics", cost: 45000 },
    { id: 102, name: "Monitor", category: "Electronics", cost: 12000 },
    { id: 103, name: "Office Chair", category: "Furniture", cost: 5000 },
    { id: 104, name: "Desk", category: "Furniture", cost: 8000 },
    { id: 105, name: "Keyboard", category: "Accessories", cost: 1000 }
]);

const sales = Object.freeze([
    { id: 1001, customerId: 1, productId: 101, date: "2026-01-10", quantity: 2, price: 65000 },
    { id: 1002, customerId: 2, productId: 102, date: "2026-01-15", quantity: 3, price: 18000 },
    { id: 1003, customerId: 3, productId: 103, date: "2026-02-05", quantity: 5, price: 8500 },
    { id: 1004, customerId: 4, productId: 104, date: "2026-02-12", quantity: 2, price: 12000 },
    { id: 1005, customerId: 1, productId: 105, date: "2026-03-01", quantity: 10, price: 1800 },
    { id: 1006, customerId: 5, productId: 101, date: "2026-03-15", quantity: 1, price: 68000 },
    { id: 1007, customerId: 3, productId: 102, date: "2026-04-02", quantity: 4, price: 17500 },
    { id: 1008, customerId: 2, productId: 103, date: "2026-04-08", quantity: 3, price: 9000 },
    { id: 1009, customerId: 4, productId: 105, date: "2026-05-10", quantity: 15, price: 1600 },
    { id: 1010, customerId: 5, productId: 104, date: "2026-05-18", quantity: 3, price: 12500 }
]);

// ============================================================
// 4. DATA VALIDATION
// ============================================================

class DataValidator {

    static validate(customers, products, sales) {

        const customerIds = new Set(customers.map(c => c.id));
        const productIds = new Set(products.map(p => p.id));
        const transactionIds = new Set();

        const errors = [];
        const valid = [];

        if (sales.length > CONFIG.maximumRecords) {
            throw new ValidationError("Maximum record count exceeded.");
        }

        for (const transaction of sales) {

            const problems = [];

            if (!Number.isInteger(transaction.id) || transaction.id <= 0) {
                problems.push("Invalid transaction ID");
            }

            if (transactionIds.has(transaction.id)) {
                problems.push("Duplicate transaction ID");
            }

            if (!customerIds.has(transaction.customerId)) {
                problems.push("Customer does not exist");
            }

            if (!productIds.has(transaction.productId)) {
                problems.push("Product does not exist");
            }

            if (!Number.isInteger(transaction.quantity) || transaction.quantity <= 0) {
                problems.push("Invalid quantity");
            }

            if (!Number.isFinite(transaction.price) || transaction.price < 0) {
                problems.push("Invalid price");
            }

            if (!/^\d{4}-\d{2}-\d{2}$/.test(transaction.date) ||
                Number.isNaN(Date.parse(transaction.date)) ||
                new Date(transaction.date).toISOString().slice(0, 10) !== transaction.date) {
                problems.push("Invalid date");
            }

            transactionIds.add(transaction.id);

            if (problems.length) {
                errors.push({
                    transactionId: transaction.id,
                    problems
                });
            } else {
                valid.push(transaction);
            }
        }

        return {
            total: sales.length,
            valid,
            rejected: errors,
            success: errors.length === 0
        };
    }
}

// ============================================================
// 5. DATA TRANSFORMATION
// ============================================================

class ETLPipeline {

    constructor(customers, products) {

        this.customerMap = new Map(
            customers.map(c => [c.id, c])
        );

        this.productMap = new Map(
            products.map(p => [p.id, p])
        );
    }

    transform(transactions) {

        return transactions.map(transaction => {

            const customer = this.customerMap.get(transaction.customerId);
            const product = this.productMap.get(transaction.productId);

            if (!customer || !product) {
                throw new ValidationError(
                    `Missing dimension reference for transaction ${transaction.id}`
                );
            }

            const revenue = transaction.quantity * transaction.price;
            const cost = transaction.quantity * product.cost;

            return Object.freeze({
                transactionId: transaction.id,
                customerId: customer.id,
                customerName: customer.name,
                region: customer.region,
                segment: customer.segment,
                productId: product.id,
                productName: product.name,
                category: product.category,
                date: transaction.date,
                year: Number(transaction.date.slice(0, 4)),
                month: Number(transaction.date.slice(5, 7)),
                quantity: transaction.quantity,
                revenue,
                cost,
                profit: revenue - cost
            });
        });
    }
}

// ============================================================
// 6. STAR SCHEMA
// ============================================================

class DataModel {

    constructor(records) {

        this.factSales = records;

        this.dimensions = {
            customer: new Map(),
            product: new Map(),
            date: new Map()
        };

        for (const record of records) {

            this.dimensions.customer.set(record.customerId, {
                id: record.customerId,
                name: record.customerName,
                region: record.region,
                segment: record.segment
            });

            this.dimensions.product.set(record.productId, {
                id: record.productId,
                name: record.productName,
                category: record.category
            });

            this.dimensions.date.set(record.date, {
                date: record.date,
                year: record.year,
                month: record.month
            });
        }
    }

    describe() {

        return {
            factTable: "FactSales",
            factRows: this.factSales.length,
            dimensions: Object.fromEntries(
                Object.entries(this.dimensions)
                    .map(([name, map]) => [name, map.size])
            )
        };
    }
}

// ============================================================
// 7. DAX-STYLE MEASURE ENGINE
// ============================================================

class MeasureEngine {

    static sum(records, field) {
        return records.reduce(
            (total, record) => total + record[field],
            0
        );
    }

    static count(records) {
        return records.length;
    }

    static distinctCount(records, field) {
        return new Set(records.map(r => r[field])).size;
    }

    static calculate(records) {

        const revenue = this.sum(records, "revenue");
        const cost = this.sum(records, "cost");
        const profit = revenue - cost;

        return Object.freeze({
            totalRevenue: revenue,
            totalCost: cost,
            totalProfit: profit,
            profitMargin: revenue === 0 ? 0 : profit / revenue * 100,
            orderCount: this.count(records),
            uniqueCustomers: this.distinctCount(records, "customerId"),
            unitsSold: this.sum(records, "quantity"),
            averageOrderValue: records.length === 0 ? 0 : revenue / records.length
        });
    }
}

// ============================================================
// 8. FILTER CONTEXT
// ============================================================

class FilterContext {

    constructor(records) {
        this.originalRecords = records;
        this.activeFilters = new Map();
    }

    setFilter(field, predicate) {

        if (typeof predicate !== "function") {
            throw new TypeError("Filter must be a function.");
        }

        this.activeFilters.set(field, predicate);
        return this;
    }

    removeFilter(field) {
        this.activeFilters.delete(field);
        return this;
    }

    clear() {
        this.activeFilters.clear();
        return this;
    }

    evaluate() {

        return this.originalRecords.filter(record => {

            for (const [field, predicate] of this.activeFilters) {
                if (!predicate(record[field], record)) {
                    return false;
                }
            }

            return true;
        });
    }
}

// ============================================================
// 9. REPORT GENERATION
// ============================================================

class ReportBuilder {

    constructor(records) {
        this.records = records;
    }

    aggregate(dimension, measure = "revenue") {

        const result = new Map();

        for (const record of this.records) {

            const key = record[dimension];

            if (key === undefined || key === null) {
                continue;
            }

            result.set(
                key,
                (result.get(key) || 0) + record[measure]
            );
        }

        return Object.fromEntries(
            [...result.entries()].sort(
                (a, b) => String(a[0]).localeCompare(String(b[0]))
            )
        );
    }

    generate(type) {

        const dimensions = {
            sales: "region",
            products: "productName",
            customers: "customerName",
            financial: "category"
        };

        const dimension = dimensions[type];

        if (!dimension) {
            throw new BIError(`Unsupported report: ${type}`);
        }

        return {
            title: `${type.toUpperCase()} REPORT`,
            generatedAt: new Date().toISOString(),
            metrics: MeasureEngine.calculate(this.records),
            chartData: this.aggregate(dimension),
            chartType: "bar"
        };
    }
}

// ============================================================
// 10. DASHBOARD
// ============================================================

class Dashboard {

    constructor(records) {
        this.records = records;
        this.widgets = [];
    }

    addKPI(name, field, unit = "") {

        const metrics = MeasureEngine.calculate(this.records);

        if (!(field in metrics)) {
            throw new BIError(`Unknown KPI field: ${field}`);
        }

        this.widgets.push(Object.freeze({
            type: "KPI",
            name,
            value: metrics[field],
            unit
        }));

        return this;
    }

    build() {

        return {
            title: "Executive Sales Dashboard",
            refreshedAt: new Date().toISOString(),
            widgets: [...this.widgets]
        };
    }
}

// ============================================================
// 11. EVENT-DRIVEN REFRESH SERVICE
// ============================================================

class RefreshService extends EventEmitter {

    constructor() {
        super();

        this.state = RefreshState.IDLE;
        this.lastRefresh = null;
        this.lastError = null;
    }

    async refresh(operation) {

        if (this.state === RefreshState.RUNNING) {
            throw new RefreshError("A refresh is already running.");
        }

        this.state = RefreshState.RUNNING;
        this.lastError = null;

        this.emit("refreshStarted");

        try {

            const result = await operation();

            this.state = RefreshState.SUCCESS;
            this.lastRefresh = new Date();

            this.emit("refreshCompleted", result);

            return result;

        } catch (error) {

            this.state = RefreshState.FAILED;
            this.lastError = error.message;

            this.emit("refreshFailed", error);

            throw new RefreshError(error.message);
        }
    }

    getStatus() {

        return {
            state: this.state,
            lastRefresh: this.lastRefresh,
            lastError: this.lastError
        };
    }
}

// ============================================================
// 12. ANALYTICAL FUNCTIONS
// ============================================================

function monthlyRevenue(records) {

    const monthly = new Map();

    for (const record of records) {

        const key = `${record.year}-${String(record.month).padStart(2, "0")}`;

        monthly.set(
            key,
            (monthly.get(key) || 0) + record.revenue
        );
    }

    return Object.fromEntries(monthly);
}

function topProducts(records, limit = 3) {

    if (!Number.isInteger(limit) || limit < 1) {
        throw new RangeError("Limit must be a positive integer.");
    }

    const totals = new Map();

    for (const record of records) {

        totals.set(
            record.productName,
            (totals.get(record.productName) || 0) + record.revenue
        );
    }

    return [...totals.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit);
}

// ============================================================
// 13. FILE EXPORT
// ============================================================

async function exportJSON(filename, data) {

    await fs.mkdir(CONFIG.outputDirectory, {
        recursive: true
    });

    const destination = path.join(
        CONFIG.outputDirectory,
        filename
    );

    await fs.writeFile(
        destination,
        JSON.stringify(data, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );

    return destination;
}

async function exportCSV(filename, records) {

    if (!records.length) {
        throw new BIError("Cannot export empty records.");
    }

    const fields = Object.keys(records[0]);

    const escapeCSV = value => {
        const text = String(value ?? "");
        return `"${text.replaceAll('"', '""')}"`;
    };

    const lines = [
        fields.map(escapeCSV).join(","),
        ...records.map(record =>
            fields.map(field => escapeCSV(record[field])).join(",")
        )
    ];

    const destination = path.join(
        CONFIG.outputDirectory,
        filename
    );

    await fs.mkdir(CONFIG.outputDirectory, {
        recursive: true
    });

    await fs.writeFile(
        destination,
        lines.join("\n") + "\n",
        { encoding: "utf8", mode: 0o600 }
    );

    return destination;
}

// ============================================================
// 14. MAIN APPLICATION
// ============================================================

async function main() {

    console.log("\nPOWER BI INTRODUCTION");
    console.log("Event-Driven Business Intelligence Architecture");
    console.log("-".repeat(65));

    const refresh = new RefreshService();

    refresh.on("refreshStarted", () => {
        console.log("Refresh started.");
    });

    refresh.on("refreshCompleted", result => {
        console.log(`Refresh completed: ${result.length} records.`);
    });

    refresh.on("refreshFailed", error => {
        console.error("Refresh failure:", error.message);
    });

    const validation = DataValidator.validate(
        customers,
        products,
        sales
    );

    console.log("\nDATA QUALITY");
    console.log({
        total: validation.total,
        accepted: validation.valid.length,
        rejected: validation.rejected.length
    });

    if (!validation.success) {
        throw new ValidationError(
            JSON.stringify(validation.rejected)
        );
    }

    const pipeline = new ETLPipeline(customers, products);

    const records = await refresh.refresh(async () => {
        return pipeline.transform(validation.valid);
    });

    const model = new DataModel(records);

    console.log("\nDATA MODEL");
    console.log(model.describe());

    const measures = MeasureEngine.calculate(records);

    console.log("\nBUSINESS MEASURES");
    console.table(measures);

    const reportBuilder = new ReportBuilder(records);

    console.log("\nREGIONAL SALES REPORT");
    console.log(
        JSON.stringify(reportBuilder.generate("sales"), null, 2)
    );

    console.log("\nPRODUCT REPORT");
    console.log(
        JSON.stringify(reportBuilder.generate("products"), null, 2)
    );

    const filters = new FilterContext(records);

    filters.setFilter(
        "region",
        region => region === "North"
    );

    console.log("\nNORTH REGION FILTER CONTEXT");
    console.log(
        MeasureEngine.calculate(filters.evaluate())
    );

    filters.clear();

    const dashboard = new Dashboard(records)
        .addKPI("Total Revenue", "totalRevenue", "INR")
        .addKPI("Total Profit", "totalProfit", "INR")
        .addKPI("Profit Margin", "profitMargin", "%")
        .addKPI("Unique Customers", "uniqueCustomers");

    console.log("\nDASHBOARD");
    console.log(JSON.stringify(dashboard.build(), null, 2));

    console.log("\nMONTHLY REVENUE");
    console.log(monthlyRevenue(records));

    console.log("\nTOP PRODUCTS");
    console.log(topProducts(records, 3));

    await exportJSON("sales-report.json", reportBuilder.generate("sales"));
    await exportCSV("fact-sales.csv", records);

    // Verify analytical invariants.
    if (records.length !== validation.valid.length) {
        throw new BIError("ETL record reconciliation failed.");
    }

    if (measures.totalRevenue <= 0) {
        throw new BIError("Revenue validation failed.");
    }

    if (MeasureEngine.calculate([]).profitMargin !== 0) {
        throw new BIError("Empty dataset calculation failed.");
    }

    console.log("\nREFRESH STATUS");
    console.log(refresh.getStatus());

    console.log("\nALL VALIDATIONS PASSED.");
}

main().catch(error => {
    console.error(
        `[${error.code || "APPLICATION_ERROR"}] ${error.message}`
    );
    process.exitCode = 1;
});
