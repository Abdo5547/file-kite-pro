from django.contrib import admin

from .models import ProcessingJob, ProcessingJobFile


class ProcessingJobFileInline(admin.TabularInline):
    model = ProcessingJobFile
    extra = 0
    readonly_fields = (
        "original_filename",
        "size",
        "order",
        "created_at",
    )


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tool",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "tool",
        "status",
        "created_at",
    )
    search_fields = (
        "id",
        "tool",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    inlines = [ProcessingJobFileInline]


@admin.register(ProcessingJobFile)
class ProcessingJobFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "original_filename",
        "size",
        "order",
        "created_at",
    )
    list_filter = (
        "created_at",
    )
    search_fields = (
        "original_filename",
        "job__id",
    )