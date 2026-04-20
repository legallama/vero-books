from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models to ensure they are registered
    from app.models.admin import organization, user
    from app.models.accounting import account, journal, tax, payment, bank_rule
    from app.models.crm import contact
    from app.models.sales import invoice, estimate, recurring
    from app.models.purchases import bill
    from app.models.audit import log

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.accounts import accounts_bp
    from app.blueprints.journal import journal_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.vendors import vendors_bp
    from app.blueprints.invoices import invoices_bp
    from app.blueprints.bills import bills_bp
    from app.blueprints.banking import banking_bp
    from app.blueprints.estimates import estimates_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.tags import tags_bp
    from app.blueprints.recurring.routes import recurring_bp
    from app.blueprints.audit.routes import audit_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(bills_bp)
    app.register_blueprint(banking_bp)
    app.register_blueprint(estimates_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(audit_bp)

    @app.errorhandler(400)
    def handle_csrf_error(e):
        if 'CSRF' in str(e):
            from flask import flash, redirect, url_for
            flash("Your session has expired. Please try again.", "danger")
            return redirect(url_for('auth.login'))
        return e, 400

    @app.context_processor
    def inject_org():
        from app.services.auth_service import get_current_org
        return dict(current_org=get_current_org())

    with app.app_context():
        db.create_all()

    return app
