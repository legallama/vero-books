import uuid
from datetime import datetime
from app.extensions import db

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, SENT, PAID, OVERDUE, VOID
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    tax_total = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    balance_due = db.Column(db.Numeric(15, 2), default=0.00)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    customer = db.relationship('Customer', back_populates='invoices')
    lines = db.relationship('InvoiceLine', back_populates='invoice', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class InvoiceLine(db.Model):
    __tablename__ = 'invoice_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) # Income account
    tax_rate_id = db.Column(db.String(36))

    invoice = db.relationship('Invoice', back_populates='lines')
    account = db.relationship('Account')

    def __repr__(self):
        return f'<InvoiceLine {self.description}>'
