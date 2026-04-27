import uuid
from datetime import datetime
from app.extensions import db

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) # Link to GL account
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50)) # Checking, Savings, Credit Card
    account_number_last4 = db.Column(db.String(4))
    bank_name = db.Column(db.String(100))
    currency_code = db.Column(db.String(3), default='USD')
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    gl_account = db.relationship('Account')
    transactions = db.relationship('BankTransaction', back_populates='bank_account')

    def __repr__(self):
        return f'<BankAccount {self.name} (*{self.account_number_last4})>'

class BankTransaction(db.Model):
    __tablename__ = 'bank_transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    bank_account_id = db.Column(db.String(36), db.ForeignKey('bank_accounts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(15, 2), nullable=False) # Positive = Deposit, Negative = Withdrawal
    reference = db.Column(db.String(100))
    status = db.Column(db.String(20), default='UNCATEGORIZED') # UNCATEGORIZED, MATCHED, EXCLUDED
    matched_source_type = db.Column(db.String(50)) # INVOICE, BILL, JOURNAL_ENTRY
    matched_source_id = db.Column(db.String(36))
    receipt_url = db.Column(db.Text)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)


    bank_account = db.relationship('BankAccount', back_populates='transactions')

    def __repr__(self):
        return f'<BankTransaction {self.date} {self.amount}>'
