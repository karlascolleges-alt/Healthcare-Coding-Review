# Healthcare Coding Review Workflow Service

I built this project to compare diagnosis groups found in submitted claims with diagnosis groups found in clinical documentation. The system identifies differences that may require human review while keeping every result traceable to its supporting records.

I developed the project as both a Snowflake data workflow and a reusable Python application. I later expanded it into a database backed workflow service that can execute reconciliation runs, track their progress, store review results, and support reviewer decisions through a FastAPI application programming interface.

All information used in this project is synthetic. The application does not determine whether a diagnosis is medically correct or automatically change a claim. It organizes differences into an explainable review queue for a person to investigate.

## Live application

I built an interactive Streamlit dashboard for exploring coding review results, filtering patient and condition records, examining unmapped diagnosis codes, and downloading the review queue.

[Open the live application](https://healthcare-coding-review.streamlit.app/)

## What I built

I created a Snowflake implementation that models the workflow using relational tables, reusable diagnosis mappings, transformation queries, analytical views, audit records, and data quality checks.

I also built a reusable Python package that reads the source files, validates their structure and relationships, applies a configurable review period, reconciles diagnosis groups, explains every result, and writes the completed outputs safely.

I developed a FastAPI service that executes the reconciliation pipeline and stores its results in a relational database. PostgreSQL supports the complete containerized environment, while SQLite provides a simple option for local development and isolated testing.

The application separates the reconciliation logic from the dashboard and application programming interface. This allows the same validated pipeline to support multiple interfaces without duplicating the underlying business rules.

## Workflow service

The workflow service includes the following endpoints.

* `POST /runs` starts a reconciliation run
* `GET /runs/{run_id}` returns the run status, timestamps, audit counts, and errors
* `GET /reviews` returns filtered and paginated review records
* `PATCH /reviews/{review_id}` saves reviewer progress and notes
* `GET /health` confirms that the service and database are available

Each reconciliation run moves through queued, running, completed, or failed states.

Each review record has a separate workflow state of pending, in review, or resolved. Updating the workflow state does not overwrite the original comparison result produced by the pipeline.

The
