import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * SQL Data Quality: Enterprise Repository Model
 *
 * This Java 17 program models a data-quality service for an enterprise
 * ingestion platform. The domain types make quality rules explicit instead of
 * representing them as unrelated conditional print statements.
 *
 * The program demonstrates:
 * - duplicate business-identity detection
 * - missing-value validation
 * - parent-child referential validation
 * - domain constraints
 * - IQR-based monetary anomaly detection
 * - daily activity anomaly detection
 * - immutable report objects
 * - service-oriented rule composition
 */

public class DataQualityGovernance {

    enum Severity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum OrderStatus {
        PENDING,
        PAID,
        CANCELLED,
        REFUNDED
    }

    record Customer(
        long id,
        String name,
        String email,
        String phone
    ) {}

    record Order(
        long id,
        long customerId,
        double amount,
        LocalDate orderDate,
        OrderStatus status
    ) {}

    record QualityIssue(
        String rule,
        String entity,
        String key,
        Severity severity,
        String message
    ) {}

    record BusinessIdentity(
        String normalizedEmail,
        String normalizedName
    ) {}

    static final class QualityReport {
        private final List<QualityIssue> issues;

        QualityReport(List<QualityIssue> issues) {
            this.issues = List.copyOf(issues);
        }

        List<QualityIssue> issues() {
            return issues;
        }

        long countBySeverity(Severity severity) {
            return issues.stream()
                .filter(issue -> issue.severity() == severity)
                .count();
        }

        double qualityScore(int rowCount) {
            if (rowCount == 0) {
                return 100.0;
            }

            double penalty = issues.stream()
                .mapToDouble(issue -> switch (issue.severity()) {
                    case CRITICAL -> 5.0;
                    case HIGH -> 3.0;
                    case MEDIUM -> 1.0;
                    case LOW -> 0.5;
                })
                .sum();

            return Math.max(
                0.0,
                100.0 - (penalty / rowCount) * 20.0
            );
        }

        void print() {
            System.out.println("\n=== QUALITY REPORT ===");

            if (issues.isEmpty()) {
                System.out.println("No quality issues detected.");
                return;
            }

            issues.forEach(issue ->
                System.out.printf(
                    "[%s] %s %s:%s - %s%n",
                    issue.severity(),
                    issue.rule(),
                    issue.entity(),
                    issue.key(),
                    issue.message()
                )
            );
        }
    }

    interface QualityRule {
        List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        );

        String name();
    }

    static final class MissingCustomerRule implements QualityRule {
        @Override
        public String name() {
            return "customer completeness";
        }

        @Override
        public List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            for (Customer customer : customers) {
                if (isMissing(customer.name())) {
                    issues.add(new QualityIssue(
                        "missing_value",
                        "customers",
                        String.valueOf(customer.id()),
                        Severity.MEDIUM,
                        "Customer name is missing."
                    ));
                }

                if (isMissing(customer.email())) {
                    issues.add(new QualityIssue(
                        "missing_value",
                        "customers",
                        String.valueOf(customer.id()),
                        Severity.MEDIUM,
                        "Customer email is missing."
                    ));
                }

                if (isMissing(customer.phone())) {
                    issues.add(new QualityIssue(
                        "missing_value",
                        "customers",
                        String.valueOf(customer.id()),
                        Severity.MEDIUM,
                        "Customer phone is missing."
                    ));
                }
            }

            return issues;
        }
    }

    static final class DuplicateCustomerRule implements QualityRule {
        @Override
        public String name() {
            return "business duplicate detection";
        }

        @Override
        public List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            Map<BusinessIdentity, List<Long>> groups = new HashMap<>();

            for (Customer customer : customers) {
                if (isMissing(customer.email())) {
                    continue;
                }

                BusinessIdentity identity = new BusinessIdentity(
                    normalize(customer.email()),
                    normalize(customer.name())
                );

                groups
                    .computeIfAbsent(identity, ignored -> new ArrayList<>())
                    .add(customer.id());
            }

            List<QualityIssue> issues = new ArrayList<>();

            groups.forEach((identity, ids) -> {
                if (ids.size() > 1) {
                    issues.add(new QualityIssue(
                        "duplicate_customer",
                        "customers",
                        identity.normalizedEmail(),
                        Severity.HIGH,
                        "Business identity appears for IDs " + ids
                    ));
                }
            });

            return issues;
        }
    }

    static final class ReferentialIntegrityRule implements QualityRule {
        @Override
        public String name() {
            return "customer-order referential integrity";
        }

        @Override
        public List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            Set<Long> customerIds = customers.stream()
                .map(Customer::id)
                .collect(Collectors.toSet());

            List<QualityIssue> issues = new ArrayList<>();

            for (Order order : orders) {
                if (!customerIds.contains(order.customerId())) {
                    issues.add(new QualityIssue(
                        "orphan_order",
                        "orders",
                        String.valueOf(order.id()),
                        Severity.CRITICAL,
                        "No customer exists for customerId=" +
                            order.customerId()
                    ));
                }
            }

            return issues;
        }
    }

    static final class OrderDomainRule implements QualityRule {
        @Override
        public String name() {
            return "order domain validation";
        }

        @Override
        public List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            for (Order order : orders) {
                if (!Double.isFinite(order.amount()) ||
                    order.amount() <= 0.0) {

                    issues.add(new QualityIssue(
                        "invalid_amount",
                        "orders",
                        String.valueOf(order.id()),
                        Severity.HIGH,
                        "Amount must be finite and greater than zero."
                    ));
                }

                if (order.orderDate() == null) {
                    issues.add(new QualityIssue(
                        "missing_order_date",
                        "orders",
                        String.valueOf(order.id()),
                        Severity.HIGH,
                        "Order date is required."
                    ));
                }

                if (order.status() == null) {
                    issues.add(new QualityIssue(
                        "invalid_status",
                        "orders",
                        String.valueOf(order.id()),
                        Severity.HIGH,
                        "Order status is required."
                    ));
                }
            }

            return issues;
        }
    }

    static final class AmountAnomalyRule implements QualityRule {
        @Override
        public String name() {
            return "IQR amount anomaly detection";
        }

        @Override
        public List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            List<Double> amounts = orders.stream()
                .map(Order::amount)
                .filter(amount -> Double.isFinite(amount) && amount > 0)
                .sorted()
                .toList();

            if (amounts.size() < 4) {
                return List.of();
            }

            double q1 = percentile(amounts, 0.25);
            double q3 = percentile(amounts, 0.75);
            double upperFence = q3 + 1.5 * (q3 - q1);

            return orders.stream()
                .filter(order -> order.amount() > upperFence)
                .map(order -> new QualityIssue(
                    "amount_anomaly",
                    "orders",
                    String.valueOf(order.id()),
                    Severity.HIGH,
                    String.format(
                        "Amount %.2f exceeds upper fence %.2f.",
                        order.amount(),
                        upperFence
                    )
                ))
                .toList();
        }
    }

    static final class DailyVelocityRule implements QualityRule {
        @Override
        public String name() {
            return "daily customer activity anomaly detection";
        }

        @Override
        public List<QualityIssue> evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            Map<String, Long> counts = orders.stream()
                .filter(order ->
                    order.orderDate() != null &&
                    order.customerId() > 0
                )
                .collect(Collectors.groupingBy(
                    order -> order.customerId() + "|" + order.orderDate(),
                    Collectors.counting()
                ));

            if (counts.size() < 2) {
                return List.of();
            }

            double average = counts.values().stream()
                .mapToDouble(Long::doubleValue)
                .average()
                .orElse(0.0);

            double variance = counts.values().stream()
                .mapToDouble(Long::doubleValue)
                .map(value -> Math.pow(value - average, 2))
                .average()
                .orElse(0.0);

            double threshold = average + 3.0 * Math.sqrt(variance);

            return counts.entrySet().stream()
                .filter(entry -> entry.getValue() > threshold)
                .map(entry -> new QualityIssue(
                    "order_velocity_anomaly",
                    "orders",
                    entry.getKey(),
                    Severity.HIGH,
                    String.format(
                        "%d daily orders exceed threshold %.2f.",
                        entry.getValue(),
                        threshold
                    )
                ))
                .toList();
        }
    }

    static final class DataQualityService {
        private final List<QualityRule> rules;

        DataQualityService(List<QualityRule> rules) {
            this.rules = List.copyOf(rules);
        }

        QualityReport evaluate(
            List<Customer> customers,
            List<Order> orders
        ) {
            List<QualityIssue> allIssues = new ArrayList<>();

            for (QualityRule rule : rules) {
                System.out.println("Evaluating: " + rule.name());

                List<QualityIssue> ruleIssues =
                    rule.evaluate(customers, orders);

                allIssues.addAll(ruleIssues);

                System.out.println(
                    "  Violations: " + ruleIssues.size()
                );
            }

            return new QualityReport(allIssues);
        }
    }

    static String normalize(String value) {
        if (value == null) {
            return "";
        }

        return value.trim().toLowerCase();
    }

    static boolean isMissing(String value) {
        return value == null || value.trim().isEmpty();
    }

    static double percentile(List<Double> sortedValues, double fraction) {
        if (sortedValues.isEmpty()) {
            throw new IllegalArgumentException(
                "Cannot calculate percentile on empty data."
            );
        }

        double position =
            (sortedValues.size() - 1) * fraction;

        int lower = (int) Math.floor(position);
        int upper = (int) Math.ceil(position);

        if (lower == upper) {
            return sortedValues.get(lower);
        }

        double weight = position - lower;

        return sortedValues.get(lower) +
            (sortedValues.get(upper) - sortedValues.get(lower)) * weight;
    }

    static List<Customer> createCustomers() {
        return List.of(
            new Customer(1, "Asha Verma", "asha@example.com", "9876500001"),
            new Customer(2, "Ravi Kumar", "ravi@example.com", "9876500002"),
            new Customer(3, "Ravi Kumar", "ravi@example.com", "9876500002"),
            new Customer(4, "Meera Shah", null, "9876500004"),
            new Customer(5, "", "meera2@example.com", null),
            new Customer(6, "Kabir Singh", "kabir@example.com", "9876500006"),
            new Customer(7, "Nisha Rao", "nisha@example.com", "9876500007"),
            new Customer(8, "Omar Khan", "omarkhan@example.com", "9876500008")
        );
    }

    static List<Order> createOrders() {
        return List.of(
            new Order(101, 1, 120.50, LocalDate.of(2026, 10, 1),
                OrderStatus.PAID),
            new Order(102, 2, 80.00, LocalDate.of(2026, 10, 1),
                OrderStatus.PAID),
            new Order(103, 2, 75.00, LocalDate.of(2026, 10, 1),
                OrderStatus.PAID),
            new Order(104, 2, 70.00, LocalDate.of(2026, 10, 1),
                OrderStatus.PAID),
            new Order(105, 2, 65.00, LocalDate.of(2026, 10, 1),
                OrderStatus.PAID),
            new Order(106, 2, 55.00, LocalDate.of(2026, 10, 1),
                OrderStatus.PAID),
            new Order(107, 6, 150.00, LocalDate.of(2026, 10, 2),
                OrderStatus.PENDING),
            new Order(108, 7, 210.00, LocalDate.of(2026, 10, 2),
                OrderStatus.PAID),
            new Order(109, 8, 9999.00, LocalDate.of(2026, 10, 2),
                OrderStatus.PAID),
            new Order(110, 1, 95.00, LocalDate.of(2026, 10, 3),
                OrderStatus.CANCELLED),
            new Order(111, 999, 45.00, LocalDate.of(2026, 10, 3),
                OrderStatus.PAID)
        );
    }

    public static void main(String[] args) {
        List<Customer> customers =
            Collections.unmodifiableList(createCustomers());

        List<Order> orders =
            Collections.unmodifiableList(createOrders());

        List<QualityRule> rules = List.of(
            new MissingCustomerRule(),
            new DuplicateCustomerRule(),
            new ReferentialIntegrityRule(),
            new OrderDomainRule(),
            new AmountAnomalyRule(),
            new DailyVelocityRule()
        );

        DataQualityService service =
            new DataQualityService(rules);

        QualityReport report =
            service.evaluate(customers, orders);

        report.print();

        System.out.println("\n=== QUALITY METRICS ===");
        System.out.println(
            "Critical issues: " +
            report.countBySeverity(Severity.CRITICAL)
        );
        System.out.println(
            "High issues: " +
            report.countBySeverity(Severity.HIGH)
        );
        System.out.println(
            "Medium issues: " +
            report.countBySeverity(Severity.MEDIUM)
        );
        System.out.printf(
            "Quality score: %.2f/100%n",
            report.qualityScore(customers.size() + orders.size())
        );

        System.out.println("\n=== GOVERNANCE INTERPRETATION ===");
        System.out.println(
            "A duplicate is a business-identity problem, not necessarily "
            + "a primary-key violation."
        );
        System.out.println(
            "A missing value is evaluated against field semantics rather "
            + "than simply counting SQL NULL values."
        );
        System.out.println(
            "Referential integrity verifies that child orders have valid "
            + "customer parents."
        );
        System.out.println(
            "An anomaly is statistically unusual data and is therefore "
            + "different from a deterministic constraint violation."
        );
    }
}
