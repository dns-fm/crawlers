ARG LAMBDA_ROOT="/function"

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ARG LAMBDA_ROOT

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

WORKDIR ${LAMBDA_ROOT}

ADD uv.lock .
ADD pyproject.toml .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

FROM python:3.11.11-slim-bookworm

ARG LAMBDA_ROOT

COPY --from=builder --chown=crawler:crawler ${LAMBDA_ROOT} ${LAMBDA_ROOT}
ENV PATH="${LAMBDA_ROOT}/.venv/bin:$PATH"
RUN playwright install --with-deps chromium

WORKDIR ${LAMBDA_ROOT}
ADD app.py ${LAMBDA_ROOT}
ADD config ${LAMBDA_ROOT}

# Download and add the Runtime Interface Emulator
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/local/bin/aws-lambda-rie
RUN chmod +x /usr/local/bin/aws-lambda-rie

# Define the entrypoint script
COPY entry_script.sh /
RUN chmod +x /entry_script.sh

ENV CRAWL4_AI_BASE_DIRECTORY="/tmp"
# ENV PLAYWRIGHT_BROWSERS_PATH="/ms-playwright"

ENTRYPOINT [ "/entry_script.sh" ]
CMD ["app.handler"]


