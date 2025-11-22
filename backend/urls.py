from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/posts/", include("posts.urls")),
    path("api/", include("comments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/", include("messaging.urls")),
    path("api/search/", include("search.urls"))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


