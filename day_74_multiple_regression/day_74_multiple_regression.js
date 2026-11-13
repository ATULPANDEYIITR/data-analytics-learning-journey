"use strict";

/*
 * MULTIPLE REGRESSION
 *
 * Event-driven regression analysis using Node.js.
 *
 * Features:
 * - Multiple numerical predictors
 * - Categorical encoding
 * - Interaction effects
 * - OLS coefficient estimation
 * - Model diagnostics
 * - Asynchronous dataset processing
 * - Prediction validation
 * - Model versioning and event notifications
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class RegressionError extends Error {}
class ValidationError extends RegressionError {}
class SingularMatrixError extends RegressionError {}

class Dataset {
    constructor(rows) {
        if (!Array.isArray(rows) || rows.length === 0) {
            throw new ValidationError("Dataset must contain records.");
        }

        this.rows = rows.map(row => Object.freeze({ ...row }));
        this.validateStructure();
    }

    validateStructure() {
        const columns = Object.keys(this.rows[0]);

        if (columns.length === 0) {
            throw new ValidationError("Dataset has no columns.");
        }

        this.rows.forEach((row, index) => {
            if (Object.keys(row).length !== columns.length ||
                columns.some(column => !(column in row))) {
                throw new ValidationError(
                    `Inconsistent columns at row ${index}.`
                );
            }
        });

        this.columns = columns;
    }

    validateModel(target, numerical, categorical) {
        for (const column of [target, ...numerical, ...categorical]) {
            if (!this.columns.includes(column)) {
                throw new ValidationError(
                    `Unknown dataset column: ${column}`
                );
            }
        }

        for (const row of this.rows) {
            for (const column of [target, ...numerical]) {
                const value = row[column];

                if (
                    typeof value !== "number" ||
                    !Number.isFinite(value)
                ) {
                    throw new ValidationError(
                        `Invalid numeric value in ${column}.`
                    );
                }
            }

            for (const column of categorical) {
                if (
                    row[column] === null ||
                    row[column] === undefined ||
                    String(row[column]).length === 0
                ) {
                    throw new ValidationError(
                        `Missing category: ${column}`
                    );
                }
            }
        }
    }
}

function solveLinearSystem(matrix, vector) {
    const n = vector.length;

    const a = matrix.map((row, i) => [
        ...row,
        vector[i]
    ]);

    for (let col = 0; col < n; col++) {
        let pivot = col;

        for (let row = col + 1; row < n; row++) {
            if (
                Math.abs(a[row][col]) >
                Math.abs(a[pivot][col])
            ) {
                pivot = row;
            }
        }

        if (Math.abs(a[pivot][col]) < 1e-12) {
            throw new SingularMatrixError(
                "Singular matrix: redundant predictors detected."
            );
        }

        [a[col], a[pivot]] = [a[pivot], a[col]];

        const divisor = a[col][col];

        for (let j = col; j <= n; j++) {
            a[col][j] /= divisor;
        }

        for (let row = 0; row < n; row++) {
            if (row === col) continue;

            const factor = a[row][col];

            for (let j = col; j <= n; j++) {
                a[row][j] -= factor * a[col][j];
            }
        }
    }

    return a.map(row => row[n]);
}

function invertMatrix(matrix) {
    const n = matrix.length;

    const a = matrix.map((row, i) => [
        ...row,
        ...Array.from(
            { length: n },
            (_, j) => i === j ? 1 : 0
        )
    ]);

    for (let col = 0; col < n; col++) {
        let pivot = col;

        for (let row = col + 1; row < n; row++) {
            if (
                Math.abs(a[row][col]) >
                Math.abs(a[pivot][col])
            ) {
                pivot = row;
            }
        }

        if (Math.abs(a[pivot][col]) < 1e-12) {
            throw new SingularMatrixError("Matrix inversion failed.");
        }

        [a[col], a[pivot]] = [a[pivot], a[col]];

        const divisor = a[col][col];

        a[col] = a[col].map(value => value / divisor);

        for (let row = 0; row < n; row++) {
            if (row === col) continue;

            const factor = a[row][col];

            a[row] = a[row].map(
                (value, j) => value - factor * a[col][j]
            );
        }
    }

    return a.map(row => row.slice(n));
}

class RegressionEngine extends EventEmitter {
    constructor(configuration) {
        super();

        this.config = Object.freeze({
            target: configuration.target,
            numerical: [...configuration.numerical],
            categorical: [...(configuration.categorical || [])],
            interactions: [...(configuration.interactions || [])]
        });

        this.version = 0;
        this.model = null;
        this.categories = new Map();
        this.termNames = [];
    }

    encode(dataset) {
        const {
            target,
            numerical,
            categorical,
            interactions
        } = this.config;

        dataset.validateModel(target, numerical, categorical);

        this.categories.clear();

        for (const column of categorical) {
            const levels = [...new Set(
                dataset.rows.map(row => String(row[column]))
            )].sort();

            if (levels.length < 2) {
                throw new ValidationError(
                    `Categorical variable ${column} needs two levels.`
                );
            }

            this.categories.set(column, levels);
        }

        const names = [
            "Intercept",
            ...numerical
        ];

        for (const [column, levels] of this.categories) {
            for (const level of levels.slice(1)) {
                names.push(`${column}[${level}]`);
            }
        }

        for (const interaction of interactions) {
            const { first, second } = interaction;

            if (
                !numerical.includes(first) ||
                !numerical.includes(second)
            ) {
                throw new ValidationError(
                    "Interactions must reference numerical predictors."
                );
            }

            names.push(`${first}:${second}`);
        }

        this.termNames = names;

        const X = dataset.rows.map(row => {
            const values = [
                1,
                ...numerical.map(column => row[column])
            ];

            for (const [column, levels] of this.categories) {
                for (const level of levels.slice(1)) {
                    values.push(
                        String(row[column]) === level ? 1 : 0
                    );
                }
            }

            for (const interaction of interactions) {
                values.push(
                    row[interaction.first] *
                    row[interaction.second]
                );
            }

            return values;
        });

        const y = dataset.rows.map(row => row[target]);

        return { X, y, names };
    }

    async fit(dataset) {
        // Yield to the event loop before processing large datasets.
        await new Promise(resolve => setImmediate(resolve));

        const { X, y, names } = this.encode(dataset);

        const n = X.length;
        const p = X[0].length;

        if (n <= p) {
            throw new ValidationError(
                "Insufficient observations for model estimation."
            );
        }

        const xtx = Array.from(
            { length: p },
            (_, i) => Array.from(
                { length: p },
                (_, j) => X.reduce(
                    (sum, row) => sum + row[i] * row[j],
                    0
                )
            )
        );

        const xty = Array.from(
            { length: p },
            (_, j) => X.reduce(
                (sum, row, i) => sum + row[j] * y[i],
                0
            )
        );

        const coefficients = solveLinearSystem(xtx, xty);

        const predictions = X.map(row =>
            row.reduce(
                (sum, value, j) =>
                    sum + value * coefficients[j],
                0
            )
        );

        const residuals = y.map(
            (value, i) => value - predictions[i]
        );

        const mean = y.reduce((a, b) => a + b, 0) / n;

        const sse = residuals.reduce(
            (sum, value) => sum + value ** 2,
            0
        );

        const sst = y.reduce(
            (sum, value) => sum + (value - mean) ** 2,
            0
        );

        if (sst < 1e-12) {
            throw new ValidationError(
                "Target variance is zero."
            );
        }

        const rSquared = 1 - sse / sst;

        const adjustedRSquared =
            1 - (1 - rSquared) * (n - 1) / (n - p);

        const rmse = Math.sqrt(sse / n);

        const mae = residuals.reduce(
            (sum, value) => sum + Math.abs(value),
            0
        ) / n;

        const inverse = invertMatrix(xtx);
        const mse = sse / (n - p);

        const standardErrors = inverse.map(
            (row, i) => Math.sqrt(
                Math.max(0, mse * row[i])
            )
        );

        const result = Object.freeze({
            version: ++this.version,
            coefficients: Object.freeze([...coefficients]),
            terms: Object.freeze([...names]),
            predictions: Object.freeze([...predictions]),
            residuals: Object.freeze([...residuals]),
            rSquared,
            adjustedRSquared,
            rmse,
            mae,
            standardErrors: Object.freeze(standardErrors),
            observations: n,
            parameters: p
        });

        this.model = result;

        this.emit("model:fitted", result);

        return result;
    }

    predict(input) {
        if (!this.model) {
            throw new RegressionError("No fitted model exists.");
        }

        const { numerical, categorical, interactions } = this.config;

        const values = [1];

        for (const column of numerical) {
            const value = input[column];

            if (
                typeof value !== "number" ||
                !Number.isFinite(value)
            ) {
                throw new ValidationError(
                    `Invalid numerical input: ${column}`
                );
            }

            values.push(value);
        }

        for (const column of categorical) {
            const levels = this.categories.get(column);
            const value = String(input[column]);

            if (!levels.includes(value)) {
                throw new ValidationError(
                    `Unknown category ${value} for ${column}.`
                );
            }

            for (const level of levels.slice(1)) {
                values.push(value === level ? 1 : 0);
            }
        }

        for (const interaction of interactions) {
            values.push(
                input[interaction.first] *
                input[interaction.second]
            );
        }

        return values.reduce(
            (sum, value, index) =>
                sum + value * this.model.coefficients[index],
            0
        );
    }

    interpret() {
        if (!this.model) {
            throw new RegressionError("Fit a model first.");
        }

        return this.model.terms.map((term, index) => ({
            term,
            estimate: this.model.coefficients[index],
            standardError: this.model.standardErrors[index],
            interpretation: term === "Intercept"
                ? "Baseline expected target value."
                : term.includes(":")
                    ? "Interaction: modifies a marginal effect."
                    : "Conditional effect holding other terms constant."
        }));
    }
}

class RegressionWorkflow extends EventEmitter {
    constructor(engine) {
        super();
        this.engine = engine;
        this.history = [];

        this.engine.on("model:fitted", result => {
            this.history.push(result);
            this.emit("analysis:completed", {
                version: result.version,
                rSquared: result.rSquared
            });
        });
    }

    async execute(rows) {
        try {
            this.emit("analysis:started");

            const dataset = new Dataset(rows);
            const result = await this.engine.fit(dataset);

            this.emit("analysis:ready", result);

            return result;
        } catch (error) {
            this.emit("analysis:failed", {
                message: error.message
            });

            throw error;
        }
    }
}

async function saveReport(result, path) {
    const report = {
        modelVersion: result.version,
        terms: result.terms.map((term, index) => ({
            term,
            coefficient: result.coefficients[index],
            standardError: result.standardErrors[index]
        })),
        metrics: {
            rSquared: result.rSquared,
            adjustedRSquared: result.adjustedRSquared,
            rmse: result.rmse,
            mae: result.mae
        }
    };

    // Private reports should be written to access-controlled storage.
    await fs.writeFile(
        path,
        JSON.stringify(report, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );
}

async function main() {
    const rows = [
        { salary: 45000, experience: 1, performance: 3,
          education: "Bachelor", department: "Sales" },
        { salary: 49000, experience: 2, performance: 4,
          education: "Bachelor", department: "Sales" },
        { salary: 53000, experience: 3, performance: 3,
          education: "Master", department: "Sales" },
        { salary: 57000, experience: 4, performance: 4,
          education: "Master", department: "Technology" },
        { salary: 65000, experience: 5, performance: 5,
          education: "Master", department: "Technology" },
        { salary: 61000, experience: 4, performance: 5,
          education: "Bachelor", department: "Technology" },
        { salary: 72000, experience: 6, performance: 4,
          education: "PhD", department: "Technology" },
        { salary: 76000, experience: 7, performance: 5,
          education: "PhD", department: "Technology" },
        { salary: 50000, experience: 2, performance: 3,
          education: "Bachelor", department: "Operations" },
        { salary: 55000, experience: 3, performance: 4,
          education: "Master", department: "Operations" },
        { salary: 59000, experience: 4, performance: 4,
          education: "Bachelor", department: "Operations" },
        { salary: 68000, experience: 6, performance: 5,
          education: "PhD", department: "Operations" },
        { salary: 48000, experience: 2, performance: 2,
          education: "Bachelor", department: "Sales" },
        { salary: 62000, experience: 5, performance: 4,
          education: "Master", department: "Sales" },
        { salary: 70000, experience: 6, performance: 5,
          education: "PhD", department: "Technology" },
        { salary: 54000, experience: 3, performance: 3,
          education: "Bachelor", department: "Operations" },
        { salary: 74000, experience: 7, performance: 5,
          education: "Master", department: "Technology" },
        { salary: 58000, experience: 4, performance: 3,
          education: "Master", department: "Sales" },
        { salary: 64000, experience: 5, performance: 5,
          education: "Bachelor", department: "Operations" },
        { salary: 79000, experience: 8, performance: 5,
          education: "PhD", department: "Technology" }
    ];

    const engine = new RegressionEngine({
        target: "salary",
        numerical: ["experience", "performance"],
        categorical: ["education", "department"],
        interactions: [
            { first: "experience", second: "performance" }
        ]
    });

    const workflow = new RegressionWorkflow(engine);

    workflow.on("analysis:started", () =>
        console.log("Analysis started.")
    );

    workflow.on("analysis:completed", event =>
        console.log("Model version:", event.version)
    );

    workflow.on("analysis:failed", event =>
        console.error("Analysis failed:", event.message)
    );

    const result = await workflow.execute(rows);

    console.log("\nCOEFFICIENTS");

    console.table(engine.interpret());

    console.log("\nMODEL METRICS");

    console.table({
        R2: result.rSquared,
        Adjusted_R2: result.adjustedRSquared,
        RMSE: result.rmse,
        MAE: result.mae
    });

    console.log("\nPREDICTION");

    console.log(
        engine.predict({
            experience: 5,
            performance: 4,
            education: "Master",
            department: "Technology"
        })
    );

    await saveReport(result, "./regression-report.json");

    console.log("\nReport saved.");
}

main().catch(error => {
    console.error("Execution error:", error.message);
    process.exitCode = 1;
});
