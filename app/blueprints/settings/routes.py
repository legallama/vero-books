from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from ._bp import settings_bp
from app.models.accounting.tax import TaxRate
from app.services.auth_service import get_current_org
from app.extensions import db

@settings_bp.route('/')
@login_required
def index():
    org = get_current_org()
    return render_template('settings/index.html', org=org)

import os
from werkzeug.utils import secure_filename
from flask import current_app
from flask_login import current_user

@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join('app', 'static', 'uploads', 'avatars')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, f"{current_user.id}_{filename}")
                file.save(file_path)
                
                # Save just the relative path
                current_user.avatar_path = f"uploads/avatars/{current_user.id}_{filename}"
                db.session.commit()
                flash("Profile picture updated.", "success")
                return redirect(url_for('settings.profile'))
                
        # Handle profile info update
        username = request.form.get('username')
        if username:
            current_user.username = username
            # For backward compatibility, also update full_name
            current_user.full_name = username
            db.session.commit()
            flash("Profile information updated.", "success")
            return redirect(url_for('settings.profile'))
                
    return render_template('settings/profile.html')

@settings_bp.route('/users')
@login_required
def users():
    org = get_current_org()
    from app.models.admin.organization import OrganizationMembership
    memberships = OrganizationMembership.query.filter_by(organization_id=org.id).all()
    return render_template('settings/users.html', memberships=memberships)

@settings_bp.route('/tax-rates')
@login_required
def tax_rates():
    org = get_current_org()
    rates = TaxRate.query.filter_by(organization_id=org.id).all()
    return render_template('settings/tax_rates.html', rates=rates)
@settings_bp.route('/api/tax-rates', methods=['POST'])
@login_required
def create_tax_rate():
    from flask import jsonify
    org = get_current_org()
    data = request.get_json()
    new_rate = TaxRate(
        organization_id=org.id,
        name=data.get('name'),
        rate=data.get('rate')
    )
    db.session.add(new_rate)
    db.session.commit()
    return jsonify({'id': new_rate.id, 'name': new_rate.name, 'rate': float(new_rate.rate)})

@settings_bp.route('/api/tax-rates/<rate_id>', methods=['DELETE'])
@login_required
def delete_tax_rate(rate_id):
    from flask import jsonify
    org = get_current_org()
    rate = TaxRate.query.filter_by(id=rate_id, organization_id=org.id).first_or_404()
    db.session.delete(rate)
    db.session.commit()
    return jsonify({'success': True})
@settings_bp.route('/organizations/new', methods=['GET', 'POST'])
@login_required
def create_organization():
    if request.method == 'POST':
        from app.models.admin.organization import Organization, OrganizationMembership, Role
        from flask import session
        
        org_name = request.form.get('name')
        new_org = Organization(name=org_name)
        db.session.add(new_org)
        db.session.flush()
        
        # Create Admin membership for current user
        admin_role = Role.query.filter_by(name='ADMIN').first()
        if not admin_role:
            admin_role = Role(name='ADMIN')
            db.session.add(admin_role)
            db.session.flush()
            
        membership = OrganizationMembership(
            user_id=current_user.id,
            organization_id=new_org.id,
            role_id=admin_role.id,
            is_owner=True
        )
        db.session.add(membership)
        db.session.commit()
        
        session['org_id'] = new_org.id
        
        # Seed standard chart of accounts for the new organization
        from app.services.account_service import seed_standard_accounts
        seed_standard_accounts(new_org.id)
        
        flash(f"Business '{org_name}' created with a standard Chart of Accounts.", "success")
        return redirect(url_for('dashboard.index'))
        
    return render_template('settings/organization_create.html')

@settings_bp.route('/organizations/switch/<org_id>')
@login_required
def switch_organization(org_id):
    from app.models.admin.organization import OrganizationMembership
    from flask import session
    
    # Verify access
    membership = OrganizationMembership.query.filter_by(user_id=current_user.id, organization_id=org_id).first()
    if membership:
        session['org_id'] = org_id
        flash("Switched businesses.", "success")
    else:
        flash("You do not have access to that business.", "danger")
        
    return redirect(url_for('dashboard.index'))
@settings_bp.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    org = get_current_org()
    if request.method == 'POST':
        org.stripe_api_key = request.form.get('stripe_api_key')
        org.stripe_publishable_key = request.form.get('stripe_publishable_key')
        db.session.commit()
        flash("Payment settings updated.", "success")
        return redirect(url_for('settings.payments'))
        
    return render_template('settings/payments.html', org=org)
@settings_bp.route('/tax-nexus', methods=['GET', 'POST'])
@login_required
def tax_nexus():
    from app.models.accounting.tax_nexus import TaxNexus
    from app.services.tax_service import TaxService
    org = get_current_org()
    
    # Seed mock rates if needed
    TaxService.seed_mock_rates()
    
    if request.method == 'POST':
        state_code = request.form.get('state_code')
        TaxService.register_nexus(org.id, state_code)
        flash(f"Nexus registered for {state_code}.", "success")
        return redirect(url_for('settings.tax_nexus'))
        
    nexus_list = TaxNexus.query.filter_by(organization_id=org.id).all()
    return render_template('settings/tax_nexus.html', nexus_list=nexus_list)
@settings_bp.route('/organizations/delete', methods=['POST'])
@login_required
def delete_organization():
    org = get_current_org()
    from app.models.admin.organization import Organization, OrganizationMembership
    from flask import session
    
    # Verify ownership
    membership = OrganizationMembership.query.filter_by(user_id=current_user.id, organization_id=org.id).first()
    if not membership or not membership.is_owner:
        flash("Only the business owner can delete this company.", "danger")
        return redirect(url_for('settings.index'))
    
    org_name = org.name
    
    # In a real app, you would have cascading deletes or soft deletes.
    # For this implementation, we will delete the memberships and the organization.
    OrganizationMembership.query.filter_by(organization_id=org.id).delete()
    db.session.delete(org)
    db.session.commit()
    
    # Clear org from session
    session.pop('org_id', None)
    
    # Try to find another organization to switch to
    next_membership = OrganizationMembership.query.filter_by(user_id=current_user.id).first()
    if next_membership:
        session['org_id'] = next_membership.organization_id
        flash(f"Business '{org_name}' has been deleted. Switched to your next available business.", "success")
        return redirect(url_for('dashboard.index'))
    else:
        flash(f"Business '{org_name}' has been deleted. Please create a new business to continue.", "info")
        return redirect(url_for('settings.create_organization'))
