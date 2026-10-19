"use strict";

/*
 * NumPy-style advanced numerical operations implemented with standard
 * JavaScript arrays and typed arrays. The implementation emphasizes
 * JavaScript-specific concerns such as explicit shape metadata,
 * event-driven execution, asynchronous batch processing, and
 * Float64Array storage.
 */

class NDArray {
    constructor(data, shape) {
        if (!Array.isArray(shape) || shape.length === 0) {
            throw new Error("Shape must contain at least one dimension.");
        }

        const expectedSize = shape.reduce((product, dimension) => {
            if (!Number.isInteger(dimension) || dimension <= 0) {
                throw new Error("Dimensions must be positive integers.");
            }
            return product * dimension;
        }, 1);

        if (data.length !== expectedSize) {
            throw new Error(
                `Data length ${data.length} does not match shape ${shape.join("x")}.`
            );
        }

        this.data = Float64Array.from(data);
        this.shape = [...shape];
    }

    static zeros(shape) {
        const size = shape.reduce((a, b) => a * b, 1);
        return new NDArray(new Float64Array(size), shape);
    }

    static fromNested(rows) {
        if (!Array.isArray(rows) || rows.length === 0) {
            throw new Error("Expected a non-empty matrix.");
        }

        if (!Array.isArray(rows[0])) {
            return new NDArray(rows, [rows.length]);
        }

        const columns = rows[0].length;
        if (columns === 0 || rows.some(row => row.length !== columns)) {
            throw new Error("All matrix rows must have the same length.");
        }

        return new NDArray(
            rows.flat(),
            [rows.length, columns]
        );
    }

    offset(indices) {
        if (indices.length !== this.shape.length) {
            throw new Error("Index dimensionality does not match array shape.");
        }

        let offset = 0;
        let stride = 1;

        for (let i = this.shape.length - 1; i >= 0; i--) {
            const index = indices[i];

            if (index < 0 || index >= this.shape[i]) {
                throw new RangeError("Index outside array bounds.");
            }

            offset += index * stride;
            stride *= this.shape[i];
        }

        return offset;
    }

    get(...indices) {
        return this.data[this.offset(indices)];
    }

    set(value, ...indices) {
        this.data[this.offset(indices)] = value;
    }

    reshape(newShape) {
        const size = newShape.reduce((a, b) => a * b, 1);

        if (size !== this.data.length) {
            throw new Error("Reshape cannot change the number of elements.");
        }

        return new NDArray(this.data, newShape);
    }

    sum(axis = null) {
        if (axis === null) {
            return this.data.reduce((sum, value) => sum + value, 0);
        }

        if (this.shape.length !== 2) {
            throw new Error("This demonstration supports axis aggregation for 2-D arrays.");
        }

        const [rows, columns] = this.shape;

        if (axis === 0) {
            const result = new Float64Array(columns);

            for (let row = 0; row < rows; row++) {
                for (let column = 0; column < columns; column++) {
                    result[column] += this.get(row, column);
                }
            }

            return new NDArray(result, [columns]);
        }

        if (axis === 1) {
            const result = new Float64Array(rows);

            for (let row = 0; row < rows; row++) {
                for (let column = 0; column < columns; column++) {
                    result[row] += this.get(row, column);
                }
            }

            return new NDArray(result, [rows]);
        }

        throw new Error("Axis must be 0 or 1.");
    }

    mean(axis = null) {
        if (axis === null) {
            return this.sum() / this.data.length;
        }

        const result = this.sum(axis);
        const divisor = axis === 0 ? this.shape[0] : this.shape[1];

        return new NDArray(
            Array.from(result.data, value => value / divisor),
            result.shape
        );
    }

    transpose() {
        if (this.shape.length !== 2) {
            throw new Error("Transpose demonstration expects a matrix.");
        }

        const [rows, columns] = this.shape;
        const result = new Float64Array(this.data.length);

        for (let row = 0; row < rows; row++) {
            for (let column = 0; column < columns; column++) {
                result[column * rows + row] = this.get(row, column);
            }
        }

        return new NDArray(result, [columns, rows]);
    }

    map(callback) {
        return new NDArray(
            Array.from(this.data, callback),
            this.shape
        );
    }

    toNested() {
        if (this.shape.length !== 2) {
            return Array.from(this.data);
        }

        const [rows, columns] = this.shape;
        const result = [];

        for (let row = 0; row < rows; row++) {
            result.push(
                Array.from(
                    this.data.slice(row * columns, (row + 1) * columns)
                )
            );
        }

        return result;
    }
}

function broadcastShape(leftShape, rightShape) {
    const length = Math.max(leftShape.length, rightShape.length);
    const result = [];

    for (let i = 0; i < length; i++) {
        const left = leftShape[leftShape.length - 1 - i] ?? 1;
        const right = rightShape[rightShape.length - 1 - i] ?? 1;

        if (left !== right && left !== 1 && right !== 1) {
            throw new Error(
                `Cannot broadcast ${leftShape.join("x")} with ${rightShape.join("x")}.`
            );
        }

        result.unshift(Math.max(left, right));
    }

    return result;
}

function broadcastAdd(matrix, vector) {
    if (matrix.shape.length !== 2 || vector.shape.length !== 1) {
        throw new Error("This example expects a matrix and a one-dimensional vector.");
    }

    const [rows, columns] = matrix.shape;

    if (vector.shape[0] !== columns) {
        throw new Error("Vector length must equal matrix column count.");
    }

    const output = new Float64Array(matrix.data.length);

    for (let row = 0; row < rows; row++) {
        for (let column = 0; column < columns; column++) {
            output[row * columns + column] =
                matrix.get(row, column) + vector.get(column);
        }
    }

    return new NDArray(output, matrix.shape);
}

function matrixMultiply(left, right) {
    if (left.shape.length !== 2 || right.shape.length !== 2) {
        throw new Error("Matrix multiplication requires two matrices.");
    }

    const [rows, shared] = left.shape;
    const [rightShared, columns] = right.shape;

    if (shared !== rightShared) {
        throw new Error("Inner matrix dimensions must agree.");
    }

    const output = new Float64Array(rows * columns);

    for (let row = 0; row < rows; row++) {
        for (let column = 0; column < columns; column++) {
            let value = 0;

            for (let k = 0; k < shared; k++) {
                value += left.get(row, k) * right.get(k, column);
            }

            output[row * columns + column] = value;
        }
    }

    return new NDArray(output, [rows, columns]);
}

function seededRandom(seed) {
    let state = seed >>> 0;

    return function () {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 4294967296;
    };
}

function normalRandom(random) {
    let u1 = random();
    let u2 = random();

    // Box-Muller requires a strictly positive first uniform sample.
    if (u1 === 0) {
        u1 = Number.MIN_VALUE;
    }

    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function generateNormalMatrix(rows, columns, mean, standardDeviation, seed) {
    const random = seededRandom(seed);
    const data = new Float64Array(rows * columns);

    for (let i = 0; i < data.length; i++) {
        data[i] = mean + standardDeviation * normalRandom(random);
    }

    return new NDArray(data, [rows, columns]);
}

function covarianceMatrix(matrix) {
    const [rows, columns] = matrix.shape;

    if (rows < 2) {
        throw new Error("At least two observations are required.");
    }

    const means = matrix.mean(0);
    const covariance = new Float64Array(columns * columns);

    for (let i = 0; i < columns; i++) {
        for (let j = 0; j < columns; j++) {
            let sum = 0;

            for (let row = 0; row < rows; row++) {
                sum +=
                    (matrix.get(row, i) - means.get(i)) *
                    (matrix.get(row, j) - means.get(j));
            }

            covariance[i * columns + j] = sum / (rows - 1);
        }
    }

    return new NDArray(covariance, [columns, columns]);
}

function calculatePortfolioReturns(assetReturns, weights) {
    if (assetReturns.shape.length !== 2 || weights.shape.length !== 1) {
        throw new Error("Portfolio input must be a return matrix and weight vector.");
    }

    const assets = assetReturns.shape[1];

    if (weights.shape[0] !== assets) {
        throw new Error("Weight count must equal asset count.");
    }

    const totalWeight = weights.sum();

    if (Math.abs(totalWeight - 1) > 1e-10) {
        throw new Error("Portfolio weights must sum to one.");
    }

    return matrixMultiply(
        assetReturns,
        new NDArray(Array.from(weights.data, value => [value]), [assets, 1])
    );
}

class NumericalWorkflow {
    constructor() {
        this.handlers = new Map();
    }

    on(eventName, handler) {
        if (!this.handlers.has(eventName)) {
            this.handlers.set(eventName, []);
        }

        this.handlers.get(eventName).push(handler);
    }

    emit(eventName, payload) {
        for (const handler of this.handlers.get(eventName) ?? []) {
            handler(payload);
        }
    }

    async run() {
        this.emit("started", { timestamp: Date.now() });

        await new Promise(resolve => setTimeout(resolve, 0));

        const observations = generateNormalMatrix(
            500,
            3,
            100,
            15,
            2026
        );

        const mean = observations.mean(0);
        const covariance = covarianceMatrix(observations);

        this.emit("statistics-ready", {
            mean,
            covariance
        });

        await new Promise(resolve => setTimeout(resolve, 0));

        this.emit("completed", {
            observations: observations.shape,
            mean,
            covariance
        });
    }
}

function display(title, value) {
    console.log(`\n${title}`);

    if (value instanceof NDArray) {
        console.log(`shape=${value.shape.join("x")}`);
        console.table(value.toNested());
    } else {
        console.log(value);
    }
}

async function main() {
    console.log("Advanced Numerical Computing in JavaScript");

    const prices = NDArray.fromNested([
        [100, 120, 80],
        [110, 115, 90],
        [95, 130, 85]
    ]);

    const adjustment = new NDArray([1.05, 1.10, 0.95], [3]);
    const adjustedPrices = broadcastAdd(prices, adjustment);

    display("Original price matrix", prices);
    display("Broadcast adjustment", adjustment);
    display("Broadcast result", adjustedPrices);

    display("Column aggregation", prices.sum(0));
    display("Row aggregation", prices.sum(1));
    display("Mean by column", prices.mean(0));
    display("Reshaped matrix", prices.reshape([1, 9]));
    display("Transpose", prices.transpose());

    const a = NDArray.fromNested([
        [2, 1],
        [4, 3]
    ]);

    const b = NDArray.fromNested([
        [5, 2],
        [1, 6]
    ]);

    display("Matrix product A × B", matrixMultiply(a, b));

    const randomObservations = generateNormalMatrix(
        6,
        3,
        50,
        8,
        42
    );

    display("Seeded normally distributed observations", randomObservations);
    display("Observation covariance matrix", covarianceMatrix(randomObservations));

    const portfolioReturns = NDArray.fromNested([
        [0.01, 0.02, -0.01],
        [0.03, -0.01, 0.02],
        [-0.02, 0.01, 0.03]
    ]);

    const weights = new NDArray([0.5, 0.3, 0.2], [3]);
    const portfolio = calculatePortfolioReturns(portfolioReturns, weights);

    display("Portfolio daily returns", portfolio);

    const workflow = new NumericalWorkflow();

    workflow.on("started", event => {
        console.log("\nWorkflow started:", new Date(event.timestamp).toISOString());
    });

    workflow.on("statistics-ready", event => {
        display("Asynchronous workflow means", event.mean);
        display("Asynchronous workflow covariance", event.covariance);
    });

    workflow.on("completed", event => {
        console.log("Workflow completed for observations:", event.observations.join("x"));
    });

    await workflow.run();

    try {
        broadcastShape([3, 4], [5]);
    } catch (error) {
        console.log("\nBroadcasting validation:", error.message);
    }

    try {
        matrixMultiply(a, prices);
    } catch (error) {
        console.log("Matrix dimension validation:", error.message);
    }

    console.log("\nCompleted.");
}

main().catch(error => {
    console.error("Numerical workflow failed:", error);
    process.exitCode = 1;
});
