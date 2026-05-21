FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "numpy==1.26.4" && \
    pip install --no-cache-dir . --no-build-isolation

EXPOSE 8000

CMD ["python", "-m", "app.main"]
