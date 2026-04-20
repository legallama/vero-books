from decimal import Decimal
from datetime import datetime
from app.extensions import db
from app.models.sales.invoice import Invoice
from app.models.accounting.journal import JournalEntry, JournalLine
from app.services.ledger_service import LedgerService

class SalesService:
    @staticmethod
    def post_invoice_to_ledger(invoice_id, user_id, organization_id):
        """
        Posts an invoice and creates the General Ledger entries.
        Dr Accounts Receivable
        Cr Income Account (per line)
        """
        invoice = Invoice.query.filter_by(id=invoice_id, organization_id=organization_id).first()
        if not invoice or invoice.status != 'DRAFT':
            return False, "Invoice not found or already posted."
            
        # 1. Find AR Account
        from app.models.accounting.account import Account
        ar_account = Account.query.filter_by(organization_id=organization_id, code='1200').first() # Sample AR code
        if not ar_account:
            return False, "Accounts Receivable account not configured."

        # 2. Create Journal Entry
        entry = JournalEntry(
            organization_id=organization_id,
            entry_number=f"INV-POST-{invoice.invoice_number}",
            entry_date=invoice.issue_date,
            memo=f"Invoice {invoice.invoice_number} - {invoice.customer.display_name}",
            source_type='INVOICE',
            source_id=invoice.id,
            status='POSTED',
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow()
        )
        db.session.add(entry)

        # 3. Debit A/R
        ar_line = JournalLine(
            journal_entry=entry,
            account_id=ar_account.id,
            debit=invoice.total,
            credit=0,
            description=f"A/R for Invoice {invoice.invoice_number}",
            customer_id=invoice.customer_id
        )
        db.session.add(ar_line)

        # 4. Credit Income for each line
        for inv_line in invoice.lines:
            cr_line = JournalLine(
                journal_entry=entry,
                account_id=inv_line.account_id,
                debit=0,
                credit=inv_line.amount,
                description=inv_line.description,
                customer_id=invoice.customer_id
            )
            db.session.add(cr_line)

        invoice.status = 'SENT'
        db.session.commit()
        return True, "Invoice posted to ledger."
