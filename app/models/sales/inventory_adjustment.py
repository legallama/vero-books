import uuid
from datetime import datetime
from app.extensions import db

class InventoryAdjustment(db.Model):
    __tablename__ = 'inventory_adjustments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    reference_number = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    reason = db.Column(db.String(50)) # SHRINKAGE, DAMAGE, PHYSICAL_COUNT, PROMOTIONAL, etc.
    adjustment_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False) # The offset expense/income account
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    adjustment_account = db.relationship('Account')
    lines = db.relationship('InventoryAdjustmentLine', back_populates='adjustment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<InventoryAdjustment {self.reference_number}>'

class InventoryAdjustmentLine(db.Model):
    __tablename__ = 'inventory_adjustment_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    adjustment_id = db.Column(db.String(36), db.ForeignKey('inventory_adjustments.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    
    quantity_adjusted = db.Column(db.Numeric(15, 2), nullable=False) # Positive to add inventory, Negative to remove
    unit_cost = db.Column(db.Numeric(15, 2), default=0.00) # Cost at time of adjustment
    total_value_adjusted = db.Column(db.Numeric(15, 2), default=0.00) # quantity_adjusted * unit_cost
    
    adjustment = db.relationship('InventoryAdjustment', back_populates='lines')
    product = db.relationship('Product')

    def __repr__(self):
        return f'<InventoryAdjustmentLine {self.product_id} ({self.quantity_adjusted})>'
