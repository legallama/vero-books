import uuid
from datetime import datetime
from app.extensions import db

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50)) # e.g., Developer, Accountant
    
    type = db.Column(db.String(20), default='EMPLOYEE') # EMPLOYEE, CONTRACTOR
    status = db.Column(db.String(20), default='ACTIVE') # ACTIVE, INACTIVE
    
    hire_date = db.Column(db.Date)
    hourly_rate = db.Column(db.Numeric(10, 2))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')

    def __repr__(self):
        return f'<TeamMember {self.full_name} ({self.type})>'
