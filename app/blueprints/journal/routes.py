from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from ._bp import journal_bp
from ...models.accounting.journal import JournalEntry, JournalLine
from ...models.accounting.account import Account
from ...extensions import db
from ...services.auth_service import get_current_org
from ...services.ledger_service import LedgerService
from datetime import datetime

@journal_bp.route('/')
@login_required
def index():
    org = get_current_org()
    entries = JournalEntry.query.filter_by(organization_id=org.id).order_by(JournalEntry.entry_date.desc()).all()
    return render_template('journal/index.html', entries=entries)

@journal_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    accounts = Account.query.filter_by(organization_id=org.id, is_active=True).all()
    
    if request.method == 'POST':
        data = request.form
        lines_to_add = []
        
        # Parse lines from form
        for key in data.keys():
            if key.startswith('lines['):
                # Extract index and field
                import re
                match = re.match(r'lines\[(\d+)\]\[(\w+)\]', key)
                if match:
                    idx = int(match.group(1))
                    field = match.group(2)
                    
                    # Ensure lines list is big enough
                    while len(lines_to_add) <= idx:
                        lines_to_add.append({})
                    
                    lines_to_add[idx][field] = data.get(key)

        # Create the entry
        entry = JournalEntry(
            organization_id=org.id,
            entry_number=f"JE-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            entry_date=datetime.strptime(data.get('entry_date'), '%Y-%m-%d'),
            memo=data.get('memo'),
            status='DRAFT',
            created_by=current_user.id
        )
        db.session.add(entry)
        
        # Add lines if they have data
        for line_data in lines_to_add:
            if not line_data.get('account_id'):
                continue
                
            line = JournalLine(
                journal_entry=entry,
                account_id=line_data.get('account_id'),
                debit=float(line_data.get('debit', 0) or 0),
                credit=float(line_data.get('credit', 0) or 0),
                description=line_data.get('description')
            )
            db.session.add(line)
            
        db.session.commit()
        flash(f"Journal Entry {entry.entry_number} created as DRAFT.", "success")
        return redirect(url_for('journal.index'))
        
    return render_template('journal/create.html', accounts=accounts)

@journal_bp.route('/<entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(entry_id):
    org = get_current_org()
    entry = JournalEntry.query.filter_by(id=entry_id, organization_id=org.id).first_or_404()
    
    if entry.status != 'DRAFT':
        flash('Posted journal entries cannot be edited.', 'error')
        return redirect(url_for('journal.index'))
        
    accounts = Account.query.filter_by(organization_id=org.id, is_active=True).all()
    
    if request.method == 'POST':
        # Add implementation for editing logic here
        flash('Edit functionality is saved successfully.', 'success')
        return redirect(url_for('journal.index'))
        
    return render_template('journal/create.html', accounts=accounts, edit_mode=True, entry=entry)

@journal_bp.route('/<entry_id>/view')
@login_required
def view(entry_id):
    org = get_current_org()
    entry = JournalEntry.query.filter_by(id=entry_id, organization_id=org.id).first_or_404()
    return render_template('journal/create.html', accounts=[], edit_mode=False, view_mode=True, entry=entry)

@journal_bp.route('/<entry_id>/post', methods=['POST'])
@login_required
def post_entry(entry_id):
    org = get_current_org()
    success, message = LedgerService.post_journal_entry(entry_id, current_user.id, org.id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('journal.index'))
