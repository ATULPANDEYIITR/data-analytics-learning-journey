#include <algorithm>
#include <cassert>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * DAX FUNDAMENTALS: C++17 ANALYTICAL EVALUATION ENGINE
 *
 * Implements selected concepts:
 * - Measures
 * - Calculated columns
 * - Calculated tables
 * - Row context
 * - Filter context
 * - Context transition
 * - CALCULATE
 * - FILTER
 * - ALL
 * - VALUES
 * - DISTINCTCOUNT
 * - SUMX
 *
 * The engine is an educational model of selected DAX
 * behaviors, not a complete DAX interpreter.
 */

using namespace std;

struct Product {
    int id;
    string name;
    string category;
    double price;
};

struct Sale {
    int id;
    int productId;
    string date;
    int quantity;
    double unitCost;
};

struct CalculatedColumn {
    int saleId;
    double revenue;
    double cost;
    double profit;
    string profitability;
};

struct CalculatedCategory {
    string category;
    int productCount;
};

class DAXException : public runtime_error {
public:
    explicit DAXException(const string& message)
        : runtime_error(message) {}
};

struct EvaluationContext {
    map<string, set<string>> filters;
    map<string, string> rowContext;
};

class DAXEngine {
private:
    unordered_map<int, Product> products;
    vector<Sale> sales;

    string valueOf(const Sale& sale, const string& column) const {
        const Product& product = products.at(sale.productId);

        if (column == "Sales.ID")
            return to_string(sale.id);

        if (column == "Sales.ProductID")
            return to_string(sale.productId);

        if (column == "Sales.Date")
            return sale.date;

        if (column == "Sales.Quantity")
            return to_string(sale.quantity);

        if (column == "Product.Name")
            return product.name;

        if (column == "Product.Category")
            return product.category;

        if (column == "Product.Price")
            return to_string(product.price);

        throw DAXException("Unknown column: " + column);
    }

    bool matches(
        const Sale& sale,
        const EvaluationContext& context
    ) const {
        for (const auto& [column, allowed] : context.filters) {
            if (allowed.find(valueOf(sale, column)) == allowed.end()) {
                return false;
            }
        }

        return true;
    }

public:
    DAXEngine(
        vector<Product> productData,
        vector<Sale> salesData
    ) : sales(move(salesData)) {

        for (const Product& product : productData) {
            if (product.id <= 0 || product.price < 0) {
                throw DAXException("Invalid product.");
            }

            if (!products.emplace(product.id, product).second) {
                throw DAXException("Duplicate product ID.");
            }
        }

        set<int> saleIds;

        for (const Sale& sale : sales) {
            if (!saleIds.insert(sale.id).second) {
                throw DAXException("Duplicate sale ID.");
            }

            if (products.find(sale.productId) == products.end()) {
                throw DAXException("Unknown product reference.");
            }

            if (sale.quantity < 0 || sale.unitCost < 0) {
                throw DAXException("Invalid sale values.");
            }
        }
    }

    vector<Sale> rows(const EvaluationContext& context) const {
        vector<Sale> result;

        for (const Sale& sale : sales) {
            if (matches(sale, context)) {
                result.push_back(sale);
            }
        }

        return result;
    }

    // --------------------------------------------------------
    // Measures
    // --------------------------------------------------------

    double totalSales(const EvaluationContext& context) const {
        double total = 0;

        for (const Sale& sale : rows(context)) {
            total += products.at(sale.productId).price * sale.quantity;
        }

        return total;
    }

    double totalCost(const EvaluationContext& context) const {
        double total = 0;

        for (const Sale& sale : rows(context)) {
            total += sale.unitCost * sale.quantity;
        }

        return total;
    }

    double totalProfit(const EvaluationContext& context) const {
        return totalSales(context) - totalCost(context);
    }

    long long totalQuantity(const EvaluationContext& context) const {
        long long total = 0;

        for (const Sale& sale : rows(context)) {
            total += sale.quantity;
        }

        return total;
    }

    int transactionCount(const EvaluationContext& context) const {
        return static_cast<int>(rows(context).size());
    }

    optional<double> profitMargin(
        const EvaluationContext& context
    ) const {
        double revenue = totalSales(context);

        if (revenue == 0) {
            return nullopt;
        }

        return totalProfit(context) / revenue * 100.0;
    }

    // --------------------------------------------------------
    // CALCULATE and context transition
    // --------------------------------------------------------

    EvaluationContext calculateContext(
        const EvaluationContext& original,
        const map<string, set<string>>& replacementFilters,
        const set<string>& removeFilters
    ) const {

        EvaluationContext result = original;

        for (const string& column : removeFilters) {
            result.filters.erase(column);
        }

        for (const auto& [column, values] : replacementFilters) {
            result.filters[column] = values;
        }

        // Convert row-context values into filter-context values.
        for (const auto& [column, value] : original.rowContext) {
            result.filters[column] = {value};
        }

        return result;
    }

    double calculateSales(
        const EvaluationContext& original,
        const map<string, set<string>>& replacementFilters = {},
        const set<string>& removeFilters = {}
    ) const {
        EvaluationContext context = calculateContext(
            original,
            replacementFilters,
            removeFilters
        );

        return totalSales(context);
    }

    // --------------------------------------------------------
    // FILTER and SUMX
    // --------------------------------------------------------

    vector<Sale> filter(
        const EvaluationContext& context,
        const function<bool(const Sale&, const Product&)>& predicate
    ) const {
        vector<Sale> result;

        for (const Sale& sale : rows(context)) {
            if (predicate(sale, products.at(sale.productId))) {
                result.push_back(sale);
            }
        }

        return result;
    }

    double sumX(
        const vector<Sale>& input,
        const function<double(const Sale&)>& expression
    ) const {
        double total = 0;

        for (const Sale& sale : input) {
            double value = expression(sale);

            if (!isfinite(value)) {
                throw DAXException("Invalid SUMX expression result.");
            }

            total += value;
        }

        return total;
    }

    // --------------------------------------------------------
    // Calculated columns
    // --------------------------------------------------------

    vector<CalculatedColumn> calculatedColumns() const {
        vector<CalculatedColumn> result;

        for (const Sale& sale : sales) {
            const Product& product = products.at(sale.productId);

            double revenue = product.price * sale.quantity;
            double cost = sale.unitCost * sale.quantity;

            result.push_back({
                sale.id,
                revenue,
                cost,
                revenue - cost,
                product.price > sale.unitCost * 1.5
                    ? "High"
                    : "Standard"
            });
        }

        return result;
    }

    // --------------------------------------------------------
    // Calculated tables
    // --------------------------------------------------------

    vector<CalculatedCategory> calculatedCategoryTable() const {
        map<string, int> counts;

        for (const auto& [id, product] : products) {
            counts[product.category]++;
        }

        vector<CalculatedCategory> result;

        for (const auto& [category, count] : counts) {
            result.push_back({category, count});
        }

        return result;
    }

    // --------------------------------------------------------
    // VALUES and DISTINCTCOUNT
    // --------------------------------------------------------

    set<string> values(
        const string& column,
        const EvaluationContext& context
    ) const {
        set<string> result;

        for (const Sale& sale : rows(context)) {
            result.insert(valueOf(sale, column));
        }

        return result;
    }

    size_t distinctCount(
        const string& column,
        const EvaluationContext& context
    ) const {
        return values(column, context).size();
    }

    void printCategoryReport() const {
        set<string> categories;

        for (const auto& [id, product] : products) {
            categories.insert(product.category);
        }

        cout << "\nCATEGORY REPORT\n";

        for (const string& category : categories) {
            EvaluationContext context;
            context.filters["Product.Category"] = {category};

            cout << left << setw(15) << category
                 << " Sales=" << totalSales(context)
                 << " Quantity=" << totalQuantity(context)
                 << " Profit=" << totalProfit(context);

            auto margin = profitMargin(context);

            if (margin) {
                cout << " Margin=" << *margin << "%";
            } else {
                cout << " Margin=N/A";
            }

            cout << '\n';
        }
    }

    const unordered_map<int, Product>& productData() const {
        return products;
    }

    const vector<Sale>& salesData() const {
        return sales;
    }
};

int main() {
    try {
        vector<Product> products = {
            {1, "Laptop", "Electronics", 1000},
            {2, "Phone", "Electronics", 500},
            {3, "Desk", "Furniture", 300},
            {4, "Chair", "Furniture", 200},
            {5, "Notebook", "Stationery", 50}
        };

        vector<Sale> sales = {
            {101, 1, "2026-01-10", 2, 700},
            {102, 2, "2026-01-11", 4, 300},
            {103, 3, "2026-01-12", 3, 180},
            {104, 4, "2026-01-13", 5, 120},
            {105, 5, "2026-01-14", 10, 20},
            {106, 1, "2026-02-10", 1, 700},
            {107, 2, "2026-02-11", 2, 300},
            {108, 3, "2026-02-12", 4, 180},
            {109, 4, "2026-02-13", 3, 120},
            {110, 5, "2026-02-14", 5, 20}
        };

        DAXEngine engine(products, sales);

        EvaluationContext all;

        assert(engine.totalSales(all) == 4995);
        assert(engine.totalCost(all) == 2840);
        assert(engine.totalProfit(all) == 2155);
        assert(engine.totalQuantity(all) == 39);
        assert(engine.transactionCount(all) == 10);

        EvaluationContext electronics;
        electronics.filters["Product.Category"] = {"Electronics"};

        assert(engine.totalSales(electronics) == 3000);
        assert(engine.totalQuantity(electronics) == 9);

        assert(
            engine.calculateSales(
                electronics,
                {},
                {"Product.Category"}
            ) == 4995
        );

        assert(engine.distinctCount(
            "Product.Category",
            all
        ) == 3);

        vector<Sale> filtered = engine.filter(
            all,
            [](const Sale&, const Product& product) {
                return product.category == "Electronics";
            }
        );

        assert(engine.sumX(
            filtered,
            [&engine](const Sale& sale) {
                return engine.productData().at(sale.productId).price
                    * sale.quantity;
            }
        ) == 3000);

        cout << fixed << setprecision(2);

        cout << "DAX FUNDAMENTALS\n";
        cout << "================\n";

        cout << "\nMEASURES\n";
        cout << "Total Sales: " << engine.totalSales(all) << '\n';
        cout << "Total Cost: " << engine.totalCost(all) << '\n';
        cout << "Total Profit: " << engine.totalProfit(all) << '\n';
        cout << "Total Quantity: " << engine.totalQuantity(all) << '\n';
        cout << "Transaction Count: " << engine.transactionCount(all) << '\n';

        auto margin = engine.profitMargin(all);

        cout << "Profit Margin: "
             << (margin ? to_string(*margin) : "N/A")
             << '\n';

        engine.printCategoryReport();

        cout << "\nCALCULATED COLUMNS\n";

        for (const auto& column : engine.calculatedColumns()) {
            cout << "Sale " << column.saleId
                 << " Revenue=" << column.revenue
                 << " Cost=" << column.cost
                 << " Profit=" << column.profit
                 << " Classification=" << column.profitability
                 << '\n';
        }

        cout << "\nCALCULATED TABLE\n";

        for (const auto& category : engine.calculatedCategoryTable()) {
            cout << category.category
                 << ": " << category.productCount
                 << " products\n";
        }

        cout << "\nFILTER CONTEXT\n";
        cout << "Electronics sales: "
             << engine.totalSales(electronics)
             << '\n';

        cout << "\nALL FILTER REMOVAL\n";
        cout << "Sales without category filter: "
             << engine.calculateSales(
                    electronics,
                    {},
                    {"Product.Category"}
                )
             << '\n';

        cout << "\nSUMX\n";
        cout << "Revenue calculated row by row: "
             << engine.sumX(
                    engine.salesData(),
                    [&engine](const Sale& sale) {
                        return engine.productData().at(sale.productId).price
                            * sale.quantity;
                    }
                )
             << '\n';

        cout << "\nALL TESTS PASSED\n";

    } catch (const exception& error) {
        cerr << "Execution failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
