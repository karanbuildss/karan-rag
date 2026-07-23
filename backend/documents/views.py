from config.api import EnvelopeReadOnlyModelViewSet, success_response
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from documents.models import DocumentPage, SourceDocument
from documents.serializers import (
    DocumentPageDetailSerializer,
    SourceDocumentDetailSerializer,
    SourceDocumentListSerializer,
)


class SourceDocumentViewSet(EnvelopeReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filterset_fields = {
        "local_government__code": ["exact"],
        "fiscal_year__code": ["exact"],
        "document_type": ["exact"],
        "language": ["exact"],
        "processing_status": ["exact"],
        "data_classification": ["exact"],
    }
    search_fields = [
        "title_en",
        "title_np",
        "original_filename",
        "local_government__name_en",
        "local_government__name_np",
    ]
    ordering_fields = ["fiscal_year__code", "title_en", "page_count", "created_at"]
    ordering = ["-fiscal_year__code", "title_en"]

    def get_queryset(self):
        queryset = SourceDocument.objects.select_related("local_government", "fiscal_year")
        if self.action == "retrieve":
            page_queryset = DocumentPage.objects.defer("extracted_text").order_by("page_number")
            queryset = queryset.prefetch_related(Prefetch("pages", queryset=page_queryset))
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SourceDocumentDetailSerializer
        return SourceDocumentListSerializer

    @extend_schema(responses=DocumentPageDetailSerializer)
    @action(detail=True, methods=["get"], url_path=r"pages/(?P<page_number>[0-9]+)")
    def page(self, request, pk=None, page_number=None):
        document = self.get_object()
        document_page = get_object_or_404(document.pages, page_number=page_number)
        serializer = DocumentPageDetailSerializer(document_page, context={"request": request})
        return success_response(serializer.data)

    @action(detail=True, methods=["get"], url_path="processing-status")
    def processing_status(self, request, pk=None):
        document = self.get_object()
        return success_response(
            {
                "document_id": str(document.id),
                "status": document.processing_status,
                "page_count": document.page_count,
                "extracted_pages": document.pages.count(),
                "review_required_pages": document.pages.filter(
                    review_status=DocumentPage.ReviewStatus.REVIEW_REQUIRED
                ).count(),
                "error": document.extraction_error or None,
                "extracted_at": document.extracted_at,
            }
        )
