"use strict";

/*
 * Python for Analytics: JavaScript perspective on data collection,
 * numeric expressions, input validation, aggregation, and reporting.
 *
 * Run with Node.js:
 *     node python_for_analytics.js
 *
 * This implementation focuses on JavaScript-specific considerations:
 * Number precision, strict validation, Map-based aggregation, asynchronous
 * data ingestion, and safe JSON/CSV output.
 */

const { setTimeout: delay } = require("node:timers/promises");

function heading(title) {
    console.log(`\n${"=".repeat(68)}\n${title}\n${"=".repeat(68)}`);
}

function inspectValue(label, value) {
    console.log(`${label}: ${String(value)}; typeof=${typeof value}`);
}

function demonstrateDataTypes() {
    heading("Analytics values and JavaScript types");

    const department = "Operations";
    const employeeCount = 48;
    const monthlyBudget = 275000.5;
    const automationEnabled = true;
    const missingMeasurement = null;
    const uninitializedMeasurement = undefined;
    const dailyMeasurements = [12.5, 13, 11.8, 14.2];
    const employee = Object.freeze({
        employeeId: "E104",
        department,
        active: automationEnabled
    });

    inspectValue("Department", department);
    inspectValue("Employee count", employeeCount);
    inspectValue("Monthly budget", monthlyBudget);
    inspectValue("Automation enabled", automationEnabled);
    inspectValue("Explicit missing value", missingMeasurement);
    inspectValue("Uninitialized value", uninitializedMeasurement);

    console.log("Daily measurements:", dailyMeasurements);
    console.log("Employee record:", employee);
    console.log("Array detection:", Array.isArray(dailyMeasurements));

    // JavaScript's typeof null is "object", a historical language quirk.
    console.log("typeof null:", typeof null);
    console.log("Explicit null check:", missingMeasurement === null);
}

function parseFiniteNumber(value, fieldName) {
    if (typeof value === "boolean" || value === null || value === undefined) {
        throw new TypeError(`${fieldName} must be a numeric value`);
    }

    if (typeof value === "string" && value.trim() === "") {
        throw new TypeError(`${fieldName} cannot be empty`);
    }

    const parsed = Number(value);

    // Number("") and Number(null) produce zero, so these cases are rejected
    // before conversion instead of being silently interpreted as valid data.
    if (!Number.isFinite(parsed)) {
        throw new RangeError(`${fieldName} must be a finite number`);
    }

    return parsed;
}

function calculateOperatingMetrics({ revenue, cost, priorRevenue }) {
    const revenueValue = parseFiniteNumber(revenue, "revenue");
    const costValue = parseFiniteNumber(cost, "cost");
    const priorValue = parseFiniteNumber(priorRevenue, "priorRevenue");

    if (revenueValue < 0 || costValue < 0 || priorValue < 0) {
        throw new RangeError("Revenue and cost values cannot be negative");
    }

    const profit = revenueValue - costValue;

    return Object.freeze({
        revenue: revenueValue,
        cost: costValue,
        profit,
        marginPercent: revenueValue === 0 ? null : profit / revenueValue * 100,
        growthPercent: priorValue === 0
            ? null
            : (revenueValue - priorValue) / priorValue * 100
    });
}

function demonstrateExpressions() {
    heading("Operators, expressions, and numeric limits");

    const revenue = 850000;
    const operatingCost = 612500;
    const previousRevenue = 790000;
    const unitsSold = 1250;

    console.log("Profit:", revenue - operatingCost);
    console.log("Profit margin:", ((revenue - operatingCost) / revenue * 100).toFixed(2) + "%");
    console.log("Revenue growth:", ((revenue - previousRevenue) / previousRevenue * 100).toFixed(2) + "%");
    console.log("Average revenue per unit:", revenue / unitsSold);
    console.log("Remainder:", 17 % 5);
    console.log("Exponentiation:", 2 ** 8);
    console.log("Strict comparison:", revenue > operatingCost);
    console.log("Logical condition:", revenue > 0 && operatingCost >= 0);

    // Binary floating-point cannot exactly represent every decimal fraction.
    console.log("0.1 + 0.2:", 0.1 + 0.2);
    console.log("Number precision limit:", Number.MAX_SAFE_INTEGER);

    const metrics = calculateOperatingMetrics({
        revenue: "125000",
        cost: "92500",
        priorRevenue: "110000"
    });
    console.log("Validated metrics:", metrics);
}

function summarize(values) {
    if (!Array.isArray(values)) {
        throw new TypeError("Expected an array of observations");
    }

    const observations = values.filter(
        value => typeof value === "number" && Number.isFinite(value)
    );

    if (observations.length === 0) {
        return {
            count: 0,
            mean: null,
            minimum: null,
            maximum: null,
            median: null
        };
    }

    // A copied array prevents the sort operation from mutating the caller's data.
    const sorted = [...observations].sort((a, b) => a - b);
    const sum = observations.reduce((total, value) => total + value, 0);
    const middle = Math.floor(sorted.length / 2);
    const median = sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];

    return {
        count: observations.length,
        mean: sum / observations.length,
        minimum: sorted[0],
        maximum: sorted[sorted.length - 1],
        median
    };
}

function aggregateTransactions(records) {
    if (!Array.isArray(records)) {
        throw new TypeError("Transaction input must be an array");
    }

    const seenIds = new Set();
    const totalsByRegion = new Map();
    const accepted = [];
    const rejected = [];

    for (const record of records) {
        const errors = [];

        if (record === null || typeof record !== "object" || Array.isArray(record)) {
            rejected.push({ record, errors: ["Record must be an object"] });
            continue;
        }

        const transactionId = String(record.transactionId ?? "").trim();
        const region = String(record.region ?? "").trim();

        if (!transactionId) {
            errors.push("transactionId cannot be empty");
        } else if (seenIds.has(transactionId)) {
            errors.push(`Duplicate transactionId: ${transactionId}`);
        }

        if (!region) {
            errors.push("region cannot be empty");
        }

        let quantity;
        let unitPrice;

        try {
            quantity = parseFiniteNumber(record.quantity, "quantity");
            if (!Number.isSafeInteger(quantity) || quantity <= 0) {
                errors.push("quantity must be a positive safe integer");
            }
        } catch (error) {
            errors.push(error.message);
        }

        try {
            unitPrice = parseFiniteNumber(record.unitPrice, "unitPrice");
            if (unitPrice < 0) {
                errors.push("unitPrice cannot be negative");
            }
        } catch (error) {
            errors.push(error.message);
        }

        if (errors.length > 0) {
            rejected.push({ record, errors });
            continue;
        }

        seenIds.add(transactionId);

        const amount = quantity * unitPrice;
        if (!Number.isFinite(amount)) {
            rejected.push({
                record,
                errors: ["Calculated sales amount exceeds finite Number range"]
            });
            continue;
        }

        const acceptedRecord = Object.freeze({
            transactionId,
            region,
            quantity,
            unitPrice,
            amount
        });

        accepted.push(acceptedRecord);
        totalsByRegion.set(
            region,
            (totalsByRegion.get(region) ?? 0) + amount
        );
    }

    const totalSales = [...totalsByRegion.values()].reduce(
        (sum, amount) => sum + amount,
        0
    );

    return {
        accepted,
        rejected,
        totalsByRegion,
        totalSales
    };
}

async function loadTransactions(source, waitMilliseconds = 0) {
    // An asynchronous boundary models fetching records from a remote service.
    // Real applications should add request timeouts, cancellation, and retries.
    await delay(waitMilliseconds);

    if (!Array.isArray(source)) {
        throw new TypeError("The transaction source did not return an array");
    }

    return source;
}

function createCsvReport(aggregation) {
    const escapeCsv = value => {
        const text = String(value);
        return /[",\r\n]/.test(text)
            ? `"${text.replace(/"/g, '""')}"`
            : text;
    };

    const lines = [["region", "sales_amount", "share_percent"]];

    const regions = [...aggregation.totalsByRegion.entries()]
        .sort(([left], [right]) => left.localeCompare(right));

    for (const [region, amount] of regions) {
        const share = aggregation.totalSales === 0
            ? 0
            : amount / aggregation.totalSales * 100;

        lines.push([
            region,
            amount.toFixed(2),
            share.toFixed(2)
        ]);
    }

    return lines.map(row => row.map(escapeCsv).join(",")).join("\n") + "\n";
}

async function main() {
    demonstrateDataTypes();
    demonstrateExpressions();

    heading("Descriptive statistics");
    console.log("Order counts:", summarize([120, 135, 0, 148, null, 162, 155]));
    console.log("Empty observations:", summarize([]));

    heading("Asynchronous transaction analytics");

    const sourceRecords = [
        { transactionId: "TX-1001", region: "North", quantity: 12, unitPrice: 1499.5 },
        { transactionId: "TX-1002", region: "South", quantity: 8, unitPrice: 2200 },
        { transactionId: "TX-1003", region: "North", quantity: 5, unitPrice: 999 },
        { transactionId: "TX-1002", region: "East", quantity: 3, unitPrice: 750 },
        { transactionId: "TX-1004", region: "West", quantity: -2, unitPrice: 100 },
        { transactionId: "TX-1005", region: "East", quantity: 4, unitPrice: "invalid" }
    ];

    try {
        const loadedRecords = await loadTransactions(sourceRecords, 10);
        const result = aggregateTransactions(loadedRecords);

        console.log("Accepted records:", result.accepted.length);
        console.log("Rejected records:", result.rejected.length);
        console.log("Regional totals:", Object.fromEntries(result.totalsByRegion));
        console.log("Total sales:", result.totalSales.toFixed(2));

        for (const rejected of result.rejected) {
            console.log("Rejected transaction:", rejected.record, rejected.errors);
        }

        const report = createCsvReport(result);
        console.log("\nCSV report:\n" + report);

        // JSON.stringify omits undefined object properties and converts NaN
        // and Infinity to null. Validate analytical values before serialization.
        const jsonReport = JSON.stringify({
            totalSales: result.totalSales,
            regionalSales: Object.fromEntries(result.totalsByRegion)
        }, null, 2);

        console.log("JSON report:\n" + jsonReport);
    } catch (error) {
        console.error("Analytics pipeline failed:", error.message);
        process.exitCode = 1;
    }

    heading("Boundary checks");

    const invalidValues = ["", null, true, "NaN", Infinity];
    for (const value of invalidValues) {
        try {
            parseFiniteNumber(value, "measurement");
            console.log("Accepted:", value);
        } catch (error) {
            console.log("Rejected:", String(value), "-", error.message);
        }
    }

    console.log("All demonstrations completed.");
}

main().catch(error => {
    console.error("Unexpected failure:", error);
    process.exitCode = 1;
});
