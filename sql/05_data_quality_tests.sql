/*
I use this file to validate the source data, expected results,
filtering logic, review statuses, and table relationships.
*/

USE DATABASE NIDHI_HEALTHCARE_ANALYTICS;
USE SCHEMA CODING_REVIEW;

/*
I confirm that each source table contains the expected number
of synthetic records.
*/

SELECT
    'SOURCE COUNTS' AS test_name,
    IFF(
        (SELECT COUNT(*) FROM PATIENT) = 10
        AND (SELECT COUNT(*) FROM CLAIM_RECORD) = 13
        AND (SELECT COUNT(*) FROM CLAIM_DIAGNOSIS) = 15
        AND (SELECT COUNT(*) FROM DOCUMENTED_DIAGNOSIS) = 15
        AND (SELECT COUNT(*) FROM DIAGNOSIS_GROUP_MAPPING) = 6,
        'PASS',
        'FAIL'
    ) AS test_status;

/*
I define the expected number of results for each status and
compare those totals with the actual pipeline results.
*/

WITH EXPECTED AS (
    SELECT
        'Captured' AS review_status,
        9 AS expected_count

    UNION ALL

    SELECT
        'Potential Gap Review Required',
        3

    UNION ALL

    SELECT
        'Submitted Code Documentation Review Required',
        2
),

ACTUAL AS (
    SELECT
        review_status,
        COUNT(*) AS actual_count
    FROM CODING_REVIEW_RESULT
    GROUP BY
        review_status
)

SELECT
    'STATUS DISTRIBUTION ' || e.review_status AS test_name,
    IFF(
        e.expected_count = COALESCE(a.actual_count, 0),
        'PASS',
        'FAIL'
    ) AS test_status,
    e.expected_count,
    COALESCE(a.actual_count, 0) AS actual_count
FROM EXPECTED AS e
LEFT JOIN ACTUAL AS a
    ON a.review_status = e.review_status;

/*
I confirm that each patient and condition group combination
appears only once in the final result.
*/

SELECT
    'ONE ROW PER PATIENT AND GROUP' AS test_name,
    IFF(
        COUNT(*) = COUNT(
            DISTINCT patient_id || '|' || demo_condition_group
        ),
        'PASS',
        'FAIL'
    ) AS test_status
FROM CODING_REVIEW_RESULT;

/*
I confirm that the heart failure diagnosis from the voided
claim for Patient 010 does not enter the final results.
*/

SELECT
    'VOIDED CLAIM EXCLUDED' AS test_name,
    IFF(
        COUNT(*) = 0,
        'PASS',
        'FAIL'
    ) AS test_status
FROM CODING_REVIEW_RESULT
WHERE patient_id = 10
    AND demo_condition_group = 'DEMO_HEART_FAILURE';

/*
I confirm that the records dated before the configured review
period for Patient 002 do not enter the final results.
*/

SELECT
    'OUT OF PERIOD RECORDS EXCLUDED' AS test_name,
    IFF(
        COUNT(*) = 0,
        'PASS',
        'FAIL'
    ) AS test_status
FROM CODING_REVIEW_RESULT
WHERE patient_id = 2
    AND demo_condition_group IN (
        'DEMO_CARDIOVASCULAR',
        'DEMO_HEART_FAILURE'
    );

/*
I expect this query to return zero rows.

I use it to find impossible combinations or results that have
an incorrect review status.
*/

SELECT *
FROM CODING_REVIEW_RESULT
WHERE (
    NOT submitted_present
    AND NOT documented_present
)
OR (
    review_status = 'Potential Gap Review Required'
    AND (
        submitted_present
        OR NOT documented_present
    )
)
OR (
    review_status =
        'Submitted Code Documentation Review Required'
    AND (
        NOT submitted_present
        OR documented_present
    )
);

/*
I expect this query to return zero rows.

I use it to identify claim diagnosis records that do not have
a matching claim record.
*/

SELECT
    cd.*
FROM CLAIM_DIAGNOSIS AS cd
LEFT JOIN CLAIM_RECORD AS c
    ON c.claim_id = cd.claim_id
WHERE c.claim_id IS NULL;

/*
I display the intentionally unmapped diagnosis codes so I can
confirm that they remain visible instead of being silently lost.
*/

SELECT
    source_name,
    diagnosis_code,
    occurrence_count
FROM VW_UNMAPPED_DIAGNOSIS_CODES
ORDER BY
    source_name,
    diagnosis_code;
