import uuid
from datetime import datetime
from app.extensions import db

class RecurringInvoice(db.Model):
    __tablename__ = 'recurring_invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    profile_name = db.Column(db.String(100), nullable=False) # e.g. "Monthly retainer"
    
    frequency = db.Column(db.String(20), nullable=False) # MONTHLY, WEEKLY, QUARTERLY, YEARLY
    next_issue_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date) # Optional
    
    is_active = db.Column(db.Boolean, default=True)
    auto_send = db.Column(db.Boolean, default=False)
    
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    tax_total = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    customer = db.relationship('Customer')
    lines = db.relationship('RecurringInvoiceLine', back_populates='recurring_invoice', cascade='all, delete-orphan')

class RecurringInvoiceLine(db.Model):
    __tablename__ = 'recurring_invoice_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recurring_invoice_id = db.Column(db.String(36), db.ForeignKey('recurring_invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))

    recurring_invoice = db.relationship('RecurringInvoice', back_populates='lines')
    account = db.relationship('Account')
