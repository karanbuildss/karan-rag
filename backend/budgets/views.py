from config.api import EnvelopeReadOnlyModelViewSet, success_response
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from budgets.models import BudgetAllocation, FiscalYear, Sector
from budgets.selectors import get_reviewed_budget_comparison
from budgets.serializers import (
    BudgetAllocationSerializer,
    BudgetComparisonResponseSerializer,
    FiscalYearSerializer,
    SectorSerializer,
)


class FiscalYearViewSet(EnvelopeReadOnlyModelViewSet):
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer
    permission_classes = [AllowAny]
    filterset_fields = {"code": ["exact"], "year_bs": ["exact"], "year_ad": ["exact"]}
    ordering_fields = ["code"]
    ordering = ["-code"]


class SectorViewSet(EnvelopeReadOnlyModelViewSet):
    serializer_class = SectorSerializer
    permission_classes = [AllowAny]
    filterset_fields = {"code": ["exact"]}
    search_fields = ["code", "name_en", "name_np", "subsectors__name_en", "subsectors__name_np"]
    ordering_fields = ["code", "name_en"]
    ordering = ["name_en"]

    def get_queryset(self):
        return Sector.objects.prefetch_related("subsectors")


class BudgetAllocationViewSet(EnvelopeReadOnlyModelViewSet):
    serializer_class = BudgetAllocationSerializer
    permission_classes = [AllowAny]
    filterset_fields = {
        "local_government__code": ["exact"],
        "fiscal_year__code": ["exact"],
        "subsector__sector__code": ["exact"],
        "subsector__code": ["exact"],
        "budget_type": ["exact"],
        "data_classification": ["exact"],
    }
    search_fields = [
        "local_government__name_en",
        "local_government__name_np",
        "subsector__name_en",
        "subsector__name_np",
    ]
    ordering_fields = ["allocated_amount", "spent_amount", "fiscal_year__code"]
    ordering = ["local_government__name_en", "-fiscal_year__code"]

    def get_queryset(self):
        return BudgetAllocation.objects.select_related(
            "local_government",
            "fiscal_year",
            "subsector__sector",
            "source_document",
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("fiscal_year", str, description="Fiscal-year code, e.g. 2081-82"),
            OpenApiParameter("sector", str, description="Optional broad sector code"),
            OpenApiParameter(
                "municipality",
                str,
                description="Optional comma-separated local-government codes",
            ),
        ],
        responses=BudgetComparisonResponseSerializer,
    )
    @action(detail=False, methods=["get"], url_path="comparison")
    def comparison(self, request):
        municipalities = [
            code.strip()
            for code in request.query_params.get("municipality", "").split(",")
            if code.strip()
        ]
        payload = get_reviewed_budget_comparison(
            fiscal_year_code=request.query_params.get("fiscal_year", "").strip(),
            sector_code=request.query_params.get("sector", "").strip(),
            municipalities=municipalities,
        )
        serializer = BudgetComparisonResponseSerializer(payload)
        return success_response(serializer.data)
