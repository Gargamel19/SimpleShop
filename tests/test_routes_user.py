from app import create_app
from app.extentions import db
from app.models import User
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
import uuid

from flask_testing import TestCase


public_id_persistant_user = str(uuid.uuid4())
public_id_persistant_user2 = str(uuid.uuid4())
public_id_persistant_admin = str(uuid.uuid4())

class UserTest(TestCase):


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

    def user_logout(self):
        
        response = self.client.get("/user/logout")
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
        global public_id_persistant_user
        global public_id_persistant_user2
        global public_id_persistant_admin
        user = User(name="testuser1", id=public_id_persistant_user, firstname="test1", lastname="user", email="testuser@testmail.com", password=password, user_type=0)
        user2 = User(name="testuser2", id=public_id_persistant_user2, firstname="test2", lastname="user", email="testuser2@testmail.com", password=password, user_type=0)
        user_admin = User(name="testadmin", id=public_id_persistant_admin, firstname="test", lastname="admin", email="testadmin@testmail.com", password=password, user_type=1)
        db.session.add(user)
        db.session.add(user2)
        db.session.add(user_admin)
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
        assert User.query.filter_by(id=user["id"]).count() == 1
        User.query.filter_by(id=user["id"]).delete()



    def test_admin(self):
        
        global public_id_persistant_user
        # CREATE USER
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
        assert User.query.filter_by(id=user["id"]).count() == 1

        # LOGIN AD ADMIN
        data = {
            "username": "testadmin",
            "password": "testpw"
        }
        response = self.client.post("/user/auth/login", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 302 # redirecting

        # EDIT OTHER USER
        data = {
            "username": "testuser3",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail2.com",
            "password": "testpw"
        }
        edit_user = User.query.filter_by(id=user["id"]).first()
        assert edit_user.name == "testuser"
        assert edit_user.email == "testuser@testmail.com"
        response = self.client.put(f"/user/{user['id']}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        edit_user = User.query.filter_by(id=user["id"]).first()
        assert edit_user.name == "testuser3"
        assert edit_user.email == "testuser@testmail2.com"

        # DELETE OTHER
        response = self.client.delete(f"/user/{user['id']}")
        assert response.status_code == 200
        assert User.query.filter_by(id=user["id"]).count() == 0

    def test_user(self):
        
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
        assert User.query.filter_by(id=user["id"]).count() == 1

        # LOGIN
        data = {
            "username": user["name"],
            "password": "testpw"
        }
        response = self.client.post("/user/auth/login", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 302 # redirecting
        
        # EDIT USER ERROR
        data = {
            "username": "testuser3",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail2.com",
            "password": "testpw"
        }
        edit_user = User.query.filter_by(id=public_id_persistant_user).first()
        assert edit_user.name == "testuser1"
        assert edit_user.email == "testuser@testmail.com"
        response = self.client.put(f"/user/{public_id_persistant_user}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 405
        edit_user = User.query.filter_by(id=public_id_persistant_user).first()
        assert edit_user.name == "testuser1"
        assert edit_user.email == "testuser@testmail.com"

        # EDIT USER
        data = {
            "username": "testuser3",
            "firstName": "test",
            "lastName": "user",
            "email": "testuser@testmail2.com",
            "password": "testpw"
        }
        edit_user = User.query.filter_by(id=user["id"]).first()
        assert edit_user.name == "testuser"
        assert edit_user.email == "testuser@testmail.com"
        response = self.client.put(f"/user/1", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 404
        response = self.client.put(f"/user/{user['id']}", data=data, headers={"Accept": "multipart/form-data"})
        assert response.status_code == 200
        edit_user = User.query.filter_by(id=user["id"]).first()
        assert edit_user.name == "testuser3"
        assert edit_user.email == "testuser@testmail2.com"


        # PROMOTE ERROR
        self.user_logout()
        response = self.client.post(f"/user/{public_id_persistant_user}/promote")
        assert response.status_code == 302
        self.user_login()
        response = self.client.post(f"/user/1/promote")
        assert response.status_code == 404
        
        # DELETE ERROR
        self.user_logout()
        assert User.query.filter_by(id=public_id_persistant_user).count() == 1
        response = self.client.delete(f"/user/{public_id_persistant_user}")
        assert response.status_code == 302
        self.user_login()
        response = self.client.delete(f"/user/{public_id_persistant_user2}")
        assert response.status_code == 405
        response = self.client.delete(f"/user/1")
        assert response.status_code == 404
        assert User.query.filter_by(id=public_id_persistant_user).count() == 1

        # DELETE
        self.admin_login()
        user_id = user["id"]
        response = self.client.delete(f"/user/{user_id}")
        assert response.status_code == 200
        assert User.query.filter_by(id=user_id).count() == 0
        
        # PROMOTE
        self.admin_login()
        response = self.client.post(f"/user/{public_id_persistant_user}/promote")
        assert response.status_code == 200

if __name__ == '__main__':
    unittest.main()