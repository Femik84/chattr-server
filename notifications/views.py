from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification, FCMDevice
from .serializers import NotificationSerializer, FCMDeviceSerializer

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


# -------------------------------
# Register FCM Token for Push Notifications
# -------------------------------
@method_decorator(csrf_exempt, name="dispatch")
class RegisterFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FCMDeviceSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]

            # Make it idempotent
            device, created = FCMDevice.objects.get_or_create(
                token=token,
                defaults={"user": request.user}
            )

            # If token exists but belongs to another user, update it
            if not created and device.user != request.user:
                device.user = request.user
                device.save()

            return Response(
                {"detail": "FCM token registered successfully."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
