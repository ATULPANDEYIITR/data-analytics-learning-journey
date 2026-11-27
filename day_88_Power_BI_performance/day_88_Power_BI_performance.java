import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * Power BI Performance Engineering
 *
 * Enterprise-oriented semantic model and performance
 * governance application.
 *
 * Java 17
 * No third-party dependencies.
 *
 * Covers:
 * - Semantic model governance
 * - Star schema validation
 * - Storage mode policies
 * - DAX optimization analysis
 * - Query execution metrics
 * - Performance thresholds
 * - Workload management
 * - Immutable evaluation results
 * - Enterprise reporting
 */

public class PowerBIPerformance {

    // ========================================================
    // 1. ENUMERATIONS
    // ========================================================

    enum StorageMode {
        IMPORT,
        DIRECTQUERY,
        DUAL,
        DIRECTLAKE
    }

    enum TableRole {
        FACT,
        DIMENSION,
        BRIDGE
    }

    enum Severity {
        CRITICAL,
        HIGH,
        MEDIUM,
        LOW
    }

    enum DaxPattern {
        SIMPLE_AGGREGATION,
        ROW_ITERATION,
        FILTER_ALL,
        VARIABLE_REUSE,
        PREAGGREGATED
    }

    enum QueryStatus {
        PENDING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    // ========================================================
    // 2. CUSTOM EXCEPTIONS
    // ========================================================

    static class ModelValidationException
            extends RuntimeException {

        ModelValidationException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException
            extends RuntimeException {

        PolicyViolationException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 3. VALIDATION UTILITIES
    // ========================================================

    static void requireName(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ModelValidationException(
                field + " cannot be empty"
            );
        }
    }

    static void requireNonNegative(
            double value,
            String field) {

        if (!Double.isFinite(value) || value < 0) {
            throw new ModelValidationException(
                field + " must be finite and non-negative"
            );
        }
    }

    static double ratio(double numerator, double denominator) {
        return denominator == 0
            ? 0
            : numerator / denominator;
    }

    // ========================================================
    // 4. COLUMN RECORD
    // ========================================================

    record Column(
        String name,
        String dataType,
        long cardinality,
        boolean used,
        boolean key
    ) {

        Column {
            requireName(name, "Column name");
            requireName(dataType, "Data type");

            if (cardinality < 0) {
                throw new ModelValidationException(
                    "Cardinality cannot be negative"
                );
            }

            if (!Set.of(
                "integer",
                "decimal",
                "string",
                "date",
                "boolean"
            ).contains(dataType)) {
                throw new ModelValidationException(
                    "Unsupported data type: " + dataType
                );
            }
        }

        void validateAgainstRows(long rows) {
            if (cardinality > rows) {
                throw new ModelValidationException(
                    "Column cardinality exceeds table rows: "
                    + name
                );
            }
        }
    }

    // ========================================================
    // 5. TABLE DOMAIN OBJECT
    // ========================================================

    static final class ModelTable {

        private final String name;
        private final TableRole role;
        private final long rows;
        private final StorageMode storageMode;
        private final List<Column> columns;
        private final boolean queryFolding;

        ModelTable(
            String name,
            TableRole role,
            long rows,
            StorageMode storageMode,
            List<Column> columns,
            boolean queryFolding
        ) {
            requireName(name, "Table name");

            if (rows < 0) {
                throw new ModelValidationException(
                    "Row count cannot be negative"
                );
            }

            this.name = name;
            this.role = Objects.requireNonNull(role);
            this.rows = rows;
            this.storageMode =
                Objects.requireNonNull(storageMode);

            this.columns = List.copyOf(columns);
            this.queryFolding = queryFolding;

            Set<String> names = new HashSet<>();

            for (Column column : this.columns) {
                column.validateAgainstRows(rows);

                if (!names.add(column.name())) {
                    throw new ModelValidationException(
                        "Duplicate column: " + column.name()
                    );
                }
            }
        }

        String name() {
            return name;
        }

        TableRole role() {
            return role;
        }

        long rows() {
            return rows;
        }

        StorageMode storageMode() {
            return storageMode;
        }

        List<Column> columns() {
            return columns;
        }

        boolean queryFolding() {
            return queryFolding;
        }

        List<Column> unusedColumns() {
            return columns.stream()
                .filter(column ->
                    !column.used() && !column.key()
                )
                .toList();
        }

        double estimateMemoryMB() {
            if (
                storageMode == StorageMode.DIRECTQUERY ||
                storageMode == StorageMode.DIRECTLAKE
            ) {
                return 0;
            }

            double bytes = 0;

            for (Column column : columns) {
                int bits = Math.max(
                    1,
                    (int) Math.ceil(
                        Math.log(
                            Math.max(2, column.cardinality())
                        ) / Math.log(2)
                    )
                );

                double encoded =
                    Math.ceil(rows * bits / 8.0);

                double dictionary =
                    column.cardinality() *
                    (
                        column.dataType().equals("string")
                            ? 24
                            : 8
                    );

                bytes += encoded + dictionary;
            }

            return bytes / (1024.0 * 1024.0);
        }
    }

    // ========================================================
    // 6. RELATIONSHIP RECORD
    // ========================================================

    record Relationship(
        String fromTable,
        String fromColumn,
        String toTable,
        String toColumn,
        String cardinality,
        boolean bidirectional
    ) {

        Relationship {
            requireName(fromTable, "Source table");
            requireName(fromColumn, "Source column");
            requireName(toTable, "Target table");
            requireName(toColumn, "Target column");

            if (!Set.of(
                "OneToOne",
                "OneToMany",
                "ManyToOne",
                "ManyToMany"
            ).contains(cardinality)) {
                throw new ModelValidationException(
                    "Invalid relationship cardinality"
                );
            }
        }
    }

    // ========================================================
    // 7. SEMANTIC MODEL
    // ========================================================

    static final class SemanticModel {

        private final String name;

        private final Map<String, ModelTable> tables =
            new HashMap<>();

        private final List<Relationship> relationships =
            new ArrayList<>();

        SemanticModel(String name) {
            requireName(name, "Model name");
            this.name = name;
        }

        void addTable(ModelTable table) {
            if (tables.putIfAbsent(
                table.name(),
                table
            ) != null) {
                throw new ModelValidationException(
                    "Duplicate table: " + table.name()
                );
            }
        }

        void addRelationship(Relationship relationship) {

            ModelTable source =
                tables.get(relationship.fromTable());

            ModelTable target =
                tables.get(relationship.toTable());

            if (source == null || target == null) {
                throw new ModelValidationException(
                    "Unknown relationship table"
                );
            }

            boolean sourceColumnExists =
                source.columns().stream().anyMatch(
                    c -> c.name().equals(
                        relationship.fromColumn()
                    )
                );

            boolean targetColumnExists =
                target.columns().stream().anyMatch(
                    c -> c.name().equals(
                        relationship.toColumn()
                    )
                );

            if (!sourceColumnExists || !targetColumnExists) {
                throw new ModelValidationException(
                    "Unknown relationship column"
                );
            }

            relationships.add(relationship);
        }

        Map<String, ModelTable> tables() {
            return Map.copyOf(tables);
        }

        List<Relationship> relationships() {
            return List.copyOf(relationships);
        }

        double estimatedMemoryMB() {
            return tables.values().stream()
                .mapToDouble(ModelTable::estimateMemoryMB)
                .sum();
        }

        Map<String, Object> statistics() {

            long rows = tables.values().stream()
                .mapToLong(ModelTable::rows)
                .sum();

            int columns = tables.values().stream()
                .mapToInt(t -> t.columns().size())
                .sum();

            return Map.of(
                "model", name,
                "tables", tables.size(),
                "relationships", relationships.size(),
                "rows", rows,
                "columns", columns,
                "estimatedMemoryMB",
                Math.round(estimatedMemoryMB() * 100.0) / 100.0
            );
        }
    }

    // ========================================================
    // 8. PERFORMANCE FINDING
    // ========================================================

    record Finding(
        String category,
        String subject,
        Severity severity,
        String description,
        String recommendation
    ) {}

    // ========================================================
    // 9. MODEL GOVERNANCE SERVICE
    // ========================================================

    static final class ModelGovernanceService {

        List<Finding> inspect(SemanticModel model) {

            List<Finding> findings = new ArrayList<>();

            for (ModelTable table : model.tables().values()) {

                if (!table.unusedColumns().isEmpty()) {
                    findings.add(new Finding(
                        "Model Size",
                        table.name(),
                        Severity.HIGH,
                        "Unused columns detected",
                        "Remove unused fields from the model"
                    ));
                }

                if (
                    table.role() == TableRole.FACT &&
                    table.rows() > 1_000_000 &&
                    !table.queryFolding()
                ) {
                    findings.add(new Finding(
                        "Refresh",
                        table.name(),
                        Severity.HIGH,
                        "Large fact table lacks query folding",
                        "Push supported transformations to the source"
                    ));
                }

                for (Column column : table.columns()) {
                    if (
                        column.dataType().equals("string") &&
                        column.cardinality() > 50_000
                    ) {
                        findings.add(new Finding(
                            "Cardinality",
                            table.name() + "." + column.name(),
                            Severity.MEDIUM,
                            "High-cardinality text field",
                            "Review necessity and storage representation"
                        ));
                    }
                }
            }

            for (
                Relationship relationship :
                model.relationships()
            ) {
                if (relationship.bidirectional()) {
                    findings.add(new Finding(
                        "Relationships",
                        relationship.fromTable(),
                        Severity.MEDIUM,
                        "Bidirectional relationship detected",
                        "Review single-direction filtering"
                    ));
                }

                if (
                    relationship.cardinality().equals(
                        "ManyToMany"
                    )
                ) {
                    findings.add(new Finding(
                        "Relationships",
                        relationship.fromTable(),
                        Severity.HIGH,
                        "Many-to-many relationship detected",
                        "Evaluate explicit bridge-table design"
                    ));
                }
            }

            return List.copyOf(findings);
        }
    }

    // ========================================================
    // 10. STORAGE MODE POLICY
    // ========================================================

    record StorageDecision(
        String tableName,
        StorageMode mode,
        String rationale,
        String risk
    ) {}

    static final class StoragePolicyService {

        StorageDecision evaluate(ModelTable table) {

            String rationale;
            String risk;

            switch (table.storageMode()) {

                case IMPORT -> {
                    rationale =
                        "In-memory analytical execution";
                    risk =
                        "Refresh duration and memory consumption";
                }

                case DIRECTQUERY -> {
                    rationale =
                        "Queries execute against the source";
                    risk =
                        "Source latency and concurrency";
                }

                case DUAL -> {
                    rationale =
                        "Context-dependent Import or DirectQuery behavior";
                    risk =
                        "Composite-model execution complexity";
                }

                case DIRECTLAKE -> {
                    rationale =
                        "Direct access through supported lake storage";
                    risk =
                        "Capacity, compatibility, and fallback behavior";
                }

                default -> throw new IllegalStateException(
                    "Unknown storage mode"
                );
            }

            return new StorageDecision(
                table.name(),
                table.storageMode(),
                rationale,
                risk
            );
        }
    }

    // ========================================================
    // 11. DAX MEASURE ANALYSIS
    // ========================================================

    record DaxMeasure(
        String name,
        String expression,
        DaxPattern pattern,
        long iterations,
        int repeatedExpressions
    ) {

        DaxMeasure {
            requireName(name, "Measure name");
            requireName(expression, "DAX expression");

            if (iterations < 0 || repeatedExpressions < 0) {
                throw new ModelValidationException(
                    "Invalid DAX complexity metadata"
                );
            }
        }
    }

    static final class DaxAnalysisService {

        List<String> analyze(DaxMeasure measure) {

            List<String> findings = new ArrayList<>();

            switch (measure.pattern()) {

                case ROW_ITERATION -> findings.add(
                    "Review iterator cost and test an equivalent "
                    + "storage-engine aggregation."
                );

                case FILTER_ALL -> findings.add(
                    "Review broad filter construction and "
                    + "filter context preservation."
                );

                case VARIABLE_REUSE -> findings.add(
                    "Variables may reduce repeated evaluation "
                    + "within an equivalent evaluation context."
                );

                case PREAGGREGATED -> findings.add(
                    "Check aggregation grain and filter coverage."
                );

                case SIMPLE_AGGREGATION -> findings.add(
                    "Simple aggregation pattern detected."
                );
            }

            if (measure.iterations() > 1_000_000) {
                findings.add(
                    "Large iterator workload requires profiling."
                );
            }

            if (measure.repeatedExpressions() > 1) {
                findings.add(
                    "Repeated expression evaluation detected."
                );
            }

            return List.copyOf(findings);
        }
    }

    // ========================================================
    // 12. QUERY METRICS
    // ========================================================

    record QueryMetrics(
        String queryName,
        double storageEngineMs,
        double formulaEngineMs,
        double sourceMs,
        double visualRenderMs,
        long rowsScanned,
        long rowsReturned,
        boolean cacheHit
    ) {

        QueryMetrics {
            requireName(queryName, "Query name");

            requireNonNegative(
                storageEngineMs,
                "Storage Engine time"
            );

            requireNonNegative(
                formulaEngineMs,
                "Formula Engine time"
            );

            requireNonNegative(sourceMs, "Source time");

            requireNonNegative(
                visualRenderMs,
                "Visual rendering time"
            );

            if (rowsScanned < 0 || rowsReturned < 0) {
                throw new ModelValidationException(
                    "Invalid row counts"
                );
            }

            if (rowsReturned > rowsScanned) {
                throw new ModelValidationException(
                    "Returned rows exceed scanned rows"
                );
            }
        }

        double totalMs() {
            return storageEngineMs +
                formulaEngineMs +
                sourceMs +
                visualRenderMs;
        }

        double formulaShare() {
            return ratio(formulaEngineMs, totalMs());
        }
    }

    // ========================================================
    // 13. QUERY POLICY SERVICE
    // ========================================================

    record QueryPolicy(
        double maxFormulaShare,
        double maxSourceMs,
        double maxVisualMs
    ) {

        QueryPolicy {
            if (
                maxFormulaShare < 0 ||
                maxFormulaShare > 1
            ) {
                throw new ModelValidationException(
                    "Formula share must be between 0 and 1"
                );
            }

            requireNonNegative(maxSourceMs, "Source threshold");
            requireNonNegative(maxVisualMs, "Visual threshold");
        }
    }

    record QueryEvaluation(
        String queryName,
        double totalMs,
        boolean passed,
        List<String> violations
    ) {}

    static final class QueryEvaluationService {

        private final QueryPolicy policy;

        QueryEvaluationService(QueryPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        QueryEvaluation evaluate(QueryMetrics query) {

            List<String> violations = new ArrayList<>();

            if (
                query.formulaShare() >
                policy.maxFormulaShare()
            ) {
                violations.add(
                    "Formula Engine contribution exceeds threshold"
                );
            }

            if (query.sourceMs() > policy.maxSourceMs()) {
                violations.add(
                    "Source execution exceeds threshold"
                );
            }

            if (
                query.visualRenderMs() >
                policy.maxVisualMs()
            ) {
                violations.add(
                    "Visual rendering exceeds threshold"
                );
            }

            return new QueryEvaluation(
                query.queryName(),
                query.totalMs(),
                violations.isEmpty(),
                List.copyOf(violations)
            );
        }
    }

    // ========================================================
    // 14. QUERY WORKLOAD SERVICE
    // ========================================================

    record QueryTask(
        String id,
        double estimatedMs,
        int priority,
        QueryStatus status
    ) {

        QueryTask {
            requireName(id, "Task ID");
            requireNonNegative(
                estimatedMs,
                "Estimated duration"
            );
            Objects.requireNonNull(status);
        }
    }

    static final class WorkloadService {

        private final List<QueryTask> tasks =
            new ArrayList<>();

        void submit(QueryTask task) {

            if (tasks.stream().anyMatch(
                existing -> existing.id().equals(task.id())
            )) {
                throw new ModelValidationException(
                    "Duplicate query task"
                );
            }

            tasks.add(task);
        }

        List<QueryTask> prioritized() {

            return tasks.stream()
                .sorted(
                    Comparator
                        .comparingInt(QueryTask::priority)
                        .reversed()
                        .thenComparingDouble(
                            QueryTask::estimatedMs
                        )
                )
                .toList();
        }
    }

    // ========================================================
    // 15. SAMPLE ENTERPRISE MODEL
    // ========================================================

    static SemanticModel buildSampleModel() {

        SemanticModel model = new SemanticModel(
            "Enterprise Sales Analytics"
        );

        model.addTable(
            new ModelTable(
                "Sales",
                TableRole.FACT,
                2_000_000,
                StorageMode.IMPORT,
                List.of(
                    new Column(
                        "SalesID", "integer",
                        2_000_000, true, true
                    ),
                    new Column(
                        "ProductKey", "integer",
                        5_000, true, false
                    ),
                    new Column(
                        "DateKey", "integer",
                        1_825, true, false
                    ),
                    new Column(
                        "SalesAmount", "decimal",
                        250_000, true, false
                    ),
                    new Column(
                        "TransactionReference", "string",
                        1_900_000, true, false
                    ),
                    new Column(
                        "UnusedDescription", "string",
                        2_000, false, false
                    )
                ),
                true
            )
        );

        model.addTable(
            new ModelTable(
                "Product",
                TableRole.DIMENSION,
                5_000,
                StorageMode.IMPORT,
                List.of(
                    new Column(
                        "ProductKey", "integer",
                        5_000, true, true
                    ),
                    new Column(
                        "Category", "string",
                        12, true, false
                    )
                ),
                true
            )
        );

        model.addTable(
            new ModelTable(
                "Date",
                TableRole.DIMENSION,
                1_825,
                StorageMode.IMPORT,
                List.of(
                    new Column(
                        "DateKey", "integer",
                        1_825, true, true
                    ),
                    new Column(
                        "Year", "integer",
                        5, true, false
                    )
                ),
                true
            )
        );

        model.addRelationship(
            new Relationship(
                "Sales",
                "ProductKey",
                "Product",
                "ProductKey",
                "ManyToOne",
                false
            )
        );

        model.addRelationship(
            new Relationship(
                "Sales",
                "DateKey",
                "Date",
                "DateKey",
                "ManyToOne",
                false
            )
        );

        return model;
    }

    // ========================================================
    // 16. REPORTING
    // ========================================================

    static void printFindings(List<Finding> findings) {

        System.out.println("\nMODEL FINDINGS");

        for (Finding finding : findings) {
            System.out.println(
                "[" + finding.severity() + "] " +
                finding.category() + " | " +
                finding.subject()
            );

            System.out.println(
                "Finding: " + finding.description()
            );

            System.out.println(
                "Action: " + finding.recommendation()
            );
        }
    }

    static void printQueryEvaluation(
        QueryEvaluation evaluation
    ) {
        System.out.println(
            "\nQuery: " + evaluation.queryName()
        );

        System.out.println(
            "Duration: " + evaluation.totalMs() + " ms"
        );

        System.out.println(
            "Policy: " +
            (evaluation.passed() ? "PASS" : "FAIL")
        );

        evaluation.violations().forEach(
            violation -> System.out.println(
                "- " + violation
            )
        );
    }

    // ========================================================
    // 17. TESTS
    // ========================================================

    static void runTests() {

        if (ratio(10, 0) != 0) {
            throw new AssertionError("Safe ratio failed");
        }

        QueryMetrics metrics = new QueryMetrics(
            "Test Query",
            100,
            50,
            0,
            20,
            10_000,
            10,
            false
        );

        if (metrics.totalMs() != 170) {
            throw new AssertionError(
                "Query duration calculation failed"
            );
        }

        boolean rejected = false;

        try {
            requireNonNegative(-1, "Test");
        } catch (ModelValidationException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError(
                "Negative values must be rejected"
            );
        }

        System.out.println(
            "All Java validation tests passed."
        );
    }

    // ========================================================
    // 18. APPLICATION ENTRY POINT
    // ========================================================

    public static void main(String[] args) {

        try {

            runTests();

            SemanticModel model = buildSampleModel();

            System.out.println(
                "\nPOWER BI ENTERPRISE PERFORMANCE REPORT"
            );

            System.out.println(model.statistics());

            ModelGovernanceService governance =
                new ModelGovernanceService();

            printFindings(
                governance.inspect(model)
            );

            StoragePolicyService storagePolicy =
                new StoragePolicyService();

            System.out.println("\nSTORAGE MODE ASSESSMENTS");

            model.tables().values().forEach(table -> {
                System.out.println(
                    storagePolicy.evaluate(table)
                );
            });

            DaxAnalysisService daxService =
                new DaxAnalysisService();

            DaxMeasure measure = new DaxMeasure(
                "Extended Revenue",
                "SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])",
                DaxPattern.ROW_ITERATION,
                2_000_000,
                1
            );

            System.out.println("\nDAX ANALYSIS");

            daxService.analyze(measure).forEach(
                System.out::println
            );

            QueryEvaluationService evaluator =
                new QueryEvaluationService(
                    new QueryPolicy(
                        0.40,
                        500,
                        300
                    )
                );

            List<QueryMetrics> queries = List.of(
                new QueryMetrics(
                    "Monthly Sales",
                    120, 80, 0, 100,
                    2_000_000, 24, false
                ),
                new QueryMetrics(
                    "Customer Detail",
                    180, 350, 700, 120,
                    500_000, 250, false
                ),
                new QueryMetrics(
                    "Product Summary",
                    90, 25, 0, 70,
                    200_000, 20, true
                )
            );

            System.out.println(
                "\nQUERY PERFORMANCE EVALUATION"
            );

            queries.stream()
                .map(evaluator::evaluate)
                .forEach(
                    PowerBIPerformance::printQueryEvaluation
                );

            WorkloadService workload =
                new WorkloadService();

            workload.submit(
                new QueryTask(
                    "Q-101", 350, 2, QueryStatus.PENDING
                )
            );

            workload.submit(
                new QueryTask(
                    "Q-102", 100, 5, QueryStatus.PENDING
                )
            );

            workload.submit(
                new QueryTask(
                    "Q-103", 200, 3, QueryStatus.PENDING
                )
            );

            System.out.println("\nPRIORITIZED WORKLOAD");

            workload.prioritized().forEach(
                System.out::println
            );

        } catch (RuntimeException exception) {

            System.err.println(
                "Application error: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
