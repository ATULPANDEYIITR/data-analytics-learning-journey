#!/usr/bin/env node
"use strict";

/*
 * Statistical Visualization Toolkit
 *
 * Node.js standard-library implementation of:
 * histograms, box plots, violin plots, scatter plots, density plots,
 * and categorical plots.
 *
 * The program computes statistics and emits an SVG dashboard.
 */

const fs = require("fs");

class VisualizationError extends Error {}

class NumericDataset {
  constructor(values) {
    if (!Array.isArray(values) || values.length === 0) {
      throw new VisualizationError("Dataset must contain observations.");
    }

    if (!values.every(
      value => typeof value === "number" && Number.isFinite(value)
    )) {
      throw new VisualizationError("Every observation must be finite.");
    }

    this.values = [...values];
  }

  get size() {
    return this.values.length;
  }

  mean() {
    return this.values.reduce((sum, value) => sum + value, 0) / this.size;
  }

  standardDeviation() {
    const avg = this.mean();
    return Math.sqrt(
      this.values.reduce((sum, value) => sum + (value - avg) ** 2, 0) /
      this.size
    );
  }

  percentile(percent) {
    if (percent < 0 || percent > 100) {
      throw new VisualizationError("Percentile must be between 0 and 100.");
    }

    const sorted = [...this.values].sort((a, b) => a - b);
    const position = (sorted.length - 1) * percent / 100;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    if (lower === upper) {
      return sorted[lower];
    }

    const fraction = position - lower;
    return sorted[lower] + (sorted[upper] - sorted[lower]) * fraction;
  }

  fiveNumberSummary() {
    const q1 = this.percentile(25);
    const median = this.percentile(50);
    const q3 = this.percentile(75);
    const iqr = q3 - q1;
    const lowerFence = q1 - 1.5 * iqr;
    const upperFence = q3 + 1.5 * iqr;

    return {
      minimum: Math.min(...this.values),
      q1,
      median,
      q3,
      maximum: Math.max(...this.values),
      lowerFence,
      upperFence,
      outliers: this.values.filter(
        value => value < lowerFence || value > upperFence
      )
    };
  }

  histogram(binCount = 8) {
    if (!Number.isInteger(binCount) || binCount < 1) {
      throw new VisualizationError("binCount must be a positive integer.");
    }

    const minimum = Math.min(...this.values);
    const maximum = Math.max(...this.values);

    if (minimum === maximum) {
      return {
        edges: Array.from({ length: binCount + 1 }, (_, i) =>
          minimum - 0.5 + i
        ),
        counts: [this.size, ...Array(binCount - 1).fill(0)]
      };
    }

    const width = (maximum - minimum) / binCount;
    const counts = Array(binCount).fill(0);

    for (const value of this.values) {
      let index = Math.floor((value - minimum) / width);
      index = Math.min(index, binCount - 1);
      counts[index]++;
    }

    return {
      edges: Array.from(
        { length: binCount + 1 },
        (_, i) => minimum + i * width
      ),
      counts
    };
  }

  kde(points = 80) {
    if (!Number.isInteger(points) || points < 2) {
      throw new VisualizationError("Density requires at least two points.");
    }

    const minimum = Math.min(...this.values);
    const maximum = Math.max(...this.values);
    let sigma = this.standardDeviation();

    if (sigma === 0) sigma = Math.max(Math.abs(minimum) * 0.05, 1);

    let bandwidth = 1.06 * sigma * this.size ** (-1 / 5);
    bandwidth = Math.max(bandwidth, 1e-9);

    const start = minimum - 3 * bandwidth;
    const end = maximum + 3 * bandwidth;
    const normalizer = this.size * bandwidth * Math.sqrt(2 * Math.PI);

    return Array.from({ length: points }, (_, i) => {
      const x = start + (end - start) * i / (points - 1);
      const density = this.values.reduce(
        (sum, value) =>
          sum + Math.exp(-0.5 * ((x - value) / bandwidth) ** 2),
        0
      ) / normalizer;

      return { x, density };
    });
  }
}

function validateXY(x, y) {
  if (!Array.isArray(x) || !Array.isArray(y) || x.length !== y.length) {
    throw new VisualizationError("Scatter coordinates must have equal lengths.");
  }
  new NumericDataset(x);
  new NumericDataset(y);
}

function categoricalCounts(categories) {
  if (!Array.isArray(categories) || categories.length === 0) {
    throw new VisualizationError("Categories cannot be empty.");
  }

  const counts = new Map();

  for (const raw of categories) {
    const category = String(raw).trim();
    if (!category) {
      throw new VisualizationError("Category labels cannot be empty.");
    }
    counts.set(category, (counts.get(category) ?? 0) + 1);
  }

  return [...counts.entries()]
    .map(([category, count]) => ({
      category,
      count,
      percentage: count * 100 / categories.length
    }))
    .sort((a, b) => b.count - a.count || a.category.localeCompare(b.category));
}

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function axes(parts, x, y, width, height) {
  parts.push(
    `<line x1="${x}" y1="${y + height}" x2="${x + width}" y2="${y + height}" stroke="black"/>`,
    `<line x1="${x}" y1="${y}" x2="${x}" y2="${y + height}" stroke="black"/>`
  );
}

function histogramSvg(data, x, y, width, height) {
  const histogram = data.histogram(8);
  const parts = [];
  axes(parts, x, y, width, height);

  const maximum = Math.max(...histogram.counts);
  const barWidth = width / histogram.counts.length;

  histogram.counts.forEach((count, index) => {
    const barHeight = maximum === 0 ? 0 : height * count / maximum;
    const bx = x + index * barWidth;
    const by = y + height - barHeight;

    parts.push(
      `<rect x="${bx.toFixed(2)}" y="${by.toFixed(2)}" ` +
      `width="${(barWidth - 2).toFixed(2)}" height="${barHeight.toFixed(2)}" ` +
      `fill="#4c78a8"/>`
    );
  });

  parts.push(`<text x="${x}" y="${y - 8}" font-family="sans-serif">Histogram</text>`);
  return parts;
}

function boxSvg(data, x, y, width, height) {
  const summary = data.fiveNumberSummary();
  const parts = [];
  axes(parts, x, y, width, height);

  let minimum = summary.minimum;
  let maximum = summary.maximum;

  if (minimum === maximum) {
    minimum -= 1;
    maximum += 1;
  }

  const scale = value =>
    x + (value - minimum) / (maximum - minimum) * width;

  const centerY = y + height / 2;
  const q1 = scale(summary.q1);
  const q3 = scale(summary.q3);

  parts.push(
    `<line x1="${scale(summary.minimum)}" y1="${centerY}" ` +
    `x2="${q1}" y2="${centerY}" stroke="black"/>`,
    `<line x1="${q3}" y1="${centerY}" ` +
    `x2="${scale(summary.maximum)}" y2="${centerY}" stroke="black"/>`,
    `<rect x="${q1}" y="${y + height * 0.25}" ` +
    `width="${q3 - q1}" height="${height * 0.5}" ` +
    `fill="#72b7b2" stroke="black"/>`,
    `<line x1="${scale(summary.median)}" y1="${y + height * 0.25}" ` +
    `x2="${scale(summary.median)}" y2="${y + height * 0.75}" ` +
    `stroke="black" stroke-width="2"/>`
  );

  for (const value of summary.outliers) {
    parts.push(
      `<circle cx="${scale(value)}" cy="${centerY}" r="4" fill="#e45756"/>`
    );
  }

  parts.push(`<text x="${x}" y="${y - 8}" font-family="sans-serif">Box Plot</text>`);
  return parts;
}

function violinSvg(data, x, y, width, height) {
  const density = data.kde(60);
  const maximum = Math.max(...density.map(point => point.density));
  const minimum = density[0].x;
  const maximumX = density[density.length - 1].x;
  const center = x + width / 2;

  const scaleY = value =>
    y + height - (value - minimum) / (maximumX - minimum) * height;

  const left = [];
  const right = [];

  for (const point of density) {
    const py = scaleY(point.x);
    const half = point.density / maximum * width * 0.45;
    left.push(`${center - half},${py}`);
    right.push(`${center + half},${py}`);
  }

  return [
    `<polygon points="${left.concat(right.reverse()).join(" ")}" ` +
    `fill="#f2cf5b" stroke="black"/>`,
    `<text x="${x}" y="${y - 8}" font-family="sans-serif">Violin Plot</text>`
  ];
}

function scatterSvg(xValues, yValues, x, y, width, height) {
  validateXY(xValues, yValues);

  const xmin = Math.min(...xValues);
  const xmax = Math.max(...xValues);
  const ymin = Math.min(...yValues);
  const ymax = Math.max(...yValues);

  const xRange = xmax === xmin ? 1 : xmax - xmin;
  const yRange = ymax === ymin ? 1 : ymax - ymin;

  const parts = [];
  axes(parts, x, y, width, height);

  for (let i = 0; i < xValues.length; i++) {
    const px = x + (xValues[i] - xmin) / xRange * width;
    const py = y + height - (yValues[i] - ymin) / yRange * height;

    parts.push(
      `<circle cx="${px.toFixed(2)}" cy="${py.toFixed(2)}" ` +
      `r="3.5" fill="#54a24b"/>`
    );
  }

  parts.push(`<text x="${x}" y="${y - 8}" font-family="sans-serif">Scatter Plot</text>`);
  return parts;
}

function densitySvg(data, x, y, width, height) {
  const density = data.kde();
  const maxDensity = Math.max(...density.map(point => point.density));
  const minimum = density[0].x;
  const maximum = density[density.length - 1].x;

  const points = density.map(point => {
    const px = x + (point.x - minimum) / (maximum - minimum) * width;
    const py = y + height - point.density / maxDensity * height;
    return `${px.toFixed(2)},${py.toFixed(2)}`;
  });

  const parts = [];
  axes(parts, x, y, width, height);
  parts.push(
    `<polyline points="${points.join(" ")}" fill="none" ` +
    `stroke="#b279a2" stroke-width="2"/>`,
    `<text x="${x}" y="${y - 8}" font-family="sans-serif">Density Plot</text>`
  );

  return parts;
}

function categoricalSvg(categories, x, y, width, height) {
  const summaries = categoricalCounts(categories);
  const maximum = Math.max(...summaries.map(item => item.count));
  const barWidth = width / summaries.length;
  const parts = [];

  axes(parts, x, y, width, height);

  summaries.forEach((item, index) => {
    const barHeight = height * item.count / maximum;
    const bx = x + index * barWidth + 4;
    const by = y + height - barHeight;

    parts.push(
      `<rect x="${bx}" y="${by}" width="${barWidth - 8}" ` +
      `height="${barHeight}" fill="#ff9da6"/>`,
      `<text x="${bx}" y="${y + height + 18}" font-family="sans-serif" ` +
      `font-size="11">${esc(item.category)}</text>`
    );
  });

  parts.push(`<text x="${x}" y="${y - 8}" font-family="sans-serif">Categorical Plot</text>`);
  return parts;
}

class VisualizationDashboard {
  constructor() {
    this.width = 1100;
    this.height = 900;
    this.parts = [
      `<svg xmlns="http://www.w3.org/2000/svg" width="${this.width}" ` +
      `height="${this.height}" viewBox="0 0 ${this.width} ${this.height}">`,
      `<rect width="100%" height="100%" fill="white"/>`,
      `<text x="30" y="32" font-family="sans-serif" font-size="20" ` +
      `font-weight="bold">Statistical Visualization Report</text>`
    ];
  }

  add(parts) {
    this.parts.push(...parts);
  }

  finish() {
    this.parts.push("</svg>");
    return this.parts.join("\n");
  }
}

async function main() {
  const measurements = new NumericDataset([
    42, 45, 47, 48, 49, 50, 51, 52, 52, 53,
    54, 55, 56, 57, 58, 59, 61, 62, 63, 65,
    68, 70, 74, 79, 91
  ]);

  const xValues = Array.from({ length: measurements.size }, (_, i) => i + 1);
  const categories = [
    "API", "API", "Web", "Web", "Web", "Mobile", "API",
    "Mobile", "Web", "API", "Desktop", "Web", "Mobile", "API"
  ];

  const dashboard = new VisualizationDashboard();

  dashboard.add(histogramSvg(measurements, 50, 70, 300, 220));
  dashboard.add(boxSvg(measurements, 400, 70, 300, 220));
  dashboard.add(violinSvg(measurements, 750, 70, 300, 220));
  dashboard.add(scatterSvg(xValues, measurements.values, 50, 390, 300, 220));
  dashboard.add(densitySvg(measurements, 400, 390, 300, 220));
  dashboard.add(categoricalSvg(categories, 750, 390, 300, 220));

  const summary = measurements.fiveNumberSummary();

  dashboard.add([
    `<text x="50" y="680" font-family="sans-serif" font-size="14">` +
    `Count: ${measurements.size} | Mean: ${measurements.mean().toFixed(2)} | ` +
    `SD: ${measurements.standardDeviation().toFixed(2)}</text>`,
    `<text x="50" y="710" font-family="sans-serif" font-size="14">` +
    `Q1: ${summary.q1.toFixed(2)} | Median: ${summary.median.toFixed(2)} | ` +
    `Q3: ${summary.q3.toFixed(2)} | Outliers: ${summary.outliers.length}</text>`
  ]);

  const output = "statistical_visualization_report_js.svg";
  fs.writeFileSync(output, dashboard.finish(), "utf8");

  if (!fs.existsSync(output)) {
    throw new Error("SVG output was not created.");
  }

  console.log(`Wrote ${output}`);
  console.log(JSON.stringify({
    n: measurements.size,
    mean: measurements.mean(),
    standardDeviation: measurements.standardDeviation(),
    outliers: summary.outliers
  }, null, 2));
}

main().catch(error => {
  console.error(`Visualization failed: ${error.message}`);
  process.exitCode = 1;
});
