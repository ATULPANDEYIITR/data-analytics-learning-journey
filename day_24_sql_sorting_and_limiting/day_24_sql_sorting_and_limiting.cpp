/*
SQL Sorting & Limiting
======================

C++ industry-style case study:
A production-oriented employee directory query service.

The program models a database result set in memory and implements the
application-layer semantics of:

    ORDER BY
    ASC
    DESC
    LIMIT
    OFFSET
    deterministic ordering
    pagination
    keyset pagination
    filtering
    validation
    safe dynamic sorting
    performance measurement

The program does not pretend to be a complete SQL database engine. Instead,
it demonstrates how an application can reason about and consume ordered
relational data, while also showing the SQL statements that a real database
layer would execute.

Requirements:
    C++17 or later
*/

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>


// -----------------------------------------------------------------------------
// Domain model
// -----------------------------------------------------------------------------

struct Employee {
    int employeeId;
    std::string employeeName;
    std::string department;
    long long salary;
    std::optional<double> performanceScore;
    std::string hireDate;
    std::optional<std::string> city;
};


// -----------------------------------------------------------------------------
// Presentation utilities
// -----------------------------------------------------------------------------

void printHeader(const std::string& title) {
    std::cout << "\n"
              << std::string(88, '=') << "\n"
              << title << "\n"
              << std::string(88, '=')
              << "\n";
}


void printSubheader(const std::string& title) {
    std::cout << "\n"
              << std::string(88, '-') << "\n"
              << title << "\n"
              << std::string(88, '-') << "\n";
}


std::string scoreToString(
    const std::optional<double>& score
) {
    if (!score.has_value()) {
        return "NULL";
    }

    std::ostringstream output;
    output << std::fixed << std::setprecision(1) << *score;
    return output.str();
}


std::string cityToString(
    const std::optional<std::string>& city
) {
    return city.value_or("NULL");
}


void printEmployees(
    const std::vector<Employee>& employees
) {
    std::cout
        << std::left
        << std::setw(6) << "ID"
        << std::setw(14) << "Name"
        << std::setw(15) << "Department"
        << std::setw(12) << "Salary"
        << std::setw(10) << "Score"
        << std::setw(13) << "Hire Date"
        << std::setw(14) << "City"
        << "\n";

    std::cout << std::string(84, '-') << "\n";

    for (const auto& employee : employees) {
        std::cout
            << std::left
            << std::setw(6) << employee.employeeId
            << std::setw(14) << employee.employeeName
            << std::setw(15) << employee.department
            << std::setw(12) << employee.salary
            << std::setw(10) << scoreToString(employee.performanceScore)
            << std::setw(13) << employee.hireDate
            << std::setw(14) << cityToString(employee.city)
            << "\n";
    }
}


// -----------------------------------------------------------------------------
// Sample database result
// -----------------------------------------------------------------------------

std::vector<Employee> createEmployees() {
    return {
        {
            1,
            "Aarav",
            "Engineering",
            125000,
            9.2,
            "2021-04-15",
            "Delhi"
        },
        {
            2,
            "Meera",
            "Engineering",
            125000,
            8.8,
            "2022-08-21",
            "Mumbai"
        },
        {
            3,
            "Kabir",
            "Engineering",
            98000,
            9.5,
            "2023-01-10",
            "Pune"
        },
        {
            4,
            "Anaya",
            "Engineering",
            87000,
            std::nullopt,
            "2024-02-19",
            "Lucknow"
        },
        {
            5,
            "Vihaan",
            "Finance",
            110000,
            8.9,
            "2020-07-01",
            "Delhi"
        },
        {
            6,
            "Ishita",
            "Finance",
            110000,
            9.1,
            "2021-11-12",
            "Bengaluru"
        },
        {
            7,
            "Rohan",
            "Finance",
            92000,
            7.8,
            "2023-05-04",
            "Mumbai"
        },
        {
            8,
            "Diya",
            "Finance",
            76000,
            std::nullopt,
            "2024-06-30",
            "Pune"
        },
        {
            9,
            "Arjun",
            "Sales",
            105000,
            8.4,
            "2021-02-17",
            "Delhi"
        },
        {
            10,
            "Sara",
            "Sales",
            105000,
            8.7,
            "2022-03-28",
            "Hyderabad"
        },
        {
            11,
            "Advik",
            "Sales",
            88000,
            7.9,
            "2023-09-11",
            "Lucknow"
        },
        {
            12,
            "Tara",
            "Sales",
            69000,
            std::nullopt,
            "2024-01-05",
            std::nullopt
        },
        {
            13,
            "Neil",
            "Operations",
            99000,
            8.1,
            "2020-12-19",
            "Delhi"
        },
        {
            14,
            "Kiara",
            "Operations",
            91000,
            9.0,
            "2022-10-07",
            "Mumbai"
        },
        {
            15,
            "Yash",
            "Operations",
            91000,
            8.3,
            "2023-03-14",
            "Pune"
        },
        {
            16,
            "Naina",
            "Operations",
            72000,
            7.5,
            "2024-05-23",
            "Lucknow"
        }
    };
}


// -----------------------------------------------------------------------------
// Sort direction and sort field
// -----------------------------------------------------------------------------

enum class SortDirection {
    Ascending,
    Descending
};


enum class SortField {
    EmployeeName,
    Department,
    Salary,
    PerformanceScore,
    HireDate,
    EmployeeId
};


struct SortSpecification {
    SortField field;
    SortDirection direction;
    bool nullsLast = false;
};


// -----------------------------------------------------------------------------
// Generic comparison helpers
// -----------------------------------------------------------------------------

template <typename T>
int compareNonOptional(
    const T& first,
    const T& second
) {
    if (first < second) {
        return -1;
    }

    if (first > second) {
        return 1;
    }

    return 0;
}


int applyDirection(
    int comparison,
    SortDirection direction
) {
    if (direction == SortDirection::Ascending) {
        return comparison;
    }

    return -comparison;
}


int compareOptionalDouble(
    const std::optional<double>& first,
    const std::optional<double>& second,
    SortDirection direction,
    bool nullsLast
) {
    const bool firstNull = !first.has_value();
    const bool secondNull = !second.has_value();

    if (firstNull && secondNull) {
        return 0;
    }

    if (firstNull || secondNull) {
        if (nullsLast) {
            return firstNull ? 1 : -1;
        }

        return firstNull ? -1 : 1;
    }

    return applyDirection(
        compareNonOptional(*first, *second),
        direction
    );
}


int compareOptionalString(
    const std::optional<std::string>& first,
    const std::optional<std::string>& second,
    SortDirection direction,
    bool nullsLast
) {
    const bool firstNull = !first.has_value();
    const bool secondNull = !second.has_value();

    if (firstNull && secondNull) {
        return 0;
    }

    if (firstNull || secondNull) {
        if (nullsLast) {
            return firstNull ? 1 : -1;
        }

        return firstNull ? -1 : 1;
    }

    return applyDirection(
        compareNonOptional(*first, *second),
        direction
    );
}


// -----------------------------------------------------------------------------
// Extract a field and compare two employees
// -----------------------------------------------------------------------------

int compareBySpecification(
    const Employee& first,
    const Employee& second,
    const SortSpecification& specification
) {
    switch (specification.field) {
        case SortField::EmployeeName:
            return applyDirection(
                compareNonOptional(
                    first.employeeName,
                    second.employeeName
                ),
                specification.direction
            );

        case SortField::Department:
            return applyDirection(
                compareNonOptional(
                    first.department,
                    second.department
                ),
                specification.direction
            );

        case SortField::Salary:
            return applyDirection(
                compareNonOptional(
                    first.salary,
                    second.salary
                ),
                specification.direction
            );

        case SortField::PerformanceScore:
            return compareOptionalDouble(
                first.performanceScore,
                second.performanceScore,
                specification.direction,
                specification.nullsLast
            );

        case SortField::HireDate:
            return applyDirection(
                compareNonOptional(
                    first.hireDate,
                    second.hireDate
                ),
                specification.direction
            );

        case SortField::EmployeeId:
            return applyDirection(
                compareNonOptional(
                    first.employeeId,
                    second.employeeId
                ),
                specification.direction
            );
    }

    return 0;
}


bool employeeComesBefore(
    const Employee& first,
    const Employee& second,
    const std::vector<SortSpecification>& specifications
) {
    for (const auto& specification : specifications) {
        const int comparison = compareBySpecification(
            first,
            second,
            specification
        );

        if (comparison != 0) {
            return comparison < 0;
        }
    }

    return false;
}


// -----------------------------------------------------------------------------
// ORDER BY implementation
// -----------------------------------------------------------------------------

std::vector<Employee> orderBy(
    const std::vector<Employee>& input,
    const std::vector<SortSpecification>& specifications
) {
    std::vector<Employee> result = input;

    std::stable_sort(
        result.begin(),
        result.end(),
        [&](const Employee& first, const Employee& second) {
            return employeeComesBefore(
                first,
                second,
                specifications
            );
        }
    );

    return result;
}


// -----------------------------------------------------------------------------
// LIMIT and OFFSET
// -----------------------------------------------------------------------------

std::vector<Employee> applyLimit(
    const std::vector<Employee>& rows,
    std::size_t limit
) {
    const std::size_t resultSize =
        std::min(limit, rows.size());

    return std::vector<Employee>(
        rows.begin(),
        rows.begin() + static_cast<std::ptrdiff_t>(resultSize)
    );
}


std::vector<Employee> applyOffsetAndLimit(
    const std::vector<Employee>& rows,
    std::size_t offset,
    std::size_t limit
) {
    if (offset >= rows.size()) {
        return {};
    }

    const std::size_t remaining =
        rows.size() - offset;

    const std::size_t resultSize =
        std::min(limit, remaining);

    const auto start =
        rows.begin() + static_cast<std::ptrdiff_t>(offset);

    const auto finish =
        start + static_cast<std::ptrdiff_t>(resultSize);

    return std::vector<Employee>(start, finish);
}


// -----------------------------------------------------------------------------
// Filtering
// -----------------------------------------------------------------------------

std::vector<Employee> filterByDepartment(
    const std::vector<Employee>& rows,
    const std::string& department
) {
    std::vector<Employee> result;

    for (const auto& employee : rows) {
        if (employee.department == department) {
            result.push_back(employee);
        }
    }

    return result;
}


// -----------------------------------------------------------------------------
// Pagination validation
// -----------------------------------------------------------------------------

struct PageRequest {
    std::size_t page;
    std::size_t pageSize;
};


std::size_t calculateOffset(
    const PageRequest& request
) {
    if (request.page == 0) {
        throw std::invalid_argument(
            "Page number must be at least 1."
        );
    }

    if (request.pageSize == 0) {
        throw std::invalid_argument(
            "Page size must be at least 1."
        );
    }

    if (request.pageSize > 100) {
        throw std::invalid_argument(
            "Page size cannot exceed 100."
        );
    }

    const std::size_t pageIndex = request.page - 1;

    if (
        pageIndex >
        std::numeric_limits<std::size_t>::max() / request.pageSize
    ) {
        throw std::overflow_error(
            "Pagination offset would overflow."
        );
    }

    return pageIndex * request.pageSize;
}


// -----------------------------------------------------------------------------
// Stable keyset cursor
// -----------------------------------------------------------------------------

struct SalaryCursor {
    long long salary;
    int employeeId;
};


bool occursAfterCursor(
    const Employee& employee,
    const SalaryCursor& cursor
) {
    /*
    Stable ordering:

        salary DESC,
        employeeId ASC

    A row comes after the cursor if:

        salary < cursor.salary

    or:

        salary == cursor.salary
        AND employeeId > cursor.employeeId
    */
    return (
        employee.salary < cursor.salary
        ||
        (
            employee.salary == cursor.salary
            &&
            employee.employeeId > cursor.employeeId
        )
    );
}


std::vector<Employee> keysetPage(
    const std::vector<Employee>& orderedRows,
    const SalaryCursor& cursor,
    std::size_t limit
) {
    std::vector<Employee> candidates;

    for (const auto& employee : orderedRows) {
        if (occursAfterCursor(employee, cursor)) {
            candidates.push_back(employee);
        }
    }

    return applyLimit(candidates, limit);
}


// -----------------------------------------------------------------------------
// Safe dynamic sort mapping
// -----------------------------------------------------------------------------

SortField parseSortField(
    const std::string& requestedField
) {
    static const std::unordered_map<std::string, SortField> allowedFields = {
        {"name", SortField::EmployeeName},
        {"department", SortField::Department},
        {"salary", SortField::Salary},
        {"score", SortField::PerformanceScore},
        {"hireDate", SortField::HireDate},
        {"employeeId", SortField::EmployeeId}
    };

    const auto iterator =
        allowedFields.find(requestedField);

    if (iterator == allowedFields.end()) {
        throw std::invalid_argument(
            "Unsupported sort field: " + requestedField
        );
    }

    return iterator->second;
}


SortDirection parseSortDirection(
    const std::string& requestedDirection
) {
    if (requestedDirection == "ASC") {
        return SortDirection::Ascending;
    }

    if (requestedDirection == "DESC") {
        return SortDirection::Descending;
    }

    throw std::invalid_argument(
        "Unsupported sort direction: " + requestedDirection
    );
}


// -----------------------------------------------------------------------------
// SQL generation for an allow-listed sort
// -----------------------------------------------------------------------------

std::string sqlColumnName(
    SortField field
) {
    switch (field) {
        case SortField::EmployeeName:
            return "employee_name";

        case SortField::Department:
            return "department";

        case SortField::Salary:
            return "salary";

        case SortField::PerformanceScore:
            return "performance_score";

        case SortField::HireDate:
            return "hire_date";

        case SortField::EmployeeId:
            return "employee_id";
    }

    throw std::logic_error(
        "Unhandled sort field."
    );
}


std::string directionName(
    SortDirection direction
) {
    return direction == SortDirection::Ascending
        ? "ASC"
        : "DESC";
}


std::string buildSafeSql(
    const std::string& requestedField,
    const std::string& requestedDirection
) {
    const SortField field =
        parseSortField(requestedField);

    const SortDirection direction =
        parseSortDirection(requestedDirection);

    /*
    Only values obtained from fixed allow-lists are inserted into SQL syntax.
    LIMIT remains a parameter placeholder in a real database API.
    */
    std::ostringstream query;

    query
        << "SELECT employee_id, employee_name, salary\n"
        << "FROM employees\n"
        << "ORDER BY "
        << sqlColumnName(field)
        << " "
        << directionName(direction)
        << ", employee_id ASC\n"
        << "LIMIT ?;";

    return query.str();
}


// -----------------------------------------------------------------------------
// Top-N per department
// -----------------------------------------------------------------------------

std::vector<Employee> topNPerDepartment(
    const std::vector<Employee>& employees,
    std::size_t n
) {
    std::vector<std::string> departments;

    for (const auto& employee : employees) {
        if (
            std::find(
                departments.begin(),
                departments.end(),
                employee.department
            ) == departments.end()
        ) {
            departments.push_back(employee.department);
        }
    }

    std::vector<Employee> result;

    const std::vector<SortSpecification> salaryOrder = {
        {
            SortField::Salary,
            SortDirection::Descending,
            false
        },
        {
            SortField::EmployeeId,
            SortDirection::Ascending,
            false
        }
    };

    for (const auto& department : departments) {
        const auto filtered =
            filterByDepartment(
                employees,
                department
            );

        const auto ordered =
            orderBy(
                filtered,
                salaryOrder
            );

        const auto topRows =
            applyLimit(ordered, n);

        result.insert(
            result.end(),
            topRows.begin(),
            topRows.end()
        );
    }

    const std::vector<SortSpecification> finalOrder = {
        {
            SortField::Department,
            SortDirection::Ascending,
            false
        },
        {
            SortField::Salary,
            SortDirection::Descending,
            false
        },
        {
            SortField::EmployeeId,
            SortDirection::Ascending,
            false
        }
    };

    return orderBy(result, finalOrder);
}


// -----------------------------------------------------------------------------
// Demonstration: basic sorting
// -----------------------------------------------------------------------------

void demonstrateAscending(
    const std::vector<Employee>& employees
) {
    printHeader("1. ASCENDING ORDER");

    const std::vector<SortSpecification> specifications = {
        {
            SortField::Salary,
            SortDirection::Ascending,
            false
        }
    };

    const auto result =
        orderBy(employees, specifications);

    printEmployees(result);

    std::cout
        << "\nConceptual SQL:\n"
        << "ORDER BY salary ASC;\n";
}


void demonstrateDescending(
    const std::vector<Employee>& employees
) {
    printHeader("2. DESCENDING ORDER");

    const std::vector<SortSpecification> specifications = {
        {
            SortField::Salary,
            SortDirection::Descending,
            false
        }
    };

    const auto result =
        orderBy(employees, specifications);

    printEmployees(result);

    std::cout
        << "\nConceptual SQL:\n"
        << "ORDER BY salary DESC;\n";
}


// -----------------------------------------------------------------------------
// Demonstration: deterministic ordering
// -----------------------------------------------------------------------------

void demonstrateDeterministicOrdering(
    const std::vector<Employee>& employees
) {
    printHeader("3. DETERMINISTIC ORDERING");

    printSubheader("Non-unique ordering key");

    const auto salaryOnly = orderBy(
        employees,
        {
            {
                SortField::Salary,
                SortDirection::Descending,
                false
            }
        }
    );

    printEmployees(salaryOnly);

    printSubheader("Unique tie-breaker");

    const auto deterministic = orderBy(
        employees,
        {
            {
                SortField::Salary,
                SortDirection::Descending,
                false
            },
            {
                SortField::EmployeeId,
                SortDirection::Ascending,
                false
            }
        }
    );

    printEmployees(deterministic);

    std::cout
        << "\nThe employeeId key gives equal salaries an explicit order.\n";
}


// -----------------------------------------------------------------------------
// Demonstration: LIMIT and OFFSET
// -----------------------------------------------------------------------------

void demonstrateLimitAndOffset(
    const std::vector<Employee>& employees
) {
    printHeader("4. LIMIT AND OFFSET");

    const auto ordered = orderBy(
        employees,
        {
            {
                SortField::Salary,
                SortDirection::Descending,
                false
            },
            {
                SortField::EmployeeId,
                SortDirection::Ascending,
                false
            }
        }
    );

    printSubheader("LIMIT 5");

    printEmployees(
        applyLimit(ordered, 5)
    );

    printSubheader("LIMIT 5 OFFSET 5");

    printEmployees(
        applyOffsetAndLimit(
            ordered,
            5,
            5
        )
    );

    std::cout
        << "\nConceptual SQL:\n"
        << "ORDER BY salary DESC, employee_id ASC\n"
        << "LIMIT 5 OFFSET 5;\n";
}


// -----------------------------------------------------------------------------
// Demonstration: pagination
// -----------------------------------------------------------------------------

void demonstratePagination(
    const std::vector<Employee>& employees
) {
    printHeader("5. OFFSET-BASED PAGINATION");

    const auto ordered = orderBy(
        employees,
        {
            {
                SortField::Salary,
                SortDirection::Descending,
                false
            },
            {
                SortField::EmployeeId,
                SortDirection::Ascending,
                false
            }
        }
    );

    constexpr std::size_t pageSize = 4;

    for (std::size_t page = 1; page <= 5; ++page) {
        PageRequest request{
            page,
            pageSize
        };

        const std::size_t offset =
            calculateOffset(request);

        const auto pageRows =
            applyOffsetAndLimit(
                ordered,
                offset,
                pageSize
            );

        std::cout
            << "\nPage "
            << page
            << " | OFFSET "
            << offset
            << "\n";

        printEmployees(pageRows);
    }
}


// -----------------------------------------------------------------------------
// Demonstration: NULL ordering
// -----------------------------------------------------------------------------

void demonstrateNullOrdering(
    const std::vector<Employee>& employees
) {
    printHeader("6. EXPLICIT NULL ORDERING");

    const auto ordered = orderBy(
        employees,
        {
            {
                SortField::PerformanceScore,
                SortDirection::Ascending,
                true
            },
            {
                SortField::EmployeeId,
                SortDirection::Ascending,
                false
            }
        }
    );

    printEmployees(ordered);

    std::cout
        << "\nThe nullsLast flag explicitly places missing scores after "
        << "known scores.\n";
}


// -----------------------------------------------------------------------------
// Demonstration: filtered top-N
// -----------------------------------------------------------------------------

void demonstrateFilteredTopN(
    const std::vector<Employee>& employees
) {
    printHeader("7. FILTER + ORDER BY + LIMIT");

    const auto engineering =
        filterByDepartment(
            employees,
            "Engineering"
        );

    const auto ordered =
        orderBy(
            engineering,
            {
                {
                    SortField::Salary,
                    SortDirection::Descending,
                    false
                },
                {
                    SortField::EmployeeId,
                    SortDirection::Ascending,
                    false
                }
            }
        );

    const auto result =
        applyLimit(ordered, 3);

    printEmployees(result);

    std::cout
        << "\nConceptual SQL:\n"
        << "WHERE department = 'Engineering'\n"
        << "ORDER BY salary DESC, employee_id ASC\n"
        << "LIMIT 3;\n";
}


// -----------------------------------------------------------------------------
// Demonstration: top-N per group
// -----------------------------------------------------------------------------

void demonstrateTopNPerGroup(
    const std::vector<Employee>& employees
) {
    printHeader("8. TOP-N PER GROUP");

    const auto result =
        topNPerDepartment(employees, 2);

    printEmployees(result);

    std::cout
        << "\nA global LIMIT does not mean LIMIT per department.\n"
        << "SQL commonly solves this with ROW_NUMBER() OVER (PARTITION BY ...).\n";
}


// -----------------------------------------------------------------------------
// Demonstration: keyset pagination
// -----------------------------------------------------------------------------

void demonstrateKeysetPagination(
    const std::vector<Employee>& employees
) {
    printHeader("9. KEYSET PAGINATION");

    const std::vector<SortSpecification> stableOrder = {
        {
            SortField::Salary,
            SortDirection::Descending,
            false
        },
        {
            SortField::EmployeeId,
            SortDirection::Ascending,
            false
        }
    };

    const auto ordered =
        orderBy(
            employees,
            stableOrder
        );

    const auto firstPage =
        applyLimit(ordered, 5);

    printSubheader("First page");
    printEmployees(firstPage);

    if (firstPage.empty()) {
        return;
    }

    const Employee& lastRow =
        firstPage.back();

    SalaryCursor cursor{
        lastRow.salary,
        lastRow.employeeId
    };

    const auto secondPage =
        keysetPage(
            ordered,
            cursor,
            5
        );

    printSubheader("Second page using cursor");
    printEmployees(secondPage);

    std::cout
        << "\nCursor:\n"
        << "salary = "
        << cursor.salary
        << ", employeeId = "
        << cursor.employeeId
        << "\n";

    std::cout
        << "\nConceptual SQL:\n"
        << "WHERE salary < ?\n"
        << "   OR (salary = ? AND employee_id > ?)\n"
        << "ORDER BY salary DESC, employee_id ASC\n"
        << "LIMIT ?;\n";
}


// -----------------------------------------------------------------------------
// Demonstration: safe dynamic ordering
// -----------------------------------------------------------------------------

void demonstrateSafeDynamicOrdering(
    const std::vector<Employee>& employees
) {
    printHeader("10. SAFE DYNAMIC ORDERING");

    const std::string requestedField = "salary";
    const std::string requestedDirection = "DESC";

    try {
        const SortField field =
            parseSortField(requestedField);

        const SortDirection direction =
            parseSortDirection(requestedDirection);

        const auto ordered =
            orderBy(
                employees,
                {
                    {
                        field,
                        direction,
                        true
                    },
                    {
                        SortField::EmployeeId,
                        SortDirection::Ascending,
                        false
                    }
                }
            );

        printEmployees(
            applyLimit(ordered, 5)
        );

        std::cout
            << "\nSafe SQL generated from allow-listed identifiers:\n"
            << buildSafeSql(
                requestedField,
                requestedDirection
            )
            << "\n";
    } catch (const std::exception& error) {
        std::cerr
            << "Request rejected: "
            << error.what()
            << "\n";
    }

    try {
        std::cout
            << "\nTesting invalid sort field:\n";

        buildSafeSql(
            "salary; DROP TABLE employees",
            "DESC"
        );
    } catch (const std::exception& error) {
        std::cout
            << "Rejected: "
            << error.what()
            << "\n";
    }

    try {
        std::cout
            << "\nTesting invalid direction:\n";

        buildSafeSql(
            "salary",
            "DESC; DROP TABLE employees"
        );
    } catch (const std::exception& error) {
        std::cout
            << "Rejected: "
            << error.what()
            << "\n";
    }
}


// -----------------------------------------------------------------------------
// Pagination validation demonstration
// -----------------------------------------------------------------------------

void demonstrateValidation() {
    printHeader("11. PAGINATION VALIDATION");

    const std::vector<PageRequest> validRequests = {
        {1, 10},
        {2, 20},
        {5, 25}
    };

    for (const auto& request : validRequests) {
        try {
            const std::size_t offset =
                calculateOffset(request);

            std::cout
                << "page="
                << request.page
                << ", pageSize="
                << request.pageSize
                << ", offset="
                << offset
                << "\n";
        } catch (const std::exception& error) {
            std::cout
                << "Rejected: "
                << error.what()
                << "\n";
        }
    }

    const std::vector<PageRequest> invalidRequests = {
        {0, 10},
        {1, 0},
        {1, 101}
    };

    for (const auto& request : invalidRequests) {
        try {
            calculateOffset(request);

            std::cout
                << "Unexpectedly accepted invalid request.\n";
        } catch (const std::exception& error) {
            std::cout
                << "Rejected page="
                << request.page
                << ", pageSize="
                << request.pageSize
                << ": "
                << error.what()
                << "\n";
        }
    }
}


// -----------------------------------------------------------------------------
// Query behavior tests
// -----------------------------------------------------------------------------

void runTests(
    const std::vector<Employee>& employees
) {
    printHeader("12. AUTOMATED TESTS");

    const auto ordered =
        orderBy(
            employees,
            {
                {
                    SortField::Salary,
                    SortDirection::Descending,
                    false
                },
                {
                    SortField::EmployeeId,
                    SortDirection::Ascending,
                    false
                }
            }
        );

    if (ordered.empty()) {
        throw std::runtime_error(
            "Expected non-empty employee dataset."
        );
    }

    for (std::size_t index = 1;
         index < ordered.size();
         ++index) {
        const Employee& previous =
            ordered[index - 1];

        const Employee& current =
            ordered[index];

        const bool validOrder =
            previous.salary > current.salary
            ||
            (
                previous.salary == current.salary
                &&
                previous.employeeId < current.employeeId
            );

        if (!validOrder) {
            throw std::runtime_error(
                "Deterministic ordering test failed."
            );
        }
    }

    const auto limited =
        applyLimit(ordered, 5);

    if (limited.size() != 5) {
        throw std::runtime_error(
            "LIMIT test failed."
        );
    }

    const auto offsetPage =
        applyOffsetAndLimit(
            ordered,
            5,
            5
        );

    if (offsetPage.size() != 5) {
        throw std::runtime_error(
            "OFFSET/LIMIT test failed."
        );
    }

    const auto beyondEnd =
        applyOffsetAndLimit(
            ordered,
            1000,
            5
        );

    if (!beyondEnd.empty()) {
        throw std::runtime_error(
            "Large OFFSET test failed."
        );
    }

    std::cout
        << "All deterministic-ordering tests passed.\n"
        << "All LIMIT tests passed.\n"
        << "All OFFSET tests passed.\n";
}


// -----------------------------------------------------------------------------
// Performance experiment
// -----------------------------------------------------------------------------

std::vector<Employee> createLargeDataset(
    std::size_t count
) {
    std::vector<Employee> employees;
    employees.reserve(count);

    const std::vector<std::string> departments = {
        "Engineering",
        "Finance",
        "Sales",
        "Operations"
    };

    for (std::size_t index = 0; index < count; ++index) {
        const int employeeId =
            static_cast<int>(index + 1);

        const long long salary =
            50'000LL
            +
            static_cast<long long>(
                (index * 7919ULL) % 100'000ULL
            );

        employees.push_back(
            Employee{
                employeeId,
                "Employee" + std::to_string(employeeId),
                departments[index % departments.size()],
                salary,
                static_cast<double>(
                    5.0 + (index % 51) / 10.0
                ),
                "2026-01-01",
                "Delhi"
            }
        );
    }

    return employees;
}


void demonstratePerformance() {
    printHeader("13. PERFORMANCE CONSIDERATIONS");

    constexpr std::size_t datasetSize = 100'000;

    auto largeDataset =
        createLargeDataset(datasetSize);

    const std::vector<SortSpecification> specifications = {
        {
            SortField::Salary,
            SortDirection::Descending,
            false
        },
        {
            SortField::EmployeeId,
            SortDirection::Ascending,
            false
        }
    };

    const auto start =
        std::chrono::steady_clock::now();

    const auto ordered =
        orderBy(
            largeDataset,
            specifications
        );

    const auto finish =
        std::chrono::steady_clock::now();

    const std::chrono::duration<double, std::milli> elapsed =
        finish - start;

    std::cout
        << "Dataset size: "
        << datasetSize
        << " rows\n"
        << "In-memory ordering time: "
        << elapsed.count()
        << " ms\n";

    std::cout
        << "\nThe timing is environment-dependent.\n"
        << "A real SQL database may use indexes, partial sorting, top-N "
        << "strategies, statistics, and other optimizer techniques.\n";

    std::cout
        << "\nImportant distinction:\n"
        << "Application-side sorting and database-side ORDER BY are not "
        << "interchangeable at scale.\n";

    const auto topTen =
        applyLimit(ordered, 10);

    std::cout
        << "Top rows retained by application: "
        << topTen.size()
        << "\n";
}


// -----------------------------------------------------------------------------
// Query design explanation
// -----------------------------------------------------------------------------

void demonstrateIndustryScenario(
    const std::vector<Employee>& employees
) {
    printHeader("14. INDUSTRY-STYLE EMPLOYEE DIRECTORY");

    std::cout
        << R"(
Scenario:
An employee-management API provides a searchable directory.

The client can request:
    - a sort field
    - a sort direction
    - a page number
    - a page size

Business requirements:
    1. Sorting must be predictable.
    2. Page size must be bounded.
    3. User-provided sort names must be allow-listed.
    4. Ties must have a unique tie-breaker.
    5. Missing scores must have an explicit position.
    6. Sequential navigation should support keyset pagination.
    7. Database SQL should use parameterized values.
)";

    const std::string requestedField = "salary";
    const std::string requestedDirection = "DESC";

    const auto field =
        parseSortField(requestedField);

    const auto direction =
        parseSortDirection(requestedDirection);

    PageRequest pageRequest{
        1,
        5
    };

    const auto offset =
        calculateOffset(pageRequest);

    const auto ordered =
        orderBy(
            employees,
            {
                {
                    field,
                    direction,
                    true
                },
                {
                    SortField::EmployeeId,
                    SortDirection::Ascending,
                    false
                }
            }
        );

    const auto page =
        applyOffsetAndLimit(
            ordered,
            offset,
            pageRequest.pageSize
        );

    printSubheader("API response data");
    printEmployees(page);

    std::cout
        << "\nGenerated database query shape:\n"
        << buildSafeSql(
            requestedField,
            requestedDirection
        )
        << "\n";

    std::cout
        << "\nThe database driver should bind LIMIT as a value parameter "
        << "rather than interpolating untrusted text.\n";
}


// -----------------------------------------------------------------------------
// Trade-offs
// -----------------------------------------------------------------------------

void printTradeoffs() {
    printHeader("15. DESIGN TRADE-OFFS");

    std::cout
        << R"(
ORDER BY only on a non-unique column
    Advantage:
        Simple query.

    Limitation:
        Equal-key rows have no explicit relative ordering.

ORDER BY plus a unique key
    Advantage:
        Defines a deterministic total order for the dataset.

    Limitation:
        Adds another ordering criterion and may influence index design.

OFFSET pagination
    Advantage:
        Simple.
        Supports direct page-number navigation.

    Limitation:
        Large offsets may require substantial work.
        Dataset changes can shift page boundaries.

Keyset pagination
    Advantage:
        Efficient sequential navigation when supported by an appropriate index.
        Avoids progressively larger OFFSET values.

    Limitation:
        Requires a stable cursor.
        Random access to arbitrary page numbers is less natural.

Large page sizes
    Advantage:
        Fewer requests.

    Limitation:
        Larger database, memory, network, and serialization cost.

Indexes
    Advantage:
        Can support filtering and ordering efficiently.

    Limitation:
        Additional storage and write-maintenance cost.
)";
}


// -----------------------------------------------------------------------------
// SQL dialect notes
// -----------------------------------------------------------------------------

void printSqlDialectNotes() {
    printHeader("16. SQL DIALECT NOTES");

    std::cout
        << R"(
Common SQL syntax:

PostgreSQL / SQLite:
    ORDER BY salary DESC
    LIMIT 10 OFFSET 20

MySQL:
    ORDER BY salary DESC
    LIMIT 20, 10

SQL Server commonly uses:
    ORDER BY salary DESC
    OFFSET 20 ROWS
    FETCH NEXT 10 ROWS ONLY

Modern Oracle supports:
    ORDER BY salary DESC
    OFFSET 20 ROWS
    FETCH NEXT 10 ROWS ONLY

Exact syntax, optimizer behavior, NULL ordering defaults, and index behavior
must be verified for the target database system.
)";
}


// -----------------------------------------------------------------------------
// Security notes
// -----------------------------------------------------------------------------

void printSecurityNotes() {
    printHeader("17. SECURITY");

    std::cout
        << R"(
Dynamic ORDER BY clauses require special care.

Safe pattern:
    application value -> allow-list -> fixed SQL identifier

Unsafe pattern:
    raw HTTP parameter -> SQL string concatenation

The direction should also be restricted to:
    ASC
    DESC

Value parameters such as:
    department
    LIMIT
    OFFSET
    search terms

should be supplied through the database driver's parameter-binding mechanism
when supported.

A bounded page size also helps protect database and API resources from
unusually large requests.
)";
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        const auto employees =
            createEmployees();

        std::cout
            << "SQL Sorting & Limiting Case Study\n"
            << "C++17+ Employee Directory Query Service\n";

        demonstrateAscending(employees);
        demonstrateDescending(employees);
        demonstrateDeterministicOrdering(employees);
        demonstrateLimitAndOffset(employees);
        demonstratePagination(employees);
        demonstrateNullOrdering(employees);
        demonstrateFilteredTopN(employees);
        demonstrateTopNPerGroup(employees);
        demonstrateKeysetPagination(employees);
        demonstrateSafeDynamicOrdering(employees);
        demonstrateValidation();
        runTests(employees);
        demonstratePerformance();
        demonstrateIndustryScenario(employees);
        printTradeoffs();
        printSqlDialectNotes();
        printSecurityNotes();

        printHeader("18. STUDY CHECKLIST");

        const std::vector<std::string> checklist = {
            "ORDER BY defines the requested result ordering.",
            "ASC represents ascending order.",
            "DESC represents descending order.",
            "Multiple sort specifications create hierarchical ordering.",
            "LIMIT restricts the maximum number of returned rows.",
            "OFFSET skips rows before returning the limited page.",
            "LIMIT without ORDER BY does not identify a deterministic top-N set.",
            "A unique tie-breaker can create deterministic ordering.",
            "NULL placement should be explicit when it matters.",
            "OFFSET pagination is simple but can become expensive at large offsets.",
            "Keyset pagination uses ordered values as a continuation cursor.",
            "Dynamic sort fields should be validated through allow-lists.",
            "Page sizes should be validated and bounded.",
            "Indexes can support filtering and ordering.",
            "Production SQL should be evaluated using database query plans."
        };

        for (const auto& item : checklist) {
            std::cout
                << "[x] "
                << item
                << "\n";
        }

        std::cout
            << "\nProgram completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "\nFatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
