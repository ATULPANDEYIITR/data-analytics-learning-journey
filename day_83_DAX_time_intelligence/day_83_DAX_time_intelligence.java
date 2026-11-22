import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;

public class TimeIntelligenceEnterprise {

    enum PeriodType {
        MTD,
        QTD,
        YTD
    }

    enum DateUnit {
        DAY,
        MONTH,
        YEAR
    }

    record Transaction(
        long id,
        LocalDate transactionDate,
        String product,
        String region,
        BigDecimal amount
    ) {
        Transaction {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Transaction ID must be positive."
                );
            }

            Objects.requireNonNull(transactionDate);
            Objects.requireNonNull(amount);

            if (product == null || product.isBlank()) {
                throw new IllegalArgumentException("Product is required.");
            }

            if (region == null || region.isBlank()) {
                throw new IllegalArgumentException("Region is required.");
            }

            if (amount.signum() < 0) {
                throw new IllegalArgumentException(
                    "Sales amount cannot be negative."
                );
            }
        }
    }

    record Comparison(
        BigDecimal current,
        BigDecimal previous,
        BigDecimal difference,
        BigDecimal percentageChange
    ) {}

    static class CalendarDimension {
        private final LocalDate start;
        private final LocalDate end;
        private final Set<LocalDate> dates;

        CalendarDimension(LocalDate start, LocalDate end) {
            if (start == null || end == null || start.isAfter(end)) {
                throw new IllegalArgumentException(
                    "Invalid calendar boundaries."
                );
            }

            this.start = start;
            this.end = end;
            this.dates = new HashSet<>();

            for (
                LocalDate current = start;
                !current.isAfter(end);
                current = current.plusDays(1)
            ) {
                dates.add(current);
            }
        }

        List<LocalDate> validate(Collection<LocalDate> selection) {
            if (selection == null || selection.isEmpty()) {
                throw new IllegalArgumentException(
                    "Date selection cannot be empty."
                );
            }

            TreeSet<LocalDate> sorted = new TreeSet<>(selection);

            if (sorted.contains(null)) {
                throw new IllegalArgumentException("Null date found.");
            }

            for (LocalDate date : sorted) {
                if (!dates.contains(date)) {
                    throw new IllegalArgumentException(
                        "Date outside calendar: " + date
                    );
                }
            }

            return List.copyOf(sorted);
        }

        List<LocalDate> range(LocalDate from, LocalDate to) {
            if (from.isAfter(to)) {
                throw new IllegalArgumentException("Invalid date range.");
            }

            List<LocalDate> result = new ArrayList<>();

            for (
                LocalDate current = from;
                !current.isAfter(to);
                current = current.plusDays(1)
            ) {
                if (dates.contains(current)) {
                    result.add(current);
                }
            }

            return result;
        }

        boolean contains(LocalDate date) {
            return dates.contains(date);
        }
    }

    static class SalesRepository {
        private final CalendarDimension calendar;
        private final Map<LocalDate, BigDecimal> dailySales =
            new HashMap<>();

        private final Map<Long, Transaction> transactions =
            new HashMap<>();

        private long revision = 0;

        SalesRepository(CalendarDimension calendar) {
            this.calendar = Objects.requireNonNull(calendar);
        }

        synchronized void insert(Transaction transaction) {
            Objects.requireNonNull(transaction);

            if (!calendar.contains(transaction.transactionDate())) {
                throw new IllegalArgumentException(
                    "Transaction date outside calendar."
                );
            }

            if (transactions.containsKey(transaction.id())) {
                throw new IllegalStateException(
                    "Duplicate transaction ID."
                );
            }

            transactions.put(transaction.id(), transaction);

            dailySales.merge(
                transaction.transactionDate(),
                transaction.amount(),
                BigDecimal::add
            );

            revision++;
        }

        synchronized BigDecimal aggregate(
            Collection<LocalDate> selectedDates
        ) {
            List<LocalDate> dates = calendar.validate(selectedDates);

            return dates.stream()
                .map(d -> dailySales.getOrDefault(
                    d, BigDecimal.ZERO
                ))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        synchronized Map<String, BigDecimal> aggregateByRegion(
            Collection<LocalDate> selectedDates
        ) {
            Set<LocalDate> selected = new HashSet<>(
                calendar.validate(selectedDates)
            );

            return transactions.values().stream()
                .filter(t -> selected.contains(t.transactionDate()))
                .collect(Collectors.groupingBy(
                    Transaction::region,
                    Collectors.mapping(
                        Transaction::amount,
                        Collectors.reducing(
                            BigDecimal.ZERO,
                            BigDecimal::add
                        )
                    )
                ));
        }

        long revision() {
            return revision;
        }
    }

    static class TimeIntelligenceService {
        private final CalendarDimension calendar;
        private final SalesRepository repository;

        TimeIntelligenceService(
            CalendarDimension calendar,
            SalesRepository repository
        ) {
            this.calendar = calendar;
            this.repository = repository;
        }

        List<LocalDate> dateadd(
            Collection<LocalDate> selection,
            DateUnit unit,
            long offset
        ) {
            List<LocalDate> dates = calendar.validate(selection);

            return dates.stream()
                .map(d -> shift(d, unit, offset))
                .filter(calendar::contains)
                .distinct()
                .sorted()
                .toList();
        }

        private LocalDate shift(
            LocalDate date,
            DateUnit unit,
            long offset
        ) {
            return switch (unit) {
                case DAY -> date.plusDays(offset);
                case MONTH -> shiftMonth(date, offset);
                case YEAR -> shiftYear(date, offset);
            };
        }

        private LocalDate shiftMonth(LocalDate date, long offset) {
            YearMonth original = YearMonth.from(date);
            YearMonth target = original.plusMonths(offset);

            boolean wasLastDay =
                date.getDayOfMonth() == original.lengthOfMonth();

            int targetDay = wasLastDay
                ? target.lengthOfMonth()
                : Math.min(
                    date.getDayOfMonth(),
                    target.lengthOfMonth()
                );

            return target.atDay(targetDay);
        }

        private LocalDate shiftYear(LocalDate date, long offset) {
            int targetYear = Math.toIntExact(
                date.getYear() + offset
            );

            int targetDay = date.getDayOfMonth();

            if (date.getMonthValue() == 2 && targetDay == 29) {
                targetDay = 28;
            }

            return LocalDate.of(
                targetYear,
                date.getMonthValue(),
                targetDay
            );
        }

        BigDecimal samePeriodLastYear(
            Collection<LocalDate> selection
        ) {
            return repository.aggregate(
                dateadd(selection, DateUnit.YEAR, -1)
            );
        }

        BigDecimal periodToDate(
            Collection<LocalDate> selection,
            PeriodType type
        ) {
            List<LocalDate> dates = calendar.validate(selection);

            LocalDate end = dates.get(dates.size() - 1);

            LocalDate start = switch (type) {
                case MTD -> end.withDayOfMonth(1);
                case QTD -> end.withMonth(
                    ((end.getMonthValue() - 1) / 3) * 3 + 1
                ).withDayOfMonth(1);
                case YTD -> end.withDayOfYear(1);
            };

            return repository.aggregate(
                calendar.range(start, end)
            );
        }

        BigDecimal rolling(
            Collection<LocalDate> selection,
            int numberOfDays
        ) {
            List<LocalDate> dates = calendar.validate(selection);

            if (numberOfDays <= 0) {
                throw new IllegalArgumentException(
                    "Rolling window must be positive."
                );
            }

            LocalDate end = dates.get(dates.size() - 1);
            LocalDate start = end.minusDays(numberOfDays - 1L);

            return repository.aggregate(
                calendar.range(start, end)
            );
        }

        Comparison compareWithPreviousYear(
            Collection<LocalDate> selection
        ) {
            BigDecimal current = repository.aggregate(selection);
            BigDecimal previous = samePeriodLastYear(selection);

            BigDecimal difference = current.subtract(previous);

            BigDecimal percentage = previous.signum() == 0
                ? null
                : difference.multiply(BigDecimal.valueOf(100))
                    .divide(previous, 2, RoundingMode.HALF_UP);

            return new Comparison(
                current,
                previous,
                difference,
                percentage
            );
        }
    }

    private static void loadSampleData(
        SalesRepository repository
    ) {
        List<Transaction> records = List.of(
            new Transaction(1, LocalDate.of(2024, 1, 15),
                "Laptop", "North", new BigDecimal("12000")),
            new Transaction(2, LocalDate.of(2024, 2, 10),
                "Phone", "South", new BigDecimal("8000")),
            new Transaction(3, LocalDate.of(2025, 1, 15),
                "Laptop", "North", new BigDecimal("16000")),
            new Transaction(4, LocalDate.of(2025, 2, 10),
                "Phone", "South", new BigDecimal("11000")),
            new Transaction(5, LocalDate.of(2025, 3, 20),
                "Laptop", "West", new BigDecimal("18000")),
            new Transaction(6, LocalDate.of(2025, 4, 12),
                "Tablet", "East", new BigDecimal("9000")),
            new Transaction(7, LocalDate.of(2026, 1, 15),
                "Laptop", "North", new BigDecimal("21000")),
            new Transaction(8, LocalDate.of(2026, 2, 10),
                "Phone", "South", new BigDecimal("14000")),
            new Transaction(9, LocalDate.of(2026, 3, 20),
                "Laptop", "West", new BigDecimal("24000")),
            new Transaction(10, LocalDate.of(2026, 4, 12),
                "Tablet", "East", new BigDecimal("12000")),
            new Transaction(11, LocalDate.of(2026, 5, 18),
                "Phone", "North", new BigDecimal("10000")),
            new Transaction(12, LocalDate.of(2026, 6, 22),
                "Laptop", "South", new BigDecimal("19000")),
            new Transaction(13, LocalDate.of(2026, 7, 14),
                "Tablet", "West", new BigDecimal("13000")),
            new Transaction(14, LocalDate.of(2026, 8, 9),
                "Phone", "East", new BigDecimal("8500")),
            new Transaction(15, LocalDate.of(2026, 9, 11),
                "Laptop", "North", new BigDecimal("22000")),
            new Transaction(16, LocalDate.of(2026, 10, 19),
                "Tablet", "South", new BigDecimal("11500")),
            new Transaction(17, LocalDate.of(2026, 11, 5),
                "Phone", "West", new BigDecimal("9500")),
            new Transaction(18, LocalDate.of(2026, 11, 15),
                "Laptop", "East", new BigDecimal("17000"))
        );

        records.forEach(repository::insert);
    }

    private static void runTests(
        TimeIntelligenceService service,
        SalesRepository repository
    ) {
        if (repository.aggregate(
            List.of(LocalDate.of(2026, 1, 15))
        ).compareTo(new BigDecimal("21000")) != 0) {
            throw new AssertionError("Aggregation failed.");
        }

        if (service.samePeriodLastYear(
            List.of(LocalDate.of(2026, 1, 15))
        ).compareTo(new BigDecimal("16000")) != 0) {
            throw new AssertionError("Previous year failed.");
        }

        if (service.periodToDate(
            List.of(LocalDate.of(2026, 2, 10)),
            PeriodType.YTD
        ).compareTo(new BigDecimal("35000")) != 0) {
            throw new AssertionError("YTD failed.");
        }

        if (!service.dateadd(
            List.of(LocalDate.of(2026, 11, 15)),
            DateUnit.MONTH,
            -1
        ).equals(List.of(LocalDate.of(2026, 10, 15)))) {
            throw new AssertionError("DATEADD failed.");
        }

        try {
            service.rolling(
                List.of(LocalDate.of(2026, 11, 15)),
                0
            );
            throw new AssertionError("Invalid rolling period accepted.");
        } catch (IllegalArgumentException expected) {
            // Expected validation behavior.
        }

        System.out.println("All Java validation tests passed.");
    }

    public static void main(String[] args) {
        try {
            CalendarDimension calendar = new CalendarDimension(
                LocalDate.of(2024, 1, 1),
                LocalDate.of(2026, 12, 31)
            );

            SalesRepository repository = new SalesRepository(calendar);

            loadSampleData(repository);

            TimeIntelligenceService service =
                new TimeIntelligenceService(calendar, repository);

            List<LocalDate> selection = List.of(
                LocalDate.of(2026, 11, 1),
                LocalDate.of(2026, 11, 15)
            );

            Comparison comparison =
                service.compareWithPreviousYear(selection);

            System.out.println("\nENTERPRISE SALES ANALYTICS");
            System.out.println("--------------------------");
            System.out.println("Current: " + comparison.current());
            System.out.println("Previous: " + comparison.previous());
            System.out.println("Difference: " + comparison.difference());
            System.out.println("Growth: " +
                (comparison.percentageChange() == null
                    ? "Undefined"
                    : comparison.percentageChange() + "%"));

            System.out.println("MTD: " +
                service.periodToDate(selection, PeriodType.MTD));

            System.out.println("QTD: " +
                service.periodToDate(selection, PeriodType.QTD));

            System.out.println("YTD: " +
                service.periodToDate(selection, PeriodType.YTD));

            System.out.println("Rolling 30 days: " +
                service.rolling(selection, 30));

            System.out.println("\nREGIONAL SALES");
            service.dateadd(
                selection,
                DateUnit.DAY,
                0
            );

            Map<String, BigDecimal> regional =
                repository.aggregateByRegion(selection);

            regional.forEach((region, amount) ->
                System.out.println(region + ": " + amount)
            );

            runTests(service, repository);

        } catch (Exception error) {
            System.err.println(
                "Analytics execution failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
