import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/*
 * Java 17 enterprise-oriented control-flow model.
 *
 * The domain represents repository governance. Control-flow constructs are
 * used to model review states, policy checks, status validation, and explicit
 * merge eligibility rather than as unrelated language demonstrations.
 */
public class RepositoryControlFlow {

    enum ReviewState {
        COMMENTED,
        CHANGES_REQUESTED,
        APPROVED
    }

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    record StatusCheck(String name, boolean passed) {
        StatusCheck {
            Objects.requireNonNull(name, "check name");
            if (name.isBlank()) {
                throw new IllegalArgumentException("check name cannot be blank");
            }
        }
    }

    record Review(String reviewer, ReviewState state) {
        Review {
            Objects.requireNonNull(reviewer, "reviewer");
            Objects.requireNonNull(state, "review state");

            if (reviewer.isBlank()) {
                throw new IllegalArgumentException("reviewer cannot be blank");
            }
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private PullRequestState state;
        private final List<StatusCheck> checks;
        private final List<Review> reviews;
        private final boolean mergeConflict;

        PullRequest(
                int number,
                String sourceBranch,
                String targetBranch,
                PullRequestState state,
                List<StatusCheck> checks,
                List<Review> reviews,
                boolean mergeConflict
        ) {
            if (number <= 0) {
                throw new IllegalArgumentException("PR number must be positive");
            }

            if (sourceBranch.isBlank() || targetBranch.isBlank()) {
                throw new IllegalArgumentException("branches cannot be blank");
            }

            this.number = number;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.state = Objects.requireNonNull(state);
            this.checks = new ArrayList<>(checks);
            this.reviews = new ArrayList<>(reviews);
            this.mergeConflict = mergeConflict;
        }

        int number() {
            return number;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        PullRequestState state() {
            return state;
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        boolean mergeConflict() {
            return mergeConflict;
        }

        void merge() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                        "only an open pull request can be merged"
                );
            }

            state = PullRequestState.MERGED;
        }
    }

    record BranchProtection(
            String branch,
            int requiredApprovals,
            boolean requireChecks,
            boolean restrictDirectPushes
    ) {
        BranchProtection {
            if (branch.isBlank()) {
                throw new IllegalArgumentException("protected branch is required");
            }

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                        "approval requirement cannot be negative"
                );
            }
        }
    }

    static final class MergeDecision {
        private final boolean eligible;
        private final List<String> reasons;

        MergeDecision(boolean eligible, List<String> reasons) {
            this.eligible = eligible;
            this.reasons = List.copyOf(reasons);
        }

        boolean eligible() {
            return eligible;
        }

        List<String> reasons() {
            return reasons;
        }
    }

    static MergeDecision evaluate(
            PullRequest pullRequest,
            BranchProtection policy
    ) {
        List<String> reasons = new ArrayList<>();

        if (!pullRequest.targetBranch().equals(policy.branch())) {
            reasons.add("target branch is not protected branch");
        } else if (pullRequest.sourceBranch()
                .equals(pullRequest.targetBranch())) {
            reasons.add("source and target branches are identical");
        }

        if (pullRequest.state() == PullRequestState.DRAFT) {
            reasons.add("pull request is still a draft");
        } else if (pullRequest.state() != PullRequestState.OPEN) {
            reasons.add("pull request is not open");
        }

        if (pullRequest.mergeConflict()) {
            reasons.add("merge conflicts exist");
        }

        if (policy.requireChecks()) {
            for (StatusCheck check : pullRequest.checks()) {
                if (!check.passed()) {
                    reasons.add("failed required check: " + check.name());
                    break;
                }
            }
        }

        int approvals = 0;

        for (Review review : pullRequest.reviews()) {
            if (review.state() == ReviewState.APPROVED) {
                approvals++;
            } else if (review.state() == ReviewState.CHANGES_REQUESTED) {
                // A requested-change review is not an approval and is retained
                // as an explicit policy failure signal.
                reasons.add(
                        "reviewer " + review.reviewer() + " requested changes"
                );
            } else {
                // A comment-only review does not change approval count.
                continue;
            }
        }

        if (approvals < policy.requiredApprovals()) {
            reasons.add(
                    "required approvals: " + policy.requiredApprovals()
                            + ", current approvals: " + approvals
            );
        }

        return new MergeDecision(reasons.isEmpty(), reasons);
    }

    static void demonstrateIfElse() {
        System.out.println("\nIF / ELSE IF / ELSE");

        int riskScore = 74;

        if (riskScore >= 90) {
            System.out.println("Critical review path");
        } else if (riskScore >= 70) {
            System.out.println("Elevated review path");
        } else if (riskScore >= 40) {
            System.out.println("Standard review path");
        } else {
            System.out.println("Low-risk review path");
        }
    }

    static void demonstrateForContinueBreak() {
        System.out.println("\nFOR, CONTINUE, BREAK");

        List<String> events = List.of(
                "push",
                "documentation",
                "review",
                "failed-check",
                "merge"
        );

        for (String event : events) {
            if (event.equals("documentation")) {
                continue;
            }

            if (event.equals("failed-check")) {
                System.out.println("Blocking event encountered.");
                break;
            }

            System.out.println("Processing event: " + event);
        }
    }

    static void demonstrateWhile() {
        System.out.println("\nWHILE");

        int attempts = 0;
        boolean available = false;

        while (attempts < 3) {
            attempts++;

            if (attempts == 2) {
                available = true;
            }

            if (available) {
                break;
            }

            System.out.println("Retrying policy service...");
        }

        if (available) {
            System.out.println("Policy service available.");
        } else {
            System.out.println("Policy service unavailable.");
        }
    }

    static void demonstratePassEquivalent() {
        System.out.println("\nPASS EQUIVALENT");

        List<ReviewState> states = List.of(
                ReviewState.COMMENTED,
                ReviewState.APPROVED,
                ReviewState.CHANGES_REQUESTED
        );

        for (ReviewState state : states) {
            if (state == ReviewState.COMMENTED) {
                /*
                 * Java has no pass keyword. An empty block intentionally
                 * performs no operation while preserving valid control flow.
                 */
            } else if (state == ReviewState.APPROVED) {
                System.out.println("Approval recorded.");
            } else {
                System.out.println("Developer action required.");
            }
        }
    }

    static void runEnterpriseScenario() {
        System.out.println("\nENTERPRISE MERGE POLICY");

        BranchProtection policy = new BranchProtection(
                "main",
                2,
                true,
                true
        );

        PullRequest ready = new PullRequest(
                701,
                "feature/identity",
                "main",
                PullRequestState.OPEN,
                List.of(
                        new StatusCheck("unit-tests", true),
                        new StatusCheck("security-scan", true),
                        new StatusCheck("lint", true)
                ),
                List.of(
                        new Review("alice", ReviewState.APPROVED),
                        new Review("bob", ReviewState.APPROVED)
                ),
                false
        );

        PullRequest blocked = new PullRequest(
                702,
                "feature/billing",
                "main",
                PullRequestState.OPEN,
                List.of(
                        new StatusCheck("unit-tests", true),
                        new StatusCheck("security-scan", false)
                ),
                List.of(
                        new Review("alice", ReviewState.APPROVED),
                        new Review("bob", ReviewState.CHANGES_REQUESTED)
                ),
                true
        );

        for (PullRequest pr : List.of(ready, blocked)) {
            MergeDecision decision = evaluate(pr, policy);

            if (decision.eligible()) {
                System.out.println("PR #" + pr.number() + " is merge eligible.");

                try {
                    pr.merge();
                    System.out.println("PR #" + pr.number() + " transitioned to MERGED.");
                } catch (IllegalStateException error) {
                    System.out.println("Merge rejected: " + error.getMessage());
                }
            } else {
                System.out.println("PR #" + pr.number() + " is blocked.");

                for (String reason : decision.reasons()) {
                    System.out.println("  " + reason);
                }
            }
        }
    }

    public static void main(String[] args) {
        try {
            demonstrateIfElse();
            demonstrateForContinueBreak();
            demonstrateWhile();
            demonstratePassEquivalent();
            runEnterpriseScenario();
        } catch (RuntimeException error) {
            System.err.println("Execution failed: " + error.getMessage());
            System.exit(1);
        }
    }
}
