import uuid
from datetime import datetime
from app.extensions import db

class Estimate(db.Model):
    __tablename__ = 'estimates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    estimate_number = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, SENT, ACCEPTED, DECLINED, CONVERTED
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    customer = db.relationship('Customer')
    lines = db.relationship('EstimateLine', back_populates='estimate', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Estimate {self.estimate_number}>'

class EstimateLine(db.Model):
    __tablename__ = 'estimate_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    estimate_id = db.Column(db.String(36), db.ForeignKey('estimates.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    
    estimate = db.relationship('Estimate', back_populates='lines')

    def __repr__(self):
        return f'<EstimateLine {self.description}>'
