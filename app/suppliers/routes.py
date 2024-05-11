from app.suppliers import suppliers_bp
from flask import render_template, request, jsonify
from flask_login import current_user, login_required
from werkzeug import exceptions
from app.models import User, Products, Suppliers
from app.extentions import db
from sqlalchemy.exc import IntegrityError
import uuid



class NotAuthorized(exceptions.HTTPException):
    code = 405 
    description = 'User is not authorized to perform this action'

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
def index():
    return render_template("base.html", user=current_user)

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
    return jsonify(supplier.to_dict())
