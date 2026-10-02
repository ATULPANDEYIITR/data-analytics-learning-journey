'use strict';

/**
 * SQL Date & Time Companion
 *
 * This Node.js program provides a JavaScript-specific model of:
 * DATE, TIMESTAMP, INTERVAL, DATE_PART, DATE_TRUNC, time zones,
 * date arithmetic, temporal aggregation, and validation.
 *
 * JavaScript's built-in Date represents an instant in time rather than a
 * database DATE type. The program therefore keeps calendar dates as ISO
 * strings where no time-of-day semantics are intended and uses Date objects
 * for instants. This distinction prevents accidental timezone conversion of
 * date-only business values.
 */

const assert = require('node:assert/strict');


// ---------------------------------------------------------------------------
// DATE representation
// ---------------------------------------------------------------------------

function isValidIsoDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }

  const [year, month, day] = value.split('-').map(Number);
  const candidate = new Date(Date.UTC(year, month - 1, day));

  return (
    candidate.getUTCFullYear() === year &&
    candidate.getUTCMonth() + 1 === month &&
    candidate.getUTCDate() === day
  );
}

function parseSqlDate(value) {
  if (!isValidIsoDate(value)) {
    throw new RangeError(`Invalid SQL DATE value: ${value}`);
  }
  return value;
}

function addDaysToDateOnly(dateValue, days) {
  parseSqlDate(dateValue);

  const [year, month, day] = dateValue.split('-').map(Number);
  const result = new Date(Date.UTC(year, month - 1, day));
  result.setUTCDate(result.getUTCDate() + days);

  return result.toISOString().slice(0, 10);
}

function lastDayOfMonth(year, month) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function addMonthsToDateOnly(dateValue, months) {
  parseSqlDate(dateValue);

  const [year, month, day] = dateValue.split('-').map(Number);
  const zeroBasedMonth = month - 1 + months;

  const targetYear =
    year + Math.floor(zeroBasedMonth / 12);

  const targetMonth =
    ((zeroBasedMonth % 12) + 12) % 12 + 1;

  const targetDay = Math.min(
    day,
    lastDayOfMonth(targetYear, targetMonth)
  );

  return [
    String(targetYear).padStart(4, '0'),
    String(targetMonth).padStart(2, '0'),
    String(targetDay).padStart(2, '0'),
  ].join('-');
}


// ---------------------------------------------------------------------------
// TIMESTAMP and instant handling
// ---------------------------------------------------------------------------

function parseTimestamp(value) {
  if (typeof value !== 'string') {
    throw new TypeError('Timestamp must be a string');
  }

  const normalized = value.endsWith('Z')
    ? value
    : value.replace(/([+-]\d{2}:\d{2})$/, '$1');

  const timestamp = new Date(normalized);

  if (Number.isNaN(timestamp.getTime())) {
    throw new RangeError(`Invalid timestamp: ${value}`);
  }

  // A timestamp intended to represent a global instant should contain either
  // Z or an explicit numeric UTC offset. A bare local timestamp is rejected
  // rather than allowing the host machine's timezone to decide its meaning.
  if (!/[zZ]|[+-]\d{2}:\d{2}$/.test(value)) {
    throw new RangeError(
      'Timestamp requires Z or an explicit UTC offset'
    );
  }

  return timestamp;
}

function formatUtc(timestamp) {
  return new Date(timestamp.getTime()).toISOString();
}

function timestampToEpochSeconds(timestamp) {
  return timestamp.getTime() / 1000;
}

function addMilliseconds(timestamp, milliseconds) {
  return new Date(timestamp.getTime() + milliseconds);
}


// ---------------------------------------------------------------------------
// INTERVAL representation
// ---------------------------------------------------------------------------

class SqlInterval {
  constructor({ months = 0, days = 0, milliseconds = 0 } = {}) {
    if (![months, days, milliseconds].every(Number.isFinite)) {
      throw new TypeError('Interval components must be finite numbers');
    }

    this.months = Math.trunc(months);
    this.days = Math.trunc(days);
    this.milliseconds = Math.trunc(milliseconds);
  }

  toString() {
    const parts = [];

    if (this.months !== 0) {
      parts.push(`${this.months} month(s)`);
    }

    if (this.days !== 0) {
      parts.push(`${this.days} day(s)`);
    }

    if (this.milliseconds !== 0) {
      parts.push(`${this.milliseconds} ms`);
    }

    return parts.length === 0 ? '0' : parts.join(' + ');
  }
}

function addIntervalToDateOnly(dateValue, interval) {
  let result = addMonthsToDateOnly(dateValue, interval.months);
  result = addDaysToDateOnly(result, interval.days);

  if (interval.milliseconds !== 0) {
    throw new RangeError(
      'A date-only value cannot receive a clock-duration component'
    );
  }

  return result;
}


// ---------------------------------------------------------------------------
// DATE_PART
// ---------------------------------------------------------------------------

function datePart(part, timestamp) {
  const value = parseTimestamp(timestamp.toISOString());
  const field = part.toLowerCase();

  switch (field) {
    case 'year':
      return value.getUTCFullYear();

    case 'month':
      return value.getUTCMonth() + 1;

    case 'day':
      return value.getUTCDate();

    case 'hour':
      return value.getUTCHours();

    case 'minute':
      return value.getUTCMinutes();

    case 'second':
      return (
        value.getUTCSeconds() +
        value.getUTCMilliseconds() / 1000
      );

    case 'dow':
      // JavaScript uses Sunday=0, matching the PostgreSQL-style convention.
      return value.getUTCDay();

    case 'isodow': {
      const day = value.getUTCDay();
      return day === 0 ? 7 : day;
    }

    case 'doy': {
      const start = Date.UTC(value.getUTCFullYear(), 0, 1);
      const current = Date.UTC(
        value.getUTCFullYear(),
        value.getUTCMonth(),
        value.getUTCDate()
      );
      return Math.floor((current - start) / 86400000) + 1;
    }

    case 'epoch':
      return timestampToEpochSeconds(value);

    default:
      throw new RangeError(`Unsupported DATE_PART field: ${part}`);
  }
}


// ---------------------------------------------------------------------------
// DATE_TRUNC
// ---------------------------------------------------------------------------

function dateTrunc(part, timestamp) {
  const value = parseTimestamp(timestamp.toISOString());
  const field = part.toLowerCase();

  switch (field) {
    case 'year':
      return new Date(Date.UTC(
        value.getUTCFullYear(), 0, 1
      ));

    case 'quarter': {
      const quarterMonth =
        Math.floor(value.getUTCMonth() / 3) * 3;
      return new Date(Date.UTC(
        value.getUTCFullYear(), quarterMonth, 1
      ));
    }

    case 'month':
      return new Date(Date.UTC(
        value.getUTCFullYear(),
        value.getUTCMonth(),
        1
      ));

    case 'week': {
      // PostgreSQL-style weekly truncation is Monday-oriented.
      const day = value.getUTCDay();
      const mondayOffset = day === 0 ? 6 : day - 1;
      const result = new Date(value.getTime());
      result.setUTCDate(result.getUTCDate() - mondayOffset);
      result.setUTCHours(0, 0, 0, 0);
      return result;
    }

    case 'day':
      return new Date(Date.UTC(
        value.getUTCFullYear(),
        value.getUTCMonth(),
        value.getUTCDate()
      ));

    case 'hour':
      return new Date(Date.UTC(
        value.getUTCFullYear(),
        value.getUTCMonth(),
        value.getUTCDate(),
        value.getUTCHours()
      ));

    case 'minute':
      return new Date(Date.UTC(
        value.getUTCFullYear(),
        value.getUTCMonth(),
        value.getUTCDate(),
        value.getUTCHours(),
        value.getUTCMinutes()
      ));

    case 'second':
      return new Date(Date.UTC(
        value.getUTCFullYear(),
        value.getUTCMonth(),
        value.getUTCDate(),
        value.getUTCHours(),
        value.getUTCMinutes(),
        value.getUTCSeconds()
      ));

    default:
      throw new RangeError(`Unsupported DATE_TRUNC field: ${part}`);
  }
}


// ---------------------------------------------------------------------------
// Time-zone aware calendar calculations using Intl
// ---------------------------------------------------------------------------

function getZonedParts(timestamp, timeZone) {
  parseTimestamp(timestamp.toISOString());

  let formatter;

  try {
    formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hourCycle: 'h23',
    });
  } catch (error) {
    throw new RangeError(`Invalid IANA timezone: ${timeZone}`);
  }

  const parts = Object.fromEntries(
    formatter
      .formatToParts(timestamp)
      .filter(part => part.type !== 'literal')
      .map(part => [part.type, part.value])
  );

  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    hour: Number(parts.hour),
    minute: Number(parts.minute),
    second: Number(parts.second),
  };
}

function zonedDateKey(timestamp, timeZone) {
  const parts = getZonedParts(timestamp, timeZone);

  return [
    String(parts.year).padStart(4, '0'),
    String(parts.month).padStart(2, '0'),
    String(parts.day).padStart(2, '0'),
  ].join('-');
}

function zonedMonthKey(timestamp, timeZone) {
  return zonedDateKey(timestamp, timeZone).slice(0, 7);
}

function compareInstants(first, second) {
  return first.getTime() - second.getTime();
}


// ---------------------------------------------------------------------------
// Event-driven Pull-style temporal processing
// ---------------------------------------------------------------------------

class EventBus {
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
    const listeners = this.listeners.get(eventName) ?? [];

    for (const listener of listeners) {
      listener(payload);
    }
  }
}

class TemporalEventStore {
  constructor(eventBus) {
    this.eventBus = eventBus;
    this.events = [];
  }

  append(event) {
    if (!(event.occurredAt instanceof Date) ||
        Number.isNaN(event.occurredAt.getTime())) {
      throw new TypeError('Event must contain a valid Date');
    }

    this.events.push(Object.freeze({
      ...event,
      occurredAt: new Date(event.occurredAt.getTime()),
    }));

    this.events.sort((a, b) =>
      compareInstants(a.occurredAt, b.occurredAt)
    );

    this.eventBus.emit('event:stored', event);
  }

  findBetween(start, end) {
    if (start >= end) {
      throw new RangeError('Start must be before end');
    }

    return this.events.filter(event =>
      event.occurredAt >= start &&
      event.occurredAt < end
    );
  }

  groupByLocalDate(timeZone) {
    const groups = new Map();

    for (const event of this.events) {
      const key = zonedDateKey(event.occurredAt, timeZone);

      if (!groups.has(key)) {
        groups.set(key, []);
      }

      groups.get(key).push(event);
    }

    return groups;
  }
}


// ---------------------------------------------------------------------------
// ISO month boundaries
// ---------------------------------------------------------------------------

function monthStartUtc(year, month) {
  return new Date(Date.UTC(year, month - 1, 1));
}

function nextMonthStartUtc(year, month) {
  return new Date(Date.UTC(year, month, 1));
}

function monthlyUtcWindow(year, month) {
  const start = monthStartUtc(year, month);
  const end = nextMonthStartUtc(year, month);

  return Object.freeze({ start, end });
}


// ---------------------------------------------------------------------------
// Validation and business rules
// ---------------------------------------------------------------------------

function assertHalfOpenRange(start, end) {
  if (!(start instanceof Date) || !(end instanceof Date)) {
    throw new TypeError('Range endpoints must be Date objects');
  }

  if (start.getTime() >= end.getTime()) {
    throw new RangeError('Range must satisfy start < end');
  }
}

function filterEventsByRange(events, start, end) {
  assertHalfOpenRange(start, end);

  return events.filter(event =>
    event.occurredAt >= start &&
    event.occurredAt < end
  );
}

function calculateElapsedHours(start, end) {
  const startInstant = parseTimestamp(start);
  const endInstant = parseTimestamp(end);

  const milliseconds = endInstant.getTime() - startInstant.getTime();

  if (milliseconds < 0) {
    throw new RangeError('End timestamp precedes start timestamp');
  }

  return milliseconds / 3600000;
}


// ---------------------------------------------------------------------------
// Demonstrations
// ---------------------------------------------------------------------------

function demonstrateDate() {
  console.log('\n=== DATE ===');

  const orderDate = parseSqlDate('2026-10-02');

  console.log('Order date:', orderDate);
  console.log('Seven days later:', addDaysToDateOnly(orderDate, 7));
  console.log(
    'One calendar month later:',
    addMonthsToDateOnly('2026-01-31', 1)
  );
  console.log(
    'Leap-year month arithmetic:',
    addMonthsToDateOnly('2024-01-31', 1)
  );
}

function demonstrateTimestamp() {
  console.log('\n=== TIMESTAMP ===');

  const instant = parseTimestamp('2026-10-02T06:48:23+05:30');

  console.log('UTC:', formatUtc(instant));
  console.log('Epoch seconds:', timestampToEpochSeconds(instant));
  console.log(
    'After 90 seconds:',
    formatUtc(addMilliseconds(instant, 90000))
  );
}

function demonstrateInterval() {
  console.log('\n=== INTERVAL ===');

  const interval = new SqlInterval({
    months: 1,
    days: 3,
    milliseconds: 90_000,
  });

  console.log('Interval:', interval.toString());

  const dateResult = addIntervalToDateOnly(
    '2026-01-31',
    new SqlInterval({ months: 1, days: 3 })
  );

  console.log('Calendar-aware result:', dateResult);
}

function demonstrateDatePart() {
  console.log('\n=== DATE_PART ===');

  const timestamp = parseTimestamp(
    '2026-10-02T06:48:23.456+05:30'
  );

  for (const field of [
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
    'dow',
    'isodow',
    'doy',
    'epoch',
  ]) {
    console.log(`${field}:`, datePart(field, timestamp));
  }
}

function demonstrateDateTrunc() {
  console.log('\n=== DATE_TRUNC ===');

  const timestamp = parseTimestamp(
    '2026-10-17T14:25:12.456Z'
  );

  for (const field of [
    'year',
    'quarter',
    'month',
    'week',
    'day',
    'hour',
    'minute',
    'second',
  ]) {
    console.log(
      `${field}:`,
      formatUtc(dateTrunc(field, timestamp))
    );
  }
}

function demonstrateTimeZones() {
  console.log('\n=== TIME ZONES ===');

  const instant = parseTimestamp(
    '2026-10-02T03:30:00Z'
  );

  for (const zone of [
    'UTC',
    'Asia/Kolkata',
    'Europe/London',
    'America/New_York',
  ]) {
    console.log(
      zone,
      '->',
      getZonedParts(instant, zone)
    );
  }

  console.log(
    'Kolkata local date:',
    zonedDateKey(instant, 'Asia/Kolkata')
  );

  console.log(
    'New York local date:',
    zonedDateKey(instant, 'America/New_York')
  );
}

function demonstrateReporting() {
  console.log('\n=== HALF-OPEN REPORTING WINDOW ===');

  const window = monthlyUtcWindow(2026, 10);

  const events = [
    {
      id: 'ORD-1001',
      occurredAt: parseTimestamp('2026-10-01T00:00:00Z'),
    },
    {
      id: 'ORD-1002',
      occurredAt: parseTimestamp('2026-10-31T23:59:59.999Z'),
    },
    {
      id: 'ORD-1003',
      occurredAt: parseTimestamp('2026-11-01T00:00:00Z'),
    },
  ];

  const selected = filterEventsByRange(
    events,
    window.start,
    window.end
  );

  console.log(
    selected.map(event => event.id)
  );
}

function demonstrateEventDrivenProcessing() {
  console.log('\n=== EVENT-DRIVEN TEMPORAL PROCESSING ===');

  const bus = new EventBus();
  const store = new TemporalEventStore(bus);

  bus.on('event:stored', event => {
    console.log(
      'Stored:',
      event.id,
      formatUtc(event.occurredAt)
    );
  });

  store.append({
    id: 'PAY-01',
    occurredAt: parseTimestamp('2026-10-01T23:30:00Z'),
  });

  store.append({
    id: 'PAY-02',
    occurredAt: parseTimestamp('2026-10-02T00:30:00Z'),
  });

  const groups = store.groupByLocalDate('Asia/Kolkata');

  for (const [day, events] of groups) {
    console.log(
      day,
      '=>',
      events.map(event => event.id)
    );
  }
}

function demonstrateElapsedTime() {
  console.log('\n=== ELAPSED TIME ===');

  const start = '2026-10-02T09:00:00+05:30';
  const end = '2026-10-02T17:45:00+05:30';

  console.log(
    'Elapsed hours:',
    calculateElapsedHours(start, end)
  );
}

function demonstrateFailures() {
  console.log('\n=== FAILURE CONDITIONS ===');

  try {
    parseSqlDate('2026-02-29');
  } catch (error) {
    console.log('Invalid DATE rejected:', error.message);
  }

  try {
    parseTimestamp('2026-10-02T06:48:23');
  } catch (error) {
    console.log('Timezone-less TIMESTAMP rejected:', error.message);
  }

  try {
    filterEventsByRange([], new Date(10), new Date(5));
  } catch (error) {
    console.log('Invalid range rejected:', error.message);
  }

  try {
    getZonedParts(new Date(), 'Invalid/Zone');
  } catch (error) {
    console.log('Invalid timezone rejected:', error.message);
  }
}


// ---------------------------------------------------------------------------
// Assertions
// ---------------------------------------------------------------------------

function runAssertions() {
  assert.equal(
    addMonthsToDateOnly('2026-01-31', 1),
    '2026-02-28'
  );

  assert.equal(
    addMonthsToDateOnly('2024-01-31', 1),
    '2024-02-29'
  );

  assert.equal(
    datePart(
      'year',
      parseTimestamp('2026-10-02T06:48:23Z')
    ),
    2026
  );

  assert.equal(
    formatUtc(
      dateTrunc(
        'month',
        parseTimestamp('2026-10-17T14:25:12Z')
      )
    ),
    '2026-10-01T00:00:00.000Z'
  );

  const original = parseTimestamp('2026-10-02T03:30:00Z');

  assert.equal(
    zonedDateKey(original, 'Asia/Kolkata'),
    '2026-10-02'
  );

  assert.equal(
    zonedDateKey(original, 'America/New_York'),
    '2026-10-01'
  );

  assert.equal(
    calculateElapsedHours(
      '2026-10-02T09:00:00Z',
      '2026-10-02T17:30:00Z'
    ),
    8.5
  );

  console.log('\nAll JavaScript assertions passed.');
}


// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  console.log('SQL DATE & TIME: JAVASCRIPT IMPLEMENTATION');
  console.log('==========================================');

  demonstrateDate();
  demonstrateTimestamp();
  demonstrateInterval();
  demonstrateDatePart();
  demonstrateDateTrunc();
  demonstrateTimeZones();
  demonstrateReporting();
  demonstrateEventDrivenProcessing();
  demonstrateElapsedTime();
  demonstrateFailures();
  runAssertions();

  console.log('\nExecution completed successfully.');
}

main();
