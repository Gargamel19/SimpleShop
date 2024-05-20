from app.products import products_bp
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug import exceptions
from app.models import User, Products
from app.extentions import db, auth
from sqlalchemy.exc import IntegrityError, StatementError
from flask import render_template_string
import uuid
import jwt
from functools import wraps


class WrongParameters(exceptions.HTTPException):
    code = 405 
    description = '"price" must be an float with "." ad decimal Sign'

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
def all():
    products_query = Products.query
    
    if "sort" in request.args:
        sort_value = request.args["sort"]
        if sort_value=="price":
            products_query=products_query.order_by(Products.price.desc())
        elif sort_value=="stock":
            products_query=products_query.order_by(Products.stock.desc())
    products = products_query.all()
    return render_template("products.html", user=current_user, products=products)


@products_bp.route('/<public_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(public_id):
    if request.method == 'GET':
        product = Products.query.filter_by(public_id=public_id).first()
        return render_template("products_edit.html", user=current_user, product=product)
    else:
        edit_product(public_id)
        return redirect(url_for('products.all'))

@products_bp.route('/<public_id>/delete', methods=['GET', 'POST'])
@login_required
def delete(public_id):
    if request.method == 'GET':
        product = Products.query.filter_by(public_id=public_id).first()
        return render_template("products_delete.html", user=current_user, product=product)
    else:
        delete_product(public_id)
        return redirect(url_for('products.all'))
    
@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        return render_template("products_create.html", user=current_user)
    else:
        create_product()
        return redirect(url_for('products.all'))

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
    except StatementError:
        raise WrongParameters()
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
    product = Products.query.filter_by(public_id=public_id).first()
    if not product:
        raise ProductNOTExist()
    db.session.delete(product)
    db.session.commit()
    return jsonify(product.to_dict())
