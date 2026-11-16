import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

/**
 * POWER BI INTRODUCTION
 *
 * Enterprise Business Intelligence Architecture.
 *
 * Java 17 implementation covering:
 * - Business intelligence domain modeling
 * - Data integration and transformation
 * - Dimensional modeling
 * - Analytical measures
 * - Report and dashboard management
 * - Refresh lifecycle
 * - Role-based access control
 * - Publication governance
 * - Data-quality validation
 *
 * Compile:
 * javac PowerBIEnterprise.java
 *
 * Run:
 * java PowerBIEnterprise
 */
public class PowerBIEnterprise {

    // ========================================================
    // 1. ENUMERATIONS
    // ========================================================

    enum RefreshStatus {
        NOT_STARTED,
        RUNNING,
        SUCCEEDED,
        FAILED
    }

    enum ReportStatus {
        DRAFT,
        IN_REVIEW,
        APPROVED,
        PUBLISHED,
        REJECTED
    }

    enum Permission {
        VIEW,
        BUILD,
        PUBLISH,
        ADMIN
    }

    enum VisualType {
        KPI_CARD,
        BAR_CHART,
        LINE_CHART,
        PIE_CHART,
        TABLE,
        MATRIX
    }

    enum DataSourceType {
        DATABASE,
        CSV,
        API,
        CLOUD_STORAGE
    }

    // ========================================================
    // 2. CUSTOM EXCEPTIONS
    // ========================================================

    static class BIException extends RuntimeException {

        BIException(String message) {
            super(message);
        }
    }

    static class ValidationException extends BIException {

        ValidationException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends BIException {

        AuthorizationException(String message) {
            super(message);
        }
    }

    static class StateTransitionException extends BIException {

        StateTransitionException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 3. IMMUTABLE DOMAIN RECORDS
    // ========================================================

    record Customer(
        int id,
        String name,
        String region,
        String segment
    ) {

        Customer {
            if (id <= 0 || name == null || name.isBlank()
                    || region == null || region.isBlank()) {
                throw new ValidationException("Invalid customer.");
            }
        }
    }

    record Product(
        int id,
        String name,
        String category,
        double unitCost
    ) {

        Product {
            if (id <= 0 || name == null || name.isBlank()
                    || category == null || category.isBlank()
                    || !Double.isFinite(unitCost) || unitCost < 0) {
                throw new ValidationException("Invalid product.");
            }
        }
    }

    record Transaction(
        int id,
        int customerId,
        int productId,
        LocalDate transactionDate,
        int quantity,
        double unitPrice
    ) {

        Transaction {
            if (id <= 0 || customerId <= 0 || productId <= 0
                    || transactionDate == null || quantity <= 0
                    || !Double.isFinite(unitPrice) || unitPrice < 0) {
                throw new ValidationException("Invalid transaction.");
            }
        }
    }

    record FactSale(
        int transactionId,
        int customerId,
        int productId,
        String customerName,
        String productName,
        String region,
        String category,
        LocalDate transactionDate,
        int quantity,
        double revenue,
        double cost,
        double profit
    ) {}

    record KPI(
        String name,
        double value,
        String unit
    ) {}

    record VisualDefinition(
        String title,
        VisualType type,
        String dimension,
        String measure
    ) {

        VisualDefinition {
            Objects.requireNonNull(title);
            Objects.requireNonNull(type);
            Objects.requireNonNull(measure);

            if (title.isBlank() || measure.isBlank()) {
                throw new ValidationException("Invalid visual definition.");
            }
        }
    }

    record ReportSnapshot(
        int id,
        String name,
        String owner,
        String description,
        ReportStatus status,
        List<VisualDefinition> visuals,
        Instant updatedAt
    ) {

        ReportSnapshot {
            visuals = List.copyOf(visuals);
        }
    }

    // ========================================================
    // 4. SAMPLE DATA REPOSITORY
    // ========================================================

    static class DataRepository {

        private final List<Customer> customers;
        private final List<Product> products;
        private final List<Transaction> transactions;

        DataRepository() {

            customers = List.of(
                new Customer(1, "Aarav Sharma", "North", "Enterprise"),
                new Customer(2, "Meera Verma", "South", "Consumer"),
                new Customer(3, "Rohan Gupta", "East", "Enterprise"),
                new Customer(4, "Ananya Singh", "West", "Consumer"),
                new Customer(5, "Kabir Patel", "North", "Small Business")
            );

            products = List.of(
                new Product(101, "Laptop", "Electronics", 45000),
                new Product(102, "Monitor", "Electronics", 12000),
                new Product(103, "Office Chair", "Furniture", 5000),
                new Product(104, "Desk", "Furniture", 8000),
                new Product(105, "Keyboard", "Accessories", 1000)
            );

            transactions = List.of(
                new Transaction(1001, 1, 101, LocalDate.parse("2026-01-10"), 2, 65000),
                new Transaction(1002, 2, 102, LocalDate.parse("2026-01-15"), 3, 18000),
                new Transaction(1003, 3, 103, LocalDate.parse("2026-02-05"), 5, 8500),
                new Transaction(1004, 4, 104, LocalDate.parse("2026-02-12"), 2, 12000),
                new Transaction(1005, 1, 105, LocalDate.parse("2026-03-01"), 10, 1800),
                new Transaction(1006, 5, 101, LocalDate.parse("2026-03-15"), 1, 68000),
                new Transaction(1007, 3, 102, LocalDate.parse("2026-04-02"), 4, 17500),
                new Transaction(1008, 2, 103, LocalDate.parse("2026-04-08"), 3, 9000),
                new Transaction(1009, 4, 105, LocalDate.parse("2026-05-10"), 15, 1600),
                new Transaction(1010, 5, 104, LocalDate.parse("2026-05-18"), 3, 12500)
            );
        }

        List<Customer> customers() {
            return customers;
        }

        List<Product> products() {
            return products;
        }

        List<Transaction> transactions() {
            return transactions;
        }
    }

    // ========================================================
    // 5. VALIDATION SERVICE
    // ========================================================

    static class ValidationService {

        static void validate(DataRepository repository) {

            Set<Integer> customerIds = new HashSet<>();
            Set<Integer> productIds = new HashSet<>();
            Set<Integer> transactionIds = new HashSet<>();

            for (Customer customer : repository.customers()) {
                if (!customerIds.add(customer.id())) {
                    throw new ValidationException("Duplicate customer ID.");
                }
            }

            for (Product product : repository.products()) {
                if (!productIds.add(product.id())) {
                    throw new ValidationException("Duplicate product ID.");
                }
            }

            for (Transaction transaction : repository.transactions()) {

                if (!transactionIds.add(transaction.id())) {
                    throw new ValidationException("Duplicate transaction ID.");
                }

                if (!customerIds.contains(transaction.customerId())) {
                    throw new ValidationException("Unknown customer reference.");
                }

                if (!productIds.contains(transaction.productId())) {
                    throw new ValidationException("Unknown product reference.");
                }
            }
        }
    }

    // ========================================================
    // 6. ETL SERVICE
    // ========================================================

    static class ETLService {

        List<FactSale> transform(DataRepository repository) {

            Map<Integer, Customer> customerMap =
                repository.customers().stream()
                    .collect(Collectors.toMap(
                        Customer::id,
                        customer -> customer
                    ));

            Map<Integer, Product> productMap =
                repository.products().stream()
                    .collect(Collectors.toMap(
                        Product::id,
                        product -> product
                    ));

            return repository.transactions().stream()
                .map(transaction -> {

                    Customer customer = customerMap.get(
                        transaction.customerId()
                    );

                    Product product = productMap.get(
                        transaction.productId()
                    );

                    if (customer == null || product == null) {
                        throw new ValidationException(
                            "Dimension lookup failed."
                        );
                    }

                    double revenue =
                        transaction.quantity() * transaction.unitPrice();

                    double cost =
                        transaction.quantity() * product.unitCost();

                    return new FactSale(
                        transaction.id(),
                        customer.id(),
                        product.id(),
                        customer.name(),
                        product.name(),
                        customer.region(),
                        product.category(),
                        transaction.transactionDate(),
                        transaction.quantity(),
                        revenue,
                        cost,
                        revenue - cost
                    );

                })
                .toList();
        }
    }

    // ========================================================
    // 7. STAR SCHEMA MODEL
    // ========================================================

    static class DimensionalModel {

        private final List<FactSale> factSales;

        private final Map<Integer, Customer> dimCustomer;
        private final Map<Integer, Product> dimProduct;
        private final Map<LocalDate, LocalDate> dimDate;

        DimensionalModel(
            List<FactSale> records,
            DataRepository repository
        ) {

            factSales = List.copyOf(records);

            dimCustomer = repository.customers().stream()
                .collect(Collectors.toUnmodifiableMap(
                    Customer::id,
                    customer -> customer
                ));

            dimProduct = repository.products().stream()
                .collect(Collectors.toUnmodifiableMap(
                    Product::id,
                    product -> product
                ));

            dimDate = records.stream()
                .map(FactSale::transactionDate)
                .distinct()
                .collect(Collectors.toUnmodifiableMap(
                    date -> date,
                    date -> date
                ));
        }

        List<FactSale> facts() {
            return factSales;
        }

        void describe() {

            System.out.println("Fact Sales Rows: " + factSales.size());
            System.out.println("Customer Dimensions: " + dimCustomer.size());
            System.out.println("Product Dimensions: " + dimProduct.size());
            System.out.println("Date Dimensions: " + dimDate.size());
        }
    }

    // ========================================================
    // 8. MEASURE SERVICE
    // ========================================================

    static class MeasureService {

        static double revenue(List<FactSale> records) {

            return records.stream()
                .mapToDouble(FactSale::revenue)
                .sum();
        }

        static double cost(List<FactSale> records) {

            return records.stream()
                .mapToDouble(FactSale::cost)
                .sum();
        }

        static double profit(List<FactSale> records) {
            return revenue(records) - cost(records);
        }

        static double margin(List<FactSale> records) {

            double revenue = revenue(records);

            return revenue == 0
                ? 0
                : profit(records) / revenue * 100;
        }

        static double averageOrderValue(List<FactSale> records) {

            return records.isEmpty()
                ? 0
                : revenue(records) / records.size();
        }

        static long uniqueCustomers(List<FactSale> records) {

            return records.stream()
                .map(FactSale::customerId)
                .distinct()
                .count();
        }

        static Map<String, Double> aggregate(
            List<FactSale> records,
            String dimension
        ) {

            Map<String, Double> result = new TreeMap<>();

            for (FactSale record : records) {

                String key = switch (dimension) {
                    case "region" -> record.region();
                    case "product" -> record.productName();
                    case "category" -> record.category();
                    default -> throw new BIException(
                        "Unsupported dimension: " + dimension
                    );
                };

                result.merge(key, record.revenue(), Double::sum);
            }

            return Collections.unmodifiableMap(result);
        }
    }

    // ========================================================
    // 9. FILTER CONTEXT SERVICE
    // ========================================================

    static class FilterService {

        List<FactSale> filterRegion(
            List<FactSale> records,
            String region
        ) {

            return records.stream()
                .filter(record -> record.region().equalsIgnoreCase(region))
                .toList();
        }

        List<FactSale> filterMinimumRevenue(
            List<FactSale> records,
            double minimum
        ) {

            if (!Double.isFinite(minimum) || minimum < 0) {
                throw new ValidationException("Invalid revenue threshold.");
            }

            return records.stream()
                .filter(record -> record.revenue() >= minimum)
                .toList();
        }

        List<FactSale> filterDateRange(
            List<FactSale> records,
            LocalDate start,
            LocalDate end
        ) {

            if (start == null || end == null || end.isBefore(start)) {
                throw new ValidationException("Invalid date range.");
            }

            return records.stream()
                .filter(record ->
                    !record.transactionDate().isBefore(start)
                    && !record.transactionDate().isAfter(end)
                )
                .toList();
        }
    }

    // ========================================================
    // 10. REPORT SERVICE
    // ========================================================

    static class ReportService {

        private final Map<Integer, ReportSnapshot> reports =
            new LinkedHashMap<>();

        ReportSnapshot create(
            int id,
            String name,
            String owner,
            String description,
            List<VisualDefinition> visuals
        ) {

            if (id <= 0 || name == null || name.isBlank()
                    || owner == null || owner.isBlank()) {
                throw new ValidationException("Invalid report.");
            }

            if (reports.containsKey(id)) {
                throw new BIException("Report already exists.");
            }

            ReportSnapshot report = new ReportSnapshot(
                id,
                name,
                owner,
                description,
                ReportStatus.DRAFT,
                visuals,
                Instant.now()
            );

            reports.put(id, report);

            return report;
        }

        ReportSnapshot transition(
            int id,
            ReportStatus nextStatus
        ) {

            ReportSnapshot current = get(id);

            boolean valid = switch (current.status()) {
                case DRAFT ->
                    nextStatus == ReportStatus.IN_REVIEW;
                case IN_REVIEW ->
                    nextStatus == ReportStatus.APPROVED
                    || nextStatus == ReportStatus.REJECTED;
                case APPROVED ->
                    nextStatus == ReportStatus.PUBLISHED;
                case REJECTED ->
                    nextStatus == ReportStatus.DRAFT;
                case PUBLISHED ->
                    nextStatus == ReportStatus.DRAFT;
            };

            if (!valid) {
                throw new StateTransitionException(
                    "Invalid report transition: "
                    + current.status() + " -> " + nextStatus
                );
            }

            ReportSnapshot updated = new ReportSnapshot(
                current.id(),
                current.name(),
                current.owner(),
                current.description(),
                nextStatus,
                current.visuals(),
                Instant.now()
            );

            reports.put(id, updated);

            return updated;
        }

        ReportSnapshot get(int id) {

            ReportSnapshot report = reports.get(id);

            if (report == null) {
                throw new BIException("Report not found.");
            }

            return report;
        }
    }

    // ========================================================
    // 11. ACCESS CONTROL
    // ========================================================

    record User(
        String username,
        Set<Permission> permissions
    ) {

        User {
            if (username == null || username.isBlank()) {
                throw new ValidationException("Invalid username.");
            }

            permissions = Set.copyOf(permissions);
        }
    }

    static class AuthorizationService {

        void authorize(User user, Permission required) {

            if (!user.permissions().contains(Permission.ADMIN)
                    && !user.permissions().contains(required)) {

                throw new AuthorizationException(
                    "Permission denied: " + required
                );
            }
        }
    }

    // ========================================================
    // 12. REFRESH SERVICE
    // ========================================================

    interface RefreshListener {
        void onRefresh(RefreshStatus status, String message);
    }

    static class RefreshService {

        private RefreshStatus status = RefreshStatus.NOT_STARTED;

        private final List<RefreshListener> listeners =
            new ArrayList<>();

        private Instant lastRefresh;

        void addListener(RefreshListener listener) {
            listeners.add(Objects.requireNonNull(listener));
        }

        void notifyListeners(String message) {

            for (RefreshListener listener : listeners) {
                listener.onRefresh(status, message);
            }
        }

        List<FactSale> refresh(
            DataRepository repository,
            ETLService etl
        ) {

            if (status == RefreshStatus.RUNNING) {
                throw new BIException("Refresh already running.");
            }

            status = RefreshStatus.RUNNING;
            notifyListeners("Data refresh started.");

            try {

                ValidationService.validate(repository);

                List<FactSale> result = etl.transform(repository);

                if (result.isEmpty()) {
                    throw new BIException("Refresh produced no data.");
                }

                status = RefreshStatus.SUCCEEDED;
                lastRefresh = Instant.now();

                notifyListeners("Data refresh completed.");

                return List.copyOf(result);

            } catch (RuntimeException exception) {

                status = RefreshStatus.FAILED;
                notifyListeners(exception.getMessage());

                throw exception;
            }
        }

        RefreshStatus status() {
            return status;
        }

        Instant lastRefresh() {
            return lastRefresh;
        }
    }

    // ========================================================
    // 13. DASHBOARD SERVICE
    // ========================================================

    static class DashboardService {

        List<KPI> build(List<FactSale> records) {

            return List.of(
                new KPI(
                    "Total Revenue",
                    MeasureService.revenue(records),
                    "INR"
                ),
                new KPI(
                    "Total Profit",
                    MeasureService.profit(records),
                    "INR"
                ),
                new KPI(
                    "Profit Margin",
                    MeasureService.margin(records),
                    "%"
                ),
                new KPI(
                    "Average Order Value",
                    MeasureService.averageOrderValue(records),
                    "INR"
                ),
                new KPI(
                    "Unique Customers",
                    MeasureService.uniqueCustomers(records),
                    "count"
                )
            );
        }

        void display(List<KPI> kpis) {

            System.out.println("\nEXECUTIVE DASHBOARD");
            System.out.println("=".repeat(65));

            kpis.forEach(kpi ->
                System.out.printf(
                    "%-25s %15,.2f %s%n",
                    kpi.name(),
                    kpi.value(),
                    kpi.unit()
                )
            );

            System.out.println("=".repeat(65));
        }
    }

    // ========================================================
    // 14. MAIN APPLICATION
    // ========================================================

    public static void main(String[] args) {

        try {

            System.out.println("\nPOWER BI INTRODUCTION");
            System.out.println("Enterprise Business Intelligence System");

            DataRepository repository = new DataRepository();

            ETLService etl = new ETLService();

            RefreshService refresh = new RefreshService();

            refresh.addListener((status, message) ->
                System.out.println(
                    "[REFRESH " + status + "] " + message
                )
            );

            List<FactSale> records = refresh.refresh(
                repository,
                etl
            );

            System.out.println("\nDATA MODEL");

            DimensionalModel model = new DimensionalModel(
                records,
                repository
            );

            model.describe();

            System.out.println("\nBUSINESS MEASURES");

            System.out.printf(
                "Revenue: %.2f%n",
                MeasureService.revenue(records)
            );

            System.out.printf(
                "Cost: %.2f%n",
                MeasureService.cost(records)
            );

            System.out.printf(
                "Profit: %.2f%n",
                MeasureService.profit(records)
            );

            System.out.printf(
                "Profit Margin: %.2f%%%n",
                MeasureService.margin(records)
            );

            System.out.println("\nREGIONAL ANALYSIS");

            MeasureService.aggregate(records, "region")
                .forEach((region, revenue) ->
                    System.out.printf(
                        "%-15s %.2f%n",
                        region,
                        revenue
                    )
                );

            System.out.println("\nFILTERED ANALYSIS");

            FilterService filters = new FilterService();

            List<FactSale> northRecords = filters.filterRegion(
                records,
                "North"
            );

            System.out.printf(
                "North Revenue: %.2f%n",
                MeasureService.revenue(northRecords)
            );

            System.out.println("\nDASHBOARD");

            DashboardService dashboard = new DashboardService();

            dashboard.display(dashboard.build(records));

            System.out.println("\nREPORT GOVERNANCE");

            ReportService reports = new ReportService();

            reports.create(
                1,
                "Executive Sales Report",
                "data_analyst",
                "Regional sales and profitability",
                List.of(
                    new VisualDefinition(
                        "Revenue by Region",
                        VisualType.BAR_CHART,
                        "region",
                        "revenue"
                    ),
                    new VisualDefinition(
                        "Profit",
                        VisualType.KPI_CARD,
                        "",
                        "profit"
                    )
                )
            );

            reports.transition(1, ReportStatus.IN_REVIEW);
            reports.transition(1, ReportStatus.APPROVED);
            reports.transition(1, ReportStatus.PUBLISHED);

            System.out.println(
                "Report status: " + reports.get(1).status()
            );

            System.out.println("\nACCESS CONTROL");

            User analyst = new User(
                "data_analyst",
                EnumSet.of(Permission.VIEW, Permission.BUILD)
            );

            User administrator = new User(
                "bi_admin",
                EnumSet.of(Permission.ADMIN)
            );

            AuthorizationService authorization =
                new AuthorizationService();

            authorization.authorize(analyst, Permission.BUILD);
            authorization.authorize(administrator, Permission.PUBLISH);

            // Empty dataset and reconciliation checks.
            if (MeasureService.margin(List.of()) != 0) {
                throw new BIException("Empty dataset validation failed.");
            }

            if (records.size() != repository.transactions().size()) {
                throw new BIException("Record reconciliation failed.");
            }

            System.out.println("\nALL ENTERPRISE VALIDATIONS PASSED.");

        } catch (BIException exception) {

            System.err.println(
                "BUSINESS INTELLIGENCE ERROR: "
                + exception.getMessage()
            );

            System.exitCode = 1;

        } catch (Exception exception) {

            System.err.println(
                "UNEXPECTED APPLICATION ERROR: "
                + exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
