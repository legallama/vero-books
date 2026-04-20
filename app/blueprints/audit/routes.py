from flask import Blueprint, render_template
from flask_login import login_required
from app.models.audit.log import AuditLog
from app.services.auth_service import get_current_org

audit_bp = Blueprint('audit', __name__, url_prefix='/audit-trail')

@audit_bp.route('/')
@login_required
def history():
    org = get_current_org()
    logs = AuditLog.query.filter_by(organization_id=org.id).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('audit/history.html', logs=logs)
