DROP SCHEMA IF EXISTS numpy_advanced_demo CASCADE;
CREATE SCHEMA numpy_advanced_demo;
SET search_path TO numpy_advanced_demo;

-- PostgreSQL is used because arrays, generate_series, CTEs, JSONB,
-- mathematical functions, constraints, and transactional behavior
-- provide useful relational support for numerical-array workflows.

CREATE TYPE dataset_status AS ENUM (
    'draft',
    'validated',
    'processed',
    'rejected'
);

CREATE TABLE datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    status dataset_status NOT NULL DEFAULT 'draft',
    row_count INTEGER NOT NULL CHECK (row_count > 0),
    column_count INTEGER NOT NULL CHECK (column_count > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE features (
    feature_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    feature_position INTEGER NOT NULL CHECK (feature_position >= 0),
    unit TEXT,
    UNIQUE (dataset_id, feature_name),
    UNIQUE (dataset_id, feature_position)
);

CREATE TABLE observations (
    observation_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    observation_position INTEGER NOT NULL CHECK (observation_position >= 0),
    values DOUBLE PRECISION[] NOT NULL,
    CONSTRAINT observation_values_not_empty
        CHECK (cardinality(values) > 0),
    UNIQUE (dataset_id, observation_position)
);

CREATE TABLE feature_weights (
    weight_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    feature_id BIGINT NOT NULL
        REFERENCES features(feature_id)
        ON DELETE CASCADE,
    weight DOUBLE PRECISION NOT NULL,
    UNIQUE (dataset_id, feature_id)
);

CREATE TABLE matrix_operations (
    operation_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    operation_type TEXT NOT NULL CHECK (
        operation_type IN (
            'broadcast',
            'aggregation',
            'reshape',
            'matrix_multiply',
            'random_generation',
            'standardization'
        )
    ),
    input_shape INTEGER[] NOT NULL,
    output_shape INTEGER[] NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT
);

CREATE TABLE matrix_results (
    result_id BIGSERIAL PRIMARY KEY,
    operation_id BIGINT NOT NULL
        REFERENCES matrix_operations(operation_id)
        ON DELETE CASCADE,
    result_values DOUBLE PRECISION[] NOT NULL,
    CHECK (cardinality(result_values) > 0)
);

CREATE INDEX idx_observations_dataset
    ON observations(dataset_id);

CREATE INDEX idx_features_dataset_position
    ON features(dataset_id, feature_position);

CREATE INDEX idx_operations_dataset_type
    ON matrix_operations(dataset_id, operation_type);

INSERT INTO datasets (
    dataset_name,
    status,
    row_count,
    column_count
)
VALUES (
    'repository-performance',
    'validated',
    5,
    4
);

INSERT INTO features (
    dataset_id,
    feature_name,
    feature_position,
    unit
)
VALUES
    (1, 'commit_count', 0, 'commits'),
    (1, 'review_count', 1, 'reviews'),
    (1, 'failure_rate', 2, 'ratio'),
    (1, 'delivery_score', 3, 'ratio');

INSERT INTO observations (
    dataset_id,
    observation_position,
    values
)
VALUES
    (1, 0, ARRAY[120.0, 18.0, 0.07, 0.92]),
    (1, 1, ARRAY[210.0, 25.0, 0.12, 0.88]),
    (1, 2, ARRAY[150.0, 11.0, 0.05, 0.95]),
    (1, 3, ARRAY[300.0, 31.0, 0.15, 0.84]),
    (1, 4, ARRAY[175.0, 20.0, 0.09, 0.90]);

INSERT INTO feature_weights (
    dataset_id,
    feature_id,
    weight
)
SELECT
    1,
    feature_id,
    CASE feature_position
        WHEN 0 THEN 0.40
        WHEN 1 THEN 0.30
        WHEN 2 THEN -0.20
        WHEN 3 THEN 0.50
    END
FROM features
WHERE dataset_id = 1;

-- PostgreSQL array subscripting gives direct access to vector components.
SELECT
    observation_position,
    values[1] AS commit_count,
    values[2] AS review_count,
    values[3] AS failure_rate,
    values[4] AS delivery_score
FROM observations
WHERE dataset_id = 1
ORDER BY observation_position;

-- Aggregation is performed across observations while retaining feature meaning.
WITH expanded AS (
    SELECT
        observation_position,
        values[1] AS commit_count,
        values[2] AS review_count,
        values[3] AS failure_rate,
        values[4] AS delivery_score
    FROM observations
    WHERE dataset_id = 1
)
SELECT
    AVG(commit_count) AS mean_commits,
    AVG(review_count) AS mean_reviews,
    AVG(failure_rate) AS mean_failure_rate,
    AVG(delivery_score) AS mean_delivery_score,
    MIN(commit_count) AS minimum_commits,
    MAX(commit_count) AS maximum_commits
FROM expanded;

-- PostgreSQL generate_subscripts lets the relational model inspect
-- each vector position without pretending that all positions have
-- the same semantic meaning.
SELECT
    o.observation_position,
    s AS feature_position,
    o.values[s] AS feature_value
FROM observations AS o
CROSS JOIN LATERAL generate_subscripts(o.values, 1) AS s
WHERE o.dataset_id = 1
ORDER BY o.observation_position, s;

-- Broadcast a feature vector across every observation.
-- Each observation vector has four elements, and the adjustment vector
-- has four elements, so element-wise multiplication is well-defined.
WITH adjustment AS (
    SELECT ARRAY[
        1.00::DOUBLE PRECISION,
        1.10::DOUBLE PRECISION,
        0.80::DOUBLE PRECISION,
        1.05::DOUBLE PRECISION
    ] AS factors
)
SELECT
    o.observation_position,
    ARRAY(
        SELECT o.values[i] * adjustment.factors[i]
        FROM generate_subscripts(o.values, 1) AS i
        ORDER BY i
    ) AS adjusted_values
FROM observations AS o
CROSS JOIN adjustment
WHERE o.dataset_id = 1
ORDER BY o.observation_position;

-- Weighted aggregation behaves like a vector dot product.
WITH weighted AS (
    SELECT
        o.observation_position,
        SUM(o.values[f.feature_position + 1] * f.weight) AS weighted_score
    FROM observations AS o
    JOIN feature_weights AS f
      ON f.dataset_id = o.dataset_id
    WHERE o.dataset_id = 1
    GROUP BY o.observation_position
)
SELECT *
FROM weighted
ORDER BY observation_position;

-- Normalize every feature using feature-wise means and population standard
-- deviations. The result is a relational representation of column-wise
-- standardization normally expressed as (X - mean) / std.
WITH feature_values AS (
    SELECT
        s AS feature_position,
        AVG(o.values[s]) AS feature_mean,
        STDDEV_POP(o.values[s]) AS feature_stddev
    FROM observations AS o
    CROSS JOIN LATERAL generate_subscripts(o.values, 1) AS s
    WHERE o.dataset_id = 1
    GROUP BY s
),
standardized AS (
    SELECT
        o.observation_position,
        ARRAY(
            SELECT
                CASE
                    WHEN fv.feature_stddev = 0 THEN NULL
                    ELSE
                        (o.values[fv.feature_position] - fv.feature_mean)
                        / fv.feature_stddev
                END
            FROM feature_values AS fv
            ORDER BY fv.feature_position
        ) AS standardized_values
    FROM observations AS o
    WHERE o.dataset_id = 1
)
SELECT *
FROM standardized
ORDER BY observation_position;

-- Matrix multiplication is represented as a relational join on the shared
-- dimension. A is a 5x4 observation matrix and W is a 4x2 projection matrix.
CREATE TEMP TABLE projection_matrix (
    row_position INTEGER NOT NULL,
    column_position INTEGER NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (row_position, column_position)
);

INSERT INTO projection_matrix VALUES
    (1, 1, 0.50),
    (1, 2, 0.20),
    (2, 1, 0.20),
    (2, 2, 0.60),
    (3, 1, 0.10),
    (3, 2, 0.30),
    (4, 1, 0.40),
    (4, 2, 0.10);

WITH source_matrix AS (
    SELECT
        o.observation_position AS matrix_row,
        s AS shared_position,
        o.values[s] AS value
    FROM observations AS o
    CROSS JOIN LATERAL generate_subscripts(o.values, 1) AS s
    WHERE o.dataset_id = 1
),
projected AS (
    SELECT
        source.matrix_row,
        projection.column_position,
        SUM(
            source.value * projection.value
        ) AS projected_value
    FROM source_matrix AS source
    JOIN projection_matrix AS projection
      ON projection.row_position = source.shared_position
    GROUP BY
        source.matrix_row,
        projection.column_position
)
SELECT
    matrix_row,
    ARRAY_AGG(
        projected_value
        ORDER BY column_position
    ) AS projected_vector
FROM projected
GROUP BY matrix_row
ORDER BY matrix_row;

-- Reshaping a flat sequence into a matrix is represented by calculating
-- row and column positions from the original linear position.
WITH RECURSIVE sequence_values AS (
    SELECT
        generate_series(0, 23) AS linear_position
),
reshaped AS (
    SELECT
        linear_position,
        linear_position / 6 AS row_position,
        linear_position % 6 AS column_position,
        linear_position + 1 AS value
    FROM sequence_values
)
SELECT
    row_position,
    ARRAY_AGG(value ORDER BY column_position) AS row_values
FROM reshaped
GROUP BY row_position
ORDER BY row_position;

-- Random generation uses PostgreSQL's random() function. The values are
-- generated inside a relational query rather than persisted as a deterministic
-- seed because PostgreSQL random() is session-state based.
SELECT
    sample_id,
    ROUND((random() * 100)::numeric, 4) AS uniform_value,
    ROUND(
        (
            50
            + 10 * sqrt(-2 * ln(GREATEST(random(), 1e-12)))
            * cos(2 * pi() * random())
        )::numeric,
        4
    ) AS approximate_normal_value
FROM generate_series(1, 10) AS sample_id;

-- Record successful operations in an audit table.
INSERT INTO matrix_operations (
    dataset_id,
    operation_type,
    input_shape,
    output_shape,
    success
)
VALUES (
    1,
    'broadcast',
    ARRAY[5, 4],
    ARRAY[5, 4],
    TRUE
);

INSERT INTO matrix_results (
    operation_id,
    result_values
)
VALUES (
    currval('matrix_operations_operation_id_seq'),
    ARRAY[
        120.0, 19.8, 0.056, 0.966,
        210.0, 27.5, 0.096, 0.924
    ]
);

-- Transactional integrity protects the operation audit record and its
-- numerical result from being persisted independently.
BEGIN;

INSERT INTO matrix_operations (
    dataset_id,
    operation_type,
    input_shape,
    output_shape,
    success
)
VALUES (
    1,
    'aggregation',
    ARRAY[5, 4],
    ARRAY[4],
    TRUE
);

INSERT INTO matrix_results (
    operation_id,
    result_values
)
VALUES (
    currval('matrix_operations_operation_id_seq'),
    ARRAY[
        191.0,
        21.0,
        0.096,
        0.898
    ]
);

COMMIT;

-- Demonstrate an integrity failure without leaving an invalid row behind.
BEGIN;

DO $$
BEGIN
    BEGIN
        INSERT INTO observations (
            dataset_id,
            observation_position,
            values
        )
        VALUES (
            1,
            5,
            ARRAY[]::DOUBLE PRECISION[]
        );
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Rejected empty numerical vector as expected.';
    END;
END;
$$;

ROLLBACK;

-- A feature-level query exposes which variables contribute most strongly
-- to a weighted numerical score.
SELECT
    f.feature_name,
    f.feature_position,
    f.weight,
    ABS(f.weight) AS absolute_weight
FROM feature_weights AS f
JOIN features AS feature
  ON feature.feature_id = f.feature_id
WHERE f.dataset_id = 1
ORDER BY ABS(f.weight) DESC;

-- Operations can be monitored as a compact numerical-processing audit trail.
SELECT
    operation_id,
    operation_type,
    input_shape,
    output_shape,
    success,
    executed_at,
    error_message
FROM matrix_operations
WHERE dataset_id = 1
ORDER BY executed_at, operation_id;
