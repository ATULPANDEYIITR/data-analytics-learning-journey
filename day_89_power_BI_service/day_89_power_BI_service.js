"use strict";

/*
 * Power BI Service workflow and policy engine.
 * Node.js 18+.
 *
 * Models workspace events, artifact publication, item permissions,
 * semantic-model Build access, refresh orchestration and auditing.
 *
 * This is an independent service simulation, not a Power BI API client.
 */

const { randomUUID } = require("node:crypto");
const { EventEmitter } = require("node:events");

class ServiceError extends Error {}
class ValidationError extends ServiceError {}
class AuthorizationError extends ServiceError {}
class NotFoundError extends ServiceError {}
class ConflictError extends ServiceError {}

const Role = Object.freeze({
    ADMIN: "Admin",
    MEMBER: "Member",
    CONTRIBUTOR: "Contributor",
    VIEWER: "Viewer"
});

const ArtifactType = Object.freeze({
    REPORT: "Report",
    DASHBOARD: "Dashboard",
    SEMANTIC_MODEL: "SemanticModel"
});

const RefreshState = Object.freeze({
    QUEUED: "Queued",
    RUNNING: "Running",
    COMPLETED: "Completed",
    FAILED: "Failed"
});

const Permission = Object.freeze({
    VIEW: "View",
    BUILD: "Build",
    WRITE: "Write",
    RESHARE: "Reshare"
});

const ROLE_PERMISSIONS = Object.freeze({
    Admin: new Set(Object.values(Permission)),
    Member: new Set(Object.values(Permission)),
    Contributor: new Set([Permission.VIEW, Permission.WRITE]),
    Viewer: new Set([Permission.VIEW])
});

function validateName(value, label) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new ValidationError(`${label} cannot be empty`);
    }

    if (value.trim().length > 120) {
        throw new ValidationError(`${label} exceeds 120 characters`);
    }

    return value.trim();
}

function assertEnum(value, enumObject, label) {
    if (!Object.values(enumObject).includes(value)) {
        throw new ValidationError(`Invalid ${label}: ${value}`);
    }
}

function createId() {
    return randomUUID();
}

class EventBus extends EventEmitter {
    emitSafely(event, payload) {
        for (const listener of this.listeners(event)) {
            try {
                listener(payload);
            } catch (error) {
                console.error(`Listener failure for ${event}:`, error.message);
            }
        }
    }
}

class AuditLog {
    #events = [];

    append(actorId, action, resourceId, details = {}) {
        const event = Object.freeze({
            eventId: createId(),
            actorId,
            action,
            resourceId,
            details: structuredClone(details),
            timestamp: new Date().toISOString()
        });

        this.#events.push(event);
        return event;
    }

    query(filter = {}) {
        return this.#events.filter(event => {
            return (!filter.actorId || event.actorId === filter.actorId)
                && (!filter.action || event.action === filter.action)
                && (!filter.resourceId || event.resourceId === filter.resourceId);
        });
    }

    get size() {
        return this.#events.length;
    }
}

class SemanticModel {
    constructor({
        id = createId(),
        name,
        ownerId,
        tables,
        source,
        gatewayRequired = false,
        gatewayConfigured = false,
        credentialsConfigured = false,
        refreshEnabled = true
    }) {
        this.id = id;
        this.name = validateName(name, "Semantic model name");
        this.ownerId = ownerId;
        this.tables = new Set(tables);
        this.source = validateName(source, "Data source");
        this.gatewayRequired = gatewayRequired;
        this.gatewayConfigured = gatewayConfigured;
        this.credentialsConfigured = credentialsConfigured;
        this.refreshEnabled = refreshEnabled;
        this.lastRefresh = null;
        this.lastRefreshState = null;
        this.refreshJobs = new Map();

        if (this.tables.size === 0) {
            throw new ValidationError("Semantic model must contain tables");
        }

        for (const table of this.tables) {
            validateName(table, "Table name");
        }
    }

    validateForRefresh() {
        if (this.gatewayRequired && !this.gatewayConfigured) {
            throw new ValidationError("On-premises gateway unavailable");
        }

        if (!this.credentialsConfigured) {
            throw new ValidationError("Data source credentials missing");
        }

        if (!this.refreshEnabled) {
            throw new ConflictError("Scheduled refresh is disabled");
        }
    }
}

class Workspace {
    constructor(name, ownerId, capacity = "Shared") {
        this.id = createId();
        this.name = validateName(name, "Workspace name");
        this.ownerId = ownerId;
        this.capacity = capacity;
        this.members = new Map();
        this.models = new Map();
        this.artifacts = new Map();
        this.shares = new Map();
        this.refreshJobs = new Map();
        this.audit = new AuditLog();
        this.members.set(ownerId, {
            userId: ownerId,
            role: Role.ADMIN,
            joinedAt: new Date()
        });
    }

    addMember(actorId, userId, role) {
        this.assertRole(actorId, [Role.ADMIN, Role.MEMBER]);
        assertEnum(role, Role, "workspace role");

        if (this.members.has(userId)) {
            throw new ConflictError("Member already exists");
        }

        this.members.set(userId, {
            userId,
            role,
            joinedAt: new Date()
        });

        this.audit.append(actorId, "MEMBER_ADDED", userId, { role });
    }

    assertRole(userId, allowedRoles) {
        const member = this.members.get(userId);

        if (!member) {
            throw new AuthorizationError("Workspace membership required");
        }

        if (!allowedRoles.includes(member.role)) {
            throw new AuthorizationError(
                `Role ${member.role} cannot perform this operation`
            );
        }

        return member;
    }

    publishModel(actorId, model) {
        this.assertRole(actorId, [
            Role.ADMIN,
            Role.MEMBER,
            Role.CONTRIBUTOR
        ]);

        if (this.models.has(model.id)) {
            throw new ConflictError("Semantic model ID already exists");
        }

        this.models.set(model.id, model);

        this.audit.append(actorId, "MODEL_PUBLISHED", model.id, {
            name: model.name,
            tables: [...model.tables]
        });
    }

    publishReport(actorId, name, modelId) {
        this.assertRole(actorId, [
            Role.ADMIN,
            Role.MEMBER,
            Role.CONTRIBUTOR
        ]);

        if (!this.models.has(modelId)) {
            throw new NotFoundError("Referenced semantic model not found");
        }

        const report = Object.freeze({
            id: createId(),
            name: validateName(name, "Report name"),
            type: ArtifactType.REPORT,
            semanticModelId: modelId,
            ownerId: actorId,
            publishedAt: new Date()
        });

        this.artifacts.set(report.id, report);

        this.audit.append(actorId, "REPORT_PUBLISHED", report.id, {
            modelId
        });

        return report;
    }

    grantPermission(actorId, resourceId, userId, permissions, expiresAt = null) {
        this.assertRole(actorId, [Role.ADMIN, Role.MEMBER]);

        if (!this.models.has(resourceId) && !this.artifacts.has(resourceId)) {
            throw new NotFoundError("Shareable item not found");
        }

        if (!Array.isArray(permissions) || permissions.length === 0) {
            throw new ValidationError("Permissions cannot be empty");
        }

        const uniquePermissions = new Set(permissions);

        for (const permission of uniquePermissions) {
            assertEnum(permission, Permission, "item permission");
        }

        if (uniquePermissions.has(Permission.WRITE)
            && !uniquePermissions.has(Permission.VIEW)) {
            throw new ValidationError("Write requires View");
        }

        if (expiresAt !== null) {
            const expiration = new Date(expiresAt);

            if (Number.isNaN(expiration.getTime())
                || expiration <= new Date()) {
                throw new ValidationError("Invalid permission expiration");
            }
        }

        const key = `${resourceId}:${userId}`;

        this.shares.set(key, Object.freeze({
            resourceId,
            userId,
            permissions: [...uniquePermissions],
            grantedBy: actorId,
            expiresAt: expiresAt ? new Date(expiresAt) : null
        }));

        this.audit.append(actorId, "PERMISSION_GRANTED", resourceId, {
            userId,
            permissions: [...uniquePermissions]
        });
    }

    effectivePermissions(userId, resourceId) {
        const effective = new Set();
        const member = this.members.get(userId);

        if (member) {
            for (const permission of ROLE_PERMISSIONS[member.role]) {
                effective.add(permission);
            }
        }

        const grant = this.shares.get(`${resourceId}:${userId}`);

        if (grant && (!grant.expiresAt || grant.expiresAt > new Date())) {
            for (const permission of grant.permissions) {
                effective.add(permission);
            }
        }

        return effective;
    }

    canBuild(userId, modelId) {
        if (!this.models.has(modelId)) {
            throw new NotFoundError("Semantic model not found");
        }

        return this.effectivePermissions(userId, modelId)
            .has(Permission.BUILD);
    }
}

class RefreshScheduler {
    constructor(workspace, eventBus, concurrencyLimit = 2) {
        this.workspace = workspace;
        this.events = eventBus;
        this.concurrencyLimit = concurrencyLimit;
        this.activeJobs = new Set();
        this.queue = [];
    }

    enqueue(actorId, modelId) {
        this.workspace.assertRole(actorId, [
            Role.ADMIN,
            Role.MEMBER,
            Role.CONTRIBUTOR
        ]);

        const model = this.workspace.models.get(modelId);

        if (!model) {
            throw new NotFoundError("Semantic model not found");
        }

        model.validateForRefresh();

        const existing = [...model.refreshJobs.values()].find(job =>
            [RefreshState.QUEUED, RefreshState.RUNNING].includes(job.state)
        );

        if (existing) {
            throw new ConflictError("Model already has an active refresh");
        }

        const job = {
            id: createId(),
            modelId,
            actorId,
            state: RefreshState.QUEUED,
            createdAt: new Date(),
            startedAt: null,
            completedAt: null,
            error: null
        };

        model.refreshJobs.set(job.id, job);
        this.workspace.refreshJobs.set(job.id, job);
        this.queue.push(job);

        this.workspace.audit.append(actorId, "REFRESH_QUEUED", modelId, {
            refreshId: job.id
        });

        this.events.emitSafely("refresh.queued", job);
        return job;
    }

    async process(job, executor) {
        const model = this.workspace.models.get(job.modelId);

        job.state = RefreshState.RUNNING;
        job.startedAt = new Date();
        this.activeJobs.add(job.id);

        this.events.emitSafely("refresh.started", job);

        try {
            model.validateForRefresh();

            await executor(model);

            job.state = RefreshState.COMPLETED;
            model.lastRefresh = new Date();
            model.lastRefreshState = RefreshState.COMPLETED;

            this.events.emitSafely("refresh.completed", job);
        } catch (error) {
            job.state = RefreshState.FAILED;
            job.error = error.message;
            model.lastRefreshState = RefreshState.FAILED;

            this.events.emitSafely("refresh.failed", job);
        } finally {
            job.completedAt = new Date();
            this.activeJobs.delete(job.id);

            this.workspace.audit.append(
                job.actorId,
                "REFRESH_FINISHED",
                job.modelId,
                {
                    refreshId: job.id,
                    state: job.state,
                    error: job.error
                }
            );
        }

        return job;
    }

    async drain(executor) {
        const workers = [];

        for (let i = 0; i < this.concurrencyLimit; i++) {
            workers.push((async () => {
                while (this.queue.length > 0) {
                    const job = this.queue.shift();
                    if (job.state !== RefreshState.QUEUED) continue;
                    await this.process(job, executor);
                }
            })());
        }

        await Promise.all(workers);
    }
}

class PowerBIService {
    constructor() {
        this.users = new Map();
        this.workspaces = new Map();
        this.events = new EventBus();
    }

    registerUser(email) {
        const normalized = String(email).trim().toLowerCase();

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized)) {
            throw new ValidationError("Invalid email");
        }

        if ([...this.users.values()].some(u => u.email === normalized)) {
            throw new ConflictError("User already registered");
        }

        const user = Object.freeze({
            id: createId(),
            email: normalized
        });

        this.users.set(user.id, user);
        return user;
    }

    createWorkspace(name, ownerId, capacity = "Shared") {
        if (!this.users.has(ownerId)) {
            throw new NotFoundError("Workspace owner not found");
        }

        if (!["Shared", "Premium", "Fabric"].includes(capacity)) {
            throw new ValidationError("Unsupported capacity");
        }

        const workspace = new Workspace(name, ownerId, capacity);
        this.workspaces.set(workspace.id, workspace);

        workspace.audit.append(
            ownerId,
            "WORKSPACE_CREATED",
            workspace.id,
            { capacity }
        );

        this.events.emitSafely("workspace.created", workspace);
        return workspace;
    }

    getWorkspace(id) {
        const workspace = this.workspaces.get(id);

        if (!workspace) {
            throw new NotFoundError("Workspace not found");
        }

        return workspace;
    }
}

async function main() {
    const service = new PowerBIService();

    service.events.on("refresh.completed", job => {
        console.log(`Refresh completed: ${job.id}`);
    });

    service.events.on("refresh.failed", job => {
        console.error(`Refresh failed: ${job.error}`);
    });

    const admin = service.registerUser("admin@enterprise.example");
    const analyst = service.registerUser("analyst@enterprise.example");
    const executive = service.registerUser("executive@enterprise.example");

    const workspace = service.createWorkspace(
        "Enterprise Analytics",
        admin.id,
        "Premium"
    );

    workspace.addMember(admin.id, analyst.id, Role.CONTRIBUTOR);
    workspace.addMember(admin.id, executive.id, Role.VIEWER);

    const model = new SemanticModel({
        name: "Sales Semantic Model",
        ownerId: analyst.id,
        tables: ["FactSales", "DimCustomer", "DimProduct"],
        source: "Enterprise SQL Server",
        gatewayRequired: true,
        gatewayConfigured: true,
        credentialsConfigured: true
    });

    workspace.publishModel(analyst.id, model);

    const report = workspace.publishReport(
        analyst.id,
        "Executive Sales Report",
        model.id
    );

    workspace.grantPermission(
        admin.id,
        model.id,
        executive.id,
        [Permission.VIEW, Permission.BUILD],
        new Date(Date.now() + 30 * 86400000)
    );

    console.log("Report:", report.name);
    console.log("Executive can build:", workspace.canBuild(
        executive.id,
        model.id
    ));

    const scheduler = new RefreshScheduler(workspace, service.events, 2);

    scheduler.enqueue(analyst.id, model.id);

    await scheduler.drain(async currentModel => {
        // Simulate asynchronous data-source processing.
        await new Promise(resolve => setTimeout(resolve, 100));

        if (currentModel.tables.size < 1) {
            throw new ValidationError("No source tables available");
        }
    });

    console.log("\nRefresh jobs:");

    for (const job of workspace.refreshJobs.values()) {
        console.log({
            id: job.id,
            state: job.state,
            durationMs: job.completedAt - job.startedAt
        });
    }

    console.log("\nAudit events:", workspace.audit.size);

    console.log("\nPermission failure test:");

    try {
        workspace.publishReport(
            executive.id,
            "Unauthorized Report",
            model.id
        );
    } catch (error) {
        console.log(error.name + ":", error.message);
    }

    console.log("\nMissing gateway failure test:");

    const brokenModel = new SemanticModel({
        name: "Unconfigured Model",
        ownerId: analyst.id,
        tables: ["FactSales"],
        source: "On-premises SQL Server",
        gatewayRequired: true,
        gatewayConfigured: false,
        credentialsConfigured: true
    });

    try {
        workspace.publishModel(analyst.id, brokenModel);
        scheduler.enqueue(analyst.id, brokenModel.id);
    } catch (error) {
        console.log(error.name + ":", error.message);
    }
}

main().catch(error => {
    console.error("Application failure:", error);
    process.exitCode = 1;
});
