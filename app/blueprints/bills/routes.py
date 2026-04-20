from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from . import bills_bp
from app.models.purchases.bill import Bill, BillLine
from app.models.crm.contact import Vendor
from app.models.accounting.account import Account
from app.extensions import db
from app.services.auth_service import get_current_org
from datetime import datetime

@bills_bp.route('/')
@login_required
def index():
    org = get_current_org()
    bills = Bill.query.filter_by(organization_id=org.id).order_by(Bill.issue_date.desc()).all()
    return render_template('bills/index.html', bills=bills)

@bills_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    vendors = Vendor.query.filter_by(organization_id=org.id, is_active=True).all()
    accounts = Account.query.filter_by(organization_id=org.id, type='Expense', is_active=True).all()
    
    if request.method == 'POST':
        # logic placeholder
        flash("Bill created.", "success")
        return redirect(url_for('bills.index'))
        
    return render_template('bills/create.html', vendors=vendors, accounts=accounts)
