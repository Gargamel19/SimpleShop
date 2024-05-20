from app import create_app
from app.extentions import db
from app.models import User, Products
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
import uuid

from flask_testing import TestCase


public_id_persistent_user = str(uuid.uuid4())
public_id_persistent_admin = str(uuid.uuid4())

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
        user = User(name="testuser1", id=public_id_persistent_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        user_admin = User(name="testadmin", id=public_id_persistent_admin, firstname="test", lastname="admin", email="testadmin@testmail.com", password=password, user_type=1)
        
        db.session.add(user)
        db.session.add(user_admin)
        db.session.commit()
    
    def test_add_product(self):
        data = {
            "title": "Leckere Schokoriegel",
            "price": 3.5,
            "stock": 10
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.post("/products/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        product = response.json
        assert Products.query.filter_by(public_id=product["public_id"]).count() == 1
        Products.query.filter_by(public_id=product["public_id"]).delete()

        # AS USER (FALUE)
        self.user_login()

        response = self.client.post("/products/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        assert Products.query.filter_by(public_id=product["public_id"]).count() == 0


    def test_get_products(self):
        public_id = str(uuid.uuid4())
        prod = Products(public_id=public_id, title="Leckere Schokoriegel", price= 3.5, stock= 10)
        db.session.add(prod)
        db.session.commit()

        response = self.client.get(f"/products/{public_id}")
        got_product = response.json
        assert got_product["title"] == "Leckere Schokoriegel"
        assert got_product["price"] == 3.5
        assert got_product["stock"] == 10


    def test_get_product(self):
        public_id = str(uuid.uuid4())
        prod = Products(public_id=public_id, title="Leckere Schokoriegel", price= 3.5, stock= 10)
        db.session.add(prod)
        db.session.commit()

        response = self.client.get(f"/products/")
        
        got_product = response.json
        assert len(got_product) == 1
        assert got_product[0]["title"] == "Leckere Schokoriegel"
        assert got_product[0]["price"] == 3.5
        assert got_product[0]["stock"] == 10


    def test_edit_product(self):
        public_id = str(uuid.uuid4())
        prod = Products(public_id=public_id, title="Leckere Schokoriegel", price= 3.5, stock= 10)
        db.session.add(prod)
        db.session.commit()

        data = {
            "title": "Leckere Schokoriegel 2",
            "price": 3,
            "stock": 20
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        prev_prod = Products.query.filter_by(public_id=public_id).first()
        assert prev_prod.title == "Leckere Schokoriegel"
        assert prev_prod.price == 3.5
        assert prev_prod.stock == 10

        response = self.client.put(f"/products/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        after_prod = Products.query.filter_by(public_id=public_id).first()
        assert after_prod.title == "Leckere Schokoriegel 2"
        assert after_prod.price == 3
        assert after_prod.stock == 20

        # AS USER (FALUE)
        self.user_login()

        response = self.client.put(f"/products/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        after_user_prod = Products.query.filter_by(public_id=public_id).first()
        assert after_prod == after_user_prod


    def test_delete(self):
        
        public_id = str(uuid.uuid4())
        prod = Products(public_id=public_id, title="Leckere Schokoriegel", price= 3.5, stock= 10)
        db.session.add(prod)
        db.session.commit()


        # AS USER (FALUE)
        self.user_login()

        response = self.client.delete(f"/products/{public_id}", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        assert Products.query.filter_by(public_id=public_id).count() == 1

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.delete(f"/products/{public_id}", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        assert Products.query.filter_by(public_id=public_id).count() == 0

    def tearDown(self):
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    unittest.main()