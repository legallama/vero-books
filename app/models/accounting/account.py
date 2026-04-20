import uuid
from enum import Enum
from ...extensions import db

class AccountType(str, Enum):
    ASSET = 'Asset'
    LIABILITY = 'Liability'
    EQUITY = 'Equity'
    INCOME = 'Income'
    EXPENSE = 'Expense'

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False) # Maps to AccountType
    subtype = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    parent_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))
    currency_code = db.Column(db.String(3), default='USD')

    organization = db.relationship('Organization', back_populates='accounts')
    children = db.relationship('Account', backref=db.backref('parent', remote_side=[id]))
    journal_lines = db.relationship('JournalLine', back_populates='account')

    def __repr__(self):
        return f'<Account {self.code} - {self.name}>'
