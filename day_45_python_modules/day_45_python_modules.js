#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository Dependency Governance Engine
 *
 * Case study:
 * A development platform maintains several Python repositories. Each
 * repository declares a Python runtime and third-party dependencies. Before
 * a build can proceed, a governance service evaluates dependency constraints,
 * detects conflicts, records diagnostic information, and determines whether
 * an environment is acceptable.
 *
 * The implementation focuses on dependency-management mechanics from a C++
 * systems perspective rather than reproducing a Python import tutorial.
 */

struct Version {
    int major{};
    int minor{};
    int patch{};

    static Version parse(const std::string& text) {
        static const std::regex pattern(R"(^(\d+)\.(\d+)(?:\.(\d+))?$)");
        std::smatch match;

        if (!std::regex_match(text, match, pattern)) {
            throw std::invalid_argument("Invalid semantic version: " + text);
        }

        return {
            std::stoi(match[1]),
            std::stoi(match[2]),
            match[3].matched ? std::stoi(match[3]) : 0
        };
    }

    std::string str() const {
        std::ostringstream output;
        output << major << '.' << minor << '.' << patch;
        return output.str();
    }

    bool operator<(const Version& other) const {
        if (major != other.major) return major < other.major;
        if (minor != other.minor) return minor < other.minor;
        return patch < other.patch;
    }

    bool operator==(const Version& other) const {
        return major == other.major &&
               minor == other.minor &&
               patch == other.patch;
    }
};

enum class ConstraintType {
    Minimum,
    Exact,
    MaximumExclusive
};

struct DependencyConstraint {
    std::string package;
    ConstraintType type;
    Version version;
    std::string source;

    bool accepts(const Version& candidate) const {
        switch (type) {
            case ConstraintType::Minimum:
                return !(candidate < version);

            case ConstraintType::Exact:
                return candidate == version;

            case ConstraintType::MaximumExclusive:
                return candidate < version;
        }

        return false;
    }
};

struct PackageRequirement {
    std::string package;
    std::vector<DependencyConstraint> constraints;

    bool accepts(const Version& candidate) const {
        return std::all_of(
            constraints.begin(),
            constraints.end(),
            [&candidate](const DependencyConstraint& constraint) {
                return constraint.accepts(candidate);
            }
        );
    }
};

class DependencyCatalog {
private:
    std::unordered_map<std::string, std::vector<Version>> availableVersions;

public:
    void add(const std::string& package, const std::string& version) {
        availableVersions[package].push_back(Version::parse(version));
    }

    std::optional<Version> resolve(const PackageRequirement& requirement) const {
        const auto iterator = availableVersions.find(requirement.package);

        if (iterator == availableVersions.end()) {
            return std::nullopt;
        }

        std::vector<Version> candidates = iterator->second;

        // Highest compatible version is selected. A production resolver would
        // also account for transitive dependencies, lock files, indexes,
        // pre-release rules, hashes, platform markers, and environment tags.
        std::sort(candidates.begin(), candidates.end());

        for (auto candidate = candidates.rbegin();
             candidate != candidates.rend();
             ++candidate) {
            if (requirement.accepts(*candidate)) {
                return *candidate;
            }
        }

        return std::nullopt;
    }
};

class DependencyResolver {
private:
    const DependencyCatalog& catalog;

public:
    explicit DependencyResolver(const DependencyCatalog& catalog)
        : catalog(catalog) {}

    std::map<std::string, Version> resolve(
        const std::vector<PackageRequirement>& requirements
    ) const {
        std::map<std::string, Version> resolved;

        for (const auto& requirement : requirements) {
            auto version = catalog.resolve(requirement);

            if (!version.has_value()) {
                throw std::runtime_error(
                    "No compatible version found for " + requirement.package
                );
            }

            auto existing = resolved.find(requirement.package);

            if (existing != resolved.end() &&
                !(existing->second == version.value())) {
                throw std::runtime_error(
                    "Internal resolution conflict for " + requirement.package
                );
            }

            resolved[requirement.package] = version.value();
        }

        return resolved;
    }
};

class Environment {
private:
    std::string interpreterVersion;
    std::map<std::string, Version> installedPackages;

public:
    explicit Environment(std::string interpreterVersion)
        : interpreterVersion(std::move(interpreterVersion)) {}

    const std::string& pythonVersion() const {
        return interpreterVersion;
    }

    void install(
        const std::string& package,
        const std::string& version
    ) {
        installedPackages[package] = Version::parse(version);
    }

    bool satisfies(
        const std::vector<PackageRequirement>& requirements
    ) const {
        for (const auto& requirement : requirements) {
            auto installed = installedPackages.find(requirement.package);

            if (installed == installedPackages.end()) {
                return false;
            }

            if (!requirement.accepts(installed->second)) {
                return false;
            }
        }

        return true;
    }

    void print() const {
        std::cout << "Python runtime: " << interpreterVersion << '\n';

        for (const auto& [package, version] : installedPackages) {
            std::cout << "  " << package << " " << version.str() << '\n';
        }
    }
};

struct AuditFinding {
    std::string severity;
    std::string package;
    std::string message;
};

class DependencyAuditor {
public:
    static std::vector<AuditFinding> audit(
        const Environment& environment,
        const std::vector<PackageRequirement>& requirements
    ) {
        std::vector<AuditFinding> findings;

        for (const auto& requirement : requirements) {
            bool found = false;

            /*
             * The Environment intentionally exposes only its acceptance
             * operation. This keeps package-state representation private.
             * A production auditor would normally query a structured
             * inventory service instead of accessing mutable process state.
             */
            if (!environment.satisfies({requirement})) {
                findings.push_back({
                    "ERROR",
                    requirement.package,
                    "Installed version does not satisfy declared constraints."
                });
            } else {
                found = true;
            }

            if (!found) {
                continue;
            }

            findings.push_back({
                "INFO",
                requirement.package,
                "Installed version satisfies declared constraints."
            });
        }

        return findings;
    }
};

void printRequirements(
    const std::vector<PackageRequirement>& requirements
) {
    std::cout << "\nDeclared dependency constraints\n";

    for (const auto& requirement : requirements) {
        std::cout << "  " << requirement.package << '\n';

        for (const auto& constraint : requirement.constraints) {
            std::string operatorText;

            switch (constraint.type) {
                case ConstraintType::Minimum:
                    operatorText = ">=";
                    break;
                case ConstraintType::Exact:
                    operatorText = "==";
                    break;
                case ConstraintType::MaximumExclusive:
                    operatorText = "<";
                    break;
            }

            std::cout
                << "    "
                << operatorText
                << constraint.version.str()
                << " from "
                << constraint.source
                << '\n';
        }
    }
}

void demonstrateConflictDetection(const DependencyCatalog& catalog) {
    std::cout << "\nConstraint conflict case\n";

    PackageRequirement applicationA{
        "httpx",
        {
            {
                "httpx",
                ConstraintType::Minimum,
                Version::parse("0.27.0"),
                "service-a"
            },
            {
                "httpx",
                ConstraintType::MaximumExclusive,
                Version::parse("1.0.0"),
                "service-a"
            }
        }
    };

    PackageRequirement applicationB{
        "httpx",
        {
            {
                "httpx",
                ConstraintType::Exact,
                Version::parse("0.26.0"),
                "legacy-service"
            }
        }
    };

    DependencyResolver resolver(catalog);

    try {
        auto first = resolver.resolve({applicationA});
        std::cout
            << "Service A resolved httpx "
            << first.at("httpx").str()
            << '\n';

        resolver.resolve({applicationA, applicationB});
        std::cout << "Unexpected compatible resolution.\n";
    } catch (const std::exception& error) {
        std::cout
            << "Resolution failure: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        std::cout << "=== Repository Dependency Governance Engine ===\n";

        DependencyCatalog catalog;

        catalog.add("httpx", "0.26.0");
        catalog.add("httpx", "0.27.2");
        catalog.add("httpx", "0.28.1");
        catalog.add("httpx", "1.0.0");

        catalog.add("pydantic", "2.4.2");
        catalog.add("pydantic", "2.9.2");
        catalog.add("pydantic", "3.0.0");

        std::vector<PackageRequirement> requirements{
            {
                "httpx",
                {
                    {
                        "httpx",
                        ConstraintType::Minimum,
                        Version::parse("0.27.0"),
                        "repository-a requirements"
                    },
                    {
                        "httpx",
                        ConstraintType::MaximumExclusive,
                        Version::parse("1.0.0"),
                        "repository-a requirements"
                    }
                }
            },
            {
                "pydantic",
                {
                    {
                        "pydantic",
                        ConstraintType::Minimum,
                        Version::parse("2.0.0"),
                        "repository-a requirements"
                    },
                    {
                        "pydantic",
                        ConstraintType::MaximumExclusive,
                        Version::parse("3.0.0"),
                        "repository-a requirements"
                    }
                }
            }
        };

        printRequirements(requirements);

        DependencyResolver resolver(catalog);
        auto resolved = resolver.resolve(requirements);

        std::cout << "\nResolved environment\n";

        for (const auto& [package, version] : resolved) {
            std::cout
                << "  "
                << package
                << " -> "
                << version.str()
                << '\n';
        }

        Environment healthyEnvironment("3.13.0");

        for (const auto& [package, version] : resolved) {
            healthyEnvironment.install(package, version.str());
        }

        std::cout << "\nHealthy environment\n";
        healthyEnvironment.print();

        std::cout
            << "Environment satisfies requirements: "
            << std::boolalpha
            << healthyEnvironment.satisfies(requirements)
            << '\n';

        Environment brokenEnvironment("3.13.0");
        brokenEnvironment.install("httpx", "0.26.0");
        brokenEnvironment.install("pydantic", "2.9.2");

        std::cout << "\nBroken environment\n";
        brokenEnvironment.print();

        auto findings = DependencyAuditor::audit(
            brokenEnvironment,
            requirements
        );

        std::cout << "\nAudit findings\n";

        for (const auto& finding : findings) {
            std::cout
                << '['
                << finding.severity
                << "] "
                << finding.package
                << ": "
                << finding.message
                << '\n';
        }

        demonstrateConflictDetection(catalog);

        /*
         * Dependency managers must distinguish a package's import name from
         * its distribution name. The resolver works with distribution-style
         * names and versions; Python's import system operates on importable
         * module/package names. They often match, but they are not guaranteed
         * to be identical.
         */
        std::cout
            << "\nArchitecture note: package distribution metadata and "
               "Python import namespaces are related but distinct concerns.\n";

        std::cout
            << "Complexity: selecting the highest compatible version requires "
               "sorting available versions, O(V log V) for V candidates.\n";

        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
