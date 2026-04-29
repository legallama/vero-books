from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ._bp import budgets_bp
from app.models.accounting.budget import Budget, BudgetLine
from app.models.accounting.account import Account
from app.services.auth_service import get_current_org
from app.extensions import db
from decimal import Decimal

@budgets_bp.route('/')
@login_required
def index():
    org = get_current_org()
    budgets = Budget.query.filter_by(organization_id=org.id).all()
    return render_template('budgets/index.html', budgets=budgets)

@budgets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org = get_current_org()
    if request.method == 'POST':
        budget = Budget(
            organization_id=org.id,
            name=request.form.get('name'),
            fiscal_year=int(request.form.get('fiscal_year'))
        )
        db.session.add(budget)
        db.session.commit()
        flash("Budget created. Now add your targets.", "success")
        return redirect(url_for('budgets.edit', budget_id=budget.id))
        
    return render_template('budgets/create.html')

@budgets_bp.route('/<budget_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(budget_id):
    org = get_current_org()
    budget = Budget.query.filter_by(id=budget_id, organization_id=org.id).first_or_404()
    
    if request.method == 'POST':
        # Clear existing lines and rebuild from form
        BudgetLine.query.filter_by(budget_id=budget.id).delete()
        
        for key, value in request.form.items():
            if key.startswith('amount_'):
                parts = key.split('_')
                account_id = parts[1]
                period = int(parts[2])
                amount = Decimal(value or 0)
                
                if amount != 0:
                    line = BudgetLine(
                        budget_id=budget.id,
                        account_id=account_id,
                        period=period,
                        amount=amount
                    )
                    db.session.add(line)
        
        db.session.commit()
        flash("Budget updated successfully.", "success")
        return redirect(url_for('budgets.index'))

    # Prepare data for grid
    accounts = Account.query.filter_by(organization_id=org.id).filter(Account.type.in_(['Revenue', 'Expense'])).all()
    lines = BudgetLine.query.filter_by(budget_id=budget.id).all()
    
    # Map lines to [account_id][period]
    budget_map = {}
    for line in lines:
        if line.account_id not in budget_map:
            budget_map[line.account_id] = {}
        budget_map[line.account_id][line.period] = line.amount
        
    return render_template('budgets/edit.html', budget=budget, accounts=accounts, budget_map=budget_map)
