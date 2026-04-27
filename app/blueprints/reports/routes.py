from flask import render_template, request
from flask_login import login_required
from ._bp import reports_bp
from app.services.auth_service import get_current_org
from app.services.ledger_service import LedgerService

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/trial-balance')
@login_required
def trial_balance():
    org = get_current_org()
    report_data = LedgerService.get_trial_balance(org.id)
    
    total_debit = sum(line['debit'] for line in report_data)
    total_credit = sum(line['credit'] for line in report_data)
    
    return render_template('reports/trial_balance.html', 
                          report_data=report_data, 
                          total_debit=total_debit, 
                          total_credit=total_credit)

@reports_bp.route('/profit-and-loss')
@login_required
def profit_and_loss():
    org = get_current_org()
    from datetime import datetime, date
    start_date = date(date.today().year, date.today().month, 1)
    end_date = date.today()
    
    report = LedgerService.get_profit_and_loss(org.id, start_date, end_date)
    return render_template('reports/profit_and_loss.html', report=report, start_date=start_date, end_date=end_date)

@reports_bp.route('/balance-sheet')
@login_required
def balance_sheet():
    org = get_current_org()
    report = LedgerService.get_balance_sheet(org.id)
    return render_template('reports/balance_sheet.html', report=report)
@reports_bp.route('/aging-ar')
@login_required
def aging_ar():
    org = get_current_org()
    from app.models.sales.invoice import Invoice
    from datetime import date
    
    invoices = Invoice.query.filter(
        Invoice.organization_id == org.id,
        Invoice.status.in_(['OPEN', 'PARTIAL'])
    ).all()
    
    today = date.today()
    buckets = {'current': [], '1-30': [], '31-60': [], '61-90': [], '90+': []}
    
    for inv in invoices:
        diff = (today - inv.due_date).days
        if diff <= 0: buckets['current'].append(inv)
        elif diff <= 30: buckets['1-30'].append(inv)
        elif diff <= 60: buckets['31-60'].append(inv)
        elif diff <= 90: buckets['61-90'].append(inv)
        else: buckets['90+'].append(inv)
        
    return render_template('reports/aging_ar.html', buckets=buckets, today=today)

@reports_bp.route('/aging-ap')
@login_required
def aging_ap():
    org = get_current_org()
    from app.models.purchases.bill import Bill
    from datetime import date
    
    bills = Bill.query.filter(
        Bill.organization_id == org.id,
        Bill.status.in_(['OPEN', 'PARTIAL'])
    ).all()
    
    today = date.today()
    buckets = {'current': [], '1-30': [], '31-60': [], '61-90': [], '90+': []}
    
    for bill in bills:
        diff = (today - bill.due_date).days
        if diff <= 0: buckets['current'].append(bill)
        elif diff <= 30: buckets['1-30'].append(bill)
        elif diff <= 60: buckets['31-60'].append(bill)
        elif diff <= 90: buckets['61-90'].append(bill)
        else: buckets['90+'].append(bill)
        
    return render_template('reports/aging_ap.html', buckets=buckets, today=today)
