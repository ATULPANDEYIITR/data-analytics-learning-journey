#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository Automation Function Engine
 *
 * Case study:
 * A repository platform evaluates proposed changes before allowing a merge.
 * The program uses functions as policies, callbacks, predicates, and
 * transformations. It models validation, review eligibility, status checks,
 * approval counting, and final merge decisions.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic repository_functions.cpp -o repository_functions
 */

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string discussion;
    bool eligible;
};

struct StatusCheck {
    std::string name;
    CheckState state;
};

struct PullRequest {
    int id;
    std::string title;
    std::string sourceBranch;
    std::string targetBranch;
    bool draft;
    bool closed;
    bool sourceUpToDate;
    bool hasConflicts;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
};

struct BranchPolicy {
    std::string branch;
    int requiredApprovals;
    bool requireUpToDate;
    bool requireResolvedDiscussions;
    bool requireLinearHistory;
    bool restrictDirectPushes;
    bool restrictForcePushes;
    bool restrictDeletion;
    bool administratorsMayBypass;
    std::set<std::string> requiredChecks;
};

struct MergeDecision {
    bool eligible;
    std::vector<std::string> reasons;
};

// A validator is a named function that either accepts a value or explains why
// the value violates a domain rule.
using PullRequestValidator = std::function<std::optional<std::string>(
    const PullRequest&
)>;

using ReviewPredicate = std::function<bool(const Review&)>;
using AmountTransform = std::function<double(double)>;

std::string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Commented: return "COMMENTED";
        case ReviewState::Approved: return "APPROVED";
        case ReviewState::ChangesRequested: return "CHANGES_REQUESTED";
        case ReviewState::Dismissed: return "DISMISSED";
    }

    throw std::logic_error("Unknown review state");
}

std::string toString(CheckState state) {
    switch (state) {
        case CheckState::Pending: return "PENDING";
        case CheckState::Passed: return "PASSED";
        case CheckState::Failed: return "FAILED";
    }

    throw std::logic_error("Unknown check state");
}

// This function has a clear contract and rejects malformed Pull Requests before
// policy evaluation begins.
std::optional<std::string> validatePullRequest(const PullRequest& pr) {
    if (pr.id <= 0) {
        return "Pull Request ID must be positive";
    }
    if (pr.title.empty()) {
        return "Pull Request title cannot be empty";
    }
    if (pr.sourceBranch.empty() || pr.targetBranch.empty()) {
        return "Source and target branches are required";
    }
    if (pr.sourceBranch == pr.targetBranch) {
        return "Source and target branches must differ";
    }
    if (pr.closed) {
        return "Closed Pull Requests cannot be merged";
    }

    std::set<std::string> reviewers;
    for (const Review& review : pr.reviews) {
        if (review.reviewer.empty()) {
            return "Review records require a reviewer identity";
        }
        if (!reviewers.insert(review.reviewer).second) {
            return "Duplicate reviewer records are not allowed";
        }
    }

    std::set<std::string> checkNames;
    for (const StatusCheck& check : pr.checks) {
        if (check.name.empty()) {
            return "Status check names cannot be empty";
        }
        if (!checkNames.insert(check.name).second) {
            return "Duplicate status check names are not allowed";
        }
    }

    return std::nullopt;
}

// A function factory captures a policy threshold and returns a predicate.
// The returned predicate can be passed into standard algorithms.
ReviewPredicate eligibleApprovalPredicate() {
    return [](const Review& review) {
        return review.eligible && review.state == ReviewState::Approved;
    };
}

int countEligibleApprovals(
    const std::vector<Review>& reviews,
    const ReviewPredicate& predicate
) {
    return static_cast<int>(std::count_if(
        reviews.begin(),
        reviews.end(),
        predicate
    ));
}

// Return the latest effective state for each reviewer. In a production system,
// reviews need a timestamp or monotonically increasing event sequence. This
// case study treats the last vector entry for each reviewer as the latest.
std::vector<Review> latestReviews(const std::vector<Review>& reviews) {
    std::map<std::string, Review> latest;

    for (const Review& review : reviews) {
        latest[review.reviewer] = review;
    }

    std::vector<Review> result;
    result.reserve(latest.size());

    for (const auto& entry : latest) {
        result.push_back(entry.second);
    }

    return result;
}

// The policy engine is a higher-order design: independent checks are stored
// as functions so the merge evaluator can apply a consistent pipeline.
std::vector<PullRequestValidator> buildPolicyValidators(
    const BranchPolicy& policy
) {
    std::vector<PullRequestValidator> validators;

    validators.emplace_back([](const PullRequest& pr)
        -> std::optional<std::string> {
        if (pr.draft) {
            return "Draft Pull Requests are not mergeable";
        }
        return std::nullopt;
    });

    validators.emplace_back([](const PullRequest& pr)
        -> std::optional<std::string> {
        if (pr.hasConflicts) {
            return "Merge conflicts must be resolved";
        }
        return std::nullopt;
    });

    validators.emplace_back([policy](const PullRequest& pr)
        -> std::optional<std::string> {
        if (policy.requireUpToDate && !pr.sourceUpToDate) {
            return "Source branch must be synchronized with the target";
        }
        return std::nullopt;
    });

    validators.emplace_back([policy](const PullRequest& pr)
        -> std::optional<std::string> {
        const std::vector<Review> effective = latestReviews(pr.reviews);

        const bool changesRequested = std::any_of(
            effective.begin(),
            effective.end(),
            [](const Review& review) {
                return review.state == ReviewState::ChangesRequested
                    && review.eligible;
            }
        );

        if (changesRequested) {
            return "An eligible reviewer has requested changes";
        }

        const int approvals = countEligibleApprovals(
            effective,
            eligibleApprovalPredicate()
        );

        if (approvals < policy.requiredApprovals) {
            return "Insufficient eligible approvals: "
                + std::to_string(approvals) + " of "
                + std::to_string(policy.requiredApprovals);
        }

        return std::nullopt;
    });

    validators.emplace_back([policy](const PullRequest& pr)
        -> std::optional<std::string> {
        std::map<std::string, CheckState> observed;

        for (const StatusCheck& check : pr.checks) {
            observed[check.name] = check.state;
        }

        for (const std::string& required : policy.requiredChecks) {
            const auto found = observed.find(required);

            if (found == observed.end()) {
                return "Required status check is missing: " + required;
            }
            if (found->second != CheckState::Passed) {
                return "Required status check is not passing: "
                    + required + " (" + toString(found->second) + ")";
            }
        }

        return std::nullopt;
    });

    return validators;
}

MergeDecision evaluateMergeEligibility(
    const PullRequest& pr,
    const BranchPolicy& policy
) {
    MergeDecision decision{true, {}};

    const auto invalid = validatePullRequest(pr);
    if (invalid.has_value()) {
        decision.eligible = false;
        decision.reasons.push_back(*invalid);
        return decision;
    }

    if (pr.targetBranch != policy.branch) {
        decision.eligible = false;
        decision.reasons.push_back(
            "Pull Request target does not match the protected branch"
        );
        return decision;
    }

    const std::vector<PullRequestValidator> validators =
        buildPolicyValidators(policy);

    for (const PullRequestValidator& validator : validators) {
        const std::optional<std::string> error = validator(pr);

        if (error.has_value()) {
            decision.eligible = false;
            decision.reasons.push_back(*error);
        }
    }

    return decision;
}

// Lambda functions also allow transformations to be supplied at runtime.
double applyTransformation(double value, const AmountTransform& transform) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument("Input must be finite");
    }

    const double result = transform(value);

    if (!std::isfinite(result)) {
        throw std::domain_error("Transformation produced a non-finite value");
    }

    return result;
}

void printDecision(const PullRequest& pr, const MergeDecision& decision) {
    std::cout << "\nPR #" << pr.id << ": " << pr.title << '\n';
    std::cout << "Target: " << pr.targetBranch << '\n';
    std::cout << "Merge eligible: "
              << (decision.eligible ? "YES" : "NO") << '\n';

    if (!decision.reasons.empty()) {
        std::cout << "Blocking conditions:\n";

        for (const std::string& reason : decision.reasons) {
            std::cout << "  - " << reason << '\n';
        }
    }
}

int main() {
    try {
        const BranchPolicy productionPolicy{
            "main",
            2,
            true,
            true,
            true,
            true,
            true,
            true,
            false,
            {"build", "unit-tests", "security-scan"}
        };

        PullRequest ready{
            418,
            "Validate payment settlement",
            "feature/settlement-validation",
            "main",
            false,
            false,
            true,
            false,
            {
                {"reviewer-ada", ReviewState::Approved,
                 "Settlement boundaries verified", true},
                {"reviewer-lin", ReviewState::Approved,
                 "Failure paths reviewed", true},
                {"reviewer-bot", ReviewState::Approved,
                 "Automated review", false}
            },
            {
                {"build", CheckState::Passed},
                {"unit-tests", CheckState::Passed},
                {"security-scan", CheckState::Passed}
            }
        };

        PullRequest blocked{
            419,
            "Update authorization middleware",
            "feature/auth-middleware",
            "main",
            false,
            false,
            false,
            true,
            {
                {"reviewer-ada", ReviewState::Approved,
                 "Initial inspection complete", true},
                {"reviewer-lin", ReviewState::ChangesRequested,
                 "Token expiry validation is missing", true}
            },
            {
                {"build", CheckState::Passed},
                {"unit-tests", CheckState::Pending}
            }
        };

        const MergeDecision readyDecision =
            evaluateMergeEligibility(ready, productionPolicy);
        const MergeDecision blockedDecision =
            evaluateMergeEligibility(blocked, productionPolicy);

        printDecision(ready, readyDecision);
        printDecision(blocked, blockedDecision);

        std::cout << "\nReview-state inspection\n";

        const std::vector<Review> effective = latestReviews(blocked.reviews);
        for (const Review& review : effective) {
            std::cout << review.reviewer << ": "
                      << toString(review.state) << '\n';
        }

        std::cout << "\nFunction composition\n";

        const AmountTransform normalize =
            [](double amount) { return std::round(amount * 100.0) / 100.0; };

        const double normalized = applyTransformation(145.678, normalize);
        std::cout << "Normalized deployment budget: "
                  << std::fixed << std::setprecision(2)
                  << normalized << '\n';

        // A stateful closure captures a threshold for a policy-specific check.
        const int maximumFilesChanged = 40;
        const auto withinChangeBudget =
            [maximumFilesChanged](int changedFiles) {
                return changedFiles >= 0
                    && changedFiles <= maximumFilesChanged;
            };

        std::cout << "12-file change set accepted: "
                  << (withinChangeBudget(12) ? "YES" : "NO") << '\n';
        std::cout << "75-file change set accepted: "
                  << (withinChangeBudget(75) ? "YES" : "NO") << '\n';

        // Merge eligibility is distinct from merge execution. A real platform
        // must revalidate branch state and policy atomically when merging.
        if (readyDecision.eligible) {
            std::cout << "\nPR #" << ready.id
                      << " is eligible for an authorized merge operation.\n";
        }

        if (!blockedDecision.eligible) {
            std::cout << "PR #" << blocked.id
                      << " remains blocked until its conditions are corrected.\n";
        }

        return readyDecision.eligible && !blockedDecision.eligible ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << "Repository governance error: "
                  << error.what() << '\n';
        return 1;
    }
}
