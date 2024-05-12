from app.suppliers import suppliers_bp
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from werkzeug import exceptions
from app.models import User, Products, Suppliers, Suppliers_Products
from app.extentions import db
from sqlalchemy.exc import IntegrityError
import uuid



class NotAuthorized(exceptions.HTTPException):
    code = 405 
    description = 'User is not authorized to perform this action'

class ProductNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Product dose not exist.'

class SupplierNOTExist(exceptions.HTTPException):
    code = 404
    description = 'Supplier dose not exist.'

class SupplierAlreadyExist(exceptions.HTTPException):
    code = 400
    description = 'Supplier dose already exist.'

@suppliers_bp.errorhandler(exceptions.HTTPException)
def handle_error(e):
    return e.description, e.code

suppliers_bp.register_error_handler(SupplierNOTExist, handle_error)
suppliers_bp.register_error_handler(SupplierAlreadyExist, handle_error)
suppliers_bp.register_error_handler(NotAuthorized, handle_error)


### USER ENDPOINTS

@suppliers_bp.route('/all', methods=['GET'])
def all():
    suppliers = Suppliers.query.all()
    suppliers_json = []
    for supplier in suppliers:
        supplier_json = supplier.to_dict()
        supplier_json["s_p"] = []
        s_ps = Suppliers_Products.query.filter(Suppliers_Products.supplier_public_id==supplier.public_id).all()
        for s_p in s_ps:
            json_s_p = s_p.to_dict()
            product = Products.query.filter(Products.public_id==s_p.product_public_id).first()
            json_s_p["product"] = product.to_dict()
            supplier_json["s_p"].append(json_s_p)
        suppliers_json.append(supplier_json)
        
    return render_template("suppliers.html", user=current_user, suppliers=suppliers_json)


@suppliers_bp.route('/<public_id>/edit', methods=['GET', 'POST'])
def edit(public_id):
    if request.method == 'GET':
        supplier = Suppliers.query.filter_by(public_id=public_id).first()
        return render_template("suppliers_edit.html", user=current_user, supplier=supplier)
    else:
        edit_supplier(public_id)
        return redirect(url_for('suppliers.all'))

@suppliers_bp.route('/<public_id>/delete', methods=['GET', 'POST'])
def delete(public_id):
    if request.method == 'GET':
        supplier = Suppliers.query.filter_by(public_id=public_id).first()
        return render_template("suppliers_delete.html", user=current_user, supplier=supplier)
    else:
        delete_supplier(public_id)
        return redirect(url_for('suppliers.all'))
    
@suppliers_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return render_template("suppliers_create.html", user=current_user)
    else:
        create_supplier()
        return redirect(url_for('suppliers.all'))
    
@suppliers_bp.route('/<public_id>/products/add', methods=['GET', 'POST'])
def products_add(public_id):
    if request.method == 'GET':
        supplier = Suppliers.query.filter_by(public_id=public_id).first()
        products = Products.query.all()
        return render_template("suppliers_create_s_p.html", user=current_user, supplier=supplier, products=products)
    else:
        add_product_to_supplier(public_id)
        return redirect(url_for('suppliers.all', public_id=public_id))
    
@suppliers_bp.route('/<public_id>/products/<s_p_id>/delete', methods=['GET', 'POST'])
def delete_product(public_id, s_p_id):
    if request.method == 'GET':
        supplier = Suppliers.query.filter_by(public_id=public_id).first()
        s_p = Suppliers_Products.query.filter_by(public_id=s_p_id).first()
        product = Products.query.filter_by(public_id=s_p.product_public_id).first()
        return render_template("suppliers_delete_s_p.html", user=current_user, supplier=supplier, s_p=s_p, product=product)
    else:
        delete_product_to_supplier(public_id, s_p_id)
        return redirect(url_for('suppliers.all', public_id=public_id))


### API ENDPOINTS

# ------------------------------------------- SUPPLIER ---------------------------------------------------

    
@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    suppliers = Suppliers.query.all()
    supp_list = [] 
    for supp in suppliers:
        supp_list.append(supp.to_dict())
    return jsonify(supp_list)



# ------------------------------------------- SUPPLIER RESSOURCE ---------------------------------------------------
# CREATE:
@suppliers_bp.route('/', methods=['POST'])
@login_required
def create_supplier():
    if current_user.user_type != 1:
        raise NotAuthorized()
    public_id = str(uuid.uuid4())
    title = request.form["title"]
    
    try:
        supp = Suppliers(public_id=public_id, title=title)
        db.session.add(supp)
        db.session.commit()
    except IntegrityError:
        raise SupplierAlreadyExist()
    
    return supp.to_dict()

@suppliers_bp.route('/<public_id>', methods=['GET'])
def get_supplier(public_id):
    supplier = Suppliers.query.filter(Suppliers.public_id == public_id).first()
    if not supplier:
        raise SupplierNOTExist()
    return jsonify(supplier.to_dict())


@suppliers_bp.route('/<public_id>', methods=['PUT'])
@login_required
def edit_supplier(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    supp = Suppliers.query.filter(Suppliers.public_id == public_id).first()
    if not supp:
        raise SupplierNOTExist()
    # TODO: if forms are not given
    title = request.form["title"]
    supp.title = title
    db.session.commit()
    return jsonify(supp.to_dict())

@suppliers_bp.route('/<public_id>', methods=['DELETE'])
@login_required
def delete_supplier(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    supplier = Suppliers.query.filter(Suppliers.public_id == public_id).first()
    if not supplier:
        raise SupplierNOTExist()
    db.session.delete(supplier)
    db.session.commit()
    return jsonify(supplier.to_dict())


@suppliers_bp.route('/<public_id>/product/add', methods=['PUT'])
@login_required
def add_product_to_supplier(public_id):
    if current_user.user_type != 1:
        raise NotAuthorized()
    supplier = Suppliers.query.filter(Suppliers.public_id == public_id).first()
    if not supplier:
        raise SupplierNOTExist()
    product_id = request.form["product_id"]
    product = Products.query.filter(Products.public_id == product_id).first()
    if not product:
        raise ProductNOTExist()
    s_p = Suppliers_Products(supplier_public_id=supplier.public_id, product_public_id=product.public_id)
    db.session.add(s_p)
    db.session.commit()
    return jsonify(s_p.to_dict())

@suppliers_bp.route('/<public_id>/product/<s_p_id>', methods=['DELETE'])
@login_required
def delete_product_to_supplier(public_id, s_p_id):
    print(public_id, s_p_id)
    if current_user.user_type != 1:
        raise NotAuthorized()
    supplier = Suppliers.query.filter(Suppliers.public_id == public_id).first()
    if not supplier:
        raise SupplierNOTExist()
    s_p = Suppliers_Products.query.filter(Suppliers_Products.public_id == s_p_id).first()
    if not s_p:
        raise ProductNOTExist()
    db.session.delete(s_p)
    db.session.commit()
    return jsonify(s_p.to_dict())