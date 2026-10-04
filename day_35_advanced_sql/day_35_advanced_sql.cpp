#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Advanced SQL CTE case study implemented as a repository-governance query
 * engine.
 *
 * The program does not pretend to execute SQL internally. Instead, it models
 * the relational facts that a PostgreSQL CTE query would consume and builds
 * executable governance decisions from those facts.
 *
 * The C++ perspective focuses on:
 * - immutable domain records where practical
 * - hash/set-based aggregation
 * - recursive graph traversal
 * - explicit policy evaluation
 * - failure isolation
 * - complexity and validation
 *
 * The SQL equivalent of these operations is shown as strings where useful,
 * but the case study itself is a native C++ implementation.
 */

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckStatus {
    Pending,
    Passed,
    Failed,
    Cancelled
};

struct PullRequest {
    int id;
    std::string title;
    PullRequestState state;
    int sourceBranch;
    int targetBranch;
};

struct Review {
    int id;
    int pullRequestId;
    int reviewerId;
    ReviewState state;
    std::string submittedAt;
};

struct StatusCheck {
    int pullRequestId;
    std::string name;
    CheckStatus status;
};

struct ReviewComment {
    int pullRequestId;
    int reviewerId;
    std::string filePath;
    int line;
    bool resolved;
};

struct BranchPolicy {
    int branchId;
    int requiredApprovals;
    bool requireStatusChecks;
    bool restrictDirectPush;
    bool allowForcePush;
    bool allowDeletion;
    bool requireConversationResolution;
    bool requireLinearHistory;
};

struct MergeDecision {
    int pullRequestId;
    bool eligible;
    std::vector<std::string> reasons;
};

std::string toString(PullRequestState state) {
    switch (state) {
        case PullRequestState::Draft:
            return "draft";
        case PullRequestState::Open:
            return "open";
        case PullRequestState::Closed:
            return "closed";
        case PullRequestState::Merged:
            return "merged";
    }
    return "unknown";
}

std::string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Commented:
            return "commented";
        case ReviewState::Approved:
            return "approved";
        case ReviewState::ChangesRequested:
            return "changes_requested";
        case ReviewState::Dismissed:
            return "dismissed";
    }
    return "unknown";
}

std::string toString(CheckStatus status) {
    switch (status) {
        case CheckStatus::Pending:
            return "pending";
        case CheckStatus::Passed:
            return "passed";
        case CheckStatus::Failed:
            return "failed";
        case CheckStatus::Cancelled:
            return "cancelled";
    }
    return "unknown";
}

class RepositoryGovernanceEngine {
private:
    std::unordered_map<int, PullRequest> pullRequests;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    std::vector<ReviewComment> comments;
    std::unordered_map<int, BranchPolicy> policies;

    /*
     * This adjacency map represents the relation that a recursive CTE would
     * traverse. The key is a parent branch and the values are child branches.
     */
    std::unordered_map<int, std::vector<int>> branchGraph;

public:
    void addPullRequest(const PullRequest& pullRequest) {
        if (pullRequests.contains(pullRequest.id)) {
            throw std::invalid_argument("Duplicate Pull Request ID.");
        }

        if (pullRequest.sourceBranch == pullRequest.targetBranch) {
            throw std::invalid_argument(
                "A Pull Request cannot target its own source branch."
            );
        }

        pullRequests.emplace(pullRequest.id, pullRequest);
    }

    void addReview(const Review& review) {
        if (!pullRequests.contains(review.pullRequestId)) {
            throw std::invalid_argument(
                "Review references an unknown Pull Request."
            );
        }

        reviews.push_back(review);
    }

    void addStatusCheck(const StatusCheck& check) {
        if (!pullRequests.contains(check.pullRequestId)) {
            throw std::invalid_argument(
                "Status check references an unknown Pull Request."
            );
        }

        checks.push_back(check);
    }

    void addComment(const ReviewComment& comment) {
        if (!pullRequests.contains(comment.pullRequestId)) {
            throw std::invalid_argument(
                "Comment references an unknown Pull Request."
            );
        }

        if (comment.line <= 0) {
            throw std::invalid_argument(
                "Review comment line number must be positive."
            );
        }

        comments.push_back(comment);
    }

    void setBranchPolicy(const BranchPolicy& policy) {
        if (policy.requiredApprovals < 0) {
            throw std::invalid_argument(
                "Required approvals cannot be negative."
            );
        }

        if (!policy.allowForcePush && policy.requireLinearHistory) {
            /*
             * These flags are not logically contradictory. This validation is
             * intentionally absent because a strict linear-history policy and
             * force-push prohibition are compatible governance choices.
             */
        }

        policies[policy.branchId] = policy;
    }

    void addBranchRelationship(int parent, int child) {
        if (parent == child) {
            throw std::invalid_argument(
                "A branch cannot be its own parent."
            );
        }

        branchGraph[parent].push_back(child);
    }

    /*
     * The latest review per reviewer is analogous to:
     *
     * WITH ranked_reviews AS (
     *   SELECT ...,
     *          ROW_NUMBER() OVER (
     *            PARTITION BY pull_request_id, reviewer_id
     *            ORDER BY submitted_at DESC, review_id DESC
     *          ) AS rank
     *   FROM reviews
     * )
     *
     * This implementation uses a map keyed by PR/reviewer and keeps the
     * greatest review ID as a deterministic proxy for chronological order.
     */
    std::map<std::pair<int, int>, Review> latestReviews() const {
        std::map<std::pair<int, int>, Review> latest;

        for (const Review& review : reviews) {
            const auto key = std::make_pair(
                review.pullRequestId,
                review.reviewerId
            );

            auto found = latest.find(key);

            if (found == latest.end() || review.id > found->second.id) {
                latest[key] = review;
            }
        }

        return latest;
    }

    int activeApprovalCount(int pullRequestId) const {
        const auto latest = latestReviews();
        std::set<int> approvingReviewers;

        for (const auto& [key, review] : latest) {
            if (key.first != pullRequestId) {
                continue;
            }

            if (review.state == ReviewState::Approved) {
                approvingReviewers.insert(review.reviewerId);
            }
        }

        return static_cast<int>(approvingReviewers.size());
    }

    std::vector<std::string> failingChecks(int pullRequestId) const {
        std::vector<std::string> failures;

        for (const StatusCheck& check : checks) {
            if (check.pullRequestId != pullRequestId) {
                continue;
            }

            if (
                check.status == CheckStatus::Failed ||
                check.status == CheckStatus::Cancelled
            ) {
                failures.push_back(check.name);
            }
        }

        return failures;
    }

    int pendingCheckCount(int pullRequestId) const {
        int pending = 0;

        for (const StatusCheck& check : checks) {
            if (
                check.pullRequestId == pullRequestId &&
                check.status == CheckStatus::Pending
            ) {
                ++pending;
            }
        }

        return pending;
    }

    int unresolvedConversationCount(int pullRequestId) const {
        int unresolved = 0;

        for (const ReviewComment& comment : comments) {
            if (
                comment.pullRequestId == pullRequestId &&
                !comment.resolved
            ) {
                ++unresolved;
            }
        }

        return unresolved;
    }

    MergeDecision evaluatePullRequest(int pullRequestId) const {
        const auto found = pullRequests.find(pullRequestId);

        if (found == pullRequests.end()) {
            throw std::out_of_range("Unknown Pull Request.");
        }

        const PullRequest& pr = found->second;
        MergeDecision decision{
            .pullRequestId = pullRequestId,
            .eligible = true,
            .reasons = {}
        };

        if (pr.state != PullRequestState::Open) {
            decision.eligible = false;
            decision.reasons.push_back("Pull Request is not open.");
        }

        const auto policyIt = policies.find(pr.targetBranch);

        if (policyIt == policies.end()) {
            decision.reasons.push_back(
                "Target branch has no configured protection policy."
            );
            return decision;
        }

        const BranchPolicy& policy = policyIt->second;

        const int approvals = activeApprovalCount(pullRequestId);

        if (approvals < policy.requiredApprovals) {
            decision.eligible = false;

            std::ostringstream message;
            message
                << "Required approvals: "
                << policy.requiredApprovals
                << ", active approvals: "
                << approvals
                << ".";
            decision.reasons.push_back(message.str());
        }

        if (policy.requireStatusChecks) {
            const auto failures = failingChecks(pullRequestId);
            const int pending = pendingCheckCount(pullRequestId);

            if (!failures.empty() || pending > 0) {
                decision.eligible = false;

                std::ostringstream message;
                message
                    << "Status checks are not green: "
                    << failures.size()
                    << " failed/cancelled, "
                    << pending
                    << " pending.";
                decision.reasons.push_back(message.str());
            }
        }

        if (policy.requireConversationResolution) {
            const int unresolved = unresolvedConversationCount(pullRequestId);

            if (unresolved > 0) {
                decision.eligible = false;

                std::ostringstream message;
                message
                    << unresolved
                    << " review conversation(s) remain unresolved.";
                decision.reasons.push_back(message.str());
            }
        }

        if (decision.eligible) {
            decision.reasons.push_back(
                "All modeled merge-policy conditions are satisfied."
            );
        }

        return decision;
    }

    /*
     * This is the C++ equivalent of a recursive CTE with cycle detection.
     *
     * SQL shape:
     *
     * WITH RECURSIVE branch_tree AS (
     *   SELECT root ...
     *   UNION ALL
     *   SELECT child ...
     *   FROM branch_tree ...
     *   WHERE child NOT IN path
     * )
     *
     * The unordered_set makes membership testing approximately O(1), while
     * the recursive traversal visits each reachable edge at most once along a
     * particular path.
     */
    std::vector<std::pair<int, int>> traverseBranchTree(int root) const {
        std::vector<std::pair<int, int>> result;
        std::unordered_set<int> visited;

        std::function<void(int, int)> walk =
            [&](int branch, int depth) {
                if (visited.contains(branch)) {
                    return;
                }

                visited.insert(branch);
                result.emplace_back(branch, depth);

                const auto found = branchGraph.find(branch);

                if (found == branchGraph.end()) {
                    return;
                }

                for (int child : found->second) {
                    walk(child, depth + 1);
                }
            };

        walk(root, 0);
        return result;
    }

    void printPullRequestMetrics() const {
        std::map<int, int> reviewCounts;
        std::map<int, int> approvalCounts;
        std::map<int, int> failedChecksByPr;

        for (const Review& review : reviews) {
            ++reviewCounts[review.pullRequestId];
        }

        const auto latest = latestReviews();

        for (const auto& [key, review] : latest) {
            if (review.state == ReviewState::Approved) {
                ++approvalCounts[key.first];
            }
        }

        for (const StatusCheck& check : checks) {
            if (
                check.status == CheckStatus::Failed ||
                check.status == CheckStatus::Cancelled
            ) {
                ++failedChecksByPr[check.pullRequestId];
            }
        }

        std::cout << "\n=== Set-based metrics analogous to a CTE pipeline ===\n";

        for (const auto& [id, pr] : pullRequests) {
            std::cout
                << "PR " << id
                << " | reviews=" << reviewCounts[id]
                << " | active approvals=" << approvalCounts[id]
                << " | failed checks=" << failedChecksByPr[id]
                << '\n';
        }
    }
};

void loadCaseStudy(RepositoryGovernanceEngine& engine) {
    engine.addPullRequest({
        101,
        "Increase payment timeout safely",
        PullRequestState::Open,
        10,
        1
    });

    engine.addPullRequest({
        102,
        "Add fraud risk rules",
        PullRequestState::Open,
        11,
        1
    });

    engine.addPullRequest({
        103,
        "Emergency authentication fix",
        PullRequestState::Open,
        12,
        2
    });

    engine.addReview({
        2001, 101, 2, ReviewState::Approved, "2026-10-03T10:00:00"
    });

    engine.addReview({
        2002, 101, 3, ReviewState::Commented, "2026-10-03T11:00:00"
    });

    engine.addReview({
        2003, 102, 3, ReviewState::ChangesRequested, "2026-10-04T09:00:00"
    });

    engine.addReview({
        2004, 102, 4, ReviewState::Approved, "2026-10-04T10:00:00"
    });

    engine.addReview({
        2005, 103, 1, ReviewState::Approved, "2026-10-04T12:00:00"
    });

    engine.addStatusCheck({
        101, "unit-tests", CheckStatus::Passed
    });

    engine.addStatusCheck({
        101, "integration-tests", CheckStatus::Passed
    });

    engine.addStatusCheck({
        101, "security-scan", CheckStatus::Passed
    });

    engine.addStatusCheck({
        102, "unit-tests", CheckStatus::Passed
    });

    engine.addStatusCheck({
        102, "integration-tests", CheckStatus::Failed
    });

    engine.addStatusCheck({
        102, "security-scan", CheckStatus::Passed
    });

    engine.addStatusCheck({
        103, "unit-tests", CheckStatus::Passed
    });

    engine.addStatusCheck({
        103, "security-scan", CheckStatus::Passed
    });

    engine.addComment({
        101, 3, "retry.py", 88, true
    });

    engine.addComment({
        102, 3, "risk_rules.py", 42, false
    });

    engine.setBranchPolicy({
        1,
        2,
        true,
        true,
        false,
        false,
        true,
        true
    });

    engine.setBranchPolicy({
        2,
        1,
        true,
        true,
        false,
        false,
        true,
        true
    });

    engine.addBranchRelationship(1, 3);
    engine.addBranchRelationship(1, 4);
    engine.addBranchRelationship(4, 5);

    // Deliberate cycle: the recursive traversal must still terminate.
    engine.addBranchRelationship(5, 1);
}

void printDecision(const MergeDecision& decision) {
    std::cout
        << "\nPR "
        << decision.pullRequestId
        << " merge eligibility: "
        << (decision.eligible ? "ELIGIBLE" : "BLOCKED")
        << '\n';

    for (const std::string& reason : decision.reasons) {
        std::cout << "  - " << reason << '\n';
    }
}

void demonstrateInvalidInput(RepositoryGovernanceEngine& engine) {
    std::cout << "\n=== Validation and failure handling ===\n";

    try {
        engine.addPullRequest({
            101,
            "Duplicate",
            PullRequestState::Open,
            99,
            1
        });
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid duplicate: "
            << error.what()
            << '\n';
    }

    try {
        engine.addPullRequest({
            200,
            "Self-targeting",
            PullRequestState::Open,
            5,
            5
        });
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid branch relationship: "
            << error.what()
            << '\n';
    }
}

void demonstrateRecursiveTraversal(
    const RepositoryGovernanceEngine& engine
) {
    std::cout << "\n=== Recursive branch traversal ===\n";

    const auto nodes = engine.traverseBranchTree(1);

    for (const auto& [branch, depth] : nodes) {
        std::cout
            << "branch=" << branch
            << " depth=" << depth
            << '\n';
    }

    std::cout
        << "Cycle protection prevents branch 1 from being traversed "
        << "indefinitely through the 1 -> 4 -> 5 -> 1 relationship.\n";
}

void demonstrateQueryDesign() {
    std::cout << "\n=== PostgreSQL CTE shape represented by the case study ===\n";

    const std::string query = R"SQL(
WITH
open_prs AS (
    SELECT id, target_branch_id
    FROM pull_requests
    WHERE state = 'open'
),
active_approvals AS (
    SELECT pull_request_id, COUNT(DISTINCT reviewer_id) AS approvals
    FROM latest_reviewer_decisions
    WHERE review_state = 'approved'
    GROUP BY pull_request_id
),
check_summary AS (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (WHERE status = 'passed') AS passed_checks,
        COUNT(*) FILTER (
            WHERE status IN ('failed', 'cancelled', 'pending')
        ) AS non_green_checks
    FROM status_checks
    GROUP BY pull_request_id
)
SELECT ...
FROM open_prs
LEFT JOIN active_approvals USING (pull_request_id)
LEFT JOIN check_summary USING (pull_request_id);
)SQL";

    std::cout << query;
}

int main() {
    try {
        RepositoryGovernanceEngine engine;
        loadCaseStudy(engine);

        std::cout
            << "Advanced SQL CTE Case Study: "
            << "C++ Governance Engine\n";

        engine.printPullRequestMetrics();

        printDecision(engine.evaluatePullRequest(101));
        printDecision(engine.evaluatePullRequest(102));
        printDecision(engine.evaluatePullRequest(103));

        demonstrateRecursiveTraversal(engine);
        demonstrateInvalidInput(engine);
        demonstrateQueryDesign();

        std::cout
            << "\n=== Design trade-off ===\n"
            << "A CTE improves SQL statement structure and allows a complex "
            << "relational transformation to be named. It does not automatically "
            << "make a query faster. Recursive CTEs require termination rules "
            << "when graph data can contain cycles.\n";

        std::cout
            << "\n=== Complexity considerations ===\n"
            << "Latest-review aggregation is O(R log R) here because the "
            << "ordered map maintains keys. Hash-based implementations can "
            << "approach O(R) average time. Branch traversal is O(V + E) for "
            << "visited vertices V and edges E.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal case-study error: "
            << error.what()
            << '\n';
        return 1;
    }
}
