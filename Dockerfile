FROM python:3.12.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

# Change the working directory to the `app` directory
WORKDIR /app

ADD uv.lock .
ADD pyproject.toml .
#ADD main.py .
#ADD crawler crawler
RUN touch README.md

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the project into the image
ADD crawler crawler

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM unclecode/crawl4ai:0.7.2

COPY --from=builder --chown=app:app /app/.venv /app/.venv
#ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
ADD config config
ADD main.py .

CMD ["/app/.venv/bin/python", "main.py"]
