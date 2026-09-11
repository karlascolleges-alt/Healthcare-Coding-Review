# Healthcare Coding Review Workflow Service

I built a deployed healthcare workflow application that compares diagnosis groups found in submitted claims with diagnosis groups found in clinical documentation.

The application identifies matching records and differences that may require human review. Reviewers can filter the results, track their progress, add notes, and save their decisions in a PostgreSQL database.

I developed the reconciliation pipeline as a reusable Python package and exposed it through a FastAPI service. The Streamlit dashboard communicates with the API, while SQLAlchemy manages workflow data stored in PostgreSQL.

All records and diagnosis mappings used in this project are synthetic. The application does not determine coding accuracy or modify claims. It organizes differences into an explainable queue for human investigation.

## Live application

[Open the Streamlit application](https://healthcare-coding-review.streamlit.app/)

[Explore the FastAPI documentation](https://healthcare-coding-review.onrender.com/docs)

[Check the API and database health](https://healthcare-coding-review.onrender.com/health)

The FastAPI service uses a free hosting plan and may require approximately one minute to wake after a period of inactivity.

## Deployed architecture

The Streamlit dashboard provides the user interface.

The FastAPI service validates requests, starts reconciliation runs, retrieves stored results, and saves reviewer updates.

The Python pipeline validates and compares the synthetic claim and documentation data.

Neon PostgreSQL stores pipeline history, review records, workflow statuses, and reviewer notes.

Render hosts the containerized FastAPI service.

Streamlit Community Cloud hosts the dashboard.

## How the application works

1. A user selects a review period and starts a reconciliation run

2. Streamlit sends the request to the FastAPI service

3. FastAPI validates the request and creates a queued pipeline run

4. The reusable Python pipeline validates and reconciles the source records

5. SQLAlchemy stores the run metadata and comparison results in PostgreSQL

6. Streamlit retrieves the database backed results through the API

7. A reviewer marks records as pending, in review, or resolved and adds notes

8. FastAPI saves the reviewer updates without replacing the original pipeline classification

## Results

The synthetic dataset produces 14 patient and condition group comparisons.

Nine condition groups appear in both submitted claims and clinical documentation.

Three condition groups appear only in documentation and require potential gap review.

Two condition groups appear only in submitted claims and require documentation review.

Five differences enter the human review queue.

Three unmapped diagnosis code occurrences remain visible for investigation.

## Workflow API

`POST /runs` starts a reconciliation run

`GET /runs/{run_id}` retrieves run status, timestamps, counts, and errors

`GET /reviews` retrieves filtered and paginated review records

`PATCH /reviews/{review_id}` saves reviewer status and notes

`GET /health` verifies the API and database connection

Pipeline runs move through queued, running, completed, and failed states.

Review records move through pending, in review, and resolved states. The reviewer workflow status remains separate from the original comparison result so the system preserves both automated output and human activity.

## Engineering practices

I separated the domain logic from the dashboard, API, and database layers so multiple interfaces can use the same reconciliation pipeline.

I implemented input schema validation, unique identifier checks, relationship validation, configurable review periods, versioned diagnosis mappings, and unmapped code reporting.

I aggregated each source to one patient and condition group before comparison to prevent duplicate evidence from inflating the results.

I used atomic file operations to prevent failed executions from leaving partially written output files.

I added typed API contracts, structured errors, database backed pagination, transaction handling, workflow timestamps, health monitoring, and application logging.

I created automated unit and integration tests covering validation, reconciliation behavior, expected outputs, API persistence, pagination, reviewer updates, command line execution, and API client errors.

GitHub Actions runs Python quality checks, parses the Snowflake SQL, executes the pipeline, and runs the automated test suite with an 85 percent coverage requirement for the reusable pipeline package.

## Technologies

Python

FastAPI

Streamlit

PostgreSQL

SQLAlchemy

Snowflake SQL

Pydantic

HTTPX

Pytest

Ruff

SQLFluff

Docker

GitHub Actions

Render

Neon
