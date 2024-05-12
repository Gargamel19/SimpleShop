from flask.blueprints import Blueprint 

products_bp = Blueprint('products', __name__, template_folder='templates', static_folder='static', url_prefix='/products')

import app.products.routes