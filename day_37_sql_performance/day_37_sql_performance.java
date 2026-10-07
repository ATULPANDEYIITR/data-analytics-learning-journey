import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.function.Predicate;

/*
 * Enterprise SQL Performance Governance Case Study
 *
 * The application models an order-reporting service that must decide whether
 * an access path and join strategy are reasonable before a database query is
 * deployed.
 *
 * Java-specific design:
 * - records represent immutable domain data
 * - enums model scan and join strategies
 * - interfaces separate cost estimation from policy
 * - generics and collections represent index structures
 * - exceptions protect invalid performance assumptions
 * - service objects model enterprise query-analysis behavior
 *
 * The calculations are intentionally simplified versions of database
 * optimizer reasoning. PostgreSQL's actual planner uses substantially more
 * statistics and cost factors.
 */

public class SqlPerformanceCaseStudy {

    enum AccessPath {
        SEQUENTIAL_SCAN,
        INDEX_SCAN
    }

    enum JoinStrategy {
        NESTED_LOOP,
        INDEXED_NESTED_LOOP,
        HASH_JOIN
    }

    record Customer(
        int customerId,
        String region
    ) {}

    record Order(
        int orderId,
        int customerId,
        int dayOfYear,
        String status,
        double amount
    ) {}

    record PlanEstimate(
        AccessPath accessPath,
        long estimatedRows,
        double estimatedCost
    ) {}

    record ExecutionResult(
        long examinedRows,
        long returnedRows
    ) {}

    interface CostModel {
        PlanEstimate estimate(
            long tableRows,
            long matchingRows
        );
    }

    static final class SimpleCostModel implements CostModel {

        private final double sequentialCpuCost;
        private final double randomPageCost;

        SimpleCostModel(
            double sequentialCpuCost,
            double randomPageCost
        ) {
            if (sequentialCpuCost <= 0 || randomPageCost <= 0) {
                throw new IllegalArgumentException(
                    "Cost parameters must be positive."
                );
            }

            this.sequentialCpuCost = sequentialCpuCost;
            this.randomPageCost = randomPageCost;
        }

        @Override
        public PlanEstimate estimate(
            long tableRows,
            long matchingRows
        ) {
            if (tableRows < 0 || matchingRows < 0) {
                throw new IllegalArgumentException(
                    "Row counts cannot be negative."
                );
            }

            if (matchingRows > tableRows) {
                throw new IllegalArgumentException(
                    "Matching rows cannot exceed table rows."
                );
            }

            if (tableRows == 0) {
                return new PlanEstimate(
                    AccessPath.SEQUENTIAL_SCAN,
                    0,
                    0
                );
            }

            double sequentialCost =
                tableRows * sequentialCpuCost;

            double treeHeight =
                Math.ceil(
                    Math.log(
                        Math.max(2, tableRows)
                    ) / Math.log(2)
                );

            double indexCost =
                treeHeight +
                matchingRows * randomPageCost * 0.05 +
                matchingRows * 0.01;

            AccessPath path =
                indexCost < sequentialCost
                    ? AccessPath.INDEX_SCAN
                    : AccessPath.SEQUENTIAL_SCAN;

            return new PlanEstimate(
                path,
                matchingRows,
                Math.min(
                    sequentialCost,
                    indexCost
                )
            );
        }
    }

    static final class QueryExecutionService {

        private final CostModel costModel;

        QueryExecutionService(CostModel costModel) {
            this.costModel = costModel;
        }

        ExecutionResult sequentialScan(
            List<Order> orders,
            Predicate<Order> predicate
        ) {
            long examined = 0;
            long returned = 0;

            for (Order order : orders) {
                examined++;

                if (predicate.test(order)) {
                    returned++;
                }
            }

            return new ExecutionResult(
                examined,
                returned
            );
        }

        ExecutionResult indexedCustomerLookup(
            Map<Integer, List<Order>> index,
            int customerId,
            Predicate<Order> predicate
        ) {
            List<Order> candidates =
                index.getOrDefault(
                    customerId,
                    List.of()
                );

            long examined = 0;
            long returned = 0;

            for (Order order : candidates) {
                examined++;

                if (predicate.test(order)) {
                    returned++;
                }
            }

            return new ExecutionResult(
                examined,
                returned
            );
        }

        PlanEstimate choosePlan(
            List<Order> orders,
            Predicate<Order> predicate
        ) {
            long matches =
                orders.stream()
                    .filter(predicate)
                    .count();

            return costModel.estimate(
                orders.size(),
                matches
            );
        }
    }

    static final class JoinEngine {

        long nestedLoopComparisons(
            List<Customer> customers,
            List<Order> orders
        ) {
            long comparisons = 0;

            for (Customer customer : customers) {
                for (Order order : orders) {
                    comparisons++;

                    if (
                        customer.customerId() ==
                        order.customerId()
                    ) {
                        // Match found. No extra work is needed
                        // for this comparison-based demonstration.
                    }
                }
            }

            return comparisons;
        }

        long indexedNestedLoopLookups(
            List<Customer> customers,
            Map<Integer, List<Order>> orderIndex
        ) {
            long lookups = 0;

            for (Customer customer : customers) {
                lookups++;

                /*
                 * The important operation is the keyed lookup. The database
                 * analogue is an indexed access to the inner relation.
                 */
                orderIndex.getOrDefault(
                    customer.customerId(),
                    List.of()
                );
            }

            return lookups;
        }

        long hashJoinProbes(
            List<Customer> customers,
            List<Order> orders
        ) {
            Map<Integer, Customer> customerHash =
                new HashMap<>();

            for (Customer customer : customers) {
                customerHash.put(
                    customer.customerId(),
                    customer
                );
            }

            long probes = 0;

            for (Order order : orders) {
                probes++;

                customerHash.get(
                    order.customerId()
                );
            }

            return probes;
        }
    }

    static List<Customer> generateCustomers(
        int count
    ) {
        List<Customer> customers =
            new ArrayList<>(count);

        String[] regions = {
            "North",
            "South",
            "East",
            "West"
        };

        for (int i = 1; i <= count; i++) {
            customers.add(
                new Customer(
                    i,
                    regions[i % regions.length]
                )
            );
        }

        return customers;
    }

    static List<Order> generateOrders(
        int count,
        int customerCount
    ) {
        Random random = new Random(42);

        String[] statuses = {
            "pending",
            "paid",
            "shipped",
            "cancelled",
            "refunded"
        };

        List<Order> orders =
            new ArrayList<>(count);

        for (int i = 1; i <= count; i++) {
            int statusRoll =
                random.nextInt(100);

            String status;

            if (statusRoll < 5) {
                status = "pending";
            } else if (statusRoll < 40) {
                status = "paid";
            } else if (statusRoll < 85) {
                status = "shipped";
            } else if (statusRoll < 93) {
                status = "cancelled";
            } else {
                status = "refunded";
            }

            orders.add(
                new Order(
                    i,
                    1 + random.nextInt(customerCount),
                    1 + random.nextInt(273),
                    status,
                    10 + random.nextDouble() * 24990
                )
            );
        }

        return orders;
    }

    static Map<Integer, List<Order>> buildCustomerIndex(
        List<Order> orders
    ) {
        Map<Integer, List<Order>> index =
            new HashMap<>();

        for (Order order : orders) {
            index.computeIfAbsent(
                order.customerId(),
                ignored -> new ArrayList<>()
            ).add(order);
        }

        return index;
    }

    static void compositeIndexModel(
        Map<Integer, List<Order>> customerIndex
    ) {
        System.out.println(
            "\n=== Composite Index Model ==="
        );

        /*
         * Each customer's rows are sorted by day. This models the ordering
         * effect of an index whose keys are (customer_id, day_of_year).
         */
        customerIndex.values().forEach(
            orders -> orders.sort(
                Comparator.comparingInt(
                    Order::dayOfYear
                )
            )
        );

        List<Order> customerOrders =
            customerIndex.getOrDefault(
                731,
                List.of()
            );

        int cutoff = 244;

        int firstMatching = 0;

        while (
            firstMatching < customerOrders.size() &&
            customerOrders
                .get(firstMatching)
                .dayOfYear() < cutoff
        ) {
            firstMatching++;
        }

        int resultRows =
            customerOrders.size() -
            firstMatching;

        System.out.println(
            "customer_id=731"
        );

        System.out.println(
            "day_of_year >= " + cutoff
        );

        System.out.println(
            "Rows after range boundary: " +
            resultRows
        );
    }

    static void printPlan(
        PlanEstimate plan,
        long actualRows
    ) {
        System.out.printf(
            "%s estimated_rows=%d actual_rows=%d cost=%.2f%n",
            plan.accessPath(),
            plan.estimatedRows(),
            actualRows,
            plan.estimatedCost()
        );

        if (plan.estimatedRows() == 0) {
            return;
        }

        double ratio =
            (double) actualRows /
            plan.estimatedRows();

        if (ratio > 10 || ratio < 0.1) {
            System.out.println(
                "Cardinality warning: investigate statistics, " +
                "data skew, or correlated predicates."
            );
        }
    }

    static void partialIndexPolicy() {
        System.out.println(
            "\n=== Partial Index Policy ==="
        );

        System.out.println(
            "A partial index such as " +
            "orders(customer_id) WHERE status='paid' " +
            "contains only paid rows."
        );

        System.out.println(
            "Its small footprint can reduce index maintenance " +
            "and lookup work for paid-order workloads."
        );

        System.out.println(
            "A query for cancelled orders cannot logically use " +
            "that partial index as though it contained cancelled rows."
        );
    }

    static void coveringIndexPolicy() {
        System.out.println(
            "\n=== Covering Index Policy ==="
        );

        System.out.println(
            "An index on customer_id INCLUDE " +
            "(order_date, total_amount) can supply projected " +
            "columns without requiring ordinary heap access in " +
            "favorable index-only-scan conditions."
        );

        System.out.println(
            "Coverage does not eliminate all visibility checks or " +
            "make every query index-only."
        );
    }

    public static void main(String[] args) {
        System.out.println(
            "ENTERPRISE SQL PERFORMANCE CASE STUDY"
        );
        System.out.println(
            "======================================="
        );

        List<Customer> customers =
            generateCustomers(10_000);

        List<Order> orders =
            generateOrders(
                100_000,
                customers.size()
            );

        QueryExecutionService service =
            new QueryExecutionService(
                new SimpleCostModel(
                    0.01,
                    4.0
                )
            );

        int targetCustomer = 731;

        Predicate<Order> customerPredicate =
            order ->
                order.customerId() ==
                targetCustomer;

        long actualMatches =
            orders.stream()
                .filter(customerPredicate)
                .count();

        PlanEstimate plan =
            service.choosePlan(
                orders,
                customerPredicate
            );

        System.out.println(
            "\n=== Access Path Evaluation ==="
        );

        printPlan(
            plan,
            actualMatches
        );

        ExecutionResult sequential =
            service.sequentialScan(
                orders,
                customerPredicate
            );

        System.out.println(
            "Sequential examined=" +
            sequential.examinedRows() +
            " returned=" +
            sequential.returnedRows()
        );

        Map<Integer, List<Order>> customerIndex =
            buildCustomerIndex(orders);

        ExecutionResult indexed =
            service.indexedCustomerLookup(
                customerIndex,
                targetCustomer,
                customerPredicate
            );

        System.out.println(
            "Indexed examined=" +
            indexed.examinedRows() +
            " returned=" +
            indexed.returnedRows()
        );

        compositeIndexModel(customerIndex);

        JoinEngine joinEngine =
            new JoinEngine();

        /*
         * The naive join is executed only on a reduced sample because its
         * O(N*M) behavior would be unnecessarily expensive at production
         * scale. The indexed and hash approaches are shown using the same
         * sample to make the relative operation counts comparable.
         */
        List<Customer> sampleCustomers =
            customers.subList(0, 100);

        List<Order> sampleOrders =
            orders.subList(0, 2_000);

        System.out.println(
            "\n=== Join Strategy Evaluation ==="
        );

        long nestedComparisons =
            joinEngine.nestedLoopComparisons(
                sampleCustomers,
                sampleOrders
            );

        long indexedLookups =
            joinEngine.indexedNestedLoopLookups(
                sampleCustomers,
                customerIndex
            );

        long hashProbes =
            joinEngine.hashJoinProbes(
                sampleCustomers,
                sampleOrders
            );

        System.out.println(
            "Nested-loop comparisons=" +
            nestedComparisons
        );

        System.out.println(
            "Indexed nested-loop lookups=" +
            indexedLookups
        );

        System.out.println(
            "Hash-join probes=" +
            hashProbes
        );

        partialIndexPolicy();
        coveringIndexPolicy();

        System.out.println(
            "\n=== Production Interpretation ==="
        );

        System.out.println(
            "A good plan is workload-dependent. Index availability, " +
            "selectivity, table size, statistics, memory, join cardinality, " +
            "and physical data distribution all influence the optimizer."
        );

        System.out.println(
            "Validate the real PostgreSQL query with " +
            "EXPLAIN (ANALYZE, BUFFERS) rather than relying only on " +
            "a theoretical index benefit."
        );
    }
}
