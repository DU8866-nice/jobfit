# One image: the React app is built first, then served by the FastAPI backend.

# ---- build the frontend
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- run the API and serve the built frontend
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JOBFIT_STATIC_DIR=/app/static
WORKDIR /app

COPY backend/pyproject.toml ./
COPY backend/jobfit ./jobfit
RUN pip install --no-cache-dir .
COPY --from=web /web/dist ./static

RUN useradd --create-home --uid 10001 jobfit
USER jobfit

EXPOSE 8000
# --proxy-headers lets the per-visitor rate limit see the real client IP behind a hosting
# platform's load balancer. Only run it behind a proxy that sets X-Forwarded-For itself.
CMD ["sh", "-c", "exec uvicorn jobfit.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
