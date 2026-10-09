"use strict";

/*
 * Advanced analytical SQL companion:
 * A streaming-friendly daily analytics engine using JavaScript Maps,
 * explicit calendar semantics, conditional aggregates, and event processing.
 *
 * Run with Node.js 18 or later:
 *     node advanced_analytical_sql.js
 *
 * Monetary amounts are represented as integer minor units (paise) to avoid
 * binary floating-point arithmetic in financial aggregations.
 */

const DAY_MS = 24 * 60 * 60 * 1000;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function parseDate(dateString) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    throw new TypeError(`Invalid ISO date: ${dateString}`);
  }

  const parsed = new Date(`${dateString}T00:00:00.000Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== dateString) {
    throw new TypeError(`Invalid calendar date: ${dateString}`);
  }
  return parsed;
}

function dateKey(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date, count) {
  return new Date(date.getTime() + count * DAY_MS);
}

function validateRecord(record) {
  const validStatuses = new Set(["completed", "cancelled", "pending"]);

  parseDate(record.date);

  if (!record.department || typeof record.department !== "string") {
    throw new TypeError("A nonempty department is required.");
  }
  if (!Number.isSafeInteger(record.revenuePaise) || record.revenuePaise < 0) {
    throw new RangeError("Revenue must be nonnegative integer paise.");
  }
  if (!Number.isSafeInteger(record.orders) || record.orders < 0) {
    throw new RangeError("Orders must be a nonnegative safe integer.");
  }
  if (!validStatuses.has(record.status)) {
    throw new TypeError(`Unknown status: ${record.status}`);
  }

  return Object.freeze({ ...record });
}

function interpolatePercentile(values, p) {
  if (!Number.isFinite(p) || p < 0 || p > 1) {
    throw new RangeError("Percentile must be between 0 and 1.");
  }
  if (values.length === 0) {
    throw new RangeError("Cannot calculate a percentile of empty input.");
  }

  const sorted = [...values].sort((a, b) => a - b);
  const position = p * (sorted.length - 1);
  const lower = Math.floor(position);
  const upper = Math.ceil(position);

  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function discretePercentile(values, p) {
  if (!Number.isFinite(p) || p < 0 || p > 1) {
    throw new RangeError("Percentile must be between 0 and 1.");
  }
  if (values.length === 0) {
    throw new RangeError("Cannot calculate a percentile of empty input.");
  }

  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.max(0, Math.ceil(p * sorted.length) - 1);
  return sorted[index];
}

function aggregateByDepartment(records) {
  const departments = new Map();

  for (const record of records) {
    if (!departments.has(record.department)) {
      departments.set(record.department, {
        department: record.department,
        completedRevenuePaise: 0,
        completedOrders: 0,
        cancelledOrders: 0,
        completedDays: 0,
        cancelledDays: 0,
        pendingDays: 0,
        completedRevenueSamples: []
      });
    }

    const aggregate = departments.get(record.department);

    switch (record.status) {
      case "completed":
        aggregate.completedRevenuePaise += record.revenuePaise;
        aggregate.completedOrders += record.orders;
        aggregate.completedDays += 1;
        aggregate.completedRevenueSamples.push(record.revenuePaise);
        break;
      case "cancelled":
        aggregate.cancelledOrders += record.orders;
        aggregate.cancelledDays += 1;
        break;
      case "pending":
        aggregate.pendingDays += 1;
        break;
      default:
        throw new Error("Record validation was bypassed.");
    }
  }

  return [...departments.values()].map((aggregate) => ({
    ...aggregate,
    completedRevenueSamples: undefined,
    medianCompletedDailyRevenuePaise:
      aggregate.completedRevenueSamples.length === 0
        ? null
        : interpolatePercentile(aggregate.completedRevenueSamples, 0.5)
  }));
}

function rollingRows(records, windowSize) {
  if (!Number.isInteger(windowSize) || windowSize < 1) {
    throw new RangeError("windowSize must be a positive integer.");
  }

  const ordered = [...records].sort(
    (a, b) => a.date.localeCompare(b.date) ||
      a.department.localeCompare(b.department)
  );

  const result = [];
  let partitionDepartment = null;
  let partition = [];

  for (const record of ordered) {
    if (record.department !== partitionDepartment) {
      partitionDepartment = record.department;
      partition = [];
    }

    partition.push(record);

    // Keep only the rows that can participate in the next trailing frame.
    if (partition.length > windowSize) partition.shift();

    const total = partition.reduce((sum, item) => sum + item.revenuePaise, 0);

    result.push({
      date: record.date,
      department: record.department,
      rollingRevenuePaise: total,
      rollingAveragePaise: total / partition.length,
      rowsInFrame: partition.length
    });
  }

  return result;
}

function rollingCalendarRevenue(records, windowDays) {
  if (!Number.isInteger(windowDays) || windowDays < 1) {
    throw new RangeError("windowDays must be a positive integer.");
  }
  if (records.length === 0) return [];

  const daily = new Map();
  for (const record of records) {
    const key = record.date;
    daily.set(key, (daily.get(key) || 0) + record.revenuePaise);
  }

  const dates = [...daily.keys()].sort();
  const first = parseDate(dates[0]);
  const last = parseDate(dates[dates.length - 1]);
  const output = [];

  for (let current = first; current <= last; current = addDays(current, 1)) {
    let total = 0;
    for (let offset = windowDays - 1; offset >= 0; offset -= 1) {
      total += daily.get(dateKey(addDays(current, -offset))) || 0;
    }

    output.push({
      date: dateKey(current),
      windowDays,
      rollingRevenuePaise: total
    });
  }

  return output;
}

function findIslands(dateStrings) {
  const dates = [...new Set(dateStrings)].sort();
  if (dates.length === 0) return [];

  const islands = [];
  let start = dates[0];
  let previous = parseDate(dates[0]);

  for (const currentString of dates.slice(1)) {
    const current = parseDate(currentString);

    if (current.getTime() - previous.getTime() !== DAY_MS) {
      islands.push({
        startDate: start,
        endDate: dateKey(previous),
        days: (previous.getTime() - parseDate(start).getTime()) / DAY_MS + 1
      });
      start = currentString;
    }

    previous = current;
  }

  islands.push({
    startDate: start,
    endDate: dateKey(previous),
    days: (previous.getTime() - parseDate(start).getTime()) / DAY_MS + 1
  });

  return islands;
}

function findMissingIntervals(dateStrings, startString, endString) {
  const start = parseDate(startString);
  const end = parseDate(endString);

  if (start > end) throw new RangeError("Start date exceeds end date.");

  const observed = new Set(dateStrings);
  const gaps = [];
  let gapStart = null;

  for (let current = start; current <= end; current = addDays(current, 1)) {
    const key = dateKey(current);

    if (!observed.has(key) && gapStart === null) {
      gapStart = key;
    } else if (observed.has(key) && gapStart !== null) {
      gaps.push({
        startDate: gapStart,
        endDate: dateKey(addDays(current, -1)),
        missingDays: (current.getTime() - parseDate(gapStart).getTime()) / DAY_MS
      });
      gapStart = null;
    }
  }

  if (gapStart !== null) {
    gaps.push({
      startDate: gapStart,
      endDate: endString,
      missingDays: (end.getTime() - parseDate(gapStart).getTime()) / DAY_MS + 1
    });
  }

  return gaps;
}

class DailyAnalytics {
  #records;

  constructor(records) {
    this.#records = records.map(validateRecord);
  }

  departmentSummary() {
    return aggregateByDepartment(this.#records);
  }

  completedRevenuePercentiles(department) {
    const values = this.#records
      .filter((record) =>
        record.department === department && record.status === "completed"
      )
      .map((record) => record.revenuePaise);

    return {
      department,
      p50Continuous: interpolatePercentile(values, 0.5),
      p90Continuous: interpolatePercentile(values, 0.9),
      p95Discrete: discretePercentile(values, 0.95)
    };
  }

  rollingRows(windowSize) {
    return rollingRows(this.#records, windowSize);
  }

  calendarWindow(windowDays) {
    return rollingCalendarRevenue(this.#records, windowDays);
  }

  dateIslands() {
    return findIslands(this.#records.map((record) => record.date));
  }

  missingDates(startDate, endDate) {
    return findMissingIntervals(
      this.#records.map((record) => record.date),
      startDate,
      endDate
    );
  }
}

function rupees(paise) {
  return (paise / 100).toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2
  });
}

function runTests() {
  assert(
    interpolatePercentile([100, 200, 300, 400], 0.5) === 250,
    "Continuous median interpolation failed."
  );
  assert(
    discretePercentile([100, 200, 300, 400], 0.5) === 200,
    "Discrete percentile selection failed."
  );

  const islands = findIslands(["2026-01-01", "2026-01-02", "2026-01-04"]);
  assert(islands.length === 2 && islands[0].days === 2, "Island detection failed.");

  const gaps = findMissingIntervals(
    ["2026-01-02", "2026-01-05"],
    "2026-01-01",
    "2026-01-06"
  );
  assert(gaps.length === 3, "Gap detection failed.");

  let rejected = false;
  try {
    validateRecord({
      date: "2026-02-30",
      department: "Operations",
      revenuePaise: 100,
      orders: 1,
      status: "completed"
    });
  } catch {
    rejected = true;
  }
  assert(rejected, "Invalid calendar date was accepted.");

  console.log("All JavaScript self-tests passed.");
}

function main() {
  runTests();

  const sample = [
    ["2026-09-01", "Operations", 120000, 24, "completed"],
    ["2026-09-02", "Operations", 135000, 27, "completed"],
    ["2026-09-03", "Operations", 0, 0, "cancelled"],
    ["2026-09-04", "Operations", 182000, 36, "completed"],
    ["2026-09-06", "Operations", 160000, 32, "completed"],
    ["2026-09-07", "Operations", 175000, 35, "completed"],
    ["2026-09-08", "Operations", 210000, 42, "completed"],
    ["2026-09-09", "Operations", 90000, 18, "pending"],
    ["2026-09-10", "Operations", 240000, 48, "completed"],
    ["2026-09-11", "Operations", 195000, 39, "completed"],
    ["2026-09-12", "Operations", 260000, 52, "completed"],
    ["2026-09-13", "Operations", 80000, 16, "cancelled"],
    ["2026-09-15", "Operations", 285000, 57, "completed"],
    ["2026-09-16", "Operations", 300000, 60, "completed"],
    ["2026-09-17", "Operations", 275000, 55, "completed"]
  ];

  const records = sample.map(([date, department, revenuePaise, orders, status]) => ({
    date,
    department,
    revenuePaise,
    orders,
    status
  }));

  const analytics = new DailyAnalytics(records);

  console.log("\nDepartment summary:");
  for (const row of analytics.departmentSummary()) {
    console.log({
      department: row.department,
      completedRevenue: rupees(row.completedRevenuePaise),
      completedOrders: row.completedOrders,
      cancelledOrders: row.cancelledOrders,
      completedDays: row.completedDays,
      medianCompletedRevenue: row.medianCompletedDailyRevenuePaise === null
        ? null
        : rupees(row.medianCompletedDailyRevenuePaise)
    });
  }

  console.log("\nRevenue percentiles:");
  const percentiles = analytics.completedRevenuePercentiles("Operations");
  console.log({
    p50: rupees(percentiles.p50Continuous),
    p90: rupees(percentiles.p90Continuous),
    p95Discrete: rupees(percentiles.p95Discrete)
  });

  console.log("\nTrailing three-row calculations:");
  for (const row of analytics.rollingRows(3)) {
    console.log({
      date: row.date,
      rollingRevenue: rupees(row.rollingRevenuePaise),
      rollingAverage: rupees(row.rollingAveragePaise),
      rows: row.rowsInFrame
    });
  }

  console.log("\nConsecutive date islands:");
  console.table(analytics.dateIslands());

  console.log("\nMissing reporting intervals:");
  console.table(analytics.missingDates("2026-09-01", "2026-09-17"));
}

if (require.main === module) {
  main();
}

module.exports = {
  interpolatePercentile,
  discretePercentile,
  aggregateByDepartment,
  rollingRows,
  rollingCalendarRevenue,
  findIslands,
  findMissingIntervals,
  DailyAnalytics
};
