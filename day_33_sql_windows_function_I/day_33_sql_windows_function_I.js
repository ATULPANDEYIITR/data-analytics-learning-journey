"use strict";

/*
 * SQL Window Functions I
 *
 * This Node.js program provides a JavaScript-specific model of:
 *
 *   OVER
 *   PARTITION BY
 *   ORDER BY
 *   ROW_NUMBER
 *   RANK
 *   DENSE_RANK
 *
 * The implementation uses JavaScript objects, Maps, higher-order functions,
 * immutable-style row copies, validation, and event-driven reporting.
 *
 * It is intentionally not a line-by-line translation of the Python program.
 * The JavaScript design emphasizes:
 *
 *   - functional transformations
 *   - Map-based partitioning
 *   - stable sorting and deterministic tie-breakers
 *   - event emission
 *   - asynchronous report generation
 *   - serialization of window specifications
 */

const sales = [
  { saleId: 101, employee: "Asha", department: "Engineering", region: "North", amount: 9200 },
  { saleId: 102, employee: "Ravi", department: "Engineering", region: "North", amount: 8700 },
  { saleId: 103, employee: "Meera", department: "Engineering", region: "South", amount: 9200 },
  { saleId: 104, employee: "Kabir", department: "Engineering", region: "South", amount: 7600 },
  { saleId: 105, employee: "Isha", department: "Sales", region: "North", amount: 12500 },
  { saleId: 106, employee: "Arjun", department: "Sales", region: "North", amount: 9800 },
  { saleId: 107, employee: "Neha", department: "Sales", region: "South", amount: 12500 },
  { saleId: 108, employee: "Vikram", department: "Sales", region: "South", amount: 8100 },
  { saleId: 109, employee: "Tara", department: "Finance", region: "North", amount: 6700 },
  { saleId: 110, employee: "Dev", department: "Finance", region: "North", amount: 6700 },
  { saleId: 111, employee: "Pooja", department: "Finance", region: "South", amount: 5900 },
  { saleId: 112, employee: "Nikhil", department: "Finance", region: "South", amount: 5100 }
];


/* -------------------------------------------------------------------------
 * Formatting and validation
 * ------------------------------------------------------------------------- */

function assertArrayOfRows(rows) {
  if (!Array.isArray(rows)) {
    throw new TypeError("Window input must be an array of rows.");
  }

  for (const [index, row] of rows.entries()) {
    if (!row || typeof row !== "object" || Array.isArray(row)) {
      throw new TypeError(`Row ${index} must be an object.`);
    }
  }
}

function requireColumns(rows, columns) {
  assertArrayOfRows(rows);

  if (rows.length === 0) {
    throw new Error("At least one row is required.");
  }

  for (const column of columns) {
    if (!(column in rows[0])) {
      throw new Error(`Missing required column: ${column}`);
    }
  }
}

function cloneRows(rows) {
  return rows.map((row) => ({ ...row }));
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return "NULL";
  }

  return typeof value === "number"
    ? value.toLocaleString("en-US", { maximumFractionDigits: 2 })
    : String(value);
}

function printRows(rows, columns, title) {
  console.log(`\n${title}`);
  console.log("-".repeat(title.length));

  if (rows.length === 0) {
    console.log("(no rows)");
    return;
  }

  const widths = Object.fromEntries(
    columns.map((column) => [
      column,
      Math.max(
        column.length,
        ...rows.map((row) => formatNumber(row[column]).length)
      )
    ])
  );

  const header = columns
    .map((column) => column.padEnd(widths[column]))
    .join(" | ");

  const separator = columns
    .map((column) => "-".repeat(widths[column]))
    .join("-+-");

  console.log(header);
  console.log(separator);

  for (const row of rows) {
    console.log(
      columns
        .map((column) => formatNumber(row[column]).padEnd(widths[column]))
        .join(" | ")
    );
  }
}


/* -------------------------------------------------------------------------
 * PARTITION BY model
 * ------------------------------------------------------------------------- */

function partitionBy(rows, columns) {
  requireColumns(rows, columns);

  /*
   * Map is useful here because a partition is naturally represented as:
   *
   *   partition key -> rows belonging to that partition
   *
   * JSON serialization is avoided as the primary grouping mechanism because
   * Map preserves JavaScript values more directly.
   */
  const partitions = new Map();

  for (const row of rows) {
    const key = columns.map((column) => row[column]).join("\u001F");

    if (!partitions.has(key)) {
      partitions.set(key, {
        values: columns.map((column) => row[column]),
        rows: []
      });
    }

    partitions.get(key).rows.push(row);
  }

  return partitions;
}

function partitionKeyText(values) {
  return values.join(" / ");
}


/* -------------------------------------------------------------------------
 * Window ordering
 * ------------------------------------------------------------------------- */

function compareValues(a, b, descending = false) {
  /*
   * JavaScript's Array.sort comparator must return:
   *   negative -> a before b
   *   zero     -> equivalent
   *   positive -> a after b
   *
   * Handling null-like values explicitly prevents accidental coercion.
   */
  if (a === b) {
    return 0;
  }

  if (a === null || a === undefined) {
    return descending ? 1 : -1;
  }

  if (b === null || b === undefined) {
    return descending ? -1 : 1;
  }

  const comparison = a < b ? -1 : 1;
  return descending ? -comparison : comparison;
}

function sortForWindow(rows, orderBy) {
  return rows
    .map((row, originalIndex) => ({ row, originalIndex }))
    .sort((left, right) => {
      for (const rule of orderBy) {
        const comparison = compareValues(
          left.row[rule.column],
          right.row[rule.column],
          Boolean(rule.descending)
        );

        if (comparison !== 0) {
          return comparison;
        }
      }

      /*
       * Explicitly preserve source order if every ORDER BY expression ties.
       * Production SQL should use a unique tie-breaker when deterministic
       * ROW_NUMBER output is required across executions.
       */
      return left.originalIndex - right.originalIndex;
    })
    .map((entry) => entry.row);
}


/* -------------------------------------------------------------------------
 * OVER specification
 * ------------------------------------------------------------------------- */

class WindowSpecification {
  constructor({ partitionBy = [], orderBy = [] } = {}) {
    if (!Array.isArray(partitionBy) || !Array.isArray(orderBy)) {
      throw new TypeError("partitionBy and orderBy must be arrays.");
    }

    this.partitionBy = [...partitionBy];
    this.orderBy = orderBy.map((rule) => ({
      column: rule.column,
      descending: Boolean(rule.descending)
    }));
  }

  toSQL() {
    const pieces = [];

    if (this.partitionBy.length > 0) {
      pieces.push(`PARTITION BY ${this.partitionBy.join(", ")}`);
    }

    if (this.orderBy.length > 0) {
      const orderText = this.orderBy
        .map(
          (rule) =>
            `${rule.column} ${rule.descending ? "DESC" : "ASC"}`
        )
        .join(", ");

      pieces.push(`ORDER BY ${orderText}`);
    }

    return `OVER (${pieces.join(" ")})`;
  }
}


/* -------------------------------------------------------------------------
 * ROW_NUMBER
 * ------------------------------------------------------------------------- */

function rowNumber(rows, specification) {
  requireColumns(rows, specification.partitionBy);

  if (specification.orderBy.length === 0) {
    throw new Error(
      "This ROW_NUMBER implementation requires an ORDER BY for deterministic output."
    );
  }

  const result = cloneRows(rows);
  const partitions = partitionBy(result, specification.partitionBy);

  for (const partition of partitions.values()) {
    const ordered = sortForWindow(partition.rows, specification.orderBy);

    ordered.forEach((row, index) => {
      row.rowNumber = index + 1;
    });
  }

  return result;
}


/* -------------------------------------------------------------------------
 * RANK
 * ------------------------------------------------------------------------- */

function rank(rows, specification) {
  requireColumns(rows, specification.partitionBy);

  if (specification.orderBy.length !== 1) {
    throw new Error(
      "This RANK implementation expects exactly one ORDER BY expression."
    );
  }

  const result = cloneRows(rows);
  const partitions = partitionBy(result, specification.partitionBy);
  const [rule] = specification.orderBy;

  for (const partition of partitions.values()) {
    const ordered = sortForWindow(partition.rows, [rule]);

    let previousValue = Symbol("no-previous-value");
    let currentRank = 0;

    ordered.forEach((row, index) => {
      const value = row[rule.column];

      if (value !== previousValue) {
        currentRank = index + 1;
        previousValue = value;
      }

      row.rank = currentRank;
    });
  }

  return result;
}


/* -------------------------------------------------------------------------
 * DENSE_RANK
 * ------------------------------------------------------------------------- */

function denseRank(rows, specification) {
  requireColumns(rows, specification.partitionBy);

  if (specification.orderBy.length !== 1) {
    throw new Error(
      "This DENSE_RANK implementation expects exactly one ORDER BY expression."
    );
  }

  const result = cloneRows(rows);
  const partitions = partitionBy(result, specification.partitionBy);
  const [rule] = specification.orderBy;

  for (const partition of partitions.values()) {
    const ordered = sortForWindow(partition.rows, [rule]);

    let previousValue = Symbol("no-previous-value");
    let currentRank = 0;

    for (const row of ordered) {
      const value = row[rule.column];

      if (value !== previousValue) {
        currentRank += 1;
        previousValue = value;
      }

      row.denseRank = currentRank;
    }
  }

  return result;
}


/* -------------------------------------------------------------------------
 * Window aggregation without collapsing rows
 * ------------------------------------------------------------------------- */

function sumOverPartition(rows, partitionColumns, valueColumn) {
  requireColumns(rows, [...partitionColumns, valueColumn]);

  const result = cloneRows(rows);
  const partitions = partitionBy(result, partitionColumns);

  for (const partition of partitions.values()) {
    const total = partition.rows.reduce(
      (sum, row) => sum + Number(row[valueColumn]),
      0
    );

    for (const row of partition.rows) {
      row.partitionTotal = total;
    }
  }

  return result;
}


/* -------------------------------------------------------------------------
 * Top-N analysis
 * ------------------------------------------------------------------------- */

function topNPerGroup(rows, n) {
  if (!Number.isInteger(n) || n < 1) {
    throw new RangeError("n must be a positive integer.");
  }

  const specification = new WindowSpecification({
    partitionBy: ["department"],
    orderBy: [
      { column: "amount", descending: true },
      { column: "saleId", descending: false }
    ]
  });

  const rankedRows = rowNumber(rows, specification);

  return rankedRows.filter((row) => row.rowNumber <= n);
}

function topNWithTies(rows, n) {
  if (!Number.isInteger(n) || n < 1) {
    throw new RangeError("n must be a positive integer.");
  }

  const specification = new WindowSpecification({
    partitionBy: ["department"],
    orderBy: [{ column: "amount", descending: true }]
  });

  const rankedRows = rank(rows, specification);

  return rankedRows.filter((row) => row.rank <= n);
}


/* -------------------------------------------------------------------------
 * Event-driven reporting
 * ------------------------------------------------------------------------- */

class WindowReportEmitter extends EventTarget {
  emit(type, detail) {
    this.dispatchEvent(
      new CustomEvent(type, { detail })
    );
  }
}

async function generateLeaderboardAsync(rows) {
  const emitter = new WindowReportEmitter();

  emitter.addEventListener("partition-created", (event) => {
    console.log(
      `Partition created: ${event.detail.partition} `
      + `(${event.detail.rowCount} rows)`
    );
  });

  emitter.addEventListener("window-complete", (event) => {
    console.log(
      `Window function completed: ${event.detail.functionName}`
    );
  });

  const specification = new WindowSpecification({
    partitionBy: ["department"],
    orderBy: [
      { column: "amount", descending: true },
      { column: "saleId", descending: false }
    ]
  });

  const partitions = partitionBy(rows, specification.partitionBy);

  for (const partition of partitions.values()) {
    emitter.emit("partition-created", {
      partition: partitionKeyText(partition.values),
      rowCount: partition.rows.length
    });

    /*
     * Yield to the event loop. This does not make the CPU-bound calculation
     * parallel. It demonstrates how an event-driven application can report
     * progress without blocking every surrounding task.
     */
    await new Promise((resolve) => setImmediate(resolve));
  }

  let result = rowNumber(rows, specification);
  emitter.emit("window-complete", { functionName: "ROW_NUMBER" });

  result = rank(result, new WindowSpecification({
    partitionBy: ["department"],
    orderBy: [{ column: "amount", descending: true }]
  }));
  emitter.emit("window-complete", { functionName: "RANK" });

  result = denseRank(result, new WindowSpecification({
    partitionBy: ["department"],
    orderBy: [{ column: "amount", descending: true }]
  }));
  emitter.emit("window-complete", { functionName: "DENSE_RANK" });

  return result;
}


/* -------------------------------------------------------------------------
 * CSV-style ingestion
 * ------------------------------------------------------------------------- */

function parseSimpleSalesCSV(csvText) {
  const lines = csvText
    .trim()
    .split(/\r?\n/)
    .filter(Boolean);

  if (lines.length < 2) {
    throw new Error("CSV must contain a header and at least one row.");
  }

  const headers = lines[0].split(",").map((value) => value.trim());

  const required = [
    "saleId",
    "employee",
    "department",
    "region",
    "amount"
  ];

  for (const column of required) {
    if (!headers.includes(column)) {
      throw new Error(`CSV is missing required column '${column}'.`);
    }
  }

  return lines.slice(1).map((line, rowOffset) => {
    const values = line.split(",");

    if (values.length !== headers.length) {
      throw new Error(
        `CSV row ${rowOffset + 2} has ${values.length} values; `
        + `expected ${headers.length}.`
      );
    }

    const row = Object.fromEntries(
      headers.map((header, index) => [
        header,
        values[index].trim()
      ])
    );

    row.saleId = Number(row.saleId);
    row.amount = Number(row.amount);

    if (!Number.isInteger(row.saleId)) {
      throw new Error(`Invalid saleId on CSV row ${rowOffset + 2}.`);
    }

    if (!Number.isFinite(row.amount) || row.amount < 0) {
      throw new Error(`Invalid amount on CSV row ${rowOffset + 2}.`);
    }

    return row;
  });
}


/* -------------------------------------------------------------------------
 * Ranking invariants
 * ------------------------------------------------------------------------- */

function assertRankingInvariants(rows) {
  const partitions = partitionBy(rows, ["department"]);

  for (const partition of partitions.values()) {
    const ordered = sortForWindow(partition.rows, [
      { column: "amount", descending: true },
      { column: "saleId", descending: false }
    ]);

    ordered.forEach((row, index) => {
      if (row.rowNumber !== index + 1) {
        throw new Error(
          `ROW_NUMBER invariant failed in ${partition.values.join("/")}.`
        );
      }
    });

    for (let index = 1; index < ordered.length; index += 1) {
      if (ordered[index].amount > ordered[index - 1].amount) {
        throw new Error("ORDER BY invariant failed.");
      }

      if (ordered[index].rank < ordered[index - 1].rank) {
        throw new Error("RANK must be non-decreasing.");
      }

      if (ordered[index].denseRank < ordered[index - 1].denseRank) {
        throw new Error("DENSE_RANK must be non-decreasing.");
      }
    }
  }
}


/* -------------------------------------------------------------------------
 * A direct comparison showing why the functions are not interchangeable
 * ------------------------------------------------------------------------- */

function demonstrateTieSemantics(rows) {
  const baseSpecification = {
    partitionBy: ["department"],
    orderBy: [{ column: "amount", descending: true }]
  };

  let result = rowNumber(
    rows,
    new WindowSpecification({
      ...baseSpecification,
      orderBy: [
        { column: "amount", descending: true },
        { column: "saleId", descending: false }
      ]
    })
  );

  result = rank(
    result,
    new WindowSpecification(baseSpecification)
  );

  result = denseRank(
    result,
    new WindowSpecification(baseSpecification)
  );

  return result
    .filter((row) => row.department === "Sales")
    .sort((a, b) => a.rowNumber - b.rowNumber);
}


/* -------------------------------------------------------------------------
 * Main executable demonstration
 * ------------------------------------------------------------------------- */

async function main() {
  requireColumns(
    sales,
    ["saleId", "employee", "department", "region", "amount"]
  );

  printRows(
    sales,
    ["saleId", "employee", "department", "region", "amount"],
    "Source rows"
  );

  const departmentTotals = sumOverPartition(
    sales,
    ["department"],
    "amount"
  );

  printRows(
    departmentTotals,
    ["saleId", "employee", "department", "amount", "partitionTotal"],
    "SUM(...) OVER (PARTITION BY department)"
  );

  const rowNumberSpecification = new WindowSpecification({
    partitionBy: ["department"],
    orderBy: [
      { column: "amount", descending: true },
      { column: "saleId", descending: false }
    ]
  });

  const numbered = rowNumber(sales, rowNumberSpecification);

  printRows(
    numbered.sort(
      (a, b) =>
        a.department.localeCompare(b.department)
        || a.rowNumber - b.rowNumber
    ),
    ["department", "rowNumber", "employee", "amount", "saleId"],
    "ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC, saleId)"
  );

  const tied = demonstrateTieSemantics(sales);

  printRows(
    tied,
    ["employee", "amount", "rowNumber", "rank", "denseRank"],
    "Tie semantics in Sales"
  );

  const topTwo = topNPerGroup(sales, 2);

  printRows(
    topTwo.sort(
      (a, b) =>
        a.department.localeCompare(b.department)
        || a.rowNumber - b.rowNumber
    ),
    ["department", "rowNumber", "employee", "amount"],
    "Top two rows per department with ROW_NUMBER"
  );

  const topTwoWithTies = topNWithTies(sales, 2);

  printRows(
    topTwoWithTies.sort(
      (a, b) =>
        a.department.localeCompare(b.department)
        || a.rank - b.rank
    ),
    ["department", "rank", "employee", "amount"],
    "Top two ranks per department with RANK"
  );

  console.log("\nWindow specification:");
  console.log(rowNumberSpecification.toSQL());

  const csvText = [
    "saleId,employee,department,region,amount",
    "301,Ananya,Engineering,North,9100",
    "302,Bharat,Engineering,South,8800",
    "303,Chitra,Sales,North,12500",
    "304,Danish,Sales,South,7600"
  ].join("\n");

  const parsedRows = parseSimpleSalesCSV(csvText);

  const parsedRanked = rank(
    parsedRows,
    new WindowSpecification({
      partitionBy: ["department"],
      orderBy: [{ column: "amount", descending: true }]
    })
  );

  printRows(
    parsedRanked,
    ["saleId", "employee", "department", "amount", "rank"],
    "Validated CSV rows with partition-local RANK"
  );

  console.log("\nEvent-driven asynchronous report:");

  const asyncLeaderboard = await generateLeaderboardAsync(sales);

  printRows(
    asyncLeaderboard.sort(
      (a, b) =>
        a.department.localeCompare(b.department)
        || a.rowNumber - b.rowNumber
    ),
    ["department", "employee", "amount", "rowNumber", "rank", "denseRank"],
    "Completed asynchronous leaderboard"
  );

  assertRankingInvariants(asyncLeaderboard);

  console.log("\nValidation test:");

  try {
    topNPerGroup(sales, 0);
  } catch (error) {
    console.log(`Rejected invalid top-N request: ${error.message}`);
  }

  try {
    rowNumber(
      sales,
      new WindowSpecification({
        partitionBy: ["missingColumn"],
        orderBy: [{ column: "amount", descending: true }]
      })
    );
  } catch (error) {
    console.log(`Rejected invalid partition column: ${error.message}`);
  }

  console.log("\nAll JavaScript window-function invariants passed.");
}

main().catch((error) => {
  /*
   * A top-level rejection handler prevents silent failures in asynchronous
   * report processing and gives a non-zero process exit status.
   */
  console.error(`Fatal error: ${error.message}`);
  process.exitCode = 1;
});
