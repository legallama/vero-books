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
