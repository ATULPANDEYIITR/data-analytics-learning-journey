#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

// Repository governance case study: an inventory service evaluates deployment
// readiness from nested configuration, sets of required checks, ordered
// deployment events, and indexed repository metadata.

struct CheckResult {
    string name;
    bool passed;
    int durationMs;
};

struct Deployment {
    string id;
    string repository;
    string environment;
    vector<CheckResult> checks;
    set<string> regions;
};

struct Repository {
    string name;
    string language;
    size_t stars;
    set<string> topics;
    vector<string> maintainers;
    bool archived;
};

struct DeploymentDecision {
    bool eligible;
    vector<string> blockers;
    int totalDurationMs;
};

class GovernanceEngine {
private:
    vector<Repository> repositories;
    unordered_map<string, size_t> repositoryIndex;
    unordered_map<string, vector<string>> topicIndex;

    static void requireNonEmpty(const string& value, const string& field) {
        if (value.empty()) {
            throw invalid_argument(field + " cannot be empty");
        }
    }

public:
    void addRepository(Repository repository) {
        requireNonEmpty(repository.name, "Repository name");
        requireNonEmpty(repository.language, "Language");

        if (repositoryIndex.count(repository.name)) {
            throw invalid_argument("Duplicate repository: " + repository.name);
        }

        if (repository.maintainers.empty() && !repository.archived) {
            throw invalid_argument(
                "An active repository must have a maintainer"
            );
        }

        const size_t index = repositories.size();

        for (const auto& topic : repository.topics) {
            requireNonEmpty(topic, "Topic");
            topicIndex[topic].push_back(repository.name);
        }

        repositoryIndex.emplace(repository.name, index);
        repositories.push_back(std::move(repository));
    }

    const Repository& findRepository(const string& name) const {
        auto it = repositoryIndex.find(name);

        if (it == repositoryIndex.end()) {
            throw out_of_range("Unknown repository: " + name);
        }

        return repositories[it->second];
    }

    vector<string> findByTopic(const string& topic) const {
        auto it = topicIndex.find(topic);

        if (it == topicIndex.end()) {
            return {};
        }

        vector<string> result = it->second;
        sort(result.begin(), result.end());
        return result;
    }

    DeploymentDecision evaluateDeployment(
        const Deployment& deployment,
        const set<string>& requiredChecks,
        const set<string>& allowedEnvironments
    ) const {
        requireNonEmpty(deployment.id, "Deployment ID");
        requireNonEmpty(deployment.repository, "Repository");
        requireNonEmpty(deployment.environment, "Environment");

        const Repository& repository = findRepository(deployment.repository);
        vector<string> blockers;
        int totalDuration = 0;

        if (repository.archived) {
            blockers.push_back("Repository is archived");
        }

        if (!allowedEnvironments.count(deployment.environment)) {
            blockers.push_back("Environment is not allowed");
        }

        unordered_map<string, bool> results;

        for (const CheckResult& check : deployment.checks) {
            requireNonEmpty(check.name, "Check name");

            if (check.durationMs < 0) {
                throw invalid_argument("Check duration cannot be negative");
            }

            if (results.count(check.name)) {
                blockers.push_back("Duplicate check result: " + check.name);
                continue;
            }

            results.emplace(check.name, check.passed);
            totalDuration += check.durationMs;

            if (!check.passed) {
                blockers.push_back("Failed check: " + check.name);
            }
        }

        for (const string& required : requiredChecks) {
            auto it = results.find(required);

            if (it == results.end()) {
                blockers.push_back("Missing required check: " + required);
            } else if (!it->second) {
                // The failed-check blocker is already recorded above.
            }
        }

        if (deployment.regions.empty()) {
            blockers.push_back("No deployment region specified");
        }

        return {
            blockers.empty(),
            std::move(blockers),
            totalDuration
        };
    }

    void printInventory() const {
        cout << "\nRepository inventory\n";

        for (const Repository& repository : repositories) {
            cout << repository.name
                 << " | " << repository.language
                 << " | stars=" << repository.stars
                 << " | archived=" << boolalpha << repository.archived
                 << " | topics=";

            for (const string& topic : repository.topics) {
                cout << topic << " ";
            }

            cout << "\n";
        }
    }
};

static void printDecision(
    const Deployment& deployment,
    const DeploymentDecision& decision
) {
    cout << "\nDeployment " << deployment.id
         << " for " << deployment.repository << "\n";

    cout << "Eligible: " << boolalpha << decision.eligible << "\n";
    cout << "Check duration: " << decision.totalDurationMs << " ms\n";

    if (decision.blockers.empty()) {
        cout << "All deployment policies satisfied.\n";
        return;
    }

    for (const string& blocker : decision.blockers) {
        cout << "Blocked: " << blocker << "\n";
    }
}

int main() {
    try {
        GovernanceEngine engine;

        engine.addRepository({
            "market-prism",
            "Python",
            320,
            {"finance", "analytics", "api"},
            {"Anika", "Rahul"},
            false
        });

        engine.addRepository({
            "portfolio-ui",
            "JavaScript",
            210,
            {"dashboard", "analytics"},
            {"Meera"},
            false
        });

        engine.addRepository({
            "legacy-reports",
            "Java",
            34,
            {"reporting", "legacy"},
            {"Dev"},
            true
        });

        engine.printInventory();

        cout << "\nRepositories tagged analytics:\n";
        for (const string& name : engine.findByTopic("analytics")) {
            cout << name << "\n";
        }

        const set<string> requiredChecks = {
            "unit-tests",
            "security-scan",
            "integration-tests"
        };

        const set<string> allowedEnvironments = {
            "staging",
            "production"
        };

        Deployment productionRelease{
            "DEP-701",
            "market-prism",
            "production",
            {
                {"unit-tests", true, 420},
                {"security-scan", true, 730},
                {"integration-tests", true, 1200}
            },
            {"ap-south-1", "eu-west-1"}
        };

        Deployment failedRelease{
            "DEP-702",
            "portfolio-ui",
            "production",
            {
                {"unit-tests", true, 300},
                {"security-scan", false, 900}
            },
            {"ap-south-1"}
        };

        Deployment archivedRelease{
            "DEP-703",
            "legacy-reports",
            "production",
            {
                {"unit-tests", true, 200},
                {"security-scan", true, 350},
                {"integration-tests", true, 500}
            },
            {"ap-south-1"}
        };

        printDecision(
            productionRelease,
            engine.evaluateDeployment(
                productionRelease,
                requiredChecks,
                allowedEnvironments
            )
        );

        printDecision(
            failedRelease,
            engine.evaluateDeployment(
                failedRelease,
                requiredChecks,
                allowedEnvironments
            )
        );

        printDecision(
            archivedRelease,
            engine.evaluateDeployment(
                archivedRelease,
                requiredChecks,
                allowedEnvironments
            )
        );

        cout << "\nValidation failure example\n";

        try {
            engine.addRepository({
                "market-prism",
                "Python",
                10,
                {"testing"},
                {"Anika"},
                false
            });
        } catch (const invalid_argument& error) {
            cout << error.what() << "\n";
        }

        cout << "\nUnknown repository example\n";

        try {
            engine.findRepository("unregistered-service");
        } catch (const out_of_range& error) {
            cout << error.what() << "\n";
        }

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
