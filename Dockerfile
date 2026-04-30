FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src

RUN pip install -r requirements.txt && pip install -e .

RUN mkdir -p /app/output && chown -R app:app /app

USER app

CMD ["python", "-m", "gitsummarizer"]
