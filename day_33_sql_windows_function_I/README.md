# SQL Window Functions I

## Scope

This module focuses on the core SQL window-function model represented by `OVER`, `PARTITION BY`, and `ORDER BY`, with particular attention to `ROW_NUMBER`, `RANK`, and `DENSE_RANK`.

The central distinction is that a window function calculates information across a related set of rows while preserving the individual rows in the result. This makes window functions useful for ranking, ordered analysis, partition-level reporting, top-N analysis, and comparisons that would be awkward with ordinary aggregation alone.

The three implementations use a common sales-analysis scenario, but they approach the subject differently:

- The Python program builds a reusable executable model of window processing, including validation, CSV ingestion, ranking, top-N analysis, invariants, and a small performance model.
- The JavaScript program models window processing through `Map`, classes, higher-order transformations, deterministic sorting, event-driven reporting, asynchronous execution, and validation.
- The C++ program treats the subject as a typed repository-style analytics engine, using explicit domain structures, partition references, sorting policies, ranking semantics, validation, and complexity analysis.

The implementations are educational execution models. They demonstrate the semantics of the SQL constructs without attempting to implement a complete SQL parser or database optimizer.

## The window-function problem

Consider a sales table containing records such as:

| sale_id | employee | department | region | amount |
| ---: | --- | --- | --- | ---: |
| 105 | Isha | Sales | North | 12500 |
| 106 | Arjun | Sales | North | 9800 |
| 107 | Neha | Sales | South | 12500 |
| 108 | Vikram | Sales | South | 8100 |

Suppose the requirement is to identify the position of each sale within its department.

An ordinary aggregate such as `GROUP BY department` can calculate one total per department, but it cannot retain the individual sales as separate result rows. A window expression can calculate department-level information while leaving every sale available.

The conceptual distinction is:

`GROUP BY` changes the row grain by collapsing source rows into groups.

A window function normally preserves the row grain while calculating a value over a related window of rows.

This difference is the foundation for the rest of the module.

## `OVER`

`OVER` defines the window associated with a window function.

A simplified form is:

`function(...) OVER (...)`

The expression inside `OVER` can contain `PARTITION BY`, `ORDER BY`, or both, depending on the window function and the required calculation.

For example:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC)`

means that the rows are separated into department-specific windows and then ordered by descending amount inside each window.

The `ROW_NUMBER`, `RANK`, and `DENSE_RANK` functions all depend on the ordering of their window. Their output cannot be understood independently of the `ORDER BY` expression.

A window can also have no partitioning:

`ROW_NUMBER() OVER (ORDER BY amount DESC)`

In that form, the entire result set acts as one logical window.

A partition is therefore not the same thing as a physical database table, and it does not create a permanent table or subset. It defines the row population over which a particular window expression operates.

## `PARTITION BY`

`PARTITION BY` divides the input rows into independent logical groups for a window calculation.

For:

`RANK() OVER (PARTITION BY department ORDER BY amount DESC)`

Sales employees are ranked only against other Sales rows. Engineering employees are ranked only against Engineering rows. Finance employees are ranked only against Finance rows.

The same source result can therefore contain several independent ranking sequences.

This is different from filtering.

A condition such as:

`WHERE department = 'Sales'`

removes rows that do not satisfy the condition.

`PARTITION BY department` does not remove Engineering or Finance rows. It simply gives each department its own window.

### Compound partitions

Multiple columns can define a partition:

`PARTITION BY department, region`

This produces groups such as:

- Engineering + North
- Engineering + South
- Sales + North
- Sales + South
- Finance + North
- Finance + South

A row belongs to one combination of partition values.

The Python implementation demonstrates this through `partition_rows`, while the C++ implementation uses separate key builders for department-only and department-plus-region partitions. This makes the difference between one-dimensional and compound partitioning explicit.

### Partition boundaries

Ranking restarts at the beginning of each partition.

If a department contains four rows, its `ROW_NUMBER` values are:

`1, 2, 3, 4`

A different department also begins at:

`1, 2, 3, 4`

The number does not continue globally across departments.

This is one of the most important practical effects of `PARTITION BY`.

## `ORDER BY` inside a window

The `ORDER BY` in a window determines the sequence used by an ordered window function.

For:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC)`

the largest amount receives the earliest position.

Adding a secondary ordering expression is often important:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC, sale_id ASC)`

The amount determines the primary order. If two rows have the same amount, `sale_id` determines their relative position.

This is particularly important for `ROW_NUMBER`, because `ROW_NUMBER` must assign different numbers to different rows even when their primary ordering values tie.

### Ordering and determinism

Suppose two Sales records both contain an amount of `12500`.

With:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC)`

the two rows are tied according to the specified ordering expression, but `ROW_NUMBER` still needs to assign two different positions.

If an application requires reproducible row positions, a unique tie-breaker should be included:

`ORDER BY amount DESC, sale_id ASC`

The Python, JavaScript, and C++ implementations deliberately demonstrate this distinction.

`RANK` and `DENSE_RANK` should not use the unique tie-breaker when the intended meaning is to keep equal amounts tied. Adding `sale_id` to their ranking order would make the two otherwise equal amounts distinct for ranking purposes.

## `ROW_NUMBER`

`ROW_NUMBER` assigns a unique sequential number to rows in the window.

Conceptually:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC)`

produces something like:

| department | employee | amount | row_number |
| --- | --- | ---: | ---: |
| Sales | Isha | 12500 | 1 |
| Sales | Neha | 12500 | 2 |
| Sales | Arjun | 9800 | 3 |
| Sales | Vikram | 8100 | 4 |

The two `12500` rows receive different numbers.

`ROW_NUMBER` therefore answers a physical-position question:

> Which row occupies this position in the ordered partition?

This makes it useful for selecting a fixed number of rows from every group.

For example, after calculating the row number, an outer query can filter for:

`row_number <= 2`

That produces exactly two rows per department when enough rows exist.

This is different from asking for the top two distinct values.

## `RANK`

`RANK` gives equal ordering values the same rank.

For the Sales values:

`12500, 12500, 9800, 8100`

the ranks are:

`1, 1, 3, 4`

The rank jumps from `1` to `3` because two rows occupy the first position.

This is often called competition-style ranking.

`RANK` answers a different question from `ROW_NUMBER`:

> What competition position does this value occupy?

The Python self-tests explicitly verify this behavior. The C++ case study also checks that the two Sales records with `12500` receive rank `1`, while the `9800` record receives rank `3`.

## `DENSE_RANK`

`DENSE_RANK` also gives equal values the same rank, but it does not leave gaps.

For:

`12500, 12500, 9800, 8100`

the dense ranks are:

`1, 1, 2, 3`

The second distinct amount receives `2`, not `3`.

`DENSE_RANK` therefore answers a distinct-value ordering question:

> Which distinct ordering value is this?

This makes it useful when rank numbers should correspond to distinct value groups rather than physical row positions.

## The three functions side by side

For the ordered values:

`12500, 12500, 9800, 8100`

the result is:

| amount | `ROW_NUMBER` | `RANK` | `DENSE_RANK` |
| ---: | ---: | ---: | ---: |
| 12500 | 1 | 1 | 1 |
| 12500 | 2 | 1 | 1 |
| 9800 | 3 | 3 | 2 |
| 8100 | 4 | 4 | 3 |

The distinction is semantic rather than cosmetic.

| Function | Ties share a value? | Unique number per row? | Gaps after ties? |
| --- | --- | --- | --- |
| `ROW_NUMBER` | No | Yes | Not applicable |
| `RANK` | Yes | No | Yes |
| `DENSE_RANK` | Yes | No | No |

Choosing the function should follow the question being answered.

A requirement such as "return exactly the first two rows" usually aligns with `ROW_NUMBER`.

A requirement such as "show everyone tied for second place" can require `RANK` or `DENSE_RANK`, depending on the intended definition of the cutoff.

## Window aggregation versus grouped aggregation

A common source of confusion is the difference between:

`SUM(amount) GROUP BY department`

and:

`SUM(amount) OVER (PARTITION BY department)`

An ordinary grouped aggregate produces one result row for each department.

The window expression attaches the department total to each original sale.

For example:

| employee | department | amount | department total |
| --- | --- | ---: | ---: |
| Isha | Sales | 12500 | 37900 |
| Neha | Sales | 12500 | 37900 |
| Arjun | Sales | 9800 | 37900 |
| Vikram | Sales | 8100 | 37900 |

The Sales total appears on each Sales row because the window calculation operates over the department partition without changing the underlying row grain.

The Python function `window_sum_by_department` and the C++ `department_totals` implementation demonstrate this distinction directly.

## Logical execution perspective

A simplified conceptual workflow for a query using a window expression is:

`FROM` and joins establish the source rows.

`WHERE` removes rows that should not participate in the result at that stage.

`GROUP BY` and ordinary aggregates, when present, establish grouped results.

Window functions then calculate values over the rows available to the window stage.

A final ordering operation can determine presentation order.

The exact physical execution plan is database-engine dependent. The conceptual sequence is useful because it explains why window functions do not behave like ordinary filtering or grouping.

For example, a common pattern is to calculate a row number in an inner query and then filter that calculated value in an outer query.

The Python `top_n_per_department` function models this separation by first assigning `row_number` and then selecting rows whose value is within the desired limit.

## Top-N per group

A classic application is finding the top two sales representatives in every department.

The ranking expression can be modeled as:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY amount DESC, sale_id ASC)`

The subsequent filtering condition is based on the generated row number.

The advantage of `ROW_NUMBER` here is that the result contains at most two rows per department.

If tied values should all survive the cutoff, `RANK` changes the semantics.

For example, if three people share the highest amount and the request is "rank 1 and 2," `RANK <= 2` can return all three tied first-place rows.

This is not equivalent to `ROW_NUMBER <= 2`.

The Python implementation exposes both behaviors through `top_n_per_department` and `top_n_with_ties_per_department`. The JavaScript implementation provides corresponding `topNPerGroup` and `topNWithTies` functions. The C++ program implements both policies as separate functions so that the business rule is explicit.

## Python implementation

The Python program is a complete standard-library implementation of a small window-processing engine.

The `SalesRow` dataclass provides typed source records. Each record contains an identifier, employee, department, region, product, and monetary amount.

`partition_rows` models the logical effect of `PARTITION BY` by constructing independent collections keyed by partition values.

`order_rows` provides the window ordering mechanism. The implementation explicitly handles `None` values and supports ascending or descending expressions.

`add_row_number` demonstrates the unique sequence produced by `ROW_NUMBER`.

`add_rank` detects changes in the ordered value and assigns the physical position of the first member of each tie group.

`add_dense_rank` increments only when the ordering value changes, so tied values do not create gaps.

`WindowSpecification` provides a small representation of the important pieces of an `OVER` clause and can render expressions such as:

`OVER (PARTITION BY department ORDER BY amount DESC, sale_id ASC)`

The program also includes CSV validation, input validation, rank invariants, deterministic tie handling, top-N analysis, compound partitions, and a rough sorting-cost model.

The self-tests are particularly important because ranking functions have precise mathematical behavior. The tests verify that row numbers form a complete sequence within each department and that the Sales tie produces `RANK = 1`, followed by `RANK = 3`, while dense ranking produces `1` followed by `2`.

## JavaScript implementation

The JavaScript program uses a different design emphasis.

`Map` represents the relationship between a partition key and its member rows. This is a natural fit for dynamically grouped JavaScript objects.

`WindowSpecification` models the contents of `OVER`, including the partition and ordering expressions. Its `toSQL` method makes the relationship between the JavaScript configuration and SQL syntax visible.

The ordering mechanism uses an explicit comparator rather than relying on JavaScript's default sorting behavior. This matters because default comparison can produce unwanted coercion and does not express SQL-style ordering semantics clearly.

The JavaScript implementation uses copied row objects when applying window results. This prevents the original `sales` array from being unexpectedly mutated by each transformation.

The asynchronous leaderboard demonstrates an event-driven reporting pattern. `WindowReportEmitter` emits partition and completion events while `generateLeaderboardAsync` yields with `setImmediate`. The asynchronous structure does not make the sorting operation magically parallel; it demonstrates how an application can expose processing progress while remaining integrated with Node.js's event loop.

The implementation also validates simple CSV input, demonstrates top-N behavior, and checks ranking invariants.

## C++ case study

The C++ program models a typed analytics service for a sales organization.

The `Sale` structure represents a transaction with an integer identifier, employee, department, region, and amount stored in cents. Using integer cents avoids floating-point representation issues for the monetary values used by the case study.

`WindowSpecification` represents the `PARTITION BY` and `ORDER BY` components of a window expression and can render a SQL-like representation.

The partitioning layer uses references to source `Sale` objects. The function `build_partitions` groups records without duplicating the complete domain objects.

The ordering layer accepts explicit `OrderRule` objects. It supports amount, sale identifier, and employee ordering and can reverse the comparison for descending order.

The ranking engine deliberately separates the semantics of `ROW_NUMBER` from `RANK` and `DENSE_RANK`.

The deterministic leaderboard uses:

`ORDER BY amount DESC, sale_id ASC`

for `ROW_NUMBER`.

The tie-aware ranking engine uses only:

`ORDER BY amount DESC`

for `RANK` and `DENSE_RANK`.

This separation is critical. If `sale_id` were included in the ranking expressions, equal monetary values would no longer be treated as ties for ranking purposes.

The C++ case study also implements a window-style department total, top-N row selection, top-N-with-ties selection, compound department-and-region partitioning, validation, and executable invariants.

## Practical distinctions

### `PARTITION BY` versus `ORDER BY`

`PARTITION BY` determines which rows belong to the same logical window.

`ORDER BY` determines the sequence or value ordering within that window.

A query can partition without ordering when the window function only needs a partition-wide value.

Ranking functions generally require meaningful ordering because the result represents position relative to other rows.

### `ROW_NUMBER` versus `RANK`

`ROW_NUMBER` distinguishes individual rows.

`RANK` groups equal ordering values into the same rank.

If two rows have equal amounts, `ROW_NUMBER` still gives them separate positions, while `RANK` gives them the same position and creates a gap afterward.

### `RANK` versus `DENSE_RANK`

Both preserve ties.

`RANK` reflects the number of rows occupying earlier positions, so ties produce gaps.

`DENSE_RANK` reflects the number of distinct ordering values encountered, so ties do not produce gaps.

## Ties and secondary ordering

Ties require special attention.

Suppose two rows have:

`amount = 100`

If the business requirement is to assign a competition rank, both should remain tied.

Using:

`RANK() OVER (ORDER BY amount DESC)`

preserves that relationship.

If the requirement is instead to choose a deterministic first row, `ROW_NUMBER` can use:

`ORDER BY amount DESC, sale_id ASC`

The secondary expression resolves the physical ordering of equal primary values.

This is why the three ranking functions should not be treated as interchangeable implementations of "sort the rows."

## Common mistakes

### Treating `PARTITION BY` as a filter

`PARTITION BY department` does not remove other departments. It creates independent calculation windows.

A filter belongs to a filtering stage, not to the definition of a window partition.

### Using `ROW_NUMBER` when ties must be preserved

`ROW_NUMBER <= 3` can return exactly three rows from a partition but can split an equal-value tie.

If all records sharing a relevant rank must remain, a tie-aware function is more appropriate.

### Adding a unique column to a tie-aware ranking

Adding `sale_id` to:

`RANK() OVER (ORDER BY amount DESC, sale_id ASC)`

changes the definition of equality for the ranking expression.

Two records with equal amounts but different IDs no longer have identical complete ordering values.

The result can therefore cease to represent an amount-based tie.

### Forgetting the partition boundary

A ranking expression without `PARTITION BY department` ranks the entire result set as one window.

Adding `PARTITION BY department` restarts the ranking for every department.

### Assuming `ORDER BY` only controls final display

An `ORDER BY` inside `OVER` is part of the window calculation itself.

It determines how ranking and other ordered functions interpret the rows.

A final query-level `ORDER BY` controls presentation of the resulting rows. These are different roles.

## Edge cases

### Empty input

A production implementation must define behavior for an empty result set. The Python and JavaScript models reject empty input for operations that require an existing schema and partition population.

### Missing columns

A window expression cannot operate correctly if its partition or ordering column is absent.

The Python and JavaScript implementations explicitly validate required columns before calculation.

### Duplicate identifiers

The C++ case study treats `sale_id` as a unique transaction identifier and rejects duplicates during validation. This makes it suitable as a deterministic tie-breaker.

### Equal ordering values

Equal amounts are deliberately retained as ties for `RANK` and `DENSE_RANK`.

`ROW_NUMBER` requires an explicit deterministic ordering policy when stable output is important.

### Null-like values

SQL `NULL` ordering is database-specific in several respects. The Python and JavaScript educational models therefore use explicit handling rather than claiming to reproduce every database engine's NULL-ordering policy.

Production SQL should be tested against the specific database engine being used.

## Performance considerations

Window functions can require substantial work when partitions must be ordered.

If a partition contains `k` rows, a comparison sort is commonly associated with approximately `O(k log k)` ordering work. Across several partitions, the total sorting work can be represented conceptually as the sum of `k log k` for each partition.

Partition construction itself can often be performed in approximately `O(n)` time in an in-memory hash-based implementation.

The Python program includes a rough `n log n` growth demonstration. It is deliberately not presented as a database execution-cost estimator.

Actual database performance depends on the database engine, indexes, existing row order, cardinality, partition distribution, memory availability, parallel execution, sorting strategy, and the complete query plan.

Large partitions can be particularly expensive because ranking requires the database to establish the relevant order within those partitions.

## Determinism and reproducibility

A ranking result should be deterministic when downstream processes depend on the exact row position.

For `ROW_NUMBER`, use a complete ordering that distinguishes rows whenever the application requires reproducible output.

For example:

`ORDER BY amount DESC, sale_id ASC`

is more deterministic than:

`ORDER BY amount DESC`

when `sale_id` is unique.

For `RANK` and `DENSE_RANK`, do not add a tie-breaker merely for determinism if the tie itself is semantically meaningful. Instead, distinguish the two requirements:

- the ranking definition determines which values are equal
- the final presentation order can use a secondary ordering expression when necessary

Keeping these concerns separate prevents accidental changes to the business meaning of the ranking.

## Practical applications

Window functions are particularly useful when a report needs both row-level detail and context derived from neighboring or related rows.

The ranking functions demonstrated here support use cases such as:

- Department leaderboards where every transaction remains visible.
- Top-N records per department without collapsing departments into aggregate rows.
- Identification of the first, second, or third distinct performance level.
- Tie-aware qualification rules.
- Department-specific reporting where a global ranking would be misleading.
- Regional rankings created through compound partitions.
- Attaching partition-level totals to individual records.

The choice between `ROW_NUMBER`, `RANK`, and `DENSE_RANK` should follow the semantics of the report rather than being chosen solely because all three produce integer output.

## Security and data-quality considerations

Window functions do not automatically validate source data.

If a ranking depends on a monetary column, invalid negative values, duplicate transaction identifiers, missing departments, or malformed imported records can produce misleading output even when the SQL expression itself is syntactically correct.

The implementations therefore place validation around the window calculation.

The Python CSV loader validates required columns, numeric conversion, and non-negative amounts.

The JavaScript CSV parser validates headers, row widths, numeric identifiers, and finite non-negative amounts.

The C++ model validates identifiers, required textual fields, non-negative monetary values, and duplicate identifiers.

In a production database, validation should also be enforced at the schema and transaction layers rather than relying only on application-level checks.

## Debugging window queries

When a ranking query produces unexpected results, inspect the problem in this order:

- Verify the rows entering the window stage.
- Verify the exact `PARTITION BY` columns.
- Verify the exact `ORDER BY` columns and directions.
- Inspect tied ordering values.
- Check whether a unique secondary ordering expression is changing tie semantics.
- Compare `ROW_NUMBER`, `RANK`, and `DENSE_RANK` on a small controlled dataset.
- Confirm whether the requirement is about physical rows, competition positions, or distinct value positions.

A small dataset containing deliberate ties is especially effective for debugging.

For example, the sequence:

`100, 100, 90, 80`

makes the distinction immediately visible:

`ROW_NUMBER`: `1, 2, 3, 4`

`RANK`: `1, 1, 3, 4`

`DENSE_RANK`: `1, 1, 2, 3`

## Limitations of the implementations

These programs model the specified window-function concepts rather than implementing full SQL.

They do not parse arbitrary SQL statements, optimize relational execution plans, perform database indexing, or reproduce every vendor-specific behavior.

The Python implementation represents decimal money values accurately for the supplied calculations but is still an in-memory model.

The JavaScript implementation uses JavaScript `Number` values for the sample monetary amounts. A production financial application may require integer minor units, `BigInt`, or a decimal arithmetic library depending on the required precision and scale.

The C++ implementation stores monetary amounts as integer cents and provides stronger compile-time structure, but it also supports only the columns and ordering expressions explicitly implemented by the case study.

The implementations should therefore be read as executable semantic models rather than database-engine replacements.

## Relationship between the three implementations

The three programs represent the same SQL concepts at different technical levels.

The Python program emphasizes a transparent algorithmic model. Its functions make partitioning, ordering, ranking, validation, and testing easy to inspect.

The JavaScript program emphasizes application-oriented data processing. Its `Map` partition structure, object transformations, event emission, asynchronous reporting, and explicit comparator demonstrate how window-like processing can fit into an event-driven runtime.

The C++ program emphasizes a typed systems design. Its domain structures, references, partition maps, explicit ordering policies, validation rules, and complexity discussion show how a ranking engine could be structured when strong data representation and predictable resource behavior matter.

The underlying semantics remain the same:

`OVER` defines the window context.

`PARTITION BY` establishes independent row populations.

`ORDER BY` establishes the relevant sequence or value ordering.

`ROW_NUMBER` assigns a unique position.

`RANK` preserves ties and introduces gaps.

`DENSE_RANK` preserves ties without gaps.

The practical value of these functions comes from selecting the correct relationship between those mechanisms for the analytical question being answered.
