from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ._bp import fixed_assets_bp
from app.models.accounting.fixed_asset import FixedAsset, DepreciationSchedule
from app.models.accounting.account import Account
from app.services.auth_service import get_current_org
from app.extensions import db
from datetime import datetime, date
from decimal import Decimal

@fixed_assets_bp.route('/')
@login_required
def index():
    org = get_current_org()
    assets = FixedAsset.query.filter_by(organization_id=org.id).all()
    return render_template('fixed_assets/index.html', assets=assets)

@fixed_assets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    if request.method == 'POST':
        asset = FixedAsset(
            organization_id=org.id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            serial_number=request.form.get('serial_number'),
            purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date(),
            purchase_price=Decimal(request.form.get('purchase_price')),
            salvage_value=Decimal(request.form.get('salvage_value', 0)),
            useful_life_months=int(request.form.get('useful_life_months')),
            asset_account_id=request.form.get('asset_account_id'),
            accumulated_depreciation_account_id=request.form.get('accumulated_depreciation_account_id'),
            depreciation_expense_account_id=request.form.get('depreciation_expense_account_id')
        )
        db.session.add(asset)
        db.session.commit()
        
        # Auto-generate schedule
        generate_depreciation_schedule(asset)
        
        flash("Fixed Asset created successfully.", "success")
        return redirect(url_for('fixed_assets.index'))
        
    accounts = Account.query.filter_by(organization_id=org.id).all()
    return render_template('fixed_assets/create.html', accounts=accounts)

@fixed_assets_bp.route('/<asset_id>')
@login_required
def detail(asset_id):
    org = get_current_org()
    asset = FixedAsset.query.filter_by(id=asset_id, organization_id=org.id).first_or_404()
    return render_template('fixed_assets/detail.html', asset=asset)

def generate_depreciation_schedule(asset):
    # Simple Straight Line
    total_to_depreciate = asset.purchase_price - asset.salvage_value
    monthly_amount = total_to_depreciate / Decimal(asset.useful_life_months)
    
    accumulated = Decimal(0)
    current_date = asset.purchase_date
    
    for i in range(1, asset.useful_life_months + 1):
        # Move to next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, current_date.day)
        else:
            current_date = date(current_date.year, current_date.month + 1, current_date.day)
            
        accumulated += monthly_amount
        book_value = asset.purchase_price - accumulated
        
        schedule = DepreciationSchedule(
            asset_id=asset.id,
            date=current_date,
            amount=monthly_amount,
            accumulated_amount=accumulated,
            book_value=book_value
        )
        db.session.add(schedule)
    
    db.session.commit()
