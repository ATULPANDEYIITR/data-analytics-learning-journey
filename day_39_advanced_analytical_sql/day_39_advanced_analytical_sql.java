import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.stream.Collectors;

/**
 * Enterprise analytical reporting for a multi-region distribution business.
 *
 * The model distinguishes row-based rolling windows from calendar-day
 * windows, uses exact decimal money values, and treats missing reporting
 * dates as a separate data-quality condition.
 *
 * Compile and run:
 *   javac AdvancedAnalyticalSql.java
 *   java AdvancedAnalyticalSql
 */
public class AdvancedAnalyticalSql {

    enum Status {
        COMPLETED,
        CANCELLED,
        PENDING
    }

    record DailyRecord(
        LocalDate date,
        String department,
        BigDecimal revenue,
        int orders,
        Status status
    ) {
        DailyRecord {
            if (date == null || status == null) {
                throw new IllegalArgumentException("Date and status are required.");
            }
            if (department == null || department.isBlank()) {
                throw new IllegalArgumentException("Department is required.");
            }
            if (revenue == null || revenue.signum() < 0) {
                throw new IllegalArgumentException("Revenue must be nonnegative.");
            }
            if (orders < 0) {
                throw new IllegalArgumentException("Orders must be nonnegative.");
            }
        }
    }

    record PercentileReport(
        BigDecimal percentile,
        BigDecimal continuous,
        BigDecimal discrete
    ) {}

    record Island(LocalDate start, LocalDate end, long days) {}

    record Gap(LocalDate start, LocalDate end, long missingDays) {}

    record RollingResult(
        LocalDate date,
        BigDecimal dailyRevenue,
        BigDecimal rollingRevenue,
        BigDecimal rollingAverage,
        int frameRows
    ) {}

    record DepartmentSummary(
        String department,
        BigDecimal completedRevenue,
        long completedOrders,
        long cancelledOrders,
        long completedDays,
        long cancelledDays,
        long pendingDays,
        BigDecimal medianCompletedDailyRevenue
    ) {}

    static final BigDecimal ZERO = new BigDecimal("0.00");

    static BigDecimal money(String value) {
        return new BigDecimal(value).setScale(2, RoundingMode.HALF_UP);
    }

    static BigDecimal average(List<BigDecimal> values) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException("Average requires observations.");
        }

        BigDecimal total = values.stream()
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        return total.divide(
            BigDecimal.valueOf(values.size()),
            4,
            RoundingMode.HALF_UP
        );
    }

    static BigDecimal percentileCont(List<BigDecimal> input, BigDecimal p) {
        validatePercentile(p);

        if (input.isEmpty()) {
            throw new IllegalArgumentException("Percentile requires observations.");
        }

        List<BigDecimal> sorted = input.stream().sorted().toList();
        BigDecimal position = p.multiply(BigDecimal.valueOf(sorted.size() - 1));

        int lowerIndex = position.intValue();
        int upperIndex = Math.min(lowerIndex + 1, sorted.size() - 1);
        BigDecimal fraction = position.subtract(BigDecimal.valueOf(lowerIndex));

        BigDecimal lower = sorted.get(lowerIndex);
        BigDecimal upper = sorted.get(upperIndex);

        return lower.add(upper.subtract(lower).multiply(fraction));
    }

    static BigDecimal percentileDisc(List<BigDecimal> input, BigDecimal p) {
        validatePercentile(p);

        if (input.isEmpty()) {
            throw new IllegalArgumentException("Percentile requires observations.");
        }

        List<BigDecimal> sorted = input.stream().sorted().toList();
        int index = p.multiply(BigDecimal.valueOf(sorted.size()))
            .setScale(0, RoundingMode.CEILING)
            .intValue() - 1;

        index = Math.max(0, index);
        return sorted.get(index);
    }

    static void validatePercentile(BigDecimal p) {
        if (p == null || p.compareTo(BigDecimal.ZERO) < 0
                || p.compareTo(BigDecimal.ONE) > 0) {
            throw new IllegalArgumentException("Percentile must be in [0, 1].");
        }
    }

    static List<PercentileReport> percentiles(List<BigDecimal> values) {
        List<PercentileReport> reports = new ArrayList<>();

        for (String value : List.of("0.25", "0.50", "0.75", "0.90", "0.95")) {
            BigDecimal p = new BigDecimal(value);
            reports.add(new PercentileReport(
                p,
                percentileCont(values, p),
                percentileDisc(values, p)
            ));
        }

        return reports;
    }

    static List<DepartmentSummary> summarize(List<DailyRecord> records) {
        Map<String, List<DailyRecord>> partitions = records.stream()
            .collect(Collectors.groupingBy(
                DailyRecord::department,
                TreeMap::new,
                Collectors.toList()
            ));

        List<DepartmentSummary> summaries = new ArrayList<>();

        for (var entry : partitions.entrySet()) {
            BigDecimal completedRevenue = BigDecimal.ZERO;
            long completedOrders = 0;
            long cancelledOrders = 0;
            long completedDays = 0;
            long cancelledDays = 0;
            long pendingDays = 0;
            List<BigDecimal> completedValues = new ArrayList<>();

            for (DailyRecord record : entry.getValue()) {
                switch (record.status()) {
                    case COMPLETED -> {
                        completedRevenue = completedRevenue.add(record.revenue());
                        completedOrders += record.orders();
                        completedDays++;
                        completedValues.add(record.revenue());
                    }
                    case CANCELLED -> {
                        cancelledOrders += record.orders();
                        cancelledDays++;
                    }
                    case PENDING -> pendingDays++;
                }
            }

            BigDecimal medianValue = completedValues.isEmpty()
                ? null
                : percentileCont(completedValues, new BigDecimal("0.50"));

            summaries.add(new DepartmentSummary(
                entry.getKey(),
                completedRevenue,
                completedOrders,
                cancelledOrders,
                completedDays,
                cancelledDays,
                pendingDays,
                medianValue
            ));
        }

        return summaries;
    }

    static List<RollingResult> rollingRows(
        List<DailyRecord> records,
        int frameSize
    ) {
        if (frameSize < 1) {
            throw new IllegalArgumentException("Frame size must be positive.");
        }

        Map<String, List<DailyRecord>> partitions = records.stream()
            .collect(Collectors.groupingBy(DailyRecord::department));

        List<RollingResult> result = new ArrayList<>();

        for (List<DailyRecord> partition : partitions.values()) {
            partition.sort(Comparator.comparing(DailyRecord::date));

            for (int index = 0; index < partition.size(); index++) {
                int start = Math.max(0, index - frameSize + 1);

                List<BigDecimal> values = partition.subList(start, index + 1)
                    .stream()
                    .map(DailyRecord::revenue)
                    .toList();

                BigDecimal total = values.stream()
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

                result.add(new RollingResult(
                    partition.get(index).date(),
                    partition.get(index).revenue(),
                    total,
                    average(values),
                    values.size()
                ));
            }
        }

        result.sort(
            Comparator.comparing(RollingResult::date)
                .thenComparing(RollingResult::dailyRevenue)
        );

        return result;
    }

    static Map<LocalDate, BigDecimal> calendarRollingRevenue(
        List<DailyRecord> records,
        LocalDate first,
        LocalDate last,
        int frameDays
    ) {
        if (first.isAfter(last) || frameDays < 1) {
            throw new IllegalArgumentException("Invalid date range or frame size.");
        }

        Map<LocalDate, BigDecimal> dailyTotals = new TreeMap<>();
        for (DailyRecord record : records) {
            dailyTotals.merge(record.date(), record.revenue(), BigDecimal::add);
        }

        Map<LocalDate, BigDecimal> result = new TreeMap<>();

        for (LocalDate current = first; !current.isAfter(last);
                current = current.plusDays(1)) {
            BigDecimal total = BigDecimal.ZERO;

            for (int offset = 0; offset < frameDays; offset++) {
                LocalDate frameDate = current.minusDays(offset);
                total = total.add(dailyTotals.getOrDefault(frameDate, BigDecimal.ZERO));
            }

            result.put(current, total);
        }

        return result;
    }

    static List<Island> findIslands(List<LocalDate> input) {
        List<LocalDate> dates = input.stream().distinct().sorted().toList();
        if (dates.isEmpty()) return List.of();

        List<Island> result = new ArrayList<>();
        LocalDate start = dates.get(0);
        LocalDate previous = start;

        for (LocalDate current : dates.subList(1, dates.size())) {
            if (!current.equals(previous.plusDays(1))) {
                result.add(new Island(
                    start,
                    previous,
                    ChronoUnit.DAYS.between(start, previous) + 1
                ));
                start = current;
            }
            previous = current;
        }

        result.add(new Island(
            start,
            previous,
            ChronoUnit.DAYS.between(start, previous) + 1
        ));

        return result;
    }

    static List<Gap> findGaps(
        List<LocalDate> input,
        LocalDate first,
        LocalDate last
    ) {
        if (first.isAfter(last)) {
            throw new IllegalArgumentException("Start date exceeds end date.");
        }

        Set<LocalDate> observed = input.stream()
            .filter(date -> !date.isBefore(first) && !date.isAfter(last))
            .collect(Collectors.toCollection(HashSet::new));

        List<Gap> result = new ArrayList<>();
        LocalDate gapStart = null;

        for (LocalDate current = first; !current.isAfter(last);
                current = current.plusDays(1)) {
            if (!observed.contains(current) && gapStart == null) {
                gapStart = current;
            } else if (observed.contains(current) && gapStart != null) {
                LocalDate gapEnd = current.minusDays(1);
                result.add(new Gap(
                    gapStart,
                    gapEnd,
                    ChronoUnit.DAYS.between(gapStart, gapEnd) + 1
                ));
                gapStart = null;
            }
        }

        if (gapStart != null) {
            result.add(new Gap(
                gapStart,
                last,
                ChronoUnit.DAYS.between(gapStart, last) + 1
            ));
        }

        return result;
    }

    static List<DailyRecord> sampleData() {
        return List.of(
            new DailyRecord(LocalDate.parse("2026-09-01"), "North", money("1200"), 24, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-02"), "North", money("1350"), 27, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-03"), "North", money("0"), 0, Status.CANCELLED),
            new DailyRecord(LocalDate.parse("2026-09-04"), "North", money("1820"), 36, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-06"), "North", money("1600"), 32, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-07"), "North", money("1750"), 35, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-08"), "North", money("2100"), 42, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-09"), "North", money("900"), 18, Status.PENDING),
            new DailyRecord(LocalDate.parse("2026-09-10"), "North", money("2400"), 48, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-11"), "North", money("1950"), 39, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-12"), "North", money("2600"), 52, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-13"), "North", money("800"), 16, Status.CANCELLED),
            new DailyRecord(LocalDate.parse("2026-09-15"), "North", money("2850"), 57, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-16"), "North", money("3000"), 60, Status.COMPLETED),
            new DailyRecord(LocalDate.parse("2026-09-17"), "North", money("2750"), 55, Status.COMPLETED)
        );
    }

    static void runTests() {
        List<BigDecimal> values = List.of(
            money("10"), money("20"), money("30"), money("40")
        );

        if (percentileCont(values, new BigDecimal("0.5"))
                .compareTo(money("25")) != 0) {
            throw new AssertionError("Continuous percentile test failed.");
        }

        if (percentileDisc(values, new BigDecimal("0.5"))
                .compareTo(money("20")) != 0) {
            throw new AssertionError("Discrete percentile test failed.");
        }

        List<Island> islands = findIslands(List.of(
            LocalDate.parse("2026-01-01"),
            LocalDate.parse("2026-01-02"),
            LocalDate.parse("2026-01-04")
        ));

        if (islands.size() != 2 || islands.get(0).days() != 2) {
            throw new AssertionError("Island test failed.");
        }

        boolean rejected = false;
        try {
            percentileCont(List.of(), new BigDecimal("0.5"));
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }

        if (!rejected) throw new AssertionError("Empty sample was accepted.");

        System.out.println("All Java self-tests passed.");
    }

    public static void main(String[] args) {
        runTests();

        List<DailyRecord> records = sampleData();

        System.out.println("\nDepartment summaries");
        for (DepartmentSummary summary : summarize(records)) {
            System.out.printf(
                "%s | completed revenue %s | completed orders %d"
                    + " | cancelled orders %d | median completed revenue %s%n",
                summary.department(),
                summary.completedRevenue().setScale(2, RoundingMode.HALF_UP),
                summary.completedOrders(),
                summary.cancelledOrders(),
                summary.medianCompletedDailyRevenue() == null
                    ? "N/A"
                    : summary.medianCompletedDailyRevenue()
                        .setScale(2, RoundingMode.HALF_UP)
            );
        }

        List<BigDecimal> completedValues = records.stream()
            .filter(record -> record.department().equals("North"))
            .filter(record -> record.status() == Status.COMPLETED)
            .map(DailyRecord::revenue)
            .toList();

        System.out.println("\nNorth revenue percentile report");
        for (PercentileReport report : percentiles(completedValues)) {
            System.out.printf(
                "p=%s continuous=%s discrete=%s%n",
                report.percentile(),
                report.continuous().setScale(2, RoundingMode.HALF_UP),
                report.discrete().setScale(2, RoundingMode.HALF_UP)
            );
        }

        System.out.println("\nTrailing three-row windows");
        for (RollingResult result : rollingRows(records, 3)) {
            System.out.printf(
                "%s | daily=%s | rolling=%s | average=%s | rows=%d%n",
                result.date(),
                result.dailyRevenue().setScale(2, RoundingMode.HALF_UP),
                result.rollingRevenue().setScale(2, RoundingMode.HALF_UP),
                result.rollingAverage().setScale(2, RoundingMode.HALF_UP),
                result.frameRows()
            );
        }

        LocalDate first = LocalDate.parse("2026-09-01");
        LocalDate last = LocalDate.parse("2026-09-17");
        List<LocalDate> dates = records.stream().map(DailyRecord::date).toList();

        System.out.println("\nConsecutive reporting islands");
        for (Island island : findIslands(dates)) {
            System.out.printf(
                "%s to %s (%d days)%n",
                island.start(), island.end(), island.days()
            );
        }

        System.out.println("\nMissing reporting intervals");
        for (Gap gap : findGaps(dates, first, last)) {
            System.out.printf(
                "%s to %s (%d missing days)%n",
                gap.start(), gap.end(), gap.missingDays()
            );
        }

        Map<LocalDate, BigDecimal> calendarWindow = calendarRollingRevenue(
            records, first, last, 7
        );
        System.out.println("\nSeven-calendar-day rolling revenue");
        calendarWindow.forEach((date, total) ->
            System.out.printf("%s | %s%n", date, total.setScale(2, RoundingMode.HALF_UP))
        );
    }
}
