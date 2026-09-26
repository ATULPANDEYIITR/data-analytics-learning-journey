#include <algorithm>
#include <cmath>
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
#include <utility>
#include <vector>

/*
 * GROUP BY & HAVING
 * =================
 *
 * C++17 industry-style case study:
 *
 * A regional sales analytics engine that models the logical behavior of
 * SQL GROUP BY and HAVING operations.
 *
 * The program demonstrates:
 *
 * - Row filtering
 * - Single-dimensional grouping
 * - Multi-dimensional grouping
 * - COUNT, SUM, AVG, MIN, MAX
 * - HAVING
 * - Conditional aggregation
 * - NULL-like optional values
 * - ROLLUP
 * - CUBE
 * - GROUPING SETS concepts
 * - Validation
 * - Error handling
 * - Sorting
 * - Performance considerations
 * - Security considerations
 * - Testing
 *
 * No external libraries are required.
 *
 * Compile:
 *
 *     g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp -o group_by_demo
 */

namespace analytics {

// ============================================================================
// 1. DATA MODEL
// ============================================================================

struct Sale {
    int saleId;
    std::string customer;
    std::optional<std::string> region;
    std::optional<std::string> category;
    std::optional<std::string> product;
    std::optional<std::string> salesperson;
    int quantity;
    std::optional<double> unitPrice;
    std::optional<double> discount;
    std::string month;
    std::string status;

    std::optional<double> grossAmount() const {
        if (!unitPrice.has_value()) {
            return std::nullopt;
        }

        return static_cast<double>(quantity) * unitPrice.value();
    }

    std::optional<double> netAmount() const {
        auto gross = grossAmount();

        if (!gross.has_value() || !discount.has_value()) {
            return std::nullopt;
        }

        return gross.value() * (1.0 - discount.value());
    }
};


// ============================================================================
// 2. SAMPLE DATA
// ============================================================================

std::vector<Sale> createSales() {
    return {
        {1, "Asha", "North", "Electronics", "Laptop", "Ravi",
         2, 800.0, 0.05, "January", "Completed"},

        {2, "Bharat", "North", "Electronics", "Phone", "Ravi",
         5, 500.0, 0.10, "January", "Completed"},

        {3, "Chen", "South", "Furniture", "Chair", "Meera",
         10, 75.0, 0.00, "January", "Completed"},

        {4, "Divya", "South", "Electronics", "Tablet", "Meera",
         3, 300.0, 0.05, "January", "Completed"},

        {5, "Eshan", "East", "Furniture", "Desk", "Arjun",
         4, 250.0, 0.08, "February", "Completed"},

        {6, "Fatima", "East", "Electronics", "Laptop", "Arjun",
         1, 900.0, 0.10, "February", "Completed"},

        {7, "Gopal", "West", "Office", "Printer", "Kiran",
         6, 200.0, 0.05, "February", "Completed"},

        {8, "Hina", "West", "Office", "Chair", "Kiran",
         15, 70.0, 0.00, "February", "Completed"},

        {9, "Ishaan", "North", "Furniture", "Desk", "Ravi",
         2, 275.0, 0.05, "March", "Completed"},

        {10, "Jaya", "South", "Office", "Printer", "Meera",
         2, 220.0, 0.00, "March", "Completed"},

        {11, "Kabir", "East", "Electronics", "Phone", "Arjun",
         8, 450.0, 0.12, "March", "Completed"},

        {12, "Leela", "West", "Furniture", "Desk", "Kiran",
         3, 260.0, 0.05, "March", "Completed"},

        {13, "Mohan", "North", "Electronics", "Laptop", "Ravi",
         1, 850.0, 0.00, "April", "Cancelled"},

        {14, "Nisha", "South", "Furniture", "Chair", "Meera",
         20, 65.0, 0.03, "April", "Completed"},

        {15, "Om", "East", "Office", "Printer", "Arjun",
         5, 210.0, 0.05, "April", "Completed"},

        {16, "Pooja", "West", "Electronics", "Tablet", "Kiran",
         4, 320.0, 0.07, "April", "Completed"}
    };
}


// ============================================================================
// 3. GENERAL HELPERS
// ============================================================================

std::string optionalString(
    const std::optional<std::string>& value
) {
    return value.has_value() ? value.value() : "NULL";
}


std::string formatDouble(
    const std::optional<double>& value
) {
    if (!value.has_value()) {
        return "NULL";
    }

    std::ostringstream stream;
    stream << std::fixed << std::setprecision(2) << value.value();
    return stream.str();
}


std::optional<double> sumOptional(
    const std::vector<std::optional<double>>& values
) {
    double total = 0.0;
    bool foundValue = false;

    for (const auto& value : values) {
        if (value.has_value()) {
            total += value.value();
            foundValue = true;
        }
    }

    if (!foundValue) {
        return std::nullopt;
    }

    return total;
}


std::optional<double> averageOptional(
    const std::vector<std::optional<double>>& values
) {
    double total = 0.0;
    std::size_t count = 0;

    for (const auto& value : values) {
        if (value.has_value()) {
            total += value.value();
            ++count;
        }
    }

    if (count == 0) {
        return std::nullopt;
    }

    return total / static_cast<double>(count);
}


std::optional<double> minimumOptional(
    const std::vector<std::optional<double>>& values
) {
    std::optional<double> result;

    for (const auto& value : values) {
        if (!value.has_value()) {
            continue;
        }

        if (!result.has_value() || value.value() < result.value()) {
            result = value.value();
        }
    }

    return result;
}


std::optional<double> maximumOptional(
    const std::vector<std::optional<double>>& values
) {
    std::optional<double> result;

    for (const auto& value : values) {
        if (!value.has_value()) {
            continue;
        }

        if (!result.has_value() || value.value() > result.value()) {
            result = value.value();
        }
    }

    return result;
}


// ============================================================================
// 4. VALIDATION
// ============================================================================

std::vector<std::string> validateSale(
    const Sale& sale
) {
    std::vector<std::string> errors;

    if (sale.saleId <= 0) {
        errors.emplace_back("saleId must be positive");
    }

    if (sale.customer.empty()) {
        errors.emplace_back("customer cannot be empty");
    }

    if (sale.quantity < 0) {
        errors.emplace_back("quantity cannot be negative");
    }

    if (sale.unitPrice.has_value() &&
        sale.unitPrice.value() < 0.0) {
        errors.emplace_back("unitPrice cannot be negative");
    }

    if (sale.discount.has_value() &&
        (sale.discount.value() < 0.0 ||
         sale.discount.value() > 1.0)) {
        errors.emplace_back("discount must be between 0 and 1");
    }

    if (sale.status != "Completed" &&
        sale.status != "Cancelled") {
        errors.emplace_back("status must be Completed or Cancelled");
    }

    return errors;
}


// ============================================================================
// 5. ROW-LEVEL FILTERING: WHERE
// ============================================================================

std::vector<Sale> filterCompleted(
    const std::vector<Sale>& sales
) {
    std::vector<Sale> result;

    for (const auto& sale : sales) {
        if (sale.status == "Completed") {
            result.push_back(sale);
        }
    }

    return result;
}


// ============================================================================
// 6. SINGLE-DIMENSION GROUPING
// ============================================================================

using RegionGroups = std::map<std::string, std::vector<Sale>>;

RegionGroups groupByRegion(
    const std::vector<Sale>& sales
) {
    RegionGroups groups;

    for (const auto& sale : sales) {
        const std::string region =
            sale.region.has_value()
                ? sale.region.value()
                : "NULL";

        groups[region].push_back(sale);
    }

    return groups;
}


// ============================================================================
// 7. MULTI-DIMENSION GROUPING
// ============================================================================

using RegionCategoryKey =
    std::pair<std::string, std::string>;

using RegionCategoryGroups =
    std::map<RegionCategoryKey, std::vector<Sale>>;


RegionCategoryGroups groupByRegionCategory(
    const std::vector<Sale>& sales
) {
    RegionCategoryGroups groups;

    for (const auto& sale : sales) {
        const std::string region =
            sale.region.has_value()
                ? sale.region.value()
                : "NULL";

        const std::string category =
            sale.category.has_value()
                ? sale.category.value()
                : "NULL";

        groups[{region, category}].push_back(sale);
    }

    return groups;
}


// ============================================================================
// 8. BASIC GROUP BY REPORT
// ============================================================================

void demonstrateBasicGroupBy(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "1. BASIC GROUP BY\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegion(sales);

    for (const auto& [region, rows] : groups) {
        std::cout
            << std::left
            << std::setw(10)
            << region
            << " COUNT(*) = "
            << rows.size()
            << "\n";
    }

    /*
     * SQL equivalent:
     *
     * SELECT region, COUNT(*)
     * FROM sales
     * GROUP BY region;
     */
}


// ============================================================================
// 9. MULTIPLE AGGREGATES
// ============================================================================

void demonstrateMultipleAggregates(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "2. MULTIPLE AGGREGATES\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegion(sales);

    for (const auto& [region, rows] : groups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        double quantity = 0.0;

        for (const auto& sale : rows) {
            quantity += sale.quantity;
        }

        std::cout
            << region
            << " rows=" << rows.size()
            << " quantity=" << quantity
            << " revenue=" << formatDouble(sumOptional(revenues))
            << " average="
            << formatDouble(averageOptional(revenues))
            << " min="
            << formatDouble(minimumOptional(revenues))
            << " max="
            << formatDouble(maximumOptional(revenues))
            << "\n";
    }

    /*
     * SQL:
     *
     * SELECT
     *     region,
     *     COUNT(*),
     *     SUM(quantity),
     *     SUM(net_amount),
     *     AVG(net_amount),
     *     MIN(net_amount),
     *     MAX(net_amount)
     * FROM sales
     * GROUP BY region;
     */
}


// ============================================================================
// 10. WHERE + GROUP BY
// ============================================================================

void demonstrateWhereAndGroupBy(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "3. WHERE BEFORE GROUP BY\n";
    std::cout << std::string(80, '=') << "\n";

    const auto completed = filterCompleted(sales);
    const auto groups = groupByRegion(completed);

    for (const auto& [region, rows] : groups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        std::cout
            << region
            << " completed revenue="
            << formatDouble(sumOptional(revenues))
            << "\n";
    }

    /*
     * SQL:
     *
     * SELECT region, SUM(net_amount)
     * FROM sales
     * WHERE status = 'Completed'
     * GROUP BY region;
     */
}


// ============================================================================
// 11. HAVING: GROUP-LEVEL FILTER
// ============================================================================

void demonstrateHaving(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "4. HAVING\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegion(sales);

    std::cout << "Regions with at least four transactions:\n";

    for (const auto& [region, rows] : groups) {
        if (rows.size() >= 4) {
            std::cout
                << region
                << " count=" << rows.size()
                << "\n";
        }
    }

    std::cout << "\nRegions with revenue >= 5000:\n";

    for (const auto& [region, rows] : groups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        auto revenue = sumOptional(revenues);

        if (revenue.has_value() &&
            revenue.value() >= 5000.0) {
            std::cout
                << region
                << " revenue="
                << formatDouble(revenue)
                << "\n";
        }
    }

    /*
     * SQL:
     *
     * SELECT region, COUNT(*)
     * FROM sales
     * GROUP BY region
     * HAVING COUNT(*) >= 4;
     *
     * HAVING is used because COUNT(*) is a group-level result.
     */
}


// ============================================================================
// 12. MULTI-DIMENSIONAL GROUPING
// ============================================================================

void demonstrateMultiDimensionalGrouping(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "5. MULTI-DIMENSIONAL GROUPING\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegionCategory(sales);

    for (const auto& [key, rows] : groups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        std::cout
            << "region=" << std::setw(8) << key.first
            << " category=" << std::setw(12) << key.second
            << " count=" << std::setw(2) << rows.size()
            << " revenue=" << formatDouble(sumOptional(revenues))
            << "\n";
    }

    /*
     * SQL:
     *
     * SELECT region, category, COUNT(*), SUM(net_amount)
     * FROM sales
     * GROUP BY region, category;
     *
     * The grouping key is the pair:
     *
     *     (region, category)
     *
     * This defines the result grain.
     */
}


// ============================================================================
// 13. CONDITIONAL AGGREGATION
// ============================================================================

void demonstrateConditionalAggregation(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "6. CONDITIONAL AGGREGATION\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegion(sales);

    for (const auto& [region, rows] : groups) {
        int completed = 0;
        int cancelled = 0;

        std::vector<std::optional<double>> electronicsRevenue;

        for (const auto& sale : rows) {
            if (sale.status == "Completed") {
                ++completed;
            }

            if (sale.status == "Cancelled") {
                ++cancelled;
            }

            if (sale.category.has_value() &&
                sale.category.value() == "Electronics") {
                electronicsRevenue.push_back(sale.netAmount());
            }
        }

        std::cout
            << region
            << " completed=" << completed
            << " cancelled=" << cancelled
            << " electronicsRevenue="
            << formatDouble(sumOptional(electronicsRevenue))
            << "\n";
    }

    /*
     * SQL:
     *
     * SELECT
     *     region,
     *     SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END),
     *     SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END)
     * FROM sales
     * GROUP BY region;
     */
}


// ============================================================================
// 14. ROLLUP-STYLE AGGREGATION
// ============================================================================

struct RollupRow {
    std::optional<std::string> region;
    std::optional<std::string> category;
    std::optional<double> revenue;
    std::string level;
};


std::vector<RollupRow> buildRollup(
    const std::vector<Sale>& sales
) {
    std::vector<RollupRow> results;

    const auto detailGroups = groupByRegionCategory(sales);

    for (const auto& [key, rows] : detailGroups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        results.push_back({
            key.first,
            key.second,
            sumOptional(revenues),
            "detail"
        });
    }

    const auto regionGroups = groupByRegion(sales);

    for (const auto& [region, rows] : regionGroups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        results.push_back({
            region,
            std::nullopt,
            sumOptional(revenues),
            "region subtotal"
        });
    }

    std::vector<std::optional<double>> allRevenues;

    for (const auto& sale : sales) {
        allRevenues.push_back(sale.netAmount());
    }

    results.push_back({
        std::nullopt,
        std::nullopt,
        sumOptional(allRevenues),
        "grand total"
    });

    return results;
}


void demonstrateRollup(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "7. ROLLUP\n";
    std::cout << std::string(80, '=') << "\n";

    for (const auto& row : buildRollup(sales)) {
        std::cout
            << "region=" << optionalString(row.region)
            << " category=" << optionalString(row.category)
            << " revenue=" << formatDouble(row.revenue)
            << " level=" << row.level
            << "\n";
    }

    /*
     * SQL:
     *
     * GROUP BY ROLLUP(region, category)
     *
     * Produces:
     *
     *     region + category
     *     region subtotal
     *     grand total
     */
}


// ============================================================================
// 15. CUBE-STYLE AGGREGATION
// ============================================================================

struct CubeRow {
    std::optional<std::string> region;
    std::optional<std::string> category;
    std::optional<double> revenue;
};


std::vector<CubeRow> buildCube(
    const std::vector<Sale>& sales
) {
    std::vector<CubeRow> results;

    // Detail level: region + category.
    {
        const auto groups = groupByRegionCategory(sales);

        for (const auto& [key, rows] : groups) {
            std::vector<std::optional<double>> revenues;

            for (const auto& sale : rows) {
                revenues.push_back(sale.netAmount());
            }

            results.push_back({
                key.first,
                key.second,
                sumOptional(revenues)
            });
        }
    }

    // Region-only level.
    {
        const auto groups = groupByRegion(sales);

        for (const auto& [region, rows] : groups) {
            std::vector<std::optional<double>> revenues;

            for (const auto& sale : rows) {
                revenues.push_back(sale.netAmount());
            }

            results.push_back({
                region,
                std::nullopt,
                sumOptional(revenues)
            });
        }
    }

    // Category-only level.
    {
        std::map<std::string, std::vector<Sale>> groups;

        for (const auto& sale : sales) {
            const std::string category =
                sale.category.has_value()
                    ? sale.category.value()
                    : "NULL";

            groups[category].push_back(sale);
        }

        for (const auto& [category, rows] : groups) {
            std::vector<std::optional<double>> revenues;

            for (const auto& sale : rows) {
                revenues.push_back(sale.netAmount());
            }

            results.push_back({
                std::nullopt,
                category,
                sumOptional(revenues)
            });
        }
    }

    // Grand total.
    {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : sales) {
            revenues.push_back(sale.netAmount());
        }

        results.push_back({
            std::nullopt,
            std::nullopt,
            sumOptional(revenues)
        });
    }

    return results;
}


void demonstrateCube(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "8. CUBE\n";
    std::cout << std::string(80, '=') << "\n";

    for (const auto& row : buildCube(sales)) {
        std::cout
            << "region=" << optionalString(row.region)
            << " category=" << optionalString(row.category)
            << " revenue=" << formatDouble(row.revenue)
            << "\n";
    }

    /*
     * SQL:
     *
     * GROUP BY CUBE(region, category)
     *
     * produces:
     *
     *     region + category
     *     region
     *     category
     *     grand total
     *
     * For n dimensions, CUBE can create up to 2^n grouping combinations.
     */
}


// ============================================================================
// 16. GROUPING SETS
// ============================================================================

void demonstrateGroupingSets(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "9. GROUPING SETS CONCEPT\n";
    std::cout << std::string(80, '=') << "\n";

    /*
     * Conceptual SQL:
     *
     * SELECT region, category, SUM(net_amount)
     * FROM sales
     * GROUP BY GROUPING SETS (
     *     (region),
     *     (category),
     *     ()
     * );
     */

    std::cout << "Region totals:\n";

    const auto regions = groupByRegion(sales);

    for (const auto& [region, rows] : regions) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        std::cout
            << "  "
            << region
            << " = "
            << formatDouble(sumOptional(revenues))
            << "\n";
    }

    std::cout << "Category totals:\n";

    std::map<std::string, std::vector<Sale>> categories;

    for (const auto& sale : sales) {
        categories[
            sale.category.has_value()
                ? sale.category.value()
                : "NULL"
        ].push_back(sale);
    }

    for (const auto& [category, rows] : categories) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        std::cout
            << "  "
            << category
            << " = "
            << formatDouble(sumOptional(revenues))
            << "\n";
    }

    std::vector<std::optional<double>> allRevenues;

    for (const auto& sale : sales) {
        allRevenues.push_back(sale.netAmount());
    }

    std::cout
        << "Grand total = "
        << formatDouble(sumOptional(allRevenues))
        << "\n";
}


// ============================================================================
// 17. GROUP BY VERSUS WINDOW FUNCTIONS
// ============================================================================

void demonstrateGroupByVsWindow(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "10. GROUP BY VERSUS WINDOW FUNCTIONS\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegion(sales);

    std::map<std::string, std::optional<double>> totals;

    for (const auto& [region, rows] : groups) {
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            revenues.push_back(sale.netAmount());
        }

        totals[region] = sumOptional(revenues);
    }

    std::cout << "GROUP BY-like result:\n";

    for (const auto& [region, total] : totals) {
        std::cout
            << region
            << " = "
            << formatDouble(total)
            << "\n";
    }

    std::cout << "\nWindow-style result preserving rows:\n";

    for (std::size_t i = 0;
         i < std::min<std::size_t>(6, sales.size());
         ++i) {

        const auto& sale = sales[i];

        const std::string region =
            sale.region.has_value()
                ? sale.region.value()
                : "NULL";

        std::cout
            << "saleId=" << sale.saleId
            << " region=" << region
            << " saleRevenue="
            << formatDouble(sale.netAmount())
            << " regionRevenue="
            << formatDouble(totals[region])
            << "\n";
    }

    /*
     * GROUP BY:
     *
     *     many rows -> one row per group
     *
     * Window function:
     *
     *     many rows -> same rows plus an analytical calculation
     *
     * SQL example:
     *
     *     SUM(net_amount) OVER (PARTITION BY region)
     */
}


// ============================================================================
// 18. REALISTIC REPORT RECORD
// ============================================================================

struct AnalyticsRecord {
    std::string region;
    std::string category;
    std::size_t transactions;
    int units;
    double revenue;
    double averageTransaction;
};


// ============================================================================
// 19. INDUSTRY-STYLE REPORT GENERATION
// ============================================================================

std::vector<AnalyticsRecord> buildSalesAnalyticsReport(
    const std::vector<Sale>& sales
) {
    /*
     * Pipeline:
     *
     * 1. WHERE status = 'Completed'
     * 2. GROUP BY region, category
     * 3. Calculate aggregates
     * 4. HAVING COUNT(*) >= 2
     * 5. ORDER BY revenue DESC
     */

    const auto completed = filterCompleted(sales);

    const auto groups = groupByRegionCategory(completed);

    std::vector<AnalyticsRecord> report;

    for (const auto& [key, rows] : groups) {
        if (rows.size() < 2) {
            continue;
        }

        double units = 0.0;
        std::vector<std::optional<double>> revenues;

        for (const auto& sale : rows) {
            units += sale.quantity;
            revenues.push_back(sale.netAmount());
        }

        const auto revenue = sumOptional(revenues);

        if (!revenue.has_value()) {
            continue;
        }

        report.push_back({
            key.first,
            key.second,
            rows.size(),
            static_cast<int>(units),
            revenue.value(),
            revenue.value() /
                static_cast<double>(rows.size())
        });
    }

    std::sort(
        report.begin(),
        report.end(),
        [](const AnalyticsRecord& left,
           const AnalyticsRecord& right) {
            if (left.revenue != right.revenue) {
                return left.revenue > right.revenue;
            }

            if (left.region != right.region) {
                return left.region < right.region;
            }

            return left.category < right.category;
        }
    );

    return report;
}


void demonstrateIndustryReport(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "11. INDUSTRY-STYLE SALES REPORT\n";
    std::cout << std::string(80, '=') << "\n";

    const auto report = buildSalesAnalyticsReport(sales);

    std::cout
        << std::left
        << std::setw(10) << "Region"
        << std::setw(14) << "Category"
        << std::setw(14) << "Transactions"
        << std::setw(10) << "Units"
        << std::setw(14) << "Revenue"
        << "Average\n";

    std::cout << std::string(75, '-') << "\n";

    for (const auto& record : report) {
        std::cout
            << std::left
            << std::setw(10) << record.region
            << std::setw(14) << record.category
            << std::setw(14) << record.transactions
            << std::setw(10) << record.units
            << std::setw(14)
            << std::fixed
            << std::setprecision(2)
            << record.revenue
            << record.averageTransaction
            << "\n";
    }

    /*
     * Equivalent SQL:
     *
     * SELECT
     *     region,
     *     category,
     *     COUNT(*) AS transactions,
     *     SUM(quantity) AS units,
     *     SUM(net_amount) AS revenue,
     *     AVG(net_amount) AS average_transaction
     * FROM sales
     * WHERE status = 'Completed'
     * GROUP BY region, category
     * HAVING COUNT(*) >= 2
     * ORDER BY revenue DESC;
     */
}


// ============================================================================
// 20. COMMON MISTAKES
// ============================================================================

void demonstrateCommonMistakes() {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "12. COMMON MISTAKES\n";
    std::cout << std::string(80, '=') << "\n";

    std::cout << R"(
1. Using an aggregate condition in WHERE.

   Incorrect:
       WHERE SUM(net_amount) > 5000

   Correct:
       HAVING SUM(net_amount) > 5000

2. Selecting a column that is neither grouped nor aggregated.

3. Forgetting that GROUP BY changes result grain.

4. Confusing COUNT(*) with COUNT(column).

5. Treating NULL as zero without a business rule.

6. Grouping inconsistent text values.

7. Grouping by too many dimensions.

8. Grouping by too few dimensions.

9. Multiplying rows through one-to-many joins before aggregation.

10. Confusing GROUP BY with window functions.

11. Rounding before aggregation when the intended rule is to round only
    after calculating the aggregate.

12. Ignoring the SQL dialect's support for ROLLUP, CUBE, and GROUPING SETS.
)";
}


// ============================================================================
// 21. PERFORMANCE AND ARCHITECTURE
// ============================================================================

void demonstratePerformance() {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "13. PERFORMANCE AND ARCHITECTURE\n";
    std::cout << std::string(80, '=') << "\n";

    std::cout << R"(
Hash-based grouping is commonly approximately O(n) for n rows when
hash-table operations are effectively constant time.

Sort-based grouping is commonly approximately O(n log n) because rows
must first be ordered by grouping keys.

Production database engines may also use:

- parallel aggregation
- partial aggregation
- hash aggregation
- sort aggregation
- index-assisted processing
- materialized views
- summary tables

Practical considerations:

- Filter early with WHERE when possible.
- Avoid grouping on unnecessarily high-cardinality keys.
- Select only columns required for the report.
- Verify row grain before aggregation.
- Examine query execution plans.
- Consider memory requirements for large hash aggregates.
- Consider disk spill behavior for aggregations exceeding memory.
- Evaluate freshness requirements before using pre-aggregated data.
)";
}


// ============================================================================
// 22. SECURITY
// ============================================================================

void demonstrateSecurity() {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "14. SECURITY\n";
    std::cout << std::string(80, '=') << "\n";

    std::cout << R"(
GROUP BY is not inherently an injection vulnerability.

The security risk occurs when application code dynamically constructs SQL
from untrusted input.

For values:
    Use parameterized queries.

For grouping identifiers:
    Use a strict allow-list of permitted columns.

Do not assume that a normal SQL value parameter can safely represent an
arbitrary SQL identifier.

Aggregation can also create information-disclosure risks. If a group contains
only one person, an aggregate report can indirectly expose individual data.

Possible controls:

- authorization
- role-based access
- minimum group-size thresholds
- aggregation policies
- masking
- careful handling of sensitive dimensions
)";
}


// ============================================================================
// 23. EDGE CASES
// ============================================================================

void demonstrateEdgeCases() {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "15. EDGE CASES\n";
    std::cout << std::string(80, '=') << "\n";

    std::vector<Sale> empty;

    const auto emptyGroups = groupByRegion(empty);

    std::cout
        << "Empty input group count: "
        << emptyGroups.size()
        << "\n";

    std::vector<std::optional<double>> allNull = {
        std::nullopt,
        std::nullopt
    };

    std::cout
        << "SUM(all NULL): "
        << formatDouble(sumOptional(allNull))
        << "\n";

    std::cout
        << "AVG(all NULL): "
        << formatDouble(averageOptional(allNull))
        << "\n";

    Sale nullDimensionSale{
        1000,
        "Test",
        std::nullopt,
        "Electronics",
        "Unknown",
        "Tester",
        1,
        100.0,
        0.0,
        "May",
        "Completed"
    };

    std::vector<Sale> testRows = {
        nullDimensionSale
    };

    const auto groups = groupByRegion(testRows);

    for (const auto& [region, rows] : groups) {
        std::cout
            << "NULL-like region group: "
            << region
            << " count="
            << rows.size()
            << "\n";
    }
}


// ============================================================================
// 24. TESTING
// ============================================================================

void require(
    bool condition,
    const std::string& message
) {
    if (!condition) {
        throw std::runtime_error(
            "TEST FAILED: " + message
        );
    }
}


void runTests(
    const std::vector<Sale>& sales
) {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "16. TESTS\n";
    std::cout << std::string(80, '=') << "\n";

    const auto groups = groupByRegion(sales);

    require(
        groups.size() == 4,
        "Expected four region groups"
    );

    const auto completed = filterCompleted(sales);

    require(
        completed.size() == 15,
        "Expected one cancelled row"
    );

    const auto report = buildSalesAnalyticsReport(sales);

    for (const auto& row : report) {
        require(
            row.transactions >= 2,
            "HAVING transaction threshold violated"
        );
    }

    for (std::size_t i = 1; i < report.size(); ++i) {
        require(
            report[i - 1].revenue >= report[i].revenue,
            "Report is not sorted by descending revenue"
        );
    }

    Sale invalid{
        -1,
        "",
        "North",
        "Electronics",
        "Phone",
        "Ravi",
        -5,
        -10.0,
        2.0,
        "May",
        "Unknown"
    };

    const auto errors = validateSale(invalid);

    require(
        errors.size() >= 5,
        "Invalid sale should produce validation errors"
    );

    std::cout << "All tests passed.\n";
}


// ============================================================================
// 25. LOGICAL SQL PROCESSING ORDER
// ============================================================================

void explainLogicalOrder() {
    std::cout << "\n";
    std::cout << std::string(80, '=') << "\n";
    std::cout << "17. LOGICAL SQL PROCESSING ORDER\n";
    std::cout << std::string(80, '=') << "\n";

    std::cout << R"(
1. FROM / JOIN
2. WHERE
3. GROUP BY
4. Aggregate calculations
5. HAVING
6. SELECT
7. DISTINCT
8. ORDER BY
9. LIMIT / OFFSET

This is a logical model used to understand SQL semantics.

A database optimizer may physically execute operations in a different order
when it can preserve the query's meaning.

The model explains why:

    WHERE -> row-level filtering

while:

    HAVING -> group-level filtering
)";
}


// ============================================================================
// 26. MAIN
// ============================================================================

} // namespace analytics


int main() {
    using namespace analytics;

    try {
        std::cout
            << std::string(80, '=')
            << "\nGROUP BY & HAVING - C++17 CASE STUDY\n"
            << std::string(80, '=')
            << "\n";

        const auto sales = createSales();

        // Validate all source records before analytics.
        for (const auto& sale : sales) {
            const auto errors = validateSale(sale);

            if (!errors.empty()) {
                std::cerr
                    << "Validation failure for sale "
                    << sale.saleId
                    << ":\n";

                for (const auto& error : errors) {
                    std::cerr
                        << "  - "
                        << error
                        << "\n";
                }

                return 1;
            }
        }

        demonstrateBasicGroupBy(sales);
        demonstrateMultipleAggregates(sales);
        demonstrateWhereAndGroupBy(sales);
        demonstrateHaving(sales);
        demonstrateMultiDimensionalGrouping(sales);
        demonstrateConditionalAggregation(sales);
        demonstrateRollup(sales);
        demonstrateCube(sales);
        demonstrateGroupingSets(sales);
        demonstrateGroupByVsWindow(sales);
        demonstrateIndustryReport(sales);
        demonstrateCommonMistakes();
        demonstratePerformance();
        demonstrateSecurity();
        demonstrateEdgeCases();
        runTests(sales);
        explainLogicalOrder();

        std::cout
            << "\n"
            << std::string(80, '=')
            << "\nCASE STUDY COMPLETED SUCCESSFULLY\n"
            << std::string(80, '=')
            << "\n";

        return 0;
    }
    catch (const std::exception& exception) {
        std::cerr
            << "Fatal error: "
            << exception.what()
            << "\n";

        return 1;
    }
}
