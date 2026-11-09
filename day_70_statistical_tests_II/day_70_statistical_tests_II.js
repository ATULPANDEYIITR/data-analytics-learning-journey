"use strict";

/*
 * Statistical Tests II
 * Event-driven statistical analysis using Node.js.
 *
 * Features:
 * - Chi-square goodness-of-fit
 * - Chi-square independence
 * - One-sample proportion z-test
 * - Two-sample proportion z-test
 * - Asynchronous analysis execution
 * - Event-based result notifications
 * - Policy evaluation and structured reporting
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

class StatisticalError extends Error {
    constructor(message) {
        super(message);
        this.name = "StatisticalError";
    }
}

const TestType = Object.freeze({
    GOODNESS_OF_FIT: "chi_square_goodness_of_fit",
    INDEPENDENCE: "chi_square_independence",
    ONE_PROPORTION: "one_sample_proportion",
    TWO_PROPORTION: "two_sample_proportion"
});

function validateAlpha(alpha) {
    if (!Number.isFinite(alpha) || alpha <= 0 || alpha >= 1) {
        throw new StatisticalError(
            "Alpha must be strictly between zero and one."
        );
    }
}

function validateCounts(values, name) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new StatisticalError(`${name} cannot be empty.`);
    }

    for (const value of values) {
        if (
            !Number.isSafeInteger(value) ||
            value < 0
        ) {
            throw new StatisticalError(
                `${name} must contain non-negative safe integers.`
            );
        }
    }
}

function validateFinitePositive(values, name) {
    if (
        !Array.isArray(values) ||
        values.some(
            value => !Number.isFinite(value) || value <= 0
        )
    ) {
        throw new StatisticalError(
            `${name} must contain positive finite values.`
        );
    }
}

function regularizedGammaQ(a, x) {
    if (a <= 0 || x < 0 || !Number.isFinite(a)) {
        throw new StatisticalError("Invalid gamma parameters.");
    }

    if (x === 0) return 1;
    if (x === Infinity) return 0;

    const epsilon = 1e-14;
    const minimum = 1e-300;
    const logFactor =
        -x + a * Math.log(x) - logGamma(a);

    if (x < a + 1) {
        let ap = a;
        let term = 1 / a;
        let sum = term;

        for (let i = 0; i < 10000; i++) {
            ap++;
            term *= x / ap;
            sum += term;

            if (Math.abs(term) < Math.abs(sum) * epsilon) {
                return Math.max(
                    0,
                    Math.min(1, 1 - sum * Math.exp(logFactor))
                );
            }
        }

        throw new StatisticalError(
            "Gamma series failed to converge."
        );
    }

    let b = x + 1 - a;
    let c = 1 / minimum;
    let d = 1 / b;
    let h = d;

    for (let i = 1; i <= 10000; i++) {
        const an = -i * (i - a);
        b += 2;

        d = an * d + b;
        if (Math.abs(d) < minimum) d = minimum;

        c = b + an / c;
        if (Math.abs(c) < minimum) c = minimum;

        d = 1 / d;
        const delta = d * c;
        h *= delta;

        if (Math.abs(delta - 1) < epsilon) {
            return Math.max(
                0,
                Math.min(1, Math.exp(logFactor) * h)
            );
        }
    }

    throw new StatisticalError(
        "Gamma continued fraction failed to converge."
    );
}

function logGamma(z) {
    const coefficients = [
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    ];

    if (z < 0.5) {
        return Math.log(Math.PI) -
            Math.log(Math.sin(Math.PI * z)) -
            logGamma(1 - z);
    }

    z -= 1;

    let x = 0.99999999999980993;

    for (let i = 0; i < coefficients.length; i++) {
        x += coefficients[i] / (z + i + 1);
    }

    const t = z + coefficients.length - 0.5;

    return (
        0.5 * Math.log(2 * Math.PI) +
        (z + 0.5) * Math.log(t) -
        t +
        Math.log(x)
    );
}

function chiSquarePValue(statistic, df) {
    if (
        !Number.isFinite(statistic) ||
        statistic < 0 ||
        !Number.isInteger(df) ||
        df <= 0
    ) {
        throw new StatisticalError(
            "Invalid chi-square statistic or degrees of freedom."
        );
    }

    return regularizedGammaQ(df / 2, statistic / 2);
}

function normalTwoSidedPValue(z) {
    // Abramowitz-Stegun approximation to the normal tail.
    const x = Math.abs(z) / Math.SQRT2;
    const t = 1 / (1 + 0.3275911 * x);

    const erf = 1 -
        (
            (
                (
                    (
                        1.061405429 * t -
                        1.453152027
                    ) * t +
                    1.421413741
                ) * t -
                0.284496736
            ) * t +
            0.254829592
        ) * t * Math.exp(-x * x);

    return Math.max(0, Math.min(1, 1 - erf));
}

function createResult(
    testName,
    statistic,
    df,
    pValue,
    alpha,
    sampleSize,
    effectSize,
    interpretation
) {
    return Object.freeze({
        testName,
        statistic,
        degreesOfFreedom: df,
        pValue,
        alpha,
        rejectNull: pValue < alpha,
        sampleSize,
        effectSize,
        interpretation
    });
}

function goodnessOfFit(observed, expected, alpha = 0.05) {
    validateAlpha(alpha);
    validateCounts(observed, "Observed counts");
    validateFinitePositive(expected, "Expected counts");

    if (observed.length !== expected.length ||
        observed.length < 2) {
        throw new StatisticalError(
            "At least two matching categories are required."
        );
    }

    const n = observed.reduce((a, b) => a + b, 0);
    const expectedTotal = expected.reduce((a, b) => a + b, 0);

    if (n === 0 || Math.abs(n - expectedTotal) > 1e-8) {
        throw new StatisticalError(
            "Observed and expected totals must match and be positive."
        );
    }

    const statistic = observed.reduce(
        (sum, value, index) =>
            sum + (value - expected[index]) ** 2 / expected[index],
        0
    );

    const df = observed.length - 1;
    const p = chiSquarePValue(statistic, df);

    return createResult(
        TestType.GOODNESS_OF_FIT,
        statistic,
        df,
        p,
        alpha,
        n,
        Math.sqrt(statistic / n),
        p < alpha
            ? "Observed frequencies differ significantly."
            : "No statistically significant distribution difference."
    );
}

function independenceTest(table, alpha = 0.05, yates = false) {
    validateAlpha(alpha);

    if (!Array.isArray(table) || table.length < 2) {
        throw new StatisticalError(
            "At least two contingency table rows are required."
        );
    }

    const columns = table[0].length;

    if (columns < 2) {
        throw new StatisticalError(
            "At least two columns are required."
        );
    }

    const rowTotals = [];

    for (const row of table) {
        validateCounts(row, "Contingency table");

        if (row.length !== columns) {
            throw new StatisticalError(
                "Contingency table must be rectangular."
            );
        }

        rowTotals.push(row.reduce((a, b) => a + b, 0));
    }

    const columnTotals = Array(columns).fill(0);

    for (const row of table) {
        row.forEach((value, index) => {
            columnTotals[index] += value;
        });
    }

    const n = rowTotals.reduce((a, b) => a + b, 0);

    if (
        n === 0 ||
        rowTotals.some(x => x === 0) ||
        columnTotals.some(x => x === 0)
    ) {
        throw new StatisticalError(
            "Every row and column must contain observations."
        );
    }

    let statistic = 0;
    let minimumExpected = Infinity;

    table.forEach((row, i) => {
        row.forEach((observed, j) => {
            const expected = rowTotals[i] * columnTotals[j] / n;
            minimumExpected = Math.min(minimumExpected, expected);

            let difference = Math.abs(observed - expected);

            if (yates && table.length === 2 && columns === 2) {
                difference = Math.max(0, difference - 0.5);
            }

            statistic += difference ** 2 / expected;
        });
    });

    const df = (table.length - 1) * (columns - 1);
    const p = chiSquarePValue(statistic, df);

    const v = Math.sqrt(
        statistic / (n * Math.min(table.length - 1, columns - 1))
    );

    return createResult(
        TestType.INDEPENDENCE,
        statistic,
        df,
        p,
        alpha,
        n,
        v,
        (p < alpha
            ? "Evidence of association between categorical variables."
            : "No significant evidence of association.") +
        (minimumExpected < 5
            ? " Warning: expected frequency below five."
            : "")
    );
}

function oneProportionTest(
    successes,
    trials,
    p0,
    alpha = 0.05
) {
    validateAlpha(alpha);

    if (
        !Number.isSafeInteger(successes) ||
        !Number.isSafeInteger(trials) ||
        trials <= 0 ||
        successes < 0 ||
        successes > trials ||
        !Number.isFinite(p0) ||
        p0 <= 0 ||
        p0 >= 1
    ) {
        throw new StatisticalError("Invalid one-proportion inputs.");
    }

    const observed = successes / trials;
    const se = Math.sqrt(p0 * (1 - p0) / trials);
    const z = (observed - p0) / se;
    const p = normalTwoSidedPValue(z);

    return createResult(
        TestType.ONE_PROPORTION,
        z,
        0,
        p,
        alpha,
        trials,
        observed - p0,
        p < alpha
            ? "Population proportion differs significantly from p0."
            : "Insufficient evidence of a proportion difference."
    );
}

function twoProportionTest(
    x1,
    n1,
    x2,
    n2,
    alpha = 0.05
) {
    validateAlpha(alpha);

    const values = [x1, n1, x2, n2];

    if (
        values.some(v => !Number.isSafeInteger(v)) ||
        n1 <= 0 || n2 <= 0 ||
        x1 < 0 || x1 > n1 ||
        x2 < 0 || x2 > n2
    ) {
        throw new StatisticalError("Invalid two-proportion inputs.");
    }

    const p1 = x1 / n1;
    const p2 = x2 / n2;
    const pooled = (x1 + x2) / (n1 + n2);

    if (pooled === 0 || pooled === 1) {
        throw new StatisticalError("Pooled variance is zero.");
    }

    const se = Math.sqrt(
        pooled * (1 - pooled) * (1 / n1 + 1 / n2)
    );

    const z = (p1 - p2) / se;
    const p = normalTwoSidedPValue(z);

    return createResult(
        TestType.TWO_PROPORTION,
        z,
        0,
        p,
        alpha,
        n1 + n2,
        p1 - p2,
        p < alpha
            ? "The population proportions differ significantly."
            : "Insufficient evidence of a difference."
    );
}

class AnalysisEngine extends EventEmitter {
    #results = new Map();
    #alpha;

    constructor(alpha = 0.05) {
        super();
        validateAlpha(alpha);
        this.#alpha = alpha;
    }

    get results() {
        return [...this.#results.values()];
    }

    async execute(name, operation) {
        if (typeof operation !== "function") {
            throw new StatisticalError("Operation must be a function.");
        }

        if (this.#results.has(name)) {
            throw new StatisticalError(
                `Analysis identifier already exists: ${name}`
            );
        }

        this.emit("started", { name });

        try {
            // Promise boundary permits integration with asynchronous
            // data retrieval and external analytical pipelines.
            const result = await Promise.resolve().then(
                () => operation(this.#alpha)
            );

            this.#results.set(name, Object.freeze({
                id: name,
                ...result
            }));

            this.emit("completed", this.#results.get(name));

            return this.#results.get(name);
        } catch (error) {
            this.emit("failed", {
                name,
                message: error.message
            });

            throw error;
        }
    }

    async exportReport(filename = "statistical_results.json") {
        const safeName = path.basename(filename);

        if (
            safeName !== filename ||
            !safeName.endsWith(".json")
        ) {
            throw new StatisticalError("Invalid report filename.");
        }

        const destination = path.resolve(process.cwd(), safeName);
        const temporary = `${destination}.tmp`;

        try {
            await fs.writeFile(
                temporary,
                JSON.stringify(this.results, null, 2),
                { encoding: "utf8", mode: 0o600 }
            );

            // Atomic replacement prevents partially written reports.
            await fs.rename(temporary, destination);

            this.emit("exported", { destination });
            return destination;
        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});
            throw error;
        }
    }
}

async function main() {
    const engine = new AnalysisEngine(0.05);

    engine.on("started", event => {
        console.log(`Starting: ${event.name}`);
    });

    engine.on("completed", result => {
        console.log(
            `Completed: ${result.id}, p=${result.pValue.toFixed(6)}`
        );
    });

    engine.on("failed", event => {
        console.error(`Failed: ${event.name}: ${event.message}`);
    });

    const jobs = [
        [
            "distribution",
            alpha => goodnessOfFit(
                [48, 52, 45, 55],
                [50, 50, 50, 50],
                alpha
            )
        ],
        [
            "independence",
            alpha => independenceTest(
                [[40, 20], [15, 45]],
                alpha
            )
        ],
        [
            "corrected_independence",
            alpha => independenceTest(
                [[40, 20], [15, 45]],
                alpha,
                true
            )
        ],
        [
            "one_proportion",
            alpha => oneProportionTest(120, 200, 0.5, alpha)
        ],
        [
            "two_proportions",
            alpha => twoProportionTest(
                140, 200, 110, 200, alpha
            )
        ]
    ];

    // Independent analyses run concurrently.
    const results = await Promise.all(
        jobs.map(([name, operation]) =>
            engine.execute(name, operation)
        )
    );

    console.log("\nSTATISTICAL REPORT");

    for (const result of results) {
        console.log({
            test: result.testName,
            statistic: result.statistic.toFixed(6),
            pValue: result.pValue.toFixed(8),
            rejectNull: result.rejectNull,
            effectSize: result.effectSize
        });
    }

    await engine.exportReport();
}

async function runTests() {
    const close = (a, b, tolerance = 1e-6) =>
        Math.abs(a - b) < tolerance;

    if (!close(chiSquarePValue(3.8414588207, 1), 0.05)) {
        throw new Error("Chi-square reference test failed.");
    }

    if (goodnessOfFit([50, 50], [50, 50]).pValue !== 1) {
        throw new Error("Goodness-of-fit test failed.");
    }

    if (independenceTest([[10, 10], [10, 10]]).statistic !== 0) {
        throw new Error("Independence test failed.");
    }

    if (oneProportionTest(50, 100, 0.5).statistic !== 0) {
        throw new Error("One-proportion test failed.");
    }

    if (twoProportionTest(50, 100, 50, 100).statistic !== 0) {
        throw new Error("Two-proportion test failed.");
    }

    const invalidCases = [
        () => goodnessOfFit([10, 20], [15, 15]),
        () => independenceTest([[10, 0], [0, 0]]),
        () => oneProportionTest(110, 100, 0.5),
        () => twoProportionTest(50, 100, 50, 0)
    ];

    for (const operation of invalidCases) {
        let failed = false;

        try {
            operation();
        } catch (error) {
            failed = error instanceof StatisticalError;
        }

        if (!failed) {
            throw new Error("Invalid input was not rejected.");
        }
    }

    console.log("All JavaScript statistical tests passed.");
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
    goodnessOfFit,
    independenceTest,
    oneProportionTest,
    twoProportionTest,
    chiSquarePValue,
    AnalysisEngine
};
