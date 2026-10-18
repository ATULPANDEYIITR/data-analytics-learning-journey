# NumPy Fundamentals

## Scope

This material focuses on the core NumPy model for numerical arrays: array construction, dimensions, shape, data types, indexing, slicing, vectorization, broadcasting, Boolean selection, reductions, reshaping, numerical validation, and matrix operations.

The four central properties of a NumPy array are closely connected:

- **Dimensions (`ndim`)** describe how many axes the array has.
- **Shape (`shape`)** describes the length of every axis.
- **Data type (`dtype`)** describes how each stored element is represented.
- **Storage size (`size` and `nbytes`)** describes how many elements exist and how much memory the representation consumes.

These properties determine which indexing operations are valid, how reshaping works, how broadcasting behaves, and which numerical operations can be performed efficiently.

## Array Structure

A NumPy array can represent a scalar, vector, matrix, or higher-dimensional tensor.

The Python implementation creates examples of each:

- A zero-dimensional array contains one scalar value and has an empty shape.
- A one-dimensional array has a shape such as `(4,)`.
- A two-dimensional matrix has a shape such as `(3, 4)`.
- A three-dimensional array can have a shape such as `(2, 3, 4)`.

The distinction between shape and dimension is important. A `(3, 4)` array has two dimensions, while the individual axis lengths are three and four.

`size` is the total number of elements. For a `(3, 4)` array, `size` is twelve.

`itemsize` describes the number of bytes used for each element. `nbytes` is the total storage occupied by the array data.

## Data Types

NumPy does not treat every numerical value as an arbitrary Python object. A homogeneous array normally stores values according to one NumPy data type.

The Python implementation explicitly demonstrates `int32` and `float64`.

This matters because dtype affects:

- Memory consumption.
- Numerical range.
- Precision.
- Arithmetic behavior.
- Compatibility with numerical and scientific routines.

Explicit conversion with `astype()` is useful when a computation requires a known representation. Accidental dtype changes can cause unexpected memory usage or precision behavior, so numerical pipelines should establish their expected dtypes deliberately.

An array containing mixed numeric Python values can undergo dtype promotion. For example, combining integers and floating-point values normally produces a floating-point array.

## Construction and Shape

The Python implementation demonstrates `zeros`, `ones`, `full`, `arange`, and `linspace`.

These constructors have different purposes:

- `zeros` creates a known numerical baseline.
- `ones` creates an array initialized to one.
- `full` fills every position with a selected value.
- `arange` creates values over an arithmetic sequence.
- `linspace` creates a specified number of evenly spaced values.

`reshape()` changes the interpretation of the same element sequence without changing the number of elements. A twelve-element array can become `(3, 4)` or `(2, 2, 3)`, but it cannot become `(5, 3)` because that would require fifteen elements.

The Java and C++ implementations make this invariant explicit through their `Shape` and `Matrix` abstractions.

## Indexing

NumPy uses zero-based indexing.

For a two-dimensional array, an expression such as `array[row, column]` identifies one scalar. Negative indices address elements from the end.

The Python implementation uses:

`array[0, 0]`

for the first element and:

`array[-1, -1]`

for the last element.

Axis-specific indexing is especially important for data analysis. `array[0]` selects the first row, while `array[:, 1]` selects the second column.

The colon represents an entire axis. This is one of the main differences between treating a NumPy matrix as structured multidimensional data and treating it as a nested collection of independent lists.

## Slicing

Slicing selects a range without manually iterating over individual elements.

The Python implementation demonstrates:

- First rows with `array[:2]`.
- Last columns with `array[:, -2:]`.
- Every second column with `array[:, ::2]`.
- Reversed rows with `array[::-1]`.

A significant implementation detail is that ordinary NumPy slices commonly produce **views** rather than independent copies. The Python example modifies a sliced row and shows that the source array changes.

When independent storage is required, `.copy()` should be used.

This distinction is important in production systems because an apparently local mutation can otherwise modify a larger data structure unexpectedly.

## Reshaping and Transposition

`reshape()` changes an array's shape while preserving its element count.

`ravel()` produces a flattened representation and can return a view when the memory layout permits it. `flatten()` creates an independent copy.

The transpose operation changes axis order. For a two-dimensional matrix, `matrix.T` exchanges rows and columns.

Higher-dimensional applications require more explicit reasoning about axes because transposition is not simply a universal row-column swap once an array contains more than two dimensions.

## Vectorization

Vectorization is a central NumPy technique.

The Python implementation converts Celsius temperatures to Fahrenheit with:

`temperatures_c * 9 / 5 + 32`

The arithmetic is applied element-wise to the complete array without writing a Python loop.

The same mechanism is used for prices, quantities, discounts, and normalized measurements.

Vectorization is not merely shorter syntax. NumPy can perform the underlying operations through optimized numerical routines over contiguous or appropriately structured array memory, reducing Python-level iteration overhead.

The C++ case study demonstrates the underlying mathematical operations explicitly, while the JavaScript version models typed numeric storage and element-wise transformations without claiming the same execution model as NumPy.

## Broadcasting

Broadcasting allows arrays with compatible shapes to participate in element-wise operations without manually copying values.

A `(3, 3)` matrix and a `(3,)` vector are compatible because the vector aligns with the matrix's final dimension.

The Python sales example divides three columns by three corresponding target values. The target vector is logically reused across every row.

Broadcasting is governed by shape compatibility rather than by arbitrary automatic repetition. If dimensions conflict, NumPy raises a `ValueError`.

The implementation intentionally demonstrates an incompatible operation so that broadcasting failure is treated as part of the concept rather than hidden.

## Boolean Indexing

Boolean indexing uses a Boolean array as a selection mask.

For example:

`temperatures_c[comfort_mask]`

returns only temperatures for which the mask contains `True`.

The score examples use conditions such as:

`scores[scores >= 70]`

and:

`scores[scores >= 90]`

This provides compact filtering for numerical datasets.

Boolean conditions involving multiple comparisons require NumPy's element-wise logical operators such as `&` and `|`. Python's scalar `and` and `or` operators should not be substituted for array-wide Boolean expressions.

## Reductions and Axes

Reduction operations convert many elements into fewer results.

The Python implementation demonstrates:

- `sum()`
- `mean()`
- `min()`
- `max()`
- `median()`
- `std()`

The `axis` argument controls which dimension is reduced.

For a `(3, 4)` matrix:

- `sum(axis=0)` produces four values, one for each column.
- `sum(axis=1)` produces three values, one for each row.
- `sum()` without an axis reduces the entire array to one value.

Understanding axis semantics is essential for data analysis because an incorrect axis can produce a result that is numerically valid but conceptually wrong.

The SQL implementation represents similar reductions using `GROUP BY row_index` and `GROUP BY column_index`.

## Advanced Indexing

The Python implementation uses arrays of row and column indices to select paired elements:

`matrix[selected_rows, selected_columns]`

This differs from ordinary rectangular slicing. The selected row and column arrays identify corresponding coordinates.

Boolean indexing is also demonstrated for extracting all values above a threshold.

Advanced indexing generally produces a new array rather than behaving like a basic slice view. This distinction should be considered when modifying selected data and when working with large arrays.

## Missing and Invalid Numerical Values

The Python implementation explicitly checks for `NaN` with `np.isnan()` and uses `np.nanmean()` when a statistical calculation should ignore missing floating-point values.

Production numerical validation should also consider infinity. The validation function uses `np.isfinite()` to reject both `NaN` and infinite values.

This is distinct from ordinary shape validation. A matrix can have the correct dimensions and still contain invalid numerical values.

The SQL implementation demonstrates a database-oriented equivalent by applying validation rules to stored numeric elements.

## Matrix Operations

The Python implementation uses the `@` operator for matrix multiplication.

The demand example represents each observation as a feature row and multiplies it by a coefficient vector. The resulting values are predictions derived from the matrix operation.

This differs from element-wise multiplication:

- `A * B` performs element-wise multiplication.
- `A @ B` performs matrix multiplication.

The C++ implementation makes the matrix multiplication algorithm explicit with three nested loops. For an `m × k` matrix multiplied by a `k × n` matrix, the direct algorithm has `O(mkn)` arithmetic complexity.

The C++ example also calculates a two-by-two determinant and discusses floating-point comparison using a tolerance.

## Python Implementation

The Python script is organized around executable demonstrations rather than a language tutorial.

The fundamental portion creates scalar, vector, matrix, and tensor arrays and inspects `shape`, `ndim`, `dtype`, `size`, `itemsize`, and `nbytes`.

The indexing section demonstrates scalar access, row selection, column selection, strided slices, views, and independent copies.

The reshaping section shows shape preservation, flattening behavior, column vectors, row vectors, and transposition.

The vectorization section applies numerical formulas to entire arrays. The broadcasting section uses a sales matrix and target vector to demonstrate compatible and incompatible shapes.

Boolean filtering and reductions demonstrate numerical selection and axis-specific aggregation. The validation section rejects non-two-dimensional data, nonnumeric values, `NaN`, and infinity.

The file-handling example uses NumPy's `.npy` format to persist and restore an array. The linear algebra example uses `@` and `np.linalg.solve()` for a small numerical model.

The final sections intentionally demonstrate common failures, including invalid indexing, impossible reshaping, incompatible broadcasting, and object dtype.

## JavaScript Implementation

JavaScript does not provide NumPy's ndarray abstraction in its standard library. The implementation therefore uses `Float64Array` for typed numerical storage and defines `NumericMatrix` to make shape and row-major indexing explicit.

The matrix stores its data in one-dimensional contiguous typed storage. A coordinate `(row, column)` maps to:

`row * columns + column`

This makes the relationship between multidimensional shape and linear memory concrete.

`BroadcastVector` provides an explicit model of broadcasting across a matrix's final dimension. Shape validation rejects incompatible vector lengths.

The JavaScript file also demonstrates matrix multiplication, Boolean-style filtering with standard array operations, `EventTarget` processing, and an asynchronous numerical pipeline.

These mechanisms complement the Python implementation by showing how JavaScript can model numerical array behavior through typed storage, classes, events, and asynchronous execution rather than attempting to reproduce NumPy's API.

## C++ Case Study

The C++ implementation models a numerical matrix used by a demand-prediction system.

`Matrix` owns a contiguous `std::vector<double>` and stores its dimensions separately. Coordinate access validates bounds before converting a two-dimensional coordinate into a linear offset.

The class implements element-wise addition, element-wise multiplication, scalar multiplication, transposition, summation, mean calculation, and maximum extraction.

The demand case study separates a feature matrix from a coefficient matrix and performs matrix multiplication through an explicit dot-product algorithm.

Boolean thresholding is represented with a mask, while shape validation rejects invalid matrix multiplication and incorrectly sized construction.

The case study also addresses numerical stability through determinant evaluation and tolerance-based floating-point comparison.

## Java Enterprise Model

The Java implementation models a numerical data service using explicit domain abstractions.

`Shape` is a Java record representing matrix dimensions. Its compact constructor enforces positive dimensions, while `NumericGrid` owns a defensive copy of its numerical storage.

The defensive copy prevents callers from modifying the internal array after construction, which is an important design decision when mutable arrays cross service boundaries.

`NumericPolicy` separates validation rules from the numerical data structure. `FiniteValuePolicy` enforces finite numerical values, while `ThresholdPolicy` represents a domain rule requiring values to meet a minimum.

`NumericService` registers policies and applies them to grids. This makes validation behavior explicit rather than embedding every business rule directly inside matrix operations.

The enterprise prediction example uses matrix multiplication to transform feature observations into predictions. Failure handling demonstrates incompatible dimensions, invalid indexes, and incorrect element counts.

## SQL Data Model

The PostgreSQL implementation represents multidimensional numerical data relationally.

`array_dataset` stores array metadata such as dimensionality, dtype, row count, and column count.

`array_element` stores individual coordinates and values. Foreign keys connect elements to their parent arrays, while a trigger validates that coordinates agree with the declared dimensionality.

`transformation` records operations such as slicing, vectorization, broadcasting, filtering, normalization, and transposition. This turns numerical transformations into auditable database records.

`validation_rule` and `validation_result` represent explicit data-quality rules and their outcomes.

The schema contains indexes on array coordinates, numeric values, and transformation history. The coordinate index supports reconstruction and inspection of matrix elements, while the numeric partial index supports value-based filtering.

## SQL Representations of Array Operations

The student-score queries use `row_index` and `column_index` to reconstruct matrix-oriented views.

A threshold query corresponds to Boolean filtering by selecting elements whose numeric value meets a condition.

Row-wise reductions use `GROUP BY row_index`, while column-wise reductions use `GROUP BY column_index`.

The temperature query applies the Celsius-to-Fahrenheit formula directly to every stored value, demonstrating a relational form of element-wise vectorization.

The sales query joins each matrix column with a three-element target vector. This represents broadcasting as an explicit relational alignment rather than implicit array shape rules.

The normalization query first calculates row maxima through a CTE and then divides each element by its corresponding maximum.

## Relationships Between the Core Concepts

These concepts are distinct but strongly connected.

| Concept | Specific role |
| --- | --- |
| Array dimensions | Describe how many axes the data has. |
| Shape | Gives the size of every axis and determines valid structural operations. |
| dtype | Defines the representation of each stored element. |
| Indexing | Retrieves particular coordinates from an array. |
| Slicing | Selects structured ranges or regions of an array. |
| Vectorization | Applies numerical operations to arrays without explicit Python-level iteration. |
| Broadcasting | Allows compatible differently shaped arrays to participate in element-wise operations. |

Shape is the structural foundation for indexing and broadcasting. dtype controls how the resulting elements are represented. Vectorization operates over that structured data, while Boolean indexing uses computed conditions to select subsets.

A shape error is therefore not merely an indexing problem. It can also prevent broadcasting or matrix multiplication. A dtype issue can alter precision or memory usage even when shape operations are completely correct.

## Views, Copies, and Memory

A major practical NumPy distinction is the difference between a view and a copy.

Basic slicing can produce a view into existing storage. Modifying the view can therefore modify the source array.

`copy()` creates independent storage.

This matters for both correctness and performance. Views can avoid unnecessary memory allocation, which is valuable for large datasets, but they also require developers to understand ownership and mutation behavior.

`ravel()` may return a view when possible, while `flatten()` explicitly creates a copy.

The C++ and Java implementations approach this issue differently. C++ owns its vector storage directly, while the Java implementation uses defensive copies at construction to provide stronger encapsulation.

## Performance Considerations

NumPy's main performance advantage is not simply that its syntax is compact. Numerical arrays have a known dtype and structured memory representation, allowing operations to run through optimized native implementations.

Repeated Python-level loops can become expensive for large numerical workloads. Vectorized expressions generally reduce that interpreter overhead.

Memory usage also matters. A large `float64` array requires eight bytes per element before considering other application-level structures.

Unnecessary copies can become expensive. A pipeline that repeatedly creates full-size arrays may consume significantly more memory than one that uses views or carefully structured operations.

Broadcasting can reduce the need to materialize repeated data, but developers should still understand the resulting operation and its memory behavior.

## Common Mistakes

### Confusing `*` with `@`

For NumPy matrices, `*` performs element-wise multiplication, while `@` performs matrix multiplication.

Using the wrong operator can produce a valid-looking numerical result with completely different mathematical meaning.

### Misunderstanding `axis`

`axis=0` and `axis=1` describe dimensions being reduced, not arbitrary labels such as "rows" or "columns" in every possible operation. The resulting shape should always be checked.

### Ignoring dtype

A numerically correct algorithm can still have inappropriate precision or memory consumption if dtype is chosen accidentally.

### Mutating a slice

A slice can be a view. Code that expects an independent object should use `.copy()`.

### Assuming broadcasting always works

Broadcasting requires compatible dimensions. Incompatible shapes produce an error rather than arbitrary repetition.

### Treating NaN as an ordinary number

`NaN` has special comparison behavior. Numerical validation and aggregation should explicitly decide whether missing values are allowed and whether functions such as `nanmean` are appropriate.

### Confusing shape with size

A `(2, 3)` array has size six and two dimensions. Shape and total element count answer different questions.

## Production Considerations

Numerical systems should validate both structure and values.

Shape validation prevents invalid matrix operations. dtype validation prevents unintended representation changes. Finite-value checks prevent `NaN` and infinity from silently entering calculations where they are not meaningful.

For external or user-supplied numerical data, validation should occur before expensive computation.

Large arrays should be handled with attention to memory allocation, copying, and temporary intermediate results. Vectorization should be preferred when it expresses the mathematical operation clearly, but code should still be profiled when performance is important.

For persistent systems, the SQL example shows how structural and quality constraints can be enforced at the database layer rather than trusting only application code.

The different implementations illustrate the same numerical ideas through different architectural models: NumPy provides the specialized multidimensional array abstraction, JavaScript uses typed arrays and explicit shape management, C++ exposes contiguous storage and algorithmic mechanics, Java emphasizes domain types and validation policies, and PostgreSQL represents array structure and transformations through relational integrity.
