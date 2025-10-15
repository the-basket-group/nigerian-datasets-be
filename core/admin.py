from django.contrib import admin
from django.contrib.admin import AdminSite
from django.http import HttpRequest


class SuperuserAdminSite(AdminSite):
    """Custom admin site that only allows superusers"""

    def has_permission(self, request: HttpRequest) -> bool:
        """Only allow superusers to access /admin/"""
        return request.user.is_active and request.user.is_superuser


# Override the default admin site
admin.site.__class__ = SuperuserAdminSite
admin.site.site_header = "Admin Dashboard (Superusers Only)"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Site Administration"
