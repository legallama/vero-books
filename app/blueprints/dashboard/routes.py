from flask import render_template
from flask_login import login_required
from ._bp import dashboard_bp
from app.extensions import db

@dashboard_bp.route('/')
@login_required
def index():
    from app.services.auth_service import get_current_org
    from app.models.sales.invoice import Invoice
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    org = get_current_org()
    if not org:
        from flask import flash, redirect, url_for
        flash("Please select or create an organization to continue.", "warning")
        return redirect(url_for('auth.logout'))
    
    # Get revenue by month for last 6 months - Using strftime for SQLite compatibility
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    revenue_data = db.session.query(
        func.strftime('%Y-%m-01', Invoice.issue_date).label('month'),
        func.sum(Invoice.total).label('total')
    ).filter(
        Invoice.organization_id == org.id,
        Invoice.issue_date >= six_months_ago
    ).group_by('month').order_by('month').all()
    
    chart_labels = [datetime.strptime(r.month, '%Y-%m-%d').strftime('%b') for r in revenue_data]
    chart_values = [float(r.total) for r in revenue_data]
    
    return render_template('dashboard/index.html', 
                          chart_labels=chart_labels, 
                          chart_values=chart_values)
