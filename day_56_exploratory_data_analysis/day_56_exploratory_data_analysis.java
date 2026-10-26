import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class RepositoryGovernanceEDA {

    enum PullRequestState {
        DRAFT,
        OPEN,
        CHANGES_REQUESTED,
        APPROVED,
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
        PASSING,
        FAILING,
        PENDING
    }

    enum MergeStrategy {
        MERGE_COMMIT,
        SQUASH,
        REBASE
    }

    record Commit(String id, String message) {
        public Commit {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Commit ID is required.");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("Commit message is required.");
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        boolean eligible,
        boolean stale
    ) {
        public Review {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required.");
            }
            if (state == null) {
                throw new IllegalArgumentException("Review state is required.");
            }
        }
    }

    record StatusCheck(
        String name,
        CheckState state,
        boolean required
    ) {
        public StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Status check name is required.");
            }
            if (state == null) {
                throw new IllegalArgumentException("Status check state is required.");
            }
        }
    }

    record BranchProtectionPolicy(
        String branchName,
        int requiredApprovals,
        boolean requiredStatusChecks,
        boolean requiredResolvedConversations,
        boolean restrictDirectPush,
        boolean restrictForcePush,
        boolean restrictDeletion,
        boolean requireLinearHistory,
        boolean administratorBypass,
        Set<MergeStrategy> allowedStrategies
    ) {
        public BranchProtectionPolicy {
            if (branchName == null || branchName.isBlank()) {
                throw new IllegalArgumentException("Protected branch is required.");
            }
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval count cannot be negative.");
            }
            allowedStrategies = Set.copyOf(allowedStrategies);
        }
    }

    static final class PullRequest {
        private final int id;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Commit> commits;
        private final List<Review> reviews;
        private final List<StatusCheck> checks;
        private PullRequestState state;
        private boolean conflicts;
        private boolean conversationsResolved;
        private boolean branchSynchronized;

        PullRequest(
            int id,
            String sourceBranch,
            String targetBranch,
            List<Commit> commits,
            List<Review> reviews,
            List<StatusCheck> checks
        ) {
            if (id <= 0) {
                throw new IllegalArgumentException("Pull Request ID must be positive.");
            }
            if (sourceBranch == null || targetBranch == null ||
                sourceBranch.isBlank() || targetBranch.isBlank()) {
                throw new IllegalArgumentException("Branches are required.");
            }
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ."
                );
            }

            this.id = id;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.commits = new ArrayList<>(commits);
            this.reviews = new ArrayList<>(reviews);
            this.checks = new ArrayList<>(checks);
            this.state = PullRequestState.OPEN;
            this.conflicts = false;
            this.conversationsResolved = true;
            this.branchSynchronized = true;
        }

        int id() {
            return id;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks);
        }

        PullRequestState state() {
            return state;
        }

        void setState(PullRequestState state) {
            if (state == null) {
                throw new IllegalArgumentException("State cannot be null.");
            }
            this.state = state;
        }

        boolean conflicts() {
            return conflicts;
        }

        void setConflicts(boolean conflicts) {
            this.conflicts = conflicts;
        }

        boolean conversationsResolved() {
            return conversationsResolved;
        }

        void setConversationsResolved(boolean resolved) {
            this.conversationsResolved = resolved;
        }

        boolean branchSynchronized() {
            return branchSynchronized;
        }

        void setBranchSynchronized(boolean synchronizedState) {
            this.branchSynchronized = synchronizedState;
        }

        boolean hasCommits() {
            return !commits.isEmpty();
        }
    }

    static final class MergeEligibilityService {

        List<String> evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy,
            MergeStrategy strategy
        ) {
            List<String> failures = new ArrayList<>();

            if (!pullRequest.hasCommits()) {
                failures.add("Pull Request contains no commits.");
            }

            if (pullRequest.state() == PullRequestState.DRAFT) {
                failures.add("Draft Pull Request cannot be merged.");
            }

            if (pullRequest.state() == PullRequestState.CHANGES_REQUESTED) {
                failures.add("Review process contains requested changes.");
            }

            if (pullRequest.conflicts()) {
                failures.add("Merge conflicts remain unresolved.");
            }

            if (!pullRequest.branchSynchronized()) {
                failures.add("Source branch is behind the protected target branch.");
            }

            if (policy.requiredResolvedConversations() &&
                !pullRequest.conversationsResolved()) {
                failures.add("Required review conversations are unresolved.");
            }

            if (countCurrentApprovals(pullRequest) <
                policy.requiredApprovals()) {
                failures.add("Required eligible approvals are missing.");
            }

            if (policy.requiredStatusChecks() &&
                !allRequiredChecksPassing(pullRequest)) {
                failures.add("One or more required status checks are not passing.");
            }

            if (!policy.allowedStrategies().contains(strategy)) {
                failures.add("Merge strategy is not permitted.");
            }

            return List.copyOf(failures);
        }

        private int countCurrentApprovals(PullRequest pullRequest) {
            Set<String> reviewers = new HashSet<>();

            for (Review review : pullRequest.reviews()) {
                if (review.eligible() &&
                    !review.stale() &&
                    review.state() == ReviewState.APPROVED) {
                    reviewers.add(review.reviewer());
                }
            }

            return reviewers.size();
        }

        private boolean allRequiredChecksPassing(PullRequest pullRequest) {
            for (StatusCheck check : pullRequest.checks()) {
                if (check.required() &&
                    check.state() != CheckState.PASSING) {
                    return false;
                }
            }
            return true;
        }

        void merge(
            PullRequest pullRequest,
            BranchProtectionPolicy policy,
            MergeStrategy strategy
        ) {
            List<String> failures = evaluate(
                pullRequest,
                policy,
                strategy
            );

            if (!failures.isEmpty()) {
                throw new IllegalStateException(
                    "Merge rejected: " + String.join("; ", failures)
                );
            }

            pullRequest.setState(PullRequestState.MERGED);
        }
    }

    static Map<String, Double> describe(List<Double> values) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException("Cannot describe empty data.");
        }

        double sum = values.stream()
            .mapToDouble(Double::doubleValue)
            .sum();

        double mean = sum / values.size();

        List<Double> sorted = values.stream()
            .sorted()
            .toList();

        double median;
        int middle = sorted.size() / 2;

        if (sorted.size() % 2 == 0) {
            median = (sorted.get(middle - 1) + sorted.get(middle)) / 2.0;
        } else {
            median = sorted.get(middle);
        }

        double variance = values.stream()
            .mapToDouble(value -> Math.pow(value - mean, 2))
            .average()
            .orElse(0.0);

        Map<String, Double> result = new HashMap<>();
        result.put("count", (double) values.size());
        result.put("mean", mean);
        result.put("median", median);
        result.put("minimum", sorted.getFirst());
        result.put("maximum", sorted.getLast());
        result.put("populationStdDev", Math.sqrt(variance));

        return Map.copyOf(result);
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy =
            new BranchProtectionPolicy(
                "main",
                2,
                true,
                true,
                true,
                true,
                true,
                true,
                false,
                EnumSet.of(
                    MergeStrategy.SQUASH,
                    MergeStrategy.REBASE
                )
            );

        PullRequest pullRequest =
            new PullRequest(
                501,
                "feature/customer-eda",
                "main",
                List.of(
                    new Commit("a1", "Add profiling workflow"),
                    new Commit("b2", "Add anomaly checks")
                ),
                List.of(
                    new Review(
                        "alice",
                        ReviewState.APPROVED,
                        true,
                        false
                    ),
                    new Review(
                        "bob",
                        ReviewState.APPROVED,
                        true,
                        false
                    ),
                    new Review(
                        "external",
                        ReviewState.APPROVED,
                        false,
                        false
                    )
                ),
                List.of(
                    new StatusCheck(
                        "unit-tests",
                        CheckState.PASSING,
                        true
                    ),
                    new StatusCheck(
                        "security-scan",
                        CheckState.PASSING,
                        true
                    )
                )
            );

        MergeEligibilityService service =
            new MergeEligibilityService();

        List<String> failures = service.evaluate(
            pullRequest,
            policy,
            MergeStrategy.SQUASH
        );

        if (!failures.isEmpty()) {
            throw new IllegalStateException(
                String.join("; ", failures)
            );
        }

        service.merge(
            pullRequest,
            policy,
            MergeStrategy.SQUASH
        );

        System.out.println(
            "Pull Request " + pullRequest.id() +
            " state: " + pullRequest.state()
        );

        List<Double> monthlySpend =
            List.of(
                280.0, 450.0, 680.0, 820.0,
                390.0, 540.0, 1450.0, 610.0,
                330.0, 760.0
            );

        Map<String, Double> statistics =
            describe(monthlySpend);

        System.out.println("EDA statistics:");
        statistics.forEach(
            (key, value) ->
                System.out.printf(
                    "  %s = %.2f%n",
                    key,
                    value
                )
        );

        /*
         * Stale approvals do not count toward current eligibility.
         * This explicit state prevents an old approval from surviving
         * a branch state change without policy review.
         */
        PullRequest staleApprovalExample =
            new PullRequest(
                502,
                "feature/stale-review",
                "main",
                List.of(new Commit("c3", "Change analytical logic")),
                List.of(
                    new Review(
                        "alice",
                        ReviewState.APPROVED,
                        true,
                        true
                    ),
                    new Review(
                        "bob",
                        ReviewState.APPROVED,
                        true,
                        false
                    )
                ),
                List.of(
                    new StatusCheck(
                        "unit-tests",
                        CheckState.PASSING,
                        true
                    )
                )
            );

        List<String> staleFailures = service.evaluate(
            staleApprovalExample,
            policy,
            MergeStrategy.SQUASH
        );

        if (staleFailures.isEmpty()) {
            throw new IllegalStateException(
                "Stale approval should have prevented eligibility."
            );
        }

        System.out.println(
            "Stale-approval policy validation passed."
        );
    }
}
