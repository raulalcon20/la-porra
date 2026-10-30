FROM python:3.13-slim

WORKDIR /app

RUN pip install uv==0.13.6

# dependencias primero porque cambian poco, así que se cachean mejor
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# codigo que cambia mas seguido, asi que se cachea menos
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "porra_api.main:app", "--host", "0.0.0.0", "--port", "8000"]