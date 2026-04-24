import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
receipts_bp = Blueprint('receipts', __name__)
from app.models.accounting.receipt import Receipt
from app import db
from app.services.auth_service import get_current_org
from werkzeug.utils import secure_filename
from datetime import datetime
from app.models.accounting.account import Account

@receipts_bp.route('/review/<int:receipt_id>', methods=['GET', 'POST'])
@login_required
def review(receipt_id):
    org = get_current_org()
    receipt = Receipt.query.filter_by(id=receipt_id, organization_id=org.id).first_or_404()
    
    if request.method == 'POST':
        receipt.vendor_name = request.form.get('vendor_name')
        
        amount_str = request.form.get('amount')
        if amount_str:
            receipt.amount = float(amount_str)
            
        date_str = request.form.get('receipt_date')
        if date_str:
            receipt.receipt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        if 'post' in request.form:
            # Mark as processed for now
            receipt.status = 'PROCESSED'
            flash('Receipt details confirmed and posted!', 'success')
            db.session.commit()
            return redirect(url_for('receipts.index'))
            
        db.session.commit()
        flash('Receipt details updated.', 'success')
        return redirect(url_for('receipts.review', receipt_id=receipt.id))

    accounts = Account.query.filter_by(organization_id=org.id).order_by(Account.code).all()
    return render_template('receipts/review.html', receipt=receipt, accounts=accounts)

@receipts_bp.route('/delete/<int:receipt_id>', methods=['POST'])
@login_required
def delete(receipt_id):
    org = get_current_org()
    receipt = Receipt.query.filter_by(id=receipt_id, organization_id=org.id).first_or_404()
    
    # Delete the physical file
    file_path = os.path.join(current_app.static_folder, 'uploads', 'receipts', receipt.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(receipt)
    db.session.commit()
    
    flash('Receipt deleted successfully.', 'success')
    return redirect(url_for('receipts.index'))

@receipts_bp.route('/')
@login_required
def index():
    org = get_current_org()
    receipts = Receipt.query.filter_by(organization_id=org.id).order_by(Receipt.upload_date.desc()).all()
    return render_template('receipts/index.html', receipts=receipts)

@receipts_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    org = get_current_org()
    if 'receipt' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('receipts.index'))
    
    file = request.files['receipt']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('receipts.index'))
    
    if file:
        filename = secure_filename(file.filename)
        # Unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'receipts')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file.save(os.path.join(upload_folder, unique_filename))
        
        new_receipt = Receipt(
            filename=unique_filename,
            original_name=filename,
            organization_id=org.id,
            user_id=current_user.id
        )
        db.session.add(new_receipt)
        db.session.commit()
        
        flash('Receipt uploaded successfully!', 'success')
        return redirect(url_for('receipts.index'))
