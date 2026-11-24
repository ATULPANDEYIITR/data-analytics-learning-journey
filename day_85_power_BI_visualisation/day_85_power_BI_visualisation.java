import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * Power BI Visualization: Enterprise Dashboard Platform
 *
 * Java 17 implementation.
 *
 * Capabilities:
 * - Immutable transaction records
 * - KPI cards
 * - Analytical tables and matrices
 * - Charts
 * - Geographic aggregations
 * - Typed slicer conditions
 * - Cross-filtering
 * - Drill-through navigation
 * - Dashboard bookmarks
 * - Asynchronous-compatible refresh boundary
 * - Validation and domain exceptions
 */

public class PowerBIDashboard {

    enum VisualType {
        CARD, TABLE, MATRIX, BAR, LINE, PIE, MAP
    }

    enum Measure {
        NET_SALES, GROSS_SALES, PROFIT, QUANTITY
    }

    enum Aggregation {
        SUM, COUNT, AVERAGE, MINIMUM, MAXIMUM, DISTINCT_COUNT
    }

    enum DashboardState {
        READY, FILTERED, NAVIGATING, REFRESHING, FAILED
    }

    static class DashboardException extends RuntimeException {
        DashboardException(String message) {
            super(message);
        }
    }

    record Transaction(
        int id,
        LocalDate transactionDate,
        String region,
        String city,
        String category,
        String product,
        String salesperson,
        int quantity,
        double unitPrice,
        double discount
    ) {
        Transaction {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Transaction ID must be positive."
                );
            }

            Objects.requireNonNull(transactionDate);
            Objects.requireNonNull(region);
            Objects.requireNonNull(city);
            Objects.requireNonNull(category);
            Objects.requireNonNull(product);
            Objects.requireNonNull(salesperson);

            if (region.isBlank() || city.isBlank() ||
                category.isBlank() || product.isBlank()) {
                throw new IllegalArgumentException(
                    "Dimension values cannot be blank."
                );
            }

            if (quantity <= 0) {
                throw new IllegalArgumentException(
                    "Quantity must be positive."
                );
            }

            if (!Double.isFinite(unitPrice) || unitPrice < 0) {
                throw new IllegalArgumentException(
                    "Invalid unit price."
                );
            }

            if (!Double.isFinite(discount) ||
                discount < 0 || discount > 1) {
                throw new IllegalArgumentException(
                    "Discount must be between 0 and 1."
                );
            }
        }

        double grossSales() {
            return quantity * unitPrice;
        }

        double netSales() {
            return grossSales() * (1 - discount);
        }

        double profit() {
            return netSales() * 0.25;
        }

        String month() {
            return transactionDate.format(
                DateTimeFormatter.ofPattern("yyyy-MM")
            );
        }

        double measure(Measure measure) {
            return switch (measure) {
                case NET_SALES -> netSales();
                case GROSS_SALES -> grossSales();
                case PROFIT -> profit();
                case QUANTITY -> quantity;
            };
        }
    }

    record DashboardFilter(
        String field,
        Object condition
    ) {
        DashboardFilter {
            if (field == null || field.isBlank()) {
                throw new IllegalArgumentException(
                    "Filter field is required."
                );
            }

            Objects.requireNonNull(condition);
        }

        boolean matches(Transaction transaction) {
            Object actual = dimension(transaction, field);

            if (condition instanceof Set<?> values) {
                return values.contains(actual);
            }

            if (condition instanceof Range range) {
                if (!(actual instanceof Number number)) {
                    throw new DashboardException(
                        "Range filters require numeric fields."
                    );
                }

                double value = number.doubleValue();

                return value >= range.minimum() &&
                       value <= range.maximum();
            }

            return Objects.equals(actual, condition);
        }
    }

    record Range(double minimum, double maximum) {
        Range {
            if (!Double.isFinite(minimum) ||
                !Double.isFinite(maximum) ||
                minimum > maximum) {
                throw new IllegalArgumentException(
                    "Invalid numeric range."
                );
            }
        }
    }

    record Bookmark(
        String name,
        List<DashboardFilter> filters,
        String selectedVisual,
        String description
    ) {
        Bookmark {
            Objects.requireNonNull(name);
            filters = List.copyOf(filters);
        }
    }

    record ChartPoint(String label, double value) {}

    record CardResult(
        String title,
        double value,
        int recordCount
    ) {}

    record TableRow(
        Map<String, String> dimensions,
        Map<String, Double> measures
    ) {
        TableRow {
            dimensions = Map.copyOf(dimensions);
            measures = Map.copyOf(measures);
        }
    }

    record MatrixResult(
        String rowField,
        String columnField,
        List<String> columns,
        List<Map<String, Double>> values
    ) {
        MatrixResult {
            columns = List.copyOf(columns);
            values = List.copyOf(values);
        }
    }

    record MapLocation(
        String region,
        String city,
        double sales,
        int transactionCount
    ) {}

    record DrillThroughResult(
        String targetPage,
        String sourceDimension,
        String sourceValue,
        List<Transaction> transactions
    ) {
        DrillThroughResult {
            transactions = List.copyOf(transactions);
        }
    }

    interface DashboardPolicy {
        boolean allowDrillThrough(
            String sourceField,
            String targetPage
        );

        boolean allowBookmarkRestore(String bookmarkName);
    }

    static class EnterpriseDashboardPolicy
        implements DashboardPolicy {

        private final Set<String> permittedFields;
        private final Set<String> permittedPages;

        EnterpriseDashboardPolicy(
            Set<String> permittedFields,
            Set<String> permittedPages
        ) {
            this.permittedFields = Set.copyOf(permittedFields);
            this.permittedPages = Set.copyOf(permittedPages);
        }

        @Override
        public boolean allowDrillThrough(
            String sourceField,
            String targetPage
        ) {
            return permittedFields.contains(sourceField) &&
                   permittedPages.contains(targetPage);
        }

        @Override
        public boolean allowBookmarkRestore(String bookmarkName) {
            return bookmarkName != null &&
                   !bookmarkName.isBlank();
        }
    }

    static final class DashboardRepository {
        private List<Transaction> records;
        private long revision = 1;

        DashboardRepository(List<Transaction> records) {
            replace(records, false);
        }

        synchronized List<Transaction> snapshot() {
            return List.copyOf(records);
        }

        synchronized long revision() {
            return revision;
        }

        synchronized void refresh(List<Transaction> replacement) {
            replace(replacement, true);
        }

        private void replace(
            List<Transaction> replacement,
            boolean incrementRevision
        ) {
            Objects.requireNonNull(replacement);

            if (replacement.isEmpty()) {
                throw new DashboardException(
                    "Dataset cannot be empty."
                );
            }

            Set<Integer> identifiers = new HashSet<>();

            for (Transaction transaction : replacement) {
                if (!identifiers.add(transaction.id())) {
                    throw new DashboardException(
                        "Duplicate transaction identifier."
                    );
                }
            }

            // State changes only after complete validation.
            records = List.copyOf(replacement);

            if (incrementRevision) {
                revision++;
            }
        }
    }

    static final class DashboardService {

        private final DashboardRepository repository;
        private final DashboardPolicy policy;

        private final Map<String, Bookmark> bookmarks =
            new LinkedHashMap<>();

        private final Deque<Bookmark> navigationHistory =
            new ArrayDeque<>();

        private List<DashboardFilter> filters = new ArrayList<>();

        private String selectedVisual;
        private DashboardState state = DashboardState.READY;

        DashboardService(
            DashboardRepository repository,
            DashboardPolicy policy
        ) {
            this.repository = repository;
            this.policy = policy;
        }

        DashboardState state() {
            return state;
        }

        private static Object dimension(
            Transaction transaction,
            String field
        ) {
            return switch (field) {
                case "region" -> transaction.region();
                case "city" -> transaction.city();
                case "category" -> transaction.category();
                case "product" -> transaction.product();
                case "salesperson" -> transaction.salesperson();
                case "month" -> transaction.month();
                case "date" -> transaction.transactionDate();
                case "quantity" -> transaction.quantity();
                case "netSales" -> transaction.netSales();
                case "profit" -> transaction.profit();
                default -> throw new DashboardException(
                    "Unknown dimension: " + field
                );
            };
        }

        private List<Transaction> filteredRecords() {
            List<DashboardFilter> currentFilters =
                List.copyOf(filters);

            return repository.snapshot().stream()
                .filter(transaction ->
                    currentFilters.stream().allMatch(
                        filter -> filter.matches(transaction)
                    )
                )
                .toList();
        }

        void setSingleValueSlicer(String field, Object value) {
            DashboardFilter filter = new DashboardFilter(
                field,
                value
            );

            // Validate the field before updating dashboard state.
            if (repository.snapshot().isEmpty()) {
                throw new DashboardException("Dataset unavailable.");
            }

            dimension(repository.snapshot().get(0), field);

            filters.removeIf(existing ->
                existing.field().equals(field)
            );

            filters.add(filter);
            state = DashboardState.FILTERED;
        }

        void setMultiValueSlicer(
            String field,
            Set<?> values
        ) {
            if (values == null || values.isEmpty()) {
                throw new DashboardException(
                    "Multi-value slicer requires values."
                );
            }

            if (repository.snapshot().isEmpty()) {
                throw new DashboardException("Dataset unavailable.");
            }

            dimension(repository.snapshot().get(0), field);

            filters.removeIf(existing ->
                existing.field().equals(field)
            );

            filters.add(new DashboardFilter(
                field,
                Set.copyOf(values)
            ));

            state = DashboardState.FILTERED;
        }

        void setNumericRange(
            String field,
            double minimum,
            double maximum
        ) {
            DashboardFilter filter = new DashboardFilter(
                field,
                new Range(minimum, maximum)
            );

            filters.removeIf(existing ->
                existing.field().equals(field)
            );

            filters.add(filter);
            state = DashboardState.FILTERED;
        }

        void clearFilters() {
            filters.clear();
            state = DashboardState.READY;
        }

        double aggregate(
            Measure measure,
            Aggregation aggregation
        ) {
            List<Transaction> records = filteredRecords();

            if (records.isEmpty()) {
                return 0;
            }

            List<Double> values = records.stream()
                .map(transaction -> transaction.measure(measure))
                .toList();

            return switch (aggregation) {
                case SUM -> values.stream()
                    .mapToDouble(Double::doubleValue)
                    .sum();

                case COUNT -> values.size();

                case AVERAGE -> values.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElse(0);

                case MINIMUM -> values.stream()
                    .mapToDouble(Double::doubleValue)
                    .min()
                    .orElse(0);

                case MAXIMUM -> values.stream()
                    .mapToDouble(Double::doubleValue)
                    .max()
                    .orElse(0);

                case DISTINCT_COUNT -> values.stream()
                    .distinct()
                    .count();
            };
        }

        CardResult card(Measure measure) {
            List<Transaction> records = filteredRecords();

            return new CardResult(
                "Total " + measure,
                aggregate(measure, Aggregation.SUM),
                records.size()
            );
        }

        List<TableRow> table(
            List<String> dimensions,
            List<Measure> measures
        ) {
            if (dimensions.isEmpty()) {
                throw new DashboardException(
                    "Table requires at least one dimension."
                );
            }

            Map<List<Object>, List<Transaction>> groups =
                filteredRecords().stream().collect(
                    Collectors.groupingBy(
                        transaction -> dimensions.stream()
                            .map(field ->
                                dimension(transaction, field)
                            )
                            .toList(),
                        TreeMapLikeComparator.INSTANCE
                    )
                );

            List<TableRow> result = new ArrayList<>();

            for (var entry : groups.entrySet()) {
                Map<String, String> dimensionValues =
                    new LinkedHashMap<>();

                for (int i = 0; i < dimensions.size(); i++) {
                    dimensionValues.put(
                        dimensions.get(i),
                        String.valueOf(entry.getKey().get(i))
                    );
                }

                Map<String, Double> measureValues =
                    new LinkedHashMap<>();

                for (Measure measure : measures) {
                    double total = entry.getValue().stream()
                        .mapToDouble(transaction ->
                            transaction.measure(measure)
                        )
                        .sum();

                    measureValues.put(
                        measure.name(),
                        total
                    );
                }

                result.add(new TableRow(
                    dimensionValues,
                    measureValues
                ));
            }

            return List.copyOf(result);
        }

        MatrixResult matrix(
            String rowField,
            String columnField,
            Measure measure
        ) {
            Map<String, Map<String, Double>> cells =
                new TreeMap<>();

            Set<String> columns = new TreeSet<>();

            for (Transaction transaction : filteredRecords()) {
                String row = String.valueOf(
                    dimension(transaction, rowField)
                );

                String column = String.valueOf(
                    dimension(transaction, columnField)
                );

                columns.add(column);

                cells.computeIfAbsent(
                    row,
                    ignored -> new TreeMap<>()
                ).merge(
                    column,
                    transaction.measure(measure),
                    Double::sum
                );
            }

            List<Map<String, Double>> rows = new ArrayList<>();

            for (Map<String, Double> values : cells.values()) {
                Map<String, Double> completed = new LinkedHashMap<>();

                for (String column : columns) {
                    completed.put(
                        column,
                        values.getOrDefault(column, 0.0)
                    );
                }

                rows.add(Collections.unmodifiableMap(completed));
            }

            return new MatrixResult(
                rowField,
                columnField,
                new ArrayList<>(columns),
                rows
            );
        }

        List<ChartPoint> chart(
            String dimension,
            Measure measure
        ) {
            Map<String, Double> groups = new TreeMap<>();

            for (Transaction transaction : filteredRecords()) {
                String key = String.valueOf(
                    dimension(transaction, dimension)
                );

                groups.merge(
                    key,
                    transaction.measure(measure),
                    Double::sum
                );
            }

            return groups.entrySet().stream()
                .map(entry -> new ChartPoint(
                    entry.getKey(),
                    entry.getValue()
                ))
                .toList();
        }

        List<MapLocation> map() {
            record LocationKey(String region, String city) {}

            Map<LocationKey, List<Transaction>> groups =
                new HashMap<>();

            for (Transaction transaction : filteredRecords()) {
                LocationKey key = new LocationKey(
                    transaction.region(),
                    transaction.city()
                );

                groups.computeIfAbsent(
                    key,
                    ignored -> new ArrayList<>()
                ).add(transaction);
            }

            return groups.entrySet().stream()
                .map(entry -> {
                    double total = entry.getValue().stream()
                        .mapToDouble(Transaction::netSales)
                        .sum();

                    return new MapLocation(
                        entry.getKey().region(),
                        entry.getKey().city(),
                        total,
                        entry.getValue().size()
                    );
                })
                .sorted(Comparator.comparing(MapLocation::region)
                    .thenComparing(MapLocation::city))
                .toList();
        }

        DrillThroughResult drillThrough(
            String sourceField,
            String sourceValue,
            String targetPage
        ) {
            if (!policy.allowDrillThrough(
                sourceField,
                targetPage
            )) {
                throw new DashboardException(
                    "Drill-through is not authorized."
                );
            }

            List<Transaction> details = filteredRecords().stream()
                .filter(transaction ->
                    String.valueOf(
                        dimension(transaction, sourceField)
                    ).equals(sourceValue)
                )
                .toList();

            if (details.isEmpty()) {
                throw new DashboardException(
                    "No drill-through records found."
                );
            }

            navigationHistory.push(new Bookmark(
                "navigation-state",
                filters,
                selectedVisual,
                "Previous dashboard context"
            ));

            state = DashboardState.NAVIGATING;

            return new DrillThroughResult(
                targetPage,
                sourceField,
                sourceValue,
                details
            );
        }

        void goBack() {
            if (navigationHistory.isEmpty()) {
                throw new DashboardException(
                    "No previous navigation state."
                );
            }

            Bookmark previous = navigationHistory.pop();

            filters = new ArrayList<>(previous.filters());
            selectedVisual = previous.selectedVisual();

            state = filters.isEmpty()
                ? DashboardState.READY
                : DashboardState.FILTERED;
        }

        void saveBookmark(
            String name,
            String description
        ) {
            if (name == null || name.isBlank()) {
                throw new DashboardException(
                    "Bookmark name is required."
                );
            }

            bookmarks.put(name, new Bookmark(
                name,
                filters,
                selectedVisual,
                description
            ));
        }

        void restoreBookmark(String name) {
            if (!policy.allowBookmarkRestore(name)) {
                throw new DashboardException(
                    "Bookmark restoration denied."
                );
            }

            Bookmark bookmark = bookmarks.get(name);

            if (bookmark == null) {
                throw new DashboardException(
                    "Bookmark not found."
                );
            }

            filters = new ArrayList<>(bookmark.filters());
            selectedVisual = bookmark.selectedVisual();

            state = filters.isEmpty()
                ? DashboardState.READY
                : DashboardState.FILTERED;
        }

        void selectVisual(String visualName) {
            if (visualName == null || visualName.isBlank()) {
                throw new DashboardException(
                    "Visual name cannot be empty."
                );
            }

            selectedVisual = visualName;
        }

        void refresh(List<Transaction> replacement) {
            state = DashboardState.REFRESHING;

            try {
                repository.refresh(replacement);
                state = filters.isEmpty()
                    ? DashboardState.READY
                    : DashboardState.FILTERED;
            } catch (RuntimeException exception) {
                state = DashboardState.FAILED;
                throw exception;
            }
        }

        int visibleRecordCount() {
            return filteredRecords().size();
        }
    }

    /*
     * TreeMap-style grouping for deterministic dimension ordering.
     */
    static class TreeMapLikeComparator {
        static final Comparator<List<Object>> INSTANCE =
            Comparator.comparing(
                list -> list.stream()
                    .map(String::valueOf)
                    .collect(Collectors.joining("|"))
            );
    }

    static List<Transaction> sampleData() {
        return List.of(
            new Transaction(
                1, LocalDate.parse("2026-01-05"),
                "North", "Delhi", "Electronics",
                "Laptop", "Amit", 2, 65000, 0.05
            ),
            new Transaction(
                2, LocalDate.parse("2026-01-12"),
                "North", "Lucknow", "Furniture",
                "Chair", "Neha", 5, 4500, 0.10
            ),
            new Transaction(
                3, LocalDate.parse("2026-02-08"),
                "South", "Bengaluru", "Electronics",
                "Mobile", "Rahul", 4, 30000, 0.08
            ),
            new Transaction(
                4, LocalDate.parse("2026-02-15"),
                "West", "Mumbai", "Clothing",
                "Jacket", "Priya", 8, 2500, 0.05
            ),
            new Transaction(
                5, LocalDate.parse("2026-03-03"),
                "East", "Kolkata", "Furniture",
                "Table", "Amit", 3, 12000, 0.12
            ),
            new Transaction(
                6, LocalDate.parse("2026-03-18"),
                "North", "Delhi", "Clothing",
                "Shirt", "Neha", 10, 1200, 0.02
            ),
            new Transaction(
                7, LocalDate.parse("2026-04-10"),
                "South", "Chennai", "Electronics",
                "Laptop", "Rahul", 1, 70000, 0.04
            ),
            new Transaction(
                8, LocalDate.parse("2026-04-20"),
                "West", "Pune", "Furniture",
                "Chair", "Priya", 6, 5000, 0.07
            ),
            new Transaction(
                9, LocalDate.parse("2026-05-05"),
                "East", "Kolkata", "Electronics",
                "Mobile", "Amit", 3, 28000, 0.06
            ),
            new Transaction(
                10, LocalDate.parse("2026-05-17"),
                "North", "Lucknow", "Clothing",
                "Jacket", "Neha", 4, 3000, 0.03
            )
        );
    }

    public static void main(String[] args) {
        DashboardRepository repository =
            new DashboardRepository(sampleData());

        DashboardPolicy policy =
            new EnterpriseDashboardPolicy(
                Set.of("region", "city", "category"),
                Set.of(
                    "Regional Details",
                    "Transaction Details"
                )
            );

        DashboardService dashboard =
            new DashboardService(repository, policy);

        System.out.println("POWER BI ENTERPRISE DASHBOARD");
        System.out.println("================================");

        System.out.println("\nKPI CARD");
        System.out.println(
            dashboard.card(Measure.NET_SALES)
        );

        System.out.println("\nTABLE");
        dashboard.table(
            List.of("region", "category"),
            List.of(Measure.NET_SALES, Measure.PROFIT)
        ).forEach(System.out::println);

        System.out.println("\nMATRIX");
        System.out.println(
            dashboard.matrix(
                "region",
                "category",
                Measure.NET_SALES
            )
        );

        System.out.println("\nBAR CHART");
        dashboard.chart(
            "category",
            Measure.NET_SALES
        ).forEach(System.out::println);

        System.out.println("\nLINE CHART");
        dashboard.chart(
            "month",
            Measure.NET_SALES
        ).forEach(System.out::println);

        System.out.println("\nPIE CHART DATA");
        dashboard.chart(
            "category",
            Measure.NET_SALES
        ).forEach(System.out::println);

        System.out.println("\nMAP DATA");
        dashboard.map().forEach(System.out::println);

        System.out.println("\nSLICER");
        dashboard.setMultiValueSlicer(
            "region",
            Set.of("North", "South")
        );

        dashboard.setSingleValueSlicer(
            "category",
            "Electronics"
        );

        System.out.println(
            dashboard.card(Measure.NET_SALES)
        );

        System.out.println("\nBOOKMARK");
        dashboard.selectVisual("Regional Analysis");
        dashboard.saveBookmark(
            "Regional_Electronics",
            "Electronics sales for selected regions"
        );

        dashboard.clearFilters();
        dashboard.restoreBookmark("Regional_Electronics");

        System.out.println(
            "Visible records: " +
            dashboard.visibleRecordCount()
        );

        System.out.println("\nDRILL-THROUGH");
        DrillThroughResult result = dashboard.drillThrough(
            "region",
            "North",
            "Transaction Details"
        );

        System.out.println(
            "Target: " + result.targetPage()
        );

        result.transactions().forEach(System.out::println);

        dashboard.goBack();

        System.out.println("\nREFRESH");
        dashboard.refresh(sampleData());

        System.out.println(
            "Dataset revision: " + repository.revision()
        );

        System.out.println(
            "Dashboard state: " + dashboard.state()
        );

        System.out.println("\nVALIDATION");

        try {
            dashboard.restoreBookmark("Unknown");
        } catch (DashboardException exception) {
            System.out.println(
                "Expected error: " + exception.getMessage()
            );
        }

        System.out.println("\nVISIBLE RECORDS");
        System.out.println(dashboard.visibleRecordCount());
    }
}
