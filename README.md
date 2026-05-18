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
docker compose up --build
```

The API will be available at `http://localhost:8000` (`/hello` endpoint).
