import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;

/**
 * Enterprise operations analytics using Java 17.
 *
 * Compile and run:
 *   javac PythonForAnalytics.java
 *   java PythonForAnalytics
 *
 * BigDecimal is used for monetary calculations. Immutable records represent
 * validated transactions, while the service separates validation, aggregation,
 * and reporting.
 */
public class PythonForAnalytics {

    enum Region {
        NORTH, SOUTH, EAST, WEST
    }

    record Transaction(
            String id,
            Region region,
            int quantity,
            BigDecimal unitPrice
    ) {
        Transaction {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Transaction ID cannot be empty");
            }
            Objects.requireNonNull(region, "Region is required");
            Objects.requireNonNull(unitPrice, "Unit price is required");

            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive");
            }
            if (unitPrice.signum() < 0) {
                throw new IllegalArgumentException("Unit price cannot be negative");
            }

            // Standardize financial scale so aggregation and display are stable.
            unitPrice = unitPrice.setScale(2, RoundingMode.UNNECESSARY);
        }

        BigDecimal salesAmount() {
            return unitPrice.multiply(BigDecimal.valueOf(quantity));
        }
    }

    record RejectedRecord(String id, List<String> errors) {
        RejectedRecord {
            errors = List.copyOf(errors);
        }
    }

    record AnalyticsReport(
            List<Transaction> accepted,
            List<RejectedRecord> rejected,
            Map<Region, BigDecimal> regionalSales,
            BigDecimal totalSales
    ) {
        AnalyticsReport {
            accepted = List.copyOf(accepted);
            rejected = List.copyOf(rejected);
            regionalSales = Collections.unmodifiableMap(
                    new EnumMap<>(regionalSales)
            );
        }
    }

    static final class AnalyticsService {
        private final Set<String> seenIds = new HashSet<>();
        private final List<Transaction> accepted = new ArrayList<>();
        private final List<RejectedRecord> rejected = new ArrayList<>();
        private final Map<Region, BigDecimal> regionalSales =
                new EnumMap<>(Region.class);

        void ingest(
                String id,
                Region region,
                String quantityText,
                String unitPriceText
        ) {
            List<String> errors = new ArrayList<>();
            int quantity = 0;
            BigDecimal unitPrice = null;

            if (id == null || id.isBlank()) {
                errors.add("Transaction ID cannot be empty");
            } else if (seenIds.contains(id)) {
                errors.add("Duplicate transaction ID");
            }

            if (region == null) {
                errors.add("Region is required");
            }

            try {
                if (quantityText == null || quantityText.isBlank()) {
                    throw new NumberFormatException("Quantity is empty");
                }
                quantity = Integer.parseInt(quantityText.trim());
                if (quantity <= 0) {
                    errors.add("Quantity must be positive");
                }
            } catch (NumberFormatException exception) {
                errors.add("Quantity must be a valid whole number");
            }

            try {
                if (unitPriceText == null || unitPriceText.isBlank()) {
                    throw new NumberFormatException("Unit price is empty");
                }

                unitPrice = new BigDecimal(unitPriceText.trim())
                        .setScale(2, RoundingMode.UNNECESSARY);

                if (unitPrice.signum() < 0) {
                    errors.add("Unit price cannot be negative");
                }
            } catch (NumberFormatException | ArithmeticException exception) {
                errors.add("Unit price must be a non-negative decimal with at most two decimal places");
            }

            if (!errors.isEmpty()) {
                rejected.add(new RejectedRecord(
                        id == null ? "" : id,
                        errors
                ));
                return;
            }

            try {
                Transaction transaction =
                        new Transaction(id.trim(), region, quantity, unitPrice);
                BigDecimal current = regionalSales.getOrDefault(
                        region, BigDecimal.ZERO.setScale(2)
                );
                BigDecimal nextTotal = current.add(transaction.salesAmount());

                // Update the ID set and regional total only after the immutable
                // transaction has passed every validation rule.
                seenIds.add(transaction.id());
                regionalSales.put(region, nextTotal);
                accepted.add(transaction);
            } catch (IllegalArgumentException exception) {
                rejected.add(new RejectedRecord(
                        id,
                        List.of(exception.getMessage())
                ));
            }
        }

        AnalyticsReport report() {
            BigDecimal total = regionalSales.values().stream()
                    .reduce(BigDecimal.ZERO.setScale(2), BigDecimal::add);

            Map<Region, BigDecimal> ordered = new EnumMap<>(Region.class);
            ordered.putAll(regionalSales);

            return new AnalyticsReport(
                    accepted,
                    rejected,
                    ordered,
                    total
            );
        }
    }

    static BigDecimal percentageChange(
            BigDecimal baseline,
            BigDecimal current
    ) {
        Objects.requireNonNull(baseline, "Baseline is required");
        Objects.requireNonNull(current, "Current value is required");

        if (baseline.signum() < 0 || current.signum() < 0) {
            throw new IllegalArgumentException("Measurements cannot be negative");
        }

        if (baseline.signum() == 0) {
            return null;
        }

        return current.subtract(baseline)
                .multiply(BigDecimal.valueOf(100))
                .divide(baseline, 2, RoundingMode.HALF_UP);
    }

    static void printReport(AnalyticsReport report) {
        System.out.println("\nRegional sales report");
        System.out.printf("%-12s %18s%n", "Region", "Sales amount");

        Map<Region, BigDecimal> sorted = new TreeMap<>(
                (left, right) -> left.name().compareTo(right.name())
        );
        sorted.putAll(report.regionalSales());

        sorted.forEach((region, amount) ->
                System.out.printf(
                        "%-12s %18s%n",
                        region,
                        amount.toPlainString()
                )
        );

        System.out.println("Total sales: " + report.totalSales().toPlainString());

        if (report.accepted().isEmpty()) {
            System.out.println("Average order value: unavailable");
        } else {
            BigDecimal average = report.totalSales().divide(
                    BigDecimal.valueOf(report.accepted().size()),
                    2,
                    RoundingMode.HALF_UP
            );
            System.out.println("Average order value: " + average.toPlainString());
        }

        System.out.println("\nRejected records");
        for (RejectedRecord rejected : report.rejected()) {
            System.out.println(rejected.id() + ": " + String.join("; ", rejected.errors()));
        }
    }

    public static void main(String[] args) {
        System.out.println("Enterprise operations analytics");

        AnalyticsService service = new AnalyticsService();

        service.ingest("TX-1001", Region.NORTH, "12", "1499.50");
        service.ingest("TX-1002", Region.SOUTH, "8", "2200.00");
        service.ingest("TX-1003", Region.NORTH, "5", "999.00");
        service.ingest("TX-1002", Region.EAST, "3", "750.00");
        service.ingest("TX-1004", Region.WEST, "-2", "100.00");
        service.ingest("TX-1005", Region.EAST, "4", "invalid");
        service.ingest("TX-1006", Region.SOUTH, "2", "10.123");

        AnalyticsReport report = service.report();
        printReport(report);

        System.out.println("\nRevenue growth");
        BigDecimal growth = percentageChange(
                new BigDecimal("790000.00"),
                new BigDecimal("850000.00")
        );
        System.out.println("Growth percentage: " + growth + "%");

        BigDecimal undefinedGrowth = percentageChange(
                BigDecimal.ZERO,
                new BigDecimal("100.00")
        );
        System.out.println("Growth with zero baseline: " + undefinedGrowth);

        System.out.println("\nType and expression behavior");
        int units = 1250;
        BigDecimal revenue = new BigDecimal("850000.00");
        System.out.println("Average revenue per unit: " +
                revenue.divide(BigDecimal.valueOf(units), 2, RoundingMode.HALF_UP));

        try {
            new Transaction(
                    "TX-INVALID",
                    Region.NORTH,
                    0,
                    new BigDecimal("10.00")
            );
        } catch (IllegalArgumentException exception) {
            System.out.println("Invalid transaction rejected: " + exception.getMessage());
        }

        System.out.println("\nAnalytics execution completed.");
    }
}
