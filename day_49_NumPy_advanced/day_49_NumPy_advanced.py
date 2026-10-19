import numpy as np


def print_array(title, value):
    print(f"\n{title}")
    print(f"shape={value.shape}, dtype={value.dtype}")
    print(value)


def broadcasting_basics():
    print("\n=== Broadcasting ===")

    prices = np.array([
        [120.0, 80.0, 200.0],
        [150.0, 90.0, 180.0],
        [100.0, 70.0, 220.0],
    ])

    tax_rates = np.array([0.05, 0.12, 0.18])

    # (3, 3) + (3,) aligns the trailing dimensions:
    # each product column receives its corresponding tax rate.
    tax_amount = prices * tax_rates
    final_prices = prices + tax_amount

    print_array("Original prices", prices)
    print_array("Tax rates", tax_rates)
    print_array("Tax amounts produced by broadcasting", tax_amount)
    print_array("Final prices", final_prices)

    regional_adjustment = np.array([
        [1.02],
        [0.98],
        [1.05],
    ])

    # (3, 1) broadcasts across the three product columns.
    adjusted = final_prices * regional_adjustment
    print_array("Region-adjusted prices", adjusted)

    incompatible = np.ones((3, 4))
    try:
        _ = prices + incompatible
    except ValueError as exc:
        print("\nBroadcasting failure detected:")
        print(exc)


def aggregation_and_axis_operations():
    print("\n=== Aggregation and Axis Semantics ===")

    sales = np.array([
        [120, 150, 130, 170],
        [90, 110, 125, 105],
        [200, 190, 210, 230],
    ])

    print_array("Monthly sales by region", sales)

    print("\nTotal sales:", sales.sum())
    print("Mean sales:", sales.mean())
    print("Median sales:", np.median(sales))
    print("Maximum sale:", sales.max())
    print("Minimum sale:", sales.min())

    # axis=0 collapses rows, leaving one result per month.
    monthly_totals = sales.sum(axis=0)

    # axis=1 collapses columns, leaving one result per region.
    regional_totals = sales.sum(axis=1)

    print_array("Totals by month (axis=0)", monthly_totals)
    print_array("Totals by region (axis=1)", regional_totals)

    print_array("Average by region", sales.mean(axis=1))
    print_array("Maximum by month", sales.max(axis=0))

    best_region = np.argmax(regional_totals)
    weakest_month = np.argmin(monthly_totals)

    print("Best region index:", best_region)
    print("Weakest month index:", weakest_month)

    weights = np.array([0.10, 0.20, 0.30, 0.40])
    weighted_month_score = sales @ weights
    print_array("Weighted regional scores", weighted_month_score)


def reshaping_and_memory_layout():
    print("\n=== Reshaping ===")

    values = np.arange(1, 25)

    matrix = values.reshape(4, 6)
    print_array("4 x 6 matrix", matrix)

    reshaped = matrix.reshape(3, 8)
    print_array("3 x 8 reshaped matrix", reshaped)

    flattened = matrix.ravel()
    print_array("Ravelled matrix", flattened)

    column_major_view = matrix.reshape(3, 8, order="F")
    print_array("Reshaped with Fortran ordering", column_major_view)

    transposed = matrix.T
    print_array("Transpose", transposed)

    # reshape requires the same number of elements.
    try:
        matrix.reshape(5, 5)
    except ValueError as exc:
        print("\nInvalid reshape detected:")
        print(exc)

    tensor = np.arange(24).reshape(2, 3, 4)
    print_array("Three-dimensional tensor", tensor)

    moved = np.moveaxis(tensor, 0, -1)
    print_array("Tensor after moving axis 0 to the end", moved)


def matrix_operations():
    print("\n=== Matrix Operations ===")

    a = np.array([
        [2.0, 1.0],
        [4.0, 3.0],
    ])

    b = np.array([
        [5.0, 2.0],
        [1.0, 6.0],
    ])

    print_array("Matrix A", a)
    print_array("Matrix B", b)

    # Element-wise multiplication is different from matrix multiplication.
    print_array("Element-wise multiplication A * B", a * b)
    print_array("Matrix multiplication A @ B", a @ b)

    print_array("Transpose of A", a.T)

    determinant = np.linalg.det(a)
    inverse = np.linalg.inv(a)

    print("det(A):", determinant)
    print_array("Inverse of A", inverse)

    identity_check = a @ inverse
    print_array("A @ inv(A)", identity_check)

    vector = np.array([7.0, 5.0])
    solution = np.linalg.solve(a, vector)

    print_array("Solution to A x = vector", solution)
    print_array("Verification A @ x", a @ solution)

    eigenvalues, eigenvectors = np.linalg.eig(a)
    print_array("Eigenvalues", eigenvalues)
    print_array("Eigenvectors", eigenvectors)

    rank = np.linalg.matrix_rank(a)
    condition_number = np.linalg.cond(a)

    print("Matrix rank:", rank)
    print("Condition number:", condition_number)

    singular = np.array([
        [1.0, 2.0],
        [2.0, 4.0],
    ])

    print("\nSingular matrix determinant:", np.linalg.det(singular))

    try:
        np.linalg.inv(singular)
    except np.linalg.LinAlgError as exc:
        print("Singular inverse failure:", exc)


def random_generation_and_reproducibility():
    print("\n=== Random Generation ===")

    rng = np.random.default_rng(42)

    uniform_values = rng.uniform(0, 1, size=(3, 4))
    normal_values = rng.normal(loc=100, scale=15, size=(3, 4))
    integers = rng.integers(10, 101, size=12)

    print_array("Uniform random values", uniform_values)
    print_array("Normally distributed measurements", normal_values)
    print_array("Random integer samples", integers)

    categories = np.array(["low", "medium", "high"])
    sampled_categories = rng.choice(categories, size=10, replace=True)

    print_array("Randomly selected categories", sampled_categories)

    # A local Generator is preferable to changing NumPy's global random state.
    first = np.random.default_rng(123).normal(size=5)
    second = np.random.default_rng(123).normal(size=5)

    print("\nReproducible sequences equal:", np.array_equal(first, second))

    permutation = rng.permutation(np.arange(1, 11))
    print_array("Random permutation", permutation)


def statistical_matrix_pipeline():
    print("\n=== Statistical Matrix Pipeline ===")

    rng = np.random.default_rng(2026)

    # Rows represent observations and columns represent measurable features.
    observations = rng.normal(
        loc=np.array([50.0, 100.0, 0.50]),
        scale=np.array([8.0, 15.0, 0.08]),
        size=(1000, 3),
    )

    means = observations.mean(axis=0)
    standard_deviations = observations.std(axis=0)

    standardized = (observations - means) / standard_deviations

    print_array("Feature means", means)
    print_array("Feature standard deviations", standard_deviations)
    print_array("First five standardized observations", standardized[:5])

    # Matrix multiplication turns standardized features into composite scores.
    feature_weights = np.array([0.50, 0.30, 0.20])
    scores = standardized @ feature_weights

    print_array("First ten composite scores", scores[:10])
    print("Score mean:", scores.mean())
    print("Score standard deviation:", scores.std())

    covariance = np.cov(observations, rowvar=False)
    correlation = np.corrcoef(observations, rowvar=False)

    print_array("Feature covariance matrix", covariance)
    print_array("Feature correlation matrix", correlation)


def masked_operations_and_nan_handling():
    print("\n=== Masks, Missing Values, and Robust Aggregation ===")

    measurements = np.array([
        12.0, 15.5, np.nan, 18.2, 21.0, np.nan, 19.5, 16.8
    ])

    valid_mask = ~np.isnan(measurements)
    valid_values = measurements[valid_mask]

    print_array("Measurements", measurements)
    print_array("Valid values selected by a Boolean mask", valid_values)

    print("Valid count:", np.count_nonzero(valid_mask))
    print("Missing count:", np.count_nonzero(~valid_mask))
    print("NaN-aware mean:", np.nanmean(measurements))
    print("NaN-aware standard deviation:", np.nanstd(measurements))

    cleaned = np.where(
        np.isnan(measurements),
        np.nanmean(measurements),
        measurements,
    )

    print_array("Missing values replaced with the mean", cleaned)

    outlier_mask = np.abs(cleaned - cleaned.mean()) > 2 * cleaned.std()
    print_array("Outlier mask", outlier_mask)
    print_array("Detected outliers", cleaned[outlier_mask])


def advanced_broadcasting_with_tensors():
    print("\n=== Tensor Broadcasting ===")

    rng = np.random.default_rng(7)

    # Batch x height x width.
    images = rng.normal(size=(8, 4, 4))

    channel_bias = np.array([
        0.10, 0.20, 0.30, 0.40
    ])

    # (8,4,4) and (4,) align on the final dimension.
    biased_images = images + channel_bias

    row_scale = np.array([
        [1.0],
        [1.1],
        [0.9],
        [1.2],
    ])

    # (8,4,4) and (4,1) broadcast over the batch and width dimensions.
    normalized_images = biased_images * row_scale

    print_array("Original tensor", images)
    print_array("Bias-adjusted tensor", biased_images)
    print_array("Scaled tensor", normalized_images)

    batch_means = normalized_images.mean(axis=(1, 2))
    print_array("Mean value of each batch item", batch_means)


def vectorized_distance_matrix():
    print("\n=== Vectorized Pairwise Distance Calculation ===")

    points = np.array([
        [0.0, 0.0],
        [1.0, 2.0],
        [4.0, 1.0],
        [3.0, 5.0],
    ])

    # points[:, None, :] has shape (n, 1, dimensions).
    # points[None, :, :] has shape (1, n, dimensions).
    # Broadcasting creates an n x n x dimensions difference tensor.
    differences = points[:, None, :] - points[None, :, :]
    squared_distances = np.sum(differences ** 2, axis=2)
    distances = np.sqrt(squared_distances)

    print_array("Input points", points)
    print_array("Pairwise Euclidean distance matrix", distances)

    nearest_neighbor = np.where(
        np.eye(len(points), dtype=bool),
        np.inf,
        distances,
    ).argmin(axis=1)

    print_array("Nearest-neighbor index for each point", nearest_neighbor)


def performance_comparison():
    print("\n=== Vectorization and Performance ===")

    rng = np.random.default_rng(99)
    data = rng.random(1_000_000)

    import time

    start = time.perf_counter()
    vectorized_result = np.sqrt(data * 1.5 + 2.0)
    vectorized_time = time.perf_counter() - start

    start = time.perf_counter()
    loop_result = [np.sqrt(x * 1.5 + 2.0) for x in data]
    loop_time = time.perf_counter() - start

    print("Vectorized calculation time:", vectorized_time)
    print("Python-loop calculation time:", loop_time)
    print("Results agree:", np.allclose(vectorized_result, loop_result))

    # NumPy arrays store homogeneous values compactly and allow operations
    # to execute in optimized native code instead of Python iteration.


def practical_portfolio_risk_model():
    print("\n=== Practical Portfolio Risk Model ===")

    rng = np.random.default_rng(31415)

    asset_names = np.array([
        "Technology",
        "Healthcare",
        "Energy",
        "Finance",
    ])

    daily_returns = rng.normal(
        loc=np.array([0.0008, 0.0005, 0.0003, 0.0006]),
        scale=np.array([0.018, 0.012, 0.025, 0.015]),
        size=(252, 4),
    )

    weights = np.array([0.35, 0.25, 0.15, 0.25])

    # Broadcasting subtracts the feature-wise means from every trading day.
    centered_returns = daily_returns - daily_returns.mean(axis=0)

    covariance = centered_returns.T @ centered_returns / (len(daily_returns) - 1)

    portfolio_returns = daily_returns @ weights

    annualized_return = portfolio_returns.mean() * 252
    annualized_volatility = portfolio_returns.std(ddof=1) * np.sqrt(252)

    portfolio_variance = weights @ covariance @ weights
    covariance_volatility = np.sqrt(portfolio_variance * 252)

    percentile_5 = np.percentile(portfolio_returns, 5)
    historical_var = -percentile_5

    print_array("Assets", asset_names)
    print_array("Portfolio weights", weights)
    print_array("Covariance matrix", covariance)
    print_array("First ten daily portfolio returns", portfolio_returns[:10])

    print("Annualized arithmetic return:", annualized_return)
    print("Annualized volatility from portfolio returns:", annualized_volatility)
    print("Annualized volatility from covariance:", covariance_volatility)
    print("Historical one-day 5% VaR:", historical_var)

    if not np.isclose(annualized_volatility, covariance_volatility, rtol=1e-10):
        raise RuntimeError("Portfolio volatility calculations disagree.")


def input_validation_examples():
    print("\n=== Validation and Numerical Safety ===")

    def validate_matrix(matrix, name):
        matrix = np.asarray(matrix, dtype=np.float64)

        if matrix.ndim != 2:
            raise ValueError(f"{name} must be two-dimensional.")

        if not np.all(np.isfinite(matrix)):
            raise ValueError(f"{name} contains NaN or infinite values.")

        return matrix

    valid = validate_matrix([[1, 2], [3, 4]], "valid")
    print_array("Validated matrix", valid)

    try:
        validate_matrix([[1, np.inf]], "unsafe")
    except ValueError as exc:
        print("Validation failure:", exc)

    # Integer overflow can occur when using narrow integer dtypes.
    small_integer = np.array([120, 120], dtype=np.int8)
    print("\nInt8 addition demonstrates dtype limits:", small_integer + small_integer)

    safe_integer = small_integer.astype(np.int64)
    print("Converted to int64 before arithmetic:", safe_integer + safe_integer)


def main():
    print("NumPy Advanced: broadcasting, aggregation, reshaping, matrices, and randomness")

    broadcasting_basics()
    aggregation_and_axis_operations()
    reshaping_and_memory_layout()
    matrix_operations()
    random_generation_and_reproducibility()
    statistical_matrix_pipeline()
    masked_operations_and_nan_handling()
    advanced_broadcasting_with_tensors()
    vectorized_distance_matrix()
    performance_comparison()
    practical_portfolio_risk_model()
    input_validation_examples()

    print("\n=== Completed Successfully ===")


if __name__ == "__main__":
    main()
