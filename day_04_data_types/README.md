# Data Types: Numeric, Categorical, Ordinal, Nominal, Binary, Discrete, Continuous, Temporal, Textual, Geographic, Identifiers, Measures and Dimensions

## Introduction

Data classification is the process of determining what a value represents, how it should be interpreted, what operations are meaningful for it, and how it should be stored, validated, transformed, analyzed, and presented.

A central principle is that **the representation of a value is not necessarily the same as its semantic data type**.

For example, `226001` is an integer from a programming-language perspective, but if it represents a postal code, treating it as a quantitative measurement would be incorrect. Likewise, `"CUS-1001"` is text syntactically, but its analytical role is an identifier.

A useful classification therefore considers several dimensions simultaneously:

- Representation type
- Semantic type
- Measurement scale
- Analytical role
- Cardinality
- Unit of measurement
- Temporal or spatial meaning
- Validation rules
- Aggregation behavior
- Security and privacy characteristics

The accompanying Python script demonstrates these concepts progressively, beginning with basic data values and moving toward validation, encoding, dimensional modeling, geographic calculations, temporal handling, data profiling, and production-oriented considerations.

## 1. What Is Data?

Data is an observation representing some property, event, entity, relationship, measurement, or description.

Examples include:

- `42` as a quantity
- `"India"` as a category
- `True` as a binary state
- `31.5` as a physical measurement
- `2026-09-04` as a date
- `"CUS-1001"` as an identifier
- `"Very Satisfied"` as an ordinal category

The same underlying value can have very different meanings depending on the field in which it appears.

For example, the value `1` might represent:

- One completed order
- A Boolean true value
- Category code 1
- Rank 1
- Priority level 1
- Product code 1
- Customer identifier 1

The numerical representation alone cannot establish the semantic interpretation.

## 2. Data Classification Is Multidimensional

A variable does not necessarily belong to one and only one data-type category.

For example:

`number_of_orders = 12`

can be classified as:

- Numeric
- Quantitative
- Discrete
- Measure

`customer_id = "CUS-1001"` can be classified as:

- Identifier
- Nominal label
- Textual representation
- Key

`satisfaction = "High"` can be classified as:

- Categorical
- Ordinal
- Qualitative
- Dimension

`revenue = 125000.50` can be classified as:

- Numeric
- Quantitative
- Continuous in conceptual interpretation
- Ratio-scale
- Measure

This multidimensional classification is more useful than attempting to force every field into one exclusive category.

## 3. Numeric Data

Numeric data represents quantities for which numerical operations have meaningful interpretations.

Typical examples include:

- Age
- Height
- Weight
- Revenue
- Quantity
- Distance
- Temperature
- Duration
- Count
- Percentage
- Monetary amount

Python commonly represents numeric values using:

- `int`
- `float`
- `Decimal`

The Python type indicates how the computer stores or manipulates the value, but it does not completely establish its semantic meaning.

For example:

`1001`

could represent:

- 1001 units
- Customer ID 1001
- Product code 1001
- Department code 1001

Only the first is obviously a quantity.

## 4. Discrete Data

Discrete data consists of distinct, countable values.

Typical examples include:

- Number of employees
- Number of orders
- Number of defects
- Number of products
- Number of website visits
- Number of support tickets

A count such as the number of completed orders is normally discrete:

`0, 1, 2, 3, 4, ...`

A value such as `7.35 completed orders` generally has no direct meaning when counting individual orders.

Discrete data is often stored as integers, but integer storage alone does not prove that a variable is conceptually discrete.

An integer customer identifier is not a discrete measurement simply because it uses an integer representation.

## 5. Continuous Data

Continuous data represents quantities that can conceptually take any value within a range.

Examples include:

- Height
- Weight
- Temperature
- Distance
- Pressure
- Voltage
- Duration
- Physical dimensions

A person's height might be stored as:

`178.4 cm`

but the underlying physical quantity can conceptually be measured at greater precision:

`178.43 cm`

or:

`178.431 cm`

The stored precision is therefore not necessarily the same as the conceptual nature of the variable.

A duration stored as an integer number of seconds may still represent a continuous physical phenomenon even though the storage representation is discrete.

## 6. Discrete vs Continuous

The distinction is primarily semantic.

### Discrete

Values are countable and distinct.

Examples:

- Number of customers
- Number of orders
- Number of defects
- Number of employees

### Continuous

Values represent measurements that can conceptually vary continuously.

Examples:

- Weight
- Height
- Distance
- Temperature
- Physical duration

A common mistake is to classify variables solely according to their Python representation.

An integer does not automatically mean discrete data, and a floating-point value does not automatically mean continuous data.

## 7. Categorical Data

Categorical data represents membership in groups or categories.

Examples include:

- Country
- Department
- Product category
- Customer segment
- Browser
- Color
- Employment status

Categorical data may be stored as:

- Strings
- Integers
- Boolean values
- Codes
- Enumerations

The defining characteristic is the meaning of the values rather than their physical storage format.

Categorical data is commonly divided into nominal and ordinal data.

## 8. Nominal Data

Nominal data consists of categories with no inherent mathematical ordering.

Examples include:

- Country
- Blood group
- Department
- Eye color
- Product type
- Browser
- Operating system

Suppose a variable contains:

`India, Japan, Germany`

There is no meaningful quantitative relationship such as:

`India > Japan`

The categories are labels.

Useful operations on nominal data include:

- Equality testing
- Grouping
- Frequency counting
- Mode calculation
- Counting distinct values

Arithmetic operations such as addition and subtraction do not normally have semantic meaning.

## 9. Ordinal Data

Ordinal data is categorical data with a meaningful order.

Examples include:

- Low, Medium, High
- Poor, Fair, Good, Excellent
- Bronze, Silver, Gold
- Satisfaction ratings
- Risk levels
- Education levels

For example:

`Low < Medium < High`

The ordering is meaningful.

The critical limitation is that the numerical distance between categories is not necessarily equal.

If:

`Poor < Fair < Good < Excellent`

it does not automatically follow that:

`Good - Fair = Fair - Poor`

Therefore ordinal data supports ordering and ranking, but arithmetic interpretation requires additional justification.

## 10. Nominal vs Ordinal

The distinction is based on ordering.

| Property | Nominal | Ordinal |
|---|---|---|
| Categories | Yes | Yes |
| Meaningful order | No | Yes |
| Ranking | No | Yes |
| Equality comparison | Yes | Yes |
| Frequency counting | Yes | Yes |
| Median | Generally not meaningful | Often meaningful |
| Arithmetic differences | No | Not automatically meaningful |

Examples:

Nominal:

- Country
- Department
- Color

Ordinal:

- Low / Medium / High
- Poor / Fair / Good / Excellent
- Satisfaction levels

## 11. Binary Data

Binary data has two possible states.

Examples include:

- True / False
- Yes / No
- Active / Inactive
- Approved / Rejected
- Defective / Non-defective
- Churned / Retained

Binary values may be represented using:

- Boolean values
- `0` and `1`
- `"Yes"` and `"No"`
- `"True"` and `"False"`
- Domain-specific codes

Binary data is frequently encoded as `0` and `1` for analytical and machine-learning purposes.

For a binary variable represented by `0` and `1`, its arithmetic mean equals the proportion of observations having value `1`.

For example:

`[1, 0, 1, 1, 0]`

has mean:

`3 / 5 = 0.60`

Therefore 60% of observations belong to class `1`.

## 12. Binary Does Not Always Mean Boolean

Binary data can be Boolean, but the broader analytical concept is simply two-state data.

For example:

- `Approved / Rejected`
- `Male / Female` in a simplified legacy dataset
- `Defective / Non-defective`

may all be binary categorical variables even though their original representation is textual.

The important property is the number and semantics of the states.

## 13. Temporal Data

Temporal data represents time-related information.

Common temporal forms include:

- Date
- Time
- Datetime
- Timestamp
- Duration
- Time interval
- Period

Examples:

- Order date
- Login timestamp
- Delivery timestamp
- Subscription duration
- Transaction time

Temporal data supports operations such as:

- Chronological ordering
- Date comparison
- Time difference
- Duration calculation
- Calendar extraction
- Windowing
- Time-based aggregation

## 14. Date vs Time vs Datetime

A date identifies a calendar day.

Example:

`2026-09-04`

A time identifies a time of day.

Example:

`14:30:15`

A datetime combines calendar and time information.

Example:

`2026-09-04 14:30:15`

These are related but distinct concepts.

A date does not identify a specific time of day.

## 15. Temporal Granularity

Temporal data can have different levels of granularity:

- Year
- Quarter
- Month
- Week
- Day
- Hour
- Minute
- Second
- Millisecond

A timestamp can therefore be transformed into analytical attributes such as:

- Year
- Month
- Day
- Weekday
- Hour
- Minute

These derived attributes can become dimensions in analytical systems.

## 16. Time Zones

Timezone handling is essential in production systems that operate across geographic regions.

A naive datetime lacks timezone information.

A timezone-aware datetime explicitly associates the timestamp with a timezone.

A common production practice is to:

- Store timestamps in UTC
- Preserve timezone information when the original local context matters
- Convert to local time at presentation boundaries

Ignoring timezone semantics can produce errors in:

- Event ordering
- Daily reports
- Log analysis
- Scheduling
- Financial transactions
- Distributed systems
- Time-series analysis

## 17. Duration Is Different from a Date

A date identifies a calendar point.

A duration represents elapsed time.

For example:

`2026-09-04`

is a date.

`7 days`

is a duration.

The two should not be treated as interchangeable.

## 18. Textual Data

Textual data represents character-based information.

Examples include:

- Customer reviews
- Support messages
- Product descriptions
- Comments
- Addresses
- Notes
- Documents
- Natural-language messages

Text may be:

- Structured
- Semi-structured
- Unstructured

Structured text might look like:

`ORDER-1001`

A natural-language sentence might look like:

`The customer reported that the package arrived late.`

A string does not automatically mean that the field is textual. A string can also represent an identifier, category, date, code, or geographic label.

## 19. Structured and Unstructured Text

Structured text follows predictable patterns.

Examples:

- `CUS-1001`
- `ORDER-5002`
- `IN-226001`

Unstructured text is natural language or free-form content.

Examples:

- Customer complaints
- Product reviews
- Support tickets
- Comments

Text processing can include:

- Normalization
- Tokenization
- Pattern matching
- Search
- Classification
- Entity extraction
- Linguistic analysis

The accompanying script demonstrates regular-expression extraction from textual data.

## 20. Text Normalization

Text normalization can make equivalent values more consistent.

For example:

- `"india"`
- `"India "`
- `" INDIA"`
- `"INDIA"`

may all represent the same category.

Basic normalization can include:

- Trimming whitespace
- Converting case
- Collapsing repeated whitespace

But formatting normalization is not always enough.

For example:

- `USA`
- `US`
- `United States`

require semantic mapping rather than merely changing capitalization.

## 21. Geographic Data

Geographic data represents location or spatial information.

Examples include:

- Latitude
- Longitude
- Country
- State
- City
- Postal code
- Address
- Point
- Line
- Polygon

Geographic data can be divided into spatial structures such as:

- Point data
- Line data
- Polygon data
- Raster data

Latitude and longitude are numeric in representation but geographic in meaning.

## 22. Latitude and Longitude

Latitude normally ranges from:

`-90` to `90`

Longitude normally ranges from:

`-180` to `180`

Examples:

- Latitude: `26.8467`
- Longitude: `80.9462`

A geographic coordinate should therefore be validated according to geographic rules rather than merely generic numeric rules.

## 23. Geographic Distance

Latitude and longitude cannot generally be compared using ordinary Cartesian distance formulas because Earth is approximately spherical.

The Python script implements the Haversine formula to calculate an approximate great-circle distance between two geographic points.

The Haversine approach is appropriate for many educational and approximate distance calculations.

More advanced geographic applications may require:

- Coordinate reference systems
- Projections
- Geodesic calculations
- Spatial indexes
- Geometry libraries
- Polygon containment
- Spatial joins

## 24. Postal Codes Are Not Quantities

A postal code such as:

`226001`

looks numeric.

But adding postal codes does not have meaningful quantitative interpretation.

It is better understood as a geographic code or categorical identifier.

The same principle applies to:

- Phone numbers
- Employee codes
- Product codes
- Account numbers
- Customer IDs
- ZIP codes

Digit-only representation does not make a value a measurement.

## 25. Identifiers

An identifier uniquely identifies an entity, record, or object.

Examples include:

- Customer ID
- Employee ID
- Order ID
- Transaction ID
- Product SKU
- UUID

An identifier answers:

**Which entity is this?**

A measure answers:

**How much, how many, or how large is something?**

For example:

`customer_id = "CUS-1001"`

identifies a customer.

`revenue = 100000`

measures an amount.

Identifiers normally support:

- Equality
- Lookup
- Joining
- Uniqueness validation

They generally should not be subjected to arithmetic operations.

## 26. Identifier Uniqueness

If a field is supposed to uniquely identify records, duplicate values indicate a potential data-quality problem.

For example:

`CUS-1, CUS-2, CUS-3`

is unique.

But:

`CUS-1, CUS-2, CUS-1`

contains a duplicate.

Whether a duplicate is actually an error depends on the intended grain of the dataset.

A customer dimension might require one row per customer, while a transaction table may legitimately contain multiple rows associated with the same customer.

## 27. Natural Keys, Surrogate Keys and Composite Keys

Identifiers can take several forms.

### Natural Key

A natural key originates from meaningful business data.

Example:

`email@example.com`

### Surrogate Key

A surrogate key is artificially generated for database purposes.

Example:

`100001`

### UUID

A UUID provides a large identifier space and is commonly used when distributed systems require globally unique identifiers.

### Composite Key

A composite key uses multiple fields together.

Example:

`(date, store_id, product_id)`

The correct choice depends on:

- Uniqueness
- Stability
- Integration requirements
- Performance
- Storage
- Business semantics

## 28. Identifiers Should Not Automatically Become Machine-Learning Features

Identifiers are often high-cardinality fields.

For example:

`customer_id`

may have hundreds of thousands or millions of distinct values.

One-hot encoding such a field could create an enormous number of features.

Identifiers can also contain accidental information. Sequential IDs may encode creation order or operational processes.

Identifiers should therefore be evaluated carefully before being used as predictive features.

## 29. Measurement Scales

A classical framework describes four measurement scales:

1. Nominal
2. Ordinal
3. Interval
4. Ratio

These scales describe what kinds of mathematical relationships are meaningful.

## 30. Nominal Scale

Nominal data contains categories without inherent order.

Examples:

- Country
- Department
- Eye color
- Product category

Useful operations include:

- Equality
- Frequency
- Mode
- Grouping

## 31. Ordinal Scale

Ordinal data has meaningful order.

Examples:

- Low
- Medium
- High

or:

- Poor
- Fair
- Good
- Excellent

Ranking is meaningful, but equal distances between categories cannot automatically be assumed.

## 32. Interval Scale

Interval data has meaningful differences between values but lacks a meaningful absolute zero.

A common example is Celsius temperature.

The difference between:

`20°C`

and:

`10°C`

is meaningful.

But saying:

`20°C is twice as hot as 10°C`

is not a valid ratio interpretation.

The zero point of Celsius is not the absolute absence of thermal energy.

## 33. Ratio Scale

Ratio data has:

- Meaningful ordering
- Meaningful differences
- A meaningful zero

Examples include:

- Weight
- Height
- Distance
- Duration
- Revenue
- Quantity

If one object weighs `20 kg` and another weighs `10 kg`, the first has twice the mass of the second.

Ratio interpretation is meaningful because zero represents the absence of the measured quantity.

## 34. Measurement Scale Comparison

| Scale | Categories | Order | Equal Differences | Meaningful Zero |
|---|---:|---:|---:|---:|
| Nominal | Yes | No | No | No |
| Ordinal | Yes | Yes | Not necessarily | No |
| Interval | No | Yes | Yes | No |
| Ratio | No | Yes | Yes | Yes |

The exact statistical treatment of particular variables should always be considered in context.

## 35. Measures

A measure is generally a quantity that can be analyzed or aggregated.

Examples:

- Revenue
- Profit
- Quantity sold
- Number of orders
- Discount amount
- Weight
- Distance

Typical operations include:

- Sum
- Average
- Minimum
- Maximum
- Count
- Median
- Percentiles

The appropriate aggregation depends on the semantics of the measure.

## 36. Dimensions

A dimension provides descriptive or contextual information used to organize analysis.

Examples include:

- Customer
- Country
- Product
- Department
- Region
- Date
- Segment

A dimension answers questions such as:

- Which country?
- Which product?
- Which customer?
- Which period?
- Which department?

Dimensions are commonly used for filtering, grouping, slicing, and drill-down.

## 37. Measures vs Dimensions

Consider a sales record:

- Country = India
- Product = Laptop
- Date = September 4, 2026
- Revenue = 120000
- Quantity = 3

Here:

- Country is a dimension.
- Product is a dimension.
- Date is a dimension.
- Revenue is a measure.
- Quantity is a measure.

The distinction is based on analytical role rather than simply whether a field is numeric.

## 38. Dimensions Can Be Numeric

A dimension does not have to be categorical in its physical representation.

Examples:

- Year = `2026`
- Fiscal year = `2026`
- Latitude = `26.8467`
- Longitude = `80.9462`
- Date key = `20260904`

These values may be numeric but can still function as dimensions.

## 39. Measures Can Be Derived from Categories

A categorical variable can generate a numeric measure through aggregation.

For example:

`Approved, Rejected, Approved, Approved`

contains a categorical status dimension.

The count of approved records is:

`3`

The status remains categorical, while the resulting count is a numeric measure.

## 40. Additive, Semi-Additive and Non-Additive Measures

Advanced BI systems distinguish measures according to their aggregation behavior.

### Additive Measures

Can generally be summed across relevant dimensions.

Example:

- Sales revenue
- Units sold

### Semi-Additive Measures

Can be summed across some dimensions but not others.

Account balance is a common example.

A balance may be summed across customers for a particular date, but summing daily balances across time usually does not represent a meaningful total balance.

### Non-Additive Measures

Should not normally be summed.

Examples:

- Percentages
- Ratios
- Average values
- Margin percentages

The correct aggregation rule is an important part of measure metadata.

## 41. Dimension Hierarchies

Dimensions can have hierarchical structures.

Geographic hierarchy:

`Country → State → City → Store`

Temporal hierarchy:

`Year → Quarter → Month → Day`

Hierarchies support:

- Drill-down
- Roll-up
- Aggregation
- Filtering
- Dashboard navigation

Real-world hierarchies may not always be perfectly strict because administrative boundaries can change and geographic relationships can be complex.

## 42. Categorical Encoding

Machine-learning and computational systems frequently require categorical data to be represented numerically.

Common techniques include:

- Label encoding
- One-hot encoding
- Ordinal encoding
- Frequency encoding
- Target encoding

The correct approach depends on the semantics of the category.

## 43. Label Encoding

Suppose:

- Red
- Blue
- Green

are mapped to:

- Red → 0
- Blue → 1
- Green → 2

This is compact, but the numbers may imply an artificial ordering.

For nominal data, arbitrary integer codes should not automatically be interpreted as quantities.

## 44. One-Hot Encoding

One-hot encoding creates one binary field for each category.

For:

- Red
- Blue
- Green

a row containing Red might become conceptually:

- Red = 1
- Blue = 0
- Green = 0

This preserves the fact that the categories are distinct rather than naturally ordered.

One-hot encoding can become expensive for high-cardinality variables.

## 45. Ordinal Encoding

Ordinal encoding assigns values according to an actual ordering.

For example:

- Low → 1
- Medium → 2
- High → 3

This is appropriate when the ordering is meaningful.

It should not be used merely because categories happen to be stored as strings.

## 46. Cardinality

Cardinality is the number of distinct values in a field.

Examples:

- Country: relatively low cardinality
- Department: low cardinality
- Customer ID: potentially high cardinality
- Transaction ID: very high cardinality

Cardinality affects:

- Storage
- Indexing
- Encoding
- Query performance
- Dashboard usability
- Machine-learning feature size

High-cardinality categorical variables require special consideration.

## 47. Dictionary Encoding

Repeated categorical strings can consume unnecessary storage.

A dictionary-encoding strategy might represent:

- `0 → India`
- `1 → Japan`
- `2 → Germany`

and store the numeric codes instead.

This can reduce storage and improve performance in columnar systems.

The codes are storage representations and do not create an ordinal relationship among the categories.

## 48. Derived Variables

A derived variable is calculated from existing data.

Examples:

- Age group derived from age
- Profit derived from revenue and cost
- Month derived from a date
- Tenure derived from registration date
- Distance derived from geographic coordinates

Derived fields can have different semantic types from their source fields.

For example:

`age = 33`

is numeric and discrete.

`age_group = "30-39"`

is categorical.

## 49. Discretization

Discretization converts continuous or numeric values into categories.

Example:

`33`

can become:

`30-39`

This can improve interpretability but causes information loss.

The original exact value `33` is no longer available after replacing it with `30-39`.

Poorly selected boundaries can also introduce artificial distinctions.

## 50. Numeric-Looking Text

Some text fields contain only digits.

Examples:

- Phone number
- Postal code
- Employee code
- Product code
- Account number

Converting these values to integers can destroy meaningful formatting.

For example:

`"00125"`

becomes:

`125`

when converted to an integer.

The leading zeros may be part of the identifier's required representation.

## 51. Codes vs Measures

Consider two fields:

`department_code = 101`

and:

`department_headcount = 101`

The numeric values are identical.

Their meanings are not.

The first is a code.

The second is a quantity.

This distinction demonstrates why semantic metadata is necessary.

## 52. Missing Values

Missingness is not itself a data type.

A missing value can mean:

- Unknown
- Not collected
- Not applicable
- Not yet available
- Intentionally withheld

Different missingness meanings can require different analytical treatment.

Common representations include:

- `None`
- `NaN`
- `NULL`
- Empty strings
- Sentinel values

A system should avoid collapsing all forms of missingness into a single meaning without considering the data-generating process.

## 53. Zero Is Not Missing

Zero is normally a valid numerical value.

False is normally a valid Boolean value.

Therefore this pattern is dangerous:

`if not value`

because it treats multiple legitimate values as false-like.

For example:

- `0`
- `False`
- `""`
- `None`

have different meanings.

The Python script explicitly demonstrates this distinction.

## 54. Data Validation

Validation rules should be based on semantic meaning.

Examples:

### Age

A reasonable domain rule might be:

`0 <= age <= 130`

The exact upper limit depends on the application.

### Percentage

A percentage represented directly as a percent might satisfy:

`0 <= value <= 100`

### Latitude

`-90 <= latitude <= 90`

### Longitude

`-180 <= longitude <= 180`

### Controlled Category

A status field might be restricted to:

- Pending
- Approved
- Rejected

### Identifier

An identifier may require:

- Correct format
- Non-null value
- Uniqueness

## 55. Type Validity vs Domain Validity

A value can have the correct programming type but still be invalid.

For example:

`age = 250`

is numeric.

It may still violate the domain rules for human age.

Validation therefore has multiple levels:

1. Representation validity
2. Type validity
3. Domain validity
4. Business-rule validity
5. Statistical plausibility

A production data pipeline should not stop after checking the programming-language type.

## 56. Data Quality

Important data-quality dimensions include:

- Completeness
- Validity
- Uniqueness
- Consistency
- Accuracy
- Timeliness
- Conformity

Different types require different checks.

For identifiers:

- Uniqueness
- Format
- Nullability

For categories:

- Allowed values
- Consistency
- Cardinality

For numbers:

- Range
- Precision
- Units
- Outliers

For timestamps:

- Timezone
- Ordering
- Valid calendar values
- Granularity

For geographic coordinates:

- Latitude range
- Longitude range
- Coordinate reference assumptions

## 57. Type Inference

Data systems often attempt to infer types from raw data.

For example:

`["1", "2", "3", "4"]`

looks numeric.

But those values could represent:

- Quantities
- Category codes
- Ranks
- Product codes
- Identifiers

Automated inference can detect representation patterns, but semantic classification often requires:

- Metadata
- Domain knowledge
- Field names
- Data dictionaries
- Business rules

## 58. Data Type Drift

Type drift occurs when a field's representation or meaning changes unexpectedly.

For example:

Day 1:

`100.50`

Day 2:

`"100.50"`

Day 3:

`"unknown"`

A field that was previously numeric has become mixed-type.

Type drift can break:

- Data pipelines
- Queries
- Aggregations
- Machine-learning models
- Reports
- APIs

Schema monitoring is therefore important in production systems.

## 59. Percentage Representation

Percentages have a common representation ambiguity.

These may both represent the same concept:

`0.25`

and:

`25`

The first may represent a fraction.

The second may represent a percentage.

A schema should explicitly define the representation.

The accompanying Python script provides a normalization function that converts both representations into a consistent fraction.

## 60. Units of Measurement

A numeric value without a unit can be ambiguous.

For example:

`10`

could mean:

- 10 kg
- 10 meters
- 10 seconds
- 10 dollars
- 10 percent

The unit is therefore part of the semantic definition of a measurement.

Important metadata for numeric fields can include:

- Unit
- Precision
- Scale
- Valid range
- Measurement scale

## 61. Monetary Data

Money requires special numerical treatment.

Binary floating-point representation cannot exactly represent many decimal fractions.

For example:

`0.1 + 0.2`

does not necessarily produce an exact binary representation of `0.3`.

For financial calculations, decimal arithmetic is often more appropriate.

Python's `Decimal` type is useful for educational demonstrations of exact decimal arithmetic.

Production financial systems should define:

- Currency
- Precision
- Scale
- Rounding rules
- Tax treatment
- Exchange-rate assumptions

## 62. Floating-Point Precision

Floating-point arithmetic is designed for efficient approximation rather than exact representation of every decimal number.

Therefore:

`0.1 + 0.2 == 0.3`

can evaluate to false.

When approximate numerical comparison is appropriate, a tolerance-based comparison such as `math.isclose()` can be used.

The correct approach depends on the domain.

Financial values often require decimal arithmetic and explicit rounding rules rather than tolerance-based floating-point comparison.

## 63. Temporal Feature Engineering

A timestamp can be transformed into multiple features:

- Year
- Month
- Day
- Weekday
- Hour
- Minute

Some temporal features are cyclic.

For example:

`23:00`

and:

`00:00`

are close in time-of-day.

Representing hours simply as integers from `0` to `23` can incorrectly make those two values appear far apart in some modeling contexts.

A common technique uses sine and cosine transformations to represent cyclic structure.

## 64. Geographic Privacy

Geographic precision can influence privacy risk.

A country-level location contains relatively coarse spatial information.

A city-level location contains more detail.

Exact latitude and longitude can provide substantially greater precision.

Therefore geographic data should be evaluated not only as a technical type but also for:

- Sensitivity
- Precision requirements
- Access control
- Retention
- Minimization

## 65. Security Classification Is Separate

Being numeric, categorical, textual, temporal, or geographic does not itself determine whether a field is sensitive.

Security and privacy are separate classification dimensions.

A numeric field might contain financial information.

A textual field might contain confidential information.

An identifier might be personally identifying.

A geographic field might reveal a sensitive location.

A mature data architecture therefore maintains both:

- Technical/semantic classification
- Security/privacy classification

## 66. Text and Security

Free-form text can unexpectedly contain sensitive information.

Customer comments may contain:

- Names
- Phone numbers
- Addresses
- Account numbers
- Internal information
- Confidential business details

Logging raw text without appropriate controls can therefore create security and privacy problems.

Production systems should consider:

- Access controls
- Encryption
- Masking
- Tokenization
- Retention policies
- Safe logging
- Data minimization

## 67. Data Type and Database Design

Database schemas should distinguish semantic roles clearly.

Examples:

`customer_id`

should generally be treated as an identifier.

`revenue`

should use a suitable numeric representation.

`created_at`

should use a temporal type.

`is_active`

should use a Boolean or equivalent two-state representation.

`country_code`

should use controlled categorical values.

Good database design prevents many downstream analytical errors.

## 68. Data Type and API Design

APIs should communicate semantic expectations explicitly.

A field definition should ideally specify information such as:

- Representation
- Required/optional status
- Minimum
- Maximum
- Allowed values
- Format
- Unit
- Timezone
- Nullability

For example:

`quantity`

can be defined as a non-negative integer.

`created_at`

can be defined as a timezone-aware timestamp.

`customer_id`

can be defined as a required string identifier.

Explicit schemas reduce ambiguity between systems.

## 69. Data Type and File Formats

Different file formats represent data differently.

### CSV

CSV fundamentally contains textual fields and therefore requires type interpretation during ingestion.

A value such as:

`00123`

can accidentally be interpreted as an integer.

### JSON

JSON supports:

- Strings
- Numbers
- Booleans
- Null
- Arrays
- Objects

### Columnar Formats

Columnar analytical formats can preserve explicit column types and support efficient storage and processing.

Schema-aware ingestion is important because raw textual representation does not necessarily establish semantic meaning.

## 70. Cardinality and Performance

Cardinality affects computational and storage behavior.

Low-cardinality fields such as country may have only a small number of distinct values.

High-cardinality fields such as transaction IDs may have nearly one unique value per row.

High-cardinality categorical variables can cause:

- Large one-hot encoded matrices
- More storage
- More memory consumption
- More expensive grouping
- Less useful dashboards

Dictionary encoding can reduce storage for repeated categorical values.

## 71. Measures and Aggregation

Different measures require different aggregation rules.

### Revenue

`SUM(revenue)` is usually meaningful.

### Quantity

`SUM(quantity)` is generally meaningful.

### Customer ID

`SUM(customer_id)` is meaningless.

### Percentage

Summing percentages is generally inappropriate.

### Account Balance

Summing across time is generally inappropriate.

### Average

An average is itself an aggregate and normally should not be blindly summed.

Correct aggregation requires semantic understanding.

## 72. Data Profiling

Data profiling examines the contents of a dataset before analysis.

Useful profiling statistics include:

- Number of rows
- Missing values
- Distinct values
- Duplicate values
- Minimum
- Maximum
- Mean
- Median
- Frequency distributions
- Observed Python types
- Invalid values

Profiling helps reveal discrepancies between assumed and actual data types.

## 73. Data Normalization

Normalization can refer to different processes depending on context.

For textual categories, normalization may involve:

- Trimming whitespace
- Case normalization
- Standardizing labels

For numerical data, normalization can refer to transformations such as scaling.

For schemas, normalization may refer to database design principles.

The exact meaning should therefore be determined from context.

## 74. Semantic Metadata

A robust data system should maintain metadata such as:

- Field name
- Business definition
- Storage type
- Semantic type
- Unit
- Measurement scale
- Allowed values
- Nullability
- Uniqueness
- Aggregation rule
- Source system
- Update frequency
- Sensitivity classification

Metadata is particularly important when multiple systems exchange data.

## 75. Example Semantic Schema

A sales transaction might contain:

| Field | Semantic Type | Role |
|---|---|---|
| transaction_id | Identifier | Key |
| transaction_time | Temporal | Time dimension |
| customer_id | Identifier | Key |
| country | Nominal categorical | Dimension |
| product | Nominal categorical | Dimension |
| quantity | Discrete numeric | Measure |
| unit_price | Numeric monetary | Measure |
| discount_percent | Ratio measure | Measure |
| review | Textual | Descriptive attribute |
| latitude | Geographic numeric | Spatial attribute |
| longitude | Geographic numeric | Spatial attribute |
| is_returned | Binary | Attribute |

This illustrates why data classification should be viewed as a schema-level activity rather than simply a list of Python types.

## 76. Data Types in Machine Learning

Different data types require different preprocessing strategies.

### Numeric

Possible operations:

- Scaling
- Normalization
- Transformation
- Imputation
- Outlier treatment

### Nominal Categorical

Possible approaches:

- One-hot encoding
- Specialized categorical encodings

### Ordinal

Possible approach:

- Ordered encoding that preserves the ranking

### Binary

Common representation:

- `0`
- `1`

### Textual

Possible approaches include:

- Tokenization
- Vectorization
- Embeddings
- Feature extraction

### Temporal

Possible features include:

- Year
- Month
- Day
- Hour
- Duration
- Cyclic encodings

### Geographic

Possible representations include:

- Coordinates
- Distances
- Regions
- Spatial features

### Identifiers

Usually require special scrutiny because they can have high cardinality or encode accidental information.

## 77. Common Machine-Learning Mistake: Arbitrary Category Numbers

Suppose:

- Red → 1
- Blue → 2
- Green → 3

If an algorithm interprets these as numeric quantities, it might infer:

`Green > Blue > Red`

There is no semantic reason for that relationship.

For nominal categories, an encoding strategy should avoid introducing false numerical ordering.

Ordinal categories are different because an actual order exists.

## 78. Common Mistake: Treating Identifiers as Predictive Features

Identifiers often have no intrinsic predictive meaning.

A customer ID is primarily used to distinguish customers.

Using it as a numerical feature may introduce:

- Artificial ordering
- Spurious relationships
- High cardinality
- Data leakage
- Poor generalization

Identifiers should therefore be analyzed for semantic content before being used in a model.

## 79. Common Mistake: Assuming Every Numeric Field Is a Measure

The following may all be stored as numbers:

- Revenue
- Postal code
- Customer ID
- Product code
- Department code
- Rank
- Temperature

They do not have the same analytical semantics.

A robust data dictionary should explicitly identify the role of each field.

## 80. Common Mistake: Assuming Every String Is Text

A string can represent:

- Natural language
- Identifier
- Category
- Code
- Date
- Timestamp
- Geographic label

For example:

`"CUS-1001"`

is syntactically text but semantically an identifier.

`"India"`

is syntactically text but semantically a nominal category.

`"2026-09-04"`

is syntactically text in raw form but semantically temporal.

## 81. Common Mistake: Treating All Missing Values the Same

An empty field can mean:

- Unknown
- Not applicable
- Not collected
- Not yet available
- Intentionally omitted

The analytical consequences can differ significantly.

A mature data pipeline should preserve missingness semantics whenever they matter.

## 82. Common Mistake: Ignoring Units

A value such as:

`10`

is incomplete without knowing whether it means:

- 10 kg
- 10 meters
- 10 seconds
- 10 dollars
- 10 percent

Unit metadata should therefore accompany quantitative measurements.

## 83. Common Mistake: Ignoring Time Zones

A timestamp without timezone semantics can be ambiguous in distributed systems.

Two systems might record:

`2026-09-04 14:00`

while referring to different local times.

This can cause incorrect:

- Ordering
- Aggregation
- Scheduling
- Reporting
- Event correlation

Timezone-aware timestamps reduce this ambiguity.

## 84. Common Mistake: Summing Non-Additive Measures

A percentage, ratio, or balance should not automatically be summed.

For example, if two stores have:

- Store A margin = 20%
- Store B margin = 30%

the combined margin is not necessarily:

`20% + 30% = 50%`

Correct calculations often require returning to the underlying numerator and denominator.

## 85. Common Mistake: Over-Binning Continuous Data

Converting:

`33`

into:

`30-39`

can simplify reporting but removes precision.

Excessive binning can:

- Discard information
- Hide relationships
- Introduce arbitrary boundaries
- Reduce statistical resolution

Binning should therefore have a clear analytical purpose.

## 86. Common Mistake: Confusing Storage Optimization with Semantic Encoding

A category code such as:

`India → 0`

and:

`Japan → 1`

may be a storage optimization.

It does not imply:

`Japan > India`

The distinction between storage representation and semantic relationship is fundamental.

## 87. Data Type and Performance

Data-type decisions influence:

- Memory consumption
- Disk usage
- Query speed
- Index size
- Encoding size
- Serialization cost
- Network transfer

Examples:

- Compact Boolean representations can reduce storage.
- Dictionary encoding can reduce repeated categorical strings.
- Appropriate numeric precision prevents unnecessary storage.
- Efficient identifier indexing improves lookup.
- Timestamp representations support efficient range filtering.

Correctness should remain the primary requirement, followed by appropriate optimization.

## 88. Data Type and Security

Data classification supports security decisions but does not replace them.

A complete data-governance approach may classify fields by:

### Technical Type

- Numeric
- Text
- Temporal
- Geographic

### Semantic Type

- Measure
- Dimension
- Identifier
- Category

### Sensitivity

- Public
- Internal
- Confidential
- Restricted

These dimensions are independent.

A field can simultaneously be:

`Geographic + Numeric + Sensitive`

or:

`Textual + Identifier + Sensitive`

## 89. Data Type and Production Systems

Production systems should define explicit schemas rather than relying entirely on inference.

Important schema properties include:

- Data type
- Semantic type
- Required/optional status
- Nullability
- Allowed values
- Valid ranges
- Units
- Precision
- Timezone
- Uniqueness
- Aggregation behavior
- Sensitivity

Explicit schemas reduce errors during ingestion, storage, transformation, and reporting.

## 90. Data-Type Decision Framework

When encountering an unfamiliar field, ask the following questions.

### Question 1: What does the value represent?

Is it:

- A quantity?
- A category?
- A label?
- A timestamp?
- Text?
- A location?
- An identifier?

### Question 2: Is there an intrinsic ordering?

If no, the variable may be nominal.

If yes, it may be ordinal or numeric.

### Question 3: Is it countable or measurable?

Countable values tend to be discrete.

Measured quantities are often continuous.

### Question 4: Does zero have a meaningful interpretation?

If yes and ratios are meaningful, ratio-scale interpretation may apply.

### Question 5: Can it be aggregated?

If yes, determine which aggregation is valid.

### Question 6: Does it identify an entity?

If yes, it may be an identifier rather than a measure.

### Question 7: Does it describe analytical context?

If yes, it may function as a dimension.

### Question 8: Does it require units?

If yes, the unit is part of the field's semantic definition.

### Question 9: Does it contain temporal or spatial semantics?

If yes, generic numeric or textual classification is insufficient.

### Question 10: Does it have security or privacy implications?

Technical type alone cannot answer this question.

## 91. A Practical Classification Table

| Data Type | Meaning | Typical Examples | Common Operations |
|---|---|---|---|
| Numeric | Quantity | Revenue, weight | Arithmetic, statistics |
| Categorical | Group membership | Country, department | Grouping, frequency |
| Nominal | Unordered categories | Country, color | Count, mode |
| Ordinal | Ordered categories | Low, medium, high | Rank, order |
| Binary | Two states | True/false | Count, proportion |
| Discrete | Countable values | Number of orders | Count, sum |
| Continuous | Measurable quantity | Height, weight | Mean, variance |
| Temporal | Time-related value | Date, timestamp | Ordering, duration |
| Textual | Character/natural language data | Review, comment | Search, extraction |
| Geographic | Spatial information | Latitude, longitude | Distance, spatial analysis |
| Identifier | Entity/record identity | Customer ID | Lookup, join, uniqueness |
| Measure | Quantifiable analytical value | Revenue, quantity | Sum, average |
| Dimension | Descriptive analytical context | Product, country | Grouping, filtering |

## 92. Important Distinctions

### Numeric vs Numeric-Looking

A numeric-looking value is not automatically quantitative.

### Nominal vs Ordinal

Nominal has no inherent order.

Ordinal has meaningful order.

### Discrete vs Continuous

Discrete values are countable.

Continuous values represent measurable quantities.

### Identifier vs Measure

An identifier identifies something.

A measure quantifies something.

### Dimension vs Measure

A dimension provides context.

A measure provides a quantity for analysis.

### Storage Type vs Semantic Type

Storage type describes how a system represents the value.

Semantic type describes what the value means.

### Missing vs Zero

Missing means information is absent or unavailable.

Zero is usually an actual numerical value.

### Interval vs Ratio

Interval supports meaningful differences.

Ratio additionally supports meaningful ratios because zero has an absolute interpretation.

## 93. Advanced Concept: Multiple Classifications

A field can have several valid classifications at once.

For example:

`revenue`

can be:

- Numeric
- Continuous
- Quantitative
- Ratio-scale
- Measure
- Monetary

`country`

can be:

- Categorical
- Nominal
- Dimension
- Geographic descriptor

`customer_id`

can be:

- Textual in representation
- Nominal in measurement scale
- Identifier
- Key
- High-cardinality

This layered classification is more powerful than a single-label data-type system.

## 94. Advanced Concept: Semantic Type vs Storage Type

Consider:

`postal_code = "226001"`

Storage type:

`string`

Semantic type:

`geographic code`

Measurement scale:

`nominal`

Analytical role:

`dimension/attribute`

This demonstrates why database and analytics systems benefit from semantic metadata beyond primitive storage types.

## 95. Advanced Concept: Analytical Grain

The meaning of a field can depend on the grain of a dataset.

For example, a customer ID can appear repeatedly in a transaction table.

That does not make it invalid.

If the grain is:

`one row per transaction`

then many transactions can legitimately share one customer ID.

If the grain is:

`one row per customer`

then duplicate customer IDs may indicate an error.

Uniqueness therefore must always be evaluated relative to dataset grain.

## 96. Advanced Concept: Derived Measures

Measures can be derived from other fields.

For example:

`net_revenue = gross_revenue - discount`

or:

`profit = revenue - cost`

Derived measures should have explicit definitions so that different systems do not calculate them inconsistently.

## 97. Advanced Concept: Derived Dimensions

Dimensions can also be derived.

Examples:

- Age → age band
- Timestamp → month
- Date → fiscal quarter
- Coordinates → region
- Revenue → customer segment

Derived dimensions simplify analysis but can introduce information loss or classification assumptions.

## 98. Advanced Concept: Canonical Categories

Categorical data should ideally use canonical values.

Instead of allowing:

- USA
- US
- United States
- U.S.A.

a controlled system can define one canonical representation:

`United States`

This improves:

- Grouping
- Filtering
- Reporting
- Joins
- Data quality

Reference data and controlled vocabularies are useful for this purpose.

## 99. Advanced Concept: Schema Evolution

Schemas change over time.

A field can evolve from:

`integer`

to:

`string`

or a category set can gain new values.

Production systems should therefore monitor:

- Type changes
- New categories
- Removed categories
- Range changes
- Nullability changes
- Cardinality changes

Schema evolution should be controlled rather than discovered only after downstream failures.

## 100. Practical Data-Type Workflow

A robust workflow is:

1. Inspect the raw data.
2. Understand the business meaning.
3. Identify the storage representation.
4. Determine semantic type.
5. Determine measurement scale.
6. Determine analytical role.
7. Identify units.
8. Define valid ranges.
9. Define allowed categories.
10. Define nullability.
11. Define uniqueness requirements.
12. Validate the data.
13. Normalize representations.
14. Apply appropriate transformations.
15. Select type-appropriate aggregations.
16. Monitor data quality and schema drift.

This workflow prevents many common analytical errors.

## 101. What the Python Script Demonstrates

The script begins with simple Python values and progressively develops a semantic understanding of data.

It demonstrates:

- Basic numeric values
- Discrete counts
- Continuous measurements
- Categorical data
- Nominal categories
- Ordinal categories
- Binary variables
- Temporal values
- Time zones
- Text normalization
- Pattern extraction
- Geographic coordinates
- Geographic validation
- Haversine distance
- Identifiers
- Duplicate detection
- Measurement scales
- Categorical encoding
- One-hot encoding
- Ordinal encoding
- Missing-value handling
- Data validation
- Domain validation
- Data profiling
- Metadata
- Measures
- Dimensions
- Dimension hierarchies
- Fact and dimension concepts
- Measure aggregation
- Additive and semi-additive measures
- Cardinality
- Dictionary encoding
- Machine-learning implications
- Temporal feature engineering
- Geographic feature calculations
- Data-quality rules
- Type drift
- Schema concepts
- Security and privacy considerations
- Performance considerations
- Integrated transaction modeling

The examples are intentionally implemented as executable Python rather than being presented solely as theoretical descriptions.

## 102. Central Principle

The most important lesson is that **data type classification is fundamentally about meaning, not merely representation**.

An integer can be:

- A quantity
- A rank
- A code
- An identifier
- A Boolean encoding

A string can be:

- Natural language
- A category
- An identifier
- A date
- A code

A floating-point value can be:

- A physical measurement
- A monetary approximation
- A coordinate
- A percentage
- A calculated statistic

Reliable data analysis therefore requires understanding the semantics of each field before deciding how that field should be stored, transformed, encoded, aggregated, modeled, or interpreted.
