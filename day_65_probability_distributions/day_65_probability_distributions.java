import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.function.DoubleSupplier;

/*
 * Probability Distributions
 *
 * Enterprise-oriented statistical calculation and simulation service.
 *
 * Supports:
 * Bernoulli, Binomial, Geometric, Poisson,
 * Uniform, Normal, and Exponential distributions.
 *
 * Java 17 features:
 * - Interfaces and records
 * - Immutable parameter objects
 * - Enum-based distribution identification
 * - Custom exceptions
 * - Concurrent simulation execution
 * - Validation and service-layer separation
 */

public class ProbabilityDistributions {

    private static final double SQRT_TWO_PI =
            Math.sqrt(2.0 * Math.PI);

    enum DistributionType {
        BERNOULLI,
        BINOMIAL,
        GEOMETRIC,
        POISSON,
        UNIFORM,
        NORMAL,
        EXPONENTIAL
    }

    static class DistributionException extends IllegalArgumentException {
        public DistributionException(String message) {
            super(message);
        }
    }

    record Statistics(
            double mean,
            double variance,
            double standardDeviation
    ) {}

    record SimulationResult(
            DistributionType type,
            int sampleCount,
            double theoreticalMean,
            double empiricalMean,
            double theoreticalVariance,
            double empiricalVariance,
            double minimum,
            double maximum,
            long executionTimeMillis
    ) {}

    record SimulationPolicy(
            int minimumSamples,
            int maximumSamples,
            boolean requireFiniteResults
    ) {
        public SimulationPolicy {
            if (minimumSamples < 1 || maximumSamples < minimumSamples) {
                throw new DistributionException(
                        "Invalid simulation policy boundaries."
                );
            }
        }

        public void validate(int count) {
            if (count < minimumSamples || count > maximumSamples) {
                throw new DistributionException(
                        "Sample count violates simulation policy."
                );
            }
        }
    }

    interface ProbabilityDistribution {
        DistributionType type();

        double mean();

        double variance();

        double sample();

        double cdf(double x);

        default double standardDeviation() {
            return Math.sqrt(variance());
        }

        default Statistics statistics() {
            return new Statistics(
                    mean(),
                    variance(),
                    standardDeviation()
            );
        }
    }

    static final class Validation {

        private Validation() {}

        static void finite(double value, String name) {
            if (!Double.isFinite(value)) {
                throw new DistributionException(
                        name + " must be finite."
                );
            }
        }

        static void probability(double p) {
            finite(p, "Probability");

            if (p < 0.0 || p > 1.0) {
                throw new DistributionException(
                        "Probability must be in [0, 1]."
                );
            }
        }

        static void positive(double value, String name) {
            finite(value, name);

            if (value <= 0.0) {
                throw new DistributionException(
                        name + " must be positive."
                );
            }
        }

        static void count(int value, int maximum) {
            if (value < 0 || value > maximum) {
                throw new DistributionException(
                        "Count must be between 0 and " + maximum + "."
                );
            }
        }
    }

    static double logCombination(int n, int k) {
        if (k < 0 || k > n) {
            return Double.NEGATIVE_INFINITY;
        }

        return logFactorial(n)
                - logFactorial(k)
                - logFactorial(n - k);
    }

    static double logFactorial(int n) {
        if (n < 0) {
            return Double.POSITIVE_INFINITY;
        }

        double result = 0.0;

        for (int i = 2; i <= n; i++) {
            result += Math.log(i);
        }

        return result;
    }

    static final class Bernoulli implements ProbabilityDistribution {
        private final double p;
        private final Random random;

        Bernoulli(double p, long seed) {
            Validation.probability(p);
            this.p = p;
            this.random = new Random(seed);
        }

        double pmf(int x) {
            if (x != 0 && x != 1) return 0.0;
            return x == 1 ? p : 1.0 - p;
        }

        @Override
        public DistributionType type() {
            return DistributionType.BERNOULLI;
        }

        @Override
        public double mean() {
            return p;
        }

        @Override
        public double variance() {
            return p * (1.0 - p);
        }

        @Override
        public double cdf(double x) {
            if (x < 0) return 0;
            if (x < 1) return 1.0 - p;
            return 1.0;
        }

        @Override
        public double sample() {
            return random.nextDouble() < p ? 1.0 : 0.0;
        }
    }

    static final class Binomial implements ProbabilityDistribution {
        private final int n;
        private final double p;
        private final Random random;

        Binomial(int n, double p, long seed) {
            Validation.count(n, 100000);
            Validation.probability(p);

            this.n = n;
            this.p = p;
            this.random = new Random(seed);
        }

        double pmf(int k) {
            if (k < 0 || k > n) return 0.0;

            if (p == 0.0) return k == 0 ? 1.0 : 0.0;
            if (p == 1.0) return k == n ? 1.0 : 0.0;

            return Math.exp(
                    logCombination(n, k)
                            + k * Math.log(p)
                            + (n - k) * Math.log1p(-p)
            );
        }

        @Override
        public DistributionType type() {
            return DistributionType.BINOMIAL;
        }

        @Override
        public double mean() {
            return n * p;
        }

        @Override
        public double variance() {
            return n * p * (1.0 - p);
        }

        @Override
        public double cdf(double x) {
            if (x < 0) return 0;
            if (x >= n) return 1;

            double result = 0.0;

            for (int k = 0; k <= Math.floor(x); k++) {
                result += pmf(k);
            }

            return Math.min(1.0, result);
        }

        @Override
        public double sample() {
            int successes = 0;

            for (int i = 0; i < n; i++) {
                if (random.nextDouble() < p) {
                    successes++;
                }
            }

            return successes;
        }
    }

    static final class Geometric implements ProbabilityDistribution {
        private final double p;
        private final Random random;

        Geometric(double p, long seed) {
            Validation.probability(p);

            if (p == 0.0) {
                throw new DistributionException(
                        "Geometric probability must be greater than zero."
                );
            }

            this.p = p;
            this.random = new Random(seed);
        }

        double pmf(int k) {
            if (k < 1) return 0.0;
            if (p == 1.0) return k == 1 ? 1.0 : 0.0;

            return Math.exp(
                    Math.log(p)
                            + (k - 1) * Math.log1p(-p)
            );
        }

        @Override
        public DistributionType type() {
            return DistributionType.GEOMETRIC;
        }

        @Override
        public double mean() {
            return 1.0 / p;
        }

        @Override
        public double variance() {
            return (1.0 - p) / (p * p);
        }

        @Override
        public double cdf(double x) {
            if (x < 1) return 0;
            if (p == 1.0) return 1;

            return -Math.expm1(
                    Math.floor(x) * Math.log1p(-p)
            );
        }

        @Override
        public double sample() {
            if (p == 1.0) return 1.0;

            return Math.floor(
                    Math.log1p(-random.nextDouble())
                            / Math.log1p(-p)
            ) + 1.0;
        }
    }

    static final class Poisson implements ProbabilityDistribution {
        private final double lambda;
        private final Random random;

        Poisson(double lambda, long seed) {
            Validation.finite(lambda, "Poisson rate");

            if (lambda < 0 || lambda > 100000) {
                throw new DistributionException(
                        "Poisson rate must be between 0 and 100000."
                );
            }

            this.lambda = lambda;
            this.random = new Random(seed);
        }

        double pmf(int k) {
            if (k < 0) return 0;
            if (lambda == 0) return k == 0 ? 1 : 0;

            return Math.exp(
                    -lambda
                            + k * Math.log(lambda)
                            - logFactorial(k)
            );
        }

        @Override
        public DistributionType type() {
            return DistributionType.POISSON;
        }

        @Override
        public double mean() {
            return lambda;
        }

        @Override
        public double variance() {
            return lambda;
        }

        @Override
        public double cdf(double x) {
            if (x < 0) return 0;
            if (lambda == 0) return 1;

            if (x > lambda + 1000 * Math.sqrt(lambda + 1) + 1000) {
                return 1.0;
            }

            double total = 0;

            for (int k = 0; k <= Math.floor(x); k++) {
                total += pmf(k);
            }

            return Math.min(1.0, total);
        }

        @Override
        public double sample() {
            if (lambda == 0) return 0;

            // Knuth's exact algorithm for moderate rates.
            if (lambda >= 30) {
                throw new DistributionException(
                        "This implementation restricts Poisson sampling "
                                + "to rates below 30."
                );
            }

            double threshold = Math.exp(-lambda);
            double product = 1.0;
            int count = 0;

            do {
                product *= random.nextDouble();
                count++;
            } while (product > threshold);

            return count - 1.0;
        }
    }

    static final class Uniform implements ProbabilityDistribution {
        private final double a;
        private final double b;
        private final Random random;

        Uniform(double a, double b, long seed) {
            Validation.finite(a, "Lower bound");
            Validation.finite(b, "Upper bound");

            if (a >= b) {
                throw new DistributionException(
                        "Uniform distribution requires a < b."
                );
            }

            this.a = a;
            this.b = b;
            this.random = new Random(seed);
        }

        double pdf(double x) {
            return x >= a && x <= b ? 1.0 / (b - a) : 0.0;
        }

        @Override
        public DistributionType type() {
            return DistributionType.UNIFORM;
        }

        @Override
        public double mean() {
            return (a + b) / 2.0;
        }

        @Override
        public double variance() {
            return (b - a) * (b - a) / 12.0;
        }

        @Override
        public double cdf(double x) {
            if (x <= a) return 0;
            if (x >= b) return 1;

            return (x - a) / (b - a);
        }

        @Override
        public double sample() {
            return a + random.nextDouble() * (b - a);
        }
    }

    static final class Normal implements ProbabilityDistribution {
        private final double mu;
        private final double sigma;
        private final Random random;

        Normal(double mu, double sigma, long seed) {
            Validation.finite(mu, "Normal mean");
            Validation.positive(sigma, "Normal standard deviation");

            this.mu = mu;
            this.sigma = sigma;
            this.random = new Random(seed);
        }

        double pdf(double x) {
            double z = (x - mu) / sigma;

            return Math.exp(-0.5 * z * z)
                    / (sigma * SQRT_TWO_PI);
        }

        @Override
        public DistributionType type() {
            return DistributionType.NORMAL;
        }

        @Override
        public double mean() {
            return mu;
        }

        @Override
        public double variance() {
            return sigma * sigma;
        }

        @Override
        public double cdf(double x) {
            return 0.5 * (1.0 + erf(
                    (x - mu) / (sigma * Math.sqrt(2.0))
            ));
        }

        @Override
        public double sample() {
            return mu + sigma * random.nextGaussian();
        }

        double standardize(double x) {
            return (x - mu) / sigma;
        }

        double intervalProbability(double lower, double upper) {
            if (lower > upper) {
                throw new DistributionException(
                        "Lower bound cannot exceed upper bound."
                );
            }

            return cdf(upper) - cdf(lower);
        }
    }

    static final class Exponential implements ProbabilityDistribution {
        private final double lambda;
        private final Random random;

        Exponential(double lambda, long seed) {
            Validation.positive(lambda, "Exponential rate");

            this.lambda = lambda;
            this.random = new Random(seed);
        }

        double pdf(double x) {
            return x < 0 ? 0 : lambda * Math.exp(-lambda * x);
        }

        @Override
        public DistributionType type() {
            return DistributionType.EXPONENTIAL;
        }

        @Override
        public double mean() {
            return 1.0 / lambda;
        }

        @Override
        public double variance() {
            return 1.0 / (lambda * lambda);
        }

        @Override
        public double cdf(double x) {
            return x < 0 ? 0 : -Math.expm1(-lambda * x);
        }

        double survival(double x) {
            return x < 0 ? 1.0 : Math.exp(-lambda * x);
        }

        @Override
        public double sample() {
            return -Math.log(
                    Math.max(random.nextDouble(), Double.MIN_VALUE)
            ) / lambda;
        }
    }

    /*
     * Lanczos approximation for the error function.
     * Used to evaluate the normal CDF without dependencies.
     */
    static double erf(double x) {
        double sign = x < 0 ? -1.0 : 1.0;
        double value = Math.abs(x);

        double t = 1.0 / (1.0 + 0.3275911 * value);

        double polynomial =
                (((((1.061405429 * t - 1.453152027) * t)
                        + 1.421413741) * t
                        - 0.284496736) * t
                        + 0.254829592) * t;

        return sign * (
                1.0 - polynomial * Math.exp(-value * value)
        );
    }

    static final class SimulationService {
        private final SimulationPolicy policy;

        SimulationService(SimulationPolicy policy) {
            this.policy = policy;
        }

        SimulationResult simulate(
                ProbabilityDistribution distribution,
                int count
        ) {
            policy.validate(count);

            long start = System.nanoTime();

            List<Double> values = new ArrayList<>(count);

            for (int i = 0; i < count; i++) {
                double value = distribution.sample();

                if (policy.requireFiniteResults()
                        && !Double.isFinite(value)) {
                    throw new DistributionException(
                            "Non-finite simulation result detected."
                    );
                }

                values.add(value);
            }

            double mean = values.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElseThrow();

            double variance = values.stream()
                    .mapToDouble(value -> Math.pow(value - mean, 2))
                    .average()
                    .orElseThrow();

            double minimum = Collections.min(values);
            double maximum = Collections.max(values);

            long elapsed = TimeUnit.NANOSECONDS.toMillis(
                    System.nanoTime() - start
            );

            return new SimulationResult(
                    distribution.type(),
                    count,
                    distribution.mean(),
                    mean,
                    distribution.variance(),
                    variance,
                    minimum,
                    maximum,
                    elapsed
            );
        }
    }

    static final class EnterpriseSimulationService {
        private final ExecutorService executor;
        private final SimulationService service;

        EnterpriseSimulationService(
                int workerCount,
                SimulationPolicy policy
        ) {
            if (workerCount < 1 || workerCount > 32) {
                throw new DistributionException(
                        "Worker count must be between 1 and 32."
                );
            }

            this.executor = Executors.newFixedThreadPool(workerCount);
            this.service = new SimulationService(policy);
        }

        CompletableFuture<SimulationResult> submit(
                ProbabilityDistribution distribution,
                int sampleCount
        ) {
            return CompletableFuture.supplyAsync(
                    () -> service.simulate(distribution, sampleCount),
                    executor
            );
        }

        void shutdown() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    static void validateCalculations() {
        Bernoulli bernoulli = new Bernoulli(0.3, 1);

        if (Math.abs(
                bernoulli.pmf(0) + bernoulli.pmf(1) - 1
        ) > 1e-10) {
            throw new AssertionError("Bernoulli normalization failed.");
        }

        Binomial binomial = new Binomial(10, 0.5, 2);
        double total = 0;

        for (int k = 0; k <= 10; k++) {
            total += binomial.pmf(k);
        }

        if (Math.abs(total - 1.0) > 1e-10) {
            throw new AssertionError("Binomial normalization failed.");
        }

        Normal normal = new Normal(0, 1, 3);

        if (Math.abs(normal.cdf(0) - 0.5) > 1e-6) {
            throw new AssertionError("Normal CDF failed.");
        }

        Exponential exponential = new Exponential(2, 4);

        if (Math.abs(exponential.mean() - 0.5) > 1e-10) {
            throw new AssertionError("Exponential mean failed.");
        }

        Poisson poisson = new Poisson(0, 5);

        if (poisson.pmf(0) != 1.0) {
            throw new AssertionError("Poisson boundary failed.");
        }

        System.out.println("All calculation assertions passed.");
    }

    public static void main(String[] args) {
        SimulationPolicy policy = new SimulationPolicy(
                1,
                100000,
                true
        );

        EnterpriseSimulationService service =
                new EnterpriseSimulationService(4, policy);

        List<ProbabilityDistribution> distributions = List.of(
                new Bernoulli(0.4, 101),
                new Binomial(20, 0.4, 102),
                new Geometric(0.2, 103),
                new Poisson(5.0, 104),
                new Uniform(10.0, 20.0, 105),
                new Normal(50.0, 10.0, 106),
                new Exponential(0.5, 107)
        );

        System.out.println("PROBABILITY DISTRIBUTIONS");
        System.out.println("=========================");

        Binomial binomial = new Binomial(10, 0.3, 11);
        Normal normal = new Normal(100, 15, 12);
        Exponential exponential = new Exponential(0.5, 13);

        System.out.println("Binomial P(X=3): " + binomial.pmf(3));
        System.out.println("Binomial P(X<=3): " + binomial.cdf(3));

        System.out.println("Normal P(X<=115): " + normal.cdf(115));
        System.out.println(
                "Normal P(85<=X<=115): "
                        + normal.intervalProbability(85, 115)
        );

        System.out.println(
                "Exponential P(X>2): " + exponential.survival(2)
        );

        try {
            List<CompletableFuture<SimulationResult>> tasks =
                    new ArrayList<>();

            for (ProbabilityDistribution distribution : distributions) {
                tasks.add(service.submit(distribution, 10000));
            }

            CompletableFuture.allOf(
                    tasks.toArray(new CompletableFuture[0])
            ).join();

            System.out.println("\nCONCURRENT SIMULATION RESULTS");
            System.out.println("=============================");

            for (CompletableFuture<SimulationResult> task : tasks) {
                SimulationResult result = task.join();

                System.out.printf(
                        "%s | theoretical mean: %.6f | empirical mean: %.6f"
                                + " | theoretical variance: %.6f"
                                + " | empirical variance: %.6f"
                                + " | min: %.6f | max: %.6f | time: %d ms%n",
                        result.type(),
                        result.theoreticalMean(),
                        result.empiricalMean(),
                        result.theoreticalVariance(),
                        result.empiricalVariance(),
                        result.minimum(),
                        result.maximum(),
                        result.executionTimeMillis()
                );
            }

            validateCalculations();

        } catch (Exception exception) {
            System.err.println(
                    "Simulation service failed: " + exception.getMessage()
            );

            throw exception;

        } finally {
            service.shutdown();
        }
    }
}
