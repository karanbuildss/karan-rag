"""Small platform-level views that do not belong to a product domain app."""

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Report process health without exposing environment or secret information."""
    return JsonResponse(
        {
            "data": {"service": "budget-darpan-api", "status": "ok"},
            "meta": {},
            "errors": [],
        }
    )
