#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Operational analytics case study.
 *
 * Scenario: an operations department receives sales transactions from regional
 * offices and must calculate validated regional performance indicators.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic analytics.cpp -o analytics
 *
 * Financial amounts are stored as integer minor units (paise/cents), avoiding
 * binary floating-point errors in the accumulation of monetary values.
 */

namespace analytics {

struct Money {
    long long minorUnits = 0;

    static Money fromMajorUnits(const std::string& text) {
        if (text.empty()) {
            throw std::invalid_argument("Monetary value cannot be empty");
        }

        std::size_t position = 0;
        bool negative = false;

        if (text[position] == '-' || text[position] == '+') {
            negative = text[position] == '-';
            ++position;
        }

        if (position == text.size()) {
            throw std::invalid_argument("Monetary value has no digits");
        }

        long long whole = 0;
        long long fraction = 0;
        int fractionalDigits = 0;
        bool decimalPoint = false;
        bool hasDigit = false;

        for (; position < text.size(); ++position) {
            const char character = text[position];

            if (character == '.' && !decimalPoint) {
                decimalPoint = true;
                continue;
            }

            if (character < '0' || character > '9') {
                throw std::invalid_argument("Invalid monetary value: " + text);
            }

            hasDigit = true;
            const int digit = character - '0';

            if (!decimalPoint) {
                if (whole > (std::numeric_limits<long long>::max() - digit) / 10) {
                    throw std::overflow_error("Monetary amount is too large");
                }
                whole = whole * 10 + digit;
            } else {
                if (fractionalDigits >= 2) {
                    throw std::invalid_argument(
                        "Monetary values must have at most two decimal places"
                    );
                }
                fraction = fraction * 10 + digit;
                ++fractionalDigits;
            }
        }

        if (!hasDigit) {
            throw std::invalid_argument("Monetary value has no digits");
        }

        if (fractionalDigits == 1) {
            fraction *= 10;
        }

        if (whole > (std::numeric_limits<long long>::max() - fraction) / 100) {
            throw std::overflow_error("Monetary amount is too large");
        }

        const long long amount = whole * 100 + fraction;
        return Money{negative ? -amount : amount};
    }

    std::string toString() const {
        const long long whole = minorUnits / 100;
        const long long fraction = std::llabs(minorUnits % 100);
        std::ostringstream output;
        output << (minorUnits < 0 ? "-" : "")
               << std::llabs(whole) << '.'
               << std::setw(2) << std::setfill('0') << fraction;
        return output.str();
    }
};

Money checkedAdd(Money left, Money right) {
    if ((right.minorUnits > 0 &&
         left.minorUnits > std::numeric_limits<long long>::max() - right.minorUnits) ||
        (right.minorUnits < 0 &&
         left.minorUnits < std::numeric_limits<long long>::min() - right.minorUnits)) {
        throw std::overflow_error("Monetary aggregation overflow");
    }

    return Money{left.minorUnits + right.minorUnits};
}

struct Transaction {
    std::string id;
    std::string region;
    long long quantity;
    Money unitPrice;
};

struct AcceptedTransaction {
    Transaction transaction;
    Money salesAmount;
};

struct RejectedTransaction {
    std::string id;
    std::vector<std::string> errors;
};

class SalesAnalytics {
private:
    std::set<std::string> transactionIds_;
    std::map<std::string, Money> regionalTotals_;
    std::vector<AcceptedTransaction> accepted_;
    std::vector<RejectedTransaction> rejected_;

public:
    void ingest(const Transaction& transaction) {
        std::vector<std::string> errors;

        if (transaction.id.empty()) {
            errors.emplace_back("Transaction ID cannot be empty");
        } else if (transactionIds_.count(transaction.id) > 0) {
            errors.emplace_back("Duplicate transaction ID");
        }

        if (transaction.region.empty()) {
            errors.emplace_back("Region cannot be empty");
        }

        if (transaction.quantity <= 0) {
            errors.emplace_back("Quantity must be positive");
        }

        if (transaction.unitPrice.minorUnits < 0) {
            errors.emplace_back("Unit price cannot be negative");
        }

        if (!errors.empty()) {
            rejected_.push_back({transaction.id, errors});
            return;
        }

        // Multiplication is checked before creating the monetary total.
        if (transaction.unitPrice.minorUnits != 0 &&
            transaction.quantity >
                std::numeric_limits<long long>::max() /
                    transaction.unitPrice.minorUnits) {
            rejected_.push_back({
                transaction.id,
                {"Sales amount exceeds the supported numeric range"}
            });
            return;
        }

        const Money amount{
            transaction.unitPrice.minorUnits * transaction.quantity
        };

        try {
            const auto existing = regionalTotals_.find(transaction.region);
            const Money current = existing == regionalTotals_.end()
                ? Money{0}
                : existing->second;
            const Money newTotal = checkedAdd(current, amount);

            // Commit changes only after all checks succeed. A rejected record
            // cannot leave a partially updated regional aggregate.
            transactionIds_.insert(transaction.id);
            regionalTotals_[transaction.region] = newTotal;
            accepted_.push_back({transaction, amount});
        } catch (const std::overflow_error& error) {
            rejected_.push_back({transaction.id, {error.what()}});
        }
    }

    const std::map<std::string, Money>& regionalTotals() const {
        return regionalTotals_;
    }

    const std::vector<AcceptedTransaction>& accepted() const {
        return accepted_;
    }

    const std::vector<RejectedTransaction>& rejected() const {
        return rejected_;
    }

    Money totalSales() const {
        Money total{0};
        for (const auto& entry : regionalTotals_) {
            total = checkedAdd(total, entry.second);
        }
        return total;
    }

    std::optional<double> averageOrderValue() const {
        if (accepted_.empty()) {
            return std::nullopt;
        }

        return static_cast<double>(totalSales().minorUnits) /
               static_cast<double>(accepted_.size()) / 100.0;
    }
};

std::optional<double> percentageChange(double baseline, double current) {
    if (!std::isfinite(baseline) || !std::isfinite(current)) {
        throw std::invalid_argument("Measurements must be finite");
    }

    if (baseline < 0 || current < 0) {
        throw std::invalid_argument("Measurements cannot be negative");
    }

    if (baseline == 0.0) {
        return std::nullopt;
    }

    return ((current - baseline) / baseline) * 100.0;
}

void printReport(const SalesAnalytics& report) {
    std::cout << "\nRegional sales report\n";
    std::cout << std::left << std::setw(16) << "Region"
              << std::right << std::setw(18) << "Sales amount\n";

    for (const auto& [region, amount] : report.regionalTotals()) {
        std::cout << std::left << std::setw(16) << region
                  << std::right << std::setw(18) << amount.toString() << '\n';
    }

    std::cout << "Total sales: " << report.totalSales().toString() << '\n';

    const auto average = report.averageOrderValue();
    if (average.has_value()) {
        std::cout << "Average order value: "
                  << std::fixed << std::setprecision(2)
                  << average.value() << '\n';
    } else {
        std::cout << "Average order value: unavailable (no accepted records)\n";
    }

    std::cout << "\nRejected transactions\n";
    for (const auto& rejected : report.rejected()) {
        std::cout << "Transaction " << rejected.id << '\n';
        for (const auto& error : rejected.errors) {
            std::cout << "  " << error << '\n';
        }
    }
}

}  // namespace analytics

int main() {
    using namespace analytics;

    try {
        std::cout << "Operational sales analytics engine\n";

        SalesAnalytics report;

        report.ingest({"TX-1001", "North", 12, Money::fromMajorUnits("1499.50")});
        report.ingest({"TX-1002", "South", 8, Money::fromMajorUnits("2200.00")});
        report.ingest({"TX-1003", "North", 5, Money::fromMajorUnits("999.00")});
        report.ingest({"TX-1002", "East", 3, Money::fromMajorUnits("750.00")});
        report.ingest({"TX-1004", "West", -2, Money::fromMajorUnits("100.00")});
        report.ingest({"TX-1005", "East", 4, Money::fromMajorUnits("invalid")});

        printReport(report);

        std::cout << "\nGrowth calculation\n";
        const auto growth = percentageChange(790000.0, 850000.0);
        if (growth.has_value()) {
            std::cout << std::fixed << std::setprecision(2)
                      << "Revenue growth: " << growth.value() << "%\n";
        }

        const auto undefinedGrowth = percentageChange(0.0, 100.0);
        std::cout << "Growth with zero baseline: "
                  << (undefinedGrowth.has_value()
                          ? std::to_string(undefinedGrowth.value())
                          : "undefined")
                  << '\n';

        std::cout << "\nNumeric validation\n";
        try {
            (void)Money::fromMajorUnits("25.123");
        } catch (const std::exception& error) {
            std::cout << "Invalid monetary precision rejected: "
                      << error.what() << '\n';
        }

        std::cout << "\nCase study completed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal analytics error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
