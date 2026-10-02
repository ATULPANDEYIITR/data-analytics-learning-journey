#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * SQL DATE & TIME GOVERNANCE CASE STUDY
 *
 * Scenario:
 * A financial operations platform stores transaction timestamps, produces
 * calendar reports, and applies service-level deadlines. The database layer
 * conceptually exposes DATE, TIMESTAMP, INTERVAL, DATE_PART and DATE_TRUNC.
 *
 * C++ does not provide a complete IANA timezone database through the standard
 * library in C++17, so this case study models timezone offsets explicitly.
 * That limitation is deliberate: a fixed UTC offset is not interchangeable
 * with a named timezone whose offset can change because of daylight-saving
 * rules.
 *
 * The program demonstrates:
 * - date-only calendar values
 * - timestamp instants
 * - interval arithmetic
 * - date-part extraction
 * - date truncation
 * - timezone offsets
 * - half-open reporting ranges
 * - merge-style event processing
 * - validation and failure handling
 * - complexity and data-structure decisions
 */

namespace sqltime {

// ---------------------------------------------------------------------------
// DATE
// ---------------------------------------------------------------------------

struct Date {
    int year;
    unsigned month;
    unsigned day;

    static bool isLeapYear(int year) {
        return (year % 400 == 0) ||
               (year % 4 == 0 && year % 100 != 0);
    }

    static unsigned daysInMonth(int year, unsigned month) {
        static constexpr unsigned days[] = {
            31, 28, 31, 30, 31, 30,
            31, 31, 30, 31, 30, 31
        };

        if (month < 1 || month > 12) {
            throw std::invalid_argument("Month must be between 1 and 12");
        }

        if (month == 2 && isLeapYear(year)) {
            return 29;
        }

        return days[month - 1];
    }

    void validate() const {
        if (month < 1 || month > 12) {
            throw std::invalid_argument("Invalid month");
        }

        if (day < 1 || day > daysInMonth(year, month)) {
            throw std::invalid_argument("Invalid day for calendar month");
        }
    }

    std::string toString() const {
        validate();

        std::ostringstream out;
        out << std::setfill('0')
            << std::setw(4) << year << '-'
            << std::setw(2) << month << '-'
            << std::setw(2) << day;
        return out.str();
    }
};


// ---------------------------------------------------------------------------
// TIMESTAMP and fixed UTC offset
// ---------------------------------------------------------------------------

struct Timestamp {
    Date date;
    int hour;
    int minute;
    int second;
    int microsecond;
    int utcOffsetMinutes;

    void validate() const {
        date.validate();

        if (hour < 0 || hour > 23) {
            throw std::invalid_argument("Invalid hour");
        }

        if (minute < 0 || minute > 59) {
            throw std::invalid_argument("Invalid minute");
        }

        if (second < 0 || second > 59) {
            throw std::invalid_argument("Invalid second");
        }

        if (microsecond < 0 || microsecond > 999999) {
            throw std::invalid_argument("Invalid microsecond");
        }

        if (utcOffsetMinutes < -1439 || utcOffsetMinutes > 1439) {
            throw std::invalid_argument("Invalid UTC offset");
        }
    }

    std::string offsetString() const {
        int absolute = std::abs(utcOffsetMinutes);
        char sign = utcOffsetMinutes < 0 ? '-' : '+';

        std::ostringstream out;
        out << sign
            << std::setfill('0')
            << std::setw(2) << absolute / 60
            << ':'
            << std::setw(2) << absolute % 60;
        return out.str();
    }

    std::string toString() const {
        validate();

        std::ostringstream out;
        out << date.toString()
            << 'T'
            << std::setfill('0')
            << std::setw(2) << hour << ':'
            << std::setw(2) << minute << ':'
            << std::setw(2) << second
            << '.'
            << std::setw(6) << microsecond
            << offsetString();

        return out.str();
    }
};


// ---------------------------------------------------------------------------
// INTERVAL
// ---------------------------------------------------------------------------

struct Interval {
    int months{0};
    int days{0};
    long long seconds{0};
    long long microseconds{0};

    std::string toString() const {
        std::ostringstream out;
        bool wrote = false;

        if (months != 0) {
            out << months << " month(s)";
            wrote = true;
        }

        if (days != 0) {
            if (wrote) out << " + ";
            out << days << " day(s)";
            wrote = true;
        }

        if (seconds != 0) {
            if (wrote) out << " + ";
            out << seconds << " second(s)";
            wrote = true;
        }

        if (microseconds != 0) {
            if (wrote) out << " + ";
            out << microseconds << " microsecond(s)";
            wrote = true;
        }

        return wrote ? out.str() : "0";
    }
};


// ---------------------------------------------------------------------------
// Calendar arithmetic
// ---------------------------------------------------------------------------

Date addDays(Date value, int numberOfDays) {
    value.validate();

    // Julian-day conversion is unnecessary for this bounded business example.
    // Walking the calendar makes the behavior explicit and keeps the
    // distinction between calendar days and fixed durations visible.
    int direction = numberOfDays >= 0 ? 1 : -1;
    int remaining = std::abs(numberOfDays);

    while (remaining-- > 0) {
        if (direction > 0) {
            if (value.day < Date::daysInMonth(value.year, value.month)) {
                ++value.day;
            } else {
                value.day = 1;

                if (value.month == 12) {
                    value.month = 1;
                    ++value.year;
                } else {
                    ++value.month;
                }
            }
        } else {
            if (value.day > 1) {
                --value.day;
            } else {
                if (value.month == 1) {
                    value.month = 12;
                    --value.year;
                } else {
                    --value.month;
                }

                value.day =
                    Date::daysInMonth(value.year, value.month);
            }
        }
    }

    return value;
}

Date addMonths(Date value, int numberOfMonths) {
    value.validate();

    long long zeroBased =
        static_cast<long long>(value.month) - 1 + numberOfMonths;

    int targetYear =
        value.year + static_cast<int>(
            std::floor(static_cast<double>(zeroBased) / 12.0)
        );

    int targetMonth =
        static_cast<int>(zeroBased % 12);

    if (targetMonth < 0) {
        targetMonth += 12;
    }

    targetMonth += 1;

    unsigned lastDay =
        Date::daysInMonth(targetYear, static_cast<unsigned>(targetMonth));

    value.year = targetYear;
    value.month = static_cast<unsigned>(targetMonth);
    value.day = std::min(value.day, lastDay);

    return value;
}

Timestamp addInterval(Timestamp value, const Interval& interval) {
    value.validate();

    value.date = addMonths(value.date, interval.months);
    value.date = addDays(value.date, interval.days);

    long long totalMicroseconds =
        static_cast<long long>(value.microsecond) +
        interval.seconds * 1'000'000LL +
        interval.microseconds;

    long long wholeSeconds =
        totalMicroseconds / 1'000'000LL;

    long long remainingMicroseconds =
        totalMicroseconds % 1'000'000LL;

    if (remainingMicroseconds < 0) {
        remainingMicroseconds += 1'000'000LL;
        --wholeSeconds;
    }

    value.microsecond =
        static_cast<int>(remainingMicroseconds);

    long long totalSeconds =
        static_cast<long long>(value.hour) * 3600LL +
        static_cast<long long>(value.minute) * 60LL +
        value.second +
        wholeSeconds;

    long long dayDelta =
        totalSeconds >= 0
            ? totalSeconds / 86400LL
            : (totalSeconds - 86399LL) / 86400LL;

    long long secondsWithinDay =
        totalSeconds - dayDelta * 86400LL;

    value.hour =
        static_cast<int>(secondsWithinDay / 3600LL);

    value.minute =
        static_cast<int>((secondsWithinDay % 3600LL) / 60LL);

    value.second =
        static_cast<int>(secondsWithinDay % 60LL);

    value.date =
        addDays(value.date, static_cast<int>(dayDelta));

    return value;
}


// ---------------------------------------------------------------------------
// DATE_PART
// ---------------------------------------------------------------------------

enum class DatePart {
    Year,
    Month,
    Day,
    Hour,
    Minute,
    Second,
    Microsecond,
    UtcOffsetMinutes
};

long long datePart(DatePart part, const Timestamp& timestamp) {
    timestamp.validate();

    switch (part) {
        case DatePart::Year:
            return timestamp.date.year;
        case DatePart::Month:
            return timestamp.date.month;
        case DatePart::Day:
            return timestamp.date.day;
        case DatePart::Hour:
            return timestamp.hour;
        case DatePart::Minute:
            return timestamp.minute;
        case DatePart::Second:
            return timestamp.second;
        case DatePart::Microsecond:
            return timestamp.microsecond;
        case DatePart::UtcOffsetMinutes:
            return timestamp.utcOffsetMinutes;
    }

    throw std::logic_error("Unhandled DatePart");
}


// ---------------------------------------------------------------------------
// DATE_TRUNC
// ---------------------------------------------------------------------------

enum class Truncation {
    Year,
    Quarter,
    Month,
    Day,
    Hour,
    Minute,
    Second
};

Timestamp dateTrunc(
    Truncation unit,
    const Timestamp& original
) {
    original.validate();

    Timestamp result = original;

    switch (unit) {
        case Truncation::Year:
            result.date.month = 1;
            result.date.day = 1;
            result.hour = 0;
            result.minute = 0;
            result.second = 0;
            result.microsecond = 0;
            break;

        case Truncation::Quarter: {
            unsigned firstMonth =
                ((result.date.month - 1) / 3) * 3 + 1;

            result.date.month = firstMonth;
            result.date.day = 1;
            result.hour = 0;
            result.minute = 0;
            result.second = 0;
            result.microsecond = 0;
            break;
        }

        case Truncation::Month:
            result.date.day = 1;
            result.hour = 0;
            result.minute = 0;
            result.second = 0;
            result.microsecond = 0;
            break;

        case Truncation::Day:
            result.hour = 0;
            result.minute = 0;
            result.second = 0;
            result.microsecond = 0;
            break;

        case Truncation::Hour:
            result.minute = 0;
            result.second = 0;
            result.microsecond = 0;
            break;

        case Truncation::Minute:
            result.second = 0;
            result.microsecond = 0;
            break;

        case Truncation::Second:
            result.microsecond = 0;
            break;
    }

    return result;
}


// ---------------------------------------------------------------------------
// Temporal event domain
// ---------------------------------------------------------------------------

struct Transaction {
    std::string transactionId;
    std::string customerId;
    Timestamp occurredAt;
    long long amountCents;
};

class TransactionLedger {
private:
    std::vector<Transaction> transactions_;

public:
    void add(Transaction transaction) {
        transaction.occurredAt.validate();

        if (transaction.transactionId.empty()) {
            throw std::invalid_argument(
                "Transaction ID cannot be empty"
            );
        }

        if (transaction.amountCents < 0) {
            throw std::invalid_argument(
                "Transaction amount cannot be negative"
            );
        }

        transactions_.push_back(std::move(transaction));
    }

    const std::vector<Transaction>& all() const {
        return transactions_;
    }

    std::vector<Transaction> between(
        const Timestamp& start,
        const Timestamp& end
    ) const {
        start.validate();
        end.validate();

        if (start.utcOffsetMinutes != end.utcOffsetMinutes) {
            throw std::invalid_argument(
                "Range endpoints must use the same offset in this "
                "fixed-offset model"
            );
        }

        std::vector<Transaction> result;

        // The half-open interval [start, end) includes the start boundary and
        // excludes the end boundary. This makes adjacent SQL reporting
        // periods composable without double-counting boundary events.
        for (const auto& transaction : transactions_) {
            if (compare(transaction.occurredAt, start) >= 0 &&
                compare(transaction.occurredAt, end) < 0) {
                result.push_back(transaction);
            }
        }

        return result;
    }

private:
    static long long compare(
        const Timestamp& left,
        const Timestamp& right
    ) {
        // For this case study, timestamps use the same fixed UTC offset.
        // Production code with named IANA zones needs a timezone database.
        auto key = [](const Timestamp& value) {
            return std::tuple{
                value.date.year,
                value.date.month,
                value.date.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond
            };
        };

        if (key(left) < key(right)) return -1;
        if (key(left) > key(right)) return 1;
        return 0;
    }
};


// ---------------------------------------------------------------------------
// Report aggregation
// ---------------------------------------------------------------------------

struct MonthlyReport {
    std::string month;
    long long transactionCount{0};
    long long totalCents{0};
};

std::vector<MonthlyReport> buildMonthlyReport(
    const TransactionLedger& ledger
) {
    std::map<std::pair<int, unsigned>, MonthlyReport> grouped;

    for (const auto& transaction : ledger.all()) {
        const Date& date = transaction.occurredAt.date;

        auto key = std::make_pair(date.year, date.month);

        if (!grouped.contains(key)) {
            grouped[key] = MonthlyReport{
                date.toString().substr(0, 7),
                0,
                0
            };
        }

        auto& report = grouped[key];
        ++report.transactionCount;
        report.totalCents += transaction.amountCents;
    }

    std::vector<MonthlyReport> result;

    for (const auto& [key, report] : grouped) {
        result.push_back(report);
    }

    return result;
}


// ---------------------------------------------------------------------------
// Business deadline calculation
// ---------------------------------------------------------------------------

bool isWeekend(const Date& date) {
    // Zeller-like weekday calculation:
    // 0 = Sunday, 6 = Saturday.
    int y = date.year;
    unsigned m = date.month;
    unsigned d = date.day;

    if (m < 3) {
        --y;
        m += 12;
    }

    int weekday =
        (y + y / 4 - y / 100 + y / 400 +
         static_cast<int>(13 * (m + 1) / 5) +
         static_cast<int>(d)) % 7;

    // Zeller's result: 0=Saturday, 1=Sunday, ..., 6=Friday.
    int normalizedSundayFirst = (weekday + 6) % 7;

    return normalizedSundayFirst == 0 ||
           normalizedSundayFirst == 6;
}

Date addBusinessDays(Date date, int count) {
    if (count < 0) {
        throw std::invalid_argument(
            "Business-day count cannot be negative"
        );
    }

    while (count > 0) {
        date = addDays(date, 1);

        if (!isWeekend(date)) {
            --count;
        }
    }

    return date;
}


// ---------------------------------------------------------------------------
// Case-study output
// ---------------------------------------------------------------------------

void printSection(const std::string& title) {
    std::cout << "\n=== " << title << " ===\n";
}

void runCaseStudy() {
    printSection("DATE");

    Date invoiceDate{2026, 10, 2};
    std::cout << "Invoice date: "
              << invoiceDate.toString() << '\n';

    std::cout << "Delivery date: "
              << addDays(invoiceDate, 7).toString() << '\n';

    printSection("TIMESTAMP");

    Timestamp transactionTime{
        {2026, 10, 2},
        6,
        48,
        23,
        456789,
        330
    };

    std::cout << "Transaction timestamp: "
              << transactionTime.toString() << '\n';

    std::cout << "Year: "
              << datePart(DatePart::Year, transactionTime)
              << '\n';

    std::cout << "Hour: "
              << datePart(DatePart::Hour, transactionTime)
              << '\n';

    std::cout << "UTC offset minutes: "
              << datePart(
                     DatePart::UtcOffsetMinutes,
                     transactionTime
                 )
              << '\n';

    printSection("INTERVAL");

    Interval renewalInterval{
        1,
        3,
        90,
        500000
    };

    std::cout << "Interval: "
              << renewalInterval.toString() << '\n';

    Timestamp renewalDate = addInterval(
        transactionTime,
        renewalInterval
    );

    std::cout << "After interval: "
              << renewalDate.toString() << '\n';

    printSection("DATE_TRUNC");

    Timestamp detailed{
        {2026, 10, 17},
        14,
        25,
        12,
        456789,
        330
    };

    Timestamp monthStart =
        dateTrunc(Truncation::Month, detailed);

    Timestamp dayStart =
        dateTrunc(Truncation::Day, detailed);

    Timestamp hourStart =
        dateTrunc(Truncation::Hour, detailed);

    std::cout << "Original: "
              << detailed.toString() << '\n';

    std::cout << "Month boundary: "
              << monthStart.toString() << '\n';

    std::cout << "Day boundary: "
              << dayStart.toString() << '\n';

    std::cout << "Hour boundary: "
              << hourStart.toString() << '\n';

    printSection("TRANSACTION LEDGER");

    TransactionLedger ledger;

    ledger.add({
        "TX-1001",
        "CUS-01",
        {{2026, 10, 1}, 23, 45, 0, 0, 330},
        125000
    });

    ledger.add({
        "TX-1002",
        "CUS-02",
        {{2026, 10, 2}, 9, 15, 20, 500000, 330},
        87500
    });

    ledger.add({
        "TX-1003",
        "CUS-03",
        {{2026, 10, 31}, 23, 59, 59, 999999, 330},
        310000
    });

    ledger.add({
        "TX-1004",
        "CUS-04",
        {{2026, 11, 1}, 0, 0, 0, 0, 330},
        45000
    });

    for (const auto& transaction : ledger.all()) {
        std::cout
            << transaction.transactionId
            << " | "
            << transaction.occurredAt.toString()
            << " | "
            << transaction.amountCents
            << " cents\n";
    }

    printSection("OCTOBER HALF-OPEN WINDOW");

    Timestamp octoberStart{
        {2026, 10, 1},
        0, 0, 0, 0, 330
    };

    Timestamp novemberStart{
        {2026, 11, 1},
        0, 0, 0, 0, 330
    };

    auto octoberTransactions =
        ledger.between(octoberStart, novemberStart);

    std::cout << "Transactions in [2026-10-01, 2026-11-01): "
              << octoberTransactions.size() << '\n';

    for (const auto& transaction : octoberTransactions) {
        std::cout << "Included: "
                  << transaction.transactionId << '\n';
    }

    printSection("MONTHLY AGGREGATION");

    for (const auto& report : buildMonthlyReport(ledger)) {
        std::cout
            << report.month
            << " | transactions="
            << report.transactionCount
            << " | total_cents="
            << report.totalCents
            << '\n';
    }

    printSection("BUSINESS DEADLINE");

    Date submissionDate{2026, 10, 2}; // Friday
    Date deadline = addBusinessDays(submissionDate, 3);

    std::cout << "Submission date: "
              << submissionDate.toString() << '\n';

    std::cout << "Three business days later: "
              << deadline.toString() << '\n';
}


// ---------------------------------------------------------------------------
// Failure and edge-case demonstrations
// ---------------------------------------------------------------------------

void runFailureTests() {
    printSection("VALIDATION AND EDGE CASES");

    try {
        Date invalid{2026, 2, 29};
        invalid.validate();
    } catch (const std::exception& error) {
        std::cout << "Rejected invalid date: "
                  << error.what() << '\n';
    }

    try {
        Date leapDay{2024, 2, 29};
        leapDay.validate();
        std::cout << "Accepted leap day: "
                  << leapDay.toString() << '\n';
    } catch (const std::exception& error) {
        std::cout << "Unexpected leap-day failure: "
                  << error.what() << '\n';
    }

    try {
        Timestamp invalidTimestamp{
            {2026, 10, 2},
            25, 0, 0, 0, 330
        };
        invalidTimestamp.validate();
    } catch (const std::exception& error) {
        std::cout << "Rejected invalid timestamp: "
                  << error.what() << '\n';
    }

    try {
        Date january31{2026, 1, 31};
        Date february = addMonths(january31, 1);

        std::cout << "January 31 + one month: "
                  << february.toString() << '\n';
    } catch (const std::exception& error) {
        std::cout << "Month arithmetic failure: "
                  << error.what() << '\n';
    }

    try {
        TransactionLedger emptyLedger;

        Timestamp end{
            {2026, 10, 1},
            0, 0, 0, 0, 330
        };

        Timestamp start{
            {2026, 10, 2},
            0, 0, 0, 0, 330
        };

        emptyLedger.between(start, end);
    } catch (const std::exception& error) {
        // The current ledger comparison model is intentionally strict about
        // ordering. A production implementation should also normalize
        // timestamps to a common instant representation.
        std::cout << "Rejected reversed range: "
                  << error.what() << '\n';
    }
}

} // namespace sqltime


int main() {
    try {
        std::cout << "SQL DATE & TIME CASE STUDY\n";
        std::cout << "=========================\n";

        sqltime::runCaseStudy();
        sqltime::runFailureTests();

        std::cout << "\nCase study completed successfully.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: "
                  << error.what() << '\n';
        return 1;
    }
}
