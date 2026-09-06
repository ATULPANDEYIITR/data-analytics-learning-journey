# Data Quality: Beginner to Advanced

## 1. Topic Introduction

Data quality is the degree to which data satisfies the requirements of its intended use.

A dataset is not automatically high quality simply because it can be stored, processed, or queried. A value can have the correct data type and still be incorrect. A record can contain no missing fields and still represent the wrong customer. A current record can still violate a business rule.

Data quality therefore combines technical, semantic, business, temporal, and operational considerations.

The major dimensions covered in the accompanying Python script are:

- Accuracy
- Completeness
- Consistency
- Validity
- Uniqueness
- Timeliness
- Integrity

The script also demonstrates:

- Missing-data detection
- Duplicate detection
- Data profiling
- Validation rules
- Business-rule validation
- Cross-field validation
- Referential integrity
- Anomaly detection
- Standardization
- Remediation
- Quarantine
- Quality scoring
- Monitoring
- Quality regression detection
- Data contracts
- Data lineage
- Quality testing
- Root-cause analysis
- Production design
- Governance
- Machine-learning data quality considerations

The implementation uses only Python's standard library.

---

## 2. Data Quality Dimensions

### 2.1 Accuracy

Accuracy measures whether a value correctly represents the real-world entity, event, or fact it is intended to describe.

For example, suppose a trusted customer system states that a customer's name is `Alice Sharma`, while the analytical database contains `Alicia Sharma`. The stored value may be correctly formatted, but it may be inaccurate.

Accuracy generally requires some form of reference or verification.

The script demonstrates accuracy by comparing customer records with a trusted reference dataset.

### 2.2 Completeness

Completeness measures whether required information is present.

For a customer dataset, required fields might include:

- Customer ID
- Name
- Email
- Age
- Country
- Signup date
- Status

A missing email decreases completeness if email is required for the intended application.

The script calculates:

`completeness = populated required cells / total required cells`

Completeness can be measured at several levels:

- Field level
- Record level
- Column level
- Dataset level
- Pipeline level

A record can be complete according to one business process and incomplete according to another.

### 2.3 Consistency

Consistency means that equivalent or related data does not contradict itself.

Examples include:

- `active` versus `ACTIVE`
- `India` versus `IN`
- Different customer addresses across systems
- A transaction recorded in USD while its currency field says INR
- An update timestamp preceding the record's creation timestamp

Consistency is different from accuracy. A system can consistently contain the wrong value.

### 2.4 Validity

Validity measures whether data conforms to defined structural, syntactic, domain, or business rules.

Examples:

- Age must be an integer between 0 and 120.
- Status must belong to an approved set.
- Date must use a valid date representation.
- Credit limit cannot be negative.
- Email must satisfy the expected syntax.

Validity can be divided into several types:

- Type validity
- Format validity
- Range validity
- Domain validity
- Enumeration validity
- Pattern validity
- Business-rule validity

A valid value is not necessarily accurate.

### 2.5 Uniqueness

Uniqueness concerns unintended duplicate entities or records.

For example, a customer ID intended to be unique should not occur twice.

Uniqueness is frequently evaluated using a business key rather than the entire row.

A duplicate may be:

- An exact duplicate
- A duplicate business key with different attributes
- A semantic duplicate
- A potential duplicate discovered through similarity matching

The script demonstrates both deterministic duplicate detection and simple candidate matching.

### 2.6 Timeliness

Timeliness measures whether data is sufficiently current for its intended purpose.

Freshness requirements depend on the application.

Examples:

- A payment-processing system may require near-real-time information.
- A stock-market application may require second-level freshness.
- A monthly financial report may tolerate substantially older data.
- A historical research dataset may intentionally contain old records.

Timeliness therefore cannot be defined independently of business requirements.

### 2.7 Integrity

Integrity concerns the preservation of valid relationships and constraints.

Important forms include:

- Primary-key integrity
- Foreign-key integrity
- Domain integrity
- Referential integrity
- Constraint integrity
- Transactional integrity

For example, if an order references customer `C999`, but customer `C999` does not exist in the customer table, referential integrity has been violated.

---

## 3. Missing Data

Missing data is one of the most common data-quality problems.

Typical representations include:

- `None`
- Empty strings
- Whitespace-only strings
- `NA`
- `N/A`
- `NULL`
- `unknown`

These representations should be standardized before analysis.

The script provides an `is_missing()` function to identify common missing representations.

### Missing Does Not Mean Zero

The following values should not automatically be treated as equivalent:

- `None`
- `0`
- `False`
- `""`
- `"unknown"`

For example, an account balance of zero is usually a legitimate value, not missing information.

### Types of Missingness

Statistical analysis often distinguishes:

- Missing Completely At Random (MCAR)
- Missing At Random (MAR)
- Missing Not At Random (MNAR)

These distinctions matter when deciding whether and how to impute missing values.

The safest approach is not to replace missing values blindly.

---

## 4. Data Profiling

Data profiling is the systematic examination of a dataset to understand its structure and quality.

Typical profiling statistics include:

- Row count
- Column count
- Missing count
- Missing percentage
- Distinct count
- Uniqueness
- Minimum
- Maximum
- Mean
- Median
- Frequency distributions
- Data types
- Pattern distributions

The script's profiling functions calculate basic missingness and uniqueness statistics for every discovered column.

Profiling is useful before implementing quality rules because it reveals the actual characteristics of the data.

---

## 5. Validation Rules

A validation rule defines an explicit condition that data must satisfy.

The script uses a `ValidationRule` abstraction containing:

- A rule name
- A validation function
- A `ValidationResult`

Each result contains:

- Rule name
- Pass/fail state
- Explanation
- Field
- Value

This separation allows validation logic to be reused and aggregated.

### Required-Field Validation

A required-field rule checks whether a field is populated.

### Email Validation

The script applies a regular expression to perform basic email syntax validation.

This demonstrates syntax checking, not mailbox verification.

A syntactically valid address does not prove that:

- The domain exists.
- The mailbox exists.
- The person owns the mailbox.
- The address belongs to the intended customer.

### Range Validation

Age is checked against a defined range.

This is an example of domain validation.

### Enumeration Validation

Customer status is restricted to:

- `active`
- `inactive`
- `suspended`

Enumeration validation prevents unexpected categorical values.

### Date Validation

The script distinguishes between:

1. Correct date format
2. Actual calendar validity
3. Business validity

A string can resemble a date while representing an impossible calendar date.

A date can also be a real calendar date but violate a business rule.

---

## 6. Technical Rules Versus Business Rules

This distinction is fundamental.

### Technical Rule

An age field must contain an integer.

### Business Rule

A customer must be at least 18 years old to qualify for a particular financial product.

Technical validation concerns representation and structure.

Business validation concerns meaning and operational requirements.

A record may pass all technical checks while failing an important business rule.

---

## 7. Accuracy Versus Validity

These concepts are frequently confused.

### Validity

"Does this value conform to the defined rule?"

### Accuracy

"Does this value represent the real-world truth or trusted reference?"

Consider:

`age = 35`

This is valid if the expected range is 0 to 120.

It is accurate only if the customer's actual age is 35.

Therefore:

- Valid but inaccurate data is possible.
- Accurate data can theoretically be represented in an invalid format.
- Validity can often be checked automatically.
- Accuracy frequently requires a trusted reference, verification mechanism, or domain knowledge.

---

## 8. Consistency Versus Accuracy

Consistency does not guarantee correctness.

Suppose five systems all report a customer's city as `Lucknow`, while the customer's verified address is actually in another city.

The systems are consistent with one another but inaccurate.

This is why data-quality programs should measure multiple dimensions separately.

---

## 9. Duplicate Data

Duplicate detection begins by defining what constitutes the same entity.

### Exact Duplicates

Two records contain the same complete information.

### Key-Based Duplicates

Two records share the same business key.

For example:

`customer_id = C001`

appearing twice is a uniqueness violation if customer ID is defined as unique.

### Semantic Duplicates

Two records may represent the same entity even when their textual values differ.

Examples:

- `Robert Smith`
- `Bob Smith`

or:

- `ABC Private Limited`
- `ABC Pvt. Ltd.`

These cases require entity-resolution techniques.

---

## 10. Duplicate Detection Strategies

Common approaches include:

### Hash-Based Exact Matching

Create a deterministic representation of each record and group identical representations.

Typical complexity is approximately O(n).

### Business-Key Matching

Group by fields such as:

- Customer ID
- Account number
- Product ID
- Transaction ID

### Composite Keys

When no single field is unique, combine multiple fields.

For example:

`customer_id + transaction_date + transaction_reference`

### Fuzzy Matching

Similarity algorithms can identify candidate matches.

The script demonstrates a simple character-set similarity calculation.

This is educational rather than production-grade entity resolution.

Fuzzy matching can create:

- False positives
- False negatives
- Computational expense

A similarity score should normally be treated as evidence rather than proof.

---

## 11. Duplicate Survivorship

Detecting duplicates is different from deciding which record should survive.

Possible survivorship strategies include:

- Keep first
- Keep latest
- Keep most complete
- Prefer trusted source
- Prefer manually verified record
- Merge attributes according to field-level rules

The script demonstrates a "latest update wins" approach.

This should only be used when the timestamp is trustworthy and the business meaning supports that rule.

---

## 12. Standardization

Standardization converts equivalent representations into a canonical form.

Examples:

- `ACTIVE` -> `active`
- ` Alice Sharma ` -> `Alice Sharma`
- `ALICE@EXAMPLE.COM` -> `alice@example.com`
- `india` -> `India`

Standardization improves consistency.

It does not automatically improve accuracy.

For example, converting:

`IND`

to:

`India`

may improve representation while still being wrong if the original value represented another country.

---

## 13. Cross-Field Consistency

Some quality rules cannot be evaluated by examining one field independently.

Examples:

- Shipment date must be on or after order date.
- Payment date cannot precede invoice date.
- Account closure date cannot precede account opening date.
- An inactive account should not receive a new transaction.
- A person's age should be compatible with their date of birth.
- A transaction amount should use the correct currency.

The script implements cross-field checks involving:

- Status
- Credit limit
- Signup date
- Update timestamp

Cross-field rules are particularly important because many real-world defects are relational rather than isolated.

---

## 14. Anomalous Records

An anomaly is an observation that differs substantially from expected behavior.

Anomaly detection is not equivalent to error detection.

An unusual transaction may be:

- A legitimate large purchase
- A fraud event
- A new customer segment
- A measurement error
- A system defect
- A rare but valid event

The script demonstrates several statistical approaches.

---

## 15. Z-Score

The z-score is:

`z = (x - mean) / standard deviation`

A large absolute z-score indicates that an observation is far from the distribution's center.

The method works best under assumptions appropriate to the underlying distribution.

It can be unreliable when:

- Data is strongly skewed.
- The dataset already contains extreme outliers.
- The distribution is non-normal.
- Sample size is small.

---

## 16. Interquartile Range

The IQR method uses:

`IQR = Q3 - Q1`

Common Tukey bounds are:

`Lower = Q1 - 1.5 × IQR`

`Upper = Q3 + 1.5 × IQR`

Values outside these bounds are candidates for outlier investigation.

IQR is often more robust to extreme values than mean-and-standard-deviation approaches.

---

## 17. Median Absolute Deviation

Median Absolute Deviation, or MAD, is another robust measure.

It is based on deviations from the median rather than deviations from the mean.

This makes MAD useful when distributions are skewed or contain extreme observations.

The script includes a modified-score implementation using MAD.

---

## 18. Anomaly Versus Error

This distinction is operationally important.

An anomaly is an observation requiring investigation.

An error is data that violates a known correctness requirement.

Automatically deleting every anomaly can destroy legitimate information.

A safer process is:

1. Detect.
2. Classify.
3. Investigate.
4. Determine whether the record is incorrect.
5. Correct, quarantine, or retain according to the decision.

---

## 19. Referential Integrity

Referential integrity ensures that relationships between entities remain valid.

Suppose:

`Customer C001`

exists.

An order referencing `C001` is valid.

An order referencing:

`C999`

is invalid if `C999` does not exist.

Relational databases commonly enforce referential integrity through foreign keys.

The Python implementation uses a set of valid customer IDs and checks orders against it.

This is efficient because set membership is approximately O(1) on average.

---

## 20. Data Quality Scoring

The script calculates dimension-level quality metrics and combines them using a weighted score.

A weighted quality score can be represented as:

`Score = Σ(score × weight) / Σ(weight)`

Different dimensions may have different importance.

For example:

- Accuracy may receive high weight.
- Completeness may receive medium weight.
- Uniqueness may receive a critical threshold even if it has moderate weight.

### Important Limitation

A composite score should never replace individual metrics.

A dataset scoring 99% overall can still contain a catastrophic primary-key failure.

Critical constraints should therefore be treated separately from aggregate scores.

---

## 21. Quality Rule Engines

The `DataQualityEngine` provides a reusable framework for applying multiple validation rules to many records.

It produces:

- Number of records
- Number of rules
- Total checks
- Passed checks
- Failed checks
- Overall pass rate
- Failures by rule
- Detailed results

This structure is useful for:

- ETL validation
- Batch pipelines
- Data ingestion
- Data warehouse quality checks
- Master-data validation
- Automated testing

---

## 22. Quarantine

A quality pipeline should generally avoid silently deleting invalid records.

A better pattern is to separate:

- Accepted records
- Rejected records
- Rejection reasons

The script implements a quarantine-style partition.

Rejected records can then be:

- Corrected
- Investigated
- Sent back to the source system
- Manually reviewed
- Stored for audit purposes

This preserves traceability.

---

## 23. Remediation

Data-quality remediation means correcting or otherwise resolving quality defects.

Possible remediation actions include:

- Standardization
- Source correction
- Imputation
- Deduplication
- Quarantine
- Manual review
- Reference-data enrichment
- Reprocessing

Automated correction should be conservative.

The script deliberately standardizes values where the transformation is deterministic but does not fabricate an invalid email address or impossible age.

---

## 24. Missing-Value Imputation

Possible strategies include:

- Mean imputation
- Median imputation
- Mode imputation
- Forward fill
- Backward fill
- Model-based imputation
- Domain-specific defaults

Each has assumptions and risks.

Replacing every missing value with zero is usually inappropriate because it changes the meaning of the data.

The reason for missingness should be considered before choosing a remediation method.

---

## 25. Null Semantics

Missing data has different semantics from ordinary values.

Examples:

- `NULL`
- `0`
- `False`
- Empty string
- Unknown

These should not automatically be treated as interchangeable.

Database systems may also implement three-valued logic involving:

- TRUE
- FALSE
- UNKNOWN

This can affect filtering, comparisons, aggregation, and joins.

---

## 26. Data Contracts

A data contract defines expectations between data producers and consumers.

A contract can specify:

- Schema
- Required fields
- Allowed values
- Data types
- Freshness
- Quality thresholds
- Ownership
- Semantics
- Privacy constraints
- Service-level expectations

The script implements a simplified contract containing:

- Required fields
- Allowed statuses
- Maximum data age

Data contracts move quality controls closer to the producer and make expectations explicit.

---

## 27. Data Lineage

Data lineage describes where data originated and how it changed.

A typical flow is:

Source system → Raw storage → Transformation → Curated data → Analytics

Lineage helps answer:

- Where did this value originate?
- Which transformation changed it?
- Which upstream system caused the defect?
- Which downstream reports are affected?

Without lineage, remediation can become a symptom-treatment exercise rather than a root-cause investigation.

---

## 28. Root-Cause Analysis

A validation rule tells you that something is wrong.

It does not necessarily tell you why.

For example:

`email is missing`

could result from:

- The source system never collected the email.
- An ETL mapping dropped the field.
- A transformation converted it to NULL.
- An upstream schema changed.
- A join failed.
- A pipeline processed an incomplete source extract.

Effective quality management therefore combines validation with lineage, logging, monitoring, and source investigation.

---

## 29. Quality Monitoring

Quality should be monitored continuously rather than checked only once.

Useful metrics include:

- Completeness percentage
- Validity percentage
- Duplicate rate
- Accuracy rate
- Freshness
- Referential-integrity failures
- Rule-failure counts
- Anomaly counts

The script provides a `QualityMonitor` abstraction that stores metric observations and compares them with thresholds.

---

## 30. Quality Thresholds

Thresholds should be tied to business requirements.

For example:

- Completeness ≥ 95%
- Validity ≥ 98%
- Uniqueness ≥ 99.9%
- Freshness ≤ 30 minutes

The appropriate values depend on the system.

A threshold should not be selected simply because it appears numerically attractive.

---

## 31. Quality Regression

A dataset can pass an absolute threshold while still experiencing serious deterioration.

For example:

Previous quality:

`98.5%`

Current quality:

`94.1%`

Even if 94.1% appears acceptable in isolation, the decline may indicate:

- Source-system change
- Schema change
- ETL defect
- New data provider
- Application deployment problem

Monitoring should therefore examine both absolute quality and changes over time.

---

## 32. Data Quality Testing

Data-quality testing is similar to software testing.

Examples include:

- Required-field tests
- Uniqueness tests
- Domain tests
- Referential-integrity tests
- Range tests
- Relationship tests
- Freshness tests
- Schema tests

The script demonstrates assertions such as:

- No duplicate customer keys.
- Required fields are populated.
- Status values belong to an allowed domain.

Quality tests can be run as part of automated pipelines.

---

## 33. Quality Invariants

An invariant is a property expected to remain true.

Examples:

- Customer IDs must be unique.
- Transaction amounts cannot be negative.
- Foreign keys must reference existing entities.
- A closing date cannot precede an opening date.
- Status must belong to the permitted domain.

Invariants are especially useful because they express business assumptions in executable form.

---

## 34. Performance Considerations

Data-quality implementations must account for scale.

Typical complexity patterns include:

| Operation | Typical Complexity |
|---|---:|
| Hash-based duplicate detection | O(n) |
| Set membership lookup | O(1) average |
| Profiling a column | O(n) |
| Sorting for IQR | O(n log n) |
| Pairwise fuzzy comparison | O(n²) |
| Referential integrity with a hash set | O(n + m) |

For large datasets:

- Prefer database constraints when appropriate.
- Use indexes on important keys.
- Stream data where possible.
- Avoid loading entire datasets into memory unnecessarily.
- Partition large processing jobs.
- Use blocking keys before fuzzy matching.
- Push simple validation toward the data source or database where practical.

---

## 35. Streaming Quality Checks

Some quality checks do not require the complete dataset in memory.

Examples:

- Missing-value counting
- Row counting
- Basic frequency counting
- Range checking
- Type checking
- Rule validation

The script demonstrates a streaming-style missing-rate calculation that processes one record at a time.

This pattern is useful for large files and data streams.

Some algorithms, such as exact median calculation, may require more memory or specialized streaming algorithms.

---

## 36. Data Quality and Security

Quality systems frequently process sensitive information.

Security considerations include:

- Least-privilege access
- Encryption
- Access control
- Secure logging
- Audit trails
- Retention policies
- Secure test data
- Data masking
- Protection against malformed input

A quality failure should not cause sensitive information to appear unnecessarily in logs.

Examples of information that should not be casually logged include:

- Passwords
- Authentication tokens
- Payment-card data
- Secret keys
- Sensitive personal information

Data quality and security are related but distinct disciplines. A dataset can be high quality and insecure, or secure and low quality.

---

## 37. Production Design

A production-grade data-quality system should generally:

1. Define requirements before implementing checks.
2. Assign ownership.
3. Establish explicit business definitions.
4. Validate data at appropriate pipeline stages.
5. Separate raw and curated data.
6. Maintain quarantine paths.
7. Record quality metrics.
8. Alert on important failures.
9. Track quality trends.
10. Maintain lineage.
11. Preserve auditability.
12. Avoid silent data loss.
13. Document automated corrections.
14. Distinguish legitimate exceptions from errors.

Prevention is generally preferable to downstream correction.

For example, preventing invalid status values at the point of entry is preferable to discovering them months later in a reporting warehouse.

---

## 38. Common Mistakes

### Treating Validity as Accuracy

A valid email format does not prove that the email belongs to the customer.

### Replacing Missing Values with Zero

Zero has semantic meaning in many domains.

### Deleting Anomalies Automatically

An anomaly may represent a legitimate rare event.

### Using Exact Row Matching Only

Two records representing the same entity may differ in spelling, formatting, or non-key fields.

### Ignoring Business Keys

Technical row equality does not define entity uniqueness.

### Using Only One Composite Quality Score

Critical failures can disappear inside an aggregate score.

### Silently Correcting Production Data

Automated changes should be explainable and auditable.

### Ignoring Upstream Changes

A sudden increase in missing fields can be caused by an upstream schema or application change.

### Using Fuzzy Matching Without Controls

Similarity algorithms can create false matches.

### Logging Sensitive Values

Debugging information should not create a security incident.

---

## 39. Quality Dimension Interactions

One defect may affect multiple dimensions.

Examples:

| Problem | Relevant Dimensions |
|---|---|
| Wrong customer email | Accuracy, validity |
| Missing customer email | Completeness |
| Duplicate customer record | Uniqueness, integrity |
| Old exchange rate | Timeliness, accuracy |
| Different country representations | Consistency |
| Order references nonexistent customer | Integrity, validity |

This illustrates why data quality is multidimensional.

---

## 40. Data Quality and Business Impact

Not every quality issue deserves the same operational response.

Prioritization can consider:

- Number of affected records
- Business criticality
- Financial impact
- Regulatory impact
- Customer impact
- Operational impact
- Security impact
- Frequency
- Time sensitivity

A small number of incorrect financial balances may be more important than thousands of formatting inconsistencies.

The script demonstrates a simple priority score based on affected records and business criticality.

Production systems should generally use domain-specific severity matrices rather than relying on one generic formula.

---

## 41. Quality Failure Classification

Different failures can require different responses.

Possible responses include:

### Monitor

Used for low-impact issues.

### Repair or Review

Used where automated remediation is reasonably safe or manual review is practical.

### Quarantine and Alert

Used when bad records should not enter downstream systems.

### Block Pipeline

Used for critical violations such as broken financial balances or primary-key integrity.

A pipeline should not necessarily fail because of every minor quality defect. Failure policy should reflect business criticality.

---

## 42. Governance

Data quality is not exclusively an engineering responsibility.

Relevant roles include:

### Data Owner

Accountable for business meaning and quality requirements.

### Data Steward

Manages definitions, standards, and operational quality.

### Data Engineer

Implements ingestion, transformation, validation, and monitoring.

### Analyst

Identifies downstream effects and quality problems.

### Domain Expert

Confirms whether values are meaningful and correct within the business context.

### Platform Team

Provides infrastructure, observability, storage, and processing capabilities.

### Security and Privacy Teams

Protect sensitive information and ensure appropriate controls.

Clear ownership is essential because a quality rule without an accountable owner may not lead to remediation.

---

## 43. Data Quality for Machine Learning

Machine-learning datasets introduce additional quality concerns.

Important dimensions include:

- Feature completeness
- Label correctness
- Duplicate samples
- Class distribution
- Outliers
- Distribution changes
- Temporal validity
- Data leakage
- Sampling bias

A dataset can be technically valid while being unsuitable for a machine-learning objective.

For example, all fields may have valid types and no missing values, yet the target labels may be systematically incorrect.

---

## 44. Data Leakage

Data leakage occurs when information unavailable at prediction time is used to construct a model's features.

Example:

A model predicts whether a loan applicant will default.

A feature containing information generated after the default event should not be available to the model at application time.

That feature could be:

- Non-null
- Correctly typed
- Correctly formatted
- Internally consistent

Yet it violates the temporal semantics of the prediction problem.

This demonstrates that data quality includes semantic and temporal correctness.

---

## 45. Data Quality and Data Pipelines

A practical pipeline can be organized as:

1. Ingest raw data.
2. Profile incoming data.
3. Standardize representations.
4. Validate schema.
5. Apply technical rules.
6. Apply business rules.
7. Detect duplicates.
8. Check relationships.
9. Detect anomalies.
10. Quarantine invalid records.
11. Load accepted data.
12. Calculate quality metrics.
13. Monitor trends.
14. Alert on important failures.
15. Investigate root causes.

The script implements a simplified version of this workflow through `DataQualityPipeline`.

---

## 46. Raw, Accepted, and Quarantined Data

A robust architecture often separates:

### Raw Data

Original input preserved for traceability.

### Validated Data

Records that satisfy required rules.

### Quarantined Data

Records that fail quality checks.

### Curated Data

Business-ready data after approved transformations and enrichment.

Keeping these stages separate improves:

- Auditability
- Debugging
- Reprocessing
- Root-cause analysis
- Reconciliation

---

## 47. Accuracy Requires a Trusted Reference

Accuracy is particularly difficult to measure automatically.

Possible reference sources include:

- Verified master data
- Government records
- Physical measurements
- Customer confirmation
- Trusted operational systems
- Audited financial systems

The reference itself must be trustworthy.

Comparing one potentially corrupted dataset against another potentially corrupted dataset does not establish true accuracy.

---

## 48. Timeliness Requires a Clock and a Requirement

Freshness cannot be evaluated without defining:

- Reference time
- Update timestamp
- Maximum acceptable age

For example:

`current_time - update_time <= allowed_age`

The allowed age must come from business requirements.

The script uses a fixed reference time for reproducibility.

Production systems should normally use the actual system clock or a controlled processing timestamp.

---

## 49. Edge Cases

Important edge cases include:

- Empty strings
- Whitespace
- Null values
- Zero
- Negative zero
- NaN
- Infinity
- Invalid dates
- Leap years
- Time zones
- Duplicate keys
- Missing timestamps
- Case differences
- Unicode characters
- Unexpected categorical values

Special numeric values such as NaN require explicit handling because NaN has unusual comparison behavior.

Date validation should distinguish formatting, calendar validity, and business validity.

---

## 50. Data Quality Limitations

No automated quality system can prove that all data is correct.

Important limitations include:

- Accuracy may require external verification.
- Business rules can change.
- Anomaly detection can produce false positives.
- Fuzzy matching can produce false matches.
- Missingness may be difficult to interpret.
- A composite quality score can hide critical failures.
- Reference data can itself be wrong.
- Automated corrections can introduce new defects.
- Statistical methods depend on assumptions about the data.

The objective is not to eliminate every unusual value. The objective is to make data quality measurable, controllable, observable, and appropriate for its intended use.

---

## 51. Implementation Considerations

The Python implementation uses several reusable abstractions:

### `ValidationRule`

Represents an individual quality rule.

### `ValidationResult`

Represents the outcome of a rule.

### `DataQualityEngine`

Executes rules and aggregates failures.

### `QualityMetric`

Represents a normalized quality dimension and weight.

### `QualityMonitor`

Stores metric observations and detects threshold violations.

### `DataContract`

Represents simplified expectations for a data source.

### `DataQualityPipeline`

Combines multiple quality operations into an end-to-end workflow.

These abstractions illustrate how data-quality logic can move from isolated checks toward maintainable systems.

---

## 52. Python Concepts Used

The script also demonstrates several general Python techniques relevant to data-quality engineering:

- Functions
- Classes
- Dataclasses
- Type hints
- Lists
- Dictionaries
- Sets
- Tuples
- Iterables
- Generators through iteration
- Regular expressions
- Exception handling
- Sorting
- Statistical calculations
- Hash-based lookup
- Assertions
- Enumerations through sets
- Object-oriented design
- Deterministic synthetic-data generation

The implementation intentionally avoids external dependencies.

---

## 53. End-to-End Quality Workflow

The central workflow demonstrated by the script is:

**Profile → Standardize → Validate → Detect duplicates → Check integrity → Detect anomalies → Quarantine → Measure → Monitor → Investigate → Remediate**

Each stage serves a different purpose.

Profiling tells you what exists.

Standardization reduces representational inconsistency.

Validation checks explicit rules.

Duplicate detection protects uniqueness.

Integrity checks relationships.

Anomaly detection identifies unusual observations.

Quarantine prevents known-bad records from silently flowing downstream.

Measurement quantifies quality.

Monitoring detects changes.

Investigation identifies root causes.

Remediation resolves the underlying problem.

---

## 54. Practical Quality Checklist

A production data-quality implementation should be able to answer:

- What does each critical field mean?
- Which fields are required?
- Which fields must be unique?
- What values are allowed?
- Which relationships must hold?
- How accurate must the data be?
- How fresh must the data be?
- How is missing data represented?
- Which values are considered anomalies?
- Which anomalies are legitimate?
- Which records should be quarantined?
- Who owns each quality dimension?
- How are quality metrics calculated?
- What thresholds trigger alerts?
- How are quality regressions detected?
- How can a defect be traced to its source?
- How are corrections audited?
- What happens when a critical rule fails?
- How are sensitive values protected during diagnosis?

These questions transform data quality from an informal cleanup activity into an operational discipline.
