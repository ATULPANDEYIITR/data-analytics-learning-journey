# Exploratory Data Analysis: Distributions, Relationships, and Anomalies

## Scope

This project implements exploratory data analysis as a structured analytical workflow rather than as a collection of isolated statistical calculations.

The dataset represents customer behavior with five numerical variables:

| Variable | Meaning | Analytical role |
|---|---|---|
| `age` | Customer age | Distribution and demographic relationship |
| `income` | Annual income | Distribution and spending relationship |
| `monthly_spend` | Monthly customer spending | Distribution, segmentation, and anomaly detection |
| `visits` | Monthly visits | Behavioral relationship |
| `satisfaction` | Customer satisfaction score from 0 to 10 | Distribution and relationship analysis |

The analysis is divided into four distinct perspectives:

- **Univariate analysis** studies one variable at a time.
- **Bivariate analysis** studies relationships between two variables.
- **Multivariate analysis** examines several numerical variables jointly.
- **Anomaly analysis** identifies observations that differ substantially from the main distribution.

The implementations use the same conceptual domain but deliberately apply different engineering approaches in each language.

## Analytical Model

The workflow can be represented as:

    Raw observations
          |
          v
    Validation
          |
          +--------------------+
          |                    |
          v                    v
    Univariate             Data distribution
    statistics             and quantiles
          |
          v
    Bivariate relationships
          |
          v
    Multivariate structure
          |
          v
    Anomaly detection
          |
          v
    Interpretation and reporting

Validation occurs before statistical calculations. This prevents invalid ages, negative monetary values, impossible satisfaction scores, duplicate identifiers, and non-finite numerical values from silently affecting results.

## Univariate Analysis

Univariate analysis examines a single variable without considering another variable.

The Python implementation calculates:

- observation count
- arithmetic mean
- median
- minimum
- maximum
- population standard deviation
- quartiles
- five-number summaries
- histogram bins

The JavaScript implementation provides equivalent analytical capabilities while using JavaScript-specific data structures and asynchronous execution.

The mean describes the arithmetic center of the observations, while the median is more resistant to extreme values. This distinction is important for `monthly_spend`, where the high-spending customer creates a right-tail observation.

The five-number representation consists of:

    minimum
    Q1
    median
    Q3
    maximum

The interquartile range is:

    IQR = Q3 - Q1

It provides the basis for the IQR anomaly rule used by the Python, JavaScript, and database implementations.

## Distribution Analysis

A histogram partitions a numerical range into intervals and counts observations in each interval.

The implementation explicitly handles the constant-value edge case. When minimum and maximum are equal, normal bin-width calculation would divide by zero, so the complete dataset is represented as one interval.

Histogram construction follows:

    width = (maximum - minimum) / number_of_bins

Each observation is assigned to a bin based on its position within the range. The final bin includes the maximum value explicitly so that the maximum cannot fall outside the histogram.

The histogram is descriptive. It does not establish statistical significance or a probability distribution.

## Bivariate Analysis

Bivariate analysis evaluates the relationship between two variables.

The implementations calculate Pearson correlation for pairs such as:

    income <-> monthly_spend
    visits <-> monthly_spend
    age <-> satisfaction

Pearson correlation is calculated as:

    r = covariance(X,Y) / (standard deviation(X) * standard deviation(Y))

Its range is approximately:

    -1 <= r <= +1

A positive value indicates that the two variables tend to increase together, while a negative value indicates an inverse linear relationship.

The implementation explicitly handles zero-variance variables. If either input contains no variation, the denominator becomes zero and the analytical engine returns `0.0` rather than producing an undefined numerical result.

Correlation is descriptive evidence of linear association. It is not evidence that one variable causes the other.

## Multivariate Analysis

Multivariate analysis considers multiple variables together.

The Python implementation builds a covariance matrix for:

    age
    income
    monthly_spend
    visits
    satisfaction

For variables X and Y, population covariance is calculated as:

    covariance(X,Y) =
        sum((Xi - mean(X)) * (Yi - mean(Y))) / N

The resulting matrix provides a compact representation of how variables vary together.

Diagonal elements represent each variable's population variance. Off-diagonal elements represent pairwise covariance.

Covariance depends on measurement scale. A large covariance does not necessarily indicate a stronger relationship than a smaller covariance from variables measured on different scales. Correlation is often easier to compare across heterogeneous variables because it is standardized.

## Anomaly Detection

Two anomaly strategies are represented.

### Z-score

The Python implementation uses:

    z = (x - mean) / population_standard_deviation

An observation is treated as anomalous when the absolute z-score reaches the configured threshold.

The threshold is deliberately configurable because an anomaly rule is a policy choice rather than a universal constant.

The implementation also handles zero standard deviation. If every observation is identical, no z-score anomaly is reported.

### IQR rule

The IQR method uses:

    lower_fence = Q1 - 1.5 * IQR
    upper_fence = Q3 + 1.5 * IQR

Observations outside these fences are reported as anomalies.

The IQR method is useful when a variable has a skewed distribution because quartiles are less affected by extreme observations than the mean and standard deviation.

An anomaly is an observation requiring investigation. It is not automatically an error. A high-spending customer may be a genuine customer segment rather than corrupted data.

## Python Implementation

The Python file defines:

- `Observation` as a typed immutable data structure
- `AnalysisType` as an explicit analytical enumeration
- `EDAError` for domain-specific failures
- `EDAEngine` as the main analytical service
- validation for identifiers and numerical ranges
- descriptive statistics
- quantile interpolation
- histogram construction
- Pearson correlation
- covariance matrices
- z-score anomaly detection
- IQR anomaly detection
- spending segmentation
- JSON reporting

The script uses only Python's standard library.

`load_observations()` converts raw dictionaries into validated domain objects. This separates input parsing from analysis.

The final report contains separate sections for univariate statistics, distributions, bivariate relationships, multivariate covariance, anomalies, and derived spending segments.

Assertions provide executable checks for key output properties. Logging reports the number of processed records and detected anomalies.

## JavaScript Implementation

The JavaScript implementation is designed for Node.js and uses no external packages.

`CustomerRecord` provides a domain representation of one observation.

`EDAEngine` uses:

- `Set` for duplicate identifier detection
- `Map` for spending-band grouping
- classes for analytical state
- `Promise` and `setImmediate()` for asynchronous dataset processing
- `EventEmitter` for completion notifications
- explicit numerical validation
- descriptive statistics
- quantiles
- histograms
- Pearson correlation
- IQR anomaly detection

The asynchronous boundary is intentionally separate from the statistical calculations. This makes the analytical engine usable inside a larger event-driven ingestion process without forcing the statistical methods themselves to become asynchronous.

The implementation catches errors at the application boundary and sets a non-zero process exit code when processing fails.

## C++17 Implementation

The C++17 program takes a different engineering perspective and models a repository governance case study.

The domain contains:

- repositories
- users
- repository membership
- branches
- commits
- Pull Requests
- reviews
- status checks
- branch protection
- merge strategies

The governance engine evaluates whether a Pull Request can be merged.

It checks:

- distinct source and target branches
- presence of commits
- draft state
- merge conflicts
- required review approvals
- reviewer eligibility
- required status checks
- resolved conversations
- allowed merge strategies

The program uses STL containers such as `vector`, `set`, and `map`, along with enums and exception handling.

The implementation also includes a correlation calculation to connect the repository-governance case study with the analytical principles of descriptive relationships. This calculation is intentionally separate from merge eligibility so that statistical association is not confused with repository policy enforcement.

A failing required status check is explicitly tested as a merge-blocking condition.

## Java 17 Implementation

The Java program models repository governance as an enterprise domain.

Records are used for immutable domain values such as:

- commits
- reviews
- status checks
- branch protection policies

`PullRequest` is modeled as mutable workflow state because its lifecycle changes from open to approved, blocked, or merged.

`MergeEligibilityService` centralizes policy evaluation.

Approval counting has explicit semantics:

- reviewer must be eligible
- review must be approved
- approval must not be stale
- approval must not be dismissed
- duplicate reviewer approvals count once

This prevents a stale approval from being treated as a current approval.

The Java implementation also calculates descriptive statistics for customer spending using streams and immutable result maps. The repository workflow and analytical calculation remain separate domain concerns.

## PostgreSQL Implementation

The PostgreSQL script creates a complete relational model for repository governance.

The primary relationships are:

    repository
        |
        +-- repository_member
        |
        +-- branch
        |      |
        |      +-- branch_protection_policy
        |
        +-- commit_record
        |
        +-- pull_request
               |
               +-- pull_request_commit
               |
               +-- review
               |     |
               |     +-- review_comment
               |
               +-- conversation
               |
               +-- status_check

The database enforces important rules using:

- primary keys
- foreign keys
- unique constraints
- check constraints
- partial indexes
- triggers
- SQL functions
- views
- transactions

`enforce_review_eligibility()` prevents an ineligible repository user from submitting an approval.

`count_current_approvals()` counts distinct, non-stale, non-dismissed approvals.

`required_checks_pass()` determines whether all required status checks are passing.

`unresolved_conversations()` exposes unresolved discussion count.

`merge_eligibility` combines these independent signals into a database-level workflow view.

`merge_pull_request()` performs a transactional eligibility check before changing the Pull Request state to `merged`.

The sample records intentionally include both an eligible Pull Request and a blocked Pull Request with stale approval and unresolved conversation state.

## Pull Request Lifecycle

A Pull Request is the workflow object through which proposed branch changes are presented for integration.

A realistic lifecycle is:

    Draft
      |
      v
    Open
      |
      +----> Changes requested ----+
      |                            |
      |                            v
      +---- Review / updates <-----+
      |
      v
    Approval + checks
      |
      v
    Merge eligibility
      |
      v
    Merged

A Pull Request contains proposed changes, normally represented by commits from a source branch relative to a target branch.

Draft status communicates that the proposal is not yet ready for normal completion. Opening or converting a Draft Pull Request does not itself constitute approval.

Synchronizing the source branch with the target branch is a branch-state operation. It can be necessary after new target-branch commits change the effective merge base.

Merge conflicts are also branch-state conditions. They are distinct from review decisions because a reviewer can approve a change while the branch is still unable to merge cleanly.

A Pull Request can be closed without being merged and can later be reopened when repository workflow permits it.

## Code Review

Code Review evaluates the actual proposed changes.

Review mechanics include:

- selecting files or lines for inspection
- creating inline comments
- discussing implementation details
- submitting a review state
- requesting changes
- approving changes
- resolving discussions

An inline comment is tied to a specific location in a changed file when the review system supports line-level comments.

A review should evaluate correctness, maintainability, security implications, test coverage, compatibility, and scope.

Review quality depends on whether the reviewer examines the actual change rather than treating approval as a procedural checkbox.

Requested changes represent a substantive review decision. They should normally be addressed by modifying the proposed changes and allowing the reviewer to reassess the updated state.

A resolved conversation means the discussion has reached a repository-defined resolution state. It does not necessarily mean the underlying code is automatically correct.

## Approvals

An approval is a review decision indicating that an eligible reviewer accepts the proposed changes under the applicable review process.

Approval semantics are narrower than the complete code-review process.

The implementation distinguishes:

- eligible reviewer
- approved review
- stale approval
- dismissed approval
- current approval count
- required approval count

A reviewer who is not eligible should not satisfy an approval requirement.

A stale approval should not automatically survive a change that invalidates the review context. The Java and PostgreSQL implementations explicitly represent stale approvals.

Dismissal removes an approval's ability to satisfy the current policy.

Approval count is therefore not simply:

    number of rows where state = approved

It is a policy result derived from reviewer eligibility and review freshness.

## Branch Protection

Branch Protection is repository-level enforcement applied to a protected target branch.

Typical controls represented in the model include:

| Control | Purpose |
|---|---|
| Required reviews | Prevent merge without required review decisions |
| Required status checks | Require automated validation to pass |
| Direct-push restriction | Force normal changes through the review workflow |
| Force-push restriction | Protect branch history |
| Branch deletion restriction | Prevent accidental removal of protected branches |
| Resolved conversations | Require review discussions to be resolved |
| Linear history | Restrict merge methods that introduce non-linear history |
| Merge strategy restrictions | Limit permitted integration methods |
| Administrator bypass | Define whether administrators can bypass selected controls |

Branch Protection does not perform the code review itself.

It establishes repository conditions that must be satisfied before integration.

This distinction is central:

    Pull Request
        = workflow for proposing changes

    Code Review
        = evaluation of proposed changes

    Approval
        = review decision

    Branch Protection
        = repository-level enforcement

Merge eligibility is the point where these independent mechanisms interact.

## Status Checks and Merge Eligibility

Automated status checks provide machine-evaluated signals such as:

- unit tests
- static analysis
- security scanning
- build validation

A required status check that is failing or pending prevents eligibility when the branch policy requires it.

The database model stores each check independently so that a repository can require several checks rather than treating all automation as one Boolean field.

This makes failure diagnosis explicit:

    Merge rejected
        |
        +-- insufficient approvals
        +-- unresolved conversations
        +-- failing required check
        +-- merge conflict
        +-- unsynchronized branch
        +-- prohibited strategy
        +-- draft Pull Request

## Security Considerations

Repository governance is an authorization problem as well as a workflow problem.

The implementations therefore distinguish reviewer eligibility from review state.

Important controls include:

- preventing unauthorized users from satisfying approval requirements
- preventing stale approvals from being counted
- restricting direct mutation of protected branches
- requiring successful security checks
- preventing force pushes where policy requires protection
- validating all identifiers and numeric inputs
- rejecting invalid domain states early

The PostgreSQL implementation places selected controls at the database layer so that application-level mistakes cannot silently bypass the corresponding relational rule.

The Python and JavaScript implementations validate input before analysis. This prevents malformed records from contaminating descriptive statistics.

## Performance Considerations

For a dataset containing N observations:

- mean calculation is O(N)
- median using sorting is O(N log N)
- quantile calculation using sorting is O(N log N)
- histogram construction is O(N) after range determination
- Pearson correlation is O(N)
- covariance matrix construction for K variables is O(N × K²)
- IQR anomaly detection is O(N log N) when quartiles require sorting

The Python implementation repeatedly extracts columns for clarity. For very large datasets, columns can be cached or processed in streaming form.

The JavaScript implementation uses arrays for numerical analysis and `Set` and `Map` for constant-time average membership and grouping operations.

The C++ implementation uses STL containers and avoids unnecessary dynamic structures in the numerical calculation.

The PostgreSQL implementation creates indexes only on workflow predicates used by the sample queries. Indexes should be selected from actual query workloads because every index introduces write and storage cost.

## Edge Cases

The implementations explicitly account for:

- empty datasets
- duplicate identifiers
- negative monetary values
- invalid ages
- invalid satisfaction scores
- negative visit counts
- NaN or non-finite numerical values
- zero-variance columns
- equal minimum and maximum histogram values
- insufficient vector sizes for correlation
- missing commits
- draft Pull Requests
- merge conflicts
- unresolved conversations
- stale approvals
- dismissed approvals
- ineligible reviewers
- failing required checks
- pending required checks
- disallowed merge strategies

These cases are part of the analytical and governance model rather than being treated as incidental errors.

## Distinction Between Data Quality and Anomalies

A validation failure and an anomaly are not the same event.

A validation failure means the record violates a domain constraint.

Examples:

    age = -5
    satisfaction = 17
    income = -1000

Such data should normally be rejected or quarantined before analysis.

An anomaly is a valid observation that is statistically unusual.

Example:

    monthly_spend = 1450

If that value is within the business domain but far from the rest of the population, it may be an anomaly. It should be investigated rather than automatically deleted.

This distinction prevents statistical rules from being used as data-cleaning rules without domain evidence.

## Practical Interpretation

EDA should be treated as a diagnostic stage.

A high correlation between income and spending can identify an association worth investigating. It does not establish a causal mechanism.

A histogram can reveal skewness or concentration, but bin choices affect visual interpretation.

An IQR anomaly can identify an unusual observation, but the reason for the unusual value must be established through domain investigation.

A covariance matrix exposes joint variation but is sensitive to measurement units.

The implementations therefore separate calculation from interpretation. They calculate explicit numerical evidence while preserving the distinction between statistical description, data validation, anomaly identification, and operational decision-making.

## File Responsibilities

| File | Primary responsibility |
|---|---|
| Python | Full dependency-free EDA engine with validation, statistics, distributions, correlations, covariance, and anomaly detection |
| JavaScript | Event-driven Node.js analytical engine using `Map`, `Set`, `Promise`, and `EventEmitter` |
| C++17 | Repository governance and merge-eligibility engine with an embedded correlation calculation |
| Java 17 | Enterprise-style repository domain model with records, enums, immutable policy data, review freshness, and merge service |
| PostgreSQL | Relational repository-governance workflow with constraints, indexes, triggers, functions, views, sample data, and transactional merge logic |

## Execution Model

The Python program can be executed directly with a standard Python installation.

The JavaScript program is designed for Node.js.

The C++ program requires a compiler with C++17 support.

The Java program requires Java 17 or later.

The PostgreSQL script requires a PostgreSQL database session with permission to create and drop the `eda_governance` schema.

The PostgreSQL script intentionally begins by recreating its schema so that the complete model can be executed repeatedly in a controlled development database.

## Design Boundary

The analytical model and repository-governance model intentionally remain distinct.

EDA answers questions such as:

    What is the distribution?
    What is typical?
    How do variables relate?
    Which observations are unusual?

Repository governance answers questions such as:

    Is the proposed change reviewable?
    Are approvals valid?
    Are required checks passing?
    Is the target branch protected?
    Is the Pull Request eligible for merging?

Both domains use explicit validation, state, rules, and failure handling, but their decisions have different meanings. Statistical evidence does not replace repository policy, and repository policy does not determine statistical significance.
