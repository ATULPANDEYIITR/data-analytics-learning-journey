import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Enterprise Business Analytics Model
 *
 * Java is used here to express explicit domain types, immutable records,
 * policy-style validation, service boundaries, and aggregation pipelines.
 *
 * Compile:
 *   javac BusinessAnalytics.java
 *
 * Run:
 *   java BusinessAnalytics
 */
public class BusinessAnalytics {

    enum OrderStatus {
        COMPLETED,
        CANCELLED,
        RETURNED,
        PENDING
    }

    enum CustomerSegment {
        CONSUMER,
        CORPORATE,
        SMALL_BUSINESS
    }

    record Product(
        String name,
        String category,
        BigDecimal price,
        BigDecimal cost
    ) {
        Product {
            Objects.requireNonNull(name);
            Objects.requireNonNull(category);
            Objects.requireNonNull(price);
            Objects.requireNonNull(cost);

            if (price.signum() <= 0) {
                throw new IllegalArgumentException("Price must be positive.");
            }

            if (cost.signum() < 0 || cost.compareTo(price) > 0) {
                throw new IllegalArgumentException(
                    "Cost must be non-negative and no greater than price."
                );
            }
        }
    }

    record OrderItem(
        Product product,
        int quantity
    ) {
        OrderItem {
            Objects.requireNonNull(product);

            if (quantity <= 0) {
                throw new IllegalArgumentException(
                    "Quantity must be positive."
                );
            }
        }

        BigDecimal revenue(BigDecimal discount) {
            return product.price()
                .multiply(BigDecimal.valueOf(quantity))
                .multiply(BigDecimal.ONE.subtract(discount));
        }

        BigDecimal profit(BigDecimal discount) {
            return product.price()
                .subtract(product.cost())
                .multiply(BigDecimal.valueOf(quantity))
                .subtract(
                    product.price()
                        .multiply(BigDecimal.valueOf(quantity))
                        .multiply(discount)
                );
        }
    }

    record Customer(
        int id,
        String name,
        CustomerSegment segment,
        String region
    ) {
        Customer {
            if (id <= 0 || name == null || name.isBlank()) {
                throw new IllegalArgumentException("Invalid customer.");
            }
        }
    }

    record SalesOrder(
        int id,
        Customer customer,
        LocalDate date,
        OrderStatus status,
        BigDecimal discount,
        List<OrderItem> items
    ) {
        SalesOrder {
            if (id <= 0) {
                throw new IllegalArgumentException("Order ID must be positive.");
            }

            Objects.requireNonNull(customer);
            Objects.requireNonNull(date);
            Objects.requireNonNull(status);
            Objects.requireNonNull(discount);

            if (discount.signum() < 0 ||
                discount.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException(
                    "Discount must be between 0 and 1."
                );
            }

            if (items == null || items.isEmpty()) {
                throw new IllegalArgumentException(
                    "An order requires line items."
                );
            }

            items = List.copyOf(items);
        }

        BigDecimal revenue() {
            return items.stream()
                .map(item -> item.revenue(discount))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        BigDecimal profit() {
            return items.stream()
                .map(item -> item.profit(discount))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }
    }

    record CustomerMetric(
        Customer customer,
        long orders,
        BigDecimal revenue,
        BigDecimal profit
    ) {}

    record CategoryMetric(
        String category,
        long units,
        BigDecimal revenue,
        BigDecimal profit
    ) {}

    record RegionMetric(
        String region,
        long orders,
        BigDecimal revenue,
        BigDecimal profit
    ) {}

    static class AnalyticsService {
        private final List<SalesOrder> orders;

        AnalyticsService(List<SalesOrder> orders) {
            this.orders = List.copyOf(orders);
        }

        private List<SalesOrder> completedOrders() {
            return orders.stream()
                .filter(order -> order.status() == OrderStatus.COMPLETED)
                .toList();
        }

        List<CustomerMetric> customerMetrics() {
            Map<Customer, List<SalesOrder>> grouped =
                completedOrders().stream()
                    .collect(Collectors.groupingBy(
                        SalesOrder::customer
                    ));

            return grouped.entrySet().stream()
                .map(entry -> new CustomerMetric(
                    entry.getKey(),
                    entry.getValue().size(),
                    scale(entry.getValue().stream()
                        .map(SalesOrder::revenue)
                        .reduce(BigDecimal.ZERO, BigDecimal::add)),
                    scale(entry.getValue().stream()
                        .map(SalesOrder::profit)
                        .reduce(BigDecimal.ZERO, BigDecimal::add))
                ))
                .sorted(
                    Comparator.comparing(
                        CustomerMetric::revenue
                    ).reversed()
                )
                .toList();
        }

        List<CategoryMetric> categoryMetrics() {
            Map<String, List<OrderItemWithDiscount>> grouped =
                new HashMap<>();

            for (SalesOrder order : completedOrders()) {
                for (OrderItem item : order.items()) {
                    grouped.computeIfAbsent(
                        item.product().category(),
                        ignored -> new ArrayList<>()
                    ).add(
                        new OrderItemWithDiscount(item, order.discount())
                    );
                }
            }

            return grouped.entrySet().stream()
                .map(entry -> {
                    long units = entry.getValue().stream()
                        .mapToLong(value -> value.item.quantity())
                        .sum();

                    BigDecimal revenue = entry.getValue().stream()
                        .map(value ->
                            value.item.revenue(value.discount))
                        .reduce(BigDecimal.ZERO, BigDecimal::add);

                    BigDecimal profit = entry.getValue().stream()
                        .map(value ->
                            value.item.profit(value.discount))
                        .reduce(BigDecimal.ZERO, BigDecimal::add);

                    return new CategoryMetric(
                        entry.getKey(),
                        units,
                        scale(revenue),
                        scale(profit)
                    );
                })
                .sorted(
                    Comparator.comparing(
                        CategoryMetric::revenue
                    ).reversed()
                )
                .toList();
        }

        List<RegionMetric> regionMetrics() {
            Map<String, List<SalesOrder>> grouped =
                completedOrders().stream()
                    .collect(Collectors.groupingBy(
                        order -> order.customer().region()
                    ));

            return grouped.entrySet().stream()
                .map(entry -> new RegionMetric(
                    entry.getKey(),
                    entry.getValue().size(),
                    scale(entry.getValue().stream()
                        .map(SalesOrder::revenue)
                        .reduce(BigDecimal.ZERO, BigDecimal::add)),
                    scale(entry.getValue().stream()
                        .map(SalesOrder::profit)
                        .reduce(BigDecimal.ZERO, BigDecimal::add))
                ))
                .sorted(
                    Comparator.comparing(
                        RegionMetric::revenue
                    ).reversed()
                )
                .toList();
        }

        Map<YearMonth, BigDecimal> monthlyRevenue() {
            return completedOrders().stream()
                .collect(Collectors.groupingBy(
                    order -> YearMonth.from(order.date()),
                    Collectors.reducing(
                        BigDecimal.ZERO,
                        SalesOrder::revenue,
                        BigDecimal::add
                    )
                ))
                .entrySet()
                .stream()
                .sorted(Map.Entry.comparingByKey())
                .collect(Collectors.toMap(
                    Map.Entry::getKey,
                    entry -> scale(entry.getValue()),
                    (left, right) -> left,
                    java.util.LinkedHashMap::new
                ));
        }

        double completionRate() {
            if (orders.isEmpty()) {
                return 0.0;
            }

            long completed = orders.stream()
                .filter(order -> order.status() == OrderStatus.COMPLETED)
                .count();

            return completed * 100.0 / orders.size();
        }

        Optional<CustomerMetric> highestValueCustomer() {
            return customerMetrics().stream().findFirst();
        }

        private record OrderItemWithDiscount(
            OrderItem item,
            BigDecimal discount
        ) {}
    }

    static BigDecimal scale(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    static void printDashboard(AnalyticsService service) {
        System.out.println("=== CUSTOMER ANALYTICS ===");

        service.customerMetrics().forEach(metric ->
            System.out.printf(
                "%s | %s | Orders=%d | Revenue=%s | Profit=%s%n",
                metric.customer().name(),
                metric.customer().segment(),
                metric.orders(),
                metric.revenue(),
                metric.profit()
            )
        );

        System.out.println("\n=== CATEGORY ANALYTICS ===");

        service.categoryMetrics().forEach(metric ->
            System.out.printf(
                "%s | Units=%d | Revenue=%s | Profit=%s%n",
                metric.category(),
                metric.units(),
                metric.revenue(),
                metric.profit()
            )
        );

        System.out.println("\n=== REGIONAL ANALYTICS ===");

        service.regionMetrics().forEach(metric ->
            System.out.printf(
                "%s | Orders=%d | Revenue=%s | Profit=%s%n",
                metric.region(),
                metric.orders(),
                metric.revenue(),
                metric.profit()
            )
        );

        System.out.println("\n=== MONTHLY REVENUE ===");

        service.monthlyRevenue().forEach(
            (month, revenue) ->
                System.out.printf(
                    "%s | Revenue=%s%n",
                    month,
                    revenue
                )
        );

        System.out.printf(
            "%nCompleted-order rate: %.2f%%%n",
            service.completionRate()
        );

        service.highestValueCustomer().ifPresent(customer ->
            System.out.printf(
                "Highest-value customer: %s (%s)%n",
                customer.customer().name(),
                customer.revenue()
            )
        );
    }

    public static void main(String[] args) {
        Product laptop = new Product(
            "Business Laptop",
            "Electronics",
            new BigDecimal("1200"),
            new BigDecimal("820")
        );

        Product monitor = new Product(
            "Security Monitor",
            "Electronics",
            new BigDecimal("650"),
            new BigDecimal("390")
        );

        Product desk = new Product(
            "Conference Desk",
            "Furniture",
            new BigDecimal("780"),
            new BigDecimal("470")
        );

        Product software = new Product(
            "Analytics Suite",
            "Software",
            new BigDecimal("900"),
            new BigDecimal("180")
        );

        Customer atlas = new Customer(
            1,
            "Atlas Consulting",
            CustomerSegment.CORPORATE,
            "North"
        );

        Customer bluePeak = new Customer(
            2,
            "BluePeak Retail",
            CustomerSegment.SMALL_BUSINESS,
            "South"
        );

        Customer delta = new Customer(
            3,
            "Delta Health",
            CustomerSegment.CORPORATE,
            "West"
        );

        Customer granite = new Customer(
            4,
            "Granite Labs",
            CustomerSegment.CORPORATE,
            "East"
        );

        List<SalesOrder> orders = List.of(
            new SalesOrder(
                1001,
                atlas,
                LocalDate.of(2026, 1, 5),
                OrderStatus.COMPLETED,
                new BigDecimal("0.05"),
                List.of(
                    new OrderItem(laptop, 3),
                    new OrderItem(monitor, 2)
                )
            ),
            new SalesOrder(
                1002,
                bluePeak,
                LocalDate.of(2026, 1, 18),
                OrderStatus.COMPLETED,
                new BigDecimal("0.10"),
                List.of(
                    new OrderItem(software, 2)
                )
            ),
            new SalesOrder(
                1003,
                delta,
                LocalDate.of(2026, 2, 8),
                OrderStatus.COMPLETED,
                new BigDecimal("0.15"),
                List.of(
                    new OrderItem(desk, 2)
                )
            ),
            new SalesOrder(
                1004,
                granite,
                LocalDate.of(2026, 3, 4),
                OrderStatus.COMPLETED,
                new BigDecimal("0.10"),
                List.of(
                    new OrderItem(laptop, 4)
                )
            ),
            new SalesOrder(
                1005,
                atlas,
                LocalDate.of(2026, 3, 20),
                OrderStatus.RETURNED,
                BigDecimal.ZERO,
                List.of(
                    new OrderItem(software, 1)
                )
            ),
            new SalesOrder(
                1006,
                bluePeak,
                LocalDate.of(2026, 4, 2),
                OrderStatus.PENDING,
                new BigDecimal("0.05"),
                List.of(
                    new OrderItem(monitor, 3)
                )
            )
        );

        AnalyticsService service = new AnalyticsService(orders);
        printDashboard(service);

        /*
         * EnumSet makes the supported status vocabulary explicit. It is useful
         * when a service needs to validate that downstream reports only include
         * recognized operational states.
         */
        EnumSet<OrderStatus> reportableStatuses =
            EnumSet.of(
                OrderStatus.COMPLETED,
                OrderStatus.RETURNED,
                OrderStatus.CANCELLED,
                OrderStatus.PENDING
            );

        System.out.println(
            "\nSupported operational statuses: " + reportableStatuses
        );
    }
}
