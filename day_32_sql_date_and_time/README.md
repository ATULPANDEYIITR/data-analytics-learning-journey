# SQL Date & Time

SQL date and time handling combines calendar values, clock values, elapsed durations, calendar intervals, extraction, truncation, timezone interpretation, and temporal arithmetic.

These concepts are related but solve different problems:

- `DATE` represents a calendar date without a time of day.
- `TIMESTAMP` represents a date and clock reading, with timezone behavior depending on the database type and expression being used.
- `INTERVAL` represents a temporal quantity that can contain calendar components such as months as well as day or clock components.
- `DATE_PART` extracts a component from a temporal value.
- `DATE_TRUNC` moves a temporal value to a defined calendar boundary.
- Timezone operations determine how a timestamp is interpreted or displayed in a geographic timezone.
- Date arithmetic calculates new temporal values from dates, timestamps, and intervals.

The implementations in this repository approach the same subject from three different programming perspectives. Python provides a standard-library simulation with timezone-aware `datetime` objects and executable tests. JavaScript focuses on the distinction between date-only values and timestamp instants, together with event-driven temporal processing. C++ presents a transaction-ledger case study that models reporting windows, interval arithmetic, extraction, truncation, validation, and business deadlines.

## Temporal Type Model

A useful SQL design begins by deciding whether a value represents a calendar concept or an instant.

A birthday such as `2026-10-02` is a calendar date. A payment recorded at `2026-10-02 06:48:23+05:30` represents a specific instant and therefore has timezone semantics.

This distinction affects storage, comparison, grouping, reporting, and application behavior.

| Concept | Meaning | Typical operation |
| --- | --- | --- |
| `DATE` | Calendar date without clock time | Date-based business rules |
| `TIMESTAMP` | Date plus clock time | Event and transaction timestamps |
| `INTERVAL` | Temporal quantity | Adding or subtracting time |
| `DATE_PART` | Component extraction | Year, month, hour, weekday |
| `DATE_TRUNC` | Boundary normalization | Month, day, hour, reporting periods |
| Time zone | Geographic interpretation/display of an instant | Local reporting and scheduling |
| Date arithmetic | Temporal calculation | Deadlines, windows, anniversaries |

A common modeling mistake is to use a timestamp where a date is intended. Another is to treat a timezone-less clock value as though it were automatically a globally comparable instant.

## DATE

A SQL `DATE` contains a calendar year, month, and day. It has no hour, minute, second, or timezone.

For example:

`2026-10-02`

represents the calendar date October 2, 2026. It does not mean midnight in India, midnight in UTC, or midnight in any other timezone unless an application explicitly adds that interpretation.

The Python implementation represents this concept with `datetime.date`. The `demonstrate_date_type()` function shows field access, ISO formatting, weekday information, and calendar-based addition.

The JavaScript implementation intentionally represents date-only values as validated ISO strings such as `2026-10-02`. This avoids using JavaScript's `Date` object for a value that does not represent an instant. JavaScript's built-in `Date` is fundamentally an instant-oriented type, so using it carelessly for a date-only business value can introduce timezone shifts.

The C++ case study uses a dedicated `Date` structure containing `year`, `month`, and `day`. Its `validate()` method rejects impossible dates, including February 29 in a non-leap year.

## Calendar Validation

Calendar arithmetic must respect the actual calendar.

February has 28 days in an ordinary year and 29 days in a leap year. Months also have different lengths.

The Python program demonstrates:

`2026-01-31 + 1 month = 2026-02-28`

while:

`2024-01-31 + 1 month = 2024-02-29`

The result is not produced by blindly adding 30 days. It is calendar-aware month arithmetic that clamps the original day to the last valid day of the target month.

This distinction becomes important for subscription renewals, billing dates, contract anniversaries, reporting periods, and recurring schedules.

## TIMESTAMP

A timestamp combines a calendar date with a clock value.

An example is:

`2026-10-02T06:48:23.456789`

The fractional component demonstrates temporal precision. SQL systems may support different timestamp precisions, so applications should not assume that every storage layer preserves arbitrary fractional precision.

A timestamp without timezone semantics should not automatically be interpreted as a globally unique instant. For example:

`2026-10-02 09:30`

could describe a wall-clock appointment in India, London, New York, or another location.

An instant-aware representation instead contains timezone information, such as:

`2026-10-02T09:30:00+05:30`

The Python program requires an explicit timezone offset when parsing timestamps intended to represent global instants.

The JavaScript program follows the same safety principle. `parseTimestamp()` rejects a timestamp without `Z` or an explicit numeric offset instead of allowing the host machine's local timezone to silently determine its meaning.

The C++ case study stores an explicit UTC offset in minutes. This is useful for demonstrating the concept, but it is intentionally not presented as a complete replacement for an IANA timezone database.

## INTERVAL

An interval describes a temporal quantity rather than a particular point in time.

A simplified example is:

`1 month + 3 days + 90 seconds`

The important property is that a month is not a fixed duration in seconds.

January has 31 days, February can have 28 or 29, and other months have 30 or 31. Therefore, "one month" cannot always be represented correctly as a fixed number of seconds.

The Python `SQLInterval` class keeps months, days, seconds, and microseconds as separate components. The `add_sql_interval()` function applies calendar months before fixed day and clock components.

The JavaScript `SqlInterval` class follows the same conceptual distinction but uses JavaScript numbers and milliseconds for its fixed clock component.

The C++ `Interval` structure stores months, days, seconds, and microseconds separately. The case study applies a renewal interval to a transaction timestamp and demonstrates why calendar arithmetic must remain separate from fixed-duration arithmetic.

## DATE_PART

`DATE_PART` extracts a component from a temporal value.

Conceptually:

`DATE_PART('year', timestamp_value)`

returns the year component, while:

`DATE_PART('month', timestamp_value)`

returns the month.

Other useful fields include hour, minute, second, day-of-week, day-of-year, and epoch-related values, depending on the SQL implementation.

The important distinction is that extraction does not move the timestamp to a new boundary. It reads a component from the existing value.

The Python implementation provides a `date_part()` function that handles year, month, day, hour, minute, second, microseconds, weekday variants, day-of-year, and epoch extraction.

The JavaScript implementation performs equivalent extraction using UTC-oriented accessors such as `getUTCFullYear()`, `getUTCMonth()`, `getUTCHours()`, and `getUTCDay()`. This avoids accidental dependence on the machine's local timezone.

The C++ implementation represents supported fields with the `DatePart` enumeration. This makes unsupported fields explicit at compile time rather than relying on arbitrary strings throughout the transaction-processing code.

## DATE_PART Versus DATE_TRUNC

These operations are often confused because both deal with temporal components.

`DATE_PART` answers:

> What is the value of this component?

`DATE_TRUNC` answers:

> What is the timestamp at the beginning of this component's boundary?

For a timestamp such as:

`2026-10-17 14:25:12`

extracting the month gives `10`.

Truncating to the month gives a timestamp equivalent to:

`2026-10-01 00:00:00`

The Python implementation demonstrates both operations independently.

The JavaScript implementation similarly separates `datePart()` from `dateTrunc()`.

The C++ program uses different enumerations, `DatePart` and `Truncation`, so the implementation makes this semantic distinction visible in its type structure.

## DATE_TRUNC

`DATE_TRUNC` is particularly useful for analytics and reporting.

A timestamp can be truncated to:

- year
- quarter
- month
- week
- day
- hour
- minute
- second

For example, truncating:

`2026-10-17 14:25:12.456789`

to the month produces a value at the October month boundary.

Truncating to the hour removes minute, second, and fractional-second components.

The Python implementation also uses `DATE_TRUNC`-style behavior to construct reporting boundaries. This is more reliable than repeatedly comparing timestamps against manually constructed end-of-day values.

The JavaScript implementation treats weekly truncation as Monday-oriented and uses UTC calendar fields for deterministic behavior.

The C++ implementation supports year, quarter, month, day, hour, minute, and second truncation. The original timezone offset is retained while the lower-order components are reset.

## Half-Open Reporting Windows

Temporal reporting is safer when ranges use:

`[start, end)`

meaning the start is included and the end is excluded.

For an October report:

`2026-10-01 00:00:00 <= timestamp < 2026-11-01 00:00:00`

This includes the entire October period without requiring a special value such as:

`2026-10-31 23:59:59.999999`

The half-open approach is independent of timestamp precision. It works whether the database stores milliseconds, microseconds, or another supported precision.

The Python `DateRange` class implements this rule through `contains()`.

The JavaScript `filterEventsByRange()` function applies the same boundary rule to event timestamps.

The C++ `TransactionLedger::between()` method uses the same `[start, end)` behavior for the October transaction report. The transaction at the November boundary is excluded, while the transaction at the final microsecond of October is included.

This is an important production pattern because adjacent windows become composable:

`[October 1, November 1)`

followed by:

`[November 1, December 1)`

does not overlap and does not leave a gap.

## Time Zones

Timezone handling has two separate operations that should not be confused.

### Interpreting a local clock value

Suppose an application receives:

`2026-10-02 09:30`

and the business rule says that this clock reading occurred in `Asia/Kolkata`.

The application is assigning a timezone interpretation to a previously timezone-less wall-clock value.

The Python function `localize_wall_clock()` explicitly performs this operation.

### Converting an instant

Once a timestamp is timezone-aware, converting it to another timezone changes its displayed local clock while preserving the instant.

The Python program converts a Kolkata timestamp to London and New York and verifies that all representations correspond to the same UTC instant.

The JavaScript program uses `Intl.DateTimeFormat` with an IANA timezone name to display an instant in different geographic zones. This is particularly useful because JavaScript's standard `Date` object does not expose an IANA timezone as a property of the object itself.

The C++ implementation deliberately uses an explicit fixed UTC offset rather than claiming that the C++17 standard library provides complete IANA timezone support. A fixed offset such as `+05:30` is not equivalent to a named timezone such as `America/New_York`, because named zones can change their offset according to historical and daylight-saving rules.

## Timezone-Aware Reporting

The same instant can belong to different local calendar dates.

For example, an event stored as:

`2026-10-01T23:30:00Z`

can be displayed as October 2 in a timezone east of UTC.

The Python `group_events_by_local_day()` function converts each instant into a requested timezone before grouping by date.

This matters for business reports. A UTC-based daily report and a local-business-day report are not necessarily equivalent.

The JavaScript implementation demonstrates the same concept with `zonedDateKey()` and groups events using `Intl.DateTimeFormat`.

The distinction is especially important for transaction systems, customer activity, usage billing, support metrics, and operational dashboards.

## Date Arithmetic

Date arithmetic can represent different business meanings.

Adding seven calendar days is a calendar operation.

Adding one month is a calendar-month operation.

Adding 86,400 seconds is an elapsed-duration operation.

These operations should not be treated as interchangeable.

The Python implementation separates `add_months()` from `timedelta`-based fixed-duration arithmetic.

The JavaScript implementation provides `addDaysToDateOnly()` and `addMonthsToDateOnly()` for date-only values and `addMilliseconds()` for timestamp instants.

The C++ implementation applies interval components separately. Calendar months and days are handled by calendar functions, while seconds and microseconds are normalized as clock components.

## Business-Day Arithmetic

Many applications need a date calculation that is more specific than ordinary calendar arithmetic.

A support request submitted on Friday may have a deadline three business days later. Saturday and Sunday should not consume business-day capacity.

The Python implementation provides `add_business_days()` and skips Saturday and Sunday.

The C++ case study applies the same idea to an operational transaction workflow.

This is distinct from adding a fixed duration. A three-business-day deadline cannot safely be represented as `72 hours`, because weekends and potentially holidays change the business interpretation.

The implementations intentionally do not model public holidays because holiday calendars are organization-specific and require an explicit data source.

## Python Implementation

The Python program is the broadest executable simulation.

Its `Event`, `DateRange`, and `SQLInterval` classes establish domain-level structures rather than treating all temporal values as interchangeable.

The program demonstrates:

- date-only values with `datetime.date`
- timestamp precision with `datetime.datetime`
- timezone-aware timestamps using `zoneinfo.ZoneInfo`
- SQL-style `DATE_PART`
- SQL-style `DATE_TRUNC`
- calendar-aware month arithmetic
- fixed-duration arithmetic
- half-open reporting windows
- local-timezone event grouping
- strict ISO parsing
- timezone validation
- CSV export of normalized timestamps
- elapsed-duration calculations
- business-day arithmetic
- automated `unittest` coverage

The tests specifically exercise leap-year month arithmetic, timestamp timezone requirements, month truncation, timezone conversion, half-open ranges, and completed calendar years.

The program is self-contained and relies on Python's standard library.

## JavaScript Implementation

The JavaScript program takes a different approach because JavaScript's built-in temporal model differs from SQL's type system.

Date-only values are represented as validated ISO strings. This avoids accidentally converting a calendar date into an instant.

Timestamp values use JavaScript `Date` objects only when an actual instant is intended.

`SqlInterval` keeps calendar months separate from fixed milliseconds.

`datePart()` extracts components using UTC accessors, while `dateTrunc()` constructs deterministic UTC boundaries.

Timezone display uses `Intl.DateTimeFormat` and explicit IANA timezone names.

The program also introduces an event-driven model through `EventBus` and `TemporalEventStore`. A stored transaction emits an event, and listeners can react without being embedded in the storage method. The event store then supports half-open timestamp queries and grouping by local business date.

This event-driven design provides a useful application-level perspective on why temporal semantics matter beyond database queries.

## C++ Transaction-Ledger Case Study

The C++ implementation models a financial transaction ledger.

A transaction contains:

- transaction identifier
- customer identifier
- timestamp
- amount in cents

The ledger validates transaction identifiers, timestamps, and non-negative amounts before accepting records.

The case study stores transactions around an October reporting boundary:

`2026-10-01`

through:

`2026-11-01`

The October query uses a half-open interval so the transaction exactly at November 1 is excluded while the transaction at the final microsecond of October remains included.

The monthly aggregation uses `std::map` keyed by year and month. This naturally provides chronological ordering of the generated monthly reports.

The implementation uses separate structures for `Date`, `Timestamp`, and `Interval`. That prevents the domain model from collapsing calendar dates, instants, and durations into one representation.

The `DatePart` enumeration demonstrates component extraction without making arbitrary string fields part of every internal operation.

The `Truncation` enumeration models boundary operations separately from extraction.

The case study also demonstrates business-day arithmetic for an operational deadline.

## Precision

Timestamp precision affects equality, range boundaries, and reporting.

Consider two values:

`2026-10-31 23:59:59.999000`

and:

`2026-10-31 23:59:59.999999`

A system that stores only milliseconds cannot distinguish those values at microsecond precision.

The Python implementation preserves microseconds internally and rounds only when presenting elapsed-duration measurements.

A good temporal design avoids repeatedly rounding timestamps before storage or comparison. Precision reduction should be an explicit boundary operation, normally performed for presentation, aggregation, or compatibility with a downstream system.

## Leap Years and Month Ends

Leap-year behavior is one of the simplest ways to expose incorrect date arithmetic.

The Gregorian leap-year rule is:

- divisible by 400: leap year
- otherwise divisible by 100: not a leap year
- otherwise divisible by 4: leap year

Therefore 2024 is a leap year while 2100 is not.

The C++ `Date::isLeapYear()` implementation encodes this rule directly.

The Python and JavaScript implementations rely on their standard date/calendar capabilities for validation while explicitly testing February 29 and month-end arithmetic.

Month arithmetic must also account for invalid target days. January 31 plus one month cannot produce February 31. The implementations clamp the day to the final valid day of the target month.

## Elapsed Time Versus Calendar Difference

Elapsed duration and calendar difference answer different questions.

If a process starts at:

`09:00`

and ends at:

`17:45`

the elapsed time is 8 hours and 45 minutes.

A calendar calculation such as "completed years since a start date" is different. Dividing elapsed days by 365 does not correctly model calendar anniversaries.

The Python implementation's `completed_years()` function compares the target date with an anniversary instead of approximating years by a fixed number of days.

The same principle applies to months, quarters, and business periods. The correct operation depends on the business meaning of the calculation.

## Common Failure Modes

### Treating a date-only value as a timestamp

A business date such as a billing date should not acquire a timezone merely because an application happens to use a timestamp class.

The JavaScript implementation avoids this by keeping date-only values as ISO calendar strings.

### Assuming every day is exactly 24 local hours

Timezone transitions can produce local calendar days whose elapsed duration differs from a naive 24-hour assumption.

The Python implementation demonstrates why timezone-aware arithmetic requires careful distinction between fixed durations and calendar semantics.

### Using `23:59:59` as a report endpoint

This can miss values when the database supports fractional seconds beyond the chosen precision.

Half-open boundaries such as `[start, next_boundary)` avoid this problem.

### Confusing extraction with truncation

`DATE_PART('month', value)` extracts a numeric component.

`DATE_TRUNC('month', value)` creates a temporal boundary.

Using one when the other is required produces different query semantics.

### Ignoring timezone semantics during grouping

Grouping by the UTC calendar date can produce different results from grouping by a customer's local calendar date.

The local timezone must be part of the reporting requirement rather than an accidental property of the database server.

### Treating one month as a fixed number of days

A month is calendar-dependent. A fixed duration and a calendar interval should remain separate in application logic.

## Performance Considerations

Temporal functions can affect query performance when they are applied to indexed columns in filtering predicates.

A range such as:

`timestamp_column >= start_boundary AND timestamp_column < end_boundary`

can be easier for a database optimizer to use with an index than a predicate that transforms every stored timestamp before comparison.

For analytics, `DATE_TRUNC` is often useful in grouping expressions, but high-volume systems may benefit from generated columns, expression indexes, partitioning, or pre-aggregated reporting tables when the database supports those mechanisms.

The Python event filtering implementation scans the complete event list, giving it linear query complexity, `O(n)`, for each range operation.

The JavaScript event store also uses a linear filter for range queries. Its sorted event collection makes chronological inspection straightforward, but the current implementation does not introduce a binary-search index.

The C++ monthly aggregation uses a `std::map`, giving logarithmic lookup and insertion complexity for each group and preserving sorted month keys. Its transaction range operation is deliberately simple and scans the ledger, which is appropriate for the instructional case study but not sufficient for very large production datasets.

## Security and Data Integrity

Temporal data can influence authorization windows, expiration periods, financial reporting, audit trails, and access policies.

Input validation is therefore part of temporal correctness.

The Python parser rejects malformed dates and timestamps without explicit timezone information when an instant is required.

The JavaScript parser rejects invalid date-only strings, timezone-less timestamps, invalid ranges, and unknown IANA timezones.

The C++ structures validate calendar fields, clock fields, timezone offsets, transaction identifiers, and transaction amounts.

Temporal values should also be treated as untrusted input when they arrive through APIs or user-controlled forms. Validation should occur before the values are used in database predicates or business decisions.

## Production Considerations

A production SQL application should define temporal semantics at the schema level rather than leaving them implicit in application code.

Important design decisions include:

- whether a column represents a date, a local wall-clock value, or a global instant
- what timestamp precision is required
- which timezone is authoritative for local business reporting
- whether recurring operations use calendar months or fixed durations
- how daylight-saving transitions are handled
- whether historical timezone rules must be preserved
- how report boundaries are defined
- whether business holidays affect deadline calculations
- how database and application timezone settings are controlled
- how temporal values are serialized across APIs

For global events, an explicit timezone-aware or UTC-normalized storage strategy is generally easier to reason about than storing ambiguous local timestamps.

For date-only business concepts, keeping them as dates rather than inventing a timezone interpretation avoids unnecessary conversion behavior.

For recurring calendar schedules, calendar arithmetic should be distinguished from fixed elapsed durations.

## C++ Timezone Limitation

The C++ case study intentionally represents timezone information as a fixed UTC offset.

For example:

`+05:30`

is stored as 330 minutes.

This demonstrates offset-aware timestamp representation but does not model the complete rules of an IANA timezone such as `America/New_York`.

A named timezone is a rule set, not merely an offset. Its historical and future offsets can change. A production C++ application requiring full timezone behavior should use a platform or library implementation that provides an appropriate IANA timezone database.

The limitation is isolated to the C++ case study so that the difference between fixed offsets and geographic timezone rules remains explicit.

## Relationship Between the Implementations

The three implementations intentionally use different structures rather than translating one program line by line.

Python emphasizes temporal semantics through standard-library date, datetime, interval, timezone, parsing, reporting, and testing abstractions.

JavaScript emphasizes the distinction between date-only values and instant-oriented `Date` objects, then adds `Intl` timezone rendering and event-driven processing.

C++ models a concrete transaction system where temporal values participate in validation, reporting windows, financial aggregation, and operational deadlines.

The common domain is SQL date and time, but each implementation demonstrates how the same temporal rules must be adapted to the capabilities and constraints of the host language.

## Practical Query Patterns

For a month-based analytical report, the important conceptual pattern is to derive a month boundary and use the next month boundary as the exclusive upper bound.

For component analysis, `DATE_PART` is appropriate when the required output is a component such as year, month, hour, or day-of-week.

For grouping into calendar periods, `DATE_TRUNC` is appropriate because it returns a temporal boundary that can serve as a grouping key.

For elapsed duration, subtract timestamps or use the database's duration facilities rather than approximating the result through calendar fields.

For local reporting, convert or interpret the timestamp according to the reporting timezone before deriving the local date or month.

For recurring calendar events, use interval semantics that preserve calendar components rather than replacing every month with a fixed day count.

## Conceptual Workflow

A reliable temporal workflow can be represented as:

`business meaning → temporal type → timezone semantics → validation → arithmetic → boundary operation → comparison/grouping → reporting`

The first decision is semantic. A value should be classified as a date, local clock value, instant, or duration before implementation details are chosen.

Once the temporal meaning is established, timezone interpretation and precision can be defined. Arithmetic can then be selected according to whether the operation is calendar-based or duration-based.

`DATE_PART` and `DATE_TRUNC` should be selected according to whether the requirement is extraction or boundary creation.

Finally, reporting and filtering should use explicit boundaries so that precision and timezone behavior do not create accidental gaps or overlaps.
