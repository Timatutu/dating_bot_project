FROM python:3.12-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000 50051

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000"]
