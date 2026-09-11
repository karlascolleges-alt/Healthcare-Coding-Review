from datetime import date

import httpx
import pytest

from app.api_client import WorkflowAPIClient, WorkflowAPIError


def response_for(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/health":
        return httpx.Response(
            200,
            json={"status": "healthy", "database": "connected"},
            request=request,
        )
    if request.url.path == "/runs" and request.method == "POST":
        return httpx.Response(202, json={"id": 7, "status": "queued"}, request=request)
    if request.url.path == "/reviews/99":
        return httpx.Response(
            404,
            json={"error": {"code": "review_not_found", "message": "Missing"}},
            request=request,
        )
    return httpx.Response(200, json={"items": [], "total": 0}, request=request)


def test_client_health_and_run_request(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "request",
        lambda method, url, **kwargs: response_for(httpx.Request(method, url)),
    )
    client = WorkflowAPIClient("https://api.example.test/")
    assert client.health()["database"] == "connected"
    run = client.start_run(date(2026, 1, 1), date(2026, 6, 30), "DEMO_V1")
    assert run == {"id": 7, "status": "queued"}


def test_client_returns_readable_api_error(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "request",
        lambda method, url, **kwargs: response_for(httpx.Request(method, url)),
    )
    client = WorkflowAPIClient("https://api.example.test")
    with pytest.raises(WorkflowAPIError, match="404. Missing"):
        client.update_review(99, "resolved", "Checked")


def test_client_returns_connection_guidance(monkeypatch):
    def unavailable(method, url, **kwargs):
        request = httpx.Request(method, url)
        raise httpx.ConnectError("offline", request=request)

    monkeypatch.setattr(httpx, "request", unavailable)
    with pytest.raises(WorkflowAPIError, match="unavailable"):
        WorkflowAPIClient("https://api.example.test").health()
