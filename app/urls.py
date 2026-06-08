from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("api/health", views.health, name="health"),
    path("api/agent", views.agent, name="agent"),
    path("api/widget-chat/", views.widget_chat, name="widget_chat"),
    # Focus Sessions
    path("sessions/", views.sessions_home, name="sessions_home"),
    path("sessions/new/", views.create_session, name="create_session"),
    path(
        "sessions/<int:session_id>/", views.session_workspace, name="session_workspace"
    ),
    path("sessions/<int:session_id>/end/", views.end_session, name="end_session"),
]
