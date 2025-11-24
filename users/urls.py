from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    GoogleAuthView,
    MeView,
    EmailSignupView,
    EmailLoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    FollowToggleView,
    UserDetailView,
    LogoutView,  
)

urlpatterns = [
    # Google OAuth
    path("google/", GoogleAuthView.as_view(), name="google-auth"),

    # Email/password auth
    path("signup/", EmailSignupView.as_view(), name="email-signup"),
    path("login/", EmailLoginView.as_view(), name="email-login"),

    # Logout
    path("logout/", LogoutView.as_view(), name="logout"),  # <-- new endpoint

    # Password reset
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),

    # JWT token refresh
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Current user profile (GET + PATCH)
    path("me/", MeView.as_view(), name="me"),

    # Follow/unfollow user
    path("follow/<int:user_id>/", FollowToggleView.as_view(), name="follow-toggle"),
     
    # Get user by username 
    path("<str:username>/", UserDetailView.as_view(), name="user-detail"),
]
