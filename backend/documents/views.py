from io import BytesIO

import pymupdf
from accounts.models import CitizenProfile
from audit.services import record_audit
from config.api import EnvelopeReadOnlyModelViewSet, success_response
from config.models import DataClassification
from django.db.models import Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response

from documents.models import DocumentPage, SourceDocument
from documents.serializers import (
    DocumentPageDetailSerializer,
    SourceDocumentDetailSerializer,
    SourceDocumentListSerializer,
)


class CanReviewDocuments(BasePermission):
    """Limit evidence acceptance to trusted demo operators."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = getattr(getattr(request.user, "citizen_profile", None), "role", None)
        return bool(
            request.user.is_staff
            or role
            in {
                CitizenProfile.Role.OFFICIAL,
                CitizenProfile.Role.MODERATOR,
                CitizenProfile.Role.SYSTEM_ADMIN,
            }
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
            queryset = queryset.prefetch_related(
                Prefetch("pages", queryset=page_queryset),
                "project_links__project",
                "budget_allocations__subsector__sector",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SourceDocumentDetailSerializer
        return SourceDocumentListSerializer

    @action(detail=True, methods=["get"], url_path="file")
    @xframe_options_exempt
    def file(self, request, pk=None):
        """Stream a preserved public source without blocking the in-app viewer."""
        document = self.get_object()
        if not document.original_file:
            if document.data_classification != DataClassification.SYNTHETIC_DEMO:
                raise Http404("The preserved source file is not available.")
            return self._synthetic_showcase_file(document)
        try:
            source = document.original_file.open("rb")
        except (FileNotFoundError, OSError) as exc:
            raise Http404("The preserved source file is not available.") from exc
        response = FileResponse(
            source,
            as_attachment=False,
            filename=document.original_filename,
        )
        response["Cache-Control"] = "private, max-age=3600"
        return response

    @staticmethod
    def _synthetic_showcase_file(document):
        """Render an explicitly labelled PDF for a synthetic demonstration record."""
        pdf = pymupdf.open()
        page_rows = list(document.pages.order_by("page_number")) or [None]
        for page_row in page_rows:
            page = pdf.new_page()
            page_number = page_row.page_number if page_row else 1
            section = page_row.section if page_row else "Synthetic showcase"
            body = page_row.extracted_text if page_row else document.source_note
            ascii_body = body.encode("ascii", errors="ignore").decode("ascii")
            text = (
                "BUDGET DARPAN - SYNTHETIC DEMONSTRATION DATA\n\n"
                f"{document.title_en}\nPage {page_number}: {section}\n\n"
                f"{ascii_body}\n\n"
                "This generated showcase is not an official government record."
            )
            page.insert_textbox(pymupdf.Rect(54, 54, 540, 780), text, fontsize=10)
        payload = BytesIO(pdf.tobytes())
        pdf.close()
        response = FileResponse(
            payload,
            as_attachment=False,
            filename=document.original_filename,
            content_type="application/pdf",
        )
        response["Cache-Control"] = "no-store"
        return response

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

    @action(
        detail=False,
        methods=["get"],
        url_path="review-queue",
        permission_classes=[CanReviewDocuments],
    )
    def review_queue(self, request):
        pages = DocumentPage.objects.filter(
            review_status=DocumentPage.ReviewStatus.REVIEW_REQUIRED
        ).select_related("document", "document__local_government", "document__fiscal_year")
        pages = pages.order_by("document__title_en", "page_number")[:100]
        return success_response(DocumentPageDetailSerializer(pages, many=True).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"pages/(?P<page_number>[0-9]+)/review",
        permission_classes=[CanReviewDocuments],
    )
    def review_page(self, request, pk=None, page_number=None):
        document = self.get_object()
        page = get_object_or_404(document.pages, page_number=page_number)
        decision = request.data.get("decision")
        if decision not in {
            DocumentPage.ReviewStatus.APPROVED,
            DocumentPage.ReviewStatus.REJECTED,
        }:
            return Response(
                {
                    "data": None,
                    "meta": {},
                    "errors": [
                        {
                            "code": "invalid_review_decision",
                            "field": "decision",
                            "message": "Decision must be approved or rejected.",
                        }
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        before = {"review_status": page.review_status}
        page.review_status = decision
        page.save(update_fields=["review_status", "updated_at"])
        remaining = document.pages.filter(
            review_status__in=[
                DocumentPage.ReviewStatus.PENDING,
                DocumentPage.ReviewStatus.REVIEW_REQUIRED,
            ]
        ).exists()
        if not remaining:
            document.processing_status = SourceDocument.ProcessingStatus.APPROVED
            document.save(update_fields=["processing_status", "updated_at"])
        record_audit(
            actor=request.user,
            action="document_page_reviewed",
            object_type="DocumentPage",
            object_id=page.pk,
            before=before,
            after={"review_status": decision},
            request_identifier=request.headers.get("X-Request-ID", ""),
        )
        return success_response(DocumentPageDetailSerializer(page).data)
