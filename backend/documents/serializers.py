from config.models import DataClassification
from django.urls import reverse
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
    hosted_metadata_only = serializers.SerializerMethodField()

    class Meta:
        model = SourceDocument
        fields = [
            "id",
            "title_en",
            "title_np",
            "document_type",
            "language",
            "file_format",
            "original_filename",
            "source_url",
            "source_url_kind",
            "source_note",
            "data_classification",
            "processing_status",
            "page_count",
            "file_url",
            "hosted_metadata_only",
            "local_government_code",
            "local_government_name_en",
            "local_government_name_np",
            "fiscal_year_code",
            "fiscal_year_bs",
        ]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_file_url(self, instance) -> str | None:
        if (
            not instance.original_file
            and instance.data_classification != DataClassification.SYNTHETIC_DEMO
        ):
            return None
        request = self.context.get("request")
        file_path = reverse("source-document-file", kwargs={"pk": instance.pk})
        return request.build_absolute_uri(file_path) if request else file_path

    @extend_schema_field(serializers.BooleanField())
    def get_hosted_metadata_only(self, instance) -> bool:
        return bool(
            not instance.original_file
            and instance.data_classification != DataClassification.SYNTHETIC_DEMO
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
    catalog_evidence = serializers.SerializerMethodField()

    class Meta(SourceDocumentListSerializer.Meta):
        fields = [
            *SourceDocumentListSerializer.Meta.fields,
            "sha256",
            "extracted_at",
            "pages",
            "catalog_evidence",
        ]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_catalog_evidence(self, instance) -> list[dict]:
        """Return reviewed, human-authored catalogue context for hosted metadata records."""
        evidence = []
        for link in instance.project_links.all():
            evidence.append(
                {
                    "kind": "project_evidence",
                    "relationship": link.relationship,
                    "page_from": link.page_from,
                    "page_to": link.page_to,
                    "section": link.section,
                    "summary_en": link.evidence_note_en,
                    "summary_np": link.evidence_note_np,
                    "project": {
                        "id": str(link.project_id),
                        "code": link.project.code,
                        "title_en": link.project.title_en,
                        "title_np": link.project.title_np,
                    },
                }
            )

        for allocation in instance.budget_allocations.all():
            if allocation.review_status != "reviewed":
                continue
            sector = allocation.subsector.sector
            evidence.append(
                {
                    "kind": "reviewed_budget_fact",
                    "relationship": "allocation",
                    "page_from": allocation.source_page,
                    "page_to": allocation.source_page,
                    "section": sector.name_en,
                    "section_np": sector.name_np,
                    "summary_en": allocation.source_scope_en,
                    "summary_np": allocation.source_scope_np,
                    "allocated_amount": str(allocation.allocated_amount),
                    "spent_amount": (
                        str(allocation.spent_amount)
                        if allocation.spent_amount is not None
                        else None
                    ),
                    "project": None,
                }
            )

        return sorted(
            evidence,
            key=lambda item: (
                item["page_from"] is None,
                item["page_from"] or 0,
                item["kind"],
            ),
        )


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
