import click
from flask.cli import with_appcontext
from app.extentions import db
from .models import User
import uuid
from werkzeug.security import generate_password_hash

@click.command(name='create_tables')
@with_appcontext
def create_tables():
    print("create tables")
    from app import create_app
    create_app()
    db.create_all()
    print("tables created")

def add_admin_h(username, firstname, lastname, email, pw, user_type=1):
    print("add_admin")
    pub_id = str(uuid.uuid4())
    password = generate_password_hash(pw, method="pbkdf2:sha256")
    newUser = User(id=pub_id, name=username, firstname=firstname, lastname=lastname, email=email, password=password, user_type=user_type)
    db.session.add(newUser)
    db.session.commit()

def add_user_h(username, firstname, lastname, email, pw, user_type=0):
    print("add_user")
    pub_id = str(uuid.uuid4())
    password = generate_password_hash(pw, method="pbkdf2:sha256")
    newUser = User(id=pub_id, name=username, firstname=firstname, lastname=lastname, email=email, password=password, user_type=user_type)
    db.session.add(newUser)
    db.session.commit()

@click.command(name='add_testdata')
@with_appcontext
def add_testdata():
    add_admin_h("fettarmqp", "ferdinand", "trendelenburg", "trendelenburger19.04@gmail.com", "1234", user_type=1)
    add_user_h("testuser", "testuser", "testuser", "testuser@gmail.com", "1234", user_type=0)



