import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;

public class RepositoryGovernance {
    enum PullRequestState {
        DRAFT, OPEN, MERGED, CLOSED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    static class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }

        GovernanceException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    static final class ValidationException extends GovernanceException {
        ValidationException(String message) {
            super(message);
        }
    }

    static final class InvalidTransitionException extends GovernanceException {
        InvalidTransitionException(String message) {
            super(message);
        }
    }

    static final class ReviewPolicyException extends GovernanceException {
        ReviewPolicyException(String message) {
            super(message);
        }
    }

    static final class MergeRejectedException extends GovernanceException {
        private final List<String> violations;

        MergeRejectedException(List<String> violations) {
            super("Merge rejected: " + String.join(" ", violations));
            this.violations = List.copyOf(violations);
        }

        List<String> violations() {
            return violations;
        }
    }

    record Repository(String fullName, String defaultBranch) {
        Repository {
            requireText(fullName, "Repository name");
            requireText(defaultBranch, "Default branch");

            if (!fullName.contains("/")) {
                throw new ValidationException(
                    "Repository name must use owner/repository format."
                );
            }
        }
    }

    record ReviewComment(
        String filePath,
        int lineNumber,
        String body,
        boolean resolved
    ) {
        ReviewComment {
            requireText(filePath, "Comment file path");
            requireText(body, "Comment body");

            if (lineNumber < 1) {
                throw new ValidationException("Comment line must be positive.");
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        String commitSha,
        Instant submittedAt,
        List<ReviewComment> comments
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            Objects.requireNonNull(state, "Review state");
            requireText(commitSha, "Reviewed commit SHA");
            Objects.requireNonNull(submittedAt, "Submission time");
            comments = List.copyOf(comments);
        }
    }

    record Commit(String sha, String message, Instant createdAt) {
        Commit {
            requireText(sha, "Commit SHA");
            requireText(message, "Commit message");
            Objects.requireNonNull(createdAt, "Commit timestamp");
        }
    }

    record BranchProtectionPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean dismissStaleApprovals,
        boolean requireResolvedConversations,
        boolean prohibitDirectPushes,
        boolean prohibitForcePushes,
        boolean prohibitDeletion,
        boolean requireLinearHistory,
        boolean allowMergeCommit,
        boolean allowSquash,
        boolean allowRebase
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new ValidationException(
                    "Required approval count cannot be negative."
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
            if (requiredChecks.stream().anyMatch(String::isBlank)) {
                throw new ValidationException(
                    "Required check names cannot be blank."
                );
            }

            if (!allowMergeCommit && !allowSquash && !allowRebase) {
                throw new ValidationException(
                    "At least one merge strategy must be enabled."
                );
            }
        }

        boolean allows(MergeStrategy strategy) {
            return switch (strategy) {
                case MERGE_COMMIT -> allowMergeCommit;
                case SQUASH -> allowSquash;
                case REBASE -> allowRebase;
            };
        }
    }

    static final class PullRequest {
        private final int number;
        private final Repository repository;
        private final String title;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, Boolean> checks = new HashMap<>();
        private PullRequestState state = PullRequestState.DRAFT;
        private int unresolvedConversations;
        private boolean baseBranchUpToDate;
        private boolean hasMergeConflict;
        private boolean linearHistoryPossible = true;

        PullRequest(
            int number,
            Repository repository,
            String title,
            String author,
            String sourceBranch,
            String targetBranch,
            String headSha
        ) {
            if (number <= 0) {
                throw new ValidationException(
                    "Pull request number must be positive."
                );
            }

            this.number = number;
            this.repository = Objects.requireNonNull(repository, "Repository");
            this.title = requireText(title, "Title");
            this.author = requireText(author, "Author");
            this.sourceBranch = requireText(sourceBranch, "Source branch");
            this.targetBranch = requireText(targetBranch, "Target branch");

            if (sourceBranch.equals(targetBranch)) {
                throw new ValidationException(
                    "Source and target branches must differ."
                );
            }

            commits.add(new Commit(
                requireText(headSha, "Head SHA"),
                "Initial pull request commit",
                Instant.now()
            ));
        }

        int number() {
            return number;
        }

        String author() {
            return author;
        }

        String headSha() {
            return commits.get(commits.size() - 1).sha();
        }

        PullRequestState state() {
            return state;
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        void publish() {
            transition(PullRequestState.DRAFT, PullRequestState.OPEN);
        }

        private void transition(
            PullRequestState expected,
            PullRequestState next
        ) {
            if (state != expected) {
                throw new InvalidTransitionException(
                    "Cannot change state from " + state + " to " + next + "."
                );
            }
            state = next;
        }

        void addCommit(Commit commit) {
            requireOpen();
            Objects.requireNonNull(commit, "Commit");

            if (commits.stream().anyMatch(
                existing -> existing.sha().equals(commit.sha())
            )) {
                throw new ValidationException(
                    "Duplicate commit SHA within pull request history."
                );
            }

            commits.add(commit);
            checks.clear();
            baseBranchUpToDate = false;
        }

        void synchronizeBase(boolean conflictDetected) {
            requireOpen();
            baseBranchUpToDate = true;
            hasMergeConflict = conflictDetected;
        }

        void setLinearHistoryPossible(boolean possible) {
            requireOpen();
            linearHistoryPossible = possible;
        }

        void setUnresolvedConversations(int count) {
            requireOpen();

            if (count < 0) {
                throw new ValidationException(
                    "Unresolved conversation count cannot be negative."
                );
            }
            unresolvedConversations = count;
        }

        void recordCheck(String name, boolean passed) {
            requireOpen();
            checks.put(requireText(name, "Check name"), passed);
        }

        void submitReview(Review review) {
            requireOpen();
            Objects.requireNonNull(review, "Review");

            if (review.reviewer().equals(author)) {
                throw new ReviewPolicyException(
                    "The pull request author cannot review their own changes."
                );
            }

            reviews.add(review);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, Boolean> checks() {
            return Map.copyOf(checks);
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        boolean baseBranchUpToDate() {
            return baseBranchUpToDate;
        }

        boolean hasMergeConflict() {
            return hasMergeConflict;
        }

        boolean linearHistoryPossible() {
            return linearHistoryPossible;
        }

        String targetBranch() {
            return targetBranch;
        }

        Repository repository() {
            return repository;
        }

        void merge(
            BranchProtectionPolicy policy,
            MergeStrategy strategy,
            MergeEligibilityService eligibilityService
        ) {
            requireOpen();

            List<String> failures = eligibilityService.evaluate(
                this, policy, strategy
            );

            if (!failures.isEmpty()) {
                throw new MergeRejectedException(failures);
            }

            state = PullRequestState.MERGED;
        }

        void close() {
            transition(PullRequestState.OPEN, PullRequestState.CLOSED);
        }

        void reopen() {
            transition(PullRequestState.CLOSED, PullRequestState.OPEN);
        }

        private void requireOpen() {
            if (state != PullRequestState.OPEN) {
                throw new InvalidTransitionException(
                    "Operation requires an open pull request."
                );
            }
        }
    }

    static final class MergeEligibilityService {
        List<String> evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy,
            MergeStrategy strategy
        ) {
            List<String> failures = new ArrayList<>();

            if (!policy.allows(strategy)) {
                failures.add("Selected merge strategy is prohibited.");
            }

            if (!pullRequest.baseBranchUpToDate()) {
                failures.add("Base branch synchronization is required.");
            }

            if (pullRequest.hasMergeConflict()) {
                failures.add("Merge conflicts must be resolved.");
            }

            if (
                policy.requireLinearHistory() &&
                !pullRequest.linearHistoryPossible()
            ) {
                failures.add("Selected operation would violate linear history.");
            }

            if (
                policy.requireResolvedConversations() &&
                pullRequest.unresolvedConversations() > 0
            ) {
                failures.add("Review conversations remain unresolved.");
            }

            Set<String> approvedReviewers = eligibleApprovals(
                pullRequest, policy
            );

            if (approvedReviewers.size() < policy.requiredApprovals()) {
                failures.add(
                    "Current approvals: " + approvedReviewers.size() +
                    "; required: " + policy.requiredApprovals() + "."
                );
            }

            for (String requiredCheck : policy.requiredChecks()) {
                if (!Boolean.TRUE.equals(
                    pullRequest.checks().get(requiredCheck)
                )) {
                    failures.add("Required check missing or failed: " + requiredCheck);
                }
            }

            return List.copyOf(failures);
        }

        private Set<String> eligibleApprovals(
            PullRequest pullRequest,
            BranchProtectionPolicy policy
        ) {
            Map<String, Review> latestByReviewer = new HashMap<>();

            for (Review review : pullRequest.reviews()) {
                if (
                    policy.dismissStaleApprovals() &&
                    !review.commitSha().equals(pullRequest.headSha())
                ) {
                    continue;
                }

                Review existing = latestByReviewer.get(review.reviewer());
                if (
                    existing == null ||
                    review.submittedAt().isAfter(existing.submittedAt())
                ) {
                    latestByReviewer.put(review.reviewer(), review);
                }
            }

            return latestByReviewer.values().stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .map(Review::reviewer)
                .collect(Collectors.toCollection(TreeSet::new));
        }
    }

    static void enforceProtectedBranchOperation(
        String branch,
        String operation,
        BranchProtectionPolicy policy
    ) {
        requireText(branch, "Branch name");

        if (!branch.equals("main")) {
            return;
        }

        boolean prohibited = switch (operation) {
            case "direct-push" -> policy.prohibitDirectPushes();
            case "force-push" -> policy.prohibitForcePushes();
            case "delete" -> policy.prohibitDeletion();
            default -> throw new ValidationException(
                "Unknown protected branch operation: " + operation
            );
        };

        if (prohibited) {
            throw new GovernanceException(
                operation + " is prohibited on protected branch main."
            );
        }
    }

    static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " cannot be blank.");
        }
        return value.trim();
    }

    static BranchProtectionPolicy productionPolicy() {
        return new BranchProtectionPolicy(
            2,
            Set.of("unit-tests", "security-scan"),
            true,
            true,
            true,
            true,
            true,
            true,
            false,
            true,
            true
        );
    }

    static Review review(
        String reviewer,
        ReviewState state,
        String sha,
        String comment
    ) {
        List<ReviewComment> comments = comment == null
            ? List.of()
            : List.of(new ReviewComment(
                "src/main/java/DeploymentValidator.java",
                48,
                comment,
                false
            ));

        return new Review(
            reviewer, state, sha, Instant.now(), comments
        );
    }

    public static void main(String[] args) {
        Repository repository = new Repository(
            "platform/deployment-service", "main"
        );
        BranchProtectionPolicy policy = productionPolicy();
        MergeEligibilityService service = new MergeEligibilityService();

        PullRequest pr = new PullRequest(
            407,
            repository,
            "Validate production deployment manifest",
            "alex",
            "feature/deployment-validation",
            "main",
            "commit-a"
        );

        pr.publish();
        pr.submitReview(review(
            "maya",
            ReviewState.APPROVED,
            "commit-a",
            "The environment allowlist is checked before deployment."
        ));
        pr.submitReview(review(
            "raj",
            ReviewState.APPROVED,
            "commit-a",
            null
        ));

        pr.recordCheck("unit-tests", true);
        pr.recordCheck("security-scan", true);
        pr.setUnresolvedConversations(0);
        pr.synchronizeBase(false);

        try {
            pr.merge(policy, MergeStrategy.SQUASH, service);
            System.out.println("Unexpected successful merge.");
        } catch (MergeRejectedException error) {
            System.out.println("Merge blocked:");
            error.violations().forEach(failure -> System.out.println(" - " + failure));
        }

        // A new commit invalidates checks tied to the earlier changeset and
        // makes previous approvals stale under the configured policy.
        pr.addCommit(new Commit(
            "commit-b",
            "Add deployment target allowlist validation",
            Instant.now()
        ));

        System.out.println(
            "Eligibility after new commit: " +
            service.evaluate(pr, policy, MergeStrategy.SQUASH)
        );

        pr.submitReview(review("maya", ReviewState.APPROVED, "commit-b", null));
        pr.submitReview(review("raj", ReviewState.APPROVED, "commit-b", null));
        pr.recordCheck("unit-tests", true);
        pr.recordCheck("security-scan", true);
        pr.synchronizeBase(false);

        try {
            pr.merge(policy, MergeStrategy.SQUASH, service);
            System.out.println("Pull request merged with squash strategy.");
        } catch (MergeRejectedException error) {
            System.out.println("Merge remains blocked: " + error.getMessage());
        }

        try {
            enforceProtectedBranchOperation("main", "force-push", policy);
        } catch (GovernanceException error) {
            System.out.println("Branch policy rejection: " + error.getMessage());
        }

        try {
            pr.close();
        } catch (InvalidTransitionException error) {
            System.out.println("Invalid state transition: " + error.getMessage());
        }

        try {
            new Repository("malformed", "main");
        } catch (ValidationException error) {
            System.out.println("Invalid repository rejected: " + error.getMessage());
        }

        System.out.println("Supported review states: " + EnumSet.allOf(ReviewState.class));
    }
}
