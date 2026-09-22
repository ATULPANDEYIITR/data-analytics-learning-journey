/*
 * SQL SELECT Case Study in C++17
 *
 * Scenario:
 * A technology company needs an in-memory analytical reporting engine for
 * employee, department, project, customer, and order data.
 *
 * The program models several concepts that are central to SQL SELECT:
 * - projection
 * - filtering
 * - sorting
 * - joins
 * - grouping
 * - aggregation
 * - CASE-style classification
 * - NULL-like optional values
 * - subquery-style analysis
 * - ranking
 * - parameter validation
 * - performance considerations
 *
 * C++ is used to demonstrate how relational operations can be represented
 * explicitly through strongly typed structures, algorithms, and functions.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic sql_select_case_study.cpp -o sql_select
 *
 * Run:
 *   ./sql_select
 */

#include <algorithm>
#include <cassert>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

struct Department {
    int departmentId;
    string departmentName;
    string location;
};

struct Employee {
    int employeeId;
    string employeeName;
    optional<int> departmentId;
    optional<int> managerId;
    double salary;
    string status;
    optional<double> commission;
};

struct Project {
    int projectId;
    string projectName;
    int departmentId;
    double budget;
};

struct Customer {
    int customerId;
    string customerName;
    optional<string> city;
};

struct Order {
    int orderId;
    int customerId;
    double amount;
    string status;
};

struct EmployeeDepartmentRow {
    Employee employee;
    optional<Department> department;
};

struct DepartmentSummary {
    int departmentId;
    string departmentName;
    size_t employeeCount;
    double averageSalary;
    double highestSalary;
};

struct CustomerRevenue {
    string customerName;
    double revenue;
    string segment;
};

void printTitle(const string& title) {
    cout << "\n" << string(90, '=') << "\n";
    cout << title << "\n";
    cout << string(90, '=') << "\n";
}

vector<Employee> createEmployees() {
    return {
        {101, "Asha", 1, nullopt, 125000, "active", 12000},
        {102, "Ravi", 1, 101, 95000, "active", nullopt},
        {103, "Meera", 2, nullopt, 140000, "active", 18000},
        {104, "Karan", 2, 103, 90000, "active", 5000},
        {105, "Neha", 3, nullopt, 110000, "active", nullopt},
        {106, "Vikram", 3, 105, 72000, "active", 3000},
        {107, "Isha", 4, nullopt, 85000, "active", nullopt},
        {108, "Arjun", nullopt, nullopt, 65000, "inactive", nullopt},
        {109, "Priya", 5, nullopt, 150000, "active", 25000},
        {110, "Dev", 5, 109, 98000, "active", nullopt}
    };
}

vector<Department> createDepartments() {
    return {
        {1, "Engineering", "Bengaluru"},
        {2, "Security", "Hyderabad"},
        {3, "Finance", "Mumbai"},
        {4, "Human Resources", "Delhi"},
        {5, "Research", "Pune"}
    };
}

vector<Project> createProjects() {
    return {
        {201, "Payments Platform", 1, 850000},
        {202, "Threat Detection", 2, 1200000},
        {203, "Audit Automation", 3, 350000},
        {204, "Quantum Research", 5, 2000000},
        {205, "Recruitment Portal", 4, 180000}
    };
}

vector<Customer> createCustomers() {
    return {
        {1, "Alpha Corp", "Delhi"},
        {2, "Beta Systems", "Mumbai"},
        {3, "Gamma Labs", "Pune"},
        {4, "Delta Security", "Bengaluru"},
        {5, "Epsilon LLC", nullopt}
    };
}

vector<Order> createOrders() {
    return {
        {1001, 1, 25000, "paid"},
        {1002, 1, 45000, "paid"},
        {1003, 2, 15000, "pending"},
        {1004, 2, 75000, "paid"},
        {1005, 3, 32000, "cancelled"},
        {1006, 3, 82000, "paid"},
        {1007, 4, 125000, "paid"},
        {1008, 5, 56000, "paid"}
    };
}

vector<Employee> selectHighEarners(
    const vector<Employee>& employees,
    double minimumSalary
) {
    vector<Employee> result;

    for (const auto& employee : employees) {
        if (employee.salary >= minimumSalary) {
            result.push_back(employee);
        }
    }

    return result;
}

void printEmployeeRows(const vector<Employee>& employees) {
    cout << left
         << setw(12) << "ID"
         << setw(16) << "Name"
         << setw(14) << "Salary"
         << setw(14) << "Department"
         << "Status\n";

    for (const auto& employee : employees) {
        cout << left
             << setw(12) << employee.employeeId
             << setw(16) << employee.employeeName
             << setw(14) << fixed << setprecision(2) << employee.salary;

        if (employee.departmentId.has_value()) {
            cout << setw(14) << *employee.departmentId;
        } else {
            cout << setw(14) << "NULL";
        }

        cout << employee.status << "\n";
    }
}

optional<Department> findDepartment(
    const vector<Department>& departments,
    int departmentId
) {
    for (const auto& department : departments) {
        if (department.departmentId == departmentId) {
            return department;
        }
    }

    return nullopt;
}

vector<EmployeeDepartmentRow> leftJoinEmployeesDepartments(
    const vector<Employee>& employees,
    const vector<Department>& departments
) {
    vector<EmployeeDepartmentRow> result;

    for (const auto& employee : employees) {
        if (!employee.departmentId.has_value()) {
            result.push_back({employee, nullopt});
            continue;
        }

        auto department = findDepartment(
            departments,
            *employee.departmentId
        );

        result.push_back({employee, department});
    }

    return result;
}

void printEmployeeDepartmentJoin(
    const vector<EmployeeDepartmentRow>& rows
) {
    cout << left
         << setw(16) << "Employee"
         << setw(22) << "Department"
         << "Location\n";

    for (const auto& row : rows) {
        cout << left
             << setw(16) << row.employee.employeeName;

        if (row.department.has_value()) {
            cout << setw(22) << row.department->departmentName
                 << row.department->location;
        } else {
            cout << setw(22) << "NULL"
                 << "NULL";
        }

        cout << "\n";
    }
}

vector<DepartmentSummary> groupEmployeesByDepartment(
    const vector<Employee>& employees,
    const vector<Department>& departments
) {
    struct Accumulator {
        size_t count = 0;
        double totalSalary = 0.0;
        double highestSalary = 0.0;
    };

    unordered_map<int, Accumulator> aggregates;

    for (const auto& employee : employees) {
        if (!employee.departmentId.has_value()) {
            continue;
        }

        auto& accumulator = aggregates[*employee.departmentId];
        accumulator.count++;
        accumulator.totalSalary += employee.salary;
        accumulator.highestSalary =
            max(accumulator.highestSalary, employee.salary);
    }

    vector<DepartmentSummary> result;

    for (const auto& department : departments) {
        auto iterator = aggregates.find(department.departmentId);

        if (iterator == aggregates.end()) {
            result.push_back({
                department.departmentId,
                department.departmentName,
                0,
                0.0,
                0.0
            });
            continue;
        }

        const auto& accumulator = iterator->second;

        result.push_back({
            department.departmentId,
            department.departmentName,
            accumulator.count,
            accumulator.totalSalary /
                static_cast<double>(accumulator.count),
            accumulator.highestSalary
        });
    }

    sort(
        result.begin(),
        result.end(),
        [](const DepartmentSummary& left,
           const DepartmentSummary& right) {
            return left.averageSalary > right.averageSalary;
        }
    );

    return result;
}

void printDepartmentSummaries(
    const vector<DepartmentSummary>& summaries
) {
    cout << left
         << setw(22) << "Department"
         << setw(14) << "Employees"
         << setw(18) << "Average Salary"
         << "Highest Salary\n";

    for (const auto& summary : summaries) {
        cout << left
             << setw(22) << summary.departmentName
             << setw(14) << summary.employeeCount
             << setw(18) << fixed << setprecision(2)
             << summary.averageSalary
             << summary.highestSalary << "\n";
    }
}

double averageSalary(const vector<Employee>& employees) {
    if (employees.empty()) {
        return 0.0;
    }

    const double total = accumulate(
        employees.begin(),
        employees.end(),
        0.0,
        [](double total, const Employee& employee) {
            return total + employee.salary;
        }
    );

    return total / static_cast<double>(employees.size());
}

vector<Employee> aboveCompanyAverage(
    const vector<Employee>& employees
) {
    const double average = averageSalary(employees);

    vector<Employee> result;

    copy_if(
        employees.begin(),
        employees.end(),
        back_inserter(result),
        [average](const Employee& employee) {
            return employee.salary > average;
        }
    );

    sort(
        result.begin(),
        result.end(),
        [](const Employee& left, const Employee& right) {
            return left.salary > right.salary;
        }
    );

    return result;
}

vector<Employee> rankEmployeesBySalary(
    vector<Employee> employees
) {
    sort(
        employees.begin(),
        employees.end(),
        [](const Employee& left, const Employee& right) {
            if (left.salary != right.salary) {
                return left.salary > right.salary;
            }

            return left.employeeName < right.employeeName;
        }
    );

    return employees;
}

string salaryBand(double salary) {
    if (salary >= 130000) {
        return "Executive Range";
    }

    if (salary >= 100000) {
        return "Senior Range";
    }

    if (salary >= 80000) {
        return "Professional Range";
    }

    return "Entry Range";
}

vector<CustomerRevenue> createCustomerRevenueReport(
    const vector<Customer>& customers,
    const vector<Order>& orders
) {
    vector<CustomerRevenue> report;

    for (const auto& customer : customers) {
        double revenue = 0.0;

        for (const auto& order : orders) {
            if (order.customerId == customer.customerId &&
                order.status == "paid") {
                revenue += order.amount;
            }
        }

        string segment;

        if (revenue >= 100000) {
            segment = "Enterprise";
        } else if (revenue >= 50000) {
            segment = "Growth";
        } else if (revenue > 0) {
            segment = "Standard";
        } else {
            segment = "No Paid Revenue";
        }

        report.push_back({
            customer.customerName,
            revenue,
            segment
        });
    }

    sort(
        report.begin(),
        report.end(),
        [](const CustomerRevenue& left,
           const CustomerRevenue& right) {
            return left.revenue > right.revenue;
        }
    );

    return report;
}

void printCustomerRevenue(
    const vector<CustomerRevenue>& report
) {
    cout << left
         << setw(22) << "Customer"
         << setw(18) << "Revenue"
         << "Segment\n";

    for (const auto& row : report) {
        cout << left
             << setw(22) << row.customerName
             << setw(18) << fixed << setprecision(2)
             << row.revenue
             << row.segment << "\n";
    }
}

void validateMinimumSalary(double minimumSalary) {
    if (!isfinite(minimumSalary) || minimumSalary < 0) {
        throw invalid_argument(
            "Minimum salary must be a non-negative finite number."
        );
    }
}

void demonstrateFiltering(
    const vector<Employee>& employees
) {
    printTitle("1. SELECT + WHERE");

    const double minimumSalary = 100000;
    validateMinimumSalary(minimumSalary);

    auto result = selectHighEarners(
        employees,
        minimumSalary
    );

    printEmployeeRows(result);
}

void demonstrateSorting(
    const vector<Employee>& employees
) {
    printTitle("2. ORDER BY");

    auto result = employees;

    sort(
        result.begin(),
        result.end(),
        [](const Employee& left,
           const Employee& right) {
            if (left.salary != right.salary) {
                return left.salary > right.salary;
            }

            return left.employeeName < right.employeeName;
        }
    );

    printEmployeeRows(result);
}

void demonstratePagination(
    const vector<Employee>& employees
) {
    printTitle("3. LIMIT AND OFFSET");

    auto sorted = rankEmployeesBySalary(employees);

    const size_t offset = 3;
    const size_t limit = 3;

    const size_t start = min(offset, sorted.size());
    const size_t end = min(start + limit, sorted.size());

    vector<Employee> page(
        sorted.begin() + static_cast<ptrdiff_t>(start),
        sorted.begin() + static_cast<ptrdiff_t>(end)
    );

    cout << "Rows corresponding to LIMIT 3 OFFSET 3:\n";
    printEmployeeRows(page);
}

void demonstrateNullSemantics(
    const vector<Employee>& employees
) {
    printTitle("4. SQL NULL-LIKE OPTIONAL VALUES");

    cout << left
         << setw(16) << "Employee"
         << setw(18) << "Commission"
         << "Interpretation\n";

    for (const auto& employee : employees) {
        cout << left
             << setw(16) << employee.employeeName;

        if (employee.commission.has_value()) {
            cout << setw(18) << fixed << setprecision(2)
                 << *employee.commission
                 << "Value present\n";
        } else {
            cout << setw(18) << "NULL"
                 << "Unknown / absent\n";
        }
    }
}

void demonstrateJoin(
    const vector<Employee>& employees,
    const vector<Department>& departments
) {
    printTitle("5. LEFT JOIN");

    auto result = leftJoinEmployeesDepartments(
        employees,
        departments
    );

    printEmployeeDepartmentJoin(result);
}

void demonstrateGrouping(
    const vector<Employee>& employees,
    const vector<Department>& departments
) {
    printTitle("6. GROUP BY + AGGREGATES");

    auto summaries = groupEmployeesByDepartment(
        employees,
        departments
    );

    printDepartmentSummaries(summaries);
}

void demonstrateSubquery(
    const vector<Employee>& employees
) {
    printTitle("7. SUBQUERY-STYLE ANALYSIS");

    const double average = averageSalary(employees);

    cout << "Company average salary: "
         << fixed << setprecision(2)
         << average << "\n\n";

    auto result = aboveCompanyAverage(employees);

    printEmployeeRows(result);
}

void demonstrateCaseExpression(
    const vector<Employee>& employees
) {
    printTitle("8. CASE EXPRESSION");

    cout << left
         << setw(16) << "Employee"
         << setw(16) << "Salary"
         << "Salary Band\n";

    for (const auto& employee : employees) {
        cout << left
             << setw(16) << employee.employeeName
             << setw(16) << fixed << setprecision(2)
             << employee.salary
             << salaryBand(employee.salary)
             << "\n";
    }
}

void demonstrateCustomerReport(
    const vector<Customer>& customers,
    const vector<Order>& orders
) {
    printTitle("9. REALISTIC CUSTOMER REPORT");

    auto report = createCustomerRevenueReport(
        customers,
        orders
    );

    printCustomerRevenue(report);
}

void demonstrateWindowStyleRanking(
    const vector<Employee>& employees
) {
    printTitle("10. WINDOW-FUNCTION-STYLE RANKING");

    auto sorted = rankEmployeesBySalary(employees);

    cout << left
         << setw(16) << "Employee"
         << setw(16) << "Salary"
         << "Rank\n";

    int rank = 0;
    double previousSalary = -1.0;

    for (size_t index = 0; index < sorted.size(); ++index) {
        if (sorted[index].salary != previousSalary) {
            rank = static_cast<int>(index) + 1;
        }

        previousSalary = sorted[index].salary;

        cout << left
             << setw(16) << sorted[index].employeeName
             << setw(16) << fixed << setprecision(2)
             << sorted[index].salary
             << rank
             << "\n";
    }
}

void demonstratePerformance(
    const vector<Employee>& employees
) {
    printTitle("11. PERFORMANCE AND COMPLEXITY");

    const size_t repetitions = 100000;

    auto start = chrono::high_resolution_clock::now();

    size_t matchedRows = 0;

    for (size_t repetition = 0;
         repetition < repetitions;
         ++repetition) {
        for (const auto& employee : employees) {
            if (employee.salary >= 100000) {
                ++matchedRows;
            }
        }
    }

    auto end = chrono::high_resolution_clock::now();

    const auto elapsed =
        chrono::duration_cast<chrono::microseconds>(
            end - start
        ).count();

    cout << "Repeated scans: " << repetitions << "\n";
    cout << "Matched rows counted: " << matchedRows << "\n";
    cout << "Elapsed microseconds: " << elapsed << "\n";

    cout << R"(
A direct scan is O(n) for one filtering operation.

Sorting with a comparison-based algorithm is generally O(n log n).

A naive nested-loop join is O(n * m), where n and m are the input
relation sizes. Database systems can use indexes, hash joins, merge
joins, statistics, and cost-based optimization to improve real workloads.

This C++ experiment measures in-memory operations and is not a substitute
for measuring an actual database query.
)" << "\n";
}

void demonstrateValidation() {
    printTitle("12. VALIDATION AND FAILURE HANDLING");

    try {
        validateMinimumSalary(100000);
        cout << "Valid salary filter accepted.\n";

        validateMinimumSalary(-1);
    } catch (const invalid_argument& error) {
        cout << "Validation rejected input: "
             << error.what() << "\n";
    }
}

void demonstrateTests(
    const vector<Employee>& employees,
    const vector<Department>& departments
) {
    printTitle("13. QUERY-STYLE TESTS");

    assert(employees.size() == 10);
    assert(departments.size() == 5);

    const double average = averageSalary(employees);
    assert(average > 0.0);

    auto highEarners = selectHighEarners(
        employees,
        100000
    );

    assert(!highEarners.empty());

    auto joined = leftJoinEmployeesDepartments(
        employees,
        departments
    );

    assert(joined.size() == employees.size());

    const auto missingDepartmentEmployee =
        find_if(
            joined.begin(),
            joined.end(),
            [](const EmployeeDepartmentRow& row) {
                return row.employee.employeeId == 108;
            }
        );

    assert(missingDepartmentEmployee != joined.end());
    assert(!missingDepartmentEmployee->department.has_value());

    cout << "All C++ assertions passed.\n";
}

void explainDesign() {
    printTitle("14. DESIGN NOTES");

    cout << R"(
The case study separates concerns into:

1. Data structures
   Strongly typed structs represent relations and result records.

2. Selection
   Filtering functions represent WHERE predicates.

3. Projection
   Result structures and print functions represent SELECT lists.

4. Ordering
   std::sort represents ORDER BY.

5. Aggregation
   unordered_map accumulators represent GROUP BY plus aggregate functions.

6. Joins
   Explicit lookup and nested iteration demonstrate relational matching.

7. NULL handling
   std::optional represents values that may be absent.

8. Conditional logic
   salaryBand and customer segmentation represent CASE expressions.

9. Subquery reasoning
   averageSalary followed by filtering models a scalar subquery.

10. Ranking
    A sorted sequence with rank calculation models a window ranking operation.

11. Validation
    Invalid query parameters are rejected before processing.

12. Testing
    Assertions verify row counts, joins, and NULL-related behavior.

The program intentionally exposes the mechanics that a SQL database normally
handles internally. Real database engines can optimize these operations using
indexes, statistics, query planners, memory management, concurrency control,
and specialized join and aggregation algorithms.
)" << "\n";
}

int main() {
    try {
        const auto employees = createEmployees();
        const auto departments = createDepartments();
        const auto projects = createProjects();
        const auto customers = createCustomers();
        const auto orders = createOrders();

        // The project dataset is created because the scenario models a
        // broader enterprise schema, even though the central demonstrations
        // focus on SELECT over employees, departments, customers, and orders.
        (void)projects;

        demonstrateFiltering(employees);
        demonstrateSorting(employees);
        demonstratePagination(employees);
        demonstrateNullSemantics(employees);
        demonstrateJoin(employees, departments);
        demonstrateGrouping(employees, departments);
        demonstrateSubquery(employees);
        demonstrateCaseExpression(employees);
        demonstrateCustomerReport(customers, orders);
        demonstrateWindowStyleRanking(employees);
        demonstratePerformance(employees);
        demonstrateValidation();
        demonstrateTests(employees, departments);
        explainDesign();

        printTitle("CASE STUDY COMPLETE");

        cout << "The C++ program demonstrated how SQL SELECT concepts "
             << "translate into strongly typed relational operations.\n";
    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
