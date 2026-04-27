from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from . import payroll_bp
from app.models.admin.payroll import Employee, PayrollRun, Paycheck
from app.models.accounting.journal import JournalEntry, JournalLine
from app.services.auth_service import get_current_org, require_role
from app.extensions import db
from datetime import datetime, date
from decimal import Decimal

@payroll_bp.route('/')
@login_required
def index():
    org = get_current_org()
    employees = Employee.query.filter_by(organization_id=org.id).all()
    recent_runs = PayrollRun.query.filter_by(organization_id=org.id).order_by(PayrollRun.payment_date.desc()).limit(10).all()
    
    return render_template('payroll/index.html', 
                           employees=employees, 
                           recent_runs=recent_runs)

@payroll_bp.route('/employees/new', methods=['GET', 'POST'])
@login_required
@require_role(['ADMIN', 'ACCOUNTANT'])
def create_employee():
    org = get_current_org()
    if request.method == 'POST':
        new_emp = Employee(
            organization_id=org.id,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            ssn_last4=request.form.get('ssn_last4'),
            pay_type=request.form.get('pay_type'),
            pay_rate=Decimal(request.form.get('pay_rate', '0')),
            pay_frequency=request.form.get('pay_frequency'),
            filing_status=request.form.get('filing_status'),
            hired_at=datetime.strptime(request.form.get('hired_at'), '%Y-%m-%d').date() if request.form.get('hired_at') else date.today()
        )
        db.session.add(new_emp)
        db.session.commit()
        flash(f"Employee {new_emp.full_name} added successfully.", "success")
        return redirect(url_for('payroll.index'))
    
    return render_template('payroll/employee_form.html')

@payroll_bp.route('/run/new', methods=['GET', 'POST'])
@login_required
@require_role(['ADMIN', 'ACCOUNTANT'])
def run_payroll():
    org = get_current_org()
    employees = Employee.query.filter_by(organization_id=org.id, status='ACTIVE').all()
    
    if request.method == 'POST':
        # 1. Create the Payroll Run
        run = PayrollRun(
            organization_id=org.id,
            period_start=datetime.strptime(request.form.get('period_start'), '%Y-%m-%d').date(),
            period_end=datetime.strptime(request.form.get('period_end'), '%Y-%m-%d').date(),
            payment_date=datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date(),
            status='PAID' # For simplicity in this MVP
        )
        db.session.add(run)
        db.session.flush()
        
        total_gross = Decimal('0.00')
        total_taxes = Decimal('0.00')
        total_net = Decimal('0.00')
        
        for emp in employees:
            # Simple tax calculation logic (Mock for MVP)
            gross = emp.pay_rate
            if emp.pay_frequency == 'BIWEEKLY' and emp.pay_type == 'SALARY':
                gross = emp.pay_rate / Decimal('26')
            
            fed_tax = gross * Decimal('0.10') # 10% flat mock
            state_tax = gross * Decimal('0.05') # 5% flat mock
            ss_tax = gross * Decimal('0.062') # 6.2%
            med_tax = gross * Decimal('0.0145') # 1.45%
            
            taxes = fed_tax + state_tax + ss_tax + med_tax
            net = gross - taxes
            
            paycheck = Paycheck(
                payroll_run_id=run.id,
                employee_id=emp.id,
                gross_pay=gross,
                federal_tax=fed_tax,
                state_tax=state_tax,
                social_security=ss_tax,
                medicare=med_tax,
                net_pay=net,
                memo=f"Payroll Period {run.period_start} to {run.period_end}"
            )
            db.session.add(paycheck)
            
            total_gross += gross
            total_taxes += taxes
            total_net += net
            
        run.total_gross = total_gross
        run.total_taxes = total_taxes
        run.total_net = total_net
        
        # 2. Post to Ledger
        # Find Payroll Expense and Tax Liability accounts
        from app.models.accounting.account import Account
        payroll_expense = Account.query.filter_by(organization_id=org.id, name='Payroll Expense').first()
        if not payroll_expense:
            payroll_expense = Account(organization_id=org.id, name='Payroll Expense', code='6000', type='Expense')
            db.session.add(payroll_expense)
            db.session.flush()
            
        tax_liability = Account.query.filter_by(organization_id=org.id, name='Payroll Tax Liability').first()
        if not tax_liability:
            tax_liability = Account(organization_id=org.id, name='Payroll Tax Liability', code='2200', type='Liability')
            db.session.add(tax_liability)
            db.session.flush()
            
        bank_account = Account.query.filter_by(organization_id=org.id, type='Asset', subtype='Bank').first()
        
        je = JournalEntry(
            organization_id=org.id,
            entry_number=f"PR-{int(datetime.utcnow().timestamp())}",
            entry_date=datetime.combine(run.payment_date, datetime.min.time()),
            memo=f"Payroll Run: {run.period_start} to {run.period_end}",
            status='POSTED',
            created_by=current_user.id
        )
        db.session.add(je)
        db.session.flush()
        
        # DR Payroll Expense (Gross)
        db.session.add(JournalLine(journal_entry_id=je.id, account_id=payroll_expense.id, debit=total_gross, description="Gross Payroll"))
        # CR Tax Liability
        db.session.add(JournalLine(journal_entry_id=je.id, account_id=tax_liability.id, credit=total_taxes, description="Payroll Taxes Withheld"))
        # CR Bank (Net)
        if bank_account:
            db.session.add(JournalLine(journal_entry_id=je.id, account_id=bank_account.id, credit=total_net, description="Net Payroll Payment"))
        
        run.journal_entry_id = je.id
        db.session.commit()
        
        flash(f"Payroll processed for {len(employees)} employees. Total Net: ${total_net:,.2f}", "success")
        return redirect(url_for('payroll.index'))
        
    return render_template('payroll/run_wizard.html', employees=employees)
