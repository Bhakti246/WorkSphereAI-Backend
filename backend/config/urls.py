from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Token views are provided by `ems.auth_urls` under `/api/auth/`
from ems.auth_views import CustomTokenObtainPairView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # JWT Authentication
    path("api/auth/", include("ems.auth_urls")),

    # Consolidated API include
    path("api/", include("ems.urls")),
    # Frontend pages for basic auth flows and dashboard
    path("", include("ems.frontend_urls")),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )