from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from ._bp import estimates_bp
from app.models.sales.estimate import Estimate
from app.models.crm.contact import Customer
from app.services.auth_service import get_current_org
from app.extensions import db
from datetime import datetime

@estimates_bp.route('/')
@login_required
def index():
    org = get_current_org()
    estimates = Estimate.query.filter_by(organization_id=org.id).order_by(Estimate.issue_date.desc()).all()
    return render_template('estimates/index.html', estimates=estimates)

@estimates_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    customers = Customer.query.filter_by(organization_id=org.id, is_active=True).all()
    
    if request.method == 'POST':
        # logic placeholder
        flash("Estimate created.", "success")
        return redirect(url_for('estimates.index'))
        
    return render_template('estimates/create.html', customers=customers)
@estimates_bp.route('/<estimate_id>/convert', methods=['POST'])
@login_required
def convert_to_invoice(estimate_id):
    org = get_current_org()
    from app.models.sales.invoice import Invoice, InvoiceLine
    from app.models.sales.estimate import Estimate
    
    estimate = Estimate.query.filter_by(id=estimate_id, organization_id=org.id).first_or_404()
    
    if estimate.status == 'INVOICED':
        flash("This estimate has already been converted to an invoice.", "warning")
        return redirect(url_for('estimates.index'))
        
    # Create Invoice
    invoice = Invoice(
        organization_id=org.id,
        customer_id=estimate.customer_id,
        invoice_number=f"INV-FROM-{estimate.estimate_number}",
        issue_date=datetime.utcnow().date(),
        due_date=datetime.utcnow().date(),
        status='DRAFT',
        subtotal=estimate.subtotal,
        tax_total=estimate.tax_total,
        total=estimate.total,
        balance_due=estimate.total,
        notes=f"Converted from Estimate {estimate.estimate_number}. {estimate.notes or ''}"
    )
    db.session.add(invoice)
    db.session.flush()
    
    # Copy Lines
    for e_line in estimate.lines:
        i_line = InvoiceLine(
            invoice_id=invoice.id,
            description=e_line.description,
            quantity=e_line.quantity,
            unit_price=e_line.unit_price,
            amount=e_line.amount,
            account_id=e_line.account_id
        )
        db.session.add(i_line)
        
    # Update Estimate
    estimate.status = 'INVOICED'
    db.session.commit()
    
    flash(f"Estimate {estimate.estimate_number} successfully converted to Invoice {invoice.invoice_number}.", "success")
    return redirect(url_for('invoices.index'))
