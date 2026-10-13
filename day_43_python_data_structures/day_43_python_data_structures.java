import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.stream.Collectors;

// Enterprise repository inventory and release-readiness model.
// Compile and run:
//   javac DataStructuresEnterprise.java
//   java DataStructuresEnterprise

public class DataStructuresEnterprise {

    enum Environment {
        DEVELOPMENT,
        STAGING,
        PRODUCTION
    }

    enum CheckStatus {
        PASSED,
        FAILED,
        PENDING
    }

    enum ReleaseStatus {
        APPROVED,
        BLOCKED
    }

    record CheckResult(
        String name,
        CheckStatus status,
        int durationMillis
    ) {
        CheckResult {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Check name is required.");
            }
            Objects.requireNonNull(status, "Check status is required.");

            if (durationMillis < 0) {
                throw new IllegalArgumentException(
                    "Duration cannot be negative."
                );
            }
        }
    }

    record ReleaseKey(String repository, Environment environment) {
        ReleaseKey {
            if (repository == null || repository.isBlank()) {
                throw new IllegalArgumentException("Repository is required.");
            }
            Objects.requireNonNull(environment, "Environment is required.");
        }
    }

    static final class Repository {
        private final String name;
        private final String language;
        private final int stars;
        private final Set<String> topics;
        private final List<String> maintainers;
        private final boolean archived;
        private final Map<String, String> metadata;

        Repository(
            String name,
            String language,
            int stars,
            Set<String> topics,
            List<String> maintainers,
            boolean archived,
            Map<String, String> metadata
        ) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Repository name is required."
                );
            }
            if (language == null || language.isBlank()) {
                throw new IllegalArgumentException("Language is required.");
            }
            if (stars < 0) {
                throw new IllegalArgumentException("Stars cannot be negative.");
            }

            Objects.requireNonNull(topics, "Topics are required.");
            Objects.requireNonNull(maintainers, "Maintainers are required.");
            Objects.requireNonNull(metadata, "Metadata is required.");

            if (topics.stream().anyMatch(
                topic -> topic == null || topic.isBlank()
            )) {
                throw new IllegalArgumentException("Invalid topic.");
            }

            if (maintainers.stream().anyMatch(
                person -> person == null || person.isBlank()
            )) {
                throw new IllegalArgumentException("Invalid maintainer.");
            }

            if (!archived && maintainers.isEmpty()) {
                throw new IllegalArgumentException(
                    "Active repositories require a maintainer."
                );
            }

            this.name = name;
            this.language = language.toLowerCase();
            this.stars = stars;
            this.topics = Collections.unmodifiableSet(
                new TreeSet<>(topics)
            );
            this.maintainers = List.copyOf(maintainers);
            this.archived = archived;
            this.metadata = Map.copyOf(metadata);
        }

        String name() {
            return name;
        }

        String language() {
            return language;
        }

        int stars() {
            return stars;
        }

        Set<String> topics() {
            return topics;
        }

        List<String> maintainers() {
            return maintainers;
        }

        boolean archived() {
            return archived;
        }

        Map<String, String> metadata() {
            return metadata;
        }

        @Override
        public String toString() {
            return name + " [" + language + ", stars=" + stars
                + ", archived=" + archived + ", topics=" + topics + "]";
        }
    }

    static final class Release {
        private final String releaseId;
        private final ReleaseKey key;
        private final Map<String, CheckResult> checks;
        private final Set<String> requiredChecks;

        Release(
            String releaseId,
            ReleaseKey key,
            List<CheckResult> checkResults,
            Set<String> requiredChecks
        ) {
            if (releaseId == null || releaseId.isBlank()) {
                throw new IllegalArgumentException("Release ID is required.");
            }

            this.releaseId = releaseId;
            this.key = Objects.requireNonNull(key, "Release key is required.");
            this.requiredChecks = Set.copyOf(requiredChecks);

            Map<String, CheckResult> indexedChecks = new LinkedHashMap<>();

            for (CheckResult check : checkResults) {
                if (indexedChecks.putIfAbsent(check.name(), check) != null) {
                    throw new IllegalArgumentException(
                        "Duplicate check: " + check.name()
                    );
                }
            }

            this.checks = Collections.unmodifiableMap(indexedChecks);
        }

        String releaseId() {
            return releaseId;
        }

        ReleaseKey key() {
            return key;
        }

        Map<String, CheckResult> checks() {
            return checks;
        }

        Set<String> requiredChecks() {
            return requiredChecks;
        }
    }

    record ReleaseDecision(
        ReleaseStatus status,
        List<String> blockers,
        int totalDurationMillis
    ) {
        ReleaseDecision {
            Objects.requireNonNull(status);
            blockers = List.copyOf(blockers);
        }
    }

    static final class RepositoryRegistry {
        private final Map<String, Repository> repositories =
            new LinkedHashMap<>();

        private final Map<String, Set<String>> topicIndex =
            new HashMap<>();

        private final Map<String, Set<String>> maintainerIndex =
            new TreeMap<>();

        void register(Repository repository) {
            Objects.requireNonNull(repository);

            if (repositories.containsKey(repository.name())) {
                throw new IllegalArgumentException(
                    "Repository already registered: " + repository.name()
                );
            }

            repositories.put(repository.name(), repository);

            for (String topic : repository.topics()) {
                topicIndex.computeIfAbsent(
                    topic, ignored -> new TreeSet<>()
                ).add(repository.name());
            }

            for (String maintainer : repository.maintainers()) {
                maintainerIndex.computeIfAbsent(
                    maintainer, ignored -> new TreeSet<>()
                ).add(repository.name());
            }
        }

        Repository find(String name) {
            Repository repository = repositories.get(name);

            if (repository == null) {
                throw new IllegalArgumentException(
                    "Unknown repository: " + name
                );
            }

            return repository;
        }

        List<Repository> all() {
            return List.copyOf(repositories.values());
        }

        Set<String> findByTopic(String topic) {
            return Set.copyOf(topicIndex.getOrDefault(topic, Set.of()));
        }

        Set<String> findByMaintainer(String maintainer) {
            return Set.copyOf(
                maintainerIndex.getOrDefault(maintainer, Set.of())
            );
        }

        Map<String, Long> activeLanguageCounts() {
            return repositories.values().stream()
                .filter(repository -> !repository.archived())
                .collect(Collectors.groupingBy(
                    Repository::language,
                    TreeMap::new,
                    Collectors.counting()
                ));
        }
    }

    static final class ReleasePolicy {
        private final Set<Environment> allowedEnvironments;
        private final Set<String> mandatoryChecks;
        private final int maximumCheckDurationMillis;

        ReleasePolicy(
            Set<Environment> allowedEnvironments,
            Set<String> mandatoryChecks,
            int maximumCheckDurationMillis
        ) {
            this.allowedEnvironments = Set.copyOf(allowedEnvironments);
            this.mandatoryChecks = Set.copyOf(mandatoryChecks);

            if (maximumCheckDurationMillis < 0) {
                throw new IllegalArgumentException(
                    "Maximum duration cannot be negative."
                );
            }

            this.maximumCheckDurationMillis = maximumCheckDurationMillis;
        }

        ReleaseDecision evaluate(
            Repository repository,
            Release release
        ) {
            List<String> blockers = new ArrayList<>();
            int totalDuration = 0;

            if (repository.archived()) {
                blockers.add("Archived repositories cannot be released.");
            }

            if (!allowedEnvironments.contains(
                release.key().environment()
            )) {
                blockers.add("Environment is not allowed by policy.");
            }

            Set<String> required = new HashSet<>(mandatoryChecks);
            required.addAll(release.requiredChecks());

            for (String requiredCheck : required) {
                CheckResult check = release.checks().get(requiredCheck);

                if (check == null) {
                    blockers.add("Missing check: " + requiredCheck);
                } else if (check.status() == CheckStatus.FAILED) {
                    blockers.add("Failed check: " + requiredCheck);
                } else if (check.status() == CheckStatus.PENDING) {
                    blockers.add("Pending check: " + requiredCheck);
                }
            }

            for (CheckResult check : release.checks().values()) {
                totalDuration = Math.addExact(
                    totalDuration, check.durationMillis()
                );

                if (check.durationMillis() > maximumCheckDurationMillis) {
                    blockers.add(
                        "Check exceeds duration limit: " + check.name()
                    );
                }
            }

            ReleaseStatus status = blockers.isEmpty()
                ? ReleaseStatus.APPROVED
                : ReleaseStatus.BLOCKED;

            return new ReleaseDecision(status, blockers, totalDuration);
        }
    }

    public static void main(String[] args) {
        RepositoryRegistry registry = new RepositoryRegistry();

        registry.register(new Repository(
            "market-prism",
            "Python",
            320,
            Set.of("finance", "analytics", "api"),
            List.of("Anika", "Rahul"),
            false,
            Map.of("tier", "production", "ownerTeam", "Risk")
        ));

        registry.register(new Repository(
            "portfolio-ui",
            "JavaScript",
            210,
            Set.of("dashboard", "analytics"),
            List.of("Meera"),
            false,
            Map.of("tier", "production", "ownerTeam", "Platform")
        ));

        registry.register(new Repository(
            "security-audit",
            "Python",
            145,
            Set.of("security", "automation"),
            List.of("Rahul", "Dev"),
            false,
            Map.of("tier", "internal", "ownerTeam", "Security")
        ));

        registry.register(new Repository(
            "legacy-reports",
            "Java",
            34,
            Set.of("reporting", "legacy"),
            List.of("Dev"),
            true,
            Map.of("tier", "archived", "ownerTeam", "Operations")
        ));

        System.out.println("Repository registry");
        registry.all().forEach(System.out::println);

        System.out.println("\nLanguage counts");
        registry.activeLanguageCounts().forEach(
            (language, count) ->
                System.out.println(language + ": " + count)
        );

        System.out.println("\nRepositories tagged analytics");
        System.out.println(registry.findByTopic("analytics"));

        System.out.println("\nRepositories maintained by Rahul");
        System.out.println(registry.findByMaintainer("Rahul"));

        ReleasePolicy policy = new ReleasePolicy(
            EnumSet.of(Environment.STAGING, Environment.PRODUCTION),
            Set.of("unit-tests", "security-scan"),
            2000
        );

        Set<String> releaseChecks = Set.of(
            "unit-tests",
            "security-scan",
            "integration-tests"
        );

        Release productionRelease = new Release(
            "REL-801",
            new ReleaseKey("market-prism", Environment.PRODUCTION),
            List.of(
                new CheckResult("unit-tests", CheckStatus.PASSED, 400),
                new CheckResult("security-scan", CheckStatus.PASSED, 800),
                new CheckResult(
                    "integration-tests", CheckStatus.PASSED, 1300
                )
            ),
            releaseChecks
        );

        Release failedRelease = new Release(
            "REL-802",
            new ReleaseKey("security-audit", Environment.PRODUCTION),
            List.of(
                new CheckResult("unit-tests", CheckStatus.PASSED, 350),
                new CheckResult("security-scan", CheckStatus.FAILED, 900)
            ),
            releaseChecks
        );

        Release archivedRelease = new Release(
            "REL-803",
            new ReleaseKey("legacy-reports", Environment.PRODUCTION),
            List.of(
                new CheckResult("unit-tests", CheckStatus.PASSED, 200),
                new CheckResult("security-scan", CheckStatus.PASSED, 400)
            ),
            releaseChecks
        );

        evaluateAndPrint(registry, policy, productionRelease);
        evaluateAndPrint(registry, policy, failedRelease);
        evaluateAndPrint(registry, policy, archivedRelease);

        try {
            registry.register(new Repository(
                "market-prism",
                "Python",
                1,
                Set.of("duplicate"),
                List.of("Anika"),
                false,
                Map.of()
            ));
        } catch (IllegalArgumentException error) {
            System.out.println("\nDuplicate rejected: " + error.getMessage());
        }

        try {
            registry.find("unknown-repository");
        } catch (IllegalArgumentException error) {
            System.out.println("Lookup rejected: " + error.getMessage());
        }
    }

    private static void evaluateAndPrint(
        RepositoryRegistry registry,
        ReleasePolicy policy,
        Release release
    ) {
        Repository repository = registry.find(
            release.key().repository()
        );

        ReleaseDecision decision = policy.evaluate(repository, release);

        System.out.println("\nRelease " + release.releaseId());
        System.out.println("Status: " + decision.status());
        System.out.println(
            "Duration: " + decision.totalDurationMillis() + " ms"
        );

        if (decision.blockers().isEmpty()) {
            System.out.println("All release policies satisfied.");
        } else {
            decision.blockers().forEach(
                blocker -> System.out.println("Blocked: " + blocker)
            );
        }
    }
}
