# Python Data Structures: A Practical Technical Study

## Scope

This project examines lists, tuples, sets, dictionaries, nested structures, and comprehensions through a repository inventory and deployment analytics system. The implementations demonstrate how collection choices influence data integrity, lookup speed, mutation, aggregation, and the design of maintainable software.

The Python script, JavaScript file, C++ program, Java application, and PostgreSQL script use different approaches to related operational problems. Each implementation is executable independently and uses standard language facilities or PostgreSQL features rather than unnecessary third-party dependencies.

## Core collection models

| Structure | Primary purpose | Typical operations | Important limitation |
|---|---|---|---|
| List | Preserve ordered records and allow mutation | Indexing, slicing, append, removal, iteration | Membership is linear in the worst case |
| Tuple | Represent a fixed sequence of values | Indexing, unpacking, iteration | The sequence cannot be reassigned, but contained mutable objects may change |
| Set | Maintain distinct hashable elements | Membership, union, intersection, difference | Elements must be hashable, and ordinary sets do not provide a meaningful business ordering |
| Dictionary | Associate keys with values | Lookup, insertion, replacement, deletion | Keys must be hashable |
| Nested structure | Represent hierarchical records and relationships | Chained lookup, traversal, aggregation | Deeply nested mutable objects can be difficult to validate and maintain |
| Comprehension | Build a collection through transformation and filtering | Mapping, filtering, flattening | Complex expressions can reduce readability |

These structures are not interchangeable. A list is appropriate when the order of deployment events matters. A set is suitable for comparing required and completed checks. A dictionary is effective when a repository name identifies one record. Nested dictionaries and lists can represent JSON payloads received from APIs. Comprehensions provide concise transformations of those structures.

## Lists and sequence behavior

The Python implementation maintains repository names in a list and modifies the collection using `append`, `insert`, indexed assignment, and `pop`. It also demonstrates slicing and slice assignment.

A slice such as `values[1:4]` produces a new list containing references to the selected elements. For a list of immutable integers, this distinction is usually unimportant. For a list of mutable dictionaries, the copied list and original list can still reference the same dictionaries.

The script demonstrates this distinction with nested lists. Calling `copy()` creates a shallow copy, while `deepcopy()` recursively copies supported nested objects. Deep copying can be useful for independent snapshots, although it may be expensive and is not always suitable for objects that represent external resources.

Repeated references are another important issue. Constructing a matrix with `[[0] * 3] * 2` creates two references to the same inner list. Changing one row therefore changes both displayed rows. A nested comprehension creates independent rows.

Lists are well suited to ordered event histories, batches of records, and output reports. They are less appropriate as the sole data structure for repeated membership checks against a large collection.

## Tuples and record integrity

Tuples represent fixed sequences such as a release identifier, version, and environment. Tuple unpacking assigns each component to a descriptive variable and makes the expected record shape explicit.

A tuple is immutable at the sequence level. Its elements cannot be replaced through item assignment. This does not imply that every object referenced by the tuple is immutable. A tuple containing a list can still expose changes to that list.

Tuples can also serve as dictionary keys when all their elements are hashable. A pair such as `("market-prism", "production")` can identify a release configuration. A tuple containing a list cannot be hashed and therefore cannot be used as a dictionary key.

For larger domain records, a dataclass or an explicit class can be clearer than a tuple because each field has a name. The Python repository model uses a dataclass for this reason.

## Sets and membership rules

Sets enforce uniqueness and support mathematical operations that map naturally to operational checks.

The required-check set contains `tests`, `lint`, and `security-scan`. The completed-check set contains `tests`, `security-scan`, and `coverage`. Their intersection identifies checks that satisfy both collections. Their difference identifies required checks that remain missing. Their union represents every distinct check observed.

The Python implementation also uses sets to remove duplicate language labels and to verify reviewer eligibility.

Set membership takes constant time on average under normal hashing assumptions, while list membership can require examining every element. Hash collisions and hashing costs can affect actual performance. Sets also consume additional memory to maintain their hash tables.

Set iteration order should not be used as a stable presentation format. Reports that require repeatable output should sort their values before serialization or comparison.

## Dictionaries and key-value mappings

A dictionary associates a key with a value. In the repository inventory, fields such as `name`, `language`, and `stars` form a record. A deployment identifier can map directly to its status or configuration.

The implementation distinguishes several useful operations:

- `get()` retrieves an optional value without raising `KeyError` when a key is missing.
- `pop()` retrieves a value while removing the associated key.
- `setdefault()` initializes a missing mapping entry, which is useful when collecting labels or grouped records.
- Dictionary unpacking merges mappings into a new dictionary. When keys overlap, values from later mappings replace earlier values.

A missing key and a present key whose value is `None` represent different states. Membership testing with `in` preserves that distinction.

The repository catalog uses a dictionary to store flexible metadata such as the operational tier and test status. In a production system, metadata should still be validated against a defined schema when its fields affect security or release decisions.

## Nested structures and data validation

Nested data represents relationships that do not fit into a single flat collection. The deployment record contains a service object, a list of check results, and a set of regions.

The Python implementation retrieves the service name from a nested dictionary, filters failed checks, and sums execution durations. It validates the shape and types of check records before trusting their values.

A nested structure can be convenient for JSON APIs, configuration files, and event payloads. Its flexibility also creates risks: a required key may be absent, a field may have the wrong type, or a list may contain unexpected elements.

Validation should occur at the boundary where external data enters the application. Type annotations improve readability but do not automatically validate runtime values. Explicit checks, domain constructors, and meaningful exceptions make failures easier to identify.

When records grow in complexity, separate classes or normalized database tables may provide stronger guarantees than deeply nested dictionaries.

## Comprehensions and collection transformations

Comprehensions combine iteration, transformation, and optional filtering.

The Python implementation builds:

- A list of repository names from repository records.
- A dictionary containing repositories above a star threshold.
- A set of distinct programming languages.
- A nested comprehension that flattens groups of required checks.
- A generator expression that calculates the total number of stars without constructing an intermediate list.

The language-count calculation derives the number of active repositories in each language. The topic index maps each topic to its associated repository names, while the maintainer index maps each maintainer to the repositories they manage.

These are examples of materialized views of the same source data. They should normally be derived from authoritative records rather than maintained independently without a synchronization strategy.

Comprehensions are most effective when their transformations are short and clear. Multi-stage business rules are often easier to debug as named functions or explicit loops.

## Python implementation

The Python script defines a `Repository` dataclass containing the repository name, programming language, star count, topics, maintainers, archive state, and metadata.

The `__post_init__()` method validates the fields and normalizes topics. The `to_record()` method creates an export-friendly dictionary and converts sets and tuples into serializable collection types.

The `build_repository_catalog()` function supplies representative repository records. `analyze_repository_catalog()` derives active repository counts, language statistics, topic indexes, maintainer indexes, failed-test records, and high-star repositories.

The implementation uses `Counter` to count statuses and languages, `defaultdict` to create grouped indexes, and `deque` to model a release queue. These standard-library collections provide clearer behavior than manually managing equivalent structures.

The error-handling examples cover missing keys, invalid field types, negative counts, empty names, and JSON serialization. The performance demonstration compares repeated membership operations against a list and a set. Timing results depend on the machine and runtime, so the example does not assume a fixed speedup.

Run the program with `python data_structures.py`.

## JavaScript implementation

The JavaScript file models the same operational domain through arrays, `Set`, `Map`, and nested objects.

Arrays preserve sequence order and provide transformation methods such as `filter`, `map`, `reduce`, and `sort`. The deployment-event pipeline filters failures, projects selected fields, derives an attention flag, and orders records by duration.

`Set` provides uniqueness and membership checks. `Map` stores deployment records and supports keys that are not limited to strings. These structures serve different purposes from ordinary objects, which are well suited to records with named properties.

The repository factory validates its input and returns a normalized record. Array copying and object spread are demonstrated as shallow operations, while `structuredClone()` creates an independent copy of supported nested data.

The program also converts `Set` values into arrays before JSON serialization. JSON serialization does not automatically preserve JavaScript collection types such as `Map` and `Set`, so explicit conversion is necessary when interoperable output is required.

The asynchronous event-processing function validates event records and uses `Promise.all()` to process a batch. It illustrates asynchronous control flow without requiring a remote API.

Run the file with Node.js 18 or later using `node data_structures.js`.

## C++ case study: deployment readiness engine

The C++ program implements a repository inventory and deployment-readiness engine.

A `Repository` contains ordered maintainer names, a set of topics, and scalar metadata. A `Deployment` contains a vector of check results and a set of target regions. The `GovernanceEngine` owns repository records and maintains an index from repository names to vector positions.

The index allows expected constant-time repository lookup through `unordered_map`, while the repository vector preserves insertion order for inventory reports. A second index maps topics to repository names.

The deployment evaluator compares actual check results with a set of required checks. It reports missing checks, failed checks, duplicate results, archived repositories, disallowed environments, and deployments without regions. Negative durations and empty identifiers are rejected through validation exceptions.

The evaluator separates a decision from its presentation. `DeploymentDecision` contains the eligibility result, blockers, and total duration. This makes the decision suitable for a user interface, command-line report, or service response.

For \(n\) repositories and \(t\) topic associations, repository insertion requires expected constant-time hash-table operations plus the cost of indexing the topics. Lookup by repository name is expected \(O(1)\), while retrieving repositories by a topic depends on the number of matching repositories.

The engine is an in-memory model, not a replacement for durable transactional storage. A production implementation would also require persistence, concurrent-update controls, identity verification, and authorization.

Compile with a C++17-compatible compiler. For example, use `g++ -std=c++17 -O2 -Wall -Wextra -pedantic` followed by the source filename and run the resulting executable.

## Java implementation: enterprise repository registry

The Java program uses explicit domain types to distinguish repository metadata, release identifiers, environments, check statuses, release policies, and release decisions.

The `Repository` class validates its input and exposes immutable collection views. `List.copyOf()` and `Map.copyOf()` protect against ordinary mutation through the original collection references, while the topic collection is stored as a sorted set for deterministic display.

`ReleaseKey` is a record whose repository and environment identify a release target. The `Release` constructor builds a map keyed by check name and rejects duplicate check results. This makes check lookup direct and gives duplicate records an explicit failure path.

`RepositoryRegistry` maintains separate indexes for repository names, topics, and maintainers. Its language-count method uses streams and `Collectors.groupingBy()` to aggregate active repositories.

`ReleasePolicy` evaluates environment restrictions, mandatory checks, pending and failed statuses, archived repository rules, and maximum check durations. It returns an immutable `ReleaseDecision` with explicit blockers rather than mixing business decisions with console output.

The model demonstrates why named domain types can be safer than passing generic nested maps between enterprise services. It also demonstrates an important distinction: an immutable collection wrapper does not automatically make arbitrary mutable objects inside that collection immutable. This implementation uses immutable field types for its domain records.

Compile and run with Java 17 or later using `javac DataStructuresEnterprise.java` and `java DataStructuresEnterprise`.

## PostgreSQL data model

The SQL implementation uses a relational model to show when collections should be stored as columns and when they should become independent rows.

The `repositories` table stores scalar fields, topic and maintainer arrays, and flexible metadata in `JSONB`. Database constraints enforce unique repository names, non-negative star counts, valid language values, and required maintainers for active repositories.

The `deployments` table references repositories through a foreign key. `deployment_checks` represents each individual check as a row, with a unique constraint on the combination of deployment and check name. This prevents a deployment from recording multiple results for the same check.

The `deployment_regions` table provides a controlled list of regions. `deployment_region_assignments` connects deployments to regions using a composite primary key, preventing duplicate assignments.

Release policies and required checks are stored separately. This design allows different environments to enforce different mandatory checks without embedding policy logic in every deployment record.

### Arrays, JSONB, and normalized relationships

Arrays are useful when a collection is small, belongs directly to one record, and is generally accessed as a whole. PostgreSQL's `unnest()` function converts array elements into rows for filtering and aggregation. A GIN index supports topic membership queries.

`JSONB` supports flexible metadata and containment queries. The program uses JSONB to store operational tier and test status, and to retain structured details about check results.

A separate child table is more appropriate when individual collection elements require foreign keys, independent status fields, uniqueness constraints, or frequent relational joins. Deployment checks and region assignments therefore use normalized tables instead of being stored only in arrays.

### Views and release policy evaluation

The `deployment_check_summary` view aggregates check counts and durations. The `deployment_policy_evaluation` view compares each deployment with its environment-specific policy and exposes blockers for missing, failed, or pending checks, excessive duration, absent regions, archived repositories, and incomplete deployment status.

The query uses common table expressions to separate check aggregation from missing-check detection. This makes each part of the policy calculation easier to inspect.

The indexes serve distinct purposes: language-based filtering of active repositories, GIN searches over topics and JSONB metadata, ordered retrieval of deployments for a repository, and status-based filtering of deployment checks.

The script demonstrates transactions and catches expected constraint failures in a `DO` block. Its final rollback preserves the initial demonstration data. In production, a policy evaluation that precedes an update must account for concurrent changes. The check and state transition should be performed atomically when release safety depends on the result.

Execute the SQL script in a PostgreSQL environment with permission to create a schema and tables.

## Collection design and performance

Choosing a data structure is a decision about the operations a system performs most often, not merely about how data looks when printed.

| Requirement | Suitable choice | Reason |
|---|---|---|
| Preserve deployment event order | List, JavaScript array, C++ vector | Supports sequential processing and position-based access |
| Find a repository by name | Dictionary, `Map`, hash map | Avoids repeatedly scanning the entire inventory |
| Identify distinct required checks | Set | Represents membership and uniqueness directly |
| Represent one release configuration | Tuple or named record | Groups related fields into one value |
| Associate each topic with repositories | Dictionary of lists or sets, indexed map | Supports reverse lookup |
| Preserve individual check history in a database | Relational child table | Enables foreign keys, independent constraints, and aggregation |
| Store flexible supplementary attributes | Dictionary, JavaScript object, or JSONB | Accommodates optional metadata with appropriate validation |

List indexing is \(O(1)\), while insertion or deletion near the beginning of a list is generally \(O(n)\) because later elements must shift. Dictionary and hash-based set operations are expected \(O(1)\) on average, but their worst-case behavior and memory costs differ from those of contiguous arrays.

The total cost of an operation also includes validation, copying, hashing, sorting, and serialization. Sorting a collection of \(n\) items typically costs \(O(n \log n)\). Deep copying a nested structure requires work proportional to the traversed objects and their contents.

## Common failure conditions

- **Unintended aliasing:** Shallow copies duplicate the outer collection but preserve references to nested mutable objects. Use independent objects or an appropriate deep copy when independent state is required.
- **Unhashable elements:** Lists and dictionaries cannot be set elements or dictionary keys in Python. Use immutable, hashable identifiers or a named immutable record.
- **Duplicate identifiers:** A collection can contain duplicate list entries even when the application requires unique repository names. Validate uniqueness or use a keyed mapping and a database constraint.
- **Missing dictionary keys:** Direct indexing raises `KeyError` when a key is absent. Use `get()` for genuinely optional values and explicit validation for required values.
- **Incorrect nested types:** A valid outer dictionary does not guarantee that its nested values have the expected type. Validate external data before calculating metrics.
- **Nondeterministic reporting:** Set iteration should not define a report's stable ordering. Sort values where reproducible output matters.
- **Serialization mismatches:** Python sets, JavaScript `Set`, and JavaScript `Map` do not directly map to ordinary JSON arrays and objects in a uniform way. Convert them explicitly.
- **Stale derived indexes:** A topic index can become incorrect when the underlying topic collection changes. Rebuild the index, update it atomically, or use a database query that derives the relationship from authoritative records.
- **Invalid numeric values:** Counts and durations should be validated for non-negative values and appropriate numeric ranges before they influence operational decisions.

## Testing and operational reliability

Collection-heavy code should be tested against both ordinary records and boundary conditions.

Tests should verify that duplicate repository identifiers are rejected, empty identifiers cannot enter the registry, required checks are not silently omitted, and archived repositories cannot pass a policy that forbids their release. Copying tests should confirm that mutations do not leak into independent snapshots. Serialization tests should confirm that a round trip preserves the fields and value types the receiving system expects.

Aggregation results should be checked against known records. A topic index should return exactly the repositories containing that topic, and language counts should exclude archived records when the report claims to represent active repositories.

Operational reports should also distinguish an absent result from a failed result and a pending result. These states have different meanings and should not be collapsed into a single truthy or falsy value.

For persistent data, application validation and database constraints serve complementary purposes. Application checks provide useful error messages and early rejection. Database constraints preserve integrity even when records are written by another program or concurrent request.
