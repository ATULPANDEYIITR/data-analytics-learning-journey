import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class PandasFundamentals {

    enum Department {
        ENGINEERING,
        SALES,
        FINANCE
    }

    record Employee(
            String name,
            Department department,
            double salary,
            double performance,
            boolean active
    ) {
        Employee {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Employee name is required.");
            }

            Objects.requireNonNull(department, "Department is required.");

            if (salary < 0) {
                throw new IllegalArgumentException("Salary cannot be negative.");
            }

            if (performance < 0 || performance > 5) {
                throw new IllegalArgumentException(
                        "Performance must be between 0 and 5."
                );
            }
        }

        double bonus() {
            return salary * performance / 100.0;
        }

        double totalCompensation() {
            return salary + bonus();
        }
    }

    interface SelectionPolicy {
        boolean accepts(Employee employee);
    }

    static final class EmployeeTable {
        private final List<Employee> employees;

        EmployeeTable(List<Employee> employees) {
            if (employees == null || employees.isEmpty()) {
                throw new IllegalArgumentException(
                        "Employee table cannot be empty."
                );
            }

            this.employees = List.copyOf(employees);
        }

        List<Employee> selectColumnsAsDomainObjects() {
            /*
             * Java does not have a direct equivalent of a Pandas column
             * projection. Streams provide a type-safe way to transform
             * a selected field into another collection.
             */
            return employees.stream()
                    .map(employee -> new Employee(
                            employee.name(),
                            employee.department(),
                            employee.salary(),
                            employee.performance(),
                            employee.active()
                    ))
                    .toList();
        }

        List<Employee> filter(SelectionPolicy policy) {
            Objects.requireNonNull(policy, "Selection policy is required.");

            return employees.stream()
                    .filter(policy::accepts)
                    .toList();
        }

        List<Employee> sortedBySalaryDescending() {
            return employees.stream()
                    .sorted(
                            Comparator.comparingDouble(Employee::salary)
                                    .reversed()
                    )
                    .toList();
        }

        Map<Department, Double> averageSalaryByDepartment() {
            return employees.stream()
                    .collect(Collectors.groupingBy(
                            Employee::department,
                            () -> new EnumMap<>(Department.class),
                            Collectors.averagingDouble(Employee::salary)
                    ));
        }

        List<Employee> rows() {
            return employees;
        }
    }

    private static void print(String title, List<Employee> employees) {
        System.out.println("\n" + title);

        for (Employee employee : employees) {
            System.out.printf(
                    "%-10s %-14s salary=%9.2f performance=%.1f active=%s%n",
                    employee.name(),
                    employee.department(),
                    employee.salary(),
                    employee.performance(),
                    employee.active()
            );
        }
    }

    public static void main(String[] args) {
        List<Employee> source = new ArrayList<>();

        source.add(new Employee(
                "Asha", Department.ENGINEERING, 95000, 4.5, true
        ));
        source.add(new Employee(
                "Ravi", Department.SALES, 72000, 3.8, true
        ));
        source.add(new Employee(
                "Meera", Department.ENGINEERING, 105000, 4.8, true
        ));
        source.add(new Employee(
                "John", Department.SALES, 68000, 3.2, false
        ));
        source.add(new Employee(
                "Fatima", Department.FINANCE, 88000, 4.1, true
        ));

        EmployeeTable table = new EmployeeTable(source);

        print("Original rows", table.rows());

        List<Employee> highPerformers = table.filter(
                employee ->
                        employee.active()
                                && employee.performance() >= 4.0
        );

        print("Filtered active high performers", highPerformers);

        List<Employee> engineering = table.filter(
                employee -> employee.department() == Department.ENGINEERING
        );

        print("Engineering rows", engineering);

        print(
                "Salary descending",
                table.sortedBySalaryDescending()
        );

        System.out.println("\nAverage salary by department:");

        table.averageSalaryByDepartment()
                .forEach(
                        (department, average) ->
                                System.out.printf(
                                        "%-14s %.2f%n",
                                        department,
                                        average
                                )
                );

        System.out.println("\nDerived compensation:");

        table.rows().stream()
                .map(employee -> String.format(
                        "%-10s bonus=%9.2f total=%10.2f",
                        employee.name(),
                        employee.bonus(),
                        employee.totalCompensation()
                ))
                .forEach(System.out::println);

        try {
            new Employee(
                    "Invalid",
                    Department.FINANCE,
                    -5000,
                    4.0,
                    true
            );
        } catch (IllegalArgumentException error) {
            System.out.println(
                    "\nValidation failure: " + error.getMessage()
            );
        }

        /*
         * Records make row data immutable.
         * Enums constrain department values.
         * Streams express filtering, sorting, projection, and grouping
         * without exposing mutable collection internals.
         */
    }
}
