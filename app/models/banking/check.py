import uuid
from datetime import datetime
from app.extensions import db

class Check(db.Model):
    __tablename__ = 'checks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    bank_account_id = db.Column(db.String(36), db.ForeignKey('bank_accounts.id'), nullable=False)
    check_number = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    payee_type = db.Column(db.String(20)) # VENDOR, CUSTOMER, OTHER
    payee_id = db.Column(db.String(36))   # ID of Vendor/Customer if applicable
    payee_name = db.Column(db.String(100)) # Name to print on check
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    memo = db.Column(db.Text)
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, PRINTED, VOID, CLEARED
    journal_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id'))

    bank_account = db.relationship('BankAccount')
    journal_entry = db.relationship('JournalEntry')

    def __repr__(self):
        return f'<Check {self.check_number} - {self.payee_name}>'
