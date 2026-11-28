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
#include <vector>

using namespace std;

class GovernanceError : public runtime_error {
public:
    explicit GovernanceError(const string& message)
        : runtime_error(message) {}
};

enum class Role {
    Admin,
    Member,
    Contributor,
    Viewer
};

enum class ArtifactType {
    Report,
    Dashboard,
    SemanticModel
};

enum class RefreshStatus {
    Queued,
    Running,
    Completed,
    Failed
};

enum class ReviewStatus {
    Pending,
    Approved,
    Rejected
};

enum class Permission {
    View,
    Build,
    Write,
    Reshare
};

string toString(Role role) {
    switch (role) {
        case Role::Admin: return "Admin";
        case Role::Member: return "Member";
        case Role::Contributor: return "Contributor";
        case Role::Viewer: return "Viewer";
    }
    throw GovernanceError("Unknown role");
}

string toString(RefreshStatus status) {
    switch (status) {
        case RefreshStatus::Queued: return "Queued";
        case RefreshStatus::Running: return "Running";
        case RefreshStatus::Completed: return "Completed";
        case RefreshStatus::Failed: return "Failed";
    }
    throw GovernanceError("Unknown refresh status");
}

struct User {
    string id;
    string email;
};

struct SemanticModel {
    string id;
    string name;
    string ownerId;
    string source;
    set<string> tables;
    bool gatewayRequired = false;
    bool gatewayConfigured = false;
    bool credentialsConfigured = false;
    bool refreshEnabled = true;
    optional<RefreshStatus> lastRefresh;
};

struct Artifact {
    string id;
    string name;
    ArtifactType type;
    string ownerId;
    optional<string> modelId;
};

struct ShareGrant {
    string userId;
    set<Permission> permissions;
    string resourceId;
};

struct RefreshJob {
    string id;
    string modelId;
    string requestedBy;
    RefreshStatus status = RefreshStatus::Queued;
    string error;
};

struct WorkspacePolicy {
    int requiredBuildApprovals = 0;
    bool requireSuccessfulRefresh = true;
    bool requireCredentials = true;
    bool requireGatewayConfiguration = true;
    bool restrictDirectPublishing = true;
};

struct Workspace {
    string id;
    string name;
    string capacity;
    map<string, Role> members;
    map<string, SemanticModel> models;
    map<string, Artifact> artifacts;
    map<string, RefreshJob> refreshJobs;
    map<string, ShareGrant> grants;
    WorkspacePolicy policy;
};

class PowerBIService {
private:
    map<string, User> users;
    map<string, Workspace> workspaces;
    unsigned long long sequence = 1000;

    string nextId(const string& prefix) {
        return prefix + "-" + to_string(sequence++);
    }

    void requireUser(const string& userId) const {
        if (users.find(userId) == users.end()) {
            throw GovernanceError("User does not exist");
        }
    }

    Workspace& workspace(const string& workspaceId) {
        auto it = workspaces.find(workspaceId);

        if (it == workspaces.end()) {
            throw GovernanceError("Workspace not found");
        }

        return it->second;
    }

    const Workspace& workspace(const string& workspaceId) const {
        auto it = workspaces.find(workspaceId);

        if (it == workspaces.end()) {
            throw GovernanceError("Workspace not found");
        }

        return it->second;
    }

    void requireRole(
        const Workspace& ws,
        const string& userId,
        const set<Role>& allowed
    ) const {
        auto it = ws.members.find(userId);

        if (it == ws.members.end()) {
            throw GovernanceError("Workspace membership required");
        }

        if (!allowed.count(it->second)) {
            throw GovernanceError(
                "Insufficient workspace role: " + toString(it->second)
            );
        }
    }

    void validateModel(const SemanticModel& model) const {
        if (model.name.empty() || model.source.empty()) {
            throw GovernanceError("Model metadata cannot be empty");
        }

        if (model.tables.empty()) {
            throw GovernanceError("Model must contain at least one table");
        }

        for (const auto& table : model.tables) {
            if (table.empty()) {
                throw GovernanceError("Empty table name");
            }
        }

        if (model.gatewayRequired && !model.gatewayConfigured) {
            throw GovernanceError("Required gateway is unavailable");
        }

        if (!model.credentialsConfigured) {
            throw GovernanceError("Data source credentials missing");
        }
    }

public:
    User registerUser(const string& email) {
        if (email.empty() || email.find('@') == string::npos) {
            throw GovernanceError("Invalid email address");
        }

        for (const auto& [id, user] : users) {
            if (user.email == email) {
                throw GovernanceError("Duplicate email");
            }
        }

        User user{nextId("USER"), email};
        users.emplace(user.id, user);
        return user;
    }

    string createWorkspace(
        const string& name,
        const string& ownerId,
        const string& capacity
    ) {
        requireUser(ownerId);

        if (name.empty()) {
            throw GovernanceError("Workspace name cannot be empty");
        }

        if (capacity != "Shared"
            && capacity != "Premium"
            && capacity != "Fabric") {
            throw GovernanceError("Unsupported capacity");
        }

        for (const auto& [id, ws] : workspaces) {
            if (ws.name == name) {
                throw GovernanceError("Duplicate workspace name");
            }
        }

        Workspace ws;
        ws.id = nextId("WS");
        ws.name = name;
        ws.capacity = capacity;
        ws.members[ownerId] = Role::Admin;

        string id = ws.id;
        workspaces.emplace(id, move(ws));

        return id;
    }

    void addMember(
        const string& workspaceId,
        const string& actorId,
        const string& userId,
        Role role
    ) {
        Workspace& ws = workspace(workspaceId);
        requireUser(userId);

        requireRole(
            ws,
            actorId,
            {Role::Admin, Role::Member}
        );

        if (ws.members.count(userId)) {
            throw GovernanceError("User is already a member");
        }

        ws.members[userId] = role;
    }

    string publishSemanticModel(
        const string& workspaceId,
        const string& actorId,
        const string& name,
        const string& source,
        const set<string>& tables,
        bool gatewayRequired,
        bool gatewayConfigured,
        bool credentialsConfigured
    ) {
        Workspace& ws = workspace(workspaceId);

        requireRole(
            ws,
            actorId,
            {Role::Admin, Role::Member, Role::Contributor}
        );

        SemanticModel model;
        model.id = nextId("MODEL");
        model.name = name;
        model.ownerId = actorId;
        model.source = source;
        model.tables = tables;
        model.gatewayRequired = gatewayRequired;
        model.gatewayConfigured = gatewayConfigured;
        model.credentialsConfigured = credentialsConfigured;

        validateModel(model);

        string id = model.id;
        ws.models.emplace(id, move(model));

        return id;
    }

    string publishReport(
        const string& workspaceId,
        const string& actorId,
        const string& name,
        const string& modelId
    ) {
        Workspace& ws = workspace(workspaceId);

        requireRole(
            ws,
            actorId,
            {Role::Admin, Role::Member, Role::Contributor}
        );

        if (!ws.models.count(modelId)) {
            throw GovernanceError("Referenced semantic model not found");
        }

        Artifact report{
            nextId("REPORT"),
            name,
            ArtifactType::Report,
            actorId,
            modelId
        };

        string id = report.id;
        ws.artifacts.emplace(id, move(report));

        return id;
    }

    void grantPermission(
        const string& workspaceId,
        const string& actorId,
        const string& resourceId,
        const string& userId,
        const set<Permission>& permissions
    ) {
        Workspace& ws = workspace(workspaceId);

        requireRole(
            ws,
            actorId,
            {Role::Admin, Role::Member}
        );

        requireUser(userId);

        if (!ws.models.count(resourceId)
            && !ws.artifacts.count(resourceId)) {
            throw GovernanceError("Resource not found");
        }

        if (permissions.empty()) {
            throw GovernanceError("At least one permission is required");
        }

        if (permissions.count(Permission::Write)
            && !permissions.count(Permission::View)) {
            throw GovernanceError("Write requires View permission");
        }

        ShareGrant grant{userId, permissions, resourceId};

        ws.grants[resourceId + ":" + userId] = move(grant);
    }

    set<Permission> effectivePermissions(
        const string& workspaceId,
        const string& userId,
        const string& resourceId
    ) const {
        const Workspace& ws = workspace(workspaceId);

        set<Permission> result;
        auto member = ws.members.find(userId);

        if (member != ws.members.end()) {
            switch (member->second) {
                case Role::Admin:
                case Role::Member:
                    result = {
                        Permission::View,
                        Permission::Build,
                        Permission::Write,
                        Permission::Reshare
                    };
                    break;

                case Role::Contributor:
                    result = {
                        Permission::View,
                        Permission::Write
                    };
                    break;

                case Role::Viewer:
                    result = {Permission::View};
                    break;
            }
        }

        auto grant = ws.grants.find(resourceId + ":" + userId);

        if (grant != ws.grants.end()) {
            result.insert(
                grant->second.permissions.begin(),
                grant->second.permissions.end()
            );
        }

        return result;
    }

    string queueRefresh(
        const string& workspaceId,
        const string& actorId,
        const string& modelId
    ) {
        Workspace& ws = workspace(workspaceId);

        requireRole(
            ws,
            actorId,
            {Role::Admin, Role::Member, Role::Contributor}
        );

        auto model = ws.models.find(modelId);

        if (model == ws.models.end()) {
            throw GovernanceError("Semantic model not found");
        }

        if (!model->second.refreshEnabled) {
            throw GovernanceError("Refresh is disabled");
        }

        validateModel(model->second);

        for (const auto& [id, job] : ws.refreshJobs) {
            if (job.modelId == modelId
                && (job.status == RefreshStatus::Queued
                    || job.status == RefreshStatus::Running)) {
                throw GovernanceError("Refresh already active");
            }
        }

        RefreshJob job;
        job.id = nextId("REFRESH");
        job.modelId = modelId;
        job.requestedBy = actorId;

        string id = job.id;
        ws.refreshJobs.emplace(id, move(job));

        return id;
    }

    void executeRefresh(
        const string& workspaceId,
        const string& refreshId,
        bool simulateFailure = false
    ) {
        Workspace& ws = workspace(workspaceId);

        auto job = ws.refreshJobs.find(refreshId);

        if (job == ws.refreshJobs.end()) {
            throw GovernanceError("Refresh job not found");
        }

        if (job->second.status != RefreshStatus::Queued) {
            throw GovernanceError("Refresh is not queued");
        }

        auto model = ws.models.find(job->second.modelId);

        if (model == ws.models.end()) {
            throw GovernanceError("Associated model was deleted");
        }

        job->second.status = RefreshStatus::Running;

        try {
            validateModel(model->second);

            if (simulateFailure) {
                throw GovernanceError("Simulated source timeout");
            }

            job->second.status = RefreshStatus::Completed;
            model->second.lastRefresh = RefreshStatus::Completed;

        } catch (const exception& ex) {
            job->second.status = RefreshStatus::Failed;
            job->second.error = ex.what();
            model->second.lastRefresh = RefreshStatus::Failed;
        }
    }

    bool canPublishReport(
        const string& workspaceId,
        const string& userId,
        const string& modelId
    ) const {
        const Workspace& ws = workspace(workspaceId);

        const auto permissions = effectivePermissions(
            workspaceId,
            userId,
            modelId
        );

        return permissions.count(Permission::Write) > 0
            && ws.models.count(modelId) > 0;
    }

    void printReport(const string& workspaceId) const {
        const Workspace& ws = workspace(workspaceId);

        cout << "\nWORKSPACE GOVERNANCE REPORT\n";
        cout << "Workspace: " << ws.name << '\n';
        cout << "Capacity: " << ws.capacity << '\n';
        cout << "Members: " << ws.members.size() << '\n';
        cout << "Semantic models: " << ws.models.size() << '\n';
        cout << "Artifacts: " << ws.artifacts.size() << '\n';

        cout << "\nREFRESH JOBS\n";

        for (const auto& [id, job] : ws.refreshJobs) {
            cout << id << " | "
                 << toString(job.status);

            if (!job.error.empty()) {
                cout << " | " << job.error;
            }

            cout << '\n';
        }
    }
};

int main() {
    try {
        PowerBIService service;

        User admin = service.registerUser("admin@enterprise.example");
        User analyst = service.registerUser("analyst@enterprise.example");
        User executive = service.registerUser("executive@enterprise.example");

        string workspaceId = service.createWorkspace(
            "Enterprise Sales Analytics",
            admin.id,
            "Premium"
        );

        service.addMember(
            workspaceId,
            admin.id,
            analyst.id,
            Role::Contributor
        );

        service.addMember(
            workspaceId,
            admin.id,
            executive.id,
            Role::Viewer
        );

        string modelId = service.publishSemanticModel(
            workspaceId,
            analyst.id,
            "Sales Semantic Model",
            "Enterprise SQL Server",
            {"FactSales", "DimCustomer", "DimProduct", "DimDate"},
            true,
            true,
            true
        );

        string reportId = service.publishReport(
            workspaceId,
            analyst.id,
            "Executive Sales Report",
            modelId
        );

        cout << "Published report: " << reportId << '\n';

        service.grantPermission(
            workspaceId,
            admin.id,
            modelId,
            executive.id,
            {Permission::View, Permission::Build}
        );

        auto permissions = service.effectivePermissions(
            workspaceId,
            executive.id,
            modelId
        );

        cout << "\nExecutive permissions:\n";

        for (Permission permission : permissions) {
            switch (permission) {
                case Permission::View: cout << "View\n"; break;
                case Permission::Build: cout << "Build\n"; break;
                case Permission::Write: cout << "Write\n"; break;
                case Permission::Reshare: cout << "Reshare\n"; break;
            }
        }

        string refreshId = service.queueRefresh(
            workspaceId,
            analyst.id,
            modelId
        );

        service.executeRefresh(workspaceId, refreshId);

        cout << "\nSuccessful refresh: " << refreshId << '\n';

        string failedRefresh = service.queueRefresh(
            workspaceId,
            analyst.id,
            modelId
        );

        service.executeRefresh(
            workspaceId,
            failedRefresh,
            true
        );

        service.printReport(workspaceId);

        cout << "\nPermission validation:\n";

        try {
            service.publishReport(
                workspaceId,
                executive.id,
                "Unauthorized Report",
                modelId
            );
        } catch (const GovernanceError& ex) {
            cout << "Rejected: " << ex.what() << '\n';
        }

        cout << "\nGateway validation:\n";

        try {
            service.publishSemanticModel(
                workspaceId,
                analyst.id,
                "Broken Model",
                "On-premises Database",
                {"FactSales"},
                true,
                false,
                true
            );
        } catch (const GovernanceError& ex) {
            cout << "Rejected: " << ex.what() << '\n';
        }

    } catch (const exception& ex) {
        cerr << "Application error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
