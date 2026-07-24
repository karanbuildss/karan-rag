from rest_framework import serializers

from anomalies.models import AnomalyFlag


class AnomalyFlagSerializer(serializers.ModelSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)
    project_title_en = serializers.CharField(source="project.title_en", read_only=True)
    project_title_np = serializers.CharField(source="project.title_np", read_only=True)

    class Meta:
        model = AnomalyFlag
        fields = "__all__"
