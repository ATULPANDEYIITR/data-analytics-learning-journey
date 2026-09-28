/*
 * SQL Joins II - C++17 Technical Case Study
 *
 * Scenario:
 *   An order-management analytics system must combine customers, orders,
 *   order items, payments, employees, managers, and projects.
 *
 * The case study demonstrates:
 *   - self joins
 *   - cross joins
 *   - multiple joins
 *   - one-to-one and one-to-many cardinality
 *   - many-to-many relationships
 *   - duplicate explosion
 *   - pre-aggregation
 *   - semi-joins
 *   - anti-joins
 *   - hash joins
 *   - nested-loop joins
 *   - validation
 *   - complexity reasoning
 *   - production-oriented safeguards
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic joins_ii.cpp -o joins_ii
 */

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

// ============================================================================
// 1. GENERIC HELPERS
// ============================================================================

void printTitle(const string& title) {
    cout << "\n" << string(88, '=') << "\n";
    cout << title << "\n";
    cout << string(88, '=') << "\n";
}

template <typename T>
void require(bool condition, const T& message) {
    if (!condition) {
        throw runtime_error(message);
    }
}

// ============================================================================
// 2. DOMAIN MODELS
// ============================================================================

struct Employee {
    int employeeId;
    string employeeName;
    optional<int> managerId;
    int departmentId;
};

struct Department {
    int departmentId;
    string departmentName;
};

struct Project {
    int projectId;
    string projectName;
    int departmentId;
};

struct EmployeeProject {
    int employeeId;
    int projectId;
};

struct Customer {
    int customerId;
    string customerName;
};

struct Order {
    int orderId;
    int customerId;
    double orderTotal;
};

struct OrderItem {
    int orderItemId;
    int orderId;
    string product;
    int quantity;
};

struct Payment {
    int paymentId;
    int orderId;
    string paymentMethod;
    double amount;
};

// ============================================================================
// 3. DATASET
// ============================================================================

class DataSet {
public:
    vector<Employee> employees{
        {1, "Asha", 4, 10},
        {2, "Bharat", 4, 10},
        {3, "Chitra", 5, 20},
        {4, "Dev", 6, 10},
        {5, "Esha", 6, 20},
        {6, "Farhan", nullopt, 30},
        {7, "Gita", 4, 10}
    };

    vector<Department> departments{
        {10, "Engineering"},
        {20, "Research"},
        {30, "Security"}
    };

    vector<Project> projects{
        {101, "Atlas", 10},
        {102, "Beacon", 10},
        {103, "Cipher", 20},
        {104, "Dragon", 30}
    };

    vector<EmployeeProject> employeeProjects{
        {1, 101},
        {1, 102},
        {2, 101},
        {3, 103},
        {4, 101},
        {4, 102},
        {4, 104},
        {5, 103},
        {6, 104},
        {7, 102}
    };

    vector<Customer> customers{
        {1, "Acme"},
        {2, "Globex"},
        {3, "Initech"}
    };

    vector<Order> orders{
        {1001, 1, 500.0},
        {1002, 1, 300.0},
        {1003, 2, 900.0},
        {1004, 3, 200.0}
    };

    vector<OrderItem> orderItems{
        {1, 1001, "Keyboard", 2},
        {2, 1001, "Mouse", 1},
        {3, 1002, "Monitor", 2},
        {4, 1003, "Laptop", 1},
        {5, 1003, "Mouse", 4},
        {6, 1004, "Keyboard", 1}
    };

    vector<Payment> payments{
        {1, 1001, "Card", 500.0},
        {2, 1002, "Card", 300.0},
        {3, 1003, "UPI", 500.0},
        {4, 1003, "Card", 400.0},
        {5, 1004, "UPI", 200.0}
    };
};

// ============================================================================
// 4. SELF JOIN: EMPLOYEE -> MANAGER
// ============================================================================

struct EmployeeManagerRow {
    string employeeName;
    string managerName;
};

vector<EmployeeManagerRow> buildEmployeeManagerView(
    const vector<Employee>& employees
) {
    /*
     * A self join uses one table twice under two aliases.
     *
     * Conceptual SQL:
     *
     *   SELECT e.employee_name, m.employee_name
     *   FROM employees e
     *   LEFT JOIN employees m
     *     ON e.manager_id = m.employee_id;
     *
     * The unordered_map represents an index on employee_id.
     */
    unordered_map<int, const Employee*> employeeById;

    for (const auto& employee : employees) {
        employeeById[employee.employeeId] = &employee;
    }

    vector<EmployeeManagerRow> result;

    for (const auto& employee : employees) {
        if (!employee.managerId.has_value()) {
            result.push_back({employee.employeeName, "(no manager)"});
            continue;
        }

        auto iterator = employeeById.find(*employee.managerId);

        if (iterator == employeeById.end()) {
            result.push_back({employee.employeeName, "(invalid manager)"});
        } else {
            result.push_back({
                employee.employeeName,
                iterator->second->employeeName
            });
        }
    }

    return result;
}

void printEmployeeManagerView(
    const vector<EmployeeManagerRow>& rows
) {
    cout << left
         << setw(15) << "Employee"
         << setw(20) << "Manager"
         << "\n";

    cout << string(35, '-') << "\n";

    for (const auto& row : rows) {
        cout << left
             << setw(15) << row.employeeName
             << setw(20) << row.managerName
             << "\n";
    }
}

// ============================================================================
// 5. SELF JOIN: SAME-DEPARTMENT PAIRS
// ============================================================================

struct EmployeePair {
    string first;
    string second;
    int departmentId;
};

vector<EmployeePair> findSameDepartmentPairs(
    const vector<Employee>& employees
) {
    /*
     * The strict index ordering i < j prevents:
     *   A,A
     *   A,B and B,A
     *
     * This is equivalent to using:
     *
     *   e1.employee_id < e2.employee_id
     *
     * in SQL.
     */
    vector<EmployeePair> result;

    for (size_t i = 0; i < employees.size(); ++i) {
        for (size_t j = i + 1; j < employees.size(); ++j) {
            if (employees[i].departmentId == employees[j].departmentId) {
                result.push_back({
                    employees[i].employeeName,
                    employees[j].employeeName,
                    employees[i].departmentId
                });
            }
        }
    }

    return result;
}

// ============================================================================
// 6. CROSS JOIN
// ============================================================================

struct RegionQuarter {
    string region;
    string quarter;
};

vector<RegionQuarter> crossJoin(
    const vector<string>& regions,
    const vector<string>& quarters
) {
    /*
     * Cartesian product:
     *
     *   output = |regions| * |quarters|
     *
     * No matching condition exists.
     */
    vector<RegionQuarter> result;

    for (const auto& region : regions) {
        for (const auto& quarter : quarters) {
            result.push_back({region, quarter});
        }
    }

    return result;
}

// ============================================================================
// 7. JOIN CARDINALITY
// ============================================================================

template <typename LeftRow, typename RightRow, typename LeftKey,
          typename RightKey>
size_t exactJoinCardinality(
    const vector<LeftRow>& left,
    const vector<RightRow>& right,
    LeftKey leftKey,
    RightKey rightKey
) {
    /*
     * For every key k:
     *
     *     output(k) = count_left(k) * count_right(k)
     *
     * This is the central rule behind duplicate explosion.
     */
    unordered_map<long long, size_t> leftCounts;
    unordered_map<long long, size_t> rightCounts;

    for (const auto& row : left) {
        leftCounts[leftKey(row)]++;
    }

    for (const auto& row : right) {
        rightCounts[rightKey(row)]++;
    }

    size_t total = 0;

    for (const auto& [key, leftCount] : leftCounts) {
        auto iterator = rightCounts.find(key);

        if (iterator != rightCounts.end()) {
            total += leftCount * iterator->second;
        }
    }

    return total;
}

// ============================================================================
// 8. ORDER-ITEM JOIN
// ============================================================================

struct OrderItemRow {
    int orderId;
    int customerId;
    string product;
    int quantity;
};

vector<OrderItemRow> joinOrdersToItems(
    const vector<Order>& orders,
    const vector<OrderItem>& items
) {
    unordered_map<int, vector<const OrderItem*>> itemsByOrder;

    for (const auto& item : items) {
        itemsByOrder[item.orderId].push_back(&item);
    }

    vector<OrderItemRow> result;

    for (const auto& order : orders) {
        auto iterator = itemsByOrder.find(order.orderId);

        if (iterator == itemsByOrder.end()) {
            continue;
        }

        for (const auto* item : iterator->second) {
            result.push_back({
                order.orderId,
                order.customerId,
                item->product,
                item->quantity
            });
        }
    }

    return result;
}

// ============================================================================
// 9. ORDER-ITEM-PAYMENT EXPLOSION
// ============================================================================

struct ExplodedOrderRow {
    int orderId;
    string product;
    int quantity;
    string paymentMethod;
    double paymentAmount;
};

vector<ExplodedOrderRow> joinItemsToPayments(
    const vector<OrderItemRow>& itemRows,
    const vector<Payment>& payments
) {
    /*
     * This is deliberately the dangerous pattern.
     *
     * If an order has:
     *     3 item rows
     *     4 payment rows
     *
     * the output contains:
     *     3 * 4 = 12 rows
     *
     * The function is logically correct but may be analytically incorrect
     * when item and payment facts are later summed together.
     */
    unordered_map<int, vector<const Payment*>> paymentsByOrder;

    for (const auto& payment : payments) {
        paymentsByOrder[payment.orderId].push_back(&payment);
    }

    vector<ExplodedOrderRow> result;

    for (const auto& item : itemRows) {
        auto iterator = paymentsByOrder.find(item.orderId);

        if (iterator == paymentsByOrder.end()) {
            continue;
        }

        for (const auto* payment : iterator->second) {
            result.push_back({
                item.orderId,
                item.product,
                item.quantity,
                payment->paymentMethod,
                payment->amount
            });
        }
    }

    return result;
}

// ============================================================================
// 10. PRE-AGGREGATED ORDER METRICS
// ============================================================================

struct OrderMetrics {
    int orderId;
    int itemCount;
    int totalQuantity;
    int paymentCount;
    double totalPaid;
};

vector<OrderMetrics> buildSafeOrderMetrics(
    const vector<Order>& orders,
    const vector<OrderItem>& items,
    const vector<Payment>& payments
) {
    /*
     * Safe strategy:
     *
     *   order_items -> one row per order
     *   payments    -> one row per order
     *
     * Then combine the two already-aggregated relations.
     *
     * This preserves order grain and prevents independent child rows from
     * multiplying one another.
     */
    unordered_map<int, int> itemCount;
    unordered_map<int, int> quantitySum;

    for (const auto& item : items) {
        itemCount[item.orderId]++;
        quantitySum[item.orderId] += item.quantity;
    }

    unordered_map<int, int> paymentCount;
    unordered_map<int, double> paymentSum;

    for (const auto& payment : payments) {
        paymentCount[payment.orderId]++;
        paymentSum[payment.orderId] += payment.amount;
    }

    vector<OrderMetrics> result;

    for (const auto& order : orders) {
        result.push_back({
            order.orderId,
            itemCount[order.orderId],
            quantitySum[order.orderId],
            paymentCount[order.orderId],
            paymentSum[order.orderId]
        });
    }

    return result;
}

void printOrderMetrics(const vector<OrderMetrics>& rows) {
    cout << left
         << setw(10) << "Order"
         << setw(12) << "Items"
         << setw(16) << "Quantity"
         << setw(14) << "Payments"
         << setw(14) << "Paid"
         << "\n";

    cout << string(66, '-') << "\n";

    cout << fixed << setprecision(2);

    for (const auto& row : rows) {
        cout << left
             << setw(10) << row.orderId
             << setw(12) << row.itemCount
             << setw(16) << row.totalQuantity
             << setw(14) << row.paymentCount
             << setw(14) << row.totalPaid
             << "\n";
    }
}

// ============================================================================
// 11. SEMI-JOIN
// ============================================================================

vector<Employee> employeesWithProjects(
    const vector<Employee>& employees,
    const vector<EmployeeProject>& links
) {
    /*
     * Semi-join semantics:
     *
     *   return the left row if at least one matching right row exists.
     *
     * Unlike an ordinary join, multiple matching links do not multiply the
     * employee row.
     */
    unordered_set<int> employeeIdsWithProjects;

    for (const auto& link : links) {
        employeeIdsWithProjects.insert(link.employeeId);
    }

    vector<Employee> result;

    for (const auto& employee : employees) {
        if (employeeIdsWithProjects.contains(employee.employeeId)) {
            result.push_back(employee);
        }
    }

    return result;
}

// ============================================================================
// 12. ANTI-JOIN
// ============================================================================

vector<Employee> employeesWithoutProjects(
    const vector<Employee>& employees,
    const vector<EmployeeProject>& links
) {
    unordered_set<int> employeeIdsWithProjects;

    for (const auto& link : links) {
        employeeIdsWithProjects.insert(link.employeeId);
    }

    vector<Employee> result;

    for (const auto& employee : employees) {
        if (!employeeIdsWithProjects.contains(employee.employeeId)) {
            result.push_back(employee);
        }
    }

    return result;
}

// ============================================================================
// 13. MANY-TO-MANY VALIDATION
// ============================================================================

string pairKey(int employeeId, int projectId) {
    return to_string(employeeId) + ":" + to_string(projectId);
}

vector<string> duplicateBridgeRelationships(
    const vector<EmployeeProject>& links
) {
    unordered_map<string, int> counts;

    for (const auto& link : links) {
        counts[pairKey(link.employeeId, link.projectId)]++;
    }

    vector<string> duplicates;

    for (const auto& [key, count] : counts) {
        if (count > 1) {
            duplicates.push_back(
                key + " appears " + to_string(count) + " times"
            );
        }
    }

    sort(duplicates.begin(), duplicates.end());

    return duplicates;
}

// ============================================================================
// 14. REFERENTIAL-INTEGRITY VALIDATION
// ============================================================================

vector<string> validateEmployeeProjectReferences(
    const DataSet& data
) {
    unordered_set<int> employeeIds;
    unordered_set<int> projectIds;

    for (const auto& employee : data.employees) {
        employeeIds.insert(employee.employeeId);
    }

    for (const auto& project : data.projects) {
        projectIds.insert(project.projectId);
    }

    vector<string> errors;

    for (const auto& link : data.employeeProjects) {
        if (!employeeIds.contains(link.employeeId)) {
            errors.push_back(
                "Invalid employee reference: " +
                to_string(link.employeeId)
            );
        }

        if (!projectIds.contains(link.projectId)) {
            errors.push_back(
                "Invalid project reference: " +
                to_string(link.projectId)
            );
        }
    }

    return errors;
}

// ============================================================================
// 15. NESTED-LOOP JOIN FOR PERFORMANCE COMPARISON
// ============================================================================

struct KeyValue {
    int key;
    int value;
};

vector<pair<int, int>> nestedLoopEqualityJoin(
    const vector<KeyValue>& left,
    const vector<KeyValue>& right
) {
    vector<pair<int, int>> result;

    for (const auto& leftRow : left) {
        for (const auto& rightRow : right) {
            if (leftRow.key == rightRow.key) {
                result.push_back({
                    leftRow.value,
                    rightRow.value
                });
            }
        }
    }

    return result;
}

// ============================================================================
// 16. HASH JOIN FOR PERFORMANCE COMPARISON
// ============================================================================

vector<pair<int, int>> hashEqualityJoin(
    const vector<KeyValue>& left,
    const vector<KeyValue>& right
) {
    /*
     * Build an index on the right side.
     *
     * Expected average behavior:
     *     build = O(M)
     *     probe = O(N)
     *     output = proportional to result size
     *
     * Total is commonly described as approximately O(N + M + K),
     * where K is the number of produced rows.
     */
    unordered_map<int, vector<int>> index;

    for (const auto& row : right) {
        index[row.key].push_back(row.value);
    }

    vector<pair<int, int>> result;

    for (const auto& row : left) {
        auto iterator = index.find(row.key);

        if (iterator == index.end()) {
            continue;
        }

        for (int rightValue : iterator->second) {
            result.push_back({
                row.value,
                rightValue
            });
        }
    }

    return result;
}

// ============================================================================
// 17. CUSTOMER REPORT
// ============================================================================

struct CustomerMetrics {
    int customerId;
    string customerName;
    int orderCount;
    double totalOrderValue;
};

vector<CustomerMetrics> buildCustomerReport(
    const vector<Customer>& customers,
    const vector<Order>& orders
) {
    unordered_map<int, int> orderCount;
    unordered_map<int, double> orderValue;

    for (const auto& order : orders) {
        orderCount[order.customerId]++;
        orderValue[order.customerId] += order.orderTotal;
    }

    vector<CustomerMetrics> result;

    for (const auto& customer : customers) {
        result.push_back({
            customer.customerId,
            customer.customerName,
            orderCount[customer.customerId],
            orderValue[customer.customerId]
        });
    }

    return result;
}

void printCustomerReport(const vector<CustomerMetrics>& rows) {
    cout << left
         << setw(12) << "Customer ID"
         << setw(16) << "Customer"
         << setw(12) << "Orders"
         << setw(18) << "Order Value"
         << "\n";

    cout << string(58, '-') << "\n";

    cout << fixed << setprecision(2);

    for (const auto& row : rows) {
        cout << left
             << setw(12) << row.customerId
             << setw(16) << row.customerName
             << setw(12) << row.orderCount
             << setw(18) << row.totalOrderValue
             << "\n";
    }
}

// ============================================================================
// 18. SQL DESIGN PRINCIPLES
// ============================================================================

void printDesignPrinciples() {
    printTitle("SQL JOIN DESIGN PRINCIPLES");

    cout
        << "1. Define row grain before joining.\n"
        << "2. Identify unique keys and duplicate foreign-key values.\n"
        << "3. Use aliases for self joins.\n"
        << "4. Treat CROSS JOIN as intentionally multiplicative.\n"
        << "5. Remember that m matching rows multiplied by n matching rows can\n"
        << "   produce m*n output rows for one join key.\n"
        << "6. Model many-to-many relationships with a bridge table.\n"
        << "7. Aggregate independent one-to-many facts before combining them\n"
        << "   when the required output grain is the parent entity.\n"
        << "8. Do not rely on DISTINCT to repair an incorrect relationship.\n"
        << "9. Check NULL behavior explicitly.\n"
        << "10. Validate intermediate row counts.\n"
        << "11. Inspect execution plans for production workloads.\n"
        << "12. Consider data skew and output size, not just input size.\n";
}

// ============================================================================
// 19. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        DataSet data;

        // --------------------------------------------------------------------
        // A. Self join: employee to manager
        // --------------------------------------------------------------------

        printTitle("1. SELF JOIN: EMPLOYEE -> MANAGER");

        const auto managerView =
            buildEmployeeManagerView(data.employees);

        printEmployeeManagerView(managerView);

        // --------------------------------------------------------------------
        // B. Same-department employee pairs
        // --------------------------------------------------------------------

        printTitle("2. SELF JOIN: SAME-DEPARTMENT PAIRS");

        const auto pairs =
            findSameDepartmentPairs(data.employees);

        for (const auto& pair : pairs) {
            cout << pair.first
                 << " <-> "
                 << pair.second
                 << " (department "
                 << pair.departmentId
                 << ")\n";
        }

        // --------------------------------------------------------------------
        // C. Cross join
        // --------------------------------------------------------------------

        printTitle("3. CROSS JOIN");

        const vector<string> regions{
            "North",
            "South"
        };

        const vector<string> quarters{
            "Q1",
            "Q2",
            "Q3",
            "Q4"
        };

        const auto planningGrid =
            crossJoin(regions, quarters);

        for (const auto& row : planningGrid) {
            cout << row.region
                 << " / "
                 << row.quarter
                 << "\n";
        }

        cout << "\nExpected combinations: "
             << regions.size() * quarters.size()
             << "\n";

        require(
            planningGrid.size() ==
                regions.size() * quarters.size(),
            "CROSS JOIN cardinality violation"
        );

        // --------------------------------------------------------------------
        // D. Basic one-to-many cardinality
        // --------------------------------------------------------------------

        printTitle("4. ONE-TO-MANY CARDINALITY");

        const size_t employeeDepartmentCardinality =
            exactJoinCardinality(
                data.employees,
                data.departments,
                [](const Employee& e) {
                    return static_cast<long long>(e.departmentId);
                },
                [](const Department& d) {
                    return static_cast<long long>(d.departmentId);
                }
            );

        cout << "Employees: "
             << data.employees.size()
             << "\n";

        cout << "Departments: "
             << data.departments.size()
             << "\n";

        cout << "Employee-department matching rows: "
             << employeeDepartmentCardinality
             << "\n";

        require(
            employeeDepartmentCardinality == data.employees.size(),
            "Expected one department match per employee"
        );

        // --------------------------------------------------------------------
        // E. Orders to items
        // --------------------------------------------------------------------

        printTitle("5. ORDERS -> ORDER ITEMS");

        const auto orderItemRows =
            joinOrdersToItems(
                data.orders,
                data.orderItems
            );

        cout << "Orders: "
             << data.orders.size()
             << "\n";

        cout << "Order-item rows: "
             << orderItemRows.size()
             << "\n";

        // --------------------------------------------------------------------
        // F. Deliberate duplicate explosion
        // --------------------------------------------------------------------

        printTitle("6. DELIBERATE DUPLICATE EXPLOSION");

        /*
         * Order 1003 has:
         *   2 items
         *   2 payments
         *
         * Therefore the order-level combination contributes:
         *   2 * 2 = 4 rows.
         */
        const auto exploded =
            joinItemsToPayments(
                orderItemRows,
                data.payments
            );

        const size_t order1003ItemCount = count_if(
            orderItemRows.begin(),
            orderItemRows.end(),
            [](const OrderItemRow& row) {
                return row.orderId == 1003;
            }
        );

        const size_t order1003PaymentCount = count_if(
            data.payments.begin(),
            data.payments.end(),
            [](const Payment& payment) {
                return payment.orderId == 1003;
            }
        );

        const size_t order1003ExplodedCount = count_if(
            exploded.begin(),
            exploded.end(),
            [](const ExplodedOrderRow& row) {
                return row.orderId == 1003;
            }
        );

        cout << "Order 1003 item rows: "
             << order1003ItemCount
             << "\n";

        cout << "Order 1003 payment rows: "
             << order1003PaymentCount
             << "\n";

        cout << "Expected combinations: "
             << order1003ItemCount * order1003PaymentCount
             << "\n";

        cout << "Actual combinations: "
             << order1003ExplodedCount
             << "\n";

        require(
            order1003ExplodedCount ==
                order1003ItemCount * order1003PaymentCount,
            "Duplicate explosion cardinality mismatch"
        );

        // --------------------------------------------------------------------
        // G. Demonstrate incorrect aggregate
        // --------------------------------------------------------------------

        printTitle("7. INCORRECT AGGREGATION AFTER EXPLOSION");

        int naiveQuantity = 0;
        double naivePayment = 0.0;

        for (const auto& row : exploded) {
            if (row.orderId == 1003) {
                naiveQuantity += row.quantity;
                naivePayment += row.paymentAmount;
            }
        }

        int actualQuantity = 0;
        double actualPayment = 0.0;

        for (const auto& row : data.orderItems) {
            if (row.orderId == 1003) {
                actualQuantity += row.quantity;
            }
        }

        for (const auto& payment : data.payments) {
            if (payment.orderId == 1003) {
                actualPayment += payment.amount;
            }
        }

        cout << fixed << setprecision(2);

        cout << "Actual quantity: "
             << actualQuantity
             << "\n";

        cout << "Naive exploded quantity: "
             << naiveQuantity
             << "\n";

        cout << "Actual payment: "
             << actualPayment
             << "\n";

        cout << "Naive exploded payment: "
             << naivePayment
             << "\n";

        // --------------------------------------------------------------------
        // H. Safe pre-aggregation
        // --------------------------------------------------------------------

        printTitle("8. SAFE PRE-AGGREGATION");

        const auto safeMetrics =
            buildSafeOrderMetrics(
                data.orders,
                data.orderItems,
                data.payments
            );

        printOrderMetrics(safeMetrics);

        const auto order1003Metric = find_if(
            safeMetrics.begin(),
            safeMetrics.end(),
            [](const OrderMetrics& row) {
                return row.orderId == 1003;
            }
        );

        require(
            order1003Metric != safeMetrics.end(),
            "Order 1003 missing from safe metrics"
        );

        require(
            order1003Metric->totalQuantity == actualQuantity,
            "Safe quantity aggregation mismatch"
        );

        require(
            fabs(
                order1003Metric->totalPaid - actualPayment
            ) < 1e-9,
            "Safe payment aggregation mismatch"
        );

        // --------------------------------------------------------------------
        // I. Semi-join
        // --------------------------------------------------------------------

        printTitle("9. SEMI-JOIN");

        const auto activeEmployees =
            employeesWithProjects(
                data.employees,
                data.employeeProjects
            );

        for (const auto& employee : activeEmployees) {
            cout << employee.employeeId
                 << ": "
                 << employee.employeeName
                 << "\n";
        }

        cout
            << "\nThe employee appears once even if the employee has many "
            << "projects.\n";

        // --------------------------------------------------------------------
        // J. Anti-join
        // --------------------------------------------------------------------

        printTitle("10. ANTI-JOIN");

        const auto employeesWithoutProject =
            employeesWithoutProjects(
                data.employees,
                data.employeeProjects
            );

        for (const auto& employee : employeesWithoutProject) {
            cout << employee.employeeId
                 << ": "
                 << employee.employeeName
                 << "\n";
        }

        // --------------------------------------------------------------------
        // K. Bridge-table validation
        // --------------------------------------------------------------------

        printTitle("11. MANY-TO-MANY BRIDGE VALIDATION");

        vector<EmployeeProject> duplicateLinks =
            data.employeeProjects;

        duplicateLinks.push_back({1, 101});

        const auto duplicates =
            duplicateBridgeRelationships(
                duplicateLinks
            );

        if (duplicates.empty()) {
            cout << "No duplicate bridge relationships.\n";
        } else {
            for (const auto& duplicate : duplicates) {
                cout << duplicate << "\n";
            }
        }

        // --------------------------------------------------------------------
        // L. Referential integrity
        // --------------------------------------------------------------------

        printTitle("12. REFERENTIAL INTEGRITY");

        const auto referenceErrors =
            validateEmployeeProjectReferences(data);

        if (referenceErrors.empty()) {
            cout << "All employee-project references are valid.\n";
        } else {
            for (const auto& error : referenceErrors) {
                cout << error << "\n";
            }
        }

        // --------------------------------------------------------------------
        // M. Nested loop vs hash join
        // --------------------------------------------------------------------

        printTitle("13. NESTED LOOP VS HASH JOIN");

        vector<KeyValue> benchmarkLeft;
        vector<KeyValue> benchmarkRight;

        for (int i = 0; i < 1000; ++i) {
            benchmarkLeft.push_back({i, i * 10});
            benchmarkRight.push_back({i, i * 20});
        }

        const auto nestedStart =
            chrono::high_resolution_clock::now();

        const auto nestedResult =
            nestedLoopEqualityJoin(
                benchmarkLeft,
                benchmarkRight
            );

        const auto nestedEnd =
            chrono::high_resolution_clock::now();

        const auto hashStart =
            chrono::high_resolution_clock::now();

        const auto hashResult =
            hashEqualityJoin(
                benchmarkLeft,
                benchmarkRight
            );

        const auto hashEnd =
            chrono::high_resolution_clock::now();

        const double nestedMilliseconds =
            chrono::duration<double, milli>(
                nestedEnd - nestedStart
            ).count();

        const double hashMilliseconds =
            chrono::duration<double, milli>(
                hashEnd - hashStart
            ).count();

        cout << "Nested-loop result rows: "
             << nestedResult.size()
             << "\n";

        cout << "Hash-join result rows: "
             << hashResult.size()
             << "\n";

        cout << fixed << setprecision(3);

        cout << "Nested-loop time: "
             << nestedMilliseconds
             << " ms\n";

        cout << "Hash-join time: "
             << hashMilliseconds
             << " ms\n";

        require(
            nestedResult.size() == hashResult.size(),
            "Join algorithms produced different cardinalities"
        );

        // --------------------------------------------------------------------
        // N. Large duplicate group
        // --------------------------------------------------------------------

        printTitle("14. OUTPUT SIZE FROM DUPLICATE KEYS");

        vector<KeyValue> hotLeft;
        vector<KeyValue> hotRight;

        for (int i = 0; i < 100; ++i) {
            hotLeft.push_back({1, i});
            hotRight.push_back({1, i});
        }

        const auto hotResult =
            hashEqualityJoin(
                hotLeft,
                hotRight
            );

        cout << "Left rows: "
             << hotLeft.size()
             << "\n";

        cout << "Right rows: "
             << hotRight.size()
             << "\n";

        cout << "Output rows: "
             << hotResult.size()
             << "\n";

        require(
            hotResult.size() == 10000,
            "Expected 10000 rows from 100 x 100 duplicate keys"
        );

        // --------------------------------------------------------------------
        // O. Customer reporting
        // --------------------------------------------------------------------

        printTitle("15. CUSTOMER REPORT");

        const auto customerMetrics =
            buildCustomerReport(
                data.customers,
                data.orders
            );

        printCustomerReport(customerMetrics);

        // --------------------------------------------------------------------
        // P. Design principles
        // --------------------------------------------------------------------

        printDesignPrinciples();

        // --------------------------------------------------------------------
        // Q. Production safeguards
        // --------------------------------------------------------------------

        printTitle("16. PRODUCTION SAFEGUARDS");

        cout
            << "- Define table grain before joining.\n"
            << "- Confirm primary-key uniqueness.\n"
            << "- Profile foreign-key multiplicity.\n"
            << "- Check NULL behavior.\n"
            << "- Estimate join output before executing large queries.\n"
            << "- Treat CROSS JOIN as intentionally multiplicative.\n"
            << "- Use table aliases in self joins.\n"
            << "- Use bridge tables for many-to-many relationships.\n"
            << "- Pre-aggregate independent child facts when required.\n"
            << "- Do not use DISTINCT as a generic repair mechanism.\n"
            << "- Check intermediate row counts.\n"
            << "- Consider indexes and execution plans.\n"
            << "- Consider skewed keys and memory consumption.\n"
            << "- Test empty tables and missing foreign-key matches.\n";

        // --------------------------------------------------------------------
        // R. Final correctness checks
        // --------------------------------------------------------------------

        printTitle("17. FINAL VALIDATION");

        require(
            data.departments.size() == 3,
            "Unexpected department count"
        );

        require(
            planningGrid.size() == 8,
            "Unexpected cross-join cardinality"
        );

        require(
            managerView.size() == data.employees.size(),
            "Self-join LEFT-style view should preserve employees"
        );

        require(
            order1003ItemCount * order1003PaymentCount ==
                order1003ExplodedCount,
            "Order 1003 multiplicity rule failed"
        );

        require(
            safeMetrics.size() == data.orders.size(),
            "Safe metrics must remain at order grain"
        );

        cout << "All case-study validation checks passed.\n";
        cout << "SQL Joins II case study completed successfully.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "ERROR: " << error.what() << "\n";
        return 1;
    }
}
