'use strict';

/*
 * POWER BI ADVANCED ANALYTICS
 *
 * JavaScript implementation emphasizing:
 * - Event-driven analytical pipelines
 * - Decomposition trees
 * - Key influencer evaluation
 * - Time-series forecasting
 * - Anomaly detection
 * - Immutable analytical results
 * - Asynchronous report generation
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

class AnalyticsError extends Error {
    constructor(message) {
        super(message);
        this.name = 'AnalyticsError';
    }
}

class ValidationError extends AnalyticsError {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

class InsufficientDataError extends AnalyticsError {
    constructor(message) {
        super(message);
        this.name = 'InsufficientDataError';
    }
}

const DIMENSIONS = Object.freeze([
    'region',
    'product',
    'segment',
    'channel'
]);

const TARGETS = Object.freeze({
    HIGH_REVENUE: 'high_revenue',
    HIGH_SATISFACTION: 'high_satisfaction',
    HIGH_DISCOUNT: 'high_discount'
});

function assertFinite(value, field) {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
        throw new ValidationError(`${field} must be a finite number.`);
    }
}

function validateRecord(record) {
    if (!Number.isInteger(record.transactionId) ||
        record.transactionId <= 0) {
        throw new ValidationError('Invalid transaction ID.');
    }

    for (const field of DIMENSIONS) {
        if (typeof record[field] !== 'string' ||
            record[field].trim() === '') {
            throw new ValidationError(`${field} cannot be empty.`);
        }
    }

    assertFinite(record.revenue, 'Revenue');
    assertFinite(record.marketingSpend, 'Marketing spend');
    assertFinite(record.discount, 'Discount');
    assertFinite(record.satisfaction, 'Satisfaction');

    if (record.revenue < 0 || record.marketingSpend < 0) {
        throw new ValidationError('Negative financial values are invalid.');
    }

    if (!Number.isInteger(record.units) || record.units < 0) {
        throw new ValidationError('Units must be a non-negative integer.');
    }

    if (record.discount < 0 || record.discount > 100) {
        throw new ValidationError('Discount must be between 0 and 100.');
    }

    if (record.satisfaction < 0 || record.satisfaction > 10) {
        throw new ValidationError('Invalid satisfaction score.');
    }

    if (!/^\d{4}-\d{2}-\d{2}$/.test(record.date)) {
        throw new ValidationError('Date must use YYYY-MM-DD format.');
    }

    const parsedDate = new Date(`${record.date}T00:00:00.000Z`);

    if (Number.isNaN(parsedDate.getTime()) ||
        parsedDate.toISOString().slice(0, 10) !== record.date) {
        throw new ValidationError('Invalid calendar date.');
    }
}

function median(values) {
    if (values.length === 0) {
        throw new InsufficientDataError('Cannot calculate empty median.');
    }

    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];
}

function average(values) {
    if (values.length === 0) {
        return 0;
    }

    return values.reduce((sum, value) => sum + value, 0) /
        values.length;
}

// ============================================================
// DETERMINISTIC DATA GENERATION
// ============================================================

class RandomGenerator {
    constructor(seed = 42) {
        this.seed = seed >>> 0;
    }

    next() {
        this.seed = (
            Math.imul(1664525, this.seed) + 1013904223
        ) >>> 0;

        return this.seed / 4294967296;
    }

    between(min, max) {
        return min + this.next() * (max - min);
    }

    integer(min, max) {
        return Math.floor(this.between(min, max + 1));
    }

    choose(values) {
        return values[this.integer(0, values.length - 1)];
    }
}

function generateRecords(count = 600) {
    if (!Number.isInteger(count) || count < 30) {
        throw new ValidationError('At least 30 records are required.');
    }

    const random = new RandomGenerator();

    const regions = ['North', 'South', 'East', 'West'];
    const products = ['Laptop', 'Mobile', 'Tablet', 'Monitor'];
    const segments = ['Consumer', 'Corporate', 'Small Business'];
    const channels = ['Online', 'Retail', 'Partner'];

    const prices = {
        Laptop: 850,
        Mobile: 420,
        Tablet: 300,
        Monitor: 260
    };

    const regionFactors = {
        North: 1.15,
        South: 1.05,
        East: 0.90,
        West: 1.10
    };

    const segmentFactors = {
        Consumer: 1.0,
        Corporate: 1.30,
        'Small Business': 1.10
    };

    const records = [];

    for (let i = 0; i < count; i++) {
        const month = String(Math.floor((i % 365) / 30) + 1)
            .padStart(2, '0');

        const day = String((i % 28) + 1).padStart(2, '0');

        const region = random.choose(regions);
        const product = random.choose(products);
        const segment = random.choose(segments);
        const channel = random.choose(channels);

        const units = random.integer(1, 12);
        const discount = random.between(0, 20);

        let revenue =
            prices[product] *
            units *
            regionFactors[region] *
            segmentFactors[segment] *
            (1 - discount / 100);

        revenue += random.between(-90, 90);
        revenue = Math.max(0, revenue);

        if ([75, 190, 330, 470].includes(i)) {
            revenue *= 3.5;
        }

        records.push({
            transactionId: i + 1,
            date: `2025-${month}-${day}`,
            region,
            product,
            segment,
            channel,
            units,
            revenue: Number(revenue.toFixed(2)),
            marketingSpend: Number(
                random.between(50, 600).toFixed(2)
            ),
            discount: Number(discount.toFixed(2)),
            satisfaction: Number(
                random.between(5, 10).toFixed(2)
            )
        });
    }

    return records;
}

// ============================================================
// EVENT-DRIVEN ANALYTICS SERVICE
// ============================================================

class AnalyticsEngine extends EventTarget {
    #records;
    #cache;

    constructor(records) {
        super();

        if (!Array.isArray(records) || records.length === 0) {
            throw new InsufficientDataError('Dataset cannot be empty.');
        }

        const ids = new Set();

        for (const record of records) {
            validateRecord(record);

            if (ids.has(record.transactionId)) {
                throw new ValidationError('Duplicate transaction ID.');
            }

            ids.add(record.transactionId);
        }

        this.#records = Object.freeze(
            records.map(record => Object.freeze({ ...record }))
        );

        this.#cache = new Map();
    }

    get recordCount() {
        return this.#records.length;
    }

    getRecords() {
        return this.#records.map(record => ({ ...record }));
    }

    #emit(eventName, detail) {
        this.dispatchEvent(
            new CustomEvent(eventName, {
                detail: Object.freeze(detail)
            })
        );
    }

    #cached(key, calculate) {
        if (this.#cache.has(key)) {
            return this.#cache.get(key);
        }

        const result = calculate();

        this.#cache.set(key, result);

        return result;
    }

    // ========================================================
    // BUSINESS MEASURES
    // ========================================================

    measures() {
        return this.#cached('measures', () => {
            const revenue = this.#records.reduce(
                (sum, record) => sum + record.revenue,
                0
            );

            const units = this.#records.reduce(
                (sum, record) => sum + record.units,
                0
            );

            const marketing = this.#records.reduce(
                (sum, record) => sum + record.marketingSpend,
                0
            );

            return Object.freeze({
                transactions: this.#records.length,
                revenue: Number(revenue.toFixed(2)),
                units,
                averageRevenue: Number(
                    (revenue / this.#records.length).toFixed(2)
                ),
                marketingSpend: Number(marketing.toFixed(2)),
                marketingROI: Number(
                    ((revenue - marketing) /
                        Math.max(marketing, 1)).toFixed(3)
                ),
                satisfaction: Number(
                    average(this.#records.map(r => r.satisfaction))
                        .toFixed(2)
                )
            });
        });
    }

    // ========================================================
    // DECOMPOSITION TREE
    // ========================================================

    decompositionTree(dimensions, topN = 5) {
        if (!Array.isArray(dimensions) || dimensions.length === 0) {
            throw new ValidationError('Dimensions are required.');
        }

        if (new Set(dimensions).size !== dimensions.length) {
            throw new ValidationError('Duplicate dimensions are invalid.');
        }

        if (dimensions.some(d => !DIMENSIONS.includes(d))) {
            throw new ValidationError('Unsupported dimension.');
        }

        if (!Number.isInteger(topN) || topN < 1) {
            throw new ValidationError('topN must be positive.');
        }

        const build = (records, depth) => {
            if (depth >= dimensions.length) {
                return [];
            }

            const dimension = dimensions[depth];
            const groups = new Map();

            for (const record of records) {
                const value = record[dimension];

                if (!groups.has(value)) {
                    groups.set(value, []);
                }

                groups.get(value).push(record);
            }

            const total = records.reduce(
                (sum, record) => sum + record.revenue,
                0
            );

            return [...groups.entries()]
                .map(([value, group]) => {
                    const revenue = group.reduce(
                        (sum, record) => sum + record.revenue,
                        0
                    );

                    return {
                        dimension,
                        value,
                        revenue: Number(revenue.toFixed(2)),
                        count: group.length,
                        contribution: Number(
                            (total > 0 ? revenue / total * 100 : 0)
                                .toFixed(2)
                        ),
                        children: build(group, depth + 1)
                    };
                })
                .sort((a, b) => b.revenue - a.revenue)
                .slice(0, topN);
        };

        const result = build(this.#records, 0);

        this.#emit('decomposition-complete', {
            dimensions,
            rootCount: result.length
        });

        return result;
    }

    // ========================================================
    // KEY INFLUENCERS
    // ========================================================

    keyInfluencers(target = TARGETS.HIGH_REVENUE) {
        const targetFields = {
            [TARGETS.HIGH_REVENUE]: 'revenue',
            [TARGETS.HIGH_SATISFACTION]: 'satisfaction',
            [TARGETS.HIGH_DISCOUNT]: 'discount'
        };

        if (!Object.hasOwn(targetFields, target)) {
            throw new ValidationError('Unsupported target.');
        }

        const field = targetFields[target];

        const threshold = median(
            this.#records.map(record => record[field])
        );

        const results = [];

        for (const dimension of DIMENSIONS) {
            const groups = new Map();

            for (const record of this.#records) {
                const value = record[dimension];

                if (!groups.has(value)) {
                    groups.set(value, []);
                }

                groups.get(value).push(record);
            }

            for (const [value, group] of groups) {
                if (group.length < 10) {
                    continue;
                }

                const comparison = this.#records.filter(
                    record => record[dimension] !== value
                );

                const targetRate = group.filter(
                    record => record[field] > threshold
                ).length / group.length;

                const comparisonRate = comparison.filter(
                    record => record[field] > threshold
                ).length / comparison.length;

                const difference = targetRate - comparisonRate;

                if (difference <= 0) {
                    continue;
                }

                results.push({
                    dimension,
                    value,
                    sampleSize: group.length,
                    comparisonSize: comparison.length,
                    targetRate: Number(targetRate.toFixed(4)),
                    comparisonRate: Number(
                        comparisonRate.toFixed(4)
                    ),
                    difference: Number(difference.toFixed(4)),
                    relativeChange: Number(
                        (
                            comparisonRate > 0
                                ? difference / comparisonRate * 100
                                : 100
                        ).toFixed(2)
                    )
                });
            }
        }

        results.sort(
            (a, b) =>
                b.difference - a.difference ||
                b.sampleSize - a.sampleSize
        );

        this.#emit('influencers-complete', {
            target,
            resultCount: results.length
        });

        return results;
    }

    // ========================================================
    // MONTHLY AGGREGATION
    // ========================================================

    monthlyRevenue() {
        return this.#cached('monthlyRevenue', () => {
            const grouped = new Map();

            for (const record of this.#records) {
                const month = record.date.slice(0, 7);

                grouped.set(
                    month,
                    (grouped.get(month) || 0) + record.revenue
                );
            }

            return [...grouped.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([period, revenue]) => ({
                    period,
                    revenue: Number(revenue.toFixed(2))
                }));
        });
    }

    // ========================================================
    // FORECASTING
    // ========================================================

    forecast(periods = 3) {
        if (!Number.isInteger(periods) ||
            periods < 1 ||
            periods > 36) {
            throw new ValidationError('Invalid forecast horizon.');
        }

        const history = this.monthlyRevenue();

        if (history.length < 6) {
            throw new InsufficientDataError(
                'Six monthly observations are required.'
            );
        }

        const values = history.map(item => item.revenue);

        const xMean = (values.length - 1) / 2;
        const yMean = average(values);

        let numerator = 0;
        let denominator = 0;

        for (let i = 0; i < values.length; i++) {
            numerator += (i - xMean) * (values[i] - yMean);
            denominator += (i - xMean) ** 2;
        }

        if (denominator === 0) {
            throw new InsufficientDataError('Regression is undefined.');
        }

        const slope = numerator / denominator;
        const intercept = yMean - slope * xMean;

        const residuals = values.map(
            (value, i) => value - (intercept + slope * i)
        );

        const residualMean = average(residuals);

        const variance = residuals.reduce(
            (sum, value) =>
                sum + (value - residualMean) ** 2,
            0
        ) / (residuals.length - 1);

        const residualStd = Math.sqrt(variance);

        const lastPeriod = history[history.length - 1].period;
        const [lastYear, lastMonth] = lastPeriod.split('-').map(Number);

        const results = [];

        for (let step = 1; step <= periods; step++) {
            const index = values.length - 1 + step;

            const prediction = Math.max(
                0,
                intercept + slope * index
            );

            const uncertainty = 1.96 * residualStd *
                Math.sqrt(1 + step / values.length);

            const monthIndex = lastMonth - 1 + step;
            const year = lastYear + Math.floor(monthIndex / 12);
            const month = (monthIndex % 12) + 1;

            results.push({
                period: `${year}-${String(month).padStart(2, '0')}`,
                prediction: Number(prediction.toFixed(2)),
                lowerBound: Number(
                    Math.max(0, prediction - uncertainty).toFixed(2)
                ),
                upperBound: Number(
                    (prediction + uncertainty).toFixed(2)
                )
            });
        }

        this.#emit('forecast-complete', {
            periods,
            resultCount: results.length
        });

        return results;
    }

    // ========================================================
    // ANOMALY DETECTION
    // ========================================================

    detectAnomalies(threshold = 3.5) {
        assertFinite(threshold, 'Threshold');

        if (threshold <= 0) {
            throw new ValidationError('Threshold must be positive.');
        }

        const values = this.#records.map(
            record => record.revenue
        );

        const center = median(values);

        const mad = median(
            values.map(value => Math.abs(value - center))
        );

        if (mad === 0) {
            throw new InsufficientDataError(
                'Median absolute deviation is zero.'
            );
        }

        const anomalies = [];

        for (const record of this.#records) {
            const score = 0.6745 *
                (record.revenue - center) / mad;

            if (Math.abs(score) >= threshold) {
                anomalies.push({
                    transactionId: record.transactionId,
                    revenue: record.revenue,
                    expected: Number(center.toFixed(2)),
                    score: Number(score.toFixed(3)),
                    direction: score > 0 ? 'HIGH' : 'LOW',
                    severity: Math.abs(score) >= 7
                        ? 'CRITICAL'
                        : 'HIGH'
                });
            }
        }

        anomalies.sort(
            (a, b) => Math.abs(b.score) - Math.abs(a.score)
        );

        this.#emit('anomalies-complete', {
            count: anomalies.length
        });

        return anomalies;
    }

    // ========================================================
    // ASYNCHRONOUS REPORT GENERATION
    // ========================================================

    async generateReport(destination) {
        if (typeof destination !== 'string' ||
            destination.trim() === '') {
            throw new ValidationError('Report path is required.');
        }

        const report = {
            reportId: randomUUID(),
            generatedAt: new Date().toISOString(),
            recordCount: this.recordCount,
            measures: this.measures(),
            decomposition: this.decompositionTree([
                'region',
                'product',
                'channel'
            ]),
            influencers: this.keyInfluencers(),
            monthlyRevenue: this.monthlyRevenue(),
            forecast: this.forecast(3),
            anomalies: this.detectAnomalies()
        };

        const absolutePath = path.resolve(destination);
        const directory = path.dirname(absolutePath);

        await fs.mkdir(directory, { recursive: true });

        const temporaryPath = path.join(
            directory,
            `.${path.basename(absolutePath)}.${randomUUID()}.tmp`
        );

        try {
            await fs.writeFile(
                temporaryPath,
                JSON.stringify(report, null, 2),
                {
                    encoding: 'utf8',
                    flag: 'wx',
                    mode: 0o600
                }
            );

            await fs.rename(temporaryPath, absolutePath);

            this.#emit('report-complete', {
                destination: absolutePath,
                reportId: report.reportId
            });

            return report;

        } catch (error) {
            await fs.rm(temporaryPath, { force: true });
            throw error;
        }
    }
}

// ============================================================
// APPLICATION ENTRY POINT
// ============================================================

async function main() {
    const records = generateRecords(600);
    const engine = new AnalyticsEngine(records);

    const eventNames = [
        'decomposition-complete',
        'influencers-complete',
        'forecast-complete',
        'anomalies-complete',
        'report-complete'
    ];

    for (const eventName of eventNames) {
        engine.addEventListener(eventName, event => {
            console.log(
                `[EVENT] ${eventName}`,
                JSON.stringify(event.detail)
            );
        });
    }

    console.log('\n1. BUSINESS MEASURES');
    console.table(engine.measures());

    console.log('\n2. DECOMPOSITION TREE');
    console.dir(
        engine.decompositionTree(
            ['region', 'product', 'channel'],
            3
        ),
        { depth: null }
    );

    console.log('\n3. KEY INFLUENCERS');
    console.table(
        engine.keyInfluencers().slice(0, 8)
    );

    console.log('\n4. FORECAST');
    console.table(engine.forecast(3));

    console.log('\n5. ANOMALIES');
    console.table(engine.detectAnomalies().slice(0, 10));

    console.log('\n6. REPORT');

    const report = await engine.generateReport(
        'powerbi_advanced_analytics_report.json'
    );

    console.log('Report ID:', report.reportId);
    console.log('Records:', report.recordCount);

    if (report.recordCount !== 600) {
        throw new AnalyticsError('Record count validation failed.');
    }

    if (report.forecast.length !== 3) {
        throw new AnalyticsError('Forecast validation failed.');
    }

    console.log('\nAll analytical operations completed.');
}

main().catch(error => {
    console.error(`[${error.name}] ${error.message}`);
    process.exitCode = 1;
});
