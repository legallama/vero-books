import uuid
from datetime import datetime
from app.extensions import db

class BankRule(db.Model):
    __tablename__ = 'bank_rules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False) # e.g. "Fuel Automation"
    
    # Logic details
    field_to_match = db.Column(db.String(20), default='DESCRIPTION') # DESCRIPTION, AMOUNT
    match_type = db.Column(db.String(20), default='CONTAINS') # CONTAINS, EXACT, GREATER_THAN
    match_value = db.Column(db.String(255), nullable=False)
    
    # Action details
    target_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    target_contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id')) # Optional Payee
    
    is_active = db.Column(db.Boolean, default=True)
    auto_post = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    organization = db.relationship('Organization')
    target_account = db.relationship('Account')
    target_contact = db.relationship('Contact')
