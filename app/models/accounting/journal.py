import uuid
from datetime import datetime
from ...extensions import db

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    entry_number = db.Column(db.String(20), nullable=False)
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    memo = db.Column(db.Text)
    source_type = db.Column(db.String(50)) # e.g., 'INVOICE', 'BILL', 'MANUAL'
    source_id = db.Column(db.String(36))
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, POSTED, REVERSED
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    posted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    posted_at = db.Column(db.DateTime)
    reversed_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id'))

    organization = db.relationship('Organization', back_populates='journal_entries')
    lines = db.relationship('JournalLine', back_populates='journal_entry', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<JournalEntry {self.entry_number} ({self.status})>'

class JournalLine(db.Model):
    __tablename__ = 'journal_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    debit = db.Column(db.Numeric(15, 2), default=0.00)
    credit = db.Column(db.Numeric(15, 2), default=0.00)
    description = db.Column(db.String(255))
    customer_id = db.Column(db.String(36)) # Optional: Link to customer
    vendor_id = db.Column(db.String(36))   # Optional: Link to vendor
    tax_rate_id = db.Column(db.String(36)) # Optional: Link to tax rate

    journal_entry = db.relationship('JournalEntry', back_populates='lines')
    account = db.relationship('Account', back_populates='journal_lines')

    def __repr__(self):
        return f'<JournalLine {self.account_id} D:{self.debit} C:{self.credit}>'
