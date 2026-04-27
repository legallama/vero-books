from app.models.audit.log import AuditLog
from app.extensions import db
from flask import request

class AuditService:
    @staticmethod
    def log_action(organization_id, user_id, action, entity_type, entity_id, changes=None, reason=None):
        """
        Creates a new audit log entry.
        """
        log = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            reason=reason,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log)
        # We don't commit here to allow it to be part of the same transaction
        return log
