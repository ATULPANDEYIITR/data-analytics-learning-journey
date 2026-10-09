#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using namespace std;

/*
 * Repository-independent operational analytics case study:
 * A distribution company analyzes daily revenue observations from multiple
 * regional warehouses. The system computes percentiles, conditional
 * aggregates, row-based rolling metrics, calendar-based rolling metrics,
 * consecutive reporting islands, and missing reporting intervals.
 *
 * C++17 implementation.
 *
 * Money is stored in integer paise. Percentile interpolation uses long
 * double because a percentile can fall between observed monetary values.
 */

struct Date {
    int year;
    int month;
    int day;

    auto key() const {
        return tuple<int, int, int>{year, month, day};
    }

    bool operator<(const Date& other) const {
        return key() < other.key();
    }

    bool operator==(const Date& other) const {
        return key() == other.key();
    }

    bool operator!=(const Date& other) const {
        return !(*this == other);
    }
};

bool leapYear(int year) {
    return year % 400 == 0 || (year % 4 == 0 && year % 100 != 0);
}

Date parseDate(const string& text) {
    if (text.size() != 10 || text[4] != '-' || text[7] != '-') {
        throw invalid_argument("Date must use YYYY-MM-DD.");
    }

    Date result{
        stoi(text.substr(0, 4)),
        stoi(text.substr(5, 2)),
        stoi(text.substr(8, 2))
    };

    if (result.month < 1 || result.month > 12) {
        throw invalid_argument("Invalid month.");
    }

    static const int monthLengths[] = {
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    };

    int maximumDay = monthLengths[result.month - 1];
    if (result.month == 2 && leapYear(result.year)) {
        maximumDay = 29;
    }

    if (result.day < 1 || result.day > maximumDay) {
        throw invalid_argument("Invalid day for calendar month.");
    }

    return result;
}

string formatDate(const Date& date) {
    ostringstream output;
    output << setfill('0')
           << setw(4) << date.year << '-'
           << setw(2) << date.month << '-'
           << setw(2) << date.day;
    return output.str();
}

long long daysFromCivil(Date date) {
    int year = date.year;
    const unsigned month = static_cast<unsigned>(date.month);
    const unsigned day = static_cast<unsigned>(date.day);

    year -= month <= 2;
    const int era = (year >= 0 ? year : year - 399) / 400;
    const unsigned yearOfEra = static_cast<unsigned>(year - era * 400);
    const unsigned adjustedMonth = month > 2 ? month - 3 : month + 9;
    const unsigned dayOfYear =
        (153 * adjustedMonth + 2) / 5 + day - 1;
    const unsigned dayOfEra =
        yearOfEra * 365 + yearOfEra / 4 - yearOfEra / 100 + dayOfYear;

    return static_cast<long long>(era) * 146097 +
           static_cast<long long>(dayOfEra);
}

Date civilFromDays(long long serial) {
    const long long era = (serial >= 0 ? serial : serial - 146096) / 146097;
    const unsigned dayOfEra =
        static_cast<unsigned>(serial - era * 146097);
    const unsigned yearOfEra =
        (dayOfEra - dayOfEra / 1460 + dayOfEra / 36524 -
         dayOfEra / 146096) / 365;
    int year = static_cast<int>(yearOfEra) + static_cast<int>(era * 400);
    const unsigned dayOfYear =
        dayOfEra - (365 * yearOfEra + yearOfEra / 4 - yearOfEra / 100);
    const unsigned monthPrime = (5 * dayOfYear + 2) / 153;
    const unsigned day = dayOfYear - (153 * monthPrime + 2) / 5 + 1;
    const unsigned month = monthPrime < 10 ? monthPrime + 3 : monthPrime - 9;

    year += month <= 2;
    return {year, static_cast<int>(month), static_cast<int>(day)};
}

Date addDays(Date date, int count) {
    return civilFromDays(daysFromCivil(date) + count);
}

enum class Status {
    Completed,
    Cancelled,
    Pending
};

string statusName(Status status) {
    switch (status) {
        case Status::Completed: return "completed";
        case Status::Cancelled: return "cancelled";
        case Status::Pending: return "pending";
    }
    throw logic_error("Unreachable status.");
}

struct DailyRecord {
    Date date;
    string region;
    long long revenuePaise;
    int orders;
    Status status;
};

class OperationalAnalytics {
private:
    vector<DailyRecord> records;

    static void validate(const DailyRecord& record) {
        if (record.region.empty()) {
            throw invalid_argument("Region must not be empty.");
        }
        if (record.revenuePaise < 0 || record.orders < 0) {
            throw invalid_argument("Revenue and orders must be nonnegative.");
        }
    }

public:
    explicit OperationalAnalytics(vector<DailyRecord> input)
        : records(move(input)) {
        for (const auto& record : records) {
            validate(record);
        }
    }

    static long double percentileCont(vector<long long> values, long double p) {
        if (values.empty()) {
            throw invalid_argument("Percentile requires observations.");
        }
        if (p < 0 || p > 1) {
            throw invalid_argument("Percentile must be in [0, 1].");
        }

        sort(values.begin(), values.end());
        const long double position = p * (values.size() - 1);
        const size_t lower = static_cast<size_t>(floor(position));
        const size_t upper = min(lower + 1, values.size() - 1);
        const long double fraction = position - lower;

        return values[lower] +
               fraction * (values[upper] - values[lower]);
    }

    static long long percentileDisc(vector<long long> values, long double p) {
        if (values.empty()) {
            throw invalid_argument("Percentile requires observations.");
        }
        if (p < 0 || p > 1) {
            throw invalid_argument("Percentile must be in [0, 1].");
        }

        sort(values.begin(), values.end());
        size_t position = static_cast<size_t>(ceil(p * values.size()));
        position = max<size_t>(1, position);
        return values[position - 1];
    }

    void printConditionalAggregates() const {
        struct Summary {
            long long completedRevenue = 0;
            long long completedOrders = 0;
            long long cancelledOrders = 0;
            size_t completedDays = 0;
            size_t cancelledDays = 0;
            size_t pendingDays = 0;
        };

        map<string, Summary> summaries;

        // Each row contributes to exactly the status-specific measures.
        for (const auto& record : records) {
            auto& summary = summaries[record.region];

            switch (record.status) {
                case Status::Completed:
                    summary.completedRevenue += record.revenuePaise;
                    summary.completedOrders += record.orders;
                    ++summary.completedDays;
                    break;
                case Status::Cancelled:
                    summary.cancelledOrders += record.orders;
                    ++summary.cancelledDays;
                    break;
                case Status::Pending:
                    ++summary.pendingDays;
                    break;
            }
        }

        cout << "\nConditional aggregates by region\n";
        for (const auto& [region, summary] : summaries) {
            cout << region
                 << " | completed revenue Rs "
                 << fixed << setprecision(2)
                 << static_cast<long double>(summary.completedRevenue) / 100
                 << " | completed orders " << summary.completedOrders
                 << " | cancelled orders " << summary.cancelledOrders
                 << " | completed days " << summary.completedDays
                 << " | cancelled days " << summary.cancelledDays
                 << " | pending days " << summary.pendingDays << '\n';
        }
    }

    void printPercentiles(const string& region) const {
        vector<long long> values;

        for (const auto& record : records) {
            if (record.region == region && record.status == Status::Completed) {
                values.push_back(record.revenuePaise);
            }
        }

        if (values.empty()) {
            cout << "\nNo completed revenue observations for " << region << '\n';
            return;
        }

        cout << "\nRevenue percentiles for " << region << '\n';
        for (long double p : {0.50L, 0.90L, 0.95L}) {
            const long double continuous = percentileCont(values, p);
            const long long discrete = percentileDisc(values, p);

            cout << fixed << setprecision(2)
                 << "p=" << p
                 << " continuous Rs " << continuous / 100
                 << ", discrete Rs "
                 << static_cast<long double>(discrete) / 100 << '\n';
        }
    }

    void printRollingRows(size_t frameSize) const {
        if (frameSize == 0) {
            throw invalid_argument("Frame size must be positive.");
        }

        map<string, vector<DailyRecord>> partitions;
        for (const auto& record : records) {
            partitions[record.region].push_back(record);
        }

        cout << "\nTrailing row-based revenue windows\n";

        for (auto& [region, partition] : partitions) {
            sort(partition.begin(), partition.end(),
                 [](const DailyRecord& a, const DailyRecord& b) {
                     return a.date < b.date;
                 });

            for (size_t index = 0; index < partition.size(); ++index) {
                const size_t start =
                    index + 1 > frameSize ? index + 1 - frameSize : 0;

                long long total = 0;
                for (size_t cursor = start; cursor <= index; ++cursor) {
                    total += partition[cursor].revenuePaise;
                }

                cout << region << " | "
                     << formatDate(partition[index].date)
                     << " | sum Rs " << fixed << setprecision(2)
                     << static_cast<long double>(total) / 100
                     << " | rows " << index - start + 1 << '\n';
            }
        }
    }

    void printCalendarRolling(Date first, Date last, int frameDays) const {
        if (first > last || frameDays < 1) {
            throw invalid_argument("Invalid reporting range or frame size.");
        }

        map<string, map<long long, long long>> daily;
        for (const auto& record : records) {
            daily[record.region][daysFromCivil(record.date)] +=
                record.revenuePaise;
        }

        cout << "\nCalendar-based rolling revenue\n";
        for (const auto& [region, values] : daily) {
            for (Date current = first; !(last < current); current = addDays(current, 1)) {
                long long total = 0;
                const long long currentSerial = daysFromCivil(current);

                for (int offset = 0; offset < frameDays; ++offset) {
                    auto found = values.find(currentSerial - offset);
                    if (found != values.end()) {
                        total += found->second;
                    }
                }

                cout << region << " | " << formatDate(current)
                     << " | Rs " << fixed << setprecision(2)
                     << static_cast<long double>(total) / 100 << '\n';
            }
        }
    }

    static vector<tuple<Date, Date, int>> findIslands(vector<Date> dates) {
        sort(dates.begin(), dates.end());
        dates.erase(unique(dates.begin(), dates.end()), dates.end());

        vector<tuple<Date, Date, int>> islands;
        if (dates.empty()) return islands;

        Date start = dates.front();
        Date previous = dates.front();

        for (size_t index = 1; index < dates.size(); ++index) {
            Date current = dates[index];

            if (daysFromCivil(current) - daysFromCivil(previous) != 1) {
                islands.emplace_back(
                    start, previous,
                    static_cast<int>(
                        daysFromCivil(previous) - daysFromCivil(start) + 1
                    )
                );
                start = current;
            }
            previous = current;
        }

        islands.emplace_back(
            start, previous,
            static_cast<int>(
                daysFromCivil(previous) - daysFromCivil(start) + 1
            )
        );

        return islands;
    }

    static vector<tuple<Date, Date, int>> findGaps(
        const vector<Date>& observations,
        Date first,
        Date last
    ) {
        if (last < first) {
            throw invalid_argument("Reporting end precedes reporting start.");
        }

        set<long long> observed;
        for (Date date : observations) {
            if (!(date < first) && !(last < date)) {
                observed.insert(daysFromCivil(date));
            }
        }

        vector<tuple<Date, Date, int>> gaps;
        optional<Date> gapStart;

        for (Date current = first; !(last < current); current = addDays(current, 1)) {
            const bool exists = observed.count(daysFromCivil(current)) != 0;

            if (!exists && !gapStart.has_value()) {
                gapStart = current;
            } else if (exists && gapStart.has_value()) {
                Date gapEnd = addDays(current, -1);
                gaps.emplace_back(
                    *gapStart, gapEnd,
                    static_cast<int>(
                        daysFromCivil(gapEnd) - daysFromCivil(*gapStart) + 1
                    )
                );
                gapStart.reset();
            }
        }

        if (gapStart.has_value()) {
            gaps.emplace_back(
                *gapStart, last,
                static_cast<int>(
                    daysFromCivil(last) - daysFromCivil(*gapStart) + 1
                )
            );
        }

        return gaps;
    }
};

int main() {
    try {
        vector<DailyRecord> records{
            {parseDate("2026-09-01"), "North", 120000, 24, Status::Completed},
            {parseDate("2026-09-02"), "North", 135000, 27, Status::Completed},
            {parseDate("2026-09-03"), "North", 0, 0, Status::Cancelled},
            {parseDate("2026-09-04"), "North", 182000, 36, Status::Completed},
            {parseDate("2026-09-06"), "North", 160000, 32, Status::Completed},
            {parseDate("2026-09-07"), "North", 175000, 35, Status::Completed},
            {parseDate("2026-09-08"), "North", 210000, 42, Status::Completed},
            {parseDate("2026-09-09"), "North", 90000, 18, Status::Pending},
            {parseDate("2026-09-10"), "North", 240000, 48, Status::Completed},
            {parseDate("2026-09-11"), "North", 195000, 39, Status::Completed},
            {parseDate("2026-09-12"), "North", 260000, 52, Status::Completed},
            {parseDate("2026-09-13"), "North", 80000, 16, Status::Cancelled},
            {parseDate("2026-09-15"), "North", 285000, 57, Status::Completed},
            {parseDate("2026-09-16"), "North", 300000, 60, Status::Completed},
            {parseDate("2026-09-17"), "North", 275000, 55, Status::Completed},
            {parseDate("2026-09-01"), "South", 95000, 19, Status::Completed},
            {parseDate("2026-09-02"), "South", 110000, 22, Status::Completed},
            {parseDate("2026-09-04"), "South", 155000, 31, Status::Completed},
            {parseDate("2026-09-05"), "South", 175000, 35, Status::Completed}
        };

        OperationalAnalytics analytics(move(records));
        analytics.printConditionalAggregates();
        analytics.printPercentiles("North");
        analytics.printRollingRows(3);
        analytics.printCalendarRolling(
            parseDate("2026-09-01"),
            parseDate("2026-09-07"),
            3
        );

        vector<Date> observed{
            parseDate("2026-09-01"),
            parseDate("2026-09-02"),
            parseDate("2026-09-04"),
            parseDate("2026-09-05"),
            parseDate("2026-09-06"),
            parseDate("2026-09-09")
        };

        cout << "\nConsecutive reporting islands\n";
        for (const auto& [start, end, count] :
             OperationalAnalytics::findIslands(observed)) {
            cout << formatDate(start) << " through " << formatDate(end)
                 << " (" << count << " days)\n";
        }

        cout << "\nMissing reporting intervals\n";
        for (const auto& [start, end, count] :
             OperationalAnalytics::findGaps(
                 observed,
                 parseDate("2026-09-01"),
                 parseDate("2026-09-10")
             )) {
            cout << formatDate(start) << " through " << formatDate(end)
                 << " (" << count << " missing days)\n";
        }

        cout << "\nEdge-case checks\n";
        try {
            OperationalAnalytics::percentileCont({}, 0.5L);
        } catch (const invalid_argument& error) {
            cout << "Empty percentile rejected: " << error.what() << '\n';
        }

        try {
            parseDate("2026-02-30");
        } catch (const invalid_argument& error) {
            cout << "Invalid date rejected: " << error.what() << '\n';
        }
    } catch (const exception& error) {
        cerr << "Analytics failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
