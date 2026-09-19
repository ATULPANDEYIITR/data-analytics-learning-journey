/*
 * Advanced Power Query: Query Folding, Custom Columns, Conditional Columns,
 * Parameters, and Reusable Transformations
 *
 * This JavaScript study file models important Power Query concepts with
 * executable JavaScript. Power Query uses the M language, but JavaScript
 * provides useful demonstrations of functional transformation, lazy execution,
 * reusable functions, validation, asynchronous data acquisition, and
 * browser/application-oriented data processing.
 *
 * The examples intentionally progress from simple row transformations to a
 * folding-aware query planner and an industry-style data pipeline.
 */


// ============================================================================
// 1. BASIC TABULAR DATA
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("1. Basic tabular data");
console.log("=".repeat(78));

const sales = [
    { OrderID: 1001, Customer: "Alpha", Region: "North", Amount: 1250 },
    { OrderID: 1002, Customer: "Beta", Region: "South", Amount: 800 },
    { OrderID: 1003, Customer: "Gamma", Region: "North", Amount: 2150 },
    { OrderID: 1004, Customer: "Delta", Region: "West", Amount: 430 }
];

console.table(sales);


// ============================================================================
// 2. CORE TABLE TRANSFORMATIONS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("2. Core table transformations");
console.log("=".repeat(78));

function selectRows(table, predicate) {
    // Conceptually similar to Power Query's Table.SelectRows.
    return table.filter(predicate);
}

function selectColumns(table, columns) {
    // Conceptually similar to Table.SelectColumns.
    return table.map(row => {
        const selected = {};

        for (const column of columns) {
            selected[column] = row[column];
        }

        return selected;
    });
}

function addColumn(table, columnName, expression) {
    // Conceptually similar to Table.AddColumn.
    return table.map(row => ({
        ...row,
        [columnName]: expression(row)
    }));
}

const northSales = selectRows(
    sales,
    row => row.Region === "North"
);

const projectedSales = selectColumns(
    northSales,
    ["OrderID", "Customer", "Amount"]
);

const salesWithTax = addColumn(
    projectedSales,
    "Tax",
    row => Number((row.Amount * 0.18).toFixed(2))
);

console.table(salesWithTax);


// ============================================================================
// 3. CUSTOM COLUMNS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("3. Custom columns");
console.log("=".repeat(78));

function classifyAmount(amount) {
    if (amount === null || amount === undefined) {
        return "Unknown";
    }

    if (amount < 0) {
        return "Invalid";
    }

    if (amount >= 2000) {
        return "High";
    }

    if (amount >= 1000) {
        return "Medium";
    }

    return "Low";
}

const customColumnResult = addColumn(
    sales,
    "AmountBand",
    row => classifyAmount(row.Amount)
);

console.table(customColumnResult);


// ============================================================================
// 4. CONDITIONAL COLUMNS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("4. Conditional columns");
console.log("=".repeat(78));

function riskCategory(row) {
    if (row.Amount === null || row.Amount === undefined) {
        return "Unknown";
    }

    if (row.Amount >= 2000) {
        return "High";
    }

    if (row.Amount >= 1000) {
        return "Medium";
    }

    return "Low";
}

const conditionalResult = addColumn(
    sales,
    "RiskCategory",
    riskCategory
);

console.table(conditionalResult);

/*
Power Query's conceptual equivalent:

Table.AddColumn(
    Source,
    "RiskCategory",
    each
        if [Amount] >= 2000 then "High"
        else if [Amount] >= 1000 then "Medium"
        else "Low"
)
*/


// ============================================================================
// 5. NULL AND TYPE HANDLING
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("5. Null and type handling");
console.log("=".repeat(78));

const messyRows = [
    { Product: "A", Amount: "1250.50" },
    { Product: "B", Amount: null },
    { Product: "C", Amount: "not-a-number" },
    { Product: "D", Amount: "-20" }
];

function safeNumber(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }

    const parsed = Number(value);

    return Number.isFinite(parsed) ? parsed : null;
}

const typedRows = addColumn(
    messyRows,
    "TypedAmount",
    row => safeNumber(row.Amount)
);

const validatedRows = addColumn(
    typedRows,
    "Status",
    row => {
        if (row.TypedAmount === null) {
            return "MissingOrInvalid";
        }

        if (row.TypedAmount < 0) {
            return "Negative";
        }

        return "Valid";
    }
);

console.table(validatedRows);


// ============================================================================
// 6. QUERY FOLDING MODEL
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("6. Query folding model");
console.log("=".repeat(78));

/*
Query folding is a Power Query optimization in which compatible
transformations are translated into operations that the source system
understands.

For a relational database, the conceptual transformation:

    Filter -> Select Columns -> Sort

can become:

    SELECT OrderID, Customer, Amount
    FROM Sales
    WHERE Region = 'North'
    ORDER BY Amount DESC

The actual SQL depends on the connector and source system.
*/

class QueryOperation {
    constructor(name, sqlFragment, foldable, description) {
        this.name = name;
        this.sqlFragment = sqlFragment;
        this.foldable = foldable;
        this.description = description;
    }
}

class QueryPlan {
    constructor(sourceName) {
        this.sourceName = sourceName;
        this.operations = [];
    }

    add(operation) {
        this.operations.push(operation);
        return this;
    }

    getFoldingBoundary() {
        const index = this.operations.findIndex(
            operation => !operation.foldable
        );

        return index === -1 ? null : index;
    }

    getFoldablePrefix() {
        const boundary = this.getFoldingBoundary();

        if (boundary === null) {
            return this.operations;
        }

        return this.operations.slice(0, boundary);
    }

    generateConceptualSQL() {
        const folded = this.getFoldablePrefix();

        let columns = "*";
        const filters = [];
        let orderBy = null;

        for (const operation of folded) {
            if (operation.name === "SelectColumns") {
                columns = operation.sqlFragment;
            }

            if (operation.name === "FilterRows") {
                filters.push(operation.sqlFragment);
            }

            if (operation.name === "Sort") {
                orderBy = operation.sqlFragment;
            }
        }

        let sql = `SELECT ${columns} FROM ${this.sourceName}`;

        if (filters.length > 0) {
            sql += ` WHERE ${filters.join(" AND ")}`;
        }

        if (orderBy) {
            sql += ` ORDER BY ${orderBy}`;
        }

        return `${sql};`;
    }
}

const foldablePlan = new QueryPlan("Sales")
    .add(
        new QueryOperation(
            "FilterRows",
            "Region = 'North'",
            true,
            "Source-translatable filter"
        )
    )
    .add(
        new QueryOperation(
            "SelectColumns",
            "OrderID, Customer, Amount",
            true,
            "Source-translatable projection"
        )
    )
    .add(
        new QueryOperation(
            "Sort",
            "Amount DESC",
            true,
            "Source-translatable sort"
        )
    );

console.log("Conceptual folded SQL:");
console.log(foldablePlan.generateConceptualSQL());
console.log("Folding boundary:", foldablePlan.getFoldingBoundary());


// ============================================================================
// 7. NON-FOLDABLE OPERATION
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("7. Non-foldable operation");
console.log("=".repeat(78));

const mixedPlan = new QueryPlan("Sales")
    .add(
        new QueryOperation(
            "FilterRows",
            "Region = 'North'",
            true,
            "Foldable source filter"
        )
    )
    .add(
        new QueryOperation(
            "SelectColumns",
            "OrderID, Customer, Amount",
            true,
            "Foldable source projection"
        )
    )
    .add(
        new QueryOperation(
            "ArbitraryJavaScriptLogic",
            null,
            false,
            "Illustrative local-only operation"
        )
    )
    .add(
        new QueryOperation(
            "Sort",
            "Amount DESC",
            true,
            "Theoretical source-side operation after boundary"
        )
    );

console.log(
    "Folding boundary index:",
    mixedPlan.getFoldingBoundary()
);

console.log(
    "Folded prefix SQL:",
    mixedPlan.generateConceptualSQL()
);

console.log(
    "Operations after a folding boundary may execute locally and may no "
    + "longer be pushed into the source."
);


// ============================================================================
// 8. PARAMETERS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("8. Parameters");
console.log("=".repeat(78));

const parameters = Object.freeze({
    minimumAmount: 1000,
    selectedRegion: "North",
    includeNegative: false
});

function applyParameters(table, params) {
    return selectRows(table, row => {
        if (row.Amount === null || row.Amount === undefined) {
            return false;
        }

        if (!params.includeNegative && row.Amount < 0) {
            return false;
        }

        return (
            row.Amount >= params.minimumAmount
            && row.Region === params.selectedRegion
        );
    });
}

console.table(applyParameters(sales, parameters));


// ============================================================================
// 9. REUSABLE TRANSFORMATION FUNCTIONS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("9. Reusable transformations");
console.log("=".repeat(78));

function normalizeCustomerName(name) {
    if (name === null || name === undefined) {
        return null;
    }

    return String(name)
        .trim()
        .replace(/\s+/g, " ")
        .toUpperCase();
}

function standardizeSalesTable(table, options = {}) {
    const minimumAmount = options.minimumAmount ?? 0;

    let result = selectColumns(
        table,
        ["OrderID", "Customer", "Region", "Amount"]
    );

    result = selectRows(
        result,
        row =>
            row.Amount !== null
            && row.Amount !== undefined
            && row.Amount >= minimumAmount
    );

    result = addColumn(
        result,
        "CustomerNormalized",
        row => normalizeCustomerName(row.Customer)
    );

    return result;
}

console.table(
    standardizeSalesTable(sales, { minimumAmount: 500 })
);


// ============================================================================
// 10. FUNCTION COMPOSITION
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("10. Function composition");
console.log("=".repeat(78));

function compose(...transformations) {
    return table =>
        transformations.reduce(
            (currentTable, transformation) =>
                transformation(currentTable),
            table
        );
}

const northOnly = table =>
    selectRows(table, row => row.Region === "North");

const highValueOnly = table =>
    selectRows(table, row => row.Amount >= 1000);

const addMargin = table =>
    addColumn(
        table,
        "EstimatedMargin",
        row => Number((row.Amount * 0.22).toFixed(2))
    );

const composedPipeline = compose(
    northOnly,
    highValueOnly,
    addMargin
);

console.table(composedPipeline(sales));


// ============================================================================
// 11. GROUPING
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("11. Grouping and aggregation");
console.log("=".repeat(78));

function groupBySum(table, groupColumn, valueColumn) {
    const groups = new Map();

    for (const row of table) {
        const key = row[groupColumn];

        if (row[valueColumn] === null || row[valueColumn] === undefined) {
            continue;
        }

        groups.set(
            key,
            (groups.get(key) ?? 0) + Number(row[valueColumn])
        );
    }

    return [...groups.entries()].map(([key, total]) => ({
        [groupColumn]: key,
        [`Total${valueColumn}`]: Number(total.toFixed(2))
    }));
}

console.table(
    groupBySum(sales, "Region", "Amount")
);


// ============================================================================
// 12. HASH JOIN
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("12. Hash join");
console.log("=".repeat(78));

const customers = [
    { Customer: "Alpha", Segment: "Enterprise" },
    { Customer: "Beta", Segment: "SMB" },
    { Customer: "Gamma", Segment: "Enterprise" },
    { Customer: "Delta", Segment: "SMB" }
];

function innerJoin(left, right, key) {
    const index = new Map();

    for (const row of right) {
        const value = row[key];

        if (!index.has(value)) {
            index.set(value, []);
        }

        index.get(value).push(row);
    }

    const result = [];

    for (const leftRow of left) {
        const matches = index.get(leftRow[key]) ?? [];

        for (const rightRow of matches) {
            result.push({
                ...leftRow,
                ...Object.fromEntries(
                    Object.entries(rightRow).filter(
                        ([column]) => column !== key
                    )
                )
            });
        }
    }

    return result;
}

console.table(innerJoin(sales, customers, "Customer"));


// ============================================================================
// 13. DATE PARAMETERS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("13. Date parameters");
console.log("=".repeat(78));

const transactions = [
    {
        TransactionID: 1,
        TransactionDate: "2026-09-01",
        Amount: 100
    },
    {
        TransactionID: 2,
        TransactionDate: "2026-09-05",
        Amount: 250
    },
    {
        TransactionID: 3,
        TransactionDate: "2026-08-20",
        Amount: 900
    },
    {
        TransactionID: 4,
        TransactionDate: "2026-09-15",
        Amount: 450
    }
];

function filterDateRange(table, column, startDate, endDate) {
    /*
     * Use [start, end), an inclusive start and exclusive end.
     * This avoids overlap when adjacent partitions are processed.
     */
    return selectRows(
        table,
        row => row[column] >= startDate && row[column] < endDate
    );
}

console.table(
    filterDateRange(
        transactions,
        "TransactionDate",
        "2026-09-01",
        "2026-09-16"
    )
);


// ============================================================================
// 14. ASYNCHRONOUS SOURCE SIMULATION
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("14. Asynchronous source acquisition");
console.log("=".repeat(78));

function fetchSourceData() {
    /*
     * JavaScript is useful for illustrating application-level data acquisition.
     * Power Query connectors have their own source-access mechanisms, but the
     * architectural idea of separating acquisition from transformation is
     * broadly useful.
     */
    return new Promise(resolve => {
        setTimeout(() => {
            resolve([
                { ID: 1, Region: "North", Amount: 1000 },
                { ID: 2, Region: "South", Amount: 500 },
                { ID: 3, Region: "North", Amount: 2000 }
            ]);
        }, 25);
    });
}

async function executeAsyncPipeline() {
    const sourceData = await fetchSourceData();

    const filtered = selectRows(
        sourceData,
        row => row.Region === "North"
    );

    return addColumn(
        filtered,
        "Tax",
        row => row.Amount * 0.18
    );
}


// ============================================================================
// 15. LAZY EVALUATION
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("15. Lazy evaluation");
console.log("=".repeat(78));

class LazyTable {
    constructor(producer) {
        this.producer = producer;
        this.cachedValue = undefined;
        this.hasCachedValue = false;
    }

    evaluate() {
        return this.producer();
    }

    buffer() {
        /*
         * This resembles the conceptual effect of materializing data.
         * It is not equivalent to Power Query's Table.Buffer implementation.
         */
        if (!this.hasCachedValue) {
            this.cachedValue = this.producer();
            this.hasCachedValue = true;
        }

        return this.cachedValue;
    }
}

let sourceEvaluations = 0;

const lazySource = new LazyTable(() => {
    sourceEvaluations += 1;

    return [
        { ID: 1 },
        { ID: 2 }
    ];
});

lazySource.evaluate();
lazySource.evaluate();

console.log(
    "Evaluations without caching:",
    sourceEvaluations
);

sourceEvaluations = 0;

const bufferedSource = new LazyTable(() => {
    sourceEvaluations += 1;

    return [
        { ID: 1 },
        { ID: 2 }
    ];
});

bufferedSource.buffer();
bufferedSource.buffer();

console.log(
    "Evaluations with educational buffering:",
    sourceEvaluations
);

console.log(
    "Materialization can save repeated evaluation in some scenarios, "
    + "but it can also consume memory and interfere with folding."
);


// ============================================================================
// 16. VALIDATION
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("16. Validation");
console.log("=".repeat(78));

function validateParameters(params) {
    if (!Number.isFinite(params.minimumAmount)) {
        throw new TypeError("minimumAmount must be a finite number");
    }

    if (typeof params.selectedRegion !== "string") {
        throw new TypeError("selectedRegion must be a string");
    }

    if (typeof params.includeNegative !== "boolean") {
        throw new TypeError("includeNegative must be boolean");
    }

    if (params.minimumAmount < 0 && !params.includeNegative) {
        throw new RangeError(
            "A negative minimum amount conflicts with the current policy"
        );
    }

    return true;
}

validateParameters(parameters);
console.log("Parameter validation passed.");


// ============================================================================
// 17. DECLARATIVE TRANSFORMATION SPECIFICATIONS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("17. Declarative transformation specifications");
console.log("=".repeat(78));

class TransformationSpec {
    constructor(name, transformation, foldable, purpose) {
        this.name = name;
        this.transformation = transformation;
        this.foldable = foldable;
        this.purpose = purpose;
    }
}

const specifications = [
    new TransformationSpec(
        "Filter North",
        northOnly,
        true,
        "Reduce source rows"
    ),
    new TransformationSpec(
        "Filter High Value",
        highValueOnly,
        true,
        "Reduce rows further"
    ),
    new TransformationSpec(
        "Add Margin",
        addMargin,
        false,
        "Execute a custom local calculation"
    )
];

function executeSpecifications(table, specs) {
    return specs.reduce(
        (current, specification) =>
            specification.transformation(current),
        table
    );
}

console.table(
    executeSpecifications(sales, specifications)
);

for (const specification of specifications) {
    console.log(
        `${specification.name}: foldable=${specification.foldable}; `
        + `${specification.purpose}`
    );
}


// ============================================================================
// 18. FOLDING-AWARE PIPELINE DESIGN
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("18. Folding-aware pipeline design");
console.log("=".repeat(78));

function describeFolding(specs) {
    let foldingActive = true;

    return specs.map(spec => {
        const executedAt = foldingActive && spec.foldable
            ? "source"
            : "local Power Query engine";

        if (!spec.foldable) {
            foldingActive = false;
        }

        return {
            Operation: spec.name,
            Foldable: spec.foldable,
            "Conceptual execution": executedAt
        };
    });
}

console.table(describeFolding(specifications));


// ============================================================================
// 19. PERFORMANCE COMPARISON
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("19. Performance-oriented transformation order");
console.log("=".repeat(78));

const largeDataset = Array.from(
    { length: 100000 },
    (_, index) => ({
        ID: index + 1,
        Region: index % 20 === 0 ? "North" : "Other",
        Amount: index * 10
    })
);

function expensiveCalculation(row) {
    return Math.sqrt(row.Amount + 1)
        * Math.log(row.Amount + 2);
}

console.time("Local calculation before filter");

const calculatedFirst = addColumn(
    largeDataset,
    "Calculated",
    expensiveCalculation
);

const filteredAfterCalculation = selectRows(
    calculatedFirst,
    row => row.Region === "North"
);

console.timeEnd("Local calculation before filter");

console.time("Filter before local calculation");

const filteredFirst = selectRows(
    largeDataset,
    row => row.Region === "North"
);

const calculatedAfterFilter = addColumn(
    filteredFirst,
    "Calculated",
    expensiveCalculation
);

console.timeEnd("Filter before local calculation");

console.log(
    "Rows after early filtering:",
    calculatedAfterFilter.length
);

console.log(
    "The structural advantage is reducing the number of rows that reach "
    + "the expensive local calculation."
);


// ============================================================================
// 20. ERROR-RESILIENT TRANSFORMATION
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("20. Error-resilient custom column");
console.log("=".repeat(78));

function safeMargin(row, marginRate) {
    try {
        const amount = safeNumber(row.Amount);

        if (amount === null) {
            return null;
        }

        return Number((amount * marginRate).toFixed(2));
    } catch {
        return null;
    }
}

const errorResistant = addColumn(
    [
        { ID: 1, Amount: "1000" },
        { ID: 2, Amount: "invalid" },
        { ID: 3, Amount: null }
    ],
    "Margin",
    row => safeMargin(row, 0.22)
);

console.table(errorResistant);


// ============================================================================
// 21. EDGE CASES
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("21. Edge cases");
console.log("=".repeat(78));

const edgeCases = [
    { ID: 1, Amount: 0 },
    { ID: 2, Amount: null },
    { ID: 3, Amount: -100 },
    { ID: 4, Amount: NaN },
    { ID: 5, Amount: Number.MAX_SAFE_INTEGER }
];

const edgeResults = addColumn(
    edgeCases,
    "Band",
    row => {
        if (row.Amount === null) {
            return "Null";
        }

        if (Number.isNaN(row.Amount)) {
            return "NaN";
        }

        if (row.Amount < 0) {
            return "Negative";
        }

        if (row.Amount === 0) {
            return "Zero";
        }

        return "Positive";
    }
);

console.table(edgeResults);


// ============================================================================
// 22. SECURITY CONSIDERATIONS
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("22. Security considerations");
console.log("=".repeat(78));

console.log(`
Important Power Query security principles include:
- Do not hard-code credentials or access tokens into transformation logic.
- Use managed credential mechanisms.
- Validate parameter values.
- Avoid unsafe construction of native SQL from untrusted strings.
- Understand privacy boundaries when combining sources.
- Apply least privilege to source accounts.
- Treat external files and API responses as untrusted input.
- Avoid unnecessary materialization of sensitive data.
- Review reusable transformations for unintended data exposure.
`);


// ============================================================================
// 23. CONCEPTUAL NATIVE QUERY BOUNDARY
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("23. Native query boundary");
console.log("=".repeat(78));

const nativeQueryOperation = new QueryOperation(
    "NativeQuery",
    "OrderID, Customer, Region, Amount",
    false,
    "Illustrative connector-specific boundary"
);

console.log({
    name: nativeQueryOperation.name,
    foldable: nativeQueryOperation.foldable,
    warning:
        "Native query behavior after the boundary is connector-dependent."
});


// ============================================================================
// 24. TESTING
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("24. Testing");
console.log("=".repeat(78));

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(
            `${message}: expected ${expected}, received ${actual}`
        );
    }

    console.log(`PASS: ${message}`);
}

assertEqual(
    classifyAmount(2500),
    "High",
    "High-value classification"
);

assertEqual(
    classifyAmount(500),
    "Low",
    "Low-value classification"
);

assertEqual(
    safeNumber("100.50"),
    100.5,
    "Numeric conversion"
);

assertEqual(
    safeNumber("invalid"),
    null,
    "Invalid numeric conversion"
);

assertEqual(
    selectRows(sales, row => row.Region === "North").length,
    2,
    "North region filtering"
);


// ============================================================================
// 25. COMPLETE ASYNCHRONOUS PIPELINE
// ============================================================================

console.log("\n" + "=".repeat(78));
console.log("25. Complete asynchronous pipeline");
console.log("=".repeat(78));

async function runCompletePipeline() {
    const sourceData = await fetchSourceData();

    const parameterized = applyParameters(
        sourceData,
        {
            minimumAmount: 1000,
            selectedRegion: "North",
            includeNegative: false
        }
    );

    const standardized = standardizeSalesTable(
        parameterized,
        { minimumAmount: 1000 }
    );

    return addColumn(
        standardized,
        "EstimatedMargin",
        row => Number((row.Amount * 0.22).toFixed(2))
    );
}


// ============================================================================
// 26. MAIN EXECUTION
// ============================================================================

(async () => {
    try {
        const finalResult = await runCompletePipeline();

        console.log("\nComplete asynchronous result:");
        console.table(finalResult);

        console.log("\n" + "=".repeat(78));
        console.log("JavaScript study execution completed");
        console.log("=".repeat(78));

        console.log(
            "The implementation demonstrated custom columns, conditional "
            + "columns, parameterization, reusable transformations, joins, "
            + "grouping, asynchronous acquisition, lazy evaluation, "
            + "validation, folding boundaries, and performance-aware ordering."
        );
    } catch (error) {
        console.error("Pipeline failed:", error.message);
        process.exitCode = 1;
    }
})();
