import java.time.Instant;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * Enterprise Power BI Service governance and operational model.
 *
 * Java 17.
 *
 * Covers:
 * - Workspaces and workspace membership
 * - Semantic models and reports
 * - Publication workflows
 * - Item-level permissions
 * - Build permission
 * - Refresh orchestration
 * - Audit events
 * - Validation and state transitions
 *
 * This program models service behavior without requiring an external API.
 */
public class PowerBIEnterprise {

    enum WorkspaceRole {
        ADMIN,
        MEMBER,
        CONTRIBUTOR,
        VIEWER
    }

    enum Permission {
        VIEW,
        BUILD,
        WRITE,
        RESHARE
    }

    enum ArtifactType {
        REPORT,
        DASHBOARD,
        SEMANTIC_MODEL
    }

    enum RefreshStatus {
        QUEUED,
        RUNNING,
        COMPLETED,
        FAILED,
        CANCELLED
    }

    enum CapacityType {
        SHARED,
        PREMIUM,
        FABRIC
    }

    static class ServiceException extends RuntimeException {
        ServiceException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends ServiceException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    static class ValidationException extends ServiceException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class ConflictException extends ServiceException {
        ConflictException(String message) {
            super(message);
        }
    }

    static class NotFoundException extends ServiceException {
        NotFoundException(String message) {
            super(message);
        }
    }

    record User(String id, String email) {
        User {
            Objects.requireNonNull(id);
            Objects.requireNonNull(email);

            email = email.trim().toLowerCase(Locale.ROOT);

            if (!email.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
                throw new ValidationException("Invalid email");
            }
        }
    }

    record Membership(
        String userId,
        WorkspaceRole role,
        Instant addedAt
    ) {
        Membership {
            Objects.requireNonNull(userId);
            Objects.requireNonNull(role);
            Objects.requireNonNull(addedAt);
        }
    }

    record SemanticModel(
        String id,
        String name,
        String ownerId,
        String source,
        Set<String> tables,
        boolean gatewayRequired,
        boolean gatewayConfigured,
        boolean credentialsConfigured,
        boolean refreshEnabled,
        int refreshIntervalHours
    ) {
        SemanticModel {
            id = requireText(id, "Model ID");
            name = requireText(name, "Model name");
            ownerId = requireText(ownerId, "Owner ID");
            source = requireText(source, "Source");

            tables = Set.copyOf(tables);

            if (tables.isEmpty()) {
                throw new ValidationException("Model requires tables");
            }

            if (refreshIntervalHours < 1
                    || refreshIntervalHours > 720) {
                throw new ValidationException(
                    "Invalid refresh interval"
                );
            }
        }

        void validateForRefresh() {
            if (gatewayRequired && !gatewayConfigured) {
                throw new ValidationException(
                    "Required gateway is not configured"
                );
            }

            if (!credentialsConfigured) {
                throw new ValidationException(
                    "Data source credentials missing"
                );
            }

            if (!refreshEnabled) {
                throw new ConflictException("Refresh is disabled");
            }
        }
    }

    record Artifact(
        String id,
        String name,
        ArtifactType type,
        String ownerId,
        String semanticModelId,
        Instant publishedAt
    ) {
        Artifact {
            id = requireText(id, "Artifact ID");
            name = requireText(name, "Artifact name");
            Objects.requireNonNull(type);
            Objects.requireNonNull(publishedAt);

            if (type == ArtifactType.REPORT
                    && semanticModelId == null) {
                throw new ValidationException(
                    "Report must reference a semantic model"
                );
            }
        }
    }

    record ShareGrant(
        String resourceId,
        String userId,
        Set<Permission> permissions,
        String grantedBy,
        Instant expiresAt
    ) {
        ShareGrant {
            permissions = Set.copyOf(permissions);

            if (permissions.isEmpty()) {
                throw new ValidationException(
                    "Permission set cannot be empty"
                );
            }

            if (permissions.contains(Permission.WRITE)
                    && !permissions.contains(Permission.VIEW)) {
                throw new ValidationException(
                    "Write requires View permission"
                );
            }
        }

        boolean isActive() {
            return expiresAt == null || expiresAt.isAfter(Instant.now());
        }
    }

    static class RefreshJob {
        private final String id;
        private final String modelId;
        private final String requestedBy;
        private RefreshStatus status;
        private final Instant createdAt;
        private Instant startedAt;
        private Instant completedAt;
        private String error;

        RefreshJob(String id, String modelId, String requestedBy) {
            this.id = id;
            this.modelId = modelId;
            this.requestedBy = requestedBy;
            this.status = RefreshStatus.QUEUED;
            this.createdAt = Instant.now();
        }

        synchronized void transition(
            RefreshStatus next,
            String error
        ) {
            boolean valid = switch (status) {
                case QUEUED -> next == RefreshStatus.RUNNING
                    || next == RefreshStatus.CANCELLED;
                case RUNNING -> next == RefreshStatus.COMPLETED
                    || next == RefreshStatus.FAILED;
                default -> false;
            };

            if (!valid) {
                throw new ConflictException(
                    "Invalid refresh transition: "
                    + status + " -> " + next
                );
            }

            if (next == RefreshStatus.RUNNING) {
                startedAt = Instant.now();
            }

            if (next == RefreshStatus.COMPLETED
                    || next == RefreshStatus.FAILED
                    || next == RefreshStatus.CANCELLED) {
                completedAt = Instant.now();
            }

            this.status = next;
            this.error = error;
        }

        String getId() {
            return id;
        }

        String getModelId() {
            return modelId;
        }

        String getRequestedBy() {
            return requestedBy;
        }

        synchronized RefreshStatus getStatus() {
            return status;
        }

        synchronized String getError() {
            return error;
        }

        synchronized long getDurationMillis() {
            if (startedAt == null || completedAt == null) {
                return -1;
            }

            return Duration.between(
                startedAt,
                completedAt
            ).toMillis();
        }
    }

    record AuditEvent(
        String id,
        String actorId,
        String action,
        String resourceId,
        Instant timestamp,
        Map<String, String> details
    ) {
        AuditEvent {
            details = Map.copyOf(details);
        }
    }

    static class Workspace {
        private final String id;
        private final String name;
        private final CapacityType capacity;

        private final Map<String, Membership> members =
            new ConcurrentHashMap<>();

        private final Map<String, SemanticModel> models =
            new ConcurrentHashMap<>();

        private final Map<String, Artifact> artifacts =
            new ConcurrentHashMap<>();

        private final Map<String, ShareGrant> grants =
            new ConcurrentHashMap<>();

        private final Map<String, RefreshJob> refreshJobs =
            new ConcurrentHashMap<>();

        private final List<AuditEvent> auditLog =
            Collections.synchronizedList(new ArrayList<>());

        Workspace(
            String id,
            String name,
            CapacityType capacity,
            String ownerId
        ) {
            this.id = id;
            this.name = name;
            this.capacity = capacity;

            members.put(
                ownerId,
                new Membership(
                    ownerId,
                    WorkspaceRole.ADMIN,
                    Instant.now()
                )
            );
        }

        void requireRole(
            String userId,
            Set<WorkspaceRole> allowed
        ) {
            Membership membership = members.get(userId);

            if (membership == null) {
                throw new AuthorizationException(
                    "Workspace membership required"
                );
            }

            if (!allowed.contains(membership.role())) {
                throw new AuthorizationException(
                    "Insufficient workspace role"
                );
            }
        }

        void audit(
            String actorId,
            String action,
            String resourceId,
            Map<String, String> details
        ) {
            auditLog.add(
                new AuditEvent(
                    UUID.randomUUID().toString(),
                    actorId,
                    action,
                    resourceId,
                    Instant.now(),
                    details
                )
            );
        }

        String getId() {
            return id;
        }

        String getName() {
            return name;
        }

        Map<String, SemanticModel> getModels() {
            return Collections.unmodifiableMap(models);
        }

        Map<String, RefreshJob> getRefreshJobs() {
            return Collections.unmodifiableMap(refreshJobs);
        }

        List<AuditEvent> getAuditLog() {
            synchronized (auditLog) {
                return List.copyOf(auditLog);
            }
        }
    }

    static class PowerBIService {
        private final Map<String, User> users =
            new ConcurrentHashMap<>();

        private final Map<String, Workspace> workspaces =
            new ConcurrentHashMap<>();

        private final AtomicLong idSequence = new AtomicLong(1000);

        private final Map<WorkspaceRole, Set<Permission>>
            rolePermissions = Map.of(
                WorkspaceRole.ADMIN,
                EnumSet.allOf(Permission.class),

                WorkspaceRole.MEMBER,
                EnumSet.allOf(Permission.class),

                WorkspaceRole.CONTRIBUTOR,
                EnumSet.of(Permission.VIEW, Permission.WRITE),

                WorkspaceRole.VIEWER,
                EnumSet.of(Permission.VIEW)
            );

        private String nextId(String prefix) {
            return prefix + "-" + idSequence.incrementAndGet();
        }

        User registerUser(String email) {
            String normalized = requireText(email, "Email")
                .toLowerCase(Locale.ROOT);

            if (!normalized.matches(
                "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"
            )) {
                throw new ValidationException("Invalid email");
            }

            boolean duplicate = users.values()
                .stream()
                .anyMatch(u -> u.email().equals(normalized));

            if (duplicate) {
                throw new ConflictException("Duplicate email");
            }

            User user = new User(
                nextId("USER"),
                normalized
            );

            users.put(user.id(), user);
            return user;
        }

        Workspace createWorkspace(
            String name,
            String ownerId,
            CapacityType capacity
        ) {
            requireUser(ownerId);

            String validName = requireText(name, "Workspace name");

            boolean duplicate = workspaces.values()
                .stream()
                .anyMatch(w -> w.name.equalsIgnoreCase(validName));

            if (duplicate) {
                throw new ConflictException(
                    "Workspace name already exists"
                );
            }

            Workspace workspace = new Workspace(
                nextId("WS"),
                validName,
                capacity,
                ownerId
            );

            workspaces.put(workspace.id, workspace);

            workspace.audit(
                ownerId,
                "WORKSPACE_CREATED",
                workspace.id,
                Map.of("capacity", capacity.name())
            );

            return workspace;
        }

        void addMember(
            String workspaceId,
            String actorId,
            String userId,
            WorkspaceRole role
        ) {
            Workspace ws = getWorkspace(workspaceId);

            requireUser(userId);

            ws.requireRole(
                actorId,
                EnumSet.of(
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.MEMBER
                )
            );

            if (ws.members.containsKey(userId)) {
                throw new ConflictException("Member already exists");
            }

            ws.members.put(
                userId,
                new Membership(userId, role, Instant.now())
            );

            ws.audit(
                actorId,
                "MEMBER_ADDED",
                userId,
                Map.of("role", role.name())
            );
        }

        SemanticModel publishModel(
            String workspaceId,
            String actorId,
            String name,
            String source,
            Set<String> tables,
            boolean gatewayRequired,
            boolean gatewayConfigured,
            boolean credentialsConfigured
        ) {
            Workspace ws = getWorkspace(workspaceId);

            ws.requireRole(
                actorId,
                EnumSet.of(
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.MEMBER,
                    WorkspaceRole.CONTRIBUTOR
                )
            );

            SemanticModel model = new SemanticModel(
                nextId("MODEL"),
                name,
                actorId,
                source,
                tables,
                gatewayRequired,
                gatewayConfigured,
                credentialsConfigured,
                true,
                24
            );

            ws.models.put(model.id(), model);

            ws.audit(
                actorId,
                "MODEL_PUBLISHED",
                model.id(),
                Map.of(
                    "name", model.name(),
                    "tableCount",
                    Integer.toString(model.tables().size())
                )
            );

            return model;
        }

        Artifact publishReport(
            String workspaceId,
            String actorId,
            String name,
            String modelId
        ) {
            Workspace ws = getWorkspace(workspaceId);

            ws.requireRole(
                actorId,
                EnumSet.of(
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.MEMBER,
                    WorkspaceRole.CONTRIBUTOR
                )
            );

            if (!ws.models.containsKey(modelId)) {
                throw new NotFoundException(
                    "Semantic model not found"
                );
            }

            Artifact report = new Artifact(
                nextId("REPORT"),
                name,
                ArtifactType.REPORT,
                actorId,
                modelId,
                Instant.now()
            );

            ws.artifacts.put(report.id(), report);

            ws.audit(
                actorId,
                "REPORT_PUBLISHED",
                report.id(),
                Map.of("modelId", modelId)
            );

            return report;
        }

        void grantPermission(
            String workspaceId,
            String actorId,
            String resourceId,
            String userId,
            Set<Permission> permissions,
            Instant expiresAt
        ) {
            Workspace ws = getWorkspace(workspaceId);

            ws.requireRole(
                actorId,
                EnumSet.of(
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.MEMBER
                )
            );

            requireUser(userId);

            if (!ws.models.containsKey(resourceId)
                    && !ws.artifacts.containsKey(resourceId)) {
                throw new NotFoundException("Resource not found");
            }

            if (expiresAt != null
                    && !expiresAt.isAfter(Instant.now())) {
                throw new ValidationException(
                    "Expiration must be in the future"
                );
            }

            ShareGrant grant = new ShareGrant(
                resourceId,
                userId,
                permissions,
                actorId,
                expiresAt
            );

            ws.grants.put(
                resourceId + ":" + userId,
                grant
            );

            ws.audit(
                actorId,
                "PERMISSION_GRANTED",
                resourceId,
                Map.of(
                    "userId", userId,
                    "permissions",
                    permissions.toString()
                )
            );
        }

        Set<Permission> effectivePermissions(
            String workspaceId,
            String userId,
            String resourceId
        ) {
            Workspace ws = getWorkspace(workspaceId);

            EnumSet<Permission> effective =
                EnumSet.noneOf(Permission.class);

            Membership membership = ws.members.get(userId);

            if (membership != null) {
                effective.addAll(
                    rolePermissions.get(membership.role())
                );
            }

            ShareGrant grant = ws.grants.get(
                resourceId + ":" + userId
            );

            if (grant != null && grant.isActive()) {
                effective.addAll(grant.permissions());
            }

            return Collections.unmodifiableSet(effective);
        }

        boolean canBuild(
            String workspaceId,
            String userId,
            String modelId
        ) {
            Workspace ws = getWorkspace(workspaceId);

            if (!ws.models.containsKey(modelId)) {
                throw new NotFoundException("Model not found");
            }

            return effectivePermissions(
                workspaceId,
                userId,
                modelId
            ).contains(Permission.BUILD);
        }

        RefreshJob queueRefresh(
            String workspaceId,
            String actorId,
            String modelId
        ) {
            Workspace ws = getWorkspace(workspaceId);

            ws.requireRole(
                actorId,
                EnumSet.of(
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.MEMBER,
                    WorkspaceRole.CONTRIBUTOR
                )
            );

            SemanticModel model = ws.models.get(modelId);

            if (model == null) {
                throw new NotFoundException("Model not found");
            }

            model.validateForRefresh();

            boolean active = ws.refreshJobs.values()
                .stream()
                .anyMatch(job ->
                    job.getModelId().equals(modelId)
                    && EnumSet.of(
                        RefreshStatus.QUEUED,
                        RefreshStatus.RUNNING
                    ).contains(job.getStatus())
                );

            if (active) {
                throw new ConflictException(
                    "Refresh already active"
                );
            }

            RefreshJob job = new RefreshJob(
                nextId("REFRESH"),
                modelId,
                actorId
            );

            ws.refreshJobs.put(job.getId(), job);

            ws.audit(
                actorId,
                "REFRESH_QUEUED",
                modelId,
                Map.of("refreshId", job.getId())
            );

            return job;
        }

        synchronized void executeRefresh(
            String workspaceId,
            String refreshId,
            boolean simulateFailure
        ) {
            Workspace ws = getWorkspace(workspaceId);

            RefreshJob job = ws.refreshJobs.get(refreshId);

            if (job == null) {
                throw new NotFoundException("Refresh job not found");
            }

            SemanticModel model = ws.models.get(job.getModelId());

            if (model == null) {
                throw new NotFoundException(
                    "Associated model not found"
                );
            }

            job.transition(RefreshStatus.RUNNING, null);

            try {
                model.validateForRefresh();

                if (simulateFailure) {
                    throw new ServiceException(
                        "Simulated data-source connection failure"
                    );
                }

                job.transition(RefreshStatus.COMPLETED, null);

            } catch (ServiceException ex) {
                job.transition(
                    RefreshStatus.FAILED,
                    ex.getMessage()
                );
            }

            ws.audit(
                job.getRequestedBy(),
                "REFRESH_FINISHED",
                model.id(),
                Map.of(
                    "refreshId", refreshId,
                    "status", job.getStatus().name(),
                    "error",
                    Objects.toString(job.getError(), "")
                )
            );
        }

        void printWorkspaceReport(String workspaceId) {
            Workspace ws = getWorkspace(workspaceId);

            System.out.println("\nENTERPRISE WORKSPACE REPORT");
            System.out.println("Workspace: " + ws.name);
            System.out.println("Capacity: " + ws.capacity);
            System.out.println("Members: " + ws.members.size());
            System.out.println("Semantic models: " + ws.models.size());
            System.out.println("Artifacts: " + ws.artifacts.size());

            Map<RefreshStatus, Long> counts =
                ws.refreshJobs.values()
                    .stream()
                    .collect(Collectors.groupingBy(
                        RefreshJob::getStatus,
                        () -> new EnumMap<>(RefreshStatus.class),
                        Collectors.counting()
                    ));

            System.out.println("Refresh distribution: " + counts);

            for (RefreshJob job : ws.refreshJobs.values()) {
                System.out.println(
                    job.getId()
                    + " | " + job.getStatus()
                    + " | " + job.getError()
                );
            }
        }

        private User requireUser(String id) {
            User user = users.get(id);

            if (user == null) {
                throw new NotFoundException("User not found");
            }

            return user;
        }

        private Workspace getWorkspace(String id) {
            Workspace ws = workspaces.get(id);

            if (ws == null) {
                throw new NotFoundException("Workspace not found");
            }

            return ws;
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " cannot be empty");
        }

        if (value.length() > 120) {
            throw new ValidationException(field + " is too long");
        }

        return value.trim();
    }

    public static void main(String[] args) {
        try {
            PowerBIService service = new PowerBIService();

            User admin = service.registerUser(
                "admin@enterprise.example"
            );

            User analyst = service.registerUser(
                "analyst@enterprise.example"
            );

            User executive = service.registerUser(
                "executive@enterprise.example"
            );

            Workspace workspace = service.createWorkspace(
                "Enterprise Sales Analytics",
                admin.id(),
                CapacityType.PREMIUM
            );

            service.addMember(
                workspace.getId(),
                admin.id(),
                analyst.id(),
                WorkspaceRole.CONTRIBUTOR
            );

            service.addMember(
                workspace.getId(),
                admin.id(),
                executive.id(),
                WorkspaceRole.VIEWER
            );

            SemanticModel model = service.publishModel(
                workspace.getId(),
                analyst.id(),
                "Sales Semantic Model",
                "Enterprise SQL Database",
                Set.of(
                    "FactSales",
                    "DimCustomer",
                    "DimProduct",
                    "DimDate"
                ),
                true,
                true,
                true
            );

            Artifact report = service.publishReport(
                workspace.getId(),
                analyst.id(),
                "Executive Sales Report",
                model.id()
            );

            System.out.println(
                "Published artifact: " + report.name()
            );

            service.grantPermission(
                workspace.getId(),
                admin.id(),
                model.id(),
                executive.id(),
                EnumSet.of(Permission.VIEW, Permission.BUILD),
                Instant.now().plus(Duration.ofDays(30))
            );

            System.out.println(
                "Executive Build permission: "
                + service.canBuild(
                    workspace.getId(),
                    executive.id(),
                    model.id()
                )
            );

            RefreshJob successfulRefresh = service.queueRefresh(
                workspace.getId(),
                analyst.id(),
                model.id()
            );

            service.executeRefresh(
                workspace.getId(),
                successfulRefresh.getId(),
                false
            );

            RefreshJob failedRefresh = service.queueRefresh(
                workspace.getId(),
                analyst.id(),
                model.id()
            );

            service.executeRefresh(
                workspace.getId(),
                failedRefresh.getId(),
                true
            );

            service.printWorkspaceReport(workspace.getId());

            System.out.println("\nAuthorization test:");

            try {
                service.publishReport(
                    workspace.getId(),
                    executive.id(),
                    "Unauthorized Report",
                    model.id()
                );
            } catch (AuthorizationException ex) {
                System.out.println("Rejected: " + ex.getMessage());
            }

            System.out.println("\nGateway test:");

            try {
                service.publishModel(
                    workspace.getId(),
                    analyst.id(),
                    "Broken Semantic Model",
                    "On-premises SQL",
                    Set.of("FactSales"),
                    true,
                    false,
                    true
                );
            } catch (ValidationException ex) {
                System.out.println("Rejected: " + ex.getMessage());
            }

            System.out.println(
                "\nAudit records: " + workspace.getAuditLog().size()
            );

        } catch (ServiceException ex) {
            System.err.println(
                "Enterprise service failure: " + ex.getMessage()
            );
            System.exit(1);
        }
    }
}
