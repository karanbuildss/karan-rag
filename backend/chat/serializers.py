from rest_framework import serializers

from chat.models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "role",
            "content",
            "route_used",
            "response_citations",
            "response_visualizations",
            "created_at",
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    project_code = serializers.CharField(
        source="selected_project.code", read_only=True, allow_null=True
    )

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "selected_project",
            "project_code",
            "created_at",
            "updated_at",
            "messages",
        ]
