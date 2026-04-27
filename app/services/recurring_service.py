from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.extensions import db
from app.models.sales.recurring import RecurringInvoice
from app.models.accounting.recurring_journal import RecurringJournalEntry
from app.models.sales.invoice import Invoice, InvoiceLine
from app.models.accounting.journal import JournalEntry, JournalLine
from app.services.ledger_service import LedgerService

class RecurringService:
    @staticmethod
    def process_all(organization_id, user_id):
        """
        Processes all active recurring templates that are due for run.
        """
        results = {
            'invoices_created': 0,
            'journals_created': 0,
            'errors': []
        }
        
        today = datetime.utcnow().date()
        
        # 1. Process Recurring Invoices
        recurring_invoices = RecurringInvoice.query.filter_by(
            organization_id=organization_id, 
            is_active=True
        ).filter(RecurringInvoice.next_issue_date <= today).all()
        
        for template in recurring_invoices:
            try:
                new_invoice = RecurringService._generate_invoice(template, user_id)
                results['invoices_created'] += 1
                
                # Update next issue date
                template.next_issue_date = RecurringService._get_next_date(template.next_issue_date, template.frequency)
                if template.end_date and template.next_issue_date > template.end_date:
                    template.is_active = False
            except Exception as e:
                results['errors'].append(f"Invoice Template {template.profile_name}: {str(e)}")

        # 2. Process Recurring Journal Entries
        recurring_journals = RecurringJournalEntry.query.filter_by(
            organization_id=organization_id, 
            status='ACTIVE'
        ).filter(RecurringJournalEntry.next_run_date <= today).all()
        
        for template in recurring_journals:
            try:
                new_je = RecurringService._generate_journal(template, user_id)
                results['journals_created'] += 1
                
                # Update next run date
                template.last_run_date = template.next_run_date
                template.next_run_date = RecurringService._get_next_date(template.next_run_date, template.frequency)
            except Exception as e:
                results['errors'].append(f"Journal Template {template.name}: {str(e)}")
                
        db.session.commit()
        return results

    @staticmethod
    def _generate_invoice(template, user_id):
        from app.models.accounting.account import Account
        from flask_login import current_user
        
        invoice = Invoice(
            organization_id=template.organization_id,
            customer_id=template.customer_id,
            invoice_number=f"INV-AUTO-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            issue_date=template.next_issue_date,
            due_date=template.next_issue_date + timedelta(days=30),
            status='OPEN',
            subtotal=template.subtotal,
            total=template.total,
            balance_due=template.total,
            notes=f"Automatically generated from template: {template.profile_name}"
        )
        db.session.add(invoice)
        db.session.flush()
        
        for t_line in template.lines:
            line = InvoiceLine(
                invoice_id=invoice.id,
                description=t_line.description,
                quantity=t_line.quantity,
                unit_price=t_line.unit_price,
                amount=t_line.amount,
                account_id=t_line.account_id
            )
            db.session.add(line)
            
        # Post to Ledger
        ar_account = Account.query.filter_by(organization_id=template.organization_id, name='Accounts Receivable').first()
        if ar_account:
            je = JournalEntry(
                organization_id=template.organization_id,
                entry_number=invoice.invoice_number,
                entry_date=datetime.combine(invoice.issue_date, datetime.min.time()),
                memo=f"Invoice {invoice.invoice_number} (Auto)",
                source_type='INVOICE',
                source_id=invoice.id,
                status='DRAFT',
                created_by=user_id
            )
            db.session.add(je)
            db.session.flush()
            
            db.session.add(JournalLine(journal_entry_id=je.id, account_id=ar_account.id, debit=invoice.total, description=f"Invoice {invoice.invoice_number}"))
            for t_line in template.lines:
                db.session.add(JournalLine(journal_entry_id=je.id, account_id=t_line.account_id, credit=t_line.amount, description=t_line.description))
            
            db.session.flush()
            LedgerService.post_journal_entry(je.id, user_id, template.organization_id)
            
        return invoice

    @staticmethod
    def _generate_journal(template, user_id):
        je = JournalEntry(
            organization_id=template.organization_id,
            entry_number=f"AUTO-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            entry_date=datetime.combine(template.next_run_date, datetime.min.time()),
            memo=template.memo or f"Recurring Entry: {template.name}",
            source_type='RECURRING',
            source_id=template.id,
            status='DRAFT',
            created_by=user_id
        )
        db.session.add(je)
        db.session.flush()
        
        for t_line in template.lines:
            line = JournalLine(
                journal_entry_id=je.id,
                account_id=t_line.account_id,
                debit=t_line.debit,
                credit=t_line.credit,
                description=t_line.description
            )
            db.session.add(line)
            
        if template.auto_post:
            db.session.flush()
            LedgerService.post_journal_entry(je.id, user_id, template.organization_id)
            
        return je

    @staticmethod
    def _get_next_date(current_date, frequency):
        if frequency == 'WEEKLY':
            return current_date + timedelta(days=7)
        elif frequency == 'MONTHLY':
            return current_date + relativedelta(months=1)
        elif frequency == 'QUARTERLY':
            return current_date + relativedelta(months=3)
        elif frequency == 'YEARLY':
            return current_date + relativedelta(years=1)
        return current_date
