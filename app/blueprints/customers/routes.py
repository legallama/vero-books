from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from ._bp import customers_bp
from app.models.crm.contact import Customer
from app.models.crm.appointment import Appointment
from app.models.sales.estimate import Estimate
from app.extensions import db
from app.services.auth_service import get_current_org
from datetime import datetime

@customers_bp.route('/overview')
@login_required
def overview():
    org = get_current_org()
    total_customers = Customer.query.filter_by(organization_id=org.id).count()
    upcoming_appointments = Appointment.query.filter_by(organization_id=org.id).filter(Appointment.start_time >= datetime.utcnow()).order_by(Appointment.start_time.asc()).limit(5).all()
    recent_estimates = Estimate.query.filter_by(organization_id=org.id).order_by(Estimate.issue_date.desc()).limit(5).all()
    
    return render_template('crm/overview.html', 
                         total_customers=total_customers,
                         upcoming_appointments=upcoming_appointments,
                         recent_estimates=recent_estimates)

@customers_bp.route('/appointments')
@login_required
def appointments():
    org = get_current_org()
    appointments = Appointment.query.filter_by(organization_id=org.id).order_by(Appointment.start_time.desc()).all()
    return render_template('crm/appointments.html', appointments=appointments)

@customers_bp.route('/appointments/create', methods=['GET', 'POST'])
@login_required
def create_appointment():
    org = get_current_org()
    customers = Customer.query.filter_by(organization_id=org.id).all()
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        title = request.form.get('title')
        description = request.form.get('description')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        location = request.form.get('location')
        
        # Parse dates
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
        
        new_appt = Appointment(
            organization_id=org.id,
            customer_id=customer_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location
        )
        db.session.add(new_appt)
        db.session.commit()
        
        flash("Appointment scheduled.", "success")
        return redirect(url_for('customers.appointments'))
        
    return render_template('crm/appointments_create.html', customers=customers)

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
