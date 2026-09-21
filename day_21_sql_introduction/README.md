# SQL Introduction

## Topic scope

This study covers the foundations of SQL and relational databases. The central concepts are databases, database management systems, relational databases, tables, rows, columns, primary keys, foreign keys, schemas, constraints, relationships, SQL statements, and the SQL execution model.

The three implementations approach the subject from different perspectives:

- Python uses SQLite to provide a real executable relational database environment.
- JavaScript models the application layer that communicates with a database and demonstrates validation, parameterized queries, asynchronous transaction structure, joins, aggregation, and application-level database services.
- C++ develops an industry-style order-management case study using standard-library data structures to make relational storage, constraints, relationships, transactions, joins, aggregation, and complexity visible without requiring an external database library.

The Python implementation is the only implementation that actually executes SQL against SQLite. The JavaScript and C++ implementations deliberately show how application code interacts with or models relational database concepts without introducing an external database dependency.

---

## 1. Databases

A database is an organized system for storing and managing data.

An application might need to store:

- customers
- products
- employees
- orders
- payments
- addresses
- inventory
- transactions
- logs
- configuration
- analytical information

A database is more than a collection of files. A database management system, or DBMS, provides mechanisms for storing, retrieving, modifying, validating, securing, and recovering data.

Common categories of database systems include:

- relational databases
- document databases
- key-value databases
- graph databases
- wide-column databases
- time-series databases

This study concentrates on relational databases.

### Database versus DBMS

A useful distinction is:

**Database**

The organized collection of stored data and its structural definitions.

**Database management system**

The software responsible for managing that data.

A relational DBMS generally provides capabilities such as:

- SQL parsing
- query execution
- constraints
- transactions
- indexes
- concurrency control
- recovery
- permissions
- metadata management
- query optimization

SQLite, PostgreSQL, MySQL, MariaDB, Microsoft SQL Server, and Oracle Database are examples of relational database technologies, although their architecture, feature sets, type systems, syntax, and operational characteristics differ.

---

## 2. Relational databases

A relational database organizes data around relations. In practical SQL terminology, relations are normally represented as tables.

A simplified customer table could contain:

| customer_id | full_name | email |
| ---: | --- | --- |
| 1 | Asha Mehta | asha@example.com |
| 2 | Rohan Singh | rohan@example.com |
| 3 | Neha Kapoor | neha@example.com |

The table has three columns and three rows.

The relational approach becomes particularly useful when information has relationships.

For an order system, separate tables can represent separate concepts:

- `customers`
- `products`
- `orders`
- `order_items`

Instead of repeatedly storing customer information inside every order, an order can contain a `customer_id` that refers to the appropriate customer.

This reduces unnecessary duplication and gives the database a clear structural model.

---

## 3. Tables

A table is a structured collection of rows described by columns.

The Python implementation creates tables with statements such as `CREATE TABLE`.

The main schema contains:

- `customers`
- `products`
- `orders`
- `order_items`

### Customers

The `customers` table stores customer-specific information.

Its important columns are:

- `customer_id`
- `full_name`
- `email`
- `created_at`

### Products

The `products` table stores product information:

- `product_id`
- `product_name`
- `price`
- `stock_quantity`

### Orders

The `orders` table represents orders:

- `order_id`
- `customer_id`
- `order_date`
- `status`

### Order items

The `order_items` table represents the products contained in an order:

- `order_id`
- `product_id`
- `quantity`
- `unit_price`

The separation of these tables is important because each table represents a distinct business concept.

---

## 4. Rows

A row represents one record.

For example, this row in the `customers` table:

`1 | Asha Mehta | asha@example.com`

represents one customer.

Rows can be inserted using `INSERT`.

The Python implementation uses parameterized `INSERT` statements to add customers and products.

A database can contain millions or billions of rows, depending on the DBMS, hardware, architecture, and workload.

A row should represent one meaningful occurrence of the entity described by the table.

For example:

- one customer row represents one customer
- one product row represents one product
- one order row represents one order
- one order-item row represents one product entry within an order

---

## 5. Columns

A column represents an attribute.

For a customer:

- `customer_id` identifies the customer
- `full_name` stores the customer's name
- `email` stores the email address

Columns normally have declared types and may have constraints.

Examples include:

- `INTEGER`
- `TEXT`
- `NUMERIC`
- `VARCHAR`
- `DATE`
- `TIMESTAMP`
- `BOOLEAN`

Exact type systems vary by DBMS.

SQLite is particularly flexible because it uses dynamic typing with type affinity. PostgreSQL and other systems provide more extensive and stricter type systems.

This difference matters when moving SQL designs between database products.

---

## 6. Primary keys

A primary key identifies a row uniquely.

The Python schema defines:

`customer_id INTEGER PRIMARY KEY`

and similar primary keys for products and orders.

A primary key normally provides two important properties:

1. values identify rows uniquely
2. a primary-key column cannot contain NULL

For example:

| customer_id | full_name |
| ---: | --- |
| 1 | Asha Mehta |
| 2 | Rohan Singh |

The value `1` identifies the first customer and `2` identifies the second.

### Why primary keys matter

Without a reliable identifier, applications have difficulty referring to a specific row.

For example, searching only by name is problematic because two customers can have the same name.

An identifier such as `customer_id` provides a stable database-level identity.

### Natural and surrogate keys

A **natural key** uses a real-world attribute that is naturally unique, such as a government-issued identifier or a formally unique business code.

A **surrogate key** is an identifier created specifically for database use, such as an integer `customer_id`.

Surrogate keys are common because they are simple, stable, and independent of changing business attributes.

The appropriate choice depends on the system.

---

## 7. Composite primary keys

A primary key can contain more than one column.

The `order_items` table uses:

`PRIMARY KEY (order_id, product_id)`

The pair identifies one product's entry in one order.

For example:

| order_id | product_id |
| ---: | ---: |
| 1001 | 1 |
| 1001 | 2 |
| 1002 | 1 |

The pair `(1001, 1)` is unique even though `1001` appears multiple times and `1` appears multiple times.

The same pair cannot be inserted twice.

Composite keys are particularly useful for junction tables and relationships where the combination of two or more values represents a unique association.

---

## 8. Foreign keys

A foreign key connects a row to another table.

The `orders` table contains:

`customer_id`

and references:

`customers(customer_id)`

Conceptually:

`customers 1 ---- many orders`

One customer can have many orders.

Each order belongs to one customer.

The foreign key protects referential integrity.

If customer `999` does not exist, an order referring to customer `999` should normally be rejected when foreign-key enforcement is active.

The Python program explicitly enables SQLite foreign-key enforcement with:

`PRAGMA foreign_keys = ON`

This is important because SQLite has connection-level foreign-key behavior that should not simply be assumed to be enabled.

---

## 9. Referential integrity

Referential integrity means that relationships between tables remain valid.

Suppose:

`orders.customer_id = 10`

If `customers.customer_id = 10` does not exist, the order contains an invalid reference.

A foreign-key constraint can prevent this.

Referential actions can also specify what happens when a referenced row changes or is deleted.

Common actions include:

- `CASCADE`
- `RESTRICT`
- `NO ACTION`
- `SET NULL`
- `SET DEFAULT`

The Python `order_items` table uses:

`ON DELETE CASCADE`

for the relationship from order items to orders.

When an order is deleted, dependent order-item rows are deleted automatically under this rule.

Cascading operations must be designed carefully because a single deletion can affect many dependent records.

---

## 10. Schemas

A schema describes the structure of a database.

Depending on the DBMS, the term can have slightly different meanings.

At a conceptual level, a schema describes objects such as:

- tables
- columns
- constraints
- indexes
- views
- relationships
- sometimes procedures, functions, sequences, and other objects

The Python implementation demonstrates schema inspection using SQLite metadata and `PRAGMA` commands.

For example, `PRAGMA table_info(customers)` exposes information about the columns in the `customers` table.

Different DBMS products expose metadata differently.

PostgreSQL provides information through `information_schema` and system catalogs.

SQLite exposes metadata through mechanisms including `sqlite_master` and `PRAGMA`.

---

## 11. SQL

SQL stands for Structured Query Language.

SQL is primarily declarative.

A declarative statement specifies what should be retrieved or changed.

For example:

`SELECT product_name FROM products WHERE price >= 5000`

states that the application wants product names whose prices meet the condition.

The application does not normally specify:

- which physical page to read first
- which index node to visit
- which join algorithm to use
- how database buffers should be managed
- how the storage engine should retrieve the rows

The database engine decides those implementation details.

This distinction is fundamental to understanding SQL.

---

## 12. SQL statement categories

SQL statements are commonly discussed using categories such as:

### DDL

Data Definition Language.

Examples:

- `CREATE`
- `ALTER`
- `DROP`

DDL changes database structures.

### DML

Data Manipulation Language.

Examples:

- `INSERT`
- `UPDATE`
- `DELETE`

These statements modify stored data.

### DQL

Data Query Language is sometimes used as a teaching category for `SELECT`.

### DCL

Data Control Language.

Examples include:

- `GRANT`
- `REVOKE`

These deal with permissions in systems that support them.

### TCL

Transaction Control Language.

Examples include:

- `BEGIN`
- `COMMIT`
- `ROLLBACK`

Exact terminology and statement behavior vary between SQL products.

---

## 13. CREATE TABLE

The Python schema uses `CREATE TABLE` to define database structures.

A simplified example is:

`CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)`

The statement defines:

- a table
- columns
- types
- a primary key
- `NOT NULL` constraints
- a uniqueness constraint

The database records this structural information as metadata.

---

## 14. INSERT

`INSERT` adds rows.

The Python implementation inserts customers with a parameterized statement:

`INSERT INTO customers (customer_id, full_name, email) VALUES (?, ?, ?)`

The `?` markers are parameter placeholders used by SQLite's Python driver.

The actual values are supplied separately.

This separation is important for both correctness and security.

---

## 15. SELECT

`SELECT` retrieves data.

Examples used by the Python implementation include selecting:

- specific columns
- all columns
- calculated expressions
- filtered rows
- sorted rows
- joined results
- grouped results

Explicit column selection is generally clearer than `SELECT *` in application code.

`SELECT *` can become problematic when:

- a table gains new columns
- the application depends on result ordering or structure
- unnecessary data is transferred
- sensitive columns become unintentionally exposed

---

## 16. WHERE

`WHERE` filters rows.

For example:

`WHERE price >= 5000`

selects only rows satisfying the condition.

Common comparison operators include:

- `=`
- `<>`
- `!=`
- `<`
- `>`
- `<=`
- `>=`

Logical operators include:

- `AND`
- `OR`
- `NOT`

Other useful conditions include:

- `IN`
- `BETWEEN`
- `LIKE`
- `IS NULL`
- `IS NOT NULL`
- `EXISTS`

---

## 17. NULL

SQL `NULL` represents an absent or unknown value.

It is not the same thing as:

- zero
- an empty string
- the string `"NULL"`

A common mistake is:

`WHERE email = NULL`

This does not correctly test for SQL NULL.

Use:

`WHERE email IS NULL`

or:

`WHERE email IS NOT NULL`

SQL expressions involving NULL can produce `UNKNOWN`, which is part of SQL's three-valued logic:

- TRUE
- FALSE
- UNKNOWN

This behavior is one reason SQL conditions involving nullable columns require care.

The Python implementation explicitly demonstrates the difference between `NULL` and an empty string.

---

## 18. UPDATE

`UPDATE` modifies existing rows.

The Python implementation uses:

`UPDATE products SET price = price * ? WHERE product_id = ?`

The `WHERE` condition limits the update to a specific product.

A dangerous mistake is:

`UPDATE products SET price = 0`

without a `WHERE` condition.

That statement can modify every row.

For destructive or large-scale updates, applications should verify the intended scope before executing the statement.

---

## 19. DELETE

`DELETE` removes rows.

Example:

`DELETE FROM customers WHERE customer_id = ?`

Again, a missing `WHERE` condition can remove every row in the table.

Production applications should treat broad `UPDATE` and `DELETE` statements carefully.

---

## 20. JOINs

A relational database becomes powerful when related tables can be combined.

The Python implementation demonstrates joins between:

- customers
- orders
- order items
- products

The relationship chain is:

`customers -> orders -> order_items -> products`

A joined report can show:

- order number
- customer name
- product name
- quantity
- unit price
- line total

### INNER JOIN

An `INNER JOIN` returns rows for which the join condition matches.

Example:

`orders JOIN customers ON orders.customer_id = customers.customer_id`

### LEFT JOIN

A `LEFT JOIN` preserves every row from the left table.

If a matching row does not exist on the right, the right-side columns can contain NULL.

This is useful for questions such as:

"Show every customer, including customers who have never placed an order."

### Other join forms

SQL systems may support:

- `RIGHT JOIN`
- `FULL OUTER JOIN`
- `CROSS JOIN`
- self joins

Support and behavior vary by database product and version.

---

## 21. Relationship cardinality

Important relationship patterns include:

### One-to-one

One record corresponds to at most one record in another table.

A unique foreign key is commonly used to enforce this structure.

### One-to-many

One parent has many children.

The case study uses:

`customer -> orders`

A customer can have multiple orders.

### Many-to-many

Many rows on one side can relate to many rows on the other side.

The order system has:

`orders <-> products`

One order can contain many products.

One product can appear in many orders.

The relationship is represented by `order_items`.

This converts the many-to-many relationship into two one-to-many relationships:

`orders -> order_items`

and:

`products -> order_items`

---

## 22. Order items as a junction table

The `order_items` table is one of the most important structures in the implementations.

It contains:

- `order_id`
- `product_id`
- `quantity`
- `unit_price`

The first two columns establish the relationship.

The other columns contain attributes of that relationship.

`quantity` is not an attribute of the product itself. It describes how many units of the product were included in a particular order.

`unit_price` represents the price used for that order line.

Storing the historical unit price can be important because the current product price may change after an order is placed.

---

## 23. Aggregate functions

SQL provides aggregate functions for working with groups of rows.

Common functions include:

- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`

The Python implementation calculates customer spending using:

`SUM(quantity * unit_price)`

This demonstrates how SQL can transform detailed transaction rows into business-level information.

---

## 24. GROUP BY

`GROUP BY` divides rows into groups.

For example:

`GROUP BY customer_id`

creates one logical group for each customer ID.

An aggregate such as:

`COUNT(*)`

can then calculate a value for each group.

The C++ case study represents this idea using a map keyed by `customerId`.

---

## 25. HAVING

`HAVING` filters groups after aggregation.

The distinction is important:

`WHERE`

filters individual rows.

`HAVING`

filters groups created by `GROUP BY`.

For example, a query can group orders by customer and then use `HAVING` to retain customers whose total spending exceeds a threshold.

---

## 26. ORDER BY

`ORDER BY` controls result ordering.

Without `ORDER BY`, SQL does not guarantee that rows will be returned in a particular meaningful order.

The Python implementation uses explicit ordering when displaying products and customer totals.

When pagination is involved, deterministic ordering is especially important.

A unique tie-breaker such as an ID can make ordering more stable.

---

## 27. LIMIT and pagination

`LIMIT` restricts the number of rows returned in systems such as SQLite.

`OFFSET` can be used to skip rows.

For example:

`LIMIT 3 OFFSET 3`

can represent the second page of a three-row-per-page result.

Offset pagination is simple but can become inefficient for large offsets because the database may still need to locate or process many preceding rows.

Keyset or cursor-based pagination can be more efficient for some large datasets.

---

## 28. Subqueries

A subquery is a query nested inside another query.

The Python implementation demonstrates:

- scalar subqueries
- `EXISTS`

`EXISTS` is useful when the application only needs to know whether a related row exists.

For example:

`WHERE EXISTS (...)`

can identify customers who have at least one order.

Subqueries can often be rewritten using joins or other constructs. Which form is preferable depends on clarity, semantics, and the database optimizer.

---

## 29. Views

A view is a named query.

The Python implementation creates:

`customer_order_totals`

The view presents customer spending as a reusable logical result.

Views can be useful for:

- reusable reporting logic
- abstraction
- controlled exposure of columns
- simplifying complex application queries

The behavior and performance of views depend on the DBMS and the underlying query.

A view should not automatically be assumed to materialize its result. Ordinary views are often logical query definitions rather than stored result sets.

---

## 30. Constraints

Constraints are database-level rules that help protect data quality.

The implementations demonstrate:

### PRIMARY KEY

Ensures row identity and uniqueness.

### FOREIGN KEY

Maintains relationships between tables.

### NOT NULL

Prevents NULL values in required columns.

### UNIQUE

Prevents duplicate values according to the database's uniqueness rules.

### CHECK

Enforces a Boolean condition.

The product table uses checks such as:

`price >= 0`

and:

`stock_quantity >= 0`

The order item table uses:

`quantity > 0`

Constraints are important because application validation alone is insufficient.

Multiple applications, processes, scripts, or services may access the same database.

The database itself should protect critical invariants.

---

## 31. Application validation versus database validation

Application-level validation is useful for producing immediate and user-friendly error messages.

The Python implementation validates `ProductInput`.

The JavaScript implementation validates product objects.

The C++ implementation validates domain objects before inserting them.

Database constraints remain necessary.

For example, two application requests might simultaneously attempt to insert the same email address.

Even if both applications independently check whether the email appears unused, both checks could occur before either insertion.

A database-level `UNIQUE` constraint provides authoritative protection.

---

## 32. Transactions

A transaction groups multiple database operations into one logical unit.

The common ACID properties are:

### Atomicity

The transaction is treated as a unit.

If an important operation fails, the transaction can be rolled back.

### Consistency

A successful transaction should preserve database rules and constraints.

### Isolation

Concurrent transactions should not improperly interfere with one another.

The exact isolation guarantees depend on the DBMS and configuration.

### Durability

After commit, the database provides persistence guarantees appropriate to its storage and configuration.

---

## 33. Transaction case study

The order operation is designed as a transaction.

The logical steps are:

1. validate the order
2. verify the customer
3. verify every product
4. verify stock
5. create the order
6. create order items
7. reduce stock
8. commit

If stock validation or another operation fails, the complete operation should be rolled back.

This prevents situations where:

- the order exists but order items do not
- order items exist but stock was not reduced
- stock was reduced but the order was never created

The Python implementation performs the operation using SQLite transactions.

The C++ implementation uses a database snapshot to simulate rollback semantics without an external database library.

---

## 34. Concurrency and race conditions

The JavaScript implementation illustrates a stock race condition.

Imagine that one unit remains in stock.

Two requests can both read:

`stock_quantity = 1`

Both may conclude that they can sell one unit.

Without appropriate concurrency control, both requests might succeed incorrectly.

Real database systems provide mechanisms such as:

- transactions
- isolation levels
- row-level locks
- optimistic concurrency
- atomic conditional updates
- database-specific locking mechanisms

The appropriate approach depends on the DBMS and workload.

---

## 35. SQL execution model

A simplified model of SQL execution is:

1. Application sends SQL and parameters.
2. Database driver communicates with the DBMS.
3. Database parses SQL.
4. Database resolves table and column names.
5. Database validates the statement.
6. Query optimizer chooses an execution strategy.
7. Execution engine accesses tables and indexes.
8. Rows are filtered, joined, grouped, sorted, or modified.
9. Results or affected-row information are returned to the driver.
10. The application receives the result.

This is a conceptual model.

A database engine may perform optimization and physical operations in ways that do not directly correspond to this simple sequence.

---

## 36. Logical processing order of SELECT

A common logical model for a query is:

`FROM / JOIN`

then:

`WHERE`

then:

`GROUP BY`

then:

`HAVING`

then:

`SELECT`

then:

`DISTINCT`

then:

`ORDER BY`

then:

`LIMIT / OFFSET`

This helps explain SQL behavior.

For example, an alias created in the `SELECT` list is generally not available to the `WHERE` clause because `WHERE` logically occurs before `SELECT`.

The database optimizer can physically rearrange operations as long as the resulting behavior remains correct.

---

## 37. Query optimizer

The optimizer determines how a SQL query should be executed.

Possible decisions include:

- whether to use an index
- which table to access first
- which join strategy to use
- whether to sort
- whether to use a particular scan
- how to combine filtering and other operations

The optimizer can choose among multiple physically different strategies that produce the same logical result.

This is one of the major reasons SQL is declarative.

The programmer describes the required result while the DBMS chooses an execution strategy.

---

## 38. Indexes

An index is a data structure used to accelerate certain access patterns.

For example:

`CREATE INDEX idx_orders_customer_id ON orders(customer_id)`

can support queries filtering by `customer_id`.

Without a suitable index, the database may need to examine many rows.

With an appropriate index, it may locate matching rows more efficiently.

Indexes have costs:

- additional disk space
- additional memory/cache usage
- insert overhead
- update overhead
- delete overhead
- maintenance complexity

An index should therefore be created based on actual query patterns and measurements.

The Python implementation uses `EXPLAIN QUERY PLAN` to inspect how SQLite approaches a query.

Different DBMS products expose query plans using different commands and levels of detail.

---

## 39. Performance considerations

Important performance factors include:

### Number of rows

A query that is fast over 100 rows may behave very differently over 100 million rows.

### Indexes

Indexes can improve selective lookups but add write cost.

### Joins

Join performance depends on:

- table size
- indexes
- join conditions
- data distribution
- optimizer decisions
- available memory

### Network transfer

Retrieving unnecessary rows or columns wastes application/database communication.

### Aggregation

Grouping and aggregation may require sorting, hashing, memory, or temporary structures.

### Query plan

Execution-plan analysis can reveal:

- full scans
- index usage
- join order
- expensive operations
- estimated costs

Performance should be measured with realistic data rather than inferred solely from query appearance.

---

## 40. Data types

Relational systems commonly provide types such as:

- integer
- decimal
- numeric
- floating-point
- character
- text
- date
- time
- timestamp
- boolean
- binary

Exact types differ between DBMS products.

### Financial values

Binary floating-point values can introduce representation issues.

For financial applications, fixed-precision decimal or numeric types are commonly appropriate when supported by the chosen database.

The C++ implementation stores money as integer paise rather than floating-point rupees:

`long long pricePaise`

This avoids binary floating-point representation problems for the modeled currency amounts.

The production choice should reflect the target database and business requirements.

---

## 41. SQL injection

SQL injection occurs when untrusted input is allowed to change the structure of a SQL statement.

An unsafe pattern conceptually looks like:

`SELECT ... WHERE email = 'user_input'`

where the application directly concatenates user input into SQL.

The safe approach is parameterized SQL.

The Python implementation uses placeholders such as `?` and supplies values separately.

The JavaScript implementation demonstrates the same conceptual separation.

A parameterized query tells the database driver:

- this is the SQL structure
- this is the value

The supplied value is not supposed to become SQL syntax.

Parameterized queries should be the default approach for dynamic values.

---

## 42. Identifiers versus values

A subtle SQL security issue is the difference between values and identifiers.

A value is something such as:

`"asha@example.com"`

A database identifier is something such as:

`customers`

or:

`email`

Ordinary query parameters are designed for values.

An application that needs dynamic table or column names should use carefully controlled allowlists or database-driver-specific identifier mechanisms.

It should not assume that ordinary value parameters can safely replace arbitrary SQL identifiers.

---

## 43. JavaScript implementation

The JavaScript file demonstrates the application layer.

It covers:

- JavaScript objects representing database rows
- arrays representing collections of rows
- schema metadata
- SQL statement construction
- parameterized query structure
- validation
- filtering
- mapping
- joining related records
- aggregation
- asynchronous transaction structure
- race-condition reasoning
- an `OrderService` class
- indexing concepts
- NULL behavior
- common application mistakes

JavaScript is particularly useful for showing how a web or Node.js application interacts with a relational database.

A real Node.js application would normally use a database driver or database library.

That dependency is intentionally omitted here so the file remains self-contained.

---

## 44. Python implementation

The Python implementation uses the built-in `sqlite3` module.

This makes the Python file an actual executable SQL study environment rather than a collection of SQL strings.

It demonstrates:

- creating a database
- enabling foreign keys
- creating tables
- inspecting schema metadata
- inserting rows
- selecting rows
- filtering
- sorting
- updating
- deleting
- joins
- aggregation
- constraints
- composite primary keys
- foreign keys
- transactions
- rollback
- parameterized queries
- SQL injection prevention
- indexes
- query plans
- normalization
- data types
- validation
- pagination
- subqueries
- views
- transactional order processing
- tests
- cascading deletion

SQLite is particularly suitable for an introductory executable because it requires no separate database server.

---

## 45. C++ case study

The C++ program models a complete order-management database.

Its domain consists of:

- customers
- products
- orders
- order items

The implementation uses standard-library containers:

- `std::map`
- `std::set`
- `std::vector`
- `std::optional`
- strings and numeric types

The database schema is represented using classes:

- `CustomerTable`
- `ProductTable`
- `OrderTable`
- `OrderItemTable`

The `Database` class groups the tables into a schema-like structure.

---

## 46. C++ primary key implementation

The customer table stores rows in:

`std::map<int, Customer>`

where the integer key is `customerId`.

This models a primary-key lookup.

The table rejects duplicate IDs.

The product and order tables use the same conceptual pattern.

For `order_items`, a custom `OrderItemKey` contains:

- `orderId`
- `productId`

The pair acts as the composite primary key.

---

## 47. C++ foreign-key implementation

When an order is inserted, the C++ implementation checks whether the referenced customer exists.

This models:

`FOREIGN KEY (customer_id) REFERENCES customers(customer_id)`

When an order item is inserted, it verifies:

- the order exists
- the product exists

These checks model referential integrity.

The C++ program is not a replacement for a production DBMS. It is an educational case study that exposes the mechanisms that a database engine normally provides internally.

---

## 48. C++ order-processing algorithm

The order-processing function performs these steps:

1. validate the request
2. consolidate duplicate product entries
3. verify the customer
4. verify each product
5. verify stock
6. save a transaction snapshot
7. insert the order
8. insert order items
9. reduce stock
10. restore the snapshot if any operation fails

This demonstrates why several related modifications should be treated as one logical transaction.

A real database engine would provide transaction isolation, durability, locking, logging, and recovery mechanisms rather than copying an entire application-level data structure.

---

## 49. C++ joins

The C++ `buildOrderReport` function reconstructs a joined report.

Conceptually, it performs:

`orders JOIN customers`

followed by:

`JOIN order_items`

followed by:

`JOIN products`

The resulting report contains:

- order ID
- customer name
- product name
- quantity
- unit price
- line total

The implementation uses keyed containers for lookup.

A real SQL database has sophisticated join algorithms and query optimization mechanisms.

---

## 50. C++ aggregation

The C++ implementation calculates customer spending using a map keyed by customer ID.

Conceptually, this corresponds to:

`GROUP BY customer_id`

combined with:

`SUM(quantity * unit_price)`

The results are then sorted by total spending.

This shows how an SQL aggregate can be represented algorithmically outside a database.

---

## 51. Normalization

Normalization is a set of principles for organizing relational data.

A poorly designed order table might contain:

- order ID
- customer name
- customer email
- product 1
- product 1 price
- product 1 quantity
- product 2
- product 2 price
- product 2 quantity

This design creates problems.

### Update anomaly

If a customer's email is stored in hundreds of order rows, changing the email requires updating many records.

### Insertion anomaly

It may be difficult to create a customer record without also creating an order.

### Deletion anomaly

Deleting the last order for a customer could accidentally remove the only stored copy of the customer's information.

### Repeating groups

Fixed columns such as `product_1`, `product_2`, and `product_3` limit the model and make queries difficult.

A normalized design separates the concepts into related tables.

---

## 52. Practical normalization structure

The case study uses:

`customers`

for customer data.

`products`

for product data.

`orders`

for order headers.

`order_items`

for individual products within orders.

This is a common relational pattern.

Normalization should not be treated as a requirement to split every possible attribute into separate tables.

Highly normalized designs can sometimes increase query complexity.

Denormalization can be appropriate when justified by:

- measured performance
- reporting requirements
- access patterns
- data warehouse design
- caching strategies
- read-heavy workloads

Denormalization should be deliberate rather than accidental.

---

## 53. Constraints versus application code

A useful architectural principle is:

**Application validation improves usability. Database constraints protect integrity.**

The application may check:

- whether a product name is empty
- whether a quantity is positive
- whether an ID has the expected format

The database should still enforce critical rules such as:

- unique IDs
- unique email addresses
- valid foreign keys
- non-negative stock
- valid quantities

This creates defense at multiple layers.

---

## 54. Common mistakes

### Confusing a database and a table

A database can contain many tables and other database objects.

### Assuming row order

Without `ORDER BY`, result order should not be relied upon.

### Using `= NULL`

Use `IS NULL`.

### Updating without a filter

An unrestricted `UPDATE` can change every row.

### Deleting without a filter

An unrestricted `DELETE` can remove every row.

### Concatenating SQL

Use parameters.

### Ignoring foreign keys

Invalid relationships can enter the system.

### Assuming all SQL dialects are identical

SQL syntax and features vary among SQLite, PostgreSQL, MySQL, SQL Server, Oracle, and other systems.

### Creating every possible index

Indexes have storage and write costs.

### Storing everything in one table

This often produces duplication and anomalies.

### Trusting client-side prices

The server/database should determine authoritative prices.

### Treating JavaScript arrays as databases

Arrays lack database-level durability, concurrency control, constraints, query optimization, transactions, and persistence.

---

## 55. Security considerations

Important database security principles include:

### Parameterized queries

Prevent SQL values from becoming SQL syntax.

### Least privilege

Database accounts should have only the permissions required by the application.

### Credential protection

Database credentials should not be hard-coded into source repositories.

### Authorization

A logged-in application user should not automatically have unrestricted database access.

### Input validation

Validate values at application boundaries.

### Database constraints

Enforce critical invariants in the database.

### Sensitive data

Applications should avoid returning columns that the caller is not authorized to see.

### Auditing

Systems handling sensitive or regulated information may require appropriate audit records.

Security architecture depends heavily on the application and regulatory environment.

---

## 56. Performance and complexity

The C++ implementation uses `std::map`.

A lookup is generally:

`O(log n)`

A sequential scan is:

`O(n)`

Sorting `n` values is commonly:

`O(n log n)`

Aggregation complexity depends on the implementation.

Hash-based aggregation can often approach linear average behavior, while sort-based aggregation can require approximately `O(n log n)` work.

Database engines use specialized indexes and storage structures.

The important lesson is that database performance depends on more than SQL text.

It also depends on:

- data volume
- indexes
- statistics
- storage
- memory
- concurrency
- network latency
- optimizer decisions
- schema design
- query selectivity

---

## 57. Database versus application responsibilities

A clean system separates responsibilities.

### Database

The database should generally handle:

- persistent storage
- constraints
- referential integrity
- transactions
- query execution
- indexing
- concurrency control
- durable state

### Application

The application generally handles:

- business workflows
- user interaction
- request validation
- authorization decisions
- presentation
- API contracts
- application-specific calculations
- orchestration

The boundary varies by architecture, but the distinction helps prevent responsibilities from becoming confused.

---

## 58. Python, JavaScript, and C++ comparison

| Aspect | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| Main role in this study | Actual SQLite SQL execution | Application/database interaction model | Relational system case study |
| Database dependency | Built-in SQLite support | None | None |
| SQL executed directly | Yes | No | No |
| Primary keys | Real SQLite constraints | Modeled conceptually | Explicit class/container enforcement |
| Foreign keys | Real SQLite enforcement | Modeled in application concepts | Explicit relationship checks |
| Transactions | Real SQLite transaction behavior | Transaction flow simulation | Snapshot-based rollback simulation |
| Joins | Real SQL joins | JavaScript lookup equivalent | Explicit join algorithm |
| Aggregation | SQL `GROUP BY` and aggregates | JavaScript aggregation | Map-based aggregation |
| Query planning | SQLite `EXPLAIN QUERY PLAN` | Conceptual | Conceptual |
| Main educational value | Direct SQL experimentation | Application integration | Systems and implementation reasoning |

No one language replaces the others in this study.

Python exposes an actual relational engine.

JavaScript demonstrates how a modern application layer can communicate with a relational database.

C++ exposes the underlying data-structure and algorithmic ideas that a database engine must implement.

---

## 59. Important distinctions

### Table versus schema

A table is one database object containing structured rows.

A schema describes database structure and can include many objects.

### Primary key versus foreign key

A primary key identifies a row in its own table.

A foreign key references a key in another table.

### Row versus column

A row represents one record.

A column represents one attribute.

### SQL versus DBMS

SQL is the language.

The DBMS is the software that parses and executes SQL and manages database state.

### Database versus application

The database stores and manages persistent structured data.

The application implements user-facing and business workflows.

### Constraint versus validation

Application validation improves input handling.

Database constraints provide authoritative data integrity.

### Logical query processing versus physical execution

Logical processing explains SQL semantics.

Physical execution describes what the database engine actually does internally.

---

## 60. Production considerations

A production relational database requires more than writing valid SQL.

Important considerations include:

- schema migration strategy
- backups
- disaster recovery
- monitoring
- access control
- connection management
- transaction design
- indexing
- query performance
- concurrency
- logging
- data retention
- encryption
- credential management
- capacity planning
- replication where appropriate
- testing
- operational recovery procedures

The exact architecture depends on the database product and system requirements.

---

## 61. Edge cases demonstrated

The implementations intentionally include several edge cases:

- duplicate primary keys
- duplicate unique values
- missing foreign-key parents
- NULL values
- empty strings
- negative prices
- negative stock
- zero quantities
- duplicate composite keys
- insufficient stock
- failed transactions
- cascading deletion
- malicious-looking SQL input
- pagination
- customers without orders
- duplicate products within an order request
- query execution planning

These cases are important because database correctness is often determined by behavior at boundaries rather than by the simplest successful query.

---

## 62. Practical order-processing model

The complete order workflow can be viewed as:

`Customer`

↓

`Order`

↓

`Order Item`

↓

`Product`

The customer owns the order.

The order contains order items.

Each order item identifies a product.

The order item also records the quantity and historical unit price.

This structure provides a clear relational representation of an e-commerce transaction.

---

## 63. SQL execution in an application

A typical application architecture can be represented conceptually as:

`User`

↓

`Application`

↓

`Database Driver`

↓

`Database Engine`

↓

`Tables / Indexes / Storage`

The application sends a SQL statement and parameters.

The driver handles database communication.

The database engine:

- parses the SQL
- resolves objects
- checks constraints
- plans the query
- executes it
- returns results

The application then maps those results into application-level structures.

This architecture applies whether the application is written in Python, JavaScript, Java, C++, Go, C#, or another language.

---

## 64. Why relational databases remain useful

Relational databases are particularly effective when an application requires:

- structured data
- relationships between entities
- strong integrity constraints
- transactions
- predictable query semantics
- complex joins
- aggregation
- consistent updates

The relational model gives applications a formal structure for representing entities and relationships.

SQL then provides a standardized family of operations for interacting with that model, while individual DBMS products provide the storage, optimization, transaction, and concurrency mechanisms underneath it.
