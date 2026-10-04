import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Advanced SQL CTEs: enterprise repository-governance case study.
 *
 * The Java program models the relational domain that an enterprise service
 * could persist in PostgreSQL. The implementation uses explicit domain types
 * and service abstractions rather than translating a SQL statement line by
 * line.
 *
 * The SQL concepts demonstrated by the corresponding repository are:
 * - ordinary CTEs for statement-scoped named relations
 * - chained and nested CTEs for multi-stage query logic
 * - recursive CTEs for hierarchy traversal
 * - CTEs combined with window functions
 * - policy evaluation after independent relational facts are prepared
 *
 * Pull Requests, Code Review, Approvals, and Branch Protection remain
 * separate domain responsibilities.
 */

public class AdvancedSqlCteEnterpriseCaseStudy {

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    enum ReviewState {
        COMMENTED,
        APPROVED,
        CHANGES_REQUESTED,
        DISMISSED
    }

    enum CheckStatus {
        PENDING,
        PASSED,
        FAILED,
        CANCELLED
    }

    record PullRequest(
        long id,
        String title,
        String sourceBranch,
        String targetBranch,
        String author,
        PullRequestState state
    ) {
        PullRequest {
            if (id <= 0) {
                throw new IllegalArgumentException("Pull Request ID must be positive.");
            }
            Objects.requireNonNull(title);
            Objects.requireNonNull(sourceBranch);
            Objects.requireNonNull(targetBranch);
            Objects.requireNonNull(author);
            Objects.requireNonNull(state);

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ."
                );
            }
        }
    }

    record Review(
        long id,
        long pullRequestId,
        String reviewer,
        ReviewState state,
        Instant submittedAt
    ) {
        Review {
            if (id <= 0 || pullRequestId <= 0) {
                throw new IllegalArgumentException("Review identifiers must be positive.");
            }
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(state);
            Objects.requireNonNull(submittedAt);
        }
    }

    record ReviewComment(
        long id,
        long pullRequestId,
        String reviewer,
        String filePath,
        int line,
        boolean resolved
    ) {
        ReviewComment {
            if (line <= 0) {
                throw new IllegalArgumentException(
                    "Review comment line must be positive."
                );
            }
            Objects.requireNonNull(filePath);
            Objects.requireNonNull(reviewer);
        }
    }

    record StatusCheck(
        long pullRequestId,
        String name,
        CheckStatus status
    ) {
        StatusCheck {
            Objects.requireNonNull(name);
            Objects.requireNonNull(status);
        }
    }

    record BranchProtectionPolicy(
        String branch,
        int requiredApprovals,
        boolean requireStatusChecks,
        boolean restrictDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean requireConversationResolution,
        boolean requireLinearHistory
    ) {
        BranchProtectionPolicy {
            Objects.requireNonNull(branch);

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approval count cannot be negative."
                );
            }
        }
    }

    record MergeEligibility(
        long pullRequestId,
        boolean eligible,
        List<String> reasons
    ) {
        MergeEligibility {
            reasons = List.copyOf(reasons);
        }
    }

    /*
     * This value object corresponds to an intermediate CTE result. Keeping
     * intermediate query-like facts explicit mirrors how chained CTEs make
     * complex SQL easier to reason about.
     */
    record ReviewSummary(
        long pullRequestId,
        long reviewCount,
        long approvalCount,
        long changeRequestCount
    ) {}

    record CheckSummary(
        long pullRequestId,
        long passed,
        long failed,
        long pending,
        long cancelled
    ) {}

    static final class RepositoryRepository {
        private final Map<Long, PullRequest> pullRequests = new LinkedHashMap<>();
        private final List<Review> reviews = new ArrayList<>();
        private final List<ReviewComment> comments = new ArrayList<>();
        private final List<StatusCheck> checks = new ArrayList<>();
        private final Map<String, BranchProtectionPolicy> policies =
            new HashMap<>();

        void addPullRequest(PullRequest pullRequest) {
            if (pullRequests.putIfAbsent(
                pullRequest.id(),
                pullRequest
            ) != null) {
                throw new IllegalStateException(
                    "Duplicate Pull Request ID: " + pullRequest.id()
                );
            }
        }

        void addReview(Review review) {
            requirePullRequest(review.pullRequestId());
            reviews.add(review);
        }

        void addComment(ReviewComment comment) {
            requirePullRequest(comment.pullRequestId());
            comments.add(comment);
        }

        void addCheck(StatusCheck check) {
            requirePullRequest(check.pullRequestId());
            checks.add(check);
        }

        void setPolicy(BranchProtectionPolicy policy) {
            policies.put(policy.branch(), policy);
        }

        Optional<PullRequest> findPullRequest(long id) {
            return Optional.ofNullable(pullRequests.get(id));
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        List<ReviewComment> comments() {
            return List.copyOf(comments);
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks);
        }

        Optional<BranchProtectionPolicy> policyFor(String branch) {
            return Optional.ofNullable(policies.get(branch));
        }

        private void requirePullRequest(long id) {
            if (!pullRequests.containsKey(id)) {
                throw new IllegalArgumentException(
                    "Unknown Pull Request: " + id
                );
            }
        }
    }

    static final class QueryLogicService {
        private final RepositoryRepository repository;

        QueryLogicService(RepositoryRepository repository) {
            this.repository = repository;
        }

        /*
         * This method represents the semantic role of a CTE:
         * calculate a named intermediate relation first, then allow another
         * operation to consume it.
         */
        List<ReviewSummary> buildReviewSummaries() {
            Map<Long, List<Review>> grouped = repository.reviews()
                .stream()
                .collect(Collectors.groupingBy(Review::pullRequestId));

            return grouped.entrySet()
                .stream()
                .map(entry -> {
                    List<Review> prReviews = entry.getValue();

                    long approvals = prReviews.stream()
                        .filter(review -> review.state() == ReviewState.APPROVED)
                        .count();

                    long changeRequests = prReviews.stream()
                        .filter(
                            review ->
                                review.state()
                                    == ReviewState.CHANGES_REQUESTED
                        )
                        .count();

                    return new ReviewSummary(
                        entry.getKey(),
                        prReviews.size(),
                        approvals,
                        changeRequests
                    );
                })
                .sorted(Comparator.comparingLong(ReviewSummary::pullRequestId))
                .toList();
        }

        /*
         * This is equivalent to a separate check_summary CTE. Keeping the
         * aggregation independent prevents review and CI facts from becoming
         * accidentally coupled.
         */
        List<CheckSummary> buildCheckSummaries() {
            Map<Long, List<StatusCheck>> grouped = repository.checks()
                .stream()
                .collect(Collectors.groupingBy(StatusCheck::pullRequestId));

            return grouped.entrySet()
                .stream()
                .map(entry -> {
                    List<StatusCheck> checks = entry.getValue();

                    return new CheckSummary(
                        entry.getKey(),
                        checks.stream()
                            .filter(c -> c.status() == CheckStatus.PASSED)
                            .count(),
                        checks.stream()
                            .filter(c -> c.status() == CheckStatus.FAILED)
                            .count(),
                        checks.stream()
                            .filter(c -> c.status() == CheckStatus.PENDING)
                            .count(),
                        checks.stream()
                            .filter(c -> c.status() == CheckStatus.CANCELLED)
                            .count()
                    );
                })
                .sorted(Comparator.comparingLong(CheckSummary::pullRequestId))
                .toList();
        }

        /*
         * The latest decision per reviewer is analogous to a SQL window
         * function:
         *
         * ROW_NUMBER() OVER (
         *   PARTITION BY pull_request_id, reviewer
         *   ORDER BY submitted_at DESC
         * )
         *
         * The Java comparator expresses the same ordering rule.
         */
        Map<Long, Map<String, Review>> latestReviewerDecisions() {
            Map<Long, Map<String, Review>> latest = new HashMap<>();

            for (Review review : repository.reviews()) {
                Map<String, Review> byReviewer = latest.computeIfAbsent(
                    review.pullRequestId(),
                    ignored -> new HashMap<>()
                );

                Review existing = byReviewer.get(review.reviewer());

                if (
                    existing == null ||
                    review.submittedAt().isAfter(existing.submittedAt())
                ) {
                    byReviewer.put(review.reviewer(), review);
                }
            }

            return latest;
        }

        long activeApprovalCount(long pullRequestId) {
            return latestReviewerDecisions()
                .getOrDefault(pullRequestId, Map.of())
                .values()
                .stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .map(Review::reviewer)
                .distinct()
                .count();
        }

        long unresolvedCommentCount(long pullRequestId) {
            return repository.comments()
                .stream()
                .filter(comment -> comment.pullRequestId() == pullRequestId)
                .filter(comment -> !comment.resolved())
                .count();
        }

        boolean allRequiredChecksPassed(long pullRequestId) {
            List<StatusCheck> prChecks = repository.checks()
                .stream()
                .filter(check -> check.pullRequestId() == pullRequestId)
                .toList();

            if (prChecks.isEmpty()) {
                return false;
            }

            return prChecks.stream()
                .allMatch(check -> check.status() == CheckStatus.PASSED);
        }

        MergeEligibility evaluateMergeEligibility(long pullRequestId) {
            PullRequest pr = repository.findPullRequest(pullRequestId)
                .orElseThrow(
                    () -> new IllegalArgumentException(
                        "Unknown Pull Request: " + pullRequestId
                    )
                );

            List<String> reasons = new ArrayList<>();
            boolean eligible = true;

            if (pr.state() != PullRequestState.OPEN) {
                eligible = false;
                reasons.add("Pull Request is not open.");
            }

            BranchProtectionPolicy policy = repository.policyFor(
                pr.targetBranch()
            ).orElseThrow(
                () -> new IllegalStateException(
                    "No branch-protection policy exists for "
                        + pr.targetBranch()
                )
            );

            long approvals = activeApprovalCount(pullRequestId);

            if (approvals < policy.requiredApprovals()) {
                eligible = false;
                reasons.add(
                    "Approval requirement not met: "
                        + approvals
                        + "/"
                        + policy.requiredApprovals()
                        + " active approvals."
                );
            }

            if (
                policy.requireStatusChecks()
                    && !allRequiredChecksPassed(pullRequestId)
            ) {
                eligible = false;
                reasons.add("Required status checks are not all passed.");
            }

            if (
                policy.requireConversationResolution()
                    && unresolvedCommentCount(pullRequestId) > 0
            ) {
                eligible = false;
                reasons.add("Review conversations remain unresolved.");
            }

            if (eligible) {
                reasons.add(
                    "All modeled branch-protection merge conditions pass."
                );
            }

            return new MergeEligibility(
                pullRequestId,
                eligible,
                reasons
            );
        }
    }

    /*
     * Recursive traversal represents the algorithmic meaning of a recursive
     * CTE. The queue is explicit and the visited set prevents infinite
     * traversal when branch data contains cycles.
     */
    static final class BranchHierarchyService {
        private final Map<String, Set<String>> children = new HashMap<>();

        void addRelationship(String parent, String child) {
            if (parent.equals(child)) {
                throw new IllegalArgumentException(
                    "A branch cannot be its own child."
                );
            }

            children
                .computeIfAbsent(parent, ignored -> new LinkedHashSet<>())
                .add(child);
        }

        record Node(String branch, int depth) {}

        List<Node> traverse(String root) {
            List<Node> result = new ArrayList<>();
            Set<String> visited = new HashSet<>();
            Deque<Node> queue = new ArrayDeque<>();

            queue.add(new Node(root, 0));

            while (!queue.isEmpty()) {
                Node current = queue.removeFirst();

                if (!visited.add(current.branch())) {
                    continue;
                }

                result.add(current);

                for (String child : children.getOrDefault(
                    current.branch(),
                    Set.of()
                )) {
                    queue.addLast(
                        new Node(child, current.depth() + 1)
                    );
                }
            }

            return result;
        }
    }

    /*
     * This small service models Pull Request lifecycle transitions rather than
     * review policy. The distinction matters: changing a PR from open to closed
     * is a workflow transition, while determining whether an open PR can merge
     * is a policy evaluation.
     */
    static final class PullRequestLifecycleService {
        private static final Map<PullRequestState, Set<PullRequestState>>
            ALLOWED = Map.of(
                PullRequestState.DRAFT,
                Set.of(PullRequestState.OPEN, PullRequestState.CLOSED),
                PullRequestState.OPEN,
                Set.of(
                    PullRequestState.CLOSED,
                    PullRequestState.MERGED
                ),
                PullRequestState.CLOSED,
                Set.of(PullRequestState.OPEN),
                PullRequestState.MERGED,
                Set.of()
            );

        PullRequestState transition(
            PullRequestState current,
            PullRequestState next
        ) {
            if (!ALLOWED.getOrDefault(current, Set.of()).contains(next)) {
                throw new IllegalStateException(
                    "Invalid lifecycle transition: "
                        + current
                        + " -> "
                        + next
                );
            }

            return next;
        }
    }

    static RepositoryRepository createCaseStudyRepository() {
        RepositoryRepository repository = new RepositoryRepository();

        repository.addPullRequest(
            new PullRequest(
                101,
                "Increase payment timeout safely",
                "feature/payment-timeout",
                "main",
                "atul",
                PullRequestState.OPEN
            )
        );

        repository.addPullRequest(
            new PullRequest(
                102,
                "Add fraud risk rules",
                "feature/risk-rules",
                "main",
                "maya",
                PullRequestState.OPEN
            )
        );

        repository.addPullRequest(
            new PullRequest(
                103,
                "Emergency authentication fix",
                "hotfix/auth",
                "release/2026.10",
                "liam",
                PullRequestState.OPEN
            )
        );

        repository.addReview(
            new Review(
                2001,
                101,
                "maya",
                ReviewState.APPROVED,
                Instant.parse("2026-10-03T10:00:00Z")
            )
        );

        repository.addReview(
            new Review(
                2002,
                101,
                "liam",
                ReviewState.COMMENTED,
                Instant.parse("2026-10-03T11:00:00Z")
            )
        );

        repository.addReview(
            new Review(
                2003,
                102,
                "liam",
                ReviewState.CHANGES_REQUESTED,
                Instant.parse("2026-10-04T09:00:00Z")
            )
        );

        repository.addReview(
            new Review(
                2004,
                102,
                "sofia",
                ReviewState.APPROVED,
                Instant.parse("2026-10-04T10:00:00Z")
            )
        );

        repository.addReview(
            new Review(
                2005,
                103,
                "atul",
                ReviewState.APPROVED,
                Instant.parse("2026-10-04T12:00:00Z")
            )
        );

        repository.addComment(
            new ReviewComment(
                3001,
                101,
                "liam",
                "retry.py",
                88,
                true
            )
        );

        repository.addComment(
            new ReviewComment(
                3002,
                102,
                "liam",
                "risk_rules.py",
                42,
                false
            )
        );

        repository.addCheck(
            new StatusCheck(
                101,
                "unit-tests",
                CheckStatus.PASSED
            )
        );

        repository.addCheck(
            new StatusCheck(
                101,
                "integration-tests",
                CheckStatus.PASSED
            )
        );

        repository.addCheck(
            new StatusCheck(
                101,
                "security-scan",
                CheckStatus.PASSED
            )
        );

        repository.addCheck(
            new StatusCheck(
                102,
                "unit-tests",
                CheckStatus.PASSED
            )
        );

        repository.addCheck(
            new StatusCheck(
                102,
                "integration-tests",
                CheckStatus.FAILED
            )
        );

        repository.addCheck(
            new StatusCheck(
                102,
                "security-scan",
                CheckStatus.PASSED
            )
        );

        repository.addCheck(
            new StatusCheck(
                103,
                "unit-tests",
                CheckStatus.PASSED
            )
        );

        repository.addCheck(
            new StatusCheck(
                103,
                "security-scan",
                CheckStatus.PASSED
            )
        );

        repository.setPolicy(
            new BranchProtectionPolicy(
                "main",
                2,
                true,
                true,
                false,
                false,
                true,
                true
            )
        );

        repository.setPolicy(
            new BranchProtectionPolicy(
                "release/2026.10",
                1,
                true,
                true,
                false,
                false,
                true,
                true
            )
        );

        return repository;
    }

    static BranchHierarchyService createBranchHierarchy() {
        BranchHierarchyService hierarchy = new BranchHierarchyService();

        hierarchy.addRelationship("main", "release/2026.10");
        hierarchy.addRelationship("release/2026.10", "hotfix/auth");
        hierarchy.addRelationship("main", "feature/payment-timeout");
        hierarchy.addRelationship("main", "feature/risk-rules");

        /*
         * Deliberate cycle. A recursive CTE and this Java traversal both need
         * cycle protection when the relationship data is not guaranteed to be
         * a tree.
         */
        hierarchy.addRelationship("hotfix/auth", "main");

        return hierarchy;
    }

    static void printSummaries(QueryLogicService service) {
        System.out.println("\n=== Review summary intermediate relation ===");

        for (ReviewSummary summary : service.buildReviewSummaries()) {
            System.out.println(summary);
        }

        System.out.println("\n=== Status-check summary intermediate relation ===");

        for (CheckSummary summary : service.buildCheckSummaries()) {
            System.out.println(summary);
        }
    }

    static void printEligibility(QueryLogicService service, long id) {
        MergeEligibility result =
            service.evaluateMergeEligibility(id);

        System.out.println(
            "\nPR "
                + result.pullRequestId()
                + " -> "
                + (result.eligible() ? "ELIGIBLE" : "BLOCKED")
        );

        result.reasons().forEach(
            reason -> System.out.println("  " + reason)
        );
    }

    public static void main(String[] args) {
        RepositoryRepository repository = createCaseStudyRepository();
        QueryLogicService queryService =
            new QueryLogicService(repository);

        System.out.println("Advanced SQL CTE Enterprise Case Study");

        printSummaries(queryService);

        printEligibility(queryService, 101);
        printEligibility(queryService, 102);
        printEligibility(queryService, 103);

        System.out.println("\n=== Recursive hierarchy traversal ===");

        BranchHierarchyService hierarchy = createBranchHierarchy();

        hierarchy.traverse("main")
            .forEach(
                node ->
                    System.out.println(
                        "depth="
                            + node.depth()
                            + " branch="
                            + node.branch()
                    )
            );

        System.out.println(
            "\nCycle detection prevents main from being revisited."
        );

        System.out.println("\n=== Pull Request lifecycle ===");

        PullRequestLifecycleService lifecycle =
            new PullRequestLifecycleService();

        PullRequestState state =
            lifecycle.transition(
                PullRequestState.DRAFT,
                PullRequestState.OPEN
            );

        System.out.println("draft -> " + state);

        try {
            lifecycle.transition(
                PullRequestState.MERGED,
                PullRequestState.OPEN
            );
        } catch (IllegalStateException error) {
            System.out.println(
                "Rejected invalid lifecycle transition: "
                    + error.getMessage()
            );
        }

        System.out.println("\n=== CTE design principles represented here ===");
        System.out.println(
            "Independent intermediate facts are calculated before the "
                + "final policy decision. This mirrors a chained SQL CTE "
                + "pipeline and prevents review, approval, and status-check "
                + "logic from becoming one opaque expression."
        );

        System.out.println(
            "Recursive traversal requires an explicit termination rule. "
                + "The visited set is the Java equivalent of a path-membership "
                + "guard in a recursive SQL query."
        );
    }
}
