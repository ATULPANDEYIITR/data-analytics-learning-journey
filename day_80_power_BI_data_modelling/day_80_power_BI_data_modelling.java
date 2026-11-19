import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * POWER BI DATA MODELING
 *
 * Enterprise-oriented retail semantic model.
 *
 * Java 17, no external dependencies.
 *
 * Features:
 * - Immutable domain records
 * - Fact and dimension separation
 * - Surrogate key validation
 * - Star schema relationship metadata
 * - Cardinality enforcement
 * - Referential integrity
 * - Approval-like model publication lifecycle
 * - Data refresh states
 * - Dimension-based filter propagation
 * - Analytical aggregation
 * - Validation and exception handling
 */

public class PowerBIDataModel {

    enum TableType {
        FACT,
        DIMENSION
    }

    enum Cardinality {
        ONE_TO_ONE,
        ONE_TO_MANY,
        MANY_TO_ONE,
        MANY_TO_MANY
    }

    enum FilterDirection {
        SINGLE,
        BOTH
    }

    enum ModelState {
        DRAFT,
        VALIDATED,
        PUBLISHED,
        FAILED
    }

    static class ModelException extends RuntimeException {
        ModelException(String message) {
            super(message);
        }
    }

    record Product(
        int productKey,
        String name,
        String category,
        String brand
    ) {
        Product {
            if (productKey <= 0) {
                throw new ModelException("Invalid product key");
            }

            Objects.requireNonNull(name);
            Objects.requireNonNull(category);
            Objects.requireNonNull(brand);
        }
    }

    record Customer(
        int customerKey,
        String name,
        String region,
        String segment
    ) {
        Customer {
            if (customerKey <= 0) {
                throw new ModelException("Invalid customer key");
            }

            Objects.requireNonNull(name);
            Objects.requireNonNull(region);
            Objects.requireNonNull(segment);
        }
    }

    record CalendarDate(
        int dateKey,
        LocalDate fullDate,
        int year,
        int month,
        int quarter
    ) {
        CalendarDate {
            Objects.requireNonNull(fullDate);

            if (dateKey <= 0 ||
                month < 1 ||
                month > 12 ||
                quarter < 1 ||
                quarter > 4) {
                throw new ModelException("Invalid date dimension");
            }

            if (fullDate.getYear() != year ||
                fullDate.getMonthValue() != month ||
                (month - 1) / 3 + 1 != quarter) {
                throw new ModelException(
                    "Date attributes are inconsistent"
                );
            }
        }
    }

    record Store(
        int storeKey,
        String name,
        String city
    ) {
        Store {
            if (storeKey <= 0) {
                throw new ModelException("Invalid store key");
            }

            Objects.requireNonNull(name);
            Objects.requireNonNull(city);
        }
    }

    record SalesFact(
        int salesId,
        String orderId,
        int dateKey,
        int productKey,
        int customerKey,
        int storeKey,
        int quantity,
        BigDecimal unitPrice,
        BigDecimal salesAmount
    ) {
        SalesFact {
            if (salesId <= 0 ||
                quantity <= 0 ||
                orderId == null ||
                orderId.isBlank()) {
                throw new ModelException("Invalid sales fact");
            }

            Objects.requireNonNull(unitPrice);
            Objects.requireNonNull(salesAmount);

            if (unitPrice.signum() < 0 ||
                salesAmount.signum() < 0) {
                throw new ModelException(
                    "Negative monetary values are not permitted"
                );
            }

            BigDecimal expected = unitPrice.multiply(
                BigDecimal.valueOf(quantity)
            );

            if (expected.compareTo(salesAmount) != 0) {
                throw new ModelException(
                    "Sales amount calculation mismatch"
                );
            }
        }
    }

    record Relationship(
        String name,
        String fromTable,
        String fromColumn,
        String toTable,
        String toColumn,
        Cardinality cardinality,
        FilterDirection direction,
        boolean active
    ) {
        Relationship {
            Objects.requireNonNull(name);
            Objects.requireNonNull(fromTable);
            Objects.requireNonNull(fromColumn);
            Objects.requireNonNull(toTable);
            Objects.requireNonNull(toColumn);
            Objects.requireNonNull(cardinality);
            Objects.requireNonNull(direction);
        }
    }

    record ValidationResult(
        boolean valid,
        List<String> issues
    ) {
        ValidationResult {
            issues = List.copyOf(issues);
        }
    }

    record ModelMetrics(
        BigDecimal totalSales,
        int totalQuantity,
        long distinctOrders,
        BigDecimal averageOrderValue
    ) {}

    interface ModelPolicy {
        ValidationResult evaluate(RetailRepository repository);
    }

    static class StarSchemaPolicy implements ModelPolicy {

        @Override
        public ValidationResult evaluate(
            RetailRepository repository
        ) {
            List<String> issues = new ArrayList<>();

            Map<String, Long> activeRelationships =
                repository.relationships.stream()
                    .filter(Relationship::active)
                    .collect(Collectors.groupingBy(
                        Relationship::toTable,
                        Collectors.counting()
                    ));

            for (String dimension : List.of(
                "DimProduct",
                "DimCustomer",
                "DimDate",
                "DimStore"
            )) {
                if (activeRelationships.getOrDefault(
                    dimension, 0L
                ) != 1L) {
                    issues.add(
                        dimension +
                        " must have exactly one active fact relationship"
                    );
                }
            }

            for (Relationship relationship :
                repository.relationships) {

                if (!relationship.active) {
                    continue;
                }

                if (relationship.cardinality ==
                    Cardinality.MANY_TO_MANY) {
                    issues.add(
                        relationship.name +
                        ": explicit bridge-table governance required"
                    );
                }

                if (relationship.direction ==
                    FilterDirection.BOTH) {
                    issues.add(
                        relationship.name +
                        ": bidirectional filtering requires ambiguity review"
                    );
                }
            }

            return new ValidationResult(
                issues.isEmpty(),
                issues
            );
        }
    }

    static class RetailRepository {

        final List<Product> products = new ArrayList<>();
        final List<Customer> customers = new ArrayList<>();
        final List<CalendarDate> dates = new ArrayList<>();
        final List<Store> stores = new ArrayList<>();
        final List<SalesFact> facts = new ArrayList<>();

        final List<Relationship> relationships =
            new ArrayList<>();

        final Map<Integer, Product> productIndex =
            new HashMap<>();

        final Map<Integer, Customer> customerIndex =
            new HashMap<>();

        final Map<Integer, CalendarDate> dateIndex =
            new HashMap<>();

        final Map<Integer, Store> storeIndex =
            new HashMap<>();

        final Set<Integer> salesIds = new HashSet<>();

        void addProduct(Product product) {
            if (productIndex.putIfAbsent(
                product.productKey(), product
            ) != null) {
                throw new ModelException(
                    "Duplicate product key"
                );
            }

            products.add(product);
        }

        void addCustomer(Customer customer) {
            if (customerIndex.putIfAbsent(
                customer.customerKey(), customer
            ) != null) {
                throw new ModelException(
                    "Duplicate customer key"
                );
            }

            customers.add(customer);
        }

        void addDate(CalendarDate date) {
            if (dateIndex.putIfAbsent(
                date.dateKey(), date
            ) != null) {
                throw new ModelException("Duplicate date key");
            }

            dates.add(date);
        }

        void addStore(Store store) {
            if (storeIndex.putIfAbsent(
                store.storeKey(), store
            ) != null) {
                throw new ModelException("Duplicate store key");
            }

            stores.add(store);
        }

        void addFact(SalesFact fact) {
            if (salesIds.contains(fact.salesId())) {
                throw new ModelException("Duplicate sales ID");
            }

            if (!productIndex.containsKey(fact.productKey()) ||
                !customerIndex.containsKey(fact.customerKey()) ||
                !dateIndex.containsKey(fact.dateKey()) ||
                !storeIndex.containsKey(fact.storeKey())) {
                throw new ModelException(
                    "Fact contains an orphan foreign key"
                );
            }

            salesIds.add(fact.salesId());
            facts.add(fact);
        }

        void addRelationship(Relationship relationship) {
            if (relationships.stream().anyMatch(
                r -> r.name().equals(relationship.name())
            )) {
                throw new ModelException(
                    "Duplicate relationship name"
                );
            }

            relationships.add(relationship);
        }

        ValidationResult validate() {
            List<String> issues = new ArrayList<>();

            for (Relationship relationship : relationships) {
                if (!relationship.active()) {
                    continue;
                }

                if (relationship.cardinality() ==
                    Cardinality.MANY_TO_MANY) {
                    issues.add(
                        relationship.name() +
                        ": many-to-many relationship detected"
                    );
                }
            }

            for (SalesFact fact : facts) {
                if (!productIndex.containsKey(fact.productKey()) ||
                    !customerIndex.containsKey(fact.customerKey()) ||
                    !dateIndex.containsKey(fact.dateKey()) ||
                    !storeIndex.containsKey(fact.storeKey())) {
                    issues.add(
                        "Referential integrity failure for sales ID " +
                        fact.salesId()
                    );
                }
            }

            return new ValidationResult(
                issues.isEmpty(),
                issues
            );
        }
    }

    static class ModelGovernanceService {

        private final RetailRepository repository;
        private final List<ModelPolicy> policies;

        private ModelState state = ModelState.DRAFT;
        private long version = 0;

        ModelGovernanceService(
            RetailRepository repository,
            List<ModelPolicy> policies
        ) {
            this.repository = repository;
            this.policies = List.copyOf(policies);
        }

        ValidationResult validateAndPublish() {
            List<String> issues = new ArrayList<>();

            ValidationResult base = repository.validate();
            issues.addAll(base.issues());

            for (ModelPolicy policy : policies) {
                ValidationResult result =
                    policy.evaluate(repository);

                issues.addAll(result.issues());
            }

            if (!issues.isEmpty()) {
                state = ModelState.FAILED;

                return new ValidationResult(false, issues);
            }

            state = ModelState.VALIDATED;
            state = ModelState.PUBLISHED;
            version++;

            return new ValidationResult(true, List.of());
        }

        ModelState state() {
            return state;
        }

        long version() {
            return version;
        }
    }

    static class AnalyticsService {

        private final RetailRepository repository;

        AnalyticsService(RetailRepository repository) {
            this.repository = repository;
        }

        BigDecimal totalSales(List<SalesFact> facts) {
            return facts.stream()
                .map(SalesFact::salesAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        ModelMetrics metrics() {
            BigDecimal total = totalSales(repository.facts);

            int quantity = repository.facts.stream()
                .mapToInt(SalesFact::quantity)
                .sum();

            Map<String, BigDecimal> orders =
                repository.facts.stream().collect(
                    Collectors.groupingBy(
                        SalesFact::orderId,
                        Collectors.mapping(
                            SalesFact::salesAmount,
                            Collectors.reducing(
                                BigDecimal.ZERO,
                                BigDecimal::add
                            )
                        )
                    )
                );

            BigDecimal average = orders.isEmpty()
                ? BigDecimal.ZERO
                : total.divide(
                    BigDecimal.valueOf(orders.size()),
                    2,
                    RoundingMode.HALF_UP
                );

            return new ModelMetrics(
                total,
                quantity,
                orders.size(),
                average
            );
        }

        Map<String, BigDecimal> salesByCategory() {
            Map<String, BigDecimal> result =
                new LinkedHashMap<>();

            for (SalesFact fact : repository.facts) {
                Product product =
                    repository.productIndex.get(fact.productKey());

                result.merge(
                    product.category(),
                    fact.salesAmount(),
                    BigDecimal::add
                );
            }

            return result;
        }

        Map<String, BigDecimal> salesByRegion() {
            Map<String, BigDecimal> result =
                new LinkedHashMap<>();

            for (SalesFact fact : repository.facts) {
                Customer customer =
                    repository.customerIndex.get(fact.customerKey());

                result.merge(
                    customer.region(),
                    fact.salesAmount(),
                    BigDecimal::add
                );
            }

            return result;
        }

        List<SalesFact> filterByCategory(String category) {
            Set<Integer> matchingProducts =
                repository.products.stream()
                    .filter(p -> p.category().equals(category))
                    .map(Product::productKey)
                    .collect(Collectors.toSet());

            return repository.facts.stream()
                .filter(f ->
                    matchingProducts.contains(f.productKey())
                )
                .toList();
        }
    }

    static RetailRepository createRepository() {
        RetailRepository repository = new RetailRepository();

        repository.addProduct(new Product(
            101, "Laptop Pro", "Electronics", "Apex"
        ));

        repository.addProduct(new Product(
            102, "Wireless Mouse", "Accessories", "Nova"
        ));

        repository.addProduct(new Product(
            103, "Mechanical Keyboard", "Accessories", "Nova"
        ));

        repository.addProduct(new Product(
            104, "Office Chair", "Furniture", "Comfort"
        ));

        repository.addCustomer(new Customer(
            201, "Aarav Sharma", "North", "Premium"
        ));

        repository.addCustomer(new Customer(
            202, "Meera Singh", "South", "Standard"
        ));

        repository.addCustomer(new Customer(
            203, "Kabir Verma", "West", "Premium"
        ));

        repository.addDate(new CalendarDate(
            20260101, LocalDate.of(2026, 1, 1), 2026, 1, 1
        ));

        repository.addDate(new CalendarDate(
            20260102, LocalDate.of(2026, 1, 2), 2026, 1, 1
        ));

        repository.addDate(new CalendarDate(
            20260201, LocalDate.of(2026, 2, 1), 2026, 2, 1
        ));

        repository.addDate(new CalendarDate(
            20260301, LocalDate.of(2026, 3, 1), 2026, 3, 1
        ));

        repository.addStore(new Store(
            301, "Lucknow Central", "Lucknow"
        ));

        repository.addStore(new Store(
            302, "Delhi Central", "Delhi"
        ));

        repository.addFact(new SalesFact(
            1, "ORD001", 20260101, 101, 201, 301,
            1, new BigDecimal("75000"), new BigDecimal("75000")
        ));

        repository.addFact(new SalesFact(
            2, "ORD001", 20260101, 102, 201, 301,
            2, new BigDecimal("1200"), new BigDecimal("2400")
        ));

        repository.addFact(new SalesFact(
            3, "ORD002", 20260102, 103, 202, 302,
            1, new BigDecimal("3500"), new BigDecimal("3500")
        ));

        repository.addFact(new SalesFact(
            4, "ORD003", 20260201, 104, 203, 301,
            2, new BigDecimal("8500"), new BigDecimal("17000")
        ));

        repository.addFact(new SalesFact(
            5, "ORD004", 20260301, 101, 202, 302,
            1, new BigDecimal("75000"), new BigDecimal("75000")
        ));

        String[] dimensions = {
            "DimDate",
            "DimProduct",
            "DimCustomer",
            "DimStore"
        };

        String[] columns = {
            "date_key",
            "product_key",
            "customer_key",
            "store_key"
        };

        for (int i = 0; i < dimensions.length; i++) {
            repository.addRelationship(new Relationship(
                "FactSales_" + dimensions[i],
                "FactSales",
                columns[i],
                dimensions[i],
                columns[i],
                Cardinality.MANY_TO_ONE,
                FilterDirection.SINGLE,
                true
            ));
        }

        return repository;
    }

    public static void main(String[] args) {

        String correlationId = UUID.randomUUID().toString();

        RetailRepository repository = createRepository();

        ModelGovernanceService governance =
            new ModelGovernanceService(
                repository,
                List.of(new StarSchemaPolicy())
            );

        System.out.println("POWER BI DATA MODEL GOVERNANCE");
        System.out.println("Execution ID: " + correlationId);

        ValidationResult validation =
            governance.validateAndPublish();

        if (!validation.valid()) {
            validation.issues().forEach(
                issue -> System.err.println("ERROR: " + issue)
            );

            throw new ModelException("Model publication rejected");
        }

        System.out.println("\nMODEL PUBLICATION");
        System.out.println("State: " + governance.state());
        System.out.println("Version: " + governance.version());

        AnalyticsService analytics =
            new AnalyticsService(repository);

        ModelMetrics metrics = analytics.metrics();

        System.out.println("\nMODEL METRICS");
        System.out.println("Total sales: " + metrics.totalSales());
        System.out.println("Total quantity: " + metrics.totalQuantity());
        System.out.println("Distinct orders: " + metrics.distinctOrders());
        System.out.println("Average order value: " +
            metrics.averageOrderValue());

        System.out.println("\nSALES BY CATEGORY");

        analytics.salesByCategory().forEach(
            (category, amount) ->
                System.out.println(category + ": " + amount)
        );

        System.out.println("\nSALES BY REGION");

        analytics.salesByRegion().forEach(
            (region, amount) ->
                System.out.println(region + ": " + amount)
        );

        List<SalesFact> filtered =
            analytics.filterByCategory("Accessories");

        System.out.println("\nACCESSORIES FILTER");
        System.out.println("Matching fact rows: " + filtered.size());
        System.out.println(
            "Filtered sales: " + analytics.totalSales(filtered)
        );

        System.out.println("\nFAILURE VALIDATION");

        try {
            repository.addFact(new SalesFact(
                99, "INVALID", 20260101, 999, 201, 301,
                1, new BigDecimal("100"), new BigDecimal("100")
            ));
        } catch (ModelException error) {
            System.out.println(
                "Orphan fact rejected: " + error.getMessage()
            );
        }

        try {
            repository.addProduct(new Product(
                101, "Duplicate", "Electronics", "Apex"
            ));
        } catch (ModelException error) {
            System.out.println(
                "Duplicate dimension key rejected: " +
                error.getMessage()
            );
        }

        System.out.println("\nMODEL EXECUTION COMPLETE");
    }
}
