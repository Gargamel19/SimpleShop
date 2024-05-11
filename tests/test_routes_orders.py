from app import create_app
from app.extentions import db
from app.models import User, Orders, Suppliers
import unittest
from werkzeug.security import generate_password_hash
import uuid

from flask_testing import TestCase


public_id_persistent_user = str(uuid.uuid4())
public_id_persistent_admin = str(uuid.uuid4())

supplier1_persistent = str(uuid.uuid4())
supplier2_persistent = str(uuid.uuid4())

class ProductTest(TestCase):

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
        user = User(name="testuser1", id=public_id_persistent_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        user_admin = User(name="testadmin", id=public_id_persistent_admin, firstname="test", lastname="admin", email="testadmin@testmail.com", password=password, user_type=1)
        
        supplier1 = Suppliers(public_id=supplier1_persistent, title="Supplier 1")
        supplier2 = Suppliers(public_id=supplier2_persistent, title="Supplier 2")


        db.session.add(user)
        db.session.add(user_admin)
        
        db.session.add(supplier1)
        db.session.add(supplier2)

        db.session.commit()
    
    def test_add_order(self):
        global supplier1_persistent
        data = {
            "supplier": supplier1_persistent
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
        assert Orders.query.filter_by(public_id=order["public_id"]).count() == 0


    def test_get_order(self):
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent)
        db.session.add(order)
        db.session.commit()

        response = self.client.get(f"/orders/{public_id}")
        got_order = response.json
        assert got_order["supplier"] == supplier1_persistent


    def test_get_orders(self):
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent)
        db.session.add(order)
        db.session.commit()

        response = self.client.get(f"/orders/")
        
        got_order = response.json
        assert len(got_order) == 1
        assert got_order[0]["supplier"] == supplier1_persistent


    def test_edit_order(self):
        global supplier1_persistent
        global supplier2_persistent
        public_id = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent)
        db.session.add(order)
        db.session.commit()

        data = {
            "supplier": supplier2_persistent
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        prev_order = Orders.query.filter_by(public_id=public_id).first()
        assert prev_order.supplier == supplier1_persistent

        response = self.client.put(f"/orders/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        after_order = Orders.query.filter_by(public_id=public_id).first()
        assert after_order.supplier == supplier2_persistent

        # AS USER (FALUE)
        self.user_login()

        response = self.client.put(f"/orders/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        after_user_order = Orders.query.filter_by(public_id=public_id).first()
        assert after_order == after_user_order


    def test_delete_order(self):
        
        global supplier1_persistent
        public_id = str(uuid.uuid4())
        order = Orders(public_id=public_id, supplier=supplier1_persistent)
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
        
        assert Orders.query.filter_by(public_id=public_id).count() == 0


if __name__ == '__main__':
    unittest.main()