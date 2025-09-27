from django.contrib import admin

from trends.models import SearchQuery


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "created_at")
    list_filter = ("created_at",)
    search_fields = ("query", "user__email")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
