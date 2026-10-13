"use strict";

/*
 * JavaScript data structures for an event-driven repository dashboard.
 * Run with Node.js 18 or later:
 *     node data_structures.js
 *
 * Focus: arrays, tuples represented by frozen arrays, Set, Map, nested
 * objects, array transformations, grouping, validation, asynchronous
 * processing, and safe handling of untrusted data.
 */

class DataValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "DataValidationError";
    }
}

function requireString(value, field) {
    if (typeof value !== "string" || value.trim() === "") {
        throw new DataValidationError(`${field} must be a non-empty string.`);
    }
    return value.trim();
}

function requireNonNegativeInteger(value, field) {
    if (!Number.isSafeInteger(value) || value < 0) {
        throw new DataValidationError(
            `${field} must be a non-negative safe integer.`
        );
    }
    return value;
}

function createRepository({
    name,
    language,
    stars = 0,
    topics = [],
    maintainers = [],
    archived = false,
    metadata = {}
}) {
    requireString(name, "name");
    requireString(language, "language");
    requireNonNegativeInteger(stars, "stars");

    if (!Array.isArray(topics) || !topics.every(
        topic => typeof topic === "string" && topic.trim() !== ""
    )) {
        throw new DataValidationError("topics must contain non-empty strings.");
    }

    if (!Array.isArray(maintainers) || !maintainers.every(
        person => typeof person === "string" && person.trim() !== ""
    )) {
        throw new DataValidationError(
            "maintainers must contain non-empty strings."
        );
    }

    if (typeof archived !== "boolean") {
        throw new DataValidationError("archived must be a boolean.");
    }

    if (
        metadata === null ||
        typeof metadata !== "object" ||
        Array.isArray(metadata)
    ) {
        throw new DataValidationError("metadata must be an object.");
    }

    return {
        name: name.trim(),
        language: language.trim().toLowerCase(),
        stars,
        topics: new Set(topics.map(topic => topic.trim().toLowerCase())),
        maintainers: Object.freeze([...maintainers]),
        archived,
        metadata: { ...metadata }
    };
}

function demonstrateArrays() {
    console.log("\nARRAYS: ordered, mutable sequences");

    const repositories = [
        "market-prism",
        "portfolio-ui",
        "security-audit"
    ];

    repositories.push("data-warehouse");
    repositories.splice(1, 1, "portfolio-dashboard");

    console.log("Updated repositories:", repositories);
    console.log("Last repository:", repositories.at(-1));
    console.log("Selected repositories:", repositories.slice(0, 2));

    // slice creates a new outer array. Nested objects remain shared.
    const deploymentHistory = [
        { id: "DEP-101", status: "passed" },
        { id: "DEP-102", status: "failed" }
    ];
    const historyCopy = deploymentHistory.slice();
    historyCopy[0].status = "reviewed";

    console.log("Shared nested mutation:", deploymentHistory[0]);

    // structuredClone copies supported nested data instead of sharing it.
    const independentHistory = structuredClone(deploymentHistory);
    independentHistory[0].status = "approved";
    console.log("Independent history:", independentHistory);
    console.log("Original history:", deploymentHistory);
}

function demonstrateSets() {
    console.log("\nSETS: unique values and set operations");

    const requiredChecks = new Set(["lint", "tests", "security"]);
    const completedChecks = new Set(["tests", "security", "coverage"]);

    const missing = [...requiredChecks].filter(
        check => !completedChecks.has(check)
    );
    const unexpected = [...completedChecks].filter(
        check => !requiredChecks.has(check)
    );

    console.log("Missing required checks:", missing);
    console.log("Unexpected checks:", unexpected);
    console.log(
        "All distinct checks:",
        [...new Set([...requiredChecks, ...completedChecks])].sort()
    );

    const repositoryTopics = new Set(["security", "api", "security"]);
    console.log("Duplicate topics removed:", [...repositoryTopics]);

    // Set preserves insertion order in JavaScript, unlike an unordered
    // mathematical set. Sorting still helps produce canonical reports.
    console.log("Sorted topics:", [...repositoryTopics].sort());
}

function demonstrateMaps() {
    console.log("\nMAPS: key-value storage");

    const deployments = new Map([
        ["DEP-201", { service: "portfolio-api", status: "passed" }],
        ["DEP-202", { service: "risk-engine", status: "failed" }]
    ]);

    deployments.set("DEP-203", {
        service: "security-monitor",
        status: "pending"
    });

    console.log("Known deployment:", deployments.get("DEP-201"));
    console.log("Deployment exists:", deployments.has("DEP-202"));

    for (const [deploymentId, deployment] of deployments) {
        console.log(deploymentId, deployment.status);
    }

    // Map supports object keys and avoids accidental collisions with
    // inherited object property names.
    const serviceKey = { id: "portfolio-api" };
    const serviceHealth = new Map([[serviceKey, "healthy"]]);
    console.log("Object-key lookup:", serviceHealth.get(serviceKey));
}

function demonstrateObjectsAndNestedData() {
    console.log("\nOBJECTS: nested repository records");

    const deployment = {
        id: "DEP-305",
        service: {
            name: "market-prism",
            version: "3.2.0"
        },
        checks: [
            { name: "unit-tests", passed: true, durationMs: 410 },
            { name: "security-scan", passed: true, durationMs: 780 },
            { name: "integration-tests", passed: false, durationMs: 1450 }
        ],
        regions: new Set(["ap-south-1", "eu-west-1"])
    };

    const failedChecks = deployment.checks
        .filter(check => check.passed === false)
        .map(check => check.name);

    const totalDuration = deployment.checks.reduce(
        (total, check) => total + check.durationMs,
        0
    );

    console.log("Service:", deployment.service.name);
    console.log("Failed checks:", failedChecks);
    console.log("Duration:", totalDuration);
    console.log("Regions:", [...deployment.regions].sort());

    // Object spread is shallow. This copy still shares service and checks.
    const shallow = { ...deployment };
    shallow.service.version = "3.3.0";
    console.log("Nested reference shared:", deployment.service.version);

    // structuredClone supports ordinary nested data, arrays, Maps, and Sets.
    const isolated = structuredClone(deployment);
    isolated.service.version = "3.4.0";
    isolated.checks[0].passed = false;
    console.log("Independent version:", isolated.service.version);
    console.log("Original version:", deployment.service.version);
}

function demonstrateDestructuringAndImmutability() {
    console.log("\nDESTRUCTURING AND IMMUTABILITY");

    const release = Object.freeze([
        "market-prism",
        "4.0.0",
        "production"
    ]);

    const [name, version, environment] = release;
    console.log({ name, version, environment });

    // Object.freeze is shallow. Freeze nested objects separately when
    // immutable snapshots are required.
    const policy = Object.freeze({
        requiredApprovals: 2,
        requiredChecks: Object.freeze(["lint", "tests", "security"])
    });

    console.log("Required approvals:", policy.requiredApprovals);
    console.log("Required checks:", policy.requiredChecks);
}

function createCatalog() {
    return [
        createRepository({
            name: "market-prism",
            language: "Python",
            stars: 320,
            topics: ["finance", "analytics", "api"],
            maintainers: ["Anika", "Rahul"],
            metadata: { tier: "production", testsPassing: true }
        }),
        createRepository({
            name: "portfolio-ui",
            language: "JavaScript",
            stars: 210,
            topics: ["dashboard", "analytics"],
            maintainers: ["Meera"],
            metadata: { tier: "production", testsPassing: true }
        }),
        createRepository({
            name: "security-audit",
            language: "Python",
            stars: 145,
            topics: ["security", "automation"],
            maintainers: ["Rahul", "Dev"],
            metadata: { tier: "internal", testsPassing: false }
        }),
        createRepository({
            name: "data-warehouse",
            language: "SQL",
            stars: 88,
            topics: ["analytics", "data"],
            maintainers: ["Anika"],
            metadata: { tier: "internal", testsPassing: true }
        }),
        createRepository({
            name: "legacy-reports",
            language: "Java",
            stars: 34,
            topics: ["reporting", "legacy"],
            maintainers: ["Dev"],
            archived: true,
            metadata: { tier: "archived", testsPassing: true }
        })
    ];
}

function analyzeCatalog(repositories) {
    const names = new Set();

    for (const repository of repositories) {
        if (names.has(repository.name)) {
            throw new DataValidationError(
                `Duplicate repository: ${repository.name}`
            );
        }
        names.add(repository.name);
    }

    const active = repositories.filter(repo => !repo.archived);

    const languageCounts = active.reduce((counts, repository) => {
        counts.set(
            repository.language,
            (counts.get(repository.language) ?? 0) + 1
        );
        return counts;
    }, new Map());

    const topicIndex = new Map();
    const maintainerIndex = new Map();

    for (const repository of active) {
        for (const topic of repository.topics) {
            if (!topicIndex.has(topic)) {
                topicIndex.set(topic, []);
            }
            topicIndex.get(topic).push(repository.name);
        }

        for (const maintainer of repository.maintainers) {
            if (!maintainerIndex.has(maintainer)) {
                maintainerIndex.set(maintainer, new Set());
            }
            maintainerIndex.get(maintainer).add(repository.name);
        }
    }

    return {
        total: repositories.length,
        active: active.length,
        archived: repositories.length - active.length,
        languageCounts: Object.fromEntries(
            [...languageCounts.entries()].sort(([a], [b]) => a.localeCompare(b))
        ),
        topicIndex: Object.fromEntries(
            [...topicIndex.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([topic, names]) => [topic, [...names].sort()])
        ),
        maintainerIndex: Object.fromEntries(
            [...maintainerIndex.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([person, names]) => [person, [...names].sort()])
        ),
        failingRepositories: active
            .filter(repo => repo.metadata.testsPassing !== true)
            .map(repo => repo.name),
        highStarRepositories: active
            .filter(repo => repo.stars >= 200)
            .map(repo => repo.name)
    };
}

function demonstrateArrayTransformation() {
    console.log("\nARRAY TRANSFORMATION PIPELINE");

    const events = [
        { repository: "market-prism", status: "passed", durationMs: 500 },
        { repository: "portfolio-ui", status: "failed", durationMs: 800 },
        { repository: "market-prism", status: "passed", durationMs: 450 },
        { repository: "security-audit", status: "failed", durationMs: 1200 }
    ];

    const failedEvents = events
        .filter(event => event.status === "failed")
        .map(({ repository, durationMs }) => ({
            repository,
            durationMs,
            needsAttention: durationMs > 1000
        }))
        .sort((a, b) => b.durationMs - a.durationMs);

    const averageDuration = events.length
        ? events.reduce((sum, event) => sum + event.durationMs, 0) /
          events.length
        : 0;

    console.log("Failures:", failedEvents);
    console.log("Average duration:", averageDuration);
}

async function processDeploymentEvents(events) {
    console.log("\nASYNCHRONOUS EVENT PROCESSING");

    const processed = await Promise.all(
        events.map(async event => {
            // Yield to the event loop so this function models an asynchronous
            // validation step without external services or dependencies.
            await Promise.resolve();

            if (
                typeof event.id !== "string" ||
                typeof event.status !== "string"
            ) {
                throw new DataValidationError("Invalid deployment event.");
            }

            return {
                id: event.id,
                status: event.status,
                accepted: ["passed", "failed", "pending"].includes(event.status)
            };
        })
    );

    return processed;
}

async function demonstrateErrorHandling() {
    console.log("\nERROR HANDLING AND UNTRUSTED DATA");

    try {
        createRepository({
            name: " ",
            language: "python",
            stars: 10
        });
    } catch (error) {
        if (error instanceof DataValidationError) {
            console.log("Rejected invalid repository:", error.message);
        } else {
            throw error;
        }
    }

    const externalPayload = JSON.parse(
        '{"name":"worker","stars":"unknown"}'
    );

    if (
        typeof externalPayload.name !== "string" ||
        !Number.isSafeInteger(externalPayload.stars) ||
        externalPayload.stars < 0
    ) {
        console.log("External payload rejected by validation.");
    }

    const outcomes = await processDeploymentEvents([
        { id: "DEP-501", status: "passed" },
        { id: "DEP-502", status: "failed" }
    ]);

    console.log("Processed events:", outcomes);

    try {
        await processDeploymentEvents([{ id: "DEP-503", status: null }]);
    } catch (error) {
        console.log("Event processing failed:", error.message);
    }
}

function demonstrateSerialization() {
    console.log("\nSERIALIZATION");

    const repository = createRepository({
        name: "market-prism",
        language: "python",
        stars: 320,
        topics: ["finance", "analytics"],
        maintainers: ["Anika", "Rahul"]
    });

    // JSON.stringify does not serialize a Set's entries by default.
    const jsonReady = {
        ...repository,
        topics: [...repository.topics].sort()
    };

    const json = JSON.stringify(jsonReady, null, 2);
    const restored = JSON.parse(json);

    console.log("Serialized repository:", json);
    console.log("Restored topics:", restored.topics);
}

async function main() {
    console.log("JAVASCRIPT DATA STRUCTURES FOR REPOSITORY OPERATIONS");

    demonstrateArrays();
    demonstrateSets();
    demonstrateMaps();
    demonstrateObjectsAndNestedData();
    demonstrateDestructuringAndImmutability();
    demonstrateArrayTransformation();
    demonstrateSerialization();

    const report = analyzeCatalog(createCatalog());
    console.log("\nCATALOG REPORT");
    console.log(JSON.stringify(report, null, 2));

    await demonstrateErrorHandling();

    console.log("\nAll demonstrations completed.");
}

main().catch(error => {
    console.error("Fatal execution error:", error.message);
    process.exitCode = 1;
});
