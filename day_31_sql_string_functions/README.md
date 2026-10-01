# SQL String Functions

This learning artifact examines SQL string functions through a realistic customer-data and support-ticket workflow. The implementations focus on `CONCAT`, `SUBSTRING`, `POSITION`, `REPLACE`, `LOWER`, `UPPER`, `TRIM`, and regular expressions.

The three programs deliberately use different technical perspectives:

- The Python program executes SQL expressions through the standard-library `sqlite3` module and registers regular-expression functions that SQLite does not provide by default.
- The JavaScript program models the same data-processing problems at an application layer, implementing SQL-style semantics explicitly and using Node.js features such as `Promise`, `RegExp`, `console.table`, and high-resolution timing.
- The C++ program presents a repository-independent support-platform case study with explicit string-processing functions, type-safe data structures, `std::regex`, validation, and error handling.

The central distinction is that these functions solve different text-processing problems. Concatenation combines values, substring extraction selects a region, position lookup locates text, replacement transforms matching text, case conversion normalizes letter casing, trimming removes boundary whitespace, and regular expressions describe patterns rather than simple literal strings.

## Why SQL string functions matter

Text columns commonly contain information that must be cleaned, compared, searched, displayed, transformed, or validated before it becomes useful.

A customer table may contain:

- Names imported with unwanted surrounding spaces.
- Email addresses stored with inconsistent capitalization.
- Telephone numbers containing different separators.
- Separate first-name and last-name columns that need to be displayed together.
- Text messages containing structured identifiers.
- Support subjects whose capitalization differs between data sources.

String functions allow these operations to be expressed directly in SQL queries. They are particularly useful in reporting, data cleaning, filtering, ETL pipelines, customer-support systems, search preparation, and data-quality checks.

The important design question is not simply which function exists. It is which operation matches the structure of the problem.

## Function boundaries

| Function | Primary purpose | Typical support-data use |
|---|---|---|
| `CONCAT` | Combines multiple strings | Construct a customer display label |
| `SUBSTRING` | Extracts part of a string | Create message previews or extract fixed-format portions |
| `POSITION` | Finds the location of a substring | Locate `@` in an email address |
| `REPLACE` | Replaces literal text | Remove phone-number separators |
| `LOWER` | Converts letters to lowercase | Canonicalize email values for comparison |
| `UPPER` | Converts letters to uppercase | Standardize status or presentation text |
| `TRIM` | Removes surrounding whitespace or selected characters | Clean imported names and email values |
| Regular expressions | Match or transform text patterns | Validate email structure or identify order identifiers |

These operations overlap when composed, but they are not interchangeable.

For example, `REPLACE(phone, '-', '')` answers a literal replacement problem. A regular expression such as `[^0-9]` answers a pattern problem in which every non-digit character should be removed. The second rule is broader and should therefore be chosen only when that broader behavior is actually intended.

## CONCAT

`CONCAT` combines separate string values into one value.

A common customer-data operation is constructing a display name from `first_name` and `last_name`.

Conceptually:

`CONCAT(first_name, ' ', last_name)`

The separator is significant. Concatenating two names without an explicit space produces a different value.

Database behavior around `NULL` differs between SQL implementations. Some `CONCAT` implementations treat null arguments differently from the `||` concatenation operator. Production SQL should therefore follow the exact semantics of the target database rather than assuming that all engines behave identically.

The Python implementation uses SQLite's `||` operator because SQLite does not expose the same built-in `CONCAT()` function found in several other database systems. The program explicitly trims the name fields before composition:

`TRIM(first_name) || ' ' || TRIM(last_name)`

This demonstrates that string functions are often composed rather than used in isolation.

The JavaScript implementation exposes this issue directly through `sqlConcat()`. It rejects `null` and `undefined` rather than silently converting them to text. This makes the null policy explicit at the application boundary.

The C++ implementation reserves the required output capacity before appending strings. This is a small but meaningful systems-level design choice because it reduces unnecessary reallocations when constructing larger strings.

## SUBSTRING

`SUBSTRING` extracts a region of a string.

SQL syntax differs between database products. Some systems use:

`SUBSTRING(value FROM start FOR length)`

while others use forms such as:

`SUBSTRING(value, start, length)`

SQLite uses `substr(value, start, length)`. The Python implementation therefore uses `SUBSTR`.

The important semantic detail is indexing. SQL substring functions commonly use one-based positions, while JavaScript and C++ string APIs use zero-based indexes internally.

The JavaScript function `sqlSubstring()` explicitly converts a one-based SQL position into a zero-based JavaScript index. The C++ function `substringSql()` performs the same boundary conversion.

The support-ticket example extracts a bounded message preview. This is useful for dashboards where displaying the complete support message would be unnecessary.

Substring extraction should not be used blindly for structured identifiers when the identifier's location is variable. If an order number can occur at different positions, pattern matching or position-based extraction may be more appropriate.

## POSITION

`POSITION` determines where a substring occurs inside another string.

A common example is locating the `@` separator in an email address.

Conceptually:

`POSITION('@' IN email)`

SQLite provides the equivalent operation through `INSTR(email, '@')`.

The Python example uses `INSTR()` and demonstrates that a missing substring produces a database-specific result. In SQLite, `INSTR()` returns `0` when the searched text is absent.

The JavaScript implementation translates JavaScript's `indexOf()` result into SQL-style semantics. JavaScript uses zero-based positions and returns `-1` when a substring is missing, so the function converts a successful match to a one-based position and maps a missing value to `0`.

The C++ implementation uses `std::string_view::find()` for efficient non-owning lookup and converts the result into the same one-based convention.

Position lookup becomes useful when combined with substring extraction. For example, after finding the position of `@`, the text following that position can be extracted as the email domain.

This combination is more adaptable than assuming that every email address has a domain of a fixed length.

## REPLACE

`REPLACE` performs literal text substitution.

A phone number such as:

`+91-98765-43210`

can be normalized to:

`+919876543210`

with a sequence of literal replacements.

The Python implementation demonstrates nested SQL `REPLACE()` calls. The JavaScript implementation uses `split().join()` because JavaScript's string-based `replace()` normally changes only the first occurrence when given a string rather than a global regular expression.

The C++ implementation searches repeatedly and replaces each literal occurrence.

Literal replacement is important because it keeps the transformation separate from pattern matching. If the intended rule is specifically "remove hyphens," then literal replacement communicates that requirement more precisely than a broad regular expression.

A literal replacement should also account for the possibility that the search text is empty. The implementations explicitly handle that case rather than allowing an accidental infinite loop or unexpected behavior.

## LOWER and UPPER

`LOWER` converts letters to lowercase, while `UPPER` converts letters to uppercase.

A canonical email value can be represented as:

`LOWER(TRIM(email))`

This is useful when imported records contain values such as:

`ATUL.PANDEY@EXAMPLE.COM`

and:

` atul.pandey@example.com `

The transformation removes surrounding whitespace and normalizes letter case before comparison.

The Python program uses `LOWER(TRIM(email))` in a filtering expression. This illustrates a practical database concern: the expression changes the value being evaluated and may affect index usage unless the database supports an appropriate expression index or a canonical stored value.

`UPPER(status)` demonstrates a different use. Status values are often presented in a consistent case even when source data has inconsistent capitalization.

Case conversion should not be confused with full Unicode case folding. Database collation, character set, locale, and Unicode behavior vary. Production applications handling multilingual text should verify the exact behavior of the selected database engine.

## TRIM

`TRIM` removes unwanted characters from the beginning and end of a string.

For imported customer data:

`TRIM('  Atul  ')`

produces:

`Atul`

It does not generally mean "remove every space everywhere." Internal whitespace is a different problem.

For example, a value conceptually shaped like:

`Atul    Pandey`

contains meaningful interior separation. A database-specific whitespace-normalization strategy may be required if multiple internal spaces should become one.

`TRIM` can also accept a specified character in database implementations that support the corresponding syntax. The Python example demonstrates trimming hyphens from a deliberately constructed value.

Trimming is commonly placed before other functions:

`LOWER(TRIM(email))`

or:

`TRIM(first_name) || ' ' || TRIM(last_name)`

This ordering matters because normalization should occur before a value is compared or combined when surrounding whitespace is not meaningful.

## Regular expressions

Regular expressions solve a different class of problem from literal string functions.

A literal function asks questions such as:

- Where is this exact substring?
- Replace this exact text.
- Remove this exact separator.
- Extract this known range.

A regular expression describes a pattern.

An order identifier such as:

`ORD-2026-1042`

can be described by:

`ORD-[0-9]{4}-[0-9]{4}`

The pattern specifies the structural rules rather than depending on a fixed location.

The Python program registers `REGEXP` and `REGEXP_REPLACE` with SQLite. This is necessary because SQLite does not provide a complete built-in regular-expression function set by default. The implementation delegates pattern processing to Python's `re` module.

The JavaScript program uses `RegExp` directly. It validates an email's common structural shape, removes non-digit phone characters, identifies order codes, and classifies support tickets using pattern matching.

The C++ implementation uses `std::regex`. It extracts order identifiers from support messages and validates the structural shape of email addresses.

The email patterns intentionally perform structural validation rather than claiming to implement the complete set of rules associated with every valid email address. Regex validation should therefore be scoped to the actual data-quality requirement.

## Python implementation

The Python program creates an in-memory SQLite database containing `customers` and `support_tickets`.

The customer records contain deliberately inconsistent formatting so the string functions perform meaningful work rather than operating on already-perfect data.

The SQL workflow demonstrates:

- Customer display-name construction through concatenation.
- Message previews through `SUBSTR`.
- Email and text positions through `INSTR`.
- Phone normalization through nested `REPLACE`.
- Email normalization through `LOWER(TRIM(...))`.
- Status normalization through `UPPER`.
- Whitespace cleanup through `TRIM`.
- Regex validation through a registered SQLite function.
- Regex replacement for phone numbers.
- Regex detection of structured order identifiers.
- Composed transformations for canonical customer data.
- Parameterized regex input rather than SQL-string interpolation.
- Edge behavior involving `NULL`, missing substrings, and empty strings.
- Query-plan inspection showing why function-wrapped predicates can have different indexing behavior.

The program also demonstrates a production-oriented distinction between database-side transformation and application-side regex processing. SQLite's extensibility allows Python functions to participate in SQL expressions, but this should be used deliberately because custom functions can affect portability and database execution behavior.

## JavaScript implementation

The JavaScript program treats the customer and ticket data as in-memory application records.

Instead of using a database driver, it implements SQL-style operations as explicit functions:

- `sqlConcat()` models string composition with an explicit null policy.
- `sqlSubstring()` converts SQL-style one-based positions into JavaScript's zero-based indexes.
- `sqlPosition()` converts `indexOf()` results into SQL-like position semantics.
- `sqlReplace()` replaces all literal occurrences without interpreting the search text as regex syntax.
- `sqlLower()` and `sqlUpper()` expose case normalization.
- `sqlTrim()` performs boundary whitespace removal.
- `regexp()` wraps JavaScript's `RegExp`.
- `regexpReplace()` performs pattern-based replacement.

The application layer then composes these operations into customer normalization, email-domain extraction, ticket classification, order-code detection, and redaction.

The asynchronous ticket-processing function demonstrates how these synchronous text transformations can participate in a Node.js event-driven workflow. The `Promise` is used for workflow modeling rather than because the string transformations themselves are asynchronous.

The JavaScript program also measures one regex operation using `process.hrtime.bigint()`. This reinforces an important distinction between correctness and performance: a regex that produces the correct result may still be unsuitable for very large or attacker-controlled inputs if its pattern can cause excessive processing.

## C++ case study

The C++ program models a support platform receiving customer and support-ticket records.

Its architecture is intentionally different from the Python and JavaScript implementations.

`Customer` and `Ticket` are strongly typed structures. Ticket categories are represented by the `TicketCategory` enumeration rather than free-form strings. This constrains category values and makes invalid categories harder to introduce accidentally.

The string-processing layer contains separate functions for:

- `trim()`, which scans the string boundaries and removes surrounding whitespace.
- `lower()` and `upper()`, which normalize ASCII-oriented letter casing.
- `concat()`, which calculates the required output capacity and appends multiple values.
- `substringSql()`, which models one-based SQL substring semantics.
- `positionSql()`, which converts C++'s zero-based search result into a one-based SQL-style position.
- `replaceAll()`, which performs literal replacement without regex interpretation.
- `regexMatches()`, which applies a compiled `std::regex`.
- `regexExtract()`, which returns an optional matched identifier.

The support-ticket classifier combines case normalization with regex rules. Security-related terms, billing terms, customer-profile terms, and email-related terms are treated as distinct categories because each represents a different operational route.

Order identifiers are extracted with a bounded expression:

`ORD-[0-9]{4}-[0-9]{4}`

This prevents arbitrary text from being treated as an order code.

The program also demonstrates failure handling through exceptions, edge cases such as missing substring searches, substring positions beyond the end of a string, and replacement of repeated literals.

## Composing functions

Real SQL transformations rarely consist of one function.

A canonical customer email might use:

`LOWER(TRIM(email))`

A display name might use:

`TRIM(first_name) || ' ' || TRIM(last_name)`

A phone transformation might use:

`REPLACE(REPLACE(phone, '-', ''), ' ', '')`

A pattern-oriented phone transformation might instead use a regex replacement that removes every non-digit character.

Composition should follow the semantic order of the transformation.

For example, comparing a trimmed, case-normalized email is different from comparing the raw database value. If normalization is part of the business rule, it should be applied consistently across ingestion, querying, indexing, and reporting.

## String functions versus regular expressions

Literal string functions are generally easier to understand and often cheaper when the transformation is simple.

For example:

`REPLACE(phone, '-', '')`

communicates one precise operation.

A regex expression such as:

`REGEXP_REPLACE(phone, '[^0-9]', '')`

communicates a broader rule: remove everything that is not a digit.

That distinction matters when data evolves. If a future input contains parentheses, spaces, and periods, the regex version may continue to satisfy the "digits only" requirement, while the literal replacement handles only the explicitly named characters.

Regex should therefore be selected because the requirement is pattern-based, not because it appears more powerful.

## Edge cases

### Missing substrings

`POSITION` can produce a database-specific "not found" result. SQLite's `INSTR()` returns `0`, while JavaScript's `indexOf()` returns `-1`. Applications that translate between SQL and application semantics must account for this difference.

### Out-of-range substring positions

A substring beginning beyond the end of a string generally produces an empty result rather than valid content. The Python, JavaScript, and C++ implementations explicitly demonstrate this boundary.

### NULL values

SQL `NULL` is not simply an empty string. String operations may propagate `NULL`, ignore it, or treat it differently depending on the function and database engine.

This is one reason the Python implementation includes explicit `NULL` examples and the JavaScript implementation refuses nullish arguments for its simplified `sqlConcat()` function.

### Empty search strings

Replacing an empty search value can have surprising semantics depending on the implementation. The JavaScript and C++ examples explicitly return the original value when the literal search string is empty.

### Case and Unicode

`LOWER` and `UPPER` behavior is database-specific and can depend on character encoding and collation. ASCII examples are straightforward, but multilingual production data requires verification against the target database's Unicode behavior.

### Regular-expression errors

An invalid regex is a different failure from a failed match. A valid regex that finds nothing is normal application behavior. A malformed regex is a configuration or validation error.

The Python, JavaScript, and C++ implementations treat invalid patterns as errors rather than silently treating them as "no match."

## Common mistakes

Applying `LOWER` to one side of a comparison while leaving the other side in an incompatible normalization state can produce inconsistent matching behavior.

Using `REPLACE` when the requirement actually describes a pattern can leave unexpected characters in the result.

Using regex when a literal replacement would satisfy the requirement can make a transformation harder to understand and maintain.

Assuming that all SQL databases use identical syntax for `SUBSTRING`, `POSITION`, concatenation, regex support, or `TRIM` is a portability mistake.

Assuming that `TRIM` removes every internal whitespace character can produce incorrect data-cleaning rules.

Extracting variable-position identifiers with fixed substring offsets is fragile. Position lookup or regex extraction is more appropriate when the identifier location is not guaranteed.

Treating an email regex as a complete standards-compliant email validator is also unsafe. Regex-based checks should be described as structural validation unless the implementation explicitly satisfies a stronger specification.

## Performance considerations

String functions can become expensive when applied to millions of rows.

A predicate such as:

`WHERE LOWER(TRIM(email)) = 'person@example.com'`

may prevent a normal index on the raw `email` column from being used, depending on the database engine and optimizer.

For frequently queried canonical values, production designs can consider:

- Storing a canonical representation alongside the original value.
- Using a database-supported expression or function index.
- Normalizing data during ingestion when the business rule permits it.
- Choosing an appropriate collation instead of repeatedly applying case transformations.
- Avoiding unnecessary repeated transformations in the same query.

Regular expressions can be substantially more expensive than simple equality, position lookup, or literal replacement. The cost depends on the engine, pattern, input length, and implementation.

User-controlled regex patterns require particular care. Some regex engines and patterns can cause excessive CPU consumption. Production systems should constrain pattern sources and input sizes where appropriate.

## Security considerations

String functions themselves are not automatically security controls.

A regex that detects a suspicious-looking value does not make that value safe.

A replacement that masks an order identifier does not guarantee that other sensitive information has been removed.

SQL expressions should be combined with parameterized queries when values originate outside trusted SQL source code. The Python implementation demonstrates parameterized regex input rather than interpolating a pattern into SQL text.

Literal replacement should remain distinct from regex replacement when the input should be treated as literal data. Accidentally interpreting user-provided text as a regex pattern can change behavior and introduce unnecessary processing risk.

Input length should also be considered. Very large text fields can make repeated substring operations, replacements, or regex evaluations expensive.

## Portability considerations

SQL string syntax is not completely uniform.

SQLite uses expressions such as:

`substr(value, start, length)`

and:

`instr(haystack, needle)`

Other database systems may provide `SUBSTRING`, `POSITION`, `CONCAT`, `CHARINDEX`, `INSTR`, `REGEXP_REPLACE`, or different regex predicates.

Regex support is especially variable. Some database engines provide extensive regular-expression functionality, some provide only a predicate, and some require extensions or user-defined functions.

The Python implementation makes this explicit by registering regex functions with SQLite rather than pretending that SQLite universally supports the same regex SQL syntax as every other database.

For production applications, SQL should therefore be written against the documented behavior of the specific database engine being deployed.

## Relationship between the functions

A realistic normalization pipeline can be viewed as a chain:

`TRIM → LOWER/UPPER → POSITION/SUBSTRING → REPLACE or REGEXP_REPLACE → CONCAT`

The order is not universal, but each stage has a distinct purpose.

For a customer email:

`TRIM` removes accidental boundary whitespace.

`LOWER` creates a consistent case representation.

`POSITION` can locate structural separators such as `@`.

`SUBSTRING` can extract the domain after the separator.

For a phone number:

`REPLACE` can remove a known separator.

Regular expressions can be used when the requirement is instead to retain only a defined character class.

For a display label:

`TRIM` cleans individual components before `CONCAT` combines them.

The key design principle is to choose the narrowest operation that accurately expresses the transformation and to compose functions only when each transformation has a clear purpose.
