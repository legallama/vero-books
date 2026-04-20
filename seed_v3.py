from app import create_app, db
from app.models.admin.organization import Organization, OrganizationMembership
from app.models.admin.user import User
from app.models.accounting.account import Account
from app.models.crm.contact import Customer
from app.models.sales.invoice import Invoice
from datetime import date, timedelta

def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        org = Organization(name="Vero Books")
        db.session.add(org)
        db.session.flush()

        user = User(email="admin@verobooks.com", password_hash="hash")
        db.session.add(user)
        db.session.flush()

        membership = OrganizationMembership(user_id=user.id, organization_id=org.id, role='ADMIN')
        db.session.add(membership)

        ar_acc = Account(organization_id=org.id, code="1200", name="Accounts Receivable", type="Asset")
        inc_acc = Account(organization_id=org.id, code="4000", name="Sales Income", type="Income")
        db.session.add(ar_acc)
        db.session.add(inc_acc)
        db.session.flush()

        cust = Customer(organization_id=org.id, display_name="Client A")
        db.session.add(cust)
        db.session.flush()

        for i in range(5):
            inv = Invoice(
                organization_id=org.id,
                customer_id=cust.id,
                invoice_number=f"INV-{i}",
                issue_date=date.today() - timedelta(days=i*30),
                due_date=date.today(),
                total=1000 * (i+1),
                balance_due=1000 * (i+1),
                status="SENT"
            )
            db.session.add(inv)

        db.session.commit()
        print("Success")

if __name__ == "__main__":
    seed()
