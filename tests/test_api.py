from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_summary_returns_verified_counts():
    response = client.get("/summary")
    assert response.status_code == 200
    counts = {
        row["review_status"]: int(row["comparison_count"])
        for row in response.json()
    }
    assert sorted(counts.values()) == [2, 3, 9]


def test_reviews_can_be_filtered_by_patient():
    response = client.get("/reviews", params={"patient_id": "3"})
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert {row["patient_id"] for row in rows} == {"3"}
