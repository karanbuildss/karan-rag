import hmac
import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from app.identity import confirm_verification, exchange_code, public_jwk, start_verification


def _payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _response(data=None, *, errors=None, status=200):
    return JsonResponse({"data": data, "meta": {}, "errors": errors or []}, status=status)


@require_GET
def health(request):
    return _response({"status": "ok", "provider": "mock"})


@require_GET
def jwks(request):
    return JsonResponse({"keys": [public_jwk()]})


@csrf_exempt
@require_POST
def start(request):
    data = _payload(request)
    challenge_id = start_verification(
        str(data.get("phone", "")),
        str(data.get("citizenship_number", "")),
    )
    if challenge_id is None:
        return _response(
            errors=[
                {
                    "code": "identity_not_matched",
                    "message": "The demo identity could not be matched.",
                }
            ],
            status=400,
        )
    result = {"challenge_id": challenge_id, "expires_in": settings.IDENTITY_CHALLENGE_SECONDS}
    if settings.EXPOSE_DEMO_OTP:
        result["demo_otp"] = settings.DEMO_OTP
    return _response(result)


@csrf_exempt
@require_POST
def confirm(request):
    data = _payload(request)
    code = confirm_verification(str(data.get("challenge_id", "")), str(data.get("otp", "")))
    if code is None:
        return _response(
            errors=[
                {
                    "code": "invalid_or_expired_challenge",
                    "message": "The challenge or OTP is invalid or expired.",
                }
            ],
            status=400,
        )
    return _response({"code": code, "expires_in": settings.IDENTITY_CODE_SECONDS})


@csrf_exempt
@require_POST
def exchange(request):
    supplied_secret = request.headers.get("X-Client-Secret", "")
    if not settings.IDENTITY_CLIENT_SECRET or not hmac.compare_digest(
        supplied_secret,
        settings.IDENTITY_CLIENT_SECRET,
    ):
        return _response(errors=[{"code": "invalid_client"}], status=401)
    assertion = exchange_code(str(_payload(request).get("code", "")))
    if assertion is None:
        return _response(errors=[{"code": "invalid_or_used_code"}], status=400)
    return _response({"assertion": assertion})
