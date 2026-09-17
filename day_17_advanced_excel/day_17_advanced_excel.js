/*
Advanced Excel concepts:
Dynamic arrays, FILTER, SORT, UNIQUE, SEQUENCE, LET, and LAMBDA

This JavaScript file complements the Python study implementation by modeling
the same spreadsheet concepts with JavaScript arrays, higher-order functions,
closures, objects, validation, and asynchronous application-style processing.

The functions are conceptual equivalents of Excel behavior. They do not attempt
to implement the Excel calculation engine.
*/

"use strict";

// =============================================================================
// 1. BASIC ARRAY CONCEPTS
// =============================================================================

console.log("=".repeat(78));
console.log("ADVANCED EXCEL CONCEPTS IN JAVASCRIPT");
console.log("=".repeat(78));

const numbers = [10, 20, 30, 40, 50];

console.log("\nDynamic-array-style data:", numbers);
console.log("Length:", numbers.length);
console.log("First value:", numbers[0]);
console.log("Last value:", numbers[numbers.length - 1]);


// =============================================================================
// 2. SEQUENCE
// =============================================================================

/*
Excel:

    =SEQUENCE(rows, [columns], [start], [step])

JavaScript does not have an exact built-in equivalent, so we implement the
same idea using Array.from().
*/

function sequence(rows, columns = 1, start = 1, step = 1) {
    if (!Number.isInteger(rows) || !Number.isInteger(columns)) {
        throw new TypeError("rows and columns must be integers");
    }

    if (rows < 0 || columns < 0) {
        throw new RangeError("rows and columns cannot be negative");
    }

    const result = [];
    let current = start;

    for (let row = 0; row < rows; row += 1) {
        const currentRow = [];

        for (let column = 0; column < columns; column += 1) {
            currentRow.push(current);
            current += step;
        }

        result.push(currentRow);
    }

    return result;
}

console.log("\nSEQUENCE(5):", sequence(5));
console.log("SEQUENCE(3, 2):", sequence(3, 2));
console.log("SEQUENCE(2, 3, 10, 5):", sequence(2, 3, 10, 5));


// =============================================================================
// 3. FILTER
// =============================================================================

/*
Excel:

    =FILTER(array, include, [if_empty])

JavaScript Array.prototype.filter() directly expresses the same fundamental
idea: retain elements for which a predicate returns true.
*/

function excelFilter(values, predicate, ifEmpty = []) {
    if (!Array.isArray(values)) {
        throw new TypeError("values must be an array");
    }

    if (typeof predicate !== "function") {
        throw new TypeError("predicate must be a function");
    }

    const result = values.filter(predicate);

    return result.length === 0 ? ifEmpty : result;
}

const scores = [45, 82, 91, 58, 76, 94];

const passingScores = excelFilter(
    scores,
    score => score >= 70
);

console.log("\nScores:", scores);
console.log("Scores >= 70:", passingScores);


// =============================================================================
// 4. RECORD-BASED FILTERING
// =============================================================================

const employees = [
    {
        id: 101,
        name: "Asha",
        department: "Technology",
        location: "Delhi",
        salary: 90000,
        performance: 91
    },
    {
        id: 102,
        name: "Ravi",
        department: "Finance",
        location: "Mumbai",
        salary: 82000,
        performance: 84
    },
    {
        id: 103,
        name: "Meera",
        department: "Technology",
        location: "Bengaluru",
        salary: 105000,
        performance: 96
    },
    {
        id: 104,
        name: "Arjun",
        department: "Operations",
        location: "Lucknow",
        salary: 72000,
        performance: 78
    },
    {
        id: 105,
        name: "Neha",
        department: "Finance",
        location: "Delhi",
        salary: 88000,
        performance: 89
    },
    {
        id: 106,
        name: "Kabir",
        department: "Technology",
        location: "Mumbai",
        salary: 97000,
        performance: 87
    },
    {
        id: 107,
        name: "Isha",
        department: "Operations",
        location: "Bengaluru",
        salary: 76000,
        performance: 82
    }
];

const technologyEmployees = excelFilter(
    employees,
    employee => employee.department === "Technology"
);

console.log("\nTechnology employees:");
console.table(technologyEmployees);


// =============================================================================
// 5. AND / OR FILTER CONDITIONS
// =============================================================================

const technologyHighSalary = excelFilter(
    employees,
    employee =>
        employee.department === "Technology" &&
        employee.salary > 90000
);

console.log("\nTechnology employees with salary > 90,000:");
console.table(technologyHighSalary);

const financeOrOperations = excelFilter(
    employees,
    employee =>
        employee.department === "Finance" ||
        employee.department === "Operations"
);

console.log("\nFinance OR Operations:");
console.table(financeOrOperations);


// =============================================================================
// 6. SORT
// =============================================================================

/*
Excel:

    =SORT(array, sort_index, sort_order)

JavaScript's sort() mutates the original array, so a copy is made first.
This is important when the source array should remain unchanged.
*/

function excelSort(values, compareFunction) {
    if (!Array.isArray(values)) {
        throw new TypeError("values must be an array");
    }

    return [...values].sort(compareFunction);
}

const salaryDescending = excelSort(
    employees,
    (a, b) => b.salary - a.salary
);

console.log("\nSalary descending:");
console.table(salaryDescending);


// =============================================================================
// 7. MULTI-KEY SORTING
// =============================================================================

/*
A multi-column Excel SORTBY-style operation can be modeled with a comparator
that evaluates primary, secondary, and tertiary keys.
*/

const multiSorted = excelSort(
    employees,
    (a, b) => {
        if (b.performance !== a.performance) {
            return b.performance - a.performance;
        }

        if (a.department !== b.department) {
            return a.department.localeCompare(b.department);
        }

        return a.name.localeCompare(b.name);
    }
);

console.log("\nPerformance descending, department ascending, name ascending:");
console.table(multiSorted);


// =============================================================================
// 8. UNIQUE
// =============================================================================

/*
Excel:

    =UNIQUE(array)

JavaScript Set preserves insertion order and removes duplicate primitive
values, making it a natural equivalent for simple UNIQUE operations.
*/

function excelUnique(values) {
    if (!Array.isArray(values)) {
        throw new TypeError("values must be an array");
    }

    return [...new Set(values)];
}

const locations = employees.map(employee => employee.location);

console.log("\nLocations:", locations);
console.log("Unique locations:", excelUnique(locations));


// =============================================================================
// 9. UNIQUE EXACTLY ONCE
// =============================================================================

/*
Excel:

    =UNIQUE(array,,TRUE)

The following implementation returns only values whose frequency equals one.
*/

function uniqueExactlyOnce(values) {
    const counts = new Map();

    for (const value of values) {
        counts.set(value, (counts.get(value) || 0) + 1);
    }

    return values.filter(value => counts.get(value) === 1);
}

console.log(
    "Locations appearing exactly once:",
    uniqueExactlyOnce(locations)
);


// =============================================================================
// 10. COMPOSITION
// =============================================================================

/*
Excel-style conceptual formula:

    =SORT(UNIQUE(FILTER(B2:B100, C2:C100="Technology")))

The JavaScript pipeline is:

    FILTER
       ↓
    UNIQUE
       ↓
    SORT
*/

const technologyLocations = excelFilter(
    employees,
    employee => employee.department === "Technology"
).map(employee => employee.location);

const uniqueTechnologyLocations = excelUnique(technologyLocations);

const sortedTechnologyLocations = [...uniqueTechnologyLocations].sort();

console.log(
    "\nSorted unique Technology locations:",
    sortedTechnologyLocations
);


// =============================================================================
// 11. LET AS INTERMEDIATE NAMING
// =============================================================================

/*
Excel LET:

    =LET(
        revenue, B2:B100,
        cost, C2:C100,
        profit, revenue-cost,
        FILTER(profit, profit>0)
    )

JavaScript's const declarations provide a closely related programming idea:
name intermediate calculations once and reuse them.
*/

const revenue = [100, 250, 300, 80, 500];
const cost = [60, 270, 200, 100, 350];

if (revenue.length !== cost.length) {
    throw new Error("Revenue and cost arrays must have equal lengths.");
}

const profit = revenue.map(
    (value, index) => value - cost[index]
);

const profitableValues = excelFilter(
    profit,
    value => value > 0
);

console.log("\nProfit:", profit);
console.log("Positive profit:", profitableValues);


// =============================================================================
// 12. LAMBDA AS A HIGHER-ORDER FUNCTION
// =============================================================================

/*
Excel LAMBDA:

    =LAMBDA(price, rate, price*(1+rate))

JavaScript functions are first-class values, so a function can be stored in a
variable and passed to another function.
*/

const addTax = (price, rate) => price * (1 + rate);

console.log("\n1000 with 18% tax:", addTax(1000, 0.18));

const prices = [100, 250, 500];

const pricesWithTax = prices.map(
    price => addTax(price, 0.18)
);

console.log("Prices with tax:", pricesWithTax);


// =============================================================================
// 13. REUSABLE LAMBDA LIBRARY
// =============================================================================

class LambdaLibrary {
    constructor() {
        this.functions = new Map();
    }

    register(name, functionValue) {
        if (!name || typeof name !== "string") {
            throw new TypeError("Function name must be a non-empty string.");
        }

        if (typeof functionValue !== "function") {
            throw new TypeError("functionValue must be callable.");
        }

        this.functions.set(name, functionValue);
    }

    call(name, ...argumentsList) {
        const functionValue = this.functions.get(name);

        if (!functionValue) {
            throw new Error(`Unknown function: ${name}`);
        }

        return functionValue(...argumentsList);
    }
}

const lambdaLibrary = new LambdaLibrary();

lambdaLibrary.register(
    "DISCOUNT_PRICE",
    (price, discount) => price * (1 - discount)
);

lambdaLibrary.register(
    "GROSS_PROFIT",
    (salesRevenue, totalCost) => salesRevenue - totalCost
);

console.log(
    "\nDiscounted price:",
    lambdaLibrary.call("DISCOUNT_PRICE", 1000, 0.15)
);

console.log(
    "Gross profit:",
    lambdaLibrary.call("GROSS_PROFIT", 1000, 650)
);


// =============================================================================
// 14. LET + LAMBDA-STYLE BUSINESS PIPELINE
// =============================================================================

const sales = [
    {
        id: 1,
        product: "Laptop",
        region: "North",
        units: 4,
        unitPrice: 85000,
        costPerUnit: 65000
    },
    {
        id: 2,
        product: "Monitor",
        region: "West",
        units: 10,
        unitPrice: 18000,
        costPerUnit: 12000
    },
    {
        id: 3,
        product: "Laptop",
        region: "West",
        units: 3,
        unitPrice: 85000,
        costPerUnit: 65000
    },
    {
        id: 4,
        product: "Keyboard",
        region: "North",
        units: 20,
        unitPrice: 3500,
        costPerUnit: 2100
    },
    {
        id: 5,
        product: "Monitor",
        region: "South",
        units: 7,
        unitPrice: 18000,
        costPerUnit: 12000
    },
    {
        id: 6,
        product: "Laptop",
        region: "North",
        units: 2,
        unitPrice: 85000,
        costPerUnit: 65000
    },
    {
        id: 7,
        product: "Keyboard",
        region: "West",
        units: 14,
        unitPrice: 3500,
        costPerUnit: 2100
    }
];

function analyzeSales(salesData, targetRegion, minimumProfit = 0) {
    /*
    This function models a LET-style calculation:
        1. filter
        2. calculate intermediate fields
        3. filter by calculated profit
        4. sort
    */

    const filteredSales = excelFilter(
        salesData,
        sale => sale.region === targetRegion
    );

    const calculatedSales = filteredSales.map(sale => {
        const revenueValue = sale.units * sale.unitPrice;
        const costValue = sale.units * sale.costPerUnit;
        const profitValue = revenueValue - costValue;

        return {
            ...sale,
            revenue: revenueValue,
            cost: costValue,
            profit: profitValue,
            margin: revenueValue === 0
                ? null
                : profitValue / revenueValue
        };
    });

    const profitableSales = excelFilter(
        calculatedSales,
        sale => sale.profit >= minimumProfit
    );

    return excelSort(
        profitableSales,
        (a, b) => b.profit - a.profit
    );
}

console.log("\nWest region sales analysis:");
console.table(analyzeSales(sales, "West", 10000));


// =============================================================================
// 15. EMPTY FILTER RESULTS
// =============================================================================

const eastSales = excelFilter(
    sales,
    sale => sale.region === "East",
    ["No matching records"]
);

console.log("\nEast-region result:", eastSales);


// =============================================================================
// 16. ERROR HANDLING
// =============================================================================

function safeMargin(revenueValue, costValue) {
    if (!Number.isFinite(revenueValue) ||
        !Number.isFinite(costValue)) {
        throw new TypeError("Revenue and cost must be finite numbers.");
    }

    if (revenueValue === 0) {
        return null;
    }

    return (revenueValue - costValue) / revenueValue;
}

const marginCases = [
    [1000, 600],
    [100, 100],
    [0, 100],
    [-100, 50]
];

console.log("\nMargin edge cases:");

for (const [revenueValue, costValue] of marginCases) {
    console.log(
        revenueValue,
        costValue,
        safeMargin(revenueValue, costValue)
    );
}


// =============================================================================
// 17. VALIDATION
// =============================================================================

function validateParallelArrays(...arrays) {
    if (arrays.length === 0) {
        return;
    }

    const expectedLength = arrays[0].length;

    arrays.forEach((array, index) => {
        if (array.length !== expectedLength) {
            throw new Error(
                `Array ${index + 1} has length ${array.length}; ` +
                `expected ${expectedLength}.`
            );
        }
    });
}

try {
    validateParallelArrays(
        [1, 2, 3],
        ["A", "B"]
    );
} catch (error) {
    console.log("\nValidation error:", error.message);
}


// =============================================================================
// 18. ASYNCHRONOUS APPLICATION-STYLE PIPELINE
// =============================================================================

/*
Excel formulas are normally recalculated by the workbook calculation engine.
JavaScript applications often perform data processing asynchronously.

This function simulates receiving spreadsheet-like records from an external
application layer before applying FILTER, calculated columns, and SORT.
*/

async function loadSalesData() {
    return structuredClone(sales);
}

async function asynchronousAnalysis(region) {
    const sourceData = await loadSalesData();

    const result = analyzeSales(
        sourceData,
        region,
        10000
    );

    return result;
}

asynchronousAnalysis("North")
    .then(result => {
        console.log("\nAsynchronous North analysis:");
        console.table(result);
    })
    .catch(error => {
        console.error("Analysis failed:", error.message);
    });


// =============================================================================
// 19. PERFORMANCE CONSIDERATIONS
// =============================================================================

/*
FILTER is generally O(n).
UNIQUE with Set/Map is approximately O(n).
SORT is generally O(n log n).

Avoid unnecessary copies of very large arrays when mutation is acceptable.
On the other hand, copying before sort protects source data from mutation.

Excel has its own calculation engine and dependency graph, so actual workbook
performance depends on formula structure, range sizes, volatility, and
recalculation dependencies.
*/

function performanceExample(values, threshold) {
    // One linear pass rather than repeatedly scanning the same array.
    return values.filter(value => value > threshold);
}

const sampleLargeArray = Array.from(
    { length: 100000 },
    (_, index) => index
);

console.log(
    "\nPerformance example result count:",
    performanceExample(sampleLargeArray, 99990).length
);


// =============================================================================
// 20. SIMPLE TEST FRAMEWORK
// =============================================================================

function assertEqual(actual, expected, testName) {
    const actualJson = JSON.stringify(actual);
    const expectedJson = JSON.stringify(expected);

    if (actualJson !== expectedJson) {
        throw new Error(
            `${testName} failed.\n` +
            `Expected: ${expectedJson}\n` +
            `Actual:   ${actualJson}`
        );
    }

    console.log(`PASS: ${testName}`);
}

function runTests() {
    assertEqual(
        sequence(3),
        [[1], [2], [3]],
        "SEQUENCE"
    );

    assertEqual(
        excelFilter(
            [1, 2, 3],
            value => value > 1
        ),
        [2, 3],
        "FILTER"
    );

    assertEqual(
        excelUnique(["A", "B", "A"]),
        ["A", "B"],
        "UNIQUE"
    );

    assertEqual(
        excelSort([3, 1, 2], (a, b) => a - b),
        [1, 2, 3],
        "SORT"
    );

    assertEqual(
        addTax(100, 0.10),
        110,
        "LAMBDA-style function"
    );

    console.log("All JavaScript tests passed.");
}

runTests();


// =============================================================================
// 21. CONCEPTUAL QUICK REFERENCE
// =============================================================================

const quickReference = {
    "Dynamic arrays":
        "One formula can produce multiple worksheet cells.",
    "Spill":
        "Automatic placement of a dynamic-array result.",
    "FILTER":
        "Retains values satisfying a condition.",
    "SORT":
        "Returns values in a selected order.",
    "UNIQUE":
        "Returns distinct values.",
    "SEQUENCE":
        "Generates numeric arrays.",
    "LET":
        "Names intermediate calculations.",
    "LAMBDA":
        "Creates reusable custom functions."
};

console.log("\nQuick reference:");

for (const [concept, meaning] of Object.entries(quickReference)) {
    console.log(`${concept}: ${meaning}`);
}

console.log("\nJavaScript study implementation completed.");
