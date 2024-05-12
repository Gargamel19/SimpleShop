from app import create_app
from app.extentions import db
from app.models import User, Products, Suppliers, Suppliers_Products
import unittest
from werkzeug.security import generate_password_hash
import uuid

from flask_testing import TestCase


id_persistant_user = str(uuid.uuid4())
id_persistant_admin = str(uuid.uuid4())

product1_persistent = str(uuid.uuid4())

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

    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_db.sqlite'
    TESTING = True

    def create_app(self):
        return create_app(type="test")

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        password = generate_password_hash("testpw", method="pbkdf2:sha256")
        global id_persistant_user
        global id_persistant_admin
        user = User(name="testuser1", id=id_persistant_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        user_admin = User(name="testadmin", id=id_persistant_admin, firstname="test", lastname="admin", email="testadmin@testmail.com", password=password, user_type=1)
        
        product1 = Products(public_id=product1_persistent, title="Product 1", price=0.3, stock=10)

        db.session.add(user)
        db.session.add(user_admin)
        db.session.add(product1)
        db.session.commit()
    
    def test_add_supplier(self):
        data = {
            "title": "Super Supplier",
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.post("/suppliers/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        supp = response.json
        assert Suppliers.query.filter_by(public_id=supp["public_id"]).count() == 1
        Suppliers.query.filter_by(public_id=supp["public_id"]).delete()

        # AS USER (FALUE)
        self.user_login()

        response = self.client.post("/suppliers/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        assert Suppliers.query.filter_by(public_id=supp["public_id"]).count() == 0


    def test_get_supplier(self):
        public_id = str(uuid.uuid4())
        supp = Suppliers(public_id=public_id, title="Super Supplier")
        db.session.add(supp)
        db.session.commit()

        response = self.client.get(f"/suppliers/{public_id}")
        got_supplier = response.json
        assert got_supplier["title"] == "Super Supplier"


    def test_get_supplier(self):
        public_id = str(uuid.uuid4())
        supp = Suppliers(public_id=public_id, title="Super Supplier")
        db.session.add(supp)
        db.session.commit()

        response = self.client.get(f"/suppliers/")
        
        got_supp = response.json
        assert len(got_supp) == 1
        assert got_supp[0]["title"] == "Super Supplier"


    def test_edit_supplier(self):
        public_id = str(uuid.uuid4())
        supp = Suppliers(public_id=public_id, title="Super Supplier")
        db.session.add(supp)
        db.session.commit()

        data = {
            "title": "Super Supplier 2"
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        prev_supp = Suppliers.query.filter_by(public_id=public_id).first()
        assert prev_supp.title == "Super Supplier"

        response = self.client.put(f"/suppliers/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        after_supp = Suppliers.query.filter_by(public_id=public_id).first()
        assert after_supp.title == "Super Supplier 2"

        # AS USER (FALUE)
        self.user_login()

        response = self.client.put(f"/suppliers/{public_id}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        after_user_supp = Suppliers.query.filter_by(public_id=public_id).first()
        assert after_supp == after_user_supp


    def test_delete(self):
        
        public_id = str(uuid.uuid4())
        supp = Suppliers(public_id=public_id, title="Super Supplier")
        db.session.add(supp)
        db.session.commit()


        # AS USER (FALUE)
        self.user_login()

        response = self.client.delete(f"/suppliers/{public_id}", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        assert Suppliers.query.filter_by(public_id=public_id).count() == 1

        # AS ADMIN (SUCC)
        self.admin_login()

        response = self.client.delete(f"/suppliers/{public_id}", headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        
        assert Suppliers.query.filter_by(public_id=public_id).count() == 0

    def test_add_product_to_supplier(self):
        global product1_persistent
        public_id = str(uuid.uuid4())
        supp = Suppliers(public_id=public_id, title="Super Supplier")
        db.session.add(supp)
        db.session.commit()

        data = {
            "product_id": product1_persistent
        }

        # AS ADMIN (SUCC)
        self.admin_login()

        assert Suppliers_Products.query.filter_by(supplier_public_id=public_id).count() == 0

        response = self.client.put(f"/suppliers/{public_id}/add", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        s_p = Suppliers_Products.query.filter_by(supplier_public_id=public_id).first()

        assert Suppliers_Products.query.filter_by(supplier_public_id=public_id).count() == 1

        db.session.delete(s_p)

        # AS USER (FALUE)
        self.user_login()

        assert Suppliers_Products.query.filter_by(supplier_public_id=public_id).count() == 0
        
        response = self.client.put(f"/suppliers/{public_id}/add", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        
        assert Suppliers_Products.query.filter_by(supplier_public_id=public_id).count() == 0

if __name__ == '__main__':
    unittest.main()