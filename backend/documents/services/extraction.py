import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import pymupdf
import pytesseract
from django.conf import settings
from django.utils import timezone
from pdf2image import convert_from_path
from PIL import Image
from pytesseract import Output

from documents.models import DataExtractionRecord, DocumentPage, SourceDocument


class DocumentExtractionError(RuntimeError):
    """A document could not be extracted while its original remained preserved."""


@dataclass(frozen=True)
class TextQualityAssessment:
    normalized_text: str
    score: float
    usable: bool
    warnings: tuple[str, ...]


def _normalize_text(text):
    text = unicodedata.normalize("NFC", text or "")
    text = "".join(
        character
        for character in text
        if character in {"\n", "\t"} or unicodedata.category(character) != "Cc"
    )
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def assess_text_quality(text, *, language, min_chars=None, min_score=None):
    """Score whether a PDF text layer is reliable enough to avoid OCR."""
    min_chars = min_chars if min_chars is not None else settings.OCR_MIN_TEXT_CHARS
    min_score = min_score if min_score is not None else settings.OCR_MIN_QUALITY_SCORE
    normalized = _normalize_text(text)
    compact = re.sub(r"\s+", "", normalized)
    warnings = []

    if len(compact) < min_chars:
        warnings.append("insufficient_embedded_text")

    if not compact:
        return TextQualityAssessment(normalized, 0.0, False, tuple(warnings))

    score = 1.0
    replacement_ratio = (compact.count("�") + compact.count("\ufffd")) / len(compact)
    if replacement_ratio:
        score -= min(0.75, replacement_ratio * 12)
        warnings.append("replacement_characters_detected")

    letters = [character for character in compact if character.isalpha()]
    devanagari_letters = sum("\u0900" <= character <= "\u097f" for character in letters)
    latin_letters = sum("a" <= character.lower() <= "z" for character in letters)
    devanagari_ratio = devanagari_letters / max(1, len(letters))

    suspicious_symbols = sum(character in "{}[]\\/|~^" for character in compact)
    suspicious_ratio = suspicious_symbols / len(compact)
    nepali_first = language == SourceDocument.Language.NEPALI
    if nepali_first and latin_letters >= 40 and devanagari_ratio < 0.15:
        score -= 0.6
        warnings.append("legacy_nepali_font_suspected")
    elif suspicious_ratio > 0.025:
        score -= min(0.35, suspicious_ratio * 4)
        warnings.append("unusual_symbol_density")

    tokens = re.findall(r"\S+", normalized)
    if len(tokens) >= 30:
        single_character_ratio = sum(len(token) == 1 for token in tokens) / len(tokens)
        if single_character_ratio > 0.45:
            score -= 0.35
            warnings.append("fragmented_character_spacing")

    repeated_pairs = len(re.findall(r"([^\W\d_])\1", compact, flags=re.UNICODE))
    if repeated_pairs / max(1, len(letters)) > 0.08:
        score -= 0.25
        warnings.append("duplicated_glyphs_suspected")

    score = round(max(0.0, min(1.0, score)), 4)
    usable = len(compact) >= min_chars and score >= min_score
    return TextQualityAssessment(normalized, score, usable, tuple(dict.fromkeys(warnings)))


@lru_cache(maxsize=1)
def _validate_tesseract_runtime():
    if settings.TESSERACT_CMD:
        command_path = Path(settings.TESSERACT_CMD)
        if not command_path.exists():
            raise DocumentExtractionError(
                "Tesseract is configured but the executable path does not exist."
            )
        pytesseract.pytesseract.tesseract_cmd = str(command_path)

    try:
        installed = set(pytesseract.get_languages(config=""))
    except pytesseract.TesseractNotFoundError as exc:
        raise DocumentExtractionError("Tesseract OCR is not available.") from exc

    required = {item.strip() for item in settings.OCR_LANGUAGES.split("+") if item.strip()}
    missing = sorted(required - installed)
    if missing:
        raise DocumentExtractionError(
            f"Tesseract is missing required language data: {', '.join(missing)}."
        )


def _image_from_page(page, *, pdf_path=None, page_number=None):
    scale = settings.OCR_DPI / 72
    try:
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale),
            colorspace=pymupdf.csRGB,
            alpha=False,
        )
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    except Exception as primary_error:
        if not pdf_path or not page_number:
            raise
        images = convert_from_path(
            pdf_path,
            dpi=settings.OCR_DPI,
            first_page=page_number,
            last_page=page_number,
            poppler_path=settings.POPPLER_PATH or None,
            thread_count=1,
        )
        if not images:
            raise DocumentExtractionError(
                "Poppler did not render the requested PDF page."
            ) from primary_error
        return images[0].convert("RGB")


def _ocr_page(page, *, pdf_path=None, page_number=None):
    _validate_tesseract_runtime()
    image = _image_from_page(page, pdf_path=pdf_path, page_number=page_number)
    data = pytesseract.image_to_data(
        image,
        lang=settings.OCR_LANGUAGES,
        config="--oem 1 --psm 3",
        output_type=Output.DICT,
    )

    lines = defaultdict(list)
    weighted_confidence = 0.0
    confidence_weight = 0
    for index, raw_word in enumerate(data.get("text", [])):
        word = raw_word.strip()
        if not word:
            continue
        key = (
            data["block_num"][index],
            data["par_num"][index],
            data["line_num"][index],
        )
        lines[key].append(word)
        try:
            confidence = float(data["conf"][index])
        except (TypeError, ValueError):
            confidence = -1
        if confidence >= 0 and math.isfinite(confidence):
            weight = max(1, len(word))
            weighted_confidence += confidence * weight
            confidence_weight += weight

    text = "\n".join(" ".join(words) for words in lines.values())
    confidence = weighted_confidence / confidence_weight if confidence_weight else None
    return _normalize_text(text), confidence


def _save_page(document, page_number, *, text, method, quality, confidence, warnings):
    review_status = (
        DocumentPage.ReviewStatus.AUTO_ACCEPTED
        if method == DocumentPage.ExtractionMethod.EMBEDDED_TEXT and quality.usable
        else DocumentPage.ReviewStatus.REVIEW_REQUIRED
    )
    DocumentPage.objects.update_or_create(
        document=document,
        page_number=page_number,
        defaults={
            "extracted_text": text,
            "extraction_method": method,
            "text_quality_score": Decimal(str(quality.score)),
            "ocr_confidence": (
                Decimal(str(round(confidence, 2))) if confidence is not None else None
            ),
            "review_status": review_status,
            "extraction_warnings": list(dict.fromkeys(warnings)),
            "character_count": len(text),
        },
    )


def extract_document(document_id, *, force=False, max_pages=None):
    """Extract one PDF page-by-page, using OCR only when its text layer fails quality checks."""
    document = SourceDocument.objects.get(pk=document_id)
    if not document.original_file:
        raise DocumentExtractionError("The original PDF is not available for extraction.")
    if document.processing_status == SourceDocument.ProcessingStatus.APPROVED and not force:
        return document

    document.processing_status = SourceDocument.ProcessingStatus.EXTRACTING
    document.extraction_error = ""
    document.save(update_fields=["processing_status", "extraction_error", "updated_at"])
    extractor_version = f"PyMuPDF {getattr(pymupdf, 'VersionBind', 'unknown')}"
    record = DataExtractionRecord.objects.create(
        document=document,
        status=DataExtractionRecord.Status.RUNNING,
        extractor_version=extractor_version,
        ocr_languages=settings.OCR_LANGUAGES,
    )

    embedded_pages = 0
    ocr_pages = 0
    failed_pages = 0
    review_required = False
    processed_pages = 0

    try:
        with pymupdf.open(document.original_file.path) as pdf:
            total_pages = len(pdf)
            pages_to_process = total_pages if max_pages is None else min(total_pages, max_pages)
            document.page_count = total_pages
            document.pages.filter(page_number__gt=total_pages).delete()

            for page_index in range(pages_to_process):
                page = pdf[page_index]
                page_number = page_index + 1
                processed_pages += 1
                embedded_quality = assess_text_quality(
                    page.get_text("text"),
                    language=document.language,
                )

                if embedded_quality.usable:
                    _save_page(
                        document,
                        page_number,
                        text=embedded_quality.normalized_text,
                        method=DocumentPage.ExtractionMethod.EMBEDDED_TEXT,
                        quality=embedded_quality,
                        confidence=None,
                        warnings=embedded_quality.warnings,
                    )
                    embedded_pages += 1
                    continue

                try:
                    ocr_text, confidence = _ocr_page(
                        page,
                        pdf_path=document.original_file.path,
                        page_number=page_number,
                    )
                    ocr_quality = assess_text_quality(
                        ocr_text,
                        language=document.language,
                        min_chars=1,
                    )
                    warnings = [*embedded_quality.warnings, "ocr_fallback_used"]
                    if confidence is None or confidence < 70:
                        warnings.append("low_ocr_confidence")
                    if not ocr_text:
                        warnings.append("ocr_returned_no_text")
                    _save_page(
                        document,
                        page_number,
                        text=ocr_text,
                        method=(
                            DocumentPage.ExtractionMethod.OCR
                            if ocr_text
                            else DocumentPage.ExtractionMethod.NONE
                        ),
                        quality=ocr_quality,
                        confidence=confidence,
                        warnings=warnings,
                    )
                    ocr_pages += 1
                    review_required = True
                except (DocumentExtractionError, pytesseract.TesseractError) as exc:
                    fallback_text = embedded_quality.normalized_text
                    method = (
                        DocumentPage.ExtractionMethod.EMBEDDED_TEXT
                        if fallback_text
                        else DocumentPage.ExtractionMethod.NONE
                    )
                    _save_page(
                        document,
                        page_number,
                        text=fallback_text,
                        method=method,
                        quality=embedded_quality,
                        confidence=None,
                        warnings=[*embedded_quality.warnings, f"ocr_failed:{type(exc).__name__}"],
                    )
                    failed_pages += 1
                    review_required = True

        partial = processed_pages < document.page_count
        if partial:
            review_required = True
        if failed_pages == processed_pages and processed_pages:
            final_status = SourceDocument.ProcessingStatus.FAILED
            record_status = DataExtractionRecord.Status.FAILED
        elif review_required:
            final_status = SourceDocument.ProcessingStatus.NEEDS_REVIEW
            record_status = DataExtractionRecord.Status.NEEDS_REVIEW
        else:
            final_status = SourceDocument.ProcessingStatus.EXTRACTED
            record_status = DataExtractionRecord.Status.COMPLETED

        now = timezone.now()
        document.processing_status = final_status
        document.extracted_at = now
        document.save(
            update_fields=["processing_status", "page_count", "extracted_at", "updated_at"]
        )
        record.status = record_status
        record.total_pages = document.page_count
        record.embedded_text_pages = embedded_pages
        record.ocr_pages = ocr_pages
        record.failed_pages = failed_pages
        record.details = {
            "processed_pages": processed_pages,
            "partial_extraction": partial,
            "quality_threshold": settings.OCR_MIN_QUALITY_SCORE,
            "minimum_text_characters": settings.OCR_MIN_TEXT_CHARS,
        }
        record.completed_at = now
        record.save()
        return document
    except Exception as exc:
        now = timezone.now()
        safe_message = f"{type(exc).__name__}: {str(exc)[:420]}"
        document.processing_status = SourceDocument.ProcessingStatus.FAILED
        document.extraction_error = safe_message
        document.save(update_fields=["processing_status", "extraction_error", "updated_at"])
        record.status = DataExtractionRecord.Status.FAILED
        record.error_message = safe_message
        record.total_pages = document.page_count
        record.embedded_text_pages = embedded_pages
        record.ocr_pages = ocr_pages
        record.failed_pages = failed_pages
        record.completed_at = now
        record.save()
        if isinstance(exc, DocumentExtractionError):
            raise
        raise DocumentExtractionError(
            "Document extraction failed; the original was preserved."
        ) from exc
