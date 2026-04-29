from flask import Blueprint

migration_bp = Blueprint('migration', __name__, url_prefix='/migration')

from . import routes
