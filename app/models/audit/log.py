import uuid
from datetime import datetime
from ...extensions import db

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False) # CREATE, UPDATE, DELETE, POST, REVERSE
    entity_type = db.Column(db.String(50), nullable=False) # e.g., 'JOURNAL_ENTRY', 'INVOICE'
    entity_id = db.Column(db.String(36), nullable=False)
    changes = db.Column(db.JSON) # JSON snapshot of changes
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    user = db.relationship('User')


    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type} {self.entity_id}>'
