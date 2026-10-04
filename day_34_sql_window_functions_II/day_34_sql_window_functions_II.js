"use strict";

/*
 * SQL Window Functions II
 *
 * This Node.js program complements the Python implementation by modeling
 * window-function behavior in JavaScript without requiring a database
 * package. It focuses on event-stream processing, explicit partitioning,
 * row-relative navigation, running state, and moving windows.
 *
 * Run with:
 *   node window-functions-ii.js
 *
 * The implementation deliberately uses JavaScript-specific features:
 * classes, Maps, immutable-style transformations, validation, async
 * processing, and event-driven execution.
 */

const { EventEmitter } = require("node:events");

const SALES = [
  { date: "2026-09-01", region: "North", product: "Cloud", revenue: 1200 },
  { date: "2026-09-02", region: "North", product: "Cloud", revenue: 1350 },
  { date: "2026-09-03", region: "North", product: "Cloud", revenue: 1280 },
  { date: "2026-09-04", region: "North", product: "Cloud", revenue: 1410 },
  { date: "2026-09-05", region: "North", product: "Cloud", revenue: 1500 },
  { date: "2026-09-06", region: "North", product: "Cloud", revenue: 1460 },
  { date: "2026-09-07", region: "North", product: "Cloud", revenue: 1600 },
  { date: "2026-09-01", region: "South", product: "Cloud", revenue: 900 },
  { date: "2026-09-02", region: "South", product: "Cloud", revenue: 980 },
  { date: "2026-09-03", region: "South", product: "Cloud", revenue: 1020 },
  { date: "2026-09-04", region: "South", product: "Cloud", revenue: 1100 },
  { date: "2026-09-05", region: "South", product: "Cloud", revenue: 1060 },
  { date: "2026-09-06", region: "South", product: "Cloud", revenue: 1170 },
  { date: "2026-09-07", region: "South", product: "Cloud", revenue: 1210 },
  { date: "2026-09-01", region: "North", product: "Security", revenue: 800 },
  { date: "2026-09-02", region: "North", product: "Security", revenue: 860 },
  { date: "2026-09-03", region: "North", product: "Security", revenue: 920 },
  { date: "2026-09-04", region: "North", product: "Security", revenue: 880 },
  { date: "2026-09-05", region: "North", product: "Security", revenue: 990 },
  { date: "2026-09-06", region: "North", product: "Security", revenue: 1040 },
  { date: "2026-09-07", region: "North", product: "Security", revenue: 1120 },
  { date: "2026-09-01", region: "South", product: "Security", revenue: 700 },
  { date: "2026-09-02", region: "South", product: "Security", revenue: 760 },
  { date: "2026-09-04", region: "South", product: "Security", revenue: 820 },
  { date: "2026-09-05", region: "South", product: "Security", revenue: 850 },
  { date: "2026-09-07", region: "South", product: "Security", revenue: 940 }
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function validateSale(row) {
  assert(row && typeof row === "object", "Sale must be an object.");
  assert(
    /^\d{4}-\d{2}-\d{2}$/.test(row.date),
    `Invalid ISO date: ${row.date}`
  );
  assert(typeof row.region === "string" && row.region.length > 0, "Region is required.");
  assert(typeof row.product === "string" && row.product.length > 0, "Product is required.");
  assert(
    Number.isFinite(row.revenue) && row.revenue >= 0,
    `Revenue must be a non-negative finite number: ${row.revenue}`
  );
}

function validateDataset(rows) {
  rows.forEach(validateSale);
  return rows;
}

function partitionKey(row) {
  return `${row.region}\u0000${row.product}`;
}

function partitionAndSort(rows) {
  /*
   * SQL PARTITION BY + ORDER BY is modeled as a Map of independent,
   * chronologically sorted arrays. The Map prevents rows from different
   * region/product histories from becoming neighbors.
   */
  const partitions = new Map();

  for (const row of rows) {
    const key = partitionKey(row);

    if (!partitions.has(key)) {
      partitions.set(key, []);
    }

    partitions.get(key).push({ ...row });
  }

  for (const partition of partitions.values()) {
    partition.sort((a, b) => a.date.localeCompare(b.date));
  }

  return partitions;
}

function lag(partition, index, offset = 1, defaultValue = null) {
  const target = index - offset;
  return target >= 0 ? partition[target].revenue : defaultValue;
}

function lead(partition, index, offset = 1, defaultValue = null) {
  const target = index + offset;
  return target < partition.length
    ? partition[target].revenue
    : defaultValue;
}

function firstValue(partition) {
  return partition.length === 0 ? null : partition[0].revenue;
}

function lastValue(partition) {
  return partition.length === 0
    ? null
    : partition[partition.length - 1].revenue;
}

function runningTotal(partition, index) {
  let total = 0;

  for (let i = 0; i <= index; i += 1) {
    total += partition[i].revenue;
  }

  return total;
}

function movingAverage(partition, index, precedingRows = 2) {
  const start = Math.max(0, index - precedingRows);
  const window = partition.slice(start, index + 1);

  if (window.length === 0) {
    return null;
  }

  const total = window.reduce((sum, row) => sum + row.revenue, 0);
  return total / window.length;
}

function calendarDaysBetween(firstDate, secondDate) {
  const first = Date.parse(`${firstDate}T00:00:00Z`);
  const second = Date.parse(`${secondDate}T00:00:00Z`);

  if (!Number.isFinite(first) || !Number.isFinite(second)) {
    return null;
  }

  return Math.round((second - first) / 86400000);
}

function analyzePartition(partition) {
  /*
   * This is intentionally a single-pass stateful analysis after sorting.
   * SQL window functions conceptually expose neighboring rows and frames;
   * this implementation makes that state visible as ordinary JavaScript
   * objects.
   */
  const first = firstValue(partition);
  const last = lastValue(partition);
  let total = 0;

  return partition.map((row, index) => {
    const previousRevenue = lag(partition, index);
    const nextRevenue = lead(partition, index);

    total += row.revenue;

    const previousDate = index > 0 ? partition[index - 1].date : null;

    const percentageChange =
      previousRevenue === null || previousRevenue === 0
        ? null
        : ((row.revenue - previousRevenue) / previousRevenue) * 100;

    return {
      ...row,
      previousRevenue,
      nextRevenue,
      firstRevenue: first,
      finalRevenue: last,
      runningRevenue: total,
      movingAverage3: movingAverage(partition, index, 2),
      calendarDaysSincePrevious:
        previousDate === null
          ? null
          : calendarDaysBetween(previousDate, row.date),
      percentageChange
    };
  });
}

function buildWindowReport(rows) {
  validateDataset(rows);

  const partitions = partitionAndSort(rows);
  const report = [];

  for (const partition of partitions.values()) {
    report.push(...analyzePartition(partition));
  }

  return report.sort(
    (a, b) =>
      a.region.localeCompare(b.region) ||
      a.product.localeCompare(b.product) ||
      a.date.localeCompare(b.date)
  );
}

function formatMoney(value) {
  return value === null ? "NULL" : value.toFixed(2);
}

function printNavigationReport(report) {
  console.log("\nLAG / LEAD / FIRST_VALUE / LAST_VALUE");
  console.log("=".repeat(100));

  for (const row of report) {
    console.log(
      `${row.date} | ${row.region.padEnd(5)} | ${row.product.padEnd(8)} | ` +
      `revenue=${formatMoney(row.revenue).padStart(8)} | ` +
      `lag=${formatMoney(row.previousRevenue).padStart(8)} | ` +
      `lead=${formatMoney(row.nextRevenue).padStart(8)} | ` +
      `first=${formatMoney(row.firstRevenue).padStart(8)} | ` +
      `last=${formatMoney(row.finalRevenue).padStart(8)}`
    );
  }
}

function printAggregateReport(report) {
  console.log("\nRUNNING TOTALS AND MOVING AVERAGES");
  console.log("=".repeat(100));

  for (const row of report) {
    console.log(
      `${row.date} | ${row.region.padEnd(5)} | ${row.product.padEnd(8)} | ` +
      `running=${formatMoney(row.runningRevenue).padStart(9)} | ` +
      `moving3=${formatMoney(row.movingAverage3).padStart(8)} | ` +
      `change=${row.percentageChange === null
        ? "NULL"
        : `${row.percentageChange.toFixed(2)}%`
      } | gap=${row.calendarDaysSincePrevious ?? "NULL"} day(s)`
    );
  }
}

function detectLargeChanges(report, thresholdPercent = 20) {
  /*
   * This is an application-level interpretation of a window calculation.
   * LAG supplies the baseline; the monitoring policy determines whether
   * the difference deserves attention.
   */
  return report.filter(
    row =>
      row.percentageChange !== null &&
      Math.abs(row.percentageChange) >= thresholdPercent
  );
}

class WindowAnalyticsService extends EventEmitter {
  /*
   * EventEmitter provides a useful Node.js representation of an analytical
   * pipeline: raw data is loaded, a window report is produced, and policy
   * alerts are emitted independently of the calculation itself.
   */
  constructor(rows) {
    super();
    this.rows = rows;
  }

  async run() {
    /*
     * Promise.resolve() places the completion on the asynchronous job queue.
     * A real application could replace this step with database I/O without
     * changing the downstream report contract.
     */
    const report = await Promise.resolve(buildWindowReport(this.rows));

    this.emit("reportReady", report);

    const alerts = detectLargeChanges(report);
    for (const alert of alerts) {
      this.emit("changeDetected", alert);
    }

    return report;
  }
}

async function demonstrateStreamingAnalytics(rows) {
  const service = new WindowAnalyticsService(rows);

  service.on("reportReady", report => {
    console.log(`\nEvent: reportReady (${report.length} analytical rows)`);
  });

  service.on("changeDetected", row => {
    console.log(
      `Event: changeDetected -> ${row.region}/${row.product} ` +
      `${row.date}: ${row.percentageChange.toFixed(2)}%`
    );
  });

  return service.run();
}

function demonstrateLastValueFrameIssue(rows) {
  /*
   * A frequent SQL mistake is expecting LAST_VALUE() to return the final
   * partition row while the default frame only reaches the current row.
   *
   * The two arrays below make the semantic distinction concrete.
   */
  const partitions = partitionAndSort(rows);
  const firstPartition = partitions.values().next().value;

  const currentFrameResults = firstPartition.map(
    (_, index) => firstPartition[index].revenue
  );

  const fullPartitionResults = firstPartition.map(
    () => firstPartition[firstPartition.length - 1].revenue
  );

  console.log("\nLAST_VALUE FRAME SEMANTICS");
  console.log("=".repeat(100));
  console.log("Current-row frame:", currentFrameResults);
  console.log("Full-partition frame:", fullPartitionResults);
}

function demonstrateBoundaryBehavior() {
  console.log("\nBOUNDARY BEHAVIOR");
  console.log("=".repeat(100));

  const partition = [
    { date: "2026-10-01", region: "Demo", product: "API", revenue: 100 },
    { date: "2026-10-02", region: "Demo", product: "API", revenue: 120 }
  ];

  assert(lag(partition, 0) === null, "First LAG should be NULL.");
  assert(lead(partition, 1) === null, "Final LEAD should be NULL.");
  assert(lag(partition, 0, 1, 0) === 0, "Default LAG value should work.");
  assert(lead(partition, 1, 1, 0) === 0, "Default LEAD value should work.");

  console.log("First-row LAG:", lag(partition, 0));
  console.log("Final-row LEAD:", lead(partition, 1));
  console.log("First-row LAG with default 0:", lag(partition, 0, 1, 0));
  console.log("Final-row LEAD with default 0:", lead(partition, 1, 1, 0));
}

function demonstrateInvalidData() {
  console.log("\nVALIDATION FAILURE");
  console.log("=".repeat(100));

  try {
    validateSale({
      date: "2026-09-01",
      region: "North",
      product: "Cloud",
      revenue: -10
    });
  } catch (error) {
    console.log(`Rejected invalid revenue: ${error.message}`);
  }
}

async function main() {
  validateDataset(SALES);

  const report = await demonstrateStreamingAnalytics(SALES);

  printNavigationReport(report);
  printAggregateReport(report);
  demonstrateLastValueFrameIssue(SALES);
  demonstrateBoundaryBehavior();
  demonstrateInvalidData();

  const alerts = detectLargeChanges(report);

  console.log("\nCHANGE DETECTION");
  console.log("=".repeat(100));

  for (const row of alerts) {
    console.log(
      `${row.date} | ${row.region} | ${row.product} | ` +
      `${row.percentageChange.toFixed(2)}% change`
    );
  }

  console.log("\nJavaScript window-analytics demonstration completed.");
}

main().catch(error => {
  console.error("Execution failed:", error.message);
  process.exitCode = 1;
});
