from flask.blueprints import Blueprint 

user_bp = Blueprint('user', __name__, template_folder='templates', url_prefix='/user')

import app.user.routes