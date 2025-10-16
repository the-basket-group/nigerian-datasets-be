from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["email", "first_name", "last_name", "role", "status", "is_staff"]
    list_filter = ["role", "status", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        qs = super().get_queryset(request)
        # Moderators can only see themselves
        if hasattr(request.user, "role") and request.user.role == "moderator":
            return qs.filter(id=request.user.id)
        return qs

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Only superusers can create users
        if not request.user.is_superuser:
            return False
        return super().has_add_permission(request)

    def has_change_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        # Moderators can only edit themselves
        if hasattr(request.user, "role") and request.user.role == "moderator":
            if obj is not None and obj.id != request.user.id:
                return False
            return True
        # Only superusers can edit other users
        if not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        # Only superusers can delete users
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
