"""Environment-driven Django settings for Budget Darpan."""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    """Read a strict, human-friendly boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated environment variable without empty entries."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = env_bool("BUDGET_DARPAN_DEBUG", default=False)
SECRET_KEY = os.getenv("SECRET_KEY", "")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-budget-darpan-local-development-only"
    else:
        raise RuntimeError("SECRET_KEY must be set when DEBUG is false.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000").rstrip("/")

INSTALLED_APPS = [
    "config",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "geography",
    "budgets",
    "projects",
    "procurement",
    "payments",
    "documents",
    "rag",
    "investigator",
    "audit",
    "accounts",
    "feedback",
    "anomalies",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

database_url = os.getenv("DATABASE_URL", "").strip()
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(database_url, conn_max_age=60, conn_health_checks=True)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "14400"))
SESSION_SAVE_EVERY_REQUEST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.EnvelopePageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {"investigator": "30/hour"},
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Budget Darpan API",
    "DESCRIPTION": (
        "Evidence-led APIs for Nepal local-government budgets, projects, and civic feedback."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "BudgetAllocationReviewStatusEnum": "budgets.models.BudgetAllocation.ReviewStatus",
        "DocumentPageReviewStatusEnum": "documents.models.DocumentPage.ReviewStatus",
        "SourceDocumentLanguageEnum": "documents.models.SourceDocument.Language",
        "InvestigatorLanguageEnum": ("investigator.serializers.INVESTIGATOR_LANGUAGE_CHOICES"),
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024

OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "nep+eng").strip()
OCR_DPI = int(os.getenv("OCR_DPI", "220"))
OCR_MIN_TEXT_CHARS = int(os.getenv("OCR_MIN_TEXT_CHARS", "80"))
OCR_MIN_QUALITY_SCORE = float(os.getenv("OCR_MIN_QUALITY_SCORE", "0.62"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()
POPPLER_PATH = os.getenv("POPPLER_PATH", "").strip()
EVIDENCE_MANIFEST = Path(
    os.getenv("EVIDENCE_MANIFEST", str(BASE_DIR.parent / "datasets" / "manifest.csv"))
)
VERIFIED_BUDGET_FACTS = Path(
    os.getenv(
        "VERIFIED_BUDGET_FACTS",
        str(BASE_DIR.parent / "datasets" / "verified_budget_facts.csv"),
    )
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:3b").strip()
OLLAMA_EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL",
    "nomic-embed-text-v2-moe",
).strip()
OLLAMA_EMBEDDING_QUERY_PREFIX = os.getenv(
    "OLLAMA_EMBEDDING_QUERY_PREFIX",
    "search_query: ",
)
OLLAMA_EMBEDDING_DOCUMENT_PREFIX = os.getenv(
    "OLLAMA_EMBEDDING_DOCUMENT_PREFIX",
    "search_document: ",
)
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))
INVESTIGATOR_ENABLE_GENERATION = env_bool("INVESTIGATOR_ENABLE_GENERATION", default=True)
INVESTIGATOR_TOP_K = int(os.getenv("INVESTIGATOR_TOP_K", "5"))
RAG_CHUNK_TOKENS = int(os.getenv("RAG_CHUNK_TOKENS", "320"))
RAG_CHUNK_OVERLAP_TOKENS = int(os.getenv("RAG_CHUNK_OVERLAP_TOKENS", "50"))

VECTOR_DB_PROVIDER = os.getenv("VECTOR_DB_PROVIDER", "chroma").strip()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "").strip()
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "budget-darpan").strip()
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "public-budget-documents").strip()
PINECONE_FALLBACK_TO_CHROMA = env_bool("PINECONE_FALLBACK_TO_CHROMA", default=True)
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "budget-darpan-evidence").strip()
chroma_db_dir = Path(os.getenv("CHROMA_DB_DIR", "../chroma_db"))
CHROMA_DB_DIR = (
    chroma_db_dir if chroma_db_dir.is_absolute() else (BASE_DIR / chroma_db_dir).resolve()
)

MOCK_IDENTITY_SERVER_URL = os.getenv(
    "MOCK_IDENTITY_SERVER_URL",
    "http://localhost:8001",
).strip()
MOCK_IDENTITY_CLIENT_SECRET = os.getenv("MOCK_IDENTITY_CLIENT_SECRET", "").strip()
MOCK_IDENTITY_PUBLIC_KEY = os.getenv("MOCK_IDENTITY_PUBLIC_KEY", "").replace("\\n", "\n").strip()
MOCK_IDENTITY_ISSUER = os.getenv(
    "MOCK_IDENTITY_ISSUER",
    "budget-darpan-mock-id",
).strip()
MOCK_IDENTITY_AUDIENCE = os.getenv(
    "MOCK_IDENTITY_AUDIENCE",
    "budget-darpan-api",
).strip()
MOCK_IDENTITY_TIMEOUT_SECONDS = int(os.getenv("MOCK_IDENTITY_TIMEOUT_SECONDS", "5"))
CITIZEN_HASH_SECRET = os.getenv("CITIZEN_HASH_SECRET", "").strip()
mock_identity_public_key_path = Path(
    os.getenv(
        "MOCK_IDENTITY_PUBLIC_KEY_PATH",
        "../mock-identity-server/keys/public.pem",
    )
)
MOCK_IDENTITY_PUBLIC_KEY_PATH = (
    mock_identity_public_key_path
    if mock_identity_public_key_path.is_absolute()
    else (BASE_DIR / mock_identity_public_key_path).resolve()
)
