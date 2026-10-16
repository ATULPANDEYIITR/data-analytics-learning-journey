# File Handling with Python, JavaScript, C++, Java, and PostgreSQL

## Technical scope

File handling connects persistent data to application behavior. An application must locate the intended file, interpret its bytes using the correct encoding, parse the chosen format, validate its contents, handle failures, and publish results without exposing partially written output.

This project examines these concerns through an operational asset-management scenario. A CSV export contains asset identifiers, department names, and replacement costs. The application validates each record, rejects invalid or duplicate entries, calculates department-level totals, and produces a JSON report and a human-readable audit file.

The implementations emphasize five distinct responsibilities:

- **Text files** store readable notes, service logs, and audit records. Their record boundaries and encoding must be handled deliberately.
- **CSV files** represent tabular records. Quoting, delimiters, headers, missing values, and inconsistent row widths affect how fields are interpreted.
- **JSON files** represent structured objects and arrays. Parsing validates syntax, while application-level validation enforces business rules.
- **File paths** identify locations in a filesystem. Relative paths, directory creation, traversal attempts, symbolic links, and permissions influence safe access.
- **Encoding and write reliability** determine whether text survives a round trip and whether readers observe complete output rather than an incomplete file.

The code uses standard-library facilities. Each language has its own implementation strategy, so the programs are complementary rather than identical translations.

## How the formats differ

| Format | Structure | Appropriate use | Main failure risks |
|---|---|---|---|
| TXT | Text arranged as lines or free-form content | Audit entries, operational notes, extracted errors | Incorrect encoding, unexpected newlines, unbounded file size |
| CSV | Rows containing delimited fields, optionally quoted | Asset exports, tabular operational records | Incorrect quote parsing, duplicate headers, missing columns, ambiguous numeric formats |
| JSON | Objects, arrays, strings, numbers, booleans, and null | Service configuration, nested reports, structured interchange | Malformed syntax, unexpected types, excessive nesting or input size |
| Binary | Bytes without an assumed text representation | Instrument snapshots and other non-text payloads | Corruption, incorrect interpretation as text, incompatible binary layouts |

CSV and JSON are both text-based formats, but their structures are different. CSV does not inherently specify a schema or the data type of each column. A field containing `45000.50` is initially text and must be converted according to an explicit numeric policy. JSON distinguishes strings from numbers, but valid JSON alone does not establish that a replacement cost is non-negative or that an asset identifier is unique.

TXT has fewer structural rules. This makes it convenient for human-readable records, but applications must define their own conventions for separating events, identifying fields, and handling multiline content.

## Paths and workspace boundaries

A path identifies a location, not the contents or type of a file. A relative path such as `input/assets.csv` is interpreted relative to an application-defined root. An absolute path refers to a location anchored in the filesystem.

The examples create separate `input` and `output` directories. This separates source data from generated reports and makes the program's filesystem activity easier to inspect.

Path normalization is important when accepting user-supplied names. A path containing `../` may attempt to leave the intended directory. The Python, JavaScript, C++, and Java implementations reject absolute paths and parent-directory traversal for their workspace operations.

These checks reduce accidental path escapes, but lexical validation alone is not a complete security boundary. A symbolic link inside the workspace may point elsewhere. Another process may also replace a directory or link between validation and opening the file. Applications processing untrusted paths should use trusted directory permissions, platform-appropriate secure file-opening operations, and explicit access controls.

Creating a directory recursively is different from creating a file. Directory creation should be handled before opening an output file, while file creation modes determine whether existing content is retained, truncated, or rejected.

## Text encoding and newline handling

Text files contain encoded bytes. UTF-8 is used throughout the examples because it supports ordinary English text and characters such as `é` without requiring a separate encoding for each language.

A successful read does not always mean the input was decoded correctly. Some APIs replace malformed byte sequences with a replacement character. Other APIs can be configured to reject malformed UTF-8. The JavaScript implementation uses `TextDecoder` with fatal decoding enabled, and the Java implementation configures its UTF-8 decoder to report malformed input.

The Python example demonstrates that ASCII cannot encode every character in its operational notes. Selecting an encoding explicitly prevents the application from silently depending on a platform-specific default.

Newline conventions also differ across environments. Text files may use LF or CRLF. Python's CSV API expects `newline=""` when opening CSV files so that its CSV implementation can manage record boundaries correctly. The JavaScript and C++ implementations process newline sequences deliberately in their respective parsing workflows.

Binary files should be read as bytes rather than decoded as text. The examples create small byte sequences containing values that are not valid standalone UTF-8 text. Such data must remain unchanged unless the application has a defined binary decoding protocol.

## Python implementation

The Python program provides a progressive file-processing workflow using `pathlib`, `csv`, `json`, `tempfile`, and other standard-library modules.

### Text and path operations

`read_text_file()` explicitly specifies the encoding and uses a context manager so that the file is closed reliably. `resolve_workspace_path()` validates relative names and verifies that the resolved target remains inside the workspace.

The workspace also contains an append-only audit log. Opening it with mode `a` retains previous entries, whereas mode `w` truncates an existing file. The distinction matters when audit history must be retained.

### CSV ingestion and validation

`read_csv_file()` uses `csv.DictReader`, checks header uniqueness, and detects rows with too many or too few fields. It returns string values rather than guessing the application's desired data types.

`validate_incident()` then converts the severity field to an integer and enforces the permitted range. `process_incident_csv()` handles duplicate incident identifiers and records rejected rows separately from accepted incidents.

This separation is important because syntactic parsing and domain validation solve different problems. A CSV record can have the correct number of columns while still containing an invalid severity value.

The resulting report groups accepted incidents by department and calculates incident counts and average severity. Invalid rows remain visible in the rejection report instead of disappearing silently.

### JSON serialization and publication

`read_json_file()` reports the line and column of malformed JSON. `write_json_atomically()` serializes structured data before publishing it. Serialization uses `ensure_ascii=False` to preserve readable Unicode and `allow_nan=False` to reject non-standard numeric values.

`write_text_atomically()` writes to a temporary file in the destination directory, flushes the file, calls `fsync()`, and replaces the destination with `os.replace()`. This helps readers avoid observing a partially written report. It does not guarantee durability under every hardware or filesystem failure.

The script also demonstrates missing files, empty files, binary input, streaming line-by-line processing, and assertions that verify important validation behavior.

## JavaScript implementation

The JavaScript implementation focuses on Node.js filesystem APIs, asynchronous I/O, and a state-machine CSV parser.

### Asynchronous filesystem operations

The `node:fs/promises` API allows filesystem operations to be awaited without blocking the event loop while the operating system performs the I/O. This is useful in services that handle multiple requests or process several files concurrently.

`writeAtomically()` creates a unique temporary filename and opens it with the exclusive `wx` flag. The flag prevents accidental reuse of an existing temporary file. The implementation writes and synchronizes the temporary file before renaming it to the destination.

The exact guarantees of replacement and durability depend on the operating system and filesystem. Production services should test their target environments and establish how concurrent writers are coordinated.

### CSV state-machine parsing

`parseCsv()` tracks whether the parser is inside a quoted field and whether a closing quote has been encountered. This is necessary because commas and line breaks inside quoted fields are part of the field value, not necessarily record separators.

For example, a description containing a comma, escaped quotes, or an embedded newline must not shift subsequent values into the wrong columns. The parser rejects unterminated quotes, unexpected characters after a closing quote, duplicate headers, and inconsistent record widths.

The parser is deliberately scoped to ordinary CSV text with comma delimiters and standard quote escaping. It does not claim to implement every possible CSV dialect or character encoding. Large, untrusted CSV inputs also require explicit limits on file size, row length, and total processing time.

### Streaming and backpressure

`demonstrateStreaming()` uses an asynchronous readable stream to process a service log in chunks. A pending string retains a partial record when a newline has not yet arrived. Matching error records are written to a destination stream.

The writable stream's `drain` event provides backpressure: the reader pauses when the destination cannot accept data immediately. Without this behavior, an application could accumulate large amounts of queued output in memory.

The JSON configuration example separately demonstrates syntax parsing and business-rule validation. A valid JSON object with warning and critical temperature thresholds is rejected if the warning threshold is not lower than the critical threshold.

## C++ case study

The C++ program models a field-inspection service receiving an exported inventory of operational assets. It uses explicit domain structures, strict numeric conversion, a CSV parser, a validation pipeline, and separate report generators.

### Data model and import flow

`Asset` stores an identifier, a department, and a replacement cost in paise. `RejectedRecord` captures the source record number and rejection reason. `ImportReport` groups accepted assets, rejected records, and department aggregates.

The workflow reads the source document, checks the header, parses each CSV record, validates its fields, and checks identifier uniqueness. Each accepted asset contributes to a department-level count and total replacement cost. Invalid records are captured without preventing unrelated valid records from being processed.

The implementation stores money as integer paise instead of binary floating-point values. This avoids many rounding errors associated with monetary calculations. The conversion function rejects negative costs, malformed decimals, excessive fractional precision, and values outside its configured range.

### CSV parsing

The CSV parser distinguishes quoted fields from ordinary fields and recognizes escaped double quotes. A document-level parser preserves newline characters inside quoted fields when identifying record boundaries.

The parser intentionally targets a constrained CSV format. The record parser is not a substitute for a fully tested production CSV library, especially for files with unusual quoting conventions, arbitrary line endings inside fields, or hostile input. The input contract should match the capabilities of the parser.

### Report generation and file operations

The program creates a JSON report and a plain-text audit report. `jsonEscape()` handles quotes, backslashes, control characters, and line breaks so that accepted string values do not break the JSON syntax. The report uses a string representation for monetary values to preserve decimal precision.

The temporary-file writer checks for failures during creation, writing, flushing, and renaming. Its deterministic temporary filename is suitable for a single-process demonstration, not concurrent production writers. A production implementation should use exclusive creation with a unique temporary name and account for platform-specific replacement behavior.

The department aggregation uses ordered maps, giving predictable report ordering. Record validation is approximately linear in the number of imported records, with logarithmic map and set operations for aggregation and uniqueness checks. If there are `n` records and `d` departments, the total work is approximately `O(n log n)` in the worst case for these ordered structures, excluding the cost of parsing and writing the file contents.

## Java implementation

The Java program models asset ingestion as a small enterprise service with immutable domain records, validation boundaries, typed import results, and filesystem operations.

### Domain types and immutable results

The `Asset` record enforces identifier, department, and monetary constraints when an instance is created. This prevents an invalid asset from entering the accepted collection through the normal construction path.

`ImportReport` contains the generation timestamp, accepted assets, rejected rows, and department totals. Its constructor uses immutable copies of the collections so that later changes to the original mutable lists do not alter the report.

`DepartmentAggregate.add()` uses exact arithmetic. Operations such as `Math.addExact()` and `Math.multiplyExact()` throw exceptions when integer overflow occurs instead of silently producing an incorrect total.

### CSV and monetary validation

The CSV parser handles quoted fields and escaped double quotes. `parseRupeesToPaise()` accepts a non-negative decimal representation with at most two fractional digits and converts it to an integer monetary value.

The importer checks for duplicate asset identifiers and isolates invalid rows as rejection records. The accepted records and rejected records remain separate, allowing an operational report to describe both successful processing and data-quality failures.

### UTF-8 and atomic output

`readUtf8Strictly()` uses a configured decoder that reports malformed input. The output writer creates a temporary file and attempts an atomic replacement. If the filesystem does not support atomic moves, the demonstration uses a documented non-atomic fallback.

That fallback is an explicit design choice rather than a universal recommendation. Applications requiring strict atomic publication should fail when the guarantee is unavailable, or use a storage system with a clearly defined publication contract.

The Java implementation also checks path traversal, tests malformed UTF-8, and uses assertions to validate monetary conversion and path restrictions.

## PostgreSQL data model

The SQL implementation stores file-processing metadata and business records in a relational model. PostgreSQL is responsible for enforcing integrity constraints on persisted data, while the application is responsible for parsing the original files and translating parsing outcomes into database operations.

### Relational entities

| Table | Responsibility |
|---|---|
| `source_file` | Stores a relative source path, format, encoding, byte size, optional content hash, and discovery timestamp |
| `import_run` | Tracks an individual processing attempt, its lifecycle state, row counts, timestamps, and error details |
| `asset` | Stores accepted asset identifiers, departments, replacement costs, and the import run that supplied each asset |
| `rejected_record` | Preserves source record numbers, original record text, and validation failure reasons |

The foreign key from `import_run` to `source_file` connects processing attempts to their source. The foreign key from `asset` to `import_run` records the provenance of accepted business data. The foreign key from `rejected_record` to `import_run` preserves rejected input for diagnosis.

The `asset` table uses a primary key on the asset identifier. A second import cannot create a duplicate identifier without violating the database constraint. A production system must still define whether repeated imports update an existing asset, are treated as duplicates, or create versioned records.

### Constraints and indexes

The schema uses `CHECK` constraints to enforce valid formats, non-negative file sizes, permitted import states, non-negative replacement costs, and valid identifier patterns. The relative-path constraint rejects obvious absolute paths and parent-directory traversal patterns.

These database checks complement application validation. They cannot establish that a file path is safe to open on the application server, nor can they validate every CSV or JSON syntax rule.

The indexes on import status and rejected record numbers support operational queries. The department index supports filtering assets by department. Indexes improve relevant lookups but add storage requirements and write overhead.

### Import lifecycle and transaction behavior

The `enforce_import_run_transition()` trigger prevents terminal import states from changing to a different state and restricts transitions from `PENDING` and `PROCESSING`. The row-count checks prevent accepted and rejected counts from exceeding the total number of source records.

The sample transaction inserts representative source metadata, import outcomes, accepted assets, and rejected rows. A savepoint isolates an intentionally invalid insert so the database can demonstrate rejection of a negative replacement cost without aborting the entire demonstration.

The `department_asset_summary` view calculates counts, totals, averages, and maximum replacement costs directly from accepted records. A common table expression identifies the latest import run for each source file, enabling rejected records to be examined in the context of the most recent processing attempt.

The schema is a learning-oriented registry rather than a complete ingestion platform. A production importer should create a processing run, ingest and validate records, record all outcomes, and finalize the run within a deliberate transaction strategy. It should also define idempotency, concurrency handling, retry behavior, permissions, retention rules, and the relationship between database transactions and filesystem publication.

## Atomic writes, concurrency, and recovery

A common failure occurs when a process truncates the final report and then fails halfway through writing it. A reader may observe incomplete JSON or an empty report.

Writing a temporary file and publishing it through a rename operation reduces this risk. The temporary file should generally be created on the same filesystem as the destination. Atomic replacement, where supported, allows readers to see either the old complete file or the new complete file rather than a partially written intermediate state.

Atomicity and durability are different properties. A rename may be atomic without guaranteeing that the directory entry and file contents have survived a sudden power failure. Durability-sensitive applications may need to synchronize both the file and its containing directory using platform-specific mechanisms.

Concurrent writers introduce another concern. If two processes publish the same destination, the last successful replacement may overwrite the other process's output. Unique temporary filenames prevent temporary-file collisions but do not establish ownership of the destination. File locks, immutable versioned filenames, conditional writes, or an explicit coordination mechanism may be necessary.

## Common failure modes and their handling

- **Malformed CSV quoting:** A comma inside a quoted field is data, while a comma outside quotes separates fields. Parsers must track quoting state and reject unterminated quoted values.
- **Duplicate column names:** Mapping a row into an object or dictionary can overwrite an earlier value when two headers have the same name. Validate headers before constructing records.
- **Invalid numeric fields:** Parsing success is not sufficient. Values must be checked for allowed ranges, decimal precision, overflow, and the application's monetary representation.
- **Malformed JSON:** JSON parsing errors should be reported with useful location information where available. Syntax validation must be followed by schema and business-rule validation.
- **Missing files and permissions:** Opening a nonexistent file, writing to a read-only directory, or replacing a protected destination can fail. Errors should identify the operation and affected path without exposing sensitive file contents.
- **Invalid encoding:** A byte sequence may not be valid UTF-8. Choose whether malformed input should be rejected or replaced, and apply that policy consistently.
- **Large inputs:** Reading an entire file into memory is convenient for small configuration files but can be unsuitable for large exports. Streaming limits memory usage, although it requires careful record-boundary handling and backpressure.
- **Path traversal:** Normalizing a path and checking its location prevents common mistakes but does not defeat every symbolic-link race. Secure filesystem access requires trusted directory boundaries and appropriate operating-system controls.
- **Partial output:** Write temporary output, check write errors, and publish only after serialization succeeds. Define a recovery policy for abandoned temporary files and failed replacements.

## Operational considerations

File-processing systems should distinguish a failure to read a source from a failure to validate a record. A source-level failure, such as unreadable bytes or an invalid document header, may prevent the import from starting. A row-level validation failure may allow the remaining records to be processed while preserving rejection details.

A reliable operational report should identify its source, processing time, accepted count, rejected count, and failure reasons. File size and cryptographic hashes can support integrity checks, although a hash only proves that bytes match a known digest. It does not establish that the content is trustworthy or semantically valid.

Access controls should limit who can read source files, publish reports, and inspect rejected records. Error logs should avoid copying secrets or sensitive personal data from malformed input. Retention policies should cover temporary files, audit logs, and rejected records as well as the original exports.

The central engineering distinction is between successfully opening a file and successfully processing its contents. Reliable file handling requires explicit path rules, encoding decisions, format-aware parsing, domain validation, recoverable writes, and traceable processing outcomes.
