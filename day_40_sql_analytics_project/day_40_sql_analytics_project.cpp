#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * Repository-style business analytics is represented here as a sales
 * performance engine. The program focuses on the C++ perspective:
 * strongly typed domain objects, indexed aggregation, deterministic
 * calculations, validation, and explicit complexity.
 */

enum class OrderStatus {
    Completed,
    Cancelled,
    Returned,
    Pending
};

string statusName(OrderStatus status) {
    switch (status) {
        case OrderStatus::Completed: return "Completed";
        case OrderStatus::Cancelled: return "Cancelled";
        case OrderStatus::Returned: return "Returned";
        case OrderStatus::Pending: return "Pending";
    }
    return "Unknown";
}

struct LineItem {
    string product;
    string category;
    int quantity;
    double unitPrice;
    double unitCost;
};

struct Order {
    int id;
    string customer;
    string segment;
    string region;
    string month;
    OrderStatus status;
    double discount;
    vector<LineItem> items;
};

struct Metric {
    double revenue = 0.0;
    double profit = 0.0;
    int units = 0;
    int orders = 0;
};

class AnalyticsEngine {
private:
    vector<Order> orders;

    static double netRevenue(const LineItem& item, double discount) {
        return item.quantity * item.unitPrice * (1.0 - discount);
    }

    static double profit(const LineItem& item, double discount) {
        return item.quantity *
               (item.unitPrice * (1.0 - discount) - item.unitCost);
    }

    static void validateItem(const LineItem& item) {
        if (item.quantity <= 0) {
            throw invalid_argument("Quantity must be positive.");
        }
        if (item.unitPrice <= 0) {
            throw invalid_argument("Unit price must be positive.");
        }
        if (item.unitCost < 0 || item.unitCost > item.unitPrice) {
            throw invalid_argument("Invalid unit cost.");
        }
    }

    static void validateOrder(const Order& order) {
        if (order.id <= 0) {
            throw invalid_argument("Order ID must be positive.");
        }
        if (order.discount < 0 || order.discount > 1) {
            throw invalid_argument("Discount must be between zero and one.");
        }
        if (order.items.empty()) {
            throw invalid_argument("Order must contain at least one item.");
        }

        for (const auto& item : order.items) {
            validateItem(item);
        }
    }

public:
    explicit AnalyticsEngine(vector<Order> source)
        : orders(move(source)) {
        for (const auto& order : orders) {
            validateOrder(order);
        }
    }

    vector<Order> completedOrders() const {
        vector<Order> result;

        copy_if(
            orders.begin(),
            orders.end(),
            back_inserter(result),
            [](const Order& order) {
                return order.status == OrderStatus::Completed;
            }
        );

        return result;
    }

    map<string, Metric> performanceByRegion() const {
        map<string, Metric> result;

        /*
         * Aggregation is O(N * L), where N is the number of orders and
         * L is the average number of line items. map insertion is O(log R),
         * which is useful when deterministic sorted regional output is wanted.
         */
        for (const auto& order : completedOrders()) {
            auto& metric = result[order.region];
            metric.orders++;

            for (const auto& item : order.items) {
                metric.units += item.quantity;
                metric.revenue += netRevenue(item, order.discount);
                metric.profit += profit(item, order.discount);
            }
        }

        return result;
    }

    map<string, Metric> performanceByCategory() const {
        map<string, Metric> result;

        for (const auto& order : completedOrders()) {
            for (const auto& item : order.items) {
                auto& metric = result[item.category];
                metric.units += item.quantity;
                metric.revenue += netRevenue(item, order.discount);
                metric.profit += profit(item, order.discount);
            }
        }

        return result;
    }

    unordered_map<string, Metric> performanceByCustomer() const {
        unordered_map<string, Metric> result;

        for (const auto& order : completedOrders()) {
            auto& metric = result[order.customer];
            metric.orders++;

            for (const auto& item : order.items) {
                metric.units += item.quantity;
                metric.revenue += netRevenue(item, order.discount);
                metric.profit += profit(item, order.discount);
            }
        }

        return result;
    }

    map<string, double> monthlyRevenue() const {
        map<string, double> result;

        for (const auto& order : completedOrders()) {
            for (const auto& item : order.items) {
                result[order.month] += netRevenue(item, order.discount);
            }
        }

        return result;
    }

    optional<pair<string, Metric>> bestRegion() const {
        const auto metrics = performanceByRegion();

        if (metrics.empty()) {
            return nullopt;
        }

        auto best = max_element(
            metrics.begin(),
            metrics.end(),
            [](const auto& left, const auto& right) {
                return left.second.revenue < right.second.revenue;
            }
        );

        return make_pair(best->first, best->second);
    }

    void printDashboard() const {
        const auto regions = performanceByRegion();
        const auto categories = performanceByCategory();
        const auto customers = performanceByCustomer();
        const auto months = monthlyRevenue();

        cout << fixed << setprecision(2);

        cout << "\n=== REGIONAL PERFORMANCE ===\n";
        for (const auto& [region, metric] : regions) {
            const double margin =
                metric.revenue == 0
                    ? 0
                    : metric.profit / metric.revenue * 100;

            cout << region
                 << " | Orders: " << metric.orders
                 << " | Units: " << metric.units
                 << " | Revenue: " << metric.revenue
                 << " | Profit: " << metric.profit
                 << " | Margin: " << margin << "%\n";
        }

        cout << "\n=== CATEGORY PERFORMANCE ===\n";
        for (const auto& [category, metric] : categories) {
            cout << category
                 << " | Units: " << metric.units
                 << " | Revenue: " << metric.revenue
                 << " | Profit: " << metric.profit << "\n";
        }

        cout << "\n=== CUSTOMER PERFORMANCE ===\n";
        vector<pair<string, Metric>> rankedCustomers(
            customers.begin(), customers.end()
        );

        sort(
            rankedCustomers.begin(),
            rankedCustomers.end(),
            [](const auto& left, const auto& right) {
                return left.second.revenue > right.second.revenue;
            }
        );

        for (const auto& [customer, metric] : rankedCustomers) {
            cout << customer
                 << " | Orders: " << metric.orders
                 << " | Revenue: " << metric.revenue << "\n";
        }

        cout << "\n=== MONTHLY REVENUE ===\n";
        double runningRevenue = 0.0;

        for (const auto& [month, revenue] : months) {
            runningRevenue += revenue;
            cout << month
                 << " | Revenue: " << revenue
                 << " | Running total: " << runningRevenue << "\n";
        }

        if (auto best = bestRegion()) {
            cout << "\nHighest-revenue region: "
                 << best->first
                 << " with revenue "
                 << best->second.revenue
                 << "\n";
        }

        const int completed = static_cast<int>(completedOrders().size());
        const int total = static_cast<int>(orders.size());

        cout << "\nCompleted-order rate: "
             << (total == 0 ? 0.0 : completed * 100.0 / total)
             << "%\n";
    }
};

int main() {
    try {
        vector<Order> orders = {
            {
                1,
                "Atlas Consulting",
                "Corporate",
                "North",
                "2026-01",
                OrderStatus::Completed,
                0.05,
                {
                    {"Business Laptop", "Electronics", 3, 1200, 820},
                    {"Security Monitor", "Electronics", 2, 650, 390}
                }
            },
            {
                2,
                "BluePeak Retail",
                "Small Business",
                "South",
                "2026-01",
                OrderStatus::Completed,
                0.10,
                {
                    {"Laser Printer", "Office Equipment", 4, 550, 340}
                }
            },
            {
                3,
                "Cedar Finance",
                "Corporate",
                "East",
                "2026-02",
                OrderStatus::Returned,
                0.00,
                {
                    {"Analytics Suite", "Software", 3, 900, 180}
                }
            },
            {
                4,
                "Delta Health",
                "Corporate",
                "West",
                "2026-02",
                OrderStatus::Completed,
                0.15,
                {
                    {"Conference Desk", "Furniture", 2, 780, 470},
                    {"Ergonomic Chair", "Furniture", 5, 360, 210}
                }
            },
            {
                5,
                "Evergreen Traders",
                "Small Business",
                "North",
                "2026-03",
                OrderStatus::Cancelled,
                0.00,
                {
                    {"Network Router", "Electronics", 5, 420, 260}
                }
            },
            {
                6,
                "Falcon Services",
                "Consumer",
                "South",
                "2026-03",
                OrderStatus::Completed,
                0.05,
                {
                    {"Document Scanner", "Office Equipment", 3, 310, 180},
                    {"Analytics Suite", "Software", 1, 900, 180}
                }
            },
            {
                7,
                "Granite Labs",
                "Corporate",
                "East",
                "2026-04",
                OrderStatus::Completed,
                0.10,
                {
                    {"Business Laptop", "Electronics", 4, 1200, 820}
                }
            }
        };

        AnalyticsEngine engine(orders);
        engine.printDashboard();

        /*
         * The invalid record demonstrates why validation belongs close to
         * the domain boundary. Bad economics are rejected before aggregation,
         * preventing corrupted KPIs from entering downstream reports.
         */
        try {
            Order invalid{
                99,
                "Invalid Customer",
                "Corporate",
                "North",
                "2026-04",
                OrderStatus::Completed,
                0.05,
                {
                    {"Business Laptop", "Electronics", 1, 1200, 1500}
                }
            };

            AnalyticsEngine rejected({invalid});
        } catch (const exception& error) {
            cout << "\nValidation failure correctly detected: "
                 << error.what() << "\n";
        }

        return 0;
    } catch (const exception& error) {
        cerr << "Analytics engine failed: " << error.what() << '\n';
        return 1;
    }
}
