from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from app.extentions import db
from sqlalchemy_serializer import SerializerMixin



class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = "user"
    id = Column(String(1000), unique=True, primary_key=True) # primary keys are required by SQLAlchemy
    name = Column(String(1000), unique=True)
    firstname = Column(String(1000), nullable=False)
    lastname = Column(String(1000), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    user_type = Column(Integer, nullable=False)
    

class Products(db.Model, SerializerMixin):
    __tablename__ = "product"
    public_id = Column(String(50), unique=True, primary_key=True) # primary keys are required by SQLAlchemy
    title = Column(String(1000), unique=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

    
class Suppliers(db.Model, SerializerMixin):
    __tablename__ = "suppliers"
    public_id = Column(String(50), unique=True, primary_key=True) # primary keys are required by SQLAlchemy
    title = Column(String(1000), nullable=False)


class Suppliers_Products(db.Model, SerializerMixin):
    __tablename__ = "suppliers_products"
    public_id = Column(Integer, primary_key=True) # primary keys are required by SQLAlchemy
    supplier_public_id = Column(String(50), nullable=False) # primary keys are required by SQLAlchemy
    product_public_id = Column(String(50), nullable=False) # primary keys are required by SQLAlchemy


class Orders(db.Model, SerializerMixin):
    __tablename__ = "orders_supply"
    public_id = Column(String(50), unique=True, primary_key=True) # primary keys are required by SQLAlchemy
    order_date = Column(DateTime, nullable=False)
    supplier = Column(String(50), nullable=True)
    type = Column(Integer, nullable=False) #(0 Supply, 1 Order)
    customer = Column(String(10000), nullable=True)
    
    
class OrdersPOS(db.Model, SerializerMixin):
    __tablename__ = "order_pos"
    public_id = Column(String(50), unique=True, primary_key=True) # primary keys are required by SQLAlchemy
    order_id = Column(String(50))
    product_id = Column(String(50), nullable=False)
    costs = Column(Float, nullable=False)
    amount = Column(Integer, nullable=False)