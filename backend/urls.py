from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from datasets.moderator_admin import moderator_admin_site

urlpatterns = [
    path("", lambda request: redirect("api-docs"), name="root-redirect"),
    path("admin/", admin.site.urls),
    path("moderator/", moderator_admin_site.urls),
    path(
        "api/v1/",
        include(
            [
                path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
                path(
                    "docs/",
                    SpectacularSwaggerView.as_view(url_name="api-schema"),
                    name="api-docs",
                ),
                path("", include("core.urls")),
                path("users/", include("users.urls")),
                path("datasets/", include("datasets.urls")),
                path("trends/", include("trends.urls")),
            ]
        ),
    ),
]
