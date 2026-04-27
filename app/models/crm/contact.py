import uuid
from datetime import datetime
from app.extensions import db

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    contact_type = db.Column(db.String(20)) # CUSTOMER, VENDOR, etc.
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')

    def __repr__(self):
        return f'<Contact {self.display_name}>'

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(255))
    address_line1 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='USA')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    invoices = db.relationship('Invoice', back_populates='customer')

    def to_dict(self):
        return {
            'id': self.id,
            'display_name': self.display_name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'address_line1': self.address_line1,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Customer {self.display_name}>'

class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address_line1 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='USA')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    # bills = db.relationship('Bill', back_populates='vendor')

    def to_dict(self):
        return {
            'id': self.id,
            'display_name': self.display_name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Vendor {self.display_name}>'

