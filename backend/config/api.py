from rest_framework import mixins, status, viewsets
from rest_framework.response import Response


def success_response(data, *, meta=None, status_code=status.HTTP_200_OK):
    return Response(
        {"data": data, "meta": meta or {}, "errors": []},
        status=status_code,
    )


class EnvelopeReadOnlyModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only viewset with one stable response envelope."""

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(serializer.data)
