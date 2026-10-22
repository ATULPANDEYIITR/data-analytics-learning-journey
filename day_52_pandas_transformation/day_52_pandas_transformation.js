"use strict";

const orders = [
  {
    orderId: 1001,
    customer: "Asha",
    region: "North",
    product: "Laptop",
    quantity: 2,
    unitPrice: 75000,
    status: "completed"
  },
  {
    orderId: 1002,
    customer: "Ravi",
    region: "South",
    product: "Monitor",
    quantity: 3,
    unitPrice: 18000,
    status: "completed"
  },
  {
    orderId: 1003,
    customer: "Meera",
    region: "West",
    product: "Keyboard",
    quantity: 5,
    unitPrice: 3500,
    status: "pending"
  },
  {
    orderId: 1004,
    customer: "Kabir",
    region: "East",
    product: "Laptop",
    quantity: 1,
    unitPrice: 82000,
    status: "cancelled"
  },
  {
    orderId: 1005,
    customer: "Asha",
    region: "North",
    product: "Mouse",
    quantity: 4,
    unitPrice: 1500,
    status: "completed"
  },
  {
    orderId: 1006,
    customer: "Ravi",
    region: "South",
    product: "Laptop",
    quantity: 2,
    unitPrice: 78000,
    status: "completed"
  },
  {
    orderId: 1007,
    customer: "Meera",
    region: "West",
    product: "Monitor",
    quantity: 2,
    unitPrice: 19500,
    status: "pending"
  }
];

function validateOrders(data) {
  if (!Array.isArray(data)) {
    throw new TypeError("Orders must be an array.");
  }

  const required = [
    "orderId",
    "customer",
    "region",
    "product",
    "quantity",
    "unitPrice",
    "status"
  ];

  const ids = new Set();

  for (const order of data) {
    for (const field of required) {
      if (!(field in order)) {
        throw new Error(`Missing field: ${field}`);
      }
    }

    if (ids.has(order.orderId)) {
      throw new Error(`Duplicate order ID: ${order.orderId}`);
    }

    if (!Number.isInteger(order.quantity) || order.quantity <= 0) {
      throw new Error(`Invalid quantity for order ${order.orderId}`);
    }

    if (!Number.isFinite(order.unitPrice) || order.unitPrice < 0) {
      throw new Error(`Invalid unit price for order ${order.orderId}`);
    }

    ids.add(order.orderId);
  }
}

function normalizeStatus(status) {
  const replacements = new Map([
    ["completed", "Completed"],
    ["pending", "Pending"],
    ["cancelled", "Cancelled"]
  ]);

  return replacements.get(status) ?? status;
}

function classifyPriority(order) {
  if (order.grossAmount >= 100000) return "High";
  if (order.grossAmount >= 30000) return "Medium";
  return "Low";
}

function transformOrders(input) {
  validateOrders(input);

  // map creates a new collection instead of mutating the source records.
  return input.map((order) => {
    const grossAmount = order.quantity * order.unitPrice;

    // Object spread creates a transformed object while preserving source fields.
    const transformed = {
      ...order,
      status: normalizeStatus(order.status),
      regionCode: {
        North: "N",
        South: "S",
        East: "E",
        West: "W"
      }[order.region] ?? "UNKNOWN",
      grossAmount
    };

    transformed.priority = classifyPriority(transformed);

    // assign-style transformation in JavaScript is represented by adding
    // derived properties after the base object has been created.
    transformed.discountRate =
      grossAmount >= 100000
        ? 0.10
        : grossAmount >= 50000
          ? 0.05
          : 0;

    transformed.netAmount =
      grossAmount * (1 - transformed.discountRate);

    transformed.customerNormalized =
      String(order.customer).trim().replace(/\s+/g, " ");

    return transformed;
  });
}

function filterActiveOrders(data) {
  return data.filter(
    (order) =>
      order.status !== "Cancelled" &&
      order.netAmount >= 30000
  );
}

function sortByBusinessPriority(data) {
  const priorityRank = {
    High: 0,
    Medium: 1,
    Low: 2
  };

  return [...data].sort((a, b) => {
    const priorityDifference =
      priorityRank[a.priority] - priorityRank[b.priority];

    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return b.netAmount - a.netAmount;
  });
}

function buildRegionalReport(data) {
  const report = new Map();

  for (const order of data) {
    if (order.status !== "Completed") continue;

    const current = report.get(order.region) ?? {
      region: order.region,
      completedOrders: 0,
      totalQuantity: 0,
      totalRevenue: 0
    };

    current.completedOrders += 1;
    current.totalQuantity += order.quantity;
    current.totalRevenue += order.netAmount;

    report.set(order.region, current);
  }

  return [...report.values()].sort(
    (a, b) => b.totalRevenue - a.totalRevenue
  );
}

async function processOrders(data) {
  // An async boundary models a pipeline that could later call an API or database.
  await Promise.resolve();

  const transformed = transformOrders(data);
  const active = filterActiveOrders(transformed);
  const sorted = sortByBusinessPriority(active);
  const regionalReport = buildRegionalReport(transformed);

  return {
    transformed,
    active: sorted,
    regionalReport
  };
}

async function main() {
  try {
    const result = await processOrders(orders);

    console.log("TRANSFORMED ORDERS");
    console.table(result.transformed);

    console.log("FILTERED AND SORTED ORDERS");
    console.table(result.active);

    console.log("REGIONAL REPORT");
    console.table(result.regionalReport);

    // replace-like normalization can be safely applied to a selected field.
    const statusValues = ["completed", "pending", "cancelled", "unknown"];
    console.log(
      "STATUS NORMALIZATION:",
      statusValues.map(normalizeStatus)
    );

    // Demonstrate validation failure handling.
    const invalidOrders = [
      {
        ...orders[0],
        quantity: 0
      }
    ];

    try {
      transformOrders(invalidOrders);
    } catch (error) {
      console.log(
        `Validation correctly rejected invalid data: ${error.message}`
      );
    }
  } catch (error) {
    console.error(`Order transformation failed: ${error.message}`);
    process.exitCode = 1;
  }
}

main();
