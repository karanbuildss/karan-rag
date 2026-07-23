from rest_framework import serializers

from projects.models import Project, ProjectLocation


class ProjectLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectLocation
        fields = ["latitude", "longitude", "label_en", "label_np"]


class ProjectSerializer(serializers.ModelSerializer):
    local_government_code = serializers.CharField(source="local_government.code", read_only=True)
    local_government_name_en = serializers.CharField(
        source="local_government.name_en", read_only=True
    )
    local_government_name_np = serializers.CharField(
        source="local_government.name_np", read_only=True
    )
    ward_number = serializers.IntegerField(source="ward.number", read_only=True, allow_null=True)
    fiscal_year_code = serializers.CharField(source="fiscal_year.code", read_only=True)
    sector_name_en = serializers.CharField(source="subsector.sector.name_en", read_only=True)
    sector_name_np = serializers.CharField(source="subsector.sector.name_np", read_only=True)
    subsector_name_en = serializers.CharField(source="subsector.name_en", read_only=True)
    subsector_name_np = serializers.CharField(source="subsector.name_np", read_only=True)
    location = ProjectLocationSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "code",
            "title_en",
            "title_np",
            "description_en",
            "description_np",
            "status",
            "allocated_amount",
            "official_progress_percent",
            "planned_start_date",
            "planned_end_date",
            "data_classification",
            "data_note_en",
            "data_note_np",
            "source_url",
            "local_government_code",
            "local_government_name_en",
            "local_government_name_np",
            "ward_number",
            "fiscal_year_code",
            "sector_name_en",
            "sector_name_np",
            "subsector_name_en",
            "subsector_name_np",
            "location",
        ]


class ProjectMoneyTrailSerializer(serializers.Serializer):
    project = serializers.DictField()
    financial_summary = serializers.DictField()
    procurement = serializers.ListField(child=serializers.DictField())
    payments = serializers.ListField(child=serializers.DictField())
    milestones = serializers.ListField(child=serializers.DictField())


class ProjectMoneyTrailResponseSerializer(serializers.Serializer):
    data = ProjectMoneyTrailSerializer()
    meta = serializers.DictField()
    errors = serializers.ListField()
