from flask import session, g
from ..models.admin.organization import Organization, OrganizationMembership

def get_current_org():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return None
        
    cached_org_id = session.get('org_id')
    
    # Verify cached org exists and user belongs to it
    if cached_org_id:
        membership = OrganizationMembership.query.filter_by(user_id=current_user.id, organization_id=cached_org_id).first()
        if membership:
            return Organization.query.get(cached_org_id)
            
    # If no valid cache, pick first available membership
    membership = OrganizationMembership.query.filter_by(user_id=current_user.id).first()
    if membership:
        session['org_id'] = membership.organization_id
        return Organization.query.get(membership.organization_id)
        
    return None
