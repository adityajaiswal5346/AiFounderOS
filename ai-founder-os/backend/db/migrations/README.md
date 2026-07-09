# Alembic Migrations

Database migrations are managed with Alembic.

## Setup

```bash
cd backend
alembic init db/migrations
# Edit alembic.ini to set sqlalchemy.url = postgresql+asyncpg://...
```

## Create a migration

```bash
alembic revision --autogenerate -m "initial schema"
```

## Run migrations

```bash
alembic upgrade head
```

## Initial migration notes

The initial schema creates:
- `tasks` table
- `approvals` table
- `memory_long` table (with pgvector `embedding` column)
- `outcomes` table
- `task_runs` table

The pgvector extension must be enabled before running migrations:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This is handled automatically by the pgvector/pgvector Docker image in docker-compose.yml.
