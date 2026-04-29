import uuid
from datetime import datetime
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50))
    type = db.Column(db.String(20), default='SERVICE') # PRODUCT, SERVICE
    
    sale_price = db.Column(db.Numeric(15, 2), default=0.00)
    sale_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))
    
    purchase_cost = db.Column(db.Numeric(15, 2), default=0.00)
    purchase_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))
    
    # Inventory Tracking
    track_inventory = db.Column(db.Boolean, default=False)
    quantity_on_hand = db.Column(db.Numeric(15, 2), default=0.00)
    reorder_point = db.Column(db.Numeric(15, 2), default=0.00)
    asset_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))
    cogs_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    sale_account = db.relationship('Account', foreign_keys=[sale_account_id])
    purchase_account = db.relationship('Account', foreign_keys=[purchase_account_id])
    asset_account = db.relationship('Account', foreign_keys=[asset_account_id])
    cogs_account = db.relationship('Account', foreign_keys=[cogs_account_id])

    def __repr__(self):
        return f'<Product {self.name}>'
