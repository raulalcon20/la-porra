# etapa builder

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# dependencias primero porque cambian poco, así que se cachean mejor
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# codigo que cambia mas seguido, asi que se cachea menos
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# etapa runtime

FROM python:3.13-slim 

RUN useradd --system --uid 1000 --no-create-home app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000

CMD ["uvicorn", "porra_api.main:app", "--host", "0.0.0.0", "--port", "8000"]