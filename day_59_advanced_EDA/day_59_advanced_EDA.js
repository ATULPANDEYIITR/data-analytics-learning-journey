'use strict';

const { EventEmitter } = require('node:events');

class EDAError extends Error {
    constructor(message) {
        super(message);
        this.name = 'EDAError';
    }
}

function validate(values, name) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new EDAError(`${name} must contain at least one value`);
    }
    if (!values.every(Number.isFinite)) {
        throw new EDAError(`${name} contains a non-finite value`);
    }
}

function mean(values) {
    validate(values, 'values');
    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values) {
    validate(values, 'values');
    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2
        ? sorted[middle]
        : (sorted[middle - 1] + sorted[middle]) / 2;
}

function quantile(values, q) {
    validate(values, 'values');
    if (q < 0 || q > 1) {
        throw new EDAError('quantile must be between 0 and 1');
    }

    const sorted = [...values].sort((a, b) => a - b);
    const position = (sorted.length - 1) * q;
    const lower = Math.floor(position);
    const upper = Math.min(lower + 1, sorted.length - 1);
    const weight = position - lower;

    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

function variance(values, sample = true) {
    validate(values, 'values');
    if (sample && values.length < 2) {
        throw new EDAError('sample variance requires at least two values');
    }

    const m = mean(values);
    const divisor = sample ? values.length - 1 : values.length;
    return values.reduce((sum, value) => sum + (value - m) ** 2, 0) / divisor;
}

function covariance(x, y) {
    validate(x, 'x');
    validate(y, 'y');
    if (x.length !== y.length || x.length < 2) {
        throw new EDAError('covariance requires equal samples');
    }

    const mx = mean(x);
    const my = mean(y);
    return x.reduce(
        (sum, value, index) => sum + (value - mx) * (y[index] - my),
        0
    ) / (x.length - 1);
}

function pearson(x, y) {
    const cov = covariance(x, y);
    const sx = Math.sqrt(variance(x));
    const sy = Math.sqrt(variance(y));
    return sx === 0 || sy === 0 ? 0 : cov / (sx * sy);
}

function skewness(values) {
    validate(values, 'values');
    if (values.length < 3) return 0;

    const n = values.length;
    const m = mean(values);
    const s = Math.sqrt(variance(values));
    if (s === 0) return 0;

    const sum = values.reduce(
        (total, value) => total + ((value - m) / s) ** 3,
        0
    );
    return (n / ((n - 1) * (n - 2))) * sum;
}

function outlierProfile(values) {
    const q1 = quantile(values, 0.25);
    const q3 = quantile(values, 0.75);
    const iqr = q3 - q1;
    const lower = q1 - 1.5 * iqr;
    const upper = q3 + 1.5 * iqr;

    return {
        q1,
        q3,
        iqr,
        lowerFence: lower,
        upperFence: upper,
        outliers: values.filter(v => v < lower || v > upper)
    };
}

function ranks(values) {
    return values.map((value, index) => ({ value, index }))
        .sort((a, b) => a.value - b.value)
        .reduce((result, item, position, sorted) => {
            let end = position;
            while (end + 1 < sorted.length &&
                   sorted[end + 1].value === item.value) {
                end++;
            }
            const rank = (position + end + 2) / 2;
            for (let i = position; i <= end; i++) {
                result[sorted[i].index] = rank;
            }
            return result;
        }, new Array(values.length));
}

function spearman(x, y) {
    if (x.length !== y.length) {
        throw new EDAError('Spearman correlation requires equal lengths');
    }
    return pearson(ranks(x), ranks(y));
}

function transform(values, operation) {
    validate(values, 'values');

    switch (operation) {
        case 'log1p':
            if (values.some(v => v <= -1)) {
                throw new EDAError('log1p requires values greater than -1');
            }
            return values.map(Math.log1p);

        case 'sqrt':
            if (values.some(v => v < 0)) {
                throw new EDAError('sqrt requires non-negative values');
            }
            return values.map(Math.sqrt);

        case 'zscore': {
            const m = mean(values);
            const s = Math.sqrt(variance(values, false));
            return values.map(v => s === 0 ? 0 : (v - m) / s);
        }

        case 'robust': {
            const med = median(values);
            const scale = quantile(values, 0.75) - quantile(values, 0.25);
            return values.map(v => scale === 0 ? 0 : (v - med) / scale);
        }

        case 'none':
            return [...values];

        default:
            throw new EDAError(`Unsupported transformation: ${operation}`);
    }
}

class EDAEngine extends EventEmitter {
    constructor(dataset) {
        super();
        this.dataset = dataset;
        this.results = new Map();
    }

    analyzeFeature(name, values) {
        validate(values, name);
        const profile = {
            count: values.length,
            mean: mean(values),
            median: median(values),
            variance: variance(values, false),
            standardDeviation: Math.sqrt(variance(values, false)),
            skewness: skewness(values),
            outliers: outlierProfile(values)
        };

        this.results.set(name, profile);
        this.emit('featureAnalyzed', { name, profile });
        return profile;
    }

    correlationMatrix() {
        const names = Object.keys(this.dataset);
        const matrix = new Map();

        for (const left of names) {
            const row = new Map();
            for (const right of names) {
                row.set(right, pearson(this.dataset[left], this.dataset[right]));
            }
            matrix.set(left, row);
        }

        this.emit('matrixReady', matrix);
        return matrix;
    }

    async runAsync() {
        await new Promise(resolve => setImmediate(resolve));

        for (const [name, values] of Object.entries(this.dataset)) {
            this.analyzeFeature(name, values);
        }

        return {
            features: this.results,
            correlations: this.correlationMatrix()
        };
    }
}

function buildDataset() {
    const rows = [
        [42000, 1100, 3, 8, 2],
        [48000, 1350, 4, 14, 1],
        [51000, 1500, 5, 18, 1],
        [56000, 1720, 6, 25, 0],
        [62000, 1900, 7, 30, 0],
        [68000, 2150, 8, 36, 1],
        [72000, 2450, 9, 42, 0],
        [79000, 2600, 10, 48, 0],
        [85000, 3000, 11, 52, 1],
        [91000, 3200, 12, 60, 0],
        [47000, 1250, 4, 12, 3],
        [53000, 1550, 5, 21, 2],
        [60000, 1820, 7, 28, 1],
        [74000, 2300, 9, 45, 0],
        [1500000, 3500, 3, 10, 5],
        [45000, 1050, 2, 5, 7]
    ];

    const names = ['income', 'spending', 'visits', 'tenure', 'complaints'];
    return Object.fromEntries(
        names.map((name, index) => [name, rows.map(row => row[index])])
    );
}

function printMatrix(matrix) {
    const names = [...matrix.keys()];
    console.log('\nCORRELATION MATRIX');
    console.log(['feature', ...names].join('\t'));

    for (const name of names) {
        console.log(
            [name, ...names.map(other => matrix.get(name).get(other).toFixed(3))]
                .join('\t')
        );
    }
}

async function main() {
    const dataset = buildDataset();
    const engine = new EDAEngine(dataset);

    engine.on('featureAnalyzed', ({ name, profile }) => {
        console.log(
            `${name}: mean=${profile.mean.toFixed(2)}, ` +
            `median=${profile.median.toFixed(2)}, ` +
            `skew=${profile.skewness.toFixed(3)}, ` +
            `outliers=${profile.outliers.outliers.length}`
        );
    });

    const result = await engine.runAsync();
    printMatrix(result.correlations);

    console.log('\nHIGH-CORRELATION PAIRS');
    const names = Object.keys(dataset);

    for (let i = 0; i < names.length; i++) {
        for (let j = i + 1; j < names.length; j++) {
            const r = pearson(dataset[names[i]], dataset[names[j]]);
            if (Math.abs(r) >= 0.7) {
                console.log(`${names[i]} <-> ${names[j]}: ${r.toFixed(3)}`);
            }
        }
    }

    console.log('\nTRANSFORMATION CHECK');
    const incomeLog = transform(dataset.income, 'log1p');
    console.log(
        `income skewness: ${skewness(dataset.income).toFixed(3)} -> ` +
        `${skewness(incomeLog).toFixed(3)} after log1p`
    );

    console.log('\nRANK CORRELATION');
    console.log(
        `income vs spending Spearman: ` +
        `${spearman(dataset.income, dataset.spending).toFixed(3)}`
    );

    console.log('\nSECURITY AND QUALITY CONTROLS');
    console.log('- Reject non-finite numeric input before statistical operations.');
    console.log('- Keep raw observations immutable when applying transformations.');
    console.log('- Treat outliers as observations requiring investigation, not automatic deletion.');
    console.log('- Do not infer causality from correlation.');
    console.log('- Fit transformation parameters only on training data in predictive workflows.');

    try {
        transform([-1.2, 2], 'log1p');
    } catch (error) {
        console.log(`Rejected invalid transformation: ${error.message}`);
    }
}

main().catch(error => {
    console.error(`EDA pipeline failed: ${error.message}`);
    process.exitCode = 1;
});
