from rest_framework.permissions import SAFE_METHODS, BasePermission


class FeedbackPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.moderation_status == obj.ModerationStatus.APPROVED or (
                request.user.is_authenticated and obj.citizen_profile.user_id == request.user.pk
            )
        return request.user.is_authenticated and obj.citizen_profile.user_id == request.user.pk
