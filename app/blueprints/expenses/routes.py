from flask import Blueprint, render_template
from flask_login import login_required
from app.models.purchases.bill import Bill
from app.services.auth_service import get_current_org

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/transactions')
@login_required
def transactions():
    org = get_current_org()
    # Fetch all expense transactions (primarily bills for now)
    bills = Bill.query.filter_by(organization_id=org.id).order_by(Bill.issue_date.desc()).all()
    return render_template('expenses/transactions.html', bills=bills)
