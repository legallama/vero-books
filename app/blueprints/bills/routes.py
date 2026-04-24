from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from . import bills_bp
from app.models.purchases.bill import Bill, BillLine
from app.models.accounting.payment import BillPayment
from app.models.crm.contact import Vendor
from app.models.accounting.account import Account
from app.extensions import db
from app.services.auth_service import get_current_org
from datetime import datetime, date

@bills_bp.route('/overview')
@login_required
def overview():
    org = get_current_org()
    today = date.today()
    
    # Summary stats
    unpaid_bills = Bill.query.filter_by(organization_id=org.id, status='OPEN').all()
    unpaid_total = sum(float(b.balance_due) for b in unpaid_bills)
    
    overdue_bills = [b for b in unpaid_bills if b.due_date < today]
    overdue_total = sum(float(b.balance_due) for b in overdue_bills)
    
    # Recent bills
    recent_bills = Bill.query.filter_by(organization_id=org.id).order_by(Bill.issue_date.desc()).limit(5).all()
    
    return render_template('expenses/overview.html', 
                         unpaid_total=unpaid_total, 
                         overdue_total=overdue_total,
                         recent_bills=recent_bills,
                         unpaid_count=len(unpaid_bills),
                         overdue_count=len(overdue_bills))

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

@bills_bp.route('/payments')
@login_required
def payments():
    org = get_current_org()
    payments = BillPayment.query.filter_by(organization_id=org.id).order_by(BillPayment.payment_date.desc()).all()
    return render_template('bills/payments.html', payments=payments)
