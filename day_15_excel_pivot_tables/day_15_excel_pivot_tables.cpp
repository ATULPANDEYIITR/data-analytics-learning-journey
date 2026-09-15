/*
 * Excel Pivot Tables: C++ Technical Case Study
 *
 * Scenario:
 *   A retail organization wants an internal analytical engine that behaves
 *   conceptually like an Excel Pivot Table. The engine must summarize sales
 *   transactions by dimensions, apply filters, calculate measures, support
 *   grouping, generate subtotals and grand totals, and allow drill-down from
 *   a summary cell to the contributing transactions.
 *
 * C++17 or later.
 *
 * Build:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic pivot_tables.cpp -o pivot_tables
 *
 * The implementation uses only the C++ standard library.
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// 1. SOURCE DATA MODEL
// ============================================================================

struct SalesRecord {
    string orderId;
    string orderDate;       // ISO YYYY-MM-DD representation.
    int year;
    int month;
    string region;
    string salesperson;
    string product;
    string category;
    int quantity;
    double unitPrice;
    double unitCost;
    string customerType;

    double sales() const {
        return quantity * unitPrice;
    }

    double cost() const {
        return quantity * unitCost;
    }

    double profit() const {
        return sales() - cost();
    }

    double margin() const {
        const double revenue = sales();

        if (revenue == 0.0) {
            return 0.0;
        }

        return profit() / revenue;
    }
};


// ============================================================================
// 2. SAMPLE SOURCE DATA
// ============================================================================

vector<SalesRecord> createSourceData() {
    return {
        {"O001", "2025-01-05", 2025, 1, "North", "Asha", "Laptop", "Electronics", 2, 800, 600, "Retail"},
        {"O002", "2025-01-12", 2025, 1, "North", "Rahul", "Phone", "Electronics", 5, 500, 350, "Corporate"},
        {"O003", "2025-01-18", 2025, 1, "South", "Neha", "Desk", "Furniture", 3, 250, 150, "Retail"},
        {"O004", "2025-02-02", 2025, 2, "South", "Vikram", "Chair", "Furniture", 10, 120, 70, "Corporate"},
        {"O005", "2025-02-09", 2025, 2, "East", "Asha", "Laptop", "Electronics", 1, 850, 610, "Retail"},
        {"O006", "2025-02-16", 2025, 2, "East", "Rahul", "Phone", "Electronics", 4, 520, 360, "Corporate"},
        {"O007", "2025-03-04", 2025, 3, "West", "Neha", "Desk", "Furniture", 2, 270, 160, "Retail"},
        {"O008", "2025-03-11", 2025, 3, "West", "Vikram", "Chair", "Furniture", 8, 125, 72, "Corporate"},
        {"O009", "2025-03-19", 2025, 3, "North", "Asha", "Monitor", "Electronics", 6, 300, 210, "Retail"},
        {"O010", "2025-04-03", 2025, 4, "South", "Rahul", "Laptop", "Electronics", 3, 820, 590, "Corporate"},
        {"O011", "2025-04-10", 2025, 4, "East", "Neha", "Chair", "Furniture", 6, 130, 75, "Retail"},
        {"O012", "2025-04-22", 2025, 4, "West", "Vikram", "Phone", "Electronics", 7, 510, 355, "Corporate"},
        {"O013", "2025-05-02", 2025, 5, "North", "Asha", "Desk", "Furniture", 4, 260, 155, "Retail"},
        {"O014", "2025-05-17", 2025, 5, "South", "Rahul", "Monitor", "Electronics", 5, 310, 215, "Corporate"},
        {"O015", "2025-06-07", 2025, 6, "East", "Neha", "Laptop", "Electronics", 2, 840, 605, "Retail"},
        {"O016", "2025-06-21", 2025, 6, "West", "Vikram", "Desk", "Furniture", 3, 255, 152, "Corporate"},
        {"O017", "2025-07-05", 2025, 7, "North", "Asha", "Chair", "Furniture", 9, 118, 69, "Retail"},
        {"O018", "2025-07-14", 2025, 7, "South", "Rahul", "Phone", "Electronics", 6, 515, 358, "Corporate"},
        {"O019", "2025-08-08", 2025, 8, "East", "Neha", "Monitor", "Electronics", 3, 305, 212, "Retail"},
        {"O020", "2025-08-25", 2025, 8, "West", "Vikram", "Laptop", "Electronics", 2, 830, 595, "Corporate"}
    };
}


// ============================================================================
// 3. MEASURE AND DIMENSION ABSTRACTIONS
// ============================================================================

enum class Aggregation {
    SUM,
    COUNT,
    AVERAGE,
    MINIMUM,
    MAXIMUM,
    DISTINCT_COUNT
};


struct ValueField {
    string name;
    Aggregation aggregation;
    string label;
};


struct PivotConfiguration {
    vector<string> rowFields;
    vector<string> columnFields;
    vector<ValueField> valueFields;

    // Each filter field maps to its accepted values.
    map<string, set<string>> filters;

    // Date grouping can be "month", "quarter", or "year".
    string dateGrouping;
};


// ============================================================================
// 4. FIELD EXTRACTION
// ============================================================================
//
// A Pivot engine needs a consistent way to transform a source record into
// dimension or measure values. In Excel this abstraction is largely hidden
// behind the field list. Here it is explicit so the architecture is visible.
//

string getStringField(
    const SalesRecord& record,
    const string& field
) {
    if (field == "region") return record.region;
    if (field == "salesperson") return record.salesperson;
    if (field == "product") return record.product;
    if (field == "category") return record.category;
    if (field == "customerType") return record.customerType;
    if (field == "orderId") return record.orderId;

    throw invalid_argument(
        "Unknown string field: " + field
    );
}


double getNumericField(
    const SalesRecord& record,
    const string& field
) {
    if (field == "quantity") {
        return static_cast<double>(record.quantity);
    }

    if (field == "unitPrice") {
        return record.unitPrice;
    }

    if (field == "unitCost") {
        return record.unitCost;
    }

    if (field == "sales") {
        return record.sales();
    }

    if (field == "cost") {
        return record.cost();
    }

    if (field == "profit") {
        return record.profit();
    }

    if (field == "margin") {
        return record.margin();
    }

    throw invalid_argument(
        "Unknown numeric field: " + field
    );
}


// ============================================================================
// 5. GROUPING
// ============================================================================

string monthGroup(const SalesRecord& record) {
    ostringstream output;

    output << record.year
           << "-"
           << setw(2)
           << setfill('0')
           << record.month;

    return output.str();
}


string quarterGroup(const SalesRecord& record) {
    const int quarter =
        (record.month - 1) / 3 + 1;

    return to_string(record.year)
        + "-Q"
        + to_string(quarter);
}


string yearGroup(const SalesRecord& record) {
    return to_string(record.year);
}


string groupDate(
    const SalesRecord& record,
    const string& grouping
) {
    if (grouping == "month") {
        return monthGroup(record);
    }

    if (grouping == "quarter") {
        return quarterGroup(record);
    }

    if (grouping == "year") {
        return yearGroup(record);
    }

    throw invalid_argument(
        "Unsupported date grouping: " + grouping
    );
}


// ============================================================================
// 6. PIVOT KEY
// ============================================================================
//
// A Pivot cell is identified by its dimensions.
//
// Example:
//
//     Rows    = Region
//     Columns = Product
//
// Cell key:
//
//     ("North", "Laptop")
//
// std::vector<string> provides a convenient composite key because vectors
// support lexicographical comparison when used in std::map.

using PivotKey = vector<string>;


// ============================================================================
// 7. RAW CELL ACCUMULATOR
// ============================================================================
//
// Instead of immediately printing a value, each cell stores sufficient
// information to calculate the requested aggregation.
//
// For SUM and COUNT, the state could be smaller than this generic design.
// The generic vector approach is intentionally educational and easy to extend.
//
// Production systems processing millions of rows may prefer streaming
// accumulators to reduce memory consumption.

struct CellAccumulator {
    map<string, vector<double>> numericValues;
    map<string, vector<string>> textValues;
};


// ============================================================================
// 8. PIVOT RESULT
// ============================================================================

struct PivotResult {
    vector<PivotKey> rowKeys;
    vector<PivotKey> columnKeys;

    map<PivotKey, map<PivotKey, map<string, double>>> cells;

    map<string, double> grandTotals;
};


// ============================================================================
// 9. PIVOT ENGINE
// ============================================================================

class PivotEngine {
private:
    const vector<SalesRecord>& records;

    bool passesFilters(
        const SalesRecord& record,
        const map<string, set<string>>& filters
    ) const {
        for (const auto& [field, allowedValues] : filters) {
            const string actualValue =
                getStringField(record, field);

            if (allowedValues.find(actualValue)
                == allowedValues.end()) {
                return false;
            }
        }

        return true;
    }

    string rowDimensionValue(
        const SalesRecord& record,
        const string& field,
        const PivotConfiguration& config
    ) const {
        if (field == "orderDate") {
            return groupDate(
                record,
                config.dateGrouping
            );
        }

        return getStringField(record, field);
    }

    string columnDimensionValue(
        const SalesRecord& record,
        const string& field,
        const PivotConfiguration& config
    ) const {
        if (field == "orderDate") {
            return groupDate(
                record,
                config.dateGrouping
            );
        }

        return getStringField(record, field);
    }

    double aggregate(
        const vector<double>& values,
        Aggregation aggregation
    ) const {
        if (aggregation == Aggregation::SUM) {
            return accumulate(
                values.begin(),
                values.end(),
                0.0
            );
        }

        if (aggregation == Aggregation::COUNT) {
            return static_cast<double>(
                values.size()
            );
        }

        if (aggregation == Aggregation::AVERAGE) {
            if (values.empty()) {
                return 0.0;
            }

            const double total =
                accumulate(
                    values.begin(),
                    values.end(),
                    0.0
                );

            return total / values.size();
        }

        if (aggregation == Aggregation::MINIMUM) {
            if (values.empty()) {
                return 0.0;
            }

            return *min_element(
                values.begin(),
                values.end()
            );
        }

        if (aggregation == Aggregation::MAXIMUM) {
            if (values.empty()) {
                return 0.0;
            }

            return *max_element(
                values.begin(),
                values.end()
            );
        }

        if (aggregation == Aggregation::DISTINCT_COUNT) {
            unordered_set<double> uniqueValues(
                values.begin(),
                values.end()
            );

            return static_cast<double>(
                uniqueValues.size()
            );
        }

        throw invalid_argument(
            "Unknown aggregation."
        );
    }

public:
    explicit PivotEngine(
        const vector<SalesRecord>& sourceRecords
    )
        : records(sourceRecords) {}

    PivotResult build(
        const PivotConfiguration& config
    ) const {
        if (config.valueFields.empty()) {
            throw invalid_argument(
                "At least one value field is required."
            );
        }

        map<PivotKey, map<PivotKey, CellAccumulator>>
            accumulators;

        set<PivotKey> rowKeySet;
        set<PivotKey> columnKeySet;

        /*
         * First phase:
         *   filter -> create dimensions -> collect measure observations
         *
         * Complexity is approximately O(N * V), where:
         *   N = source records
         *   V = number of value fields.
         */
        for (const SalesRecord& record : records) {
            if (!passesFilters(
                    record,
                    config.filters
                )) {
                continue;
            }

            PivotKey rowKey;
            PivotKey columnKey;

            for (const string& field :
                 config.rowFields) {
                rowKey.push_back(
                    rowDimensionValue(
                        record,
                        field,
                        config
                    )
                );
            }

            for (const string& field :
                 config.columnFields) {
                columnKey.push_back(
                    columnDimensionValue(
                        record,
                        field,
                        config
                    )
                );
            }

            rowKeySet.insert(rowKey);
            columnKeySet.insert(columnKey);

            CellAccumulator& cell =
                accumulators[rowKey][columnKey];

            for (const ValueField& valueField :
                 config.valueFields) {

                /*
                 * Every supported value field in this case study is numeric
                 * or countable. The order ID is represented as 1.0 per record
                 * when COUNT is requested.
                 */
                double numericValue = 0.0;

                if (valueField.name == "orderId") {
                    numericValue = 1.0;
                } else {
                    numericValue =
                        getNumericField(
                            record,
                            valueField.name
                        );
                }

                cell.numericValues[
                    valueField.label
                ].push_back(numericValue);
            }
        }

        PivotResult result;

        result.rowKeys.assign(
            rowKeySet.begin(),
            rowKeySet.end()
        );

        result.columnKeys.assign(
            columnKeySet.begin(),
            columnKeySet.end()
        );

        /*
         * Second phase:
         *   raw accumulator -> requested aggregate.
         */
        for (const auto& [rowKey, rowMap] :
             accumulators) {

            for (const auto& [columnKey, cell] :
                 rowMap) {

                for (const ValueField& valueField :
                     config.valueFields) {

                    const auto iterator =
                        cell.numericValues.find(
                            valueField.label
                        );

                    if (iterator == cell.numericValues.end()) {
                        continue;
                    }

                    result.cells[
                        rowKey
                    ][
                        columnKey
                    ][
                        valueField.label
                    ] = aggregate(
                        iterator->second,
                        valueField.aggregation
                    );
                }
            }
        }

        /*
         * Grand totals are calculated across all filtered source records.
         */
        for (const ValueField& valueField :
             config.valueFields) {

            vector<double> values;

            for (const SalesRecord& record :
                 records) {

                if (!passesFilters(
                        record,
                        config.filters
                    )) {
                    continue;
                }

                if (valueField.name == "orderId") {
                    values.push_back(1.0);
                } else {
                    values.push_back(
                        getNumericField(
                            record,
                            valueField.name
                        )
                    );
                }
            }

            result.grandTotals[
                valueField.label
            ] = aggregate(
                values,
                valueField.aggregation
            );
        }

        return result;
    }

    /*
     * Drill-down is deliberately separate from aggregation.
     *
     * A summary cell contains less information than the source dataset.
     * Drill-down identifies the source records corresponding to a particular
     * combination of dimension values.
     */
    vector<SalesRecord> drillDown(
        const string& rowField,
        const string& rowValue,
        const optional<string>& columnField,
        const optional<string>& columnValue
    ) const {
        vector<SalesRecord> result;

        for (const SalesRecord& record : records) {
            if (getStringField(
                    record,
                    rowField
                ) != rowValue) {
                continue;
            }

            if (columnField.has_value()) {
                if (!columnValue.has_value()) {
                    throw invalid_argument(
                        "Column value must be supplied with column field."
                    );
                }

                if (getStringField(
                        record,
                        *columnField
                    ) != *columnValue) {
                    continue;
                }
            }

            result.push_back(record);
        }

        return result;
    }
};


// ============================================================================
// 10. OUTPUT FUNCTIONS
// ============================================================================

string formatMoney(double value) {
    ostringstream output;

    output << fixed
           << setprecision(2)
           << value;

    return output.str();
}


string keyToString(const PivotKey& key) {
    if (key.empty()) {
        return "(All)";
    }

    ostringstream output;

    for (size_t index = 0;
         index < key.size();
         ++index) {

        if (index > 0) {
            output << " | ";
        }

        output << key[index];
    }

    return output.str();
}


void printPivot(
    const PivotResult& result,
    const string& title
) {
    cout << "\n"
         << string(90, '=')
         << "\n"
         << title
         << "\n"
         << string(90, '=')
         << "\n";

    for (const PivotKey& rowKey :
         result.rowKeys) {

        cout << "\nRow: "
             << keyToString(rowKey)
             << "\n";

        for (const PivotKey& columnKey :
             result.columnKeys) {

            cout << "  Column: "
                 << keyToString(columnKey)
                 << " -> ";

            const auto rowIterator =
                result.cells.find(rowKey);

            if (rowIterator == result.cells.end()) {
                cout << "no records\n";
                continue;
            }

            const auto columnIterator =
                rowIterator->second.find(
                    columnKey
                );

            if (columnIterator ==
                rowIterator->second.end()) {
                cout << "no records\n";
                continue;
            }

            bool first = true;

            for (const auto& [label, value] :
                 columnIterator->second) {

                if (!first) {
                    cout << ", ";
                }

                cout << label
                     << "="
                     << formatMoney(value);

                first = false;
            }

            cout << "\n";
        }
    }

    cout << "\nGrand Totals:\n";

    for (const auto& [label, value] :
         result.grandTotals) {

        cout << "  "
             << label
             << "="
             << formatMoney(value)
             << "\n";
    }
}


// ============================================================================
// 11. VALIDATION
// ============================================================================

vector<string> validateSource(
    const vector<SalesRecord>& records
) {
    vector<string> errors;
    unordered_set<string> orderIds;

    for (size_t index = 0;
         index < records.size();
         ++index) {

        const SalesRecord& record =
            records[index];

        if (record.orderId.empty()) {
            errors.push_back(
                "Blank order ID at row "
                + to_string(index + 1)
            );
        }

        if (!orderIds.insert(
                record.orderId
            ).second) {

            errors.push_back(
                "Duplicate order ID: "
                + record.orderId
            );
        }

        if (record.quantity < 0) {
            errors.push_back(
                "Negative quantity for "
                + record.orderId
            );
        }

        if (record.unitPrice < 0.0) {
            errors.push_back(
                "Negative unit price for "
                + record.orderId
            );
        }

        if (record.unitCost < 0.0) {
            errors.push_back(
                "Negative unit cost for "
                + record.orderId
            );
        }

        if (record.region.empty()) {
            errors.push_back(
                "Blank region for "
                + record.orderId
            );
        }
    }

    return errors;
}


// ============================================================================
// 12. CATEGORY SUBTOTALS
// ============================================================================
//
// Excel can show subtotals when multiple row dimensions are arranged
// hierarchically. This function demonstrates a subtotal layer independently
// from the main matrix.

map<string, double> categorySubtotals(
    const vector<SalesRecord>& records
) {
    map<string, double> totals;

    for (const SalesRecord& record :
         records) {

        totals[record.category] +=
            record.sales();
    }

    return totals;
}


// ============================================================================
// 13. MANAGEMENT REPORT
// ============================================================================

struct ManagementMetrics {
    double totalSales = 0.0;
    double totalProfit = 0.0;
    long long totalQuantity = 0;
    size_t orderCount = 0;
    double averageOrderValue = 0.0;
    double profitMargin = 0.0;
};


ManagementMetrics calculateManagementMetrics(
    const vector<SalesRecord>& records
) {
    ManagementMetrics metrics;

    for (const SalesRecord& record :
         records) {

        metrics.totalSales +=
            record.sales();

        metrics.totalProfit +=
            record.profit();

        metrics.totalQuantity +=
            record.quantity;
    }

    metrics.orderCount =
        records.size();

    if (metrics.orderCount > 0) {
        metrics.averageOrderValue =
            metrics.totalSales
            / static_cast<double>(
                metrics.orderCount
            );
    }

    if (metrics.totalSales != 0.0) {
        metrics.profitMargin =
            metrics.totalProfit
            / metrics.totalSales;
    }

    return metrics;
}


// ============================================================================
// 14. TOP-N PRODUCT ANALYSIS
// ============================================================================

vector<pair<string, double>> topProducts(
    const vector<SalesRecord>& records,
    size_t n
) {
    map<string, double> totals;

    for (const SalesRecord& record :
         records) {

        totals[record.product] +=
            record.sales();
    }

    vector<pair<string, double>> ranked(
        totals.begin(),
        totals.end()
    );

    sort(
        ranked.begin(),
        ranked.end(),
        [](
            const auto& left,
            const auto& right
        ) {
            return left.second > right.second;
        }
    );

    if (ranked.size() > n) {
        ranked.resize(n);
    }

    return ranked;
}


// ============================================================================
// 15. PERCENTAGE OF GRAND TOTAL
// ============================================================================

map<string, double> percentageOfTotal(
    const map<string, double>& values
) {
    const double grandTotal =
        accumulate(
            values.begin(),
            values.end(),
            0.0,
            [](
                double current,
                const auto& item
            ) {
                return current + item.second;
            }
        );

    map<string, double> percentages;

    for (const auto& [key, value] :
         values) {

        percentages[key] =
            grandTotal == 0.0
                ? 0.0
                : value / grandTotal * 100.0;
    }

    return percentages;
}


// ============================================================================
// 16. FILTERED RECORD EXTRACTION
// ============================================================================

vector<SalesRecord> filterByCustomerType(
    const vector<SalesRecord>& records,
    const string& customerType
) {
    vector<SalesRecord> filtered;

    copy_if(
        records.begin(),
        records.end(),
        back_inserter(filtered),
        [&customerType](
            const SalesRecord& record
        ) {
            return record.customerType
                == customerType;
        }
    );

    return filtered;
}


// ============================================================================
// 17. TESTS
// ============================================================================

void testSalesCalculation() {
    SalesRecord record{
        "TEST",
        "2025-01-01",
        2025,
        1,
        "Test",
        "Tester",
        "Product",
        "Category",
        3,
        100.0,
        60.0,
        "Retail"
    };

    assert(
        fabs(record.sales() - 300.0)
        < 1e-9
    );

    assert(
        fabs(record.cost() - 180.0)
        < 1e-9
    );

    assert(
        fabs(record.profit() - 120.0)
        < 1e-9
    );
}


void testPivotGrandTotal(
    const vector<SalesRecord>& records
) {
    PivotEngine engine(records);

    PivotConfiguration configuration;

    configuration.rowFields = {
        "region"
    };

    configuration.valueFields = {
        {
            "sales",
            Aggregation::SUM,
            "Total Sales"
        }
    };

    const PivotResult result =
        engine.build(configuration);

    double expected = 0.0;

    for (const SalesRecord& record :
         records) {
        expected += record.sales();
    }

    assert(
        fabs(
            result.grandTotals.at(
                "Total Sales"
            ) - expected
        ) < 1e-9
    );
}


void testFiltering(
    const vector<SalesRecord>& records
) {
    const auto filtered =
        filterByCustomerType(
            records,
            "Corporate"
        );

    assert(!filtered.empty());

    for (const SalesRecord& record :
         filtered) {

        assert(
            record.customerType
            == "Corporate"
        );
    }
}


void testDrillDown(
    const vector<SalesRecord>& records
) {
    PivotEngine engine(records);

    const auto drilled =
        engine.drillDown(
            "region",
            "North",
            string("product"),
            string("Laptop")
        );

    for (const SalesRecord& record :
         drilled) {

        assert(
            record.region == "North"
        );

        assert(
            record.product == "Laptop"
        );
    }
}


void runTests(
    const vector<SalesRecord>& records
) {
    testSalesCalculation();
    testPivotGrandTotal(records);
    testFiltering(records);
    testDrillDown(records);

    cout << "\nAll C++ tests passed.\n";
}


// ============================================================================
// 18. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        const vector<SalesRecord> records =
            createSourceData();

        // --------------------------------------------------------------------
        // Validate the source dataset before building analytical reports.
        // --------------------------------------------------------------------

        cout << string(90, '=')
             << "\nSource Validation\n"
             << string(90, '=')
             << "\n";

        const vector<string> errors =
            validateSource(records);

        if (errors.empty()) {
            cout << "Source data passed validation.\n";
        } else {
            for (const string& error :
                 errors) {
                cout << "ERROR: "
                     << error
                     << "\n";
            }

            return 1;
        }


        // --------------------------------------------------------------------
        // Basic Pivot:
        //
        // Rows    = Region
        // Values  = SUM(Sales)
        // --------------------------------------------------------------------

        PivotEngine engine(records);

        PivotConfiguration basic;

        basic.rowFields = {
            "region"
        };

        basic.valueFields = {
            {
                "sales",
                Aggregation::SUM,
                "Total Sales"
            }
        };

        PivotResult basicResult =
            engine.build(basic);

        printPivot(
            basicResult,
            "Case Study 1 - Sales by Region"
        );


        // --------------------------------------------------------------------
        // Two-dimensional Pivot:
        //
        // Rows    = Region
        // Columns = Product
        // Values  = SUM(Sales)
        //
        // This represents the central matrix structure of a Pivot Table.
        // --------------------------------------------------------------------

        PivotConfiguration matrix;

        matrix.rowFields = {
            "region"
        };

        matrix.columnFields = {
            "product"
        };

        matrix.valueFields = {
            {
                "sales",
                Aggregation::SUM,
                "Total Sales"
            }
        };

        PivotResult matrixResult =
            engine.build(matrix);

        printPivot(
            matrixResult,
            "Case Study 2 - Region x Product"
        );


        // --------------------------------------------------------------------
        // Multiple measures:
        //
        // Values:
        //   SUM(Sales)
        //   SUM(Profit)
        //   AVERAGE(Quantity)
        // --------------------------------------------------------------------

        PivotConfiguration metrics;

        metrics.rowFields = {
            "category"
        };

        metrics.valueFields = {
            {
                "sales",
                Aggregation::SUM,
                "Total Sales"
            },
            {
                "profit",
                Aggregation::SUM,
                "Total Profit"
            },
            {
                "quantity",
                Aggregation::AVERAGE,
                "Average Quantity"
            }
        };

        PivotResult metricsResult =
            engine.build(metrics);

        printPivot(
            metricsResult,
            "Case Study 3 - Category Metrics"
        );


        // --------------------------------------------------------------------
        // Filter:
        //
        // Corporate customers only.
        //
        // The filter is applied before aggregation, which is essential to
        // obtaining a correct filtered Pivot result.
        // --------------------------------------------------------------------

        PivotConfiguration corporate;

        corporate.rowFields = {
            "region"
        };

        corporate.columnFields = {
            "category"
        };

        corporate.valueFields = {
            {
                "sales",
                Aggregation::SUM,
                "Corporate Sales"
            },
            {
                "profit",
                Aggregation::SUM,
                "Corporate Profit"
            }
        };

        corporate.filters["customerType"] = {
            "Corporate"
        };

        PivotResult corporateResult =
            engine.build(corporate);

        printPivot(
            corporateResult,
            "Case Study 4 - Corporate Region x Category"
        );


        // --------------------------------------------------------------------
        // Date grouping:
        //
        // Rows = Order Date
        // Grouping = Quarter
        // Values = Sales
        //
        // Excel can group date fields into months, quarters, and years.
        // --------------------------------------------------------------------

        PivotConfiguration quarterly;

        quarterly.rowFields = {
            "orderDate"
        };

        quarterly.dateGrouping =
            "quarter";

        quarterly.valueFields = {
            {
                "sales",
                Aggregation::SUM,
                "Quarterly Sales"
            }
        };

        PivotResult quarterlyResult =
            engine.build(quarterly);

        printPivot(
            quarterlyResult,
            "Case Study 5 - Quarterly Sales"
        );


        // --------------------------------------------------------------------
        // Calculated-field concept:
        //
        // Profit = Sales - Cost
        //
        // The SalesRecord::profit method acts as a calculated measure.
        // A real Excel calculated field is configured through the Pivot Table
        // and has specific rules and limitations.
        // --------------------------------------------------------------------

        PivotConfiguration calculated;

        calculated.rowFields = {
            "region"
        };

        calculated.valueFields = {
            {
                "sales",
                Aggregation::SUM,
                "Total Sales"
            },
            {
                "profit",
                Aggregation::SUM,
                "Calculated Profit"
            },
            {
                "margin",
                Aggregation::AVERAGE,
                "Average Margin"
            }
        };

        PivotResult calculatedResult =
            engine.build(calculated);

        printPivot(
            calculatedResult,
            "Case Study 6 - Calculated Business Measures"
        );


        // --------------------------------------------------------------------
        // Drill-down:
        //
        // Select a Pivot cell represented by:
        //
        //   Region = North
        //   Product = Laptop
        //
        // Return the contributing source transactions.
        // --------------------------------------------------------------------

        const vector<SalesRecord> drilledRecords =
            engine.drillDown(
                "region",
                "North",
                string("product"),
                string("Laptop")
            );

        cout << "\n"
             << string(90, '=')
             << "\n"
             << "Case Study 7 - Drill-Down: North + Laptop"
             << "\n"
             << string(90, '=')
             << "\n";

        for (const SalesRecord& record :
             drilledRecords) {

            cout << record.orderId
                 << " | "
                 << record.orderDate
                 << " | "
                 << record.region
                 << " | "
                 << record.product
                 << " | quantity="
                 << record.quantity
                 << " | sales="
                 << formatMoney(record.sales())
                 << " | profit="
                 << formatMoney(record.profit())
                 << "\n";
        }


        // --------------------------------------------------------------------
        // Subtotals.
        // --------------------------------------------------------------------

        const auto subtotals =
            categorySubtotals(records);

        cout << "\n"
             << string(90, '=')
             << "\n"
             << "Case Study 8 - Category Subtotals"
             << "\n"
             << string(90, '=')
             << "\n";

        for (const auto& [category, value] :
             subtotals) {

            cout << category
                 << ": "
                 << formatMoney(value)
                 << "\n";
        }


        // --------------------------------------------------------------------
        // Percentage of total.
        // --------------------------------------------------------------------

        const auto percentages =
            percentageOfTotal(subtotals);

        cout << "\n"
             << string(90, '=')
             << "\n"
             << "Case Study 9 - Percentage of Grand Total"
             << "\n"
             << string(90, '=')
             << "\n";

        for (const auto& [category, percentage] :
             percentages) {

            cout << category
                 << ": "
                 << fixed
                 << setprecision(2)
                 << percentage
                 << "%\n";
        }


        // --------------------------------------------------------------------
        // Top-N analysis.
        // --------------------------------------------------------------------

        const auto topThree =
            topProducts(records, 3);

        cout << "\n"
             << string(90, '=')
             << "\n"
             << "Case Study 10 - Top Three Products"
             << "\n"
             << string(90, '=')
             << "\n";

        for (size_t index = 0;
             index < topThree.size();
             ++index) {

            cout << index + 1
                 << ". "
                 << topThree[index].first
                 << ": "
                 << formatMoney(
                        topThree[index].second
                    )
                 << "\n";
        }


        // --------------------------------------------------------------------
        // Management metrics.
        // --------------------------------------------------------------------

        const ManagementMetrics management =
            calculateManagementMetrics(records);

        cout << "\n"
             << string(90, '=')
             << "\n"
             << "Case Study 11 - Management Metrics"
             << "\n"
             << string(90, '=')
             << "\n";

        cout << "Total Sales: "
             << formatMoney(
                    management.totalSales
                )
             << "\n";

        cout << "Total Profit: "
             << formatMoney(
                    management.totalProfit
                )
             << "\n";

        cout << "Total Quantity: "
             << management.totalQuantity
             << "\n";

        cout << "Order Count: "
             << management.orderCount
             << "\n";

        cout << "Average Order Value: "
             << formatMoney(
                    management.averageOrderValue
                )
             << "\n";

        cout << "Profit Margin: "
             << fixed
             << setprecision(2)
             << management.profitMargin * 100.0
             << "%\n";


        // --------------------------------------------------------------------
        // Tests.
        // --------------------------------------------------------------------

        runTests(records);

        /*
         * Architectural observations:
         *
         * 1. Filtering happens before aggregation.
         * 2. Dimensions define the coordinate system of the Pivot.
         * 3. Measures define what is calculated at each coordinate.
         * 4. Grouping transforms raw dimensions into analytical buckets.
         * 5. Subtotals summarize hierarchical dimensions.
         * 6. Grand totals summarize the complete filtered dataset.
         * 7. Drill-down maps a summarized coordinate back to source records.
         *
         * Complexity:
         *
         * Let N be the number of source records and V the number of measures.
         *
         * Main accumulation:
         *     approximately O(N * V)
         *
         * Sorting unique row and column keys:
         *     approximately O(R log R + C log C)
         *
         * where:
         *     R = number of unique row keys
         *     C = number of unique column keys
         *
         * Memory:
         *     approximately proportional to the number of distinct Pivot cells
         *     and stored observations.
         *
         * A production-scale implementation can reduce memory consumption by
         * maintaining streaming accumulators:
         *
         *     SUM       -> running sum
         *     COUNT     -> running count
         *     AVERAGE   -> running sum + count
         *     MIN       -> running minimum
         *     MAX       -> running maximum
         *
         * Distinct count is more complicated because it requires tracking
         * uniqueness, which can become memory-intensive.
         *
         * Security:
         *
         * Pivot-style summaries can reveal sensitive information even when
         * raw records are not directly displayed. Drill-down is particularly
         * important because it can expose the source rows behind a summary.
         * Access controls and data minimization therefore remain relevant.
         */

        return 0;
    }
    catch (const exception& error) {
        cerr << "Application error: "
             << error.what()
             << "\n";

        return 1;
    }
}
