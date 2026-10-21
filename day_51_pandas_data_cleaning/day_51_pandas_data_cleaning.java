import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class DataCleaningEnterprise {

    enum CustomerSegment {
        STANDARD,
        PREMIUM,
        ENTERPRISE
    }

    record RawCustomer(
        int customerId,
        String name,
        String age,
        String email,
        String city,
        String segment,
        String signupDate,
        String orders
    ) {}

    record Customer(
        int customerId,
        String name,
        Integer age,
        String email,
        String city,
        CustomerSegment segment,
        LocalDate signupDate,
        Integer orders
    ) {}

    record CleaningMetrics(
        int inputRows,
        int invalidValues,
        int duplicatesRemoved,
        int outputRows
    ) {}

    static final class DataValidationException extends Exception {
        DataValidationException(String message) {
            super(message);
        }
    }

    static final class CleaningService {
        private static final Pattern EMAIL_PATTERN =
            Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");

        private final Set<CustomerSegment> allowedSegments =
            EnumSet.allOf(CustomerSegment.class);

        private int invalidValues;
        private int duplicatesRemoved;

        private String cleanText(String value) {
            if (value == null) {
                return null;
            }

            String cleaned = value.trim().replaceAll("\\s+", " ");

            if (cleaned.isEmpty() || cleaned.equalsIgnoreCase("unknown")) {
                return null;
            }

            return cleaned;
        }

        private String titleCase(String value) {
            String cleaned = cleanText(value);

            if (cleaned == null) {
                return null;
            }

            return java.util.Arrays.stream(
                    cleaned.toLowerCase(Locale.ROOT).split(" ")
                )
                .filter(part -> !part.isBlank())
                .map(part ->
                    Character.toUpperCase(part.charAt(0)) +
                    part.substring(1)
                )
                .collect(Collectors.joining(" "));
        }

        private Integer parseInteger(
            String value,
            int minimum,
            int maximum
        ) {
            String cleaned = cleanText(value);

            if (cleaned == null) {
                return null;
            }

            try {
                int number = Integer.parseInt(cleaned);

                if (number < minimum || number > maximum) {
                    invalidValues++;
                    return null;
                }

                return number;
            } catch (NumberFormatException exception) {
                invalidValues++;
                return null;
            }
        }

        private String normalizeEmail(String value) {
            String cleaned = cleanText(value);

            if (cleaned == null) {
                return null;
            }

            String email = cleaned.toLowerCase(Locale.ROOT);

            if (!EMAIL_PATTERN.matcher(email).matches()) {
                invalidValues++;
                return null;
            }

            return email;
        }

        private LocalDate parseDate(String value) {
            String cleaned = cleanText(value);

            if (cleaned == null) {
                return null;
            }

            String normalized = cleaned.replace('/', '-');

            try {
                return LocalDate.parse(
                    normalized,
                    DateTimeFormatter.ISO_LOCAL_DATE
                );
            } catch (DateTimeParseException exception) {
                invalidValues++;
                return null;
            }
        }

        private CustomerSegment parseSegment(String value)
            throws DataValidationException {

            String cleaned = cleanText(value);

            if (cleaned == null) {
                return CustomerSegment.STANDARD;
            }

            try {
                CustomerSegment segment =
                    CustomerSegment.valueOf(
                        cleaned.toUpperCase(Locale.ROOT)
                    );

                if (!allowedSegments.contains(segment)) {
                    throw new DataValidationException(
                        "Segment is not permitted: " + value
                    );
                }

                return segment;
            } catch (IllegalArgumentException exception) {
                throw new DataValidationException(
                    "Invalid customer segment: " + value
                );
            }
        }

        private Customer normalize(RawCustomer raw)
            throws DataValidationException {

            return new Customer(
                raw.customerId(),
                Optional.ofNullable(titleCase(raw.name()))
                    .orElse("Unknown Customer"),
                parseInteger(raw.age(), 18, 100),
                normalizeEmail(raw.email()),
                Optional.ofNullable(titleCase(raw.city()))
                    .orElse("Unknown"),
                parseSegment(raw.segment()),
                parseDate(raw.signupDate()),
                parseInteger(raw.orders(), 0, 1_000_000)
            );
        }

        private List<Customer> removeDuplicates(
            List<Customer> customers
        ) {
            Set<Integer> customerIds = new HashSet<>();
            Set<String> emails = new HashSet<>();
            List<Customer> unique = new ArrayList<>();

            for (Customer customer : customers) {
                if (!customerIds.add(customer.customerId())) {
                    duplicatesRemoved++;
                    continue;
                }

                if (customer.email() != null &&
                    !emails.add(customer.email())) {
                    duplicatesRemoved++;
                    continue;
                }

                unique.add(customer);
            }

            return unique;
        }

        private Integer median(List<Integer> values) {
            if (values.isEmpty()) {
                return null;
            }

            List<Integer> sorted = new ArrayList<>(values);
            sorted.sort(Comparator.naturalOrder());

            int middle = sorted.size() / 2;

            if (sorted.size() % 2 == 1) {
                return sorted.get(middle);
            }

            return Math.round(
                (sorted.get(middle - 1) + sorted.get(middle)) / 2.0f
            );
        }

        private List<Customer> imputeMissingValues(
            List<Customer> customers
        ) {
            Integer ageMedian = median(
                customers.stream()
                    .map(Customer::age)
                    .filter(Objects::nonNull)
                    .toList()
            );

            Integer orderMedian = median(
                customers.stream()
                    .map(Customer::orders)
                    .filter(Objects::nonNull)
                    .toList()
            );

            return customers.stream()
                .map(customer -> new Customer(
                    customer.customerId(),
                    customer.name(),
                    customer.age() == null
                        ? ageMedian
                        : customer.age(),
                    customer.email(),
                    customer.city(),
                    customer.segment(),
                    customer.signupDate(),
                    customer.orders() == null
                        ? orderMedian
                        : customer.orders()
                ))
                .toList();
        }

        List<Customer> clean(List<RawCustomer> source)
            throws DataValidationException {

            List<Customer> normalized = source.stream()
                .map(raw -> {
                    try {
                        return normalize(raw);
                    } catch (DataValidationException exception) {
                        throw new RuntimeException(exception);
                    }
                })
                .toList();

            List<Customer> unique = removeDuplicates(normalized);
            return imputeMissingValues(unique);
        }

        CleaningMetrics metrics(int inputRows, int outputRows) {
            return new CleaningMetrics(
                inputRows,
                invalidValues,
                duplicatesRemoved,
                outputRows
            );
        }
    }

    private static List<RawCustomer> sampleData() {
        return List.of(
            new RawCustomer(
                101, " Alice  Sharma ", "29",
                " ALICE.SHARMA@EXAMPLE.COM ", "Lucknow",
                "Premium", "2026-01-15", "12"
            ),
            new RawCustomer(
                102, "Bob Khan", "",
                "bob.khan@example.com", "Delhi",
                "Standard", "2026/02/20", "5"
            ),
            new RawCustomer(
                103, "Charlie  Rao", "34",
                "", "Mumbai",
                "Premium", "2026-03-10", "8"
            ),
            new RawCustomer(
                104, "Alice  Sharma", "29",
                "alice.sharma@example.com", "Lucknow",
                "Premium", "2026-01-15", "12"
            ),
            new RawCustomer(
                105, "David Mehta", "unknown",
                "david.mehta@example.com", "Delhi",
                "standard", "2026-04-05", "3"
            ),
            new RawCustomer(
                106, "Esha Patel", "41",
                "esha.patel@example.com", " ",
                "Enterprise", "2026-05-11", "21"
            ),
            new RawCustomer(
                107, "Farhan Ali", "37",
                "farhan.ali@example.com", "Bengaluru",
                "Standard", "invalid", "7"
            ),
            new RawCustomer(
                108, "", "26",
                "neha@example.com", "Pune",
                "Standard", "2026-06-30", "2"
            ),
            new RawCustomer(
                109, "George Sen", "-5",
                "george.sen@example.com", "Chennai",
                "Premium", "2026-07-01", "15"
            ),
            new RawCustomer(
                110, "Hina Roy", "30",
                "hina.roy@example.com", "Kolkata",
                "premium", "2026-07-18", "10"
            )
        );
    }

    public static void main(String[] args) {
        CleaningService service = new CleaningService();

        try {
            List<Customer> cleaned = service.clean(sampleData());

            System.out.printf(
                "%-5s %-20s %-6s %-30s %-14s %-12s %-12s %-7s%n",
                "ID", "Name", "Age", "Email",
                "City", "Segment", "Signup", "Orders"
            );

            System.out.println("-".repeat(115));

            for (Customer customer : cleaned) {
                System.out.printf(
                    "%-5d %-20s %-6s %-30s %-14s %-12s %-12s %-7s%n",
                    customer.customerId(),
                    customer.name(),
                    String.valueOf(customer.age()),
                    String.valueOf(customer.email()),
                    customer.city(),
                    customer.segment(),
                    String.valueOf(customer.signupDate()),
                    String.valueOf(customer.orders())
                );
            }

            CleaningMetrics metrics =
                service.metrics(sampleData().size(), cleaned.size());

            System.out.println("\nCleaning metrics");
            System.out.println(metrics);

            System.out.println("\nSegment counts");

            cleaned.stream()
                .collect(Collectors.groupingBy(
                    Customer::segment,
                    Collectors.counting()
                ))
                .forEach((segment, count) ->
                    System.out.println(segment + ": " + count)
                );

            /*
             * Domain decisions:
             * - CustomerSegment is an enum, preventing arbitrary categories.
             * - Customer is immutable because it is a record.
             * - Invalid numeric/date values become null rather than being
             *   converted to misleading defaults.
             * - Email remains nullable because a fabricated address is worse
             *   than an explicitly missing identity attribute.
             */
        } catch (RuntimeException exception) {
            Throwable cause = exception.getCause();

            if (cause instanceof DataValidationException validationError) {
                System.err.println(
                    "Validation failed: " + validationError.getMessage()
                );
            } else {
                System.err.println(
                    "Cleaning failed: " + exception.getMessage()
                );
            }

            System.exit(1);
        } catch (Exception exception) {
            System.err.println(
                "Unexpected cleaning failure: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
