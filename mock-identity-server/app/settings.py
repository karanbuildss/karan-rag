import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY is required.")

DEBUG = os.getenv("IDENTITY_DEBUG", "False").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [
    item.strip() for item in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
]
ROOT_URLCONF = "app.urls"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "app.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
INSTALLED_APPS = ["app"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "mock.sqlite3"}}
USE_TZ = True
TIME_ZONE = "Asia/Kathmandu"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", str(not DEBUG)).lower() in {
    "1",
    "true",
    "yes",
}
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

CORS_ALLOWED_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")
IDENTITY_ISSUER = os.getenv("IDENTITY_ISSUER", "budget-darpan-mock-id")
IDENTITY_AUDIENCE = os.getenv("IDENTITY_AUDIENCE", "budget-darpan-api")
IDENTITY_CLIENT_SECRET = os.getenv("IDENTITY_CLIENT_SECRET", "")
IDENTITY_PRIVATE_KEY = os.getenv("IDENTITY_PRIVATE_KEY", "").replace("\\n", "\n").strip()
IDENTITY_KEY_ID = os.getenv("IDENTITY_KEY_ID", "budget-darpan-demo-1")
IDENTITY_ASSERTION_SECONDS = int(os.getenv("IDENTITY_ASSERTION_SECONDS", "300"))
IDENTITY_CODE_SECONDS = int(os.getenv("IDENTITY_CODE_SECONDS", "60"))
IDENTITY_CHALLENGE_SECONDS = int(os.getenv("IDENTITY_CHALLENGE_SECONDS", "300"))
DEMO_OTP = os.getenv("DEMO_OTP", "123456")
EXPOSE_DEMO_OTP = os.getenv("EXPOSE_DEMO_OTP", "True").lower() in {"1", "true", "yes"}


def resolved_path(name, default):
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else (BASE_DIR / value).resolve()


IDENTITY_PRIVATE_KEY_PATH = resolved_path("IDENTITY_PRIVATE_KEY_PATH", "keys/private.pem")
SEEDED_IDENTITIES_PATH = resolved_path(
    "SEEDED_IDENTITIES_PATH",
    "seeded_identities/identities.json",
)

if not IDENTITY_CLIENT_SECRET:
    raise RuntimeError("IDENTITY_CLIENT_SECRET is required.")
if not IDENTITY_PRIVATE_KEY and not IDENTITY_PRIVATE_KEY_PATH.is_file():
    raise RuntimeError(
        "Set IDENTITY_PRIVATE_KEY or point IDENTITY_PRIVATE_KEY_PATH to a readable private key."
    )
if not SEEDED_IDENTITIES_PATH.is_file():
    raise RuntimeError("SEEDED_IDENTITIES_PATH must point to the fictional identity fixture.")
