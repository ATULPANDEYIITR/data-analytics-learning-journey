# Pandas Combining Data

## Scope

This project studies how structured datasets are combined when their relationships are represented through keys, indexes, rows, and columns.

The central operations are:

| Operation | Main purpose | Relationship model |
|---|---|---|
| `merge()` | Combine records through one or more key columns | Relational join |
| `join()` | Combine data using indexes or aligned keys | Index-oriented combination |
| `concat()` | Stack or align complete objects | Row-wise or column-wise combination |
| `append()` alternative | Add records to an existing dataset | `concat()` |
| Relational operations | Identify matches, differences, and aggregates | Set and relational logic |

The important distinction is that these operations do not solve the same problem.

A merge asks which records are related through a key. A join commonly emphasizes index alignment. Concatenation combines objects along an axis without requiring a relational key. Set-difference operations identify records that do not have corresponding keys.

## Core Data Model

The implementations use a small customer-order domain.

    Customers
        |
        | customer_id
        v
    Orders
        |
        +--> order_id
        +--> amount
        +--> status

    Customers
        |
        +--> Customer Contacts
              |
              +--> email

    Monthly Imports
        |
        +--> January records
        +--> February records

The important relationships are:

- One customer can have many orders.
- A customer contact is modeled as one record per customer.
- Monthly order imports are naturally combined row-wise.
- An imported order can refer to a customer that does not exist in the master customer table.
- A customer can exist without any order.

These cases create meaningful matched and unmatched states.

## `merge()`

`merge()` is the primary relational combination mechanism.

A typical operation conceptually has the form:

`left.merge(right, on="customer_id", how="left")`

The key determines how records are related.

### Inner merge

An inner merge returns only records with matching keys on both sides.

    Customers:       1  2  3  4
    Orders:          1  2  2  3  5

    Inner result:    1  2  2  3

Customer `4` has no order and therefore disappears from an inner result. Order `104`, associated with customer `5`, also disappears because customer `5` does not exist in the customer relation.

### Left merge

A left merge preserves every record from the left DataFrame.

For customer data on the left, this means customer `4` remains present even though it has no order.

This is useful when the left DataFrame represents the authoritative population that must not be lost.

### Right merge

A right merge preserves records from the right DataFrame.

This can expose records that do not have corresponding left-side records.

### Outer merge

An outer merge preserves both sides.

The result can therefore contain:

- matched records
- left-only records
- right-only records

The `indicator=True` option is particularly useful for inspecting these states because pandas can identify whether a result came from the left relation, the right relation, or both.

## Join Cardinality

A key design issue is the expected relationship between the two datasets.

Common cardinalities include:

| Validation | Meaning |
|---|---|
| `one_to_one` | Each key occurs once on both sides |
| `one_to_many` | Each left key maps to zero or more right records |
| `many_to_one` | Multiple left records may reference one right record |
| `many_to_many` | Both sides may contain repeated keys |

The customer-order model is naturally one-to-many:

    Customer 1 -> Order 101
    Customer 2 -> Order 102
    Customer 2 -> Order 103
    Customer 3 -> Order 105

Using `validate="one_to_many"` turns an implicit assumption into an executable validation rule.

This is important because accidental duplicate keys can multiply output rows.

For example, if the left side contains two records for key `2` and the right side contains three records for key `2`, a many-to-many merge can produce six combinations for that key.

The resulting rows may be syntactically valid while being semantically wrong.

## `join()`

`join()` is particularly convenient when the relationship is expressed through indexes.

The Python implementation creates:

`customers.set_index("customer_id")`

and:

`contacts.set_index("customer_id")`

The two structures can then be combined using the shared index.

This makes the operation different in emphasis from a normal column-based merge.

The distinction can be expressed as:

    merge()
        column key
            |
            v
        relational matching

    join()
        index alignment
            |
            v
        index-oriented combination

The contact example represents a one-to-one relationship, so validation prevents duplicate contact records from silently changing the result shape.

## `concat()`

`concat()` combines complete pandas objects along an axis.

For monthly data:

    January
    101
    102

    +

    February
    103
    104
    105

    =

    Combined
    101
    102
    103
    104
    105

The operation does not need a relational key between January and February.

This makes concatenation fundamentally different from merging.

A merge asks:

> Which rows correspond?

Concatenation asks:

> How should these objects be placed together along an axis?

## Row-Wise Concatenation

With `axis=0`, records are stacked vertically.

This is the normal replacement for the historical DataFrame `append()` pattern.

Modern pandas does not provide `DataFrame.append()` as a separate row-addition API. The appropriate operation is `pd.concat()`.

For example, conceptually:

`pd.concat([old_data, new_data], ignore_index=True)`

combines the records while creating a new continuous positional index.

The implementation also demonstrates integrity checking with `verify_integrity=True`.

This can detect duplicate index values when index uniqueness is part of the data contract.

## Column-Wise Concatenation

With `axis=1`, objects are aligned horizontally.

Conceptually:

    Left                     Right

    customer_id              region
    1                        North
    2                        South

                |

                v

    customer_id  region
    1            North
    2            South

The alignment behavior makes indexes important. Two DataFrames with different indexes may produce missing values rather than simply pairing rows by their physical position.

This is one reason index semantics must be understood before using column-wise concatenation.

## Relational Operations

Combining data often requires more than a single merge.

The Python implementation explicitly calculates several relational states.

### Matched records

An inner merge identifies records with keys existing on both sides.

### Unmatched customers

The implementation uses membership testing to identify customers whose IDs do not occur in the orders relation.

This is equivalent to a relational anti-join.

    Customers
        -
    Customers having orders
        =
    Customers without orders

### Unmatched orders

The reverse membership test identifies order records whose customer IDs do not exist in the customer relation.

These are often called orphan records.

### Aggregation after combination

Once records have been related, `groupby()` can calculate customer-level totals.

The workflow is:

    Customers
        |
        v
    Merge with Orders
        |
        v
    Matched order records
        |
        v
    Group by customer
        |
        v
    Total amount
        |
        v
    Customer segment

This separates combination from aggregation.

The merge establishes relationships. The group operation calculates measures over those relationships.

## Collision Handling

When both DataFrames contain the same non-key column name, pandas needs a way to distinguish the values.

The Python implementation uses:

`suffixes=("_order", "_customer")`

This prevents ambiguous output columns.

Column collisions should not be treated as merely cosmetic. They can indicate that two datasets contain different meanings under the same field name.

For example:

    status_order
    status_customer

may represent two distinct states and should not be silently collapsed into one field.

## Validation and Failure Handling

The Python implementation validates required keys before merging.

It also rejects missing join keys for the controlled workflow.

Relationship validation is performed with pandas' merge validation options.

An intentional failure demonstrates what happens when a supposedly one-to-one relationship contains duplicate keys.

This is preferable to silently accepting a changed cardinality.

The PostgreSQL implementation reinforces similar rules at the database layer through primary keys, foreign keys, unique constraints, and check constraints.

## Python Implementation

The Python program uses:

- `DataFrame.merge()` for relational joins
- `DataFrame.join()` for index-oriented combination
- `pd.concat()` for row combination
- membership tests for relational differences
- `groupby()` for aggregation
- `dataclass` for operation results
- explicit validation functions
- merge cardinality validation
- assertions for final integrity checks
- exception handling for expected invalid relationships

The program is self-contained apart from pandas.

Its main design objective is to make data-combination behavior observable rather than hiding every operation inside a single transformation.

## JavaScript Implementation

The JavaScript implementation provides a complementary event-oriented model using native Node.js-compatible JavaScript.

It uses:

- `Map` for key-based indexing
- `Set` for membership and difference operations
- classes for validation errors
- object records for tabular data
- explicit merge functions
- row-wise concatenation
- column-wise combination
- aggregation by customer
- validation of one-to-one and one-to-many relationships

The `merge()` implementation constructs indexes with `Map`.

This gives expected linear behavior for key-based matching when hash-map operations are approximately constant time.

The implementation also handles overlapping column names through configurable suffixes.

No external npm dependency is required.

## C++17 Implementation

The C++ program models data combination as a repository-like relational processing engine.

Its domain structures are:

- `Customer`
- `Order`
- `MergedOrder`

The implementation uses:

- `unordered_map` for customer indexing
- grouped order maps for one-to-many relationships
- `set` and `unordered_set` for difference operations
- enums for join types and relationship constraints
- exception-based validation
- vector-based result materialization

The merge engine explicitly distinguishes:

- inner joins
- left joins
- right joins
- full joins

It also validates the expected relationship before producing results.

This design makes the cardinality contract part of the application logic.

## Java 17 Implementation

The Java implementation models data combination using explicit enterprise-style domain types.

It uses records for immutable data structures:

- `Customer`
- `Order`
- `Contact`
- `CombinedOrder`
- `CustomerTotal`

It uses enums for:

- join type
- relationship cardinality

The `DataService` class separates:

- input validation
- relationship validation
- merge execution
- aggregation
- concatenation
- set difference

The service returns immutable lists using `List.copyOf()`.

This makes the result of a combination operation less vulnerable to accidental mutation after the operation has completed.

The one-to-many customer-order relationship is represented explicitly instead of being inferred only from a particular query.

## PostgreSQL Implementation

The PostgreSQL script models the same conceptual domain relationally.

The main tables are:

| Table | Purpose |
|---|---|
| `customers` | Master customer relation |
| `customer_contacts` | One-to-one customer contact relation |
| `orders` | Customer order relation |
| `monthly_order_import` | Staging-style monthly data |

Database constraints enforce important invariants.

### Primary keys

Primary keys uniquely identify:

- customers
- contacts
- orders
- monthly import records

### Foreign keys

`orders.customer_id` references `customers.customer_id`.

`customer_contacts.customer_id` also references the customer table.

These constraints prevent invalid relationships from entering the normalized operational tables.

### Unique constraints

Customer email addresses are unique.

Customer contacts use the customer ID as their primary key, enforcing at most one contact row per customer.

### Check constraints

The database rejects:

- negative order amounts
- invalid order statuses
- blank customer names
- malformed basic email values

These constraints provide database-level validation independent of application code.

## SQL Join Operations

The SQL script demonstrates:

- `INNER JOIN`
- `LEFT JOIN`
- `FULL OUTER JOIN`
- anti-joins using `NOT EXISTS`
- aggregation after joins
- `UNION ALL` for row-wise combination

The SQL join model maps closely to pandas `merge()`.

For example:

    pandas                    PostgreSQL

    merge(..., how="inner")   INNER JOIN
    merge(..., how="left")    LEFT JOIN
    merge(..., how="outer")   FULL OUTER JOIN
    concat(axis=0)             UNION ALL
    anti-join                  NOT EXISTS
    groupby()                  GROUP BY

The mapping is conceptual rather than a claim that the APIs are identical.

## Transactional Integrity

The SQL script includes explicit transactions.

A valid order insertion is committed after the resulting state is inspected.

An invalid foreign-key operation is handled as an expected failure and rolled back.

This illustrates an important distinction between in-memory DataFrame validation and persistent database enforcement.

Pandas can detect invalid relationships while processing data. PostgreSQL can prevent invalid persistent relationships from being stored in constrained tables.

## Performance Considerations

For key-based combination, the main performance factors are:

- number of rows
- number of columns
- key cardinality
- duplicate key frequency
- output row count
- memory available for intermediate structures

Hash-based matching can provide approximately linear expected lookup behavior:

`O(n + m)`

where `n` and `m` represent the sizes of the two input datasets.

The actual cost can be higher when duplicate keys create a large Cartesian result.

For example:

    left key 7:   3 records
    right key 7:  4 records

    result for key 7:
    3 × 4 = 12 records

This is why cardinality validation is important.

For concatenation, the main cost is usually proportional to the number of records and columns that must be materialized.

## Memory Considerations

Pandas operations commonly create new objects rather than modifying both input DataFrames in place.

Large joins can therefore require substantial temporary memory.

Practical controls include:

- selecting only required columns before a merge
- using appropriate dtypes
- avoiding accidental many-to-many joins
- validating key relationships
- processing very large datasets in controlled batches where appropriate
- using database-side joins when the source data already resides in a relational database

The correct optimization depends on the data volume and workflow.

## Security Considerations

Data combination operations can expose sensitive information when datasets are joined too broadly.

Important controls include:

- select only required columns
- avoid joining sensitive fields unnecessarily
- validate dataset provenance
- avoid logging complete confidential rows
- control access to source files
- validate externally supplied data
- use parameterized database queries when SQL is constructed by an application
- avoid treating an imported identifier as trusted merely because it has the expected type

A join can increase the information content of a dataset even when neither source appears sensitive in isolation.

## Common Failure Modes

### Accidental many-to-many merge

Duplicate keys on both sides can multiply rows unexpectedly.

Use merge validation when the expected relationship is known.

### Missing keys

Null or invalid keys can produce surprising relationships.

Validate critical identifiers before combination.

### Column collisions

Identically named fields can become ambiguous.

Use explicit suffixes and inspect the resulting schema.

### Wrong join direction

A left join preserves the left dataset, not necessarily the records that a business user considers most important.

Choose the preserved side deliberately.

### Incorrect concatenation

Concatenation is not a replacement for a relational merge.

If two datasets represent the same entities and must be matched by a key, concatenating them can produce duplicated or structurally misleading records.

### Index misalignment

Column-wise concatenation depends on index alignment.

Two rows that appear visually adjacent are not necessarily combined if their indexes differ.

### Orphan records

External imports can contain identifiers absent from the master relation.

Detect these records explicitly before treating the combined dataset as authoritative.

## Practical Decision Rules

Use `merge()` when:

- two datasets share a business key
- records must be matched
- relationship cardinality matters
- the result depends on relational semantics

Use `join()` when:

- indexes naturally identify the relationship
- index alignment is central to the operation
- the data is already organized around compatible indexes

Use `concat()` when:

- datasets represent compatible slices of the same structure
- rows should be stacked
- columns should be aligned
- there is no need to match records through a relational key

Use an append alternative when:

- new rows must be added to an existing DataFrame
- the structures have compatible schemas
- `pd.concat()` can express the operation explicitly

Use set-difference logic when:

- unmatched records must be identified
- data-quality checks require orphan detection
- master and transaction populations must be reconciled

## Conceptual Separation

The complete workflow can be viewed as:

    Raw datasets
         |
         v
    Schema and key validation
         |
         +----------------------+
         |                      |
         v                      v
    Relational matching     Axis combination
         |                      |
         v                      v
    merge / join             concat
         |                      |
         +----------+-----------+
                    |
                    v
           Match / difference analysis
                    |
                    v
               Aggregation
                    |
                    v
            Validated result

The central engineering principle is to select the combination operation according to the relationship between the datasets rather than according to superficial similarity between their shapes.
