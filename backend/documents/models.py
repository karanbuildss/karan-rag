import uuid
from pathlib import Path

from budgets.models import FiscalYear
from config.models import DataClassification
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from geography.models import LocalGovernment
from projects.models import Project


def document_upload_path(instance, filename):
    safe_name = Path(filename).name
    return f"documents/originals/{instance.id}/{safe_name}"


class SourceDocument(models.Model):
    class FileFormat(models.TextChoices):
        PDF = "pdf", "PDF"
        IMAGE = "image", "Image"

    class DocumentType(models.TextChoices):
        BUDGET_BOOK = "budget_book", "Budget book / red book"
        BUDGET_SPEECH = "budget_speech", "Budget speech"
        ANNUAL_PROGRAM = "annual_program", "Annual policy or program"
        ECONOMIC_ACT = "economic_act", "Economic act or bill"
        PROGRESS_REPORT = "progress_report", "Progress report"
        EXPENDITURE_REPORT = "expenditure_report", "Expenditure report"
        PROCUREMENT_NOTICE = "procurement_notice", "Procurement notice"
        CONTRACT_AWARD = "contract_award", "Contract award"
        PAYMENT_RECORD = "payment_record", "Payment record"
        AUDIT_REPORT = "audit_report", "Audit report"
        OTHER = "other", "Other"

    class Language(models.TextChoices):
        NEPALI = "nep", "Nepali"
        ENGLISH = "eng", "English"
        MIXED = "nep+eng", "Nepali and English"

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        EXTRACTING = "extracting", "Extracting"
        EXTRACTED = "extracted", "Extracted"
        NEEDS_REVIEW = "needs_review", "Needs review"
        APPROVED = "approved", "Approved"
        FAILED = "failed", "Failed"

    class SourceUrlKind(models.TextChoices):
        DIRECT_PDF = "direct_pdf", "Direct PDF"
        LANDING_PAGE = "landing_page", "Official landing page"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_en = models.CharField(max_length=300)
    title_np = models.CharField(max_length=300, blank=True)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    local_government = models.ForeignKey(
        LocalGovernment,
        on_delete=models.PROTECT,
        related_name="source_documents",
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.PROTECT,
        related_name="source_documents",
    )
    language = models.CharField(max_length=10, choices=Language.choices)
    file_format = models.CharField(
        max_length=10,
        choices=FileFormat.choices,
        default=FileFormat.PDF,
    )
    original_file = models.FileField(upload_to=document_upload_path, blank=True)
    original_filename = models.CharField(max_length=260)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    source_url = models.URLField(max_length=1000)
    source_url_kind = models.CharField(
        max_length=20,
        choices=SourceUrlKind.choices,
        default=SourceUrlKind.DIRECT_PDF,
    )
    source_note = models.CharField(max_length=500, blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.OFFICIAL,
    )
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    page_count = models.PositiveIntegerField(default=0)
    extraction_error = models.CharField(max_length=500, blank=True)
    extracted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fiscal_year__code", "local_government__name_en", "title_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["sha256"],
                condition=~models.Q(sha256=""),
                name="unique_nonempty_document_sha256",
            )
        ]
        indexes = [
            models.Index(fields=["local_government", "fiscal_year", "document_type"]),
            models.Index(fields=["processing_status", "document_type"]),
        ]

    def __str__(self):
        return self.title_en


class DocumentPage(models.Model):
    class ExtractionMethod(models.TextChoices):
        EMBEDDED_TEXT = "embedded_text", "Embedded text"
        OCR = "ocr", "Optical character recognition"
        NONE = "none", "No usable text"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        AUTO_ACCEPTED = "auto_accepted", "Auto-accepted"
        REVIEW_REQUIRED = "review_required", "Review required"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    document = models.ForeignKey(SourceDocument, on_delete=models.CASCADE, related_name="pages")
    page_number = models.PositiveIntegerField()
    section = models.CharField(max_length=240, blank=True)
    extracted_text = models.TextField(blank=True)
    extraction_method = models.CharField(
        max_length=20,
        choices=ExtractionMethod.choices,
        default=ExtractionMethod.NONE,
    )
    text_quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    ocr_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    extraction_warnings = models.JSONField(default=list, blank=True)
    character_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "page_number"],
                name="unique_page_number_per_document",
            ),
            models.CheckConstraint(
                condition=models.Q(page_number__gte=1),
                name="document_page_number_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(text_quality_score__gte=0, text_quality_score__lte=1),
                name="document_page_quality_between_0_and_1",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(ocr_confidence__isnull=True)
                    | models.Q(ocr_confidence__gte=0, ocr_confidence__lte=100)
                ),
                name="document_page_ocr_confidence_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["document", "review_status"]),
            models.Index(fields=["extraction_method", "review_status"]),
        ]

    def __str__(self):
        return f"{self.document} · page {self.page_number}"


class DataExtractionRecord(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        NEEDS_REVIEW = "needs_review", "Needs review"
        FAILED = "failed", "Failed"

    document = models.ForeignKey(
        SourceDocument,
        on_delete=models.CASCADE,
        related_name="extraction_records",
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    extractor_version = models.CharField(max_length=100)
    ocr_languages = models.CharField(max_length=40, blank=True)
    total_pages = models.PositiveIntegerField(default=0)
    embedded_text_pages = models.PositiveIntegerField(default=0)
    ocr_pages = models.PositiveIntegerField(default=0)
    failed_pages = models.PositiveIntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.document} · {self.started_at:%Y-%m-%d %H:%M}"


class DocumentChunk(models.Model):
    page = models.ForeignKey(DocumentPage, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    section = models.CharField(max_length=240, blank=True)
    token_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    vector_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["page__page_number", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "chunk_index"],
                name="unique_chunk_index_per_page",
            )
        ]

    def __str__(self):
        return f"{self.page} · chunk {self.chunk_index}"


class ProjectDocumentLink(models.Model):
    class Relationship(models.TextChoices):
        CONTEXT = "context", "Municipal context"
        ALLOCATION = "allocation", "Budget allocation"
        AUDIT = "audit", "Official audit finding"
        PROCUREMENT = "procurement", "Procurement"
        PAYMENT = "payment", "Payment"
        PROGRESS = "progress", "Progress"
        COMPLETION = "completion", "Completion"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="document_links")
    document = models.ForeignKey(
        SourceDocument,
        on_delete=models.CASCADE,
        related_name="project_links",
    )
    relationship = models.CharField(max_length=20, choices=Relationship.choices)
    page_from = models.PositiveIntegerField(null=True, blank=True)
    page_to = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(max_length=240, blank=True)
    evidence_note_en = models.CharField(max_length=500)
    evidence_note_np = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["relationship", "document__title_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "document", "relationship"],
                name="unique_project_document_relationship",
            ),
            models.CheckConstraint(
                condition=models.Q(page_from__isnull=True) | models.Q(page_from__gte=1),
                name="project_document_page_from_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(page_to__isnull=True) | models.Q(page_to__gte=1),
                name="project_document_page_to_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(page_from__isnull=True)
                    | models.Q(page_to__isnull=True)
                    | models.Q(page_to__gte=models.F("page_from"))
                ),
                name="project_document_page_range_valid",
            ),
        ]

    def __str__(self):
        return f"{self.project} · {self.document}"
