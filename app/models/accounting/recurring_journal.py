import uuid
from datetime import datetime
from app import db

class RecurringJournalEntry(db.Model):
    __tablename__ = 'recurring_journal_entries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    memo = db.Column(db.Text)
    
    frequency = db.Column(db.String(20), nullable=False) # WEEKLY, MONTHLY, QUARTERLY, YEARLY
    day_of_month = db.Column(db.Integer) # 1-31
    
    next_run_date = db.Column(db.Date)
    last_run_date = db.Column(db.Date)
    
    status = db.Column(db.String(20), default='ACTIVE') # ACTIVE, PAUSED, COMPLETED
    auto_post = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    lines = db.relationship('RecurringJournalLine', back_populates='recurring_entry', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<RecurringJournalEntry {self.name} ({self.frequency})>'

class RecurringJournalLine(db.Model):
    __tablename__ = 'recurring_journal_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recurring_entry_id = db.Column(db.String(36), db.ForeignKey('recurring_journal_entries.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    
    debit = db.Column(db.Numeric(15, 2), default=0.00)
    credit = db.Column(db.Numeric(15, 2), default=0.00)
    description = db.Column(db.String(255))

    recurring_entry = db.relationship('RecurringJournalEntry', back_populates='lines')
    account = db.relationship('Account')
