from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from ._bp import customers_bp
from app.models.crm.contact import Customer
from app.extensions import db
from app.services.auth_service import get_current_org

@customers_bp.route('/')
@login_required
def index():
    org = get_current_org()
    customers = Customer.query.filter_by(organization_id=org.id).order_by(Customer.display_name).all()
    return render_template('customers/index.html', customers=customers)

@customers_bp.route('/create', methods=['POST'])
@login_required
def create():
    org = get_current_org()
    display_name = request.form.get('display_name')
    company_name = request.form.get('company_name')
    email = request.form.get('email')
    
    new_customer = Customer(
        organization_id=org.id,
        display_name=display_name,
        company_name=company_name,
        email=email
    )
    db.session.add(new_customer)
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        customers = Customer.query.filter_by(organization_id=org.id).order_by(Customer.display_name).all()
        return render_template('customers/_customer_list.html', customers=customers)
        
    return redirect(url_for('customers.index'))
