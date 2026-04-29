import uuid
from datetime import datetime
from app.extensions import db

class SalesReceipt(db.Model):
    __tablename__ = 'sales_receipts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    receipt_number = db.Column(db.String(50), nullable=False)
    
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    deposit_to_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) # Bank Account or Undeposited Funds
    
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    tax_total = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    
    payment_method = db.Column(db.String(50)) # Cash, Check, Credit Card
    reference_number = db.Column(db.String(100)) # Check # or Transaction ID
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    customer = db.relationship('Customer')
    deposit_to_account = db.relationship('Account')
    lines = db.relationship('SalesReceiptLine', back_populates='sales_receipt', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SalesReceipt {self.receipt_number}>'

class SalesReceiptLine(db.Model):
    __tablename__ = 'sales_receipt_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_receipt_id = db.Column(db.String(36), db.ForeignKey('sales_receipts.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'))
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) # Income account
    tax_rate_id = db.Column(db.String(36))

    sales_receipt = db.relationship('SalesReceipt', back_populates='lines')
    product = db.relationship('Product')
    account = db.relationship('Account')

    def __repr__(self):
        return f'<SalesReceiptLine {self.description}>'
