'use strict';

/*
 * Pandas-style grouping concepts implemented with standard Node.js JavaScript.
 *
 * The model uses:
 * - Map-based grouping for groupby behavior
 * - reducer functions for aggregation
 * - group-level derived values for transform behavior
 * - nested maps for pivot_table behavior
 * - frequency maps for crosstab behavior
 * - event-driven policy notifications
 *
 * Runtime: Node.js 18+
 */

const rawOrders = [
  [1001, '2026-01-05', 'North', 'Cloud', 'Online', 'Compute', 'Enterprise', 8, 1200, 0.05, false],
  [1002, '2026-01-07', 'North', 'Security', 'Partner', 'Firewall', 'Enterprise', 4, 2100, 0.00, false],
  [1003, '2026-01-09', 'South', 'Cloud', 'Online', 'Storage', 'SMB', 15, 400, 0.10, false],
  [1004, '2026-01-11', 'West', 'Data', 'Direct', 'Analytics', 'Enterprise', 6, 1800, 0.05, false],
  [1005, '2026-01-13', 'East', 'Security', 'Online', 'Identity', 'SMB', 20, 250, 0.00, true],
  [1006, '2026-01-15', 'North', 'Data', 'Partner', 'Analytics', 'SMB', 5, 1800, 0.15, false],
  [1007, '2026-01-18', 'South', 'Security', 'Direct', 'Firewall', 'Enterprise', 3, 2100, 0.05, false],
  [1008, '2026-01-20', 'West', 'Cloud', 'Online', 'Compute', 'SMB', 12, 1200, 0.00, false],
  [1009, '2026-01-22', 'East', 'Data', 'Direct', 'Analytics', 'Enterprise', 7, 1800, 0.10, false],
  [1010, '2026-01-25', 'North', 'Cloud', 'Partner', 'Storage', 'SMB', 30, 400, 0.05, false],
  [1011, '2026-02-02', 'South', 'Cloud', 'Online', 'Compute', 'Enterprise', 5, 1200, 0.00, false],
  [1012, '2026-02-04', 'West', 'Security', 'Partner', 'Identity', 'SMB', 18, 250, 0.10, true],
  [1013, '2026-02-06', 'East', 'Cloud', 'Direct', 'Storage', 'SMB', 22, 400, 0.05, false],
  [1014, '2026-02-08', 'North', 'Data', 'Online', 'Analytics', 'Enterprise', 4, 1800, 0.00, false],
  [1015, '2026-02-11', 'South', 'Security', 'Online', 'Firewall', 'SMB', 9, 2100, 0.15, false],
  [1016, '2026-02-14', 'West', 'Cloud', 'Direct', 'Compute', 'Enterprise', 10, 1200, 0.05, false],
  [1017, '2026-02-17', 'East', 'Security', 'Partner', 'Identity', 'Enterprise', 11, 250, 0.00, false],
  [1018, '2026-02-20', 'North', 'Data', 'Direct', 'Analytics', 'SMB', 8, 1800, 0.10, true]
];

const columns = [
  'orderId', 'orderDate', 'region', 'department', 'channel',
  'product', 'customerSegment', 'units', 'unitPrice',
  'discount', 'returned'
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function parseOrders(rows) {
  const seenIds = new Set();

  return rows.map((row) => {
    assert(row.length === columns.length, 'Unexpected order column count.');

    const order = Object.fromEntries(
      columns.map((column, index) => [column, row[index]])
    );

    assert(Number.isInteger(order.orderId), 'Order ID must be an integer.');
    assert(!seenIds.has(order.orderId), `Duplicate order ID: ${order.orderId}`);
    seenIds.add(order.orderId);

    assert(order.units > 0, `Units must be positive for ${order.orderId}.`);
    assert(order.unitPrice >= 0, `Price cannot be negative for ${order.orderId}.`);
    assert(
      order.discount >= 0 && order.discount <= 1,
      `Invalid discount for ${order.orderId}.`
    );

    order.date = new Date(`${order.orderDate}T00:00:00Z`);
    order.revenue = order.units * order.unitPrice;
    order.netRevenue = order.revenue * (1 - order.discount);
    order.month = order.orderDate.slice(0, 7);
    order.highValue = order.netRevenue >= 5000;

    return order;
  });
}

function groupBy(rows, keySelector) {
  const groups = new Map();

  for (const row of rows) {
    const key = keySelector(row);

    if (!groups.has(key)) {
      groups.set(key, []);
    }

    groups.get(key).push(row);
  }

  return groups;
}

function aggregate(rows, specification) {
  const result = {};

  for (const [name, reducer] of Object.entries(specification)) {
    result[name] = reducer(rows);
  }

  return result;
}

const aggregators = {
  count: (rows) => rows.length,
  sum: (field) => (rows) =>
    rows.reduce((total, row) => total + row[field], 0),
  mean: (field) => (rows) => {
    if (rows.length === 0) return null;
    return rows.reduce((total, row) => total + row[field], 0) / rows.length;
  },
  min: (field) => (rows) =>
    rows.length === 0 ? null : Math.min(...rows.map((row) => row[field])),
  max: (field) => (rows) =>
    rows.length === 0 ? null : Math.max(...rows.map((row) => row[field])),
  countWhere: (predicate) => (rows) =>
    rows.reduce((count, row) => count + (predicate(row) ? 1 : 0), 0)
};

function groupAggregate(rows, keySelector, specification) {
  const groups = groupBy(rows, keySelector);

  return [...groups.entries()].map(([key, group]) => ({
    key,
    ...aggregate(group, specification)
  }));
}

function transform(rows, keySelector, valueSelector, reducer) {
  const groups = groupBy(rows, keySelector);
  const groupValues = new Map();

  for (const [key, group] of groups) {
    groupValues.set(key, reducer(group.map(valueSelector)));
  }

  return rows.map((row) => ({
    ...row,
    transformedValue: groupValues.get(keySelector(row))
  }));
}

function pivotTable(rows, rowSelector, columnSelector, valueSelector, reducer) {
  const table = new Map();

  for (const row of rows) {
    const rowKey = rowSelector(row);
    const columnKey = columnSelector(row);

    if (!table.has(rowKey)) {
      table.set(rowKey, new Map());
    }

    const rowMap = table.get(rowKey);

    if (!rowMap.has(columnKey)) {
      rowMap.set(columnKey, []);
    }

    rowMap.get(columnKey).push(valueSelector(row));
  }

  const result = [];

  for (const [rowKey, rowMap] of table) {
    const output = { rowKey };

    for (const [columnKey, values] of rowMap) {
      output[columnKey] = reducer(values);
    }

    result.push(output);
  }

  return result;
}

function crosstab(rows, rowSelector, columnSelector) {
  const counts = new Map();

  for (const row of rows) {
    const rowKey = rowSelector(row);
    const columnKey = columnSelector(row);

    if (!counts.has(rowKey)) {
      counts.set(rowKey, new Map());
    }

    const rowCounts = counts.get(rowKey);
    rowCounts.set(columnKey, (rowCounts.get(columnKey) ?? 0) + 1);
  }

  return counts;
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

class GroupingEventBus extends EventTarget {
  publish(eventName, detail) {
    this.dispatchEvent(new CustomEvent(eventName, { detail }));
  }
}

async function processAnalysis(rows) {
  const eventBus = new GroupingEventBus();

  eventBus.addEventListener('group-complete', (event) => {
    const { group, records } = event.detail;
    console.log(`Processed ${records} records for ${group}.`);
  });

  const regional = groupAggregate(
    rows,
    (row) => row.region,
    {
      orders: aggregators.count,
      units: aggregators.sum('units'),
      netRevenue: aggregators.sum('netRevenue'),
      returnedOrders: aggregators.countWhere((row) => row.returned)
    }
  );

  for (const item of regional) {
    eventBus.publish('group-complete', {
      group: item.key,
      records: item.orders
    });
  }

  const department = groupAggregate(
    rows,
    (row) => row.department,
    {
      orders: aggregators.count,
      averageRevenue: aggregators.mean('netRevenue'),
      minimumRevenue: aggregators.min('netRevenue'),
      maximumRevenue: aggregators.max('netRevenue')
    }
  );

  const regionRevenueTotals = transform(
    rows,
    (row) => row.region,
    (row) => row.netRevenue,
    (values) => values.reduce((sum, value) => sum + value, 0)
  );

  const transformedRows = regionRevenueTotals.map((row) => ({
    orderId: row.orderId,
    region: row.region,
    netRevenue: row.netRevenue,
    regionRevenue: row.transformedValue,
    regionShare: row.netRevenue / row.transformedValue
  }));

  const pivot = pivotTable(
    rows,
    (row) => row.region,
    (row) => row.channel,
    (row) => row.netRevenue,
    (values) => values.reduce((sum, value) => sum + value, 0)
  );

  const cross = crosstab(
    rows,
    (row) => row.department,
    (row) => row.channel
  );

  const highValueRows = rows.filter((row) => row.highValue);

  const highValueByRegion = groupAggregate(
    highValueRows,
    (row) => row.region,
    {
      orders: aggregators.count,
      revenue: aggregators.sum('netRevenue')
    }
  );

  return {
    regional,
    department,
    transformedRows,
    pivot,
    cross,
    highValueByRegion
  };
}

function printTable(title, rows) {
  console.log(`\n${title}`);
  console.table(rows);
}

function printCrosstab(cross) {
  const rows = [];

  for (const [department, channels] of cross) {
    rows.push({
      department,
      ...Object.fromEntries(channels)
    });
  }

  printTable('CROSSTAB: DEPARTMENT × CHANNEL', rows);
}

function validateAnalysis(rows, result) {
  const sourceRevenue = rows.reduce((sum, row) => sum + row.netRevenue, 0);
  const groupedRevenue = result.regional.reduce(
    (sum, row) => sum + row.netRevenue,
    0
  );

  assert(
    Math.abs(sourceRevenue - groupedRevenue) < 0.000001,
    'Grouped revenue failed reconciliation.'
  );

  assert(
    result.transformedRows.length === rows.length,
    'Transform must preserve row count.'
  );

  const firstRegion = rows[0].region;
  const firstRegionRows = result.transformedRows.filter(
    (row) => row.region === firstRegion
  );

  const share = firstRegionRows.reduce(
    (sum, row) => sum + row.regionShare,
    0
  );

  assert(
    Math.abs(share - 1) < 0.000001,
    'Region shares must sum to one.'
  );
}

async function main() {
  const orders = parseOrders(rawOrders);

  // Promise.resolve makes the workflow asynchronous without requiring
  // an external dependency or a network connection.
  const analysis = await processAnalysis(orders);

  validateAnalysis(orders, analysis);

  printTable(
    'REGION GROUPING',
    analysis.regional.map((row) => ({
      region: row.key,
      orders: row.orders,
      units: row.units,
      netRevenue: formatCurrency(row.netRevenue),
      returnedOrders: row.returnedOrders
    }))
  );

  printTable(
    'DEPARTMENT AGGREGATION',
    analysis.department.map((row) => ({
      department: row.key,
      orders: row.orders,
      averageRevenue: formatCurrency(row.averageRevenue),
      minimumRevenue: formatCurrency(row.minimumRevenue),
      maximumRevenue: formatCurrency(row.maximumRevenue)
    }))
  );

  printTable(
    'TRANSFORM-LIKE ROW METRICS',
    analysis.transformedRows.map((row) => ({
      orderId: row.orderId,
      region: row.region,
      netRevenue: formatCurrency(row.netRevenue),
      regionRevenue: formatCurrency(row.regionRevenue),
      regionShare: row.regionShare.toFixed(4)
    }))
  );

  printTable(
    'PIVOT TABLE: REGION × CHANNEL',
    analysis.pivot
  );

  printCrosstab(analysis.cross);

  printTable(
    'HIGH-VALUE ORDERS BY REGION',
    analysis.highValueByRegion
  );

  console.log('\nVALIDATION');
  console.log(`Orders: ${orders.length}`);
  console.log(
    `Net revenue: ${formatCurrency(
      orders.reduce((sum, row) => sum + row.netRevenue, 0)
    )}`
  );
  console.log('All grouping invariants passed.');
}

main().catch((error) => {
  console.error(`Analysis failed: ${error.message}`);
  process.exitCode = 1;
});
