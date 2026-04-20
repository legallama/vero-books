import uuid
from datetime import datetime
from app.extensions import db

class InvoicePayment(db.Model):
    __tablename__ = 'invoice_payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'), nullable=False)
    bank_account_id = db.Column(db.String(36), db.ForeignKey('bank_accounts.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    reference = db.Column(db.String(100))
    payment_method = db.Column(db.String(50)) # CHECK, WIRE, CASH, CREDIT_CARD

    invoice = db.relationship('Invoice')
    bank_account = db.relationship('BankAccount')

class BillPayment(db.Model):
    __tablename__ = 'bill_payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    bill_id = db.Column(db.String(36), db.ForeignKey('bills.id'), nullable=False)
    bank_account_id = db.Column(db.String(36), db.ForeignKey('bank_accounts.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    reference = db.Column(db.String(100))

    bill = db.relationship('Bill')
    bank_account = db.relationship('BankAccount')
