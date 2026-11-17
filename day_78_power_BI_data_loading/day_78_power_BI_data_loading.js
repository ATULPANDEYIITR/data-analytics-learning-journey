'use strict';

/*
 * POWER BI DATA LOADING
 *
 * Node.js implementation of a data-source orchestration engine.
 * Demonstrates CSV, JSON, SQLite-independent database adapters,
 * Excel-export ingestion, web APIs, connection management,
 * refresh scheduling, caching, and storage-mode evaluation.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const fs = require('node:fs/promises');
const path = require('node:path');
const https = require('node:https');
const { EventEmitter } = require('node:events');
const { performance } = require('node:perf_hooks');
const { setTimeout: delay } = require('node:timers/promises');


const SourceType = Object.freeze({
    CSV: 'CSV',
    EXCEL_EXPORT: 'EXCEL_EXPORT',
    DATABASE: 'DATABASE',
    JSON: 'JSON',
    WEB: 'WEB'
});

const StorageMode = Object.freeze({
    IMPORT: 'IMPORT',
    DIRECT_QUERY: 'DIRECT_QUERY',
    LIVE_CONNECTION: 'LIVE_CONNECTION'
});

const ConnectionState = Object.freeze({
    CREATED: 'CREATED',
    CONNECTED: 'CONNECTED',
    LOADING: 'LOADING',
    READY: 'READY',
    FAILED: 'FAILED',
    DISABLED: 'DISABLED'
});


// ---------------------------------------------------------
// Custom errors
// ---------------------------------------------------------

class DataLoadingError extends Error {
    constructor(message, code = 'DATA_LOADING_ERROR') {
        super(message);
        this.name = 'DataLoadingError';
        this.code = code;
    }
}

class ValidationError extends DataLoadingError {
    constructor(message) {
        super(message, 'VALIDATION_ERROR');
        this.name = 'ValidationError';
    }
}

class ConnectionError extends DataLoadingError {
    constructor(message) {
        super(message, 'CONNECTION_ERROR');
        this.name = 'ConnectionError';
    }
}


// ---------------------------------------------------------
// CSV parser
// ---------------------------------------------------------

class CSVParser {

    static parse(input, delimiter = ',') {

        if (typeof input !== 'string' || !input.trim()) {
            throw new ValidationError('CSV content is empty.');
        }

        if (delimiter.length !== 1) {
            throw new ValidationError(
                'Delimiter must contain one character.'
            );
        }

        const rows = [];
        let row = [];
        let field = '';
        let quoted = false;

        for (let index = 0; index < input.length; index++) {

            const character = input[index];

            if (quoted) {

                if (character === '"') {

                    if (input[index + 1] === '"') {
                        field += '"';
                        index++;
                    } else {
                        quoted = false;
                    }

                } else {
                    field += character;
                }

            } else if (character === '"') {

                if (field.length !== 0) {
                    throw new ValidationError(
                        'Unexpected quote in CSV field.'
                    );
                }

                quoted = true;

            } else if (character === delimiter) {

                row.push(field);
                field = '';

            } else if (
                character === '\n' ||
                character === '\r'
            ) {

                if (
                    character === '\r' &&
                    input[index + 1] === '\n'
                ) {
                    index++;
                }

                row.push(field);
                rows.push(row);

                row = [];
                field = '';

            } else {
                field += character;
            }
        }

        if (quoted) {
            throw new ValidationError(
                'CSV contains an unclosed quoted field.'
            );
        }

        if (field.length || row.length) {
            row.push(field);
            rows.push(row);
        }

        if (rows.length < 2) {
            throw new ValidationError(
                'CSV requires a header and data rows.'
            );
        }

        const headers = rows.shift().map(
            header => header.trim().toLowerCase()
                .replace(/\s+/g, '_')
        );

        if (
            headers.some(header => !header) ||
            new Set(headers).size !== headers.length
        ) {
            throw new ValidationError(
                'CSV contains empty or duplicate headers.'
            );
        }

        return rows
            .filter(values => values.some(value => value !== ''))
            .map((values, index) => {

                if (values.length !== headers.length) {
                    throw new ValidationError(
                        `Column count mismatch at row ${index + 2}.`
                    );
                }

                return Object.fromEntries(
                    headers.map(
                        (header, position) => [
                            header,
                            values[position]
                        ]
                    )
                );
            });
    }
}


// ---------------------------------------------------------
// Data transformation and validation
// ---------------------------------------------------------

class SalesTransformer {

    static transform(rows) {

        if (!Array.isArray(rows) || rows.length === 0) {
            throw new ValidationError(
                'No records available for transformation.'
            );
        }

        const required = [
            'product',
            'quantity',
            'revenue'
        ];

        const result = [];
        const rejected = [];

        rows.forEach((record, index) => {

            try {

                const normalized = Object.fromEntries(
                    Object.entries(record).map(
                        ([key, value]) => [
                            key.trim().toLowerCase()
                                .replace(/\s+/g, '_'),
                            value
                        ]
                    )
                );

                for (const column of required) {
                    if (!(column in normalized)) {
                        throw new ValidationError(
                            `Missing column: ${column}`
                        );
                    }
                }

                const product = String(
                    normalized.product
                ).trim();

                const quantity = Number(
                    normalized.quantity
                );

                const revenue = Number(
                    normalized.revenue
                );

                if (!product) {
                    throw new ValidationError(
                        'Product name cannot be empty.'
                    );
                }

                if (
                    !Number.isSafeInteger(quantity) ||
                    quantity < 0
                ) {
                    throw new ValidationError(
                        'Quantity must be a non-negative integer.'
                    );
                }

                if (
                    !Number.isFinite(revenue) ||
                    revenue < 0
                ) {
                    throw new ValidationError(
                        'Revenue must be finite and non-negative.'
                    );
                }

                result.push({
                    ...normalized,
                    product,
                    quantity,
                    revenue: Math.round(
                        (revenue + Number.EPSILON) * 100
                    ) / 100
                });

            } catch (error) {

                rejected.push({
                    row: index + 1,
                    reason: error.message
                });
            }
        });

        if (result.length === 0) {
            throw new ValidationError(
                'Every source record failed validation.'
            );
        }

        return {
            rows: result,
            rejected
        };
    }
}


// ---------------------------------------------------------
// Database adapter contract
// ---------------------------------------------------------

class DatabaseAdapter {

    async executeReadOnly(query) {
        throw new DataLoadingError(
            'Database adapter is not implemented.'
        );
    }
}


class InMemoryDatabaseAdapter extends DatabaseAdapter {

    constructor(tables = {}) {
        super();
        this.tables = new Map(
            Object.entries(tables)
        );
    }

    async executeReadOnly(query) {

        const match = query.match(
            /^\s*SELECT\s+\*\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;?\s*$/i
        );

        if (!match) {
            throw new ValidationError(
                'Adapter permits SELECT * FROM table only.'
            );
        }

        const rows = this.tables.get(match[1]);

        if (!rows) {
            throw new ConnectionError(
                'Requested database table does not exist.'
            );
        }

        return rows.map(row => ({ ...row }));
    }
}


// ---------------------------------------------------------
// Secure web source
// ---------------------------------------------------------

class WebSource {

    static async fetchJSON(url, timeout = 10000) {

        const parsed = new URL(url);

        if (parsed.protocol !== 'https:') {
            throw new ValidationError(
                'Only HTTPS web sources are permitted.'
            );
        }

        if (
            parsed.hostname === 'localhost' ||
            parsed.hostname.endsWith('.localhost')
        ) {
            throw new ValidationError(
                'Local web endpoints are not permitted.'
            );
        }

        return new Promise((resolve, reject) => {

            const request = https.get(
                parsed,
                {
                    headers: {
                        Accept: 'application/json'
                    }
                },
                response => {

                    if (
                        response.statusCode < 200 ||
                        response.statusCode >= 300
                    ) {
                        response.resume();

                        reject(
                            new ConnectionError(
                                `HTTP ${response.statusCode}`
                            )
                        );

                        return;
                    }

                    const chunks = [];
                    let size = 0;
                    const maximum = 2_000_000;

                    response.on('data', chunk => {

                        size += chunk.length;

                        if (size > maximum) {
                            request.destroy(
                                new ConnectionError(
                                    'Response size limit exceeded.'
                                )
                            );

                            return;
                        }

                        chunks.push(chunk);
                    });

                    response.on('end', () => {

                        try {

                            const body = Buffer.concat(
                                chunks
                            ).toString('utf8');

                            const parsedBody = JSON.parse(body);

                            resolve(
                                Array.isArray(parsedBody)
                                    ? parsedBody
                                    : parsedBody.data
                            );

                        } catch (error) {
                            reject(
                                new ValidationError(
                                    `Invalid JSON response: ${error.message}`
                                )
                            );
                        }
                    });
                }
            );

            request.setTimeout(timeout, () => {
                request.destroy(
                    new ConnectionError(
                        'Web request timed out.'
                    )
                );
            });

            request.on('error', reject);
        });
    }
}


// ---------------------------------------------------------
// Connection registry
// ---------------------------------------------------------

class ConnectionRegistry {

    constructor() {
        this.connections = new Map();
    }

    register(configuration) {

        const {
            id,
            type,
            location,
            enabled = true
        } = configuration;

        if (!id || !location) {
            throw new ValidationError(
                'Connection ID and location are required.'
            );
        }

        if (!Object.values(SourceType).includes(type)) {
            throw new ValidationError(
                'Unsupported source type.'
            );
        }

        if (this.connections.has(id)) {
            throw new ValidationError(
                `Connection ${id} already exists.`
            );
        }

        this.connections.set(id, {
            ...configuration,
            enabled,
            state: enabled
                ? ConnectionState.CREATED
                : ConnectionState.DISABLED,
            lastRefresh: null
        });
    }

    get(id) {

        const connection = this.connections.get(id);

        if (!connection) {
            throw new ConnectionError(
                `Connection ${id} not found.`
            );
        }

        return connection;
    }

    disable(id) {

        const connection = this.get(id);

        connection.enabled = false;
        connection.state = ConnectionState.DISABLED;
    }
}


// ---------------------------------------------------------
// Data source dispatcher
// ---------------------------------------------------------

class DataSourceDispatcher {

    constructor(registry) {
        this.registry = registry;
    }

    async load(id) {

        const connection = this.registry.get(id);

        if (!connection.enabled) {
            throw new ConnectionError(
                'Connection is disabled.'
            );
        }

        connection.state = ConnectionState.CONNECTED;

        try {

            connection.state = ConnectionState.LOADING;

            let rows;

            switch (connection.type) {

                case SourceType.CSV: {

                    const content = await fs.readFile(
                        connection.location,
                        'utf8'
                    );

                    rows = CSVParser.parse(content);

                    break;
                }

                case SourceType.EXCEL_EXPORT: {

                    // Excel data exported to CSV is accepted here.
                    // XLSX parsing requires a ZIP/XML-capable library.
                    const content = await fs.readFile(
                        connection.location,
                        'utf8'
                    );

                    rows = CSVParser.parse(content);

                    break;
                }

                case SourceType.JSON: {

                    const content = await fs.readFile(
                        connection.location,
                        'utf8'
                    );

                    const data = JSON.parse(content);

                    rows = Array.isArray(data)
                        ? data
                        : data.data;

                    break;
                }

                case SourceType.DATABASE: {

                    if (
                        !(connection.adapter instanceof DatabaseAdapter)
                    ) {
                        throw new ConnectionError(
                            'A valid database adapter is required.'
                        );
                    }

                    rows = await connection.adapter.executeReadOnly(
                        connection.query
                    );

                    break;
                }

                case SourceType.WEB: {

                    rows = await WebSource.fetchJSON(
                        connection.location,
                        connection.timeout || 10000
                    );

                    break;
                }

                default:
                    throw new ValidationError(
                        'Unknown source type.'
                    );
            }

            const transformed = SalesTransformer.transform(rows);

            connection.state = ConnectionState.READY;

            connection.lastRefresh = new Date().toISOString();

            return {
                connectionId: id,
                rows: transformed.rows,
                rejected: transformed.rejected,
                count: transformed.rows.length,
                loadedAt: connection.lastRefresh
            };

        } catch (error) {

            connection.state = ConnectionState.FAILED;

            throw error;
        }
    }
}


// ---------------------------------------------------------
// Semantic model
// ---------------------------------------------------------

class SemanticModel extends EventEmitter {

    constructor() {
        super();

        this.tables = new Map();
        this.refreshHistory = [];
        this.cache = new Map();
    }

    async importTable(name, loadResult) {

        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
            throw new ValidationError(
                'Invalid semantic model table name.'
            );
        }

        const replacement = loadResult.rows.map(
            row => Object.freeze({ ...row })
        );

        // Replace the table only after successful validation.
        this.tables.set(name, replacement);

        this.cache.clear();

        const record = {
            table: name,
            mode: StorageMode.IMPORT,
            rows: replacement.length,
            timestamp: loadResult.loadedAt
        };

        this.refreshHistory.push(record);

        this.emit('tableImported', record);

        return record;
    }

    queryImportedTable(name) {

        const table = this.tables.get(name);

        if (!table) {
            throw new DataLoadingError(
                `Table ${name} is not imported.`
            );
        }

        return table.map(row => ({ ...row }));
    }

    async directQuery(dispatcher, connectionId) {

        // Each call reads the source again.
        const result = await dispatcher.load(connectionId);

        return result.rows;
    }

    liveConnection(externalModel) {

        if (
            !externalModel ||
            externalModel.available !== true
        ) {
            throw new ConnectionError(
                'External semantic model is unavailable.'
            );
        }

        return externalModel;
    }
}


// ---------------------------------------------------------
// Refresh coordinator
// ---------------------------------------------------------

class RefreshCoordinator extends EventEmitter {

    constructor(dispatcher, semanticModel) {
        super();

        this.dispatcher = dispatcher;
        this.semanticModel = semanticModel;
        this.active = new Set();
    }

    async refresh(connectionId, tableName) {

        if (this.active.has(connectionId)) {
            throw new DataLoadingError(
                'Refresh already running for this connection.'
            );
        }

        this.active.add(connectionId);

        const started = performance.now();

        this.emit('refreshStarted', {
            connectionId,
            timestamp: new Date().toISOString()
        });

        try {

            const result = await this.dispatcher.load(
                connectionId
            );

            const record = await this.semanticModel.importTable(
                tableName,
                result
            );

            const report = {
                ...record,
                durationMs: Number(
                    (performance.now() - started).toFixed(2)
                ),
                rejectedRows: result.rejected.length,
                status: 'SUCCESS'
            };

            this.emit('refreshCompleted', report);

            return report;

        } catch (error) {

            const failure = {
                connectionId,
                status: 'FAILED',
                message: error.message
            };

            this.emit('refreshFailed', failure);

            throw error;

        } finally {
            this.active.delete(connectionId);
        }
    }
}


// ---------------------------------------------------------
// Analytics
// ---------------------------------------------------------

class SalesReport {

    static generate(rows) {

        if (!rows.length) {
            throw new ValidationError(
                'Cannot generate an empty report.'
            );
        }

        const summary = rows.reduce(
            (result, row) => {

                result.quantity += row.quantity;
                result.revenue += row.revenue;

                result.byProduct.set(
                    row.product,
                    (
                        result.byProduct.get(row.product) || 0
                    ) + row.revenue
                );

                return result;

            },
            {
                quantity: 0,
                revenue: 0,
                byProduct: new Map()
            }
        );

        return {
            recordCount: rows.length,
            totalQuantity: summary.quantity,
            totalRevenue: Number(
                summary.revenue.toFixed(2)
            ),
            productRevenue: Object.fromEntries(
                summary.byProduct
            )
        };
    }
}


// ---------------------------------------------------------
// Application
// ---------------------------------------------------------

async function main() {

    const directory = path.resolve(
        'powerbi_js_demo'
    );

    await fs.mkdir(directory, {
        recursive: true
    });

    const csvPath = path.join(
        directory,
        'sales.csv'
    );

    const jsonPath = path.join(
        directory,
        'sales.json'
    );

    await fs.writeFile(
        csvPath,
        [
            'product,quantity,revenue',
            'Laptop,5,250000',
            'Monitor,8,120000',
            'Keyboard,20,40000',
            'Mouse,-2,10000'
        ].join('\n'),
        'utf8'
    );

    await fs.writeFile(
        jsonPath,
        JSON.stringify({
            data: [
                {
                    product: 'Tablet',
                    quantity: 4,
                    revenue: 80000
                },
                {
                    product: 'Phone',
                    quantity: 10,
                    revenue: 200000
                }
            ]
        }, null, 2),
        'utf8'
    );

    const registry = new ConnectionRegistry();

    registry.register({
        id: 'csv_sales',
        type: SourceType.CSV,
        location: csvPath
    });

    registry.register({
        id: 'json_sales',
        type: SourceType.JSON,
        location: jsonPath
    });

    registry.register({
        id: 'database_sales',
        type: SourceType.DATABASE,
        location: 'in-memory-database',
        adapter: new InMemoryDatabaseAdapter({
            sales: [
                {
                    product: 'Desktop',
                    quantity: 3,
                    revenue: 180000
                },
                {
                    product: 'Printer',
                    quantity: 2,
                    revenue: 30000
                }
            ]
        }),
        query: 'SELECT * FROM sales'
    });

    const dispatcher = new DataSourceDispatcher(
        registry
    );

    const model = new SemanticModel();

    const coordinator = new RefreshCoordinator(
        dispatcher,
        model
    );

    coordinator.on('refreshCompleted', report => {
        console.log('\nRefresh completed:', report);
    });

    coordinator.on('refreshFailed', error => {
        console.error('\nRefresh failed:', error);
    });

    console.log('\nPOWER BI DATA LOADING ENGINE');

    const sources = [
        ['csv_sales', 'SalesCSV'],
        ['json_sales', 'SalesJSON'],
        ['database_sales', 'SalesDatabase']
    ];

    for (const [connectionId, tableName] of sources) {

        try {

            await coordinator.refresh(
                connectionId,
                tableName
            );

        } catch (error) {

            console.error(
                `${connectionId}: ${error.message}`
            );
        }
    }

    console.log('\nIMPORTED TABLES');

    for (const name of model.tables.keys()) {
        console.log(name);
    }

    const allRows = [
        ...model.queryImportedTable('SalesCSV'),
        ...model.queryImportedTable('SalesJSON'),
        ...model.queryImportedTable('SalesDatabase')
    ];

    console.log('\nSALES REPORT');

    console.log(
        JSON.stringify(
            SalesReport.generate(allRows),
            null,
            2
        )
    );

    console.log('\nDIRECTQUERY-STYLE EXECUTION');

    const directRows = await model.directQuery(
        dispatcher,
        'csv_sales'
    );

    console.log(
        'Fresh source records:',
        directRows.length
    );

    console.log('\nLIVE CONNECTION');

    const externalModel = {
        name: 'CorporateSalesModel',
        available: true
    };

    console.log(
        model.liveConnection(externalModel)
    );

    console.log('\nEXPECTED ERROR HANDLING');

    try {
        await dispatcher.load('unknown_source');
    } catch (error) {
        console.log(error.code, error.message);
    }

    try {
        CSVParser.parse('product,quantity,revenue\n"broken,2,10');
    } catch (error) {
        console.log(error.code, error.message);
    }

    console.log('\nREFRESH HISTORY');

    console.log(
        JSON.stringify(
            model.refreshHistory,
            null,
            2
        )
    );
}


main().catch(error => {

    console.error(
        'Application failed:',
        error.message
    );

    process.exitCode = 1;
});
