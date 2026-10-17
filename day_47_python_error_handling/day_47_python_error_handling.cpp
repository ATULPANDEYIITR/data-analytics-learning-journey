#include <algorithm>
#include <exception>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class PullRequestState {
    Draft,
    Open,
    Merged,
    Closed
};

enum class ReviewDecision {
    Commented,
    Approved,
    ChangesRequested
};

std::string to_string(PullRequestState state) {
    switch (state) {
        case PullRequestState::Draft: return "draft";
        case PullRequestState::Open: return "open";
        case PullRequestState::Merged: return "merged";
        case PullRequestState::Closed: return "closed";
    }
    throw std::logic_error("Unknown pull request state.");
}

std::string to_string(ReviewDecision decision) {
    switch (decision) {
        case ReviewDecision::Commented: return "commented";
        case ReviewDecision::Approved: return "approved";
        case ReviewDecision::ChangesRequested: return "changes requested";
    }
    throw std::logic_error("Unknown review decision.");
}

class GovernanceError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class ValidationError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

class TransitionError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

class MergeBlockedError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

struct Review {
    std::string reviewer;
    ReviewDecision decision;
    std::string commit_sha;
    std::vector<std::string> inline_comments;
};

struct PullRequest {
    int number;
    std::string repository;
    std::string title;
    std::string author;
    std::string source_branch;
    std::string target_branch;
    std::string head_sha;
    PullRequestState state = PullRequestState::Draft;
    std::vector<Review> reviews;
    std::map<std::string, bool> checks;
    int unresolved_threads = 0;

    PullRequest(
        int number_,
        std::string repository_,
        std::string title_,
        std::string author_,
        std::string source_,
        std::string target_,
        std::string sha_
    )
        : number(number_),
          repository(std::move(repository_)),
          title(std::move(title_)),
          author(std::move(author_)),
          source_branch(std::move(source_)),
          target_branch(std::move(target_)),
          head_sha(std::move(sha_)) {
        if (number <= 0) {
            throw ValidationError("Pull request number must be positive.");
        }
        if (repository.find('/') == std::string::npos) {
            throw ValidationError("Repository must use owner/repository format.");
        }
        if (title.empty() || author.empty() || head_sha.empty()) {
            throw ValidationError("Title, author, and head SHA are required.");
        }
        if (source_branch.empty() || target_branch.empty() ||
            source_branch == target_branch) {
            throw ValidationError("Source and target branches must differ.");
        }
    }

    void publish() {
        if (state != PullRequestState::Draft) {
            throw TransitionError("Only draft pull requests can be published.");
        }
        state = PullRequestState::Open;
    }

    void add_review(Review review) {
        if (state != PullRequestState::Open) {
            throw TransitionError("Reviews require an open pull request.");
        }
        if (review.reviewer.empty() || review.commit_sha.empty()) {
            throw ValidationError("Review identity and commit SHA are required.");
        }
        if (review.reviewer == author) {
            throw ValidationError("Self-approval is not permitted.");
        }
        for (const auto& comment : review.inline_comments) {
            if (comment.empty()) {
                throw ValidationError("Inline review comments cannot be empty.");
            }
        }
        reviews.push_back(std::move(review));
    }

    void set_check(const std::string& name, bool passed) {
        if (state != PullRequestState::Open) {
            throw TransitionError("Status checks require an open pull request.");
        }
        if (name.empty()) {
            throw ValidationError("Status check name cannot be empty.");
        }
        checks[name] = passed;
    }

    void synchronize(const std::string& new_sha) {
        if (state != PullRequestState::Open) {
            throw TransitionError("Only open pull requests can be synchronized.");
        }
        if (new_sha.empty() || new_sha == head_sha) {
            throw ValidationError("Synchronization requires a different valid SHA.");
        }

        head_sha = new_sha;
        // Check results describe a particular changeset and must be rerun.
        checks.clear();
    }
};

struct BranchPolicy {
    std::size_t required_approvals = 2;
    std::set<std::string> required_checks{"unit-tests", "security-scan"};
    bool require_resolved_threads = true;
    bool dismiss_stale_approvals = true;
    bool prohibit_direct_pushes = true;
    bool prohibit_force_pushes = true;
    bool prohibit_deletion = true;
};

std::set<std::string> eligible_approvals(
    const PullRequest& pr,
    const BranchPolicy& policy
) {
    // The latest meaningful decision from each reviewer determines whether
    // that reviewer currently approves the pull request.
    std::map<std::string, ReviewDecision> latest_decisions;

    for (const auto& review : pr.reviews) {
        if (policy.dismiss_stale_approvals && review.commit_sha != pr.head_sha) {
            continue;
        }
        latest_decisions[review.reviewer] = review.decision;
    }

    std::set<std::string> result;
    for (const auto& [reviewer, decision] : latest_decisions) {
        if (decision == ReviewDecision::Approved) {
            result.insert(reviewer);
        }
    }
    return result;
}

std::vector<std::string> evaluate_merge(
    const PullRequest& pr,
    const BranchPolicy& policy
) {
    std::vector<std::string> violations;

    if (pr.state != PullRequestState::Open) {
        violations.emplace_back("Pull request is not open.");
    }

    const auto approvals = eligible_approvals(pr, policy);
    if (approvals.size() < policy.required_approvals) {
        violations.push_back(
            "Insufficient current approvals: required " +
            std::to_string(policy.required_approvals) + ", found " +
            std::to_string(approvals.size()) + "."
        );
    }

    for (const auto& check : policy.required_checks) {
        const auto it = pr.checks.find(check);
        if (it == pr.checks.end() || !it->second) {
            violations.push_back("Required check missing or failed: " + check + ".");
        }
    }

    if (policy.require_resolved_threads && pr.unresolved_threads != 0) {
        violations.emplace_back("Unresolved review discussions remain.");
    }

    return violations;
}

void merge(PullRequest& pr, const BranchPolicy& policy) {
    const auto violations = evaluate_merge(pr, policy);
    if (!violations.empty()) {
        std::string message = "Merge denied:";
        for (const auto& violation : violations) {
            message += "\n - " + violation;
        }
        throw MergeBlockedError(message);
    }

    pr.state = PullRequestState::Merged;
}

void enforce_branch_operation(
    const std::string& branch,
    const std::string& operation,
    const BranchPolicy& policy
) {
    if (branch.empty()) {
        throw ValidationError("Branch name cannot be empty.");
    }
    if (branch != "main") {
        return;
    }

    bool prohibited = false;
    if (operation == "direct-push") {
        prohibited = policy.prohibit_direct_pushes;
    } else if (operation == "force-push") {
        prohibited = policy.prohibit_force_pushes;
    } else if (operation == "delete") {
        prohibited = policy.prohibit_deletion;
    } else {
        throw ValidationError("Unknown branch operation: " + operation);
    }

    if (prohibited) {
        throw GovernanceError(operation + " is prohibited on protected branch main.");
    }
}

void print_eligibility(const PullRequest& pr, const BranchPolicy& policy) {
    const auto failures = evaluate_merge(pr, policy);
    std::cout << "PR #" << pr.number << " state=" << to_string(pr.state) << '\n';

    if (failures.empty()) {
        std::cout << "Merge eligibility: approved by governance policy\n";
    } else {
        std::cout << "Merge eligibility: blocked\n";
        for (const auto& failure : failures) {
            std::cout << "  " << failure << '\n';
        }
    }
}

void run_case_study() {
    BranchPolicy policy;
    PullRequest pr(
        218,
        "platform/deployment-controller",
        "Reject invalid production deployment manifests",
        "developer-alex",
        "feature/manifest-guard",
        "main",
        "sha-100"
    );

    pr.publish();
    pr.unresolved_threads = 1;

    pr.add_review({
        "reviewer-maya",
        ReviewDecision::Approved,
        "sha-100",
        {"The deployment target is checked against the environment allowlist."}
    });

    pr.add_review({
        "reviewer-raj",
        ReviewDecision::Commented,
        "sha-100",
        {"Add a test for an absent deployment region."}
    });

    pr.set_check("unit-tests", true);
    pr.set_check("security-scan", false);
    print_eligibility(pr, policy);

    std::cout << "\nSynchronizing with the latest changeset...\n";
    pr.synchronize("sha-101");
    pr.unresolved_threads = 0;
    print_eligibility(pr, policy);

    pr.add_review({
        "reviewer-maya",
        ReviewDecision::Approved,
        "sha-101",
        {}
    });
    pr.add_review({
        "reviewer-raj",
        ReviewDecision::Approved,
        "sha-101",
        {}
    });

    pr.set_check("unit-tests", true);
    pr.set_check("security-scan", true);
    print_eligibility(pr, policy);

    merge(pr, policy);
    std::cout << "Merged successfully; state=" << to_string(pr.state) << '\n';

    try {
        enforce_branch_operation("main", "force-push", policy);
    } catch (const GovernanceError& error) {
        std::cout << "Protected branch rejection: " << error.what() << '\n';
    }

    try {
        pr.publish();
    } catch (const TransitionError& error) {
        std::cout << "Invalid lifecycle transition: " << error.what() << '\n';
    }
}

int main() {
    std::cout << "Repository governance case study\n\n";

    try {
        run_case_study();

        // Malformed domain input is rejected before it enters the workflow.
        try {
            PullRequest invalid(
                0, "invalid", "", "", "main", "main", ""
            );
        } catch (const ValidationError& error) {
            std::cout << "\nInput validation: " << error.what() << '\n';
        }
    } catch (const GovernanceError& error) {
        std::cerr << "Governance failure: " << error.what() << '\n';
        return 1;
    } catch (const std::exception& error) {
        // Unexpected standard-library failures are not misreported as
        // expected policy rejections.
        std::cerr << "Unexpected failure: " << error.what() << '\n';
        return 2;
    }

    return 0;
}
