"use strict";

/*
 * Statistical Analysis Project
 * Event-driven statistical analysis using Node.js.
 *
 * Features:
 * - Descriptive statistics
 * - Pearson correlation
 * - Simple linear regression
 * - Bootstrap confidence intervals
 * - Permutation hypothesis testing
 * - Asynchronous execution
 * - Structured reporting
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");
const path = require("node:path");

class ValidationError extends Error {}
class StatisticalError extends Error {}

function assertFinite(value, label) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new ValidationError(`${label} must be a finite number.`);
    }
}

function validateObservation(record) {
    if (!Number.isInteger(record.id) || record.id <= 0) {
        throw new ValidationError("Participant ID must be positive.");
    }

    assertFinite(record.studyHours, "Study hours");
    assertFinite(record.examScore, "Exam score");

    if (record.studyHours < 0) {
        throw new ValidationError("Study hours cannot be negative.");
    }

    if (record.examScore < 0 || record.examScore > 100) {
        throw new ValidationError("Exam score must be between 0 and 100.");
    }

    return Object.freeze({ ...record });
}

function mean(values) {
    if (values.length === 0) {
        throw new StatisticalError("Cannot calculate an empty mean.");
    }

    return values.reduce((sum, value) => sum + value, 0)
        / values.length;
}

function variance(values) {
    if (values.length < 2) {
        throw new StatisticalError("At least two values are required.");
    }

    const center = mean(values);

    return values.reduce(
        (sum, value) => sum + (value - center) ** 2,
        0
    ) / (values.length - 1);
}

function standardDeviation(values) {
    return Math.sqrt(variance(values));
}

function pearson(x, y) {
    if (x.length !== y.length || x.length < 3) {
        throw new StatisticalError("Invalid correlation sample.");
    }

    const mx = mean(x);
    const my = mean(y);

    let numerator = 0;
    let sumX = 0;
    let sumY = 0;

    for (let i = 0; i < x.length; i++) {
        const dx = x[i] - mx;
        const dy = y[i] - my;

        numerator += dx * dy;
        sumX += dx * dx;
        sumY += dy * dy;
    }

    const denominator = Math.sqrt(sumX * sumY);

    if (denominator === 0) {
        throw new StatisticalError("Correlation is undefined.");
    }

    return numerator / denominator;
}

function regression(x, y) {
    const mx = mean(x);
    const my = mean(y);

    const denominator = x.reduce(
        (sum, value) => sum + (value - mx) ** 2,
        0
    );

    if (denominator === 0) {
        throw new StatisticalError("Regression slope is undefined.");
    }

    let numerator = 0;

    for (let i = 0; i < x.length; i++) {
        numerator += (x[i] - mx) * (y[i] - my);
    }

    const slope = numerator / denominator;
    const intercept = my - slope * mx;

    const predictions = x.map(
        value => intercept + slope * value
    );

    const residuals = y.map(
        (value, index) => value - predictions[index]
    );

    const ssResidual = residuals.reduce(
        (sum, value) => sum + value ** 2,
        0
    );

    const ssTotal = y.reduce(
        (sum, value) => sum + (value - my) ** 2,
        0
    );

    return {
        slope,
        intercept,
        rSquared: 1 - ssResidual / ssTotal,
        rmse: Math.sqrt(
            mean(residuals.map(value => value ** 2))
        ),
        mae: mean(residuals.map(Math.abs))
    };
}

function percentile(values, probability) {
    if (!values.length || probability < 0 || probability > 1) {
        throw new StatisticalError("Invalid percentile request.");
    }

    const sorted = [...values].sort((a, b) => a - b);
    const position = (sorted.length - 1) * probability;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    return sorted[lower]
        + (sorted[upper] - sorted[lower])
        * (position - lower);
}

// Deterministic pseudo-random generator for reproducible experiments.
function createRandom(seed) {
    let state = seed >>> 0;

    return function random() {
        state += 0x6D2B79F5;

        let value = state;
        value = Math.imul(value ^ (value >>> 15), value | 1);
        value ^= value + Math.imul(value ^ (value >>> 7), value | 61);

        return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
}

function shuffle(values, random) {
    const result = [...values];

    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1));
        [result[i], result[j]] = [result[j], result[i]];
    }

    return result;
}

class StatisticalEngine extends EventEmitter {
    constructor(records, seed = 42) {
        super();

        if (!Array.isArray(records) || records.length < 4) {
            throw new ValidationError(
                "At least four observations are required."
            );
        }

        const ids = new Set();

        this.records = Object.freeze(
            records.map(record => {
                const validated = validateObservation(record);

                if (ids.has(validated.id)) {
                    throw new ValidationError("Duplicate participant ID.");
                }

                ids.add(validated.id);
                return validated;
            })
        );

        this.x = this.records.map(item => item.studyHours);
        this.y = this.records.map(item => item.examScore);

        if (new Set(this.x).size < 2 || new Set(this.y).size < 2) {
            throw new StatisticalError(
                "Both variables must contain variation."
            );
        }

        this.random = createRandom(seed);
    }

    describe(values) {
        return {
            count: values.length,
            mean: mean(values),
            median: percentile(values, 0.5),
            standardDeviation: standardDeviation(values),
            minimum: Math.min(...values),
            maximum: Math.max(...values)
        };
    }

    bootstrap(statistic, iterations = 5000, confidence = 0.95) {
        if (!Number.isInteger(iterations) || iterations < 1000) {
            throw new ValidationError(
                "At least 1000 bootstrap iterations are required."
            );
        }

        if (confidence <= 0 || confidence >= 1) {
            throw new ValidationError("Invalid confidence level.");
        }

        const estimates = [];
        const n = this.records.length;

        for (let iteration = 0; iteration < iterations; iteration++) {
            const sampleX = [];
            const sampleY = [];

            for (let i = 0; i < n; i++) {
                const index = Math.floor(this.random() * n);

                sampleX.push(this.x[index]);
                sampleY.push(this.y[index]);
            }

            try {
                estimates.push(statistic(sampleX, sampleY));
            } catch (error) {
                if (!(error instanceof StatisticalError)) {
                    throw error;
                }
            }
        }

        if (estimates.length < iterations * 0.95) {
            throw new StatisticalError(
                "Too many invalid bootstrap samples."
            );
        }

        const tail = (1 - confidence) / 2;

        return {
            lower: percentile(estimates, tail),
            upper: percentile(estimates, 1 - tail),
            confidenceLevel: confidence
        };
    }

    async permutationTest(iterations = 10000) {
        if (!Number.isInteger(iterations) || iterations < 1000) {
            throw new ValidationError(
                "At least 1000 permutations are required."
            );
        }

        const observed = Math.abs(pearson(this.x, this.y));
        let extreme = 0;

        for (let i = 0; i < iterations; i++) {
            const randomizedY = shuffle(this.y, this.random);

            if (
                Math.abs(pearson(this.x, randomizedY))
                >= observed
            ) {
                extreme++;
            }

            // Yield periodically so the Node.js event loop remains responsive.
            if (i > 0 && i % 1000 === 0) {
                await new Promise(resolve => setImmediate(resolve));
                this.emit("progress", {
                    completed: i,
                    total: iterations
                });
            }
        }

        return (extreme + 1) / (iterations + 1);
    }

    async analyze() {
        this.emit("analysisStarted", {
            observations: this.records.length
        });

        try {
            const correlation = pearson(this.x, this.y);
            const model = regression(this.x, this.y);

            const correlationCI = this.bootstrap(pearson);
            const slopeCI = this.bootstrap(
                (x, y) => regression(x, y).slope
            );

            const pValue = await this.permutationTest();

            const result = {
                generatedAt: new Date().toISOString(),
                sampleSize: this.records.length,

                descriptiveStatistics: {
                    studyHours: this.describe(this.x),
                    examScores: this.describe(this.y)
                },

                hypothesis: {
                    null: "H0: Population correlation equals zero.",
                    alternative: "H1: Population correlation is not zero.",
                    significanceLevel: 0.05,
                    pValue,
                    decision: pValue < 0.05
                        ? "Reject the null hypothesis."
                        : "Fail to reject the null hypothesis."
                },

                relationship: {
                    pearsonCorrelation: correlation,
                    confidenceInterval: correlationCI,
                    regressionSlope: model.slope,
                    slopeConfidenceInterval: slopeCI,
                    regressionIntercept: model.intercept,
                    rSquared: model.rSquared,
                    rmse: model.rmse,
                    mae: model.mae
                },

                interpretation: {
                    direction: correlation >= 0 ? "positive" : "negative",
                    strength: Math.abs(correlation) >= 0.7
                        ? "strong"
                        : Math.abs(correlation) >= 0.4
                            ? "moderate"
                            : "weak",
                    limitation: "Correlation does not establish causation."
                }
            };

            this.emit("analysisCompleted", result);

            return result;
        } catch (error) {
            this.emit("analysisFailed", error);
            throw error;
        }
    }
}

const sampleData = [
    [1, 1.0, 48],
    [2, 1.5, 52],
    [3, 2.0, 55],
    [4, 2.5, 58],
    [5, 3.0, 62],
    [6, 3.5, 65],
    [7, 4.0, 68],
    [8, 4.5, 70],
    [9, 5.0, 74],
    [10, 5.5, 77],
    [11, 6.0, 80],
    [12, 7.0, 86]
].map(([id, studyHours, examScore]) => ({
    id,
    studyHours,
    examScore
}));

async function saveReport(report) {
    const destination = path.resolve(
        process.cwd(),
        "statistical_analysis_report.json"
    );

    const temporary = `${destination}.tmp`;

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "wx" }
        );

        await fs.rename(temporary, destination);

        return destination;
    } catch (error) {
        await fs.rm(temporary, { force: true }).catch(() => {});
        throw error;
    }
}

async function main() {
    const engine = new StatisticalEngine(sampleData, 42);

    engine.on("analysisStarted", event => {
        console.log("Analysis started:", event);
    });

    engine.on("progress", event => {
        console.log(
            `Permutation progress: ${event.completed}/${event.total}`
        );
    });

    engine.on("analysisCompleted", () => {
        console.log("Analysis completed successfully.");
    });

    engine.on("analysisFailed", error => {
        console.error("Analysis failed:", error.message);
    });

    const report = await engine.analyze();
    const output = await saveReport(report);

    console.log(JSON.stringify(report, null, 2));
    console.log("\nReport saved:", output);
}

main().catch(error => {
    console.error("Fatal execution error:", error.message);
    process.exitCode = 1;
});
