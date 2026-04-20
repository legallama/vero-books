from app.models.accounting.account import Account, AccountType
from app.extensions import db

def seed_standard_accounts(organization_id):
    standard_accounts = [
        # Assets (1000-1999)
        {'code': '1010', 'name': 'Cash on Hand', 'type': 'Asset', 'subtype': 'Cash and Cash Equivalents'},
        {'code': '1020', 'name': 'Operating Checking', 'type': 'Asset', 'subtype': 'Bank'},
        {'code': '1100', 'name': 'Accounts Receivable (A/R)', 'type': 'Asset', 'subtype': 'Accounts Receivable'},
        {'code': '1200', 'name': 'Inventory Asset', 'type': 'Asset', 'subtype': 'Inventory'},
        {'code': '1500', 'name': 'Furniture & Equipment', 'type': 'Asset', 'subtype': 'Fixed Assets'},
        
        # Liabilities (2000-2999)
        {'code': '2000', 'name': 'Accounts Payable (A/P)', 'type': 'Liability', 'subtype': 'Accounts Payable'},
        {'code': '2100', 'name': 'Credit Card - Corporate', 'type': 'Liability', 'subtype': 'Credit Card'},
        {'code': '2200', 'name': 'Sales Tax Payable', 'type': 'Liability', 'subtype': 'Other Current Liabilities'},
        
        # Equity (3000-3999)
        {'code': '3000', 'name': 'Owner\'s Equity', 'type': 'Equity', 'subtype': 'Equity'},
        {'code': '3100', 'name': 'Retained Earnings', 'type': 'Equity', 'subtype': 'Equity'},
        
        # Income (4000-4999)
        {'code': '4000', 'name': 'Product Sales', 'type': 'Income', 'subtype': 'Service/Fee Income'},
        {'code': '4100', 'name': 'Service Income', 'type': 'Income', 'subtype': 'Service/Fee Income'},
        
        # COGS (5000-5999)
        {'code': '5000', 'name': 'Cost of Goods Sold', 'type': 'Expense', 'subtype': 'Cost of Goods Sold'},
        
        # Expenses (6000-7999)
        {'code': '6000', 'name': 'Advertising & Promotion', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6100', 'name': 'Bank Charges & Fees', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6200', 'name': 'Insurance', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6300', 'name': 'Office Supplies & Software', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6400', 'name': 'Rent or Lease', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6500', 'name': 'Utilities', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6600', 'name': 'Travel & Meals', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
        {'code': '6700', 'name': 'Professional Fees', 'type': 'Expense', 'subtype': 'Other Business Expenses'},
    ]
    
    for acc_data in standard_accounts:
        # Check if exists
        existing = Account.query.filter_by(organization_id=organization_id, code=acc_data['code']).first()
        if not existing:
            new_acc = Account(
                organization_id=organization_id,
                code=acc_data['code'],
                name=acc_data['name'],
                type=acc_data['type'],
                subtype=acc_data['subtype']
            )
            db.session.add(new_acc)
    
    db.session.commit()
