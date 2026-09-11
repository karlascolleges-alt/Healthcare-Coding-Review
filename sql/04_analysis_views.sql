/*
I use this file to create the human review queue, status summary,
unmapped diagnosis report, and individual patient trace.
*/

USE DATABASE NIDHI_HEALTHCARE_ANALYTICS;
USE SCHEMA CODING_REVIEW;

/*
I create a view containing only the differences that require
human review. I exclude results with a Captured status.
*/

CREATE OR REPLACE VIEW VW_CODING_REVIEW_QUEUE AS
SELECT
    r.review_end_date,
    p.patient_id,
    p.patient_name,
    r.demo_condition_group,
    r.submitted_codes,
    r.documented_codes,
    r.latest_claim_date,
    r.latest_documentation_date,
    r.review_status,
    r.review_reason
FROM CODING_REVIEW_RESULT AS r
INNER JOIN PATIENT AS p
    ON p.patient_id = r.patient_id
WHERE r.review_status <> 'Captured';

/*
I create a summary view that counts the number of comparisons
assigned to each review status.
*/

CREATE OR REPLACE VIEW VW_REVIEW_STATUS_SUMMARY AS
SELECT
    review_end_date,
    review_status,
    COUNT(*) AS comparison_count
FROM CODING_REVIEW_RESULT
GROUP BY
    review_end_date,
    review_status;

/*
I create a view that keeps diagnosis codes visible when they
are not found in the active mapping table.
*/

CREATE OR REPLACE VIEW VW_UNMAPPED_DIAGNOSIS_CODES AS

WITH CONFIG AS (
    SELECT *
    FROM PROJECT_CONFIG
    WHERE config_id = 1
),

/*
I find submitted claim diagnosis codes that do not have an
active mapping for the selected mapping version.
*/

SUBMITTED_UNMAPPED AS (
    SELECT
        'SUBMITTED_CLAIM' AS source_name,
        cd.diagnosis_code,
        COUNT(*) AS occurrence_count
    FROM CLAIM_RECORD AS c
    INNER JOIN CLAIM_DIAGNOSIS AS cd
        ON cd.claim_id = c.claim_id
    CROSS JOIN CONFIG AS cfg
    LEFT JOIN DIAGNOSIS_GROUP_MAPPING AS m
        ON m.diagnosis_code = cd.diagnosis_code
        AND m.mapping_version = cfg.mapping_version
        AND m.active_flag = TRUE
    WHERE c.claim_status = 'Submitted'
        AND c.service_date BETWEEN
            cfg.review_start_date
            AND cfg.review_end_date
        AND m.diagnosis_code IS NULL
    GROUP BY
        cd.diagnosis_code
),

/*
I find documented diagnosis codes that do not have an active
mapping for the selected mapping version.
*/

DOCUMENTED_UNMAPPED AS (
    SELECT
        'DOCUMENTATION' AS source_name,
        d.diagnosis_code,
        COUNT(*) AS occurrence_count
    FROM DOCUMENTED_DIAGNOSIS AS d
    CROSS JOIN CONFIG AS cfg
    LEFT JOIN DIAGNOSIS_GROUP_MAPPING AS m
        ON m.diagnosis_code = d.diagnosis_code
        AND m.mapping_version = cfg.mapping_version
        AND m.active_flag = TRUE
    WHERE d.documentation_date BETWEEN
        cfg.review_start_date
        AND cfg.review_end_date
        AND m.diagnosis_code IS NULL
    GROUP BY
        d.diagnosis_code
)

SELECT
    source_name,
    diagnosis_code,
    occurrence_count
FROM SUBMITTED_UNMAPPED

UNION ALL

SELECT
    source_name,
    diagnosis_code,
    occurrence_count
FROM DOCUMENTED_UNMAPPED;

/*
I display the five records requiring human review.
*/

SELECT *
FROM VW_CODING_REVIEW_QUEUE
ORDER BY
    patient_id,
    demo_condition_group;

/*
I display the result totals.

I expect 9 captured results, 3 potential gaps, and
2 submitted code documentation reviews.
*/

SELECT *
FROM VW_REVIEW_STATUS_SUMMARY
ORDER BY
    comparison_count DESC;

/*
I display the unmapped diagnosis codes.

I expect Z00.00 from the submitted claims and E78.5 from
the documentation.
*/

SELECT *
FROM VW_UNMAPPED_DIAGNOSIS_CODES
ORDER BY
    source_name,
    diagnosis_code;

/*
I trace Patient 003 from the source information to the final
comparison results.
*/

SELECT
    p.patient_name,
    r.demo_condition_group,
    r.submitted_codes,
    r.documented_codes,
    r.review_status,
    r.review_reason
FROM CODING_REVIEW_RESULT AS r
INNER JOIN PATIENT AS p
    ON p.patient_id = r.patient_id
WHERE p.patient_id = 3
ORDER BY
    r.demo_condition_group;
