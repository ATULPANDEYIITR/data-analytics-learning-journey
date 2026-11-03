DROP SCHEMA IF EXISTS probability_fundamentals CASCADE;

CREATE SCHEMA probability_fundamentals;

SET search_path TO probability_fundamentals;

-- A sample space contains mutually exclusive outcomes.
CREATE TABLE sample_spaces (
    sample_space_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE outcomes (
    outcome_id BIGSERIAL PRIMARY KEY,
    sample_space_id BIGINT NOT NULL
        REFERENCES sample_spaces(sample_space_id)
        ON DELETE CASCADE,
    outcome_code TEXT NOT NULL,
    probability NUMERIC(18, 12) NOT NULL,
    CONSTRAINT outcomes_probability_range
        CHECK (probability >= 0 AND probability <= 1),
    CONSTRAINT outcomes_unique_code
        UNIQUE (sample_space_id, outcome_code)
);

CREATE INDEX idx_outcomes_sample_space
    ON outcomes(sample_space_id);

CREATE TABLE events (
    event_id BIGSERIAL PRIMARY KEY,
    sample_space_id BIGINT NOT NULL
        REFERENCES sample_spaces(sample_space_id)
        ON DELETE CASCADE,
    event_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT events_unique_name
        UNIQUE (sample_space_id, event_name)
);

CREATE TABLE event_outcomes (
    event_id BIGINT NOT NULL
        REFERENCES events(event_id)
        ON DELETE CASCADE,
    outcome_id BIGINT NOT NULL
        REFERENCES outcomes(outcome_id)
        ON DELETE CASCADE,
    PRIMARY KEY (event_id, outcome_id)
);

CREATE INDEX idx_event_outcomes_outcome
    ON event_outcomes(outcome_id);

CREATE TABLE conditional_observations (
    observation_id BIGSERIAL PRIMARY KEY,
    sample_space_id BIGINT NOT NULL
        REFERENCES sample_spaces(sample_space_id)
        ON DELETE CASCADE,
    target_event_id BIGINT NOT NULL
        REFERENCES events(event_id)
        ON DELETE CASCADE,
    condition_event_id BIGINT NOT NULL
        REFERENCES events(event_id)
        ON DELETE CASCADE,
    observed_probability NUMERIC(18, 12),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT observations_different_events
        CHECK (target_event_id <> condition_event_id),
    CONSTRAINT observed_probability_range
        CHECK (
            observed_probability IS NULL
            OR (
                observed_probability >= 0
                AND observed_probability <= 1
            )
        )
);

CREATE TABLE probability_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    maximum_probability NUMERIC(18, 12) NOT NULL,
    minimum_sample_space_probability NUMERIC(18, 12)
        NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT policy_probability_range
        CHECK (
            maximum_probability BETWEEN 0 AND 1
            AND minimum_sample_space_probability BETWEEN 0 AND 1
        )
);

CREATE TABLE probability_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL
        REFERENCES probability_policies(policy_id),
    event_id BIGINT NOT NULL
        REFERENCES events(event_id),
    evaluated_probability NUMERIC(18, 12) NOT NULL,
    eligible BOOLEAN NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Prevent invalid probability totals for a complete discrete sample space.
CREATE OR REPLACE FUNCTION validate_sample_space_probability()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    total_probability NUMERIC(18, 12);
BEGIN
    SELECT COALESCE(SUM(probability), 0)
    INTO total_probability
    FROM outcomes
    WHERE sample_space_id = NEW.sample_space_id;

    IF total_probability > 1.000000000001 THEN
        RAISE EXCEPTION
            'Total probability for sample space % exceeds 1',
            NEW.sample_space_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_probability_upper_bound
AFTER INSERT OR UPDATE OF probability, sample_space_id
ON outcomes
FOR EACH ROW
EXECUTE FUNCTION validate_sample_space_probability();

-- A helper function calculates P(event).
CREATE OR REPLACE FUNCTION event_probability(
    p_event_id BIGINT
)
RETURNS NUMERIC(18, 12)
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(SUM(o.probability), 0)::NUMERIC(18, 12)
    FROM event_outcomes eo
    JOIN outcomes o
      ON o.outcome_id = eo.outcome_id
    WHERE eo.event_id = p_event_id;
$$;

-- P(A ∩ B) for events belonging to the same sample space.
CREATE OR REPLACE FUNCTION intersection_probability(
    p_first_event BIGINT,
    p_second_event BIGINT
)
RETURNS NUMERIC(18, 12)
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(SUM(o.probability), 0)::NUMERIC(18, 12)
    FROM event_outcomes first_event
    JOIN event_outcomes second_event
      ON second_event.outcome_id = first_event.outcome_id
    JOIN outcomes o
      ON o.outcome_id = first_event.outcome_id
    WHERE first_event.event_id = p_first_event
      AND second_event.event_id = p_second_event;
$$;

CREATE OR REPLACE FUNCTION conditional_probability(
    p_target_event BIGINT,
    p_condition_event BIGINT
)
RETURNS NUMERIC(18, 12)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    denominator NUMERIC(18, 12);
    numerator NUMERIC(18, 12);
BEGIN
    denominator := event_probability(p_condition_event);

    IF denominator = 0 THEN
        RAISE EXCEPTION
            'Conditional probability undefined because P(condition) = 0';
    END IF;

    numerator := intersection_probability(
        p_target_event,
        p_condition_event
    );

    RETURN (numerator / denominator)::NUMERIC(18, 12);
END;
$$;

CREATE OR REPLACE FUNCTION events_are_independent(
    p_first_event BIGINT,
    p_second_event BIGINT
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT ABS(
        intersection_probability(p_first_event, p_second_event)
        - (
            event_probability(p_first_event)
            * event_probability(p_second_event)
        )
    ) <= 0.000000000001;
$$;

INSERT INTO sample_spaces (name, description)
VALUES (
    'fair_die',
    'A six-outcome fair die sample space.'
);

INSERT INTO outcomes (
    sample_space_id,
    outcome_code,
    probability
)
SELECT
    sample_space_id,
    value::TEXT,
    1.0 / 6.0
FROM sample_spaces,
     generate_series(1, 6) AS value
WHERE name = 'fair_die';

INSERT INTO events (
    sample_space_id,
    event_name,
    description
)
SELECT
    sample_space_id,
    event_name,
    description
FROM sample_spaces
CROSS JOIN (
    VALUES
        (
            'even',
            'The die result is even.'
        ),
        (
            'high',
            'The die result is greater than four.'
        ),
        (
            'odd',
            'The die result is odd.'
        ),
        (
            'greater_than_three',
            'The die result is greater than three.'
        )
) AS event_data(event_name, description)
WHERE name = 'fair_die';

INSERT INTO event_outcomes (event_id, outcome_id)
SELECT
    e.event_id,
    o.outcome_id
FROM events e
JOIN outcomes o
  ON o.sample_space_id = e.sample_space_id
WHERE
    (e.event_name = 'even' AND o.outcome_code IN ('2', '4', '6'))
    OR
    (e.event_name = 'high' AND o.outcome_code IN ('5', '6'))
    OR
    (e.event_name = 'odd' AND o.outcome_code IN ('1', '3', '5'))
    OR
    (
        e.event_name = 'greater_than_three'
        AND o.outcome_code IN ('4', '5', '6')
    );

INSERT INTO probability_policies (
    policy_name,
    maximum_probability,
    minimum_sample_space_probability
)
VALUES
    ('low_risk_event', 0.25, 0.99),
    ('moderate_risk_event', 0.50, 0.99);

-- Retrieval and validation.
SELECT
    ss.name AS sample_space,
    o.outcome_code,
    o.probability
FROM sample_spaces ss
JOIN outcomes o
  ON o.sample_space_id = ss.sample_space_id
ORDER BY o.outcome_code::INT;

-- Event probability report.
SELECT
    e.event_name,
    event_probability(e.event_id) AS probability
FROM events e
ORDER BY e.event_name;

-- Inclusion-exclusion:
-- P(A ∪ B) = P(A) + P(B) - P(A ∩ B).
WITH event_pairs AS (
    SELECT
        e1.event_id AS first_event,
        e2.event_id AS second_event
    FROM events e1
    JOIN events e2
      ON e1.sample_space_id = e2.sample_space_id
    WHERE e1.event_name = 'even'
      AND e2.event_name = 'high'
)
SELECT
    event_probability(first_event)
    + event_probability(second_event)
    - intersection_probability(first_event, second_event)
        AS union_probability
FROM event_pairs;

-- Conditional probability.
SELECT
    conditional_probability(
        target.event_id,
        condition.event_id
    ) AS p_even_given_high
FROM events target
CROSS JOIN events condition
WHERE target.event_name = 'even'
  AND condition.event_name = 'high';

-- Independence evaluation.
SELECT
    first_event.event_name AS event_a,
    second_event.event_name AS event_b,
    event_probability(first_event.event_id) AS p_a,
    event_probability(second_event.event_id) AS p_b,
    intersection_probability(
        first_event.event_id,
        second_event.event_id
    ) AS p_a_and_b,
    events_are_independent(
        first_event.event_id,
        second_event.event_id
    ) AS independent
FROM events first_event
JOIN events second_event
  ON first_event.sample_space_id = second_event.sample_space_id
WHERE first_event.event_name = 'even'
  AND second_event.event_name = 'high';

-- Aggregation by event.
SELECT
    e.event_name,
    COUNT(eo.outcome_id) AS outcome_count,
    ROUND(
        event_probability(e.event_id),
        6
    ) AS event_probability
FROM events e
LEFT JOIN event_outcomes eo
  ON eo.event_id = e.event_id
GROUP BY e.event_id, e.event_name
ORDER BY event_probability DESC;

-- Policy evaluation workflow.
INSERT INTO probability_evaluations (
    policy_id,
    event_id,
    evaluated_probability,
    eligible
)
SELECT
    p.policy_id,
    e.event_id,
    event_probability(e.event_id),
    p.enabled
    AND event_probability(e.event_id) <= p.maximum_probability
FROM probability_policies p
CROSS JOIN events e
WHERE e.event_name IN ('even', 'high');

-- Eligibility report.
SELECT
    p.policy_name,
    e.event_name,
    pe.evaluated_probability,
    pe.eligible,
    pe.evaluated_at
FROM probability_evaluations pe
JOIN probability_policies p
  ON p.policy_id = pe.policy_id
JOIN events e
  ON e.event_id = pe.event_id
ORDER BY pe.evaluated_at, p.policy_name, e.event_name;

-- Transactional validation example.
BEGIN;

INSERT INTO conditional_observations (
    sample_space_id,
    target_event_id,
    condition_event_id,
    observed_probability
)
SELECT
    ss.sample_space_id,
    target.event_id,
    condition.event_id,
    conditional_probability(
        target.event_id,
        condition.event_id
    )
FROM sample_spaces ss
JOIN events target
  ON target.sample_space_id = ss.sample_space_id
JOIN events condition
  ON condition.sample_space_id = ss.sample_space_id
WHERE ss.name = 'fair_die'
  AND target.event_name = 'even'
  AND condition.event_name = 'high';

COMMIT;

-- Performance-oriented lookup.
EXPLAIN
SELECT
    e.event_name,
    event_probability(e.event_id)
FROM events e
WHERE e.sample_space_id = (
    SELECT sample_space_id
    FROM sample_spaces
    WHERE name = 'fair_die'
);
