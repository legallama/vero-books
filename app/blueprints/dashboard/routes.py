from flask import render_template
from flask_login import login_required
from ._bp import dashboard_bp
from app.extensions import db

@dashboard_bp.route('/')
@login_required
def index():
    from flask import request
    from app.services.auth_service import get_current_org
    from app.models.sales.invoice import Invoice
    from app.models.purchases.bill import Bill
    from app.models.accounting.journal import JournalEntry, JournalLine
    from app.models.accounting.account import Account
    from sqlalchemy import func
    from datetime import datetime, date
    import calendar
    
    org = get_current_org()
    if not org:
        from flask import flash, redirect, url_for
        flash("Please select or create an organization to continue.", "warning")
        return redirect(url_for('auth.logout'))
    
    # --- Dynamic Setup Progress Calculation ---
    setup_steps = [
        {'id': 'org', 'title': 'Complete Company Profile', 'completed': bool(org.legal_name or org.phone)},
        {'id': 'accounts', 'title': 'Review Chart of Accounts', 'completed': Account.query.filter_by(organization_id=org.id).count() > 10},
        {'id': 'bank', 'title': 'Set Up Bank Account', 'completed': Account.query.filter_by(organization_id=org.id, subtype='Bank').count() > 0},
        {'id': 'team', 'title': 'Invite Team Members', 'completed': len(org.memberships) > 1},
        {'id': 'trans', 'title': 'Record First Transaction', 'completed': JournalEntry.query.filter_by(organization_id=org.id).count() > 0}
    ]
    completed_steps = len([s for s in setup_steps if s['completed']])
    setup_percent = (completed_steps / len(setup_steps)) * 100
    # ------------------------------------------
    
    # Get date range from request or default to current year
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = date(date.today().year, 1, 1)
        
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = date(date.today().year, 12, 31)

    # 1. Receivables (Unpaid Invoices) - Overall current
    receivables = db.session.query(func.sum(Invoice.balance_due)).filter(
        Invoice.organization_id == org.id,
        Invoice.status.in_(['OPEN', 'PARTIAL', 'OVERDUE'])
    ).scalar() or 0
    
    # 2. Payables (Unpaid Bills) - Overall current
    payables = db.session.query(func.sum(Bill.balance_due)).filter(
        Bill.organization_id == org.id,
        Bill.status.in_(['OPEN', 'PARTIAL', 'OVERDUE'])
    ).scalar() or 0
    
    # Helper for time-series data
    def get_monthly_data(query_result, date_field='month', value_field='total'):
        data_map = {r[0]: float(r[1]) for r in query_result}
        labels = []
        values = []
        
        # Generate months between start and end
        curr = start_date.replace(day=1)
        while curr <= end_date:
            m_str = curr.strftime('%Y-%m-01')
            labels.append(curr.strftime('%b'))
            values.append(data_map.get(m_str, 0.0))
            
            # Move to next month
            if curr.month == 12:
                curr = curr.replace(year=curr.year + 1, month=1)
            else:
                curr = curr.replace(month=curr.month + 1)
        return labels, values

    # 3. Cash Flow (Incoming/Outgoing to Bank Accounts)
    cash_in_raw = db.session.query(
        func.strftime('%Y-%m-01', JournalEntry.entry_date).label('month'),
        func.sum(JournalLine.debit).label('total')
    ).join(JournalLine).join(Account).filter(
        JournalEntry.organization_id == org.id,
        JournalEntry.status == 'POSTED',
        Account.type == 'Asset',
        Account.subtype == 'Bank',
        JournalEntry.entry_date >= start_date,
        JournalEntry.entry_date <= end_date
    ).group_by('month').all()

    cash_out_raw = db.session.query(
        func.strftime('%Y-%m-01', JournalEntry.entry_date).label('month'),
        func.sum(JournalLine.credit).label('total')
    ).join(JournalLine).join(Account).filter(
        JournalEntry.organization_id == org.id,
        JournalEntry.status == 'POSTED',
        Account.type == 'Asset',
        Account.subtype == 'Bank',
        JournalEntry.entry_date >= start_date,
        JournalEntry.entry_date <= end_date
    ).group_by('month').all()

    chart_labels, cash_in_values = get_monthly_data(cash_in_raw)
    _, cash_out_values = get_monthly_data(cash_out_raw)

    # 4. Profit & Loss (Income vs Expense)
    income_raw = db.session.query(
        func.strftime('%Y-%m-01', JournalEntry.entry_date).label('month'),
        func.sum(JournalLine.credit - JournalLine.debit).label('total')
    ).join(JournalLine).join(Account).filter(
        JournalEntry.organization_id == org.id,
        JournalEntry.status == 'POSTED',
        Account.type == 'Income',
        JournalEntry.entry_date >= start_date,
        JournalEntry.entry_date <= end_date
    ).group_by('month').all()

    expense_raw = db.session.query(
        func.strftime('%Y-%m-01', JournalEntry.entry_date).label('month'),
        func.sum(JournalLine.debit - JournalLine.credit).label('total')
    ).join(JournalLine).join(Account).filter(
        JournalEntry.organization_id == org.id,
        JournalEntry.status == 'POSTED',
        Account.type == 'Expense',
        JournalEntry.entry_date >= start_date,
        JournalEntry.entry_date <= end_date
    ).group_by('month').all()

    _, income_values = get_monthly_data(income_raw)
    _, expense_values = get_monthly_data(expense_raw)

    # 5. Expenses By Category
    expenses_by_cat = db.session.query(
        Account.name,
        func.sum(JournalLine.debit - JournalLine.credit).label('total')
    ).join(JournalLine).join(JournalEntry).filter(
        JournalEntry.organization_id == org.id,
        JournalEntry.status == 'POSTED',
        Account.type == 'Expense',
        JournalEntry.entry_date >= start_date,
        JournalEntry.entry_date <= end_date
    ).group_by(Account.name).having(func.sum(JournalLine.debit - JournalLine.credit) > 0).all()

    cat_labels = [r[0] for r in expenses_by_cat]
    cat_values = [float(r[1]) for r in expenses_by_cat]

    # 6. Recent Activity (Last 5 Journal Entries)
    recent_activity = JournalEntry.query.filter_by(organization_id=org.id).order_by(JournalEntry.entry_date.desc()).limit(5).all()

    return render_template('dashboard/index.html', 
                          receivables=receivables,
                          payables=payables,
                          chart_labels=chart_labels, 
                          cash_in_values=cash_in_values,
                          cash_out_values=cash_out_values,
                          income_values=income_values,
                          expense_values=expense_values,
                          cat_labels=cat_labels,
                          cat_values=cat_values,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'),
                          total_steps=len(setup_steps),
                          setup_percent=setup_percent,
                          recent_activity=recent_activity)

@dashboard_bp.route('/api/global-search')
@login_required
def global_search():
    from flask import request, jsonify
    from app.services.auth_service import get_current_org
    from app.models.sales.invoice import Invoice
    from app.models.purchases.bill import Bill
    from app.models.crm.contact import Contact
    from app.models.accounting.account import Account
    
    query = request.args.get('q', '').strip()
    org = get_current_org()
    
    if not query or not org:
        return jsonify([])
    
    results = []
    
    # Search Invoices
    invoices = Invoice.query.filter(
        Invoice.organization_id == org.id,
        (Invoice.invoice_number.ilike(f'%{query}%'))
    ).limit(3).all()
    for inv in invoices:
        results.append({'name': f'Invoice {inv.invoice_number}', 'icon': 'file-text', 'url': url_for('invoices.index'), 'type': 'Sales'})
        
    # Search Customers
    customers = Contact.query.filter(
        Contact.organization_id == org.id,
        Contact.type == 'CUSTOMER',
        Contact.display_name.ilike(f'%{query}%')
    ).limit(3).all()
    for c in customers:
        results.append({'name': f'Customer: {c.display_name}', 'icon': 'user', 'url': url_for('customers.index'), 'type': 'People'})
        
    # Search Accounts
    accounts = Account.query.filter(
        Account.organization_id == org.id,
        Account.name.ilike(f'%{query}%')
    ).limit(3).all()
    for a in accounts:
        results.append({'name': f'Account: {a.name}', 'icon': 'list', 'url': url_for('accounts.index'), 'type': 'Accounting'})
        
    return jsonify(results)

