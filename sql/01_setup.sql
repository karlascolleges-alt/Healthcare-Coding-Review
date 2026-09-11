/*
I use this file to create the database, schema, and tables for my
retrospective diagnosis coding review project.
*/

CREATE DATABASE IF NOT EXISTS NIDHI_HEALTHCARE_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS
    NIDHI_HEALTHCARE_ANALYTICS.CODING_REVIEW;

USE DATABASE NIDHI_HEALTHCARE_ANALYTICS;
USE SCHEMA CODING_REVIEW;

CREATE OR REPLACE TABLE PROJECT_CONFIG (
    config_id          INTEGER      NOT NULL,
    review_start_date  DATE         NOT NULL,
    review_end_date    DATE         NOT NULL,
    mapping_version    VARCHAR(20)  NOT NULL,
    config_description VARCHAR(200) NOT NULL,
    CONSTRAINT pk_coding_config PRIMARY KEY (config_id)
);

CREATE OR REPLACE TABLE PATIENT (
    patient_id   INTEGER     NOT NULL,
    patient_name VARCHAR(40) NOT NULL,
    CONSTRAINT pk_coding_patient PRIMARY KEY (patient_id)
);

CREATE OR REPLACE TABLE CLAIM_RECORD (
    claim_id     INTEGER     NOT NULL,
    patient_id   INTEGER     NOT NULL,
    service_date DATE        NOT NULL,
    claim_status VARCHAR(15) NOT NULL,
    CONSTRAINT pk_claim_record PRIMARY KEY (claim_id),
    CONSTRAINT fk_claim_patient
        FOREIGN KEY (patient_id) REFERENCES PATIENT (patient_id)
);

CREATE OR REPLACE TABLE CLAIM_DIAGNOSIS (
    claim_diagnosis_id INTEGER     NOT NULL,
    claim_id           INTEGER     NOT NULL,
    diagnosis_code     VARCHAR(10) NOT NULL,
    CONSTRAINT pk_claim_diagnosis PRIMARY KEY (claim_diagnosis_id),
    CONSTRAINT fk_claim_diagnosis_claim
        FOREIGN KEY (claim_id) REFERENCES CLAIM_RECORD (claim_id)
);

CREATE OR REPLACE TABLE DOCUMENTED_DIAGNOSIS (
    documented_diagnosis_id INTEGER     NOT NULL,
    patient_id              INTEGER     NOT NULL,
    documentation_date      DATE        NOT NULL,
    diagnosis_code          VARCHAR(10) NOT NULL,
    CONSTRAINT pk_documented_diagnosis
        PRIMARY KEY (documented_diagnosis_id),
    CONSTRAINT fk_documented_diagnosis_patient
        FOREIGN KEY (patient_id) REFERENCES PATIENT (patient_id)
);

/*
I use educational condition groups in this project.
These groups are not official CMS HCC mappings.
*/

CREATE OR REPLACE TABLE DIAGNOSIS_GROUP_MAPPING (
    mapping_version       VARCHAR(20)  NOT NULL,
    diagnosis_code       VARCHAR(10)  NOT NULL,
    diagnosis_name       VARCHAR(100) NOT NULL,
    demo_condition_group VARCHAR(30)  NOT NULL,
    active_flag          BOOLEAN      NOT NULL,
    CONSTRAINT pk_diagnosis_group_mapping
        PRIMARY KEY (mapping_version, diagnosis_code)
);

/*
I store one result for each patient and condition group
within one review period.
*/

CREATE OR REPLACE TABLE CODING_REVIEW_RESULT (
    review_end_date           DATE          NOT NULL,
    mapping_version           VARCHAR(20)   NOT NULL,
    patient_id                INTEGER       NOT NULL,
    demo_condition_group      VARCHAR(30)   NOT NULL,
    submitted_codes           VARCHAR(200),
    documented_codes          VARCHAR(200),
    submitted_code_count      INTEGER       NOT NULL,
    documented_code_count     INTEGER       NOT NULL,
    latest_claim_date         DATE,
    latest_documentation_date DATE,
    submitted_present         BOOLEAN       NOT NULL,
    documented_present        BOOLEAN       NOT NULL,
    review_status             VARCHAR(60)   NOT NULL,
    review_reason             VARCHAR(200)  NOT NULL,
    calculated_at             TIMESTAMP_NTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_coding_review_result
        PRIMARY KEY (
            review_end_date,
            patient_id,
            demo_condition_group
        ),
    CONSTRAINT fk_coding_review_result_patient
        FOREIGN KEY (patient_id) REFERENCES PATIENT (patient_id)
);

CREATE OR REPLACE TABLE REVIEW_RUN_AUDIT (
    review_end_date            DATE          NOT NULL,
    config_id                  INTEGER       NOT NULL,
    comparison_count           INTEGER       NOT NULL,
    captured_count             INTEGER       NOT NULL,
    potential_gap_count        INTEGER       NOT NULL,
    documentation_review_count INTEGER       NOT NULL,
    completed_at               TIMESTAMP_NTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_review_run_audit
        PRIMARY KEY (review_end_date)
);
