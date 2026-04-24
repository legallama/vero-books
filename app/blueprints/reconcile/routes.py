from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
reconciliation_bp = Blueprint('reconciliation', __name__)
from app.models.accounting.account import Account
from app.models.accounting.journal import JournalLine
from app.models.accounting.reconciliation import Reconciliation
from app import db
from app.services.auth_service import get_current_org
from datetime import datetime

@reconciliation_bp.route('/')
@login_required
def index():
    org = get_current_org()
    # Find Bank and Credit Card accounts
    accounts = Account.query.filter_by(organization_id=org.id).filter(
        (Account.type == 'Asset') | (Account.type == 'Liability')
    ).all()
    
    # Filter for bank-like accounts
    bank_accounts = [a for a in accounts if any(keyword in a.name.lower() for keyword in ['checking', 'savings', 'credit card', 'line of credit', 'bank'])]
    
    # Get last reconciliation for each account
    for acc in bank_accounts:
        acc.last_recon = Reconciliation.query.filter_by(account_id=acc.id).order_by(Reconciliation.statement_date.desc()).first()
    
    return render_template('reconciliation/index.html', accounts=bank_accounts)

@reconciliation_bp.route('/start/<string:account_id>', methods=['GET', 'POST'])
@login_required
def start(account_id):
    org = get_current_org()
    account = Account.query.filter_by(id=account_id, organization_id=org.id).first_or_404()
    
    if request.method == 'POST':
        date_str = request.form.get('statement_date')
        balance_str = request.form.get('statement_balance')
        
        if not date_str or not balance_str:
            flash('Please enter both statement date and ending balance.', 'danger')
            return redirect(url_for('reconciliation.start', account_id=account.id))
            
        statement_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        statement_balance = float(balance_str)
        
        # Calculate starting balance (sum of all cleared transactions to date)
        # For Assets: Debits - Credits
        # For Liabilities: Credits - Debits
        starting_balance = 0.0
        cleared_lines = JournalLine.query.filter_by(account_id=account.id, cleared=True).all()
        for line in cleared_lines:
            if account.type == 'Asset':
                starting_balance += float(line.debit - line.credit)
            else:
                starting_balance += float(line.credit - line.debit)
        
        recon = Reconciliation(
            organization_id=org.id,
            account_id=account.id,
            user_id=current_user.id,
            statement_date=statement_date,
            statement_balance=statement_balance,
            starting_balance=starting_balance
        )
        db.session.add(recon)
        db.session.commit()
        
        return redirect(url_for('reconciliation.match', recon_id=recon.id))

    # Get last reconciliation to suggest starting balance
    last_recon = Reconciliation.query.filter_by(account_id=account.id).order_by(Reconciliation.statement_date.desc()).first()
    suggested_start = last_recon.statement_balance if last_recon else 0.0

    return render_template('reconciliation/start.html', account=account, suggested_start=suggested_start)

@reconciliation_bp.route('/match/<int:recon_id>', methods=['GET', 'POST'])
@login_required
def match(recon_id):
    org = get_current_org()
    recon = Reconciliation.query.filter_by(id=recon_id, organization_id=org.id).first_or_404()
    
    if request.method == 'POST':
        # If finishing
        if 'finish' in request.form:
            recon.status = 'COMPLETED'
            recon.completed_at = datetime.utcnow()
            db.session.commit()
            flash(f'Reconciliation for {recon.account.name} completed successfully!', 'success')
            return redirect(url_for('reconciliation.index'))

    # Get uncleared transactions for this account
    lines = JournalLine.query.filter_by(account_id=recon.account_id, cleared=False).order_by(JournalLine.id).all()
    
    return render_template('reconciliation/match.html', recon=recon, lines=lines)

@reconciliation_bp.route('/toggle_line/<int:recon_id>/<string:line_id>', methods=['POST'])
@login_required
def toggle_line(recon_id, line_id):
    org = get_current_org()
    recon = Reconciliation.query.filter_by(id=recon_id, organization_id=org.id).first_or_404()
    line = JournalLine.query.filter_by(id=line_id, account_id=recon.account_id).first_or_404()
    
    line.cleared = not line.cleared
    if line.cleared:
        line.reconciliation_id = recon.id
    else:
        line.reconciliation_id = None
        
    db.session.commit()
    return {'success': True, 'cleared': line.cleared}
