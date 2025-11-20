from django.urls import path
from . import views

urlpatterns = [
    # Conversations
    path("conversations/", views.ConversationListView.as_view(), name="conversation-list"),
    path("conversations/start/", views.ConversationStartView.as_view(), name="conversation-start"),
    path("conversations/<int:pk>/", views.ConversationDetailView.as_view(), name="conversation-detail"),

    # Messages
    path(
        "conversations/<int:conversation_id>/messages/",
        views.MessageListCreateView.as_view(),
        name="message-list-create",
    ),

    # Mark messages as read
    path(
        "conversations/<int:conversation_id>/messages/mark-read/",
        views.MarkMessagesReadView.as_view(),
        name="message-mark-read",
    ),
]
