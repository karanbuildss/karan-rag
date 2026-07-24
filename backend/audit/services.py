from audit.models import AuditLog


def record_audit(
    *,
    actor,
    action,
    object_type,
    object_id,
    before=None,
    after=None,
    request_identifier="",
):
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        before_summary=before or {},
        after_summary=after or {},
        request_identifier=request_identifier,
    )
