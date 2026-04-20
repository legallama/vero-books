import uuid
from datetime import datetime
from app.extensions import db

class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    vendor_id = db.Column(db.String(36), db.ForeignKey('vendors.id'), nullable=False)
    bill_number = db.Column(db.String(50)) # Vendor's invoice number
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, OPEN, PAID, VOID
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    tax_total = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    balance_due = db.Column(db.Numeric(15, 2), default=0.00)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    vendor = db.relationship('Vendor')
    lines = db.relationship('BillLine', back_populates='bill', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Bill {self.bill_number} from {self.vendor_id}>'

class BillLine(db.Model):
    __tablename__ = 'bill_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = db.Column(db.String(36), db.ForeignKey('bills.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) # Expense account
    
    bill = db.relationship('Bill', back_populates='lines')
    account = db.relationship('Account')

    def __repr__(self):
        return f'<BillLine {self.description}>'
