from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.accounting.recurring_journal import RecurringJournalEntry, RecurringJournalLine
from app.models.accounting.account import Account
from app.services.auth_service import get_current_org
from app import db
from datetime import datetime

from ._bp import recurring_journal_bp

@recurring_journal_bp.route('/')
@login_required
def index():
    org = get_current_org()
    templates = RecurringJournalEntry.query.filter_by(organization_id=org.id).all()
    return render_template('accounting/recurring_journal/index.html', templates=templates)

@recurring_journal_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    if request.method == 'POST':
        name = request.form.get('name')
        frequency = request.form.get('frequency')
        memo = request.form.get('memo')
        
        template = RecurringJournalEntry(
            organization_id=org.id,
            name=name,
            frequency=frequency,
            memo=memo,
            created_by=current_user.id
        )
        
        # Parse lines
        # (Simplified for now, expecting at least two lines)
        db.session.add(template)
        db.session.commit()
        
        flash('Recurring transaction template created!', 'success')
        return redirect(url_for('recurring_journal.index'))
    
    accounts = Account.query.filter_by(organization_id=org.id).order_by(Account.code).all()
    return render_template('accounting/recurring_journal/create.html', accounts=accounts)
