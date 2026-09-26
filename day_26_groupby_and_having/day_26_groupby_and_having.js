"use strict";

/*
 * GROUP BY & HAVING
 * =================
 *
 * A standalone JavaScript study program covering:
 *
 * - GROUP BY concepts
 * - Aggregate functions
 * - WHERE versus HAVING
 * - Multi-column grouping
 * - Conditional aggregation
 * - NULL behavior
 * - ROLLUP, CUBE, and GROUPING SETS concepts
 * - GROUP BY versus window functions
 * - Validation
 * - Error handling
 * - Edge cases
 * - Performance
 * - Security
 * - A realistic sales analytics case study
 *
 * The program does not require external npm packages.
 *
 * It models relational aggregation with JavaScript arrays and Maps.
 * The same logical operations correspond to SQL queries such as:
 *
 *   SELECT region, COUNT(*)
 *   FROM sales
 *   GROUP BY region;
 *
 *   SELECT region, SUM(netAmount)
 *   FROM sales
 *   GROUP BY region
 *   HAVING SUM(netAmount) > 5000;
 */


// ============================================================================
// 1. DATA MODEL
// ============================================================================

class Sale {
    constructor({
        saleId,
        customer,
        region,
        category,
        product,
        salesperson,
        quantity,
        unitPrice,
        discount,
        month,
        status
    }) {
        this.saleId = saleId;
        this.customer = customer;
        this.region = region;
        this.category = category;
        this.product = product;
        this.salesperson = salesperson;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
        this.discount = discount;
        this.month = month;
        this.status = status;
    }

    get grossAmount() {
        if (this.unitPrice === null || this.unitPrice === undefined) {
            return null;
        }

        return this.quantity * this.unitPrice;
    }

    get netAmount() {
        if (
            this.grossAmount === null ||
            this.discount === null ||
            this.discount === undefined
        ) {
            return null;
        }

        return this.grossAmount * (1 - this.discount);
    }
}


// ============================================================================
// 2. SAMPLE DATA
// ============================================================================

const sales = [
    new Sale({
        saleId: 1,
        customer: "Asha",
        region: "North",
        category: "Electronics",
        product: "Laptop",
        salesperson: "Ravi",
        quantity: 2,
        unitPrice: 800,
        discount: 0.05,
        month: "January",
        status: "Completed"
    }),
    new Sale({
        saleId: 2,
        customer: "Bharat",
        region: "North",
        category: "Electronics",
        product: "Phone",
        salesperson: "Ravi",
        quantity: 5,
        unitPrice: 500,
        discount: 0.10,
        month: "January",
        status: "Completed"
    }),
    new Sale({
        saleId: 3,
        customer: "Chen",
        region: "South",
        category: "Furniture",
        product: "Chair",
        salesperson: "Meera",
        quantity: 10,
        unitPrice: 75,
        discount: 0,
        month: "January",
        status: "Completed"
    }),
    new Sale({
        saleId: 4,
        customer: "Divya",
        region: "South",
        category: "Electronics",
        product: "Tablet",
        salesperson: "Meera",
        quantity: 3,
        unitPrice: 300,
        discount: 0.05,
        month: "January",
        status: "Completed"
    }),
    new Sale({
        saleId: 5,
        customer: "Eshan",
        region: "East",
        category: "Furniture",
        product: "Desk",
        salesperson: "Arjun",
        quantity: 4,
        unitPrice: 250,
        discount: 0.08,
        month: "February",
        status: "Completed"
    }),
    new Sale({
        saleId: 6,
        customer: "Fatima",
        region: "East",
        category: "Electronics",
        product: "Laptop",
        salesperson: "Arjun",
        quantity: 1,
        unitPrice: 900,
        discount: 0.10,
        month: "February",
        status: "Completed"
    }),
    new Sale({
        saleId: 7,
        customer: "Gopal",
        region: "West",
        category: "Office",
        product: "Printer",
        salesperson: "Kiran",
        quantity: 6,
        unitPrice: 200,
        discount: 0.05,
        month: "February",
        status: "Completed"
    }),
    new Sale({
        saleId: 8,
        customer: "Hina",
        region: "West",
        category: "Office",
        product: "Chair",
        salesperson: "Kiran",
        quantity: 15,
        unitPrice: 70,
        discount: 0,
        month: "February",
        status: "Completed"
    }),
    new Sale({
        saleId: 9,
        customer: "Ishaan",
        region: "North",
        category: "Furniture",
        product: "Desk",
        salesperson: "Ravi",
        quantity: 2,
        unitPrice: 275,
        discount: 0.05,
        month: "March",
        status: "Completed"
    }),
    new Sale({
        saleId: 10,
        customer: "Jaya",
        region: "South",
        category: "Office",
        product: "Printer",
        salesperson: "Meera",
        quantity: 2,
        unitPrice: 220,
        discount: 0,
        month: "March",
        status: "Completed"
    }),
    new Sale({
        saleId: 11,
        customer: "Kabir",
        region: "East",
        category: "Electronics",
        product: "Phone",
        salesperson: "Arjun",
        quantity: 8,
        unitPrice: 450,
        discount: 0.12,
        month: "March",
        status: "Completed"
    }),
    new Sale({
        saleId: 12,
        customer: "Leela",
        region: "West",
        category: "Furniture",
        product: "Desk",
        salesperson: "Kiran",
        quantity: 3,
        unitPrice: 260,
        discount: 0.05,
        month: "March",
        status: "Completed"
    }),
    new Sale({
        saleId: 13,
        customer: "Mohan",
        region: "North",
        category: "Electronics",
        product: "Laptop",
        salesperson: "Ravi",
        quantity: 1,
        unitPrice: 850,
        discount: 0,
        month: "April",
        status: "Cancelled"
    }),
    new Sale({
        saleId: 14,
        customer: "Nisha",
        region: "South",
        category: "Furniture",
        product: "Chair",
        salesperson: "Meera",
        quantity: 20,
        unitPrice: 65,
        discount: 0.03,
        month: "April",
        status: "Completed"
    }),
    new Sale({
        saleId: 15,
        customer: "Om",
        region: "East",
        category: "Office",
        product: "Printer",
        salesperson: "Arjun",
        quantity: 5,
        unitPrice: 210,
        discount: 0.05,
        month: "April",
        status: "Completed"
    }),
    new Sale({
        saleId: 16,
        customer: "Pooja",
        region: "West",
        category: "Electronics",
        product: "Tablet",
        salesperson: "Kiran",
        quantity: 4,
        unitPrice: 320,
        discount: 0.07,
        month: "April",
        status: "Completed"
    })
];


// ============================================================================
// 3. AGGREGATE FUNCTIONS
// ============================================================================

function countRows(rows) {
    return rows.length;
}


// SQL COUNT(expression) ignores NULL.
function countValues(values) {
    return values.filter(value => value !== null && value !== undefined).length;
}


function sumValues(values) {
    const nonNull = values.filter(
        value => value !== null && value !== undefined
    );

    if (nonNull.length === 0) {
        return null;
    }

    return nonNull.reduce((total, value) => total + Number(value), 0);
}


function averageValues(values) {
    const nonNull = values.filter(
        value => value !== null && value !== undefined
    );

    if (nonNull.length === 0) {
        return null;
    }

    return sumValues(nonNull) / nonNull.length;
}


function minimumValue(values) {
    const nonNull = values.filter(
        value => value !== null && value !== undefined
    );

    return nonNull.length === 0 ? null : Math.min(...nonNull);
}


function maximumValue(values) {
    const nonNull = values.filter(
        value => value !== null && value !== undefined
    );

    return nonNull.length === 0 ? null : Math.max(...nonNull);
}


// ============================================================================
// 4. GENERIC GROUP BY
// ============================================================================

function groupBy(rows, keyFunction) {
    const groups = new Map();

    for (const row of rows) {
        const key = keyFunction(row);

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(row);
    }

    return groups;
}


// JavaScript object keys cannot directly represent SQL-style tuple keys.
// JSON.stringify gives us a deterministic composite-key representation.
function compositeKey(values) {
    return JSON.stringify(values);
}


function groupByMultiple(rows, keyFunctions) {
    const groups = new Map();

    for (const row of rows) {
        const dimensions = keyFunctions.map(fn => fn(row));
        const key = compositeKey(dimensions);

        if (!groups.has(key)) {
            groups.set(key, {
                dimensions,
                rows: []
            });
        }

        groups.get(key).rows.push(row);
    }

    return groups;
}


// ============================================================================
// 5. HAVING IMPLEMENTATION
// ============================================================================

function having(groups, predicate) {
    const filtered = new Map();

    for (const [key, rows] of groups.entries()) {
        if (predicate(key, rows)) {
            filtered.set(key, rows);
        }
    }

    return filtered;
}


// ============================================================================
// 6. BASIC GROUP BY
// ============================================================================

function demonstrateBasicGroupBy() {
    console.log("\n" + "=".repeat(80));
    console.log("1. BASIC GROUP BY");
    console.log("=".repeat(80));

    const byRegion = groupBy(sales, sale => sale.region);

    for (const [region, rows] of byRegion.entries()) {
        console.log(region, countRows(rows));
    }

    /*
     * SQL:
     *
     * SELECT region, COUNT(*)
     * FROM sales
     * GROUP BY region;
     */
}


// ============================================================================
// 7. MULTIPLE AGGREGATES
// ============================================================================

function demonstrateMultipleAggregates() {
    console.log("\n" + "=".repeat(80));
    console.log("2. MULTIPLE AGGREGATES");
    console.log("=".repeat(80));

    const groups = groupBy(sales, sale => sale.region);

    for (const [region, rows] of groups.entries()) {
        const quantities = rows.map(row => row.quantity);
        const revenues = rows.map(row => row.netAmount);

        console.log({
            region,
            count: countRows(rows),
            quantity: sumValues(quantities),
            revenue: sumValues(revenues),
            averageRevenue: averageValues(revenues),
            minimumRevenue: minimumValue(revenues),
            maximumRevenue: maximumValue(revenues)
        });
    }

    /*
     * SQL:
     *
     * SELECT
     *     region,
     *     COUNT(*) AS sale_count,
     *     SUM(quantity) AS total_quantity,
     *     SUM(net_amount) AS revenue,
     *     AVG(net_amount) AS average_revenue,
     *     MIN(net_amount) AS minimum_revenue,
     *     MAX(net_amount) AS maximum_revenue
     * FROM sales
     * GROUP BY region;
     */
}


// ============================================================================
// 8. WHERE BEFORE GROUP BY
// ============================================================================

function demonstrateWhereBeforeGroupBy() {
    console.log("\n" + "=".repeat(80));
    console.log("3. WHERE BEFORE GROUP BY");
    console.log("=".repeat(80));

    // Row-level filtering occurs before the grouping operation.
    const completedSales = sales.filter(
        sale => sale.status === "Completed"
    );

    const groups = groupBy(
        completedSales,
        sale => sale.region
    );

    for (const [region, rows] of groups.entries()) {
        console.log(
            region,
            sumValues(rows.map(row => row.netAmount))
        );
    }

    /*
     * SQL:
     *
     * SELECT region, SUM(net_amount)
     * FROM sales
     * WHERE status = 'Completed'
     * GROUP BY region;
     */
}


// ============================================================================
// 9. HAVING
// ============================================================================

function demonstrateHaving() {
    console.log("\n" + "=".repeat(80));
    console.log("4. HAVING");
    console.log("=".repeat(80));

    const groups = groupBy(sales, sale => sale.region);

    const largeGroups = having(
        groups,
        (region, rows) => rows.length >= 4
    );

    console.log("Regions with at least four rows:");

    for (const [region, rows] of largeGroups.entries()) {
        console.log(region, rows.length);
    }

    const highRevenueGroups = having(
        groups,
        (region, rows) => {
            const revenue = sumValues(
                rows.map(row => row.netAmount)
            ) ?? 0;

            return revenue >= 5000;
        }
    );

    console.log("\nRegions with revenue >= 5000:");

    for (const [region, rows] of highRevenueGroups.entries()) {
        console.log(
            region,
            sumValues(rows.map(row => row.netAmount))
        );
    }

    /*
     * SQL:
     *
     * SELECT region, COUNT(*)
     * FROM sales
     * GROUP BY region
     * HAVING COUNT(*) >= 4;
     *
     * SELECT region, SUM(net_amount)
     * FROM sales
     * GROUP BY region
     * HAVING SUM(net_amount) >= 5000;
     */
}


// ============================================================================
// 10. WHERE VERSUS HAVING
// ============================================================================

function demonstrateWhereVsHaving() {
    console.log("\n" + "=".repeat(80));
    console.log("5. WHERE VERSUS HAVING");
    console.log("=".repeat(80));

    /*
     * WHERE:
     *   Works with individual rows.
     *
     * HAVING:
     *   Works with groups after aggregation.
     */

    const completed = sales.filter(
        sale => sale.status === "Completed"
    );

    const groups = groupBy(
        completed,
        sale => sale.region
    );

    const result = having(
        groups,
        (region, rows) => {
            const revenue = sumValues(
                rows.map(row => row.netAmount)
            ) ?? 0;

            return revenue > 3000;
        }
    );

    for (const [region, rows] of result.entries()) {
        console.log(
            region,
            sumValues(rows.map(row => row.netAmount))
        );
    }

    /*
     * SQL:
     *
     * SELECT region, SUM(net_amount)
     * FROM sales
     * WHERE status = 'Completed'
     * GROUP BY region
     * HAVING SUM(net_amount) > 3000;
     *
     * Incorrect:
     *
     * WHERE SUM(net_amount) > 3000
     *
     * The SUM belongs to the group-level stage.
     */
}


// ============================================================================
// 11. MULTI-COLUMN GROUPING
// ============================================================================

function demonstrateMultiColumnGrouping() {
    console.log("\n" + "=".repeat(80));
    console.log("6. MULTI-COLUMN GROUPING");
    console.log("=".repeat(80));

    const groups = groupByMultiple(
        sales,
        [
            sale => sale.region,
            sale => sale.category
        ]
    );

    for (const group of groups.values()) {
        const revenue = sumValues(
            group.rows.map(row => row.netAmount)
        );

        console.log({
            region: group.dimensions[0],
            category: group.dimensions[1],
            count: group.rows.length,
            revenue
        });
    }

    /*
     * SQL:
     *
     * SELECT region, category, COUNT(*), SUM(net_amount)
     * FROM sales
     * GROUP BY region, category;
     *
     * The group key is the complete combination:
     *
     *   (region, category)
     */
}


// ============================================================================
// 12. CONDITIONAL AGGREGATION
// ============================================================================

function demonstrateConditionalAggregation() {
    console.log("\n" + "=".repeat(80));
    console.log("7. CONDITIONAL AGGREGATION");
    console.log("=".repeat(80));

    const groups = groupBy(sales, sale => sale.region);

    for (const [region, rows] of groups.entries()) {
        const completedCount = rows.filter(
            row => row.status === "Completed"
        ).length;

        const cancelledCount = rows.filter(
            row => row.status === "Cancelled"
        ).length;

        const electronicsRevenue = sumValues(
            rows
                .filter(row => row.category === "Electronics")
                .map(row => row.netAmount)
        );

        console.log({
            region,
            completedCount,
            cancelledCount,
            electronicsRevenue
        });
    }

    /*
     * SQL:
     *
     * SELECT
     *     region,
     *     SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END),
     *     SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END)
     * FROM sales
     * GROUP BY region;
     */
}


// ============================================================================
// 13. DISTINCT VERSUS GROUP BY
// ============================================================================

function demonstrateDistinctVsGroupBy() {
    console.log("\n" + "=".repeat(80));
    console.log("8. DISTINCT VERSUS GROUP BY");
    console.log("=".repeat(80));

    const distinctRegions = [
        ...new Set(sales.map(sale => sale.region))
    ];

    const groupedRegions = [
        ...groupBy(sales, sale => sale.region).keys()
    ];

    console.log("DISTINCT-style result:", distinctRegions);
    console.log("GROUP BY keys:", groupedRegions);

    /*
     * SELECT DISTINCT region FROM sales;
     *
     * and
     *
     * SELECT region FROM sales GROUP BY region;
     *
     * may produce equivalent region lists.
     *
     * GROUP BY becomes useful when aggregate calculations are needed.
     */
}


// ============================================================================
// 14. NULL BEHAVIOR
// ============================================================================

function demonstrateNullBehavior() {
    console.log("\n" + "=".repeat(80));
    console.log("9. NULL BEHAVIOR");
    console.log("=".repeat(80));

    const values = [100, null, 200, null];

    console.log("COUNT(*) equivalent:", values.length);
    console.log("COUNT(value):", countValues(values));
    console.log("SUM(value):", sumValues(values));
    console.log("AVG(value):", averageValues(values));

    /*
     * JavaScript uses null and undefined differently from SQL NULL,
     * so the aggregate functions explicitly treat both as missing values.
     *
     * SQL:
     *
     * COUNT(*)       -> counts rows
     * COUNT(column) -> ignores NULL
     * SUM(column)   -> ignores NULL
     * AVG(column)   -> ignores NULL
     */
}


// ============================================================================
// 15. ROLLUP-STYLE AGGREGATION
// ============================================================================

function rollupRegionCategory(rows) {
    const results = [];

    const detailGroups = groupByMultiple(
        rows,
        [
            sale => sale.region,
            sale => sale.category
        ]
    );

    for (const group of detailGroups.values()) {
        results.push({
            region: group.dimensions[0],
            category: group.dimensions[1],
            revenue: sumValues(
                group.rows.map(row => row.netAmount)
            ),
            level: "detail"
        });
    }

    const regionGroups = groupBy(
        rows,
        sale => sale.region
    );

    for (const [region, groupedRows] of regionGroups.entries()) {
        results.push({
            region,
            category: null,
            revenue: sumValues(
                groupedRows.map(row => row.netAmount)
            ),
            level: "region subtotal"
        });
    }

    results.push({
        region: null,
        category: null,
        revenue: sumValues(rows.map(row => row.netAmount)),
        level: "grand total"
    });

    return results;
}


function demonstrateRollup() {
    console.log("\n" + "=".repeat(80));
    console.log("10. ROLLUP-STYLE AGGREGATION");
    console.log("=".repeat(80));

    for (const row of rollupRegionCategory(sales)) {
        console.log(row);
    }

    /*
     * SQL:
     *
     * GROUP BY ROLLUP(region, category)
     *
     * Conceptually produces:
     *
     *   region + category
     *   region subtotal
     *   grand total
     */
}


// ============================================================================
// 16. CUBE-STYLE AGGREGATION
// ============================================================================

function cubeRegionCategory(rows) {
    const results = [];

    const combinations = [
        { region: true, category: true },
        { region: true, category: false },
        { region: false, category: true },
        { region: false, category: false }
    ];

    for (const combination of combinations) {
        const groups = new Map();

        for (const sale of rows) {
            const region = combination.region ? sale.region : null;
            const category = combination.category ? sale.category : null;
            const key = compositeKey([region, category]);

            if (!groups.has(key)) {
                groups.set(key, []);
            }

            groups.get(key).push(sale);
        }

        for (const [key, groupedRows] of groups.entries()) {
            const [region, category] = JSON.parse(key);

            results.push({
                region,
                category,
                revenue: sumValues(
                    groupedRows.map(row => row.netAmount)
                )
            });
        }
    }

    return results;
}


function demonstrateCube() {
    console.log("\n" + "=".repeat(80));
    console.log("11. CUBE-STYLE AGGREGATION");
    console.log("=".repeat(80));

    for (const row of cubeRegionCategory(sales)) {
        console.log(row);
    }

    /*
     * CUBE(region, category) produces:
     *
     *   region + category
     *   region
     *   category
     *   grand total
     *
     * With n dimensions, the number of grouping combinations can reach 2^n.
     */
}


// ============================================================================
// 17. GROUPING SETS
// ============================================================================

function groupingSetsLike(rows) {
    const result = {
        region: {},
        category: {},
        grandTotal: null
    };

    const regionGroups = groupBy(
        rows,
        sale => sale.region
    );

    for (const [region, groupedRows] of regionGroups.entries()) {
        result.region[region] = sumValues(
            groupedRows.map(row => row.netAmount)
        );
    }

    const categoryGroups = groupBy(
        rows,
        sale => sale.category
    );

    for (const [category, groupedRows] of categoryGroups.entries()) {
        result.category[category] = sumValues(
            groupedRows.map(row => row.netAmount)
        );
    }

    result.grandTotal = sumValues(
        rows.map(row => row.netAmount)
    );

    return result;
}


function demonstrateGroupingSets() {
    console.log("\n" + "=".repeat(80));
    console.log("12. GROUPING SETS");
    console.log("=".repeat(80));

    console.dir(groupingSetsLike(sales), {
        depth: null
    });

    /*
     * SQL:
     *
     * GROUP BY GROUPING SETS (
     *     (region),
     *     (category),
     *     ()
     * )
     *
     * This asks for multiple aggregation levels in one conceptual query.
     */
}


// ============================================================================
// 18. GROUP BY VERSUS WINDOW FUNCTIONS
// ============================================================================

function demonstrateGroupByVsWindow() {
    console.log("\n" + "=".repeat(80));
    console.log("13. GROUP BY VERSUS WINDOW FUNCTIONS");
    console.log("=".repeat(80));

    const groups = groupBy(
        sales,
        sale => sale.region
    );

    const totals = new Map();

    for (const [region, rows] of groups.entries()) {
        totals.set(
            region,
            sumValues(rows.map(row => row.netAmount))
        );
    }

    console.log("GROUP BY-like output:");

    for (const [region, total] of totals.entries()) {
        console.log(region, total);
    }

    console.log("\nWindow-style output:");

    for (const sale of sales.slice(0, 6)) {
        console.log({
            saleId: sale.saleId,
            region: sale.region,
            saleRevenue: sale.netAmount,
            regionRevenue: totals.get(sale.region)
        });
    }

    /*
     * GROUP BY collapses rows.
     *
     * A SQL window expression such as:
     *
     * SUM(net_amount) OVER (PARTITION BY region)
     *
     * preserves each sale while adding the regional total.
     */
}


// ============================================================================
// 19. ADVANCED HAVING
// ============================================================================

function demonstrateAdvancedHaving() {
    console.log("\n" + "=".repeat(80));
    console.log("14. ADVANCED HAVING CONDITIONS");
    console.log("=".repeat(80));

    const groups = groupBy(
        sales,
        sale => sale.salesperson
    );

    const selected = having(
        groups,
        (salesperson, rows) => {
            const revenue = sumValues(
                rows.map(row => row.netAmount)
            ) ?? 0;

            const averageQuantity = averageValues(
                rows.map(row => row.quantity)
            ) ?? 0;

            return (
                rows.length >= 3 &&
                revenue >= 3000 &&
                averageQuantity >= 3
            );
        }
    );

    for (const [salesperson, rows] of selected.entries()) {
        console.log({
            salesperson,
            transactionCount: rows.length,
            revenue: sumValues(rows.map(row => row.netAmount)),
            averageQuantity: averageValues(
                rows.map(row => row.quantity)
            )
        });
    }
}


// ============================================================================
// 20. NORMALIZATION
// ============================================================================

function normalizeRegion(region) {
    if (region === null || region === undefined) {
        return "UNKNOWN";
    }

    const normalized = String(region)
        .trim()
        .replace(/\s+/g, " ")
        .toUpperCase();

    return normalized || "UNKNOWN";
}


function demonstrateNormalization() {
    console.log("\n" + "=".repeat(80));
    console.log("15. NORMALIZATION BEFORE GROUPING");
    console.log("=".repeat(80));

    const messyRegions = [
        "North",
        " north ",
        "NORTH",
        "South",
        " south",
        null,
        ""
    ];

    const groups = groupBy(
        messyRegions,
        normalizeRegion
    );

    for (const [region, rows] of groups.entries()) {
        console.log(region, rows.length);
    }

    /*
     * SQL systems may use expressions such as:
     *
     * GROUP BY UPPER(TRIM(region))
     *
     * Such expressions can affect index usage, depending on the database.
     */
}


// ============================================================================
// 21. VALIDATION
// ============================================================================

function validateSale(sale) {
    const errors = [];

    if (!Number.isInteger(sale.saleId) || sale.saleId <= 0) {
        errors.push("saleId must be a positive integer");
    }

    if (
        typeof sale.customer !== "string" ||
        sale.customer.trim() === ""
    ) {
        errors.push("customer must not be empty");
    }

    if (!Number.isFinite(sale.quantity) || sale.quantity < 0) {
        errors.push("quantity must be a non-negative number");
    }

    if (
        sale.unitPrice !== null &&
        (!Number.isFinite(sale.unitPrice) || sale.unitPrice < 0)
    ) {
        errors.push("unitPrice must be non-negative or null");
    }

    if (
        sale.discount !== null &&
        (
            !Number.isFinite(sale.discount) ||
            sale.discount < 0 ||
            sale.discount > 1
        )
    ) {
        errors.push("discount must be between 0 and 1");
    }

    if (!["Completed", "Cancelled"].includes(sale.status)) {
        errors.push("status is invalid");
    }

    return errors;
}


function demonstrateValidation() {
    console.log("\n" + "=".repeat(80));
    console.log("16. VALIDATION");
    console.log("=".repeat(80));

    const invalidSale = new Sale({
        saleId: -1,
        customer: "",
        region: "North",
        category: "Electronics",
        product: "Phone",
        salesperson: "Ravi",
        quantity: -5,
        unitPrice: -50,
        discount: 1.5,
        month: "May",
        status: "Unknown"
    });

    const errors = validateSale(invalidSale);

    for (const error of errors) {
        console.log("ERROR:", error);
    }
}


// ============================================================================
// 22. REALISTIC SALES REPORT
// ============================================================================

function salesAnalyticsReport(rows) {
    // WHERE status = 'Completed'
    const completed = rows.filter(
        sale => sale.status === "Completed"
    );

    // GROUP BY region, category
    const groups = groupByMultiple(
        completed,
        [
            sale => sale.region,
            sale => sale.category
        ]
    );

    const report = [];

    for (const group of groups.values()) {
        // HAVING COUNT(*) >= 2
        if (group.rows.length < 2) {
            continue;
        }

        const revenue = sumValues(
            group.rows.map(row => row.netAmount)
        ) ?? 0;

        report.push({
            region: group.dimensions[0],
            category: group.dimensions[1],
            transactions: group.rows.length,
            units: sumValues(
                group.rows.map(row => row.quantity)
            ) ?? 0,
            revenue,
            averageTransaction:
                revenue / group.rows.length
        });
    }

    // ORDER BY revenue DESC
    report.sort(
        (left, right) => right.revenue - left.revenue
    );

    return report;
}


function demonstrateSalesReport() {
    console.log("\n" + "=".repeat(80));
    console.log("17. REALISTIC SALES ANALYTICS REPORT");
    console.log("=".repeat(80));

    const report = salesAnalyticsReport(sales);

    console.table(report);

    /*
     * SQL equivalent:
     *
     * SELECT
     *     region,
     *     category,
     *     COUNT(*) AS transactions,
     *     SUM(quantity) AS units,
     *     SUM(net_amount) AS revenue,
     *     AVG(net_amount) AS average_transaction
     * FROM sales
     * WHERE status = 'Completed'
     * GROUP BY region, category
     * HAVING COUNT(*) >= 2
     * ORDER BY revenue DESC;
     */
}


// ============================================================================
// 23. COMMON MISTAKES
// ============================================================================

function demonstrateCommonMistakes() {
    console.log("\n" + "=".repeat(80));
    console.log("18. COMMON MISTAKES");
    console.log("=".repeat(80));

    console.log(`
1. Using WHERE with SUM(), COUNT(), or AVG() when the condition is group-level.

2. Selecting a column that is neither grouped nor aggregated.

3. Forgetting that GROUP BY changes result granularity.

4. Confusing COUNT(*) with COUNT(column).

5. Treating NULL as zero without an explicit business rule.

6. Grouping on inconsistent text values.

7. Grouping by too many columns and creating unnecessarily small groups.

8. Grouping by too few columns and losing an important analytical dimension.

9. Accidentally multiplying rows through one-to-many joins before aggregation.

10. Assuming GROUP BY and window functions have the same output shape.

11. Rounding values before aggregation when the business rule requires
    aggregation first and rounding afterward.

12. Ignoring the database's exact SQL dialect for ROLLUP, CUBE,
    GROUPING SETS, FILTER, and related features.
    `);
}


// ============================================================================
// 24. EDGE CASES
// ============================================================================

function demonstrateEdgeCases() {
    console.log("\n" + "=".repeat(80));
    console.log("19. EDGE CASES");
    console.log("=".repeat(80));

    const empty = [];

    console.log("Empty groups:", groupBy(empty, row => row));
    console.log("Empty COUNT:", countRows(empty));
    console.log("Empty SUM:", sumValues(empty));
    console.log("Empty AVG:", averageValues(empty));

    const nullValues = [null, null];

    console.log("All NULL COUNT(value):", countValues(nullValues));
    console.log("All NULL SUM:", sumValues(nullValues));
    console.log("All NULL AVG:", averageValues(nullValues));

    /*
     * Important edge cases:
     *
     * - empty input
     * - all NULL values
     * - partially NULL values
     * - NULL grouping keys
     * - duplicate rows
     * - zero-valued measures
     * - negative values where permitted
     * - very large groups
     * - high-cardinality group keys
     */
}


// ============================================================================
// 25. PERFORMANCE DISCUSSION
// ============================================================================

function demonstratePerformanceConsiderations() {
    console.log("\n" + "=".repeat(80));
    console.log("20. PERFORMANCE CONSIDERATIONS");
    console.log("=".repeat(80));

    console.log(`
A JavaScript Map-based grouping operation is generally approximately O(n)
for n rows when key lookup is effectively constant time.

Memory usage can approach O(n) because the implementation stores grouped rows.

Database engines may use:

- Hash aggregation
- Sort-based aggregation
- Partial aggregation
- Parallel aggregation
- Pre-aggregation
- Materialized views

Practical SQL considerations:

- Use WHERE to eliminate unnecessary rows before grouping.
- Select only required columns.
- Avoid unnecessarily high-cardinality grouping keys.
- Review execution plans for expensive reports.
- Use appropriate indexes for selective filtering.
- Be aware that expressions around columns may affect index usage.
- Consider summary tables or materialized views for repeated reporting.

Logical SQL processing order is not the same as physical execution.
The optimizer can transform a query while preserving its semantics.
    `);
}


// ============================================================================
// 26. SECURITY
// ============================================================================

function demonstrateSecurityConsiderations() {
    console.log("\n" + "=".repeat(80));
    console.log("21. SECURITY CONSIDERATIONS");
    console.log("=".repeat(80));

    console.log(`
GROUP BY itself is not SQL injection.

The risk appears when an application constructs SQL using untrusted input.

For values:
- use parameterized queries.

For identifiers such as selectable grouping columns:
- use a strict whitelist.

Do not assume that a parameter placeholder can safely represent arbitrary
SQL identifiers.

Aggregation can also expose sensitive information. A group containing one
person can effectively reveal individual-level information.

Possible controls include:
- authorization
- minimum group-size policies
- aggregation thresholds
- masking
- carefully designed reporting permissions
    `);
}


// ============================================================================
// 27. TESTING
// ============================================================================

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(
            `${message}\nExpected: ${expected}\nActual: ${actual}`
        );
    }
}


function runTests() {
    console.log("\n" + "=".repeat(80));
    console.log("22. TESTS");
    console.log("=".repeat(80));

    assertEqual(
        countRows([1, 2, 3]),
        3,
        "COUNT(*) should count rows"
    );

    assertEqual(
        countValues([1, null, 2, undefined]),
        2,
        "COUNT(column) should ignore missing values"
    );

    assertEqual(
        sumValues([10, null, 20]),
        30,
        "SUM should ignore null"
    );

    assertEqual(
        averageValues([10, null, 20]),
        15,
        "AVG should ignore null"
    );

    const regions = groupBy(
        sales,
        sale => sale.region
    );

    assertEqual(
        regions.size,
        4,
        "Expected four regions"
    );

    const report = salesAnalyticsReport(sales);

    if (!report.every(
        item => item.transactions >= 2
    )) {
        throw new Error(
            "HAVING transaction threshold failed"
        );
    }

    for (let index = 1; index < report.length; index += 1) {
        if (
            report[index - 1].revenue <
            report[index].revenue
        ) {
            throw new Error(
                "Report is not sorted by revenue descending"
            );
        }
    }

    console.log("All tests passed.");
}


// ============================================================================
// 28. SQL REFERENCE
// ============================================================================

function printSqlReference() {
    console.log("\n" + "=".repeat(80));
    console.log("23. SQL REFERENCE");
    console.log("=".repeat(80));

    console.log(`
Basic GROUP BY:
SELECT region, COUNT(*)
FROM sales
GROUP BY region;

Multiple aggregates:
SELECT
    region,
    COUNT(*),
    SUM(net_amount),
    AVG(net_amount)
FROM sales
GROUP BY region;

WHERE before grouping:
SELECT region, SUM(net_amount)
FROM sales
WHERE status = 'Completed'
GROUP BY region;

HAVING after grouping:
SELECT region, SUM(net_amount)
FROM sales
GROUP BY region
HAVING SUM(net_amount) > 5000;

Multidimensional grouping:
SELECT region, category, SUM(net_amount)
FROM sales
GROUP BY region, category;

ROLLUP:
GROUP BY ROLLUP(region, category);

CUBE:
GROUP BY CUBE(region, category);

GROUPING SETS:
GROUP BY GROUPING SETS (
    (region),
    (category),
    ()
);
    `);
}


// ============================================================================
// 29. MAIN
// ============================================================================

function main() {
    console.log("GROUP BY & HAVING - JAVASCRIPT STUDY PROGRAM");

    demonstrateBasicGroupBy();
    demonstrateMultipleAggregates();
    demonstrateWhereBeforeGroupBy();
    demonstrateHaving();
    demonstrateWhereVsHaving();
    demonstrateMultiColumnGrouping();
    demonstrateConditionalAggregation();
    demonstrateDistinctVsGroupBy();
    demonstrateNullBehavior();
    demonstrateRollup();
    demonstrateCube();
    demonstrateGroupingSets();
    demonstrateGroupByVsWindow();
    demonstrateAdvancedHaving();
    demonstrateNormalization();
    demonstrateValidation();
    demonstrateSalesReport();
    demonstrateCommonMistakes();
    demonstrateEdgeCases();
    demonstratePerformanceConsiderations();
    demonstrateSecurityConsiderations();
    runTests();
    printSqlReference();

    console.log("\n" + "=".repeat(80));
    console.log("PROGRAM COMPLETED");
    console.log("=".repeat(80));
}


main();
