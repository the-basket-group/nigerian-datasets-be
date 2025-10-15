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
        # Moderators cannot create users
        if hasattr(request.user, "role") and request.user.role == "moderator":
            return False
        return super().has_add_permission(request)

    def has_delete_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        # Moderators cannot delete users
        if hasattr(request.user, "role") and request.user.role == "moderator":
            return False
        return super().has_delete_permission(request, obj)
