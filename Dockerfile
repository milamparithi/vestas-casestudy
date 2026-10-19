FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Report PDFs are mounted at runtime, never baked into the image.
# Mount the output and eval dirs to persist per-run pipeline output and eval
# artifacts:
#   docker run --rm --env-file .env \
#     -v "$PWD:/data" -v "$PWD/output/runs:/app/output/runs" -v "$PWD/eval:/app/eval" \
#     risk-pipeline /data/report.pdf [--eval]
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin app \
    && mkdir -p /app/output/runs /app/eval \
    && chown -R app:app /app/output /app/eval
USER app

ENTRYPOINT ["risk-pipeline"]
