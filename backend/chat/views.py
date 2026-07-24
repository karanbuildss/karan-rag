from config.api import EnvelopeReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated

from chat.models import ChatSession
from chat.serializers import ChatSessionSerializer


class ChatSessionViewSet(EnvelopeReadOnlyModelViewSet):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-updated_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ChatSession.objects.none()
        return (
            ChatSession.objects.filter(user=self.request.user)
            .select_related("selected_project")
            .prefetch_related("messages")
        )
