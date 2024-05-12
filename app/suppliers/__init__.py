from flask.blueprints import Blueprint 

suppliers_bp = Blueprint('suppliers', __name__, static_folder="static", template_folder='templates', url_prefix='/suppliers')

import app.suppliers.routes