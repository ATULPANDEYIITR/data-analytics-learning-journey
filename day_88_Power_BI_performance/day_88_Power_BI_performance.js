'use strict';

/**
 * Power BI Performance Engineering
 * ---------------------------------
 * Event-driven semantic model and query performance evaluator.
 *
 * Features:
 * - Semantic model metadata
 * - Storage mode evaluation
 * - DAX pattern inspection
 * - Query workload simulation
 * - Asynchronous query scheduling
 * - Concurrency control
 * - Performance policy evaluation
 * - Event-driven monitoring
 * - Benchmarking
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require('node:events');
const { performance } = require('node:perf_hooks');
const fs = require('node:fs/promises');


/* ============================================================
   1. DOMAIN ENUMERATIONS
   ============================================================ */

const StorageMode = Object.freeze({
    IMPORT: 'Import',
    DIRECTQUERY: 'DirectQuery',
    DUAL: 'Dual',
    DIRECTLAKE: 'DirectLake'
});

const TableRole = Object.freeze({
    FACT: 'Fact',
    DIMENSION: 'Dimension',
    BRIDGE: 'Bridge'
});

const Severity = Object.freeze({
    CRITICAL: 'Critical',
    HIGH: 'High',
    MEDIUM: 'Medium',
    LOW: 'Low'
});

const QueryType = Object.freeze({
    AGGREGATION: 'Aggregation',
    DETAIL: 'Detail',
    TIME_INTELLIGENCE: 'TimeIntelligence',
    CROSS_FILTER: 'CrossFilter'
});


/* ============================================================
   2. VALIDATION
   ============================================================ */

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

function requireString(value, field) {
    if (typeof value !== 'string' || !value.trim()) {
        throw new ValidationError(`${field} must be a non-empty string`);
    }
}

function requireNonNegative(value, field) {
    if (
        typeof value !== 'number' ||
        !Number.isFinite(value) ||
        value < 0
    ) {
        throw new ValidationError(
            `${field} must be a finite non-negative number`
        );
    }
}

function requirePositiveInteger(value, field) {
    if (!Number.isSafeInteger(value) || value <= 0) {
        throw new ValidationError(
            `${field} must be a positive safe integer`
        );
    }
}


/* ============================================================
   3. SEMANTIC MODEL OBJECTS
   ============================================================ */

class ModelColumn {
    constructor({
        name,
        dataType,
        cardinality,
        used = true,
        key = false
    }) {
        requireString(name, 'Column name');
        requireNonNegative(cardinality, 'Cardinality');

        const supportedTypes = [
            'integer',
            'decimal',
            'string',
            'date',
            'boolean'
        ];

        if (!supportedTypes.includes(dataType)) {
            throw new ValidationError(
                `Unsupported data type: ${dataType}`
            );
        }

        this.name = name;
        this.dataType = dataType;
        this.cardinality = cardinality;
        this.used = Boolean(used);
        this.key = Boolean(key);
    }
}

class ModelTable {
    constructor({
        name,
        role,
        rows,
        storageMode = StorageMode.IMPORT,
        queryFolding = true,
        columns = []
    }) {
        requireString(name, 'Table name');
        requireNonNegative(rows, 'Rows');

        if (!Object.values(TableRole).includes(role)) {
            throw new ValidationError('Invalid table role');
        }

        if (!Object.values(StorageMode).includes(storageMode)) {
            throw new ValidationError('Invalid storage mode');
        }

        this.name = name;
        this.role = role;
        this.rows = rows;
        this.storageMode = storageMode;
        this.queryFolding = Boolean(queryFolding);

        this.columns = new Map();

        for (const column of columns) {
            if (!(column instanceof ModelColumn)) {
                throw new ValidationError(
                    'Columns must be ModelColumn instances'
                );
            }

            if (column.cardinality > rows) {
                throw new ValidationError(
                    `Column ${column.name} exceeds table row count`
                );
            }

            if (this.columns.has(column.name)) {
                throw new ValidationError(
                    `Duplicate column ${column.name}`
                );
            }

            this.columns.set(column.name, column);
        }
    }

    get unusedColumns() {
        return [...this.columns.values()]
            .filter(column => !column.used && !column.key)
            .map(column => column.name);
    }

    estimateMemoryMB() {
        if (
            ![
                StorageMode.IMPORT,
                StorageMode.DUAL
            ].includes(this.storageMode)
        ) {
            return 0;
        }

        let bytes = 0;

        for (const column of this.columns.values()) {
            const bits = Math.max(
                1,
                Math.ceil(
                    Math.log2(Math.max(2, column.cardinality))
                )
            );

            const encodedBytes = Math.ceil(
                this.rows * bits / 8
            );

            const dictionaryBytes =
                column.cardinality *
                (column.dataType === 'string' ? 24 : 8);

            bytes += encodedBytes + dictionaryBytes;
        }

        return bytes / (1024 * 1024);
    }
}


/* ============================================================
   4. MODEL REGISTRY
   ============================================================ */

class SemanticModel {

    constructor(name) {
        requireString(name, 'Model name');

        this.name = name;
        this.tables = new Map();
        this.relationships = [];
    }

    addTable(table) {
        if (!(table instanceof ModelTable)) {
            throw new ValidationError('Invalid table');
        }

        if (this.tables.has(table.name)) {
            throw new ValidationError(
                `Table already exists: ${table.name}`
            );
        }

        this.tables.set(table.name, table);
    }

    addRelationship({
        fromTable,
        fromColumn,
        toTable,
        toColumn,
        cardinality = 'ManyToOne',
        bidirectional = false
    }) {
        const source = this.tables.get(fromTable);
        const target = this.tables.get(toTable);

        if (!source || !target) {
            throw new ValidationError(
                'Relationship references unknown table'
            );
        }

        if (
            !source.columns.has(fromColumn) ||
            !target.columns.has(toColumn)
        ) {
            throw new ValidationError(
                'Relationship references unknown column'
            );
        }

        if (
            ![
                'OneToOne',
                'OneToMany',
                'ManyToOne',
                'ManyToMany'
            ].includes(cardinality)
        ) {
            throw new ValidationError(
                'Invalid relationship cardinality'
            );
        }

        this.relationships.push({
            fromTable,
            fromColumn,
            toTable,
            toColumn,
            cardinality,
            bidirectional: Boolean(bidirectional)
        });
    }

    statistics() {
        return {
            name: this.name,
            tableCount: this.tables.size,
            relationshipCount: this.relationships.length,
            rowCount: [...this.tables.values()]
                .reduce((sum, table) => sum + table.rows, 0),
            estimatedMemoryMB: Number(
                [...this.tables.values()]
                    .reduce(
                        (sum, table) =>
                            sum + table.estimateMemoryMB(),
                        0
                    )
                    .toFixed(2)
            )
        };
    }
}


/* ============================================================
   5. PERFORMANCE POLICY ENGINE
   ============================================================ */

class PerformancePolicy {

    constructor({
        maximumFormulaEngineShare = 0.4,
        maximumSourceLatencyMs = 500,
        maximumVisualLatencyMs = 300,
        maximumUnusedColumns = 0
    } = {}) {
        this.maximumFormulaEngineShare =
            maximumFormulaEngineShare;

        this.maximumSourceLatencyMs =
            maximumSourceLatencyMs;

        this.maximumVisualLatencyMs =
            maximumVisualLatencyMs;

        this.maximumUnusedColumns =
            maximumUnusedColumns;
    }

    evaluateQuery(query) {
        const total =
            query.storageEngineMs +
            query.formulaEngineMs +
            query.sourceMs +
            query.visualRenderMs;

        const formulaShare =
            total === 0 ? 0 : query.formulaEngineMs / total;

        const violations = [];

        if (
            formulaShare >
            this.maximumFormulaEngineShare
        ) {
            violations.push({
                code: 'FORMULA_ENGINE_HIGH',
                severity: Severity.HIGH,
                message: 'Formula Engine share exceeds policy'
            });
        }

        if (
            query.sourceMs >
            this.maximumSourceLatencyMs
        ) {
            violations.push({
                code: 'SOURCE_LATENCY_HIGH',
                severity: Severity.HIGH,
                message: 'Source query latency exceeds policy'
            });
        }

        if (
            query.visualRenderMs >
            this.maximumVisualLatencyMs
        ) {
            violations.push({
                code: 'VISUAL_RENDER_HIGH',
                severity: Severity.MEDIUM,
                message: 'Visual rendering exceeds policy'
            });
        }

        return {
            totalMs: total,
            formulaShare,
            passed: violations.length === 0,
            violations
        };
    }

    evaluateModel(model) {
        const violations = [];

        for (const table of model.tables.values()) {
            if (
                table.unusedColumns.length >
                this.maximumUnusedColumns
            ) {
                violations.push({
                    code: 'UNUSED_COLUMNS',
                    table: table.name,
                    severity: Severity.MEDIUM,
                    count: table.unusedColumns.length
                });
            }
        }

        return {
            passed: violations.length === 0,
            violations
        };
    }
}


/* ============================================================
   6. DAX PATTERN CATALOG
   ============================================================ */

class DAXCatalog {

    static analyze({
        expression,
        pattern,
        iterations = 0,
        repeatedExpressions = 0
    }) {
        requireString(expression, 'DAX expression');

        requireNonNegative(iterations, 'Iterations');
        requireNonNegative(
            repeatedExpressions,
            'Repeated expressions'
        );

        const findings = [];

        if (pattern === 'SUMX') {
            findings.push(
                'Check whether the calculation can be performed ' +
                'as a storage-engine SUM over a source or model column.'
            );
        }

        if (pattern === 'FILTER_ALL') {
            findings.push(
                'Review broad filter-table construction and ' +
                'whether a Boolean filter is sufficient.'
            );
        }

        if (pattern === 'REPEATED_EXPRESSION') {
            findings.push(
                'Consider VAR for reusable expressions evaluated ' +
                'in the same context.'
            );
        }

        if (iterations > 1000000) {
            findings.push(
                'Large iterator workload. Profile Formula Engine work.'
            );
        }

        if (repeatedExpressions > 1) {
            findings.push(
                'Repeated calculation detected.'
            );
        }

        return {
            pattern,
            findings: findings.length
                ? findings
                : ['No obvious pattern-level issue detected']
        };
    }
}


/* ============================================================
   7. QUERY WORKLOAD
   ============================================================ */

class QueryRequest {

    constructor({
        id,
        type,
        storageEngineMs,
        formulaEngineMs,
        sourceMs = 0,
        visualRenderMs = 0
    }) {
        requireString(id, 'Query ID');

        if (!Object.values(QueryType).includes(type)) {
            throw new ValidationError('Invalid query type');
        }

        for (const [name, value] of Object.entries({
            storageEngineMs,
            formulaEngineMs,
            sourceMs,
            visualRenderMs
        })) {
            requireNonNegative(value, name);
        }

        this.id = id;
        this.type = type;
        this.storageEngineMs = storageEngineMs;
        this.formulaEngineMs = formulaEngineMs;
        this.sourceMs = sourceMs;
        this.visualRenderMs = visualRenderMs;
    }

    get estimatedDurationMs() {
        return (
            this.storageEngineMs +
            this.formulaEngineMs +
            this.sourceMs +
            this.visualRenderMs
        );
    }
}


/* ============================================================
   8. CONCURRENCY-LIMITED EXECUTION
   ============================================================ */

class QueryScheduler extends EventEmitter {

    constructor(maxConcurrency = 3) {
        super();

        requirePositiveInteger(
            maxConcurrency,
            'Maximum concurrency'
        );

        this.maxConcurrency = maxConcurrency;
        this.active = 0;
        this.queue = [];
        this.completed = 0;
        this.failed = 0;
    }

    submit(request) {
        if (!(request instanceof QueryRequest)) {
            return Promise.reject(
                new ValidationError('Invalid query request')
            );
        }

        return new Promise((resolve, reject) => {
            this.queue.push({
                request,
                resolve,
                reject
            });

            this.emit('queued', {
                queryId: request.id,
                queueLength: this.queue.length
            });

            this.processQueue();
        });
    }

    processQueue() {
        while (
            this.active < this.maxConcurrency &&
            this.queue.length > 0
        ) {
            const task = this.queue.shift();

            this.active++;

            this.execute(task)
                .finally(() => {
                    this.active--;
                    this.processQueue();
                });
        }
    }

    async execute(task) {
        const { request, resolve, reject } = task;

        const started = performance.now();

        try {
            // Simulated query execution time.
            // A real integration would submit work to a data source.
            await new Promise(done => {
                setTimeout(
                    done,
                    Math.min(request.estimatedDurationMs, 5000)
                );
            });

            const result = {
                queryId: request.id,
                durationMs: Number(
                    (performance.now() - started).toFixed(2)
                ),
                estimatedDurationMs: request.estimatedDurationMs,
                status: 'COMPLETED'
            };

            this.completed++;
            this.emit('completed', result);
            resolve(result);

        } catch (error) {
            this.failed++;

            this.emit('failed', {
                queryId: request.id,
                message: error.message
            });

            reject(error);
        }
    }

    get statistics() {
        return {
            active: this.active,
            queued: this.queue.length,
            completed: this.completed,
            failed: this.failed
        };
    }
}


/* ============================================================
   9. EVENT-DRIVEN MONITOR
   ============================================================ */

class PerformanceMonitor extends EventEmitter {

    constructor(policy) {
        super();

        this.policy = policy;
        this.history = [];
    }

    record(query) {
        const evaluation = this.policy.evaluateQuery(query);

        const record = {
            queryId: query.id,
            totalMs: evaluation.totalMs,
            passed: evaluation.passed,
            violations: evaluation.violations,
            timestamp: new Date().toISOString()
        };

        this.history.push(record);

        this.emit('queryEvaluated', record);

        if (!evaluation.passed) {
            this.emit('performanceViolation', record);
        }

        return record;
    }

    report() {
        const durations = this.history.map(
            item => item.totalMs
        );

        const sorted = [...durations].sort(
            (a, b) => a - b
        );

        const percentile = (p) => {
            if (!sorted.length) return 0;

            return sorted[
                Math.min(
                    sorted.length - 1,
                    Math.ceil(p * sorted.length) - 1
                )
            ];
        };

        return {
            queries: this.history.length,
            failures: this.history.filter(
                item => !item.passed
            ).length,
            meanMs: durations.length
                ? durations.reduce((a, b) => a + b, 0) /
                  durations.length
                : 0,
            p95Ms: percentile(0.95),
            p99Ms: percentile(0.99)
        };
    }
}


/* ============================================================
   10. MODEL FACTORY
   ============================================================ */

function buildModel() {
    const model = new SemanticModel(
        'Enterprise Sales Analytics'
    );

    model.addTable(
        new ModelTable({
            name: 'Sales',
            role: TableRole.FACT,
            rows: 2000000,
            columns: [
                new ModelColumn({
                    name: 'SalesID',
                    dataType: 'integer',
                    cardinality: 2000000,
                    key: true
                }),
                new ModelColumn({
                    name: 'ProductKey',
                    dataType: 'integer',
                    cardinality: 5000
                }),
                new ModelColumn({
                    name: 'DateKey',
                    dataType: 'integer',
                    cardinality: 1825
                }),
                new ModelColumn({
                    name: 'SalesAmount',
                    dataType: 'decimal',
                    cardinality: 250000
                }),
                new ModelColumn({
                    name: 'TransactionReference',
                    dataType: 'string',
                    cardinality: 1900000
                }),
                new ModelColumn({
                    name: 'UnusedDescription',
                    dataType: 'string',
                    cardinality: 2000,
                    used: false
                })
            ]
        })
    );

    model.addTable(
        new ModelTable({
            name: 'Product',
            role: TableRole.DIMENSION,
            rows: 5000,
            columns: [
                new ModelColumn({
                    name: 'ProductKey',
                    dataType: 'integer',
                    cardinality: 5000,
                    key: true
                }),
                new ModelColumn({
                    name: 'Category',
                    dataType: 'string',
                    cardinality: 12
                })
            ]
        })
    );

    model.addTable(
        new ModelTable({
            name: 'Date',
            role: TableRole.DIMENSION,
            rows: 1825,
            columns: [
                new ModelColumn({
                    name: 'DateKey',
                    dataType: 'integer',
                    cardinality: 1825,
                    key: true
                }),
                new ModelColumn({
                    name: 'Year',
                    dataType: 'integer',
                    cardinality: 5
                })
            ]
        })
    );

    model.addRelationship({
        fromTable: 'Sales',
        fromColumn: 'ProductKey',
        toTable: 'Product',
        toColumn: 'ProductKey'
    });

    model.addRelationship({
        fromTable: 'Sales',
        fromColumn: 'DateKey',
        toTable: 'Date',
        toColumn: 'DateKey'
    });

    return model;
}


/* ============================================================
   11. MODEL OPTIMIZATION
   ============================================================ */

function optimizeModel(model) {
    const recommendations = [];

    for (const table of model.tables.values()) {

        if (table.unusedColumns.length) {
            recommendations.push({
                table: table.name,
                severity: Severity.HIGH,
                recommendation:
                    'Remove unused columns from the semantic model'
            });
        }

        if (
            table.role === TableRole.FACT &&
            table.rows > 1000000 &&
            !table.queryFolding
        ) {
            recommendations.push({
                table: table.name,
                severity: Severity.HIGH,
                recommendation:
                    'Review query folding and source-side transformations'
            });
        }

        for (const column of table.columns.values()) {
            if (
                column.dataType === 'string' &&
                column.cardinality > 50000
            ) {
                recommendations.push({
                    table: table.name,
                    column: column.name,
                    severity: Severity.MEDIUM,
                    recommendation:
                        'Investigate high-cardinality text storage'
                });
            }
        }
    }

    for (const relationship of model.relationships) {
        if (relationship.bidirectional) {
            recommendations.push({
                table: relationship.fromTable,
                severity: Severity.MEDIUM,
                recommendation:
                    'Review bidirectional relationship necessity'
            });
        }
    }

    return recommendations;
}


/* ============================================================
   12. BENCHMARKING
   ============================================================ */

async function benchmark(operation, repetitions = 5) {
    requirePositiveInteger(repetitions, 'Repetitions');

    if (repetitions > 1000) {
        throw new ValidationError(
            'Maximum repetitions is 1000'
        );
    }

    const results = [];

    for (let i = 0; i < repetitions; i++) {
        const start = performance.now();

        await operation();

        results.push(performance.now() - start);
    }

    results.sort((a, b) => a - b);

    return {
        runs: repetitions,
        minimumMs: results[0],
        medianMs: results[Math.floor(results.length / 2)],
        maximumMs: results[results.length - 1]
    };
}


/* ============================================================
   13. MAIN EXECUTION
   ============================================================ */

async function main() {

    const model = buildModel();

    const policy = new PerformancePolicy({
        maximumFormulaEngineShare: 0.4,
        maximumSourceLatencyMs: 500,
        maximumVisualLatencyMs: 300
    });

    const monitor = new PerformanceMonitor(policy);

    monitor.on('performanceViolation', event => {
        console.error(
            'PERFORMANCE POLICY VIOLATION:',
            JSON.stringify(event, null, 2)
        );
    });

    monitor.on('queryEvaluated', event => {
        console.log(
            `Evaluated ${event.queryId}: ${event.totalMs} ms`
        );
    });

    const scheduler = new QueryScheduler(2);

    scheduler.on('completed', event => {
        console.log(
            `Completed ${event.queryId} in ${event.durationMs} ms`
        );
    });

    const requests = [
        new QueryRequest({
            id: 'Q-001',
            type: QueryType.AGGREGATION,
            storageEngineMs: 100,
            formulaEngineMs: 50,
            visualRenderMs: 80
        }),
        new QueryRequest({
            id: 'Q-002',
            type: QueryType.DETAIL,
            storageEngineMs: 250,
            formulaEngineMs: 300,
            sourceMs: 700,
            visualRenderMs: 100
        }),
        new QueryRequest({
            id: 'Q-003',
            type: QueryType.TIME_INTELLIGENCE,
            storageEngineMs: 120,
            formulaEngineMs: 220,
            visualRenderMs: 90
        })
    ];

    const executionResults = await Promise.all(
        requests.map(request => {
            monitor.record(request);
            return scheduler.submit(request);
        })
    );

    const modelPolicy = policy.evaluateModel(model);

    const daxAnalysis = DAXCatalog.analyze({
        expression:
            'SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])',
        pattern: 'SUMX',
        iterations: 2000000
    });

    const report = {
        model: model.statistics(),
        modelPolicy,
        recommendations: optimizeModel(model),
        daxAnalysis,
        queryResults: executionResults,
        monitor: monitor.report(),
        scheduler: scheduler.statistics
    };

    await fs.writeFile(
        'powerbi_performance_report.json',
        JSON.stringify(report, null, 2),
        'utf8'
    );

    console.log('\nPOWER BI PERFORMANCE REPORT');
    console.log(JSON.stringify(report, null, 2));
}


/* ============================================================
   14. ERROR HANDLING AND ENTRY POINT
   ============================================================ */

main().catch(error => {
    console.error('Execution failed:', error.message);
    process.exitCode = 1;
});
