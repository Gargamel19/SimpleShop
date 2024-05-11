from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

login_manager = LoginManager()
db = SQLAlchemy()
auth = HTTPBasicAuth()