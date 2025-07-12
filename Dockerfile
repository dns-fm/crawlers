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

FROM python:3.11-bookworm

ARG LAMBDA_ROOT
COPY --from=builder  ${LAMBDA_ROOT} ${LAMBDA_ROOT}
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers

ENV PATH="${LAMBDA_ROOT}/.venv/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH="/ms-playwright-browsers"
RUN playwright install chromium

WORKDIR ${LAMBDA_ROOT}
ADD app.py ${LAMBDA_ROOT}
ADD config ${LAMBDA_ROOT}

# Download and add the Runtime Interface Emulator
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/local/bin/aws-lambda-rie
RUN chmod +x /usr/local/bin/aws-lambda-rie

RUN mkdir /root/crawl4ai

# Define the entrypoint script
COPY entry_script.sh /
RUN chmod +x /entry_script.sh

ENV CRAWL4_AI_BASE_DIRECTORY="/tmp"

ENTRYPOINT ["/entry_script.sh" ]
CMD ["app.handler"]


