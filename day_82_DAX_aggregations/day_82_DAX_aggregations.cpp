#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

/*
 * DAX AGGREGATIONS
 *
 * C++17 repository-independent analytical engine.
 *
 * Implements:
 * SUM, AVERAGE, COUNT, DISTINCTCOUNT,
 * CALCULATE, FILTER and grouped aggregation.
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic dax_aggregations.cpp -o dax
 *
 * Run:
 * ./dax
 */

enum class Region {
    North,
    South,
    East,
    West
};

enum class Category {
    Electronics,
    Furniture,
    Clothing
};

enum class Status {
    Completed,
    Pending,
    Cancelled
};

enum class Operator {
    Equal,
    NotEqual,
    GreaterThan,
    GreaterOrEqual,
    LessThan,
    LessOrEqual
};

struct Transaction {
    int id;
    int customerId;
    int productId;
    Region region;
    Category category;
    Status status;
    int quantity;
    double unitPrice;
    std::optional<double> revenue;
};

struct Filter {
    std::string column;
    Operator operation;
    std::string value;
};

class AnalyticsException : public std::runtime_error {
public:
    explicit AnalyticsException(const std::string& message)
        : std::runtime_error(message) {}
};

class FilterContext {
private:
    std::vector<Filter> filters;

public:
    FilterContext() = default;

    explicit FilterContext(std::vector<Filter> initial)
        : filters(std::move(initial)) {}

    FilterContext add(const Filter& filter) const {
        FilterContext result = *this;
        result.filters.push_back(filter);
        return result;
    }

    FilterContext replace(
        const std::string& column,
        const Filter& replacement
    ) const {
        FilterContext result;

        for (const auto& filter : filters) {
            if (filter.column != column) {
                result.filters.push_back(filter);
            }
        }

        result.filters.push_back(replacement);
        return result;
    }

    const std::vector<Filter>& getFilters() const {
        return filters;
    }
};

class SalesAnalytics {
private:
    std::vector<Transaction> transactions;
    std::unordered_set<int> transactionIds;

    static std::string toString(Region region) {
        switch (region) {
            case Region::North: return "North";
            case Region::South: return "South";
            case Region::East: return "East";
            case Region::West: return "West";
        }

        throw AnalyticsException("Invalid region.");
    }

    static std::string toString(Category category) {
        switch (category) {
            case Category::Electronics: return "Electronics";
            case Category::Furniture: return "Furniture";
            case Category::Clothing: return "Clothing";
        }

        throw AnalyticsException("Invalid category.");
    }

    static std::string toString(Status status) {
        switch (status) {
            case Status::Completed: return "Completed";
            case Status::Pending: return "Pending";
            case Status::Cancelled: return "Cancelled";
        }

        throw AnalyticsException("Invalid status.");
    }

    static bool compare(
        const std::string& actual,
        const Filter& filter
    ) {
        switch (filter.operation) {
            case Operator::Equal:
                return actual == filter.value;

            case Operator::NotEqual:
                return actual != filter.value;

            case Operator::GreaterThan:
                return actual > filter.value;

            case Operator::GreaterOrEqual:
                return actual >= filter.value;

            case Operator::LessThan:
                return actual < filter.value;

            case Operator::LessOrEqual:
                return actual <= filter.value;
        }

        throw AnalyticsException("Unknown comparison operator.");
    }

    static std::string getColumnValue(
        const Transaction& transaction,
        const std::string& column
    ) {
        if (column == "region") {
            return toString(transaction.region);
        }

        if (column == "category") {
            return toString(transaction.category);
        }

        if (column == "status") {
            return toString(transaction.status);
        }

        if (column == "customerId") {
            return std::to_string(transaction.customerId);
        }

        if (column == "productId") {
            return std::to_string(transaction.productId);
        }

        if (column == "quantity") {
            return std::to_string(transaction.quantity);
        }

        if (column == "transactionId") {
            return std::to_string(transaction.id);
        }

        if (column == "revenue") {
            if (!transaction.revenue.has_value()) {
                return "";
            }

            return std::to_string(*transaction.revenue);
        }

        throw AnalyticsException("Unknown column: " + column);
    }

    bool matches(
        const Transaction& transaction,
        const FilterContext& context
    ) const {
        for (const auto& filter : context.getFilters()) {
            const std::string actual =
                getColumnValue(transaction, filter.column);

            // BLANK values do not satisfy ordinary comparisons.
            if (actual.empty()) {
                return false;
            }

            if (!compare(actual, filter)) {
                return false;
            }
        }

        return true;
    }

public:
    explicit SalesAnalytics(
        std::vector<Transaction> data
    ) : transactions(std::move(data)) {
        validate();
    }

    void validate() {
        transactionIds.clear();

        for (const auto& transaction : transactions) {
            if (transaction.id <= 0) {
                throw AnalyticsException(
                    "Transaction ID must be positive."
                );
            }

            if (!transactionIds.insert(transaction.id).second) {
                throw AnalyticsException(
                    "Duplicate transaction ID."
                );
            }

            if (transaction.quantity < 0 ||
                transaction.unitPrice < 0) {
                throw AnalyticsException(
                    "Negative transaction values are invalid."
                );
            }

            if (transaction.revenue.has_value() &&
                *transaction.revenue < 0) {
                throw AnalyticsException(
                    "Negative revenue is invalid."
                );
            }
        }
    }

    std::vector<const Transaction*> filter(
        const FilterContext& context
    ) const {
        std::vector<const Transaction*> result;

        for (const auto& transaction : transactions) {
            if (matches(transaction, context)) {
                result.push_back(&transaction);
            }
        }

        return result;
    }

    double sum(
        const std::string& column,
        const FilterContext& context = FilterContext()
    ) const {
        if (column != "revenue" &&
            column != "unitPrice" &&
            column != "quantity" &&
            column != "productId" &&
            column != "customerId" &&
            column != "transactionId") {
            throw AnalyticsException(
                "SUM requires a numeric column."
            );
        }

        double total = 0.0;

        for (const auto* transaction : filter(context)) {
            if (column == "revenue") {
                if (transaction->revenue.has_value()) {
                    total += *transaction->revenue;
                }
            } else if (column == "unitPrice") {
                total += transaction->unitPrice;
            } else if (column == "quantity") {
                total += transaction->quantity;
            } else if (column == "productId") {
                total += transaction->productId;
            } else if (column == "customerId") {
                total += transaction->customerId;
            } else if (column == "transactionId") {
                total += transaction->id;
            }
        }

        return total;
    }

    std::optional<double> average(
        const std::string& column,
        const FilterContext& context = FilterContext()
    ) const {
        double total = 0.0;
        std::size_t count = 0;

        for (const auto* transaction : filter(context)) {
            if (column == "revenue") {
                if (transaction->revenue.has_value()) {
                    total += *transaction->revenue;
                    ++count;
                }
            } else if (column == "quantity") {
                total += transaction->quantity;
                ++count;
            } else if (column == "unitPrice") {
                total += transaction->unitPrice;
                ++count;
            } else {
                throw AnalyticsException(
                    "AVERAGE requires a supported numeric column."
                );
            }
        }

        if (count == 0) {
            return std::nullopt;
        }

        return total / static_cast<double>(count);
    }

    std::size_t count(
        const std::string& column,
        const FilterContext& context = FilterContext()
    ) const {
        if (column != "revenue" &&
            column != "quantity" &&
            column != "unitPrice" &&
            column != "productId" &&
            column != "customerId" &&
            column != "transactionId") {
            throw AnalyticsException(
                "COUNT requires a numeric column."
            );
        }

        std::size_t result = 0;

        for (const auto* transaction : filter(context)) {
            if (column == "revenue") {
                if (transaction->revenue.has_value()) {
                    ++result;
                }
            } else {
                ++result;
            }
        }

        return result;
    }

    std::size_t distinctCount(
        const std::string& column,
        const FilterContext& context = FilterContext()
    ) const {
        std::set<std::string> uniqueValues;

        for (const auto* transaction : filter(context)) {
            uniqueValues.insert(
                getColumnValue(*transaction, column)
            );
        }

        // Empty string represents one distinct BLANK value.
        return uniqueValues.size();
    }

    template<typename Expression>
    auto calculate(
        Expression expression,
        const FilterContext& original,
        const std::vector<Filter>& additionalFilters,
        const std::set<std::string>& replaceColumns = {}
    ) const {
        FilterContext modified = original;

        for (const auto& filter : additionalFilters) {
            if (replaceColumns.count(filter.column)) {
                modified = modified.replace(
                    filter.column,
                    filter
                );
            } else {
                modified = modified.add(filter);
            }
        }

        return expression(modified);
    }

    void regionalReport() const {
        std::map<Region, double> revenue;

        for (const auto& transaction : transactions) {
            if (transaction.revenue.has_value()) {
                revenue[transaction.region] +=
                    *transaction.revenue;
            }
        }

        std::cout << "\nREGIONAL REVENUE\n";

        for (const auto& [region, total] : revenue) {
            std::cout << std::setw(12)
                      << toString(region)
                      << " : "
                      << std::fixed
                      << std::setprecision(2)
                      << total << '\n';
        }
    }

    void categoryReport() const {
        std::map<Category, double> revenue;

        for (const auto& transaction : transactions) {
            if (transaction.revenue.has_value()) {
                revenue[transaction.category] +=
                    *transaction.revenue;
            }
        }

        std::cout << "\nCATEGORY REVENUE\n";

        for (const auto& [category, total] : revenue) {
            std::cout << std::setw(15)
                      << toString(category)
                      << " : " << total << '\n';
        }
    }
};

std::vector<Transaction> sampleData() {
    return {
        {1001, 101, 1, Region::North, Category::Electronics,
         Status::Completed, 2, 500, 1000.0},

        {1002, 102, 2, Region::South, Category::Furniture,
         Status::Completed, 1, 800, 800.0},

        {1003, 101, 3, Region::North, Category::Electronics,
         Status::Completed, 3, 200, 600.0},

        {1004, 103, 4, Region::East, Category::Furniture,
         Status::Pending, 2, 350, 700.0},

        {1005, 104, 5, Region::West, Category::Clothing,
         Status::Completed, 5, 100, 500.0},

        {1006, 102, 6, Region::South, Category::Electronics,
         Status::Completed, 1, 1200, 1200.0},

        {1007, 105, 7, Region::North, Category::Clothing,
         Status::Cancelled, 4, 150, 600.0},

        {1008, 103, 8, Region::East, Category::Electronics,
         Status::Completed, 2, 450, 900.0},

        {1009, 0, 9, Region::West, Category::Furniture,
         Status::Pending, 0, 250, std::nullopt},

        {1010, 106, 10, Region::North, Category::Electronics,
         Status::Completed, 1, 300, 300.0}
    };
}

int main() {
    try {
        SalesAnalytics analytics(sampleData());

        std::cout << "DAX AGGREGATION ENGINE\n";
        std::cout << "======================\n";

        std::cout << std::fixed << std::setprecision(2);

        std::cout << "\n1. SUM\n";
        std::cout << analytics.sum("revenue") << '\n';

        std::cout << "\n2. AVERAGE\n";
        auto avg = analytics.average("revenue");

        if (avg.has_value()) {
            std::cout << *avg << '\n';
        } else {
            std::cout << "BLANK\n";
        }

        std::cout << "\n3. COUNT\n";
        std::cout << analytics.count("revenue") << '\n';

        std::cout << "\n4. DISTINCTCOUNT\n";
        std::cout << analytics.distinctCount("customerId") << '\n';

        Filter north{
            "region",
            Operator::Equal,
            "North"
        };

        FilterContext northContext({north});

        std::cout << "\n5. FILTER: NORTH REGION\n";
        std::cout << "Revenue: "
                  << analytics.sum("revenue", northContext)
                  << '\n';

        Filter electronics{
            "category",
            Operator::Equal,
            "Electronics"
        };

        Filter completed{
            "status",
            Operator::Equal,
            "Completed"
        };

        FilterContext combined = northContext
            .add(electronics)
            .add(completed);

        std::cout << "\n6. MULTIPLE FILTERS\n";
        std::cout << analytics.sum("revenue", combined)
                  << '\n';

        std::cout << "\n7. CALCULATE\n";

        Filter south{
            "region",
            Operator::Equal,
            "South"
        };

        double southRevenue = analytics.calculate(
            [&](const FilterContext& context) {
                return analytics.sum("revenue", context);
            },
            FilterContext(),
            std::vector<Filter>{south}
        );

        std::cout << "South revenue: "
                  << southRevenue << '\n';

        std::cout << "\n8. CALCULATE FILTER REPLACEMENT\n";

        double replacedRevenue = analytics.calculate(
            [&](const FilterContext& context) {
                return analytics.sum("revenue", context);
            },
            northContext,
            std::vector<Filter>{south},
            std::set<std::string>{"region"}
        );

        std::cout << "North replaced by South: "
                  << replacedRevenue << '\n';

        std::cout << "\n9. CALCULATE FILTER PRESERVATION\n";

        double preservedRevenue = analytics.calculate(
            [&](const FilterContext& context) {
                return analytics.sum("revenue", context);
            },
            northContext,
            std::vector<Filter>{electronics}
        );

        std::cout << "North electronics: "
                  << preservedRevenue << '\n';

        analytics.regionalReport();
        analytics.categoryReport();

        std::cout << "\n10. EMPTY FILTER RESULT\n";

        Filter impossible{
            "region",
            Operator::Equal,
            "Antarctica"
        };

        FilterContext empty({impossible});

        std::cout << "SUM: "
                  << analytics.sum("revenue", empty)
                  << '\n';

        auto emptyAverage = analytics.average("revenue", empty);

        std::cout << "AVERAGE: ";

        if (emptyAverage.has_value()) {
            std::cout << *emptyAverage;
        } else {
            std::cout << "BLANK";
        }

        std::cout << "\nCOUNT: "
                  << analytics.count("revenue", empty);

        std::cout << "\nDISTINCTCOUNT: "
                  << analytics.distinctCount("customerId", empty)
                  << '\n';

        // Regression checks.
        if (std::abs(analytics.sum("revenue") - 6600.0) > 0.0001) {
            throw AnalyticsException("SUM validation failed.");
        }

        if (analytics.count("revenue") != 9) {
            throw AnalyticsException("COUNT validation failed.");
        }

        if (analytics.distinctCount("customerId") != 7) {
            throw AnalyticsException(
                "DISTINCTCOUNT validation failed."
            );
        }

        if (std::abs(
            analytics.sum("revenue", northContext) - 2500.0
        ) > 0.0001) {
            throw AnalyticsException("FILTER validation failed.");
        }

        std::cout << "\nAll validation checks passed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Analytics failure: "
                  << error.what() << '\n';

        return 1;
    }

    return 0;
}
