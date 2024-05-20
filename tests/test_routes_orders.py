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
        user = User(name="testuser1", id=public_id_persistent_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        user_admin = User(name="testadmin", id=public_id_persistent_admin, firstname="test", lastname="admin", email="testadmin@testmail.com", password=password, user_type=1)

        product1 = Products(public_id=product1_persistent, title="Product 1", price=0.3, stock=100)
        product2 = Products(public_id=product2_persistent, title="Product 2", price=0.4, stock=100)

        supplier1 = Suppliers(public_id=supplier1_persistent, title="Supplier 1")
        supplier2 = Suppliers(public_id=supplier2_persistent, title="Supplier 2")


        db.session.add(user)
        db.session.add(user_admin)

        db.session.add(product1)
        db.session.add(product2)
        
        db.session.add(supplier1)
        db.session.add(supplier2)

        db.session.commit()
    
    def test_add_order(self):
        global supplier1_persistent
        data = {
            "supplier": supplier1_persistent,
            "order_type": 0
        }
        
        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.post("/orders/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        order = response.json
        assert Orders.query.filter_by(public_id=order["public_id"]).count() == 1
        Orders.query.filter_by(public_id=order["public_id"]).delete()

        # AS USER (FALUE)
        self.user_login()

        response = self.client.post("/orders/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405

    def test_add_order_wrong_parameters(self):
        global supplier1_persistent
        data = {
            "supplier": supplier1_persistent,
            "order_type": 1
        }
        
        # AS USER (FALUE)
        self.admin_login()

        response = self.client.post("/orders/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        assert Orders.query.filter_by(supplier=supplier1_persistent).count() == 0

        data = {
            "customer": "Hans Jürgen",
            "order_type": 0
        }
        
        # AS USER (FALUE)
        self.admin_login()

        response = self.client.post("/orders/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        assert Orders.query.filter_by(supplier=supplier1_persistent).count() == 0

        
        data = {
            "customer": "Hans Jürgen",
            "order_type": 1
        }
        
        # AS USER (FALUE)
        self.admin_login()

        response = self.client.post("/orders/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        order_json = response.json
        assert Orders.query.filter_by(public_id=order_json["public_id"]).count() == 1
        order = Orders.query.filter_by(public_id=order_json["public_id"]).first()
        db.session.delete(order)
        db.session.commit()

        
        data = {
            "supplier": supplier1_persistent,
            "order_type": 0
        }
        
        # AS USER (FALUE)
        self.admin_login()

        response = self.client.post("/orders/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        order_json = response.json
        assert Orders.query.filter_by(public_id=order_json["public_id"]).count() == 1
        order = Orders.query.filter_by(public_id=order_json["public_id"]).first()
        db.session.delete(order)
        db.session.commit()


    def test_get_order(self):
        global supplier1_persistent
        global product1_persistent
        public_id = str(uuid.uuid4())
        public_id_pos = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        orderpos = OrdersPOS(public_id=public_id_pos, order_id=public_id, product_id=product1_persistent, costs=10.3, amount=20)
        db.session.add(order)
        db.session.add(orderpos)
        db.session.commit()

        response = self.client.get(f"/orders/{public_id}")
        assert response.status_code == 200
        got_order = response.json
        print(got_order)
        assert got_order["supplier"] == supplier1_persistent

        
        response = self.client.get(f"/orders/lol")
        assert response.status_code == 404


    def test_get_orders(self):
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        public_id_pos = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        orderpos = OrdersPOS(public_id=public_id_pos, order_id=public_id, product_id=product1_persistent, costs=10.3, amount=20)
        db.session.add(order)
        db.session.add(orderpos)
        db.session.commit()

        response = self.client.get(f"/orders/")
        
        got_order = response.json
        assert len(got_order) == 1
        assert got_order[0]["supplier"] == supplier1_persistent


    def test_edit_order(self):
        global supplier1_persistent
        global supplier2_persistent
        public_id = str(uuid.uuid4())
        public_id_customer = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        order_customer = Orders(public_id=public_id_customer, customer="Hans Jürgen", type=1, order_date=datetime.now())
        db.session.add(order)
        db.session.add(order_customer)
        db.session.commit()

        data = {
            "supplier": supplier2_persistent
        }
        data_customer = {
            "customer": "Peter Maier"
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        prev_order = Orders.query.filter_by(public_id=public_id).first()
        assert prev_order.supplier == supplier1_persistent

        response = self.client.put(f"/orders/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        response = self.client.put(f"/orders/{public_id_customer}", data=data_customer, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        after_order = Orders.query.filter_by(public_id=public_id).first()
        assert after_order.supplier == supplier2_persistent
        
        response = self.client.put(f"/orders/lol", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 404
        
        # wrong paramerters

        response = self.client.put(f"/orders/{public_id_customer}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        response = self.client.put(f"/orders/{public_id}", data=data_customer, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405

        # AS USER (FALUE)
        self.user_login()

        response = self.client.put(f"/orders/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        response = self.client.put(f"/orders/{public_id_customer}", data=data_customer, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        after_user_order = Orders.query.filter_by(public_id=public_id).first()
        assert after_order == after_user_order




    def test_delete_order(self):
        
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        db.session.add(order)
        db.session.commit()


        # AS USER (FALUE)
        self.user_login()

        response = self.client.delete(f"/orders/{public_id}", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        assert Orders.query.filter_by(public_id=public_id).count() == 1

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.delete(f"/orders/{public_id}", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        response = self.client.delete(f"/orders/lol", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 404
        
        assert Orders.query.filter_by(public_id=public_id).count() == 0


    def test_add_pos_to_order(self):
        
        global product1_persistent
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        public_id_customer = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        order_customer = Orders(public_id=public_id_customer, customer="Hans Jürgen", type=1, order_date=datetime.now())
        db.session.add(order)
        db.session.add(order_customer)
        db.session.commit()

        data = {
            "product_id": product1_persistent,
            "amount": 2
        }
        
        data_failure = {
            "product_id": "lolobionda",
            "amount": 2
        }

        # AS USER (FALUE)
        self.user_login()

        response = self.client.put(f"/orders/{public_id}/pos/add", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        assert OrdersPOS.query.filter_by(product_id=product1_persistent).count() == 0
        

        # AS ADMIN (SUCC)
        self.admin_login()

        # supply
        before_stock = Products.query.filter(Products.public_id==product1_persistent).first().stock

        response = self.client.put(f"/orders/{public_id}/pos/add", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        after_stock = Products.query.filter(Products.public_id==product1_persistent).first().stock

        #assert before_stock - data["amount"] == after_stock
        # customer
        
        before_stock = Products.query.filter(Products.public_id==product1_persistent).first().stock

        response = self.client.put(f"/orders/{public_id_customer}/pos/add", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        after_stock = Products.query.filter(Products.public_id==product1_persistent).first().stock

        #assert before_stock + data["amount"] == after_stock

        
        response = self.client.put(f"/orders/lol/pos/add", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 404
        
        response = self.client.put(f"/orders/{public_id}/pos/add", data=data_failure, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 404
        
        assert OrdersPOS.query.filter_by(product_id=product1_persistent).count() == 2
        

    def test_edit_pos_from_order(self):
        
        global product1_persistent
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        public_id_POS = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        orderpos = OrdersPOS(public_id=public_id_POS, order_id=public_id, product_id=product1_persistent, costs=19.3, amount=10)
        db.session.add(order)
        db.session.add(orderpos)
        db.session.commit()

        data = {
            "product_id": product2_persistent,
            "amount": 5
        }

        # AS USER (FALUE)
        self.user_login()


        old_order_pos = OrdersPOS.query.filter_by(public_id=public_id_POS).first()
        assert old_order_pos.product_id == product1_persistent
        assert old_order_pos.amount == 10

        response = self.client.put(f"/orders/{public_id}/pos/{public_id_POS}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        nothing_order_pos = OrdersPOS.query.filter_by(public_id=public_id_POS).first()
        assert nothing_order_pos == old_order_pos

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.put(f"/orders/{public_id}/pos/{public_id_POS}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        
        new_order_pos = OrdersPOS.query.filter_by(public_id=public_id_POS).first()
        assert new_order_pos.product_id == product2_persistent
        assert new_order_pos.amount == 5

    def test_delete_pos_from_order(self):
        
        global product1_persistent
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        public_id_POS = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        orderpos = OrdersPOS(public_id=public_id_POS, order_id=public_id, product_id=product1_persistent, costs=19.3, amount=10)
        db.session.add(order)
        db.session.add(orderpos)
        db.session.commit()

        # AS USER (FALUE)
        self.user_login()


        assert OrdersPOS.query.filter_by(public_id=public_id_POS).count() == 1

        response = self.client.delete(f"/orders/{public_id}/pos/{public_id_POS}")
        assert response.status_code == 405
        
        assert OrdersPOS.query.filter_by(public_id=public_id_POS).count() == 1

        # AS ADMIN (SUCC)
        self.admin_login()

        assert OrdersPOS.query.filter_by(public_id=public_id_POS).count() == 1

        response = self.client.delete(f"/orders/{public_id}/pos/{public_id_POS}")
        assert response.status_code == 200
        
        assert OrdersPOS.query.filter_by(public_id=public_id_POS).count() == 0

    def test_get_pos_from_order(self):
        
        global product1_persistent
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        public_id_POS = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        orderpos = OrdersPOS(public_id=public_id_POS, order_id=public_id, product_id=product1_persistent, costs=19.3, amount=10)
        db.session.add(order)
        db.session.add(orderpos)
        db.session.commit()

        # AS USER (FALUE)
        self.user_login()

        response = self.client.get(f"/orders/{public_id}/pos/{public_id_POS}")
        assert response.status_code == 200
        
        assert OrdersPOS.query.filter_by(public_id=public_id_POS).count() == 1

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.get(f"/orders/{public_id}/pos/{public_id_POS}")
        assert response.status_code == 200
        
        assert OrdersPOS.query.filter_by(public_id=public_id_POS).count() == 1


    def test_get_poss_from_order(self):
        
        global product1_persistent
        global product2_persistent
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        public_id_POS = str(uuid.uuid4())
        public_id_POS2 = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent, type=0, order_date=datetime.now())
        orderpos = OrdersPOS(public_id=public_id_POS, order_id=public_id, product_id=product1_persistent, costs=19.3, amount=10)
        orderpos2 = OrdersPOS(public_id=public_id_POS2, order_id=public_id, product_id=product2_persistent, costs=134.3, amount=140)
        db.session.add(order)
        db.session.add(orderpos)
        db.session.add(orderpos2)
        db.session.commit()

        # AS USER (FALUE)
        self.user_login()

        response = self.client.get(f"/orders/{public_id}/pos/")
        assert response.status_code == 200
        
        assert OrdersPOS.query.filter_by(order_id=public_id).count() == 2

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.get(f"/orders/{public_id}/pos/")
        assert response.status_code == 200
        
        assert OrdersPOS.query.filter_by(order_id=public_id).count() == 2

if __name__ == '__main__':
    unittest.main()