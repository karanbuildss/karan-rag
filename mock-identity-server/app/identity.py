import hmac
import json
import secrets
import threading
import time
import uuid

import jwt
from django.conf import settings

_lock = threading.Lock()
_challenges = {}
_codes = {}


def _now():
    return int(time.time())


def _identities():
    return json.loads(settings.SEEDED_IDENTITIES_PATH.read_text(encoding="utf-8"))


def start_verification(phone, citizenship_number):
    identity = next(
        (
            item
            for item in _identities()
            if hmac.compare_digest(item["phone"], phone)
            and hmac.compare_digest(item["citizenship_number"], citizenship_number)
        ),
        None,
    )
    if identity is None:
        return None
    challenge_id = secrets.token_urlsafe(24)
    with _lock:
        _challenges[challenge_id] = {
            "identity": identity,
            "expires": _now() + settings.IDENTITY_CHALLENGE_SECONDS,
        }
    return challenge_id


def confirm_verification(challenge_id, otp):
    with _lock:
        challenge = _challenges.pop(challenge_id, None)
        if (
            challenge is None
            or challenge["expires"] < _now()
            or not hmac.compare_digest(settings.DEMO_OTP, otp)
        ):
            return None
        code = secrets.token_urlsafe(32)
        _codes[code] = {
            "identity": challenge["identity"],
            "expires": _now() + settings.IDENTITY_CODE_SECONDS,
        }
    return code


def exchange_code(code):
    with _lock:
        record = _codes.pop(code, None)
    if record is None or record["expires"] < _now():
        return None
    identity = record["identity"]
    now = _now()
    claims = {
        "iss": settings.IDENTITY_ISSUER,
        "aud": settings.IDENTITY_AUDIENCE,
        "sub": identity["subject"],
        "jti": str(uuid.uuid4()),
        "phone_verified": True,
        "citizenship_verified": True,
        "municipality_code": identity["municipality_code"],
        "ward_number": identity["ward_number"],
        "iat": now,
        "exp": now + settings.IDENTITY_ASSERTION_SECONDS,
    }
    private_key = settings.IDENTITY_PRIVATE_KEY_PATH.read_text(encoding="utf-8")
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": settings.IDENTITY_KEY_ID},
    )


def public_jwk():
    from cryptography.hazmat.primitives import serialization

    private_key = serialization.load_pem_private_key(
        settings.IDENTITY_PRIVATE_KEY_PATH.read_bytes(),
        password=None,
    )
    public_key = private_key.public_key()
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    return {**jwk, "kid": settings.IDENTITY_KEY_ID, "use": "sig", "alg": "RS256"}
