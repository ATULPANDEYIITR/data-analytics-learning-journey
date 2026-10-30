/*
==============================================================================
PROJECT: COMPREHENSIVE EXPLORATORY DATA ANALYSIS
DATABASE: PostgreSQL 14+
DATASET: UCI IRIS
SOURCE: https://doi.org/10.24432/C56C76
LICENSE: CC BY 4.0

RELATIONAL DESIGN:
    Raw observations
        |
        v
    Data validation and ingestion
        |
        +------> Rejected records
        |
        v
    Validated observations
        |
        +------> Dataset profiling
        +------> Species distribution
        +------> Descriptive statistics
        +------> Pearson correlation
        +------> IQR outlier analysis
        +------> Analytical reporting
==============================================================================
*/

DROP SCHEMA IF EXISTS iris_eda CASCADE;

CREATE SCHEMA iris_eda;

SET search_path TO iris_eda, public;


/* ==========================================================================
   1. RAW DATA INGESTION
   ========================================================================== */

CREATE TABLE raw_iris (
    raw_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    batch_id VARCHAR(80) NOT NULL,
    source_row VARCHAR(40) NOT NULL,

    sepal_length_text TEXT,
    sepal_width_text TEXT,
    petal_length_text TEXT,
    petal_width_text TEXT,
    species_text TEXT,

    processing_status VARCHAR(12)
        NOT NULL DEFAULT 'PENDING',

    rejection_reason TEXT,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    processed_at TIMESTAMPTZ,

    CONSTRAINT uq_raw_batch_row
        UNIQUE (batch_id, source_row),

    CONSTRAINT chk_processing_status
        CHECK (
            processing_status IN (
                'PENDING',
                'ACCEPTED',
                'REJECTED'
            )
        )
);


/*
Permissive raw staging permits incomplete and malformed input.
Strict validation occurs before data enters the analytical table.
*/


/* ==========================================================================
   2. VALIDATED ANALYTICAL TABLE
   ========================================================================== */

CREATE TABLE iris_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    raw_id BIGINT NOT NULL UNIQUE,

    sepal_length NUMERIC(5,2) NOT NULL,
    sepal_width NUMERIC(5,2) NOT NULL,
    petal_length NUMERIC(5,2) NOT NULL,
    petal_width NUMERIC(5,2) NOT NULL,

    species VARCHAR(20) NOT NULL,

    ingested_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_observation_raw
        FOREIGN KEY (raw_id)
        REFERENCES raw_iris(raw_id),

    CONSTRAINT chk_sepal_length
        CHECK (sepal_length > 0 AND sepal_length < 10),

    CONSTRAINT chk_sepal_width
        CHECK (sepal_width > 0 AND sepal_width < 10),

    CONSTRAINT chk_petal_length
        CHECK (petal_length > 0 AND petal_length < 10),

    CONSTRAINT chk_petal_width
        CHECK (petal_width > 0 AND petal_width < 10),

    CONSTRAINT chk_species
        CHECK (
            species IN (
                'setosa',
                'versicolor',
                'virginica'
            )
        )
);


/* ==========================================================================
   3. INDEXING
   ========================================================================== */

CREATE INDEX idx_iris_species
    ON iris_observations(species);

CREATE INDEX idx_raw_status_batch
    ON raw_iris(batch_id, processing_status);

CREATE INDEX idx_iris_petal_measurements
    ON iris_observations(petal_length, petal_width);


/*
Indexes support species aggregation, pending ingestion retrieval,
and common petal-measurement analysis.
*/


/* ==========================================================================
   4. AUDIT PROTECTION
   ========================================================================== */

CREATE OR REPLACE FUNCTION prevent_processed_raw_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF OLD.processing_status <> 'PENDING' THEN
        RAISE EXCEPTION
            'Processed raw record % cannot be modified or deleted.',
            OLD.raw_id;
    END IF;

    RETURN CASE
        WHEN TG_OP = 'DELETE' THEN OLD
        ELSE NEW
    END;

END;
$$;


CREATE TRIGGER trg_protect_processed_raw
BEFORE UPDATE OR DELETE
ON raw_iris
FOR EACH ROW
EXECUTE FUNCTION prevent_processed_raw_mutation();


/*
The raw record becomes immutable after acceptance or rejection.
This preserves the original input used for analytical processing.
*/


/* ==========================================================================
   5. NORMALIZATION FUNCTION
   ========================================================================== */

CREATE OR REPLACE FUNCTION normalize_species(
    input_species TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    normalized TEXT;
BEGIN

    normalized := LOWER(TRIM(input_species));

    normalized := REPLACE(
        normalized,
        'iris-',
        ''
    );

    normalized := REPLACE(
        normalized,
        ' ',
        ''
    );

    IF normalized = 'versicolour' THEN
        normalized := 'versicolor';
    END IF;

    RETURN normalized;

END;
$$;


/* ==========================================================================
   6. VALIDATION AND INGESTION PROCEDURE
   ========================================================================== */

CREATE OR REPLACE PROCEDURE process_pending_rows()
LANGUAGE plpgsql
AS $$
DECLARE
    current_row RECORD;
    normalized_label TEXT;
    measurements NUMERIC[];
    validation_error TEXT;
BEGIN

    FOR current_row IN
        SELECT *
        FROM raw_iris
        WHERE processing_status = 'PENDING'
        ORDER BY raw_id
        FOR UPDATE
    LOOP

        validation_error := NULL;

        /*
        Numeric conversion is deliberately delayed until after
        lexical validation.
        */

        IF current_row.sepal_length_text IS NULL
            OR current_row.sepal_width_text IS NULL
            OR current_row.petal_length_text IS NULL
            OR current_row.petal_width_text IS NULL
            OR current_row.species_text IS NULL
        THEN

            validation_error := 'Missing required field';

        ELSIF
            current_row.sepal_length_text
                !~ '^[0-9]+(\.[0-9]+)?$'
            OR current_row.sepal_width_text
                !~ '^[0-9]+(\.[0-9]+)?$'
            OR current_row.petal_length_text
                !~ '^[0-9]+(\.[0-9]+)?$'
            OR current_row.petal_width_text
                !~ '^[0-9]+(\.[0-9]+)?$'
        THEN

            validation_error := 'Invalid numerical measurement';

        ELSE

            BEGIN

                measurements := ARRAY[
                    current_row.sepal_length_text::NUMERIC,
                    current_row.sepal_width_text::NUMERIC,
                    current_row.petal_length_text::NUMERIC,
                    current_row.petal_width_text::NUMERIC
                ];

                IF EXISTS (
                    SELECT 1
                    FROM UNNEST(measurements) AS value
                    WHERE value <= 0 OR value >= 10
                ) THEN

                    validation_error :=
                        'Measurement outside permitted range';

                END IF;

                normalized_label := normalize_species(
                    current_row.species_text
                );

                IF normalized_label NOT IN (
                    'setosa',
                    'versicolor',
                    'virginica'
                ) THEN

                    validation_error := 'Unknown species category';

                END IF;

            EXCEPTION
                WHEN OTHERS THEN
                    validation_error := SQLERRM;
            END;

        END IF;


        IF validation_error IS NOT NULL THEN

            UPDATE raw_iris
            SET
                processing_status = 'REJECTED',
                rejection_reason = validation_error,
                processed_at = CURRENT_TIMESTAMP
            WHERE raw_id = current_row.raw_id;

        ELSE

            INSERT INTO iris_observations (
                raw_id,
                sepal_length,
                sepal_width,
                petal_length,
                petal_width,
                species
            )
            VALUES (
                current_row.raw_id,
                measurements[1],
                measurements[2],
                measurements[3],
                measurements[4],
                normalized_label
            );

            UPDATE raw_iris
            SET
                processing_status = 'ACCEPTED',
                processed_at = CURRENT_TIMESTAMP
            WHERE raw_id = current_row.raw_id;

        END IF;

    END LOOP;

END;
$$;


/* ==========================================================================
   7. SAMPLE DATA: AUTHENTIC IRIS OBSERVATIONS
   ========================================================================== */

INSERT INTO raw_iris (
    batch_id,
    source_row,
    sepal_length_text,
    sepal_width_text,
    petal_length_text,
    petal_width_text,
    species_text
)
VALUES

('IRIS_SAMPLE_001', '001', '5.1', '3.5', '1.4', '0.2', 'Iris-setosa'),
('IRIS_SAMPLE_001', '002', '4.9', '3.0', '1.4', '0.2', 'Iris-setosa'),
('IRIS_SAMPLE_001', '003', '4.7', '3.2', '1.3', '0.2', 'Iris-setosa'),
('IRIS_SAMPLE_001', '004', '4.6', '3.1', '1.5', '0.2', 'Iris-setosa'),
('IRIS_SAMPLE_001', '005', '5.0', '3.6', '1.4', '0.2', 'Iris-setosa'),

('IRIS_SAMPLE_001', '006', '7.0', '3.2', '4.7', '1.4', 'Iris-versicolor'),
('IRIS_SAMPLE_001', '007', '6.4', '3.2', '4.5', '1.5', 'Iris-versicolor'),
('IRIS_SAMPLE_001', '008', '6.9', '3.1', '4.9', '1.5', 'Iris-versicolor'),
('IRIS_SAMPLE_001', '009', '5.5', '2.3', '4.0', '1.3', 'Iris-versicolor'),
('IRIS_SAMPLE_001', '010', '6.5', '2.8', '4.6', '1.5', 'Iris-versicolor'),

('IRIS_SAMPLE_001', '011', '6.3', '3.3', '6.0', '2.5', 'Iris-virginica'),
('IRIS_SAMPLE_001', '012', '5.8', '2.7', '5.1', '1.9', 'Iris-virginica'),
('IRIS_SAMPLE_001', '013', '7.1', '3.0', '5.9', '2.1', 'Iris-virginica'),
('IRIS_SAMPLE_001', '014', '6.3', '2.9', '5.6', '1.8', 'Iris-virginica'),
('IRIS_SAMPLE_001', '015', '6.5', '3.0', '5.8', '2.2', 'Iris-virginica'),

/* Deliberately malformed record for ingestion validation. */
('IRIS_SAMPLE_001', '016', 'not_available', '3.0', '1.4', '0.2', 'Iris-setosa');


/* ==========================================================================
   8. EXECUTE INGESTION TRANSACTION
   ========================================================================== */

BEGIN;

CALL process_pending_rows();

COMMIT;


/* ==========================================================================
   9. OPTIONAL FULL DATASET IMPORT
   ========================================================================== */

/*
The Python and JavaScript implementations can produce
iris_cleaned.csv with a header.

For a CSV file prepared in the staging format, use:

\copy iris_eda.raw_iris (
    batch_id,
    source_row,
    sepal_length_text,
    sepal_width_text,
    petal_length_text,
    petal_width_text,
    species_text
) FROM 'iris_staging.csv' WITH (FORMAT CSV, HEADER TRUE);

Then execute:

CALL iris_eda.process_pending_rows();

The staging file must supply batch_id and source_row.
Do not import an unkeyed five-column CSV into this seven-column structure.
*/


/* ==========================================================================
   10. DATASET PROFILE VIEW
   ========================================================================== */

CREATE OR REPLACE VIEW v_dataset_profile AS
SELECT
    COUNT(*) AS observation_count,

    COUNT(DISTINCT species) AS species_count,

    COUNT(*) FILTER (
        WHERE sepal_length IS NULL
    ) AS missing_sepal_length,

    COUNT(*) FILTER (
        WHERE sepal_width IS NULL
    ) AS missing_sepal_width,

    COUNT(*) FILTER (
        WHERE petal_length IS NULL
    ) AS missing_petal_length,

    COUNT(*) FILTER (
        WHERE petal_width IS NULL
    ) AS missing_petal_width,

    COUNT(*) FILTER (
        WHERE species IS NULL
    ) AS missing_species

FROM iris_observations;


/* ==========================================================================
   11. DATA QUALITY VIEW
   ========================================================================== */

CREATE OR REPLACE VIEW v_ingestion_quality AS
SELECT
    processing_status,
    COUNT(*) AS record_count
FROM raw_iris
GROUP BY processing_status;


/* ==========================================================================
   12. SPECIES DISTRIBUTION VIEW
   ========================================================================== */

CREATE OR REPLACE VIEW v_species_distribution AS
SELECT
    species,
    COUNT(*) AS sample_count,

    ROUND(
        COUNT(*) * 100.0 /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS percentage

FROM iris_observations
GROUP BY species;


/* ==========================================================================
   13. FEATURE DESCRIPTIVE STATISTICS
   ========================================================================== */

CREATE OR REPLACE VIEW v_feature_statistics AS

SELECT
    'sepal_length'::TEXT AS feature,
    MIN(sepal_length)::NUMERIC AS minimum,
    percentile_cont(0.25) WITHIN GROUP (
        ORDER BY sepal_length
    )::NUMERIC AS q1,
    percentile_cont(0.50) WITHIN GROUP (
        ORDER BY sepal_length
    )::NUMERIC AS median,
    AVG(sepal_length)::NUMERIC AS mean,
    percentile_cont(0.75) WITHIN GROUP (
        ORDER BY sepal_length
    )::NUMERIC AS q3,
    MAX(sepal_length)::NUMERIC AS maximum,
    STDDEV_SAMP(sepal_length)::NUMERIC AS standard_deviation

FROM iris_observations

UNION ALL

SELECT
    'sepal_width',
    MIN(sepal_width)::NUMERIC,
    percentile_cont(0.25) WITHIN GROUP (
        ORDER BY sepal_width
    )::NUMERIC,
    percentile_cont(0.50) WITHIN GROUP (
        ORDER BY sepal_width
    )::NUMERIC,
    AVG(sepal_width)::NUMERIC,
    percentile_cont(0.75) WITHIN GROUP (
        ORDER BY sepal_width
    )::NUMERIC,
    MAX(sepal_width)::NUMERIC,
    STDDEV_SAMP(sepal_width)::NUMERIC

FROM iris_observations

UNION ALL

SELECT
    'petal_length',
    MIN(petal_length)::NUMERIC,
    percentile_cont(0.25) WITHIN GROUP (
        ORDER BY petal_length
    )::NUMERIC,
    percentile_cont(0.50) WITHIN GROUP (
        ORDER BY petal_length
    )::NUMERIC,
    AVG(petal_length)::NUMERIC,
    percentile_cont(0.75) WITHIN GROUP (
        ORDER BY petal_length
    )::NUMERIC,
    MAX(petal_length)::NUMERIC,
    STDDEV_SAMP(petal_length)::NUMERIC

FROM iris_observations

UNION ALL

SELECT
    'petal_width',
    MIN(petal_width)::NUMERIC,
    percentile_cont(0.25) WITHIN GROUP (
        ORDER BY petal_width
    )::NUMERIC,
    percentile_cont(0.50) WITHIN GROUP (
        ORDER BY petal_width
    )::NUMERIC,
    AVG(petal_width)::NUMERIC,
    percentile_cont(0.75) WITHIN GROUP (
        ORDER BY petal_width
    )::NUMERIC,
    MAX(petal_width)::NUMERIC,
    STDDEV_SAMP(petal_width)::NUMERIC

FROM iris_observations;


/* ==========================================================================
   14. SPECIES-LEVEL ANALYSIS VIEW
   ========================================================================== */

CREATE OR REPLACE VIEW v_species_statistics AS
SELECT
    species,

    COUNT(*) AS observation_count,

    ROUND(AVG(sepal_length), 3) AS mean_sepal_length,
    ROUND(AVG(sepal_width), 3) AS mean_sepal_width,
    ROUND(AVG(petal_length), 3) AS mean_petal_length,
    ROUND(AVG(petal_width), 3) AS mean_petal_width,

    ROUND(STDDEV_SAMP(sepal_length), 3)
        AS sepal_length_sd,

    ROUND(STDDEV_SAMP(petal_length), 3)
        AS petal_length_sd

FROM iris_observations
GROUP BY species;


/* ==========================================================================
   15. PEARSON CORRELATION ANALYSIS
   ========================================================================== */

CREATE OR REPLACE VIEW v_feature_correlations AS

SELECT
    'sepal_length' AS feature_one,
    'sepal_width' AS feature_two,
    CORR(sepal_length, sepal_width) AS correlation
FROM iris_observations

UNION ALL

SELECT
    'sepal_length',
    'petal_length',
    CORR(sepal_length, petal_length)
FROM iris_observations

UNION ALL

SELECT
    'sepal_length',
    'petal_width',
    CORR(sepal_length, petal_width)
FROM iris_observations

UNION ALL

SELECT
    'sepal_width',
    'petal_length',
    CORR(sepal_width, petal_length)
FROM iris_observations

UNION ALL

SELECT
    'sepal_width',
    'petal_width',
    CORR(sepal_width, petal_width)
FROM iris_observations

UNION ALL

SELECT
    'petal_length',
    'petal_width',
    CORR(petal_length, petal_width)
FROM iris_observations;


/* ==========================================================================
   16. IQR OUTLIER DETECTION
   ========================================================================== */

CREATE OR REPLACE VIEW v_iqr_outliers AS

WITH feature_values AS (

    SELECT
        observation_id,
        species,
        feature,
        measurement

    FROM iris_observations

    CROSS JOIN LATERAL (
        VALUES
            ('sepal_length', sepal_length::DOUBLE PRECISION),
            ('sepal_width', sepal_width::DOUBLE PRECISION),
            ('petal_length', petal_length::DOUBLE PRECISION),
            ('petal_width', petal_width::DOUBLE PRECISION)
    ) AS features(feature, measurement)

),

feature_bounds AS (

    SELECT
        feature,

        percentile_cont(0.25)
            WITHIN GROUP (ORDER BY measurement) AS q1,

        percentile_cont(0.75)
            WITHIN GROUP (ORDER BY measurement) AS q3

    FROM feature_values
    GROUP BY feature

),

outlier_candidates AS (

    SELECT
        values.observation_id,
        values.species,
        values.feature,
        values.measurement,
        bounds.q1,
        bounds.q3,

        bounds.q1 - 1.5 * (bounds.q3 - bounds.q1)
            AS lower_bound,

        bounds.q3 + 1.5 * (bounds.q3 - bounds.q1)
            AS upper_bound

    FROM feature_values values

    JOIN feature_bounds bounds
        ON bounds.feature = values.feature

)

SELECT *
FROM outlier_candidates
WHERE
    measurement < lower_bound
    OR measurement > upper_bound;


/* ==========================================================================
   17. DATASET REPORTING QUERIES
   ========================================================================== */

-- A. Overall dataset profile.

SELECT *
FROM v_dataset_profile;


-- B. Ingestion quality and rejection reasons.

SELECT *
FROM v_ingestion_quality
ORDER BY processing_status;

SELECT
    source_row,
    rejection_reason
FROM raw_iris
WHERE processing_status = 'REJECTED';


-- C. Species distribution.

SELECT *
FROM v_species_distribution
ORDER BY species;


-- D. Global feature statistics.

SELECT *
FROM v_feature_statistics
ORDER BY feature;


-- E. Species comparisons.

SELECT *
FROM v_species_statistics
ORDER BY species;


-- F. Feature correlations.

SELECT
    feature_one,
    feature_two,
    ROUND(correlation::NUMERIC, 4) AS pearson_correlation
FROM v_feature_correlations
ORDER BY feature_one, feature_two;


-- G. IQR outlier observations.

SELECT
    observation_id,
    species,
    feature,
    measurement,
    q1,
    q3,
    lower_bound,
    upper_bound
FROM v_iqr_outliers
ORDER BY feature, observation_id;


-- H. Outlier counts by feature.

SELECT
    feature,
    COUNT(*) AS outlier_count
FROM v_iqr_outliers
GROUP BY feature
ORDER BY feature;


-- I. Species with the largest average petal length.

SELECT
    species,
    mean_petal_length
FROM v_species_statistics
ORDER BY mean_petal_length DESC;


-- J. Data distribution using a reporting CTE.

WITH species_totals AS (
    SELECT
        species,
        COUNT(*) AS sample_count,
        AVG(petal_length) AS mean_petal_length,
        AVG(petal_width) AS mean_petal_width
    FROM iris_observations
    GROUP BY species
),

ranked_species AS (
    SELECT
        *,
        RANK() OVER (
            ORDER BY mean_petal_length DESC
        ) AS petal_length_rank
    FROM species_totals
)

SELECT
    species,
    sample_count,
    ROUND(mean_petal_length, 3) AS mean_petal_length,
    ROUND(mean_petal_width, 3) AS mean_petal_width,
    petal_length_rank
FROM ranked_species
ORDER BY petal_length_rank;


/* ==========================================================================
   18. INGESTION STATUS AUDIT
   ========================================================================== */

SELECT
    batch_id,
    processing_status,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (
        WHERE rejection_reason IS NOT NULL
    ) AS rejected_records
FROM raw_iris
GROUP BY
    batch_id,
    processing_status
ORDER BY
    batch_id,
    processing_status;


/* ==========================================================================
   END OF EXECUTABLE POSTGRESQL ANALYTICS PROJECT
   ========================================================================== */
