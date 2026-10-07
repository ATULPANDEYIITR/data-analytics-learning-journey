"use strict";

/*
 * SQL Performance Laboratory in JavaScript
 *
 * This Node.js-compatible program complements the Python implementation by
 * modeling query-plan decisions with JavaScript data structures and an
 * event-driven execution trace.
 *
 * Focus:
 * - sequential scans
 * - index lookups
 * - filtering efficiency
 * - composite index behavior
 * - join strategy selection
 * - plan cost estimation
 * - query execution events
 * - cardinality estimation
 * - practical plan diagnostics
 *
 * No third-party packages are required.
 */

const { performance } = require("node:perf_hooks");

const REGIONS = ["North", "South", "East", "West"];
const STATUSES = ["pending", "paid", "shipped", "cancelled", "refunded"];

function seededRandom(seed = 42) {
  let state = seed >>> 0;

  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function randomChoice(random, values) {
  return values[Math.floor(random() * values.length)];
}

function randomInt(random, min, max) {
  return Math.floor(random() * (max - min + 1)) + min;
}

function createOrders(count = 100_000, seed = 42) {
  const random = seededRandom(seed);
  const orders = [];

  for (let orderId = 1; orderId <= count; orderId += 1) {
    const month = randomInt(random, 0, 8);
    const day = randomInt(random, 1, 28);

    orders.push({
      orderId,
      customerId: randomInt(random, 1, 10_000),
      orderDate: new Date(Date.UTC(2026, month, day)),
      status: randomChoice(random, STATUSES),
      totalAmount: Number(
        (10 + Math.pow(random(), 2) * 25_000).toFixed(2)
      ),
    });
  }

  return orders;
}

function buildHashIndex(rows, keySelector) {
  const index = new Map();

  for (const row of rows) {
    const key = keySelector(row);

    if (!index.has(key)) {
      index.set(key, []);
    }

    index.get(key).push(row);
  }

  return index;
}

function sequentialScan(rows, predicate) {
  const result = [];
  let examinedRows = 0;

  for (const row of rows) {
    examinedRows += 1;

    if (predicate(row)) {
      result.push(row);
    }
  }

  return {
    result,
    examinedRows,
  };
}

function indexedLookup(index, key, predicate = () => true) {
  const candidates = index.get(key) ?? [];
  const result = [];
  let examinedRows = 0;

  for (const row of candidates) {
    examinedRows += 1;

    if (predicate(row)) {
      result.push(row);
    }
  }

  return {
    result,
    examinedRows,
    candidateRows: candidates.length,
  };
}

function compareScanStrategies(orders) {
  console.log("\n=== Sequential Scan vs Index Lookup ===");

  const customerId = 731;
  const customerIndex = buildHashIndex(
    orders,
    order => order.customerId
  );

  const sequential = sequentialScan(
    orders,
    order => order.customerId === customerId
  );

  const indexed = indexedLookup(
    customerIndex,
    customerId
  );

  console.log({
    sequentialExamined: sequential.examinedRows,
    sequentialRowsReturned: sequential.result.length,
    indexedCandidates: indexed.candidateRows,
    indexedExamined: indexed.examinedRows,
    indexedRowsReturned: indexed.result.length,
  });

  /*
   * A JavaScript Map gives O(1)-average key lookup, while a PostgreSQL
   * B-tree index provides ordered access and supports equality plus range
   * predicates. The structures are therefore conceptually related but not
   * implementation-equivalent.
   */
}

function buildCompositeIndex(rows) {
  const index = new Map();

  for (const row of rows) {
    const customerKey = String(row.customerId);

    if (!index.has(customerKey)) {
      index.set(customerKey, []);
    }

    index.get(customerKey).push(row);
  }

  for (const rowsForCustomer of index.values()) {
    rowsForCustomer.sort(
      (a, b) => a.orderDate.getTime() - b.orderDate.getTime()
    );
  }

  return index;
}

function binarySearchFirstAtOrAfter(rows, cutoff) {
  let low = 0;
  let high = rows.length;

  while (low < high) {
    const middle = Math.floor((low + high) / 2);

    if (rows[middle].orderDate < cutoff) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }

  return low;
}

function compositeRangeLookup(index, customerId, cutoff) {
  const rows = index.get(String(customerId)) ?? [];
  const start = binarySearchFirstAtOrAfter(rows, cutoff);

  return {
    result: rows.slice(start),
    candidateRows: rows.length - start,
  };
}

function compositeIndexDemo(orders) {
  console.log("\n=== Composite Index Behavior ===");

  const index = buildCompositeIndex(orders);
  const cutoff = new Date("2026-09-01T00:00:00Z");
  const result = compositeRangeLookup(index, 731, cutoff);

  console.log({
    customerId: 731,
    cutoff: cutoff.toISOString().slice(0, 10),
    rowsAfterRangeStart: result.result.length,
    indexedCandidates: result.candidateRows,
  });

  console.log(
    "A conceptual PostgreSQL index on (customer_id, order_date) " +
    "can exploit equality on customer_id followed by a range on " +
    "order_date."
  );
}

function createPartialIndex(orders, predicate, keySelector) {
  const qualifyingRows = orders.filter(predicate);
  return buildHashIndex(qualifyingRows, keySelector);
}

function partialIndexDemo(orders) {
  console.log("\n=== Partial Index ===");

  const paidIndex = createPartialIndex(
    orders,
    order => order.status === "paid",
    order => order.customerId
  );

  const paidCustomerRows = paidIndex.get(731) ?? [];

  console.log(
    `Partial index entries for paid customer 731: ` +
    `${paidCustomerRows.length}`
  );

  console.log(
    "A partial PostgreSQL index is useful when its predicate matches " +
    "the query's logical requirements. It does not become a general " +
    "index over rows outside the predicate."
  );
}

function estimateSelectivity(totalRows, matchingRows) {
  return totalRows === 0 ? 0 : matchingRows / totalRows;
}

function estimatePlanCost({
  totalRows,
  matchingRows,
  randomPageCost = 4,
}) {
  const sequentialCost = totalRows * 0.01;
  const indexTreeTraversal = Math.max(
    1,
    Math.ceil(Math.log2(Math.max(2, totalRows)))
  );

  const indexCost =
    indexTreeTraversal +
    matchingRows * randomPageCost * 0.05 +
    matchingRows * 0.01;

  return {
    sequentialCost,
    indexCost,
    selectivity: estimateSelectivity(
      totalRows,
      matchingRows
    ),
  };
}

function chooseAccessPath(orders, predicate) {
  const matchingRows = orders.reduce(
    (count, order) => count + (predicate(order) ? 1 : 0),
    0
  );

  const costs = estimatePlanCost({
    totalRows: orders.length,
    matchingRows,
  });

  return {
    ...costs,
    accessPath:
      costs.indexCost < costs.sequentialCost
        ? "Index Scan"
        : "Sequential Scan",
  };
}

function planCostDemo(orders) {
  console.log("\n=== Cost-Based Access Path Reasoning ===");

  const selectivePlan = chooseAccessPath(
    orders,
    order => order.orderId === 50_000
  );

  const broadPlan = chooseAccessPath(
    orders,
    order => (
      order.status === "paid" ||
      order.status === "shipped"
    )
  );

  console.log("Highly selective predicate:", selectivePlan);
  console.log("Broad predicate:", broadPlan);

  /*
   * PostgreSQL's planner does not simply ask "does an index exist?"
   * It compares estimated costs using table statistics and configuration.
   */
}

function nestedLoopJoin(customers, orders) {
  const result = [];
  let comparisons = 0;

  for (const customer of customers) {
    for (const order of orders) {
      comparisons += 1;

      if (customer.customerId === order.customerId) {
        result.push({ customer, order });
      }
    }
  }

  return { result, comparisons };
}

function indexedNestedLoopJoin(customers, orderIndex) {
  const result = [];
  let indexLookups = 0;

  for (const customer of customers) {
    indexLookups += 1;

    const orders = orderIndex.get(customer.customerId) ?? [];

    for (const order of orders) {
      result.push({ customer, order });
    }
  }

  return { result, indexLookups };
}

function hashJoin(customers, orders) {
  const customerHash = new Map(
    customers.map(customer => [
      customer.customerId,
      customer,
    ])
  );

  const result = [];
  let probes = 0;

  for (const order of orders) {
    probes += 1;

    const customer = customerHash.get(order.customerId);

    if (customer) {
      result.push({ customer, order });
    }
  }

  return { result, probes };
}

function joinOptimizationDemo(orders) {
  console.log("\n=== Join Strategy Comparison ===");

  const customers = Array.from(
    { length: 100 },
    (_, index) => ({
      customerId: index + 1,
      region: REGIONS[index % REGIONS.length],
    })
  );

  const limitedOrders = orders.slice(0, 2_000);

  const nested = nestedLoopJoin(
    customers,
    limitedOrders
  );

  const orderIndex = buildHashIndex(
    limitedOrders,
    order => order.customerId
  );

  const indexed = indexedNestedLoopJoin(
    customers,
    orderIndex
  );

  const hashed = hashJoin(
    customers,
    limitedOrders
  );

  console.log({
    nestedLoopComparisons: nested.comparisons,
    indexedNestedLoopLookups: indexed.indexLookups,
    hashJoinProbes: hashed.probes,
  });

  /*
   * Nested loops are not inherently bad. They can be excellent when the
   * outer relation is small and the inner relation has a selective index.
   * Hash joins often suit larger equality joins when sufficient memory is
   * available for the hash table.
   */
}

class QueryExecutionTrace {
  constructor() {
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }

    this.listeners.get(eventName).push(listener);
  }

  emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) ?? []) {
      listener(payload);
    }
  }
}

async function executeQuerySimulation(orders, predicate) {
  const trace = new QueryExecutionTrace();

  trace.on("scan:start", payload => {
    console.log(
      `scan:start relation=${payload.relation} ` +
      `rows=${payload.rows}`
    );
  });

  trace.on("scan:finish", payload => {
    console.log(
      `scan:finish examined=${payload.examined} ` +
      `returned=${payload.returned}`
    );
  });

  trace.on("query:finish", payload => {
    console.log(
      `query:finish elapsed=${payload.elapsedMs.toFixed(3)} ms`
    );
  });

  trace.emit("scan:start", {
    relation: "orders",
    rows: orders.length,
  });

  const started = performance.now();

  const result = sequentialScan(
    orders,
    predicate
  );

  await new Promise(resolve => setImmediate(resolve));

  trace.emit("scan:finish", {
    examined: result.examinedRows,
    returned: result.result.length,
  });

  trace.emit("query:finish", {
    elapsedMs: performance.now() - started,
  });

  return result.result;
}

function explainLike(plan) {
  console.log("\n=== EXPLAIN-Like Diagnostic ===");

  console.log(
    `${plan.nodeType} on ${plan.relation} ` +
    `(cost=${plan.startupCost.toFixed(2)}..` +
    `${plan.totalCost.toFixed(2)} ` +
    `rows=${plan.estimatedRows} ` +
    `actual rows=${plan.actualRows})`
  );

  if (plan.estimatedRows > 0) {
    const ratio = plan.actualRows / plan.estimatedRows;

    console.log(
      `Actual/estimated row ratio: ${ratio.toFixed(2)}`
    );

    if (ratio > 10 || ratio < 0.1) {
      console.log(
        "Large cardinality mismatch: investigate statistics, " +
        "data skew, correlated predicates, or estimation assumptions."
      );
    }
  }
}

function queryShapeGuidance() {
  console.log("\n=== Query Shape Guidance ===");

  console.log(
    "Range predicates on raw indexed columns are generally more " +
    "index-friendly than applying functions to those columns."
  );

  console.log(
    "A predicate that filters early can reduce the number of rows " +
    "participating in later joins and aggregations."
  );

  console.log(
    "An index that supports a lookup but does not contain all requested " +
    "columns may still require heap access."
  );

  console.log(
    "An index can lose its advantage when a query needs a large fraction " +
    "of the relation."
  );
}

async function main() {
  console.log("SQL PERFORMANCE LABORATORY");
  console.log("=".repeat(72));

  const orders = createOrders();

  console.log(`Generated ${orders.length.toLocaleString()} orders.`);

  compareScanStrategies(orders);
  compositeIndexDemo(orders);
  partialIndexDemo(orders);
  planCostDemo(orders);
  joinOptimizationDemo(orders);

  await executeQuerySimulation(
    orders,
    order => (
      order.customerId === 731 &&
      order.orderDate >= new Date("2026-09-01T00:00:00Z")
    )
  );

  explainLike({
    nodeType: "Index Scan",
    relation: "orders",
    estimatedRows: 9,
    actualRows: 11,
    startupCost: 0.42,
    totalCost: 18.31,
  });

  queryShapeGuidance();

  console.log("\n=== PostgreSQL Validation ===");
  console.log(
    "Use EXPLAIN (ANALYZE, BUFFERS) against the real query to compare " +
    "estimated rows, actual rows, buffer activity, and execution time."
  );
}

main().catch(error => {
  console.error("Execution failed:", error);
  process.exitCode = 1;
});
