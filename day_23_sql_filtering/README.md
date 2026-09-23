# SQL Filtering: WHERE, Comparison Operators, AND, OR, NOT, IN, BETWEEN, LIKE, IS NULL

## Topic introduction

SQL filtering determines which rows from a query result should be retained. The central mechanism is the `WHERE` clause, which evaluates a condition for each candidate row.

The most important filtering tools covered in this project are:

- `WHERE`
- comparison operators
- `AND`
- `OR`
- `NOT`
- `IN`
- `BETWEEN`
- `LIKE`
- `IS NULL`
- `IS NOT NULL`

These operators are the foundation of database search, reporting, analytics, administration systems, dashboards, APIs, business applications, and data-processing workflows.

The project uses the same general employee dataset across the three implementations. The Python program executes real SQL against SQLite. The JavaScript program demonstrates equivalent filtering concepts with JavaScript data structures and functions. The C++ program develops a database-style predicate engine that models SQL filtering semantics, including SQL's three-valued logic.

---

## Fundamental concept: selecting rows

A basic SQL query has this structure:

`SELECT column_list FROM table WHERE condition;`

The `SELECT` portion determines which columns are returned.

The `FROM` portion identifies the source table.

The `WHERE` portion determines which rows are eligible.

For example:

`SELECT employee_name, salary FROM employees WHERE salary > 100000;`

The database examines candidate employee rows and retains rows for which `salary > 100000` evaluates to `TRUE`.

Filtering is performed on rows, not individual columns in isolation. A predicate can reference one column, several columns, constants, functions, subqueries, or values from joined tables.

---

## The WHERE clause

`WHERE` introduces a search condition.

A simple predicate is:

`WHERE salary > 100000`

Multiple predicates can be combined:

`WHERE salary > 100000 AND active = 1`

A filtering condition can also use membership:

`WHERE department_id IN (1, 5)`

A pattern:

`WHERE employee_name LIKE 'A%'`

Or a null test:

`WHERE email IS NULL`

The most important rule is that `WHERE` retains rows whose complete condition evaluates to `TRUE`.

Rows whose condition evaluates to `FALSE` are rejected.

Rows whose condition evaluates to `UNKNOWN` are also rejected.

The last point is fundamental to understanding `NULL`.

---

## Comparison operators

The primary comparison operators are:

| Operator | Meaning |
|---|---|
| `=` | Equal to |
| `<>` | Not equal to |
| `!=` | Not equal to in systems that support it |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal to |
| `<=` | Less than or equal to |

For example:

`WHERE salary = 98000`

returns rows whose salary is exactly `98000`.

`WHERE salary >= 100000`

returns rows whose salary is at least `100000`.

`WHERE age < 30`

returns rows whose age is below `30`.

SQL equality uses `=` rather than the Python or JavaScript-style `==` operator. Some database systems, including SQLite, accept `==`, but portable SQL should normally use `=`.

---

## AND

`AND` requires all connected conditions to be true.

For example:

`WHERE salary >= 80000 AND age < 40`

requires both conditions to succeed.

A row with salary `90000` and age `35` satisfies both conditions.

A row with salary `90000` and age `45` does not satisfy the complete condition.

Multiple `AND` conditions can be used:

`WHERE active = 1 AND salary >= 90000 AND email IS NOT NULL`

This is common in application search systems where several restrictions must all apply.

---

## OR

`OR` succeeds when at least one condition is true.

For example:

`WHERE city = 'Delhi' OR city = 'Mumbai'`

selects employees from either city.

Several equality comparisons against the same column can often be expressed more clearly with `IN`:

`WHERE city IN ('Delhi', 'Mumbai')`

When `AND` and `OR` are mixed, parentheses should normally be used to make the intended business rule explicit.

Consider:

`WHERE city = 'Delhi' OR city = 'Mumbai' AND salary > 100000`

`AND` has higher logical precedence than `OR`, so the expression is interpreted approximately as:

`city = 'Delhi' OR (city = 'Mumbai' AND salary > 100000)`

If the intended meaning is that the salary condition applies to both cities, the query should be written as:

`WHERE (city = 'Delhi' OR city = 'Mumbai') AND salary > 100000`

Parentheses prevent logical ambiguity and make maintenance safer.

---

## NOT

`NOT` reverses a logical condition.

For example:

`WHERE NOT city = 'Delhi'`

is a logical negation of the comparison.

`NOT` can also be applied to grouped conditions:

`WHERE NOT (department_id = 1 OR department_id = 2)`

It can be combined with other SQL operators:

`NOT IN`

`NOT BETWEEN`

`NOT LIKE`

A critical qualification is that `NOT` does not turn SQL `UNKNOWN` into `TRUE`.

`NOT UNKNOWN` is still `UNKNOWN`.

This matters when a column contains `NULL`.

---

## IN

`IN` checks whether a value belongs to a specified set.

Instead of:

`WHERE city = 'Delhi' OR city = 'Mumbai' OR city = 'Lucknow'`

the query can use:

`WHERE city IN ('Delhi', 'Mumbai', 'Lucknow')`

This is easier to read and particularly useful when the allowed values are known.

`NOT IN` expresses the inverse membership condition:

`WHERE department_id NOT IN (1, 2, 3)`

`IN` can also work with a subquery:

`WHERE department_id IN (SELECT department_id FROM departments WHERE location IN ('Bengaluru', 'Hyderabad'))`

This allows the membership set to be produced dynamically.

### IN and NULL

`NOT IN` requires special care when its comparison set can contain `NULL`.

A subquery that returns:

`1, 2, NULL`

can cause `NOT IN` to produce `UNKNOWN` for comparisons that might otherwise appear to be true.

When the requirement is "there is no related row satisfying this condition", `NOT EXISTS` is often a more robust expression.

The Python implementation demonstrates this distinction with a subquery containing `NULL`.

---

## BETWEEN

`BETWEEN` tests an inclusive range.

`WHERE salary BETWEEN 80000 AND 100000`

means:

`salary >= 80000 AND salary <= 100000`

Both boundaries are included.

Therefore a salary of exactly `80000` passes, and a salary of exactly `100000` also passes.

This differs from many programming constructs where the upper boundary is exclusive.

`NOT BETWEEN` expresses the inverse range condition:

`WHERE price NOT BETWEEN 5000 AND 50000`

### BETWEEN and dates

For consistently formatted date values, `BETWEEN` can be useful:

`WHERE order_date BETWEEN '2026-02-01' AND '2026-03-31'`

For timestamp data, a half-open range is frequently safer:

`WHERE timestamp >= '2026-03-01' AND timestamp < '2026-04-01'`

This avoids having to invent a final timestamp such as `23:59:59.999999`.

The Python and JavaScript implementations demonstrate this approach.

---

## LIKE

`LIKE` performs pattern matching.

The two most important wildcard characters are:

| Pattern character | Meaning |
|---|---|
| `%` | Zero or more characters |
| `_` | Exactly one character |

Examples:

`WHERE employee_name LIKE 'A%'`

means the name starts with `A`.

`WHERE employee_name LIKE '%ar%'`

means the value contains `ar`.

`WHERE employee_name LIKE '%a'`

means the value ends with `a`.

`WHERE employee_name LIKE '_e%'`

means the second character is `e`.

`LIKE` is different from equality.

`employee_name = 'Aarav Sharma'`

tests one exact value.

`employee_name LIKE 'Aarav%'`

tests a pattern.

### LIKE and escaping

If a literal `%` or `_` needs to be searched for, SQL dialects commonly provide an `ESCAPE` mechanism. The exact syntax and behavior should be checked for the target database system.

### LIKE and case sensitivity

Case sensitivity is database-dependent. SQLite, PostgreSQL, MySQL, SQL Server, and other database systems can differ in their default behavior, collations, and available operators.

Applications that depend on case-sensitive or case-insensitive search should make the intended behavior explicit.

---

## IS NULL

`NULL` represents missing, unknown, or inapplicable information.

It is not equivalent to:

- zero
- an empty string
- the text `"NULL"`
- `FALSE`

The correct test for a null value is:

`WHERE email IS NULL`

The correct test for a non-null value is:

`WHERE email IS NOT NULL`

This is not equivalent to:

`WHERE email = NULL`

The latter does not produce `TRUE`.

---

## SQL three-valued logic

Ordinary programming languages commonly describe Boolean logic using two values:

- true
- false

SQL uses three logical states:

- `TRUE`
- `FALSE`
- `UNKNOWN`

`UNKNOWN` is particularly important when `NULL` participates in an expression.

Examples include:

`NULL = 5`

`NULL <> 5`

`NULL > 5`

`NULL = NULL`

These do not evaluate to `TRUE`.

They produce `UNKNOWN`.

### AND

The important rules include:

| Left | Right | Result |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE |
| TRUE | UNKNOWN | UNKNOWN |
| FALSE | UNKNOWN | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

### OR

Important rules include:

| Left | Right | Result |
|---|---|---|
| TRUE | FALSE | TRUE |
| TRUE | UNKNOWN | TRUE |
| FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN |

### NOT

| Input | NOT result |
|---|---|
| TRUE | FALSE |
| FALSE | TRUE |
| UNKNOWN | UNKNOWN |

Because `WHERE` keeps only `TRUE`, both `FALSE` and `UNKNOWN` cause a row to be excluded.

This explains why a nullable column requires `IS NULL` rather than ordinary equality.

---

## Operator precedence

When SQL combines multiple logical operators, precedence matters.

A useful conceptual order is:

1. `NOT`
2. `AND`
3. `OR`

For example:

`WHERE NOT active = 1 AND salary > 50000 OR department_id = 5`

can be difficult to interpret at a glance.

Explicit grouping is safer:

`WHERE (NOT active = 1 AND salary > 50000) OR department_id = 5`

Parentheses communicate the intended logic directly.

This is particularly important in production queries because a syntactically valid query can still express the wrong business rule.

---

## Python implementation

The Python implementation uses the standard-library `sqlite3` module.

This means the filtering examples execute against a real SQL engine rather than merely imitating SQL syntax.

The program creates:

- `departments`
- `employees`
- `customers`
- `products`
- `orders`

The employee data includes nullable columns, which makes it possible to demonstrate `IS NULL`, `IS NOT NULL`, and three-valued logic.

### Basic WHERE

The Python implementation executes:

`SELECT employee_id, employee_name, salary FROM employees WHERE salary > 100000`

This demonstrates the complete lifecycle of a real SQL filtering operation.

### Comparison operators

The Python program separately demonstrates:

- equality
- inequality
- greater than
- less than
- greater than or equal to
- less than or equal to

The examples use real database values.

### Logical operators

The Python implementation demonstrates:

- `AND`
- `OR`
- `NOT`

It also explicitly compares queries with and without parentheses.

### IN

The Python implementation demonstrates both a literal membership list and an `IN` subquery.

### BETWEEN

The Python program demonstrates inclusive numeric ranges and date filtering.

### LIKE

The program demonstrates `%` and `_` patterns against employee and product names.

### NULL

The program deliberately runs both:

`WHERE email IS NULL`

and:

`WHERE email = NULL`

The second query illustrates why ordinary equality is not the correct method for detecting SQL `NULL`.

### Parameterized queries

The Python implementation demonstrates parameterized SQL:

`WHERE salary >= ? AND city = ?`

The values are supplied separately from the SQL statement.

This separation is an important security practice because application data should not be inserted into SQL syntax by string concatenation.

### Dynamic filters

The `EmployeeRepository` and `EmployeeFilter` classes model a common application requirement: users may provide some filters while leaving others unspecified.

The application builds only the necessary predicate fragments while keeping user values parameterized.

This approach is useful for employee search pages, administrative dashboards, reporting systems, customer search interfaces, and API endpoints.

### JOIN filtering

The Python implementation also shows that `WHERE` can filter results produced by joins.

For example, employees can be joined to departments and then restricted based on department location.

The program demonstrates an important outer-join issue: placing a condition in `WHERE` can remove rows whose right-side values are `NULL`, changing the effective result of a `LEFT JOIN`.

### WHERE versus HAVING

`WHERE` filters individual rows before grouping.

`HAVING` filters groups after `GROUP BY`.

The Python program demonstrates both in one query:

- `WHERE active = 1` removes inactive employee rows.
- `GROUP BY department_id` creates groups.
- `HAVING AVG(salary) >= 90000` filters the resulting groups.

This distinction becomes important in analytical SQL.

---

## JavaScript implementation

The JavaScript implementation does not require an external database package.

Instead, it models SQL filtering concepts using arrays, objects, functions, `Set`, and explicit SQL-style helper functions.

This makes the relationship between database filtering and application-level filtering easier to see.

### Array.filter()

JavaScript's `Array.prototype.filter()` is conceptually similar to SQL's row filtering:

`employees.filter(employee => employee.salary > 100000)`

The callback determines whether each object remains in the result.

This is not a replacement for SQL filtering in a database. Filtering large database tables in application memory can be inefficient because unnecessary rows must first be transferred from the database.

It is useful here as a conceptual comparison.

### AND and OR

JavaScript uses:

`&&`

for logical AND and:

`||`

for logical OR.

For example:

`employee.salary >= 80000 && employee.age < 40`

corresponds conceptually to:

`salary >= 80000 AND age < 40`

### NOT

JavaScript uses `!` for Boolean negation.

The program uses:

`!(employee.city === "Delhi")`

to illustrate the relationship with SQL `NOT`.

### IN

JavaScript's `Set` provides an efficient and readable membership representation:

`allowedCities.has(employee.city)`

This corresponds conceptually to:

`city IN ('Delhi', 'Mumbai', 'Lucknow')`

### BETWEEN

JavaScript does not have a built-in `BETWEEN` operator. The implementation defines a reusable function:

`value >= lower && value <= upper`

The function deliberately includes both boundaries to match SQL `BETWEEN`.

### LIKE

JavaScript does not provide a SQL `LIKE` operator.

The implementation creates a small `sqlLike()` function that translates:

- `%` into zero or more characters
- `_` into one character

into a regular-expression-based implementation.

This is educational and demonstrates the semantics of SQL pattern matching.

A real database application should normally let the database engine perform the filtering rather than retrieving all records and applying a custom JavaScript matcher.

### NULL

JavaScript represents database-style missing values using `null` in the example data.

The implementation distinguishes:

`employee.email === null`

from the SQL expression:

`email IS NULL`

The underlying concepts are related but the languages are not identical. SQL `NULL` is integrated into SQL's three-valued logic, whereas JavaScript's `null` is a language-level value.

### Reusable predicates

The JavaScript program creates reusable functions for:

- salary ranges
- department membership
- city membership
- email presence
- name patterns

This demonstrates how filtering rules can become reusable application components.

### Optional search criteria

The `searchEmployees()` function models an application search interface where users can specify:

- minimum salary
- maximum salary
- cities
- departments
- active status
- name pattern
- email requirement

The function applies only the supplied restrictions.

This resembles the logic used by administrative portals and API search endpoints.

---

## C++ case study

The C++ program models a workforce search service.

The purpose is not merely to reproduce SQL syntax. It demonstrates how database-style predicates can be represented as application-level components and combined into an industry-style search system.

The implementation uses C++17 and the standard library.

### Problem being solved

The modeled system contains employee records with:

- employee ID
- name
- department
- salary
- age
- city
- email
- active status

A user or application can request filtered employee results.

The search system must support conditions such as:

- salary thresholds
- salary ranges
- department membership
- city membership
- text patterns
- active employees
- non-null email addresses

These individual conditions can then be combined with `AND`, `OR`, and `NOT`.

---

## C++ architecture

The C++ case study contains several layers.

### Employee

The `Employee` structure represents a database row.

`std::optional<std::string>` is used for nullable city and email values.

This is useful because an optional value makes the distinction between:

- a present string
- no value

explicit in the C++ type system.

### TruthValue

The `TruthValue` enumeration contains:

- `False`
- `True`
- `Unknown`

This directly models SQL's three-valued logic.

### Predicate

The program defines:

`using Predicate = function<TruthValue(const Employee&)>;`

A predicate is therefore a function that receives an employee and returns a SQL-style logical result.

This design allows predicates to be composed.

### filterEmployees()

The filtering engine retains a row only when the predicate returns `TruthValue::True`.

This accurately models the key behavior of SQL `WHERE`.

`FALSE` is rejected.

`UNKNOWN` is also rejected.

### Predicate factories

Functions such as:

- `salaryGreaterThan()`
- `salaryAtLeast()`
- `salaryBetween()`
- `departmentEquals()`
- `departmentIn()`
- `cityEquals()`
- `cityIn()`
- `activeOnly()`
- `hasEmail()`
- `nameLike()`

produce reusable predicates.

This resembles how application code can encapsulate business search rules.

---

## C++ logical composition

The C++ implementation provides:

- `logicalAnd()`
- `logicalOr()`
- `logicalNot()`

These functions combine predicates using SQL-style three-valued logic.

For example, a complex filter can be represented as:

`activeOnly() AND departmentIn(...) AND salaryBetween(...) AND hasEmail()`

This gives the case study a compositional structure rather than embedding every possible search rule inside one large function.

---

## C++ LIKE implementation

The C++ program includes a recursive `likeMatch()` implementation.

It supports:

- `%`
- `_`

The implementation is intentionally explicit so that the mechanics of pattern matching can be studied.

For `%`, the algorithm considers two possibilities:

- `%` consumes zero characters.
- `%` consumes one character and remains active for additional characters.

For `_`, exactly one character must be available.

The implementation is suitable as an educational demonstration. A production database application would normally delegate SQL `LIKE` evaluation to the database engine.

---

## C++ NULL behavior

The C++ program uses `std::optional` for nullable values.

For example:

`optional<string> email`

can contain an email or no value.

A comparison against a missing optional value returns `Unknown`.

This enables the case study to reproduce an important SQL behavior:

`NULL = 'Delhi'`

is not `TRUE` or `FALSE`; it is `UNKNOWN`.

Consequently:

`NOT (NULL = 'Delhi')`

also remains `UNKNOWN`.

That means a row with a null city is not returned by either:

`city = 'Delhi'`

or:

`NOT city = 'Delhi'`

This behavior is demonstrated directly by the program.

---

## Complex workforce search

The C++ program defines a realistic search requirement:

Find employees who:

- are active
- work in Engineering or Security
- earn between `90000` and `140000`
- have an email address
- have a name matching `%a%`

The implementation constructs the predicate from smaller reusable predicates.

This illustrates how a complex SQL `WHERE` clause can be understood as a composition of smaller logical conditions.

---

## Optional search criteria

The `EmployeeFilter` structure represents user-provided search criteria.

Every property is optional except for the Boolean switches.

The `buildPredicate()` function constructs the appropriate combined predicate.

This approach is useful when implementing:

- employee administration systems
- customer search interfaces
- reporting tools
- internal dashboards
- API filtering
- enterprise search services

It also demonstrates why dynamic query systems need careful separation between filter structure and user-provided values.

---

## Algorithmic complexity

A direct in-memory scan over `n` employees has time complexity:

`O(n)`

because each row may need to be inspected.

A membership lookup using `std::set` is approximately:

`O(log k)`

where `k` is the number of values in the set.

If a database table has millions of rows, a direct application-level scan can be very expensive.

A database engine can use indexes and its query optimizer to choose a different execution strategy.

For example, a primary-key filter such as:

`WHERE employee_id = 11`

may be able to use an index.

The actual execution strategy depends on the database system, indexes, statistics, query structure, and data distribution.

---

## Filtering and indexes

A filter does not automatically mean that an index will be used.

Database systems consider several factors, including:

- available indexes
- predicate structure
- estimated selectivity
- table statistics
- data distribution
- estimated I/O cost
- sorting requirements
- joins
- database-specific optimizer rules

For a large table, filtering on an indexed column can sometimes avoid a full table scan.

The Python implementation uses SQLite's `EXPLAIN QUERY PLAN` to demonstrate how an index can affect query planning.

---

## Selectivity

Selectivity describes how strongly a predicate reduces the candidate row set.

A primary-key condition such as:

`employee_id = 11`

is usually highly selective because it identifies very few rows.

A condition such as:

`active = 1`

may be much less selective if most employees are active.

This distinction matters to query optimization and index usefulness.

The database optimizer, rather than the application programmer, normally determines the final execution strategy.

---

## Security considerations

Filtering systems frequently receive values from users.

Examples include:

- search fields
- API query parameters
- dashboard controls
- administrative interfaces
- web forms

A dangerous approach is to concatenate untrusted input directly into SQL.

For example, constructing SQL by embedding an untrusted city string directly into the statement can allow the input to become SQL syntax.

Parameterized queries avoid this by separating SQL structure from values.

The Python program demonstrates:

`WHERE salary >= ? AND city = ?`

with the actual values passed separately.

This is the preferred pattern for dynamic values.

The same principle applies when JavaScript, C++, Java, Go, C#, or another application language communicates with a database.

Parameterization does not mean that every part of a SQL query can safely be represented by a parameter. Values can generally be parameterized, while SQL identifiers such as table names, column names, and sort directions usually require controlled application logic or allowlisting.

---

## Common mistakes

### Using NULL with equality

Incorrect:

`WHERE email = NULL`

Correct:

`WHERE email IS NULL`

The reason is SQL's three-valued logic.

### Forgetting BETWEEN is inclusive

`BETWEEN 10 AND 20`

includes `10` and `20`.

### Misunderstanding AND and OR

An expression such as:

`A OR B AND C`

is not equivalent to:

`(A OR B) AND C`

Use parentheses when the intended grouping is important.

### Treating NULL as zero

`NULL` does not mean `0`.

A missing salary and a salary of zero have different meanings.

### Treating NULL as an empty string

`NULL` and `''` are different.

An empty string is a string value containing no characters.

`NULL` represents the absence of a value.

### Using NOT IN carelessly

A `NULL` in a `NOT IN` subquery can produce unexpected `UNKNOWN` results.

`NOT EXISTS` can often express an anti-match requirement more safely.

### Filtering in application memory unnecessarily

If a database can perform the filtering efficiently, retrieving a large table and filtering it in Python, JavaScript, or C++ can create unnecessary network, memory, and CPU costs.

### Building SQL with string concatenation

Direct string concatenation of user input creates SQL injection risk.

Use parameterized queries.

### Assuming all SQL dialects behave identically

SQL is standardized, but database systems differ in:

- operators
- functions
- collation
- case sensitivity
- NULL behavior in certain constructs
- date handling
- optimizer behavior
- indexing features
- pattern matching features

Queries should be tested against the actual target database.

---

## Edge cases

### NULL in a comparison

`NULL > 100`

produces `UNKNOWN`.

### NULL with NOT

`NOT (NULL > 100)`

still produces `UNKNOWN`.

### NULL with AND

`FALSE AND UNKNOWN`

is `FALSE`.

This is important because one known-false condition can determine the result of an `AND`.

### NULL with OR

`TRUE OR UNKNOWN`

is `TRUE`.

One known-true condition can determine the result of an `OR`.

### Empty membership sets

An application that constructs an `IN` list dynamically must handle an empty list carefully.

Not every SQL dialect accepts an empty `IN ()` expression, and even where syntax is accepted the intended business meaning must be explicit.

The application should decide whether an empty set means:

- no rows should match
- no membership restriction should apply
- invalid input

before generating SQL.

### Date and timestamp boundaries

Filtering timestamps using an inclusive end point can be error-prone when the precision of the database column is unknown.

A half-open range such as:

`timestamp >= start AND timestamp < end`

is often easier to reason about.

### LIKE wildcards

A search for literal `%` or `_` requires escaping when those characters should not behave as wildcards.

---

## Important distinctions

### WHERE versus HAVING

`WHERE` filters rows before aggregation.

`HAVING` filters groups after aggregation.

Example:

`WHERE active = 1`

filters employee rows.

`HAVING AVG(salary) >= 90000`

filters grouped departments after the average has been calculated.

### WHERE versus ON

In joins, predicate placement can change results.

With an `INNER JOIN`, many filtering arrangements produce equivalent results, subject to query semantics and optimizer behavior.

With an outer join such as `LEFT JOIN`, moving a right-table condition between `ON` and `WHERE` can change whether unmatched left-side rows survive.

The Python implementation demonstrates this with employees that do not have a matching department.

### = versus LIKE

`=` checks equality.

`LIKE` performs pattern matching.

Use equality when an exact value is required.

Use `LIKE` when wildcard-based text matching is required.

### IN versus OR

These can express similar membership logic:

`city = 'Delhi' OR city = 'Mumbai'`

and:

`city IN ('Delhi', 'Mumbai')`

`IN` is generally clearer when the intent is membership in a fixed set.

### BETWEEN versus explicit comparisons

These are logically equivalent for ordinary non-null values:

`salary BETWEEN 80000 AND 100000`

and:

`salary >= 80000 AND salary <= 100000`

The `BETWEEN` form is concise and explicitly communicates a range.

---

## Python, JavaScript, and C++ comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Main purpose | Execute real SQL | Demonstrate application-side filtering | Model a filtering engine |
| Database | SQLite | None required | None required |
| SQL executed directly | Yes | No | No |
| `WHERE` demonstration | Real SQL | `Array.filter()` | Predicate engine |
| `IN` | SQL `IN` | `Set` membership | `std::set` membership |
| `BETWEEN` | Real SQL | Reusable function | Predicate factory |
| `LIKE` | SQLite `LIKE` | Custom matcher | Custom matcher |
| NULL model | SQLite `NULL` | `null` | `std::optional` + `Unknown` |
| Three-valued logic | Database engine | Explicit helper functions | Explicit `TruthValue` |
| Dynamic filtering | Parameterized SQL | Object-based criteria | Predicate composition |
| Security example | Parameterized SQL | Parameterized-query concept | Architectural discussion |
| Performance model | SQLite query planner | In-memory array filtering | In-memory linear filtering |

The three languages therefore serve different educational purposes.

Python is closest to actual database work because the program executes real SQLite queries.

JavaScript demonstrates how database filtering concepts relate to application-side collection processing and web-oriented logic.

C++ demonstrates how filtering semantics can be represented as reusable, strongly typed components and how SQL-style three-valued logic can be modeled explicitly.

---

## Implementation considerations

A production filtering system should separate several responsibilities.

### Input validation

User-supplied values should be validated before they become application-level filter parameters.

Examples include:

- numeric ranges
- valid date formats
- allowed department values
- maximum search-string length
- supported filter names

### Parameterization

Values should be passed as parameters rather than concatenated into SQL syntax.

### Controlled dynamic SQL

Dynamic filter construction should control SQL structure separately from values.

A safe design can use an allowlist for permitted:

- column names
- operators
- sort fields
- filter types

and parameters for values.

### Database-side filtering

When data is stored in a database, filtering should generally be pushed to the database rather than retrieving unnecessary rows.

This reduces:

- network transfer
- application memory consumption
- application CPU usage
- unnecessary serialization and deserialization

### Index design

Indexes should be based on real query workloads.

Adding indexes has costs:

- storage consumption
- additional write work
- maintenance overhead
- possible optimizer trade-offs

An index should therefore be evaluated against actual access patterns rather than added indiscriminately.

---

## Testing considerations

Filtering logic should be tested against:

- ordinary matching rows
- ordinary non-matching rows
- lower boundaries
- upper boundaries
- values outside ranges
- `NULL`
- empty input
- multiple matching values
- mixed `AND` and `OR`
- `NOT`
- pattern matching
- unexpected user input

The Python, JavaScript, and C++ programs contain executable assertions or validation checks for several of these cases.

A production test suite should also verify database-specific behavior because SQL dialects can differ.

---

## Real-world applications

SQL filtering is used throughout software systems.

Examples include:

### Banking

Filtering transactions by:

- date range
- amount
- account
- transaction type
- status

### E-commerce

Filtering products by:

- category
- price
- stock
- availability
- name pattern

### Human resources

Filtering employees by:

- department
- salary
- location
- employment status
- hiring date

### Cybersecurity

Filtering events by:

- severity
- source
- IP address
- event type
- timestamp
- authentication status

### Healthcare systems

Filtering records by:

- patient identifiers
- dates
- status
- department
- laboratory categories

### Analytics

Filtering datasets before:

- aggregation
- grouping
- reporting
- visualization
- statistical analysis

### APIs

Query parameters often translate into database predicates.

For example, an API request may conceptually represent:

`minimum_salary=90000`

`department=Engineering`

`active=true`

The application validates these parameters and converts them into controlled database conditions.

---

## Practical filtering pattern

A reliable mental model for a filtering query is:

1. Identify the rows that can be considered.
2. Determine the exact business condition.
3. Break the condition into small predicates.
4. Decide whether each predicate uses comparison, membership, range, pattern matching, or null testing.
5. Use parentheses for mixed logical operators.
6. Consider `NULL` explicitly.
7. Parameterize dynamic values.
8. Check whether filtering should occur in the database.
9. Consider indexes and query plans for large datasets.
10. Test boundary and null cases.

This approach prevents many common SQL filtering errors.

---

## Files in this implementation

The Python implementation is a complete SQLite-based study program covering the filtering operators and their interaction with joins, aggregation, subqueries, parameterized queries, dynamic filtering, indexing, security, and testing.

The JavaScript implementation provides an executable application-side representation of filtering using arrays, sets, predicates, pattern matching, optional criteria, and explicit SQL-style three-valued logic.

The C++ implementation presents an industry-style workforce search case study with strongly typed data, nullable values, SQL-style truth values, reusable predicates, logical composition, pattern matching, optional search criteria, validation, complexity analysis, and a service layer.

Together, the implementations demonstrate that SQL filtering is not simply a collection of isolated operators. It is a system of predicates governed by logical semantics, null behavior, data representation, query structure, performance considerations, and application requirements.
