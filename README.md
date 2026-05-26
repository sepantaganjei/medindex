# 2026-bioimages

Team 2, Year 2026

## Start

1. Create your env file:

```bash
cp .env.example .env
```

### Local start

Install dependencies (equivalent to `requirements.txt` install):

```bash
pip install .
```

Run the API:

```bash
python -m app.main
```

### Docker start

```bash
docker build -t bioimages-app .
docker compose up
```

The API will be available at `http://localhost:8000` (endpoints under `/api`, object storage under `/api/object-storage`).
The frontend mock UI will be available at `http://localhost:8080`.
MinIO will be available at `http://localhost:9000` (API) and `http://localhost:9001` (console).
