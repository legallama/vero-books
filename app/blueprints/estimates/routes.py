from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from ._bp import estimates_bp
from app.models.sales.estimate import Estimate
from app.models.crm.contact import Customer
from app.services.auth_service import get_current_org
from app.extensions import db
from datetime import datetime

@estimates_bp.route('/')
@login_required
def index():
    org = get_current_org()
    estimates = Estimate.query.filter_by(organization_id=org.id).order_by(Estimate.issue_date.desc()).all()
    return render_template('estimates/index.html', estimates=estimates)

@estimates_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    customers = Customer.query.filter_by(organization_id=org.id, is_active=True).all()
    
    if request.method == 'POST':
        # logic placeholder
        flash("Estimate created.", "success")
        return redirect(url_for('estimates.index'))
        
    return render_template('estimates/create.html', customers=customers)
