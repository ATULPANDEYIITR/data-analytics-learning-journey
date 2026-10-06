#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * SQL Data Quality Case Study
 *
 * Scenario:
 * A retail data platform receives customer and order records from several
 * operational systems. Before records are loaded into an analytical system,
 * a governance engine evaluates duplicates, missing attributes, broken
 * relationships, domain violations, and statistical anomalies.
 *
 * The C++ implementation focuses on an in-memory governance engine. Its
 * purpose is not to replace SQL, but to show how the same quality rules can
 * become a reusable service around a relational data pipeline.
 */

enum class Severity {
    Low,
    Medium,
    High,
    Critical
};

string severityName(Severity severity) {
    switch (severity) {
        case Severity::Low:
            return "LOW";
        case Severity::Medium:
            return "MEDIUM";
        case Severity::High:
            return "HIGH";
        case Severity::Critical:
            return "CRITICAL";
    }
    return "UNKNOWN";
}

struct Customer {
    int id;
    string name;
    string email;
    string phone;
};

struct Order {
    int id;
    int customerId;
    double amount;
    string orderDate;
    string status;
};

struct QualityIssue {
    string rule;
    string entity;
    string key;
    Severity severity;
    string message;
};

class QualityReport {
private:
    vector<QualityIssue> issues;

public:
    void add(QualityIssue issue) {
        issues.push_back(std::move(issue));
    }

    const vector<QualityIssue>& all() const {
        return issues;
    }

    size_t count() const {
        return issues.size();
    }

    void print() const {
        cout << "\n=== QUALITY ISSUES ===\n";

        for (const auto& issue : issues) {
            cout << '[' << severityName(issue.severity) << "] "
                 << issue.rule << " "
                 << issue.entity << ':' << issue.key
                 << " - " << issue.message << '\n';
        }

        if (issues.empty()) {
            cout << "No quality violations detected.\n";
        }
    }
};

class RepositoryQualityEngine {
private:
    const vector<Customer>& customers;
    const vector<Order>& orders;
    QualityReport report;

    static string normalize(string value) {
        transform(
            value.begin(),
            value.end(),
            value.begin(),
            [](unsigned char c) {
                return static_cast<char>(tolower(c));
            }
        );

        while (!value.empty() && isspace(
            static_cast<unsigned char>(value.front()))) {
            value.erase(value.begin());
        }

        while (!value.empty() && isspace(
            static_cast<unsigned char>(value.back()))) {
            value.pop_back();
        }

        return value;
    }

    static bool missing(const string& value) {
        return value.empty() ||
            all_of(
                value.begin(),
                value.end(),
                [](unsigned char c) {
                    return isspace(c);
                }
            );
    }

    static double percentile(vector<double> values, double p) {
        if (values.empty()) {
            throw invalid_argument("Percentile requires non-empty data.");
        }

        sort(values.begin(), values.end());

        double position =
            (static_cast<double>(values.size()) - 1.0) * p;

        size_t lower = static_cast<size_t>(floor(position));
        size_t upper = static_cast<size_t>(ceil(position));

        if (lower == upper) {
            return values[lower];
        }

        double fraction = position - static_cast<double>(lower);

        return values[lower] +
            (values[upper] - values[lower]) * fraction;
    }

    void checkMissingValues() {
        for (const auto& customer : customers) {
            if (missing(customer.name)) {
                report.add({
                    "missing_value",
                    "customers",
                    to_string(customer.id),
                    Severity::Medium,
                    "Customer name is missing."
                });
            }

            if (missing(customer.email)) {
                report.add({
                    "missing_value",
                    "customers",
                    to_string(customer.id),
                    Severity::Medium,
                    "Customer email is missing."
                });
            }

            if (missing(customer.phone)) {
                report.add({
                    "missing_value",
                    "customers",
                    to_string(customer.id),
                    Severity::Medium,
                    "Customer phone is missing."
                });
            }
        }
    }

    void checkDuplicates() {
        /*
         * A surrogate primary key cannot reveal business duplicates. The
         * grouping key therefore uses normalized email plus normalized name.
         */
        map<string, vector<int>> groups;

        for (const auto& customer : customers) {
            if (missing(customer.email)) {
                continue;
            }

            string key =
                normalize(customer.email) + "|" +
                normalize(customer.name);

            groups[key].push_back(customer.id);
        }

        for (const auto& [key, ids] : groups) {
            if (ids.size() > 1) {
                ostringstream detail;

                detail << "Business identity occurs for customer IDs: ";

                for (size_t index = 0; index < ids.size(); ++index) {
                    if (index > 0) {
                        detail << ", ";
                    }
                    detail << ids[index];
                }

                report.add({
                    "duplicate_customer",
                    "customers",
                    key,
                    Severity::High,
                    detail.str()
                });
            }
        }
    }

    void checkReferentialIntegrity() {
        unordered_map<int, bool> customerIds;

        for (const auto& customer : customers) {
            customerIds[customer.id] = true;
        }

        for (const auto& order : orders) {
            if (!customerIds.contains(order.customerId)) {
                report.add({
                    "orphan_order",
                    "orders",
                    to_string(order.id),
                    Severity::Critical,
                    "Order references a customer that does not exist."
                });
            }
        }
    }

    void checkDomainRules() {
        const set<string> allowedStatuses = {
            "pending",
            "paid",
            "cancelled",
            "refunded"
        };

        for (const auto& order : orders) {
            if (!isfinite(order.amount) || order.amount <= 0.0) {
                report.add({
                    "invalid_amount",
                    "orders",
                    to_string(order.id),
                    Severity::High,
                    "Order amount must be finite and greater than zero."
                });
            }

            if (order.orderDate.empty()) {
                report.add({
                    "missing_order_date",
                    "orders",
                    to_string(order.id),
                    Severity::High,
                    "Order date is required."
                });
            }

            if (!allowedStatuses.contains(order.status)) {
                report.add({
                    "invalid_status",
                    "orders",
                    to_string(order.id),
                    Severity::High,
                    "Order status is outside the allowed domain."
                });
            }
        }
    }

    void checkAmountAnomalies() {
        vector<double> amounts;

        for (const auto& order : orders) {
            if (isfinite(order.amount) && order.amount > 0.0) {
                amounts.push_back(order.amount);
            }
        }

        if (amounts.size() < 4) {
            return;
        }

        double q1 = percentile(amounts, 0.25);
        double q3 = percentile(amounts, 0.75);
        double upperFence = q3 + 1.5 * (q3 - q1);

        for (const auto& order : orders) {
            if (order.amount > upperFence) {
                ostringstream detail;
                detail << fixed << setprecision(2)
                       << "Amount " << order.amount
                       << " exceeds IQR upper fence "
                       << upperFence << '.';

                report.add({
                    "amount_anomaly",
                    "orders",
                    to_string(order.id),
                    Severity::High,
                    detail.str()
                });
            }
        }
    }

    void checkDailyOrderVelocity() {
        /*
         * The key corresponds to the SQL GROUP BY customer_id, order_date
         * operation. The resulting frequency distribution is evaluated with
         * a three-standard-deviation threshold.
         */
        map<pair<int, string>, int> dailyCounts;

        for (const auto& order : orders) {
            if (order.customerId > 0 && !order.orderDate.empty()) {
                dailyCounts[{order.customerId, order.orderDate}]++;
            }
        }

        if (dailyCounts.size() < 2) {
            return;
        }

        vector<double> counts;

        for (const auto& [key, count] : dailyCounts) {
            counts.push_back(static_cast<double>(count));
        }

        double average =
            accumulate(counts.begin(), counts.end(), 0.0) /
            static_cast<double>(counts.size());

        double variance = 0.0;

        for (double count : counts) {
            variance += pow(count - average, 2.0);
        }

        variance /= static_cast<double>(counts.size());

        double standardDeviation = sqrt(variance);
        double threshold = average + 3.0 * standardDeviation;

        for (const auto& [key, count] : dailyCounts) {
            if (static_cast<double>(count) > threshold) {
                ostringstream detail;

                detail << count
                       << " orders exceed daily activity threshold "
                       << fixed << setprecision(2)
                       << threshold << '.';

                report.add({
                    "order_velocity_anomaly",
                    "orders",
                    to_string(key.first) + ":" + key.second,
                    Severity::High,
                    detail.str()
                });
            }
        }
    }

public:
    RepositoryQualityEngine(
        const vector<Customer>& customerData,
        const vector<Order>& orderData
    )
        : customers(customerData), orders(orderData) {}

    QualityReport run() {
        checkMissingValues();
        checkDuplicates();
        checkReferentialIntegrity();
        checkDomainRules();
        checkAmountAnomalies();
        checkDailyOrderVelocity();

        return report;
    }
};

double calculateQualityScore(const QualityReport& report,
                             size_t sourceRowCount) {
    if (sourceRowCount == 0) {
        return 100.0;
    }

    double penalty = 0.0;

    for (const auto& issue : report.all()) {
        switch (issue.severity) {
            case Severity::Critical:
                penalty += 5.0;
                break;
            case Severity::High:
                penalty += 3.0;
                break;
            case Severity::Medium:
                penalty += 1.0;
                break;
            case Severity::Low:
                penalty += 0.5;
                break;
        }
    }

    return max(
        0.0,
        100.0 - (penalty / static_cast<double>(sourceRowCount)) * 20.0
    );
}

void demonstrateTransactionalThinking() {
    /*
     * C++ does not provide a database transaction by itself. This function
     * models the decision boundary that a database transaction would enforce:
     * stage a repair, validate its postcondition, then commit or discard.
     */
    cout << "\n=== REPAIR TRANSACTION MODEL ===\n";
    cout << "A safe remediation follows: stage change -> validate -> commit.\n";
    cout << "If validation fails, the database transaction should roll back.\n";
}

int main() {
    vector<Customer> customers = {
        {1, "Asha Verma", "asha@example.com", "9876500001"},
        {2, "Ravi Kumar", "ravi@example.com", "9876500002"},
        {3, "Ravi Kumar", "ravi@example.com", "9876500002"},
        {4, "Meera Shah", "", "9876500004"},
        {5, "", "meera2@example.com", ""},
        {6, "Kabir Singh", "kabir@example.com", "9876500006"},
        {7, "Nisha Rao", "nisha@example.com", "9876500007"},
        {8, "Omar Khan", "omarkhan@example.com", "9876500008"}
    };

    vector<Order> orders = {
        {101, 1, 120.50, "2026-10-01", "paid"},
        {102, 2, 80.00, "2026-10-01", "paid"},
        {103, 2, 75.00, "2026-10-01", "paid"},
        {104, 2, 70.00, "2026-10-01", "paid"},
        {105, 2, 65.00, "2026-10-01", "paid"},
        {106, 2, 55.00, "2026-10-01", "paid"},
        {107, 6, 150.00, "2026-10-02", "pending"},
        {108, 7, 210.00, "2026-10-02", "paid"},
        {109, 8, 9999.00, "2026-10-02", "paid"},
        {110, 1, 95.00, "2026-10-03", "cancelled"},
        {111, 999, 45.00, "2026-10-03", "paid"}
    };

    RepositoryQualityEngine engine(customers, orders);
    QualityReport report = engine.run();

    report.print();

    cout << "\n=== QUALITY SCORE ===\n";
    cout << fixed << setprecision(2)
         << calculateQualityScore(
                report,
                customers.size() + orders.size()
            )
         << "/100\n";

    demonstrateTransactionalThinking();

    cout << "\n=== CASE STUDY DESIGN ===\n";
    cout << "Duplicate detection uses business identity rather than "
            "surrogate IDs.\n";
    cout << "Missing-value checks distinguish absent attributes from valid "
            "empty business states.\n";
    cout << "Referential checks model parent-child integrity between "
            "customers and orders.\n";
    cout << "Anomaly detection uses IQR for monetary outliers and a "
            "three-sigma rule for daily activity.\n";

    return 0;
}
