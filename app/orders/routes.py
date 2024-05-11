from app.orders import orders_bp
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug import exceptions
from app.models import User, Orders
from app.extentions import db, auth
from sqlalchemy.exc import IntegrityError
from flask import render_template_string
import uuid
from functools import wraps



class NotAuthorized(exceptions.HTTPException):
    code = 405 
    description = 'User is not authorized to perform this action'

class OrderNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Order dose not exist.'

class OrderAlreadyExist(exceptions.HTTPException):
    code = 400
    description = 'Order dose already exist.'

@orders_bp.errorhandler(exceptions.HTTPException)
def handle_error(e):
    return e.description, e.code

orders_bp.register_error_handler(OrderNOTExist, handle_error)
orders_bp.register_error_handler(OrderAlreadyExist, handle_error)
orders_bp.register_error_handler(NotAuthorized, handle_error)


### USER ENDPOINTS

@orders_bp.route('/all', methods=['GET'])
def index():
    return render_template("base.html", user=current_user)

### API ENDPOINTS

# ------------------------------------------- PRODUCTS ---------------------------------------------------

    
@orders_bp.route('/', methods=['GET'])
def get_products():
    products = Orders.query.all()
    prod_list = [] 
    for prod in products:
        prod_list.append(prod.to_dict())
    return jsonify(prod_list)



# ------------------------------------------- PRODUCT RESSOURCE ---------------------------------------------------
# CREATE:
@orders_bp.route('/', methods=['POST'])
@login_required
def create_product():
    if current_user.user_type != 1:
        raise NotAuthorized()
    public_id = str(uuid.uuid4())
    supplier = request.form["supplier"]
    
    try:
        order = Orders(public_id=public_id, supplier=supplier)
        db.session.add(order)
        db.session.commit()
    except IntegrityError:
        raise OrderAlreadyExist()
    return order.to_dict()

@orders_bp.route('/<public_id>', methods=['GET'])
def get_product(public_id):
    order = Orders.query.filter(Orders.public_id == public_id).first()
    if not order:
        raise OrderNOTExist()
    return jsonify(order.to_dict())


@orders_bp.route('/<public_id>', methods=['PUT'])
@login_required
def edit_product(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    # TODO: if forms are not given
    supplier = request.form["supplier"]
    order.supplier = supplier
    db.session.commit()
    return jsonify(order.to_dict())

@orders_bp.route('/<public_id>', methods=['DELETE'])
@login_required
def delete_product(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    db.session.delete(order)
    return jsonify(order.to_dict())
