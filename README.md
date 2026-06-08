# postgres-rag

Local stack for RAG workflows using PostgreSQL + pgvector, n8n, and pgAdmin.

## Services

| Service  | URL                        | Credentials                          |
|----------|----------------------------|--------------------------------------|
| n8n      | http://localhost:5678      | Set on first run                     |
| pgAdmin  | http://localhost:5050      | `admin@admin.com` / `admin`          |
| Postgres | `localhost:5432` (internal)| user: `n8n` / password: `n8n_pass`   |

## Databases

| Database | Purpose                                      |
|----------|----------------------------------------------|
| `n8n`    | n8n internal storage (workflows, credentials)|
| `rag`    | RAG workload — pgvector extension + `documents` table |

### `rag` schema

```sql
documents (
  id        SERIAL PRIMARY KEY,
  content   TEXT,
  metadata  JSONB,
  embedding VECTOR(1536)   -- IVFFlat cosine index
)
```

## Getting started

```bash
# First time — pull images and start all services
docker compose up -d

# Verify all containers are running
docker compose ps

# Stop and remove containers (keeps data volumes)
docker compose down

# Stop and remove containers + all data volumes (full reset)
docker compose down -v
```

### Access pgAdmin

1. Open http://localhost:5050 in your browser.
2. Log in with `admin@admin.com` / `admin`.
3. Go to **Object → Register → Server** and fill in:
   - **General → Name**: anything (e.g. `local`)
   - **Connection → Host**: `postgres`
   - **Connection → Port**: `5432`
   - **Connection → Database**: `n8n`
   - **Connection → Username**: `n8n`
   - **Connection → Password**: `n8n_pass`
4. Click **Save** — you should see the `n8n` database in the left panel.

## Local documents

Place any files you want n8n to process inside the `documents/` folder at the root of this repo. They are mounted into the n8n container at `/home/node/.n8n-files` (the only path n8n allows for file access).

Use that path in n8n nodes that read files (e.g. **Read/Write Files from Disk**):

```
/home/node/.n8n-files/*
```

## Stack

- **pgvector/pgvector:pg16** — Postgres 16 with the `vector` extension for similarity search
- **n8nio/n8n** — workflow automation connected to Postgres
- **dpage/pgadmin4** — database GUI
