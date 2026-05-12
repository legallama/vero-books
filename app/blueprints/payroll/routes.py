from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from . import payroll_bp
from app.models.admin.payroll import Employee, PayrollRun, Paycheck, TimeEntry
from app.models.banking.bank_account import BankAccount
from app.models.banking.check import Check
from app.models.accounting.journal import JournalEntry, JournalLine
from app.services.auth_service import get_current_org, require_role
from app.services.ledger_service import LedgerService
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
            pay_rate=Decimal(request.form.get('pay_rate') or '0'),
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
            gross = Decimal('0.00')
            hours_val = Decimal('0.00')

            if emp.pay_type == 'SALARY':
                if emp.pay_frequency == 'BIWEEKLY':
                    gross = emp.pay_rate / Decimal('26')
                else:
                    gross = emp.pay_rate # fallback
            else: # HOURLY
                # Sum PENDING time entries within the period
                entries = TimeEntry.query.filter(
                    TimeEntry.employee_id == emp.id,
                    TimeEntry.date >= run.period_start,
                    TimeEntry.date <= run.period_end,
                    TimeEntry.status == 'PENDING'
                ).all()
                
                hours_val = sum(entry.hours for entry in entries)
                gross = hours_val * emp.pay_rate
                
                # Mark entries as PROCESSED
                for entry in entries:
                    entry.status = 'PROCESSED'
            
            fed_tax = gross * Decimal('0.10') # 10% flat mock
            state_tax = gross * Decimal('0.05') # 5% flat mock
            ss_tax = gross * Decimal('0.062') # 6.2%
            med_tax = gross * Decimal('0.0145') # 1.45%
            
            taxes = fed_tax + state_tax + ss_tax + med_tax
            net = gross - taxes
            
            paycheck = Paycheck(
                payroll_run_id=run.id,
                employee_id=emp.id,
                hours_worked=hours_val,
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
        
        # 3. Create individual Check records for printing
        primary_bank = BankAccount.query.filter_by(organization_id=org.id, account_type='Checking').first()
        if primary_bank:
            # Re-fetch paychecks for this run to create checks
            for emp_paycheck in run.paychecks:
                check_num = f"PR{datetime.utcnow().strftime('%y%m%d')}{emp_paycheck.employee.first_name[0]}{emp_paycheck.employee.last_name[0]}"
                new_check = Check(
                    organization_id=org.id,
                    bank_account_id=primary_bank.id,
                    check_number=check_num,
                    date=run.payment_date,
                    payee_name=emp_paycheck.employee.full_name,
                    payee_type='EMPLOYEE',
                    amount=emp_paycheck.net_pay,
                    memo=f"Payroll Period {run.period_start} to {run.period_end}",
                    status='DRAFT',
                    journal_entry_id=je.id
                )
                db.session.add(new_check)

        run.journal_entry_id = je.id
        db.session.commit()
        
        flash(f"Payroll processed for {len(employees)} employees. Total Net: ${total_net:,.2f}", "success")
        return redirect(url_for('payroll.index'))
        
    return render_template('payroll/run_wizard.html', employees=employees)

@payroll_bp.route('/time-tracking', methods=['GET', 'POST'])
@login_required
def time_tracking():
    org = get_current_org()
    employees = Employee.query.filter_by(organization_id=org.id, status='ACTIVE').all()
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        date_str = request.form.get('date')
        hours = request.form.get('hours')
        description = request.form.get('description')
        
        entry = TimeEntry(
            organization_id=org.id,
            employee_id=employee_id,
            date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today(),
            hours=Decimal(hours or '0'),
            description=description
        )
        db.session.add(entry)
        db.session.commit()
        flash("Time entry recorded successfully.", "success")
        return redirect(url_for('payroll.time_tracking'))

    # Get recent entries
    entries = TimeEntry.query.filter_by(organization_id=org.id).order_by(TimeEntry.date.desc()).limit(50).all()
    return render_template('payroll/time_tracking.html', employees=employees, entries=entries, today=date.today().strftime('%Y-%m-%d'))

@payroll_bp.route('/run/<run_id>/void', methods=['POST'])
@login_required
@require_role(['ADMIN', 'ACCOUNTANT'])
def void_payroll_run(run_id):
    org = get_current_org()
    run = PayrollRun.query.filter_by(id=run_id, organization_id=org.id).first_or_404()
    
    if run.status == 'VOID':
        flash("This payroll run is already voided.", "warning")
        return redirect(url_for('payroll.index'))

    # 1. Handle the Journal Entry
    if run.journal_entry_id:
        from app.models.accounting.journal import JournalEntry
        je = JournalEntry.query.filter_by(id=run.journal_entry_id, organization_id=org.id).first()
        if je:
            if je.status == 'POSTED':
                success, msg = LedgerService.reverse_journal_entry(
                    run.journal_entry_id, 
                    current_user.id, 
                    org.id, 
                    f"Voiding Payroll Run for period {run.period_start} to {run.period_end}"
                )
                if not success:
                    flash(f"Error reversing ledger entry: {msg}", "danger")
                    return redirect(url_for('payroll.index'))
            elif je.status == 'DRAFT':
                # If it's still a draft, we can just delete it
                db.session.delete(je)
            elif je.status == 'REVERSED':
                pass # Already handled

    # 2. Void or Delete Check records
    # Finding checks linked to this run's journal entry
    checks = Check.query.filter_by(journal_entry_id=run.journal_entry_id, organization_id=org.id).all()
    for check in checks:
        check.status = 'VOID'
        check.memo = f"VOID: {check.memo}"

    # 3. Reset Time Entries to PENDING
    # We find processed time entries for these employees within the period
    employee_ids = [p.employee_id for p in run.paychecks]
    affected_entries = TimeEntry.query.filter(
        TimeEntry.employee_id.in_(employee_ids),
        TimeEntry.date >= run.period_start,
        TimeEntry.date <= run.period_end,
        TimeEntry.status == 'PROCESSED'
    ).all()
    
    for entry in affected_entries:
        entry.status = 'PENDING'

    # 4. Update Run Status
    run.status = 'VOID'
    db.session.commit()
    
    flash("Payroll run has been voided. Journal entries reversed and time entries reset.", "success")
    return redirect(url_for('payroll.index'))

@payroll_bp.route('/employees/<employee_id>/delete', methods=['POST'])
@login_required
@require_role(['ADMIN', 'ACCOUNTANT'])
def delete_employee(employee_id):
    org = get_current_org()
    employee = Employee.query.filter_by(id=employee_id, organization_id=org.id).first_or_404()
    
    # Check if employee has paychecks
    if employee.paychecks:
        flash(f"Cannot delete {employee.full_name} because they have paycheck history. Set their status to 'INACTIVE' instead.", "warning")
        return redirect(url_for('payroll.index'))
        
    db.session.delete(employee)
    db.session.commit()
    flash(f"Employee {employee.full_name} has been deleted.", "info")
    return redirect(url_for('payroll.index'))

@payroll_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role(['ADMIN', 'ACCOUNTANT'])
def edit_employee(employee_id):
    org = get_current_org()
    employee = Employee.query.filter_by(id=employee_id, organization_id=org.id).first_or_404()
    
    if request.method == 'POST':
        employee.first_name = request.form.get('first_name')
        employee.last_name = request.form.get('last_name')
        employee.email = request.form.get('email')
        employee.ssn_last4 = request.form.get('ssn_last4')
        employee.pay_type = request.form.get('pay_type')
        employee.pay_rate = Decimal(request.form.get('pay_rate') or '0')
        employee.pay_frequency = request.form.get('pay_frequency')
        employee.filing_status = request.form.get('filing_status')
        employee.federal_allowances = int(request.form.get('federal_allowances', 0))
        employee.status = request.form.get('status', employee.status)
        
        if request.form.get('hired_at'):
            try:
                employee.hired_at = datetime.strptime(request.form.get('hired_at'), '%Y-%m-%d').date()
            except ValueError:
                pass
            
        db.session.commit()
        flash(f"Employee {employee.full_name} updated successfully.", "success")
        return redirect(url_for('payroll.index'))
    
    return render_template('payroll/employee_form.html', employee=employee)
