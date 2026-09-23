/*
 * SQL Filtering Case Study
 *
 * Topic:
 *   WHERE, comparison operators, AND, OR, NOT, IN, BETWEEN, LIKE, IS NULL
 *
 * Case study:
 *   Employee and workforce search system
 *
 * The program models a database-style filtering engine in standard C++17.
 * It demonstrates how SQL predicates can be represented by application code,
 * composed into complex search rules, validated, tested, and evaluated.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic sql_filtering.cpp -o sql_filtering
 *
 * Run:
 *   ./sql_filtering
 *
 * On Windows with MinGW:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic sql_filtering.cpp -o sql_filtering.exe
 *   .\sql_filtering.exe
 */

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using namespace std;


// ---------------------------------------------------------------------------
// 1. DOMAIN MODEL
// ---------------------------------------------------------------------------

struct Employee {
    int id;
    string name;
    string department;
    double salary;
    int age;
    optional<string> city;
    optional<string> email;
    bool active;
};


// ---------------------------------------------------------------------------
// 2. SQL-STYLE THREE-VALUED LOGIC
// ---------------------------------------------------------------------------

enum class TruthValue {
    False,
    True,
    Unknown
};

string truthValueToString(TruthValue value) {
    switch (value) {
        case TruthValue::False:
            return "FALSE";
        case TruthValue::True:
            return "TRUE";
        case TruthValue::Unknown:
            return "UNKNOWN";
    }

    return "UNKNOWN";
}

TruthValue sqlNot(TruthValue value) {
    if (value == TruthValue::Unknown) {
        return TruthValue::Unknown;
    }

    return value == TruthValue::True
        ? TruthValue::False
        : TruthValue::True;
}

TruthValue sqlAnd(TruthValue left, TruthValue right) {
    /*
     * SQL AND:
     *
     * TRUE AND TRUE       = TRUE
     * TRUE AND FALSE      = FALSE
     * TRUE AND UNKNOWN    = UNKNOWN
     * FALSE AND anything  = FALSE
     * UNKNOWN AND UNKNOWN = UNKNOWN
     */
    if (left == TruthValue::False || right == TruthValue::False) {
        return TruthValue::False;
    }

    if (left == TruthValue::Unknown || right == TruthValue::Unknown) {
        return TruthValue::Unknown;
    }

    return TruthValue::True;
}

TruthValue sqlOr(TruthValue left, TruthValue right) {
    /*
     * SQL OR:
     *
     * TRUE OR anything     = TRUE
     * FALSE OR FALSE       = FALSE
     * FALSE OR UNKNOWN     = UNKNOWN
     * UNKNOWN OR UNKNOWN   = UNKNOWN
     */
    if (left == TruthValue::True || right == TruthValue::True) {
        return TruthValue::True;
    }

    if (left == TruthValue::Unknown || right == TruthValue::Unknown) {
        return TruthValue::Unknown;
    }

    return TruthValue::False;
}


// ---------------------------------------------------------------------------
// 3. COMPARISON HELPERS
// ---------------------------------------------------------------------------

TruthValue sqlEqual(
    const optional<string>& left,
    const optional<string>& right
) {
    /*
     * SQL NULL is not an ordinary value.
     *
     * NULL = value -> UNKNOWN
     * NULL = NULL  -> UNKNOWN
     */
    if (!left.has_value() || !right.has_value()) {
        return TruthValue::Unknown;
    }

    return *left == *right
        ? TruthValue::True
        : TruthValue::False;
}

TruthValue sqlGreaterThan(
    const optional<double>& left,
    double right
) {
    if (!left.has_value()) {
        return TruthValue::Unknown;
    }

    return *left > right
        ? TruthValue::True
        : TruthValue::False;
}

TruthValue sqlBetween(
    const optional<double>& value,
    double lower,
    double upper
) {
    if (!value.has_value()) {
        return TruthValue::Unknown;
    }

    return *value >= lower && *value <= upper
        ? TruthValue::True
        : TruthValue::False;
}


// ---------------------------------------------------------------------------
// 4. LIKE IMPLEMENTATION
// ---------------------------------------------------------------------------

bool likeMatch(
    string_view text,
    string_view pattern,
    size_t textIndex = 0,
    size_t patternIndex = 0
) {
    /*
     * This recursive implementation models the two major SQL LIKE
     * wildcards:
     *
     *   % -> zero or more characters
     *   _ -> exactly one character
     *
     * For a production database, pattern matching would normally be handled
     * by the database engine rather than reimplemented in application code.
     */
    if (patternIndex == pattern.size()) {
        return textIndex == text.size();
    }

    char patternCharacter = pattern[patternIndex];

    if (patternCharacter == '%') {
        /*
         * % can represent zero characters or consume one character and
         * continue matching.
         */
        if (likeMatch(text, pattern, textIndex, patternIndex + 1)) {
            return true;
        }

        if (textIndex < text.size()) {
            return likeMatch(
                text,
                pattern,
                textIndex + 1,
                patternIndex
            );
        }

        return false;
    }

    if (patternCharacter == '_') {
        if (textIndex >= text.size()) {
            return false;
        }

        return likeMatch(
            text,
            pattern,
            textIndex + 1,
            patternIndex + 1
        );
    }

    if (textIndex >= text.size()) {
        return false;
    }

    char textCharacter = static_cast<char>(
        tolower(static_cast<unsigned char>(text[textIndex]))
    );

    char normalizedPatternCharacter = static_cast<char>(
        tolower(static_cast<unsigned char>(patternCharacter))
    );

    if (textCharacter != normalizedPatternCharacter) {
        return false;
    }

    return likeMatch(
        text,
        pattern,
        textIndex + 1,
        patternIndex + 1
    );
}


// ---------------------------------------------------------------------------
// 5. DATASET
// ---------------------------------------------------------------------------

vector<Employee> createEmployees() {
    return {
        {
            1,
            "Aarav Sharma",
            "Engineering",
            145000,
            42,
            string("Bengaluru"),
            string("aarav@example.com"),
            true
        },
        {
            2,
            "Priya Singh",
            "Engineering",
            118000,
            34,
            string("Lucknow"),
            string("priya@example.com"),
            true
        },
        {
            3,
            "Rahul Verma",
            "Engineering",
            92000,
            28,
            string("Delhi"),
            string("rahul@example.com"),
            true
        },
        {
            4,
            "Neha Gupta",
            "Finance",
            87000,
            31,
            string("Mumbai"),
            string("neha@example.com"),
            true
        },
        {
            5,
            "Vikram Rao",
            "Finance",
            71000,
            39,
            string("Pune"),
            nullopt,
            true
        },
        {
            6,
            "Ananya Mehta",
            "Human Resources",
            68000,
            29,
            string("Delhi"),
            string("ananya@example.com"),
            true
        },
        {
            7,
            "Karan Malhotra",
            "Finance",
            130000,
            45,
            string("Mumbai"),
            string("karan@example.com"),
            true
        },
        {
            8,
            "Ishita Kapoor",
            "Sales",
            76000,
            27,
            string("Lucknow"),
            string("ishita@example.com"),
            true
        },
        {
            9,
            "Dev Patel",
            "Sales",
            73000,
            30,
            string("Ahmedabad"),
            string("dev@example.com"),
            true
        },
        {
            10,
            "Riya Nair",
            "Sales",
            110000,
            38,
            string("Kochi"),
            string("riya@example.com"),
            true
        },
        {
            11,
            "Arjun Das",
            "Security",
            105000,
            33,
            string("Hyderabad"),
            string("arjun@example.com"),
            true
        },
        {
            12,
            "Meera Joshi",
            "Security",
            138000,
            41,
            string("Pune"),
            string("meera@example.com"),
            true
        },
        {
            13,
            "Kabir Khan",
            "Engineering",
            35000,
            21,
            string("Jaipur"),
            string("kabir@example.com"),
            false
        },
        {
            14,
            "Sara Ali",
            "Consulting",
            98000,
            36,
            nullopt,
            string("sara@example.com"),
            true
        }
    };
}


// ---------------------------------------------------------------------------
// 6. OUTPUT
// ---------------------------------------------------------------------------

string optionalValue(const optional<string>& value) {
    return value.has_value() ? *value : "NULL";
}

void printEmployees(
    const vector<Employee>& employees,
    const string& title
) {
    cout << "\n--- " << title << " ---\n";

    if (employees.empty()) {
        cout << "(no rows)\n";
        return;
    }

    cout << left
         << setw(4) << "ID"
         << setw(20) << "Name"
         << setw(18) << "Department"
         << setw(12) << "Salary"
         << setw(6) << "Age"
         << setw(15) << "City"
         << setw(28) << "Email"
         << setw(8) << "Active"
         << '\n';

    cout << string(111, '-') << '\n';

    for (const Employee& employee : employees) {
        cout << left
             << setw(4) << employee.id
             << setw(20) << employee.name
             << setw(18) << employee.department
             << setw(12) << fixed << setprecision(2) << employee.salary
             << setw(6) << employee.age
             << setw(15) << optionalValue(employee.city)
             << setw(28) << optionalValue(employee.email)
             << setw(8) << (employee.active ? "YES" : "NO")
             << '\n';
    }
}


// ---------------------------------------------------------------------------
// 7. GENERIC FILTER ENGINE
// ---------------------------------------------------------------------------

using Predicate = function<TruthValue(const Employee&)>;

vector<Employee> filterEmployees(
    const vector<Employee>& employees,
    const Predicate& predicate
) {
    vector<Employee> result;

    for (const Employee& employee : employees) {
        /*
         * SQL WHERE keeps only TRUE.
         *
         * FALSE and UNKNOWN are both rejected.
         */
        if (predicate(employee) == TruthValue::True) {
            result.push_back(employee);
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// 8. BASIC PREDICATES
// ---------------------------------------------------------------------------

Predicate salaryGreaterThan(double amount) {
    return [amount](const Employee& employee) {
        return employee.salary > amount
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate salaryAtLeast(double amount) {
    return [amount](const Employee& employee) {
        return employee.salary >= amount
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate salaryBetween(double lower, double upper) {
    return [lower, upper](const Employee& employee) {
        return sqlBetween(employee.salary, lower, upper);
    };
}

Predicate departmentEquals(string department) {
    return [department](const Employee& employee) {
        return employee.department == department
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate departmentIn(set<string> departments) {
    return [departments = move(departments)](const Employee& employee) {
        return departments.contains(employee.department)
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate cityEquals(string city) {
    return [city = move(city)](const Employee& employee) {
        if (!employee.city.has_value()) {
            return TruthValue::Unknown;
        }

        return *employee.city == city
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate cityIn(set<string> cities) {
    return [cities = move(cities)](const Employee& employee) {
        if (!employee.city.has_value()) {
            return TruthValue::Unknown;
        }

        return cities.contains(*employee.city)
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate activeOnly() {
    return [](const Employee& employee) {
        return employee.active
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate hasEmail() {
    return [](const Employee& employee) {
        return employee.email.has_value()
            ? TruthValue::True
            : TruthValue::False;
    };
}

Predicate nameLike(string pattern) {
    return [pattern = move(pattern)](const Employee& employee) {
        return likeMatch(employee.name, pattern)
            ? TruthValue::True
            : TruthValue::False;
    };
}


// ---------------------------------------------------------------------------
// 9. LOGICAL COMBINATORS
// ---------------------------------------------------------------------------

Predicate logicalNot(Predicate predicate) {
    return [predicate = move(predicate)](const Employee& employee) {
        return sqlNot(predicate(employee));
    };
}

Predicate logicalAnd(
    Predicate left,
    Predicate right
) {
    return [
        left = move(left),
        right = move(right)
    ](const Employee& employee) {
        return sqlAnd(left(employee), right(employee));
    };
}

Predicate logicalOr(
    Predicate left,
    Predicate right
) {
    return [
        left = move(left),
        right = move(right)
    ](const Employee& employee) {
        return sqlOr(left(employee), right(employee));
    };
}


// ---------------------------------------------------------------------------
// 10. BASIC WHERE CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateWhere(const vector<Employee>& employees) {
    auto result = filterEmployees(
        employees,
        salaryGreaterThan(100000)
    );

    printEmployees(
        result,
        "WHERE salary > 100000"
    );
}


// ---------------------------------------------------------------------------
// 11. AND CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateAnd(const vector<Employee>& employees) {
    /*
     * SQL:
     *
     * WHERE salary >= 80000
     *   AND age < 40
     */
    auto predicate = logicalAnd(
        salaryAtLeast(80000),
        [](const Employee& employee) {
            return employee.age < 40
                ? TruthValue::True
                : TruthValue::False;
        }
    );

    auto result = filterEmployees(employees, predicate);

    printEmployees(
        result,
        "AND: salary >= 80000 AND age < 40"
    );
}


// ---------------------------------------------------------------------------
// 12. OR CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateOr(const vector<Employee>& employees) {
    /*
     * SQL:
     *
     * WHERE city = 'Lucknow'
     *    OR city = 'Mumbai'
     */
    auto predicate = logicalOr(
        cityEquals("Lucknow"),
        cityEquals("Mumbai")
    );

    auto result = filterEmployees(employees, predicate);

    printEmployees(
        result,
        "OR: Lucknow or Mumbai"
    );
}


// ---------------------------------------------------------------------------
// 13. NOT CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateNot(const vector<Employee>& employees) {
    /*
     * SQL:
     *
     * WHERE NOT city = 'Delhi'
     *
     * Employees whose city is NULL do not pass this filter because:
     *
     * NOT UNKNOWN = UNKNOWN
     *
     * WHERE retains only TRUE.
     */
    auto predicate = logicalNot(cityEquals("Delhi"));

    auto result = filterEmployees(employees, predicate);

    printEmployees(
        result,
        "NOT city = Delhi"
    );
}


// ---------------------------------------------------------------------------
// 14. IN CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateIn(const vector<Employee>& employees) {
    auto predicate = cityIn({
        "Delhi",
        "Mumbai",
        "Lucknow"
    });

    auto result = filterEmployees(employees, predicate);

    printEmployees(
        result,
        "IN: Delhi, Mumbai, Lucknow"
    );
}


// ---------------------------------------------------------------------------
// 15. BETWEEN CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateBetween(const vector<Employee>& employees) {
    auto predicate = salaryBetween(80000, 100000);

    auto result = filterEmployees(employees, predicate);

    printEmployees(
        result,
        "BETWEEN 80000 AND 100000"
    );
}


// ---------------------------------------------------------------------------
// 16. LIKE CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateLike(const vector<Employee>& employees) {
    auto startsWithA = filterEmployees(
        employees,
        nameLike("A%")
    );

    auto containsAr = filterEmployees(
        employees,
        nameLike("%ar%")
    );

    auto secondCharacterE = filterEmployees(
        employees,
        nameLike("_e%")
    );

    printEmployees(
        startsWithA,
        "LIKE 'A%'"
    );

    printEmployees(
        containsAr,
        "LIKE '%ar%'"
    );

    printEmployees(
        secondCharacterE,
        "LIKE '_e%'"
    );
}


// ---------------------------------------------------------------------------
// 17. IS NULL / IS NOT NULL
// ---------------------------------------------------------------------------

void demonstrateNullFiltering(const vector<Employee>& employees) {
    /*
     * SQL:
     *
     * WHERE email IS NULL
     *
     * is represented by checking optional::has_value().
     */
    auto missingEmail = filterEmployees(
        employees,
        [](const Employee& employee) {
            return employee.email.has_value()
                ? TruthValue::False
                : TruthValue::True;
        }
    );

    auto availableEmail = filterEmployees(
        employees,
        hasEmail()
    );

    printEmployees(
        missingEmail,
        "IS NULL: missing email"
    );

    printEmployees(
        availableEmail,
        "IS NOT NULL: available email"
    );
}


// ---------------------------------------------------------------------------
// 18. COMPLEX BUSINESS FILTER
// ---------------------------------------------------------------------------

void demonstrateComplexBusinessFilter(
    const vector<Employee>& employees
) {
    /*
     * Business requirement:
     *
     * Find active employees who:
     *   - work in Engineering or Security,
     *   - earn between 90000 and 140000,
     *   - have an email address,
     *   - and have a name containing "a".
     *
     * SQL form:
     *
     * WHERE active = 1
     *   AND department IN ('Engineering', 'Security')
     *   AND salary BETWEEN 90000 AND 140000
     *   AND email IS NOT NULL
     *   AND name LIKE '%a%'
     */
    auto predicate = logicalAnd(
        activeOnly(),
        logicalAnd(
            departmentIn({
                "Engineering",
                "Security"
            }),
            logicalAnd(
                salaryBetween(90000, 140000),
                logicalAnd(
                    hasEmail(),
                    nameLike("%a%")
                )
            )
        )
    );

    auto result = filterEmployees(
        employees,
        predicate
    );

    printEmployees(
        result,
        "Complex workforce search"
    );
}


// ---------------------------------------------------------------------------
// 19. OPTIONAL SEARCH CRITERIA
// ---------------------------------------------------------------------------

struct EmployeeFilter {
    optional<double> minimumSalary;
    optional<double> maximumSalary;
    set<string> cities;
    set<string> departments;
    optional<string> namePattern;
    bool activeOnly = false;
    bool requireEmail = false;
};

Predicate buildPredicate(const EmployeeFilter& criteria) {
    /*
     * Optional application filters are composed incrementally.
     *
     * The empty condition starts as TRUE. Each specified filter adds an AND.
     */
    Predicate predicate = [](const Employee&) {
        return TruthValue::True;
    };

    if (criteria.minimumSalary.has_value()) {
        predicate = logicalAnd(
            move(predicate),
            salaryAtLeast(*criteria.minimumSalary)
        );
    }

    if (criteria.maximumSalary.has_value()) {
        const double maximum = *criteria.maximumSalary;

        predicate = logicalAnd(
            move(predicate),
            [maximum](const Employee& employee) {
                return employee.salary <= maximum
                    ? TruthValue::True
                    : TruthValue::False;
            }
        );
    }

    if (!criteria.cities.empty()) {
        predicate = logicalAnd(
            move(predicate),
            cityIn(criteria.cities)
        );
    }

    if (!criteria.departments.empty()) {
        predicate = logicalAnd(
            move(predicate),
            departmentIn(criteria.departments)
        );
    }

    if (criteria.namePattern.has_value()) {
        predicate = logicalAnd(
            move(predicate),
            nameLike(*criteria.namePattern)
        );
    }

    if (criteria.activeOnly) {
        predicate = logicalAnd(
            move(predicate),
            activeOnly()
        );
    }

    if (criteria.requireEmail) {
        predicate = logicalAnd(
            move(predicate),
            hasEmail()
        );
    }

    return predicate;
}

void demonstrateOptionalSearch(
    const vector<Employee>& employees
) {
    EmployeeFilter criteria;

    criteria.minimumSalary = 70000;
    criteria.maximumSalary = 140000;

    criteria.cities = {
        "Lucknow",
        "Delhi",
        "Pune",
        "Hyderabad"
    };

    criteria.departments = {
        "Engineering",
        "Finance",
        "Security",
        "Sales"
    };

    criteria.namePattern = "%a%";
    criteria.activeOnly = true;
    criteria.requireEmail = true;

    auto predicate = buildPredicate(criteria);

    auto result = filterEmployees(
        employees,
        predicate
    );

    printEmployees(
        result,
        "Configurable employee search"
    );
}


// ---------------------------------------------------------------------------
// 20. QUERY LOGIC PRECEDENCE
// ---------------------------------------------------------------------------

void demonstratePrecedence(
    const vector<Employee>& employees
) {
    /*
     * Without parentheses:
     *
     * city = 'Delhi'
     * OR city = 'Mumbai'
     * AND salary > 100000
     *
     * AND has higher logical precedence than OR.
     *
     * Explicit grouping:
     *
     * (city = 'Delhi' OR city = 'Mumbai')
     * AND salary > 100000
     *
     * can produce a different result.
     */
    auto withoutGrouping = logicalOr(
        cityEquals("Delhi"),
        logicalAnd(
            cityEquals("Mumbai"),
            salaryGreaterThan(100000)
        )
    );

    auto withGrouping = logicalAnd(
        logicalOr(
            cityEquals("Delhi"),
            cityEquals("Mumbai")
        ),
        salaryGreaterThan(100000)
    );

    auto firstResult = filterEmployees(
        employees,
        withoutGrouping
    );

    auto secondResult = filterEmployees(
        employees,
        withGrouping
    );

    printEmployees(
        firstResult,
        "AND/OR precedence without explicit grouping"
    );

    printEmployees(
        secondResult,
        "Explicit grouping with parentheses"
    );
}


// ---------------------------------------------------------------------------
// 21. NULL LOGIC TABLE
// ---------------------------------------------------------------------------

void demonstrateTruthTables() {
    vector<TruthValue> values = {
        TruthValue::True,
        TruthValue::False,
        TruthValue::Unknown
    };

    cout << "\n--- SQL AND truth table ---\n";

    for (TruthValue left : values) {
        for (TruthValue right : values) {
            cout << truthValueToString(left)
                 << " AND "
                 << truthValueToString(right)
                 << " = "
                 << truthValueToString(sqlAnd(left, right))
                 << '\n';
        }
    }

    cout << "\n--- SQL OR truth table ---\n";

    for (TruthValue left : values) {
        for (TruthValue right : values) {
            cout << truthValueToString(left)
                 << " OR "
                 << truthValueToString(right)
                 << " = "
                 << truthValueToString(sqlOr(left, right))
                 << '\n';
        }
    }

    cout << "\n--- SQL NOT truth table ---\n";

    for (TruthValue value : values) {
        cout << "NOT "
             << truthValueToString(value)
             << " = "
             << truthValueToString(sqlNot(value))
             << '\n';
    }
}


// ---------------------------------------------------------------------------
// 22. VALIDATION
// ---------------------------------------------------------------------------

void validateFiltering(
    const vector<Employee>& employees
) {
    auto highEarners = filterEmployees(
        employees,
        salaryGreaterThan(100000)
    );

    for (const Employee& employee : highEarners) {
        if (employee.salary <= 100000) {
            throw runtime_error(
                "Filtering invariant failed: salary threshold"
            );
        }
    }

    auto missingEmail = filterEmployees(
        employees,
        [](const Employee& employee) {
            return employee.email.has_value()
                ? TruthValue::False
                : TruthValue::True;
        }
    );

    for (const Employee& employee : missingEmail) {
        if (employee.email.has_value()) {
            throw runtime_error(
                "Filtering invariant failed: NULL email"
            );
        }
    }

    auto boundedSalary = filterEmployees(
        employees,
        salaryBetween(80000, 100000)
    );

    for (const Employee& employee : boundedSalary) {
        if (employee.salary < 80000 ||
            employee.salary > 100000) {
            throw runtime_error(
                "Filtering invariant failed: BETWEEN range"
            );
        }
    }

    cout << "\n--- Validation ---\n";
    cout << "Salary predicate: PASS\n";
    cout << "IS NULL predicate: PASS\n";
    cout << "BETWEEN predicate: PASS\n";
}


// ---------------------------------------------------------------------------
// 23. COMPLEXITY DISCUSSION
// ---------------------------------------------------------------------------

void demonstrateComplexity(
    const vector<Employee>& employees
) {
    /*
     * A straightforward in-memory filter scans every employee:
     *
     *     O(n)
     *
     * If a membership test uses std::set, the membership lookup is roughly:
     *
     *     O(log k)
     *
     * where k is the number of allowed values.
     *
     * A database may do better than a full scan by using an index. The
     * database optimizer chooses an execution strategy based on statistics,
     * indexes, predicate structure, selectivity, and other factors.
     */
    size_t inspectedRows = 0;

    vector<Employee> result;

    for (const Employee& employee : employees) {
        ++inspectedRows;

        if (employee.salary >= 100000) {
            result.push_back(employee);
        }
    }

    cout << "\n--- In-memory complexity demonstration ---\n";
    cout << "Rows inspected: " << inspectedRows << '\n';
    cout << "Rows returned: " << result.size() << '\n';
    cout << "Time complexity of a direct scan: O(n)\n";
    cout << "Additional result storage: O(r), where r is result count\n";
}


// ---------------------------------------------------------------------------
// 24. EDGE CASES
// ---------------------------------------------------------------------------

void demonstrateEdgeCases(
    const vector<Employee>& employees
) {
    /*
     * Edge case 1:
     * A NULL city does not satisfy city = 'Delhi'.
     */
    auto delhi = filterEmployees(
        employees,
        cityEquals("Delhi")
    );

    /*
     * Edge case 2:
     * A NULL city also does not satisfy NOT(city = 'Delhi') because
     * NOT UNKNOWN is UNKNOWN.
     */
    auto notDelhi = filterEmployees(
        employees,
        logicalNot(cityEquals("Delhi"))
    );

    /*
     * Edge case 3:
     * LIKE '%' matches every non-NULL name.
     */
    auto allNamedEmployees = filterEmployees(
        employees,
        nameLike("%")
    );

    cout << "\n--- Edge cases ---\n";
    cout << "Delhi rows: " << delhi.size() << '\n';
    cout << "NOT Delhi rows: " << notDelhi.size() << '\n';
    cout << "LIKE '%' rows: " << allNamedEmployees.size() << '\n';

    /*
     * The employee with a NULL city is intentionally absent from both
     * city = 'Delhi' and NOT(city = 'Delhi').
     */
}


// ---------------------------------------------------------------------------
// 25. PERFORMANCE-AWARE FILTERING
// ---------------------------------------------------------------------------

void demonstratePerformanceConsiderations(
    const vector<Employee>& employees
) {
    /*
     * In a real SQL database:
     *
     *   WHERE employee_id = 11
     *
     * may use a primary-key index and avoid scanning every row.
     *
     * In this C++ case study, the vector itself is not indexed, so a search
     * still scans linearly.
     *
     * This illustrates an important distinction:
     * application-level filtering and database-level filtering are not
     * interchangeable from a performance perspective.
     */
    auto result = filterEmployees(
        employees,
        [](const Employee& employee) {
            return employee.id == 11
                ? TruthValue::True
                : TruthValue::False;
        }
    );

    printEmployees(
        result,
        "Highly selective ID filter"
    );

    cout << "\nA vector scan is O(n); a database index may provide a different "
            "execution strategy.\n";
}


// ---------------------------------------------------------------------------
// 26. INDUSTRY-STYLE SEARCH SERVICE
// ---------------------------------------------------------------------------

class EmployeeSearchService {
private:
    const vector<Employee>& employees;

public:
    explicit EmployeeSearchService(
        const vector<Employee>& employees
    )
        : employees(employees) {}

    vector<Employee> search(
        const EmployeeFilter& criteria
    ) const {
        Predicate predicate = buildPredicate(criteria);
        return filterEmployees(employees, predicate);
    }

    vector<Employee> searchHighValueEngineering() const {
        EmployeeFilter criteria;

        criteria.minimumSalary = 100000;
        criteria.departments = {"Engineering"};
        criteria.activeOnly = true;
        criteria.requireEmail = true;

        return search(criteria);
    }
};

void demonstrateServiceLayer(
    const vector<Employee>& employees
) {
    EmployeeSearchService service(employees);

    auto result = service.searchHighValueEngineering();

    printEmployees(
        result,
        "Service-layer: active high-value Engineering employees"
    );
}


// ---------------------------------------------------------------------------
// 27. MAIN
// ---------------------------------------------------------------------------

int main() {
    try {
        cout << string(78, '=') << '\n';
        cout << "SQL FILTERING CASE STUDY IN C++17\n";
        cout << string(78, '=') << '\n';

        const vector<Employee> employees = createEmployees();

        demonstrateWhere(employees);
        demonstrateAnd(employees);
        demonstrateOr(employees);
        demonstrateNot(employees);
        demonstrateIn(employees);
        demonstrateBetween(employees);
        demonstrateLike(employees);
        demonstrateNullFiltering(employees);
        demonstrateComplexBusinessFilter(employees);
        demonstrateOptionalSearch(employees);
        demonstratePrecedence(employees);
        demonstrateTruthTables();
        demonstrateEdgeCases(employees);
        demonstrateComplexity(employees);
        demonstratePerformanceConsiderations(employees);
        demonstrateServiceLayer(employees);
        validateFiltering(employees);

        cout << "\n" << string(78, '=') << '\n';
        cout << "C++ CASE STUDY COMPLETED SUCCESSFULLY\n";
        cout << string(78, '=') << '\n';

        return 0;
    }
    catch (const exception& error) {
        cerr << "\nFatal error: " << error.what() << '\n';
        return 1;
    }
}
