from rest_framework import serializers

INVESTIGATOR_LANGUAGE_CHOICES = [
    ("auto", "Detect from question"),
    ("en", "English"),
    ("ne", "Nepali"),
    ("romanized_ne", "Romanized Nepali"),
]


class InvestigatorQuerySerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000, trim_whitespace=True)
    project_id = serializers.UUIDField(required=False, allow_null=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    language = serializers.ChoiceField(
        choices=INVESTIGATOR_LANGUAGE_CHOICES,
        default="auto",
    )

    def validate_question(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Question must contain at least three characters.",
                code="question_too_short",
            )
        return value.strip()


class InvestigatorResultSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(allow_null=True)
    question = serializers.CharField()
    route = serializers.CharField()
    language = serializers.CharField()
    answer = serializers.CharField()
    project = serializers.DictField(allow_null=True)
    structured_facts = serializers.DictField(allow_null=True)
    anomalies = serializers.ListField(child=serializers.DictField())
    citations = serializers.ListField(child=serializers.DictField())
    visualizations = serializers.ListField(child=serializers.DictField())
    limitations = serializers.ListField(child=serializers.DictField())
    provenance = serializers.DictField()


class InvestigatorResponseSerializer(serializers.Serializer):
    data = InvestigatorResultSerializer()
    meta = serializers.DictField()
    errors = serializers.ListField()
