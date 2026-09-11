"""Interactive dashboard connected to the coding review workflow API."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app.api_client import WorkflowAPIClient, WorkflowAPIError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"


def configured_api_url() -> str:
    value = os.getenv("API_BASE_URL", "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get("API_BASE_URL", "")).strip()
    except FileNotFoundError:
        return ""


def render_metrics(results: pd.DataFrame, unmapped_occurrences: int) -> None:
    captured = int((results["review_status"] == "Captured").sum())
    review_required = int((results["review_status"] != "Captured").sum())
    resolved = (
        int((results["workflow_status"] == "resolved").sum())
        if "workflow_status" in results
        else 0
    )
    first, second, third, fourth = st.columns(4)
    first.metric("Comparisons", len(results))
    second.metric("Captured", captured)
    third.metric("Review required", review_required)
    fourth.metric(
        "Resolved" if "workflow_status" in results else "Unmapped occurrences",
        resolved if "workflow_status" in results else unmapped_occurrences,
    )


def render_chart(results: pd.DataFrame) -> None:
    st.subheader("Review status")
    counts = (
        results["review_status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
    )
    figure = px.bar(counts, x="count", y="status", orientation="h", color="status")
    figure.update_layout(showlegend=False, yaxis_title=None, xaxis_title="Comparisons")
    st.plotly_chart(figure, use_container_width=True)


def render_demo_mode() -> None:
    st.warning(
        "The dashboard is using stored demonstration results because the workflow "
        "API has not been configured yet."
    )
    results = pd.read_csv(DATA / "coding_review_results.csv")
    unmapped = pd.read_csv(DATA / "unmapped_codes.csv")
    render_metrics(results, int(unmapped["occurrence_count"].sum()))
    render_chart(results)
    st.subheader("Patient condition comparison")
    status_options = ["All", *sorted(results["review_status"].unique())]
    selected_status = st.selectbox("Review status", status_options)
    search = st.text_input("Search by patient or condition group")
    filtered = results.copy()
    if selected_status != "All":
        filtered = filtered[filtered["review_status"] == selected_status]
    if search:
        matched = filtered["patient_name"].str.contains(
            search, case=False, na=False
        ) | filtered["demo_condition_group"].str.contains(search, case=False, na=False)
        filtered = filtered[matched]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download current view",
        filtered.to_csv(index=False),
        "coding_review_queue.csv",
        "text/csv",
    )
    with st.expander("Unmapped diagnosis codes"):
        st.dataframe(unmapped, use_container_width=True, hide_index=True)


def render_connected_mode(client: WorkflowAPIClient) -> None:
    try:
        health = client.health()
    except WorkflowAPIError as exc:
        st.error(str(exc))
        st.info("Check the API_BASE_URL value in Streamlit Secrets and try again.")
        return

    st.success(f"Workflow service connected and database {health['database']}")
    with st.sidebar:
        st.header("New reconciliation run")
        start_date = st.date_input("Review start date", date(2026, 1, 1))
        end_date = st.date_input("Review end date", date(2026, 6, 30))
        mapping_version = st.text_input("Mapping version", "DEMO_V1")
        if st.button("Start reconciliation run", type="primary"):
            try:
                run = client.start_run(start_date, end_date, mapping_version)
                st.session_state["run_id"] = run["id"]
                st.rerun()
            except WorkflowAPIError as exc:
                st.error(str(exc))

        run_id_value = st.number_input(
            "Run ID",
            min_value=1,
            value=int(st.session_state.get("run_id", 1)),
        )
        st.session_state["run_id"] = int(run_id_value)
        if st.button("Refresh run"):
            st.rerun()

    run_id = st.session_state.get("run_id")
    if not run_id:
        st.info("Start a reconciliation run to create the database backed queue.")
        return

    try:
        run = client.get_run(int(run_id))
    except WorkflowAPIError as exc:
        st.info(f"Run {run_id} is not available yet. {exc}")
        return

    status = run["status"]
    st.subheader(f"Run {run['id']}")
    st.write(
        f"Status **{status}**  |  Mapping **{run['mapping_version']}**  |  "
        f"Review period **{run['review_start_date']} to {run['review_end_date']}**"
    )
    if status in {"queued", "running"}:
        st.info("The reconciliation pipeline is still running. Select Refresh run.")
        return
    if status == "failed":
        st.error(run.get("error_message") or "The pipeline run failed.")
        return

    filter_one, filter_two, filter_three = st.columns(3)
    review_status = filter_one.selectbox(
        "Pipeline result",
        [
            "All",
            "Captured",
            "Potential Gap Review Required",
            "Submitted Code Documentation Review Required",
        ],
    )
    workflow_status = filter_two.selectbox(
        "Workflow status", ["All", "pending", "in_review", "resolved"]
    )
    patient_id = filter_three.text_input("Patient ID")
    page_size = st.selectbox("Results per page", [5, 10, 25, 50], index=1)
    page = st.number_input("Page", min_value=1, value=1)

    try:
        response = client.get_reviews(
            int(run_id),
            None if review_status == "All" else review_status,
            None if workflow_status == "All" else workflow_status,
            patient_id or None,
            page_size,
            (int(page) - 1) * page_size,
        )
    except WorkflowAPIError as exc:
        st.error(str(exc))
        return

    results = pd.DataFrame(response["items"])
    if results.empty:
        st.warning("No review records match the selected filters.")
        return
    render_metrics(results, int(run.get("unmapped_code_count") or 0))
    render_chart(results)
    st.caption(f"Showing {len(results)} of {response['total']} matching records")
    st.dataframe(results, use_container_width=True, hide_index=True)
    st.download_button(
        "Download current view",
        results.to_csv(index=False),
        f"coding_review_run_{run_id}.csv",
        "text/csv",
    )

    st.subheader("Update a review")
    selected_id = st.selectbox("Review record", results["id"].tolist())
    selected = results.loc[results["id"] == selected_id].iloc[0]
    states = ["pending", "in_review", "resolved"]
    selected_state = st.selectbox(
        "Reviewer status", states, index=states.index(selected["workflow_status"])
    )
    notes = st.text_area(
        "Reviewer notes", value=selected.get("reviewer_notes") or "", max_chars=2000
    )
    if st.button("Save review update"):
        try:
            client.update_review(int(selected_id), selected_state, notes)
            st.success("The reviewer status and notes were saved.")
            st.rerun()
        except WorkflowAPIError as exc:
            st.error(str(exc))


st.set_page_config(page_title="Healthcare Coding Review", layout="wide")
st.title("Healthcare Coding Review")
st.caption(
    "Explainable comparison of submitted and documented diagnosis groups using "
    "synthetic data"
)

api_url = configured_api_url()
if api_url:
    render_connected_mode(WorkflowAPIClient(api_url))
else:
    render_demo_mode()

st.info(
    "This educational application identifies records for human review. "
    "It does not determine coding accuracy or modify claims."
)
