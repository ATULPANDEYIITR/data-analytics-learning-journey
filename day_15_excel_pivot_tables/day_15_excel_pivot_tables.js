/*
 * Excel Pivot Tables: Comprehensive JavaScript Study
 *
 * This standalone file demonstrates the conceptual architecture of Excel
 * Pivot Tables using JavaScript.
 *
 * Topics demonstrated:
 *   - Source data
 *   - Rows
 *   - Columns
 *   - Values
 *   - Filters
 *   - Aggregation
 *   - Grouping
 *   - Calculated fields
 *   - Drill-down
 *   - Subtotals
 *   - Grand totals
 *   - Percentage of total
 *   - Running totals
 *   - Top-N analysis
 *   - Validation
 *   - Performance considerations
 *   - A reusable pivot engine
 *
 * Run with:
 *   node pivot_tables.js
 *
 * No external npm packages are required.
 */

// ---------------------------------------------------------------------------
// 1. SOURCE DATA
// ---------------------------------------------------------------------------

const salesData = [
    { orderId: "O001", orderDate: "2025-01-05", region: "North", salesperson: "Asha", product: "Laptop", category: "Electronics", quantity: 2, unitPrice: 800, unitCost: 600, customerType: "Retail" },
    { orderId: "O002", orderDate: "2025-01-12", region: "North", salesperson: "Rahul", product: "Phone", category: "Electronics", quantity: 5, unitPrice: 500, unitCost: 350, customerType: "Corporate" },
    { orderId: "O003", orderDate: "2025-01-18", region: "South", salesperson: "Neha", product: "Desk", category: "Furniture", quantity: 3, unitPrice: 250, unitCost: 150, customerType: "Retail" },
    { orderId: "O004", orderDate: "2025-02-02", region: "South", salesperson: "Vikram", product: "Chair", category: "Furniture", quantity: 10, unitPrice: 120, unitCost: 70, customerType: "Corporate" },
    { orderId: "O005", orderDate: "2025-02-09", region: "East", salesperson: "Asha", product: "Laptop", category: "Electronics", quantity: 1, unitPrice: 850, unitCost: 610, customerType: "Retail" },
    { orderId: "O006", orderDate: "2025-02-16", region: "East", salesperson: "Rahul", product: "Phone", category: "Electronics", quantity: 4, unitPrice: 520, unitCost: 360, customerType: "Corporate" },
    { orderId: "O007", orderDate: "2025-03-04", region: "West", salesperson: "Neha", product: "Desk", category: "Furniture", quantity: 2, unitPrice: 270, unitCost: 160, customerType: "Retail" },
    { orderId: "O008", orderDate: "2025-03-11", region: "West", salesperson: "Vikram", product: "Chair", category: "Furniture", quantity: 8, unitPrice: 125, unitCost: 72, customerType: "Corporate" },
    { orderId: "O009", orderDate: "2025-03-19", region: "North", salesperson: "Asha", product: "Monitor", category: "Electronics", quantity: 6, unitPrice: 300, unitCost: 210, customerType: "Retail" },
    { orderId: "O010", orderDate: "2025-04-03", region: "South", salesperson: "Rahul", product: "Laptop", category: "Electronics", quantity: 3, unitPrice: 820, unitCost: 590, customerType: "Corporate" },
    { orderId: "O011", orderDate: "2025-04-10", region: "East", salesperson: "Neha", product: "Chair", category: "Furniture", quantity: 6, unitPrice: 130, unitCost: 75, customerType: "Retail" },
    { orderId: "O012", orderDate: "2025-04-22", region: "West", salesperson: "Vikram", product: "Phone", category: "Electronics", quantity: 7, unitPrice: 510, unitCost: 355, customerType: "Corporate" },
    { orderId: "O013", orderDate: "2025-05-02", region: "North", salesperson: "Asha", product: "Desk", category: "Furniture", quantity: 4, unitPrice: 260, unitCost: 155, customerType: "Retail" },
    { orderId: "O014", orderDate: "2025-05-17", region: "South", salesperson: "Rahul", product: "Monitor", category: "Electronics", quantity: 5, unitPrice: 310, unitCost: 215, customerType: "Corporate" },
    { orderId: "O015", orderDate: "2025-06-07", region: "East", salesperson: "Neha", product: "Laptop", category: "Electronics", quantity: 2, unitPrice: 840, unitCost: 605, customerType: "Retail" },
    { orderId: "O016", orderDate: "2025-06-21", region: "West", salesperson: "Vikram", product: "Desk", category: "Furniture", quantity: 3, unitPrice: 255, unitCost: 152, customerType: "Corporate" },
    { orderId: "O017", orderDate: "2025-07-05", region: "North", salesperson: "Asha", product: "Chair", category: "Furniture", quantity: 9, unitPrice: 118, unitCost: 69, customerType: "Retail" },
    { orderId: "O018", orderDate: "2025-07-14", region: "South", salesperson: "Rahul", product: "Phone", category: "Electronics", quantity: 6, unitPrice: 515, unitCost: 358, customerType: "Corporate" },
    { orderId: "O019", orderDate: "2025-08-08", region: "East", salesperson: "Neha", product: "Monitor", category: "Electronics", quantity: 3, unitPrice: 305, unitCost: 212, customerType: "Retail" },
    { orderId: "O020", orderDate: "2025-08-25", region: "West", salesperson: "Vikram", product: "Laptop", category: "Electronics", quantity: 2, unitPrice: 830, unitCost: 595, customerType: "Corporate" }
];


// ---------------------------------------------------------------------------
// 2. DERIVED SOURCE FIELDS
// ---------------------------------------------------------------------------

function getFieldValue(record, fieldName) {
    const normalized = fieldName.trim().toLowerCase();

    switch (normalized) {
        case "order id":
        case "orderid":
            return record.orderId;

        case "order date":
        case "orderdate":
            return new Date(`${record.orderDate}T00:00:00`);

        case "region":
            return record.region;

        case "salesperson":
            return record.salesperson;

        case "product":
            return record.product;

        case "category":
            return record.category;

        case "quantity":
            return record.quantity;

        case "unit price":
        case "unitprice":
            return record.unitPrice;

        case "unit cost":
        case "unitcost":
            return record.unitCost;

        case "sales":
        case "revenue":
            return record.quantity * record.unitPrice;

        case "cost":
            return record.quantity * record.unitCost;

        case "profit":
            return (
                record.quantity * record.unitPrice
                - record.quantity * record.unitCost
            );

        case "profit margin": {
            const sales = record.quantity * record.unitPrice;
            const profit =
                record.quantity * record.unitPrice
                - record.quantity * record.unitCost;

            return sales === 0 ? 0 : profit / sales;
        }

        case "customer type":
        case "customertype":
            return record.customerType;

        default:
            throw new Error(`Unknown Pivot field: ${fieldName}`);
    }
}


// ---------------------------------------------------------------------------
// 3. AGGREGATION FUNCTIONS
// ---------------------------------------------------------------------------

const aggregations = {
    sum(values) {
        return values.reduce((total, value) => total + Number(value), 0);
    },

    count(values) {
        return values.length;
    },

    average(values) {
        if (values.length === 0) return 0;

        return values.reduce(
            (total, value) => total + Number(value),
            0
        ) / values.length;
    },

    min(values) {
        return values.length === 0 ? null : Math.min(...values);
    },

    max(values) {
        return values.length === 0 ? null : Math.max(...values);
    },

    distinctCount(values) {
        return new Set(values).size;
    }
};


// ---------------------------------------------------------------------------
// 4. FILTERS
// ---------------------------------------------------------------------------

function applyFilters(records, filters = {}) {
    return records.filter(record => {
        return Object.entries(filters).every(
            ([fieldName, allowedValues]) => {
                const actualValue = getFieldValue(record, fieldName);

                return allowedValues.includes(actualValue);
            }
        );
    });
}


// ---------------------------------------------------------------------------
// 5. GROUPING
// ---------------------------------------------------------------------------

function groupDate(dateValue, grouping) {
    const date = dateValue instanceof Date
        ? dateValue
        : new Date(`${dateValue}T00:00:00`);

    if (Number.isNaN(date.getTime())) {
        throw new Error(`Invalid date: ${dateValue}`);
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const quarter = Math.floor(date.getMonth() / 3) + 1;

    if (grouping === "year") {
        return String(year);
    }

    if (grouping === "quarter") {
        return `${year}-Q${quarter}`;
    }

    if (grouping === "month") {
        return `${year}-${month}`;
    }

    throw new Error(`Unsupported date grouping: ${grouping}`);
}


function groupQuantity(quantity) {
    if (quantity <= 2) return "1-2";
    if (quantity <= 5) return "3-5";
    if (quantity <= 8) return "6-8";
    return "9+";
}


function getGroupedFieldValue(record, fieldName, grouping) {
    const value = getFieldValue(record, fieldName);

    if (!grouping) {
        return value;
    }

    if (grouping === "year" ||
        grouping === "quarter" ||
        grouping === "month") {
        return groupDate(value, grouping);
    }

    if (grouping === "quantityBand") {
        return groupQuantity(value);
    }

    throw new Error(`Unsupported grouping: ${grouping}`);
}


// ---------------------------------------------------------------------------
// 6. PIVOT ENGINE
// ---------------------------------------------------------------------------

class PivotEngine {
    constructor(records) {
        this.records = records;
    }

    validateConfiguration(configuration) {
        if (!configuration.values ||
            configuration.values.length === 0) {
            throw new Error(
                "A Pivot configuration requires at least one value field."
            );
        }

        for (const valueField of configuration.values) {
            if (!aggregations[valueField.aggregation]) {
                throw new Error(
                    `Unsupported aggregation: ${valueField.aggregation}`
                );
            }
        }
    }

    calculateValue(record, valueField, calculatedFields) {
        if (calculatedFields &&
            calculatedFields[valueField]) {
            return calculatedFields[valueField](record);
        }

        return getFieldValue(record, valueField);
    }

    build(configuration) {
        this.validateConfiguration(configuration);

        const {
            rows = [],
            columns = [],
            values,
            filters = {},
            rowGrouping = {},
            columnGrouping = {},
            calculatedFields = {}
        } = configuration;

        const filteredRecords = applyFilters(
            this.records,
            filters
        );

        /*
         * Map structure:
         *
         * rowKey -> columnKey -> valueLabel -> raw values
         *
         * This is the core of a two-dimensional Pivot Table.
         */
        const cells = new Map();
        const rowKeys = new Set();
        const columnKeys = new Set();

        for (const record of filteredRecords) {
            const rowKey = rows.map(
                fieldName => getGroupedFieldValue(
                    record,
                    fieldName,
                    rowGrouping[fieldName]
                )
            );

            const columnKey = columns.map(
                fieldName => getGroupedFieldValue(
                    record,
                    fieldName,
                    columnGrouping[fieldName]
                )
            );

            const rowKeyString = JSON.stringify(rowKey);
            const columnKeyString = JSON.stringify(columnKey);

            rowKeys.add(rowKeyString);
            columnKeys.add(columnKeyString);

            if (!cells.has(rowKeyString)) {
                cells.set(rowKeyString, new Map());
            }

            const rowMap = cells.get(rowKeyString);

            if (!rowMap.has(columnKeyString)) {
                rowMap.set(columnKeyString, new Map());
            }

            const columnMap = rowMap.get(columnKeyString);

            for (const valueDefinition of values) {
                const label =
                    valueDefinition.label ||
                    `${valueDefinition.aggregation.toUpperCase()} of ${valueDefinition.field}`;

                const value = this.calculateValue(
                    record,
                    valueDefinition.field,
                    calculatedFields
                );

                if (!columnMap.has(label)) {
                    columnMap.set(label, []);
                }

                columnMap.get(label).push(value);
            }
        }

        const sortedRows = [...rowKeys].sort();
        const sortedColumns = [...columnKeys].sort();

        const result = {
            rows: sortedRows.map(JSON.parse),
            columns: sortedColumns.map(JSON.parse),
            cells: {},
            grandTotals: {}
        };

        for (const rowKeyString of sortedRows) {
            result.cells[rowKeyString] = {};

            const rowMap = cells.get(rowKeyString);

            for (const columnKeyString of sortedColumns) {
                if (!rowMap || !rowMap.has(columnKeyString)) {
                    continue;
                }

                const columnMap = rowMap.get(columnKeyString);

                result.cells[rowKeyString][columnKeyString] = {};

                for (const valueDefinition of values) {
                    const label =
                        valueDefinition.label ||
                        `${valueDefinition.aggregation.toUpperCase()} of ${valueDefinition.field}`;

                    const rawValues = columnMap.get(label);

                    result.cells[rowKeyString][columnKeyString][label] =
                        aggregations[valueDefinition.aggregation](
                            rawValues
                        );
                }
            }
        }

        /*
         * Grand totals aggregate all records after filters have been applied.
         */
        for (const valueDefinition of values) {
            const label =
                valueDefinition.label ||
                `${valueDefinition.aggregation.toUpperCase()} of ${valueDefinition.field}`;

            const allValues = filteredRecords.map(
                record => this.calculateValue(
                    record,
                    valueDefinition.field,
                    calculatedFields
                )
            );

            result.grandTotals[label] =
                aggregations[valueDefinition.aggregation](allValues);
        }

        return result;
    }
}


// ---------------------------------------------------------------------------
// 7. OUTPUT HELPERS
// ---------------------------------------------------------------------------

function formatValue(value) {
    if (value === null || value === undefined) {
        return "-";
    }

    if (typeof value === "number") {
        return value.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );
    }

    return String(value);
}


function printPivot(result, title) {
    console.log("\n" + "=".repeat(90));
    console.log(title);
    console.log("=".repeat(90));

    for (const rowKey of result.rows) {
        const rowKeyString = JSON.stringify(rowKey);
        console.log(`\nRow: ${JSON.stringify(rowKey)}`);

        for (const columnKey of result.columns) {
            const columnKeyString = JSON.stringify(columnKey);
            const cell =
                result.cells[rowKeyString]?.[columnKeyString];

            if (!cell) {
                console.log(
                    `  ${JSON.stringify(columnKey)}: no records`
                );
                continue;
            }

            const values = Object.entries(cell)
                .map(
                    ([label, value]) =>
                        `${label}=${formatValue(value)}`
                )
                .join(", ");

            console.log(
                `  ${JSON.stringify(columnKey)}: ${values}`
            );
        }
    }

    console.log("\nGrand Totals:");

    for (const [label, value] of Object.entries(
        result.grandTotals
    )) {
        console.log(
            `  ${label}: ${formatValue(value)}`
        );
    }
}


// ---------------------------------------------------------------------------
// 8. BASIC PIVOT
// ---------------------------------------------------------------------------

const engine = new PivotEngine(salesData);

const salesByRegion = engine.build({
    rows: ["region"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Total Sales"
        }
    ]
});

printPivot(
    salesByRegion,
    "Example 1 - Sales by Region"
);


// ---------------------------------------------------------------------------
// 9. ROWS + COLUMNS
// ---------------------------------------------------------------------------

const regionProductPivot = engine.build({
    rows: ["region"],
    columns: ["product"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Total Sales"
        }
    ]
});

printPivot(
    regionProductPivot,
    "Example 2 - Sales by Region and Product"
);


// ---------------------------------------------------------------------------
// 10. MULTIPLE VALUE FIELDS
// ---------------------------------------------------------------------------

const categoryMetricsPivot = engine.build({
    rows: ["category"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Total Sales"
        },
        {
            field: "profit",
            aggregation: "sum",
            label: "Total Profit"
        },
        {
            field: "quantity",
            aggregation: "average",
            label: "Average Quantity"
        },
        {
            field: "orderId",
            aggregation: "count",
            label: "Order Count"
        }
    ]
});

printPivot(
    categoryMetricsPivot,
    "Example 3 - Multiple Metrics by Category"
);


// ---------------------------------------------------------------------------
// 11. FILTERS
// ---------------------------------------------------------------------------

const corporateNorthSouth = engine.build({
    rows: ["product"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Corporate Sales"
        },
        {
            field: "profit",
            aggregation: "sum",
            label: "Corporate Profit"
        }
    ],
    filters: {
        region: ["North", "South"],
        "customer type": ["Corporate"]
    }
});

printPivot(
    corporateNorthSouth,
    "Example 4 - Corporate Sales in North and South"
);


// ---------------------------------------------------------------------------
// 12. DATE GROUPING
// ---------------------------------------------------------------------------

const monthlySales = engine.build({
    rows: ["order date"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Monthly Sales"
        }
    ],
    rowGrouping: {
        "order date": "month"
    }
});

printPivot(
    monthlySales,
    "Example 5 - Monthly Sales"
);


const quarterlySales = engine.build({
    rows: ["order date"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Quarterly Sales"
        }
    ],
    rowGrouping: {
        "order date": "quarter"
    }
});

printPivot(
    quarterlySales,
    "Example 6 - Quarterly Sales"
);


// ---------------------------------------------------------------------------
// 13. NUMERIC GROUPING
// ---------------------------------------------------------------------------

const quantityBands = engine.build({
    rows: ["quantity"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Sales"
        },
        {
            field: "quantity",
            aggregation: "count",
            label: "Transaction Count"
        }
    ],
    rowGrouping: {
        quantity: "quantityBand"
    }
});

printPivot(
    quantityBands,
    "Example 7 - Quantity Bands"
);


// ---------------------------------------------------------------------------
// 14. CALCULATED FIELDS
// ---------------------------------------------------------------------------

const calculatedFields = {
    calculatedProfit(record) {
        return (
            record.quantity * record.unitPrice
            - record.quantity * record.unitCost
        );
    },

    calculatedMargin(record) {
        const sales =
            record.quantity * record.unitPrice;

        const profit =
            record.quantity * record.unitPrice
            - record.quantity * record.unitCost;

        return sales === 0 ? 0 : profit / sales;
    },

    salesIncludingTax(record) {
        const sales =
            record.quantity * record.unitPrice;

        return sales * 1.18;
    }
};


const calculatedPivot = engine.build({
    rows: ["region"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Total Sales"
        },
        {
            field: "calculatedProfit",
            aggregation: "sum",
            label: "Calculated Profit"
        },
        {
            field: "calculatedMargin",
            aggregation: "average",
            label: "Average Margin"
        }
    ],
    calculatedFields
});

printPivot(
    calculatedPivot,
    "Example 8 - Calculated Fields"
);


// ---------------------------------------------------------------------------
// 15. DRILL-DOWN
// ---------------------------------------------------------------------------

function drillDown(records, criteria) {
    return records.filter(record => {
        return Object.entries(criteria).every(
            ([fieldName, expectedValue]) => {
                return getFieldValue(
                    record,
                    fieldName
                ) === expectedValue;
            }
        );
    });
}


const northLaptopRecords = drillDown(
    salesData,
    {
        region: "North",
        product: "Laptop"
    }
);

console.log("\n" + "=".repeat(90));
console.log("Example 9 - Drill-Down: North + Laptop");
console.log("=".repeat(90));

console.table(northLaptopRecords);


// ---------------------------------------------------------------------------
// 16. SUBTOTALS
// ---------------------------------------------------------------------------

function subtotalByField(records, fieldName, measureField) {
    const totals = new Map();

    for (const record of records) {
        const dimensionValue =
            getFieldValue(record, fieldName);

        const measureValue =
            Number(
                getFieldValue(
                    record,
                    measureField
                )
            );

        totals.set(
            dimensionValue,
            (totals.get(dimensionValue) || 0)
            + measureValue
        );
    }

    return totals;
}


const categorySubtotals = subtotalByField(
    salesData,
    "category",
    "sales"
);

console.log("\n" + "=".repeat(90));
console.log("Example 10 - Category Subtotals");
console.log("=".repeat(90));

for (const [category, total] of categorySubtotals) {
    console.log(
        `${category}: ${formatValue(total)}`
    );
}


// ---------------------------------------------------------------------------
// 17. PERCENTAGE OF GRAND TOTAL
// ---------------------------------------------------------------------------

const grandTotalSales =
    [...categorySubtotals.values()]
        .reduce((sum, value) => sum + value, 0);

console.log("\n" + "=".repeat(90));
console.log("Example 11 - Percentage of Grand Total");
console.log("=".repeat(90));

for (const [category, total] of categorySubtotals) {
    const percentage =
        grandTotalSales === 0
            ? 0
            : total / grandTotalSales * 100;

    console.log(
        `${category}: ${formatValue(total)} ` +
        `(${percentage.toFixed(2)}%)`
    );
}


// ---------------------------------------------------------------------------
// 18. RUNNING TOTAL
// ---------------------------------------------------------------------------

function monthlySalesMap(records) {
    const totals = new Map();

    for (const record of records) {
        const month =
            groupDate(record.orderDate, "month");

        const sales =
            getFieldValue(record, "sales");

        totals.set(
            month,
            (totals.get(month) || 0) + sales
        );
    }

    return totals;
}


const monthlySalesMapResult =
    monthlySalesMap(salesData);

let runningTotal = 0;

console.log("\n" + "=".repeat(90));
console.log("Example 12 - Running Total");
console.log("=".repeat(90));

for (const [month, sales] of
    [...monthlySalesMapResult.entries()].sort()) {

    runningTotal += sales;

    console.log(
        `${month}: monthly=${formatValue(sales)}, ` +
        `running=${formatValue(runningTotal)}`
    );
}


// ---------------------------------------------------------------------------
// 19. TOP-N ANALYSIS
// ---------------------------------------------------------------------------

const productSubtotals = subtotalByField(
    salesData,
    "product",
    "sales"
);

const topThreeProducts =
    [...productSubtotals.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);

console.log("\n" + "=".repeat(90));
console.log("Example 13 - Top Three Products");
console.log("=".repeat(90));

topThreeProducts.forEach(
    ([product, sales], index) => {
        console.log(
            `${index + 1}. ${product}: ${formatValue(sales)}`
        );
    }
);


// ---------------------------------------------------------------------------
// 20. SOURCE VALIDATION
// ---------------------------------------------------------------------------

function validateSourceData(records) {
    const errors = [];
    const orderIds = new Set();

    records.forEach((record, index) => {
        if (!record.orderId) {
            errors.push(
                `Row ${index + 1}: missing order ID.`
            );
        }

        if (orderIds.has(record.orderId)) {
            errors.push(
                `Duplicate order ID: ${record.orderId}`
            );
        }

        orderIds.add(record.orderId);

        if (!Number.isInteger(record.quantity) ||
            record.quantity < 0) {
            errors.push(
                `Invalid quantity for ${record.orderId}.`
            );
        }

        if (!Number.isFinite(record.unitPrice) ||
            record.unitPrice < 0) {
            errors.push(
                `Invalid unit price for ${record.orderId}.`
            );
        }

        if (!Number.isFinite(record.unitCost) ||
            record.unitCost < 0) {
            errors.push(
                `Invalid unit cost for ${record.orderId}.`
            );
        }

        if (!record.region) {
            errors.push(
                `Missing region for ${record.orderId}.`
            );
        }

        const date =
            new Date(`${record.orderDate}T00:00:00`);

        if (Number.isNaN(date.getTime())) {
            errors.push(
                `Invalid order date for ${record.orderId}.`
            );
        }
    });

    return errors;
}


const validationErrors =
    validateSourceData(salesData);

console.log("\n" + "=".repeat(90));
console.log("Example 14 - Source Validation");
console.log("=".repeat(90));

if (validationErrors.length === 0) {
    console.log("Source data passed validation.");
} else {
    validationErrors.forEach(
        error => console.log("ERROR:", error)
    );
}


// ---------------------------------------------------------------------------
// 21. DISTINCT COUNT
// ---------------------------------------------------------------------------

const customerExample = [
    "Customer-A",
    "Customer-B",
    "Customer-A",
    "Customer-C",
    "Customer-B"
];

console.log("\n" + "=".repeat(90));
console.log("Example 15 - Distinct Count");
console.log("=".repeat(90));

console.log(
    "COUNT:",
    customerExample.length
);

console.log(
    "DISTINCT COUNT:",
    new Set(customerExample).size
);


// ---------------------------------------------------------------------------
// 22. CUSTOM SORTING
// ---------------------------------------------------------------------------
//
// Alphabetical sorting is not always the correct business ordering.
//
// A custom fiscal-quarter order or manually defined category order can be
// necessary in a real report.

const preferredRegionOrder = [
    "North",
    "South",
    "East",
    "West"
];

const customRegionComparator =
    (a, b) =>
        preferredRegionOrder.indexOf(a)
        - preferredRegionOrder.indexOf(b);

console.log("\n" + "=".repeat(90));
console.log("Example 16 - Custom Business Sorting");
console.log("=".repeat(90));

console.log(
    [...new Set(salesData.map(record => record.region))]
        .sort(customRegionComparator)
);


// ---------------------------------------------------------------------------
// 23. PERFORMANCE: STREAMING AGGREGATION
// ---------------------------------------------------------------------------
//
// A naive pivot implementation can retain every value for every cell.
// For SUM, a streaming accumulator is more memory efficient.
//
// Time complexity for one measure is approximately O(N).
// Space is approximately O(K), where K is the number of distinct groups.

function streamingSum(records, dimensionField, measureField) {
    const totals = new Map();

    for (const record of records) {
        const dimension =
            getFieldValue(record, dimensionField);

        const measure =
            Number(
                getFieldValue(record, measureField)
            );

        totals.set(
            dimension,
            (totals.get(dimension) || 0) + measure
        );
    }

    return totals;
}


console.log("\n" + "=".repeat(90));
console.log("Example 17 - Streaming SUM");
console.log("=".repeat(90));

console.log(
    [...streamingSum(
        salesData,
        "region",
        "sales"
    ).entries()]
);


// ---------------------------------------------------------------------------
// 24. SAFE NUMERIC NORMALIZATION
// ---------------------------------------------------------------------------

function normalizeNumeric(value) {
    if (value === null ||
        value === undefined ||
        value === "") {
        return null;
    }

    if (typeof value === "boolean") {
        return null;
    }

    if (typeof value === "number") {
        return Number.isFinite(value)
            ? value
            : null;
    }

    if (typeof value === "string") {
        const cleaned =
            value.replace(/,/g, "").trim();

        if (cleaned === "") {
            return null;
        }

        const parsed = Number(cleaned);

        return Number.isFinite(parsed)
            ? parsed
            : null;
    }

    return null;
}


console.log("\n" + "=".repeat(90));
console.log("Example 18 - Data Normalization");
console.log("=".repeat(90));

[
    "1,250.50",
    "500",
    "",
    null,
    "not a number",
    250
].forEach(value => {
    console.log(
        JSON.stringify(value),
        "=>",
        normalizeNumeric(value)
    );
});


// ---------------------------------------------------------------------------
// 25. EVENT-DRIVEN / ASYNCHRONOUS REFRESH SIMULATION
// ---------------------------------------------------------------------------
//
// Excel Pivot Tables can be refreshed after the source data changes.
// JavaScript is naturally suited to modeling asynchronous application
// workflows.
//
// This function simulates an asynchronous data refresh without any network
// dependency.

function refreshPivotAsync(records, configuration) {
    return new Promise(resolve => {
        setTimeout(() => {
            const refreshedEngine =
                new PivotEngine(records);

            resolve(
                refreshedEngine.build(configuration)
            );
        }, 10);
    });
}


async function demonstrateAsyncRefresh() {
    const refreshedPivot =
        await refreshPivotAsync(
            salesData,
            {
                rows: ["region"],
                values: [
                    {
                        field: "sales",
                        aggregation: "sum",
                        label: "Refreshed Sales"
                    }
                ]
            }
        );

    console.log("\n" + "=".repeat(90));
    console.log("Example 19 - Asynchronous Pivot Refresh");
    console.log("=".repeat(90));

    console.log(
        refreshedPivot.grandTotals
    );
}


// ---------------------------------------------------------------------------
// 26. ADVANCED MANAGEMENT PIVOT
// ---------------------------------------------------------------------------

const managementPivot = engine.build({
    rows: ["region"],
    columns: ["category"],
    values: [
        {
            field: "sales",
            aggregation: "sum",
            label: "Total Sales"
        },
        {
            field: "profit",
            aggregation: "sum",
            label: "Total Profit"
        }
    ],
    filters: {
        "customer type": ["Corporate"]
    }
});

printPivot(
    managementPivot,
    "Example 20 - Corporate Management Pivot"
);


// ---------------------------------------------------------------------------
// 27. TESTS
// ---------------------------------------------------------------------------

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}


function runTests() {
    const sampleRecord = {
        orderId: "TEST",
        orderDate: "2025-01-01",
        region: "Test",
        salesperson: "Tester",
        product: "Test Product",
        category: "Test",
        quantity: 3,
        unitPrice: 100,
        unitCost: 60,
        customerType: "Retail"
    };

    assert(
        getFieldValue(sampleRecord, "sales") === 300,
        "Sales should equal quantity multiplied by unit price."
    );

    assert(
        getFieldValue(sampleRecord, "profit") === 120,
        "Profit should equal sales minus cost."
    );

    const filtered =
        applyFilters(
            salesData,
            { region: ["North"] }
        );

    assert(
        filtered.length > 0,
        "North filter should return records."
    );

    assert(
        filtered.every(
            record => record.region === "North"
        ),
        "Every filtered record should be North."
    );

    const pivot =
        engine.build({
            rows: ["region"],
            values: [
                {
                    field: "sales",
                    aggregation: "sum",
                    label: "Sales"
                }
            ]
        });

    const expected =
        salesData.reduce(
            (sum, record) =>
                sum + getFieldValue(record, "sales"),
            0
        );

    assert(
        Math.abs(
            pivot.grandTotals.Sales - expected
        ) < Number.EPSILON,
        "Grand total should match source data."
    );

    const drilled =
        drillDown(
            salesData,
            {
                region: "North",
                product: "Laptop"
            }
        );

    assert(
        drilled.every(
            record =>
                record.region === "North" &&
                record.product === "Laptop"
        ),
        "Drill-down should return matching source rows."
    );

    console.log("\nAll JavaScript tests passed.");
}


// ---------------------------------------------------------------------------
// 28. EXECUTION
// ---------------------------------------------------------------------------

runTests();
demonstrateAsyncRefresh()
    .catch(error => {
        console.error(
            "Asynchronous refresh failed:",
            error.message
        );
        process.exitCode = 1;
    });


// ---------------------------------------------------------------------------
// CONCEPTUAL ARCHITECTURE
// ---------------------------------------------------------------------------
//
// A Pivot Table can be understood as:
//
// Source records
//       |
//       v
// Filters
//       |
//       v
// Dimensions
//       |
//       +---- Rows
//       |
//       +---- Columns
//       |
//       +---- Grouping
//       |
//       v
// Measures
//       |
//       +---- SUM
//       +---- COUNT
//       +---- AVERAGE
//       +---- MIN
//       +---- MAX
//       +---- DISTINCT COUNT
//       |
//       v
// Pivot cells
//       |
//       +---- Subtotals
//       +---- Grand totals
//       +---- Percentage analysis
//       +---- Running totals
//       |
//       v
// Drill-down to source records
//
// This architecture is the central computational idea behind Pivot Tables.
