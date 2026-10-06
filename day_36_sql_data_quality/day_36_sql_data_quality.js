'use strict';

/*
 * SQL Data Quality: JavaScript workflow model
 *
 * This Node.js program complements the SQL and Python implementations by
 * modeling data-quality checks as an event-driven pipeline. It deliberately
 * focuses on JavaScript-specific mechanisms: immutable records, Map-based
 * grouping, asynchronous pipeline stages, event emission, validation, and
 * deterministic anomaly calculations.
 *
 * Run with:
 *   node data-quality.js
 */

const fs = require('node:fs/promises');
const { EventEmitter } = require('node:events');

const STATUS_VALUES = new Set(['pending', 'paid', 'cancelled', 'refunded']);

class DataQualityIssue {
    constructor({ rule, entity, key, severity, message }) {
        this.rule = rule;
        this.entity = entity;
        this.key = String(key);
        this.severity = severity;
        this.message = message;
        Object.freeze(this);
    }
}

class QualityEventBus extends EventEmitter {
    record(issue) {
        this.emit('issue', issue);
    }

    stageStarted(name) {
        this.emit('stageStarted', name);
    }

    stageFinished(name, count) {
        this.emit('stageFinished', { name, count });
    }
}

function normalizeText(value) {
    return typeof value === 'string' ? value.trim().toLowerCase() : null;
}

function isMissing(value) {
    return value === null ||
        value === undefined ||
        (typeof value === 'string' && value.trim() === '');
}

function parseDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

function percentile(values, percentage) {
    if (!values.length) {
        throw new Error('Cannot calculate a percentile from an empty set.');
    }

    const sorted = [...values].sort((a, b) => a - b);
    const position = (sorted.length - 1) * percentage / 100;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    if (lower === upper) {
        return sorted[lower];
    }

    const weight = position - lower;
    return sorted[lower] + (sorted[upper] - sorted[lower]) * weight;
}

function median(values) {
    return percentile(values, 50);
}

function validateCustomerRecord(customer) {
    const issues = [];

    if (!Number.isInteger(customer.customerId) || customer.customerId <= 0) {
        issues.push(new DataQualityIssue({
            rule: 'invalid_customer_key',
            entity: 'customers',
            key: customer.customerId,
            severity: 'CRITICAL',
            message: 'customerId must be a positive integer'
        }));
    }

    if (isMissing(customer.fullName)) {
        issues.push(new DataQualityIssue({
            rule: 'missing_value',
            entity: 'customers',
            key: customer.customerId,
            severity: 'MEDIUM',
            message: 'fullName is missing'
        }));
    }

    if (isMissing(customer.email)) {
        issues.push(new DataQualityIssue({
            rule: 'missing_value',
            entity: 'customers',
            key: customer.customerId,
            severity: 'MEDIUM',
            message: 'email is missing'
        }));
    }

    if (!isMissing(customer.email) &&
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(customer.email.trim())) {
        issues.push(new DataQualityIssue({
            rule: 'invalid_format',
            entity: 'customers',
            key: customer.customerId,
            severity: 'HIGH',
            message: 'email does not match the expected format'
        }));
    }

    return issues;
}

function detectCustomerDuplicates(customers) {
    const groups = new Map();

    for (const customer of customers) {
        if (isMissing(customer.email)) {
            continue;
        }

        const key = [
            normalizeText(customer.email),
            normalizeText(customer.fullName)
        ].join('|');

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(customer);
    }

    const issues = [];

    for (const [key, group] of groups) {
        if (group.length > 1) {
            issues.push(new DataQualityIssue({
                rule: 'duplicate_customer',
                entity: 'customers',
                key,
                severity: 'HIGH',
                message: `Business identity occurs ${group.length} times: ` +
                    group.map(record => record.customerId).join(', ')
            }));
        }
    }

    return issues;
}

function detectMissingCustomerValues(customers) {
    return customers.flatMap(validateCustomerRecord);
}

function detectReferentialIntegrity(customers, orders) {
    const customerIds = new Set(customers.map(customer => customer.customerId));
    const issues = [];

    for (const order of orders) {
        if (!customerIds.has(order.customerId)) {
            issues.push(new DataQualityIssue({
                rule: 'orphan_order',
                entity: 'orders',
                key: order.orderId,
                severity: 'CRITICAL',
                message: `customerId ${order.customerId} has no parent customer`
            }));
        }
    }

    return issues;
}

function detectOrderDomainViolations(orders) {
    const issues = [];

    for (const order of orders) {
        if (!Number.isFinite(order.amount) || order.amount <= 0) {
            issues.push(new DataQualityIssue({
                rule: 'invalid_amount',
                entity: 'orders',
                key: order.orderId,
                severity: 'HIGH',
                message: `amount=${order.amount} must be positive`
            }));
        }

        if (!STATUS_VALUES.has(order.status)) {
            issues.push(new DataQualityIssue({
                rule: 'invalid_status',
                entity: 'orders',
                key: order.orderId,
                severity: 'HIGH',
                message: `status=${order.status} is not an accepted order state`
            }));
        }

        if (!parseDate(order.orderDate)) {
            issues.push(new DataQualityIssue({
                rule: 'invalid_date',
                entity: 'orders',
                key: order.orderId,
                severity: 'HIGH',
                message: `orderDate=${order.orderDate} is not parseable`
            }));
        }
    }

    return issues;
}

function detectAmountAnomalies(orders) {
    const values = orders
        .map(order => Number(order.amount))
        .filter(amount => Number.isFinite(amount) && amount > 0);

    if (values.length < 4) {
        return [];
    }

    const q1 = percentile(values, 25);
    const q3 = percentile(values, 75);
    const upperFence = q3 + 1.5 * (q3 - q1);

    return orders
        .filter(order =>
            Number.isFinite(order.amount) &&
            order.amount > upperFence
        )
        .map(order => new DataQualityIssue({
            rule: 'amount_anomaly',
            entity: 'orders',
            key: order.orderId,
            severity: 'HIGH',
            message:
                `amount=${order.amount.toFixed(2)} exceeds upper IQR fence ` +
                `${upperFence.toFixed(2)}`
        }));
}

function detectDailyVelocityAnomalies(orders) {
    const groups = new Map();

    for (const order of orders) {
        const date = parseDate(order.orderDate);

        if (!date || order.customerId === null || order.customerId === undefined) {
            continue;
        }

        const day = date.toISOString().slice(0, 10);
        const key = `${order.customerId}|${day}`;

        groups.set(key, (groups.get(key) || 0) + 1);
    }

    const counts = [...groups.values()];
    if (counts.length < 2) {
        return [];
    }

    const average = counts.reduce((sum, value) => sum + value, 0) /
        counts.length;

    const variance = counts.reduce(
        (sum, value) => sum + Math.pow(value - average, 2),
        0
    ) / counts.length;

    const standardDeviation = Math.sqrt(variance);
    const threshold = average + 3 * standardDeviation;
    const issues = [];

    for (const [key, count] of groups) {
        if (count > threshold) {
            const [customerId, day] = key.split('|');

            issues.push(new DataQualityIssue({
                rule: 'order_velocity_anomaly',
                entity: 'orders',
                key,
                severity: 'HIGH',
                message:
                    `${count} orders for customer ${customerId} on ${day} ` +
                    `exceeds threshold ${threshold.toFixed(2)}`
            }));
        }
    }

    return issues;
}

class DataQualityPipeline {
    constructor(data) {
        this.data = data;
        this.events = new QualityEventBus();
        this.issues = [];

        this.events.on('stageStarted', stage => {
            console.log(`\n[START] ${stage}`);
        });

        this.events.on('stageFinished', ({ name, count }) => {
            console.log(`[DONE ] ${name}: ${count} issue(s)`);
        });

        this.events.on('issue', issue => {
            this.issues.push(issue);
        });
    }

    async runStage(name, detector) {
        this.events.stageStarted(name);

        // setImmediate demonstrates that each stage can participate in an
        // asynchronous Node.js workflow without blocking the event loop.
        await new Promise(resolve => setImmediate(resolve));

        const issues = detector(this.data.customers, this.data.orders);

        for (const issue of issues) {
            this.events.record(issue);
        }

        this.events.stageFinished(name, issues.length);
        return issues;
    }

    async run() {
        await this.runStage(
            'Missing values and field validation',
            customers => detectMissingCustomerValues(customers)
        );

        await this.runStage(
            'Duplicate detection',
            customers => detectCustomerDuplicates(customers)
        );

        await this.runStage(
            'Referential integrity',
            (customers, orders) =>
                detectReferentialIntegrity(customers, orders)
        );

        await this.runStage(
            'Order domain validation',
            (_, orders) => detectOrderDomainViolations(orders)
        );

        await this.runStage(
            'Monetary anomaly detection',
            (_, orders) => detectAmountAnomalies(orders)
        );

        await this.runStage(
            'Daily activity anomaly detection',
            (_, orders) => detectDailyVelocityAnomalies(orders)
        );

        return Object.freeze([...this.issues]);
    }

    qualityScore() {
        const rowCount =
            this.data.customers.length + this.data.orders.length;

        if (rowCount === 0) {
            return 100;
        }

        const severityWeights = {
            CRITICAL: 5,
            HIGH: 3,
            MEDIUM: 1,
            LOW: 0.5
        };

        const weightedPenalty = this.issues.reduce(
            (sum, issue) => sum + severityWeights[issue.severity],
            0
        );

        return Math.max(
            0,
            100 - (weightedPenalty / rowCount) * 20
        );
    }
}

async function writeJsonAuditReport(issues, path) {
    const report = {
        generatedAt: new Date().toISOString(),
        issueCount: issues.length,
        issues
    };

    await fs.writeFile(
        path,
        JSON.stringify(report, null, 2),
        'utf8'
    );
}

function createDataset() {
    return {
        customers: [
            Object.freeze({
                customerId: 1,
                fullName: 'Asha Verma',
                email: 'asha@example.com',
                phone: '9876500001'
            }),
            Object.freeze({
                customerId: 2,
                fullName: 'Ravi Kumar',
                email: 'ravi@example.com',
                phone: '9876500002'
            }),
            Object.freeze({
                customerId: 3,
                fullName: 'Ravi Kumar',
                email: 'ravi@example.com',
                phone: '9876500002'
            }),
            Object.freeze({
                customerId: 4,
                fullName: 'Meera Shah',
                email: null,
                phone: '9876500004'
            }),
            Object.freeze({
                customerId: 5,
                fullName: '',
                email: 'meera2@example.com',
                phone: null
            }),
            Object.freeze({
                customerId: 6,
                fullName: 'Kabir Singh',
                email: 'kabir@example.com',
                phone: '9876500006'
            }),
            Object.freeze({
                customerId: 7,
                fullName: 'Nisha Rao',
                email: 'nisha@example.com',
                phone: '9876500007'
            }),
            Object.freeze({
                customerId: 8,
                fullName: 'Omar Khan',
                email: 'omarkhan@example.com',
                phone: '9876500008'
            })
        ],
        orders: [
            Object.freeze({
                orderId: 101,
                customerId: 1,
                amount: 120.50,
                orderDate: '2026-10-01',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 102,
                customerId: 2,
                amount: 80,
                orderDate: '2026-10-01',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 103,
                customerId: 2,
                amount: 75,
                orderDate: '2026-10-01',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 104,
                customerId: 2,
                amount: 70,
                orderDate: '2026-10-01',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 105,
                customerId: 2,
                amount: 65,
                orderDate: '2026-10-01',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 106,
                customerId: 2,
                amount: 55,
                orderDate: '2026-10-01',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 107,
                customerId: 6,
                amount: 150,
                orderDate: '2026-10-02',
                status: 'pending'
            }),
            Object.freeze({
                orderId: 108,
                customerId: 7,
                amount: 210,
                orderDate: '2026-10-02',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 109,
                customerId: 8,
                amount: 9999,
                orderDate: '2026-10-02',
                status: 'paid'
            }),
            Object.freeze({
                orderId: 110,
                customerId: 1,
                amount: 95,
                orderDate: '2026-10-03',
                status: 'cancelled'
            }),
            Object.freeze({
                orderId: 111,
                customerId: 999,
                amount: 45,
                orderDate: '2026-10-03',
                status: 'paid'
            })
        ]
    };
}

async function main() {
    const data = createDataset();
    const pipeline = new DataQualityPipeline(data);

    const issues = await pipeline.run();

    console.log('\n=== QUALITY ISSUE DETAILS ===');

    for (const issue of issues) {
        console.log(
            `[${issue.severity}] ${issue.rule} ` +
            `${issue.entity}:${issue.key} - ${issue.message}`
        );
    }

    const amounts = data.orders
        .map(order => order.amount)
        .filter(amount => Number.isFinite(amount) && amount > 0);

    console.log('\n=== DISTRIBUTION ===');
    console.log(`Mean: ${(
        amounts.reduce((sum, value) => sum + value, 0) /
        amounts.length
    ).toFixed(2)}`);
    console.log(`Median: ${median(amounts).toFixed(2)}`);
    console.log(`P95: ${percentile(amounts, 95).toFixed(2)}`);

    console.log('\n=== QUALITY SCORE ===');
    console.log(`${pipeline.qualityScore().toFixed(2)}/100`);

    await writeJsonAuditReport(
        issues,
        'javascript_data_quality_report.json'
    );

    console.log(
        '\nAudit report written to javascript_data_quality_report.json'
    );
}

main().catch(error => {
    console.error('Data-quality pipeline failed:', error);
    process.exitCode = 1;
});
