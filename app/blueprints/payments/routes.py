from flask import render_template, request, flash, redirect, url_for, jsonify
from . import payments_bp
from app.models.sales.invoice import Invoice
from app.models.accounting.journal import JournalEntry, JournalLine
from app.models.accounting.payment import InvoicePayment
from app.extensions import db
from datetime import datetime
from decimal import Decimal

@payments_bp.route('/invoice/<string:token>')
def view_invoice(token):
    invoice = Invoice.query.filter_by(public_token=token).first_or_404()
    org = invoice.organization
    
    # If the invoice is already paid, show a success screen
    if invoice.status == 'PAID':
        return render_template('payments/success.html', invoice=invoice)
        
    return render_template('payments/public_invoice.html', 
                           invoice=invoice, 
                           org=org,
                           stripe_key=org.stripe_publishable_key)

@payments_bp.route('/invoice/<string:token>/pay', methods=['POST'])
def process_payment(token):
    invoice = Invoice.query.filter_by(public_token=token).first_or_404()
    org = invoice.organization
    
    # In a real app, we would verify the Stripe PaymentIntent here.
    # For this implementation, we'll simulate a successful payment.
    
    # 1. Record the Payment
    payment = InvoicePayment(
        organization_id=org.id,
        invoice_id=invoice.id,
        bank_account_id=bank_account.id if bank_account else None,
        amount=invoice.total,
        payment_date=datetime.utcnow().date(),
        payment_method='STRIPE',
        reference=f"STRIPE-{int(datetime.utcnow().timestamp())}"
    )
    db.session.add(payment)

    
    # 2. Update Invoice Status
    invoice.status = 'PAID'
    invoice.balance_due = 0.00
    
    # 3. Create Journal Entry (DR Bank, CR Accounts Receivable)
    from app.models.accounting.account import Account
    bank_account = Account.query.filter_by(organization_id=org.id, type='Asset', subtype='Bank').first()
    ar_account = Account.query.filter_by(organization_id=org.id, type='Asset', name='Accounts Receivable').first()
    
    if bank_account and ar_account:
        je = JournalEntry(
            organization_id=org.id,
            entry_number=f"PAY-{int(datetime.utcnow().timestamp())}",
            entry_date=datetime.utcnow(),
            memo=f"Payment for Invoice {invoice.invoice_number} via Stripe",
            status='POSTED'
        )
        db.session.add(je)
        db.session.flush()
        
        # DR Bank
        db.session.add(JournalLine(journal_entry_id=je.id, account_id=bank_account.id, debit=invoice.total))
        # CR AR
        db.session.add(JournalLine(journal_entry_id=je.id, account_id=ar_account.id, credit=invoice.total))
    
    db.session.commit()
    
    return jsonify({'success': True, 'redirect': url_for('payments.view_invoice', token=token)})
