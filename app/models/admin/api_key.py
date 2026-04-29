import uuid
from datetime import datetime
from app.extensions import db

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    token_prefix = db.Column(db.String(8), nullable=False) # e.g., 'vb_live_'
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    user = db.relationship('User')

    def __repr__(self):
        return f'<ApiKey {self.name} ({self.token_prefix}...)>'
