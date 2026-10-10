"use strict";

/*
 * Business Analytics Event and KPI Engine
 *
 * This JavaScript implementation uses Node.js features to model an analytics
 * pipeline as an event-driven system. It focuses on metric computation,
 * asynchronous ingestion, validation, filtering, grouping, and KPI snapshots.
 *
 * Run with:
 *   node business_analytics.js
 */

const orders = [
  {
    id: 1001,
    date: "2026-01-05",
    customer: "Atlas Consulting",
    segment: "Corporate",
    region: "North",
    status: "Completed",
    discount: 0.05,
    items: [
      { product: "Business Laptop", category: "Electronics", quantity: 2, price: 1200, cost: 820 },
      { product: "Security Monitor", category: "Electronics", quantity: 1, price: 650, cost: 390 }
    ]
  },
  {
    id: 1002,
    date: "2026-01-14",
    customer: "BluePeak Retail",
    segment: "Small Business",
    region: "South",
    status: "Completed",
    discount: 0.10,
    items: [
      { product: "Laser Printer", category: "Office Equipment", quantity: 3, price: 550, cost: 340 }
    ]
  },
  {
    id: 1003,
    date: "2026-02-03",
    customer: "Cedar Finance",
    segment: "Corporate",
    region: "East",
    status: "Returned",
    discount: 0,
    items: [
      { product: "Analytics Suite", category: "Software", quantity: 2, price: 900, cost: 180 }
    ]
  },
  {
    id: 1004,
    date: "2026-02-18",
    customer: "Delta Health",
    segment: "Corporate",
    region: "West",
    status: "Completed",
    discount: 0.15,
    items: [
      { product: "Conference Desk", category: "Furniture", quantity: 2, price: 780, cost: 470 },
      { product: "Ergonomic Chair", category: "Furniture", quantity: 4, price: 360, cost: 210 }
    ]
  },
  {
    id: 1005,
    date: "2026-03-09",
    customer: "Evergreen Traders",
    segment: "Small Business",
    region: "North",
    status: "Cancelled",
    discount: 0,
    items: [
      { product: "Network Router", category: "Electronics", quantity: 5, price: 420, cost: 260 }
    ]
  },
  {
    id: 1006,
    date: "2026-03-22",
    customer: "Falcon Services",
    segment: "Consumer",
    region: "South",
    status: "Completed",
    discount: 0.05,
    items: [
      { product: "Document Scanner", category: "Office Equipment", quantity: 3, price: 310, cost: 180 },
      { product: "Analytics Suite", category: "Software", quantity: 1, price: 900, cost: 180 }
    ]
  },
  {
    id: 1007,
    date: "2026-04-06",
    customer: "Granite Labs",
    segment: "Corporate",
    region: "East",
    status: "Completed",
    discount: 0.10,
    items: [
      { product: "Business Laptop", category: "Electronics", quantity: 4, price: 1200, cost: 820 }
    ]
  },
  {
    id: 1008,
    date: "2026-04-25",
    customer: "Horizon Media",
    segment: "Small Business",
    region: "West",
    status: "Pending",
    discount: 0.05,
    items: [
      { product: "Conference Desk", category: "Furniture", quantity: 1, price: 780, cost: 470 }
    ]
  }
];

const events = new EventTarget();

function money(value) {
  return Number(value.toFixed(2));
}

function assertValidOrder(order) {
  if (!Number.isInteger(order.id)) {
    throw new TypeError("Order ID must be an integer.");
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(order.date)) {
    throw new Error(`Invalid date for order ${order.id}.`);
  }

  const validStatuses = new Set([
    "Completed",
    "Cancelled",
    "Returned",
    "Pending"
  ]);

  if (!validStatuses.has(order.status)) {
    throw new Error(`Unsupported order status: ${order.status}`);
  }

  if (order.discount < 0 || order.discount > 1) {
    throw new RangeError(`Invalid discount for order ${order.id}.`);
  }

  if (!Array.isArray(order.items) || order.items.length === 0) {
    throw new Error(`Order ${order.id} has no line items.`);
  }

  for (const item of order.items) {
    if (!Number.isInteger(item.quantity) || item.quantity <= 0) {
      throw new RangeError(`Invalid quantity for ${item.product}.`);
    }

    if (item.cost < 0 || item.cost > item.price) {
      throw new RangeError(`Invalid economics for ${item.product}.`);
    }
  }
}

function netLineRevenue(item, discount) {
  return item.quantity * item.price * (1 - discount);
}

function lineProfit(item, discount) {
  return item.quantity *
    (item.price * (1 - discount) - item.cost);
}

function completedOrders(data) {
  return data.filter(order => order.status === "Completed");
}

function orderRevenue(order) {
  return order.items.reduce(
    (sum, item) => sum + netLineRevenue(item, order.discount),
    0
  );
}

function orderProfit(order) {
  return order.items.reduce(
    (sum, item) => sum + lineProfit(item, order.discount),
    0
  );
}

function aggregateBy(data, keySelector, valueSelector) {
  const result = new Map();

  for (const record of data) {
    const key = keySelector(record);
    const value = valueSelector(record);

    result.set(key, (result.get(key) ?? 0) + value);
  }

  return [...result.entries()]
    .map(([key, value]) => ({ key, value: money(value) }))
    .sort((a, b) => b.value - a.value);
}

function revenueByRegion(data) {
  return aggregateBy(
    completedOrders(data),
    order => order.region,
    orderRevenue
  );
}

function revenueBySegment(data) {
  return aggregateBy(
    completedOrders(data),
    order => order.segment,
    orderRevenue
  );
}

function revenueByCategory(data) {
  const categoryRevenue = new Map();

  for (const order of completedOrders(data)) {
    for (const item of order.items) {
      const revenue = netLineRevenue(item, order.discount);
      categoryRevenue.set(
        item.category,
        (categoryRevenue.get(item.category) ?? 0) + revenue
      );
    }
  }

  return [...categoryRevenue.entries()]
    .map(([category, revenue]) => ({
      category,
      revenue: money(revenue)
    }))
    .sort((a, b) => b.revenue - a.revenue);
}

function productPerformance(data) {
  const performance = new Map();

  for (const order of completedOrders(data)) {
    for (const item of order.items) {
      if (!performance.has(item.product)) {
        performance.set(item.product, {
          product: item.product,
          category: item.category,
          units: 0,
          revenue: 0,
          profit: 0
        });
      }

      const metric = performance.get(item.product);
      metric.units += item.quantity;
      metric.revenue += netLineRevenue(item, order.discount);
      metric.profit += lineProfit(item, order.discount);
    }
  }

  return [...performance.values()]
    .map(metric => ({
      ...metric,
      revenue: money(metric.revenue),
      profit: money(metric.profit),
      margin: money(
        metric.revenue === 0
          ? 0
          : (metric.profit / metric.revenue) * 100
      )
    }))
    .sort((a, b) => b.revenue - a.revenue);
}

function customerLifetimeValue(data) {
  const customers = new Map();

  for (const order of completedOrders(data)) {
    const current = customers.get(order.customer) ?? {
      customer: order.customer,
      segment: order.segment,
      orders: 0,
      revenue: 0
    };

    current.orders += 1;
    current.revenue += orderRevenue(order);
    customers.set(order.customer, current);
  }

  return [...customers.values()]
    .map(customer => ({
      ...customer,
      revenue: money(customer.revenue)
    }))
    .sort((a, b) => b.revenue - a.revenue);
}

function monthlyRevenue(data) {
  const monthly = aggregateBy(
    completedOrders(data),
    order => order.date.slice(0, 7),
    orderRevenue
  );

  return monthly.sort((a, b) => a.key.localeCompare(b.key));
}

function calculateKpis(data) {
  const valid = data.filter(order => {
    try {
      assertValidOrder(order);
      return true;
    } catch (error) {
      console.error(`Validation rejected order: ${error.message}`);
      return false;
    }
  });

  const completed = completedOrders(valid);
  const revenue = completed.reduce((sum, order) => sum + orderRevenue(order), 0);
  const profit = completed.reduce((sum, order) => sum + orderProfit(order), 0);
  const completedCount = completed.length;

  return {
    totalOrders: valid.length,
    completedOrders: completedCount,
    cancelledOrders: valid.filter(o => o.status === "Cancelled").length,
    returnedOrders: valid.filter(o => o.status === "Returned").length,
    pendingOrders: valid.filter(o => o.status === "Pending").length,
    revenue: money(revenue),
    grossProfit: money(profit),
    grossMarginPercent: money(revenue ? (profit / revenue) * 100 : 0),
    averageOrderValue: money(completedCount ? revenue / completedCount : 0)
  };
}

/*
 * Event-driven analytics is useful when a reporting system receives data
 * incrementally. The listener recomputes a snapshot after ingestion rather
 * than coupling ingestion logic directly to every KPI implementation.
 */
events.addEventListener("analytics:completed", event => {
  const dataset = event.detail;
  const kpis = calculateKpis(dataset);

  console.log("\n=== KPI SNAPSHOT ===");
  console.table(kpis);

  console.log("\n=== REVENUE BY REGION ===");
  console.table(revenueByRegion(dataset));

  console.log("\n=== REVENUE BY SEGMENT ===");
  console.table(revenueBySegment(dataset));

  console.log("\n=== REVENUE BY CATEGORY ===");
  console.table(revenueByCategory(dataset));

  console.log("\n=== PRODUCT PERFORMANCE ===");
  console.table(productPerformance(dataset));

  console.log("\n=== CUSTOMER LIFETIME VALUE ===");
  console.table(customerLifetimeValue(dataset));

  console.log("\n=== MONTHLY REVENUE ===");
  console.table(monthlyRevenue(dataset));
});

async function ingestOrders(source) {
  /*
   * The Promise models asynchronous ingestion without requiring an external
   * service. A real implementation could replace this boundary with a stream,
   * API response, message queue, or database cursor.
   */
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(structuredClone(source));
    }, 20);
  });
}

async function runAnalytics() {
  try {
    const dataset = await ingestOrders(orders);

    for (const order of dataset) {
      assertValidOrder(order);
    }

    events.dispatchEvent(
      new CustomEvent("analytics:completed", {
        detail: dataset
      })
    );

    const topProduct = productPerformance(dataset)[0];

    if (topProduct) {
      console.log(
        `\nHighest-revenue product: ${topProduct.product} (${topProduct.revenue})`
      );
    }
  } catch (error) {
    console.error(`Analytics pipeline failed: ${error.message}`);
    process.exitCode = 1;
  }
}

runAnalytics();
