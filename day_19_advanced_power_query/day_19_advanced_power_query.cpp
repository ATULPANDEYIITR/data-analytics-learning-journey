/*
 * Advanced Power Query Case Study in C++17
 *
 * Scenario:
 * A retail analytics organization receives transactional data from an
 * operational relational database. Analysts need a reusable transformation
 * pipeline that:
 *
 *   - applies configurable parameters,
 *   - reduces rows and columns early,
 *   - creates custom and conditional columns,
 *   - validates data,
 *   - joins customer metadata,
 *   - aggregates results,
 *   - tracks transformation stages,
 *   - distinguishes source-side operations from local operations,
 *   - handles errors and edge cases,
 *   - reports performance-oriented metrics.
 *
 * Power Query itself uses M. This C++ implementation is an independent
 * technical case study that models the same architectural concepts.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic power_query_case_study.cpp -o power_query_case_study
 */

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>


// ============================================================================
// 1. DATA MODEL
// ============================================================================

struct SalesRow {
    int orderId{};
    std::string customer;
    std::string region;
    double amount{};
    std::string orderDate;
};

struct CustomerRow {
    std::string customer;
    std::string segment;
    int creditScore{};
};

struct EnrichedSalesRow {
    int orderId{};
    std::string customer;
    std::string region;
    double amount{};
    std::string orderDate;
    std::string segment;
    int creditScore{};
    double estimatedMargin{};
    std::string amountBand;
};

struct Parameters {
    double minimumAmount{1000.0};
    std::string selectedRegion{"North"};
    std::string startDate{"2026-09-01"};
    std::string endDate{"2026-10-01"};
    double marginRate{0.22};
};


// ============================================================================
// 2. TRANSFORMATION METADATA
// ============================================================================

struct Operation {
    std::string name;
    bool foldable{};
    std::string description;
    std::string conceptualSql;
};

struct QueryPlan {
    std::string sourceName;
    std::vector<Operation> operations;

    void add(Operation operation) {
        operations.push_back(std::move(operation));
    }

    std::optional<std::size_t> foldingBoundary() const {
        for (std::size_t index = 0; index < operations.size(); ++index) {
            if (!operations[index].foldable) {
                return index;
            }
        }

        return std::nullopt;
    }

    std::string foldedSql() const {
        std::string selectClause = "*";
        std::vector<std::string> filters;
        std::string orderClause;

        for (const auto& operation : operations) {
            if (!operation.foldable) {
                break;
            }

            if (operation.name == "SelectColumns") {
                selectClause = operation.conceptualSql;
            } else if (operation.name == "FilterRows") {
                filters.push_back(operation.conceptualSql);
            } else if (operation.name == "Sort") {
                orderClause = operation.conceptualSql;
            }
        }

        std::ostringstream sql;

        sql << "SELECT " << selectClause
            << " FROM " << sourceName;

        if (!filters.empty()) {
            sql << " WHERE ";

            for (std::size_t i = 0; i < filters.size(); ++i) {
                if (i > 0) {
                    sql << " AND ";
                }

                sql << filters[i];
            }
        }

        if (!orderClause.empty()) {
            sql << " ORDER BY " << orderClause;
        }

        sql << ";";

        return sql.str();
    }
};


// ============================================================================
// 3. UTILITY FUNCTIONS
// ============================================================================

void printHeading(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}


std::string trim(const std::string& value) {
    const auto first = value.find_first_not_of(" \t\r\n");

    if (first == std::string::npos) {
        return "";
    }

    const auto last = value.find_last_not_of(" \t\r\n");

    return value.substr(first, last - first + 1);
}


std::string normalizeCustomer(const std::string& customer) {
    std::string result = trim(customer);

    std::string normalized;
    bool previousWasWhitespace = false;

    for (char character : result) {
        if (std::isspace(static_cast<unsigned char>(character))) {
            if (!previousWasWhitespace) {
                normalized.push_back(' ');
            }

            previousWasWhitespace = true;
        } else {
            normalized.push_back(
                static_cast<char>(
                    std::toupper(static_cast<unsigned char>(character))
                )
            );

            previousWasWhitespace = false;
        }
    }

    return normalized;
}


bool isValidAmount(double amount) {
    return std::isfinite(amount);
}


std::string classifyAmount(double amount) {
    if (!isValidAmount(amount)) {
        return "Invalid";
    }

    if (amount < 0.0) {
        return "Negative";
    }

    if (amount == 0.0) {
        return "Zero";
    }

    if (amount >= 2000.0) {
        return "High";
    }

    if (amount >= 1000.0) {
        return "Medium";
    }

    return "Low";
}


// ============================================================================
// 4. SOURCE DATA
// ============================================================================

std::vector<SalesRow> createSalesSource() {
    return {
        {1001, " Alpha ", "North", 1250.0, "2026-09-01"},
        {1002, "Beta", "South", 800.0, "2026-09-03"},
        {1003, "Gamma", "North", 2150.0, "2026-09-05"},
        {1004, "Delta", "West", 430.0, "2026-09-07"},
        {1005, "Gamma", "North", 3500.0, "2026-09-10"},
        {1006, "Alpha", "North", -50.0, "2026-09-12"},
        {1007, "Beta", "South", 4500.0, "2026-09-13"},
        {1008, "Delta", "North", 1800.0, "2026-09-15"}
    };
}


std::vector<CustomerRow> createCustomerSource() {
    return {
        {"ALPHA", "Enterprise", 780},
        {"BETA", "SMB", 690},
        {"GAMMA", "Enterprise", 820},
        {"DELTA", "SMB", 710}
    };
}


// ============================================================================
// 5. PARAMETER VALIDATION
// ============================================================================

void validateParameters(const Parameters& parameters) {
    if (!std::isfinite(parameters.minimumAmount)) {
        throw std::invalid_argument(
            "minimumAmount must be finite."
        );
    }

    if (parameters.selectedRegion.empty()) {
        throw std::invalid_argument(
            "selectedRegion cannot be empty."
        );
    }

    if (!std::isfinite(parameters.marginRate)) {
        throw std::invalid_argument(
            "marginRate must be finite."
        );
    }

    if (parameters.marginRate < 0.0 || parameters.marginRate > 1.0) {
        throw std::out_of_range(
            "marginRate must be between 0 and 1."
        );
    }

    if (parameters.startDate >= parameters.endDate) {
        throw std::invalid_argument(
            "startDate must precede endDate."
        );
    }
}


// ============================================================================
// 6. SOURCE-SIDE FILTER
// ============================================================================

std::vector<SalesRow> sourceFilter(
    const std::vector<SalesRow>& source,
    const Parameters& parameters
) {
    /*
     * This operation is intentionally designed to represent a foldable
     * operation. A relational source could theoretically perform it using
     * WHERE predicates before transferring rows to the local engine.
     *
     * The date range uses [startDate, endDate):
     *     startDate <= date < endDate
     *
     * This avoids overlap between adjacent partitions.
     */

    std::vector<SalesRow> result;
    result.reserve(source.size());

    for (const auto& row : source) {
        if (row.region != parameters.selectedRegion) {
            continue;
        }

        if (row.orderDate < parameters.startDate) {
            continue;
        }

        if (row.orderDate >= parameters.endDate) {
            continue;
        }

        if (!isValidAmount(row.amount)) {
            continue;
        }

        if (row.amount < parameters.minimumAmount) {
            continue;
        }

        result.push_back(row);
    }

    return result;
}


// ============================================================================
// 7. CUSTOM COLUMN
// ============================================================================

std::vector<EnrichedSalesRow> createCustomColumns(
    const std::vector<SalesRow>& filtered,
    const Parameters& parameters
) {
    /*
     * Custom columns represent derived values.
     *
     * In Power Query, a conceptual expression could be:
     *
     *   Table.AddColumn(
     *       Source,
     *       "EstimatedMargin",
     *       each [Amount] * MarginRate
     *   )
     *
     * Arbitrary custom logic is not automatically assumed to fold.
     */

    std::vector<EnrichedSalesRow> result;
    result.reserve(filtered.size());

    for (const auto& row : filtered) {
        EnrichedSalesRow enriched;

        enriched.orderId = row.orderId;
        enriched.customer = normalizeCustomer(row.customer);
        enriched.region = row.region;
        enriched.amount = row.amount;
        enriched.orderDate = row.orderDate;

        enriched.estimatedMargin =
            row.amount * parameters.marginRate;

        enriched.amountBand =
            classifyAmount(row.amount);

        result.push_back(std::move(enriched));
    }

    return result;
}


// ============================================================================
// 8. HASH JOIN
// ============================================================================

std::vector<EnrichedSalesRow> joinCustomerMetadata(
    const std::vector<EnrichedSalesRow>& sales,
    const std::vector<CustomerRow>& customers
) {
    /*
     * A hash index gives average O(n + m) join behavior for n sales rows
     * and m customer rows.
     *
     * A database engine may perform this join differently depending on
     * indexes, statistics, cardinality, and its optimizer.
     */

    std::unordered_map<std::string, CustomerRow> customerIndex;
    customerIndex.reserve(customers.size());

    for (const auto& customer : customers) {
        customerIndex.emplace(customer.customer, customer);
    }

    std::vector<EnrichedSalesRow> result;
    result.reserve(sales.size());

    for (const auto& sale : sales) {
        const auto iterator =
            customerIndex.find(sale.customer);

        if (iterator == customerIndex.end()) {
            /*
             * Inner-join behavior:
             * if customer metadata does not exist, the row is excluded.
             */
            continue;
        }

        EnrichedSalesRow enriched = sale;
        enriched.segment = iterator->second.segment;
        enriched.creditScore = iterator->second.creditScore;

        result.push_back(std::move(enriched));
    }

    return result;
}


// ============================================================================
// 9. CONDITIONAL BUSINESS RULE
// ============================================================================

std::string determineBusinessAction(
    const EnrichedSalesRow& row
) {
    /*
     * This represents a conditional column with ordered rules.
     *
     * Rule order matters:
     * the first matching condition determines the result.
     */

    if (row.creditScore < 650) {
        return "CreditReview";
    }

    if (row.amount >= 5000.0) {
        return "SeniorApproval";
    }

    if (row.amount >= 2000.0) {
        return "ManagerApproval";
    }

    if (row.amount >= 1000.0) {
        return "StandardApproval";
    }

    return "ManualReview";
}


// ============================================================================
// 10. AGGREGATION
// ============================================================================

struct RegionAggregate {
    std::string region;
    double totalAmount{};
    std::size_t transactionCount{};
    double averageAmount{};
};


std::vector<RegionAggregate> aggregateByRegion(
    const std::vector<EnrichedSalesRow>& rows
) {
    struct Accumulator {
        double total{};
        std::size_t count{};
    };

    std::unordered_map<std::string, Accumulator> groups;

    for (const auto& row : rows) {
        auto& accumulator = groups[row.region];

        accumulator.total += row.amount;
        ++accumulator.count;
    }

    std::vector<RegionAggregate> result;

    for (const auto& [region, accumulator] : groups) {
        RegionAggregate aggregate;

        aggregate.region = region;
        aggregate.totalAmount = accumulator.total;
        aggregate.transactionCount = accumulator.count;

        aggregate.averageAmount =
            accumulator.count == 0
                ? 0.0
                : accumulator.total
                    / static_cast<double>(accumulator.count);

        result.push_back(std::move(aggregate));
    }

    std::sort(
        result.begin(),
        result.end(),
        [](const RegionAggregate& left, const RegionAggregate& right) {
            return left.totalAmount > right.totalAmount;
        }
    );

    return result;
}


// ============================================================================
// 11. QUERY DIAGNOSTICS
// ============================================================================

struct QueryMetrics {
    std::size_t sourceRows{};
    std::size_t rowsAfterFilter{};
    std::size_t finalRows{};
    std::size_t foldableOperations{};
    std::size_t localOperations{};
    double elapsedMilliseconds{};
};


QueryMetrics calculateMetrics(
    std::size_t sourceRows,
    std::size_t filteredRows,
    std::size_t finalRows,
    const QueryPlan& plan,
    double elapsedMilliseconds
) {
    QueryMetrics metrics;

    metrics.sourceRows = sourceRows;
    metrics.rowsAfterFilter = filteredRows;
    metrics.finalRows = finalRows;
    metrics.elapsedMilliseconds = elapsedMilliseconds;

    bool foldingActive = true;

    for (const auto& operation : plan.operations) {
        if (foldingActive && operation.foldable) {
            ++metrics.foldableOperations;
        } else {
            foldingActive = false;
            ++metrics.localOperations;
        }
    }

    return metrics;
}


// ============================================================================
// 12. OUTPUT HELPERS
// ============================================================================

void printSales(const std::vector<SalesRow>& rows) {
    std::cout
        << std::left
        << std::setw(10) << "OrderID"
        << std::setw(16) << "Customer"
        << std::setw(12) << "Region"
        << std::setw(12) << "Amount"
        << std::setw(14) << "OrderDate"
        << "\n";

    std::cout << std::string(64, '-') << "\n";

    for (const auto& row : rows) {
        std::cout
            << std::left
            << std::setw(10) << row.orderId
            << std::setw(16) << row.customer
            << std::setw(12) << row.region
            << std::setw(12) << std::fixed << std::setprecision(2)
            << row.amount
            << std::setw(14) << row.orderDate
            << "\n";
    }
}


void printEnriched(
    const std::vector<EnrichedSalesRow>& rows
) {
    std::cout
        << std::left
        << std::setw(8) << "ID"
        << std::setw(12) << "Customer"
        << std::setw(12) << "Amount"
        << std::setw(12) << "Band"
        << std::setw(15) << "Segment"
        << std::setw(12) << "Margin"
        << std::setw(18) << "Action"
        << "\n";

    std::cout << std::string(89, '-') << "\n";

    for (const auto& row : rows) {
        std::cout
            << std::left
            << std::setw(8) << row.orderId
            << std::setw(12) << row.customer
            << std::setw(12) << std::fixed
            << std::setprecision(2) << row.amount
            << std::setw(12) << row.amountBand
            << std::setw(15) << row.segment
            << std::setw(12) << row.estimatedMargin
            << std::setw(18) << determineBusinessAction(row)
            << "\n";
    }
}


void printAggregates(
    const std::vector<RegionAggregate>& aggregates
) {
    std::cout
        << std::left
        << std::setw(14) << "Region"
        << std::setw(18) << "Total Amount"
        << std::setw(18) << "Transactions"
        << std::setw(18) << "Average Amount"
        << "\n";

    std::cout << std::string(68, '-') << "\n";

    for (const auto& aggregate : aggregates) {
        std::cout
            << std::left
            << std::setw(14) << aggregate.region
            << std::setw(18) << std::fixed
            << std::setprecision(2)
            << aggregate.totalAmount
            << std::setw(18) << aggregate.transactionCount
            << std::setw(18) << aggregate.averageAmount
            << "\n";
    }
}


// ============================================================================
// 13. QUERY PLAN
// ============================================================================

QueryPlan createQueryPlan() {
    QueryPlan plan;
    plan.sourceName = "Sales";

    /*
     * These operations form the source-side foldable prefix.
     */

    plan.add({
        "FilterRows",
        true,
        "Filter region, date range, and minimum amount.",
        "Region = 'North' "
        "AND OrderDate >= '2026-09-01' "
        "AND OrderDate < '2026-10-01' "
        "AND Amount >= 1000"
    });

    plan.add({
        "SelectColumns",
        true,
        "Keep only fields needed downstream.",
        "OrderID, Customer, Region, Amount, OrderDate"
    });

    /*
     * The following custom calculation represents a local boundary in this
     * educational model.
     */

    plan.add({
        "CustomColumn",
        false,
        "Calculate EstimatedMargin and AmountBand.",
        ""
    });

    /*
     * These operations occur after the modeled folding boundary.
     */

    plan.add({
        "JoinCustomerMetadata",
        false,
        "Join customer metadata locally in this case study.",
        ""
    });

    plan.add({
        "ConditionalColumn",
        false,
        "Apply ordered business rules.",
        ""
    });

    return plan;
}


// ============================================================================
// 14. FOLDING EXPLANATION
// ============================================================================

void explainQueryPlan(const QueryPlan& plan) {
    printHeading("Query plan and folding analysis");

    for (std::size_t index = 0; index < plan.operations.size(); ++index) {
        const auto& operation = plan.operations[index];

        std::cout
            << index + 1
            << ". "
            << operation.name
            << " | foldable="
            << (operation.foldable ? "true" : "false")
            << "\n"
            << "   "
            << operation.description
            << "\n";
    }

    if (const auto boundary = plan.foldingBoundary()) {
        std::cout
            << "\nFolding boundary occurs at operation index "
            << *boundary
            << " (zero-based).\n";
    } else {
        std::cout
            << "\nNo folding boundary exists in this plan.\n";
    }

    std::cout
        << "\nConceptual SQL generated by the foldable prefix:\n"
        << plan.foldedSql()
        << "\n";
}


// ============================================================================
// 15. TESTING
// ============================================================================

void runTests() {
    printHeading("Transformation tests");

    if (classifyAmount(2500.0) != "High") {
        throw std::runtime_error(
            "High-value classification test failed."
        );
    }

    if (classifyAmount(500.0) != "Low") {
        throw std::runtime_error(
            "Low-value classification test failed."
        );
    }

    if (classifyAmount(-100.0) != "Negative") {
        throw std::runtime_error(
            "Negative-value classification test failed."
        );
    }

    if (normalizeCustomer("  alpha   ltd ") != "ALPHA LTD") {
        throw std::runtime_error(
            "Customer normalization test failed."
        );
    }

    Parameters parameters;
    parameters.minimumAmount = 1000;
    parameters.selectedRegion = "North";

    validateParameters(parameters);

    std::cout << "PASS: Amount classification\n";
    std::cout << "PASS: Customer normalization\n";
    std::cout << "PASS: Parameter validation\n";
}


// ============================================================================
// 16. FAILURE CONDITION DEMONSTRATION
// ============================================================================

void demonstrateFailureHandling() {
    printHeading("Failure handling");

    try {
        Parameters invalid;
        invalid.minimumAmount = std::numeric_limits<double>::quiet_NaN();

        validateParameters(invalid);
    } catch (const std::exception& error) {
        std::cout
            << "Expected validation failure: "
            << error.what()
            << "\n";
    }

    try {
        Parameters invalid;
        invalid.marginRate = 1.5;

        validateParameters(invalid);
    } catch (const std::exception& error) {
        std::cout
            << "Expected validation failure: "
            << error.what()
            << "\n";
    }
}


// ============================================================================
// 17. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        printHeading("Advanced Power Query case study");

        Parameters parameters;
        parameters.minimumAmount = 1000.0;
        parameters.selectedRegion = "North";
        parameters.startDate = "2026-09-01";
        parameters.endDate = "2026-10-01";
        parameters.marginRate = 0.22;

        validateParameters(parameters);

        const auto sourceSales = createSalesSource();
        const auto customerMetadata = createCustomerSource();

        printHeading("Raw source data");
        printSales(sourceSales);

        /*
         * Stage 1:
         * Filter at the source.
         *
         * In a relational Power Query source, this is the kind of operation
         * that may fold into a WHERE clause.
         */
        const auto start =
            std::chrono::steady_clock::now();

        const auto filtered =
            sourceFilter(sourceSales, parameters);

        /*
         * Stage 2:
         * Apply custom and conditional transformations.
         */
        const auto customColumns =
            createCustomColumns(filtered, parameters);

        /*
         * Stage 3:
         * Join customer information.
         */
        const auto enriched =
            joinCustomerMetadata(
                customColumns,
                customerMetadata
            );

        const auto end =
            std::chrono::steady_clock::now();

        const double elapsedMilliseconds =
            std::chrono::duration<double, std::milli>(
                end - start
            ).count();

        printHeading("Filtered source rows");
        printSales(filtered);

        printHeading("Enriched transformed rows");
        printEnriched(enriched);

        /*
         * Stage 4:
         * Aggregate after transformation.
         */
        const auto aggregates =
            aggregateByRegion(enriched);

        printHeading("Aggregated result");
        printAggregates(aggregates);

        /*
         * Stage 5:
         * Analyze the transformation plan.
         */
        const auto plan = createQueryPlan();

        explainQueryPlan(plan);

        /*
         * Stage 6:
         * Produce educational diagnostics.
         */
        const auto metrics =
            calculateMetrics(
                sourceSales.size(),
                filtered.size(),
                enriched.size(),
                plan,
                elapsedMilliseconds
            );

        printHeading("Query diagnostics");

        std::cout
            << "Source rows:              "
            << metrics.sourceRows
            << "\n";

        std::cout
            << "Rows after source filter: "
            << metrics.rowsAfterFilter
            << "\n";

        std::cout
            << "Final rows:               "
            << metrics.finalRows
            << "\n";

        std::cout
            << "Foldable operations:      "
            << metrics.foldableOperations
            << "\n";

        std::cout
            << "Local operations:         "
            << metrics.localOperations
            << "\n";

        std::cout
            << "Measured local time:      "
            << std::fixed
            << std::setprecision(4)
            << metrics.elapsedMilliseconds
            << " ms\n";

        /*
         * Stage 7:
         * Tests and explicit failure cases.
         */
        runTests();
        demonstrateFailureHandling();

        printHeading("Design observations");

        std::cout << R"(
1. Source-side filtering can reduce the number of rows transferred.

2. Selecting only required columns can reduce data volume.

3. Custom columns express business logic but may create a folding boundary
   when the source cannot translate the expression.

4. Conditional columns should use explicitly ordered rules because the first
   matching branch determines the result.

5. Parameters separate configuration from transformation logic.

6. Reusable transformation functions reduce duplicated business logic.

7. Hash-based local joins can be efficient, but source-side joins may benefit
   from database indexes, query optimization, statistics, and parallelism.

8. Aggregation can be computationally expensive when performed locally over
   very large datasets.

9. Buffering or materialization is not automatically an optimization because
   it can increase memory usage and prevent useful source-side execution.

10. Production pipelines should validate inputs, control credentials,
    respect privacy boundaries, and monitor refresh performance.

11. Query folding is connector-dependent. A transformation that folds for one
    source may not fold for another.

12. The correct optimization strategy is based on measured behavior rather
    than assuming that every transformation has the same execution cost.
)";

        printHeading("Case study completed");

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal pipeline error: "
            << error.what()
            << "\n";

        return 1;
    }
}
