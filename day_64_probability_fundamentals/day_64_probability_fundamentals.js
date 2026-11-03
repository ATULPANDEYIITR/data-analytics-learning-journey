"use strict";

/*
 * Probability Fundamentals
 *
 * This implementation uses JavaScript's Map and Set collections to model
 * discrete probability spaces and an event-driven experiment runner.
 */

class ProbabilityError extends Error {
    constructor(message) {
        super(message);
        this.name = "ProbabilityError";
    }
}

class ProbabilitySpace {
    constructor(probabilities) {
        if (!(probabilities instanceof Map) || probabilities.size === 0) {
            throw new ProbabilityError("A non-empty Map of probabilities is required.");
        }

        this.probabilities = new Map(probabilities);

        let total = 0;
        for (const [outcome, probability] of this.probabilities) {
            if (typeof outcome !== "string" || outcome.length === 0) {
                throw new ProbabilityError("Outcomes must be non-empty strings.");
            }

            if (!Number.isFinite(probability) || probability < 0 || probability > 1) {
                throw new ProbabilityError(
                    `Invalid probability for outcome ${outcome}.`
                );
            }

            total += probability;
        }

        if (Math.abs(total - 1) > 1e-12) {
            throw new ProbabilityError(
                `Probabilities must sum to 1. Received ${total}.`
            );
        }
    }

    validateEvent(event) {
        if (!(event instanceof Set)) {
            throw new ProbabilityError("Events must be represented by Set objects.");
        }

        for (const outcome of event) {
            if (!this.probabilities.has(outcome)) {
                throw new ProbabilityError(`Unknown outcome: ${outcome}`);
            }
        }
    }

    probability(event) {
        this.validateEvent(event);

        let result = 0;
        for (const outcome of event) {
            result += this.probabilities.get(outcome);
        }
        return result;
    }

    complement(event) {
        this.validateEvent(event);

        const result = new Set();
        for (const outcome of this.probabilities.keys()) {
            if (!event.has(outcome)) {
                result.add(outcome);
            }
        }
        return result;
    }

    intersection(a, b) {
        this.validateEvent(a);
        this.validateEvent(b);

        const result = new Set();
        for (const outcome of a) {
            if (b.has(outcome)) {
                result.add(outcome);
            }
        }
        return result;
    }

    union(a, b) {
        this.validateEvent(a);
        this.validateEvent(b);

        return new Set([...a, ...b]);
    }

    conditionalProbability(event, given) {
        const pGiven = this.probability(given);

        if (pGiven === 0) {
            throw new ProbabilityError(
                "Conditional probability is undefined when P(given) = 0."
            );
        }

        return this.probability(this.intersection(event, given)) / pGiven;
    }

    areIndependent(a, b, tolerance = 1e-12) {
        const pIntersection = this.probability(this.intersection(a, b));
        const product = this.probability(a) * this.probability(b);

        return Math.abs(pIntersection - product) <= tolerance;
    }
}

class Experiment {
    constructor(name, outcomes) {
        if (!name || !Array.isArray(outcomes) || outcomes.length === 0) {
            throw new ProbabilityError("Experiment requires a name and outcomes.");
        }

        this.name = name;
        this.outcomes = [...outcomes];
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (typeof listener !== "function") {
            throw new ProbabilityError("Listener must be a function.");
        }

        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(listener);
        return this;
    }

    emit(eventName, payload) {
        for (const listener of this.listeners.get(eventName) ?? []) {
            listener(payload);
        }
    }

    run(trials, random = Math.random) {
        if (!Number.isInteger(trials) || trials <= 0) {
            throw new ProbabilityError("Trials must be a positive integer.");
        }

        if (typeof random !== "function") {
            throw new ProbabilityError("Random source must be callable.");
        }

        const counts = new Map(
            this.outcomes.map((outcome) => [outcome, 0])
        );

        for (let i = 0; i < trials; i++) {
            const index = Math.floor(random() * this.outcomes.length);

            if (index < 0 || index >= this.outcomes.length) {
                throw new ProbabilityError("Random source returned an invalid value.");
            }

            const outcome = this.outcomes[index];
            counts.set(outcome, counts.get(outcome) + 1);
            this.emit("trial", { trial: i + 1, outcome });
        }

        this.emit("complete", { trials, counts });
        return counts;
    }
}

function binomialProbability(n, successes, p) {
    if (!Number.isInteger(n) || n < 0) {
        throw new ProbabilityError("n must be a non-negative integer.");
    }

    if (!Number.isInteger(successes) || successes < 0 || successes > n) {
        throw new ProbabilityError("Invalid number of successes.");
    }

    if (!Number.isFinite(p) || p < 0 || p > 1) {
        throw new ProbabilityError("p must be between 0 and 1.");
    }

    let coefficient = 1;

    // Multiplicative computation avoids factorial overflow for moderate n.
    for (let k = 1; k <= Math.min(successes, n - successes); k++) {
        coefficient *= (n - k + 1) / k;
    }

    return coefficient * p ** successes * (1 - p) ** (n - successes);
}

function formatSet(set) {
    return `{${[...set].join(", ")}}`;
}

function main() {
    const die = new ProbabilitySpace(
        new Map([
            ["1", 1 / 6],
            ["2", 1 / 6],
            ["3", 1 / 6],
            ["4", 1 / 6],
            ["5", 1 / 6],
            ["6", 1 / 6],
        ])
    );

    const even = new Set(["2", "4", "6"]);
    const high = new Set(["5", "6"]);
    const odd = new Set(["1", "3", "5"]);

    console.log("=== Probability Fundamentals ===");
    console.log(`P(even) = ${die.probability(even).toFixed(4)}`);
    console.log(`P(high) = ${die.probability(high).toFixed(4)}`);
    console.log(`P(not even) = ${die.probability(die.complement(even)).toFixed(4)}`);

    const intersection = die.intersection(even, high);
    const union = die.union(even, high);

    console.log(`A ∩ B = ${formatSet(intersection)}`);
    console.log(`A ∪ B = ${formatSet(union)}`);
    console.log(`P(A ∪ B) = ${die.probability(union).toFixed(4)}`);

    console.log(
        `P(even | high) = ${die.conditionalProbability(even, high).toFixed(4)}`
    );

    console.log(
        `Even and high independent = ${die.areIndependent(even, high)}`
    );

    const target = high;
    const totalProbability =
        die.conditionalProbability(target, odd) * die.probability(odd) +
        die.conditionalProbability(target, even) * die.probability(even);

    console.log(`Law of total probability = ${totalProbability.toFixed(4)}`);

    console.log("\n=== Binomial Model ===");
    console.log(
        `P(exactly 3 successes in 10 trials, p=0.2) = ` +
        `${binomialProbability(10, 3, 0.2).toFixed(6)}`
    );

    console.log("\n=== Event-Driven Experiment ===");
    const experiment = new Experiment("Coin Toss", ["H", "T"]);

    experiment.on("complete", ({ trials, counts }) => {
        console.log(`Completed ${trials} trials.`);
        console.log(`Heads: ${counts.get("H")}`);
        console.log(`Tails: ${counts.get("T")}`);
    });

    experiment.run(1000);

    console.log("\n=== Validation ===");
    try {
        new ProbabilitySpace(new Map([["A", 0.4], ["B", 0.4]]));
    } catch (error) {
        console.log(`Rejected invalid model: ${error.message}`);
    }
}

main();
