# SQL Performance: Query Plans, Indexes, Sequential Scans, Filtering Efficiency, and Join Optimization

## Scope

This laboratory examines SQL performance through five closely related but distinct areas:

- **Query plans** describe how the database intends to execute a statement and provide the evidence needed to compare estimated work with actual execution.
- **Indexes** provide alternative access paths to table data and are valuable when their structure matches real query predicates and ordering requirements.
- **Sequential scans** read a relation systematically and can be the correct plan when a large portion of the table is required or when an index would not reduce enough work.
- **Filtering efficiency** concerns how effectively predicates reduce the amount of data that must be read, carried through joins, sorted, grouped, or aggregated.
- **Join optimization** concerns the choice and cost of joining relations, including nested loops, indexed nested loops, hash joins, and the effect of cardinality estimates.

The six deliverables deliberately approach the subject differently. The Python program acts as a broad executable performance laboratory. The JavaScript program emphasizes event-driven execution traces and index-like data structures. The C++ program treats query planning as a systems case study. The Java program models the domain with enterprise-oriented types and services. The SQL script uses PostgreSQL itself to produce execution plans and enforce the relational model.

---

## Query Plans

A query plan is the database engine's selected execution strategy for a SQL statement. It is not simply a description of the SQL text. The optimizer transforms a declarative request into physical operations such as scans, joins, sorts, aggregations, and filters.

Typical PostgreSQL plan nodes relevant to this laboratory include `Seq Scan`, `Index Scan`, `Index Only Scan`, `Bitmap Index Scan`, `Bitmap Heap Scan`, `Nested Loop`, `Hash Join`, `Merge Join`, `Sort`, and `Aggregate`.

A plan normally contains estimated cost and cardinality information. With `EXPLAIN ANALYZE`, PostgreSQL also executes the query and reports actual row counts and timing. The comparison between estimated and actual cardinality is particularly important.

For example, a plan that estimates 20 rows but actually processes 200,000 rows is not merely slightly inaccurate. The difference can cause downstream decisions to become inappropriate. A nested loop that is excellent for 20 rows can be disastrous when its outer input actually contains 200,000 rows.

The SQL deliverable uses:

`EXPLAIN (ANALYZE, BUFFERS)`

so that estimated rows, actual rows, execution behavior, and buffer activity can be examined together.

### Estimated versus actual cardinality

Cardinality means the number of rows produced by an operation.

The Python, JavaScript, C++, and Java implementations model cardinality estimation explicitly. They compare the number of rows predicted by a simplified cost model with the number of rows observed from the generated workload.

PostgreSQL obtains cardinality estimates from statistics maintained by `ANALYZE`. Those statistics include information about value distributions and distinct-value estimates. Real workloads can still produce estimation errors because data may be skewed, predicates may be correlated, or the available statistics may not describe the relevant relationship precisely.

A large estimate-to-actual mismatch should therefore trigger investigation rather than an immediate conclusion that the index or join algorithm is wrong.

### Cost is not elapsed time

An estimated PostgreSQL cost is a planner unit, not a direct measurement in milliseconds.

The optimizer uses configurable cost parameters and statistics to compare alternative plans. Actual execution time depends on factors such as memory, cache state, storage behavior, CPU availability, concurrency, network effects, and the current state of the database.

The deliverables therefore use simplified cost formulas only to demonstrate the reasoning behind access-path selection. They do not claim to reproduce PostgreSQL's internal planner.

---

## Sequential Scans

A sequential scan examines a relation systematically rather than locating rows through an index.

A sequential scan is often a good plan when:

- the table is small;
- a query needs a large percentage of the rows;
- a predicate has low selectivity;
- no useful index exists;
- the physical access pattern makes sequential reading inexpensive.

A sequential scan should not be interpreted as a performance failure.

The laboratory workload deliberately includes a `status` column with only a few possible values. A query such as `status = 'paid'` can match a substantial fraction of the table. An index on such a low-cardinality column may not provide enough reduction in work to justify indexed access.

The Python program makes this visible by counting every row examined during a sequential scan.

The JavaScript implementation performs the same type of observation but uses JavaScript arrays and predicate functions.

The C++ case study exposes the cost of scanning through explicit iteration and records the number of rows examined.

The Java implementation models the same operation through a `Predicate<Order>` so that filtering logic remains separate from scan mechanics.

The SQL implementation lets PostgreSQL make the actual decision through `EXPLAIN`.

---

## Indexes

An index is an additional data structure maintained by the database to provide an alternative way of finding or ordering rows.

The main example uses a B-tree-oriented access pattern. The laboratory models indexes such as:

`orders(customer_id)`

and:

`orders(customer_id, order_date)`

The single-column index is useful for a selective customer lookup. The composite index extends that access pattern to a customer plus a date range.

### Index scan

An index scan generally uses the index to locate qualifying entries and then retrieves table rows as needed.

The existence of an index does not guarantee an index scan. PostgreSQL evaluates the estimated cost of alternative plans.

For a highly selective lookup such as:

`WHERE customer_id = 731`

an index can substantially reduce the number of rows examined.

For a broad predicate that returns a large fraction of a relation, a sequential scan can be cheaper.

### Composite index ordering

The ordering of keys matters.

An index defined conceptually as:

`(customer_id, order_date)`

places customer identity before date.

This structure naturally supports queries that first constrain `customer_id` and then restrict `order_date`.

The SQL deliverable tests:

`customer_id = 731 AND order_date >= ... AND order_date < ...`

and separately tests a date-only predicate.

This distinction is important because:

`(customer_id, order_date)`

is not simply interchangeable with:

`(order_date, customer_id)`

for every access pattern.

The C++ and JavaScript implementations model the same idea by grouping rows by customer and ordering those rows by date.

### Partial indexes

A partial index stores only rows satisfying an index predicate.

The SQL laboratory creates:

`idx_orders_paid_customer`

with a predicate equivalent to:

`status = 'paid'`

This can reduce index size and maintenance work compared with indexing every row when the workload repeatedly targets paid orders.

The index cannot be treated as a universal customer index because cancelled, refunded, pending, and shipped rows are not represented by that partial index.

The Python and Java implementations explain this distinction through explicit policy models rather than translating the SQL syntax directly.

### Covering indexes

The SQL laboratory also creates an index on `customer_id` with included payload columns:

`order_date` and `total_amount`.

The purpose is to demonstrate a covering-index design where the index can contain the columns required by a query's projection.

When PostgreSQL can satisfy the visibility requirements, this structure can permit an index-only scan and reduce heap access.

An index-only scan is not guaranteed simply because the index contains every selected column. PostgreSQL must also be able to determine tuple visibility efficiently, which is influenced by the visibility map and table maintenance.

### Index maintenance cost

Indexes improve some reads but impose costs on writes.

An insert into `orders` may require changes to several indexes. Updates affecting indexed columns can require additional index maintenance. Indexes also consume storage and may require vacuum and other maintenance work.

The correct question is therefore not "Should every frequently queried column have an index?" It is "Which indexes provide enough workload benefit to justify their storage and write-maintenance cost?"

---

## Filtering Efficiency

Filtering efficiency concerns how quickly a query reduces irrelevant rows.

Consider a predicate on an indexed date column:

`order_date >= DATE '2026-09-01' AND order_date < DATE '2026-10-01'`

This exposes a direct range relationship on the column.

By contrast, an expression such as:

`date_trunc('month', order_date) = ...`

changes the form of the predicate. A normal index on the raw `order_date` column may not provide the same direct access opportunity.

The SQL implementation demonstrates both patterns and then creates an expression index specifically for the expression-based access pattern.

This illustrates an important distinction: an expression is not inherently bad. The question is whether the physical design supports the expression used by the workload.

### Filtering before expensive operations

Filtering can reduce downstream work.

If a query joins one million orders to customers but only 10,000 orders fall within the requested date range, reducing the order relation before the join can substantially reduce subsequent processing.

The SQL script demonstrates filtered order data feeding a join and aggregation.

The same principle appears in the join implementations, where indexed access or early filtering reduces the number of rows that later operations must inspect.

### Sargability

A predicate is often described as sargable when its structure allows an index to be used effectively as a search argument.

Direct comparisons and ranges on indexed columns are common examples.

For date filtering, half-open ranges are often useful:

`order_date >= start_date AND order_date < end_date`

This avoids applying a transformation to every indexed value and provides a clear lower and upper boundary.

Sargability is not an absolute rule. Expression indexes, generated columns, specialized indexes, and other database features can support expressions that would otherwise prevent direct use of an ordinary index.

---

## Join Optimization

A join combines rows from two or more relations according to a relationship.

The optimizer must estimate:

- the size of each input;
- the expected number of matching rows;
- the usefulness of available indexes;
- the cost of building temporary structures;
- memory requirements;
- the cost of reading each relation;
- the expected result cardinality.

The C++ and Java programs implement three distinct join perspectives.

### Nested loop

A naive nested loop compares each row of one relation with rows of the other relation.

For inputs of sizes `N` and `M`, the comparison count can approach:

`O(N × M)`

This becomes expensive when both relations are large.

The C++ program deliberately restricts its naive nested-loop demonstration to a smaller sample so that the algorithm remains observable without performing an unnecessary production-scale Cartesian comparison.

### Indexed nested loop

An indexed nested loop uses one relation as the outer input and performs an indexed lookup into the inner relation.

This can be highly effective when the outer relation is small and each lookup returns only a small number of rows.

The important point is that "nested loop" does not automatically mean "slow." An indexed nested loop can be the correct plan for a selective lookup.

### Hash join

A hash join builds a hash structure for one input and probes it using the other.

For an equality join, expected work is approximately linear in the combined input sizes under normal hash behavior:

`O(N + M)`

Memory availability matters because a hash join needs working space. PostgreSQL can use more complex behavior when a hash operation does not fit comfortably in memory.

The JavaScript, C++, and Java implementations model hash joins with language-native hash structures.

### Merge join

A merge join is not implemented as the primary algorithm in the programs because the educational focus is on sequential scans, index scans, and the contrast between nested-loop and hash-join behavior.

In PostgreSQL, merge joins can be valuable when both inputs are available in compatible sorted order or can be efficiently sorted.

---

## Python Implementation

The Python program is the broadest executable laboratory.

It generates:

- customers;
- orders;
- products;
- order items.

It then models sequential scans, customer indexes, composite index behavior, partial-index reasoning, covering indexes, nested-loop joins, indexed nested-loop joins, hash joins, selectivity, simplified cost estimates, and estimated-versus-actual cardinality.

The `PlanNode` class provides an `EXPLAIN`-style representation containing estimated rows, actual rows, costs, and rows removed by filters.

The Python implementation also deliberately distinguishes theoretical cost from production database execution. It does not pretend that a dictionary is an actual PostgreSQL B-tree or that a simplified formula reproduces PostgreSQL's planner.

---

## JavaScript Implementation

The JavaScript program uses Node.js standard-library capabilities and approaches SQL performance through an event-driven execution model.

`Map` structures represent hash-style lookup indexes. A customer index groups orders by `customerId`, while the composite-index demonstration sorts each customer's rows by date and uses binary search to locate a range boundary.

The `QueryExecutionTrace` class demonstrates an event-driven way to observe stages of simulated execution. Events such as `scan:start`, `scan:finish`, and `query:finish` separate execution instrumentation from the query operation itself.

This perspective is useful because real database performance work frequently involves observing execution rather than only reading SQL text.

The program also contrasts sequential scans with indexed lookups and compares nested-loop, indexed nested-loop, and hash-join operation counts.

---

## C++ Case Study

The C++ program treats query performance as a systems-level cost problem.

Its order workload contains 100,000 orders and 10,000 customers. A `CustomerIndex` maps customer identifiers to pointers into the order collection.

The case study uses explicit data structures to expose the work performed by different access strategies.

The composite-index simulation sorts each customer's order pointers by day and uses `std::lower_bound` to locate the beginning of a date range. This gives a concrete algorithmic representation of why a composite key can support equality followed by a range condition.

The program compares:

- naive nested-loop comparisons;
- indexed nested-loop lookups;
- hash-join probes.

The naive nested loop runs only on a reduced sample because its `O(N × M)` behavior would otherwise dominate execution time without adding useful evidence.

The program also reports cardinality estimates and warns when estimated and actual row counts differ by a large factor.

---

## Java Implementation

The Java implementation uses an enterprise-oriented service model.

Immutable records represent `Customer`, `Order`, `PlanEstimate`, and `ExecutionResult`.

The `CostModel` interface separates plan estimation from query execution. `SimpleCostModel` provides a deliberately simplified cost model, while `QueryExecutionService` handles sequential scans, indexed lookups, and plan selection.

The `JoinEngine` isolates join strategies so that their operation counts can be compared without embedding join logic into unrelated application code.

Java's `Predicate<Order>` is used to represent query filtering behavior. This allows the scan mechanism to remain independent of the actual business predicate.

Validation is implemented through exceptions for invalid cost parameters and impossible cardinality values. This reflects an enterprise design principle in which invalid planning assumptions are rejected at the boundary rather than silently producing misleading results.

---

## PostgreSQL Data Model

The SQL implementation creates a dedicated schema containing:

| Relation | Performance role |
| --- | --- |
| `customers` | Join dimension with region and tier attributes |
| `products` | Product dimension used by order-item aggregation |
| `orders` | Main high-volume fact-like relation for scan and index experiments |
| `order_items` | Many-to-one order and product relationship used in multi-table joins |

The relationships are enforced with foreign keys.

The `orders` table contains:

- `order_id` as the primary key;
- `customer_id` as a foreign key;
- `order_date` for temporal filtering;
- `status` for low-cardinality filtering;
- `total_amount` for aggregation.

The `order_items` table uses a uniqueness constraint on `(order_id, product_id)` so that the same product cannot appear twice in one order row set.

---

## SQL Index Design

The SQL laboratory creates several deliberately different indexes.

`idx_orders_customer` supports selective equality access by customer.

`idx_orders_customer_date` supports a customer equality condition followed by a date range.

`idx_orders_paid_customer` is a partial index restricted to paid orders.

`idx_orders_month_expression` supports the specific `date_trunc` expression used in the corresponding demonstration.

`idx_orders_customer_covering` uses `INCLUDE` columns to demonstrate a covering-index design.

Each index has a different purpose. They are not interchangeable.

The script also runs `ANALYZE` after data loading and index creation so that PostgreSQL has current statistics for its planning decisions.

---

## SQL Query Plan Analysis

The SQL script repeatedly uses:

`EXPLAIN (ANALYZE, BUFFERS)`

This is more informative than measuring only total elapsed time because the execution plan identifies the physical operators responsible for the work.

Useful observations include:

- whether a sequential scan or index access was selected;
- estimated rows compared with actual rows;
- whether a bitmap strategy was chosen;
- which join algorithm was selected;
- whether a covering index enables an index-only scan;
- how much buffer activity occurred;
- whether a sort or aggregation becomes a major operation.

The plan must be interpreted in the context of the actual workload.

---

## Join Filtering and Cardinality

The SQL examples join `customers` and `orders` using `customer_id`.

A selective condition on the customer relation can reduce the number of relevant customer rows. A date or status predicate on orders can reduce the fact-side input.

The optimizer must estimate the resulting join cardinality.

If the estimates are badly wrong, the selected join algorithm can also become inappropriate.

For example, a nested loop selected under the assumption that the outer relation contains a few rows can become expensive if the outer relation actually contains hundreds of thousands of rows.

This is why cardinality estimation is a central part of join optimization rather than a secondary diagnostic detail.

---

## Query Plan Failure Modes

### Large cardinality mismatch

If a plan estimates a small number of rows but actually processes a much larger number, investigate:

- stale statistics;
- skewed distributions;
- correlated predicates;
- inadequate statistics;
- changes in workload or data volume.

The correct response is not automatically "add an index."

### Unexpected sequential scan

A sequential scan may be correct when the query returns a large proportion of the table.

If the query should be highly selective, investigate:

- predicate shape;
- available indexes;
- data distribution;
- statistics;
- implicit casts;
- expressions on indexed columns;
- estimated versus actual cardinality.

### Index scan that is slower than a sequential scan

An index can locate qualifying entries efficiently but still require many random heap accesses.

When a large fraction of the relation qualifies, the cumulative table access can cost more than reading the relation sequentially.

This is one reason index presence alone is not sufficient evidence for good performance.

### Poor join choice

An inappropriate join strategy can result from incorrect cardinality estimates, insufficient indexes, memory constraints, or an access pattern that differs from the workload used when the plan was evaluated.

The SQL laboratory allows join-strategy inspection with `EXPLAIN` and uses temporary planner settings as diagnostic experiments.

---

## Performance Trade-offs

Performance engineering involves trade-offs rather than universal rules.

| Decision | Benefit | Cost or limitation |
| --- | --- | --- |
| Sequential scan | Simple, efficient for broad reads | Reads rows that may later be discarded |
| Single-column index | Efficient selective lookup | Additional storage and write maintenance |
| Composite index | Supports multi-column access patterns | More storage and key-order constraints |
| Partial index | Small, focused access path | Only useful for predicates covered by its condition |
| Covering index | Can reduce heap access | Larger index and additional maintenance |
| Nested loop | Excellent for small outer inputs and selective inner access | Can become expensive as outer cardinality grows |
| Hash join | Efficient equality joins for suitable workloads | Requires memory and can spill |
| Expression index | Supports a specific computed predicate | Adds a specialized index and maintenance overhead |

---

## Common Performance Mistakes

### Treating every sequential scan as a defect

A sequential scan can be the most efficient plan for a broad analytical query.

### Creating an index for every WHERE column

Indexes are not free. Excessive indexing increases storage requirements and write overhead.

### Ignoring composite key order

A composite index should be designed around actual predicates and ordering requirements. Changing key order can substantially change which queries benefit.

### Looking only at execution time

Execution time alone does not explain why a query behaved as it did. The execution plan, actual row counts, buffer activity, and operator behavior provide more diagnostic information.

### Optimizing without representative data

A plan that performs well on a small development table may behave differently at production scale.

### Ignoring writes

An index that makes one report faster can increase the cost of every insert or update affecting its indexed columns.

### Assuming one plan is permanently optimal

Data distribution, table size, statistics, cache state, and workload characteristics change. Query performance should be evaluated as the workload evolves.

---

## Security and Operational Considerations

Performance tuning should not weaken database security or integrity.

The SQL schema keeps referential integrity in the database through foreign keys and uses check constraints for valid statuses, tiers, regions, quantities, prices, and order amounts.

Application-level validation is useful, but database constraints remain important because multiple applications, scripts, batch processes, or administrative tools may write to the same database.

Performance experiments should also avoid destructive production operations. Index creation on a production-sized relation can have operational consequences, and PostgreSQL's `CREATE INDEX CONCURRENTLY` may be appropriate when minimizing blocking is important.

Execution-plan analysis should use representative but appropriately protected data. Sensitive production information should not be copied into development environments merely for benchmarking.

---

## Production Validation

The practical workflow demonstrated by these deliverables is:

- identify the slow or high-impact SQL statement;
- inspect the actual execution plan;
- compare estimated and actual cardinalities;
- determine whether filtering is selective enough to benefit from indexed access;
- inspect join algorithms and join cardinalities;
- evaluate whether the current index structure matches the predicate pattern;
- consider write and storage costs before adding an index;
- test with representative data;
- measure again after the change.

The critical diagnostic statement is:

`EXPLAIN (ANALYZE, BUFFERS)`

A proposed optimization should be judged from actual evidence rather than from the existence of an index or a general assumption that one access method is always faster.

---

## Relationship Between the Core Areas

The five performance areas form a connected chain without being interchangeable.

A **query plan** is the optimizer's physical execution strategy.

An **index** is one possible access structure that can influence that strategy.

A **sequential scan** is another access path and may be optimal when filtering is not selective.

**Filtering efficiency** determines how much irrelevant data is eliminated before later work.

**Join optimization** determines how relations are combined after the optimizer considers their estimated cardinalities, available access paths, and expected costs.

The relationship can therefore be expressed as:

`SQL predicate → selectivity estimate → possible access paths → filtering work → join cardinality → join strategy → execution`

The key engineering lesson is that these decisions interact. Adding an index can change an access path, which can change the rows entering a join, which can change the preferred join algorithm. A change that appears local at the SQL-text level can therefore alter the entire execution plan.

---

## Technical Boundary of the Simulations

The Python, JavaScript, C++, and Java programs use simplified models rather than implementing PostgreSQL internally.

They intentionally omit engine-specific behavior such as:

- PostgreSQL's complete cost model;
- visibility-map details;
- MVCC tuple visibility;
- buffer-cache state;
- table and index bloat;
- parallel query planning;
- work-memory spill behavior;
- extended statistics;
- bitmap heap internals;
- physical page layout;
- vacuum behavior;
- concurrent transactions.

Their purpose is to make access-path and join reasoning executable and observable.

The PostgreSQL script provides the engine-backed portion of the laboratory where actual query plans can be inspected.

---

## Practical Interpretation

Good SQL performance is not achieved by mechanically replacing sequential scans with index scans.

The correct objective is to minimize the total cost of the workload.

That can mean:

- retaining a sequential scan;
- adding a selective index;
- changing a composite index key order;
- using a partial index;
- improving predicate shape;
- reducing rows before a join;
- correcting statistics;
- changing a join strategy;
- or removing an index that provides insufficient benefit for its maintenance cost.

The strongest evidence comes from the relationship between the SQL statement, the execution plan, actual cardinalities, buffer activity, and representative workload behavior.
