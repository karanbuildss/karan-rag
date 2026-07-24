"""Generate ignored local secrets and mock identity RSA keys without printing them."""

import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = ROOT / "backend" / ".env"
MOCK_ROOT = ROOT / "mock-identity-server"
MOCK_ENV = MOCK_ROOT / ".env"
KEY_DIR = MOCK_ROOT / "keys"


def read_env(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def set_values(path, values, *, template=None):
    lines = read_env(path)
    if not lines and template and template.exists():
        lines = read_env(template)
    seen = set()
    output = []
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            output.append(line)
            continue
        key = line.split("=", 1)[0]
        if key in values:
            output.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in values.items():
        if key not in seen:
            output.append(f"{key}={value}")
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def existing_value(path, key):
    for line in read_env(path):
        if line.startswith(f"{key}="):
            value = line.split("=", 1)[1].strip()
            if value and "replace-with" not in value:
                return value
    return ""


def main():
    citizen_secret = existing_value(BACKEND_ENV, "CITIZEN_HASH_SECRET") or secrets.token_urlsafe(48)
    client_secret = existing_value(
        BACKEND_ENV,
        "MOCK_IDENTITY_CLIENT_SECRET",
    ) or secrets.token_urlsafe(48)
    mock_django_secret = existing_value(MOCK_ENV, "DJANGO_SECRET_KEY") or secrets.token_urlsafe(48)

    set_values(
        BACKEND_ENV,
        {
            "CITIZEN_HASH_SECRET": citizen_secret,
            "MOCK_IDENTITY_CLIENT_SECRET": client_secret,
            "MOCK_IDENTITY_PUBLIC_KEY_PATH": "../mock-identity-server/keys/public.pem",
        },
    )
    set_values(
        MOCK_ENV,
        {
            "DJANGO_SECRET_KEY": mock_django_secret,
            "IDENTITY_CLIENT_SECRET": client_secret,
        },
        template=MOCK_ROOT / ".env.example",
    )

    KEY_DIR.mkdir(parents=True, exist_ok=True)
    private_path = KEY_DIR / "private.pem"
    public_path = KEY_DIR / "public.pem"
    if not private_path.exists() or not public_path.exists():
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        private_path.write_bytes(
            private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        public_path.write_bytes(
            private_key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    print("Local security material is ready in ignored environment and key files.")


if __name__ == "__main__":
    main()
