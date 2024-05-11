from flask import Flask
from flask_cors import CORS, cross_origin
import os

from app.extentions import login_manager

from app.extentions import db
from flask_font_awesome import FontAwesome



font_awesome = FontAwesome()

def create_app(type="run"):
    app = Flask(__name__)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    
    app.chat_reader_player = []
    app.recent_votes = {}

    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    if type == "test":
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.sqlite'
        app.config['TESTING'] = True
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)
    font_awesome.init_app(app)

    login_manager.login_view = 'user.index'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    from app.user import user_bp
    app.register_blueprint(user_bp)

    from app.products import products_bp
    app.register_blueprint(products_bp)

    from app.suppliers import suppliers_bp
    app.register_blueprint(suppliers_bp)

    from app.commands import create_tables
    app.cli.add_command(create_tables)

    from app import models

    return app