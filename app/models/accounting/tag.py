import uuid
from datetime import datetime
from app.extensions import db

# Association Table for Many-to-Many tagging
transaction_tags = db.Table('transaction_tags',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('tag_id', db.String(36), db.ForeignKey('tags.id'), nullable=False),
    db.Column('journal_entry_id', db.String(36), db.ForeignKey('journal_entries.id')),
    db.Column('invoice_id', db.String(36), db.ForeignKey('invoices.id')),
    db.Column('bill_id', db.String(36), db.ForeignKey('bills.id'))
)


class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#6366f1') # HEX color for UI
    type = db.Column(db.String(20), default='GENERAL') # PROJECT, DEPARTMENT, GENERAL
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization')
    
    # Relationships to tagged entities
    journal_entries = db.relationship('JournalEntry', secondary=transaction_tags, backref=db.backref('tags', lazy='dynamic'))
    invoices = db.relationship('Invoice', secondary=transaction_tags, backref=db.backref('tags', lazy='dynamic'))
    bills = db.relationship('Bill', secondary=transaction_tags, backref=db.backref('tags', lazy='dynamic'))

    def __repr__(self):
        return f'<Tag {self.name}>'
