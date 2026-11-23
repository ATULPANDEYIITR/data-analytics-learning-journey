#include <algorithm>
#include <cmath>
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

using namespace std;

/*
 * ADVANCED DAX CONCEPTS
 *
 * Row Context
 * Filter Context
 * Context Transition
 * CALCULATE
 * SUMX
 * FILTER
 * ADDCOLUMNS
 * Variables
 *
 * C++17 analytical evaluation and merge-free
 * in-memory reporting engine.
 */

// ============================================================
// 1. DOMAIN MODEL
// ============================================================

struct Sale {
    int id;
    int productId;
    string category;
    string region;
    double quantity;
    double unitPrice;
    double cost;

    double revenue() const {
        return quantity * unitPrice;
    }

    double totalCost() const {
        return quantity * cost;
    }

    double profit() const {
        return revenue() - totalCost();
    }
};

struct Product {
    int id;
    string name;
    string category;
};

const vector<Sale> SALES = {
    {1, 101, "Electronics", "North", 2, 500, 350},
    {2, 102, "Electronics", "South", 1, 800, 600},
    {3, 103, "Furniture", "North", 3, 200, 120},
    {4, 101, "Electronics", "West", 1, 500, 350},
    {5, 104, "Furniture", "South", 4, 150, 90},
    {6, 105, "Clothing", "North", 5, 80, 40}
};

const vector<Product> PRODUCTS = {
    {101, "Laptop", "Electronics"},
    {102, "Monitor", "Electronics"},
    {103, "Desk", "Furniture"},
    {104, "Chair", "Furniture"},
    {105, "Shirt", "Clothing"}
};


// ============================================================
// 2. ENUMS AND ERRORS
// ============================================================

enum class Aggregation {
    SUM,
    COUNT,
    AVERAGE
};

class EvaluationException : public runtime_error {
public:
    explicit EvaluationException(const string& message)
        : runtime_error(message) {}
};


// ============================================================
// 3. FILTER CONTEXT
// ============================================================

struct FilterContext {

    map<string, set<string>> filters;

    bool allows(const Sale& sale) const {

        auto matches = [&](const string& column,
                           const string& value) {
            auto it = filters.find(column);

            return it == filters.end()
                || it->second.count(value) > 0;
        };

        return matches("region", sale.region)
            && matches("category", sale.category);
    }

    void apply(const string& column,
               const set<string>& values) {

        static const set<string> validColumns = {
            "region", "category"
        };

        if (!validColumns.count(column)) {
            throw EvaluationException(
                "Unsupported filter column: " + column
            );
        }

        auto it = filters.find(column);

        if (it == filters.end()) {
            filters[column] = values;
            return;
        }

        set<string> intersection;

        set_intersection(
            it->second.begin(), it->second.end(),
            values.begin(), values.end(),
            inserter(intersection, intersection.begin())
        );

        it->second = move(intersection);
    }

    void replace(const string& column,
                 const set<string>& values) {

        static const set<string> validColumns = {
            "region", "category"
        };

        if (!validColumns.count(column)) {
            throw EvaluationException(
                "Unsupported filter column: " + column
            );
        }

        filters[column] = values;
    }
};


// ============================================================
// 4. ROW CONTEXT
// ============================================================

struct RowContext {
    vector<const Sale*> rows;

    void push(const Sale& sale) {
        rows.push_back(&sale);
    }

    void pop() {
        if (rows.empty()) {
            throw EvaluationException(
                "Cannot pop an empty row context."
            );
        }

        rows.pop_back();
    }

    const Sale& current() const {
        if (rows.empty()) {
            throw EvaluationException(
                "No active row context."
            );
        }

        return *rows.back();
    }
};


// ============================================================
// 5. DATA MODEL AND RELATIONSHIPS
// ============================================================

class DataModel {

private:
    vector<Sale> sales;
    vector<Product> products;

    unordered_map<int, const Product*> productIndex;

public:
    DataModel(vector<Sale> s, vector<Product> p)
        : sales(move(s)), products(move(p)) {

        for (const auto& product : products) {
            if (!productIndex.emplace(
                    product.id, &product
                ).second) {
                throw EvaluationException(
                    "Duplicate ProductID."
                );
            }
        }

        for (const auto& sale : sales) {
            if (!productIndex.count(sale.productId)) {
                throw EvaluationException(
                    "Sale references an unknown product."
                );
            }

            if (sale.quantity < 0 || sale.unitPrice < 0
                || sale.cost < 0) {
                throw EvaluationException(
                    "Negative transactional values are invalid."
                );
            }
        }
    }

    const vector<Sale>& allSales() const {
        return sales;
    }

    const vector<Product>& allProducts() const {
        return products;
    }

    const Product& findProduct(int id) const {
        auto it = productIndex.find(id);

        if (it == productIndex.end()) {
            throw EvaluationException("Product not found.");
        }

        return *it->second;
    }

    vector<const Sale*> filteredSales(
        const FilterContext& context
    ) const {

        vector<const Sale*> result;

        for (const auto& sale : sales) {
            if (context.allows(sale)) {
                result.push_back(&sale);
            }
        }

        return result;
    }

    vector<const Sale*> salesForProduct(
        int productId,
        const FilterContext& context
    ) const {

        FilterContext modified = context;
        modified.apply("category", {
            findProduct(productId).category
        });

        vector<const Sale*> result;

        for (const auto& sale : sales) {
            if (sale.productId == productId
                && modified.allows(sale)) {
                result.push_back(&sale);
            }
        }

        return result;
    }
};


// ============================================================
// 6. MEASURE ENGINE
// ============================================================

class MeasureEngine {

private:
    const DataModel& model;

public:
    explicit MeasureEngine(const DataModel& m)
        : model(m) {}

    double revenue(const FilterContext& context) const {
        double total = 0;

        for (const Sale* sale : model.filteredSales(context)) {
            total += sale->revenue();
        }

        return total;
    }

    double cost(const FilterContext& context) const {
        double total = 0;

        for (const Sale* sale : model.filteredSales(context)) {
            total += sale->totalCost();
        }

        return total;
    }

    double profit(const FilterContext& context) const {
        return revenue(context) - cost(context);
    }

    double margin(const FilterContext& context) const {
        const double salesValue = revenue(context);
        const double costValue = cost(context);
        const double profitValue = salesValue - costValue;

        return salesValue == 0
            ? 0
            : profitValue / salesValue;
    }

    double revenueWithContextTransition(
        const FilterContext& original,
        const RowContext& rowContext
    ) const {

        FilterContext modified = original;

        // Current row values become filters.
        for (const Sale* row : rowContext.rows) {
            modified.apply("region", {row->region});
            modified.apply("category", {row->category});

            // Transaction identity is preserved by the
            // current-row predicate below.
        }

        const Sale& current = rowContext.current();

        double total = 0;

        for (const Sale* sale : model.filteredSales(modified)) {
            if (sale->id == current.id) {
                total += sale->revenue();
            }
        }

        return total;
    }
};


// ============================================================
// 7. ITERATOR ENGINE
// ============================================================

class IteratorEngine {

public:

    template<typename Expression>
    static double SUMX(
        const vector<const Sale*>& rows,
        Expression expression
    ) {
        double total = 0;

        for (const Sale* row : rows) {
            RowContext context;
            context.push(*row);

            const double value = expression(context);

            if (!isfinite(value)) {
                throw EvaluationException(
                    "SUMX expression produced a non-finite value."
                );
            }

            total += value;
        }

        return total;
    }

    template<typename Predicate>
    static vector<const Sale*> FILTER(
        const vector<const Sale*>& rows,
        Predicate predicate
    ) {
        vector<const Sale*> result;

        for (const Sale* row : rows) {
            RowContext context;
            context.push(*row);

            if (predicate(context)) {
                result.push_back(row);
            }
        }

        return result;
    }
};


// ============================================================
// 8. CALCULATE
// ============================================================

double CALCULATE(
    const MeasureEngine& engine,
    const FilterContext& context,
    const optional<pair<string, set<string>>>& filter = nullopt
) {
    FilterContext modified = context;

    if (filter.has_value()) {
        modified.replace(
            filter->first,
            filter->second
        );
    }

    return engine.revenue(modified);
}


// ============================================================
// 9. VARIABLE-BASED EVALUATION
// ============================================================

struct Profitability {
    double revenue;
    double cost;
    double profit;
    double margin;
};

Profitability evaluateProfitability(
    const MeasureEngine& engine,
    const FilterContext& context
) {
    // Each value is computed once and reused.
    const double revenue = engine.revenue(context);
    const double cost = engine.cost(context);
    const double profit = revenue - cost;

    const double margin = revenue == 0
        ? 0
        : profit / revenue;

    return {revenue, cost, profit, margin};
}


// ============================================================
// 10. VIRTUAL TABLE / ADDCOLUMNS
// ============================================================

struct ProductMetric {
    string productName;
    string category;
    double productRevenue;
    double productProfit;
};

vector<ProductMetric> ADDCOLUMNS(
    const DataModel& model,
    const MeasureEngine& engine,
    const FilterContext& context
) {
    vector<ProductMetric> result;

    for (const auto& product : model.allProducts()) {

        FilterContext modified = context;
        modified.apply("category", {product.category});

        double revenue = 0;
        double cost = 0;

        for (const Sale* sale :
             model.salesForProduct(product.id, modified)) {
            revenue += sale->revenue();
            cost += sale->totalCost();
        }

        result.push_back({
            product.name,
            product.category,
            revenue,
            revenue - cost
        });
    }

    return result;
}


// ============================================================
// 11. REPORTING
// ============================================================

void printRegionalReport(
    const DataModel& model,
    const MeasureEngine& engine
) {
    set<string> regions;

    for (const auto& sale : model.allSales()) {
        regions.insert(sale.region);
    }

    cout << "\nREGIONAL REPORT\n";

    for (const auto& region : regions) {
        FilterContext context;
        context.apply("region", {region});

        cout << left << setw(12) << region
             << "Revenue: " << setw(10)
             << engine.revenue(context)
             << "Profit: " << engine.profit(context)
             << '\n';
    }
}


// ============================================================
// 12. TESTS
// ============================================================

void runTests(
    const DataModel& model,
    const MeasureEngine& engine
) {
    FilterContext base;

    if (engine.revenue(base) != 3350)
        throw EvaluationException("Revenue test failed.");

    if (engine.cost(base) != 2190)
        throw EvaluationException("Cost test failed.");

    if (engine.profit(base) != 1160)
        throw EvaluationException("Profit test failed.");

    FilterContext north;
    north.apply("region", {"North"});

    if (engine.revenue(north) != 1900)
        throw EvaluationException("North filter test failed.");

    FilterContext electronics;
    electronics.apply("category", {"Electronics"});

    if (engine.revenue(electronics) != 1800)
        throw EvaluationException("Category filter test failed.");

    const auto rows = model.filteredSales(base);

    const double iteratorRevenue = IteratorEngine::SUMX(
        rows,
        [](const RowContext& context) {
            return context.current().revenue();
        }
    );

    if (iteratorRevenue != 3350)
        throw EvaluationException("SUMX test failed.");

    const auto expensive = IteratorEngine::FILTER(
        rows,
        [](const RowContext& context) {
            return context.current().revenue() >= 500;
        }
    );

    if (expensive.size() != 5)
        throw EvaluationException("FILTER test failed.");

    FilterContext empty;
    empty.apply("region", {"Unknown"});

    if (engine.margin(empty) != 0)
        throw EvaluationException("Empty-context test failed.");

    bool rejected = false;

    try {
        model.findProduct(999);
    } catch (const EvaluationException&) {
        rejected = true;
    }

    if (!rejected)
        throw EvaluationException("Missing product was accepted.");

    cout << "\nAll C++17 tests passed.\n";
}


// ============================================================
// 13. MAIN
// ============================================================

int main() {

    try {
        DataModel model(SALES, PRODUCTS);
        MeasureEngine engine(model);

        FilterContext base;

        cout << fixed << setprecision(2);
        cout << "ADVANCED DAX EVALUATION ENGINE\n";
        cout << "==============================\n";

        // Base filter context
        const auto metrics = evaluateProfitability(
            engine, base
        );

        cout << "\nBASE MEASURES\n";
        cout << "Revenue: " << metrics.revenue << '\n';
        cout << "Cost: " << metrics.cost << '\n';
        cout << "Profit: " << metrics.profit << '\n';
        cout << "Margin: " << metrics.margin * 100 << "%\n";

        // CALCULATE
        cout << "\nCALCULATE - NORTH\n";
        cout << CALCULATE(
            engine,
            base,
            make_pair(
                string("region"),
                set<string>{"North"}
            )
        ) << '\n';

        // Row context and SUMX
        const auto rows = model.filteredSales(base);

        cout << "\nSUMX\n";

        cout << IteratorEngine::SUMX(
            rows,
            [](const RowContext& context) {
                const Sale& sale = context.current();
                return sale.quantity * sale.unitPrice;
            }
        ) << '\n';

        // Explicit context transition
        cout << "\nCONTEXT TRANSITION\n";

        double transitioned = 0;

        for (const Sale* sale : rows) {
            RowContext row;
            row.push(*sale);

            transitioned += engine.revenueWithContextTransition(
                base, row
            );
        }

        cout << transitioned << '\n';

        // FILTER
        const auto expensive = IteratorEngine::FILTER(
            rows,
            [](const RowContext& context) {
                return context.current().revenue() >= 500;
            }
        );

        cout << "\nFILTER RESULT COUNT: "
             << expensive.size() << '\n';

        // ADDCOLUMNS
        cout << "\nPRODUCT VIRTUAL TABLE\n";

        for (const auto& item :
             ADDCOLUMNS(model, engine, base)) {

            cout << left << setw(12) << item.productName
                 << setw(15) << item.category
                 << "Revenue: " << setw(10)
                 << item.productRevenue
                 << "Profit: " << item.productProfit
                 << '\n';
        }

        printRegionalReport(model, engine);

        runTests(model, engine);

    } catch (const exception& error) {
        cerr << "Evaluation error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
