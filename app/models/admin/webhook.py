import uuid
from datetime import datetime
from app.extensions import db

class WebhookEndpoint(db.Model):
    __tablename__ = 'webhook_endpoints'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(255))
    secret = db.Column(db.String(255)) # For signature verification
    
    subscribed_events = db.Column(db.String(500), default='*') # Comma separated list, or '*'
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    deliveries = db.relationship('WebhookDelivery', back_populates='endpoint', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<WebhookEndpoint {self.url}>'

class WebhookDelivery(db.Model):
    __tablename__ = 'webhook_deliveries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = db.Column(db.String(36), db.ForeignKey('webhook_endpoints.id'), nullable=False)
    
    event_type = db.Column(db.String(100), nullable=False) # e.g., 'invoice.created'
    payload = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='PENDING') # PENDING, SUCCESS, FAILED
    response_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    
    duration_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    endpoint = db.relationship('WebhookEndpoint', back_populates='deliveries')

    def __repr__(self):
        return f'<WebhookDelivery {self.event_type} - {self.status}>'
