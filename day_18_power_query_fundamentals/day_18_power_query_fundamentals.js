/*
 * Power Query Fundamentals: ETL Concepts in JavaScript
 *
 * This self-contained JavaScript program demonstrates the same core
 * data-preparation ideas used in Power Query:
 *
 * Extract -> Transform -> Load
 *
 * JavaScript is particularly useful for showing:
 * - JSON-oriented data
 * - Functional transformations
 * - Array methods such as map/filter/reduce
 * - Validation
 * - Object-based data modeling
 * - Asynchronous extraction patterns
 * - Deterministic transformation pipelines
 * - Browser/application-oriented ETL
 * - Performance considerations
 *
 * Run with:
 *     node power-query-fundamentals.js
 */

"use strict";


// ============================================================================
// 1. ETL FUNDAMENTALS
// ============================================================================

console.log("=".repeat(78));
console.log("POWER QUERY FUNDAMENTALS: ETL WITH JAVASCRIPT");
console.log("=".repeat(78));

console.log(`
Extract:
  Read data from CSV, JSON, databases, APIs, files, or other sources.

Transform:
  Clean, validate, type, filter, join, append, aggregate, and reshape data.

Load:
  Send the prepared dataset to a report, application, file, database,
  data model, or other destination.

Power Query records transformations as repeatable query steps.
This program models that idea with JavaScript functions and classes.
`);


// ============================================================================
// 2. SOURCE DATA
// ============================================================================

const salesSource = [
    {
        OrderID: "1001",
        OrderDate: "2026-01-05",
        CustomerID: "C001",
        ProductID: "P100",
        Quantity: "2",
        UnitPrice: "1250.50",
        Region: " North "
    },
    {
        OrderID: "1002",
        OrderDate: "2026-01-06",
        CustomerID: "C002",
        ProductID: "P200",
        Quantity: "5",
        UnitPrice: "299.99",
        Region: "South"
    },
    {
        OrderID: "1003",
        OrderDate: "2026-01-07",
        CustomerID: "C003",
        ProductID: "P100",
        Quantity: "1",
        UnitPrice: "1250.50",
        Region: "West"
    },
    {
        OrderID: "1004",
        OrderDate: "2026-01-08",
        CustomerID: "C001",
        ProductID: "P300",
        Quantity: "3",
        UnitPrice: "850.00",
        Region: "North"
    },
    {
        OrderID: "1005",
        OrderDate: "2026-01-09",
        CustomerID: "C004",
        ProductID: "P200",
        Quantity: "4",
        UnitPrice: "299.99",
        Region: "East"
    },
    {
        OrderID: "1006",
        OrderDate: "2026-01-10",
        CustomerID: "C005",
        ProductID: "P400",
        Quantity: "2",
        UnitPrice: "1750.00",
        Region: "South"
    }
];

const customers = [
    { CustomerID: "C001", CustomerName: "Atul Pandey", Segment: "Professional" },
    { CustomerID: "C002", CustomerName: "Neha Sharma", Segment: "Enterprise" },
    { CustomerID: "C003", CustomerName: "Rahul Verma", Segment: "SMB" },
    { CustomerID: "C004", CustomerName: "Priya Singh", Segment: "Enterprise" },
    { CustomerID: "C005", CustomerName: "Arjun Mehta", Segment: "Professional" }
];

const products = [
    { ProductID: "P100", ProductName: "Laptop", Category: "Computing" },
    { ProductID: "P200", ProductName: "Keyboard", Category: "Accessories" },
    { ProductID: "P300", ProductName: "Monitor", Category: "Computing" },
    { ProductID: "P400", ProductName: "Server", Category: "Infrastructure" }
];


// ============================================================================
// 3. TYPE INSPECTION
// ============================================================================

function inspectSchema(rows) {
    if (rows.length === 0) {
        return {};
    }

    const schema = {};

    for (const column of Object.keys(rows[0])) {
        schema[column] = [
            ...new Set(
                rows.map(row => {
                    if (row[column] === null) return "null";
                    if (Array.isArray(row[column])) return "array";
                    return typeof row[column];
                })
            )
        ];
    }

    return schema;
}

console.log("\nRAW SCHEMA:");
console.log(inspectSchema(salesSource));


// ============================================================================
// 4. DATA TYPE CONVERSION
// ============================================================================

function parseInteger(value, fieldName) {
    const number = Number.parseInt(String(value).trim(), 10);

    if (!Number.isInteger(number)) {
        throw new Error(`${fieldName} must be an integer`);
    }

    return number;
}

function parseMoney(value, fieldName) {
    const number = Number.parseFloat(String(value).trim());

    if (!Number.isFinite(number)) {
        throw new Error(`${fieldName} must be numeric`);
    }

    return number;
}

function parseDate(value, fieldName) {
    const date = new Date(`${String(value).trim()}T00:00:00Z`);

    if (Number.isNaN(date.getTime())) {
        throw new Error(`${fieldName} contains an invalid date`);
    }

    return date;
}

function typeSalesRows(rows) {
    return rows.map(row => ({
        OrderID: parseInteger(row.OrderID, "OrderID"),
        OrderDate: parseDate(row.OrderDate, "OrderDate"),
        CustomerID: String(row.CustomerID).trim(),
        ProductID: String(row.ProductID).trim(),
        Quantity: parseInteger(row.Quantity, "Quantity"),
        UnitPrice: parseMoney(row.UnitPrice, "UnitPrice"),
        Region: String(row.Region).trim()
    }));
}

const typedSales = typeSalesRows(salesSource);

console.log("\nTYPED ROW:");
console.log(typedSales[0]);


// ============================================================================
// 5. TEXT TRANSFORMATION
// ============================================================================

function normalizeText(value) {
    return String(value).trim().replace(/\s+/g, " ");
}

function cleanSalesText(rows) {
    return rows.map(row => ({
        ...row,
        CustomerID: normalizeText(row.CustomerID),
        ProductID: normalizeText(row.ProductID),
        Region: normalizeText(row.Region)
            .toLowerCase()
            .replace(/\b\w/g, letter => letter.toUpperCase())
    }));
}

const cleanedSales = cleanSalesText(typedSales);


// ============================================================================
// 6. CUSTOM COLUMN
// ============================================================================

function addSalesAmount(rows) {
    return rows.map(row => ({
        ...row,
        SalesAmount: row.Quantity * row.UnitPrice
    }));
}

const calculatedSales = addSalesAmount(cleanedSales);

console.log("\nCALCULATED COLUMN:");
console.log(calculatedSales[0].SalesAmount);


// ============================================================================
// 7. FILTERING
// ============================================================================

const northSales = calculatedSales.filter(
    row => row.Region === "North"
);

const largeOrders = calculatedSales.filter(
    row => row.Quantity >= 4
);

const highValueOrders = calculatedSales.filter(
    row => row.SalesAmount >= 2000
);

console.log("\nFILTERING:");
console.log("North:", northSales.length);
console.log("Quantity >= 4:", largeOrders.length);
console.log("SalesAmount >= 2000:", highValueOrders.length);


// ============================================================================
// 8. SELECTING AND RENAMING COLUMNS
// ============================================================================

function selectColumns(rows, columns) {
    return rows.map(row => {
        const selected = {};

        for (const column of columns) {
            selected[column] = row[column];
        }

        return selected;
    });
}

function renameColumns(rows, mapping) {
    return rows.map(row => {
        const renamed = {};

        for (const [key, value] of Object.entries(row)) {
            renamed[mapping[key] ?? key] = value;
        }

        return renamed;
    });
}

const compactSales = renameColumns(
    selectColumns(
        calculatedSales,
        ["OrderID", "CustomerID", "Region", "SalesAmount"]
    ),
    { SalesAmount: "Revenue" }
);

console.log("\nSELECTED/RENAMED:");
console.log(compactSales[0]);


// ============================================================================
// 9. SORTING
// ============================================================================

const sortedSales = [...calculatedSales].sort(
    (a, b) => b.SalesAmount - a.SalesAmount
);

console.log("\nTOP ORDERS:");

for (const row of sortedSales.slice(0, 3)) {
    console.log(row.OrderID, row.SalesAmount);
}


// ============================================================================
// 10. NULL AND ERROR HANDLING
// ============================================================================

function safeMoney(value) {
    if (value === null || value === undefined || String(value).trim() === "") {
        return null;
    }

    const number = Number.parseFloat(String(value));

    return Number.isFinite(number) ? number : null;
}

const dirtyValues = ["1250.50", "", null, "invalid"];

console.log("\nSAFE CONVERSION:");

for (const value of dirtyValues) {
    console.log(JSON.stringify(value), "=>", safeMoney(value));
}


// ============================================================================
// 11. VALIDATION
// ============================================================================

function validateSales(rows) {
    const errors = [];

    rows.forEach((row, index) => {
        if (row.Quantity <= 0) {
            errors.push(`Row ${index + 1}: Quantity must be positive`);
        }

        if (row.UnitPrice < 0) {
            errors.push(`Row ${index + 1}: UnitPrice cannot be negative`);
        }

        if (!row.CustomerID) {
            errors.push(`Row ${index + 1}: CustomerID is required`);
        }

        if (!row.ProductID) {
            errors.push(`Row ${index + 1}: ProductID is required`);
        }
    });

    return errors;
}

console.log("\nVALIDATION:");
console.log(validateSales(calculatedSales));


// ============================================================================
// 12. DEDUPLICATION
// ============================================================================

function distinctByKey(rows, key) {
    const seen = new Set();

    return rows.filter(row => {
        const value = row[key];

        if (seen.has(value)) {
            return false;
        }

        seen.add(value);
        return true;
    });
}

const duplicateData = [
    ...calculatedSales,
    { ...calculatedSales[0] }
];

console.log("\nDEDUPLICATION:");
console.log(
    "Before:",
    duplicateData.length,
    "After:",
    distinctByKey(duplicateData, "OrderID").length
);


// ============================================================================
// 13. MERGING WITH AN INDEX
// ============================================================================

function createIndex(rows, key) {
    const index = new Map();

    for (const row of rows) {
        index.set(row[key], row);
    }

    return index;
}

function leftMerge(leftRows, rightRows, leftKey, rightKey, prefix = "") {
    const rightIndex = createIndex(rightRows, rightKey);

    return leftRows.map(leftRow => {
        const rightRow = rightIndex.get(leftRow[leftKey]);
        const merged = { ...leftRow };

        if (rightRow) {
            for (const [key, value] of Object.entries(rightRow)) {
                if (key !== rightKey) {
                    merged[`${prefix}${key}`] = value;
                }
            }
        } else {
            for (const key of Object.keys(rightRows[0] ?? {})) {
                if (key !== rightKey) {
                    merged[`${prefix}${key}`] = null;
                }
            }
        }

        return merged;
    });
}

const salesWithCustomers = leftMerge(
    calculatedSales,
    customers,
    "CustomerID",
    "CustomerID"
);

const enrichedSales = leftMerge(
    salesWithCustomers,
    products,
    "ProductID",
    "ProductID"
);

console.log("\nMERGED ROW:");
console.log(enrichedSales[0]);


// ============================================================================
// 14. INNER MERGE
// ============================================================================

function innerMerge(leftRows, rightRows, leftKey, rightKey) {
    const rightIndex = createIndex(rightRows, rightKey);
    const result = [];

    for (const leftRow of leftRows) {
        const rightRow = rightIndex.get(leftRow[leftKey]);

        if (rightRow) {
            const merged = { ...leftRow };

            for (const [key, value] of Object.entries(rightRow)) {
                if (key !== rightKey) {
                    merged[`right_${key}`] = value;
                }
            }

            result.push(merged);
        }
    }

    return result;
}

console.log(
    "\nINNER JOIN ROWS:",
    innerMerge(
        calculatedSales,
        customers,
        "CustomerID",
        "CustomerID"
    ).length
);


// ============================================================================
// 15. APPENDING
// ============================================================================

function appendTables(...tables) {
    return tables.flatMap(table => table.map(row => ({ ...row })));
}

const january = [
    { OrderID: 1, Region: "North", Revenue: 100 },
    { OrderID: 2, Region: "South", Revenue: 200 }
];

const february = [
    { OrderID: 3, Region: "North", Revenue: 150 },
    { OrderID: 4, Region: "West", Revenue: 300 }
];

const appended = appendTables(january, february);

console.log("\nAPPENDED ROWS:");
console.log(appended);


// ============================================================================
// 16. MERGE VS APPEND
// ============================================================================

console.log(`
MERGE VS APPEND

Merge:
  Horizontal combination.
  Uses a key relationship.
  Usually increases the number of columns.

Append:
  Vertical combination.
  Stacks rows.
  Usually increases the number of rows.

Example:

Orders + Customers by CustomerID = Merge

January Orders + February Orders = Append
`);


// ============================================================================
// 17. GROUP BY
// ============================================================================

function groupSum(rows, groupKey, valueKey) {
    const totals = new Map();

    for (const row of rows) {
        const group = row[groupKey];
        const value = Number(row[valueKey]);

        totals.set(
            group,
            (totals.get(group) ?? 0) + value
        );
    }

    return Object.fromEntries(totals);
}

const regionalRevenue = groupSum(
    enrichedSales,
    "Region",
    "SalesAmount"
);

console.log("\nREGIONAL REVENUE:");
console.log(regionalRevenue);


// ============================================================================
// 18. DATE ATTRIBUTES
// ============================================================================

function addDateAttributes(rows) {
    return rows.map(row => {
        const date = row.OrderDate;

        return {
            ...row,
            Year: date.getUTCFullYear(),
            Month: date.getUTCMonth() + 1,
            Quarter: Math.floor(date.getUTCMonth() / 3) + 1,
            DayOfWeek: date.toLocaleDateString(
                "en-US",
                {
                    weekday: "long",
                    timeZone: "UTC"
                }
            )
        };
    });
}

const datedSales = addDateAttributes(enrichedSales);

console.log("\nDATE ATTRIBUTES:");
console.log(datedSales[0]);


// ============================================================================
// 19. CONDITIONAL COLUMN
// ============================================================================

function addOrderValueClass(rows) {
    return rows.map(row => {
        let orderValueClass;

        if (row.SalesAmount >= 4000) {
            orderValueClass = "Very High";
        } else if (row.SalesAmount >= 2000) {
            orderValueClass = "High";
        } else if (row.SalesAmount >= 1000) {
            orderValueClass = "Medium";
        } else {
            orderValueClass = "Low";
        }

        return {
            ...row,
            OrderValueClass: orderValueClass
        };
    });
}

const classifiedSales = addOrderValueClass(datedSales);


// ============================================================================
// 20. QUERY PIPELINE
// ============================================================================

class DataQuery {
    /*
     * This class models Power Query's sequence of applied transformation
     * steps. Each operation receives the result of the preceding step.
     */
    constructor(source) {
        this.source = source.map(row => ({ ...row }));
        this.steps = [];
    }

    addStep(name, transformation) {
        this.steps.push({
            name,
            transformation
        });

        return this;
    }

    execute() {
        let current = this.source.map(row => ({ ...row }));

        for (const step of this.steps) {
            current = step.transformation(current);
        }

        return current;
    }

    describe() {
        return this.steps.map(step => step.name);
    }
}

const query = new DataQuery(calculatedSales)
    .addStep(
        "Filter North region",
        rows => rows.filter(row => row.Region === "North")
    )
    .addStep(
        "Filter high-value orders",
        rows => rows.filter(row => row.SalesAmount > 1000)
    )
    .addStep(
        "Sort by revenue",
        rows => [...rows].sort(
            (a, b) => b.SalesAmount - a.SalesAmount
        )
    );

console.log("\nQUERY STEPS:");

query.describe().forEach((step, index) => {
    console.log(`${index + 1}. ${step}`);
});

console.log("\nQUERY RESULT:");
console.log(query.execute());


// ============================================================================
// 21. REFERENTIAL INTEGRITY
// ============================================================================

function findUnmatchedKeys(factRows, dimensionRows, factKey, dimensionKey) {
    const dimensionKeys = new Set(
        dimensionRows.map(row => row[dimensionKey])
    );

    return [
        ...new Set(
            factRows
                .filter(row => !dimensionKeys.has(row[factKey]))
                .map(row => row[factKey])
        )
    ];
}

console.log("\nUNMATCHED CUSTOMER KEYS:");
console.log(
    findUnmatchedKeys(
        calculatedSales,
        customers,
        "CustomerID",
        "CustomerID"
    )
);


// ============================================================================
// 22. SCHEMA VALIDATION
// ============================================================================

function requireColumns(rows, requiredColumns) {
    if (rows.length === 0) {
        throw new Error("Source contains no rows");
    }

    const actualColumns = new Set(Object.keys(rows[0]));

    const missing = requiredColumns.filter(
        column => !actualColumns.has(column)
    );

    if (missing.length > 0) {
        throw new Error(
            `Missing columns: ${missing.join(", ")}`
        );
    }
}

requireColumns(
    salesSource,
    [
        "OrderID",
        "OrderDate",
        "CustomerID",
        "ProductID",
        "Quantity",
        "UnitPrice",
        "Region"
    ]
);

console.log("\nSCHEMA VALIDATION: passed");


// ============================================================================
// 23. ASYNCHRONOUS EXTRACTION
// ============================================================================

function simulateApiExtraction() {
    /*
     * Real applications may obtain source data asynchronously from APIs.
     * Power Query similarly supports many external data sources.
     */
    return new Promise(resolve => {
        setTimeout(
            () => resolve([
                { ProductID: "P500", ProductName: "Router" }
            ]),
            10
        );
    });
}

async function demonstrateAsyncExtraction() {
    const apiData = await simulateApiExtraction();

    console.log("\nASYNC EXTRACTION:");
    console.log(apiData);
}


// ============================================================================
// 24. COMPLETE END-TO-END PIPELINE
// ============================================================================

function runSalesETL(
    sourceSales,
    sourceCustomers,
    sourceProducts
) {
    requireColumns(
        sourceSales,
        [
            "OrderID",
            "OrderDate",
            "CustomerID",
            "ProductID",
            "Quantity",
            "UnitPrice",
            "Region"
        ]
    );

    const typed = typeSalesRows(sourceSales);
    const cleaned = cleanSalesText(typed);
    const calculated = addSalesAmount(cleaned);

    const errors = validateSales(calculated);

    if (errors.length > 0) {
        throw new Error(
            `Validation failed: ${errors.join("; ")}`
        );
    }

    const withCustomers = leftMerge(
        calculated,
        sourceCustomers,
        "CustomerID",
        "CustomerID"
    );

    const withProducts = leftMerge(
        withCustomers,
        sourceProducts,
        "ProductID",
        "ProductID"
    );

    const withDates = addDateAttributes(withProducts);

    return addOrderValueClass(withDates);
}

const start = performance.now();

const finalDataset = runSalesETL(
    salesSource,
    customers,
    products
);

const elapsed = performance.now() - start;

console.log("\nEND-TO-END ETL:");
console.log("Rows:", finalDataset.length);
console.log("Execution time:", `${elapsed.toFixed(3)} ms`);


// ============================================================================
// 25. TESTING
// ============================================================================

function assertEqual(actual, expected, description) {
    if (actual !== expected) {
        throw new Error(
            `${description}: expected ${expected}, got ${actual}`
        );
    }

    console.log("PASS:", description);
}

assertEqual(
    finalDataset.length,
    salesSource.length,
    "Left merge preserves sales rows"
);

assertEqual(
    finalDataset[0].SalesAmount,
    2501,
    "Sales amount calculation"
);

assertEqual(
    finalDataset[0].CustomerName,
    "Atul Pandey",
    "Customer merge"
);

assertEqual(
    finalDataset[0].ProductName,
    "Laptop",
    "Product merge"
);

assertEqual(
    finalDataset[0].Quarter,
    1,
    "Quarter calculation"
);


// ============================================================================
// 26. JSON LOAD
// ============================================================================

function prepareForJSON(rows) {
    return rows.map(row => ({
        ...row,
        OrderDate: row.OrderDate.toISOString().slice(0, 10)
    }));
}

const jsonOutput = JSON.stringify(
    prepareForJSON(finalDataset.slice(0, 2)),
    null,
    2
);

console.log("\nLOAD-READY JSON:");
console.log(jsonOutput);


// ============================================================================
// 27. PERFORMANCE NOTES
// ============================================================================

console.log(`
PERFORMANCE

Array.filter/map/reduce are expressive and useful for moderate datasets.

Repeated nested searches can approach O(n*m) for a join.

Creating a Map index provides approximately O(1) average lookup and makes
an indexed equality join approximately O(n + m).

For large datasets:
- Avoid unnecessary copies.
- Select required columns early.
- Filter early when semantics permit it.
- Avoid repeated full-array scans.
- Use streaming or database-side processing when datasets exceed memory.
- Use source-side filtering when the source system supports it.
- Measure actual performance instead of assuming an optimization helps.

Power Query's query folding is analogous to pushing supported work toward
the data source so that the client processes less data.
`);


// ============================================================================
// 28. EDGE CASES
// ============================================================================

const edgeCases = [
    { Quantity: 0, UnitPrice: 100 },
    { Quantity: -2, UnitPrice: 100 },
    { Quantity: 2, UnitPrice: 0 },
    { Quantity: 2, UnitPrice: -50 },
    { Quantity: 2, UnitPrice: null }
];

console.log("\nEDGE CASES:");

for (const row of edgeCases) {
    const valid =
        Number.isInteger(row.Quantity) &&
        row.Quantity > 0 &&
        Number.isFinite(row.UnitPrice) &&
        row.UnitPrice >= 0;

    console.log(row, "=>", valid ? "valid" : "invalid");
}


// ============================================================================
// 29. IDEMPOTENT TRANSFORMATION
// ============================================================================

function normalizeRegion(value) {
    return normalizeText(value)
        .toLowerCase()
        .replace(/\b\w/g, letter => letter.toUpperCase());
}

const normalizedOnce = normalizeRegion("  north ");
const normalizedTwice = normalizeRegion(normalizedOnce);

console.log("\nIDEMPOTENCE:");
console.log(normalizedOnce);
console.log(normalizedTwice);
console.log("Same:", normalizedOnce === normalizedTwice);


// ============================================================================
// 30. FINAL OUTPUT
// ============================================================================

console.log("\nFINAL DATASET SAMPLE:");

console.table(
    finalDataset.map(row => ({
        OrderID: row.OrderID,
        Date: row.OrderDate.toISOString().slice(0, 10),
        Customer: row.CustomerName,
        Product: row.ProductName,
        Region: row.Region,
        Revenue: row.SalesAmount,
        Class: row.OrderValueClass
    }))
);

(async () => {
    await demonstrateAsyncExtraction();

    console.log("\n" + "=".repeat(78));
    console.log("ETL STUDY PROGRAM COMPLETE");
    console.log("=".repeat(78));
})();
