from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from . import invoices_bp
from app.models.sales.invoice import Invoice, InvoiceLine
from app.models.crm.contact import Customer
from app.models.accounting.account import Account
from app.extensions import db
from app.services.auth_service import get_current_org
from datetime import datetime, timedelta

@invoices_bp.route('/')
@login_required
def index():
    org = get_current_org()
    invoices = Invoice.query.filter_by(organization_id=org.id).order_by(Invoice.issue_date.desc()).all()
    return render_template('invoices/index.html', invoices=invoices)

@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    from app.models.crm.contact import Customer
    from app.models.accounting.account import Account
    from app.services.ledger_service import LedgerService
    from decimal import Decimal
    
    from app.models.accounting.tag import Tag
    
    customers = Customer.query.filter_by(organization_id=org.id, is_active=True).all()
    accounts = Account.query.filter_by(organization_id=org.id, type='Income', is_active=True).all()
    available_tags = Tag.query.filter_by(organization_id=org.id, is_active=True).all()
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        issue_date_str = request.form.get('issue_date')
        due_date_str = request.form.get('due_date')
        notes = request.form.get('notes')
        selected_tag_ids = request.form.getlist('tag_ids')
        
        # 1. Create Invoice
        invoice = Invoice(
            organization_id=org.id,
            customer_id=customer_id,
            invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            issue_date=datetime.strptime(issue_date_str, '%Y-%m-%d').date(),
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date(),
            status='OPEN', 
            notes=notes
        )
        
        # Add Tags
        if selected_tag_ids:
            tags = Tag.query.filter(Tag.id.in_(selected_tag_ids)).all()
            invoice.tags = tags

        db.session.add(invoice)
        db.session.flush()

        
        # 2. Parse Line Items
        total_amount = Decimal('0.00')
        line_count = int(request.form.get('line_count', 0))
        
        invoice_lines = []
        for i in range(line_count):
            desc = request.form.get(f'lines[{i}][description]')
            acc_id = request.form.get(f'lines[{i}][account_id]')
            qty = Decimal(request.form.get(f'lines[{i}][quantity]', '0'))
            price = Decimal(request.form.get(f'lines[{i}][unit_price]', '0'))
            
            if desc and acc_id and qty > 0:
                amount = qty * price
                line = InvoiceLine(
                    invoice_id=invoice.id,
                    description=desc,
                    account_id=acc_id,
                    quantity=qty,
                    unit_price=price,
                    amount=amount
                )
                db.session.add(line)
                invoice_lines.append(line)
                total_amount += amount
                
        invoice.total = total_amount
        invoice.subtotal = total_amount
        invoice.balance_due = total_amount
        
        # 3. Create Ledger Entry
        # DR Accounts Receivable, CR Income Accounts
        ar_account = Account.query.filter_by(organization_id=org.id, name='Accounts Receivable').first()
        if not ar_account:
            flash("Accounts Receivable account not found. Please set up your Chart of Accounts.", "danger")
            return redirect(url_for('invoices.create'))

        je = JournalEntry(
            organization_id=org.id,
            entry_number=invoice.invoice_number,
            entry_date=datetime.combine(invoice.issue_date, datetime.min.time()),
            memo=f"Invoice {invoice.invoice_number} to {invoice.customer.display_name}",
            source_type='INVOICE',
            source_id=invoice.id,
            status='DRAFT',
            created_by=current_user.id
        )
        db.session.add(je)
        db.session.flush()
        
        # Line 1: Debit Accounts Receivable
        ar_line = JournalLine(
            journal_entry_id=je.id,
            account_id=ar_account.id,
            debit=total_amount,
            description=f"Invoice {invoice.invoice_number}"
        )
        db.session.add(ar_line)
        
        # Income Lines
        for iline in invoice_lines:
            inc_line = JournalLine(
                journal_entry_id=je.id,
                account_id=iline.account_id,
                credit=iline.amount,
                description=iline.description
            )
            db.session.add(inc_line)
            
        db.session.flush()
        
        # Post it
        from app.services.audit_service import AuditService
        success, msg = LedgerService.post_journal_entry(je.id, current_user.id, org.id)
        if success:
            AuditService.log_action(org.id, current_user.id, 'CREATE', 'INVOICE', invoice.id, reason=f"New Invoice {invoice.invoice_number}")
            db.session.commit()
            flash(f"Invoice {invoice.invoice_number} created and posted to ledger.", "success")

        else:
            db.session.rollback()
            flash(f"Error posting invoice: {msg}", "danger")
            
        return redirect(url_for('invoices.index'))
        
    today = datetime.utcnow().date()
    default_due = today + timedelta(days=30)
    return render_template('invoices/create.html', 
                          customers=customers, 
                          accounts=accounts,
                          available_tags=available_tags,
                          today=today.strftime('%Y-%m-%d'),
                          default_due=default_due.strftime('%Y-%m-%d'))

@invoices_bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    org = get_current_org()
    from app.services.ledger_service import LedgerService
    from app.models.accounting.journal import JournalEntry
    
    action = request.form.get('action')
    ids_str = request.form.get('invoice_ids')
    
    if not ids_str:
        flash("No invoices selected.", "warning")
        return redirect(url_for('invoices.index'))
        
    invoice_ids = ids_str.split(',')
    count = 0
    
    for inv_id in invoice_ids:
        invoice = Invoice.query.filter_by(id=inv_id, organization_id=org.id).first()
        if not invoice: continue
        
        if action == 'VOID':
            if invoice.status != 'VOID':
                je = JournalEntry.query.filter_by(source_type='INVOICE', source_id=invoice.id).first()
                if je:
                    LedgerService.reverse_journal_entry(je.id, current_user.id, org.id, reason=f"Bulk Void Invoice {invoice.invoice_number}")
                
                invoice.status = 'VOID'
                invoice.balance_due = 0
                count += 1
        elif action == 'DELETE':
            # For simplicity, we delete the invoice and lines (Ledger entries remain for audit unless manually reversed)
            db.session.delete(invoice)
            count += 1
            
    db.session.commit()
    flash(f"Successfully processed {count} invoices.", "success")
    return redirect(url_for('invoices.index'))



@invoices_bp.route('/credit-memo/create', methods=['GET', 'POST'])
@login_required
def create_credit_memo():
    org = get_current_org()
    from app.models.crm.contact import Customer
    from app.models.accounting.account import Account
    from app.services.ledger_service import LedgerService
    from decimal import Decimal
    from app.models.accounting.tag import Tag
    
    customers = Customer.query.filter_by(organization_id=org.id, is_active=True).all()
    accounts = Account.query.filter_by(organization_id=org.id, type='Income', is_active=True).all()
    available_tags = Tag.query.filter_by(organization_id=org.id, is_active=True).all()
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        issue_date_str = request.form.get('issue_date')
        notes = request.form.get('notes')
        
        # 1. Create Credit Memo
        memo = Invoice(
            organization_id=org.id,
            customer_id=customer_id,
            invoice_number=f"CM-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            type='CREDIT_MEMO',
            issue_date=datetime.strptime(issue_date_str, '%Y-%m-%d').date(),
            due_date=datetime.strptime(issue_date_str, '%Y-%m-%d').date(),
            status='OPEN', 
            notes=notes
        )
        db.session.add(memo)
        db.session.flush()
        
        # 2. Parse Line Items
        total_amount = Decimal('0.00')
        line_count = int(request.form.get('line_count', 0))
        
        memo_lines = []
        for i in range(line_count):
            desc = request.form.get(f'lines[{i}][description]')
            acc_id = request.form.get(f'lines[{i}][account_id]')
            qty = Decimal(request.form.get(f'lines[{i}][quantity]', '0'))
            price = Decimal(request.form.get(f'lines[{i}][unit_price]', '0'))
            
            if desc and acc_id and qty > 0:
                amount = qty * price
                line = InvoiceLine(
                    invoice_id=memo.id,
                    description=desc,
                    account_id=acc_id,
                    quantity=qty,
                    unit_price=price,
                    amount=amount
                )
                db.session.add(line)
                memo_lines.append(line)
                total_amount += amount
                
        memo.total = total_amount
        memo.subtotal = total_amount
        memo.balance_due = 0 # CM doesn't have balance due usually, it reduces others
        
        # 3. Create Ledger Entry
        # DR Income (Reverse), CR Accounts Receivable (Reduce)
        ar_account = Account.query.filter_by(organization_id=org.id, name='Accounts Receivable').first()
        
        je = JournalEntry(
            organization_id=org.id,
            entry_number=memo.invoice_number,
            entry_date=datetime.combine(memo.issue_date, datetime.min.time()),
            memo=f"Credit Memo {memo.invoice_number} to {memo.customer.display_name}",
            source_type='INVOICE',
            source_id=memo.id,
            status='DRAFT',
            created_by=current_user.id
        )
        db.session.add(je)
        db.session.flush()
        
        # Credit Accounts Receivable (Reduce)
        db.session.add(JournalLine(journal_entry_id=je.id, account_id=ar_account.id, credit=total_amount, description=f"Credit Memo {memo.invoice_number}"))
        
        # Debit Income Lines (Reverse Revenue)
        for mline in memo_lines:
            db.session.add(JournalLine(journal_entry_id=je.id, account_id=mline.account_id, debit=mline.amount, description=mline.description))
            
        db.session.flush()
        LedgerService.post_journal_entry(je.id, current_user.id, org.id)
        
        db.session.commit()
        flash(f"Credit Memo {memo.invoice_number} created.", "success")
        return redirect(url_for('invoices.index'))
        
    today = datetime.utcnow().date()
    return render_template('invoices/create.html', 
                          is_credit_memo=True,
                          customers=customers, 
                          accounts=accounts,
                          available_tags=available_tags,
                          today=today.strftime('%Y-%m-%d'),
                          default_due=today.strftime('%Y-%m-%d'))
