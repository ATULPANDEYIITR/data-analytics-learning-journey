#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <numeric>

/*
 * POWER BI INTRODUCTION
 *
 * C++17 Business Intelligence Governance and Processing Engine.
 *
 * Implements:
 * - Repository-independent BI data architecture
 * - Source and dimensional data management
 * - Fact table processing
 * - Report definitions
 * - KPI calculations
 * - Refresh lifecycle
 * - Dashboard publication controls
 * - Access permissions
 * - Merge-like publication eligibility evaluation
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic power_bi.cpp -o power_bi
 */

using namespace std;

// ============================================================
// 1. DOMAIN ENUMS
// ============================================================

enum class RefreshStatus {
    NOT_STARTED,
    RUNNING,
    SUCCEEDED,
    FAILED
};

enum class PublicationStatus {
    DRAFT,
    REVIEW,
    APPROVED,
    PUBLISHED,
    REJECTED
};

enum class Permission {
    VIEW,
    BUILD,
    PUBLISH,
    ADMIN
};

enum class VisualType {
    KPI_CARD,
    BAR_CHART,
    LINE_CHART,
    PIE_CHART,
    TABLE
};

string toString(RefreshStatus status) {
    switch (status) {
        case RefreshStatus::NOT_STARTED: return "NOT_STARTED";
        case RefreshStatus::RUNNING: return "RUNNING";
        case RefreshStatus::SUCCEEDED: return "SUCCEEDED";
        case RefreshStatus::FAILED: return "FAILED";
    }
    return "UNKNOWN";
}

string toString(PublicationStatus status) {
    switch (status) {
        case PublicationStatus::DRAFT: return "DRAFT";
        case PublicationStatus::REVIEW: return "REVIEW";
        case PublicationStatus::APPROVED: return "APPROVED";
        case PublicationStatus::PUBLISHED: return "PUBLISHED";
        case PublicationStatus::REJECTED: return "REJECTED";
    }
    return "UNKNOWN";
}

// ============================================================
// 2. DOMAIN STRUCTURES
// ============================================================

struct Customer {
    int id;
    string name;
    string region;
    string segment;
};

struct Product {
    int id;
    string name;
    string category;
    double unitCost;
};

struct Transaction {
    int id;
    int customerId;
    int productId;
    string date;
    int quantity;
    double unitPrice;
};

struct FactSale {
    int transactionId;
    int customerId;
    int productId;
    string customerName;
    string productName;
    string region;
    string category;
    string date;
    int quantity;
    double revenue;
    double cost;
    double profit;
};

struct KPI {
    string name;
    double value;
    string unit;
};

struct Visual {
    string title;
    VisualType type;
    string dimension;
    string measure;
};

struct Report {
    int id;
    string name;
    string owner;
    string description;
    PublicationStatus status;
    vector<Visual> visuals;
};

struct User {
    string username;
    set<Permission> permissions;
};

// ============================================================
// 3. EXCEPTIONS
// ============================================================

class BIException : public runtime_error {
public:
    explicit BIException(const string& message)
        : runtime_error(message) {}
};

// ============================================================
// 4. SOURCE DATA REPOSITORY
// ============================================================

class SourceRepository {

private:
    vector<Customer> customers;
    vector<Product> products;
    vector<Transaction> transactions;

public:

    SourceRepository() {

        customers = {
            {1, "Aarav Sharma", "North", "Enterprise"},
            {2, "Meera Verma", "South", "Consumer"},
            {3, "Rohan Gupta", "East", "Enterprise"},
            {4, "Ananya Singh", "West", "Consumer"},
            {5, "Kabir Patel", "North", "Small Business"}
        };

        products = {
            {101, "Laptop", "Electronics", 45000},
            {102, "Monitor", "Electronics", 12000},
            {103, "Office Chair", "Furniture", 5000},
            {104, "Desk", "Furniture", 8000},
            {105, "Keyboard", "Accessories", 1000}
        };

        transactions = {
            {1001, 1, 101, "2026-01-10", 2, 65000},
            {1002, 2, 102, "2026-01-15", 3, 18000},
            {1003, 3, 103, "2026-02-05", 5, 8500},
            {1004, 4, 104, "2026-02-12", 2, 12000},
            {1005, 1, 105, "2026-03-01", 10, 1800},
            {1006, 5, 101, "2026-03-15", 1, 68000},
            {1007, 3, 102, "2026-04-02", 4, 17500},
            {1008, 2, 103, "2026-04-08", 3, 9000},
            {1009, 4, 105, "2026-05-10", 15, 1600},
            {1010, 5, 104, "2026-05-18", 3, 12500}
        };
    }

    const vector<Customer>& getCustomers() const {
        return customers;
    }

    const vector<Product>& getProducts() const {
        return products;
    }

    const vector<Transaction>& getTransactions() const {
        return transactions;
    }
};

// ============================================================
// 5. VALIDATION ENGINE
// ============================================================

class DataValidator {

public:

    static void validate(const SourceRepository& source) {

        set<int> customerIds;
        set<int> productIds;
        set<int> transactionIds;

        for (const auto& customer : source.getCustomers()) {

            if (customer.id <= 0 ||
                customer.name.empty() ||
                customer.region.empty()) {
                throw BIException("Invalid customer dimension.");
            }

            if (!customerIds.insert(customer.id).second) {
                throw BIException("Duplicate customer identifier.");
            }
        }

        for (const auto& product : source.getProducts()) {

            if (product.id <= 0 ||
                product.name.empty() ||
                product.unitCost < 0) {
                throw BIException("Invalid product dimension.");
            }

            if (!productIds.insert(product.id).second) {
                throw BIException("Duplicate product identifier.");
            }
        }

        for (const auto& transaction : source.getTransactions()) {

            if (!transactionIds.insert(transaction.id).second) {
                throw BIException("Duplicate transaction identifier.");
            }

            if (!customerIds.count(transaction.customerId)) {
                throw BIException("Unknown customer foreign key.");
            }

            if (!productIds.count(transaction.productId)) {
                throw BIException("Unknown product foreign key.");
            }

            if (transaction.quantity <= 0 ||
                transaction.unitPrice < 0) {
                throw BIException("Invalid transaction amount.");
            }

            if (transaction.date.size() != 10) {
                throw BIException("Invalid transaction date.");
            }
        }
    }
};

// ============================================================
// 6. ETL AND STAR SCHEMA ENGINE
// ============================================================

class DataWarehouse {

private:
    vector<FactSale> factSales;

public:

    void load(const SourceRepository& source) {

        unordered_map<int, Customer> customerLookup;
        unordered_map<int, Product> productLookup;

        for (const auto& customer : source.getCustomers()) {
            customerLookup.emplace(customer.id, customer);
        }

        for (const auto& product : source.getProducts()) {
            productLookup.emplace(product.id, product);
        }

        vector<FactSale> staging;

        for (const auto& transaction : source.getTransactions()) {

            const auto customer = customerLookup.find(
                transaction.customerId
            );

            const auto product = productLookup.find(
                transaction.productId
            );

            if (customer == customerLookup.end() ||
                product == productLookup.end()) {
                throw BIException("Dimension lookup failed.");
            }

            double revenue =
                transaction.quantity * transaction.unitPrice;

            double cost =
                transaction.quantity * product->second.unitCost;

            staging.push_back({
                transaction.id,
                transaction.customerId,
                transaction.productId,
                customer->second.name,
                product->second.name,
                customer->second.region,
                product->second.category,
                transaction.date,
                transaction.quantity,
                revenue,
                cost,
                revenue - cost
            });
        }

        // Replace the warehouse dataset only after successful staging.
        factSales.swap(staging);
    }

    const vector<FactSale>& getFactSales() const {
        return factSales;
    }

    size_t size() const {
        return factSales.size();
    }
};

// ============================================================
// 7. ANALYTICAL ENGINE
// ============================================================

class AnalyticsEngine {

public:

    static double totalRevenue(const vector<FactSale>& records) {

        double total = 0;

        for (const auto& record : records) {
            total += record.revenue;
        }

        return total;
    }

    static double totalCost(const vector<FactSale>& records) {

        double total = 0;

        for (const auto& record : records) {
            total += record.cost;
        }

        return total;
    }

    static double totalProfit(const vector<FactSale>& records) {

        return totalRevenue(records) - totalCost(records);
    }

    static double profitMargin(const vector<FactSale>& records) {

        double revenue = totalRevenue(records);

        if (revenue == 0) {
            return 0;
        }

        return totalProfit(records) / revenue * 100;
    }

    static double averageOrderValue(
        const vector<FactSale>& records
    ) {

        if (records.empty()) {
            return 0;
        }

        return totalRevenue(records) / records.size();
    }

    static int distinctCustomers(
        const vector<FactSale>& records
    ) {

        set<int> customerIds;

        for (const auto& record : records) {
            customerIds.insert(record.customerId);
        }

        return static_cast<int>(customerIds.size());
    }

    static map<string, double> groupRevenue(
        const vector<FactSale>& records,
        const string& dimension
    ) {

        map<string, double> result;

        for (const auto& record : records) {

            if (dimension == "region") {
                result[record.region] += record.revenue;
            }
            else if (dimension == "product") {
                result[record.productName] += record.revenue;
            }
            else if (dimension == "category") {
                result[record.category] += record.revenue;
            }
            else {
                throw BIException("Unsupported analytical dimension.");
            }
        }

        return result;
    }
};

// ============================================================
// 8. INTERACTIVE FILTER ENGINE
// ============================================================

class QueryEngine {

public:

    static vector<FactSale> filterRegion(
        const vector<FactSale>& records,
        const string& region
    ) {

        vector<FactSale> result;

        copy_if(
            records.begin(),
            records.end(),
            back_inserter(result),
            [&](const FactSale& record) {
                return record.region == region;
            }
        );

        return result;
    }

    static vector<FactSale> filterRevenueAbove(
        const vector<FactSale>& records,
        double threshold
    ) {

        if (threshold < 0) {
            throw BIException("Revenue threshold cannot be negative.");
        }

        vector<FactSale> result;

        copy_if(
            records.begin(),
            records.end(),
            back_inserter(result),
            [&](const FactSale& record) {
                return record.revenue > threshold;
            }
        );

        return result;
    }
};

// ============================================================
// 9. REPORT MANAGEMENT
// ============================================================

class ReportManager {

private:
    map<int, Report> reports;

public:

    void addReport(const Report& report) {

        if (report.id <= 0 || report.name.empty()) {
            throw BIException("Invalid report definition.");
        }

        if (reports.count(report.id)) {
            throw BIException("Report identifier already exists.");
        }

        reports.emplace(report.id, report);
    }

    void requestReview(int id) {

        auto it = reports.find(id);

        if (it == reports.end()) {
            throw BIException("Report does not exist.");
        }

        if (it->second.status != PublicationStatus::DRAFT) {
            throw BIException("Only draft reports can enter review.");
        }

        it->second.status = PublicationStatus::REVIEW;
    }

    void approve(int id) {

        auto it = reports.find(id);

        if (it == reports.end()) {
            throw BIException("Report does not exist.");
        }

        if (it->second.status != PublicationStatus::REVIEW) {
            throw BIException("Report is not under review.");
        }

        it->second.status = PublicationStatus::APPROVED;
    }

    void publish(int id) {

        auto it = reports.find(id);

        if (it == reports.end()) {
            throw BIException("Report does not exist.");
        }

        if (it->second.status != PublicationStatus::APPROVED) {
            throw BIException("Publication requires approval.");
        }

        it->second.status = PublicationStatus::PUBLISHED;
    }

    const Report& getReport(int id) const {

        auto it = reports.find(id);

        if (it == reports.end()) {
            throw BIException("Report not found.");
        }

        return it->second;
    }
};

// ============================================================
// 10. ROLE-BASED ACCESS CONTROL
// ============================================================

class AccessControl {

public:

    static bool hasPermission(
        const User& user,
        Permission required
    ) {

        if (user.permissions.count(Permission::ADMIN)) {
            return true;
        }

        return user.permissions.count(required) > 0;
    }

    static void authorize(
        const User& user,
        Permission required
    ) {

        if (!hasPermission(user, required)) {
            throw BIException(
                "Access denied for user: " + user.username
            );
        }
    }
};

// ============================================================
// 11. REFRESH MANAGEMENT
// ============================================================

class RefreshManager {

private:
    RefreshStatus status = RefreshStatus::NOT_STARTED;
    string errorMessage;

public:

    void execute(DataWarehouse& warehouse,
                 const SourceRepository& source) {

        if (status == RefreshStatus::RUNNING) {
            throw BIException("Refresh already in progress.");
        }

        status = RefreshStatus::RUNNING;
        errorMessage.clear();

        try {

            DataValidator::validate(source);
            warehouse.load(source);

            status = RefreshStatus::SUCCEEDED;

        } catch (const exception& error) {

            status = RefreshStatus::FAILED;
            errorMessage = error.what();

            throw;
        }
    }

    RefreshStatus getStatus() const {
        return status;
    }

    const string& getError() const {
        return errorMessage;
    }
};

// ============================================================
// 12. DASHBOARD ENGINE
// ============================================================

class DashboardEngine {

public:

    static vector<KPI> generate(
        const vector<FactSale>& records
    ) {

        return {
            {
                "Total Revenue",
                AnalyticsEngine::totalRevenue(records),
                "INR"
            },
            {
                "Total Profit",
                AnalyticsEngine::totalProfit(records),
                "INR"
            },
            {
                "Profit Margin",
                AnalyticsEngine::profitMargin(records),
                "%"
            },
            {
                "Average Order Value",
                AnalyticsEngine::averageOrderValue(records),
                "INR"
            },
            {
                "Unique Customers",
                static_cast<double>(
                    AnalyticsEngine::distinctCustomers(records)
                ),
                "count"
            }
        };
    }

    static void display(const vector<KPI>& kpis) {

        cout << "\nEXECUTIVE DASHBOARD\n";
        cout << string(65, '=') << '\n';

        for (const auto& kpi : kpis) {

            cout << left << setw(25) << kpi.name
                 << right << setw(18) << fixed
                 << setprecision(2) << kpi.value
                 << " " << kpi.unit << '\n';
        }

        cout << string(65, '=') << '\n';
    }
};

// ============================================================
// 13. MAIN APPLICATION
// ============================================================

int main() {

    try {

        cout << "\nPOWER BI INTRODUCTION\n";
        cout << "Enterprise Business Intelligence Engine\n";

        SourceRepository source;
        DataWarehouse warehouse;
        RefreshManager refresh;

        // Validate and load data.
        refresh.execute(warehouse, source);

        cout << "\nREFRESH STATUS: "
             << toString(refresh.getStatus()) << '\n';

        cout << "FACT TABLE RECORDS: "
             << warehouse.size() << '\n';

        const auto& records = warehouse.getFactSales();

        // Calculate KPIs.
        auto kpis = DashboardEngine::generate(records);

        DashboardEngine::display(kpis);

        // Regional aggregation.
        cout << "\nREVENUE BY REGION\n";

        auto regional = AnalyticsEngine::groupRevenue(
            records,
            "region"
        );

        for (const auto& [region, revenue] : regional) {

            cout << left << setw(20) << region
                 << right << fixed << setprecision(2)
                 << revenue << '\n';
        }

        // Product aggregation.
        cout << "\nREVENUE BY PRODUCT\n";

        auto products = AnalyticsEngine::groupRevenue(
            records,
            "product"
        );

        for (const auto& [product, revenue] : products) {

            cout << left << setw(20) << product
                 << right << fixed << setprecision(2)
                 << revenue << '\n';
        }

        // Filter context.
        auto northRecords = QueryEngine::filterRegion(
            records,
            "North"
        );

        cout << "\nNORTH REGION ANALYSIS\n";
        cout << "Transactions: " << northRecords.size() << '\n';
        cout << "Revenue: "
             << AnalyticsEngine::totalRevenue(northRecords)
             << '\n';

        // Role-based publication.
        User analyst{
            "data_analyst",
            {Permission::VIEW, Permission::BUILD}
        };

        User administrator{
            "bi_administrator",
            {Permission::ADMIN}
        };

        AccessControl::authorize(
            analyst,
            Permission::BUILD
        );

        AccessControl::authorize(
            administrator,
            Permission::PUBLISH
        );

        // Report lifecycle.
        ReportManager manager;

        manager.addReport({
            1,
            "Executive Sales Report",
            "data_analyst",
            "Regional sales and profitability",
            PublicationStatus::DRAFT,
            {
                {
                    "Revenue by Region",
                    VisualType::BAR_CHART,
                    "region",
                    "revenue"
                },
                {
                    "Profit KPI",
                    VisualType::KPI_CARD,
                    "",
                    "profit"
                }
            }
        });

        manager.requestReview(1);
        manager.approve(1);
        manager.publish(1);

        cout << "\nREPORT PUBLICATION STATUS: "
             << toString(manager.getReport(1).status)
             << '\n';

        // Edge case validation.
        vector<FactSale> emptyRecords;

        if (AnalyticsEngine::profitMargin(emptyRecords) != 0) {
            throw BIException("Empty-data calculation failed.");
        }

        if (warehouse.size() != source.getTransactions().size()) {
            throw BIException("Data reconciliation failed.");
        }

        auto highValue = QueryEngine::filterRevenueAbove(
            records,
            50000
        );

        cout << "\nHIGH VALUE TRANSACTIONS: "
             << highValue.size() << '\n';

        cout << "\nALL GOVERNANCE AND DATA VALIDATIONS PASSED.\n";

    } catch (const exception& error) {

        cerr << "\nAPPLICATION ERROR: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
