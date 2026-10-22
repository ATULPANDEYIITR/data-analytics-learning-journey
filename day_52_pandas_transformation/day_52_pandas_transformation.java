import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

public class PandasTransformationEnterpriseModel {

    enum Status {
        COMPLETED,
        PENDING,
        CANCELLED
    }

    enum Priority {
        HIGH,
        MEDIUM,
        LOW
    }

    record Order(
        int id,
        String customer,
        String region,
        String product,
        int quantity,
        double unitPrice,
        Status status
    ) {
        Order {
            if (id <= 0) {
                throw new IllegalArgumentException("Order ID must be positive");
            }
            if (customer == null || customer.isBlank()) {
                throw new IllegalArgumentException("Customer is required");
            }
            if (region == null || region.isBlank()) {
                throw new IllegalArgumentException("Region is required");
            }
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive");
            }
            if (unitPrice < 0) {
                throw new IllegalArgumentException("Unit price cannot be negative");
            }
            Objects.requireNonNull(status, "Status is required");
        }
    }

    record TransformedOrder(
        Order source,
        String regionCode,
        double grossAmount,
        double discountRate,
        double netAmount,
        Priority priority
    ) {}

    interface TransformationRule<T, R> {
        R apply(T value);
    }

    static final class TransformationService {

        private final Map<String, String> regionCodes = Map.of(
            "North", "N",
            "South", "S",
            "East", "E",
            "West", "W"
        );

        TransformedOrder transform(Order order) {
            Objects.requireNonNull(order);

            double gross = order.quantity() * order.unitPrice();

            double discount =
                gross >= 100000
                    ? 0.10
                    : gross >= 50000
                        ? 0.05
                        : 0.0;

            double net = gross * (1.0 - discount);

            Priority priority =
                net >= 100000
                    ? Priority.HIGH
                    : net >= 30000
                        ? Priority.MEDIUM
                        : Priority.LOW;

            String regionCode =
                regionCodes.getOrDefault(order.region(), "UNKNOWN");

            return new TransformedOrder(
                order,
                regionCode,
                gross,
                discount,
                net,
                priority
            );
        }

        List<TransformedOrder> transformAll(List<Order> orders) {
            validateUniqueIds(orders);

            return orders.stream()
                .map(this::transform)
                .toList();
        }

        List<TransformedOrder> filterActive(
            List<TransformedOrder> orders
        ) {
            return orders.stream()
                .filter(order ->
                    order.source().status() != Status.CANCELLED
                    && order.netAmount() >= 30000
                )
                .sorted(
                    Comparator
                        .comparing(TransformedOrder::priority)
                        .thenComparing(
                            TransformedOrder::netAmount,
                            Comparator.reverseOrder()
                        )
                )
                .toList();
        }

        Map<String, Double> completedRevenue(
            List<TransformedOrder> orders
        ) {
            return orders.stream()
                .filter(order ->
                    order.source().status() == Status.COMPLETED
                )
                .collect(
                    Collectors.groupingBy(
                        order -> order.source().region(),
                        Collectors.summingDouble(
                            TransformedOrder::netAmount
                        )
                    )
                );
        }

        private void validateUniqueIds(List<Order> orders) {
            Set<Integer> ids = new HashSet<>();

            for (Order order : orders) {
                if (!ids.add(order.id())) {
                    throw new IllegalArgumentException(
                        "Duplicate order ID: " + order.id()
                    );
                }
            }
        }
    }

    static final class ReportFormatter {

        void printOrders(List<TransformedOrder> orders) {
            System.out.printf(
                "%-6s %-10s %-14s %-12s %-12s %-10s%n",
                "ID",
                "Region",
                "Product",
                "Status",
                "Net",
                "Priority"
            );

            System.out.println("-".repeat(70));

            for (TransformedOrder order : orders) {
                System.out.printf(
                    "%-6d %-10s %-14s %-12s %-12.2f %-10s%n",
                    order.source().id(),
                    order.regionCode(),
                    order.source().product(),
                    order.source().status(),
                    order.netAmount(),
                    order.priority()
                );
            }
        }

        void printRevenue(Map<String, Double> revenue) {
            revenue.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
                .forEach(entry ->
                    System.out.printf(
                        "%s: %.2f%n",
                        entry.getKey(),
                        entry.getValue()
                    )
                );
        }
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(
                1001, "Asha", "North", "Laptop",
                2, 75000, Status.COMPLETED
            ),
            new Order(
                1002, "Ravi", "South", "Monitor",
                3, 18000, Status.COMPLETED
            ),
            new Order(
                1003, "Meera", "West", "Keyboard",
                5, 3500, Status.PENDING
            ),
            new Order(
                1004, "Kabir", "East", "Laptop",
                1, 82000, Status.CANCELLED
            ),
            new Order(
                1005, "Asha", "North", "Mouse",
                4, 1500, Status.COMPLETED
            ),
            new Order(
                1006, "Ravi", "South", "Laptop",
                2, 78000, Status.COMPLETED
            ),
            new Order(
                1007, "Meera", "West", "Monitor",
                2, 19500, Status.PENDING
            )
        );

        TransformationService service =
            new TransformationService();

        ReportFormatter formatter =
            new ReportFormatter();

        List<TransformedOrder> transformed =
            service.transformAll(orders);

        List<TransformedOrder> active =
            service.filterActive(transformed);

        System.out.println("TRANSFORMED ORDERS");
        formatter.printOrders(transformed);

        System.out.println("\nFILTERED AND SORTED ORDERS");
        formatter.printOrders(active);

        System.out.println("\nCOMPLETED REVENUE BY REGION");
        formatter.printRevenue(
            service.completedRevenue(transformed)
        );

        // Java records provide immutable transformed results. This reduces
        // accidental mutation after a transformation has been applied.

        try {
            new Order(
                2001,
                "Invalid Customer",
                "North",
                "Laptop",
                0,
                50000,
                Status.PENDING
            );
        } catch (IllegalArgumentException ex) {
            System.out.println(
                "\nValidation correctly rejected invalid data: "
                + ex.getMessage()
            );
        }
    }
}
