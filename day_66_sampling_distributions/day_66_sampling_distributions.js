"use strict";

/*
 * Sampling Distributions
 *
 * Node.js implementation featuring:
 * - Population modeling
 * - Sample statistics
 * - Standard error and finite population correction
 * - Sampling distributions
 * - Central Limit Theorem simulation
 * - Law of Large Numbers experiments
 * - Asynchronous simulation jobs
 * - Event-driven experiment reporting
 * - Confidence intervals
 *
 * Runtime: Node.js 18+
 * External dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const path = require("node:path");
const { randomUUID } = require("node:crypto");

class SamplingError extends Error {
    constructor(message) {
        super(message);
        this.name = "SamplingError";
    }
}

const SamplingMethod = Object.freeze({
    WITH_REPLACEMENT: "WITH_REPLACEMENT",
    WITHOUT_REPLACEMENT: "WITHOUT_REPLACEMENT"
});

function validateNumber(value, name) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value)
    ) {
        throw new SamplingError(`${name} must be a finite number.`);
    }
}

function validatePositiveInteger(value, name) {
    if (!Number.isSafeInteger(value) || value <= 0) {
        throw new SamplingError(
            `${name} must be a positive safe integer.`
        );
    }
}

// Reproducible pseudo-random generator for educational simulations.
// This is not suitable for cryptographic applications.
class RandomGenerator {
    constructor(seed = 2026) {
        if (!Number.isSafeInteger(seed)) {
            throw new SamplingError("Seed must be a safe integer.");
        }

        this.state = seed >>> 0;
    }

    next() {
        let x = this.state;

        x ^= x << 13;
        x ^= x >>> 17;
        x ^= x << 5;

        this.state = x >>> 0;

        return this.state / 4294967296;
    }

    integer(maxExclusive) {
        return Math.floor(this.next() * maxExclusive);
    }
}

class Statistics {
    static mean(values) {
        if (!values.length) {
            throw new SamplingError("Cannot calculate empty mean.");
        }

        return values.reduce((sum, value) => sum + value, 0)
            / values.length;
    }

    static populationVariance(values) {
        const mean = Statistics.mean(values);

        return values.reduce(
            (sum, value) => sum + (value - mean) ** 2,
            0
        ) / values.length;
    }

    static sampleVariance(values) {
        if (values.length < 2) {
            throw new SamplingError(
                "Sample variance requires at least two observations."
            );
        }

        const mean = Statistics.mean(values);

        return values.reduce(
            (sum, value) => sum + (value - mean) ** 2,
            0
        ) / (values.length - 1);
    }

    static standardDeviation(variance) {
        return Math.sqrt(variance);
    }

    static median(values) {
        const sorted = [...values].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);

        return sorted.length % 2
            ? sorted[middle]
            : (sorted[middle - 1] + sorted[middle]) / 2;
    }
}

class Population {
    #observations;

    constructor(name, observations) {
        if (!name || typeof name !== "string") {
            throw new SamplingError("Population name is required.");
        }

        if (!Array.isArray(observations) || observations.length === 0) {
            throw new SamplingError(
                "Population must contain observations."
            );
        }

        observations.forEach(value =>
            validateNumber(value, "Population observation")
        );

        this.name = name;
        this.#observations = Object.freeze([...observations]);

        this.statistics = Object.freeze({
            size: this.size,
            mean: Statistics.mean(this.#observations),
            variance: Statistics.populationVariance(
                this.#observations
            ),
            standardDeviation: Math.sqrt(
                Statistics.populationVariance(this.#observations)
            ),
            median: Statistics.median(this.#observations)
        });
    }

    get size() {
        return this.#observations.length;
    }

    get observations() {
        return [...this.#observations];
    }

    drawSample(size, method, random) {
        validatePositiveInteger(size, "Sample size");

        if (
            method !== SamplingMethod.WITH_REPLACEMENT &&
            method !== SamplingMethod.WITHOUT_REPLACEMENT
        ) {
            throw new SamplingError("Unsupported sampling method.");
        }

        if (
            method === SamplingMethod.WITHOUT_REPLACEMENT &&
            size > this.size
        ) {
            throw new SamplingError(
                "Sample exceeds population size."
            );
        }

        const sample = [];

        if (method === SamplingMethod.WITH_REPLACEMENT) {
            for (let i = 0; i < size; i++) {
                const index = random.integer(this.size);
                sample.push(this.#observations[index]);
            }
        } else {
            // Partial Fisher-Yates shuffle avoids sorting the
            // entire population for every sample.
            const indices = Array.from(
                { length: this.size },
                (_, index) => index
            );

            for (let i = 0; i < size; i++) {
                const j = i + random.integer(this.size - i);

                [indices[i], indices[j]] = [
                    indices[j],
                    indices[i]
                ];

                sample.push(this.#observations[indices[i]]);
            }
        }

        return sample;
    }

    standardError(size, method) {
        validatePositiveInteger(size, "Sample size");

        if (
            method === SamplingMethod.WITHOUT_REPLACEMENT &&
            size > this.size
        ) {
            throw new SamplingError("Invalid sample size.");
        }

        let result =
            this.statistics.standardDeviation / Math.sqrt(size);

        if (method === SamplingMethod.WITHOUT_REPLACEMENT) {
            const correction = this.size === 1
                ? 0
                : Math.sqrt(
                    (this.size - size) / (this.size - 1)
                );

            result *= correction;
        }

        return result;
    }
}

class SamplingExperiment extends EventEmitter {
    constructor(population, seed = 2026) {
        super();

        if (!(population instanceof Population)) {
            throw new SamplingError("A Population instance is required.");
        }

        this.population = population;
        this.random = new RandomGenerator(seed);
        this.jobs = new Map();
    }

    async simulate({
        sampleSize,
        repetitions = 10000,
        method = SamplingMethod.WITH_REPLACEMENT,
        batchSize = 1000
    }) {
        validatePositiveInteger(sampleSize, "Sample size");
        validatePositiveInteger(repetitions, "Repetitions");
        validatePositiveInteger(batchSize, "Batch size");

        if (
            method === SamplingMethod.WITHOUT_REPLACEMENT &&
            sampleSize > this.population.size
        ) {
            throw new SamplingError("Invalid sample size.");
        }

        const jobId = randomUUID();
        const startedAt = Date.now();

        const job = {
            id: jobId,
            status: "RUNNING",
            sampleSize,
            repetitions,
            method,
            completed: 0
        };

        this.jobs.set(jobId, job);

        this.emit("experimentStarted", { ...job });

        try {
            let sum = 0;
            let sumSquares = 0;
            let minimum = Infinity;
            let maximum = -Infinity;

            // Online aggregation avoids storing every simulated mean.
            while (job.completed < repetitions) {
                const count = Math.min(
                    batchSize,
                    repetitions - job.completed
                );

                for (let i = 0; i < count; i++) {
                    const sample = this.population.drawSample(
                        sampleSize,
                        method,
                        this.random
                    );

                    const mean = Statistics.mean(sample);

                    sum += mean;
                    sumSquares += mean * mean;

                    minimum = Math.min(minimum, mean);
                    maximum = Math.max(maximum, mean);
                }

                job.completed += count;

                this.emit("experimentProgress", {
                    id: jobId,
                    completed: job.completed,
                    total: repetitions
                });

                // Yield to the event loop between batches.
                await new Promise(resolve => setImmediate(resolve));
            }

            const samplingMean = sum / repetitions;

            const variance = Math.max(
                0,
                (sumSquares - sum * sum / repetitions)
                / (repetitions - 1)
            );

            const result = Object.freeze({
                experimentId: jobId,
                sampleSize,
                repetitions,
                method,
                samplingMean,
                populationMean: this.population.statistics.mean,
                bias: samplingMean - this.population.statistics.mean,
                empiricalStandardError: Math.sqrt(variance),
                theoreticalStandardError:
                    this.population.standardError(sampleSize, method),
                minimum,
                maximum,
                elapsedMilliseconds: Date.now() - startedAt
            });

            job.status = "COMPLETED";

            this.emit("experimentCompleted", result);

            return result;
        } catch (error) {
            job.status = "FAILED";
            job.error = error.message;

            this.emit("experimentFailed", {
                id: jobId,
                error: error.message
            });

            throw error;
        }
    }

    async centralLimitTheorem(sampleSizes, repetitions = 10000) {
        if (!Array.isArray(sampleSizes) || sampleSizes.length === 0) {
            throw new SamplingError("Sample sizes are required.");
        }

        const results = [];

        for (const sampleSize of sampleSizes) {
            const result = await this.simulate({
                sampleSize,
                repetitions,
                method: SamplingMethod.WITH_REPLACEMENT
            });

            results.push(result);
        }

        return results;
    }

    async lawOfLargeNumbers(sampleSizes) {
        const results = [];

        for (const sampleSize of sampleSizes) {
            const sample = this.population.drawSample(
                sampleSize,
                SamplingMethod.WITH_REPLACEMENT,
                this.random
            );

            const sampleMean = Statistics.mean(sample);

            results.push({
                sampleSize,
                sampleMean,
                populationMean: this.population.statistics.mean,
                absoluteError: Math.abs(
                    sampleMean - this.population.statistics.mean
                )
            });
        }

        return results;
    }

    getJob(jobId) {
        const job = this.jobs.get(jobId);

        return job ? Object.freeze({ ...job }) : null;
    }
}

function confidenceInterval(
    estimate,
    standardError,
    confidenceLevel = 0.95
) {
    validateNumber(estimate, "Estimate");
    validateNumber(standardError, "Standard error");

    if (standardError < 0) {
        throw new SamplingError("Standard error cannot be negative.");
    }

    const criticalValues = new Map([
        [0.90, 1.645],
        [0.95, 1.96],
        [0.99, 2.576]
    ]);

    const criticalValue = criticalValues.get(confidenceLevel);

    if (criticalValue === undefined) {
        throw new SamplingError(
            "Supported confidence levels are 0.90, 0.95 and 0.99."
        );
    }

    const margin = criticalValue * standardError;

    return Object.freeze({
        estimate,
        standardError,
        confidenceLevel,
        lowerBound: estimate - margin,
        upperBound: estimate + margin
    });
}

async function exportResults(results) {
    const filename = path.resolve(
        process.cwd(),
        "sampling_results.json"
    );

    // Write to a temporary file before replacing the output.
    const temporaryFile = `${filename}.${randomUUID()}.tmp`;

    try {
        await fs.writeFile(
            temporaryFile,
            JSON.stringify(results, null, 2),
            { encoding: "utf8", flag: "wx" }
        );

        await fs.rename(temporaryFile, filename);
    } catch (error) {
        await fs.rm(temporaryFile, { force: true }).catch(() => {});
        throw new Error(`Result export failed: ${error.message}`);
    }
}

async function main() {
    const observations = [
        ...Array(500).fill(5),
        ...Array(250).fill(15),
        ...Array(150).fill(30),
        ...Array(100).fill(100)
    ];

    const population = new Population(
        "Customer Transaction Values",
        observations
    );

    const experiment = new SamplingExperiment(population, 2026);

    experiment.on("experimentStarted", job => {
        console.log(`Started experiment ${job.id}`);
    });

    experiment.on("experimentProgress", progress => {
        if (progress.completed === progress.total) {
            console.log("Simulation batch processing completed.");
        }
    });

    experiment.on("experimentFailed", failure => {
        console.error("Experiment failed:", failure.error);
    });

    console.log("\nPOPULATION");
    console.log(population.statistics);

    console.log("\nSAMPLE");
    const sample = population.drawSample(
        30,
        SamplingMethod.WITHOUT_REPLACEMENT,
        new RandomGenerator(100)
    );

    console.log({
        size: sample.length,
        mean: Statistics.mean(sample),
        variance: Statistics.sampleVariance(sample)
    });

    console.log("\nCENTRAL LIMIT THEOREM");

    const clt = await experiment.centralLimitTheorem(
        [2, 5, 10, 30, 50, 100],
        10000
    );

    for (const result of clt) {
        console.log({
            sampleSize: result.sampleSize,
            samplingMean: result.samplingMean.toFixed(4),
            theoreticalSE:
                result.theoreticalStandardError.toFixed(4),
            empiricalSE:
                result.empiricalStandardError.toFixed(4)
        });
    }

    console.log("\nLAW OF LARGE NUMBERS");

    const lln = await experiment.lawOfLargeNumbers([
        10, 50, 100, 500, 1000, 5000
    ]);

    console.table(lln);

    console.log("\nFINITE POPULATION CORRECTION");

    console.table([10, 50, 100, 250].map(size => ({
        sampleSize: size,
        withReplacement: population.standardError(
            size,
            SamplingMethod.WITH_REPLACEMENT
        ),
        withoutReplacement: population.standardError(
            size,
            SamplingMethod.WITHOUT_REPLACEMENT
        )
    })));

    const estimate = clt[clt.length - 1].samplingMean;

    console.log("\nCONFIDENCE INTERVAL");

    console.log(
        confidenceInterval(
            estimate,
            clt[clt.length - 1].theoreticalStandardError
        )
    );

    await exportResults({
        population: population.statistics,
        clt,
        lln
    });

    console.log("\nResults saved to sampling_results.json");
}

async function runTests() {
    const population = new Population("Test", [10, 20, 30, 40, 50]);

    if (population.statistics.mean !== 30) {
        throw new Error("Population mean test failed.");
    }

    if (population.statistics.variance !== 200) {
        throw new Error("Population variance test failed.");
    }

    const se = population.standardError(
        4,
        SamplingMethod.WITH_REPLACEMENT
    );

    if (Math.abs(se - Math.sqrt(50)) > 1e-10) {
        throw new Error("Standard error test failed.");
    }

    const random = new RandomGenerator(42);

    const sample = population.drawSample(
        3,
        SamplingMethod.WITHOUT_REPLACEMENT,
        random
    );

    if (new Set(sample).size !== 3) {
        throw new Error("Sampling without replacement failed.");
    }

    let failed = false;

    try {
        population.drawSample(
            6,
            SamplingMethod.WITHOUT_REPLACEMENT,
            random
        );
    } catch (error) {
        failed = error instanceof SamplingError;
    }

    if (!failed) {
        throw new Error("Invalid sample was accepted.");
    }

    const interval = confidenceInterval(30, 2);

    if (!(interval.lowerBound < 30 && interval.upperBound > 30)) {
        throw new Error("Confidence interval test failed.");
    }

    console.log("All JavaScript tests passed.");
}

if (require.main === module) {
    runTests()
        .then(main)
        .catch(error => {
            console.error(error);
            process.exitCode = 1;
        });
}

module.exports = {
    Population,
    SamplingExperiment,
    SamplingMethod,
    SamplingError,
    Statistics,
    RandomGenerator,
    confidenceInterval
};
