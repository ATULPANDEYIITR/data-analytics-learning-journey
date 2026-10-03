#include <algorithm>
#include <iomanip>
#include <iostream>
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
 * SQL Window Functions I
 *
 * C++17 case study:
 *
 * A sales analytics service needs to produce department-local leaderboards
 * while preserving every transaction row. The service must distinguish:
 *
 *   ROW_NUMBER
 *   RANK
 *   DENSE_RANK
 *
 * and must model the SQL concepts:
 *
 *   OVER
 *   PARTITION BY
 *   ORDER BY
 *
 * The program intentionally treats window processing as a separate execution
 * stage. Source records remain present after ranking, unlike a GROUP BY result
 * that collapses records.
 *
 * The design demonstrates:
 *
 *   - typed records instead of unstructured maps
 *   - explicit window specifications
 *   - partition construction
 *   - deterministic ordering
 *   - tie-aware ranking
 *   - top-N and top-N-with-ties policies
 *   - validation and failure handling
 *   - complexity and governance considerations
 */

struct Sale {
    int sale_id;
    std::string employee;
    std::string department;
    std::string region;
    long long amount_cents;
};

struct RankedSale {
    Sale sale;
    std::size_t row_number{};
    std::size_t rank{};
    std::size_t dense_rank{};
};

struct OrderRule {
    std::string column;
    bool descending{};
};

struct WindowSpecification {
    std::vector<std::string> partition_by;
    std::vector<OrderRule> order_by;

    std::string to_sql() const {
        std::ostringstream out;
        out << "OVER (";

        bool needs_space = false;

        if (!partition_by.empty()) {
            out << "PARTITION BY ";

            for (std::size_t i = 0; i < partition_by.size(); ++i) {
                if (i > 0) {
                    out << ", ";
                }
                out << partition_by[i];
            }

            needs_space = true;
        }

        if (!order_by.empty()) {
            if (needs_space) {
                out << ' ';
            }

            out << "ORDER BY ";

            for (std::size_t i = 0; i < order_by.size(); ++i) {
                if (i > 0) {
                    out << ", ";
                }

                out << order_by[i].column
                    << (order_by[i].descending ? " DESC" : " ASC");
            }
        }

        out << ')';
        return out.str();
    }
};


/* -------------------------------------------------------------------------
 * Domain validation
 * ------------------------------------------------------------------------- */

void validate_sale(const Sale& sale) {
    if (sale.sale_id <= 0) {
        throw std::invalid_argument("sale_id must be positive.");
    }

    if (sale.employee.empty()) {
        throw std::invalid_argument("employee cannot be empty.");
    }

    if (sale.department.empty()) {
        throw std::invalid_argument("department cannot be empty.");
    }

    if (sale.region.empty()) {
        throw std::invalid_argument("region cannot be empty.");
    }

    if (sale.amount_cents < 0) {
        throw std::invalid_argument("amount cannot be negative.");
    }
}

void validate_sales(const std::vector<Sale>& sales) {
    std::set<int> identifiers;

    for (const auto& sale : sales) {
        validate_sale(sale);

        if (!identifiers.insert(sale.sale_id).second) {
            throw std::invalid_argument(
                "Duplicate sale_id: " + std::to_string(sale.sale_id)
            );
        }
    }
}


/* -------------------------------------------------------------------------
 * Typed partitioning
 * ------------------------------------------------------------------------- */

using PartitionKey = std::string;

PartitionKey make_department_key(const Sale& sale) {
    return sale.department;
}

PartitionKey make_department_region_key(const Sale& sale) {
    return sale.department + "\x1f" + sale.region;
}

template <typename KeyBuilder>
std::map<PartitionKey, std::vector<const Sale*>> build_partitions(
    const std::vector<Sale>& sales,
    KeyBuilder key_builder
) {
    /*
     * This map models PARTITION BY. Each partition receives references to
     * source rows rather than copies, so the partitioning stage itself does
     * not duplicate the transaction objects.
     */
    std::map<PartitionKey, std::vector<const Sale*>> partitions;

    for (const auto& sale : sales) {
        partitions[key_builder(sale)].push_back(&sale);
    }

    return partitions;
}


/* -------------------------------------------------------------------------
 * ORDER BY comparison
 * ------------------------------------------------------------------------- */

int compare_sales(
    const Sale& left,
    const Sale& right,
    const std::vector<OrderRule>& order_rules
) {
    for (const auto& rule : order_rules) {
        int comparison = 0;

        if (rule.column == "amount") {
            if (left.amount_cents < right.amount_cents) {
                comparison = -1;
            } else if (left.amount_cents > right.amount_cents) {
                comparison = 1;
            }
        } else if (rule.column == "sale_id") {
            if (left.sale_id < right.sale_id) {
                comparison = -1;
            } else if (left.sale_id > right.sale_id) {
                comparison = 1;
            }
        } else if (rule.column == "employee") {
            if (left.employee < right.employee) {
                comparison = -1;
            } else if (left.employee > right.employee) {
                comparison = 1;
            }
        } else {
            throw std::invalid_argument(
                "Unsupported ORDER BY column: " + rule.column
            );
        }

        if (comparison != 0) {
            return rule.descending ? -comparison : comparison;
        }
    }

    return 0;
}

std::vector<const Sale*> ordered_partition(
    const std::vector<const Sale*>& partition,
    const std::vector<OrderRule>& order_rules
) {
    if (order_rules.empty()) {
        throw std::invalid_argument(
            "This ranking case study requires an ORDER BY clause."
        );
    }

    std::vector<const Sale*> ordered = partition;

    std::stable_sort(
        ordered.begin(),
        ordered.end(),
        [&](const Sale* left, const Sale* right) {
            return compare_sales(*left, *right, order_rules) < 0;
        }
    );

    return ordered;
}


/* -------------------------------------------------------------------------
 * ROW_NUMBER, RANK, and DENSE_RANK
 * ------------------------------------------------------------------------- */

std::vector<RankedSale> build_leaderboard(
    const std::vector<Sale>& sales
) {
    WindowSpecification ranking_window{
        {"department"},
        {{"amount", true}}
    };

    /*
     * RANK and DENSE_RANK must see amount ties as equal. A unique sale_id
     * should not be added to their ORDER BY expressions because that would
     * make otherwise equal amounts distinct.
     */
    auto partitions = build_partitions(
        sales,
        make_department_key
    );

    std::vector<RankedSale> result;
    result.reserve(sales.size());

    for (const auto& [department, members] : partitions) {
        auto ordered = ordered_partition(
            members,
            ranking_window.order_by
        );

        std::size_t current_rank = 0;
        std::size_t current_dense_rank = 0;
        std::optional<long long> previous_amount;

        for (std::size_t position = 0; position < ordered.size(); ++position) {
            const Sale& sale = *ordered[position];

            if (!previous_amount.has_value()
                || sale.amount_cents != previous_amount.value()) {

                /*
                 * RANK uses the physical position of the first row in a tie
                 * group. If two rows tie for first, the next distinct amount
                 * starts at rank 3.
                 */
                current_rank = position + 1;

                /*
                 * DENSE_RANK increments once for every distinct ordering
                 * value. No rank number is skipped.
                 */
                ++current_dense_rank;

                previous_amount = sale.amount_cents;
            }

            /*
             * ROW_NUMBER remains unique because position represents the
             * actual row sequence. For production deterministic output,
             * a unique secondary ORDER BY key should be supplied.
             */
            result.push_back(
                RankedSale{
                    sale,
                    position + 1,
                    current_rank,
                    current_dense_rank
                }
            );
        }
    }

    return result;
}


/* -------------------------------------------------------------------------
 * Deterministic ROW_NUMBER variant
 * ------------------------------------------------------------------------- */

std::vector<RankedSale> build_deterministic_leaderboard(
    const std::vector<Sale>& sales
) {
    WindowSpecification row_number_window{
        {"department"},
        {
            {"amount", true},
            {"sale_id", false}
        }
    };

    auto partitions = build_partitions(
        sales,
        make_department_key
    );

    std::vector<RankedSale> result;
    result.reserve(sales.size());

    for (const auto& [department, members] : partitions) {
        auto ordered = ordered_partition(
            members,
            row_number_window.order_by
        );

        for (std::size_t position = 0; position < ordered.size(); ++position) {
            const Sale& sale = *ordered[position];

            result.push_back(
                RankedSale{
                    sale,
                    position + 1,
                    0,
                    0
                }
            );
        }
    }

    /*
     * Ranking functions are calculated separately below so that the
     * deterministic ROW_NUMBER tie-breaker does not accidentally destroy
     * the semantic ties needed by RANK and DENSE_RANK.
     */
    auto tie_aware = build_leaderboard(sales);

    for (auto& row : result) {
        auto match = std::find_if(
            tie_aware.begin(),
            tie_aware.end(),
            [&](const RankedSale& candidate) {
                return candidate.sale.sale_id == row.sale.sale_id;
            }
        );

        if (match != tie_aware.end()) {
            row.rank = match->rank;
            row.dense_rank = match->dense_rank;
        }
    }

    return result;
}


/* -------------------------------------------------------------------------
 * Window aggregate: SUM(amount) OVER (PARTITION BY department)
 * ------------------------------------------------------------------------- */

struct SaleWithDepartmentTotal {
    Sale sale;
    long long department_total_cents{};
};

std::vector<SaleWithDepartmentTotal> department_totals(
    const std::vector<Sale>& sales
) {
    auto partitions = build_partitions(
        sales,
        make_department_key
    );

    std::map<PartitionKey, long long> totals;

    for (const auto& [department, members] : partitions) {
        long long total = 0;

        for (const Sale* sale : members) {
            total += sale->amount_cents;
        }

        totals[department] = total;
    }

    std::vector<SaleWithDepartmentTotal> result;
    result.reserve(sales.size());

    for (const auto& sale : sales) {
        result.push_back(
            SaleWithDepartmentTotal{
                sale,
                totals.at(sale.department)
            }
        );
    }

    return result;
}


/* -------------------------------------------------------------------------
 * Top-N policies
 * ------------------------------------------------------------------------- */

std::vector<RankedSale> top_n_rows(
    const std::vector<Sale>& sales,
    std::size_t n
) {
    if (n == 0) {
        throw std::invalid_argument("n must be greater than zero.");
    }

    auto leaderboard = build_deterministic_leaderboard(sales);

    leaderboard.erase(
        std::remove_if(
            leaderboard.begin(),
            leaderboard.end(),
            [n](const RankedSale& row) {
                return row.row_number > n;
            }
        ),
        leaderboard.end()
    );

    return leaderboard;
}

std::vector<RankedSale> top_n_with_ties(
    const std::vector<Sale>& sales,
    std::size_t n
) {
    if (n == 0) {
        throw std::invalid_argument("n must be greater than zero.");
    }

    auto leaderboard = build_leaderboard(sales);

    leaderboard.erase(
        std::remove_if(
            leaderboard.begin(),
            leaderboard.end(),
            [n](const RankedSale& row) {
                return row.rank > n;
            }
        ),
        leaderboard.end()
    );

    return leaderboard;
}


/* -------------------------------------------------------------------------
 * Output
 * ------------------------------------------------------------------------- */

std::string money(long long cents) {
    std::ostringstream out;
    out << '$'
        << cents / 100
        << '.'
        << std::setw(2)
        << std::setfill('0')
        << cents % 100;
    return out.str();
}

void print_source_rows(const std::vector<Sale>& sales) {
    std::cout << "\nSource transactions\n";
    std::cout << "-------------------\n";

    for (const auto& sale : sales) {
        std::cout
            << sale.sale_id << " | "
            << sale.employee << " | "
            << sale.department << " | "
            << sale.region << " | "
            << money(sale.amount_cents)
            << '\n';
    }
}

void print_department_totals(
    const std::vector<SaleWithDepartmentTotal>& rows
) {
    std::cout << "\nSUM(amount) OVER (PARTITION BY department)\n";
    std::cout << "--------------------------------------------\n";

    for (const auto& row : rows) {
        std::cout
            << row.sale.employee << " | "
            << row.sale.department << " | "
            << money(row.sale.amount_cents) << " | department total = "
            << money(row.department_total_cents)
            << '\n';
    }
}

void print_leaderboard(
    std::vector<RankedSale> rows,
    const std::string& title
) {
    std::sort(
        rows.begin(),
        rows.end(),
        [](const RankedSale& left, const RankedSale& right) {
            if (left.sale.department != right.sale.department) {
                return left.sale.department < right.sale.department;
            }

            return left.row_number < right.row_number;
        }
    );

    std::cout << "\n" << title << '\n';
    std::cout << std::string(title.size(), '-') << '\n';

    for (const auto& row : rows) {
        std::cout
            << row.sale.department << " | "
            << row.sale.employee << " | "
            << money(row.sale.amount_cents)
            << " | ROW_NUMBER=" << row.row_number
            << " | RANK=" << row.rank
            << " | DENSE_RANK=" << row.dense_rank
            << '\n';
    }
}


/* -------------------------------------------------------------------------
 * Assertions and case-study tests
 * ------------------------------------------------------------------------- */

void verify_rank_invariants(
    const std::vector<Sale>& sales
) {
    auto leaderboard = build_leaderboard(sales);

    auto partitions = build_partitions(
        sales,
        make_department_key
    );

    for (const auto& [department, members] : partitions) {
        std::vector<const RankedSale*> ranked_members;

        for (const auto& row : leaderboard) {
            if (row.sale.department == department) {
                ranked_members.push_back(&row);
            }
        }

        std::sort(
            ranked_members.begin(),
            ranked_members.end(),
            [](const RankedSale* left, const RankedSale* right) {
                return left->row_number < right->row_number;
            }
        );

        for (std::size_t i = 0; i < ranked_members.size(); ++i) {
            if (ranked_members[i]->row_number != i + 1) {
                throw std::runtime_error(
                    "ROW_NUMBER invariant failed."
                );
            }

            if (i > 0) {
                if (ranked_members[i]->rank
                    < ranked_members[i - 1]->rank) {
                    throw std::runtime_error(
                        "RANK must be non-decreasing."
                    );
                }

                if (ranked_members[i]->dense_rank
                    < ranked_members[i - 1]->dense_rank) {
                    throw std::runtime_error(
                        "DENSE_RANK must be non-decreasing."
                    );
                }
            }
        }
    }

    /*
     * The Sales department contains two 12,500 values followed by 9,800.
     *
     * Therefore:
     *   the tied first rows have RANK 1
     *   the next amount has RANK 3
     *   the tied first rows have DENSE_RANK 1
     *   the next amount has DENSE_RANK 2
     */
    const auto sales_members = std::count_if(
        leaderboard.begin(),
        leaderboard.end(),
        [](const RankedSale& row) {
            return row.sale.department == "Sales"
                && row.sale.amount_cents == 1250000;
        }
    );

    if (sales_members != 2) {
        throw std::runtime_error(
            "Expected two tied Sales records at 12,500."
        );
    }

    for (const auto& row : leaderboard) {
        if (row.sale.department == "Sales"
            && row.sale.amount_cents == 1250000) {

            if (row.rank != 1 || row.dense_rank != 1) {
                throw std::runtime_error(
                    "Tie ranking semantics are incorrect."
                );
            }
        }

        if (row.sale.department == "Sales"
            && row.sale.amount_cents == 980000) {

            if (row.rank != 3 || row.dense_rank != 2) {
                throw std::runtime_error(
                    "Gap behavior between RANK and DENSE_RANK is incorrect."
                );
            }
        }
    }
}


/* -------------------------------------------------------------------------
 * Main case study
 * ------------------------------------------------------------------------- */

int main() {
    try {
        const std::vector<Sale> sales{
            {101, "Asha",   "Engineering", "North", 920000},
            {102, "Ravi",   "Engineering", "North", 870000},
            {103, "Meera",  "Engineering", "South", 920000},
            {104, "Kabir",  "Engineering", "South", 760000},
            {105, "Isha",   "Sales",       "North", 1250000},
            {106, "Arjun",  "Sales",       "North", 980000},
            {107, "Neha",   "Sales",       "South", 1250000},
            {108, "Vikram", "Sales",       "South", 810000},
            {109, "Tara",   "Finance",     "North", 670000},
            {110, "Dev",    "Finance",     "North", 670000},
            {111, "Pooja",  "Finance",     "South", 590000},
            {112, "Nikhil", "Finance",     "South", 510000}
        };

        validate_sales(sales);

        WindowSpecification window{
            {"department"},
            {
                {"amount", true},
                {"sale_id", false}
            }
        };

        std::cout
            << "Window specification: "
            << window.to_sql()
            << "\n";

        print_source_rows(sales);

        auto totals = department_totals(sales);
        print_department_totals(totals);

        auto leaderboard = build_deterministic_leaderboard(sales);

        /*
         * ROW_NUMBER uses amount DESC plus sale_id ASC. This makes two equal
         * amounts receive different physical positions while preserving their
         * shared RANK and DENSE_RANK values.
         */
        print_leaderboard(
            leaderboard,
            "Department leaderboard"
        );

        auto top_two = top_n_rows(sales, 2);

        print_leaderboard(
            top_two,
            "Top two rows per department using ROW_NUMBER"
        );

        auto top_two_ties = top_n_with_ties(sales, 2);

        print_leaderboard(
            top_two_ties,
            "Top two ranks per department using RANK"
        );

        /*
         * Compound PARTITION BY is a different partitioning policy:
         *
         *   PARTITION BY department, region
         *
         * Engineering/North is independent from Engineering/South.
         */
        auto regional_partitions = build_partitions(
            sales,
            make_department_region_key
        );

        std::cout
            << "\nCompound PARTITION BY department, region\n"
            << "-------------------------------------------\n";

        for (const auto& [key, members] : regional_partitions) {
            long long total = 0;

            for (const Sale* sale : members) {
                total += sale->amount_cents;
            }

            std::cout
                << key
                << " | rows=" << members.size()
                << " | total=" << money(total)
                << '\n';
        }

        verify_rank_invariants(sales);

        std::cout
            << "\nCase-study verification passed.\n"
            << "Every source row remains available after window ranking, "
            << "ties receive shared RANK and DENSE_RANK values, and "
            << "ROW_NUMBER remains a unique sequence within each department.\n";

        /*
         * Complexity:
         *
         * Partition construction is approximately O(n) for this map-based
         * representation, excluding key construction.
         *
         * Sorting each partition costs O(k log k), so total sorting work is
         * approximately the sum of k log k over all partitions.
         *
         * The overall memory requirement is O(n) for the partition references
         * and result rows.
         *
         * Real SQL engines can optimize these operations using indexes,
         * existing order, incremental sorting, parallel execution, and
         * engine-specific execution plans.
         */
        std::cout
            << "\nPerformance characteristics\n"
            << "----------------------------\n"
            << "Partition construction: approximately O(n)\n"
            << "Window ordering: approximately sum(k log k) over partitions\n"
            << "Result storage: O(n)\n";

        /*
         * Governance consideration:
         *
         * A top-N report using ROW_NUMBER and one using RANK answer different
         * business questions. Selecting the function is therefore a semantic
         * decision, not merely a syntax choice.
         */
        std::cout
            << "\nSemantic distinction\n"
            << "--------------------\n"
            << "ROW_NUMBER answers: which physical row occupies each position?\n"
            << "RANK answers: what competition position does each tied value receive?\n"
            << "DENSE_RANK answers: what distinct-value position does each row receive?\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Execution failed: "
            << error.what()
            << '\n';

        return 1;
    }
}
