"use strict";

/*
 * Probability Distributions
 *
 * Node.js implementation of:
 * Bernoulli, Binomial, Geometric, Poisson,
 * Uniform, Normal, and Exponential distributions.
 *
 * Features:
 * - Probability mass and density functions.
 * - Cumulative distribution functions.
 * - Statistical moments.
 * - Random sampling.
 * - Seeded pseudo-random generation.
 * - Asynchronous simulation batches.
 * - Distribution comparison and validation.
 *
 * Run: node probability_distributions.js
 */

const { performance } = require("node:perf_hooks");
const { EventEmitter } = require("node:events");

class DistributionError extends Error {
    constructor(message) {
        super(message);
        this.name = "DistributionError";
    }
}

function assertFinite(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new DistributionError(`${name} must be finite.`);
    }
}

function assertProbability(p) {
    assertFinite(p, "Probability");

    if (p < 0 || p > 1) {
        throw new DistributionError("Probability must be in [0, 1].");
    }
}

function assertNonNegativeInteger(value, name) {
    if (!Number.isSafeInteger(value) || value < 0) {
        throw new DistributionError(
            `${name} must be a non-negative safe integer.`
        );
    }
}

function assertPositive(value, name) {
    assertFinite(value, name);

    if (value <= 0) {
        throw new DistributionError(`${name} must be positive.`);
    }
}

function logFactorial(n) {
    if (n < 0 || !Number.isSafeInteger(n)) {
        return Infinity;
    }

    let result = 0;

    for (let i = 2; i <= n; i++) {
        result += Math.log(i);
    }

    return result;
}

function logCombination(n, k) {
    if (k < 0 || k > n) {
        return -Infinity;
    }

    return (
        logFactorial(n)
        - logFactorial(k)
        - logFactorial(n - k)
    );
}

class RandomGenerator {
    /*
     * Mulberry32 provides reproducible pseudo-random values.
     * It is suitable for simulations, not cryptography.
     */

    constructor(seed = Date.now()) {
        this.state = seed >>> 0;
    }

    next() {
        let t = this.state += 0x6D2B79F5;

        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);

        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }

    normal() {
        // Box-Muller transformation.
        const u1 = Math.max(this.next(), Number.MIN_VALUE);
        const u2 = this.next();

        return Math.sqrt(-2 * Math.log(u1))
            * Math.cos(2 * Math.PI * u2);
    }
}

class Distribution {
    constructor(seed) {
        this.random = new RandomGenerator(seed);
    }

    mean() {
        throw new Error("mean() must be implemented.");
    }

    variance() {
        throw new Error("variance() must be implemented.");
    }

    sample() {
        throw new Error("sample() must be implemented.");
    }

    cdf() {
        throw new Error("cdf() must be implemented.");
    }

    standardDeviation() {
        return Math.sqrt(this.variance());
    }

    sampleMany(size) {
        assertNonNegativeInteger(size, "Sample size");

        return Array.from(
            { length: size },
            () => this.sample()
        );
    }

    empiricalStatistics(values) {
        if (!Array.isArray(values) || values.length === 0) {
            throw new DistributionError(
                "A non-empty sample array is required."
            );
        }

        const mean = values.reduce((sum, value) => sum + value, 0)
            / values.length;

        const variance = values.reduce(
            (sum, value) => sum + (value - mean) ** 2,
            0
        ) / values.length;

        return Object.freeze({
            count: values.length,
            mean,
            variance,
            standardDeviation: Math.sqrt(variance),
            minimum: Math.min(...values),
            maximum: Math.max(...values)
        });
    }
}

class Bernoulli extends Distribution {
    constructor(p, seed) {
        super(seed);
        assertProbability(p);
        this.p = p;
    }

    pmf(x) {
        if (x !== 0 && x !== 1) return 0;
        return x === 1 ? this.p : 1 - this.p;
    }

    cdf(x) {
        if (x < 0) return 0;
        if (x < 1) return 1 - this.p;
        return 1;
    }

    mean() {
        return this.p;
    }

    variance() {
        return this.p * (1 - this.p);
    }

    sample() {
        return Number(this.random.next() < this.p);
    }
}

class Binomial extends Distribution {
    constructor(n, p, seed) {
        super(seed);
        assertNonNegativeInteger(n, "Number of trials");
        assertProbability(p);

        this.n = n;
        this.p = p;
    }

    pmf(k) {
        if (!Number.isSafeInteger(k) || k < 0 || k > this.n) {
            return 0;
        }

        if (this.p === 0) return Number(k === 0);
        if (this.p === 1) return Number(k === this.n);

        const logProbability =
            logCombination(this.n, k)
            + k * Math.log(this.p)
            + (this.n - k) * Math.log1p(-this.p);

        return Math.exp(logProbability);
    }

    cdf(x) {
        if (x < 0) return 0;
        if (x >= this.n) return 1;

        const upper = Math.floor(x);
        let total = 0;

        for (let k = 0; k <= upper; k++) {
            total += this.pmf(k);
        }

        return Math.min(1, total);
    }

    mean() {
        return this.n * this.p;
    }

    variance() {
        return this.n * this.p * (1 - this.p);
    }

    sample() {
        let successes = 0;

        for (let i = 0; i < this.n; i++) {
            if (this.random.next() < this.p) {
                successes++;
            }
        }

        return successes;
    }
}

class Geometric extends Distribution {
    constructor(p, seed) {
        super(seed);
        assertProbability(p);

        if (p === 0) {
            throw new DistributionError(
                "Geometric probability must be greater than zero."
            );
        }

        this.p = p;
    }

    pmf(k) {
        if (!Number.isSafeInteger(k) || k < 1) return 0;

        if (this.p === 1) return Number(k === 1);

        return Math.exp(
            Math.log(this.p)
            + (k - 1) * Math.log1p(-this.p)
        );
    }

    cdf(x) {
        if (x < 1) return 0;
        if (this.p === 1) return 1;

        return -Math.expm1(
            Math.floor(x) * Math.log1p(-this.p)
        );
    }

    mean() {
        return 1 / this.p;
    }

    variance() {
        return (1 - this.p) / (this.p * this.p);
    }

    sample() {
        if (this.p === 1) return 1;

        const u = this.random.next();

        return Math.floor(
            Math.log1p(-u) / Math.log1p(-this.p)
        ) + 1;
    }
}

class Poisson extends Distribution {
    constructor(lambda, seed) {
        super(seed);
        assertFinite(lambda, "Poisson rate");

        if (lambda < 0) {
            throw new DistributionError(
                "Poisson rate cannot be negative."
            );
        }

        this.lambda = lambda;
    }

    pmf(k) {
        if (!Number.isSafeInteger(k) || k < 0) return 0;
        if (this.lambda === 0) return Number(k === 0);

        return Math.exp(
            -this.lambda
            + k * Math.log(this.lambda)
            - logFactorial(k)
        );
    }

    cdf(x) {
        if (x < 0) return 0;
        if (this.lambda === 0) return 1;

        const upper = Math.floor(x);
        let total = 0;

        for (let k = 0; k <= upper; k++) {
            total += this.pmf(k);
        }

        return Math.min(1, total);
    }

    mean() {
        return this.lambda;
    }

    variance() {
        return this.lambda;
    }

    sample() {
        if (this.lambda === 0) return 0;

        /*
         * Knuth's exact algorithm.
         * Runtime is proportional to the event rate.
         * A production high-rate service should use
         * an optimized transformed-rejection algorithm.
         */
        if (this.lambda >= 30) {
            throw new DistributionError(
                "Knuth sampling is restricted to rates below 30. "
                + "Use a transformed-rejection sampler for larger rates."
            );
        }

        const threshold = Math.exp(-this.lambda);
        let product = 1;
        let count = 0;

        do {
            product *= this.random.next();
            count++;
        } while (product > threshold);

        return count - 1;
    }
}

class Uniform extends Distribution {
    constructor(a, b, seed) {
        super(seed);
        assertFinite(a, "Lower bound");
        assertFinite(b, "Upper bound");

        if (a >= b) {
            throw new DistributionError(
                "Uniform distribution requires a < b."
            );
        }

        this.a = a;
        this.b = b;
    }

    pdf(x) {
        return x >= this.a && x <= this.b
            ? 1 / (this.b - this.a)
            : 0;
    }

    cdf(x) {
        if (x <= this.a) return 0;
        if (x >= this.b) return 1;

        return (x - this.a) / (this.b - this.a);
    }

    mean() {
        return (this.a + this.b) / 2;
    }

    variance() {
        return (this.b - this.a) ** 2 / 12;
    }

    sample() {
        return this.a + this.random.next() * (this.b - this.a);
    }
}

class Normal extends Distribution {
    constructor(mu, sigma, seed) {
        super(seed);
        assertFinite(mu, "Normal mean");
        assertPositive(sigma, "Normal standard deviation");

        this.mu = mu;
        this.sigma = sigma;
    }

    pdf(x) {
        const z = (x - this.mu) / this.sigma;

        return Math.exp(-0.5 * z * z)
            / (this.sigma * Math.sqrt(2 * Math.PI));
    }

    cdf(x) {
        const z = (x - this.mu) / (this.sigma * Math.SQRT2);
        return 0.5 * (1 + erf(z));
    }

    mean() {
        return this.mu;
    }

    variance() {
        return this.sigma ** 2;
    }

    sample() {
        return this.mu + this.sigma * this.random.normal();
    }

    standardize(x) {
        return (x - this.mu) / this.sigma;
    }

    intervalProbability(lower, upper) {
        if (lower > upper) {
            throw new DistributionError(
                "Lower bound cannot exceed upper bound."
            );
        }

        return this.cdf(upper) - this.cdf(lower);
    }
}

class Exponential extends Distribution {
    constructor(lambda, seed) {
        super(seed);
        assertPositive(lambda, "Exponential rate");
        this.lambda = lambda;
    }

    pdf(x) {
        return x < 0 ? 0 : this.lambda * Math.exp(-this.lambda * x);
    }

    cdf(x) {
        return x < 0
            ? 0
            : -Math.expm1(-this.lambda * x);
    }

    survival(x) {
        return x < 0 ? 1 : Math.exp(-this.lambda * x);
    }

    mean() {
        return 1 / this.lambda;
    }

    variance() {
        return 1 / (this.lambda ** 2);
    }

    sample() {
        const u = Math.max(this.random.next(), Number.MIN_VALUE);
        return -Math.log(u) / this.lambda;
    }
}

/*
 * Numerical approximation of the error function.
 * Maximum absolute error is approximately 1.5e-7.
 */
function erf(x) {
    const sign = x < 0 ? -1 : 1;
    const value = Math.abs(x);

    const t = 1 / (1 + 0.3275911 * value);

    const polynomial =
        (((((1.061405429 * t - 1.453152027) * t)
            + 1.421413741) * t
            - 0.284496736) * t
            + 0.254829592) * t;

    return sign * (
        1 - polynomial * Math.exp(-value * value)
    );
}

class SimulationEngine extends EventEmitter {
    constructor() {
        super();
        this.results = new Map();
    }

    async simulate(name, distribution, sampleSize, batchSize = 1000) {
        assertNonNegativeInteger(sampleSize, "Sample size");
        assertNonNegativeInteger(batchSize, "Batch size");

        if (batchSize === 0) {
            throw new DistributionError("Batch size must be positive.");
        }

        if (!(distribution instanceof Distribution)) {
            throw new DistributionError(
                "A valid distribution instance is required."
            );
        }

        const start = performance.now();
        const values = [];

        for (let offset = 0; offset < sampleSize; offset += batchSize) {
            const count = Math.min(batchSize, sampleSize - offset);
            const batch = distribution.sampleMany(count);

            values.push(...batch);

            this.emit("batch", {
                name,
                completed: values.length,
                total: sampleSize
            });

            // Yield control so event listeners and other tasks can run.
            await new Promise(resolve => setImmediate(resolve));
        }

        if (values.length === 0) {
            throw new DistributionError(
                "Cannot calculate statistics from an empty simulation."
            );
        }

        const result = {
            theoreticalMean: distribution.mean(),
            theoreticalVariance: distribution.variance(),
            empirical: distribution.empiricalStatistics(values),
            durationMilliseconds: performance.now() - start
        };

        this.results.set(name, Object.freeze(result));

        this.emit("completed", { name, result });

        return result;
    }
}

function assertClose(actual, expected, tolerance = 1e-8) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(
            `Assertion failed: ${actual} differs from ${expected}.`
        );
    }
}

function validateImplementations() {
    const bernoulli = new Bernoulli(0.3, 1);
    assertClose(bernoulli.pmf(0) + bernoulli.pmf(1), 1);

    const binomial = new Binomial(10, 0.5, 2);
    let binomialTotal = 0;

    for (let k = 0; k <= 10; k++) {
        binomialTotal += binomial.pmf(k);
    }

    assertClose(binomialTotal, 1);

    const geometric = new Geometric(0.5, 3);
    assertClose(geometric.cdf(1), 0.5);

    const poisson = new Poisson(0, 4);
    assertClose(poisson.pmf(0), 1);

    const uniform = new Uniform(0, 10, 5);
    assertClose(uniform.mean(), 5);

    const normal = new Normal(0, 1, 6);
    assertClose(normal.cdf(0), 0.5, 1e-6);

    const exponential = new Exponential(2, 7);
    assertClose(exponential.mean(), 0.5);

    assertClose(exponential.survival(2), Math.exp(-4));

    console.log("All validation assertions passed.");
}

async function main() {
    const distributions = new Map([
        ["Bernoulli", new Bernoulli(0.4, 101)],
        ["Binomial", new Binomial(20, 0.4, 102)],
        ["Geometric", new Geometric(0.2, 103)],
        ["Poisson", new Poisson(5, 104)],
        ["Uniform", new Uniform(10, 20, 105)],
        ["Normal", new Normal(50, 10, 106)],
        ["Exponential", new Exponential(0.5, 107)]
    ]);

    console.log("PROBABILITY DISTRIBUTIONS");
    console.log("=========================");

    const binomial = distributions.get("Binomial");
    console.log("Binomial P(X=5):", binomial.pmf(5));
    console.log("Binomial P(X<=5):", binomial.cdf(5));

    const normal = distributions.get("Normal");
    console.log("Normal P(X<=60):", normal.cdf(60));
    console.log(
        "Normal P(40<=X<=60):",
        normal.intervalProbability(40, 60)
    );

    const exponential = distributions.get("Exponential");
    console.log("Exponential P(X>2):", exponential.survival(2));

    const engine = new SimulationEngine();

    engine.on("batch", event => {
        if (event.completed === event.total) {
            console.log(`${event.name}: simulation batches completed.`);
        }
    });

    engine.on("completed", ({ name }) => {
        console.log(`${name}: simulation finished.`);
    });

    for (const [name, distribution] of distributions) {
        const result = await engine.simulate(
            name,
            distribution,
            10000,
            1000
        );

        console.log(`\n${name}`);
        console.log({
            theoreticalMean: result.theoreticalMean,
            empiricalMean: result.empirical.mean,
            theoreticalVariance: result.theoreticalVariance,
            empiricalVariance: result.empirical.variance,
            durationMilliseconds: result.durationMilliseconds
        });
    }

    validateImplementations();

    console.log("\nAll distribution simulations completed.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
