#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using namespace std;

struct Date {
    int year;
    int month;
    int day;

    auto key() const {
        return tuple<int, int, int>(year, month, day);
    }

    bool operator<(const Date& other) const {
        return key() < other.key();
    }

    bool operator==(const Date& other) const {
        return key() == other.key();
    }
};

bool isLeapYear(int year) {
    return year % 400 == 0 ||
           (year % 4 == 0 && year % 100 != 0);
}

int daysInMonth(int year, int month) {
    static const int days[] = {
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    };

    if (month < 1 || month > 12) {
        throw invalid_argument("Invalid month.");
    }

    if (month == 2 && isLeapYear(year)) {
        return 29;
    }

    return days[month - 1];
}

bool validDate(const Date& d) {
    return d.year >= 1 &&
           d.month >= 1 &&
           d.month <= 12 &&
           d.day >= 1 &&
           d.day <= daysInMonth(d.year, d.month);
}

Date shiftYear(const Date& d, int offset) {
    Date result = d;
    result.year += offset;
    result.day = min(result.day, daysInMonth(result.year, result.month));
    return result;
}

Date shiftMonth(const Date& d, int offset) {
    int index = d.year * 12 + d.month - 1 + offset;

    int targetYear = index / 12;
    int targetMonth = index % 12 + 1;

    int originalLast = daysInMonth(d.year, d.month);
    int targetLast = daysInMonth(targetYear, targetMonth);

    int targetDay = d.day == originalLast
        ? targetLast
        : min(d.day, targetLast);

    return {targetYear, targetMonth, targetDay};
}

int dayNumber(const Date& d) {
    static const int cumulative[] = {
        0, 31, 59, 90, 120, 151,
        181, 212, 243, 273, 304, 334
    };

    int result = cumulative[d.month - 1] + d.day;

    if (d.month > 2 && isLeapYear(d.year)) {
        ++result;
    }

    return result;
}

long long ordinal(const Date& d) {
    long long y = d.year - 1;

    return 365LL * y +
           y / 4 -
           y / 100 +
           y / 400 +
           dayNumber(d);
}

Date fromOrdinal(long long value) {
    int low = 1;
    int high = 10000;

    while (low < high) {
        int mid = low + (high - low) / 2;
        long long start = ordinal({mid, 1, 1});

        if (start <= value) {
            low = mid + 1;
        } else {
            high = mid;
        }
    }

    int year = low - 1;

    if (year < 1 || year > 9999) {
        throw out_of_range("Date outside supported range.");
    }

    int remaining = static_cast<int>(
        value - ordinal({year, 1, 1})
    ) + 1;

    int month = 1;

    while (remaining > daysInMonth(year, month)) {
        remaining -= daysInMonth(year, month);
        ++month;
    }

    return {year, month, remaining};
}

Date addDays(const Date& d, int offset) {
    return fromOrdinal(ordinal(d) + offset);
}

struct Transaction {
    int id;
    Date date;
    string product;
    string region;
    double amount;
};

enum class Period {
    MTD,
    QTD,
    YTD
};

class SalesAnalytics {
private:
    map<Date, double> salesByDate;
    set<int> transactionIds;
    set<Date> calendar;
    Date calendarStart;
    Date calendarEnd;

    void validateSelection(const vector<Date>& dates) const {
        if (dates.empty()) {
            throw invalid_argument("Date selection cannot be empty.");
        }

        for (const auto& d : dates) {
            if (!validDate(d) || !calendar.count(d)) {
                throw invalid_argument("Date outside calendar.");
            }
        }
    }

    vector<Date> dateRange(Date start, Date end) const {
        vector<Date> result;

        for (Date current = start; !(end < current);
             current = addDays(current, 1)) {
            if (calendar.count(current)) {
                result.push_back(current);
            }
        }

        return result;
    }

public:
    SalesAnalytics(Date start, Date end)
        : calendarStart(start), calendarEnd(end) {

        if (!validDate(start) || !validDate(end) || end < start) {
            throw invalid_argument("Invalid calendar boundaries.");
        }

        for (Date d = start; !(end < d); d = addDays(d, 1)) {
            calendar.insert(d);
        }
    }

    void addTransaction(const Transaction& transaction) {
        if (transaction.id <= 0 ||
            !transactionIds.insert(transaction.id).second) {
            throw invalid_argument("Invalid or duplicate transaction ID.");
        }

        if (!validDate(transaction.date) ||
            !calendar.count(transaction.date)) {
            transactionIds.erase(transaction.id);
            throw invalid_argument("Transaction date outside calendar.");
        }

        if (!isfinite(transaction.amount) || transaction.amount < 0) {
            transactionIds.erase(transaction.id);
            throw invalid_argument("Invalid transaction amount.");
        }

        salesByDate[transaction.date] += transaction.amount;
    }

    double sales(const vector<Date>& dates) const {
        validateSelection(dates);

        double total = 0;

        for (const Date& d : dates) {
            auto it = salesByDate.find(d);

            if (it != salesByDate.end()) {
                total += it->second;
            }
        }

        return total;
    }

    vector<Date> dateadd(
        const vector<Date>& dates,
        int offset,
        const string& unit
    ) const {
        validateSelection(dates);

        vector<Date> result;

        for (const Date& d : dates) {
            Date shifted;

            if (unit == "YEAR") {
                shifted = shiftYear(d, offset);
            } else if (unit == "MONTH") {
                shifted = shiftMonth(d, offset);
            } else if (unit == "DAY") {
                shifted = addDays(d, offset);
            } else {
                throw invalid_argument("Unsupported date unit.");
            }

            if (calendar.count(shifted)) {
                result.push_back(shifted);
            }
        }

        sort(result.begin(), result.end());
        result.erase(unique(result.begin(), result.end()), result.end());

        return result;
    }

    double samePeriodLastYear(const vector<Date>& dates) const {
        return sales(dateadd(dates, -1, "YEAR"));
    }

    double periodToDate(
        const vector<Date>& dates,
        Period period
    ) const {
        validateSelection(dates);

        Date end = *max_element(dates.begin(), dates.end());

        Date start = end;

        if (period == Period::MTD) {
            start.day = 1;
        } else if (period == Period::QTD) {
            start.month = ((end.month - 1) / 3) * 3 + 1;
            start.day = 1;
        } else {
            start.month = 1;
            start.day = 1;
        }

        return sales(dateRange(start, end));
    }

    double rolling(const vector<Date>& dates, int days) const {
        validateSelection(dates);

        if (days <= 0) {
            throw invalid_argument("Rolling days must be positive.");
        }

        Date end = *max_element(dates.begin(), dates.end());
        Date start = addDays(end, -(days - 1));

        return sales(dateRange(start, end));
    }

    void report(const vector<Date>& selection) const {
        double current = sales(selection);
        double previous = samePeriodLastYear(selection);

        double difference = current - previous;

        cout << fixed << setprecision(2);
        cout << "\nTIME INTELLIGENCE REPORT\n";
        cout << "------------------------\n";
        cout << "Current sales: " << current << '\n';
        cout << "Previous year: " << previous << '\n';
        cout << "Difference: " << difference << '\n';

        if (previous != 0) {
            cout << "Growth: "
                 << difference / previous * 100
                 << "%\n";
        } else {
            cout << "Growth: Not defined (zero baseline)\n";
        }

        cout << "MTD: "
             << periodToDate(selection, Period::MTD) << '\n';

        cout << "QTD: "
             << periodToDate(selection, Period::QTD) << '\n';

        cout << "YTD: "
             << periodToDate(selection, Period::YTD) << '\n';

        cout << "Rolling 30 days: "
             << rolling(selection, 30) << '\n';
    }
};

void runTests() {
    SalesAnalytics analytics(
        {2024, 1, 1},
        {2026, 12, 31}
    );

    analytics.addTransaction({
        1, {2025, 1, 15}, "Laptop", "North", 16000
    });

    analytics.addTransaction({
        2, {2026, 1, 15}, "Laptop", "North", 21000
    });

    analytics.addTransaction({
        3, {2026, 2, 10}, "Phone", "South", 14000
    });

    vector<Date> january = {{2026, 1, 15}};

    if (analytics.sales(january) != 21000) {
        throw runtime_error("Sales aggregation test failed.");
    }

    if (analytics.samePeriodLastYear(january) != 16000) {
        throw runtime_error("Previous-year calculation failed.");
    }

    if (analytics.periodToDate(
            {{2026, 2, 10}}, Period::YTD
        ) != 35000) {
        throw runtime_error("YTD test failed.");
    }

    if (!(shiftYear({2024, 2, 29}, -1) == Date{2023, 2, 28})) {
        throw runtime_error("Leap-year test failed.");
    }

    cout << "All C++ validation tests passed.\n";
}

int main() {
    try {
        SalesAnalytics analytics(
            {2024, 1, 1},
            {2026, 12, 31}
        );

        vector<Transaction> transactions = {
            {1, {2024, 1, 15}, "Laptop", "North", 12000},
            {2, {2024, 2, 10}, "Phone", "South", 8000},
            {3, {2025, 1, 15}, "Laptop", "North", 16000},
            {4, {2025, 2, 10}, "Phone", "South", 11000},
            {5, {2025, 3, 20}, "Laptop", "West", 18000},
            {6, {2025, 4, 12}, "Tablet", "East", 9000},
            {7, {2026, 1, 15}, "Laptop", "North", 21000},
            {8, {2026, 2, 10}, "Phone", "South", 14000},
            {9, {2026, 3, 20}, "Laptop", "West", 24000},
            {10, {2026, 4, 12}, "Tablet", "East", 12000},
            {11, {2026, 5, 18}, "Phone", "North", 10000},
            {12, {2026, 6, 22}, "Laptop", "South", 19000},
            {13, {2026, 7, 14}, "Tablet", "West", 13000},
            {14, {2026, 8, 9}, "Phone", "East", 8500},
            {15, {2026, 9, 11}, "Laptop", "North", 22000},
            {16, {2026, 10, 19}, "Tablet", "South", 11500},
            {17, {2026, 11, 5}, "Phone", "West", 9500},
            {18, {2026, 11, 15}, "Laptop", "East", 17000}
        };

        for (const auto& transaction : transactions) {
            analytics.addTransaction(transaction);
        }

        analytics.report({
            {2026, 11, 1},
            {2026, 11, 15}
        });

        cout << "\nDATEADD PREVIOUS MONTH\n";

        Date previous = shiftMonth({2026, 11, 15}, -1);

        cout << previous.year << '-'
             << previous.month << '-'
             << previous.day << '\n';

        cout << "\nLEAP YEAR VALIDATION\n";
        Date leapShift = shiftYear({2024, 2, 29}, -1);

        cout << leapShift.year << '-'
             << leapShift.month << '-'
             << leapShift.day << '\n';

        runTests();

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
