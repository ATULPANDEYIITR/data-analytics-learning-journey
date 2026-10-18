import numpy as np


def print_array_details(name, array):
    """Display the structural properties that make a NumPy array useful."""
    print(f"\n{name}")
    print(f"values:\n{array}")
    print(f"shape={array.shape}, ndim={array.ndim}, dtype={array.dtype}, size={array.size}")
    print(f"itemsize={array.itemsize} bytes, nbytes={array.nbytes} bytes")


def fundamentals():
    print("=== NumPy array fundamentals ===")

    scalar_array = np.array(42)
    vector = np.array([10, 20, 30, 40])
    matrix = np.array([[1, 2, 3], [4, 5, 6]])
    tensor = np.arange(24).reshape(2, 3, 4)

    print_array_details("0-D scalar", scalar_array)
    print_array_details("1-D vector", vector)
    print_array_details("2-D matrix", matrix)
    print_array_details("3-D tensor", tensor)

    integer_array = np.array([1, 2, 3], dtype=np.int32)
    floating_array = np.array([1, 2, 3], dtype=np.float64)

    print("\nExplicit dtype control:")
    print(integer_array, integer_array.dtype)
    print(floating_array, floating_array.dtype)

    zeros = np.zeros((2, 3), dtype=np.float64)
    ones = np.ones((2, 3), dtype=np.int32)
    filled = np.full((2, 3), 7)
    sequence = np.arange(0, 12, 2)
    evenly_spaced = np.linspace(0.0, 1.0, 5)

    print("\nArray construction:")
    print("zeros:\n", zeros)
    print("ones:\n", ones)
    print("full:\n", filled)
    print("arange:", sequence)
    print("linspace:", evenly_spaced)


def indexing_and_slicing():
    print("\n=== Indexing and slicing ===")

    scores = np.array(
        [
            [82, 91, 77, 88],
            [95, 84, 90, 73],
            [68, 79, 85, 92],
        ]
    )

    print("Scores:\n", scores)

    print("\nScalar indexing:")
    print("first student, first subject:", scores[0, 0])
    print("last student, last subject:", scores[-1, -1])

    print("\nRow and column selection:")
    print("first row:", scores[0])
    print("second column:", scores[:, 1])
    print("last two columns:\n", scores[:, -2:])
    print("first two rows:\n", scores[:2])

    print("\nStrided slicing:")
    print("every second column:\n", scores[:, ::2])
    print("reverse rows:\n", scores[::-1])

    # Basic slices usually return views. Mutating a slice can therefore mutate
    # the original array, which is an important distinction from Python lists.
    working = scores.copy()
    first_row_view = working[0, :]
    first_row_view[0] = 100
    print("\nAfter modifying a row view:")
    print(working)

    # copy() creates independent storage when modification must not affect source.
    independent = scores[:, :2].copy()
    independent[0, 0] = -1
    print("\nIndependent copy:")
    print(independent)
    print("Original remains unchanged:\n", scores)


def reshaping_and_dimensions():
    print("\n=== Shape, dimensions, and reshaping ===")

    data = np.arange(1, 13)
    matrix = data.reshape(3, 4)
    cube = data.reshape(2, 2, 3)

    print("Original:", data)
    print("3 x 4:\n", matrix)
    print("2 x 2 x 3:\n", cube)

    # reshape preserves element count. A 3x4 array cannot become a 5x3 array.
    try:
        matrix.reshape(5, 3)
    except ValueError as exc:
        print("\nInvalid reshape rejected:", exc)

    flattened = matrix.ravel()
    flattened_copy = matrix.flatten()

    print("\nravel:", flattened)
    print("flatten:", flattened_copy)

    column_vector = data[:, np.newaxis]
    row_vector = data[np.newaxis, :]

    print("\nColumn vector shape:", column_vector.shape)
    print("Row vector shape:", row_vector.shape)

    transposed = matrix.T
    print("\nTranspose:\n", transposed)


def dtype_and_numeric_behavior():
    print("\n=== dtype and numeric behavior ===")

    values = np.array([1, 2, 3], dtype=np.int16)
    converted = values.astype(np.float64)
    booleans = np.array([True, False, True, True])

    print("int16:", values, values.dtype)
    print("float64:", converted, converted.dtype)
    print("boolean array:", booleans)

    # NumPy arithmetic follows the array dtype rules. Explicit conversion is
    # safer when calculations require a particular numeric precision.
    large_values = np.array([300, 400], dtype=np.int16)
    print("large int16 values:", large_values)

    mixed = np.array([1, 2.5, 3])
    print("Mixed numeric input promotes dtype:", mixed, mixed.dtype)

    try:
        np.array([1, 2, 3], dtype=np.uint8).astype(np.int8)
        print("Explicit integer conversion completed.")
    except (OverflowError, ValueError) as exc:
        print("Conversion failed:", exc)


def vectorization():
    print("\n=== Vectorization ===")

    temperatures_c = np.array([18.5, 21.0, 24.5, 27.0, 30.0])

    # The expression operates element-by-element without an explicit Python loop.
    temperatures_f = temperatures_c * 9 / 5 + 32
    comfort_mask = (temperatures_c >= 20) & (temperatures_c <= 26)

    print("Celsius:", temperatures_c)
    print("Fahrenheit:", temperatures_f)
    print("Comfort mask:", comfort_mask)
    print("Comfortable temperatures:", temperatures_c[comfort_mask])

    prices = np.array([120.0, 80.0, 250.0, 45.0])
    quantities = np.array([2, 5, 1, 10])

    totals = prices * quantities
    discounted_totals = np.where(prices >= 100, totals * 0.90, totals)

    print("\nPrices:", prices)
    print("Quantities:", quantities)
    print("Totals:", totals)
    print("Discounted totals:", discounted_totals)


def broadcasting():
    print("\n=== Broadcasting ===")

    monthly_sales = np.array(
        [
            [120, 150, 180],
            [90, 110, 140],
            [200, 220, 250],
        ],
        dtype=np.float64,
    )

    monthly_targets = np.array([100, 120, 160], dtype=np.float64)

    # A (3,) array aligns with the final dimension of a (3,3) matrix.
    achievement_ratio = monthly_sales / monthly_targets

    print("Sales:\n", monthly_sales)
    print("Targets:", monthly_targets)
    print("Achievement ratios:\n", achievement_ratio)

    # A (3,1) column broadcasts across columns, allowing row-specific adjustment.
    regional_adjustment = np.array([[1.05], [0.98], [1.10]])
    adjusted_sales = monthly_sales * regional_adjustment

    print("\nAdjusted sales:\n", adjusted_sales)

    incompatible = np.ones((2, 3))
    other = np.ones((2, 2))
    try:
        incompatible + other
    except ValueError as exc:
        print("\nBroadcasting failure:", exc)


def boolean_filtering_and_statistics():
    print("\n=== Boolean filtering and statistics ===")

    scores = np.array([61, 74, 88, 92, 55, 79, 96, 83, 67])

    passing = scores[scores >= 70]
    distinction = scores[scores >= 90]

    print("Scores:", scores)
    print("Passing:", passing)
    print("Distinction:", distinction)
    print("Mean:", scores.mean())
    print("Median:", np.median(scores))
    print("Minimum:", scores.min())
    print("Maximum:", scores.max())
    print("Standard deviation:", scores.std())

    print("\nIndices of scores above 85:", np.where(scores > 85)[0])

    row_maximums = np.array(
        [
            [3, 9, 4],
            [8, 2, 7],
            [6, 5, 1],
        ]
    )

    print("Row maxima:", row_maximums.max(axis=1))
    print("Column minima:", row_maximums.min(axis=0))


def advanced_indexing():
    print("\n=== Advanced indexing ===")

    matrix = np.arange(1, 17).reshape(4, 4)

    selected_rows = np.array([0, 2, 3])
    selected_columns = np.array([3, 1, 0])

    print("Matrix:\n", matrix)
    print("Selected rows:\n", matrix[selected_rows])
    print(
        "Paired indexed elements:",
        matrix[selected_rows, selected_columns],
    )

    # Boolean indexing selects values according to a condition and returns
    # a new array containing the selected elements.
    high_values = matrix[matrix > 10]
    print("Values greater than 10:", high_values)


def reductions_and_axis_reasoning():
    print("\n=== Reductions and axis semantics ===")

    transactions = np.array(
        [
            [120, 150, 180, 90],
            [100, 130, 160, 110],
            [80, 140, 170, 125],
        ],
        dtype=np.float64,
    )

    print("Transactions:\n", transactions)

    # axis=0 reduces rows, producing one value for each column.
    print("Column totals:", transactions.sum(axis=0))

    # axis=1 reduces columns, producing one value for each row.
    print("Row totals:", transactions.sum(axis=1))

    print("Column means:", transactions.mean(axis=0))
    print("Row means:", transactions.mean(axis=1))

    print("Global total:", transactions.sum())


def missing_values_and_validation():
    print("\n=== Missing values and validation ===")

    measurements = np.array([10.5, 11.2, np.nan, 12.7, np.nan, 13.1])

    valid_mask = ~np.isnan(measurements)
    valid_values = measurements[valid_mask]

    print("Measurements:", measurements)
    print("Valid mask:", valid_mask)
    print("Valid measurements:", valid_values)
    print("NaN count:", np.isnan(measurements).sum())
    print("Mean ignoring NaN:", np.nanmean(measurements))

    def validate_numeric_matrix(value):
        array = np.asarray(value)

        if array.ndim != 2:
            raise ValueError("Expected a two-dimensional numeric matrix.")
        if not np.issubdtype(array.dtype, np.number):
            raise TypeError("Matrix must contain numeric values.")
        if not np.isfinite(array).all():
            raise ValueError("Matrix contains NaN or infinite values.")

        return array

    valid = validate_numeric_matrix([[1, 2], [3, 4]])
    print("Validated matrix:\n", valid)

    try:
        validate_numeric_matrix([[1, np.inf]])
    except ValueError as exc:
        print("Validation failure:", exc)


def file_round_trip():
    print("\n=== NumPy binary file handling ===")

    data = np.arange(12, dtype=np.float64).reshape(3, 4)
    path = "numpy_demo_data.npy"

    np.save(path, data)
    restored = np.load(path)

    print("Saved array:\n", data)
    print("Restored array:\n", restored)
    print("Round-trip identical:", np.array_equal(data, restored))

    try:
        import os
        os.remove(path)
    except OSError as exc:
        print("Temporary file cleanup warning:", exc)


def linear_algebra_case_study():
    print("\n=== Linear algebra case study ===")

    # A small production-style example: compute the predicted demand from
    # feature measurements and a learned coefficient vector.
    features = np.array(
        [
            [1.0, 20.0, 4.0],
            [1.0, 30.0, 6.0],
            [1.0, 40.0, 8.0],
        ]
    )
    coefficients = np.array([15.0, 2.5, 5.0])

    predictions = features @ coefficients

    print("Feature matrix:\n", features)
    print("Coefficients:", coefficients)
    print("Predictions:", predictions)

    covariance = np.cov(features[:, 1:].T)
    print("Feature covariance matrix:\n", covariance)

    matrix = np.array([[4.0, 1.0], [2.0, 3.0]])
    vector = np.array([10.0, 14.0])

    solution = np.linalg.solve(matrix, vector)

    print("\nLinear system solution:", solution)
    print("Verification:", matrix @ solution)

    determinant = np.linalg.det(matrix)
    print("Determinant:", determinant)

    if abs(determinant) < 1e-12:
        print("Matrix is numerically singular.")
    else:
        print("Matrix has a usable inverse for this example.")


def performance_comparison():
    print("\n=== Vectorization and performance considerations ===")

    values = np.arange(1_000_000, dtype=np.float64)

    # The vectorized expression executes the arithmetic through NumPy's
    # optimized array operations rather than repeatedly invoking Python code.
    vectorized_result = values * values + 2 * values + 1

    # A loop is retained only as a conceptual comparison. It uses Python
    # scalar operations and therefore generally scales less efficiently.
    sample = values[:10]
    loop_result = [x * x + 2 * x + 1 for x in sample]

    print("Vectorized result sample:", vectorized_result[:10])
    print("Equivalent loop result:", loop_result)

    print(
        "Vectorized result dtype:",
        vectorized_result.dtype,
        "shape:",
        vectorized_result.shape,
    )


def common_failure_cases():
    print("\n=== Common NumPy failure cases ===")

    array = np.arange(12).reshape(3, 4)

    try:
        print(array[3, 0])
    except IndexError as exc:
        print("Index error:", exc)

    try:
        array.reshape(2, 5)
    except ValueError as exc:
        print("Shape error:", exc)

    try:
        array[:, 0] + np.ones(5)
    except ValueError as exc:
        print("Broadcasting error:", exc)

    # Object dtype can silently reduce the performance benefits of numerical
    # NumPy operations, so accidental mixed Python objects should be avoided.
    object_array = np.array([1, "two", 3], dtype=object)
    print("Object dtype example:", object_array, object_array.dtype)


def main():
    fundamentals()
    indexing_and_slicing()
    reshaping_and_dimensions()
    dtype_and_numeric_behavior()
    vectorization()
    broadcasting()
    boolean_filtering_and_statistics()
    advanced_indexing()
    reductions_and_axis_reasoning()
    missing_values_and_validation()
    file_round_trip()
    linear_algebra_case_study()
    performance_comparison()
    common_failure_cases()


if __name__ == "__main__":
    main()
