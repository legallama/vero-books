from app import create_app, db
from app.models.admin.organization import Organization, OrganizationMembership
from app.models.admin.user import User
from werkzeug.security import generate_password_hash

def fix_login():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create Org
        org = Organization(name="Vero Ledger")
        db.session.add(org)
        db.session.flush()

        # Create User - admin@verobooks.com / password123
        user = User(
            email="admin@verobooks.com",
            # We must use the same hash method Flask-Login expects if we aren't using the model method
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.flush()

        # Create Membership
        from app.models.admin.organization import Role
        role = Role(name="ADMIN")
        db.session.add(role)
        db.session.flush()
        
        membership = OrganizationMembership(user_id=user.id, organization_id=org.id, role_id=role.id, is_owner=True)
        db.session.add(membership)

        db.session.commit()
        print(f"User Created: admin@verobooks.com / password123")
        print(f"Org Created: {org.name}")

if __name__ == "__main__":
    fix_login()
