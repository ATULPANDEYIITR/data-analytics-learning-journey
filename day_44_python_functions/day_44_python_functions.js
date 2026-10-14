"use strict";

/*
 * Python Functions concepts expressed through JavaScript function mechanics.
 * Run with Node.js 18 or later:
 *     node javascript_functions.js
 *
 * The implementation emphasizes callbacks, closures, promise-based
 * composition, function context, memoization, and event-driven processing.
 */

// Function declarations are hoisted, which can matter when functions
// reference other declarations earlier in the source file.
function calculateShipping(weightKg, distanceKm, options = {}) {
    const {
        express = false,
        insuranceValue = 0
    } = options;

    if (!Number.isFinite(weightKg) || weightKg <= 0) {
        throw new RangeError("Weight must be a positive finite number.");
    }

    if (!Number.isFinite(distanceKm) || distanceKm < 0) {
        throw new RangeError("Distance must be a non-negative finite number.");
    }

    if (!Number.isFinite(insuranceValue) || insuranceValue < 0) {
        throw new RangeError("Insurance value must be non-negative.");
    }

    const base = 45 + weightKg * 12 + distanceKm * 0.8;
    const expressCharge = express ? base * 0.35 : 0;
    const insuranceCharge = insuranceValue * 0.002;

    return Number((base + expressCharge + insuranceCharge).toFixed(2));
}

// JavaScript supports positional parameters and default parameter values.
// It does not enforce declared parameter types at runtime.
function describeDeployment(service, environment = "staging") {
    if (typeof service !== "string" || !service.trim()) {
        throw new TypeError("A service name is required.");
    }

    const allowedEnvironments = new Set(["development", "staging", "production"]);

    if (!allowedEnvironments.has(environment)) {
        throw new RangeError(`Unsupported environment: ${environment}`);
    }

    return `${service.trim()} deployed to ${environment}`;
}

// Rest parameters collect remaining positional arguments into a real array.
function calculateMean(...values) {
    if (values.length === 0) {
        return null;
    }

    if (values.some(value => !Number.isFinite(value))) {
        throw new TypeError("All values must be finite numbers.");
    }

    return values.reduce((total, value) => total + value, 0) / values.length;
}

// Object destructuring provides named options and makes call sites clearer.
function calculateCloudCost({
    computeHours,
    storageGb,
    requestCount = 0,
    reservedDiscount = 0
}) {
    for (const [name, value] of Object.entries({
        computeHours,
        storageGb,
        requestCount,
        reservedDiscount
    })) {
        if (!Number.isFinite(value) || value < 0) {
            throw new RangeError(`${name} must be a non-negative finite number.`);
        }
    }

    if (reservedDiscount > 1) {
        throw new RangeError("reservedDiscount must not exceed 1.");
    }

    const compute = computeHours * 0.12;
    const storage = storageGb * 0.025;
    const requests = requestCount / 1_000_000 * 0.40;
    const beforeDiscount = compute + storage + requests;

    return Number((beforeDiscount * (1 - reservedDiscount)).toFixed(4));
}

// A function can return undefined when execution reaches the end without return.
function logDeployment(service) {
    console.log(`Deployment requested for ${service}`);
}

// Arrow functions capture lexical `this`; they do not create their own `this`.
const applyTransformation = (value, transformation) => transformation(value);

const roundCurrency = value => Math.round((value + Number.EPSILON) * 100) / 100;
const addServiceFee = rate => amount => roundCurrency(amount * (1 + rate));

// Closures retain access to their lexical environment.
function createRateLimiter(maximumCalls) {
    if (!Number.isInteger(maximumCalls) || maximumCalls < 1) {
        throw new RangeError("maximumCalls must be a positive integer.");
    }

    let calls = 0;

    return function executeIfAllowed(operation) {
        if (calls >= maximumCalls) {
            throw new Error("Call limit reached.");
        }

        calls += 1;
        return operation();
    };
}

// A higher-order function receives another function and controls when it runs.
function retry(operation, maximumAttempts = 3) {
    if (typeof operation !== "function") {
        throw new TypeError("operation must be a function.");
    }

    if (!Number.isInteger(maximumAttempts) || maximumAttempts < 1) {
        throw new RangeError("maximumAttempts must be positive.");
    }

    let lastError;

    for (let attempt = 1; attempt <= maximumAttempts; attempt += 1) {
        try {
            return operation(attempt);
        } catch (error) {
            lastError = error;
        }
    }

    throw new Error(
        `Operation failed after ${maximumAttempts} attempts.`,
        { cause: lastError }
    );
}

// Decorators can be implemented as ordinary functions that wrap other functions.
function withExecutionMetrics(operation) {
    return function measuredOperation(...args) {
        const start = performance.now();

        try {
            return operation.apply(this, args);
        } finally {
            const elapsed = performance.now() - start;
            console.log(`${operation.name || "anonymous"}: ${elapsed.toFixed(3)} ms`);
        }
    };
}

// Memoization caches pure function results. This example uses JSON serialization
// for a restricted set of JSON-compatible primitive arguments.
function memoize(operation) {
    const cache = new Map();

    return function memoized(...args) {
        const key = JSON.stringify(args);

        if (cache.has(key)) {
            return cache.get(key);
        }

        const result = operation.apply(this, args);
        cache.set(key, result);
        return result;
    };
}

const fibonacci = memoize(function fibonacciNumber(number) {
    if (!Number.isInteger(number) || number < 0 || number > 75) {
        throw new RangeError("Number must be an integer from 0 through 75.");
    }

    if (number < 2) {
        return number;
    }

    return fibonacci(number - 1) + fibonacci(number - 2);
});

// Async functions always return promises. A thrown error becomes a rejection.
async function fetchDeploymentStatus(service, simulatedLatencyMs = 20) {
    if (typeof service !== "string" || !service.trim()) {
        throw new TypeError("A service name is required.");
    }

    if (!Number.isFinite(simulatedLatencyMs) || simulatedLatencyMs < 0) {
        throw new RangeError("Latency must be non-negative.");
    }

    await new Promise(resolve => setTimeout(resolve, simulatedLatencyMs));

    return {
        service: service.trim(),
        state: "healthy",
        checkedAt: new Date().toISOString()
    };
}

// Promise.all provides concurrent execution and rejects if one task rejects.
// The tasks below are independent health checks, so concurrency is appropriate.
async function inspectServices(serviceNames) {
    if (!Array.isArray(serviceNames) || serviceNames.length === 0) {
        throw new TypeError("Provide at least one service name.");
    }

    return Promise.all(
        serviceNames.map(name => fetchDeploymentStatus(name))
    );
}

// This pipeline processes an event using small composable transformations.
function createEventPipeline(handlers) {
    if (!Array.isArray(handlers) || handlers.some(handler => typeof handler !== "function")) {
        throw new TypeError("Every pipeline handler must be a function.");
    }

    return function processEvent(initialEvent) {
        return handlers.reduce(
            (event, handler) => handler(event),
            initialEvent
        );
    };
}

const deploymentPipeline = createEventPipeline([
    event => ({ ...event, service: event.service.trim() }),
    event => {
        if (!event.service) {
            throw new Error("Service cannot be empty.");
        }
        return event;
    },
    event => ({ ...event, normalizedEnvironment: event.environment.toLowerCase() }),
    event => ({ ...event, accepted: true })
]);

// Function context is dynamic for ordinary methods. Extracting a method can
// lose its receiver; bind creates a function with a fixed `this`.
const deploymentManager = {
    name: "ProductionManager",

    report(service) {
        return `${this.name} is managing ${service}`;
    }
};

const boundReport = deploymentManager.report.bind(deploymentManager);

// Generator functions return iterators and pause at each yield expression.
function* generateCostSnapshots(hourlyRate, hours) {
    if (!Number.isFinite(hourlyRate) || hourlyRate < 0) {
        throw new RangeError("Hourly rate must be non-negative.");
    }

    if (!Number.isInteger(hours) || hours < 0) {
        throw new RangeError("Hours must be a non-negative integer.");
    }

    let cumulative = 0;

    for (let hour = 1; hour <= hours; hour += 1) {
        cumulative += hourlyRate;
        yield { hour, cumulativeCost: roundCurrency(cumulative) };
    }
}

async function main() {
    console.log("Parameters and return values");
    console.log(calculateShipping(3.5, 250, { express: true, insuranceValue: 5000 }));
    console.log(describeDeployment("billing-api", "production"));
    console.log("Mean:", calculateMean(72, 84, 96));

    console.log("\nNamed options");
    console.log(calculateCloudCost({
        computeHours: 730,
        storageGb: 250,
        requestCount: 4_000_000,
        reservedDiscount: 0.15
    }));

    console.log("\nReturn semantics");
    console.log("Implicit return value:", logDeployment("inventory-api"));

    console.log("\nHigher-order functions and closures");
    const withServiceFee = addServiceFee(0.08);
    console.log(applyTransformation(2500, withServiceFee));

    const limitedOperation = createRateLimiter(2);
    console.log(limitedOperation(() => "first call"));
    console.log(limitedOperation(() => "second call"));

    try {
        limitedOperation(() => "third call");
    } catch (error) {
        console.log("Expected limit:", error.message);
    }

    console.log("\nRetry behavior");
    let transientFailures = 0;

    const response = retry(() => {
        transientFailures += 1;

        if (transientFailures < 3) {
            throw new Error("Temporary deployment registry failure");
        }

        return { status: "available", attempts: transientFailures };
    }, 3);

    console.log(response);

    console.log("\nMemoization");
    console.log("Fibonacci(40):", fibonacci(40));
    console.log("Fibonacci(40) from cache:", fibonacci(40));

    console.log("\nMeasured operation");
    const measuredTotal = withExecutionMetrics(function totalCosts(costs) {
        return costs.reduce((sum, cost) => sum + cost, 0);
    });

    console.log(measuredTotal([120, 240, 360]));

    console.log("\nEvent pipeline");
    console.log(deploymentPipeline({
        service: "  Payments-API ",
        environment: "PRODUCTION"
    }));

    console.log("\nBound method context");
    console.log(boundReport("identity-service"));

    console.log("\nLazy cost snapshots");
    console.log([...generateCostSnapshots(0.12, 4)]);

    console.log("\nConcurrent health checks");
    try {
        const statuses = await inspectServices([
            "billing-api",
            "identity-service",
            "inventory-api"
        ]);

        console.log(statuses);
    } catch (error) {
        console.error("Health-check failure:", error.message);
    }

    console.log("\nValidation checks");
    try {
        calculateShipping(-2, 100);
    } catch (error) {
        console.log("Invalid shipping input:", error.message);
    }

    try {
        deploymentPipeline({ service: " ", environment: "production" });
    } catch (error) {
        console.log("Rejected event:", error.message);
    }

    console.log("\nAll demonstrations completed.");
}

main().catch(error => {
    console.error("Application failed:", error);
    process.exitCode = 1;
});
