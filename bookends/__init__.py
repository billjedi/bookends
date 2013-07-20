from flask import Flask

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, current_user

from sqlalchemy.orm.interfaces import SessionExtension

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

class OrphanedSetListener(SessionExtension):
    def after_flush(self, session, ctx):
        for set in Set().query.filter_by(user_id=current_user.id).all():
            if len(set.books.all()) is 0:
                print "DELETE"
                session.delete(set)

db = SQLAlchemy(app, session_extensions=[OrphanedSetListener()])

bcrypt = Bcrypt(app)

from . import views

from .models import User, Book, Set

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view =  "signin"
login_manager.login_message = "Please sign in to view this page"

@login_manager.user_loader
def load_user(userid):
    return User.get(userid=userid)
