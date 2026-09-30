# SQL CASE Expressions

SQL `CASE` is an expression that evaluates conditions and returns a value. It is particularly useful when query results need to contain business classifications, transformed values, numeric buckets, conditional metrics, or explicit handling for exceptional data states.

The central distinction is between the SQL mechanism and the business rule implemented through it. `CASE` provides the conditional expression mechanism. The `WHEN` predicates define the conditions, and `THEN` expressions define the resulting values.

This project treats three closely related uses as separate concerns:

- **CASE WHEN** provides conditional evaluation.
- **Conditional transformations and bucketing** convert raw database values into useful analytical categories.
- **Business rules** encode domain-specific decisions such as operational priorities or customer segmentation.

The Python, JavaScript, and C++ implementations use a sales and customer-data scenario so that the same SQL concepts can be examined from different implementation perspectives.

## Core CASE Syntax

A searched `CASE` evaluates independent Boolean conditions:

    CASE
        WHEN condition_a THEN result_a
        WHEN condition_b THEN result_b
        ELSE fallback_result
    END

For example:

    CASE
        WHEN annual_spend >= 200000 THEN 'Enterprise'
        WHEN annual_spend >= 100000 THEN 'Premium'
        WHEN annual_spend >= 50000 THEN 'Growth'
        ELSE 'Standard'
    END

The conditions are evaluated in order. Once a `WHEN` condition matches, its corresponding `THEN` result is returned.

This makes predicate ordering part of the business rule.

A simple `CASE` compares one expression against equality values:

    CASE region
        WHEN 'North' THEN 'Northern Territory'
        WHEN 'South' THEN 'Southern Territory'
        WHEN 'East' THEN 'Eastern Territory'
        WHEN 'West' THEN 'Western Territory'
        ELSE 'Unassigned Territory'
    END

Simple `CASE` is appropriate when the decision is fundamentally an equality mapping. Searched `CASE` is more appropriate for ranges, compound predicates, NULL checks, and conditions involving several columns.

## CASE WHEN Semantics

The Python implementation uses `sqlite3` to execute actual SQL. Its `demonstrate_searched_case()` function classifies customers by annual spending.

The threshold ordering is significant:

    WHEN annual_spend >= 200000 THEN 'Enterprise'
    WHEN annual_spend >= 100000 THEN 'Premium'
    WHEN annual_spend >= 50000 THEN 'Growth'
    ELSE 'Standard'

A customer spending `225000` satisfies all three numeric thresholds, but the result is `Enterprise` because the first condition is the first matching branch.

Reversing the rules would change the result. A rule such as `WHEN annual_spend >= 50000 THEN 'Growth'` placed before the Enterprise rule would capture every Enterprise customer before the later condition was reached.

This is one of the most important properties of `CASE`: overlapping predicates are not automatically resolved by SQL according to the most specific condition. The developer must encode the intended precedence.

## Simple CASE and Equality Mapping

Simple `CASE` has the form:

    CASE expression
        WHEN value_a THEN result_a
        WHEN value_b THEN result_b
        ELSE fallback
    END

The Python implementation uses customer regions such as `North`, `South`, `East`, and `West`. The JavaScript implementation provides a complementary `switch` representation of the same equality-oriented decision structure.

Simple `CASE` is particularly suitable for controlled categorical mappings where the comparison expression is the same for every branch.

It is not the right abstraction for a rule such as:

    WHEN order_amount >= 50000 THEN 'Large'

because that rule depends on a range rather than equality. A searched `CASE` should be used for such conditions.

## Conditional Transformations

A conditional transformation changes how a source value is presented without changing the stored value.

The Python program transforms `discount_rate` into categories:

- A `NULL` discount becomes `Discount not recorded`.
- A zero discount becomes `No discount`.
- A discount below `0.10` becomes `Low discount`.
- A discount from `0.10` up to, but not including, `0.20` becomes `Standard discount`.
- A discount of `0.20` or higher becomes `High discount`.

The transformation also calculates an estimated net amount using `COALESCE(discount_rate, 0)`.

This distinction is important. A missing discount and an explicitly stored zero discount can represent different business states. Replacing both with zero before classification would remove information from the result.

## Numeric Bucketing

Bucketing converts continuous numeric data into discrete analytical categories.

The implementations use order amount ranges:

| Range | Bucket |
|---|---|
| `0 <= amount < 5000` | Small |
| `5000 <= amount < 15000` | Medium |
| `15000 <= amount < 50000` | Large |
| `amount >= 50000` | Enterprise |

The SQL form is:

    CASE
        WHEN order_amount < 5000 THEN 'Small'
        WHEN order_amount < 15000 THEN 'Medium'
        WHEN order_amount < 50000 THEN 'Large'
        ELSE 'Enterprise'
    END

The lower boundary is implicit after the previous condition has failed. For example, an amount of `5000` does not satisfy `amount < 5000`, so it reaches the next branch and becomes `Medium`.

This produces half-open intervals. Such boundaries are usually easier to reason about than overlapping conditions such as `amount BETWEEN 0 AND 5000` followed by another rule that also includes `5000`.

Boundary values are explicitly tested in all three implementations.

## Business Rules

Business rules use `CASE` to convert several database attributes into an operational decision.

The Python program classifies an order using status, shipping time, and order amount:

    CASE
        WHEN order_status = 'cancelled'
            THEN 'Do not process'
        WHEN shipping_days IS NULL
            THEN 'Investigate shipping data'
        WHEN shipping_days > 7 AND order_amount >= 20000
            THEN 'Escalate delayed high-value order'
        WHEN order_amount >= 50000
            THEN 'Priority fulfillment'
        WHEN shipping_days > 7
            THEN 'Shipping review'
        ELSE 'Normal fulfillment'
    END

These rules demonstrate why business logic should not be treated as a collection of interchangeable conditions.

A cancelled order must be handled before fulfillment rules. Otherwise, another condition could classify the same order as a high-value fulfillment task.

A missing shipping value also represents a distinct operational state. It should not automatically be treated as a normal shipping duration.

The order of the predicates therefore expresses precedence.

## Conditional Aggregation

`CASE` can be placed inside aggregate functions.

A common pattern is:

    SUM(
        CASE
            WHEN order_status = 'completed' THEN 1
            ELSE 0
        END
    )

This counts completed orders without removing non-completed orders from the query's input set.

The Python implementation extends the pattern to revenue:

    SUM(
        CASE
            WHEN order_status = 'completed'
            THEN order_amount
            ELSE 0
        END
    )

This produces completed revenue while retaining pending and cancelled orders for other conditional metrics.

The same query can calculate completed orders, cancelled orders, total orders, and completed revenue for each region.

This is different from placing `WHERE order_status = 'completed'` on the entire query. A `WHERE` clause removes rows before aggregation, whereas conditional aggregation allows several categories to be measured within the same group.

The C++ case study models the same operation explicitly. It increments `completedOrders` only when the order status is `completed` and adds the order amount to `completedRevenue` under the same condition.

## CASE and NULL

SQL `NULL` represents an unknown or missing value. It does not behave like an ordinary value.

A condition such as:

    discount_rate = 0

does not identify a `NULL` discount.

An explicit condition is required:

    CASE
        WHEN discount_rate IS NULL THEN 'Missing'
        WHEN discount_rate = 0 THEN 'Explicitly zero'
        ELSE 'Present and non-zero'
    END

The Python program executes this SQL directly against SQLite.

The JavaScript implementation uses `null` to model the same distinction.

The C++ implementation uses `std::optional<double>`, which prevents a missing discount from being silently represented as a numeric value.

The three implementations therefore use different language mechanisms to represent the same database-level distinction.

## Rule Precedence and Overlapping Conditions

Consider:

    CASE
        WHEN amount >= 50000 THEN 'Growth'
        WHEN amount >= 100000 THEN 'Premium'
        ELSE 'Standard'
    END

An amount of `120000` matches the first branch. The second branch is never reached for that value.

The issue is not a SQL syntax error. The expression is valid SQL. The problem is the relationship between the business rules.

There are two ways to address such a design:

- Encode explicit precedence intentionally when overlap is meaningful.
- Convert the rules into mutually exclusive ranges when each value should belong to exactly one category.

The Python, JavaScript, and C++ implementations deliberately demonstrate the first-match behavior so that the consequence of rule ordering is observable rather than merely described.

## Configuration-Driven Bucketing

Hard-coded thresholds can become difficult to maintain when business boundaries change frequently.

The Python program introduces a `CaseRule` data structure containing a label, minimum, and optional maximum. The program validates the ranges before generating a SQL `CASE` expression.

For example, the configuration represents:

    Micro       [0, 5000)
    Small       [5000, 15000)
    Medium      [15000, 50000)
    Large       [50000, infinity)

The validation rejects overlapping intervals.

The generated SQL uses numeric boundaries that have already passed validation and escapes the generated labels as SQL string literals.

This pattern demonstrates an important production distinction: dynamic SQL should be generated from validated configuration, and externally supplied runtime values should generally be passed through parameter binding rather than concatenated into SQL.

For very large or frequently changing rule sets, storing rules in database tables can be more appropriate than maintaining an enormous `CASE` expression.

## Parameterized CASE

The Python implementation includes a query where the threshold is passed as a SQLite parameter:

    CASE
        WHEN order_amount >= ? THEN 'Above threshold'
        ELSE 'Below threshold'
    END

The threshold is supplied separately through the database driver's parameter-binding interface.

This prevents the threshold value from becoming part of the SQL syntax.

A useful distinction is that parameterization is appropriate for values, while SQL identifiers such as column names generally cannot be supplied through ordinary value parameters. The Python and JavaScript SQL-generation helpers therefore validate column identifiers before interpolation.

## Python Implementation

The Python program is an executable SQLite case study rather than a collection of isolated Python conditionals.

`create_database()` creates an in-memory relational model containing `customers` and `orders`.

The SQL demonstrations cover:

- searched `CASE` for customer spend segmentation
- simple `CASE` for region transformation
- conditional discount transformation
- order-amount bucketing
- multi-column operational business rules
- `SUM(CASE ...)` conditional aggregation
- grouped classification with `HAVING`
- `CASE` inside `ORDER BY`
- generated CASE expressions from validated bucket configuration
- parameterized CASE thresholds
- explicit NULL classification
- overlapping-rule behavior
- boundary testing

The `validate_bucket_rules()` function checks whether configured ranges overlap. This is an application-level safeguard around business logic that would otherwise be encoded directly into SQL.

The script requires only the Python standard library and can run without an external database server because SQLite is included with normal Python distributions.

## JavaScript Implementation

The JavaScript program deliberately approaches the topic from a different direction.

Rather than executing SQL directly, it builds a JavaScript representation of the decision-processing layer that would correspond to SQL `CASE` logic in a reporting system.

`classifySpend()` models searched CASE behavior through ordered predicates.

`describeRegion()` uses a JavaScript `switch` to represent an equality-oriented simple CASE.

`evaluateRules()` provides a reusable first-match rule engine. Each rule contains a predicate and a label, making rule precedence explicit as data.

`calculateRegionalMetrics()` models conditional aggregation using a `Map` and a customer index. This demonstrates how `SUM(CASE ...)` can be understood operationally before a SQL engine performs the aggregation.

`buildBucketCase()` generates a validated SQL bucket expression. The implementation checks the SQL identifier with a strict regular expression, validates bucket ranges, and escapes generated string labels.

This JavaScript perspective is useful when an application needs to generate reporting queries from controlled business configuration.

## C++ Case Study

The C++ implementation models a repository-owned subscription-commerce reporting engine.

The system contains customers, orders, optional discounts, optional shipping information, numeric classifications, operational actions, and regional aggregate metrics.

`CaseEngine::classifySpend()` represents searched CASE semantics for customer segmentation.

`CaseEngine::describeRegion()` represents an equality-based simple CASE.

`CaseEngine::classifyDiscount()` uses `std::optional<double>` to model a SQL NULL discount.

`CaseEngine::bucketAmount()` implements mutually exclusive amount buckets.

`CaseEngine::operationalAction()` combines status, shipping time, and order amount to model a multi-column business rule with explicit precedence.

The `Rule` structure and `evaluateRules()` function provide a configurable first-match evaluator. This makes the relationship between predicate order and CASE behavior explicit.

The bucket validator sorts configured intervals and rejects overlapping ranges. Its sorting operation has `O(B log B)` complexity for `B` buckets.

Regional aggregation indexes customers by ID using `std::unordered_map`. This provides expected constant-time customer lookup for each order and allows the order-processing pass to remain approximately `O(O)` for `O` orders.

The use of `std::optional` is also deliberate. It makes missing values explicit rather than encoding them with sentinel numbers such as `-1` or `0`.

## CASE in ORDER BY

`CASE` is not restricted to the selected columns.

It can define a business-specific ordering:

    ORDER BY
        CASE order_status
            WHEN 'cancelled' THEN 1
            WHEN 'pending' THEN 2
            WHEN 'completed' THEN 3
            ELSE 4
        END,
        order_amount DESC

This allows query results to follow operational priority rather than alphabetical status order.

The Python implementation demonstrates this pattern by placing cancelled orders before pending and completed orders.

The classification expression is different from the ordering expression even though both use the same SQL `CASE` mechanism.

## CASE in HAVING

`CASE` can participate in grouped business logic.

The Python implementation calculates completed revenue with a conditional aggregate and then uses `HAVING` to retain customers whose completed revenue exceeds a threshold.

The conceptual sequence is:

    FROM and JOIN
        ↓
    GROUP BY
        ↓
    conditional aggregate
        ↓
    HAVING filter
        ↓
    SELECT classification

This differs from a row-level `WHERE` condition because the decision is based on a group-level result.

## Edge Cases

### Boundary values

Bucket thresholds must define what happens exactly at each boundary.

For example:

    WHEN amount < 5000 THEN 'Small'
    WHEN amount < 15000 THEN 'Medium'

means `5000` belongs to `Medium`.

The implementations explicitly test values such as `4999.99`, `5000`, `14999.99`, `15000`, `49999.99`, and `50000`.

### Missing values

A missing discount or shipping duration should not automatically become a valid business value.

Explicit `IS NULL` branches make missing information visible.

### Unknown categories

A simple CASE should normally include an `ELSE` when unexpected values are possible.

Without a matching branch, SQL `CASE` can return `NULL` when no `WHEN` condition matches and no `ELSE` is supplied.

### Overlapping rules

Overlapping predicates can make later branches unreachable.

This is especially dangerous when the rules appear independently reasonable but interact incorrectly.

### Negative numeric values

A business bucket defined for order amounts should specify what happens to negative amounts. The C++ implementation explicitly classifies negative amounts as `Invalid`, rather than silently assigning them to the smallest positive bucket.

## Common Mistakes

### Treating CASE as a statement

`CASE` is an expression. It returns a value and can be embedded in expressions such as `SELECT`, `ORDER BY`, aggregates, and conditional calculations.

### Reversing threshold precedence

A broad condition placed before a more specific condition can make the specific condition unreachable.

### Mixing inclusive boundaries carelessly

Rules such as `BETWEEN 0 AND 5000` and another range beginning at `5000` require deliberate handling of the shared boundary.

Half-open ranges such as `[0, 5000)` and `[5000, 15000)` are easier to reason about when represented through `>=` and `<`.

### Treating NULL as zero

`NULL` means the value is missing or unknown. It is not the same as an explicit numeric zero.

### Embedding untrusted text into generated CASE expressions

Dynamic SQL generation must distinguish SQL syntax from values. Parameter binding should be used for runtime values whenever the database interface supports it.

### Building an enormous CASE expression

A small set of stable business rules can be clear in SQL. A very large and frequently changing rule set can become difficult to test and maintain. In such cases, a reference table or dedicated rules structure may provide better separation of configuration and query logic.

## Performance Considerations

A `CASE` expression itself does not automatically make a query slow. Performance depends on the expressions used by its predicates, the amount of data processed, grouping requirements, joins, and whether expressions prevent useful index strategies.

A simple classification such as:

    CASE
        WHEN status = 'completed' THEN ...
        ELSE ...
    END

is generally inexpensive compared with operations such as large joins or aggregations.

Performance concerns become more significant when a CASE expression:

- contains expensive functions
- performs repeated calculations
- evaluates large numbers of branches for millions of rows
- is repeated across several query expressions
- prevents an otherwise useful access strategy because the expression is applied to an indexed column

Conditional aggregation is often preferable to running separate queries for each category when the same grouped dataset is required for multiple metrics.

The C++ implementation illustrates the same principle algorithmically by indexing customer records once rather than scanning the complete customer collection for every order.

## Security Considerations

`CASE` does not itself create SQL injection vulnerabilities. The risk appears when application code constructs SQL dynamically.

Values should be supplied through parameterized queries.

Identifiers that genuinely must be dynamic require a different approach because normal value parameters do not substitute for identifiers. The Python and JavaScript generators therefore validate column names against a conservative identifier pattern before inserting them into generated SQL.

Generated string literals must also be escaped correctly if they are being inserted into SQL syntax.

For production systems, a small allowlist of permitted columns and rule names is safer than accepting arbitrary SQL fragments.

## Testing and Debugging

CASE rules should be tested at the points where their behavior changes.

For a threshold of `5000`, tests should include values below the threshold, exactly at the threshold, and just above it.

For overlapping rules, tests should include values that satisfy multiple predicates.

For NULL-sensitive rules, tests should include `NULL`, zero, ordinary values, and unexpected values.

For business-rule CASE expressions involving several columns, tests should cover combinations that might conflict. For example, a cancelled order with a high amount should verify that the cancellation rule takes precedence over a high-value fulfillment rule.

The implementations intentionally expose these situations through executable examples rather than relying solely on descriptive text.

## Practical Relationship Between the Mechanisms

`CASE WHEN` is the decision mechanism.

Conditional transformation uses that mechanism to convert raw values into meaningful representations.

Bucketing uses ordered predicates to partition a numeric or temporal domain into categories.

Business rules use multiple conditions to encode operational or analytical policy.

Conditional aggregation combines CASE with aggregate functions so several metrics can be calculated from the same grouped dataset.

NULL handling ensures that missing information does not accidentally receive the semantics of an ordinary value.

Rule validation protects configurable CASE logic from ambiguous ranges and unintended precedence.

These are different uses of the same SQL expression mechanism, and maintaining that distinction makes complex reporting SQL easier to reason about and test.
