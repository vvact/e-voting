from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redoc (clean documentation)
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # path('grappelli/', include('grappelli.urls')),
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/elections/", include("elections.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
