"use strict";

const assert = require("node:assert/strict");

class MeasureError extends Error {
    constructor(message) {
        super(message);
        this.name = "MeasureError";
    }
}

const MeasureType = Object.freeze({
    MEAN: "mean",
    MEDIAN: "median",
    MODE: "mode",
    WEIGHTED_MEAN: "weightedMean",
    GEOMETRIC_MEAN: "geometricMean",
    HARMONIC_MEAN: "harmonicMean"
});

class CentralTendencyEngine {
    static validateValues(values) {
        if (!Array.isArray(values) || values.length === 0) {
            throw new MeasureError("Values must be a non-empty array.");
        }

        if (!values.every(
            value => typeof value === "number" && Number.isFinite(value)
        )) {
            throw new MeasureError("Every observation must be a finite number.");
        }
    }

    static mean(values) {
        this.validateValues(values);
        return values.reduce((sum, value) => sum + value, 0) / values.length;
    }

    static median(values) {
        this.validateValues(values);

        const ordered = [...values].sort((a, b) => a - b);
        const middle = Math.floor(ordered.length / 2);

        return ordered.length % 2 === 1
            ? ordered[middle]
            : (ordered[middle - 1] + ordered[middle]) / 2;
    }

    static mode(values) {
        this.validateValues(values);

        const frequencies = new Map();

        for (const value of values) {
            frequencies.set(value, (frequencies.get(value) ?? 0) + 1);
        }

        const maximum = Math.max(...frequencies.values());

        if (maximum === 1) {
            return [];
        }

        return [...frequencies.entries()]
            .filter(([, frequency]) => frequency === maximum)
            .map(([value]) => value)
            .sort((a, b) => a - b);
    }

    static weightedMean(observations) {
        if (!Array.isArray(observations) || observations.length === 0) {
            throw new MeasureError("Weighted observations cannot be empty.");
        }

        let weightedTotal = 0;
        let totalWeight = 0;

        for (const observation of observations) {
            const { value, weight } = observation;

            if (!Number.isFinite(value) || !Number.isFinite(weight)) {
                throw new MeasureError("Values and weights must be finite.");
            }

            if (weight < 0) {
                throw new MeasureError("Weights cannot be negative.");
            }

            weightedTotal += value * weight;
            totalWeight += weight;
        }

        if (totalWeight === 0) {
            throw new MeasureError("Total weight must be greater than zero.");
        }

        return weightedTotal / totalWeight;
    }

    static geometricMean(values) {
        this.validateValues(values);

        if (values.some(value => value <= 0)) {
            throw new MeasureError(
                "Geometric mean requires every value to be positive."
            );
        }

        const logarithmicSum = values.reduce(
            (sum, value) => sum + Math.log(value),
            0
        );

        return Math.exp(logarithmicSum / values.length);
    }

    static harmonicMean(values) {
        this.validateValues(values);

        if (values.some(value => value <= 0)) {
            throw new MeasureError(
                "Harmonic mean requires every value to be positive."
            );
        }

        const reciprocalSum = values.reduce(
            (sum, value) => sum + 1 / value,
            0
        );

        return values.length / reciprocalSum;
    }
}

class RepositoryMetricsStream {
    constructor() {
        this.values = [];
        this.runningSum = 0;
    }

    add(value) {
        if (!Number.isFinite(value)) {
            throw new MeasureError("Metric value must be finite.");
        }

        this.values.push(value);
        this.runningSum += value;
    }

    snapshot() {
        if (this.values.length === 0) {
            throw new MeasureError("No metrics have been recorded.");
        }

        return Object.freeze({
            count: this.values.length,
            mean: this.runningSum / this.values.length,
            median: CentralTendencyEngine.median(this.values),
            mode: CentralTendencyEngine.mode(this.values)
        });
    }
}

function round(value) {
    return Number(value.toFixed(4));
}

function printDataset(name, values) {
    console.log(`\n${name}`);
    console.log("-".repeat(name.length));
    console.log("Values:", values.join(", "));
    console.log("Mean:", round(CentralTendencyEngine.mean(values)));
    console.log("Median:", round(CentralTendencyEngine.median(values)));

    const modes = CentralTendencyEngine.mode(values);
    console.log("Mode:", modes.length ? modes.join(", ") : "No mode");

    try {
        console.log(
            "Geometric mean:",
            round(CentralTendencyEngine.geometricMean(values))
        );
    } catch (error) {
        console.log("Geometric mean:", `Unavailable (${error.message})`);
    }

    try {
        console.log(
            "Harmonic mean:",
            round(CentralTendencyEngine.harmonicMean(values))
        );
    } catch (error) {
        console.log("Harmonic mean:", `Unavailable (${error.message})`);
    }
}

async function runAsynchronousMetricCollection() {
    const samples = [20, 22, 22, 24, 30, 35];

    const readings = samples.map(
        value => Promise.resolve(value)
    );

    const resolved = await Promise.all(readings);
    const stream = new RepositoryMetricsStream();

    for (const value of resolved) {
        stream.add(value);
    }

    return stream.snapshot();
}

async function main() {
    const responseTimes = [120, 125, 125, 130, 135, 140, 500];
    const deliveryMultipliers = [1.02, 1.04, 1.06, 1.03];
    const unitRates = [20, 30, 40];

    printDataset("Response Times", responseTimes);
    printDataset("Delivery Multipliers", deliveryMultipliers);
    printDataset("Unit Rates", unitRates);

    const weightedScore = CentralTendencyEngine.weightedMean([
        { value: 72, weight: 0.20 },
        { value: 84, weight: 0.30 },
        { value: 91, weight: 0.50 }
    ]);

    console.log("\nWeighted Score");
    console.log("--------------");
    console.log(round(weightedScore));

    const streamSnapshot = await runAsynchronousMetricCollection();

    console.log("\nAsynchronous Metric Snapshot");
    console.log("----------------------------");
    console.log(streamSnapshot);

    const validationCases = [
        () => CentralTendencyEngine.mean([]),
        () => CentralTendencyEngine.geometricMean([10, 0, 20]),
        () => CentralTendencyEngine.harmonicMean([10, -2, 20]),
        () => CentralTendencyEngine.weightedMean([
            { value: 10, weight: 0 },
            { value: 20, weight: 0 }
        ])
    ];

    console.log("\nValidation");
    console.log("----------");

    for (const operation of validationCases) {
        try {
            operation();
            console.log("Unexpectedly accepted.");
        } catch (error) {
            console.log(`${error.name}: ${error.message}`);
        }
    }

    assert.equal(CentralTendencyEngine.mean([2, 4, 6]), 4);
    assert.equal(CentralTendencyEngine.median([1, 2, 3, 4]), 2.5);
    assert.deepEqual(CentralTendencyEngine.mode([1, 2, 2, 3]), [2]);

    console.log("\nAssertions passed.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
