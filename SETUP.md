# 🤖 Django AI Chat Application

A modern Django web application with integrated LLM (Large Language Model) support for intelligent conversations. Features user authentication, conversation history, and support for multiple LLM providers.

## 📋 Features

- **AI Chat Interface**: Interactive chat with AI using Ollama or OpenAI
- **Conversation History**: Save and organize conversations
- **User Authentication**: Secure login system with Django admin
- **Database Integration**: PostgreSQL by default
- **Multi-LLM Support**: 
  - Ollama (local, free, open-source)
  - OpenAI (cloud-based)
- **Public Demo**: Try the chat without authentication
- **Admin Dashboard**: Manage conversations and messages via Django admin
- **Token Tracking**: Monitor token usage for each message
- **Responsive Design**: Bootstrap 5 UI with mobile support

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to project directory
cd web-devops-app

# Activate virtual environment
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

### 3. Configuration

Edit `.env` file in the project root:

```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/webdevops
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=webdevops
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# For Ollama (local LLM)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# For OpenAI (optional)
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. Start the Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

### Run with Docker

```bash
docker build -t web-devops-app .
docker run --rm --env-file .env -p 8000:8080 web-devops-app
```

Stop the container:

```bash
Ctrl+C
```

## 📖 Usage

### Public Demo Chat
- **URL**: `/chat/demo/`
- Try the AI without logging in
- Responses are not saved
- Perfect for testing

### Authenticated Chat
1. **Login**: `/admin/login/` (use your superuser credentials)
2. **Create Conversation**: Click "New Conversation"
3. **Chat**: Type your message and send
4. **View History**: See all past conversations
5. **Manage**: Delete conversations anytime

### Admin Dashboard
- **URL**: `/admin/`
- View and manage conversations
- See message history with token counts
- Monitor app events

## 🔧 LLM Configuration

### Using Ollama (Free, Local)

```bash
# Install Ollama: https://ollama.ai

# Run Ollama in another terminal
ollama serve

# Download a model
ollama pull llama3.2:1b

# Update .env
OLLAMA_MODEL=llama3.2:1b
```

**Pros**: Free, runs locally, no API keys needed
**Cons**: Requires local installation, slower than cloud models

### Using OpenAI

```bash
# Get API key from: https://platform.openai.com/api-keys

# Update .env
OPENAI_API_KEY=sk-your-key-here
```

**Pros**: Fast, high quality responses
**Cons**: Requires API key, paid service

## 📁 Project Structure

```
web-devops-app/
├── app/
│   ├── models.py           # Database models (Conversation, Message)
│   ├── views.py            # Chat views and logic
│   ├── forms.py            # Form classes
│   ├── urls.py             # URL routing
│   ├── admin.py            # Admin configuration
│   ├── llm_service.py      # LLM integration service
│   ├── migrations/         # Database migrations
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       ├── chat_demo.html  # Demo chat
│       ├── chat_home.html  # Conversations list
│       ├── chat_conversation.html  # Main chat view
│       ├── create_conversation.html # Create new chat
│       └── index.html      # Home page
├── config/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL config
│   └── wsgi.py             # WSGI application
├── .env                    # Environment variables
├── manage.py               # Django management
└── requirements.txt        # Python dependencies
```

## 🔌 API Endpoints

### Chat Views
- `GET /` - Home page
- `GET /chat/` - List conversations (requires login)
- `GET /chat/demo/` - Public demo chat
- `POST /chat/demo/` - Send demo message
- `GET /chat/new/` - Create conversation form
- `POST /chat/new/` - Create new conversation
- `GET /chat/<id>/` - View conversation (requires login)
- `POST /chat/<id>/` - Send message in conversation
- `POST /chat/<id>/delete/` - Delete conversation

### System Endpoints
- `GET /api/health` - Health check
- `POST /api/agent` - Legacy agent endpoint (for testing)

## 💾 Database Models

### Conversation
```python
- id (Integer, Primary Key)
- user (Foreign Key to User)
- title (String)
- created_at (DateTime)
- updated_at (DateTime)
- is_active (Boolean)
```

### Message
```python
- id (Integer, Primary Key)
- conversation (Foreign Key to Conversation)
- role (String: user/assistant/system)
- content (Text)
- created_at (DateTime)
- tokens_used (Integer)
```

## 🛡️ Security Features

- CSRF protection on all forms
- User authentication required for saving conversations
- Admin user permissions
- Secure secret key in .env
- SQL injection prevention via ORM
- XFrame clickjacking protection

## 🐛 Troubleshooting

### "Could not connect to Ollama"
- Ollama is not running
- Check `OLLAMA_URL` in `.env`
- Make sure Ollama is installed and running on port 11434

### "ImportError: No module named 'django'"
- Activate virtual environment: `source ../.venv/bin/activate`
- Install requirements: `pip install -r requirements.txt`

### "No such table: app_conversation"
- Run migrations: `python manage.py migrate`

### Slow responses
- Try smaller models: `ollama pull mistral:latest`
- Increase timeout in `llm_service.py`
- Use OpenAI for faster responses

## 📦 Dependencies

- Django 4.2.30 - Web framework
- OpenAI 1.3.0 - OpenAI API client
- requests 2.32.3 - HTTP library
- redis 5.0.8 - Caching (optional)
- python-dotenv 1.0.1 - Environment variables
- Bootstrap 5 - UI framework (via CDN)

## 🚀 Production Deployment

1. Set `DEBUG=False` in `.env`
2. Set proper `DJANGO_SECRET_KEY`
3. Configure PostgreSQL database
4. Use environment-based settings
5. Collect static files: `python manage.py collectstatic`
6. Use production WSGI server (Gunicorn, uWSGI)

## 📝 Example Prompts

Try these in the chat:
- "What is machine learning?"
- "Explain Python decorators"
- "Write a function to reverse a string"
- "How does Django ORM work?"
- "Summarize the concept of REST APIs"

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## 📄 License

This project is open source and available under the MIT License.

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the Django documentation
3. Check Ollama or OpenAI documentation

## 🎯 Future Enhancements

- [ ] Multiple file uploads
- [ ] Conversation export (PDF, JSON)
- [ ] Search conversations
- [ ] Custom system prompts
- [ ] Rate limiting
- [ ] Multi-language support
- [ ] WebSocket for real-time chat
- [ ] Voice chat integration

---

**Last Updated**: May 29, 2026
**Django Version**: 4.2.30
**Python Version**: 3.9+
