import uuid
from datetime import datetime
from app.extensions import db

class TaxNexus(db.Model):
    __tablename__ = 'tax_nexus'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    state_code = db.Column(db.String(2), nullable=False) # e.g., 'CA', 'NY'
    state_name = db.Column(db.String(100))
    registration_number = db.Column(db.String(100))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TaxZipRate(db.Model):
    """A lookup table for zip-to-rate mapping (Mocking an external tax API)"""
    __tablename__ = 'tax_zip_rates'
    
    zip_code = db.Column(db.String(20), primary_key=True)
    state_code = db.Column(db.String(2), nullable=False)
    combined_rate = db.Column(db.Numeric(6, 4), nullable=False) # e.g., 0.0825 for 8.25%
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
