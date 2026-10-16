-- PostgreSQL 15+ file-ingestion registry for operational asset exports.
--
-- The database stores file metadata, import runs, accepted asset records,
-- rejected rows, and aggregate reporting results. PostgreSQL does not parse
-- local CSV or JSON files through ordinary INSERT statements; a trusted
-- application or COPY operation supplies records to this relational model.
--
-- Run using psql against a database where the executing role may create tables.

BEGIN;

CREATE SCHEMA IF NOT EXISTS file_lab;
SET LOCAL search_path TO file_lab, public;

CREATE TABLE IF NOT EXISTS source_file (
    file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    relative_path TEXT NOT NULL,
    file_format TEXT NOT NULL
        CHECK (file_format IN ('TXT', 'CSV', 'JSON', 'BINARY')),
    encoding_name TEXT,
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    sha256_hex TEXT
        CHECK (sha256_hex IS NULL OR sha256_hex ~ '^[0-9a-f]{64}$'),
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT source_path_not_empty CHECK (length(trim(relative_path)) > 0),
    CONSTRAINT source_path_relative CHECK (
        relative_path !~ '^/' AND
        relative_path !~ '(^|/)\.\.(/|$)' AND
        relative_path !~ '^[A-Za-z]:'
    ),
    CONSTRAINT source_path_unique UNIQUE (relative_path, sha256_hex)
);

CREATE TABLE IF NOT EXISTS import_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    file_id BIGINT NOT NULL REFERENCES source_file(file_id),
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN (
            'PENDING', 'PROCESSING', 'COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED'
        )),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    total_rows INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
    accepted_rows INTEGER NOT NULL DEFAULT 0 CHECK (accepted_rows >= 0),
    rejected_rows INTEGER NOT NULL DEFAULT 0 CHECK (rejected_rows >= 0),
    error_message TEXT,
    CONSTRAINT run_time_order CHECK (
        finished_at IS NULL OR
        (started_at IS NOT NULL AND finished_at >= started_at)
    ),
    CONSTRAINT row_count_consistency CHECK (
        accepted_rows + rejected_rows <= total_rows
    ),
    CONSTRAINT completed_run_has_end_time CHECK (
        status NOT IN ('COMPLETED', 'COMPLETED_WITH_ERRORS')
        OR finished_at IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS import_run_file_status_idx
    ON import_run (file_id, status, started_at DESC);

CREATE TABLE IF NOT EXISTS asset (
    asset_id TEXT PRIMARY KEY
        CHECK (asset_id ~ '^AST-[0-9]{4,8}$'),
    department TEXT NOT NULL
        CHECK (length(trim(department)) BETWEEN 1 AND 80),
    replacement_cost NUMERIC(14, 2) NOT NULL
        CHECK (replacement_cost >= 0),
    source_run_id BIGINT NOT NULL REFERENCES import_run(run_id),
    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS asset_department_idx
    ON asset (department);

CREATE TABLE IF NOT EXISTS rejected_record (
    rejected_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES import_run(run_id) ON DELETE CASCADE,
    record_number INTEGER NOT NULL CHECK (record_number > 0),
    raw_record TEXT NOT NULL,
    rejection_reason TEXT NOT NULL
        CHECK (length(trim(rejection_reason)) > 0),
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rejected_record_unique UNIQUE (run_id, record_number)
);

CREATE INDEX IF NOT EXISTS rejected_record_run_idx
    ON rejected_record (run_id, record_number);

CREATE OR REPLACE FUNCTION enforce_import_run_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED')
       AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION
            'Terminal import status % cannot transition to %',
            OLD.status, NEW.status;
    END IF;

    IF OLD.status = 'PENDING'
       AND NEW.status NOT IN ('PENDING', 'PROCESSING', 'FAILED') THEN
        RAISE EXCEPTION 'PENDING run must start processing or fail';
    END IF;

    IF OLD.status = 'PROCESSING'
       AND NEW.status NOT IN (
           'PROCESSING', 'COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED'
       ) THEN
        RAISE EXCEPTION 'Invalid PROCESSING status transition';
    END IF;

    IF NEW.accepted_rows + NEW.rejected_rows > NEW.total_rows THEN
        RAISE EXCEPTION 'Accepted and rejected rows exceed total rows';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS import_run_transition_guard ON import_run;

CREATE TRIGGER import_run_transition_guard
BEFORE UPDATE ON import_run
FOR EACH ROW
EXECUTE FUNCTION enforce_import_run_transition();

CREATE OR REPLACE VIEW department_asset_summary AS
SELECT
    department,
    COUNT(*) AS asset_count,
    SUM(replacement_cost) AS total_replacement_cost,
    ROUND(AVG(replacement_cost), 2) AS average_replacement_cost,
    MAX(replacement_cost) AS highest_replacement_cost
FROM asset
GROUP BY department;

-- Record realistic input files. The hash is optional because duplicate
-- content and duplicate paths are separate operational concerns.
INSERT INTO source_file (
    relative_path, file_format, encoding_name, byte_size, sha256_hex
)
VALUES
    ('input/assets.csv', 'CSV', 'UTF-8', 512, NULL),
    ('input/service_notes.txt', 'TXT', 'UTF-8', 128, NULL),
    ('input/service_config.json', 'JSON', 'UTF-8', 256, NULL)
ON CONFLICT (relative_path, sha256_hex) DO NOTHING;

-- Sample import run is linked to the CSV metadata. The demonstration is
-- repeatable because its data is isolated by the relative file path.
INSERT INTO import_run (
    file_id, status, started_at, finished_at,
    total_rows, accepted_rows, rejected_rows, error_message
)
SELECT
    file_id,
    'COMPLETED_WITH_ERRORS',
    CURRENT_TIMESTAMP - INTERVAL '2 minutes',
    CURRENT_TIMESTAMP,
    5,
    3,
    2,
    'Two source rows failed validation.'
FROM source_file
WHERE relative_path = 'input/assets.csv'
ON CONFLICT DO NOTHING;

-- The example rows are inserted only if they do not already exist. A
-- production importer should use a stable import idempotency key and a
-- transaction covering run creation, record validation, and final status.
INSERT INTO asset (
    asset_id, department, replacement_cost, source_run_id
)
SELECT sample.asset_id, sample.department, sample.replacement_cost, run.run_id
FROM (
    VALUES
        ('AST-1001', 'Water Operations', 45000.50::NUMERIC),
        ('AST-1002', 'Power Operations', 175000.00::NUMERIC),
        ('AST-1003', 'Water Operations', 62000.00::NUMERIC)
) AS sample(asset_id, department, replacement_cost)
JOIN import_run AS run
  ON run.file_id = (
      SELECT file_id
      FROM source_file
      WHERE relative_path = 'input/assets.csv'
      LIMIT 1
  )
ON CONFLICT (asset_id) DO NOTHING;

INSERT INTO rejected_record (
    run_id, record_number, raw_record, rejection_reason
)
SELECT run.run_id, sample.record_number, sample.raw_record, sample.reason
FROM import_run AS run
JOIN source_file AS source ON source.file_id = run.file_id
CROSS JOIN (
    VALUES
        (
            5,
            'AST-1004,Power Operations,-25.00',
            'Replacement cost cannot be negative.'
        ),
        (
            6,
            'AST-1001,Water Operations,100.00',
            'Duplicate asset identifier.'
        )
) AS sample(record_number, raw_record, reason)
WHERE source.relative_path = 'input/assets.csv'
ON CONFLICT (run_id, record_number) DO NOTHING;

-- Query accepted operational data using the department aggregation view.
SELECT
    department,
    asset_count,
    total_replacement_cost,
    average_replacement_cost,
    highest_replacement_cost
FROM department_asset_summary
ORDER BY total_replacement_cost DESC;

-- Compare the source row count with accepted and rejected records.
SELECT
    source.relative_path,
    run.status,
    run.total_rows,
    run.accepted_rows,
    run.rejected_rows,
    run.accepted_rows + run.rejected_rows AS classified_rows,
    run.total_rows - run.accepted_rows - run.rejected_rows AS unclassified_rows
FROM import_run AS run
JOIN source_file AS source ON source.file_id = run.file_id
ORDER BY run.run_id;

-- Use a CTE to identify failed source rows without exposing unrelated files.
WITH latest_run AS (
    SELECT DISTINCT ON (file_id)
        run_id, file_id, status, started_at
    FROM import_run
    ORDER BY file_id, started_at DESC NULLS LAST, run_id DESC
)
SELECT
    source.relative_path,
    latest.status AS import_status,
    rejected.record_number,
    rejected.rejection_reason,
    rejected.raw_record
FROM latest_run AS latest
JOIN source_file AS source ON source.file_id = latest.file_id
JOIN rejected_record AS rejected ON rejected.run_id = latest.run_id
ORDER BY source.relative_path, rejected.record_number;

-- Demonstrate transactional integrity. The attempted invalid asset would
-- violate the non-negative cost constraint, so the savepoint lets the script
-- continue while the database rejects the record.
SAVEPOINT invalid_asset_test;

DO $$
BEGIN
    BEGIN
        INSERT INTO asset (
            asset_id, department, replacement_cost, source_run_id
        )
        SELECT
            'AST-9999', 'Testing', -10.00, run.run_id
        FROM import_run AS run
        JOIN source_file AS source ON source.file_id = run.file_id
        WHERE source.relative_path = 'input/assets.csv'
        ORDER BY run.run_id
        LIMIT 1;

        RAISE EXCEPTION 'Expected the negative-cost constraint to reject the row';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Expected check constraint rejected negative cost';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_asset_test;
RELEASE SAVEPOINT invalid_asset_test;

-- Demonstrate a valid status transition from PROCESSING to COMPLETED.
-- The example uses a separate file and run to avoid changing the imported
-- sample run that already records validation errors.
INSERT INTO import_run (
    file_id, status, started_at, total_rows
)
SELECT file_id, 'PENDING', CURRENT_TIMESTAMP, 0
FROM source_file
WHERE relative_path = 'input/service_notes.txt'
RETURNING run_id;

UPDATE import_run
SET status = 'PROCESSING'
WHERE file_id = (
    SELECT file_id FROM source_file
    WHERE relative_path = 'input/service_notes.txt'
)
AND status = 'PENDING';

UPDATE import_run
SET status = 'COMPLETED',
    finished_at = CURRENT_TIMESTAMP
WHERE file_id = (
    SELECT file_id FROM source_file
    WHERE relative_path = 'input/service_notes.txt'
)
AND status = 'PROCESSING';

COMMIT;
