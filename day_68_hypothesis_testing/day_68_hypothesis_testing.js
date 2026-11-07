"use strict";

/**
 * Hypothesis Testing and Experiment Evaluation Engine.
 *
 * Features:
 * - Two-proportion Z-test
 * - Null and alternative hypotheses
 * - P-values and significance levels
 * - Type I and Type II error interpretation
 * - Statistical power estimation
 * - Confidence intervals
 * - Multiple-comparison correction
 * - Event-driven experiment lifecycle
 * - Asynchronous experiment processing
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const Alternative = Object.freeze({
    TWO_SIDED: "two-sided",
    GREATER: "greater",
    LESS: "less"
});

const ExperimentState = Object.freeze({
    CREATED: "created",
    RUNNING: "running",
    COMPLETED: "completed",
    FAILED: "failed"
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class StatisticalError extends Error {
    constructor(message) {
        super(message);
        this.name = "StatisticalError";
    }
}

function validateProbability(value, name) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value <= 0 ||
        value >= 1
    ) {
        throw new ValidationError(
            `${name} must be between 0 and 1.`
        );
    }
}

function validateCounts(successes, trials, label) {
    if (
        !Number.isSafeInteger(successes) ||
        !Number.isSafeInteger(trials) ||
        trials <= 0 ||
        successes < 0 ||
        successes > trials
    ) {
        throw new ValidationError(
            `Invalid success/trial counts for ${label}.`
        );
    }
}

function normalCDF(x) {
    // Abramowitz-Stegun approximation to the normal CDF.
    const z = Math.abs(x);
    const t = 1 / (1 + 0.2316419 * z);

    const density =
        Math.exp(-0.5 * z * z) /
        Math.sqrt(2 * Math.PI);

    const polynomial =
        t * (
            0.319381530 +
            t * (
                -0.356563782 +
                t * (
                    1.781477937 +
                    t * (
                        -1.821255978 +
                        t * 1.330274429
                    )
                )
            )
        );

    const upper = density * polynomial;

    return x >= 0 ? 1 - upper : upper;
}

function normalQuantile(probability) {
    validateProbability(probability, "Probability");

    // Acklam rational approximation.
    const a = [
        -3.969683028665376e1,
        2.209460984245205e2,
        -2.759285104469687e2,
        1.383577518672690e2,
        -3.066479806614716e1,
        2.506628277459239
    ];

    const b = [
        -5.447609879822406e1,
        1.615858368580409e2,
        -1.556989798598866e2,
        6.680131188771972e1,
        -1.328068155288572e1
    ];

    const c = [
        -7.784894002430293e-3,
        -3.223964580411365e-1,
        -2.400758277161838,
        -2.549732539343734,
        4.374664141464968,
        2.938163982698783
    ];

    const d = [
        7.784695709041462e-3,
        3.224671290700398e-1,
        2.445134137142996,
        3.754408661907416
    ];

    const low = 0.02425;
    const high = 1 - low;

    if (probability < low) {
        const q = Math.sqrt(-2 * Math.log(probability));

        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q +
                c[3]) * q + c[4]) * q + c[5]) /
            ((((d[0] * q + d[1]) * q + d[2]) * q +
                d[3]) * q + 1)
        );
    }

    if (probability > high) {
        return -normalQuantile(1 - probability);
    }

    const q = probability - 0.5;
    const r = q * q;

    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r +
            a[3]) * r + a[4]) * r + a[5]) * q /
        (((((b[0] * r + b[1]) * r + b[2]) * r +
            b[3]) * r + b[4]) * r + 1)
    );
}

function calculatePValue(z, alternative) {
    switch (alternative) {
        case Alternative.TWO_SIDED:
            return Math.min(
                1,
                2 * (1 - normalCDF(Math.abs(z)))
            );

        case Alternative.GREATER:
            return 1 - normalCDF(z);

        case Alternative.LESS:
            return normalCDF(z);

        default:
            throw new ValidationError(
                "Unsupported alternative hypothesis."
            );
    }
}

class TwoProportionTest {
    static evaluate({
        controlSuccesses,
        controlTrials,
        treatmentSuccesses,
        treatmentTrials,
        alpha = 0.05,
        alternative = Alternative.TWO_SIDED
    }) {
        validateProbability(alpha, "Alpha");

        validateCounts(
            controlSuccesses,
            controlTrials,
            "control"
        );

        validateCounts(
            treatmentSuccesses,
            treatmentTrials,
            "treatment"
        );

        if (!Object.values(Alternative).includes(alternative)) {
            throw new ValidationError("Invalid alternative.");
        }

        const pControl =
            controlSuccesses / controlTrials;

        const pTreatment =
            treatmentSuccesses / treatmentTrials;

        const difference = pTreatment - pControl;

        // The pooled proportion is used under the null hypothesis
        // that both population proportions are equal.
        const pooled =
            (controlSuccesses + treatmentSuccesses) /
            (controlTrials + treatmentTrials);

        const standardError = Math.sqrt(
            pooled * (1 - pooled) *
            (
                1 / controlTrials +
                1 / treatmentTrials
            )
        );

        let statistic;

        if (standardError === 0) {
            statistic = difference === 0
                ? 0
                : Math.sign(difference) * Infinity;
        } else {
            statistic = difference / standardError;
        }

        const pValue = Number.isFinite(statistic)
            ? calculatePValue(statistic, alternative)
            : (
                (alternative === Alternative.TWO_SIDED ||
                    (alternative === Alternative.GREATER &&
                        statistic > 0) ||
                    (alternative === Alternative.LESS &&
                        statistic < 0))
                    ? 0
                    : 1
            );

        const ciStandardError = Math.sqrt(
            pControl * (1 - pControl) / controlTrials +
            pTreatment * (1 - pTreatment) / treatmentTrials
        );

        const critical = normalQuantile(1 - alpha / 2);

        const margin = critical * ciStandardError;

        const confidenceInterval = [
            difference - margin,
            difference + margin
        ];

        return Object.freeze({
            test: "Two-proportion Z-test",
            nullHypothesis:
                "Treatment and control population proportions are equal",
            alternative,
            controlProportion: pControl,
            treatmentProportion: pTreatment,
            observedDifference: difference,
            standardError,
            statistic,
            pValue,
            alpha,
            confidenceLevel: 1 - alpha,
            confidenceInterval,
            decision: pValue < alpha
                ? "REJECT_H0"
                : "FAIL_TO_REJECT_H0"
        });
    }
}

class MultipleTesting {
    static benjaminiHochberg(pValues, alpha = 0.05) {
        validateProbability(alpha, "Alpha");

        if (!Array.isArray(pValues)) {
            throw new ValidationError(
                "P-values must be supplied as an array."
            );
        }

        for (const value of pValues) {
            if (
                typeof value !== "number" ||
                !Number.isFinite(value) ||
                value < 0 ||
                value > 1
            ) {
                throw new ValidationError(
                    "Each p-value must be between 0 and 1."
                );
            }
        }

        const sorted = pValues
            .map((pValue, index) => ({
                pValue,
                index
            }))
            .sort((a, b) => a.pValue - b.pValue);

        let largestRank = 0;

        sorted.forEach((item, index) => {
            const rank = index + 1;

            if (item.pValue <= alpha * rank / sorted.length) {
                largestRank = rank;
            }
        });

        const decisions = new Array(pValues.length).fill(false);

        for (let i = 0; i < largestRank; i++) {
            decisions[sorted[i].index] = true;
        }

        return decisions;
    }
}

class Experiment extends EventEmitter {
    constructor(configuration) {
        super();

        if (!configuration || typeof configuration !== "object") {
            throw new ValidationError(
                "Experiment configuration is required."
            );
        }

        const {
            id,
            control,
            treatment,
            alpha = 0.05,
            alternative = Alternative.TWO_SIDED
        } = configuration;

        if (
            typeof id !== "string" ||
            !/^[a-zA-Z0-9_-]{1,64}$/.test(id)
        ) {
            throw new ValidationError("Invalid experiment ID.");
        }

        this.id = id;
        this.control = Object.freeze({ ...control });
        this.treatment = Object.freeze({ ...treatment });

        this.alpha = alpha;
        this.alternative = alternative;
        this.state = ExperimentState.CREATED;
        this.result = null;

        validateProbability(alpha, "Alpha");
    }

    async execute() {
        if (this.state !== ExperimentState.CREATED) {
            throw new StatisticalError(
                `Cannot execute experiment in state ${this.state}.`
            );
        }

        this.state = ExperimentState.RUNNING;
        this.emit("started", { id: this.id });

        try {
            // Yield control to the event loop for asynchronous workflows.
            await new Promise(resolve => setImmediate(resolve));

            this.result = TwoProportionTest.evaluate({
                ...this.control,
                ...this.treatment,
                alpha: this.alpha,
                alternative: this.alternative
            });

            this.state = ExperimentState.COMPLETED;

            this.emit("completed", {
                id: this.id,
                result: this.result
            });

            return this.result;
        } catch (error) {
            this.state = ExperimentState.FAILED;

            this.emit("failed", {
                id: this.id,
                message: error.message
            });

            throw error;
        }
    }
}

async function saveReport(result, filename) {
    const safeName = /^[a-zA-Z0-9_.-]+\.json$/.test(filename);

    if (!safeName) {
        throw new ValidationError("Unsafe report filename.");
    }

    await fs.writeFile(
        filename,
        JSON.stringify(result, null, 2),
        {
            encoding: "utf8",
            flag: "wx",
            mode: 0o600
        }
    );
}

async function main() {
    const experiment = new Experiment({
        id: "website-checkout-experiment",
        control: {
            controlSuccesses: 420,
            controlTrials: 1000
        },
        treatment: {
            treatmentSuccesses: 475,
            treatmentTrials: 1000
        },
        alpha: 0.05,
        alternative: Alternative.TWO_SIDED
    });

    experiment.on("started", event => {
        console.log("Experiment started:", event.id);
    });

    experiment.on("completed", event => {
        console.log("Experiment completed:", event.id);
    });

    experiment.on("failed", event => {
        console.error("Experiment failed:", event.message);
    });

    const result = await experiment.execute();

    console.log("\nSTATISTICAL RESULTS");
    console.log(JSON.stringify(result, null, 2));

    console.log("\nERROR INTERPRETATION");
    console.log("Type I error: Rejecting a true null hypothesis.");
    console.log("Type II error: Failing to reject a false null hypothesis.");
    console.log("Statistical power: 1 - beta.");

    const decisions = MultipleTesting.benjaminiHochberg(
        [0.001, 0.015, 0.04, 0.12, 0.30],
        0.05
    );

    console.log("\nMultiple-testing decisions:", decisions);

    await saveReport(
        result,
        "hypothesis_test_report.json"
    );

    console.log("\nReport saved successfully.");
}

if (require.main === module) {
    main().catch(error => {
        console.error(`${error.name}: ${error.message}`);
        process.exitCode = 1;
    });
}

module.exports = {
    Alternative,
    ExperimentState,
    TwoProportionTest,
    MultipleTesting,
    Experiment,
    normalCDF,
    normalQuantile
};
