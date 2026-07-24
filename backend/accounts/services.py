import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from audit.services import record_audit
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from accounts.models import CitizenProfile, VerificationRecord


class IdentityServiceUnavailable(APIException):
    status_code = 503
    default_code = "identity_service_unavailable"
    default_detail = "The mock identity service is temporarily unavailable."


def _exchange_code(code):
    payload = json.dumps({"code": code}).encode("utf-8")
    request = Request(
        f"{settings.MOCK_IDENTITY_SERVER_URL.rstrip('/')}/api/v1/verification/exchange/",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Client-Secret": settings.MOCK_IDENTITY_CLIENT_SECRET,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.MOCK_IDENTITY_TIMEOUT_SECONDS) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            assertion = response_data.get("data", {}).get("assertion")
            if not assertion:
                raise ValueError("The identity exchange response did not contain an assertion.")
            return assertion
    except HTTPError as exc:
        if exc.code in {400, 401, 404, 409}:
            raise ValidationError(
                {"code": "invalid_verification_code"},
                code="invalid_verification_code",
            ) from exc
        raise IdentityServiceUnavailable() from exc
    except (URLError, TimeoutError, KeyError, ValueError) as exc:
        raise IdentityServiceUnavailable() from exc


def _public_key():
    path = Path(settings.MOCK_IDENTITY_PUBLIC_KEY_PATH)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise IdentityServiceUnavailable("The mock identity public key is unavailable.") from exc


def _citizen_key(issuer, subject):
    material = f"{issuer}:{subject}".encode()
    return hmac.new(
        settings.CITIZEN_HASH_SECRET.encode(),
        material,
        hashlib.sha256,
    ).hexdigest()


def complete_verification(*, user, code, request_identifier=""):
    assertion = _exchange_code(code)
    try:
        claims = jwt.decode(
            assertion,
            _public_key(),
            algorithms=["RS256"],
            audience=settings.MOCK_IDENTITY_AUDIENCE,
            issuer=settings.MOCK_IDENTITY_ISSUER,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise ValidationError(
            {"code": "invalid_identity_assertion"},
            code="invalid_identity_assertion",
        ) from exc

    if not claims.get("phone_verified") or not claims.get("citizenship_verified"):
        raise ValidationError(
            {"code": "identity_not_verified"},
            code="identity_not_verified",
        )

    citizen_key = _citizen_key(claims["iss"], claims["sub"])
    jti_hash = hashlib.sha256(claims["jti"].encode()).hexdigest()
    expires_at = datetime.fromtimestamp(claims["exp"], tz=UTC)

    try:
        with transaction.atomic():
            profile, _ = CitizenProfile.objects.select_for_update().get_or_create(user=user)
            if profile.citizen_key and profile.citizen_key != citizen_key:
                raise ValidationError(
                    {"code": "account_already_verified"},
                    code="account_already_verified",
                )
            profile.citizen_key = citizen_key
            if profile.role == CitizenProfile.Role.CITIZEN:
                profile.role = CitizenProfile.Role.VERIFIED_CITIZEN
            profile.verified_municipality_code = claims.get("municipality_code", "")
            profile.verified_ward_number = claims.get("ward_number")
            profile.verified_at = timezone.now()
            profile.save()
            VerificationRecord.objects.create(
                profile=profile,
                issuer=claims["iss"],
                subject_key=citizen_key,
                token_identifier_hash=jti_hash,
                status=VerificationRecord.Status.VERIFIED,
                expires_at=expires_at,
            )
            record_audit(
                actor=user,
                action="identity_verified",
                object_type="CitizenProfile",
                object_id=profile.pk,
                after={"role": profile.role, "municipality": profile.verified_municipality_code},
                request_identifier=request_identifier,
            )
    except IntegrityError as exc:
        raise ValidationError(
            {"code": "identity_already_linked"},
            code="identity_already_linked",
        ) from exc
    return profile
