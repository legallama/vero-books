from flask import Blueprint

fixed_assets_bp = Blueprint('fixed_assets', __name__, template_folder='templates')

from . import routes
