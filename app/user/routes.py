from app.user import user_bp
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug import exceptions
from app.models import User
from app.extentions import db, auth
from sqlalchemy.exc import IntegrityError
from flask import render_template_string
import uuid
import jwt
from functools import wraps



class NotAuthorized(exceptions.HTTPException):
    code = 405 
    description = 'User is not authorized to perform this action'

class UserNOTExist(exceptions.HTTPException):
    code = 404
    description = 'User dose not exist.'

class UserAlreadyExist(exceptions.HTTPException):
    code = 400
    description = 'User dose already exist.'

@user_bp.errorhandler(exceptions.HTTPException)
def handle_error(e):
    return e.description, e.code

user_bp.register_error_handler(UserNOTExist, handle_error)
user_bp.register_error_handler(UserAlreadyExist, handle_error)
user_bp.register_error_handler(NotAuthorized, handle_error)

@user_bp.route('/', methods=['GET'])
def index():
    return render_template("base.html", user=current_user)

### USER ENDPOINTS

# login user
@user_bp.route('/login')
def login():
    return render_template("login.html", user=current_user)

# logout user
@user_bp.route('/logout')
def logout():
    auth_logout()
    return redirect(url_for('user.login'))

### API ENDPOINTS

# ------------------------------------------- LOGIN ---------------------------------------------------

    
@user_bp.route('/auth/login', methods=['POST'])
def auth_login():
    username = request.form["username"]
    pw = request.form["password"]
    remember = True if request.form.get("remember") else False
    user = User.query.filter(User.name == username).first()
    if not user or not check_password_hash(user.password, pw):
        flash("Please check your login details and try again")
        return redirect(url_for("user.login"))
    login_user(user, remember=remember)
    return redirect(url_for("user.index"))

# ------------------------------------------- LOGOUT ---------------------------------------------------


@user_bp.route('/auth/logout', methods=['POST'])
@login_required
def auth_logout():
    logout_user()


# ------------------------------------------- USER RESSOURCE ---------------------------------------------------
# CREATE:

@user_bp.route('/', methods=['POST'])
def create_user():
    username = request.form["username"]
    firstName = request.form["firstName"]
    lastName = request.form["lastName"]
    email = request.form["email"]
    pw = request.form["password"]
    password = generate_password_hash(pw, method="pbkdf2:sha256")
    public_id = str(uuid.uuid4())

    try:
        user = User(public_id=public_id, name=username, firstname=firstName, lastname=lastName, email=email, password=password, user_type=0)
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        raise UserAlreadyExist()

    return user.get_as_obj()

# GET
@user_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    
    user = User.query.filter(User.public_id == user_id).first()
    if not user:
        raise UserNOTExist()
    return user.get_as_obj()

# UPDATE
@user_bp.route('/<user_id>', methods=['PUT'])
@login_required
def edit_user(user_id):
    if not (user_id == current_user.public_id or current_user.user_type == 1):
        raise NotAuthorized()
    username = request.form["username"]
    firstName = request.form["firstName"]
    lastName = request.form["lastName"]
    email = request.form["email"]
    pw = request.form["password"]
    password = generate_password_hash(pw, method="pbkdf2:sha256")
    user = User.query.filter(User.public_id == user_id).first()
    if not user:
        raise UserNOTExist()
    user.name = username
    user.firstName = firstName
    user.lastName = lastName
    user.email = email
    user.password = password
    db.session.add(user)
    db.session.commit()
    return user.get_as_obj()

# DELETE
@user_bp.route('/<public_id>', methods=['DELETE'])
@login_required
def delete_user(public_id):
    if not (public_id == current_user.public_id or current_user.user_type == 1):
        raise NotAuthorized()
    user = User.query.filter(User.public_id == public_id).first()
    if not user:
        raise UserNOTExist()
    db.session.delete(user)
    db.session.commit()
    return user.get_as_obj()

# PROMOTE
@user_bp.route('/<user_id>/promote', methods=['POST'])
@login_required
def promote_user(user_id):
    if not (current_user.user_type == 1):
        raise NotAuthorized()
    user = User.query.filter(User.public_id == user_id).first()
    if not user:
        raise UserNOTExist()
    user.user_type=1
    db.session.commit()
    return user.get_as_obj()
