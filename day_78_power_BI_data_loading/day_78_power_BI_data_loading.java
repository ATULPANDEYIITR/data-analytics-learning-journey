import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import java.time.Instant;

import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;

/*
 * POWER BI DATA LOADING
 *
 * Enterprise-oriented data integration and semantic model.
 *
 * Java 17
 * No third-party dependencies.
 *
 * Features:
 * - CSV and Excel-exported CSV ingestion
 * - Database connector interface
 * - Web source configuration
 * - Data validation
 * - Import, DirectQuery, and Live Connection modes
 * - Connection governance
 * - Refresh coordination
 * - Audit records
 * - Failure handling
 * - Reporting
 */

public class PowerBIDataLoading {

    // -----------------------------------------------------
    // Enumerations
    // -----------------------------------------------------

    enum SourceType {
        CSV,
        EXCEL_EXPORT,
        DATABASE,
        WEB
    }

    enum StorageMode {
        IMPORT,
        DIRECT_QUERY,
        LIVE_CONNECTION
    }

    enum ConnectionState {
        CREATED,
        CONNECTED,
        LOADING,
        READY,
        FAILED,
        DISABLED
    }

    enum RefreshStatus {
        SUCCESS,
        FAILED
    }


    // -----------------------------------------------------
    // Exceptions
    // -----------------------------------------------------

    static class DataLoadingException
            extends RuntimeException {

        DataLoadingException(String message) {
            super(message);
        }

        DataLoadingException(
                String message,
                Throwable cause
        ) {
            super(message, cause);
        }
    }

    static class ValidationException
            extends DataLoadingException {

        ValidationException(String message) {
            super(message);
        }
    }

    static class ConnectionException
            extends DataLoadingException {

        ConnectionException(String message) {
            super(message);
        }
    }


    // -----------------------------------------------------
    // Immutable domain records
    // -----------------------------------------------------

    record SalesRecord(
            String product,
            int quantity,
            double revenue
    ) {

        SalesRecord {

            Objects.requireNonNull(product);

            product = product.trim();

            if (product.isEmpty()) {
                throw new ValidationException(
                        "Product cannot be empty."
                );
            }

            if (quantity < 0) {
                throw new ValidationException(
                        "Quantity cannot be negative."
                );
            }

            if (
                    !Double.isFinite(revenue) ||
                    revenue < 0
            ) {
                throw new ValidationException(
                        "Revenue must be finite and non-negative."
                );
            }

        }
    }


    record ConnectionConfig(
            String id,
            SourceType sourceType,
            String location,
            boolean enabled,
            int timeoutSeconds,
            Map<String, String> options
    ) {

        ConnectionConfig {

            if (
                    id == null ||
                    id.isBlank() ||
                    location == null ||
                    location.isBlank()
            ) {
                throw new ValidationException(
                        "Connection ID and location are required."
                );
            }

            Objects.requireNonNull(sourceType);

            if (timeoutSeconds <= 0) {
                throw new ValidationException(
                        "Timeout must be positive."
                );
            }

            options = Collections.unmodifiableMap(
                    new HashMap<>(
                            options == null
                                    ? Map.of()
                                    : options
                    )
            );
        }
    }


    record LoadResult(
            String connectionId,
            List<SalesRecord> records,
            int rejectedRows,
            Instant loadedAt
    ) {

        LoadResult {

            records = List.copyOf(records);

            if (rejectedRows < 0) {
                throw new ValidationException(
                        "Rejected row count cannot be negative."
                );
            }
        }
    }


    record RefreshAudit(
            String connectionId,
            String tableName,
            StorageMode storageMode,
            RefreshStatus status,
            int recordCount,
            Instant timestamp,
            String message
    ) {}


    // -----------------------------------------------------
    // Connection state
    // -----------------------------------------------------

    static class ConnectionContext {

        private final ConnectionConfig config;

        private volatile ConnectionState state;

        ConnectionContext(ConnectionConfig config) {

            this.config = config;

            this.state = config.enabled()
                    ? ConnectionState.CREATED
                    : ConnectionState.DISABLED;
        }

        ConnectionConfig config() {
            return config;
        }

        ConnectionState state() {
            return state;
        }

        void transition(ConnectionState next) {

            if (
                    state == ConnectionState.DISABLED &&
                    next != ConnectionState.DISABLED
            ) {
                throw new ConnectionException(
                        "Disabled connection cannot change state."
                );
            }

            state = next;
        }
    }


    // -----------------------------------------------------
    // Source adapter interface
    // -----------------------------------------------------

    interface SourceAdapter {

        List<Map<String, String>> read(
                ConnectionConfig configuration
        ) throws Exception;
    }


    // -----------------------------------------------------
    // CSV adapter
    // -----------------------------------------------------

    static class CSVAdapter implements SourceAdapter {

        private List<String> parseLine(String line) {

            List<String> fields = new ArrayList<>();

            StringBuilder current = new StringBuilder();

            boolean quoted = false;

            for (int i = 0; i < line.length(); i++) {

                char c = line.charAt(i);

                if (quoted) {

                    if (c == '"') {

                        if (
                                i + 1 < line.length() &&
                                line.charAt(i + 1) == '"'
                        ) {
                            current.append('"');
                            i++;
                        } else {
                            quoted = false;
                        }

                    } else {
                        current.append(c);
                    }

                } else if (c == '"') {

                    if (!current.isEmpty()) {
                        throw new ValidationException(
                                "Unexpected CSV quote."
                        );
                    }

                    quoted = true;

                } else if (c == ',') {

                    fields.add(current.toString());

                    current.setLength(0);

                } else {
                    current.append(c);
                }
            }

            if (quoted) {
                throw new ValidationException(
                        "Unclosed CSV quote."
                );
            }

            fields.add(current.toString());

            return fields;
        }

        @Override
        public List<Map<String, String>> read(
                ConnectionConfig configuration
        ) throws IOException {

            Path file = Path.of(
                    configuration.location()
            );

            if (!Files.isRegularFile(file)) {
                throw new ConnectionException(
                        "CSV source file does not exist."
                );
            }

            List<Map<String, String>> records =
                    new ArrayList<>();

            try (
                    BufferedReader reader = Files.newBufferedReader(
                            file,
                            StandardCharsets.UTF_8
                    )
            ) {

                String headerLine = reader.readLine();

                if (headerLine == null) {
                    throw new ValidationException(
                            "CSV file is empty."
                    );
                }

                List<String> headers = parseLine(headerLine)
                        .stream()
                        .map(value -> value.trim()
                                .toLowerCase()
                                .replaceAll("\\s+", "_"))
                        .toList();

                if (
                        headers.stream().anyMatch(String::isBlank) ||
                        new HashSet<>(headers).size() != headers.size()
                ) {
                    throw new ValidationException(
                            "Invalid or duplicate CSV headers."
                    );
                }

                String line;

                while ((line = reader.readLine()) != null) {

                    if (line.isBlank()) {
                        continue;
                    }

                    List<String> values = parseLine(line);

                    if (values.size() != headers.size()) {
                        throw new ValidationException(
                                "CSV column count mismatch."
                        );
                    }

                    Map<String, String> row =
                            new LinkedHashMap<>();

                    for (int i = 0; i < headers.size(); i++) {
                        row.put(
                                headers.get(i),
                                values.get(i)
                        );
                    }

                    records.add(row);
                }
            }

            return records;
        }
    }


    // -----------------------------------------------------
    // Database adapter contract
    // -----------------------------------------------------

    interface DatabaseAdapter extends SourceAdapter {

        List<Map<String, String>> executeReadOnly(
                String query
        );
    }


    static class InMemoryDatabaseAdapter
            implements DatabaseAdapter {

        private final Map<
                String,
                List<Map<String, String>>
        > tables = new ConcurrentHashMap<>();

        InMemoryDatabaseAdapter() {

            tables.put(
                    "sales",
                    List.of(
                            Map.of(
                                    "product", "Desktop",
                                    "quantity", "3",
                                    "revenue", "180000"
                            ),
                            Map.of(
                                    "product", "Printer",
                                    "quantity", "2",
                                    "revenue", "30000"
                            )
                    )
            );
        }

        @Override
        public List<Map<String, String>> executeReadOnly(
                String query
        ) {

            String normalized = query.trim();

            if (
                    !normalized.matches(
                            "(?i)^SELECT\\s+\\*\\s+FROM\\s+[a-zA-Z_][a-zA-Z0-9_]*;?$"
                    )
            ) {
                throw new ValidationException(
                        "Only SELECT * FROM table is supported."
                );
            }

            String table = normalized
                    .replaceFirst("(?i)^SELECT\\s+\\*\\s+FROM\\s+", "")
                    .replace(";", "")
                    .trim();

            List<Map<String, String>> rows =
                    tables.get(table);

            if (rows == null) {
                throw new ConnectionException(
                        "Database table does not exist."
                );
            }

            return rows.stream()
                    .map(HashMap::new)
                    .map(row -> (Map<String, String>) row)
                    .toList();
        }

        @Override
        public List<Map<String, String>> read(
                ConnectionConfig configuration
        ) {

            return executeReadOnly(
                    configuration.options().getOrDefault(
                            "query",
                            "SELECT * FROM sales"
                    )
            );
        }
    }


    // -----------------------------------------------------
    // Web connection validation
    // -----------------------------------------------------

    static class WebSourceValidator {

        static void validate(String url) {

            if (url == null || url.length() > 2048) {
                throw new ValidationException(
                        "Invalid web source URL."
                );
            }

            if (!url.startsWith("https://")) {
                throw new ValidationException(
                        "Web connections require HTTPS."
                );
            }
        }
    }


    // -----------------------------------------------------
    // Source registry
    // -----------------------------------------------------

    static class ConnectionRegistry {

        private final Map<
                String,
                ConnectionContext
        > contexts = new ConcurrentHashMap<>();

        void register(ConnectionConfig configuration) {

            ConnectionContext context =
                    new ConnectionContext(configuration);

            if (
                    contexts.putIfAbsent(
                            configuration.id(),
                            context
                    ) != null
            ) {
                throw new ValidationException(
                        "Duplicate connection ID."
                );
            }
        }

        ConnectionContext get(String id) {

            ConnectionContext context = contexts.get(id);

            if (context == null) {
                throw new ConnectionException(
                        "Unknown connection: " + id
                );
            }

            return context;
        }
    }


    // -----------------------------------------------------
    // Data transformation
    // -----------------------------------------------------

    static class DataTransformer {

        record TransformationResult(
                List<SalesRecord> valid,
                int rejected
        ) {}

        static TransformationResult transform(
                List<Map<String, String>> source
        ) {

            if (source.isEmpty()) {
                throw new ValidationException(
                        "Source contains no records."
                );
            }

            List<SalesRecord> valid =
                    new ArrayList<>();

            int rejected = 0;

            for (Map<String, String> row : source) {

                try {

                    SalesRecord record = new SalesRecord(
                            row.get("product"),
                            Integer.parseInt(
                                    row.get("quantity")
                            ),
                            Double.parseDouble(
                                    row.get("revenue")
                            )
                    );

                    valid.add(record);

                } catch (RuntimeException error) {

                    rejected++;
                }
            }

            if (valid.isEmpty()) {
                throw new ValidationException(
                        "No valid records remain."
                );
            }

            return new TransformationResult(
                    valid,
                    rejected
            );
        }
    }


    // -----------------------------------------------------
    // Loading service
    // -----------------------------------------------------

    static class DataLoadingService {

        private final ConnectionRegistry registry;

        private final Map<
                SourceType,
                SourceAdapter
        > adapters = new EnumMap<>(
                SourceType.class
        );

        DataLoadingService(
                ConnectionRegistry registry
        ) {

            this.registry = registry;

            adapters.put(
                    SourceType.CSV,
                    new CSVAdapter()
            );

            adapters.put(
                    SourceType.EXCEL_EXPORT,
                    new CSVAdapter()
            );

            adapters.put(
                    SourceType.DATABASE,
                    new InMemoryDatabaseAdapter()
            );
        }

        LoadResult load(String connectionId) {

            ConnectionContext context =
                    registry.get(connectionId);

            ConnectionConfig config =
                    context.config();

            if (!config.enabled()) {
                throw new ConnectionException(
                        "Connection is disabled."
                );
            }

            try {

                context.transition(
                        ConnectionState.CONNECTED
                );

                context.transition(
                        ConnectionState.LOADING
                );

                List<Map<String, String>> raw;

                if (config.sourceType() == SourceType.WEB) {

                    WebSourceValidator.validate(
                            config.location()
                    );

                    throw new ConnectionException(
                            "HTTP transport is not implemented "
                            + "in this standard-library example."
                    );
                }

                SourceAdapter adapter = adapters.get(
                        config.sourceType()
                );

                if (adapter == null) {
                    throw new ConnectionException(
                            "No adapter registered."
                    );
                }

                raw = adapter.read(config);

                var transformed =
                        DataTransformer.transform(raw);

                context.transition(
                        ConnectionState.READY
                );

                return new LoadResult(
                        connectionId,
                        transformed.valid(),
                        transformed.rejected(),
                        Instant.now()
                );

            } catch (Exception error) {

                context.transition(
                        ConnectionState.FAILED
                );

                if (
                        error instanceof DataLoadingException
                ) {
                    throw (DataLoadingException) error;
                }

                throw new DataLoadingException(
                        "Source loading failed: "
                        + error.getMessage(),
                        error
                );
            }
        }
    }


    // -----------------------------------------------------
    // Semantic model
    // -----------------------------------------------------

    static class SemanticModel {

        private final Map<
                String,
                List<SalesRecord>
        > tables = new ConcurrentHashMap<>();

        private final List<RefreshAudit> audit =
                Collections.synchronizedList(
                        new ArrayList<>()
                );

        private final AtomicBoolean refreshing =
                new AtomicBoolean(false);

        void importTable(
                String tableName,
                LoadResult result
        ) {

            if (
                    tableName == null ||
                    !tableName.matches(
                            "[a-zA-Z_][a-zA-Z0-9_]*"
                    )
            ) {
                throw new ValidationException(
                        "Invalid semantic table name."
                );
            }

            // Build the replacement before publishing it.
            List<SalesRecord> replacement =
                    List.copyOf(result.records());

            tables.put(
                    tableName,
                    replacement
            );

            audit.add(
                    new RefreshAudit(
                            result.connectionId(),
                            tableName,
                            StorageMode.IMPORT,
                            RefreshStatus.SUCCESS,
                            replacement.size(),
                            Instant.now(),
                            "Import completed."
                    )
            );
        }

        List<SalesRecord> getTable(String name) {

            List<SalesRecord> rows = tables.get(name);

            if (rows == null) {
                throw new DataLoadingException(
                        "Semantic table not found."
                );
            }

            return rows;
        }

        void directQuery(
                DataLoadingService service,
                String connectionId
        ) {

            LoadResult result = service.load(
                    connectionId
            );

            System.out.println(
                    "DirectQuery-style fresh records: "
                    + result.records().size()
            );
        }

        void liveConnection(boolean externalModelAvailable) {

            if (!externalModelAvailable) {
                throw new ConnectionException(
                        "External model is unavailable."
                );
            }

            System.out.println(
                    "Connected to external semantic model."
            );
        }

        void beginRefresh() {

            if (!refreshing.compareAndSet(false, true)) {
                throw new DataLoadingException(
                        "Refresh is already running."
                );
            }
        }

        void endRefresh() {
            refreshing.set(false);
        }

        List<RefreshAudit> auditRecords() {
            synchronized (audit) {
                return List.copyOf(audit);
            }
        }
    }


    // -----------------------------------------------------
    // Refresh orchestration
    // -----------------------------------------------------

    static class RefreshService {

        private final DataLoadingService loader;

        private final SemanticModel model;

        RefreshService(
                DataLoadingService loader,
                SemanticModel model
        ) {
            this.loader = loader;
            this.model = model;
        }

        RefreshAudit refresh(
                String connectionId,
                String tableName
        ) {

            model.beginRefresh();

            try {

                LoadResult result = loader.load(
                        connectionId
                );

                model.importTable(
                        tableName,
                        result
                );

                return new RefreshAudit(
                        connectionId,
                        tableName,
                        StorageMode.IMPORT,
                        RefreshStatus.SUCCESS,
                        result.records().size(),
                        Instant.now(),
                        "Refresh successful."
                );

            } finally {

                model.endRefresh();
            }
        }
    }


    // -----------------------------------------------------
    // Reporting
    // -----------------------------------------------------

    static class SalesAnalytics {

        record Report(
                int recordCount,
                long totalQuantity,
                double totalRevenue,
                Map<String, Double> revenueByProduct
        ) {}

        static Report calculate(
                List<SalesRecord> records
        ) {

            long quantity = 0;

            double revenue = 0;

            Map<String, Double> byProduct =
                    records.stream().collect(
                            Collectors.groupingBy(
                                    SalesRecord::product,
                                    Collectors.summingDouble(
                                            SalesRecord::revenue
                                    )
                            )
                    );

            for (SalesRecord record : records) {

                quantity += record.quantity();

                revenue += record.revenue();
            }

            return new Report(
                    records.size(),
                    quantity,
                    Math.round(revenue * 100.0) / 100.0,
                    Collections.unmodifiableMap(byProduct)
            );
        }
    }


    // -----------------------------------------------------
    // Main application
    // -----------------------------------------------------

    public static void main(String[] args) {

        Path directory = Path.of(
                "powerbi_java_demo"
        );

        Path csvFile = directory.resolve(
                "sales.csv"
        );

        try {

            Files.createDirectories(directory);

            Files.writeString(
                    csvFile,
                    """
                    product,quantity,revenue
                    Laptop,5,250000
                    Monitor,8,120000
                    Keyboard,20,40000
                    Mouse,-2,10000
                    """,
                    StandardCharsets.UTF_8
            );

            ConnectionRegistry registry =
                    new ConnectionRegistry();

            registry.register(
                    new ConnectionConfig(
                            "csv_sales",
                            SourceType.CSV,
                            csvFile.toString(),
                            true,
                            15,
                            Map.of()
                    )
            );

            registry.register(
                    new ConnectionConfig(
                            "database_sales",
                            SourceType.DATABASE,
                            "database",
                            true,
                            15,
                            Map.of(
                                    "query",
                                    "SELECT * FROM sales"
                            )
                    )
            );

            registry.register(
                    new ConnectionConfig(
                            "excel_export",
                            SourceType.EXCEL_EXPORT,
                            csvFile.toString(),
                            true,
                            15,
                            Map.of()
                    )
            );

            DataLoadingService loader =
                    new DataLoadingService(registry);

            SemanticModel model =
                    new SemanticModel();

            RefreshService refreshService =
                    new RefreshService(loader, model);

            System.out.println(
                    "\nPOWER BI DATA LOADING ENGINE"
            );

            System.out.println(
                    "============================"
            );

            refreshService.refresh(
                    "csv_sales",
                    "SalesCSV"
            );

            refreshService.refresh(
                    "database_sales",
                    "SalesDatabase"
            );

            refreshService.refresh(
                    "excel_export",
                    "SalesExcelExport"
            );

            System.out.println("\nIMPORT MODE");

            System.out.println(
                    "Tables: " + List.of(
                            "SalesCSV",
                            "SalesDatabase",
                            "SalesExcelExport"
                    )
            );

            List<SalesRecord> combined =
                    new ArrayList<>();

            combined.addAll(
                    model.getTable("SalesCSV")
            );

            combined.addAll(
                    model.getTable("SalesDatabase")
            );

            combined.addAll(
                    model.getTable("SalesExcelExport")
            );

            System.out.println("\nDIRECTQUERY-STYLE MODE");

            model.directQuery(
                    loader,
                    "csv_sales"
            );

            System.out.println("\nLIVE CONNECTION");

            model.liveConnection(true);

            System.out.println("\nSALES REPORT");

            SalesAnalytics.Report report =
                    SalesAnalytics.calculate(combined);

            System.out.println(
                    "Record count: " + report.recordCount()
            );

            System.out.println(
                    "Quantity: " + report.totalQuantity()
            );

            System.out.println(
                    "Revenue: " + report.totalRevenue()
            );

            System.out.println(
                    "Product revenue: "
                    + report.revenueByProduct()
            );

            System.out.println("\nREFRESH AUDIT");

            model.auditRecords().forEach(
                    System.out::println
            );

            System.out.println("\nERROR VALIDATION");

            try {

                new SalesRecord(
                        "Invalid",
                        -1,
                        100
                );

            } catch (ValidationException error) {

                System.out.println(
                        "Expected failure: "
                        + error.getMessage()
                );
            }

            try {

                WebSourceValidator.validate(
                        "http://insecure.example.com"
                );

            } catch (ValidationException error) {

                System.out.println(
                        "Expected failure: "
                        + error.getMessage()
                );
            }

            System.out.println(
                    "\nProcessing completed."
            );

        } catch (Exception error) {

            System.err.println(
                    "Application failed: "
                    + error.getMessage()
            );

            System.exit(1);
        }
    }
}
