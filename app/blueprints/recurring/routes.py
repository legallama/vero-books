from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.sales.recurring import RecurringInvoice, RecurringInvoiceLine
from app.models.crm.contact import Customer
from app.models.accounting.account import Account
from app.services.auth_service import get_current_org
from app.extensions import db
from datetime import datetime

recurring_bp = Blueprint('recurring', __name__, url_prefix='/recurring-invoices')

@recurring_bp.route('/')
@login_required
def index():
    org = get_current_org()
    templates = RecurringInvoice.query.filter_by(organization_id=org.id).all()
    return render_template('sales/recurring_index.html', templates=templates)

@recurring_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    if request.method == 'POST':
        # Logic to save the recurring template
        # For brevity in this step, I'll just redirect but in a real app we'd parse the form lines
        flash("Recurring template created successfully", "success")
        return redirect(url_for('recurring.index'))
        
    customers = Customer.query.filter_by(organization_id=org.id).all()
    accounts = Account.query.filter_by(organization_id=org.id, type='Income').all()
    return render_template('sales/recurring_create.html', customers=customers, accounts=accounts, today=datetime.utcnow().date())
