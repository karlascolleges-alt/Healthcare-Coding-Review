from pathlib import Path

from fastapi.testclient import TestClient

from app.api import create_app


def make_client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'workflow.db'}"
    root = Path(__file__).resolve().parents[1]
    return TestClient(create_app(database_url=database_url, root=root))


def start_run(client: TestClient) -> dict:
    response = client.post(
        "/runs",
        json={
            "review_start_date": "2026-01-01",
            "review_end_date": "2026-06-30",
            "mapping_version": "DEMO_V1",
        },
    )
    assert response.status_code == 202
    return response.json()


def test_health_check_verifies_database(tmp_path):
    response = make_client(tmp_path).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_run_executes_and_persists_audit_counts(tmp_path):
    client = make_client(tmp_path)
    created = start_run(client)
    response = client.get(f"/runs/{created['id']}")
    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "completed"
    assert run["comparison_count"] == 14
    assert run["review_queue_count"] == 5
    assert run["unmapped_code_count"] == 3


def test_reviews_are_database_backed_filtered_and_paginated(tmp_path):
    client = make_client(tmp_path)
    run = start_run(client)
    first_page = client.get("/reviews", params={"run_id": run["id"], "limit": 5})
    assert first_page.status_code == 200
    page = first_page.json()
    assert page["total"] == 14
    assert len(page["items"]) == 5
    assert page["limit"] == 5
    patient = client.get(
        "/reviews", params={"run_id": run["id"], "patient_id": "3"}
    ).json()
    assert patient["total"] == 2
    assert {row["patient_id"] for row in patient["items"]} == {"3"}


def test_reviewer_can_update_workflow_state_and_notes(tmp_path):
    client = make_client(tmp_path)
    run = start_run(client)
    review = client.get("/reviews", params={"run_id": run["id"], "limit": 1}).json()[
        "items"
    ][0]
    response = client.patch(
        f"/reviews/{review['id']}",
        json={
            "workflow_status": "resolved",
            "reviewer_notes": "Documentation verified during manual review.",
        },
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["workflow_status"] == "resolved"
    assert updated["reviewer_notes"] == "Documentation verified during manual review."


def test_structured_not_found_error(tmp_path):
    response = make_client(tmp_path).get("/runs/999")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "run_not_found", "message": "Pipeline run was not found"}
    }


def test_invalid_run_period_is_rejected(tmp_path):
    response = make_client(tmp_path).post(
        "/runs",
        json={
            "review_start_date": "2026-07-01",
            "review_end_date": "2026-06-30",
            "mapping_version": "DEMO_V1",
        },
    )
    assert response.status_code == 422
