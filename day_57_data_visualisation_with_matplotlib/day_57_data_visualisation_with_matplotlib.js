"use strict";

/*
 * Data Visualization companion model.
 *
 * The program prepares visualization-ready data, evaluates chart policies,
 * emits an SVG dashboard, and demonstrates event-driven updates without
 * requiring an external npm package.
 *
 * The SVG representation deliberately complements Matplotlib rather than
 * duplicating its API. It focuses on data preparation, interaction state,
 * validation, and browser-oriented rendering.
 */

const fs = require("node:fs");
const path = require("node:path");
const EventEmitter = require("node:events");

const MONTHS = Object.freeze(["Jan", "Feb", "Mar", "Apr", "May", "Jun"]);

const teams = Object.freeze([
  {
    name: "Platform",
    deployments: Object.freeze([42, 48, 53, 61, 67, 74]),
    incidents: Object.freeze([8, 7, 6, 5, 4, 4]),
    leadTimeHours: Object.freeze([18, 16, 14, 12, 10.5, 9.2]),
    coverage: Object.freeze([76, 79, 82, 85, 88, 91]),
  },
  {
    name: "Payments",
    deployments: Object.freeze([31, 35, 39, 44, 49, 55]),
    incidents: Object.freeze([10, 9, 8, 7, 6, 5]),
    leadTimeHours: Object.freeze([24, 22, 19, 17, 15, 13.5]),
    coverage: Object.freeze([71, 74, 77, 80, 83, 86]),
  },
  {
    name: "Analytics",
    deployments: Object.freeze([25, 28, 34, 38, 43, 47]),
    incidents: Object.freeze([5, 5, 4, 3, 3, 2]),
    leadTimeHours: Object.freeze([20, 18, 15.5, 13, 11.5, 10]),
    coverage: Object.freeze([81, 83, 86, 89, 92, 94]),
  },
]);

function validateSeries(series) {
  if (!series || typeof series.name !== "string" || !series.name.trim()) {
    throw new TypeError("Every series needs a non-empty name.");
  }

  for (const field of ["deployments", "incidents", "leadTimeHours", "coverage"]) {
    if (!Array.isArray(series[field]) || series[field].length !== MONTHS.length) {
      throw new RangeError(`${series.name}: ${field} must contain six values.`);
    }
  }

  if (series.deployments.some((v) => !Number.isInteger(v) || v < 0)) {
    throw new RangeError(`${series.name}: invalid deployment count.`);
  }

  if (series.incidents.some((v) => !Number.isInteger(v) || v < 0)) {
    throw new RangeError(`${series.name}: invalid incident count.`);
  }

  if (series.leadTimeHours.some((v) => !Number.isFinite(v) || v <= 0)) {
    throw new RangeError(`${series.name}: lead time must be positive.`);
  }

  if (series.coverage.some((v) => !Number.isFinite(v) || v < 0 || v > 100)) {
    throw new RangeError(`${series.name}: coverage must be between 0 and 100.`);
  }
}

function percentageChange(first, last) {
  if (first === 0) {
    return null;
  }
  return ((last - first) / first) * 100;
}

function linearScale(domainMin, domainMax, rangeMin, rangeMax) {
  if (!Number.isFinite(domainMin) || !Number.isFinite(domainMax)) {
    throw new TypeError("Scale domain must be finite.");
  }

  if (domainMin === domainMax) {
    return () => (rangeMin + rangeMax) / 2;
  }

  return (value) =>
    rangeMin +
    ((value - domainMin) / (domainMax - domainMin)) *
      (rangeMax - rangeMin);
}

function svgEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

class VisualizationState extends EventEmitter {
  #selectedTeam = teams[0].name;
  #metric = "deployments";

  selectTeam(name) {
    if (!teams.some((team) => team.name === name)) {
      throw new Error(`Unknown team: ${name}`);
    }

    this.#selectedTeam = name;
    this.emit("selectionChanged", this.snapshot());
  }

  selectMetric(metric) {
    const allowed = new Set([
      "deployments",
      "incidents",
      "leadTimeHours",
      "coverage",
    ]);

    if (!allowed.has(metric)) {
      throw new Error(`Unsupported metric: ${metric}`);
    }

    this.#metric = metric;
    this.emit("selectionChanged", this.snapshot());
  }

  snapshot() {
    return Object.freeze({
      team: this.#selectedTeam,
      metric: this.#metric,
    });
  }
}

function buildPolyline(series, width, height, margin) {
  const values = series;
  const min = Math.min(...values);
  const max = Math.max(...values);

  const x = linearScale(
    0,
    values.length - 1,
    margin.left,
    width - margin.right,
  );

  const y = linearScale(
    min === max ? min - 1 : min,
    min === max ? max + 1 : max,
    height - margin.bottom,
    margin.top,
  );

  return values
    .map((value, index) => `${x(index).toFixed(1)},${y(value).toFixed(1)}`)
    .join(" ");
}

function renderSvg(dataset, state) {
  const width = 960;
  const height = 560;
  const margin = Object.freeze({
    top: 70,
    right: 40,
    bottom: 90,
    left: 80,
  });

  const selected = dataset.find((team) => team.name === state.team);
  if (!selected) {
    throw new Error("Selected series is unavailable.");
  }

  const values = selected[state.metric];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const x = linearScale(0, values.length - 1, margin.left, width - margin.right);
  const y = linearScale(
    min === max ? min - 1 : min,
    min === max ? max + 1 : max,
    height - margin.bottom,
    margin.top,
  );

  const points = buildPolyline(values, width, height, margin);

  const labels = MONTHS.map(
    (month, index) =>
      `<text x="${x(index).toFixed(1)}" y="${height - 45}" text-anchor="middle" font-size="13">${svgEscape(month)}</text>`,
  ).join("");

  const markers = values
    .map(
      (value, index) =>
        `<circle cx="${x(index).toFixed(1)}" cy="${y(value).toFixed(1)}" r="5"><title>${svgEscape(
          `${MONTHS[index]}: ${value}`,
        )}</title></circle>`,
    )
    .join("");

  const grid = [0, 0.25, 0.5, 0.75, 1]
    .map((fraction) => {
      const value = min + (max - min) * fraction;
      const py = y(value);
      return `
        <line x1="${margin.left}" y1="${py}" x2="${width - margin.right}" y2="${py}"
              stroke="#dddddd" />
        <text x="${margin.left - 12}" y="${py + 4}" text-anchor="end"
              font-size="12">${value.toFixed(1)}</text>`;
    })
    .join("");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="${width / 2}" y="32" text-anchor="middle"
        font-size="22" font-weight="bold">Interactive Delivery Metric</text>
  <text x="${width / 2}" y="54" text-anchor="middle"
        font-size="14">${svgEscape(selected.name)} — ${svgEscape(state.metric)}</text>
  ${grid}
  <line x1="${margin.left}" y1="${height - margin.bottom}"
        x2="${width - margin.right}" y2="${height - margin.bottom}" stroke="black"/>
  <line x1="${margin.left}" y1="${margin.top}"
        x2="${margin.left}" y2="${height - margin.bottom}" stroke="black"/>
  <polyline points="${points}" fill="none" stroke="#2463a6"
            stroke-width="3"/>
  ${markers}
  ${labels}
</svg>`;
}

function evaluateVisualizationPolicy(dataset) {
  const warnings = [];

  for (const team of dataset) {
    if (team.coverage.some((value) => value < 70)) {
      warnings.push(`${team.name}: coverage includes a value below 70%.`);
    }

    if (team.leadTimeHours.some((value) => value <= 0)) {
      warnings.push(`${team.name}: logarithmic lead-time scale is invalid.`);
    }
  }

  return Object.freeze({
    valid: warnings.length === 0,
    warnings: Object.freeze(warnings),
  });
}

function printMetrics(dataset) {
  console.log("Visualization-ready analysis");
  console.log("-".repeat(72));

  for (const team of dataset) {
    const deploymentChange = percentageChange(
      team.deployments[0],
      team.deployments.at(-1),
    );

    const leadTimeChange = percentageChange(
      team.leadTimeHours[0],
      team.leadTimeHours.at(-1),
    );

    console.log(
      `${team.name.padEnd(12)} ` +
        `deployments=${deploymentChange.toFixed(2).padStart(8)}% ` +
        `leadTime=${leadTimeChange.toFixed(2).padStart(8)}% ` +
        `coverage=${team.coverage.at(-1).toFixed(1)}%`,
    );
  }
}

function main() {
  for (const team of teams) {
    validateSeries(team);
  }

  const policy = evaluateVisualizationPolicy(teams);
  if (!policy.valid) {
    throw new Error(policy.warnings.join("\n"));
  }

  const state = new VisualizationState();

  state.on("selectionChanged", (snapshot) => {
    console.log(
      `State changed: team=${snapshot.team}, metric=${snapshot.metric}`,
    );
  });

  printMetrics(teams);

  state.selectTeam("Analytics");
  state.selectMetric("coverage");

  const svg = renderSvg(teams, state.snapshot());

  const outputDirectory = path.resolve(process.cwd(), "output");
  fs.mkdirSync(outputDirectory, { recursive: true });

  const outputFile = path.join(outputDirectory, "delivery_metric.svg");
  fs.writeFileSync(outputFile, svg, {
    encoding: "utf8",
    flag: "w",
  });

  console.log(`SVG written to: ${outputFile}`);
}

main();
