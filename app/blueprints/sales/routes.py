from flask import Blueprint, render_template
from flask_login import login_required
from app.models.sales.invoice import Invoice
from app.models.sales.product import Product
from app.services.auth_service import get_current_org
from datetime import date

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/overview')
@login_required
def overview():
    org = get_current_org()
    today = date.today()
    
    # Summary stats
    unpaid_invoices = Invoice.query.filter_by(organization_id=org.id).filter(Invoice.status != 'PAID').all()
    unpaid_total = sum(float(i.balance_due) for i in unpaid_invoices)
    
    overdue_invoices = [i for i in unpaid_invoices if i.due_date < today]
    overdue_total = sum(float(i.balance_due) for i in overdue_invoices)
    
    return render_template('sales/overview.html', 
                         unpaid_total=unpaid_total, 
                         overdue_total=overdue_total,
                         unpaid_count=len(unpaid_invoices),
                         overdue_count=len(overdue_invoices))

@sales_bp.route('/transactions')
@login_required
def transactions():
    org = get_current_org()
    invoices = Invoice.query.filter_by(organization_id=org.id).order_by(Invoice.issue_date.desc()).all()
    return render_template('sales/transactions.html', invoices=invoices)

@sales_bp.route('/products')
@login_required
def products():
    org = get_current_org()
    products = Product.query.filter_by(organization_id=org.id).all()
    return render_template('sales/products.html', products=products)
@sales_bp.route('/api/tax-rate', methods=['POST'])
@login_required
def get_tax_rate():
    from flask import request, jsonify
    from app.services.tax_service import TaxService
    from app.models.crm.contact import Customer
    
    org = get_current_org()
    data = request.get_json()
    customer_id = data.get('customer_id')
    zip_code = data.get('zip_code')
    
    if not zip_code and customer_id:
        customer = Customer.query.filter_by(id=customer_id, organization_id=org.id).first()
        if customer:
            zip_code = customer.zip_code
            
    if not zip_code:
        return jsonify({'rate': 0.00})
        
    rate = TaxService.get_rate_for_zip(zip_code, org.id)
    return jsonify({'rate': float(rate)})
