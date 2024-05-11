from app.products import products_bp
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug import exceptions
from app.models import User, Products
from app.extentions import db, auth
from sqlalchemy.exc import IntegrityError
from flask import render_template_string
import uuid
import jwt
from functools import wraps



class NotAuthorized(exceptions.HTTPException):
    code = 405 
    description = 'User is not authorized to perform this action'

class ProductNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Product dose not exist.'

class ProductAlreadyExist(exceptions.HTTPException):
    code = 400
    description = 'Product dose already exist.'

@products_bp.errorhandler(exceptions.HTTPException)
def handle_error(e):
    return e.description, e.code

products_bp.register_error_handler(ProductNOTExist, handle_error)
products_bp.register_error_handler(ProductAlreadyExist, handle_error)
products_bp.register_error_handler(NotAuthorized, handle_error)


### USER ENDPOINTS

@products_bp.route('/all', methods=['GET'])
def index():
    return render_template("base.html", user=current_user)

### API ENDPOINTS

# ------------------------------------------- PRODUCTS ---------------------------------------------------

    
@products_bp.route('/', methods=['GET'])
def get_products():
    products = Products.query.all()
    prod_list = [] 
    for prod in products:
        prod_list.append(prod.to_dict())
    return jsonify(prod_list)



# ------------------------------------------- PRODUCT RESSOURCE ---------------------------------------------------
# CREATE:
@products_bp.route('/', methods=['POST'])
@login_required
def create_product():
    if current_user.user_type != 1:
        raise NotAuthorized()
    public_id = str(uuid.uuid4())
    title = request.form["title"]
    price = request.form["price"]
    stock = request.form["stock"]
    
    try:
        prod = Products(public_id=public_id, title=title, price=price, stock=stock)
        db.session.add(prod)
        db.session.commit()
    except IntegrityError:
        raise ProductAlreadyExist()
    
    return prod.to_dict()

@products_bp.route('/<public_id>', methods=['GET'])
def get_product(public_id):
    product = Products.query.filter(Products.public_id == public_id).first()
    if not product:
        raise ProductNOTExist()
    return jsonify(product.to_dict())


@products_bp.route('/<public_id>', methods=['PUT'])
@login_required
def edit_product(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    product = Products.query.filter(Products.public_id == public_id).first()
    if not product:
        raise ProductNOTExist()
    # TODO: if forms are not given
    title = request.form["title"]
    price = request.form["price"]
    stock = request.form["stock"]
    product.title = title
    product.price = price
    product.stock = stock
    db.session.commit()
    return jsonify(product.to_dict())

@products_bp.route('/<public_id>', methods=['DELETE'])
@login_required
def delete_product(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    product = Products.query.filter(Products.public_id == public_id).first()
    if not product:
        raise ProductNOTExist()
    db.session.delete(product)
    return jsonify(product.to_dict())
