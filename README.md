# Acumen Backend Developer Assessment

This project builds a small data pipeline using three Dockerized services:

- **Flask Mock Server**: serves paginated customer data from a JSON file.
- **FastAPI Pipeline Service**: ingests all customer data from Flask into PostgreSQL using `dlt`, and exposes query APIs.
- **PostgreSQL**: stores customer records.

## Architecture

Flask (`/api/customers`) → FastAPI (`POST /api/ingest`) → PostgreSQL → FastAPI query endpoints

## Prerequisites

- Docker Desktop running
- Python 3.10+
- Git
- `docker compose version`

## Start Services

```bash
docker compose up --build -d
```

## Test Endpoints

### Flask mock server
```bash
curl "http://localhost:5000/api/customers?page=1&limit=5"
curl "http://localhost:5000/api/customers/CUST-1001"
curl "http://localhost:5000/api/health"
```

### FastAPI pipeline service
```bash
curl -X POST http://localhost:8000/api/ingest
curl "http://localhost:8000/api/customers?page=1&limit=5"
curl "http://localhost:8000/api/customers/CUST-1001"
curl "http://localhost:8000/api/health"
```

## Notes

- Flask loads data from `mock-server/data/customers.json`.
- FastAPI fetches all pages automatically from the Flask service.
- Ingestion is implemented with `dlt` configured for a PostgreSQL destination.
- Upsert behavior is enforced using PostgreSQL `ON CONFLICT (customer_id)`.
