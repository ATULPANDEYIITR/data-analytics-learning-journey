/*
 * Enterprise Dashboard Design and Governance Platform
 *
 * Java 17
 *
 * Compile:
 * javac DashboardDesign.java
 *
 * Run:
 * java DashboardDesign
 *
 * Features:
 * - Enterprise dashboard domain modeling
 * - Immutable KPI and business records
 * - Policy-driven KPI evaluation
 * - Visual hierarchy and layout management
 * - Responsive grid allocation
 * - Interactive state transitions
 * - Event-driven filtering
 * - Dashboard authorization
 * - Accessibility validation
 * - Aggregation and reporting
 * - Custom exception handling
 */

import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

// ============================================================
// 1. APPLICATION ENTRY POINT
// ============================================================

public class DashboardDesign {

    public static void main(String[] args) {
        try {
            DashboardApplication application = new DashboardApplication();

            application.initialize();
            application.display();

            application.demonstrateFiltering();
            application.displayLayout();

            application.runTests();

        } catch (DashboardException exception) {
            System.err.println(
                "Dashboard error [" + exception.getCode() + "]: "
                + exception.getMessage()
            );

            System.exit(1);
        }
    }
}

// ============================================================
// 2. CUSTOM EXCEPTIONS
// ============================================================

class DashboardException extends RuntimeException {

    private final String code;

    public DashboardException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}

class ValidationException extends DashboardException {

    public ValidationException(String message) {
        super("VALIDATION_ERROR", message);
    }
}

class AuthorizationException extends DashboardException {

    public AuthorizationException(String message) {
        super("AUTHORIZATION_ERROR", message);
    }
}

class LayoutException extends DashboardException {

    public LayoutException(String message) {
        super("LAYOUT_ERROR", message);
    }
}

// ============================================================
// 3. ENUMERATIONS
// ============================================================

enum KPIStatus {
    GOOD,
    WARNING,
    CRITICAL,
    NEUTRAL
}

enum MetricFormat {
    NUMBER,
    CURRENCY,
    PERCENTAGE
}

enum Aggregation {
    SUM,
    AVERAGE,
    COUNT,
    MINIMUM,
    MAXIMUM
}

enum ChartType {
    LINE,
    BAR,
    DONUT,
    AREA,
    TABLE
}

enum UserRole {
    VIEWER,
    ANALYST,
    MANAGER,
    ADMINISTRATOR
}

enum DashboardEventType {
    FILTER_CHANGED,
    SORT_CHANGED,
    DRILL_DOWN,
    RESET
}

// ============================================================
// 4. DESIGN TOKENS
// ============================================================

record ColorToken(
    String name,
    String hexadecimal,
    String meaning
) {}

record TypographyToken(
    String name,
    int fontSize,
    int weight
) {}

final class DesignSystem {

    private DesignSystem() {}

    public static final Map<String, ColorToken> COLORS = Map.of(
        "primary",
        new ColorToken("primary", "#2563EB", "Primary actions"),

        "background",
        new ColorToken("background", "#F8FAFC", "Page background"),

        "surface",
        new ColorToken("surface", "#FFFFFF", "Cards and panels"),

        "text",
        new ColorToken("text", "#172033", "Primary text"),

        "muted",
        new ColorToken("muted", "#64748B", "Secondary text"),

        "success",
        new ColorToken("success", "#15803D", "Positive performance"),

        "warning",
        new ColorToken("warning", "#B45309", "Warning condition"),

        "danger",
        new ColorToken("danger", "#B91C1C", "Critical condition")
    );

    public static final Map<String, TypographyToken> TYPOGRAPHY = Map.of(
        "page-title", new TypographyToken("page-title", 28, 700),
        "section-title", new TypographyToken("section-title", 20, 600),
        "card-title", new TypographyToken("card-title", 14, 600),
        "kpi-value", new TypographyToken("kpi-value", 30, 700),
        "body", new TypographyToken("body", 14, 400),
        "caption", new TypographyToken("caption", 12, 400)
    );

    public static ColorToken color(String name) {
        ColorToken token = COLORS.get(name);

        if (token == null) {
            throw new ValidationException("Unknown design color: " + name);
        }

        return token;
    }

    private static double luminance(String hex) {
        if (!hex.matches("#[0-9A-Fa-f]{6}")) {
            throw new ValidationException("Invalid hexadecimal color");
        }

        double[] channels = new double[3];

        for (int i = 0; i < 3; i++) {
            int value = Integer.parseInt(
                hex.substring(1 + i * 2, 3 + i * 2),
                16
            );

            double channel = value / 255.0;

            channels[i] = channel <= 0.04045
                ? channel / 12.92
                : Math.pow((channel + 0.055) / 1.055, 2.4);
        }

        return 0.2126 * channels[0]
            + 0.7152 * channels[1]
            + 0.0722 * channels[2];
    }

    public static double contrastRatio(String foreground, String background) {
        double a = luminance(foreground);
        double b = luminance(background);

        return (Math.max(a, b) + 0.05)
            / (Math.min(a, b) + 0.05);
    }
}

// ============================================================
// 5. KPI POLICY AND DOMAIN MODEL
// ============================================================

record KpiPolicy(
    boolean higherIsBetter,
    Double warningThreshold,
    Double criticalThreshold
) {
    KpiPolicy {
        if (
            warningThreshold != null &&
            criticalThreshold != null
        ) {
            if (
                higherIsBetter &&
                warningThreshold < criticalThreshold
            ) {
                throw new ValidationException(
                    "Invalid descending threshold configuration"
                );
            }

            if (
                !higherIsBetter &&
                warningThreshold > criticalThreshold
            ) {
                throw new ValidationException(
                    "Invalid ascending threshold configuration"
                );
            }
        }
    }
}

record KPI(
    String id,
    String name,
    double value,
    Double previousValue,
    Double target,
    MetricFormat format,
    Aggregation aggregation,
    KpiPolicy policy,
    String description
) {

    KPI {
        if (id == null || id.isBlank()) {
            throw new ValidationException("KPI ID is required");
        }

        if (name == null || name.isBlank()) {
            throw new ValidationException("KPI name is required");
        }

        if (!Double.isFinite(value)) {
            throw new ValidationException("KPI value must be finite");
        }

        Objects.requireNonNull(format);
        Objects.requireNonNull(aggregation);
        Objects.requireNonNull(policy);
    }

    KPIStatus evaluate() {
        Double critical = policy.criticalThreshold();
        Double warning = policy.warningThreshold();

        if (critical != null) {
            boolean breached = policy.higherIsBetter()
                ? value < critical
                : value > critical;

            if (breached) {
                return KPIStatus.CRITICAL;
            }
        }

        if (warning != null) {
            boolean breached = policy.higherIsBetter()
                ? value < warning
                : value > warning;

            if (breached) {
                return KPIStatus.WARNING;
            }
        }

        return KPIStatus.GOOD;
    }

    OptionalDouble changePercent() {
        if (previousValue == null || previousValue == 0) {
            return OptionalDouble.empty();
        }

        return OptionalDouble.of(
            ((value - previousValue) / Math.abs(previousValue)) * 100
        );
    }

    OptionalDouble targetAchievement() {
        if (target == null || target == 0) {
            return OptionalDouble.empty();
        }

        if (!policy.higherIsBetter()) {
            if (value == 0) {
                return OptionalDouble.empty();
            }

            return OptionalDouble.of(target / value * 100);
        }

        return OptionalDouble.of(value / target * 100);
    }

    String formattedValue() {
        return switch (format) {
            case CURRENCY -> String.format(Locale.US, "$%,.2f", value);
            case PERCENTAGE -> String.format(Locale.US, "%.2f%%", value);
            case NUMBER -> String.format(Locale.US, "%,.2f", value);
        };
    }
}

// ============================================================
// 6. BUSINESS DATA MODEL
// ============================================================

record MetricRecord(
    int id,
    String date,
    String department,
    String region,
    double revenue,
    double expenses,
    int orders,
    double satisfaction,
    double conversion
) {

    MetricRecord {
        if (id <= 0) {
            throw new ValidationException("Record ID must be positive");
        }

        if (
            date == null ||
            !date.matches("\\d{4}-\\d{2}-\\d{2}")
        ) {
            throw new ValidationException("Invalid record date");
        }

        if (
            department == null || department.isBlank() ||
            region == null || region.isBlank()
        ) {
            throw new ValidationException("Business dimensions are required");
        }

        if (
            revenue < 0 ||
            expenses < 0 ||
            orders < 0 ||
            satisfaction < 0 ||
            satisfaction > 100 ||
            conversion < 0 ||
            conversion > 100
        ) {
            throw new ValidationException("Invalid business metric");
        }
    }
}

record DashboardMetrics(
    double revenue,
    double expenses,
    double profit,
    double orders,
    double satisfaction,
    double conversion
) {}

// ============================================================
// 7. DATA ACCESS SERVICE
// ============================================================

final class DashboardRepository {

    private final List<MetricRecord> records;

    DashboardRepository(List<MetricRecord> input) {
        Set<Integer> ids = new HashSet<>();

        for (MetricRecord record : input) {
            if (!ids.add(record.id())) {
                throw new ValidationException("Duplicate record identifier");
            }
        }

        this.records = List.copyOf(input);
    }

    List<MetricRecord> all() {
        return records;
    }

    List<MetricRecord> filter(
        Predicate<MetricRecord> condition,
        Comparator<MetricRecord> comparator
    ) {
        return records.stream()
            .filter(condition)
            .sorted(comparator)
            .toList();
    }

    DashboardMetrics aggregate(List<MetricRecord> selected) {
        if (selected.isEmpty()) {
            return new DashboardMetrics(0, 0, 0, 0, 0, 0);
        }

        double revenue = selected.stream()
            .mapToDouble(MetricRecord::revenue)
            .sum();

        double expenses = selected.stream()
            .mapToDouble(MetricRecord::expenses)
            .sum();

        double orders = selected.stream()
            .mapToDouble(MetricRecord::orders)
            .sum();

        double satisfaction = selected.stream()
            .mapToDouble(MetricRecord::satisfaction)
            .average()
            .orElse(0);

        double conversion = selected.stream()
            .mapToDouble(MetricRecord::conversion)
            .average()
            .orElse(0);

        return new DashboardMetrics(
            revenue,
            expenses,
            revenue - expenses,
            orders,
            satisfaction,
            conversion
        );
    }

    Map<String, DashboardMetrics> regionalPerformance() {
        return records.stream().collect(
            Collectors.groupingBy(
                MetricRecord::region,
                TreeMap::new,
                Collectors.collectingAndThen(
                    Collectors.toList(),
                    this::aggregate
                )
            )
        );
    }
}

// ============================================================
// 8. LAYOUT DOMAIN MODEL
// ============================================================

record GridComponent(
    String id,
    String title,
    ChartType type,
    int row,
    int column,
    int rowSpan,
    int columnSpan,
    int priority
) {

    GridComponent {
        if (id == null || id.isBlank()) {
            throw new LayoutException("Component ID is required");
        }

        Objects.requireNonNull(type);

        if (
            row < 1 ||
            column < 1 ||
            rowSpan < 1 ||
            columnSpan < 1 ||
            priority < 1
        ) {
            throw new LayoutException("Invalid component placement");
        }
    }
}

final class DashboardLayout {

    private final int columns;
    private final Map<String, GridComponent> components =
        new LinkedHashMap<>();

    DashboardLayout(int columns) {
        if (columns < 1) {
            throw new LayoutException("Invalid grid column count");
        }

        this.columns = columns;
    }

    void add(GridComponent component) {
        if (components.containsKey(component.id())) {
            throw new LayoutException("Duplicate component ID");
        }

        if (
            component.column() + component.columnSpan() - 1 > columns
        ) {
            throw new LayoutException("Component exceeds grid width");
        }

        for (GridComponent existing : components.values()) {
            boolean rowOverlap =
                component.row() < existing.row() + existing.rowSpan() &&
                existing.row() < component.row() + component.rowSpan();

            boolean columnOverlap =
                component.column() <
                    existing.column() + existing.columnSpan() &&
                existing.column() <
                    component.column() + component.columnSpan();

            if (rowOverlap && columnOverlap) {
                throw new LayoutException(
                    "Layout collision: " +
                    component.id() + " and " + existing.id()
                );
            }
        }

        components.put(component.id(), component);
    }

    List<GridComponent> render() {
        return components.values().stream()
            .sorted(
                Comparator.comparingInt(GridComponent::row)
                    .thenComparing(
                        Comparator.comparingInt(
                            GridComponent::priority
                        ).reversed()
                    )
                    .thenComparingInt(GridComponent::column)
            )
            .toList();
    }

    static int responsiveColumns(int width) {
        if (width <= 0) {
            throw new LayoutException("Invalid viewport width");
        }

        if (width < 600) return 1;
        if (width < 1024) return 6;

        return 12;
    }
}

// ============================================================
// 9. INTERACTION AND AUTHORIZATION
// ============================================================

record DashboardEvent(
    DashboardEventType type,
    Map<String, String> attributes,
    long revision
) {}

interface DashboardEventListener {
    void onEvent(DashboardEvent event);
}

final class DashboardAuthorization {

    private DashboardAuthorization() {}

    static void authorize(UserRole role, DashboardEventType action) {
        Objects.requireNonNull(role);
        Objects.requireNonNull(action);

        if (
            role == UserRole.VIEWER &&
            action == DashboardEventType.RESET
        ) {
            throw new AuthorizationException(
                "Viewer cannot reset shared dashboard state"
            );
        }

        if (
            role == UserRole.VIEWER &&
            action == DashboardEventType.SORT_CHANGED
        ) {
            return;
        }
    }
}

// ============================================================
// 10. DASHBOARD STATE SERVICE
// ============================================================

final class DashboardStateService {

    private final List<DashboardEventListener> listeners =
        new ArrayList<>();

    private Map<String, String> filters = Map.of();
    private long revision = 0;

    void subscribe(DashboardEventListener listener) {
        listeners.add(Objects.requireNonNull(listener));
    }

    Map<String, String> filters() {
        return filters;
    }

    long revision() {
        return revision;
    }

    void update(
        UserRole role,
        DashboardEventType type,
        Map<String, String> candidate
    ) {
        DashboardAuthorization.authorize(role, type);

        // Validate before committing the new state.
        Map<String, String> immutableCandidate =
            Map.copyOf(candidate);

        if (
            immutableCandidate.containsKey("from") &&
            immutableCandidate.containsKey("to") &&
            immutableCandidate.get("from").compareTo(
                immutableCandidate.get("to")
            ) > 0
        ) {
            throw new ValidationException("Invalid filter date range");
        }

        filters = immutableCandidate;
        revision++;

        DashboardEvent event = new DashboardEvent(
            type,
            filters,
            revision
        );

        for (DashboardEventListener listener : List.copyOf(listeners)) {
            try {
                listener.onEvent(event);
            } catch (RuntimeException exception) {
                System.err.println(
                    "Dashboard listener failed: " +
                    exception.getMessage()
                );
            }
        }
    }

    void reset(UserRole role) {
        update(
            role,
            DashboardEventType.RESET,
            Map.of()
        );
    }
}

// ============================================================
// 11. DASHBOARD POLICY SERVICE
// ============================================================

final class DashboardPolicyService {

    List<KPI> buildKpis(DashboardMetrics metrics) {
        return List.of(
            new KPI(
                "revenue",
                "Total Revenue",
                metrics.revenue(),
                45000.0,
                50000.0,
                MetricFormat.CURRENCY,
                Aggregation.SUM,
                new KpiPolicy(true, 35000.0, 25000.0),
                "Revenue generated during the selected period"
            ),
            new KPI(
                "profit",
                "Operating Profit",
                metrics.profit(),
                12000.0,
                15000.0,
                MetricFormat.CURRENCY,
                Aggregation.SUM,
                new KpiPolicy(true, 8000.0, 4000.0),
                "Revenue less expenses"
            ),
            new KPI(
                "satisfaction",
                "Customer Satisfaction",
                metrics.satisfaction(),
                82.0,
                90.0,
                MetricFormat.PERCENTAGE,
                Aggregation.AVERAGE,
                new KpiPolicy(true, 75.0, 60.0),
                "Mean customer satisfaction"
            ),
            new KPI(
                "conversion",
                "Conversion Rate",
                metrics.conversion(),
                3.5,
                5.0,
                MetricFormat.PERCENTAGE,
                Aggregation.AVERAGE,
                new KpiPolicy(true, 2.5, 1.5),
                "Conversion percentage"
            )
        );
    }
}

// ============================================================
// 12. SAMPLE DATA
// ============================================================

final class SampleData {

    private SampleData() {}

    static List<MetricRecord> create() {
        return List.of(
            new MetricRecord(
                1, "2026-11-20", "Sales", "North",
                18000, 11000, 120, 91, 5.2
            ),
            new MetricRecord(
                2, "2026-11-21", "Technology", "North",
                14000, 9000, 90, 87, 4.5
            ),
            new MetricRecord(
                3, "2026-11-22", "Sales", "South",
                16000, 10000, 110, 83, 3.8
            ),
            new MetricRecord(
                4, "2026-11-23", "Technology", "South",
                12000, 8500, 75, 88, 4.2
            ),
            new MetricRecord(
                5, "2026-11-24", "Operations", "East",
                9000, 7000, 65, 79, 2.8
            ),
            new MetricRecord(
                6, "2026-11-25", "Sales", "East",
                21000, 13000, 140, 94, 5.8
            ),
            new MetricRecord(
                7, "2026-11-26", "Operations", "West",
                11000, 7500, 80, 85, 3.6
            ),
            new MetricRecord(
                8, "2026-11-27", "Technology", "West",
                15000, 9500, 95, 90, 4.9
            )
        );
    }
}

// ============================================================
// 13. ENTERPRISE APPLICATION SERVICE
// ============================================================

final class DashboardApplication {

    private DashboardRepository repository;
    private DashboardLayout layout;
    private DashboardStateService stateService;
    private DashboardPolicyService policyService;

    void initialize() {
        repository = new DashboardRepository(SampleData.create());
        layout = new DashboardLayout(12);
        stateService = new DashboardStateService();
        policyService = new DashboardPolicyService();

        configureLayout();

        stateService.subscribe(event -> {
            System.out.println(
                "Event: " + event.type() +
                " | Revision: " + event.revision()
            );
        });
    }

    private void configureLayout() {
        layout.add(new GridComponent(
            "revenue", "Revenue KPI", ChartType.TABLE,
            1, 1, 1, 3, 10
        ));

        layout.add(new GridComponent(
            "profit", "Profit KPI", ChartType.TABLE,
            1, 4, 1, 3, 9
        ));

        layout.add(new GridComponent(
            "satisfaction", "Satisfaction KPI", ChartType.TABLE,
            1, 7, 1, 3, 8
        ));

        layout.add(new GridComponent(
            "conversion", "Conversion KPI", ChartType.TABLE,
            1, 10, 1, 3, 7
        ));

        layout.add(new GridComponent(
            "trend", "Revenue Trend", ChartType.LINE,
            2, 1, 2, 8, 6
        ));

        layout.add(new GridComponent(
            "regional", "Regional Performance", ChartType.BAR,
            2, 9, 2, 4, 5
        ));
    }

    void display() {
        List<MetricRecord> records = repository.all();

        DashboardMetrics metrics = repository.aggregate(records);

        List<KPI> kpis = policyService.buildKpis(metrics);

        System.out.println(
            "\n=============================================="
        );

        System.out.println(
            "       ENTERPRISE PERFORMANCE DASHBOARD"
        );

        System.out.println(
            "=============================================="
        );

        System.out.println("\nKEY PERFORMANCE INDICATORS");

        for (KPI kpi : kpis) {
            String change = kpi.changePercent().isPresent()
                ? String.format(
                    Locale.US,
                    "%+.2f%%",
                    kpi.changePercent().getAsDouble()
                )
                : "N/A";

            System.out.printf(
                Locale.US,
                "%-25s %15s | %9s | %s%n",
                kpi.name(),
                kpi.formattedValue(),
                change,
                kpi.evaluate()
            );
        }

        System.out.println("\nREGIONAL PERFORMANCE");

        repository.regionalPerformance().forEach((region, values) ->
            System.out.printf(
                Locale.US,
                "%-12s Revenue: %10.2f Profit: %10.2f%n",
                region,
                values.revenue(),
                values.profit()
            )
        );

        System.out.println("\nTOTAL RECORDS: " + records.size());
    }

    void demonstrateFiltering() {
        System.out.println("\nINTERACTIVE FILTER");

        stateService.update(
            UserRole.ANALYST,
            DashboardEventType.FILTER_CHANGED,
            Map.of("region", "North")
        );

        List<MetricRecord> filtered = repository.filter(
            record -> record.region().equals("North"),
            Comparator.comparingDouble(MetricRecord::revenue).reversed()
        );

        DashboardMetrics metrics = repository.aggregate(filtered);

        System.out.println("Region: North");
        System.out.println("Records: " + filtered.size());
        System.out.println("Revenue: " + metrics.revenue());
        System.out.println("Profit: " + metrics.profit());
    }

    void displayLayout() {
        System.out.println("\nDASHBOARD LAYOUT");

        for (GridComponent component : layout.render()) {
            System.out.printf(
                "%-15s %-8s Row=%d Column=%d Priority=%d%n",
                component.id(),
                component.type(),
                component.row(),
                component.column(),
                component.priority()
            );
        }

        System.out.println("\nRESPONSIVE GRID");

        System.out.println(
            "Desktop: " + DashboardLayout.responsiveColumns(1440)
        );

        System.out.println(
            "Tablet: " + DashboardLayout.responsiveColumns(800)
        );

        System.out.println(
            "Mobile: " + DashboardLayout.responsiveColumns(390)
        );

        System.out.println("\nDESIGN ACCESSIBILITY");

        double ratio = DesignSystem.contrastRatio(
            "#172033",
            "#FFFFFF"
        );

        System.out.printf(
            Locale.US,
            "Primary text contrast: %.2f:1%n",
            ratio
        );
    }

    void runTests() {
        if (
            repository.aggregate(List.of()).revenue() != 0
        ) {
            throw new DashboardException(
                "TEST_FAILURE",
                "Empty aggregation failed"
            );
        }

        KPI critical = new KPI(
            "critical",
            "Critical Metric",
            30,
            40.0,
            100.0,
            MetricFormat.NUMBER,
            Aggregation.AVERAGE,
            new KpiPolicy(true, 70.0, 50.0),
            "Validation metric"
        );

        if (critical.evaluate() != KPIStatus.CRITICAL) {
            throw new DashboardException(
                "TEST_FAILURE",
                "KPI threshold evaluation failed"
            );
        }

        boolean invalidDateDetected = false;

        try {
            stateService.update(
                UserRole.MANAGER,
                DashboardEventType.FILTER_CHANGED,
                Map.of(
                    "from", "2026-11-27",
                    "to", "2026-11-20"
                )
            );
        } catch (ValidationException exception) {
            invalidDateDetected = true;
        }

        if (!invalidDateDetected) {
            throw new DashboardException(
                "TEST_FAILURE",
                "Invalid date filter was accepted"
            );
        }

        boolean unauthorized = false;

        try {
            stateService.reset(UserRole.VIEWER);
        } catch (AuthorizationException exception) {
            unauthorized = true;
        }

        if (!unauthorized) {
            throw new DashboardException(
                "TEST_FAILURE",
                "Unauthorized reset was accepted"
            );
        }

        double ratio = DesignSystem.contrastRatio(
            "#172033",
            "#FFFFFF"
        );

        if (ratio < 4.5) {
            throw new DashboardException(
                "TEST_FAILURE",
                "Text accessibility threshold failed"
            );
        }

        System.out.println("\nAll Java 17 validation tests passed.");
    }
}
