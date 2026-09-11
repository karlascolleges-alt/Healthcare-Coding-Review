"""Interactive review dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(page_title="Healthcare Coding Review", layout="wide")
st.title("Healthcare Coding Review")
st.caption(
    "Explainable comparison of submitted and documented diagnosis groups "
    "using synthetic data"
)

results = pd.read_csv(DATA / "coding_review_results.csv")
unmapped = pd.read_csv(DATA / "unmapped_codes.csv")

captured = int((results["review_status"] == "Captured").sum())
review_required = int((results["review_status"] != "Captured").sum())

first, second, third, fourth = st.columns(4)
first.metric("Comparisons", len(results))
second.metric("Captured", captured)
third.metric("Review required", review_required)
fourth.metric("Unmapped occurrences", int(unmapped["occurrence_count"].sum()))

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

st.info(
    "This educational application identifies records for human review. "
    "It does not determine coding accuracy or modify claims."
)
