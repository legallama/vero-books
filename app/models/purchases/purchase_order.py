import uuid
from datetime import datetime
from app.extensions import db

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    vendor_id = db.Column(db.String(36), db.ForeignKey('vendors.id'), nullable=False)
    po_number = db.Column(db.String(50), nullable=False)
    
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    expected_date = db.Column(db.Date)
    
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, SENT, PARTIAL, RECEIVED, CLOSED, CANCELLED
    
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    tax_total = db.Column(db.Numeric(15, 2), default=0.00)
    total = db.Column(db.Numeric(15, 2), default=0.00)
    
    notes = db.Column(db.Text)
    delivery_address = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    vendor = db.relationship('Vendor')
    lines = db.relationship('PurchaseOrderLine', back_populates='purchase_order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}>'

class PurchaseOrderLine(db.Model):
    __tablename__ = 'purchase_order_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id = db.Column(db.String(36), db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'))
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    quantity_received = db.Column(db.Numeric(10, 2), default=0.00)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id')) 
    
    purchase_order = db.relationship('PurchaseOrder', back_populates='lines')
    product = db.relationship('Product')
    account = db.relationship('Account')

    def __repr__(self):
        return f'<PurchaseOrderLine {self.description}>'
