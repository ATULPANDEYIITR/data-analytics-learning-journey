"use strict";

/*
 * NumPy is Python-specific, so this JavaScript implementation models the
 * same array concepts without pretending JavaScript has NumPy semantics.
 * The focus is on typed arrays, explicit shape metadata, row-major indexing,
 * vectorized-style operations, validation, and event-driven processing.
 */

class NumericMatrix {
    constructor(rows, columns, values = []) {
        if (!Number.isInteger(rows) || rows <= 0) {
            throw new RangeError("rows must be a positive integer");
        }
        if (!Number.isInteger(columns) || columns <= 0) {
            throw new RangeError("columns must be a positive integer");
        }

        const expected = rows * columns;
        if (values.length !== 0 && values.length !== expected) {
            throw new RangeError(
                `Expected ${expected} values, received ${values.length}`
            );
        }

        this.rows = rows;
        this.columns = columns;
        this.data = new Float64Array(expected);

        if (values.length > 0) {
            this.data.set(values);
        }
    }

    index(row, column) {
        if (
            !Number.isInteger(row) ||
            !Number.isInteger(column) ||
            row < 0 ||
            row >= this.rows ||
            column < 0 ||
            column >= this.columns
        ) {
            throw new RangeError("Matrix index is outside the valid shape");
        }

        // Row-major layout maps a 2-D coordinate into one contiguous buffer.
        return row * this.columns + column;
    }

    get(row, column) {
        return this.data[this.index(row, column)];
    }

    set(row, column, value) {
        if (!Number.isFinite(value)) {
            throw new TypeError("Matrix values must be finite numbers");
        }

        this.data[this.index(row, column)] = value;
    }

    row(row) {
        if (!Number.isInteger(row) || row < 0 || row >= this.rows) {
            throw new RangeError("Invalid row");
        }

        const start = row * this.columns;
        return Array.from(this.data.slice(start, start + this.columns));
    }

    column(column) {
        if (!Number.isInteger(column) || column < 0 || column >= this.columns) {
            throw new RangeError("Invalid column");
        }

        const result = [];
        for (let row = 0; row < this.rows; row++) {
            result.push(this.get(row, column));
        }
        return result;
    }

    map(operation) {
        const result = new NumericMatrix(this.rows, this.columns);
        for (let i = 0; i < this.data.length; i++) {
            result.data[i] = operation(this.data[i], i);
        }
        return result;
    }

    add(other) {
        this.assertSameShape(other);

        const result = new NumericMatrix(this.rows, this.columns);
        for (let i = 0; i < this.data.length; i++) {
            result.data[i] = this.data[i] + other.data[i];
        }
        return result;
    }

    multiplyElementWise(other) {
        this.assertSameShape(other);

        const result = new NumericMatrix(this.rows, this.columns);
        for (let i = 0; i < this.data.length; i++) {
            result.data[i] = this.data[i] * other.data[i];
        }
        return result;
    }

    multiplyScalar(scalar) {
        if (!Number.isFinite(scalar)) {
            throw new TypeError("Scalar must be finite");
        }

        return this.map(value => value * scalar);
    }

    assertSameShape(other) {
        if (
            !(other instanceof NumericMatrix) ||
            this.rows !== other.rows ||
            this.columns !== other.columns
        ) {
            throw new RangeError("Matrix shapes must match");
        }
    }

    toString() {
        const rows = [];
        for (let row = 0; row < this.rows; row++) {
            rows.push(`[${this.row(row).join(", ")}]`);
        }
        return rows.join("\n");
    }
}


class BroadcastVector {
    constructor(values) {
        if (!values.length || !values.every(Number.isFinite)) {
            throw new TypeError("Broadcast vector requires finite numeric values");
        }
        this.values = Float64Array.from(values);
    }

    multiply(matrix) {
        if (this.values.length !== matrix.columns) {
            throw new RangeError(
                "Vector length must match the matrix's final dimension"
            );
        }

        const result = new NumericMatrix(matrix.rows, matrix.columns);

        for (let row = 0; row < matrix.rows; row++) {
            for (let column = 0; column < matrix.columns; column++) {
                result.set(
                    row,
                    column,
                    matrix.get(row, column) * this.values[column]
                );
            }
        }

        return result;
    }
}


function demonstrateTypedArrays() {
    console.log("=== Typed arrays and NumPy-like numeric storage ===");

    const values = new Float64Array([10, 20, 30, 40]);
    const integers = new Int32Array([2, 4, 6, 8]);

    console.log("Float64Array:", values);
    console.log("Int32Array:", integers);
    console.log("Float64 bytes:", values.byteLength);
    console.log("Integer bytes:", integers.byteLength);

    // Typed arrays enforce a numeric storage representation, unlike ordinary
    // JavaScript arrays that can contain arbitrary JavaScript values.
    const transformed = Float64Array.from(values, value => value * 1.5);
    console.log("Transformed values:", transformed);
}


function demonstrateMatrixOperations() {
    console.log("\n=== Shape, indexing, slicing, and element-wise operations ===");

    const matrix = new NumericMatrix(3, 4, [
        82, 91, 77, 88,
        95, 84, 90, 73,
        68, 79, 85, 92
    ]);

    console.log("Matrix:\n" + matrix);
    console.log("Shape:", [matrix.rows, matrix.columns]);
    console.log("First element:", matrix.get(0, 0));
    console.log("Last element:", matrix.get(2, 3));
    console.log("Second row:", matrix.row(1));
    console.log("Third column:", matrix.column(2));

    const normalized = matrix.map(value => value / 100);
    console.log("Normalized:\n" + normalized);

    const doubled = matrix.multiplyScalar(2);
    console.log("Doubled:\n" + doubled);
}


function demonstrateBooleanFiltering() {
    console.log("\n=== Boolean-style filtering ===");

    const scores = Float64Array.from([61, 74, 88, 92, 55, 79, 96, 83, 67]);

    const passing = Array.from(scores).filter(score => score >= 70);
    const distinction = Array.from(scores).filter(score => score >= 90);

    console.log("Passing:", passing);
    console.log("Distinction:", distinction);

    const mean =
        Array.from(scores).reduce((sum, value) => sum + value, 0) /
        scores.length;

    console.log("Mean:", mean);
}


function demonstrateBroadcasting() {
    console.log("\n=== Explicit broadcasting model ===");

    const sales = new NumericMatrix(3, 3, [
        120, 150, 180,
        90, 110, 140,
        200, 220, 250
    ]);

    const targets = new BroadcastVector([100, 120, 160]);
    const ratios = targets.multiply(
        sales.map((value, index) => {
            const column = index % sales.columns;
            return value / targets.values[column];
        })
    );

    console.log("Sales:\n" + sales);
    console.log("Column-scaled values:\n" + ratios);

    try {
        new BroadcastVector([1, 2]).multiply(sales);
    } catch (error) {
        console.log("Broadcasting validation:", error.message);
    }
}


function matrixMultiply(left, right) {
    if (left.columns !== right.rows) {
        throw new RangeError(
            `Cannot multiply ${left.rows}x${left.columns} by ` +
            `${right.rows}x${right.columns}`
        );
    }

    const result = new NumericMatrix(left.rows, right.columns);

    // This is the direct matrix multiplication algorithm. Unlike a numerical
    // library, this implementation makes the accumulation behavior explicit.
    for (let i = 0; i < left.rows; i++) {
        for (let j = 0; j < right.columns; j++) {
            let total = 0;
            for (let k = 0; k < left.columns; k++) {
                total += left.get(i, k) * right.get(k, j);
            }
            result.set(i, j, total);
        }
    }

    return result;
}


function demonstrateLinearAlgebra() {
    console.log("\n=== Matrix multiplication ===");

    const features = new NumericMatrix(3, 2, [
        20, 4,
        30, 6,
        40, 8
    ]);

    const coefficients = new NumericMatrix(2, 1, [
        2.5,
        5
    ]);

    const predictions = matrixMultiply(features, coefficients);

    console.log("Features:\n" + features);
    console.log("Coefficients:\n" + coefficients);
    console.log("Predictions:\n" + predictions);
}


function demonstrateEventDrivenProcessing() {
    console.log("\n=== Event-driven numeric processing ===");

    const events = [
        { type: "measurement", values: [18.5, 21.0, 24.5] },
        { type: "measurement", values: [19.0, 25.5, 29.0] },
        { type: "invalid", values: [10, Number.NaN, 20] }
    ];

    const emitter = new EventTarget();

    emitter.addEventListener("measurement", event => {
        const values = event.detail.values;

        if (!values.every(Number.isFinite)) {
            console.error("Rejected non-finite measurement:", values);
            return;
        }

        const normalized = values.map(value => value / 100);
        console.log("Processed measurement:", normalized);
    });

    for (const event of events) {
        emitter.dispatchEvent(
            new CustomEvent(event.type, { detail: event })
        );
    }
}


function demonstrateAsyncPipeline() {
    console.log("\n=== Asynchronous data pipeline ===");

    return new Promise(resolve => {
        setTimeout(() => {
            const raw = Float64Array.from([12, 15, 18, 21]);
            const normalized = Float64Array.from(
                raw,
                value => (value - 12) / 9
            );

            console.log("Raw:", raw);
            console.log("Normalized:", normalized);
            resolve();
        }, 10);
    });
}


async function main() {
    demonstrateTypedArrays();
    demonstrateMatrixOperations();
    demonstrateBooleanFiltering();
    demonstrateBroadcasting();
    demonstrateLinearAlgebra();
    demonstrateEventDrivenProcessing();
    await demonstrateAsyncPipeline();

    console.log("\n=== JavaScript implementation completed ===");
}


main().catch(error => {
    console.error("Unexpected failure:", error);
    process.exitCode = 1;
});
