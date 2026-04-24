import uuid
from datetime import datetime
from app.extensions import db

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id')) # Staff member
    
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.String(20), default='SCHEDULED') # SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
    location = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    customer = db.relationship('Customer')
    user = db.relationship('User')

    def __repr__(self):
        return f'<Appointment {self.title} with {self.customer_id}>'
