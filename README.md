# DevPulse — Developer Productivity Platform

A focused engineering workspace that helps developers stay on task, track work, and get AI assistance — all in one place.

## What it does

- **Dashboard** — Personal task board + system health at a glance
- **Focus Sessions** — AI-powered workspaces scoped to a single task or problem (debugging, architecture, code review…)
- **AI Assistant** — Floating chat widget available across every page
- **Health API** — Real-time service status endpoint

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 / Python 3.9 |
| Database | PostgreSQL 16 |
| Cache | Redis |
| AI backend | Ollama (local) or OpenAI |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Containers | Docker Compose |

## Quick start (local dev)

```bash
# 1. Start services
docker compose up -d postgres redis

# 2. Install Python deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Create a superuser
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
```

Open http://localhost:8000 — register or log in to access the workspace.

## Docker (full stack)

```bash
docker compose up --build
```

App available at http://localhost:8080 when running in Docker.

## Key URLs

| Path | Description |
|---|---|
| `/` | Dashboard (requires login) |
| `/sessions/` | All focus sessions |
| `/sessions/new/` | Start a new session |
| `/api/health` | JSON health check |
| `/admin/` | Django admin panel |

## Design

Dark sidebar navigation (`#0f172a`) with a clean light content area (`#f1f5f9`). Emerald green (`#059669`) accent color throughout. No external UI frameworks beyond Bootstrap.
