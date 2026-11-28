#!/usr/bin/env python3
"""
Power BI Service: Workspace, Publishing, Sharing, Semantic Models,
Refresh Scheduling, Permissions, and Governance.

Python 3.10+
Standard-library only.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("powerbi_service")


class ServiceError(Exception):
    pass


class ValidationError(ServiceError):
    pass


class PermissionDenied(ServiceError):
    pass


class ResourceNotFound(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class WorkspaceRole(str, Enum):
    ADMIN = "Admin"
    MEMBER = "Member"
    CONTRIBUTOR = "Contributor"
    VIEWER = "Viewer"


class ArtifactType(str, Enum):
    REPORT = "Report"
    SEMANTIC_MODEL = "SemanticModel"
    DASHBOARD = "Dashboard"


class RefreshStatus(str, Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class Permission(str, Enum):
    VIEW = "View"
    BUILD = "Build"
    RESHARE = "Reshare"
    WRITE = "Write"


ROLE_PERMISSIONS = {
    WorkspaceRole.ADMIN: set(Permission),
    WorkspaceRole.MEMBER: set(Permission),
    WorkspaceRole.CONTRIBUTOR: {
        Permission.WRITE,
        Permission.VIEW,
    },
    WorkspaceRole.VIEWER: {
        Permission.VIEW,
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_name(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    if len(value.strip()) > 120:
        raise ValidationError(f"{field_name} exceeds 120 characters")
    return value.strip()


@dataclass(frozen=True)
class User:
    user_id: str
    email: str

    def __post_init__(self):
        email = self.email.strip().lower()
        if "@" not in email or email.startswith("@"):
            raise ValidationError("Invalid email address")
        object.__setattr__(self, "email", email)


@dataclass
class Membership:
    user_id: str
    role: WorkspaceRole
    added_at: datetime = field(default_factory=utc_now)


@dataclass
class SemanticModel:
    model_id: str
    name: str
    owner_id: str
    source_description: str
    tables: set[str]
    gateway_required: bool = False
    gateway_configured: bool = False
    credentials_configured: bool = False
    refresh_enabled: bool = True
    last_refresh: Optional[datetime] = None
    last_refresh_status: Optional[RefreshStatus] = None
    refresh_interval_hours: int = 24

    def validate(self):
        validate_name(self.name, "Semantic model name")
        if not self.tables:
            raise ValidationError("A semantic model requires at least one table")
        if not 1 <= self.refresh_interval_hours <= 24 * 30:
            raise ValidationError("Invalid refresh interval")

        if self.gateway_required and not self.gateway_configured:
            raise ValidationError("Required on-premises gateway is not configured")

        if not self.credentials_configured:
            raise ValidationError("Data source credentials are not configured")


@dataclass
class Artifact:
    artifact_id: str
    name: str
    artifact_type: ArtifactType
    owner_id: str
    semantic_model_id: Optional[str] = None
    published_at: datetime = field(default_factory=utc_now)


@dataclass
class RefreshJob:
    refresh_id: str
    model_id: str
    requested_by: str
    status: RefreshStatus
    requested_at: datetime = field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ShareGrant:
    resource_id: str
    user_id: str
    permissions: set[Permission]
    granted_by: str
    expires_at: Optional[datetime] = None


@dataclass
class AuditEvent:
    event_id: str
    actor_id: str
    action: str
    resource_id: str
    timestamp: datetime = field(default_factory=utc_now)
    details: dict = field(default_factory=dict)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    capacity: str = "Shared"
    memberships: dict[str, Membership] = field(default_factory=dict)
    semantic_models: dict[str, SemanticModel] = field(default_factory=dict)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    refresh_jobs: dict[str, RefreshJob] = field(default_factory=dict)
    shares: dict[tuple[str, str], ShareGrant] = field(default_factory=dict)
    audit_log: list[AuditEvent] = field(default_factory=list)
    deleted: bool = False


class PowerBIService:
    """
    An in-memory Power BI Service workflow simulator.

    Workspace roles and item-level grants are deliberately separate.
    A workspace Viewer role does not automatically grant Build permission
    on every semantic model.
    """

    def __init__(self):
        self.users: dict[str, User] = {}
        self.workspaces: dict[str, Workspace] = {}

    def register_user(self, email: str) -> User:
        email = email.strip().lower()

        if any(user.email == email for user in self.users.values()):
            raise ConflictError("User already registered")

        user = User(str(uuid.uuid4()), email)
        self.users[user.user_id] = user
        return user

    def _user(self, user_id: str) -> User:
        try:
            return self.users[user_id]
        except KeyError:
            raise ResourceNotFound("User not found")

    def _workspace(self, workspace_id: str) -> Workspace:
        try:
            workspace = self.workspaces[workspace_id]
        except KeyError:
            raise ResourceNotFound("Workspace not found")

        if workspace.deleted:
            raise ResourceNotFound("Workspace has been deleted")

        return workspace

    def _membership(
        self,
        workspace: Workspace,
        user_id: str,
    ) -> Membership:
        membership = workspace.memberships.get(user_id)

        if membership is None:
            raise PermissionDenied("User is not a workspace member")

        return membership

    def _require_role(
        self,
        workspace: Workspace,
        user_id: str,
        allowed: set[WorkspaceRole],
    ):
        membership = self._membership(workspace, user_id)

        if membership.role not in allowed:
            raise PermissionDenied(
                f"Role {membership.role.value} is not authorized"
            )

    def _audit(
        self,
        workspace: Workspace,
        actor_id: str,
        action: str,
        resource_id: str,
        details: Optional[dict] = None,
    ):
        workspace.audit_log.append(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                actor_id=actor_id,
                action=action,
                resource_id=resource_id,
                details=details or {},
            )
        )

    def create_workspace(
        self,
        name: str,
        owner_id: str,
        capacity: str = "Shared",
    ) -> Workspace:
        self._user(owner_id)
        name = validate_name(name, "Workspace name")

        if capacity not in {"Shared", "Premium", "Fabric"}:
            raise ValidationError("Unsupported capacity classification")

        if any(
            w.name.lower() == name.lower() and not w.deleted
            for w in self.workspaces.values()
        ):
            raise ConflictError("Workspace name already exists")

        workspace = Workspace(
            workspace_id=str(uuid.uuid4()),
            name=name,
            capacity=capacity,
        )

        workspace.memberships[owner_id] = Membership(
            owner_id,
            WorkspaceRole.ADMIN,
        )

        self.workspaces[workspace.workspace_id] = workspace

        self._audit(
            workspace,
            owner_id,
            "WORKSPACE_CREATED",
            workspace.workspace_id,
            {"capacity": capacity},
        )

        logger.info("Created workspace: %s", name)
        return workspace

    def add_member(
        self,
        workspace_id: str,
        actor_id: str,
        user_id: str,
        role: WorkspaceRole,
    ):
        workspace = self._workspace(workspace_id)
        self._user(actor_id)
        self._user(user_id)

        self._require_role(
            workspace,
            actor_id,
            {WorkspaceRole.ADMIN, WorkspaceRole.MEMBER},
        )

        if user_id in workspace.memberships:
            raise ConflictError("User is already a workspace member")

        workspace.memberships[user_id] = Membership(user_id, role)

        self._audit(
            workspace,
            actor_id,
            "MEMBER_ADDED",
            user_id,
            {"role": role.value},
        )

    def change_member_role(
        self,
        workspace_id: str,
        actor_id: str,
        user_id: str,
        role: WorkspaceRole,
    ):
        workspace = self._workspace(workspace_id)

        self._require_role(
            workspace,
            actor_id,
            {WorkspaceRole.ADMIN},
        )

        membership = self._membership(workspace, user_id)

        if membership.role == WorkspaceRole.ADMIN:
            admin_count = sum(
                m.role == WorkspaceRole.ADMIN
                for m in workspace.memberships.values()
            )
            if admin_count == 1 and role != WorkspaceRole.ADMIN:
                raise ConflictError("Cannot demote the last workspace admin")

        membership.role = role

        self._audit(
            workspace,
            actor_id,
            "MEMBER_ROLE_CHANGED",
            user_id,
            {"new_role": role.value},
        )

    def create_semantic_model(
        self,
        workspace_id: str,
        actor_id: str,
        name: str,
        source_description: str,
        tables: set[str],
        gateway_required: bool = False,
        gateway_configured: bool = False,
        credentials_configured: bool = True,
    ) -> SemanticModel:
        workspace = self._workspace(workspace_id)

        self._require_role(
            workspace,
            actor_id,
            {
                WorkspaceRole.ADMIN,
                WorkspaceRole.MEMBER,
                WorkspaceRole.CONTRIBUTOR,
            },
        )

        model = SemanticModel(
            model_id=str(uuid.uuid4()),
            name=validate_name(name, "Model name"),
            owner_id=actor_id,
            source_description=validate_name(
                source_description,
                "Source description",
            ),
            tables={validate_name(t, "Table name") for t in tables},
            gateway_required=gateway_required,
            gateway_configured=gateway_configured,
            credentials_configured=credentials_configured,
        )

        model.validate()

        workspace.semantic_models[model.model_id] = model

        self._audit(
            workspace,
            actor_id,
            "SEMANTIC_MODEL_CREATED",
            model.model_id,
            {"tables": sorted(model.tables)},
        )

        return model

    def publish_artifact(
        self,
        workspace_id: str,
        actor_id: str,
        name: str,
        artifact_type: ArtifactType,
        semantic_model_id: Optional[str] = None,
    ) -> Artifact:
        workspace = self._workspace(workspace_id)

        self._require_role(
            workspace,
            actor_id,
            {
                WorkspaceRole.ADMIN,
                WorkspaceRole.MEMBER,
                WorkspaceRole.CONTRIBUTOR,
            },
        )

        if artifact_type == ArtifactType.REPORT:
            if semantic_model_id not in workspace.semantic_models:
                raise ResourceNotFound(
                    "Report requires a semantic model in this workspace"
                )

        elif semantic_model_id is not None:
            if semantic_model_id not in workspace.semantic_models:
                raise ResourceNotFound("Semantic model not found")

        artifact = Artifact(
            artifact_id=str(uuid.uuid4()),
            name=validate_name(name, "Artifact name"),
            artifact_type=artifact_type,
            owner_id=actor_id,
            semantic_model_id=semantic_model_id,
        )

        workspace.artifacts[artifact.artifact_id] = artifact

        self._audit(
            workspace,
            actor_id,
            "ARTIFACT_PUBLISHED",
            artifact.artifact_id,
            {
                "type": artifact_type.value,
                "semantic_model_id": semantic_model_id,
            },
        )

        logger.info("Published artifact: %s", artifact.name)
        return artifact

    def grant_item_permission(
        self,
        workspace_id: str,
        actor_id: str,
        resource_id: str,
        user_id: str,
        permissions: set[Permission],
        expires_at: Optional[datetime] = None,
    ):
        workspace = self._workspace(workspace_id)

        self._require_role(
            workspace,
            actor_id,
            {WorkspaceRole.ADMIN, WorkspaceRole.MEMBER},
        )

        self._user(user_id)

        if resource_id not in (
            set(workspace.artifacts) | set(workspace.semantic_models)
        ):
            raise ResourceNotFound("Shareable resource not found")

        if not permissions:
            raise ValidationError("At least one permission is required")

        if expires_at and expires_at <= utc_now():
            raise ValidationError("Expiration must be in the future")

        if Permission.WRITE in permissions and (
            Permission.VIEW not in permissions
        ):
            raise ValidationError("Write permission requires View permission")

        grant = ShareGrant(
            resource_id=resource_id,
            user_id=user_id,
            permissions=set(permissions),
            granted_by=actor_id,
            expires_at=expires_at,
        )

        workspace.shares[(resource_id, user_id)] = grant

        self._audit(
            workspace,
            actor_id,
            "ITEM_PERMISSION_GRANTED",
            resource_id,
            {
                "user_id": user_id,
                "permissions": sorted(p.value for p in permissions),
            },
        )

    def effective_permissions(
        self,
        workspace: Workspace,
        user_id: str,
        resource_id: str,
    ) -> set[Permission]:
        permissions = set()

        membership = workspace.memberships.get(user_id)

        if membership:
            permissions.update(ROLE_PERMISSIONS[membership.role])

        grant = workspace.shares.get((resource_id, user_id))

        if grant:
            if grant.expires_at is None or grant.expires_at > utc_now():
                permissions.update(grant.permissions)

        return permissions

    def can_build(
        self,
        workspace_id: str,
        user_id: str,
        model_id: str,
    ) -> bool:
        workspace = self._workspace(workspace_id)

        if model_id not in workspace.semantic_models:
            raise ResourceNotFound("Semantic model not found")

        return Permission.BUILD in self.effective_permissions(
            workspace,
            user_id,
            model_id,
        )

    def start_refresh(
        self,
        workspace_id: str,
        actor_id: str,
        model_id: str,
    ) -> RefreshJob:
        workspace = self._workspace(workspace_id)

        self._require_role(
            workspace,
            actor_id,
            {
                WorkspaceRole.ADMIN,
                WorkspaceRole.MEMBER,
                WorkspaceRole.CONTRIBUTOR,
            },
        )

        model = workspace.semantic_models.get(model_id)

        if model is None:
            raise ResourceNotFound("Semantic model not found")

        if not model.refresh_enabled:
            raise ConflictError("Refresh is disabled")

        model.validate()

        active = [
            job for job in workspace.refresh_jobs.values()
            if job.model_id == model_id
            and job.status in {
                RefreshStatus.QUEUED,
                RefreshStatus.RUNNING,
            }
        ]

        if active:
            raise ConflictError("A refresh is already active")

        job = RefreshJob(
            refresh_id=str(uuid.uuid4()),
            model_id=model_id,
            requested_by=actor_id,
            status=RefreshStatus.QUEUED,
        )

        workspace.refresh_jobs[job.refresh_id] = job

        self._audit(
            workspace,
            actor_id,
            "REFRESH_QUEUED",
            model_id,
            {"refresh_id": job.refresh_id},
        )

        return job

    def execute_refresh(
        self,
        workspace_id: str,
        refresh_id: str,
        simulated_failure: bool = False,
    ) -> RefreshJob:
        workspace = self._workspace(workspace_id)
        job = workspace.refresh_jobs.get(refresh_id)

        if job is None:
            raise ResourceNotFound("Refresh job not found")

        if job.status != RefreshStatus.QUEUED:
            raise ConflictError("Only queued jobs can start")

        model = workspace.semantic_models[job.model_id]

        job.status = RefreshStatus.RUNNING
        job.started_at = utc_now()

        try:
            model.validate()

            if simulated_failure:
                raise ServiceError("Simulated source connectivity failure")

            job.status = RefreshStatus.COMPLETED
            model.last_refresh = utc_now()
            model.last_refresh_status = RefreshStatus.COMPLETED

        except ServiceError as exc:
            job.status = RefreshStatus.FAILED
            job.error_message = str(exc)
            model.last_refresh_status = RefreshStatus.FAILED
            logger.error("Refresh failed: %s", exc)

        finally:
            job.completed_at = utc_now()

            self._audit(
                workspace,
                job.requested_by,
                "REFRESH_FINISHED",
                job.model_id,
                {
                    "refresh_id": refresh_id,
                    "status": job.status.value,
                    "error": job.error_message,
                },
            )

        return job

    def close_workspace(self, workspace_id: str, actor_id: str):
        workspace = self._workspace(workspace_id)

        self._require_role(
            workspace,
            actor_id,
            {WorkspaceRole.ADMIN},
        )

        workspace.deleted = True

        logger.warning("Workspace deleted: %s", workspace.name)

    def workspace_report(self, workspace_id: str) -> dict:
        workspace = self._workspace(workspace_id)

        return {
            "workspace": workspace.name,
            "capacity": workspace.capacity,
            "members": len(workspace.memberships),
            "semantic_models": len(workspace.semantic_models),
            "reports": sum(
                a.artifact_type == ArtifactType.REPORT
                for a in workspace.artifacts.values()
            ),
            "dashboards": sum(
                a.artifact_type == ArtifactType.DASHBOARD
                for a in workspace.artifacts.values()
            ),
            "refreshes": {
                status.value: sum(
                    j.status == status
                    for j in workspace.refresh_jobs.values()
                )
                for status in RefreshStatus
            },
        }

    def export_audit_log(
        self,
        workspace_id: str,
        output_path: str,
    ):
        workspace = self._workspace(workspace_id)

        # Write to a restricted local destination in production.
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(
                [asdict(event) for event in workspace.audit_log],
                file,
                default=lambda value: (
                    value.isoformat()
                    if isinstance(value, datetime)
                    else value.value
                    if isinstance(value, Enum)
                    else str(value)
                ),
                indent=2,
            )


def run_demo():
    service = PowerBIService()

    admin = service.register_user("admin@enterprise.example")
    analyst = service.register_user("analyst@enterprise.example")
    executive = service.register_user("executive@enterprise.example")

    workspace = service.create_workspace(
        "Enterprise Sales Analytics",
        admin.user_id,
        "Premium",
    )

    service.add_member(
        workspace.workspace_id,
        admin.user_id,
        analyst.user_id,
        WorkspaceRole.CONTRIBUTOR,
    )

    service.add_member(
        workspace.workspace_id,
        admin.user_id,
        executive.user_id,
        WorkspaceRole.VIEWER,
    )

    model = service.create_semantic_model(
        workspace.workspace_id,
        analyst.user_id,
        "Sales Semantic Model",
        "Enterprise SQL Sales Database",
        {"FactSales", "DimCustomer", "DimProduct", "DimDate"},
        gateway_required=True,
        gateway_configured=True,
        credentials_configured=True,
    )

    report = service.publish_artifact(
        workspace.workspace_id,
        analyst.user_id,
        "Executive Sales Report",
        ArtifactType.REPORT,
        model.model_id,
    )

    service.grant_item_permission(
        workspace.workspace_id,
        admin.user_id,
        model.model_id,
        executive.user_id,
        {Permission.VIEW, Permission.BUILD},
        utc_now() + timedelta(days=30),
    )

    print("\nSemantic model Build permission:")
    print(service.can_build(
        workspace.workspace_id,
        executive.user_id,
        model.model_id,
    ))

    refresh = service.start_refresh(
        workspace.workspace_id,
        analyst.user_id,
        model.model_id,
    )

    service.execute_refresh(
        workspace.workspace_id,
        refresh.refresh_id,
    )

    print("\nWorkspace report:")
    print(json.dumps(
        service.workspace_report(workspace.workspace_id),
        indent=2,
    ))

    print("\nPublished report:")
    print(report.name)

    # An invalid report publication is rejected.
    try:
        service.publish_artifact(
            workspace.workspace_id,
            analyst.user_id,
            "Broken Report",
            ArtifactType.REPORT,
            "missing-model",
        )
    except ResourceNotFound as exc:
        print("Expected validation failure:", exc)

    # A second refresh cannot start while the first is active.
    failed_job = service.start_refresh(
        workspace.workspace_id,
        analyst.user_id,
        model.model_id,
    )

    service.execute_refresh(
        workspace.workspace_id,
        failed_job.refresh_id,
        simulated_failure=True,
    )

    print("\nFinal audit events:", len(workspace.audit_log))


if __name__ == "__main__":
    run_demo()
