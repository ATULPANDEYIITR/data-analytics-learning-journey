"use strict";

/*
 * DAX FUNDAMENTALS: EVENT-DRIVEN ANALYTICAL MODEL
 *
 * Concepts:
 * - Measures
 * - Calculated columns
 * - Calculated tables
 * - Filter context
 * - Row context
 * - Context transition
 * - CALCULATE
 * - FILTER
 * - ALL
 * - VALUES
 * - DISTINCTCOUNT
 * - SUMX
 * - Aggregation and policy evaluation
 *
 * This implementation models selected DAX semantics.
 * It is not a replacement for the Power BI DAX engine.
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const assert = require("node:assert/strict");
const fs = require("node:fs/promises");

class DAXError extends Error {
    constructor(message) {
        super(message);
        this.name = "DAXError";
    }
}

class FilterContext {
    constructor(filters = new Map(), rowContext = null) {
        this.filters = new Map();

        for (const [column, values] of filters) {
            this.filters.set(column, new Set(values));
        }

        this.rowContext = rowContext
            ? Object.freeze({ ...rowContext })
            : null;
    }

    withFilter(column, values) {
        const next = new Map(this.filters);
        next.set(column, new Set(values));
        return new FilterContext(next, this.rowContext);
    }

    withoutFilter(column) {
        const next = new Map(this.filters);
        next.delete(column);
        return new FilterContext(next, this.rowContext);
    }

    withRow(row) {
        return new FilterContext(this.filters, row);
    }

    snapshot() {
        return Object.fromEntries(
            [...this.filters.entries()].map(
                ([column, values]) => [
                    column,
                    [...values]
                ]
            )
        );
    }
}

class DAXModel {
    constructor(products, sales) {
        this.products = new Map();
        this.sales = [...sales];

        for (const product of products) {
            if (this.products.has(product.id)) {
                throw new DAXError("Duplicate product ID.");
            }

            if (!Number.isFinite(product.price) || product.price < 0) {
                throw new DAXError("Invalid product price.");
            }

            this.products.set(product.id, Object.freeze({ ...product }));
        }

        this.validateSales();

        this.measureRegistry = new Map([
            ["Total Sales", context => this.totalSales(context)],
            ["Total Cost", context => this.totalCost(context)],
            ["Total Profit", context => this.totalProfit(context)],
            ["Total Quantity", context => this.totalQuantity(context)],
            ["Profit Margin", context => this.profitMargin(context)],
            ["Transaction Count", context => this.transactionCount(context)]
        ]);

        this.calculatedColumns = this.buildCalculatedColumns();
        this.calculatedTables = this.buildCalculatedTables();
    }

    validateSales() {
        const ids = new Set();

        for (const sale of this.sales) {
            if (ids.has(sale.id)) {
                throw new DAXError("Duplicate sale ID.");
            }

            ids.add(sale.id);

            if (!this.products.has(sale.productId)) {
                throw new DAXError(
                    `Unknown product in sale ${sale.id}.`
                );
            }

            if (!Number.isInteger(sale.quantity) || sale.quantity < 0) {
                throw new DAXError("Quantity must be a non-negative integer.");
            }

            if (!Number.isFinite(sale.unitCost) || sale.unitCost < 0) {
                throw new DAXError("Invalid unit cost.");
            }

            if (!/^\d{4}-\d{2}-\d{2}$/.test(sale.date)) {
                throw new DAXError("Invalid sale date.");
            }
        }
    }

    getRows(context = new FilterContext()) {
        return this.sales.filter(sale => {
            const product = this.products.get(sale.productId);

            const values = {
                "Sales.ID": sale.id,
                "Sales.ProductID": sale.productId,
                "Sales.Date": sale.date,
                "Sales.Quantity": sale.quantity,
                "Product.Name": product.name,
                "Product.Category": product.category,
                "Product.Price": product.price
            };

            for (const [column, allowed] of context.filters) {
                if (!allowed.has(values[column])) {
                    return false;
                }
            }

            return true;
        });
    }

    // --------------------------------------------------------
    // Measures
    // --------------------------------------------------------

    totalSales(context) {
        return this.getRows(context).reduce(
            (sum, sale) => {
                const product = this.products.get(sale.productId);
                return sum + product.price * sale.quantity;
            },
            0
        );
    }

    totalCost(context) {
        return this.getRows(context).reduce(
            (sum, sale) => sum + sale.unitCost * sale.quantity,
            0
        );
    }

    totalProfit(context) {
        return this.totalSales(context) - this.totalCost(context);
    }

    totalQuantity(context) {
        return this.getRows(context).reduce(
            (sum, sale) => sum + sale.quantity,
            0
        );
    }

    profitMargin(context) {
        const sales = this.totalSales(context);

        if (sales === 0) {
            return null;
        }

        return this.totalProfit(context) / sales * 100;
    }

    transactionCount(context) {
        return this.getRows(context).length;
    }

    evaluateMeasure(name, context) {
        const measure = this.measureRegistry.get(name);

        if (!measure) {
            throw new DAXError(`Unknown measure: ${name}`);
        }

        return measure(context);
    }

    // --------------------------------------------------------
    // CALCULATE
    // --------------------------------------------------------

    calculate(measure, context, options = {}) {
        let next = new FilterContext(context.filters);

        // ALL removes selected filter context.
        for (const column of options.removeFilters ?? []) {
            next = next.withoutFilter(column);
        }

        // Explicit CALCULATE filters replace filters
        // on the same columns.
        for (const [column, values] of Object.entries(
            options.filters ?? {}
        )) {
            next = next.withFilter(column, values);
        }

        // Context transition converts row values into filters.
        if (context.rowContext) {
            for (const [column, value] of Object.entries(
                context.rowContext
            )) {
                next = next.withFilter(column, [value]);
            }
        }

        return measure(next);
    }

    // --------------------------------------------------------
    // FILTER and SUMX
    // --------------------------------------------------------

    filter(context, predicate) {
        if (typeof predicate !== "function") {
            throw new DAXError("FILTER requires a predicate.");
        }

        return this.getRows(context).filter(sale => {
            return predicate(
                sale,
                this.products.get(sale.productId)
            );
        });
    }

    sumX(rows, expression) {
        if (!Array.isArray(rows)) {
            throw new DAXError("SUMX requires an array of rows.");
        }

        return rows.reduce((sum, row) => {
            const value = expression(row);

            if (!Number.isFinite(value)) {
                throw new DAXError("SUMX expression returned an invalid value.");
            }

            return sum + value;
        }, 0);
    }

    // --------------------------------------------------------
    // Calculated columns
    // --------------------------------------------------------

    buildCalculatedColumns() {
        return this.sales.map(sale => {
            const product = this.products.get(sale.productId);

            return Object.freeze({
                saleId: sale.id,
                revenue: product.price * sale.quantity,
                cost: sale.unitCost * sale.quantity,
                profit: (
                    product.price - sale.unitCost
                ) * sale.quantity,
                profitability: product.price > sale.unitCost * 1.5
                    ? "High"
                    : "Standard"
            });
        });
    }

    // --------------------------------------------------------
    // Calculated tables
    // --------------------------------------------------------

    buildCalculatedTables() {
        const categoryMap = new Map();

        for (const product of this.products.values()) {
            const current = categoryMap.get(product.category) ?? {
                category: product.category,
                productCount: 0
            };

            current.productCount++;
            categoryMap.set(product.category, current);
        }

        return Object.freeze({
            CategorySummary: Object.freeze(
                [...categoryMap.values()].map(Object.freeze)
            ),

            ProductList: Object.freeze(
                [...this.products.values()].map(
                    product => Object.freeze({
                        productId: product.id,
                        name: product.name,
                        category: product.category
                    })
                )
            )
        });
    }

    // --------------------------------------------------------
    // VALUES and DISTINCTCOUNT
    // --------------------------------------------------------

    values(column, context) {
        const result = new Set();

        for (const sale of this.getRows(context)) {
            const product = this.products.get(sale.productId);

            const mapping = {
                "Product.Category": product.category,
                "Product.Name": product.name,
                "Sales.Date": sale.date,
                "Sales.ProductID": sale.productId
            };

            if (!(column in mapping)) {
                throw new DAXError(`Unknown column: ${column}`);
            }

            result.add(mapping[column]);
        }

        return result;
    }

    distinctCount(column, context) {
        return this.values(column, context).size;
    }

    categoryReport() {
        const categories = new Set(
            [...this.products.values()].map(p => p.category)
        );

        return [...categories].sort().map(category => {
            const context = new FilterContext().withFilter(
                "Product.Category",
                [category]
            );

            return {
                category,
                sales: this.totalSales(context),
                cost: this.totalCost(context),
                profit: this.totalProfit(context),
                margin: this.profitMargin(context),
                quantity: this.totalQuantity(context)
            };
        });
    }

    async exportReport(path) {
        const report = {
            generatedAt: new Date().toISOString(),
            categories: this.categoryReport()
        };

        // Exclusive creation prevents accidental overwrite.
        await fs.writeFile(
            path,
            JSON.stringify(report, null, 2),
            {
                encoding: "utf8",
                flag: "wx",
                mode: 0o600
            }
        );

        return report;
    }
}

// ------------------------------------------------------------
// Sample analytical data
// ------------------------------------------------------------

function createModel() {
    const products = [
        { id: 1, name: "Laptop", category: "Electronics", price: 1000 },
        { id: 2, name: "Phone", category: "Electronics", price: 500 },
        { id: 3, name: "Desk", category: "Furniture", price: 300 },
        { id: 4, name: "Chair", category: "Furniture", price: 200 },
        { id: 5, name: "Notebook", category: "Stationery", price: 50 }
    ];

    const sales = [
        { id: 101, productId: 1, date: "2026-01-10", quantity: 2, unitCost: 700 },
        { id: 102, productId: 2, date: "2026-01-11", quantity: 4, unitCost: 300 },
        { id: 103, productId: 3, date: "2026-01-12", quantity: 3, unitCost: 180 },
        { id: 104, productId: 4, date: "2026-01-13", quantity: 5, unitCost: 120 },
        { id: 105, productId: 5, date: "2026-01-14", quantity: 10, unitCost: 20 },
        { id: 106, productId: 1, date: "2026-02-10", quantity: 1, unitCost: 700 },
        { id: 107, productId: 2, date: "2026-02-11", quantity: 2, unitCost: 300 },
        { id: 108, productId: 3, date: "2026-02-12", quantity: 4, unitCost: 180 },
        { id: 109, productId: 4, date: "2026-02-13", quantity: 3, unitCost: 120 },
        { id: 110, productId: 5, date: "2026-02-14", quantity: 5, unitCost: 20 }
    ];

    return new DAXModel(products, sales);
}

// ------------------------------------------------------------
// Validation and execution
// ------------------------------------------------------------

async function main() {
    const model = createModel();
    const all = new FilterContext();

    assert.equal(model.totalSales(all), 4995);
    assert.equal(model.totalCost(all), 2840);
    assert.equal(model.totalProfit(all), 2155);
    assert.equal(model.totalQuantity(all), 39);
    assert.equal(model.transactionCount(all), 10);

    const electronics = all.withFilter(
        "Product.Category",
        ["Electronics"]
    );

    assert.equal(model.totalSales(electronics), 3000);
    assert.equal(model.totalQuantity(electronics), 9);

    const allCategories = model.calculate(
        context => model.totalSales(context),
        electronics,
        {
            removeFilters: ["Product.Category"]
        }
    );

    assert.equal(allCategories, 4995);

    const filteredRows = model.filter(
        all,
        (sale, product) => product.category === "Electronics"
    );

    assert.equal(
        model.sumX(
            filteredRows,
            sale => model.products.get(sale.productId).price * sale.quantity
        ),
        3000
    );

    assert.equal(
        model.distinctCount("Product.Category", all),
        3
    );

    assert.equal(model.calculatedColumns.length, 10);
    assert.equal(model.calculatedTables.ProductList.length, 5);

    // Unknown measures and columns must fail explicitly.
    assert.throws(
        () => model.evaluateMeasure("Unknown", all),
        DAXError
    );

    assert.throws(
        () => model.values("Unknown.Column", all),
        DAXError
    );

    console.log("DAX FUNDAMENTALS");
    console.log("================");

    console.log("\nMEASURES");

    for (const name of model.measureRegistry.keys()) {
        console.log(
            `${name}: ${model.evaluateMeasure(name, all)}`
        );
    }

    console.log("\nCATEGORY REPORT");
    console.table(model.categoryReport());

    console.log("\nCALCULATED COLUMNS");
    console.table(model.calculatedColumns.slice(0, 3));

    console.log("\nCALCULATED TABLES");
    console.log(JSON.stringify(model.calculatedTables, null, 2));

    console.log("\nFILTER CONTEXT");
    console.log(electronics.snapshot());

    console.log("\nALL FILTER REMOVAL");
    console.log(allCategories);

    console.log("\nSUMX");
    console.log(model.sumX(
        model.sales,
        sale => model.products.get(sale.productId).price * sale.quantity
    ));

    console.log("\nALL TESTS PASSED");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
