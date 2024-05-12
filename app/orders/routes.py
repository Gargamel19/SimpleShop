from app.orders import orders_bp
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug import exceptions
from app.models import User, Products, Orders, OrdersPOS
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
    
class OrderPosNOTExist(exceptions.HTTPException):
    code = 404
    description = 'OrderPOS dose not exist.'

class ProductNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Product dose not exist.'

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
def get_orders():
    orders = Orders.query.all()
    order_list = [] 
    for order in orders:
        order_json = order.to_dict()
        order_poss = OrdersPOS.query.filter_by(order_id = order.public_id).all()
        order_json["pos"] = []
        for order_pos in order_poss:
            order_json["pos"].append(order_pos.to_dict())
        order_list.append(order_json)
        
    return jsonify(order_list)



# ------------------------------------------- PRODUCT RESSOURCE ---------------------------------------------------
# CREATE:
@orders_bp.route('/', methods=['POST'])
@login_required
def create_order():
    print("HERE")
    if current_user.user_type != 1:
        raise NotAuthorized()
    public_id = str(uuid.uuid4())
    if "order_type" in request.form:
        order_type = int(request.form["order_type"])
    if "supplier" in request.form:
        supplier = request.form["supplier"]
    if "customer" in request.form:
        customer = request.form["customer"]
    try:
        if order_type == 0:
            order = Orders(public_id=public_id, supplier=supplier, type=order_type)
            db.session.add(order)
            db.session.commit()
        else:
            order = Orders(public_id=public_id, customer=customer, type=order_type)
            db.session.add(order)
            db.session.commit()
    except IntegrityError:
        print("OrderAlreadyExist")
        raise OrderAlreadyExist()
    return order.to_dict()


@orders_bp.route('/<public_id>', methods=['GET'])
def get_order(public_id):
    order = Orders.query.filter(Orders.public_id == public_id).first()
    if not order:
        raise OrderNOTExist()
    order_json = order.to_dict()
    order_poss = OrdersPOS.query.filter_by(order_id = public_id).all()
    order_json["pos"] = []
    for order_pos in order_poss:
        order_json["pos"].append(order_pos.to_dict())
    return jsonify(order_json)


@orders_bp.route('/<public_id>', methods=['PUT'])
@login_required
def edit_order(public_id):
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
def delete_order(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    db.session.delete(order)
    return jsonify(order.to_dict())


##### POS 

@orders_bp.route('/<public_id>/pos/add', methods=['PUT'])
@login_required
def add_order_pos(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    OrdersPOS_id = str(uuid.uuid4())
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    product_id = request.form["product_id"]
    product = Products.query.filter_by(public_id=product_id).first()
    if not product:
        raise ProductNOTExist()
    amount = request.form["amount"]
    pos = OrdersPOS(public_id=OrdersPOS_id, order_id=public_id, product_id=product_id, costs=float(amount)*product.price, amount=amount)
    db.session.add(pos)
    db.session.commit()
    return jsonify(pos.to_dict())

@orders_bp.route('/<public_id>/pos/', methods=['GET'])
def get_order_poss(public_id):
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter_by(order_id = public_id).all()
    order_pos_list = []
    for order_pos in pos:
        order_pos_list.append(order_pos.to_dict())
    return jsonify(order_pos_list)

# EDIT POS
@orders_bp.route('/<public_id>/pos/<pos_id>', methods=['PUT'])
@login_required
def edit_order_pos(public_id, pos_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter_by(public_id=pos_id).first()
    if not order:
        raise OrderPosNOTExist()
    product_id = request.form["product_id"]
    product = Products.query.filter_by(public_id=product_id).first()
    if not product:
        raise ProductNOTExist()
    amount = request.form["amount"]
    pos.product_id = product_id
    pos.amount = amount
    pos.costs = float(amount)*product.price
    db.session.commit()
    return jsonify(pos.to_dict())

@orders_bp.route('/<public_id>/pos/<pos_id>', methods=['GET'])
def get_order_pos(public_id, pos_id):
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter_by(public_id=pos_id).first()
    if not order:
        raise OrderPosNOTExist()
    return jsonify(pos.to_dict())

# DELETE POS
@orders_bp.route('/<public_id>/pos/<pos_id>', methods=['DELETE'])
@login_required
def delete_order_pos(public_id, pos_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter_by(public_id=pos_id).first()
    if not order:
        raise OrderPosNOTExist()
    db.session.delete(pos)
    db.session.commit()
    return jsonify(pos.to_dict())