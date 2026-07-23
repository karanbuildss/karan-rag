from django.contrib import admin

from documents.models import (
    DataExtractionRecord,
    DocumentChunk,
    DocumentPage,
    ProjectDocumentLink,
    SourceDocument,
)


class DocumentPageInline(admin.TabularInline):
    model = DocumentPage
    fields = (
        "page_number",
        "extraction_method",
        "text_quality_score",
        "ocr_confidence",
        "review_status",
    )
    readonly_fields = fields
    extra = 0
    show_change_link = True


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title_en",
        "local_government",
        "fiscal_year",
        "document_type",
        "processing_status",
        "page_count",
    )
    list_filter = ("processing_status", "document_type", "language", "local_government")
    search_fields = ("title_en", "title_np", "original_filename", "sha256")
    readonly_fields = ("sha256", "page_count", "extracted_at", "created_at", "updated_at")
    inlines = [DocumentPageInline]


@admin.action(description="Approve selected extracted pages")
def approve_pages(modeladmin, request, queryset):
    queryset.exclude(extraction_method=DocumentPage.ExtractionMethod.NONE).update(
        review_status=DocumentPage.ReviewStatus.APPROVED
    )


@admin.register(DocumentPage)
class DocumentPageAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "page_number",
        "extraction_method",
        "text_quality_score",
        "ocr_confidence",
        "review_status",
    )
    list_filter = ("extraction_method", "review_status")
    search_fields = ("document__title_en", "document__title_np", "extracted_text")
    actions = [approve_pages]


admin.site.register(DataExtractionRecord)
admin.site.register(DocumentChunk)
admin.site.register(ProjectDocumentLink)
