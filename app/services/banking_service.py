from app.models.accounting.bank_rule import BankRule
from app.models.banking.bank_account import BankTransaction
from app.models.accounting.journal import JournalEntry, JournalLine
from app.extensions import db
from app.services.ledger_service import LedgerService
from datetime import datetime
import time

class BankingService:
    @staticmethod
    def get_suggestion(transaction, organization_id):
        """
        Returns a suggested GL account for a transaction based on rules or history.
        """
        from app.models.accounting.bank_rule import BankRule
        from app.models.accounting.account import Account
        from app.models.accounting.journal import JournalEntry
        
        # 1. Check Rules
        active_rules = BankRule.query.filter_by(
            organization_id=organization_id, 
            is_active=True
        ).order_by(BankRule.priority.desc()).all()

        for rule in active_rules:
            match = False
            if rule.field_to_match == 'DESCRIPTION':
                if rule.match_type == 'CONTAINS' and rule.match_value.lower() in transaction.description.lower():
                    match = True
                elif rule.match_type == 'EXACT' and rule.match_value.lower() == transaction.description.lower():
                    match = True
            elif rule.field_to_match == 'AMOUNT':
                try:
                    val = float(rule.match_value)
                    if rule.match_type == 'EXACT' and float(transaction.amount) == val:
                        match = True
                    elif rule.match_type == 'GREATER_THAN' and float(transaction.amount) > val:
                        match = True
                except: pass
            
            if match:
                return rule.target_account, rule.name

        # 2. Heuristic: History-based matching
        last_match = BankTransaction.query.filter(
            BankTransaction.organization_id == organization_id,
            BankTransaction.description == transaction.description,
            BankTransaction.status == 'MATCHED',
            BankTransaction.id != transaction.id
        ).order_by(BankTransaction.date.desc()).first()
        
        if last_match and last_match.matched_source_id:
            je = JournalEntry.query.get(last_match.matched_source_id)
            if je:
                for line in je.lines:
                    if line.account_id != transaction.bank_account.account_id:
                        return line.account, "Based on your history"
                        
        return None, None

    @staticmethod
    def apply_rules_to_transaction(transaction, organization_id, user_id=None):
        """
        Matches a transaction against active rules.
        If auto_post is True, it creates and posts a journal entry immediately.
        """
        from app.models.accounting.bank_rule import BankRule
        active_rules = BankRule.query.filter_by(
            organization_id=organization_id, 
            is_active=True
        ).order_by(BankRule.priority.desc()).all()

        for rule in active_rules:
            match = False
            if rule.field_to_match == 'DESCRIPTION':
                if rule.match_type == 'CONTAINS' and rule.match_value.lower() in transaction.description.lower():
                    match = True
                elif rule.match_type == 'EXACT' and rule.match_value.lower() == transaction.description.lower():
                    match = True
            elif rule.field_to_match == 'AMOUNT':
                try:
                    val = float(rule.match_value)
                    if rule.match_type == 'EXACT' and float(transaction.amount) == val:
                        match = True
                    elif rule.match_type == 'GREATER_THAN' and float(transaction.amount) > val:
                        match = True
                except: pass
            
            if match:
                if rule.auto_post and user_id:
                    # Execute Auto-Post
                    BankingService.post_transaction_to_ledger(transaction, rule.target_account_id, user_id, organization_id)
                return rule
        return None

    @staticmethod
    def post_transaction_to_ledger(tx, target_account_id, user_id, organization_id):
        """
        Logic extracted from accept_match route to allow reuse.
        """
        from app.models.accounting.account import Account
        
        bank_account = tx.bank_account
        if not bank_account.account_id:
            # Fallback: find or create GL account for bank
            gl_account = Account.query.filter_by(organization_id=organization_id, name=bank_account.name).first()
            if not gl_account:
                gl_account = Account(
                    organization_id=organization_id, 
                    name=bank_account.name, 
                    code=bank_account.account_number_last4 or "1000", 
                    type="Asset", 
                    subtype="Bank"
                )
                db.session.add(gl_account)
                db.session.flush()
            bank_account.account_id = gl_account.id

        je = JournalEntry(
            organization_id=organization_id,
            entry_number=f"AUTO-{int(time.time())}-{tx.id[:4]}",
            entry_date=tx.date,
            memo=f"Auto-Posted: {tx.description}",
            source_type='BANK_FEED',
            source_id=tx.id,
            status='DRAFT'
        )
        db.session.add(je)
        db.session.flush()
        
        amount = abs(float(tx.amount))
        if float(tx.amount) > 0: # Deposit
            bank_line = JournalLine(journal_entry_id=je.id, account_id=bank_account.account_id, debit=amount, description=tx.description)
            target_line = JournalLine(journal_entry_id=je.id, account_id=target_account_id, credit=amount, description=tx.description)
        else: # Withdrawal
            bank_line = JournalLine(journal_entry_id=je.id, account_id=bank_account.account_id, credit=amount, description=tx.description)
            target_line = JournalLine(journal_entry_id=je.id, account_id=target_account_id, debit=amount, description=tx.description)
            
        db.session.add(bank_line)
        db.session.add(target_line)
        db.session.flush()
        
        success, msg = LedgerService.post_journal_entry(je.id, user_id, organization_id)
        if success:
            tx.status = 'MATCHED'
            tx.matched_source_type = 'JOURNAL_ENTRY'
            tx.matched_source_id = je.id
            return True
        return False
