/**
 * SQL CASE Expressions
 * ====================
 *
 * A self-contained Node.js program that models SQL CASE behavior.
 *
 * The implementation focuses on:
 * - searched CASE WHEN rules
 * - simple CASE equality mappings
 * - conditional transformations
 * - numeric bucketing
 * - business-rule evaluation
 * - review of rule ordering
 * - NULL-like database values
 * - conditional aggregation
 * - policy validation
 * - generation of safe CASE SQL fragments
 *
 * The program uses JavaScript to build a reusable rule-processing layer and
 * emits SQL expressions that can be incorporated into reporting queries.
 */

"use strict";

/*
 * Database NULL is represented by null in JavaScript. Undefined is treated
 * differently: it usually means that a property was not supplied at all.
 */
const customers = [
  {
    customerId: 1,
    customerName: "Asha",
    region: "North",
    tier: "Gold",
    annualSpend: 125000,
    accountAgeMonths: 38,
  },
  {
    customerId: 2,
    customerName: "Ravi",
    region: "South",
    tier: "Silver",
    annualSpend: 64000,
    accountAgeMonths: 19,
  },
  {
    customerId: 3,
    customerName: "Meera",
    region: "West",
    tier: null,
    annualSpend: 18000,
    accountAgeMonths: 7,
  },
  {
    customerId: 4,
    customerName: "Kabir",
    region: "East",
    tier: "Bronze",
    annualSpend: 42000,
    accountAgeMonths: 14,
  },
  {
    customerId: 5,
    customerName: "Neha",
    region: "North",
    tier: "Gold",
    annualSpend: 225000,
    accountAgeMonths: 64,
  },
];

const orders = [
  {
    orderId: 101,
    customerId: 1,
    amount: 18000,
    status: "completed",
    discountRate: 0.1,
    shippingDays: 2,
  },
  {
    orderId: 102,
    customerId: 1,
    amount: 42000,
    status: "completed",
    discountRate: 0.05,
    shippingDays: 4,
  },
  {
    orderId: 103,
    customerId: 2,
    amount: 7600,
    status: "pending",
    discountRate: 0.05,
    shippingDays: 6,
  },
  {
    orderId: 104,
    customerId: 3,
    amount: 2500,
    status: "completed",
    discountRate: null,
    shippingDays: 9,
  },
  {
    orderId: 105,
    customerId: 3,
    amount: 14000,
    status: "completed",
    discountRate: 0.2,
    shippingDays: 5,
  },
  {
    orderId: 106,
    customerId: 4,
    amount: 48000,
    status: "completed",
    discountRate: 0.05,
    shippingDays: 2,
  },
  {
    orderId: 107,
    customerId: 5,
    amount: 65000,
    status: "completed",
    discountRate: 0.12,
    shippingDays: 1,
  },
];

/**
 * JavaScript's if/else is useful for building the same decision logic that
 * a SQL searched CASE expression performs. The important SQL characteristic
 * modeled here is first-match-wins ordering.
 */
function classifySpend(annualSpend) {
  if (annualSpend >= 200000) {
    return "Enterprise";
  }

  if (annualSpend >= 100000) {
    return "Premium";
  }

  if (annualSpend >= 50000) {
    return "Growth";
  }

  return "Standard";
}

/**
 * A simple CASE is conceptually close to a JavaScript switch because both
 * compare one expression with multiple equality values.
 */
function describeRegion(region) {
  switch (region) {
    case "North":
      return "Northern Territory";
    case "South":
      return "Southern Territory";
    case "East":
      return "Eastern Territory";
    case "West":
      return "Western Territory";
    default:
      return "Unassigned Territory";
  }
}

/**
 * Conditional transformation based on the presence and magnitude of a value.
 *
 * The explicit null check is important. Treating null as zero can hide a
 * missing-data problem, while SQL CASE often needs to distinguish NULL from
 * an explicitly stored zero.
 */
function classifyDiscount(discountRate) {
  if (discountRate === null) {
    return "Discount not recorded";
  }

  if (discountRate === 0) {
    return "No discount";
  }

  if (discountRate < 0.1) {
    return "Low discount";
  }

  if (discountRate < 0.2) {
    return "Standard discount";
  }

  return "High discount";
}

/**
 * Numeric bucketing mirrors a searched SQL CASE expression. The thresholds
 * are intentionally written from the lowest boundary upward.
 */
function bucketOrderAmount(amount) {
  if (amount < 5000) {
    return "Small";
  }

  if (amount < 15000) {
    return "Medium";
  }

  if (amount < 50000) {
    return "Large";
  }

  return "Enterprise";
}

/**
 * A reusable rule evaluator demonstrates how configurable CASE-like rules can
 * be separated from the data being classified.
 *
 * Each predicate corresponds to a SQL WHEN condition.
 */
function evaluateRules(value, rules, fallback) {
  if (!Array.isArray(rules) || rules.length === 0) {
    throw new TypeError("rules must be a non-empty array");
  }

  for (const rule of rules) {
    if (typeof rule.matches !== "function" || typeof rule.label !== "string") {
      throw new TypeError(
        "Each rule must contain a matches function and a label string"
      );
    }

    if (rule.matches(value)) {
      return rule.label;
    }
  }

  return fallback;
}

const spendRules = [
  {
    label: "Enterprise",
    matches: (spend) => spend >= 200000,
  },
  {
    label: "Premium",
    matches: (spend) => spend >= 100000,
  },
  {
    label: "Growth",
    matches: (spend) => spend >= 50000,
  },
];

/**
 * Business rules can combine several fields. The rule order represents
 * precedence, just as WHEN order does in SQL.
 */
function determineOperationalAction(order) {
  if (order.status === "cancelled") {
    return "Do not process";
  }

  if (order.shippingDays === null) {
    return "Investigate shipping data";
  }

  if (order.shippingDays > 7 && order.amount >= 20000) {
    return "Escalate delayed high-value order";
  }

  if (order.amount >= 50000) {
    return "Priority fulfillment";
  }

  if (order.shippingDays > 7) {
    return "Shipping review";
  }

  return "Normal fulfillment";
}

/**
 * Conditional aggregation is a common SQL use of CASE. This JavaScript
 * function produces the equivalent business metric before the result would
 * normally be grouped by SQL.
 */
function calculateRegionalMetrics(customerRows, orderRows) {
  const customerById = new Map(
    customerRows.map((customer) => [customer.customerId, customer])
  );

  const metrics = new Map();

  for (const order of orderRows) {
    const customer = customerById.get(order.customerId);

    if (!customer) {
      throw new Error(
        `Order ${order.orderId} references an unknown customer`
      );
    }

    if (!metrics.has(customer.region)) {
      metrics.set(customer.region, {
        region: customer.region,
        totalOrders: 0,
        completedOrders: 0,
        cancelledOrders: 0,
        completedRevenue: 0,
      });
    }

    const metric = metrics.get(customer.region);
    metric.totalOrders += 1;

    if (order.status === "completed") {
      metric.completedOrders += 1;
      metric.completedRevenue += order.amount;
    } else if (order.status === "cancelled") {
      metric.cancelledOrders += 1;
    }
  }

  return [...metrics.values()].sort(
    (left, right) => right.completedRevenue - left.completedRevenue
  );
}

/**
 * Validate interval-style buckets before turning them into SQL CASE branches.
 *
 * Adjacent intervals are acceptable:
 * [0, 5000), [5000, 15000), ...
 *
 * Overlapping intervals are rejected because otherwise CASE result depends on
 * WHEN order rather than representing a clean partition of the domain.
 */
function validateBuckets(buckets) {
  if (!Array.isArray(buckets) || buckets.length === 0) {
    throw new TypeError("At least one bucket is required");
  }

  const sorted = [...buckets].sort((a, b) => a.min - b.min);

  for (let index = 0; index < sorted.length; index += 1) {
    const bucket = sorted[index];

    if (!Number.isFinite(bucket.min)) {
      throw new TypeError("Bucket minimum must be a finite number");
    }

    if (
      bucket.max !== null &&
      (!Number.isFinite(bucket.max) || bucket.max <= bucket.min)
    ) {
      throw new RangeError(`Invalid range for ${bucket.label}`);
    }

    const previous = sorted[index - 1];

    if (
      previous &&
      previous.max !== null &&
      bucket.min < previous.max
    ) {
      throw new RangeError(
        `Overlapping buckets: ${previous.label} and ${bucket.label}`
      );
    }
  }
}

/**
 * Escape a SQL string literal.
 *
 * This is not a substitute for parameterized SQL for dynamic values. It is
 * used here only because CASE labels are being rendered into a generated SQL
 * expression. Numeric boundaries are validated as finite numbers before they
 * are interpolated.
 */
function escapeSqlString(value) {
  return String(value).replaceAll("'", "''");
}

/**
 * Build a CASE expression for a validated numeric column.
 *
 * A strict identifier check prevents a caller from turning the column name
 * into arbitrary SQL syntax.
 */
function buildBucketCase(columnName, buckets, fallback = "Unclassified") {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(columnName)) {
    throw new Error("Unsafe SQL column identifier");
  }

  validateBuckets(buckets);

  const sorted = [...buckets].sort((a, b) => a.min - b.min);

  const branches = sorted.map((bucket) => {
    const min = bucket.min;

    if (bucket.max === null) {
      return (
        `WHEN ${columnName} >= ${min} ` +
        `THEN '${escapeSqlString(bucket.label)}'`
      );
    }

    return (
      `WHEN ${columnName} >= ${min} ` +
      `AND ${columnName} < ${bucket.max} ` +
      `THEN '${escapeSqlString(bucket.label)}'`
    );
  });

  branches.push(`ELSE '${escapeSqlString(fallback)}'`);

  return `CASE\n  ${branches.join("\n  ")}\nEND`;
}

/**
 * Generate a practical SQL CASE expression for an order dashboard.
 */
function demonstrateSqlGeneration() {
  const buckets = [
    { label: "Small", min: 0, max: 5000 },
    { label: "Medium", min: 5000, max: 15000 },
    { label: "Large", min: 15000, max: 50000 },
    { label: "Enterprise", min: 50000, max: null },
  ];

  return buildBucketCase("order_amount", buckets, "Invalid");
}

/**
 * A deliberately overlapping rule set demonstrates the first-match-wins
 * behavior that must be understood before changing CASE predicates.
 */
function demonstrateRulePrecedence() {
  const rules = [
    {
      label: "Growth",
      matches: (value) => value >= 50000,
    },
    {
      label: "Premium",
      matches: (value) => value >= 100000,
    },
  ];

  const classification = evaluateRules(120000, rules, "Standard");

  console.log("\n--- Rule precedence ---");
  console.log("Value:", 120000);
  console.log("First matching rule:", classification);
  console.log(
    "The Premium rule is unreachable for values >= 100000 because Growth matches first."
  );
}

/**
 * CASE conditions can represent explicit data-quality states.
 */
function classifyTier(tier) {
  if (tier === null) {
    return "Tier missing";
  }

  if (tier === "Gold") {
    return "High-value relationship";
  }

  if (tier === "Silver") {
    return "Established relationship";
  }

  if (tier === "Bronze") {
    return "Developing relationship";
  }

  return "Unknown tier";
}

/**
 * Produce a complete dashboard-oriented transformation without introducing
 * SQL syntax into the business classification itself.
 */
function createOrderView(customerRows, orderRows) {
  const customerById = new Map(
    customerRows.map((customer) => [customer.customerId, customer])
  );

  return orderRows.map((order) => {
    const customer = customerById.get(order.customerId);

    if (!customer) {
      throw new Error(`Unknown customer for order ${order.orderId}`);
    }

    const netAmount =
      order.amount * (1 - (order.discountRate ?? 0));

    return {
      orderId: order.orderId,
      customerName: customer.customerName,
      region: customer.region,
      spendSegment: classifySpend(customer.annualSpend),
      tierClassification: classifyTier(customer.tier),
      orderBucket: bucketOrderAmount(order.amount),
      discountCategory: classifyDiscount(order.discountRate),
      operationalAction: determineOperationalAction(order),
      netAmount: Math.round(netAmount * 100) / 100,
    };
  });
}

function printTable(title, rows) {
  console.log(`\n--- ${title} ---`);

  for (const row of rows) {
    console.log(JSON.stringify(row));
  }
}

function main() {
  console.log("--- Searched CASE equivalent ---");

  for (const customer of customers) {
    console.log(
      customer.customerName,
      "=>",
      classifySpend(customer.annualSpend)
    );
  }

  console.log("\n--- Simple CASE equivalent ---");

  for (const customer of customers) {
    console.log(
      customer.region,
      "=>",
      describeRegion(customer.region)
    );
  }

  console.log("\n--- Configurable CASE-style rules ---");

  for (const customer of customers) {
    const result = evaluateRules(
      customer.annualSpend,
      spendRules,
      "Standard"
    );

    console.log(
      `${customer.customerName}: ${result}`
    );
  }

  printTable(
    "Conditional transformations",
    createOrderView(customers, orders)
  );

  printTable(
    "Conditional aggregation equivalent",
    calculateRegionalMetrics(customers, orders)
  );

  demonstrateRulePrecedence();

  console.log("\n--- Generated SQL CASE expression ---");
  console.log(demonstrateSqlGeneration());

  console.log("\n--- Boundary behavior ---");

  const boundaryValues = [
    0,
    4999.99,
    5000,
    14999.99,
    15000,
    49999.99,
    50000,
  ];

  for (const value of boundaryValues) {
    console.log(`${value} => ${bucketOrderAmount(value)}`);
  }

  console.log("\n--- Production-oriented observations ---");
  console.log(
    "Keep CASE predicates mutually exclusive when possible so rule meaning does not depend on branch order."
  );
  console.log(
    "Use explicit NULL branches when missing data has business significance."
  );
  console.log(
    "Use parameter binding for runtime values rather than concatenating untrusted values into SQL."
  );
  console.log(
    "Move very large or frequently changing rule sets into database tables when configuration is more appropriate than hard-coded SQL."
  );
}

main();
