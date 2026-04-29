import uuid
from datetime import datetime
from app.extensions import db

class VendorCredit(db.Model):
    __tablename__ = 'vendor_credits'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    vendor_id = db.Column(db.String(36), db.ForeignKey('vendors.id'), nullable=False)
    credit_number = db.Column(db.String(50))
    
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), default='OPEN') # OPEN, PARTIAL, APPLIED, VOID
    
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    available_balance = db.Column(db.Numeric(15, 2), default=0.00)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    vendor = db.relationship('Vendor')
    lines = db.relationship('VendorCreditLine', back_populates='vendor_credit', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<VendorCredit {self.credit_number} ({self.available_balance})>'

class VendorCreditLine(db.Model):
    __tablename__ = 'vendor_credit_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_credit_id = db.Column(db.String(36), db.ForeignKey('vendor_credits.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) 
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'))
    
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    
    vendor_credit = db.relationship('VendorCredit', back_populates='lines')
    account = db.relationship('Account')
    product = db.relationship('Product')

    def __repr__(self):
        return f'<VendorCreditLine {self.amount}>'
