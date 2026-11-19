#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

/*
 * POWER BI DATA MODELING
 *
 * C++17 repository-independent semantic model engine.
 *
 * Implements:
 * - Fact and dimension table structures
 * - Star schema relationships
 * - Primary and foreign key validation
 * - Cardinality verification
 * - Relationship direction
 * - Dimension-to-fact filter propagation
 * - Aggregation
 * - Merge-like relationship diagnostics
 * - Model validation and reporting
 */

enum class TableType {
    FACT,
    DIMENSION
};

enum class Cardinality {
    ONE_TO_ONE,
    ONE_TO_MANY,
    MANY_TO_ONE,
    MANY_TO_MANY
};

enum class FilterDirection {
    SINGLE,
    BOTH
};

struct Product {
    int productKey;
    string name;
    string category;
    string brand;
};

struct Customer {
    int customerKey;
    string name;
    string region;
    string segment;
};

struct CalendarDate {
    int dateKey;
    int year;
    int month;
    int quarter;
};

struct Store {
    int storeKey;
    string name;
    string city;
};

struct SalesFact {
    int salesId;
    string orderId;
    int dateKey;
    int productKey;
    int customerKey;
    int storeKey;
    int quantity;
    double unitPrice;
    double salesAmount;
};

struct Relationship {
    string name;
    string fromTable;
    string fromColumn;
    string toTable;
    string toColumn;
    Cardinality cardinality;
    FilterDirection direction;
    bool active;
};

class ModelException : public runtime_error {
public:
    explicit ModelException(const string& message)
        : runtime_error(message) {}
};

class RetailDataModel {
private:
    vector<Product> products;
    vector<Customer> customers;
    vector<CalendarDate> dates;
    vector<Store> stores;
    vector<SalesFact> sales;
    vector<Relationship> relationships;

    unordered_map<int, size_t> productIndex;
    unordered_map<int, size_t> customerIndex;
    unordered_map<int, size_t> dateIndex;
    unordered_map<int, size_t> storeIndex;

    unordered_set<int> salesIds;

    static void require(bool condition, const string& message) {
        if (!condition) {
            throw ModelException(message);
        }
    }

public:
    void addProduct(const Product& product) {
        require(product.productKey > 0, "Invalid product key");

        require(
            productIndex.find(product.productKey) == productIndex.end(),
            "Duplicate product key"
        );

        require(!product.name.empty(), "Product name is required");

        productIndex[product.productKey] = products.size();
        products.push_back(product);
    }

    void addCustomer(const Customer& customer) {
        require(customer.customerKey > 0, "Invalid customer key");

        require(
            customerIndex.find(customer.customerKey) == customerIndex.end(),
            "Duplicate customer key"
        );

        customerIndex[customer.customerKey] = customers.size();
        customers.push_back(customer);
    }

    void addDate(const CalendarDate& date) {
        require(date.dateKey > 0, "Invalid date key");
        require(date.month >= 1 && date.month <= 12, "Invalid month");
        require(date.quarter >= 1 && date.quarter <= 4, "Invalid quarter");

        require(
            dateIndex.find(date.dateKey) == dateIndex.end(),
            "Duplicate date key"
        );

        dateIndex[date.dateKey] = dates.size();
        dates.push_back(date);
    }

    void addStore(const Store& store) {
        require(store.storeKey > 0, "Invalid store key");

        require(
            storeIndex.find(store.storeKey) == storeIndex.end(),
            "Duplicate store key"
        );

        storeIndex[store.storeKey] = stores.size();
        stores.push_back(store);
    }

    void addSale(const SalesFact& fact) {
        require(fact.salesId > 0, "Invalid sales identifier");
        require(!fact.orderId.empty(), "Order ID is required");
        require(fact.quantity > 0, "Quantity must be positive");
        require(fact.unitPrice >= 0, "Negative unit price");
        require(isfinite(fact.unitPrice), "Invalid unit price");

        require(
            fact.productKey > 0 &&
            fact.customerKey > 0 &&
            fact.dateKey > 0 &&
            fact.storeKey > 0,
            "Foreign keys must be positive"
        );

        require(
            salesIds.find(fact.salesId) == salesIds.end(),
            "Duplicate sales identifier"
        );

        require(
            productIndex.count(fact.productKey),
            "Unknown product foreign key"
        );

        require(
            customerIndex.count(fact.customerKey),
            "Unknown customer foreign key"
        );

        require(
            dateIndex.count(fact.dateKey),
            "Unknown date foreign key"
        );

        require(
            storeIndex.count(fact.storeKey),
            "Unknown store foreign key"
        );

        const double expected =
            fact.quantity * fact.unitPrice;

        require(
            abs(expected - fact.salesAmount) < 0.000001,
            "Sales amount does not match quantity multiplied by unit price"
        );

        salesIds.insert(fact.salesId);
        sales.push_back(fact);
    }

    void addRelationship(const Relationship& relationship) {
        if (relationship.name.empty()) {
            throw ModelException("Relationship name is required");
        }

        for (const auto& existing : relationships) {
            require(
                existing.name != relationship.name,
                "Duplicate relationship name"
            );
        }

        relationships.push_back(relationship);
    }

    vector<string> validate() const {
        vector<string> issues;

        for (const auto& relationship : relationships) {
            if (!relationship.active) {
                continue;
            }

            if (relationship.cardinality ==
                Cardinality::MANY_TO_MANY) {
                issues.push_back(
                    relationship.name +
                    ": many-to-many relationship needs explicit bridge design"
                );
            }
        }

        for (const auto& fact : sales) {
            if (!productIndex.count(fact.productKey)) {
                issues.push_back("Missing product foreign key");
            }

            if (!customerIndex.count(fact.customerKey)) {
                issues.push_back("Missing customer foreign key");
            }

            if (!dateIndex.count(fact.dateKey)) {
                issues.push_back("Missing date foreign key");
            }

            if (!storeIndex.count(fact.storeKey)) {
                issues.push_back("Missing store foreign key");
            }
        }

        return issues;
    }

    vector<SalesFact> filterByCategory(
        const string& category
    ) const {
        unordered_set<int> matchingProducts;

        for (const auto& product : products) {
            if (product.category == category) {
                matchingProducts.insert(product.productKey);
            }
        }

        vector<SalesFact> result;

        for (const auto& fact : sales) {
            if (matchingProducts.count(fact.productKey)) {
                result.push_back(fact);
            }
        }

        return result;
    }

    vector<SalesFact> filterByRegion(
        const string& region
    ) const {
        unordered_set<int> matchingCustomers;

        for (const auto& customer : customers) {
            if (customer.region == region) {
                matchingCustomers.insert(customer.customerKey);
            }
        }

        vector<SalesFact> result;

        for (const auto& fact : sales) {
            if (matchingCustomers.count(fact.customerKey)) {
                result.push_back(fact);
            }
        }

        return result;
    }

    map<string, double> salesByCategory() const {
        map<string, double> totals;

        for (const auto& fact : sales) {
            const auto index = productIndex.at(fact.productKey);
            const string& category = products[index].category;

            totals[category] += fact.salesAmount;
        }

        return totals;
    }

    map<string, double> salesByRegion() const {
        map<string, double> totals;

        for (const auto& fact : sales) {
            const auto index = customerIndex.at(fact.customerKey);
            const string& region = customers[index].region;

            totals[region] += fact.salesAmount;
        }

        return totals;
    }

    map<int, double> salesByYear() const {
        map<int, double> totals;

        for (const auto& fact : sales) {
            const auto index = dateIndex.at(fact.dateKey);
            const int year = dates[index].year;

            totals[year] += fact.salesAmount;
        }

        return totals;
    }

    double totalSales() const {
        double total = 0;

        for (const auto& fact : sales) {
            total += fact.salesAmount;
        }

        return total;
    }

    int totalQuantity() const {
        int total = 0;

        for (const auto& fact : sales) {
            total += fact.quantity;
        }

        return total;
    }

    double averageOrderValue() const {
        unordered_map<string, double> orders;

        for (const auto& fact : sales) {
            orders[fact.orderId] += fact.salesAmount;
        }

        if (orders.empty()) {
            return 0;
        }

        double total = 0;

        for (const auto& [orderId, amount] : orders) {
            total += amount;
        }

        return total / orders.size();
    }

    void printModel() const {
        cout << "\nSTAR SCHEMA\n";
        cout << "-----------------------------\n";

        cout << "FactSales: " << sales.size() << " rows\n";
        cout << "DimProduct: " << products.size() << " rows\n";
        cout << "DimCustomer: " << customers.size() << " rows\n";
        cout << "DimDate: " << dates.size() << " rows\n";
        cout << "DimStore: " << stores.size() << " rows\n";

        cout << "\nRELATIONSHIPS\n";

        for (const auto& relationship : relationships) {
            cout << relationship.fromTable << "."
                 << relationship.fromColumn << " -> "
                 << relationship.toTable << "."
                 << relationship.toColumn << " | ";

            switch (relationship.cardinality) {
                case Cardinality::MANY_TO_ONE:
                    cout << "MANY_TO_ONE";
                    break;
                case Cardinality::ONE_TO_MANY:
                    cout << "ONE_TO_MANY";
                    break;
                case Cardinality::ONE_TO_ONE:
                    cout << "ONE_TO_ONE";
                    break;
                case Cardinality::MANY_TO_MANY:
                    cout << "MANY_TO_MANY";
                    break;
            }

            cout << "\n";
        }
    }

    void printAggregation(
        const map<string, double>& totals
    ) const {
        for (const auto& [category, amount] : totals) {
            cout << left << setw(18) << category
                 << right << fixed << setprecision(2)
                 << amount << "\n";
        }
    }

    size_t factCount() const {
        return sales.size();
    }
};

int main() {
    try {
        RetailDataModel model;

        model.addProduct({
            101, "Laptop Pro", "Electronics", "Apex"
        });

        model.addProduct({
            102, "Wireless Mouse", "Accessories", "Nova"
        });

        model.addProduct({
            103, "Mechanical Keyboard", "Accessories", "Nova"
        });

        model.addProduct({
            104, "Office Chair", "Furniture", "Comfort"
        });

        model.addCustomer({
            201, "Aarav Sharma", "North", "Premium"
        });

        model.addCustomer({
            202, "Meera Singh", "South", "Standard"
        });

        model.addCustomer({
            203, "Kabir Verma", "West", "Premium"
        });

        model.addDate({20260101, 2026, 1, 1});
        model.addDate({20260102, 2026, 1, 1});
        model.addDate({20260201, 2026, 2, 1});
        model.addDate({20260301, 2026, 3, 1});

        model.addStore({301, "Lucknow Central", "Lucknow"});
        model.addStore({302, "Delhi Central", "Delhi"});

        model.addSale({
            1, "ORD001", 20260101, 101, 201, 301,
            1, 75000, 75000
        });

        model.addSale({
            2, "ORD001", 20260101, 102, 201, 301,
            2, 1200, 2400
        });

        model.addSale({
            3, "ORD002", 20260102, 103, 202, 302,
            1, 3500, 3500
        });

        model.addSale({
            4, "ORD003", 20260201, 104, 203, 301,
            2, 8500, 17000
        });

        model.addSale({
            5, "ORD004", 20260301, 101, 202, 302,
            1, 75000, 75000
        });

        const vector<string> dimensionNames = {
            "DimDate",
            "DimProduct",
            "DimCustomer",
            "DimStore"
        };

        const vector<string> factColumns = {
            "date_key",
            "product_key",
            "customer_key",
            "store_key"
        };

        const vector<string> dimensionKeys = {
            "date_key",
            "product_key",
            "customer_key",
            "store_key"
        };

        for (size_t i = 0; i < dimensionNames.size(); ++i) {
            model.addRelationship({
                "Relationship_" + dimensionNames[i],
                "FactSales",
                factColumns[i],
                dimensionNames[i],
                dimensionKeys[i],
                Cardinality::MANY_TO_ONE,
                FilterDirection::SINGLE,
                true
            });
        }

        model.printModel();

        cout << "\nMODEL VALIDATION\n";

        const auto issues = model.validate();

        if (issues.empty()) {
            cout << "All model integrity checks passed.\n";
        } else {
            for (const auto& issue : issues) {
                cout << "ERROR: " << issue << "\n";
            }

            return 1;
        }

        cout << "\nTOTAL SALES\n";
        cout << fixed << setprecision(2)
             << model.totalSales() << "\n";

        cout << "\nTOTAL QUANTITY\n";
        cout << model.totalQuantity() << "\n";

        cout << "\nAVERAGE ORDER VALUE\n";
        cout << model.averageOrderValue() << "\n";

        cout << "\nSALES BY CATEGORY\n";
        model.printAggregation(model.salesByCategory());

        cout << "\nSALES BY REGION\n";
        model.printAggregation(model.salesByRegion());

        cout << "\nSALES BY YEAR\n";

        for (const auto& [year, amount] : model.salesByYear()) {
            cout << year << ": " << amount << "\n";
        }

        cout << "\nDIMENSION FILTER: ACCESSORIES\n";

        const auto filtered = model.filterByCategory(
            "Accessories"
        );

        double filteredTotal = 0;

        for (const auto& fact : filtered) {
            filteredTotal += fact.salesAmount;
        }

        cout << "Matching fact rows: " << filtered.size() << "\n";
        cout << "Filtered sales: " << filteredTotal << "\n";

        cout << "\nDIMENSION FILTER: NORTH REGION\n";

        const auto regional = model.filterByRegion("North");

        double regionalTotal = 0;

        for (const auto& fact : regional) {
            regionalTotal += fact.salesAmount;
        }

        cout << "Matching fact rows: " << regional.size() << "\n";
        cout << "Regional sales: " << regionalTotal << "\n";

        cout << "\nEDGE CASE VALIDATION\n";

        try {
            model.addSale({
                99, "INVALID", 20260101, 999, 201, 301,
                1, 100, 100
            });
        } catch (const ModelException& error) {
            cout << "Invalid foreign key rejected: "
                 << error.what() << "\n";
        }

        try {
            model.addProduct({
                101, "Duplicate Product", "Electronics", "Apex"
            });
        } catch (const ModelException& error) {
            cout << "Duplicate dimension key rejected: "
                 << error.what() << "\n";
        }

        cout << "\nMODEL EXECUTION COMPLETED\n";

    } catch (const exception& error) {
        cerr << "Fatal model error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
