from flask import Flask

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, current_user

from sqlalchemy.orm.interfaces import SessionExtension

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

from . import views

from .models import User, Book, Set

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view =  "signin"
login_manager.login_message = "Please sign in to view this page"
login_manager.refresh_view = "refresh_login"

@login_manager.user_loader
def load_user(userid):
    return User.get(userid=userid)
