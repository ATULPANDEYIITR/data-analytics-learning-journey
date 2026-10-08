/**
 * SQL Analytics Patterns companion.
 *
 * This file models analytics patterns with JavaScript data structures and
 * event-driven processing. It intentionally uses JavaScript-specific Maps,
 * Sets, sorting, higher-order functions, and asynchronous workflow simulation
 * rather than translating the Python implementation line by line.
 */

"use strict";

class AnalyticsEvent {
  constructor(userId, occurredAt, eventName, properties = {}) {
    if (!Number.isInteger(userId) || userId <= 0) {
      throw new TypeError("userId must be a positive integer");
    }
    if (!(occurredAt instanceof Date) || Number.isNaN(occurredAt.getTime())) {
      throw new TypeError("occurredAt must be a valid Date");
    }
    if (!eventName) {
      throw new TypeError("eventName is required");
    }

    this.userId = userId;
    this.occurredAt = occurredAt;
    this.eventName = eventName;
    this.properties = Object.freeze({ ...properties });
  }
}

const users = [
  { userId: 1, signupDate: "2026-01-02", country: "IN", channel: "organic" },
  { userId: 2, signupDate: "2026-01-03", country: "IN", channel: "paid" },
  { userId: 3, signupDate: "2026-01-08", country: "US", channel: "organic" },
  { userId: 4, signupDate: "2026-01-15", country: "IN", channel: "referral" },
  { userId: 5, signupDate: "2026-02-02", country: "DE", channel: "paid" },
  { userId: 6, signupDate: "2026-02-05", country: "IN", channel: "organic" },
  { userId: 7, signupDate: "2026-02-09", country: "US", channel: "paid" },
  { userId: 8, signupDate: "2026-02-20", country: "IN", channel: "referral" },
];

const events = [
  new AnalyticsEvent(1, new Date("2026-01-02T09:00:00Z"), "signup"),
  new AnalyticsEvent(1, new Date("2026-01-02T09:10:00Z"), "view_product"),
  new AnalyticsEvent(1, new Date("2026-01-02T09:20:00Z"), "add_to_cart"),
  new AnalyticsEvent(1, new Date("2026-01-02T09:30:00Z"), "checkout_started"),
  new AnalyticsEvent(1, new Date("2026-01-02T09:40:00Z"), "purchase", { amount: 300 }),
  new AnalyticsEvent(1, new Date("2026-01-09T10:00:00Z"), "login"),
  new AnalyticsEvent(2, new Date("2026-01-03T09:00:00Z"), "signup"),
  new AnalyticsEvent(2, new Date("2026-01-03T09:10:00Z"), "view_product"),
  new AnalyticsEvent(2, new Date("2026-01-03T09:20:00Z"), "add_to_cart"),
  new AnalyticsEvent(2, new Date("2026-01-03T09:30:00Z"), "checkout_started"),
  new AnalyticsEvent(2, new Date("2026-01-03T09:40:00Z"), "purchase", { amount: 180 }),
  new AnalyticsEvent(3, new Date("2026-01-08T09:00:00Z"), "signup"),
  new AnalyticsEvent(3, new Date("2026-01-08T09:10:00Z"), "view_product"),
  new AnalyticsEvent(3, new Date("2026-01-15T09:00:00Z"), "login"),
  new AnalyticsEvent(4, new Date("2026-01-15T09:00:00Z"), "signup"),
  new AnalyticsEvent(4, new Date("2026-01-15T09:10:00Z"), "view_product"),
  new AnalyticsEvent(4, new Date("2026-01-15T09:20:00Z"), "add_to_cart"),
  new AnalyticsEvent(5, new Date("2026-02-02T09:00:00Z"), "signup"),
  new AnalyticsEvent(5, new Date("2026-02-02T09:10:00Z"), "view_product"),
  new AnalyticsEvent(5, new Date("2026-02-02T09:20:00Z"), "add_to_cart"),
  new AnalyticsEvent(5, new Date("2026-02-02T09:30:00Z"), "checkout_started"),
  new AnalyticsEvent(5, new Date("2026-02-02T09:40:00Z"), "purchase", { amount: 230 }),
  new AnalyticsEvent(5, new Date("2026-02-09T09:00:00Z"), "login"),
  new AnalyticsEvent(6, new Date("2026-02-05T09:00:00Z"), "signup"),
  new AnalyticsEvent(6, new Date("2026-02-05T09:10:00Z"), "view_product"),
  new AnalyticsEvent(6, new Date("2026-02-12T09:00:00Z"), "login"),
  new AnalyticsEvent(7, new Date("2026-02-09T09:00:00Z"), "signup"),
  new AnalyticsEvent(7, new Date("2026-02-09T09:10:00Z"), "view_product"),
  new AnalyticsEvent(8, new Date("2026-02-20T09:00:00Z"), "signup"),
  new AnalyticsEvent(8, new Date("2026-02-20T09:10:00Z"), "view_product"),
  new AnalyticsEvent(8, new Date("2026-02-20T09:20:00Z"), "add_to_cart"),
];

const products = [
  { id: "P100", name: "Analytics Platform", revenue: 18200 },
  { id: "P200", name: "Operations Suite", revenue: 15700 },
  { id: "P300", name: "Data Connector", revenue: 15700 },
  { id: "P400", name: "Audit Module", revenue: 11900 },
  { id: "P500", name: "Forecasting Module", revenue: 9400 },
];

function monthKey(value) {
  const date = value instanceof Date ? value : new Date(`${value}T00:00:00Z`);
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

function monthDifference(start, end) {
  const a = new Date(`${start}T00:00:00Z`);
  const b = new Date(`${end}T00:00:00Z`);
  return (
    (b.getUTCFullYear() - a.getUTCFullYear()) * 12 +
    b.getUTCMonth() -
    a.getUTCMonth()
  );
}

function topNByRevenue(items, n) {
  if (!Number.isInteger(n) || n <= 0) {
    throw new RangeError("n must be a positive integer");
  }

  const sorted = [...items].sort(
    (a, b) => b.revenue - a.revenue || a.id.localeCompare(b.id)
  );

  let rank = 0;
  let previousRevenue = null;

  return sorted
    .map((item, index) => {
      if (item.revenue !== previousRevenue) {
        rank += 1;
      }
      previousRevenue = item.revenue;

      return {
        rank,
        position: index + 1,
        ...item,
      };
    })
    .filter((item) => item.rank <= n);
}

function prepareCohorts(userRows) {
  return userRows.map((user) => ({
    ...user,
    cohortMonth: monthKey(user.signupDate),
  }));
}

function calculateRetention(userRows, eventRows) {
  const userMap = new Map(userRows.map((user) => [user.userId, user]));
  const activePeriods = new Map();

  for (const event of eventRows) {
    if (!["login", "view_product", "add_to_cart", "purchase"].includes(event.eventName)) {
      continue;
    }

    const user = userMap.get(event.userId);
    if (!user) continue;

    const period = monthDifference(user.signupDate, event.occurredAt.toISOString().slice(0, 10));
    const key = `${user.userId}:${period}`;
    activePeriods.set(key, true);
  }

  const cohorts = new Map();

  for (const user of userRows) {
    const cohort = monthKey(user.signupDate);
    if (!cohorts.has(cohort)) cohorts.set(cohort, []);
    cohorts.get(cohort).push(user.userId);
  }

  return [...cohorts.entries()].flatMap(([cohortMonth, memberIds]) => {
    return [0, 1].map((period) => {
      const retained = memberIds.filter((userId) =>
        activePeriods.has(`${userId}:${period}`)
      ).length;

      return {
        cohortMonth,
        period,
        cohortSize: memberIds.length,
        retainedUsers: retained,
        retentionPct: memberIds.length
          ? Number(((retained / memberIds.length) * 100).toFixed(1))
          : 0,
      };
    });
  });
}

function buildFunnel(userRows, eventRows) {
  const stages = [
    ["signup", "signup"],
    ["product_view", "view_product"],
    ["cart", "add_to_cart"],
    ["checkout", "checkout_started"],
    ["purchase", "purchase"],
  ];

  const eventsByUser = new Map();

  for (const event of eventRows) {
    if (!eventsByUser.has(event.userId)) {
      eventsByUser.set(event.userId, new Set());
    }
    eventsByUser.get(event.userId).add(event.eventName);
  }

  let previous = null;

  return stages.map(([stage, eventName]) => {
    const usersAtStage = userRows.filter((user) =>
      eventsByUser.get(user.userId)?.has(eventName)
    ).length;

    const conversion =
      previous === null
        ? usersAtStage > 0 ? 100 : 0
        : previous === 0 ? 0 : Number(((usersAtStage / previous) * 100).toFixed(1));

    previous = usersAtStage;

    return {
      stage,
      users: usersAtStage,
      conversionFromPreviousPct: conversion,
    };
  });
}

function segmentUsers(userRows, eventRows) {
  const metrics = new Map();

  for (const user of userRows) {
    metrics.set(user.userId, {
      activity: 0,
      purchases: 0,
      revenue: 0,
    });
  }

  for (const event of eventRows) {
    const metric = metrics.get(event.userId);
    if (!metric) continue;

    if (["login", "view_product", "add_to_cart"].includes(event.eventName)) {
      metric.activity += 1;
    }

    if (event.eventName === "purchase") {
      metric.purchases += 1;
      metric.revenue += Number(event.properties.amount ?? 0);
    }
  }

  return userRows.map((user) => {
    const metric = metrics.get(user.userId);

    let segment;
    if (metric.purchases >= 2 || metric.revenue >= 300) {
      segment = "high_value";
    } else if (metric.purchases > 0) {
      segment = "buyer";
    } else if (metric.activity >= 3) {
      segment = "engaged_non_buyer";
    } else {
      segment = "low_activity";
    }

    return {
      ...user,
      ...metric,
      segment,
    };
  });
}

function segmentSummary(rows) {
  const groups = new Map();

  for (const row of rows) {
    if (!groups.has(row.segment)) groups.set(row.segment, []);
    groups.get(row.segment).push(row);
  }

  return [...groups.entries()].map(([segment, members]) => {
    const revenue = members.reduce((sum, row) => sum + row.revenue, 0);
    const buyers = members.filter((row) => row.purchases > 0).length;

    return {
      segment,
      users: members.length,
      buyers,
      buyerRatePct: Number(((buyers / members.length) * 100).toFixed(1)),
      revenue: Number(revenue.toFixed(2)),
    };
  });
}

class AnalyticsPipeline {
  constructor() {
    this.handlers = new Map();
  }

  on(eventType, handler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType).push(handler);
  }

  async publish(eventType, payload) {
    const handlers = this.handlers.get(eventType) ?? [];

    // Promise.all makes the event pipeline concurrent. In production,
    // handlers that update shared state would need transaction boundaries
    // or another consistency mechanism.
    await Promise.all(handlers.map((handler) => handler(payload)));
  }
}

async function demonstrateEventDrivenAnalytics() {
  const pipeline = new AnalyticsPipeline();
  let purchaseCount = 0;
  let purchaseRevenue = 0;

  pipeline.on("purchase", async (event) => {
    purchaseCount += 1;
    purchaseRevenue += Number(event.properties.amount ?? 0);
  });

  pipeline.on("purchase", async (event) => {
    if (Number(event.properties.amount ?? 0) >= 250) {
      console.log(`High-value purchase observed for user ${event.userId}`);
    }
  });

  await Promise.all(
    events
      .filter((event) => event.eventName === "purchase")
      .map((event) => pipeline.publish("purchase", event))
  );

  return {
    purchaseCount,
    purchaseRevenue: Number(purchaseRevenue.toFixed(2)),
  };
}

function print(title, value) {
  console.log(`\n=== ${title} ===`);
  console.table(value);
}

async function main() {
  print("Top-N by Revenue", topNByRevenue(products, 3));
  print("Cohort Preparation", prepareCohorts(users));
  print("Retention", calculateRetention(users, events));
  print("Funnel", buildFunnel(users, events));

  const segments = segmentUsers(users, events);
  print("User Segments", segments);
  print("Segment Performance", segmentSummary(segments));

  const eventResult = await demonstrateEventDrivenAnalytics();
  print("Event-Driven Purchase Metrics", [eventResult]);

  try {
    topNByRevenue(products, -1);
  } catch (error) {
    console.log("\nValidation failure:", error.message);
  }
}

main().catch((error) => {
  console.error("Analytics pipeline failed:", error);
  process.exitCode = 1;
});
