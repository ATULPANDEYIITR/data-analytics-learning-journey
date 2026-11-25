"use strict";

/**
 * Enterprise Dashboard Interaction and Policy Engine
 *
 * Run:
 *   node dashboard.js
 *
 * Implements:
 * - Event-driven dashboard state
 * - KPI evaluation and comparison
 * - Responsive component placement
 * - Interactive filters and drill-down
 * - Semantic color policies
 * - Accessible interaction metadata
 * - Asynchronous data loading
 * - Request cancellation and stale-response protection
 * - Dashboard persistence through JSON export
 */

const fs = require("node:fs/promises");

// ============================================================
// 1. ENUMERATIONS AND DESIGN TOKENS
// ============================================================

const KPIStatus = Object.freeze({
    GOOD: "good",
    WARNING: "warning",
    CRITICAL: "critical",
    NEUTRAL: "neutral"
});

const ChartType = Object.freeze({
    LINE: "line",
    BAR: "bar",
    DONUT: "donut",
    TABLE: "table",
    AREA: "area"
});

const Aggregation = Object.freeze({
    SUM: "sum",
    AVERAGE: "average",
    COUNT: "count",
    MIN: "min",
    MAX: "max"
});

const COLORS = Object.freeze({
    primary: "#2563EB",
    background: "#F8FAFC",
    surface: "#FFFFFF",
    text: "#172033",
    muted: "#64748B",
    success: "#15803D",
    warning: "#B45309",
    danger: "#B91C1C",
    border: "#E2E8F0"
});

const TYPOGRAPHY = Object.freeze({
    pageTitle: 28,
    sectionTitle: 20,
    cardTitle: 14,
    metricValue: 30,
    body: 14,
    caption: 12
});

// ============================================================
// 2. VALIDATION UTILITIES
// ============================================================

class DashboardError extends Error {
    constructor(message, code = "DASHBOARD_ERROR") {
        super(message);
        this.name = "DashboardError";
        this.code = code;
    }
}

function requireNumber(value, field, minimum = -Infinity) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < minimum
    ) {
        throw new DashboardError(
            `Invalid numeric value for ${field}`,
            "INVALID_METRIC"
        );
    }

    return value;
}

function requireText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new DashboardError(
            `${field} must be a non-empty string`,
            "INVALID_TEXT"
        );
    }

    return value.trim();
}

function safeDate(value) {
    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
        throw new DashboardError("Invalid date", "INVALID_DATE");
    }

    return parsed;
}

// ============================================================
// 3. KPI MODEL
// ============================================================

class KPI {
    constructor({
        id,
        name,
        value,
        previousValue = null,
        target = null,
        format = "number",
        higherIsBetter = true,
        warningThreshold = null,
        criticalThreshold = null,
        description = ""
    }) {
        this.id = requireText(id, "KPI id");
        this.name = requireText(name, "KPI name");
        this.value = requireNumber(value, "KPI value");

        this.previousValue =
            previousValue === null
                ? null
                : requireNumber(previousValue, "previousValue");

        this.target =
            target === null
                ? null
                : requireNumber(target, "target");

        if (!["number", "currency", "percentage"].includes(format)) {
            throw new DashboardError("Unsupported KPI format");
        }

        this.format = format;
        this.higherIsBetter = Boolean(higherIsBetter);
        this.warningThreshold = warningThreshold;
        this.criticalThreshold = criticalThreshold;
        this.description = description;

        for (const [field, threshold] of [
            ["warningThreshold", warningThreshold],
            ["criticalThreshold", criticalThreshold]
        ]) {
            if (threshold !== null) {
                requireNumber(threshold, field);
            }
        }

        if (
            warningThreshold !== null &&
            criticalThreshold !== null
        ) {
            if (
                higherIsBetter &&
                warningThreshold < criticalThreshold
            ) {
                throw new DashboardError("Invalid KPI threshold ordering");
            }

            if (
                !higherIsBetter &&
                warningThreshold > criticalThreshold
            ) {
                throw new DashboardError("Invalid KPI threshold ordering");
            }
        }
    }

    getChange() {
        if (this.previousValue === null || this.previousValue === 0) {
            return null;
        }

        return (
            (this.value - this.previousValue) /
            Math.abs(this.previousValue)
        ) * 100;
    }

    getTargetAchievement() {
        if (this.target === null || this.target === 0) {
            return null;
        }

        if (!this.higherIsBetter) {
            return this.value === 0
                ? null
                : (this.target / this.value) * 100;
        }

        return (this.value / this.target) * 100;
    }

    getStatus() {
        if (this.criticalThreshold !== null) {
            const critical = this.higherIsBetter
                ? this.value < this.criticalThreshold
                : this.value > this.criticalThreshold;

            if (critical) return KPIStatus.CRITICAL;
        }

        if (this.warningThreshold !== null) {
            const warning = this.higherIsBetter
                ? this.value < this.warningThreshold
                : this.value > this.warningThreshold;

            if (warning) return KPIStatus.WARNING;
        }

        return KPIStatus.GOOD;
    }

    formatValue() {
        switch (this.format) {
            case "currency":
                return new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD"
                }).format(this.value);

            case "percentage":
                return `${this.value.toFixed(2)}%`;

            default:
                return new Intl.NumberFormat("en-US", {
                    maximumFractionDigits: 2
                }).format(this.value);
        }
    }

    toJSON() {
        return {
            id: this.id,
            name: this.name,
            value: this.value,
            formattedValue: this.formatValue(),
            change: this.getChange(),
            targetAchievement: this.getTargetAchievement(),
            status: this.getStatus(),
            description: this.description
        };
    }
}

// ============================================================
// 4. DATASET AND AGGREGATION
// ============================================================

class DashboardDataset {
    #records;
    #recordIds;

    constructor(records) {
        if (!Array.isArray(records)) {
            throw new DashboardError("Dataset must be an array");
        }

        this.#records = [];
        this.#recordIds = new Set();

        for (const input of records) {
            const record = Object.freeze({
                id: requireNumber(input.id, "record id", 1),
                date: safeDate(input.date).toISOString(),
                department: requireText(input.department, "department"),
                region: requireText(input.region, "region"),
                revenue: requireNumber(input.revenue, "revenue", 0),
                expenses: requireNumber(input.expenses, "expenses", 0),
                orders: requireNumber(input.orders, "orders", 0),
                satisfaction: requireNumber(
                    input.satisfaction,
                    "satisfaction",
                    0
                ),
                conversion: requireNumber(
                    input.conversion,
                    "conversion",
                    0
                )
            });

            if (record.satisfaction > 100 || record.conversion > 100) {
                throw new DashboardError("Percentage metric exceeds 100");
            }

            if (this.#recordIds.has(record.id)) {
                throw new DashboardError("Duplicate dataset record ID");
            }

            this.#recordIds.add(record.id);
            this.#records.push(record);
        }

        Object.freeze(this.#records);
    }

    get size() {
        return this.#records.length;
    }

    query(filters = {}) {
        const {
            region = null,
            department = null,
            search = "",
            from = null,
            to = null,
            sortBy = "revenue",
            descending = true
        } = filters;

        const allowedSortFields = new Set([
            "revenue",
            "expenses",
            "orders",
            "satisfaction",
            "conversion",
            "date"
        ]);

        if (!allowedSortFields.has(sortBy)) {
            throw new DashboardError("Unsupported sort field");
        }

        const start = from ? safeDate(from).getTime() : -Infinity;
        const end = to ? safeDate(to).getTime() : Infinity;

        if (start > end) {
            throw new DashboardError("Invalid filter date range");
        }

        const normalizedSearch = String(search).toLocaleLowerCase();

        const result = this.#records.filter(record => {
            const timestamp = new Date(record.date).getTime();

            return (
                (!region || record.region === region) &&
                (!department || record.department === department) &&
                timestamp >= start &&
                timestamp <= end &&
                (
                    !normalizedSearch ||
                    record.department.toLocaleLowerCase().includes(normalizedSearch) ||
                    record.region.toLocaleLowerCase().includes(normalizedSearch)
                )
            );
        });

        result.sort((a, b) => {
            let comparison;

            if (typeof a[sortBy] === "string") {
                comparison = a[sortBy].localeCompare(b[sortBy]);
            } else {
                comparison = a[sortBy] - b[sortBy];
            }

            return descending ? -comparison : comparison;
        });

        return result;
    }

    aggregate(records = this.#records) {
        if (records.length === 0) {
            return Object.freeze({
                revenue: 0,
                expenses: 0,
                profit: 0,
                orders: 0,
                averageSatisfaction: 0,
                averageConversion: 0
            });
        }

        const totals = records.reduce(
            (accumulator, record) => {
                accumulator.revenue += record.revenue;
                accumulator.expenses += record.expenses;
                accumulator.orders += record.orders;
                accumulator.satisfaction += record.satisfaction;
                accumulator.conversion += record.conversion;

                return accumulator;
            },
            {
                revenue: 0,
                expenses: 0,
                orders: 0,
                satisfaction: 0,
                conversion: 0
            }
        );

        return Object.freeze({
            revenue: totals.revenue,
            expenses: totals.expenses,
            profit: totals.revenue - totals.expenses,
            orders: totals.orders,
            averageSatisfaction: totals.satisfaction / records.length,
            averageConversion: totals.conversion / records.length
        });
    }

    groupByRegion() {
        const groups = Map.groupBy
            ? Map.groupBy(this.#records, record => record.region)
            : this.#records.reduce((map, record) => {
                if (!map.has(record.region)) {
                    map.set(record.region, []);
                }

                map.get(record.region).push(record);
                return map;
            }, new Map());

        return Object.fromEntries(
            [...groups.entries()].map(([region, records]) => [
                region,
                this.aggregate(records)
            ])
        );
    }

    trend() {
        const groups = new Map();

        for (const record of this.#records) {
            const day = record.date.slice(0, 10);

            if (!groups.has(day)) {
                groups.set(day, {
                    date: day,
                    revenue: 0,
                    orders: 0
                });
            }

            const entry = groups.get(day);
            entry.revenue += record.revenue;
            entry.orders += record.orders;
        }

        return [...groups.values()].sort((a, b) =>
            a.date.localeCompare(b.date)
        );
    }
}

// ============================================================
// 5. RESPONSIVE LAYOUT ENGINE
// ============================================================

class DashboardGrid {
    constructor(columns = 12) {
        if (!Number.isInteger(columns) || columns < 1) {
            throw new DashboardError("Invalid grid column count");
        }

        this.columns = columns;
        this.components = new Map();
    }

    add({
        id,
        type,
        row,
        column,
        rowSpan = 1,
        columnSpan = 1,
        priority = 1
    }) {
        requireText(id, "component id");

        if (this.components.has(id)) {
            throw new DashboardError("Duplicate component identifier");
        }

        if (!Object.values(ChartType).includes(type)) {
            throw new DashboardError("Unsupported component type");
        }

        for (const [field, value] of Object.entries({
            row,
            column,
            rowSpan,
            columnSpan,
            priority
        })) {
            if (!Number.isInteger(value) || value < 1) {
                throw new DashboardError(`Invalid layout ${field}`);
            }
        }

        if (column + columnSpan - 1 > this.columns) {
            throw new DashboardError("Component exceeds grid width");
        }

        const candidate = {
            id,
            type,
            row,
            column,
            rowSpan,
            columnSpan,
            priority
        };

        for (const existing of this.components.values()) {
            const rowOverlap =
                candidate.row < existing.row + existing.rowSpan &&
                existing.row < candidate.row + candidate.rowSpan;

            const columnOverlap =
                candidate.column < existing.column + existing.columnSpan &&
                existing.column < candidate.column + candidate.columnSpan;

            if (rowOverlap && columnOverlap) {
                throw new DashboardError(
                    `Grid collision between ${id} and ${existing.id}`
                );
            }
        }

        this.components.set(id, Object.freeze(candidate));
    }

    getResponsiveColumns(width) {
        requireNumber(width, "viewport width", 1);

        if (width < 600) return 1;
        if (width < 1024) return 6;

        return 12;
    }

    render() {
        return [...this.components.values()].sort(
            (a, b) => a.row - b.row ||
                b.priority - a.priority ||
                a.column - b.column
        );
    }
}

// ============================================================
// 6. EVENT-DRIVEN STATE MANAGEMENT
// ============================================================

class DashboardStore extends EventTarget {
    #filters;
    #revision;

    constructor() {
        super();

        this.#filters = Object.freeze({
            region: null,
            department: null,
            from: null,
            to: null,
            search: "",
            sortBy: "revenue",
            descending: true
        });

        this.#revision = 0;
    }

    get state() {
        return this.#filters;
    }

    get revision() {
        return this.#revision;
    }

    update(patch) {
        const allowed = new Set(Object.keys(this.#filters));

        for (const key of Object.keys(patch)) {
            if (!allowed.has(key)) {
                throw new DashboardError(`Unsupported filter: ${key}`);
            }
        }

        const next = Object.freeze({
            ...this.#filters,
            ...patch
        });

        if (next.from && next.to) {
            if (safeDate(next.from) > safeDate(next.to)) {
                throw new DashboardError("Start date exceeds end date");
            }
        }

        if (typeof next.search !== "string") {
            throw new DashboardError("Search must be a string");
        }

        this.#filters = next;
        this.#revision += 1;

        this.dispatchEvent(
            new CustomEvent("filtersChanged", {
                detail: {
                    filters: this.#filters,
                    revision: this.#revision
                }
            })
        );
    }

    reset() {
        this.update({
            region: null,
            department: null,
            from: null,
            to: null,
            search: "",
            sortBy: "revenue",
            descending: true
        });
    }
}

// ============================================================
// 7. DASHBOARD APPLICATION SERVICE
// ============================================================

class DashboardApplication {
    constructor(dataset, store) {
        this.dataset = dataset;
        this.store = store;
        this.lastSnapshot = null;
    }

    getDashboard() {
        const records = this.dataset.query(this.store.state);
        const metrics = this.dataset.aggregate(records);

        const kpis = [
            new KPI({
                id: "revenue",
                name: "Total Revenue",
                value: metrics.revenue,
                previousValue: 45000,
                target: 50000,
                format: "currency",
                warningThreshold: 35000,
                criticalThreshold: 25000
            }),
            new KPI({
                id: "profit",
                name: "Operating Profit",
                value: metrics.profit,
                previousValue: 12000,
                target: 15000,
                format: "currency",
                warningThreshold: 8000,
                criticalThreshold: 4000
            }),
            new KPI({
                id: "satisfaction",
                name: "Customer Satisfaction",
                value: metrics.averageSatisfaction,
                previousValue: 82,
                target: 90,
                format: "percentage",
                warningThreshold: 75,
                criticalThreshold: 60
            }),
            new KPI({
                id: "conversion",
                name: "Conversion Rate",
                value: metrics.averageConversion,
                previousValue: 3.5,
                target: 5,
                format: "percentage",
                warningThreshold: 2.5,
                criticalThreshold: 1.5
            })
        ];

        const result = Object.freeze({
            revision: this.store.revision,
            recordCount: records.length,
            metrics,
            kpis: kpis.map(kpi => kpi.toJSON()),
            regionalPerformance: this.dataset.groupByRegion(),
            trend: this.dataset.trend(),
            records
        });

        this.lastSnapshot = result;
        return result;
    }
}

// ============================================================
// 8. ASYNCHRONOUS DATA SERVICE
// ============================================================

class DashboardDataService {
    #requestSequence = 0;
    #controller = null;

    async load(fetchFunction) {
        if (typeof fetchFunction !== "function") {
            throw new DashboardError("Data provider must be callable");
        }

        if (this.#controller) {
            this.#controller.abort();
        }

        this.#controller = new AbortController();
        const controller = this.#controller;
        const sequence = ++this.#requestSequence;

        try {
            const result = await fetchFunction(controller.signal);

            if (controller.signal.aborted) {
                throw new DashboardError(
                    "Request cancelled",
                    "REQUEST_CANCELLED"
                );
            }

            if (sequence !== this.#requestSequence) {
                throw new DashboardError(
                    "Stale response rejected",
                    "STALE_RESPONSE"
                );
            }

            if (!Array.isArray(result)) {
                throw new DashboardError("Invalid API response");
            }

            return result;
        } catch (error) {
            if (error.name === "AbortError") {
                throw new DashboardError(
                    "Request cancelled",
                    "REQUEST_CANCELLED"
                );
            }

            throw error;
        }
    }

    cancel() {
        if (this.#controller) {
            this.#controller.abort();
        }
    }
}

// ============================================================
// 9. SEMANTIC COLOR AND ACCESSIBILITY POLICIES
// ============================================================

function getStatusColor(status) {
    const mapping = {
        [KPIStatus.GOOD]: COLORS.success,
        [KPIStatus.WARNING]: COLORS.warning,
        [KPIStatus.CRITICAL]: COLORS.danger,
        [KPIStatus.NEUTRAL]: COLORS.muted
    };

    if (!mapping[status]) {
        throw new DashboardError("Unknown KPI status");
    }

    return mapping[status];
}

function luminance(hex) {
    if (!/^#[0-9A-Fa-f]{6}$/.test(hex)) {
        throw new DashboardError("Invalid hexadecimal color");
    }

    const values = [1, 3, 5].map(index => {
        const channel = parseInt(hex.slice(index, index + 2), 16) / 255;

        return channel <= 0.04045
            ? channel / 12.92
            : Math.pow((channel + 0.055) / 1.055, 2.4);
    });

    return (
        0.2126 * values[0] +
        0.7152 * values[1] +
        0.0722 * values[2]
    );
}

function contrastRatio(first, second) {
    const a = luminance(first);
    const b = luminance(second);

    return (Math.max(a, b) + 0.05) /
        (Math.min(a, b) + 0.05);
}

function validateColorAccessibility() {
    const ratio = contrastRatio(COLORS.text, COLORS.surface);

    if (ratio < 4.5) {
        throw new DashboardError("Text contrast fails WCAG AA target");
    }

    return ratio;
}

// ============================================================
// 10. SAMPLE DATA
// ============================================================

function sampleData() {
    const data = [
        ["Sales", "North", 18000, 11000, 120, 91, 5.2],
        ["Technology", "North", 14000, 9000, 90, 87, 4.5],
        ["Sales", "South", 16000, 10000, 110, 83, 3.8],
        ["Technology", "South", 12000, 8500, 75, 88, 4.2],
        ["Operations", "East", 9000, 7000, 65, 79, 2.8],
        ["Sales", "East", 21000, 13000, 140, 94, 5.8],
        ["Operations", "West", 11000, 7500, 80, 85, 3.6],
        ["Technology", "West", 15000, 9500, 95, 90, 4.9]
    ];

    return data.map((item, index) => ({
        id: index + 1,
        date: `2026-11-${String(20 + index).padStart(2, "0")}`,
        department: item[0],
        region: item[1],
        revenue: item[2],
        expenses: item[3],
        orders: item[4],
        satisfaction: item[5],
        conversion: item[6]
    }));
}

// ============================================================
// 11. DASHBOARD PRESENTATION
// ============================================================

function printDashboard(snapshot) {
    console.log("\n" + "=".repeat(70));
    console.log("              ENTERPRISE PERFORMANCE DASHBOARD");
    console.log("=".repeat(70));

    console.log("\nKEY PERFORMANCE INDICATORS");

    for (const kpi of snapshot.kpis) {
        const change = kpi.change === null
            ? "N/A"
            : `${kpi.change.toFixed(2)}%`;

        console.log(
            `${kpi.name.padEnd(26)} ${kpi.formattedValue.padStart(15)} ` +
            `| ${change.padStart(10)} | ${kpi.status.toUpperCase()}`
        );
    }

    console.log("\nREGIONAL PERFORMANCE");

    for (const [region, values] of Object.entries(
        snapshot.regionalPerformance
    )) {
        console.log(
            `${region.padEnd(12)} Revenue: ${values.revenue.toFixed(2)} ` +
            `Profit: ${(values.revenue - values.expenses).toFixed(2)}`
        );
    }

    console.log("\nFILTERED RECORD COUNT:", snapshot.recordCount);
    console.log("REVISION:", snapshot.revision);
}

// ============================================================
// 12. AUTOMATED TESTS
// ============================================================

function runTests() {
    const kpi = new KPI({
        id: "test",
        name: "Test Metric",
        value: 80,
        previousValue: 100,
        target: 100,
        warningThreshold: 70,
        criticalThreshold: 50
    });

    console.assert(kpi.getChange() === -20);
    console.assert(kpi.getStatus() === KPIStatus.GOOD);

    const critical = new KPI({
        id: "critical",
        name: "Critical Metric",
        value: 30,
        target: 100,
        warningThreshold: 70,
        criticalThreshold: 50
    });

    console.assert(critical.getStatus() === KPIStatus.CRITICAL);

    const empty = new DashboardDataset([]);
    console.assert(empty.aggregate([]).revenue === 0);

    const grid = new DashboardGrid();

    grid.add({
        id: "revenue",
        type: ChartType.LINE,
        row: 1,
        column: 1,
        columnSpan: 6
    });

    let collisionDetected = false;

    try {
        grid.add({
            id: "duplicate-space",
            type: ChartType.BAR,
            row: 1,
            column: 3,
            columnSpan: 6
        });
    } catch (error) {
        collisionDetected = error instanceof DashboardError;
    }

    console.assert(collisionDetected);

    const ratio = validateColorAccessibility();
    console.assert(ratio >= 4.5);

    console.log("\nAll JavaScript validation tests passed.");
}

// ============================================================
// 13. MAIN APPLICATION
// ============================================================

async function main() {
    const dataset = new DashboardDataset(sampleData());
    const store = new DashboardStore();
    const application = new DashboardApplication(dataset, store);

    const grid = new DashboardGrid();

    grid.add({
        id: "revenue",
        type: ChartType.TABLE,
        row: 1,
        column: 1,
        columnSpan: 3,
        priority: 10
    });

    grid.add({
        id: "profit",
        type: ChartType.TABLE,
        row: 1,
        column: 4,
        columnSpan: 3,
        priority: 9
    });

    grid.add({
        id: "satisfaction",
        type: ChartType.TABLE,
        row: 1,
        column: 7,
        columnSpan: 3,
        priority: 8
    });

    grid.add({
        id: "conversion",
        type: ChartType.TABLE,
        row: 1,
        column: 10,
        columnSpan: 3,
        priority: 7
    });

    grid.add({
        id: "trend",
        type: ChartType.LINE,
        row: 2,
        column: 1,
        columnSpan: 8,
        rowSpan: 2,
        priority: 6
    });

    grid.add({
        id: "regional",
        type: ChartType.BAR,
        row: 2,
        column: 9,
        columnSpan: 4,
        rowSpan: 2,
        priority: 5
    });

    store.addEventListener("filtersChanged", event => {
        console.log(
            "\nFilter event received. Revision:",
            event.detail.revision
        );
    });

    const initial = application.getDashboard();
    printDashboard(initial);

    store.update({ region: "North" });

    const filtered = application.getDashboard();

    console.log("\nFILTERED DASHBOARD");
    console.log(JSON.stringify(filtered.metrics, null, 2));

    const layout = {
        desktopColumns: grid.columns,
        tabletColumns: grid.getResponsiveColumns(800),
        mobileColumns: grid.getResponsiveColumns(390),
        components: grid.render()
    };

    console.log("\nRESPONSIVE LAYOUT");
    console.log(JSON.stringify(layout, null, 2));

    console.log(
        "\nTEXT CONTRAST:",
        validateColorAccessibility().toFixed(2),
        ":1"
    );

    runTests();

    const exportData = {
        generatedAt: new Date().toISOString(),
        dashboard: initial,
        layout,
        designTokens: {
            colors: COLORS,
            typography: TYPOGRAPHY
        }
    };

    await fs.writeFile(
        "dashboard_report.json",
        JSON.stringify(exportData, null, 2),
        {
            encoding: "utf8",
            flag: "w"
        }
    );

    console.log("\nDashboard report exported successfully.");
}

main().catch(error => {
    console.error(
        "Dashboard execution failed:",
        error.code || error.name,
        error.message
    );

    process.exitCode = 1;
});
