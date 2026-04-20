from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ._bp import banking_bp
from app.models.banking.bank_account import BankAccount, BankTransaction
from app.services.auth_service import get_current_org
from app.extensions import db

@banking_bp.route('/')
@login_required
def index():
    org = get_current_org()
    from app.models.banking.bank_account import BankAccount, BankTransaction
    from app.models.accounting.bank_rule import BankRule
    
    accounts = BankAccount.query.filter_by(organization_id=org.id).all()
    transactions = BankTransaction.query.filter_by(organization_id=org.id).order_by(BankTransaction.date.desc()).limit(50).all()
    active_rules = BankRule.query.filter_by(organization_id=org.id, is_active=True).order_by(BankRule.priority.desc()).all()
    
    # Apply rules to transaction list for display
    for tx in transactions:
        tx.suggested_account = None
        tx.rule_name = None
        
        for rule in active_rules:
            match = False
            if rule.field_to_match == 'DESCRIPTION':
                if rule.match_type == 'CONTAINS' and rule.match_value.lower() in tx.description.lower():
                    match = True
                elif rule.match_type == 'EXACT' and rule.match_value.lower() == tx.description.lower():
                    match = True
            elif rule.field_to_match == 'AMOUNT':
                try:
                    val = float(rule.match_value)
                    if rule.match_type == 'EXACT' and float(tx.amount) == val:
                        match = True
                    elif rule.match_type == 'GREATER_THAN' and float(tx.amount) > val:
                        match = True
                except: pass
            
            if match:
                tx.suggested_account = rule.target_account
                tx.rule_name = rule.name
                break # First match wins based on priority
                
    from app.models.accounting.account import Account
    gl_accounts = Account.query.filter_by(organization_id=org.id).order_by(Account.name).all()
    return render_template('banking/index.html', accounts=accounts, transactions=transactions, gl_accounts=gl_accounts)

@banking_bp.route('/accounts/create', methods=['POST'])
@login_required
def create_account():
    org = get_current_org()
    name = request.form.get('name')
    acc_type = request.form.get('type')
    
    new_acc = BankAccount(
        organization_id=org.id,
        name=name,
        account_type=acc_type
    )
    db.session.add(new_acc)
    db.session.commit()
    flash("Bank account linked.", "success")
    return redirect(url_for('banking.index'))

@banking_bp.route('/transactions/manual', methods=['POST'])
@login_required
def manual_transaction():
    org = get_current_org()
    from app.models.banking.bank_account import BankTransaction
    from datetime import datetime
    
    tx_type = request.form.get('type')
    amount_str = request.form.get('amount', '0')
    try:
        amount = float(amount_str)
        if tx_type == 'withdrawal':
            amount = -abs(amount)
        else:
            amount = abs(amount)
    except ValueError:
        amount = 0.0
        
    date_str = request.form.get('date')
    tx_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    
    new_tx = BankTransaction(
        organization_id=org.id,
        bank_account_id=request.form.get('bank_account_id'),
        date=tx_date,
        description=request.form.get('description'),
        amount=amount,
        status='UNCATEGORIZED' # Will be caught by rules engine later
    )
    db.session.add(new_tx)
    db.session.commit()
    
    flash(f"Manual {tx_type} recorded successfully.", "success")
    return redirect(url_for('banking.index'))

@banking_bp.route('/accept-match/<tx_id>', methods=['POST'])
@login_required
def accept_match(tx_id):
    org = get_current_org()
    account_id = request.args.get('account_id') or request.form.get('account_id')
    
    # Get Transaction
    tx = BankTransaction.query.filter_by(id=tx_id, organization_id=org.id).first_or_404()
    
    if tx.status == 'MATCHED':
        flash('Transaction already matched.', 'warning')
        return redirect(url_for('banking.index'))
        
    from app.models.accounting.account import Account
    target_account = Account.query.filter_by(id=account_id, organization_id=org.id).first_or_404()
    
    # Map Bank Account to GL
    bank_account = tx.bank_account
    if not bank_account.account_id:
        gl_account = Account.query.filter_by(organization_id=org.id, name=bank_account.name).first()
        if not gl_account:
            gl_account = Account(organization_id=org.id, name=bank_account.name, code=bank_account.account_number_last4 or "1000", type="Asset", subtype="Bank")
            db.session.add(gl_account)
            db.session.flush()
        bank_account.account_id = gl_account.id
        
    # Create Journal Entry
    import time
    from app.models.accounting.journal import JournalEntry, JournalLine
    
    je = JournalEntry(
        organization_id=org.id,
        entry_number=f"BNK-{int(time.time())}",
        entry_date=tx.date,
        memo=f"Banking Feed: {tx.description}",
        source_type='BANK_FEED',
        source_id=tx.id,
        status='DRAFT'
    )
    db.session.add(je)
    db.session.flush()
    
    amount = abs(float(tx.amount))
    if float(tx.amount) > 0: # Deposit: Debit Bank, Credit Target
        bank_line = JournalLine(journal_entry_id=je.id, account_id=bank_account.account_id, debit=amount, description=tx.description)
        target_line = JournalLine(journal_entry_id=je.id, account_id=target_account.id, credit=amount, description=tx.description)
    else: # Withdrawal: Credit Bank, Debit Target
        bank_line = JournalLine(journal_entry_id=je.id, account_id=bank_account.account_id, credit=amount, description=tx.description)
        target_line = JournalLine(journal_entry_id=je.id, account_id=target_account.id, debit=amount, description=tx.description)
        
    db.session.add(bank_line)
    db.session.add(target_line)
    
    # Post it
    from app.services.ledger_service import LedgerService
    success, msg = LedgerService.post_journal_entry(je.id, current_user.id, org.id)
    if not success:
        flash(f"Error posting match to ledger: {msg}", "danger")
        return redirect(url_for('banking.index'))
        
    # Mark Match
    tx.status = 'MATCHED'
    tx.matched_source_type = 'JOURNAL_ENTRY'
    tx.matched_source_id = je.id
    
    db.session.commit()
    flash('Transaction mathematically categorized and added to the General Ledger.', 'success')
    return redirect(url_for('banking.index'))

@banking_bp.route('/delete-transaction/<tx_id>', methods=['POST'])
@login_required
def delete_transaction(tx_id):
    org = get_current_org()
    
    # Get Transaction
    tx = BankTransaction.query.filter_by(id=tx_id, organization_id=org.id).first_or_404()
    
    # Allow deletion. Technically if it's MATCHED, deleting it from the feed won't delete the journal entry, 
    # but that's acceptable for feed management. 
    db.session.delete(tx)
    db.session.commit()
    
    flash('Transaction removed from bank feed.', 'success')
    return redirect(url_for('banking.index'))

@banking_bp.route('/delete-transactions-batch', methods=['POST'])
@login_required
def delete_batch():
    org = get_current_org()
    
    tx_ids = request.form.getlist('tx_ids')
    if not tx_ids:
        flash('No transactions selected.', 'warning')
        return redirect(url_for('banking.index'))
        
    deleted_count = 0
    for tx_id in tx_ids:
        tx = BankTransaction.query.filter_by(id=tx_id, organization_id=org.id).first()
        if tx:
            db.session.delete(tx)
            deleted_count += 1
            
    db.session.commit()
    flash(f'{deleted_count} transactions permanently removed from bank feed.', 'success')
    return redirect(url_for('banking.index'))

@banking_bp.route('/import-statements', methods=['POST'])
@login_required
def import_statements():
    org = get_current_org()
    if 'statement_file' not in request.files:
        flash("No file provided.", "danger")
        return redirect(url_for('banking.index'))
        
    file = request.files['statement_file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('banking.index'))
        
    filename = file.filename.lower()
    imported_txs = 0
    from app.models.banking.bank_account import BankAccount, BankTransaction
    
    try:
        # ---- OFX / QBO PARSING ----
        if filename.endswith('.qbo') or filename.endswith('.ofx') or filename.endswith('.qfx'):
            from ofxparse import OfxParser
            ofx = OfxParser.parse(file.stream)
            
            for account in ofx.accounts:
                acct_num = account.account_id[-4:] if len(account.account_id) > 4 else account.account_id
                bank_acc = BankAccount.query.filter_by(organization_id=org.id, account_number_last4=acct_num).first()
                if not bank_acc:
                    bank_acc = BankAccount(
                        organization_id=org.id,
                        name=f"Bank Import ({acct_num})",
                        account_type="Checking",
                        account_number_last4=acct_num,
                        balance=account.statement.balance if hasattr(account.statement, 'balance') else 0.0
                    )
                    db.session.add(bank_acc)
                    db.session.flush()
                elif hasattr(account.statement, 'balance'):
                    bank_acc.balance = account.statement.balance
                    
                for tx in account.statement.transactions:
                    existing = BankTransaction.query.filter_by(
                        bank_account_id=bank_acc.id, date=tx.date.date(), amount=tx.amount
                    ).first()
                    if not existing:
                        new_tx = BankTransaction(
                            organization_id=org.id,
                            bank_account_id=bank_acc.id,
                            date=tx.date.date(),
                            description=tx.payee or tx.memo or "Unknown Transaction",
                            amount=tx.amount,
                            status='UNCATEGORIZED'
                        )
                        db.session.add(new_tx)
                        imported_txs += 1
                        
            db.session.commit()
            flash(f"Successfully imported {imported_txs} transactions from QBO/OFX.", "success")
            
        # ---- EXCEL / CSV PARSING ----
        elif filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv'):
            # Grab or create a generic default account for CSV/XLSX imports 
            bank_acc = BankAccount.query.filter_by(organization_id=org.id).first()
            if not bank_acc:
                bank_acc = BankAccount(
                    organization_id=org.id,
                    name=f"Manual Import Account",
                    account_type="Checking",
                    account_number_last4="0000"
                )
                db.session.add(bank_acc)
                db.session.flush()

            import csv
            import io
            from datetime import datetime
            
            rows = []
            
            if filename.endswith('.csv'):
                content_bytes = file.stream.read()
                file.stream.seek(0)
                try:
                    with open(r'c:\dev\veros_books\last_import.csv', 'wb') as f:
                        f.write(content_bytes)
                except:
                    pass
                stream = io.StringIO(content_bytes.decode("UTF8"), newline=None)
                raw_rows = list(csv.reader(stream))
                header_row_index = 0
                
                # Scan for actual headers to bypass QB's 4-5 line metadata blocks
                for idx, row in enumerate(raw_rows):
                    row_str = " ".join([str(x).lower() for x in row if x])
                    if 'date' in row_str and ('amount' in row_str or 'debit' in row_str):
                        header_row_index = idx
                        break
                        
                if len(raw_rows) > header_row_index + 1:
                    headers = raw_rows[header_row_index]
                    for row in raw_rows[header_row_index + 1:]:
                        if any(row):
                            rows.append(dict(zip(headers, row)))
            else:
                content_bytes = file.stream.read()
                file.stream.seek(0)
                try:
                    with open(r'c:\dev\veros_books\last_import.xlsx', 'wb') as f:
                        f.write(content_bytes)
                except:
                    pass
                import openpyxl
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                
                header_row_index = 1
                for idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                    row_str = " ".join([str(x).lower() for x in row if x])
                    if 'date' in row_str and ('amount' in row_str or 'debit' in row_str):
                        header_row_index = idx
                        break
                
                cell_rows = list(sheet.iter_rows(min_row=header_row_index, values_only=True))
                if len(cell_rows) > 1:
                    headers = cell_rows[0]
                    for row in cell_rows[1:]:
                        if any(row):
                            rows.append(dict(zip(headers, row)))
                            
            for row in rows:
                lowered_row = {str(k).lower().strip(): v for k, v in row.items() if k}
                date_val = lowered_row.get('date') or lowered_row.get('posted date') or lowered_row.get('transaction date')
                desc_val = lowered_row.get('description') or lowered_row.get('payee') or lowered_row.get('memo') or lowered_row.get('name')
                amount_val = lowered_row.get('amount')
                
                if not date_val:
                    continue
                    
                # Deal with split debit/credit columns if amount isn't provided directly
                amount = None
                if amount_val:
                    try: amount = float(str(amount_val).replace('$', '').replace(',', ''))
                    except: pass
                
                if amount is None and lowered_row.get('debit'):
                    try: amount = -abs(float(str(lowered_row.get('debit')).replace('$', '').replace(',', '')))
                    except: pass
                    
                if amount is None and lowered_row.get('credit'):
                    try: amount = abs(float(str(lowered_row.get('credit')).replace('$', '').replace(',', '')))
                    except: pass
                    
                if amount is None:
                    continue
                    
                # Parse python datetime or string
                if isinstance(date_val, datetime):
                    tx_date = date_val.date()
                else:
                    try:
                        tx_date = datetime.strptime(str(date_val).split(' ')[0], '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            tx_date = datetime.strptime(str(date_val).split(' ')[0], '%m/%d/%Y').date()
                        except:
                            tx_date = datetime.utcnow().date()

                existing = BankTransaction.query.filter_by(
                    bank_account_id=bank_acc.id, date=tx_date, amount=amount
                ).first()
                
                if not existing:
                    new_tx = BankTransaction(
                        organization_id=org.id,
                        bank_account_id=bank_acc.id,
                        date=tx_date,
                        description=str(desc_val) if desc_val else "Unknown Transaction",
                        amount=amount,
                        status='UNCATEGORIZED'
                    )
                    db.session.add(new_tx)
                    imported_txs += 1
                    
            db.session.commit()
            flash(f"Successfully imported {imported_txs} transactions from Spreadsheet.", "success")
            
        else:
            flash("Unsupported file format.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Error parsing statement file: {str(e)}", "danger")
        
    return redirect(url_for('banking.index'))
@banking_bp.route('/rules')
@login_required
def rules():
    org = get_current_org()
    from app.models.accounting.bank_rule import BankRule
    from app.models.accounting.account import Account
    from app.models.crm.contact import Customer, Vendor
    
    rules = BankRule.query.filter_by(organization_id=org.id).order_by(BankRule.priority.desc()).all()
    accounts = Account.query.filter_by(organization_id=org.id).all()
    
    return render_template('banking/rules.html', rules=rules, accounts=accounts)

@banking_bp.route('/rules/create', methods=['POST'])
@login_required
def create_rule():
    org = get_current_org()
    from app.models.accounting.bank_rule import BankRule
    
    new_rule = BankRule(
        organization_id=org.id,
        name=request.form.get('name'),
        field_to_match=request.form.get('field'),
        match_type=request.form.get('match_type'),
        match_value=request.form.get('match_value'),
        target_account_id=request.form.get('target_account_id')
    )
    db.session.add(new_rule)
    db.session.commit()
    flash("Bank rule created successfully.", "success")
    return redirect(url_for('banking.rules'))

@banking_bp.route('/rules/<rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    org = get_current_org()
    from app.models.accounting.bank_rule import BankRule
    rule = BankRule.query.filter_by(id=rule_id, organization_id=org.id).first_or_404()
    db.session.delete(rule)
    db.session.commit()
    flash("Bank rule removed.", "success")
    return redirect(url_for('banking.rules'))
