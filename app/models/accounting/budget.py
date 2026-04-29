import uuid
from datetime import datetime
from app.extensions import db

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fiscal_year = db.Column(db.Integer, nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    lines = db.relationship('BudgetLine', back_populates='budget', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Budget {self.name} ({self.fiscal_year})>'

class BudgetLine(db.Model):
    __tablename__ = 'budget_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id = db.Column(db.String(36), db.ForeignKey('budgets.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    
    period = db.Column(db.Integer, nullable=False) # 1 through 12 for months
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    
    budget = db.relationship('Budget', back_populates='lines')
    account = db.relationship('Account')

    def __repr__(self):
        return f'<BudgetLine Period {self.period} - {self.amount}>'
