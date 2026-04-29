import uuid
import hashlib
import secrets
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from . import developer_bp
from app.models.admin.api_key import ApiKey
from app.models.admin.webhook import WebhookEndpoint, WebhookDelivery
from app.extensions import db
from app.services.auth_service import get_current_org

@developer_bp.route('/')
@login_required
def index():
    org = get_current_org()
    api_keys = ApiKey.query.filter_by(organization_id=org.id).all()
    webhooks = WebhookEndpoint.query.filter_by(organization_id=org.id).all()
    return render_template('developer/index.html', api_keys=api_keys, webhooks=webhooks)

@developer_bp.route('/api-keys/create', methods=['POST'])
@login_required
def create_api_key():
    org = get_current_org()
    name = request.form.get('name')
    
    # Generate token
    raw_token = secrets.token_urlsafe(32)
    token_prefix = 'vb_live_'
    full_token = token_prefix + raw_token
    token_hash = hashlib.sha256(full_token.encode()).hexdigest()
    
    new_key = ApiKey(
        organization_id=org.id,
        user_id=current_user.id,
        name=name,
        token_prefix=token_prefix + raw_token[:4],
        token_hash=token_hash
    )
    db.session.add(new_key)
    db.session.commit()
    
    flash(f"API Key created! Please copy your key now, it will not be shown again: {full_token}", "success")
    return redirect(url_for('developer.index'))

@developer_bp.route('/webhooks/create', methods=['POST'])
@login_required
def create_webhook():
    org = get_current_org()
    url = request.form.get('url')
    description = request.form.get('description')
    events = request.form.get('events', '*')
    
    secret = secrets.token_urlsafe(24)
    
    new_wh = WebhookEndpoint(
        organization_id=org.id,
        url=url,
        description=description,
        subscribed_events=events,
        secret=secret
    )
    db.session.add(new_wh)
    db.session.commit()
    
    flash("Webhook endpoint successfully added.", "success")
    return redirect(url_for('developer.index'))
