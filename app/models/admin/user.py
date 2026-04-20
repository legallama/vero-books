import uuid
from datetime import datetime
from flask_login import UserMixin
from ...extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255))
    avatar_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship('OrganizationMembership', back_populates='user')

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
