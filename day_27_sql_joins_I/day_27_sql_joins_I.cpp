/*
 * SQL JOINS I
 * ===========
 *
 * C++17 industry-style case study:
 *
 * Build a small in-memory relational reporting engine for an organization.
 *
 * The modeled system contains:
 *
 *   departments
 *   employees
 *   projects
 *   employee_projects
 *
 * The implementation demonstrates:
 *
 *   - join keys
 *   - INNER JOIN
 *   - LEFT JOIN
 *   - RIGHT JOIN
 *   - FULL OUTER JOIN
 *   - one-to-many relationships
 *   - many-to-many relationships
 *   - composite keys
 *   - duplicate keys
 *   - unmatched rows
 *   - NULL-like optional values
 *   - aggregation
 *   - validation
 *   - complexity and performance trade-offs
 *
 * Compile:
 *
 *   g++ -std=c++17 -O2 sql_joins_case_study.cpp -o sql_joins_case_study
 *
 * Run:
 *
 *   ./sql_joins_case_study
 */

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// 1. DATA MODELS
// ============================================================================

struct Department {
    int id;
    string name;
};

struct Employee {
    int id;
    string name;
    optional<int> departmentId;
    optional<int> managerId;
    int salary;
};

struct Project {
    int id;
    string name;
};

struct EmployeeProject {
    int employeeId;
    int projectId;
    string role;
};

struct Sales {
    string region;
    string product;
    int amount;
};

struct Target {
    string region;
    string product;
    int amount;
};


// ============================================================================
// 2. HASH SUPPORT FOR COMPOSITE KEYS
// ============================================================================

struct CompositeKey {
    string first;
    string second;

    bool operator==(const CompositeKey& other) const {
        return first == other.first && second == other.second;
    }
};

struct CompositeKeyHash {
    size_t operator()(const CompositeKey& key) const {
        const size_t firstHash = hash<string>{}(key.first);
        const size_t secondHash = hash<string>{}(key.second);

        // A simple hash combination suitable for this educational example.
        return firstHash ^ (secondHash << 1);
    }
};


// ============================================================================
// 3. OUTPUT UTILITIES
// ============================================================================

void printLine() {
    cout << string(82, '-') << '\n';
}

void printSection(const string& title) {
    cout << '\n';
    cout << string(82, '=') << '\n';
    cout << title << '\n';
    cout << string(82, '=') << '\n';
}


// ============================================================================
// 4. GENERIC INNER JOIN
// ============================================================================

/*
 * This template implements an equality INNER JOIN.
 *
 * L = left relation
 * R = right relation
 *
 * The caller supplies:
 *
 *   leftKey(row)  -> join key
 *   rightKey(row) -> join key
 *   combine(left, right) -> result row
 *
 * An unordered_map acts like a hash index.
 *
 * Average expected complexity:
 *
 *   O(|L| + |R| + |output|)
 *
 * compared with a naive nested-loop implementation:
 *
 *   O(|L| * |R|)
 *
 * The output term is essential because a one-to-many relationship can
 * legitimately produce many rows.
 */

template<
    typename Left,
    typename Right,
    typename Key,
    typename Result,
    typename LeftKey,
    typename RightKey,
    typename Combine
>
vector<Result> innerJoin(
    const vector<Left>& left,
    const vector<Right>& right,
    LeftKey leftKey,
    RightKey rightKey,
    Combine combine
) {
    unordered_multimap<Key, const Right*> index;

    for (const auto& rightRow : right) {
        index.emplace(rightKey(rightRow), &rightRow);
    }

    vector<Result> result;

    for (const auto& leftRow : left) {
        const Key key = leftKey(leftRow);

        const auto range = index.equal_range(key);

        for (auto iterator = range.first; iterator != range.second; ++iterator) {
            result.push_back(combine(leftRow, *iterator->second));
        }
    }

    return result;
}


// ============================================================================
// 5. GENERIC LEFT JOIN
// ============================================================================

template<
    typename Left,
    typename Right,
    typename Key,
    typename Result,
    typename LeftKey,
    typename RightKey,
    typename Combine
>
vector<Result> leftJoin(
    const vector<Left>& left,
    const vector<Right>& right,
    LeftKey leftKey,
    RightKey rightKey,
    Combine combine
) {
    unordered_multimap<Key, const Right*> index;

    for (const auto& rightRow : right) {
        index.emplace(rightKey(rightRow), &rightRow);
    }

    vector<Result> result;

    for (const auto& leftRow : left) {
        const Key key = leftKey(leftRow);
        const auto range = index.equal_range(key);

        if (range.first == range.second) {
            /*
             * std::nullopt represents the NULL-extended right side of
             * an SQL LEFT JOIN.
             */
            result.push_back(combine(leftRow, nullopt));
            continue;
        }

        for (auto iterator = range.first; iterator != range.second; ++iterator) {
            result.push_back(combine(leftRow, optional<Right>(*iterator->second)));
        }
    }

    return result;
}


// ============================================================================
// 6. RIGHT JOIN THROUGH REVERSED LEFT JOIN
// ============================================================================

/*
 * RIGHT JOIN is logically equivalent to reversing the tables and using
 * LEFT JOIN. This avoids maintaining two independent join algorithms.
 */

template<
    typename Left,
    typename Right,
    typename Key,
    typename Result,
    typename LeftKey,
    typename RightKey,
    typename Combine
>
vector<Result> rightJoin(
    const vector<Left>& left,
    const vector<Right>& right,
    LeftKey leftKey,
    RightKey rightKey,
    Combine combine
) {
    return leftJoin<Right, Left, Key, Result>(
        right,
        left,
        rightKey,
        leftKey,
        [&](const Right& rightRow, optional<Left> leftRow) {
            if (leftRow.has_value()) {
                return combine(leftRow.value(), optional<Right>(rightRow));
            }

            return combine(optional<Left>(), optional<Right>(rightRow));
        }
    );
}


// ============================================================================
// 7. FULL OUTER JOIN
// ============================================================================

template<
    typename Left,
    typename Right,
    typename Key,
    typename Result,
    typename LeftKey,
    typename RightKey,
    typename Combine
>
vector<Result> fullOuterJoin(
    const vector<Left>& left,
    const vector<Right>& right,
    LeftKey leftKey,
    RightKey rightKey,
    Combine combine
) {
    unordered_multimap<Key, pair<size_t, const Right*>> index;

    for (size_t i = 0; i < right.size(); ++i) {
        index.emplace(rightKey(right[i]), make_pair(i, &right[i]));
    }

    unordered_set<size_t> matchedRightRows;
    vector<Result> result;

    for (const auto& leftRow : left) {
        const Key key = leftKey(leftRow);
        const auto range = index.equal_range(key);

        if (range.first == range.second) {
            result.push_back(combine(leftRow, optional<Right>()));
            continue;
        }

        for (auto iterator = range.first; iterator != range.second; ++iterator) {
            matchedRightRows.insert(iterator->second.first);

            result.push_back(
                combine(
                    leftRow,
                    optional<Right>(*iterator->second.second)
                )
            );
        }
    }

    for (size_t i = 0; i < right.size(); ++i) {
        if (!matchedRightRows.contains(i)) {
            result.push_back(combine(optional<Left>(), right[i]));
        }
    }

    return result;
}


// ============================================================================
// 8. DATABASE DATASET
// ============================================================================

struct Database {
    vector<Department> departments;
    vector<Employee> employees;
    vector<Project> projects;
    vector<EmployeeProject> assignments;
    vector<Sales> sales;
    vector<Target> targets;
};

Database createDatabase() {
    Database database;

    database.departments = {
        {10, "Engineering"},
        {20, "Finance"},
        {30, "Human Resources"},
        {40, "Security"},
        {50, "Research"}
    };

    database.employees = {
        {1, "Asha", 10, nullopt, 95000},
        {2, "Ravi", 10, 1, 82000},
        {3, "Meera", 20, 1, 78000},
        {4, "Kabir", nullopt, 1, 70000},
        {5, "Isha", 30, 1, 68000},
        {6, "Arjun", 40, 1, 88000}
    };

    database.projects = {
        {101, "Cloud Migration"},
        {102, "Fraud Detection"},
        {103, "Security Audit"}
    };

    database.assignments = {
        {1, 101, "Architect"},
        {1, 103, "Lead"},
        {2, 101, "Developer"},
        {3, 102, "Analyst"},
        {6, 103, "Security Engineer"}
    };

    database.sales = {
        {"North", "Laptop", 100000},
        {"North", "Phone", 70000},
        {"South", "Laptop", 85000},
        {"West", "Tablet", 45000}
    };

    database.targets = {
        {"North", "Laptop", 90000},
        {"North", "Phone", 80000},
        {"South", "Laptop", 80000},
        {"East", "Tablet", 40000}
    };

    return database;
}


// ============================================================================
// 9. INNER JOIN CASE STUDY
// ============================================================================

void demonstrateInnerJoin(const Database& database) {
    printSection("1. INNER JOIN: EMPLOYEES WITH DEPARTMENTS");

    auto result = innerJoin<
        Employee,
        Department,
        int,
        string
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](const Employee& employee, const Department& department) {
            return employee.name + " -> " + department.name;
        }
    );

    for (const auto& row : result) {
        cout << row << '\n';
    }

    cout << "\nRows returned: " << result.size() << '\n';
}


// ============================================================================
// 10. LEFT JOIN CASE STUDY
// ============================================================================

struct EmployeeDepartmentRow {
    string employeeName;
    optional<string> departmentName;
};

void demonstrateLeftJoin(const Database& database) {
    printSection("2. LEFT JOIN: PRESERVE ALL EMPLOYEES");

    auto result = leftJoin<
        Employee,
        Department,
        int,
        EmployeeDepartmentRow
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](const Employee& employee, optional<Department> department) {
            EmployeeDepartmentRow row;
            row.employeeName = employee.name;

            if (department.has_value()) {
                row.departmentName = department->name;
            }

            return row;
        }
    );

    for (const auto& row : result) {
        cout << left << setw(12) << row.employeeName
             << " | ";

        if (row.departmentName.has_value()) {
            cout << *row.departmentName;
        } else {
            cout << "NULL";
        }

        cout << '\n';
    }
}


// ============================================================================
// 11. RIGHT JOIN CASE STUDY
// ============================================================================

struct DepartmentEmployeeRow {
    optional<string> employeeName;
    string departmentName;
};

void demonstrateRightJoin(const Database& database) {
    printSection("3. RIGHT JOIN: PRESERVE ALL DEPARTMENTS");

    auto result = rightJoin<
        Employee,
        Department,
        int,
        DepartmentEmployeeRow
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](optional<Employee> employee, optional<Department> department) {
            DepartmentEmployeeRow row;

            if (employee.has_value()) {
                row.employeeName = employee->name;
            }

            row.departmentName = department->name;
            return row;
        }
    );

    for (const auto& row : result) {
        cout << left << setw(20) << row.departmentName
             << " | ";

        if (row.employeeName.has_value()) {
            cout << *row.employeeName;
        } else {
            cout << "NULL";
        }

        cout << '\n';
    }
}


// ============================================================================
// 12. FULL OUTER JOIN CASE STUDY
// ============================================================================

void demonstrateFullOuterJoin(const Database& database) {
    printSection("4. FULL OUTER JOIN: BOTH SIDES PRESERVED");

    auto result = fullOuterJoin<
        Department,
        Employee,
        int,
        string
    >(
        database.departments,
        database.employees,
        [](const Department& department) {
            return department.id;
        },
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](optional<Department> department, optional<Employee> employee) {
            string departmentName =
                department.has_value() ? department->name : "NULL";

            string employeeName =
                employee.has_value() ? employee->name : "NULL";

            return departmentName + " | " + employeeName;
        }
    );

    for (const auto& row : result) {
        cout << row << '\n';
    }
}


// ============================================================================
// 13. MANY-TO-MANY CASE STUDY
// ============================================================================

struct AssignmentDetail {
    string employeeName;
    int projectId;
    string role;
};

void demonstrateManyToMany(const Database& database) {
    printSection("5. MANY-TO-MANY: EMPLOYEES AND PROJECTS");

    auto firstJoin = innerJoin<
        Employee,
        EmployeeProject,
        int,
        AssignmentDetail
    >(
        database.employees,
        database.assignments,
        [](const Employee& employee) {
            return employee.id;
        },
        [](const EmployeeProject& assignment) {
            return assignment.employeeId;
        },
        [](const Employee& employee, const EmployeeProject& assignment) {
            return AssignmentDetail{
                employee.name,
                assignment.projectId,
                assignment.role
            };
        }
    );

    struct CompleteAssignment {
        string employee;
        string project;
        string role;
    };

    auto secondJoin = innerJoin<
        AssignmentDetail,
        Project,
        int,
        CompleteAssignment
    >(
        firstJoin,
        database.projects,
        [](const AssignmentDetail& assignment) {
            return assignment.projectId;
        },
        [](const Project& project) {
            return project.id;
        },
        [](const AssignmentDetail& assignment, const Project& project) {
            return CompleteAssignment{
                assignment.employeeName,
                project.name,
                assignment.role
            };
        }
    );

    for (const auto& row : secondJoin) {
        cout << left << setw(12) << row.employee
             << " | " << setw(20) << row.project
             << " | " << row.role << '\n';
    }
}


// ============================================================================
// 14. COMPOSITE JOIN KEY CASE STUDY
// ============================================================================

void demonstrateCompositeJoin(const Database& database) {
    printSection("6. COMPOSITE JOIN KEY: REGION + PRODUCT");

    unordered_multimap<
        CompositeKey,
        const Target*,
        CompositeKeyHash
    > targetIndex;

    for (const auto& target : database.targets) {
        targetIndex.emplace(
            CompositeKey{target.region, target.product},
            &target
        );
    }

    for (const auto& sale : database.sales) {
        CompositeKey key{sale.region, sale.product};

        auto range = targetIndex.equal_range(key);

        if (range.first == range.second) {
            cout << sale.region << " | "
                 << sale.product << " | "
                 << sale.amount << " | target=NULL\n";
            continue;
        }

        for (auto iterator = range.first; iterator != range.second; ++iterator) {
            const Target& target = *iterator->second;

            cout << sale.region << " | "
                 << sale.product << " | "
                 << sale.amount << " | "
                 << target.amount << " | variance="
                 << sale.amount - target.amount << '\n';
        }
    }

    cout << "\nMatching only region would be incorrect because a region can "
            "contain multiple products.\n";
}


// ============================================================================
// 15. SELF JOIN CASE STUDY
// ============================================================================

void demonstrateSelfJoin(const Database& database) {
    printSection("7. SELF JOIN: EMPLOYEE-MANAGER HIERARCHY");

    unordered_map<int, const Employee*> employeeIndex;

    for (const auto& employee : database.employees) {
        employeeIndex[employee.id] = &employee;
    }

    for (const auto& employee : database.employees) {
        cout << left << setw(12) << employee.name << " | manager=";

        if (!employee.managerId.has_value()) {
            cout << "NULL";
        } else {
            auto iterator = employeeIndex.find(*employee.managerId);

            if (iterator != employeeIndex.end()) {
                cout << iterator->second->name;
            } else {
                cout << "NULL";
            }
        }

        cout << '\n';
    }
}


// ============================================================================
// 16. UNMATCHED RECORD DETECTION
// ============================================================================

void demonstrateUnmatchedRows(const Database& database) {
    printSection("8. UNMATCHED RECORD DETECTION");

    auto employeesWithoutDepartments = leftJoin<
        Employee,
        Department,
        int,
        pair<string, bool>
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](const Employee& employee, optional<Department> department) {
            return make_pair(
                employee.name,
                department.has_value()
            );
        }
    );

    cout << "Employees without matching departments:\n";

    for (const auto& row : employeesWithoutDepartments) {
        if (!row.second) {
            cout << "  " << row.first << '\n';
        }
    }

    auto departmentsWithNoEmployees = rightJoin<
        Employee,
        Department,
        int,
        pair<string, bool>
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](optional<Employee> employee, optional<Department> department) {
            return make_pair(
                department->name,
                employee.has_value()
            );
        }
    );

    cout << "\nDepartments without matching employees:\n";

    for (const auto& row : departmentsWithNoEmployees) {
        if (!row.second) {
            cout << "  " << row.first << '\n';
        }
    }
}


// ============================================================================
// 17. AGGREGATION AFTER JOIN
// ============================================================================

struct DepartmentStatistics {
    int departmentId;
    string departmentName;
    int employeeCount = 0;
    long long totalSalary = 0;
};

void demonstrateAggregation(const Database& database) {
    printSection("9. AGGREGATION AFTER LEFT JOIN");

    vector<DepartmentStatistics> statistics;

    for (const auto& department : database.departments) {
        DepartmentStatistics row{
            department.id,
            department.name,
            0,
            0
        };

        for (const auto& employee : database.employees) {
            if (
                employee.departmentId.has_value() &&
                *employee.departmentId == department.id
            ) {
                ++row.employeeCount;
                row.totalSalary += employee.salary;
            }
        }

        statistics.push_back(row);
    }

    for (const auto& row : statistics) {
        double averageSalary =
            row.employeeCount == 0
                ? 0.0
                : static_cast<double>(row.totalSalary) / row.employeeCount;

        cout << left
             << setw(20) << row.departmentName
             << " | employees=" << setw(3) << row.employeeCount
             << " | average_salary=" << fixed << setprecision(2)
             << averageSalary << '\n';
    }

    cout << "\nThe department with zero employees is preserved because "
            "the conceptual operation is a LEFT JOIN followed by aggregation.\n";
}


// ============================================================================
// 18. DUPLICATE JOIN KEY CASE
// ============================================================================

void demonstrateDuplicateKeys() {
    printSection("10. DUPLICATE JOIN KEYS");

    struct Alias {
        int employeeId;
        string value;
    };

    vector<Employee> employees = {
        {1, "Asha", 10, nullopt, 95000},
        {2, "Ravi", 10, 1, 82000}
    };

    vector<Alias> aliases = {
        {1, "Asha P."},
        {1, "Architect Asha"},
        {2, "Ravi K."}
    };

    auto result = innerJoin<
        Employee,
        Alias,
        int,
        string
    >(
        employees,
        aliases,
        [](const Employee& employee) {
            return employee.id;
        },
        [](const Alias& alias) {
            return alias.employeeId;
        },
        [](const Employee& employee, const Alias& alias) {
            return employee.name + " -> " + alias.value;
        }
    );

    for (const auto& row : result) {
        cout << row << '\n';
    }

    cout << "\nA non-unique join key creates multiple output rows for "
            "a matching left row.\n";
}


// ============================================================================
// 19. PERFORMANCE COMPARISON
// ============================================================================

void demonstratePerformance() {
    printSection("11. HASH-INDEX JOIN PERFORMANCE");

    struct Record {
        int id;
        long long value;
    };

    vector<Record> left;
    vector<Record> right;

    constexpr int rowCount = 50000;

    left.reserve(rowCount);
    right.reserve(rowCount);

    for (int i = 0; i < rowCount; ++i) {
        left.push_back({i, static_cast<long long>(i) * 2});
        right.push_back({i, static_cast<long long>(i) * 3});
    }

    const auto start = chrono::steady_clock::now();

    auto result = innerJoin<
        Record,
        Record,
        int,
        long long
    >(
        left,
        right,
        [](const Record& row) {
            return row.id;
        },
        [](const Record& row) {
            return row.id;
        },
        [](const Record& first, const Record& second) {
            return first.value + second.value;
        }
    );

    const auto end = chrono::steady_clock::now();

    const auto milliseconds =
        chrono::duration_cast<chrono::milliseconds>(
            end - start
        ).count();

    cout << "Left rows: " << left.size() << '\n';
    cout << "Right rows: " << right.size() << '\n';
    cout << "Joined rows: " << result.size() << '\n';
    cout << "Elapsed time: " << milliseconds << " ms\n";

    cout << "\nA naive nested-loop equality join would inspect approximately "
            "50,000 * 50,000 pairs in this example. The hash-index approach "
            "avoids that full Cartesian comparison in the common case.\n";
}


// ============================================================================
// 20. VALIDATION
// ============================================================================

void runValidation(const Database& database) {
    printSection("12. CASE STUDY VALIDATION");

    auto innerResult = innerJoin<
        Employee,
        Department,
        int,
        string
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](const Employee& employee, const Department& department) {
            return employee.name + ":" + department.name;
        }
    );

    auto leftResult = leftJoin<
        Employee,
        Department,
        int,
        string
    >(
        database.employees,
        database.departments,
        [](const Employee& employee) {
            return employee.departmentId.value_or(-1);
        },
        [](const Department& department) {
            return department.id;
        },
        [](const Employee& employee, optional<Department> department) {
            return employee.name + ":" +
                (department.has_value() ? department->name : "NULL");
        }
    );

    if (innerResult.size() != 5) {
        throw runtime_error("INNER JOIN validation failed.");
    }

    if (leftResult.size() != 6) {
        throw runtime_error("LEFT JOIN validation failed.");
    }

    cout << "INNER JOIN row count: " << innerResult.size() << '\n';
    cout << "LEFT JOIN row count: " << leftResult.size() << '\n';
    cout << "All validation checks passed.\n";
}


// ============================================================================
// 21. DESIGN RULES
// ============================================================================

void printDesignRules() {
    printSection("13. PRODUCTION JOIN DESIGN RULES");

    vector<string> rules = {
        "Define the intended result grain before writing the join.",
        "Identify the business key used to establish correspondence.",
        "Verify whether the key is unique on either side.",
        "Use INNER JOIN when unmatched rows should be excluded.",
        "Use LEFT JOIN when every left-side entity must remain visible.",
        "Use RIGHT JOIN when preserving the right relation is clearer.",
        "Use FULL OUTER JOIN when discrepancies on both sides matter.",
        "Use all columns of a composite business key.",
        "Expect row multiplication in one-to-many and many-to-many relationships.",
        "Use IS NULL rather than = NULL.",
        "Check ON versus WHERE placement carefully with outer joins.",
        "Use indexes when they support real query workloads.",
        "Use parameterized SQL for untrusted external values.",
        "Validate row counts and expected cardinality during query development.",
        "Inspect execution plans when joins become expensive."
    };

    for (size_t i = 0; i < rules.size(); ++i) {
        cout << (i + 1) << ". " << rules[i] << '\n';
    }
}


// ============================================================================
// 22. MAIN
// ============================================================================

int main() {
    try {
        const Database database = createDatabase();

        demonstrateInnerJoin(database);
        demonstrateLeftJoin(database);
        demonstrateRightJoin(database);
        demonstrateFullOuterJoin(database);
        demonstrateManyToMany(database);
        demonstrateCompositeJoin(database);
        demonstrateSelfJoin(database);
        demonstrateUnmatchedRows(database);
        demonstrateAggregation(database);
        demonstrateDuplicateKeys();
        demonstratePerformance();
        runValidation(database);
        printDesignRules();

        printSection("CASE STUDY COMPLETED");
        cout << "The in-memory relational join engine completed successfully.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
