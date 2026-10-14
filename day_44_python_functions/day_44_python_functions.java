import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.function.UnaryOperator;
import java.util.stream.Collectors;

/*
 * Enterprise Repository Governance
 *
 * Java 17+
 * Compile: javac RepositoryGovernance.java
 * Run:     java RepositoryGovernance
 *
 * Functions are represented through typed methods, predicates, transformations,
 * and services. The domain model distinguishes review decisions from repository
 * policy and final merge eligibility.
 */
public class RepositoryGovernance {

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

    enum CheckState {
        PENDING,
        PASSED,
        FAILED
    }

    enum MergeStrategy {
        MERGE_COMMIT,
        SQUASH,
        REBASE
    }

    record Reviewer(String username, boolean eligibleToApprove) {
        Reviewer {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Reviewer username is required");
            }
        }
    }

    record Review(
        Reviewer reviewer,
        ReviewState state,
        String summary,
        boolean discussionResolved
    ) {
        Review {
            Objects.requireNonNull(reviewer, "Reviewer is required");
            Objects.requireNonNull(state, "Review state is required");

            if (summary == null) {
                summary = "";
            }
        }
    }

    record StatusCheck(String name, CheckState state) {
        StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Status check name is required");
            }
            Objects.requireNonNull(state, "Status state is required");
        }
    }

    record BranchProtectionPolicy(
        String protectedBranch,
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireUpToDate,
        boolean requireResolvedDiscussions,
        boolean requireLinearHistory,
        boolean blockForcePushes,
        boolean blockDeletion,
        boolean allowAdministratorBypass,
        Set<MergeStrategy> allowedMergeStrategies
    ) {
        BranchProtectionPolicy {
            if (protectedBranch == null || protectedBranch.isBlank()) {
                throw new IllegalArgumentException("Protected branch is required");
            }
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval threshold cannot be negative");
            }

            requiredChecks = Set.copyOf(requiredChecks);
            allowedMergeStrategies = Set.copyOf(allowedMergeStrategies);

            if (allowedMergeStrategies.isEmpty()) {
                throw new IllegalArgumentException("At least one merge strategy is required");
            }
        }
    }

    record PullRequest(
        int id,
        String title,
        String author,
        String sourceBranch,
        String targetBranch,
        PullRequestState state,
        boolean sourceUpToDate,
        boolean conflictsPresent,
        boolean linearHistoryAvailable,
        List<Review> reviews,
        List<StatusCheck> checks
    ) {
        PullRequest {
            if (id <= 0) {
                throw new IllegalArgumentException("Pull Request ID must be positive");
            }
            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException("Pull Request title is required");
            }
            if (author == null || author.isBlank()) {
                throw new IllegalArgumentException("Author is required");
            }
            if (sourceBranch == null || sourceBranch.isBlank()
                    || targetBranch == null || targetBranch.isBlank()) {
                throw new IllegalArgumentException("Both branches are required");
            }
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException("Source and target must differ");
            }

            Objects.requireNonNull(state, "Pull Request state is required");
            reviews = List.copyOf(reviews);
            checks = List.copyOf(checks);
        }
    }

    record MergeDecision(boolean eligible, List<String> reasons) {
        MergeDecision {
            reasons = List.copyOf(reasons);
        }
    }

    // Review policy is isolated from branch-protection mechanics. The predicate
    // can be reused by approval counting without embedding policy in each caller.
    static Predicate<Review> eligibleApproval() {
        return review ->
            review.reviewer().eligibleToApprove()
                && review.state() == ReviewState.APPROVED;
    }

    static List<Review> latestReviewPerReviewer(List<Review> reviews) {
        Map<String, Review> latest = new HashMap<>();

        // Input order represents event order in this demonstration. A production
        // implementation should order persisted review events by creation time.
        for (Review review : reviews) {
            latest.put(review.reviewer().username(), review);
        }

        return List.copyOf(latest.values());
    }

    static int countApprovals(List<Review> reviews) {
        return (int) latestReviewPerReviewer(reviews).stream()
            .filter(eligibleApproval())
            .count();
    }

    static boolean hasOutstandingChangeRequest(List<Review> reviews) {
        return latestReviewPerReviewer(reviews).stream()
            .anyMatch(review ->
                review.reviewer().eligibleToApprove()
                    && review.state() == ReviewState.CHANGES_REQUESTED
            );
    }

    static boolean discussionsAreResolved(List<Review> reviews) {
        return reviews.stream()
            .allMatch(Review::discussionResolved);
    }

    static Map<String, CheckState> effectiveChecks(List<StatusCheck> checks) {
        Map<String, CheckState> effective = new HashMap<>();

        // Repeated check names represent newer check runs; the last is effective.
        for (StatusCheck check : checks) {
            effective.put(check.name(), check.state());
        }

        return Map.copyOf(effective);
    }

    static final class MergeEligibilityService {

        MergeDecision evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy,
            MergeStrategy requestedStrategy
        ) {
            List<String> blockers = new ArrayList<>();

            if (pullRequest.state() != PullRequestState.OPEN) {
                blockers.add("Pull Request must be open and not merged");
            }

            if (!pullRequest.targetBranch().equals(policy.protectedBranch())) {
                blockers.add("Target branch does not match the protected branch");
            }

            if (pullRequest.conflictsPresent()) {
                blockers.add("Merge conflicts must be resolved");
            }

            if (policy.requireUpToDate() && !pullRequest.sourceUpToDate()) {
                blockers.add("Source branch is behind the target branch");
            }

            if (policy.requireLinearHistory()
                    && !pullRequest.linearHistoryAvailable()) {
                blockers.add("Linear history is required");
            }

            if (!policy.allowedMergeStrategies().contains(requestedStrategy)) {
                blockers.add("Requested merge strategy is not allowed");
            }

            if (hasOutstandingChangeRequest(pullRequest.reviews())) {
                blockers.add("An eligible reviewer has requested changes");
            }

            int approvals = countApprovals(pullRequest.reviews());
            if (approvals < policy.requiredApprovals()) {
                blockers.add(
                    "Approval threshold not met: " + approvals
                        + " of " + policy.requiredApprovals()
                );
            }

            if (policy.requireResolvedDiscussions()
                    && !discussionsAreResolved(pullRequest.reviews())) {
                blockers.add("Review discussions remain unresolved");
            }

            Map<String, CheckState> observedChecks =
                effectiveChecks(pullRequest.checks());

            for (String required : policy.requiredChecks()) {
                CheckState actual = observedChecks.get(required);

                if (actual == null) {
                    blockers.add("Required check is missing: " + required);
                } else if (actual != CheckState.PASSED) {
                    blockers.add(
                        "Required check is not passing: "
                            + required + " (" + actual + ")"
                    );
                }
            }

            return new MergeDecision(blockers.isEmpty(), blockers);
        }
    }

    // A higher-order method receives a transformation and applies it only after
    // validating the input. This pattern separates reusable policy from behavior.
    static double transformBudget(
        double amount,
        UnaryOperator<Double> transformation
    ) {
        if (!Double.isFinite(amount) || amount < 0) {
            throw new IllegalArgumentException("Budget must be finite and non-negative");
        }

        double result = transformation.apply(amount);

        if (!Double.isFinite(result) || result < 0) {
            throw new IllegalStateException("Transformation produced an invalid budget");
        }

        return result;
    }

    static void printDecision(PullRequest pr, MergeDecision decision) {
        System.out.printf("%nPR #%d: %s%n", pr.id(), pr.title());
        System.out.println("Target: " + pr.targetBranch());
        System.out.println("Merge eligible: " + decision.eligible());

        if (!decision.reasons().isEmpty()) {
            decision.reasons().forEach(reason -> System.out.println(" - " + reason));
        }
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy = new BranchProtectionPolicy(
            "main",
            2,
            Set.of("build", "unit-tests", "security-scan"),
            true,
            true,
            true,
            true,
            true,
            false,
            Set.of(MergeStrategy.SQUASH, MergeStrategy.REBASE)
        );

        Reviewer ada = new Reviewer("ada", true);
        Reviewer lin = new Reviewer("lin", true);
        Reviewer bot = new Reviewer("ci-review-bot", false);

        PullRequest ready = new PullRequest(
            621,
            "Enforce payment request validation",
            "developer-lee",
            "feature/payment-validation",
            "main",
            PullRequestState.OPEN,
            true,
            false,
            true,
            List.of(
                new Review(ada, ReviewState.APPROVED, "Boundary cases checked", true),
                new Review(lin, ReviewState.APPROVED, "Failure paths checked", true),
                new Review(bot, ReviewState.APPROVED, "Automated inspection", true)
            ),
            List.of(
                new StatusCheck("build", CheckState.PASSED),
                new StatusCheck("unit-tests", CheckState.PASSED),
                new StatusCheck("security-scan", CheckState.PASSED)
            )
        );

        PullRequest blocked = new PullRequest(
            622,
            "Change authentication token handling",
            "developer-kim",
            "feature/token-handling",
            "main",
            PullRequestState.OPEN,
            false,
            true,
            false,
            List.of(
                new Review(ada, ReviewState.APPROVED, "Initial review", true),
                new Review(lin, ReviewState.CHANGES_REQUESTED,
                    "Expiry validation is incomplete", false)
            ),
            List.of(
                new StatusCheck("build", CheckState.PASSED),
                new StatusCheck("unit-tests", CheckState.PENDING)
            )
        );

        MergeEligibilityService service = new MergeEligibilityService();

        MergeDecision readyDecision =
            service.evaluate(ready, policy, MergeStrategy.SQUASH);
        MergeDecision blockedDecision =
            service.evaluate(blocked, policy, MergeStrategy.MERGE_COMMIT);

        printDecision(ready, readyDecision);
        printDecision(blocked, blockedDecision);

        System.out.println("\nHigher-order budget transformation");
        double deploymentBudget = transformBudget(
            125_000,
            amount -> Math.round(amount * 0.92 * 100.0) / 100.0
        );
        System.out.printf("Adjusted budget: %.2f%n", deploymentBudget);

        System.out.println("\nFunction-based review metrics");
        Map<ReviewState, Long> reviewCounts = ready.reviews().stream()
            .collect(Collectors.groupingBy(
                Review::state,
                Collectors.counting()
            ));

        System.out.println(reviewCounts);

        // These are policy decisions, not merge execution. A real merge operation
        // must recheck current branch and review state atomically to avoid races.
        if (readyDecision.eligible() && !blockedDecision.eligible()) {
            System.out.println("Governance evaluation behaved as expected.");
        } else {
            throw new IllegalStateException("Unexpected merge eligibility result");
        }
    }
}
