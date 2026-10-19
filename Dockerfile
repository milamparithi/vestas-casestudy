FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Report PDFs are mounted at runtime, never baked into the image.
# Mount the runs dir too to persist per-run predictions + reports:
#   docker run --rm --env-file .env \
#     -v "$PWD:/data" -v "$PWD/eval/runs:/app/eval/runs" \
#     risk-pipeline /data/report.pdf [--eval]
ENTRYPOINT ["risk-pipeline"]
