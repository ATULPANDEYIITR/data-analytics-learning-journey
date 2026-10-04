#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

/*
 * SQL Window Functions II
 *
 * C++ case study:
 * A revenue-governance engine receives daily sales observations and evaluates
 * them by region and product. The engine models the semantics of:
 *
 *   LAG
 *   LEAD
 *   FIRST_VALUE
 *   LAST_VALUE
 *   running totals
 *   moving averages
 *
 * The implementation uses sorted partitions, explicit row frames, validation,
 * and a policy layer for detecting large day-over-day changes.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic window_functions_ii.cpp -o window_functions_ii
 */

struct Sale {
    std::string date;
    std::string region;
    std::string product;
    double revenue;
};

struct WindowRow {
    Sale sale;
    std::optional<double> previousRevenue;
    std::optional<double> nextRevenue;
    double firstRevenue;
    double finalRevenue;
    double runningRevenue;
    double movingAverage3;
    std::optional<double> percentageChange;
    std::optional<int> calendarGap;
};

using PartitionKey = std::pair<std::string, std::string>;
using Partitions = std::map<PartitionKey, std::vector<Sale>>;

void require(bool condition, const std::string& message) {
    if (!condition) {
        throw std::invalid_argument(message);
    }
}

bool isIsoDate(const std::string& value) {
    if (value.size() != 10) {
        return false;
    }

    return value[4] == '-' &&
           value[7] == '-' &&
           std::all_of(
               value.begin(),
               value.end(),
               [](unsigned char c) {
                   return std::isdigit(c) || c == '-';
               }
           );
}

void validateSale(const Sale& sale) {
    require(isIsoDate(sale.date), "Invalid ISO date: " + sale.date);
    require(!sale.region.empty(), "Region cannot be empty.");
    require(!sale.product.empty(), "Product cannot be empty.");
    require(std::isfinite(sale.revenue), "Revenue must be finite.");
    require(sale.revenue >= 0.0, "Revenue cannot be negative.");
}

void validateDataset(const std::vector<Sale>& sales) {
    for (const auto& sale : sales) {
        validateSale(sale);
    }
}

Partitions buildPartitions(std::vector<Sale> sales) {
    /*
     * SQL PARTITION BY region, product becomes a map keyed by the two
     * partition columns. ORDER BY date is enforced before any window
     * calculation so "previous" and "next" have deterministic meaning.
     */
    Partitions partitions;

    for (const auto& sale : sales) {
        partitions[{sale.region, sale.product}].push_back(sale);
    }

    for (auto& [key, partition] : partitions) {
        std::sort(
            partition.begin(),
            partition.end(),
            [](const Sale& left, const Sale& right) {
                return left.date < right.date;
            }
        );
    }

    return partitions;
}

std::optional<double> lag(
    const std::vector<Sale>& partition,
    std::size_t index,
    std::size_t offset = 1
) {
    /*
     * LAG is row-relative. If the requested earlier row does not exist,
     * SQL normally returns NULL; std::optional models that state explicitly.
     */
    if (offset > index) {
        return std::nullopt;
    }

    return partition[index - offset].revenue;
}

std::optional<double> lead(
    const std::vector<Sale>& partition,
    std::size_t index,
    std::size_t offset = 1
) {
    /*
     * LEAD has symmetric boundary behavior: requesting a row beyond the
     * final observation produces an absent value.
     */
    if (index + offset >= partition.size()) {
        return std::nullopt;
    }

    return partition[index + offset].revenue;
}

double firstValue(const std::vector<Sale>& partition) {
    require(!partition.empty(), "FIRST_VALUE requires a non-empty partition.");
    return partition.front().revenue;
}

double lastValue(const std::vector<Sale>& partition) {
    require(!partition.empty(), "LAST_VALUE requires a non-empty partition.");
    return partition.back().revenue;
}

double runningTotal(
    const std::vector<Sale>& partition,
    std::size_t index
) {
    /*
     * This directly models:
     *
     * SUM(revenue) OVER (
     *   ORDER BY date
     *   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
     * )
     *
     * The optimized report implementation below maintains the cumulative
     * value incrementally rather than recalculating this loop for every row.
     */
    double total = 0.0;

    for (std::size_t i = 0; i <= index; ++i) {
        total += partition[i].revenue;
    }

    return total;
}

double movingAverage(
    const std::vector<Sale>& partition,
    std::size_t index,
    std::size_t precedingRows
) {
    const std::size_t start =
        index > precedingRows ? index - precedingRows : 0;

    double total = 0.0;
    std::size_t count = 0;

    for (std::size_t i = start; i <= index; ++i) {
        total += partition[i].revenue;
        ++count;
    }

    return count == 0 ? 0.0 : total / static_cast<double>(count);
}

int dateToOrdinal(const std::string& isoDate) {
    /*
     * The input uses fixed-width ISO dates. This compact Gregorian conversion
     * lets the case study detect missing calendar dates without external
     * date libraries.
     */
    const int year = std::stoi(isoDate.substr(0, 4));
    const int month = std::stoi(isoDate.substr(5, 2));
    const int day = std::stoi(isoDate.substr(8, 2));

    int y = year;
    int m = month;

    if (m <= 2) {
        --y;
        m += 12;
    }

    return 365 * y +
           y / 4 -
           y / 100 +
           y / 400 +
           (153 * (m + 1)) / 5 +
           day;
}

std::optional<int> calendarGap(
    const std::vector<Sale>& partition,
    std::size_t index
) {
    if (index == 0) {
        return std::nullopt;
    }

    return dateToOrdinal(partition[index].date) -
           dateToOrdinal(partition[index - 1].date);
}

std::vector<WindowRow> analyzePartition(
    const std::vector<Sale>& partition
) {
    require(!partition.empty(), "Cannot analyze an empty partition.");

    /*
     * firstValue/lastValue correspond to a full-partition frame. This is
     * intentionally different from a LAST_VALUE frame ending at CURRENT ROW,
     * which would return the current row's revenue.
     */
    const double first = firstValue(partition);
    const double final = lastValue(partition);

    std::vector<WindowRow> result;
    result.reserve(partition.size());

    double cumulative = 0.0;

    for (std::size_t i = 0; i < partition.size(); ++i) {
        const auto previous = lag(partition, i);
        const auto next = lead(partition, i);

        cumulative += partition[i].revenue;

        std::optional<double> change;

        if (previous.has_value() && *previous != 0.0) {
            change =
                100.0 *
                (partition[i].revenue - *previous) /
                *previous;
        }

        result.push_back({
            partition[i],
            previous,
            next,
            first,
            final,
            cumulative,
            movingAverage(partition, i, 2),
            change,
            calendarGap(partition, i)
        });
    }

    return result;
}

std::vector<WindowRow> buildReport(
    const std::vector<Sale>& sales
) {
    validateDataset(sales);

    const Partitions partitions = buildPartitions(sales);

    std::vector<WindowRow> report;

    for (const auto& [key, partition] : partitions) {
        const auto analyzed = analyzePartition(partition);
        report.insert(
            report.end(),
            analyzed.begin(),
            analyzed.end()
        );
    }

    return report;
}

void printOptional(
    const std::optional<double>& value,
    int width = 9
) {
    if (value.has_value()) {
        std::cout << std::setw(width)
                  << std::fixed
                  << std::setprecision(2)
                  << *value;
    } else {
        std::cout << std::setw(width) << "NULL";
    }
}

void printReport(const std::vector<WindowRow>& report) {
    std::cout << "\nWINDOW ANALYTICS REPORT\n";
    std::cout << std::string(115, '=') << '\n';

    std::cout
        << "Date       Region  Product    Revenue"
        << " | Previous | Next     | First    | Final"
        << " | Running  | Moving3  | Change   | Gap\n";

    std::cout << std::string(115, '-') << '\n';

    for (const auto& row : report) {
        std::cout
            << row.sale.date << " "
            << std::setw(6) << row.sale.region << " "
            << std::setw(9) << row.sale.product << " "
            << std::setw(9)
            << std::fixed
            << std::setprecision(2)
            << row.sale.revenue
            << " | ";

        printOptional(row.previousRevenue);
        std::cout << " | ";
        printOptional(row.nextRevenue);
        std::cout << " | "
                  << std::setw(8)
                  << row.firstRevenue
                  << " | "
                  << std::setw(8)
                  << row.finalRevenue
                  << " | "
                  << std::setw(8)
                  << row.runningRevenue
                  << " | "
                  << std::setw(8)
                  << row.movingAverage3
                  << " | ";

        if (row.percentageChange.has_value()) {
            std::cout
                << std::setw(7)
                << std::setprecision(2)
                << *row.percentageChange
                << "%";
        } else {
            std::cout << std::setw(8) << "NULL";
        }

        std::cout << " | ";

        if (row.calendarGap.has_value()) {
            std::cout << *row.calendarGap;
        } else {
            std::cout << "NULL";
        }

        std::cout << '\n';
    }
}

void reportLargeChanges(
    const std::vector<WindowRow>& report,
    double thresholdPercent
) {
    std::cout << "\nLARGE DAY-OVER-DAY CHANGES\n";
    std::cout << std::string(70, '=') << '\n';

    for (const auto& row : report) {
        if (
            row.percentageChange.has_value() &&
            std::fabs(*row.percentageChange) >= thresholdPercent
        ) {
            std::cout
                << row.date << " | "
                << row.region << " | "
                << row.product << " | "
                << std::fixed
                << std::setprecision(2)
                << *row.percentageChange
                << "%\n";
        }
    }
}

void demonstrateLastValueFrameSemantics(
    const std::vector<Sale>& partition
) {
    /*
     * SQL's LAST_VALUE is controlled by the window frame.
     *
     * With:
     *   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
     *
     * the last row in the frame is the current row.
     *
     * With:
     *   ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
     *
     * the frame covers the entire partition, so the true final value is
     * visible from every row.
     */
    std::cout << "\nLAST_VALUE FRAME DEMONSTRATION\n";
    std::cout << std::string(70, '=') << '\n';

    const double finalValue = partition.back().revenue;

    for (std::size_t i = 0; i < partition.size(); ++i) {
        const double currentFrameLast = partition[i].revenue;

        std::cout
            << partition[i].date
            << " | current-frame LAST_VALUE="
            << currentFrameLast
            << " | full-partition LAST_VALUE="
            << finalValue
            << '\n';
    }
}

void demonstrateMissingDates(
    const std::vector<WindowRow>& report
) {
    std::cout << "\nMISSING-CALENDAR-DATE DETECTION\n";
    std::cout << std::string(70, '=') << '\n';

    for (const auto& row : report) {
        if (row.calendarGap.has_value() && *row.calendarGap > 1) {
            std::cout
                << row.region << " / "
                << row.product << " / "
                << row.sale.date
                << " follows a gap of "
                << *row.calendarGap
                << " calendar days.\n";
        }
    }
}

void demonstrateBoundaryCases() {
    std::cout << "\nBOUNDARY CASES\n";
    std::cout << std::string(70, '=') << '\n';

    std::vector<Sale> partition = {
        {"2026-10-01", "Demo", "API", 100.0},
        {"2026-10-02", "Demo", "API", 120.0}
    };

    const auto firstLag = lag(partition, 0);
    const auto lastLead = lead(partition, 1);

    require(!firstLag.has_value(), "First LAG must be absent.");
    require(!lastLead.has_value(), "Final LEAD must be absent.");

    std::cout << "First-row LAG: NULL\n";
    std::cout << "Final-row LEAD: NULL\n";
}

void demonstrateInvalidInput() {
    std::cout << "\nVALIDATION\n";
    std::cout << std::string(70, '=') << '\n';

    try {
        validateSale({
            "2026-09-01",
            "North",
            "Cloud",
            -50.0
        });
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid sale: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        /*
         * South/Security intentionally lacks 2026-09-03 and 2026-09-06.
         * LAG therefore identifies the previous stored row, not necessarily
         * the previous calendar day. The calendarGap field exposes that
         * distinction.
         */
        const std::vector<Sale> sales = {
            {"2026-09-01", "North", "Cloud", 1200.0},
            {"2026-09-02", "North", "Cloud", 1350.0},
            {"2026-09-03", "North", "Cloud", 1280.0},
            {"2026-09-04", "North", "Cloud", 1410.0},
            {"2026-09-05", "North", "Cloud", 1500.0},
            {"2026-09-06", "North", "Cloud", 1460.0},
            {"2026-09-07", "North", "Cloud", 1600.0},

            {"2026-09-01", "South", "Cloud", 900.0},
            {"2026-09-02", "South", "Cloud", 980.0},
            {"2026-09-03", "South", "Cloud", 1020.0},
            {"2026-09-04", "South", "Cloud", 1100.0},
            {"2026-09-05", "South", "Cloud", 1060.0},
            {"2026-09-06", "South", "Cloud", 1170.0},
            {"2026-09-07", "South", "Cloud", 1210.0},

            {"2026-09-01", "North", "Security", 800.0},
            {"2026-09-02", "North", "Security", 860.0},
            {"2026-09-03", "North", "Security", 920.0},
            {"2026-09-04", "North", "Security", 880.0},
            {"2026-09-05", "North", "Security", 990.0},
            {"2026-09-06", "North", "Security", 1040.0},
            {"2026-09-07", "North", "Security", 1120.0},

            {"2026-09-01", "South", "Security", 700.0},
            {"2026-09-02", "South", "Security", 760.0},
            {"2026-09-04", "South", "Security", 820.0},
            {"2026-09-05", "South", "Security", 850.0},
            {"2026-09-07", "South", "Security", 940.0}
        };

        validateDataset(sales);

        const auto report = buildReport(sales);

        printReport(report);
        reportLargeChanges(report, 20.0);
        demonstrateMissingDates(report);

        const auto partitions = buildPartitions(sales);
        demonstrateLastValueFrameSemantics(
            partitions.at({"South", "Security"})
        );

        demonstrateBoundaryCases();
        demonstrateInvalidInput();

        /*
         * Complexity:
         * partition construction is O(n), sorting partitions is collectively
         * O(n log n) in the general case, and the report calculation is O(n)
         * once the partitions are ordered. The running total is maintained
         * incrementally, avoiding an O(n^2) cumulative-sum implementation.
         */
        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
