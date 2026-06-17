FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

COPY . .

RUN mkdir -p data && uv sync --dev && uv pip install -e .

ENTRYPOINT ["uv", "run", "python", "main.py"]