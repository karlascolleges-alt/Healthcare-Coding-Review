"""Client used by Streamlit to communicate with the workflow API."""

from __future__ import annotations

from datetime import date

import httpx


class WorkflowAPIError(RuntimeError):
    """Raised when the workflow API cannot complete a request."""


class WorkflowAPIClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            try:
                detail = exc.response.json().get("error", {})
                message = detail.get("message", exc.response.text)
            except ValueError:
                message = exc.response.text
            raise WorkflowAPIError(
                f"The workflow service returned {exc.response.status_code}. {message}"
            ) from exc
        except httpx.RequestError as exc:
            raise WorkflowAPIError(
                "The workflow service is unavailable. A free service may need "
                "about one minute to wake up."
            ) from exc

    def health(self) -> dict:
        return self._request("GET", "/health")

    def start_run(
        self, review_start_date: date, review_end_date: date, mapping_version: str
    ) -> dict:
        return self._request(
            "POST",
            "/runs",
            json={
                "review_start_date": review_start_date.isoformat(),
                "review_end_date": review_end_date.isoformat(),
                "mapping_version": mapping_version,
            },
        )

    def get_run(self, run_id: int) -> dict:
        return self._request("GET", f"/runs/{run_id}")

    def get_reviews(
        self,
        run_id: int,
        review_status: str | None = None,
        workflow_status: str | None = None,
        patient_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        params = {
            "run_id": run_id,
            "limit": limit,
            "offset": offset,
        }
        if review_status:
            params["review_status"] = review_status
        if workflow_status:
            params["workflow_status"] = workflow_status
        if patient_id:
            params["patient_id"] = patient_id
        return self._request("GET", "/reviews", params=params)

    def update_review(
        self, review_id: int, workflow_status: str, reviewer_notes: str | None
    ) -> dict:
        return self._request(
            "PATCH",
            f"/reviews/{review_id}",
            json={
                "workflow_status": workflow_status,
                "reviewer_notes": reviewer_notes or None,
            },
        )
