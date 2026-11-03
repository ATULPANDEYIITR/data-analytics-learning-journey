# Probability Fundamentals

This project implements discrete probability concepts across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The central domain is a finite probability space containing outcomes and events. The implementations cover sample spaces, event operations, probability rules, conditional probability, independence, simulation, validation, and probability-based policy evaluation.

## Core Concepts

### Sample Space

A sample space is the complete set of possible outcomes of an experiment.

For a fair six-sided die:

`S = {1, 2, 3, 4, 5, 6}`

Each outcome has probability `1/6`, and the probabilities must satisfy:

`0 <= P(x) <= 1`

and

`Σ P(x) = 1`

The implementations explicitly validate these constraints.

### Events

An event is a subset of the sample space.

For example:

`A = {2, 4, 6}`

represents the event that a die produces an even result.

Events are represented with sets or set-like database relationships so that union, intersection, and complement operations can be evaluated directly.

### Union

The union `A ∪ B` contains outcomes belonging to either event.

The probability is calculated using inclusion-exclusion:

`P(A ∪ B) = P(A) + P(B) - P(A ∩ B)`

The source implementations calculate the intersection explicitly before applying the rule.

### Intersection

The intersection `A ∩ B` contains outcomes common to both events.

For example:

`A = {2, 4, 6}`

`B = {5, 6}`

Therefore:

`A ∩ B = {6}`

and for a fair die:

`P(A ∩ B) = 1/6`

### Complement

The complement of event `A` contains every outcome in the sample space that is not in `A`.

For a fair die:

`A = {2, 4, 6}`

`Aᶜ = {1, 3, 5}`

The complement rule is:

`P(Aᶜ) = 1 - P(A)`

## Conditional Probability

Conditional probability measures the probability of one event when another event is known to have occurred.

The fundamental rule is:

`P(A | B) = P(A ∩ B) / P(B)`

The denominator must be non-zero.

For the die example:

`A = {2, 4, 6}`

`B = {5, 6}`

The intersection is `{6}`.

Therefore:

`P(A | B) = (1/6) / (2/6) = 1/2`

All implementations reject a conditional-probability calculation when the conditioning event has probability zero.

## Independence

Two events are independent when the occurrence of one does not change the probability of the other.

The operational test is:

`P(A ∩ B) = P(A)P(B)`

Independence is different from being mutually exclusive.

Two non-empty mutually exclusive events have:

`P(A ∩ B) = 0`

They cannot generally be independent because their individual probabilities are positive.

The source implementations therefore distinguish:

| Relationship | Condition |
|---|---|
| Independent | `P(A ∩ B) = P(A)P(B)` |
| Disjoint | `A ∩ B = ∅` |
| Overlapping | `A ∩ B ≠ ∅` and independence does not hold |
| Dependent | Joint probability does not equal the product of marginal probabilities |

## Law of Total Probability

When events form a partition of the sample space, a target event can be evaluated through conditional probabilities.

For a partition consisting of `B` and `Bᶜ`:

`P(A) = P(A | B)P(B) + P(A | Bᶜ)P(Bᶜ)`

The Python and JavaScript implementations demonstrate this relationship using die events.

## Bayes' Rule

Bayes' rule reverses conditional probability:

`P(A | B) = P(B | A)P(A) / P(B)`

The Python implementation demonstrates the rule using two production lines with different prior probabilities and defect rates.

The calculation separates:

- prior probability
- conditional likelihood
- total probability of the observed evidence
- posterior probability

This separation is important because observing an event does not automatically imply that its most likely source is the source with the highest conditional rate.

## Binomial Probability

The implementations also include a finite independent-trial model.

For exactly `k` successes in `n` independent trials:

`P(X = k) = C(n,k)p^k(1-p)^(n-k)`

The implementation computes the binomial coefficient without requiring an external numerical library.

For example, with ten trials and success probability `0.2`, the probability of exactly three successes is evaluated directly.

## Python Implementation

The Python source uses a `ProbabilitySpace` dataclass to enforce invariants at object construction.

Important mechanisms include:

- immutable outcome sets
- probability validation
- event validation
- complement calculation
- conditional probability
- independence testing
- event relationship classification
- binomial probability
- Bayes' rule
- failure handling through `ProbabilityError`

The implementation uses Python sets for event operations and mappings for outcome probabilities.

This provides expected average constant-time membership checks and linear-time event probability evaluation relative to the number of outcomes in the event.

The validation examples demonstrate two important failure conditions:

- probabilities that do not sum to one
- conditional probabilities conditioned on an empty or zero-probability event

## JavaScript Implementation

The JavaScript source uses `Map` for probability storage and `Set` for event representation.

It provides a different engineering perspective through an event-driven experiment abstraction.

The `Experiment` class supports:

- event listeners
- trial execution
- generated outcome counts
- completion events
- configurable random sources

This separates probability-domain calculations from execution of repeated experiments.

The implementation also validates the random source and trial count so that invalid simulation state cannot silently produce misleading results.

## C++17 Implementation

The C++ implementation models a probability space with STL containers.

`std::map` stores outcome probabilities, while `std::set` represents events.

The implementation demonstrates:

- domain-specific exceptions
- set algorithms
- explicit validation
- intersection and union operations
- conditional probability
- independence checks
- binomial probability
- deterministic random simulation

A fixed random seed is used for reproducible simulation results.

The design avoids external dependencies and uses standard C++17 facilities only.

## Java 17 Implementation

The Java implementation uses explicit domain types suitable for an enterprise-style probability service.

The `Outcome` record validates individual outcome definitions.

`DiscreteProbabilitySpace` owns the probability model and exposes controlled operations for event evaluation.

The implementation also separates policy evaluation from probability calculation through the `ProbabilityPolicy` interface and `RiskPolicy` implementation.

This demonstrates a useful domain separation:

`Probability Model -> Event Evaluation -> Policy Decision`

The policy layer does not calculate probabilities itself. It consumes an already evaluated probability and determines whether the value satisfies a defined threshold.

Immutable collections are used for externally exposed state where appropriate.

## PostgreSQL Implementation

The PostgreSQL implementation represents the probability domain relationally.

The main relationships are:

`Sample Space -> Outcomes`

`Sample Space -> Events`

`Events -> Event Outcomes`

`Events -> Conditional Observations`

`Policies -> Probability Evaluations`

A many-to-many relationship between events and outcomes is represented by `event_outcomes`.

This allows an event to contain multiple outcomes while an outcome can participate in multiple events.

### Database Integrity

The schema uses:

- primary keys
- foreign keys
- unique constraints
- range checks
- indexes
- triggers
- stored functions

Outcome probabilities are constrained to the interval `[0, 1]`.

A trigger prevents the accumulated probability for a sample space from exceeding one.

The schema does not attempt to enforce every global probability invariant through a row-level constraint because aggregate conditions can require transactional or deferred validation in more complex production models.

### Database Functions

`event_probability` calculates the probability of an event.

`intersection_probability` calculates the probability of two events occurring together.

`conditional_probability` implements:

`P(A | B) = P(A ∩ B) / P(B)`

and explicitly raises an exception when the denominator is zero.

`events_are_independent` evaluates:

`P(A ∩ B) ≈ P(A)P(B)`

using a small numerical tolerance.

### Queries

The SQL script includes examples for:

- outcome retrieval
- event probability reporting
- inclusion-exclusion
- conditional probability
- independence testing
- event aggregation
- policy evaluation
- eligibility reporting
- transactional processing
- execution-plan inspection

The indexes on sample-space and event-outcome relationships support common lookup paths.

## Simulation Versus Exact Probability

Exact probability and empirical simulation answer related but different questions.

Exact calculation derives a value from a mathematical model.

Simulation estimates a probability from repeated observations.

For `N` simulated trials:

`estimated probability = successful trials / N`

As the number of trials increases, empirical estimates generally become more stable, but simulation does not replace validation of the underlying probability model.

The C++ and JavaScript implementations include simulations, while the analytical calculations remain deterministic.

## Edge Cases

The implementations explicitly address several failure conditions.

| Case | Handling |
|---|---|
| Empty sample space | Rejected |
| Probability below zero | Rejected |
| Probability above one | Rejected |
| Probabilities not summing to one | Rejected |
| Unknown event outcome | Rejected |
| Zero-probability condition | Conditional calculation rejected |
| Invalid binomial parameters | Rejected |
| Invalid trial count | Rejected |
| Invalid random source | Rejected in JavaScript |
| Duplicate outcome definitions | Rejected in Java |

These checks prevent invalid probability models from producing plausible-looking but incorrect results.

## Numerical Precision

Probability calculations use floating-point or numeric representations depending on the implementation.

Floating-point equality is not treated as exact when testing independence. A small tolerance is used because arithmetic operations can introduce representation error.

PostgreSQL uses `NUMERIC` values for probability storage and applies an explicit tolerance for independence testing.

The database and application layers therefore make numerical assumptions visible rather than silently treating approximate values as exact.

## Security and Reliability Considerations

Probability calculations themselves do not require external network access or third-party services in these implementations.

Reliability comes primarily from input validation and controlled state.

Important controls include:

- rejecting invalid probabilities
- rejecting unknown outcomes
- preventing division by zero
- validating trial counts
- constraining database values
- using foreign keys for relational integrity
- using transactions for multi-step database workflows
- avoiding dynamically constructed SQL
- keeping probability policies separate from probability calculations

In a production system, externally supplied probability data should also be authenticated, authorized, audited, and validated against an appropriate domain-specific data-quality policy.

## Conceptual Workflow

A typical probability evaluation follows this sequence:

`Sample Space`
    
`↓`

`Outcomes + Outcome Probabilities`
    
`↓`

`Event Definition`
    
`↓`

`Event Set Operations`
    
`↓`

`P(A), P(B), P(A ∩ B), P(A ∪ B)`
    
`↓`

`Conditional Probability / Independence`
    
`↓`

`Policy Evaluation or Decision`

The implementations preserve these conceptual boundaries while expressing them through different programming and database models.

## Practical Distinctions

Several terms that are often conflated are deliberately separated.

**Outcome** is one possible result of an experiment.

**Sample space** is the complete collection of possible outcomes.

**Event** is a subset of the sample space.

**Probability** assigns a numerical measure to an event.

**Conditional probability** changes the reference space based on known information.

**Independence** describes a relationship between events.

**Simulation** estimates behavior through repeated trials rather than deriving the probability directly.

These distinctions are reflected in the domain models, functions, validation rules, and database relationships rather than being treated only as explanatory terminology.
