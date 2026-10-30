"use strict";

/*
 * Event-driven Exploratory Data Analysis of the UCI Iris Dataset.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 * Dataset: UCI Iris, 150 observations, four measurements.
 *
 * Outputs:
 *   iris_eda_output/analytical_report.md
 *   iris_eda_output/iris_cleaned.csv
 *   iris_eda_output/rejected_rows.txt (when required)
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

const DATASET_URL =
    "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data";

const FEATURES = [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width"
];

const SPECIES = new Set([
    "setosa",
    "versicolor",
    "virginica"
]);

const SAMPLE_DATA = `sepal_length,sepal_width,petal_length,petal_width,species
5.1,3.5,1.4,0.2,setosa
4.9,3.0,1.4,0.2,setosa
4.7,3.2,1.3,0.2,setosa
4.6,3.1,1.5,0.2,setosa
5.0,3.6,1.4,0.2,setosa
7.0,3.2,4.7,1.4,versicolor
6.4,3.2,4.5,1.5,versicolor
6.9,3.1,4.9,1.5,versicolor
5.5,2.3,4.0,1.3,versicolor
6.5,2.8,4.6,1.5,versicolor
6.3,3.3,6.0,2.5,virginica
5.8,2.7,5.1,1.9,virginica
7.1,3.0,5.9,2.1,virginica
6.3,2.9,5.6,1.8,virginica
6.5,3.0,5.8,2.2,virginica
`;

class EDAError extends Error {
    constructor(message) {
        super(message);
        this.name = "EDAError";
    }
}

class AnalysisEvents extends EventEmitter {
    constructor() {
        super();
        this.accepted = 0;
        this.rejected = 0;

        this.on("rowAccepted", () => this.accepted++);
        this.on("rowRejected", () => this.rejected++);
    }
}

class DatasetRepository {
    constructor(events) {
        this.events = events;
    }

    async load(inputPath, offline = false) {
        let content;
        let source;

        try {
            content = await fs.readFile(inputPath, "utf8");
            source = `Local CSV: ${inputPath}`;
        } catch (error) {
            if (error.code !== "ENOENT") {
                throw error;
            }

            if (!offline) {
                try {
                    const response = await fetch(DATASET_URL, {
                        signal: AbortSignal.timeout(15000),
                        headers: {
                            "User-Agent": "Node-Iris-EDA/1.0"
                        }
                    });

                    if (!response.ok) {
                        throw new Error(
                            `Dataset server returned HTTP ${response.status}`
                        );
                    }

                    content = await response.text();

                    await fs.mkdir(
                        path.dirname(inputPath),
                        { recursive: true }
                    );

                    await fs.writeFile(
                        inputPath,
                        content,
                        "utf8"
                    );

                    source = `UCI dataset downloaded to ${inputPath}`;

                } catch (downloadError) {
                    console.warn(
                        `Remote dataset unavailable: ${downloadError.message}`
                    );

                    content = SAMPLE_DATA;
                    source = "Embedded genuine Iris observation subset";
                }
            } else {
                content = SAMPLE_DATA;
                source = "Embedded genuine Iris observation subset";
            }
        }

        return this.parse(content, source);
    }

    parseCsvLine(line) {
        const values = [];
        let current = "";
        let quoted = false;

        for (let index = 0; index < line.length; index++) {
            const character = line[index];

            if (character === '"') {
                if (quoted && line[index + 1] === '"') {
                    current += '"';
                    index++;
                } else {
                    quoted = !quoted;
                }
            } else if (character === "," && !quoted) {
                values.push(current.trim());
                current = "";
            } else {
                current += character;
            }
        }

        if (quoted) {
            throw new EDAError("Unclosed quoted CSV field.");
        }

        values.push(current.trim());
        return values;
    }

    normalizeSpecies(value) {
        let species = value.trim().toLowerCase();

        species = species.replace(/^iris-/, "");

        if (species === "versicolour") {
            species = "versicolor";
        }

        if (!SPECIES.has(species)) {
            throw new EDAError(
                `Unknown species category: ${value}`
            );
        }

        return species;
    }

    parseRow(values) {
        if (values.length !== 5) {
            throw new EDAError(
                `Expected five fields, received ${values.length}.`
            );
        }

        const measurements = values.slice(0, 4).map(value => {
            if (value === "") {
                throw new EDAError("Missing numerical measurement.");
            }

            const number = Number(value);

            if (!Number.isFinite(number)) {
                throw new EDAError("Measurement must be finite.");
            }

            if (number <= 0 || number >= 10) {
                throw new EDAError(
                    "Measurement must be between zero and ten."
                );
            }

            return number;
        });

        return Object.freeze({
            sepalLength: measurements[0],
            sepalWidth: measurements[1],
            petalLength: measurements[2],
            petalWidth: measurements[3],
            species: this.normalizeSpecies(values[4])
        });
    }

    parse(content, source) {
        const observations = [];
        const rejectedRows = [];
        const seen = new Set();

        const lines = content.split(/\r?\n/);

        for (let index = 0; index < lines.length; index++) {
            const line = lines[index].trim();

            if (!line) {
                continue;
            }

            const values = this.parseCsvLine(line);

            if (
                [
                    "sepal_length",
                    "sepallengthcm",
                    "sepal length"
                ].includes(values[0].toLowerCase())
            ) {
                continue;
            }

            try {
                const flower = this.parseRow(values);
                observations.push(flower);
                this.events.emit("rowAccepted", flower);

                const key = JSON.stringify(flower);

                if (seen.has(key)) {
                    rejectedRows.push(
                        `Line ${index + 1}: duplicate observation detected.`
                    );
                } else {
                    seen.add(key);
                }

            } catch (error) {
                rejectedRows.push(
                    `Line ${index + 1}: ${error.message}`
                );

                this.events.emit("rowRejected", {
                    line: index + 1,
                    error: error.message
                });
            }
        }

        if (observations.length === 0) {
            throw new EDAError(
                "No valid observations were found."
            );
        }

        return {
            observations,
            rejectedRows,
            source
        };
    }
}

function percentile(input, probability) {
    const values = [...input].sort((a, b) => a - b);

    if (values.length === 0) {
        throw new EDAError(
            "Cannot calculate statistics on empty data."
        );
    }

    const position = (values.length - 1) * probability;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    if (lower === upper) {
        return values[lower];
    }

    return (
        values[lower] * (upper - position) +
        values[upper] * (position - lower)
    );
}

function mean(values) {
    if (values.length === 0) {
        throw new EDAError("Mean requires observations.");
    }

    return values.reduce((sum, value) => sum + value, 0)
        / values.length;
}

function sampleStandardDeviation(values) {
    if (values.length < 2) {
        return 0;
    }

    const average = mean(values);

    const squaredDifference = values.reduce(
        (sum, value) => sum + (value - average) ** 2,
        0
    );

    return Math.sqrt(
        squaredDifference / (values.length - 1)
    );
}

function calculateStatistics(values) {
    const sorted = [...values].sort((a, b) => a - b);

    const q1 = percentile(sorted, 0.25);
    const median = percentile(sorted, 0.5);
    const q3 = percentile(sorted, 0.75);
    const iqr = q3 - q1;

    const lower = q1 - 1.5 * iqr;
    const upper = q3 + 1.5 * iqr;

    const outlierCount = values.filter(
        value => value < lower || value > upper
    ).length;

    return Object.freeze({
        minimum: sorted[0],
        q1,
        median,
        mean: mean(values),
        q3,
        maximum: sorted[sorted.length - 1],
        standardDeviation: sampleStandardDeviation(values),
        outlierCount
    });
}

function extractFeature(observations, feature) {
    const propertyMap = {
        sepal_length: "sepalLength",
        sepal_width: "sepalWidth",
        petal_length: "petalLength",
        petal_width: "petalWidth"
    };

    return observations.map(
        flower => flower[propertyMap[feature]]
    );
}

function pearsonCorrelation(first, second) {
    if (
        first.length !== second.length ||
        first.length < 2
    ) {
        return null;
    }

    const firstMean = mean(first);
    const secondMean = mean(second);

    let numerator = 0;
    let sumFirst = 0;
    let sumSecond = 0;

    for (let index = 0; index < first.length; index++) {
        const differenceFirst = first[index] - firstMean;
        const differenceSecond = second[index] - secondMean;

        numerator += differenceFirst * differenceSecond;
        sumFirst += differenceFirst ** 2;
        sumSecond += differenceSecond ** 2;
    }

    const denominator = Math.sqrt(sumFirst * sumSecond);

    return denominator === 0
        ? null
        : numerator / denominator;
}

class EDAEngine {
    constructor(observations) {
        if (!Array.isArray(observations) || observations.length === 0) {
            throw new EDAError("A non-empty observation array is required.");
        }

        this.observations = Object.freeze([...observations]);
    }

    speciesDistribution() {
        const distribution = new Map(
            [...SPECIES].map(species => [species, 0])
        );

        for (const flower of this.observations) {
            distribution.set(
                flower.species,
                distribution.get(flower.species) + 1
            );
        }

        return distribution;
    }

    statistics() {
        const result = new Map();

        for (const feature of FEATURES) {
            result.set(
                feature,
                calculateStatistics(
                    extractFeature(this.observations, feature)
                )
            );
        }

        return result;
    }

    speciesMeans() {
        const result = new Map();

        for (const species of [...SPECIES].sort()) {
            const group = this.observations.filter(
                flower => flower.species === species
            );

            if (group.length === 0) {
                continue;
            }

            const featureMeans = FEATURES.map(feature => {
                const values = extractFeature(group, feature);
                return mean(values);
            });

            result.set(species, featureMeans);
        }

        return result;
    }

    correlations() {
        return FEATURES.map(first => {
            return FEATURES.map(second => {
                return pearsonCorrelation(
                    extractFeature(this.observations, first),
                    extractFeature(this.observations, second)
                );
            });
        });
    }

    duplicateCount() {
        const seen = new Set();

        for (const flower of this.observations) {
            seen.add(JSON.stringify(flower));
        }

        return this.observations.length - seen.size;
    }

    generateReport(source, rejectedCount) {
        const stats = this.statistics();
        const distribution = this.speciesDistribution();
        const speciesMeans = this.speciesMeans();
        const correlations = this.correlations();

        const lines = [
            "# Exploratory Data Analysis: Iris Dataset",
            "",
            `Generated: ${new Date().toISOString()}`,
            "",
            "## 1. Dataset Overview",
            "",
            `- Source: ${source}`,
            `- Valid observations: ${this.observations.length}`,
            "- Numerical variables: 4",
            "- Categorical variable: species",
            "- Measurement unit: centimetres",
            "",
            "## 2. Data Quality",
            "",
            "| Metric | Result |",
            "|---|---:|",
            `| Valid observations | ${this.observations.length} |`,
            `| Rejected rows | ${rejectedCount} |`,
            "| Missing values in accepted records | 0 |",
            `| Duplicate observations | ${this.duplicateCount()} |`,
            "",
            "## 3. Species Distribution",
            "",
            "| Species | Count | Percentage |",
            "|---|---:|---:|"
        ];

        for (const [species, count] of distribution) {
            lines.push(
                `| ${species} | ${count} | ` +
                `${(count / this.observations.length * 100).toFixed(2)}% |`
            );
        }

        lines.push(
            "",
            "## 4. Descriptive Statistics",
            "",
            "| Feature | Min | Q1 | Median | Mean | Q3 | Max | SD | Outliers |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
        );

        for (const [feature, result] of stats) {
            lines.push(
                `| ${feature} | ` +
                [
                    result.minimum,
                    result.q1,
                    result.median,
                    result.mean,
                    result.q3,
                    result.maximum,
                    result.standardDeviation
                ].map(value => value.toFixed(3)).join(" | ") +
                ` | ${result.outlierCount} |`
            );
        }

        lines.push(
            "",
            "## 5. Species-Level Comparison",
            "",
            "| Species | Sepal length | Sepal width | Petal length | Petal width |",
            "|---|---:|---:|---:|---:|"
        );

        for (const [species, values] of speciesMeans) {
            lines.push(
                `| ${species} | ` +
                values.map(value => value.toFixed(3)).join(" | ") +
                " |"
            );
        }

        lines.push(
            "",
            "## 6. Pearson Correlation Matrix",
            "",
            "| Feature | " + FEATURES.join(" | ") + " |",
            "|" + "---|".repeat(FEATURES.length + 1)
        );

        for (let index = 0; index < FEATURES.length; index++) {
            const cells = correlations[index].map(
                value => value === null
                    ? "N/A"
                    : value.toFixed(4)
            );

            lines.push(
                `| ${FEATURES[index]} | ${cells.join(" | ")} |`
            );
        }

        const petalLengthIndex = FEATURES.indexOf("petal_length");
        const petalWidthIndex = FEATURES.indexOf("petal_width");

        lines.push(
            "",
            "## 7. Analytical Findings",
            "",
            `- Petal length and petal width correlation: ` +
            `${correlations[petalLengthIndex][petalWidthIndex]?.toFixed(4) ?? "N/A"}.`
        );

        const speciesEntries = [...speciesMeans.entries()];

        const largest = [...speciesEntries].sort(
            (a, b) => b[1][2] - a[1][2]
        )[0];

        const smallest = [...speciesEntries].sort(
            (a, b) => a[1][2] - b[1][2]
        )[0];

        lines.push(
            `- Highest average petal length: ${largest[0]} (${largest[1][2].toFixed(3)} cm).`,
            `- Lowest average petal length: ${smallest[0]} (${smallest[1][2].toFixed(3)} cm).`,
            "- Outliers are identified using the 1.5 × IQR rule.",
            "- Flagged outliers are retained in the analysis.",
            "- Correlation indicates association, not causation.",
            "",
            "## 8. Methodological Limitations",
            "",
            "- Iris contains only 150 observations in its complete version.",
            "- It is a small, balanced dataset with three known species.",
            "- Pearson correlation describes linear association only.",
            "- Automated outlier detection does not establish data error.",
            "- A fallback sample must not be interpreted as a full-dataset result.",
            "",
            "## 9. Provenance",
            "",
            "Fisher, R. A. (1936). The Use of Multiple Measurements in Taxonomic Problems.",
            "",
            "UCI Machine Learning Repository: Iris.",
            "",
            "https://doi.org/10.24432/C56C76",
            "",
            "License: CC BY 4.0."
        );

        return lines.join("\n");
    }
}

function createCleanCsv(observations) {
    const escape = value => {
        const text = String(value);

        return /[",\n]/.test(text)
            ? `"${text.replace(/"/g, '""')}"`
            : text;
    };

    const rows = [
        FEATURES.join(",") + ",species"
    ];

    for (const flower of observations) {
        rows.push([
            flower.sepalLength,
            flower.sepalWidth,
            flower.petalLength,
            flower.petalWidth,
            flower.species
        ].map(escape).join(","));
    }

    return rows.join("\n") + "\n";
}

async function main() {
    const argumentsList = process.argv.slice(2);

    const offline = argumentsList.includes("--offline");

    const positional = argumentsList.filter(
        argument => !argument.startsWith("--")
    );

    const inputPath = positional[0] || "iris.csv";
    const outputDirectory = positional[1] || "iris_eda_output";

    const events = new AnalysisEvents();

    events.on("rowRejected", event => {
        console.warn(
            `Rejected line ${event.line}: ${event.error}`
        );
    });

    const repository = new DatasetRepository(events);

    const dataset = await repository.load(
        inputPath,
        offline
    );

    const engine = new EDAEngine(dataset.observations);

    const report = engine.generateReport(
        dataset.source,
        dataset.rejectedRows.length
    );

    await fs.mkdir(outputDirectory, {
        recursive: true
    });

    await Promise.all([
        fs.writeFile(
            path.join(outputDirectory, "analytical_report.md"),
            report,
            "utf8"
        ),
        fs.writeFile(
            path.join(outputDirectory, "iris_cleaned.csv"),
            createCleanCsv(dataset.observations),
            "utf8"
        )
    ]);

    if (dataset.rejectedRows.length > 0) {
        await fs.writeFile(
            path.join(outputDirectory, "rejected_rows.txt"),
            dataset.rejectedRows.join("\n"),
            "utf8"
        );
    }

    console.log("\nIRIS EXPLORATORY DATA ANALYSIS");
    console.log("==================================");
    console.log(`Source: ${dataset.source}`);
    console.log(`Valid rows: ${dataset.observations.length}`);
    console.log(`Rejected rows: ${dataset.rejectedRows.length}`);
    console.log(`Accepted events: ${events.accepted}`);
    console.log(`Rejected events: ${events.rejected}`);

    console.log("\nDescriptive statistics:");

    for (const [feature, result] of engine.statistics()) {
        console.log(
            `${feature.padEnd(16)} ` +
            `mean=${result.mean.toFixed(3)} ` +
            `median=${result.median.toFixed(3)} ` +
            `SD=${result.standardDeviation.toFixed(3)} ` +
            `outliers=${result.outlierCount}`
        );
    }

    console.log(
        `\nReport: ${path.join(outputDirectory, "analytical_report.md")}`
    );

    console.log(
        `Cleaned data: ${path.join(outputDirectory, "iris_cleaned.csv")}`
    );

    console.log("\nAnalysis completed.");
}

main().catch(error => {
    console.error(`EDA failed: ${error.message}`);
    process.exitCode = 1;
});
