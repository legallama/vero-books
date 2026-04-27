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

@bills_bp.route('/pay/<string:bill_id>', methods=['GET', 'POST'])
@login_required
def pay(bill_id):
    org = get_current_org()
    from app.models.banking.bank_account import BankAccount
    from app.services.ledger_service import LedgerService
    
    bill = Bill.query.filter_by(id=bill_id, organization_id=org.id).first_or_404()
    bank_accounts = BankAccount.query.filter_by(organization_id=org.id).filter(BankAccount.account_id != None).all()
    
    if request.method == 'POST':
        bank_account_id = request.form.get('bank_account_id')
        payment_date_str = request.form.get('payment_date')
        amount_str = request.form.get('amount')
        reference = request.form.get('reference')
        
        try:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            amount = float(amount_str)
        except:
            flash("Invalid date or amount.", "danger")
            return redirect(url_for('bills.pay', bill_id=bill_id))
            
        if amount <= 0 or amount > bill.balance_due:
            flash(f"Payment amount must be between 0.01 and {bill.balance_due}.", "danger")
            return redirect(url_for('bills.pay', bill_id=bill_id))
            
        # 1. Record in Ledger
        from flask_login import current_user
        success, result = LedgerService.record_bill_payment(
            bill_id=bill.id,
            bank_account_id=bank_account_id,
            amount=amount,
            payment_date=payment_date,
            user_id=current_user.id,
            organization_id=org.id,
            reference=reference
        )
        
        if success:
            # 2. Record Payment Object
            payment = BillPayment(
                organization_id=org.id,
                bill_id=bill.id,
                bank_account_id=bank_account_id,
                payment_date=payment_date,
                amount=amount,
                reference=reference
            )
            db.session.add(payment)
            
            # 3. Update Bill
            bill.balance_due = float(bill.balance_due) - amount
            if bill.balance_due <= 0:
                bill.status = 'PAID'
            else:
                bill.status = 'PARTIAL'
                
            db.session.commit()
            flash(f"Payment of ${amount:,.2f} recorded for Bill {bill.bill_number}.", "success")
            return redirect(url_for('bills.index'))
        else:
            flash(f"Error recording payment: {result}", "danger")
            
    return render_template('bills/pay.html', bill=bill, bank_accounts=bank_accounts, today=date.today().strftime('%Y-%m-%d'))

@bills_bp.route('/payments')
@login_required
def payments():
    org = get_current_org()
    payments = BillPayment.query.filter_by(organization_id=org.id).order_by(BillPayment.payment_date.desc()).all()
    return render_template('bills/payments.html', payments=payments)


