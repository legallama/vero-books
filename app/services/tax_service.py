from app.models.accounting.tax_nexus import TaxNexus, TaxZipRate
from app.extensions import db
from decimal import Decimal

class TaxService:
    @staticmethod
    def get_rate_for_zip(zip_code, org_id):
        """Returns the tax rate for a given zip code if Nexus exists in that state."""
        lookup = TaxZipRate.query.filter_by(zip_code=zip_code).first()
        if not lookup:
            return Decimal('0.00')
            
        # Check if the organization has Nexus in this state
        nexus = TaxNexus.query.filter_by(organization_id=org_id, state_code=lookup.state_code, is_active=True).first()
        if not nexus:
            # No Nexus, no sales tax required
            return Decimal('0.00')
            
        return lookup.combined_rate

    @staticmethod
    def seed_mock_rates():
        """Populates mock rates for common zip codes for demo purposes."""
        mock_data = [
            ('90210', 'CA', Decimal('0.0950')), # Beverly Hills
            ('10001', 'NY', Decimal('0.08875')), # NYC
            ('33101', 'FL', Decimal('0.0700')), # Miami
            ('60601', 'IL', Decimal('0.1025')), # Chicago
            ('77001', 'TX', Decimal('0.0825')), # Houston
            ('85001', 'AZ', Decimal('0.0860')), # Phoenix
        ]
        
        for zip_code, state, rate in mock_data:
            existing = TaxZipRate.query.filter_by(zip_code=zip_code).first()
            if not existing:
                new_rate = TaxZipRate(zip_code=zip_code, state_code=state, combined_rate=rate)
                db.session.add(new_rate)
        
        db.session.commit()

    @staticmethod
    def register_nexus(org_id, state_code):
        """Registers a new tax nexus for an organization."""
        existing = TaxNexus.query.filter_by(organization_id=org_id, state_code=state_code).first()
        if not existing:
            new_nexus = TaxNexus(organization_id=org_id, state_code=state_code)
            db.session.add(new_nexus)
            db.session.commit()
            return new_nexus
        return existing
