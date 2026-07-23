from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from documents.models import DocumentPage, ProjectDocumentLink, SourceDocument


class SourceDocumentListSerializer(serializers.ModelSerializer):
    local_government_code = serializers.CharField(source="local_government.code", read_only=True)
    local_government_name_en = serializers.CharField(
        source="local_government.name_en", read_only=True
    )
    local_government_name_np = serializers.CharField(
        source="local_government.name_np", read_only=True
    )
    fiscal_year_code = serializers.CharField(source="fiscal_year.code", read_only=True)
    fiscal_year_bs = serializers.CharField(source="fiscal_year.year_bs", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = SourceDocument
        fields = [
            "id",
            "title_en",
            "title_np",
            "document_type",
            "language",
            "original_filename",
            "source_url",
            "source_url_kind",
            "source_note",
            "data_classification",
            "processing_status",
            "page_count",
            "file_url",
            "local_government_code",
            "local_government_name_en",
            "local_government_name_np",
            "fiscal_year_code",
            "fiscal_year_bs",
        ]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_file_url(self, instance) -> str | None:
        if not instance.original_file:
            return None
        request = self.context.get("request")
        return (
            request.build_absolute_uri(instance.original_file.url)
            if request
            else instance.original_file.url
        )


class DocumentPageSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPage
        fields = [
            "page_number",
            "section",
            "extraction_method",
            "text_quality_score",
            "ocr_confidence",
            "review_status",
            "extraction_warnings",
            "character_count",
        ]


class DocumentPageDetailSerializer(DocumentPageSummarySerializer):
    document_id = serializers.UUIDField(source="document.id", read_only=True)
    document_title = serializers.CharField(source="document.title_en", read_only=True)
    source_url = serializers.URLField(source="document.source_url", read_only=True)

    class Meta(DocumentPageSummarySerializer.Meta):
        fields = [
            "document_id",
            "document_title",
            *DocumentPageSummarySerializer.Meta.fields,
            "extracted_text",
            "source_url",
        ]


class SourceDocumentDetailSerializer(SourceDocumentListSerializer):
    pages = DocumentPageSummarySerializer(many=True, read_only=True)

    class Meta(SourceDocumentListSerializer.Meta):
        fields = [*SourceDocumentListSerializer.Meta.fields, "sha256", "extracted_at", "pages"]


class ProjectDocumentLinkSerializer(serializers.ModelSerializer):
    document = SourceDocumentListSerializer(read_only=True)
    citation = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDocumentLink
        fields = [
            "relationship",
            "page_from",
            "page_to",
            "section",
            "evidence_note_en",
            "evidence_note_np",
            "document",
            "citation",
        ]

    @extend_schema_field(serializers.DictField())
    def get_citation(self, instance) -> dict:
        return {
            "document_id": str(instance.document_id),
            "document_title": instance.document.title_en,
            "page": instance.page_from,
            "section": instance.section,
            "source_url": instance.document.source_url,
        }
