from app import create_app, db
from app.models.admin.user import User
from app.models.admin.organization import Organization, OrganizationMembership, Role
from app.models.accounting.account import Account

app = create_app()

def seed():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if user already exists
        if User.query.filter_by(email='admin@verobooks.com').first():
            print("Database already seeded.")
            return

        # Create Demo User
        user = User(email='admin@verobooks.com', full_name='Demo Admin')
        # In a real app, use password hashing
        user.password_hash = 'pbkdf2:sha256:...' 
        db.session.add(user)
        
        # Create Demo Organization
        org = Organization(name='VeroBooks Demo', legal_name='VeroBooks Systems Inc.')
        db.session.add(org)
        
        # Create Admin Role
        role = Role(name='Administrator', description='Full access')
        db.session.add(role)
        
        db.session.flush() # Get IDs
        
        # Create Membership
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role_id=role.id,
            is_owner=True
        )
        db.session.add(membership)
        
        # Create basic Chart of Accounts
        accounts = [
            ('1000', 'Cash', 'Asset'),
            ('1200', 'Accounts Receivable', 'Asset'),
            ('2000', 'Accounts Payable', 'Liability'),
            ('3000', 'Owner Equity', 'Equity'),
            ('4000', 'Sales Income', 'Income'),
            ('5000', 'General Expense', 'Expense'),
        ]
        
        for code, name, acc_type in accounts:
            acc = Account(
                organization_id=org.id,
                code=code,
                name=name,
                type=acc_type,
                is_active=True
            )
            db.session.add(acc)
            
        db.session.commit()
        print("Database seeded successfully with 'admin@verobooks.com'")

if __name__ == '__main__':
    seed()
