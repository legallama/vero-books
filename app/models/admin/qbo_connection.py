import uuid
from datetime import datetime
from app.extensions import db

class QboConnection(db.Model):
    __tablename__ = 'qbo_connections'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, unique=True)
    
    realm_id = db.Column(db.String(100)) # QBO Company ID
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    
    access_token_expires_at = db.Column(db.DateTime)
    refresh_token_expires_at = db.Column(db.DateTime)
    
    client_id = db.Column(db.String(255))
    client_secret = db.Column(db.String(255))
    environment = db.Column(db.String(20), default='sandbox') # sandbox or production
    
    last_sync_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')

    def __repr__(self):
        return f'<QboConnection {self.realm_id}>'
