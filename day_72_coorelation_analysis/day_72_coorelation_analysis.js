"use strict";

/*
 * Correlation Analysis Engine
 *
 * Node.js 18+
 * No external dependencies.
 *
 * Features:
 * - Pearson correlation
 * - Spearman correlation with average ranks
 * - Kendall tau-b
 * - Partial correlation
 * - Asynchronous permutation testing
 * - Event-driven analysis
 * - Input validation and analysis policies
 * - Structured reporting
 */

const { EventEmitter } = require("node:events");
const { readFile, writeFile } = require("node:fs/promises");
const { randomInt } = require("node:crypto");

class AnalysisError extends Error {}
class ValidationError extends AnalysisError {}
class InsufficientDataError extends AnalysisError {}

const METHODS = Object.freeze({
    PEARSON: "pearson",
    SPEARMAN: "spearman",
    KENDALL: "kendall"
});

function validatePairs(x, y, minimum = 3) {
    if (!Array.isArray(x) || !Array.isArray(y)) {
        throw new ValidationError("Inputs must be arrays.");
    }

    if (x.length !== y.length) {
        throw new ValidationError("Array lengths must match.");
    }

    const cleanX = [];
    const cleanY = [];

    for (let i = 0; i < x.length; i++) {
        if (x[i] == null || y[i] == null) continue;

        const a = Number(x[i]);
        const b = Number(y[i]);

        if (!Number.isFinite(a) || !Number.isFinite(b)) {
            throw new ValidationError(
                `Invalid numeric observation at index ${i}.`
            );
        }

        cleanX.push(a);
        cleanY.push(b);
    }

    if (cleanX.length < minimum) {
        throw new InsufficientDataError(
            `At least ${minimum} paired observations are required.`
        );
    }

    return [cleanX, cleanY];
}

function mean(values) {
    return values.reduce((sum, value) => sum + value, 0)
        / values.length;
}

function pearson(x, y) {
    [x, y] = validatePairs(x, y);

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
        throw new ValidationError(
            "Correlation undefined for constant variables."
        );
    }

    return numerator / denominator;
}

function averageRanks(values) {
    const sorted = values
        .map((value, index) => ({ value, index }))
        .sort((a, b) => a.value - b.value);

    const ranks = new Array(values.length);
    let i = 0;

    while (i < sorted.length) {
        let j = i + 1;

        while (
            j < sorted.length &&
            sorted[j].value === sorted[i].value
        ) {
            j++;
        }

        const rank = (i + 1 + j) / 2;

        for (let k = i; k < j; k++) {
            ranks[sorted[k].index] = rank;
        }

        i = j;
    }

    return ranks;
}

function spearman(x, y) {
    [x, y] = validatePairs(x, y);

    return pearson(
        averageRanks(x),
        averageRanks(y)
    );
}

function kendallTauB(x, y) {
    [x, y] = validatePairs(x, y);

    let concordant = 0;
    let discordant = 0;
    let tiesX = 0;
    let tiesY = 0;

    for (let i = 0; i < x.length; i++) {
        for (let j = i + 1; j < x.length; j++) {
            const dx = Math.sign(x[i] - x[j]);
            const dy = Math.sign(y[i] - y[j]);

            if (dx === 0 && dy === 0) continue;

            if (dx === 0) tiesX++;
            else if (dy === 0) tiesY++;
            else if (dx === dy) concordant++;
            else discordant++;
        }
    }

    const denominator = Math.sqrt(
        (concordant + discordant + tiesX) *
        (concordant + discordant + tiesY)
    );

    if (denominator === 0) {
        throw new ValidationError(
            "Kendall tau-b is undefined."
        );
    }

    return (concordant - discordant) / denominator;
}

function interpret(value) {
    const magnitude = Math.abs(value);

    let strength;

    if (magnitude < 0.10) strength = "negligible";
    else if (magnitude < 0.30) strength = "weak";
    else if (magnitude < 0.50) strength = "moderate";
    else if (magnitude < 0.70) strength = "strong";
    else strength = "very strong";

    const direction = value > 0
        ? "positive"
        : value < 0
            ? "negative"
            : "neutral";

    return `${strength} ${direction} association`;
}

function residualize(values, confounder) {
    if (values.length !== confounder.length) {
        throw new ValidationError("Confounder length mismatch.");
    }

    const mv = mean(values);
    const mz = mean(confounder);

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < values.length; i++) {
        numerator +=
            (confounder[i] - mz) * (values[i] - mv);

        denominator += (confounder[i] - mz) ** 2;
    }

    if (denominator === 0) {
        throw new ValidationError("Constant confounder.");
    }

    const slope = numerator / denominator;
    const intercept = mv - slope * mz;

    return values.map(
        (value, i) => value - (intercept + slope * confounder[i])
    );
}

function partialCorrelation(x, y, z) {
    [x, y] = validatePairs(x, y);

    if (!Array.isArray(z) || z.length !== x.length) {
        throw new ValidationError("Invalid confounder array.");
    }

    const cleanZ = z.map(Number);

    if (!cleanZ.every(Number.isFinite)) {
        throw new ValidationError("Confounder contains invalid values.");
    }

    return pearson(
        residualize(x, cleanZ),
        residualize(y, cleanZ)
    );
}

/*
 * Cryptographically generated random indices are used for the
 * permutation sampler. The statistical test still assumes that
 * observations are exchangeable under the null hypothesis.
 */
function secureShuffle(values) {
    const result = [...values];

    for (let i = result.length - 1; i > 0; i--) {
        const j = randomInt(i + 1);

        [result[i], result[j]] = [result[j], result[i]];
    }

    return result;
}

class CorrelationWorkbench extends EventEmitter {
    constructor(options = {}) {
        super();

        this.minimumSampleSize = options.minimumSampleSize ?? 3;

        if (
            !Number.isInteger(this.minimumSampleSize) ||
            this.minimumSampleSize < 3
        ) {
            throw new ValidationError(
                "Minimum sample size must be an integer >= 3."
            );
        }

        this.history = new Map();
        this.nextId = 1;
    }

    analyze(name, x, y) {
        if (typeof name !== "string" || !name.trim()) {
            throw new ValidationError("Analysis name is required.");
        }

        [x, y] = validatePairs(
            x,
            y,
            this.minimumSampleSize
        );

        const calculations = [
            [METHODS.PEARSON, pearson],
            [METHODS.SPEARMAN, spearman],
            [METHODS.KENDALL, kendallTauB]
        ];

        const metrics = {};

        for (const [method, calculate] of calculations) {
            const coefficient = calculate(x, y);

            metrics[method] = {
                coefficient,
                interpretation: interpret(coefficient)
            };
        }

        const record = Object.freeze({
            id: this.nextId++,
            name: name.trim(),
            sampleSize: x.length,
            metrics,
            timestamp: new Date().toISOString()
        });

        this.history.set(record.id, record);

        this.emit("analysisCompleted", record);

        return record;
    }

    async permutationTest(
        x,
        y,
        iterations = 2000,
        alpha = 0.05
    ) {
        [x, y] = validatePairs(
            x,
            y,
            this.minimumSampleSize
        );

        if (!Number.isInteger(iterations) || iterations < 100) {
            throw new ValidationError(
                "At least 100 permutations are required."
            );
        }

        if (!(alpha > 0 && alpha < 1)) {
            throw new ValidationError("Invalid significance level.");
        }

        const observed = pearson(x, y);
        let extreme = 0;

        for (let i = 0; i < iterations; i++) {
            const shuffled = secureShuffle(y);

            if (
                Math.abs(pearson(x, shuffled)) >=
                Math.abs(observed)
            ) {
                extreme++;
            }

            // Yield periodically to avoid monopolizing the event loop.
            if ((i + 1) % 100 === 0) {
                this.emit("permutationProgress", {
                    completed: i + 1,
                    total: iterations
                });

                await new Promise(resolve => setImmediate(resolve));
            }
        }

        const pValue = (extreme + 1) / (iterations + 1);

        const result = Object.freeze({
            observed,
            pValue,
            iterations,
            alpha,
            significant: pValue < alpha
        });

        this.emit("permutationCompleted", result);

        return result;
    }

    getHistory() {
        return [...this.history.values()];
    }

    getAnalysis(id) {
        return this.history.get(id) ?? null;
    }

    async exportJSON(filePath) {
        const payload = JSON.stringify(
            this.getHistory(),
            null,
            2
        );

        await writeFile(filePath, payload, {
            encoding: "utf8",
            mode: 0o600
        });
    }
}

function createScenario() {
    const x = [1, 2, 3, 4, 5, 6];
    const y = [2, 4, 6, 8, 10, 12];

    const monotonicX = [1, 2, 3, 4, 5, 6];
    const monotonicY = [1, 4, 9, 16, 25, 36];

    const tiedX = [1, 2, 2, 4, 5, 5];
    const tiedY = [2, 1, 3, 4, 4, 6];

    const rng = (seed) => {
        let state = seed >>> 0;

        return () => {
            state = (1664525 * state + 1013904223) >>> 0;
            return state / 4294967296;
        };
    };

    const random = rng(42);
    const z = [];
    const a = [];
    const b = [];

    for (let i = 0; i < 100; i++) {
        const common = i;

        z.push(common);

        a.push(
            3 * common + (random() - 0.5) * 16
        );

        b.push(
            2.5 * common + (random() - 0.5) * 16
        );
    }

    return {
        x,
        y,
        monotonicX,
        monotonicY,
        tiedX,
        tiedY,
        a,
        b,
        z
    };
}

async function main() {
    const engine = new CorrelationWorkbench({
        minimumSampleSize: 3
    });

    engine.on("analysisCompleted", result => {
        console.log(`Completed: ${result.name}`);
    });

    engine.on("permutationProgress", progress => {
        if (progress.completed % 500 === 0) {
            console.log(
                `Permutation progress: ${progress.completed}/${progress.total}`
            );
        }
    });

    const data = createScenario();

    engine.analyze("Perfect linear relationship", data.x, data.y);

    engine.analyze(
        "Nonlinear monotonic relationship",
        data.monotonicX,
        data.monotonicY
    );

    engine.analyze("Tied observations", data.tiedX, data.tiedY);

    const adjusted = partialCorrelation(
        data.a,
        data.b,
        data.z
    );

    const raw = pearson(data.a, data.b);

    const permutation = await engine.permutationTest(
        data.x,
        data.y,
        1000
    );

    console.log("\nAnalysis history:");

    console.log(
        JSON.stringify(engine.getHistory(), null, 2)
    );

    console.log("\nConfounding demonstration:");

    console.log({
        rawPearson: raw,
        partialPearson: adjusted
    });

    console.log("\nPermutation test:");

    console.log(permutation);

    await engine.exportJSON("correlation-results.json");

    // Fundamental validation checks.
    if (Math.abs(pearson([1, 2, 3], [2, 4, 6]) - 1) > 1e-10) {
        throw new Error("Pearson verification failed.");
    }

    if (Math.abs(spearman([1, 2, 3], [1, 4, 9]) - 1) > 1e-10) {
        throw new Error("Spearman verification failed.");
    }

    if (Math.abs(kendallTauB([1, 2, 3], [1, 4, 9]) - 1) > 1e-10) {
        throw new Error("Kendall verification failed.");
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error("Analysis failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    CorrelationWorkbench,
    pearson,
    spearman,
    kendallTauB,
    partialCorrelation,
    averageRanks,
    validatePairs
};
