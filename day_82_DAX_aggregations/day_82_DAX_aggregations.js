"use strict";

/*
 * DAX AGGREGATIONS
 *
 * Event-driven analytical model using JavaScript Maps, Sets,
 * immutable filter contexts, asynchronous query execution,
 * and explicit aggregation policies.
 *
 * Runtime: Node.js 18+
 *
 * Run:
 * node dax_aggregations.js
 */

const { EventEmitter } = require("node:events");
const { performance } = require("node:perf_hooks");

class AnalyticsError extends Error {}
class ValidationError extends AnalyticsError {}
class ColumnError extends AnalyticsError {}
class AggregationError extends AnalyticsError {}

const OPERATORS = Object.freeze({
    EQ: "eq",
    NE: "ne",
    GT: "gt",
    GTE: "gte",
    LT: "lt",
    LTE: "lte",
    IN: "in"
});

const COLUMN_TYPES = Object.freeze({
    transactionId: "number",
    orderDate: "date",
    customerId: "number",
    productId: "number",
    region: "string",
    category: "string",
    quantity: "number",
    unitPrice: "number",
    revenue: "number",
    status: "string"
});

function createRecord(data) {
    const record = Object.freeze({ ...data });

    if (!Number.isInteger(record.transactionId) ||
        record.transactionId <= 0) {
        throw new ValidationError("Invalid transaction ID.");
    }

    if (!Number.isInteger(record.productId) ||
        record.productId <= 0) {
        throw new ValidationError("Invalid product ID.");
    }

    if (record.quantity !== null &&
        (!Number.isInteger(record.quantity) || record.quantity < 0)) {
        throw new ValidationError("Invalid quantity.");
    }

    if (record.revenue !== null &&
        (!Number.isFinite(record.revenue) || record.revenue < 0)) {
        throw new ValidationError("Invalid revenue.");
    }

    if (!Object.hasOwn(COLUMN_TYPES, "revenue")) {
        throw new ValidationError("Invalid model definition.");
    }

    return record;
}

class Filter {
    constructor(column, operator, value) {
        if (!Object.hasOwn(COLUMN_TYPES, column)) {
            throw new ColumnError(`Unknown column: ${column}`);
        }

        if (!Object.values(OPERATORS).includes(operator)) {
            throw new ValidationError("Unsupported filter operator.");
        }

        if (operator === OPERATORS.IN && !Array.isArray(value)) {
            throw new ValidationError("IN requires an array.");
        }

        this.column = column;
        this.operator = operator;
        this.value = value;

        Object.freeze(this);
    }

    matches(record) {
        const actual = record[this.column];

        if (actual === null || actual === undefined) {
            return false;
        }

        switch (this.operator) {
            case OPERATORS.EQ:
                return actual === this.value;

            case OPERATORS.NE:
                return actual !== this.value;

            case OPERATORS.GT:
                return actual > this.value;

            case OPERATORS.GTE:
                return actual >= this.value;

            case OPERATORS.LT:
                return actual < this.value;

            case OPERATORS.LTE:
                return actual <= this.value;

            case OPERATORS.IN:
                return this.value.includes(actual);

            default:
                throw new ValidationError("Invalid operator.");
        }
    }
}

class FilterContext {
    constructor(filters = []) {
        if (!Array.isArray(filters) ||
            !filters.every(filter => filter instanceof Filter)) {
            throw new ValidationError("Invalid filter context.");
        }

        this.filters = Object.freeze([...filters]);
        Object.freeze(this);
    }

    add(...filters) {
        return new FilterContext([
            ...this.filters,
            ...filters
        ]);
    }

    replace(column, filter) {
        if (!(filter instanceof Filter) || filter.column !== column) {
            throw new ValidationError(
                "Replacement filter must target the specified column."
            );
        }

        return new FilterContext([
            ...this.filters.filter(f => f.column !== column),
            filter
        ]);
    }

    matches(record) {
        return this.filters.every(filter => filter.matches(record));
    }
}

class AnalyticsEngine extends EventEmitter {
    constructor(records) {
        super();

        this.records = Object.freeze([...records]);
        this.transactionIds = new Set();

        for (const record of this.records) {
            if (this.transactionIds.has(record.transactionId)) {
                throw new ValidationError(
                    `Duplicate transaction ${record.transactionId}`
                );
            }

            this.transactionIds.add(record.transactionId);
        }

        this.cache = new Map();
    }

    validateColumn(column) {
        if (!Object.hasOwn(COLUMN_TYPES, column)) {
            throw new ColumnError(`Unknown column: ${column}`);
        }
    }

    select(context = new FilterContext()) {
        if (!(context instanceof FilterContext)) {
            throw new ValidationError("Expected FilterContext.");
        }

        return this.records.filter(record => context.matches(record));
    }

    aggregateValues(column, context) {
        this.validateColumn(column);

        if (COLUMN_TYPES[column] !== "number") {
            throw new AggregationError(
                `${column} is not a numeric column.`
            );
        }

        return this.select(context)
            .map(record => record[column])
            .filter(value => value !== null && value !== undefined);
    }

    sum(column, context = new FilterContext()) {
        const values = this.aggregateValues(column, context);

        return values.reduce((total, value) => total + value, 0);
    }

    average(column, context = new FilterContext()) {
        const values = this.aggregateValues(column, context);

        if (values.length === 0) {
            return null;
        }

        return this.sum(column, context) / values.length;
    }

    count(column, context = new FilterContext()) {
        return this.aggregateValues(column, context).length;
    }

    distinctCount(column, context = new FilterContext()) {
        this.validateColumn(column);

        // Set includes null, corresponding to a blank category.
        const values = this.select(context)
            .map(record => record[column]);

        return new Set(values).size;
    }

    filter(context, predicate) {
        if (!(context instanceof FilterContext)) {
            throw new ValidationError("Invalid filter context.");
        }

        if (typeof predicate !== "function") {
            throw new ValidationError("Predicate must be a function.");
        }

        return this.select(context).filter(predicate);
    }

    calculate(expression, filters = [], options = {}) {
        if (typeof expression !== "function") {
            throw new ValidationError("Expression must be callable.");
        }

        let context = options.context || new FilterContext();

        if (!(context instanceof FilterContext)) {
            throw new ValidationError("Invalid base context.");
        }

        const replaceColumns = new Set(
            options.replaceColumns || []
        );

        for (const filter of filters) {
            if (!(filter instanceof Filter)) {
                throw new ValidationError("Invalid CALCULATE filter.");
            }

            context = replaceColumns.has(filter.column)
                ? context.replace(filter.column, filter)
                : context.add(filter);
        }

        return expression(context);
    }

    async query(name, expression, context = new FilterContext()) {
        const start = performance.now();

        // The asynchronous boundary allows callers to schedule
        // analytical work without blocking their orchestration flow.
        await Promise.resolve();

        try {
            const result = expression(context);

            const event = {
                name,
                result,
                durationMs: performance.now() - start,
                status: "success"
            };

            this.emit("queryCompleted", event);
            return result;
        } catch (error) {
            this.emit("queryFailed", {
                name,
                message: error.message
            });

            throw error;
        }
    }

    calculateSum(column, filters = [], options = {}) {
        return this.calculate(
            context => this.sum(column, context),
            filters,
            options
        );
    }

    groupBy(column, measureColumn) {
        this.validateColumn(column);

        const groups = new Map();

        for (const record of this.records) {
            const key = record[column];

            if (!groups.has(key)) {
                groups.set(key, {
                    rows: 0,
                    nonblank: 0,
                    sum: 0
                });
            }

            const group = groups.get(key);
            group.rows++;

            const value = record[measureColumn];

            if (value !== null && value !== undefined) {
                group.nonblank++;
                group.sum += value;
            }
        }

        return groups;
    }
}

function sampleRecords() {
    const data = [
        [1001, "2026-01-05", 101, 1, "North", "Electronics", 2, 500, 1000, "Completed"],
        [1002, "2026-01-08", 102, 2, "South", "Furniture", 1, 800, 800, "Completed"],
        [1003, "2026-01-12", 101, 3, "North", "Electronics", 3, 200, 600, "Completed"],
        [1004, "2026-02-02", 103, 4, "East", "Furniture", 2, 350, 700, "Pending"],
        [1005, "2026-02-09", 104, 5, "West", "Clothing", 5, 100, 500, "Completed"],
        [1006, "2026-02-15", 102, 6, "South", "Electronics", 1, 1200, 1200, "Completed"],
        [1007, "2026-03-01", 105, 7, "North", "Clothing", 4, 150, 600, "Cancelled"],
        [1008, "2026-03-05", 103, 8, "East", "Electronics", 2, 450, 900, "Completed"],
        [1009, "2026-03-12", null, 9, "West", "Furniture", null, 250, null, "Pending"],
        [1010, "2026-03-18", 106, 10, "North", "Electronics", 1, 300, 300, "Completed"]
    ];

    return data.map(row => createRecord({
        transactionId: row[0],
        orderDate: row[1],
        customerId: row[2],
        productId: row[3],
        region: row[4],
        category: row[5],
        quantity: row[6],
        unitPrice: row[7],
        revenue: row[8],
        status: row[9]
    }));
}

async function main() {
    const engine = new AnalyticsEngine(sampleRecords());

    engine.on("queryCompleted", event => {
        console.log(
            `[QUERY] ${event.name}: completed in ` +
            `${event.durationMs.toFixed(3)} ms`
        );
    });

    engine.on("queryFailed", event => {
        console.error(`[QUERY ERROR] ${event.name}: ${event.message}`);
    });

    const eq = (column, value) =>
        new Filter(column, OPERATORS.EQ, value);

    console.log("\nDAX AGGREGATION ENGINE");
    console.log("======================");

    console.log("\nSUM:", engine.sum("revenue"));
    console.log("AVERAGE:", engine.average("revenue"));
    console.log("COUNT:", engine.count("revenue"));
    console.log("DISTINCTCOUNT:", engine.distinctCount("customerId"));

    const northContext = new FilterContext([
        eq("region", "North")
    ]);

    console.log("\nNORTH REGION");
    console.log("SUM:", engine.sum("revenue", northContext));
    console.log("AVERAGE:", engine.average("revenue", northContext));

    const electronics = eq("category", "Electronics");
    const completed = eq("status", "Completed");

    const combined = northContext.add(electronics, completed);

    console.log("\nNORTH COMPLETED ELECTRONICS");
    console.log("SUM:", engine.sum("revenue", combined));

    console.log("\nFILTER");
    const highValue = engine.filter(
        new FilterContext(),
        record => record.revenue !== null &&
                  record.revenue >= 800
    );

    console.log("Transactions with revenue >= 800:", highValue.length);

    console.log("\nCALCULATE");
    const southRevenue = engine.calculateSum(
        "revenue",
        [eq("region", "South")]
    );

    console.log("South revenue:", southRevenue);

    console.log("\nCALCULATE WITH FILTER REPLACEMENT");
    const replacement = engine.calculateSum(
        "revenue",
        [eq("region", "South")],
        {
            context: northContext,
            replaceColumns: ["region"]
        }
    );

    console.log("North replaced by South:", replacement);

    console.log("\nCALCULATE WITH FILTER PRESERVATION");
    const preserved = engine.calculateSum(
        "revenue",
        [electronics],
        { context: northContext }
    );

    console.log("North electronics:", preserved);

    console.log("\nGROUPED REVENUE");

    for (const [region, metrics] of engine.groupBy(
        "region",
        "revenue"
    )) {
        console.log(region, metrics);
    }

    console.log("\nASYNCHRONOUS QUERY");
    const result = await engine.query(
        "RegionalRevenue",
        context => engine.sum("revenue", context),
        northContext
    );

    console.log("Result:", result);

    console.log("\nEDGE CASES");

    const empty = new FilterContext([
        eq("region", "Antarctica")
    ]);

    console.log("Empty SUM:", engine.sum("revenue", empty));
    console.log("Empty AVERAGE:", engine.average("revenue", empty));
    console.log("Empty COUNT:", engine.count("revenue", empty));
    console.log(
        "Empty DISTINCTCOUNT:",
        engine.distinctCount("customerId", empty)
    );

    // Validate the model against known analytical results.
    console.assert(engine.sum("revenue") === 6600);
    console.assert(engine.count("revenue") === 9);
    console.assert(engine.distinctCount("customerId") === 7);
    console.assert(engine.sum("revenue", northContext) === 2500);
    console.assert(engine.average("revenue", empty) === null);

    try {
        engine.sum("unknownColumn");
    } catch (error) {
        console.log("Expected validation error:", error.message);
    }

    console.log("\nAll assertions completed.");
}

main().catch(error => {
    console.error("Fatal analytical failure:", error);
    process.exitCode = 1;
});
