import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * DAX FUNDAMENTALS: ENTERPRISE ANALYTICAL MODEL
 *
 * Implements selected DAX concepts:
 * - Measures
 * - Calculated columns
 * - Calculated tables
 * - Row context
 * - Filter context
 * - Context transition
 * - CALCULATE
 * - FILTER
 * - ALL
 * - VALUES
 * - DISTINCTCOUNT
 * - SUMX
 *
 * This is a Java simulation of selected DAX semantics,
 * not a complete DAX interpreter.
 *
 * Runtime: Java 17
 * Dependencies: None
 */

public class DAXFundamentals {

    enum Category {
        ELECTRONICS,
        FURNITURE,
        STATIONERY
    }

    enum Profitability {
        HIGH,
        STANDARD
    }

    record Product(
        int id,
        String name,
        Category category,
        BigDecimal price
    ) {
        Product {
            if (id <= 0) {
                throw new IllegalArgumentException("Invalid product ID.");
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Product name is required.");
            }

            Objects.requireNonNull(category);
            Objects.requireNonNull(price);

            if (price.signum() < 0) {
                throw new IllegalArgumentException("Negative price.");
            }
        }
    }

    record Sale(
        int id,
        int productId,
        LocalDate date,
        int quantity,
        BigDecimal unitCost
    ) {
        Sale {
            if (id <= 0 || productId <= 0 || quantity < 0) {
                throw new IllegalArgumentException("Invalid sale values.");
            }

            Objects.requireNonNull(date);
            Objects.requireNonNull(unitCost);

            if (unitCost.signum() < 0) {
                throw new IllegalArgumentException("Negative unit cost.");
            }
        }
    }

    record CalculatedColumn(
        int saleId,
        BigDecimal revenue,
        BigDecimal cost,
        BigDecimal profit,
        Profitability profitability
    ) {}

    record CategorySummary(
        Category category,
        long productCount
    ) {}

    record CategoryReport(
        Category category,
        BigDecimal sales,
        BigDecimal cost,
        BigDecimal profit,
        BigDecimal margin,
        long quantity
    ) {}

    static class DAXException extends RuntimeException {
        DAXException(String message) {
            super(message);
        }
    }

    // --------------------------------------------------------
    // Evaluation context
    // --------------------------------------------------------

    static final class EvaluationContext {
        private final Map<String, Set<Object>> filters;
        private final Map<String, Object> rowContext;

        EvaluationContext() {
            this(Map.of(), Map.of());
        }

        EvaluationContext(
            Map<String, Set<Object>> filters,
            Map<String, Object> rowContext
        ) {
            Map<String, Set<Object>> copy = new HashMap<>();

            filters.forEach(
                (key, value) -> copy.put(
                    key,
                    Collections.unmodifiableSet(new HashSet<>(value))
                )
            );

            this.filters = Collections.unmodifiableMap(copy);
            this.rowContext = Collections.unmodifiableMap(
                new HashMap<>(rowContext)
            );
        }

        EvaluationContext withFilter(
            String column,
            Set<Object> values
        ) {
            Map<String, Set<Object>> next = new HashMap<>(filters);
            next.put(column, values);

            return new EvaluationContext(next, rowContext);
        }

        EvaluationContext withoutFilter(String column) {
            Map<String, Set<Object>> next = new HashMap<>(filters);
            next.remove(column);

            return new EvaluationContext(next, rowContext);
        }

        EvaluationContext withRow(Map<String, Object> row) {
            return new EvaluationContext(filters, row);
        }

        Map<String, Set<Object>> filters() {
            return filters;
        }

        Map<String, Object> rowContext() {
            return rowContext;
        }
    }

    // --------------------------------------------------------
    // Functional measure interface
    // --------------------------------------------------------

    @FunctionalInterface
    interface Measure {
        BigDecimal evaluate(EvaluationContext context);
    }

    static final class AnalyticsService {

        private final Map<Integer, Product> products;
        private final List<Sale> sales;
        private final Map<String, Measure> measures;

        AnalyticsService(
            List<Product> productInput,
            List<Sale> salesInput
        ) {
            Map<Integer, Product> productMap = new HashMap<>();

            for (Product product : productInput) {
                if (productMap.putIfAbsent(
                    product.id(),
                    product
                ) != null) {
                    throw new DAXException("Duplicate product ID.");
                }
            }

            Set<Integer> saleIds = new HashSet<>();

            for (Sale sale : salesInput) {
                if (!saleIds.add(sale.id())) {
                    throw new DAXException("Duplicate sale ID.");
                }

                if (!productMap.containsKey(sale.productId())) {
                    throw new DAXException(
                        "Sale references an unknown product."
                    );
                }
            }

            this.products = Map.copyOf(productMap);
            this.sales = List.copyOf(salesInput);

            Map<String, Measure> registry = new LinkedHashMap<>();

            registry.put("Total Sales", this::totalSales);
            registry.put("Total Cost", this::totalCost);
            registry.put("Total Profit", this::totalProfit);
            registry.put("Total Quantity", this::totalQuantity);
            registry.put("Profit Margin", this::profitMargin);
            registry.put("Transaction Count", this::transactionCount);

            this.measures = Collections.unmodifiableMap(registry);
        }

        // ----------------------------------------------------
        // Relationships and filter propagation
        // ----------------------------------------------------

        private Object columnValue(Sale sale, String column) {
            Product product = products.get(sale.productId());

            return switch (column) {
                case "Sales.ID" -> sale.id();
                case "Sales.ProductID" -> sale.productId();
                case "Sales.Date" -> sale.date();
                case "Sales.Quantity" -> sale.quantity();
                case "Product.Name" -> product.name();
                case "Product.Category" -> product.category();
                case "Product.Price" -> product.price();
                default -> throw new DAXException(
                    "Unknown column: " + column
                );
            };
        }

        List<Sale> rows(EvaluationContext context) {
            return sales.stream()
                .filter(sale -> context.filters().entrySet().stream()
                    .allMatch(entry -> entry.getValue().contains(
                        columnValue(sale, entry.getKey())
                    )))
                .toList();
        }

        // ----------------------------------------------------
        // Measures
        // ----------------------------------------------------

        BigDecimal totalSales(EvaluationContext context) {
            return rows(context).stream()
                .map(sale -> products.get(sale.productId())
                    .price()
                    .multiply(BigDecimal.valueOf(sale.quantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        BigDecimal totalCost(EvaluationContext context) {
            return rows(context).stream()
                .map(sale -> sale.unitCost()
                    .multiply(BigDecimal.valueOf(sale.quantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        BigDecimal totalProfit(EvaluationContext context) {
            return totalSales(context).subtract(totalCost(context));
        }

        BigDecimal totalQuantity(EvaluationContext context) {
            return rows(context).stream()
                .map(sale -> BigDecimal.valueOf(sale.quantity()))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        BigDecimal transactionCount(EvaluationContext context) {
            return BigDecimal.valueOf(rows(context).size());
        }

        BigDecimal profitMargin(EvaluationContext context) {
            BigDecimal revenue = totalSales(context);

            if (revenue.signum() == 0) {
                return null;
            }

            return totalProfit(context)
                .multiply(BigDecimal.valueOf(100))
                .divide(revenue, 4, RoundingMode.HALF_UP);
        }

        BigDecimal evaluateMeasure(
            String name,
            EvaluationContext context
        ) {
            Measure measure = measures.get(name);

            if (measure == null) {
                throw new DAXException("Unknown measure: " + name);
            }

            return measure.evaluate(context);
        }

        Map<String, Measure> measureRegistry() {
            return measures;
        }

        // ----------------------------------------------------
        // CALCULATE and context transition
        // ----------------------------------------------------

        EvaluationContext calculateContext(
            EvaluationContext original,
            Map<String, Set<Object>> replacementFilters,
            Set<String> removeFilters
        ) {
            EvaluationContext result = original;

            for (String column : removeFilters) {
                result = result.withoutFilter(column);
            }

            for (Map.Entry<String, Set<Object>> entry
                : replacementFilters.entrySet()) {
                result = result.withFilter(
                    entry.getKey(),
                    entry.getValue()
                );
            }

            // Context transition converts row-context values
            // into filter-context values.
            for (Map.Entry<String, Object> entry
                : original.rowContext().entrySet()) {
                result = result.withFilter(
                    entry.getKey(),
                    Set.of(entry.getValue())
                );
            }

            return result;
        }

        BigDecimal calculate(
            Measure measure,
            EvaluationContext original,
            Map<String, Set<Object>> replacementFilters,
            Set<String> removeFilters
        ) {
            EvaluationContext updated = calculateContext(
                original,
                replacementFilters,
                removeFilters
            );

            return measure.evaluate(updated);
        }

        // ----------------------------------------------------
        // FILTER and SUMX
        // ----------------------------------------------------

        List<Sale> filter(
            EvaluationContext context,
            Predicate<Sale> predicate
        ) {
            return rows(context).stream()
                .filter(predicate)
                .toList();
        }

        BigDecimal sumX(
            List<Sale> input,
            java.util.function.Function<Sale, BigDecimal> expression
        ) {
            return input.stream()
                .map(expression)
                .peek(value -> {
                    if (value == null) {
                        throw new DAXException(
                            "SUMX expression returned null."
                        );
                    }
                })
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        // ----------------------------------------------------
        // Calculated columns
        // ----------------------------------------------------

        List<CalculatedColumn> calculatedColumns() {
            return sales.stream()
                .map(sale -> {
                    Product product = products.get(sale.productId());

                    BigDecimal quantity =
                        BigDecimal.valueOf(sale.quantity());

                    BigDecimal revenue = product.price().multiply(quantity);
                    BigDecimal cost = sale.unitCost().multiply(quantity);

                    Profitability profitability =
                        product.price().compareTo(
                            sale.unitCost().multiply(
                                BigDecimal.valueOf(1.5)
                            )
                        ) > 0
                            ? Profitability.HIGH
                            : Profitability.STANDARD;

                    return new CalculatedColumn(
                        sale.id(),
                        revenue,
                        cost,
                        revenue.subtract(cost),
                        profitability
                    );
                })
                .toList();
        }

        // ----------------------------------------------------
        // Calculated tables
        // ----------------------------------------------------

        List<CategorySummary> calculatedCategoryTable() {
            Map<Category, Long> grouped = products.values().stream()
                .collect(Collectors.groupingBy(
                    Product::category,
                    Collectors.counting()
                ));

            return grouped.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(entry -> new CategorySummary(
                    entry.getKey(),
                    entry.getValue()
                ))
                .toList();
        }

        List<Product> calculatedProductTable() {
            return products.values().stream()
                .sorted(java.util.Comparator.comparingInt(Product::id))
                .toList();
        }

        // ----------------------------------------------------
        // VALUES and DISTINCTCOUNT
        // ----------------------------------------------------

        Set<Object> values(
            String column,
            EvaluationContext context
        ) {
            return rows(context).stream()
                .map(sale -> columnValue(sale, column))
                .collect(Collectors.toCollection(TreeSet::new));
        }

        long distinctCount(
            String column,
            EvaluationContext context
        ) {
            return values(column, context).size();
        }

        // ----------------------------------------------------
        // Reporting
        // ----------------------------------------------------

        List<CategoryReport> categoryReport() {
            return products.values().stream()
                .map(Product::category)
                .distinct()
                .sorted()
                .map(category -> {
                    EvaluationContext context =
                        new EvaluationContext().withFilter(
                            "Product.Category",
                            Set.of(category)
                        );

                    return new CategoryReport(
                        category,
                        totalSales(context),
                        totalCost(context),
                        totalProfit(context),
                        profitMargin(context),
                        totalQuantity(context).longValue()
                    );
                })
                .toList();
        }
    }

    // --------------------------------------------------------
    // Sample enterprise data
    // --------------------------------------------------------

    static List<Product> sampleProducts() {
        return List.of(
            new Product(1, "Laptop", Category.ELECTRONICS,
                new BigDecimal("1000")),
            new Product(2, "Phone", Category.ELECTRONICS,
                new BigDecimal("500")),
            new Product(3, "Desk", Category.FURNITURE,
                new BigDecimal("300")),
            new Product(4, "Chair", Category.FURNITURE,
                new BigDecimal("200")),
            new Product(5, "Notebook", Category.STATIONERY,
                new BigDecimal("50"))
        );
    }

    static List<Sale> sampleSales() {
        return List.of(
            new Sale(101, 1, LocalDate.of(2026, 1, 10), 2,
                new BigDecimal("700")),
            new Sale(102, 2, LocalDate.of(2026, 1, 11), 4,
                new BigDecimal("300")),
            new Sale(103, 3, LocalDate.of(2026, 1, 12), 3,
                new BigDecimal("180")),
            new Sale(104, 4, LocalDate.of(2026, 1, 13), 5,
                new BigDecimal("120")),
            new Sale(105, 5, LocalDate.of(2026, 1, 14), 10,
                new BigDecimal("20")),
            new Sale(106, 1, LocalDate.of(2026, 2, 10), 1,
                new BigDecimal("700")),
            new Sale(107, 2, LocalDate.of(2026, 2, 11), 2,
                new BigDecimal("300")),
            new Sale(108, 3, LocalDate.of(2026, 2, 12), 4,
                new BigDecimal("180")),
            new Sale(109, 4, LocalDate.of(2026, 2, 13), 3,
                new BigDecimal("120")),
            new Sale(110, 5, LocalDate.of(2026, 2, 14), 5,
                new BigDecimal("20"))
        );
    }

    // --------------------------------------------------------
    // Validation
    // --------------------------------------------------------

    static void runTests(AnalyticsService service) {
        EvaluationContext all = new EvaluationContext();

        if (service.totalSales(all).compareTo(
            new BigDecimal("4995")
        ) != 0) {
            throw new AssertionError("Total sales test failed.");
        }

        if (service.totalCost(all).compareTo(
            new BigDecimal("2840")
        ) != 0) {
            throw new AssertionError("Total cost test failed.");
        }

        if (service.totalProfit(all).compareTo(
            new BigDecimal("2155")
        ) != 0) {
            throw new AssertionError("Total profit test failed.");
        }

        if (service.totalQuantity(all).compareTo(
            new BigDecimal("39")
        ) != 0) {
            throw new AssertionError("Quantity test failed.");
        }

        EvaluationContext electronics = all.withFilter(
            "Product.Category",
            Set.of(Category.ELECTRONICS)
        );

        if (service.totalSales(electronics).compareTo(
            new BigDecimal("3000")
        ) != 0) {
            throw new AssertionError("Category filter test failed.");
        }

        BigDecimal withoutCategory = service.calculate(
            service::totalSales,
            electronics,
            Map.of(),
            Set.of("Product.Category")
        );

        if (withoutCategory.compareTo(
            new BigDecimal("4995")
        ) != 0) {
            throw new AssertionError("ALL behavior test failed.");
        }

        if (service.distinctCount(
            "Product.Category",
            all
        ) != 3) {
            throw new AssertionError("DISTINCTCOUNT test failed.");
        }

        if (service.calculatedColumns().size() != 10) {
            throw new AssertionError("Calculated column test failed.");
        }

        if (service.calculatedCategoryTable().size() != 3) {
            throw new AssertionError("Calculated table test failed.");
        }

        if (service.profitMargin(
            all.withFilter("Sales.ID", Set.of(999))
        ) != null) {
            throw new AssertionError("Zero-sales test failed.");
        }
    }

    static String format(BigDecimal value) {
        return value == null
            ? "N/A"
            : value.setScale(2, RoundingMode.HALF_UP).toPlainString();
    }

    public static void main(String[] args) {
        try {
            AnalyticsService service = new AnalyticsService(
                sampleProducts(),
                sampleSales()
            );

            runTests(service);

            EvaluationContext all = new EvaluationContext();

            System.out.println("DAX FUNDAMENTALS");
            System.out.println("================");

            System.out.println("\nMEASURES");

            service.measureRegistry().forEach((name, measure) ->
                System.out.println(
                    name + ": " + format(measure.evaluate(all))
                )
            );

            System.out.println("\nCATEGORY REPORT");

            for (CategoryReport report : service.categoryReport()) {
                System.out.printf(
                    "%-15s Sales=%s Cost=%s Profit=%s Margin=%s%% Quantity=%d%n",
                    report.category(),
                    format(report.sales()),
                    format(report.cost()),
                    format(report.profit()),
                    format(report.margin()),
                    report.quantity()
                );
            }

            System.out.println("\nCALCULATED COLUMNS");

            service.calculatedColumns().stream()
                .limit(3)
                .forEach(System.out::println);

            System.out.println("\nCALCULATED TABLE");

            service.calculatedCategoryTable().forEach(
                System.out::println
            );

            System.out.println("\nCALCULATED PRODUCT TABLE");

            service.calculatedProductTable().forEach(
                System.out::println
            );

            System.out.println("\nFILTER CONTEXT");

            EvaluationContext electronics = all.withFilter(
                "Product.Category",
                Set.of(Category.ELECTRONICS)
            );

            System.out.println(
                "Electronics sales: "
                    + format(service.totalSales(electronics))
            );

            System.out.println("\nALL FILTER REMOVAL");

            System.out.println(
                "Sales without category filter: "
                    + format(service.calculate(
                        service::totalSales,
                        electronics,
                        Map.of(),
                        Set.of("Product.Category")
                    ))
            );

            System.out.println("\nSUMX");

            BigDecimal sumX = service.sumX(
                sampleSales(),
                sale -> {
                    Product product = sampleProducts().stream()
                        .filter(p -> p.id() == sale.productId())
                        .findFirst()
                        .orElseThrow();

                    return product.price().multiply(
                        BigDecimal.valueOf(sale.quantity())
                    );
                }
            );

            System.out.println("Row-by-row revenue: " + format(sumX));

            System.out.println("\nALL TESTS PASSED");

        } catch (Exception exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
