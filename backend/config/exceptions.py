"""Stable API error envelopes shared by all Django apps."""

from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Wrap DRF errors without exposing internal exception details."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = response.data
    errors = []

    if isinstance(details, dict):
        for field, messages in details.items():
            message_list = messages if isinstance(messages, list) else [messages]
            for message in message_list:
                code = getattr(message, "code", "invalid")
                errors.append({"code": str(code), "field": field, "message": str(message)})
    elif isinstance(details, list):
        for message in details:
            code = getattr(message, "code", "invalid")
            errors.append({"code": str(code), "field": None, "message": str(message)})
    else:
        errors.append({"code": "error", "field": None, "message": str(details)})

    response.data = {"data": None, "meta": {}, "errors": errors}
    return response
