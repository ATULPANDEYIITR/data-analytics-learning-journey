/*
 * Power Query Fundamentals: Industry-Style ETL Case Study
 *
 * Scenario:
 *   A retail analytics system receives transaction records together with
 *   customer and product reference data. The system must validate, type,
 *   clean, enrich, filter, merge, append, aggregate, and export the data.
 *
 * This C++17 implementation models the core concepts of Power Query while
 * emphasizing:
 *   - Strong typing
 *   - Explicit data structures
 *   - Hash-based joins
 *   - Validation
 *   - Error handling
 *   - ETL architecture
 *   - Performance considerations
 *   - Separation of extraction, transformation, and loading
 *
 * Compile:
 *   g++ -std=c++17 -O2 power_query_fundamentals.cpp -o etl
 *
 * Run:
 *   ./etl
 */

#include <algorithm>
#include <cctype>
#include <chrono>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;


// ============================================================================
// 1. CORE DATA MODELS
// ============================================================================

struct RawSale {
    string orderId;
    string orderDate;
    string customerId;
    string productId;
    string quantity;
    string unitPrice;
    string region;
};

struct Sale {
    int orderId{};
    string orderDate;
    string customerId;
    string productId;
    int quantity{};
    double unitPrice{};
    string region;
    double salesAmount{};
};

struct Customer {
    string customerId;
    string customerName;
    string segment;
};

struct Product {
    string productId;
    string productName;
    string category;
};

struct EnrichedSale {
    Sale sale;

    optional<string> customerName;
    optional<string> segment;

    optional<string> productName;
    optional<string> category;

    int year{};
    int month{};
    int quarter{};

    string orderValueClass;
};


// ============================================================================
// 2. UTILITY FUNCTIONS
// ============================================================================

string trim(const string& input) {
    size_t start = 0;
    size_t end = input.size();

    while (start < end &&
           isspace(static_cast<unsigned char>(input[start]))) {
        ++start;
    }

    while (end > start &&
           isspace(static_cast<unsigned char>(input[end - 1]))) {
        --end;
    }

    return input.substr(start, end - start);
}


string normalizeWhitespace(const string& input) {
    string result;
    bool previousWasSpace = false;

    for (char character : input) {
        if (isspace(static_cast<unsigned char>(character))) {
            if (!previousWasSpace) {
                result.push_back(' ');
            }

            previousWasSpace = true;
        } else {
            result.push_back(character);
            previousWasSpace = false;
        }
    }

    return trim(result);
}


string titleCase(string value) {
    value = normalizeWhitespace(value);

    bool capitalizeNext = true;

    for (char& character : value) {
        if (isspace(static_cast<unsigned char>(character))) {
            capitalizeNext = true;
        } else if (capitalizeNext) {
            character = static_cast<char>(
                toupper(static_cast<unsigned char>(character))
            );
            capitalizeNext = false;
        } else {
            character = static_cast<char>(
                tolower(static_cast<unsigned char>(character))
            );
        }
    }

    return value;
}


int parseInteger(const string& value, const string& fieldName) {
    string cleaned = trim(value);

    if (cleaned.empty()) {
        throw invalid_argument(
            fieldName + " is missing"
        );
    }

    size_t consumed = 0;
    int number = 0;

    try {
        number = stoi(cleaned, &consumed);
    } catch (const exception&) {
        throw invalid_argument(
            fieldName + " is not a valid integer: " + value
        );
    }

    if (consumed != cleaned.size()) {
        throw invalid_argument(
            fieldName + " contains invalid characters: " + value
        );
    }

    return number;
}


double parseDecimal(const string& value, const string& fieldName) {
    string cleaned = trim(value);

    if (cleaned.empty()) {
        throw invalid_argument(
            fieldName + " is missing"
        );
    }

    size_t consumed = 0;
    double number = 0.0;

    try {
        number = stod(cleaned, &consumed);
    } catch (const exception&) {
        throw invalid_argument(
            fieldName + " is not numeric: " + value
        );
    }

    if (consumed != cleaned.size() ||
        !isfinite(number)) {
        throw invalid_argument(
            fieldName + " contains an invalid number"
        );
    }

    return number;
}


// ============================================================================
// 3. EXTRACT
// ============================================================================

vector<RawSale> extractSales() {
    /*
     * A real implementation could read CSV, Excel, SQL, JSON, or an API.
     * The example uses in-memory source records so that it remains completely
     * self-contained.
     */
    return {
        {"1001", "2026-01-05", "C001", "P100", "2", "1250.50", " North "},
        {"1002", "2026-01-06", "C002", "P200", "5", "299.99", "South"},
        {"1003", "2026-01-07", "C003", "P100", "1", "1250.50", "West"},
        {"1004", "2026-01-08", "C001", "P300", "3", "850.00", "North"},
        {"1005", "2026-01-09", "C004", "P200", "4", "299.99", "East"},
        {"1006", "2026-01-10", "C005", "P400", "2", "1750.00", "South"},
        {"1007", "2026-01-11", "C006", "P300", "6", "850.00", "West"}
    };
}


vector<Customer> extractCustomers() {
    return {
        {"C001", "Atul Pandey", "Professional"},
        {"C002", "Neha Sharma", "Enterprise"},
        {"C003", "Rahul Verma", "SMB"},
        {"C004", "Priya Singh", "Enterprise"},
        {"C005", "Arjun Mehta", "Professional"},
        {"C006", "Simran Kaur", "SMB"}
    };
}


vector<Product> extractProducts() {
    return {
        {"P100", "Laptop", "Computing"},
        {"P200", "Keyboard", "Accessories"},
        {"P300", "Monitor", "Computing"},
        {"P400", "Server", "Infrastructure"}
    };
}


// ============================================================================
// 4. SCHEMA VALIDATION
// ============================================================================

void validateSourceSchema(
    const vector<RawSale>& rows
) {
    /*
     * C++ gives us compile-time structure for RawSale. Runtime validation
     * remains necessary because external sources can contain missing or
     * malformed values.
     */
    if (rows.empty()) {
        throw runtime_error("Sales source contains no records");
    }

    for (const RawSale& row : rows) {
        if (trim(row.orderId).empty()) {
            throw runtime_error("OrderID is required");
        }

        if (trim(row.customerId).empty()) {
            throw runtime_error("CustomerID is required");
        }

        if (trim(row.productId).empty()) {
            throw runtime_error("ProductID is required");
        }
    }
}


// ============================================================================
// 5. TRANSFORM: TYPE CONVERSION AND CLEANING
// ============================================================================

vector<Sale> transformSales(
    const vector<RawSale>& rawRows
) {
    vector<Sale> result;
    result.reserve(rawRows.size());

    for (const RawSale& raw : rawRows) {
        Sale sale;

        sale.orderId = parseInteger(raw.orderId, "OrderID");
        sale.orderDate = trim(raw.orderDate);
        sale.customerId = normalizeWhitespace(raw.customerId);
        sale.productId = normalizeWhitespace(raw.productId);
        sale.quantity = parseInteger(raw.quantity, "Quantity");
        sale.unitPrice = parseDecimal(raw.unitPrice, "UnitPrice");
        sale.region = titleCase(raw.region);

        if (sale.quantity <= 0) {
            throw invalid_argument(
                "Quantity must be greater than zero for OrderID "
                + to_string(sale.orderId)
            );
        }

        if (sale.unitPrice < 0.0) {
            throw invalid_argument(
                "UnitPrice cannot be negative for OrderID "
                + to_string(sale.orderId)
            );
        }

        /*
         * A calculated column.
         *
         * Power Query's Custom Column conceptually performs the same type
         * of row-level calculation.
         */
        sale.salesAmount =
            static_cast<double>(sale.quantity) * sale.unitPrice;

        result.push_back(sale);
    }

    return result;
}


// ============================================================================
// 6. FILTERING
// ============================================================================

vector<Sale> filterSales(
    const vector<Sale>& rows,
    const function<bool(const Sale&)>& predicate
) {
    vector<Sale> result;

    for (const Sale& row : rows) {
        if (predicate(row)) {
            result.push_back(row);
        }
    }

    return result;
}


// ============================================================================
// 7. MERGE: LEFT OUTER JOIN
// ============================================================================

unordered_map<string, Customer> indexCustomers(
    const vector<Customer>& customers
) {
    unordered_map<string, Customer> index;

    for (const Customer& customer : customers) {
        index[customer.customerId] = customer;
    }

    return index;
}


unordered_map<string, Product> indexProducts(
    const vector<Product>& products
) {
    unordered_map<string, Product> index;

    for (const Product& product : products) {
        index[product.productId] = product;
    }

    return index;
}


vector<EnrichedSale> mergeReferenceData(
    const vector<Sale>& sales,
    const vector<Customer>& customers,
    const vector<Product>& products
) {
    /*
     * Hash indexes make equality lookups approximately O(1) on average.
     *
     * A naive nested-loop join could approach O(n*m), which becomes costly
     * as datasets grow.
     */
    const auto customerIndex = indexCustomers(customers);
    const auto productIndex = indexProducts(products);

    vector<EnrichedSale> result;
    result.reserve(sales.size());

    for (const Sale& sale : sales) {
        EnrichedSale enriched;
        enriched.sale = sale;

        auto customerIt =
            customerIndex.find(sale.customerId);

        if (customerIt != customerIndex.end()) {
            enriched.customerName =
                customerIt->second.customerName;

            enriched.segment =
                customerIt->second.segment;
        }

        auto productIt =
            productIndex.find(sale.productId);

        if (productIt != productIndex.end()) {
            enriched.productName =
                productIt->second.productName;

            enriched.category =
                productIt->second.category;
        }

        result.push_back(enriched);
    }

    return result;
}


// ============================================================================
// 8. DATE TRANSFORMATION
// ============================================================================

int monthFromISODate(const string& date) {
    /*
     * The source uses ISO YYYY-MM-DD.
     *
     * This intentionally avoids a third-party date library so that the
     * example remains self-contained.
     */
    if (date.size() < 7) {
        throw invalid_argument(
            "Invalid ISO date: " + date
        );
    }

    return parseInteger(
        date.substr(5, 2),
        "Month"
    );
}


int yearFromISODate(const string& date) {
    if (date.size() < 4) {
        throw invalid_argument(
            "Invalid ISO date: " + date
        );
    }

    return parseInteger(
        date.substr(0, 4),
        "Year"
    );
}


void addDateAttributes(
    vector<EnrichedSale>& rows
) {
    for (EnrichedSale& row : rows) {
        row.year = yearFromISODate(
            row.sale.orderDate
        );

        row.month = monthFromISODate(
            row.sale.orderDate
        );

        row.quarter =
            ((row.month - 1) / 3) + 1;
    }
}


// ============================================================================
// 9. CONDITIONAL COLUMN
// ============================================================================

void classifyOrders(
    vector<EnrichedSale>& rows
) {
    for (EnrichedSale& row : rows) {
        const double amount =
            row.sale.salesAmount;

        if (amount >= 4000.0) {
            row.orderValueClass = "Very High";
        } else if (amount >= 2000.0) {
            row.orderValueClass = "High";
        } else if (amount >= 1000.0) {
            row.orderValueClass = "Medium";
        } else {
            row.orderValueClass = "Low";
        }
    }
}


// ============================================================================
// 10. REFERENTIAL INTEGRITY
// ============================================================================

vector<string> findUnmatchedCustomers(
    const vector<Sale>& sales,
    const vector<Customer>& customers
) {
    unordered_set<string> customerIds;

    for (const Customer& customer : customers) {
        customerIds.insert(customer.customerId);
    }

    vector<string> unmatched;
    unordered_set<string> alreadyReported;

    for (const Sale& sale : sales) {
        if (!customerIds.count(sale.customerId) &&
            !alreadyReported.count(sale.customerId)) {
            unmatched.push_back(sale.customerId);
            alreadyReported.insert(sale.customerId);
        }
    }

    return unmatched;
}


// ============================================================================
// 11. APPEND
// ============================================================================

vector<Sale> appendSales(
    const vector<Sale>& first,
    const vector<Sale>& second
) {
    /*
     * Append means vertical combination.

     * Merge means horizontal combination based on a relationship.

     * For append to be semantically correct, the input tables should
     * represent compatible structures.
     */
    vector<Sale> result;
    result.reserve(first.size() + second.size());

    result.insert(
        result.end(),
        first.begin(),
        first.end()
    );

    result.insert(
        result.end(),
        second.begin(),
        second.end()
    );

    return result;
}


// ============================================================================
// 12. GROUP BY AND AGGREGATION
// ============================================================================

map<string, double> revenueByRegion(
    const vector<EnrichedSale>& rows
) {
    map<string, double> totals;

    for (const EnrichedSale& row : rows) {
        totals[row.sale.region] +=
            row.sale.salesAmount;
    }

    return totals;
}


// ============================================================================
// 13. DATA QUALITY REPORT
// ============================================================================

struct DataQualityReport {
    size_t totalRows{};
    size_t invalidQuantityRows{};
    size_t negativePriceRows{};
    size_t missingCustomerMatches{};
    size_t missingProductMatches{};
};


DataQualityReport createQualityReport(
    const vector<Sale>& sales,
    const vector<Customer>& customers,
    const vector<Product>& products
) {
    DataQualityReport report;
    report.totalRows = sales.size();

    unordered_set<string> customerIds;
    unordered_set<string> productIds;

    for (const Customer& customer : customers) {
        customerIds.insert(customer.customerId);
    }

    for (const Product& product : products) {
        productIds.insert(product.productId);
    }

    for (const Sale& sale : sales) {
        if (sale.quantity <= 0) {
            ++report.invalidQuantityRows;
        }

        if (sale.unitPrice < 0) {
            ++report.negativePriceRows;
        }

        if (!customerIds.count(sale.customerId)) {
            ++report.missingCustomerMatches;
        }

        if (!productIds.count(sale.productId)) {
            ++report.missingProductMatches;
        }
    }

    return report;
}


// ============================================================================
// 14. QUERY-STEP MODEL
// ============================================================================

class ETLQuery {
private:
    vector<Sale> source;

    vector<pair<
        string,
        function<vector<Sale>(const vector<Sale>&)>
    >> steps;

public:
    explicit ETLQuery(vector<Sale> sourceRows)
        : source(std::move(sourceRows)) {}

    ETLQuery& addStep(
        const string& name,
        function<vector<Sale>(
            const vector<Sale>&
        )> transformation
    ) {
        steps.emplace_back(
            name,
            std::move(transformation)
        );

        return *this;
    }

    vector<Sale> execute() const {
        vector<Sale> current = source;

        for (const auto& step : steps) {
            current = step.second(current);
        }

        return current;
    }

    void describe() const {
        for (size_t i = 0; i < steps.size(); ++i) {
            cout << "  "
                 << (i + 1)
                 << ". "
                 << steps[i].first
                 << '\n';
        }
    }
};


// ============================================================================
// 15. LOAD
// ============================================================================

void loadReport(
    const vector<EnrichedSale>& rows
) {
    /*
     * Loading can mean inserting into a database, writing to a file,
     * populating an analytical model, or producing a reporting dataset.
     * Here the destination is a formatted console report.
     */
    cout << "\nFINAL REPORT\n";
    cout << left
         << setw(8) << "Order"
         << setw(14) << "Customer"
         << setw(14) << "Product"
         << setw(10) << "Region"
         << setw(12) << "Revenue"
         << setw(12) << "Class"
         << '\n';

    cout << string(70, '-') << '\n';

    cout << fixed
         << setprecision(2);

    for (const EnrichedSale& row : rows) {
        cout << left
             << setw(8)
             << row.sale.orderId

             << setw(14)
             << row.customerName.value_or("UNKNOWN")

             << setw(14)
             << row.productName.value_or("UNKNOWN")

             << setw(10)
             << row.sale.region

             << setw(12)
             << row.sale.salesAmount

             << setw(12)
             << row.orderValueClass

             << '\n';
    }
}


// ============================================================================
// 16. ASSERTION HELPER
// ============================================================================

void assertCondition(
    bool condition,
    const string& description
) {
    if (!condition) {
        throw runtime_error(
            "TEST FAILED: " + description
        );
    }

    cout << "PASS: " << description << '\n';
}


// ============================================================================
// 17. COMPLETE ETL APPLICATION
// ============================================================================

int main() {
    try {
        cout << string(78, '=') << '\n';
        cout << "POWER QUERY FUNDAMENTALS: C++ ETL CASE STUDY\n";
        cout << string(78, '=') << "\n\n";

        /*
         * EXTRACT
         */
        const auto rawSales = extractSales();
        const auto customers = extractCustomers();
        const auto products = extractProducts();

        cout << "Extracted sales rows: "
             << rawSales.size()
             << '\n';

        cout << "Extracted customers: "
             << customers.size()
             << '\n';

        cout << "Extracted products: "
             << products.size()
             << "\n\n";

        /*
         * Validate the source before transformation.
         */
        validateSourceSchema(rawSales);

        /*
         * TRANSFORM
         */
        const auto sales =
            transformSales(rawSales);

        cout << "Typed sales rows: "
             << sales.size()
             << "\n\n";

        /*
         * DATA QUALITY
         */
        const DataQualityReport quality =
            createQualityReport(
                sales,
                customers,
                products
            );

        cout << "DATA QUALITY\n";
        cout << "Total rows: "
             << quality.totalRows
             << '\n';

        cout << "Invalid quantity rows: "
             << quality.invalidQuantityRows
             << '\n';

        cout << "Negative price rows: "
             << quality.negativePriceRows
             << '\n';

        cout << "Missing customer matches: "
             << quality.missingCustomerMatches
             << '\n';

        cout << "Missing product matches: "
             << quality.missingProductMatches
             << "\n\n";

        /*
         * FILTERING
         */
        const auto northSales =
            filterSales(
                sales,
                [](const Sale& sale) {
                    return sale.region == "North";
                }
            );

        cout << "North-region rows: "
             << northSales.size()
             << '\n';

        const auto highValueSales =
            filterSales(
                sales,
                [](const Sale& sale) {
                    return sale.salesAmount >= 2000.0;
                }
            );

        cout << "High-value rows: "
             << highValueSales.size()
             << "\n\n";

        /*
         * MERGE
         */
        auto enriched =
            mergeReferenceData(
                sales,
                customers,
                products
            );

        /*
         * ADD DATE ATTRIBUTES
         */
        addDateAttributes(enriched);

        /*
         * ADD CONDITIONAL BUSINESS CLASS
         */
        classifyOrders(enriched);

        /*
         * REFERENTIAL INTEGRITY
         */
        const auto unmatchedCustomers =
            findUnmatchedCustomers(
                sales,
                customers
            );

        cout << "Unmatched customers: "
             << unmatchedCustomers.size()
             << '\n';

        for (const string& customerId :
             unmatchedCustomers) {
            cout << "  Missing key: "
                 << customerId
                 << '\n';
        }

        /*
         * GROUP BY
         */
        const auto regionTotals =
            revenueByRegion(enriched);

        cout << "\nREVENUE BY REGION\n";
        cout << fixed
             << setprecision(2);

        for (const auto& [region, revenue] :
             regionTotals) {
            cout << "  "
                 << setw(10)
                 << region
                 << revenue
                 << '\n';
        }

        /*
         * QUERY STEP DEMONSTRATION
         */
        ETLQuery query(sales);

        query
            .addStep(
                "Filter North region",
                [](const vector<Sale>& rows) {
                    return filterSales(
                        rows,
                        [](const Sale& sale) {
                            return sale.region == "North";
                        }
                    );
                }
            )
            .addStep(
                "Filter revenue above 1000",
                [](const vector<Sale>& rows) {
                    return filterSales(
                        rows,
                        [](const Sale& sale) {
                            return sale.salesAmount > 1000.0;
                        }
                    );
                }
            )
            .addStep(
                "Sort by revenue descending",
                [](const vector<Sale>& rows) {
                    vector<Sale> result = rows;

                    sort(
                        result.begin(),
                        result.end(),
                        [](const Sale& a, const Sale& b) {
                            return a.salesAmount >
                                   b.salesAmount;
                        }
                    );

                    return result;
                }
            );

        cout << "\nQUERY STEPS\n";
        query.describe();

        const auto queryResult =
            query.execute();

        cout << "\nQUERY RESULT ROWS: "
             << queryResult.size()
             << '\n';

        /*
         * APPEND DEMONSTRATION
         */
        vector<Sale> firstPeriod{
            sales.begin(),
            sales.begin() + 3
        };

        vector<Sale> secondPeriod{
            sales.begin() + 3,
            sales.end()
        };

        const auto appended =
            appendSales(
                firstPeriod,
                secondPeriod
            );

        cout << "\nAPPEND\n";
        cout << "First table rows: "
             << firstPeriod.size()
             << '\n';

        cout << "Second table rows: "
             << secondPeriod.size()
             << '\n';

        cout << "Appended rows: "
             << appended.size()
             << '\n';

        /*
         * PERFORMANCE MEASUREMENT
         */
        const auto start =
            chrono::steady_clock::now();

        volatile double checksum = 0.0;

        for (const EnrichedSale& row : enriched) {
            checksum += row.sale.salesAmount;
        }

        const auto end =
            chrono::steady_clock::now();

        const auto elapsed =
            chrono::duration_cast<
                chrono::microseconds
            >(end - start).count();

        cout << "\nPERFORMANCE SAMPLE\n";
        cout << "Checksum: "
             << checksum
             << '\n';

        cout << "Aggregation loop: "
             << elapsed
             << " microseconds\n";

        /*
         * TESTS
         */
        cout << "\nTESTS\n";

        assertCondition(
            sales.size() == rawSales.size(),
            "Extraction preserves expected sales count"
        );

        assertCondition(
            sales.front().quantity == 2,
            "Quantity converted from text to integer"
        );

        assertCondition(
            abs(
                sales.front().salesAmount - 2501.0
            ) < 0.000001,
            "Calculated sales amount"
        );

        assertCondition(
            enriched.front().customerName.has_value(),
            "Customer merge succeeded"
        );

        assertCondition(
            enriched.front().productName.has_value(),
            "Product merge succeeded"
        );

        assertCondition(
            enriched.front().quarter == 1,
            "Quarter calculation"
        );

        assertCondition(
            appended.size() == sales.size(),
            "Append preserves total compatible rows"
        );

        /*
         * LOAD
         */
        loadReport(enriched);

        /*
         * ARCHITECTURAL NOTES
         */
        cout << R"(

ARCHITECTURAL NOTES

ETL stages:
    Extract
        |
        v
    Validate source
        |
        v
    Type and clean
        |
        v
    Calculate derived fields
        |
        v
    Filter
        |
        v
    Merge reference data
        |
        v
    Aggregate / enrich
        |
        v
    Load

Merge:
    Combines related datasets horizontally using keys.

Append:
    Combines compatible datasets vertically.

Strong typing:
    C++ represents important data structures explicitly, making invalid
    structural assumptions easier to detect during development.

Hash joins:
    unordered_map provides approximately O(1) average key lookup.
    Building indexes is approximately O(n), followed by O(m) lookups.

Potential complexity:
    Naive nested-loop join: O(n*m)
    Indexed equality join: approximately O(n+m)

Production considerations:
    - Validate external schemas.
    - Record rejected rows rather than silently discarding them.
    - Keep credentials outside source code.
    - Protect personally identifiable information.
    - Use transactions for database loads where appropriate.
    - Make loads idempotent where possible.
    - Monitor source and destination row counts.
    - Log transformation failures.
    - Preserve data lineage.
    - Detect schema changes.
    - Consider source-side filtering and query folding.
    - Avoid loading data into memory when streaming or database-side
      processing is more appropriate.

Power Query relation:
    The same conceptual operations appear in Power Query as source steps,
    Changed Type, filtering, custom columns, Merge Queries, Append Queries,
    Group By, and loading into the destination model.
)";

        cout << "\n"
             << string(78, '=')
             << '\n';

        cout << "ETL CASE STUDY COMPLETE\n";

        cout << string(78, '=')
             << '\n';

        return 0;
    }
    catch (const exception& error) {
        /*
         * Production ETL systems should distinguish recoverable record-level
         * errors from fatal pipeline errors. This example reports fatal
         * failures cleanly and returns a non-zero process status.
         */
        cerr << "\nETL FAILURE: "
             << error.what()
             << '\n';

        return 1;
    }
}
