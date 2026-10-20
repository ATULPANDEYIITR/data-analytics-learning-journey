#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

struct Employee {
    std::string name;
    std::string department;
    double salary;
    double performance;
    bool active;
};

class EmployeeTable {
private:
    std::vector<Employee> rows;

    static void validate(const Employee& employee) {
        if (employee.name.empty()) {
            throw std::invalid_argument("Employee name cannot be empty.");
        }

        if (employee.department.empty()) {
            throw std::invalid_argument("Department cannot be empty.");
        }

        if (employee.salary < 0) {
            throw std::invalid_argument("Salary cannot be negative.");
        }

        if (employee.performance < 0 || employee.performance > 5) {
            throw std::invalid_argument(
                "Performance must be between 0 and 5."
            );
        }
    }

public:
    void add(Employee employee) {
        validate(employee);
        rows.push_back(std::move(employee));
    }

    const std::vector<Employee>& data() const {
        return rows;
    }

    std::vector<Employee> filter(
        const std::function<bool(const Employee&)>& predicate
    ) const {
        std::vector<Employee> result;

        for (const auto& employee : rows) {
            if (predicate(employee)) {
                result.push_back(employee);
            }
        }

        return result;
    }

    std::vector<Employee> selectActiveHighPerformers() const {
        return filter([](const Employee& employee) {
            return employee.active && employee.performance >= 4.0;
        });
    }

    std::map<std::string, double> averageSalaryByDepartment() const {
        std::map<std::string, double> totals;
        std::map<std::string, std::size_t> counts;

        for (const auto& employee : rows) {
            totals[employee.department] += employee.salary;
            counts[employee.department]++;
        }

        std::map<std::string, double> averages;

        for (const auto& [department, total] : totals) {
            averages[department] = total / counts[department];
        }

        return averages;
    }

    void sortBySalaryDescending() {
        std::sort(
            rows.begin(),
            rows.end(),
            [](const Employee& a, const Employee& b) {
                return a.salary > b.salary;
            }
        );
    }
};

void printEmployees(const std::vector<Employee>& employees) {
    std::cout << std::left
              << std::setw(12) << "Employee"
              << std::setw(16) << "Department"
              << std::setw(12) << "Salary"
              << std::setw(12) << "Performance"
              << "Active\n";

    std::cout << std::string(65, '-') << '\n';

    for (const auto& employee : employees) {
        std::cout << std::left
                  << std::setw(12) << employee.name
                  << std::setw(16) << employee.department
                  << std::setw(12) << std::fixed
                  << std::setprecision(2) << employee.salary
                  << std::setw(12) << employee.performance
                  << (employee.active ? "yes" : "no")
                  << '\n';
    }
}

int main() {
    try {
        EmployeeTable table;

        table.add({"Asha", "Engineering", 95000, 4.5, true});
        table.add({"Ravi", "Sales", 72000, 3.8, true});
        table.add({"Meera", "Engineering", 105000, 4.8, true});
        table.add({"John", "Sales", 68000, 3.2, false});
        table.add({"Fatima", "Finance", 88000, 4.1, true});

        std::cout << "All rows\n";
        printEmployees(table.data());

        std::cout << "\nSelected rows\n";
        printEmployees(table.selectActiveHighPerformers());

        std::cout << "\nAverage salary by department\n";
        const auto averages = table.averageSalaryByDepartment();

        for (const auto& [department, average] : averages) {
            std::cout << std::left
                      << std::setw(16) << department
                      << std::fixed
                      << std::setprecision(2)
                      << average << '\n';
        }

        table.sortBySalaryDescending();

        std::cout << "\nSorted rows\n";
        printEmployees(table.data());

        try {
            table.add({"Invalid", "Finance", -1000, 4.0, true});
        } catch (const std::invalid_argument& error) {
            std::cout << "\nValidation failure: "
                      << error.what() << '\n';
        }

        /*
         * Filtering is O(n), grouping is O(n log k) because std::map
         * maintains ordered department keys, and sorting is O(n log n).
         * Keeping rows in a vector gives compact storage and cache-friendly
         * iteration, while the map is appropriate for grouped aggregation.
         */
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
