from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


# -------------------------------
# List Notifications for Logged-in User
# -------------------------------
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects.filter(to_user=self.request.user)
            .select_related("from_user", "to_user", "post", "comment")
            .prefetch_related("post__images")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# Mark a Single Notification as Read
# -------------------------------
class NotificationMarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, id=pk, to_user=request.user)
        notification.is_read = True
        notification.save()
        return Response(
            {"detail": "Notification marked as read."},
            status=status.HTTP_200_OK,
        )


# -------------------------------
# Mark All Notifications as Read
# -------------------------------
class NotificationMarkAllAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(
            to_user=request.user, is_read=False
        ).update(is_read=True)

        return Response(
            {"detail": f"{count} notifications marked as read.", "updated_count": count},
            status=status.HTTP_200_OK,
        )
