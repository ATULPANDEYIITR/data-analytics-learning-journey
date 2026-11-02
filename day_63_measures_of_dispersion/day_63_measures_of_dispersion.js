'use strict';

const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const EventEmitter = require('node:events');

class DispersionError extends Error {}

function validateData(values) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new DispersionError('At least one observation is required.');
    }

    return values.map((value, index) => {
        if (
            typeof value !== 'number' ||
            !Number.isFinite(value)
        ) {
            throw new DispersionError(
                `Invalid numeric observation at index ${index}.`
            );
        }
        return value;
    });
}

function mean(values) {
    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function percentile(values, p) {
    const ordered = [...values].sort((a, b) => a - b);

    if (ordered.length === 1) {
        return ordered[0];
    }

    const position = (ordered.length - 1) * p;
    const lower = Math.floor(position);
    const upper = Math.min(lower + 1, ordered.length - 1);
    const fraction = position - lower;

    return ordered[lower] +
        fraction * (ordered[upper] - ordered[lower]);
}

function median(values) {
    const ordered = [...values].sort((a, b) => a - b);
    const middle = Math.floor(ordered.length / 2);

    return ordered.length % 2 === 0
        ? (ordered[middle - 1] + ordered[middle]) / 2
        : ordered[middle];
}

function calculateDispersion(values) {
    const data = validateData(values);
    const avg = mean(data);

    const squaredDeviations = data.map(
        value => (value - avg) ** 2
    );

    const populationVariance =
        squaredDeviations.reduce((a, b) => a + b, 0) / data.length;

    const sampleVariance =
        data.length > 1
            ? squaredDeviations.reduce((a, b) => a + b, 0) /
              (data.length - 1)
            : null;

    const q1 = percentile(data, 0.25);
    const q3 = percentile(data, 0.75);
    const med = median(data);

    const absoluteDeviations = data.map(
        value => Math.abs(value - med)
    );

    const mad = median(absoluteDeviations);

    const populationSD = Math.sqrt(populationVariance);
    const cv = avg === 0
        ? null
        : (populationSD / Math.abs(avg)) * 100;

    return Object.freeze({
        count: data.length,
        minimum: Math.min(...data),
        maximum: Math.max(...data),
        range: Math.max(...data) - Math.min(...data),
        mean: avg,
        populationVariance,
        sampleVariance,
        populationStandardDeviation: populationSD,
        sampleStandardDeviation:
            sampleVariance === null ? null : Math.sqrt(sampleVariance),
        q1,
        q3,
        iqr: q3 - q1,
        mad,
        coefficientOfVariationPercent: cv
    });
}

function evaluateVariability(report) {
    if (report.coefficientOfVariationPercent === null) {
        return 'CV is undefined because the mean is zero.';
    }

    if (report.coefficientOfVariationPercent < 10) {
        return 'Low relative dispersion';
    }

    if (report.coefficientOfVariationPercent < 20) {
        return 'Moderate relative dispersion';
    }

    return 'High relative dispersion';
}

class DispersionMonitor extends EventEmitter {
    constructor() {
        super();
        this.history = [];
    }

    process(values, source = 'unknown') {
        const report = calculateDispersion(values);

        const event = {
            source,
            timestamp: new Date().toISOString(),
            report
        };

        this.history.push(event);
        this.emit('calculated', event);

        if (report.coefficientOfVariationPercent !== null &&
            report.coefficientOfVariationPercent > 20) {
            this.emit('high-variability', event);
        }

        return event;
    }
}

async function saveReport(event) {
    const filePath = path.join(
        os.tmpdir(),
        `dispersion-${Date.now()}.json`
    );

    await fs.writeFile(
        filePath,
        JSON.stringify(event, null, 2),
        { encoding: 'utf8', mode: 0o600 }
    );

    return filePath;
}

function runTests() {
    const report = calculateDispersion(
        [12, 15, 14, 10, 18, 20, 13, 16, 15, 11]
    );

    console.assert(report.count === 10);
    console.assert(report.minimum === 10);
    console.assert(report.maximum === 20);
    console.assert(report.range === 10);
    console.assert(Math.abs(report.mean - 14.4) < 1e-10);
    console.assert(report.populationVariance > 0);
    console.assert(report.iqr > 0);
    console.assert(report.mad > 0);

    const single = calculateDispersion([5]);
    console.assert(single.range === 0);
    console.assert(single.populationVariance === 0);
    console.assert(single.iqr === 0);
    console.assert(single.mad === 0);

    try {
        calculateDispersion([]);
        throw new Error('Empty input should fail.');
    } catch (error) {
        console.assert(error instanceof DispersionError);
    }

    try {
        calculateDispersion([1, Number.NaN]);
        throw new Error('NaN input should fail.');
    } catch (error) {
        console.assert(error instanceof DispersionError);
    }
}

async function main() {
    const monitor = new DispersionMonitor();

    monitor.on('calculated', event => {
        console.log(
            `Calculated dispersion for ${event.source}: ` +
            `range=${event.report.range.toFixed(2)}, ` +
            `IQR=${event.report.iqr.toFixed(2)}`
        );
    });

    monitor.on('high-variability', event => {
        console.log(
            `High variability detected: ` +
            `${event.report.coefficientOfVariationPercent.toFixed(2)}% CV`
        );
    });

    const event = monitor.process(
        [12, 15, 14, 10, 18, 20, 13, 16, 15, 11],
        'production-sample'
    );

    console.log('\nMeasures of Dispersion');
    console.log('======================');
    console.log(event.report);
    console.log(
        `Interpretation: ${evaluateVariability(event.report)}`
    );

    const reportPath = await saveReport(event);
    console.log(`Report written to: ${reportPath}`);

    runTests();
    console.log('Validation tests: passed');
}

main().catch(error => {
    console.error(`Execution failed: ${error.message}`);
    process.exitCode = 1;
});
