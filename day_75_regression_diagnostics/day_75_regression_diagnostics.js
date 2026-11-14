'use strict';

/*
 * Regression Diagnostics Engine
 *
 * Implements:
 * - OLS regression
 * - VIF and predictor correlations
 * - Breusch-Pagan test
 * - Residual normality diagnostics
 * - Leverage and Cook's distance
 * - HC3 robust standard errors
 * - Event-driven diagnostic reporting
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const fs = require('node:fs/promises');

class RegressionError extends Error {
    constructor(message) {
        super(message);
        this.name = 'RegressionError';
    }
}

const Status = Object.freeze({
    PASS: 'PASS',
    WARNING: 'WARNING',
    FAIL: 'FAIL'
});

class DiagnosticEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(event, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function.');
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(listener);

        return () => {
            this.listeners.get(event)?.delete(listener);
        };
    }

    emit(event, payload) {
        const subscribers = this.listeners.get(event);

        if (!subscribers) return;

        for (const listener of subscribers) {
            try {
                listener(Object.freeze({ ...payload }));
            } catch (error) {
                process.stderr.write(
                    `Event listener failed: ${error.message}\n`
                );
            }
        }
    }
}

function mean(values) {
    return values.reduce((sum, value) => sum + value, 0)
        / values.length;
}

function variance(values) {
    const center = mean(values);

    return values.reduce(
        (sum, value) => sum + (value - center) ** 2,
        0
    ) / values.length;
}

function dot(a, b) {
    return a.reduce(
        (sum, value, index) => sum + value * b[index],
        0
    );
}

function transpose(matrix) {
    return matrix[0].map(
        (_, column) => matrix.map(row => row[column])
    );
}

function multiply(a, b) {
    const bt = transpose(b);

    return a.map(
        row => bt.map(column => dot(row, column))
    );
}

function solve(matrix, vector) {
    const n = vector.length;

    if (matrix.length !== n ||
        matrix.some(row => row.length !== n)) {
        throw new RegressionError('Invalid matrix dimensions.');
    }

    const a = matrix.map(
        (row, index) => [...row, vector[index]]
    );

    for (let col = 0; col < n; col++) {
        let pivot = col;

        for (let row = col + 1; row < n; row++) {
            if (Math.abs(a[row][col]) >
                Math.abs(a[pivot][col])) {
                pivot = row;
            }
        }

        if (Math.abs(a[pivot][col]) < 1e-12) {
            throw new RegressionError(
                'Singular design matrix.'
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

function inverse(matrix) {
    const n = matrix.length;

    const columns = Array.from(
        { length: n },
        (_, i) => {
            const unit = Array(n).fill(0);
            unit[i] = 1;
            return solve(matrix, unit);
        }
    );

    return transpose(columns);
}

function chiSquareSurvival(statistic, degrees) {
    if (statistic < 0 || degrees <= 0) {
        throw new RangeError('Invalid chi-square parameters.');
    }

    const a = degrees / 2;
    const x = statistic / 2;

    if (x === 0) return 1;

    const logGamma = z => {
        const coefficients = [
            676.5203681218851,
            -1259.1392167224028,
            771.3234287776531,
            -176.6150291621406,
            12.507343278686905,
            -0.13857109526572012,
            9.9843695780195716e-6,
            1.5056327351493116e-7
        ];

        if (z < 0.5) {
            return Math.log(Math.PI)
                - Math.log(Math.sin(Math.PI * z))
                - logGamma(1 - z);
        }

        z -= 1;

        let sum = 0.99999999999980993;

        coefficients.forEach((c, i) => {
            sum += c / (z + i + 1);
        });

        const t = z + coefficients.length - 0.5;

        return 0.5 * Math.log(2 * Math.PI)
            + (z + 0.5) * Math.log(t)
            - t + Math.log(sum);
    };

    const factor = Math.exp(
        -x + a * Math.log(x) - logGamma(a)
    );

    if (x < a + 1) {
        let term = 1 / a;
        let sum = term;
        let ap = a;

        for (let i = 0; i < 1000; i++) {
            ap++;
            term *= x / ap;
            sum += term;

            if (Math.abs(term) < Math.abs(sum) * 1e-14) {
                break;
            }
        }

        return Math.max(0, Math.min(1, 1 - sum * factor));
    }

    let b = x + 1 - a;
    let c = 1e300;
    let d = 1 / b;
    let h = d;

    for (let i = 1; i < 1000; i++) {
        const an = -i * (i - a);
        b += 2;

        d = an * d + b;
        if (Math.abs(d) < 1e-300) d = 1e-300;

        c = b + an / c;
        if (Math.abs(c) < 1e-300) c = 1e-300;

        d = 1 / d;
        const delta = d * c;
        h *= delta;

        if (Math.abs(delta - 1) < 1e-14) break;
    }

    return Math.max(0, Math.min(1, factor * h));
}

function validateDataset(rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
        throw new RegressionError('Dataset must not be empty.');
    }

    const identifiers = new Set();
    const featureCount = rows[0].features.length;

    if (featureCount === 0) {
        throw new RegressionError('At least one predictor is required.');
    }

    for (const row of rows) {
        if (!row.id || identifiers.has(row.id)) {
            throw new RegressionError(
                'Missing or duplicate observation identifier.'
            );
        }

        identifiers.add(row.id);

        if (!Array.isArray(row.features) ||
            row.features.length !== featureCount) {
            throw new RegressionError(
                'Inconsistent predictor dimensions.'
            );
        }

        if (![...row.features, row.target].every(
            Number.isFinite
        )) {
            throw new RegressionError(
                `Invalid numeric value in ${row.id}.`
            );
        }
    }

    if (rows.length <= featureCount + 1) {
        throw new RegressionError(
            'Insufficient observations for regression.'
        );
    }

    return featureCount;
}

class RegressionModel {
    constructor(rows) {
        this.rows = rows;
        this.featureCount = validateDataset(rows);
        this.n = rows.length;
        this.p = this.featureCount + 1;

        this.X = rows.map(row => [
            1,
            ...row.features
        ]);

        this.y = rows.map(row => row.target);

        this.state = 'INITIALIZED';
        this.events = new DiagnosticEventBus();
    }

    fit() {
        if (this.state === 'FITTED') {
            throw new RegressionError(
                'Model has already been fitted.'
            );
        }

        const xt = transpose(this.X);
        const xtx = multiply(xt, this.X);

        this.xtxInverse = inverse(xtx);

        const xty = xt.map(column => dot(column, this.y));

        this.beta = this.xtxInverse.map(
            row => dot(row, xty)
        );

        this.fitted = this.X.map(
            row => dot(row, this.beta)
        );

        this.residuals = this.y.map(
            (value, i) => value - this.fitted[i]
        );

        this.sse = dot(
            this.residuals,
            this.residuals
        );

        this.df = this.n - this.p;

        if (this.df <= 0) {
            throw new RegressionError(
                'Residual degrees of freedom must be positive.'
            );
        }

        this.mse = this.sse / this.df;

        const center = mean(this.y);

        this.sst = this.y.reduce(
            (sum, value) => sum + (value - center) ** 2,
            0
        );

        if (this.sst <= 1e-15) {
            throw new RegressionError(
                'Target variance is zero.'
            );
        }

        this.rSquared = 1 - this.sse / this.sst;

        this.state = 'FITTED';

        this.events.emit('model:fitted', {
            observations: this.n,
            rSquared: this.rSquared
        });

        return this;
    }

    getLeverage() {
        this.assertFitted();

        const hat = multiply(
            multiply(this.X, this.xtxInverse),
            transpose(this.X)
        );

        return hat.map((row, i) => row[i]);
    }

    getStudentizedResiduals() {
        this.assertFitted();

        if (this.mse <= 0) {
            throw new RegressionError(
                'Residual variance is zero.'
            );
        }

        const leverage = this.getLeverage();

        return this.residuals.map(
            (residual, i) => residual / Math.sqrt(
                this.mse * Math.max(1e-15, 1 - leverage[i])
            )
        );
    }

    getCooksDistance() {
        const leverage = this.getLeverage();
        const residuals = this.getStudentizedResiduals();

        return residuals.map((r, i) =>
            r * r * leverage[i] /
            (this.p * Math.max(1e-15, 1 - leverage[i]))
        );
    }

    getVIF() {
        this.assertFitted();

        const columns = transpose(this.X).slice(1);

        return columns.map((target, i) => {
            const others = columns.filter(
                (_, j) => i !== j
            );

            if (others.length === 0) return 1;

            const auxX = Array.from(
                { length: this.n },
                (_, row) => [
                    1,
                    ...others.map(column => column[row])
                ]
            );

            const auxT = transpose(auxX);
            const auxInverse = inverse(
                multiply(auxT, auxX)
            );

            const auxY = auxT.map(
                column => dot(column, target)
            );

            const beta = auxInverse.map(
                row => dot(row, auxY)
            );

            const predictions = auxX.map(
                row => dot(row, beta)
            );

            const sse = target.reduce(
                (sum, value, j) =>
                    sum + (value - predictions[j]) ** 2,
                0
            );

            const center = mean(target);

            const sst = target.reduce(
                (sum, value) =>
                    sum + (value - center) ** 2,
                0
            );

            if (sst <= 1e-15) {
                throw new RegressionError(
                    'Constant predictor cannot have a VIF.'
                );
            }

            const rSquared = 1 - sse / sst;

            return 1 / Math.max(1e-15, 1 - rSquared);
        });
    }

    breuschPagan() {
        this.assertFitted();

        const squared = this.residuals.map(
            value => value ** 2
        );

        const xt = transpose(this.X);
        const inv = inverse(multiply(xt, this.X));

        const xty = xt.map(
            column => dot(column, squared)
        );

        const beta = inv.map(
            row => dot(row, xty)
        );

        const predicted = this.X.map(
            row => dot(row, beta)
        );

        const center = mean(squared);

        const sst = squared.reduce(
            (sum, value) => sum + (value - center) ** 2,
            0
        );

        if (sst <= 1e-15) {
            return { statistic: 0, pValue: 1 };
        }

        const sse = squared.reduce(
            (sum, value, i) =>
                sum + (value - predicted[i]) ** 2,
            0
        );

        const rSquared = Math.max(
            0, Math.min(1, 1 - sse / sst)
        );

        const statistic = this.n * rSquared;

        return {
            statistic,
            pValue: chiSquareSurvival(
                statistic,
                this.featureCount
            )
        };
    }

    jarqueBera() {
        const residuals = this.residuals;
        const center = mean(residuals);
        const v = variance(residuals);

        if (v <= 1e-15) {
            return { statistic: 0, pValue: 1 };
        }

        const skewness = mean(
            residuals.map(x => (x - center) ** 3)
        ) / Math.pow(v, 1.5);

        const kurtosis = mean(
            residuals.map(x => (x - center) ** 4)
        ) / (v * v);

        const statistic = this.n / 6 * (
            skewness ** 2 +
            (kurtosis - 3) ** 2 / 4
        );

        return {
            statistic,
            pValue: chiSquareSurvival(statistic, 2)
        };
    }

    getHC3StandardErrors() {
        const leverage = this.getLeverage();

        const weighted = this.X.map((row, i) => {
            const adjusted = this.residuals[i] /
                Math.max(1e-12, 1 - leverage[i]);

            return row.map(
                value => value * adjusted ** 2
            );
        });

        const middle = multiply(
            transpose(this.X),
            weighted
        );

        const covariance = multiply(
            multiply(this.xtxInverse, middle),
            this.xtxInverse
        );

        return covariance.map(
            (row, i) => Math.sqrt(Math.max(0, row[i]))
        );
    }

    assertFitted() {
        if (this.state !== 'FITTED') {
            throw new RegressionError(
                'Model must be fitted first.'
            );
        }
    }
}

class DiagnosticPolicy {
    constructor(options = {}) {
        this.vifWarning = options.vifWarning ?? 5;
        this.vifCritical = options.vifCritical ?? 10;
        this.bpAlpha = options.bpAlpha ?? 0.05;
        this.cookMultiplier = options.cookMultiplier ?? 4;
        this.leverageMultiplier =
            options.leverageMultiplier ?? 2;
    }

    evaluate(model) {
        model.assertFitted();

        const findings = [];
        const vif = model.getVIF();

        vif.forEach((value, i) => {
            findings.push({
                category: 'MULTICOLLINEARITY',
                predictor: `X${i + 1}`,
                statistic: value,
                status: value >= this.vifCritical
                    ? Status.FAIL
                    : value >= this.vifWarning
                        ? Status.WARNING
                        : Status.PASS
            });
        });

        const bp = model.breuschPagan();

        findings.push({
            category: 'HETEROSCEDASTICITY',
            ...bp,
            status: bp.pValue < this.bpAlpha
                ? Status.WARNING
                : Status.PASS
        });

        const jb = model.jarqueBera();

        findings.push({
            category: 'RESIDUAL_NORMALITY',
            ...jb,
            status: jb.pValue < 0.05
                ? Status.WARNING
                : Status.PASS
        });

        const leverage = model.getLeverage();
        const cooks = model.getCooksDistance();

        const cookThreshold = this.cookMultiplier / model.n;
        const leverageThreshold =
            this.leverageMultiplier * model.p / model.n;

        model.rows.forEach((row, i) => {
            if (cooks[i] > cookThreshold) {
                findings.push({
                    category: 'INFLUENTIAL_OBSERVATION',
                    observation: row.id,
                    statistic: cooks[i],
                    threshold: cookThreshold,
                    status: Status.WARNING
                });
            }

            if (leverage[i] > leverageThreshold) {
                findings.push({
                    category: 'HIGH_LEVERAGE',
                    observation: row.id,
                    statistic: leverage[i],
                    threshold: leverageThreshold,
                    status: Status.WARNING
                });
            }
        });

        return Object.freeze({
            sampleSize: model.n,
            coefficients: [...model.beta],
            rSquared: model.rSquared,
            adjustedRSquared: 1 -
                (1 - model.rSquared) *
                (model.n - 1) / model.df,
            vif,
            breuschPagan: bp,
            jarqueBera: jb,
            hc3StandardErrors: model.getHC3StandardErrors(),
            findings
        });
    }
}

function generateDataset() {
    return Array.from({ length: 80 }, (_, index) => {
        const i = index + 1;
        const x1 = i;
        const x2 = 0.92 * i + (i % 7) * 0.8;

        let error = ((i % 9) - 4) *
            (0.4 + 0.025 * i);

        if (i === 72) error += 35;

        return {
            id: `OBS-${String(i).padStart(3, '0')}`,
            features: [x1, x2],
            target: 12 + 2.5 * x1 + 1.3 * x2 + error
        };
    });
}

async function saveReport(report, filename) {
    const temporary = `${filename}.tmp`;

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(report, null, 2),
            { encoding: 'utf8', flag: 'w' }
        );

        await fs.rename(temporary, filename);
    } catch (error) {
        await fs.rm(temporary, { force: true });
        throw error;
    }
}

async function main() {
    const events = new DiagnosticEventBus();

    events.on('model:fitted', event => {
        process.stdout.write(
            `Model fitted: n=${event.observations}, ` +
            `R²=${event.rSquared.toFixed(5)}\n`
        );
    });

    const model = new RegressionModel(generateDataset());

    model.events.on('model:fitted', event => {
        events.emit('model:fitted', event);
    });

    model.fit();

    const policy = new DiagnosticPolicy();
    const report = policy.evaluate(model);

    console.log('\nREGRESSION DIAGNOSTIC REPORT');
    console.log('============================');
    console.log('Coefficients:', report.coefficients);
    console.log('R-squared:', report.rSquared.toFixed(5));
    console.log('Adjusted R-squared:',
        report.adjustedRSquared.toFixed(5));
    console.log('VIF:', report.vif);
    console.log('Breusch-Pagan:', report.breuschPagan);
    console.log('Jarque-Bera:', report.jarqueBera);
    console.log('HC3 standard errors:',
        report.hc3StandardErrors);

    console.log('\nFindings:');

    for (const finding of report.findings) {
        if (finding.status !== Status.PASS) {
            console.log(
                `[${finding.status}] ${finding.category}`,
                finding.observation ?? finding.predictor ?? '',
                finding.statistic
            );
        }
    }

    await saveReport(
        report,
        'regression_diagnostics.json'
    );

    console.log('\nReport exported successfully.');

    // Validate the diagnostic engine against a known distribution.
    const knownProbability = chiSquareSurvival(
        5.9914645, 2
    );

    if (Math.abs(knownProbability - 0.05) > 1e-5) {
        throw new RegressionError(
            'Chi-square probability validation failed.'
        );
    }

    if (report.vif.some(value => value < 1)) {
        throw new RegressionError('Invalid VIF result.');
    }

    console.log('Validation tests passed.');
}

main().catch(error => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
