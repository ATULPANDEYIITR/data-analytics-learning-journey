import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * DAX AGGREGATIONS: ENTERPRISE ANALYTICS MODEL
 *
 * Java 17 implementation featuring:
 * - Immutable transaction records
 * - Typed analytical filters
 * - Filter-context evaluation
 * - SUM, AVERAGE, COUNT, DISTINCTCOUNT
 * - CALCULATE and FILTER
 * - Business validation
 * - Aggregation services
 *
 * Compile:
 * javac DaxAggregations.java
 *
 * Run:
 * java DaxAggregations
 */

public class DaxAggregations {

    enum Region {
        NORTH, SOUTH, EAST, WEST
    }

    enum Category {
        ELECTRONICS, FURNITURE, CLOTHING
    }

    enum Status {
        COMPLETED, PENDING, CANCELLED
    }

    enum Operator {
        EQUALS,
        NOT_EQUALS,
        GREATER_THAN,
        GREATER_OR_EQUAL,
        LESS_THAN,
        LESS_OR_EQUAL,
        IN
    }

    enum Column {
        TRANSACTION_ID,
        ORDER_DATE,
        CUSTOMER_ID,
        PRODUCT_ID,
        REGION,
        CATEGORY,
        QUANTITY,
        UNIT_PRICE,
        REVENUE,
        STATUS
    }

    static class AnalyticsException extends RuntimeException {
        AnalyticsException(String message) {
            super(message);
        }
    }

    static class ValidationException extends AnalyticsException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class AggregationException extends AnalyticsException {
        AggregationException(String message) {
            super(message);
        }
    }

    record Transaction(
        int transactionId,
        LocalDate orderDate,
        Integer customerId,
        int productId,
        Region region,
        Category category,
        Integer quantity,
        BigDecimal unitPrice,
        BigDecimal revenue,
        Status status
    ) {
        Transaction {
            if (transactionId <= 0 || productId <= 0) {
                throw new ValidationException(
                    "Transaction and product IDs must be positive."
                );
            }

            Objects.requireNonNull(orderDate);
            Objects.requireNonNull(region);
            Objects.requireNonNull(category);
            Objects.requireNonNull(unitPrice);
            Objects.requireNonNull(status);

            if (quantity != null && quantity < 0) {
                throw new ValidationException(
                    "Quantity cannot be negative."
                );
            }

            if (unitPrice.signum() < 0) {
                throw new ValidationException(
                    "Unit price cannot be negative."
                );
            }

            if (revenue != null && revenue.signum() < 0) {
                throw new ValidationException(
                    "Revenue cannot be negative."
                );
            }
        }

        Object value(Column column) {
            return switch (column) {
                case TRANSACTION_ID -> transactionId;
                case ORDER_DATE -> orderDate;
                case CUSTOMER_ID -> customerId;
                case PRODUCT_ID -> productId;
                case REGION -> region;
                case CATEGORY -> category;
                case QUANTITY -> quantity;
                case UNIT_PRICE -> unitPrice;
                case REVENUE -> revenue;
                case STATUS -> status;
            };
        }
    }

    record Filter(
        Column column,
        Operator operator,
        Object value
    ) {
        Filter {
            Objects.requireNonNull(column);
            Objects.requireNonNull(operator);
            Objects.requireNonNull(value);

            if (operator == Operator.IN && !(value instanceof Set<?>)) {
                throw new ValidationException(
                    "IN requires a Set of values."
                );
            }
        }

        boolean matches(Transaction transaction) {
            Object actual = transaction.value(column);

            // Ordinary comparisons do not match BLANK.
            if (actual == null) {
                return false;
            }

            if (operator == Operator.IN) {
                return ((Set<?>) value).contains(actual);
            }

            if (operator == Operator.EQUALS) {
                return actual.equals(value);
            }

            if (operator == Operator.NOT_EQUALS) {
                return !actual.equals(value);
            }

            if (!(actual instanceof Comparable<?>)) {
                throw new ValidationException(
                    "Ordered comparison requires comparable values."
                );
            }

            @SuppressWarnings("unchecked")
            Comparable<Object> comparable =
                (Comparable<Object>) actual;

            int comparison = comparable.compareTo(value);

            return switch (operator) {
                case GREATER_THAN -> comparison > 0;
                case GREATER_OR_EQUAL -> comparison >= 0;
                case LESS_THAN -> comparison < 0;
                case LESS_OR_EQUAL -> comparison <= 0;
                default -> throw new ValidationException(
                    "Unsupported comparison."
                );
            };
        }
    }

    static final class FilterContext {
        private final List<Filter> filters;

        FilterContext() {
            this.filters = List.of();
        }

        private FilterContext(List<Filter> filters) {
            this.filters = List.copyOf(filters);
        }

        FilterContext add(Filter... additional) {
            List<Filter> updated = new ArrayList<>(filters);
            Collections.addAll(updated, additional);
            return new FilterContext(updated);
        }

        FilterContext replace(Column column, Filter replacement) {
            if (replacement.column() != column) {
                throw new ValidationException(
                    "Replacement filter column mismatch."
                );
            }

            List<Filter> updated = filters.stream()
                .filter(filter -> filter.column() != column)
                .collect(Collectors.toCollection(ArrayList::new));

            updated.add(replacement);

            return new FilterContext(updated);
        }

        boolean matches(Transaction transaction) {
            return filters.stream().allMatch(
                filter -> filter.matches(transaction)
            );
        }

        List<Filter> filters() {
            return filters;
        }
    }

    interface Measure {
        BigDecimal evaluate(
            AnalyticsService service,
            FilterContext context
        );
    }

    static final class SalesMeasures {

        private SalesMeasures() {}

        static Measure totalRevenue() {
            return AnalyticsService::sumRevenue;
        }

        static Measure averageRevenue() {
            return AnalyticsService::averageRevenue;
        }

        static Measure completedRevenue() {
            return (service, context) -> {
                Filter completed = new Filter(
                    Column.STATUS,
                    Operator.EQUALS,
                    Status.COMPLETED
                );

                return service.sumRevenue(
                    context.add(completed)
                );
            };
        }
    }

    static final class AnalyticsService {
        private final List<Transaction> transactions;

        AnalyticsService(List<Transaction> transactions) {
            this.transactions = List.copyOf(transactions);
            validateDataset();
        }

        private void validateDataset() {
            Set<Integer> ids = new HashSet<>();

            for (Transaction transaction : transactions) {
                if (!ids.add(transaction.transactionId())) {
                    throw new ValidationException(
                        "Duplicate transaction ID: " +
                        transaction.transactionId()
                    );
                }
            }
        }

        List<Transaction> evaluate(FilterContext context) {
            return transactions.stream()
                .filter(context::matches)
                .toList();
        }

        BigDecimal sumRevenue(FilterContext context) {
            return evaluate(context).stream()
                .map(Transaction::revenue)
                .filter(Objects::nonNull)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        BigDecimal averageRevenue(FilterContext context) {
            List<BigDecimal> values = evaluate(context).stream()
                .map(Transaction::revenue)
                .filter(Objects::nonNull)
                .toList();

            if (values.isEmpty()) {
                return null;
            }

            BigDecimal total = values.stream()
                .reduce(BigDecimal.ZERO, BigDecimal::add);

            return total.divide(
                BigDecimal.valueOf(values.size()),
                4,
                RoundingMode.HALF_UP
            );
        }

        long count(Column column, FilterContext context) {
            validateNumericColumn(column);

            return evaluate(context).stream()
                .map(transaction -> transaction.value(column))
                .filter(Objects::nonNull)
                .count();
        }

        long distinctCount(Column column, FilterContext context) {
            Set<Object> distinct = evaluate(context).stream()
                .map(transaction -> transaction.value(column))
                .collect(Collectors.toSet());

            return distinct.size();
        }

        private void validateNumericColumn(Column column) {
            if (column != Column.TRANSACTION_ID &&
                column != Column.PRODUCT_ID &&
                column != Column.CUSTOMER_ID &&
                column != Column.QUANTITY &&
                column != Column.UNIT_PRICE &&
                column != Column.REVENUE) {

                throw new AggregationException(
                    "COUNT requires a numeric column."
                );
            }
        }

        List<Transaction> filter(
            FilterContext context,
            Predicate<Transaction> predicate
        ) {
            Objects.requireNonNull(predicate);

            return evaluate(context).stream()
                .filter(predicate)
                .toList();
        }

        <T> T calculate(
            java.util.function.Function<FilterContext, T> expression,
            FilterContext original,
            List<Filter> additionalFilters,
            Set<Column> replaceColumns
        ) {
            FilterContext modified = original;

            for (Filter filter : additionalFilters) {
                if (replaceColumns.contains(filter.column())) {
                    modified = modified.replace(
                        filter.column(),
                        filter
                    );
                } else {
                    modified = modified.add(filter);
                }
            }

            return expression.apply(modified);
        }

        Map<Region, BigDecimal> regionalRevenue() {
            Map<Region, BigDecimal> result = new LinkedHashMap<>();

            for (Region region : Region.values()) {
                FilterContext context = new FilterContext().add(
                    new Filter(
                        Column.REGION,
                        Operator.EQUALS,
                        region
                    )
                );

                result.put(region, sumRevenue(context));
            }

            return result;
        }

        Map<Category, BigDecimal> categoryRevenue() {
            return evaluate(new FilterContext()).stream()
                .filter(t -> t.revenue() != null)
                .collect(Collectors.groupingBy(
                    Transaction::category,
                    () -> new LinkedHashMap<>(),
                    Collectors.reducing(
                        BigDecimal.ZERO,
                        Transaction::revenue,
                        BigDecimal::add
                    )
                ));
        }

        int totalTransactions() {
            return transactions.size();
        }
    }

    private static List<Transaction> sampleData() {
        return List.of(
            new Transaction(
                1001, LocalDate.of(2026, 1, 5), 101, 1,
                Region.NORTH, Category.ELECTRONICS, 2,
                new BigDecimal("500.00"),
                new BigDecimal("1000.00"),
                Status.COMPLETED
            ),
            new Transaction(
                1002, LocalDate.of(2026, 1, 8), 102, 2,
                Region.SOUTH, Category.FURNITURE, 1,
                new BigDecimal("800.00"),
                new BigDecimal("800.00"),
                Status.COMPLETED
            ),
            new Transaction(
                1003, LocalDate.of(2026, 1, 12), 101, 3,
                Region.NORTH, Category.ELECTRONICS, 3,
                new BigDecimal("200.00"),
                new BigDecimal("600.00"),
                Status.COMPLETED
            ),
            new Transaction(
                1004, LocalDate.of(2026, 2, 2), 103, 4,
                Region.EAST, Category.FURNITURE, 2,
                new BigDecimal("350.00"),
                new BigDecimal("700.00"),
                Status.PENDING
            ),
            new Transaction(
                1005, LocalDate.of(2026, 2, 9), 104, 5,
                Region.WEST, Category.CLOTHING, 5,
                new BigDecimal("100.00"),
                new BigDecimal("500.00"),
                Status.COMPLETED
            ),
            new Transaction(
                1006, LocalDate.of(2026, 2, 15), 102, 6,
                Region.SOUTH, Category.ELECTRONICS, 1,
                new BigDecimal("1200.00"),
                new BigDecimal("1200.00"),
                Status.COMPLETED
            ),
            new Transaction(
                1007, LocalDate.of(2026, 3, 1), 105, 7,
                Region.NORTH, Category.CLOTHING, 4,
                new BigDecimal("150.00"),
                new BigDecimal("600.00"),
                Status.CANCELLED
            ),
            new Transaction(
                1008, LocalDate.of(2026, 3, 5), 103, 8,
                Region.EAST, Category.ELECTRONICS, 2,
                new BigDecimal("450.00"),
                new BigDecimal("900.00"),
                Status.COMPLETED
            ),
            new Transaction(
                1009, LocalDate.of(2026, 3, 12), null, 9,
                Region.WEST, Category.FURNITURE, null,
                new BigDecimal("250.00"),
                null,
                Status.PENDING
            ),
            new Transaction(
                1010, LocalDate.of(2026, 3, 18), 106, 10,
                Region.NORTH, Category.ELECTRONICS, 1,
                new BigDecimal("300.00"),
                new BigDecimal("300.00"),
                Status.COMPLETED
            )
        );
    }

    private static String money(BigDecimal value) {
        return value == null
            ? "BLANK"
            : value.setScale(2, RoundingMode.HALF_UP).toPlainString();
    }

    public static void main(String[] args) {
        try {
            AnalyticsService service =
                new AnalyticsService(sampleData());

            FilterContext all = new FilterContext();

            System.out.println("DAX AGGREGATIONS");
            System.out.println("================");

            System.out.println("\nSUM");
            System.out.println(money(service.sumRevenue(all)));

            System.out.println("\nAVERAGE");
            System.out.println(money(service.averageRevenue(all)));

            System.out.println("\nCOUNT");
            System.out.println(
                service.count(Column.REVENUE, all)
            );

            System.out.println("\nDISTINCTCOUNT");
            System.out.println(
                service.distinctCount(Column.CUSTOMER_ID, all)
            );

            Filter north = new Filter(
                Column.REGION,
                Operator.EQUALS,
                Region.NORTH
            );

            FilterContext northContext = all.add(north);

            System.out.println("\nFILTER: NORTH");
            System.out.println(
                money(service.sumRevenue(northContext))
            );

            Filter electronics = new Filter(
                Column.CATEGORY,
                Operator.EQUALS,
                Category.ELECTRONICS
            );

            Filter completed = new Filter(
                Column.STATUS,
                Operator.EQUALS,
                Status.COMPLETED
            );

            FilterContext combined = northContext.add(
                electronics,
                completed
            );

            System.out.println("\nNORTH COMPLETED ELECTRONICS");
            System.out.println(
                money(service.sumRevenue(combined))
            );

            System.out.println("\nCALCULATE");
            Filter south = new Filter(
                Column.REGION,
                Operator.EQUALS,
                Region.SOUTH
            );

            BigDecimal southRevenue = service.calculate(
                service::sumRevenue,
                all,
                List.of(south),
                Set.of()
            );

            System.out.println(money(southRevenue));

            System.out.println("\nCALCULATE: REPLACE REGION");

            BigDecimal replaced = service.calculate(
                service::sumRevenue,
                northContext,
                List.of(south),
                Set.of(Column.REGION)
            );

            System.out.println(money(replaced));

            System.out.println("\nCALCULATE: PRESERVE REGION");

            BigDecimal preserved = service.calculate(
                service::sumRevenue,
                northContext,
                List.of(electronics),
                Set.of()
            );

            System.out.println(money(preserved));

            System.out.println("\nNAMED MEASURES");

            System.out.println(
                "Total revenue: " +
                money(SalesMeasures.totalRevenue().evaluate(
                    service, all
                ))
            );

            System.out.println(
                "Average revenue: " +
                money(SalesMeasures.averageRevenue().evaluate(
                    service, all
                ))
            );

            System.out.println(
                "Completed revenue: " +
                money(SalesMeasures.completedRevenue().evaluate(
                    service, all
                ))
            );

            System.out.println("\nREGIONAL REVENUE");

            service.regionalRevenue().forEach(
                (region, value) ->
                    System.out.println(region + ": " + money(value))
            );

            System.out.println("\nCATEGORY REVENUE");

            service.categoryRevenue().forEach(
                (category, value) ->
                    System.out.println(category + ": " + money(value))
            );

            System.out.println("\nEMPTY FILTER RESULT");

            Filter impossible = new Filter(
                Column.REGION,
                Operator.EQUALS,
                "ANTARCTICA"
            );

            FilterContext empty = all.add(impossible);

            System.out.println("SUM: " +
                money(service.sumRevenue(empty)));

            System.out.println("AVERAGE: " +
                money(service.averageRevenue(empty)));

            System.out.println("COUNT: " +
                service.count(Column.REVENUE, empty));

            System.out.println("DISTINCTCOUNT: " +
                service.distinctCount(Column.CUSTOMER_ID, empty));

            System.out.println("\nVALIDATION");

            if (service.sumRevenue(all).compareTo(
                new BigDecimal("6600.00")) != 0) {
                throw new AnalyticsException("SUM assertion failed.");
            }

            if (service.count(Column.REVENUE, all) != 9) {
                throw new AnalyticsException("COUNT assertion failed.");
            }

            if (service.distinctCount(
                Column.CUSTOMER_ID, all
            ) != 7) {
                throw new AnalyticsException(
                    "DISTINCTCOUNT assertion failed."
                );
            }

            if (service.totalTransactions() != 10) {
                throw new AnalyticsException(
                    "Transaction count assertion failed."
                );
            }

            System.out.println("All assertions passed.");

        } catch (AnalyticsException error) {
            System.err.println(
                "Enterprise analytics failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
