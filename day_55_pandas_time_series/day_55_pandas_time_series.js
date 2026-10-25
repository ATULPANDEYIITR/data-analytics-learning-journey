"use strict";

/*
 * Pandas-style time-series concepts implemented with Node.js standard
 * library data structures:
 * - DatetimeIndex equivalent
 * - resampling
 * - time-based rolling windows
 * - shifting and differences
 * - calendar/time grouping
 *
 * JavaScript Date stores instants in milliseconds. Timestamps are kept
 * internally as epoch milliseconds so sorting and time arithmetic are
 * deterministic.
 */

const assert = require("node:assert/strict");

class TimeSeriesPoint {
    constructor(timestamp, values) {
        const date = new Date(timestamp);

        if (Number.isNaN(date.getTime())) {
            throw new TypeError(`Invalid timestamp: ${timestamp}`);
        }

        this.timestamp = date;
        this.values = Object.freeze({ ...values });
    }

    get time() {
        return this.timestamp.getTime();
    }
}

class TimeSeries {
    constructor(points) {
        if (!Array.isArray(points) || points.length === 0) {
            throw new Error("Time series must contain at least one point.");
        }

        const normalized = points.map(
            (point) =>
                point instanceof TimeSeriesPoint
                    ? point
                    : new TimeSeriesPoint(point.timestamp, point.values)
        );

        normalized.sort((a, b) => a.time - b.time);

        for (let i = 1; i < normalized.length; i++) {
            if (normalized[i].time === normalized[i - 1].time) {
                throw new Error("Duplicate timestamps are not allowed.");
            }
        }

        this.points = Object.freeze(normalized);
    }

    resampleDaily() {
        const buckets = new Map();

        for (const point of this.points) {
            const d = point.timestamp;
            const key = Date.UTC(
                d.getUTCFullYear(),
                d.getUTCMonth(),
                d.getUTCDate()
            );

            if (!buckets.has(key)) {
                buckets.set(key, []);
            }

            buckets.get(key).push(point);
        }

        return [...buckets.entries()]
            .sort(([a], [b]) => a - b)
            .map(([key, points]) => {
                const temperature = mean(
                    points.map((p) => p.values.temperature)
                );
                const pressure = mean(
                    points.map((p) => p.values.pressure)
                );
                const energy = sum(
                    points.map((p) => p.values.energyKwh)
                );

                return {
                    timestamp: new Date(key).toISOString(),
                    temperatureMean: temperature,
                    pressureMean: pressure,
                    energyTotal: energy,
                    observations: points.length,
                };
            });
    }

    rollingTimeWindow(windowHours = 168) {
        if (windowHours <= 0) {
            throw new RangeError("Rolling window must be positive.");
        }

        const windowMs = windowHours * 60 * 60 * 1000;
        const output = [];

        let left = 0;
        const temperatures = this.points.map(
            (point) => point.values.temperature
        );

        for (let right = 0; right < this.points.length; right++) {
            while (
                left < right &&
                this.points[right].time - this.points[left].time > windowMs
            ) {
                left++;
            }

            const window = temperatures.slice(left, right + 1);

            output.push({
                timestamp: this.points[right].timestamp.toISOString(),
                temperature: temperatures[right],
                rollingMean: mean(window),
                rollingStdDev: standardDeviation(window),
                observations: window.length,
            });
        }

        return output;
    }

    shiftAndDiff(field) {
        const output = [];

        for (let i = 0; i < this.points.length; i++) {
            const current = this.points[i].values[field];
            const previous =
                i === 0 ? null : this.points[i - 1].values[field];

            output.push({
                timestamp: this.points[i].timestamp.toISOString(),
                current,
                previous,
                difference:
                    previous === null ? null : current - previous,
                percentageChange:
                    previous === null || previous === 0
                        ? null
                        : ((current - previous) / previous) * 100,
            });
        }

        return output;
    }

    groupByWeek() {
        const groups = new Map();

        for (const point of this.points) {
            const date = new Date(point.time);
            const day = date.getUTCDay();
            const daysFromMonday = (day + 6) % 7;

            date.setUTCDate(date.getUTCDate() - daysFromMonday);
            date.setUTCHours(0, 0, 0, 0);

            const key = date.toISOString();

            if (!groups.has(key)) {
                groups.set(key, []);
            }

            groups.get(key).push(point);
        }

        return [...groups.entries()].map(([week, points]) => ({
            week,
            temperatureMean: mean(
                points.map((p) => p.values.temperature)
            ),
            temperatureMax: Math.max(
                ...points.map((p) => p.values.temperature)
            ),
            energyTotal: sum(
                points.map((p) => p.values.energyKwh)
            ),
            observations: points.length,
        }));
    }

    groupByHour() {
        const groups = new Map();

        for (const point of this.points) {
            const hour = point.timestamp.getUTCHours();

            if (!groups.has(hour)) {
                groups.set(hour, []);
            }

            groups.get(hour).push(point);
        }

        return [...groups.entries()]
            .sort(([a], [b]) => a - b)
            .map(([hour, points]) => ({
                hour,
                temperatureMean: mean(
                    points.map((p) => p.values.temperature)
                ),
                energyTotal: sum(
                    points.map((p) => p.values.energyKwh)
                ),
                observations: points.length,
            }));
    }
}

function sum(values) {
    if (values.length === 0) {
        return 0;
    }

    return values.reduce((total, value) => total + value, 0);
}

function mean(values) {
    if (values.length === 0) {
        return null;
    }

    return sum(values) / values.length;
}

function standardDeviation(values) {
    if (values.length < 2) {
        return null;
    }

    const average = mean(values);
    const variance =
        values.reduce(
            (total, value) => total + (value - average) ** 2,
            0
        ) / (values.length - 1);

    return Math.sqrt(variance);
}

function createDataset() {
    const records = [
        ["2026-01-01T08:00:00Z", 21.2, 1008, 3.1],
        ["2026-01-01T12:00:00Z", 22.1, 1007, 2.4],
        ["2026-01-02T09:30:00Z", 20.8, 1009, 3.7],
        ["2026-01-03T10:00:00Z", 23.4, 1006, 4.0],
        ["2026-01-05T14:00:00Z", 24.0, 1005, 5.1],
        ["2026-01-06T11:15:00Z", 23.2, 1007, 4.4],
        ["2026-01-08T16:30:00Z", 25.1, 1004, 5.8],
        ["2026-01-10T09:00:00Z", 26.0, 1003, 6.2],
        ["2026-01-12T13:45:00Z", 24.7, 1005, 5.0],
        ["2026-01-14T15:00:00Z", 27.2, 1002, 6.7],
    ];

    return new TimeSeries(
        records.map(([timestamp, temperature, pressure, energyKwh]) => ({
            timestamp,
            values: { temperature, pressure, energyKwh },
        }))
    );
}

function main() {
    const series = createDataset();

    console.log("\n=== Daily Resampling ===");
    console.table(series.resampleDaily());

    console.log("\n=== Seven-Day Time Rolling Window ===");
    console.table(series.rollingTimeWindow(168));

    console.log("\n=== Shift and Difference ===");
    console.table(series.shiftAndDiff("temperature"));

    console.log("\n=== Weekly Grouping ===");
    console.table(series.groupByWeek());

    console.log("\n=== Hour-of-Day Grouping ===");
    console.table(series.groupByHour());

    assert.equal(series.points.length, 10);
    assert.equal(series.resampleDaily().length, 10);
    assert.equal(series.rollingTimeWindow().length, 10);
    assert.equal(series.shiftAndDiff("temperature")[0].previous, null);

    console.log("\nValidation checks passed.");
}

main();
