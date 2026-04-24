from app import db
from datetime import datetime

class Receipt(db.Model):
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Financial data (to be extracted via OCR or manual entry later)
    amount = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3), default='USD')
    vendor_name = db.Column(db.String(255))
    receipt_date = db.Column(db.Date)
    
    status = db.Column(db.String(20), default='PENDING') # PENDING, PROCESSED, DISCARDED
    
    # Relationships
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Linked journal entry (if processed)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'))
    
    def __repr__(self):
        return f'<Receipt {self.original_name}>'
