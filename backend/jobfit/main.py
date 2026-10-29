"""HTTP API.

Run locally with:
    uvicorn jobfit.main:create_app --factory --reload

Errors come back as {"detail": {"code": "...", "message": "..."}} so the frontend
can show them in the user's language.
"""

from __future__ import annotations

import logging
from typing import get_args

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings
from .errors import AppError
from .llm import LLMClient, LLMError, get_client
from .parsing import FileTooLargeError, ResumeParseError, extract_text
from .pipeline import AnalysisError, InputError, analyze
from .ratelimit import RateLimiter
from .schemas import AnalysisResult, Language

log = logging.getLogger(__name__)

LANGUAGES = set(get_args(Language))


def _http_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _from_app_error(status: int, exc: AppError) -> HTTPException:
    return _http_error(status, exc.code, exc.message)


def _visitor_ip(request: Request, header: str | None) -> str:
    if header:
        value = request.headers.get(header, "").strip()
        if value:
            return value
    return request.client.host if request.client else "unknown"


def create_app(settings: Settings | None = None, client: LLMClient | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    client = client or get_client(settings)
    per_visitor = RateLimiter(settings.rate_limit_per_hour, window_seconds=3600)
    site_wide = RateLimiter(settings.daily_analysis_limit, window_seconds=24 * 3600)

    app = FastAPI(title="JobFit API", version=__version__)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "provider": client.name, "version": __version__}

    # A plain `def` endpoint runs in FastAPI's thread pool, so the blocking model
    # calls don't stall other requests.
    @app.post("/api/analyze", response_model=AnalysisResult)
    def analyze_endpoint(
        request: Request,
        job_description: str = Form(...),
        resume_text: str | None = Form(None),
        resume_file: UploadFile | None = File(None),
        language: str = Form("en"),
    ) -> AnalysisResult:
        if language not in LANGUAGES:
            raise _http_error(400, "bad_language", f"language must be one of {sorted(LANGUAGES)}.")

        visitor = _visitor_ip(request, settings.client_ip_header)
        if not per_visitor.allow(visitor):
            raise _http_error(429, "rate_limited", "Too many analyses from this address. Please try again in an hour.")
        if not site_wide.allow("site"):
            raise _http_error(503, "daily_limit", "Today's free analyses have run out. Please come back tomorrow.")

        if resume_file is not None and resume_file.filename:
            # Read one byte past the limit so an oversized file is detected without reading all of it.
            data = resume_file.file.read(settings.max_upload_bytes + 1)
            try:
                text = extract_text(resume_file.filename, data, max_bytes=settings.max_upload_bytes)
            except FileTooLargeError as exc:
                raise _from_app_error(413, exc) from exc
            except ResumeParseError as exc:
                raise _from_app_error(400, exc) from exc
        elif resume_text and resume_text.strip():
            text = resume_text
        else:
            raise _http_error(400, "no_resume", "Add your resume, either as a file or as pasted text.")

        try:
            return analyze(job_description, text, client, language=language, max_chars=settings.max_text_chars)
        except InputError as exc:
            raise _from_app_error(400, exc) from exc
        except (LLMError, AnalysisError) as exc:
            raise _from_app_error(502, exc) from exc

    # In production the built React app is served from the same origin.
    if settings.static_dir and settings.static_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="static")

    log.info("JobFit started with provider=%s", client.name)
    return app
