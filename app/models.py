from flask_login import UserMixin
from flask import current_app
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship, mapped_column
from app.extentions import db
from sqlalchemy_serializer import SerializerMixin
import jwt
import time


class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True) # primary keys are required by SQLAlchemy
    public_id = Column(String(50), unique=True) # primary keys are required by SQLAlchemy
    name = Column(String(1000), unique=True)
    firstname = Column(String(1000))
    lastname = Column(String(1000))
    email = Column(String(100))
    password = Column(String(100))
    user_type = Column(Integer, nullable=False)

    def get_as_obj(self):
        return {
            "public_id": self.public_id,
            "name": self.name,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "user_type": self.user_type
        }