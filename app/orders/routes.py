from app.orders import orders_bp
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug import exceptions
from app.models import User, Products, Suppliers, Suppliers_Products, Orders, OrdersPOS
from app.extentions import db, auth
from sqlalchemy.exc import IntegrityError
from flask import render_template_string
import uuid
from functools import wraps
from datetime import datetime
from operator import itemgetter, attrgetter


def read_order_content(order):
    '''
    gets order positions of orders and gets products of orders positions.
    also sums up all costs and amounts and returns a dict representation of the Order, OrderPOS and Products.
    '''
    ordersPOS = OrdersPOS.query.filter(OrdersPOS.order_id==order.public_id).all()
    order_json = order.to_dict()
    order_json["total_costs"] = 0
    order_json["total_amount"] = 0
    date = datetime.strptime(order_json["order_date"], '%Y-%m-%d %H:%M:%S')
    order_json["order_date"] = date.strftime('%d.%m.%y %H:%M')
    if order.supplier:
        supplier = Suppliers.query.filter(Suppliers.public_id==order.supplier).first()
        order_json["supplier"] = supplier.to_dict()
    ordersPOS_json = []
    for pos in ordersPOS:
        new_pos = pos.to_dict()
        order_json["total_costs"] += pos.costs
        order_json["total_amount"] += pos.amount
        new_pos["product"] = Products.query.filter(Products.public_id==pos.product_id).first()
        ordersPOS_json.append(new_pos)
    order_json["total_amount"] = round(order_json["total_amount"], 2)
    order_json["total_costs"] = round(order_json["total_costs"], 2)
    order_json["pos"] = ordersPOS_json
    return order_json

def recompute_stock(order, product, amount):
    '''
    recomputing the stock-values of an product.
    '''
    if order.type == 0:
        product.stock = int(product.stock) + int(amount)
    elif order.type == 1:
        product.stock = int(product.stock) - int(amount)

class NotAuthorized(exceptions.HTTPException):
    code = 405 
    description = 'User is not authorized to perform this action'

class OrderNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Order not exist.'
    
class OrderPosNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Order Position not exist.'

class ProductNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Product not exist.'

class OrderAlreadyExist(exceptions.HTTPException):
    code = 400
    description = 'Order already exist.'

@orders_bp.errorhandler(exceptions.HTTPException)
def handle_error(e):
    return e.description, e.code

orders_bp.register_error_handler(OrderNOTExist, handle_error)
orders_bp.register_error_handler(OrderAlreadyExist, handle_error)
orders_bp.register_error_handler(NotAuthorized, handle_error)


### USER ENDPOINTS

@orders_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():

    products_aos = Products.query.order_by(Products.stock).filter(Products.stock<0).all()
    products_close_aos = Products.query.order_by(Products.stock).filter(Products.stock<10, Products.stock>0).all()
    products = Products.query.order_by(Products.stock).filter(Products.stock>10).all()

    orders = Orders.query.order_by(Orders.order_date.desc()).limit(5).all()
    orders_by_date = {}
    for order in orders:
        temp_date = str(order.order_date.date())
        if not temp_date in orders_by_date:
            orders_by_date[temp_date] = []
        order_json = read_order_content(order)
        orders_by_date[temp_date].append(order_json)
    return render_template("dashboard.html", user=current_user, orders_by_date=orders_by_date, products_aos=products_aos, products_close_aos=products_close_aos, products=products)


@orders_bp.route('/all', methods=['GET'])
@login_required
def all():

    order_query = Orders.query

    # filtering by 'customer' od 'supplier' and sorting by 'date' in query-argument 
    if "customer" in request.args:
        filter_value = request.args["customer"]
        order_query=order_query.filter(Orders.customer.ilike(filter_value))
    if "supplier" in request.args:
        filter_value = request.args["supplier"]
        order_query=order_query.filter(Orders.supplier.ilike(filter_value))
    if "sort" in request.args:
        sort_value = request.args["sort"]
        if sort_value=="date":
            order_query=order_query.order_by(Orders.order_date.desc())

    orders = order_query.all()
    orders_json = []
    for order in orders:
        order_json = read_order_content(order)
        orders_json.append(order_json)


    return render_template("orders.html", user=current_user, orders=orders_json)

@orders_bp.route('/<public_id>/one', methods=['GET'])
@login_required
def one(public_id):
    order = Orders.query.filter(Orders.public_id==public_id).first()
    order_json = read_order_content(order)
    return render_template("order.html", user=current_user, orders=[order_json])

@orders_bp.route('/create_order_customer', methods=['GET', 'POST'])
@login_required
def create_customer():
    if request.method == "GET":
        return render_template("orders_customer_create.html", user=current_user)
    else:
        create_order()
        return redirect(url_for('orders.all'))

@orders_bp.route('/create_order_supply', methods=['GET', 'POST'])
@login_required
def create_supplier():
    if request.method == "GET":
        supplier = Suppliers.query.all()
        return render_template("orders_supply_create.html", user=current_user, supplier=supplier)
    else:
        create_order()
        return redirect(url_for('orders.all'))


@orders_bp.route('<public_id>/edit_order_supply', methods=['GET', 'POST'])
@login_required
def edit_supplier(public_id):
    if request.method == "GET":
        supplier = Suppliers.query.all()
        order = Orders.query.filter_by(public_id=public_id).first()
        return render_template("orders_supply_edit.html", user=current_user, supplier=supplier, order=order)
    else:
        edit_order(public_id)
        return redirect(url_for('orders.all'))
    

@orders_bp.route('<public_id>/edit_order_customer', methods=['GET', 'POST'])
@login_required
def edit_customer(public_id):
    if request.method == "GET":
        order = Orders.query.filter_by(public_id=public_id).first()
        return render_template("orders_customer_edit.html", user=current_user, order=order)
    else:
        edit_order(public_id, type=0)
        return redirect(url_for('orders.all'))


@orders_bp.route('/<public_id>/delete', methods=['GET', 'POST'])
@login_required
def delete(public_id):
    if request.method == "GET":
        order = Orders.query.filter_by(public_id=public_id).first()
        return render_template("orders_delete.html", user=current_user, order=order)
    else:
        delete_order(public_id)
        return redirect(url_for('orders.all'))
    

##### POS #####

@orders_bp.route('/<public_id>/positions/add', methods=['GET', 'POST'])
@login_required
def create_pos(public_id):
    if request.method == "GET":
        order = Orders.query.filter_by(public_id=public_id).first()
        if order.type == 0:
            products = db.session.query(Suppliers_Products.product_public_id, Products.title).join(Products, Suppliers_Products.product_public_id==Products.public_id).filter(Suppliers_Products.supplier_public_id==order.supplier).all()
        else:
            products = db.session.query(Products.public_id, Products.title).all()
        return render_template("orders_create_pos.html", user=current_user, order=order, products=products)
    else:
        add_order_pos(public_id)
        return redirect(url_for('orders.all'))

@orders_bp.route('/<public_id>/positions/<pos_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_pos(public_id, pos_id):
    if request.method == 'GET':
        order = Orders.query.filter_by(public_id=public_id).first()
        orderPOS = OrdersPOS.query.filter(OrdersPOS.public_id == pos_id).first()
        orderPOS_json = orderPOS.to_dict()
        product = Products.query.filter(Products.public_id == orderPOS.product_id).first()
        orderPOS_json["product"] = product.to_dict()
        return render_template("orders_delete_pos.html", user=current_user, order=order, pos=orderPOS_json)
    else:
        delete_order_pos(public_id, pos_id)
        return redirect(url_for('orders.all'))


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
    # loged in user is not admin
    if current_user.user_type != 1:
        raise NotAuthorized()
    public_id = str(uuid.uuid4())
    order_type = None
    supplier = None
    customer = None
    if "order_type" in request.form:
        order_type = int(request.form["order_type"])
    if "supplier" in request.form:
        supplier = request.form["supplier"]
    if "customer" in request.form:
        customer = request.form["customer"]
    if not ((order_type==0 and supplier) or (order_type==1 and customer)):
        abort(405)
    try:
        if order_type == 0:
            order = Orders(public_id=public_id, supplier=supplier, type=order_type, order_date=datetime.now())
            db.session.add(order)
            db.session.commit()
        else:
            order = Orders(public_id=public_id, customer=customer, type=order_type, order_date=datetime.now())
            db.session.add(order)
            db.session.commit()
    except IntegrityError:
        raise OrderAlreadyExist()
    return order.to_dict()


@orders_bp.route('/<public_id>', methods=['GET'])
def get_order(public_id):
    order = Orders.query.filter(Orders.public_id == public_id).first()
    # Order of public_id do not exist 
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
def edit_order(public_id, type=1):
    # loged in user is not admin
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
    if not order:
        raise OrderNOTExist()
    customer = None
    supplier = None
    # TODO: if forms are not given
    if "supplier" in request.form:
        supplier = request.form["supplier"]
        order.supplier = supplier
    if "customer" in request.form:
        customer = request.form["customer"]
        order.customer = customer
    if not ((order.type == 0 and supplier) or (order.type == 1 and customer)):
        abort(405)
    db.session.commit()
    return jsonify(order.to_dict())

@orders_bp.route('/<public_id>', methods=['DELETE'])
@login_required
def delete_order(public_id):
    # loged in user is not admin
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
    if not order:
        raise OrderNOTExist()
    # delete all pos of order
    orderPos = OrdersPOS.query.filter_by(order_id=public_id).all()
    for pos in orderPos:
        product = Products.query.filter_by(public_id=pos.product_id).first()
        recompute_stock(order, product, -pos.amount)
        db.session.delete(pos)
    db.session.delete(order)
    db.session.commit()
    return jsonify(order.to_dict())


##### POS #####

@orders_bp.route('/<public_id>/pos/add', methods=['PUT'])
@login_required
def add_order_pos(public_id):
    # loged in user is not admin
    if current_user.user_type != 1:
        raise NotAuthorized()
    OrdersPOS_id = str(uuid.uuid4())
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
    if not order:
        raise OrderNOTExist()
    product_id = request.form["product_id"]
    product = Products.query.filter_by(public_id=product_id).first()
    if not product:
        raise ProductNOTExist()
    amount = request.form["amount"]
    pos = OrdersPOS(public_id=OrdersPOS_id, order_id=public_id, product_id=product_id, costs=round(float(amount)*product.price, 2), amount=amount)

    product = Products.query.filter(Products.public_id==pos.product_id).first()
    
    recompute_stock(order, product, amount)

    db.session.add(pos)
    db.session.commit()
    return jsonify(pos.to_dict())

@orders_bp.route('/<public_id>/pos/', methods=['GET'])
def get_order_poss(public_id):
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
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
    # loged in user is not admin
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter_by(public_id=pos_id).first()
    # OrderPOS of pos_id do not exist 
    if not pos:
        raise OrderPosNOTExist()
    product_id = request.form["product_id"]
    product = Products.query.filter_by(public_id=product_id).first()
    if not product:
        raise ProductNOTExist()
    amount = request.form["amount"]
    pos.product_id = product_id
    pos.amount = amount
    pos.costs = round(float(amount)*product.price, 2)

    recompute_stock(order, product, int(pos.amount)+int(amount))

    db.session.commit()
    return jsonify(pos.to_dict())

@orders_bp.route('/<public_id>/pos/<pos_id>', methods=['GET'])
def get_order_pos(public_id, pos_id):
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter_by(public_id=pos_id).first()
    # OrderPOS of pos_id do not exist 
    if not pos:
        raise OrderPosNOTExist()
    return jsonify(pos.to_dict())

# DELETE POS
@orders_bp.route('/<public_id>/pos/<pos_id>', methods=['DELETE'])
@login_required
def delete_order_pos(public_id, pos_id):
    # loged in user is not admin
    if current_user.user_type != 1:
        raise NotAuthorized()
    order = Orders.query.filter_by(public_id=public_id).first()
    # Order of public_id do not exist 
    if not order:
        raise OrderNOTExist()
    pos = OrdersPOS.query.filter(OrdersPOS.public_id==pos_id).first()
    # OrderPOS of pos_id do not exist 
    if not pos:
        raise OrderPosNOTExist()
    
    product = Products.query.filter(Products.public_id==pos.product_id).first()
    recompute_stock(order, product, -int(pos.amount))

    db.session.delete(pos)
    db.session.commit()
    return jsonify(pos.to_dict())