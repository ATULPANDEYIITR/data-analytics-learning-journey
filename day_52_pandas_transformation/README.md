# Pandas Transformation: apply, map, replace, assign, rename, Sorting, Filtering, and Vectorized Operations

## Scope

This project studies dataframe transformation as a data-processing workflow rather than as isolated Pandas functions.

The central pipeline transforms order data through:

- validation
- vectorized arithmetic
- value mapping
- categorical replacement
- row-aware `apply`
- derived-column construction with `assign`
- schema-oriented renaming
- boolean filtering
- stable sorting
- vectorized string operations
- aggregation
- CSV persistence and reload
- explicit validation failure handling

The same domain is represented through Python, JavaScript, C++17, Java 17, and PostgreSQL, but each implementation uses mechanisms appropriate to its language or execution environment.

## Transformation Model

The source dataset contains commercial orders with customer, region, product, quantity, price, and status information.

A simplified transformation flow is:

`Raw Orders`
→ `Validation`
→ `Derived Gross Amount`
→ `Mapped Region Code`
→ `Normalized Status`
→ `Priority Classification`
→ `Discount Assignment`
→ `Net Amount`
→ `Filtering`
→ `Sorting`
→ `Regional Reporting`

The original order attributes remain useful for auditing. Derived attributes represent analytical transformations rather than replacement of the original business record.

## Core Pandas Operations

### Vectorized operations

The Python implementation calculates gross order value with:

`quantity * unit_price`

Pandas performs this operation across the complete Series. No explicit Python loop is required.

Vectorization is generally preferred when the operation can be expressed using arithmetic, comparison, string methods, or other operations implemented efficiently over arrays.

For the order dataset, vectorized arithmetic is preferable to calling a Python function for every row because the calculation has no row-specific control flow beyond the values already present in the columns.

### `map`

`map` is used for one-to-one transformations.

The region values:

`North`, `South`, `East`, `West`

are mapped to:

`N`, `S`, `E`, `W`.

This is a useful distinction from `apply`. A dictionary mapping directly expresses a lookup relationship and does not require a general-purpose row function.

The implementation also handles an unmapped value with `fillna("UNKNOWN")`, avoiding an accidental assumption that every source value is valid.

### `replace`

`replace` normalizes known categorical values.

The source status values are lowercase:

`completed`, `pending`, and `cancelled`.

They are transformed into consistent display values:

`Completed`, `Pending`, and `Cancelled`.

This is different from a dictionary lookup whose purpose is to derive another field. `replace` changes selected values in an existing column.

### `apply`

`apply` is used for priority classification because the decision depends on the derived monetary value and contains multiple conditional branches.

The classification is:

| Net amount | Priority |
|---:|---|
| 100000 or more | High |
| 30000 to less than 100000 | Medium |
| Less than 30000 | Low |

`apply(axis=1)` receives a row and therefore provides greater flexibility than a simple Series mapping.

That flexibility has a performance cost. For large datasets, a vectorized expression using `numpy.where`, `Series.mask`, or `Series.cut` is generally preferable when the logic can be expressed without Python-level row calls.

### `assign`

`assign` creates derived columns while keeping transformations composable.

The Python implementation uses it to calculate:

- `discount_rate`
- `net_amount`

The discount policy is:

| Gross amount | Discount |
|---:|---:|
| 100000 or more | 10% |
| 50000 to less than 100000 | 5% |
| Less than 50000 | 0% |

`assign` is useful when several transformations should be expressed as a readable pipeline without repeatedly modifying the source dataframe through separate statements.

### `rename`

`rename` changes analytical column names without changing their values.

The example changes:

`gross_value` → `gross_amount`

and:

`net_value` → `net_amount`.

This separates schema presentation from the underlying calculations.

### Filtering

Boolean filtering selects records based on conditions.

The active-order selection excludes cancelled orders and retains orders whose net value is at least 30000.

The condition is conceptually:

`status != Cancelled AND net_amount >= 30000`

Pandas requires parentheses around individual comparisons when combining conditions with `&` and `|`.

The implementation also demonstrates `query` for expressions where a dataframe-oriented filtering syntax improves readability.

### Sorting

The transformed active orders are sorted by:

1. priority
2. net amount

Priority is ordered from high to low operational importance, while monetary value is ordered descending within a priority.

A stable sorting algorithm is selected so that records with equal sorting keys retain a predictable relative order.

### Vectorized string operations

Customer names are normalized with Pandas string methods.

The operation uses:

`str.strip()`

followed by:

`str.title()`

This demonstrates vectorized string processing instead of calling a Python function separately for every record.

## Python Implementation

The Python program is the most dataframe-oriented implementation.

It constructs an order dataframe, validates required fields, and then applies transformations in stages.

The validation layer checks:

- required columns
- unique order identifiers
- positive quantities
- non-negative unit prices

The transformation pipeline then derives monetary and classification fields.

The script also writes transformed data to a temporary CSV, reloads it, validates the reloaded data, and creates another transformed representation. This tests the boundary between in-memory dataframe processing and persistent tabular data.

A deliberate invalid quantity is introduced at the end to demonstrate that invalid input produces an explicit `ValueError` rather than silently entering the transformation pipeline.

## JavaScript Implementation

The JavaScript implementation does not attempt to reproduce the Pandas API.

Instead, it models the same transformation concepts using native collection operations.

`Array.map()` performs record transformation.

`Map` is used for controlled lookup behavior, corresponding conceptually to dictionary-based Pandas mapping.

`Array.filter()` handles record selection.

`Array.sort()` provides ordering, with a copied array used before sorting so that the original collection is not unexpectedly mutated.

Objects created with spread syntax preserve source attributes while adding derived properties.

The implementation also uses an asynchronous processing boundary. This is relevant when a transformation pipeline eventually receives data from a database, HTTP API, stream, or other asynchronous source.

Validation is performed before transformation so malformed records cannot silently propagate through later operations.

## C++17 Implementation

The C++ program treats transformation as an explicit domain-processing engine.

`Order` is a structured domain record containing both source and derived fields.

`RepositoryTransformationEngine` owns the transformation rules and validation logic.

The implementation uses:

- `unordered_map` for constant-time categorical lookups
- `unordered_set` for duplicate-ID detection
- `copy_if` for filtering
- `stable_sort` for deterministic ordering
- `map` for ordered regional aggregation
- exceptions for invalid input

The design makes mutation explicit through references and returned containers.

This is materially different from dataframe semantics. C++ requires the implementation to make memory ownership, mutation, collection types, and algorithm selection explicit.

The main transformation pass is linear in the number of orders.

Sorting introduces `O(n log n)` time complexity.

The validation pass uses additional storage proportional to the number of unique order identifiers.

## Java 17 Implementation

The Java implementation models transformation as an enterprise-style service.

The immutable `Order` record represents validated source data.

`TransformedOrder` represents the result of transformation without mutating the original order.

The domain uses enums for:

- order status
- priority

This prevents arbitrary strings from representing known business states inside the core domain model.

`TransformationService` contains transformation and filtering behavior.

The service uses Java Streams for:

- transformation
- filtering
- sorting
- regional aggregation

Validation occurs at the domain boundary and includes duplicate identifier detection.

Immutable records are useful when transformed results should not be modified accidentally after processing.

## PostgreSQL Implementation

The SQL implementation moves transformation concerns into a relational model.

The schema contains:

- `customers`
- `regions`
- `orders`
- `order_transformations`

PostgreSQL enums represent controlled states for order status and priority.

Foreign keys preserve relationships between customers, regions, and orders.

Check constraints prevent:

- blank product names
- non-positive quantities
- negative unit prices
- invalid discount rates
- invalid monetary values

The transformation function calculates gross amount, discount, net amount, and priority.

A trigger refreshes the transformation when quantity or unit price changes. This prevents a previously calculated transformation from becoming stale after a source order is modified.

The reporting view combines source and derived information into a queryable representation.

## Relational Transformation Workflow

The SQL workflow can be represented as:

`customers`
→ `orders`
→ `transform_order()`
→ `order_transformations`
→ `transformed_order_report`
→ `filtered / sorted / aggregated reports`

The original order remains stored independently from derived analytical values.

This is useful when transformation results need to be audited, queried repeatedly, or refreshed after source changes.

## Transformation and Mutation Distinctions

The operations are related but not interchangeable.

| Operation | Primary purpose | Typical input | Result |
|---|---|---|---|
| `map` | One-to-one value mapping | Series | Transformed values |
| `replace` | Substitute known values | DataFrame/Series | Normalized values |
| `apply` | Custom function | Series/DataFrame | Function-dependent result |
| `assign` | Add or derive columns | DataFrame | DataFrame with new columns |
| `rename` | Change labels | DataFrame | DataFrame with renamed labels |
| Filtering | Select records | Boolean condition | Subset |
| Sorting | Order records | Columns/keys | Ordered dataframe |
| Vectorization | Efficient array operations | Series/DataFrame | Computed values |

A common source of inefficient Pandas code is using `apply` for calculations that can be expressed directly with vectorized operations.

For example, multiplication of quantity and price should be written as a vectorized expression rather than as a row-wise function.

## Edge Cases

The implementations explicitly account for several data-quality problems.

### Missing columns

The Python validator checks for required fields before transformation begins.

Without this validation, a misspelled column name could cause a failure much later in a pipeline.

### Duplicate identifiers

Order identifiers are expected to be unique.

Python, C++, and Java explicitly detect duplicate IDs.

The PostgreSQL schema enforces uniqueness through the primary key.

### Invalid quantities

A quantity of zero is rejected.

Negative quantities are also rejected because the domain model treats the order quantity as a positive purchase quantity.

### Negative prices

Negative unit prices are rejected at validation time.

The PostgreSQL implementation also enforces the rule through a database check constraint.

### Unknown categories

Unknown region values do not cause the mapping operation to invent a valid region.

The Python and JavaScript implementations use an explicit `UNKNOWN` representation.

This is safer than silently assigning an unrelated category.

### Cancelled orders

Cancelled orders remain in the transformed dataset for traceability but are excluded from the active-order operational view.

This demonstrates the distinction between transformation and filtering.

Transformation does not necessarily mean deletion.

## Performance Considerations

Vectorized Pandas operations should normally be preferred over row-wise `apply` when equivalent vectorized logic exists.

For example, arithmetic on entire Series is generally more efficient than invoking Python code once for every row.

Sorting is more expensive than simple filtering because sorting requires ordering the selected records.

Dictionary-based mapping is appropriate when each source value has a direct target value.

For very large datasets, memory usage becomes important because multiple derived columns increase the dataframe footprint.

Repeated copies should be avoided when they do not provide a correctness benefit.

The SQL implementation uses indexes on status/region and net amount because the demonstration queries filter or order on those attributes.

Indexes should be selected from actual query patterns rather than added to every column.

## Security and Data Integrity

Transformation code should not assume that input data is trustworthy.

Validation protects the application layer, while database constraints provide a second enforcement boundary.

The PostgreSQL schema therefore validates critical invariants independently of client code.

The SQL transformation function raises an exception when an unknown order identifier is requested.

The Python implementation rejects malformed data before processing.

The Java implementation rejects invalid domain objects at construction time.

The JavaScript implementation validates records before transformation.

This layered approach reduces the chance that invalid data becomes a valid-looking analytical result.

## Failure Boundaries

The implementations deliberately fail when required invariants are violated.

A transformation should not convert invalid source data into apparently valid analytical output.

The practical boundary is:

`Input validation → Transformation → Filtering → Reporting`

Validation errors should be handled before reporting or persistence.

For database workflows, transactions provide an additional boundary so failed writes can be rolled back without leaving partially transformed state.

## Practical Interpretation

The project distinguishes transformation from selection.

A transformation changes or derives representation.

A filter selects records.

A sort changes order.

A mapping changes values according to a known relationship.

A custom function provides flexible business logic.

A vectorized operation expresses calculations over complete columns.

These distinctions matter because choosing the wrong mechanism can affect readability, correctness, execution speed, and memory consumption.

The five implementations preserve the same business scenario while deliberately using different computational models: Pandas dataframe operations, JavaScript collection processing, C++ algorithmic containers, Java domain services and immutable records, and PostgreSQL relational transformations.
