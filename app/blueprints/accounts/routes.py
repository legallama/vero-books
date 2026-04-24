from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ._bp import accounts_bp
from ...models.accounting.account import Account, AccountType
from ...extensions import db
from ...services.auth_service import get_current_org

@accounts_bp.route('/')
@login_required
def index():
    org = get_current_org()
    if not org:
        flash("No active organization found.", "error")
        return redirect(url_for('dashboard.index'))
        
    accounts = Account.query.filter_by(organization_id=org.id).order_by(Account.code).all()
    return render_template('accounts/index.html', accounts=accounts, types=[t.value for t in AccountType])

@accounts_bp.route('/create', methods=['POST'])
@login_required
def create():
    org = get_current_org()
    code = request.form.get('code')
    name = request.form.get('name')
    acc_type = request.form.get('type')
    subtype = request.form.get('subtype')
    
    new_acc = Account(
        organization_id=org.id,
        code=code,
        name=name,
        type=acc_type,
        subtype=subtype
    )
    db.session.add(new_acc)
    db.session.commit()
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/<acc_id>/update', methods=['POST'])
@login_required
def update(acc_id):
    org = get_current_org()
    acc = Account.query.filter_by(id=acc_id, organization_id=org.id).first_or_404()
    
    acc.code = request.form.get('code')
    acc.name = request.form.get('name')
    acc.type = request.form.get('type')
    acc.subtype = request.form.get('subtype')
    
    db.session.commit()
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/import-qb', methods=['POST'])
@login_required
def import_qb():
    import csv
    import io
    
    org = get_current_org()
    if 'qb_csv' not in request.files:
        flash("No CSV file provided.", "error")
        return redirect(url_for('accounts.index'))
        
    file = request.files['qb_csv']
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('accounts.index'))
        
    try:
        # Read the CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_input:
            # QuickBooks CSVs can have various column names like "Account", "Name", "Type", "Detail Type"
            # We'll normalize keys by extracting lowercased fields
            lowered_row = {k.lower().strip(): v for k, v in row.items() if k}
            
            # Identify core fields from typical QB outputs
            name = lowered_row.get('account') or lowered_row.get('name') or lowered_row.get('account name')
            acc_type = lowered_row.get('type') or lowered_row.get('account type') or 'Expense'
            subtype = lowered_row.get('detail type') or ''
            
            if not name:
                continue # Skip raw header/footer junk
                
            # Attempt to extract code if Name looks like "1010 - Checking"
            code = ""
            if " - " in name and name.split(" - ")[0].strip().isdigit():
                parts = name.split(" - ")
                code = parts[0].strip()
                name = " - ".join(parts[1:]).strip()
            
            # Check if exists to avoid duplicates
            existing = Account.query.filter_by(organization_id=org.id, name=name).first()
            if not existing:
                new_acc = Account(
                    organization_id=org.id,
                    code=code,
                    name=name,
                    type=acc_type,
                    subtype=subtype
                )
                db.session.add(new_acc)
                imported_count += 1
                
        db.session.commit()
        flash(f"Successfully imported {imported_count} accounts from QuickBooks.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error parsing QuickBooks Data: {str(e)}", "danger")
        
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/<acc_id>/register')
@login_required
def register(acc_id):
    """Full check register for a single GL account — like QuickBooks register view."""
    org = get_current_org()
    account = Account.query.filter_by(id=acc_id, organization_id=org.id).first_or_404()
    
    from ...models.accounting.journal import JournalEntry, JournalLine
    from decimal import Decimal
    
    # Get all posted journal lines for this account, ordered by date
    lines = db.session.query(JournalLine).join(JournalEntry).filter(
        JournalEntry.organization_id == org.id,
        JournalEntry.status == 'POSTED',
        JournalLine.account_id == acc_id
    ).order_by(JournalEntry.entry_date.asc(), JournalEntry.posted_at.asc()).all()
    
    # Build register with running balance
    register_entries = []
    running_balance = Decimal('0.00')
    
    for line in lines:
        je = line.journal_entry
        debit = Decimal(str(line.debit or 0))
        credit = Decimal(str(line.credit or 0))
        
        # For Asset/Expense accounts: debits increase, credits decrease
        # For Liability/Equity/Income: credits increase, debits decrease
        if account.type in ('Asset', 'Expense'):
            running_balance += (debit - credit)
        else:
            running_balance += (credit - debit)
        
        # Determine the "other account" (the contra account in the journal entry)
        other_accounts = []
        for other_line in je.lines:
            if other_line.id != line.id:
                other_accounts.append(other_line.account)
        
        register_entries.append({
            'date': je.entry_date,
            'entry_number': je.entry_number,
            'entry_id': je.id,
            'memo': je.memo or line.description or '',
            'description': line.description or je.memo or '',
            'payee': '',  # Could be extracted from memo or linked customer/vendor
            'debit': debit,
            'credit': credit,
            'balance': running_balance,
            'other_accounts': other_accounts,
            'source_type': je.source_type or 'MANUAL',
            'status': je.status,
        })
    
    # Get all accounts for the quick-entry category dropdown
    all_accounts = Account.query.filter(
        Account.organization_id == org.id,
        Account.id != acc_id,
        Account.is_active == True
    ).order_by(Account.type, Account.code).all()
    
    return render_template('accounts/register.html',
        account=account,
        register_entries=register_entries,
        running_balance=running_balance,
        all_accounts=all_accounts
    )

@accounts_bp.route('/<acc_id>/register/quick-entry', methods=['POST'])
@login_required
def quick_entry(acc_id):
    """QuickBooks-style quick entry directly from the check register."""
    org = get_current_org()
    account = Account.query.filter_by(id=acc_id, organization_id=org.id).first_or_404()
    
    from ...models.accounting.journal import JournalEntry, JournalLine
    from ...services.ledger_service import LedgerService
    from datetime import datetime
    import time
    
    date_str = request.form.get('date')
    description = request.form.get('description', '').strip()
    category_id = request.form.get('category_id')
    tx_type = request.form.get('type')  # 'payment' or 'deposit'
    amount_str = request.form.get('amount', '0')
    
    if not date_str or not description or not category_id or not amount_str:
        flash('Please fill in all required fields.', 'warning')
        return redirect(url_for('accounts.register', acc_id=acc_id))
    
    try:
        amount = abs(float(amount_str))
    except ValueError:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('accounts.register', acc_id=acc_id))
    
    if amount == 0:
        flash('Amount must be greater than zero.', 'warning')
        return redirect(url_for('accounts.register', acc_id=acc_id))
    
    tx_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Verify the category account exists
    category_account = Account.query.filter_by(id=category_id, organization_id=org.id).first()
    if not category_account:
        flash('Invalid category account selected.', 'danger')
        return redirect(url_for('accounts.register', acc_id=acc_id))
    
    # Create a balanced journal entry
    je = JournalEntry(
        organization_id=org.id,
        entry_number=f"REG-{int(time.time())}",
        entry_date=tx_date,
        memo=description,
        source_type='REGISTER',
        status='DRAFT',
        created_by=current_user.id
    )
    db.session.add(je)
    db.session.flush()
    
    # For Asset/Expense accounts:
    #   Payment (money going out) = Credit this account, Debit the category
    #   Deposit (money coming in) = Debit this account, Credit the category
    if account.type in ('Asset', 'Expense'):
        if tx_type == 'payment':
            this_line = JournalLine(journal_entry_id=je.id, account_id=acc_id, credit=amount, debit=0, description=description)
            cat_line = JournalLine(journal_entry_id=je.id, account_id=category_id, debit=amount, credit=0, description=description)
        else:  # deposit
            this_line = JournalLine(journal_entry_id=je.id, account_id=acc_id, debit=amount, credit=0, description=description)
            cat_line = JournalLine(journal_entry_id=je.id, account_id=category_id, credit=amount, debit=0, description=description)
    else:
        # For Liability/Equity/Income accounts:
        #   Payment = Debit this account (reduce liability), Credit category
        #   Deposit = Credit this account (increase liability), Debit category
        if tx_type == 'payment':
            this_line = JournalLine(journal_entry_id=je.id, account_id=acc_id, debit=amount, credit=0, description=description)
            cat_line = JournalLine(journal_entry_id=je.id, account_id=category_id, credit=amount, debit=0, description=description)
        else:  # deposit
            this_line = JournalLine(journal_entry_id=je.id, account_id=acc_id, credit=amount, debit=0, description=description)
            cat_line = JournalLine(journal_entry_id=je.id, account_id=category_id, debit=amount, credit=0, description=description)
    
    db.session.add(this_line)
    db.session.add(cat_line)
    db.session.flush()
    
    # Auto-post the entry
    success, msg = LedgerService.post_journal_entry(je.id, current_user.id, org.id)
    if not success:
        flash(f'Entry created but could not be posted: {msg}', 'warning')
    else:
        flash(f'Transaction recorded and posted to ledger.', 'success')
    
    return redirect(url_for('accounts.register', acc_id=acc_id))

