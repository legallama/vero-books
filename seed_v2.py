from app import create_app, db
from app.models.admin.organization import Organization
from app.models.admin.user import User
from app.models.accounting.account import Account
from app.models.crm.contact import Customer
from app.models.sales.invoice import Invoice, InvoiceLine
from datetime import datetime, date, timedelta

def seed():
    app = create_app()
    with app.app_context():
        # Clear existing
        db.drop_all()
        db.create_all()

        # Create Org
        org = Organization(name="Vero Ledger Demo")
        db.session.add(org)
        db.session.commit()

        # Create User
        user = User(email="admin@verobooks.com")
        user.password_hash = "scrypt:32768:8:1$tq2YV7mK0YpPz7yT$58e578c7..." # hashed password123
        db.session.add(user)
        db.session.commit()

        # Create Membership
        from app.models.admin.organization import OrganizationMembership
        membership = OrganizationMembership(user_id=user.id, organization_id=org.id, role='ADMIN')
        db.session.add(membership)

        # Create COA
        accounts = [
            Account(organization_id=org.id, code="1000", name="Checking", type="Asset"),
            Account(organization_id=org.id, code="1200", name="Accounts Receivable", type="Asset"),
            Account(organization_id=org.id, code="4000", name="Service Revenue", type="Income"),
            Account(organization_id=org.id, code="6000", name="Standard Expenses", type="Expense")
        ]
        for a in accounts: db.session.add(a)

        # Create Customer
        cust = Customer(organization_id=org.id, display_name="Acme Corp")
        db.session.add(cust)
        db.session.commit()

        # Create some Invoices for the chart
        for i in range(5):
            inv = Invoice(
                organization_id=org.id,
                customer_id=cust.id,
                invoice_number=f"INV-00{i}",
                issue_date=date.today() - timedelta(days=i*30),
                due_date=date.today() - timedelta(days=i*30-30),
                total=5000 + (i * 1000),
                status="PAID" if i > 0 else "SENT"
            )
            db.session.add(inv)

        db.session.commit()
        print("Database seeded with sample data.")

if __name__ == "__main__":
    seed()
