import uuid
from datetime import datetime
from app.extensions import db

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    tag_type = db.Column(db.String(20)) # CLASS, LOCATION, PROJECT
    color_code = db.Column(db.String(7)) # Hex color
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Tag {self.name} ({self.tag_type})>'
