# Healthcare Coding Review Workflow Service

## Connected application

I connected the Streamlit dashboard to the FastAPI workflow service so the
interface can now start reconciliation runs, retrieve persisted results, filter
and paginate the review queue, and save reviewer decisions and notes.

The dashboard automatically uses the connected workflow when `API_BASE_URL` is
available. It uses the stored synthetic results in a clearly labeled
demonstration mode when the API address has not been configured.

The connected workflow works as follows.

1. A user starts a reconciliation run from Streamlit
2. Streamlit sends the run request to FastAPI
3. FastAPI validates the request and executes the reusable Python pipeline
4. SQLAlchemy stores the run history and review records in PostgreSQL
5. Streamlit retrieves the database backed results through the API
6. A reviewer changes a record to pending, in review, or resolved
7. FastAPI saves the reviewer status and notes without changing the original
   pipeline classification

## Deployment configuration

The repository includes `render.yaml` for deploying the FastAPI service from
GitHub. The deployed service requires a PostgreSQL connection string named
`DATABASE_URL`.

After the API is deployed, add its public address to Streamlit Community Cloud
under App settings and Secrets.

```toml
API_BASE_URL = "https://your-api-name.onrender.com"
```

Do not add a trailing slash and do not commit database credentials or Streamlit
Secrets to GitHub.

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
