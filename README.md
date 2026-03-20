# Boooking-service

## Docker

Minimum setup uses 2 containers:
- `api` (FastAPI)
- `db` (PostgreSQL)

Start:

```bash
docker compose up --build
```

If only application code changed and image rebuild is not needed:

```bash
docker compose up
```

`docker-compose.yml` now already includes bind mount for `./app` and runs `uvicorn` with `--reload`.

Check:
- API: `http://localhost:8000/api`
- Frontend: `http://localhost:8000/`

Stop:

```bash
docker compose down
```

Stop and remove DB volume:

```bash
docker compose down -v
```
