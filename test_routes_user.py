from app import create_app
from app.extentions import db
from app.models import User
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
import uuid

from flask_testing import TestCase


public_id_persistant_user = str(uuid.uuid4())

class MyTest(TestCase):


    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_db.sqlite'
    TESTING = True

    def create_app(self):
        return create_app(type="test")

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        password = generate_password_hash("testpw", method="pbkdf2:sha256")
        global public_id_persistant_user
        user = User(name="testuser1", public_id=public_id_persistant_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        db.session.add(user)
        db.session.commit()

    def test_homepage(self):
        response = self.client.get("/user/")
        assert response.status_code == 200

        
    def test_add_user(self):
        data = {
            "username": "testuser",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail.com",
            "password": "testpw"
        }
        response = self.client.post("/user/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        user = response.json
        assert User.query.filter_by(public_id=user["public_id"]).count() == 1
        User.query.filter_by(public_id=user["public_id"]).delete()

    def test_create_login_edit_delete(self):
        
        global public_id_persistant_user
        # CREATE
        data = {
            "username": "testuser",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail.com",
            "password": "testpw"
        }
        response = self.client.post("/user/", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        user = response.json
        assert User.query.filter_by(public_id=user["public_id"]).count() == 1

        # LOGIN
        data = {
            "username": user["name"],
            "password": "testpw"
        }
        response = self.client.post("/user/auth/login", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 302 # redirecting
        
        # EDIT USER ERROR
        data = {
            "username": "testuser2",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail2.com",
            "password": "testpw"
        }
        edit_user = User.query.filter_by(public_id=public_id_persistant_user).first()
        assert edit_user.name == "testuser1"
        assert edit_user.email == "testuser@testmail.com"
        response = self.client.put(f"/user/{public_id_persistant_user}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        edit_user = User.query.filter_by(public_id=public_id_persistant_user).first()
        assert edit_user.name == "testuser1"
        assert edit_user.email == "testuser@testmail.com"

        # EDIT USER
        data = {
            "username": "testuser2",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail2.com",
            "password": "testpw"
        }
        edit_user = User.query.filter_by(public_id=user["public_id"]).first()
        assert edit_user.name == "testuser"
        assert edit_user.email == "testuser@testmail.com"
        response = self.client.put(f"/user/{user['public_id']}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        edit_user = User.query.filter_by(public_id=user["public_id"]).first()
        assert edit_user.name == "testuser2"
        assert edit_user.email == "testuser@testmail2.com"

        
        # DELETE ERROR
        assert User.query.filter_by(public_id=public_id_persistant_user).count() == 1
        response = self.client.delete(f"/user/{public_id_persistant_user}")
        assert response.status_code == 405
        assert User.query.filter_by(public_id=public_id_persistant_user).count() == 1

        # DELETE
        response = self.client.delete(f"/user/{user['public_id']}")
        assert response.status_code == 200
        assert User.query.filter_by(public_id=user["public_id"]).count() == 0

if __name__ == '__main__':
    unittest.main()