import json
from datetime import datetime, timezone

import redis
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from .models import AppEvent, Conversation, Message, SearchRecord
from .forms import ConversationForm, LoginForm, MessageForm, RegisterForm
from .llm_service import LLMService

LOCAL_HITS = 0
TASKS_SESSION_KEY = "task_board_tasks"
TASK_SEQUENCE_SESSION_KEY = "task_board_task_sequence"


def redis_client():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )


def get_cache_hits():
    global LOCAL_HITS
    try:
        cache = redis_client()
        return cache.incr("home_hits"), "redis"
    except Exception:
        LOCAL_HITS += 1
        return LOCAL_HITS, "local-memory"


def db_backend_name():
    engine = settings.DATABASES["default"]["ENGINE"]
    if "postgresql" in engine:
        return "postgres"
    if "sqlite" in engine:
        return "sqlite"
    return engine


def get_tasks(request):
    return request.session.get(TASKS_SESSION_KEY, [])


def save_tasks(request, tasks):
    request.session[TASKS_SESSION_KEY] = tasks
    request.session.modified = True


def next_task_id(request):
    task_sequence = request.session.get(TASK_SEQUENCE_SESSION_KEY, 0) + 1
    request.session[TASK_SEQUENCE_SESSION_KEY] = task_sequence
    request.session.modified = True
    return task_sequence


@login_required(login_url="login")
def index(request):
    now_utc = datetime.now(timezone.utc).isoformat()
    now_utc_clock = datetime.now(timezone.utc).strftime("%H:%M:%S")
    hit_count, cache_backend = get_cache_hits()
    tasks = get_tasks(request)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            title = request.POST.get("task", "").strip()
            note = request.POST.get("note", "").strip()

            if not title:
                messages.warning(request, "Add a short task title first.")
                return redirect("index")

            tasks.insert(
                0,
                {
                    "id": next_task_id(request),
                    "title": title,
                    "note": note,
                    "done": False,
                },
            )
            save_tasks(request, tasks)
            messages.success(request, f'Added "{title}" to your task board.')
            return redirect("index")

        if action == "toggle":
            task_id = request.POST.get("task_id")
            updated_tasks = []
            toggled = False

            for task in tasks:
                if str(task.get("id")) == task_id:
                    task = {**task, "done": not task.get("done", False)}
                    toggled = True
                updated_tasks.append(task)

            save_tasks(request, updated_tasks)
            if toggled:
                messages.info(request, "Task status updated.")
            else:
                messages.warning(request, "Task not found.")
            return redirect("index")

        if action == "remove":
            task_id = request.POST.get("task_id")
            filtered_tasks = [task for task in tasks if str(task.get("id")) != task_id]

            if len(filtered_tasks) == len(tasks):
                messages.warning(request, "Task not found.")
            else:
                messages.success(request, "Task removed.")

            save_tasks(request, filtered_tasks)
            return redirect("index")

        if action == "clear_completed":
            filtered_tasks = [task for task in tasks if not task.get("done", False)]
            removed_count = len(tasks) - len(filtered_tasks)
            save_tasks(request, filtered_tasks)
            messages.success(request, f"Cleared {removed_count} completed task(s).")
            return redirect("index")

        messages.warning(request, "Unknown action.")
        return redirect("index")

    AppEvent.objects.create(event_type="page_view")
    db_events = AppEvent.objects.count()
    open_tasks = sum(1 for task in tasks if not task.get("done", False))
    completed_tasks = len(tasks) - open_tasks

    conversation_count = Conversation.objects.filter(
        user=request.user, is_active=True
    ).count()
    message_count = Message.objects.filter(
        conversation__user=request.user, conversation__is_active=True
    ).count()
    token_total = (
        Message.objects.filter(
            conversation__user=request.user, conversation__is_active=True
        )
        .aggregate(total=Sum("tokens_used"))
        .get("total")
        or 0
    )
    recent_sessions = Conversation.objects.filter(
        user=request.user,
        is_active=True,
    )[:4]

    context = {
        "now_utc": now_utc,
        "now_utc_clock": now_utc_clock,
        "hit_count": hit_count,
        "db_events": db_events,
        "db_backend": db_backend_name(),
        "cache_backend": cache_backend,
        "tasks": tasks,
        "total_tasks": len(tasks),
        "open_tasks": open_tasks,
        "completed_tasks": completed_tasks,
        "today_label": datetime.now(timezone.utc).strftime("%A, %d %B %Y"),
        "session_count": conversation_count,
        "message_count": message_count,
        "token_total": token_total,
        "recent_sessions": recent_sessions,
    }
    return render(request, "index.html", context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = RegisterForm()

    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "You are now signed in.")
            next_url = (
                request.POST.get("next")
                or request.GET.get("next")
                or settings.LOGIN_REDIRECT_URL
            )
            return redirect(next_url)
    else:
        form = LoginForm(request)

    return render(
        request, "auth/login.html", {"form": form, "next": request.GET.get("next", "")}
    )


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("login")


def health(request):
    status = {
        "app": "ok",
        "database": "unknown",
        "cache": "unknown",
        "ollama": "unknown",
    }

    try:
        AppEvent.objects.exists()
        status["database"] = "ok"
    except Exception as exc:
        status["database"] = str(exc)

    try:
        cache = redis_client()
        cache.ping()
        status["cache"] = "ok"
    except Exception as exc:
        status["cache"] = str(exc)

    try:
        response = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        status["ollama"] = "ok"
    except Exception as exc:
        status["ollama"] = f"optional service unavailable: {exc}"

    code = 200 if status["database"] == "ok" else 503
    return JsonResponse(status, status=code)


@csrf_exempt
def agent(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON body"}, status=400)

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return JsonResponse({"error": "prompt is required"}, status=400)

    try:
        response = requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return JsonResponse(
            {
                "model": settings.OLLAMA_MODEL,
                "response": data.get("response", ""),
            }
        )
    except Exception as exc:
        return JsonResponse({"error": f"ollama request failed: {exc}"}, status=502)


# ============================================================================
# Focus Session Views (DevPulse)
# ============================================================================


@login_required(login_url="login")
def sessions_home(request):
    """List all active focus sessions for the signed-in user."""
    sessions = Conversation.objects.filter(user=request.user, is_active=True)
    llm_info = LLMService().get_provider_info()
    return render(
        request, "sessions/list.html", {"sessions": sessions, "llm_info": llm_info}
    )


@login_required(login_url="login")
def create_session(request):
    """Create a new focus session."""
    if request.method == "POST":
        form = ConversationForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            messages.success(request, f'Session "{session.title}" created.')
            return redirect("session_workspace", session_id=session.id)
    else:
        form = ConversationForm()
    return render(request, "sessions/create.html", {"form": form})


@login_required(login_url="login")
def session_workspace(request, session_id):
    """Active focus session with AI."""
    session = get_object_or_404(
        Conversation, id=session_id, user=request.user, is_active=True
    )

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data["content"]
            Message.objects.create(
                conversation=session, role="user", content=user_message
            )
            history = [
                {"role": m.role, "content": m.content} for m in session.messages.all()
            ]
            llm = LLMService()
            result = llm.generate_response(
                messages=history, temperature=0.7, max_tokens=600
            )
            if not result.get("error", False):
                Message.objects.create(
                    conversation=session,
                    role="assistant",
                    content=result["response"],
                    tokens_used=result.get("tokens_used", 0),
                )
            else:
                messages.error(
                    request, f"AI error: {result.get('response', 'Unknown')}"
                )
            return redirect("session_workspace", session_id=session_id)
    else:
        form = MessageForm()

    all_sessions = Conversation.objects.filter(user=request.user, is_active=True)
    llm_info = LLMService().get_provider_info()
    return render(
        request,
        "sessions/workspace.html",
        {
            "session": session,
            "all_sessions": all_sessions,
            "form": form,
            "llm_info": llm_info,
        },
    )


@login_required(login_url="login")
@require_http_methods(["POST"])
def end_session(request, session_id):
    """Archive (soft-delete) a focus session."""
    session = get_object_or_404(Conversation, id=session_id, user=request.user)
    session.is_active = False
    session.save()
    messages.success(request, "Session archived.")
    return redirect("sessions_home")


# ============================================================================
# Legacy LLM Chat Views (kept for backward compat, not exposed in URLs)
# ============================================================================


@login_required(login_url="login")
def chat_home(request):
    """Legacy workroom list (not in primary navigation)."""
    conversations = Conversation.objects.filter(user=request.user, is_active=True)
    llm_info = LLMService().get_provider_info()

    context = {
        "conversations": conversations,
        "llm_info": llm_info,
    }
    return render(request, "chat_home.html", context)


@login_required(login_url="login")
def chat_demo(request):
    """Legacy demo chat route (not exposed in main navigation)"""
    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()

        if not user_message:
            messages.warning(request, "Please enter a message.")
            return redirect("chat_demo")

        # Generate response using LLM
        llm = LLMService()
        response_data = llm.generate_response(
            messages=[{"role": "user", "content": user_message}],
            temperature=0.7,
            max_tokens=500,
        )

        context = {
            "user_message": user_message,
            "ai_response": response_data.get("response"),
            "tokens_used": response_data.get("tokens_used"),
            "provider": response_data.get("provider"),
            "error": response_data.get("error", False),
            "llm_info": llm.get_provider_info(),
        }
        return render(request, "chat_demo.html", context)

    llm = LLMService()
    context = {
        "llm_info": llm.get_provider_info(),
    }
    return render(request, "chat_demo.html", context)


@login_required(login_url="login")
def chat_conversation(request, conversation_id):
    """View a specific conversation with the AI"""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, user=request.user, is_active=True
    )

    if request.method == "POST":
        form = MessageForm(request.POST)

        if form.is_valid():
            user_message = form.cleaned_data["content"]

            # Save user message
            Message.objects.create(
                conversation=conversation,
                role="user",
                content=user_message,
            )

            # Get conversation history
            previous_messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                }
                for msg in conversation.messages.all()
            ]

            # Generate AI response
            llm = LLMService()
            response_data = llm.generate_response(
                messages=previous_messages,
                temperature=0.7,
                max_tokens=500,
            )

            if not response_data.get("error", False):
                # Save assistant response
                Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=response_data["response"],
                    tokens_used=response_data.get("tokens_used", 0),
                )
                messages.success(request, "Response generated successfully.")
            else:
                messages.error(
                    request, f"Error: {response_data.get('response', 'Unknown error')}"
                )

            return redirect("chat_conversation", conversation_id=conversation_id)
    else:
        form = MessageForm()

    all_conversations = Conversation.objects.filter(user=request.user, is_active=True)
    llm = LLMService()

    context = {
        "conversation": conversation,
        "all_conversations": all_conversations,
        "form": form,
        "llm_info": llm.get_provider_info(),
    }
    return render(request, "chat_conversation.html", context)


@login_required(login_url="login")
def create_conversation(request):
    """Create a new conversation"""
    if request.method == "POST":
        form = ConversationForm(request.POST)

        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.user = request.user
            conversation.save()
            messages.success(request, f"Conversation '{conversation.title}' created.")
            return redirect("chat_conversation", conversation_id=conversation.id)
    else:
        form = ConversationForm()

    context = {
        "form": form,
    }
    return render(request, "create_conversation.html", context)


@login_required(login_url="login")
@require_http_methods(["POST"])
def delete_conversation(request, conversation_id):
    """Delete a conversation (soft delete)"""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, user=request.user
    )
    conversation.is_active = False
    conversation.save()
    messages.success(request, "Conversation deleted.")
    return redirect("chat_home")


# ============================================================================
# Floating Widget Chat API
# ============================================================================


@csrf_exempt
@require_http_methods(["POST"])
def widget_chat(request):
    """AJAX endpoint for the floating chat widget (no auth required)"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = (payload.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "message is required"}, status=400)

    llm = LLMService()
    result = llm.generate_response(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant embedded in a web application. "
                    "Give concise, friendly answers. Max 3 short paragraphs."
                ),
            },
            {"role": "user", "content": message},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return JsonResponse(
        {"response": result.get("response", ""), "tokens": result.get("tokens_used", 0)}
    )


# ============================================================================
# Smart Search Application
# ============================================================================


def _seed_records():
    """Create demo records if the table is empty"""
    if SearchRecord.objects.exists():
        return
    demo = [
        {
            "title": "Django Framework",
            "category": "article",
            "content": (
                "Django is a high-level Python web framework that encourages rapid development "
                "and clean, pragmatic design. It includes an ORM, admin interface, authentication, and more."
            ),
            "tags": "python,web,framework,backend",
        },
        {
            "title": "Machine Learning Basics",
            "category": "article",
            "content": (
                "Machine learning is a subset of AI that enables systems to learn from data. "
                "Key algorithms include linear regression, decision trees, neural networks, and clustering."
            ),
            "tags": "AI,ML,data,science",
        },
        {
            "title": "Alice Johnson",
            "category": "person",
            "content": (
                "Senior software engineer with 8 years of experience in Python, Django, and cloud technologies. "
                "Works at TechCorp. Expert in API design and microservices."
            ),
            "tags": "engineer,python,backend",
        },
        {
            "title": "Bob Smith",
            "category": "person",
            "content": (
                "Product manager with a background in UX design. Manages the mobile team at StartupXYZ. "
                "Interested in agile methodologies and user research."
            ),
            "tags": "PM,agile,mobile,design",
        },
        {
            "title": "Smart Watch Pro",
            "category": "product",
            "content": (
                "A premium smartwatch with health tracking, 7-day battery, GPS, and AMOLED display. "
                "Waterproof up to 50m. Available in black and silver. Price: $299."
            ),
            "tags": "wearable,gadget,health,tech",
        },
        {
            "title": "Ergonomic Office Chair",
            "category": "product",
            "content": (
                "Fully adjustable ergonomic chair with lumbar support, breathable mesh back, "
                "and 360-degree swivel. Ideal for long work sessions. Price: $450."
            ),
            "tags": "furniture,office,ergonomic",
        },
        {
            "title": "REST API Design Best Practices",
            "category": "note",
            "content": (
                "Use nouns for resource URLs, HTTP verbs for actions, JSON for responses. "
                "Always version your API (v1/v2). Return proper status codes. Add pagination for list endpoints."
            ),
            "tags": "api,rest,design,backend",
        },
        {
            "title": "Python Tips & Tricks",
            "category": "note",
            "content": (
                "Use list comprehensions for clean loops. f-strings are faster than .format(). "
                "dataclasses simplify class creation. Use walrus operator := for assignment expressions."
            ),
            "tags": "python,tips,dev",
        },
    ]
    for d in demo:
        SearchRecord.objects.create(**d)


@login_required(login_url="login")
def search_home(request):
    """Legacy Smart Search route (not exposed in main navigation)"""
    _seed_records()

    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    ai_answer = None
    results = SearchRecord.objects.all()

    if category:
        results = results.filter(category=category)

    if query:
        # Keyword filter across title, content, tags
        from django.db.models import Q

        results = results.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(tags__icontains=query)
        )

        # Ask the LLM to summarise based on the matching records
        if results.exists():
            records_text = "\n\n".join(
                f"[{r.category.upper()}] {r.title}:\n{r.content}" for r in results[:5]
            )
            llm = LLMService()
            llm_result = llm.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a search assistant. The user searched for a query. "
                            "Based on the matching records below, give a brief, helpful "
                            "summary (2-3 sentences). Be direct and informative."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nMatching records:\n{records_text}",
                    },
                ],
                temperature=0.5,
                max_tokens=250,
            )
            ai_answer = llm_result.get("response")
        else:
            # No keyword match — ask LLM for a general answer
            llm = LLMService()
            llm_result = llm.generate_response(
                messages=[{"role": "user", "content": query}],
                temperature=0.7,
                max_tokens=300,
            )
            ai_answer = llm_result.get("response")

    categories = SearchRecord.CATEGORY_CHOICES
    context = {
        "query": query,
        "category": category,
        "results": results,
        "ai_answer": ai_answer,
        "categories": categories,
        "total_records": SearchRecord.objects.count(),
    }
    return render(request, "search_home.html", context)


@login_required(login_url="login")
def add_search_record(request):
    """Add a new searchable record"""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        category = request.POST.get("category", "other")
        content = request.POST.get("content", "").strip()
        tags = request.POST.get("tags", "").strip()

        if not title or not content:
            messages.error(request, "Title and content are required.")
            return redirect("search_home")

        SearchRecord.objects.create(
            title=title,
            category=category,
            content=content,
            tags=tags,
            created_by=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, f'Record "{title}" added successfully.')
        return redirect("search_home")

    return redirect("search_home")


@login_required(login_url="login")
def delete_search_record(request, record_id):
    """Delete a search record"""
    record = get_object_or_404(SearchRecord, id=record_id)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Record deleted.")
    return redirect("search_home")
