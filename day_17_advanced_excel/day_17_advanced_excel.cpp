/*
Advanced Excel Case Study in C++17
==================================

Scenario:
    A company receives sales records and needs a reusable analytical engine
    capable of performing operations conceptually equivalent to modern Excel
    dynamic-array workflows.

The system demonstrates:

    - dynamic-array thinking
    - SEQUENCE-style generation
    - FILTER-style selection
    - UNIQUE-style deduplication
    - SORT-style ordering
    - LET-style intermediate calculations
    - LAMBDA-style reusable functions through std::function
    - validation
    - error handling
    - aggregation
    - multi-stage analytical pipelines
    - complexity and performance considerations

The program uses only the C++17 standard library.
*/

#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

// =============================================================================
// 1. DATA MODEL
// =============================================================================

struct Sale {
    int transactionId;
    string product;
    string region;
    int units;
    double unitPrice;
    double costPerUnit;

    double revenue() const {
        return static_cast<double>(units) * unitPrice;
    }

    double cost() const {
        return static_cast<double>(units) * costPerUnit;
    }

    double profit() const {
        return revenue() - cost();
    }

    optional<double> margin() const {
        const double revenueValue = revenue();

        if (revenueValue == 0.0) {
            return nullopt;
        }

        return profit() / revenueValue;
    }
};


// =============================================================================
// 2. OUTPUT HELPERS
// =============================================================================

void printLine(char character = '-', size_t length = 78) {
    cout << string(length, character) << '\n';
}

void printSale(const Sale& sale) {
    cout << left
         << setw(5) << sale.transactionId
         << setw(12) << sale.product
         << setw(10) << sale.region
         << right
         << setw(7) << sale.units
         << setw(14) << fixed << setprecision(2) << sale.revenue()
         << setw(14) << sale.cost()
         << setw(14) << sale.profit()
         << '\n';
}

void printSales(const vector<Sale>& sales) {
    cout << left
         << setw(5) << "ID"
         << setw(12) << "Product"
         << setw(10) << "Region"
         << right
         << setw(7) << "Units"
         << setw(14) << "Revenue"
         << setw(14) << "Cost"
         << setw(14) << "Profit"
         << '\n';

    printLine();

    for (const auto& sale : sales) {
        printSale(sale);
    }
}


// =============================================================================
// 3. SEQUENCE
// =============================================================================

/*
Excel:

    =SEQUENCE(rows, columns, start, step)

This implementation generates a rectangular two-dimensional vector.
*/

vector<vector<int>> sequence(
    int rows,
    int columns = 1,
    int start = 1,
    int step = 1
) {
    if (rows < 0 || columns < 0) {
        throw invalid_argument(
            "SEQUENCE rows and columns cannot be negative."
        );
    }

    vector<vector<int>> result(
        static_cast<size_t>(rows),
        vector<int>(static_cast<size_t>(columns))
    );

    int current = start;

    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            result[row][column] = current;
            current += step;
        }
    }

    return result;
}

void printMatrix(const vector<vector<int>>& matrix) {
    for (const auto& row : matrix) {
        for (const int value : row) {
            cout << setw(6) << value;
        }
        cout << '\n';
    }
}


// =============================================================================
// 4. FILTER
// =============================================================================

/*
Excel FILTER is conceptually a selection operation:

    FILTER(array, include, [if_empty])

The predicate is equivalent to the include Boolean array.
*/

template <typename T>
vector<T> filter(
    const vector<T>& values,
    const function<bool(const T&)>& predicate
) {
    vector<T> result;

    for (const auto& value : values) {
        if (predicate(value)) {
            result.push_back(value);
        }
    }

    return result;
}


// =============================================================================
// 5. UNIQUE
// =============================================================================

/*
For arbitrary objects, uniqueness requires an equality relationship.
For strings, std::unordered_set provides efficient membership tracking.
*/

vector<string> uniqueStrings(
    const vector<string>& values
) {
    unordered_set<string> seen;
    vector<string> result;

    for (const auto& value : values) {
        if (seen.insert(value).second) {
            result.push_back(value);
        }
    }

    return result;
}


// =============================================================================
// 6. SORT
// =============================================================================

template <typename T>
vector<T> sortedCopy(
    const vector<T>& values,
    const function<bool(const T&, const T&)>& comparator
) {
    vector<T> result = values;

    sort(result.begin(), result.end(), comparator);

    return result;
}


// =============================================================================
// 7. LAMBDA-STYLE FUNCTIONS
// =============================================================================

/*
Excel LAMBDA creates reusable functions.

C++ lambda expressions provide a related programming mechanism:

    auto margin = [](double revenue, double cost) {
        ...
    };

std::function can store a reusable callable with a specified signature.
*/

using MarginFunction = function<optional<double>(double, double)>;

MarginFunction createMarginFunction() {
    return [](double revenue, double cost) -> optional<double> {
        if (!isfinite(revenue) || !isfinite(cost)) {
            throw invalid_argument(
                "Revenue and cost must be finite numbers."
            );
        }

        if (revenue == 0.0) {
            return nullopt;
        }

        return (revenue - cost) / revenue;
    };
}


// =============================================================================
// 8. LET-STYLE CALCULATION
// =============================================================================

/*
Excel LET:

    =LET(
        revenue, ...,
        cost, ...,
        profit, revenue-cost,
        ...
    )

C++ local variables express the same fundamental software-engineering idea:
calculate an intermediate result once, give it a meaningful name, and reuse it.
*/

struct CalculatedSale {
    Sale source;
    double revenue;
    double cost;
    double profit;
    optional<double> margin;
};

CalculatedSale calculateSale(
    const Sale& sale,
    const MarginFunction& marginFunction
) {
    // Named intermediate calculations model LET variables.
    const double revenue = sale.revenue();
    const double cost = sale.cost();
    const double profit = revenue - cost;
    const optional<double> marginValue =
        marginFunction(revenue, cost);

    return {
        sale,
        revenue,
        cost,
        profit,
        marginValue
    };
}


// =============================================================================
// 9. DATASET
// =============================================================================

vector<Sale> createSalesData() {
    return {
        {1, "Laptop", "North", 4, 85000.0, 65000.0},
        {2, "Monitor", "West", 10, 18000.0, 12000.0},
        {3, "Laptop", "West", 3, 85000.0, 65000.0},
        {4, "Keyboard", "North", 20, 3500.0, 2100.0},
        {5, "Monitor", "South", 7, 18000.0, 12000.0},
        {6, "Laptop", "North", 2, 85000.0, 65000.0},
        {7, "Keyboard", "West", 14, 3500.0, 2100.0},
        {8, "Mouse", "West", 30, 1500.0, 900.0},
        {9, "Mouse", "North", 25, 1500.0, 900.0},
        {10, "Monitor", "West", 4, 18000.0, 12000.0}
    };
}


// =============================================================================
// 10. REGION FILTER
// =============================================================================

vector<Sale> filterByRegion(
    const vector<Sale>& sales,
    const string& region
) {
    return filter<Sale>(
        sales,
        [&region](const Sale& sale) {
            return sale.region == region;
        }
    );
}


// =============================================================================
// 11. PRODUCT UNIQUE OPERATION
// =============================================================================

vector<string> productsFromSales(
    const vector<Sale>& sales
) {
    vector<string> products;

    products.reserve(sales.size());

    for (const auto& sale : sales) {
        products.push_back(sale.product);
    }

    return uniqueStrings(products);
}


// =============================================================================
// 12. AGGREGATION MODEL
// =============================================================================

struct ProductSummary {
    string product;
    int units = 0;
    double revenue = 0.0;
    double cost = 0.0;
    double profit = 0.0;
    double margin = 0.0;
};

vector<ProductSummary> summarizeProducts(
    const vector<Sale>& sales
) {
    const vector<string> products = productsFromSales(sales);

    vector<ProductSummary> result;

    for (const string& product : products) {
        ProductSummary summary;
        summary.product = product;

        // The product list came from UNIQUE, so each product is processed
        // once even when several source records contain the same product.
        for (const auto& sale : sales) {
            if (sale.product == product) {
                summary.units += sale.units;
                summary.revenue += sale.revenue();
                summary.cost += sale.cost();
            }
        }

        summary.profit = summary.revenue - summary.cost;

        if (summary.revenue != 0.0) {
            summary.margin =
                summary.profit / summary.revenue;
        }

        result.push_back(summary);
    }

    return result;
}

void printProductSummaries(
    const vector<ProductSummary>& summaries
) {
    cout << left
         << setw(12) << "Product"
         << right
         << setw(10) << "Units"
         << setw(16) << "Revenue"
         << setw(16) << "Cost"
         << setw(16) << "Profit"
         << setw(12) << "Margin"
         << '\n';

    printLine();

    for (const auto& summary : summaries) {
        cout << left
             << setw(12) << summary.product
             << right
             << setw(10) << summary.units
             << setw(16) << fixed << setprecision(2)
             << summary.revenue
             << setw(16) << summary.cost
             << setw(16) << summary.profit
             << setw(11) << setprecision(2)
             << summary.margin * 100.0
             << "%"
             << '\n';
    }
}


// =============================================================================
// 13. COMPLETE DYNAMIC-ARRAY PIPELINE
// =============================================================================

/*
The workflow models a formula such as:

    =LET(
        filtered, FILTER(data, region="West"),
        products, UNIQUE(filtered_products),
        ...
        SORT(results, profit, -1)
    )

Stages:

    source records
        ↓
    FILTER by region
        ↓
    calculate revenue/cost/profit
        ↓
    FILTER by minimum profit
        ↓
    UNIQUE product categories
        ↓
    aggregate
        ↓
    SORT by profit descending
*/

vector<ProductSummary> regionalProductAnalysis(
    const vector<Sale>& sales,
    const string& region,
    double minimumProfit
) {
    // LET-style named intermediate result.
    const vector<Sale> filteredSales =
        filterByRegion(sales, region);

    const MarginFunction marginFunction =
        createMarginFunction();

    vector<CalculatedSale> calculatedSales;

    for (const auto& sale : filteredSales) {
        calculatedSales.push_back(
            calculateSale(sale, marginFunction)
        );
    }

    // FILTER using a value calculated by the pipeline.
    vector<CalculatedSale> profitableSales =
        filter<CalculatedSale>(
            calculatedSales,
            [minimumProfit](const CalculatedSale& sale) {
                return sale.profit >= minimumProfit;
            }
        );

    vector<Sale> reducedSales;

    for (const auto& sale : profitableSales) {
        reducedSales.push_back(sale.source);
    }

    vector<ProductSummary> summaries =
        summarizeProducts(reducedSales);

    // SORT-style operation.
    return sortedCopy<ProductSummary>(
        summaries,
        [](const ProductSummary& left,
           const ProductSummary& right) {
            if (left.profit != right.profit) {
                return left.profit > right.profit;
            }

            return left.product < right.product;
        }
    );
}


// =============================================================================
// 14. MULTI-CRITERIA SORT
// =============================================================================

vector<Sale> multiCriteriaSort(
    const vector<Sale>& sales
) {
    return sortedCopy<Sale>(
        sales,
        [](const Sale& left, const Sale& right) {
            // Primary key: profit descending.
            if (left.profit() != right.profit()) {
                return left.profit() > right.profit();
            }

            // Secondary key: product ascending.
            if (left.product != right.product) {
                return left.product < right.product;
            }

            // Tertiary key: transaction ID ascending.
            return left.transactionId < right.transactionId;
        }
    );
}


// =============================================================================
// 15. EXACTLY-ONCE UNIQUE
// =============================================================================

vector<string> uniqueExactlyOnce(
    const vector<string>& values
) {
    unordered_map<string, int> counts;

    for (const auto& value : values) {
        ++counts[value];
    }

    vector<string> result;

    for (const auto& value : values) {
        if (counts[value] == 1) {
            result.push_back(value);
        }
    }

    return result;
}


// =============================================================================
// 16. VALIDATION
// =============================================================================

void validateSale(const Sale& sale) {
    if (sale.transactionId <= 0) {
        throw invalid_argument(
            "Transaction ID must be positive."
        );
    }

    if (sale.product.empty()) {
        throw invalid_argument(
            "Product cannot be empty."
        );
    }

    if (sale.region.empty()) {
        throw invalid_argument(
            "Region cannot be empty."
        );
    }

    if (sale.units < 0) {
        throw invalid_argument(
            "Units cannot be negative."
        );
    }

    if (!isfinite(sale.unitPrice) ||
        !isfinite(sale.costPerUnit)) {
        throw invalid_argument(
            "Price and cost must be finite."
        );
    }
}

void validateDataset(
    const vector<Sale>& sales
) {
    unordered_set<int> transactionIds;

    for (const auto& sale : sales) {
        validateSale(sale);

        if (!transactionIds.insert(
                sale.transactionId
            ).second) {
            throw invalid_argument(
                "Duplicate transaction ID detected."
            );
        }
    }
}


// =============================================================================
// 17. STATISTICAL ANALYSIS
// =============================================================================

struct Statistics {
    size_t count = 0;
    double minimum = 0.0;
    double maximum = 0.0;
    double mean = 0.0;
    double median = 0.0;
};

Statistics calculateStatistics(
    vector<double> values
) {
    if (values.empty()) {
        throw invalid_argument(
            "Cannot calculate statistics for an empty array."
        );
    }

    sort(values.begin(), values.end());

    const double total =
        accumulate(values.begin(), values.end(), 0.0);

    Statistics result;
    result.count = values.size();
    result.minimum = values.front();
    result.maximum = values.back();
    result.mean = total / static_cast<double>(values.size());

    const size_t middle = values.size() / 2;

    if (values.size() % 2 == 0) {
        result.median =
            (values[middle - 1] + values[middle]) / 2.0;
    } else {
        result.median = values[middle];
    }

    return result;
}


// =============================================================================
// 18. PERFORMANCE MODEL
// =============================================================================

/*
Approximate complexity:

    SEQUENCE:
        O(n) where n is the number of output cells.

    FILTER:
        O(n).

    UNIQUE with unordered_set:
        approximately O(n) average case.

    SORT:
        O(n log n).

    The aggregation implementation below scans source records for each
    unique product. If there are n records and k unique products, its
    worst-case behavior is approximately O(n*k).

    A production implementation could build a hash map in one pass to
    reduce aggregation toward O(n) average time.
*/

vector<ProductSummary> fastProductAggregation(
    const vector<Sale>& sales
) {
    unordered_map<string, ProductSummary> grouped;

    for (const auto& sale : sales) {
        auto& summary = grouped[sale.product];

        summary.product = sale.product;
        summary.units += sale.units;
        summary.revenue += sale.revenue();
        summary.cost += sale.cost();
    }

    vector<ProductSummary> result;

    result.reserve(grouped.size());

    for (auto& [product, summary] : grouped) {
        summary.profit =
            summary.revenue - summary.cost;

        if (summary.revenue != 0.0) {
            summary.margin =
                summary.profit / summary.revenue;
        }

        result.push_back(summary);
    }

    return sortedCopy<ProductSummary>(
        result,
        [](const ProductSummary& left,
           const ProductSummary& right) {
            return left.profit > right.profit;
        }
    );
}


// =============================================================================
// 19. TESTS
// =============================================================================

void require(
    bool condition,
    const string& message
) {
    if (!condition) {
        throw runtime_error(
            "Test failed: " + message
        );
    }
}

void runTests() {
    const auto generated = sequence(3);

    require(
        generated.size() == 3,
        "SEQUENCE row count"
    );

    require(
        generated[0][0] == 1 &&
        generated[1][0] == 2 &&
        generated[2][0] == 3,
        "SEQUENCE values"
    );

    const vector<int> values = {1, 2, 3, 4};

    const auto filtered = filter<int>(
        values,
        [](int value) {
            return value % 2 == 0;
        }
    );

    require(
        filtered == vector<int>{2, 4},
        "FILTER"
    );

    const vector<string> duplicateValues = {
        "A", "B", "A", "C", "B"
    };

    require(
        uniqueStrings(duplicateValues) ==
            vector<string>{"A", "B", "C"},
        "UNIQUE"
    );

    const auto sorted = sortedCopy<int>(
        values,
        [](int left, int right) {
            return left > right;
        }
    );

    require(
        sorted == vector<int>{4, 3, 2, 1},
        "SORT"
    );

    const MarginFunction margin =
        createMarginFunction();

    const auto marginResult =
        margin(1000.0, 600.0);

    require(
        marginResult.has_value() &&
        abs(*marginResult - 0.4) < 1e-9,
        "LAMBDA-style margin"
    );

    cout << "\nAll C++ tests passed.\n";
}


// =============================================================================
// 20. MAIN CASE STUDY
// =============================================================================

int main() {
    try {
        printLine('=');
        cout << "ADVANCED EXCEL DYNAMIC-ARRAY CASE STUDY IN C++17\n";
        printLine('=');

        // ---------------------------------------------------------------------
        // SEQUENCE demonstration
        // ---------------------------------------------------------------------

        cout << "\n1. SEQUENCE-style generation\n";
        printLine();

        const auto generated = sequence(
            3,
            4,
            10,
            5
        );

        printMatrix(generated);

        // ---------------------------------------------------------------------
        // Source dataset
        // ---------------------------------------------------------------------

        const vector<Sale> sales =
            createSalesData();

        validateDataset(sales);

        cout << "\n2. Source sales dataset\n";
        printLine();
        printSales(sales);

        // ---------------------------------------------------------------------
        // FILTER
        // ---------------------------------------------------------------------

        const vector<Sale> westSales =
            filterByRegion(sales, "West");

        cout << "\n3. FILTER: West-region records\n";
        printLine();
        printSales(westSales);

        // ---------------------------------------------------------------------
        // UNIQUE
        // ---------------------------------------------------------------------

        const vector<string> products =
            productsFromSales(westSales);

        cout << "\n4. UNIQUE: West-region products\n";
        printLine();

        for (const auto& product : products) {
            cout << product << '\n';
        }

        // ---------------------------------------------------------------------
        // SORT
        // ---------------------------------------------------------------------

        const vector<Sale> sortedSales =
            multiCriteriaSort(sales);

        cout << "\n5. SORT: profit descending\n";
        printLine();
        printSales(sortedSales);

        // ---------------------------------------------------------------------
        // LET-style calculation
        // ---------------------------------------------------------------------

        const MarginFunction marginFunction =
            createMarginFunction();

        cout << "\n6. LET-style calculated fields\n";
        printLine();

        for (const auto& sale : westSales) {
            const CalculatedSale calculated =
                calculateSale(
                    sale,
                    marginFunction
                );

            cout << calculated.source.product
                 << " | Revenue: "
                 << fixed << setprecision(2)
                 << calculated.revenue
                 << " | Cost: "
                 << calculated.cost
                 << " | Profit: "
                 << calculated.profit
                 << " | Margin: ";

            if (calculated.margin.has_value()) {
                cout << *calculated.margin * 100.0 << "%";
            } else {
                cout << "N/A";
            }

            cout << '\n';
        }

        // ---------------------------------------------------------------------
        // Integrated FILTER + LET + UNIQUE + SORT workflow
        // ---------------------------------------------------------------------

        cout << "\n7. Integrated dynamic-array workflow\n";
        printLine();

        const auto regionalAnalysis =
            regionalProductAnalysis(
                sales,
                "West",
                10000.0
            );

        printProductSummaries(
            regionalAnalysis
        );

        // ---------------------------------------------------------------------
        // Exactly-once UNIQUE
        // ---------------------------------------------------------------------

        const vector<string> sampleCategories = {
            "A", "B", "A", "C", "D", "D"
        };

        cout << "\n8. UNIQUE exactly_once behavior\n";
        printLine();

        const auto exactlyOnce =
            uniqueExactlyOnce(
                sampleCategories
            );

        for (const auto& value : exactlyOnce) {
            cout << value << '\n';
        }

        // ---------------------------------------------------------------------
        // Statistics
        // ---------------------------------------------------------------------

        vector<double> westProfits;

        for (const auto& sale : westSales) {
            westProfits.push_back(
                sale.profit()
            );
        }

        cout << "\n9. Statistics over filtered array\n";
        printLine();

        if (!westProfits.empty()) {
            const Statistics stats =
                calculateStatistics(
                    westProfits
                );

            cout << "Count:   " << stats.count << '\n'
                 << "Minimum: " << stats.minimum << '\n'
                 << "Maximum: " << stats.maximum << '\n'
                 << "Mean:    " << stats.mean << '\n'
                 << "Median:  " << stats.median << '\n';
        }

        // ---------------------------------------------------------------------
        // Fast aggregation
        // ---------------------------------------------------------------------

        cout << "\n10. Hash-based aggregation\n";
        printLine();

        const auto fastAggregation =
            fastProductAggregation(
                sales
            );

        printProductSummaries(
            fastAggregation
        );

        // ---------------------------------------------------------------------
        // Empty result
        // ---------------------------------------------------------------------

        cout << "\n11. Empty FILTER result\n";
        printLine();

        const auto eastSales =
            filterByRegion(
                sales,
                "East"
            );

        if (eastSales.empty()) {
            cout << "No matching records.\n";
        }

        // ---------------------------------------------------------------------
        // Failure condition
        // ---------------------------------------------------------------------

        cout << "\n12. Validation failure example\n";
        printLine();

        try {
            Sale invalidSale{
                -1,
                "",
                "West",
                -5,
                numeric_limits<double>::quiet_NaN(),
                100.0
            };

            validateSale(invalidSale);
        } catch (const exception& error) {
            cout << "Controlled error: "
                 << error.what()
                 << '\n';
        }

        // ---------------------------------------------------------------------
        // Tests
        // ---------------------------------------------------------------------

        cout << "\n13. Automated tests\n";
        printLine();

        runTests();

        // ---------------------------------------------------------------------
        // Architectural notes
        // ---------------------------------------------------------------------

        cout << "\n14. Case-study architecture\n";
        printLine();

        cout << "Source records -> FILTER -> calculated fields ->\n"
             << "FILTER by derived metric -> UNIQUE -> aggregation -> SORT\n";

        cout << "\nComplexity considerations:\n"
             << "FILTER: approximately O(n)\n"
             << "UNIQUE: approximately O(n) average with hashing\n"
             << "SORT: O(n log n)\n"
             << "Hash aggregation: approximately O(n) average\n";

        cout << "\nC++ case study completed successfully.\n";

    } catch (const exception& error) {
        cerr << "\nFatal error: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
