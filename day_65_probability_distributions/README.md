# Probability Distributions

## 1. Introduction

Probability distributions describe how probabilities are assigned to possible outcomes of a random variable.

A random variable represents a numerical outcome of a random process. Its probability distribution provides the mathematical relationship between possible values and their likelihood.

The seven distributions implemented in this project are:

| Distribution | Type | Main parameter | Typical application |
|---|---|---|---|
| Bernoulli | Discrete | \(p\) | Success or failure |
| Binomial | Discrete | \(n,p\) | Number of successes in fixed trials |
| Geometric | Discrete | \(p\) | Trials until first success |
| Poisson | Discrete | \(\lambda\) | Events within a fixed interval |
| Uniform | Continuous | \(a,b\) | Equally likely values within an interval |
| Normal | Continuous | \(\mu,\sigma\) | Measurement variation |
| Exponential | Continuous | \(\lambda\) | Waiting time between events |

The project implements probability calculations, statistical properties, random sampling, Monte Carlo simulations, parameter validation, and structured statistical reporting across five programming and database environments.

## 2. Fundamental Probability Concepts

### 2.1 Random variables

A random variable assigns a numerical value to an outcome of a random experiment.

Two major categories are used.

**Discrete random variable**

A discrete random variable has a finite or countably infinite set of possible values.

Examples:

- Number of defective products.
- Number of customer arrivals.
- Number of attempts before success.
- Whether a transaction succeeds.

**Continuous random variable**

A continuous random variable can take any value within a specified interval or continuous domain.

Examples:

- Processing time.
- Temperature.
- Measurement error.
- Waiting time.

### 2.2 Probability mass function

A probability mass function (PMF) applies to discrete random variables.

\[
P(X=x)=f(x)
\]

Its fundamental properties are:

\[
f(x)\geq 0
\]

\[
\sum_x f(x)=1
\]

The PMF gives the probability of an exact discrete outcome.

Bernoulli, Binomial, Geometric, and Poisson distributions use PMFs.

### 2.3 Probability density function

A probability density function (PDF) applies to continuous random variables.

\[
f(x)\geq 0
\]

\[
\int_{-\infty}^{\infty}f(x)\,dx=1
\]

For a continuous random variable:

\[
P(X=x)=0
\]

The probability of an interval is calculated through integration:

\[
P(a\leq X\leq b)
=
\int_a^b f(x)\,dx
\]

Uniform, Normal, and Exponential distributions use PDFs.

### 2.4 Cumulative distribution function

The cumulative distribution function (CDF) represents the probability that a random variable does not exceed a particular value.

\[
F(x)=P(X\leq x)
\]

For discrete distributions:

\[
F(x)=\sum_{k\leq x}P(X=k)
\]

For continuous distributions:

\[
F(x)=\int_{-\infty}^{x}f(t)\,dt
\]

Important properties:

- Its values are between zero and one.
- It is non-decreasing.
- Its limit approaches zero as \(x\) approaches negative infinity.
- Its limit approaches one as \(x\) approaches positive infinity.

### 2.5 Expected value

Expected value represents the theoretical long-run average of a random variable.

For a discrete distribution:

\[
E[X]=\sum_x xP(X=x)
\]

For a continuous distribution:

\[
E[X]=\int_{-\infty}^{\infty}xf(x)\,dx
\]

### 2.6 Variance and standard deviation

Variance measures the spread of a distribution around its expected value.

\[
Var(X)=E[(X-\mu)^2]
\]

An equivalent expression is:

\[
Var(X)=E[X^2]-E[X]^2
\]

Standard deviation is:

\[
\sigma=\sqrt{Var(X)}
\]

The implementations distinguish theoretical variance from variance calculated using simulated observations.

## 3. Bernoulli Distribution

### 3.1 Definition

The Bernoulli distribution models a single experiment with two possible outcomes:

- Success: 1
- Failure: 0

The probability of success is \(p\), and the probability of failure is \(1-p\).

\[
X\sim Bernoulli(p)
\]

### 3.2 Probability mass function

\[
P(X=x)=
\begin{cases}
p & x=1\\
1-p & x=0\\
0 & \text{otherwise}
\end{cases}
\]

### 3.3 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(p\) |
| Variance | \(p(1-p)\) |
| Standard deviation | \(\sqrt{p(1-p)}\) |

### 3.4 Example

Consider a payment transaction with a 0.95 probability of success.

\[
P(X=1)=0.95
\]

\[
P(X=0)=0.05
\]

Expected value:

\[
E[X]=0.95
\]

Variance:

\[
Var(X)=0.95(0.05)=0.0475
\]

### 3.5 Implementation

- Python: `BernoulliDistribution`
- JavaScript: `Bernoulli`
- C++17: `Bernoulli`
- Java 17: `Bernoulli`
- PostgreSQL: `probability_mass()`

The implementations validate the probability range and handle the boundary cases \(p=0\) and \(p=1\).

## 4. Binomial Distribution

### 4.1 Definition

The Binomial distribution calculates the number of successes in a fixed number of independent Bernoulli trials.

Its assumptions are:

1. The number of trials is fixed.
2. Each trial has two possible outcomes.
3. Trials are independent.
4. The success probability remains constant.

\[
X\sim Binomial(n,p)
\]

Where:

- \(n\): Number of trials.
- \(p\): Probability of success.
- \(1-p\): Probability of failure.
- \(k\): Number of successes.

### 4.2 Probability mass function

\[
P(X=k)=
\binom{n}{k}p^k(1-p)^{n-k}
\]

The binomial coefficient is:

\[
\binom{n}{k}=\frac{n!}{k!(n-k)!}
\]

### 4.3 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(np\) |
| Variance | \(np(1-p)\) |
| Standard deviation | \(\sqrt{np(1-p)}\) |

### 4.4 Example

A quality inspection system tests 10 independent products. Each product has a 0.3 probability of being defective.

The probability of exactly three defective products is:

\[
P(X=3)=
\binom{10}{3}(0.3)^3(0.7)^7
\]

\[
P(X=3)\approx 0.266827932
\]

Expected number of defective products:

\[
E[X]=10(0.3)=3
\]

Variance:

\[
Var(X)=10(0.3)(0.7)=2.1
\]

### 4.5 Implementation considerations

The implementations use logarithmic factorial calculations to reduce numerical overflow.

Instead of directly calculating large factorials:

\[
\ln P(X=k)
=
\ln\binom{n}{k}
+k\ln p
+(n-k)\ln(1-p)
\]

The probability is recovered using the exponential function.

Boundary conditions include:

- \(n=0\).
- \(p=0\).
- \(p=1\).
- \(k<0\).
- \(k>n\).

## 5. Geometric Distribution

### 5.1 Definition

The Geometric distribution models the number of independent trials required to obtain the first success.

The implementation uses the convention that the first successful trial is counted.

\[
X\sim Geometric(p)
\]

Possible values:

\[
X\in\{1,2,3,\ldots\}
\]

### 5.2 Probability mass function

\[
P(X=k)=(1-p)^{k-1}p
\]

The first \(k-1\) trials must fail, and the \(k\)-th trial must succeed.

### 5.3 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(\frac{1}{p}\) |
| Variance | \(\frac{1-p}{p^2}\) |
| Standard deviation | \(\frac{\sqrt{1-p}}{p}\) |

### 5.4 Example

A network operation succeeds independently with probability 0.25 per attempt.

The probability that its first success occurs on the fourth attempt is:

\[
P(X=4)=(0.75)^3(0.25)
\]

\[
P(X=4)=0.10546875
\]

Expected attempts:

\[
E[X]=\frac{1}{0.25}=4
\]

### 5.5 Memoryless property

The Geometric distribution has the memoryless property:

\[
P(X>s+t\mid X>s)=P(X>t)
\]

Previous failures do not change the probability structure of future independent attempts.

### 5.6 Implementation considerations

The implementations use inverse-transform sampling or equivalent random sampling methods.

The parameter restriction is:

\[
0<p\leq 1
\]

A value of \(p=0\) is rejected because success never occurs and the expected number of trials is infinite.

## 6. Poisson Distribution

### 6.1 Definition

The Poisson distribution models the number of events occurring within a fixed interval of time, distance, area, or another measurable quantity.

\[
X\sim Poisson(\lambda)
\]

Where \(\lambda\) is the expected event count within the interval.

Typical applications:

- Network incidents per hour.
- Customer arrivals per minute.
- System failures per day.
- Requests received by a service.
- Defects per production batch under an appropriate event-count model.

### 6.2 Probability mass function

\[
P(X=k)=\frac{e^{-\lambda}\lambda^k}{k!}
\]

Where:

\[
k=0,1,2,\ldots
\]

### 6.3 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(\lambda\) |
| Variance | \(\lambda\) |
| Standard deviation | \(\sqrt{\lambda}\) |

An important property is that the theoretical mean and variance are equal.

### 6.4 Example

A security monitoring system observes an average of four incidents per hour.

\[
\lambda=4
\]

The probability of exactly two incidents is:

\[
P(X=2)=\frac{e^{-4}4^2}{2!}
\]

\[
P(X=2)\approx 0.146525112
\]

Expected incidents:

\[
E[X]=4
\]

Variance:

\[
Var(X)=4
\]

### 6.5 Sampling methods

Poisson sampling can use:

- Knuth's algorithm for moderate event rates.
- Transformed rejection algorithms for large event rates.
- Standard-library Poisson random generators.

The Python implementation uses Knuth's method for rates below 30 and a transformed-rejection method for larger rates.

The JavaScript and Java implementations deliberately restrict Knuth sampling to moderate rates instead of silently using a potentially expensive algorithm for large rates.

The C++ implementation uses `std::poisson_distribution`.

The SQL implementation focuses on probability calculations and statistical reporting.

## 7. Uniform Distribution

### 7.1 Definition

The continuous Uniform distribution represents a random variable whose density is constant throughout an interval.

\[
X\sim Uniform(a,b)
\]

Where:

- \(a\): Lower boundary.
- \(b\): Upper boundary.
- \(a<b\).

### 7.2 Probability density function

\[
f(x)=
\begin{cases}
\frac{1}{b-a} & a\leq x\leq b\\
0 & \text{otherwise}
\end{cases}
\]

Although the density is constant, the probability of a specific point is zero.

### 7.3 Cumulative distribution function

\[
F(x)=
\begin{cases}
0 & x\leq a\\
\frac{x-a}{b-a} & a<x<b\\
1 & x\geq b
\end{cases}
\]

### 7.4 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(\frac{a+b}{2}\) |
| Variance | \(\frac{(b-a)^2}{12}\) |
| Standard deviation | \(\frac{b-a}{\sqrt{12}}\) |

### 7.5 Example

A processing duration is modeled as uniformly distributed between 10 and 20 minutes.

\[
X\sim Uniform(10,20)
\]

The probability density is:

\[
f(x)=\frac{1}{20-10}=0.1
\]

Probability that processing takes no more than 14 minutes:

\[
P(X\leq14)=\frac{14-10}{20-10}
\]

\[
P(X\leq14)=0.4
\]

Expected processing duration:

\[
E[X]=15
\]

### 7.6 Implementation considerations

All implementations enforce:

\[
a<b
\]

The random sampler generates values within the configured interval.

The probability density is zero outside the interval.

## 8. Normal Distribution

### 8.1 Definition

The Normal distribution is a continuous, symmetric, bell-shaped probability distribution.

\[
X\sim N(\mu,\sigma^2)
\]

Where:

- \(\mu\): Mean.
- \(\sigma\): Standard deviation.
- \(\sigma^2\): Variance.

The mean, median, and mode are equal.

### 8.2 Probability density function

\[
f(x)=
\frac{1}{\sigma\sqrt{2\pi}}
e^{-\frac{(x-\mu)^2}{2\sigma^2}}
\]

### 8.3 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(\mu\) |
| Variance | \(\sigma^2\) |
| Standard deviation | \(\sigma\) |
| Skewness | 0 |
| Excess kurtosis | 0 |

### 8.4 Standard Normal Distribution

A Normal random variable can be standardized using:

\[
Z=\frac{X-\mu}{\sigma}
\]

The standard Normal distribution is:

\[
Z\sim N(0,1)
\]

This transformation allows observations from different Normal distributions to be compared on a common scale.

### 8.5 Empirical coverage

For a Normal distribution:

| Interval | Approximate probability |
|---|---:|
| \(\mu\pm\sigma\) | 68.27% |
| \(\mu\pm2\sigma\) | 95.45% |
| \(\mu\pm3\sigma\) | 99.73% |

These are theoretical coverage probabilities, not guarantees about individual observations.

### 8.6 Example

Suppose a measurement process follows:

\[
X\sim N(100,15^2)
\]

The standardized value for 115 is:

\[
Z=\frac{115-100}{15}=1
\]

Therefore:

\[
P(X\leq115)=\Phi(1)\approx0.841345
\]

The probability of an observation between 85 and 115 is:

\[
P(85\leq X\leq115)
=
\Phi(1)-\Phi(-1)
\]

\[
P(85\leq X\leq115)\approx0.682689
\]

### 8.7 Numerical implementation

The Normal CDF depends on the error function:

\[
\Phi(z)=
\frac{1}{2}
\left[
1+\operatorname{erf}
\left(\frac{z}{\sqrt{2}}\right)
\right]
\]

Implementation approaches:

- Python uses `math.erfc`.
- JavaScript uses an error-function approximation.
- C++17 uses `std::erfc`.
- Java uses an error-function approximation.
- PostgreSQL uses its mathematical `ERF` function.

Approximation accuracy differs between implementations and should be considered when comparing very small tail probabilities.

Normal sampling uses Gaussian random-number generators or the Box-Muller transformation.

## 9. Exponential Distribution

### 9.1 Definition

The Exponential distribution models the waiting time between events in a homogeneous Poisson process.

\[
X\sim Exponential(\lambda)
\]

Where \(\lambda\) represents the event rate per unit of time or another measurable interval.

Its support is:

\[
x\geq0
\]

### 9.2 Probability density function

\[
f(x)=
\begin{cases}
\lambda e^{-\lambda x} & x\geq0\\
0 & x<0
\end{cases}
\]

### 9.3 Cumulative distribution function

\[
F(x)=1-e^{-\lambda x}
\]

For negative values:

\[
F(x)=0
\]

### 9.4 Survival function

The survival function measures the probability that waiting time exceeds a specified value.

\[
S(x)=P(X>x)=e^{-\lambda x}
\]

### 9.5 Statistical properties

| Property | Formula |
|---|---|
| Mean | \(\frac{1}{\lambda}\) |
| Variance | \(\frac{1}{\lambda^2}\) |
| Standard deviation | \(\frac{1}{\lambda}\) |

### 9.6 Example

A service receives an average of 0.5 requests per minute.

\[
\lambda=0.5
\]

The probability that the next request arrives within two minutes is:

\[
P(X\leq2)=1-e^{-0.5(2)}
\]

\[
P(X\leq2)\approx0.632121
\]

The probability that the waiting time exceeds two minutes is:

\[
P(X>2)=e^{-1}\approx0.367879
\]

### 9.7 Memoryless property

The Exponential distribution satisfies:

\[
P(X>s+t\mid X>s)=P(X>t)
\]

The remaining waiting time has the same distribution regardless of how long the process has already waited.

This property is useful in queueing and reliability models, although real-world service times and equipment lifetimes do not always satisfy the assumption.

## 10. Comparison of the Seven Distributions

| Characteristic | Bernoulli | Binomial | Geometric | Poisson | Uniform | Normal | Exponential |
|---|---|---|---|---|---|---|---|
| Variable type | Discrete | Discrete | Discrete | Discrete | Continuous | Continuous | Continuous |
| Main purpose | Binary outcome | Success count | First success | Event count | Equal density | Symmetric variation | Waiting time |
| Support | 0, 1 | 0 to n | 1 onward | 0 onward | [a,b] | All real values | Non-negative values |
| Parameters | p | n, p | p | lambda | a, b | mu, sigma | lambda |
| Mean | p | np | 1/p | lambda | (a+b)/2 | mu | 1/lambda |
| Variance | p(1-p) | np(1-p) | (1-p)/p² | lambda | (b-a)²/12 | sigma² | 1/lambda² |
| PMF/PDF | PMF | PMF | PMF | PMF | PDF | PDF | PDF |

### 10.1 Important distinctions

**Bernoulli versus Binomial**

Bernoulli represents one trial. Binomial represents the total successes across multiple independent trials.

**Binomial versus Poisson**

Binomial requires a fixed number of trials. Poisson models an event count over a specified interval.

A Poisson approximation to a Binomial distribution may be appropriate when the number of trials is large, the success probability is small, and \(np\) remains moderate.

**Geometric versus Exponential**

Geometric models discrete trial counts. Exponential models continuous waiting times.

**Uniform versus Normal**

Uniform has constant density within its interval. Normal has a symmetric bell-shaped density.

**Poisson versus Exponential**

Poisson models how many events occur within an interval. Exponential models the waiting time between successive events in a homogeneous Poisson process.

## 11. Source File Architecture

### 11.1 Python

The Python implementation uses a shared abstract distribution interface and individual classes.

| Component | Responsibility |
|---|---|
| `Distribution` | Shared sampling and statistical interface |
| `BernoulliDistribution` | Binary outcome calculations |
| `BinomialDistribution` | Fixed-trial success calculations |
| `GeometricDistribution` | First-success calculations |
| `PoissonDistribution` | Event-count calculations |
| `UniformDistribution` | Constant-density calculations |
| `NormalDistribution` | Gaussian calculations |
| `ExponentialDistribution` | Waiting-time calculations |
| `DistributionStatistics` | Immutable statistical results |
| `DistributionError` | Parameter validation failures |

Important implementation mechanisms:

- `dataclass` for statistical results.
- `Enum` for distribution identification.
- `math.lgamma` for stable factorial-related calculations.
- `math.erfc` for Normal CDF evaluation.
- `random.Random` for reproducible simulation.
- `math.expm1` and `math.log1p` for numerical stability.
- Assertions for mathematical validation.

The simulation reports theoretical and empirical means and variances.

### 11.2 JavaScript

The JavaScript implementation uses an event-driven simulation architecture.

| Component | Responsibility |
|---|---|
| `RandomGenerator` | Seeded random number generation |
| `Distribution` | Common statistical interface |
| Individual distribution classes | Probability calculations and sampling |
| `SimulationEngine` | Batched Monte Carlo execution |
| `EventEmitter` | Simulation progress notifications |
| `SimulationEngine.results` | Named simulation results |

The simulation engine processes samples in batches and yields execution control using `setImmediate`.

This reduces the time spent blocking the event loop during long-running simulations.

The implementation uses a seeded Mulberry32 generator for reproducibility.

It is not cryptographically secure and must not be used for security-sensitive randomness.

### 11.3 C++17

The C++ implementation models distributions using runtime polymorphism.

The abstract `Distribution` class defines:

- `mean()`
- `variance()`
- `sample()`
- `cdf()`
- `statistics()`
- `sampleMany()`

Each distribution provides its own implementation.

The program uses:

- `std::mt19937_64` for random generation.
- `std::bernoulli_distribution` for Bernoulli sampling.
- `std::binomial_distribution` for Binomial sampling.
- `std::geometric_distribution` for Geometric sampling.
- `std::poisson_distribution` for Poisson sampling.
- `std::uniform_real_distribution` for Uniform sampling.
- `std::normal_distribution` for Normal sampling.
- `std::exponential_distribution` for Exponential sampling.
- `std::lgamma` for logarithmic factorial calculations.
- `std::erfc` for Normal CDF evaluation.

The simulation engine calculates sample statistics using STL containers and algorithms.

### 11.4 Java 17

The Java implementation follows an enterprise service-oriented design.

Its major components are:

| Component | Responsibility |
|---|---|
| `ProbabilityDistribution` | Common distribution interface |
| `DistributionType` | Supported distribution identifiers |
| `Validation` | Centralized parameter validation |
| `Statistics` | Immutable statistical record |
| `SimulationResult` | Immutable simulation report |
| `SimulationPolicy` | Sample-count and result policies |
| `SimulationService` | Individual simulation execution |
| `EnterpriseSimulationService` | Concurrent execution |

The concurrent service uses:

- `ExecutorService`
- `CompletableFuture`
- `List`
- Java records
- Explicit service shutdown

Each simulation returns a structured result containing theoretical statistics, empirical statistics, sample boundaries, and execution time.

The implementation restricts sample sizes and worker counts to prevent unbounded resource consumption.

### 11.5 PostgreSQL

The SQL implementation uses the `probability_lab` schema.

Its relational model separates distribution metadata, experiments, and observations.

**Main tables**

| Table | Purpose |
|---|---|
| `distribution_catalog` | Distribution definitions and parameter metadata |
| `experiments` | Experiment configuration and lifecycle |
| `simulation_observations` | Individual simulated observations |

**Main functions**

| Function | Responsibility |
|---|---|
| `validate_distribution_parameters()` | Validates distribution parameters |
| `log_factorial()` | Computes logarithmic factorial |
| `log_combination()` | Computes logarithmic combinations |
| `probability_mass()` | Calculates discrete probabilities |
| `probability_density()` | Calculates continuous densities |
| `normal_cdf()` | Calculates the Normal CDF |
| `probability_cdf()` | Calculates cumulative probabilities |
| `distribution_statistics()` | Returns theoretical moments |
| `start_experiment()` | Changes an experiment to RUNNING |
| `complete_experiment()` | Validates sample completeness and completes an experiment |

**Database integrity mechanisms**

- Primary keys identify records.
- Foreign keys maintain experiment and distribution relationships.
- Unique constraints prevent duplicate observation numbers.
- Check constraints enforce valid sample counts.
- JSONB stores distribution-specific parameter configurations.
- Triggers validate parameters and observation domains.
- Indexes support experiment retrieval and observation queries.
- Transactions protect multi-step database operations.
- The reporting view combines theoretical and empirical statistics.

The PostgreSQL implementation stores observations rather than implementing a database-side random sampling engine.

## 12. Monte Carlo Simulation

### 12.1 Definition

Monte Carlo simulation uses repeated random sampling to estimate statistical properties or probabilities.

Suppose a random variable has theoretical mean \(\mu\).

For \(N\) simulated observations:

\[
x_1,x_2,\ldots,x_N
\]

The empirical mean is:

\[
\bar{x}=\frac{1}{N}\sum_{i=1}^{N}x_i
\]

The empirical population variance is:

\[
s_N^2=
\frac{1}{N}
\sum_{i=1}^{N}(x_i-\bar{x})^2
\]

As the number of independent observations increases, the sample mean generally approaches the theoretical mean under the assumptions of the law of large numbers.

### 12.2 Simulation workflow

The implementations follow this workflow:

1. Select a distribution.
2. Validate its parameters.
3. Configure a random seed.
4. Generate independent observations.
5. Calculate empirical statistics.
6. Retrieve theoretical statistics.
7. Compare empirical and theoretical results.
8. Report deviations and simulation performance.

### 12.3 Example

Consider a Binomial distribution:

\[
X\sim Binomial(20,0.4)
\]

The theoretical mean is:

\[
E[X]=20(0.4)=8
\]

The theoretical variance is:

\[
Var(X)=20(0.4)(0.6)=4.8
\]

A simulation of 10,000 independent observations should produce empirical statistics reasonably close to these values.

The exact empirical results depend on the random generator and seed.

## 13. Validation and Edge Cases

Correct probability calculations require explicit validation.

| Distribution | Validation rule | Important edge case |
|---|---|---|
| Bernoulli | \(0\leq p\leq1\) | Certain success or failure |
| Binomial | \(n\geq0,\ 0\leq p\leq1\) | Zero trials |
| Geometric | \(0<p\leq1\) | Success on first trial |
| Poisson | \(\lambda\geq0\) | Zero event rate |
| Uniform | \(a<b\) | Values outside support |
| Normal | \(\sigma>0\) | Extreme standardized values |
| Exponential | \(\lambda>0\) | Negative waiting time |

Additional checks include:

- Non-finite numeric parameters.
- Negative sample sizes.
- Empty statistical samples.
- Invalid discrete outcomes.
- Probabilities outside the unit interval.
- Reversed integration or interval boundaries.
- Extremely large event rates.
- Numerical underflow and overflow.

## 14. Numerical Stability

Probability calculations can involve extremely small or large intermediate values.

Direct factorial calculations become problematic as the input grows.

For example:

\[
100!
\]

is extremely large for ordinary floating-point arithmetic.

The implementations use logarithmic transformations:

\[
\ln(n!)=\operatorname{lgamma}(n+1)
\]

This helps calculate Binomial and Poisson probabilities without directly constructing large factorials.

Other stability mechanisms include:

- `log1p(x)` for accurate evaluation of \(\ln(1+x)\).
- `expm1(x)` for accurate evaluation of \(e^x-1\).
- Error-function evaluation for Normal cumulative probabilities.
- Probability bounds to prevent small rounding errors from exceeding one.
- Parameter limits to control computational complexity.

For extreme tail probabilities, ordinary floating-point CDF subtraction may lose precision. Specialized survival functions or logarithmic probability calculations are preferable in high-precision statistical systems.

## 15. Performance Considerations

| Operation | Typical computational cost |
|---|---|
| Bernoulli PMF | O(1) |
| Binomial PMF | O(1) with logarithmic factorial functions |
| Binomial CDF | O(n) in the implemented summation approach |
| Geometric PMF | O(1) |
| Poisson PMF | O(1) after logarithmic factorial evaluation |
| Poisson CDF | O(k) in the implemented summation approach |
| Uniform PDF | O(1) |
| Normal PDF | O(1) |
| Normal CDF | O(1) using a numerical approximation or library function |
| Exponential PDF | O(1) |
| Exponential CDF | O(1) |
| Monte Carlo sampling | O(N) for N observations |

The implemented Binomial and Poisson CDF calculations use direct summation. For very large parameters, production systems should use specialized incomplete beta and incomplete gamma functions or optimized recurrence algorithms.

Simulation memory requirements depend on whether all observations are retained.

Streaming aggregation can reduce memory requirements when only means, variances, and extrema are required.

## 16. Practical Applications

### Quality control

- Bernoulli: Whether a product passes inspection.
- Binomial: Number of defective products in a fixed batch.
- Poisson: Number of defects or incidents in an interval.
- Normal: Variation in manufactured measurements.

### Network and cybersecurity operations

- Bernoulli: Whether an authentication attempt succeeds.
- Binomial: Number of successful requests in a fixed number of attempts.
- Geometric: Attempts until the first successful connection.
- Poisson: Incident arrivals within an observation interval.
- Exponential: Time between independent event arrivals.

### Business and service operations

- Poisson: Customer arrivals.
- Exponential: Inter-arrival times under a homogeneous Poisson process.
- Uniform: Simplified bounded-duration modeling.
- Normal: Measurement and forecasting errors under suitable assumptions.

### Scientific measurement

- Normal: Measurement error and approximately symmetric natural variation.
- Uniform: Bounded uncertainty with constant density.
- Exponential: Waiting-time and lifetime models under a constant hazard assumption.

The suitability of a distribution must be evaluated against the underlying data and assumptions rather than selected solely because its mathematical calculations are convenient.

## 17. Important Statistical Limitations

The implementations provide mathematical distribution models and simulation mechanisms. They do not automatically establish that a selected distribution accurately represents real-world observations.

Important assumptions include:

**Independence**

Binomial and Geometric models require independent trials with constant success probability.

**Constant event rate**

The standard Poisson process assumes a constant event intensity over the modeled interval.

**Poisson process waiting times**

The Exponential waiting-time relationship assumes a homogeneous Poisson process.

**Normality**

A Normal model assumes a symmetric continuous distribution. Real measurements may exhibit skewness, heavy tails, outliers, or multiple modes.

**Uniformity**

A Uniform model assumes constant density throughout the selected interval.

**Randomness**

Reproducible pseudo-random generators are useful for simulations but do not provide cryptographic randomness.

**Parameter estimation**

The project uses supplied parameters. Estimating parameters from real datasets requires separate statistical procedures and validation.

## 18. Security and Production Considerations

- Validate user-supplied parameters before calculations.
- Enforce sample-size limits to prevent excessive computation.
- Avoid accepting untrusted JSON without validation.
- Use parameterized SQL statements when integrating with external applications.
- Restrict database permissions according to application roles.
- Keep experiment configuration separate from recorded observations.
- Use reproducible random seeds for controlled experiments.
- Avoid exposing confidential observations in statistical reports.
- Use cryptographically secure randomness when randomness is security-sensitive.
- Monitor simulation execution time and memory consumption.
- Preserve experiment metadata for reproducibility.
- Distinguish simulated results from actual operational measurements.

## 19. Project Execution

### Python

Requirements:

- Python 3.10 or later.
- Standard library only.

Run the script using:

`python probability_distributions.py`

### JavaScript

Requirements:

- Node.js with modern ECMAScript support.
- No npm dependencies.

Run:

`node probability_distributions.js`

### C++17

Requirements:

- C++17-compatible compiler.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic probability_distributions.cpp -o probability_distributions`

Run:

`./probability_distributions`

On Windows:

`probability_distributions.exe`

### Java 17

Requirements:

- JDK 17.

Compile:

`javac ProbabilityDistributions.java`

Run:

`java ProbabilityDistributions`

### PostgreSQL

Requirements:

- PostgreSQL 14 or later.
- A database account permitted to create schemas, functions, tables, indexes, and triggers.

Execute the SQL script against a dedicated database.

The SQL creates the `probability_lab` schema and its distribution catalog, experiment tables, functions, triggers, indexes, views, and sample configurations.

## 20. Learning Outcomes

The implementations demonstrate:

- The mathematical distinction between discrete and continuous random variables.
- Probability mass functions and probability density functions.
- Cumulative probability calculations.
- Expected values and variance.
- Distribution-specific sampling algorithms.
- The memoryless property.
- Numerical stability in probability calculations.
- Reproducible pseudo-random simulations.
- Monte Carlo statistical estimation.
- Object-oriented distribution modeling.
- Event-driven and concurrent simulation services.
- Relational modeling of statistical experiments.
- Database constraints and validation triggers.
- Comparison of theoretical and empirical statistical properties.

The central distinction across the project is between a probability model, its mathematical calculations, and the empirical results produced by repeated random sampling. These three elements are related, but they are not interchangeable.
