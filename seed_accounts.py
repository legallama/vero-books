from app import create_app
from app.models.admin.organization import Organization
from app.services.account_service import seed_standard_accounts
from app.extensions import db

def run_seeder():
    app = create_app()
    with app.app_context():
        orgs = Organization.query.all()
        print(f"Seeding accounts for {len(orgs)} organizations...")
        for org in orgs:
            print(f" - Seeding {org.name}...")
            seed_standard_accounts(org.id)
        print("Seeding complete.")

if __name__ == "__main__":
    run_seeder()
