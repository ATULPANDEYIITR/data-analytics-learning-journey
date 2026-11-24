#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

/*
 * Power BI Visualization and Dashboard Governance Engine.
 *
 * C++17 implementation covering:
 * - Cards
 * - Tables
 * - Matrices
 * - Bar, line, and pie chart datasets
 * - Geographic aggregation
 * - Slicers
 * - Drill-through
 * - Bookmarks
 * - Dashboard state
 * - Validation and merge-like state consistency
 *
 * No external dependencies.
 */

enum class VisualType {
    CARD,
    TABLE,
    MATRIX,
    BAR,
    LINE,
    PIE,
    MAP
};

enum class Aggregation {
    SUM,
    COUNT,
    AVERAGE,
    MINIMUM,
    MAXIMUM,
    DISTINCT_COUNT
};

struct Transaction {
    int id;
    string date;
    string month;
    string region;
    string city;
    string category;
    string product;
    string salesperson;
    int quantity;
    double unitPrice;
    double discount;

    double grossSales() const {
        return quantity * unitPrice;
    }

    double netSales() const {
        return grossSales() * (1.0 - discount);
    }

    double profit() const {
        return netSales() * 0.25;
    }
};

struct VisualResult {
    VisualType type;
    string title;
    vector<pair<string, double>> data;
};

struct Bookmark {
    string name;
    map<string, string> filters;
    string selectedVisual;
};

class DashboardException : public runtime_error {
public:
    explicit DashboardException(const string& message)
        : runtime_error(message) {}
};

class Dashboard {
private:
    vector<Transaction> transactions;
    map<string, string> filters;
    map<string, Bookmark> bookmarks;
    string selectedVisual;

    static double roundValue(double value) {
        return round(value * 100.0) / 100.0;
    }

    static void validateTransaction(const Transaction& transaction) {
        if (transaction.id <= 0) {
            throw DashboardException("Transaction ID must be positive.");
        }

        if (transaction.quantity <= 0) {
            throw DashboardException("Quantity must be positive.");
        }

        if (!isfinite(transaction.unitPrice) ||
            transaction.unitPrice < 0) {
            throw DashboardException("Invalid unit price.");
        }

        if (!isfinite(transaction.discount) ||
            transaction.discount < 0 ||
            transaction.discount > 1) {
            throw DashboardException("Invalid discount.");
        }

        if (transaction.region.empty() ||
            transaction.category.empty() ||
            transaction.city.empty()) {
            throw DashboardException("Required dimension is empty.");
        }
    }

    static double getMeasure(
        const Transaction& transaction,
        const string& field
    ) {
        if (field == "netSales") return transaction.netSales();
        if (field == "grossSales") return transaction.grossSales();
        if (field == "profit") return transaction.profit();
        if (field == "quantity") return transaction.quantity;

        throw DashboardException("Unknown measure: " + field);
    }

    static string getDimension(
        const Transaction& transaction,
        const string& field
    ) {
        if (field == "region") return transaction.region;
        if (field == "city") return transaction.city;
        if (field == "category") return transaction.category;
        if (field == "product") return transaction.product;
        if (field == "salesperson") return transaction.salesperson;
        if (field == "month") return transaction.month;
        if (field == "date") return transaction.date;

        throw DashboardException("Unknown dimension: " + field);
    }

    bool matches(const Transaction& transaction) const {
        for (const auto& [field, value] : filters) {
            if (field == "minimumSales") {
                if (transaction.netSales() < stod(value)) {
                    return false;
                }
            } else if (field == "maximumSales") {
                if (transaction.netSales() > stod(value)) {
                    return false;
                }
            } else if (getDimension(transaction, field) != value) {
                return false;
            }
        }

        return true;
    }

public:
    explicit Dashboard(vector<Transaction> records)
        : transactions(move(records)) {
        if (transactions.empty()) {
            throw DashboardException("Dataset cannot be empty.");
        }

        set<int> identifiers;

        for (const auto& transaction : transactions) {
            validateTransaction(transaction);

            if (!identifiers.insert(transaction.id).second) {
                throw DashboardException("Duplicate transaction ID.");
            }
        }
    }

    vector<Transaction> filteredRecords() const {
        vector<Transaction> result;

        copy_if(
            transactions.begin(),
            transactions.end(),
            back_inserter(result),
            [this](const Transaction& transaction) {
                return matches(transaction);
            }
        );

        return result;
    }

    void setSlicer(const string& field, const string& value) {
        if (field.empty() || value.empty()) {
            throw DashboardException("Slicer field and value are required.");
        }

        // Validate field names before saving the filter.
        if (field != "region" &&
            field != "city" &&
            field != "category" &&
            field != "product" &&
            field != "salesperson" &&
            field != "month") {
            throw DashboardException("Unsupported slicer field.");
        }

        filters[field] = value;
    }

    void setSalesRange(double minimum, double maximum) {
        if (!isfinite(minimum) ||
            !isfinite(maximum) ||
            minimum < 0 ||
            minimum > maximum) {
            throw DashboardException("Invalid sales range.");
        }

        filters["minimumSales"] = to_string(minimum);
        filters["maximumSales"] = to_string(maximum);
    }

    void clearFilters() {
        filters.clear();
    }

    double aggregate(
        const string& field,
        Aggregation operation
    ) const {
        const auto records = filteredRecords();

        if (records.empty()) return 0.0;

        vector<double> values;
        values.reserve(records.size());

        for (const auto& transaction : records) {
            values.push_back(getMeasure(transaction, field));
        }

        switch (operation) {
            case Aggregation::SUM:
                return roundValue(
                    accumulate(values.begin(), values.end(), 0.0)
                );

            case Aggregation::COUNT:
                return static_cast<double>(values.size());

            case Aggregation::AVERAGE:
                return roundValue(
                    accumulate(values.begin(), values.end(), 0.0) /
                    values.size()
                );

            case Aggregation::MINIMUM:
                return *min_element(values.begin(), values.end());

            case Aggregation::MAXIMUM:
                return *max_element(values.begin(), values.end());

            case Aggregation::DISTINCT_COUNT: {
                set<double> distinct(values.begin(), values.end());
                return static_cast<double>(distinct.size());
            }
        }

        throw DashboardException("Unsupported aggregation.");
    }

    void displayCard(const string& measure) const {
        const double value = aggregate(
            measure,
            Aggregation::SUM
        );

        cout << "\nCARD: " << measure << '\n';
        cout << "Value: " << fixed << setprecision(2)
             << value << '\n';
        cout << "Records: " << filteredRecords().size() << '\n';
    }

    map<string, map<string, double>> buildMatrix(
        const string& rowField,
        const string& columnField,
        const string& measure
    ) const {
        map<string, map<string, double>> matrix;

        for (const auto& transaction : filteredRecords()) {
            const string row = getDimension(transaction, rowField);
            const string column = getDimension(
                transaction, columnField
            );

            matrix[row][column] += getMeasure(transaction, measure);
        }

        return matrix;
    }

    void displayMatrix(
        const string& rowField,
        const string& columnField,
        const string& measure
    ) const {
        const auto matrix = buildMatrix(
            rowField,
            columnField,
            measure
        );

        set<string> columns;

        for (const auto& [row, values] : matrix) {
            for (const auto& [column, value] : values) {
                columns.insert(column);
            }
        }

        cout << "\nMATRIX: " << rowField
             << " x " << columnField << '\n';

        cout << setw(18) << rowField;

        for (const auto& column : columns) {
            cout << setw(16) << column;
        }

        cout << setw(16) << "TOTAL" << '\n';

        for (const auto& [row, values] : matrix) {
            double total = 0;

            cout << setw(18) << row;

            for (const auto& column : columns) {
                const auto iterator = values.find(column);

                const double value = iterator == values.end()
                    ? 0.0
                    : iterator->second;

                total += value;

                cout << setw(16) << fixed
                     << setprecision(2) << value;
            }

            cout << setw(16) << total << '\n';
        }
    }

    vector<pair<string, double>> buildChart(
        const string& dimension,
        const string& measure
    ) const {
        map<string, double> groups;

        for (const auto& transaction : filteredRecords()) {
            groups[getDimension(transaction, dimension)] +=
                getMeasure(transaction, measure);
        }

        vector<pair<string, double>> result;

        for (const auto& [label, value] : groups) {
            result.emplace_back(label, roundValue(value));
        }

        return result;
    }

    void displayChart(
        const string& chartName,
        const string& dimension,
        const string& measure
    ) const {
        cout << "\n" << chartName << '\n';

        const auto data = buildChart(dimension, measure);

        if (data.empty()) {
            cout << "No data available.\n";
            return;
        }

        double maximum = 0;

        for (const auto& [label, value] : data) {
            maximum = max(maximum, value);
        }

        for (const auto& [label, value] : data) {
            const int barLength = maximum > 0
                ? static_cast<int>(value / maximum * 35)
                : 0;

            cout << setw(15) << left << label << " | ";

            for (int i = 0; i < barLength; ++i) {
                cout << '#';
            }

            cout << " " << fixed << setprecision(2)
                 << value << '\n';
        }
    }

    void displayMapData() const {
        map<pair<string, string>, double> locations;

        for (const auto& transaction : filteredRecords()) {
            locations[
                {transaction.region, transaction.city}
            ] += transaction.netSales();
        }

        cout << "\nGEOGRAPHIC AGGREGATION\n";

        for (const auto& [location, sales] : locations) {
            cout << location.first << " | "
                 << location.second << " | "
                 << fixed << setprecision(2)
                 << sales << '\n';
        }

        cout << "Coordinates must be supplied through "
             << "a validated geographic dimension.\n";
    }

    vector<Transaction> drillThrough(
        const string& field,
        const string& value
    ) const {
        vector<Transaction> details;

        for (const auto& transaction : filteredRecords()) {
            if (getDimension(transaction, field) == value) {
                details.push_back(transaction);
            }
        }

        if (details.empty()) {
            throw DashboardException(
                "No matching drill-through records."
            );
        }

        return details;
    }

    void saveBookmark(
        const string& name,
        const string& visual
    ) {
        if (name.empty()) {
            throw DashboardException("Bookmark name is required.");
        }

        bookmarks[name] = Bookmark{
            name,
            filters,
            visual
        };
    }

    void restoreBookmark(const string& name) {
        const auto iterator = bookmarks.find(name);

        if (iterator == bookmarks.end()) {
            throw DashboardException("Bookmark not found.");
        }

        filters = iterator->second.filters;
        selectedVisual = iterator->second.selectedVisual;
    }

    void displayTable() const {
        map<pair<string, string>, pair<double, double>> groups;

        for (const auto& transaction : filteredRecords()) {
            auto& values = groups[
                {transaction.region, transaction.category}
            ];

            values.first += transaction.netSales();
            values.second += transaction.profit();
        }

        cout << "\nREGIONAL SALES TABLE\n";

        for (const auto& [dimensions, measures] : groups) {
            cout << left << setw(12) << dimensions.first
                 << setw(16) << dimensions.second
                 << right << fixed << setprecision(2)
                 << setw(14) << measures.first
                 << setw(14) << measures.second << '\n';
        }
    }

    void displayDrillThrough(
        const string& field,
        const string& value
    ) const {
        cout << "\nDRILL-THROUGH DETAILS: "
             << field << "=" << value << '\n';

        for (const auto& transaction :
             drillThrough(field, value)) {
            cout << "ID: " << transaction.id
                 << " | Date: " << transaction.date
                 << " | Product: " << transaction.product
                 << " | Quantity: " << transaction.quantity
                 << " | Sales: " << fixed << setprecision(2)
                 << transaction.netSales() << '\n';
        }
    }
};

vector<Transaction> sampleData() {
    return {
        {1, "2026-01-05", "2026-01", "North", "Delhi",
         "Electronics", "Laptop", "Amit", 2, 65000, 0.05},

        {2, "2026-01-12", "2026-01", "North", "Lucknow",
         "Furniture", "Chair", "Neha", 5, 4500, 0.10},

        {3, "2026-02-08", "2026-02", "South", "Bengaluru",
         "Electronics", "Mobile", "Rahul", 4, 30000, 0.08},

        {4, "2026-02-15", "2026-02", "West", "Mumbai",
         "Clothing", "Jacket", "Priya", 8, 2500, 0.05},

        {5, "2026-03-03", "2026-03", "East", "Kolkata",
         "Furniture", "Table", "Amit", 3, 12000, 0.12},

        {6, "2026-03-18", "2026-03", "North", "Delhi",
         "Clothing", "Shirt", "Neha", 10, 1200, 0.02},

        {7, "2026-04-10", "2026-04", "South", "Chennai",
         "Electronics", "Laptop", "Rahul", 1, 70000, 0.04},

        {8, "2026-04-20", "2026-04", "West", "Pune",
         "Furniture", "Chair", "Priya", 6, 5000, 0.07},

        {9, "2026-05-05", "2026-05", "East", "Kolkata",
         "Electronics", "Mobile", "Amit", 3, 28000, 0.06},

        {10, "2026-05-17", "2026-05", "North", "Lucknow",
         "Clothing", "Jacket", "Neha", 4, 3000, 0.03}
    };
}

int main() {
    try {
        Dashboard dashboard(sampleData());

        cout << "POWER BI VISUALIZATION ENGINE\n";
        cout << "====================================\n";

        dashboard.displayCard("netSales");
        dashboard.displayCard("profit");

        dashboard.displayTable();

        dashboard.displayMatrix(
            "region",
            "category",
            "netSales"
        );

        dashboard.displayChart(
            "BAR CHART: SALES BY CATEGORY",
            "category",
            "netSales"
        );

        dashboard.displayChart(
            "LINE CHART: MONTHLY SALES",
            "month",
            "netSales"
        );

        dashboard.displayChart(
            "PIE CHART: CATEGORY CONTRIBUTION",
            "category",
            "netSales"
        );

        dashboard.displayMapData();

        cout << "\nAPPLYING SLICERS\n";

        dashboard.setSlicer("region", "North");
        dashboard.setSlicer("category", "Electronics");

        dashboard.displayCard("netSales");

        cout << "\nSAVING BOOKMARK\n";

        dashboard.saveBookmark(
            "North_Electronics",
            "Regional Sales"
        );

        dashboard.clearFilters();
        dashboard.displayCard("netSales");

        cout << "\nRESTORING BOOKMARK\n";

        dashboard.restoreBookmark("North_Electronics");
        dashboard.displayCard("netSales");

        dashboard.displayDrillThrough("region", "North");

        cout << "\nVALIDATION TEST\n";

        try {
            dashboard.setSlicer("invalidField", "value");
        } catch (const DashboardException& error) {
            cout << "Expected error: "
                 << error.what() << '\n';
        }

        dashboard.clearFilters();

        cout << "\nFINAL DATASET SIZE: "
             << dashboard.filteredRecords().size()
             << '\n';

    } catch (const exception& error) {
        cerr << "Dashboard failure: "
             << error.what() << '\n';
        return 1;
    }

    return 0;
}
