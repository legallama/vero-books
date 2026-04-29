import uuid
from datetime import datetime
from app.extensions import db

class FixedAsset(db.Model):
    __tablename__ = 'fixed_assets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    serial_number = db.Column(db.String(100))
    
    purchase_date = db.Column(db.Date, nullable=False)
    purchase_price = db.Column(db.Numeric(15, 2), default=0.00)
    salvage_value = db.Column(db.Numeric(15, 2), default=0.00)
    useful_life_months = db.Column(db.Integer, default=60) # Default 5 years
    
    depreciation_method = db.Column(db.String(50), default='STRAIGHT_LINE') # STRAIGHT_LINE, DOUBLE_DECLINING
    
    asset_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    accumulated_depreciation_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    depreciation_expense_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    
    status = db.Column(db.String(20), default='ACTIVE') # ACTIVE, DISPOSED, SOLD
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    asset_account = db.relationship('Account', foreign_keys=[asset_account_id])
    accum_dep_account = db.relationship('Account', foreign_keys=[accumulated_depreciation_account_id])
    expense_account = db.relationship('Account', foreign_keys=[depreciation_expense_account_id])
    
    schedules = db.relationship('DepreciationSchedule', back_populates='asset', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<FixedAsset {self.name}>'

class DepreciationSchedule(db.Model):
    __tablename__ = 'depreciation_schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = db.Column(db.String(36), db.ForeignKey('fixed_assets.id'), nullable=False)
    journal_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id'))
    
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    accumulated_amount = db.Column(db.Numeric(15, 2), nullable=False)
    book_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    status = db.Column(db.String(20), default='SCHEDULED') # SCHEDULED, POSTED

    asset = db.relationship('FixedAsset', back_populates='schedules')
    journal_entry = db.relationship('JournalEntry')

    def __repr__(self):
        return f'<DepreciationSchedule {self.date} - {self.amount}>'
