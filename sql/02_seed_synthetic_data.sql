
USE DATABASE NIDHI_HEALTHCARE_ANALYTICS;
USE SCHEMA CODING_REVIEW;

TRUNCATE TABLE PROJECT_CONFIG;
TRUNCATE TABLE CLAIM_DIAGNOSIS;
TRUNCATE TABLE CLAIM_RECORD;
TRUNCATE TABLE DOCUMENTED_DIAGNOSIS;
TRUNCATE TABLE DIAGNOSIS_GROUP_MAPPING;
TRUNCATE TABLE PATIENT;

INSERT INTO PROJECT_CONFIG
VALUES (
    1,
    DATE '2026-01-01',
    DATE '2026-06-30',
    'DEMO_V1',
    'Educational diagnosis group comparison requiring human review'
);

INSERT INTO PATIENT (
    patient_id,
    patient_name
)
VALUES
    (1, 'Coding Patient 001'),
    (2, 'Coding Patient 002'),
    (3, 'Coding Patient 003'),
    (4, 'Coding Patient 004'),
    (5, 'Coding Patient 005'),
    (6, 'Coding Patient 006'),
    (7, 'Coding Patient 007'),
    (8, 'Coding Patient 008'),
    (9, 'Coding Patient 009'),
    (10, 'Coding Patient 010');

INSERT INTO DIAGNOSIS_GROUP_MAPPING (
    mapping_version,
    diagnosis_code,
    diagnosis_name,
    demo_condition_group,
    active_flag
)
VALUES
    (
        'DEMO_V1',
        'I10',
        'Hypertension',
        'DEMO_CARDIOVASCULAR',
        TRUE
    ),
    (
        'DEMO_V1',
        'E11.9',
        'Type 2 diabetes',
        'DEMO_DIABETES',
        TRUE
    ),
    (
        'DEMO_V1',
        'I50.9',
        'Heart failure',
        'DEMO_HEART_FAILURE',
        TRUE
    ),
    (
        'DEMO_V1',
        'J44.9',
        'Chronic obstructive lung disease',
        'DEMO_LUNG',
        TRUE
    ),
    (
        'DEMO_V1',
        'N18.31',
        'Chronic kidney disease stage 3',
        'DEMO_KIDNEY',
        TRUE
    ),
    (
        'DEMO_V1',
        'F32.9',
        'Depressive disorder',
        'DEMO_BEHAVIORAL',
        TRUE
    );

/*
I use claims 11 and 12 to test the status and date filters.

I use claim 13 to repeat I10 for Patient 001. This confirms that
repeated claim evidence does not create a duplicate final group result.
*/

INSERT INTO CLAIM_RECORD (
    claim_id,
    patient_id,
    service_date,
    claim_status
)
VALUES
    (1, 1, DATE '2026-01-10', 'Submitted'),
    (2, 2, DATE '2026-01-18', 'Submitted'),
    (3, 3, DATE '2026-02-02', 'Submitted'),
    (4, 4, DATE '2026-02-20', 'Submitted'),
    (5, 5, DATE '2026-03-05', 'Submitted'),
    (6, 6, DATE '2026-03-19', 'Submitted'),
    (7, 7, DATE '2026-04-08', 'Submitted'),
    (8, 8, DATE '2026-04-27', 'Submitted'),
    (9, 9, DATE '2026-05-11', 'Submitted'),
    (10, 10, DATE '2026-05-30', 'Submitted'),
    (11, 10, DATE '2026-04-01', 'Voided'),
    (12, 2, DATE '2025-12-15', 'Submitted'),
    (13, 1, DATE '2026-05-01', 'Submitted');

INSERT INTO CLAIM_DIAGNOSIS (
    claim_diagnosis_id,
    claim_id,
    diagnosis_code
)
VALUES
    (1, 1, 'I10'),
    (2, 1, 'E11.9'),
    (3, 2, 'E11.9'),
    (4, 3, 'I10'),
    (5, 4, 'I10'),
    (6, 4, 'J44.9'),
    (7, 5, 'I50.9'),
    (8, 6, 'I10'),
    (9, 7, 'F32.9'),
    (10, 8, 'I10'),
    (11, 9, 'J44.9'),
    (12, 10, 'Z00.00'),
    (13, 11, 'I50.9'),
    (14, 12, 'I10'),
    (15, 13, 'I10');

/*
I use documented diagnosis 15 to test the review period.
Its documentation date is outside the configured period.
*/

INSERT INTO DOCUMENTED_DIAGNOSIS (
    documented_diagnosis_id,
    patient_id,
    documentation_date,
    diagnosis_code
)
VALUES
    (1, 1, DATE '2026-01-10', 'I10'),
    (2, 1, DATE '2026-01-10', 'E11.9'),
    (3, 2, DATE '2026-01-18', 'E11.9'),
    (4, 3, DATE '2026-02-02', 'I10'),
    (5, 3, DATE '2026-02-02', 'E11.9'),
    (6, 4, DATE '2026-02-20', 'I10'),
    (7, 5, DATE '2026-03-05', 'I50.9'),
    (8, 6, DATE '2026-03-19', 'I10'),
    (9, 6, DATE '2026-03-19', 'N18.31'),
    (10, 7, DATE '2026-04-08', 'F32.9'),
    (11, 8, DATE '2026-04-27', 'I10'),
    (12, 8, DATE '2026-04-27', 'J44.9'),
    (13, 9, DATE '2026-05-11', 'E78.5'),
    (14, 10, DATE '2026-05-30', 'E78.5'),
    (15, 2, DATE '2025-12-15', 'I50.9');
