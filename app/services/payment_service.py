from decimal import Decimal
from datetime import datetime
from app.extensions import db
from app.models.accounting.payment import InvoicePayment, BillPayment
from app.models.accounting.journal import JournalEntry, JournalLine
from app.models.sales.invoice import Invoice
from app.models.purchases.bill import Bill

class PaymentService:
    @staticmethod
    def record_invoice_payment(invoice_id, bank_account_id, amount, payment_date, user_id, organization_id, reference=None):
        """
        Records a payment against an invoice and updates the ledger.
        Dr Bank Account
        Cr Accounts Receivable
        """
        invoice = Invoice.query.filter_by(id=invoice_id, organization_id=organization_id).first()
        if not invoice:
            return False, "Invoice not found."

        # 1. Create Payment Record
        payment = InvoicePayment(
            organization_id=organization_id,
            invoice_id=invoice_id,
            bank_account_id=bank_account_id,
            payment_date=payment_date,
            amount=amount,
            reference=reference
        )
        db.session.add(payment)

        # 2. Create Journal Entry
        entry = JournalEntry(
            organization_id=organization_id,
            entry_number=f"PYMT-{invoice.invoice_number}",
            entry_date=payment_date,
            memo=f"Payment for Invoice {invoice.invoice_number} - {invoice.customer.display_name}",
            source_type='RECEIPT',
            source_id=payment.id,
            status='POSTED',
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow()
        )
        db.session.add(entry)

        # 3. Dr Bank Account (Cash)
        from app.models.banking.bank_account import BankAccount
        bank_acc = BankAccount.query.get(bank_account_id)
        
        dr_line = JournalLine(
            journal_entry=entry,
            account_id=bank_acc.account_id,
            debit=amount,
            credit=0,
            description=f"Payment received for {invoice.invoice_number}"
        )
        db.session.add(dr_line)

        # 4. Cr A/R
        from app.models.accounting.account import Account
        ar_account = Account.query.filter_by(organization_id=organization_id, code='1200').first()
        
        cr_line = JournalLine(
            journal_entry=entry,
            account_id=ar_account.id,
            debit=0,
            credit=amount,
            description=f"A/R credit for {invoice.invoice_number}",
            customer_id=invoice.customer_id
        )
        db.session.add(cr_line)

        # Update Invoice Balance
        invoice.balance_due -= Decimal(str(amount))
        if invoice.balance_due <= 0:
            invoice.status = 'PAID'

        db.session.commit()
        return True, "Payment recorded and ledger updated."
