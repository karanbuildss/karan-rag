from django.conf import settings


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            from django.http import HttpResponse

            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = settings.CORS_ALLOWED_ORIGIN
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Cache-Control"] = "no-store"
        return response
