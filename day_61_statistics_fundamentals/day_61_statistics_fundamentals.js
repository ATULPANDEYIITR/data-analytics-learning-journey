"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const EventEmitter = require("node:events");

class StatisticsError extends Error {}

function validateNumeric(values, name = "values") {
    if (!Array.isArray(values) || values.length === 0) {
        throw new StatisticsError(`${name} must be a non-empty array.`);
    }
    if (!values.every(
        value => typeof value === "number" && Number.isFinite(value)
    )) {
        throw new StatisticsError(`${name} must contain finite numbers.`);
    }
    return [...values];
}

function mean(values) {
    const data = validateNumeric(values);
    return data.reduce((sum, value) => sum + value, 0) / data.length;
}

function median(values) {
    const data = validateNumeric(values).sort((a, b) => a - b);
    const middle = Math.floor(data.length / 2);
    return data.length % 2 === 0
        ? (data[middle - 1] + data[middle]) / 2
        : data[middle];
}

function modes(values) {
    const data = validateNumeric(values);
    const frequencies = new Map();

    for (const value of data) {
        frequencies.set(value, (frequencies.get(value) || 0) + 1);
    }

    const maximum = Math.max(...frequencies.values());
    return [...frequencies.entries()]
        .filter(([, count]) => count === maximum)
        .map(([value]) => value)
        .sort((a, b) => a - b);
}

function variance(values, sample = false) {
    const data = validateNumeric(values);
    if (sample && data.length < 2) {
        throw new StatisticsError(
            "Sample variance requires at least two observations."
        );
    }

    const average = mean(data);
    const divisor = sample ? data.length - 1 : data.length;

    return data.reduce(
        (total, value) => total + (value - average) ** 2,
        0
    ) / divisor;
}

function describe(values) {
    const data = validateNumeric(values);
    const populationVariance = variance(data);
    const sampleVariance = data.length >= 2 ? variance(data, true) : null;

    return Object.freeze({
        count: data.length,
        minimum: Math.min(...data),
        maximum: Math.max(...data),
        mean: mean(data),
        median: median(data),
        modes: modes(data),
        populationVariance,
        populationStdDev: Math.sqrt(populationVariance),
        sampleVariance,
        sampleStdDev: sampleVariance === null
            ? null
            : Math.sqrt(sampleVariance)
    });
}

function seededRandom(seed) {
    let state = seed >>> 0;
    return () => {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 0x100000000;
    };
}

function simpleRandomSample(population, size, seed = 1) {
    const data = validateNumeric(population, "population");
    if (!Number.isInteger(size) || size < 1 || size > data.length) {
        throw new StatisticsError("Invalid sample size.");
    }

    const result = [...data];
    const random = seededRandom(seed);

    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1));
        [result[i], result[j]] = [result[j], result[i]];
    }

    return result.slice(0, size);
}

function systematicSample(population, size) {
    const data = validateNumeric(population, "population");
    if (!Number.isInteger(size) || size < 1 || size > data.length) {
        throw new StatisticsError("Invalid sample size.");
    }

    const interval = data.length / size;
    return Array.from(
        { length: size },
        (_, index) => data[Math.floor(index * interval)]
    );
}

class StatisticsPipeline extends EventEmitter {
    constructor(values) {
        super();
        this.population = validateNumeric(values, "population");
    }

    run(sampleSize) {
        const sample = simpleRandomSample(this.population, sampleSize, 42);
        const result = {
            population: describe(this.population),
            sample: describe(sample),
            sampleValues: sample,
            estimatedPopulationMean: mean(sample),
            standardError: Math.sqrt(
                variance(sample, true) / sample.length
            )
        };

        this.emit("statistics", result);
        return result;
    }

    export(result) {
        const directory = fs.mkdtempSync(
            path.join(os.tmpdir(), "statistics-")
        );
        const file = path.join(directory, "result.json");
        fs.writeFileSync(file, JSON.stringify(result, null, 2), "utf8");
        this.emit("exported", file);
        return file;
    }
}

async function main() {
    const population = [
        61, 64, 66, 68, 69, 71, 72, 73, 74, 75,
        76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
        86, 87, 88, 90, 92
    ];

    const pipeline = new StatisticsPipeline(population);

    pipeline.on("statistics", result => {
        console.log("Population mean:", result.population.mean.toFixed(2));
        console.log("Sample mean:", result.sample.mean.toFixed(2));
        console.log(
            "Standard error:",
            result.standardError.toFixed(4)
        );
    });

    pipeline.on("exported", file => {
        console.log("Exported:", file);
    });

    const result = pipeline.run(8);
    pipeline.export(result);

    const systematic = systematicSample(population, 5);
    console.log("Systematic sample:", systematic);

    try {
        simpleRandomSample(population, 100);
    } catch (error) {
        if (!(error instanceof StatisticsError)) {
            throw error;
        }
        console.log("Expected validation:", error.message);
    }

    if (result.population.count !== 25) {
        throw new Error("Population count validation failed.");
    }
    if (result.sample.count !== 8) {
        throw new Error("Sample count validation failed.");
    }
}

main().catch(error => {
    console.error("Fatal error:", error.message);
    process.exitCode = 1;
});
