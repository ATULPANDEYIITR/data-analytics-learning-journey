import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * Enterprise-oriented analytics model.
 *
 * The program separates domain facts from analytical services. This mirrors
 * the separation normally created in SQL between source tables, preparation
 * CTEs, and final analytical queries.
 */
public class SqlAnalyticsPatterns {

    enum EventType {
        SIGNUP,
        VIEW_PRODUCT,
        ADD_TO_CART,
        CHECKOUT_STARTED,
        PURCHASE,
        LOGIN
    }

    record User(
        int id,
        LocalDate signupDate,
        String country,
        String channel
    ) {
        User {
            if (id <= 0) {
                throw new IllegalArgumentException("User ID must be positive");
            }
            if (signupDate == null) {
                throw new IllegalArgumentException("Signup date is required");
            }
        }

        YearMonth cohortMonth() {
            return YearMonth.from(signupDate);
        }
    }

    record Event(
        int userId,
        LocalDate eventDate,
        EventType type,
        double amount
    ) {}

    record Product(
        String id,
        String name,
        String category,
        double revenue
    ) {}

    record FunnelRow(
        String stage,
        int users,
        double conversionFromPrevious
    ) {}

    record SegmentMetrics(
        int activity,
        int purchases,
        double revenue
    ) {}

    static final class AnalyticsService {

        private final List<User> users;
        private final List<Event> events;

        AnalyticsService(List<User> users, List<Event> events) {
            this.users = List.copyOf(users);
            this.events = List.copyOf(events);
        }

        Map<YearMonth, List<User>> prepareCohorts() {
            return users.stream()
                .collect(Collectors.groupingBy(
                    User::cohortMonth,
                    LinkedHashMap::new,
                    Collectors.toList()
                ));
        }

        List<Product> topNByRevenue(List<Product> products, int n) {
            if (n <= 0) {
                throw new IllegalArgumentException("n must be positive");
            }

            List<Product> ordered = new ArrayList<>(products);
            ordered.sort(
                Comparator.comparingDouble(Product::revenue)
                    .reversed()
                    .thenComparing(Product::id)
            );

            List<Product> result = new ArrayList<>();
            int rank = 0;
            Double previousRevenue = null;

            for (Product product : ordered) {
                if (previousRevenue == null ||
                    Double.compare(previousRevenue, product.revenue) != 0) {
                    rank++;
                    previousRevenue = product.revenue;
                }

                if (rank <= n) {
                    result.add(product);
                }
            }

            return List.copyOf(result);
        }

        List<Map<String, Object>> retention() {
            Map<Integer, User> userById = users.stream()
                .collect(Collectors.toMap(User::id, user -> user));

            Map<YearMonth, Set<Integer>> cohortMembers = new LinkedHashMap<>();
            Map<YearMonth, Map<Integer, Set<Integer>>> activeByPeriod =
                new LinkedHashMap<>();

            for (User user : users) {
                cohortMembers
                    .computeIfAbsent(user.cohortMonth(), ignored -> new HashSet<>())
                    .add(user.id());
            }

            for (Event event : events) {
                if (!isRetentionActivity(event.type())) {
                    continue;
                }

                User user = userById.get(event.userId());
                if (user == null) {
                    continue;
                }

                int period = monthsBetween(
                    user.signupDate(),
                    event.eventDate()
                );

                if (period < 0) {
                    continue;
                }

                activeByPeriod
                    .computeIfAbsent(user.cohortMonth(), ignored -> new HashMap<>())
                    .computeIfAbsent(period, ignored -> new HashSet<>())
                    .add(user.id());
            }

            List<Map<String, Object>> result = new ArrayList<>();

            for (Map.Entry<YearMonth, Set<Integer>> cohortEntry :
                cohortMembers.entrySet()) {

                YearMonth cohort = cohortEntry.getKey();
                int cohortSize = cohortEntry.getValue().size();

                for (int period = 0; period <= 1; period++) {
                    int retained = activeByPeriod
                        .getOrDefault(cohort, Map.of())
                        .getOrDefault(period, Set.of())
                        .size();

                    double rate = cohortSize == 0
                        ? 0.0
                        : retained * 100.0 / cohortSize;

                    result.add(Map.of(
                        "cohort", cohort.toString(),
                        "period", period,
                        "cohortSize", cohortSize,
                        "retained", retained,
                        "retentionPct", round(rate)
                    ));
                }
            }

            return result;
        }

        List<FunnelRow> funnel() {
            List<FunnelStage> stages = List.of(
                new FunnelStage("signup", EventType.SIGNUP),
                new FunnelStage("product_view", EventType.VIEW_PRODUCT),
                new FunnelStage("cart", EventType.ADD_TO_CART),
                new FunnelStage("checkout", EventType.CHECKOUT_STARTED),
                new FunnelStage("purchase", EventType.PURCHASE)
            );

            Map<Integer, Set<EventType>> eventTypesByUser = new HashMap<>();

            for (Event event : events) {
                eventTypesByUser
                    .computeIfAbsent(event.userId(), ignored -> new HashSet<>())
                    .add(event.type());
            }

            List<FunnelRow> result = new ArrayList<>();
            int previous = 0;

            for (int index = 0; index < stages.size(); index++) {
                FunnelStage stage = stages.get(index);

                int count = (int) users.stream()
                    .filter(user ->
                        eventTypesByUser
                            .getOrDefault(user.id(), Set.of())
                            .contains(stage.type())
                    )
                    .count();

                double conversion;

                if (index == 0) {
                    conversion = count == 0 ? 0.0 : 100.0;
                } else if (previous == 0) {
                    conversion = 0.0;
                } else {
                    conversion = count * 100.0 / previous;
                }

                result.add(
                    new FunnelRow(stage.name(), count, round(conversion))
                );

                previous = count;
            }

            return result;
        }

        Map<Integer, SegmentMetrics> calculateMetrics() {
            Map<Integer, SegmentMetricsBuilder> builders = new HashMap<>();

            for (User user : users) {
                builders.put(user.id(), new SegmentMetricsBuilder());
            }

            for (Event event : events) {
                SegmentMetricsBuilder builder = builders.get(event.userId());

                if (builder == null) {
                    continue;
                }

                if (event.type() == EventType.LOGIN ||
                    event.type() == EventType.VIEW_PRODUCT ||
                    event.type() == EventType.ADD_TO_CART) {
                    builder.activity++;
                }

                if (event.type() == EventType.PURCHASE) {
                    builder.purchases++;
                    builder.revenue += event.amount();
                }
            }

            return builders.entrySet().stream()
                .collect(Collectors.toMap(
                    Map.Entry::getKey,
                    entry -> entry.getValue().freeze()
                ));
        }

        Map<Integer, String> classifySegments() {
            Map<Integer, SegmentMetrics> metrics = calculateMetrics();
            Map<Integer, String> result = new LinkedHashMap<>();

            for (User user : users) {
                SegmentMetrics metric = metrics.getOrDefault(
                    user.id(),
                    new SegmentMetrics(0, 0, 0.0)
                );

                String segment;

                if (metric.purchases() >= 2 || metric.revenue() >= 300.0) {
                    segment = "high_value";
                } else if (metric.purchases() > 0) {
                    segment = "buyer";
                } else if (metric.activity() >= 3) {
                    segment = "engaged_non_buyer";
                } else {
                    segment = "low_activity";
                }

                result.put(user.id(), segment);
            }

            return Map.copyOf(result);
        }

        private static boolean isRetentionActivity(EventType type) {
            return switch (type) {
                case LOGIN, VIEW_PRODUCT, ADD_TO_CART, PURCHASE -> true;
                default -> false;
            };
        }

        private static int monthsBetween(LocalDate start, LocalDate end) {
            return (end.getYear() - start.getYear()) * 12
                + end.getMonthValue() - start.getMonthValue();
        }

        private static double round(double value) {
            return Math.round(value * 10.0) / 10.0;
        }

        private record FunnelStage(String name, EventType type) {}

        private static final class SegmentMetricsBuilder {
            private int activity;
            private int purchases;
            private double revenue;

            private SegmentMetrics freeze() {
                return new SegmentMetrics(activity, purchases, revenue);
            }
        }
    }

    private static void printTable(String title, List<?> rows) {
        System.out.println("\n=== " + title + " ===");
        rows.forEach(System.out::println);
    }

    public static void main(String[] args) {
        List<User> users = List.of(
            new User(1, LocalDate.of(2026, 1, 2), "IN", "organic"),
            new User(2, LocalDate.of(2026, 1, 3), "IN", "paid"),
            new User(3, LocalDate.of(2026, 1, 8), "US", "organic"),
            new User(4, LocalDate.of(2026, 1, 15), "IN", "referral"),
            new User(5, LocalDate.of(2026, 2, 2), "DE", "paid"),
            new User(6, LocalDate.of(2026, 2, 5), "IN", "organic"),
            new User(7, LocalDate.of(2026, 2, 9), "US", "paid"),
            new User(8, LocalDate.of(2026, 2, 20), "IN", "referral")
        );

        List<Event> events = List.of(
            new Event(1, LocalDate.of(2026, 1, 2), EventType.SIGNUP, 0),
            new Event(1, LocalDate.of(2026, 1, 2), EventType.VIEW_PRODUCT, 0),
            new Event(1, LocalDate.of(2026, 1, 2), EventType.ADD_TO_CART, 0),
            new Event(1, LocalDate.of(2026, 1, 2), EventType.CHECKOUT_STARTED, 0),
            new Event(1, LocalDate.of(2026, 1, 2), EventType.PURCHASE, 300),
            new Event(1, LocalDate.of(2026, 2, 2), EventType.LOGIN, 0),

            new Event(2, LocalDate.of(2026, 1, 3), EventType.SIGNUP, 0),
            new Event(2, LocalDate.of(2026, 1, 3), EventType.VIEW_PRODUCT, 0),
            new Event(2, LocalDate.of(2026, 1, 3), EventType.ADD_TO_CART, 0),
            new Event(2, LocalDate.of(2026, 1, 3), EventType.CHECKOUT_STARTED, 0),
            new Event(2, LocalDate.of(2026, 1, 3), EventType.PURCHASE, 180),

            new Event(3, LocalDate.of(2026, 1, 8), EventType.SIGNUP, 0),
            new Event(3, LocalDate.of(2026, 1, 8), EventType.VIEW_PRODUCT, 0),
            new Event(3, LocalDate.of(2026, 2, 8), EventType.LOGIN, 0),

            new Event(4, LocalDate.of(2026, 1, 15), EventType.SIGNUP, 0),
            new Event(4, LocalDate.of(2026, 1, 15), EventType.VIEW_PRODUCT, 0),
            new Event(4, LocalDate.of(2026, 1, 15), EventType.ADD_TO_CART, 0),

            new Event(5, LocalDate.of(2026, 2, 2), EventType.SIGNUP, 0),
            new Event(5, LocalDate.of(2026, 2, 2), EventType.VIEW_PRODUCT, 0),
            new Event(5, LocalDate.of(2026, 2, 2), EventType.ADD_TO_CART, 0),
            new Event(5, LocalDate.of(2026, 2, 2), EventType.CHECKOUT_STARTED, 0),
            new Event(5, LocalDate.of(2026, 2, 2), EventType.PURCHASE, 230),
            new Event(5, LocalDate.of(2026, 3, 2), EventType.LOGIN, 0),

            new Event(6, LocalDate.of(2026, 2, 5), EventType.SIGNUP, 0),
            new Event(6, LocalDate.of(2026, 2, 5), EventType.VIEW_PRODUCT, 0),
            new Event(6, LocalDate.of(2026, 3, 5), EventType.LOGIN, 0),

            new Event(7, LocalDate.of(2026, 2, 9), EventType.SIGNUP, 0),
            new Event(7, LocalDate.of(2026, 2, 9), EventType.VIEW_PRODUCT, 0),

            new Event(8, LocalDate.of(2026, 2, 20), EventType.SIGNUP, 0),
            new Event(8, LocalDate.of(2026, 2, 20), EventType.VIEW_PRODUCT, 0),
            new Event(8, LocalDate.of(2026, 2, 20), EventType.ADD_TO_CART, 0)
        );

        List<Product> products = List.of(
            new Product("P100", "Analytics Platform", "software", 18200),
            new Product("P200", "Operations Suite", "software", 15700),
            new Product("P300", "Data Connector", "integration", 15700),
            new Product("P400", "Audit Module", "governance", 11900),
            new Product("P500", "Forecasting Module", "analytics", 9400)
        );

        AnalyticsService service = new AnalyticsService(users, events);

        printTable(
            "Top-N Revenue",
            service.topNByRevenue(products, 3)
        );

        printTable(
            "Cohort Preparation",
            service.prepareCohorts().entrySet().stream()
                .map(entry -> entry.getKey() + " -> " + entry.getValue())
                .toList()
        );

        printTable("Retention", service.retention());
        printTable("Funnel", service.funnel().stream().toList());

        System.out.println("\n=== Segmentation ===");
        service.classifySegments()
            .forEach((userId, segment) ->
                System.out.println("User " + userId + " -> " + segment)
            );

        System.out.println("\n=== Failure Validation ===");

        try {
            service.topNByRevenue(products, 0);
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "Invalid Top-N request rejected: " + exception.getMessage()
            );
        }
    }
}
