from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ._bp import accounts_bp
from ...models.accounting.account import Account, AccountType
from ...extensions import db
from ...services.auth_service import get_current_org

@accounts_bp.route('/')
@login_required
def index():
    org = get_current_org()
    if not org:
        flash("No active organization found.", "error")
        return redirect(url_for('dashboard.index'))
        
    accounts = Account.query.filter_by(organization_id=org.id).order_by(Account.code).all()
    return render_template('accounts/index.html', accounts=accounts, types=[t.value for t in AccountType])

@accounts_bp.route('/create', methods=['POST'])
@login_required
def create():
    org = get_current_org()
    code = request.form.get('code')
    name = request.form.get('name')
    acc_type = request.form.get('type')
    subtype = request.form.get('subtype')
    
    new_acc = Account(
        organization_id=org.id,
        code=code,
        name=name,
        type=acc_type,
        subtype=subtype
    )
    db.session.add(new_acc)
    db.session.commit()
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/<acc_id>/update', methods=['POST'])
@login_required
def update(acc_id):
    org = get_current_org()
    acc = Account.query.filter_by(id=acc_id, organization_id=org.id).first_or_404()
    
    acc.code = request.form.get('code')
    acc.name = request.form.get('name')
    acc.type = request.form.get('type')
    acc.subtype = request.form.get('subtype')
    
    db.session.commit()
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/import-qb', methods=['POST'])
@login_required
def import_qb():
    import csv
    import io
    
    org = get_current_org()
    if 'qb_csv' not in request.files:
        flash("No CSV file provided.", "error")
        return redirect(url_for('accounts.index'))
        
    file = request.files['qb_csv']
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('accounts.index'))
        
    try:
        # Read the CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_input:
            # QuickBooks CSVs can have various column names like "Account", "Name", "Type", "Detail Type"
            # We'll normalize keys by extracting lowercased fields
            lowered_row = {k.lower().strip(): v for k, v in row.items() if k}
            
            # Identify core fields from typical QB outputs
            name = lowered_row.get('account') or lowered_row.get('name') or lowered_row.get('account name')
            acc_type = lowered_row.get('type') or lowered_row.get('account type') or 'Expense'
            subtype = lowered_row.get('detail type') or ''
            
            if not name:
                continue # Skip raw header/footer junk
                
            # Attempt to extract code if Name looks like "1010 - Checking"
            code = ""
            if " - " in name and name.split(" - ")[0].strip().isdigit():
                parts = name.split(" - ")
                code = parts[0].strip()
                name = " - ".join(parts[1:]).strip()
            
            # Check if exists to avoid duplicates
            existing = Account.query.filter_by(organization_id=org.id, name=name).first()
            if not existing:
                new_acc = Account(
                    organization_id=org.id,
                    code=code,
                    name=name,
                    type=acc_type,
                    subtype=subtype
                )
                db.session.add(new_acc)
                imported_count += 1
                
        db.session.commit()
        flash(f"Successfully imported {imported_count} accounts from QuickBooks.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error parsing QuickBooks Data: {str(e)}", "danger")
        
    return redirect(url_for('accounts.index'))
