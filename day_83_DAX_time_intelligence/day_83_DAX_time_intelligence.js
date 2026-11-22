"use strict";

/*
 * DAX-style time intelligence engine.
 * Implements date-context evaluation, period transformations,
 * asynchronous sales retrieval, and cached aggregations.
 */

const { EventEmitter } = require("node:events");

class ValidationError extends Error {}
class DataIntegrityError extends Error {}

const PeriodType = Object.freeze({
    MTD: "MTD",
    QTD: "QTD",
    YTD: "YTD",
});

function parseDate(value) {
    if (value instanceof Date) {
        if (Number.isNaN(value.getTime())) {
            throw new ValidationError("Invalid date.");
        }

        return value.toISOString().slice(0, 10);
    }

    if (typeof value !== "string" ||
        !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        throw new ValidationError("Date must use YYYY-MM-DD.");
    }

    const parsed = new Date(`${value}T00:00:00.000Z`);

    if (Number.isNaN(parsed.getTime()) ||
        parsed.toISOString().slice(0, 10) !== value) {
        throw new ValidationError(`Invalid calendar date: ${value}`);
    }

    return value;
}

function dateParts(value) {
    const [year, month, day] = value.split("-").map(Number);
    return { year, month, day };
}

function formatDate(year, month, day) {
    return [
        String(year).padStart(4, "0"),
        String(month).padStart(2, "0"),
        String(day).padStart(2, "0"),
    ].join("-");
}

function daysInMonth(year, month) {
    return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function shiftYear(value, offset) {
    const { year, month, day } = dateParts(value);
    const targetYear = year + offset;

    return formatDate(
        targetYear,
        month,
        Math.min(day, daysInMonth(targetYear, month))
    );
}

function shiftMonth(value, offset) {
    const { year, month, day } = dateParts(value);

    const index = year * 12 + month - 1 + offset;
    const targetYear = Math.floor(index / 12);
    const targetMonth = ((index % 12) + 12) % 12 + 1;

    const originalLastDay = daysInMonth(year, month);
    const targetLastDay = daysInMonth(targetYear, targetMonth);

    const targetDay = day === originalLastDay
        ? targetLastDay
        : Math.min(day, targetLastDay);

    return formatDate(targetYear, targetMonth, targetDay);
}

function addDays(value, count) {
    const date = new Date(`${value}T00:00:00.000Z`);
    date.setUTCDate(date.getUTCDate() + count);

    return date.toISOString().slice(0, 10);
}

function quarterStart(value) {
    const { year, month } = dateParts(value);
    const firstMonth = Math.floor((month - 1) / 3) * 3 + 1;

    return formatDate(year, firstMonth, 1);
}

class CalendarDimension {
    constructor(start, end) {
        this.start = parseDate(start);
        this.end = parseDate(end);

        if (this.start > this.end) {
            throw new ValidationError("Invalid calendar range.");
        }

        this.index = new Set();

        for (
            let current = this.start;
            current <= this.end;
            current = addDays(current, 1)
        ) {
            this.index.add(current);
        }
    }

    validateSelection(selection) {
        if (!Array.isArray(selection) || selection.length === 0) {
            throw new ValidationError("Date selection is empty.");
        }

        const result = [...new Set(selection.map(parseDate))].sort();

        for (const date of result) {
            if (!this.index.has(date)) {
                throw new ValidationError(
                    `Date outside calendar: ${date}`
                );
            }
        }

        return result;
    }

    range(start, end) {
        const result = [];

        for (
            let current = start;
            current <= end;
            current = addDays(current, 1)
        ) {
            if (this.index.has(current)) {
                result.push(current);
            }
        }

        return result;
    }
}

class SalesRepository extends EventEmitter {
    #records = new Map();
    #cache = new Map();
    #revision = 0;

    constructor(calendar) {
        super();
        this.calendar = calendar;
    }

    add(record) {
        if (!record || !Number.isSafeInteger(record.id) ||
            record.id <= 0) {
            throw new ValidationError("Invalid transaction ID.");
        }

        const date = parseDate(record.date);
        const amount = Number(record.amount);

        if (!this.calendar.index.has(date)) {
            throw new ValidationError("Transaction date is outside calendar.");
        }

        if (!Number.isFinite(amount) || amount < 0) {
            throw new ValidationError("Invalid sales amount.");
        }

        if (this.#records.has(record.id)) {
            throw new DataIntegrityError("Duplicate transaction ID.");
        }

        const stored = Object.freeze({
            id: record.id,
            date,
            amount,
            region: String(record.region || "Unspecified"),
            product: String(record.product || "Unspecified"),
        });

        this.#records.set(record.id, stored);
        this.#revision++;
        this.#cache.clear();

        this.emit("transactionAdded", stored);
    }

    async query(dates) {
        const selection = this.calendar.validateSelection(dates);

        // A sorted date key makes equivalent selections share cached results.
        const key = `${this.#revision}:${selection.join(",")}`;

        if (this.#cache.has(key)) {
            return this.#cache.get(key);
        }

        await Promise.resolve();

        const selected = new Set(selection);
        let total = 0;

        for (const record of this.#records.values()) {
            if (selected.has(record.date)) {
                total += record.amount;
            }
        }

        if (!Number.isFinite(total)) {
            throw new DataIntegrityError("Aggregation overflow.");
        }

        this.#cache.set(key, total);
        return total;
    }

    async queryByRegion(dates) {
        const selection = new Set(
            this.calendar.validateSelection(dates)
        );

        const totals = new Map();

        for (const record of this.#records.values()) {
            if (!selection.has(record.date)) continue;

            totals.set(
                record.region,
                (totals.get(record.region) || 0) + record.amount
            );
        }

        return Object.fromEntries(totals);
    }

    get revision() {
        return this.#revision;
    }
}

class TimeIntelligence {
    constructor(repository) {
        this.repository = repository;
        this.calendar = repository.calendar;
    }

    async dateadd(selection, unit, offset) {
        const dates = this.calendar.validateSelection(selection);

        if (!Number.isInteger(offset)) {
            throw new ValidationError("Offset must be an integer.");
        }

        let shifted;

        switch (unit.toLowerCase()) {
            case "year":
                shifted = dates.map(d => shiftYear(d, offset));
                break;

            case "month":
                shifted = dates.map(d => shiftMonth(d, offset));
                break;

            case "day":
                shifted = dates.map(d => addDays(d, offset));
                break;

            default:
                throw new ValidationError("Unsupported date unit.");
        }

        return shifted.filter(d => this.calendar.index.has(d));
    }

    async sameperiodlastyear(selection) {
        const previousDates = await this.dateadd(
            selection,
            "year",
            -1
        );

        return this.repository.query(previousDates);
    }

    async periodToDate(selection, type) {
        const dates = this.calendar.validateSelection(selection);
        const end = dates[dates.length - 1];

        const { year, month } = dateParts(end);

        let start;

        switch (type) {
            case PeriodType.MTD:
                start = formatDate(year, month, 1);
                break;

            case PeriodType.QTD:
                start = quarterStart(end);
                break;

            case PeriodType.YTD:
                start = formatDate(year, 1, 1);
                break;

            default:
                throw new ValidationError("Invalid period type.");
        }

        return this.repository.query(
            this.calendar.range(start, end)
        );
    }

    async rolling(selection, numberOfDays) {
        const dates = this.calendar.validateSelection(selection);

        if (!Number.isInteger(numberOfDays) || numberOfDays <= 0) {
            throw new ValidationError("Rolling window must be positive.");
        }

        const end = dates[dates.length - 1];
        const start = addDays(end, -(numberOfDays - 1));

        return this.repository.query(
            this.calendar.range(start, end)
        );
    }

    async compareWithPreviousYear(selection) {
        const current = await this.repository.query(selection);
        const previous = await this.sameperiodlastyear(selection);

        return Object.freeze({
            current,
            previous,
            difference: current - previous,
            percentageChange: previous === 0
                ? null
                : ((current - previous) / previous) * 100,
        });
    }
}

async function main() {
    const calendar = new CalendarDimension(
        "2024-01-01",
        "2026-12-31"
    );

    const repository = new SalesRepository(calendar);

    repository.on("transactionAdded", record => {
        console.log(`Recorded transaction ${record.id}`);
    });

    const transactions = [
        [1, "2025-11-15", 10000, "North", "Laptop"],
        [2, "2025-11-20", 7000, "South", "Phone"],
        [3, "2026-01-15", 21000, "North", "Laptop"],
        [4, "2026-02-10", 14000, "South", "Phone"],
        [5, "2026-03-20", 24000, "West", "Laptop"],
        [6, "2026-04-12", 12000, "East", "Tablet"],
        [7, "2026-05-18", 10000, "North", "Phone"],
        [8, "2026-06-22", 19000, "South", "Laptop"],
        [9, "2026-07-14", 13000, "West", "Tablet"],
        [10, "2026-08-09", 8500, "East", "Phone"],
        [11, "2026-09-11", 22000, "North", "Laptop"],
        [12, "2026-10-19", 11500, "South", "Tablet"],
        [13, "2026-11-05", 9500, "West", "Phone"],
        [14, "2026-11-15", 17000, "East", "Laptop"],
    ];

    for (const [id, date, amount, region, product] of transactions) {
        repository.add({ id, date, amount, region, product });
    }

    const engine = new TimeIntelligence(repository);
    const selection = ["2026-11-01", "2026-11-15"];

    const [mtd, qtd, ytd, rolling, previous, comparison, regional] =
        await Promise.all([
            engine.periodToDate(selection, PeriodType.MTD),
            engine.periodToDate(selection, PeriodType.QTD),
            engine.periodToDate(selection, PeriodType.YTD),
            engine.rolling(selection, 30),
            engine.sameperiodlastyear(selection),
            engine.compareWithPreviousYear(selection),
            repository.queryByRegion(selection),
        ]);

    console.log("\nTIME INTELLIGENCE REPORT");
    console.log("------------------------");
    console.log("MTD:", mtd);
    console.log("QTD:", qtd);
    console.log("YTD:", ytd);
    console.log("Rolling 30 days:", rolling);
    console.log("Same period last year:", previous);
    console.log("Comparison:", comparison);
    console.log("Regional sales:", regional);

    const shifted = await engine.dateadd(
        ["2026-11-15"],
        "month",
        -1
    );

    console.log("DATEADD previous month:", shifted);

    console.log("\nVALIDATION");

    try {
        await engine.rolling(selection, -5);
    } catch (error) {
        console.log("Invalid window rejected:", error.message);
    }

    try {
        repository.add({
            id: 1,
            date: "2026-11-15",
            amount: 500,
        });
    } catch (error) {
        console.log("Duplicate rejected:", error.message);
    }

    try {
        calendar.validateSelection(["2030-01-01"]);
    } catch (error) {
        console.log("Out-of-calendar date rejected:", error.message);
    }
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
