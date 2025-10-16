from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from datasets.models import Dataset


class ModeratorAdminSite(AdminSite):
    site_header = "Moderator Dashboard"
    site_title = "Dataset Moderation"
    index_title = "Approve Datasets"

    def has_permission(self, request: HttpRequest) -> bool:
        """Allow moderators only"""
        return (
            request.user.is_active
            and request.user.is_staff
            and request.user.role == "moderator"
        )


# Create the moderator admin site instance
moderator_admin_site = ModeratorAdminSite(name="moderator_admin")


@admin.register(Dataset, site=moderator_admin_site)
class ModeratorDatasetAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "title",
        "owner",
        "status",
        "approval_status",
        "is_public",
        "views",
        "downloads",
        "created_at",
    ]
    list_filter = ["is_approved", "status", "is_public", "created_at"]
    search_fields = ["title", "description", "owner__email"]
    readonly_fields = [
        "id",
        "title",
        "description",
        "license",
        "source_org",
        "geography",
        "update_frequency",
        "status",
        "is_public",
        "metadata",
        "owner",
        "tags",
        "completeness_score",
        "changelog",
        "views",
        "downloads",
        "created_at",
        "updated_at",
    ]
    actions = ["approve_datasets", "reject_datasets"]

    def approval_status(self, obj: Dataset) -> str:
        if obj.is_approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">⏳ Pending</span>'
        )

    approval_status.short_description = "Approval Status"  # type: ignore[attr-defined]

    @admin.action(description="Approve selected datasets")
    def approve_datasets(
        self, request: HttpRequest, queryset: QuerySet[Dataset]
    ) -> None:
        updated = queryset.update(is_approved=True, approved_by=request.user)
        self.message_user(request, f"{updated} dataset(s) approved successfully.")

    @admin.action(description="Reject selected datasets")
    def reject_datasets(
        self, request: HttpRequest, queryset: QuerySet[Dataset]
    ) -> None:
        updated = queryset.update(is_approved=False, approved_by=request.user)
        self.message_user(request, f"{updated} dataset(s) rejected.")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Dataset]:
        qs = super().get_queryset(request)
        # Moderators only see datasets pending approval
        return qs.filter(is_approved=False)

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Moderators cannot create datasets
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Dataset | None = None
    ) -> bool:
        # Moderators cannot delete datasets
        return False
