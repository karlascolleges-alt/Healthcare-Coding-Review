# Architecture

## Connected interface

The Streamlit application uses `WorkflowAPIClient` as its only connection to
the workflow service. The client owns HTTP communication and translates network
or service failures into messages the interface can display safely.

When `API_BASE_URL` is configured, Streamlit checks service and database health,
starts pipeline runs, retrieves run metadata, requests filtered pages of review
records, and persists reviewer updates. When the setting is absent, the
dashboard remains usable with stored synthetic demonstration results and
clearly identifies that mode to the user.

The dashboard does not connect directly to PostgreSQL. FastAPI remains the
boundary for validation, workflow execution, and persistence. This keeps
database credentials out of the interface and ensures that every consumer uses
the same application rules.

## Workflow-service architecture

1. A client submits a typed run request to `POST /runs`.
2. FastAPI validates the review period and mapping version with Pydantic.
3. SQLAlchemy persists a queued run in SQLite or PostgreSQL.
4. A background task invokes the existing reusable `ReviewPipeline`.
5. The pipeline validates relationships, reconciles both diagnosis sources,
   writes atomic file outputs, and returns structured results.
6. The workflow layer persists results and audit counts in one database-backed
   run history.
7. Clients retrieve filtered, paginated results and update reviewer workflow
   state through typed endpoints.

The pipeline classification and human workflow state are intentionally stored
separately. A result can remain a `Potential Gap Review Required` classification
while its operational state changes from `pending` to `resolved`.

## Reliability boundaries

Pipeline failures are caught and persisted as a failed run with a bounded error
message and completion timestamp. API not-found responses use stable error codes.
Atomic CSV replacement protects existing exports, while database transactions
protect workflow metadata and review updates.

FastAPI background tasks are appropriate for this portfolio-scale service. A
production system with long-running or high-volume jobs would move execution to
a durable queue and worker system so jobs can survive API restarts.

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
