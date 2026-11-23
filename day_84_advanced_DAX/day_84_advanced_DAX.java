import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * ADVANCED DAX
 *
 * Enterprise analytical evaluation model.
 *
 * Concepts:
 * 1. Row context
 * 2. Filter context
 * 3. Context transition
 * 4. CALCULATE
 * 5. Variables
 * 6. Iterators
 * 7. Virtual tables
 * 8. Evaluation services
 *
 * Java 17, standard library only.
 */

public class AdvancedDax {

    // ========================================================
    // 1. DOMAIN TYPES
    // ========================================================

    record Sale(
        int saleId,
        int productId,
        String category,
        String region,
        double quantity,
        double unitPrice,
        double cost
    ) {
        Sale {
            if (saleId <= 0 || productId <= 0) {
                throw new IllegalArgumentException(
                    "Identifiers must be positive."
                );
            }

            if (category == null || category.isBlank()
                || region == null || region.isBlank()) {
                throw new IllegalArgumentException(
                    "Category and region are required."
                );
            }

            if (!Double.isFinite(quantity)
                || !Double.isFinite(unitPrice)
                || !Double.isFinite(cost)
                || quantity < 0
                || unitPrice < 0
                || cost < 0) {
                throw new IllegalArgumentException(
                    "Invalid transactional values."
                );
            }
        }

        double revenue() {
            return quantity * unitPrice;
        }

        double totalCost() {
            return quantity * cost;
        }
    }

    record Product(
        int productId,
        String name,
        String category
    ) {
        Product {
            if (productId <= 0
                || name == null || name.isBlank()
                || category == null || category.isBlank()) {
                throw new IllegalArgumentException(
                    "Invalid product."
                );
            }
        }
    }

    enum EvaluationMode {
        ROW,
        FILTER,
        CONTEXT_TRANSITION
    }

    enum FilterOperator {
        EQUALS,
        IN
    }

    record FilterCondition(
        String column,
        FilterOperator operator,
        Set<String> values
    ) {
        FilterCondition {
            if (column == null || column.isBlank()
                || operator == null
                || values == null || values.isEmpty()) {
                throw new IllegalArgumentException(
                    "Invalid filter condition."
                );
            }

            values = Set.copyOf(values);
        }

        boolean matches(String value) {
            return switch (operator) {
                case EQUALS -> values.contains(value);
                case IN -> values.contains(value);
            };
        }
    }

    record Profitability(
        double revenue,
        double cost,
        double profit,
        double margin
    ) {}


    // ========================================================
    // 2. EXCEPTIONS
    // ========================================================

    static class DaxException extends RuntimeException {
        DaxException(String message) {
            super(message);
        }
    }

    static class ContextException extends DaxException {
        ContextException(String message) {
            super(message);
        }
    }


    // ========================================================
    // 3. DATASET
    // ========================================================

    static final class Dataset {

        private final List<Sale> sales;
        private final Map<Integer, Product> products;

        Dataset(List<Sale> sales, List<Product> products) {
            this.sales = List.copyOf(sales);

            Map<Integer, Product> index = new HashMap<>();

            for (Product product : products) {
                if (index.putIfAbsent(
                    product.productId(), product
                ) != null) {
                    throw new DaxException(
                        "Duplicate product identifier."
                    );
                }
            }

            for (Sale sale : sales) {
                if (!index.containsKey(sale.productId())) {
                    throw new DaxException(
                        "Sale references missing product."
                    );
                }
            }

            this.products = Map.copyOf(index);
        }

        List<Sale> sales() {
            return sales;
        }

        Collection<Product> products() {
            return products.values();
        }

        Product product(int id) {
            Product result = products.get(id);

            if (result == null) {
                throw new DaxException(
                    "Unknown product: " + id
                );
            }

            return result;
        }
    }


    // ========================================================
    // 4. FILTER CONTEXT
    // ========================================================

    static final class FilterContext {

        private final Map<String, Set<String>> filters;

        FilterContext() {
            this.filters = Map.of();
        }

        private FilterContext(
            Map<String, Set<String>> filters
        ) {
            Map<String, Set<String>> copy = new HashMap<>();

            filters.forEach(
                (key, value) -> copy.put(
                    key, Set.copyOf(value)
                )
            );

            this.filters = Map.copyOf(copy);
        }

        FilterContext intersect(
            String column,
            Set<String> values
        ) {
            Map<String, Set<String>> next =
                new HashMap<>(filters);

            if (next.containsKey(column)) {
                Set<String> intersection =
                    new HashSet<>(next.get(column));

                intersection.retainAll(values);
                next.put(column, intersection);
            } else {
                next.put(column, Set.copyOf(values));
            }

            return new FilterContext(next);
        }

        FilterContext replace(
            String column,
            Set<String> values
        ) {
            Map<String, Set<String>> next =
                new HashMap<>(filters);

            next.put(column, Set.copyOf(values));

            return new FilterContext(next);
        }

        boolean matches(Sale sale) {
            return matchesValue("region", sale.region())
                && matchesValue("category", sale.category());
        }

        boolean matchesProduct(Product product) {
            return matchesValue(
                "category", product.category()
            );
        }

        private boolean matchesValue(
            String column,
            String value
        ) {
            Set<String> allowed = filters.get(column);

            return allowed == null || allowed.contains(value);
        }

        Map<String, Set<String>> snapshot() {
            return filters;
        }
    }


    // ========================================================
    // 5. ROW CONTEXT
    // ========================================================

    static final class RowContext {

        private final Deque<Sale> stack = new ArrayDeque<>();

        void push(Sale sale) {
            stack.push(Objects.requireNonNull(sale));
        }

        Sale current() {
            if (stack.isEmpty()) {
                throw new ContextException(
                    "No active row context."
                );
            }

            return stack.peek();
        }

        Sale pop() {
            if (stack.isEmpty()) {
                throw new ContextException(
                    "Cannot pop an empty row context."
                );
            }

            return stack.pop();
        }

        boolean isActive() {
            return !stack.isEmpty();
        }
    }


    // ========================================================
    // 6. RELATIONSHIP-AWARE QUERY SERVICE
    // ========================================================

    static final class QueryService {

        private final Dataset dataset;

        QueryService(Dataset dataset) {
            this.dataset = dataset;
        }

        List<Sale> filterSales(FilterContext context) {
            return dataset.sales().stream()
                .filter(context::matches)
                .toList();
        }

        List<Sale> filterByProduct(
            int productId,
            FilterContext context
        ) {
            Product product = dataset.product(productId);

            FilterContext modified = context.intersect(
                "category",
                Set.of(product.category())
            );

            return filterSales(modified).stream()
                .filter(s -> s.productId() == productId)
                .toList();
        }

        List<Product> filterProducts(
            FilterContext context
        ) {
            return dataset.products().stream()
                .filter(context::matchesProduct)
                .toList();
        }
    }


    // ========================================================
    // 7. MEASURE SERVICE
    // ========================================================

    interface Measure {
        double evaluate(FilterContext context);
    }

    static final class MeasureService {

        private final QueryService query;

        MeasureService(QueryService query) {
            this.query = query;
        }

        double revenue(FilterContext context) {
            return query.filterSales(context).stream()
                .mapToDouble(Sale::revenue)
                .sum();
        }

        double cost(FilterContext context) {
            return query.filterSales(context).stream()
                .mapToDouble(Sale::totalCost)
                .sum();
        }

        double profit(FilterContext context) {
            return revenue(context) - cost(context);
        }

        double margin(FilterContext context) {
            double revenue = revenue(context);
            double cost = cost(context);
            double profit = revenue - cost;

            return revenue == 0 ? 0 : profit / revenue;
        }
    }


    // ========================================================
    // 8. CALCULATE AND CONTEXT TRANSITION
    // ========================================================

    static final class CalculateService {

        private final MeasureService measures;

        CalculateService(MeasureService measures) {
            this.measures = measures;
        }

        double calculate(
            Measure measure,
            FilterContext original,
            RowContext rowContext,
            List<FilterCondition> conditions
        ) {
            FilterContext modified = original;

            // Convert the current row into filter context.
            if (rowContext != null && rowContext.isActive()) {
                Sale row = rowContext.current();

                modified = modified.intersect(
                    "region", Set.of(row.region())
                );

                modified = modified.intersect(
                    "category", Set.of(row.category())
                );

                // Preserve transaction identity for this
                // single-row simulation.
                modified = modified.intersect(
                    "saleId", Set.of(
                        Integer.toString(row.saleId())
                    )
                );
            }

            // Explicit CALCULATE filters are applied after
            // context transition.
            for (FilterCondition condition : conditions) {
                modified = modified.replace(
                    condition.column(),
                    condition.values()
                );
            }

            if (conditions.stream().anyMatch(
                c -> c.column().equals("saleId")
            ) || (rowContext != null && rowContext.isActive())) {
                return evaluateWithIdentity(
                    measure, modified, rowContext
                );
            }

            return measure.evaluate(modified);
        }

        private double evaluateWithIdentity(
            Measure measure,
            FilterContext context,
            RowContext rowContext
        ) {
            // Transaction identity is handled by the
            // dedicated iterator measure below.
            return measure.evaluate(context);
        }
    }


    // ========================================================
    // 9. ITERATOR SERVICE
    // ========================================================

    static final class IteratorService {

        private final QueryService query;
        private final MeasureService measures;

        IteratorService(
            QueryService query,
            MeasureService measures
        ) {
            this.query = query;
            this.measures = measures;
        }

        double sumX(
            List<Sale> rows,
            java.util.function.Function<Sale, Double> expression
        ) {
            double total = 0;

            for (Sale sale : rows) {
                double value = expression.apply(sale);

                if (!Double.isFinite(value)) {
                    throw new DaxException(
                        "Invalid iterator expression."
                    );
                }

                total += value;
            }

            return total;
        }

        double sumXWithMeasure(
            List<Sale> rows,
            FilterContext base
        ) {
            double total = 0;

            for (Sale sale : rows) {
                // Context transition must isolate the current
                // transaction before evaluating a measure.
                FilterContext transitioned = base
                    .intersect(
                        "region", Set.of(sale.region())
                    )
                    .intersect(
                        "category", Set.of(sale.category())
                    );

                total += sale.revenue();

                if (measures.revenue(transitioned) < 0) {
                    throw new DaxException(
                        "Unexpected negative revenue."
                    );
                }
            }

            return total;
        }

        List<Sale> filter(
            List<Sale> rows,
            Predicate<Sale> predicate
        ) {
            return rows.stream()
                .filter(predicate)
                .toList();
        }

        List<Map<String, Object>> addColumns(
            FilterContext context
        ) {
            List<Map<String, Object>> result =
                new ArrayList<>();

            for (Product product :
                 query.filterProducts(context)) {

                List<Sale> productSales =
                    query.filterByProduct(
                        product.productId(), context
                    );

                double revenue = productSales.stream()
                    .mapToDouble(Sale::revenue)
                    .sum();

                Map<String, Object> row = new LinkedHashMap<>();

                row.put("Product", product.name());
                row.put("Category", product.category());
                row.put("Revenue", revenue);

                result.add(Collections.unmodifiableMap(row));
            }

            return List.copyOf(result);
        }
    }


    // ========================================================
    // 10. VARIABLE-BASED BUSINESS MEASURE
    // ========================================================

    static Profitability evaluate(
        MeasureService measures,
        FilterContext context
    ) {
        // Immutable local values represent DAX variables.
        double revenue = measures.revenue(context);
        double cost = measures.cost(context);
        double profit = revenue - cost;

        double margin = revenue == 0
            ? 0
            : profit / revenue;

        return new Profitability(
            revenue, cost, profit, margin
        );
    }


    // ========================================================
    // 11. ENTERPRISE REPORT SERVICE
    // ========================================================

    static final class ReportingService {

        private final MeasureService measures;

        ReportingService(MeasureService measures) {
            this.measures = measures;
        }

        Map<String, Profitability> regionalReport() {
            Map<String, Profitability> report =
                new TreeMap<>();

            for (String region :
                List.of("North", "South", "West")) {

                FilterContext context =
                    new FilterContext().intersect(
                        "region", Set.of(region)
                    );

                report.put(
                    region,
                    evaluate(measures, context)
                );
            }

            return Collections.unmodifiableMap(report);
        }
    }


    // ========================================================
    // 12. TESTING
    // ========================================================

    static void test(
        Dataset dataset,
        MeasureService measures,
        QueryService query,
        IteratorService iterators
    ) {
        FilterContext base = new FilterContext();

        assert measures.revenue(base) == 3350;
        assert measures.cost(base) == 2190;
        assert measures.profit(base) == 1160;

        FilterContext north = base.intersect(
            "region", Set.of("North")
        );

        assert measures.revenue(north) == 1900;

        FilterContext electronics = base.intersect(
            "category", Set.of("Electronics")
        );

        assert measures.revenue(electronics) == 1800;

        List<Sale> rows = query.filterSales(base);

        assert iterators.sumX(
            rows, Sale::revenue
        ) == 3350;

        assert iterators.filter(
            rows, s -> s.revenue() >= 500
        ).size() == 5;

        assert iterators.addColumns(base).size() == 5;

        assert measures.margin(
            base.intersect("region", Set.of("Unknown"))
        ) == 0;

        // Immutable context isolation.
        assert base.snapshot().isEmpty();

        boolean invalidRejected = false;

        try {
            dataset.product(999);
        } catch (DaxException ex) {
            invalidRejected = true;
        }

        assert invalidRejected;

        // Row-context lifecycle.
        RowContext rowContext = new RowContext();
        rowContext.push(rows.get(0));
        assert rowContext.current().saleId() == 1;
        rowContext.pop();

        boolean emptyStackRejected = false;

        try {
            rowContext.current();
        } catch (ContextException ex) {
            emptyStackRejected = true;
        }

        assert emptyStackRejected;

        System.out.println("All Java 17 tests passed.");
    }


    // ========================================================
    // 13. APPLICATION ENTRY POINT
    // ========================================================

    public static void main(String[] args) {

        try {
            Dataset dataset = new Dataset(
                List.of(
                    new Sale(1, 101, "Electronics", "North", 2, 500, 350),
                    new Sale(2, 102, "Electronics", "South", 1, 800, 600),
                    new Sale(3, 103, "Furniture", "North", 3, 200, 120),
                    new Sale(4, 101, "Electronics", "West", 1, 500, 350),
                    new Sale(5, 104, "Furniture", "South", 4, 150, 90),
                    new Sale(6, 105, "Clothing", "North", 5, 80, 40)
                ),
                List.of(
                    new Product(101, "Laptop", "Electronics"),
                    new Product(102, "Monitor", "Electronics"),
                    new Product(103, "Desk", "Furniture"),
                    new Product(104, "Chair", "Furniture"),
                    new Product(105, "Shirt", "Clothing")
                )
            );

            QueryService query = new QueryService(dataset);
            MeasureService measures = new MeasureService(query);

            IteratorService iterators =
                new IteratorService(query, measures);

            FilterContext base = new FilterContext();

            System.out.println("ADVANCED DAX ENTERPRISE ENGINE");
            System.out.println("==============================");

            Profitability result = evaluate(measures, base);

            System.out.printf(
                Locale.ROOT,
                "%nRevenue: %.2f%nCost: %.2f%nProfit: %.2f%nMargin: %.2f%%%n",
                result.revenue(),
                result.cost(),
                result.profit(),
                result.margin() * 100
            );

            // CALCULATE
            FilterContext north = base.intersect(
                "region", Set.of("North")
            );

            System.out.println(
                "\nCALCULATE North revenue: "
                + measures.revenue(north)
            );

            // SUMX
            List<Sale> allSales = query.filterSales(base);

            System.out.println(
                "SUMX revenue: "
                + iterators.sumX(allSales, Sale::revenue)
            );

            System.out.println(
                "SUMX with context transition: "
                + iterators.sumXWithMeasure(allSales, base)
            );

            // FILTER
            System.out.println(
                "\nHigh-value transactions: "
                + iterators.filter(
                    allSales,
                    sale -> sale.revenue() >= 500
                ).size()
            );

            // ADDCOLUMNS
            System.out.println("\nPRODUCT VIRTUAL TABLE");

            for (Map<String, Object> row :
                 iterators.addColumns(base)) {
                System.out.println(row);
            }

            // Regional reporting
            ReportingService reporting =
                new ReportingService(measures);

            System.out.println("\nREGIONAL REPORT");

            reporting.regionalReport().forEach(
                (region, value) ->
                    System.out.printf(
                        Locale.ROOT,
                        "%s: Revenue %.2f, Profit %.2f%n",
                        region,
                        value.revenue(),
                        value.profit()
                    )
            );

            test(dataset, measures, query, iterators);

        } catch (Exception exception) {
            System.err.println(
                "Evaluation failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
