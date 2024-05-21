from pathlib import Path
import os
import sys

main_folder = Path(__file__).parent.parent
sys.path.insert(0, str(main_folder))
sys.path.insert(0, str(main_folder / 'app'))
sys.path.insert(0, str(main_folder / 'tests'))
os.chdir(main_folder / 'app')

from app import create_app
from app.extentions import db
from app.models import User, Orders, OrdersPOS, Suppliers, Products
import unittest
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime 

from flask_testing import TestCase


public_id_persistent_user = str(uuid.uuid4())
public_id_persistent_admin = str(uuid.uuid4())

supplier1_persistent = str(uuid.uuid4())
supplier2_persistent = str(uuid.uuid4())

product1_persistent = str(uuid.uuid4())
product2_persistent = str(uuid.uuid4())

order_persistent = str(uuid.uuid4())

orderPOS_persistent = str(uuid.uuid4())

class OrderTest(TestCase):

    def admin_login(self):
        data = {
            "username": "testadmin",
            "password": "testpw"
        }
        response = self.client.post("/user/auth/login", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 302 # redirecting

    def user_login(self):
        data = {
            "username": "testuser1",
            "password": "testpw"
        }
        response = self.client.post("/user/auth/login", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 302 # redirecting

    def create_app(self):
        return create_app(type="test")

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        password = generate_password_hash("testpw", method="pbkdf2:sha256")
        global public_id_persistent_user
        global public_id_persistent_admin
        global supplier1_persistent
        global supplier2_persistent
        global product1_persistent
        global product2_persistent
        global order_persistent
        global orderPOS_persistent
        user = User(name="testuser1", id=public_id_persistent_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        user_admin = User(name="testadmin", id=public_id_persistent_admin, firstname="test", lastname="admin", email="testadmin@testmail.com", password=password, user_type=1)

        product1 = Products(public_id=product1_persistent, title="Product 1", price=0.3, stock=100)
        product2 = Products(public_id=product2_persistent, title="Product 2", price=0.4, stock=100)

        supplier1 = Suppliers(public_id=supplier1_persistent, title="Supplier 1")
        supplier2 = Suppliers(public_id=supplier2_persistent, title="Supplier 2")


        order1 = Orders(public_id=order_persistent, order_date=datetime.now(), type=1, customer="hans")

        
        order1POS = OrdersPOS(public_id=orderPOS_persistent, order_id=order_persistent, product_id=product1_persistent, costs=100.3, amount=2)

        db.session.add(user)
        db.session.add(user_admin)

        db.session.add(product1)
        db.session.add(product2)
        
        db.session.add(supplier1)
        db.session.add(supplier2)
        
        db.session.add(order1)

        db.session.add(order1POS)

        db.session.commit()

    def test_create(self):
        response = self.client.get("/products/create")
        assert response.status_code == 302 # not logged in

        self.user_login()

        response = self.client.get("/products/create")
        assert response.status_code == 200

    def test_all(self):

        response = self.client.get("/products/all")
        assert response.status_code == 200
        assert b"Products:" in response.data

    
    def test_edit(self):
        global product1_persistent
        response = self.client.get(f"/products/{product1_persistent}/edit")
        assert response.status_code == 302 # not logged in

        self.user_login()

        print(product1_persistent)

        response = self.client.get(f"/products/{product1_persistent}/edit")
        assert response.status_code == 200
        product = Products.query.filter(Products.public_id == product1_persistent).first()
        print(product.title)
        assert bytes(product.title, 'utf-8') in response.data

        
    def test_delete(self):
        global product1_persistent
        response = self.client.get(f"/products/{product1_persistent}/delete")
        assert response.status_code == 302 # not logged in

        self.user_login()

        print(product1_persistent)

        response = self.client.get(f"/products/{product1_persistent}/delete")
        assert response.status_code == 200
        product = Products.query.filter(Products.public_id == product1_persistent).first()
        assert b"Edit Product" in response.data
        print(response.data)
        assert bytes(product.title, 'utf-8') in response.data
    

        

if __name__ == '__main__':
    unittest.main()