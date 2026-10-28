DROP SCHEMA IF EXISTS statistical_visualization CASCADE;
CREATE SCHEMA statistical_visualization;

SET search_path TO statistical_visualization, public;

-- Observations are stored in long form so the same model supports
-- numerical and categorical visualization workflows.
CREATE TABLE dataset (
    dataset_id BIGSERIAL PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE observation (
    observation_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(dataset_id) ON DELETE CASCADE,
    observation_index INTEGER NOT NULL CHECK (observation_index > 0),
    numeric_value NUMERIC,
    category_value TEXT,
    CHECK (
        (numeric_value IS NOT NULL AND category_value IS NULL)
        OR
        (numeric_value IS NULL AND category_value IS NOT NULL
         AND length(btrim(category_value)) > 0)
    ),
    UNIQUE (dataset_id, observation_index)
);

CREATE TABLE scatter_point (
    point_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(dataset_id) ON DELETE CASCADE,
    point_index INTEGER NOT NULL CHECK (point_index > 0),
    x_value NUMERIC NOT NULL,
    y_value NUMERIC NOT NULL,
    UNIQUE (dataset_id, point_index)
);

CREATE TABLE visualization_request (
    request_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES dataset(dataset_id) ON DELETE CASCADE,
    plot_type TEXT NOT NULL CHECK (
        plot_type IN (
            'histogram',
            'box',
            'violin',
            'scatter',
            'density',
            'categorical'
        )
    ),
    requested_bins INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        requested_bins IS NULL
        OR requested_bins BETWEEN 1 AND 1000
    )
);

CREATE TABLE visualization_result (
    result_id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL UNIQUE
        REFERENCES visualization_request(request_id)
        ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'valid', 'invalid', 'completed')
    ),
    message TEXT NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_observation_dataset_numeric
    ON observation(dataset_id, numeric_value)
    WHERE numeric_value IS NOT NULL;

CREATE INDEX idx_observation_dataset_category
    ON observation(dataset_id, category_value)
    WHERE category_value IS NOT NULL;

CREATE INDEX idx_scatter_dataset
    ON scatter_point(dataset_id);

INSERT INTO dataset(dataset_name, description)
VALUES
    (
        'service_latency',
        'Latency measurements in milliseconds for a service endpoint'
    ),
    (
        'client_platform',
        'Observed client platform categories'
    ),
    (
        'traffic_scatter',
        'Request volume and latency pairs'
    );

INSERT INTO observation(dataset_id, observation_index, numeric_value)
SELECT
    d.dataset_id,
    row_number() OVER (),
    v.value
FROM dataset d
CROSS JOIN LATERAL (
    VALUES
        (42::numeric), (45), (47), (48), (49),
        (50), (51), (52), (52), (53),
        (54), (55), (56), (57), (58),
        (59), (61), (62), (63), (65),
        (68), (70), (74), (79), (91)
) AS v(value)
WHERE d.dataset_name = 'service_latency';

INSERT INTO observation(dataset_id, observation_index, category_value)
SELECT
    d.dataset_id,
    row_number() OVER (),
    v.value
FROM dataset d
CROSS JOIN LATERAL (
    VALUES
        ('API'), ('API'), ('Web'), ('Web'), ('Web'),
        ('Mobile'), ('API'), ('Mobile'), ('Web'), ('API'),
        ('Desktop'), ('Web'), ('Mobile'), ('API')
) AS v(value)
WHERE d.dataset_name = 'client_platform';

INSERT INTO scatter_point(dataset_id, point_index, x_value, y_value)
SELECT
    d.dataset_id,
    row_number() OVER (),
    v.request_count,
    v.latency
FROM dataset d
CROSS JOIN LATERAL (
    VALUES
        (10::numeric, 42::numeric),
        (15, 45),
        (20, 48),
        (25, 51),
        (30, 52),
        (35, 55),
        (40, 58),
        (45, 62),
        (50, 65),
        (60, 70),
        (70, 74),
        (80, 79),
        (90, 91)
) AS v(request_count, latency)
WHERE d.dataset_name = 'traffic_scatter';

INSERT INTO visualization_request(dataset_id, plot_type, requested_bins)
SELECT dataset_id, 'histogram', 8
FROM dataset
WHERE dataset_name = 'service_latency';

INSERT INTO visualization_request(dataset_id, plot_type)
SELECT dataset_id, 'box'
FROM dataset
WHERE dataset_name = 'service_latency';

INSERT INTO visualization_request(dataset_id, plot_type)
SELECT dataset_id, 'violin'
FROM dataset
WHERE dataset_name = 'service_latency';

INSERT INTO visualization_request(dataset_id, plot_type)
SELECT dataset_id, 'density'
FROM dataset
WHERE dataset_name = 'service_latency';

INSERT INTO visualization_request(dataset_id, plot_type)
SELECT dataset_id, 'scatter'
FROM dataset
WHERE dataset_name = 'traffic_scatter';

INSERT INTO visualization_request(dataset_id, plot_type)
SELECT dataset_id, 'categorical'
FROM dataset
WHERE dataset_name = 'client_platform';

-- Quartiles use PostgreSQL's continuous percentile definition.
CREATE OR REPLACE FUNCTION numeric_five_number_summary(
    p_dataset_id BIGINT
)
RETURNS TABLE (
    minimum NUMERIC,
    q1 NUMERIC,
    median NUMERIC,
    q3 NUMERIC,
    maximum NUMERIC,
    iqr NUMERIC,
    lower_fence NUMERIC,
    upper_fence NUMERIC
)
LANGUAGE SQL
STABLE
AS $$
    WITH values AS (
        SELECT numeric_value
        FROM observation
        WHERE dataset_id = p_dataset_id
          AND numeric_value IS NOT NULL
    ),
    quartiles AS (
        SELECT
            min(numeric_value) AS minimum,
            percentile_cont(0.25)
                WITHIN GROUP (ORDER BY numeric_value) AS q1,
            percentile_cont(0.50)
                WITHIN GROUP (ORDER BY numeric_value) AS median,
            percentile_cont(0.75)
                WITHIN GROUP (ORDER BY numeric_value) AS q3,
            max(numeric_value) AS maximum
        FROM values
    )
    SELECT
        minimum,
        q1,
        median,
        q3,
        maximum,
        q3 - q1 AS iqr,
        q1 - 1.5 * (q3 - q1) AS lower_fence,
        q3 + 1.5 * (q3 - q1) AS upper_fence
    FROM quartiles;
$$;

CREATE OR REPLACE FUNCTION validate_visualization_request(
    p_request_id BIGINT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    request_record visualization_request%ROWTYPE;
    numeric_count BIGINT;
    category_count BIGINT;
    point_count BIGINT;
BEGIN
    SELECT *
    INTO request_record
    FROM visualization_request
    WHERE request_id = p_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Visualization request % does not exist',
            p_request_id;
    END IF;

    SELECT count(*)
    INTO numeric_count
    FROM observation
    WHERE dataset_id = request_record.dataset_id
      AND numeric_value IS NOT NULL;

    SELECT count(*)
    INTO category_count
    FROM observation
    WHERE dataset_id = request_record.dataset_id
      AND category_value IS NOT NULL;

    SELECT count(*)
    INTO point_count
    FROM scatter_point
    WHERE dataset_id = request_record.dataset_id;

    IF request_record.plot_type IN
        ('histogram', 'box', 'violin', 'density')
    THEN
        IF numeric_count = 0 THEN
            RETURN 'invalid: numerical observations are required';
        END IF;
    END IF;

    IF request_record.plot_type = 'categorical' THEN
        IF category_count = 0 THEN
            RETURN 'invalid: categorical observations are required';
        END IF;
    END IF;

    IF request_record.plot_type = 'scatter' THEN
        IF point_count = 0 THEN
            RETURN 'invalid: scatter points are required';
        END IF;
    END IF;

    RETURN 'valid';
END;
$$;

CREATE OR REPLACE FUNCTION initialize_visualization_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    validation_message TEXT;
BEGIN
    validation_message :=
        validate_visualization_request(NEW.request_id);

    INSERT INTO visualization_result(
        request_id,
        status,
        message,
        completed_at
    )
    VALUES (
        NEW.request_id,
        CASE
            WHEN validation_message = 'valid'
                THEN 'valid'
            ELSE 'invalid'
        END,
        validation_message,
        CASE
            WHEN validation_message = 'valid'
                THEN CURRENT_TIMESTAMP
            ELSE NULL
        END
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_visualization_validation
AFTER INSERT ON visualization_request
FOR EACH ROW
EXECUTE FUNCTION initialize_visualization_result();

-- Descriptive statistics for the numerical dataset.
SELECT
    d.dataset_name,
    count(o.numeric_value) AS observations,
    round(avg(o.numeric_value), 2) AS mean,
    round(stddev_pop(o.numeric_value), 2) AS population_sd,
    min(o.numeric_value) AS minimum,
    max(o.numeric_value) AS maximum
FROM dataset d
JOIN observation o
    ON o.dataset_id = d.dataset_id
WHERE d.dataset_name = 'service_latency'
GROUP BY d.dataset_name;

-- Box-plot statistics and IQR fences.
SELECT
    d.dataset_name,
    s.*
FROM dataset d
CROSS JOIN LATERAL numeric_five_number_summary(d.dataset_id) s
WHERE d.dataset_name = 'service_latency';

-- Explicit outlier retrieval.
WITH summary AS (
    SELECT *
    FROM numeric_five_number_summary(
        (
            SELECT dataset_id
            FROM dataset
            WHERE dataset_name = 'service_latency'
        )
    )
)
SELECT
    o.observation_index,
    o.numeric_value
FROM observation o
CROSS JOIN summary s
WHERE o.dataset_id = (
    SELECT dataset_id
    FROM dataset
    WHERE dataset_name = 'service_latency'
)
AND (
    o.numeric_value < s.lower_fence
    OR o.numeric_value > s.upper_fence
)
ORDER BY o.numeric_value;

-- Histogram using an explicit eight-bin range.
WITH bounds AS (
    SELECT
        min(numeric_value) AS minimum,
        max(numeric_value) AS maximum
    FROM observation
    WHERE dataset_id = (
        SELECT dataset_id
        FROM dataset
        WHERE dataset_name = 'service_latency'
    )
),
bucketed AS (
    SELECT
        o.numeric_value,
        width_bucket(
            o.numeric_value,
            b.minimum,
            b.maximum,
            8
        ) AS bucket
    FROM observation o
    CROSS JOIN bounds b
    WHERE o.dataset_id = (
        SELECT dataset_id
        FROM dataset
        WHERE dataset_name = 'service_latency'
    )
)
SELECT
    bucket,
    count(*) AS frequency
FROM bucketed
GROUP BY bucket
ORDER BY bucket;

-- Categorical frequencies and percentages.
SELECT
    o.category_value AS category,
    count(*) AS frequency,
    round(
        100.0 * count(*) /
        sum(count(*)) OVER (),
        2
    ) AS percentage
FROM observation o
WHERE o.dataset_id = (
    SELECT dataset_id
    FROM dataset
    WHERE dataset_name = 'client_platform'
)
GROUP BY o.category_value
ORDER BY frequency DESC, category;

-- Scatter data prepared for a plotting layer.
SELECT
    point_index,
    x_value,
    y_value
FROM scatter_point
WHERE dataset_id = (
    SELECT dataset_id
    FROM dataset
    WHERE dataset_name = 'traffic_scatter'
)
ORDER BY point_index;

-- Workflow state for every requested visualization.
SELECT
    vr.request_id,
    d.dataset_name,
    vr.plot_type,
    vr.requested_bins,
    result.status,
    result.message,
    result.completed_at
FROM visualization_request vr
JOIN dataset d
    ON d.dataset_id = vr.dataset_id
JOIN visualization_result result
    ON result.request_id = vr.request_id
ORDER BY vr.request_id;

-- Transactional example: an invalid request is inserted and then removed
-- atomically, leaving the persistent visualization queue unchanged.
BEGIN;

WITH inserted AS (
    INSERT INTO visualization_request(
        dataset_id,
        plot_type,
        requested_bins
    )
    SELECT
        dataset_id,
        'histogram',
        12
    FROM dataset
    WHERE dataset_name = 'service_latency'
    RETURNING request_id
)
SELECT request_id
FROM inserted;

DELETE FROM visualization_request
WHERE request_id = (
    SELECT max(request_id)
    FROM visualization_request
);

COMMIT;
