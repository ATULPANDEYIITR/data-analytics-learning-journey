"""
Probability Distributions
=========================

Implementations:
- Bernoulli
- Binomial
- Geometric
- Poisson
- Uniform
- Normal
- Exponential

Includes probability mass functions, probability density functions,
cumulative distribution functions, random sampling, statistical
properties, validation, simulation, and numerical edge-case handling.

Python standard library only.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence


class DistributionType(Enum):
    BERNOULLI = "bernoulli"
    BINOMIAL = "binomial"
    GEOMETRIC = "geometric"
    POISSON = "poisson"
    UNIFORM = "uniform"
    NORMAL = "normal"
    EXPONENTIAL = "exponential"


class DistributionError(ValueError):
    """Raised when distribution parameters or operations are invalid."""


def validate_probability(p: float) -> None:
    if not math.isfinite(p) or not 0.0 <= p <= 1.0:
        raise DistributionError("Probability must be between 0 and 1.")


def validate_positive(value: float, name: str) -> None:
    if not math.isfinite(value) or value <= 0:
        raise DistributionError(f"{name} must be finite and positive.")


def validate_count(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DistributionError(f"{name} must be a non-negative integer.")


def log_combination(n: int, k: int) -> float:
    if k < 0 or k > n:
        return -math.inf
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    )


@dataclass(frozen=True)
class DistributionStatistics:
    mean: float
    variance: float
    standard_deviation: float


class Distribution:
    """Base class defining the distribution interface."""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def mean(self) -> float:
        raise NotImplementedError

    def variance(self) -> float:
        raise NotImplementedError

    def sample(self) -> float:
        raise NotImplementedError

    def cdf(self, x: float) -> float:
        raise NotImplementedError

    def statistics(self) -> DistributionStatistics:
        variance = self.variance()
        return DistributionStatistics(
            mean=self.mean(),
            variance=variance,
            standard_deviation=math.sqrt(variance),
        )

    def sample_many(self, size: int) -> list[float]:
        validate_count(size, "Sample size")
        return [self.sample() for _ in range(size)]

    def empirical_statistics(self, size: int) -> dict[str, float]:
        values = self.sample_many(size)

        if not values:
            raise DistributionError("At least one sample is required.")

        return {
            "sample_size": float(size),
            "sample_mean": statistics.fmean(values),
            "sample_variance": statistics.pvariance(values),
            "minimum": min(values),
            "maximum": max(values),
        }


class BernoulliDistribution(Distribution):
    """One trial with success probability p."""

    def __init__(self, p: float, seed: int | None = None):
        super().__init__(seed)
        validate_probability(p)
        self.p = p

    def pmf(self, x: int) -> float:
        if x not in (0, 1):
            return 0.0
        return self.p if x == 1 else 1.0 - self.p

    def cdf(self, x: float) -> float:
        if x < 0:
            return 0.0
        if x < 1:
            return 1.0 - self.p
        return 1.0

    def mean(self) -> float:
        return self.p

    def variance(self) -> float:
        return self.p * (1.0 - self.p)

    def sample(self) -> float:
        return float(self.rng.random() < self.p)


class BinomialDistribution(Distribution):
    """Number of successes in n independent Bernoulli trials."""

    def __init__(self, n: int, p: float, seed: int | None = None):
        super().__init__(seed)
        validate_count(n, "Number of trials")
        validate_probability(p)
        self.n = n
        self.p = p

    def pmf(self, k: int) -> float:
        if isinstance(k, bool) or not isinstance(k, int):
            return 0.0

        if k < 0 or k > self.n:
            return 0.0

        if self.p == 0:
            return float(k == 0)

        if self.p == 1:
            return float(k == self.n)

        log_probability = (
            log_combination(self.n, k)
            + k * math.log(self.p)
            + (self.n - k) * math.log1p(-self.p)
        )

        return math.exp(log_probability)

    def cdf(self, x: float) -> float:
        if x < 0:
            return 0.0

        if x >= self.n:
            return 1.0

        upper = math.floor(x)
        result = math.fsum(self.pmf(k) for k in range(upper + 1))
        return min(1.0, result)

    def mean(self) -> float:
        return self.n * self.p

    def variance(self) -> float:
        return self.n * self.p * (1.0 - self.p)

    def sample(self) -> float:
        return float(sum(self.rng.random() < self.p for _ in range(self.n)))


class GeometricDistribution(Distribution):
    """
    Number of independent trials until the first success.

    Support: 1, 2, 3, ...
    """

    def __init__(self, p: float, seed: int | None = None):
        super().__init__(seed)
        validate_probability(p)

        if p == 0:
            raise DistributionError(
                "Geometric distribution requires p greater than zero."
            )

        self.p = p

    def pmf(self, k: int) -> float:
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            return 0.0

        if self.p == 1:
            return float(k == 1)

        return math.exp(
            math.log(self.p) + (k - 1) * math.log1p(-self.p)
        )

    def cdf(self, x: float) -> float:
        if x < 1:
            return 0.0

        if self.p == 1:
            return 1.0

        k = math.floor(x)
        return -math.expm1(k * math.log1p(-self.p))

    def mean(self) -> float:
        return 1.0 / self.p

    def variance(self) -> float:
        return (1.0 - self.p) / (self.p * self.p)

    def sample(self) -> float:
        if self.p == 1:
            return 1.0

        u = self.rng.random()
        return float(math.floor(math.log1p(-u) / math.log1p(-self.p)) + 1)


class PoissonDistribution(Distribution):
    """Number of independent events occurring in a fixed interval."""

    def __init__(self, rate: float, seed: int | None = None):
        super().__init__(seed)

        if not math.isfinite(rate) or rate < 0:
            raise DistributionError("Poisson rate must be finite and non-negative.")

        self.rate = rate

    def pmf(self, k: int) -> float:
        if isinstance(k, bool) or not isinstance(k, int) or k < 0:
            return 0.0

        if self.rate == 0:
            return float(k == 0)

        log_probability = (
            -self.rate
            + k * math.log(self.rate)
            - math.lgamma(k + 1)
        )

        return math.exp(log_probability)

    def cdf(self, x: float) -> float:
        if x < 0:
            return 0.0

        if self.rate == 0:
            return 1.0

        k = math.floor(x)

        if k > self.rate + 1000 * math.sqrt(self.rate + 1) + 1000:
            return 1.0

        return min(1.0, math.fsum(self.pmf(i) for i in range(k + 1)))

    def mean(self) -> float:
        return self.rate

    def variance(self) -> float:
        return self.rate

    def sample(self) -> float:
        if self.rate == 0:
            return 0.0

        # Knuth's exact Poisson sampling algorithm.
        if self.rate < 30:
            threshold = math.exp(-self.rate)
            product = 1.0
            count = 0

            while product > threshold:
                product *= self.rng.random()
                count += 1

            return float(count - 1)

        # Exact rejection sampling using transformed rejection.
        # PTRS method, suitable for large Poisson rates.
        sqrt_rate = math.sqrt(self.rate)
        b = 0.931 + 2.53 * sqrt_rate
        a = -0.059 + 0.02483 * b
        inverse_alpha = 1.1239 + 1.1328 / (b - 3.4)
        v_r = 0.9277 - 3.6224 / (b - 2)

        while True:
            u = self.rng.random() - 0.5
            v = self.rng.random()
            us = 0.5 - abs(u)

            if us <= 0:
                continue

            k = math.floor((2 * a / us + b) * u + self.rate + 0.43)

            if us >= 0.07 and v <= v_r and k >= 0:
                return float(k)

            if k < 0 or (us < 0.013 and v > us):
                continue

            lhs = math.log(
                v * inverse_alpha / (a / (us * us) + b)
            )

            rhs = (
                -self.rate
                + k * math.log(self.rate)
                - math.lgamma(k + 1)
            )

            if lhs <= rhs:
                return float(k)


class UniformDistribution(Distribution):
    """Continuous uniform distribution on [a, b]."""

    def __init__(
        self,
        a: float,
        b: float,
        seed: int | None = None
    ):
        super().__init__(seed)

        if not math.isfinite(a) or not math.isfinite(b) or a >= b:
            raise DistributionError("Uniform distribution requires finite a < b.")

        self.a = a
        self.b = b

    def pdf(self, x: float) -> float:
        return 1.0 / (self.b - self.a) if self.a <= x <= self.b else 0.0

    def cdf(self, x: float) -> float:
        if x <= self.a:
            return 0.0
        if x >= self.b:
            return 1.0
        return (x - self.a) / (self.b - self.a)

    def mean(self) -> float:
        return (self.a + self.b) / 2.0

    def variance(self) -> float:
        return (self.b - self.a) ** 2 / 12.0

    def sample(self) -> float:
        return self.rng.uniform(self.a, self.b)


class NormalDistribution(Distribution):
    """Continuous Gaussian distribution with mean mu and deviation sigma."""

    def __init__(
        self,
        mu: float,
        sigma: float,
        seed: int | None = None
    ):
        super().__init__(seed)

        if not math.isfinite(mu):
            raise DistributionError("Normal mean must be finite.")

        validate_positive(sigma, "Standard deviation")

        self.mu = mu
        self.sigma = sigma

    def pdf(self, x: float) -> float:
        z = (x - self.mu) / self.sigma

        return (
            math.exp(-0.5 * z * z)
            / (self.sigma * math.sqrt(2.0 * math.pi))
        )

    def cdf(self, x: float) -> float:
        z = (x - self.mu) / (self.sigma * math.sqrt(2.0))
        return 0.5 * math.erfc(-z)

    def mean(self) -> float:
        return self.mu

    def variance(self) -> float:
        return self.sigma * self.sigma

    def sample(self) -> float:
        return self.rng.gauss(self.mu, self.sigma)

    def standardize(self, x: float) -> float:
        return (x - self.mu) / self.sigma

    def interval_probability(self, lower: float, upper: float) -> float:
        if lower > upper:
            raise DistributionError("Lower bound cannot exceed upper bound.")

        return self.cdf(upper) - self.cdf(lower)


class ExponentialDistribution(Distribution):
    """Continuous waiting-time distribution with rate lambda."""

    def __init__(self, rate: float, seed: int | None = None):
        super().__init__(seed)
        validate_positive(rate, "Exponential rate")
        self.rate = rate

    def pdf(self, x: float) -> float:
        if x < 0:
            return 0.0

        return self.rate * math.exp(-self.rate * x)

    def cdf(self, x: float) -> float:
        if x < 0:
            return 0.0

        return -math.expm1(-self.rate * x)

    def survival_probability(self, x: float) -> float:
        if x < 0:
            return 1.0

        return math.exp(-self.rate * x)

    def mean(self) -> float:
        return 1.0 / self.rate

    def variance(self) -> float:
        return 1.0 / (self.rate * self.rate)

    def sample(self) -> float:
        return self.rng.expovariate(self.rate)


def run_distribution(
    name: str,
    distribution: Distribution,
    sample_size: int = 10000
) -> None:
    theoretical = distribution.statistics()
    empirical = distribution.empirical_statistics(sample_size)

    print(f"\n{name}")
    print("-" * 55)
    print(f"Theoretical mean:     {theoretical.mean:.6f}")
    print(f"Empirical mean:       {empirical['sample_mean']:.6f}")
    print(f"Theoretical variance: {theoretical.variance:.6f}")
    print(f"Empirical variance:   {empirical['sample_variance']:.6f}")
    print(f"Minimum:              {empirical['minimum']:.6f}")
    print(f"Maximum:              {empirical['maximum']:.6f}")


def demonstrate_probability_calculations() -> None:
    print("\nPROBABILITY DISTRIBUTION CALCULATIONS")
    print("=" * 60)

    bernoulli = BernoulliDistribution(0.7, seed=42)
    print("\nBernoulli P(X=1):", bernoulli.pmf(1))

    binomial = BinomialDistribution(10, 0.3, seed=42)
    print("Binomial P(X=3):", binomial.pmf(3))
    print("Binomial P(X<=3):", binomial.cdf(3))

    geometric = GeometricDistribution(0.25, seed=42)
    print("Geometric P(X=4):", geometric.pmf(4))
    print("Geometric P(X<=4):", geometric.cdf(4))

    poisson = PoissonDistribution(4.0, seed=42)
    print("Poisson P(X=2):", poisson.pmf(2))
    print("Poisson P(X<=5):", poisson.cdf(5))

    uniform = UniformDistribution(0, 10, seed=42)
    print("Uniform PDF at 5:", uniform.pdf(5))
    print("Uniform P(X<=4):", uniform.cdf(4))

    normal = NormalDistribution(100, 15, seed=42)
    print("Normal PDF at 100:", normal.pdf(100))
    print("Normal P(X<=115):", normal.cdf(115))
    print("Normal P(85<=X<=115):", normal.interval_probability(85, 115))

    exponential = ExponentialDistribution(0.5, seed=42)
    print("Exponential PDF at 2:", exponential.pdf(2))
    print("Exponential P(X<=2):", exponential.cdf(2))
    print("Exponential survival at 2:", exponential.survival_probability(2))


def demonstrate_simulations() -> None:
    print("\nMONTE CARLO SIMULATION")
    print("=" * 60)

    distributions: list[tuple[str, Distribution]] = [
        ("Bernoulli", BernoulliDistribution(0.4, seed=101)),
        ("Binomial", BinomialDistribution(20, 0.4, seed=102)),
        ("Geometric", GeometricDistribution(0.2, seed=103)),
        ("Poisson", PoissonDistribution(5.0, seed=104)),
        ("Uniform", UniformDistribution(10, 20, seed=105)),
        ("Normal", NormalDistribution(50, 10, seed=106)),
        ("Exponential", ExponentialDistribution(0.5, seed=107)),
    ]

    for name, distribution in distributions:
        run_distribution(name, distribution, 10000)


def demonstrate_edge_cases() -> None:
    print("\nEDGE CASES")
    print("=" * 60)

    certain_success = BernoulliDistribution(1.0)
    certain_failure = BernoulliDistribution(0.0)

    print("Bernoulli p=1:", certain_success.sample())
    print("Bernoulli p=0:", certain_failure.sample())

    print("Binomial n=0:", BinomialDistribution(0, 0.5).pmf(0))
    print("Poisson lambda=0:", PoissonDistribution(0).pmf(0))
    print("Geometric p=1:", GeometricDistribution(1).sample())

    try:
        NormalDistribution(0, 0)
    except DistributionError as error:
        print("Expected validation error:", error)

    try:
        GeometricDistribution(0)
    except DistributionError as error:
        print("Expected validation error:", error)


def run_assertions() -> None:
    """Verify normalization, boundaries, and theoretical properties."""

    assert math.isclose(
        BernoulliDistribution(0.3).pmf(0)
        + BernoulliDistribution(0.3).pmf(1),
        1.0
    )

    assert math.isclose(
        math.fsum(BinomialDistribution(8, 0.4).pmf(k) for k in range(9)),
        1.0,
        abs_tol=1e-10
    )

    assert math.isclose(
        math.fsum(GeometricDistribution(0.5).pmf(k) for k in range(1, 100)),
        1.0,
        abs_tol=1e-10
    )

    assert math.isclose(
        math.fsum(PoissonDistribution(3).pmf(k) for k in range(100)),
        1.0,
        abs_tol=1e-10
    )

    assert math.isclose(
        UniformDistribution(0, 10).mean(),
        5.0
    )

    assert math.isclose(
        NormalDistribution(0, 1).cdf(0),
        0.5
    )

    assert math.isclose(
        ExponentialDistribution(2).mean(),
        0.5
    )

    assert math.isclose(
        ExponentialDistribution(2).survival_probability(3),
        math.exp(-6)
    )

    print("\nAll probability distribution assertions passed.")


def main() -> None:
    demonstrate_probability_calculations()
    demonstrate_simulations()
    demonstrate_edge_cases()
    run_assertions()


if __name__ == "__main__":
    main()
