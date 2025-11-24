from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkAsReadView,
    NotificationMarkAllAsReadView,
    RegisterFCMTokenView,  
)

urlpatterns = [
    # Notifications
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/read/", NotificationMarkAsReadView.as_view(), name="notification-mark-read"),
    path("read-all/", NotificationMarkAllAsReadView.as_view(), name="notification-mark-all-read"),

    path("register-token/", RegisterFCMTokenView.as_view(), name="register-fcm-token"),
]
