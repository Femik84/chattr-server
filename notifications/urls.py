from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkAsReadView,
    NotificationMarkAllAsReadView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/read/", NotificationMarkAsReadView.as_view(), name="notification-mark-read"),
    path("read-all/", NotificationMarkAllAsReadView.as_view(), name="notification-mark-all-read"),
]
