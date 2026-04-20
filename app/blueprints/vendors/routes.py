from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from . import vendors_bp
from app.models.crm.contact import Vendor
from app.extensions import db
from app.services.auth_service import get_current_org

@vendors_bp.route('/')
@login_required
def index():
    org = get_current_org()
    vendors = Vendor.query.filter_by(organization_id=org.id).order_by(Vendor.display_name).all()
    return render_template('vendors/index.html', vendors=vendors)

@vendors_bp.route('/create', methods=['POST'])
@login_required
def create():
    org = get_current_org()
    display_name = request.form.get('display_name')
    company_name = request.form.get('company_name')
    email = request.form.get('email')
    
    new_vendor = Vendor(
        organization_id=org.id,
        display_name=display_name,
        company_name=company_name,
        email=email
    )
    db.session.add(new_vendor)
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        vendors = Vendor.query.filter_by(organization_id=org.id).order_by(Vendor.display_name).all()
        return render_template('vendors/_vendor_list.html', vendors=vendors)
        
    return redirect(url_for('vendors.index'))
