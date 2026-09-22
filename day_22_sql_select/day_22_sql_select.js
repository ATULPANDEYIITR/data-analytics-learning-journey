/*
SQL SELECT: SELECT, FROM, aliases, DISTINCT, expressions, and calculated columns

This standalone Node.js program teaches the conceptual and practical behavior
of SQL SELECT statements through executable examples.

Node.js itself does not include a relational database driver in its standard
library, so this file implements a small in-memory relational data model for
demonstrating the same operations in JavaScript. The examples deliberately
mirror real SQL concepts while also demonstrating how application code can
prepare, validate, transform, and consume SELECT-style results.

For actual SQL execution, the SQL strings shown in the examples can be used
with a database driver such as sqlite3, better-sqlite3, pg, mysql2, or another
database-specific client.
*/

// -----------------------------------------------------------------------------
// 1. Sample relational data
// -----------------------------------------------------------------------------

const departments = [
  { department_id: 1, department_name: "Technology" },
  { department_id: 2, department_name: "Finance" },
  { department_id: 3, department_name: "Operations" },
  { department_id: 4, department_name: "Human Resources" }
];

const employees = [
  {
    employee_id: 1,
    first_name: "Aarav",
    last_name: "Sharma",
    department_id: 1,
    job_title: "Software Engineer",
    salary: 85000,
    city: "Lucknow",
    hire_date: "2022-04-10",
    active: 1
  },
  {
    employee_id: 2,
    first_name: "Meera",
    last_name: "Singh",
    department_id: 1,
    job_title: "Data Analyst",
    salary: 72000,
    city: "Delhi",
    hire_date: "2023-01-15",
    active: 1
  },
  {
    employee_id: 3,
    first_name: "Rohan",
    last_name: "Verma",
    department_id: 2,
    job_title: "Financial Analyst",
    salary: 78000,
    city: "Mumbai",
    hire_date: "2021-08-20",
    active: 1
  },
  {
    employee_id: 4,
    first_name: "Isha",
    last_name: "Patel",
    department_id: 3,
    job_title: "Operations Manager",
    salary: 92000,
    city: "Pune",
    hire_date: "2020-02-12",
    active: 1
  },
  {
    employee_id: 5,
    first_name: "Kabir",
    last_name: "Khan",
    department_id: 3,
    job_title: "Operations Analyst",
    salary: 65000,
    city: "Lucknow",
    hire_date: "2024-03-05",
    active: 1
  },
  {
    employee_id: 6,
    first_name: "Nisha",
    last_name: "Gupta",
    department_id: 4,
    job_title: "HR Specialist",
    salary: null,
    city: "Delhi",
    hire_date: "2023-09-18",
    active: 1
  },
  {
    employee_id: 7,
    first_name: "Dev",
    last_name: "Joshi",
    department_id: 1,
    job_title: "Software Engineer",
    salary: 88000,
    city: "Bengaluru",
    hire_date: "2019-11-01",
    active: 0
  }
];

const products = [
  {
    product_id: 1,
    product_name: "Laptop Pro 14",
    category: "Computers",
    unit_price: 1200,
    cost_price: 850,
    stock_quantity: 25,
    supplier: "TechSource"
  },
  {
    product_id: 2,
    product_name: "Mechanical Keyboard",
    category: "Accessories",
    unit_price: 95,
    cost_price: 55,
    stock_quantity: 80,
    supplier: "KeyWorks"
  },
  {
    product_id: 3,
    product_name: "Wireless Mouse",
    category: "Accessories",
    unit_price: 45,
    cost_price: 20,
    stock_quantity: 150,
    supplier: "KeyWorks"
  },
  {
    product_id: 4,
    product_name: "4K Monitor",
    category: "Displays",
    unit_price: 450,
    cost_price: 310,
    stock_quantity: 40,
    supplier: "VisionTech"
  },
  {
    product_id: 5,
    product_name: "USB-C Hub",
    category: "Accessories",
    unit_price: 65,
    cost_price: 32,
    stock_quantity: 0,
    supplier: "PortWorks"
  },
  {
    product_id: 6,
    product_name: "Server Rack",
    category: "Infrastructure",
    unit_price: 900,
    cost_price: 690,
    stock_quantity: 10,
    supplier: null
  }
];

const sales = [
  {
    sale_id: 1,
    product_id: 1,
    employee_id: 1,
    quantity: 2,
    unit_price: 1200,
    discount_rate: 0.10,
    sale_date: "2026-01-05",
    region: "North"
  },
  {
    sale_id: 2,
    product_id: 2,
    employee_id: 2,
    quantity: 5,
    unit_price: 95,
    discount_rate: 0.05,
    sale_date: "2026-01-06",
    region: "North"
  },
  {
    sale_id: 3,
    product_id: 3,
    employee_id: 3,
    quantity: 10,
    unit_price: 45,
    discount_rate: 0,
    sale_date: "2026-01-07",
    region: "West"
  },
  {
    sale_id: 4,
    product_id: 4,
    employee_id: 4,
    quantity: 3,
    unit_price: 450,
    discount_rate: 0.08,
    sale_date: "2026-01-09",
    region: "West"
  },
  {
    sale_id: 5,
    product_id: 5,
    employee_id: 5,
    quantity: 7,
    unit_price: 65,
    discount_rate: 0.15,
    sale_date: "2026-01-12",
    region: "North"
  },
  {
    sale_id: 6,
    product_id: 1,
    employee_id: 2,
    quantity: 1,
    unit_price: 1200,
    discount_rate: 0,
    sale_date: "2026-01-15",
    region: "South"
  },
  {
    sale_id: 7,
    product_id: 6,
    employee_id: 4,
    quantity: 2,
    unit_price: 900,
    discount_rate: 0.05,
    sale_date: "2026-02-01",
    region: "West"
  },
  {
    sale_id: 8,
    product_id: 3,
    employee_id: 1,
    quantity: 20,
    unit_price: 45,
    discount_rate: 0.10,
    sale_date: "2026-02-03",
    region: "North"
  }
];

// -----------------------------------------------------------------------------
// 2. Utility functions
// -----------------------------------------------------------------------------

function printTitle(title) {
  console.log("\n" + "=".repeat(78));
  console.log(title);
  console.log("=".repeat(78));
}

function printRows(rows) {
  if (rows.length === 0) {
    console.log("(no rows)");
    return;
  }

  const columns = [...new Set(rows.flatMap(row => Object.keys(row)))];

  const widths = {};
  for (const column of columns) {
    widths[column] = Math.max(
      column.length,
      ...rows.map(row => String(row[column] ?? "NULL").length)
    );
  }

  const header = columns
    .map(column => column.padEnd(widths[column]))
    .join(" | ");

  const separator = columns
    .map(column => "-".repeat(widths[column]))
    .join("-+-");

  console.log(header);
  console.log(separator);

  for (const row of rows) {
    console.log(
      columns
        .map(column => String(row[column] ?? "NULL").padEnd(widths[column]))
        .join(" | ")
    );
  }

  console.log(`\nRows: ${rows.length}`);
}

function showQuery(description, sql, rows) {
  printTitle(description);
  console.log("SQL:");
  console.log(sql.trim());
  console.log("\nResult:");
  printRows(rows);
}

// -----------------------------------------------------------------------------
// 3. SELECT and FROM concepts
// -----------------------------------------------------------------------------

function demonstrateSelectFrom() {
  const sql = `
SELECT first_name, last_name, job_title
FROM employees;
`;

  // SELECT chooses output columns. FROM identifies the source table.
  const rows = employees.map(employee => ({
    first_name: employee.first_name,
    last_name: employee.last_name,
    job_title: employee.job_title
  }));

  showQuery("1. SELECT and FROM", sql, rows);

  const oneColumnSql = `
SELECT first_name
FROM employees;
`;

  const oneColumnRows = employees.map(employee => ({
    first_name: employee.first_name
  }));

  showQuery("2. Selecting one column", oneColumnSql, oneColumnRows);

  // SELECT * conceptually means every available column.
  const allColumnsSql = `
SELECT *
FROM products;
`;

  showQuery("3. SELECT *", allColumnsSql, products);
}

// -----------------------------------------------------------------------------
// 4. Column aliases
// -----------------------------------------------------------------------------

function demonstrateAliases() {
  const sql = `
SELECT
    first_name AS employee_first_name,
    last_name AS employee_last_name,
    salary AS annual_salary
FROM employees;
`;

  const rows = employees.map(employee => ({
    employee_first_name: employee.first_name,
    employee_last_name: employee.last_name,
    annual_salary: employee.salary
  }));

  showQuery("4. Column aliases", sql, rows);

  const calculatedSql = `
SELECT
    product_name,
    unit_price,
    unit_price * 1.18 AS price_with_tax
FROM products;
`;

  const calculatedRows = products.map(product => ({
    product_name: product.product_name,
    unit_price: product.unit_price,
    price_with_tax: Number((product.unit_price * 1.18).toFixed(2))
  }));

  showQuery("5. Alias for a calculated column", calculatedSql, calculatedRows);
}

// -----------------------------------------------------------------------------
// 5. DISTINCT
// -----------------------------------------------------------------------------

function distinctBy(rows, keySelector) {
  const seen = new Set();
  const result = [];

  for (const row of rows) {
    const key = keySelector(row);

    if (!seen.has(key)) {
      seen.add(key);
      result.push(row);
    }
  }

  return result;
}

function demonstrateDistinct() {
  const sql = `
SELECT DISTINCT city
FROM employees;
`;

  const rows = distinctBy(
    employees.map(employee => ({ city: employee.city })),
    row => row.city
  );

  showQuery("6. DISTINCT cities", sql, rows);

  // DISTINCT applies to the complete selected combination.
  const pairSql = `
SELECT DISTINCT city, job_title
FROM employees;
`;

  const pairRows = distinctBy(
    employees.map(employee => ({
      city: employee.city,
      job_title: employee.job_title
    })),
    row => `${row.city}\u0000${row.job_title}`
  );

  showQuery("7. DISTINCT across multiple columns", pairSql, pairRows);
}

// -----------------------------------------------------------------------------
// 6. Expressions and calculated columns
// -----------------------------------------------------------------------------

function roundMoney(value) {
  return Number(value.toFixed(2));
}

function demonstrateExpressions() {
  const sql = `
SELECT
    product_name,
    unit_price,
    cost_price,
    unit_price - cost_price AS gross_margin,
    (unit_price - cost_price) / unit_price AS margin_ratio
FROM products;
`;

  const rows = products.map(product => ({
    product_name: product.product_name,
    unit_price: product.unit_price,
    cost_price: product.cost_price,
    gross_margin: roundMoney(product.unit_price - product.cost_price),
    margin_ratio: Number(
      ((product.unit_price - product.cost_price) / product.unit_price).toFixed(4)
    )
  }));

  showQuery("8. Expressions and calculated columns", sql, rows);

  const salesSql = `
SELECT
    sale_id,
    quantity * unit_price AS gross_revenue,
    quantity * unit_price * discount_rate AS discount_amount,
    quantity * unit_price * (1 - discount_rate) AS net_revenue
FROM sales;
`;

  const salesRows = sales.map(sale => {
    const grossRevenue = sale.quantity * sale.unit_price;
    const discountAmount = grossRevenue * sale.discount_rate;
    const netRevenue = grossRevenue - discountAmount;

    return {
      sale_id: sale.sale_id,
      gross_revenue: roundMoney(grossRevenue),
      discount_amount: roundMoney(discountAmount),
      net_revenue: roundMoney(netRevenue)
    };
  });

  showQuery("9. Sales calculations", salesSql, salesRows);
}

// -----------------------------------------------------------------------------
// 7. String expressions
// -----------------------------------------------------------------------------

function demonstrateStringExpressions() {
  const sql = `
SELECT
    first_name || ' ' || last_name AS full_name
FROM employees;
`;

  const rows = employees.map(employee => ({
    full_name: `${employee.first_name} ${employee.last_name}`
  }));

  showQuery("10. String concatenation", sql, rows);

  const transformSql = `
SELECT
    product_name,
    UPPER(product_name) AS uppercase_name,
    LOWER(category) AS lowercase_category,
    LENGTH(product_name) AS name_length
FROM products;
`;

  const transformedRows = products.map(product => ({
    product_name: product.product_name,
    uppercase_name: product.product_name.toUpperCase(),
    lowercase_category: product.category.toLowerCase(),
    name_length: product.product_name.length
  }));

  showQuery("11. String functions", transformSql, transformedRows);
}

// -----------------------------------------------------------------------------
// 8. NULL behavior
// -----------------------------------------------------------------------------

function coalesce(value, fallback) {
  return value === null || value === undefined ? fallback : value;
}

function demonstrateNull() {
  const sql = `
SELECT
    first_name,
    salary,
    COALESCE(salary, 0) AS normalized_salary
FROM employees;
`;

  const rows = employees.map(employee => ({
    first_name: employee.first_name,
    salary: employee.salary,
    normalized_salary: coalesce(employee.salary, 0)
  }));

  showQuery("12. NULL and COALESCE", sql, rows);

  // A SQL arithmetic expression involving NULL normally evaluates to NULL.
  // JavaScript has different null semantics, so application developers must
  // explicitly normalize values when reproducing SQL calculations.
  const salarySql = `
SELECT
    first_name,
    salary * 1.10 AS salary_after_raise
FROM employees;
`;

  const salaryRows = employees.map(employee => ({
    first_name: employee.first_name,
    salary_after_raise:
      employee.salary === null
        ? null
        : roundMoney(employee.salary * 1.10)
  }));

  showQuery("13. NULL-aware calculation", salarySql, salaryRows);
}

// -----------------------------------------------------------------------------
// 9. CASE-style conditional expressions
// -----------------------------------------------------------------------------

function salaryBand(salary) {
  if (salary === null) return "Unknown";
  if (salary >= 90000) return "High";
  if (salary >= 70000) return "Medium";
  return "Standard";
}

function inventoryStatus(stock) {
  if (stock === null || stock === undefined) return "Unknown";
  if (stock === 0) return "Out of stock";
  if (stock < 20) return "Low stock";
  return "Available";
}

function demonstrateCase() {
  const sql = `
SELECT
    first_name,
    salary,
    CASE
        WHEN salary IS NULL THEN 'Unknown'
        WHEN salary >= 90000 THEN 'High'
        WHEN salary >= 70000 THEN 'Medium'
        ELSE 'Standard'
    END AS salary_band
FROM employees;
`;

  const rows = employees.map(employee => ({
    first_name: employee.first_name,
    salary: employee.salary,
    salary_band: salaryBand(employee.salary)
  }));

  showQuery("14. CASE expression", sql, rows);

  const inventorySql = `
SELECT
    product_name,
    stock_quantity,
    CASE
        WHEN stock_quantity = 0 THEN 'Out of stock'
        WHEN stock_quantity < 20 THEN 'Low stock'
        ELSE 'Available'
    END AS inventory_status
FROM products;
`;

  const inventoryRows = products.map(product => ({
    product_name: product.product_name,
    stock_quantity: product.stock_quantity,
    inventory_status: inventoryStatus(product.stock_quantity)
  }));

  showQuery("15. Inventory classification", inventorySql, inventoryRows);
}

// -----------------------------------------------------------------------------
// 10. Aggregates
// -----------------------------------------------------------------------------

function average(values) {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function demonstrateAggregates() {
  const sql = `
SELECT
    COUNT(*) AS product_count,
    MIN(unit_price) AS minimum_price,
    MAX(unit_price) AS maximum_price,
    AVG(unit_price) AS average_price
FROM products;
`;

  const prices = products.map(product => product.unit_price);

  const rows = [{
    product_count: products.length,
    minimum_price: Math.min(...prices),
    maximum_price: Math.max(...prices),
    average_price: roundMoney(average(prices))
  }];

  showQuery("16. Aggregate expressions", sql, rows);

  const salesSql = `
SELECT
    SUM(quantity) AS total_units,
    SUM(quantity * unit_price) AS gross_revenue
FROM sales;
`;

  const totalUnits = sales.reduce((sum, sale) => sum + sale.quantity, 0);
  const grossRevenue = sales.reduce(
    (sum, sale) => sum + sale.quantity * sale.unit_price,
    0
  );

  showQuery("17. Sales aggregates", salesSql, [{
    total_units: totalUnits,
    gross_revenue: roundMoney(grossRevenue)
  }]);
}

// -----------------------------------------------------------------------------
// 11. JOIN-style report
// -----------------------------------------------------------------------------

function findById(rows, key, value) {
  return rows.find(row => row[key] === value) ?? null;
}

function demonstrateJoinedReport() {
  /*
  SQL would conceptually perform:
      FROM sales
      JOIN products
          ON products.product_id = sales.product_id
      LEFT JOIN employees
          ON employees.employee_id = sales.employee_id

  The JavaScript implementation below performs the equivalent lookups.
  */
  const sql = `
SELECT
    s.sale_id AS transaction_id,
    p.product_name AS product,
    COALESCE(e.first_name || ' ' || e.last_name, 'Unassigned')
        AS salesperson,
    s.quantity AS units,
    s.quantity * s.unit_price * (1 - s.discount_rate)
        AS net_revenue
FROM sales AS s
JOIN products AS p
    ON p.product_id = s.product_id
LEFT JOIN employees AS e
    ON e.employee_id = s.employee_id;
`;

  const rows = sales.map(sale => {
    const product = findById(products, "product_id", sale.product_id);
    const employee = findById(employees, "employee_id", sale.employee_id);

    const netRevenue =
      sale.quantity *
      sale.unit_price *
      (1 - sale.discount_rate);

    return {
      transaction_id: sale.sale_id,
      product: product?.product_name ?? "Unknown product",
      salesperson: employee
        ? `${employee.first_name} ${employee.last_name}`
        : "Unassigned",
      units: sale.quantity,
      net_revenue: roundMoney(netRevenue)
    };
  });

  showQuery("18. JOIN-style SELECT report", sql, rows);
}

// -----------------------------------------------------------------------------
// 12. Date expressions
// -----------------------------------------------------------------------------

function addDays(isoDate, days) {
  const date = new Date(`${isoDate}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function demonstrateDates() {
  const sql = `
SELECT
    sale_date,
    strftime('%Y', sale_date) AS sale_year,
    strftime('%m', sale_date) AS sale_month
FROM sales;
`;

  const rows = sales.map(sale => ({
    sale_date: sale.sale_date,
    sale_year: sale.sale_date.slice(0, 4),
    sale_month: sale.sale_date.slice(5, 7)
  }));

  showQuery("19. Date expressions", sql, rows);

  const dateSql = `
SELECT
    sale_date,
    date(sale_date, '+30 days') AS thirty_days_later
FROM sales;
`;

  const dateRows = sales.map(sale => ({
    sale_date: sale.sale_date,
    thirty_days_later: addDays(sale.sale_date, 30)
  }));

  showQuery("20. Date arithmetic", dateSql, dateRows);
}

// -----------------------------------------------------------------------------
// 13. DISTINCT performance concept
// -----------------------------------------------------------------------------

function demonstrateDistinctPerformance() {
  const manyRows = Array.from({ length: 100000 }, (_, index) => ({
    city: index % 5 === 0 ? "Lucknow" : index % 2 === 0 ? "Delhi" : "Mumbai"
  }));

  const start = performance.now();

  const uniqueCities = new Set(manyRows.map(row => row.city));

  const elapsed = performance.now() - start;

  printTitle("21. DISTINCT-style deduplication performance");
  console.log(`Input rows: ${manyRows.length}`);
  console.log(`Unique values: ${uniqueCities.size}`);
  console.log(`Elapsed JavaScript time: ${elapsed.toFixed(3)} ms`);
  console.log(
    "Database DISTINCT performance depends on indexes, sorting, hashing, "
    + "cardinality, memory, query planner decisions, and the database engine."
  );
}

// -----------------------------------------------------------------------------
// 14. Validation and safe parameter concept
// -----------------------------------------------------------------------------

function validateCity(city) {
  if (typeof city !== "string") {
    throw new TypeError("City must be a string.");
  }

  const normalized = city.trim();

  if (normalized.length === 0) {
    throw new Error("City cannot be empty.");
  }

  return normalized;
}

function parameterizedSelectByCity(city) {
  /*
  In an actual SQL client, this value should be supplied through a parameter
  placeholder, for example:

      SELECT employee_id, first_name, city
      FROM employees
      WHERE city = ?;

  and the parameter array would contain [city].

  The simulation below filters the local data after validation.
  */
  const safeCity = validateCity(city);

  return employees
    .filter(employee => employee.city === safeCity)
    .map(employee => ({
      employee_id: employee.employee_id,
      first_name: employee.first_name,
      city: employee.city
    }));
}

function demonstrateValidation() {
  printTitle("22. Parameter validation");

  try {
    const rows = parameterizedSelectByCity("Lucknow");
    printRows(rows);
  } catch (error) {
    console.error(error.message);
  }

  try {
    parameterizedSelectByCity("");
  } catch (error) {
    console.log(`Expected validation error: ${error.message}`);
  }
}

// -----------------------------------------------------------------------------
// 15. Test suite
// -----------------------------------------------------------------------------

function assertEqual(actual, expected, testName) {
  if (actual !== expected) {
    throw new Error(
      `${testName}: expected ${JSON.stringify(expected)}, `
      + `received ${JSON.stringify(actual)}`
    );
  }
}

function assertDeepEqual(actual, expected, testName) {
  const actualJson = JSON.stringify(actual);
  const expectedJson = JSON.stringify(expected);

  if (actualJson !== expectedJson) {
    throw new Error(
      `${testName}: expected ${expectedJson}, received ${actualJson}`
    );
  }
}

function runTests() {
  printTitle("23. Automated tests");

  const firstEmployee = employees[0];
  assertEqual(
    firstEmployee.first_name,
    "Aarav",
    "First employee should be Aarav"
  );
  console.log("[PASS] SELECT-style column access");

  const cities = [
    ...new Set(employees.map(employee => employee.city))
  ].sort();

  assertDeepEqual(
    cities,
    ["Bengaluru", "Delhi", "Lucknow", "Mumbai", "Pune"],
    "DISTINCT cities"
  );
  console.log("[PASS] DISTINCT behavior");

  const firstSale = sales[0];
  const grossRevenue = firstSale.quantity * firstSale.unit_price;

  assertEqual(
    grossRevenue,
    2400,
    "Calculated gross revenue"
  );
  console.log("[PASS] Calculated column");

  assertEqual(
    coalesce(null, 0),
    0,
    "COALESCE-style NULL replacement"
  );
  console.log("[PASS] NULL handling");

  assertEqual(
    salaryBand(92000),
    "High",
    "Salary CASE classification"
  );
  console.log("[PASS] CASE expression");

  console.log("All JavaScript tests passed.");
}

// -----------------------------------------------------------------------------
// 16. Complete executive report
// -----------------------------------------------------------------------------

function buildExecutiveReport() {
  const rows = products.map(product => {
    const unitMargin = product.unit_price - product.cost_price;
    const marginPercentage =
      (unitMargin * 100) / product.unit_price;

    return {
      product_id: product.product_id,
      product_name: product.product_name,
      category: product.category,
      unit_price: product.unit_price,
      cost_price: product.cost_price,
      unit_margin: roundMoney(unitMargin),
      margin_percentage: roundMoney(marginPercentage),
      stock_units: coalesce(product.stock_quantity, 0),
      stock_status: inventoryStatus(product.stock_quantity),
      supplier_name: coalesce(product.supplier, "Unknown supplier")
    };
  });

  const sql = `
SELECT
    product_id,
    product_name,
    category,
    unit_price,
    cost_price,
    unit_price - cost_price AS unit_margin,
    (unit_price - cost_price) * 100.0 / unit_price
        AS margin_percentage,
    COALESCE(stock_quantity, 0) AS stock_units,
    CASE
        WHEN COALESCE(stock_quantity, 0) = 0 THEN 'OUT'
        WHEN stock_quantity < 20 THEN 'LOW'
        ELSE 'HEALTHY'
    END AS stock_status,
    COALESCE(supplier, 'Unknown supplier') AS supplier_name
FROM products;
`;

  showQuery("24. Complete product executive report", sql, rows);
}

// -----------------------------------------------------------------------------
// 17. Main
// -----------------------------------------------------------------------------

function main() {
  demonstrateSelectFrom();
  demonstrateAliases();
  demonstrateDistinct();
  demonstrateExpressions();
  demonstrateStringExpressions();
  demonstrateNull();
  demonstrateCase();
  demonstrateAggregates();
  demonstrateJoinedReport();
  demonstrateDates();
  demonstrateDistinctPerformance();
  demonstrateValidation();
  buildExecutiveReport();
  runTests();

  printTitle("25. Completion");
  console.log(
    "The program demonstrated SELECT, FROM, aliases, DISTINCT, expressions, "
    + "calculated columns, NULL handling, CASE expressions, aggregates, "
    + "JOIN-style reporting, date expressions, validation, testing, and "
    + "performance considerations."
  );
}

main();
