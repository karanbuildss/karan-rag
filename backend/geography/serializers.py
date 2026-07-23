from rest_framework import serializers

from geography.models import LocalGovernment


class LocalGovernmentSerializer(serializers.ModelSerializer):
    district_code = serializers.CharField(source="district.code", read_only=True)
    district_name_en = serializers.CharField(source="district.name_en", read_only=True)
    district_name_np = serializers.CharField(source="district.name_np", read_only=True)
    province_code = serializers.CharField(source="district.province.code", read_only=True)

    class Meta:
        model = LocalGovernment
        fields = [
            "id",
            "code",
            "name_en",
            "name_np",
            "government_type",
            "district_code",
            "district_name_en",
            "district_name_np",
            "province_code",
        ]
