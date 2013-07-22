from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, flash, redirect, url_for

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, current_user

from sqlalchemy.orm.interfaces import SessionExtension

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

def check_expired(f):
    """
    A decorator to check that the user's account is active.

    It will check that the user's account_expires date is no
    more than 7 days in the past.

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated():
            if datetime.utcnow() - current_user.account_expires > timedelta(seconds=7):
                flash("It looks like it's time to update your billing information to keep using Bookends.")
                return redirect(url_for('account_billing'))
        return f(*args, **kwargs)

    return decorated_function

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
