"use strict";

/*
 * Statistical Tests I
 * One-sample, independent two-sample, pooled two-sample,
 * and paired Student's t-tests.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const fs = require("node:fs/promises");

const TestType = Object.freeze({
    ONE_SAMPLE: "one_sample_t",
    WELCH: "independent_welch_t",
    POOLED: "independent_pooled_t",
    PAIRED: "paired_t"
});

function validateAlpha(alpha) {
    if (!Number.isFinite(alpha) || alpha <= 0 || alpha >= 1) {
        throw new RangeError("Alpha must be between zero and one.");
    }
}

function validateSample(values, name = "sample") {
    if (!Array.isArray(values) || values.length < 2) {
        throw new TypeError(
            `${name} must contain at least two observations.`
        );
    }

    if (!values.every(
        value => typeof value === "number" && Number.isFinite(value)
    )) {
        throw new TypeError(`${name} contains invalid observations.`);
    }

    return [...values];
}

function average(values) {
    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function variance(values) {
    const center = average(values);

    return values.reduce(
        (sum, value) => sum + (value - center) ** 2,
        0
    ) / (values.length - 1);
}

// Lanczos approximation.
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
        return Math.log(Math.PI) -
            Math.log(Math.abs(Math.sin(Math.PI * z))) -
            logGamma(1 - z);
    }

    z -= 1;

    let x = 0.99999999999980993;

    coefficients.forEach((coefficient, index) => {
        x += coefficient / (z + index + 1);
    });

    const t = z + 7.5;

    return (
        0.5 * Math.log(2 * Math.PI) +
        (z + 0.5) * Math.log(t) -
        t +
        Math.log(x)
    );
}

function betaFraction(a, b, x) {
    const maxIterations = 300;
    const epsilon = 3e-14;
    const tiny = 1e-300;

    const qab = a + b;
    const qap = a + 1;
    const qam = a - 1;

    let c = 1;
    let d = 1 - qab * x / qap;

    if (Math.abs(d) < tiny) d = tiny;

    d = 1 / d;

    let h = d;

    for (let m = 1; m <= maxIterations; m++) {
        const m2 = 2 * m;

        let aa = m * (b - m) * x /
            ((qam + m2) * (a + m2));

        d = 1 + aa * d;
        if (Math.abs(d) < tiny) d = tiny;

        c = 1 + aa / c;
        if (Math.abs(c) < tiny) c = tiny;

        d = 1 / d;
        h *= d * c;

        aa = -((a + m) * (qab + m) * x) /
            ((a + m2) * (qap + m2));

        d = 1 + aa * d;
        if (Math.abs(d) < tiny) d = tiny;

        c = 1 + aa / c;
        if (Math.abs(c) < tiny) c = tiny;

        d = 1 / d;

        const delta = d * c;
        h *= delta;

        if (Math.abs(delta - 1) < epsilon) {
            return h;
        }
    }

    throw new Error("Incomplete beta calculation did not converge.");
}

function regularizedBeta(x, a, b) {
    if (a <= 0 || b <= 0) {
        throw new RangeError("Beta parameters must be positive.");
    }

    if (x <= 0) return 0;
    if (x >= 1) return 1;

    const front = Math.exp(
        logGamma(a + b) -
        logGamma(a) -
        logGamma(b) +
        a * Math.log(x) +
        b * Math.log1p(-x)
    );

    if (x < (a + 1) / (a + b + 2)) {
        return front * betaFraction(a, b, x) / a;
    }

    return 1 - (
        front * betaFraction(b, a, 1 - x) / b
    );
}

function studentTPValue(statistic, df) {
    if (!Number.isFinite(df) || df <= 0) {
        throw new RangeError("Degrees of freedom must be positive.");
    }

    const x = df / (df + statistic * statistic);

    return regularizedBeta(x, df / 2, 0.5);
}

class TestResult {
    constructor({
        name,
        statistic,
        degreesOfFreedom,
        pValue,
        alpha,
        sampleSize,
        meanDifference
    }) {
        this.name = name;
        this.statistic = statistic;
        this.degreesOfFreedom = degreesOfFreedom;
        this.pValue = pValue;
        this.alpha = alpha;
        this.sampleSize = sampleSize;
        this.meanDifference = meanDifference;
        this.significant = pValue < alpha;
        this.interpretation = this.significant
            ? "Reject the null hypothesis."
            : "Fail to reject the null hypothesis.";
    }
}

function buildResult(
    name,
    statistic,
    df,
    pValue,
    alpha,
    sampleSize,
    difference
) {
    return new TestResult({
        name,
        statistic,
        degreesOfFreedom: df,
        pValue,
        alpha,
        sampleSize,
        meanDifference: difference
    });
}

function oneSampleTTest(sample, populationMean, alpha = 0.05) {
    const data = validateSample(sample);
    validateAlpha(alpha);

    if (!Number.isFinite(populationMean)) {
        throw new TypeError("Population mean must be finite.");
    }

    const n = data.length;
    const difference = average(data) - populationMean;
    const v = variance(data);

    if (v === 0) {
        if (difference === 0) {
            throw new Error("The t-statistic is undefined.");
        }

        return buildResult(
            TestType.ONE_SAMPLE,
            Math.sign(difference) * Infinity,
            n - 1,
            0,
            alpha,
            n,
            difference
        );
    }

    const statistic = difference / Math.sqrt(v / n);

    return buildResult(
        TestType.ONE_SAMPLE,
        statistic,
        n - 1,
        studentTPValue(statistic, n - 1),
        alpha,
        n,
        difference
    );
}

function independentTTest(
    groupA,
    groupB,
    {
        equalVariance = false,
        alpha = 0.05
    } = {}
) {
    const a = validateSample(groupA, "groupA");
    const b = validateSample(groupB, "groupB");

    validateAlpha(alpha);

    const n1 = a.length;
    const n2 = b.length;

    const m1 = average(a);
    const m2 = average(b);

    const v1 = variance(a);
    const v2 = variance(b);

    const difference = m1 - m2;

    let standardError;
    let df;
    let name;

    if (equalVariance) {
        df = n1 + n2 - 2;

        const pooledVariance = (
            (n1 - 1) * v1 + (n2 - 1) * v2
        ) / df;

        standardError = Math.sqrt(
            pooledVariance * (1 / n1 + 1 / n2)
        );

        name = TestType.POOLED;
    } else {
        const term1 = v1 / n1;
        const term2 = v2 / n2;

        standardError = Math.sqrt(term1 + term2);

        df = (term1 + term2) ** 2 / (
            term1 ** 2 / (n1 - 1) +
            term2 ** 2 / (n2 - 1)
        );

        name = TestType.WELCH;
    }

    if (standardError === 0) {
        if (difference === 0) {
            throw new Error("The t-statistic is undefined.");
        }

        return buildResult(
            name,
            Math.sign(difference) * Infinity,
            df,
            0,
            alpha,
            n1 + n2,
            difference
        );
    }

    const statistic = difference / standardError;

    return buildResult(
        name,
        statistic,
        df,
        studentTPValue(statistic, df),
        alpha,
        n1 + n2,
        difference
    );
}

function pairedTTest(before, after, alpha = 0.05) {
    const x = validateSample(before, "before");
    const y = validateSample(after, "after");

    validateAlpha(alpha);

    if (x.length !== y.length) {
        throw new RangeError("Paired samples must have equal lengths.");
    }

    const differences = x.map((value, index) => y[index] - value);

    const n = differences.length;
    const difference = average(differences);
    const v = variance(differences);

    if (v === 0) {
        if (difference === 0) {
            throw new Error("All paired differences are zero.");
        }

        return buildResult(
            TestType.PAIRED,
            Math.sign(difference) * Infinity,
            n - 1,
            0,
            alpha,
            n,
            difference
        );
    }

    const statistic = difference / Math.sqrt(v / n);

    return buildResult(
        TestType.PAIRED,
        statistic,
        n - 1,
        studentTPValue(statistic, n - 1),
        alpha,
        n,
        difference
    );
}

class StatisticalWorkspace {
    #results = [];
    #alpha;

    constructor(alpha = 0.05) {
        validateAlpha(alpha);
        this.#alpha = alpha;
    }

    execute(testFunction, ...args) {
        const result = testFunction(...args, this.#alpha);

        this.#results.push(result);

        return result;
    }

    get results() {
        return this.#results.map(result => ({ ...result }));
    }

    async exportJSON(filename) {
        await fs.writeFile(
            filename,
            JSON.stringify(this.#results, null, 2),
            { encoding: "utf8", flag: "wx" }
        );
    }

    async exportCSV(filename) {
        if (this.#results.length === 0) {
            throw new Error("There are no results to export.");
        }

        const headers = Object.keys(this.#results[0]);

        const escape = value => {
            const text = String(value);

            return `"${text.replaceAll('"', '""')}"`;
        };

        const rows = this.#results.map(result =>
            headers.map(header => escape(result[header])).join(",")
        );

        await fs.writeFile(
            filename,
            [headers.join(","), ...rows].join("\n"),
            { encoding: "utf8", flag: "wx" }
        );
    }

    report() {
        console.table(this.#results.map(result => ({
            test: result.name,
            statistic: Number.isFinite(result.statistic)
                ? result.statistic.toFixed(4)
                : String(result.statistic),
            df: result.degreesOfFreedom.toFixed(3),
            pValue: result.pValue.toExponential(5),
            significant: result.significant,
            difference: result.meanDifference.toFixed(4)
        })));
    }
}

async function main() {
    const workspace = new StatisticalWorkspace(0.05);

    const deliveryTimes = [28, 31, 29, 32, 30, 27, 34, 31, 29, 30];

    workspace.execute(
        oneSampleTTest,
        deliveryTimes,
        30
    );

    const control = [72, 75, 78, 74, 71, 80, 77, 76];
    const treatment = [81, 84, 79, 86, 82, 83, 85, 80];

    workspace.execute(
        independentTTest,
        control,
        treatment
    );

    workspace.execute(
        independentTTest,
        control,
        treatment,
        { equalVariance: true }
    );

    const before = [65, 70, 72, 68, 75, 71, 69, 73];
    const after = [72, 74, 76, 75, 79, 76, 74, 78];

    workspace.execute(
        pairedTTest,
        before,
        after
    );

    workspace.report();

    console.log("\nValidating numerical behavior...");

    console.assert(
        Math.abs(studentTPValue(0, 10) - 1) < 1e-10,
        "Zero t-statistic must produce p-value 1."
    );

    console.assert(
        studentTPValue(2, 10) > 0 &&
        studentTPValue(2, 10) < 1
    );

    try {
        pairedTTest([1, 2, 3], [1, 2]);
    } catch (error) {
        console.log("Expected validation:", error.message);
    }

    try {
        validateSample([1, NaN, 3]);
    } catch (error) {
        console.log("Expected validation:", error.message);
    }

    console.log("\nResults:");
    console.log(workspace.results);

    try {
        await workspace.exportJSON("statistical_results.json");
        await workspace.exportCSV("statistical_results.csv");
        console.log("Results exported successfully.");
    } catch (error) {
        console.error("Export failed:", error.message);
        process.exitCode = 1;
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error("Execution failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    oneSampleTTest,
    independentTTest,
    pairedTTest,
    studentTPValue,
    StatisticalWorkspace
};
