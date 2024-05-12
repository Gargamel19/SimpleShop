from flask.blueprints import Blueprint 

orders_bp = Blueprint('orders', __name__, static_folder="static", template_folder='templates', url_prefix='/orders')

import app.orders.routes