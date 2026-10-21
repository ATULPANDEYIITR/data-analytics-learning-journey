"use strict";

/*
 * Pandas Data Cleaning counterpart:
 * this Node.js program models the same data-quality concerns without
 * translating pandas syntax. It uses Maps, Sets, regular expressions,
 * Date validation, categorical policies, and an event-driven pipeline.
 */

const rawCustomers = [
  { customerId: 101, name: " Alice  Sharma ", age: "29", email: " ALICE.SHARMA@EXAMPLE.COM ", city: "Lucknow", segment: "Premium", signupDate: "2026-01-15", orders: "12" },
  { customerId: 102, name: "Bob Khan", age: "", email: "bob.khan@example.com", city: "Delhi", segment: "Standard", signupDate: "2026/02/20", orders: "5" },
  { customerId: 103, name: "Charlie  Rao", age: "34", email: "", city: "Mumbai", segment: "Premium", signupDate: "2026-03-10", orders: "8" },
  { customerId: 104, name: "Alice  Sharma", age: "29", email: "alice.sharma@example.com", city: "Lucknow", segment: "Premium", signupDate: "2026-01-15", orders: "12" },
  { customerId: 105, name: "David Mehta", age: "unknown", email: "david.mehta@example.com", city: "Delhi", segment: "standard", signupDate: "2026-04-05", orders: "3" },
  { customerId: 106, name: "Esha Patel", age: "41", email: "esha.patel@example.com", city: " ", segment: "Enterprise", signupDate: "2026-05-11", orders: "21" },
  { customerId: 107, name: "Farhan Ali", age: "37", email: "farhan.ali@example.com", city: "Bengaluru", segment: "Standard", signupDate: "invalid", orders: "7" },
  { customerId: 108, name: "", age: "26", email: "neha@example.com", city: "Pune", segment: "Standard", signupDate: "2026-06-30", orders: "2" },
  { customerId: 109, name: "George Sen", age: "-5", email: "george.sen@example.com", city: "Chennai", segment: "Premium", signupDate: "2026-07-01", orders: "15" },
  { customerId: 110, name: "Hina Roy", age: "30", email: "hina.roy@example.com", city: "Kolkata", segment: "premium", signupDate: "2026-07-18", orders: "10" }
];

const allowedSegments = new Set(["Standard", "Premium", "Enterprise"]);

class DataCleaner {
  constructor(records) {
    this.records = structuredClone(records);
    this.metrics = {
      inputRows: records.length,
      invalidValues: 0,
      duplicateRows: 0,
      outputRows: 0
    };
  }

  cleanText(value) {
    if (value === null || value === undefined) {
      return null;
    }

    const cleaned = String(value)
      .trim()
      .replace(/\s+/g, " ");

    return cleaned === "" || cleaned.toLowerCase() === "unknown"
      ? null
      : cleaned;
  }

  normalizeName(value) {
    const cleaned = this.cleanText(value);
    if (cleaned === null) return null;

    return cleaned
      .toLowerCase()
      .replace(/\b[a-z]/g, character => character.toUpperCase());
  }

  normalizeEmail(value) {
    const cleaned = this.cleanText(value);
    if (cleaned === null) return null;

    const email = cleaned.toLowerCase();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {
      this.metrics.invalidValues++;
      return null;
    }

    return email;
  }

  parseInteger(value, minimum = null, maximum = null) {
    if (value === null || value === undefined || String(value).trim() === "") {
      return null;
    }

    const number = Number(value);

    if (!Number.isInteger(number)) {
      this.metrics.invalidValues++;
      return null;
    }

    if (minimum !== null && number < minimum) {
      this.metrics.invalidValues++;
      return null;
    }

    if (maximum !== null && number > maximum) {
      this.metrics.invalidValues++;
      return null;
    }

    return number;
  }

  parseDate(value) {
    if (!value) return null;

    const normalized = String(value).replaceAll("/", "-");
    const date = new Date(`${normalized}T00:00:00Z`);

    if (Number.isNaN(date.getTime())) {
      this.metrics.invalidValues++;
      return null;
    }

    return date.toISOString().slice(0, 10);
  }

  normalizeRecord(record) {
    const segmentText = this.cleanText(record.segment);
    const normalizedSegment = segmentText
      ? segmentText[0].toUpperCase() + segmentText.slice(1).toLowerCase()
      : "Standard";

    if (!allowedSegments.has(normalizedSegment)) {
      this.metrics.invalidValues++;
      throw new Error(
        `Unsupported segment '${record.segment}' for customer ${record.customerId}`
      );
    }

    return {
      customerId: this.parseInteger(record.customerId, 1),
      name: this.normalizeName(record.name) ?? "Unknown Customer",
      age: this.parseInteger(record.age, 18, 100),
      email: this.normalizeEmail(record.email),
      city: this.cleanText(record.city)?.replace(
        /\b[a-z]/g,
        character => character.toUpperCase()
      ) ?? "Unknown",
      segment: normalizedSegment,
      signupDate: this.parseDate(record.signupDate),
      orders: this.parseInteger(record.orders, 0)
    };
  }

  removeDuplicates(records) {
    const seenIds = new Set();
    const seenEmails = new Set();
    const output = [];

    for (const record of records) {
      if (seenIds.has(record.customerId)) {
        this.metrics.duplicateRows++;
        continue;
      }

      if (record.email && seenEmails.has(record.email)) {
        this.metrics.duplicateRows++;
        continue;
      }

      seenIds.add(record.customerId);
      if (record.email) seenEmails.add(record.email);
      output.push(record);
    }

    return output;
  }

  impute(records) {
    const ages = records
      .map(record => record.age)
      .filter(Number.isInteger)
      .sort((a, b) => a - b);

    const orders = records
      .map(record => record.orders)
      .filter(Number.isInteger)
      .sort((a, b) => a - b);

    const median = values => {
      if (values.length === 0) return null;
      const middle = Math.floor(values.length / 2);
      return values.length % 2
        ? values[middle]
        : Math.round((values[middle - 1] + values[middle]) / 2);
    };

    const medianAge = median(ages);
    const medianOrders = median(orders);

    return records.map(record => ({
      ...record,
      age: record.age ?? medianAge,
      orders: record.orders ?? medianOrders
    }));
  }

  async run() {
    /*
     * A Promise and queue-like stage make the pipeline event-driven:
     * each transformation completes before the next stage consumes it.
     */
    await new Promise(resolve => setImmediate(resolve));

    let cleaned = this.records.map(record => this.normalizeRecord(record));
    cleaned = this.removeDuplicates(cleaned);
    cleaned = this.impute(cleaned);

    this.metrics.outputRows = cleaned.length;

    return cleaned;
  }
}

async function main() {
  const cleaner = new DataCleaner(rawCustomers);

  try {
    const cleaned = await cleaner.run();

    console.table(cleaned);

    const segmentCounts = cleaned.reduce((counts, record) => {
      counts[record.segment] = (counts[record.segment] ?? 0) + 1;
      return counts;
    }, {});

    console.log("\nSegment counts:");
    console.table(segmentCounts);

    console.log("\nQuality metrics:");
    console.table(cleaner.metrics);

    console.log("\nMissing emails retained:",
      cleaned.filter(record => record.email === null).length
    );
  } catch (error) {
    console.error(`Cleaning failed: ${error.message}`);
    process.exitCode = 1;
  }
}

main();
