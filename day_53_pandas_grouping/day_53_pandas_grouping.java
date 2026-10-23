import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Java 17 enterprise-style implementation of grouped analytical workflows.
 *
 * The domain models:
 * - transactional records
 * - grouped aggregation
 * - transform-like group metrics
 * - pivot-style summaries
 * - crosstab frequency analysis
 * - validation and business invariants
 */

public class PandasGroupingEnterprise {

    enum Region {
        NORTH, SOUTH, EAST, WEST
    }

    enum Department {
        CLOUD, SECURITY, DATA
    }

    enum Channel {
        ONLINE, PARTNER, DIRECT
    }

    enum Segment {
        ENTERPRISE, SMB
    }

    record Order(
        int id,
        String orderDate,
        Region region,
        Department department,
        Channel channel,
        String product,
        Segment segment,
        int units,
        double unitPrice,
        double discount,
        boolean returned
    ) {
        Order {
            if (id <= 0) {
                throw new IllegalArgumentException("Order ID must be positive.");
            }
            Objects.requireNonNull(region);
            Objects.requireNonNull(department);
            Objects.requireNonNull(channel);
            Objects.requireNonNull(product);
            Objects.requireNonNull(segment);

            if (units <= 0) {
                throw new IllegalArgumentException("Units must be positive.");
            }

            if (unitPrice < 0) {
                throw new IllegalArgumentException("Unit price cannot be negative.");
            }

            if (discount < 0 || discount > 1) {
                throw new IllegalArgumentException(
                    "Discount must be between zero and one."
                );
            }
        }

        double revenue() {
            return units * unitPrice;
        }

        double netRevenue() {
            return revenue() * (1 - discount);
        }

        boolean highValue(double threshold) {
            return netRevenue() >= threshold;
        }
    }

    record RegionMetrics(
        long orders,
        long units,
        double netRevenue,
        long returnedOrders
    ) {}

    record DepartmentMetrics(
        long orders,
        double averageRevenue,
        double minimumRevenue,
        double maximumRevenue
    ) {}

    record RowTransform(
        int orderId,
        Region region,
        double netRevenue,
        double regionRevenue,
        double regionShare
    ) {}

    record PivotCell(
        Region region,
        Channel channel,
        double revenue
    ) {}

    static final class AnalyticsService {
        private final List<Order> orders;

        AnalyticsService(List<Order> orders) {
            this.orders = List.copyOf(orders);
            validateUniqueIds();
        }

        Map<Region, RegionMetrics> aggregateByRegion() {
            Map<Region, List<Order>> grouped =
                orders.stream()
                    .collect(Collectors.groupingBy(
                        Order::region,
                        () -> new EnumMap<>(Region.class),
                        Collectors.toList()
                    ));

            Map<Region, RegionMetrics> result =
                new EnumMap<>(Region.class);

            for (var entry : grouped.entrySet()) {
                List<Order> group = entry.getValue();

                long units = group.stream()
                    .mapToLong(Order::units)
                    .sum();

                double revenue = group.stream()
                    .mapToDouble(Order::netRevenue)
                    .sum();

                long returned = group.stream()
                    .filter(Order::returned)
                    .count();

                result.put(
                    entry.getKey(),
                    new RegionMetrics(
                        group.size(),
                        units,
                        revenue,
                        returned
                    )
                );
            }

            return result;
        }

        Map<Department, DepartmentMetrics> aggregateByDepartment() {
            Map<Department, List<Order>> grouped =
                orders.stream()
                    .collect(Collectors.groupingBy(
                        Order::department,
                        () -> new EnumMap<>(Department.class),
                        Collectors.toList()
                    ));

            Map<Department, DepartmentMetrics> result =
                new EnumMap<>(Department.class);

            for (var entry : grouped.entrySet()) {
                List<Order> group = entry.getValue();

                double[] revenues = group.stream()
                    .mapToDouble(Order::netRevenue)
                    .toArray();

                double total =
                    java.util.Arrays.stream(revenues).sum();

                double minimum =
                    java.util.Arrays.stream(revenues).min().orElse(0);

                double maximum =
                    java.util.Arrays.stream(revenues).max().orElse(0);

                result.put(
                    entry.getKey(),
                    new DepartmentMetrics(
                        group.size(),
                        total / group.size(),
                        minimum,
                        maximum
                    )
                );
            }

            return result;
        }

        List<RowTransform> transformRegionMetrics() {
            Map<Region, Double> regionTotals =
                orders.stream()
                    .collect(Collectors.groupingBy(
                        Order::region,
                        () -> new EnumMap<>(Region.class),
                        Collectors.summingDouble(Order::netRevenue)
                    ));

            return orders.stream()
                .map(order -> {
                    double total = regionTotals.get(order.region());

                    if (total <= 0) {
                        throw new IllegalStateException(
                            "Cannot calculate a group share from zero revenue."
                        );
                    }

                    return new RowTransform(
                        order.id(),
                        order.region(),
                        order.netRevenue(),
                        total,
                        order.netRevenue() / total
                    );
                })
                .toList();
        }

        Map<Region, Map<Channel, Double>> pivotRevenue() {
            Map<Region, Map<Channel, Double>> result =
                new EnumMap<>(Region.class);

            for (Order order : orders) {
                result
                    .computeIfAbsent(
                        order.region(),
                        ignored -> new EnumMap<>(Channel.class)
                    )
                    .merge(
                        order.channel(),
                        order.netRevenue(),
                        Double::sum
                    );
            }

            return result;
        }

        Map<Department, Map<Channel, Long>> crosstab() {
            Map<Department, Map<Channel, Long>> result =
                new EnumMap<>(Department.class);

            for (Order order : orders) {
                result
                    .computeIfAbsent(
                        order.department(),
                        ignored -> new EnumMap<>(Channel.class)
                    )
                    .merge(
                        order.channel(),
                        1L,
                        Long::sum
                    );
            }

            return result;
        }

        List<Order> highValueOrders(double threshold) {
            if (threshold < 0) {
                throw new IllegalArgumentException(
                    "Threshold cannot be negative."
                );
            }

            return orders.stream()
                .filter(order -> order.highValue(threshold))
                .toList();
        }

        void validateInvariants() {
            double sourceTotal = orders.stream()
                .mapToDouble(Order::netRevenue)
                .sum();

            double groupedTotal = aggregateByRegion()
                .values()
                .stream()
                .mapToDouble(RegionMetrics::netRevenue)
                .sum();

            if (Math.abs(sourceTotal - groupedTotal) > 0.000001) {
                throw new IllegalStateException(
                    "Grouped revenue does not reconcile."
                );
            }

            Map<Region, Double> shares = transformRegionMetrics()
                .stream()
                .collect(Collectors.groupingBy(
                    RowTransform::region,
                    Collectors.summingDouble(RowTransform::regionShare)
                ));

            for (var entry : shares.entrySet()) {
                if (Math.abs(entry.getValue() - 1.0) > 0.000001) {
                    throw new IllegalStateException(
                        "Shares do not sum to one for " + entry.getKey()
                    );
                }
            }
        }

        private void validateUniqueIds() {
            long distinctIds = orders.stream()
                .map(Order::id)
                .distinct()
                .count();

            if (distinctIds != orders.size()) {
                throw new IllegalArgumentException(
                    "Order IDs must be unique."
                );
            }
        }
    }

    static Order order(
        int id,
        Region region,
        Department department,
        Channel channel,
        String product,
        Segment segment,
        int units,
        double price,
        double discount,
        boolean returned
    ) {
        return new Order(
            id,
            "2026-01-01",
            region,
            department,
            channel,
            product,
            segment,
            units,
            price,
            discount,
            returned
        );
    }

    static List<Order> sampleOrders() {
        return List.of(
            order(1001, Region.NORTH, Department.CLOUD, Channel.ONLINE,
                "Compute", Segment.ENTERPRISE, 8, 1200, .05, false),
            order(1002, Region.NORTH, Department.SECURITY, Channel.PARTNER,
                "Firewall", Segment.ENTERPRISE, 4, 2100, 0, false),
            order(1003, Region.SOUTH, Department.CLOUD, Channel.ONLINE,
                "Storage", Segment.SMB, 15, 400, .10, false),
            order(1004, Region.WEST, Department.DATA, Channel.DIRECT,
                "Analytics", Segment.ENTERPRISE, 6, 1800, .05, false),
            order(1005, Region.EAST, Department.SECURITY, Channel.ONLINE,
                "Identity", Segment.SMB, 20, 250, 0, true),
            order(1006, Region.NORTH, Department.DATA, Channel.PARTNER,
                "Analytics", Segment.SMB, 5, 1800, .15, false),
            order(1007, Region.SOUTH, Department.SECURITY, Channel.DIRECT,
                "Firewall", Segment.ENTERPRISE, 3, 2100, .05, false),
            order(1008, Region.WEST, Department.CLOUD, Channel.ONLINE,
                "Compute", Segment.SMB, 12, 1200, 0, false),
            order(1009, Region.EAST, Department.DATA, Channel.DIRECT,
                "Analytics", Segment.ENTERPRISE, 7, 1800, .10, false),
            order(1010, Region.NORTH, Department.CLOUD, Channel.PARTNER,
                "Storage", Segment.SMB, 30, 400, .05, false),
            order(1011, Region.SOUTH, Department.CLOUD, Channel.ONLINE,
                "Compute", Segment.ENTERPRISE, 5, 1200, 0, false),
            order(1012, Region.WEST, Department.SECURITY, Channel.PARTNER,
                "Identity", Segment.SMB, 18, 250, .10, true),
            order(1013, Region.EAST, Department.CLOUD, Channel.DIRECT,
                "Storage", Segment.SMB, 22, 400, .05, false),
            order(1014, Region.NORTH, Department.DATA, Channel.ONLINE,
                "Analytics", Segment.ENTERPRISE, 4, 1800, 0, false),
            order(1015, Region.SOUTH, Department.SECURITY, Channel.ONLINE,
                "Firewall", Segment.SMB, 9, 2100, .15, false),
            order(1016, Region.WEST, Department.CLOUD, Channel.DIRECT,
                "Compute", Segment.ENTERPRISE, 10, 1200, .05, false),
            order(1017, Region.EAST, Department.SECURITY, Channel.PARTNER,
                "Identity", Segment.ENTERPRISE, 11, 250, 0, false),
            order(1018, Region.NORTH, Department.DATA, Channel.DIRECT,
                "Analytics", Segment.SMB, 8, 1800, .10, true)
        );
    }

    static void printRegionMetrics(
        Map<Region, RegionMetrics> metrics
    ) {
        System.out.println("\nREGION GROUPING");

        metrics.forEach((region, value) ->
            System.out.printf(
                "%s orders=%d units=%d revenue=%.2f returned=%d%n",
                region,
                value.orders(),
                value.units(),
                value.netRevenue(),
                value.returnedOrders()
            )
        );
    }

    static void printDepartmentMetrics(
        Map<Department, DepartmentMetrics> metrics
    ) {
        System.out.println("\nDEPARTMENT AGGREGATION");

        metrics.forEach((department, value) ->
            System.out.printf(
                "%s orders=%d average=%.2f min=%.2f max=%.2f%n",
                department,
                value.orders(),
                value.averageRevenue(),
                value.minimumRevenue(),
                value.maximumRevenue()
            )
        );
    }

    static void printPivot(
        Map<Region, Map<Channel, Double>> pivot
    ) {
        System.out.println("\nPIVOT TABLE: REGION × CHANNEL");

        pivot.forEach((region, channels) -> {
            channels.forEach((channel, revenue) ->
                System.out.printf(
                    "%s | %s | %.2f%n",
                    region,
                    channel,
                    revenue
                )
            );
        });
    }

    static void printCrosstab(
        Map<Department, Map<Channel, Long>> crosstab
    ) {
        System.out.println("\nCROSSTAB: DEPARTMENT × CHANNEL");

        crosstab.forEach((department, channels) -> {
            channels.forEach((channel, count) ->
                System.out.printf(
                    "%s | %s | %d%n",
                    department,
                    channel,
                    count
                )
            );
        });
    }

    public static void main(String[] args) {
        try {
            AnalyticsService service =
                new AnalyticsService(sampleOrders());

            service.validateInvariants();

            printRegionMetrics(service.aggregateByRegion());
            printDepartmentMetrics(service.aggregateByDepartment());

            System.out.println("\nTRANSFORM-LIKE REGION METRICS");

            service.transformRegionMetrics().forEach(row ->
                System.out.printf(
                    "order=%d region=%s revenue=%.2f groupRevenue=%.2f share=%.4f%n",
                    row.orderId(),
                    row.region(),
                    row.netRevenue(),
                    row.regionRevenue(),
                    row.regionShare()
                )
            );

            printPivot(service.pivotRevenue());
            printCrosstab(service.crosstab());

            System.out.println("\nHIGH-VALUE ORDERS");

            service.highValueOrders(5000)
                .forEach(order ->
                    System.out.printf(
                        "%d | %s | %.2f%n",
                        order.id(),
                        order.region(),
                        order.netRevenue()
                    )
                );

            System.out.println("\nVALIDATION");
            System.out.println("All grouping invariants passed.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Analysis failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
