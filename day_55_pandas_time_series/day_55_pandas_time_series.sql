DROP SCHEMA IF EXISTS pandas_time_series CASCADE;

CREATE SCHEMA pandas_time_series;

SET search_path TO pandas_time_series;

-- The relational model stores the same concepts handled by a Pandas
-- DatetimeIndex: timestamped observations, calendar aggregation,
-- rolling-window analysis, shifts, and derived measurements.

CREATE TABLE sensors (
    sensor_id BIGSERIAL PRIMARY KEY,
    sensor_code TEXT NOT NULL UNIQUE,
    sensor_name TEXT NOT NULL,
    timezone_name TEXT NOT NULL DEFAULT 'UTC',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensor_readings (
    reading_id BIGSERIAL PRIMARY KEY,
    sensor_id BIGINT NOT NULL
        REFERENCES sensors(sensor_id)
        ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    temperature NUMERIC(8, 3) NOT NULL,
    pressure NUMERIC(9, 3) NOT NULL,
    energy_kwh NUMERIC(12, 4) NOT NULL,
    CONSTRAINT sensor_reading_temperature_valid
        CHECK (temperature BETWEEN -80 AND 100),
    CONSTRAINT sensor_reading_pressure_valid
        CHECK (pressure > 0),
    CONSTRAINT sensor_reading_energy_valid
        CHECK (energy_kwh >= 0),
    CONSTRAINT sensor_reading_unique_timestamp
        UNIQUE (sensor_id, observed_at)
);

CREATE INDEX idx_sensor_readings_sensor_time
    ON sensor_readings (sensor_id, observed_at);

CREATE INDEX idx_sensor_readings_time
    ON sensor_readings (observed_at);

INSERT INTO sensors (
    sensor_code,
    sensor_name,
    timezone_name
)
VALUES
    ('SENSOR-001', 'Operations Sensor A', 'UTC'),
    ('SENSOR-002', 'Operations Sensor B', 'UTC');

INSERT INTO sensor_readings (
    sensor_id,
    observed_at,
    temperature,
    pressure,
    energy_kwh
)
SELECT
    s.sensor_id,
    data.observed_at,
    data.temperature,
    data.pressure,
    data.energy_kwh
FROM sensors s
JOIN (
    VALUES
        ('SENSOR-001', '2026-01-01 08:00:00+00'::timestamptz, 21.2, 1008, 3.1),
        ('SENSOR-001', '2026-01-01 12:00:00+00'::timestamptz, 22.1, 1007, 2.4),
        ('SENSOR-001', '2026-01-02 09:30:00+00'::timestamptz, 20.8, 1009, 3.7),
        ('SENSOR-001', '2026-01-03 10:00:00+00'::timestamptz, 23.4, 1006, 4.0),
        ('SENSOR-001', '2026-01-05 14:00:00+00'::timestamptz, 24.0, 1005, 5.1),
        ('SENSOR-001', '2026-01-06 11:15:00+00'::timestamptz, 23.2, 1007, 4.4),
        ('SENSOR-001', '2026-01-08 16:30:00+00'::timestamptz, 25.1, 1004, 5.8),
        ('SENSOR-001', '2026-01-10 09:00:00+00'::timestamptz, 26.0, 1003, 6.2),
        ('SENSOR-001', '2026-01-12 13:45:00+00'::timestamptz, 24.7, 1005, 5.0),
        ('SENSOR-001', '2026-01-14 15:00:00+00'::timestamptz, 27.2, 1002, 6.7)
) AS data (
    sensor_code,
    observed_at,
    temperature,
    pressure,
    energy_kwh
)
ON s.sensor_code = data.sensor_code;

-- Daily resampling equivalent.
CREATE OR REPLACE VIEW daily_sensor_summary AS
SELECT
    sensor_id,
    date_trunc('day', observed_at) AS day,
    AVG(temperature) AS average_temperature,
    AVG(pressure) AS average_pressure,
    SUM(energy_kwh) AS total_energy_kwh,
    COUNT(*) AS observation_count
FROM sensor_readings
GROUP BY
    sensor_id,
    date_trunc('day', observed_at);

-- Shift and difference equivalent using LAG.
CREATE OR REPLACE VIEW sensor_changes AS
WITH ordered AS (
    SELECT
        sr.*,
        LAG(temperature)
            OVER (
                PARTITION BY sensor_id
                ORDER BY observed_at
            ) AS previous_temperature,
        LAG(energy_kwh)
            OVER (
                PARTITION BY sensor_id
                ORDER BY observed_at
            ) AS previous_energy
    FROM sensor_readings sr
)
SELECT
    *,
    temperature - previous_temperature
        AS temperature_difference,
    energy_kwh - previous_energy
        AS energy_difference,
    CASE
        WHEN previous_energy IS NULL
             OR previous_energy = 0
        THEN NULL
        ELSE (energy_kwh - previous_energy)
             / previous_energy * 100
    END AS energy_percent_change
FROM ordered;

-- Time-based rolling window equivalent.
CREATE OR REPLACE VIEW seven_day_rolling_metrics AS
SELECT
    sr.sensor_id,
    sr.observed_at,
    sr.temperature,
    sr.energy_kwh,
    AVG(sr.temperature) OVER (
        PARTITION BY sr.sensor_id
        ORDER BY sr.observed_at
        RANGE BETWEEN INTERVAL '7 days' PRECEDING
                  AND CURRENT ROW
    ) AS rolling_temperature_mean,
    STDDEV_SAMP(sr.temperature) OVER (
        PARTITION BY sr.sensor_id
        ORDER BY sr.observed_at
        RANGE BETWEEN INTERVAL '7 days' PRECEDING
                  AND CURRENT ROW
    ) AS rolling_temperature_stddev,
    SUM(sr.energy_kwh) OVER (
        PARTITION BY sr.sensor_id
        ORDER BY sr.observed_at
        RANGE BETWEEN INTERVAL '7 days' PRECEDING
                  AND CURRENT ROW
    ) AS rolling_energy_total,
    COUNT(*) OVER (
        PARTITION BY sr.sensor_id
        ORDER BY sr.observed_at
        RANGE BETWEEN INTERVAL '7 days' PRECEDING
                  AND CURRENT ROW
    ) AS rolling_observations
FROM sensor_readings sr;

-- Calendar-based grouping by week.
CREATE OR REPLACE VIEW weekly_sensor_summary AS
SELECT
    sensor_id,
    date_trunc('week', observed_at) AS week_start,
    AVG(temperature) AS average_temperature,
    MAX(temperature) AS maximum_temperature,
    MIN(temperature) AS minimum_temperature,
    SUM(energy_kwh) AS total_energy_kwh,
    COUNT(*) AS observation_count
FROM sensor_readings
GROUP BY
    sensor_id,
    date_trunc('week', observed_at);

-- Time-of-day grouping.
CREATE OR REPLACE VIEW hourly_sensor_summary AS
SELECT
    sensor_id,
    EXTRACT(HOUR FROM observed_at)::INTEGER AS hour_of_day,
    AVG(temperature) AS average_temperature,
    SUM(energy_kwh) AS total_energy_kwh,
    COUNT(*) AS observation_count
FROM sensor_readings
GROUP BY
    sensor_id,
    EXTRACT(HOUR FROM observed_at)::INTEGER;

-- Parameterized function for retrieving a bounded time range.
CREATE OR REPLACE FUNCTION readings_between(
    p_sensor_code TEXT,
    p_start TIMESTAMPTZ,
    p_end TIMESTAMPTZ
)
RETURNS TABLE (
    observed_at TIMESTAMPTZ,
    temperature NUMERIC,
    pressure NUMERIC,
    energy_kwh NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        sr.observed_at,
        sr.temperature,
        sr.pressure,
        sr.energy_kwh
    FROM sensor_readings sr
    JOIN sensors s
      ON s.sensor_id = sr.sensor_id
    WHERE s.sensor_code = p_sensor_code
      AND sr.observed_at >= p_start
      AND sr.observed_at < p_end
    ORDER BY sr.observed_at;
$$;

-- Demonstrate DatetimeIndex-style chronological retrieval.
SELECT *
FROM readings_between(
    'SENSOR-001',
    '2026-01-01 00:00:00+00',
    '2026-01-15 00:00:00+00'
);

-- Daily resampling report.
SELECT *
FROM daily_sensor_summary
ORDER BY sensor_id, day;

-- Rolling-window report.
SELECT *
FROM seven_day_rolling_metrics
ORDER BY sensor_id, observed_at;

-- Shift and difference report.
SELECT *
FROM sensor_changes
ORDER BY sensor_id, observed_at;

-- Weekly time grouping.
SELECT *
FROM weekly_sensor_summary
ORDER BY sensor_id, week_start;

-- Hour-of-day grouping.
SELECT *
FROM hourly_sensor_summary
ORDER BY sensor_id, hour_of_day;

-- Example validation query for chronological data quality.
SELECT
    sensor_id,
    COUNT(*) AS reading_count,
    MIN(observed_at) AS first_reading,
    MAX(observed_at) AS last_reading,
    COUNT(*) FILTER (
        WHERE temperature IS NULL
    ) AS null_temperature_count
FROM sensor_readings
GROUP BY sensor_id;

-- Transactional example: a new observation is inserted only when
-- the referenced sensor exists and all table constraints pass.
BEGIN;

INSERT INTO sensor_readings (
    sensor_id,
    observed_at,
    temperature,
    pressure,
    energy_kwh
)
SELECT
    sensor_id,
    '2026-01-15 10:00:00+00',
    26.4,
    1001.5,
    6.1
FROM sensors
WHERE sensor_code = 'SENSOR-001'
  AND active = TRUE;

COMMIT;

-- The unique timestamp constraint protects against accidental duplicate
-- observations, while the timestamp index supports chronological scans.
SELECT
    s.sensor_code,
    sr.observed_at,
    sr.temperature
FROM sensor_readings sr
JOIN sensors s
  ON s.sensor_id = sr.sensor_id
WHERE s.sensor_code = 'SENSOR-001'
ORDER BY sr.observed_at;
