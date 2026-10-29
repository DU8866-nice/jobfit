"""HTTP API tests. They need FastAPI installed (they run in CI)."""

import io

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from jobfit.config import Settings  # noqa: E402
from jobfit.llm.mock_client import MockClient  # noqa: E402
from jobfit.main import create_app  # noqa: E402


def make_client(**overrides) -> TestClient:
    settings = Settings(provider="mock", **overrides)
    return TestClient(create_app(settings, MockClient()))


def error_code(response) -> str:
    return response.json()["detail"]["code"]


def test_health():
    response = make_client().get("/api/health")
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_analyze_with_pasted_resume(job_ad, resume):
    response = make_client().post("/api/analyze", data={"job_description": job_ad, "resume_text": resume})
    assert response.status_code == 200
    body = response.json()
    assert body["job_title"] == "Junior Data Analyst"
    assert body["language"] == "en"
    assert 0 <= body["score"]["overall"] <= 100


def test_analyze_with_uploaded_file_in_chinese(job_ad, resume):
    response = make_client().post(
        "/api/analyze",
        data={"job_description": job_ad, "language": "zh"},
        files={"resume_file": ("cv.txt", io.BytesIO(resume.encode()), "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["language"] == "zh"


def test_missing_resume(job_ad):
    response = make_client().post("/api/analyze", data={"job_description": job_ad})
    assert response.status_code == 400
    assert error_code(response) == "no_resume"


def test_short_job_description(resume):
    response = make_client().post("/api/analyze", data={"job_description": "Data analyst", "resume_text": resume})
    assert response.status_code == 400
    assert error_code(response) == "job_too_short"


def test_unsupported_language(job_ad, resume):
    response = make_client().post(
        "/api/analyze", data={"job_description": job_ad, "resume_text": resume, "language": "fr"}
    )
    assert response.status_code == 400
    assert error_code(response) == "bad_language"


def test_unsupported_file(job_ad):
    response = make_client().post(
        "/api/analyze",
        data={"job_description": job_ad},
        files={"resume_file": ("cv.pages", io.BytesIO(b"x" * 200), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert error_code(response) == "unsupported_file_type"


def test_file_too_large(job_ad):
    response = make_client(max_upload_bytes=100).post(
        "/api/analyze",
        data={"job_description": job_ad},
        files={"resume_file": ("cv.txt", io.BytesIO(b"x" * 500), "text/plain")},
    )
    assert response.status_code == 413
    assert error_code(response) == "file_too_large"


def test_per_visitor_rate_limit(job_ad, resume):
    client = make_client(rate_limit_per_hour=2)
    data = {"job_description": job_ad, "resume_text": resume}
    assert client.post("/api/analyze", data=data).status_code == 200
    assert client.post("/api/analyze", data=data).status_code == 200
    response = client.post("/api/analyze", data=data)
    assert response.status_code == 429
    assert error_code(response) == "rate_limited"


def test_site_wide_daily_limit(job_ad, resume):
    client = make_client(rate_limit_per_hour=0, daily_analysis_limit=1)
    data = {"job_description": job_ad, "resume_text": resume}
    assert client.post("/api/analyze", data=data).status_code == 200
    response = client.post("/api/analyze", data=data)
    assert response.status_code == 503
    assert error_code(response) == "daily_limit"


def test_serves_the_frontend_when_built(tmp_path):
    (tmp_path / "index.html").write_text("<h1>JobFit</h1>")
    client = make_client(static_dir=tmp_path)
    assert "JobFit" in client.get("/").text
    assert client.get("/api/health").status_code == 200
