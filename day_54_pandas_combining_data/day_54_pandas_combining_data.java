import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class DataCombinationDemo {

    enum JoinType {
        INNER,
        LEFT,
        RIGHT,
        FULL
    }

    enum Relationship {
        ONE_TO_ONE,
        ONE_TO_MANY
    }

    record Customer(int id, String name, String region) {}

    record Order(
        int id,
        int customerId,
        double amount,
        String status
    ) {}

    record Contact(int customerId, String email) {}

    record CombinedOrder(
        int customerId,
        String customerName,
        String region,
        Integer orderId,
        Double amount,
        String status,
        boolean matched
    ) {}

    record CustomerTotal(
        int customerId,
        double total,
        String segment
    ) {}

    static class CombinationException extends RuntimeException {
        CombinationException(String message) {
            super(message);
        }
    }

    interface CombinationOperation<L, R, O> {
        O execute(L left, R right);
    }

    static final class DataService {

        private static void requirePositiveId(int id, String field) {
            if (id <= 0) {
                throw new CombinationException(
                    field + " must be positive: " + id
                );
            }
        }

        static void validateCustomers(List<Customer> customers) {
            Set<Integer> ids = new HashSet<>();

            for (Customer customer : customers) {
                requirePositiveId(customer.id(), "customer.id");

                if (!ids.add(customer.id())) {
                    throw new CombinationException(
                        "Duplicate customer id: " + customer.id()
                    );
                }

                if (customer.name() == null ||
                    customer.name().isBlank()) {
                    throw new CombinationException(
                        "Customer name cannot be blank."
                    );
                }
            }
        }

        static void validateOrders(List<Order> orders) {
            Set<Integer> ids = new HashSet<>();

            for (Order order : orders) {
                requirePositiveId(order.id(), "order.id");
                requirePositiveId(order.customerId(), "order.customerId");

                if (!ids.add(order.id())) {
                    throw new CombinationException(
                        "Duplicate order id: " + order.id()
                    );
                }

                if (order.amount() < 0) {
                    throw new CombinationException(
                        "Order amount cannot be negative: " + order.id()
                    );
                }
            }
        }

        static void validateRelationship(
            List<Customer> customers,
            List<Order> orders,
            Relationship relationship
        ) {
            validateCustomers(customers);
            validateOrders(orders);

            if (relationship == Relationship.ONE_TO_ONE) {
                Map<Integer, Integer> counts = new HashMap<>();

                for (Order order : orders) {
                    counts.merge(order.customerId(), 1, Integer::sum);
                }

                for (Map.Entry<Integer, Integer> entry : counts.entrySet()) {
                    if (entry.getValue() > 1) {
                        throw new CombinationException(
                            "One-to-one relationship violated for customer "
                                + entry.getKey()
                        );
                    }
                }
            }
        }

        static List<CombinedOrder> merge(
            List<Customer> customers,
            List<Order> orders,
            JoinType joinType,
            Relationship relationship
        ) {
            validateRelationship(customers, orders, relationship);

            Map<Integer, Customer> customerIndex =
                new LinkedHashMap<>();

            for (Customer customer : customers) {
                customerIndex.put(customer.id(), customer);
            }

            Map<Integer, List<Order>> ordersByCustomer =
                new LinkedHashMap<>();

            for (Order order : orders) {
                ordersByCustomer
                    .computeIfAbsent(
                        order.customerId(),
                        ignored -> new ArrayList<>()
                    )
                    .add(order);
            }

            List<CombinedOrder> result = new ArrayList<>();
            Set<Integer> matchedCustomers = new HashSet<>();

            for (Customer customer : customers) {
                List<Order> customerOrders =
                    ordersByCustomer.get(customer.id());

                if (customerOrders != null &&
                    !customerOrders.isEmpty()) {

                    matchedCustomers.add(customer.id());

                    for (Order order : customerOrders) {
                        result.add(
                            new CombinedOrder(
                                customer.id(),
                                customer.name(),
                                customer.region(),
                                order.id(),
                                order.amount(),
                                order.status(),
                                true
                            )
                        );
                    }
                } else if (
                    joinType == JoinType.LEFT ||
                    joinType == JoinType.FULL
                ) {
                    result.add(
                        new CombinedOrder(
                            customer.id(),
                            customer.name(),
                            customer.region(),
                            null,
                            null,
                            "NO_ORDER",
                            false
                        )
                    );
                }
            }

            if (joinType == JoinType.RIGHT ||
                joinType == JoinType.FULL) {

                for (Order order : orders) {
                    if (!customerIndex.containsKey(order.customerId())) {
                        result.add(
                            new CombinedOrder(
                                order.customerId(),
                                "UNKNOWN_CUSTOMER",
                                "UNKNOWN",
                                order.id(),
                                order.amount(),
                                order.status(),
                                false
                            )
                        );
                    }
                }
            }

            return List.copyOf(result);
        }

        static List<CustomerTotal> aggregate(
            List<CombinedOrder> rows
        ) {
            Map<Integer, Double> totals = new LinkedHashMap<>();

            for (CombinedOrder row : rows) {
                if (row.orderId() != null) {
                    totals.merge(
                        row.customerId(),
                        row.amount(),
                        Double::sum
                    );
                }
            }

            List<CustomerTotal> result = new ArrayList<>();

            for (Map.Entry<Integer, Double> entry : totals.entrySet()) {
                double total = entry.getValue();
                result.add(
                    new CustomerTotal(
                        entry.getKey(),
                        total,
                        total >= 1500 ? "HIGH" : "STANDARD"
                    )
                );
            }

            return List.copyOf(result);
        }

        static <T> List<T> concat(
            List<T> first,
            List<T> second
        ) {
            List<T> result = new ArrayList<>(
                first.size() + second.size()
            );

            result.addAll(first);
            result.addAll(second);

            return List.copyOf(result);
        }

        static <L, R> List<String> setDifference(
            List<L> left,
            List<R> right,
            java.util.function.Function<L, Integer> leftKey,
            java.util.function.Function<R, Integer> rightKey
        ) {
            Set<Integer> rightKeys = new HashSet<>();

            for (R value : right) {
                rightKeys.add(rightKey.apply(value));
            }

            List<String> result = new ArrayList<>();

            for (L value : left) {
                int key = leftKey.apply(value);

                if (!rightKeys.contains(key)) {
                    result.add(String.valueOf(key));
                }
            }

            return List.copyOf(result);
        }
    }

    private static void printRows(
        String title,
        List<CombinedOrder> rows
    ) {
        System.out.println("\n=== " + title + " ===");

        for (CombinedOrder row : rows) {
            System.out.printf(
                "customer=%d name=%s order=%s amount=%s status=%s matched=%s%n",
                row.customerId(),
                row.customerName(),
                row.orderId(),
                row.amount(),
                row.status(),
                row.matched()
            );
        }
    }

    public static void main(String[] args) {
        List<Customer> customers = List.of(
            new Customer(1, "Atul", "North"),
            new Customer(2, "Priya", "South"),
            new Customer(3, "Rahul", "North"),
            new Customer(4, "Neha", "West")
        );

        List<Order> orders = List.of(
            new Order(101, 1, 1200.0, "paid"),
            new Order(102, 2, 850.0, "paid"),
            new Order(103, 2, 450.0, "pending"),
            new Order(104, 5, 700.0, "paid"),
            new Order(105, 3, 1500.0, "paid")
        );

        List<Order> january = List.of(
            new Order(101, 1, 1200.0, "paid"),
            new Order(102, 2, 850.0, "paid")
        );

        List<Order> february = List.of(
            new Order(103, 2, 450.0, "pending"),
            new Order(104, 5, 700.0, "paid"),
            new Order(105, 3, 1500.0, "paid")
        );

        List<CombinedOrder> merged = DataService.merge(
            customers,
            orders,
            JoinType.LEFT,
            Relationship.ONE_TO_MANY
        );

        printRows("Left merge", merged);

        System.out.println("\n=== Aggregation ===");

        for (CustomerTotal total : DataService.aggregate(merged)) {
            System.out.printf(
                "customer=%d total=%.2f segment=%s%n",
                total.customerId(),
                total.total(),
                total.segment()
            );
        }

        List<Order> allOrders =
            DataService.concat(january, february);

        System.out.println("\n=== Concatenation ===");

        for (Order order : allOrders) {
            System.out.println(order);
        }

        System.out.println("\n=== Unmatched Customers ===");

        List<String> unmatchedCustomers =
            DataService.setDifference(
                customers,
                orders,
                Customer::id,
                Order::customerId
            );

        unmatchedCustomers.forEach(
            id -> System.out.println("customer_id=" + id)
        );

        System.out.println("\n=== Unmatched Orders ===");

        List<String> unmatchedOrders =
            DataService.setDifference(
                orders,
                customers,
                Order::customerId,
                Customer::id
            );

        unmatchedOrders.forEach(
            id -> System.out.println("customer_id=" + id)
        );

        System.out.println("\n=== Expected Validation Failure ===");

        try {
            List<Order> duplicateCustomerOrders = List.of(
                new Order(201, 1, 100.0, "paid"),
                new Order(202, 1, 200.0, "paid")
            );

            DataService.merge(
                customers,
                duplicateCustomerOrders,
                JoinType.LEFT,
                Relationship.ONE_TO_ONE
            );
        } catch (CombinationException exception) {
            System.out.println(exception.getMessage());
        }

        if (merged.size() != 6) {
            throw new CombinationException(
                "Unexpected merge result size."
            );
        }

        if (allOrders.size() != 5) {
            throw new CombinationException(
                "Unexpected concatenation size."
            );
        }

        System.out.println(
            "\nAll Java 17 validation checks passed."
        );
    }
}
