import uuid
from datetime import datetime
from app.extensions import db

class Currency(db.Model):
    __tablename__ = 'currencies'
    
    code = db.Column(db.String(3), primary_key=True) # USD, EUR, GBP
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Currency {self.code}>'

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    base_currency = db.Column(db.String(3), db.ForeignKey('currencies.code'), nullable=False)
    target_currency = db.Column(db.String(3), db.ForeignKey('currencies.code'), nullable=False)
    
    rate = db.Column(db.Numeric(18, 6), nullable=False)
    effective_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    
    organization = db.relationship('Organization')
    base = db.relationship('Currency', foreign_keys=[base_currency])
    target = db.relationship('Currency', foreign_keys=[target_currency])

    def __repr__(self):
        return f'<ExchangeRate {self.base_currency} to {self.target_currency} = {self.rate}>'
