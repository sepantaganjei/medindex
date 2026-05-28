FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install "numpy==1.26.4" && \
    pip install . --no-build-isolation

EXPOSE 8000

CMD ["python", "-m", "app.main"]
