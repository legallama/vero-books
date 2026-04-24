from app import db
from datetime import datetime

class Reconciliation(db.Model):
    __tablename__ = 'reconciliations'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    statement_date = db.Column(db.Date, nullable=False)
    statement_balance = db.Column(db.Numeric(15, 2), nullable=False) # Ending balance
    starting_balance = db.Column(db.Numeric(15, 2), nullable=False) # Cleared balance at start
    
    status = db.Column(db.String(20), default='STARTED') # STARTED, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    account = db.relationship('Account', backref='reconciliations')
    cleared_lines = db.relationship('JournalLine', backref='reconciliation')
    
    def __repr__(self):
        return f'<Reconciliation {self.account.name} {self.statement_date}>'
