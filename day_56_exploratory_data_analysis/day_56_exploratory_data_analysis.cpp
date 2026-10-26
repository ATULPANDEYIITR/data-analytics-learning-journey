#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class ReviewStatus {
    Draft,
    Open,
    Approved,
    ChangesRequested,
    Closed,
    Merged
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct Commit {
    std::string id;
    std::string message;
};

struct StatusCheck {
    std::string name;
    bool passed;
    bool required;
};

struct Review {
    std::string reviewer;
    ReviewStatus status;
    bool eligible;
};

struct PullRequest {
    int id;
    std::string sourceBranch;
    std::string targetBranch;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    bool draft;
    bool mergeableByContent;
    bool conversationsResolved;
};

struct BranchProtection {
    std::string branchName;
    int requiredApprovals;
    bool requireStatusChecks;
    bool restrictDirectPush;
    bool restrictForcePush;
    bool restrictDeletion;
    bool requireResolvedConversations;
    bool requireLinearHistory;
    bool allowAdministratorBypass;
    std::set<MergeStrategy> allowedStrategies;
};

class GovernanceError : public std::runtime_error {
public:
    explicit GovernanceError(const std::string& message)
        : std::runtime_error(message) {}
};

class MergeEligibilityEngine {
public:
    static bool hasValidBranches(const PullRequest& pr) {
        return !pr.sourceBranch.empty() &&
               !pr.targetBranch.empty() &&
               pr.sourceBranch != pr.targetBranch;
    }

    static bool hasCommits(const PullRequest& pr) {
        return !pr.commits.empty();
    }

    static int eligibleApprovals(const PullRequest& pr) {
        std::set<std::string> approvingReviewers;

        for (const auto& review : pr.reviews) {
            if (review.eligible &&
                review.status == ReviewStatus::Approved) {
                approvingReviewers.insert(review.reviewer);
            }
        }

        return static_cast<int>(approvingReviewers.size());
    }

    static bool requiredChecksPassed(const PullRequest& pr) {
        for (const auto& check : pr.checks) {
            if (check.required && !check.passed) {
                return false;
            }
        }
        return true;
    }

    static bool allRequiredChecksPresent(const PullRequest& pr) {
        for (const auto& check : pr.checks) {
            if (check.required && check.name.empty()) {
                return false;
            }
        }
        return true;
    }

    static std::vector<std::string> evaluate(
        const PullRequest& pr,
        const BranchProtection& policy,
        MergeStrategy strategy
    ) {
        std::vector<std::string> failures;

        if (!hasValidBranches(pr)) {
            failures.push_back("Source and target branches must be distinct.");
        }

        if (!hasCommits(pr)) {
            failures.push_back("Pull Request contains no commits.");
        }

        if (pr.draft) {
            failures.push_back("Draft Pull Requests cannot be merged.");
        }

        if (!pr.mergeableByContent) {
            failures.push_back("Pull Request has unresolved merge conflicts.");
        }

        if (policy.requireResolvedConversations &&
            !pr.conversationsResolved) {
            failures.push_back("Required review conversations are unresolved.");
        }

        if (eligibleApprovals(pr) < policy.requiredApprovals) {
            failures.push_back(
                "Required eligible approval count has not been reached."
            );
        }

        if (policy.requireStatusChecks &&
            (!allRequiredChecksPresent(pr) || !requiredChecksPassed(pr))) {
            failures.push_back("Required status checks are not passing.");
        }

        if (!policy.allowedStrategies.contains(strategy)) {
            failures.push_back("Selected merge strategy is not permitted.");
        }

        return failures;
    }

    static void merge(
        PullRequest& pr,
        const BranchProtection& policy,
        MergeStrategy strategy
    ) {
        const auto failures = evaluate(pr, policy, strategy);

        if (!failures.empty()) {
            std::string message = "Merge rejected:\n";
            for (const auto& failure : failures) {
                message += " - " + failure + "\n";
            }
            throw GovernanceError(message);
        }

        pr.reviews.erase(
            std::remove_if(
                pr.reviews.begin(),
                pr.reviews.end(),
                [](const Review& review) {
                    return review.status == ReviewStatus::ChangesRequested;
                }
            ),
            pr.reviews.end()
        );

        pr.targetBranch = pr.targetBranch;
        std::cout << "Pull Request #" << pr.id
                  << " merged successfully.\n";
    }
};

void printCorrelation(
    const std::vector<double>& x,
    const std::vector<double>& y
) {
    if (x.size() != y.size() || x.empty()) {
        throw GovernanceError("Correlation vectors must have equal size.");
    }

    const double xMean =
        std::accumulate(x.begin(), x.end(), 0.0) / x.size();
    const double yMean =
        std::accumulate(y.begin(), y.end(), 0.0) / y.size();

    double numerator = 0.0;
    double denominatorX = 0.0;
    double denominatorY = 0.0;

    for (std::size_t i = 0; i < x.size(); ++i) {
        const double dx = x[i] - xMean;
        const double dy = y[i] - yMean;

        numerator += dx * dy;
        denominatorX += dx * dx;
        denominatorY += dy * dy;
    }

    const double denominator = std::sqrt(
        denominatorX * denominatorY
    );

    const double correlation =
        denominator == 0.0 ? 0.0 : numerator / denominator;

    std::cout << std::fixed << std::setprecision(4)
              << "Correlation: " << correlation << "\n";
}

int main() {
    try {
        /*
         * The governance case study models the final decision layer of a
         * repository workflow. Reviews and status checks are separate
         * signals; branch protection converts them into merge constraints.
         */
        BranchProtection policy{
            "main",
            2,
            true,
            true,
            true,
            true,
            true,
            true,
            false,
            {
                MergeStrategy::Squash,
                MergeStrategy::Rebase
            }
        };

        PullRequest pr{
            481,
            "feature/customer-analysis",
            "main",
            {
                {"a17c1", "Add customer segmentation"},
                {"b28d2", "Add anomaly detection"},
                {"c39e3", "Add validation tests"}
            },
            {
                {"reviewer-alice", ReviewStatus::Approved, true},
                {"reviewer-bob", ReviewStatus::Approved, true},
                {"external-user", ReviewStatus::Approved, false}
            },
            {
                {"unit-tests", true, true},
                {"security-scan", true, true},
                {"static-analysis", true, true}
            },
            false,
            true,
            true
        };

        auto failures = MergeEligibilityEngine::evaluate(
            pr,
            policy,
            MergeStrategy::Squash
        );

        if (failures.empty()) {
            std::cout << "Pull Request is merge eligible.\n";
            MergeEligibilityEngine::merge(
                pr,
                policy,
                MergeStrategy::Squash
            );
        } else {
            std::cout << "Pull Request is not merge eligible.\n";
            for (const auto& failure : failures) {
                std::cout << " - " << failure << "\n";
            }
        }

        /*
         * A small analytical calculation demonstrates that correlation is
         * descriptive evidence rather than proof of causation.
         */
        printCorrelation(
            {42000, 58000, 76000, 91000, 51000, 67000},
            {280, 450, 680, 820, 390, 540}
        );

        /*
         * Failure scenario: an unresolved required check must block merging.
         */
        PullRequest failingPr = pr;
        failingPr.id = 482;
        failingPr.checks[1].passed = false;

        const auto blocked = MergeEligibilityEngine::evaluate(
            failingPr,
            policy,
            MergeStrategy::Squash
        );

        if (blocked.empty()) {
            throw GovernanceError(
                "Expected failing status check to block the merge."
            );
        }

        std::cout << "Failure-path validation passed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
