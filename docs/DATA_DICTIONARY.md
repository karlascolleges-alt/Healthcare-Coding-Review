# Data Dictionary

I created this data dictionary to explain the purpose and level of detail for each table in my project.

The level of detail is also called the grain. It describes what one row represents in a table.

## Configuration and mapping tables

### `PROJECT_CONFIG`

I use one row in this table to define the review period and mapping version used by the pipeline.

| Column | What I use it for |
|---|---|
| `config_id` | I use this value to identify the selected configuration |
| `review_start_date` | I use this date as the beginning of the review period |
| `review_end_date` | I use this date as the end of the review period |
| `mapping_version` | I use this value to select the diagnosis mapping version |
| `config_description` | I use this field to describe the configuration |

### `DIAGNOSIS_GROUP_MAPPING`

I use one row for each diagnosis code and mapping version.

I created the `DEMO_` condition groups only for this educational project. They are not official CMS HCC mappings or an official medical coding system.

| Column | What I use it for |
|---|---|
| `mapping_version` | I use this value to identify the mapping version |
| `diagnosis_code` | I use this field to store the diagnosis code |
| `diagnosis_name` | I use this field to store a readable diagnosis name |
| `demo_condition_group` | I use this field to place the diagnosis code into an educational condition group |
| `active_flag` | I use this value to determine whether the mapping is active |

## Source tables

### `PATIENT`

I use one row for each synthetic patient.

| Column | What I use it for |
|---|---|
| `patient_id` | I use this value as the unique patient identifier |
| `patient_name` | I use this field as a synthetic patient label |

### `CLAIM_RECORD`

I use one row for each synthetic claim.

| Column | What I use it for |
|---|---|
| `claim_id` | I use this value as the unique claim identifier |
| `patient_id` | I use this value to connect the claim to a patient |
| `service_date` | I use this date to determine whether the claim falls within the review period |
| `claim_status` | I use this field to include submitted claims and exclude voided claims |

### `CLAIM_DIAGNOSIS`

I use one row for each diagnosis code recorded on a claim.

| Column | What I use it for |
|---|---|
| `claim_diagnosis_id` | I use this value as the unique claim diagnosis identifier |
| `claim_id` | I use this value to connect the diagnosis code to a claim |
| `diagnosis_code` | I use this field to store the submitted diagnosis code |

### `DOCUMENTED_DIAGNOSIS`

I use one row for each documented diagnosis supplied in the synthetic data.

| Column | What I use it for |
|---|---|
| `documented_diagnosis_id` | I use this value as the unique documented diagnosis identifier |
| `patient_id` | I use this value to connect the documented diagnosis to a patient |
| `documentation_date` | I use this date to determine whether the record falls within the review period |
| `diagnosis_code` | I use this field to store the documented diagnosis code |

I use explicitly supplied diagnosis records. I do not extract or infer diagnoses from narrative clinical text.

## Result table

### `CODING_REVIEW_RESULT`

I use one row for each patient and educational condition group for one review end date.

| Column | What I use it for |
|---|---|
| `review_end_date` | I use this value to identify the review period |
| `mapping_version` | I use this value to record the mapping version used for the result |
| `patient_id` | I use this value to identify the patient |
| `demo_condition_group` | I use this field to identify the educational condition group |
| `submitted_codes` | I use this field to list the distinct submitted diagnosis codes supporting the group |
| `documented_codes` | I use this field to list the distinct documented diagnosis codes supporting the group |
| `submitted_code_count` | I use this value to count the distinct submitted diagnosis codes |
| `documented_code_count` | I use this value to count the distinct documented diagnosis codes |
| `latest_claim_date` | I use this field to record the most recent included claim date for the group |
| `latest_documentation_date` | I use this field to record the most recent included documentation date for the group |
| `submitted_present` | I use this value to show whether the group appears in the submitted claims |
| `documented_present` | I use this value to show whether the group appears in the documentation |
| `review_status` | I use this field to classify the comparison |
| `review_reason` | I use this field to explain why the status was assigned |
| `calculated_at` | I use this timestamp to record when the result was created |

## Audit table

### `REVIEW_RUN_AUDIT`

I use one row for each review end date.

| Column | What I use it for |
|---|---|
| `review_end_date` | I use this value to identify the completed review period |
| `config_id` | I use this value to identify the configuration used |
| `comparison_count` | I use this value to store the total number of comparisons |
| `captured_count` | I use this value to store the number of captured results |
| `potential_gap_count` | I use this value to store the number of potential gap results |
| `documentation_review_count` | I use this value to store the number of submitted code documentation reviews |
| `completed_at` | I use this timestamp to record when the audit result was created |

## Table relationships

I connect `CLAIM_RECORD` to `PATIENT` using `patient_id`.

I connect `CLAIM_DIAGNOSIS` to `CLAIM_RECORD` using `claim_id`.

I connect `DOCUMENTED_DIAGNOSIS` directly to `PATIENT` using `patient_id`.

I connect diagnosis records to `DIAGNOSIS_GROUP_MAPPING` using `diagnosis_code` and `mapping_version`.

I connect the final results to `PATIENT` using `patient_id`.
