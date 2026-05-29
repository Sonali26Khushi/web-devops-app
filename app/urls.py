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
    # Chat views
    path("chat/", views.chat_home, name="chat_home"),
    path("chat/demo/", views.chat_demo, name="chat_demo"),
    path("chat/new/", views.create_conversation, name="create_conversation"),
    path("chat/<int:conversation_id>/", views.chat_conversation, name="chat_conversation"),
    path("chat/<int:conversation_id>/delete/", views.delete_conversation, name="delete_conversation"),
    # Smart Search
    path("search/", views.search_home, name="search_home"),
    path("search/add/", views.add_search_record, name="add_search_record"),
    path("search/delete/<int:record_id>/", views.delete_search_record, name="delete_search_record"),
]
