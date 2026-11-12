"use strict";

/*
 * Regression Fundamentals
 * Simple Linear Regression using ordinary least squares.
 *
 * Node.js 18+.
 *
 * Includes:
 * - Model fitting
 * - Event-driven model lifecycle
 * - Predictions
 * - Residual analysis
 * - Regression metrics
 * - Assumption diagnostics
 * - Input validation
 * - Asynchronous CSV loading
 * - Automated tests
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");

class RegressionError extends Error {}
class ValidationError extends RegressionError {}
class ModelNotFittedError extends RegressionError {}

const ModelState = Object.freeze({
    UNFITTED: "UNFITTED",
    FITTED: "FITTED",
    INVALIDATED: "INVALIDATED"
});

class RegressionDataset {
    constructor(observations) {
        if (!Array.isArray(observations) || observations.length < 3) {
            throw new ValidationError(
                "At least three observations are required."
            );
        }

        this.observations = observations.map((row, index) => {
            if (
                !row ||
                !Number.isFinite(row.x) ||
                !Number.isFinite(row.y)
            ) {
                throw new ValidationError(
                    `Invalid observation at index ${index}.`
                );
            }

            return Object.freeze({
                x: row.x,
                y: row.y
            });
        });

        Object.freeze(this.observations);
    }

    get size() {
        return this.observations.length;
    }

    get x() {
        return this.observations.map(row => row.x);
    }

    get y() {
        return this.observations.map(row => row.y);
    }
}

class RegressionModel extends EventEmitter {
    constructor(options = {}) {
        super();

        this.varianceTolerance = options.varianceTolerance ?? 1e-12;

        if (
            !Number.isFinite(this.varianceTolerance) ||
            this.varianceTolerance <= 0
        ) {
            throw new ValidationError("Invalid variance tolerance.");
        }

        this.state = ModelState.UNFITTED;
        this.parameters = null;
        this.trainingData = null;
        this.version = 0;
    }

    fit(dataset) {
        if (!(dataset instanceof RegressionDataset)) {
            throw new ValidationError(
                "Expected a RegressionDataset instance."
            );
        }

        const observations = dataset.observations;
        const n = observations.length;

        const xMean = observations.reduce(
            (sum, row) => sum + row.x, 0
        ) / n;

        const yMean = observations.reduce(
            (sum, row) => sum + row.y, 0
        ) / n;

        let sxx = 0;
        let syy = 0;
        let sxy = 0;

        for (const row of observations) {
            const dx = row.x - xMean;
            const dy = row.y - yMean;

            sxx += dx * dx;
            syy += dy * dy;
            sxy += dx * dy;
        }

        if (sxx <= this.varianceTolerance) {
            throw new ValidationError(
                "Predictor has insufficient variance."
            );
        }

        const slope = sxy / sxx;
        const intercept = yMean - slope * xMean;

        const fittedValues = [];
        const residuals = [];

        let sse = 0;
        let absoluteError = 0;

        for (const row of observations) {
            const predicted = intercept + slope * row.x;
            const residual = row.y - predicted;

            fittedValues.push(predicted);
            residuals.push(residual);

            sse += residual * residual;
            absoluteError += Math.abs(residual);
        }

        const rSquared = syy > this.varianceTolerance
            ? 1 - sse / syy
            : (sse <= this.varianceTolerance ? 1 : 0);

        const mse = sse / n;

        const adjustedRSquared =
            1 - (1 - rSquared) * (n - 1) / (n - 2);

        const residualVariance = sse / (n - 2);

        const slopeStandardError = Math.sqrt(
            residualVariance / sxx
        );

        const interceptStandardError = Math.sqrt(
            residualVariance *
            (1 / n + xMean * xMean / sxx)
        );

        // Build the complete model state before publishing the event.
        const parameters = Object.freeze({
            slope,
            intercept,
            xMean,
            yMean,
            sxx,
            syy,
            sse,
            fittedValues: Object.freeze(fittedValues),
            residuals: Object.freeze(residuals),
            metrics: Object.freeze({
                mae: absoluteError / n,
                mse,
                rmse: Math.sqrt(mse),
                rSquared,
                adjustedRSquared,
                residualStandardError: Math.sqrt(residualVariance),
                slopeStandardError,
                interceptStandardError
            })
        });

        this.parameters = parameters;
        this.trainingData = dataset;
        this.state = ModelState.FITTED;
        this.version += 1;

        this.emit("model:fitted", {
            version: this.version,
            observations: n,
            slope,
            intercept
        });

        return this;
    }

    ensureFitted() {
        if (this.state !== ModelState.FITTED) {
            throw new ModelNotFittedError(
                "The model must be fitted before prediction."
            );
        }
    }

    predictOne(x) {
        this.ensureFitted();

        if (!Number.isFinite(x)) {
            throw new ValidationError(
                "Prediction input must be a finite number."
            );
        }

        return (
            this.parameters.intercept +
            this.parameters.slope * x
        );
    }

    predict(values) {
        if (!Array.isArray(values)) {
            throw new ValidationError("Expected an array of inputs.");
        }

        return values.map(value => this.predictOne(value));
    }

    getMetrics() {
        this.ensureFitted();
        return this.parameters.metrics;
    }

    getResiduals() {
        this.ensureFitted();

        return this.trainingData.observations.map((row, index) => ({
            actual: row.y,
            predicted: this.parameters.fittedValues[index],
            residual: this.parameters.residuals[index]
        }));
    }

    confidenceIntervalSlope(criticalValue = 1.96) {
        this.ensureFitted();

        if (
            !Number.isFinite(criticalValue) ||
            criticalValue <= 0
        ) {
            throw new ValidationError(
                "Critical value must be positive."
            );
        }

        const { slope, slopeStandardError } = this.parameters.metrics;

        return Object.freeze({
            lower: slope - criticalValue * slopeStandardError,
            upper: slope + criticalValue * slopeStandardError
        });
    }

    diagnose() {
        this.ensureFitted();

        const residuals = this.parameters.residuals;
        const n = residuals.length;

        const mean = residuals.reduce(
            (sum, value) => sum + value, 0
        ) / n;

        const variance = residuals.reduce(
            (sum, value) => sum + (value - mean) ** 2, 0
        ) / (n - 1);

        const skewness = variance > 0
            ? residuals.reduce(
                (sum, value) => sum + ((value - mean) / Math.sqrt(variance)) ** 3,
                0
            ) / n
            : 0;

        const lagNumerator = residuals
            .slice(1)
            .reduce(
                (sum, value, index) =>
                    sum + value * residuals[index],
                0
            );

        const denominator = residuals.reduce(
            (sum, value) => sum + value * value,
            0
        );

        const lagCorrelation = denominator > 0
            ? lagNumerator / denominator
            : 0;

        const ordered = this.trainingData.observations
            .map((row, index) => ({
                predicted: this.parameters.fittedValues[index],
                residual: residuals[index]
            }))
            .sort((a, b) => a.predicted - b.predicted);

        const split = Math.floor(n / 2);

        const sampleVariance = values => {
            if (values.length < 2) return 0;

            const avg = values.reduce((a, b) => a + b, 0) / values.length;

            return values.reduce(
                (sum, value) => sum + (value - avg) ** 2,
                0
            ) / (values.length - 1);
        };

        const lowVariance = sampleVariance(
            ordered.slice(0, split).map(row => row.residual)
        );

        const highVariance = sampleVariance(
            ordered.slice(split).map(row => row.residual)
        );

        const varianceRatio =
            Math.max(lowVariance, highVariance) /
            Math.max(Math.min(lowVariance, highVariance), 1e-15);

        return Object.freeze({
            meanResidual: mean,
            residualVariance: variance,
            skewness,
            lagCorrelation,
            varianceRatio,
            indicators: Object.freeze({
                approximateZeroMean: Math.abs(mean) < 1e-8,
                weakLagCorrelation: Math.abs(lagCorrelation) < 0.3,
                approximatelyConstantVariance: varianceRatio < 4,
                moderateSkewness: Math.abs(skewness) < 1
            })
        });
    }

    summary() {
        this.ensureFitted();

        return Object.freeze({
            equation:
                `y = ${this.parameters.intercept.toFixed(4)} + ` +
                `${this.parameters.slope.toFixed(4)}x`,
            observations: this.trainingData.size,
            version: this.version,
            metrics: this.getMetrics(),
            diagnostics: this.diagnose()
        });
    }
}

class RegressionService {
    constructor() {
        this.models = new Map();
    }

    register(name, model) {
        if (typeof name !== "string" || !name.trim()) {
            throw new ValidationError("Model name is required.");
        }

        if (!(model instanceof RegressionModel)) {
            throw new ValidationError("Invalid regression model.");
        }

        if (this.models.has(name)) {
            throw new ValidationError("Model name already exists.");
        }

        this.models.set(name, model);
        return model;
    }

    get(name) {
        const model = this.models.get(name);

        if (!model) {
            throw new RegressionError(`Unknown model: ${name}`);
        }

        return model;
    }

    remove(name) {
        return this.models.delete(name);
    }
}

/*
 * CSV format:
 * study_hours,exam_score
 * 1,42
 * 2,46
 *
 * CSV fields are validated and quoted values are handled.
 */
function parseCSVLine(line) {
    const fields = [];
    let field = "";
    let quoted = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
            if (quoted && line[i + 1] === '"') {
                field += '"';
                i++;
            } else {
                quoted = !quoted;
            }
        } else if (char === "," && !quoted) {
            fields.push(field.trim());
            field = "";
        } else {
            field += char;
        }
    }

    if (quoted) {
        throw new ValidationError("Unclosed CSV quote.");
    }

    fields.push(field.trim());

    return fields;
}

async function loadCSV(path, xColumn, yColumn) {
    const content = await fs.readFile(path, "utf8");
    const lines = content.trim().split(/\r?\n/);

    if (lines.length < 4) {
        throw new ValidationError(
            "CSV must contain a header and at least three records."
        );
    }

    const headers = parseCSVLine(lines[0]);

    const xIndex = headers.indexOf(xColumn);
    const yIndex = headers.indexOf(yColumn);

    if (xIndex < 0 || yIndex < 0) {
        throw new ValidationError("Required CSV columns are missing.");
    }

    const observations = [];

    for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;

        const fields = parseCSVLine(lines[i]);

        const x = Number(fields[xIndex]);
        const y = Number(fields[yIndex]);

        if (!Number.isFinite(x) || !Number.isFinite(y)) {
            throw new ValidationError(
                `Invalid numeric record at line ${i + 1}.`
            );
        }

        observations.push({ x, y });
    }

    return new RegressionDataset(observations);
}

function runTests() {
    const dataset = new RegressionDataset([
        { x: 1, y: 3 },
        { x: 2, y: 5 },
        { x: 3, y: 7 },
        { x: 4, y: 9 },
        { x: 5, y: 11 }
    ]);

    const model = new RegressionModel();

    let eventReceived = false;

    model.on("model:fitted", event => {
        eventReceived = true;
        console.log("Model fitted event:", event);
    });

    model.fit(dataset);

    console.assert(eventReceived);
    console.assert(Math.abs(model.parameters.slope - 2) < 1e-10);
    console.assert(Math.abs(model.parameters.intercept - 1) < 1e-10);
    console.assert(Math.abs(model.getMetrics().rSquared - 1) < 1e-10);
    console.assert(model.predictOne(6) === 13);

    try {
        new RegressionModel().predictOne(5);
        throw new Error("Unfitted model was accepted.");
    } catch (error) {
        if (!(error instanceof ModelNotFittedError)) throw error;
    }

    try {
        new RegressionDataset([
            { x: 1, y: 2 },
            { x: 1, y: 3 },
            { x: 1, y: 4 }
        ]);

        const invalidModel = new RegressionModel();
        invalidModel.fit(
            new RegressionDataset([
                { x: 1, y: 2 },
                { x: 1, y: 3 },
                { x: 1, y: 4 }
            ])
        );

        throw new Error("Constant predictor was accepted.");
    } catch (error) {
        if (!(error instanceof ValidationError)) throw error;
    }

    console.log("All JavaScript tests passed.");
}

async function main() {
    const observations = [
        { x: 1, y: 42 },
        { x: 2, y: 46 },
        { x: 3, y: 53 },
        { x: 4, y: 57 },
        { x: 5, y: 61 },
        { x: 6, y: 68 },
        { x: 7, y: 72 },
        { x: 8, y: 79 }
    ];

    const dataset = new RegressionDataset(observations);
    const model = new RegressionModel();

    const service = new RegressionService();
    service.register("examination-performance", model);

    model.on("model:fitted", event => {
        console.log("\nLifecycle event:", event);
    });

    model.fit(dataset);

    console.log("\nREGRESSION SUMMARY");
    console.log(model.summary());

    console.log("\nPREDICTIONS");

    for (const input of [2.5, 5.5, 9]) {
        console.log(
            `X=${input}, predicted Y=${model.predictOne(input).toFixed(3)}`
        );
    }

    console.log("\nRESIDUAL ANALYSIS");

    for (const row of model.getResiduals()) {
        console.log(row);
    }

    console.log("\nSLOPE CONFIDENCE INTERVAL");
    console.log(model.confidenceIntervalSlope());

    console.log("\nASSUMPTION INDICATORS");
    console.log(model.diagnose());

    runTests();

    // Optional CSV loading:
    // const csvDataset = await loadCSV(
    //     "./regression_data.csv",
    //     "study_hours",
    //     "exam_score"
    // );
    // const csvModel = new RegressionModel().fit(csvDataset);
    // console.log(csvModel.summary());
}

main().catch(error => {
    console.error("Regression execution failed:", error.message);
    process.exitCode = 1;
});
