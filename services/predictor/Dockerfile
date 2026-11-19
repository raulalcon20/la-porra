# ---------- Etapa 1: builder (construye el .venv) ----------
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencias: cambian poco → primero, para aprovechar la caché
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Código: cambia a menudo → después
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# ---------- Etapa 2: runtime (la imagen final) ----------
FROM python:3.13-slim

RUN useradd --system --uid 1000 --no-create-home app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER app

ENTRYPOINT ["python", "-m", "porra_predictor"]