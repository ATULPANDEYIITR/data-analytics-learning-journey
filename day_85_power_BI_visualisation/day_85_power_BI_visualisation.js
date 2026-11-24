"use strict";

/*
 * Power BI Visualization: Event-Driven Dashboard Model
 *
 * Demonstrates:
 * - KPI cards and tabular visualizations
 * - Matrix aggregation
 * - Bar, line, and pie chart datasets
 * - Geographic aggregation
 * - Slicer state management
 * - Cross-filtering
 * - Drill-through navigation
 * - Bookmarks and restoration
 * - Asynchronous refresh and error handling
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class DashboardError extends Error {}
class ValidationError extends DashboardError {}
class NavigationError extends DashboardError {}
class RefreshError extends DashboardError {}

const Visualization = Object.freeze({
    CARD: "card",
    TABLE: "table",
    MATRIX: "matrix",
    BAR: "bar",
    LINE: "line",
    PIE: "pie",
    MAP: "map"
});

const Aggregation = Object.freeze({
    SUM: "sum",
    COUNT: "count",
    AVERAGE: "average",
    MIN: "min",
    MAX: "max",
    DISTINCT: "distinct"
});

const clone = value => structuredClone(value);

function round(value, decimals = 2) {
    const factor = 10 ** decimals;
    return Math.round((value + Number.EPSILON) * factor) / factor;
}

function validateRecord(record) {
    const required = [
        "id",
        "date",
        "region",
        "city",
        "category",
        "product",
        "salesperson",
        "quantity",
        "unitPrice",
        "discount"
    ];

    for (const field of required) {
        if (!(field in record)) {
            throw new ValidationError(`Missing field: ${field}`);
        }
    }

    if (!Number.isInteger(record.id) || record.id <= 0) {
        throw new ValidationError("Transaction ID must be positive.");
    }

    if (!Number.isInteger(record.quantity) || record.quantity <= 0) {
        throw new ValidationError("Quantity must be a positive integer.");
    }

    if (!Number.isFinite(record.unitPrice) || record.unitPrice < 0) {
        throw new ValidationError("Invalid unit price.");
    }

    if (!Number.isFinite(record.discount) ||
        record.discount < 0 ||
        record.discount > 1) {
        throw new ValidationError("Discount must be between 0 and 1.");
    }

    if (Number.isNaN(Date.parse(record.date))) {
        throw new ValidationError("Invalid transaction date.");
    }
}

class SalesTransaction {
    constructor(data) {
        validateRecord(data);

        this.id = data.id;
        this.date = data.date;
        this.region = data.region;
        this.city = data.city;
        this.category = data.category;
        this.product = data.product;
        this.salesperson = data.salesperson;
        this.quantity = data.quantity;
        this.unitPrice = data.unitPrice;
        this.discount = data.discount;

        Object.freeze(this);
    }

    get grossSales() {
        return this.quantity * this.unitPrice;
    }

    get netSales() {
        return this.grossSales * (1 - this.discount);
    }

    get profit() {
        return this.netSales * 0.25;
    }

    get month() {
        return this.date.slice(0, 7);
    }

    value(field) {
        if (field === "netSales") return this.netSales;
        if (field === "grossSales") return this.grossSales;
        if (field === "profit") return this.profit;
        if (field === "month") return this.month;

        if (!(field in this)) {
            throw new ValidationError(`Unknown field: ${field}`);
        }

        return this[field];
    }
}

class DashboardStore extends EventEmitter {
    constructor(records) {
        super();

        if (!Array.isArray(records) || records.length === 0) {
            throw new ValidationError("Dataset must contain records.");
        }

        this.records = records.map(
            record => new SalesTransaction(record)
        );

        const identifiers = new Set();

        for (const record of this.records) {
            if (identifiers.has(record.id)) {
                throw new ValidationError(
                    `Duplicate transaction ID: ${record.id}`
                );
            }
            identifiers.add(record.id);
        }

        this.revision = 1;
    }

    snapshot() {
        return {
            revision: this.revision,
            records: this.records
        };
    }

    async replaceRecords(rawRecords) {
        // Build and validate a replacement before changing current state.
        const replacement = rawRecords.map(
            record => new SalesTransaction(record)
        );

        const identifiers = new Set();

        for (const record of replacement) {
            if (identifiers.has(record.id)) {
                throw new ValidationError("Duplicate transaction ID.");
            }
            identifiers.add(record.id);
        }

        if (replacement.length === 0) {
            throw new ValidationError("Replacement dataset is empty.");
        }

        this.records = replacement;
        this.revision++;

        this.emit("data:refreshed", {
            revision: this.revision,
            recordCount: this.records.length
        });

        return this.snapshot();
    }
}

class FilterEngine {
    constructor() {
        this.filters = new Map();
        this.version = 0;
    }

    set(field, condition) {
        if (typeof field !== "string" || !field.trim()) {
            throw new ValidationError("Filter field is required.");
        }

        if (condition === undefined || condition === null) {
            throw new ValidationError("Filter condition is required.");
        }

        if (condition && typeof condition === "object" &&
            !Array.isArray(condition) &&
            !(condition instanceof Set)) {
            const { min, max } = condition;

            if (typeof min !== "number" ||
                typeof max !== "number" ||
                min > max) {
                throw new ValidationError("Invalid range condition.");
            }
        }

        this.filters.set(field, clone(condition));
        this.version++;
    }

    remove(field) {
        if (this.filters.delete(field)) {
            this.version++;
        }
    }

    clear() {
        if (this.filters.size > 0) {
            this.filters.clear();
            this.version++;
        }
    }

    matches(record) {
        for (const [field, condition] of this.filters) {
            const actual = record.value(field);

            if (condition instanceof Set) {
                if (!condition.has(actual)) return false;
            } else if (Array.isArray(condition)) {
                if (!condition.includes(actual)) return false;
            } else if (typeof condition === "object") {
                if (actual < condition.min || actual > condition.max) {
                    return false;
                }
            } else if (actual !== condition) {
                return false;
            }
        }

        return true;
    }

    apply(records) {
        return records.filter(record => this.matches(record));
    }

    exportState() {
        return [...this.filters.entries()].map(
            ([field, condition]) => [
                field,
                condition instanceof Set
                    ? { type: "set", values: [...condition] }
                    : clone(condition)
            ]
        );
    }

    importState(state) {
        const replacement = new Map();

        for (const [field, condition] of state) {
            if (condition &&
                typeof condition === "object" &&
                condition.type === "set") {
                replacement.set(field, new Set(condition.values));
            } else {
                replacement.set(field, clone(condition));
            }
        }

        this.filters = replacement;
        this.version++;
    }
}

class VisualEngine {
    static aggregate(records, field, operation) {
        const values = records.map(record => record.value(field));

        if (values.length === 0) return 0;

        switch (operation) {
            case Aggregation.SUM:
                return round(values.reduce((a, b) => a + b, 0));

            case Aggregation.COUNT:
                return values.length;

            case Aggregation.AVERAGE:
                return round(
                    values.reduce((a, b) => a + b, 0) / values.length
                );

            case Aggregation.MIN:
                return Math.min(...values);

            case Aggregation.MAX:
                return Math.max(...values);

            case Aggregation.DISTINCT:
                return new Set(values).size;

            default:
                throw new ValidationError("Unsupported aggregation.");
        }
    }

    static card(records, measure) {
        return {
            type: Visualization.CARD,
            measure,
            value: this.aggregate(records, measure, Aggregation.SUM),
            recordCount: records.length
        };
    }

    static table(records, dimensions, measures) {
        if (!dimensions.length) {
            throw new ValidationError("Table requires dimensions.");
        }

        const groups = new Map();

        for (const record of records) {
            const values = dimensions.map(
                field => record.value(field)
            );

            const key = JSON.stringify(values);

            if (!groups.has(key)) {
                groups.set(key, {
                    dimensions: Object.fromEntries(
                        dimensions.map((field, index) => [
                            field,
                            values[index]
                        ])
                    ),
                    records: []
                });
            }

            groups.get(key).records.push(record);
        }

        return [...groups.values()]
            .map(group => {
                const row = { ...group.dimensions };

                for (const measure of measures) {
                    row[measure] = this.aggregate(
                        group.records,
                        measure,
                        Aggregation.SUM
                    );
                }

                return row;
            })
            .sort((a, b) =>
                JSON.stringify(a).localeCompare(JSON.stringify(b))
            );
    }

    static matrix(records, rowField, columnField, measure) {
        const rows = new Set();
        const columns = new Set();
        const cells = new Map();

        for (const record of records) {
            const row = record.value(rowField);
            const column = record.value(columnField);
            const key = JSON.stringify([row, column]);

            rows.add(row);
            columns.add(column);

            cells.set(
                key,
                (cells.get(key) || 0) + record.value(measure)
            );
        }

        const sortedRows = [...rows].sort();
        const sortedColumns = [...columns].sort();

        const output = sortedRows.map(row => {
            const result = { [rowField]: row };
            let total = 0;

            for (const column of sortedColumns) {
                const value = round(
                    cells.get(JSON.stringify([row, column])) || 0
                );

                result[column] = value;
                total += value;
            }

            result.total = round(total);
            return result;
        });

        return {
            type: Visualization.MATRIX,
            rowField,
            columnField,
            measure,
            columns: sortedColumns,
            rows: output
        };
    }

    static chart(records, dimension, measure, type) {
        const supported = [
            Visualization.BAR,
            Visualization.LINE,
            Visualization.PIE
        ];

        if (!supported.includes(type)) {
            throw new ValidationError("Unsupported chart type.");
        }

        const groups = new Map();

        for (const record of records) {
            const key = record.value(dimension);
            groups.set(
                key,
                (groups.get(key) || 0) + record.value(measure)
            );
        }

        return {
            type,
            dimension,
            measure,
            data: [...groups.entries()]
                .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
                .map(([label, value]) => ({
                    label,
                    value: round(value)
                }))
        };
    }

    static map(records) {
        const groups = new Map();

        for (const record of records) {
            const key = JSON.stringify([
                record.region,
                record.city
            ]);

            if (!groups.has(key)) {
                groups.set(key, {
                    region: record.region,
                    city: record.city,
                    netSales: 0,
                    transactionCount: 0
                });
            }

            const location = groups.get(key);
            location.netSales += record.netSales;
            location.transactionCount++;
        }

        return {
            type: Visualization.MAP,
            locations: [...groups.values()].map(location => ({
                ...location,
                netSales: round(location.netSales)
            })),
            geocodingRequired: true
        };
    }
}

class BookmarkManager {
    constructor() {
        this.bookmarks = new Map();
    }

    save(name, filterState, selectedVisual) {
        if (!name || !name.trim()) {
            throw new ValidationError("Bookmark name is required.");
        }

        this.bookmarks.set(name, Object.freeze({
            filterState: clone(filterState),
            selectedVisual
        }));
    }

    restore(name) {
        const bookmark = this.bookmarks.get(name);

        if (!bookmark) {
            throw new NavigationError(`Bookmark not found: ${name}`);
        }

        return clone(bookmark);
    }

    remove(name) {
        this.bookmarks.delete(name);
    }
}

class DashboardController extends EventEmitter {
    constructor(store) {
        super();

        this.store = store;
        this.filters = new FilterEngine();
        this.bookmarks = new BookmarkManager();
        this.selectedVisual = null;
        this.navigationStack = [];

        this.store.on("data:refreshed", event => {
            this.emit("dashboard:invalidated", event);
        });
    }

    get records() {
        return this.filters.apply(this.store.records);
    }

    setSlicer(field, condition) {
        this.filters.set(field, condition);

        this.emit("slicer:changed", {
            field,
            filters: this.filters.exportState(),
            visibleRecords: this.records.length
        });
    }

    clearSlicers() {
        this.filters.clear();

        this.emit("slicer:cleared", {
            visibleRecords: this.records.length
        });
    }

    render(type, configuration = {}) {
        const records = this.records;

        let result;

        switch (type) {
            case Visualization.CARD:
                result = VisualEngine.card(
                    records,
                    configuration.measure || "netSales"
                );
                break;

            case Visualization.TABLE:
                result = VisualEngine.table(
                    records,
                    configuration.dimensions || ["region"],
                    configuration.measures || ["netSales"]
                );
                break;

            case Visualization.MATRIX:
                result = VisualEngine.matrix(
                    records,
                    configuration.rowField || "region",
                    configuration.columnField || "category",
                    configuration.measure || "netSales"
                );
                break;

            case Visualization.BAR:
            case Visualization.LINE:
            case Visualization.PIE:
                result = VisualEngine.chart(
                    records,
                    configuration.dimension || "category",
                    configuration.measure || "netSales",
                    type
                );
                break;

            case Visualization.MAP:
                result = VisualEngine.map(records);
                break;

            default:
                throw new ValidationError("Unknown visualization.");
        }

        this.emit("visual:rendered", { type, result });
        return result;
    }

    selectVisual(name) {
        if (!name) {
            throw new ValidationError("Visual name is required.");
        }

        this.selectedVisual = name;
        this.emit("visual:selected", { name });
    }

    drillThrough(field, value, targetPage) {
        if (!targetPage) {
            throw new NavigationError("Target page is required.");
        }

        const matching = this.records.filter(
            record => record.value(field) === value
        );

        if (matching.length === 0) {
            throw new NavigationError("No matching detail records.");
        }

        this.navigationStack.push({
            sourceVisual: this.selectedVisual,
            sourceFilters: this.filters.exportState(),
            targetPage
        });

        const result = matching.map(record => ({
            id: record.id,
            date: record.date,
            region: record.region,
            city: record.city,
            category: record.category,
            product: record.product,
            quantity: record.quantity,
            netSales: round(record.netSales)
        }));

        this.emit("navigation:drillthrough", {
            field,
            value,
            targetPage,
            recordCount: result.length
        });

        return result;
    }

    goBack() {
        const previous = this.navigationStack.pop();

        if (!previous) {
            throw new NavigationError("Navigation history is empty.");
        }

        this.filters.importState(previous.sourceFilters);
        this.selectedVisual = previous.sourceVisual;

        this.emit("navigation:back", previous);
        return previous;
    }

    saveBookmark(name) {
        this.bookmarks.save(
            name,
            this.filters.exportState(),
            this.selectedVisual
        );

        this.emit("bookmark:saved", { name });
    }

    restoreBookmark(name) {
        const state = this.bookmarks.restore(name);

        this.filters.importState(state.filterState);
        this.selectedVisual = state.selectedVisual;

        this.emit("bookmark:restored", { name });
    }

    async exportDashboard(filename) {
        const report = {
            generatedAt: new Date().toISOString(),
            datasetRevision: this.store.revision,
            filters: this.filters.exportState(),
            cards: {
                netSales: this.render(Visualization.CARD, {
                    measure: "netSales"
                }),
                profit: this.render(Visualization.CARD, {
                    measure: "profit"
                })
            },
            table: this.render(Visualization.TABLE, {
                dimensions: ["region", "category"],
                measures: ["netSales", "profit"]
            }),
            matrix: this.render(Visualization.MATRIX),
            barChart: this.render(Visualization.BAR),
            lineChart: this.render(Visualization.LINE, {
                dimension: "month"
            }),
            pieChart: this.render(Visualization.PIE),
            map: this.render(Visualization.MAP)
        };

        try {
            await fs.writeFile(
                filename,
                JSON.stringify(report, null, 2),
                { encoding: "utf8", flag: "w" }
            );

            this.emit("report:exported", { filename });
            return report;
        } catch (error) {
            throw new RefreshError(
                `Dashboard export failed: ${error.message}`
            );
        }
    }
}

function sampleRecords() {
    return [
        {
            id: 1, date: "2026-01-05", region: "North",
            city: "Delhi", category: "Electronics", product: "Laptop",
            salesperson: "Amit", quantity: 2,
            unitPrice: 65000, discount: 0.05
        },
        {
            id: 2, date: "2026-01-12", region: "North",
            city: "Lucknow", category: "Furniture", product: "Chair",
            salesperson: "Neha", quantity: 5,
            unitPrice: 4500, discount: 0.10
        },
        {
            id: 3, date: "2026-02-08", region: "South",
            city: "Bengaluru", category: "Electronics", product: "Mobile",
            salesperson: "Rahul", quantity: 4,
            unitPrice: 30000, discount: 0.08
        },
        {
            id: 4, date: "2026-02-15", region: "West",
            city: "Mumbai", category: "Clothing", product: "Jacket",
            salesperson: "Priya", quantity: 8,
            unitPrice: 2500, discount: 0.05
        },
        {
            id: 5, date: "2026-03-03", region: "East",
            city: "Kolkata", category: "Furniture", product: "Table",
            salesperson: "Amit", quantity: 3,
            unitPrice: 12000, discount: 0.12
        },
        {
            id: 6, date: "2026-03-18", region: "North",
            city: "Delhi", category: "Clothing", product: "Shirt",
            salesperson: "Neha", quantity: 10,
            unitPrice: 1200, discount: 0.02
        },
        {
            id: 7, date: "2026-04-10", region: "South",
            city: "Chennai", category: "Electronics", product: "Laptop",
            salesperson: "Rahul", quantity: 1,
            unitPrice: 70000, discount: 0.04
        },
        {
            id: 8, date: "2026-04-20", region: "West",
            city: "Pune", category: "Furniture", product: "Chair",
            salesperson: "Priya", quantity: 6,
            unitPrice: 5000, discount: 0.07
        }
    ];
}

async function main() {
    const store = new DashboardStore(sampleRecords());
    const dashboard = new DashboardController(store);

    dashboard.on("slicer:changed", event => {
        console.log(
            "Slicer changed:",
            event.field,
            "Visible records:",
            event.visibleRecords
        );
    });

    dashboard.on("navigation:drillthrough", event => {
        console.log("Drill-through:", event.targetPage);
    });

    dashboard.on("bookmark:restored", event => {
        console.log("Bookmark restored:", event.name);
    });

    console.log("\nPOWER BI DASHBOARD");
    console.log("==============================");

    console.log("\nCARD");
    console.log(dashboard.render(Visualization.CARD));

    console.log("\nTABLE");
    console.table(dashboard.render(Visualization.TABLE, {
        dimensions: ["region", "category"],
        measures: ["netSales", "profit"]
    }));

    console.log("\nMATRIX");
    console.dir(dashboard.render(Visualization.MATRIX), {
        depth: null
    });

    console.log("\nBAR CHART");
    console.dir(dashboard.render(Visualization.BAR), {
        depth: null
    });

    console.log("\nLINE CHART");
    console.dir(dashboard.render(Visualization.LINE, {
        dimension: "month"
    }), { depth: null });

    console.log("\nPIE CHART");
    console.dir(dashboard.render(Visualization.PIE), {
        depth: null
    });

    console.log("\nMAP");
    console.dir(dashboard.render(Visualization.MAP), {
        depth: null
    });

    console.log("\nSLICER AND CROSS-FILTERING");
    dashboard.setSlicer("region", ["North", "South"]);
    dashboard.setSlicer("category", "Electronics");

    console.log("Filtered KPI:", dashboard.render(
        Visualization.CARD
    ));

    console.log("\nDRILL-THROUGH");
    dashboard.selectVisual("regional-sales");
    console.table(
        dashboard.drillThrough("region", "North", "Transaction Details")
    );

    console.log("\nBOOKMARK");
    dashboard.saveBookmark("Regional Analysis");
    dashboard.clearSlicers();
    dashboard.restoreBookmark("Regional Analysis");

    console.log("\nASYNC DATA REFRESH");
    await store.replaceRecords(sampleRecords());
    console.log("Dataset revision:", store.revision);

    console.log("\nREPORT EXPORT");
    await dashboard.exportDashboard(
        "powerbi_dashboard_report.json"
    );
    console.log("Export completed.");

    console.log("\nERROR HANDLING");

    try {
        dashboard.drillThrough(
            "region",
            "Unknown",
            "Transaction Details"
        );
    } catch (error) {
        console.log(error.name + ":", error.message);
    }
}

main().catch(error => {
    console.error("Dashboard execution failed:", error);
    process.exitCode = 1;
});
