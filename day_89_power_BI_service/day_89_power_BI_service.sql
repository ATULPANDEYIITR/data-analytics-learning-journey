/*
    POWER BI SERVICE: ENTERPRISE WORKSPACE GOVERNANCE DATABASE

    PostgreSQL 15+

    Models:
      - Organizations and users
      - Workspaces and capacities
      - Workspace membership and roles
      - Semantic models and data sources
      - Reports and dashboards
      - Publication records
      - Item-level permissions
      - Refresh schedules and execution history
      - Gateway configuration
      - Audit events
      - Workspace sharing
      - Permission evaluation
      - Operational reporting

    This database is a governance and operational simulation.
    It is not a replacement for the Power BI Service metadata store.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS powerbi;

SET search_path TO powerbi, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE workspace_role AS ENUM (
    'ADMIN',
    'MEMBER',
    'CONTRIBUTOR',
    'VIEWER'
);

CREATE TYPE capacity_type AS ENUM (
    'SHARED',
    'PREMIUM',
    'FABRIC'
);

CREATE TYPE artifact_type AS ENUM (
    'SEMANTIC_MODEL',
    'REPORT',
    'DASHBOARD'
);

CREATE TYPE permission_type AS ENUM (
    'VIEW',
    'BUILD',
    'WRITE',
    'RESHARE'
);

CREATE TYPE refresh_status AS ENUM (
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE publication_status AS ENUM (
    'PUBLISHED',
    'SUPERSEDED',
    'WITHDRAWN'
);

-- ============================================================
-- 2. USERS AND ORGANIZATIONS
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_email UNIQUE (email),
    CONSTRAINT ck_user_email CHECK (
        email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
    ),
    CONSTRAINT ck_display_name CHECK (
        LENGTH(TRIM(display_name)) > 0
    )
);

CREATE INDEX idx_users_organization
    ON users(organization_id);

-- ============================================================
-- 3. WORKSPACES
-- ============================================================

CREATE TABLE workspaces (
    workspace_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    workspace_name VARCHAR(150) NOT NULL,
    capacity capacity_type NOT NULL DEFAULT 'SHARED',
    owner_user_id BIGINT NOT NULL REFERENCES users(user_id),
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_workspace_name
        UNIQUE (organization_id, workspace_name),

    CONSTRAINT ck_workspace_name CHECK (
        LENGTH(TRIM(workspace_name)) > 0
    )
);

CREATE INDEX idx_workspaces_org_active
    ON workspaces(organization_id, active);

CREATE TABLE workspace_members (
    workspace_id BIGINT NOT NULL
        REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL
        REFERENCES users(user_id),
    role workspace_role NOT NULL,
    added_by BIGINT NOT NULL REFERENCES users(user_id),
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (workspace_id, user_id)
);

CREATE INDEX idx_workspace_members_user
    ON workspace_members(user_id, active);

CREATE INDEX idx_workspace_members_role
    ON workspace_members(workspace_id, role)
    WHERE active = TRUE;

-- ============================================================
-- 4. DATA SOURCES AND GATEWAYS
-- ============================================================

CREATE TABLE data_sources (
    data_source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    source_name VARCHAR(150) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    connection_class VARCHAR(20) NOT NULL,
    endpoint_description TEXT NOT NULL,
    gateway_required BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_connection_class CHECK (
        connection_class IN ('CLOUD', 'ON_PREMISES')
    ),

    CONSTRAINT ck_source_type CHECK (
        LENGTH(TRIM(source_type)) > 0
    )
);

CREATE TABLE gateways (
    gateway_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    gateway_name VARCHAR(150) NOT NULL,
    machine_name VARCHAR(150) NOT NULL,
    cluster_name VARCHAR(150),
    online BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,

    CONSTRAINT uq_gateway_name
        UNIQUE (organization_id, gateway_name)
);

CREATE INDEX idx_gateways_health
    ON gateways(organization_id, online, enabled);

CREATE TABLE gateway_source_mappings (
    gateway_id BIGINT NOT NULL
        REFERENCES gateways(gateway_id),
    data_source_id BIGINT NOT NULL
        REFERENCES data_sources(data_source_id),
    configured BOOLEAN NOT NULL DEFAULT FALSE,
    credential_reference VARCHAR(255),
    last_validated_at TIMESTAMPTZ,

    PRIMARY KEY (gateway_id, data_source_id)
);

-- Credential values and secrets are deliberately not stored here.
-- credential_reference identifies an external secret-management entry.

-- ============================================================
-- 5. SEMANTIC MODELS
-- ============================================================

CREATE TABLE semantic_models (
    semantic_model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id BIGINT NOT NULL
        REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    data_source_id BIGINT NOT NULL
        REFERENCES data_sources(data_source_id),
    gateway_id BIGINT REFERENCES gateways(gateway_id),
    model_name VARCHAR(150) NOT NULL,
    owner_user_id BIGINT NOT NULL REFERENCES users(user_id),
    description TEXT,
    storage_mode VARCHAR(20) NOT NULL DEFAULT 'IMPORT',
    credentials_configured BOOLEAN NOT NULL DEFAULT FALSE,
    refresh_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    refresh_interval_hours INTEGER NOT NULL DEFAULT 24,
    last_refresh_at TIMESTAMPTZ,
    last_refresh_status refresh_status,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_model_workspace_name
        UNIQUE (workspace_id, model_name),

    CONSTRAINT ck_storage_mode CHECK (
        storage_mode IN ('IMPORT', 'DIRECTQUERY', 'DUAL', 'LIVE')
    ),

    CONSTRAINT ck_refresh_interval CHECK (
        refresh_interval_hours BETWEEN 1 AND 720
    )
);

CREATE INDEX idx_models_workspace
    ON semantic_models(workspace_id);

CREATE INDEX idx_models_refresh
    ON semantic_models(refresh_enabled, last_refresh_status)
    WHERE refresh_enabled = TRUE;

CREATE TABLE semantic_model_tables (
    model_table_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    semantic_model_id BIGINT NOT NULL
        REFERENCES semantic_models(semantic_model_id) ON DELETE CASCADE,
    table_name VARCHAR(150) NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,

    CONSTRAINT uq_model_table
        UNIQUE (semantic_model_id, table_name)
);

CREATE INDEX idx_model_tables_model
    ON semantic_model_tables(semantic_model_id);

-- ============================================================
-- 6. REPORTS AND DASHBOARDS
-- ============================================================

CREATE TABLE artifacts (
    artifact_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id BIGINT NOT NULL
        REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    semantic_model_id BIGINT
        REFERENCES semantic_models(semantic_model_id),
    artifact_name VARCHAR(150) NOT NULL,
    artifact_kind artifact_type NOT NULL,
    owner_user_id BIGINT NOT NULL REFERENCES users(user_id),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMPTZ,

    CONSTRAINT uq_artifact_workspace_name
        UNIQUE (workspace_id, artifact_name),

    CONSTRAINT ck_report_model CHECK (
        artifact_kind <> 'REPORT'
        OR semantic_model_id IS NOT NULL
    )
);

CREATE INDEX idx_artifacts_workspace_type
    ON artifacts(workspace_id, artifact_kind);

CREATE INDEX idx_artifacts_semantic_model
    ON artifacts(semantic_model_id)
    WHERE semantic_model_id IS NOT NULL;

-- ============================================================
-- 7. PUBLICATION HISTORY
-- ============================================================

CREATE TABLE publication_history (
    publication_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artifact_id BIGINT NOT NULL
        REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    published_by BIGINT NOT NULL REFERENCES users(user_id),
    publication_version INTEGER NOT NULL,
    source_branch VARCHAR(150),
    source_commit VARCHAR(80),
    status publication_status NOT NULL DEFAULT 'PUBLISHED',
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_artifact_publication_version
        UNIQUE (artifact_id, publication_version),

    CONSTRAINT ck_publication_version CHECK (
        publication_version > 0
    )
);

CREATE INDEX idx_publication_history_artifact
    ON publication_history(artifact_id, published_at DESC);

-- ============================================================
-- 8. ITEM-LEVEL PERMISSIONS
-- ============================================================

CREATE TABLE item_permissions (
    permission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artifact_id BIGINT
        REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    semantic_model_id BIGINT
        REFERENCES semantic_models(semantic_model_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    permission permission_type NOT NULL,
    granted_by BIGINT NOT NULL REFERENCES users(user_id),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_permission_resource CHECK (
        (artifact_id IS NOT NULL AND semantic_model_id IS NULL)
        OR
        (artifact_id IS NULL AND semantic_model_id IS NOT NULL)
    ),

    CONSTRAINT ck_permission_expiration CHECK (
        expires_at IS NULL OR expires_at > granted_at
    )
);

CREATE UNIQUE INDEX uq_active_artifact_permission
    ON item_permissions(artifact_id, user_id, permission)
    WHERE active = TRUE AND artifact_id IS NOT NULL;

CREATE UNIQUE INDEX uq_active_model_permission
    ON item_permissions(semantic_model_id, user_id, permission)
    WHERE active = TRUE AND semantic_model_id IS NOT NULL;

CREATE INDEX idx_item_permissions_user
    ON item_permissions(user_id, active);

-- ============================================================
-- 9. REFRESH SCHEDULES AND EXECUTION
-- ============================================================

CREATE TABLE refresh_schedules (
    schedule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    semantic_model_id BIGINT NOT NULL
        REFERENCES semantic_models(semantic_model_id) ON DELETE CASCADE,
    schedule_name VARCHAR(120) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    timezone_name VARCHAR(80) NOT NULL DEFAULT 'UTC',
    frequency VARCHAR(20) NOT NULL DEFAULT 'DAILY',
    scheduled_time TIME NOT NULL DEFAULT '02:00',
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_refresh_frequency CHECK (
        frequency IN ('HOURLY', 'DAILY', 'WEEKLY')
    )
);

CREATE INDEX idx_refresh_schedules_due
    ON refresh_schedules(next_run_at)
    WHERE enabled = TRUE;

CREATE TABLE refresh_jobs (
    refresh_job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    semantic_model_id BIGINT NOT NULL
        REFERENCES semantic_models(semantic_model_id),
    requested_by BIGINT NOT NULL REFERENCES users(user_id),
    schedule_id BIGINT
        REFERENCES refresh_schedules(schedule_id),
    status refresh_status NOT NULL DEFAULT 'QUEUED',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    rows_processed BIGINT,
    error_code VARCHAR(80),
    error_message TEXT,

    CONSTRAINT ck_refresh_timestamps CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    ),

    CONSTRAINT ck_rows_processed CHECK (
        rows_processed IS NULL OR rows_processed >= 0
    )
);

CREATE INDEX idx_refresh_jobs_model_time
    ON refresh_jobs(semantic_model_id, requested_at DESC);

CREATE INDEX idx_refresh_jobs_status
    ON refresh_jobs(status, requested_at);

CREATE UNIQUE INDEX uq_one_active_refresh_per_model
    ON refresh_jobs(semantic_model_id)
    WHERE status IN ('QUEUED', 'RUNNING');

-- ============================================================
-- 10. AUDIT EVENTS
-- ============================================================

CREATE TABLE audit_events (
    audit_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    workspace_id BIGINT REFERENCES workspaces(workspace_id),
    actor_id BIGINT REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id BIGINT,
    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_audit_action CHECK (
        LENGTH(TRIM(action)) > 0
    )
);

CREATE INDEX idx_audit_workspace_time
    ON audit_events(workspace_id, occurred_at DESC);

CREATE INDEX idx_audit_actor_time
    ON audit_events(actor_id, occurred_at DESC);

CREATE INDEX idx_audit_details
    ON audit_events USING GIN(event_details);

-- ============================================================
-- 11. WORKSPACE ROLE PERMISSION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.role_has_permission(
    p_role workspace_role,
    p_permission permission_type
)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE p_role
        WHEN 'ADMIN' THEN TRUE
        WHEN 'MEMBER' THEN TRUE
        WHEN 'CONTRIBUTOR' THEN
            p_permission IN ('VIEW', 'WRITE')
        WHEN 'VIEWER' THEN
            p_permission = 'VIEW'
        ELSE FALSE
    END;
$$;

-- ============================================================
-- 12. EFFECTIVE PERMISSION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.has_item_permission(
    p_workspace_id BIGINT,
    p_user_id BIGINT,
    p_model_id BIGINT,
    p_artifact_id BIGINT,
    p_permission permission_type
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
    SELECT
        EXISTS (
            SELECT 1
            FROM workspace_members wm
            WHERE wm.workspace_id = p_workspace_id
              AND wm.user_id = p_user_id
              AND wm.active = TRUE
              AND role_has_permission(wm.role, p_permission)
        )
        OR EXISTS (
            SELECT 1
            FROM item_permissions ip
            WHERE ip.user_id = p_user_id
              AND ip.permission = p_permission
              AND ip.active = TRUE
              AND (ip.expires_at IS NULL
                   OR ip.expires_at > CURRENT_TIMESTAMP)
              AND (
                  (p_model_id IS NOT NULL
                   AND ip.semantic_model_id = p_model_id)
                  OR
                  (p_artifact_id IS NOT NULL
                   AND ip.artifact_id = p_artifact_id)
              )
        );
$$;

-- ============================================================
-- 13. VALIDATE REPORT PUBLICATION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.validate_artifact_model()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_model_workspace BIGINT;
BEGIN
    IF NEW.artifact_kind = 'REPORT' THEN
        IF NEW.semantic_model_id IS NULL THEN
            RAISE EXCEPTION
                'A report must reference a semantic model';
        END IF;

        SELECT workspace_id
        INTO v_model_workspace
        FROM semantic_models
        WHERE semantic_model_id = NEW.semantic_model_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION
                'Referenced semantic model does not exist';
        END IF;

        IF v_model_workspace <> NEW.workspace_id THEN
            RAISE EXCEPTION
                'Report and semantic model must belong to the same workspace';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_artifact_model
BEFORE INSERT OR UPDATE ON artifacts
FOR EACH ROW
EXECUTE FUNCTION powerbi.validate_artifact_model();

-- ============================================================
-- 14. AUTOMATIC AUDIT ON ARTIFACT PUBLICATION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.audit_artifact_publication()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_organization_id BIGINT;
BEGIN
    SELECT organization_id
    INTO v_organization_id
    FROM workspaces
    WHERE workspace_id = NEW.workspace_id;

    INSERT INTO audit_events (
        organization_id,
        workspace_id,
        actor_id,
        action,
        resource_type,
        resource_id,
        event_details
    )
    VALUES (
        v_organization_id,
        NEW.workspace_id,
        NEW.owner_user_id,
        'ARTIFACT_PUBLISHED',
        NEW.artifact_kind::TEXT,
        NEW.artifact_id,
        jsonb_build_object(
            'artifact_name', NEW.artifact_name,
            'semantic_model_id', NEW.semantic_model_id
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_artifact_publication
AFTER INSERT ON artifacts
FOR EACH ROW
EXECUTE FUNCTION powerbi.audit_artifact_publication();

-- ============================================================
-- 15. REFRESH JOB STATE VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.validate_refresh_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'QUEUED' THEN
            RAISE EXCEPTION
                'A new refresh job must start in QUEUED state';
        END IF;

        RETURN NEW;
    END IF;

    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'QUEUED'
         AND NEW.status IN ('RUNNING', 'CANCELLED'))
        OR
        (OLD.status = 'RUNNING'
         AND NEW.status IN ('COMPLETED', 'FAILED'))
    ) THEN
        RAISE EXCEPTION
            'Invalid refresh state transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'RUNNING' THEN
        NEW.started_at := COALESCE(
            NEW.started_at,
            CURRENT_TIMESTAMP
        );
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at := COALESCE(
            NEW.completed_at,
            CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_refresh_transition
BEFORE INSERT OR UPDATE OF status ON refresh_jobs
FOR EACH ROW
EXECUTE FUNCTION powerbi.validate_refresh_transition();

-- ============================================================
-- 16. REFRESH ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.refresh_eligibility(
    p_model_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_model semantic_models%ROWTYPE;
    v_source data_sources%ROWTYPE;
    v_gateway_online BOOLEAN;
    v_mapping_configured BOOLEAN;
BEGIN
    SELECT *
    INTO v_model
    FROM semantic_models
    WHERE semantic_model_id = p_model_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Semantic model does not exist';
        RETURN;
    END IF;

    IF NOT v_model.refresh_enabled THEN
        RETURN QUERY
        SELECT FALSE, 'Refresh is disabled';
        RETURN;
    END IF;

    IF NOT v_model.credentials_configured THEN
        RETURN QUERY
        SELECT FALSE, 'Data source credentials are missing';
        RETURN;
    END IF;

    SELECT *
    INTO v_source
    FROM data_sources
    WHERE data_source_id = v_model.data_source_id;

    IF NOT FOUND OR NOT v_source.enabled THEN
        RETURN QUERY
        SELECT FALSE, 'Data source is unavailable';
        RETURN;
    END IF;

    IF v_source.gateway_required THEN
        IF v_model.gateway_id IS NULL THEN
            RETURN QUERY
            SELECT FALSE, 'No gateway assigned';
            RETURN;
        END IF;

        SELECT online AND enabled
        INTO v_gateway_online
        FROM gateways
        WHERE gateway_id = v_model.gateway_id;

        IF NOT FOUND OR NOT v_gateway_online THEN
            RETURN QUERY
            SELECT FALSE, 'Gateway is offline or disabled';
            RETURN;
        END IF;

        SELECT configured
        INTO v_mapping_configured
        FROM gateway_source_mappings
        WHERE gateway_id = v_model.gateway_id
          AND data_source_id = v_model.data_source_id;

        IF NOT FOUND OR NOT v_mapping_configured THEN
            RETURN QUERY
            SELECT FALSE, 'Gateway source mapping is not configured';
            RETURN;
        END IF;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'Refresh prerequisites satisfied';
END;
$$;

-- ============================================================
-- 17. QUEUE REFRESH PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE powerbi.queue_refresh(
    p_model_id BIGINT,
    p_requested_by BIGINT,
    OUT p_refresh_job_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_eligible BOOLEAN;
    v_reason TEXT;
BEGIN
    SELECT eligible, reason
    INTO v_eligible, v_reason
    FROM refresh_eligibility(p_model_id);

    IF NOT COALESCE(v_eligible, FALSE) THEN
        RAISE EXCEPTION 'Refresh rejected: %', v_reason;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM users
        WHERE user_id = p_requested_by
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Requester is not an active user';
    END IF;

    INSERT INTO refresh_jobs (
        semantic_model_id,
        requested_by,
        status
    )
    VALUES (
        p_model_id,
        p_requested_by,
        'QUEUED'
    )
    RETURNING refresh_job_id INTO p_refresh_job_id;

    INSERT INTO audit_events (
        organization_id,
        workspace_id,
        actor_id,
        action,
        resource_type,
        resource_id,
        event_details
    )
    SELECT
        w.organization_id,
        w.workspace_id,
        p_requested_by,
        'REFRESH_QUEUED',
        'SEMANTIC_MODEL',
        p_model_id,
        jsonb_build_object(
            'refresh_job_id', p_refresh_job_id
        )
    FROM semantic_models sm
    JOIN workspaces w
      ON w.workspace_id = sm.workspace_id
    WHERE sm.semantic_model_id = p_model_id;
END;
$$;

-- ============================================================
-- 18. REFRESH COMPLETION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE powerbi.complete_refresh(
    p_refresh_job_id BIGINT,
    p_success BOOLEAN,
    p_rows_processed BIGINT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_model_id BIGINT;
    v_organization_id BIGINT;
    v_workspace_id BIGINT;
    v_actor_id BIGINT;
BEGIN
    SELECT
        r.semantic_model_id,
        r.requested_by,
        sm.workspace_id,
        w.organization_id
    INTO
        v_model_id,
        v_actor_id,
        v_workspace_id,
        v_organization_id
    FROM refresh_jobs r
    JOIN semantic_models sm
      ON sm.semantic_model_id = r.semantic_model_id
    JOIN workspaces w
      ON w.workspace_id = sm.workspace_id
    WHERE r.refresh_job_id = p_refresh_job_id
    FOR UPDATE OF r;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Refresh job does not exist';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM refresh_jobs
        WHERE refresh_job_id = p_refresh_job_id
          AND status = 'RUNNING'
    ) THEN
        RAISE EXCEPTION
            'Only RUNNING refresh jobs can be completed';
    END IF;

    IF p_rows_processed < 0 THEN
        RAISE EXCEPTION 'Processed rows cannot be negative';
    END IF;

    UPDATE refresh_jobs
    SET
        status = CASE
            WHEN p_success THEN 'COMPLETED'::refresh_status
            ELSE 'FAILED'::refresh_status
        END,
        completed_at = CURRENT_TIMESTAMP,
        rows_processed = p_rows_processed,
        error_message = CASE
            WHEN p_success THEN NULL
            ELSE COALESCE(
                p_error_message,
                'Unspecified refresh failure'
            )
        END
    WHERE refresh_job_id = p_refresh_job_id;

    UPDATE semantic_models
    SET
        last_refresh_at = CASE
            WHEN p_success THEN CURRENT_TIMESTAMP
            ELSE last_refresh_at
        END,
        last_refresh_status = CASE
            WHEN p_success THEN 'COMPLETED'::refresh_status
            ELSE 'FAILED'::refresh_status
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE semantic_model_id = v_model_id;

    INSERT INTO audit_events (
        organization_id,
        workspace_id,
        actor_id,
        action,
        resource_type,
        resource_id,
        event_details
    )
    VALUES (
        v_organization_id,
        v_workspace_id,
        v_actor_id,
        'REFRESH_FINISHED',
        'SEMANTIC_MODEL',
        v_model_id,
        jsonb_build_object(
            'refresh_job_id', p_refresh_job_id,
            'success', p_success,
            'rows_processed', p_rows_processed,
            'error', p_error_message
        )
    );
END;
$$;

-- ============================================================
-- 19. WORKSPACE ADMINISTRATOR PROTECTION
-- ============================================================

CREATE OR REPLACE FUNCTION powerbi.protect_last_admin()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_admin_count BIGINT;
BEGIN
    IF OLD.role = 'ADMIN'
       AND (
           TG_OP = 'DELETE'
           OR NEW.role <> 'ADMIN'
           OR NEW.active = FALSE
       ) THEN

        SELECT COUNT(*)
        INTO v_admin_count
        FROM workspace_members
        WHERE workspace_id = OLD.workspace_id
          AND role = 'ADMIN'
          AND active = TRUE
          AND user_id <> OLD.user_id;

        IF v_admin_count = 0 THEN
            RAISE EXCEPTION
                'A workspace must retain at least one active administrator';
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protect_last_admin
BEFORE UPDATE OR DELETE ON workspace_members
FOR EACH ROW
EXECUTE FUNCTION powerbi.protect_last_admin();

-- ============================================================
-- 20. WORKSPACE GOVERNANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW powerbi.workspace_governance AS
SELECT
    w.workspace_id,
    w.workspace_name,
    w.capacity,
    w.active,
    COUNT(DISTINCT wm.user_id)
        FILTER (WHERE wm.active) AS active_members,
    COUNT(DISTINCT sm.semantic_model_id) AS semantic_models,
    COUNT(DISTINCT a.artifact_id)
        FILTER (WHERE a.artifact_kind = 'REPORT') AS reports,
    COUNT(DISTINCT a.artifact_id)
        FILTER (WHERE a.artifact_kind = 'DASHBOARD') AS dashboards,
    COUNT(DISTINCT r.refresh_job_id)
        FILTER (WHERE r.status = 'FAILED') AS failed_refreshes,
    COUNT(DISTINCT r.refresh_job_id)
        FILTER (WHERE r.status = 'COMPLETED') AS successful_refreshes
FROM workspaces w
LEFT JOIN workspace_members wm
    ON wm.workspace_id = w.workspace_id
LEFT JOIN semantic_models sm
    ON sm.workspace_id = w.workspace_id
LEFT JOIN artifacts a
    ON a.workspace_id = w.workspace_id
LEFT JOIN refresh_jobs r
    ON r.semantic_model_id = sm.semantic_model_id
GROUP BY
    w.workspace_id,
    w.workspace_name,
    w.capacity,
    w.active;

-- ============================================================
-- 21. REFRESH HEALTH VIEW
-- ============================================================

CREATE OR REPLACE VIEW powerbi.refresh_health AS
SELECT
    sm.semantic_model_id,
    sm.model_name,
    sm.workspace_id,
    sm.refresh_enabled,
    sm.last_refresh_at,
    sm.last_refresh_status,
    COUNT(r.refresh_job_id) AS total_refreshes,
    COUNT(r.refresh_job_id)
        FILTER (WHERE r.status = 'FAILED') AS failures,
    COUNT(r.refresh_job_id)
        FILTER (WHERE r.status = 'COMPLETED') AS successes,
    MAX(r.completed_at) AS latest_completion
FROM semantic_models sm
LEFT JOIN refresh_jobs r
    ON r.semantic_model_id = sm.semantic_model_id
GROUP BY
    sm.semantic_model_id,
    sm.model_name,
    sm.workspace_id,
    sm.refresh_enabled,
    sm.last_refresh_at,
    sm.last_refresh_status;

-- ============================================================
-- 22. SAMPLE ORGANIZATION AND USERS
-- ============================================================

INSERT INTO organizations (organization_name)
VALUES ('Enterprise Analytics Group');

INSERT INTO users (
    organization_id,
    email,
    display_name
)
VALUES
(
    1,
    'admin@enterprise.example',
    'Platform Administrator'
),
(
    1,
    'analyst@enterprise.example',
    'Data Analyst'
),
(
    1,
    'executive@enterprise.example',
    'Executive Viewer'
),
(
    1,
    'engineer@enterprise.example',
    'Data Engineer'
);

-- ============================================================
-- 23. SAMPLE WORKSPACE
-- ============================================================

INSERT INTO workspaces (
    organization_id,
    workspace_name,
    capacity,
    owner_user_id,
    description
)
VALUES (
    1,
    'Enterprise Sales Analytics',
    'PREMIUM',
    1,
    'Enterprise sales reporting and semantic model management'
);

INSERT INTO workspace_members (
    workspace_id,
    user_id,
    role,
    added_by
)
VALUES
(1, 1, 'ADMIN', 1),
(1, 2, 'CONTRIBUTOR', 1),
(1, 3, 'VIEWER', 1),
(1, 4, 'MEMBER', 1);

-- ============================================================
-- 24. DATA SOURCE AND GATEWAY
-- ============================================================

INSERT INTO data_sources (
    organization_id,
    source_name,
    source_type,
    connection_class,
    endpoint_description,
    gateway_required,
    enabled
)
VALUES
(
    1,
    'Enterprise Sales SQL',
    'SQL_SERVER',
    'ON_PREMISES',
    'Internal enterprise SQL database',
    TRUE,
    TRUE
),
(
    1,
    'Cloud Marketing Data',
    'AZURE_SQL',
    'CLOUD',
    'Cloud-hosted marketing database',
    FALSE,
    TRUE
);

INSERT INTO gateways (
    organization_id,
    gateway_name,
    machine_name,
    cluster_name,
    online,
    enabled,
    last_seen_at
)
VALUES (
    1,
    'Enterprise Gateway',
    'BI-GATEWAY-01',
    'PRODUCTION-CLUSTER',
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP
);

INSERT INTO gateway_source_mappings (
    gateway_id,
    data_source_id,
    configured,
    credential_reference,
    last_validated_at
)
VALUES (
    1,
    1,
    TRUE,
    'secret://enterprise/sql/sales',
    CURRENT_TIMESTAMP
);

-- ============================================================
-- 25. SEMANTIC MODELS
-- ============================================================

INSERT INTO semantic_models (
    workspace_id,
    data_source_id,
    gateway_id,
    model_name,
    owner_user_id,
    description,
    storage_mode,
    credentials_configured,
    refresh_enabled,
    refresh_interval_hours
)
VALUES
(
    1,
    1,
    1,
    'Sales Semantic Model',
    2,
    'Sales facts and customer dimensions',
    'IMPORT',
    TRUE,
    TRUE,
    24
),
(
    1,
    2,
    NULL,
    'Marketing Semantic Model',
    2,
    'Cloud marketing metrics',
    'DIRECTQUERY',
    TRUE,
    TRUE,
    12
);

INSERT INTO semantic_model_tables (
    semantic_model_id,
    table_name,
    is_hidden
)
VALUES
(1, 'FactSales', FALSE),
(1, 'DimCustomer', FALSE),
(1, 'DimProduct', FALSE),
(1, 'DimDate', TRUE),
(2, 'FactCampaign', FALSE),
(2, 'DimChannel', FALSE);

-- ============================================================
-- 26. REPORTS AND DASHBOARDS
-- ============================================================

INSERT INTO artifacts (
    workspace_id,
    semantic_model_id,
    artifact_name,
    artifact_kind,
    owner_user_id,
    description,
    published_at
)
VALUES
(
    1,
    1,
    'Executive Sales Report',
    'REPORT',
    2,
    'Sales performance by region and product',
    CURRENT_TIMESTAMP
),
(
    1,
    2,
    'Marketing Performance Report',
    'REPORT',
    2,
    'Campaign performance and acquisition metrics',
    CURRENT_TIMESTAMP
),
(
    1,
    NULL,
    'Executive Operations Dashboard',
    'DASHBOARD',
    1,
    'High-level organizational KPI dashboard',
    CURRENT_TIMESTAMP
);

-- Publication history.
INSERT INTO publication_history (
    artifact_id,
    published_by,
    publication_version,
    source_branch,
    source_commit
)
VALUES
(1, 2, 1, 'main', 'a1b2c3d4'),
(1, 2, 2, 'main', 'e5f6a7b8'),
(2, 2, 1, 'main', 'c1d2e3f4'),
(3, 1, 1, 'main', 'd5e6f7a8');

-- ============================================================
-- 27. ITEM-LEVEL SHARING
-- ============================================================

INSERT INTO item_permissions (
    semantic_model_id,
    user_id,
    permission,
    granted_by,
    expires_at
)
VALUES
(1, 3, 'VIEW', 1, CURRENT_TIMESTAMP + INTERVAL '30 days'),
(1, 3, 'BUILD', 1, CURRENT_TIMESTAMP + INTERVAL '30 days'),
(2, 3, 'VIEW', 1, CURRENT_TIMESTAMP + INTERVAL '30 days'),
(1, 4, 'BUILD', 1, NULL);

INSERT INTO item_permissions (
    artifact_id,
    user_id,
    permission,
    granted_by
)
VALUES
(1, 3, 'VIEW', 1),
(3, 3, 'VIEW', 1);

-- ============================================================
-- 28. REFRESH SCHEDULES
-- ============================================================

INSERT INTO refresh_schedules (
    semantic_model_id,
    schedule_name,
    enabled,
    timezone_name,
    frequency,
    scheduled_time,
    next_run_at
)
VALUES
(
    1,
    'Daily Sales Refresh',
    TRUE,
    'Asia/Kolkata',
    'DAILY',
    '02:00',
    CURRENT_TIMESTAMP + INTERVAL '1 day'
),
(
    2,
    'Marketing Twelve Hour Refresh',
    TRUE,
    'Asia/Kolkata',
    'HOURLY',
    '03:00',
    CURRENT_TIMESTAMP + INTERVAL '12 hours'
);

-- ============================================================
-- 29. REFRESH EXECUTION EXAMPLES
-- ============================================================

-- First successful refresh.
INSERT INTO refresh_jobs (
    semantic_model_id,
    requested_by,
    status,
    requested_at,
    started_at,
    completed_at,
    rows_processed
)
VALUES (
    1,
    2,
    'COMPLETED',
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    CURRENT_TIMESTAMP - INTERVAL '115 minutes',
    CURRENT_TIMESTAMP - INTERVAL '110 minutes',
    125000
);

UPDATE semantic_models
SET
    last_refresh_at = CURRENT_TIMESTAMP - INTERVAL '110 minutes',
    last_refresh_status = 'COMPLETED'
WHERE semantic_model_id = 1;

-- Failed refresh.
INSERT INTO refresh_jobs (
    semantic_model_id,
    requested_by,
    status,
    requested_at,
    started_at,
    completed_at,
    error_code,
    error_message
)
VALUES (
    2,
    2,
    'FAILED',
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    CURRENT_TIMESTAMP - INTERVAL '55 minutes',
    CURRENT_TIMESTAMP - INTERVAL '50 minutes',
    'SOURCE_TIMEOUT',
    'Cloud source connection timed out'
);

UPDATE semantic_models
SET last_refresh_status = 'FAILED'
WHERE semantic_model_id = 2;

-- ============================================================
-- 30. SAMPLE AUDIT EVENTS
-- ============================================================

INSERT INTO audit_events (
    organization_id,
    workspace_id,
    actor_id,
    action,
    resource_type,
    resource_id,
    event_details
)
VALUES
(
    1, 1, 1,
    'WORKSPACE_CREATED',
    'WORKSPACE', 1,
    '{"capacity":"PREMIUM"}'
),
(
    1, 1, 1,
    'MEMBER_ADDED',
    'USER', 2,
    '{"role":"CONTRIBUTOR"}'
),
(
    1, 1, 2,
    'MODEL_PUBLISHED',
    'SEMANTIC_MODEL', 1,
    '{"model_name":"Sales Semantic Model"}'
),
(
    1, 1, 1,
    'PERMISSION_GRANTED',
    'SEMANTIC_MODEL', 1,
    '{"user_id":3,"permission":"BUILD"}'
);

-- ============================================================
-- 31. RETRIEVAL: WORKSPACE CONTENTS
-- ============================================================

SELECT
    w.workspace_name,
    w.capacity,
    a.artifact_name,
    a.artifact_kind,
    sm.model_name
FROM workspaces w
LEFT JOIN artifacts a
    ON a.workspace_id = w.workspace_id
LEFT JOIN semantic_models sm
    ON sm.semantic_model_id = a.semantic_model_id
WHERE w.workspace_id = 1
ORDER BY a.artifact_name;

-- ============================================================
-- 32. RETRIEVAL: WORKSPACE MEMBERS AND ROLES
-- ============================================================

SELECT
    w.workspace_name,
    u.email,
    u.display_name,
    wm.role,
    wm.active
FROM workspace_members wm
JOIN users u
    ON u.user_id = wm.user_id
JOIN workspaces w
    ON w.workspace_id = wm.workspace_id
WHERE wm.workspace_id = 1
ORDER BY wm.role, u.email;

-- ============================================================
-- 33. EVALUATION: EFFECTIVE SEMANTIC MODEL PERMISSIONS
-- ============================================================

SELECT
    u.email,
    sm.model_name,
    p.permission,
    has_item_permission(
        sm.workspace_id,
        u.user_id,
        sm.semantic_model_id,
        NULL,
        p.permission
    ) AS permitted
FROM users u
CROSS JOIN semantic_models sm
CROSS JOIN unnest(
    ARRAY[
        'VIEW'::permission_type,
        'BUILD'::permission_type,
        'WRITE'::permission_type,
        'RESHARE'::permission_type
    ]
) AS p(permission)
WHERE sm.workspace_id = 1
ORDER BY u.email, sm.model_name, p.permission;

-- ============================================================
-- 34. VALIDATION: REFRESH ELIGIBILITY
-- ============================================================

SELECT
    sm.model_name,
    eligibility.eligible,
    eligibility.reason
FROM semantic_models sm
CROSS JOIN LATERAL refresh_eligibility(
    sm.semantic_model_id
) AS eligibility;

-- ============================================================
-- 35. AGGREGATION: WORKSPACE GOVERNANCE
-- ============================================================

SELECT *
FROM workspace_governance
ORDER BY workspace_name;

-- ============================================================
-- 36. AGGREGATION: REFRESH HEALTH
-- ============================================================

SELECT
    model_name,
    total_refreshes,
    successes,
    failures,
    CASE
        WHEN total_refreshes = 0 THEN 0
        ELSE ROUND(
            100.0 * successes / total_refreshes,
            2
        )
    END AS success_percentage,
    latest_completion
FROM refresh_health
ORDER BY model_name;

-- ============================================================
-- 37. REPORT: PUBLICATION VERSIONS
-- ============================================================

SELECT
    a.artifact_name,
    ph.publication_version,
    u.email AS published_by,
    ph.source_branch,
    ph.source_commit,
    ph.status,
    ph.published_at
FROM publication_history ph
JOIN artifacts a
    ON a.artifact_id = ph.artifact_id
JOIN users u
    ON u.user_id = ph.published_by
ORDER BY
    a.artifact_name,
    ph.publication_version DESC;

-- ============================================================
-- 38. REPORT: FAILED REFRESHES
-- ============================================================

SELECT
    sm.model_name,
    r.requested_at,
    r.completed_at,
    r.error_code,
    r.error_message
FROM refresh_jobs r
JOIN semantic_models sm
    ON sm.semantic_model_id = r.semantic_model_id
WHERE r.status = 'FAILED'
ORDER BY r.requested_at DESC;

-- ============================================================
-- 39. REPORT: WORKSPACES WITH EXCESSIVE SHARING
-- ============================================================

SELECT
    w.workspace_name,
    COUNT(DISTINCT ip.user_id) AS external_item_grantees,
    COUNT(ip.permission_id) AS permission_records
FROM workspaces w
LEFT JOIN semantic_models sm
    ON sm.workspace_id = w.workspace_id
LEFT JOIN item_permissions ip
    ON ip.semantic_model_id = sm.semantic_model_id
   AND ip.active = TRUE
   AND (
       ip.expires_at IS NULL
       OR ip.expires_at > CURRENT_TIMESTAMP
   )
GROUP BY w.workspace_id, w.workspace_name
ORDER BY external_item_grantees DESC;

-- ============================================================
-- 40. CTE: MODELS REQUIRING OPERATIONAL ATTENTION
-- ============================================================

WITH latest_refresh AS (
    SELECT
        semantic_model_id,
        MAX(requested_at) AS latest_requested_at
    FROM refresh_jobs
    GROUP BY semantic_model_id
),
model_status AS (
    SELECT
        sm.semantic_model_id,
        sm.model_name,
        sm.refresh_enabled,
        lr.latest_requested_at,
        r.status,
        r.error_message
    FROM semantic_models sm
    LEFT JOIN latest_refresh lr
        ON lr.semantic_model_id = sm.semantic_model_id
    LEFT JOIN refresh_jobs r
        ON r.semantic_model_id = sm.semantic_model_id
       AND r.requested_at = lr.latest_requested_at
)
SELECT *
FROM model_status
WHERE refresh_enabled = FALSE
   OR status = 'FAILED'
   OR latest_requested_at IS NULL;

-- ============================================================
-- 41. WORKFLOW: QUEUE A NEW REFRESH
-- ============================================================

DO $$
DECLARE
    v_refresh_id BIGINT;
BEGIN
    CALL queue_refresh(1, 2, v_refresh_id);

    RAISE NOTICE 'Queued refresh job: %', v_refresh_id;
END;
$$;

-- ============================================================
-- 42. WORKFLOW: START AND COMPLETE A REFRESH
-- ============================================================

DO $$
DECLARE
    v_job_id BIGINT;
BEGIN
    SELECT refresh_job_id
    INTO v_job_id
    FROM refresh_jobs
    WHERE semantic_model_id = 1
      AND status = 'QUEUED'
    ORDER BY requested_at
    LIMIT 1
    FOR UPDATE;

    IF v_job_id IS NOT NULL THEN
        UPDATE refresh_jobs
        SET status = 'RUNNING'
        WHERE refresh_job_id = v_job_id;

        CALL complete_refresh(
            v_job_id,
            TRUE,
            130000,
            NULL
        );

        RAISE NOTICE 'Completed refresh: %', v_job_id;
    END IF;
END;
$$;

-- ============================================================
-- 43. TRANSACTION: GRANT BUILD ACCESS
-- ============================================================

SAVEPOINT before_build_grant;

INSERT INTO item_permissions (
    semantic_model_id,
    user_id,
    permission,
    granted_by,
    expires_at
)
VALUES (
    2,
    3,
    'BUILD',
    1,
    CURRENT_TIMESTAMP + INTERVAL '7 days'
)
ON CONFLICT DO NOTHING;

-- Validate that the permission exists.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM item_permissions
        WHERE semantic_model_id = 2
          AND user_id = 3
          AND permission = 'BUILD'
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Build grant validation failed';
    END IF;
END;
$$;

RELEASE SAVEPOINT before_build_grant;

-- ============================================================
-- 44. FAILURE EXAMPLE: INVALID REPORT PUBLICATION
-- ============================================================

-- This statement is intentionally excluded from the main
-- executable transaction because it must fail.
--
-- INSERT INTO artifacts (
--     workspace_id,
--     semantic_model_id,
--     artifact_name,
--     artifact_kind,
--     owner_user_id
-- )
-- VALUES (1, NULL, 'Invalid Report', 'REPORT', 2);
--
-- The trigger and CHECK constraint reject the operation.

-- ============================================================
-- 45. FAILURE EXAMPLE: INVALID REFRESH TRANSITION
-- ============================================================

-- A direct QUEUED -> COMPLETED transition is rejected.
--
-- UPDATE refresh_jobs
-- SET status = 'COMPLETED'
-- WHERE refresh_job_id = 1
--   AND status = 'QUEUED';

-- ============================================================
-- 46. FINAL DATA INTEGRITY CHECKS
-- ============================================================

-- Models without source tables.
SELECT
    sm.semantic_model_id,
    sm.model_name
FROM semantic_models sm
LEFT JOIN semantic_model_tables mt
    ON mt.semantic_model_id = sm.semantic_model_id
GROUP BY sm.semantic_model_id, sm.model_name
HAVING COUNT(mt.model_table_id) = 0;

-- Reports with missing model references.
SELECT
    a.artifact_id,
    a.artifact_name
FROM artifacts a
LEFT JOIN semantic_models sm
    ON sm.semantic_model_id = a.semantic_model_id
WHERE a.artifact_kind = 'REPORT'
  AND sm.semantic_model_id IS NULL;

-- Active users with no workspace membership.
SELECT
    u.user_id,
    u.email
FROM users u
LEFT JOIN workspace_members wm
    ON wm.user_id = u.user_id
   AND wm.active = TRUE
WHERE u.active = TRUE
GROUP BY u.user_id, u.email
HAVING COUNT(wm.workspace_id) = 0;

-- ============================================================
-- 47. COMMIT
-- ============================================================

COMMIT;
