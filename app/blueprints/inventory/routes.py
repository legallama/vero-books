from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.models.sales.product import Product
from app.models.sales.inventory_adjustment import InventoryAdjustment, InventoryAdjustmentLine
from app.models.accounting.account import Account
from app.services.auth_service import get_current_org
from app.extensions import db
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
def dashboard():
    org = get_current_org()
    products = Product.query.filter_by(organization_id=org.id, track_inventory=True).all()
    adjustments = InventoryAdjustment.query.filter_by(organization_id=org.id).order_by(InventoryAdjustment.date.desc()).limit(10).all()
    
    low_stock = [p for p in products if float(p.quantity_on_hand) <= float(p.reorder_point)]
    
    return render_template('inventory/dashboard.html', 
                         products=products, 
                         adjustments=adjustments,
                         low_stock=low_stock)

@inventory_bp.route('/adjustments')
@login_required
def adjustments():
    org = get_current_org()
    adjustments = InventoryAdjustment.query.filter_by(organization_id=org.id).order_by(InventoryAdjustment.date.desc()).all()
    return render_template('inventory/adjustments.html', adjustments=adjustments)

@inventory_bp.route('/adjustments/new', methods=['GET', 'POST'])
@login_required
def new_adjustment():
    org = get_current_org()
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        reason = request.form.get('reason')
        account_id = request.form.get('adjustment_account_id')
        notes = request.form.get('notes')
        
        adj = InventoryAdjustment(
            organization_id=org.id,
            reference_number=f"ADJ-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            reason=reason,
            adjustment_account_id=account_id,
            notes=notes
        )
        db.session.add(adj)
        db.session.flush() # get ID
        
        # Process lines
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity_adjusted[]')
        
        for pid, qty_str in zip(product_ids, quantities):
            if pid and qty_str:
                qty = float(qty_str)
                if qty == 0:
                    continue
                    
                product = Product.query.get(pid)
                unit_cost = float(product.purchase_cost) if product.purchase_cost else 0.00
                
                line = InventoryAdjustmentLine(
                    adjustment_id=adj.id,
                    product_id=pid,
                    quantity_adjusted=qty,
                    unit_cost=unit_cost,
                    total_value_adjusted=qty * unit_cost
                )
                db.session.add(line)
                
                # Update product quantity
                product.quantity_on_hand = float(product.quantity_on_hand) + qty
                
        db.session.commit()
        flash('Inventory adjustment recorded.', 'success')
        return redirect(url_for('inventory.dashboard'))
        
    products = Product.query.filter_by(organization_id=org.id, track_inventory=True).all()
    expense_accounts = Account.query.filter_by(organization_id=org.id).filter(Account.type == 'EXPENSE').all()
    
    return render_template('inventory/new_adjustment.html', products=products, expense_accounts=expense_accounts)
