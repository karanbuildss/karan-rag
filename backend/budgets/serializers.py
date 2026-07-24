from rest_framework import serializers

from budgets.models import BudgetAllocation, FiscalYear, Sector, SubSector


class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = ["id", "code", "year_bs", "year_ad", "label_np"]


class SubSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = ["id", "code", "name_en", "name_np"]


class SectorSerializer(serializers.ModelSerializer):
    subsectors = SubSectorSerializer(many=True, read_only=True)

    class Meta:
        model = Sector
        fields = ["id", "code", "name_en", "name_np", "subsectors"]


class BudgetAllocationSerializer(serializers.ModelSerializer):
    local_government_code = serializers.CharField(source="local_government.code", read_only=True)
    local_government_name_en = serializers.CharField(
        source="local_government.name_en", read_only=True
    )
    local_government_name_np = serializers.CharField(
        source="local_government.name_np", read_only=True
    )
    fiscal_year_code = serializers.CharField(source="fiscal_year.code", read_only=True)
    sector_code = serializers.CharField(source="subsector.sector.code", read_only=True)
    sector_name_en = serializers.CharField(source="subsector.sector.name_en", read_only=True)
    sector_name_np = serializers.CharField(source="subsector.sector.name_np", read_only=True)
    subsector_code = serializers.CharField(source="subsector.code", read_only=True)
    subsector_name_en = serializers.CharField(source="subsector.name_en", read_only=True)
    subsector_name_np = serializers.CharField(source="subsector.name_np", read_only=True)

    class Meta:
        model = BudgetAllocation
        fields = [
            "id",
            "local_government_code",
            "local_government_name_en",
            "local_government_name_np",
            "fiscal_year_code",
            "sector_code",
            "sector_name_en",
            "sector_name_np",
            "subsector_code",
            "subsector_name_en",
            "subsector_name_np",
            "budget_type",
            "allocated_amount",
            "spent_amount",
            "data_classification",
            "source_url",
            "source_document",
            "source_page",
            "review_status",
            "reliability",
            "comparability",
            "source_scope_en",
            "source_scope_np",
        ]


class BudgetComparisonCitationSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    document_title = serializers.CharField()
    document_title_np = serializers.CharField(allow_blank=True)
    page = serializers.IntegerField(min_value=1)
    section = serializers.CharField()
    source_url = serializers.URLField()


class BudgetComparisonRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    local_government_code = serializers.CharField()
    local_government_name_en = serializers.CharField()
    local_government_name_np = serializers.CharField()
    sector_code = serializers.CharField()
    sector_name_en = serializers.CharField()
    sector_name_np = serializers.CharField()
    allocated_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    spent_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    utilization_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        allow_null=True,
    )
    review_status = serializers.CharField()
    reliability = serializers.CharField()
    comparability = serializers.CharField()
    source_scope_en = serializers.CharField()
    source_scope_np = serializers.CharField()
    data_classification = serializers.CharField()
    citation = BudgetComparisonCitationSerializer()


class BudgetComparisonEvidenceSummarySerializer(serializers.Serializer):
    record_count = serializers.IntegerField()
    municipality_count = serializers.IntegerField()
    sector_count = serializers.IntegerField()
    reviewed_only = serializers.BooleanField()
    note_en = serializers.CharField()
    note_np = serializers.CharField()


class BudgetComparisonResponseSerializer(serializers.Serializer):
    fiscal_year = FiscalYearSerializer(allow_null=True)
    currency = serializers.CharField()
    records = BudgetComparisonRowSerializer(many=True)
    evidence_summary = BudgetComparisonEvidenceSummarySerializer()
