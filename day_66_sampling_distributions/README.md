# Sampling Distributions

## 1. Domain Overview

Sampling distributions form the statistical foundation of estimation, hypothesis testing, confidence intervals, and inferential statistics.

A population contains all observations relevant to a statistical investigation. A sample is a subset selected from that population.

Instead of examining only one sample, statistical inference considers the possible results obtained from repeatedly drawing samples of the same size using the same sampling procedure.

The resulting probability distribution of a statistic is called its **sampling distribution**.

This project implements four connected statistical mechanisms:

1. Sampling distributions of the sample mean.
2. Standard error and its relationship with sample size.
3. Central Limit Theorem.
4. Law of Large Numbers.

The implementations use customer transaction values as a common analytical scenario.

## 2. Fundamental Statistical Concepts

### 2.1 Population

A population is the complete collection of observations under investigation.

For example, a financial institution may maintain transaction amounts for 1,000 customers.

Let the population be:

\[
X=\{x_1,x_2,\ldots,x_N\}
\]

Where:

- \(N\) is the population size.
- \(x_i\) represents an individual observation.

The population mean is:

\[
\mu=\frac{1}{N}\sum_{i=1}^{N}x_i
\]

Population variance is:

\[
\sigma^2=
\frac{1}{N}\sum_{i=1}^{N}(x_i-\mu)^2
\]

Population standard deviation is:

\[
\sigma=\sqrt{\sigma^2}
\]

The population parameters describe the complete dataset.

### 2.2 Sample

A sample contains selected observations from the population.

For a sample of size \(n\):

\[
\bar X=\frac{1}{n}\sum_{i=1}^{n}X_i
\]

The sample mean estimates the population mean.

Sample variance is:

\[
s^2=
\frac{1}{n-1}
\sum_{i=1}^{n}(X_i-\bar X)^2
\]

The denominator \(n-1\) applies to the conventional unbiased sample variance estimator.

The distinction between population and sample variance is important:

| Property | Population | Sample |
|---|---|---|
| Size | \(N\) | \(n\) |
| Mean | \(\mu\) | \(\bar X\) |
| Variance | \(\sigma^2\) | \(s^2\) |
| Standard deviation | \(\sigma\) | \(s\) |
| Variance denominator | \(N\) | \(n-1\) |

### 2.3 Sampling Distribution

A sampling distribution describes the probability distribution of a statistic calculated from repeated samples.

For example, suppose 1,000 independent samples are drawn from a customer transaction population. Each sample contains 30 transactions.

Calculate the mean of each sample:

\[
\bar X_1,\bar X_2,\ldots,\bar X_{1000}
\]

These 1,000 means form an empirical approximation of the sampling distribution of the sample mean.

The sampling distribution is different from the distribution of individual population observations.

| Distribution | Represents |
|---|---|
| Population distribution | Individual population observations |
| Sample distribution | Individual observations in one selected sample |
| Sampling distribution | A statistic calculated across repeated samples |

This distinction is central to statistical inference.

## 3. Sampling Mean

The sample mean is a statistic used to estimate the population mean.

For independent observations with a common population mean:

\[
E(\bar X)=\mu
\]

This means that the sample mean is an unbiased estimator of the population mean under the stated sampling assumptions.

For repeated samples, the average of their sample means approaches the population mean.

The sample mean changes between samples because different observations may be selected.

### Example

Consider the population:

\[
X=\{10,20,30,40,50\}
\]

Its population mean is:

\[
\mu=\frac{10+20+30+40+50}{5}=30
\]

Consider three samples:

| Sample | Observations | Sample mean |
|---|---|---:|
| A | 10, 20, 30 | 20 |
| B | 20, 30, 50 | 33.33 |
| C | 30, 40, 50 | 40 |

Each sample produces a different estimate.

The distribution of these estimates represents the sampling distribution of the sample mean when all possible samples are considered.

### Implementation

- Python implements sample statistics using `statistics`.
- JavaScript implements statistical operations through a dedicated `Statistics` class.
- C++17 separates sample calculation from population management.
- Java 17 uses immutable statistical records.
- PostgreSQL stores individual observations and calculated sample means.

## 4. Standard Error

Standard error measures the variability of a statistic across repeated samples.

For the sample mean under independent sampling with replacement:

\[
SE(\bar X)=\frac{\sigma}{\sqrt n}
\]

Where:

- \(\sigma\) is population standard deviation.
- \(n\) is sample size.

Standard error is not the same as standard deviation.

Standard deviation describes the variability of individual observations.

Standard error describes the variability of an estimator across repeated samples.

### 4.1 Effect of Sample Size

The standard error decreases as sample size increases.

| Sample size | Standard error |
|---:|---:|
| 1 | \(\sigma\) |
| 4 | \(\sigma/2\) |
| 16 | \(\sigma/4\) |
| 25 | \(\sigma/5\) |
| 100 | \(\sigma/10\) |

Increasing sample size by a factor of four reduces standard error by a factor of two.

This relationship is important in survey design, quality assurance, market research, and experimental planning.

### 4.2 Finite Population Correction

When sampling without replacement from a finite population, observations are not independent.

The standard error becomes:

\[
SE(\bar X)=
\frac{\sigma}{\sqrt n}
\sqrt{\frac{N-n}{N-1}}
\]

The second term is the finite population correction factor.

\[
FPC=\sqrt{\frac{N-n}{N-1}}
\]

Where:

- \(N\) is population size.
- \(n\) is sample size.

The correction accounts for the reduction in uncertainty when a substantial proportion of a finite population is observed.

Important cases:

- When \(n\) is small relative to \(N\), the correction is close to one.
- When \(n=N\), the correction is zero.
- When the entire population is observed, there is no sampling uncertainty.

The Python, JavaScript, C++, Java, and PostgreSQL implementations distinguish sampling with replacement from sampling without replacement.

## 5. Central Limit Theorem

The Central Limit Theorem (CLT) explains why sampling distributions of sample means often become approximately normal as sample size increases.

For independent and identically distributed observations with finite mean and finite variance:

\[
\frac{\bar X-\mu}{\sigma/\sqrt n}
\xrightarrow{d}N(0,1)
\]

Equivalently, for sufficiently large sample sizes:

\[
\bar X\approx N\left(
\mu,\frac{\sigma^2}{n}
\right)
\]

The original population does not need to follow a normal distribution.

The approximation concerns the distribution of sample means, not necessarily the distribution of individual observations.

### 5.1 CLT Mechanism

The implementations use a deliberately skewed transaction population:

| Transaction value | Frequency |
|---:|---:|
| 5 | 500 |
| 15 | 250 |
| 30 | 150 |
| 100 | 100 |
| **Total** | **1,000** |

This population contains a substantial concentration of low transaction values and a smaller group of high transaction values.

Its distribution is not normal.

Repeatedly sampling from this population produces sample means.

The experiments examine sample sizes:

\[
n\in\{2,5,10,30,50,100\}
\]

For each sample size, the implementations compare:

- Empirical sampling mean.
- Theoretical population mean.
- Theoretical standard error.
- Empirical standard error.
- Estimation bias.

As sample size increases, the empirical distribution of sample means is expected to become more nearly normal under the CLT assumptions.

### 5.2 Conditions and Limitations

The CLT is not an unconditional guarantee for every sampling design.

Important considerations include:

- Observations should be independent or satisfy suitable dependence conditions.
- The population should have finite variance for the classical version.
- Sample sizes required for a useful approximation depend on population characteristics.
- Highly skewed populations or extreme outliers may require larger samples.
- Sampling without replacement from a finite population requires consideration of its sampling design.

A sample size of 30 is not a universal guarantee of normality.

The appropriate sample size depends on the population distribution and the required approximation accuracy.

## 6. Law of Large Numbers

The Law of Large Numbers (LLN) explains the convergence of sample averages toward the population mean as the sample size increases.

For independent and identically distributed observations with a finite expected value:

\[
\bar X_n\xrightarrow{P}\mu
\]

The strong law provides the stronger almost-sure convergence result under its assumptions:

\[
\bar X_n\xrightarrow{a.s.}\mu
\]

The law explains why larger representative samples generally provide more stable estimates.

### 6.1 Practical Demonstration

The implementations examine sample sizes:

\[
n\in\{10,50,100,500,1000,5000\}
\]

For each sample, the sample mean is calculated.

Absolute estimation error is:

\[
Error=|\bar X-\mu|
\]

The experiment tracks the difference between the sample mean and population mean.

Larger samples generally reduce the variability of the sample mean, although a particular sequence of sampled means does not have to move monotonically toward the population mean.

### 6.2 LLN Versus CLT

These concepts answer different statistical questions.

| Property | Law of Large Numbers | Central Limit Theorem |
|---|---|---|
| Primary question | Does the sample mean converge to the population mean? | What is the approximate distribution of the sample mean? |
| Main focus | Convergence | Distribution |
| Output | Convergence toward \(\mu\) | Approximate normal distribution |
| Practical use | Estimation consistency | Statistical inference |
| Main relationship | Increasing sample size stabilizes estimates | Increasing sample size often improves normal approximation |

The LLN describes convergence of the estimator.

The CLT describes the distribution of its estimation error after appropriate scaling.

## 7. Confidence Intervals

A confidence interval provides an interval estimate for an unknown population parameter.

Using the normal approximation:

\[
CI=\bar X\pm z_{\alpha/2}SE
\]

For commonly used confidence levels:

| Confidence level | Critical value |
|---|---:|
| 90% | 1.645 |
| 95% | 1.960 |
| 99% | 2.576 |

For a 95% confidence interval:

\[
CI=\bar X\pm1.96SE
\]

The implementations provide confidence interval calculations using these critical values.

### Interpretation

A 95% confidence procedure produces intervals that contain the true population parameter in approximately 95% of repeated applications when the assumptions hold.

It does not mean that a particular calculated interval has a 95% probability of containing a fixed population mean.

### Limitations

The normal approximation requires appropriate statistical assumptions.

When population variance is unknown and sample sizes are small, a Student's t-distribution may be more appropriate.

The included implementations use normal critical values for educational comparison and should not automatically be treated as a complete production inference package.

## 8. Sampling With and Without Replacement

Two different sampling mechanisms are implemented.

### 8.1 Sampling With Replacement

After an observation is selected, it remains eligible for subsequent selection.

The same population observation can appear multiple times.

Properties:

- Repeated selections are possible.
- Draws are independent under the usual random sampling design.
- The standard error follows \(\sigma/\sqrt n\).
- The same observation may contribute more than once to a sample.

### 8.2 Sampling Without Replacement

Once an observation is selected, it is excluded from subsequent selections in that sample.

Properties:

- Duplicate population records cannot appear in one sample.
- Draws are dependent.
- Sample size cannot exceed population size.
- Finite population correction applies.

### Comparison

| Feature | With replacement | Without replacement |
|---|---|---|
| Repeated records | Possible | Not possible |
| Independent draws | Yes, under random selection | No |
| Sample size limit | No population-size limit | At most \(N\) |
| Finite population correction | Not required | Required |
| Common application | Bootstrap sampling | Surveys and finite-population audits |

## 9. Python Implementation

The Python program provides a complete statistical simulation workflow.

### Architecture

| Component | Responsibility |
|---|---|
| `SamplingMethod` | Defines sampling mechanisms |
| `SamplingError` | Handles invalid sampling operations |
| `PopulationStatistics` | Stores population parameters |
| `SamplingResult` | Stores simulation results |
| `ConfidenceInterval` | Stores interval estimates |
| `SamplingDistribution` | Manages sampling and statistical calculations |

### Main mechanisms

**Population validation**

The constructor rejects empty populations, non-numeric observations, and non-finite values.

**Population statistics**

The implementation calculates population mean, variance, and standard deviation using the population variance denominator.

**Sample generation**

`draw_sample()` supports both replacement policies using Python's standard-library random functionality.

**Standard error**

`theoretical_standard_error()` calculates theoretical standard error and applies finite population correction when required.

**CLT experiments**

`central_limit_theorem()` executes multiple simulation experiments for different sample sizes.

**LLN experiments**

`law_of_large_numbers()` examines sample means and their absolute estimation errors.

**Export**

`export_results()` writes statistical results to a JSON file in the current working directory.

### Performance

For a population of size \(N\), sample size \(n\), and \(R\) repetitions:

- Sampling with replacement requires approximately \(O(Rn)\) selection operations.
- Sampling without replacement uses population-sized index preparation and partial selection.
- The simulation retains sample means for each repetition in the CLT implementation.
- Statistical calculations avoid unnecessary external dependencies.

The program is suitable for reproducible educational experiments and small-to-medium simulations.

## 10. JavaScript Implementation

The JavaScript implementation uses an event-driven architecture and asynchronous simulation execution.

### Architecture

| Component | Responsibility |
|---|---|
| `RandomGenerator` | Seeded pseudo-random number generation |
| `Statistics` | Statistical calculations |
| `Population` | Population validation and sample generation |
| `SamplingExperiment` | Event-driven simulation management |
| `SamplingMethod` | Sampling policy constants |
| `confidenceInterval()` | Confidence interval calculation |

### Event-driven workflow

The experiment service extends Node.js `EventEmitter`.

It publishes:

- `experimentStarted`
- `experimentProgress`
- `experimentCompleted`
- `experimentFailed`

This separates statistical processing from experiment monitoring.

A monitoring component can subscribe to progress events without changing the statistical calculation.

### Asynchronous execution

The simulation processes observations in batches.

Between batches, `setImmediate()` yields control to the Node.js event loop.

This improves responsiveness during long-running simulations.

The simulation does not automatically become CPU-parallel through asynchronous execution. Intensive statistical workloads may require worker threads or a distributed processing architecture.

### Memory optimization

The experiment service calculates the mean and variance of sample means using running aggregates.

It does not need to store every simulated sample mean.

This reduces the memory requirement compared with retaining the entire sampling distribution.

The implementation also uses immutable population observations and a private class field to protect population state.

## 11. C++17 Implementation

The C++ implementation focuses on computational efficiency and controlled memory usage.

### Architecture

| Component | Responsibility |
|---|---|
| `SamplingMethod` | Sampling strategy |
| `PopulationStatistics` | Population parameters |
| `SamplingResult` | Simulation output |
| `SamplingEngine` | Sampling and inference calculations |

### Statistical mechanisms

The program uses `std::mt19937_64` for reproducible pseudo-random sampling.

`uniform_int_distribution` selects observations for sampling with replacement.

Sampling without replacement uses partial Fisher-Yates selection.

This avoids sorting the entire population for each sample.

### Online variance calculation

The simulation uses Welford's algorithm.

For each new sample mean \(x_i\):

\[
\delta=x_i-\bar x_{i-1}
\]

\[
\bar x_i=\bar x_{i-1}+\frac{\delta}{i}
\]

\[
M_{2,i}=M_{2,i-1}+\delta(x_i-\bar x_i)
\]

The final empirical variance is:

\[
s^2=\frac{M_2}{R-1}
\]

Where \(R\) is the number of simulation repetitions.

This approach avoids retaining the complete collection of sample means and is numerically more stable than calculating variance directly from large sums of squared values.

### Complexity

| Operation | Approximate complexity |
|---|---|
| Population statistics | \(O(N)\) |
| Sample with replacement | \(O(n)\) |
| Sample without replacement | \(O(N+n)\) |
| One simulation repetition | Depends on sampling method |
| Online simulation aggregation | \(O(1)\) additional memory |

The implementation validates population values, sample sizes, and repetition counts before execution.

## 12. Java 17 Implementation

The Java implementation models a statistical analytics service using explicit domain types and enterprise-oriented execution controls.

### Architecture

| Component | Responsibility |
|---|---|
| `Population` | Immutable population management |
| `PopulationStatistics` | Population statistical record |
| `SampleStatistics` | Sample statistical record |
| `SamplingPolicy` | Experiment validation |
| `ExperimentRequest` | Experiment configuration |
| `ExperimentService` | Statistical processing |
| `ExperimentManager` | Asynchronous execution |
| `SamplingResult` | Experiment output |
| `ConfidenceInterval` | Interval estimation |

### Domain modeling

Java records represent immutable statistical data.

For example, `SamplingResult` contains:

- Experiment identifier.
- Sample size.
- Repetition count.
- Sampling method.
- Sampling mean.
- Population mean.
- Theoretical standard error.
- Empirical standard error.
- Bias.
- Minimum and maximum sample means.

The population uses `List.copyOf()` to prevent external modification of its observations.

### Policy validation

`SamplingPolicy` controls:

- Minimum sample size.
- Minimum simulation repetitions.
- Whether sampling with replacement is permitted.
- Whether the sample size is valid for the selected method.

Separating validation from statistical execution makes the design easier to maintain.

### Asynchronous execution

`ExperimentManager` uses an `ExecutorService` and `CompletableFuture`.

Independent experiments can be submitted without blocking the calling thread.

The service synchronizes access to its shared random generator to avoid unsafe concurrent random-state modification.

For higher-throughput production systems, independent experiment-specific random generators and carefully managed task allocation would provide better concurrency.

### Failure handling

The implementation rejects:

- Empty populations.
- Invalid observations.
- Missing sampling methods.
- Invalid sample sizes.
- Insufficient repetitions.
- Unsupported confidence levels.
- Invalid policy configurations.

Executor shutdown includes timeout handling and interruption restoration.

## 13. PostgreSQL Implementation

The PostgreSQL implementation models sampling experiments as a relational workflow.

### 13.1 Database Structure

The database uses the `sampling_lab` schema.

| Table | Purpose |
|---|---|
| `populations` | Population definitions |
| `population_observations` | Individual population records |
| `sampling_experiments` | Experiment configuration and status |
| `sampling_draws` | Calculated sample means |
| `sample_observations` | Individual selected observations |
| `experiment_results` | Final statistical results |

### 13.2 Relationships

The principal relationships are:

- One population contains many observations.
- One population can have multiple experiments.
- One experiment produces multiple sampling draws.
- One sampling draw contains multiple selected observations.
- One completed experiment produces one final result record.

Relationship diagram:

    populations
        |
        | 1:N
        |
    population_observations

    populations
        |
        | 1:N
        |
    sampling_experiments
        |
        | 1:N
        |
    sampling_draws
        |
        | 1:N
        |
    sample_observations

    sampling_experiments
        |
        | 1:1
        |
    experiment_results

### 13.3 Population Statistics View

`population_statistics` calculates:

- Population size.
- Population mean.
- Population variance.
- Population standard deviation.
- Minimum observation.
- Maximum observation.

The view centralizes population-level calculations.

### 13.4 Sampling Functions

`calculate_sample_mean()` calculates the mean of a supplied numeric array.

`calculate_standard_error()` applies the appropriate theoretical formula according to the sampling method.

`create_sampling_experiment()` registers an experiment and returns its identifier.

`execute_sampling_experiment()`:

1. Locks the selected experiment.
2. Validates its current state.
3. Retrieves population parameters.
4. Changes the experiment status to `RUNNING`.
5. Generates repeated samples.
6. Calculates sample statistics.
7. Stores individual sample observations.
8. Calculates empirical sampling statistics.
9. Stores the final experiment result.
10. Marks the experiment as `COMPLETED`.

The workflow is executed transactionally.

A failed operation raises an exception, allowing the surrounding transaction to roll back instead of leaving partially completed experiment records.

### 13.5 Constraints and Integrity

The schema uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Positive sample-size constraints.
- Repetition-count validation.
- Experiment status constraints.
- Sampling method enumeration.
- Indexes for population and experiment retrieval.

The experiment validation trigger checks whether a sample is valid for the selected population and sampling method.

### 13.6 Reporting

The SQL script includes reporting operations for:

- Population statistics.
- Sampling distribution results.
- Empirical versus theoretical standard errors.
- Law of Large Numbers experiments.
- Finite population correction.
- Confidence intervals.
- Individual sample observation audits.
- Experiment eligibility.
- Experiment status aggregation.

These queries demonstrate how statistical computation and relational data management can work together.

### 13.7 Database Performance

Indexes support common filtering and joining operations.

The most relevant indexes cover:

- Population identifiers.
- Experiment identifiers.
- Experiment status.
- Repetition numbers.
- Observation retrieval.

The individual observation audit table increases storage requirements because it retains selected observations.

For large-scale workloads, retaining only aggregate results or archiving detailed sample records may be more economical.

The SQL implementation uses PostgreSQL's pseudo-random `RANDOM()` function for educational simulations. It is not a cryptographically secure random source.

Its `SETSEED()` operation provides session-level reproducibility, not a general guarantee of identical results across different PostgreSQL versions or execution environments.

## 14. Statistical Validation and Testing

The five implementations include validation for important statistical and computational conditions.

| Validation | Expected behavior |
|---|---|
| Empty population | Reject |
| Non-finite population observation | Reject |
| Zero sample size | Reject |
| Negative sample size | Reject |
| Insufficient repetitions | Reject |
| Sample exceeds population without replacement | Reject |
| Duplicate population record in a sample without replacement | Prevent |
| Negative standard error | Reject |
| Unsupported confidence level | Reject |
| Valid sampling configuration | Execute |

The test populations use known values so that the expected statistics can be independently verified.

For the population:

\[
X=\{10,20,30,40,50\}
\]

Expected results:

| Statistic | Value |
|---|---:|
| Population size | 5 |
| Population mean | 30 |
| Population variance | 200 |
| Population standard deviation | 14.1421 |
| Standard error for \(n=4\), with replacement | 7.0711 |

These values provide reference checks for the implementations.

## 15. Practical Applications

Sampling distributions are useful in several operational and analytical settings.

### Financial services

- Estimating average transaction values.
- Monitoring customer spending patterns.
- Auditing financial transactions.
- Estimating average processing costs.
- Comparing financial product performance.

### Business analytics

- Estimating average customer satisfaction.
- Evaluating average purchase amounts.
- Measuring campaign conversion rates.
- Comparing operational performance.
- Estimating average delivery times.

### Quality control

- Measuring manufacturing defect rates.
- Estimating average production times.
- Monitoring service-level performance.
- Evaluating process variability.

### Research and experimentation

- Estimating population parameters.
- Designing experiments.
- Calculating confidence intervals.
- Evaluating sampling uncertainty.
- Supporting hypothesis-testing procedures.

## 16. Limitations and Production Considerations

The implementations are educational statistical systems, not complete statistical inference platforms.

Important limitations include:

1. **Sampling assumptions:** The theoretical standard error formulas require the corresponding sampling design assumptions.

2. **Randomness:** Seeded pseudo-random generators provide reproducibility for controlled simulations but are not cryptographically secure.

3. **Normal approximation:** The CLT does not guarantee that every finite-sample distribution is normal.

4. **Confidence intervals:** The included normal critical values do not replace Student's t-distribution methods when those are required.

5. **Sampling bias:** Random sampling cannot correct an incorrectly defined or incomplete population.

6. **Outliers:** Extreme values can substantially affect sample means and standard errors.

7. **Finite population:** The finite population correction assumes an appropriate simple random sampling design without replacement.

8. **SQL scalability:** Retaining every selected observation can generate substantial database storage and write overhead.

9. **Concurrency:** Reproducible concurrent simulations require independent random streams and explicit experiment-state management.

10. **Numerical precision:** Floating-point and database numeric calculations may produce small differences between implementations.

11. **Missing data:** The examples use complete numerical populations. Real datasets require explicit missing-value and data-quality policies.

12. **Statistical independence:** Repeated observations from the same customer, account, or operational unit may be correlated. Such data may require cluster-aware or other specialized sampling methods.

## 17. Implementation Comparison

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Population statistics | Yes | Yes | Yes | Yes | Yes |
| Sample generation | Yes | Yes | Yes | Yes | Yes |
| Sampling with replacement | Yes | Yes | Yes | Yes | Yes |
| Sampling without replacement | Yes | Yes | Yes | Yes | Yes |
| Standard error | Yes | Yes | Yes | Yes | Yes |
| Finite population correction | Yes | Yes | Yes | Yes | Yes |
| CLT simulation | Yes | Yes | Yes | Yes | Yes |
| LLN experiment | Yes | Yes | Yes | Yes | Yes |
| Confidence intervals | Yes | Yes | Yes | Yes | Yes |
| Asynchronous execution | No | Yes | No | Yes | Transactional |
| Persistent experiment records | JSON | JSON | No | No | Yes |
| Event-driven monitoring | No | Yes | No | No | No |
| Relational integrity | No | No | No | No | Yes |

## 18. Execution Requirements

| Deliverable | Requirement | Execution |
|---|---|---|
| Python | Python 3.10+ | `python sampling_distributions.py` |
| JavaScript | Node.js 18+ | `node sampling_distributions.js` |
| C++17 | C++17 compiler | `g++ -std=c++17 -O2 sampling_distributions.cpp -o sampling_distributions` |
| Java | Java 17 | `javac SamplingDistributions.java` followed by `java SamplingDistributions` |
| PostgreSQL | PostgreSQL 15+ | Execute the SQL script using `psql` |

The Python and JavaScript implementations create `sampling_results.json` in the current working directory.

The C++ and Java programs display simulation results in the terminal.

The PostgreSQL implementation stores experiment configurations, sample observations, and statistical results in relational tables.

## 19. Core Statistical Relationships

The main relationships implemented throughout the project are:

**Population mean**

\[
\mu=E[X]
\]

**Sample mean**

\[
\bar X=\frac{1}{n}\sum_{i=1}^{n}X_i
\]

**Population variance**

\[
\sigma^2=E[(X-\mu)^2]
\]

**Standard error**

\[
SE(\bar X)=\frac{\sigma}{\sqrt n}
\]

**Finite population correction**

\[
FPC=\sqrt{\frac{N-n}{N-1}}
\]

**Standard error without replacement**

\[
SE(\bar X)=
\frac{\sigma}{\sqrt n}FPC
\]

**Central Limit Theorem**

\[
\frac{\bar X-\mu}{\sigma/\sqrt n}
\xrightarrow{d}N(0,1)
\]

**Law of Large Numbers**

\[
\bar X_n\xrightarrow{P}\mu
\]

These equations describe the statistical mechanisms implemented across the five source files. Together, they establish the relationship between population characteristics, sample estimates, sampling variability, and statistical inference.
