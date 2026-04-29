from flask import render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_required, current_user
from . import migration_bp
from app.models.admin.qbo_connection import QboConnection
from app.extensions import db
from app.services.auth_service import get_current_org
import requests
import base64
import urllib.parse
from datetime import datetime, timedelta

# Constants for QBO OAuth
QBO_AUTH_URL = {
    'sandbox': 'https://appcenter.intuit.com/connect/oauth2',
    'production': 'https://appcenter.intuit.com/connect/oauth2'
}
QBO_TOKEN_URL = {
    'sandbox': 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
    'production': 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
}
QBO_API_BASE = {
    'sandbox': 'https://sandbox-quickbooks.api.intuit.com/v3/company',
    'production': 'https://quickbooks.api.intuit.com/v3/company'
}

@migration_bp.route('/')
@login_required
def index():
    org = get_current_org()
    qbo = QboConnection.query.filter_by(organization_id=org.id).first()
    return render_template('migration/index.html', qbo=qbo)

@migration_bp.route('/save-keys', methods=['POST'])
@login_required
def save_keys():
    org = get_current_org()
    qbo = QboConnection.query.filter_by(organization_id=org.id).first()
    
    if not qbo:
        qbo = QboConnection(organization_id=org.id)
        db.session.add(qbo)
        
    qbo.client_id = request.form.get('client_id', '').strip()
    qbo.client_secret = request.form.get('client_secret', '').strip()
    qbo.environment = request.form.get('environment', 'sandbox')
    db.session.commit()
    
    flash("QuickBooks API credentials saved.", "success")
    return redirect(url_for('migration.index'))

@migration_bp.route('/connect')
@login_required
def connect():
    org = get_current_org()
    qbo = QboConnection.query.filter_by(organization_id=org.id).first()
    
    if not qbo or not qbo.client_id:
        flash("Please save your Client ID and Secret first.", "warning")
        return redirect(url_for('migration.index'))
        
    # Explicitly hardcode redirect_uri to avoid 127.0.0.1 vs localhost mismatches
    redirect_uri = "http://localhost:5000/migration/callback"
    scopes = 'com.intuit.quickbooks.accounting'
    state = 'migration_state_qbo'
    session['qbo_state'] = state
    
    params = {
        'client_id': qbo.client_id,
        'response_type': 'code',
        'scope': scopes,
        'redirect_uri': redirect_uri,
        'state': state
    }
    auth_url = f"{QBO_AUTH_URL[qbo.environment]}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@migration_bp.route('/callback')
@login_required
def callback():
    org = get_current_org()
    qbo = QboConnection.query.filter_by(organization_id=org.id).first()
    
    code = request.args.get('code')
    state = request.args.get('state')
    realm_id = request.args.get('realmId')
    error = request.args.get('error')
    
    if error:
        flash(f"QuickBooks authorization failed: {error}", "danger")
        return redirect(url_for('migration.index'))
        
    if state != session.get('qbo_state'):
        flash("Invalid state token. Possible CSRF attack.", "danger")
        return redirect(url_for('migration.index'))
        
    redirect_uri = "http://localhost:5000/migration/callback"
    
    # Exchange code for tokens
    client_id = qbo.client_id.strip() if qbo.client_id else ''
    client_secret = qbo.client_secret.strip() if qbo.client_secret else ''
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_header}'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    token_url = QBO_TOKEN_URL[qbo.environment]
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        json_resp = response.json()
        qbo.realm_id = realm_id
        qbo.access_token = json_resp.get('access_token')
        qbo.refresh_token = json_resp.get('refresh_token')
        qbo.access_token_expires_at = datetime.utcnow() + timedelta(seconds=json_resp.get('expires_in', 3600))
        qbo.refresh_token_expires_at = datetime.utcnow() + timedelta(seconds=json_resp.get('x_refresh_token_expires_in', 8726400))
        db.session.commit()
        flash("Successfully connected to QuickBooks Online!", "success")
    else:
        flash(f"Failed to get tokens: {response.text}", "danger")
        
    return redirect(url_for('migration.index'))

@migration_bp.route('/disconnect')
@login_required
def disconnect():
    org = get_current_org()
    qbo = QboConnection.query.filter_by(organization_id=org.id).first()
    if qbo:
        qbo.access_token = None
        qbo.refresh_token = None
        qbo.realm_id = None
        db.session.commit()
        flash("Disconnected from QuickBooks Online.", "info")
    return redirect(url_for('migration.index'))

@migration_bp.route('/sync/<entity>', methods=['POST'])
@login_required
def sync(entity):
    org = get_current_org()
    qbo = QboConnection.query.filter_by(organization_id=org.id).first()
    
    if not qbo or not qbo.access_token:
        flash("Not connected to QuickBooks.", "warning")
        return redirect(url_for('migration.index'))
        
    # Example logic for syncing accounts
    if entity == 'accounts':
        url = f"{QBO_API_BASE[qbo.environment]}/{qbo.realm_id}/query?query=select * from Account maxresults 1000"
        headers = {
            'Authorization': f'Bearer {qbo.access_token}',
            'Accept': 'application/json'
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            accounts_data = resp.json().get('QueryResponse', {}).get('Account', [])
            imported = 0
            from app.models.accounting.account import Account
            from app.models.accounting.journal import JournalEntry, JournalLine
            from decimal import Decimal
            import time
            
            # Create a journal entry to hold all the opening balances
            opening_je = JournalEntry(
                organization_id=org.id,
                entry_number=f"MIGRATE-OB-{int(time.time())}",
                entry_date=datetime.utcnow().date(),
                memo="QuickBooks Migration Opening Balances",
                source_type="MIGRATION",
                status="POSTED"
            )
            db.session.add(opening_je)
            db.session.flush()

            for acc in accounts_data:
                name = acc.get('Name')
                acc_type = acc.get('AccountType')
                subtype = acc.get('AccountSubType')
                acct_num = acc.get('AcctNum')
                balance = Decimal(str(acc.get('CurrentBalance', 0)))
                
                if not acct_num:
                    import random
                    acct_num = str(random.randint(10000, 99999))
                
                existing_acc = Account.query.filter_by(organization_id=org.id, name=name).first()
                if not existing_acc:
                    existing_acc = Account(
                        organization_id=org.id,
                        code=acct_num,
                        name=name,
                        type=acc_type,
                        subtype=subtype
                    )
                    db.session.add(existing_acc)
                    db.session.flush()
                    imported += 1
                
                # If there's a balance, add a journal line
                if balance > 0:
                    # Debits increase Asset/Expense, Credits increase Liab/Equity/Income
                    if acc_type in ('Bank', 'Accounts Receivable', 'Other Current Asset', 'Fixed Asset', 'Other Asset', 'Expense', 'Other Expense', 'Cost of Goods Sold'):
                        debit = balance
                        credit = 0
                    else:
                        credit = balance
                        debit = 0
                        
                    bl = JournalLine(
                        journal_entry_id=opening_je.id,
                        account_id=existing_acc.id,
                        debit=debit,
                        credit=credit,
                        description="Opening Balance"
                    )
                    db.session.add(bl)

            # We need an offset account to balance the JE (usually Retained Earnings or Opening Balance Equity)
            # Find or create Opening Balance Equity
            obe = Account.query.filter_by(organization_id=org.id, name="Opening Balance Equity").first()
            if not obe:
                obe = Account(organization_id=org.id, code="39999", name="Opening Balance Equity", type="Equity", subtype="OpeningBalanceEquity")
                db.session.add(obe)
                db.session.flush()

            # Calculate total debits and credits
            total_debits = sum([l.debit or 0 for l in opening_je.lines])
            total_credits = sum([l.credit or 0 for l in opening_je.lines])
            
            if total_debits > total_credits:
                # Add credit to OBE
                bl = JournalLine(journal_entry_id=opening_je.id, account_id=obe.id, debit=0, credit=(total_debits - total_credits), description="Offset")
                db.session.add(bl)
            elif total_credits > total_debits:
                # Add debit to OBE
                bl = JournalLine(journal_entry_id=opening_je.id, account_id=obe.id, debit=(total_credits - total_debits), credit=0, description="Offset")
                db.session.add(bl)
                
            db.session.commit()
            qbo.last_sync_at = datetime.utcnow()
            db.session.commit()
            flash(f"Successfully synced {imported} accounts and imported Opening Balances from QuickBooks.", "success")
        elif resp.status_code == 401:
            flash("Access token expired. Please reconnect.", "danger")
        else:
            flash(f"Failed to fetch accounts: {resp.text}", "danger")
            
    elif entity == 'history':
        headers = {
            'Authorization': f'Bearer {qbo.access_token}',
            'Accept': 'application/json'
        }
        
        # 1. Fetch Invoices
        url_inv = f"{QBO_API_BASE[qbo.environment]}/{qbo.realm_id}/query?query=select * from Invoice maxresults 100"
        resp_inv = requests.get(url_inv, headers=headers)
        
        imported_invoices = 0
        if resp_inv.status_code == 200:
            inv_data = resp_inv.json().get('QueryResponse', {}).get('Invoice', [])
            from app.models.sales.invoice import Invoice
            from app.models.crm.contact import Customer
            
            # Find or create a generic customer for imported invoices since we aren't syncing full CRM yet
            generic_cust = Customer.query.filter_by(organization_id=org.id, display_name='QuickBooks Imported Customer').first()
            if not generic_cust:
                generic_cust = Customer(organization_id=org.id, display_name='QuickBooks Imported Customer', email='imported@qbo.local')
                db.session.add(generic_cust)
                db.session.flush()

            for inv in inv_data:
                # Basic mock import to avoid massive customer/product mapping for now
                if not Invoice.query.filter_by(organization_id=org.id, invoice_number=inv.get('DocNumber')).first():
                    new_inv = Invoice(
                        organization_id=org.id,
                        invoice_number=inv.get('DocNumber', f"QBO-{inv.get('Id')}"),
                        customer_id=generic_cust.id, 
                        issue_date=datetime.strptime(inv.get('TxnDate', '2023-01-01'), '%Y-%m-%d').date(),
                        due_date=datetime.strptime(inv.get('DueDate', '2023-01-01'), '%Y-%m-%d').date(),
                        total=inv.get('TotalAmt', 0),
                        balance_due=inv.get('Balance', 0),
                        status='PAID' if inv.get('Balance', 0) == 0 else 'SENT'
                    )
                    db.session.add(new_inv)
                    imported_invoices += 1
            db.session.commit()
            
        # 2. Fetch Journal Entries
        url_je = f"{QBO_API_BASE[qbo.environment]}/{qbo.realm_id}/query?query=select * from JournalEntry maxresults 100"
        resp_je = requests.get(url_je, headers=headers)
        imported_jes = 0
        if resp_je.status_code == 200:
            je_data = resp_je.json().get('QueryResponse', {}).get('JournalEntry', [])
            from app.models.accounting.journal import JournalEntry
            for je in je_data:
                if not JournalEntry.query.filter_by(organization_id=org.id, entry_number=je.get('DocNumber')).first():
                    new_je = JournalEntry(
                        organization_id=org.id,
                        entry_number=je.get('DocNumber', f"QBO-JE-{je.get('Id')}"),
                        entry_date=datetime.strptime(je.get('TxnDate', '2023-01-01'), '%Y-%m-%d').date(),
                        memo=je.get('PrivateNote', ''),
                        source_type='MIGRATION',
                        status='POSTED'
                    )
                    db.session.add(new_je)
                    imported_jes += 1
            db.session.commit()
            
        qbo.last_sync_at = datetime.utcnow()
        db.session.commit()
        flash(f"Successfully synced {imported_invoices} invoices and {imported_jes} journal entries from QuickBooks.", "success")
        
    return redirect(url_for('migration.index'))
