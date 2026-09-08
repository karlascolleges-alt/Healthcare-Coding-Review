# Technical Walkthrough

I created this walkthrough to explain how data moves through my Snowflake healthcare coding review project.

## 1. I define the review configuration

I begin with `PROJECT_CONFIG`.

This table identifies the beginning and end of the review period. It also identifies the version of the diagnosis mapping that I want to use.

I use one configuration throughout the pipeline so the submitted claims and documented diagnoses are evaluated with the same dates and mapping version.

## 2. I organize the source data

I separate the source information into four tables.

1. I use `PATIENT` to store one row for each synthetic patient.
2. I use `CLAIM_RECORD` to store the claim date and claim status.
3. I use `CLAIM_DIAGNOSIS` to store the diagnosis codes connected to each claim.
4. I use `DOCUMENTED_DIAGNOSIS` to store the diagnosis codes found in the synthetic documentation records.

A claim can contain several diagnosis codes. I keep the claim and diagnosis information in separate tables to represent that relationship accurately.

## 3. I map diagnosis codes to condition groups

I use `DIAGNOSIS_GROUP_MAPPING` to connect individual diagnosis codes to educational condition groups.

For example, I map `I10` to `DEMO_CARDIOVASCULAR` and `E11.9` to `DEMO_DIABETES`.

I include a mapping version and an active indicator. This allows me to select one mapping version without changing the main comparison logic.

I created these condition groups for this educational project. They are not official CMS HCC mappings.

## 4. I filter the submitted claims

In `SUBMITTED_GROUPS`, I include only claims with a `Submitted` status.

I also include only service dates between the configured review start date and review end date.

This filtering excludes the voided claim and the claim dated before the review period.

## 5. I summarize submitted diagnosis groups

A patient can have the same diagnosis group on more than one claim.

I summarize the submitted information by `patient_id` and `demo_condition_group` before performing the comparison.

I use `LISTAGG` to retain the distinct diagnosis codes supporting each condition group.

I use `COUNT` with `DISTINCT` to count the unique diagnosis codes.

I use `MAX` to retain the most recent included claim date.

This creates one submitted row for each patient and condition group.

## 6. I summarize documented diagnosis groups

In `DOCUMENTED_GROUPS`, I apply the same review period to the documented diagnosis records.

I map each diagnosis code to an educational condition group.

I then summarize the documentation by `patient_id` and `demo_condition_group`.

I use `LISTAGG` to retain the documented diagnosis codes.

I use `COUNT` with `DISTINCT` to count the unique documented codes.

I use `MAX` to retain the most recent documentation date.

This creates one documented row for each patient and condition group.

## 7. I compare both sources

In `COMPARED_GROUPS`, I compare `SUBMITTED_GROUPS` with `DOCUMENTED_GROUPS`.

I use a full outer join based on `patient_id` and `demo_condition_group`.

I selected a full outer join because I needed to retain three possible outcomes.

1. I retain groups found in both sources.
2. I retain groups found only in the documentation.
3. I retain groups found only in the submitted claims.

An inner join would retain only the matches. That would remove the differences that I need for the review queue.

## 8. I use `COALESCE` to retain the identifiers

A full outer join can produce a missing value on either side of the comparison.

I use `COALESCE` to select the available `patient_id` and `demo_condition_group`.

This allows me to retain the correct identifiers even when a condition group appears in only one source.

## 9. I create presence indicators

I create `submitted_present` to show whether the condition group exists in the submitted claims.

I create `documented_present` to show whether the condition group exists in the documentation.

These indicators allow me to classify each comparison clearly.

## 10. I assign the review status

I use a `CASE` statement to assign one of three statuses.

| Submitted | Documented | Status |
|---|---|---|
| Yes | Yes | `Captured` |
| No | Yes | `Potential Gap - Review Required` |
| Yes | No | `Submitted Code - Documentation Review Required` |

I assign `Captured` when the condition group appears in both sources.

I assign `Potential Gap - Review Required` when the condition group appears in the documentation but not in the submitted claims.

I assign `Submitted Code - Documentation Review Required` when the condition group appears in the submitted claims but not in the documentation.

These statuses identify records for human review. They do not prove that a coding error occurred.

## 11. I create the human review queue

I create `VW_CODING_REVIEW_QUEUE` from the final result table.

I exclude records with a `Captured` status.

This leaves five records that require further review.

The queue contains the patient, condition group, supporting diagnosis codes, latest dates, review status, and review reason.

## 12. I create the status summary

I create `VW_REVIEW_STATUS_SUMMARY` to count the number of results assigned to each status.

My synthetic data produces the following results.

| Status | Count |
|---|---:|
| `Captured` | 9 |
| `Potential Gap - Review Required` | 3 |
| `Submitted Code - Documentation Review Required` | 2 |

The complete output contains 14 patient and condition group comparisons.

## 13. I keep unmapped codes visible

The mapped comparison uses diagnosis codes found in `DIAGNOSIS_GROUP_MAPPING`.

A code missing from that table cannot enter the grouped comparison.

I created `VW_UNMAPPED_DIAGNOSIS_CODES` so those records remain visible.

The synthetic data includes `Z00.00` on the submitted claims side and `E78.5` on the documentation side.

I report these codes separately instead of allowing them to disappear from the analysis.

## 14. I record the run totals

I use `REVIEW_RUN_AUDIT` to store the total comparison count and the count assigned to each status.

I delete the existing audit record for the review date before inserting the updated totals.

This allows me to rerun the pipeline without creating duplicate audit records for the same review period.

## 15. I test specific edge cases

I included several intentional test cases in the synthetic data.

1. I included a voided claim to confirm that it is excluded.
2. I included a claim outside the review period.
3. I included a documented diagnosis outside the review period.
4. I repeated `I10` on two claims for Patient 001.
5. I included diagnosis codes missing from the mapping table.
6. I included matches and both types of differences.

These cases help me confirm that the pipeline handles more than the simplest matching scenario.

## Example using Patient 003

Patient 003 has submitted diagnosis code `I10`.

The documentation for Patient 003 contains `I10` and `E11.9`.

I map `I10` to `DEMO_CARDIOVASCULAR`. Because this group appears in both sources, I classify it as `Captured`.

I map `E11.9` to `DEMO_DIABETES`. Because this group appears only in the documentation, I classify it as `Potential Gap - Review Required`.

I place the diabetes result in the human review queue. I do not automatically add the diagnosis to a claim.

## Design choices and limitations

I used an educational condition group comparison because it is easy to trace and explain. The result identifies differences, but it does not establish whether the submitted coding is correct.

I intentionally used a small mapping table. I cannot generalize it to real coding or risk adjustment work.

I used `LISTAGG` because it makes the supporting diagnosis codes easy to read in this small project. A larger system might store the code level history in a separate table.

I used a repeatable batch rebuild for the project. I did not design it as an incremental production pipeline.

I used only synthetic data. I did not use protected health information, credentials, or information from a payer, provider, or health system.
