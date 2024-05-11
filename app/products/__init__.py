from flask.blueprints import Blueprint 

products_bp = Blueprint('products', __name__, template_folder='templates', url_prefix='/products')

import app.products.routes