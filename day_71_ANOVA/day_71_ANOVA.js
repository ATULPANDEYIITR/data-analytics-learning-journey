"use strict";

/*
 * ANOVA Statistical Analysis and Experiment Evaluation Engine
 *
 * Node.js 18+
 *
 * Features:
 * - One-way ANOVA
 * - Balanced two-way ANOVA with interaction
 * - Variance and residual diagnostics
 * - Pairwise pooled-variance and Welch comparisons
 * - Holm multiple-testing correction
 * - Asynchronous experiment processing
 * - Event-driven analysis lifecycle
 * - Immutable experiment snapshots
 * - Validation and structured reporting
 *
 * No external npm dependencies.
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");


class AnalysisError extends Error {
    constructor(message, code = "ANALYSIS_ERROR") {
        super(message);
        this.name = "AnalysisError";
        this.code = code;
    }
}


const AnalysisState = Object.freeze({
    CREATED: "CREATED",
    VALIDATING: "VALIDATING",
    RUNNING: "RUNNING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED"
});


const DEFAULT_ALPHA = 0.05;


// ============================================================
// 1. NUMERICAL FUNCTIONS
// ============================================================

function logGamma(z) {
    const coefficients = [
        676.5203681218851,
        -1259.1392167224028,
        771.3234287776531,
        -176.6150291621406,
        12.507343278686905,
        -0.13857109526572012,
        9.984369578019572e-6,
        1.5056327351493116e-7
    ];

    if (z < 0.5) {
        return Math.log(Math.PI)
            - Math.log(Math.sin(Math.PI * z))
            - logGamma(1 - z);
    }

    z -= 1;

    let x = 0.9999999999998099;

    coefficients.forEach((c, i) => {
        x += c / (z + i + 1);
    });

    const t = z + coefficients.length - 0.5;

    return 0.5 * Math.log(2 * Math.PI)
        + (z + 0.5) * Math.log(t)
        - t
        + Math.log(x);
}


function betaFraction(a, b, x) {
    const qab = a + b;
    const qap = a + 1;
    const qam = a - 1;

    let c = 1;
    let d = 1 - qab * x / qap;

    if (Math.abs(d) < 1e-30) d = 1e-30;

    d = 1 / d;

    let h = d;

    for (let m = 1; m <= 300; m++) {
        const m2 = 2 * m;

        let aa = m * (b - m) * x
            / ((qam + m2) * (a + m2));

        d = 1 + aa * d;
        if (Math.abs(d) < 1e-30) d = 1e-30;

        c = 1 + aa / c;
        if (Math.abs(c) < 1e-30) c = 1e-30;

        d = 1 / d;
        h *= d * c;

        aa = -(a + m) * (qab + m) * x
            / ((a + m2) * (qap + m2));

        d = 1 + aa * d;
        if (Math.abs(d) < 1e-30) d = 1e-30;

        c = 1 + aa / c;
        if (Math.abs(c) < 1e-30) c = 1e-30;

        d = 1 / d;

        const delta = d * c;
        h *= delta;

        if (Math.abs(delta - 1) < 3e-14) break;
    }

    return h;
}


function regularizedBeta(x, a, b) {
    if (a <= 0 || b <= 0) {
        throw new AnalysisError("Invalid beta parameters.");
    }

    if (x <= 0) return 0;
    if (x >= 1) return 1;

    const front = Math.exp(
        logGamma(a + b)
        - logGamma(a)
        - logGamma(b)
        + a * Math.log(x)
        + b * Math.log1p(-x)
    );

    if (x < (a + 1) / (a + b + 2)) {
        return front * betaFraction(a, b, x) / a;
    }

    return 1 - front * betaFraction(b, a, 1 - x) / b;
}


function fSurvival(f, df1, df2) {
    if (df1 <= 0 || df2 <= 0) {
        throw new AnalysisError("Invalid F degrees of freedom.");
    }

    if (f <= 0) return 1;

    return regularizedBeta(
        df2 / (df2 + df1 * f),
        df2 / 2,
        df1 / 2
    );
}


function tCDF(t, df) {
    const x = df / (df + t * t);

    const probability = regularizedBeta(
        x,
        df / 2,
        0.5
    );

    return t >= 0
        ? 1 - probability / 2
        : probability / 2;
}


function tPValue(t, df) {
    return Math.min(1, 2 * (1 - tCDF(Math.abs(t), df)));
}


// ============================================================
// 2. STATISTICAL UTILITIES
// ============================================================

function mean(values) {
    return values.reduce((sum, value) => sum + value, 0)
        / values.length;
}


function variance(values) {
    if (values.length < 2) {
        throw new AnalysisError("At least two values are required.");
    }

    const avg = mean(values);

    return values.reduce(
        (sum, x) => sum + (x - avg) ** 2,
        0
    ) / (values.length - 1);
}


function sumSquares(values, center) {
    return values.reduce(
        (sum, x) => sum + (x - center) ** 2,
        0
    );
}


function median(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2
        ? sorted[middle]
        : (sorted[middle - 1] + sorted[middle]) / 2;
}


function holmCorrection(pValues) {
    const ordered = pValues
        .map((p, index) => ({ p, index }))
        .sort((a, b) => a.p - b.p);

    const adjusted = Array(pValues.length).fill(0);

    let maximum = 0;

    ordered.forEach((item, rank) => {
        maximum = Math.max(
            maximum,
            Math.min(1, (ordered.length - rank) * item.p)
        );

        adjusted[item.index] = maximum;
    });

    return adjusted;
}


// ============================================================
// 3. EXPERIMENT DOMAIN
// ============================================================

class Experiment {
    #observations;

    constructor({
        id = crypto.randomUUID(),
        name,
        observations
    }) {
        if (!name || !name.trim()) {
            throw new AnalysisError("Experiment name is required.");
        }

        if (!Array.isArray(observations) || observations.length === 0) {
            throw new AnalysisError("Observations cannot be empty.");
        }

        this.id = id;
        this.name = name;

        this.#observations = observations.map(item => {
            if (!Number.isFinite(item.value)) {
                throw new AnalysisError("Values must be finite.");
            }

            if (!item.factorA || !item.factorA.trim()) {
                throw new AnalysisError("Factor A is required.");
            }

            return Object.freeze({
                value: item.value,
                factorA: item.factorA,
                factorB: item.factorB ?? null
            });
        });

        Object.freeze(this);
    }

    get observations() {
        return this.#observations.map(item => ({ ...item }));
    }

    groups() {
        const result = new Map();

        for (const observation of this.#observations) {
            const group = observation.factorA;

            if (!result.has(group)) result.set(group, []);

            result.get(group).push(observation.value);
        }

        return result;
    }

    cells() {
        const result = new Map();

        for (const observation of this.#observations) {
            if (observation.factorB === null) {
                throw new AnalysisError(
                    "Factor B is required for two-way ANOVA."
                );
            }

            const key = JSON.stringify([
                observation.factorA,
                observation.factorB
            ]);

            if (!result.has(key)) {
                result.set(key, {
                    a: observation.factorA,
                    b: observation.factorB,
                    values: []
                });
            }

            result.get(key).values.push(observation.value);
        }

        return result;
    }
}


// ============================================================
// 4. ONE-WAY ANOVA
// ============================================================

function oneWayANOVA(experiment) {
    const groups = experiment.groups();

    if (groups.size < 2) {
        throw new AnalysisError("At least two groups are required.");
    }

    const entries = [...groups.entries()];

    if (entries.some(([, values]) => values.length < 2)) {
        throw new AnalysisError("Every group needs at least two values.");
    }

    const all = entries.flatMap(([, values]) => values);
    const grandMean = mean(all);

    const ssBetween = entries.reduce(
        (sum, [, values]) =>
            sum + values.length * (mean(values) - grandMean) ** 2,
        0
    );

    const ssWithin = entries.reduce(
        (sum, [, values]) =>
            sum + sumSquares(values, mean(values)),
        0
    );

    const dfBetween = groups.size - 1;
    const dfWithin = all.length - groups.size;

    const msBetween = ssBetween / dfBetween;
    const msWithin = ssWithin / dfWithin;

    const f = msWithin === 0
        ? (msBetween === 0 ? 0 : Infinity)
        : msBetween / msWithin;

    const p = f === Infinity
        ? 0
        : fSurvival(f, dfBetween, dfWithin);

    const totalSS = ssBetween + ssWithin;

    return Object.freeze({
        method: "One-way ANOVA",
        grandMean,
        ssBetween,
        ssWithin,
        dfBetween,
        dfWithin,
        msBetween,
        msWithin,
        fStatistic: f,
        pValue: p,
        etaSquared: totalSS ? ssBetween / totalSS : 0,
        omegaSquared: totalSS + msWithin
            ? Math.max(
                0,
                (ssBetween - dfBetween * msWithin)
                / (totalSS + msWithin)
            )
            : 0
    });
}


// ============================================================
// 5. TWO-WAY ANOVA
// ============================================================

function twoWayANOVA(experiment) {
    const cells = [...experiment.cells().values()];

    const factorA = [...new Set(cells.map(c => c.a))].sort();
    const factorB = [...new Set(cells.map(c => c.b))].sort();

    if (factorA.length < 2 || factorB.length < 2) {
        throw new AnalysisError("Both factors need at least two levels.");
    }

    if (cells.length !== factorA.length * factorB.length) {
        throw new AnalysisError("Missing factorial cells.");
    }

    const sizes = new Set(cells.map(cell => cell.values.length));

    if (sizes.size !== 1 || cells[0].values.length < 2) {
        throw new AnalysisError(
            "Two-way implementation requires balanced replication."
        );
    }

    const replication = cells[0].values.length;

    const all = cells.flatMap(cell => cell.values);
    const grand = mean(all);

    const cellMap = new Map(
        cells.map(cell => [
            JSON.stringify([cell.a, cell.b]),
            mean(cell.values)
        ])
    );

    const meansA = new Map();
    const meansB = new Map();

    for (const a of factorA) {
        const values = cells
            .filter(cell => cell.a === a)
            .flatMap(cell => cell.values);

        meansA.set(a, mean(values));
    }

    for (const b of factorB) {
        const values = cells
            .filter(cell => cell.b === b)
            .flatMap(cell => cell.values);

        meansB.set(b, mean(values));
    }

    const ssA = factorA.reduce(
        (sum, a) => sum
            + factorB.length * replication
            * (meansA.get(a) - grand) ** 2,
        0
    );

    const ssB = factorB.reduce(
        (sum, b) => sum
            + factorA.length * replication
            * (meansB.get(b) - grand) ** 2,
        0
    );

    let ssInteraction = 0;
    let ssError = 0;

    for (const cell of cells) {
        const key = JSON.stringify([cell.a, cell.b]);

        const interaction = cellMap.get(key)
            - meansA.get(cell.a)
            - meansB.get(cell.b)
            + grand;

        ssInteraction += replication * interaction ** 2;

        ssError += sumSquares(
            cell.values,
            cellMap.get(key)
        );
    }

    const dfA = factorA.length - 1;
    const dfB = factorB.length - 1;
    const dfAB = dfA * dfB;
    const dfError = factorA.length
        * factorB.length
        * (replication - 1);

    const msError = ssError / dfError;

    function effect(name, ss, df) {
        const ms = ss / df;

        const f = msError === 0
            ? (ms === 0 ? 0 : Infinity)
            : ms / msError;

        return {
            source: name,
            ss,
            df,
            ms,
            fStatistic: f,
            pValue: f === Infinity
                ? 0
                : fSurvival(f, df, dfError)
        };
    }

    return {
        factorA: effect("Factor A", ssA, dfA),
        factorB: effect("Factor B", ssB, dfB),
        interaction: effect("A x B", ssInteraction, dfAB),
        error: {
            ss: ssError,
            df: dfError,
            ms: msError
        }
    };
}


// ============================================================
// 6. ASSUMPTION DIAGNOSTICS
// ============================================================

function leveneDiagnostic(experiment) {
    const groups = experiment.groups();

    const deviations = [];

    for (const [name, values] of groups) {
        const center = median(values);

        for (const value of values) {
            deviations.push({
                value: Math.abs(value - center),
                factorA: name
            });
        }
    }

    return oneWayANOVA(
        new Experiment({
            name: "Levene diagnostic",
            observations: deviations
        })
    );
}


function jarqueBera(residuals) {
    if (residuals.length < 3) {
        throw new AnalysisError("Insufficient residuals.");
    }

    const avg = mean(residuals);

    const m2 = residuals.reduce(
        (s, x) => s + (x - avg) ** 2,
        0
    ) / residuals.length;

    if (m2 === 0) return { statistic: 0, pValue: 1 };

    const skew = residuals.reduce(
        (s, x) => s + (x - avg) ** 3,
        0
    ) / residuals.length / Math.pow(m2, 1.5);

    const kurtosis = residuals.reduce(
        (s, x) => s + (x - avg) ** 4,
        0
    ) / residuals.length / (m2 ** 2);

    const jb = residuals.length / 6 * (
        skew ** 2 + (kurtosis - 3) ** 2 / 4
    );

    // Chi-square with two degrees of freedom.
    return {
        statistic: jb,
        pValue: Math.exp(-jb / 2)
    };
}


function diagnostics(experiment) {
    const groups = experiment.groups();

    const residuals = [];

    for (const values of groups.values()) {
        const avg = mean(values);

        values.forEach(x => residuals.push(x - avg));
    }

    const varianceTest = leveneDiagnostic(experiment);
    const normalityTest = jarqueBera(residuals);

    return {
        independence: {
            status: "DESIGN_DEPENDENT",
            explanation: "Verify independence using sampling design."
        },
        homogeneity: {
            statistic: varianceTest.fStatistic,
            pValue: varianceTest.pValue,
            status: varianceTest.pValue >= DEFAULT_ALPHA
                ? "PASS"
                : "WARNING"
        },
        residualNormality: {
            ...normalityTest,
            status: normalityTest.pValue >= DEFAULT_ALPHA
                ? "PASS"
                : "WARNING"
        }
    };
}


// ============================================================
// 7. POST-HOC ANALYSIS
// ============================================================

function postHoc(experiment, equalVariances = true) {
    const groups = [...experiment.groups().entries()];
    const comparisons = [];

    for (let i = 0; i < groups.length; i++) {
        for (let j = i + 1; j < groups.length; j++) {
            const [nameA, a] = groups[i];
            const [nameB, b] = groups[j];

            const difference = mean(a) - mean(b);

            let se;
            let df;

            if (equalVariances) {
                df = a.length + b.length - 2;

                const pooled = (
                    (a.length - 1) * variance(a)
                    + (b.length - 1) * variance(b)
                ) / df;

                se = Math.sqrt(
                    pooled * (1 / a.length + 1 / b.length)
                );
            } else {
                const va = variance(a) / a.length;
                const vb = variance(b) / b.length;

                se = Math.sqrt(va + vb);

                df = (va + vb) ** 2 / (
                    va ** 2 / (a.length - 1)
                    + vb ** 2 / (b.length - 1)
                );
            }

            const t = se === 0
                ? (difference === 0 ? 0 : Math.sign(difference) * Infinity)
                : difference / se;

            const p = Number.isFinite(t)
                ? tPValue(t, df)
                : 0;

            comparisons.push({
                groupA: nameA,
                groupB: nameB,
                meanDifference: difference,
                statistic: t,
                rawPValue: p,
                method: equalVariances
                    ? "Pooled-variance pairwise t"
                    : "Welch pairwise t"
            });
        }
    }

    const adjusted = holmCorrection(
        comparisons.map(c => c.rawPValue)
    );

    return comparisons.map((comparison, index) => ({
        ...comparison,
        adjustedPValue: adjusted[index],
        significant: adjusted[index] < DEFAULT_ALPHA,
        correction: "Holm"
    }));
}


// ============================================================
// 8. EVENT-DRIVEN ANALYSIS SERVICE
// ============================================================

class AnalysisService extends EventEmitter {
    #jobs = new Map();

    async execute(experiment, method = "one-way") {
        const jobId = crypto.randomUUID();

        const job = {
            id: jobId,
            state: AnalysisState.CREATED,
            startedAt: null,
            completedAt: null,
            error: null
        };

        this.#jobs.set(jobId, job);

        try {
            job.state = AnalysisState.VALIDATING;

            this.emit("state", { ...job });

            await Promise.resolve();

            if (!(experiment instanceof Experiment)) {
                throw new AnalysisError("Invalid experiment object.");
            }

            job.state = AnalysisState.RUNNING;
            job.startedAt = new Date().toISOString();

            this.emit("state", { ...job });

            const result = await new Promise((resolve, reject) => {
                setImmediate(() => {
                    try {
                        if (method === "one-way") {
                            resolve(oneWayANOVA(experiment));
                        } else if (method === "two-way") {
                            resolve(twoWayANOVA(experiment));
                        } else {
                            throw new AnalysisError(
                                `Unsupported analysis: ${method}`
                            );
                        }
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            job.state = AnalysisState.COMPLETED;
            job.completedAt = new Date().toISOString();

            this.emit("completed", {
                job: { ...job },
                result
            });

            return {
                job: { ...job },
                result
            };

        } catch (error) {
            job.state = AnalysisState.FAILED;
            job.error = error.message;
            job.completedAt = new Date().toISOString();

            this.emit("failed", { ...job });

            throw error;
        }
    }

    getJob(jobId) {
        const job = this.#jobs.get(jobId);

        return job ? Object.freeze({ ...job }) : null;
    }
}


// ============================================================
// 9. DESCRIPTIVE REPORTING
// ============================================================

function descriptiveReport(experiment) {
    const output = {};

    for (const [name, values] of experiment.groups()) {
        output[name] = {
            n: values.length,
            mean: mean(values),
            median: median(values),
            variance: variance(values),
            standardDeviation: Math.sqrt(variance(values)),
            minimum: Math.min(...values),
            maximum: Math.max(...values)
        };
    }

    return output;
}


// ============================================================
// 10. VALIDATION TESTS
// ============================================================

function runTests() {
    const experiment = new Experiment({
        name: "Testing treatments",
        observations: [
            { value: 10, factorA: "A" },
            { value: 12, factorA: "A" },
            { value: 20, factorA: "B" },
            { value: 22, factorA: "B" }
        ]
    });

    const result = oneWayANOVA(experiment);

    if (result.dfBetween !== 1 || result.dfWithin !== 2) {
        throw new Error("One-way ANOVA test failed.");
    }

    if (!(result.fStatistic > 0)) {
        throw new Error("Invalid F statistic.");
    }

    const adjusted = holmCorrection([0.01, 0.03, 0.04]);

    if (adjusted.some(p => p < 0 || p > 1)) {
        throw new Error("Holm correction test failed.");
    }

    const factorial = new Experiment({
        name: "Factorial test",
        observations: [
            { value: 10, factorA: "A", factorB: "Low" },
            { value: 11, factorA: "A", factorB: "Low" },
            { value: 15, factorA: "A", factorB: "High" },
            { value: 16, factorA: "A", factorB: "High" },
            { value: 13, factorA: "B", factorB: "Low" },
            { value: 14, factorA: "B", factorB: "Low" },
            { value: 23, factorA: "B", factorB: "High" },
            { value: 24, factorA: "B", factorB: "High" }
        ]
    });

    const twoWay = twoWayANOVA(factorial);

    if (twoWay.interaction.df !== 1) {
        throw new Error("Two-way interaction test failed.");
    }

    console.log("All JavaScript tests passed.");
}


// ============================================================
// 11. APPLICATION
// ============================================================

async function main() {
    runTests();

    const experiment = new Experiment({
        name: "Manufacturing process comparison",
        observations: [
            ...[21, 23, 22, 24, 20, 22].map(value => ({
                value,
                factorA: "Control"
            })),
            ...[25, 27, 26, 28, 24, 27].map(value => ({
                value,
                factorA: "Process A"
            })),
            ...[30, 32, 29, 31, 33, 30].map(value => ({
                value,
                factorA: "Process B"
            }))
        ]
    });

    const service = new AnalysisService();

    service.on("state", job => {
        console.log(`Job ${job.id}: ${job.state}`);
    });

    service.on("completed", event => {
        console.log("Analysis completed:", event.job.id);
    });

    service.on("failed", event => {
        console.error("Analysis failed:", event.error);
    });

    const { job, result } = await service.execute(
        experiment,
        "one-way"
    );

    const report = {
        experiment: {
            id: experiment.id,
            name: experiment.name
        },
        job,
        descriptiveStatistics: descriptiveReport(experiment),
        anova: result,
        diagnostics: diagnostics(experiment),
        postHoc: postHoc(experiment, true),
        welchPostHoc: postHoc(experiment, false)
    };

    await fs.writeFile(
        "anova_javascript_report.json",
        JSON.stringify(report, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );

    console.log(JSON.stringify(report, null, 2));
    console.log("Report saved.");
}


if (require.main === module) {
    main().catch(error => {
        console.error(error.name, error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    Experiment,
    AnalysisService,
    oneWayANOVA,
    twoWayANOVA,
    diagnostics,
    postHoc,
    holmCorrection
};
