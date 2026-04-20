import uuid
from datetime import datetime
from ...extensions import db

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    legal_name = db.Column(db.String(255))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    default_currency_code = db.Column(db.String(3), default='USD')
    fiscal_year_start_month = db.Column(db.Integer, default=1)
    timezone = db.Column(db.String(50), default='UTC')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship('OrganizationMembership', back_populates='organization')
    accounts = db.relationship('Account', back_populates='organization')
    journal_entries = db.relationship('JournalEntry', back_populates='organization')

    def __repr__(self):
        return f'<Organization {self.name}>'

class OrganizationMembership(db.Model):
    __tablename__ = 'organization_memberships'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    is_owner = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='memberships')
    user = db.relationship('User', back_populates='memberships')
    role = db.relationship('Role')

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    # Add permissions list / bitmask later
