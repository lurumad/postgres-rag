# postgres-rag

Local stack for RAG workflows using PostgreSQL + pgvector, n8n, pgAdmin, Ollama, and MarkItDown.

## Services

| Service  | URL                        | Credentials                          |
|----------|----------------------------|--------------------------------------|
| n8n      | http://localhost:5678      | Set on first run                     |
| pgAdmin  | http://localhost:5050      | `admin@admin.com` / `admin`          |
| Postgres | `localhost:5432` (internal)| user: `n8n` / password: `n8n_pass`   |
| Ollama   | http://localhost:11434     | No auth                              |
| MarkItDown | http://localhost:8080    | No auth                              |

## Databases

| Database | Purpose                                      |
|----------|----------------------------------------------|
| `n8n`    | n8n internal storage (workflows, credentials)|
| `rag`    | RAG workload — pgvector extension + `documents` table |

### `rag` schema

```sql
documents (
  id        SERIAL PRIMARY KEY,
  text      TEXT,
  metadata  JSONB,
  embedding VECTOR(384)    -- IVFFlat cosine index (all-minilm dimensions)
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

## Ollama (local models)

Ollama runs locally and serves two models — no external API calls required:

| Model | Purpose | Dimensions |
|-------|---------|------------|
| `all-minilm` | Embeddings | 384 |
| `llama3.2:1b` | Chat / AI Agent | — |

`all-minilm` is pulled automatically on first start. Pull `llama3.2:1b` once after starting the stack:

```bash
docker compose exec ollama ollama pull llama3.2:1b

# Verify available models
curl http://localhost:11434/api/tags
```

To use a GPU (NVIDIA), uncomment the `deploy` block in `docker-compose.yml` under the `ollama` service.

## n8n Workflow

The file `embeddings-workflow.json` contains a single combined workflow with two pipelines:

### Ingestion pipeline (scheduled)

1. **Schedule Trigger** — runs on a schedule
2. **Has Files** — skips run if `documents/` is empty
3. **Read documents** — reads files from `/home/node/.n8n-files`
4. **MarkItDown** — converts each document to Markdown via the MarkItDown service
5. **Recursive Character Text Splitter** — splits content into chunks
6. **Embeddings Ollama** — generates 384-dimension embeddings using `all-minilm`
7. **Postgres PGVector Store** — stores chunks + embeddings in the `documents` table
8. **Clean Files** — deletes processed files via the MarkItDown `/delete` endpoint

### Chat pipeline (on demand)

1. **When chat message received** — entry point for chat input
2. **AI Agent** — orchestrates the response using the chat model and a PGVector retrieval tool
3. **Ollama Chat Model** — `llama3.2:1b` served locally via Ollama
4. **Postgres PGVector Retrieval** — fetches relevant document chunks for RAG context

### Import the workflow

1. Open n8n at http://localhost:5678
2. Go to **Workflows → Import from file**
3. Select `embeddings-workflow.json`

## MarkItDown (document conversion)

MarkItDown converts documents (PDF, DOCX, XLSX, images, etc.) to Markdown via a simple HTTP API. Files in `documents/` are mounted at `/documents` inside the container.

```bash
# Convert a file by path (must be inside /documents)
curl -X POST http://localhost:8080/convert \
  -H "Content-Type: application/json" \
  -d '{"path":"/documents/example.txt"}'

# Convert by uploading a file directly
curl -X POST http://localhost:8080/convert \
  -F "file=@/path/to/local/file.pdf"

# Health check
curl http://localhost:8080/health

# Delete a file
curl -X POST http://localhost:8080/delete \
  -H "Content-Type: application/json" \
  -d '{"path":"/documents/example.txt"}'
```

## Stack

- **pgvector/pgvector:pg16** — Postgres 16 with the `vector` extension for similarity search
- **n8nio/n8n** — workflow automation connected to Postgres
- **dpage/pgadmin4** — database GUI
- **ollama/ollama** — local LLM server running `all-minilm` (embeddings) and `llama3.2:1b` (chat)
- **python:3.12-slim + markitdown** — document-to-Markdown conversion service
