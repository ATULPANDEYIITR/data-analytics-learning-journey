"use strict";

/*
 * Exploratory Data Analysis in Node.js.
 *
 * The implementation uses Maps, Sets, classes, Promises, event-driven
 * processing, validation, descriptive statistics, correlations, and
 * anomaly detection without external npm dependencies.
 */

const { EventEmitter } = require("node:events");

class EDAError extends Error {
    constructor(message) {
        super(message);
        this.name = "EDAError";
    }
}

class CustomerRecord {
    constructor({ customerId, age, income, monthlySpend, visits, satisfaction }) {
        this.customerId = Number(customerId);
        this.age = Number(age);
        this.income = Number(income);
        this.monthlySpend = Number(monthlySpend);
        this.visits = Number(visits);
        this.satisfaction = Number(satisfaction);
    }
}

class EDAEngine extends EventEmitter {
    constructor(records) {
        super();

        if (!Array.isArray(records) || records.length === 0) {
            throw new EDAError("Dataset must contain at least one record.");
        }

        this.records = records.map((record) => {
            const normalized = record instanceof CustomerRecord
                ? record
                : new CustomerRecord(record);

            this.validate(normalized);
            return normalized;
        });

        this.validateUniqueIds();
    }

    validate(record) {
        const numericFields = [
            "customerId",
            "age",
            "income",
            "monthlySpend",
            "visits",
            "satisfaction"
        ];

        for (const field of numericFields) {
            if (!Number.isFinite(record[field])) {
                throw new EDAError(
                    `Invalid numeric value in ${field} for customer ${record.customerId}.`
                );
            }
        }

        if (record.age < 0 || record.age > 120) {
            throw new EDAError(`Invalid age: ${record.age}`);
        }

        if (record.income < 0 || record.monthlySpend < 0) {
            throw new EDAError("Income and monthly spend cannot be negative.");
        }

        if (!Number.isInteger(record.visits) || record.visits < 0) {
            throw new EDAError("Visits must be a non-negative integer.");
        }

        if (record.satisfaction < 0 || record.satisfaction > 10) {
            throw new EDAError("Satisfaction must be between 0 and 10.");
        }
    }

    validateUniqueIds() {
        const ids = new Set();

        for (const record of this.records) {
            if (ids.has(record.customerId)) {
                throw new EDAError(`Duplicate customer ID: ${record.customerId}`);
            }
            ids.add(record.customerId);
        }
    }

    values(field) {
        const validFields = new Set([
            "age",
            "income",
            "monthlySpend",
            "visits",
            "satisfaction"
        ]);

        if (!validFields.has(field)) {
            throw new EDAError(`Unknown analytical field: ${field}`);
        }

        return this.records.map((record) => record[field]);
    }

    static mean(values) {
        if (values.length === 0) {
            throw new EDAError("Mean requires at least one value.");
        }

        return values.reduce((sum, value) => sum + value, 0) / values.length;
    }

    static median(values) {
        if (values.length === 0) {
            throw new EDAError("Median requires at least one value.");
        }

        const sorted = [...values].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);

        return sorted.length % 2 === 0
            ? (sorted[middle - 1] + sorted[middle]) / 2
            : sorted[middle];
    }

    static populationStdDev(values) {
        const average = EDAEngine.mean(values);

        return Math.sqrt(
            EDAEngine.mean(
                values.map((value) => (value - average) ** 2)
            )
        );
    }

    static quantile(values, q) {
        if (values.length === 0 || q < 0 || q > 1) {
            throw new EDAError("Invalid quantile request.");
        }

        const sorted = [...values].sort((a, b) => a - b);
        const position = (sorted.length - 1) * q;
        const lower = Math.floor(position);
        const upper = Math.ceil(position);

        if (lower === upper) {
            return sorted[lower];
        }

        const fraction = position - lower;
        return sorted[lower] * (1 - fraction) + sorted[upper] * fraction;
    }

    descriptiveStatistics(field) {
        const values = this.values(field);

        return {
            count: values.length,
            mean: EDAEngine.mean(values),
            median: EDAEngine.median(values),
            minimum: Math.min(...values),
            maximum: Math.max(...values),
            standardDeviation: EDAEngine.populationStdDev(values),
            q1: EDAEngine.quantile(values, 0.25),
            q3: EDAEngine.quantile(values, 0.75)
        };
    }

    histogram(field, binCount = 5) {
        if (!Number.isInteger(binCount) || binCount <= 0) {
            throw new EDAError("binCount must be a positive integer.");
        }

        const values = this.values(field);
        const min = Math.min(...values);
        const max = Math.max(...values);

        if (min === max) {
            return [{ lower: min, upper: max, count: values.length }];
        }

        const width = (max - min) / binCount;
        const bins = Array.from(
            { length: binCount },
            (_, index) => ({
                lower: min + index * width,
                upper: index === binCount - 1
                    ? max
                    : min + (index + 1) * width,
                count: 0
            })
        );

        for (const value of values) {
            let index = Math.floor((value - min) / width);
            index = Math.min(index, binCount - 1);
            bins[index].count += 1;
        }

        return bins;
    }

    pearsonCorrelation(fieldA, fieldB) {
        const x = this.values(fieldA);
        const y = this.values(fieldB);

        const meanX = EDAEngine.mean(x);
        const meanY = EDAEngine.mean(y);

        let numerator = 0;
        let denominatorX = 0;
        let denominatorY = 0;

        for (let i = 0; i < x.length; i++) {
            const dx = x[i] - meanX;
            const dy = y[i] - meanY;

            numerator += dx * dy;
            denominatorX += dx ** 2;
            denominatorY += dy ** 2;
        }

        const denominator = Math.sqrt(denominatorX * denominatorY);
        return denominator === 0 ? 0 : numerator / denominator;
    }

    iqrAnomalies(field) {
        const values = this.values(field);
        const q1 = EDAEngine.quantile(values, 0.25);
        const q3 = EDAEngine.quantile(values, 0.75);
        const iqr = q3 - q1;

        const lowerFence = q1 - 1.5 * iqr;
        const upperFence = q3 + 1.5 * iqr;

        return this.records
            .filter((record) => {
                const value = record[field];
                return value < lowerFence || value > upperFence;
            })
            .map((record) => ({
                customerId: record.customerId,
                field,
                value: record[field],
                lowerFence,
                upperFence
            }));
    }

    groupBySpendBand() {
        const groups = new Map([
            ["low", []],
            ["medium", []],
            ["high", []]
        ]);

        for (const record of this.records) {
            let band;

            if (record.monthlySpend < 300) {
                band = "low";
            } else if (record.monthlySpend <= 700) {
                band = "medium";
            } else {
                band = "high";
            }

            groups.get(band).push(record.customerId);
        }

        return Object.fromEntries(groups);
    }

    generateReport() {
        const numericFields = [
            "age",
            "income",
            "monthlySpend",
            "visits",
            "satisfaction"
        ];

        const report = {
            rowCount: this.records.length,
            univariate: {},
            distributions: {},
            bivariate: {},
            anomalies: {},
            segments: this.groupBySpendBand()
        };

        for (const field of numericFields) {
            report.univariate[field] = this.descriptiveStatistics(field);
        }

        report.distributions.monthlySpend = this.histogram("monthlySpend");
        report.distributions.satisfaction = this.histogram("satisfaction");

        report.bivariate.incomeVsSpend =
            this.pearsonCorrelation("income", "monthlySpend");

        report.bivariate.visitsVsSpend =
            this.pearsonCorrelation("visits", "monthlySpend");

        report.bivariate.ageVsSatisfaction =
            this.pearsonCorrelation("age", "satisfaction");

        report.anomalies.income = this.iqrAnomalies("income");
        report.anomalies.monthlySpend = this.iqrAnomalies("monthlySpend");

        return report;
    }
}

async function processDataset(records) {
    /*
     * Promise-based processing allows this analytical engine to become part
     * of an asynchronous ingestion pipeline without changing its core API.
     */
    return new Promise((resolve, reject) => {
        setImmediate(() => {
            try {
                const engine = new EDAEngine(records);

                engine.on("analysisComplete", (summary) => {
                    console.error(
                        `Analysis completed for ${summary.rowCount} records.`
                    );
                });

                const report = engine.generateReport();

                engine.emit("analysisComplete", {
                    rowCount: engine.records.length
                });

                resolve(report);
            } catch (error) {
                reject(error);
            }
        });
    });
}

async function main() {
    const records = [
        { customerId: 101, age: 24, income: 42000, monthlySpend: 280, visits: 4, satisfaction: 7.5 },
        { customerId: 102, age: 31, income: 58000, monthlySpend: 450, visits: 6, satisfaction: 8.2 },
        { customerId: 103, age: 45, income: 76000, monthlySpend: 680, visits: 8, satisfaction: 8.7 },
        { customerId: 104, age: 52, income: 91000, monthlySpend: 820, visits: 10, satisfaction: 9.1 },
        { customerId: 105, age: 29, income: 51000, monthlySpend: 390, visits: 5, satisfaction: 7.9 },
        { customerId: 106, age: 38, income: 67000, monthlySpend: 540, visits: 7, satisfaction: 8.4 },
        { customerId: 107, age: 63, income: 125000, monthlySpend: 1450, visits: 18, satisfaction: 6.1 },
        { customerId: 108, age: 41, income: 72000, monthlySpend: 610, visits: 9, satisfaction: 8.8 },
        { customerId: 109, age: 34, income: 47000, monthlySpend: 330, visits: 4, satisfaction: 7.1 },
        { customerId: 110, age: 57, income: 84000, monthlySpend: 760, visits: 11, satisfaction: 8.9 }
    ];

    try {
        const report = await processDataset(records);

        if (report.rowCount !== 10) {
            throw new EDAError("Unexpected row count.");
        }

        console.log(JSON.stringify(report, null, 2));
    } catch (error) {
        console.error(`${error.name}: ${error.message}`);
        process.exitCode = 1;
    }
}

main();
