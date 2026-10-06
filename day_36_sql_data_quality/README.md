# SQL Data Quality Engineering

## Scope

This project treats SQL data quality as a combination of deterministic validation, relational integrity, completeness measurement, duplicate discovery, and statistical anomaly detection.

The central distinction is important:

- **Duplicate detection** asks whether multiple rows represent the same business entity or business event.
- **Missing-value detection** asks whether required information is absent or unusable.
- **Referential integrity** asks whether relationships between related tables remain structurally valid.
- **Anomaly detection** asks whether an observation is unusually different from an established distribution or historical baseline.

These conditions overlap in production systems, but they require different detection strategies. A duplicate may satisfy every database constraint because it has a different primary key. A missing value may be syntactically valid SQL `NULL` but operationally unacceptable. A foreign-key violation is deterministic rather than statistical. An anomaly may be completely valid and still deserve investigation.

The six deliverables use a common retail customer-and-order scenario while deliberately approaching the problem differently in each language.

---

## Data Quality as a Relational Engineering Problem

A data-quality system should distinguish between structural rules, semantic rules, and statistical rules.

Structural rules describe relationships that the database can enforce directly. A customer identifier should be unique, an order should reference an existing customer, and an order amount should satisfy a positive-value constraint.

Semantic rules describe whether a value has meaning in the business domain. A non-null email address can still be malformed, and two records with different identifiers can still represent the same customer.

Statistical rules describe unusual behavior relative to a distribution. A very large order is not automatically invalid. It becomes an anomaly when it is sufficiently unusual relative to an appropriate baseline.

This distinction determines the appropriate response:

| Quality condition | Typical detection | Typical response |
|---|---|---|
| Duplicate business identity | `GROUP BY`, normalized keys | Investigate, merge, or quarantine |
| Missing required value | `IS NULL`, blank checks, completeness metrics | Repair, reject, or request source correction |
| Broken relationship | Foreign key and anti-join | Reject or quarantine |
| Invalid domain value | `CHECK`, predicates, validation queries | Reject or correct |
| Statistical anomaly | Percentiles, IQR, averages, standard deviation, windows | Investigate rather than automatically delete |

A production data-quality platform should avoid treating every detected issue as a deletion candidate.

---

## Duplicate Detection

### Why primary keys are insufficient

A primary key answers the question:

> Does this row have a unique database identifier?

It does not answer:

> Does this row represent a unique real-world customer?

The example contains two customer records for Ravi Kumar with the same normalized email and name but different `customer_id` values. A normal primary-key constraint accepts both rows.

The Python, JavaScript, C++, Java, and SQL implementations therefore create a business identity from attributes such as normalized email and normalized name.

Normalization removes differences that should not create separate identities. The implementations use trimming and case normalization so that values such as `RAVI@EXAMPLE.COM` and ` ravi@example.com ` can be compared consistently.

### Exact business-identity duplicates

The core SQL pattern is:

`GROUP BY lower(btrim(email)), lower(btrim(full_name)) HAVING COUNT(*) > 1`

This groups rows by normalized business identity and returns only groups with multiple records.

The resulting customer IDs are retained because a quality report needs traceability. A duplicate group should lead an operator back to the source records that caused the detection.

### Duplicate email versus duplicate customer

The SQL implementation deliberately includes two different checks.

An identical email can indicate duplicate identity, but it does not necessarily prove that two records represent the same person. Shared organizational addresses, family accounts, support addresses, and legacy migration records can all create legitimate email collisions.

The business-identity rule therefore combines attributes instead of treating one field as universally decisive.

### Duplicate remediation

The SQL script demonstrates transactional remediation rather than automatic deletion. A reviewed duplicate record is changed, a postcondition is evaluated, and the transaction is committed only after the quality condition has been rechecked.

This pattern is safer than issuing an unconditional `DELETE` because data-quality remediation changes source information and can have downstream consequences.

---

## Missing Values and Completeness

Missing data has several forms.

A SQL `NULL` represents an absent value. An empty string represents a supplied string containing no useful characters. A whitespace-only value is technically a string but may be semantically missing.

The implementations therefore distinguish checks such as:

`email IS NULL`

from:

`btrim(email) = ''`

A completeness profile is more useful than a single count because it shows which fields are causing the problem.

The SQL view `customer_completeness_profile` calculates populated and missing counts for customer attributes. This allows the same dataset to be monitored over time.

### Field-level auditing

The SQL script uses `UNION ALL` to turn column-level completeness failures into a row-oriented audit result:

`customer_id | column_name`

This representation is useful for downstream issue management because each missing attribute becomes an independently traceable quality event.

### Required versus optional fields

Not every `NULL` is automatically a data-quality error.

For example, a phone number might legitimately be unavailable for a particular customer. A quality policy must establish whether the field is required for the relevant business process.

A good implementation therefore separates:

- physical database nullability,
- business-required completeness,
- conditional requirements,
- acceptable unknown states.

The code demonstrates the detection mechanism, while the business policy determines the severity and remediation path.

---

## Referential Integrity

Referential integrity is concerned with relationships between tables.

The example uses:

`customers.customer_id`

as the parent key and:

`orders.customer_id`

as the child reference.

The PostgreSQL definition uses a foreign key so that a newly inserted order cannot reference a nonexistent customer.

This is different from duplicate detection. Referential integrity does not ask whether two customers are the same. It asks whether an order's referenced customer exists.

### Why an audit query is still useful

A foreign key protects the current database state when it is enabled and enforced. Quality engineering can still require explicit orphan detection when auditing:

- legacy imports,
- external databases,
- migration snapshots,
- files loaded before validation,
- systems where constraints were temporarily disabled.

The anti-join pattern is:

`LEFT JOIN customers ... WHERE customers.customer_id IS NULL`

It identifies child rows without a corresponding parent.

### Severity

A broken foreign-key relationship is treated as critical in the examples because downstream joins can lose business meaning. An order without a valid customer cannot be reliably attributed to a customer.

The appropriate operational response may be quarantine rather than deletion because the source system may still contain enough information to repair the relationship.

---

## Deterministic Constraints versus Anomalies

A deterministic constraint defines what is allowed.

For example:

`CHECK (amount > 0)`

states that zero and negative order amounts are invalid.

An anomaly rule has a different meaning.

A very large amount may be unusual without being invalid. A high-value enterprise order can be legitimate. Therefore, an anomaly detector normally creates an investigation signal rather than automatically rejecting the record.

This distinction is central to responsible data-quality design.

---

## Anomaly Detection with SQL

### IQR-based monetary anomaly detection

The SQL implementation uses:

- first quartile, `Q1`
- third quartile, `Q3`
- interquartile range, `IQR = Q3 - Q1`
- upper fence, `Q3 + 1.5 × IQR`

PostgreSQL's `percentile_cont` calculates interpolated percentiles.

The query then compares each order against the upper fence.

This method is useful when a numeric distribution is skewed because quartiles are less sensitive to extreme values than a simple mean.

### Why the IQR rule is not a validity rule

An IQR outlier is not automatically corrupt data.

For example, an order worth ₹500,000 may be unusual in a dataset where most orders are worth ₹1,000, but it may represent a genuine enterprise purchase.

The correct classification is therefore:

**statistical anomaly**, not necessarily **invalid record**.

---

## Customer-Relative Anomalies

Global statistics can miss contextual anomalies.

Suppose most customers purchase between ₹50 and ₹200, while one enterprise customer regularly purchases between ₹20,000 and ₹50,000. A global threshold may flag that customer repeatedly even though the behavior is normal for that customer.

The Python, Java, and SQL implementations therefore include customer-relative analysis.

The SQL implementation uses window functions:

`AVG(amount) OVER (PARTITION BY customer_id)`

This calculates a customer's average without collapsing the individual order rows.

The result can then compare each order with the customer's own historical level.

This illustrates an important data-quality principle:

> Anomaly detection requires an appropriate comparison population.

Possible comparison populations include all customers, one customer, one product category, one geographic region, one account type, or one time period.

---

## Activity Anomalies

The implementations also model daily order velocity.

The relevant grouping operation is conceptually:

`GROUP BY customer_id, order_date`

The resulting daily counts form a distribution. The examples then use a three-standard-deviation threshold.

This can identify sudden bursts of activity that deserve investigation.

The rule is deliberately separate from duplicate detection. Five orders from the same customer on the same day are not necessarily duplicates. They are multiple business events that may instead indicate unusually high activity.

---

## Python Implementation

The Python program uses only the standard library and SQLite.

The `DataQualityEngine` class provides a coherent quality-analysis layer. It executes SQL queries for:

- customer completeness,
- business duplicate detection,
- referential-integrity audits,
- order-domain validation,
- IQR monetary anomalies,
- daily order-velocity anomalies.

The SQLite database enables the script to demonstrate actual relational behavior rather than merely manipulating Python dictionaries.

The schema contains:

- `customers`
- `orders`

The `orders.customer_id` foreign key demonstrates database-level relationship enforcement.

The script also enables SQLite foreign-key enforcement explicitly with:

`PRAGMA foreign_keys = ON`

The `demonstrate_constraint_enforcement` function attempts invalid inserts and captures `sqlite3.IntegrityError`. This shows the difference between detecting a problem after the fact and preventing a new invalid state from being committed.

The Python implementation also writes a CSV issue report. This converts the in-memory quality findings into an auditable artifact suitable for later processing.

### Python anomaly implementation

The Python script implements percentile interpolation directly instead of depending on NumPy. This keeps the example executable with a standard Python installation.

The IQR calculation is performed from positive order amounts. The script also uses SQL window-function logic for customer-level analysis.

### Python remediation

The transactional repair example uses a SQLite savepoint. It changes a known duplicate, evaluates the postcondition, and commits only if the duplicate condition disappears.

This illustrates a broader production pattern:

`stage -> validate -> commit`

rather than:

`change -> assume success`

---

## JavaScript Implementation

The JavaScript program takes a different perspective.

Instead of embedding a SQL engine, it models the quality process as an asynchronous Node.js pipeline. This is useful for understanding how database-derived quality signals can be consumed by an event-driven application layer.

`DataQualityIssue` represents an immutable issue.

`QualityEventBus` uses Node's `EventEmitter` to publish:

- stage start events,
- stage completion events,
- individual quality issues.

`DataQualityPipeline` orchestrates the checks.

The pipeline deliberately separates:

- missing-value validation,
- duplicate detection,
- referential-integrity checks,
- domain validation,
- monetary anomaly detection,
- activity anomaly detection.

JavaScript's `Map` is used for grouping records by normalized business identity. `Set` is used for efficient membership testing during referential-integrity validation.

The pipeline uses asynchronous scheduling through `setImmediate`. This does not make the calculations computationally parallel, but it demonstrates how quality stages can participate in a Node.js event-driven workflow.

The program writes an audit report as JSON using Node's filesystem API.

---

## C++ Case Study

The C++ implementation models a repository-quality service as a reusable in-memory governance engine.

The case study uses:

- `Customer`
- `Order`
- `QualityIssue`
- `QualityReport`
- `RepositoryQualityEngine`

The engine performs all four major quality categories.

### C++ data structures

`std::map` groups customers by normalized business identity.

`std::unordered_map` provides efficient customer-ID membership checks for referential integrity.

`std::set` stores valid order states.

`std::vector` stores source records and detected issues.

These structures represent the same logical operations that SQL performs with grouping, joins, predicates, and aggregation, but from an application-engineering perspective.

### C++ duplicate detection

The duplicate key combines normalized email and name.

This is intentionally different from checking whether two integer IDs are equal. A unique surrogate identifier does not eliminate business duplicates.

### C++ referential validation

Customer identifiers are indexed in an `unordered_map`. Each order is then checked against that collection.

The resulting operation is conceptually equivalent to a relational anti-join.

### C++ anomaly detection

The C++ engine calculates interpolated percentiles and derives an IQR upper fence.

It also groups order activity by customer and date and calculates a population standard deviation for activity counts.

The implementation therefore demonstrates both robust distribution-based detection and contextual activity analysis.

### C++ transactional reasoning

C++ itself does not provide a relational transaction.

The case study therefore models the transaction boundary as an architectural concern: stage the repair, validate its postcondition, and commit through the actual database transaction layer.

This distinction prevents an application-level data structure from being mistaken for a database consistency mechanism.

---

## Java Enterprise Implementation

The Java program models data quality as an explicit rule-driven service.

The primary domain types are:

- `Customer`
- `Order`
- `QualityIssue`
- `QualityReport`
- `BusinessIdentity`

The `QualityRule` interface defines a common contract for individual validation rules.

Concrete implementations include:

- `MissingCustomerRule`
- `DuplicateCustomerRule`
- `ReferentialIntegrityRule`
- `OrderDomainRule`
- `AmountAnomalyRule`
- `DailyVelocityRule`

This structure is useful in enterprise systems because quality rules can be composed without placing every rule inside one large conditional method.

Java records provide immutable domain values for the sample model. The quality report itself stores an immutable copy of the issue collection.

The service evaluates each rule independently and aggregates the resulting issues.

### Java-specific design

The implementation uses Java collections for grouping and membership validation and streams for statistical and reporting operations.

The `BusinessIdentity` record explicitly represents the concept of a normalized customer identity. This is more expressive than passing around an unstructured concatenated string.

The quality score is calculated from severity weights:

- critical issues have the largest penalty,
- high-severity issues have a substantial penalty,
- medium issues have a smaller penalty,
- low issues have the smallest penalty.

This is an illustrative scoring model rather than a universal data-quality standard. A production organization should define weights according to business impact.

---

## SQL Data Model

The PostgreSQL implementation provides the strongest database-native representation.

### Customers

The `customers` table contains:

- `customer_id`
- `full_name`
- `email`
- `phone`
- `created_at`

The primary key guarantees identifier uniqueness.

The `customers_name_not_blank` and `customers_email_not_blank` constraints prevent certain forms of invalid input while still allowing `NULL` where the schema permits it.

### Orders

The `orders` table contains:

- `order_id`
- `customer_id`
- `amount`
- `order_date`
- `status`

The `orders_customer_fk` foreign key establishes the parent-child relationship.

The positive amount constraint prevents a class of invalid financial records.

The status constraint limits order state values to the defined domain.

### Indexes

The normalized customer identity index supports repeated searches involving normalized email and name.

The order customer/date index supports queries that inspect a customer's activity over time.

The amount index supports amount-oriented filtering and investigation.

Indexes are not automatically beneficial for every query. Their value depends on data volume, selectivity, query frequency, write overhead, and the optimizer's chosen execution plan.

---

## Database-Level Enforcement

Quality checks should be enforced at the strongest appropriate layer.

A primary key is appropriate for identifier uniqueness.

A foreign key is appropriate for parent-child existence.

A `CHECK` constraint is appropriate for simple domain conditions such as positive amounts or allowed status values.

An application-level validation rule is appropriate when the rule requires contextual business logic that would be awkward or expensive to enforce as a constraint.

Statistical anomaly detection usually belongs in an analytical or monitoring layer because an anomaly is not necessarily an invalid database state.

This creates a layered quality architecture:

**database constraints → deterministic validation → semantic quality rules → statistical monitoring**

Each layer has a different responsibility.

---

## Transactional Remediation

A data-quality system should distinguish detection from remediation.

Detection can be read-only.

Remediation changes business data and therefore requires stronger controls.

The SQL example uses a transaction around a duplicate remediation. The postcondition is checked before `COMMIT`.

If the validation fails, the transaction should be rolled back.

This pattern is especially important for data cleansing because an incorrect automatic repair can destroy evidence needed to understand the original problem.

Production remediation commonly benefits from:

- audit records,
- source lineage,
- before-and-after values,
- operator or service identity,
- transaction boundaries,
- validation after modification,
- rollback capability.

---

## Quality Scoring

The implementations include illustrative quality scores to show how issue severity can be aggregated.

A score is useful for monitoring trends, but a single score should not replace detailed issue reporting.

For example, two datasets might both score 90 while one contains a critical referential-integrity problem and the other contains many minor completeness issues.

A useful dashboard therefore exposes both:

- aggregate measures,
- detailed rule-level findings.

The most important metrics may include completeness percentage, duplicate rate, orphan-record count, constraint-violation count, anomaly rate, and unresolved issue age.

---

## Edge Cases

### Null versus blank

`NULL` and `''` are different database states. A completeness rule should explicitly decide whether both count as missing.

### Case differences

Email and identity matching can produce false negatives if normalization is inconsistent.

### Legitimate duplicates

Two records with the same email do not always represent the same person. Duplicate detection should create evidence for review rather than blindly merge records.

### Statistical false positives

A legitimate high-value order may be an IQR outlier.

### Small datasets

Percentiles and standard deviations become unstable with very small samples. The examples therefore avoid anomaly classification when insufficient observations exist.

### Customer-specific distributions

A global threshold can misclassify customers with naturally different transaction sizes. Customer-relative baselines reduce this problem.

### Missing foreign keys

An order with a missing customer relationship is structurally problematic, but remediation may require recovering the correct parent rather than deleting the order.

### Historical imports

Existing databases may contain invalid records even when current constraints are strong. Audit queries remain valuable during migrations and data reconciliation.

---

## Common Failure Modes

### Treating primary-key uniqueness as duplicate prevention

A unique surrogate identifier only guarantees identifier uniqueness. It does not guarantee real-world entity uniqueness.

### Using `COUNT(*)` without a business key

Counting rows does not identify which attributes make two records duplicates. The grouping key must represent the business identity being investigated.

### Treating every NULL as an error

Optional attributes can legitimately be unknown. Completeness policies must be field-specific.

### Using anomaly thresholds as deletion rules

Statistical unusualness is evidence for investigation, not proof of corruption.

### Detecting relationships only in application code

Critical parent-child integrity should be enforced at the database layer when the relationship belongs inside the same relational system.

### Ignoring normalization

Case and whitespace differences can fragment duplicate groups and create false negatives.

### Producing only aggregate quality scores

A score without record-level evidence makes remediation difficult. Quality systems need traceable findings.

---

## Performance Considerations

Duplicate detection over large tables can become expensive because normalization and grouping may require substantial computation.

Expression indexes can improve repeated normalized-key searches. The PostgreSQL implementation creates an index over:

`lower(btrim(email))`

and:

`lower(btrim(full_name))`

For large analytical datasets, partitioning or incremental processing may be more appropriate than repeatedly scanning the entire history.

Referential checks benefit from indexes on foreign-key columns.

Time-based anomaly analysis benefits from indexes involving the fields used to group or filter events, such as customer ID and order date.

Statistical queries can require sorting. Percentile functions may therefore become expensive as the dataset grows. Production systems may use pre-aggregated data, materialized views, approximate statistics, or dedicated analytical storage when the workload justifies it.

`EXPLAIN` should be used to verify whether the database optimizer is actually using an intended index or choosing another access path.

---

## Security and Governance

Data-quality systems frequently process sensitive customer attributes.

Quality reports should avoid exposing unnecessary personal information. A production issue record can often use an internal customer ID rather than copying full names, email addresses, or phone numbers into every audit destination.

Database permissions should follow least privilege.

Read-only quality checks should use read-only credentials where possible.

Remediation operations should require stronger authorization than detection operations.

Audit records should preserve who or which service changed data, when the change occurred, and which quality rule motivated the change.

Anomaly detection should also be treated carefully because suspicious behavior is not equivalent to confirmed misuse or fraud.

---

## Debugging Data-Quality Rules

A quality rule should be testable against a small dataset with known expected outcomes.

For duplicate detection, test:

- two identical business identities,
- different casing,
- surrounding whitespace,
- same email with different names,
- missing email values.

For completeness, test both `NULL` and blank values.

For referential integrity, test a valid parent, an absent parent, and a nullable relationship if the domain allows it.

For anomaly detection, test a normal distribution, a single extreme value, and a dataset too small to support reliable statistics.

When a quality query produces unexpected results, inspect the normalized values and intermediate aggregates before changing the final predicate. Common errors originate in the grouping key or population used to calculate statistics.

---

## Relationship Between the Implementations

The implementations intentionally do not translate the same program line-for-line.

The Python program emphasizes direct SQL execution through SQLite, database constraints, issue reporting, and transactional repair.

The JavaScript program models a Node.js event-driven quality pipeline with immutable records, `Map`/`Set` grouping, asynchronous stages, and JSON audit output.

The C++ program treats quality validation as a reusable governance engine and focuses on data structures, algorithmic complexity, and service-level reasoning.

The Java program models an enterprise rule architecture using domain types, interfaces, immutable records, collections, and a composable quality service.

The SQL script puts the strongest relational mechanisms directly in the database: constraints, foreign keys, indexes, views, CTEs, window functions, percentile calculations, issue tables, transactions, and execution-plan inspection.

The shared domain makes the differences meaningful while preserving the distinction between completeness, duplication, referential integrity, and statistical anomaly detection.

---

## Practical Quality Architecture

A mature relational data-quality pipeline can be represented as:

`source data → ingestion validation → relational constraints → quality profiling → rule-based detection → anomaly analysis → issue management → reviewed remediation → post-remediation validation`

The order matters.

Structural integrity should be protected before downstream analytics depend on the data.

Completeness and semantic rules should identify records that satisfy database structure but fail business requirements.

Anomaly detection should operate after a sufficiently reliable population has been established because corrupted or incomplete inputs can distort statistical baselines.

Remediation should be auditable and reversible.

The result is not merely a cleaner table. It is a repeatable process in which quality conditions are explicit, measurable, explainable, and tied to concrete records.
