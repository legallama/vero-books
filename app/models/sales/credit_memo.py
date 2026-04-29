import uuid
from datetime import datetime
from app.extensions import db

class CreditMemo(db.Model):
    __tablename__ = 'credit_memos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    credit_number = db.Column(db.String(50), nullable=False)
    
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), default='OPEN') # OPEN, PARTIAL, APPLIED, CLOSED
    
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    tax_total = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    available_balance = db.Column(db.Numeric(15, 2), default=0.00)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    customer = db.relationship('Customer')
    lines = db.relationship('CreditMemoLine', back_populates='credit_memo', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CreditMemo {self.credit_number}>'

class CreditMemoLine(db.Model):
    __tablename__ = 'credit_memo_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credit_memo_id = db.Column(db.String(36), db.ForeignKey('credit_memos.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'))
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) # Income account being reduced
    tax_rate_id = db.Column(db.String(36))

    credit_memo = db.relationship('CreditMemo', back_populates='lines')
    product = db.relationship('Product')
    account = db.relationship('Account')

    def __repr__(self):
        return f'<CreditMemoLine {self.description}>'
