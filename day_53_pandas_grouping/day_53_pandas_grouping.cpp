#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

using namespace std;

struct Order {
    int id;
    string region;
    string department;
    string channel;
    string product;
    string segment;
    int units;
    double unitPrice;
    double discount;
    bool returned;

    double revenue() const {
        return units * unitPrice;
    }

    double netRevenue() const {
        return revenue() * (1.0 - discount);
    }

    bool highValue(double threshold) const {
        return netRevenue() >= threshold;
    }
};

struct RegionalMetrics {
    int orders = 0;
    int units = 0;
    double revenue = 0.0;
    int returnedOrders = 0;
};

struct DepartmentMetrics {
    int orders = 0;
    double revenue = 0.0;
    double minimum = 0.0;
    double maximum = 0.0;
};

struct GovernanceReport {
    map<string, RegionalMetrics> regions;
    map<string, DepartmentMetrics> departments;
    map<pair<string, string>, double> pivot;
    map<pair<string, string>, int> crosstab;
};

class RepositorySalesEngine {
public:
    explicit RepositorySalesEngine(vector<Order> orders)
        : orders_(move(orders)) {
        validateOrders();
    }

    GovernanceReport analyze() const {
        GovernanceReport report;

        for (const auto& order : orders_) {
            auto& region = report.regions[order.region];
            region.orders++;
            region.units += order.units;
            region.revenue += order.netRevenue();
            if (order.returned) {
                region.returnedOrders++;
            }

            auto& department = report.departments[order.department];

            if (department.orders == 0) {
                department.minimum = order.netRevenue();
                department.maximum = order.netRevenue();
            } else {
                department.minimum =
                    min(department.minimum, order.netRevenue());
                department.maximum =
                    max(department.maximum, order.netRevenue());
            }

            department.orders++;
            department.revenue += order.netRevenue();

            // Pivot-table semantics: two categorical dimensions form
            // the coordinates and numeric revenue forms the measure.
            report.pivot[{order.region, order.channel}] += order.netRevenue();

            // Crosstab semantics: categorical combinations are counted.
            report.crosstab[{order.department, order.channel}]++;
        }

        return report;
    }

    map<int, double> regionShareByOrder() const {
        unordered_map<string, double> totals;

        for (const auto& order : orders_) {
            totals[order.region] += order.netRevenue();
        }

        map<int, double> shares;

        for (const auto& order : orders_) {
            const double total = totals.at(order.region);

            if (total <= 0.0) {
                throw runtime_error("Cannot compute share from zero revenue.");
            }

            shares[order.id] = order.netRevenue() / total;
        }

        return shares;
    }

    vector<Order> filterHighValue(double threshold) const {
        vector<Order> result;

        copy_if(
            orders_.begin(),
            orders_.end(),
            back_inserter(result),
            [threshold](const Order& order) {
                return order.highValue(threshold);
            }
        );

        return result;
    }

    double totalNetRevenue() const {
        return accumulate(
            orders_.begin(),
            orders_.end(),
            0.0,
            [](double total, const Order& order) {
                return total + order.netRevenue();
            }
        );
    }

    void validateGroupingInvariant(const GovernanceReport& report) const {
        double groupedRevenue = 0.0;

        for (const auto& [region, metrics] : report.regions) {
            (void)region;
            groupedRevenue += metrics.revenue;
        }

        if (fabs(groupedRevenue - totalNetRevenue()) > 1e-8) {
            throw runtime_error(
                "Grouped revenue does not reconcile with source revenue."
            );
        }

        const auto shares = regionShareByOrder();

        unordered_map<string, double> shareTotals;

        for (const auto& order : orders_) {
            shareTotals[order.region] += shares.at(order.id);
        }

        for (const auto& [region, total] : shareTotals) {
            if (fabs(total - 1.0) > 1e-8) {
                throw runtime_error(
                    "Transform-style shares do not sum to one for " + region
                );
            }
        }
    }

private:
    vector<Order> orders_;

    void validateOrders() const {
        if (orders_.empty()) {
            throw runtime_error("The dataset cannot be empty.");
        }

        map<int, bool> identifiers;

        for (const auto& order : orders_) {
            if (identifiers.contains(order.id)) {
                throw runtime_error("Duplicate order ID detected.");
            }

            identifiers[order.id] = true;

            if (order.units <= 0) {
                throw runtime_error("Units must be positive.");
            }

            if (order.unitPrice < 0.0) {
                throw runtime_error("Unit price cannot be negative.");
            }

            if (order.discount < 0.0 || order.discount > 1.0) {
                throw runtime_error("Discount must be within [0, 1].");
            }

            if (order.region.empty() || order.department.empty()) {
                throw runtime_error("Grouping dimensions cannot be empty.");
            }
        }
    }
};

void printReport(const GovernanceReport& report) {
    cout << fixed << setprecision(2);

    cout << "\nREGION GROUPING\n";
    cout << left
         << setw(12) << "Region"
         << setw(10) << "Orders"
         << setw(10) << "Units"
         << setw(16) << "NetRevenue"
         << setw(16) << "Returned"
         << '\n';

    for (const auto& [region, metrics] : report.regions) {
        cout << left
             << setw(12) << region
             << setw(10) << metrics.orders
             << setw(10) << metrics.units
             << setw(16) << metrics.revenue
             << setw(16) << metrics.returnedOrders
             << '\n';
    }

    cout << "\nDEPARTMENT AGGREGATION\n";

    for (const auto& [department, metrics] : report.departments) {
        const double mean = metrics.revenue / metrics.orders;

        cout << department
             << " orders=" << metrics.orders
             << " mean=" << mean
             << " min=" << metrics.minimum
             << " max=" << metrics.maximum
             << '\n';
    }

    cout << "\nPIVOT TABLE: REGION x CHANNEL\n";

    for (const auto& [key, value] : report.pivot) {
        cout << key.first << " | "
             << key.second << " | "
             << value << '\n';
    }

    cout << "\nCROSSTAB: DEPARTMENT x CHANNEL\n";

    for (const auto& [key, count] : report.crosstab) {
        cout << key.first << " | "
             << key.second << " | "
             << count << '\n';
    }
}

int main() {
    try {
        vector<Order> orders = {
            {1001, "North", "Cloud", "Online", "Compute", "Enterprise", 8, 1200, 0.05, false},
            {1002, "North", "Security", "Partner", "Firewall", "Enterprise", 4, 2100, 0.00, false},
            {1003, "South", "Cloud", "Online", "Storage", "SMB", 15, 400, 0.10, false},
            {1004, "West", "Data", "Direct", "Analytics", "Enterprise", 6, 1800, 0.05, false},
            {1005, "East", "Security", "Online", "Identity", "SMB", 20, 250, 0.00, true},
            {1006, "North", "Data", "Partner", "Analytics", "SMB", 5, 1800, 0.15, false},
            {1007, "South", "Security", "Direct", "Firewall", "Enterprise", 3, 2100, 0.05, false},
            {1008, "West", "Cloud", "Online", "Compute", "SMB", 12, 1200, 0.00, false},
            {1009, "East", "Data", "Direct", "Analytics", "Enterprise", 7, 1800, 0.10, false},
            {1010, "North", "Cloud", "Partner", "Storage", "SMB", 30, 400, 0.05, false},
            {1011, "South", "Cloud", "Online", "Compute", "Enterprise", 5, 1200, 0.00, false},
            {1012, "West", "Security", "Partner", "Identity", "SMB", 18, 250, 0.10, true},
            {1013, "East", "Cloud", "Direct", "Storage", "SMB", 22, 400, 0.05, false},
            {1014, "North", "Data", "Online", "Analytics", "Enterprise", 4, 1800, 0.00, false},
            {1015, "South", "Security", "Online", "Firewall", "SMB", 9, 2100, 0.15, false},
            {1016, "West", "Cloud", "Direct", "Compute", "Enterprise", 10, 1200, 0.05, false},
            {1017, "East", "Security", "Partner", "Identity", "Enterprise", 11, 250, 0.00, false},
            {1018, "North", "Data", "Direct", "Analytics", "SMB", 8, 1800, 0.10, true}
        };

        RepositorySalesEngine engine(move(orders));
        GovernanceReport report = engine.analyze();

        engine.validateGroupingInvariant(report);

        printReport(report);

        const auto highValue = engine.filterHighValue(5000.0);

        cout << "\nHIGH-VALUE ORDERS\n";
        for (const auto& order : highValue) {
            cout << order.id
                 << " | "
                 << order.region
                 << " | "
                 << order.netRevenue()
                 << '\n';
        }

        cout << "\nVALIDATION\n";
        cout << "Total net revenue: "
             << engine.totalNetRevenue()
             << '\n';
        cout << "Grouping invariants passed.\n";

    } catch (const exception& error) {
        cerr << "Analysis failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
