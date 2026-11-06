"use strict";

/*
 * Confidence interval analysis using Node.js built-in modules.
 *
 * Implements:
 * - Point estimates
 * - Normal and Student t intervals
 * - Wilson proportion intervals
 * - Bootstrap percentile intervals
 * - Margin of error and sample-size planning
 * - Asynchronous batch analysis
 * - Validation and JSON reporting
 */

const fs = require("node:fs/promises");
const crypto = require("node:crypto");

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class AnalysisError extends Error {
    constructor(message) {
        super(message);
        this.name = "AnalysisError";
    }
}

const T95 = [
    12.706, 4.303, 3.182, 2.776, 2.571,
    2.447, 2.365, 2.306, 2.262, 2.228,
    2.201, 2.179, 2.160, 2.145, 2.131,
    2.120, 2.110, 2.101, 2.093, 2.086,
    2.080, 2.074, 2.069, 2.064, 2.060,
    2.056, 2.052, 2.048, 2.045, 2.042
];

function validateSample(data, minimum = 1) {
    if (!Array.isArray(data)) {
        throw new ValidationError("Sample must be an array.");
    }

    if (data.length < minimum) {
        throw new ValidationError(`At least ${minimum} observations required.`);
    }

    if (!data.every(
        value => typeof value === "number" && Number.isFinite(value)
    )) {
        throw new ValidationError("Sample contains invalid numeric values.");
    }

    return [...data];
}

function validateConfidence(confidence) {
    if (
        typeof confidence !== "number" ||
        !Number.isFinite(confidence) ||
        confidence <= 0 ||
        confidence >= 1
    ) {
        throw new ValidationError("Confidence must be between zero and one.");
    }

    return confidence;
}

function mean(data) {
    const values = validateSample(data);

    // Incremental mean reduces intermediate summation overflow.
    return values.reduce(
        (current, value, index) =>
            current + (value - current) / (index + 1),
        0
    );
}

function variance(data) {
    const values = validateSample(data, 2);
    const average = mean(values);

    return values.reduce(
        (sum, value) => sum + (value - average) ** 2,
        0
    ) / (values.length - 1);
}

function standardDeviation(data) {
    return Math.sqrt(variance(data));
}

function quantile(sorted, probability) {
    if (
        !Array.isArray(sorted) ||
        sorted.length === 0 ||
        probability < 0 ||
        probability > 1
    ) {
        throw new ValidationError("Invalid quantile input.");
    }

    const position = probability * (sorted.length - 1);
    const lower = Math.floor(position);
    const upper = Math.ceil(position);
    const weight = position - lower;

    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

function normalCriticalValue(confidence) {
    validateConfidence(confidence);

    const alpha = 1 - confidence;
    const p = 1 - alpha / 2;

    const a = [
        -39.69683028665376,
        220.9460984245205,
        -275.9285104469687,
        138.3577518672690,
        -30.66479806614716,
        2.506628277459239
    ];

    const b = [
        -54.47609879822406,
        161.5858368580409,
        -155.6989798598866,
        66.80131188771972,
        -13.28068155288572
    ];

    const c = [
        -0.007784894002430293,
        -0.3223964580411365,
        -2.400758277161838,
        -2.549732539343734,
        4.374664141464968,
        2.938163982698783
    ];

    const d = [
        0.007784695709041462,
        0.3224671290700398,
        2.445134137142996,
        3.754408661907416
    ];

    const low = 0.02425;
    const high = 1 - low;

    if (p < low) {
        const q = Math.sqrt(-2 * Math.log(p));

        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
                + c[4]) * q + c[5]) /
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        );
    }

    if (p > high) {
        const q = Math.sqrt(-2 * Math.log(1 - p));

        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
                + c[4]) * q + c[5]) /
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        );
    }

    const q = p - 0.5;
    const r = q * q;

    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r
            + a[4]) * r + a[5]) * q /
        (((((b[0] * r + b[1]) * r + b[2]) * r
            + b[3]) * r + b[4]) * r + 1)
    );
}

function tCritical95(degreesOfFreedom) {
    if (!Number.isInteger(degreesOfFreedom) || degreesOfFreedom < 1) {
        throw new ValidationError("Invalid degrees of freedom.");
    }

    return degreesOfFreedom <= 30
        ? T95[degreesOfFreedom - 1]
        : normalCriticalValue(0.95);
}

function createInterval({
    estimate,
    lower,
    upper,
    confidence,
    method,
    sampleSize
}) {
    if (![estimate, lower, upper].every(Number.isFinite)) {
        throw new AnalysisError("Interval contains a non-finite value.");
    }

    if (lower > upper) {
        throw new AnalysisError("Invalid interval bounds.");
    }

    return Object.freeze({
        estimate,
        lower,
        upper,
        confidence,
        marginOfError: (upper - lower) / 2,
        width: upper - lower,
        method,
        sampleSize,
        contains(value) {
            return value >= lower && value <= upper;
        }
    });
}

function meanNormalInterval(data, confidence = 0.95, populationSD = null) {
    const values = validateSample(data, 2);
    validateConfidence(confidence);

    const sd = populationSD === null
        ? standardDeviation(values)
        : populationSD;

    if (!Number.isFinite(sd) || sd < 0) {
        throw new ValidationError("Invalid population standard deviation.");
    }

    const estimate = mean(values);
    const standardError = sd / Math.sqrt(values.length);
    const margin = normalCriticalValue(confidence) * standardError;

    return createInterval({
        estimate,
        lower: estimate - margin,
        upper: estimate + margin,
        confidence,
        method: "Normal mean interval",
        sampleSize: values.length
    });
}

function meanTInterval(data, confidence = 0.95) {
    const values = validateSample(data, 2);
    validateConfidence(confidence);

    if (confidence !== 0.95) {
        throw new ValidationError("Student t table supports 95% only.");
    }

    const estimate = mean(values);
    const standardError = standardDeviation(values) / Math.sqrt(values.length);
    const margin = tCritical95(values.length - 1) * standardError;

    return createInterval({
        estimate,
        lower: estimate - margin,
        upper: estimate + margin,
        confidence,
        method: "Student t interval",
        sampleSize: values.length
    });
}

function wilsonInterval(successes, trials, confidence = 0.95) {
    validateConfidence(confidence);

    if (
        !Number.isSafeInteger(successes) ||
        !Number.isSafeInteger(trials) ||
        trials <= 0 ||
        successes < 0 ||
        successes > trials
    ) {
        throw new ValidationError("Invalid success and trial counts.");
    }

    const p = successes / trials;
    const z = normalCriticalValue(confidence);
    const z2 = z * z;
    const denominator = 1 + z2 / trials;

    const center = (p + z2 / (2 * trials)) / denominator;

    const adjustment = z * Math.sqrt(
        p * (1 - p) / trials + z2 / (4 * trials * trials)
    ) / denominator;

    return createInterval({
        estimate: p,
        lower: Math.max(0, center - adjustment),
        upper: Math.min(1, center + adjustment),
        confidence,
        method: "Wilson proportion interval",
        sampleSize: trials
    });
}

// Seeded PRNG makes bootstrap results reproducible.
class RandomGenerator {
    constructor(seed = 42) {
        this.state = seed >>> 0;
    }

    next() {
        this.state = (1664525 * this.state + 1013904223) >>> 0;
        return this.state / 4294967296;
    }

    integer(maximum) {
        return Math.floor(this.next() * maximum);
    }
}

function bootstrapInterval(
    data,
    statistic = mean,
    confidence = 0.95,
    repetitions = 10000,
    seed = 42
) {
    const values = validateSample(data, 2);
    validateConfidence(confidence);

    if (!Number.isInteger(repetitions) || repetitions < 100) {
        throw new ValidationError("At least 100 repetitions are required.");
    }

    if (typeof statistic !== "function") {
        throw new ValidationError("Statistic must be a function.");
    }

    const random = new RandomGenerator(seed);
    const estimates = new Array(repetitions);

    for (let iteration = 0; iteration < repetitions; iteration++) {
        const sample = Array.from(
            { length: values.length },
            () => values[random.integer(values.length)]
        );

        const result = statistic(sample);

        if (!Number.isFinite(result)) {
            throw new AnalysisError("Bootstrap statistic is not finite.");
        }

        estimates[iteration] = result;
    }

    estimates.sort((a, b) => a - b);

    const alpha = (1 - confidence) / 2;
    const estimate = statistic(values);

    return createInterval({
        estimate,
        lower: quantile(estimates, alpha),
        upper: quantile(estimates, 1 - alpha),
        confidence,
        method: "Percentile bootstrap interval",
        sampleSize: values.length
    });
}

function calculateMarginOfError(sd, sampleSize, confidence = 0.95) {
    validateConfidence(confidence);

    if (!Number.isFinite(sd) || sd < 0) {
        throw new ValidationError("Invalid standard deviation.");
    }

    if (!Number.isSafeInteger(sampleSize) || sampleSize <= 0) {
        throw new ValidationError("Invalid sample size.");
    }

    return normalCriticalValue(confidence) * sd / Math.sqrt(sampleSize);
}

function calculateRequiredSampleSize(sd, margin, confidence = 0.95) {
    validateConfidence(confidence);

    if (!Number.isFinite(sd) || sd < 0) {
        throw new ValidationError("Invalid standard deviation.");
    }

    if (!Number.isFinite(margin) || margin <= 0) {
        throw new ValidationError("Margin must be positive.");
    }

    return Math.ceil(
        (normalCriticalValue(confidence) * sd / margin) ** 2
    );
}

// Asynchronous execution prevents a large batch from blocking callers.
async function analyzeCampaigns(campaigns) {
    if (!Array.isArray(campaigns)) {
        throw new ValidationError("Campaign collection must be an array.");
    }

    const results = await Promise.all(
        campaigns.map(async campaign => {
            await Promise.resolve();

            return {
                campaignId: campaign.id,
                interval: wilsonInterval(
                    campaign.successes,
                    campaign.trials
                )
            };
        })
    );

    return results;
}

async function exportReport(results, filename) {
    if (typeof filename !== "string" || !filename.endsWith(".json")) {
        throw new ValidationError("Report filename must end in .json.");
    }

    const serializable = results.map(result => ({
        ...result,
        interval: result.interval
            ? {
                estimate: result.interval.estimate,
                lower: result.interval.lower,
                upper: result.interval.upper,
                confidence: result.interval.confidence,
                marginOfError: result.interval.marginOfError,
                method: result.interval.method,
                sampleSize: result.interval.sampleSize
            }
            : result.interval
    }));

    await fs.writeFile(
        filename,
        JSON.stringify(serializable, null, 2),
        { encoding: "utf8", flag: "w", mode: 0o600 }
    );
}

function runTests() {
    const data = [12, 14, 15, 13, 16, 18, 14, 15, 17, 16];

    const interval = meanTInterval(data);

    if (!(interval.lower < interval.estimate &&
        interval.estimate < interval.upper)) {
        throw new Error("Mean interval test failed.");
    }

    const proportion = wilsonInterval(72, 100);

    if (
        proportion.lower < 0 ||
        proportion.upper > 1 ||
        proportion.lower > proportion.estimate ||
        proportion.upper < proportion.estimate
    ) {
        throw new Error("Wilson interval test failed.");
    }

    const bootstrap = bootstrapInterval(
        data,
        values => [...values].sort((a, b) => a - b)[4],
        0.95,
        1000,
        42
    );

    if (!bootstrap.contains(bootstrap.estimate)) {
        throw new Error("Bootstrap test failed.");
    }

    if (calculateRequiredSampleSize(10, 2) !== 97) {
        throw new Error("Sample size test failed.");
    }

    let failed = false;

    try {
        wilsonInterval(120, 100);
    } catch (error) {
        failed = error instanceof ValidationError;
    }

    if (!failed) {
        throw new Error("Invalid count test failed.");
    }

    console.log("All tests passed.");
}

async function main() {
    const responseTimes = [
        12.4, 13.1, 11.8, 14.2, 12.9,
        13.7, 12.1, 14.0, 13.3, 12.7,
        11.9, 13.5, 14.1, 12.6, 13.0
    ];

    console.log("CONFIDENCE INTERVAL ANALYSIS");
    console.log("=".repeat(55));

    const normal = meanNormalInterval(responseTimes);
    const student = meanTInterval(responseTimes);

    const conversion = wilsonInterval(735, 1000);

    const bootstrap = bootstrapInterval(
        responseTimes,
        values => {
            const sorted = [...values].sort((a, b) => a - b);
            return sorted[Math.floor(sorted.length / 2)];
        },
        0.95,
        5000,
        42
    );

    for (const result of [normal, student, conversion, bootstrap]) {
        console.log({
            method: result.method,
            estimate: result.estimate.toFixed(4),
            lower: result.lower.toFixed(4),
            upper: result.upper.toFixed(4),
            marginOfError: result.marginOfError.toFixed(4)
        });
    }

    console.log(
        "Required sample size:",
        calculateRequiredSampleSize(10, 2)
    );

    console.log(
        "Margin of error:",
        calculateMarginOfError(10, 100).toFixed(4)
    );

    const campaigns = await analyzeCampaigns([
        { id: "C001", successes: 735, trials: 1000 },
        { id: "C002", successes: 420, trials: 600 },
        { id: "C003", successes: 92, trials: 120 }
    ]);

    await exportReport(
        [
            { method: "normal", interval: normal },
            { method: "student_t", interval: student },
            { method: "wilson", interval: conversion },
            { method: "bootstrap", interval: bootstrap },
            ...campaigns
        ],
        "confidence_intervals.json"
    );

    console.log("Report exported.");

    runTests();

    // Cryptographically generated identifiers can be used to identify
    // separate analysis runs without exposing sample observations.
    console.log("Analysis run ID:", crypto.randomUUID());
}

main().catch(error => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
