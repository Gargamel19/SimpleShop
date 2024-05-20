# test_app.py
import pytest
from click.testing import CliRunner
from app import create_app
from app.extentions import db
from app.models import User
from flask import current_app
import unittest

from flask_testing import TestCase


class OrderTest(TestCase):

    runner =  CliRunner()
    temp_app = None

    def create_app(self):
        self.temp_app = create_app(type="test")
        return self.temp_app
    
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()


    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()


    def test_hello_command(self):
        result = self.runner.invoke(self.temp_app.cli.commands['create_tables'])
        assert result.exit_code == 0
        assert 'tables created' in result.output


    def test_add_admin_h(self):
        result = self.runner.invoke(self.temp_app.cli.commands['add_testdata'])
        assert result.exit_code == 0
        assert User.query.filter(User.name == "fettarmqp").count() == 1
        assert User.query.filter(User.name == "testuser").count() == 1


if __name__ == '__main__':
    unittest.main()