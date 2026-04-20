from decimal import Decimal
from datetime import datetime
from ..extensions import db
from ..models.accounting.journal import JournalEntry, JournalLine
from ..models.audit.log import AuditLog

class LedgerService:
    @staticmethod
    def validate_balanced(lines):
        """
        Ensures total debits equal total credits.
        lines: list of dictionaries with 'debit' and 'credit'
        """
        total_debit = sum(Decimal(str(line.get('debit', 0))) for line in lines)
        total_credit = sum(Decimal(str(line.get('credit', 0))) for line in lines)
        
        if total_debit != total_credit:
            return False, f"Out of balance: Debits {total_debit} != Credits {total_credit}"
        
        if total_debit == 0:
            return False, "Transaction must have non-zero value."
            
        return True, None

    @staticmethod
    def post_journal_entry(entry_id, user_id, organization_id):
        """
        Transitions a JournalEntry from DRAFT to POSTED.
        """
        entry = JournalEntry.query.filter_by(id=entry_id, organization_id=organization_id).first()
        if not entry:
            return False, "Journal Entry not found."
        
        if entry.status != 'DRAFT':
            return False, f"Cannot post entry with status {entry.status}."

        # Validate balance before posting
        lines_data = [{'debit': l.debit, 'credit': l.credit} for l in entry.lines]
        is_balanced, error = LedgerService.validate_balanced(lines_data)
        if not is_balanced:
            return False, error

        entry.status = 'POSTED'
        entry.posted_by = user_id
        entry.posted_at = datetime.utcnow()

        # Log the action
        audit = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action='POST',
            entity_type='JOURNAL_ENTRY',
            entity_id=entry_id,
            reason="User manual post"
        )
        db.session.add(audit)
        db.session.commit()
        
        return True, "Entry posted successfully."

    @staticmethod
    def reverse_journal_entry(entry_id, user_id, organization_id, reason):
        """
        Creates a reversing entry and marks the original as REVERSED.
        Prefer reversals over destructive edits.
        """
        original = JournalEntry.query.filter_by(id=entry_id, organization_id=organization_id).first()
        if not original:
            return False, "Original entry not found."
            
        if original.status != 'POSTED':
            return False, "Only POSTED entries can be reversed."

        # Create reversing entry
        reversal = JournalEntry(
            organization_id=organization_id,
            entry_number=f"REV-{original.entry_number}",
            entry_date=datetime.utcnow(),
            memo=f"Reversal of {original.entry_number}: {reason}",
            source_type='REVERSAL',
            source_id=original.id,
            status='POSTED',
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow()
        )
        
        for line in original.lines:
            rev_line = JournalLine(
                journal_entry=reversal,
                account_id=line.account_id,
                debit=line.credit, # Flip D/C
                credit=line.debit,
                description=f"Reversal: {line.description}"
            )
            db.session.add(rev_line)

        original.status = 'REVERSED'
        original.reversed_entry_id = reversal.id
        
        db.session.add(reversal)
        
        # Log the action
        audit = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action='REVERSE',
            entity_type='JOURNAL_ENTRY',
            entity_id=entry_id,
            reason=reason
        )
        db.session.add(audit)
        db.session.commit()
        
        return True, "Entry reversed successfully."
    @staticmethod
    def get_account_balances(organization_id, date_at=None):
        """
        Calculates net balance for every account in the organization.
        Returns a dictionary mapping account_id to Decimal balance.
        Positive = Debit balance, Negative = Credit balance.
        """
        from ..models.accounting.account import Account
        
        # Base query for posted journal lines
        query = db.session.query(
            JournalLine.account_id,
            db.func.sum(JournalLine.debit - JournalLine.credit).label('balance')
        ).join(JournalEntry).filter(
            JournalEntry.organization_id == organization_id,
            JournalEntry.status == 'POSTED'
        )
        
        if date_at:
            query = query.filter(JournalEntry.entry_date <= date_at)
            
        results = query.group_by(JournalLine.account_id).all()
        
        # Convert to dictionary and include accounts with zero balance
        balances = {r.account_id: r.balance or Decimal('0.00') for r in results}
        
        # Ensure all accounts are present
        all_accounts = Account.query.filter_by(organization_id=organization_id).all()
        for acc in all_accounts:
            if acc.id not in balances:
                balances[acc.id] = Decimal('0.00')
                
        return balances

    @staticmethod
    def get_trial_balance(organization_id, date_at=None):
        """
        Returns a list of accounts with their specific debit and credit totals.
        Useful for the Trial Balance report UI.
        """
        from ..models.accounting.account import Account
        
        query = db.session.query(
            JournalLine.account_id,
            db.func.sum(JournalLine.debit).label('total_debit'),
            db.func.sum(JournalLine.credit).label('total_credit')
        ).join(JournalEntry).filter(
            JournalEntry.organization_id == organization_id,
            JournalEntry.status == 'POSTED'
        )
        
        if date_at:
            query = query.filter(JournalEntry.entry_date <= date_at)
            
        results = query.group_by(JournalLine.account_id).all()
        results_map = {r.account_id: r for r in results}
        
        accounts = Account.query.filter_by(organization_id=organization_id).order_by(Account.code).all()
        
        report_data = []
        for acc in accounts:
            res = results_map.get(acc.id)
            report_data.append({
                'account': acc,
                'debit': res.total_debit if res else Decimal('0.00'),
                'credit': res.total_credit if res else Decimal('0.00'),
                'net_balance': (res.total_debit - res.total_credit) if res else Decimal('0.00')
            })
            
        return report_data

    @staticmethod
    def get_profit_and_loss(organization_id, start_date, end_date):
        """
        Calculates Income - Expenses for a period.
        """
        from app.models.accounting.account import Account
        
        # Get all income and expense accounts
        accounts = Account.query.filter(
            Account.organization_id == organization_id,
            Account.type.in_(['Income', 'Expense'])
        ).all()
        
        period_query = db.session.query(
            JournalLine.account_id,
            db.func.sum(JournalLine.debit - JournalLine.credit).label('balance')
        ).join(JournalEntry).filter(
            JournalEntry.organization_id == organization_id,
            JournalEntry.status == 'POSTED',
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date
        ).group_by(JournalLine.account_id).all()
        
        period_balances = {r.account_id: r.balance for r in period_query}
        
        income_total = Decimal('0.00')
        expense_total = Decimal('0.00')
        lines = []
        
        for acc in accounts:
            bal = period_balances.get(acc.id, Decimal('0.00'))
            # Income accounts usually have Credit balances (negative in our logic)
            # We flip them for display
            display_bal = bal if acc.type == 'Expense' else -bal
            
            if acc.type == 'Income':
                income_total += display_bal
            else:
                expense_total += display_bal
                
            lines.append({'account': acc, 'balance': display_bal})
            
        return {
            'lines': lines,
            'income_total': income_total,
            'expense_total': expense_total,
            'net_profit': income_total - expense_total
        }

    @staticmethod
    def get_balance_sheet(organization_id, date_at=None):
        """
        Assets = Liabilities + Equity
        """
        from app.models.accounting.account import Account
        
        balances = LedgerService.get_account_balances(organization_id, date_at)
        
        accounts = Account.query.filter(
            Account.organization_id == organization_id,
            Account.type.in_(['Asset', 'Liability', 'Equity'])
        ).all()
        
        asset_total = Decimal('0.00')
        liability_total = Decimal('0.00')
        equity_total = Decimal('0.00')
        
        sections = {'Asset': [], 'Liability': [], 'Equity': []}
        
        for acc in accounts:
            bal = balances.get(acc.id, Decimal('0.00'))
            # Assets = Debit (+), Liab/Equity = Credit (-)
            display_bal = bal if acc.type == 'Asset' else -bal
            
            if acc.type == 'Asset': asset_total += display_bal
            elif acc.type == 'Liability': liability_total += display_bal
            elif acc.type == 'Equity': equity_total += display_bal
            
            sections[acc.type].append({'account': acc, 'balance': display_bal})
            
        return {
            'sections': sections,
            'asset_total': asset_total,
            'liability_total': liability_total,
            'equity_total': equity_total,
            'is_balanced': asset_total == (liability_total + equity_total)
        }
