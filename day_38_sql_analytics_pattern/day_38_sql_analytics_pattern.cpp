#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * Technical case study:
 * A product analytics service receives user activity and must determine
 * revenue leaders, cohort retention, funnel progression, and behavioral
 * segments without counting the same user multiple times at a stage.
 *
 * The design intentionally separates:
 *   - event facts
 *   - user dimensions
 *   - derived analytical metrics
 *
 * This resembles the logical separation commonly achieved with SQL CTEs
 * and window functions.
 */

struct User {
    int id;
    string signupMonth;
    string country;
    string channel;
};

struct Event {
    int userId;
    string month;
    string type;
    double amount = 0.0;
};

struct Product {
    string id;
    string name;
    string category;
    double revenue;
};

struct UserMetrics {
    int activity = 0;
    int purchases = 0;
    double revenue = 0.0;
};

struct FunnelRow {
    string stage;
    int users;
    double conversion;
};

static void printHeader(const string& title) {
    cout << "\n============================================================\n";
    cout << title << "\n";
    cout << "============================================================\n";
}

static vector<Product> topNProducts(const vector<Product>& products, int n) {
    if (n <= 0) {
        throw invalid_argument("n must be positive");
    }

    vector<Product> ordered = products;

    sort(
        ordered.begin(),
        ordered.end(),
        [](const Product& a, const Product& b) {
            if (a.revenue != b.revenue) {
                return a.revenue > b.revenue;
            }
            return a.id < b.id;
        }
    );

    /*
     * Dense-rank behavior: products with identical revenue share a rank.
     * This differs from simply taking the first n rows.
     */
    vector<Product> result;
    int rank = 0;
    double previousRevenue = -1.0;

    for (const auto& product : ordered) {
        if (product.revenue != previousRevenue) {
            ++rank;
            previousRevenue = product.revenue;
        }

        if (rank <= n) {
            result.push_back(product);
        }
    }

    return result;
}

static map<string, vector<int>> prepareCohorts(const vector<User>& users) {
    map<string, vector<int>> cohorts;

    for (const auto& user : users) {
        cohorts[user.signupMonth].push_back(user.id);
    }

    return cohorts;
}

static map<string, map<int, set<int>>> buildRetentionActivity(
    const vector<User>& users,
    const vector<Event>& events
) {
    unordered_map<int, string> signupMonth;

    for (const auto& user : users) {
        signupMonth[user.id] = user.signupMonth;
    }

    /*
     * The sample data uses month labels. A production system would normally
     * calculate period offsets from actual timestamps or a calendar dimension.
     */
    map<string, map<int, set<int>>> activity;

    for (const auto& event : events) {
        if (
            event.type != "login" &&
            event.type != "view_product" &&
            event.type != "add_to_cart" &&
            event.type != "purchase"
        ) {
            continue;
        }

        const string& cohort = signupMonth.at(event.userId);

        int cohortYear = stoi(cohort.substr(0, 4));
        int cohortMonth = stoi(cohort.substr(5, 2));
        int eventYear = stoi(event.month.substr(0, 4));
        int eventMonth = stoi(event.month.substr(5, 2));

        int period = (eventYear - cohortYear) * 12
                   + (eventMonth - cohortMonth);

        if (period >= 0) {
            activity[cohort][period].insert(event.userId);
        }
    }

    return activity;
}

static vector<map<string, string>> calculateRetention(
    const vector<User>& users,
    const vector<Event>& events
) {
    auto cohorts = prepareCohorts(users);
    auto activity = buildRetentionActivity(users, events);

    vector<map<string, string>> rows;

    for (const auto& [cohort, members] : cohorts) {
        for (int period = 0; period <= 1; ++period) {
            size_t retained = activity[cohort][period].size();

            double percentage = members.empty()
                ? 0.0
                : static_cast<double>(retained) / members.size() * 100.0;

            rows.push_back({
                {"cohort", cohort},
                {"period", to_string(period)},
                {"cohort_size", to_string(members.size())},
                {"retained", to_string(retained)},
                {"retention_pct", to_string(percentage)}
            });
        }
    }

    return rows;
}

static vector<FunnelRow> calculateFunnel(
    const vector<User>& users,
    const vector<Event>& events
) {
    const vector<pair<string, string>> stages = {
        {"signup", "signup"},
        {"product_view", "view_product"},
        {"cart", "add_to_cart"},
        {"checkout", "checkout_started"},
        {"purchase", "purchase"}
    };

    unordered_map<int, set<string>> userEvents;

    for (const auto& event : events) {
        userEvents[event.userId].insert(event.type);
    }

    vector<FunnelRow> result;
    int previous = 0;

    for (size_t index = 0; index < stages.size(); ++index) {
        const auto& [stageName, eventName] = stages[index];

        int count = 0;

        for (const auto& user : users) {
            if (userEvents[user.id].contains(eventName)) {
                ++count;
            }
        }

        double conversion;

        if (index == 0) {
            conversion = count == 0 ? 0.0 : 100.0;
        } else if (previous == 0) {
            conversion = 0.0;
        } else {
            conversion = static_cast<double>(count) / previous * 100.0;
        }

        result.push_back({stageName, count, conversion});
        previous = count;
    }

    return result;
}

static map<int, UserMetrics> calculateMetrics(
    const vector<Event>& events
) {
    map<int, UserMetrics> metrics;

    for (const auto& event : events) {
        if (
            event.type == "login" ||
            event.type == "view_product" ||
            event.type == "add_to_cart"
        ) {
            metrics[event.userId].activity++;
        }

        if (event.type == "purchase") {
            metrics[event.userId].purchases++;
            metrics[event.userId].revenue += event.amount;
        }
    }

    return metrics;
}

static string classify(const UserMetrics& metrics) {
    if (metrics.purchases >= 2 || metrics.revenue >= 300.0) {
        return "high_value";
    }

    if (metrics.purchases > 0) {
        return "buyer";
    }

    if (metrics.activity >= 3) {
        return "engaged_non_buyer";
    }

    return "low_activity";
}

static void printSegments(
    const vector<User>& users,
    const map<int, UserMetrics>& metrics
) {
    cout << left
         << setw(8) << "User"
         << setw(18) << "Activity"
         << setw(12) << "Purchases"
         << setw(14) << "Revenue"
         << "Segment\n";

    for (const auto& user : users) {
        auto it = metrics.find(user.id);
        UserMetrics current;

        if (it != metrics.end()) {
            current = it->second;
        }

        cout << left
             << setw(8) << user.id
             << setw(18) << current.activity
             << setw(12) << current.purchases
             << setw(14) << fixed << setprecision(2) << current.revenue
             << classify(current)
             << '\n';
    }
}

static void demonstrateCohortRetention(
    const vector<User>& users,
    const vector<Event>& events
) {
    printHeader("Cohort Retention");

    auto rows = calculateRetention(users, events);

    cout << left
         << setw(12) << "Cohort"
         << setw(10) << "Period"
         << setw(14) << "Cohort Size"
         << setw(12) << "Retained"
         << "Retention\n";

    for (const auto& row : rows) {
        cout << left
             << setw(12) << row.at("cohort")
             << setw(10) << row.at("period")
             << setw(14) << row.at("cohort_size")
             << setw(12) << row.at("retained")
             << row.at("retention_pct")
             << '\n';
    }
}

static void demonstrateFunnel(
    const vector<User>& users,
    const vector<Event>& events
) {
    printHeader("Unique-User Funnel");

    auto funnel = calculateFunnel(users, events);

    cout << left
         << setw(20) << "Stage"
         << setw(12) << "Users"
         << "Conversion From Previous\n";

    for (const auto& row : funnel) {
        cout << left
             << setw(20) << row.stage
             << setw(12) << row.users
             << fixed << setprecision(1)
             << row.conversion << "%\n";
    }
}

int main() {
    try {
        vector<User> users = {
            {1, "2026-01", "IN", "organic"},
            {2, "2026-01", "IN", "paid"},
            {3, "2026-01", "US", "organic"},
            {4, "2026-01", "IN", "referral"},
            {5, "2026-02", "DE", "paid"},
            {6, "2026-02", "IN", "organic"},
            {7, "2026-02", "US", "paid"},
            {8, "2026-02", "IN", "referral"}
        };

        vector<Event> events = {
            {1, "2026-01", "signup"},
            {1, "2026-01", "view_product"},
            {1, "2026-01", "add_to_cart"},
            {1, "2026-01", "checkout_started"},
            {1, "2026-01", "purchase", 300.0},
            {1, "2026-02", "login"},

            {2, "2026-01", "signup"},
            {2, "2026-01", "view_product"},
            {2, "2026-01", "add_to_cart"},
            {2, "2026-01", "checkout_started"},
            {2, "2026-01", "purchase", 180.0},

            {3, "2026-01", "signup"},
            {3, "2026-01", "view_product"},
            {3, "2026-02", "login"},

            {4, "2026-01", "signup"},
            {4, "2026-01", "view_product"},
            {4, "2026-01", "add_to_cart"},

            {5, "2026-02", "signup"},
            {5, "2026-02", "view_product"},
            {5, "2026-02", "add_to_cart"},
            {5, "2026-02", "checkout_started"},
            {5, "2026-02", "purchase", 230.0},
            {5, "2026-03", "login"},

            {6, "2026-02", "signup"},
            {6, "2026-02", "view_product"},
            {6, "2026-03", "login"},

            {7, "2026-02", "signup"},
            {7, "2026-02", "view_product"},

            {8, "2026-02", "signup"},
            {8, "2026-02", "view_product"},
            {8, "2026-02", "add_to_cart"}
        };

        vector<Product> products = {
            {"P100", "Analytics Platform", "software", 18200.0},
            {"P200", "Operations Suite", "software", 15700.0},
            {"P300", "Data Connector", "integration", 15700.0},
            {"P400", "Audit Module", "governance", 11900.0},
            {"P500", "Forecasting Module", "analytics", 9400.0}
        };

        printHeader("Top-N With Dense Ranking");

        auto leaders = topNProducts(products, 3);

        cout << left
             << setw(10) << "Product"
             << setw(26) << "Name"
             << setw(14) << "Revenue\n";

        for (const auto& product : leaders) {
            cout << left
                 << setw(10) << product.id
                 << setw(26) << product.name
                 << fixed << setprecision(2)
                 << product.revenue << '\n';
        }

        auto cohorts = prepareCohorts(users);

        printHeader("Cohort Preparation");

        for (const auto& [cohort, members] : cohorts) {
            cout << cohort << ": ";
            for (int id : members) {
                cout << id << ' ';
            }
            cout << '\n';
        }

        demonstrateCohortRetention(users, events);
        demonstrateFunnel(users, events);

        printHeader("Behavioral Segmentation");

        auto metrics = calculateMetrics(events);
        printSegments(users, metrics);

        printHeader("Analytical Design Decisions");

        cout << "Top-N uses dense rank semantics so revenue ties are preserved.\n";
        cout << "Retention counts distinct users per cohort and activity period.\n";
        cout << "Funnel stages count unique users, not raw event rows.\n";
        cout << "Segmentation applies deterministic rules to activity, purchases, and revenue.\n";
        cout << "Maps and sets prevent accidental double-counting during aggregation.\n";

        printHeader("Failure Conditions");

        try {
            topNProducts(products, 0);
        } catch (const invalid_argument& error) {
            cout << "Invalid Top-N request rejected: "
                 << error.what() << '\n';
        }

        /*
         * The standard containers provide memory safety for this analytical
         * workload. For large event streams, database-side aggregation or
         * streaming aggregation would usually be preferable to materializing
         * the entire event set in memory.
         */
    } catch (const exception& error) {
        cerr << "Analytics engine failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
