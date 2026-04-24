from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.admin.team import TeamMember
from app.services.auth_service import get_current_org

team_bp = Blueprint('team', __name__)

@team_bp.route('/overview')
@login_required
def overview():
    org = get_current_org()
    total_staff = TeamMember.query.filter_by(organization_id=org.id).count()
    employees = TeamMember.query.filter_by(organization_id=org.id, type='EMPLOYEE').count()
    contractors = TeamMember.query.filter_by(organization_id=org.id, type='CONTRACTOR').count()
    
    return render_template('team/overview.html', 
                         total_staff=total_staff,
                         employee_count=employees,
                         contractor_count=contractors)

@team_bp.route('/employees')
@login_required
def employees():
    org = get_current_org()
    members = TeamMember.query.filter_by(organization_id=org.id, type='EMPLOYEE').all()
    return render_template('team/list.html', members=members, title="Employees", type="EMPLOYEE")

@team_bp.route('/contractors')
@login_required
def contractors():
    org = get_current_org()
    members = TeamMember.query.filter_by(organization_id=org.id, type='CONTRACTOR').all()
    return render_template('team/list.html', members=members, title="Contractors", type="CONTRACTOR")

@team_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    member_type = request.args.get('type', 'EMPLOYEE')
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role')
        member_type = request.form.get('type')
        hourly_rate = request.form.get('hourly_rate')
        
        from app.extensions import db
        new_member = TeamMember(
            organization_id=org.id,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            type=member_type,
            hourly_rate=hourly_rate
        )
        db.session.add(new_member)
        db.session.commit()
        
        flash(f"{member_type.capitalize()} added successfully.", "success")
        return redirect(url_for('team.employees' if member_type == 'EMPLOYEE' else 'team.contractors'))
        
    return render_template('team/create.html', member_type=member_type)
