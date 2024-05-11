import click
from flask.cli import with_appcontext
from app.extentions import db
from .models import User
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash

@click.command(name='create_tables')
@with_appcontext
def create_tables():
    print("create tables")
    from app import create_app
    create_app()
    db.create_all()