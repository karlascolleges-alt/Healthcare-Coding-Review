/*
I use this file to map both diagnosis sources to the same
patient and condition group level.

I then compare the sources and create the review results.
*/

USE DATABASE NIDHI_HEALTHCARE_ANALYTICS;
USE SCHEMA CODING_REVIEW;

/*
I remove an existing result for the configured review period
before rebuilding it. This prevents duplicate results if I run
the file more than once.
*/

DELETE FROM CODING_REVIEW_RESULT
WHERE review_end_date = (
    SELECT review_end_date
    FROM PROJECT_CONFIG
    WHERE config_id = 1
);

INSERT INTO CODING_REVIEW_RESULT (
    review_end_date,
    mapping_version,
    patient_id,
    demo_condition_group,
    submitted_codes,
    documented_codes,
    submitted_code_count,
    documented_code_count,
    latest_claim_date,
    latest_documentation_date,
    submitted_present,
    documented_present,
    review_status,
    review_reason
)

/*
I select the review dates and mapping version that I want
to use throughout the comparison.
*/

WITH CONFIG AS (
    SELECT *
    FROM PROJECT_CONFIG
    WHERE config_id = 1
),

/*
I connect each submitted claim diagnosis to its educational
condition group.

I include only submitted claims within the configured review
period. I then summarize the results so that each patient and
condition group appears once.
*/

SUBMITTED_GROUPS AS (
    SELECT
        c.patient_id,
        m.demo_condition_group,
        LISTAGG(
            DISTINCT cd.diagnosis_code,
            ', '
        ) WITHIN GROUP (
            ORDER BY cd.diagnosis_code
        ) AS submitted_codes,
        COUNT(
            DISTINCT cd.diagnosis_code
        ) AS submitted_code_count,
        MAX(c.service_date) AS latest_claim_date
    FROM CLAIM_RECORD AS c
    INNER JOIN CLAIM_DIAGNOSIS AS cd
        ON cd.claim_id = c.claim_id
    CROSS JOIN CONFIG AS cfg
    INNER JOIN DIAGNOSIS_GROUP_MAPPING AS m
        ON m.diagnosis_code = cd.diagnosis_code
        AND m.mapping_version = cfg.mapping_version
        AND m.active_flag = TRUE
    WHERE c.claim_status = 'Submitted'
        AND c.service_date BETWEEN
            cfg.review_start_date
            AND cfg.review_end_date
    GROUP BY
        c.patient_id,
        m.demo_condition_group
),

/*
I map the documented diagnosis records to the same educational
condition groups.

I include only documentation within the configured review period.
I then summarize the results so that each patient and condition
group appears once.
*/

DOCUMENTED_GROUPS AS (
    SELECT
        d.patient_id,
        m.demo_condition_group,
        LISTAGG(
            DISTINCT d.diagnosis_code,
            ', '
        ) WITHIN GROUP (
            ORDER BY d.diagnosis_code
        ) AS documented_codes,
        COUNT(
            DISTINCT d.diagnosis_code
        ) AS documented_code_count,
        MAX(
            d.documentation_date
        ) AS latest_documentation_date
    FROM DOCUMENTED_DIAGNOSIS AS d
    CROSS JOIN CONFIG AS cfg
    INNER JOIN DIAGNOSIS_GROUP_MAPPING AS m
        ON m.diagnosis_code = d.diagnosis_code
        AND m.mapping_version = cfg.mapping_version
        AND m.active_flag = TRUE
    WHERE d.documentation_date BETWEEN
        cfg.review_start_date
        AND cfg.review_end_date
    GROUP BY
        d.patient_id,
        m.demo_condition_group
),

/*
I use a full outer join so that I keep matches and both types
of differences.

COALESCE selects the available patient and condition group
when a result appears in only one source.
*/

COMPARED_GROUPS AS (
    SELECT
        cfg.review_end_date,
        cfg.mapping_version,
        COALESCE(
            s.patient_id,
            d.patient_id
        ) AS patient_id,
        COALESCE(
            s.demo_condition_group,
            d.demo_condition_group
        ) AS demo_condition_group,
        s.submitted_codes,
        d.documented_codes,
        COALESCE(
            s.submitted_code_count,
            0
        ) AS submitted_code_count,
        COALESCE(
            d.documented_code_count,
            0
        ) AS documented_code_count,
        s.latest_claim_date,
        d.latest_documentation_date,
        s.patient_id IS NOT NULL AS submitted_present,
        d.patient_id IS NOT NULL AS documented_present
    FROM SUBMITTED_GROUPS AS s
    FULL OUTER JOIN DOCUMENTED_GROUPS AS d
        ON d.patient_id = s.patient_id
        AND d.demo_condition_group = s.demo_condition_group
    CROSS JOIN CONFIG AS cfg
)

/*
I assign a status and explanation based on whether each
condition group appears in the submitted claims, documentation,
or both sources.
*/

SELECT
    review_end_date,
    mapping_version,
    patient_id,
    demo_condition_group,
    submitted_codes,
    documented_codes,
    submitted_code_count,
    documented_code_count,
    latest_claim_date,
    latest_documentation_date,
    submitted_present,
    documented_present,
    CASE
        WHEN submitted_present
            AND documented_present
            THEN 'Captured'
        WHEN NOT submitted_present
            AND documented_present
            THEN 'Potential Gap - Review Required'
        ELSE
            'Submitted Code - Documentation Review Required'
    END AS review_status,
    CASE
        WHEN submitted_present
            AND documented_present
            THEN
                'Group appears in both submitted claims and documentation'
        WHEN NOT submitted_present
            AND documented_present
            THEN
                'Documented group is absent from submitted claims in the review period'
        ELSE
            'Submitted group is absent from documentation in the review period'
    END AS review_reason
FROM COMPARED_GROUPS;

/*
I rebuild the audit result for the configured review period.
The audit table records the total number of comparisons and
the number assigned to each status.
*/

DELETE FROM REVIEW_RUN_AUDIT
WHERE review_end_date = (
    SELECT review_end_date
    FROM PROJECT_CONFIG
    WHERE config_id = 1
);

INSERT INTO REVIEW_RUN_AUDIT (
    review_end_date,
    config_id,
    comparison_count,
    captured_count,
    potential_gap_count,
    documentation_review_count
)
SELECT
    review_end_date,
    1 AS config_id,
    COUNT(*) AS comparison_count,
    COUNT_IF(
        review_status = 'Captured'
    ) AS captured_count,
    COUNT_IF(
        review_status = 'Potential Gap - Review Required'
    ) AS potential_gap_count,
    COUNT_IF(
        review_status =
            'Submitted Code - Documentation Review Required'
    ) AS documentation_review_count
FROM CODING_REVIEW_RESULT
GROUP BY review_end_date;
