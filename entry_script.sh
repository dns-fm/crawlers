#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec /usr/local/bin/aws-lambda-rie /function/.venv/bin/python -m awslambdaric "$@"
else
    exec /function/.venv/bin/python -m awslambdaric "$@"
fi
