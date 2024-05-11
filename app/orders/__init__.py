from flask.blueprints import Blueprint 

orders_bp = Blueprint('orders', __name__, template_folder='templates', url_prefix='/orders')

import app.orders.routes