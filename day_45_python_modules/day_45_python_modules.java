import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/*
 * Enterprise Python Environment Governance Model
 *
 * The application represents a platform team that validates Python
 * applications before deployment. It models runtime requirements, dependency
 * constraints, environment state, validation policies, and failure states.
 *
 * Java 17 is used so records, sealed-style domain modeling through enums,
 * immutable views, generics, and service-oriented classes can represent the
 * governance rules explicitly.
 */

public class DependencyGovernanceApp {

    enum ConstraintOperator {
        MINIMUM,
        EXACT,
        MAXIMUM_EXCLUSIVE
    }

    enum EnvironmentStatus {
        NEW,
        VALID,
        INVALID
    }

    enum Severity {
        INFO,
        WARNING,
        ERROR
    }

    record Version(int major, int minor, int patch)
            implements Comparable<Version> {

        public Version {
            if (major < 0 || minor < 0 || patch < 0) {
                throw new IllegalArgumentException(
                        "Version components cannot be negative."
                );
            }
        }

        public static Version parse(String value) {
            Objects.requireNonNull(value, "Version is required.");

            String[] parts = value.split("\\.");

            if (parts.length < 2 || parts.length > 3) {
                throw new IllegalArgumentException(
                        "Version must contain two or three numeric components."
                );
            }

            try {
                int major = Integer.parseInt(parts[0]);
                int minor = Integer.parseInt(parts[1]);
                int patch = parts.length == 3
                        ? Integer.parseInt(parts[2])
                        : 0;

                return new Version(major, minor, patch);
            } catch (NumberFormatException exception) {
                throw new IllegalArgumentException(
                        "Invalid numeric version: " + value,
                        exception
                );
            }
        }

        @Override
        public int compareTo(Version other) {
            int majorResult = Integer.compare(major, other.major);

            if (majorResult != 0) {
                return majorResult;
            }

            int minorResult = Integer.compare(minor, other.minor);

            if (minorResult != 0) {
                return minorResult;
            }

            return Integer.compare(patch, other.patch);
        }

        @Override
        public String toString() {
            return major + "." + minor + "." + patch;
        }
    }

    record DependencyConstraint(
            String packageName,
            ConstraintOperator operator,
            Version version,
            String policySource
    ) {
        public DependencyConstraint {
            Objects.requireNonNull(packageName);
            Objects.requireNonNull(operator);
            Objects.requireNonNull(version);
            Objects.requireNonNull(policySource);
        }

        public boolean accepts(Version candidate) {
            return switch (operator) {
                case MINIMUM -> candidate.compareTo(version) >= 0;
                case EXACT -> candidate.compareTo(version) == 0;
                case MAXIMUM_EXCLUSIVE -> candidate.compareTo(version) < 0;
            };
        }
    }

    record DependencyDeclaration(
            String packageName,
            List<DependencyConstraint> constraints
    ) {
        public DependencyDeclaration {
            Objects.requireNonNull(packageName);
            Objects.requireNonNull(constraints);

            constraints = List.copyOf(constraints);

            if (constraints.isEmpty()) {
                throw new IllegalArgumentException(
                        "At least one dependency constraint is required."
                );
            }
        }

        public boolean accepts(Version version) {
            return constraints.stream()
                    .allMatch(constraint -> constraint.accepts(version));
        }
    }

    record RuntimeRequirement(
            String runtimeName,
            Version minimumVersion
    ) {
        public boolean accepts(Version actualVersion) {
            return actualVersion.compareTo(minimumVersion) >= 0;
        }
    }

    record InstalledPackage(
            String packageName,
            Version version
    ) {}

    record ValidationFinding(
            Severity severity,
            String subject,
            String message
    ) {}

    static final class PythonEnvironment {

        private final RuntimeRequirement runtimeRequirement;
        private final Version actualRuntime;
        private final Map<String, InstalledPackage> packages;
        private EnvironmentStatus status = EnvironmentStatus.NEW;

        PythonEnvironment(
                RuntimeRequirement runtimeRequirement,
                Version actualRuntime
        ) {
            this.runtimeRequirement = Objects.requireNonNull(runtimeRequirement);
            this.actualRuntime = Objects.requireNonNull(actualRuntime);
            this.packages = new LinkedHashMap<>();
        }

        void install(String packageName, Version version) {
            if (packageName == null || packageName.isBlank()) {
                throw new IllegalArgumentException(
                        "Package name cannot be empty."
                );
            }

            packages.put(
                    packageName,
                    new InstalledPackage(packageName, version)
            );

            status = EnvironmentStatus.NEW;
        }

        Optional<InstalledPackage> find(String packageName) {
            return Optional.ofNullable(packages.get(packageName));
        }

        List<ValidationFinding> validate(
                List<DependencyDeclaration> declarations
        ) {
            List<ValidationFinding> findings = new ArrayList<>();

            if (!runtimeRequirement.accepts(actualRuntime)) {
                findings.add(
                        new ValidationFinding(
                                Severity.ERROR,
                                "Python runtime",
                                "Runtime " + actualRuntime
                                        + " does not satisfy minimum "
                                        + runtimeRequirement.minimumVersion()
                        )
                );
            } else {
                findings.add(
                        new ValidationFinding(
                                Severity.INFO,
                                "Python runtime",
                                "Runtime satisfies the declared requirement."
                        )
                );
            }

            for (DependencyDeclaration declaration : declarations) {
                InstalledPackage installed =
                        packages.get(declaration.packageName());

                if (installed == null) {
                    findings.add(
                            new ValidationFinding(
                                    Severity.ERROR,
                                    declaration.packageName(),
                                    "Required package is not installed."
                            )
                    );
                    continue;
                }

                if (!declaration.accepts(installed.version())) {
                    findings.add(
                            new ValidationFinding(
                                    Severity.ERROR,
                                    declaration.packageName(),
                                    "Installed version "
                                            + installed.version()
                                            + " violates dependency policy."
                            )
                    );
                } else {
                    findings.add(
                            new ValidationFinding(
                                    Severity.INFO,
                                    declaration.packageName(),
                                    "Installed version "
                                            + installed.version()
                                            + " satisfies policy."
                            )
                    );
                }
            }

            boolean hasErrors = findings.stream()
                    .anyMatch(finding -> finding.severity() == Severity.ERROR);

            status = hasErrors
                    ? EnvironmentStatus.INVALID
                    : EnvironmentStatus.VALID;

            return List.copyOf(findings);
        }

        EnvironmentStatus status() {
            return status;
        }

        void printInventory() {
            System.out.println("Python runtime: " + actualRuntime);

            packages.values().forEach(packageInfo ->
                    System.out.println(
                            "  " + packageInfo.packageName()
                                    + " " + packageInfo.version()
                    )
            );
        }
    }

    interface EnvironmentPolicy {
        List<ValidationFinding> evaluate(PythonEnvironment environment);
    }

    static final class ProductionDependencyPolicy
            implements EnvironmentPolicy {

        private final List<DependencyDeclaration> declarations;

        ProductionDependencyPolicy(
                List<DependencyDeclaration> declarations
        ) {
            this.declarations = List.copyOf(declarations);
        }

        @Override
        public List<ValidationFinding> evaluate(
                PythonEnvironment environment
        ) {
            return environment.validate(declarations);
        }
    }

    static final class EnvironmentReport {

        private final List<ValidationFinding> findings;

        EnvironmentReport(List<ValidationFinding> findings) {
            this.findings = List.copyOf(findings);
        }

        boolean deployable() {
            return findings.stream()
                    .noneMatch(
                            finding -> finding.severity() == Severity.ERROR
                    );
        }

        void print() {
            findings.forEach(finding ->
                    System.out.println(
                            "[" + finding.severity() + "] "
                                    + finding.subject()
                                    + ": "
                                    + finding.message()
                    )
            );

            System.out.println("Deployable: " + deployable());
        }
    }

    private static DependencyDeclaration dependency(
            String packageName,
            String minimum,
            String maximumExclusive
    ) {
        return new DependencyDeclaration(
                packageName,
                List.of(
                        new DependencyConstraint(
                                packageName,
                                ConstraintOperator.MINIMUM,
                                Version.parse(minimum),
                                "production policy"
                        ),
                        new DependencyConstraint(
                                packageName,
                                ConstraintOperator.MAXIMUM_EXCLUSIVE,
                                Version.parse(maximumExclusive),
                                "production policy"
                        )
                )
        );
    }

    private static void runHealthyEnvironment(
            List<DependencyDeclaration> declarations
    ) {
        System.out.println("\n=== Healthy Environment ===");

        PythonEnvironment environment =
                new PythonEnvironment(
                        new RuntimeRequirement(
                                "Python",
                                Version.parse("3.11.0")
                        ),
                        Version.parse("3.13.0")
                );

        environment.install("httpx", Version.parse("0.28.1"));
        environment.install("pydantic", Version.parse("2.9.2"));

        environment.printInventory();

        EnvironmentPolicy policy =
                new ProductionDependencyPolicy(declarations);

        EnvironmentReport report =
                new EnvironmentReport(policy.evaluate(environment));

        report.print();

        if (environment.status() != EnvironmentStatus.VALID) {
            throw new IllegalStateException(
                    "Healthy environment unexpectedly failed validation."
            );
        }
    }

    private static void runInvalidEnvironment(
            List<DependencyDeclaration> declarations
    ) {
        System.out.println("\n=== Invalid Environment ===");

        PythonEnvironment environment =
                new PythonEnvironment(
                        new RuntimeRequirement(
                                "Python",
                                Version.parse("3.11.0")
                        ),
                        Version.parse("3.10.14")
                );

        // The package is present, but its version violates the minimum
        // requirement. Runtime and dependency failures are independent policy
        // dimensions and should therefore be reported separately.
        environment.install("httpx", Version.parse("0.26.0"));
        environment.install("pydantic", Version.parse("2.9.2"));

        environment.printInventory();

        EnvironmentPolicy policy =
                new ProductionDependencyPolicy(declarations);

        EnvironmentReport report =
                new EnvironmentReport(policy.evaluate(environment));

        report.print();

        if (environment.status() != EnvironmentStatus.INVALID) {
            throw new IllegalStateException(
                    "Invalid environment unexpectedly passed validation."
            );
        }
    }

    private static void demonstratePolicyComposition() {
        System.out.println("\n=== Policy Composition ===");

        EnumSet<Severity> blockingSeverities =
                EnumSet.of(Severity.ERROR);

        System.out.println(
                "Blocking severities: " + blockingSeverities
        );

        System.out.println(
                "Warnings can be recorded without making deployment "
                        + "automatically impossible, while ERROR findings "
                        + "represent policy violations."
        );
    }

    public static void main(String[] args) {
        List<DependencyDeclaration> declarations = List.of(
                dependency("httpx", "0.27.0", "1.0.0"),
                dependency("pydantic", "2.0.0", "3.0.0")
        );

        System.out.println(
                "=== Enterprise Python Environment Governance ==="
        );

        runHealthyEnvironment(declarations);
        runInvalidEnvironment(declarations);
        demonstratePolicyComposition();

        System.out.println("\n=== Complete ===");
        System.out.println(
                "The model separates runtime policy, dependency declarations, "
                        + "installed state, validation findings, and deployment "
                        + "eligibility."
        );
    }
}
