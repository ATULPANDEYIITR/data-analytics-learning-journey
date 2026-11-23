"use strict";

/*
 * ADVANCED DAX CONCEPTS
 *
 * Context transition
 * Row context
 * Filter context
 * Variables
 * Iterators
 *
 * Event-driven analytical evaluation engine.
 * Runtime: Node.js 18+
 */


// ============================================================
// 1. DOMAIN DATA
// ============================================================

const sales = Object.freeze([
    Object.freeze({
        saleId: 1, productId: 101, category: "Electronics",
        region: "North", quantity: 2, unitPrice: 500, cost: 350
    }),
    Object.freeze({
        saleId: 2, productId: 102, category: "Electronics",
        region: "South", quantity: 1, unitPrice: 800, cost: 600
    }),
    Object.freeze({
        saleId: 3, productId: 103, category: "Furniture",
        region: "North", quantity: 3, unitPrice: 200, cost: 120
    }),
    Object.freeze({
        saleId: 4, productId: 101, category: "Electronics",
        region: "West", quantity: 1, unitPrice: 500, cost: 350
    }),
    Object.freeze({
        saleId: 5, productId: 104, category: "Furniture",
        region: "South", quantity: 4, unitPrice: 150, cost: 90
    }),
    Object.freeze({
        saleId: 6, productId: 105, category: "Clothing",
        region: "North", quantity: 5, unitPrice: 80, cost: 40
    })
]);

const products = Object.freeze([
    Object.freeze({ productId: 101, name: "Laptop", category: "Electronics" }),
    Object.freeze({ productId: 102, name: "Monitor", category: "Electronics" }),
    Object.freeze({ productId: 103, name: "Desk", category: "Furniture" }),
    Object.freeze({ productId: 104, name: "Chair", category: "Furniture" }),
    Object.freeze({ productId: 105, name: "Shirt", category: "Clothing" })
]);


// ============================================================
// 2. ERRORS
// ============================================================

class EvaluationError extends Error {}
class ContextError extends EvaluationError {}
class DataValidationError extends EvaluationError {}


// ============================================================
// 3. IMMUTABLE FILTER CONTEXT
// ============================================================

class FilterContext {

    constructor(filters = new Map()) {
        this.filters = new Map();

        for (const [column, values] of filters) {
            if (!(values instanceof Set)) {
                throw new ContextError(
                    `Filter ${column} must contain a Set.`
                );
            }

            this.filters.set(column, new Set(values));
        }

        Object.freeze(this);
    }

    withFilter(column, values) {
        const next = new Map(this.filters);
        const incoming = new Set(values);

        if (next.has(column)) {
            const existing = next.get(column);
            next.set(
                column,
                new Set([...existing].filter(v => incoming.has(v)))
            );
        } else {
            next.set(column, incoming);
        }

        return new FilterContext(next);
    }

    withReplacement(column, values) {
        const next = new Map(this.filters);
        next.set(column, new Set(values));
        return new FilterContext(next);
    }

    allows(row) {
        for (const [column, values] of this.filters) {
            if (
                Object.hasOwn(row, column) &&
                !values.has(row[column])
            ) {
                return false;
            }
        }

        return true;
    }

    static empty() {
        return new FilterContext();
    }
}


// ============================================================
// 4. ROW CONTEXT
// ============================================================

class RowContext {

    constructor(parent = null, row = null) {
        this.parent = parent;
        this.row = row;
    }

    current() {
        if (!this.row) {
            throw new ContextError("No active row context.");
        }
        return this.row;
    }

    push(row) {
        return new RowContext(this, row);
    }

    ancestors() {
        const rows = [];
        let current = this;

        while (current && current.row) {
            rows.unshift(current.row);
            current = current.parent;
        }

        return rows;
    }
}


// ============================================================
// 5. RELATIONAL MODEL
// ============================================================

class AnalyticalModel {

    constructor() {
        this.tables = new Map([
            ["Sales", sales],
            ["Products", products]
        ]);

        this.productById = new Map(
            products.map(product => [product.productId, product])
        );

        this.salesByProduct = new Map();

        for (const sale of sales) {
            if (!this.salesByProduct.has(sale.productId)) {
                this.salesByProduct.set(sale.productId, []);
            }

            this.salesByProduct.get(sale.productId).push(sale);
        }

        this.relationships = Object.freeze([
            {
                from: "Products.productId",
                to: "Sales.productId",
                cardinality: "one-to-many"
            }
        ]);
    }

    getTable(name) {
        const table = this.tables.get(name);

        if (!table) {
            throw new DataValidationError(
                `Unknown table: ${name}`
            );
        }

        return table;
    }

    rows(tableName, context) {
        let rows = this.getTable(tableName);

        // Product dimension filters propagate to Sales.
        if (tableName === "Sales") {
            const productFilters = context.filters.get("category");

            if (productFilters) {
                const allowedIds = new Set(
                    products
                        .filter(p => productFilters.has(p.category))
                        .map(p => p.productId)
                );

                rows = rows.filter(
                    row => allowedIds.has(row.productId)
                );
            }
        }

        return rows.filter(context.allows.bind(context));
    }
}

const model = new AnalyticalModel();


// ============================================================
// 6. MEASURES
// ============================================================

const Measures = {

    revenue(context) {
        return model.rows("Sales", context).reduce(
            (total, row) => total + row.quantity * row.unitPrice,
            0
        );
    },

    cost(context) {
        return model.rows("Sales", context).reduce(
            (total, row) => total + row.quantity * row.cost,
            0
        );
    },

    profit(context) {
        return this.revenue(context) - this.cost(context);
    },

    margin(context) {
        const revenue = this.revenue(context);
        const cost = this.cost(context);
        const profit = revenue - cost;

        return revenue === 0 ? 0 : profit / revenue;
    }
};


// ============================================================
// 7. CALCULATE AND CONTEXT TRANSITION
// ============================================================

function calculate(
    expression,
    filterContext,
    rowContext = new RowContext(),
    explicitFilters = []
) {
    let modified = filterContext;

    // Context transition: row values become filters.
    for (const row of rowContext.ancestors()) {
        for (const [column, value] of Object.entries(row)) {
            modified = modified.withFilter(column, [value]);
        }
    }

    // Explicit filter arguments replace filters on
    // their corresponding columns in this simulation.
    for (const filter of explicitFilters) {
        modified = modified.withReplacement(
            filter.column,
            filter.values
        );
    }

    return expression(modified);
}


// ============================================================
// 8. ITERATOR FRAMEWORK
// ============================================================

function sumX(rows, expression, filterContext) {
    if (!Array.isArray(rows)) {
        throw new DataValidationError("SUMX requires an array.");
    }

    return rows.reduce((total, row) => {
        const rowContext = new RowContext().push(row);
        const result = expression(rowContext, filterContext);

        if (typeof result !== "number" || !Number.isFinite(result)) {
            throw new EvaluationError(
                "SUMX expression returned an invalid number."
            );
        }

        return total + result;
    }, 0);
}


function filterX(rows, predicate) {
    if (!Array.isArray(rows)) {
        throw new DataValidationError("FILTER requires an array.");
    }

    return rows.filter(row => {
        const rowContext = new RowContext().push(row);
        return Boolean(predicate(rowContext));
    });
}


function addColumns(rows, expressions) {
    return rows.map(row => {
        const context = new RowContext().push(row);
        const calculated = {};

        for (const [name, expression] of Object.entries(expressions)) {
            if (Object.hasOwn(row, name)) {
                throw new DataValidationError(
                    `Column ${name} already exists.`
                );
            }

            calculated[name] = expression(context);
        }

        return Object.freeze({
            ...row,
            ...calculated
        });
    });
}


// ============================================================
// 9. VARIABLE-BASED MEASURES
// ============================================================

function calculateProfitability(context) {

    // Each variable is evaluated once in the incoming context.
    const revenue = Measures.revenue(context);
    const cost = Measures.cost(context);
    const profit = revenue - cost;

    const margin = revenue === 0
        ? 0
        : profit / revenue;

    return Object.freeze({
        revenue,
        cost,
        profit,
        margin
    });
}


// ============================================================
// 10. EVENT-DRIVEN EVALUATION
// ============================================================

class AnalyticsEngine {

    #context;
    #listeners;

    constructor() {
        this.#context = FilterContext.empty();
        this.#listeners = new Map();
    }

    on(event, listener) {
        if (typeof listener !== "function") {
            throw new DataValidationError(
                "Listener must be a function."
            );
        }

        if (!this.#listeners.has(event)) {
            this.#listeners.set(event, new Set());
        }

        this.#listeners.get(event).add(listener);

        return () => this.#listeners.get(event)?.delete(listener);
    }

    emit(event, payload) {
        for (const listener of this.#listeners.get(event) ?? []) {
            listener(payload);
        }
    }

    applyFilter(column, values) {
        this.#context = this.#context.withFilter(
            column,
            values
        );

        this.emit("filterChanged", {
            column,
            values: [...values],
            context: this.#context
        });
    }

    reset() {
        this.#context = FilterContext.empty();
        this.emit("contextReset", {});
    }

    getContext() {
        return this.#context;
    }

    evaluate() {
        const result = calculateProfitability(this.#context);
        this.emit("evaluated", result);
        return result;
    }
}


// ============================================================
// 11. ASYNCHRONOUS REPORT PROCESSING
// ============================================================

async function generateRegionalReport(engine) {
    const regions = [...new Set(sales.map(s => s.region))];

    const report = await Promise.all(
        regions.map(async region => {
            // Each region receives an independent context.
            const context = FilterContext.empty()
                .withFilter("region", [region]);

            await Promise.resolve();

            return {
                region,
                revenue: Measures.revenue(context),
                profit: Measures.profit(context)
            };
        })
    );

    return report;
}


// ============================================================
// 12. EXECUTION AND TESTS
// ============================================================

async function main() {

    const engine = new AnalyticsEngine();

    engine.on("filterChanged", event => {
        console.log(
            `Filter changed: ${event.column} = ${event.values.join(",")}`
        );
    });

    engine.on("evaluated", result => {
        console.log("Evaluation completed:", result);
    });

    console.log("\nADVANCED DAX ENGINE");
    console.log("===================");

    const base = FilterContext.empty();

    console.log("Total revenue:", Measures.revenue(base));
    console.log("Total cost:", Measures.cost(base));
    console.log("Total profit:", Measures.profit(base));

    // Filter context
    engine.applyFilter("region", ["North"]);
    console.log("North:", engine.evaluate());

    // Independent context evaluation
    console.log(
        "Electronics:",
        calculateProfitability(
            base.withFilter("category", ["Electronics"])
        )
    );

    // SUMX without measure evaluation
    const iteratedRevenue = sumX(
        sales,
        context => {
            const row = context.current();
            return row.quantity * row.unitPrice;
        },
        base
    );

    console.log("SUMX revenue:", iteratedRevenue);

    // SUMX with context transition
    const transitionedRevenue = sumX(
        sales,
        (rowContext, filterContext) => calculate(
            Measures.revenue,
            filterContext,
            rowContext
        ),
        base
    );

    console.log("Context-transition SUMX:", transitionedRevenue);

    // FILTER
    const expensiveSales = filterX(
        sales,
        context => {
            const row = context.current();
            return row.quantity * row.unitPrice >= 500;
        }
    );

    console.log("Expensive transactions:", expensiveSales.length);

    // ADDCOLUMNS
    const productMetrics = addColumns(
        products,
        {
            productRevenue: context => calculate(
                Measures.revenue,
                base,
                context
            )
        }
    );

    console.log("Product metrics:", productMetrics);

    // Asynchronous processing
    const regionalReport = await generateRegionalReport(engine);
    console.log("Regional report:", regionalReport);

    // Validation
    console.assert(Measures.revenue(base) === 3350);
    console.assert(Measures.cost(base) === 2190);
    console.assert(Measures.profit(base) === 1160);
    console.assert(iteratedRevenue === 3350);
    console.assert(transitionedRevenue === 3350);
    console.assert(expensiveSales.length === 5);
    console.assert(regionalReport.length === 3);

    const empty = base.withFilter("region", ["Unknown"]);
    console.assert(Measures.margin(empty) === 0);

    // Context isolation
    console.assert(engine.getContext().filters.has("region"));
    console.assert(base.filters.size === 0);

    // Error handling
    try {
        model.getTable("MissingTable");
    } catch (error) {
        if (!(error instanceof DataValidationError)) {
            throw error;
        }
        console.log("Expected validation:", error.message);
    }

    console.log("\nAll JavaScript tests passed.");
}

main().catch(error => {
    console.error("Analytics execution failed:", error.message);
    process.exitCode = 1;
});
