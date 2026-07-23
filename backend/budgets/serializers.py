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
        ]
