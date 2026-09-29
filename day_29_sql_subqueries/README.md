# SQL Subqueries: Scalar, Correlated, Nested, EXISTS, and NOT EXISTS

## 1. Topic Introduction

A SQL subquery is a query written inside another SQL statement. The inner query produces a value, a set of values, rows, or an existence condition that the outer query uses to make a decision.

Subqueries are useful when a query needs information that must be calculated or filtered before the outer query can complete.

The central patterns covered in this study are:

- Scalar subqueries
- Multi-row subqueries
- Nested subqueries
- Correlated subqueries
- `EXISTS`
- `NOT EXISTS`
- Subqueries in `SELECT`
- Subqueries in `WHERE`
- Subqueries in `FROM`
- Aggregate subqueries
- Derived tables
- Anti-existence logic
- Relational division using nested `NOT EXISTS`
- `NULL` and `NOT IN`
- Query performance and indexing
- Alternatives involving joins and window functions

The three implementations use the same conceptual sales domain:

- `customers`
- `products`
- `orders`
- `order_items`

The Python implementation executes real SQL against SQLite. The JavaScript implementation models relational and subquery behavior using native JavaScript structures. The C++ implementation develops an industry-style analytics case study using C++17 data structures and indexes.

---

## 2. Relational Model Used by the Examples

The examples use four primary relations.

### Customers

Important attributes:

- `customer_id`
- `customer_name`
- `city`
- `segment`

### Products

Important attributes:

- `product_id`
- `product_name`
- `category`
- `price`
- `active`

### Orders

Important attributes:

- `order_id`
- `customer_id`
- `order_date`
- `status`

### Order Items

Important attributes:

- `order_id`
- `product_id`
- `quantity`
- `unit_price`

The relationships are:

- One customer can have many orders.
- One order can have many order items.
- One product can appear in many order items.
- `orders.customer_id` references `customers.customer_id`.
- `order_items.order_id` references `orders.order_id`.
- `order_items.product_id` references `products.product_id`.

This model is useful for subquery demonstrations because many realistic questions require information from related tables.

---

## 3. Fundamental Concept: What Is a Subquery?

A subquery is a query nested inside another SQL statement.

A basic example is:

`SELECT product_name, price FROM products WHERE price > (SELECT AVG(price) FROM products);`

The inner query:

`SELECT AVG(price) FROM products`

calculates one value.

The outer query then compares every product price with that value.

Conceptually:

1. Calculate the average product price.
2. Use that result as a comparison value.
3. Return products above the average.

A subquery therefore allows one query to depend on the result of another query.

---

## 4. Major Subquery Categories

Subqueries can be classified by both their result and their relationship with the outer query.

### 4.1 Scalar subquery

A scalar subquery produces one value.

Typical examples include:

- `AVG()`
- `MAX()`
- `MIN()`
- `COUNT()`
- a single selected column from one logical row

Example:

`WHERE price > (SELECT AVG(price) FROM products)`

The inner query supplies one value.

### 4.2 Multi-row subquery

A multi-row subquery produces multiple values.

It is commonly combined with:

- `IN`
- `NOT IN`
- `EXISTS`
- `NOT EXISTS`

Example:

`WHERE customer_id IN (SELECT customer_id FROM orders WHERE status = 'Delivered')`

The inner query can return many customer IDs.

### 4.3 Correlated subquery

A correlated subquery references a value from the current row of the outer query.

Example:

`WHERE p.price > (SELECT AVG(p2.price) FROM products p2 WHERE p2.category = p.category)`

The inner query depends on `p.category`, which comes from the outer query.

### 4.4 Non-correlated subquery

A non-correlated subquery does not depend on the current outer row.

Example:

`WHERE price > (SELECT AVG(price) FROM products)`

The inner query can logically be evaluated independently of each outer row.

### 4.5 Nested subquery

A nested subquery contains another subquery.

For example:

`SELECT ... WHERE customer_id IN (SELECT customer_id FROM orders WHERE order_id IN (SELECT order_id FROM ...))`

Multiple logical stages are nested inside one another.

---

## 5. Scalar Subqueries

A scalar subquery is used where SQL expects one value.

A common pattern is:

`SELECT product_name, price FROM products WHERE price > (SELECT AVG(price) FROM products);`

The inner query calculates the global average.

The outer query performs the comparison.

### Common scalar operations

Typical scalar aggregate expressions include:

- `(SELECT AVG(price) FROM products)`
- `(SELECT MAX(price) FROM products)`
- `(SELECT MIN(price) FROM products)`
- `(SELECT COUNT(*) FROM orders)`

### Scalar subquery in SELECT

A scalar subquery can also appear in the selected columns.

Example:

`SELECT product_name, price, (SELECT AVG(price) FROM products) AS average_price FROM products;`

The same average is displayed beside every product.

### Important cardinality rule

The logical expectation of a scalar subquery is one value.

This distinction is important:

- Zero rows may produce `NULL` depending on the expression and database.
- One row produces one scalar value.
- Multiple rows violate the intended scalar cardinality.

Database behavior for invalid multi-row scalar expressions can differ, so production queries should make the intended cardinality explicit.

---

## 6. Aggregate Subqueries

Aggregate functions are especially common in scalar subqueries.

For example:

`SELECT AVG(price) FROM products`

returns one aggregate result.

The outer query can then compare individual rows against it.

Other useful aggregate comparisons include:

`WHERE price = (SELECT MAX(price) FROM products)`

`WHERE price = (SELECT MIN(price) FROM products)`

`WHERE order_count > (SELECT AVG(order_count) FROM ...)`

Aggregate subqueries are useful for threshold-based analysis.

---

## 7. Multi-Row Subqueries and IN

A multi-row subquery can return a set of values.

Example:

`SELECT customer_name FROM customers WHERE customer_id IN (SELECT customer_id FROM orders WHERE status = 'Delivered');`

The inner query produces customer IDs.

The outer query selects customers whose IDs occur in that set.

The logical structure is:

1. Find qualifying IDs.
2. Test whether each outer ID belongs to those IDs.
3. Return matching rows.

### Why IN is useful

`IN` is appropriate when the requirement is naturally expressed as membership.

For example:

- products belonging to selected categories
- customers with qualifying orders
- employees belonging to selected departments
- records whose IDs occur in another result

---

## 8. NOT IN and the NULL Problem

`NOT IN` deserves special attention because of SQL's three-valued logic.

SQL predicates can evaluate to:

- `TRUE`
- `FALSE`
- `UNKNOWN`

Consider:

`3 NOT IN (1, 2, NULL)`

The comparison against `NULL` is not `TRUE` or `FALSE`. It is `UNKNOWN`.

As a result, a `NOT IN` condition involving a nullable subquery can produce surprising results.

This is one reason `NOT EXISTS` is often preferred for anti-existence logic.

The Python program explicitly creates a nullable relation to demonstrate this issue.

The JavaScript and C++ implementations also explain the distinction conceptually.

---

## 9. EXISTS

`EXISTS` answers a Boolean question:

> Does at least one matching row exist?

Example:

`SELECT c.customer_name FROM customers AS c WHERE EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);`

The contents of the inner row are not important.

The important fact is whether at least one matching row exists.

### Why SELECT 1 is common

Inside `EXISTS`, the selected value does not normally matter.

Therefore:

`SELECT 1`

is a conventional way to communicate that the query is an existence test.

These are logically equivalent existence tests:

`EXISTS (SELECT 1 FROM orders ...)`

and

`EXISTS (SELECT customer_id FROM orders ...)`

The important part is the existence of a qualifying row.

---

## 10. EXISTS Versus IN

`IN` and `EXISTS` can sometimes express similar requirements, but they communicate different concepts.

### IN

`IN` focuses on membership:

`customer_id IN (SELECT customer_id FROM orders ...)`

The outer value is compared with values returned by the inner query.

### EXISTS

`EXISTS` focuses on relationship existence:

`EXISTS (SELECT 1 FROM orders WHERE orders.customer_id = customers.customer_id)`

The inner query is correlated with the current outer row.

A useful design question is:

> Do I need values from the inner result, or do I only need to know whether a relationship exists?

If only existence matters, `EXISTS` is often the clearer expression.

Actual performance depends on the database optimizer, indexes, data distribution, and query structure.

---

## 11. NOT EXISTS

`NOT EXISTS` asks whether no qualifying related row exists.

Example:

`SELECT p.product_name FROM products AS p WHERE NOT EXISTS (SELECT 1 FROM order_items AS oi WHERE oi.product_id = p.product_id);`

This finds products that have never appeared in an order item.

The logical structure is:

1. Take one product.
2. Search for related order items.
3. If a matching row exists, reject the product.
4. If no matching row exists, keep the product.

This is an anti-existence operation.

---

## 12. NOT EXISTS Versus NOT IN

For anti-join requirements, the following pattern is usually robust:

`WHERE NOT EXISTS (SELECT 1 FROM related_table WHERE related_table.key = outer_table.key)`

It avoids the specific `NULL` poisoning problem associated with `NOT IN`.

This does not mean `NOT IN` is always wrong.

`NOT IN` can be appropriate when:

- the subquery column is guaranteed `NOT NULL`
- the semantics are clearly membership-based
- the query is tested against the target database

The important issue is understanding `NULL` semantics rather than applying a rule mechanically.

---

## 13. Correlated Subqueries

A correlated subquery references the outer query.

Example:

`SELECT c.customer_name, (SELECT MAX(o.order_date) FROM orders AS o WHERE o.customer_id = c.customer_id) AS latest_order FROM customers AS c;`

The inner query references:

`c.customer_id`

The value belongs to the current outer customer.

This creates a correlation between the two query levels.

### Logical execution model

A simplified conceptual model is:

1. Select one customer.
2. Use that customer's ID inside the subquery.
3. Calculate the customer's latest order.
4. Return the result.
5. Repeat the logical operation for the next customer.

Actual database engines may optimize this substantially. The conceptual model explains the dependency between the query levels, not necessarily the physical execution plan.

---

## 14. Correlated Aggregate Example

A useful business question is:

> Which products are more expensive than the average product in their own category?

The query pattern is:

`SELECT p.product_name, p.category, p.price FROM products AS p WHERE p.price > (SELECT AVG(p2.price) FROM products AS p2 WHERE p2.category = p.category);`

The important relationship is:

`p2.category = p.category`

The inner query changes based on the outer product's category.

For a product in `Accessories`, the inner query calculates the average of active accessories.

For a product in `Computers`, it calculates the average of active computers.

---

## 15. Correlated EXISTS

`EXISTS` becomes especially useful when correlated.

Example:

`SELECT c.customer_name FROM customers AS c WHERE EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id AND o.status = 'Delivered');`

The inner query is evaluated in the context of each customer.

The condition asks:

> Does this customer have at least one delivered order?

This is a direct representation of a relationship requirement.

---

## 16. Nested Queries

A nested query can contain multiple levels.

For example, an application might need to identify:

> Customers who have delivered orders whose calculated order totals exceed 100,000.

The logical stages are:

1. Calculate each order's total.
2. Identify high-value orders.
3. Select delivered high-value orders.
4. Extract their customer IDs.
5. Return customer information.

This can be represented with multiple nested subqueries.

The Python implementation executes this pattern directly in SQLite.

The JavaScript implementation builds the intermediate relations explicitly.

The C++ implementation separates the calculation into functions and containers.

---

## 17. Subqueries in FROM

A subquery in `FROM` is commonly called a derived table.

Example:

`SELECT order_id, order_value FROM (SELECT order_id, SUM(quantity * unit_price) AS order_value FROM order_items GROUP BY order_id) AS order_totals WHERE order_value > 100000;`

The inner query creates an intermediate result.

The outer query treats that result as a relation.

This is useful when:

- an aggregate must be filtered
- an intermediate calculation should be named
- a complex transformation is easier to understand in stages
- a result needs to be queried again

A derived table must normally have an alias in SQL dialects that require it.

---

## 18. Subqueries in SELECT

A subquery can appear in the selected column list when it returns a scalar value.

Example:

`SELECT customer_name, (SELECT COUNT(*) FROM orders WHERE orders.customer_id = customers.customer_id) AS order_count FROM customers;`

This is a correlated scalar subquery.

It allows each outer row to receive a calculated value.

For large datasets, the same requirement might be expressed with aggregation and a join, or with a window function, depending on the database and desired execution plan.

---

## 19. Subqueries in WHERE

The `WHERE` clause is the most common location for subqueries.

Typical patterns include:

`WHERE price > (SELECT AVG(price) FROM products)`

`WHERE customer_id IN (SELECT customer_id FROM orders ...)`

`WHERE EXISTS (SELECT 1 FROM orders ...)`

`WHERE NOT EXISTS (SELECT 1 FROM order_items ...)`

These patterns allow the inner query to control which outer rows qualify.

---

## 20. Relational Division with Double NOT EXISTS

One of the more advanced uses of subqueries is relational division.

Consider the requirement:

> Find customers who purchased every required product.

Suppose the required products are:

- product 3
- product 4
- product 6

A nested `NOT EXISTS` formulation is conceptually:

`WHERE NOT EXISTS ( SELECT required_product WHERE NOT EXISTS ( SELECT purchase WHERE customer bought required_product ) )`

The logic is subtle.

The inner condition asks:

> Is this required product missing for the current customer?

The outer `NOT EXISTS` asks:

> Is there no required product that is missing?

Therefore the customer must have every required product.

This pattern is powerful for requirements involving "all", "every", or "for each".

---

## 21. C++ Case Study

The C++ program models a retail analytics system.

The central class is `SalesAnalytics`.

Its data structures represent the relational tables:

- `std::vector<Customer>`
- `std::vector<Product>`
- `std::vector<Order>`
- `std::vector<OrderItem>`

The implementation then constructs indexes:

- `ordersByCustomer`
- `itemsByProduct`

These indexes model the effect of database indexes used to locate related records efficiently.

### Case-study requirements

The system answers questions such as:

1. Which products are above the global average price?
2. Which customers have delivered orders?
3. Which products have never been ordered?
4. What is each customer's latest order?
5. Which products are above their category average?
6. Which customers have high-value delivered orders?
7. Which customers purchased every required product?
8. How does a repeated scan compare conceptually with indexed lookup?

---

## 22. C++ Scalar Subquery Implementation

The C++ method `averageProductPrice()` represents the scalar result:

`SELECT AVG(price) FROM products`

The `scalarSubquery()` method then uses that result to select products above the average.

This demonstrates the separation between:

- calculating one value
- applying that value to many outer rows

The C++ implementation uses `std::accumulate` to calculate the total and then divides by the number of products.

---

## 23. C++ EXISTS Implementation

The method `hasDeliveredOrder()` represents:

`EXISTS (SELECT 1 FROM orders WHERE orders.customer_id = current_customer AND status = 'Delivered')`

The indexed structure allows the method to locate a customer's orders directly.

The method can return as soon as a qualifying delivered order is found.

That mirrors an important property of existence checks: once existence has been established, additional matching rows do not change the Boolean result.

---

## 24. C++ NOT EXISTS Implementation

The method `productWasNeverOrdered()` models:

`NOT EXISTS (SELECT 1 FROM order_items WHERE order_items.product_id = current_product)`

The `itemsByProduct` index allows the system to determine whether the product has associated order-item records.

This is an anti-existence operation.

---

## 25. C++ Correlated Subquery Implementation

The method `latestOrderDate()` corresponds to the logical SQL pattern:

`SELECT MAX(o.order_date) FROM orders AS o WHERE o.customer_id = c.customer_id`

The customer ID comes from the current outer customer.

The result is optional because a customer could theoretically have no orders.

This corresponds conceptually to SQL's ability to produce a `NULL` result for an aggregate over an empty relationship.

---

## 26. C++ Derived-Table Style Processing

The C++ method `calculateCustomerRevenue()` creates an intermediate customer-revenue relation.

The subsequent method `derivedTableClassification()` classifies the intermediate result:

- `High Value`
- `Medium Value`
- `Standard`

This mirrors the SQL architecture:

1. Aggregate customer revenue.
2. Treat the aggregated relation as an intermediate result.
3. Apply classification logic.

Separating those phases is useful for readability and maintainability.

---

## 27. C++ Relational Division

The C++ method `doubleNotExists()` implements the "customer purchased every required product" requirement.

The required product set is represented by `std::set<int>`.

For every customer, the program checks every required product.

If one required product is missing, the customer fails.

If no required product is missing, the customer qualifies.

This is equivalent to the conceptual SQL structure:

`NOT EXISTS (required item that is NOT EXISTS in customer purchases)`

---

## 28. JavaScript Implementation

The JavaScript file uses arrays and functions to model relational operations.

This is useful for understanding the logical meaning of subqueries independently of a database engine.

### Scalar subqueries

The `scalarSubquery()` helper explicitly validates that a query-like function returns exactly one row.

This emphasizes scalar cardinality.

### IN

`sqlLikeIn()` demonstrates membership semantics.

### EXISTS

`sqlLikeExists()` checks whether a query-like operation produces at least one row.

### NOT EXISTS

`sqlLikeNotExists()` negates the existence condition.

### Correlation

The customer loop calculates customer-specific results by filtering related orders for the current customer.

This makes the relationship between the outer row and inner operation visible.

---

## 29. JavaScript and Eventual Database Execution

JavaScript is frequently used in application layers that communicate with databases.

Although the supplied JavaScript file intentionally avoids external database packages, the same logical patterns apply when JavaScript executes SQL through a database driver.

For production application code:

- SQL should be parameterized.
- User input should not be concatenated into SQL.
- Database errors should be handled explicitly.
- Transactions should be used when multiple writes must be atomic.
- Query performance should be measured at realistic scale.

The JavaScript implementation therefore focuses on the logical behavior rather than hiding the SQL concepts behind a database library.

---

## 30. Python Implementation

The Python implementation uses SQLite through Python's built-in `sqlite3` module.

This means it can execute real SQL without installing an external database package.

The database is created in memory, so the study file is self-contained.

The Python program creates:

- `customers`
- `products`
- `orders`
- `order_items`

It also creates indexes on important relationship columns.

The program then executes actual SQL statements covering the subquery patterns discussed in this document.

---

## 31. Python Scalar Subqueries

The Python implementation demonstrates:

- average-price comparisons
- maximum-price comparisons
- minimum-price comparisons
- scalar subqueries in the `SELECT` list

For example:

`WHERE price > (SELECT AVG(price) FROM products)`

is executed directly against SQLite.

This makes the Python implementation the most direct demonstration of actual SQL syntax among the three programs.

---

## 32. Python Correlated Queries

The Python implementation contains examples such as:

`WHERE p.price > (SELECT AVG(p2.price) FROM products AS p2 WHERE p2.category = p.category)`

The query demonstrates correlation through the outer alias `p`.

The inner alias `p2` refers to another logical instance of the same table.

This distinction is important:

- `p` represents the current outer row.
- `p2` represents rows examined by the inner query.

---

## 33. Python EXISTS and NOT EXISTS

The Python implementation demonstrates:

`EXISTS (SELECT 1 FROM orders WHERE ...)`

and:

`NOT EXISTS (SELECT 1 FROM order_items WHERE ...)`

The examples cover:

- customers with delivered orders
- products that have been ordered
- products that have never been ordered
- customers without pending orders
- customers without cancelled orders

These are practical existence and anti-existence requirements.

---

## 34. Python Nested Queries

The Python implementation also calculates order totals using a derived relation and then uses those totals in another query.

This demonstrates why nested queries can be useful for multi-stage business logic.

For complex SQL, clear aliases are important.

For example:

- `o` for orders
- `oi` for order items
- `p` for outer products
- `p2` for inner products

Meaningful aliases reduce ambiguity in correlated queries.

---

## 35. UPDATE and DELETE with Subqueries

Subqueries are not limited to `SELECT`.

The Python implementation demonstrates a temporary `UPDATE` using a scalar subquery.

It also demonstrates a temporary `DELETE` using `NOT EXISTS`.

The examples are rolled back so the study database remains unchanged.

Subqueries in data-modification statements should be handled carefully because they can affect many rows.

Before executing a production `UPDATE` or `DELETE`, it is useful to verify the corresponding `SELECT` predicate first.

For example, first inspect:

`SELECT * FROM products WHERE ...`

before applying:

`DELETE FROM products WHERE ...`

when practical.

---

## 36. Query Plans and Performance

A query's SQL text describes logical intent.

The database optimizer determines how the query will actually execute.

The Python implementation uses `EXPLAIN QUERY PLAN` to inspect execution strategies.

This distinction is essential:

> A correlated subquery is not automatically slow, and a join is not automatically faster.

Performance depends on:

- table cardinality
- indexes
- predicate selectivity
- statistics
- database engine
- optimizer behavior
- data distribution
- concurrency
- memory
- disk access
- query shape

The correct approach is measurement and plan inspection.

---

## 37. Correlated Subquery Performance

A correlated query logically depends on an outer row.

A naive implementation could repeatedly search a large table.

For example, with:

- 1 million customers
- 10 million orders

a poorly supported relationship lookup can become expensive.

An index such as:

`CREATE INDEX idx_orders_customer ON orders(customer_id);`

can make related-row lookups substantially more efficient.

The exact benefit depends on the database engine and workload.

The C++ case study models this difference using:

- repeated sequential scans
- `unordered_map`-based indexed lookup

The C++ implementation is a conceptual performance model rather than a replacement for database benchmarking.

---

## 38. EXISTS and Short-Circuiting

An existence question does not need every matching row.

If the database establishes that one qualifying row exists, the Boolean result is already known.

This makes `EXISTS` a natural expression for relationship testing.

The exact physical execution depends on the optimizer.

The important logical distinction is:

- `EXISTS` asks whether a matching relationship exists.
- An ordinary join can produce every matching relationship.
- `COUNT(*)` calculates a quantity when the quantity is actually needed.

If the requirement is only existence, expressing it as existence can communicate the requirement more directly.

---

## 39. When to Use a Subquery

Subqueries are useful when they make the requirement clear.

Typical situations include:

### Global comparison

`price > (SELECT AVG(price) FROM products)`

### Membership

`customer_id IN (SELECT customer_id FROM orders ...)`

### Existence

`EXISTS (SELECT 1 FROM orders ...)`

### Anti-existence

`NOT EXISTS (SELECT 1 FROM order_items ...)`

### Correlated comparison

`price > (SELECT AVG(price) FROM products WHERE category = outer.category)`

### Intermediate transformation

A subquery in `FROM` can create a derived table for further filtering.

### Universal requirements

Nested `NOT EXISTS` can express "for every required item" logic.

---

## 40. When a JOIN May Be Clearer

Many subquery requirements can also be expressed using joins.

For example:

`SELECT DISTINCT c.customer_name FROM customers c JOIN orders o ON o.customer_id = c.customer_id WHERE o.status = 'Delivered';`

can express a relationship that could also be written with `EXISTS`.

Neither syntax is universally superior.

Consider:

- semantic clarity
- expected cardinality
- duplicate behavior
- indexes
- optimizer behavior
- maintainability

A join can introduce duplicate outer rows when the relationship is one-to-many.

`EXISTS` naturally avoids returning duplicates caused solely by multiple matching child rows.

---

## 41. EXISTS and Duplicate Rows

Suppose one customer has five delivered orders.

A join can produce five customer rows unless the query uses:

`DISTINCT`

or aggregation.

An `EXISTS` predicate still produces one Boolean result for that customer.

Therefore:

`EXISTS` can be useful when the requirement is:

> Return the customer if at least one qualifying order exists.

rather than:

> Return every matching customer-order combination.

---

## 42. Subqueries and Window Functions

Some correlated subqueries can be replaced by window functions.

For example, finding the highest-priced product in each category can be expressed with a correlated `MAX()` subquery or with:

`RANK() OVER (PARTITION BY category ORDER BY price DESC)`

The supplied Python and JavaScript examples compare these conceptual approaches.

Window functions are often useful when the query needs both:

- row-level information
- group-level analytical information

A correlated subquery can still be preferable when its logic is clearer or when the database optimizer handles it effectively.

---

## 43. Common Mistakes

### Mistake 1: Assuming every subquery is scalar

This is incorrect:

`WHERE customer_id = (SELECT customer_id FROM orders)`

if the inner query can return many rows.

Use `IN` when the requirement is membership.

### Mistake 2: Ignoring NULL with NOT IN

This can produce unexpected results:

`WHERE id NOT IN (SELECT nullable_id FROM ...)`

Use `NOT EXISTS` when the requirement is anti-existence and NULLs are possible.

### Mistake 3: Forgetting correlation

A condition such as:

`WHERE p2.category = p.category`

is essential when the inner calculation must be category-specific.

Without the correlation, the inner query may calculate a global value instead.

### Mistake 4: Creating unnecessary nesting

Deeply nested queries can become difficult to maintain.

A derived table, CTE, join, or window function may sometimes communicate the logic more clearly.

### Mistake 5: Ignoring duplicate behavior

A join can multiply rows in one-to-many relationships.

`EXISTS` does not create those duplicate outer rows.

### Mistake 6: Optimizing by intuition

A query that looks expensive may be optimized well by the database.

A query that looks simple may perform poorly at scale.

Use execution plans and realistic measurements.

### Mistake 7: Building SQL through string concatenation

Application code should not concatenate untrusted values into SQL.

Use parameterized queries.

---

## 44. Edge Cases

### Empty input relation

An aggregate over an empty relation can produce `NULL` for functions such as `AVG()` and `MAX()`.

Applications should account for nullable results.

### No matching correlated rows

A correlated scalar aggregate can produce `NULL` when there are no matching rows.

### NULL values

`NULL` represents an unknown or missing value, not an ordinary value.

Comparisons involving `NULL` use SQL's three-valued logic.

### Duplicate values

A multi-row subquery can return duplicate values.

`IN` is a membership condition, so duplicates generally do not change the Boolean result.

### Multiple maximum rows

A query using:

`WHERE price = (SELECT MAX(price) FROM products)`

can return multiple products if several products share the maximum price.

### Empty required set

Relational-division logic must define what should happen when the required set is empty.

In formal relational logic, the "all requirements satisfied" condition can become vacuously true. Business applications may require a different interpretation.

---

## 45. Security Considerations

Subqueries themselves do not create SQL injection.

Unsafe construction of SQL strings does.

For example, application code should not directly concatenate user input into a query.

Parameterized SQL should be used instead.

Conceptually:

`WHERE customer_id = ?`

with the value supplied separately is safer than building SQL text by concatenating the value.

Security considerations also include:

- least-privilege database accounts
- restricted write permissions
- transaction boundaries
- validation of application inputs
- careful handling of database errors
- avoiding exposure of sensitive query results
- auditing destructive operations

---

## 46. Transaction Considerations

Subqueries can participate in `UPDATE` and `DELETE` statements.

When modifying data:

1. Confirm the intended predicate.
2. Test the equivalent `SELECT`.
3. Use a transaction when multiple operations must be atomic.
4. Consider concurrent changes.
5. Check affected-row counts.
6. Commit only after validation.

The Python implementation demonstrates this principle by performing temporary modifications and rolling them back.

---

## 47. Performance Best Practices

### Index correlation columns

Common relationship columns include:

- `orders.customer_id`
- `order_items.order_id`
- `order_items.product_id`

### Filter early when appropriate

Conditions inside the subquery can reduce the number of qualifying rows.

### Avoid unnecessary SELECT columns

For `EXISTS`, the selected expression generally does not matter.

`SELECT 1` communicates the intent clearly.

### Measure

Use database-specific tools such as execution-plan facilities.

The Python implementation uses SQLite's `EXPLAIN QUERY PLAN`.

### Consider alternatives

Evaluate:

- correlated subquery
- join
- derived table
- CTE
- window function

based on clarity and actual workload.

---

## 48. Complexity Considerations

Suppose:

- `C` = number of customers
- `O` = number of orders
- `P` = number of products
- `I` = number of order items

A naive correlated customer-order search can conceptually approach `O(C × O)` comparisons.

An index on customer ID changes the access pattern by allowing direct lookup of relevant orders.

Similarly, an index on product ID allows direct access to order items associated with a product.

These are conceptual complexity models. Real database performance also depends on:

- B-tree traversal
- hash structures
- caching
- selectivity
- join algorithms
- sorting
- aggregation strategy
- parallel execution
- physical storage

---

## 49. Implementation Comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Database execution | SQLite | No external database | No external database |
| Main purpose | Actual SQL execution | Logical SQL modeling | Industry-style systems case study |
| Scalar subqueries | Direct SQL | Scalar helper | Aggregate method |
| EXISTS | Direct SQL | Boolean helper | Indexed relationship lookup |
| NOT EXISTS | Direct SQL | Negated existence helper | Anti-existence lookup |
| Correlation | SQL aliases | Explicit outer-row filtering | Customer-specific methods |
| Derived tables | SQL subqueries | Intermediate arrays | Intermediate vectors |
| NULL behavior | SQLite execution | Explicit conceptual model | Explicit conceptual model |
| Performance | Query plan | Data-structure comparison | Indexed versus repeated scan |
| Best educational use | Learn actual syntax | Understand logical mechanics | Understand system design |

---

## 50. Practical SQL Design Rules

A reliable design process is:

1. State the business question in plain language.
2. Identify the outer relation.
3. Identify the information required from related rows.
4. Decide whether the requirement is:
   - one value
   - a set of values
   - existence
   - non-existence
   - a correlated calculation
5. Select an appropriate subquery pattern.
6. Check `NULL` behavior.
7. Check duplicate behavior.
8. Test edge cases.
9. Inspect the execution plan.
10. Measure performance with representative data.

---

## 51. Decision Guide

### Need one calculated value?

Consider a scalar subquery.

Example:

`price > (SELECT AVG(price) FROM products)`

### Need membership in another result?

Consider `IN`.

Example:

`customer_id IN (SELECT customer_id FROM orders ...)`

### Need to know whether a related row exists?

Consider `EXISTS`.

Example:

`EXISTS (SELECT 1 FROM orders WHERE ...)`

### Need to know whether no related row exists?

Consider `NOT EXISTS`.

Example:

`NOT EXISTS (SELECT 1 FROM order_items WHERE ...)`

### Need a value calculated separately for each outer row?

Consider a correlated subquery.

### Need an intermediate relation?

Consider a derived table or CTE.

### Need "every required item"?

Consider nested `NOT EXISTS` or an equivalent relational-division technique.

### Need ranking or group-level values alongside individual rows?

Consider a window function.

---

## 52. Advanced Concept: Logical Versus Physical Execution

SQL describes declarative intent.

The query does not necessarily execute in the textual order in which it is written.

For example, a correlated subquery may appear to execute once for every outer row from a logical perspective, but an optimizer can transform the physical execution.

Possible optimizer strategies include:

- index lookup
- join transformation
- semi-join
- anti-join
- materialization
- predicate pushdown
- hash-based processing
- nested-loop execution

Therefore, source-level query shape and physical execution are separate concepts.

---

## 53. Semi-Join and Anti-Join Concepts

`EXISTS` is closely related to the concept of a semi-join.

A semi-join returns rows from one side when at least one matching row exists on the other side.

`NOT EXISTS` corresponds conceptually to an anti-join.

An anti-join returns rows for which no qualifying relationship exists.

These concepts explain why `EXISTS` and `NOT EXISTS` are often preferable to joins when the requirement is specifically existence.

---

## 54. Why Aliases Matter

Correlated queries often reference the same table at multiple query levels.

For example:

`FROM products AS p`

and:

`FROM products AS p2`

The aliases communicate different logical roles.

Without clear aliases, correlated queries can become difficult to understand and maintain.

Good aliases should be:

- short enough to read
- descriptive enough to identify the role
- used consistently

Examples:

- `c` for customers
- `o` for orders
- `oi` for order items
- `p` for outer products
- `p2` for inner products

---

## 55. Testing Subqueries

Subquery testing should include more than normal rows.

Important cases include:

- no related rows
- one related row
- multiple related rows
- duplicate values
- `NULL`
- maximum values
- minimum values
- equal values
- empty tables
- inactive records
- cancelled records
- customers with no orders

The Python implementation contains assertions that verify core semantics.

The JavaScript implementation performs validation through explicit checks.

The C++ implementation uses assertions and exceptions.

---

## 56. Relationship to Real Applications

Subqueries are common in:

- sales reporting
- customer analytics
- financial reporting
- inventory systems
- HR systems
- procurement
- order management
- subscription platforms
- fraud analysis
- data quality checks
- operational dashboards
- enterprise reporting

Typical business questions include:

- Which customers have never ordered?
- Which products have never sold?
- Which employees have no assignments?
- Which accounts have transactions above their average?
- Which products are above their category average?
- Which customers purchased every product in a required bundle?
- Which departments have no active employees?
- Which records have no matching compliance event?

These questions naturally map to existence, anti-existence, scalar, correlated, and nested subqueries.

---

## 57. Important Distinctions

### Scalar versus correlated

Scalar describes the expected result shape.

Correlated describes the dependency on the outer query.

A subquery can be both scalar and correlated.

### IN versus EXISTS

`IN` emphasizes membership.

`EXISTS` emphasizes relationship existence.

### NOT IN versus NOT EXISTS

Both can express exclusion, but `NULL` makes their semantics different.

### Nested versus correlated

Nested describes query levels.

Correlated describes whether an inner query references an outer query.

A nested query can be correlated.

### Derived table versus scalar subquery

A derived table produces a relation that can contain multiple rows and columns.

A scalar subquery produces one value.

---

## 58. What the Three Implementations Demonstrate

### Python

The Python file is the primary SQL implementation.

It demonstrates actual SQL syntax through SQLite and covers:

- scalar subqueries
- aggregate subqueries
- `IN`
- `NOT IN`
- `EXISTS`
- `NOT EXISTS`
- correlated queries
- nested queries
- derived tables
- `UPDATE`
- `DELETE`
- `EXPLAIN QUERY PLAN`
- transactions
- validation
- `NULL` behavior

### JavaScript

The JavaScript file focuses on relational mechanics.

It demonstrates:

- membership
- existence
- anti-existence
- scalar-result validation
- correlation
- nested intermediate results
- derived-table-style processing
- performance implications of indexed lookups

This makes the logical behavior of subqueries visible without depending on a database package.

### C++

The C++ file develops a more system-oriented case study.

It demonstrates:

- structured data models
- classes
- vectors
- sets
- hash maps
- indexing
- aggregation
- validation
- optional values
- correlated lookups
- nested requirements
- performance modeling
- production-oriented design considerations

---

## 59. Limitations

The JavaScript and C++ implementations model SQL concepts rather than implementing full SQL engines.

They do not reproduce every behavior of a database optimizer.

In particular, they do not provide:

- SQL parsing
- relational algebra optimization
- transaction isolation
- database locking
- query compilation
- cost-based optimization
- disk-backed indexes
- database concurrency

The Python SQLite implementation provides actual SQL execution, but SQLite's optimizer and SQL dialect are not identical to every enterprise database system.

Production SQL should therefore be tested against the target database engine.

---

## 60. Practical Checklist

Before using a subquery in production, verify:

- Is the inner query scalar or multi-row?
- Can the inner query return zero rows?
- Can it return more than one row?
- Can the inner result contain `NULL`?
- Is `IN` appropriate?
- Would `EXISTS` communicate the requirement better?
- Would `NOT EXISTS` avoid a `NOT IN` NULL issue?
- Is the subquery correlated?
- Is correlation actually required?
- Would a join be clearer?
- Would a window function be clearer?
- Are duplicates possible?
- Are the correlation columns indexed?
- Has the execution plan been inspected?
- Has the query been tested with realistic data volume?
- Is application input parameterized?
- If the query modifies data, is the transaction boundary correct?

The three programs provide executable demonstrations of these decisions using a consistent retail analytics domain.
