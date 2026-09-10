# Architecture

## My design goal

I designed the project so the reconciliation rules do not depend on one interface or one execution environment. The Snowflake workflow and Python workflow implement the same review process while serving different purposes.

## My processing layers

### Source layer

I store synthetic patients, claims, claim diagnoses, documented diagnoses, and diagnosis mappings as separate inputs. This preserves the relationships found in the source data.

### Validation layer

I confirm that every dataset contains its required columns. I check primary identifiers for duplicates and confirm that claims and diagnoses connect to existing parent records.

### Transformation layer

I apply one review period and one mapping version to both diagnosis sources. I then summarize each source to one patient and condition group record before comparing them.

### Review layer

I compare the complete set of patient and condition groups. I retain records found in both sources and records found in only one source. Every result contains presence indicators, supporting codes, dates, a review status, and a plain language explanation.

### Output layer

I produce the complete comparison, the human review queue, a status summary, an unmapped code report, and a run audit record. I write each file atomically so an interrupted run cannot replace a valid output with a partial file.

### Interface layer

I keep the presentation logic outside the pipeline. Streamlit provides an interactive review experience. FastAPI provides read only access to results and supports filtering by review status or patient.

## My reliability controls

I test expected results and edge cases in Python and Snowflake SQL. GitHub Actions checks Python quality, parses the Snowflake SQL, runs the complete pipeline, and measures test coverage for every proposed change.

## My privacy boundary

I use only synthetic records and educational condition groups. I do not include protected health information, credentials, proprietary mappings, or automatic claim changes.
