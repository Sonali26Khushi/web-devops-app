# web-devops-app

Django web application that combines:

- Authenticated task board (session-backed tasks)
- AI chat (conversation history + demo/widget endpoints)
- Smart search over stored records with optional LLM summaries

The project is built with Django templates, PostgreSQL by default, optional Redis cache, and optional Ollama/OpenAI LLM integration.

## Features

- User registration, login, and logout
- Personal task board at `/` (add, toggle, remove, clear completed)
- AI conversation management (`/chat/`, `/chat/new/`, `/chat/<id>/`)
- Smart search app (`/search/`) with category filters and seeded demo records
- Health endpoint at `/api/health` (database/cache/Ollama status)
- API endpoints for agent testing and floating widget chat

## Tech Stack

- Python 3.9+
- Django 4.2
- PostgreSQL (default), configurable via `DATABASE_URL`
- Redis (optional hit counter/cache dependency)
- Ollama (default LLM provider) or OpenAI (if `OPENAI_API_KEY` is set)

## Project Structure

```text
web-devops-app/
|-- app/
|   |-- models.py        # AppEvent, Conversation, Message, SearchRecord
|   |-- views.py         # Task board, auth, chat, smart search, APIs
|   |-- llm_service.py   # Ollama/OpenAI provider integration
|   |-- forms.py         # Auth and chat forms
|   |-- templates/       # HTML templates
|   `-- static/          # CSS assets
|-- config/
|   |-- settings.py      # Env-driven Django settings
|   `-- urls.py          # Root URL configuration
|-- manage.py
|-- requirements.txt
|-- SETUP.md
`-- README.md
```

## Quick Start

1. Move into the app directory.

```bash
cd web-devops-app
```

2. Create and activate a virtual environment.

```bash
python3 -m venv ../.venv
source ../.venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Configure environment variables.

```bash
cp .env.example .env
```

5. Apply migrations.

```bash
python manage.py migrate
```

6. Create an admin user.

```bash
python manage.py createsuperuser
```

7. Run the server.

```bash
python manage.py runserver
```

8. Open the app.

- Home: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/api/health

## Environment Variables

Create `.env` in the project root with values like:

```env
DJANGO_SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL (default)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/webdevops
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=webdevops
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Optional Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# If set, OpenAI is used instead of Ollama
OPENAI_API_KEY=
```

Notes:

- If `OPENAI_API_KEY` is empty, the app uses Ollama.
- The app can run without Redis; it falls back to local in-memory hit counting.

## Docker (App Container)

Build the image:

```bash
docker build -t web-devops-app .
```

Run the container:

```bash
docker run --rm --env-file .env -p 8000:8080 web-devops-app
```

Open the app:

- Home: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/api/health

Stop the container:

```bash
Ctrl+C
```

## Main Routes

### Auth and Core

- `GET /` - Task board home (login required)
- `GET|POST /register/` - Register user
- `GET|POST /login/` - Login user
- `POST /logout/` - Logout user

### Chat

- `GET /chat/` - Conversation list
- `GET|POST /chat/demo/` - Demo chat page
- `GET|POST /chat/new/` - Create conversation
- `GET|POST /chat/<id>/` - View/send messages
- `POST /chat/<id>/delete/` - Soft-delete conversation

### Smart Search

- `GET /search/` - Search UI and LLM summarization
- `POST /search/add/` - Add search record
- `POST /search/delete/<record_id>/` - Delete search record

### APIs

- `GET /api/health` - App dependency health
- `POST /api/agent` - Direct prompt passthrough to Ollama model
- `POST /api/widget-chat/` - JSON endpoint for floating chat widget

## LLM Provider Setup

### Ollama (default)

```bash
ollama serve
ollama pull llama3.2:1b
```

Then ensure `.env` includes:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OPENAI_API_KEY=
```

### OpenAI

Set:

```env
OPENAI_API_KEY=your-key
```

When this value is present, OpenAI is selected by `LLMService`.

## Troubleshooting

- `Could not connect to Ollama`: start Ollama and confirm `OLLAMA_URL`.
- `No module named django`: activate venv and reinstall requirements.
- Migration errors: run `python manage.py migrate`.
- Redis connection warnings in health: Redis is optional for local development.

## Deployment Notes

- Set `DEBUG=False`.
- Use a strong `DJANGO_SECRET_KEY`.
- Configure production `ALLOWED_HOSTS`.
- Point `DATABASE_URL` to PostgreSQL (recommended in production).
- Run `python manage.py collectstatic` in your deployment pipeline.
