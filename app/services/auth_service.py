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
def get_current_membership():
    from flask_login import current_user
    org = get_current_org()
    if not current_user.is_authenticated or not org:
        return None
    return OrganizationMembership.query.filter_by(user_id=current_user.id, organization_id=org.id).first()

def require_role(roles):
    """
    Decorator to restrict access based on organization roles.
    roles: list of allowed role names (strings)
    """
    from functools import wraps
    from flask import flash, redirect, url_for, abort
    from flask_login import current_user
    
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            membership = get_current_membership()
            if not membership:
                flash("You do not have a valid membership for this organization.", "danger")
                return redirect(url_for('dashboard.index'))
            
            if membership.role.name not in roles and membership.role.name != 'ADMIN':
                flash(f"Access Denied. This action requires one of the following roles: {', '.join(roles)}", "danger")
                return redirect(url_for('dashboard.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
