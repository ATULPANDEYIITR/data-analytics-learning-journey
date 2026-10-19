# NumPy Advanced

## Scope

This module focuses on five tightly connected NumPy capabilities: broadcasting, aggregation, reshaping, matrix operations, and random generation. The implementations treat arrays as numerical data structures rather than as ordinary Python lists.

The central idea is that NumPy separates the shape and dtype of numerical data from the Python control flow used to manipulate it. Broadcasting allows compatible arrays with different shapes to participate in element-wise operations. Aggregation reduces dimensions through operations such as `sum`, `mean`, `min`, and `max`. Reshaping changes how existing elements are organized without changing their count. Matrix operations provide linear-algebra semantics through multiplication, inversion, solving, eigenvalue calculations, and covariance transformations. Random generation provides controlled stochastic data for simulation and testing.

The examples use realistic data-processing scenarios such as prices, regional measurements, feature matrices, statistical observations, and portfolio returns.

## Broadcasting

Broadcasting is NumPy's rule for applying element-wise operations to arrays whose shapes are compatible but not identical.

For shapes aligned from the right, two dimensions are compatible when they are equal or when one of them is `1`. Missing leading dimensions are treated as `1`.

For example, the Python implementation contains a price matrix with shape `(3, 3)` and a tax vector with shape `(3,)`. The vector aligns with the final dimension, so each product column receives its corresponding tax rate.

The operation represented by `prices * tax_rates` therefore behaves conceptually like:

`(3, 3) * (3,) -> (3, 3)`

A second example uses a `(3, 1)` regional adjustment against a `(3, 3)` matrix. The singleton dimension expands across the product dimension.

Broadcasting is not arbitrary replication. A shape such as `(3, 4)` cannot be combined element-wise with `(3, 3)` because the trailing dimensions are incompatible. The Python implementation explicitly demonstrates this failure with exception handling.

Broadcasting is especially useful for:

- Applying feature-specific scaling factors to every observation.
- Subtracting feature means from every row of a dataset.
- Applying normalization parameters to batches of measurements.
- Applying tax rates, calibration factors, or weights to structured numerical data.
- Performing tensor operations without manually constructing repeated arrays.

The important performance advantage is that broadcasting expresses the operation without requiring Python-level loops that explicitly construct copies of the repeated data.

## Aggregation and Axis Semantics

Aggregation converts many numerical values into smaller results.

For a matrix shaped `(rows, columns)`, `axis=0` collapses the row dimension and produces one result per column. `axis=1` collapses the column dimension and produces one result per row.

The sales example makes this distinction concrete. A matrix contains monthly values for multiple regions. `sales.sum(axis=0)` produces totals by month, while `sales.sum(axis=1)` produces totals by region.

The same distinction applies to `mean`, `max`, `min`, `std`, and many other reduction functions.

Global aggregation produces a scalar:

`array.sum()`

Feature-wise aggregation produces a vector:

`array.mean(axis=0)`

Row-wise aggregation produces a vector:

`array.mean(axis=1)`

Aggregation becomes particularly useful after broadcasting because feature transformations can be followed by reductions to create compact analytical metrics.

The implementation also demonstrates `argmax` and `argmin`, which identify positions rather than returning the corresponding values directly.

For missing numerical observations, ordinary `mean` and `std` propagate `NaN`. The example therefore uses `nanmean` and `nanstd` when missing values are intentionally present.

## Reshaping

Reshaping changes the dimensions used to interpret an existing sequence of elements.

A 24-element array can become a `(4, 6)` matrix, `(3, 8)` matrix, `(2, 3, 4)` tensor, or another compatible shape whose dimensions multiply to 24.

The key invariant is the element count. Attempting to reshape 24 values into `(5, 5)` fails because that shape requires 25 values.

`reshape` is useful when numerical data changes representation between processing stages. A flat data stream can become a feature matrix, a matrix can become a tensor, and a tensor can be reorganized for a different computation.

`ravel` creates a flattened one-dimensional representation, while `T` provides the conventional two-dimensional transpose.

The example also demonstrates `moveaxis`, which is useful when multidimensional data has a semantic axis in the wrong position. This matters in batch-oriented numerical processing where dimensions may represent samples, channels, rows, or columns.

Memory behavior matters when using reshape operations. NumPy can often provide a view instead of copying the underlying data, but the exact behavior depends on memory layout and the requested transformation. Operations that require incompatible layouts can result in copies.

## Matrix Operations

Element-wise multiplication and matrix multiplication are distinct operations.

For matrices `A` and `B` with compatible shapes:

`A * B`

performs element-wise multiplication, while:

`A @ B`

performs matrix multiplication.

The Python implementation deliberately demonstrates both operations to make the distinction explicit.

The linear-algebra examples include:

- Transposition through `A.T`.
- Determinants through `np.linalg.det`.
- Inversion through `np.linalg.inv`.
- Linear-system solutions through `np.linalg.solve`.
- Eigenvalues and eigenvectors through `np.linalg.eig`.
- Rank through `np.linalg.matrix_rank`.
- Conditioning through `np.linalg.cond`.

Solving a system with `np.linalg.solve(A, b)` is preferable to explicitly calculating `inv(A) @ b` because a direct solver can be numerically and computationally preferable for this task.

The code also handles singular matrices. A matrix with linearly dependent rows or columns may have determinant zero and cannot have an ordinary inverse. Numerical algorithms can also become unstable when a matrix is close to singular, which is why condition number is useful for assessing sensitivity.

## Statistical Matrix Processing

The statistical pipeline treats rows as observations and columns as features.

The generated observations contain different feature means and scales. Feature means are computed with `axis=0`, and standard deviations are also calculated feature-wise.

Standardization is then expressed as:

`(observations - means) / standard_deviations`

This is a direct application of broadcasting. A vector of feature means is automatically applied to every observation row.

The standardized feature matrix is then multiplied by a feature-weight vector using matrix multiplication. This produces a composite score for every observation.

Covariance and correlation matrices expose relationships between features. `np.cov(..., rowvar=False)` treats columns as variables, while `np.corrcoef(..., rowvar=False)` produces normalized correlation coefficients.

This distinction is important because the orientation of a dataset determines how statistical functions interpret observations and variables.

## Masks and Missing Values

Boolean masks provide a vectorized way to select values that satisfy a condition.

The missing-value example creates:

`valid_mask = ~np.isnan(measurements)`

and uses the mask to select valid measurements without iterating through the array manually.

`np.where` then creates a cleaned array by replacing missing values with a computed mean.

The same mechanism can identify potential outliers through a Boolean expression. Boolean indexing returns only the values for which the condition is true.

Masks are therefore useful for:

- Missing-value handling.
- Threshold filtering.
- Conditional transformations.
- Outlier identification.
- Selecting records for downstream aggregation.

A production pipeline should distinguish between genuinely missing data and mathematically invalid values such as positive or negative infinity. The validation example uses `np.isfinite` when finite numerical input is required.

## Tensor Broadcasting

The tensor example uses a shape of `(8, 4, 4)` to represent a batch of eight two-dimensional numerical objects.

A four-element bias vector broadcasts over the final dimension:

`(8, 4, 4) + (4,) -> (8, 4, 4)`

A `(4, 1)` row-scaling array broadcasts over the batch and width dimensions:

`(8, 4, 4) * (4, 1) -> (8, 4, 4)`

The important point is that broadcasting follows shape alignment rules rather than semantic names. The programmer must arrange dimensions so that the intended axes are compatible.

This becomes particularly important in scientific computing, image processing, machine-learning pipelines, simulation, and batch statistical processing.

## Random Generation

Modern NumPy code should generally use an explicit `Generator` created by `np.random.default_rng`.

The examples use:

`rng = np.random.default_rng(42)`

A local generator makes random state easier to reason about and avoids unexpectedly modifying a global random stream.

The script demonstrates:

- Uniform random values.
- Normally distributed values.
- Random integers.
- Random categorical selection.
- Random permutations.
- Reproducible sequences.

The same seed produces the same sequence for the same NumPy generator algorithm, which is valuable for testing and reproducible experiments.

Randomness should not be treated as cryptographic randomness. NumPy's random generators are designed for numerical simulation, statistical sampling, testing, and modeling rather than secrets, passwords, authentication tokens, or cryptographic keys.

## Vectorized Pairwise Distances

The pairwise-distance example demonstrates a more advanced use of broadcasting.

For an array of points with shape `(n, d)`:

`points[:, None, :]`

has shape `(n, 1, d)`, while:

`points[None, :, :]`

has shape `(1, n, d)`.

Subtracting these arrays produces a difference tensor with shape `(n, n, d)`. Summing squared differences along the final dimension and taking the square root produces an `(n, n)` distance matrix.

The diagonal contains zero because each point has zero distance from itself. The example replaces those diagonal values with infinity before searching for nearest neighbors so that a point cannot select itself.

This technique is compact and highly expressive, but it also demonstrates an important limitation: the intermediate difference tensor requires `O(n²d)` storage. For very large datasets, constructing the complete pairwise matrix can become memory-intensive.

## Performance and Vectorization

The performance example compares a vectorized NumPy expression against Python-level iteration over one million values.

The vectorized expression operates on the array as a whole and delegates numerical work to optimized native implementations. The Python comprehension repeatedly crosses the Python interpreter boundary.

The performance benefit depends on the operation, array size, dtype, memory layout, and hardware. Vectorization is not automatically faster for every tiny operation, but large homogeneous numerical workloads are a major strength of NumPy.

A useful design principle is to reduce Python-level loops around numerical arrays when the operation can be represented naturally as a NumPy expression.

At the same time, unnecessary vectorization can create large temporary arrays. Memory usage therefore matters alongside arithmetic throughput.

## Portfolio Risk Case Study

The portfolio example uses a simulated matrix of daily asset returns.

Rows represent trading days and columns represent assets. A portfolio weight vector is multiplied by the return matrix:

`portfolio_returns = daily_returns @ weights`

The covariance matrix is estimated from centered observations. Portfolio variance is then expressed using the quadratic form:

`wᵀΣw`

The square root of annualized variance provides an annualized volatility estimate under the scaling assumptions used by the example.

Historical Value at Risk is approximated from the fifth percentile of the simulated portfolio-return distribution.

The example also compares volatility obtained directly from portfolio returns with volatility calculated from the covariance matrix. Agreement between these two calculations provides a useful numerical consistency check.

This case illustrates how broadcasting, aggregation, centering, covariance, and matrix multiplication combine into a practical numerical workflow.

## Python Implementation

The Python script is the most direct NumPy-focused implementation.

Its broadcasting examples use price matrices, tax vectors, regional adjustments, and tensors. Aggregation examples use sales data and explicit axis choices. Reshaping examples demonstrate matrices and higher-dimensional tensors. Linear algebra examples use determinants, inverses, linear-system solving, eigenvalues, rank, and condition numbers.

The script also includes statistical standardization, masks, missing-value handling, vectorized pairwise distances, seeded random generation, performance comparison, and portfolio risk analysis.

Validation is deliberately included where numerical mistakes would otherwise produce misleading results. Invalid broadcasting, invalid reshapes, non-finite input, singular matrices, and integer overflow are exposed as concrete failure cases.

## JavaScript Implementation

The JavaScript implementation does not attempt to pretend that ordinary JavaScript arrays are NumPy arrays.

Instead, it builds an explicit `NDArray` abstraction backed by `Float64Array`. Shape metadata is stored separately, and operations validate shape compatibility.

The implementation includes:

- Explicit shape validation.
- Matrix construction from nested arrays.
- Reshaping.
- Axis-based sums and means.
- Transposition.
- Broadcasting a one-dimensional vector across matrix rows.
- Matrix multiplication.
- Seeded random generation.
- Box-Muller normal random generation.
- Covariance calculation.
- Portfolio-return calculation.
- An event-driven asynchronous numerical workflow.

The event-driven workflow demonstrates a JavaScript-specific design. Statistics are emitted through events rather than simply printed in a linear script, and asynchronous scheduling uses promises.

JavaScript's `Float64Array` provides a more appropriate numerical storage representation than heterogeneous ordinary arrays when large quantities of floating-point data are processed.

## C++ Case Study

The C++ program models a numerical analytics system using a strongly typed `Matrix` class.

The matrix stores values in a contiguous `std::vector<double>`. This provides predictable ownership and compact numerical storage while allowing the class to enforce dimensional invariants.

The class supports matrix multiplication, transposition, row and column aggregation, and explicit row-vector broadcasting. The latter models the same shape behavior as applying a feature vector to every row of a NumPy matrix.

The case study uses repository-performance metrics as a numerical dataset. Feature adjustment demonstrates broadcasting semantics, covariance demonstrates statistical aggregation, and a projection matrix demonstrates linear transformation.

The program also generates normally distributed observations using the C++ standard library's random facilities. A fixed seed makes the simulation reproducible.

The dedicated 2×2 linear-algebra functions demonstrate determinant and inverse calculations while explicitly rejecting numerically singular matrices.

The multiplication algorithm uses the shared dimension as the middle loop:

`C[i][j] += A[i][k] * B[k][j]`

For an `m × n` matrix multiplied by an `n × p` matrix, the arithmetic complexity is `O(mnp)`.

## Java Implementation

The Java program models numerical processing through immutable-style records and an `AnalyticsService`.

The `Matrix` record validates its shape and stores a defensive copy of supplied rows. Broadcasting is represented explicitly by `addBroadcast` and `multiplyBroadcast`, since Java's standard collections do not provide NumPy's implicit broadcasting semantics.

The enterprise model uses `RepositoryMetrics` as a domain record with feature values for commits, reviews, failure rate, and delivery score. These records are converted into a matrix for numerical analysis.

The service performs feature-wise standardization, deterministic random normal generation, weighted transformations, aggregation, and matrix projection.

Java's enum `Metric` gives the feature positions explicit domain meaning rather than treating every numerical column as anonymous data.

The program also demonstrates explicit exception handling for incompatible matrix multiplication and singular matrix inversion.

## PostgreSQL Data Model

The SQL implementation stores numerical observations as PostgreSQL `DOUBLE PRECISION[]` arrays.

The `datasets` table identifies an analytical dataset and records its expected shape. `features` gives each array position a semantic feature name. `observations` stores each row as an array, preserving the relationship between a matrix row and its feature vector.

`feature_weights` represents a numerical weight vector, while `matrix_operations` and `matrix_results` provide an audit trail for numerical transformations.

The schema uses:

- Primary keys to identify numerical entities.
- Foreign keys to maintain dataset relationships.
- Unique constraints for feature positions and observation positions.
- Check constraints to prevent empty numerical vectors and invalid dimensions.
- Indexes for dataset and operation lookups.
- Transactions for atomic operation and result persistence.

PostgreSQL's `generate_subscripts` exposes individual array positions relationally. This allows feature-wise aggregation, broadcasting-style transformations, standardization, and matrix multiplication to be expressed through SQL.

## SQL Representation of Broadcasting

The SQL broadcast example joins each observation vector with a four-element adjustment vector and multiplies corresponding positions.

This is conceptually equivalent to applying a feature vector across every matrix row.

The SQL implementation does not assume that array operations automatically have all of NumPy's broadcasting semantics. It explicitly iterates through compatible positions using `generate_subscripts`.

This makes shape compatibility visible in the relational implementation and avoids silently applying a mathematically incorrect transformation.

## SQL Representation of Matrix Multiplication

Matrix multiplication is represented through a relational join on the shared matrix dimension.

For matrices `A` and `B`, each output element is calculated from the sum of products of corresponding values along the shared dimension.

The SQL query groups those products by output row and output column before assembling the resulting vector with `array_agg`.

This representation demonstrates that matrix multiplication is fundamentally an aggregation over a shared dimension, not merely an arbitrary nested loop.

## Reshaping and Array Semantics in SQL

The SQL script demonstrates reshaping by converting a linear sequence into calculated row and column positions.

The row position is derived using integer division, while the column position is derived using the remainder operation. The values are then grouped into ordered arrays.

This is useful when a database stores flat numerical measurements but downstream processing expects explicit matrix dimensions.

A database representation should still preserve the semantic shape explicitly rather than relying only on array length. The `datasets` table therefore records row and column counts separately.

## Random Numerical Data

Random generation is included for simulation rather than security.

PostgreSQL's `random()` produces uniform values. The SQL script uses a Box-Muller-style expression to derive an approximate normal distribution from uniform samples.

The Python implementation instead uses NumPy's `Generator`, while the C++ and Java implementations use their respective standard-library random facilities. These are deliberately different implementations of the same numerical requirement.

None of these mechanisms should be used for cryptographic secrets.

## Edge Cases and Failure Conditions

Several failure modes are represented explicitly.

Broadcasting fails when trailing dimensions are incompatible. Reshaping fails when the requested shape contains a different number of elements. Matrix multiplication fails when inner dimensions do not match. Singular matrices cannot be inverted reliably.

Numerical data can also contain `NaN` or infinity. The Python implementation validates finite input where required and uses NaN-aware aggregation when missing values are intentional.

Integer dtype selection matters because narrow integer types can overflow. The Python example converts an `int8` array to `int64` before arithmetic when a larger range is required.

Statistical standardization can fail when a feature has zero variance because division by its standard deviation is undefined.

Pairwise distance matrices present a different issue: even when the arithmetic is correct, `O(n²)` storage can become impractical for large datasets.

## Performance Considerations

Broadcasting generally avoids explicitly constructing repeated copies of data, although operations can still create temporary arrays.

Aggregation over a contiguous numerical array is typically efficient because NumPy can execute the numerical loop in optimized native code.

Matrix multiplication is computationally expensive for large matrices, with the basic dense multiplication algorithm requiring cubic work for square matrices. NumPy's linear-algebra operations can use optimized underlying implementations where available.

Memory traffic can become as important as arithmetic. A mathematically simple expression involving several intermediate arrays may consume substantial memory. Large-scale numerical programs therefore need to consider array size, dtype, temporary allocations, and memory layout.

The C++ case study stores matrix values contiguously in a `std::vector<double>`, while the Java and JavaScript implementations make their storage decisions explicit because those languages do not provide NumPy's native multidimensional array model.

## Practical Distinctions

| Operation | Main purpose | Typical NumPy form |
| --- | --- | --- |
| Broadcasting | Align compatible shapes for element-wise operations | `A + vector` |
| Aggregation | Reduce values along an axis | `A.mean(axis=0)` |
| Reshaping | Change dimensional interpretation | `A.reshape(...)` |
| Matrix multiplication | Linear transformation and algebra | `A @ B` |
| Random generation | Simulation and stochastic sampling | `rng.normal(...)` |

These operations frequently appear together. A numerical pipeline may generate observations, reshape them into a feature matrix, broadcast feature-specific normalization parameters, aggregate statistics by axis, and finally multiply the resulting matrix by a transformation or weight matrix.

The operations remain conceptually distinct even when they are chained in one expression.

## Common Mistakes

Confusing `*` with `@` is one of the most important errors in NumPy matrix work. `*` is element-wise multiplication, while `@` represents matrix multiplication.

Another common mistake is misunderstanding `axis`. The axis identifies the dimension being reduced, so the resulting shape depends directly on which dimension is removed.

Broadcasting can also produce mathematically valid but semantically incorrect results. A shape-compatible operation is not automatically a logically correct operation. Feature order and feature meaning must be validated before applying a broadcast vector.

Explicitly calculating a matrix inverse when the real requirement is to solve `Ax=b` can introduce unnecessary numerical work. `np.linalg.solve` is usually the more appropriate abstraction for linear-system solving.

Using global random state can make experiments difficult to reproduce when unrelated code also consumes random values. A local `Generator` provides cleaner control.

## Production Considerations

Production numerical pipelines should validate shapes, dtypes, finiteness, feature ordering, missing-value policy, and expected numerical ranges before applying transformations.

Shape validation is especially important when broadcasting because an accidental shape can produce a result that is syntactically valid but semantically wrong.

Random simulations should record their seed or generator configuration when reproducibility matters.

Numerical algorithms should also consider floating-point precision, matrix conditioning, overflow, underflow, cancellation, and the stability of the selected algorithm.

For large datasets, memory consumption should be measured rather than inferred from the apparent simplicity of an expression. Vectorization improves numerical execution but does not eliminate the cost of allocating large intermediate arrays.

The database implementation shows a complementary principle: structural integrity can be enforced at the data layer through constraints, while numerical transformations can be recorded transactionally for traceability.
