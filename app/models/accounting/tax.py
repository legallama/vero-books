import uuid
from app.extensions import db

class TaxRate(db.Model):
    __tablename__ = 'tax_rates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    rate = db.Column(db.Numeric(5, 4), nullable=False) # e.g. 0.0825 for 8.25%
    is_compound = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TaxRate {self.name}: {self.rate*100}%>'
