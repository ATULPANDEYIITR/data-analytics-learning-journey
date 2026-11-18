import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * Enterprise Power Query simulation.
 *
 * Java 17
 *
 * Covers:
 * - Query lifecycle
 * - Data cleaning
 * - Type conversion
 * - Merge and append
 * - Query dependencies
 * - Transformation policies
 * - Validation and failure handling
 */

public class PowerQueryEnterprise {

    enum DataType {
        TEXT, INTEGER, DECIMAL, DATE, BOOLEAN
    }

    enum QueryStatus {
        CREATED, RUNNING, COMPLETED, FAILED
    }

    enum JoinType {
        INNER, LEFT, FULL
    }

    static class QueryException extends RuntimeException {
        QueryException(String message) {
            super(message);
        }

        QueryException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    record Customer(
        int customerId,
        String name,
        String region
    ) {}

    record Order(
        int orderId,
        int customerId,
        BigDecimal amount,
        LocalDate orderDate
    ) {}

    record QueryPolicy(
        boolean removeDuplicates,
        boolean rejectInvalidTypes,
        Set<String> requiredColumns
    ) {
        QueryPolicy {
            requiredColumns = Set.copyOf(requiredColumns);
        }
    }

    static final class DataTable {

        private final String name;
        private final List<String> columns;
        private final List<Map<String, Object>> rows;

        DataTable(
            String name,
            List<String> columns,
            List<Map<String, Object>> rows
        ) {
            this.name = Objects.requireNonNull(name);
            this.columns = List.copyOf(columns);

            List<Map<String, Object>> copied = new ArrayList<>();

            for (Map<String, Object> row : rows) {
                copied.add(
                    Collections.unmodifiableMap(
                        new LinkedHashMap<>(row)
                    )
                );
            }

            this.rows = List.copyOf(copied);
            validate();
        }

        String name() {
            return name;
        }

        List<String> columns() {
            return columns;
        }

        List<Map<String, Object>> rows() {
            return rows;
        }

        void validate() {
            if (columns.isEmpty()) {
                throw new QueryException("No columns defined.");
            }

            if (new HashSet<>(columns).size() != columns.size()) {
                throw new QueryException("Duplicate column names.");
            }

            for (Map<String, Object> row : rows) {
                if (!row.keySet().equals(new LinkedHashSet<>(columns))) {
                    throw new QueryException("Invalid row schema.");
                }
            }
        }

        void display() {
            System.out.println("\n" + name);

            System.out.println(String.join(" | ", columns));

            for (Map<String, Object> row : rows) {
                System.out.println(
                    columns.stream()
                        .map(column -> String.valueOf(row.get(column)))
                        .collect(Collectors.joining(" | "))
                );
            }

            System.out.println("Rows: " + rows.size());
        }
    }

    static final class TransformationService {

        private TransformationService() {}

        static String cleanText(String value) {
            if (value == null) return null;

            String cleaned = value.trim().replaceAll("\\s+", " ");

            return cleaned.isEmpty() ? null : cleaned;
        }

        static DataTable clean(
            DataTable table,
            QueryPolicy policy
        ) {
            List<Map<String, Object>> cleaned = new ArrayList<>();

            Set<String> seen = new HashSet<>();

            for (Map<String, Object> original : table.rows()) {
                Map<String, Object> row = new LinkedHashMap<>();

                for (String column : table.columns()) {
                    Object value = original.get(column);

                    if (value instanceof String text) {
                        value = cleanText(text);
                    }

                    row.put(column, value);
                }

                if (!row.keySet().containsAll(
                    policy.requiredColumns()
                )) {
                    throw new QueryException(
                        "Missing required columns."
                    );
                }

                String key = policy.requiredColumns().stream()
                    .sorted()
                    .map(column -> String.valueOf(row.get(column)))
                    .collect(Collectors.joining("|"));

                if (!policy.removeDuplicates() || seen.add(key)) {
                    cleaned.add(row);
                }
            }

            return new DataTable(
                table.name(),
                table.columns(),
                cleaned
            );
        }

        static Object convert(
            Object value,
            DataType type
        ) {
            if (value == null) return null;

            try {
                return switch (type) {
                    case TEXT -> value.toString();

                    case INTEGER -> {
                        String text = value.toString().trim();

                        if (!text.matches("-?\\d+")) {
                            throw new NumberFormatException();
                        }

                        yield Long.parseLong(text);
                    }

                    case DECIMAL ->
                        new BigDecimal(value.toString().trim());

                    case DATE ->
                        LocalDate.parse(value.toString());

                    case BOOLEAN -> {
                        String normalized = value.toString()
                            .toLowerCase();

                        if (List.of("true", "yes", "1")
                            .contains(normalized)) {
                            yield true;
                        }

                        if (List.of("false", "no", "0")
                            .contains(normalized)) {
                            yield false;
                        }

                        throw new IllegalArgumentException(
                            "Invalid boolean."
                        );
                    }
                };
            } catch (
                NumberFormatException |
                DateTimeParseException |
                IllegalArgumentException error
            ) {
                throw new QueryException(
                    "Type conversion failed for " + value,
                    error
                );
            }
        }

        static DataTable changeTypes(
            DataTable table,
            Map<String, DataType> schema,
            boolean strict
        ) {
            if (!table.columns().containsAll(schema.keySet())) {
                throw new QueryException("Unknown type column.");
            }

            List<Map<String, Object>> rows = new ArrayList<>();

            for (Map<String, Object> original : table.rows()) {
                Map<String, Object> row = new LinkedHashMap<>(original);

                for (Map.Entry<String, DataType> entry :
                    schema.entrySet()) {

                    try {
                        row.put(
                            entry.getKey(),
                            convert(
                                original.get(entry.getKey()),
                                entry.getValue()
                            )
                        );
                    } catch (QueryException error) {
                        if (strict) throw error;

                        row.put(entry.getKey(), null);
                    }
                }

                rows.add(row);
            }

            return new DataTable(table.name(), table.columns(), rows);
        }

        static DataTable filter(
            DataTable table,
            Predicate<Map<String, Object>> predicate
        ) {
            return new DataTable(
                table.name(),
                table.columns(),
                table.rows().stream()
                    .filter(predicate)
                    .toList()
            );
        }

        static DataTable addColumn(
            DataTable table,
            String column,
            java.util.function.Function<
                Map<String, Object>, Object
            > expression
        ) {
            if (table.columns().contains(column)) {
                throw new QueryException("Column already exists.");
            }

            List<String> columns = new ArrayList<>(table.columns());
            columns.add(column);

            List<Map<String, Object>> rows = table.rows().stream()
                .map(original -> {
                    Map<String, Object> row =
                        new LinkedHashMap<>(original);

                    row.put(column, expression.apply(original));

                    return row;
                })
                .toList();

            return new DataTable(table.name(), columns, rows);
        }

        static DataTable merge(
            DataTable left,
            DataTable right,
            String leftKey,
            String rightKey,
            JoinType joinType
        ) {
            if (!left.columns().contains(leftKey) ||
                !right.columns().contains(rightKey)) {
                throw new QueryException("Invalid merge key.");
            }

            List<String> rightColumns = right.columns().stream()
                .filter(column -> !column.equals(rightKey))
                .toList();

            Map<String, String> renamed = new LinkedHashMap<>();

            for (String column : rightColumns) {
                String output = left.columns().contains(column)
                    ? column + "_right"
                    : column;

                if (left.columns().contains(output) ||
                    renamed.containsValue(output)) {
                    throw new QueryException("Column collision.");
                }

                renamed.put(column, output);
            }

            Map<Object, List<Map<String, Object>>> index =
                new HashMap<>();

            for (Map<String, Object> row : right.rows()) {
                Object key = row.get(rightKey);

                if (key != null) {
                    index.computeIfAbsent(
                        key,
                        ignored -> new ArrayList<>()
                    ).add(row);
                }
            }

            List<String> columns = new ArrayList<>(left.columns());

            columns.addAll(renamed.values());

            List<Map<String, Object>> rows = new ArrayList<>();

            Set<Map<String, Object>> matched =
                Collections.newSetFromMap(new java.util.IdentityHashMap<>());

            for (Map<String, Object> leftRow : left.rows()) {
                Object key = leftRow.get(leftKey);

                List<Map<String, Object>> matches =
                    index.getOrDefault(key, List.of());

                if (matches.isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        Map<String, Object> output =
                            new LinkedHashMap<>(leftRow);

                        renamed.values().forEach(
                            column -> output.put(column, null)
                        );

                        rows.add(output);
                    }

                    continue;
                }

                for (Map<String, Object> rightRow : matches) {
                    matched.add(rightRow);

                    Map<String, Object> output =
                        new LinkedHashMap<>(leftRow);

                    renamed.forEach(
                        (original, target) ->
                            output.put(target, rightRow.get(original))
                    );

                    rows.add(output);
                }
            }

            if (joinType == JoinType.FULL) {
                for (Map<String, Object> rightRow : right.rows()) {
                    if (matched.contains(rightRow)) continue;

                    Map<String, Object> output = new LinkedHashMap<>();

                    left.columns().forEach(
                        column -> output.put(column, null)
                    );

                    renamed.forEach(
                        (original, target) ->
                            output.put(target, rightRow.get(original))
                    );

                    rows.add(output);
                }
            }

            return new DataTable(
                left.name() + "_merged",
                columns,
                rows
            );
        }

        static DataTable append(List<DataTable> tables) {
            if (tables.isEmpty()) {
                throw new QueryException("No tables to append.");
            }

            LinkedHashSet<String> columnSet = new LinkedHashSet<>();

            tables.forEach(
                table -> columnSet.addAll(table.columns())
            );

            List<String> columns = List.copyOf(columnSet);

            List<Map<String, Object>> rows = new ArrayList<>();

            for (DataTable table : tables) {
                for (Map<String, Object> original : table.rows()) {
                    Map<String, Object> output = new LinkedHashMap<>();

                    for (String column : columns) {
                        output.put(column, original.get(column));
                    }

                    rows.add(output);
                }
            }

            return new DataTable("appended", columns, rows);
        }

        static DataTable groupBy(
            DataTable table,
            String groupColumn,
            String valueColumn
        ) {
            Map<Object, BigDecimal> totals = new LinkedHashMap<>();

            for (Map<String, Object> row : table.rows()) {
                Object key = row.get(groupColumn);

                BigDecimal amount = new BigDecimal(
                    row.get(valueColumn).toString()
                );

                totals.merge(key, amount, BigDecimal::add);
            }

            List<Map<String, Object>> rows = totals.entrySet()
                .stream()
                .map(entry -> {
                    Map<String, Object> row = new LinkedHashMap<>();

                    row.put(groupColumn, entry.getKey());
                    row.put("total", entry.getValue());

                    return row;
                })
                .toList();

            return new DataTable(
                "grouped",
                List.of(groupColumn, "total"),
                rows
            );
        }
    }

    static final class Query {

        private final String name;
        private final List<String> dependencies;
        private final java.util.function.Function<
            Map<String, DataTable>, DataTable
        > transform;

        private QueryStatus status = QueryStatus.CREATED;

        Query(
            String name,
            List<String> dependencies,
            java.util.function.Function<
                Map<String, DataTable>, DataTable
            > transform
        ) {
            this.name = name;
            this.dependencies = List.copyOf(dependencies);
            this.transform = transform;
        }

        String name() {
            return name;
        }

        List<String> dependencies() {
            return dependencies;
        }

        QueryStatus status() {
            return status;
        }
    }

    static final class QueryEngine {

        private final Map<String, Query> queries =
            new LinkedHashMap<>();

        private final Map<String, DataTable> results =
            new LinkedHashMap<>();

        void register(Query query) {
            if (queries.containsKey(query.name())) {
                throw new QueryException("Duplicate query.");
            }

            queries.put(query.name(), query);
        }

        List<String> executionOrder() {
            Set<String> completed = new HashSet<>();
            Set<String> active = new HashSet<>();
            List<String> order = new ArrayList<>();

            for (String name : queries.keySet()) {
                visit(name, completed, active, order);
            }

            return order;
        }

        private void visit(
            String name,
            Set<String> completed,
            Set<String> active,
            List<String> order
        ) {
            if (!queries.containsKey(name)) {
                throw new QueryException("Unknown dependency: " + name);
            }

            if (active.contains(name)) {
                throw new QueryException("Circular dependency.");
            }

            if (completed.contains(name)) return;

            active.add(name);

            for (String dependency :
                queries.get(name).dependencies()) {
                visit(dependency, completed, active, order);
            }

            active.remove(name);
            completed.add(name);
            order.add(name);
        }

        Map<String, DataTable> execute() {
            for (String name : executionOrder()) {
                Query query = queries.get(name);
                query.status = QueryStatus.RUNNING;

                try {
                    Map<String, DataTable> input =
                        query.dependencies().stream()
                            .collect(Collectors.toMap(
                                dependency -> dependency,
                                dependency -> results.get(dependency)
                            ));

                    DataTable result = query.transform.apply(
                        Collections.unmodifiableMap(input)
                    );

                    result.validate();

                    results.put(name, result);
                    query.status = QueryStatus.COMPLETED;

                    System.out.println("Completed: " + name);

                } catch (RuntimeException error) {
                    query.status = QueryStatus.FAILED;

                    throw new QueryException(
                        "Query failed: " + name,
                        error
                    );
                }
            }

            return Collections.unmodifiableMap(results);
        }
    }

    private static DataTable sampleCustomers() {
        List<Map<String, Object>> rows = new ArrayList<>();

        rows.add(row(
            "customer_id", "1",
            "name", " Alice ",
            "region", "North"
        ));

        rows.add(row(
            "customer_id", "2",
            "name", "Bob",
            "region", "South"
        ));

        rows.add(row(
            "customer_id", "3",
            "name", "Carol",
            "region", "North"
        ));

        return new DataTable(
            "customers",
            List.of("customer_id", "name", "region"),
            rows
        );
    }

    private static DataTable sampleOrders() {
        List<Map<String, Object>> rows = new ArrayList<>();

        rows.add(row(
            "order_id", "101",
            "customer_id", "1",
            "amount", "1250.50",
            "order_date", "2026-01-10"
        ));

        rows.add(row(
            "order_id", "102",
            "customer_id", "2",
            "amount", "800.00",
            "order_date", "2026-01-12"
        ));

        rows.add(row(
            "order_id", "103",
            "customer_id", "1",
            "amount", "450.25",
            "order_date", "2026-02-02"
        ));

        rows.add(row(
            "order_id", "104",
            "customer_id", "99",
            "amount", "300.00",
            "order_date", "2026-02-05"
        ));

        return new DataTable(
            "orders",
            List.of(
                "order_id",
                "customer_id",
                "amount",
                "order_date"
            ),
            rows
        );
    }

    private static Map<String, Object> row(Object... values) {
        Map<String, Object> result = new LinkedHashMap<>();

        for (int i = 0; i < values.length; i += 2) {
            result.put(
                values[i].toString(),
                values[i + 1]
            );
        }

        return result;
    }

    public static void main(String[] args) {

        DataTable customers = sampleCustomers();
        DataTable orders = sampleOrders();

        QueryPolicy policy = new QueryPolicy(
            true,
            true,
            Set.of("customer_id")
        );

        customers = TransformationService.clean(
            customers,
            policy
        );

        orders = TransformationService.clean(
            orders,
            policy
        );

        customers = TransformationService.changeTypes(
            customers,
            Map.of(
                "customer_id", DataType.INTEGER,
                "name", DataType.TEXT,
                "region", DataType.TEXT
            ),
            true
        );

        orders = TransformationService.changeTypes(
            orders,
            Map.of(
                "order_id", DataType.INTEGER,
                "customer_id", DataType.INTEGER,
                "amount", DataType.DECIMAL,
                "order_date", DataType.DATE
            ),
            true
        );

        System.out.println("\n1. CLEANED DATA");
        customers.display();

        System.out.println("\n2. MERGE");
        DataTable merged = TransformationService.merge(
            orders,
            customers,
            "customer_id",
            "customer_id",
            JoinType.LEFT
        );
        merged.display();

        System.out.println("\n3. FILTER");
        DataTable filtered = TransformationService.filter(
            orders,
            row -> (BigDecimal) row.get("amount")
                .compareTo(new BigDecimal("500")) >= 0
        );
        filtered.display();

        System.out.println("\n4. APPEND");

        DataTable archived = new DataTable(
            "archived",
            orders.columns(),
            List.of(
                row(
                    "order_id", 90L,
                    "customer_id", 2L,
                    "amount", new BigDecimal("500.00"),
                    "order_date", LocalDate.of(2025, 12, 15)
                )
            )
        );

        DataTable appended = TransformationService.append(
            List.of(orders, archived)
        );

        appended.display();

        System.out.println("\n5. GROUPING");

        DataTable categorized = TransformationService.addColumn(
            appended,
            "category",
            row -> ((BigDecimal) row.get("amount"))
                .compareTo(new BigDecimal("1000")) >= 0
                    ? "High Value"
                    : "Standard"
        );

        TransformationService.groupBy(
            categorized,
            "category",
            "amount"
        ).display();

        System.out.println("\n6. DEPENDENCY ENGINE");

        QueryEngine engine = new QueryEngine();

        DataTable finalOrders = orders;

        engine.register(new Query(
            "source",
            List.of(),
            ignored -> finalOrders
        ));

        engine.register(new Query(
            "filtered",
            List.of("source"),
            input -> TransformationService.filter(
                input.get("source"),
                row -> ((BigDecimal) row.get("amount"))
                    .compareTo(new BigDecimal("500")) >= 0
            )
        ));

        engine.register(new Query(
            "summary",
            List.of("filtered"),
            input -> {
                DataTable source = input.get("filtered");

                BigDecimal total = source.rows().stream()
                    .map(row -> (BigDecimal) row.get("amount"))
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

                return new DataTable(
                    "summary",
                    List.of("order_count", "total_amount"),
                    List.of(
                        row("order_count", source.rows().size(),
                            "total_amount", total)
                    )
                );
            }
        ));

        Map<String, DataTable> results = engine.execute();

        results.get("summary").display();

        if (merged.rows().size() != 4 ||
            appended.rows().size() != 5) {
            throw new QueryException("Validation failed.");
        }

        System.out.println("\nAll enterprise validation checks passed.");
    }
}
